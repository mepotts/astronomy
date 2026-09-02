#!/usr/bin/env python
"""M5-writeup: re-derive every headline number that enters the draft.

Reads ONLY committed artifacts in out/ plus (where a number cannot be reached
otherwise) the gitignored-but-regenerable bulk products in data/.  Prints one
line per audited quantity:  KEY | claimed | rederived | VERDICT.

Provenance tiers printed with each row:
  [out]      re-derived from a committed out/ CSV or JSON
  [bulk]     re-derived from data/ (gitignored, regenerable by the M1-M4 scripts)
  [external] not derivable here - must be checked against its source by hand

Usage:  .venv/Scripts/python.exe scripts/m5w_audit.py
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
DATA = os.path.join(ROOT, "data")

ROWS: list[dict] = []


def check(key, claimed, rederived, tier, source, tol=None, note=""):
    """Record one audited number."""
    if rederived is None:
        verdict = "NOT-RE-DERIVABLE"
    elif isinstance(claimed, str) or isinstance(rederived, str):
        verdict = "VERIFIED" if str(claimed) == str(rederived) else "CORRECTED"
    elif isinstance(claimed, (int, np.integer)) and isinstance(
        rederived, (int, np.integer)
    ):
        verdict = "VERIFIED" if int(claimed) == int(rederived) else "CORRECTED"
    else:
        t = tol if tol is not None else 0.005 * max(abs(float(claimed)), 1e-30)
        verdict = (
            "VERIFIED" if abs(float(claimed) - float(rederived)) <= t else "CORRECTED"
        )
    ROWS.append(
        dict(
            key=key,
            claimed=claimed,
            rederived=rederived,
            tier=tier,
            source=source,
            verdict=verdict,
            note=note,
        )
    )
    print(f"{verdict:16s} {key:52s} claimed={claimed!s:22s} got={rederived!s:22s} [{tier}]")


# --------------------------------------------------------------------------
# A. cross-walk, scale offset, amplitude census   (M1 §1-§2)
# --------------------------------------------------------------------------
print("\n=== A. cross-walk / scale / amplitudes (M1) ===")
st = json.load(open(os.path.join(OUT, "w2_stats.json")))

# w2_stats.json is itself a committed artifact; cross-check its pair count and
# scale offset independently against the full pair table before trusting it.
pq = os.path.join(DATA, "w2_pairs.parquet")
pairs = None
if os.path.exists(pq):
    pairs = pd.read_parquet(pq)
    check("n_clean_pairs", 632668, int(len(pairs)), "bulk", "data/w2_pairs.parquet")
else:
    check("n_clean_pairs", 632668, int(st["n_clean_pairs"]), "out", "out/w2_stats.json",
          note="parquet absent; value echoed from committed stats JSON only")

check("n_dr2_main_rows", 1975540, int(st["n_dr2_total"]), "out", "out/w2_stats.json")
check("n_dr1_main_rows", 930203, int(st["n_dr1_total"]), "out", "out/w2_stats.json")
check("n_uid_dr1_nonzero", 742056, int(st["n_dr2_with_dr1_match"]), "out",
      "out/w2_stats.json")
check("frac_dr2_with_dr1_crosswalk_pct", 37.6,
      round(100 * st["n_dr2_with_dr1_match"] / st["n_dr2_total"], 1), "out",
      "out/w2_stats.json", tol=0.05)
check("n_bright_tier_20sigma", 1238, int(st["n_bright_tier"]), "out",
      "out/w2_stats.json")
check("scale_offset_median_R", 0.979, round(float(st["bright_tier_median_R"]), 3),
      "out", "out/w2_stats.json", tol=0.0005)
check("scale_offset_pct", 2.0, round(100 * (1 - float(st["bright_tier_median_R"])), 1),
      "out", "out/w2_stats.json", tol=0.05)
check("all_clean_median_R", 0.825, round(float(st["all_clean_R_quantiles"]["0.5"]), 3),
      "out", "out/w2_stats.json", tol=0.0005)
check("n_z5", 2138, int(st["z5_n"]), "out", "out/w2_stats.json")
check("n_cons_amp_gt5_stacked", 62, int(st["n_cons_amp_gt5_z5"]), "out",
      "out/w2_stats.json")
check("n_cons_amp_gt10_stacked", 14, int(st["n_cons_amp_gt10_z5"]), "out",
      "out/w2_stats.json")
check("n_epoch_amp_gt5", 225, int(st["n_epoch_amp_gt5_z5"]), "out", "out/w2_stats.json")
check("n_epoch_amp_gt10", 49, int(st["n_epoch_amp_gt10_z5"]), "out", "out/w2_stats.json")
check("n_dr1_clean_detlike30", 118253, int(st["n_dr1_clean_detlike30"]), "out",
      "out/w2_stats.json")
check("n_vanished_detlike30", 261, int(st["n_vanished_detlike30"]), "out",
      "out/w2_stats.json")
check("n_new_bright", 286, int(st["n_new_bright_rate_gt_p2"]), "out",
      "out/w2_stats.json")

# independent re-derivation of the scale offset from the pair table, if present
if pairs is not None:
    cols = set(pairs.columns)
    ratecol3 = "ML_RATE_1" if "ML_RATE_1" in cols else None
    ratecol1 = "ML_RATE_1_D1" if "ML_RATE_1_D1" in cols else None
    print("   pair-table columns available:", sorted(cols)[:24], "...")
    if ratecol3 and ratecol1:
        e3 = pairs.get("ML_RATE_ERR_1")
        e1 = pairs.get("ML_RATE_ERR_1_D1")
        if e3 is not None and e1 is not None:
            m = (pairs[ratecol3] / e3 >= 20) & (pairs[ratecol1] / e1 >= 20)
            n_b = int(m.sum())
            med = float((pairs.loc[m, ratecol3] / pairs.loc[m, ratecol1]).median())
            check("scale_offset_median_R_INDEPENDENT", 0.979, round(med, 3), "bulk",
                  "data/w2_pairs.parquet recomputed", tol=0.002,
                  note=f"independent recompute over n={n_b} >=20sigma pairs")
            check("n_bright_tier_INDEPENDENT", 1238, n_b, "bulk",
                  "data/w2_pairs.parquet recomputed")
        # NOTE: w2_stats' R quantiles are SCALE-NORMALISED (divided by the
        # bright-tier median). Reproduce that normalisation before comparing.
        med_all_raw = float((pairs[ratecol3] / pairs[ratecol1]).median())
        med_all = med_all_raw / float(st["bright_tier_median_R"])
        check("all_clean_median_R_INDEPENDENT", 0.825, round(med_all, 3), "bulk",
              "data/w2_pairs.parquet recomputed, scale-normalised", tol=0.002,
              note=f"raw (un-normalised) median ratio is {med_all_raw:.3f}")
        if "ML_EXP_1" in cols and "ML_EXP_1_D1" in cols:
            er = float((pairs["ML_EXP_1"] / pairs["ML_EXP_1_D1"]).median())
            check("exposure_ratio_t3_over_t1_median", 2.9, round(er, 2), "bulk",
                  "data/w2_pairs.parquet ML_EXP_1 / ML_EXP_1_D1", tol=0.02,
                  note="M1 quotes 2.9 'over the ranked set'; over all clean pairs "
                       "it is 2.84")

# --------------------------------------------------------------------------
# B. vanished-source census and the artifact/fader split   (M2 §3)
# --------------------------------------------------------------------------
print("\n=== B. vanished census (M2 §3) ===")
van = pd.read_csv(os.path.join(OUT, "m2_vanished_forensics.csv"))
check("vanished_census_rows", 261, int(len(van)), "out",
      "out/m2_vanished_forensics.csv")

vc = van["forensic_class_v2"].value_counts()
print("   class tally:", dict(vc))
n_fade = int(vc.get("FADE-CANDIDATE", 0))
n_indet = int(
    vc.get("CONFUSED-IDENTITY", 0) + vc.get("INDETERMINATE-HALO", 0)
)
n_art = int(len(van) - n_fade - n_indet)
check("n_fade_candidates", 107, n_fade, "out", "out/m2_vanished_forensics.csv")
check("n_artifacts", 148, n_art, "out", "out/m2_vanished_forensics.csv")
check("n_indeterminate", 6, n_indet, "out", "out/m2_vanished_forensics.csv")
check("artifact_pct", 57, int(round(100 * n_art / len(van))), "out",
      "out/m2_vanished_forensics.csv")
check("fader_pct", 41, int(round(100 * n_fade / len(van))), "out",
      "out/m2_vanished_forensics.csv")
check("n_artifact_confusion_mode", 85, int(vc.get("ARTIFACT-CONFUSION", 0)), "out",
      "out/m2_vanished_forensics.csv")
check("n_artifact_extended_mode", 36, int(vc.get("ARTIFACT-EXTENDED", 0)), "out",
      "out/m2_vanished_forensics.csv")
check("n_artifact_split_mode", 25, int(vc.get("ARTIFACT-SPLIT/MOVED", 0)), "out",
      "out/m2_vanished_forensics.csv")

check("vanished_frac_of_bright_dr1_pct", 0.22,
      round(100 * len(van) / st["n_dr1_clean_detlike30"], 2), "out",
      "derived: 261 / 118253", tol=0.005)
check("fader_frac_of_bright_dr1_pct", 0.09,
      round(100 * n_fade / st["n_dr1_clean_detlike30"], 2), "out",
      "derived: 107 / 118253", tol=0.005)

# Threshold band. M2 quotes 107 (+35/-12) for moving the presence cut to
# 2.0 / 1.3. That is only right if the cut acted in isolation; in the actual
# classification tree (scripts/m2_upper_limits.py) the split/halo/PSF branches
# are evaluated FIRST, so most rows in the band never become faders. Re-run the
# tree verbatim at each cut - this is the load-bearing systematic on the census.
pres = van["ul_presence"].astype(float)
is_fade = van["forensic_class_v2"] == "FADE-CANDIDATE"


def m2_tree_faders(cut: float) -> int:
    """Re-run scripts/m2_upper_limits.py's v2 tree with a different presence cut."""
    is_split = van["in_dr2_any_sep"] <= 15.0
    is_halo = ~is_split & (pres <= 0.01)
    counts_present = ~is_split & ~is_halo & (pres > cut)
    blank = ~is_split & ~is_halo & ~counts_present
    near_psf = van["nn2_bright_sep_arcsec"] <= 40.0
    return int((blank & ~near_psf).sum())


