#!/usr/bin/env python
"""M3 task 3: December-2 dress rehearsal -- run the frozen pipeline
end-to-end against DR3 *as if it were DR4*, stage-timed, into
data/rehearsal/ (M2 production outputs are NOT touched).

Stages (each timed; failure branches noted in DR4-DAY-RUNBOOK.md):
  A. schema-pin      TAP_SCHEMA.schemas + .columns for the three tables the
                     day-one query touches; verify every column the patched
                     query needs exists live (the mechanical form of the
                     rename-map checklist in queries/dr3-to-dr4-tables.md).
  B. rename-patch    queries/01_nss_compact_companion_triage.sql (DR4 names)
                     -> DR3 executable via the rename map, DR4-only columns
                     stripped; validated live with a TOP 5 sync probe.
  C. plan-B pull     the range-partitioned sync pull (the async-queue
                     fallback that delivered M2), re-exercised in full into
                     data/rehearsal/range_chunks; exact-count guarded.
  D. triage          scripts/amrf_triage.py on the rehearsal parquet
                     (patched paths); BH1+BH2 acceptance gate must PASS.
  E. corrvec         not re-run here (politeness: the identical pull ran
                     today, 74 s for 4,203 rows in 11 sync chunks + 10 s
                     MC); timings carried into the table as measured.
  F. epoch-vet       scripts/vet_epoch_astrometry.py on the pre-release
                     epoch file (the DataLink stand-in), patched output.
  G. bulletin        day-one candidate bulletin CSV assembled from the
                     rehearsal triage + covariance probabilities (+ dust
                     tier columns when present).
  H. day-one queue   (M5) the epoch-vet queue, emitted BY THE DRIVER through
                     the shared builder scripts/m5_day1_queue.py -- main
                     class-III bin + the retrieval bin's Pr >= 0.999, every
                     caution flag, BH1/BH2 acceptance asserted inside the
                     builder.  M4 produced this file from a separate
                     one-off script; December 2 must not depend on anyone
                     remembering to run it.

Output: data/rehearsal/* + out/rehearsal_timings.csv
Run   : .venv/Scripts/python.exe scripts/rehearse_dr4_day.py
"""

import io
import os
import re
import sys
import time

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REH = os.path.join(BASE, "data", "rehearsal")
REH_OUT = os.path.join(REH, "out")
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"

# DR4 -> DR3 rename map (reverse of queries/dr3-to-dr4-tables.md) + the
# DR4-only columns the patch must strip when emulating on DR3.
RENAME = {
    "gaiadr4.": "gaiadr3.",
    "nss_masses": "binary_masses",
    "n.solution_type": "n.nss_solution_type",
    "n.gof": "n.goodness_of_fit",
}
DR4_ONLY_TOKENS = [
    "n.subtype", "n.semi_major_axis", "n.inclination", "n.arg_periastron",
    "n.pos_ascending_node", "n.mass_function", "n.bic", "n.tuwe",
    "n.astrometric_jitter", "g.has_epoch_astrometry", "m.flag AS nss_masses_flag",
]
DR4_ONLY_SOLUTION_TYPES = ["'OrbitalPoorlyConstrained', "]

TIMINGS = []
NOTES = {}          # stage -> free-text note carried into the timings CSV


def stage(name):
    def deco(fn):
        def wrapper(*a, **k):
            t0 = time.time()
            print(f"\n=== stage {name} ===", flush=True)
            try:
                result = fn(*a, **k)
                status = "OK"
            except Exception:
                TIMINGS.append({"stage": name,
                                "seconds": round(time.time()-t0, 1),
                                "status": "FAIL",
                                "note": NOTES.get(name, "")})
                raise
            TIMINGS.append({"stage": name, "seconds": round(time.time()-t0, 1),
                            "status": status, "note": NOTES.get(name, "")})
            print(f"=== stage {name}: {time.time()-t0:.1f}s ===", flush=True)
            return result
        return wrapper
    return deco


RETRIES = 6
BACKOFF_S = 5.0

