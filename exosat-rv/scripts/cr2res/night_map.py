"""Map the 18 archive ADP epochs onto ~/cr2res night directories.

Prints one line per epoch:  <nightdir>\t<ADP file>\t<MJD>\t<status>
status = done (already reduced), todo (needs fetch+reduce).
Existing night1..5 keep their numbers; missing epochs get night6.. in MJD order.
"""
import glob
import os
import sys

from astropy.io import fits

ADP_DIR = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/spectra"
RED = os.path.expanduser("~/cr2res/red")

adps = []
for f in sorted(glob.glob(os.path.join(ADP_DIR, "ADP*.fits"))):
    mjd = float(fits.getheader(f)["MJD-OBS"])
    adps.append((mjd, os.path.basename(f)))
adps.sort()

have = {}
for d in sorted(glob.glob(os.path.join(RED, "night*"))):
    fa = os.path.join(d, "cr2res_obs_nodding_extractedA.fits")
    if os.path.exists(fa):
        have[os.path.basename(d)] = float(fits.getheader(fa)["MJD-OBS"])

used = set()
rows = []
nxt = max([int(n[5:]) for n in have] + [0]) + 1
for mjd, adp in adps:
    hit = None
    for n, m in have.items():
        if abs(m - mjd) < 0.02 and n not in used:
            hit = n
            break
    if hit:
        used.add(hit)
        rows.append((hit, adp, mjd, "done"))
    else:
        rows.append((f"night{nxt}", adp, mjd, "todo"))
        nxt += 1

for n, adp, mjd, st in rows:
    print(f"{n}\t{adp}\t{mjd:.5f}\t{st}")
missing = [n for n, m in have.items() if n not in used]
if missing:
    print(f"# reduced nights with no ADP match: {missing}", file=sys.stderr)
