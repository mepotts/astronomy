"""M7: fetch current MPC orbits for the Feb-5-batch validation subset, politely.

One GET per designation against the MPC's public orbits API
(``https://data.minorplanetcenter.net/api/get-orb``, documented at
``minorplanetcenter.net/mpcops/documentation/orbits-api/``), >= 1.1 s apart, cached to
disk so a re-run costs zero requests. The response's ``mpc_orb`` block carries the
current fitted orbit as a heliocentric **ecliptic** cartesian state (CAR) at an MJD/TDT
epoch, plus fit statistics -- see ``src/itf_linker/attrib/core.py`` for the parse.

Designations that resolve to a merged object come back under a *primary* designation
that may differ from the one asked for (the Feb batch is already partly merged --
e.g. 2025 PD126 -> primary 2025 MH98); the sweep dedupes on the primary afterwards.

Read-only, no credentials. HOUSE LAW: nothing is ever submitted.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl

ORB_URL = "https://data.minorplanetcenter.net/api/get-orb"
USER_AGENT = (
    "itf-linker/0.3 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)
MIN_INTERVAL_S = 1.1
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}

SUBSET = ROOT / "data" / "raw" / "rubin" / "batch-feb-bright400.parquet"
CACHE = ROOT / "data" / "raw" / "rubin" / "orbits"


def cache_path(desig: str) -> Path:
    return CACHE / (desig.replace(" ", "_").replace("/", "_") + ".json")


def fetch_one(session: requests.Session, desig: str) -> dict:
    for attempt in range(4):
        resp = session.get(
            ORB_URL,
            json={"desig": desig},
            headers={"User-Agent": USER_AGENT},
            timeout=90,
        )
        if resp.status_code in RETRY_STATUS and attempt < 3:
            time.sleep(5.0 * 2**attempt)
            continue
        if resp.status_code == 200:
            return {"status": 200, "doc": resp.json()}
        # A non-retryable non-200 is an answer (e.g. no orbit), not an outage.
        return {"status": resp.status_code, "text": resp.text[:400]}
    return {"status": resp.status_code, "text": resp.text[:400]}


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    desigs = pl.read_parquet(SUBSET)["provid"].to_list()
    session = requests.Session()
    fetched = skipped = failed = 0
    last = 0.0
    for i, desig in enumerate(desigs):
        dest = cache_path(desig)
        if dest.exists():
            skipped += 1
            continue
        wait = MIN_INTERVAL_S - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        out = fetch_one(session, desig)
        out["requested_desig"] = desig
        out["fetched_at_unix"] = time.time()
        dest.write_text(json.dumps(out), encoding="utf-8")
        fetched += 1
        if out["status"] != 200:
            failed += 1
        if (i + 1) % 50 == 0:
            print(f"{i + 1}/{len(desigs)} fetched={fetched} cached={skipped} non200={failed}",
                  flush=True)
    print(f"done: {len(desigs)} designations, fetched={fetched}, cached={skipped}, "
          f"non200={failed}", flush=True)


if __name__ == "__main__":
    main()