assert m2_tree_faders(1.5) == n_fade, "tree replay does not reproduce the CSV"
n_13, n_20 = m2_tree_faders(1.3), m2_tree_faders(2.0)
print(f"   tree replay: cut 1.3 -> {n_13} faders, cut 1.5 -> {n_fade}, "
      f"cut 2.0 -> {n_20}")
check("threshold_band_minus (cut 1.5->1.3)", 12, n_fade - n_13, "out",
      "m2_upper_limits.py v2 tree replayed at cut=1.3",
      note="M2's -12 counts every blank row in (1.3,1.5]; 4 of those are "
           "CONFUSED-IDENTITY, not faders")
check("threshold_band_plus (cut 1.5->2.0)", 35, n_20 - n_fade, "out",
      "m2_upper_limits.py v2 tree replayed at cut=2.0",
      note="M2's +35 counts every artifact row in (1.5,2.0]; 18 of those are "
           "ARTIFACT-SPLIT/MOVED or near-PSF and are caught by earlier branches")
check("fader_band_low", 95, n_13, "out", "tree replay at cut=1.3")
check("fader_band_high", 142, n_20, "out", "tree replay at cut=2.0")

# blank-population clustering claim (presence 1.0-1.3 for faders)
fp = pres[is_fade]
print(f"   fader presence: min {fp.min():.3f} med {fp.median():.3f} "
      f"p90 {fp.quantile(0.9):.3f} max {fp.max():.3f}")
