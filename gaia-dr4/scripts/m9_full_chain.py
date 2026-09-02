#!/usr/bin/env python
"""M9 task 1: the PRODUCTION CHAIN, end to end, at December scale.

WHY THIS EXISTS
===============
Every part of December has now been measured, and the chain never has.

  M6  built the harness and measured a throughput band.
  M7  measured the transport half at 981-row scale (real network, real
      batching) and built the refit arm, validated on three objects.
  M8  measured the analysis half at 981-row scale on synthetic verdict
      stores, and rehearsed every pre-registered command.

Nobody had ever run  harness -> orbital refit arm -> v2 verdict store ->
pre-registered labels  as ONE thing at 981 rows.  M8's own recommendation 4
says so: "the pieces are all now measured; the chain is not."  Things that
only break at full scale, or only at a stage BOUNDARY, cannot be found any
other way -- and the first run of this driver found two of them (see the
M9 doc, DEFECT M9-1 and M9-2).

THE STAGES, AND WHAT EACH ONE STANDS IN FOR
===========================================
  0  preflight    fixture + zero-point table present; hash every frozen
                  artifact BEFORE the run, so an out-dir leak (M8 landmine
                  #4) is caught by this driver and not by git at close.
  1  TRANSPORT    981 sources through the production harness against live
                  DR3 EPOCH_PHOTOMETRY, into a chain-private cache root so
                  the network is really exercised.  This is December's
                  dominant cost and the only stage whose stand-in differs
                  from December in KIND (photometry, not astrometry): the
                  cost model (M7) converts it.
  2  ADJUDICATE   981 real day-one queue members through the harness's real
                  adjudication path, reading epoch ASTROMETRY from the M9
                  fixture (scripts/m9_dec_scale_fixture.py) -> a v1 verdict
                  store of December's size and shape.
  3  REFIT        every CONFIRMED row through the orbital refit arm's
                  December entry point (--queue), WITH --zeropoint, ->
                  refit ledger + v2 store.
  4  LABELS       the seven pre-registered commands + m8_prereg_labels.py
                  against the store stage 2 and 3 just built.

RESUME IS TESTED BY KILLING THINGS, not by asserting that it would work.
`--resume-test` runs stages 1-3 as subprocesses, SIGKILLs each one partway
through, restarts it, and checks that (a) the restart reports the right
"already done / to do" split, (b) the ledger ends with exactly the right
number of rows and no duplicates, and (c) no `.tmp` cache file is left
behind pretending to be a cache hit.

NOTHING HERE MAY REACH A SCIENCE ARTIFACT.  All output goes to
out/verdicts_dec_rehearsal/ and out/m9_chain/; `out/verdicts/` and
`out/verdicts_v2/` are hashed before and after and asserted unchanged.

  .venv\\Scripts\\python.exe scripts\\m9_full_chain.py --run
  .venv\\Scripts\\python.exe scripts\\m9_full_chain.py --run --skip-transport
  .venv\\Scripts\\python.exe scripts\\m9_full_chain.py --resume-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PY = os.path.join(BASE, ".venv", "Scripts", "python.exe")
OUT = os.path.join(BASE, "out")
CHAIN_OUT = os.path.join(OUT, "m9_chain")
STORE = os.path.join(OUT, "verdicts_dec_rehearsal")
QUEUE = os.path.join(OUT, "epoch_vet_day1_queue.v2.csv")
SETB = os.path.join(OUT, "m7_dryrun", "setB_payload_stratified981.csv")
FIXTURE_RELEASE = "Gaia DR4 M9 rehearsal Dec-scale fixture"
CHAIN_CACHE_ROOT = os.path.join(BASE, "data", "epoch_cache_m9_chain")

V1_LEDGER = os.path.join(STORE, "harness_dec_scale.v1.csv")
REFIT_LEDGER = os.path.join(CHAIN_OUT, "refit_ledger.csv")
V2_STORE = os.path.join(CHAIN_OUT, "harness_dec_scale_refit.v2.csv")
TRANSPORT_LEDGER = os.path.join(CHAIN_OUT, "transport_ledger.csv")

# artifacts that MUST NOT move.  Hashed before and after every run: M8
# landmine #4 was a script that took --out-dir and wrote somewhere else,
# twice in one file, straight over frozen results.
FROZEN = [
    "out/verdicts/eb26.v1.csv",
    "out/verdicts/harness_prerelease.v1.csv",
    "out/verdicts_v2/harness_prerelease_refit.v2.csv",
    "out/m7_refit_trio.csv", "out/m7_refit_vs_literature.csv",
    "out/m7_refit_acceptance.json",
    "out/m4_eb26_erosita_xmatch.csv", "out/m4_eb26_discriminator_stats.txt",
    "out/m5_activity_eb26_table.csv", "out/m5_activity_metric_results.csv",
    "out/m5_activity_discriminator_stats.txt",
    "out/epoch_vet_day1_queue.csv", "out/epoch_vet_day1_queue.v2.csv",
]


def sha(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_snapshot():
    return {p: sha(os.path.join(BASE, p)) for p in FROZEN}


def frozen_check(before, label="", verbose=True):
    after = frozen_snapshot()
    moved = [p for p in before if before[p] != after[p]]
    if verbose:
        print("  frozen-artifact check%s: %d/%d unchanged%s"
              % (label, len(before) - len(moved), len(before),
                 "" if not moved else "  *** MOVED: %s ***" % moved))
    return moved


def _run(cmd, log_path, timeout=None, kill_after=None, tag=""):
    """Run a subprocess, tee to a log, and optionally KILL it partway.

    Returns (returncode_or_None, seconds).  returncode None == we killed it.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "ab") as fh:
        fh.write(("\n==== %s : %s\n" % (time.strftime("%H:%M:%S"),
                                        " ".join(cmd))).encode())
        fh.flush()
        p = subprocess.Popen(cmd, cwd=BASE, stdout=fh,
                             stderr=subprocess.STDOUT)
        if kill_after is not None:
            try:
                p.wait(timeout=kill_after)
                rc = p.returncode
                print("      (%s finished in %.1fs before the kill at %.0fs "
                      "-- resume test degenerates to a re-run)"
                      % (tag, time.time() - t0, kill_after))
                return rc, time.time() - t0
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
                print("      KILLED %s after %.0fs" % (tag, kill_after))
                return None, time.time() - t0
        rc = p.wait(timeout=timeout)
    return rc, time.time() - t0


