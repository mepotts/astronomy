#!/usr/bin/env python
"""M9: DECEMBER'S SECTION 3.3, AS ONE COMMAND.

The pre-registration (sec.6) and the runbook (sec.3.3) prescribe seven
commands and then a label per test.  M8 made the labelling mechanical
(`m8_prereg_labels.py` is sec.5 + sec.2.2 as one total function) but left
the driving to a human: on release day somebody has to type seven commands
in the right order with the right flags into the right three output
directories, read four results CSVs, call the label function eight times,
and remember the negative-control veto.  At 3 a.m. that is a defect
waiting to happen, and it is the last piece of "release day needs no new
code and no new decisions" that was missing.

This runs all of it, in the frozen order, with the frozen flags:

  PRIMARY     scope-pure, harness verdicts only        -> out/dec/primary
  REGRESSION  EB26 alone; MUST reproduce the frozen
              M4/M5 artifacts byte-identically         -> out/dec/regression
  SECONDARY   pooled; POSITIVE only may be interpreted -> out/dec/pooled

then assigns the pre-registered label to D1-D4 in each of the two
interpretable arms, applies the negative-control veto (sec.3), and writes:

  <out>/dec_labels.csv     one row per (test, analysis), with the defect
                           code where the frozen registration determines no
                           label (M8 GAP-1..GAP-4).  Header line says
                           `keep_default_na=False` because the label NULL is
                           pandas' default NA token (M8 landmine #14).
  <out>/dec_runs.csv       every subprocess, its rc and its wall clock
  <out>/dec_analysis.txt   the transcript

WHAT IT DOES NOT DO.  It does not choose between GAP-4's two readings, it
does not soften a label, and it does not decide anything the registration
left to Matthew.  Where the rules do not determine an answer it prints both
readings and the defect code, exactly as M8 specified.

  .venv\\Scripts\\python.exe scripts\\m9_december_analysis.py --verdicts all
  .venv\\Scripts\\python.exe scripts\\m9_december_analysis.py --verdicts out\\verdicts_dec_rehearsal --out out\\m9_chain\\dec --no-regression
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m8_prereg_labels as L                                     # noqa: E402
import m8_prereg_rehearsal as R                                  # noqa: E402

PY = os.path.join(BASE, ".venv", "Scripts", "python.exe")
OUT = os.path.join(BASE, "out")

# The seven commands, frozen.  (script, arm, extra selection args).
# Copied from PREREG-2026-08-23 sec.6 -- if these ever disagree with the
# pre-registration, the pre-registration wins.
ARMS = [
    ("primary", ["--scopes", "orbit_reality",
                 "--sources", "epoch_vet_harness"]),
    ("regression", ["--scopes", "compact_companion",
                    "--sources", "elbadry2026"]),
    ("pooled", []),
]


def run_arms(verdicts, outdir, say, arms=None, timeout=3600):
    runs = []
    for arm, sel in (arms or ARMS):
        od = os.path.join(outdir, arm)
        os.makedirs(od, exist_ok=True)
        for script in ("m4_eb26_erosita_test.py",
                       "m5_activity_discriminator.py"):
            r = R.run([PY, os.path.join("scripts", script),
                       "--verdicts", verdicts] + sel + ["--out-dir", od],
                      timeout=timeout)
            r["arm"], r["script"] = arm, script
            runs.append(r)
            say("  %-10s %-32s rc=%s  %.1fs" % (arm, script, r["rc"],
                                                r["seconds"]))
            if r["rc"] not in (0, 2):
                say("    !! %s" % (r["stderr"].strip().splitlines()[-1]
                                   if r["stderr"].strip() else "no stderr"))
        # D4 runs only in the scope-pure primary: it is a decision about a
        # config entry, its own Holm family of one (prereg sec.3, D4).
        if arm == "primary":
            r = R.run([PY, os.path.join("scripts",
                                        "m6_astrom_quiet_decision.py"),
                       "--verdicts", verdicts, "--scopes", "orbit_reality",
                       "--out-dir", od], timeout=timeout)
            r["arm"], r["script"] = arm, "m6_astrom_quiet_decision.py"
            runs.append(r)
            say("  %-10s %-32s rc=%s  %.1fs"
                % (arm, "m6_astrom_quiet_decision.py", r["rc"],
                   r["seconds"]))
            if r["rc"] != 0:
                say("    !! %s" % (r["stderr"].strip().splitlines()[-1]
                                   if r["stderr"].strip() else "no stderr"))
    return runs


def label_arm(outdir, analysis, with_d4):
    od = os.path.join(outdir, analysis)
    ctrl = R.negative_control_p(od)
    labs = [R.label_from_m4(od, analysis)]
    for test in ("D2", "D3"):
        labs.append(R.label_from_m5(od, test, analysis))
    if with_d4:
        labs.append(R.label_from_m6(od, analysis))
    labs, vetoed = L.apply_negative_control_veto(labs, ctrl)
    for x in labs:
        x["analysis"] = analysis
        x["control_p"] = ctrl
        x["control_vetoed"] = vetoed
    return labs, ctrl, vetoed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verdicts", default="all",
                    help="'all' (= every producer in out/verdicts/), a "
                         "directory, or a glob -- load_store() expands all "
                         "three")
    ap.add_argument("--out", default=os.path.join(OUT, "dec"))
    ap.add_argument("--no-regression", action="store_true",
                    help="skip the EB26 byte-identity arm (used when the "
                         "store under test is a rehearsal store)")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)

    outdir = a.out if os.path.isabs(a.out) else os.path.join(BASE, a.out)
    os.makedirs(outdir, exist_ok=True)
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    t0 = time.time()
    say("=" * 78)
    say("DECEMBER SECTION 3.3 -- the pre-registered analysis, as one command")
    say("  verdicts   : %s" % a.verdicts)
    say("  out        : %s" % os.path.relpath(outdir, BASE))
    say("  prereg     : PREREG-2026-08-23-december-discriminators.md (FROZEN)")
    say("=" * 78)

    arms = [x for x in ARMS
            if not (a.no_regression and x[0] == "regression")]
    runs = run_arms(a.verdicts, outdir, say, arms=arms, timeout=a.timeout)

    say("\n" + "-" * 78)
    say("REGRESSION CHECK (prereg sec.2.2): the frozen M4/M5 artifacts")
    reg_ok = None
    if a.no_regression:
        say("  SKIPPED (--no-regression)")
    else:
        od = os.path.join(outdir, "regression")
        reg_ok = True
        for f in R.FROZEN:
            b = os.path.join(od, f)
            if not os.path.exists(b):
                say("  %-42s NOT PRODUCED" % f)
                reg_ok = False
                continue
            ha, hb = R.sha256(os.path.join(OUT, f)), R.sha256(b)
            say("  %-42s %s  %s" % (f, "IDENTICAL" if ha == hb else "DIFFERS",
                                    ha[:12]))
            reg_ok &= ha == hb
        say("  -> %s" % ("PASS" if reg_ok else
                         "FAIL -- this is a BUG REPORT about the pipeline, "
                         "never a scientific update"))

    say("\n" + "-" * 78)
    say("LABELS (prereg sec.5 + sec.2.2, via m8_prereg_labels.py)")
    labels = []
    for arm, _sel in arms:
        if arm == "regression":
            continue
        labs, ctrl, vetoed = label_arm(outdir, arm, with_d4=(arm == "primary"))
        labels += labs
        say("\n  %s  (negative control phot_g_n_obs p = %s%s)"
            % (arm.upper(), "n/a" if not np.isfinite(ctrl) else "%.4g" % ctrl,
               "  *** VETO ACTIVE ***" if vetoed else ""))
        for x in labs:
            say("    %s" % L.format_label(x))

    df = pd.DataFrame(labels)
    lp = os.path.join(outdir, "dec_labels.csv")
    with open(lp, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("# READ WITH keep_default_na=False -- the pre-registered "
                 "label NULL is pandas' default NA token (M8 landmine 14)\n")
        df.to_csv(fh, index=False, lineterminator="\n")
    pd.DataFrame(runs).drop(columns=["stdout", "stderr"],
                            errors="ignore").to_csv(
        os.path.join(outdir, "dec_runs.csv"), index=False,
        lineterminator="\n")

    say("\n" + "-" * 78)
    say("SUMMARY")
    if len(df):
        for k, v in df["label"].value_counts().items():
            say("  %-46s %d" % (k, v))
    n_defect = int(df["defect"].notna().sum()) if "defect" in df else 0
    say("  labels with a registration defect code: %d" % n_defect)
    if n_defect:
        say("  -> a defect code is NOT a licence to choose: report the "
            "emitted label, the code, and which reading was used.")
    say("  wall clock %.1f s over %d subprocess runs, %d non-zero exits"
        % (time.time() - t0, len(runs),
           sum(1 for r in runs if r["rc"] not in (0, 2))))
    say("  wrote %s" % os.path.relpath(lp, BASE))

    with open(os.path.join(outdir, "dec_analysis.txt"), "w", newline="\n",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(outdir, "dec_summary.json"), "w", newline="\n",
              encoding="utf-8") as fh:
        json.dump({"verdicts": a.verdicts,
                   "produced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime()),
                   "seconds": round(time.time() - t0, 2),
                   "n_runs": len(runs),
                   "n_nonzero_exits": sum(1 for r in runs
                                          if r["rc"] not in (0, 2)),
                   "regression_pass": reg_ok,
                   "labels": (df["label"].value_counts().to_dict()
                              if len(df) else {}),
                   "n_defect_codes": n_defect}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
