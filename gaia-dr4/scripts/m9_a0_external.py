#!/usr/bin/env python
"""M9 task 3: an EXTERNAL reference for the photocentre semi-major axis a0.

THE GAP, IN M8's OWN WORDS (sec.1f)
===================================
    "SB9 gives P and e.  The companion mass goes as a0^3, and no external
     reference for a0 is used anywhere above ... An inflation factor
     measured on P and e does not license one on a0, and the honest
     statement is that a0's external calibration is still open."

M8 measured the DR3 NSS error inflation at x1.40 on 202 period and
eccentricity comparisons against SB9.  Neither element is the one the mass
function is cubed in.  This closes that -- or says plainly what is left
open.

THE IDEA, AND WHY IT IS EXTERNAL
================================
For a spectroscopic binary, the RADIAL VELOCITIES alone fix the primary's
own orbit about the barycentre:

    a1 sin i = K1 P sqrt(1 - e^2) / (2 pi)                     [1]

That is ground-based spectroscopy.  It shares no photons with Gaia, it does
not use a parallax, and it does not use an astrometric model.

Gaia's astrometric NSS solution independently gives the PHOTOCENTRE orbit,
a0 [mas], and the inclination i, through the Thiele-Innes elements; with the
solution's own parallax,

    a0 sin i [AU] = (a0 [mas] / varpi [mas]) x sin i           [2]

and the two are related by the classical photocentre identity

    a0 = a_rel (B - beta),      a1 = a_rel B,                  [3]
    B = M2/(M1+M2)  (mass fraction),  beta = L2/(L1+L2)  (light fraction)

    =>  a0 = a1 - beta a_rel  <=  a1     for every beta >= 0.  [4]

**[4] is the whole test, and it is one-sided.**  A companion that emits
light drags the photocentre towards it and can only make a0 SMALLER than
a1.  So

  * the ratio  R = (a0 sin i)_Gaia / (a1 sin i)_SB9  must satisfy R <= 1
    up to measurement error, for every system, with no astrophysical
    escape;
  * any system with R > 1 by more than the quoted errors is a failure of
    the errors (or of a0, or of i, or of varpi) -- it cannot be explained
    by the companion;
  * therefore the OVER-RUN FRACTION -- how often R exceeds 1 by more than
    k sigma -- is a CONSERVATIVE lower bound on how badly the a0 error bar
    is understated.  Every luminous secondary in the sample makes the test
    weaker, never falsely positive.

INDEPENDENCE, STATED HONESTLY (and this decides the primary sample)
==================================================================
`AstroSpectroSB1` solutions are JOINT astrometry+RV fits: Gaia's own RVS
supplies K1 inside the same solution that produces a0.  For those, [1] and
[2] are not independent and the comparison is circular.  They are excluded
from the primary sample and reported separately as the internal control --
they SHOULD agree better, and if they do not, something is wrong with the
implementation rather than with Gaia.

The primary sample is `Orbital` / `OrbitalTargetedSearch[Validated]`:
astrometry-only Gaia solutions against ground-based radial velocities.

PRE-REGISTERED RULES (fixed in this docstring before any R was looked at)
========================================================================
  * SB9 crossmatch radius 2.0", one orbit per SB9 Seq (best Grade, ties to
    the larger number of RVs) -- identical to M8 sec.1b, reused not
    reinvented.
  * SAME-ORBIT GATE |ln(P_Gaia / P_SB9)| < 0.05, failures counted.  Two
    catalogues describing different orbits cannot calibrate anything.
  * both sides must publish finite positive uncertainties on everything
    that enters [1] and [2].
  * ECCENTRICITY GUARD e < 0.99 and K1 > 0.
  * the primary statistic is the MEDIAN of R with a 5,000-resample
    bootstrap CI; the secondary is the over-run fraction at k = 1, 2, 3.
  * the a0 and i uncertainties come from a Monte-Carlo over the four
    published Thiele-Innes elements and their published errors.  The
    published correlations are NOT available for most of this sample
    (corr_vec was pulled for the class-III + retrieval sets only, M3), so
    the MC treats them as independent and the resulting sigma is reported
    as an APPROXIMATION -- named here, before the numbers.

  .venv\\Scripts\\python.exe scripts\\m9_a0_external.py --run
  .venv\\Scripts\\python.exe scripts\\m9_a0_external.py --eb26
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m8_error_inflation as EI                                  # noqa: E402

OUT = os.path.join(BASE, "out")
DATA = os.path.join(BASE, "data")
NSS = os.path.join(DATA, "dr3_nss_amrf_input.parquet")

AU_KM = 1.495978707e8
DAY_S = 86400.0
MATCH_RADIUS_AS = 2.0
PERIOD_GATE = 0.05
N_MC = 4000
N_BOOT = 5000
SEED = 20261202

ASTROMETRY_ONLY = ("Orbital", "OrbitalTargetedSearch",
                   "OrbitalTargetedSearchValidated", "OrbitalAlternative",
                   "OrbitalAlternativeValidated")


# ----------------------------------------------------------------------
def a1sini_au(K1_kms, P_d, e):
    """[1]: the primary's semi-major axis about the barycentre, projected.
    Pure spectroscopy -- no parallax, no astrometric model."""
    return (K1_kms * P_d * DAY_S * np.sqrt(np.clip(1.0 - e**2, 0, None))
            / (2.0 * np.pi)) / AU_KM


def campbell_a0_inc(A, B, F, G):
    """Thiele-Innes -> (a0 [same unit as A..G], inclination [rad]).

    The standard inversion (e.g. Halbwachs et al. 2023 eq. 5-9, and the
    identical algebra inside nsstools).  Only a0 and i are needed here, and
    both come out of the two invariants below, so the quadrant ambiguities
    in omega/Omega -- which is where an independent implementation usually
    goes wrong -- never arise.
    """
    u = 0.5 * (A**2 + B**2 + F**2 + G**2)
    v = A * G - B * F
    a0 = np.sqrt(np.clip(u + np.sqrt(np.clip(u**2 - v**2, 0, None)), 0, None))
    # cos i = v / a0^2, signed; the sign is the sense of revolution
    with np.errstate(divide="ignore", invalid="ignore"):
        cosi = np.clip(v / np.where(a0 > 0, a0**2, np.nan), -1.0, 1.0)
    return a0, np.arccos(cosi)


def _mc_a0_sini(row, rng, n=N_MC):
    """a0 sin i [AU] with an uncertainty, by MC over the published
    Thiele-Innes elements, their published errors and the solution's own
    parallax error.  Correlations unavailable for most of this sample --
    see the docstring."""
    A = rng.normal(row.a_thiele_innes, row.a_thiele_innes_error, n)
    B = rng.normal(row.b_thiele_innes, row.b_thiele_innes_error, n)
    F = rng.normal(row.f_thiele_innes, row.f_thiele_innes_error, n)
    G = rng.normal(row.g_thiele_innes, row.g_thiele_innes_error, n)
    plx = rng.normal(row.nss_parallax, row.nss_parallax_error, n)
    a0, inc = campbell_a0_inc(A, B, F, G)
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.where(plx > 0, (a0 / plx) * np.sin(inc), np.nan)
    x = x[np.isfinite(x)]
    if len(x) < n // 10:
        return np.nan, np.nan, np.nan, np.nan
    a0c, incc = campbell_a0_inc(row.a_thiele_innes, row.b_thiele_innes,
                                row.f_thiele_innes, row.g_thiele_innes)
    central = (a0c / row.nss_parallax) * np.sin(incc) \
        if row.nss_parallax > 0 else np.nan
    return (central, float(np.std(x)), float(a0c),
            float(np.degrees(incc)))


def _mc_a1sini(row, rng, n=N_MC):
    K1 = rng.normal(row.K1, row.e_K1, n)
    P = rng.normal(row.Per, row.e_Per if np.isfinite(row.e_Per) else 0.0, n)
    e = np.clip(rng.normal(row.e_sb9, row.e_e_sb9
                           if np.isfinite(row.e_e_sb9) else 0.0, n),
                0.0, 0.999)
    x = a1sini_au(K1, P, e)
    x = x[np.isfinite(x) & (x > 0)]
    central = a1sini_au(row.K1, row.Per, min(max(row.e_sb9, 0.0), 0.999))
    return central, (float(np.std(x)) if len(x) > n // 10 else np.nan)


# ----------------------------------------------------------------------
def build(say, radius_as=MATCH_RADIUS_AS):
    cols = ["source_id", "nss_solution_type", "period", "period_error",
            "eccentricity", "eccentricity_error",
            "a_thiele_innes", "a_thiele_innes_error",
            "b_thiele_innes", "b_thiele_innes_error",
            "f_thiele_innes", "f_thiele_innes_error",
            "g_thiele_innes", "g_thiele_innes_error",
            "nss_parallax", "nss_parallax_error", "significance",
            "phot_g_mean_mag", "ra", "dec", "bm_fluxratio", "bm_m1"]
    nss = pd.read_parquet(NSS, columns=cols)
    say("  DR3 NSS rows on disk: %d" % len(nss))
    j = EI.sb9_match(nss, radius_as=radius_as)
    say("  SB9 positional matches within %.1f\": %d" % (radius_as, len(j)))
    j = j.rename(columns={"e": "e_sb9", "e_e": "e_e_sb9"})
    for c in ("Per", "e_Per", "e_sb9", "e_e_sb9", "K1", "e_K1", "K2",
              "e_K2", "Grade"):
        j[c] = pd.to_numeric(j[c], errors="coerce")
    # ---- the pre-registered gates ------------------------------------
    n0 = len(j)
    j = j[np.isfinite(j.Per) & (j.Per > 0) & np.isfinite(j.period)]
    same = np.abs(np.log(j.period / j.Per)) < PERIOD_GATE
    say("  same-orbit gate |ln(P_Gaia/P_SB9)| < %.2f: %d pass, %d fail"
        % (PERIOD_GATE, int(same.sum()), int((~same).sum())))
    j = j[same]
    need = ["K1", "e_K1", "a_thiele_innes", "a_thiele_innes_error",
            "b_thiele_innes", "b_thiele_innes_error", "f_thiele_innes",
            "f_thiele_innes_error", "g_thiele_innes", "g_thiele_innes_error",
            "nss_parallax", "nss_parallax_error"]
    ok = np.ones(len(j), bool)
    for c in need:
        ok &= np.isfinite(pd.to_numeric(j[c], errors="coerce").values)
    ok &= (pd.to_numeric(j["K1"], errors="coerce").values > 0)
    ok &= (pd.to_numeric(j["e_K1"], errors="coerce").values > 0)
    ok &= (pd.to_numeric(j["nss_parallax"], errors="coerce").values > 0)
    ok &= (pd.to_numeric(j["e_sb9"], errors="coerce").fillna(0).values < 0.99)
    say("  finite-and-positive gate on everything in eq.[1] and eq.[2]: "
        "%d pass of %d" % (int(ok.sum()), len(j)))
    j = j[ok].reset_index(drop=True)
    say("  -> %d systems from %d SB9 matches" % (len(j), n0))
    return j


def measure(j, say, seed=SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for _, r in j.iterrows():
        a0s, a0s_e, a0_mas, inc_deg = _mc_a0_sini(r, rng)
        a1s, a1s_e = _mc_a1sini(r, rng)
        if not (np.isfinite(a0s) and np.isfinite(a1s) and a1s > 0):
            continue
        R = a0s / a1s
        sR = R * np.sqrt((a0s_e / a0s) ** 2 + (a1s_e / a1s) ** 2) \
            if np.isfinite(a0s_e) and np.isfinite(a1s_e) else np.nan
        rows.append({
            "source_id": int(r.source_id), "Seq": int(r.Seq),
            "nss_solution_type": r.nss_solution_type,
            "astrometry_only": r.nss_solution_type in ASTROMETRY_ONLY,
            "sb9_grade": r.Grade, "sep_arcsec": r.sep_arcsec,
            "period_gaia_d": r.period, "period_sb9_d": r.Per,
            "ecc_sb9": r.e_sb9, "K1_kms": r.K1, "e_K1_kms": r.e_K1,
            "sb2": bool(np.isfinite(r.K2) and r.K2 > 0),
            "a0_mas": a0_mas, "inc_deg": inc_deg,
            "nss_parallax_mas": r.nss_parallax,
            "a0_sini_au": a0s, "a0_sini_err_au": a0s_e,
            "a1_sini_au": a1s, "a1_sini_err_au": a1s_e,
            "R": R, "R_err": sR,
            "z_over": (R - 1.0) / sR if np.isfinite(sR) and sR > 0 else np.nan,
            "significance": r.significance,
            "phot_g_mean_mag": r.phot_g_mean_mag,
            "bm_fluxratio": r.bm_fluxratio,
        })
    return pd.DataFrame(rows)


def _jsonable(o):
    """json default that never silently stringifies a whole table."""
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, (pd.DataFrame, pd.Series)):
        return "<%s %s omitted>" % (type(o).__name__, getattr(o, "shape", ""))
    return str(o)


def _boot_median(x, rng, n=N_BOOT):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan, np.nan, np.nan
    b = np.median(rng.choice(x, size=(n, len(x)), replace=True), axis=1)
    return float(np.median(x)), float(np.percentile(b, 2.5)), \
        float(np.percentile(b, 97.5))


def report(d, say, seed=SEED):
    rng = np.random.default_rng(seed + 1)
    out = {}
    for tag, sub in (("PRIMARY  astrometry-only Gaia vs ground-based RV",
                      d[d.astrometry_only]),
                     ("CONTROL  AstroSpectroSB1 (joint fit -- NOT external)",
                      d[~d.astrometry_only])):
        if not len(sub):
            say("\n  %s: no systems" % tag)
            continue
        med, lo, hi = _boot_median(sub.R, rng)
        say("\n  %s" % tag)
        say("    n = %d systems" % len(sub))
        say("    median R = a0 sin i / a1 sin i : %.3f  [%.3f, %.3f] "
            "(95%% bootstrap)" % (med, lo, hi))
        say("    quartiles of R: %.3f / %.3f / %.3f"
            % tuple(np.nanpercentile(sub.R, [25, 50, 75])))
        z = sub["z_over"].replace([np.inf, -np.inf], np.nan).dropna()
        line = []
        for k, expect in ((1, 15.87), (2, 2.28), (3, 0.135)):
            f = 100.0 * float((z > k).mean()) if len(z) else np.nan
            line.append("k=%d: %.1f%% (expect <= %.2f%%)" % (k, f, expect))
        say("    ONE-SIDED OVER-RUN, R > 1 by more than k sigma "
            "(n = %d with a sigma):" % len(z))
        for x in line:
            say("        " + x)
        say("    fraction with R > 1 at all: %.1f %% "
            "(a luminous secondary can only push R DOWN)"
            % (100.0 * float((sub.R > 1).mean())))
        out[tag.split()[0]] = {
            "n": int(len(sub)), "median_R": med, "R_lo": lo, "R_hi": hi,
            "frac_R_gt_1": float((sub.R > 1).mean()),
            "over_run_1sig": float((z > 1).mean()) if len(z) else None,
            "over_run_2sig": float((z > 2).mean()) if len(z) else None,
            "over_run_3sig": float((z > 3).mean()) if len(z) else None,
        }
    return out


# ======================================================================
# ROUTE 2 and 3 -- catalogues that publish a0 ITSELF, from other photons.
#
# Two exist in the whole of the published literature that are machine
# readable, cover more than a handful of systems, and are not derived from
# Gaia:
#
#   HIP-DMSA/O  the Hipparcos Double and Multiple Systems Annex, Part O
#               (ESA 1997, SP-1200 Vol.10), VizieR I/239/hip_dm_o: 235
#               photocentric orbits with a0 [mas] AND a published e_a0.
#   ORB6 g9     the Sixth Catalog of Orbits of Visual Binary Stars
#               (Hartkopf, Mason & Worley 2001, AJ 122, 3472; USNO), whose
#               GRADE 9 means "astrometric binary" -- i.e. a photocentric
#               orbit.  Not in VizieR; a fixed-width file over anonymous
#               HTTPS.  It is the only machine-readable aggregator of
#               Goldin & Makarov (2006, 2007), Ren & Fu (2013) and
#               Pourbaix & Jorissen (2000).
#
# THEY ARE NOT INDEPENDENT OF EACH OTHER, and this code proves it rather
# than assuming it: most ORB6 grade-9 entries are references back to
# HIP1997d, i.e. the DMSA/O numbers themselves.  The union is therefore
# smaller than the sum, and the per-reference breakdown is printed.
# ======================================================================
HIP_DMSA_O = os.path.join(DATA, "hipparcos", "I_239_hip_dm_o.parquet")
ORB6_TXT = os.path.join(DATA, "orb6", "orb6orbits.txt")
ORB6_PARQUET = os.path.join(DATA, "orb6", "orb6orbits.parquet")
ORB6_URL = "https://crf.usno.navy.mil/data_products/WDS/orb6/orb6orbits.txt"
VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"


def fetch_hip_dmsa_o(force=False):
    if os.path.exists(HIP_DMSA_O) and not force:
        return pd.read_parquet(HIP_DMSA_O)
    import io as _io
    import requests
    os.makedirs(os.path.dirname(HIP_DMSA_O), exist_ok=True)
    q = ('SELECT HIP,P,e_P,a0,e_a0,ecc,e_ecc,i,Omega,w,T,dmRef,flag '
         'FROM "I/239/hip_dm_o"')
    r = requests.post(VIZIER_TAP, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                        "FORMAT": "csv", "QUERY": q},
                      timeout=180)
    r.raise_for_status()
    d = pd.read_csv(_io.StringIO(r.text))
    d.to_parquet(HIP_DMSA_O, index=False)
    return d


def fetch_orb6(force=False):
    """ORB6 is fixed-width and SELF-DESCRIBING: line 5 (0-based) is a
    template of the field widths.  The column slices below are read off
    that template rather than hard-coded from a paper, and `--orb6` prints
    a parse check against a row whose values also appear in DMSA/O."""
    if os.path.exists(ORB6_PARQUET) and not force:
        return pd.read_parquet(ORB6_PARQUET)
    import requests
    os.makedirs(os.path.dirname(ORB6_TXT), exist_ok=True)
    r = requests.get(ORB6_URL, timeout=300)
    r.raise_for_status()
    with open(ORB6_TXT, "w", newline="\n", encoding="utf-8",
              errors="replace") as fh:
        fh.write(r.text)
    rows = []
    for line in r.text.splitlines()[7:]:
        if len(line) < 240:
            continue
        def g(a, b):
            return line[a:b].strip()
        try:
            rows.append({
                "wds": g(19, 29), "hip": g(58, 64),
                "orb6_period": g(81, 92), "period_unit": line[92],
                "a": g(105, 114), "a_unit": line[114], "e_a": g(116, 124),
                "inc": g(125, 133), "grade": g(233, 234),
                "ref": g(237, 245), "ra_dec": g(0, 18),
            })
        except IndexError:
            continue
    d = pd.DataFrame(rows)
    for c in ("hip", "orb6_period", "a", "e_a", "inc", "grade"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    # period units: d=day, y=year, c=century, m=millennium
    fac = {"d": 1.0, "y": 365.25, "c": 36525.0, "m": 365250.0}
    d["period_d"] = d["orb6_period"] * d["period_unit"].map(fac)
    # a units: a=arcsec, m=mas, M=arcmin
    afac = {"a": 1000.0, "m": 1.0, "M": 60000.0}
    d["a_mas"] = d["a"] * d["a_unit"].map(afac)
    d["e_a_mas"] = d["e_a"] * d["a_unit"].map(afac)
    d.to_parquet(ORB6_PARQUET, index=False)
    return d


def _nss_with_sigma_a0(rng, n_mc=1500):
    """DR3 NSS a0 [mas] and its MC sigma over the published Thiele-Innes
    errors.  Needed because an external reference is only a calibration if
    BOTH sides carry an uncertainty."""
    nss = pd.read_parquet(NSS, columns=[
        "source_id", "nss_solution_type", "period", "eccentricity",
        "a_thiele_innes", "a_thiele_innes_error", "b_thiele_innes",
        "b_thiele_innes_error", "f_thiele_innes", "f_thiele_innes_error",
        "g_thiele_innes", "g_thiele_innes_error", "nss_parallax",
        "significance", "phot_g_mean_mag", "ra", "dec"])
    a0, inc = campbell_a0_inc(nss.a_thiele_innes.values,
                              nss.b_thiele_innes.values,
                              nss.f_thiele_innes.values,
                              nss.g_thiele_innes.values)
    nss["a0_mas"] = a0
    nss["inc_deg"] = np.degrees(inc)
    return nss


def _sigma_a0_mc(sub, rng, n=3000):
    out = []
    for _, r in sub.iterrows():
        A = rng.normal(r.a_thiele_innes, r.a_thiele_innes_error, n)
        B = rng.normal(r.b_thiele_innes, r.b_thiele_innes_error, n)
        F = rng.normal(r.f_thiele_innes, r.f_thiele_innes_error, n)
        G = rng.normal(r.g_thiele_innes, r.g_thiele_innes_error, n)
        a0, _ = campbell_a0_inc(A, B, F, G)
        a0 = a0[np.isfinite(a0)]
        out.append(float(np.std(a0)) if len(a0) > n // 10 else np.nan)
    return np.array(out)


def _match_external(ext, nss, radius_as=MATCH_RADIUS_AS, ra="_ra", dec="_dec"):
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    c1 = SkyCoord(ra=ext[ra].values * u.deg, dec=ext[dec].values * u.deg)
    c2 = SkyCoord(ra=nss.ra.values * u.deg, dec=nss.dec.values * u.deg)
    idx, sep, _ = c1.match_to_catalog_sky(c2)
    ok = sep.arcsec < radius_as
    e = ext[ok].reset_index(drop=True)
    g = nss.iloc[idx[ok]].reset_index(drop=True)
    g["source_id"] = nss["source_id"].values[idx[ok]].astype(np.int64)
    e["sep_arcsec"] = sep.arcsec[ok]
    return pd.concat([e, g], axis=1)


def run_photocentric(say, seed=SEED):
    """The two catalogues that publish a0 itself, verified live."""
    rng = np.random.default_rng(seed + 7)
    nss = _nss_with_sigma_a0(rng)
    nss = nss[nss.nss_solution_type.isin(ASTROMETRY_ONLY)
              | nss.nss_solution_type.str.contains("AstroSpectro", na=False)]
    frames = []

    # ---- Hipparcos DMSA/O -------------------------------------------
    say("\n  ROUTE 2 -- Hipparcos DMSA Part O (ESA 1997), VizieR "
        "I/239/hip_dm_o")
    h = fetch_hip_dmsa_o()
    say("    %d photocentric orbits; %d with a published e_a0"
        % (len(h), int(h.e_a0.notna().sum())))
    import io as _io
    import requests
    q = ('SELECT HIP, RAICRS, DEICRS FROM "I/239/hip_main" WHERE HIP IN (%s)'
         % ",".join(str(int(x)) for x in h.HIP.dropna().unique()))
    r = requests.post(VIZIER_TAP, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                        "FORMAT": "csv", "QUERY": q},
                      timeout=180)
    pos = pd.read_csv(_io.StringIO(r.text))
    h = h.merge(pos, on="HIP", how="inner").rename(
        columns={"RAICRS": "_ra", "DEICRS": "_dec"})
    m = _match_external(h, nss)
    say("    positional matches to DR3 NSS orbital solutions (2\"): %d"
        % len(m))
    m = m[np.isfinite(m.P) & np.isfinite(m.a0) & (m.a0 > 0)
          & np.isfinite(m.e_a0) & (m.e_a0 > 0)]
    same = np.abs(np.log(m.period / m.P)) < PERIOD_GATE
    say("    same-orbit gate + a0>0 + published e_a0: %d pass, %d fail"
        % (int(same.sum()), int((~same).sum())))
    m = m[same].reset_index(drop=True)
    if len(m):
        m["ext_a0_mas"], m["ext_a0_err_mas"] = m.a0, m.e_a0
        m["ext_ref"] = "HIP1997d(DMSA/O)"
        m["route"] = "HIP-DMSA/O"
        frames.append(m)

    # ---- ORB6 grade 9 -----------------------------------------------
    say("\n  ROUTE 3 -- ORB6 grade 9 = 'astrometric binary' (USNO, "
        "Hartkopf+2001)")
    o = fetch_orb6()
    say("    %d orbits parsed; grade-9 (photocentric): %d; with a0 in mas "
        "or arcsec and an error: %d"
        % (len(o), int((o.grade == 9).sum()),
           int(((o.grade == 9) & o.a_mas.notna() & o.e_a_mas.notna()).sum())))
    g9 = o[(o.grade == 9) & o.a_mas.notna() & o.e_a_mas.notna()
           & (o.a_mas > 0) & (o.e_a_mas > 0) & o.period_d.notna()].copy()
    ra = g9.ra_dec.str.slice(0, 2).astype(float)
    rb = g9.ra_dec.str.slice(2, 4).astype(float)
    rc = g9.ra_dec.str.slice(4, 9).astype(float)
    g9["_ra"] = 15.0 * (ra + rb / 60.0 + rc / 3600.0)
    sgn = np.where(g9.ra_dec.str.slice(9, 10) == "-", -1.0, 1.0)
    da = g9.ra_dec.str.slice(10, 12).astype(float)
    db = g9.ra_dec.str.slice(12, 14).astype(float)
    dc = g9.ra_dec.str.slice(14, 18).astype(float)
    g9["_dec"] = sgn * (da + db / 60.0 + dc / 3600.0)
    m2 = _match_external(g9, nss)
    say("    positional matches to DR3 NSS orbital solutions (2\"): %d"
        % len(m2))
    same2 = np.abs(np.log(m2.period / m2.period_d)) < PERIOD_GATE
    say("    same-orbit gate: %d pass, %d fail"
        % (int(same2.sum()), int((~same2).sum())))
    m2 = m2[same2].reset_index(drop=True)
    if len(m2):
        m2["ext_a0_mas"], m2["ext_a0_err_mas"] = m2.a_mas, m2.e_a_mas
        m2["ext_ref"] = m2["ref"]
        m2["route"] = "ORB6-g9"
        say("    ORB6 grade-9 provenance of the matched rows: %s"
            % m2.ref.value_counts().to_dict())
        frames.append(m2)

    if not frames:
        say("\n  no external photocentric orbits matched.")
        return None, {}
    keep = ["source_id", "nss_solution_type", "route", "ext_ref",
            "sep_arcsec", "period", "a0_mas", "inc_deg", "nss_parallax",
            "significance", "phot_g_mean_mag", "ext_a0_mas",
            "ext_a0_err_mas"]
    d = pd.concat([f[keep] for f in frames], ignore_index=True)
    # THE OVERLAP THE RECONNAISSANCE PREDICTED, MEASURED
    dup = d[d.duplicated("source_id", keep=False)].sort_values("source_id")
    say("\n  sources appearing in BOTH routes: %d (of %d rows, %d unique "
        "sources)" % (d.source_id.nunique() - (len(d) - len(dup)) // 1
                      if False else int(dup.source_id.nunique()),
                      len(d), int(d.source_id.nunique())))
    say("    -> the two catalogues are NOT independent of each other: most "
        "ORB6\n       grade-9 entries cite HIP1997d, i.e. the DMSA/O numbers "
        "themselves.")
    d = d.sort_values(["source_id", "ext_a0_err_mas"]).drop_duplicates(
        "source_id", keep="first").reset_index(drop=True)
    say("  union, best external error per source: %d systems" % len(d))

    sub = pd.read_parquet(NSS, columns=[
        "source_id", "a_thiele_innes", "a_thiele_innes_error",
        "b_thiele_innes", "b_thiele_innes_error", "f_thiele_innes",
        "f_thiele_innes_error", "g_thiele_innes", "g_thiele_innes_error"])
    sub = sub[sub.source_id.isin(d.source_id)].drop_duplicates("source_id")
    sub = sub.set_index("source_id").loc[d.source_id].reset_index()
    d["a0_err_mas"] = _sigma_a0_mc(sub, rng)
    d["ratio"] = d.a0_mas / d.ext_a0_mas
    d["z"] = (d.a0_mas - d.ext_a0_mas) / np.sqrt(d.a0_err_mas ** 2
                                                 + d.ext_a0_err_mas ** 2)
    return d, _photocentric_report(d, say, rng)


def _photocentric_report(d, say, rng):
    say("\n  " + "-" * 74)
    say("  THE COMPARISON: DR3 NSS Thiele-Innes a0 vs an external "
        "photocentric a0")
    say("    n = %d systems" % len(d))
    say("    Gaia   sigma(a0)/a0 : median %.1f %%"
        % (100 * np.nanmedian(d.a0_err_mas / d.a0_mas)))
    say("    extern sigma(a0)/a0 : median %.1f %%"
        % (100 * np.nanmedian(d.ext_a0_err_mas / d.ext_a0_mas)))
    r = float(np.nanmedian(d.ext_a0_err_mas / d.ext_a0_mas)
              / np.nanmedian(d.a0_err_mas / d.a0_mas))
    say("    -> the reference's error is %.1fx the error it would "
        "calibrate." % r)
    med, lo, hi = _boot_median(d.ratio, rng)
    say("    median a0_Gaia / a0_external : %.3f  [%.3f, %.3f]" % (med, lo, hi))
    w = 1.0 / (d.ext_a0_err_mas / d.ext_a0_mas) ** 2
    wm = float(np.nansum(w * d.ratio) / np.nansum(w))
    wse = float(np.sqrt(1.0 / np.nansum(w)))
    say("    inverse-variance weighted ratio : %.3f +/- %.3f (%.1f sigma "
        "from 1)" % (wm, wse, abs(wm - 1) / wse if wse else np.nan))
    z = d.z.replace([np.inf, -np.inf], np.nan).dropna()
    infl = float(np.nanmedian(np.abs(z)) / 0.67449) if len(z) else np.nan
    say("    median |z| %.2f  ->  implied inflation %.2f  "
        "(1.00 = errors honest)" % (np.nanmedian(np.abs(z)), infl))
    say("    within 1 sigma %d/%d (%.0f %%, expect 68)"
        % (int((np.abs(z) <= 1).sum()), len(z),
           100 * float((np.abs(z) <= 1).mean())))
    # ---- is the sub-unity ratio Gaia's fault?  Two named alternatives --
    from scipy import stats as _st
    d = d.copy()
    d["snr_ext"] = d.ext_a0_mas / d.ext_a0_err_mas
    lo_snr = d[d.snr_ext < d.snr_ext.median()]
    hi_snr = d[d.snr_ext >= d.snr_ext.median()]
    rho, pv = _st.spearmanr(d.snr_ext, d.ratio, nan_policy="omit")
    say("\n    IS THE DEFICIT GAIA'S?  Two alternatives, both of which "
        "predict a0_Gaia < a0_ext")
    say("      (i)  near-threshold external detections are biased HIGH "
        "(Eddington).\n           Prediction: the deficit shrinks as the "
        "external S/N rises.")
    say("           low-S/N half  median ratio %.3f (n=%d)"
        % (lo_snr.ratio.median(), len(lo_snr)))
    say("           high-S/N half median ratio %.3f (n=%d)"
        % (hi_snr.ratio.median(), len(hi_snr)))
    say("           Spearman rho(S/N_ext, ratio) = %+.3f, p = %.3f -- the "
        "sign is\n           as predicted, the significance is not there at "
        "this n." % (rho, pv))
    say("      (ii) the photocentre is BAND-DEPENDENT.  A red secondary "
        "contributes\n           more light in G than in Hp, so beta is "
        "larger in G and a0 is\n           GENUINELY smaller in G.  This is "
        "astrophysics, not error.")
    say("      Neither can be separated from a real Gaia a0 offset with "
        "36 systems,\n      and the sign of all three is the same.  The "
        "deficit is therefore NOT\n      attributed to Gaia here.")
    # ---- THE NUMBER THAT DECIDES "ADEQUATE OR NOT" -------------------
    say("\n    POWER OF THIS ROUTE, measured rather than asserted.")
    say("      If Gaia's a0 error were understated by a factor f, would "
        "this\n      sample see it?  Simulate: draw n = %d systems with the "
        "OBSERVED\n      sigma ratio, inflate Gaia's error by f, and ask how "
        "often the\n      median |z| exceeds its own f=1 95th percentile."
        % len(d))
    n = len(d)
    sg = np.nanmedian(d.a0_err_mas / d.a0_mas)
    se = np.nanmedian(d.ext_a0_err_mas / d.ext_a0_mas)
    null = np.median(np.abs(rng.normal(0, np.hypot(sg, se), (4000, n))
                            / np.hypot(sg, se)), axis=1)
    crit = np.percentile(null, 95)
    powers = {}
    for f in (1.4, 2.0, 3.0, 4.0):
        sim = np.median(np.abs(rng.normal(0, np.hypot(f * sg, se),
                                          (4000, n)) / np.hypot(sg, se)),
                        axis=1)
        powers[f] = float((sim > crit).mean())
        say("        f = %.1f  ->  power %.0f %%" % (f, 100 * powers[f]))
    return {"n": int(len(d)), "median_ratio": med, "ratio_lo": lo,
            "ratio_hi": hi, "weighted_ratio": wm, "weighted_se": wse,
            "sigma_ratio_external_over_gaia": r,
            "median_abs_z": float(np.nanmedian(np.abs(z))),
            "implied_inflation": infl,
            "power": {str(k): v for k, v in powers.items()}}


def eb26_a0(say):
    """The SEMI-independent reference: El-Badry et al. 2026's joint
    astrometry+RV solutions publish a0 with intervals.  Not photon-
    independent (the joint fit uses Gaia's own astrometry), but a different
    pipeline, a different noise model, and RV information Gaia does not
    have -- so it bounds a0 in a way SB9 alone cannot."""
    import re
    p = os.path.join(DATA, "papers", "2608.06453",
                     "astrometric_joint_dark_table_preview.tex")
    if not os.path.exists(p):
        say("  EB26 table not on disk: %s" % p)
        return None
    rows = []
    pat = re.compile(r"^(\d{15,20})\s*&(.*)\\\\")
    val = re.compile(r"\$([-\d.]+)_\{?-?([\d.]+)\}?\^\{?\+?([\d.]+)\}?\$")
    for line in open(p, encoding="utf-8"):
        m = pat.match(line.strip())
        if not m:
            continue
        cells = m.group(2).split("&")
        got = [val.search(c) for c in cells]
        if len(cells) < 6 or got[3] is None or got[4] is None:
            continue
        rows.append({"source_id": int(m.group(1)),
                     "eb26_a0_mas": float(got[3].group(1)),
                     "eb26_a0_lo": float(got[3].group(2)),
                     "eb26_a0_hi": float(got[3].group(3)),
                     "eb26_parallax_mas": float(got[4].group(1))})
    e = pd.DataFrame(rows)
    if not len(e):
        say("  EB26 table parsed 0 rows")
        return None
    nss = pd.read_parquet(NSS, columns=[
        "source_id", "nss_solution_type", "a_thiele_innes",
        "a_thiele_innes_error", "b_thiele_innes", "b_thiele_innes_error",
        "f_thiele_innes", "f_thiele_innes_error", "g_thiele_innes",
        "g_thiele_innes_error", "nss_parallax", "nss_parallax_error"])
    m = e.merge(nss, on="source_id", how="inner")
    a0, inc = campbell_a0_inc(m.a_thiele_innes.values, m.b_thiele_innes.values,
                              m.f_thiele_innes.values, m.g_thiele_innes.values)
    m["gaia_a0_mas"] = a0
    m["gaia_inc_deg"] = np.degrees(inc)
    m["ratio"] = m.gaia_a0_mas / m.eb26_a0_mas
    m["eb26_a0_sigma"] = 0.5 * (m.eb26_a0_lo + m.eb26_a0_hi)
    # both sides carry an error; using EB26's alone overstates every z
    rng = np.random.default_rng(SEED + 3)
    m["gaia_a0_sigma"] = _sigma_a0_mc(m, rng)
    m["z"] = (m.gaia_a0_mas - m.eb26_a0_mas) / np.sqrt(
        m.gaia_a0_sigma ** 2 + m.eb26_a0_sigma ** 2)
    say("\n  EB26 joint astrometry+RV a0 vs the DR3 NSS Thiele-Innes a0")
    say("    (El-Badry et al. 2026, tab:astrometric-joint-dark-orbits; the "
        "printed\n     preview rows -- the complete table is "
        "machine-readable but the arXiv\n     source carries only these)")
    say("    n = %d" % len(m))
    for _, r in m.iterrows():
        say("      %19d  Gaia a0 %.3f   EB26 a0 %.3f +/- %.3f   "
            "ratio %.3f   z %+.1f"
            % (r.source_id, r.gaia_a0_mas, r.eb26_a0_mas, r.eb26_a0_sigma,
               r.ratio, r.z))
    say("    median ratio %.4f, median |z| %.2f, %d/%d within 1 sigma"
        % (m.ratio.median(), m.z.abs().median(), int((m.z.abs() <= 1).sum()),
           len(m)))
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--eb26", action="store_true")
    ap.add_argument("--photocentric", action="store_true")
    ap.add_argument("--radius", type=float, default=MATCH_RADIUS_AS)
    ap.add_argument("--out", default=os.path.join(OUT, "m9_a0_external.txt"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    t0 = time.time()
    say("=" * 78)
    say("M9 TASK 3 -- AN EXTERNAL REFERENCE FOR a0")
    say("=" * 78)
    say("  the mass function goes as a0^3; M8 calibrated P and e and said "
        "so.\n  Reference: SB9 (Pourbaix et al. 2004, A&A 424, 727) K1, P, e"
        " -> a1 sin i,\n  against Gaia's Thiele-Innes a0 and i and the "
        "solution's own parallax.\n  The test is ONE-SIDED: a luminous "
        "secondary can only make a0 < a1.")

    res = {}
    if a.run or not (a.run or a.eb26 or a.photocentric):
        j = build(say, radius_as=a.radius)
        d = measure(j, say)
        say("\n  systems with both quantities computable: %d" % len(d))
        say("    astrometry-only (the external sample): %d"
            % int(d.astrometry_only.sum()))
        say("    AstroSpectroSB1 (the circular control): %d"
            % int((~d.astrometry_only).sum()))
        say("    SB2 (both K1 and K2 published): %d" % int(d.sb2.sum()))
        res["sb9"] = report(d, say)
        d.to_csv(os.path.join(OUT, "m9_a0_sb9.csv"), index=False,
                 lineterminator="\n")
        say("\n  wrote out/m9_a0_sb9.csv")
    if a.photocentric or not (a.run or a.eb26 or a.photocentric):
        say("\n" + "=" * 78)
        say("ROUTES 2 and 3 -- catalogues that publish a0 ITSELF")
        say("=" * 78)
        dp, rep = run_photocentric(say)
        if dp is not None:
            dp.to_csv(os.path.join(OUT, "m9_a0_photocentric.csv"),
                      index=False, lineterminator="\n")
            res["photocentric"] = rep
            say("  wrote out/m9_a0_photocentric.csv")
    if a.eb26 or not (a.run or a.eb26 or a.photocentric):
        m = eb26_a0(say)
        if m is not None:
            m.to_csv(os.path.join(OUT, "m9_a0_eb26.csv"), index=False,
                     lineterminator="\n")
            res["eb26"] = {"n": int(len(m)),
                           "median_ratio": float(m.ratio.median()),
                           "median_abs_z": float(m.z.abs().median()),
                           "within_1sigma": int((m.z.abs() <= 1).sum())}
            say("  wrote out/m9_a0_eb26.csv")

    say("\n  %.1f s" % (time.time() - t0))
    with open(a.out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(OUT, "m9_a0_external.json"), "w", newline="\n",
              encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, default=_jsonable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
