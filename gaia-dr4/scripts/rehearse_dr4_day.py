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


def stage(name):
    def deco(fn):
        def wrapper(*a, **k):
            t0 = time.time()
            print(f"\n=== stage {name} ===", flush=True)
            try:
                result = fn(*a, **k)
                status = "OK"
            except Exception:
                TIMINGS.append({"stage": name, "seconds": round(time.time()-t0, 1),
                                "status": "FAIL"})
                raise
            TIMINGS.append({"stage": name, "seconds": round(time.time()-t0, 1),
                            "status": status})
            print(f"=== stage {name}: {time.time()-t0:.1f}s ===", flush=True)
            return result
        return wrapper
    return deco


def sync_csv(q, timeout=300):
    r = requests.post(ENDPOINT, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                      "FORMAT": "csv", "QUERY": q},
                      timeout=timeout)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


@stage("A_schema_pin")
def stage_a():
    schemas = sync_csv("SELECT schema_name FROM TAP_SCHEMA.schemas")
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
        live = sync_csv(f"SELECT column_name FROM TAP_SCHEMA.columns "
                        f"WHERE table_name = '{tab}'")
        live_cols = set(live["column_name"].astype(str).str.lower())
        missing = [c for c in cols if c not in live_cols]
        print(f"{tab}: {len(live_cols)} live columns; "
              f"missing of ours: {missing if missing else 'none'}")
        assert not missing, f"{tab} misses {missing}"


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
    import pull_dr3_nss_orbits_ranged as ranged
    ranged.RANGE_DIR = os.path.join(REH, "range_chunks")
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


def main():
    t0 = time.time()
    os.makedirs(REH, exist_ok=True)
    stage_a()
    stage_b()
    stage_c()
    stage_d()
    stage_e()
    stage_f()
    stage_g()
    tdf = pd.DataFrame(TIMINGS)
    tdf.to_csv(os.path.join(BASE, "out", "rehearsal_timings.csv"),
               index=False, lineterminator="\n")
    print("\n" + tdf.to_string(index=False))
    print(f"\nREHEARSAL COMPLETE in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