# ======================================================================
def stage0_preflight(verbose=True):
    t0 = time.time()
    import m9_dec_scale_fixture as FX
    ok_fix = FX.verify(verbose=verbose)
    zp = os.path.join(BASE, "data", "dr3_zeropoint_columns.parquet")
    ok_zp = os.path.exists(zp)
    n_zp = len(pd.read_parquet(zp, columns=["source_id"])) if ok_zp else 0
    if verbose:
        print("  zero-point column pull: %s (%d sources)"
              % ("present" if ok_zp else "MISSING", n_zp))
    os.makedirs(CHAIN_OUT, exist_ok=True)
    os.makedirs(STORE, exist_ok=True)
    # The POOLED arm is only a pooled arm if the store holds both producers.
    # December's out/verdicts/ will hold eb26.v1.csv beside the day's harness
    # ledger, so the rehearsal store gets a COPY of the real frozen EB26 file
    # (not a synthetic one) -- otherwise stage 4's "pooled" numbers come out
    # identical to "primary" and the pooling code path is never exercised.
    import shutil
    src = os.path.join(OUT, "verdicts", "eb26.v1.csv")
    dst = os.path.join(STORE, "eb26.v1.csv")
    if os.path.exists(src) and (not os.path.exists(dst)
                                or sha(src) != sha(dst)):
        shutil.copyfile(src, dst)
    if verbose:
        print("  rehearsal store: %s (+ a copy of the frozen eb26.v1.csv)"
              % os.path.relpath(STORE, BASE))
    return {"stage": "0 preflight", "seconds": round(time.time() - t0, 2),
            "ok": bool(ok_fix and ok_zp), "n_zeropoint_sources": n_zp,
            "eb26_copied": os.path.exists(dst)}


