#!/usr/bin/env python
"""M6 closeout: acceptance re-run, verdict-store build, config v5.

Same order and the same law as M4 and M5: the acceptance gates the config
write.  A config version is issued because M6 freezes new POLICY -- the
epoch-vet verdict rules, the verdict-record schema, and the measured
day-one throughput -- and because the `flag_astrom_quiet` decision has to
be recorded in the config, not only in a milestone document.

ACCEPTANCE (must PASS before anything is written):
  A1 Gaia BH1 + BH2 present in the v2 candidate list at Pr(III|corr) =
     1.0000 and top-2 by M2_min;
  A2 EB26 operating point re-measured THROUGH THE VERDICT STORE (not the
     fixture): 39/42 confirmed kept, 7/23 spurious passed.  Reading it
     through the store is itself part of the acceptance -- if the store
     does not reproduce the fixture's operating point, the store is wrong;
  A3 the verdict store validates against schemas/day1_verdict_record.v1.json;
  A4 the harness's end-to-end validation run reproduces M3's prototype:
     exactly the 3 pre-release orbit sources CONFIRMED, all 9 quiet ones
     SPURIOUS, and the f2 values agree with out/epoch_vetting_prototype.csv
     to within its own printed precision.

Config v5 (queries/dr4-triage-config.v5.json; v1-v4 untouched on disk):
selection, screen, probability method and membership IDENTICAL to v2/v3/v4
-- 949 rows, nothing about the candidate list changes.  What v5 adds:
  1. `verdict_schema`      the day-one verdict record and its scope rule;
  2. `epoch_vet_policy`    the pre-registered f2 verdict rules, the harness's
                           batching/politeness/resumability contract, and the
                           MEASURED throughput + projected day-one wall clock;
  3. `astrometric_quality_flag.m6_decision`  the flag_astrom_quiet decision
                           and the pre-registered test that settles it.

Run: .venv/Scripts/python.exe scripts/m6_acceptance_and_config.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as vs                      # noqa: E402
import epoch_vet_harness as evh                  # noqa: E402
from m5_day1_queue import BH1, BH2               # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "out")
QUERIES = os.path.join(BASE, "queries")

PRERELEASE_ORBIT_SOURCES = {
    4318465066420528000: "Gaia BH3",
    3937211745905473024: "HD 114762",
    1457486023639239296: "Gaia-4",
}


def _gaiasupdate_version():
    import gaiasupdate
    v = getattr(gaiasupdate, "__version__", None)
    if v:
        return v
    try:
        from importlib.metadata import version
        return version("gaiasupdate")
    except Exception:                                   # noqa: BLE001
        return "UNKNOWN"


def main():
    print("=== M6 acceptance re-run (selection identical to v2/v3/v4) ===")
    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))

    # ---- A1 ---------------------------------------------------------------
    for name, sid in (("BH1", BH1), ("BH2", BH2)):
        row = v2[v2["source_id"] == sid]
        assert len(row) == 1, f"{name} missing from candidate list"
        pr = float(row["p_class3_corr"].iloc[0])
        m2 = float(row["m2_min_dark_dust"].iloc[0])
        print(f"  A1 {name}: present, Pr(III|corr) = {pr:.4f}, "
              f"M2_min = {m2:.2f}")
        assert pr >= 0.9999, f"{name} Pr regression"
    top2 = set(v2.sort_values("m2_min_dark_dust", ascending=False)
                 .head(2)["source_id"].tolist())
    assert top2 == {BH1, BH2}, f"top-2 by M2_min changed: {top2}"
    print("  A1 top-2 by M2_min: BH1 + BH2 -- PASS")

    # ---- A2, through the store -------------------------------------------
    store_eb = vs.load_store([os.path.join(vs.STORE_DIR, "eb26.v1.csv")])
    memb = set(v2["source_id"])
    kept = int(store_eb.loc[store_eb["verdict"] == "CONFIRMED", "source_id"]
               .isin(memb).sum())
    passed = int(store_eb.loc[store_eb["verdict"] == "SPURIOUS", "source_id"]
                 .isin(memb).sum())
    print(f"  A2 EB26 operating point READ THROUGH THE VERDICT STORE: "
          f"{kept}/42 confirmed kept, {passed}/23 spurious passed")
    assert (kept, passed) == (39, 7), "operating point drifted"

    # and the store must reproduce the fixture it replaces, column for column
    fix = pd.read_csv(os.path.join(BASE, "fixtures",
                                   "elbadry2026_astrometric_candidates.csv"))
    compat = vs.eb26_compatible_frame(store_eb)
    for col in ("source_id", "period_d", "significance", "verdict"):
        assert (compat[col].values == fix[col].values).all(), \
            f"store does not reproduce the fixture's {col}"
    n1 = compat["notes"].fillna("~NA~").values
    n2 = fix["notes"].fillna("~NA~").values
    assert (n1 == n2).all(), "store does not reproduce the fixture's notes"
    print("  A2 store reproduces the fixture on every consumed column -- PASS")

    # ---- A3 ---------------------------------------------------------------
    paths = sorted(os.path.join(vs.STORE_DIR, f)
                   for f in os.listdir(vs.STORE_DIR) if f.endswith(".csv"))
    store_all = vs.load_store(paths)
    vs.validate(store_all)          # raises on any violation
    print(f"  A3 verdict store validates: {len(store_all)} records from "
          f"{len(paths)} file(s)")
    print(f"     {vs.scope_composition_string(store_all)}")

    # ---- A4 ---------------------------------------------------------------
    led_p = os.path.join(vs.STORE_DIR, "harness_prerelease.v1.csv")
    assert os.path.exists(led_p), \
        "run scripts/epoch_vet_harness.py --source prerelease first"
    led = vs.load_store([led_p])
    keep = set(led.loc[led["verdict"] == "CONFIRMED", "source_id"]
               .astype("int64"))
    demote = set(led.loc[led["verdict"] == "SPURIOUS", "source_id"]
                 .astype("int64"))
    assert keep == set(PRERELEASE_ORBIT_SOURCES), \
        f"harness kept {keep}, expected {set(PRERELEASE_ORBIT_SOURCES)}"
    assert len(demote) == 9, f"harness demoted {len(demote)}, expected 9"
    proto = pd.read_csv(os.path.join(OUT_DIR, "epoch_vetting_prototype.csv"))
    j = proto.set_index("source_id").join(
        led.set_index("source_id")[["f2_single_star"]], rsuffix="_h")
    dmax = float((j["f2_single_star_h"] - j["f2_single_star"]).abs().max())
    assert dmax <= 0.005, f"f2 drift vs the M3 prototype: {dmax}"
    print(f"  A4 harness end-to-end: {len(keep)}/3 kept, {len(demote)}/9 "
          f"demoted; max |delta f2| vs the M3 prototype = {dmax:.4f} "
          f"(= its own 2-dp rounding) -- PASS")
    print("  ACCEPTANCE PASS -- config v5 may be written")

    # ---- gather what M6 measured -----------------------------------------
    proj_csv = os.path.join(OUT_DIR, "m6_throughput_projection.csv")
    thr = {}
    if os.path.exists(proj_csv):
        pj = pd.read_csv(proj_csv)
        sel = pj[(pj["batch"] == 20) & (pj["degrade"] == 1.0)]
        for _, r in sel.iterrows():
            thr[f"model_{r['model']}_sources_per_hour"] = round(
                float(r["sources_per_hour"]), 1)
            thr[f"model_{r['model']}_hours_for_983"] = round(
                float(r["hours_for_queue"]), 2)
        worst = pj[(pj["batch"] == 20) & (pj["degrade"] == 10.0)
                   & (pj["model"] == "A")]
        if len(worst):
            thr["model_A_degraded10x_hours_for_983"] = round(
                float(worst["hours_for_queue"].iloc[0]), 1)
        thr["fit_seconds_per_source"] = round(
            float(sel["fit_s_per_source"].iloc[0]), 4) if len(sel) else None

    aq_txt = os.path.join(OUT_DIR, "m6_astrom_quiet_decision.txt")
    aq_decision, aq_lines = "NOT RUN", []
    if os.path.exists(aq_txt):
        aq_lines = open(aq_txt, encoding="utf-8").read().splitlines()
        for ln in aq_lines:
            if ln.strip().startswith("-> "):
                aq_decision = ln.strip()[3:].strip()
    aq_inlist = os.path.join(OUT_DIR, "m6_astrom_quiet_inlist.csv")
    aq_nums = {}
    if os.path.exists(aq_inlist):
        ai = pd.read_csv(aq_inlist)
        for _, r in ai.iterrows():
            aq_nums[f"{r['metric']}|{r['population']}"] = {
                "n_conf": int(r["n_conf"]), "n_spur": int(r["n_spur"]),
                "p": round(float(r["p"]), 4), "auc": round(float(r["auc"]), 3),
                "auc_ci": [round(float(r["auc_lo"]), 3),
                           round(float(r["auc_hi"]), 3)],
                "min_detectable_auc": (None
                                       if not np.isfinite(r["min_detectable_auc"])
                                       else round(float(r["min_detectable_auc"]), 3))}

    # ---- config v5 --------------------------------------------------------
    with open(os.path.join(QUERIES, "dr4-triage-config.v4.json"),
              encoding="utf-8") as fh:
        cfg = json.load(fh)

    cfg["_comment"] = (
        "v5 (M6, 2026-08-21). Selection/screen/probability/membership "
        "IDENTICAL to v2, v3 and v4 (949 rows) -- M6 changed nothing about "
        "the candidate list. It adds the day-one VERDICT RECORD schema, the "
        "epoch-vet harness policy with its MEASURED throughput, and the "
        "flag_astrom_quiet decision. See gaia-dr4/M6-verdict-harness.md.")
    cfg["version"] = 5
    cfg["supersedes"] = "dr4-triage-config.v4.json (v4, M5)"

    cfg["verdict_schema"] = {
        "schema_version": vs.SCHEMA_VERSION,
        "definition": "schemas/day1_verdict_record.v1.json",
        "code": "scripts/verdict_schema.py",
        "store": "out/verdicts/*.csv (one file per producer)",
        "producers": {
            "elbadry2026": "the published follow-up table, scope "
                           "compact_companion, basis rv_followup",
            "epoch_vet_harness": "scripts/epoch_vet_harness.py, scope "
                                 "orbit_reality, basis epoch_astrometry_f2",
        },
        "verdict_vocabulary": vs.VERDICT_VOCAB,
        "scope_vocabulary": vs.SCOPE_VOCAB,
        "scope_rule": (
            "verdict_scope is MANDATORY and is the honest part of the "
            "schema. `compact_companion` answers 'is there a dark massive "
            "companion?'; `orbit_reality` answers 'does the published "
            "photocentre orbit have epoch-level support?'. A harness "
            "SPURIOUS and an EB26 SPURIOUS mean nearly the same thing; a "
            "harness CONFIRMED is WEAKER than an EB26 CONFIRMED (orbit "
            "real, companion nature unestablished). Pooling the scopes is "
            "therefore ASYMMETRIC. Any consumer that pools them must print "
            "the scope composition of both groups -- the M4 and M5 tests "
            "now do this automatically whenever the store carries more "
            "than one (source, scope) combination."),
        "consumers_wired": [
            "scripts/m4_eb26_erosita_test.py --verdicts ... --scopes ...",
            "scripts/m5_activity_discriminator.py --verdicts ... --scopes ...",
            "scripts/m6_astrom_quiet_decision.py --verdicts ...",
        ],
        "refactor_acceptance_2026-08-21": (
            "all five frozen M4/M5 artifacts reproduce BYTE-IDENTICALLY "
            "through the store: m4_eb26_erosita_xmatch.csv, "
            "m4_eb26_discriminator_stats.txt, m5_activity_eb26_table.csv, "
            "m5_activity_metric_results.csv, "
            "m5_activity_discriminator_stats.txt."),
    }

    cfg["epoch_vet_policy"] = {
        "harness": "scripts/epoch_vet_harness.py (" + evh.HARNESS_VERSION + ")",
        "input": "the day-one queue (out/epoch_vet_day1_queue*.csv), in rank "
                 "order",
        "fetch": (
            "Gaia DataLink, retrieval_type=EPOCH_ASTROMETRY, "
            "data_structure=RAW, BATCHED (one request serves `batch` "
            "sources; gaiasupdate's own from_gacs_datalink() sends one id "
            "per request and is deliberately not used). Epoch astrometry is "
            "DataLink-only -- there is no TAP join (M1 finding #1)."),
        "fit": (f"gaiasupdate {_gaiasupdate_version()} single-star fit "
                f"(6p_constrained_colour, the DR4-like configuration)"),
        "day1_probe_REQUIRED": (
            "MEASURED 2026-08-21: asking the live ESAC data server for "
            "retrieval_type='EPOCH_ASTROMETRY' returns HTTP 500 with the "
            "body 'Unknown retrieval type: EPOCH_ASTROMETRY' for BOTH "
            "RELEASE='Gaia DR4' and 'Gaia DR4_INT4' -- the service does not "
            "serve it yet, and astroquery 0.4.11 lists the type client-side "
            "so nothing catches it earlier. On 2026-12-02, probe one source "
            "through DataLink BEFORE starting the harness and read the "
            "BODY of any 500: a deterministic rejection is a wrong "
            "retrieval_type/release pair, not a flaky archive. The harness "
            "now fails fast on those markers instead of burning six "
            "backoffs (scripts/epoch_vet_harness.py _is_deterministic)."),
        "pre_registered_rules": {
            "f2_gate": evh.F2_GATE,
            "min_transits": evh.MIN_TRANSITS,
            "RULE_1": f"n_used < {evh.MIN_TRANSITS} -> INCONCLUSIVE (not a "
                      f"demotion)",
            "RULE_2": f"|f2| > {evh.F2_GATE} -> CONFIRMED (orbit_reality): "
                      f"epoch-level wobble present -> orbital refit",
            "RULE_3": f"|f2| <= {evh.F2_GATE} -> SPURIOUS (orbit_reality): "
                      f"no epoch support for the claimed photocentre orbit",
            "RULE_4": "DataLink served nothing -> NO_DATA",
            "RULE_5": "the fit raised -> ERROR with the exception text; "
                      "never silently dropped",
            "confidence": f"r = |f2|/{evh.F2_GATE}; HIGH if r >= "
                          f"{evh.CONF_FACTOR} or r <= "
                          f"{1/evh.CONF_FACTOR:.2f}; MEDIUM within a factor "
                          f"{evh.CONF_FACTOR} of the gate; LOW if "
                          f"INCONCLUSIVE/NO_DATA/ERROR or n_used < "
                          f"{evh.LOW_CONFIDENCE_TRANSITS}",
        },
        "operational_contract": {
            "resumable": "per-source epoch parquet cache "
                         "(data/epoch_cache/<release>/) written atomically, "
                         "plus an append-only verdict ledger; a session kill "
                         "costs at most the batch in flight",
            "politeness": f"{evh.GAP_S} s between requests, {evh.RETRIES} "
                          f"retries with exponential backoff, HTTP "
                          f"429/503 Retry-After honoured to the second",
            "instrumented": "per-batch and per-source timings appended to "
                            "out/m6_harness_timings.csv every run",
        },
        "measured_2026-08-21": {
            "validation": "12/12 pre-release sources; 3 CONFIRMED (Gaia BH3 "
                          "f2 894.0, HD 114762 186.5, Gaia-4 31.5), 9 "
                          "SPURIOUS (|f2| <= 1.55) -- reproduces M3's "
                          "prototype, max |delta f2| 0.005",
            "fit_throughput": thr.get("fit_seconds_per_source"),
            "datalink_probe": "DR3 EPOCH_PHOTOMETRY as a labelled PROXY "
                              "(DR4 epoch astrometry does not exist yet); "
                              "out/m6_datalink_probe.csv",
            "projection_band_batch20_undegraded": {
                "sources_per_hour": [thr.get("model_B_sources_per_hour"),
                                     thr.get("model_A_sources_per_hour")],
                "hours_for_983_row_queue": [thr.get("model_B_hours_for_983"),
                                            thr.get("model_A_hours_for_983")],
            },
            "degraded_10x_hours_for_983": thr.get(
                "model_A_degraded10x_hours_for_983"),
            "note": "the band is spanned by two models fitted to the same "
                    "calls (per-source server work vs per-byte transport); "
                    "they differ only because DR4's payload per source is "
                    "~7x the probe's. RE-MEASURE on 2026-12-02 before "
                    "choosing a batch size -- it takes ~6 minutes.",
        },
        "day1_consequence": (
            "the queue is RANKED and the harness consumes it in rank order, "
            "so a slow archive costs DEPTH, not the headline: BH1, BH2 and "
            "the EB26-refuted poster child are adjudicated in the first "
            "minutes under every branch measured."),
    }

    cfg["astrometric_quality_flag"]["m6_decision"] = {
        "decision": aq_decision,
        "test": "scripts/m6_astrom_quiet_decision.py; "
                "out/m6_astrom_quiet_decision.txt",
        "what_m6_added": (
            "M5 measured astrometric_gof_al across all 65 verdicted EB26 "
            "targets. The flag does not operate on those 65 -- it operates "
            "on the day-one queue, and the frozen screen removes most of "
            "the 65 before the flag is ever computed. M6 re-asked the "
            "question on the flag's OWN operating population (the verdicted "
            "rows that are IN the queue) and computed the power of that "
            "test exactly."),
        "in_list_numbers": aq_nums,
        "why_0_of_7_is_not_evidence": (
            "at the flag's measured in-list marking rate, the EXPECTED "
            "catch among the 7 in-list spurious rows is well below 1. "
            "Observing 0 is what a working flag and a dead flag both "
            "predict. The in-list test has no power; M5's '0 of 7' is a "
            "statement about the sample size, not about the flag."),
        "december_decision_rule_preregistered": {
            "KEEP": "the in-list continuous test reaches p < 0.05 two-sided "
                    "in the M5 direction (AUC < 0.5) AND the thresholded "
                    "flag's in-list catch rate beats its marking rate at "
                    "Fisher p < 0.05",
            "REMOVE": "the in-list test is well powered (smallest "
                      "detectable AUC <= 0.70) and the observed in-list AUC "
                      "is consistent with 0.5",
            "CARRY": "anything else -- the flag stays exactly as v4 froze "
                     "it, tiebreaker only, both caveats attached",
        },
        "status_unchanged_from_v4": True,
    }

    cfg["measured_on_dr3"].update({
        "m6_verdict_records_eb26": int(len(store_eb)),
        "m6_verdict_records_harness_prerelease": int(len(led)),
        "m6_harness_prerelease_kept": int(len(keep)),
        "m6_harness_prerelease_demoted": int(len(demote)),
        "m6_refactor_byte_identical_artifacts": 5,
        "m6_fit_seconds_per_source": thr.get("fit_seconds_per_source"),
        "m6_projected_sources_per_hour_band": [
            thr.get("model_B_sources_per_hour"),
            thr.get("model_A_sources_per_hour")],
        "m6_projected_hours_for_983_queue": [
            thr.get("model_B_hours_for_983"),
            thr.get("model_A_hours_for_983")],
        "m6_astrom_quiet_decision": aq_decision,
        "m6_membership_moved": 0,
    })

    out = os.path.join(QUERIES, "dr4-triage-config.v5.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(out, BASE)} "
          f"(v1-v4 untouched on disk; membership unchanged at 949)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
