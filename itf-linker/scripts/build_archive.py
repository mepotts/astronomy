"""Assemble the deposit that makes the RNAAS note reproducible, and verify it.

WHY THIS EXISTS. The note's numbers live in run reports that are far too large for git --
109 MB for one of them -- so the repository carries the code and the prose but not the
evidence. A reader can read the three analysis scripts and cannot run them. This builds the
missing half: a single directory holding every input those scripts need, with checksums and
provenance, ready to attach to a release or a Zenodo deposit.

WHAT IS IN IT, AND WHAT IS DELIBERATELY NOT. Only what reproduces *the note*:

* the four run reports, gzipped (~7.5x; 157 MB becomes about 20);
* ``link-candidates.parquet``, needed to match links to the snapshot archive by member
  trkSub -- link ids are positional and must never be matched on (see ``link_key``);
* the committed snapshot delta chain, which is the ground truth in section 4.

Not included: the 10,330 Find_Orb chunk directories and the 44 MB old-slice link table.
Those reproduce **M5**, not the note, and would multiply the deposit by fifteen. They are a
separate deposit if one is ever wanted.

The layout mirrors the repository's, so the analysis scripts run against the unpacked
deposit with their default arguments and no edits.

    python scripts/build_archive.py --out ../astronomy-deposit
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path

README = """# Reproduction data for "A wrong link need not raise the residuals"

{n} files, {mb:.0f} MB. Everything needed to recompute every derived number in the note
*(subset fits and the limits of an RMS gate in archival minor-planet linking)*, and nothing
else.

## Unpack

    gunzip *.gz

## Reproduce

Clone `github.com/mepotts/astronomy`, install `itf-linker`, and run its scripts against this
directory. The layout mirrors the repository's, so the defaults work:

| command | reproduces |
|---|---|
| `python scripts/table1_guard_rates.py --root .` | Table 1, all six columns |
| `python scripts/guard_vs_confirmed.py --report m4-new.json --links data/link-candidates.parquet --snapshots data/snapshots` | section 4's ground-truth result |
| `python scripts/guard_threshold_curve.py --report m4-new.json --links data/link-candidates.parquet --snapshots data/snapshots` | the threshold sweep (working notes, not the note) |

Two of them self-check. `table1_guard_rates.py` verifies for every row that column 5 minus
column 6 equals the figure that run independently recorded as `passed_all_gates`.
`guard_threshold_curve.py` verifies that recomputing the guard at its shipped 0.8 threshold
returns the rejection count the run recorded.

## What is here

* **`m1-report.json`, `m3-fits.json`, `m4-new.json`, `m4-old.json`** -- the four run reports,
  one per row of Table 1. Their `fits.outcomes[]` arrays carry a record per fitted link, and
  that is what every derived number is computed from.
* **`data/link-candidates.parquet`** -- the M3 link table, needed to match links to the
  snapshot archive.
* **`data/snapshots/*/`** -- the committed snapshot delta chain: which observations left the
  Isolated Tracklet File between consecutive pulls. This is the ground truth in section 4,
  and it is independent of every gate, fit and catalogue query in the pipeline.
* **`data/snapshots/<newest>/desigs.parquet`** -- `SELECT DISTINCT desig` over the newest
  snapshot's key set. The key set itself is 178 MB and only this column is read, to
  establish which trkSubs still survive.

## What is not here, on purpose

The 10,330 Find_Orb chunk directories and the 44 MB older-slice link table. Those reproduce
milestone M5, not this note, and would multiply the deposit roughly fifteenfold.

## One trap