# M5, 2026-08-18: ESAC's sync endpoint spent the afternoon alternating
# between 30-80 s replies, HTTP 500 and read-timeouts, and its
# TAP_SCHEMA.columns path was effectively unusable.  Two official Gaia
# partner-data-centre DR3 mirrors answered the same ADQL in under 2 s.
#
# WHERE FAILOVER IS AND IS NOT ALLOWED (this distinction is the point):
#   stage A (TAP_SCHEMA introspection) MAY fail over -- it asks "does this
#     column exist in gaiadr3", and a DR3 mirror answers that identically.
#   stage B/C (the actual data path) MUST NOT -- the rehearsal parquet has
#     to stay byte-identical to the M2/M3 production pull, and on
#     2026-12-02 only ESAC will have DR4 at all.  Those stay ESAC-only and
#     rely on the retry plus the pull's resumability.
SCHEMA_ENDPOINTS = [
    ("esac", ENDPOINT),
    ("ari", "https://gaia.ari.uni-heidelberg.de/tap/sync"),
]
SCHEMA_TIMEOUT = 30     # a TAP_SCHEMA query that takes 30 s is a sick
                        # endpoint, not a big query -- ARI answers in 0.6 s
SERVED_BY = {}          # stage -> set of hostnames that answered


def _sync(url, q, timeout):
    r = requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                 "FORMAT": "csv", "QUERY": q},
                      timeout=timeout)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def sync_csv(q, timeout=300):
    """Sync CSV against ESAC with bounded retry.  A retry cannot change the
    result; it only stops one flaky response from killing the rehearsal."""
    last = None
    for attempt in range(RETRIES):
        try:
            return _sync(ENDPOINT, q, timeout)
        except Exception as e:            # noqa: BLE001 - retry anything
            last = e
            if attempt == RETRIES - 1:
                break
            wait = BACKOFF_S * (attempt + 1)
            print(f"  sync_csv {type(e).__name__} -- retry "
                  f"{attempt+1}/{RETRIES-1} in {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"sync_csv failed after {RETRIES} attempts: "
                       f"{type(last).__name__}: {last}")


def sync_csv_schema(q, stage_name="A_schema_pin"):
    """TAP_SCHEMA introspection with endpoint failover (see the comment
    above for why this is allowed here and nowhere else).  Two attempts per
    endpoint, short timeout -- a schema query that takes 90 s is a sick
    endpoint, not a big query."""
    last = None
    for name, url in SCHEMA_ENDPOINTS:
        for attempt in range(2):
            try:
                df = _sync(url, q, SCHEMA_TIMEOUT)
                SERVED_BY.setdefault(stage_name, set()).add(name)
                return df
            except Exception as e:        # noqa: BLE001
                last = e
                print(f"  schema query on {name}: {type(e).__name__} "
                      f"(attempt {attempt+1}/2)", flush=True)
                time.sleep(BACKOFF_S)
    raise RuntimeError(f"schema query failed on every endpoint: "
                       f"{type(last).__name__}: {last}")


@stage("A_schema_pin")
def stage_a():
    schemas = sync_csv_schema("SELECT schema_name FROM TAP_SCHEMA.schemas")
    names = set(schemas["schema_name"].astype(str))
    assert "gaiadr3" in names, "gaiadr3 schema missing?!"
    print(f"schemas: {len(names)} (gaiadr3 present)")
    need = {
        "gaiadr3.nss_two_body_orbit": [
            "source_id", "nss_solution_type", "period", "eccentricity",
            "a_thiele_innes", "b_thiele_innes", "f_thiele_innes",
            "g_thiele_innes", "parallax", "significance", "goodness_of_fit",
            "corr_vec", "bit_index"],
        "gaiadr3.gaia_source": ["source_id", "ra", "dec", "l", "b",
                                "phot_g_mean_mag", "bp_rp", "ruwe",
                                "parallax_over_error"],
        "gaiadr3.binary_masses": ["source_id", "m1", "m1_ref",
                                  "combination_method"],
    }
    for tab, cols in need.items():
        live = sync_csv_schema(f"SELECT column_name FROM TAP_SCHEMA.columns "
                               f"WHERE table_name = '{tab}'")
        live_cols = set(live["column_name"].astype(str).str.lower())
        missing = [c for c in cols if c not in live_cols]
        print(f"{tab}: {len(live_cols)} live columns; "
              f"missing of ours: {missing if missing else 'none'}")
        assert not missing, f"{tab} misses {missing}"
    served = sorted(SERVED_BY.get("A_schema_pin", set()))
    print(f"schema introspection served by: {', '.join(served)}")
    if served != ["esac"]:
        NOTES["A_schema_pin"] = (
            f"ESAC's TAP_SCHEMA path was unusable; introspection failed "
            f"over to {', '.join(served)} (allowed: DR3 schema only, never "
            f"the data path)")


