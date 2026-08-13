"""Sweep the subset guard's used-observation threshold, including against ground truth.

WHY THIS EXISTS. The note reports one guard at one threshold -- 80% of observations used --
and `rnaas-notes.md` names the obvious objection: "an 80% threshold with a three-night rule
is a blunt instrument". A referee will ask why 0.8. The honest answer is a curve, not a
paragraph, and it is cheap: both halves of the guard are reconstructible from the stored
per-fit records, so no refitting is needed.

* the **used-fraction** half varies with the threshold and is recomputed from ``n_used`` and
  ``n_obs``;
* the **used-nights** half does not vary with it, so whether a fit failed that half is read
  off its stored ``gate_reasons``.

TWO CURVES, AND THE SECOND IS THE POINT. Raising a threshold always rejects more, so a
rejection-rate curve on its own says nothing about whether the rejections are *right*. The
second curve puts each threshold against the links an independent archival test confirms
somebody else made -- the only ground truth this project has. It answers the question a
referee actually cares about: at what threshold does this check start discarding links that
are real?

    python scripts/guard_threshold_curve.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_vs_confirmed import GUARD_REASONS, confirmed_link_keys

NIGHTS_REASON = "observations actually used span"
UNAVAILABLE_REASON = "observation counts unavailable"
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


def guard_rejects(o: dict, threshold: float) -> bool:
    """Would the guard reject this fit if MIN_USED_FRACTION were ``threshold``?"""
    reasons = o.get("gate_reasons") or []
    if any(UNAVAILABLE_REASON in r for r in reasons):
        return True
    n_obs, n_used = o.get("n_obs"), o.get("n_used")
    if not n_obs or n_used is None:
        return True
    if any(NIGHTS_REASON in r for r in reasons):
        return True           # the nights half is independent of the threshold
    return (n_used / n_obs) < threshold


def meets_gate(o: dict) -> bool:
    """Acceptance-gate pass: every stored reason came from the guard, not the gate."""
    return all(any(f in r for f in GUARD_REASONS) for r in (o.get("gate_reasons") or []))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, default=Path("m4-new.json"))
    ap.add_argument("--links", type=Path, default=Path("data/link-candidates.parquet"))
    ap.add_argument("--snapshots", type=Path, default=Path("data/snapshots"))
    args = ap.parse_args(argv)

    outcomes = json.loads(args.report.read_text(encoding="utf-8"))["fits"]["outcomes"]
    converged = [o for o in outcomes if o.get("converged")]
    gate_ok = [o for o in converged if meets_gate(o)]
    print(f"{args.report.name}: {len(converged):,} converged, {len(gate_ok):,} meet our gate\n")

    confirmed = confirmed_link_keys(args.snapshots, args.links)
    truth = [o for o in outcomes if frozenset(o["source_desigs"]) in confirmed]
    truth_conv = [o for o in truth if o.get("converged")]
    print(f"ground truth: {len(confirmed)} independently confirmed links, "
          f"{len(truth)} rows here, {len(truth_conv)} converged\n")

    print("| threshold | rejected of converged | rejected of gate-passers | "
          "confirmed links rejected |")
    print("|---:|---:|---:|---:|")
    for t in THRESHOLDS:
        n_all = sum(guard_rejects(o, t) for o in converged)
        n_gate = sum(guard_rejects(o, t) for o in gate_ok)
        n_true = sum(guard_rejects(o, t) for o in truth_conv)
        star = "  <- shipped" if abs(t - 0.8) < 1e-9 else ""
        print(f"| {t:.0%} | {n_all:,} ({100*n_all/len(converged):.1f}%) | "
              f"{n_gate:,} ({100*n_gate/max(len(gate_ok),1):.1f}%) | "
              f"{n_true} of {len(truth_conv)}{star} |")

    shipped = sum(guard_rejects(o, 0.8) for o in converged)
    print(f"\nsanity: at 0.8 the recomputation gives {shipped:,} rejections of converged "
          f"fits; the run itself recorded "
          f"{json.loads(args.report.read_text(encoding='utf-8'))['fits']['failed_subset_guard']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
