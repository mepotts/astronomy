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
    ("2M0103AB B (25 nights!)", "object = '2M0103AB B' AND date_obs > '2024-01-01'"),
    ("2M0103AB B (early)", "object = '2M0103AB B' AND date_obs < '2023-06-01'"),
    ("HIP81208 113.26AY", "prog_id LIKE '113.26AY%' AND ra BETWEEN 248.9 AND 249.1 AND dec BETWEEN -55.6 AND -55.4"),
    ("CD-35 2722 (host-name frames)", "object = 'CD-35 2722' "),
    ("CD-35 2722B (nospace)", "object = 'CD-35 2722B' AND date_obs > '2025-02-01'"),
    ("PDS70 2025 raw H-labeled", "object = 'CD-40 8434' AND date_obs BETWEEN '2025-04-04' AND '2025-04-05'"),
    ("HD206893", "object = 'HD 206893'"),
    ("GQ LUP", "(object = 'GQ LUP' OR object = 'V GQ LUP') AND date_obs > '2022-01-01'"),
    ("YSES1 (TYC 8998)", "(object = 'TYC 8998-760-1B' OR object = 'YSES 1BC')"),
    ("HR8799 (HD 218396)", "object = 'HD 218396'"),
    ("HD19467", "(object = 'HD 19467' OR object = 'HD19467')"),
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
