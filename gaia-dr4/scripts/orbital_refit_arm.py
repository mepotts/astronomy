#!/usr/bin/env python
"""M7 task 2: the ORBITAL-REFIT ARM -- epoch astrometry to a companion-mass
posterior, as a pipeline instead of a pattern.

WHAT WAS MISSING.  The M6 harness adjudicates `orbit_reality` and stops at
CONFIRMED: "this photocentre orbit has epoch-level support".  That is not
December's headline.  The headline is *the independent orbit and the
companion mass it implies* -- and until now that existed only as
scripts/fit_prerelease_orbit_bh3.py: one hard-coded source, one hard-coded
primary mass, point estimates, a printed text file, no uncertainty on the
companion mass, and no place in the verdict record.  M1 proved the route
works (P 11.45 yr, e 0.728, M2 34.7 Msun against Panuzzo's published 11.6 /
0.729 / 32.70 +/- 0.82).  This turns that route into the arm.

THE ROUTE (unchanged from M1 on purpose -- ESA's own notebook,
esa/gaia-bhthree branch gaia-dr4-prerelease, via kepmodel/spleaf + pystrometry)

  1. gaiasupdate prepares the epoch table: used_by_agis filter, sort by
     obs_time_tcb, relative time, scan-angle derived columns.
  2. kepmodel AstroModel with five linear terms (ra, dec, parallax, mura,
     mudec) -- the single-star model.
  3. periodogram of the single-star residuals -> peak period + FAP.
  4. Keplerian added at the peak, then all seven Campbell elements freed and
     refitted.
  5. a0 [mas] + parallax [mas] -> a1 [m]; pystrometry.pjGet_m2 -> M2.

WHAT THE ARM ADDS
  * it runs from the verdict ledger, over any set of sources, not one id;
  * a COMPANION-MASS POSTERIOR rather than a point estimate.  kepmodel
    exposes the log-likelihood Hessian, so the parameter covariance is
    -inv(H) at the optimum; the arm draws from that multivariate normal,
    draws the primary mass from its own uncertainty, and solves the mass
    function per draw.  That is a Laplace posterior and it is labelled as
    one -- it is not an MCMC and does not claim to be;
  * the M1-FREE observable reported alongside it.  The astrometric mass
    function a0^3/(P_yr^2 * parallax^3) needs no primary mass, so it is the
    number that survives a wrong M1 -- and a wrong M1 is the single most
    likely way this arm produces a confident wrong companion mass;
  * the primary mass taken from the TRIAGE'S OWN three-tier ladder
    (binary_masses IsocLum -> photometric MS -> evolved bracket, config v2+)
    rather than a new chain invented here, with the rung recorded.  The
    candidate list was ranked with that ladder; the mass posterior has to be
    consistent with the ranking or the two cannot be quoted together;
  * output as verdict-record v2 (`scripts/verdict_schema_v2.py`), so a refit
    lands on the same row as the verdict that triggered it.

PRE-REGISTERED ACCEPTANCE (written before the M7 runs; the arm is not
allowed to be used for anything else until it passes).  Re-derive Gaia BH3
through the production arm and reproduce M1's own artifact
`out/bh3_orbit_fit.txt` -- P 11.454 yr, e 0.7278, M2 34.68 Msun -- to within
the reference's PRINTED precision, i.e.

      |dP|  <= 0.005 yr        (M1 printed 3 dp in yr)
      |de|  <= 0.0005          (M1 printed 4 dp)
      |dM2| <= 0.005 Msun      (M1 printed 2 dp)

Set from the reference's own precision, not from a hopeful epsilon (M6
landmine #10).  A separate, non-gating science check compares the same
numbers with Panuzzo et al. 2024 (A&A 686 L2): P 11.6 yr, e 0.729,
MBH 32.70 +/- 0.82 Msun.

Run:
  .venv/Scripts/python.exe scripts/orbital_refit_arm.py --acceptance
  .venv/Scripts/python.exe scripts/orbital_refit_arm.py --trio
"""
import argparse
import copy
import io
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amrf                                                      # noqa: E402
import epoch_vet_harness as H                                    # noqa: E402
import verdict_schema_v2 as v2                                   # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
STORE_V2 = os.path.join(BASE, "out", "verdicts_v2")

ARM_VERSION = "orbital_refit_arm 1.0 (M7, 2026-08-23)"
METHOD = "kepmodel_spleaf_astro"
POSTERIOR_METHOD = ("laplace_mvn_from_loglike_hessian x M1 prior; "
                    "mass function solved per draw")

# periodogram grid -- M1's values, kept so the acceptance is a reproduction
PMIN_D, PMAX_D, NFREQ = 5.0, 10000.0, 10000
FAP_GATE = 1e-3          # pre-registered: no peak below this -> NO_PEAK
N_POSTERIOR = 20000
RNG_SEED = 20261202

# M1 milestone acceptance reference (out/bh3_orbit_fit.txt), and the
# published values it was checked against
BH3_ID = 4318465066420528000
M1_REF = {"P_yr": 11.454, "e": 0.7278, "m2": 34.68}
M1_TOL = {"P_yr": 0.005, "e": 0.0005, "m2": 0.005}
PANUZZO = {"P_yr": 11.6, "e": 0.729, "m2": 32.70, "m2_err": 0.82}

# primary masses that do NOT come from the triage ladder, with provenance.
# BH3's 0.76 Msun is the value ESA's own notebook adopts and the value M1
# reproduced the published orbit with; using anything else would make the
# acceptance test a different measurement.
LITERATURE_M1 = {
    BH3_ID: (0.76, 0.05, "literature:esa_gaia-bhthree_notebook_m1_0.76"),
}

TRIO = {
    4318465066420528000: "Gaia BH3",
    3937211745905473024: "HD 114762",
    1457486023639239296: "Gaia-4",
}