@stage("B_rename_patch")
def stage_b():
    src = os.path.join(BASE, "queries", "01_nss_compact_companion_triage.sql")
    sql = open(src, encoding="utf-8").read()
    # strip full-line AND inline comments before surgery (an inline comment
    # left in place glues onto the next select item after token removal)
    lines = [re.sub(r"--.*$", "", l).rstrip() for l in sql.splitlines()]
    body = "\n".join(l for l in lines if l.strip())
    # 1) the DR4 query derives a0_over_plx from semi_major_axis (DR4-only):
    #    patch that select item FIRST, before generic token removal
    body = re.sub(r"n\.semi_major_axis\s*/\s*n\.parallax\s+AS\s+a0_over_plx_au",
                  "n.parallax AS nss_parallax_dup", body)
    # 2) remove DR4-only select tokens; (?![\w]) stops semi_major_axis from
    #    also eating semi_major_axis_error
    for tok in DR4_ONLY_TOKENS:
        pat_err = re.escape(tok) + r"_error(?!\w)"   # matching _error twin
        pat = re.escape(tok) + r"(?!\w)(\s+AS\s+\w+)?"
        for p in (pat_err, pat):
            body = re.sub(r",\s*" + p, "", body)
            body = re.sub(p + r"\s*,", "", body)
    # 3) DR4-only solution types out of the IN list
    body = re.sub(r"'OrbitalPoorlyConstrained'\s*,\s*", "", body)
    for a, b in RENAME.items():
        body = body.replace(a, b)
    body = body.replace("SELECT TOP 100000", "SELECT TOP 5")
    patched = os.path.join(REH, "01_patched.dr3.sql")
    os.makedirs(REH, exist_ok=True)
    with open(patched, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    probe = sync_csv(body)
    print(f"patched query -> {patched}; live probe returned {len(probe)} "
          f"rows, {len(probe.columns)} cols")
    assert len(probe) == 5


@stage("C_planB_ranged_pull")
def stage_c():
    import glob
    import pull_dr3_nss_orbits_ranged as ranged
    ranged.RANGE_DIR = os.path.join(REH, "range_chunks")
    cached = len(glob.glob(os.path.join(ranged.RANGE_DIR, "range_*.parquet")))
    if cached:
        # The ranged puller is resumable by design: a range whose parquet is
        # already on disk with the expected count is skipped.  On a re-run
        # that means the wall clock measures cache validation + the live
        # histogram + the live exact-COUNT guard, NOT a fresh 169k-row pull.
        # Say so instead of quietly reporting a fast "pull".
        NOTES["C_planB_ranged_pull"] = (
            f"RESUMED from {cached} cached range chunks -- this timing is "
            f"cache validation + live histogram + live exact-COUNT guard, "
            f"not a fresh pull (fresh pull measured twice: M2 ~35 min, "
            f"M3 38.7 min, byte-identical parquets)")
        print(f"NOTE: {cached} range chunks already cached -- the pull will "
              f"resume, not re-download (see NOTES)")
    ranged.OUT_PARQUET = os.path.join(REH, "dr4day_input.parquet")
    ranged.OUT_NOTE = os.path.join(REH, "dr4day_input.NOTE.md")
    ranged.main()
    # cross-check against the M2 production pull: same archive, same query
    m2 = pd.read_parquet(os.path.join(BASE, "data",
                                      "dr3_nss_amrf_input.parquet"),
                         columns=["source_id"])
    rh = pd.read_parquet(ranged.OUT_PARQUET, columns=["source_id"])
    same = (len(m2) == len(rh)
            and int(m2["source_id"].sum()) == int(rh["source_id"].sum()))
    print(f"rehearsal pull vs M2 production pull: rows {len(rh)} vs "
          f"{len(m2)}, id-sum match: {same}")
    assert same, "rehearsal pull differs from M2 -- archive drift?!"


@stage("D_triage_acceptance")
def stage_d():
    import amrf_triage
    amrf_triage.IN_PARQUET = os.path.join(REH, "dr4day_input.parquet")
    amrf_triage.OUT_PARQUET = os.path.join(REH, "dr4day_triage.parquet")
    amrf_triage.OUT_DIR = REH_OUT
    os.makedirs(REH_OUT, exist_ok=True)
    old_argv = sys.argv
    sys.argv = ["amrf_triage.py"]
    try:
        rc = amrf_triage.main()
    finally:
        sys.argv = old_argv
    assert rc == 0, "BH1/BH2 acceptance gate FAILED in rehearsal"


@stage("E_corrvec_note")
def stage_e():
    print("corr_vec stage measured separately today (2026-08-16): "
          "targeted pull 4,203 rows / 11 sync chunks / 74 s; "
          "covariance MC 4,203 rows / 10 s. Not re-run (politeness).")
    TIMINGS.append({"stage": "E_corrvec_pull(measured)", "seconds": 74.0,
                    "status": "OK(measured)"})
    TIMINGS.append({"stage": "E_corrvec_mc(measured)", "seconds": 10.0,
                    "status": "OK(measured)"})


@stage("F_epoch_vet")
def stage_f():
    import vet_epoch_astrometry as vet
    vet.OUT = os.path.join(REH_OUT, "epoch_vetting_rehearsal.csv")
    rc = vet.main()
    assert rc == 0, "epoch-vet loop check FAILED in rehearsal"


@stage("G_bulletin")
def stage_g():
    tri = pd.read_parquet(os.path.join(REH, "dr4day_triage.parquet"))
    is3 = (tri["class_det"] == 3) & tri["cuts_eb26"]
    cand = tri[is3].copy()
    probs_p = os.path.join(BASE, "data", "dr3_corrvec_probs.parquet")
    if os.path.exists(probs_p):
        probs = pd.read_parquet(probs_p)[
            ["source_id", "nss_solution_type", "p_class3_corr",
             "sigma_A_corr"]]
        cand = cand.merge(probs, on=["source_id", "nss_solution_type"],
                          how="left")
    dust_p = os.path.join(BASE, "out", "dust_retriage.csv")
    if os.path.exists(dust_p):
        dust = pd.read_csv(dust_p)[
            ["source_id", "nss_solution_type", "dust_tier", "a_v_mag",
             "m1_dust", "class_det_dust"]]
        cand = cand.merge(dust, on=["source_id", "nss_solution_type"],
                          how="left")
    cand = cand.sort_values("m2_min_dark", ascending=False)
    keep = [c for c in ["source_id", "ra", "dec", "l", "b",
                        "nss_solution_type", "period", "a0_mas",
                        "nss_parallax", "significance", "m1_used",
                        "m1_source", "amrf", "a_tr_margin", "m2_min_dark",
                        "p_class3_mc", "p_class3_corr", "sigma_A_corr",
                        "dust_tier", "a_v_mag", "m1_dust", "class_det_dust",
                        "flag_alias_1yr", "flag_low_lat", "flag_sig_gt20"]
            if c in cand.columns]
    out = os.path.join(REH_OUT, "dr4day_bulletin.csv")
    cand[keep].to_csv(out, index=False, lineterminator="\n")
    print(f"bulletin: {len(cand)} candidates -> {out}")


@stage("H_day1_queue")
def stage_h():
    """M5: the epoch-vet queue falls out of the driver, not out of a
    separate script.  Built from the rehearsal's OWN triage output through
    the shared builder (which asserts the BH1/BH2 acceptance itself)."""
    from m5_day1_queue import build_queue, load_xray_keys, KEY, BASE_COLS

    tri = pd.read_parquet(os.path.join(REH, "dr4day_triage.parquet"))
    probs_p = os.path.join(BASE, "data", "dr3_corrvec_probs.parquet")
    probs = pd.read_parquet(probs_p)[KEY + ["p_class3_corr"]]
    tri = tri.merge(probs, on=KEY, how="left")

    is3 = tri["class_det"] == 3
    main_df = tri[is3 & tri["cuts_eb26"]].copy()
    ret_df = tri[is3 & tri["cuts_core"] & tri["cut_gof"]
                 & ~tri["cut_significance"]].copy()
    for d in (main_df, ret_df):
        d["m2_min"] = d["m2_min_dark"]
    print(f"from the rehearsal triage: main bin {len(main_df)}, "
          f"retrieval bin {len(ret_df)} "
          f"({int((ret_df['p_class3_corr'] >= 0.999).sum())} at Pr>=0.999)")

    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    ver_p = os.path.join(BASE, "out", "m5_vergely_dust_south.csv")
    south, fragile = set(), set()
    if os.path.exists(ver_p):
        ver = pd.read_csv(ver_p)
        south = set(ver.loc[ver["verdict"] == "UNRESOLVED_outside_box",
                            "source_id"])
        fragile = set(ver.loc[ver["verdict"]
                              == "UNRESOLVED_sigma_flips_verdict",
                              "source_id"])
    # M5 caution flag: astrometric_gof_al below the 25th percentile of the
    # day's OWN main bin (config v4 `astrometric_quality_flag`).  The column
    # is already in the triage output, so this costs nothing extra -- the
    # threshold is self-calibrating and moves with the release.
    frames = []
    if "astrometric_gof_al" in main_df.columns:
        thr = float(np.nanpercentile(main_df["astrometric_gof_al"], 25))
        quiet = pd.concat([main_df, ret_df])[["source_id",
                                              "astrometric_gof_al"]]
        quiet = quiet[quiet["astrometric_gof_al"] < thr]["source_id"]
        frames.append(pd.DataFrame({"source_id": sorted(set(quiet)),
                                    "flag_astrom_quiet": True}))
        print(f"flag_astrom_quiet: astrometric_gof_al < {thr:.2f} "
              f"(bottom quartile of the day's main bin)")
    if fragile:
        frames.append(pd.DataFrame({"source_id": sorted(fragile),
                                    "flag_dust_sigma_fragile": True}))
    extra = None
    if frames:
        extra = frames[0]
        for f in frames[1:]:
            extra = extra.merge(f, on="source_id", how="outer")

    q = build_queue(
        main_df, ret_df, eb,
        xray_keys=load_xray_keys(os.path.join(BASE, "out",
                                              "erosita_class3_xmatch.csv")),
        south_unresolved=south, extra_flags=extra,
        out_path=os.path.join(REH_OUT, "epoch_vet_day1_queue.csv"))
    # the rehearsal runs the pre-dust triage, so its main bin is the 951,
    # not the dust-corrected 949 -- state it rather than hide it
    prod = os.path.join(BASE, "out", "epoch_vet_day1_queue.v2.csv")
    if os.path.exists(prod):
        p = pd.read_csv(prod)
        print(f"vs the production (dust-corrected) queue: {len(q)} vs "
              f"{len(p)} rows -- the rehearsal driver stops before the "
              f"Phase-2 dust re-triage, so its main bin is the pre-dust "
              f"class-III set")


STAGES = [("A", stage_a), ("B", stage_b), ("C", stage_c), ("D", stage_d),
          ("E", stage_e), ("F", stage_f), ("G", stage_g), ("H", stage_h)]
STAGE_NAMES = {"A": "A_schema_pin", "B": "B_rename_patch",
               "C": "C_planB_ranged_pull", "D": "D_triage_acceptance",
               "E": "E_corrvec_note", "F": "F_epoch_vet", "G": "G_bulletin",
               "H": "H_day1_queue"}


def main(argv=None):
    """--stages ABCDEFGH selects which stages run (default: all).

    Stages A-C are the only network-bound ones.  When the archive is having
    the kind of afternoon ESAC had on 2026-08-18, `--stages DEFGH` still
    exercises everything downstream of the pull against the cached
    rehearsal artifacts, and the skipped stages are written into
    out/rehearsal_timings.csv as SKIPPED with the reason -- so a partial
    rehearsal can never be mistaken for a green one.
    """
    argv = sys.argv[1:] if argv is None else argv
    want = "ABCDEFGH"
    reason = ""
    if "--stages" in argv:
        want = argv[argv.index("--stages") + 1].upper()
    if "--reason" in argv:
        reason = argv[argv.index("--reason") + 1]
    t0 = time.time()
    os.makedirs(REH, exist_ok=True)
    for letter, fn in STAGES:
        if letter in want:
            fn()
        else:
            TIMINGS.append({"stage": STAGE_NAMES[letter], "seconds": 0.0,
                            "status": "SKIPPED",
                            "note": reason or "not requested"})
            print(f"\n=== stage {STAGE_NAMES[letter]}: SKIPPED "
                  f"({reason or 'not requested'}) ===")
    tdf = pd.DataFrame(TIMINGS)
    tdf = tdf.set_index("stage").reindex(
        [STAGE_NAMES[l] for l, _ in STAGES]
        + [s for s in tdf["stage"] if s not in STAGE_NAMES.values()]
    ).dropna(how="all").reset_index()
    tdf.to_csv(os.path.join(BASE, "out", "rehearsal_timings.csv"),
               index=False, lineterminator="\n")
    print("\n" + tdf.to_string(index=False))
    n_skip = int((tdf["status"] == "SKIPPED").sum())
    print(f"\nREHEARSAL {'COMPLETE' if not n_skip else 'PARTIAL'} in "
          f"{time.time()-t0:.0f}s"
          + (f" -- {n_skip} stage(s) SKIPPED, see the timings CSV"
             if n_skip else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