check("fader_presence_max", 1.5, round(float(fp.max()), 2), "out",
      "out/m2_vanished_forensics.csv", tol=0.05,
      note="cut is presence <= 1.5 by construction")

# --------------------------------------------------------------------------
# C. fader demographics  (M2 §3 tail)
# --------------------------------------------------------------------------
print("\n=== C. fader demographics (M2 §3) ===")
ax = pd.read_csv(os.path.join(OUT, "m2_archival_xray.csv"))
fad = van.loc[is_fade].merge(
    ax, left_on="IAUNAME", right_on="name", how="left", suffixes=("", "_ax")
)
print(f"   fade candidates joined to archival sweep: {len(fad)} "
      f"({int(fad['name'].notna().sum())} matched)")

w1w2 = fad["catwise_w1"].astype(float) - fad["catwise_w2"].astype(float)
gcls = fad["gclass_class"].astype(str)
agn_like = ((gcls.str.upper().str.contains("AGN|QSO", na=False)) | (w1w2 >= 0.8))
check("n_faders_agn_like", 39, int(agn_like.sum()), "out",
      "m2_vanished_forensics x m2_archival_xray: Gaia-class AGN or W1-W2>=0.8")

# M2 says "bright stellar counterparts (W1<15, flat W1-W2)" without defining
# "flat". The count is definition-dependent: 23 at |W1-W2|<0.3, 25 at <0.5.
stellar = (fad["catwise_w1"].astype(float) < 15) & (w1w2.abs() < 0.3)
check("n_faders_stellar", 23, int(stellar.sum()), "out",
      "m2_archival_xray: W1<15 and |W1-W2|<0.3",
      note="definition-dependent: 25 at |W1-W2|<0.5, 24 at <0.4, 23 at <0.3; "
           "39 counterparts have W1<15 at any colour; disjoint from the AGN set")

