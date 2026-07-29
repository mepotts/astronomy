"""Stream the gzipped ITF through the 80-column parser into a typed Parquet file.

The ITF is ~9.4M rows / ~750 MB uncompressed. Rather than materialise all of it as
Python strings, this reads the gzip in batches, hands each batch to the vectorised
:func:`itf_linker.mpc80.parse_frame`, and appends a Parquet row group per batch.
Peak memory stays proportional to ``batch_size``, not to the file.
"""

from __future__ import annotations

import gzip
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq

from .. import config
from ..mpc80 import OUTPUT_COLUMNS, parse_frame

DEFAULT_BATCH = 1_000_000


def itf_lines(path: Path | None = None, batch_size: int = DEFAULT_BATCH) -> Iterator[list[str]]:
    """Yield batches of raw (newline-stripped) lines from the gzipped ITF."""
    path = path or config.ITF_GZ
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        batch: list[str] = []
        for line in fh:
            batch.append(line.rstrip("\n").rstrip("\r"))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def parse_batch(lines: list[str]) -> pl.DataFrame:
    """Parse one batch of raw lines into the typed schema."""
    lf = pl.LazyFrame({"raw": lines}, schema={"raw": pl.String})
    return parse_frame(lf).select(OUTPUT_COLUMNS).collect()


def parse_itf(
    src: Path | None = None,
    dest: Path | None = None,
    *,
    batch_size: int = DEFAULT_BATCH,
    compression: str = "zstd",
) -> dict[str, Any]:
    """Parse the whole ITF snapshot to Parquet. Returns ingest statistics."""
    src = src or config.ITF_GZ
    dest = dest or config.ITF_PARQUET
    dest.parent.mkdir(parents=True, exist_ok=True)

    raw_lines = 0
    kept_rows = 0
    writer: pq.ParquetWriter | None = None
    try:
        for batch in itf_lines(src, batch_size=batch_size):
            raw_lines += len(batch)
            df = parse_batch(batch)
            kept_rows += df.height
            if df.height == 0:
                continue
            table = df.to_arrow()
            if writer is None:
                writer = pq.ParquetWriter(dest, table.schema, compression=compression)
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()

    return {
        "source": str(src),
        "parquet": str(dest),
        "raw_lines": raw_lines,
        "observations": kept_rows,
        "dropped_lines": raw_lines - kept_rows,
        "parquet_bytes": dest.stat().st_size if dest.exists() else 0,
    }


def scan(path: Path | None = None) -> pl.LazyFrame:
    """Lazily scan the parsed ITF Parquet."""
    return pl.scan_parquet(path or config.ITF_PARQUET)
