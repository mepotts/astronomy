"""M12: the daily archive read as a series, not as a pile of snapshots.

Twenty-six days of ITF snapshots have accumulated since 2026-07-29 and every milestone so
far has used them one pair at a time -- "what did the MPC consume between M8's pull and
M9's". Nobody has asked what the *series* says. It says the file is draining: 168,078
observations left and 38,319 arrived, a ratio of 4.4 to 1, and the drain is not uniform.

**The confound this pays for first.** ``obs_key`` folds ``desig`` into the hash
(``snapshot.py::obs_key``), so an observation the MPC merely *re-labels* -- same station,
same instant, same position, new trksub -- vanishes under its old key and reappears under
a new one. Read naively that is one departure and one arrival, and a file that only
churned its designations would look exactly like a file being drained. The test is cheap
and it has to come before every other number here: match each delta's departed rows
against its arrived rows on ``(obscode, mjd)``, ignoring ``desig``. Section 1 reports the
answer (0.1%), which is why the rest of this script is worth running.

**Why a backward walk.** Only six full key sets survive on disk -- the archive prunes them
to a rolling window of four release assets -- but every delta is committed forever, and
the chain is invertible exactly:

    keys(parent) = keys(child) - appeared(child) + disappeared(child)

That identity is M11's (``m11_snapshot_series.py``), used there over the ~2,200 ledger
designations. Here it runs over the whole file, which is the only way to ask what
fraction of a *designation* left at once.

**Segments, because the chain is broken.** 2026-08-13's manifest carries
``parent_snapshot: null`` -- the key set it needed had been pruned before the diff ran, so
its delta could not be computed and is recorded as absent rather than as a zero. A walk
cannot cross that. The series is therefore two contiguous segments, each anchored at its
own newest surviving key set and each verified against every *other* surviving key set it
covers. A segment that fails its check is not reported.

Writes ``m12-series.json`` to a path given on the command line. Reads only; the archive
and its clone are never touched.
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

import polars as pl

# Set from --snapshots. The development checkout is not necessarily the right directory:
# the daily task writes key sets there but commits manifests and deltas from a separate
# archive clone, so neither tree alone holds the whole series. Point this at a merged
# read-only view (all manifests and deltas, plus whatever key sets still survive).
SNAP_DIR = ROOT / "data" / "snapshots"
COLS = ["obs_key", "desig", "obscode", "mjd"]

# M9's independent reconstruction of the 08-16 universe. NOT the 08-16 key set: it is
# 08-18's rows whose obs_key was also present at 08-16, with every tracklet that lost any
# observation dropped whole (M9 s0.1). The walk must reproduce that *intersection*, which
# is a stronger check than comparing row counts -- see verify_against_reconstruction.
RECONSTRUCTION = ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
RECON_AT = "20260818T152903Z"
RECON_BASE = "20260816T202701Z"


def manifest(sid: str) -> dict[str, Any]:
    return json.loads((SNAP_DIR / sid / "manifest.json").read_text(encoding="utf-8"))


def snapshot_ids() -> list[str]:
    return sorted(p.name for p in SNAP_DIR.iterdir() if (p / "manifest.json").exists())


def segments(ids: list[str]) -> list[list[str]]:
    """Split the snapshot list wherever a delta is not against its immediate predecessor.

    A segment is a maximal run over which the backward walk is exact. Baselines and
    uncomputable deltas both start a new one.
    """
    out: list[list[str]] = []
    cur: list[str] = []
    for a, b in itertools.pairwise([None, *ids]):
        if a is None:
            cur = [b]
            continue
        m = manifest(b)
        st = m.get("delta_status")
        # Manifests written before 2026-08-06 have no delta_status; for those the delta
        # was computed whenever the snapshot is not a baseline.
        if st is None:
            ok = not m.get("is_baseline", False) and m.get("parent_snapshot") == a
        else:
            ok = bool(st.get("computed")) and st.get("against") == a
        if ok:
            cur.append(b)
        else:
            out.append(cur)
            cur = [b]
    out.append(cur)
    return [s for s in out if len(s) > 1]


def keyset_on_disk(sid: str) -> Path | None:
    p = SNAP_DIR / sid / "observations.parquet"
    return p if p.exists() else None


def delta(sid: str) -> pl.DataFrame:
    return pl.read_parquet(SNAP_DIR / sid / "delta.parquet")


def redesignations(d: pl.DataFrame) -> int:
    """Departed rows whose (obscode, mjd) also arrives in the same delta -- a re-label."""
    gone = d.filter(pl.col("change") < 0)
    came = d.filter(pl.col("change") > 0)
    if gone.is_empty() or came.is_empty():
        return 0
    key = ["obscode", "mjd"]
    return gone.join(came.select(key).unique(), on=key, how="semi").height


def step_stats(parent_keys: pl.DataFrame, d: pl.DataFrame) -> dict[str, Any]:
    """Everything measurable about one transition, given the parent's full key set."""
    gone = d.filter(pl.col("change") < 0)
    came = d.filter(pl.col("change") > 0)
    stats: dict[str, Any] = {
        "appeared": came.height,
        "disappeared": gone.height,
        "redesignated": redesignations(d),
    }
    if gone.is_empty():
        return stats

    had = parent_keys.group_by("desig").len().rename({"len": "had"})
    lost = gone.group_by("desig").len().rename({"len": "lost"})
    j = lost.join(had, on="desig", how="left").with_columns(
        (pl.col("had") - pl.col("lost")).alias("kept")
    )
    whole = j.filter(pl.col("kept") == 0)
    part = j.filter(pl.col("kept") > 0)
    stats |= {
        "desigs_losing_observations": j.height,
        "desigs_gone_whole": whole.height,
        "desigs_gone_partial": part.height,
        "obs_from_whole_desigs": int(whole["lost"].sum()),
        "obs_from_partial_desigs": int(part["lost"].sum()),
        "whole_desig_size_median": float(whole["had"].median()) if whole.height else None,
        # A designation that loses observations but is absent from the parent key set
        # would mean the walk is wrong; count it rather than reporting a silent null.
        "unmatched_desigs": int(j["had"].null_count()),
        "departed_mjd_median": float(gone["mjd"].median()),
        "departed_mjd_p10": float(gone["mjd"].quantile(0.10)),
        "departed_mjd_p90": float(gone["mjd"].quantile(0.90)),
        "departed_obscodes": gone["obscode"].n_unique(),
    }
    return stats


