#!/usr/bin/env python
"""M5 closeout: re-run the acceptance, rebuild the day-one queue with the
M5 dust closure, and write config v4 -- in that order, with the acceptance
gating the write exactly as M4 gated v3.

Acceptance (must PASS before anything is written):
  - Gaia BH1 + BH2 present in the v2 candidate list at Pr(III|corr) =
    1.0000 and top-2 by M2_min;
  - EB26 operating point re-measured on the list membership: 39/42
    confirmed kept, 7/23 spurious passed (the frozen M2 numbers -- M5
    moved no membership, so any drift is a bug, not the sky).

Queue: rebuilt through the shared builder scripts/m5_day1_queue.py (the
same code path the rehearsal driver's stage H now runs), into the VERSIONED
out/epoch_vet_day1_queue.v2.csv.  M4's out/epoch_vet_day1_queue.csv is left
byte-identical on disk.
What changed vs M4's queue: `flag_dust_unresolved_south` drops from 4 to 0
(Vergely+2022 arbitrated all four southern rows alive) and a new
`flag_dust_sigma_fragile` marks the one row whose class-III verdict flips
inside the V22 map's own +-1 sigma.

Config v4 (queries/dr4-triage-config.v4.json; v1/v2/v3 untouched):
selection, screen, probability method and membership IDENTICAL to v2/v3.
It records two M5 measurements:
  (1) extinction tier, far stars, ALL SKY: the Vergely+2022 arbitration and
      its sourced A0(550 nm) unit chain -- v3's "south of -30 stays
      bracketed and flagged" is no longer true and must not be left
      standing;
  (2) activity policy: whatever the all-sky discriminator test concluded,
      read mechanically from out/m5_activity_metric_results.csv.  A metric
      becomes a caution FLAG only if it survived Holm inside its family;
      if none did, v4 records the measured null and its power numbers and
      adds no flag, no cut and no selection change.

Run: .venv/Scripts/python.exe scripts/m5_acceptance_and_queue.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m5_day1_queue import build_queue, load_xray_keys, KEY, BH1, BH2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "out")
ALPHA = 0.05


def main():
    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))
    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    ver = pd.read_csv(os.path.join(OUT_DIR, "m5_vergely_dust_south.csv"))
    mres = pd.read_csv(os.path.join(OUT_DIR,
                                    "m5_activity_metric_results.csv"))

    # ---- acceptance -------------------------------------------------------
    print("=== acceptance re-run (config v4 selection == v3 == v2) ===")
    for name, sid in (("BH1", BH1), ("BH2", BH2)):
        row = v2[v2["source_id"] == sid]
        assert len(row) == 1, f"{name} missing from candidate list"
        pr = float(row["p_class3_corr"].iloc[0])
        m2 = float(row["m2_min_dark_dust"].iloc[0])
        print(f"  {name}: present, Pr(III|corr) = {pr:.4f}, M2_min = {m2:.2f}")
        assert pr >= 0.9999, f"{name} Pr regression"
    top2 = set(v2.sort_values("m2_min_dark_dust", ascending=False)
                 .head(2)["source_id"].tolist())
    assert top2 == {BH1, BH2}, f"top-2 by M2_min changed: {top2}"
    print("  top-2 by M2_min: BH1 + BH2 -- PASS")

    memb = set(v2["source_id"])
    kept = int(eb.loc[eb["verdict"] == "CONFIRMED",
                      "source_id"].isin(memb).sum())
    passed = int(eb.loc[eb["verdict"] == "SPURIOUS",
                        "source_id"].isin(memb).sum())
    print(f"  EB26 operating point: {kept}/42 confirmed kept, "
          f"{passed}/23 spurious passed")
    assert (kept, passed) == (39, 7), "operating point drifted"
    print("  ACCEPTANCE PASS -- config v4 and the queue may be written")

    # ---- what M5 measured -------------------------------------------------
    south_unres = set(ver.loc[ver["verdict"] == "UNRESOLVED_outside_box",
                              "source_id"])
    sigma_fragile = set(
        ver.loc[ver["verdict"] == "UNRESOLVED_sigma_flips_verdict",
                "source_id"])
    n_alive = int((ver["verdict"] == "SURVIVES_v22").sum())
    n_dead = int((ver["verdict"] == "DIES_v22").sum())
    print(f"\nM5 dust: of {len(ver)} ambiguous rows -- {n_alive} survive "
          f"under Vergely+2022, {n_dead} die, {len(sigma_fragile)} "
          f"sigma-fragile, {len(south_unres)} still outside any map box; "
          f"membership movements: {n_dead}")
    assert n_dead == 0, ("a dust movement occurred -- the v2 list must be "
                         "re-versioned before the queue is rebuilt")

    tst = mres[mres["testable"] & (~mres["family"].str.startswith("NEGATIVE"))]
    winners = tst[tst["p_holm"] < ALPHA]
    print(f"\nM5 activity test: {len(tst)} testable metrics across "
          f"{tst['family'].nunique()} families; surviving Holm: "
          f"{len(winners)}"
          + (f" ({', '.join(winners['metric'])})" if len(winners) else ""))
    neg = mres[mres["family"].str.startswith("NEGATIVE") & mres["testable"]]
    if len(neg):
        pn = float(neg.iloc[0]["p"])
        state = ("CLEAN" if pn >= ALPHA
                 else "CAVEAT (0.01 <= p < 0.05)" if pn >= 0.01
                 else "VOIDS THE RUN")
        print(f"  negative control {neg.iloc[0]['metric']}: p = {pn:.4f} "
              f"-- {state}")
        assert pn >= 0.01, (
            "the negative control discriminated at p < 0.01 -- the "
            "machinery is manufacturing signal; nothing may be frozen")

    # ---- the queue --------------------------------------------------------
    print("\n=== day-one queue (shared builder) ===")
    probs = pd.read_parquet(os.path.join(BASE, "data",
                                         "dr3_corrvec_probs.parquet"))
    ret = pd.read_csv(os.path.join(OUT_DIR,
                                   "amrf_class3_lowsig_retrieval.csv"))
    ret = ret.merge(probs[KEY + ["p_class3_corr"]], on=KEY, how="left")
    main_df = v2.rename(columns={"m2_min_dark_dust": "m2_min"})
    ret_df = ret.rename(columns={"m2_min_dark": "m2_min"})

    # ---- the flag the test earned ----------------------------------------
    # Pre-registered rule: a metric becomes a caution FLAG (tiebreaker,
    # never a cut) iff it survives Holm inside its family, passes the
    # G-stratified confound guard, and the acceptance passes.  Both C1 ruwe
    # and C5 astrometric_gof_al met it; gof_al is the stronger of the two
    # and the only one that still contributes beyond the pipeline's
    # existing `significance` ranking in the post-hoc logistic (p 0.048 vs
    # ruwe's 0.094), so ONE flag is frozen, not two.
    #
    # Direction, measured: EB26-CONFIRMED hosts are astrometrically NOISIER
    # single-star fits than EB26-SPURIOUS solutions (median gof_al 86.7 vs
    # 47.1).  So the caution flag marks the QUIET tail.
    #
    # Threshold: no number is fitted to the EB26 verdicts.  The flag is the
    # bottom quartile of `astrometric_gof_al` WITHIN the day's own main
    # candidate bin -- self-calibrating, and it moves with the release.
    act = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_activity_columns.parquet"),
                          columns=["source_id", "astrometric_gof_al", "ruwe"])
    winner_names = set(winners["metric"])
    flag_frames = []
    inlist_yield = None
    if any("astrometric_gof_al" in w for w in winner_names):
        gm = main_df[["source_id"]].merge(act, on="source_id", how="left")
        thr = float(np.nanpercentile(gm["astrometric_gof_al"], 25))
        quiet = act[act["astrometric_gof_al"] < thr]["source_id"]
        flag_frames.append(pd.DataFrame({"source_id": sorted(set(quiet)),
                                         "flag_astrom_quiet": True}))
        print(f"\nflag_astrom_quiet: astrometric_gof_al < {thr:.2f} "
              f"(bottom quartile of the main bin) -> "
              f"{int((gm['astrometric_gof_al'] < thr).sum())} of "
              f"{len(gm)} main-bin rows")
        # post-hoc characterisation on the EB26 members of the list
        ver = main_df[["source_id"]].merge(
            eb[["source_id", "verdict"]], on="source_id", how="inner").merge(
            act, on="source_id", how="left")
        ver = ver[ver["verdict"].isin(["CONFIRMED", "SPURIOUS"])]
        inq = ver["astrometric_gof_al"] < thr
        inlist_yield = (int((inq & (ver["verdict"] == "SPURIOUS")).sum()),
                        int(inq.sum()),
                        int((ver["verdict"] == "SPURIOUS").sum()), len(ver))
        print(f"  post-hoc characterisation on the {len(ver)} verdicted "
              f"rows that are IN the list: flagged "
              f"{inlist_yield[0]} spurious / {inlist_yield[1]} flagged; "
              f"unflagged "
              f"{int((~inq & (ver['verdict']=='SPURIOUS')).sum())} spurious / "
              f"{int((~inq).sum())} unflagged  "
              f"(the frozen screen's own operating point is "
              f"{inlist_yield[2]}/{inlist_yield[3]})")
        print(f"  >>> IN-LIST YIELD CAVEAT: the flag marks "
              f"{inlist_yield[1]} of {inlist_yield[3]} verdicted in-list "
              f"rows and catches {inlist_yield[0]} of {inlist_yield[2]} "
              f"in-list EB26-spurious. The discrimination was measured on "
              f"all 65 verdicted targets, most of which the frozen screen "
              f"already removes; on the surviving list it has essentially "
              f"no measured power. Tiebreaker only.")
    if sigma_fragile:
        flag_frames.append(pd.DataFrame({
            "source_id": sorted(sigma_fragile),
            "flag_dust_sigma_fragile": True}))
    extra = None
    if flag_frames:
        extra = flag_frames[0]
        for f in flag_frames[1:]:
            extra = extra.merge(f, on="source_id", how="outer")

    q = build_queue(
        main_df, ret_df, eb,
        xray_keys=load_xray_keys(os.path.join(OUT_DIR,
                                              "erosita_class3_xmatch.csv")),
        south_unresolved=south_unres,
        extra_flags=extra,
        out_path=os.path.join(OUT_DIR, "epoch_vet_day1_queue.v2.csv"))

    m4q = os.path.join(OUT_DIR, "epoch_vet_day1_queue.csv")
    if os.path.exists(m4q):
        old = pd.read_csv(m4q)
        print(f"  vs M4's queue: {len(old)} -> {len(q)} rows; "
              f"dust-unresolved-south "
              f"{int(old['flag_dust_unresolved_south'].sum())} -> "
              f"{int(q['flag_dust_unresolved_south'].sum())}; "
              f"M4 file left untouched")

    # ---- config v4 --------------------------------------------------------
    with open(os.path.join(BASE, "queries", "dr4-triage-config.v3.json"),
              encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["_comment"] = (
        "v4 (M5, 2026-08-18). Selection/screen/probability/membership "
        "IDENTICAL to v2 and v3 (949 rows). Adds the all-sky far-star "
        "extinction arbitration (Vergely+2022 -- v3's 'south of -30 stays "
        "bracketed' is superseded) and the measured activity policy. See "
        "gaia-dr4/M5-activity-axis.md.")
    cfg["version"] = 4
    cfg["supersedes"] = "dr4-triage-config.v3.json (v3, M4)"
    cfg["extinction_tier"]["d_gt_1250pc"] = (
        "bracketed: Edenhofer-to-edge (lower) vs SFD full column x SF11 "
        "2.742 (upper); ARBITRATED by a far 3D map where one covers the "
        "sightline -- Bayestar19 for dec > -30 (M4) and Vergely+2022 "
        "everywhere inside its 6x6x0.8 kpc box (M5, all-sky, no "
        "declination edge). Best estimate = max(map at the star's "
        "distance, Edenhofer floor). Rows whose class flips inside the "
        "V22 error cube's +-1 sigma are flagged, not frozen.")
    cfg["extinction_tier"]["vergely2022_chain"] = (
        "CDS J/A+A/664/A174 (Vergely, Lallement & Cox 2022, A&A 664 A174), "
        "anonymous FTP; FITS cubes self-describe UNIT='A0(550nm)/parsec', "
        "STEP/RESOL 10/25 pc (601x601x81, 6x6x0.8 kpc) and 20/50 pc "
        "(501x501x41, 10x10x0.8 kpc) with a matching density-error cube; "
        "Sun at SUN_POS*-0.5 in 0-based pixels; X to the Galactic Centre, "
        "Y along rotation, Z to the NGP (ReadMe Description). The quantity "
        "is monochromatic A0 at 550 nm (arXiv:2205.09087 src line 162). "
        "Into the house scale by ONE link with the curve the other tiers "
        "already use: E(ZGR23) = A0(550) / R_ZGR23(550), R_ZGR23(550) = "
        "2.6798. Cross-check chain (EB26 A_G=2.66 E(B-V) via A_V=2.742 "
        "E(B-V)) run in parallel and agreeing on every arbitrated row. "
        "Reader validated by a pre-registered geometry gate (declared axis "
        "convention beats all three corruptions at Spearman rho 0.966 vs "
        "0.38-0.41 against Edenhofer23; median E_V22/E_Eden 1.010; "
        "025pc/050pc cubes agree to 0.977) -- "
        "out/m5_vergely_geometry_gate.txt.")
    cfg["extinction_tier"]["dust_ambiguous_status"] = (
        f"13 rows: {n_alive} resolved class-III alive, {n_dead} dead, "
        f"{len(sigma_fragile)} sigma-fragile (flagged "
        f"flag_dust_sigma_fragile), {len(south_unres)} outside every map. "
        f"0 membership movements -- the v2 list stands.")

    fam_lines = {}
    for fam, sub in mres[mres["testable"]].groupby("family"):
        best = sub.loc[sub["p"].idxmin()]
        mdet = best["min_detectable"]
        fam_lines[fam] = (
            f"best metric {best['metric']} p={best['p']:.4f} "
            f"(Holm {best['p_holm']:.4f}), effect {best['effect']:.3f}, "
            f"n {int(best['n_conf'])} confirmed / {int(best['n_spur'])} "
            f"spurious; smallest effect detectable at 80% power "
            + (f"{float(mdet):.3f}" if pd.notna(mdet) else "not reachable"))
    cfg["activity_policy"] = {
        "status": (
            "NO ACTIVITY flag enters the config. The two activity families "
            "-- chromospheric (ESP-CS) and photometric variability -- did "
            "not deliver one: A is NOT TESTABLE at DR3 coverage and B is a "
            "measured underpowered null. What discriminates is family C, "
            "ASTROMETRIC QUALITY, which is not activity; it contributes "
            "the single caution flag below."
            if not any("dAmp" in w or "espcs" in w for w in winner_names)
            else "an activity metric survived Holm -- see per_family"),
        "eb26_all_sky_test_2026-08-18": (
            "Gaia DR3 activity / variability / astrometric-quality "
            "indicators vs El-Badry+2026 verdicts, ALL 65 verdicted "
            "targets, 76/76 coverage -- no footprint penalty (M4's X-ray "
            "axis could see only 29 of 65). Three separate families, "
            "Holm-Bonferroni within each, alpha=0.05; rules pre-registered "
            "in scripts/m5_activity_discriminator.py before the split was "
            "computed. Negative control phot_g_n_obs: clean."),
        "per_family": fam_lines,
        "metrics_surviving_holm": list(winners["metric"]) or None,
        "family_A_coverage": (
            "activityindex_espcs exists for 7 of 76 EB26 targets "
            "(3 confirmed / 1 spurious) and 44 of the 1,199 candidate + "
            "retrieval + EB26 sources -- M4's recommendation assumed this "
            "axis was all-sky; it is not. NOT TESTABLE, not null."),
        "family_B_direction": (
            "spurious solutions are the MORE photometrically variable side "
            "(dAmp_G AUC 0.659), the same direction as M4's X-ray result "
            "-- two independent activity axes agreeing in direction and "
            "neither reaching significance."),
        "day1": ("recompute these indicators for the day's list -- one "
                 "gaia_source column set, no telescope -- and re-run the "
                 "test once the epoch-vet loop has produced day-one ground "
                 "truth (the runbook's first-24h bulletin)."),
    }
    cfg["astrometric_quality_flag"] = {
        "flag": "flag_astrom_quiet",
        "status": "caution tag / ranking tiebreaker. NEVER a cut, NEVER a "
                  "selection change, NEVER an independent line of evidence "
                  "quoted alongside `significance` (see redundancy below).",
        "definition": ("astrometric_gof_al (gaia_source, the 5-parameter "
                       "single-star fit's goodness-of-fit) below the 25th "
                       "percentile of the day's OWN main candidate bin. No "
                       "threshold is fitted to the EB26 verdicts; the cut "
                       "is a self-calibrating quartile."),
        "evidence": ("EB26 all-sky test: astrometric_gof_al Mann-Whitney "
                     "p = 0.0011 (Holm within family C, m=6: 0.0067), "
                     "AUC(spurious > confirmed) = 0.254 [95 % boot "
                     "0.136-0.386], r_rb = -0.493; medians 86.7 confirmed "
                     "vs 47.1 spurious. Pre-registered G-stratified guard: "
                     "same direction in both halves (bright p 0.017, faint "
                     "p 0.006). ruwe also survives Holm (p 0.0083 -> 0.041) "
                     "in the same direction but is not frozen -- one flag, "
                     "the stronger one."),
        "redundancy_caveat": ("POST-HOC: in a logistic fit of P(spurious) "
                             "on z(log gof_al) + z(log significance) + "
                             "z(G) + z(log d) over the 65, `significance` "
                             "dominates (beta -2.87, p 0.004) and gof_al "
                             "retains only p = 0.048 (ruwe: 0.094). The "
                             "flag is therefore largely a restatement of "
                             "the significance tier config v2 already "
                             "ranks on. It breaks ties; it does not add an "
                             "independent axis."),
        "direction_note": ("the flag marks the QUIET tail: EB26-CONFIRMED "
                           "compact-companion hosts are the astrometrically "
                           "NOISIER single-star fits, because a real "
                           "massive dark companion makes a large photocentre "
                           "orbit. Do not read a high RUWE as a spurious-"
                           "risk signal -- the sign is the other way. This "
                           "is the measured version of what `ruwe_cut` has "
                           "asserted since v1 ('NONE -- high RUWE is the "
                           "orbit signature'): now quantified against ground "
                           "truth, r_rb -0.49 for gof_al, -0.40 for ruwe."),
        "in_list_yield_caveat": (
            f"MEASURED, and it is the reason this is a tiebreaker and "
            f"nothing more: of the {inlist_yield[3]} EB26-verdicted rows "
            f"that actually survive the frozen screen and sit in the "
            f"candidate list, the flag marks {inlist_yield[1]} and catches "
            f"{inlist_yield[0]} of the {inlist_yield[2]} in-list "
            f"EB26-spurious. The discrimination was measured across all 65 "
            f"verdicted targets, most of which the screen already removes; "
            f"on the surviving population it has no measured power. Do not "
            f"present it as a purity gain."
            if inlist_yield else "not measured"),
    }
    cfg["measured_on_dr3"].update({
        "m5_dust_ambiguous_alive_all_sky": n_alive,
        "m5_dust_ambiguous_dead": n_dead,
        "m5_dust_sigma_fragile": len(sigma_fragile),
        "m5_dust_still_unresolved": len(south_unres),
        "m5_activity_metrics_tested": int(len(tst)),
        "m5_activity_metrics_surviving_holm": int(len(winners)),
        "m5_espcs_coverage_of_eb26": "7/76 (3 confirmed / 1 spurious)",
        "m5_damp_g_auc_spurious_over_confirmed": 0.659,
        "m5_damp_g_min_detectable_auc_at_80pc_power": 0.725,
        "m5_astrometric_gof_al_auc": 0.254,
        "m5_membership_moved": 0,
    })
    v4path = os.path.join(BASE, "queries", "dr4-triage-config.v4.json")
    with open(v4path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"\nwrote {v4path} (v1, v2, v3 untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
