#!/usr/bin/env python
"""AMRF (astrometric mass-ratio function) triage library -- Gaia DR3/DR4.

Formalism (verified against the LaTeX sources, local copies in data/papers/):

  Shahaf, Mazeh, Faigler & Holl 2019, MNRAS 487, 5610 (arXiv:1905.08542), S19:
    AMRF          A  = (a0/varpi) * (M1/Msun)^(-1/3) * (P/yr)^(-2/3)   [their eq. 4]
    Astrometry eq A  = q(1+q)^(-2/3) * [1 - S(1+q)/(q(1+S))]           [their eq. 6]
                  with q = M2/M1 and S = F2/F1 the G-band flux ratio.
    Dark companion (S=0): q_min is the unique positive root of
                  A^-3 q^3 - q^2 - 2q - 1 = 0                           [their eq. 3]
    Classes: I  (A < A_MS)  single-MS companion possible;
             II (A_MS < A < A_tr) close-binary MS companion possible;
             III(A > A_tr)  compact-object candidate.
    A_MS(M1) = max over q<=1 of the astrometry eq. with S = S_MS(q);
    A_tr(M1) = max of the astrometry eq. with the companion an equal-mass
               (q2=1) close MS binary, S = 2*L(q*M1/2)/L(M1), up to the q
               where S=1 (secondary as bright as the primary).

  Shahaf et al. 2023, MNRAS 518, 2991 (arXiv:2209.00828), S23:
    applied to DR3 with M1 from gaiadr3.binary_masses (m1_ref='IsocLum') and
    a conservative limiting curve (MIST-ensemble 99.9% envelope; their
    lookup table is only in the paywalled supplementary material).  Here the
    Mamajek-MLR curves are computed from scratch and *validated against
    S23's per-source published classifications* (CDS J/MNRAS/518/2991).

Mass-luminosity input: the Pecaut & Mamajek 2013 (ApJS 208, 9) mean dwarf
sequence, version 2022.04.16 of the EEM table (M_G and Msun columns);
local copy data/papers/EEM_dwarf_UBVIJHK_colors_Teff.txt.
S23 used the same source for their non-MIST reference curve ("mamajek13").

a0 from Thiele-Innes coefficients (both Orbital and AstroSpectroSB1 publish
A,B,F,G in mas; AstroSpectroSB1 additionally has C,H -- NOT needed for a0):
    u  = (A^2+B^2+F^2+G^2)/2 ;  v = A*G - B*F
    a0 = sqrt(u + sqrt(u^2 - v^2))
[Halbwachs et al. 2023, A&A 674, A9, arXiv:2206.05726, eq. 12-14]
"""

import os
from functools import lru_cache

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EEM_PATH = os.path.join(BASE, "data", "papers", "EEM_dwarf_UBVIJHK_colors_Teff.txt")

YR_DAYS = 365.25


# ----------------------------------------------------------------------
# Thiele-Innes -> a0
# ----------------------------------------------------------------------

def thiele_innes_a0(A, B, F, G):
    """Photocentre angular semi-major axis a0 [mas] from Thiele-Innes
    coefficients [mas].  Halbwachs et al. 2023 eq. 12-14."""
    A, B, F, G = (np.asarray(x, dtype=float) for x in (A, B, F, G))
    u = (A**2 + B**2 + F**2 + G**2) / 2.0
    v = A * G - B * F
    disc = np.clip(u * u - v * v, 0.0, None)
    return np.sqrt(u + np.sqrt(disc))


