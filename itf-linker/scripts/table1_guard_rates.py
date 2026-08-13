"""Regenerate Table 1 of the RNAAS note from the archived run reports.

WHY THIS EXISTS. Columns 5 and 6 of that table are the load-bearing numbers -- the guard's
effect *restricted to solutions our acceptance gate already accepts* -- and they are the only
figures in the note that are not a stored field in a report. They were derived by throwaway
scripts that lived in a session scratchpad, which `rnaas-notes.md` flagged as a blocker:
"If the note is ever submitted, they should be committed so column 6 is reproducible by a
reader." This is that script.

HOW COLUMNS 5 AND 6 ARE DERIVED. Each report carries per-fit records in ``fits.outcomes[]``,
each with ``gate_reasons``. Two rules are applied to converged fits only:

* **column 5** -- the fit meets our acceptance gate iff *every* entry in ``gate_reasons`` is
  one of the subset guard's own reason strings (or there are none). The guard's strings and
  the acceptance gate's are textually disjoint, so this partitions cleanly without having to
  re-run either check.
* **column 6** -- of those, the ones carrying at least one guard reason: solutions an
  RMS-based filter would have passed and the guard caught.

SELF-CHECK. ``column 5 - column 6`` must equal the report's own ``fits.passed_all_gates``,
independently computed at run time by a different code path. All four rows are checked and
the script exits non-zero if any disagrees.

A NOTE ON THE LABEL. These columns count fits meeting **our** gate -- an unconditional 0.25"
RMS ceiling plus the sigma limits on three-night links -- which is stricter than the MPC's
published rule on both counts (see ``fit/gates.py``). Earlier drafts called it "the published
criteria"; the numbers were always this.

    python scripts/table1_guard_rates.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: Reason fragments emitted by the supplementary subset guard rather than the acceptance
#: gate. From ``fit/collide.py``; kept as fragments because two of them interpolate counts.
GUARD_REASONS = (
    "fit used only",
    "observations actually used span",
    "observation counts unavailable",
)

#: Report file, row label, and the hypothesis count for that run.
ROWS = [
    ("m1-report.json", "Survey pipelines (survey-made groupings, whole file)", "-"),
    ("m3-fits.json", "1.4-5.6 AU grid, 2023-2026 observations", "387"),
    ("m4-new.json", "0.55-50 AU grid, 2023-2026 observations", "2,555"),
    ("m4-old.json", "0.55-50 AU grid, 1995-2023 observations", "2,555"),
]


def is_guard_reason(reason: str) -> bool:
    return any(frag in reason for frag in GUARD_REASONS)


def row_for(report: Path) -> dict:
    fits = json.loads(report.read_text(encoding="utf-8"))["fits"]
    outcomes = fits.get("outcomes")
    if not outcomes:
        raise SystemExit(f"FATAL: {report} carries no per-fit outcomes[]")

    converged = [o for o in outcomes if o.get("converged")]
    # Meets our acceptance gate: nothing in gate_reasons came from the gate itself.
    meets_gate = [o for o in converged if all(is_guard_reason(r) for r in o["gate_reasons"])]
    guard_rejected = [o for o in meets_gate if o["gate_reasons"]]

    return {
        "converged": len(converged),
        "guard_rejected_all": fits["failed_subset_guard"],
        "meets_gate": len(meets_gate),
        "meets_gate_and_guard_rejected": len(guard_rejected),
        "passed_all_gates_reported": fits["passed_all_gates"],
        "converged_reported": fits["converged"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    print(f"| {'Associations came from':52} | Hyp. | Converged | Guard rej. | "
          f"Meet our gate | ...guard-rejected |")
    print(f"|{'-'*54}|-----:|----------:|-----------:|--------------:|----------------:|")

    ok = True
    for filename, label, hypotheses in ROWS:
        path = args.root / filename
        if not path.exists():
            print(f"  SKIP {filename}: not found", file=sys.stderr)
            ok = False
            continue
        r = row_for(path)
        pct_all = 100 * r["guard_rejected_all"] / r["converged"]
        pct_gate = 100 * r["meets_gate_and_guard_rejected"] / max(r["meets_gate"], 1)
        print(f"| {label:52} | {hypotheses:>4} | {r['converged']:9,} | "
              f"{r['guard_rejected_all']:5,} ({pct_all:4.1f}%) | {r['meets_gate']:13,} | "
              f"{r['meets_gate_and_guard_rejected']:6,} ({pct_gate:4.1f}%) |")

        # self-check: two independent code paths must agree
        implied = r["meets_gate"] - r["meets_gate_and_guard_rejected"]
        if implied != r["passed_all_gates_reported"]:
            print(f"  MISMATCH in {filename}: column5 - column6 = {implied:,} but the run "
                  f"recorded passed_all_gates = {r['passed_all_gates_reported']:,}",
                  file=sys.stderr)
            ok = False
        if r["converged"] != r["converged_reported"]:
            print(f"  MISMATCH in {filename}: {r['converged']:,} converged outcomes but the "
                  f"run recorded {r['converged_reported']:,}", file=sys.stderr)
            ok = False

    if ok:
        print("\nself-check passed: every row's (column 5 - column 6) equals the run's own "
              "passed_all_gates, and converged counts agree")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
