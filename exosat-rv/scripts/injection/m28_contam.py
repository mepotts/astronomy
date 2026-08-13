"""M28: direct measurement of primary-star contamination in the CD-35 2722 B slit.

The extraction swath spans the full 10.07" slit (order height 179.8 px x 0.056"/px),
sampled by a 512-point slit function -> 0.0197"/point. The primary sits 3.17" from the
companion along a slit pinned at POSANG 153.1 deg on all 18 nights, so if its light
enters the slit it lands 161 points from the companion peak, on one side or the other.

This reports the slit-function height at exactly that offset, relative to the companion
peak: a direct, per-night, per-order measurement of the contamination fraction Hoy et
al. estimate from slit-viewer PSF fits (their Fig. 3), which this project has never
reduced. Also reports the local background so a non-detection can be quoted as a limit.

Usage (WSL): python m28_contam.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

PIXSCALE = 0.056
SEP_LIT = 3.17
HEIGHT_PX = 179.8


def main():
    dirs = sorted(glob.glob("/home/matth/cr2res/red/night*"))
    per_night = {}
    rows = []
    for d in dirs:
        p = os.path.join(d, "cr2res_obs_nodding_slitfuncA.fits")
        if not os.path.exists(p):
            continue
        night = os.path.basename(d)
        vals = []
        with fits.open(p) as hd:
            for ext in hd[1:]:
                if ext.data is None:
                    continue
                for col in ext.data.columns.names:
                    if "SLIT_FUNC" not in col:
                        continue
                    v = np.asarray(ext.data[col], float).ravel()
                    if v.size < 100 or not np.isfinite(v).any():
                        continue
                    scale = HEIGHT_PX * PIXSCALE / v.size
                    off = int(round(SEP_LIT / scale))
                    v = np.nan_to_num(v)
                    base = np.median(v)
                    v = v - base
                    i1 = int(np.argmax(v))
                    peak = v[i1]
                    if peak <= 0:
                        continue
                    # local noise: robust scatter of the profile away from both
                    # the companion and either candidate primary position
                    mask = np.ones(v.size, bool)
                    for c in (i1, i1 - off, i1 + off):
                        mask[max(0, c - 25):c + 26] = False
                    noise = 1.4826 * np.median(np.abs(v[mask] - np.median(v[mask])))
                    for sign in (-1, +1):
                        j = i1 + sign * off
                        if 0 <= j < v.size:
                            # take the best of a +-0.15" window (pointing wander)
                            w = int(round(0.15 / scale))
                            seg = v[max(0, j - w):j + w + 1]
                            vals.append((sign, seg.max() / peak, noise / peak))
        if vals:
            per_night[night] = vals
            rows.extend(vals)

    if not rows:
        print("no slit functions found")
        return
    a = np.array([r[1] for r in rows])
    nz = np.array([r[2] for r in rows])
    print(f"# CD-35 2722 A contamination at the companion trace, from {len(per_night)} "
          f"nights, {len(rows)} order-side measurements")
    print(f"# slit 10.07\" over 512 pts = 0.0197\"/pt; primary offset {SEP_LIT}\" "
          f"= {int(round(SEP_LIT / 0.0197))} pts")
    print(f"# ratio at the primary position / companion peak:")
    print(f"#   median {np.median(a):.5f}   90th pct {np.percentile(a, 90):.5f}   "
          f"max {a.max():.5f}")
    print(f"# profile noise / companion peak: median {np.median(nz):.5f}")
    print(f"# => contamination is {'DETECTED' if np.median(a) > 3 * np.median(nz) else 'NOT detected'} "
          f"({np.median(a) / np.median(nz):.1f}x the local profile noise)")
    print(f"\n# per night (median over orders/sides, and 3-sigma upper bound)")
    print(f"# {'night':<9s} {'ratio':>9s} {'3sig_lim':>9s}")
    for k in sorted(per_night, key=lambda s: int(s[5:])):
        v = np.array([x[1] for x in per_night[k]])
        z = np.array([x[2] for x in per_night[k]])
        print(f"  {k:<9s} {np.median(v):>9.5f} {3 * np.median(z):>9.5f}")


if __name__ == "__main__":
    main()