**Link identifiers (`lnk...`) are positional row numbers, not identifiers.** The same string
denotes different links in different tables -- across the two link tables in the source
repository, 13,618 ids appear in both and not one refers to the same link. Match links on
their member trkSubs. Runs after 2026-08-07 also carry a content-addressed `link_key`, which
is stable; these tables predate it.
"""


#: Run reports, gzipped into the deposit. These carry the per-fit ``outcomes[]`` records
#: that Table 1's columns 5 and 6, section 3's rates and section 4's ground truth all read.
REPORTS = ("m1-report.json", "m3-fits.json", "m4-new.json", "m4-old.json")

#: Copied verbatim: already compressed, and needed to key links by their members.
TABLES = ("data/link-candidates.parquet",)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []

    for name in REPORTS:
        src = args.root / name
        if not src.exists():
            print(f"FATAL: missing {src}", file=sys.stderr)
            return 1
        dst = out / f"{name}.gz"
        with src.open("rb") as fh, gzip.open(dst, "wb", compresslevel=9) as gz:
            shutil.copyfileobj(fh, gz)
        entries.append({"path": dst.name, "bytes": dst.stat().st_size,
                        "uncompressed_bytes": src.stat().st_size,
                        "sha256": sha256(dst), "gzipped": True})
        print(f"  {name}: {src.stat().st_size/1e6:.0f} MB -> {dst.stat().st_size/1e6:.1f} MB")

    for rel in TABLES:
        src = args.root / rel
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        entries.append({"path": rel, "bytes": dst.stat().st_size,
                        "sha256": sha256(dst), "gzipped": False})
        print(f"  {rel}: {dst.stat().st_size/1e6:.1f} MB")

    # One projection of the newest key set: SELECT DISTINCT desig. The survival half of the
    # ground-truth test needs to know which trkSubs are still in the ITF, and the key set
    # itself is 178 MB against 13 for the column that answers it. Without this the deposit
    # cannot run guard_vs_confirmed.py at all -- found by running it against the deposit.
    keysets = sorted(d for d in (args.root / "data/snapshots").iterdir()
                     if (d / "observations.parquet").exists())
    if keysets:
        import polars as pl
        newest = keysets[-1]
        dst = out / "data/snapshots" / newest.name / "desigs.parquet"
        dst.parent.mkdir(parents=True, exist_ok=True)
        (pl.scan_parquet(newest / "observations.parquet")
           .select("desig").unique().collect()
           .write_parquet(dst, compression="zstd"))
        entries.append({"path": str(dst.relative_to(out)).replace("\\", "/"),
                        "bytes": dst.stat().st_size, "sha256": sha256(dst), "gzipped": False,
                        "derivation": f"SELECT DISTINCT desig FROM {newest.name}/observations.parquet"})
        print(f"  key-set projection ({newest.name}): {dst.stat().st_size/1e6:.1f} MB")

    # The snapshot chain: manifests and deltas only. Full key sets are the rolling window and
    # are not part of the permanent record.
    snaps = sorted((args.root / "data/snapshots").iterdir())
    n_snaps = 0
    for snap in snaps:
        keep = [f for f in ("manifest.json", "delta.parquet") if (snap / f).exists()]
        if len(keep) != 2:
            continue
        for f in keep:
            src, dst = snap / f, out / "data/snapshots" / snap.name / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            entries.append({"path": str(dst.relative_to(out)).replace("\\", "/"),
                            "bytes": dst.stat().st_size, "sha256": sha256(dst),
                            "gzipped": False})
        n_snaps += 1
    print(f"  snapshot chain: {n_snaps} snapshots")

    total = sum(e["bytes"] for e in entries)
    manifest = {
        "title": "Reproduction data for 'A wrong link need not raise the residuals'",
        "reproduces": "itf-linker/docs/rnaas-subset-guard.md",
        "scripts": {
            "table1_guard_rates.py": "Table 1, all six columns, self-checked per row",
            "guard_vs_confirmed.py": "section 4: the guard against independently confirmed links",
            "guard_threshold_curve.py": "the used-fraction threshold sweep (notes only)",
        },
        "files": entries,
        "file_count": len(entries),
        "total_bytes": total,
        "note": (
            "Link identifiers (lnk...) are positional row numbers and differ between tables; "
            "match links on their member trkSubs, never on desig."
        ),
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "README.md").write_text(README.format(n=len(entries), mb=total / 1e6),
                                   encoding="utf-8")
    print(f"\n{len(entries)} files, {total/1e6:.1f} MB total -> {out}")
    print("wrote MANIFEST.json (sha256 for every file) and README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
