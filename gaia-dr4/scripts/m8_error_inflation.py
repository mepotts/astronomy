#!/usr/bin/env python
"""M8 task 1: the ERROR-INFLATION FACTOR, measured on a real sample.

WHAT M7 LEFT.  M7 section 2e-i measured |refit - published| / (the refit's own
formal sigma) on **11 elements from 3 objects**: median 2.28, max 6.16, only
4 of 11 inside 1 sigma.  It concluded that the arm's Laplace/Hessian error
bars are lower bounds by a factor ~2.3.  December has to quote an inflation
factor beside every companion mass, and 2.3-from-three-objects is not a
number anyone should publish.

WHAT CANNOT BE DONE, AND WHY -- state it before anything else.
The literal M8 ask was "run the refit arm at queue scale on DR3 NSS".  The
arm's first half consumes EPOCH ASTROMETRY.  **Gaia DR3 publishes no stellar
epoch astrometry at all** -- DR4 is the first release that will, it is
DataLink-only (M1 landmine #1), and the only epoch astrometry in existence
today is the 12-source 2026-06-26 pre-release file.  So the arm's Keplerian
half cannot be run over hundreds of DR3 sources by anyone, in this repository
or outside it, before 2026-12-02.  Saying so is the honest first result of
this task; everything below is what CAN be measured, and each route is
labelled with what it does and does not bound.

FOUR ROUTES, three of them at real scale:

  S1  EXTERNAL, at scale -- Gaia DR3 NSS vs SB9.
      The Ninth Catalogue of Spectroscopic Binary Orbits (Pourbaix et al.
      2004, A&A 424, 727; CDS B/sb9, live-pulled) is ground-based
      spectroscopy: genuinely independent data, independent reduction,
      published uncertainties on P, e and T0.  This is the only route here
      whose reference shares no photons with the thing being tested, and it
      is the one that carries the headline number.  It measures the
      **catalogue's** formal errors, not the arm's -- see S3 for why that is
      the right proxy and where it stops being one.

  S2  INTERNAL REPLICATION, at scale -- the 98 DR3 sources that carry TWO
      astrometric orbital solutions (M2 landmine #4).  Two NSS pipelines,
      two solution types, one star.  Their errors are CORRELATED because
      they share the same astrometry, so this is a LOWER BOUND on the
      inflation factor and is reported as one.

  S3  INJECTION-RECOVERY THROUGH THE ARM ITSELF, at scale.  Real pre-release
      scan geometry (times, scan angles, parallax factors, per-CCD sigma) +
      a known injected Keplerian + Gaussian noise -> the arm's own
      single_star_model / periodogram / keplerian_fit / get_param_error
      chain -> recovered minus injected, in units of the arm's own formal
      sigma.  This is the ONLY route that measures the Laplace error bar
      itself.  Under a perfectly specified model it must return ~1.0 by
      construction; that is not a null result, it is the discriminator --
      if it returns 1.0 then M7's 2.3 is model misspecification and real
      data complexity, not a broken Hessian, and the inflation factor is a
      property of the DATA rather than of the code.  The misspecified arm
      (injected jitter the fitter is not told about) brackets the other end.

  S4  THE M7 ANCHOR -- the same 11 published-comparison elements,
      recomputed here so that the new numbers and the old one sit in one
      table.

PRE-REGISTERED RULES, written before any z-distribution was looked at:

  * SB9 crossmatch radius **2.0 arcsec** (SB9 positions are J2000, Gaia's
    are J2016; a 16-year proper-motion drift is the reason it is not
    tighter).  The 1/3/5/10 arcsec variants are reported as a sensitivity
    strip, never chosen after the fact.
  * SB9 systems with more than one orbit: take the one with the **best
    Grade** (SB9's own quality flag, 5 = best), ties broken by the larger
    number of RVs `o_K1`.
  * **SAME-ORBIT GATE**: a pair enters the error test only if
    |ln(P_gaia / P_sb9)| < 0.05.  Outside it the two catalogues are
    describing different periods (aliases, or the wrong star) and the
    difference is not an error-bar question.  The number excluded is
    REPORTED, not hidden -- it is itself a result about Gaia NSS periods.
  * An element enters only if BOTH sides publish a finite, strictly
    positive uncertainty.
  * The inflation factor is **median|z| / 0.67449**, the ratio that would
    make the observed median |z| that of a standard normal.  It is reported
    with a bootstrap 68 % interval (5,000 resamples, seed 20261202), beside
    the raw coverage fractions, because a single ratio hides a fat tail.
  * Coverage is reported as the fraction with |z| < 1 and |z| < 2 against
    the normal expectations 68.27 % and 95.45 %.

Run:
  .venv/Scripts/python.exe scripts/m8_error_inflation.py --all
  .venv/Scripts/python.exe scripts/m8_error_inflation.py --sb9 --duals --anchor
  .venv/Scripts/python.exe scripts/m8_error_inflation.py --injection --n-inject 240
"""
import argparse
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
DATA = os.path.join(BASE, "data")
SB9_DIR = os.path.join(DATA, "sb9")