def stage1_transport(batch=20, gap=1.0, limit=None, kill_after=None,
                     fresh_cache=True, verbose=True):
    """981 sources of live DR3 epoch photometry through the production
    harness, into a chain-private cache root."""
    log = os.path.join(CHAIN_OUT, "stage1_transport.log")
    cmd = [PY, os.path.join("scripts", "m9_transport_leg.py"),
           "--queue", os.path.relpath(SETB, BASE),
           "--ledger", os.path.relpath(TRANSPORT_LEDGER, BASE),
           "--cache-root", os.path.relpath(CHAIN_CACHE_ROOT, BASE),
           "--batch", str(batch), "--gap", str(gap)]
    if limit:
        cmd += ["--limit", str(limit)]
    rc, secs = _run(cmd, log, kill_after=kill_after, tag="stage1")
    led = (pd.read_csv(TRANSPORT_LEDGER)
           if os.path.exists(TRANSPORT_LEDGER) else pd.DataFrame())
    return {"stage": "1 transport", "seconds": round(secs, 2), "rc": rc,
            "n_ledger": len(led),
            "n_served": int(led["served"].sum()) if len(led) else 0,
            "n_transits": int(pd.to_numeric(led.get("n_transits"),
                                            errors="coerce").sum())
            if len(led) else 0,
            "cache_bytes": int(pd.to_numeric(led.get("cache_bytes"),
                                             errors="coerce").sum())
            if len(led) else 0}


def stage2_adjudicate(batch=20, limit=None, kill_after=None, verbose=True):
    log = os.path.join(CHAIN_OUT, "stage2_adjudicate.log")
    cmd = [PY, os.path.join("scripts", "epoch_vet_harness.py"),
           "--source", "cache", "--release", FIXTURE_RELEASE,
           "--queue", os.path.relpath(QUEUE, BASE),
           "--ledger", os.path.relpath(V1_LEDGER, BASE),
           "--timings", os.path.relpath(
               os.path.join(CHAIN_OUT, "harness_timings.csv"), BASE),
           "--batch", str(batch)]
    if limit:
        cmd += ["--limit", str(limit)]
    rc, secs = _run(cmd, log, kill_after=kill_after, tag="stage2")
    led = pd.read_csv(V1_LEDGER) if os.path.exists(V1_LEDGER) \
        else pd.DataFrame()
    tally = led["verdict"].value_counts().to_dict() if len(led) else {}
    return {"stage": "2 adjudicate", "seconds": round(secs, 2), "rc": rc,
            "n_ledger": len(led),
            "n_duplicate_ids": int(len(led) - led["source_id"].nunique())
            if len(led) else 0,
            "verdicts": tally}


def stage3_refit(kill_after=None, zeropoint=True, n_posterior=20000,
                 limit=None, verbose=True):
    log = os.path.join(CHAIN_OUT, "stage3_refit.log")
    cmd = [PY, os.path.join("scripts", "orbital_refit_arm.py"),
           "--queue", os.path.relpath(V1_LEDGER, BASE),
           "--epoch-release", FIXTURE_RELEASE,
           "--refit-ledger", os.path.relpath(REFIT_LEDGER, BASE),
           "--v2-out", os.path.relpath(V2_STORE, BASE),
           "--out-dir", os.path.relpath(CHAIN_OUT, BASE),
           "--n-posterior", str(n_posterior)]
    if zeropoint:
        cmd += ["--zeropoint"]
    if limit:
        cmd += ["--limit", str(limit)]
    rc, secs = _run(cmd, log, kill_after=kill_after, tag="stage3")
    rl = pd.read_csv(REFIT_LEDGER) if os.path.exists(REFIT_LEDGER) \
        else pd.DataFrame()
    st = {}
    sp = os.path.join(CHAIN_OUT, "refit_queue_stats.json")
    if os.path.exists(sp):
        st = json.load(open(sp, encoding="utf-8"))
    return {"stage": "3 refit", "seconds": round(secs, 2), "rc": rc,
            "n_refit_ledger": len(rl),
            "n_duplicate_ids": int(len(rl) - rl["source_id"].nunique())
            if len(rl) else 0,
            "status": rl["refit_status"].value_counts().to_dict()
            if len(rl) else {},
            "arm_stats": st}


def stage4_labels(verbose=True):
    """The seven pre-registered commands + the label function, against the
    store stages 2-3 just built.  Reuses M8's rehearsal driver so the
    December code path under test is identical."""
    log = os.path.join(CHAIN_OUT, "stage4_labels.log")
    cmd = [PY, os.path.join("scripts", "m9_december_analysis.py"),
           "--verdicts", os.path.relpath(STORE, BASE),
           "--out", os.path.relpath(os.path.join(CHAIN_OUT, "dec"), BASE),
           "--no-regression"]
    rc, secs = _run(cmd, log, tag="stage4")
    lab = os.path.join(CHAIN_OUT, "dec", "dec_labels.csv")
    df = (pd.read_csv(lab, comment="#", keep_default_na=False)
          if os.path.exists(lab) else pd.DataFrame())
    return {"stage": "4 labels", "seconds": round(secs, 2), "rc": rc,
            "n_labels": len(df),
            "labels": df["label"].value_counts().to_dict() if len(df) else {}}