def distinct_keys(frame: pl.DataFrame) -> pl.DataFrame:
    """The sorted distinct obs_key column -- the only thing a delta chain can preserve.

    The ITF ships ~1,130 exactly duplicated records (same designation, station, instant
    and position), which every manifest reports as ``duplicate_observations``. A delta is
    an anti-join on ``obs_key``, so the chain transports the *distinct key set* and a walk
    can never reproduce a raw row count. Comparing a walk against a file's row count is
    therefore guaranteed to fail by exactly the duplicate count, which is what it did the
    first time this ran. Both sides of every check are reduced through here.
    """
    return frame.select("obs_key").unique().sort("obs_key")


def verify_against_reconstruction(tables: dict[str, pl.DataFrame]) -> dict[str, Any] | None:
    """Reproduce M9's 08-16 reconstruction from the walk, exactly.

    The reconstruction is *not* the 08-16 key set and it is not "08-18 minus designations
    that lost something" either -- that reading is off by 98 keys and was the second thing
    this check caught. ``m9_reconstruct_snapshot.py`` builds it as 08-18's rows whose
    ``obs_key`` is also in the 08-16 key set, with every **tracklet** that lost any
    observation dropped whole, where a tracklet is ``(desig, obscode, night)`` under
    ``load_tracklets``' night definition (local night from the observatory's signed
    longitude) and unnamed rows (``desig == ""``) pass through untouched. A designation
    can hold several tracklets and lose only one of them, which is exactly the 98.

    Both key sets come from the walk, so agreement tests the walk end to end over the
    whole file. The reconstruction carries astrometry but no key, so its keys are
    recomputed with the same vectorised function the archive uses.
    """
    if RECON_AT not in tables or RECON_BASE not in tables or not RECONSTRUCTION.exists():
        return None
    from itf_linker.ingest.fetch import fetch_obscodes
    from itf_linker.snapshot import obs_keys

    sys.path.insert(0, str(ROOT / "scripts"))
    from m9_reconstruct_snapshot import with_night

    k16, k18 = tables[RECON_BASE], tables[RECON_AT]
    lon = fetch_obscodes()
    lon_df = pl.DataFrame({
        "obscode": list(lon.keys()),
        "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()],
    })
    flagged = k16.join(
        k18.select("obs_key").with_columns(pl.lit(True).alias("survives")),
        on="obs_key", how="left",
    ).with_columns(pl.col("survives").fill_null(False))
    per_trk = (
        with_night(flagged.lazy().filter(pl.col("desig") != ""), lon_df)
        .group_by("desig", "obscode", "night")
        .agg(pl.len().alias("n"), pl.col("survives").sum().alias("n_survive"))
        .collect()
    )
    dropped = per_trk.filter(pl.col("n_survive") < pl.col("n")).select(
        "desig", "obscode", "night"
    )
    kept = k18.join(k16.select("obs_key"), on="obs_key", how="semi")
    kept_named = (
        with_night(kept.lazy().filter(pl.col("desig") != ""), lon_df)
        .collect()
        .join(dropped, on=["desig", "obscode", "night"], how="anti")
    )
    rebuilt = pl.concat(
        [kept_named.select("obs_key"), kept.filter(pl.col("desig") == "").select("obs_key")],
        how="vertical",
    )
    raw = pl.read_parquet(
        RECONSTRUCTION, columns=["desig", "obscode", "mjd", "ra_deg", "dec_deg"]
    )
    indep = raw.with_columns(pl.Series("obs_key", obs_keys(raw), dtype=pl.UInt64))
    a, b = distinct_keys(rebuilt), distinct_keys(indep)
    return {
        "check": "M9 08-16 reconstruction",
        "tracklets_dropped": dropped.height,
        "walk_distinct_keys": a.height,
        "independent_distinct_keys": b.height,
        "independent_rows": indep.height,
        "identical": bool(a.equals(b)),
    }


