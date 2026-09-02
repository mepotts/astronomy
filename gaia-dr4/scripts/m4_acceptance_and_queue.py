#!/usr/bin/env python
"""M4 tasks 1+3 closeout: re-run the acceptance on the standing v2 list,
freeze config v3, and build the day-one epoch-vet queue.

Acceptance (must PASS before config v3 is written):
  - Gaia BH1 + BH2 present in the candidate list, Pr(III|corr) = 1.0000,
    and they are the top two by M2_min;
  - EB26 operating point re-measured on the list membership:
    39/42 confirmed kept, 7/23 spurious passed (the frozen M2 numbers --
    membership is unchanged by M4, so any drift = a bug, not the sky).

Config v3 (queries/dr4-triage-config.v3.json; v1, v2 untouched):
  selection/screen/probability IDENTICAL to v2.  What changes is
  documentation of two M4 measurements:
  (1) extinction tier, far stars: Bayestar19 arbitration on a fully-sourced
      unit chain (scripts/m4_bayestar_dozen.py) -- 9 of the 13
      dust-ambiguous rows resolved-alive, 4 south of the Bayestar
      footprint stay bracketed, 0 membership movements;
  (2) X-ray policy: an eROSITA match stays a CAUTION TAG, not a selection
      flag -- the EB26 activity-vs-spuriousness test is UNDERPOWERED
      (2/13 spurious vs 0/16 confirmed detected in-footprint,
      Fisher p = 0.19; only a spurious rate >= 0.40 was detectable at 80%
      power).  The hypothetical X-ray *cut* is also measured here and
      rejected (removes candidates without measured purity gain).

Day-one queue (out/epoch_vet_day1_queue.csv): the 949 v2 rows + the
retrieval bin's Pr >= 0.999 rows (32 on DR3), ordered by Pr(III|corr)
desc with M2_min tiebreak, carrying every caution flag the runbook's
Phase 3 needs (1-yr alias, low-|b|, sigma_TI^2 > 20, X-ray-active,
EB26 verdict where known, dust-unresolved-south).

Run: .venv/Scripts/python.exe scripts/m4_acceptance_and_queue.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "out")
BH1, BH2 = 4373465352415301632, 5870569352746779008
KEY = ["source_id", "nss_solution_type"]


def main():
    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))
    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    xm = pd.read_csv(os.path.join(OUT_DIR, "erosita_class3_xmatch.csv"))
    doz = pd.read_csv(os.path.join(OUT_DIR, "m4_bayestar_dozen.csv"))

    # ---- acceptance -------------------------------------------------------
    print("=== acceptance re-run (config v3 semantics == v2 selection) ===")
    for name, sid in (("BH1", BH1), ("BH2", BH2)):
        row = v2[v2["source_id"] == sid]
        assert len(row) == 1, f"{name} missing from candidate list"
        pr = float(row["p_class3_corr"].iloc[0])
        m2 = float(row["m2_min_dark_dust"].iloc[0])
        print(f"  {name}: present, Pr(III|corr) = {pr:.4f}, "
              f"M2_min = {m2:.2f}")
        assert pr >= 0.9999, f"{name} Pr regression"
    top2 = v2.sort_values("m2_min_dark_dust", ascending=False) \
             .head(2)["source_id"].tolist()
    assert set(top2) == {BH1, BH2}, f"top-2 by M2_min changed: {top2}"
    print(f"  top-2 by M2_min: BH1 + BH2  -- PASS")

    memb = set(v2["source_id"])
    conf = eb[eb["verdict"] == "CONFIRMED"]["source_id"]
    spur = eb[eb["verdict"] == "SPURIOUS"]["source_id"]
    kept = int(conf.isin(memb).sum())
    passed = int(spur.isin(memb).sum())
    print(f"  EB26 operating point on the list: {kept}/42 confirmed kept, "
          f"{passed}/23 spurious passed")
    assert (kept, passed) == (39, 7), "operating point drifted"
    print("  ACCEPTANCE PASS")

    # ---- the hypothetical X-ray cut (measured, rejected) ------------------
    xr = xm[xm["route"].astype(str).str.startswith("positional")]
    xr_keys = set(map(tuple, xr[KEY].itertuples(index=False)))
    v2k = v2[KEY].apply(tuple, axis=1)
    n_x = int(v2k.isin(xr_keys).sum())
    x_v = v2.loc[v2k.isin(xr_keys)].merge(
        eb[["source_id", "verdict"]], on="source_id", how="left")
    n_conf_x = int((x_v["verdict"] == "CONFIRMED").sum())
    n_spur_x = int((x_v["verdict"] == "SPURIOUS").sum())
    print(f"\nhypothetical 'X-ray match as a cut' on the list: would drop "
          f"{n_x} rows ({n_conf_x} EB26-confirmed, {n_spur_x} "
          f"EB26-spurious, {n_x - n_conf_x - n_spur_x} unverdicted, "
          f"incl. the top NS-range RS CVn-locus candidates) -> REJECTED, "
          f"stays a caution tag")

    # ---- day-one queue ----------------------------------------------------
    probs = pd.read_parquet(os.path.join(BASE, "data",
                                         "dr3_corrvec_probs.parquet"))
    ret = pd.read_csv(os.path.join(OUT_DIR,
                                   "amrf_class3_lowsig_retrieval.csv"))
    ret = ret.merge(probs[KEY + ["p_class3_corr"]], on=KEY, how="left")
    ret_hi = ret[ret["p_class3_corr"] >= 0.999].copy()
    print(f"\nretrieval bin at Pr >= 0.999: {len(ret_hi)} rows "
          f"(head: {int(ret_hi.sort_values('p_class3_corr', ascending=False)['source_id'].iloc[0])})")

    south_unres = set(doz.loc[doz["verdict"] ==
                              "UNRESOLVED_south_of_footprint", "source_id"])

    qa = v2[KEY + ["p_class3_corr", "m2_min_dark_dust", "period",
                   "significance", "sigma_ti2", "phot_g_mean_mag",
                   "flag_alias_1yr", "flag_low_lat"]].copy()
    qa["m2_min"] = qa.pop("m2_min_dark_dust")
    qa["queue_bin"] = "v2_main"
    qb = ret_hi[KEY + ["p_class3_corr", "m2_min_dark", "period",
                       "significance", "sigma_ti2", "phot_g_mean_mag",
                       "flag_alias_1yr", "flag_low_lat"]].copy()
    qb["m2_min"] = qb.pop("m2_min_dark")
    qb["queue_bin"] = "retrieval_pr999"
    q = pd.concat([qa, qb], ignore_index=True)
    q["flag_hi_sigma_ti2"] = q["sigma_ti2"] > 20.0
    qk = q[KEY].apply(tuple, axis=1)
    q["flag_xray_active"] = qk.isin(xr_keys) & (q["queue_bin"] == "v2_main")
    q["xray_tested"] = q["queue_bin"] == "v2_main"  # retrieval not crossed yet
    q["flag_dust_unresolved_south"] = q["source_id"].isin(south_unres)
    q = q.merge(eb[["source_id", "verdict"]], on="source_id", how="left") \
         .rename(columns={"verdict": "eb26_verdict"})
    q = q.sort_values(["p_class3_corr", "m2_min"],
                      ascending=[False, False]).reset_index(drop=True)
    q.insert(0, "rank", np.arange(1, len(q) + 1))
    qpath = os.path.join(OUT_DIR, "epoch_vet_day1_queue.csv")
    q.to_csv(qpath, index=False, lineterminator="\n")
    print(f"wrote {qpath}: {len(q)} rows "
          f"({(q['queue_bin']=='v2_main').sum()} v2 + "
          f"{(q['queue_bin']=='retrieval_pr999').sum()} retrieval); "
          f"cautions: alias {int(q['flag_alias_1yr'].sum())}, "
          f"low-|b| {int(q['flag_low_lat'].sum())}, "
          f"sigma_TI2>20 {int(q['flag_hi_sigma_ti2'].sum())}, "
          f"X-ray {int(q['flag_xray_active'].sum())}, "
          f"EB26-spurious {int((q['eb26_verdict']=='SPURIOUS').sum())}")

    # ---- config v3 --------------------------------------------------------
    with open(os.path.join(BASE, "queries", "dr4-triage-config.v2.json"),
              encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["_comment"] = (
        "v3 (M4, 2026-08-18). Selection/screen/probability IDENTICAL to v2 "
        "(frozen M2/M3); candidate-list membership unchanged (949). Adds "
        "two measured policies: the Bayestar19 far-star arbitration "
        "(sourced unit chain) and the X-ray caution-tag policy (EB26 "
        "discriminator test underpowered). See gaia-dr4/"
        "M4-xray-discriminator.md.")
    cfg["version"] = 3
    cfg["supersedes"] = "dr4-triage-config.v2.json (v2, M3)"
    cfg["extinction_tier"]["d_gt_1250pc"] = (
        "bracketed: Edenhofer-to-edge (lower) vs SFD full column x SF11 "
        "2.742 (upper); where dec > -30, Bayestar19 at the star's distance "
        "arbitrates (max(B19, Edenhofer floor) = best estimate); south of "
        "-30 stays bracketed and flagged")
    cfg["extinction_tier"]["bayestar19_chain"] = (
        "1 B19 unit = E(gP1-rP1) 0.901 mag (Green+19 ApJ 887,93, src line "
        "399 + extinction-vector table) = 1.000 x E(B-V)_SFD in the same "
        "colour (SF11 ApJ 737,103 Table 6 R_V=3.1: PS1 g 3.172, r 2.271); "
        "A_V = 2.742 x E(B-V) (SF11 Table 6 Landolt V); Gaia bands via "
        "ZGR23 ratios (house). Cross-check chain: EB26 A_G=2.66E, "
        "E(BP-RP)=1.33E (arXiv:2608.06453 src lines 171-172) -- verdicts "
        "agree on all arbitrated rows (m4_bayestar_dozen.csv). Data: "
        "bayestar2019.h5 Dataverse doi:10.7910/DVN/2EJ9TX, md5 "
        "ab815d2fd3068d1b81a1bd61fb18a722.")
    cfg["xray_policy"] = {
        "status": "caution tag, NOT a selection flag and NOT a cut",
        "eb26_test_2026-08-18": (
            "in eROSITA-DE footprint: 2/13 EB26-spurious vs 0/16 "
            "EB26-confirmed detected (eRASS:3); Fisher two-sided p=0.19 "
            "-- direction consistent with activity->spurious-orbit but "
            "UNDERPOWERED (80%-power detectable spurious rate at this n: "
            ">= 0.40); both detections coronal (log fx/fopt -2.4/-3.3, "
            "soft HR), no hard-band, no accretor"),
        "as_a_cut_rejected": (
            "would drop in-list rows incl. 0 EB26-confirmed / 1 "
            "EB26-spurious / the rest unverdicted NS-range active-binary "
            "candidates -- no measured purity gain"),
        "day1": ("run the eROSITA cross on the new list (runbook Phase 3 "
                 "step 4); treat matches as epoch-vet-first cases")}
    cfg["measured_on_dr3"].update({
        "m4_eb26_xray_confirmed_detected": "0/16",
        "m4_eb26_xray_spurious_detected": "2/13",
        "m4_eb26_xray_fisher_p": 0.19,
        "m4_dust_ambiguous_resolved_alive": 9,
        "m4_dust_ambiguous_south_unresolved": 4,
        "m4_membership_moved": 0})
    v3path = os.path.join(BASE, "queries", "dr4-triage-config.v3.json")
    with open(v3path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"\nwrote {v3path} (v1, v2 untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
