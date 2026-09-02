"""M2: download the DR2 NWAY counterpart catalogs + Hard catalog (idempotent, serial).

The six eRASSc3 counterpart variants (NWAY vs LS10 / Gaia DR3 / CatWISE2020, for the
Main and Hard catalogs) plus the Hard catalog itself, from the DR2 portal file listing
(https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/, verified 2026-08-14).
Sizes are checked against Content-Length at run time (portal page shows none).

Rule (repo): >500 MB downloads need a disk check; done here (5 GB headroom kept).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/"

NAMES = [
    "eRASS3_Hard_v1.2.fits",
    "eRASSc3_Hard_LS10_Public_27Jul2026.fits.gz",
    "eRASSc3_Hard_GDR3_Public_27Jul2026.fits.gz",
    "eRASSc3_Hard_CW2020_Public_27Jul2026.fits.gz",
    "eRASSc3_Main_GDR3_Public_27Jul2026.fits.gz",
    "eRASSc3_Main_CW2020_Public_27Jul2026.fits.gz",
    "eRASSc3_Main_LS10_Public_27Jul2026.fits.gz",
]


def main() -> int:
    DATA.mkdir(exist_ok=True)
    sizes: dict[str, int] = {}
    for n in NAMES:
        r = requests.head(BASE + n, timeout=60)
        r.raise_for_status()
        sizes[n] = int(r.headers.get("Content-Length", 0))
        print(f"remote: {n} {sizes[n]:,} bytes")
    needed = sum(s for n, s in sizes.items()
                 if not ((DATA / n).exists() and (DATA / n).stat().st_size == s))
    free = shutil.disk_usage(DATA).free
    print(f"to download: {needed:,} bytes; free: {free:,}")
    if free < needed + 5_000_000_000:
        print("not enough disk")
        return 1
    for n in NAMES:
        dest = DATA / n
        if dest.exists() and dest.stat().st_size == sizes[n]:
            print(f"ok (cached): {n}")
            continue
        print(f"downloading {n} ...", flush=True)
        with requests.get(BASE + n, stream=True, timeout=1200) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        got = dest.stat().st_size
        print(f"done: {n} {got:,} bytes {'OK' if got == sizes[n] else 'SIZE MISMATCH'}")
        if got != sizes[n]:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
