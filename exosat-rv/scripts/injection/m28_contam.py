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
# The A-B separation this project documents is 2.8" (M0-RESULTS: 2.8" at 22.36 pc =
# 62.6 au). An earlier version of this script assumed 3.17" from memory and sampled a
# +-0.15" window around it, i.e. 153-169 points -- which does not contain the 2.8"
# position at 142 points. That measurement looked in the wrong place and is withdrawn.
# This version SCANS the profile instead of trusting any single value.
SEP_DOC = 2.8
SEP_ALT = 3.17
SCAN_LO, SCAN_HI = 1.5, 4.5     # arcsec, the range a primary could plausibly occupy
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
                    mask[max(0, i1 - 25):i1 + 26] = False
                    noise = 1.4826 * np.median(np.abs(v[mask] - np.median(v[mask])))
                    for sign in (-1, +1):
                        lo = i1 + sign * int(round(SCAN_LO / scale))
                        hi = i1 + sign * int(round(SCAN_HI / scale))
                        a, b = (lo, hi) if lo < hi else (hi, lo)
                        a, b = max(a, 0), min(b, v.size - 1)
                        if b - a < 5:
                            continue
                        seg = v[a:b + 1]
                        k = int(np.argmax(seg))
                        best_sep = abs((a + k) - i1) * scale
                        w = int(round(0.15 / scale))
                        def at(sep):
                            j = i1 + sign * int(round(sep / scale))
                            if not (0 <= j < v.size):
                                return np.nan
                            return v[max(0, j - w):j + w + 1].max() / peak
                        vals.append((sign, seg.max() / peak, noise / peak,
                                     best_sep, at(SEP_DOC), at(SEP_ALT)))
        if vals:
            per_night[night] = vals
            rows.extend(vals)

    if not rows:
        print("no slit functions found")
        return
    a  = np.array([r[1] for r in rows])
    nz = np.array([r[2] for r in rows])
    sp = np.array([r[3] for r in rows])
    d28 = np.array([r[4] for r in rows], float)
    d317 = np.array([r[5] for r in rows], float)
    print(f"# CD-35 2722 A contamination, SCANNED over {SCAN_LO}-{SCAN_HI} arcsec")
    print(f"# {len(per_night)} nights, {len(rows)} order-side profiles; "
          f"slit 10.07\" over 512 pts = 0.0197\"/pt")
    print(f"# strongest structure anywhere in the scan / companion peak:")
    print(f"#   median {np.median(a):.5f}   90th pct {np.percentile(a, 90):.5f}   "
          f"max {a.max():.5f}")
    print(f"# profile noise / companion peak: median {np.median(nz):.5f}")
    print(f"# separation of that strongest feature: median {np.median(sp):.2f}\"  "
          f"(16-84 pct {np.percentile(sp,16):.2f}-{np.percentile(sp,84):.2f}\")")
    print(f"#")
    print(f"# value AT the documented separation {SEP_DOC}\": "
          f"median {np.nanmedian(d28):.5f}  max {np.nanmax(d28):.5f}")
    print(f"# value at the previously-assumed {SEP_ALT}\":  "
          f"median {np.nanmedian(d317):.5f}  max {np.nanmax(d317):.5f}")
    thr = 3 * np.median(nz)
    print(f"#")
    print(f"# 3-sigma detection threshold (ratio): {thr:.5f}")
    for lbl, arr in ((f"{SEP_DOC}\"", d28), (f"{SEP_ALT}\"", d317),
                     ("anywhere in scan", a)):
        det = int(np.nansum(arr > thr))
        print(f"#   profiles above 3 sigma at {lbl:<18s}: {det}/{len(arr)} "
              f"({100*det/len(arr):.1f}%)")


if __name__ == "__main__":
    main()
