"""Download the two bulk catalogs used by M1 (idempotent; serial, polite).

Sources (verified 2026-08-14):
  DR2 main: https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.fits
            (2,139,595,200 bytes per Content-Length header, 2026-08-14)
  DR1 main: https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/MerloniA_DR1/eRASS1_Main.v1.2.fits.tar.gz
            (643,072,855 bytes per Content-Length header, 2026-08-14)

Rule (repo): before any download >500 MB, check free disk space and note the size in STATUS.md.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"

FILES = {
    "eRASS3_Main_v1.3.fits": (
        "https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/"
        "RamosM_DR2/eRASS3_Main_v1.3.fits",
        2_139_595_200,
    ),
    "eRASS1_Main.v1.2.fits.tar.gz": (
        "https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/"
        "MerloniA_DR1/eRASS1_Main.v1.2.fits.tar.gz",
        643_072_855,
    ),
}


def main() -> int:
    DATA.mkdir(exist_ok=True)
    needed = sum(size for _, size in FILES.values())
    free = shutil.disk_usage(DATA).free
    if free < needed + 5_000_000_000:  # keep 5 GB headroom
        print(f"not enough disk: free={free:,} needed={needed:,}")
        return 1
    for name, (url, size) in FILES.items():
        dest = DATA / name
        if dest.exists() and dest.stat().st_size == size:
            print(f"ok (cached): {name} {size:,} bytes")
            continue
        print(f"downloading {name} ({size:,} bytes) ...")
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        got = dest.stat().st_size
        print(f"done: {name} {got:,} bytes {'OK' if got == size else 'SIZE MISMATCH'}")
        if got != size:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
