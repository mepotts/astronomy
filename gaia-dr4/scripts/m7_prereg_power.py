#!/usr/bin/env python
"""M7 task 3: the numbers behind the December pre-registration.

Every sample threshold quoted in
`PREREG-2026-08-23-december-discriminators.md` is computed here, and it is
computed by IMPORTING M5's own power routines rather than by reimplementing
them.  That matters: a fresh normal-approximation implementation written
here reproduced M5's published `min_detectable` column only to about 2 %
(0.711 vs 0.725 at n = 42/23, 0.816 vs 0.800 at n = 40/8), because M5's is a
Monte-Carlo power on the exact MWU evaluated on a 0.025 grid and M4's Fisher
routine scans a 0.05 grid.  Two power conventions in one repository is one
too many, and the pre-registration must be readable against the published
numbers without a footnote.  So: same functions, same alpha, same target
power, same grids.

Nothing here reads a verdict.  It runs before December's data exists, which
is the point.

Run: .venv/Scripts/python.exe scripts/m7_prereg_power.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m5_activity_discriminator as M5                           # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
SEED = 20261202

# conf:spur ratios December might deliver.  The harness's own split is not
# knowable in advance, so every threshold is quoted at three.
RATIOS = [("1:1", 1.0),
          ("1.83:1 (the EB26 split 42:23)", 42.0 / 23.0),
          ("0.33:1 (the M6 pre-release harness split 3:9)", 3.0 / 9.0)]


def n_for_auc(auc, ratio, rng, nmax=4000):
    """Smallest (n_conf, n_spur) at a fixed conf:spur ratio reaching M5's
    POWER_TARGET against `auc`, searched on a coarse-then-fine ladder."""
    lo, hi = 3, nmax
    while lo < hi:
        n2 = (lo + hi) // 2
        n1 = max(3, int(round(n2 * ratio)))
        if M5.mwu_power(n1, n2, auc, rng) >= M5.POWER_TARGET:
            hi = n2
        else:
            lo = n2 + 1
    n2 = lo
    return max(3, int(round(n2 * ratio))), n2


def n_for_fisher(p1, p2, ratio, nmax=2000):
    """Smallest (n_conf, n_spur) at a fixed ratio reaching POWER_TARGET.

    p1 = SPURIOUS event rate, p2 = CONFIRMED event rate.  M5's fisher_power
    signature is (n1, p1, n2, p2) with group 1 first.
    """
    lo, hi = 4, nmax
    while lo < hi:
        n_spur = (lo + hi) // 2
        n_conf = max(4, int(round(n_spur * ratio)))
        if M5.fisher_power(n_spur, p1, n_conf, p2) >= M5.POWER_TARGET:
            hi = n_spur
        else:
            lo = n_spur + 1
    n_spur = lo
    return max(4, int(round(n_spur * ratio))), n_spur


def main():
    rng = np.random.default_rng(SEED)
    L = []

    def say(s=""):
        L.append(s)
        print(s, flush=True)

    say("M7 -- decisive-sample thresholds for the December discriminator "
        "re-runs")
    say("=" * 74)
    say("Computed 2026-08-23, BEFORE any December verdict exists.")
    say("alpha = %.2f two-sided, target power = %.0f %%, using M5's own "
        "power routines" % (M5.ALPHA, 100 * M5.POWER_TARGET))
    say("(scripts/m5_activity_discriminator.py: mwu_power / "
        "min_detectable_auc on a 0.025")
    say("AUC grid, fisher_power / min_detectable_rate on a 0.05 rate grid, "
        "%d MC trials)." % M5.N_POWER_TRIALS)
    say("")

    say("0. REPRODUCTION OF THE PUBLISHED POWER STATEMENTS (a check on this "
        "driver)")
    say("-" * 74)
    a1 = M5.min_detectable_auc(42, 23, rng)
    say("  M5 families B/C, n = 42 conf / 23 spur : min detectable AUC "
        "%.3f   (M5 published 0.725)  %s"
        % (a1, "MATCH" if abs(a1 - 0.725) < 1e-9 else "DIFFERS"))
    a2 = M5.min_detectable_auc(40, 8, rng)
    say("  M6 in-list,      n = 40 conf /  8 spur : min detectable AUC "
        "%.3f   (M6 published 0.800)  %s"
        % (a2, "MATCH" if abs(a2 - 0.800) < 1e-9 else "DIFFERS"))
    # ARGUMENT ORDER MATTERS AND IS EASY TO GET BACKWARDS.  M5's signature
    # is min_detectable_rate(n1, p0, n2): group 1 has size n1 and the FIXED
    # rate p0, group 2 has size n2 and the rate being solved for.  Passing
    # (8, 0.075, 40) -- the spurious group first -- returns 0.60 instead of
    # M6's published 0.55, and the mismatch is the only reason it was
    # caught.  The reproduction block earns its keep.
    r1 = M5.min_detectable_rate(40, 0.075, 8)
    say("  M6 thresholded flag, n = 40/8, confirmed marking rate 0.075:")
    say("      min detectable SPURIOUS marking rate %.2f   (M6 published "
        "0.55)  %s"
        % (r1, "MATCH" if abs(r1 - 0.55) < 1e-9 else "DIFFERS"))
    r2 = M5.min_detectable_rate(16, 0.0, 13)
    say("  M4 X-ray, n = 16 conf / 13 spur, confirmed detection rate 0.000:")
    say("      min detectable SPURIOUS detection rate %.2f   (M4 published "
        "0.40)  %s"
        % (r2, "MATCH" if abs(r2 - 0.40) < 1e-9 else "DIFFERS"))
    say("")

    say("1. HOW BIG DECEMBER'S VERDICT SAMPLE HAS TO BE, PER TEST")
    say("-" * 74)
    say("")

    say("  D1  X-RAY (eROSITA-DE) -- Fisher on the detection rate")
    say("      effect under test = M4's observed SPURIOUS 0.154 vs "
        "CONFIRMED 0.000.")
    say("      The n below are IN-FOOTPRINT. eROSITA-DE is half the sky and "
        "M4 found")
    say("      29 of 65 verdicted targets inside it (45 %), so the total "
        "verdict")
    say("      count needed is roughly the in-footprint count divided by "
        "0.45.")
    for lab, r in RATIOS:
        nc, ns = n_for_fisher(0.154, 0.0, r)
        say("      %-46s %4d conf + %4d spur in footprint  (~%d verdicts)"
            % (lab, nc, ns, int((nc + ns) / 0.45)))
    say("      against a non-zero CONFIRMED baseline of 0.02, which is the "
        "more")
    say("      honest null (M4's 0/16 is a point estimate of zero, not a "
        "zero):")
    for lab, r in RATIOS:
        nc, ns = n_for_fisher(0.154, 0.02, r)
        say("      %-46s %4d conf + %4d spur in footprint" % (lab, nc, ns))
    say("")

    say("  D2  PHOTOMETRIC VARIABILITY (dAmp_G, magnitude-detrended) -- MWU")
    say("      effect under test = M5's observed AUC 0.659 (spurious MORE "
        "variable).")
    for lab, r in RATIOS:
        nc, ns = n_for_auc(0.659, r, rng)
        say("      %-46s %4d conf + %4d spur" % (lab, nc, ns))
    say("      (M5 published 'about 84 + 46' at the EB26 ratio, from a "
        "coarser scan;")
    say("       the EB26-ratio line above supersedes it as the frozen "
        "threshold.)")
    say("")

    say("  D3  ASTROMETRIC QUALITY (astrometric_gof_al) -- MWU")
    say("      effect under test (a) = M5's all-65 AUC 0.254, i.e. 0.746 on "
        "the high side")
    for lab, r in RATIOS:
        nc, ns = n_for_auc(0.746, r, rng)
        say("      %-46s %4d conf + %4d spur" % (lab, nc, ns))
    say("      effect under test (b) = M6's weaker IN-LIST AUC 0.344, i.e. "
        "0.656 high side")
    say("      -- (b) is the binding one, because the day-one sample IS the "
        "in-list")
    say("      population and M6 showed the two populations give different "
        "effects.")
    for lab, r in RATIOS:
        nc, ns = n_for_auc(0.656, r, rng)
        say("      %-46s %4d conf + %4d spur" % (lab, nc, ns))
    say("")

    say("  D4  flag_astrom_quiet, THRESHOLDED -- Fisher on the marking rate")
    say("      effect under test = the flag marks SPURIOUS at 0.30 against "
        "the")
    say("      measured in-list CONFIRMED marking rate of 0.075.  0.30 is "
        "DECLARED")
    say("      here, in advance, as the smallest marking rate that would "
        "make the")
    say("      flag worth keeping as a tiebreaker; it is not the observed "
        "0.00, and")
    say("      choosing it after seeing December would be the exact "
        "manoeuvre this")
    say("      pre-registration exists to prevent.")
    for lab, r in RATIOS:
        nc, ns = n_for_fisher(0.30, 0.075, r)
        say("      %-46s %4d conf + %4d spur in the QUEUE" % (lab, nc, ns))
    say("")

    say("2. WHAT ONE HARNESS PASS OVER THE 981-ROW QUEUE DELIVERS")
    say("-" * 74)
    say("  Every adjudicated queue row is an in-list verdict by "
        "construction, so the")
    say("  binding quantity is the CONFIRMED:SPURIOUS split, not the total.")
    for lab, r in RATIOS:
        ns = 981.0 / (1.0 + r)
        say("      %-46s ~%4d conf + %4d spur" % (lab, int(981 - ns), int(ns)))
    say("  Read D2, D3 and D4 against those rows: at every ratio, one full "
        "pass")
    say("  clears them.  D1 is the exception and cannot be cleared by "
        "throughput --")
    say("  it is capped by the eROSITA-DE footprint at ~45 % of whatever "
        "is")
    say("  adjudicated, and by the low absolute detection rate.")

    p = os.path.join(OUT, "m7_prereg_power.txt")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\nwrote %s" % os.path.relpath(p, BASE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