# PUBLISHED reference orbits for the trio, read out of the papers (M7).
# Every number here is sourced; where the literature disagrees with itself
# the disagreement is carried rather than resolved, because the refit's job
# is to land somewhere in it, not to pick a side in advance.
LITERATURE_ORBITS = {
    4318465066420528000: {
        "name": "Gaia BH3",
        "cite": ("Gaia Collaboration: Panuzzo et al. 2024, A&A 686, L2 "
                 "(DOI 10.1051/0004-6361/202449763, arXiv:2404.10486), "
                 "Table 2 ASTROMETRIC-ONLY column"),
        "P_d": (4194.7, 112.3), "ecc": (0.7262, 0.0056),
        "a0_mas": (27.07, 0.56), "parallax_mas": (1.6747, 0.0094),
        "inc_deg": (110.659, 0.107), "omega_deg": (77.77, 0.66),
        "bigomega_deg": (136.200, 0.147),
        "mass_function_msun": (32.03, 0.64),
        "m2_msun": (32.70, 0.82), "m1_msun": (0.76, 0.05),
        "note": ("The published M_BH 32.70 +/- 0.82 comes from the COMBINED "
                 "astrometry+RVS solution via a1 in AU, NOT from a0/parallax "
                 "-- Panuzzo says explicitly that the Table-2 mass-function "
                 "uncertainty is underestimated because the preliminary-NSS "
                 "parallax bias could not be quantified. A photocentre-only "
                 "mass function goes as parallax^-3, so this is the single "
                 "largest systematic the refit arm carries."),
    },
    1457486023639239296: {
        "name": "Gaia-4",
        "cite": ("Stefansson et al. 2025, AJ 169, 107 "
                 "(DOI 10.3847/1538-3881/ada9e1, arXiv:2410.05654), Table 2 "
                 "ADOPTED Gaia+RV column; DR3 NSS column in the same table"),
        "P_d": (571.3, 1.35), "ecc": (0.338, 0.0245),
        "a0_mas": (0.279, 0.015), "parallax_mas": (13.628, 0.021),
        "inc_deg": (116.9, 4.3), "m1_msun": (0.644, 0.024),
        "m2_mjup": (11.8, 0.70),
        "m2_msun": (0.01126, 0.00067),
        "note": ("m2 in Msun is a UNIT CONVERSION of the published 11.8 "
                 "+0.73/-0.66 MJup at 1 MJup = 9.5458e-4 Msun, not a "
                 "published number. The paper's abstract a0 = 0.312 mas is "
                 "the Gaia-ONLY value; the adopted joint a0 is 0.279."),
    },
    3937211745905473024: {
        "name": "HD 114762",
        "cite": ("Winn 2022, arXiv:2209.05516 (AJ volume/page UNVERIFIED), "
                 "joint Gaia DR3 + Doppler WITH the M/L prior; Doppler "
                 "period from the same Table 3"),
        "P_d": (83.91712, 0.00064), "ecc": (0.3442, 0.0012),
        "parallax_mas": (25.35, 0.035), "inc_deg": (3.63, 0.06),
        "m1_msun": (1.00, 0.10), "m2_msun": (0.215, 0.013),
        "note": ("THE LITERATURE CONFLICTS BY A FACTOR ~2 and the conflict "
                 "is the interesting part: Kiefer 2019 gives 108 +31/-26 "
                 "MJup = 0.103 Msun and Kiefer et al. 2021 gives 147 "
                 "+39/-42 MJup = 0.140 Msun (both GASTON excess-noise "
                 "masses), against Winn 2022's 0.215 +/- 0.013 (0.293 "
                 "+0.103/-0.056 without the M/L prior). Winn's own note "
                 "that 'Kiefer 2019 found 0.13 +/- 0.03' misquotes Kiefer's "
                 "uncorrected Table 4 rather than his adopted abstract "
                 "value. a0 is not tabulated by Winn."),
    },
}

ENDPOINTS = ["https://gea.esac.esa.int/tap-server/tap/sync",
             "https://gaia.ari.uni-heidelberg.de/tap/sync"]


# ======================================================================
# mass function <-> companion mass
# ======================================================================
def mass_function_shortcut(a0_mas, period_d, parallax_mas):
    """F = a0^3 / (P_yr^2 * parallax^3)  [Msun] -- the astronomical shortcut,
    which is what M2's AMRF triage and S23 use.  Reported for continuity."""
    p_yr = np.asarray(period_d, float) / 365.25
    return (np.asarray(a0_mas, float) ** 3
            / (p_yr ** 2 * np.asarray(parallax_mas, float) ** 3))


def mass_function_msun(a0_mas, period_d, parallax_mas):
    """F = 4 pi^2 a1^3 / (G P^2)  [Msun], the M1-free observable.

    Computed in pystrometry's OWN constants (AU, Julian day, G, MSun) rather
    than through the a0^3/(P_yr^2 parallax^3) shortcut, because the
    companion mass is then solved from exactly the equation
    pystrometry.pjGet_m2 solves.  The shortcut assumes
    G MSun = 4 pi^2 AU^3 / yr^2 for a particular year and AU and differs
    from the SI chain by ~1e-4 in F (3.6e-5 in M2 on Gaia BH3) -- invisible
    physically, fatal to a bit-exactness claim, and it cost one debugging
    round here.  Both numbers are carried: this one in the record, the
    shortcut in refit_notes.
    """
    from pystrometry.pystrometry import (convert_from_angular_to_linear,
                                         Ggrav, MS_kg, day2sec)
    a_m = convert_from_angular_to_linear(np.asarray(a0_mas, float),
                                         np.asarray(parallax_mas, float))
    p_s = np.asarray(period_d, float) * day2sec
    return 4.0 * np.pi ** 2 * a_m ** 3 / (Ggrav * p_s ** 2) / MS_kg


