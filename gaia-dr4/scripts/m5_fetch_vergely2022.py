#!/usr/bin/env python
"""M5 task 2: fetch the Vergely, Lallement & Cox (2022) 3D extinction cubes.

Why: M4 closed 9 of the 13 dust-ambiguous far-star rows with Bayestar19,
but B19 is a north-only (dec > -30) map and 4 rows stayed bracketed.
Vergely+2022 is an ALL-SKY Cartesian inversion -- it reaches the south.

Product, verified against the CDS ReadMe (J/A+A/664/A174, ReadMe fetched
2026-08-18, local copy data/dustmaps/vergely2022/ReadMe):

    "3D distribution of extinction density at 550nm in a 6kpc by 6kpc by
     0.8kpc volume around the Sun.  The map is in Cartesian coordinates
     with the Sun at centre X,Y,Z=0,0,0.  The X axis is directed to the
     Galactic Centre, the Y axis is along the direction of rotation, and
     the Z axis points to the Northern Galactic Pole.  Distances X, Y, Z
     units are parsecs.  The extinction density is in nanomagnitude per
     parsec."
    "Caution: read the article for assumptions during the inversion
     (especially the resolution) and errors at large distances or beyond
     very dense structures."

and against list.dat (5 FITS cubes; the two we need):

    601 601  81  114294 explore_cube_density_values_025pc_v2.fits
        "Explore cube density, 6kpc x 6kpc x 0.8kpc for a correlation
         length of 25pc"
    501 501  41   40208 explore_cube_density_values_050pc_v2.fits
        "Explore cube density, 10kpc x 10kpc x 0.8kpc for a correlation
         length of 50pc"
    501 501  41   40208 explore_cube_density_errors_050pc_v2.fits
        "Explore cube density errors, ... correlation length of 50pc"

We take 025pc (the finest cube that contains all four targets), 050pc
(independent coarser cross-check) and the 050pc ERROR cube (the map's own
uncertainty -- the honest bracket on any arbitration).  The 7.5 GB ASCII
`cube_ext.dat` is the same data as the 025pc FITS and is NOT downloaded.

Access: anonymous FTP (cdsarc.cds.unistra.fr:/pub/cats/J/A+A/664/A174).
The https view of the same tree (cdsarc.cds.unistra.fr/ftp/...) sits behind
an Anubis proof-of-work bot check as of 2026-08-18 and intermittently
refuses plain clients.  The anonymous FTP service accepts the same requests
without any challenge, so we use it; we do NOT attempt to solve the bot
challenge.

Run: .venv/Scripts/python.exe scripts/m5_fetch_vergely2022.py
"""

import hashlib
import io
import os
import sys
import time
from ftplib import FTP

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(BASE, "data", "dustmaps", "vergely2022")

HOST = "cdsarc.cds.unistra.fr"
ROOT = "/pub/cats/J/A+A/664/A174"
DOC = ["ReadMe", "list.dat"]
CUBES = [
    ("fits/explore_cube_density_values_025pc_v2.fits", 117034560),
    ("fits/explore_cube_density_values_050pc_v2.fits", 41169600),
    ("fits/explore_cube_density_errors_050pc_v2.fits", 41169600),
]


def md5_of(path, chunk=1 << 22):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def fetch(ftp, remote, local, expect_size=None):
    if os.path.exists(local) and (expect_size is None
                                  or os.path.getsize(local) == expect_size):
        print(f"exists ({os.path.getsize(local)} B): {local}")
        return
    os.makedirs(os.path.dirname(local), exist_ok=True)
    t0 = time.time()
    tmp = local + ".part"
    with open(tmp, "wb") as fh:
        ftp.retrbinary(f"RETR {remote}", fh.write, blocksize=1 << 20)
    got = os.path.getsize(tmp)
    if expect_size is not None and got != expect_size:
        os.remove(tmp)
        raise RuntimeError(f"{remote}: got {got} B, ReadMe/LIST says "
                           f"{expect_size} B -- ABORT")
    os.replace(tmp, local)
    print(f"downloaded {local} ({got/1e6:.1f} MB, {time.time()-t0:.0f}s, "
          f"md5 {md5_of(local)})")


def main():
    os.makedirs(DEST, exist_ok=True)
    ftp = FTP(HOST, timeout=180)
    ftp.login()          # anonymous
    print(f"connected: {ftp.getwelcome()}")
    ftp.cwd(ROOT)
    listing = []
    ftp.retrlines("LIST", listing.append)
    print("\n".join(listing))
    for name in DOC:
        buf = io.BytesIO()
        ftp.retrbinary(f"RETR {name}", buf.write)
        with open(os.path.join(DEST, name), "wb") as fh:
            fh.write(buf.getvalue())
        print(f"wrote {name} ({len(buf.getvalue())} B)")
    for remote, size in CUBES:
        fetch(ftp, remote, os.path.join(DEST, os.path.basename(remote)), size)
    ftp.quit()
    print("Vergely+2022 cubes ready in", DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
