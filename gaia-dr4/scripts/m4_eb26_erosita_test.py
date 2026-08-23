#!/usr/bin/env python
"""M4 task 1: the activity-vs-spuriousness test.

M3's n=1 observation: the X-ray-loudest class-III match (relative to its
star) was a known EB26-refuted spurious solution, and magnetic activity is
a known spurious-orbit risk factor (starspot photocentre jitter).  Test it
properly: cross ALL 76 El-Badry 2026 followed-up astrometric candidates
(42 CONFIRMED compact objects / 23 SPURIOUS / 11 other verdicts) against
eROSITA-DE DR2 (eRASS:3 stack) and DR1 (eRASS1), with shifted-position
controls.

Question: does X-ray detection -- or f_X/f_opt, or hardness -- statistically
discriminate CONFIRMED from SPURIOUS?

Pre-registered verdict rules (written before running):
  WORKS        Fisher exact p < 0.05 on the in-footprint detection fractions
               (confirmed vs spurious), or Mann-Whitney p < 0.05 on
               log10(f_X/f_opt) with >= 3 detections per side; direction
               must be stated.
  DOESN'T      a well-powered null (the minimum detectable effect at the
               achieved n is small and the observed difference is ~0).
  UNDERPOWERED anything else; report the minimum spurious-detection rate
               detectable at alpha = 0.05 with 80% power given the achieved
               in-footprint counts (exact binomial enumeration).

Match machinery = the M3 house pattern (scripts/erosita_xmatch.py):
  route A: NWAY GDR3 id lookup in eRASSc3_Main_GDR3 (duplicate-TTYPE
           landmine handled);
  route B: positional vs eRASS3 Main v1.3, radius 3.44 x POS_ERR
           (2-D Rayleigh 99.7%) clipped to [1, 10] arcsec, Gaia positions
           PM-propagated 2016.0 -> 2020.5;
  hard   : positional vs eRASS3 Hard v1.2 (2.3-5 keV);
  DR1    : positional vs eRASS1 Main v1.2 (PM-propagated to ~2020.2) --
           what DR1 adds: an independent shallower epoch (variability;
           a DR1-only detection would be a fader).
  controls: 8 dec shifts +-0.5..2.0 deg of the full in-footprint target
           set vs eRASS3 Main, same radii.

Hardness: HR = (R_hi - R_lo)/(R_hi + R_lo) from ML_RATE_P* sub-bands,
band edges per the DR2 data model page (eRASS3_Main_v1.3.html, read
2026-08-18): P1 0.2-0.5, P2 0.5-1.0, P3 1.0-2.0, P4 2.0-5.0 keV.
HR1 = (P2-P1)/(P2+P1), HR2 = (P3-P2)/(P3+P2), HR3 = (P4-P3)/(P4+P3).
f_X/f_opt: log10(FX) + 0.4*G + 5.37 (Maccacaro et al. 1988 V-band
constant, G substituted -- conventional, marked; same as M3).

Footprint: eROSITA-DE = 179.944 < l < 359.944 deg; only ~half the EB26
sample can be tested at all -- the power statement is part of the result.

AMENDMENT LOG
  M6 (2026-08-21) -- SOURCE OF VERDICTS, not behaviour.  The verdict table
  is no longer read from fixtures/elbadry2026_astrometric_candidates.csv
  directly: it comes from the day-one VERDICT STORE
  (scripts/verdict_schema.py, out/verdicts/*.csv), of which the EB26
  fixture is one producer and the epoch-vet harness is the other.  The
  test, the match machinery, the controls and the pre-registered rules are
  untouched -- the acceptance test of the refactor is that this script's
  frozen M4 artifacts reproduce BYTE-IDENTICALLY through the new path.
  --verdicts / --scopes / --sources / --out-dir added so that on
  2026-12-03 this question is re-asked against harness verdicts with no
  new code.  A verdict-provenance line is printed every run and written
  into the stats file only when the store carries more than one
  (source, scope) combination -- see the asymmetry note in
  scripts/verdict_schema.py before pooling scopes.

Inputs : out/verdicts/*.csv  (the day-one verdict store; M6)
         ../erosita-dr2/data/  (READ-ONLY)
Outputs: out/m4_eb26_erosita_xmatch.csv   (per-target, all 76)
         out/m4_eb26_discriminator_stats.txt
Run    : .venv/Scripts/python.exe scripts/m4_eb26_erosita_test.py
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from astropy.io import fits
from scipy.spatial import cKDTree
from scipy.stats import fisher_exact, mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as vs  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERO = os.path.join(os.path.dirname(BASE), "erosita-dr2", "data")
OUT_DIR = os.path.join(BASE, "out")

L_LO, L_HI = 179.94423568, 359.94423568
SHIFT_DR2_YR = 4.5    # 2016.0 -> ~2020.5 (eRASS:3 midpoint)
SHIFT_DR1_YR = 4.2    # 2016.0 -> ~2020.2 (eRASS1 midpoint)
R_MIN_AS, R_MAX_AS = 1.0, 10.0
RAYLEIGH = 3.44
DEC_SHIFTS = [-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0]
MACCACARO_C = 5.37
ALPHA = 0.05
POWER_TARGET = 0.80


def unit_vecs(ra_deg, dec_deg):
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    return np.column_stack([np.cos(dec) * np.cos(ra),
                            np.cos(dec) * np.sin(ra),
                            np.sin(dec)])


def match_positional(cand_ra, cand_dec, ero_ra, ero_dec, radius_as):
    tree = cKDTree(unit_vecs(ero_ra, ero_dec))
    cv = unit_vecs(cand_ra, cand_dec)
    chord = 2.0 * np.sin(np.radians(R_MAX_AS / 3600.0) / 2.0)
    pairs = tree.query_ball_point(cv, r=chord)
    ic, ie, sep = [], [], []
    for i, js in enumerate(pairs):
        for j in js:
            d = np.degrees(2.0 * np.arcsin(
                np.linalg.norm(cv[i] - tree.data[j]) / 2.0)) * 3600.0
            if d <= radius_as[j]:
                ic.append(i)
                ie.append(j)
                sep.append(d)
    return np.array(ic, int), np.array(ie, int), np.array(sep, float)


def wilson_ci(k, n, z=1.959964):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1.0 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - hw), min(1.0, ctr + hw))


def fisher_power(n1, p1, n2, p2, alpha=ALPHA):
    """Exact power of the two-sided Fisher test at (n1,p1) vs (n2,p2)
    by full enumeration (n <= ~30 so trivial)."""
    from scipy.stats import binom
    pw = 0.0
    for k1 in range(n1 + 1):
        w1 = binom.pmf(k1, n1, p1)
        if w1 < 1e-12:
            continue
        for k2 in range(n2 + 1):
            w2 = binom.pmf(k2, n2, p2)
            if w2 < 1e-12:
                continue
            _, p = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])
            if p < alpha:
                pw += w1 * w2
    return pw


def load_nway():
    with fits.open(os.path.join(
            ERO, "eRASSc3_Main_GDR3_Public_27Jul2026.fits.gz")) as h:
        hdr = h[1].header
        seen = set()
        for i in range(1, hdr["TFIELDS"] + 1):
            nm = hdr[f"TTYPE{i}"]
            if nm in seen:
                hdr[f"TTYPE{i}"] = f"{nm}_dup{i}"
            seen.add(nm)
        d = h[1].data
        nway = pd.DataFrame({
            "DETUID": [str(x) for x in d["DETUID"]],
            "GDR3_source_id": np.asarray(d["GDR3_source_id"], np.int64),
            "NWAY_p_any": np.asarray(d["NWAY_p_any"], float),
            "NWAY_p_i": np.asarray(d["NWAY_p_i"], float),
            "NWAY_sep": np.asarray(d["NWAY_Separation_GDR3_ERO"], float),
        })
    return nway


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="M4 activity-vs-spuriousness test (EB26 x eROSITA-DE)")
    ap.add_argument("--verdicts", nargs="*", default=None,
                    help="verdict-store CSV(s); default out/verdicts/eb26.v1.csv")
    ap.add_argument("--scopes", nargs="*", default=None)
    ap.add_argument("--sources", nargs="*", default=None)
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    out_dir = a.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # M6: verdicts come from the verdict STORE, not from the fixture.
    store_paths = a.verdicts or [os.path.join(vs.STORE_DIR, "eb26.v1.csv")]
    store = vs.load_store(store_paths, scopes=a.scopes, sources=a.sources)
    prov = vs.scope_composition_string(store)
    n_combo = store.groupby(["verdict_source", "verdict_scope"]).ngroups
    print(f"VERDICT PROVENANCE: {len(store)} records from "
          f"{[os.path.basename(p) for p in store_paths]}")
    print(f"  scope composition: {prov}")
    eb = vs.eb26_compatible_frame(store).drop(
        columns=["verdict_source", "verdict_scope", "verdict_confidence"])
    tri = pd.read_parquet(
        os.path.join(BASE, "data", "dr3_amrf_triage.parquet"),
        columns=["source_id", "nss_solution_type", "ra", "dec", "l", "b",
                 "pmra", "pmdec", "nss_parallax", "phot_g_mean_mag",
                 "class_det", "cuts_eb26", "significance"])
    t = eb.merge(tri, on="source_id", how="left", suffixes=("", "_tri"))
    # M7: the invariant this guards is NO JOIN FAN-OUT, which is a property
    # of the merge; the "== 76" was the size of the ONLY store that existed
    # when it was written.  The moment the store holds a second producer --
    # which is the entire point of the schema -- `--verdicts all` failed
    # here, and so did the pooled command the runbook told December to run.
    # Rows that are not in the day's triage frame cannot be tested and are
    # DROPPED WITH A COUNT, never silently: today that is the 12 pre-release
    # demo sources, which are not NSS candidates at all.
    assert len(t) == len(eb), \
        f"verdict join to triage parquet fanned out: {len(t)} vs {len(eb)}"
    n_unjoined = int(t["ra"].isna().sum())
    if n_unjoined:
        print(f"  {n_unjoined} of {len(t)} verdict rows are not in the "
              f"triage frame (no sky position) -- DROPPED from this test")
        t = t[t["ra"].notna()].reset_index(drop=True)
    if len(t) == 0:
        # M7: an empty testable set is a COVERAGE RESULT, not a crash --
        # see the matching note in m5_activity_discriminator.py.
        print("\nNOT TESTABLE: 0 of the selected verdict rows are in the "
              "triage frame (no sky position).")
        print("  This is a coverage result, not a failure. Report the "
              "coverage; claim nothing.")
        return 2

    t["in_footprint"] = (t["l"] > L_LO) & (t["l"] < L_HI)

    cosd = np.cos(np.radians(t["dec"].values))
    def prop(yr):
        ra = t["ra"].values + np.nan_to_num(t["pmra"].values) \
            * yr / 3.6e6 / np.clip(cosd, 1e-6, None)
        de = t["dec"].values + np.nan_to_num(t["pmdec"].values) * yr / 3.6e6
        return ra, de
    ra2, de2 = prop(SHIFT_DR2_YR)
    ra1, de1 = prop(SHIFT_DR1_YR)

    # ---- eRASS3 Main ------------------------------------------------------
    print("loading eRASS3 Main v1.3 (memmap)...", flush=True)
    hm = fits.open(os.path.join(ERO, "eRASS3_Main_v1.3.fits"), memmap=True)
    dm = hm[1].data
    m_ra = np.asarray(dm["RA"], float)
    m_dec = np.asarray(dm["DEC"], float)
    m_poserr = np.asarray(dm["POS_ERR"], float)
    radius = np.clip(RAYLEIGH * np.nan_to_num(m_poserr, nan=R_MAX_AS),
                     R_MIN_AS, R_MAX_AS)
    ic, ie, sep = match_positional(ra2, de2, m_ra, m_dec, radius)
    print(f"route B vs eRASS3 Main: {len(ic)} matches "
          f"({len(set(ic))} targets)")

    ctrl_counts = []
    infoot_idx = np.where(t["in_footprint"].values)[0]
    for ds in DEC_SHIFTS:
        icc, _, _ = match_positional(ra2[infoot_idx], de2[infoot_idx] + ds,
                                     m_ra, m_dec, radius)
        ctrl_counts.append(len(icc))
    print(f"shifted controls (in-footprint set, {len(DEC_SHIFTS)} shifts): "
          f"{ctrl_counts} -> mean {np.mean(ctrl_counts):.2f}")

    # ---- eRASS3 Hard ------------------------------------------------------
    with fits.open(os.path.join(ERO, "eRASS3_Hard_v1.2.fits"),
                   memmap=True) as h:
        dh = h[1].data
        rad_h = np.clip(RAYLEIGH * np.nan_to_num(
            np.asarray(dh["POS_ERR"], float), nan=R_MAX_AS),
            R_MIN_AS, R_MAX_AS)
        ich, ieh, seph = match_positional(
            ra2, de2, np.asarray(dh["RA"], float),
            np.asarray(dh["DEC"], float), rad_h)
    print(f"vs eRASS3 Hard: {len(ich)} matches")

    # ---- eRASS1 Main (DR1) ------------------------------------------------
    print("loading eRASS1 Main v1.2 (memmap)...", flush=True)
    h1 = fits.open(os.path.join(ERO, "eRASS1_Main.v1.2.fits"), memmap=True)
    d1 = h1[1].data
    r1_ra = np.asarray(d1["RA"], float)
    r1_dec = np.asarray(d1["DEC"], float)
    rad_1 = np.clip(RAYLEIGH * np.nan_to_num(
        np.asarray(d1["POS_ERR"], float), nan=R_MAX_AS),
        R_MIN_AS, R_MAX_AS)
    ic1, ie1, sep1 = match_positional(ra1, de1, r1_ra, r1_dec, rad_1)
    print(f"vs eRASS1 Main (DR1): {len(ic1)} matches")

    # ---- NWAY route A -----------------------------------------------------
    print("loading NWAY GDR3 counterpart catalog...", flush=True)
    nway = load_nway()
    nw = t.merge(nway, left_on="source_id", right_on="GDR3_source_id",
                 how="inner")
    print(f"route A (NWAY id lookup): {len(nw)} rows for "
          f"{nw['source_id'].nunique()} targets")

    # ---- assemble per-target table ---------------------------------------
    def hr(num, den):
        s = num + den
        return (num - den) / s if s > 0 else np.nan

    t = t.reset_index(drop=True)
    t["det_dr2"] = False
    for c in ("sep_arcsec", "det_like_0", "ml_flux_1", "log_fx_fopt",
              "l_x_erg_s", "hr1", "hr2", "hr3", "ml_rate_1", "dr1_rate_1",
              "rate_ratio_dr2_dr1", "nway_p_any", "nway_sep"):
        t[c] = np.nan
    t["ero_iauname"] = ""
    t["flag_opt"] = -1
    t["uid_dr1"] = 0
    t["det_hard"] = False
    t["det_dr1"] = False

    # keep the closest DR2 match per target
    best = {}
    for k in range(len(ic)):
        i = ic[k]
        if i not in best or sep[k] < best[i][1]:
            best[i] = (ie[k], sep[k])
    for i, (j, s) in best.items():
        row = dm[j]
        fx = float(row["ML_FLUX_1"])
        g = float(t.loc[i, "phot_g_mean_mag"])
        plx = float(t.loc[i, "nss_parallax"])
        d_cm = 1000.0 / plx * 3.086e18
        t.loc[i, "det_dr2"] = True
        t.loc[i, "sep_arcsec"] = round(s, 2)
        t.loc[i, "ero_iauname"] = str(row["IAUNAME"])
        t.loc[i, "det_like_0"] = float(row["DET_LIKE_0"])
        t.loc[i, "ml_flux_1"] = fx
        t.loc[i, "ml_rate_1"] = float(row["ML_RATE_1"])
        t.loc[i, "flag_opt"] = int(row["FLAG_OPT"])
        t.loc[i, "uid_dr1"] = int(row["UID_DR1"])
        if fx > 0:
            t.loc[i, "log_fx_fopt"] = np.log10(fx) + 0.4 * g + MACCACARO_C
            t.loc[i, "l_x_erg_s"] = 4.0 * np.pi * d_cm ** 2 * fx
        p = {b: float(row[f"ML_RATE_{b}"]) for b in
             ("P1", "P2", "P3", "P4")}
        t.loc[i, "hr1"] = hr(p["P2"], p["P1"])
        t.loc[i, "hr2"] = hr(p["P3"], p["P2"])
        t.loc[i, "hr3"] = hr(p["P4"], p["P3"])
    for k in range(len(ich)):
        t.loc[ich[k], "det_hard"] = True
    best1 = {}
    for k in range(len(ic1)):
        i = ic1[k]
        if i not in best1 or sep1[k] < best1[i][1]:
            best1[i] = (ie1[k], sep1[k])
    for i, (j, s) in best1.items():
        t.loc[i, "det_dr1"] = True
        t.loc[i, "dr1_rate_1"] = float(d1[j]["ML_RATE_1"])
    ok = t["det_dr2"] & t["det_dr1"] & (t["dr1_rate_1"] > 0)
    t.loc[ok, "rate_ratio_dr2_dr1"] = (t.loc[ok, "ml_rate_1"]
                                       / t.loc[ok, "dr1_rate_1"])
    nw_best = nw.sort_values("NWAY_p_any", ascending=False) \
                .drop_duplicates("source_id")
    for _, r in nw_best.iterrows():
        i = t.index[t["source_id"] == r["source_id"]][0]
        t.loc[i, "nway_p_any"] = r["NWAY_p_any"]
        t.loc[i, "nway_sep"] = r["NWAY_sep"]

    keep = ["source_id", "verdict", "in_footprint", "l", "b", "ra", "dec",
            "phot_g_mean_mag", "nss_parallax", "period_d", "significance",
            "class_det", "cuts_eb26", "det_dr2", "det_dr1", "det_hard",
            "sep_arcsec", "ero_iauname", "det_like_0", "ml_flux_1",
            "ml_rate_1", "log_fx_fopt", "l_x_erg_s", "hr1", "hr2", "hr3",
            "dr1_rate_1", "rate_ratio_dr2_dr1", "uid_dr1", "flag_opt",
            "nway_p_any", "nway_sep", "notes"]
    t[keep].to_csv(os.path.join(out_dir, "m4_eb26_erosita_xmatch.csv"),
                   index=False, lineterminator="\n")

    # ---- the statistics ---------------------------------------------------
    lines = []
    def say(s=""):
        lines.append(s)
        print(s)

    say("M4 activity-vs-spuriousness test -- EB26 x eROSITA-DE "
        "(2026-08-18)")
    say("=" * 72)
    if n_combo > 1:
        # MANDATORY disclosure when verdicts of more than one provenance or
        # scope are pooled (scripts/verdict_schema.py: a harness
        # `orbit_reality` CONFIRMED is weaker than an EB26 one).
        say("VERDICT PROVENANCE (more than one source/scope in this run):")
        say(f"  {prov}")
    nf = t.groupby("verdict")["in_footprint"].agg(["sum", "count"])
    say("\nfootprint (eROSITA-DE, 179.94<l<359.94):")
    for v, r in nf.iterrows():
        say(f"  {v:10s} {int(r['sum']):2d} of {int(r['count']):2d} "
            f"in footprint")

    f = t[t["in_footprint"]]
    conf = f[f["verdict"] == "CONFIRMED"]
    spur = f[f["verdict"] == "SPURIOUS"]
    k1, n1 = int(conf["det_dr2"].sum()), len(conf)
    k2, n2 = int(spur["det_dr2"].sum()), len(spur)
    lo1, hi1 = wilson_ci(k1, n1)
    lo2, hi2 = wilson_ci(k2, n2)
    say(f"\nDR2 (eRASS:3) detection, in-footprint:")
    say(f"  CONFIRMED  {k1}/{n1} = {k1/max(n1,1):.3f} "
        f"(95% Wilson {lo1:.3f}-{hi1:.3f})")
    say(f"  SPURIOUS   {k2}/{n2} = {k2/max(n2,1):.3f} "
        f"(95% Wilson {lo2:.3f}-{hi2:.3f})")
    nctrl = len(infoot_idx)
    chance = np.mean(ctrl_counts) / nctrl
    say(f"  chance/target (8 shifted controls, {nctrl} targets): "
        f"{chance:.4f}  (counts {ctrl_counts})")
    orr, pfish = fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])
    say(f"  Fisher exact (spurious vs confirmed, two-sided): "
        f"odds ratio {orr:.2f}, p = {pfish:.4f}")

    other = f[~f["verdict"].isin(["CONFIRMED", "SPURIOUS"])]
    say(f"  other verdicts in footprint: "
        f"{int(other['det_dr2'].sum())}/{len(other)} detected "
        f"({ {k: int(v) for k, v in other.groupby('verdict')['det_dr2'].sum().items()} })")

    say(f"\nhard band (2.3-5 keV): {int(t['det_hard'].sum())} of 76")
    say(f"DR1 (eRASS1): CONFIRMED {int(conf['det_dr1'].sum())}/{n1}, "
        f"SPURIOUS {int(spur['det_dr1'].sum())}/{n2}; "
        f"DR1-only (fader candidates): "
        f"{int((t['det_dr1'] & ~t['det_dr2']).sum())}")

    # f_X/f_opt among detected
    x1 = conf.loc[conf["det_dr2"], "log_fx_fopt"].dropna()
    x2 = spur.loc[spur["det_dr2"], "log_fx_fopt"].dropna()
    say(f"\nlog10(f_X/f_opt,G) among detected:")
    say(f"  CONFIRMED (n={len(x1)}): " +
        (f"median {x1.median():.2f}, values "
         f"{sorted(round(v,2) for v in x1)}" if len(x1) else "--"))
    say(f"  SPURIOUS  (n={len(x2)}): " +
        (f"median {x2.median():.2f}, values "
         f"{sorted(round(v,2) for v in x2)}" if len(x2) else "--"))
    pmw = None
    if len(x1) >= 3 and len(x2) >= 3:
        u, pmw = mannwhitneyu(x1, x2, alternative="two-sided")
        say(f"  Mann-Whitney two-sided: U={u:.0f}, p={pmw:.4f}")
    else:
        say("  Mann-Whitney: NOT RUN (needs >= 3 detections per side)")

    # hardness
    hboth = t.loc[t["det_dr2"], ["verdict", "hr1", "hr2", "hr3"]]
    say(f"\nhardness (detected sources): HR2 by verdict: "
        f"{ {v: [round(x,2) for x in g['hr2'].dropna()] for v, g in hboth.groupby('verdict')} }")

    # confound check
    say("\nconfound check (in-footprint medians):")
    for lab, grp in (("CONFIRMED", conf), ("SPURIOUS", spur)):
        say(f"  {lab:10s} G={grp['phot_g_mean_mag'].median():.2f}  "
            f"d={np.median(1000/grp['nss_parallax']):.0f} pc  "
            f"|b|={grp['b'].abs().median():.1f}")

    # ---- power ------------------------------------------------------------
    say("\npower at the achieved n "
        f"(alpha={ALPHA}, target power {POWER_TARGET:.0%}):")
    p0 = k1 / n1 if n1 else 0.0
    grid = np.arange(0.0, 1.0001, 0.05)
    detectable = None
    for p1 in grid:
        if p1 <= p0:
            continue
        pw = fisher_power(n1, p0, n2, p1)
        if pw >= POWER_TARGET:
            detectable = (p1, pw)
            break
    if detectable:
        say(f"  with CONFIRMED at {p0:.2f} ({k1}/{n1}), the smallest "
            f"SPURIOUS detection rate detectable at 80% power is "
            f"~{detectable[0]:.2f} (power {detectable[1]:.2f}) "
            f"-- an odds ratio of "
            f"{(detectable[0]/(1-detectable[0]))/max(p0/(1-p0),1e-9):.1f}")
    else:
        say(f"  NO spurious detection rate p1 <= 1.0 reaches 80% power "
            f"against CONFIRMED at {p0:.2f} ({k1}/{n1} vs n2={n2}) -- "
            f"the test cannot be well-powered at this footprint/sample")
    # and the reverse direction (spurious quieter)
    pw_extreme = fisher_power(n1, p0, n2, min(1.0, 3 * p0)) if p0 > 0 \
        else np.nan
    say(f"  power to see a 3x detection-rate excess in SPURIOUS: "
        f"{pw_extreme:.2f}" if np.isfinite(pw_extreme) else
        "  (3x-excess power undefined at p0=0)")

    # ---- verdict (rules in docstring) -------------------------------------
    say("\n" + "=" * 72)
    if pfish < ALPHA:
        say(f"VERDICT: DISCRIMINATES (detection rate, p={pfish:.4f}) -- "
            f"direction: {'SPURIOUS' if k2/max(n2,1) > k1/max(n1,1) else 'CONFIRMED'} louder")
    elif pmw is not None and pmw < ALPHA:
        say(f"VERDICT: DISCRIMINATES (f_X/f_opt among detected, "
            f"p={pmw:.4f})")
    else:
        say("VERDICT: NO SIGNIFICANT DISCRIMINATION at these numbers -- "
            "see the power statement above for whether that is a real "
            "null or an underpowered test.")

    with open(os.path.join(out_dir, "m4_eb26_discriminator_stats.txt"),
              "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    # per-target detected table for the record
    det = t[t["det_dr2"]].sort_values("log_fx_fopt", ascending=False)
    cols = ["source_id", "verdict", "sep_arcsec", "det_like_0",
            "log_fx_fopt", "l_x_erg_s", "hr2", "det_dr1",
            "rate_ratio_dr2_dr1", "nway_p_any", "flag_opt"]
    print("\ndetected targets:")
    print(det[cols].to_string(index=False))
    hm.close()
    h1.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