def m2_from_mass_function(fmass, m1, iters=300, polish=8):
    """Solve M2^3 / (M1 + M2)^2 = F for M2, vectorised.

    Fixed-point iteration M2 <- (F (M1 + M2)^2)^(1/3), then a few Newton
    steps to polish.  NEWTON ALONE IS WRONG HERE and was tried first: the
    natural starting guess (F M1^2)^(1/3) sits left of the turning point of
    h(x) = x^3 - F (M1 + x)^2, where h' is negative, so the first Newton
    step walks away from the root and the iteration collapses onto the
    lower clip.  On Gaia BH3 that produced M2 = 1e-9 instead of 34.68 --
    caught only because every point estimate is cross-checked against
    pystrometry.pjGet_m2 in refit_source(), which is the whole reason that
    cross-check exists.  The fixed-point map is monotone and globally
    convergent for F, M1 > 0.
    """
    fmass = np.asarray(fmass, float)
    m1 = np.asarray(m1, float)
    m2 = np.cbrt(np.clip(fmass, 1e-30, None) * np.clip(m1, 1e-6, None) ** 2)
    for _ in range(iters):
        m2 = np.cbrt(fmass * (m1 + m2) ** 2)
    for _ in range(polish):
        g = m2 ** 3 - fmass * (m1 + m2) ** 2
        dg = 3.0 * m2 ** 2 - 2.0 * fmass * (m1 + m2)
        m2 = np.where(np.abs(dg) > 0, m2 - g / dg, m2)
    return m2


def m2_reference(fmass, m1_msun, a0_mas, period_d, parallax_mas):
    """pystrometry's own solver, exactly as M1 called it."""
    from pystrometry.pystrometry import (convert_from_angular_to_linear,
                                         pjGet_m2, MS_kg)
    a_m = convert_from_angular_to_linear(a0_mas, parallax_mas)
    return float(pjGet_m2(m1_msun * MS_kg, a_m, period_d) / MS_kg)


# ======================================================================
# the primary mass ladder
# ======================================================================
def _tap(adql, first_col="source_id", timeout=180):
    import requests
    for url in ENDPOINTS:
        try:
            r = requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                         "FORMAT": "csv", "QUERY": adql},
                              timeout=timeout)
            r.raise_for_status()
            if not r.text.lstrip().lower().startswith(first_col.lower()):
                continue
            d = pd.read_csv(io.StringIO(r.text))
            d.columns = [c.lower() for c in d.columns]
            return d
        except Exception:                                        # noqa: BLE001
            continue
    return None


def dr3_counterpart(ra_deg, dec_deg, radius_arcsec=1.5):
    """The DR3 row for a pre-release source, matched by POSITION.

    DR3 -> DR4 source_ids are not guaranteed stable (M1 landmine #2), so a
    positional match is the only honest crosswalk for a pre-release id.
    """
    adql = (
        "SELECT TOP 5 g.source_id, g.phot_g_mean_mag, g.bp_rp, g.parallax, "
        "bm.m1 AS bm_m1, bm.m1_ref AS bm_m1_ref, bm.m1_lower AS bm_m1_lower, "
        "bm.m1_upper AS bm_m1_upper, "
        "DISTANCE(POINT('ICRS', g.ra, g.dec), "
        "POINT('ICRS', %.8f, %.8f)) * 3600.0 AS sep_arcsec "
        "FROM gaiadr3.gaia_source AS g "
        "LEFT OUTER JOIN gaiadr3.binary_masses AS bm ON bm.source_id = g.source_id "
        "WHERE 1 = CONTAINS(POINT('ICRS', g.ra, g.dec), "
        "CIRCLE('ICRS', %.8f, %.8f, %.8f)) "
        "ORDER BY sep_arcsec ASC"
        % (ra_deg, dec_deg, ra_deg, dec_deg, radius_arcsec / 3600.0))
    d = _tap(adql)
    if d is None or not len(d):
        return None
    out = d.iloc[0].to_dict()
    # MEASURED LANDMINE (M7).  `DataFrame.iloc[0]` on a mixed-dtype frame
    # upcasts EVERY column to float64, and a Gaia source_id is ~4.3e18 --
    # far past 2^53, so it comes back rounded to the nearest multiple of
    # 512.  Gaia BH3's DR3 id 4318465066420528000 read back as
    # ...528128 and would have been written into `source_id_dr3` as a
    # source that does not exist.  This is the pandas twin of M2's ADQL
    # landmine (#4: bucket arithmetic on source_id rounds past 2^53); the
    # int column has to be taken from the COLUMN, never from the row.
    out["source_id"] = int(d["source_id"].astype("int64").iloc[0])
    return out


def dr3_nss_orbit(dr3_source_id):
    """The DR3 catalogue orbit for a source, as the refit's reference.

    This is the comparison December actually makes: the arm re-derives an
    orbit from epoch astrometry, and the published NSS solution is the thing
    it has to agree with (or knowingly disagree with).  Point estimates and
    the Thiele-Innes a0 through the repo's own frozen converter.
    """
    adql = ("SELECT source_id, nss_solution_type, period, eccentricity, "
            "a_thiele_innes, b_thiele_innes, f_thiele_innes, g_thiele_innes, "
            "parallax, significance FROM gaiadr3.nss_two_body_orbit "
            "WHERE source_id = %d" % int(dr3_source_id))
    d = _tap(adql)
    if d is None or not len(d):
        return None
    rows = []
    for i in range(len(d)):
        r = {k: (None if pd.isna(d[k].iloc[i]) else d[k].iloc[i])
             for k in d.columns if k != "source_id"}
        r["source_id"] = int(d["source_id"].astype("int64").iloc[i])
        try:
            r["a0_mas"] = float(amrf.thiele_innes_a0(
                d["a_thiele_innes"].iloc[i], d["b_thiele_innes"].iloc[i],
                d["f_thiele_innes"].iloc[i], d["g_thiele_innes"].iloc[i]))
        except Exception:                                        # noqa: BLE001
            r["a0_mas"] = None
        rows.append(r)
    return rows


