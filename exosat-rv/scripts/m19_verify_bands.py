"""Pull ONE raw frame header per candidate campaign and read the truth:
WLEN ID (the band/setting), OBJECT, DIT, and mode. Settles which of the
census finds are usable by the H/K pipeline and which are other regimes.

filter_path has now lied six times; this is the only reliable classifier.
Frames land in the scratchpad and are deleted after the header read.
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse

import requests
from astropy.io import fits

TAP = "https://archive.eso.org/tap_obs/sync"

# (label, ADQL where-clause fragment for one representative night)
PROBES = [
    ("BETPIC 110.23NC 2022-12-23", "object = 'BET PIC' AND prog_id LIKE '110.23NC%' AND date_obs BETWEEN '2022-12-23' AND '2022-12-24'"),
    ("BETPIC 114.27DX 2025-01-11", "object = 'BET PIC' AND prog_id LIKE '114.27DX%' AND date_obs BETWEEN '2025-01-11' AND '2025-01-12'"),
    ("BETPIC 114.27C6 2024-11-22", "object = 'BET PIC' AND prog_id LIKE '114.27C6%' AND date_obs BETWEEN '2024-11-22' AND '2024-11-23'"),
    ("HD1160 114.27C6 2024-10-24", "object = 'HD  1160' AND date_obs BETWEEN '2024-10-24' AND '2024-10-25'"),
    ("HD26820 114.27C6 2024-10-24", "object = 'HD 26820' AND date_obs BETWEEN '2024-10-24' AND '2024-10-25'"),
    ("PDS70 (CD-40 8434)", "object = 'CD-40 8434'"),
    ("HIP65426", "(object = 'HIP 65426' OR object = 'HIP65426B' OR object = 'HD 116434')"),
    ("AF LEP", "object = 'AF LEP'"),
    ("51 ERI", "object = '51 ERI'"),
]


def tap(query, tries=5):
    for k in range(tries):
        try:
            r = requests.get(TAP, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                          "FORMAT": "json", "MAXREC": "5",
                                          "QUERY": query}, timeout=180)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001
            print(f"  retry {k+1}: {str(e)[:80]}")
            time.sleep(15 * (k + 1))
    return []


def main():
    tmp = tempfile.mkdtemp(prefix="hdrprobe_")
    for label, where in PROBES:
        rows = tap(f"SELECT dp_id FROM dbo.raw WHERE instrument='CRIRES' "
                   f"AND dp_cat='SCIENCE' AND {where}")
        if not rows:
            print(f"{label:<30} no frames found")
            continue
        dp = rows[0]["dp_id"]
        dest = os.path.join(tmp, "probe.fits")
        url = f"https://dataportal.eso.org/dataPortal/file/{dp}"
        ok = False
        for k in range(4):
            try:
                r = requests.get(url, timeout=300)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(r.content)
                ok = True
                break
            except Exception as e:  # noqa: BLE001
                print(f"  fetch retry {k+1} ({label}): {str(e)[:60]}")
                time.sleep(20 * (k + 1))
        if not ok:
            print(f"{label:<30} FETCH FAILED")
            continue
        try:
            if r.content[:2] == b"\x1f\x8b" or dp.endswith(".Z"):
                subprocess.run(["python", "-c", "pass"])  # placeholder; .Z unlikely via direct file
            h = fits.getheader(dest)
            print(f"{label:<30} WLEN={h.get('HIERARCH ESO INS WLEN ID', '?'):8s} "
                  f"OBJ={str(h.get('OBJECT'))[:16]:16s} "
                  f"DIT={h.get('HIERARCH ESO DET SEQ1 DIT')} "
                  f"TECH={str(h.get('HIERARCH ESO DPR TECH'))[:24]}")
        except Exception as e:  # noqa: BLE001
            print(f"{label:<30} unreadable: {str(e)[:60]}")
        finally:
            if os.path.exists(dest):
                os.remove(dest)


if __name__ == "__main__":
    main()
