"""Derive the telluric-selected order set for ANY setting, by the paper's own
criterion: keep segments with real telluric line density, exclude the ~zero ones
(H26's "sufficient telluric lines"; M13 §1 showed this criterion reproduces their
eleven H1567 orders exactly).

STATUS (M19 validation): counting raw FTS-atlas absorption dips does NOT
discriminate — the H-band atlas is line-dense in every segment at every depth
threshold tried (0.02..0.5), so this script keeps all 21 and fails to reproduce
H_C. M13's coherence check evidently counted lines of the MOLECULES VIPER FITS
per segment (its atm model species), not raw transmission. Until that variant is
implemented, use: (a) K-band targets -> all orders + injection-based screening
(sanctioned by the M13 order-drop rule), (b) H1575 -> map H_C by wavelength
overlap from H1567. Kept for the per-segment wavelength/line reporting, which is
still useful diagnostics.

Method: for each (order, detector) segment of a converted product, count telluric
absorption lines in viper's own FTS atlas over that segment's wavelength range
(local minima with depth >= --depth, default 2%). Segments with fewer than --min
lines (default 5) are excluded. Emits the viper oset string for both the H-band
(0-based) and K-band (1-based) index conventions.

Validation mode: run against a CD-35/eta Tel H1567 file — it must reproduce
`4,7,8,9,10,12,13,14,17,18,19` (H_C) or the derivation logic is wrong.

Usage (WSL):
  python m2x_derive_oset.py CONVERTED.fits FTS_FILE [--depth 0.02] [--min 5]
"""
import argparse
import sys

import numpy as np
from astropy.io import fits


def load_fts(path):
    d = np.loadtxt(path)
    wn, trans = d[:, 0], d[:, 1]
    wl_nm = 1e7 / wn  # wavenumber (cm^-1) -> nm, vacuum
    i = np.argsort(wl_nm)
    return wl_nm[i], trans[i]


def count_lines(wl, tr, lo, hi, depth):
    m = (wl >= lo) & (wl <= hi)
    if m.sum() < 10:
        return 0
    t = tr[m]
    # local minima below (1 - depth)
    minima = (t[1:-1] < t[:-2]) & (t[1:-1] < t[2:]) & (t[1:-1] < 1.0 - depth)
    return int(minima.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("fts")
    ap.add_argument("--depth", type=float, default=0.02)
    ap.add_argument("--min", type=int, dest="min_lines", default=5)
    args = ap.parse_args()

    wl, tr = load_fts(args.fts)
    h = fits.open(args.product)

    # segment ranges in viper's enumeration order. Mirror inst_CRIRES exactly:
    # H-band (0-based): det_ord_max from the last column name per chip;
    #   order o -> order_idx, det = divmod(o, 3); detector rotated by the chip
    #   holding the max order; drs = det_ord_max[det-1] - order_idx.
    # K-band (1-based): drs = 7 - (o-1)//3, det = (o-1)%3 + 1.
    det_ord_max = [int(h[det].columns.names[-1].split("_")[0]) for det in (1, 2, 3)]
    ord_max = max(det_ord_max)
    ind_det_max = det_ord_max.index(ord_max) + 1
    wlen = h[0].header.get("HIERARCH ESO INS WLEN ID") or \
        h[0].header.get("ESO INS WLEN ID") or "?"
    kband = str(wlen).startswith("K")

    rows = []
    o_range = range(1, 19) if kband else range(0, 21)
    for o in o_range:
        if kband:
            q, r = divmod(o - 1, 3)
            det, drs = r + 1, 7 - q
        else:
            order_idx, det = divmod(o, 3)
            det = (det + ind_det_max) % 3
            det = 3 if det == 0 else det
            drs = det_ord_max[det - 1] - order_idx
        col = f"{drs:02d}_01_WL"
        if col not in h[det].columns.names:
            rows.append((o, det, drs, None, 0))
            continue
        w = np.asarray(h[det].data[col]).ravel()
        n = count_lines(wl, tr, np.nanmin(w), np.nanmax(w), args.depth)
        rows.append((o, det, drs, (float(np.nanmin(w)), float(np.nanmax(w))), n))

    keep = []
    print(f"setting {wlen} ({'K 1-based' if kband else 'H 0-based'} indexing), "
          f"depth>={args.depth}, min lines {args.min_lines}")
    for o, det, drs, rng, n in rows:
        mark = ""
        if rng is None:
            mark = "  (absent)"
        elif n >= args.min_lines:
            keep.append(o)
            mark = "  KEEP"
        print(f"  o={o:2d} det{det} drs{drs:02d} "
              f"{'%.1f-%.1f nm' % rng if rng else '--':>18s}  lines={n:4d}{mark}")
    print("\noset:", ",".join(str(o) for o in keep))


if __name__ == "__main__":
    main()
