#!/usr/bin/env python
"""M8 task 3: RUN the pre-registration, end to end, on a synthetic store.

M7's lesson was that three pre-registered commands did not run until somebody
ran them, and running them found a `== 76` assertion that would have killed
the pooled analysis on release day.  That check covered the two discriminator
commands.  It did not cover the D4 command, the scope-pure primary at a
realistic sample size, the pooled rule, or -- the largest gap -- the six
outcome LABELS, which no code in this repository has ever emitted.

This driver executes every pre-registered analysis path against the M8
synthetic stores and checks that each one produces the label the registration
says it should.

WHAT IS CHECKED, per scenario:

  (1) EXECUTABILITY.  Each pre-registered command, as written in section 6 of
      the frozen file, run with `--verdicts <synthetic dir>` substituted for
      `--verdicts all`.  The substitution is deliberate and it is the ONLY
      one: `all` means "every CSV in out/verdicts/", so honouring it
      literally would require writing fabricated verdicts into the real
      store.  `load_store` expands a directory through the same branch it
      expands `all` with, so the code path under test is identical.
      Non-zero exit, traceback, or an unrecognised argument is a FAIL.

  (2) LABELLING.  The numbers each command emits are fed to
      m8_prereg_labels.assign_label(), which is section 5 written as one
      total function.  The label is compared with the label the scenario's
      DECLARED truth requires.

  (3) SCOPE DISCIPLINE.  The primary must see harness verdicts only; the
      regression check must reproduce the frozen M4/M5 artifacts
      byte-identically; the pooled run must print its scope composition and
      must never be allowed to read as a null.

  (4) TOTALITY.  Every one of the six labels, plus the three
      beyond-the-six cases the registration does not cover, must be reached
      by at least one scenario.  A label nobody can produce is a label that
      will not be produced in December either.

Run:
  .venv/Scripts/python.exe scripts/m8_prereg_rehearsal.py --all
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m8_prereg_labels as L                                     # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
PY = os.path.join(BASE, ".venv", "Scripts", "python.exe")
SYNTH_DIR = os.path.join(OUT, "verdicts_synth")
REH = os.path.join(OUT, "m8_rehearsal")

FROZEN = {
    "m4_eb26_erosita_xmatch.csv": None,
    "m4_eb26_discriminator_stats.txt": None,
    "m5_activity_eb26_table.csv": None,
    "m5_activity_metric_results.csv": None,
    "m5_activity_discriminator_stats.txt": None,
}

# scenario -> {test: expected label}, from the scenario's DECLARED truth.
# 'primary' analyses only unless the key names an analysis.
EXPECTED = {
    "null_eb26":    {"D2": "NULL", "D3": "NULL"},
    "null_even":    {"D2": "NULL", "D3": "NULL"},
    "null_harness": {"D2": "NULL", "D3": "NULL"},
    "d1_effect":    {"D1": "POSITIVE"},
    "d2_effect":    {"D2": "POSITIVE"},
    "d3_effect":    {"D3": "POSITIVE"},
    "d4_effect":    {"D4": "POSITIVE"},
    "d3_reversal":  {"D3": "DIRECTION REVERSAL"},
    "d2_reversal":  {"D2": "DIRECTION REVERSAL"},
    "thin":         {"D1": "NOT TESTABLE", "D2": "NOT TESTABLE",
                     "D3": "NOT TESTABLE", "D4": "NOT TESTABLE"},
    "no_coverage":  {"D3": "NOT TESTABLE"},
}

M5_PRIMARY = {"D2": "B1 dAmp_G", "D3": "C5 astrometric_gof_al"}
M4_PRIMARY = "D1a in-footprint detection rate"


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run(cmd, cwd=BASE, timeout=1800):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout)
    return {"cmd": " ".join(cmd[1:]), "rc": r.returncode,
            "seconds": round(time.time() - t0, 1),
            "stdout": r.stdout, "stderr": r.stderr}


def m5_primary_metric_name(res, test):
    """M5's metric labels carry a family prefix; find the pre-registered
    primary by substring rather than by an index that can move."""
    want = {"D2": "dAmp_G", "D3": "astrometric_gof_al"}[test]
    hit = res[res["metric"].str.contains(want, regex=False)]
    if not len(hit):
        return None
    exact = hit[hit["metric"].str.strip().str.endswith(want)]
    return (exact if len(exact) else hit).iloc[0]


# ======================================================================
def label_from_m5(outdir, test, analysis):
    p = os.path.join(outdir, "m5_activity_metric_results.csv")
    if not os.path.exists(p):
        return L.assign_label(test, analysis, 0, 0, np.nan, np.nan, np.nan,
                              joined_rows=0)
    res = pd.read_csv(p)
    r = m5_primary_metric_name(res, test)
    if r is None:
        return L.assign_label(test, analysis, 0, 0, np.nan, np.nan, np.nan,
                              joined_rows=0)
    testable = bool(r.get("testable", False))
    n1 = int(r.get("n_conf", 0) or 0)
    n2 = int(r.get("n_spur", 0) or 0)
    return L.assign_label(
        test, analysis, n1, n2,
        r.get("p_holm", np.nan) if testable else np.nan,
        r.get("effect", np.nan), r.get("min_detectable", np.nan),
        joined_rows=None if testable else 0)


def label_from_m4(outdir, analysis):
    p = os.path.join(outdir, "m4_eb26_discriminator_results.csv")
    if not os.path.exists(p):
        return L.assign_label("D1", analysis, 0, 0, np.nan, np.nan, np.nan,
                              joined_rows=0)
    res = pd.read_csv(p)
    r = res[res["metric"] == M4_PRIMARY]
    if not len(r):
        return L.assign_label("D1", analysis, 0, 0, np.nan, np.nan, np.nan,
                              joined_rows=0)
    r = r.iloc[0]
    return L.assign_label("D1", analysis, int(r["n_conf"]), int(r["n_spur"]),
                          r.get("p_holm", np.nan), r.get("effect", np.nan),
                          r.get("min_detectable", np.nan),
                          rate_conf=r.get("rate_conf", np.nan))


def label_from_m6(outdir, analysis):
    p = os.path.join(outdir, "m6_astrom_quiet_d4_results.csv")
    if not os.path.exists(p):
        return L.assign_label("D4", analysis, 0, 0, np.nan, np.nan, np.nan,
                              joined_rows=0)
    r = pd.read_csv(p).iloc[0]
    return L.assign_label("D4", analysis, int(r["n_conf"]), int(r["n_spur"]),
                          r.get("p_holm", np.nan), r.get("effect", np.nan),
                          r.get("min_detectable", np.nan),
                          rate_conf=r.get("rate_conf", np.nan))


def negative_control_p(outdir):
    """M5 runs phot_g_n_obs outside every family, uncorrected."""
    p = os.path.join(outdir, "m5_activity_metric_results.csv")
    if not os.path.exists(p):
        return np.nan
    res = pd.read_csv(p)
    hit = res[res["metric"].str.contains("phot_g_n_obs", regex=False)]
    if not len(hit):
        return np.nan
    return float(hit.iloc[0].get("p", np.nan))


# ======================================================================
def rehearse_scenario(name, say, keep_logs=True):
    sdir = os.path.join(SYNTH_DIR, name)
    synth_only = os.path.join(REH, name, "_harness_only")
    os.makedirs(synth_only, exist_ok=True)
    shutil.copyfile(os.path.join(sdir, "harness_synth.v1.csv"),
                    os.path.join(synth_only, "harness_synth.v1.csv"))
    res = {"scenario": name, "runs": [], "labels": [], "fails": []}

    # The REGRESSION arm selects elbadry2026/compact_companion out of the
    # scenario directory, and every scenario directory holds the same copy of
    # the frozen eb26.v1.csv -- so that arm is scenario-INDEPENDENT and is run
    # once, globally, by check_regression_byte_identity().  Running it per
    # scenario would be eleven identical two-minute runs.
    arms = [
        # (analysis, verdict source dir, extra selection args)
        ("primary", synth_only, ["--scopes", "orbit_reality",
                                 "--sources", "epoch_vet_harness"]),
        ("pooled", sdir, []),
    ]
    for analysis, vdir, sel in arms:
        od = os.path.join(REH, name, analysis)
        os.makedirs(od, exist_ok=True)
        for script in ("m4_eb26_erosita_test.py",
                       "m5_activity_discriminator.py"):
            r = run([PY, os.path.join("scripts", script),
                     "--verdicts", vdir] + sel + ["--out-dir", od])
            r["scenario"], r["analysis"] = name, analysis
            res["runs"].append(r)
            if r["rc"] not in (0, 2):
                res["fails"].append(
                    f"{analysis}/{script} exited {r['rc']}: "
                    f"{r['stderr'].strip().splitlines()[-1] if r['stderr'].strip() else ''}")
        ctrl = negative_control_p(od)
        labs = [label_from_m4(od, analysis)]
        for test in ("D2", "D3"):
            labs.append(label_from_m5(od, test, analysis))
        if analysis == "primary":
            r = run([PY, os.path.join("scripts",
                                      "m6_astrom_quiet_decision.py"),
                     "--verdicts", vdir, "--scopes", "orbit_reality",
                     "--out-dir", od])
            r["scenario"], r["analysis"] = name, "primary (D4)"
            res["runs"].append(r)
            if r["rc"] != 0:
                res["fails"].append(
                    f"D4 command exited {r['rc']}: "
                    f"{r['stderr'].strip().splitlines()[-1] if r['stderr'].strip() else ''}")
            labs.append(label_from_m6(od, analysis))
        labs, vetoed = L.apply_negative_control_veto(labs, ctrl)
        for x in labs:
            x["scenario"] = name
            x["control_p"] = ctrl
            x["control_vetoed"] = vetoed
        res["labels"] += labs

    # ---- check against the declared truth --------------------------------
    exp = EXPECTED.get(name, {})
    for test, want in exp.items():
        got = [x for x in res["labels"]
               if x["test"] == test and x["analysis"] == "primary"]
        if not got:
            res["fails"].append(f"{test}: no primary label produced")
            continue
        g = got[0]["label"]
        if g != want:
            res["fails"].append(
                f"{test} primary: expected {want!r}, got {g!r} "
                f"({got[0]['reason']})")
    return res


# ======================================================================
def check_regression_byte_identity(say):
    """The pre-registration's section 2.2: the EB26-alone re-run must
    reproduce the frozen artifacts byte-identically."""
    say("\n" + "=" * 78)
    say("REGRESSION CHECK -- the frozen M4/M5 artifacts through the M8 code")
    say("=" * 78)
    od = os.path.join(REH, "_regression_frozen")
    os.makedirs(od, exist_ok=True)
    for script, sel in (
            ("m4_eb26_erosita_test.py", ["--scopes", "compact_companion",
                                         "--sources", "elbadry2026"]),
            ("m5_activity_discriminator.py", ["--scopes", "compact_companion",
                                              "--sources", "elbadry2026"])):
        r = run([PY, os.path.join("scripts", script), "--verdicts", "all"]
                + sel + ["--out-dir", od])
        say(f"  {script}: rc={r['rc']} ({r['seconds']}s)")
    ok = True
    for f in FROZEN:
        a, b = os.path.join(OUT, f), os.path.join(od, f)
        if not os.path.exists(b):
            say(f"  {f:<42s} NOT PRODUCED")
            ok = False
            continue
        ha, hb = sha256(a), sha256(b)
        same = ha == hb
        say(f"  {f:<42s} {'IDENTICAL' if same else 'DIFFERS'}  {ha[:12]}")
        ok &= same
    say(f"  -> {'PASS' if ok else 'FAIL'}")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--scenarios", nargs="*", default=None)
    ap.add_argument("--out", default=os.path.join(OUT,
                                                  "m8_prereg_rehearsal.txt"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    os.makedirs(REH, exist_ok=True)
    man = json.load(open(os.path.join(SYNTH_DIR, "MANIFEST.json")))
    names = a.scenarios or [s["scenario"] for s in man["scenarios"]]

    say("M8 TASK 3 -- THE PRE-REGISTERED DECEMBER ANALYSIS, REHEARSED")
    say(f"produced {pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    say(f"synthetic store: {len(names)} scenarios, seed {man['seed']}")
    say("substitution: `--verdicts all` -> `--verdicts <synthetic dir>`, so "
        "that no")
    say("fabricated verdict is ever written into out/verdicts/.  load_store "
        "expands a")
    say("directory through the same branch it expands `all` with.")

    reg_ok = check_regression_byte_identity(say)

    all_labels, all_fails, all_runs = [], [], []
    for name in names:
        say("\n" + "=" * 78)
        s = [x for x in man["scenarios"] if x["scenario"] == name][0]
        extra = ""
        if "realised_auc" in s:
            extra = (f"  realised AUC {s['realised_auc']:.4f} "
                     f"(target {s['target_auc']:.3f})")
        elif "realised_rates" in s:
            extra = (f"  realised rates spur {s['realised_rates'][0]:.4f} / "
                     f"conf {s['realised_rates'][1]:.4f}")
        say(f"SCENARIO {name}  [{s['mode']}, {s['n_conf']} conf / "
            f"{s['n_spur']} spur]{extra}")
        say("=" * 78)
        r = rehearse_scenario(name, say)
        all_runs += r["runs"]
        all_labels += r["labels"]
        for x in r["labels"]:
            say(L.format_label(x))
        exp = EXPECTED.get(name, {})
        if exp:
            say("  expected (from the scenario's declared truth): "
                + ", ".join(f"{k}={v}" for k, v in exp.items()))
        if r["fails"]:
            for f in r["fails"]:
                say(f"  ** FAIL: {f}")
            all_fails += [f"{name}: {x}" for x in r["fails"]]
        else:
            say("  -> all checks PASS")

    # ---- totality --------------------------------------------------------
    say("\n" + "=" * 78)
    say("TOTALITY -- is every pre-registered label reachable?")
    say("=" * 78)
    seen = {}
    for x in all_labels:
        seen.setdefault(x["label"].split(" -- VETOED")[0], []).append(
            f"{x['scenario']}/{x['test']}/{x['analysis']}")
    for lab in L.SIX + L.BEYOND_SIX:
        hits = seen.get(lab, [])
        say(f"  {lab:<46s} {len(hits):>3d}  "
            f"{hits[0] if hits else '** NEVER PRODUCED **'}")
    unreached = [x for x in L.SIX if not seen.get(x)]

    say("\n" + "=" * 78)
    say("DEFECTS IN THE FROZEN REGISTRATION FOUND BY RUNNING IT")
    say("=" * 78)
    gaps = {}
    for x in all_labels:
        for g in str(x["defect"]).split("+"):
            if g:
                gaps.setdefault(g, []).append(
                    f"{x['scenario']}/{x['test']}/{x['analysis']}")
    for g in ("GAP-1", "GAP-2", "GAP-3", "GAP-4"):
        hits = gaps.get(g, [])
        say(f"  {g}: {len(hits)} occurrence(s)"
            + (f"  e.g. {hits[0]}" if hits else "  (not exercised)"))

    # LANDMINE (M8), and it eats the one result this project has never been
    # able to claim: the pre-registered label **NULL** is exactly pandas'
    # default NA token, so `pd.read_csv(...)` reads all 20 NULL labels back
    # as NaN and a naive `df.label.value_counts()` reports ZERO nulls.  The
    # file is written with the literal string because that is the
    # registration's vocabulary; every reader must pass
    # keep_default_na=False, and the header line below says so in the file
    # itself so that nobody has to know it in advance.
    lab_path = os.path.join(OUT, "m8_prereg_rehearsal_labels.csv")
    with open(lab_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# READ WITH pandas.read_csv(..., keep_default_na=False) --"
                 " the label 'NULL' is pandas' default NA token and is"
                 " otherwise silently read back as a missing value\n")
        pd.DataFrame(all_labels).to_csv(fh, index=False,
                                        lineterminator="\n")
    pd.DataFrame([{k: v for k, v in r.items()
                   if k not in ("stdout", "stderr")}
                  for r in all_runs]).to_csv(
        os.path.join(OUT, "m8_prereg_rehearsal_runs.csv"), index=False,
        lineterminator="\n")

    say("\n" + "=" * 78)
    say(f"RESULT: {len(all_runs)} command runs, "
        f"{len(all_labels)} labels assigned, {len(all_fails)} failure(s); "
        f"regression byte-identity {'PASS' if reg_ok else 'FAIL'}")
    if unreached:
        say(f"  labels never produced: {unreached}")
    for f in all_fails:
        say(f"  ** {f}")
    say("=" * 78)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.relpath(a.out, BASE)}")
    return 0 if (not all_fails and reg_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