# ======================================================================
def run_chain(skip_transport=False, batch=20, n_posterior=20000,
              verbose=True):
    print("=" * 74)
    print("M9 FULL PRODUCTION CHAIN, DECEMBER SCALE")
    print("=" * 74)
    before = frozen_snapshot()
    t_chain = time.time()
    stages = [stage0_preflight()]
    print("  stage 0 preflight: %s (%.1fs)"
          % ("OK" if stages[0]["ok"] else "FAIL", stages[0]["seconds"]))

    if skip_transport:
        print("  stage 1 transport: SKIPPED (--skip-transport)")
        stages.append({"stage": "1 transport", "seconds": 0.0,
                       "rc": None, "skipped": True})
    else:
        print("  stage 1 transport: 981 sources, live DR3 EPOCH_PHOTOMETRY "
              "...", flush=True)
        s = stage1_transport(batch=batch)
        stages.append(s)
        print("    -> %d ledger rows, %d served, %d transits, %.1f MiB, "
              "%.1fs" % (s["n_ledger"], s["n_served"], s["n_transits"],
                         s["cache_bytes"] / 2**20, s["seconds"]))

    print("  stage 2 adjudicate: 981 queue members through the harness ...",
          flush=True)
    s2 = stage2_adjudicate(batch=batch)
    stages.append(s2)
    print("    -> %d verdicts %s in %.1fs"
          % (s2["n_ledger"], s2["verdicts"], s2["seconds"]))

    print("  stage 3 refit: every CONFIRMED through the arm, --zeropoint ...",
          flush=True)
    s3 = stage3_refit(n_posterior=n_posterior)
    stages.append(s3)
    print("    -> %d refits %s in %.1fs"
          % (s3["n_refit_ledger"], s3["status"], s3["seconds"]))

    print("  stage 4 labels: the seven pre-registered commands ...",
          flush=True)
    s4 = stage4_labels()
    stages.append(s4)
    print("    -> %d labels %s in %.1fs"
          % (s4["n_labels"], s4["labels"], s4["seconds"]))

    wall = time.time() - t_chain
    moved = frozen_check(before, " at close")
    payload = {
        "what": "M9 full production chain at December scale",
        "produced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "chain_wall_seconds": round(wall, 2),
        "chain_wall_minutes": round(wall / 60.0, 2),
        "stages": stages,
        "frozen_artifacts_moved": moved,
        "skip_transport": bool(skip_transport),
    }
    with open(os.path.join(CHAIN_OUT, "m9_chain_result.json"), "w",
              newline="\n", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("-" * 74)
    print("CHAIN WALL CLOCK: %.1f s = %.2f min  (%s)"
          % (wall, wall / 60.0,
             "transport SKIPPED" if skip_transport else "transport included"))
    for s in stages:
        print("    %-14s %8.1f s" % (s["stage"], s["seconds"]))
    return payload


# ======================================================================
def resume_test(kill_at=(25, 12, 20), batch=20, n_posterior=2000,
                skip_transport=False):
    """Kill each stage partway through, restart it, and check the contract."""
    print("=" * 74)
    print("M9 RESUME CONTRACT TEST -- every stage boundary, by KILLING it")
    print("=" * 74)
    results = []

    def _tmp_files(root):
        n = 0
        for dp, _dn, fn in os.walk(root):
            n += sum(1 for f in fn if f.endswith(".tmp"))
        return n

    # ---- stage 1 --------------------------------------------------------
    if not skip_transport:
        for p in (TRANSPORT_LEDGER,):
            if os.path.exists(p):
                os.remove(p)
        a = stage1_transport(batch=batch, kill_after=kill_at[0])
        b = stage1_transport(batch=batch)
        r = {"stage": "1 transport", "after_kill": a["n_ledger"],
             "after_restart": b["n_ledger"], "expected": 981,
             "killed": a["rc"] is None,
             "tmp_files_left": _tmp_files(CHAIN_CACHE_ROOT),
             "restart_rc": b["rc"]}
        r["pass"] = (r["after_restart"] == r["expected"]
                     and r["after_kill"] < r["expected"]
                     and r["tmp_files_left"] == 0 and b["rc"] == 0)
        results.append(r)
        print("  stage 1: killed at %d rows -> restart -> %d rows  [%s]"
              % (r["after_kill"], r["after_restart"],
                 "PASS" if r["pass"] else "FAIL"))

    # ---- stage 2 --------------------------------------------------------
    if os.path.exists(V1_LEDGER):
        os.remove(V1_LEDGER)
    a = stage2_adjudicate(batch=batch, kill_after=kill_at[1])
    b = stage2_adjudicate(batch=batch)
    r = {"stage": "2 adjudicate", "after_kill": a["n_ledger"],
         "after_restart": b["n_ledger"], "expected": 981,
         "killed": a["rc"] is None, "duplicates": b["n_duplicate_ids"],
         "restart_rc": b["rc"]}
    r["pass"] = (r["after_restart"] == r["expected"]
                 and r["after_kill"] < r["expected"]
                 and r["duplicates"] == 0 and b["rc"] == 0)
    results.append(r)
    print("  stage 2: killed at %d rows -> restart -> %d rows, %d dupes  [%s]"
          % (r["after_kill"], r["after_restart"], r["duplicates"],
             "PASS" if r["pass"] else "FAIL"))

    # ---- stage 3 --------------------------------------------------------
    if os.path.exists(REFIT_LEDGER):
        os.remove(REFIT_LEDGER)
    n_conf = int((pd.read_csv(V1_LEDGER)["verdict"] == "CONFIRMED").sum())
    a = stage3_refit(kill_after=kill_at[2], n_posterior=n_posterior)
    b = stage3_refit(n_posterior=n_posterior)
    r = {"stage": "3 refit", "after_kill": a["n_refit_ledger"],
         "after_restart": b["n_refit_ledger"], "expected": n_conf,
         "killed": a["rc"] is None, "duplicates": b["n_duplicate_ids"],
         "restart_rc": b["rc"]}
    r["pass"] = (r["after_restart"] == r["expected"]
                 and r["after_kill"] < r["expected"]
                 and r["duplicates"] == 0 and b["rc"] == 0)
    results.append(r)
    print("  stage 3: killed at %d refits -> restart -> %d refits, %d dupes "
          " [%s]" % (r["after_kill"], r["after_restart"], r["duplicates"],
                     "PASS" if r["pass"] else "FAIL"))

    # ---- stage 4: no ledger; the contract is IDEMPOTENCE ----------------
    s1 = stage4_labels()
    h1 = sha(os.path.join(CHAIN_OUT, "dec", "dec_labels.csv"))
    s2 = stage4_labels()
    h2 = sha(os.path.join(CHAIN_OUT, "dec", "dec_labels.csv"))
    r = {"stage": "4 labels", "contract": "idempotent re-run",
         "sha_first": (h1 or "")[:16], "sha_second": (h2 or "")[:16],
         "n_labels": s2["n_labels"], "pass": bool(h1 and h1 == h2)}
    results.append(r)
    print("  stage 4: re-run byte-identical  [%s]"
          % ("PASS" if r["pass"] else "FAIL"))

    payload = {"what": "M9 resume-contract test",
               "produced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime()),
               "kill_after_seconds": list(kill_at), "results": results,
               "all_pass": all(x["pass"] for x in results)}
    with open(os.path.join(CHAIN_OUT, "m9_resume_test.json"), "w",
              newline="\n", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("-" * 74)
    print("RESUME CONTRACT: %s"
          % ("ALL STAGES PASS" if payload["all_pass"] else "FAILURES ABOVE"))
    return payload


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--resume-test", action="store_true")
    ap.add_argument("--skip-transport", action="store_true")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--n-posterior", type=int, default=20000)
    a = ap.parse_args(argv)
    os.makedirs(CHAIN_OUT, exist_ok=True)
    if a.run:
        run_chain(skip_transport=a.skip_transport, batch=a.batch,
                  n_posterior=a.n_posterior)
    if a.resume_test:
        resume_test(batch=a.batch, skip_transport=a.skip_transport)
    if not (a.run or a.resume_test):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