def primary_mass(sid, parallax_mas, g_mag=None, bp_rp=None, dr3=None,
                 triage_row=None):
    """(m1, sigma, rung) from the triage's own three-tier ladder.

    Rungs, highest first -- identical to scripts/amrf_triage.compute_m1:
      literature       an explicitly sourced value for this object
      triage_frame     the value the candidate list was actually ranked with
      binary_masses    gaiadr3.binary_masses m1 with m1_ref = 'IsocLum'
      photometric_ms   the EEM MS relation on (G, parallax[, BP-RP])
      UNSOURCED        nothing on the ladder reached -- reported, never
                       guessed; the mass function is still valid
    """
    if int(sid) in LITERATURE_M1:
        m1, sg, tag = LITERATURE_M1[int(sid)]
        return m1, sg, tag
    if triage_row is not None and pd.notna(triage_row.get("m1_used")):
        return (float(triage_row["m1_used"]),
                float(triage_row.get("m1_sigma", 0.1
                                     * float(triage_row["m1_used"]))),
                "triage_frame:" + str(triage_row.get("m1_source", "?")))
    if dr3 is not None and pd.notna(dr3.get("bm_m1")) \
            and str(dr3.get("bm_m1_ref")) == "IsocLum":
        lo, hi = dr3.get("bm_m1_lower"), dr3.get("bm_m1_upper")
        sg = 0.1 * float(dr3["bm_m1"])
        if pd.notna(lo) and pd.notna(hi):
            sg = max(float(hi - lo) / 2.0, 0.02)
        return float(dr3["bm_m1"]), sg, "binary_masses"
    gm = g_mag if g_mag is not None else (dr3 or {}).get("phot_g_mean_mag")
    br = bp_rp if bp_rp is not None else (dr3 or {}).get("bp_rp")
    if gm is not None and pd.notna(gm) and parallax_mas and parallax_mas > 0:
        mg = amrf.abs_g(gm, parallax_mas)
        m1p = float(amrf.mass_of_mg(mg))
        ms = bool(amrf.is_main_sequence(mg, br)) if br is not None \
            and pd.notna(br) else np.isfinite(m1p)
        if np.isfinite(m1p) and ms:
            return m1p, 0.10 * m1p, "photometric_ms"
    return np.nan, np.nan, "UNSOURCED"


# ======================================================================
# the fit
# ======================================================================
def prepare_epochs(df_raw, sid):
    """gaiasupdate's preparation chain, exactly as ESA's notebook."""
    from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ea = GaiaEpochAstrometryArchive.from_dataframe(df_raw.copy())
        ea.epoch_data = ea.epoch_data.epochastrometryarchive \
            .filter_on_used_by_agis()
        ea.epoch_data.epochastrometryarchive.sort_by_column("obs_time_tcb")
        ea.epoch_data.epochastrometryarchive.set_relative_time()
        ea.epoch_data = ea.epoch_data.epochastrometryarchive \
            .set_scan_angle_derived_columns()
    return ea.epoch_data


def single_star_model(d):
    import spleaf
    from kepmodel.astro import AstroModel
    m = AstroModel(d["relative_time_day"].values,
                   d["centroid_pos_al"].values,
                   d["cos_theta"].values, d["sin_theta"].values,
                   err=spleaf.term.Error(d["centroid_pos_error_al"].values),
                   jit=spleaf.term.Jitter(0.0))
    m.add_lin(d["sin_theta"].values, "ra")
    m.add_lin(d["cos_theta"].values, "dec")
    m.add_lin(d["parallax_factor_al"].values, "parallax")
    m.add_lin(d["relative_time_year"].values * d["sin_theta"].values, "mura")
    m.add_lin(d["relative_time_year"].values * d["cos_theta"].values, "mudec")
    m.fit()
    return m


def peak_period(model, pmin=PMIN_D, pmax=PMAX_D, nfreq=NFREQ):
    nu0 = 2 * np.pi / pmax
    dnu = (2 * np.pi / pmin - nu0) / (nfreq - 1)
    mm = copy.deepcopy(model)
    nu, power = mm.periodogram(nu0, dnu, nfreq)
    k = int(np.argmax(power))
    return float(2 * np.pi / nu[k]), float(mm.fap(power[k], nu.max())), mm


def keplerian_fit(model, p_best):
    kep = copy.deepcopy(model)
    kep.add_keplerian_from_period(p_best)
    kep.fit()
    kep.set_keplerian_param("0", param=["P", "Tp", "as", "e", "w", "i",
                                        "bigw"])
    kep.fit()
    return kep


def posterior_draws(kep, m1, m1_sigma, n=N_POSTERIOR, seed=RNG_SEED,
                    zeropoint_mas=None):
    """Laplace posterior on (P, a0, parallax) x the M1 prior -> M2 draws.

    cov = -inv(loglike_hess) at the optimum, i.e. exactly the matrix
    kepmodel's own get_param_error() takes its error bars from -- so the
    marginals of these draws reproduce the formal errors by construction,
    and the point of drawing rather than propagating is the P-a0-parallax
    COVARIANCE, which the mass function is highly sensitive to.
    """
    names = list(kep.fit_param)
    theta = np.asarray(kep.get_param(names), float)
    hess = kep.loglike_hess(param=names)
    with np.errstate(invalid="ignore"):
        cov = -np.linalg.inv(hess)
    cov = 0.5 * (cov + cov.T)
    # nearest PSD: clip tiny negative eigenvalues from finite differencing
    w, V = np.linalg.eigh(cov)
    bad = int((w < 0).sum())
    w = np.clip(w, 1e-18, None)
    cov = (V * w) @ V.T
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(theta, cov, size=n, method="eigh")
    idx = {nm: i for i, nm in enumerate(names)}
    P = draws[:, idx["kep.0.P"]]
    a0 = draws[:, idx["kep.0.as"]]
    plx = draws[:, idx["lin.parallax"]]
    # M8: the zero-point has to move the POSTERIOR, not only the point
    # estimate.  The first wiring shifted refit_m2_msun and left
    # refit_m2_p16/p84 on the raw parallax, which would have shipped a
    # corrected mass inside an uncorrected interval.
    if zeropoint_mas is not None and np.isfinite(zeropoint_mas):
        plx = plx - float(zeropoint_mas)
    ecc = draws[:, idx["kep.0.e"]]
    good = (P > 0) & (a0 > 0) & (plx > 0) & (ecc >= 0) & (ecc < 1)
    fmass = mass_function_msun(a0[good], P[good], plx[good])
    if np.isfinite(m1) and m1 > 0:
        m1d = rng.normal(m1, max(m1_sigma, 1e-3), size=int(good.sum()))
        m1d = np.clip(m1d, 0.05, None)
    else:
        m1d = np.full(int(good.sum()), np.nan)
    m2 = m2_from_mass_function(fmass, m1d) if np.isfinite(m1) \
        else np.full(int(good.sum()), np.nan)
    return {"fmass": fmass, "m2": m2, "n_draws": int(good.sum()),
            "n_rejected": int((~good).sum()), "n_negative_eig": bad}