def walk(segment: list[str]) -> tuple[dict[str, pl.DataFrame], list[dict[str, Any]]] | None:
    """Backward walk over one contiguous segment, anchored at its newest key set.

    Returns None when the segment has no surviving key set to anchor on. That is a real
    and permanent state -- the release assets are pruned to a rolling window of four, so
    the oldest segments lose their anchor and can never get it back -- and it must read as
    "not measurable" rather than as a failure or, worse, as a zero.
    """
    have = [s for s in segment if keyset_on_disk(s)]
    if not have:
        return None
    anchor = have[-1]
    raw = pl.read_parquet(keyset_on_disk(anchor), columns=COLS)
    # Collapse the file's duplicate records once, here, so every table in the walk is a
    # key set and the invariant is not established silently by the first unique() below.
    cur = raw.unique(subset=["obs_key"])
    print(f"    anchor {anchor}: {raw.height:,} rows -> {cur.height:,} distinct keys "
          f"({raw.height - cur.height:,} duplicate records)", flush=True)
    tables = {anchor: cur}
    checks: list[dict[str, Any]] = []
    for i in range(segment.index(anchor), 0, -1):
        child, parent = segment[i], segment[i - 1]
        d = delta(child)
        cur = pl.concat(
            [
                cur.join(d.filter(pl.col("change") > 0).select("obs_key"),
                         on="obs_key", how="anti"),
                d.filter(pl.col("change") < 0).select(COLS),
            ],
            how="vertical",
        ).unique(subset=["obs_key"])
        tables[parent] = cur
        # Every other key set that survived on disk is an independent check on the walk.
        if keyset_on_disk(parent):
            disk = pl.read_parquet(keyset_on_disk(parent), columns=["obs_key"])
            a, b = distinct_keys(cur), distinct_keys(disk)
            identical = bool(a.equals(b))
            checks.append({
                "check": f"on-disk key set {parent}",
                "walk_distinct_keys": a.height,
                "independent_distinct_keys": b.height,
                "independent_rows": disk.height,
                "identical": identical,
            })
            print(f"    check {parent}: walk {a.height:,} vs disk {b.height:,} distinct "
                  f"({disk.height:,} rows) -- "
                  f"{'IDENTICAL' if identical else 'DISAGREE'}", flush=True)
    return tables, checks


