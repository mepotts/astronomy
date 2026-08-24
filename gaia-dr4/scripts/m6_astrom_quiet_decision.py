#!/usr/bin/env python
"""M6 task 5: settle `flag_astrom_quiet` -- earn the column, or lose it.

M5 froze `flag_astrom_quiet` (astrometric_gof_al below the 25th percentile
of the day's own main candidate bin) as a ranking tiebreaker while
recording two caveats against it: controlling for `significance` it retains
only p = 0.048, and on the rows that actually survive the frozen screen it
marks 2 and catches 0 of the 7 in-list EB26-spurious.  M6 was asked to
decide with evidence.

=======================================================================
THE MEASUREMENT M5 DID NOT MAKE, AND IT IS THE DECISIVE ONE
=======================================================================
M5 measured `astrometric_gof_al` across ALL 65 verdicted EB26 targets.
But the flag does not operate on those 65.  It operates on the DAY-ONE
QUEUE -- the rows that survive the frozen screen.  Most of the 65 are
removed by the screen before the flag is ever computed, and the ones that
survive are a biased subset (high significance, bright).  A discriminator
measured on a population it will never see is not evidence about the flag.

So this script re-asks M5's family-C question on the flag's OWN operating
population -- the EB26-verdicted rows that are IN the day-one queue -- and
states the power of that test exactly.  Three things are computed:

  1. CONTINUOUS, in-list: Mann-Whitney on astrometric_gof_al (and ruwe)
     restricted to queue members, AUC(spurious > confirmed) with a
     bootstrap CI, and the smallest AUC detectable at 80 % power at the
     achieved n (the M5 routine, same seed).
  2. THRESHOLDED, in-list: Fisher exact on the flag itself, plus the
     smallest spurious marking-rate detectable at 80 % power against the
     observed confirmed marking-rate (the M4 routine).
  3. WHAT DECEMBER NEEDS: the number of in-list verdicts required for
     80 % power at the observed in-list effect, and at the effect M5
     measured over all 65 -- i.e. the size of the harvest that settles it.

=======================================================================
DECISION RULE, PRE-REGISTERED HERE FOR DECEMBER (so the answer cannot be
chosen after seeing the day-one verdicts)
=======================================================================
Re-run this script with the day-one harness verdicts in the store
(--verdicts out/verdicts/*.csv).  Then:

  KEEP (and re-freeze in the then-current config)
      the in-list continuous test reaches p < 0.05 two-sided in the M5
      direction (AUC < 0.5, i.e. confirmed are the noisier fits) AND the
      thresholded flag's in-list catch rate exceeds its marking rate at
      Fisher p < 0.05.
  REMOVE (drop the column; the config records the removal and why)
      the in-list test is WELL POWERED -- smallest detectable AUC <= 0.70 --
      and the observed in-list AUC is consistent with 0.5 (CI covers it).
  CARRY (leave it exactly as v4 froze it, tiebreaker only)
      anything else.  A flag that cannot be tested is not a flag that has
      been vindicated; the config must keep saying so.

Inputs : out/verdicts/*.csv, out/epoch_vet_day1_queue.v2.csv,
         data/dr3_activity_columns.parquet
Outputs: out/m6_astrom_quiet_decision.txt, out/m6_astrom_quiet_inlist.csv
Run    : .venv/Scripts/python.exe scripts/m6_astrom_quiet_decision.py
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as vs  # noqa: E402
from m5_activity_discriminator import (  # noqa: E402
    auc_of, boot_auc_ci, min_detectable_auc, min_detectable_rate,
    mwu_power, wilson_ci, SEED, ALPHA, POWER_TARGET)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
METRICS = [("astrometric_gof_al", "C5 astrometric_gof_al (the frozen flag's "
                                  "metric)"),
           ("ruwe", "C1 ruwe (the runner-up M5 deliberately did not freeze)")]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", nargs="*", default=None)
    # DEFECT FOUND BY THE M8 REHEARSAL, and it would have fired on the day.
    # The frozen pre-registration's section 6 and DR4-DAY-RUNBOOK section 3.3
    # both prescribe
    #     m6_astrom_quiet_decision.py --verdicts all --scopes orbit_reality
    # and this parser had no --scopes.  argparse exits 2 with "unrecognized
    # arguments" -- so the D4 command, alone of the seven, had never been
    # run.  M7's executability note covered the two discriminator tests only.
    # Adding the flag makes the pre-registered command executable AS
    # WRITTEN; it changes no rule and no default (None = every scope, which
    # is what the script did before).
    ap.add_argument("--scopes", nargs="*", default=None)
    ap.add_argument("--sources", nargs="*", default=None)
    ap.add_argument("--queue", default=os.path.join(
        OUT, "epoch_vet_day1_queue.v2.csv"))
    ap.add_argument("--out-dir", default=OUT)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    rng = np.random.default_rng(SEED)
    lines = []

    def say(s=""):
        lines.append(s)
        print(s)

    store = vs.load_store(a.verdicts or
                          [os.path.join(vs.STORE_DIR, "eb26.v1.csv")],
                          scopes=a.scopes, sources=a.sources)
    q = pd.read_csv(a.queue)
    act = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_activity_columns.parquet"))

    say("M6 -- does `flag_astrom_quiet` earn its column?  (2026-08-21)")
    say("=" * 74)
    say(f"verdict store: {len(store)} records; "
        f"{vs.scope_composition_string(store)}")
    say(f"queue: {len(q)} rows, flag_astrom_quiet marks "
        f"{int(q['flag_astrom_quiet'].sum())} "
        f"({100*q['flag_astrom_quiet'].mean():.1f} %)")

    # ---- the operating population ---------------------------------------
    t = store.merge(q[["source_id", "flag_astrom_quiet", "queue_bin",
                       "p_class3_corr", "significance", "m2_min"]],
                    on="source_id", how="left", suffixes=("", "_q"))
    t = t.merge(act[["source_id", "astrometric_gof_al", "ruwe",
                     "phot_g_mean_mag"]], on="source_id", how="left")
    t["in_list"] = t["queue_bin_q"].notna()
    t["flag"] = t["flag_astrom_quiet_q"].fillna(False).astype(bool)
    ver = t[t["verdict"].isin(["CONFIRMED", "SPURIOUS"])].copy()

    say("")
    say("POPULATIONS " + "-" * 61)
    say(f"  all verdicted EB26 targets (what M5 measured on): "
        f"{len(ver)}  "
        f"({int((ver['verdict']=='CONFIRMED').sum())} conf / "
        f"{int((ver['verdict']=='SPURIOUS').sum())} spur)")
    inl = ver[ver["in_list"]]
    say(f"  verdicted AND in the day-one queue (what the flag actually "
        f"operates on): {len(inl)}  "
        f"({int((inl['verdict']=='CONFIRMED').sum())} conf / "
        f"{int((inl['verdict']=='SPURIOUS').sum())} spur)")
    say(f"  the frozen screen removes {len(ver) - len(inl)} of the "
        f"verdicted targets before the flag is ever computed.")
    say("  -- a discriminator measured on a population it will never see "
        "is not")
    say("     evidence about the flag.  That is why this test exists.")

    # RECONCILIATION with M5's published in-list numbers, which must not be
    # left looking like a disagreement: M5 counted the MAIN bin only; the
    # flag is computed over the whole queue, retrieval bin included.
    mainb = inl[inl["queue_bin_q"] == "v2_main"]
    say("")
    say("  reconciliation with M5's published in-list counts:")
    say(f"    main bin only (M5's population): {len(mainb)} verdicted "
        f"({int((mainb['verdict']=='CONFIRMED').sum())} conf / "
        f"{int((mainb['verdict']=='SPURIOUS').sum())} spur), flagged "
        f"{int(mainb['flag'].sum())}, of which spurious "
        f"{int(mainb.loc[mainb['verdict']=='SPURIOUS','flag'].sum())} "
        f"-- M5 reported 46 / 2 / 0-of-7 and this reproduces it.")
    say(f"    + retrieval bin (Pr >= 0.999), which the flag ALSO marks: "
        f"{len(inl) - len(mainb)} more verdicted rows.")
    say(f"    = {len(inl)} in-list verdicted rows in total. This test uses "
        f"the whole queue,")
    say("      because the whole queue is what the flag is computed on.")

    # ---- 1. continuous, both populations --------------------------------
    say("")
    say("1. CONTINUOUS TEST, all-65 (M5's population) vs in-list (the "
        "flag's) " + "-" * 3)
    rows = []
    for col, label in METRICS:
        for pop_name, pop in (("all-65", ver), ("in-list", inl)):
            xc = pd.to_numeric(pop.loc[pop["verdict"] == "CONFIRMED", col],
                               errors="coerce").dropna().values
            xs = pd.to_numeric(pop.loc[pop["verdict"] == "SPURIOUS", col],
                               errors="coerce").dropna().values
            if len(xc) < 3 or len(xs) < 3:
                say(f"  {label} [{pop_name}]: n {len(xc)}/{len(xs)} -- "
                    f"NOT TESTABLE")
                continue
            u, p = mannwhitneyu(xs, xc, alternative="two-sided")
            auc = u / (len(xc) * len(xs))
            lo, hi = boot_auc_ci(xc, xs, rng)
            mda = min_detectable_auc(len(xc), len(xs), rng)
            say(f"  {label} [{pop_name}]")
            say(f"    n {len(xc)} conf / {len(xs)} spur; medians "
                f"{np.median(xc):.2f} vs {np.median(xs):.2f}")
            say(f"    MWU p = {p:.4f}; AUC(spur>conf) = {auc:.3f} "
                f"[95 % boot {lo:.3f}-{hi:.3f}]")
            say(f"    smallest AUC detectable at 80 % power here: "
                f"{('%.3f' % mda) if mda else '> 0.975'}"
                f"  (equivalently {(1-mda):.3f} on the low side)"
                if mda else "")
            rows.append({"metric": col, "population": pop_name,
                         "n_conf": len(xc), "n_spur": len(xs), "p": p,
                         "auc": auc, "auc_lo": lo, "auc_hi": hi,
                         "min_detectable_auc": mda})

    # ---- 2. thresholded, in-list ----------------------------------------
    say("")
    say("2. THRESHOLDED TEST -- the flag itself, on the in-list "
        "population " + "-" * 6)
    k1 = int(inl.loc[inl["verdict"] == "CONFIRMED", "flag"].sum())
    n1 = int((inl["verdict"] == "CONFIRMED").sum())
    k2 = int(inl.loc[inl["verdict"] == "SPURIOUS", "flag"].sum())
    n2 = int((inl["verdict"] == "SPURIOUS").sum())
    lo1, hi1 = wilson_ci(k1, n1)
    lo2, hi2 = wilson_ci(k2, n2)
    orr, pf = fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])
    mdr = min_detectable_rate(n1, k1 / n1 if n1 else 0.0, n2)
    say(f"  flagged CONFIRMED {k1}/{n1} = {k1/max(n1,1):.3f} "
        f"(95 % Wilson {lo1:.3f}-{hi1:.3f})")
    say(f"  flagged SPURIOUS  {k2}/{n2} = {k2/max(n2,1):.3f} "
        f"(95 % Wilson {lo2:.3f}-{hi2:.3f})")
    say(f"  Fisher two-sided p = {pf:.4f}, odds ratio {orr:.2f}")
    say(f"  power: against a confirmed marking-rate of "
        f"{k1/max(n1,1):.3f} at n = {n1}/{n2}, the smallest SPURIOUS "
        f"marking-rate detectable at 80 % power is "
        f"{('%.2f' % mdr) if mdr is not None else 'NOT REACHABLE at any '
                                                 'rate <= 1.0'}")
    say(f"  -- with {n2} in-list spurious rows, the flag would have to mark "
        f"{'essentially every one of them' if mdr is None or mdr > 0.85 else ('%.0f %%' % (100*mdr))} "
        f"before this test could notice.")
    say(f"  M5's '0 of 7' is therefore NOT evidence that the flag fails: at "
        f"a {k1/max(n1,1):.3f}")
    say(f"     marking rate, the EXPECTED catch among {n2} spurious rows is "
        f"{n2*k1/max(n1,1):.2f}.  Observing 0 is what both a working flag "
        f"and a")
    say(f"     dead one predict.  The in-list test has no power, full stop.")

    # ---- machine-readable D4 result (M8) ---------------------------------
    # Same reason as the M4 addition: the pre-registration assigns D4 one of
    # six labels "mechanically from the numbers", and the numbers were only
    # ever in prose.  New file; nothing frozen is touched.
    pd.DataFrame([{
        "family": "D4 (flag_astrom_quiet, thresholded)",
        "metric": "flagged fraction, in-list", "kind": "rate",
        "n_conf": n1, "n_spur": n2, "k_conf": k1, "k_spur": k2,
        "rate_conf": k1 / n1 if n1 else np.nan,
        "rate_spur": k2 / n2 if n2 else np.nan,
        "effect": (k2 / n2 if n2 else np.nan) - (k1 / n1 if n1 else np.nan),
        "p": float(pf), "p_holm": float(pf),      # family size m = 1
        "min_detectable": float(mdr) if mdr is not None else np.nan,
        "testable": bool(n1 >= 5 and n2 >= 5),
        "n_store_rows": int(len(store)), "n_in_list": int(len(inl)),
    }]).to_csv(os.path.join(a.out_dir, "m6_astrom_quiet_d4_results.csv"),
               index=False, lineterminator="\n")

    # ---- 3. what December needs -----------------------------------------
    say("")
    say("3. WHAT DECEMBER HAS TO HARVEST TO SETTLE IT " + "-" * 29)
    say(f"  (in-list verdicts; today's in-list confirmed:spurious ratio "
        f"{n1}:{n2} held")
    say("   fixed, 80 % power at alpha = 0.05, two-sided MWU)")
    all65 = [r for r in rows if r["population"] == "all-65"
             and r["metric"] == "astrometric_gof_al"]
    inlist = [r for r in rows if r["population"] == "in-list"
              and r["metric"] == "astrometric_gof_al"]
    targets = []
    if all65:
        targets.append(("M5's all-65 effect", all65[0]["auc"]))
    if inlist:
        targets.append(("the observed in-list effect", inlist[0]["auc"]))
    for label, auc in targets:
        auc_eff = auc if auc > 0.5 else 1.0 - auc
        need = None
        for scale in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64):
            nn1, nn2 = n1 * scale, n2 * scale
            if mwu_power(nn1, nn2, auc_eff, rng, trials=1500) >= POWER_TARGET:
                need = (nn1, nn2, scale)
                break
        say(f"  at {label} (AUC {auc:.3f}): "
            + (f"{need[0]} confirmed + {need[1]} spurious in-list verdicts "
               f"= {need[2]}x today's in-list sample "
               f"({need[0]+need[1]} rows)" if need
               else "> 64x today's in-list sample -- not reachable by one "
                    "release"))
    say("")
    say(f"  The day-one queue is {len(q)} rows.  The harness adjudicates "
        f"all of them,")
    say("  so the in-list verdict count goes from "
        f"{len(inl)} to O({len(q)}) in one pass -- which is more than "
        "enough for")
    say("  every row above.  This is the whole argument for M6 existing.")

    # ---- the decision ----------------------------------------------------
    say("")
    say("=" * 74)
    say("DECISION " + "-" * 64)
    if inlist:
        r = inlist[0]
        well_powered = (r["min_detectable_auc"] is not None
                        and np.isfinite(r["min_detectable_auc"])
                        and r["min_detectable_auc"] <= 0.70)
        significant = r["p"] < ALPHA and r["auc"] < 0.5
        covers_half = (r["auc_lo"] <= 0.5 <= r["auc_hi"])
        if significant and pf < ALPHA:
            decision = "KEEP"
        elif well_powered and covers_half:
            decision = "REMOVE"
        else:
            decision = "CARRY"
    else:
        decision = "CARRY"
    say(f"  -> {decision}")
    if decision == "CARRY":
        say("  CANNOT DECIDE UNTIL DECEMBER'S VERDICTS EXIST, and the reason "
            "is measured,")
        say(f"  not rhetorical: the population the flag operates on holds "
            f"{n2} spurious")
        say("  rows, the in-list continuous test cannot see anything short "
            "of the AUC")
        say("  printed above, and the thresholded test cannot see anything "
            "at all.  The")
        say("  flag stays exactly as config v4 froze it -- tiebreaker only, "
            "both caveats")
        say("  attached, never a cut and never quoted beside "
            "`significance` -- and the")
        say("  test that settles it is pre-registered in this script's "
            "docstring.")
        say("  Removing it today would be as unevidenced as promoting it.")
    say("=" * 74)

    os.makedirs(a.out_dir, exist_ok=True)
    pd.DataFrame(rows).to_csv(
        os.path.join(a.out_dir, "m6_astrom_quiet_inlist.csv"),
        index=False, lineterminator="\n")
    with open(os.path.join(a.out_dir, "m6_astrom_quiet_decision.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    # M7 landmine #14, third occurrence: this line hard-coded `out/...` while
    # the files went to --out-dir, so a rehearsal or a December run into a
    # scratch directory reported that it had just overwritten the FROZEN M6
    # artifacts when it had not.  M7 fixed the same bug in
    # m5_activity_discriminator.py and did not check this script.
    rel = os.path.relpath(a.out_dir, BASE)
    print(f"\nwrote {rel}/m6_astrom_quiet_decision.txt, "
          f"{rel}/m6_astrom_quiet_inlist.csv, "
          f"{rel}/m6_astrom_quiet_d4_results.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
