"""M11: diff two review-queue CSVs, so a versioned queue never swaps under a reviewer.

``out/review-queue.csv`` is the file Matthew is working through. Regenerating it in
place would silently move rows under a half-finished review -- and after a week of MPC
consumption a regenerated queue is genuinely different: rows leave because the tracklet
was taken, tier A shrinks when any member of a combined object is consumed, and every
rank below a departure shifts by one. So M11 writes a **new** file and this script says
exactly what changed between them.

Rows are identified by ``link_keys`` (content-addressed, stable across runs -- HANDOFF
section 4: ``lnk...`` ids are row numbers and must never be joined on) plus the object,
because one object can appear in several rows.

Writes a JSON diff. Nothing is overwritten.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("tier") == "SPOTCHECK":
                continue
            rows[(r["object"], r["link_keys"])] = r
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--refresh", type=Path, required=True,
                    help="the refresh that produced --new; supplies WHY a row left")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    old, new = load(args.old), load(args.new)
    refresh = json.loads(args.refresh.read_text(encoding="utf-8"))
    status = {
        (r["trksub"], r["obscode"], int(r["night"])): r["itf_status"]
        for r in refresh["rows"]
    }
    agreement = {
        (r["trksub"], r["obscode"], int(r["night"])): r["agreement"]
        for r in refresh["consumed_rows"]
    }

    def why_gone(row: dict[str, Any]) -> dict[str, Any]:
        keys = [k.strip() for k in (row.get("tracklets") or "").split(";") if k.strip()]
        parts = []
        for k in keys:
            # the queue writes tracklets as "<trksub>@<obscode>/n<night>"
            try:
                trk, rest = k.split("@", 1)
                obs, night = rest.split("/", 1)
                key = (trk, obs, int(night.lstrip("n")))
            except ValueError:
                continue
            parts.append({"tracklet": k, "itf_status": status.get(key, "?"),
                          "agreement": agreement.get(key)})
        return {"members": parts,
                "consumed_members": sum(1 for p in parts
                                        if p["itf_status"] != "STILL_LIVE")}

    left = []
    for k, r in old.items():
        if k not in new:
            left.append({"object": r["object"], "tier": r["tier"],
                         "old_rank": int(r["rank"]),
                         "arc_extension_days": r["arc_extension_days"],
                         **why_gone(r)})
    entered = [{"object": r["object"], "tier": r["tier"], "new_rank": int(r["rank"]),
                "arc_extension_days": r["arc_extension_days"]}
               for k, r in new.items() if k not in old]
    tier_changed = []
    rank_moved = []
    for k, r in new.items():
        o = old.get(k)
        if not o:
            continue
        if o["tier"] != r["tier"]:
            tier_changed.append({"object": r["object"], "from": o["tier"],
                                 "to": r["tier"], "old_rank": int(o["rank"]),
                                 "new_rank": int(r["rank"])})
        d = int(r["rank"]) - int(o["rank"])
        if d:
            rank_moved.append(d)

    doc = {
        "old": str(args.old),
        "new": str(args.new),
        "old_rows": len(old),
        "new_rows": len(new),
        "left": sorted(left, key=lambda e: e["old_rank"]),
        "n_left": len(left),
        "entered": sorted(entered, key=lambda e: e["new_rank"]),
        "n_entered": len(entered),
        "tier_changed": sorted(tier_changed, key=lambda e: e["new_rank"]),
        "n_tier_changed": len(tier_changed),
        "n_rank_moved": len(rank_moved),
        "rank_shift_min_max": [min(rank_moved), max(rank_moved)] if rank_moved else None,
        "unchanged_rows": len(new) - len(entered) - len(tier_changed) - len(
            [d for d in rank_moved if d]
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in doc.items()
                      if k not in ("left", "entered", "tier_changed")}, indent=2))
    print(f"\nrows that left ({len(left)}):")
    for e in left[:40]:
        print(f"  rank {e['old_rank']:4d} tier {e['tier']} {e['object']:14s} "
              f"consumed {e['consumed_members']}/{len(e['members'])} members "
              + "; ".join(f"{m['tracklet']} {m['itf_status']}"
                          + (f" {m['agreement']}" if m["agreement"] else "")
                          for m in e["members"]))
    if len(left) > 40:
        print(f"  ... and {len(left) - 40} more (see the JSON)")
    print(f"\nrows that entered ({len(entered)}):")
    for e in entered[:20]:
        print(f"  rank {e['new_rank']:4d} tier {e['tier']} {e['object']}")
    print(f"\ntier changes ({len(tier_changed)}):")
    for e in tier_changed[:40]:
        print(f"  {e['object']:14s} {e['from']} -> {e['to']} "
              f"(rank {e['old_rank']} -> {e['new_rank']})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