def main() -> None:
    global SNAP_DIR
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--snapshots", type=Path, default=SNAP_DIR,
                    help="snapshot directory; see the SNAP_DIR comment")
    args = ap.parse_args()
    SNAP_DIR = args.snapshots

    ids = snapshot_ids()
    segs = segments(ids)
    print(f"{len(ids)} snapshots; {len(segs)} contiguous segment(s)", flush=True)
    for s in segs:
        print(f"  {s[0]} .. {s[-1]}  ({len(s)} snapshots, "
              f"{sum(1 for x in s if keyset_on_disk(x))} key sets on disk)", flush=True)

    doc: dict[str, Any] = {"snapshots": len(ids), "segments": [], "verification": []}
    for seg in segs:
        print(f"\nsegment {seg[0]} .. {seg[-1]}", flush=True)
        walked = walk(seg)
        if walked is None:
            print("    no surviving key set to anchor on -- NOT MEASURABLE", flush=True)
            doc["segments"].append({
                "first": seg[0], "last": seg[-1], "steps": [],
                "unanchored": True,
                "reason": "no key set survives in this segment; the rolling window "
                          "pruned them and they cannot be recovered",
            })
            continue
        tables, checks = walked
        doc["verification"].extend(checks)
        rec = verify_against_reconstruction(tables)
        if rec:
            doc["verification"].append(rec)
            print(f"    check {rec['check']}: walk {rec['walk_distinct_keys']:,} vs "
                  f"independent {rec['independent_distinct_keys']:,} distinct "
                  f"({rec['independent_rows']:,} rows) -- "
                  f"{'IDENTICAL' if rec['identical'] else 'DISAGREE'}", flush=True)

        steps = []
        for parent, child in itertools.pairwise(seg):
            st = step_stats(tables[parent], delta(child))
            m = manifest(child)
            st["snapshot"] = child
            st["against"] = parent
            st["manifest_appeared"] = (m.get("delta") or {}).get("appeared")
            st["manifest_disappeared"] = (m.get("delta") or {}).get("disappeared")
            st["agrees_with_manifest"] = (
                st["appeared"] == st["manifest_appeared"]
                and st["disappeared"] == st["manifest_disappeared"]
            )
            st["observations_after"] = m["observations"]
            st["designations_after"] = m["designations"]
            st["designations_3plus_nights_after"] = m["designations_3plus_nights"]
            st["source_last_modified"] = m["provenance"].get("last_modified")
            st["source_bytes"] = m["provenance"].get("size_bytes")
            steps.append(st)
            print(f"  {child}: -{st['disappeared']:,} +{st['appeared']:,}  "
                  f"whole={st.get('desigs_gone_whole', 0):,} "
                  f"partial={st.get('desigs_gone_partial', 0):,}", flush=True)
        doc["segments"].append({"first": seg[0], "last": seg[-1], "steps": steps})

    bad = [c for c in doc["verification"] if not c["identical"]]
    doc["verification_passed"] = not bad
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}", flush=True)
    if bad:
        raise SystemExit(f"{len(bad)} verification check(s) FAILED; series not trustworthy")
    print(f"all {len(doc['verification'])} verification checks identical", flush=True)


if __name__ == "__main__":
    main()
