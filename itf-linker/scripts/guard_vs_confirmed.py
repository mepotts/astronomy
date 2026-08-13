"""Measure the gates against links the world independently confirmed.

WHY THIS EXISTS. ``HANDOFF.md`` names the sharpest weakness in this project's publishable
finding: *"The guard's false-rejection rate is measured nowhere. '84.4% rejected' is not
'84.4% were wrong'."* The supplementary subset guard rejects most of what converges, and
until now there was no ground truth to check it against -- every other number in the project
comes from the pipeline judging its own output.

The snapshot archive supplies that ground truth. The ITF holds observations no survey
pipeline could link; when somebody links them, they leave the file. A link of ours whose
every member has since departed the ITF entirely is one **somebody else independently
agreed with**, established without any orbit fit, catalogue query or gate of ours.

So: take those links, find them in a completed fit run, and ask what each gate did to them.
A gate that rejects a confirmed link is rejecting something real.

Matching is on the **set of member trkSubs**, never on ``desig``: link ids are positional
indices into whichever link table produced them (audit C4), so the same ``lnk...`` string
means different things in different runs and comparing them silently answers the wrong
question.

    python scripts/guard_vs_confirmed.py --report m4-new.json \
        --links data/link-candidates.parquet --snapshots data/snapshots
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import polars as pl

from itf_linker.fit.findorb import FitResult
from itf_linker.fit.gates import mpc_published_gate, post_fit_gate

#: Reason fragments emitted by the supplementary subset guard, as opposed to the acceptance
#: gate. Kept here rather than imported because the guard writes prose, not codes.
GUARD_REASONS = (
    "fit used only",
    "observations actually used span",
    "observation counts unavailable",
)


def confirmed_link_keys(snapshots: Path, links: Path) -> set[frozenset[str]]:
    """Links every member of which has left the ITF with nothing left behind.

    The strict form of the test: a member counts as departed only when **no** observation of
    it survives in the newest key set, not merely when one observation left.
    """
    deltas = [
        pl.read_parquet(d / "delta.parquet").filter(pl.col("change") == -1)
        for d in sorted(snapshots.iterdir())
        if (d / "delta.parquet").exists()
    ]
    deltas = [d for d in deltas if len(d)]
    if not deltas:
        return set()
    departed = set(pl.concat(deltas)["desig"].unique().to_list())

    # A full key set is 178 MB and is only kept for the newest few snapshots, so a
    # distribution ships ``desigs.parquet`` instead -- SELECT DISTINCT desig over the same
    # file, which is all the survival test reads. Prefer the real thing when it is present.
    keysets = sorted(d for d in snapshots.iterdir() if (d / "observations.parquet").exists())
    projections = sorted(d for d in snapshots.iterdir() if (d / "desigs.parquet").exists())
    if keysets:
        source = keysets[-1] / "observations.parquet"
    elif projections:
        source = projections[-1] / "desigs.parquet"
    else:
        raise SystemExit(
            "FATAL: no snapshot retains a key set or a desigs.parquet projection; "
            "the survival test cannot run"
        )
    surviving = set(pl.scan_parquet(source).select("desig").collect()["desig"].unique().to_list())
    gone = departed - surviving

    table = pl.read_parquet(links, columns=["source_desigs", "link_pass"]).filter(
        pl.col("link_pass")
    )
    return {
        frozenset(r["source_desigs"])
        for r in table.iter_rows(named=True)
        if (m := set(r["source_desigs"])) and m <= gone
    }


def _fit(o: dict) -> FitResult:
    return FitResult(
        desig=o["desig"],
        converged=bool(o.get("converged")),
        status=o.get("status") or "converged",
        rms_residual=o.get("rms_residual"),
        sigma_a=o.get("sigma_a"),
        sigma_q=o.get("sigma_q"),
        sigma_i=o.get("sigma_i"),
        sigma_e=o.get("sigma_e"),
        e=o.get("e"),
        a=o.get("a"),
        q=o.get("q"),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True, help="a fit report with outcomes[]")
    ap.add_argument("--links", type=Path, required=True)
    ap.add_argument("--snapshots", type=Path, default=Path("data/snapshots"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    confirmed = confirmed_link_keys(args.snapshots, args.links)
    print(f"independently confirmed links: {len(confirmed)}", flush=True)

    outcomes = json.loads(args.report.read_text(encoding="utf-8"))["fits"].get("outcomes")
    if not outcomes:
        raise SystemExit(f"FATAL: {args.report} carries no per-link outcomes[]")

    rows = [o for o in outcomes if frozenset(o["source_desigs"]) in confirmed]
    matched = {frozenset(o["source_desigs"]) for o in rows}
    if not rows:
        print(
            "No confirmed link appears in this run. The usual cause is a slice mismatch --\n"
            "the confirmed links and the report must cover the same MJD range.",
            file=sys.stderr,
        )
        return 1

    strict = published = guard_only = 0
    reasons: Counter[str] = Counter()
    for o in rows:
        fit = _fit(o)
        nights = o.get("n_nights")
        arc = o.get("prefit_arc_days") or o.get("arc_days")
        strict += post_fit_gate(fit, n_nights=nights).passes
        published += mpc_published_gate(fit, n_nights=nights, arc_days=arc).passes
        if not o["gate_passes"]:
            rs = o["gate_reasons"]
            hits = [r for r in rs if any(s in r for s in GUARD_REASONS)]
            if rs and len(hits) == len(rs):
                guard_only += 1
            for r in rs:
                reasons[r.split("(")[0].strip()[:60]] += 1

    report = {
        "confirmed_links": len(confirmed),
        "confirmed_links_in_report": len(matched),
        "fitted_rows": len(rows),
        "converged": sum(1 for o in rows if o.get("converged")),
        "passed_every_gate_in_the_run": sum(1 for o in rows if o["gate_passes"]),
        "kept_by_our_post_fit_gate": strict,
        "kept_by_the_mpc_published_rule": published,
        "rejected_by_the_subset_guard_alone": guard_only,
        "rejection_reasons": dict(reasons.most_common()),
    }
    print(json.dumps(report, indent=2))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        f"\nGuard false rejections against ground truth: {guard_only}."
        f"\nOur gate keeps {strict} of {len(rows)}; the MPC's published rule keeps {published}.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