inbox = (
    (fad["RA"].astype(float) >= 60)
    & (fad["RA"].astype(float) <= 105)
    & (fad["DEC"].astype(float) >= -75)
    & (fad["DEC"].astype(float) <= -60)
)
check("n_faders_in_lmc_box", 25, int(inbox.sum()), "out",
      "RA 60-105, Dec -75..-60 applied to the 107 faders")

prior = (
    fad["2rxs_sep"].notna()
    | fad["xmmsl3_sep"].notna()
    | fad["csc21_sep"].notna()
    | fad["2sxps_sep"].notna()
    | fad["xmmssc_sep"].notna()
)
check("n_faders_prior_xray", 21, int(prior.sum()), "out",
      "m2_archival_xray: any of 2RXS/XMMSL3/CSC2.1/2SXPS/XMMSSC")

cwblank = fad["catwise_sep"].isna()
check("n_faders_catwise_blank", 3, int(cwblank.sum()), "out",
      "m2_archival_xray catwise_sep null")

check("fader_median_detlike", 40, int(round(float(van.loc[is_fade, "DET_LIKE_0"].median()))),
      "out", "out/m2_vanished_forensics.csv", tol=0.5)
check("n_faders_detlike_gt100", 8, int((van.loc[is_fade, "DET_LIKE_0"] > 100).sum()),
      "out", "out/m2_vanished_forensics.csv")

# M2's "at DET_LIKE>100 the artifact fraction is 14/20" (the M1 top-20 claim)
top20 = van.nlargest(20, "DET_LIKE_0")
n_art_top20 = int((~top20["forensic_class_v2"].isin(
    ["FADE-CANDIDATE", "CONFUSED-IDENTITY", "INDETERMINATE-HALO"])).sum())
check("m1_top20_artifact_count", 14, n_art_top20, "out",
      "top 20 by DET_LIKE_0 in m2_vanished_forensics.csv")

# --------------------------------------------------------------------------
# D. upper-limit calibration  (M2 §3)
# --------------------------------------------------------------------------
print("\n=== D. UL-server calibration (M2 §3) ===")
cal = pd.read_csv(os.path.join(OUT, "m2_ul_calibration.csv"))
check("n_calibration_pairs", 25, int(len(cal)), "out", "out/m2_ul_calibration.csv")
ff = cal["ul_fade_frac"].astype(float)
check("calib_fade_frac_median", 1.13, round(float(ff.median()), 2), "out",
      "out/m2_ul_calibration.csv", tol=0.005,
      note="M2's '1.13 +- 0.07' is the MEAN +- sd; the median is 1.14")
check("calib_fade_frac_mean", 1.13, round(float(ff.mean()), 2), "out",
      "out/m2_ul_calibration.csv", tol=0.005)
check("calib_fade_frac_sd", 0.07, round(float(ff.std(ddof=1)), 2), "out",
      "out/m2_ul_calibration.csv sample sd", tol=0.005)
