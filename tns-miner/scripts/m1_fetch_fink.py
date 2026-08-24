"""Fetch full ZTF alert histories from Fink for a list of ZTF object IDs.

Fink's /api/v1/objects returns the complete raw alert packet per detection plus
Fink's own cross-matches (SIMBAD, VSX, GCVS, TNS, MPC).  Crucially the `d:tns`
column is stamped at the moment Fink processed that alert and is NOT back-filled,
so alerts predating a TNS report carry an empty `d:tns` -- which is what makes the
rewind in the positive control honest.  (Verified on ZTF26abfokua / AT 2026stb:
empty before the report, "Nova" after.)

Cache: data/fink/<oid>.json  (gitignored).  Tokenless.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import DATA, session  # noqa: E402

FINK_OBJECTS = "https://api.ztf.fink-portal.org/api/v1/objects"
CACHE = DATA / "fink"
CACHE.mkdir(parents=True, exist_ok=True)


def fetch_one(s: requests.Session, oid: str, refresh: bool = False) -> list[dict]:
    p = CACHE / f"{oid}.json"
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            r = s.post(FINK_OBJECTS,
                       json={"objectId": oid, "output-format": "json",
                             "withupperlim": "False"}, timeout=120)
            if r.status_code == 200:
                d = r.json()
                p.write_text(json.dumps(d), encoding="utf-8")
                return d
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    p.write_text("[]", encoding="utf-8")
    return []


def fetch_many(oids: list[str], refresh: bool = False, sleep: float = 0.15) -> dict:
    s = session()
    out = {}
    for i, oid in enumerate(oids, 1):
        out[oid] = fetch_one(s, oid, refresh=refresh)
        if i % 25 == 0:
            print(f"  fink {i}/{len(oids)}", flush=True)
        time.sleep(sleep)
    return out


if __name__ == "__main__":
    ids = sys.argv[1:]
    got = fetch_many(ids)
    for k, v in got.items():
        print(k, len(v))


CONE = "https://api.ztf.fink-portal.org/api/v1/conesearch"
_RESOLVE_CACHE = CACHE / "_resolve.json"


def resolve_oid(s: requests.Session, ra_deg: float, dec_deg: float,
                radius_arcsec: float = 3.0) -> str | None:
    """TNS gives many reporters' own internal names, not the ZTF objectId.
    Resolve by position against Fink.  3" matches TNS's own duplicate radius."""
    key = f"{ra_deg:.6f}_{dec_deg:.6f}_{radius_arcsec}"
    cache = {}
    if _RESOLVE_CACHE.exists():
        cache = json.loads(_RESOLVE_CACHE.read_text(encoding="utf-8"))
    if key in cache:
        return cache[key]
    oid = None
    try:
        r = s.post(CONE, json={"ra": str(ra_deg), "dec": str(dec_deg),
                               "radius": radius_arcsec, "output-format": "json",
                               "columns": "i:objectId,i:jd"}, timeout=120)
        if r.status_code == 200:
            j = r.json()
            if j:
                # most-alerted object wins if several fall in the cone
                counts: dict[str, int] = {}
                for x in j:
                    counts[x["i:objectId"]] = counts.get(x["i:objectId"], 0) + 1
                oid = max(counts, key=counts.get)
    except requests.RequestException:
        pass
    cache[key] = oid
    _RESOLVE_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return oid