NSS_PARQUET = os.path.join(DATA, "dr3_nss_amrf_input.parquet")
TRIAGE_PARQUET = os.path.join(DATA, "dr3_amrf_triage.parquet")

MATCH_RADIUS_AS = 2.0
MATCH_RADIUS_STRIP = [1.0, 2.0, 3.0, 5.0, 10.0]
SAME_ORBIT_LNP = 0.05
NORMAL_MEDIAN_ABS = 0.6744897501960817
SEED = 20261202
N_BOOT = 5000


# ======================================================================
# shared statistics
# ======================================================================
def inflation(z, rng=None, n_boot=N_BOOT):
    """median|z| / 0.67449 with a bootstrap 68 % interval."""
    z = np.asarray(z, float)
    z = z[np.isfinite(z)]
    if len(z) < 3:
        return dict(n=len(z), factor=np.nan, lo=np.nan, hi=np.nan,
                    med_abs_z=np.nan, cov1=np.nan, cov2=np.nan,
                    max_abs_z=np.nan, mean_z=np.nan)
    rng = rng or np.random.default_rng(SEED)
    f = np.median(np.abs(z)) / NORMAL_MEDIAN_ABS
    bs = np.array([np.median(np.abs(rng.choice(z, len(z), replace=True)))
                   for _ in range(n_boot)]) / NORMAL_MEDIAN_ABS
    return dict(n=int(len(z)), factor=float(f),
                lo=float(np.percentile(bs, 16)),
                hi=float(np.percentile(bs, 84)),
                med_abs_z=float(np.median(np.abs(z))),
                cov1=float(np.mean(np.abs(z) < 1)),
                cov2=float(np.mean(np.abs(z) < 2)),
                max_abs_z=float(np.nanmax(np.abs(z))),
                mean_z=float(np.mean(z)))


def fmt_inflation(tag, s):
    if not np.isfinite(s["factor"]):
        return f"  {tag:<34s} n={s['n']:<4d} (too few)"
    return (f"  {tag:<34s} n={s['n']:<4d} med|z| {s['med_abs_z']:5.2f}  "
            f"inflation {s['factor']:5.2f} [{s['lo']:.2f}, {s['hi']:.2f}]   "
            f"|z|<1 {100*s['cov1']:5.1f}%  |z|<2 {100*s['cov2']:5.1f}%  "
            f"max|z| {s['max_abs_z']:7.2f}")


def zscore(x1, e1, x2, e2):
    with np.errstate(invalid="ignore", divide="ignore"):
        return (np.asarray(x1, float) - np.asarray(x2, float)) / np.sqrt(
            np.asarray(e1, float) ** 2 + np.asarray(e2, float) ** 2)


# ======================================================================
# S1 -- SB9
# ======================================================================
def fetch_sb9(force=False):
    """CDS B/sb9 via VizieR, cached to data/sb9/*.parquet."""
    need = ["B_sb9_main", "B_sb9_orbits"]
    paths = {n: os.path.join(SB9_DIR, n + ".parquet") for n in need}
    if all(os.path.exists(p) for p in paths.values()) and not force:
        return {n: pd.read_parquet(p) for n, p in paths.items()}
    from astroquery.vizier import Vizier
    os.makedirs(SB9_DIR, exist_ok=True)
    v = Vizier(columns=["**"], row_limit=-1)
    for t in v.get_catalogs("B/sb9"):
        nm = t.meta.get("name").replace("/", "_")
        t.to_pandas().to_parquet(os.path.join(SB9_DIR, nm + ".parquet"),
                                 index=False)
    return {n: pd.read_parquet(p) for n, p in paths.items()}


