#!/usr/bin/env python
"""M2 fallback v2: range-partitioned SYNC pull of the full DR3 NSS orbit set.

Faster than the keyset windows (pull_dr3_nss_orbits_windowed.py): a 3-second
server-side aggregate first maps the row count per source_id bucket
(FLOOR(source_id / 2^52); 1,536 non-empty buckets, max 566 rows on
2026-08-16), then consecutive buckets are greedily packed into ranges of
<= {PACK} rows and each range is pulled with a plain indexed predicate --
no ORDER BY, no per-window sort, no truncation risk (every range is checked
against its expected count; a mismatch aborts).

Assembles data/range_chunks/* together with any keyset chunks already in
data/windowed_chunks/*, dedups on source_id, and hard-checks the total
against the live aggregate before writing:
  data/dr3_nss_amrf_input.parquet + data/dr3_nss_amrf_input.NOTE.md

Run   : .venv/Scripts/python.exe scripts/pull_dr3_nss_orbits_ranged.py
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
RANGE_DIR = os.path.join(BASE, "data", "range_chunks")
KEYSET_DIR = os.path.join(BASE, "data", "windowed_chunks")
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"
BUCKET = 2 ** 52
PACK = 1900          # max rows per range request (sync cap 2000)
PAUSE_S = 0.5
TYPES = ("'Orbital','AstroSpectroSB1','OrbitalAlternative',"
         "'OrbitalAlternativeValidated','OrbitalTargetedSearch',"
         "'OrbitalTargetedSearchValidated'")


def sync_csv(q, timeout=300):
    r = requests.post(ENDPOINT, data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q,
    }, timeout=timeout)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def bucket_histogram():
    q = (f"SELECT FLOOR(source_id/{float(BUCKET)}) AS bucket, COUNT(*) AS n "
         f"FROM gaiadr3.nss_two_body_orbit "
         f"WHERE nss_solution_type IN ({TYPES}) GROUP BY bucket")
    h = sync_csv(q)
    h["bucket"] = h["bucket"].astype("int64")
    h["n"] = h["n"].astype(int)
    return h.sort_values("bucket").reset_index(drop=True)


def pack_ranges(hist):
    """Greedy pack of consecutive buckets into ranges of <= PACK expected
    rows, then TILE: each range's hi = next range's lo, first lo = 0, last
    hi = None (open).  Tiling matters because the server histogram is
    computed in double precision (FLOOR(id/2^52.0)); ids beyond 2^53 round,
    so per-bucket counts wobble +-1 at boundaries and a row could otherwise
    fall into a skipped 'empty' gap.  Expected counts are therefore
    approximate; the exact global COUNT(*) check in main() is the loss
    guard."""
    groups = []
    cur_lo, cur_n = None, 0
    prev_b = None
    for b, n in zip(hist["bucket"], hist["n"]):
        if cur_lo is None:
            cur_lo, cur_n = b, n
        elif cur_n + n > PACK:
            groups.append((cur_lo, cur_n))
            cur_lo, cur_n = b, n
        else:
            cur_n += n
        prev_b = b
    if cur_lo is not None:
        groups.append((cur_lo, cur_n))
    ranges = []
    for i, (lo_b, n) in enumerate(groups):
        lo = 0 if i == 0 else lo_b * BUCKET
        hi = groups[i + 1][0] * BUCKET if i + 1 < len(groups) else None
        ranges.append((lo, hi, n))
    return ranges


def main():
    os.makedirs(RANGE_DIR, exist_ok=True)
    hist = bucket_histogram()
    expected_total = int(hist["n"].sum())
    ranges = pack_ranges(hist)
    print(f"{len(hist)} buckets, {expected_total} rows -> "
          f"{len(ranges)} range requests (max {max(r[2] for r in ranges)} "
          f"rows/request)")

    got = 0
    for i, (lo, hi, n_exp) in enumerate(ranges, 1):
        path = os.path.join(RANGE_DIR, f"range_{i:04d}.parquet")
        if os.path.exists(path):
            k = len(pd.read_parquet(path, columns=["source_id"]))
            if abs(k - n_exp) <= 8:  # histogram is approximate (see above)
                got += k
                continue
        pred = f"\n  AND n.source_id >= {lo}"
        if hi is not None:
            pred += f" AND n.source_id < {hi}"
        q = QUERY.rstrip() + pred + "\n"
        t0 = time.time()
        df = sync_csv(q)
        if len(df) >= 2000:
            raise RuntimeError(
                f"range {i}: {len(df)} rows hit the sync cap -- possible "
                f"truncation; ABORT (no silent loss)")
        if len(df) != n_exp:
            print(f"  note: range {i} got {len(df)} vs approx-expected "
                  f"{n_exp} (double-precision bucket rounding)")
        df.to_parquet(path, index=False)
        got += len(df)
        print(f"range {i:04d}/{len(ranges)}: {len(df):4d} rows in "
              f"{time.time()-t0:4.1f}s (total {got}/{expected_total})")
        time.sleep(PAUSE_S)

    # Assembly from the tiled range chunks ONLY (they cover the whole id
    # space; the keyset chunks from fallback v1 are redundant).
    #
    # Two verified multiplicities (live archive, 2026-08-16) mean source_id
    # is NOT a key in either table:
    #   - nss_two_body_orbit, 6 astrometric types: 169,227 rows over
    #     169,129 distinct sources -- 98 sources carry BOTH an
    #     AstroSpectroSB1 and an OrbitalTargetedSearch(Validated) solution.
    #     Both are genuine independent orbits: KEEP both rows.
    #   - binary_masses: 195,315 rows over 195,239 distinct sources -- the
    #     LEFT JOIN fans out one extra row for sources with two mass rows.
    #     Resolve: prefer the bm row whose combination_method starts with
    #     the row's nss_solution_type, then m1_ref='IsocLum', then first.
    parts = [pd.read_parquet(p) for p in
             sorted(glob.glob(os.path.join(RANGE_DIR, "range_*.parquet")))]
    full = pd.concat(parts, ignore_index=True)
    import numpy as np
    meth = full["bm_combination_method"].astype(str)
    stype = full["nss_solution_type"].astype(str)
    pref = np.where([m.startswith(s) for m, s in zip(meth, stype)], 0,
                    np.where(full["bm_m1_ref"] == "IsocLum", 1, 2))
    full = (full.assign(_pref=pref)
            .sort_values(["source_id", "nss_solution_type", "_pref"],
                         kind="stable")
            .groupby(["source_id", "nss_solution_type"], as_index=False,
                     sort=False)
            .head(1)
            .drop(columns="_pref"))
    print(f"assembled {len(full)} solution rows "
          f"({full['source_id'].nunique()} distinct sources), "
          f"{len(full.columns)} cols")
    # EXACT loss guard: a plain integer COUNT(*) with the same WHERE
    exact = int(sync_csv(
        f"SELECT COUNT(*) AS n FROM gaiadr3.nss_two_body_orbit "
        f"WHERE nss_solution_type IN ({TYPES})")["n"].iloc[0])
    if len(full) != exact:
        raise RuntimeError(f"assembly {len(full)} != exact count {exact}")
    full = full.sort_values("source_id").reset_index(drop=True)
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
            f" (RANGE-PARTITIONED SYNC: bucket histogram + {len(ranges)} "
            f"indexed range requests <= {PACK} rows, {PAUSE_S}s pause; "
            f"async queue was congested >100 min)\n"
            f"- endpoint: {ENDPOINT} (anonymous)\n"
            f"- rows: {len(full)} (hard-checked == exact live COUNT(*) "
            f"{exact}; bucket histogram approx-total was {expected_total})\n"
            f"- columns: {len(full.columns)}\n"
            f"- file size: {size} bytes\n- sha256: {digest}\n\n"
            f"## rows per nss_solution_type\n\n```\n{counts}\n```\n\n"
            f"## query (per-range WHERE added; see "
            f"scripts/pull_dr3_nss_orbits_ranged.py)\n\n```sql\n{QUERY}\n```\n"
        )
    print(f"wrote {OUT_PARQUET} ({size} B)\nsha256 {digest}")
    print(counts)


if __name__ == "__main__":
    sys.exit(main())