# ======================================================================
def zeropoint_for(dr3_source_id):
    """Lindegren+2021 Z [mas] for a DR3 source, or None.

    M8 task 2.  The house pattern lives in scripts/m8_zeropoint.py, which is
    itself a reproduction of the sibling seti-ellipsoid-broker project's
    implementation.  Convention: varpi_true = varpi - Z, Z typically
    negative, corrected parallax LARGER, companion mass SMALLER.
    """
    try:
        import m8_zeropoint as ZP
        d = ZP.load()
        row = d[d["source_id"] == int(dr3_source_id)]
        if not len(row):
            return None
        z = ZP.parallax_zeropoint(
            row["phot_g_mean_mag"].values,
            row["nu_eff_used_in_astrometry"].values,
            row["pseudocolour"].values, row["ecl_lat"].values,
            row["astrometric_params_solved"].values)[0]
        return None if not np.isfinite(z) else float(z)
    except Exception:                                            # noqa: BLE001
        return None


def refit_source(sid, df_raw, m1=None, m1_sigma=None, m1_source=None,
                 n_posterior=N_POSTERIOR, verbose=True, zeropoint_mas=None):
    """One source, raw epoch table in -> one dict of refit_* fields out.

    `zeropoint_mas` (M8): if given, the Lindegren+2021 zero-point is applied
    to the fitted parallax BEFORE the mass function -- which is the only
    place it can be applied, because the mass function goes as parallax^-3.
    Default None reproduces M7 exactly, so the frozen acceptance and the
    frozen trio table are byte-identical without the flag.
    """
    t0 = time.time()
    rec = {c: None for c in v2.REFIT_COLUMNS}
    rec.update({"refit_status": "OK", "refit_method": METHOD,
                "refit_code_version": ARM_VERSION,
                "refit_posterior_method": POSTERIOR_METHOD})
    try:
        d = prepare_epochs(df_raw, sid)
        rec["refit_n_ccd"] = int(len(d))
        single = single_star_model(d)
        rec["refit_rms_single_mas"] = round(float(np.std(single.residuals())),
                                            6)
        p_best, fap, model = peak_period(single)
        rec["refit_peak_period_d"] = round(p_best, 6)
        rec["refit_peak_fap"] = float(fap)
        if not (fap < FAP_GATE):
            rec["refit_status"] = "NO_PEAK"
            rec["refit_notes"] = ("periodogram FAP %.3g >= gate %.1g: no "
                                  "orbit to refit" % (fap, FAP_GATE))
            rec["refit_seconds"] = round(time.time() - t0, 3)
            return rec
        kep = keplerian_fit(model, p_best)
        names = list(kep.fit_param)
        vals, errs = kep.get_param_error(param=names)
        gp = dict(zip(names, vals))
        ge = dict(zip(names, errs))
        plx_raw = float(gp["lin.parallax"])
        plx = plx_raw
        zp_note = ""
        if zeropoint_mas is not None and np.isfinite(zeropoint_mas):
            plx = plx_raw - float(zeropoint_mas)
            zp_note = ("L21 zero-point APPLIED before the mass function: "
                       "Z %+.1f uas, parallax %.6f -> %.6f mas; "
                       % (1e3 * zeropoint_mas, plx_raw, plx))
        rec.update({
            "refit_period_d": round(float(gp["kep.0.P"]), 6),
            "refit_period_err_d": round(float(ge["kep.0.P"]), 6),
            "refit_ecc": round(float(gp["kep.0.e"]), 8),
            "refit_ecc_err": round(float(ge["kep.0.e"]), 8),
            "refit_a0_mas": round(float(gp["kep.0.as"]), 8),
            "refit_a0_err_mas": round(float(ge["kep.0.as"]), 8),
            "refit_inc_deg": round(float(np.degrees(gp["kep.0.i"])), 6),
            "refit_omega_deg": round(float(np.degrees(gp["kep.0.w"])), 6),
            "refit_bigomega_deg": round(float(np.degrees(gp["kep.0.bigw"])), 6),
            "refit_tp_d": round(float(gp["kep.0.Tp"]), 6),
            "refit_parallax_mas": round(plx, 8),
            "refit_parallax_err_mas": round(float(ge["lin.parallax"]), 8),
            "refit_pmra_masyr": round(float(gp["lin.mura"]), 6),
            "refit_pmdec_masyr": round(float(gp["lin.mudec"]), 6),
        })
        fmass = float(mass_function_msun(gp["kep.0.as"], gp["kep.0.P"], plx))
        f_short = float(mass_function_shortcut(gp["kep.0.as"], gp["kep.0.P"],
                                               plx))
        rec["refit_mass_function_msun"] = round(fmass, 8)
        rec["refit_m1_msun"] = None if m1 is None or not np.isfinite(m1) \
            else round(float(m1), 6)
        rec["refit_m1_sigma_msun"] = None if m1_sigma is None \
            or not np.isfinite(m1_sigma) else round(float(m1_sigma), 6)
        rec["refit_m1_source"] = m1_source or "UNSOURCED"
        if m1 is not None and np.isfinite(m1):
            m2_ref = m2_reference(fmass, float(m1), gp["kep.0.as"],
                                  gp["kep.0.P"], plx)
            m2_own = float(m2_from_mass_function(fmass, float(m1)))
            if abs(m2_ref - m2_own) > 1e-6 * max(1.0, abs(m2_ref)):
                raise AssertionError(
                    "internal M2 solver disagrees with pystrometry: "
                    "%.9f vs %.9f" % (m2_own, m2_ref))
            rec["refit_m2_msun"] = round(m2_ref, 6)
            post = posterior_draws(kep, float(m1), float(m1_sigma or 0.1
                                                         * m1),
                                   n=n_posterior,
                                   zeropoint_mas=zeropoint_mas)
            q = np.nanpercentile(post["m2"], [5, 16, 50, 84, 95])
            rec.update({
                "refit_m2_p05": round(float(q[0]), 6),
                "refit_m2_p16": round(float(q[1]), 6),
                "refit_m2_p50": round(float(q[2]), 6),
                "refit_m2_p84": round(float(q[3]), 6),
                "refit_m2_p95": round(float(q[4]), 6),
                "refit_m2_posterior_n": int(post["n_draws"]),
            })
            fq = np.nanpercentile(post["fmass"], [16, 84])
            rec["refit_notes"] = zp_note + (
                "mass function 68%% CI %.4f-%.4f Msun; a0^3/(P_yr^2 plx^3) "
                "shortcut gives %.4f (%.1e rel.); %d/%d draws rejected as "
                "unphysical; %d negative Hessian eigenvalue(s) clipped"
                % (fq[0], fq[1], f_short, abs(f_short - fmass) / fmass,
                   post["n_rejected"],
                   post["n_rejected"] + post["n_draws"],
                   post["n_negative_eig"]))
        else:
            post = posterior_draws(kep, np.nan, np.nan, n=n_posterior,
                                   zeropoint_mas=zeropoint_mas)
            fq = np.nanpercentile(post["fmass"], [16, 84])
            rec["refit_notes"] = zp_note + (
                "M1 UNSOURCED: companion mass not computed. Mass function "
                "(M1-free) %.4f Msun, 68%% CI %.4f-%.4f; shortcut %.4f"
                % (fmass, fq[0], fq[1], f_short))
    except Exception as exc:                                     # noqa: BLE001
        rec["refit_status"] = "FIT_FAILED"
        rec["refit_notes"] = "%s: %s" % (type(exc).__name__, exc)
        if verbose:
            print("    %s: REFIT FAILED %s: %s" % (sid, type(exc).__name__,
                                                   exc))
    rec["refit_seconds"] = round(time.time() - t0, 3)
    return rec