cp = cal["ul_presence"].astype(float)
n_degenerate = int((cp <= 0.01).sum())
check("calib_presence_degenerate_rows", 0, n_degenerate, "out",
      "out/m2_ul_calibration.csv",
      note="M2 claims 'steady calibrators are all >> 1'; one row "
           "(3eRASS J114550.9-552043) returned UL_S = inf -> P = 0")
good = cp[cp > 0.01]
check("calib_presence_min_valid", 5.7, round(float(good.min()), 1), "out",
      "out/m2_ul_calibration.csv excluding the degenerate row", tol=0.05)
check("calib_presence_max_valid", 13.9, round(float(good.max()), 1), "out",
      "out/m2_ul_calibration.csv excluding the degenerate row", tol=0.05)
check("calib_n_valid_presence", 25, int(len(good)), "out",
      "out/m2_ul_calibration.csv",
      note="the presence calibration is effectively n=24, not n=25")

# --------------------------------------------------------------------------
# E. LMC sub-study  (M4 Part A)
# --------------------------------------------------------------------------
print("\n=== E. LMC sub-study (M4 Part A) ===")
lmc = pd.read_csv(os.path.join(OUT, "m4_lmc_ogle_matches.csv"))
check("n_lmc_faders", 25, int(len(lmc)), "out", "out/m4_lmc_ogle_matches.csv")
for col, label in [
    ("ocvs_n_match", "ocvs"),
    ("xrom_n_match", "xrom"),
    ("be_n_match", "be_sabogal"),
    ("hmxb_n_match", "hmxb_vac"),
]:
    check(f"lmc_matches_{label}", 0, int(lmc[col].fillna(0).astype(int).sum()), "out",
          "out/m4_lmc_ogle_matches.csv")

ctrl = pd.read_csv(os.path.join(OUT, "m4_lmc_ogle_control.csv"))
c_ocvs = ctrl.loc[ctrl["catalog"] == "ocvs_all"].iloc[0]
check("control_positions", 400, int(c_ocvs["control_positions"]), "out",
      "out/m4_lmc_ogle_control.csv")
check("control_ocvs_hits", 3, int(c_ocvs["control_hits"]), "out",
      "out/m4_lmc_ogle_control.csv")
check("expected_chance_matches_per25", 0.19,
      round(float(c_ocvs["expected_chance_matches_per_25"]), 2), "out",
      "out/m4_lmc_ogle_control.csv", tol=0.005)

bd = lmc["be_donor_candidate"].astype(str).str.lower().isin(["true", "1"])
check("n_be_donor_candidates", 1, int(bd.sum()), "out",
      "out/m4_lmc_ogle_matches.csv be_donor_candidate")
check("n_no_be_donor", 24, int((~bd).sum()), "out",
      "out/m4_lmc_ogle_matches.csv be_donor_candidate")

