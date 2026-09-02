#!/usr/bin/env python
"""M3: fetch the dust-map data files for the extinction tier (task 2).

Downloads (into data/dustmaps/, gitignored):
  1. Edenhofer et al. 2023 3D map, mean_and_std_healpix.fits (~3.2 GB),
     Zenodo record 8187943 -- md5 pinned from the dustmaps 1.0.14 reference
     implementation (dustmaps/edenhofer2023.py; we replicate its loader
     because healpy, a hard dustmaps dependency, has no Windows build).
  2. SFD 1998 dust maps (sfddata, ~134 MB) from the kbarbary/sfddata
     GitHub archive, for sfdmap2 (2D far-field upper-bound tier).

Anonymous HTTP; resumable-ish (skips files that already verify).
Run   : .venv/Scripts/python.exe scripts/fetch_dust_data.py
"""

import hashlib
import os
import sys
import tarfile
import time

import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUST_DIR = os.path.join(BASE, "data", "dustmaps")
EDEN_DIR = os.path.join(DUST_DIR, "edenhofer_2023")
SFD_DIR = os.path.join(DUST_DIR, "sfddata-master")

EDEN_URL = ("https://zenodo.org/record/8187943/files/"
            "mean_and_std_healpix.fits")
EDEN_MD5 = "10c823a5fcf81b47b6e15530bcdf54dc"  # dustmaps 1.0.14 edenhofer2023.py
SFD_URL = "https://github.com/kbarbary/sfddata/archive/master.tar.gz"


def md5_of(path, chunk=1 << 22):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def download(url, dest, expected_md5=None):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        if expected_md5 is None:
            print(f"exists, keeping: {dest}")
            return
        if md5_of(dest) == expected_md5:
            print(f"exists + md5 OK: {dest}")
            return
        print(f"exists but md5 mismatch, re-downloading: {dest}")
    t0 = time.time()
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        tmp = dest + ".part"
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 22):
                fh.write(chunk)
                done += len(chunk)
                if total and done % (1 << 28) < (1 << 22):
                    print(f"  {done/1e9:.2f}/{total/1e9:.2f} GB "
                          f"({time.time()-t0:.0f}s)", flush=True)
    os.replace(tmp, dest)
    if expected_md5 is not None:
        got = md5_of(dest)
        if got != expected_md5:
            raise RuntimeError(f"md5 mismatch for {dest}: {got} != "
                               f"{expected_md5}")
        print(f"md5 verified: {got}")
    print(f"downloaded {dest} ({os.path.getsize(dest)/1e9:.2f} GB, "
          f"{time.time()-t0:.0f}s)")


def main():
    download(EDEN_URL, os.path.join(EDEN_DIR, "mean_and_std_healpix.fits"),
             EDEN_MD5)
    sfd_probe = os.path.join(SFD_DIR, "SFD_dust_4096_ngp.fits")
    if not os.path.exists(sfd_probe):
        tgz = os.path.join(DUST_DIR, "sfddata-master.tar.gz")
        download(SFD_URL, tgz)
        with tarfile.open(tgz) as tf:
            tf.extractall(DUST_DIR)
        os.remove(tgz)
        print(f"extracted SFD data to {SFD_DIR}")
    else:
        print(f"SFD data already present: {SFD_DIR}")
    print("dust data ready")


if __name__ == "__main__":
    sys.exit(main())