# ======================================================================
def _inventory():
    p = os.path.join(OUT, "source_inventory.csv")
    return pd.read_csv(p).set_index("source_id") if os.path.exists(p) else None


def run_prerelease(ids=None, use_dr3=True, n_posterior=N_POSTERIOR,
                   verbose=True, zeropoint=False):
    """Refit the pre-release sources named in `ids` (default: the trio)."""
    src = H.PrereleaseSource()
    inv = _inventory()
    ids = [int(i) for i in (ids or sorted(TRIO))]
    rows = []
    for sid in ids:
        got = src.fetch([sid])
        if sid not in got:
            rows.append(dict({"source_id": sid}, refit_status="NO_DATA",
                             refit_method=METHOD,
                             refit_code_version=ARM_VERSION))
            continue
        g_mag = plx0 = bp_rp = None
        dr3 = None
        if inv is not None and sid in inv.index:
            g_mag = float(inv.loc[sid, "g_mag_median"])
            if use_dr3:
                dr3 = dr3_counterpart(float(inv.loc[sid, "ra0_deg"]),
                                      float(inv.loc[sid, "dec0_deg"]))
                if dr3 is not None:
                    plx0 = dr3.get("parallax")
                    bp_rp = dr3.get("bp_rp")
        # a first pass to get the fitted parallax, which the photometric
        # rung of the ladder needs; the catalogue parallax is used only if
        # the DR3 counterpart supplied one
        pre = refit_source(sid, got[sid], m1=None, n_posterior=200,
                           verbose=False)
        plx_fit = pre.get("refit_parallax_mas") or plx0
        m1, m1s, rung = primary_mass(sid, plx_fit, g_mag=g_mag, bp_rp=bp_rp,
                                     dr3=dr3)
        zp = None
        if zeropoint and dr3 is not None:
            zp = zeropoint_for(int(dr3["source_id"]))
            if zp is None and verbose:
                print("    %d: no L21 zero-point available (outside the "
                      "validity box, or a 2-parameter solution) -- "
                      "UNCORRECTED" % sid)
        rec = refit_source(sid, got[sid], m1=m1, m1_sigma=m1s,
                           m1_source=rung, n_posterior=n_posterior,
                           verbose=verbose, zeropoint_mas=zp)
        rec["source_id"] = sid
        rec["_name"] = TRIO.get(sid, "")
        rec["_dr3_source_id"] = None if dr3 is None else int(dr3["source_id"])
        rec["_dr3_sep_arcsec"] = None if dr3 is None else float(
            dr3["sep_arcsec"])
        # the catalogue orbit this refit is independent OF
        nss = dr3_nss_orbit(dr3["source_id"]) if (dr3 is not None
                                                  and use_dr3) else None
        if nss:
            n0 = nss[0]
            rec["_nss_solution_type"] = n0.get("nss_solution_type")
            rec["_nss_period_d"] = n0.get("period")
            rec["_nss_ecc"] = n0.get("eccentricity")
            rec["_nss_a0_mas"] = n0.get("a0_mas")
            rec["_nss_parallax_mas"] = n0.get("parallax")
            rec["_nss_significance"] = n0.get("significance")
            rec["_nss_n_solutions"] = len(nss)
        rows.append(rec)
        if verbose:
            print("  %-11s %-19d %-9s P %-10s e %-8s a0 %-8s M1 %-6s "
                  "(%s) -> M2 %s [%s, %s]"
                  % (TRIO.get(sid, ""), sid, rec["refit_status"],
                     rec.get("refit_period_d"), rec.get("refit_ecc"),
                     rec.get("refit_a0_mas"), rec.get("refit_m1_msun"),
                     rec.get("refit_m1_source"), rec.get("refit_m2_msun"),
                     rec.get("refit_m2_p16"), rec.get("refit_m2_p84")))
    return pd.DataFrame(rows)


