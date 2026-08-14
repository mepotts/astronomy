"""M29: measure the delivered spatial PSF from the nodding slit functions.

M29 sec 9 left an open question. Neither contrast nor separation nor S orders all the
outcomes once HD 4747 B is included:

    HIP 81208 B   0.325"  CLEAN 124 m/s
    beta Pic b    0.51"   FLOODED
    HD 4747 B     0.59"   companion not even separable from the host

A companion closer than two that fail. Raw separation cannot be the variable, and neither
can seeing alone, because CRIRES+ runs adaptive optics and the correction depends on the
guide star -- HIP 81208 is a bright B9, beta Pic is brighter still but at a much larger
distance in AO terms. What should matter is the separation measured in units of the
DELIVERED PSF, not in arcseconds.

That is measurable from data already on disk. The nodding slit function is the spatial
profile along the slit; its FWHM is the delivered PSF width for that observation, after AO,
seeing and instrument. This measures it per night per order and reports

    R = separation / PSF_FWHM

the number of resolution elements between companion and host. No new data, no modelling.

Method: for each slit function, subtract the median, normalise to the peak, and take the
full width at half maximum by linear interpolation on each side of the peak. Report the
median over all orders and nights of a target. Profiles whose half-power points run off
the array are discarded rather than extrapolated.

Usage (WSL): python m29_psf.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

PIXSCALE = 0.056

# target -> (glob of reduction dirs, separation ", outcome)
TARGETS = [
    ("CD-35 2722 B",  "/home/matth/cr2res/red/night*",            2.80, "CLEAN"),
    ("eta Tel B",     "/home/matth/cr2res/red_etatel/*",          4.21, "CLEAN"),
    ("beta Pic b",    "/home/matth/cr2res/red_bpb/*",             0.511, "FLOODED"),
    ("HD 4747 B",     "/home/matth/cr2res/red_m26/hd4747h",       0.59, "UNRESOLVED"),
    ("HIP 81208 B",   "/home/matth/cr2res/red_m26/h81208k*",      0.325, "CLEAN"),
    ("YSES 1 b",      "/home/matth/cr2res/red_m26/yses1[cd]",     1.70, "CLEAN"),
    ("PDS 70",        "/home/matth/cr2res/red_m26/pds70h*",       0.173, "FAILS"),
]


def order_height_arcsec(d):
    """Spatial extent the slit function spans, from the trace-wave polynomials."""
    for name in ("cr2res_cal_wave_tw_fpet.fits", "cr2res_cal_flat_tw_merged.fits"):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            continue
        try:
            with fits.open(p) as h:
                r = h[1].data[0]
                x = 1024.0
                up = np.asarray(r["Upper"]).ravel()
                lo = np.asarray(r["Lower"]).ravel()
                hi = sum(c * x ** i for i, c in enumerate(up))
                ll = sum(c * x ** i for i, c in enumerate(lo))
                if 50 < hi - ll < 400:
                    return (hi - ll) * PIXSCALE
        except Exception:
            pass
    return None


def fwhm(v, scale):
    """FWHM of a normalised profile, by linear interpolation. None if it runs off-array."""
    v = np.nan_to_num(v - np.median(v))
    if v.max() <= 0:
        return None
    v = v / v.max()
    i = int(np.argmax(v))
    half = 0.5

    def cross(rng):
        prev = i
        for j in rng:
            if v[j] < half:
                if v[prev] == v[j]:
                    return float(j)
                return prev + (v[prev] - half) / (v[prev] - v[j]) * (j - prev)
            prev = j
        return None
    left = cross(range(i - 1, -1, -1))
    right = cross(range(i + 1, len(v)))
    if left is None or right is None:
        return None
    return abs(right - left) * scale


def main():
    print("# M29: delivered PSF from the nodding slit function, and separation in")
    print("# resolution elements. R = separation / PSF_FWHM.\n")
    print(f"{'target':<15s} {'sep(\")':>7s} {'PSF FWHM(\")':>12s} {'n':>5s} "
          f"{'R = sep/PSF':>12s}  outcome")
    rows = []
    for name, pat, sep, out in TARGETS:
        widths = []
        for d in sorted(glob.glob(pat)):
            h = order_height_arcsec(d)
            p = os.path.join(d, "cr2res_obs_nodding_slitfuncA.fits")
            if h is None or not os.path.exists(p):
                continue
            try:
                with fits.open(p) as hd:
                    for e in hd[1:]:
                        if e.data is None:
                            continue
                        for c in e.data.columns.names:
                            if "SLIT_FUNC" not in c:
                                continue
                            v = np.asarray(e.data[c], float).ravel()
                            if v.size < 100:
                                continue
                            w = fwhm(v, h / v.size)
                            if w and 0.05 < w < 6.0:
                                widths.append(w)
            except Exception:
                continue
        if not widths:
            print(f"{name:<15s} {sep:>7.3f} {'--':>12s} {0:>5d} {'--':>12s}  {out}")
            continue
        psf = float(np.median(widths))
        R = sep / psf
        rows.append((name, sep, psf, R, out))
        print(f"{name:<15s} {sep:>7.3f} {psf:>12.3f} {len(widths):>5d} {R:>12.2f}  {out}")

    ok = [r for r in rows if r[4] in ("CLEAN", "FLOODED", "FAILS", "UNRESOLVED")]
    if len(ok) >= 3:
        print("\n# ordered by R (resolution elements between companion and host):")
        for n, sep, psf, R, out in sorted(ok, key=lambda x: x[3]):
            print(f"    R = {R:>6.2f}   {out:<11s} {n}")
        clean = [r[3] for r in ok if r[4] == "CLEAN"]
        bad = [r[3] for r in ok if r[4] != "CLEAN"]
        if clean and bad:
            sep_ok = min(clean) > max(bad)
            print(f"\n# lowest CLEAN R = {min(clean):.2f} ; highest non-clean R = "
                  f"{max(bad):.2f}   separates: {sep_ok}")
    print("\n# CAVEAT: the slit function is the profile cr2res fitted while extracting the")
    print("# BRIGHTEST trace. For a wide companion observed on its own that is the")
    print("# companion; for a blended pair it is the host. The width is the delivered")
    print("# spatial resolution either way, which is what R needs.")


if __name__ == "__main__":
    main()
