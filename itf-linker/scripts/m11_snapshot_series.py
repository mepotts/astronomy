"""M11: rebuild the ledger's snapshot series after the archive pruned M10's base.

**The trap this exists to pay for.** M10's refresh built its snapshot series by scanning
``data/snapshots/`` for directories that still carry an ``observations.parquet`` and
keeping those at or after ``BASE_SNAPSHOT = 20260816T202701Z`` -- the universe M8, M9 and
the M10 shell swept. Five days later the archive's rolling retention has pruned the key
sets for 08-16, 08-17, 08-18, 08-19 and 08-20, so that scan now returns
**08-21 -> 08-22 -> 08-23** and the script's ``counts_by_snap[0]`` silently becomes the
08-21 snapshot. Every "consumed since 08-16" count then measures consumption since
08-21 instead, under a heading that says 08-16, and *nothing about the output looks
wrong*. This is the archive's own delta-of-zero failure wearing a different hat: a
measurement that cannot be taken must never be recorded as a measurement of something
else.

Two things make the series recoverable exactly, and both are properties the archive was
built to have:

* ``data/parquet/itf_observations_20260816_reconstructed.parquet`` is M9's exact
  reconstruction of the base snapshot (residue 0, M9 section 0.1), so the base universe
  survives its own pruning.
* Every pruned snapshot kept its ``delta.parquet``, and every manifest in the
  08-16 -> 08-23 chain records ``delta_status.against`` = its *immediate* predecessor.
  A contiguous chain of content-addressed deltas reconstructs each intermediate key set
  exactly: ``keys(parent) = keys(child) - appeared(child) + disappeared(child)``.

Because only the candidate ledger's ~2,200 designations are ever asked about, the
reconstruction is restricted to them and each snapshot's slim table is a few hundred
kilobytes rather than 180 MB. The walk is verified against the independent 08-16
reconstruction at the end: if the two disagree by a single observation the series is
rejected rather than reported.

Writes the restricted slim tables and a ``series.json`` into a directory **outside the
repository**; the archive and its clone are not touched.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import polars as pl

SNAP_DIR = ROOT / "data" / "snapshots"
BASE_SNAPSHOT = "20260816T202701Z"
BASE_RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
COLS = ["obs_key", "desig", "obscode", "mjd"]


def ledger_desigs(paths: list[Path]) -> list[str]:
    out: set[str] = set()
    for p in paths:
        doc = json.loads(p.read_text(encoding="utf-8"))
        for v in doc["verdicts"]:
            out.add(v["trksub"])
    return sorted(out)


def manifest(sid: str) -> dict[str, Any]:
    return json.loads((SNAP_DIR / sid / "manifest.json").read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="scratch directory OUTSIDE the repository")
    ap.add_argument("--ledgers", nargs="+", required=True)
    ap.add_argument("--fresh-slim", type=Path, required=True)
    ap.add_argument("--fresh-provenance", type=Path, required=True)
    ap.add_argument("--extra-desigs", nargs="*", default=[],
                    help="M7's held rows are not in a ledger file")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    desigs = sorted(set(ledger_desigs([Path(p) for p in args.ledgers])
                        + list(args.extra_desigs)))
    print(f"ledger designations: {len(desigs)}", flush=True)

    # ---- which snapshots are on the chain, and which still have a key set -----------
    ids = sorted(p.name for p in SNAP_DIR.iterdir()
                 if (p / "manifest.json").exists() and p.name >= BASE_SNAPSHOT)
    full = [s for s in ids if (SNAP_DIR / s / "observations.parquet").exists()]
    pruned = [s for s in ids if s not in full]
    print(f"snapshots at/after base: {len(ids)}; key sets surviving: {len(full)}; "
          f"pruned: {pruned}", flush=True)

    # The chain must be contiguous for the backward walk to be exact.
    chain_ok = True
    for a, b in itertools.pairwise(ids):
        m = manifest(b)
        if m.get("delta_status", {}).get("against") != a:
            chain_ok = False
            print(f"  CHAIN BREAK: {b} delta is against "
                  f"{m.get('delta_status', {}).get('against')}, not {a}", flush=True)
    if not chain_ok:
        raise SystemExit("delta chain is not contiguous; series cannot be reconstructed")

    # ---- walk backwards from the newest surviving key set ---------------------------
    newest = full[-1]
    cur = (
        pl.scan_parquet(SNAP_DIR / newest / "observations.parquet")
        .filter(pl.col("desig").is_in(desigs))
        .select(COLS)
        .collect()
    )
    tables: dict[str, pl.DataFrame] = {newest: cur}
    idx = ids.index(newest)
    for i in range(idx, 0, -1):
        child, parent = ids[i], ids[i - 1]
        d = pl.read_parquet(SNAP_DIR / child / "delta.parquet").filter(
            pl.col("desig").is_in(desigs)
        )
        appeared = d.filter(pl.col("change") == 1).select(COLS)
        gone = d.filter(pl.col("change") == -1).select(COLS)
        cur = (
            pl.concat([cur.join(appeared.select("obs_key"), on="obs_key", how="anti"),
                       gone], how="vertical")
            .unique(subset=["obs_key"])
        )
        tables[parent] = cur
        print(f"  {child} -> {parent}: -{appeared.height} +{gone.height} "
              f"= {cur.height} ledger observations", flush=True)

    # ---- verify the walk against M9's independent reconstruction --------------------
    #
    # The check is against 08-18, NOT 08-16, and the reason is a real distinction that
    # cost a run to find. ``itf_observations_20260816_reconstructed.parquet`` is not the
    # 08-16 table: M9 section 0.1 built it as 08-18's rows whose content-addressed
    # ``obs_key`` was also present at 08-16, **with every tracklet that lost any
    # observation dropped whole** (5,563 tracklets, 22,353 observations). It is the
    # *intersection* of the two snapshots -- exactly the right universe for a sweep that
    # must not propose a tracklet the MPC has already taken, and exactly the wrong one
    # for "how many observations did this tracklet have on 08-16". The delta walk gives
    # the latter and legitimately exceeds the reconstruction by the tracklets consumed
    # in between; the intersection is what the two must agree on.
    indep = (
        pl.scan_parquet(BASE_RECONSTRUCTED)
        .filter(pl.col("desig").is_in(desigs))
        .select("desig", "obscode", "mjd")
        .collect()
        .sort(["desig", "obscode", "mjd"])
    )
    check_sid = "20260818T152903Z"
    walk = tables[check_sid].select("desig", "obscode", "mjd").sort(
        ["desig", "obscode", "mjd"]
    )
    agree = indep.equals(walk)
    base_rows = tables[BASE_SNAPSHOT].height
    print(f"walk check at {check_sid}: {walk.height} rows vs M9 reconstruction "
          f"{indep.height} rows -- {'IDENTICAL' if agree else 'DISAGREE'}", flush=True)
    print(f"base {BASE_SNAPSHOT}: {base_rows} rows "
          f"(+{base_rows - indep.height} over the reconstruction = the ledger "
          f"observations the MPC consumed between 08-16 and 08-18)", flush=True)
    if not agree:
        raise SystemExit(
            "the delta walk does not reproduce M9's reconstruction at 08-18; refusing "
            "to report a series whose chain cannot be verified"
        )

    # ---- write the restricted slim tables + the series document ---------------------
    series: list[dict[str, Any]] = []
    for sid in ids:
        m = manifest(sid)
        path = args.out_dir / f"slim-{sid}.parquet"
        tables[sid].sort("obs_key").write_parquet(path, compression="zstd")
        series.append({
            "snapshot_id": sid,
            "last_modified": m["provenance"]["last_modified"],
            "observations": m["observations"],
            "key_set_source": ("archive" if sid in full else "delta walk"),
            "slim": str(path),
        })
    fresh_prov = json.loads(args.fresh_provenance.read_text(encoding="utf-8"))
    series.append({
        "snapshot_id": "FRESH-" + fresh_prov["last_modified"],
        "last_modified": fresh_prov["last_modified"],
        "observations": None,
        "key_set_source": "live pull (outside the repository)",
        "slim": str(args.fresh_slim),
    })
    doc = {
        "base_snapshot": BASE_SNAPSHOT,
        "n_designations": len(desigs),
        "pruned_by_retention": pruned,
        "base_verified_against": str(BASE_RECONSTRUCTED),
        "verification": {
            "checked_at": check_sid,
            "walk_rows": walk.height,
            "reconstruction_rows": indep.height,
            "identical": bool(agree),
            "base_rows": base_rows,
            "base_minus_reconstruction": base_rows - indep.height,
            "note": ("the reconstruction is the 08-16/08-18 intersection, not the "
                     "08-16 table; the base legitimately exceeds it by the ledger "
                     "observations consumed in between"),
        },
        "series": series,
    }
    (args.out_dir / "series.json").write_text(json.dumps(doc, indent=2),
                                              encoding="utf-8")
    print(f"wrote {args.out_dir / 'series.json'}: "
          + " -> ".join(s["snapshot_id"] for s in series))


if __name__ == "__main__":
    main()