def acceptance(n_posterior=N_POSTERIOR, verbose=True):
    """The pre-registered gate: BH3 through the production arm vs M1."""
    print("ACCEPTANCE -- Gaia BH3 through the production refit arm")
    print("=" * 72)
    df = run_prerelease(ids=[BH3_ID], n_posterior=n_posterior,
                        verbose=verbose)
    r = df.iloc[0]
    if r.get("refit_status") != "OK" or r.get("refit_m2_msun") is None:
        print("  refit_status %s -- %s" % (r.get("refit_status"),
                                           r.get("refit_notes")))
        print("  -> ACCEPTANCE FAIL (the arm did not produce a mass)")
        return False, df
    got = {"P_yr": float(r["refit_period_d"]) / 365.25,
           "e": float(r["refit_ecc"]), "m2": float(r["refit_m2_msun"])}
    lines, ok = [], True
    for k in ("P_yr", "e", "m2"):
        d = abs(got[k] - M1_REF[k])
        p = d <= M1_TOL[k]
        ok &= p
        lines.append("  %-5s arm %-12.5f  M1 %-9.4f  |d| %-10.6f  tol %-8.4f "
                     " %s" % (k, got[k], M1_REF[k], d, M1_TOL[k],
                              "PASS" if p else "FAIL"))
    print("\n".join(lines))
    print("  -> ACCEPTANCE %s" % ("PASS" if ok else "FAIL"))
    print("\n  non-gating science check vs Panuzzo et al. 2024 (A&A 686 L2):")
    print("    P   %.3f yr   vs published %.1f yr" % (got["P_yr"],
                                                      PANUZZO["P_yr"]))
    print("    e   %.4f      vs published %.3f" % (got["e"], PANUZZO["e"]))
    print("    M2  %.2f Msun vs published %.2f +/- %.2f  (%.1f sigma)"
          % (got["m2"], PANUZZO["m2"], PANUZZO["m2_err"],
             (got["m2"] - PANUZZO["m2"]) / PANUZZO["m2_err"]))
    print("    posterior M2 = %.2f [%.2f, %.2f] (68%%), [%.2f, %.2f] (90%%)"
          % (r["refit_m2_p50"], r["refit_m2_p16"], r["refit_m2_p84"],
             r["refit_m2_p05"], r["refit_m2_p95"]))
    print("    %s" % r["refit_notes"])
    return ok, df


def literature_comparison(refits, out_path=None):
    """Refit vs DR3 catalogue vs published, per element, in sigma.

    Three references, and they are three different things: the DR3
    `nss_two_body_orbit` solution is the orbit the day-one queue is BUILT
    from, the published joint solution is the best external truth, and the
    refit is what this pipeline claims.  A refit that matches the catalogue
    is reproducing; a refit that matches the published joint solution
    better than the catalogue does is adding something.
    """
    rows = []
    for _, r in refits.iterrows():
        sid = int(r["source_id"])
        lit = LITERATURE_ORBITS.get(sid, {})
        for key, lab in (("P_d", "refit_period_d"), ("ecc", "refit_ecc"),
                         ("a0_mas", "refit_a0_mas"),
                         ("parallax_mas", "refit_parallax_mas"),
                         ("inc_deg", "refit_inc_deg"),
                         ("omega_deg", "refit_omega_deg"),
                         ("bigomega_deg", "refit_bigomega_deg"),
                         ("mass_function_msun", "refit_mass_function_msun"),
                         ("m1_msun", "refit_m1_msun"),
                         ("m2_msun", "refit_m2_msun")):
            got = r.get(lab)
            pub = lit.get(key)
            nss = {"P_d": r.get("_nss_period_d"), "ecc": r.get("_nss_ecc"),
                   "a0_mas": r.get("_nss_a0_mas"),
                   "parallax_mas": r.get("_nss_parallax_mas")}.get(key)
            if got is None or (pub is None and nss is None):
                continue
            row = {"name": lit.get("name", TRIO.get(sid, "")),
                   "source_id": sid, "element": key, "refit": got,
                   "published": None if pub is None else pub[0],
                   "published_err": None if pub is None else pub[1],
                   "dr3_nss": nss}
            # the refit's OWN formal (Hessian/Laplace) error, where it has
            # one -- this is the column that calibrates whether the arm's
            # error bars can be believed
            errcol = {"refit_period_d": "refit_period_err_d",
                      "refit_ecc": "refit_ecc_err",
                      "refit_a0_mas": "refit_a0_err_mas",
                      "refit_parallax_mas": "refit_parallax_err_mas"}.get(lab)
            sig_own = r.get(errcol) if errcol else None
            row["refit_formal_err"] = sig_own
            if pub is not None and pub[1]:
                row["sigma_vs_published"] = round((got - pub[0]) / pub[1], 2)
                if sig_own is not None and pd.notna(sig_own) and sig_own > 0:
                    row["delta_over_refit_formal_err"] = round(
                        (got - pub[0]) / sig_own, 2)
            if nss is not None and pd.notna(nss) and nss:
                row["frac_vs_dr3_nss"] = round((got - nss) / nss, 4)
            rows.append(row)
    out = pd.DataFrame(rows)
    out_path = out_path or os.path.join(OUT, "m7_refit_vs_literature.csv")
    out.to_csv(out_path, index=False, lineterminator="\n")
    print("\nREFIT vs DR3 CATALOGUE vs PUBLISHED")
    print(out.to_string(index=False))
    # ---- the calibration that matters more than any single row ----------
    # How far off is the arm, in units of ITS OWN claimed error?  If the
    # Laplace error bars were honest this would be ~1 and ~68 % of the rows
    # would fall inside 1.  It is the only external check the arm has, and
    # it is the number December must quote next to every mass.
    z = out["delta_over_refit_formal_err"].dropna().abs()
    if len(z):
        print("\n  ERROR-BAR CALIBRATION (|refit - published| / the refit's "
              "OWN formal error)")
        print("    n = %d elements with both a published value and a formal "
              "error" % len(z))
        print("    median %.2f | max %.2f | within 1 sigma %d/%d (%.0f %%, "
              "expect 68) | within 2 sigma %d/%d (%.0f %%, expect 95)"
              % (z.median(), z.max(), int((z <= 1).sum()), len(z),
                 100.0 * (z <= 1).mean(), int((z <= 2).sum()), len(z),
                 100.0 * (z <= 2).mean()))
        print("    -> the Laplace/Hessian errors are LOWER BOUNDS. An "
              "inflation factor of about")
        print("       %.1fx would make this trio self-consistent. Quote the "
              "posterior as a" % z.median())
        print("       formal interval, never as a total uncertainty.")
    plx = out[out["element"] == "parallax_mas"]
    plx = plx[plx["published"].notna()]
    if len(plx):
        d_uas = (plx["refit"] - plx["published"]) * 1000.0
        print("\n  PARALLAX OFFSET, all %d targets: %s uas (refit minus "
              "published)"
              % (len(plx), ", ".join("%+.1f" % v for v in d_uas)))
        # M8: this line used to assert "every one NEGATIVE" unconditionally.
        # With --zeropoint the offsets change sign and the sentence became a
        # log line that lied.  It is now read off the numbers -- and the
        # comparison itself needs a health warning, because the published
        # parallaxes here are NOT zero-point corrected (Panuzzo Table 2, and
        # the Letter says why), so a corrected refit is deliberately being
        # compared against an uncorrected reference.  The apples-to-apples
        # test is against Panuzzo's zero-point-FREE a0/a1 parallax, and that
        # lives in scripts/m8_zeropoint_effect.py section Z2.
        sgn = ("every one NEGATIVE" if (d_uas < 0).all()
               else "every one POSITIVE" if (d_uas > 0).all()
               else "MIXED SIGN")
        print("    %s, magnitudes %.0f-%.0f uas -- the Lindegren+2021 "
              "zero-point"
              % (sgn, d_uas.abs().min(), d_uas.abs().max()))
        print("    scale.  The photocentre mass function goes as "
              "parallax^-3, so this propagates")
        print("    to about %.1f %% on every companion mass and is the "
              "arm's dominant systematic."
              % (100.0 * (abs(3.0 * (d_uas / 1000.0
                                     / plx["published"])).mean())))
    for sid, lit in LITERATURE_ORBITS.items():
        print("\n  [%s] %s" % (lit["name"], lit["cite"]))
        print("      %s" % lit["note"])
    return out


