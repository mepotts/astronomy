"""M30 header probes: pull ONE raw frame per candidate night and read the truth
(LESSONS §3.1 filter_path lies; §1.10 check INS MODE + ORIGFILE before classifying).

The m19_verify_bands.py pattern: fetch to a temp dir, read the header, delete.
Given (night, object) pairs, picks the longest-DIT science frame of the night —
for HiRISE that is the deep (companion) integration, the frame whose setting the
pipeline would actually consume.

Usage: m30_probe.py "NIGHT|OBJECT[,OBJECT]" ...
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

import requests
from astropy.io import fits

TAP = "https://archive.eso.org/tap_obs/sync"


def tap(query: str, tries: int = 5) -> list[dict]:
    for k in range(tries):
        try:
            r = requests.get(TAP, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                          "FORMAT": "json", "MAXREC": "500",
                                          "QUERY": query}, timeout=180)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001
            print(f"  TAP retry {k + 1}: {str(e)[:80]}", flush=True)
            time.sleep(15 * (k + 1))
    return []


def main() -> None:
    tmp = tempfile.mkdtemp(prefix="m30probe_")
    for spec in sys.argv[1:]:
        night, objlist = spec.split("|", 1)
        names = " OR ".join(f"object = '{o.strip()}'" for o in objlist.split(","))
        rows = tap(f"SELECT dp_id, exposure FROM dbo.raw "
                   f"WHERE instrument='CRIRES' AND dp_cat='SCIENCE' AND ({names}) "
                   f"AND date_obs BETWEEN '{night}' AND '{night}T23:59:59'")
        if not rows:
            print(f"{spec:<34} no frames found", flush=True)
            continue
        rows.sort(key=lambda r: -(r.get("exposure") or 0))
        dp = rows[0]["dp_id"]
        dest = os.path.join(tmp, "probe.fits")
        url = f"https://dataportal.eso.org/dataPortal/file/{dp}"
        ok = False
        for k in range(3):
            try:
                r = requests.get(url, timeout=600)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(r.content)
                ok = True
                break
            except Exception as e:  # noqa: BLE001
                print(f"  fetch retry {k + 1}: {str(e)[:60]}", flush=True)
                time.sleep(20 * (k + 1))
        if not ok:
            print(f"{spec:<34} FETCH FAILED ({dp})", flush=True)
            continue
        try:
            h = fits.getheader(dest)
            print(f"{night} {dp}\n"
                  f"    OBJECT={h.get('OBJECT')!r}"
                  f" WLEN={h.get('HIERARCH ESO INS WLEN ID', '?')}"
                  f" MODE={h.get('HIERARCH ESO INS MODE', '?')}"
                  f" DIT={h.get('HIERARCH ESO DET SEQ1 DIT')}\n"
                  f"    TECH={h.get('HIERARCH ESO DPR TECH', '?')}"
                  f" TPL={h.get('HIERARCH ESO TPL ID', '?')}"
                  f" NODPOS={h.get('HIERARCH ESO SEQ NODPOS', '?')}\n"
                  f"    ORIGFILE={h.get('ORIGFILE', h.get('HIERARCH ESO ORIGFILE', '?'))}"
                  f" PROG={h.get('HIERARCH ESO OBS PROG ID', '?')}",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{spec:<34} unreadable: {str(e)[:70]}", flush=True)
        finally:
            if os.path.exists(dest):
                os.remove(dest)
        time.sleep(5)  # politeness between fetches


if __name__ == "__main__":
    main()