na = lmc["ocvs_nearest_any_arcmin"].astype(float)
check("nearest_ocvs_variable_min_arcmin", 0.4, round(float(na.min()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05)
check("nearest_ocvs_variable_max_arcmin", 4.8, round(float(na.max()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05)
check("nearest_xrom_min_arcmin", 50.0,
      round(float(lmc["xrom_nearest_any_arcmin"].astype(float).min()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05,
      note="M4 rounds 49.8' UP to '>= 50'', which overstates the separation")
check("nearest_hmxb_min_arcmin", 13.0,
      round(float(lmc["hmxb_nearest_any_arcmin"].astype(float).min()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05,
      note="M4 rounds 12.9' UP to '>= 13'', which overstates the separation")
check("nearest_sabogal_be_min_deg", 2.0, round(float(
    lmc["be_nearest_any_arcmin"].astype(float).min()) / 60.0, 1), "out",
    "out/m4_lmc_ogle_matches.csv", tol=0.05)

rr = lmc["r_match_arcsec"].astype(float)
check("match_radius_min_arcsec", 5.7, round(float(rr.min()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05)
check("match_radius_max_arcsec", 11.2, round(float(rr.max()), 1), "out",
      "out/m4_lmc_ogle_matches.csv", tol=0.05)

# demographics tally of the 25 (M4 table)
w = lmc["catwise_w1_w2"].astype(float)
check("lmc_firm_agn_colored", 9, int((w >= 0.8).sum()), "out",
      "out/m4_lmc_ogle_matches.csv catwise_w1_w2 >= 0.8")

# OGLE-IV dark window, measured from the XROM light curve
lc = pd.read_csv(os.path.join(OUT, "m4_lmc_ogle_lightcurves.csv"))
xr = lc.loc[lc["vtype"] == "xrom"]
if len(xr):
    gap = float(xr.iloc[0]["max_gap_2019p5_2024_d"])
    check("ogle_iv_dark_days", 886, int(round(gap)), "out",
          "out/m4_lmc_ogle_lightcurves.csv (XROM CAL 83 max gap)", tol=1.0)
    check("xrom_lc_last_hjd_prime", 11186.5, round(float(xr.iloc[0]["hjd_last"]), 1),
          "out", "out/m4_lmc_ogle_lightcurves.csv", tol=0.1,
          note="HJD-2450000; 2026-05-25 per M4")
rr_lc = lc.loc[lc["vtype"] == "rrlyr"]
if len(rr_lc):
    check("ocvs_rrlyr_last_hjd_prime", 7492.5,
          round(float(rr_lc["hjd_last"].astype(float).max()), 1), "out",
          "out/m4_lmc_ogle_lightcurves.csv", tol=0.1, note="2016-04-14 per M4")

# HJD' -> calendar, to test the 2020-03-13 / 2022-08-16 endpoints
try:
    from astropy.time import Time

    if len(xr):
        # the gap is bracketed by the last point before and first after; the
        # CSV stores only the gap length, so convert the two dates M4 quotes and
        # confirm they differ by the measured gap.
        t0 = Time("2020-03-13").jd
        t1 = Time("2022-08-16").jd
        check("ogle_dark_endpoints_consistent", int(round(gap)), int(round(t1 - t0)),
              "out", "astropy JD difference of the two quoted calendar dates",
              tol=1.0)
        # eRASS2+3 window (2020-06-11 -> 2021-06-16 per the DR2 portal) inside?
        e2 = Time("2020-06-11").jd
        e3 = Time("2021-06-16").jd
        check("erass23_window_inside_ogle_dark", "yes",
              "yes" if (e2 > t0 and e3 < t1) else "NO", "out",
              "astropy JD comparison")
except Exception as exc:  # pragma: no cover
    print("   astropy time check skipped:", exc)

# OCVS pool size, from the cached ident files
ocvs_dir = os.path.join(DATA, "ogle")
if os.path.isdir(ocvs_dir):
    tot = 0
    per = {}
    for fn in sorted(os.listdir(ocvs_dir)):
        if fn.endswith("_ident.dat"):
            n = sum(1 for line in open(os.path.join(ocvs_dir, fn), encoding="latin-1")
                    if line.strip())
            per[fn.replace("_ident.dat", "")] = n
            tot += n
    print("   OCVS ident counts:", per)
    check("ocvs_pool_total", 217725, tot, "bulk", "data/ogle/*_ident.dat line counts")
    check("ocvs_rrlyr", 41471, per.get("ocvs4_lmc_rrlyr", 0), "bulk",
          "data/ogle/ocvs4_lmc_rrlyr_ident.dat")
    check("ocvs_ecl", 63252, per.get("ocvs4_lmc_ecl", 0), "bulk",
          "data/ogle/ocvs4_lmc_ecl_ident.dat")
    check("ocvs_lpv_ogle3", 91995, per.get("ocvs3_lmc_lpv", 0), "bulk",
          "data/ogle/ocvs3_lmc_lpv_ident.dat")
    sab = os.path.join(ocvs_dir, "sabogal_lmc_be.csv")
    if os.path.exists(sab):
        check("sabogal_be_candidates", 2446, int(len(pd.read_csv(sab))), "bulk",
              "data/ogle/sabogal_lmc_be.csv")

# LMC HMXB VAC: donor G range
vac = os.path.join(DATA, "eRASS1_HMXB_LMC_v1.0.fits.tgz")
if os.path.exists(vac):
    import tarfile
    from astropy.io import fits

    try:
        with tarfile.open(vac) as tf:
            member = [m for m in tf.getmembers() if m.name.endswith(".fits")][0]
            fh = tf.extractfile(member)
            with fits.open(fh) as hd:
                tb = hd[1].data
                gcol = [c for c in hd[1].columns.names
                        if c.lower() in ("gmag", "g", "phot_g_mean_mag", "gaia_g", "g_mag")]
                check("hmxb_vac_rows", 53, int(len(tb)), "bulk", vac)
                if gcol:
                    g = np.asarray(tb[gcol[0]], dtype=float)
                    g = g[np.isfinite(g)]
                    check("hmxb_vac_G_min", 12.68, round(float(g.min()), 2), "bulk",
                          f"{vac}::{gcol[0]}", tol=0.005)
                    check("hmxb_vac_G_max", 17.00, round(float(g.max()), 2), "bulk",
                          f"{vac}::{gcol[0]}", tol=0.005)
                    check("hmxb_vac_G_median", 14.85, round(float(np.median(g)), 2),
                          "bulk", f"{vac}::{gcol[0]}", tol=0.005)
                else:
                    print("   HMXB VAC columns:", hd[1].columns.names)
    except Exception as exc:  # pragma: no cover
        print("   HMXB VAC read failed:", exc)

# --------------------------------------------------------------------------
# F. verdict tallies  (M2 §1)
# --------------------------------------------------------------------------
print("\n=== F. verdict tallies (M2 §1) ===")
ver = pd.read_csv(os.path.join(OUT, "m2_verdicts.csv"))
check("n_touched_sources", 381, int(len(ver)), "out", "out/m2_verdicts.csv")
vt = ver["verdict"].value_counts()
print("   verdicts:", dict(vt))
check("n_identified", 104, int(vt.get("IDENTIFIED", 0)), "out", "out/m2_verdicts.csv")
check("n_plausible_class", 123, int(vt.get("PLAUSIBLE-CLASS", 0)), "out",
      "out/m2_verdicts.csv")
check("n_artifact_verdict", 153, int(vt.get("ARTIFACT", 0)), "out",
      "out/m2_verdicts.csv")
check("n_genuinely_unexplained", 1, int(vt.get("GENUINELY-UNEXPLAINED", 0)), "out",
      "out/m2_verdicts.csv")

# --------------------------------------------------------------------------
# G. catalogue-level structural facts, read straight from the FITS files
#    (these are the claims about DR1/DR2 themselves that the draft rests on)
# --------------------------------------------------------------------------
print("\n=== G. catalogue structure, direct from the FITS (M1 §1) ===")
try:
    from astropy.io import fits
    from astropy.time import Time

    f_dr2 = os.path.join(DATA, "eRASS3_Main_v1.3.fits")
    f_dr1 = os.path.join(DATA, "eRASS1_Main.v1.2.fits")
    f_hard = os.path.join(DATA, "eRASS3_Hard_v1.2.fits")

    if os.path.exists(f_dr2):
        with fits.open(f_dr2, memmap=True) as hd:
            names = hd[1].columns.names
            check("dr2_main_rows_FITS", 1975540, int(hd[1].header["NAXIS2"]), "bulk",
                  f_dr2)
            check("dr2_main_ncols", 250, len(names), "bulk", f_dr2)
            ext = hd[1].data["EXT_LIKE"]
            check("dr2_point_sources", 1911744, int((ext == 0).sum()), "bulk",
                  f_dr2, note="matches DR2 paper Table 15 as quoted in M1 §1")
            check("dr2_extended_sources", 63796, int((ext > 0).sum()), "bulk", f_dr2)
            n_time = len([c for c in names if "MJD" in c.upper()
                          or "TIME" in c.upper()])
            check("dr2_has_no_epoch_time_columns", 0, n_time, "bulk", f_dr2,
                  note="M1 §1 kill-check: DR2 ships stacked values only")
            check("dr2_has_UID_DR1_column", "yes",
                  "yes" if "UID_DR1" in names else "NO", "bulk", f_dr2)

    if os.path.exists(f_dr1):
        with fits.open(f_dr1, memmap=True) as hd:
            check("dr1_main_rows_FITS", 930203, int(hd[1].header["NAXIS2"]), "bulk",
                  f_dr1)
            mn = np.asarray(hd[1].data["MJD_MIN"], dtype=float)
            mx = np.asarray(hd[1].data["MJD_MAX"], dtype=float)
            mn = mn[np.isfinite(mn) & (mn > 0)]
            mx = mx[np.isfinite(mx) & (mx > 0)]
            t0, t1 = Time(mn.min(), format="mjd"), Time(mx.max(), format="mjd")
            check("erass1_start_date", "2019-12-12", t0.iso[:10], "bulk",
                  f_dr1 + "::MJD_MIN",
                  note="the catalogue's own earliest MJD is 2019-12-11.9")
            check("erass1_end_date", "2020-06-11", t1.iso[:10], "bulk",
                  f_dr1 + "::MJD_MAX")
            check("erass1_span_days", 182, int(round(mx.max() - mn.min())), "bulk",
                  f_dr1, tol=0.6)

    if os.path.exists(f_hard):
        with fits.open(f_hard, memmap=True) as hd:
            check("dr2_hard_rows", 15980, int(hd[1].header["NAXIS2"]), "bulk", f_hard)

    # the survey-span arithmetic M1 quotes from the portal
    span = float(Time("2021-06-16").jd - Time("2019-12-12").jd)
    check("erass3_span_days_from_quoted_dates", 556, int(span), "external",
          "arithmetic on the two dates M1 §1 attributes to the DR2 portal",
          note="INTERNAL INCONSISTENCY: 2019-12-12 -> 2021-06-16 is 552 d, not "
               "556 d; one of the three portal-sourced figures is wrong. The "
               "draft must not depend on the exact value.")
except Exception as exc:  # pragma: no cover
    print("   FITS checks skipped:", exc)

# --------------------------------------------------------------------------
# H. faint-end validation of the presence metric (new in M5-writeup)
#    scripts/m5w_faint_validation.py -> out/m5w_faint_validation.{csv,json}
# --------------------------------------------------------------------------
print("\n=== H. faint-end validation of the presence metric (M5-writeup) ===")
vj = os.path.join(OUT, "m5w_faint_validation.json")
if os.path.exists(vj):
    v = json.load(open(vj))
    ctrl = pd.read_csv(os.path.join(OUT, "m5w_faint_validation.csv"))
    cp = ctrl["ul_presence"].astype(float)
    cp = cp[np.isfinite(cp) & (cp > 0.01)]
    check("validation_n_controls", 60, int(len(cp)), "out",
          "out/m5w_faint_validation.csv")
    check("validation_control_presence_min", 2.03, round(float(cp.min()), 2), "out",
          "out/m5w_faint_validation.csv", tol=0.005)
    check("validation_control_presence_median", 2.60, round(float(cp.median()), 2),
          "out", "out/m5w_faint_validation.csv", tol=0.005)
    check("validation_control_presence_max", 3.78, round(float(cp.max()), 2), "out",
          "out/m5w_faint_validation.csv", tol=0.005)
    check("validation_controls_below_cut", 0, int((cp <= 1.5).sum()), "out",
          "out/m5w_faint_validation.csv",
          note="zero of 60 flux-matched steady sources fall in the fader class")
    check("validation_false_positive_95ul_pct", 4.9,
          round(100 * float(v["false_positive_rate_95ul"]), 1), "out",
          "1 - 0.05^(1/60), one-sided binomial", tol=0.05)
    check("validation_max_contaminants_of_107", 6,
          int(v["implied_max_contaminants"]), "out",
          "0.049 x 107, rounded up")
    check("validation_populations_disjoint", "yes",
          "yes" if float(cp.min()) > float(pres[is_fade].max()) else "NO", "out",
          "control min vs fader max",
          note=f"faders reach P={pres[is_fade].max():.2f}, controls start at "
               f"P={cp.min():.2f}")
else:
    print("   validation JSON absent - run scripts/m5w_faint_validation.py first")

# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------
df = pd.DataFrame(ROWS)
outp = os.path.join(OUT, "m5w_audit.csv")
df.to_csv(outp, index=False)
print("\n=== SUMMARY ===")
print(df["verdict"].value_counts().to_string())
print(f"\nwrote {outp} ({len(df)} audited quantities)")
bad = df.loc[df["verdict"] != "VERIFIED"]
if len(bad):
    print("\nNOT VERIFIED:")
    for _, r in bad.iterrows():
        print(f"  {r['verdict']:16s} {r['key']}: claimed {r['claimed']} vs {r['rederived']}")
sys.exit(0)