def build_v2_store(refits, ledger=None, out_path=None):
    """Attach refit rows to the harness verdict records -> a v2 store file."""
    ledger = ledger or os.path.join(OUT, "verdicts",
                                    "harness_prerelease.v1.csv")
    base = v2.upgrade(pd.read_csv(ledger))
    r = refits.drop(columns=[c for c in refits.columns
                             if c.startswith("_")], errors="ignore")
    keep = ["source_id"] + [c for c in v2.REFIT_COLUMNS if c in r.columns]
    m = base.drop(columns=v2.REFIT_COLUMNS).merge(r[keep], on="source_id",
                                                  how="left")
    m["refit_status"] = m["refit_status"].fillna("SKIPPED")
    m = v2.coerce(m)
    v2.validate(m)
    out_path = out_path or os.path.join(STORE_V2,
                                        "harness_prerelease_refit.v2.csv")
    v2.write_store(m, out_path)
    return m, out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--acceptance", action="store_true")
    ap.add_argument("--trio", action="store_true")
    ap.add_argument("--ids", default=None,
                    help="comma-separated pre-release source_ids")
    ap.add_argument("--n-posterior", type=int, default=N_POSTERIOR)
    ap.add_argument("--zeropoint", action="store_true",
                    help="apply the Lindegren+2021 parallax zero-point "
                         "before the mass function (M8). DEFAULT OFF so the "
                         "frozen M7 acceptance reproduces byte-identically; "
                         "DECEMBER MUST PASS IT -- see DR4-DAY-RUNBOOK 3.4")
    ap.add_argument("--no-dr3", action="store_true",
                    help="skip the positional DR3 crossmatch for M1")
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)

    outdir = a.out_dir or OUT
    os.makedirs(outdir, exist_ok=True)
    status = 0

    if a.acceptance:
        ok, df = acceptance(n_posterior=a.n_posterior)
        with open(os.path.join(outdir, "m7_refit_acceptance.json"), "w",
                  newline="\n") as fh:
            json.dump({"acceptance_pass": bool(ok),
                       "reference": M1_REF, "tolerance": M1_TOL,
                       "published": PANUZZO,
                       "arm_version": ARM_VERSION,
                       "produced_utc": v2.utcnow(),
                       "row": {k: (None if pd.isna(v) else
                                   (v.item() if hasattr(v, "item") else v))
                               for k, v in df.iloc[0].items()}}, fh, indent=2)
        status |= 0 if ok else 1

    if a.trio or a.ids:
        ids = [int(x) for x in a.ids.split(",")] if a.ids else None
        print("\nORBITAL REFIT ARM -- pre-release orbit trio")
        print("=" * 72)
        df = run_prerelease(ids=ids, use_dr3=not a.no_dr3,
                            n_posterior=a.n_posterior,
                            zeropoint=a.zeropoint)
        p = os.path.join(outdir, "m7_refit_trio.csv")
        df.to_csv(p, index=False, lineterminator="\n")
        print("wrote %s" % os.path.relpath(p, BASE))
        # LANDMINE (M8), second instance in this file: literature_comparison
        # also defaulted to out/, so `--trio --out-dir <scratch>` wrote its
        # comparison table over the FROZEN M7 one.  Caught by `git status`
        # at close, which is why the close-out check exists.
        literature_comparison(
            df, out_path=(os.path.join(outdir, "m7_refit_vs_literature.csv")
                          if a.out_dir else None))
        # LANDMINE (M8): build_v2_store defaults to out/verdicts_v2/, so a
        # run given --out-dir wrote its trio table into the scratch directory
        # and its v2 STORE straight over the frozen one.  Same family as M7
        # landmine #14 -- a script that writes outside the directory it was
        # told to write in.  An explicit --out-dir now contains everything.
        m, sp = build_v2_store(
            df, out_path=(os.path.join(outdir,
                                       "harness_prerelease_refit.v2.csv")
                          if a.out_dir else None))
        print("v2 store: %s (%d records, %d with a refit)"
              % (os.path.relpath(sp, BASE), len(m),
                 int((m["refit_status"] == "OK").sum())))
    return status


if __name__ == "__main__":
    sys.exit(main())