def sigma_ti_sq(A, eA, B, eB, F, eF, G, eG):
    """S23 Thiele-Innes quality statistic: sum of squared relative errors
    (their eq. 8; cut sigma_TI^2 <= 36)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((eA / A) ** 2 + (eB / B) ** 2 + (eF / F) ** 2 + (eG / G) ** 2)


# ----------------------------------------------------------------------
# AMRF and the dark-companion inversion
# ----------------------------------------------------------------------

def amrf(a0_mas, parallax_mas, m1_msun, period_days):
    """A = (a0/varpi) * M1^(-1/3) * (P/yr)^(-2/3)  [S19 eq. 4 / S23 eq. 1]."""
    a0_mas = np.asarray(a0_mas, dtype=float)
    return (a0_mas / parallax_mas) * m1_msun ** (-1.0 / 3.0) \
        * (period_days / YR_DAYS) ** (-2.0 / 3.0)


def q_min_dark(A):
    """Unique positive root q of  A^-3 q^3 - q^2 - 2q - 1 = 0  (S19 eq. 3):
    the mass ratio if the companion is completely dark (S=0)."""
    A = np.atleast_1d(np.asarray(A, dtype=float))
    out = np.full(A.shape, np.nan)
    for i, a in np.ndenumerate(A):
        if not np.isfinite(a) or a <= 0:
            continue
        roots = np.roots([a ** -3.0, -1.0, -2.0, -1.0])
        real = roots[np.abs(roots.imag) < 1e-9].real
        pos = real[real > 0]
        if len(pos):
            out[i] = pos.min() if len(pos) == 1 else pos[np.argmin(np.abs(pos))]
    return out if out.size > 1 else float(out.ravel()[0])


def photocentre_factor(q, S):
    """The bracket of S19 eq. 6: 1 - S(1+q)/(q(1+S))."""
    return 1.0 - S * (1.0 + q) / (q * (1.0 + S))


def amrf_of_q(q, S=0.0):
    """Astrometry equation A(q, S)  [S19 eq. 6]."""
    return q / (1.0 + q) ** (2.0 / 3.0) * photocentre_factor(q, S)


# ----------------------------------------------------------------------
# Mamajek/Pecaut MS sequence: M_G(mass) and mass(M_G)
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _eem_ms_table():
    """(mass_msun, M_G) arrays for the MS, sorted by mass, from the EEM table.
    Keeps rows where both Msun and M_G are numeric (B9V..L2, 2.75..~0.07)."""
    with open(EEM_PATH, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    header = next(l for l in lines if l.startswith("#SpT"))
    cols = header.lstrip("#").split()
    i_mg, i_mass = cols.index("M_G"), cols.index("Msun")
    masses, mgs = [], []
    for l in lines:
        if l.startswith("#") or not l.strip():
            continue
        parts = l.split()
        if len(parts) != len(cols):
            continue
        try:
            mg = float(parts[i_mg])
            mass = float(parts[i_mass])
        except ValueError:
            continue
        if mass > 0:
            masses.append(mass)
            mgs.append(mg)
    m = np.array(masses)
    g = np.array(mgs)
    order = np.argsort(m)
    m, g = m[order], g[order]
    # enforce strict monotonicity for interpolation (average duplicates)
    um, ug = [], []
    for mi in np.unique(m):
        um.append(mi)
        ug.append(g[m == mi].mean())
    return np.array(um), np.array(ug)


def mg_of_mass(mass):
    """Absolute G magnitude of an MS star of given mass [Msun] (EEM table,
    linear interpolation in log-mass). NaN outside the table range."""
    m_tab, g_tab = _eem_ms_table()
    mass = np.asarray(mass, dtype=float)
    out = np.interp(np.log10(mass), np.log10(m_tab), g_tab,
                    left=np.nan, right=np.nan)
    return out


def mass_of_mg(mg):
    """MS mass [Msun] from absolute G magnitude (inverse interpolation).
    NaN outside the table range (evolved stars land here too -- caller must
    apply a CMD main-sequence cut first)."""
    m_tab, g_tab = _eem_ms_table()
    # M_G decreases with mass -> reverse for np.interp
    mg = np.asarray(mg, dtype=float)
    logm = np.interp(mg, g_tab[::-1], np.log10(m_tab)[::-1],
                     left=np.nan, right=np.nan)
    return 10.0 ** logm


def flux_ratio_ms(m2, m1):
    """G-band flux ratio S = F2/F1 for two MS stars (EEM table).
    Below the table's low-mass end the companion is treated as dark (S=0)."""
    mg1 = mg_of_mass(m1)
    mg2 = mg_of_mass(m2)
    S = 10.0 ** (-0.4 * (mg2 - mg1))
    return np.where(np.isnan(mg2), 0.0, S)


# ----------------------------------------------------------------------
# Class-boundary curves A_MS(M1), A_tr(M1)
# ----------------------------------------------------------------------