def sb9_best_orbits(orb):
    """One orbit per SB9 Seq: best Grade, ties to the larger o_K1."""
    o = orb.copy()
    for c in ("Grade", "o_K1"):
        o[c] = pd.to_numeric(o[c], errors="coerce").fillna(-1)
    o = o.sort_values(["Seq", "Grade", "o_K1"],
                      ascending=[True, False, False])
    return o.drop_duplicates("Seq", keep="first")


def sb9_match(nss, radius_as=MATCH_RADIUS_AS):
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    tabs = fetch_sb9()
    main, orb = tabs["B_sb9_main"], sb9_best_orbits(tabs["B_sb9_orbits"])
    c1 = SkyCoord(ra=main.RAJ2000.values, dec=main.DEJ2000.values,
                  unit=(u.hourangle, u.deg))
    c2 = SkyCoord(ra=nss.ra.values * u.deg, dec=nss.dec.values * u.deg)
    idx, sep, _ = c1.match_to_catalog_sky(c2)
    ok = sep.arcsec < radius_as
    m = main.loc[ok, ["Seq", "mag1"]].reset_index(drop=True)
    m["sep_arcsec"] = sep.arcsec[ok]
    g = nss.iloc[idx[ok]].reset_index(drop=True)
    g["source_id"] = nss["source_id"].values[idx[ok]].astype(np.int64)
    j = pd.concat([m, g], axis=1)
    j = j.merge(orb, on="Seq", how="inner", suffixes=("", "_sb9"))
    return j


