"""Re-score a completed fit run under both acceptance gates, without refitting.

WHY THIS EXISTS. Until 2026-08-07 this project applied one gate and described it as the
MPC's published criteria. It is not: it applies the 0.25" RMS ceiling unconditionally where
the MPC applies it only as one conjunct of an arc-length bullet, and it never implemented
the published ``e < 0.5`` condition. See :mod:`itf_linker.fit.gates`.

Every survivor count in M1-M5 is against the strict gate. Rather than revise those numbers,
the decision was to *report both* -- strict as the headline, published alongside. That needs
the published gate applied to the same population, and the population is large enough that
refitting is not an option: M5 was 4.4 hours of Find_Orb over 412,929 links.

It does not have to be. Find_Orb's ``total.json`` is kept per chunk, so every fit that ever
happened is still on disk and can be re-read. This script walks those chunk directories,
re-derives each :class:`FitResult`, joins the link table for the night count and arc length
the published rule needs, and applies both gates. Zero Find_Orb time.

SELF-CHECK, AND WHY IT DOES NOT PASS CLEANLY ON M5. The run recomputes ``converged`` and
``rms_le_0.25`` from disk and compares them to what the original run recorded (M5: 67,828
and 31,636). On M5 it recovers 408,457 of 412,929 links -- 98.92% -- with 66,090 converged.

That gap is **fully accounted for and is not a parsing bug**: 70 chunk ``total.json`` files
are truncated mid-object, ending in ``},`` with no closing braces. They are exactly the
chunks where Find_Orb hit ``orb_func.cpp:1038: Assertion 'fabs(jd1) < 1e+9' failed`` and
aborted (rc=134); the run's own ``fo_invocation_failures`` names them, and
:func:`load_previous_run` deliberately refuses partial files because a half-written one
"silently turns *not fitted* into *did not converge*". 70 chunks x 64 designations = 4,480,
against an observed 4,472.

So the absolute totals here are ~1.1% short of the original run, and the script says so.
**The gate-versus-gate comparison is unaffected**: both gates are applied to the identical
recovered population, row for row. Read the strict/published split as exact and the
absolute counts as a 98.9% sample.

    python scripts/rescore_gates.py --fits data/m5-fits --links data/m4-links-old.parquet \
        --expect-converged 67828 --expect-rms-ok 31636 --out data/m5-rescore.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import polars as pl

from itf_linker.fit.findorb import parse_total_json
from itf_linker.fit.gates import MAX_RMS_ARCSEC, mpc_published_gate, post_fit_gate


def load_link_meta(path: Path) -> dict[str, tuple[int, float]]:
    """desig -> (n_nights, arc_days). The arc the MPC's bullets measure is the tracklets'."""
    df = pl.read_parquet(path, columns=["desig", "n_nights", "arc_days"])
    return {
        d: (int(n), float(a))
        for d, n, a in zip(df["desig"], df["n_nights"], df["arc_days"], strict=True)
        if n is not None and a is not None
    }


def iter_total_json(fits_dir: Path):
    """Every chunk's ``total.json``, in a deterministic order."""
    yield from sorted(fits_dir.glob("*/chunk*/total.json"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fits", type=Path, required=True, help="root holding b*/chunk*/total.json")
    ap.add_argument("--links", type=Path, required=True, help="link table parquet")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expect-converged", type=int, default=None)
    ap.add_argument("--expect-rms-ok", type=int, default=None)
    args = ap.parse_args(argv)

    meta = load_link_meta(args.links)
    want = set(meta)
    print(f"link table: {len(meta):,} designations with n_nights and arc_days", flush=True)

    chunks = list(iter_total_json(args.fits))
    if not chunks:
        print(f"FATAL: no chunk total.json under {args.fits}", file=sys.stderr)
        return 1
    print(f"chunks on disk: {len(chunks):,}", flush=True)

    seen: set[str] = set()
    unparseable: list[str] = []
    n_fits = converged = rms_ok = 0
    strict_pass = published_pass = 0
    both = strict_only = published_only = neither = 0
    no_meta = 0
    high_e_strict_survivors = 0
    published_only_by_nights: Counter[int] = Counter()
    strict_survivor_nights: Counter[int] = Counter()

    for i, path in enumerate(chunks, 1):
        try:
            fits = parse_total_json(path.read_text(encoding="utf-8", errors="replace"), want)
        except (json.JSONDecodeError, OSError):
            # Truncated by an aborted fo. Recorded, never silently skipped: this is the
            # entire difference between the re-read and the original run.
            unparseable.append(f"{path.parent.parent.name}/{path.parent.name}")
            continue
        for desig, fit in fits.items():
            # Chunks are re-run on resume, so the same designation can appear twice.
            if desig in seen:
                continue
            seen.add(desig)
            n_fits += 1
            if fit.converged:
                converged += 1
                if fit.rms_residual is not None and fit.rms_residual <= MAX_RMS_ARCSEC:
                    rms_ok += 1

            info = meta.get(desig)
            if info is None:
                no_meta += 1
                continue
            n_nights, arc_days = info

            s = post_fit_gate(fit, n_nights=n_nights).passes
            p = mpc_published_gate(fit, n_nights=n_nights, arc_days=arc_days).passes
            strict_pass += s
            published_pass += p
            if s and p:
                both += 1
            elif s:
                strict_only += 1
            elif p:
                published_only += 1
                published_only_by_nights[n_nights] += 1
            else:
                neither += 1
            if s:
                strict_survivor_nights[n_nights] += 1
                if fit.e is not None and fit.e >= 0.5:
                    high_e_strict_survivors += 1

        if i % 500 == 0:
            print(f"  {i:,}/{len(chunks):,} chunks, {n_fits:,} fits", flush=True)

    report = {
        "fits_dir": str(args.fits),
        "links": str(args.links),
        "chunks_read": len(chunks),
        "chunks_unparseable": len(unparseable),
        "chunks_unparseable_names": unparseable,
        "fits_recovered": n_fits,
        "fits_without_link_metadata": no_meta,
        "converged": converged,
        "rms_le_0.25": rms_ok,
        "strict_gate_pass": strict_pass,
        "mpc_published_gate_pass": published_pass,
        "both": both,
        "strict_only": strict_only,
        "published_only": published_only,
        "neither": neither,
        "published_only_by_nights": dict(sorted(published_only_by_nights.items())),
        "strict_survivors_by_nights": dict(sorted(strict_survivor_nights.items())),
        "strict_survivors_with_e_ge_0.5": high_e_strict_survivors,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    exact = True
    for label, got, expected in (
        ("converged", converged, args.expect_converged),
        ("rms_le_0.25", rms_ok, args.expect_rms_ok),
    ):
        if expected is not None and got != expected:
            print(
                f"\nSHORT: {label} re-read from disk is {got:,}; the original run recorded "
                f"{expected:,} ({got - expected:+,}).",
                file=sys.stderr,
            )
            exact = False

    if exact:
        print("\nself-check passed: re-read reproduces the original run's funnel counts")
        return 0

    if not unparseable:
        print(
            "FATAL: the re-read is short but every chunk parsed. The shortfall is "
            "unexplained -- do not use the gate counts above.",
            file=sys.stderr,
        )
        return 1

    recovery = ""
    if args.expect_converged:
        recovery = f" ({100 * converged / args.expect_converged:.2f}% of converged fits)"
    print(
        f"\n{len(unparseable)} chunk total.json files are truncated and were skipped -- "
        f"Find_Orb aborted mid-write on them (see the run's fo_invocation_failures). That "
        f"is where the shortfall comes from, and those links have no recoverable fit on "
        f"disk.\n"
        f"  -> absolute counts above are a partial sample{recovery}, NOT the original "
        f"run's totals.\n"
        f"  -> the strict-vs-published split IS exact: both gates saw the identical "
        f"{n_fits:,} rows.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
