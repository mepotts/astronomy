"""M1: harvest the public TNS object list, tokenless, via the web CSV export.

Why not /api/get/: it returns HTTP 401 without an API key (measured 2026-08-24).
The tokenless read route is the ordinary search page with &format=csv, which
returns the same fields the web UI shows.  Rate limit measured on BOTH paths:
x-rate-limit-limit: 10 per rolling 60 s.  We use 8/60 s.

Writes data/tns/<tag>.csv (gitignored).
"""

from __future__ import annotations

import io
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import DATA, session, tns_get  # noqa: E402

TNS_SEARCH = "https://www.wis-tns.org/search"
PAGE = 500  # max accepted; 1000 silently falls back to 50
TNSDIR = DATA / "tns"
TNSDIR.mkdir(parents=True, exist_ok=True)


def fetch_window(s, d0: date, d1: date, extra: dict | None = None) -> pd.DataFrame:
    """All TNS objects with discovery date in [d0, d1), paginated."""
    frames, page = [], 0
    while True:
        params = {
            "date_start[date]": d0.isoformat(),
            "date_end[date]": (d1 - timedelta(days=1)).isoformat(),
            "num_page": PAGE,
            "page": page,
            "format": "csv",
        }
        if extra:
            params.update(extra)
        r = tns_get(s, TNS_SEARCH, params=params)
        r.raise_for_status()
        txt = r.content.decode("utf-8", "replace")
        if not txt.lstrip().startswith('"ID"'):
            raise RuntimeError(f"unexpected TNS payload at {d0} page {page}: {txt[:200]!r}")
        df = pd.read_csv(io.StringIO(txt), dtype=str)
        print(f"  {d0} page {page}: {len(df)} rows", flush=True)
        if df.empty:
            break
        frames.append(df)
        if len(df) < PAGE:
            break
        page += 1
        if page > 40:
            raise RuntimeError("pagination runaway")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    s = session()
    today = date.today()

    # --- 12 months of everything, month by month (deterministic windows) ------
    start = date(today.year - 1, today.month, 1)
    months, cur = [], start
    while cur < today:
        nxt = date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
        months.append((cur, min(nxt, today + timedelta(days=1))))
        cur = nxt

    allf = []
    for d0, d1 in months:
        tag = f"month_{d0:%Y%m}"
        cache = TNSDIR / f"{tag}.csv"
        if cache.exists():
            df = pd.read_csv(cache, dtype=str)
            print(f"{tag}: cached {len(df)}", flush=True)
        else:
            df = fetch_window(s, d0, d1)
            df.to_csv(cache, index=False)
            print(f"{tag}: fetched {len(df)}", flush=True)
        allf.append(df)

    full = pd.concat(allf, ignore_index=True).drop_duplicates(subset=["ID"])
    full.to_csv(TNSDIR / "tns_12mo.csv", index=False)
    print(f"TOTAL 12 months: {len(full)} objects -> {TNSDIR/'tns_12mo.csv'}")


if __name__ == "__main__":
    main()