def run_sb9(say):
    say("\n" + "=" * 78)
    say("S1  EXTERNAL REFERENCE AT SCALE -- Gaia DR3 NSS vs SB9")
    say("=" * 78)
    say("  reference: Pourbaix et al. 2004, A&A 424, 727 -- the Ninth "
        "Catalogue of\n            Spectroscopic Binary Orbits, CDS B/sb9 "
        "(VizieR, anonymous).\n            Ground-based spectroscopy: it "
        "shares no photons with Gaia.")
    cols = ["source_id", "nss_solution_type", "period", "period_error",
            "eccentricity", "eccentricity_error", "t_periastron",
            "t_periastron_error", "significance", "phot_g_mean_mag",
            "goodness_of_fit", "astrometric_n_good_obs_al", "ra", "dec",
            "nss_parallax", "nss_parallax_error"]
    nss = pd.read_parquet(NSS_PARQUET, columns=cols)

    say("\n  crossmatch radius sensitivity strip (the pre-registered radius "
        "is 2.0\"):")
    strip = []
    for r in MATCH_RADIUS_STRIP:
        j = sb9_match(nss, r)
        strip.append((r, len(j)))
        say(f"    {r:5.1f}\"  {len(j):4d} matched systems")
    j = sb9_match(nss, MATCH_RADIUS_AS)

    # SB9 period is in days; T0 in HJD-2400000 for most rows.  Only P and e
    # are compared -- T0 carries an epoch-convention risk that is not worth
    # a milestone, and it is said out loud rather than silently dropped.
    j["P_sb9"] = pd.to_numeric(j["Per"], errors="coerce")
    j["eP_sb9"] = pd.to_numeric(j["e_Per"], errors="coerce")
    j["e_sb9"] = pd.to_numeric(j["e"], errors="coerce")
    j["ee_sb9"] = pd.to_numeric(j["e_e"], errors="coerce")

    lnp = np.log(j["period"].values / j["P_sb9"].values)
    j["ln_period_ratio"] = lnp
    same = np.abs(lnp) < SAME_ORBIT_LNP
    j["same_orbit"] = same
    say(f"\n  matched systems at 2.0\": {len(j)}")
    say(f"  SAME-ORBIT GATE |ln(P_gaia/P_sb9)| < {SAME_ORBIT_LNP}: "
        f"{int(same.sum())} pass, {int((~same).sum())} fail")
    if (~same).sum():
        bad = j.loc[~same, "ln_period_ratio"].values
        near2 = int(np.sum(np.abs(np.abs(bad) - np.log(2)) < 0.1))
        nearhalf = int(np.sum(np.abs(bad + np.log(2)) < 0.1))
        say(f"    of the {int((~same).sum())} failures, {near2 + nearhalf} "
            f"sit within 10 % of a factor-2 period alias "
            f"({near2} at 2x, {nearhalf} at 1/2x) -- the classic "
            f"astrometric-orbit alias, and a result in its own right")
    s = j[same].copy()

    rows = []
    for el, gv, ge, sv, se in [
            ("period_d", "period", "period_error", "P_sb9", "eP_sb9"),
            ("eccentricity", "eccentricity", "eccentricity_error",
             "e_sb9", "ee_sb9")]:
        v = s[[gv, ge, sv, se, "nss_solution_type", "phot_g_mean_mag",
               "significance", "source_id"]].copy()
        v = v[(v[ge] > 0) & (v[se] > 0)]
        v["z"] = zscore(v[gv], v[ge], v[sv], v[se])
        v["element"] = el
        v["rel_diff"] = (v[gv] - v[sv]) / v[sv].replace(0, np.nan)
        rows.append(v.rename(columns={gv: "gaia", ge: "gaia_err",
                                      sv: "ref", se: "ref_err"})[
            ["source_id", "element", "gaia", "gaia_err", "ref", "ref_err",
             "z", "rel_diff", "nss_solution_type", "phot_g_mean_mag",
             "significance"]])
    z = pd.concat(rows, ignore_index=True)
    z.to_csv(os.path.join(OUT, "m8_inflation_sb9.csv"), index=False,
             lineterminator="\n")

    rng = np.random.default_rng(SEED)
    say("\n  INFLATION FACTOR (median|z| / 0.67449; bootstrap 68 % interval)")
    all_s = inflation(z["z"].values, rng)
    say(fmt_inflation("ALL elements pooled", all_s))
    for el, sub in z.groupby("element"):
        say(fmt_inflation(f"  by element: {el}", inflation(sub["z"].values,
                                                           rng)))
    say("\n  TRENDS -- does the factor depend on anything?")
    say("   by NSS solution type:")
    for k, sub in z.groupby("nss_solution_type"):
        say(fmt_inflation(f"     {k}", inflation(sub["z"].values, rng)))
    _trend(say, z, "phot_g_mean_mag", "G magnitude", rng)
    per = z.merge(s[["source_id", "period"]].drop_duplicates("source_id"),
                  on="source_id", how="left")
    _trend(say, per, "period", "period (d)", rng, log=True)
    _trend(say, z, "significance", "NSS significance", rng, log=True)
    rw = queue_reweight(say, z, rng)
    all_s = dict(all_s)
    all_s["queue_reweighted_factor"] = rw
    return z, j, all_s


def queue_reweight(say, z, rng, col="significance",
                   edges=(0, 20, 40, 80, 160, 1e9)):
    """The SB9 sample is not the day-one queue and must not be quoted as if
    it were: SB9's stars are bright spectroscopic binaries (median G 8.4)
    while the queue's median G is 15.0, and SB9's Gaia solutions are more
    significant (median 65 vs the queue's 34).  This reweights the per-bin
    median |z| by the QUEUE's own distribution in `col`, which is the number
    that applies to what December will actually refit."""
    q = pd.read_csv(os.path.join(OUT, "epoch_vet_day1_queue.v2.csv"))
    zb = np.digitize(z[col].values, edges)
    qb = np.digitize(q[col].values, edges)
    num = den = 0.0
    say("")
    say(f"  REWEIGHTED TO THE QUEUE'S OWN {col} DISTRIBUTION")
    say(f"    {'bin':<18s} {'n_ref':>6s} {'med|z|':>8s} {'queue frac':>11s}")
    for b in range(1, len(edges)):
        sub = z[zb == b]
        w = float((qb == b).mean())
        tag = (f"{edges[b-1]:.0f}-{edges[b]:.0f}" if edges[b] < 1e8
               else f">{edges[b-1]:.0f}")
        if len(sub) >= 8:
            m = float(np.median(np.abs(sub["z"].values)))
            num += w * m
            den += w
            say(f"    {tag:<18s} {len(sub):>6d} {m:>8.3f} {w:>11.3f}")
        else:
            say(f"    {tag:<18s} {len(sub):>6d} {'(too few)':>8s} {w:>11.3f}")
    if den <= 0:
        return np.nan
    mz = num / den
    f = mz / NORMAL_MEDIAN_ABS
    say(f"    -> queue-reweighted median|z| {mz:.3f}, inflation {f:.2f} "
        f"(raw, unweighted: "
        f"{np.median(np.abs(z['z'].values))/NORMAL_MEDIAN_ABS:.2f})")
    return f


