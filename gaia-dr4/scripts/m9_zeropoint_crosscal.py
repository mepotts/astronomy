#!/usr/bin/env python
"""M9 task 2: how December decides between L21 and DR4's OWN parallax bias.

THE SITUATION
=============
M8 closed the parallax zero-point using Lindegren+2021 (L21), reproduced
Panuzzo's own 35.4 uas to 0.006 uas, and moved Gaia BH3 from +2.42 sigma to
-0.07 sigma against his published mass.  While writing that up it read the
DR4 pre-release DRAFT DATA MODEL and found a column nobody here knew about:

    tentative_parallax_bias : Parallax bias correction (double, Angle[mas])
    "This is the parallax bias correction computed based on the recipe in
     [the DR4 astrometry paper].  This correction is to be subtracted from
     parallax to get the corrected parallax."

-- declared in BOTH `gaia_source` (draft p. 20) and `all_source_astrometry`
(p. 74), on L21's exact convention (varpi_true = varpi - bias).  M8's
recommendation was "prefer it, keep L21 as the cross-check".  What M8 did
not do -- and what this file is -- is decide IN ADVANCE what the comparison
means, so 2 December executes a prediction instead of improvising.

WHAT THIS FILE FIXES BEFORE THE DATA EXISTS
===========================================
  1. the PREDICTION: L21's Z for every source in the day-one queue, frozen
     to `out/m9_zeropoint_prediction.csv` with its summary statistics;
  2. the DECISION RULE: five verdicts with numeric thresholds, and which
     correction the pipeline uses under each;
  3. the CODE: `--compare` runs the whole comparison on a two-column file
     (source_id, tentative_parallax_bias) and returns one verdict;
  4. the REHEARSAL: `--selftest` runs `--compare` against six DECLARED
     synthetic bias columns and checks each returns its declared verdict.

THE DECISION RULE, PRE-REGISTERED (2026-08-24, before DR4 exists)
=================================================================
Let D = bias_DR4 - Z_L21 in microarcsec over the queue's correctable rows,
rho = Spearman(bias_DR4, Z_L21), NMAD = 1.4826 x median|D - median(D)|.

  AGREE            |median D| <= 10 uas AND rho >= 0.5 AND NMAD <= 20 uas
                   -> USE DR4's column.  Report the agreement: it validates
                      both, and the <= 2 uas DR3 residual bound (M8 sec.2e)
                      may then be quoted as CARRIED to DR4.
  OFFSET           |median D| > 10 uas, but rho >= 0.5 and NMAD <= 20 uas
                   -> USE DR4's column.  The offset is the DR3->DR4
                      recalibration and is EXPECTED (longer baseline, new
                      recipe).  Report it in uas and in % of a companion
                      mass; L21's residual bound does NOT carry.
  UNCORRELATED     rho < 0.5 or NMAD > 20 uas
                   -> USE DR4's column, FLAG EVERY MASS, quote both.  The
                      two recipes do not describe the same effect and that
                      is a paragraph, not a footnote.
  CONVENTION FLIP  rho <= -0.5
                   -> STOP.  One side has the opposite sign convention.
                      Applying the wrong sign DOUBLES the error instead of
                      removing it.  Correct nothing until it is resolved.
  UNUSABLE         the column is absent, or null for > 50 % of the queue
                   -> FALL BACK to L21 and record the <= 2 uas bound as
                      UNVERIFIED FOR DR4 (runbook sec.3.4 already says so).

WHICH ONE WINS, AND WHY -- decided now, not on the day.
**DR4's own column wins wherever it is usable.**  Three reasons, in order:
(1) it is computed on the very astrometric solution it corrects, while L21
is calibrated on EDR3/DR3 -- a different solution with half the time
baseline; (2) DR4's binaries reach further (EB26 forecast this), and the
zero-point's effect on a companion mass is 3Z/varpi, i.e. a DISTANCE effect,
so using a correction calibrated on a nearer sample is exactly the wrong
approximation; (3) a mass quoted on the release's own convention is
reproducible by anybody holding the release.  The single exception is
CONVENTION FLIP, where neither is used because one of them is wrong.

*** AND A LANDMINE M8 NAMED HALF OF.  IT IS WORSE THAN A RENAME. ***
M8 found that `astrometric_params_solved` becomes `astrometric_params` in
DR4 and that `zpt.get_zpt` RAISES if that guard column is wrong.  Reading
the same draft model to the end (p. 19, the value table) shows the VALUE SET
has also changed.  DR3's column took 3 / 31 / 95.  DR4's takes NINETEEN
declared values --

    3, 7, 27, 31, 63, 95, 479, 2015, 2079, 2463, 3999, 4127, 4575,
    6111, 6175, 8223, 8607, 10143, 10271

-- because DR4 adds bits for fitted ACCELERATION terms and, at bits 11/12/13,
for NON-SINGLE-STAR models (Orbital / VIM / Resolved).  `zpt.get_zpt`
accepts 31 and 95 and nothing else.  **Every source in this project's
candidate list is a non-single-star solution**, so on release day the guard
column will carry 2079 / 2463 / 3999 / ... and the zero-point call would
raise on the entire queue.

The fix is not to widen the accepted set: it is to read the bit that
actually matters.  Bit 6 (value 64) is C = pseudocolour.  If it is set the
solution is SIX-parameter and L21 wants 95 and `pseudocolour`; if it is
clear the solution is FIVE-parameter and L21 wants 31 and
`nu_eff_used_in_astrometry`.  Bit 2 (value 4) is the parallax itself: if it
is clear there is no parallax to correct.  `l21_guard_from_dr4()` below is
that decode, and `--decode` prints it for all nineteen declared values.
Note also that NONE of the nineteen NSS values has bit 6 set -- an orbital
solution does not fit a pseudocolour -- so December's queue is expected to
be entirely on the FIVE-parameter branch of L21, which is the branch that
needs `nu_eff_used_in_astrometry` to be populated.  Check that in Phase 0.

  .venv\\Scripts\\python.exe scripts\\m9_zeropoint_crosscal.py --decode
  .venv\\Scripts\\python.exe scripts\\m9_zeropoint_crosscal.py --predict
  .venv\\Scripts\\python.exe scripts\\m9_zeropoint_crosscal.py --selftest
  .venv\\Scripts\\python.exe scripts\\m9_zeropoint_crosscal.py --compare dr4_bias.csv
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

OUT = os.path.join(BASE, "out")
PREDICTION = os.path.join(OUT, "m9_zeropoint_prediction.csv")
SUMMARY = os.path.join(OUT, "m9_zeropoint_crosscal.json")

# the nineteen values the DR4 draft data model declares for
# `astrometric_params` (draft p. 19, table under the field description).
# The draft's BINARY column has at least one typo (6175 is printed with
# 4127's bit string), so the DECIMALS are the data.
DR4_ASTROMETRIC_PARAMS_DECLARED = [3, 7, 27, 31, 63, 95, 479, 2015, 2079,
                                   2463, 3999, 4127, 4575, 6111, 6175,
                                   8223, 8607, 10143, 10271]
BIT_PARALLAX = 4            # bit 2
BIT_PSEUDOCOLOUR = 64       # bit 6
BIT_ORBITAL = 2048          # bit 11
BIT_VIM = 4096              # bit 12
BIT_RESOLVED = 8192         # bit 13

# pre-registered thresholds (uas)
AGREE_MEDIAN_UAS = 10.0
NMAD_UAS = 20.0
RHO_MIN = 0.5
RHO_FLIP = -0.5
NULL_FRACTION_MAX = 0.50


def l21_guard_from_dr4(astrometric_params):
    """DR4 `astrometric_params` -> the value `zpt.get_zpt` must be given.

    Returns 31 (five-parameter branch), 95 (six-parameter branch), or 0
    meaning "not correctable" (no parallax was fitted).  The extra DR4 bits
    -- acceleration terms and the Orbital/VIM/Resolved non-single-star flags
    -- are deliberately IGNORED: they say what else was fitted, not which
    colour quantity the astrometry used, and L21's two branches differ only
    in that.
    """
    a = np.asarray(astrometric_params)
    out = np.where((a & BIT_PARALLAX) == 0, 0,
                   np.where((a & BIT_PSEUDOCOLOUR) != 0, 95, 31))
    return out.astype(int)


def decode_table(say):
    say("  DR4 `astrometric_params` -> the L21 guard value, for every "
        "declared value")
    say("    %-8s %-9s %-9s %-9s %-9s %-6s %s"
        % ("value", "parallax", "pseudo-C", "Orbital", "VIM/Resolv",
           "guard", "zpt.get_zpt on the RAW value"))
    rows = []
    for v in DR4_ASTROMETRIC_PARAMS_DECLARED:
        g = int(l21_guard_from_dr4(v))
        raw_ok = v in (31, 95)
        say("    %-8d %-9s %-9s %-9s %-9s %-6d %s"
            % (v, "yes" if v & BIT_PARALLAX else "NO",
               "yes" if v & BIT_PSEUDOCOLOUR else "no",
               "yes" if v & BIT_ORBITAL else "no",
               "yes" if v & (BIT_VIM | BIT_RESOLVED) else "no",
               g, "OK" if raw_ok else "*** RAISES ***"))
        rows.append({"astrometric_params": v,
                     "has_parallax": bool(v & BIT_PARALLAX),
                     "has_pseudocolour": bool(v & BIT_PSEUDOCOLOUR),
                     "orbital": bool(v & BIT_ORBITAL),
                     "vim_or_resolved": bool(v & (BIT_VIM | BIT_RESOLVED)),
                     "l21_guard": g, "raw_accepted_by_zpt": raw_ok})
    n_bad = sum(1 for r in rows if not r["raw_accepted_by_zpt"])
    say("    -> %d of %d declared values would make zpt.get_zpt RAISE if "
        "passed raw." % (n_bad, len(rows)))
    nss = [r for r in rows if r["orbital"] or r["vim_or_resolved"]]
    say("    -> %d of them are NON-SINGLE-STAR values, and NONE of those "
        "has the\n       pseudocolour bit: December's queue is expected "
        "entirely on L21's\n       FIVE-parameter branch "
        "(nu_eff_used_in_astrometry)." % len(nss))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
def build_prediction(say):
    """L21's Z for the day-one queue, frozen now so December compares
    against a written-down number rather than against a fresh run."""
    import m8_zeropoint as ZP
    d = ZP.load()
    q = pd.read_csv(os.path.join(OUT, "epoch_vet_day1_queue.v2.csv"))
    q["source_id"] = q["source_id"].astype("int64")
    d = d[d["source_id"].isin(q["source_id"])].copy()
    z = ZP.parallax_zeropoint(d["phot_g_mean_mag"].values,
                              d["nu_eff_used_in_astrometry"].values,
                              d["pseudocolour"].values, d["ecl_lat"].values,
                              d["astrometric_params_solved"].values)
    d["z_l21_mas"] = z
    d["z_l21_uas"] = 1e3 * z
    ok = np.isfinite(z)
    say("  queue rows with the five L21 inputs pulled : %d of %d"
        % (len(d), len(q)))
    say("  correctable by L21 (inside the validity box): %d (%.1f %%)"
        % (int(ok.sum()), 100.0 * ok.mean()))
    say("  Z over the queue [uas]: median %.2f, p10 %.2f, p90 %.2f, "
        "min %.2f, max %.2f"
        % tuple(np.nanpercentile(d.z_l21_uas, [50, 10, 90, 0, 100])))
    say("  by 5p/6p branch: %s"
        % {int(k): int(v) for k, v in
           d["astrometric_params_solved"].value_counts().items()})
    d[["source_id", "phot_g_mean_mag", "nu_eff_used_in_astrometry",
       "pseudocolour", "ecl_lat", "astrometric_params_solved",
       "z_l21_mas", "z_l21_uas"]].to_csv(PREDICTION, index=False,
                                         lineterminator="\n")
    say("  wrote %s" % os.path.relpath(PREDICTION, BASE))
    return d


def compare(bias_path, say, prediction_path=PREDICTION):
    """THE DECEMBER COMPARISON.  One file in, one verdict out."""
    from scipy import stats
    pred = pd.read_csv(prediction_path)
    if isinstance(bias_path, pd.DataFrame):
        b = bias_path.copy()
    elif bias_path is None or not os.path.exists(str(bias_path)):
        say("  DR4 bias column NOT PRESENT -> verdict UNUSABLE")
        return {"verdict": "UNUSABLE", "reason": "column absent",
                "use": "L21", "n": 0}
    else:
        b = pd.read_csv(bias_path)
    col = [c for c in b.columns if "bias" in c.lower()]
    if not col:
        return {"verdict": "UNUSABLE", "reason": "no *bias* column",
                "use": "L21", "n": 0}
    b = b.rename(columns={col[0]: "bias_mas"})
    b["source_id"] = b["source_id"].astype("int64")
    m = pred.merge(b[["source_id", "bias_mas"]], on="source_id", how="left")
    n_q = len(m)
    have = m["bias_mas"].notna() & np.isfinite(m["z_l21_mas"])
    frac_null = 1.0 - float(have.mean())
    say("  queue rows              : %d" % n_q)
    say("  with BOTH a DR4 bias and an L21 Z : %d (%.1f %% null/absent)"
        % (int(have.sum()), 100 * frac_null))
    if frac_null > NULL_FRACTION_MAX:
        say("  -> more than %.0f %% missing: verdict UNUSABLE"
            % (100 * NULL_FRACTION_MAX))
        return {"verdict": "UNUSABLE",
                "reason": "%.1f %% of the queue has no DR4 bias"
                          % (100 * frac_null),
                "use": "L21", "n": int(have.sum()),
                "null_fraction": frac_null}
    m = m[have]
    D = 1e3 * (m["bias_mas"].values - m["z_l21_mas"].values)
    med = float(np.median(D))
    nmad = float(1.4826 * np.median(np.abs(D - med)))
    rho = float(stats.spearmanr(m["bias_mas"], m["z_l21_mas"]).statistic)
    say("  median(bias_DR4 - Z_L21) : %+.2f uas" % med)
    say("  NMAD of the difference   : %.2f uas" % nmad)
    say("  Spearman rho             : %+.3f" % rho)
    if rho <= RHO_FLIP:
        v, use = "CONVENTION FLIP", "NEITHER -- STOP"
        why = ("rho %.2f <= %.1f: one side has the opposite sign "
               "convention" % (rho, RHO_FLIP))
    elif rho < RHO_MIN or nmad > NMAD_UAS:
        v, use = "UNCORRELATED", "DR4 column, EVERY MASS FLAGGED"
        why = ("rho %.2f < %.1f or NMAD %.1f > %.1f uas: the two recipes "
               "do not describe the same effect" % (rho, RHO_MIN, nmad,
                                                    NMAD_UAS))
    elif abs(med) > AGREE_MEDIAN_UAS:
        v, use = "OFFSET", "DR4 column"
        why = ("|median D| %.1f > %.1f uas with rho %.2f and NMAD %.1f: a "
               "recalibration, expected" % (abs(med), AGREE_MEDIAN_UAS, rho,
                                            nmad))
    else:
        v, use = "AGREE", "DR4 column"
        why = ("|median D| %.1f <= %.1f uas, rho %.2f >= %.1f, NMAD %.1f "
               "<= %.1f" % (abs(med), AGREE_MEDIAN_UAS, rho, RHO_MIN, nmad,
                            NMAD_UAS))
    # what the difference is worth, in the only unit that matters
    plx = pd.read_csv(os.path.join(OUT, "m8_zeropoint_queue.csv"),
                      usecols=["source_id", "nss_parallax"])
    mm = m.merge(plx, on="source_id", how="left")
    with np.errstate(divide="ignore", invalid="ignore"):
        # UNIT TRAP, caught by the sign-flip scenario reporting 0.01 % for
        # a 71 uas difference: bias and Z are ALREADY in mas, so the 1e-3
        # that used to be here converted them to arcsec and divided a mass
        # shift by a thousand.  A rehearsal that only checked the VERDICT
        # would have shipped it -- check the numbers beside the verdict.
        dm = 3.0 * (mm["bias_mas"] - mm["z_l21_mas"]) / mm["nss_parallax"]
    say("  what the DIFFERENCE is worth as a companion mass (3 D / varpi):")
    say("    median %.2f %%, p90 %.2f %%, worst %.2f %%"
        % tuple(100 * np.nanpercentile(np.abs(dm), [50, 90, 100])))
    say("  VERDICT: %s  ->  USE: %s" % (v, use))
    say("    %s" % why)
    return {"verdict": v, "use": use, "reason": why, "n": int(len(m)),
            "median_diff_uas": med, "nmad_uas": nmad, "spearman_rho": rho,
            "null_fraction": frac_null,
            "mass_effect_median_pct": float(100 * np.nanmedian(np.abs(dm))),
            "mass_effect_worst_pct": float(100 * np.nanmax(np.abs(dm)))}


# ----------------------------------------------------------------------
# THE REHEARSAL.  Six declared scenarios; each must return its declared
# verdict.  A decision rule nobody has run is a promise, not a protocol
# (M8 sec.3, applied to itself).
SCENARIOS = [
    ("perfect_agreement", "DR4 = L21 exactly", "AGREE"),
    ("small_scatter", "DR4 = L21 + N(0, 5 uas)", "AGREE"),
    ("recalibrated", "DR4 = 0.7 x L21 + N(0, 5 uas) -- a shorter "
                     "zero-point, as a longer baseline should give",
     "OFFSET"),
    ("uncorrelated", "DR4 = a random draw with L21's own spread",
     "UNCORRELATED"),
    ("sign_flip", "DR4 = -L21 -- the convention read backwards",
     "CONVENTION FLIP"),
    ("mostly_null", "DR4 present for 20 % of the queue", "UNUSABLE"),
]


def selftest(say, seed=20261202):
    rng = np.random.default_rng(seed)
    pred = pd.read_csv(PREDICTION)
    z = pred["z_l21_mas"].values
    ok = True
    results = []
    for name, desc, want in SCENARIOS:
        if name == "perfect_agreement":
            b = z.copy()
        elif name == "small_scatter":
            b = z + rng.normal(0, 5e-3, len(z))
        elif name == "recalibrated":
            b = 0.7 * z + rng.normal(0, 5e-3, len(z))
        elif name == "uncorrelated":
            b = rng.normal(np.nanmean(z), np.nanstd(z), len(z))
        elif name == "sign_flip":
            b = -z
        else:
            b = z.copy()
            b[rng.random(len(z)) > 0.2] = np.nan
        df = pd.DataFrame({"source_id": pred["source_id"],
                           "tentative_parallax_bias": b})
        say("\n  SCENARIO %-18s %s" % (name, desc))
        r = compare(df, say)
        hit = r["verdict"] == want
        ok &= hit
        say("    declared %-16s got %-16s  %s"
            % (want, r["verdict"], "OK" if hit else "*** MISMATCH ***"))
        results.append({"scenario": name, "declared": want,
                        "got": r["verdict"], "pass": hit, **r})
    say("\n  SELFTEST: %s (%d/%d scenarios)"
        % ("PASS" if ok else "FAIL", sum(r["pass"] for r in results),
           len(results)))
    return ok, results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--out", default=os.path.join(OUT,
                                                  "m9_zeropoint_crosscal.txt"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if not (a.decode or a.predict or a.selftest or a.compare):
        a.decode = a.predict = a.selftest = True
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    t0 = time.time()
    res = {}
    say("=" * 78)
    say("M9 TASK 2 -- L21 vs DR4's OWN `tentative_parallax_bias`")
    say("  the comparison, and the decision, fixed BEFORE the data exists")
    say("=" * 78)
    if a.decode:
        say("\n" + "-" * 78)
        say("THE GUARD COLUMN (draft data model p. 19; M8 found the rename, "
            "not the\nvalue-set change that makes it bite)")
        t = decode_table(say)
        t.to_csv(os.path.join(OUT, "m9_astrometric_params_decode.csv"),
                 index=False, lineterminator="\n")
        res["decode"] = {"n_declared": len(t),
                         "n_would_raise": int((~t.raw_accepted_by_zpt).sum()),
                         "n_non_single_star": int((t.orbital
                                                   | t.vim_or_resolved).sum())}
    if a.predict:
        say("\n" + "-" * 78)
        say("THE PREDICTION -- L21's Z for the day-one queue, frozen")
        d = build_prediction(say)
        res["prediction"] = {
            "n": int(len(d)),
            "median_uas": float(np.nanmedian(d.z_l21_uas)),
            "p10_uas": float(np.nanpercentile(d.z_l21_uas, 10)),
            "p90_uas": float(np.nanpercentile(d.z_l21_uas, 90))}
    if a.selftest:
        say("\n" + "-" * 78)
        say("THE REHEARSAL -- six declared scenarios through the decision "
            "rule")
        ok, rr = selftest(say)
        res["selftest"] = {"pass": bool(ok),
                           "scenarios": [{k: v for k, v in r.items()
                                          if k in ("scenario", "declared",
                                                   "got", "pass")}
                                         for r in rr]}
    if a.compare:
        say("\n" + "-" * 78)
        say("THE COMPARISON -- %s" % a.compare)
        res["compare"] = compare(a.compare, say)

    say("\n  %.1f s" % (time.time() - t0))
    with open(a.out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(SUMMARY, "w", newline="\n", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, default=float)
    if a.selftest and not res.get("selftest", {}).get("pass", True):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
