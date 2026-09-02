#!/usr/bin/env python
"""M2 fallback: windowed SYNC pull of the same rows/columns as
pull_dr3_nss_orbits.py, for when the anonymous async queue is congested
(observed 2026-08-16: async jobs >100 min in queue; sync answers in seconds).

Repo convention (README): anonymous TAP stays small and polite -- "window or
async for anything bigger". This is the window branch: keyset pagination on
source_id, TOP {WINDOW} per query (sync cap 2,000 rows), fixed pause between
requests, resumable via a checkpoint file.

Output: identical schema to the async path ->
        data/dr3_nss_amrf_input.parquet + data/dr3_nss_amrf_input.NOTE.md
Run   : .venv/Scripts/python.exe scripts/pull_dr3_nss_orbits_windowed.py
"""

import datetime
import glob
import hashlib
import io
import os
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pull_dr3_nss_orbits import QUERY, OUT_PARQUET, OUT_NOTE  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNK_DIR = os.path.join(BASE, "data", "windowed_chunks")
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"
WINDOW = 2000          # sync row cap (M1-verified)
PAUSE_S = 1.0          # politeness gap between requests
EXPECTED_TOTAL = 169227  # live GROUP BY count, 2026-08-16


def window_query(after_source_id):
    where_extra = f"\n  AND n.source_id > {after_source_id}"
    q = QUERY.replace("SELECT\n", f"SELECT TOP {WINDOW}\n", 1)
    q = q.rstrip() + where_extra + "\nORDER BY n.source_id\n"
    return q


def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)
    # resume support
    done = sorted(glob.glob(os.path.join(CHUNK_DIR, "chunk_*.parquet")))
    if done:
        last_df = pd.read_parquet(done[-1], columns=["source_id"])
        after = int(last_df["source_id"].max())
        n_have = sum(len(pd.read_parquet(p, columns=["source_id"]))
                     for p in done)
        print(f"resuming after source_id {after} ({len(done)} chunks, "
              f"{n_have} rows)")
    else:
        after = 0
        n_have = 0

    i = len(done)
    while True:
        q = window_query(after)
        t0 = time.time()
        r = requests.post(ENDPOINT, data={
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q,
        }, timeout=300)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        if not len(df):
            print("window empty -> done")
            break
        i += 1
        n_have += len(df)
        after = int(df["source_id"].max())
        df.to_parquet(os.path.join(CHUNK_DIR, f"chunk_{i:04d}.parquet"),
                      index=False)
        print(f"chunk {i:04d}: {len(df):5d} rows in {time.time()-t0:5.1f}s "
              f"(total {n_have}/{EXPECTED_TOTAL}, last id {after})")
        if len(df) < WINDOW:
            print("short window -> done")
            break
        time.sleep(PAUSE_S)

    # assemble
    parts = [pd.read_parquet(p)
             for p in sorted(glob.glob(os.path.join(CHUNK_DIR,
                                                    "chunk_*.parquet")))]
    full = pd.concat(parts, ignore_index=True)
    full = full.drop_duplicates(subset="source_id", keep="first")
    print(f"assembled {len(full)} unique rows, {len(full.columns)} cols")
    full.to_parquet(OUT_PARQUET, index=False)

    sha = hashlib.sha256()
    with open(OUT_PARQUET, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    digest = sha.hexdigest()
    size = os.path.getsize(OUT_PARQUET)
    counts = full["nss_solution_type"].value_counts().to_string()
    with open(OUT_NOTE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            f"# dr3_nss_amrf_input.parquet\n\n"
            f"- pulled: {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
            f" (WINDOWED SYNC fallback; async queue congested; "
            f"{WINDOW}-row keyset windows, {PAUSE_S}s pause)\n"
            f"- endpoint: {ENDPOINT} (anonymous)\n"
            f"- rows: {len(full)} (expected {EXPECTED_TOTAL} from live "
            f"GROUP BY, 2026-08-16)\n"
            f"- columns: {len(full.columns)}\n"
            f"- file size: {size} bytes\n- sha256: {digest}\n\n"
            f"## rows per nss_solution_type\n\n```\n{counts}\n```\n\n"
            f"## query (windowed variant of the below; see "
            f"scripts/pull_dr3_nss_orbits_windowed.py)\n\n```sql\n{QUERY}\n```\n"
        )
    print(f"wrote {OUT_PARQUET} ({size} B)\nsha256 {digest}")
    print(counts)


if __name__ == "__main__":
    sys.exit(main())
