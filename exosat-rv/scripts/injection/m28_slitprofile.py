"""SUPERSEDED by m28_contam.py -- kept for the record.

This first pass assumed the slit function spanned the full 10" slit but did not
verify it against the trace-wave order height, and it located the secondary peak
by masking +-0.6" around the companion -- which simply returns the companion's own
PSF skirt at the mask edge (every night reported ~0.62", not the 3.17" binary
separation). m28_contam.py fixes both: it derives the scale from the order height
(179.8 px x 0.056"/px = 10.07" over 512 points) and samples the profile at the
expected primary offset directly.

M28: measure the primary's contribution to the CD-35 2722 B slit, from the data.

Hoy et al. Fig. 3 estimates stellar contamination from slit-viewer PSF fits; this
project has never reduced the SV imaging, so the draft's figure-by-figure section
leaves that one comparison blank. The nodding slit function is an independent handle
on the same number: it is the spatial profile along the slit, so a primary inside the
slit appears as a second peak at the binary separation, and its height relative to the
companion peak bounds the contamination at the companion's position.

Usage (WSL): python m28_slitprofile.py [nightdir ...]
"""
import glob
import os
import sys

import numpy as np
from astropy.io import fits

PIXSCALE = 0.056
SEP_LIT = 3.17
SLIT_LEN = 10.0


def orders(path):
    with fits.open(path) as hd:
        for ext in hd[1:]:
            if ext.data is None:
                continue
            for col in ext.data.columns.names:
                v = np.asarray(ext.data[col], float).ravel()
                if v.size > 8 and np.isfinite(v).sum() > 8:
                    yield ext.name, col, v


def main():
    dirs = sys.argv[1:] or sorted(glob.glob("/home/matth/cr2res/red/night*"))
    print(f"# CRIRES+ slit {SLIT_LEN}\" long; literature A-B separation {SEP_LIT}\"")
    print(f"# {'night':<8s} {'chip/order':<18s} {'npts':>5s} {'\"/pt':>6s} "
          f"{'peak':>5s} {'2nd':>5s} {'2nd/1st':>8s} {'sep(\")':>7s}")
    rec = []
    for d in dirs:
        p = os.path.join(d, "cr2res_obs_nodding_slitfuncA.fits")
        if not os.path.exists(p):
            continue
        night = os.path.basename(d)
        shown = 0
        for chip, col, v in orders(p):
            v = np.nan_to_num(v - np.nanmedian(v))
            if v.max() <= 0:
                continue
            v = v / v.max()
            n = len(v)
            scale = SLIT_LEN / n           # arcsec per slit-function point
            i1 = int(np.argmax(v))
            w = max(3, int(round(0.6 / scale)))   # mask +-0.6" around the companion
            m = v.copy()
            m[max(0, i1 - w):i1 + w + 1] = -np.inf
            i2 = int(np.argmax(m))
            rec.append((night, chip, col, n, scale, i1, i2, m[i2]))
            if shown < 2:
                print(f"  {night:<8s} {chip + '/' + col:<18s} {n:>5d} {scale:>6.3f} "
                      f"{i1:>5d} {i2:>5d} {m[i2]:>8.4f} "
                      f"{abs(i2 - i1) * scale:>7.2f}")
                shown += 1
    if not rec:
        print("no slit functions found")
        return
    r = np.array([x[7] for x in rec])
    sep = np.array([abs(x[6] - x[5]) * x[4] for x in rec])
    near = np.abs(sep - SEP_LIT) < 0.6
    print(f"\n# {len(rec)} order-profiles from {len({x[0] for x in rec})} nights")
    print(f"# slit-function lengths: {sorted({x[3] for x in rec})} points "
          f"-> {sorted({round(x[4], 3) for x in rec})} \"/point")
    print(f"# secondary peak / companion peak: median {np.median(r):.4f}  "
          f"90th pct {np.percentile(r, 90):.4f}  max {r.max():.4f}")
    print(f"# secondary peaks landing within 0.6\" of the {SEP_LIT}\" binary "
          f"separation: {near.sum()}/{len(rec)} ({100 * near.mean():.1f}%)")
    if near.any():
        print(f"#   their relative height: median {np.median(r[near]):.4f}, "
              f"max {r[near].max():.4f}")


if __name__ == "__main__":
    main()