def a_ms_max(m1, nq=2000):
    """max over q in (0,1] of A(q, S_MS(q)) -- the class-I/II boundary."""
    q = np.linspace(1e-3, 1.0, nq)
    S = flux_ratio_ms(q * m1, m1)
    vals = amrf_of_q(q, S)
    return float(np.nanmax(vals))


def a_tr_max(m1, nq=4000):
    """max of A for a companion that is an equal-mass (q2=1) close MS binary
    -- the class-II/III boundary.  Components each of mass q*M1/2;
    S = 2*L(q*M1/2)/L(M1); valid while S <= 1 (S19 Sec. 2.3)."""
    q = np.linspace(1e-3, 2.0, nq)
    S = 2.0 * flux_ratio_ms(q * m1 / 2.0, m1)
    ok = S <= 1.0
    vals = np.where(ok, amrf_of_q(q, np.clip(S, 0, None)), np.nan)
    return float(np.nanmax(vals))


@lru_cache(maxsize=8)
def boundary_curves(m1_lo=0.10, m1_hi=2.60, n=126):
    """Tabulated (m1_grid, A_MS, A_tr) for interpolation."""
    m1_grid = np.linspace(m1_lo, m1_hi, n)
    ams = np.array([a_ms_max(m) for m in m1_grid])
    atr = np.array([a_tr_max(m) for m in m1_grid])
    return m1_grid, ams, atr


def a_ms(m1):
    g, ams, _ = boundary_curves()
    return np.interp(np.asarray(m1, dtype=float), g, ams,
                     left=ams[0], right=ams[-1])


def a_tr(m1, inflate=1.0):
    """Class-II/III boundary at M1. `inflate` multiplies the curve --
    the knob that emulates S23's conservative MIST envelope (calibrated
    against their published classifications in the pipeline)."""
    g, _, atr = boundary_curves()
    return inflate * np.interp(np.asarray(m1, dtype=float), g, atr,
                               left=atr[0], right=atr[-1])


def classify(A, m1, inflate=1.0):
    """Deterministic class from best-fit A and M1: 1, 2 or 3 (0 = undefined)."""
    A = np.asarray(A, dtype=float)
    ams = a_ms(m1)
    atr = a_tr(m1, inflate=inflate)
    cls = np.zeros(np.broadcast(A, ams).shape, dtype=int)
    cls[np.asarray(A <= ams)] = 1
    cls[np.asarray((A > ams) & (A <= atr))] = 2
    cls[np.asarray(A > atr)] = 3
    cls[~np.isfinite(A)] = 0
    return cls


# ----------------------------------------------------------------------
# Photometric M1 (fallback when binary_masses/nss_masses has no row)
# ----------------------------------------------------------------------

def abs_g(g_mag, parallax_mas):
    """Absolute G magnitude from apparent G and parallax [mas].
    NO extinction correction (documented limitation; biases M1 low and A
    high for reddened sources -- conservative for completeness, inflates
    false positives at low |b|)."""
    parallax_mas = np.asarray(parallax_mas, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.asarray(g_mag, dtype=float) + 5.0 * np.log10(parallax_mas / 100.0)


def is_main_sequence(mg0, bp_rp0):
    """El-Badry et al. 2026 (arXiv:2608.06453) eq. 1 CMD main-sequence cut:
    MS if M_G0 > 4.5  or  M_G0 > -9.37 + 13.42*(BP-RP)0."""
    mg0 = np.asarray(mg0, dtype=float)
    bp_rp0 = np.asarray(bp_rp0, dtype=float)
    return (mg0 > 4.5) | (mg0 > -9.37 + 13.42 * bp_rp0)


def m1_photometric(g_mag, parallax_mas, bp_rp=None, require_ms=True):
    """MS photometric primary mass from (G, parallax) via the EEM sequence.
    Returns (m1, ms_flag).  Evolved/off-table sources -> NaN when
    require_ms; the caller decides how to treat them (never silently)."""
    mg = abs_g(g_mag, parallax_mas)
    m1 = mass_of_mg(mg)
    if bp_rp is None:
        ms = np.isfinite(m1)
    else:
        ms = is_main_sequence(mg, bp_rp)
    if require_ms:
        m1 = np.where(ms, m1, np.nan)
    return m1, ms