def _trend(say, z, col, label, rng, log=False, nbin=4):
    v = z[np.isfinite(z[col].values)].copy()
    if len(v) < 4 * nbin:
        nbin = max(2, len(v) // 12)
    if len(v) < 8:
        say(f"   by {label}: too few rows")
        return
    qs = np.nanpercentile(v[col].values, np.linspace(0, 100, nbin + 1))
    qs[0] -= 1e-9
    qs[-1] += 1e-9
    say(f"   by {label} (quartiles):")
    for i in range(nbin):
        sub = v[(v[col] > qs[i]) & (v[col] <= qs[i + 1])]
        tag = (f"     {qs[i]:.4g}-{qs[i+1]:.4g}" if not log
               else f"     {qs[i]:.4g}-{qs[i+1]:.4g}")
        say(fmt_inflation(tag, inflation(sub["z"].values, rng)))


# ======================================================================
# S2 -- internal replication
# ======================================================================
DUAL_ELEMENTS = ["period", "eccentricity", "t_periastron", "a_thiele_innes",
                 "b_thiele_innes", "f_thiele_innes", "g_thiele_innes",
                 "nss_parallax"]


def run_duals(say):
    say("\n" + "=" * 78)
    say("S2  INTERNAL REPLICATION AT SCALE -- the 98 dual-solution sources")
    say("=" * 78)
    say("  Two NSS solution types, one star, one set of Gaia astrometry.\n"
        "  Their errors are CORRELATED (shared photons), so the factor "
        "below is a\n  LOWER BOUND on the true inflation and is reported "
        "as one.")
    cols = (["source_id", "nss_solution_type", "significance",
             "phot_g_mean_mag"]
            + DUAL_ELEMENTS + [e + "_error" for e in DUAL_ELEMENTS])
    d = pd.read_parquet(NSS_PARQUET, columns=cols)
    vc = d.source_id.value_counts()
    dup = vc[vc > 1].index
    s = d[d.source_id.isin(dup)]
    a = s[s.nss_solution_type == "AstroSpectroSB1"].set_index("source_id")
    b = s[s.nss_solution_type != "AstroSpectroSB1"].set_index("source_id")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    say(f"\n  pairs: {len(common)}  "
        f"({dict(b.nss_solution_type.value_counts())} vs AstroSpectroSB1)")
    rows = []
    for el in DUAL_ELEMENTS:
        z = zscore(a[el].values, a[el + "_error"].values,
                   b[el].values, b[el + "_error"].values)
        rows.append(pd.DataFrame({
            "source_id": common.values.astype(np.int64), "element": el,
            "gaia": a[el].values, "gaia_err": a[el + "_error"].values,
            "ref": b[el].values, "ref_err": b[el + "_error"].values, "z": z,
            "nss_solution_type": b["nss_solution_type"].values,
            "phot_g_mean_mag": a["phot_g_mean_mag"].values,
            "significance": a["significance"].values}))
    z = pd.concat(rows, ignore_index=True)
    z.to_csv(os.path.join(OUT, "m8_inflation_duals.csv"), index=False,
             lineterminator="\n")
    rng = np.random.default_rng(SEED)
    say("\n  INFLATION FACTOR (lower bound -- correlated errors)")
    all_s = inflation(z["z"].values, rng)
    say(fmt_inflation("ALL elements pooled", all_s))
    for el, sub in z.groupby("element"):
        say(fmt_inflation(f"  {el}", inflation(sub["z"].values, rng)))
    return z, all_s


# ======================================================================
# S4 -- the M7 anchor
# ======================================================================
def run_anchor(say):
    say("\n" + "=" * 78)
    say("S4  THE M7 ANCHOR -- 11 elements, 3 objects, refit vs published")
    say("=" * 78)
    p = os.path.join(OUT, "m7_refit_vs_literature.csv")
    if not os.path.exists(p):
        say("  out/m7_refit_vs_literature.csv missing -- SKIPPED")
        return None, None
    d = pd.read_csv(p)
    v = d[np.isfinite(d.get("delta_over_refit_formal_err", np.nan))].copy()
    z = v["delta_over_refit_formal_err"].values
    rng = np.random.default_rng(SEED)
    s = inflation(z, rng)
    say(fmt_inflation("M7 trio, refit vs published", s))
    say(f"    (M7 published: median |z| 2.28, max 6.16, 4/11 inside 1 sigma)")
    return v, s


# ======================================================================
# S3 -- injection-recovery through the arm's own fitter
# ======================================================================
def _prepared_templates(min_ccd=300):
    """Real prepared epoch tables from the pre-release file: the scan
    geometry an injected orbit is written onto."""
    import epoch_vet_harness as H
    import orbital_refit_arm as A
    src = H.PrereleaseSource()
    out = {}
    for sid in src.all_ids():
        raw = src.fetch([sid]).get(int(sid))
        if raw is None:
            continue
        try:
            d = A.prepare_epochs(raw, sid)
        except Exception:                                        # noqa: BLE001
            continue
        if len(d) >= min_ccd:
            out[int(sid)] = d
    return out


def _inject_once(d, pars, rng, jitter_mas=0.0):
    """Simulate along-scan positions for a known orbit on a real scan
    geometry, then run the ARM'S OWN fit chain on them."""
    import spleaf
    from kepmodel.astro import AstroModel
    import orbital_refit_arm as A

    t = d["relative_time_day"].values
    ct, st = d["cos_theta"].values, d["sin_theta"].values
    pf = d["parallax_factor_al"].values
    sig = d["centroid_pos_error_al"].values
    ty = d["relative_time_year"].values

    def build(y):
        m = AstroModel(t, y, ct, st,
                       err=spleaf.term.Error(sig),
                       jit=spleaf.term.Jitter(0.0))
        m.add_lin(st, "ra")
        m.add_lin(ct, "dec")
        m.add_lin(pf, "parallax")
        m.add_lin(ty * st, "mura")
        m.add_lin(ty * ct, "mudec")
        return m

    gen = build(np.zeros_like(t))
    gen.add_keplerian_from_period(pars["P"])
    gen.set_keplerian_param("0", param=["P", "Tp", "as", "e", "w", "i",
                                        "bigw"])
    # kepmodel's set_param signature is set_param(VALUE, param=...) -- value
    # first.  Passing the names first raises deep inside the translator with
    # "'float' object has no attribute 'split'", which reads like a bug in
    # the library rather than a swapped argument.
    gen.set_param([pars["P"], pars["Tp"], pars["as"], pars["e"], pars["w"],
                   pars["i"], pars["bigw"]],
                  param=["kep.0.P", "kep.0.Tp", "kep.0.as", "kep.0.e",
                         "kep.0.w", "kep.0.i", "kep.0.bigw"])
    signal = gen.keplerian_model()

    truth_lin = {"ra": pars["ra"], "dec": pars["dec"],
                 "parallax": pars["parallax"], "mura": pars["mura"],
                 "mudec": pars["mudec"]}
    lin = (truth_lin["ra"] * st + truth_lin["dec"] * ct
           + truth_lin["parallax"] * pf + truth_lin["mura"] * ty * st
           + truth_lin["mudec"] * ty * ct)
    noise = rng.normal(0.0, np.sqrt(sig ** 2 + jitter_mas ** 2))
    y = signal + lin + noise

    m = build(y)
    m.fit()
    p_best, fap, model = A.peak_period(m)
    if not (fap < A.FAP_GATE):
        return None
    kep = A.keplerian_fit(model, p_best)
    names = list(kep.fit_param)
    vals, errs = kep.get_param_error(param=names)
    gp = dict(zip(names, vals))
    ge = dict(zip(names, errs))
    rec = {}
    for key, tk in [("kep.0.P", "P"), ("kep.0.e", "e"), ("kep.0.as", "as"),
                    ("lin.parallax", "parallax")]:
        rec[tk] = (float(gp[key]), float(ge[key]), float(
            pars[tk] if tk != "parallax" else truth_lin["parallax"]))
    return rec


def run_injection(say, n_inject=240, jitter_frac=0.0, tag="clean"):
    import orbital_refit_arm as A                            # noqa: F401
    say("\n" + "=" * 78)
    say(f"S3  INJECTION-RECOVERY THROUGH THE ARM ({tag}, n={n_inject})")
    say("=" * 78)
    say("  Real pre-release scan geometry + a real DR3 NSS orbit injected\n"
        "  + Gaussian noise at the real per-CCD sigma, through the arm's\n"
        "  OWN single_star_model -> periodogram -> keplerian_fit ->\n"
        "  get_param_error chain.  This is the only route that tests the\n"
        "  Laplace error bar itself.")
    tpl = _prepared_templates()
    say(f"  scan-geometry templates: {len(tpl)} pre-release sources "
        f"({', '.join(str(len(v)) for v in list(tpl.values())[:6])}... CCDs)")
    q = pd.read_csv(os.path.join(OUT, "epoch_vet_day1_queue.v2.csv"))
    nss = pd.read_parquet(NSS_PARQUET, columns=[
        "source_id", "nss_solution_type", "period", "eccentricity",
        "a_thiele_innes", "b_thiele_innes", "f_thiele_innes",
        "g_thiele_innes", "t_periastron", "nss_parallax", "significance",
        "phot_g_mean_mag"])
    tri = pd.read_parquet(TRIAGE_PARQUET,
                          columns=["source_id", "nss_solution_type",
                                   "a0_mas"])
    pool = nss.merge(tri, on=["source_id", "nss_solution_type"], how="left")
    pool = pool[pool.source_id.isin(q.source_id.astype("int64"))]
    pool = pool[np.isfinite(pool.a0_mas) & (pool.a0_mas > 0)
                & (pool.period > 20) & (pool.period < 3000)
                & (pool.eccentricity >= 0) & (pool.eccentricity < 0.95)]
    say(f"  injection pool: {len(pool)} DR3 NSS orbits from the day-one "
        f"queue")
    rng = np.random.default_rng(SEED)
    keys = sorted(tpl)
    rows = []
    t0 = time.time()
    picks = pool.sample(n=min(n_inject, len(pool)), random_state=SEED,
                        replace=n_inject > len(pool))
    for i, (_, r) in enumerate(picks.iterrows()):
        d = tpl[keys[i % len(keys)]]
        jit = jitter_frac * float(np.median(d["centroid_pos_error_al"]))
        pars = {"P": float(r.period),
                "Tp": float(rng.uniform(0, float(r.period))),
                "as": float(r.a0_mas), "e": float(r.eccentricity),
                "w": float(rng.uniform(0, 2 * np.pi)),
                "i": float(np.arccos(rng.uniform(-1, 1))),
                "bigw": float(rng.uniform(0, 2 * np.pi)),
                "ra": 0.0, "dec": 0.0,
                "parallax": float(r.nss_parallax),
                "mura": float(rng.normal(0, 5)),
                "mudec": float(rng.normal(0, 5))}
        try:
            rec = _inject_once(d, pars, rng, jitter_mas=jit)
        except Exception as exc:                                 # noqa: BLE001
            rows.append({"element": "ERROR",
                         "note": f"{type(exc).__name__}: {exc}"})
            continue
        if rec is None:
            rows.append({"element": "NO_PEAK", "note": ""})
            continue
        for el, (got, err, true) in rec.items():
            rows.append({"source_id": int(r.source_id), "element": el,
                         "recovered": got, "formal_err": err, "true": true,
                         "z": (got - true) / err if err > 0 else np.nan,
                         "template_id": int(keys[i % len(keys)]),
                         "n_ccd": int(len(d)), "period_d": float(r.period),
                         "a0_mas": float(r.a0_mas),
                         "significance": float(r.significance),
                         "phot_g_mean_mag": float(r.phot_g_mean_mag),
                         "jitter_mas": jit})
        if (i + 1) % 40 == 0:
            say(f"    {i+1}/{len(picks)}  ({time.time()-t0:.0f}s)")
    z = pd.DataFrame(rows)
    z.to_csv(os.path.join(OUT, f"m8_inflation_injection_{tag}.csv"),
             index=False, lineterminator="\n")
    nfail = int((z["element"] == "NO_PEAK").sum())
    nerr = int((z["element"] == "ERROR").sum())
    zz = z[~z["element"].isin(["NO_PEAK", "ERROR"])]
    say(f"\n  {len(picks)} injections in {time.time()-t0:.0f}s: "
        f"{nfail} NO_PEAK, {nerr} ERROR, "
        f"{len(zz)//4 if len(zz) else 0} recovered orbits")
    rngb = np.random.default_rng(SEED)
    all_s = inflation(zz["z"].values, rngb)
    say(fmt_inflation("ALL elements pooled", all_s))
    for el, sub in zz.groupby("element"):
        say(fmt_inflation(f"  {el}", inflation(sub["z"].values, rngb)))
    if len(zz):
        _trend(say, zz, "period_d", "injected period (d)", rngb)
        _trend(say, zz, "a0_mas", "injected a0 (mas)", rngb)
    return zz, all_s


# ======================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sb9", action="store_true")
    ap.add_argument("--duals", action="store_true")
    ap.add_argument("--anchor", action="store_true")
    ap.add_argument("--injection", action="store_true")
    ap.add_argument("--injection-cached", nargs="*", default=None,
                    help="tags whose out/m8_inflation_injection_<tag>.csv "
                         "are summarised instead of re-run")
    ap.add_argument("--n-inject", type=int, default=240)
    ap.add_argument("--jitter-frac", type=float, default=0.0)
    ap.add_argument("--tag", default="clean")
    ap.add_argument("--out", default=os.path.join(OUT,
                                                  "m8_error_inflation.txt"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.all:
        a.sb9 = a.duals = a.anchor = a.injection = True

    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    say("M8 TASK 1 -- THE ERROR-INFLATION FACTOR AT SCALE")
    say(f"produced {pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    say("\nWHAT CANNOT BE RUN, AND WHY:")
    say("  Gaia DR3 publishes NO stellar epoch astrometry.  The refit arm's")
    say("  Keplerian half consumes epoch astrometry, so it cannot be run over")
    say("  hundreds of DR3 sources by anyone before 2026-12-02; the only")
    say("  epoch astrometry that exists is the 12-source pre-release file.")
    say("  The four routes below are what CAN be measured, each labelled with")
    say("  what it bounds.")

    summ = []
    if a.sb9:
        _, _, s = run_sb9(say)
        summ.append(("S1 SB9 external (Gaia NSS formal errors)", s))
    if a.duals:
        _, s = run_duals(say)
        summ.append(("S2 dual-solution internal (LOWER BOUND)", s))
    if a.injection:
        _, s = run_injection(say, a.n_inject, a.jitter_frac, a.tag)
        summ.append((f"S3 injection-recovery, {a.tag} (arm's Laplace sigma)",
                     s))
    for tag in (a.injection_cached or []):
        p = os.path.join(OUT, f"m8_inflation_injection_{tag}.csv")
        if not os.path.exists(p):
            say("")
            say(f"  S3 cache {tag}: {p} missing -- SKIPPED")
            continue
        zz = pd.read_csv(p)
        zz = zz[~zz["element"].isin(["NO_PEAK", "ERROR"])]
        rngb = np.random.default_rng(SEED)
        st = inflation(zz["z"].values, rngb)
        say("")
        say("=" * 78)
        say(f"S3  INJECTION-RECOVERY THROUGH THE ARM ({tag}) -- from cache")
        say("=" * 78)
        say(fmt_inflation("ALL elements pooled", st))
        for el, sub in zz.groupby("element"):
            say(fmt_inflation(f"  {el}", inflation(sub["z"].values, rngb)))
        summ.append((f"S3 injection-recovery, {tag}", st))

    if a.anchor:
        _, s = run_anchor(say)
        if s:
            summ.append(("S4 M7 anchor (arm vs published, n=11)", s))

    if summ:
        say("\n" + "=" * 78)
        say("SUMMARY -- the inflation factor by route")
        say("=" * 78)
        for tag, s in summ:
            say(fmt_inflation(tag, s))
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.relpath(a.out, BASE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
