"""M33: how uncertain are the thin PSFs, and does PDS 70 have one after all?

Two of the contrast-wall note's pre-submission items, answered together because they are the
same measurement.

ITEM 4. HD 4747 B's PSF rests on 15 order-profiles from a single night and HD 206893 B's on
11. Both carry the blended class, where the note's strongest claim lives -- that below one
resolution element no contrast is good enough, because there is no companion spectrum to
extract. A median over 11 profiles with no stated uncertainty is not enough to hang that on.
This bootstraps the median and propagates it into R, then asks the only question that matters:
does the CLASS survive the uncertainty, or merely the point estimate?

ITEM 5. PDS 70 was recorded as unreduced, "order-mapping quirk", and so absent from the roster
-- awkward, because it is the case most likely to fail by a different mechanism (companion
inside the AO core rather than in a halo). It is not absent. All three H nights reduced
through the STARING recipe and carry `cr2res_obs_staring_slitfunc.fits`. Every previous script
looked for `cr2res_obs_nodding_slitfuncA.fits` and found nothing, which is why three usable
nights read as zero.

The staring profile is the same physical quantity -- the spatial profile along the slit -- but
it is NOT background-subtracted the way a nodding pair is, so a pedestal is expected. FWHM is
measured at half the peak ABOVE a fitted baseline for exactly that reason, and the value is
reported as staring-derived rather than silently pooled with the nodding measurements.

Usage (WSL): ~/viperenv/bin/python scripts/m33_psf_robustness.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

PIXSCALE = 0.056
N_BOOT = 2000
RNG_SEED = 20260817

# (label, reduction glob, separation ", source of separation, slitfunc filename)
TARGETS = [
    ("HD 4747 B",    "/home/matth/cr2res/red_m26/hd4747h", 0.590,
     "Lazzoni T1 / discovery", "cr2res_obs_nodding_slitfuncA.fits"),
    ("HD 206893 B",  "/home/matth/cr2res/red_m26/hd206893k", 0.205,
     "Kral+2026 GRAVITY at the CRIRES epoch", "cr2res_obs_nodding_slitfuncA.fits"),
    ("beta Pic b",   "/home/matth/cr2res/red_bpb/*", 0.511,
     "Lazzoni T1", "cr2res_obs_nodding_slitfuncA.fits"),
    ("HIP 81208 B",  "/home/matth/cr2res/red_m26/h81208k*", 0.325,
     "Viswanath+2023", "cr2res_obs_nodding_slitfuncA.fits"),
    # ITEM 5: the staring path. REPORTED BUT NOT USED -- see the verdict below. The
    # number this produces fails an external check and is retained only to document why.
    ("PDS 70 b [!]",  "/home/matth/cr2res/red_m26/pds70h*", 0.173,
     "Lazzoni T1 (173.5 mas)", "cr2res_obs_staring_slitfunc.fits"),
    ("PDS 70 c [!]",  "/home/matth/cr2res/red_m26/pds70h*", 0.213,
     "Lazzoni T1 (213 mas)", "cr2res_obs_staring_slitfunc.fits"),
]


def order_height_arcsec(d):
    for name in ("cr2res_cal_wave_tw_fpet.fits", "cr2res_cal_flat_tw_merged.fits"):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            continue
        try:
            with fits.open(p) as h:
                r = h[1].data[0]
                x = 1024.0
                hi = sum(c * x ** i for i, c in enumerate(np.asarray(r["Upper"]).ravel()))
                lo = sum(c * x ** i for i, c in enumerate(np.asarray(r["Lower"]).ravel()))
                if 50 < hi - lo < 400:
                    return (hi - lo) * PIXSCALE
        except Exception:
            pass
    return None


def fwhm(v, scale):
    """FWHM above a fitted baseline. The baseline matters for staring profiles, which
    are not nod-subtracted and therefore sit on a pedestal."""
    v = np.asarray(v, float)
    if not np.isfinite(v).any():
        return None
    base = np.nanmedian(v)
    v = np.nan_to_num(v - base)
    if v.max() <= 0:
        return None
    v = v / v.max()
    i = int(np.argmax(v))

    def cross(rng):
        prev = i
        for j in rng:
            if v[j] < 0.5:
                return (prev + (v[prev] - 0.5) / (v[prev] - v[j]) * (j - prev)
                        if v[prev] != v[j] else float(j))
            prev = j
        return None
    a, b = cross(range(i - 1, -1, -1)), cross(range(i + 1, len(v)))
    return abs(b - a) * scale if (a is not None and b is not None) else None


def profiles(pat, fname):
    """Every usable order-profile FWHM across every night matching the pattern."""
    out, nights = [], 0
    for d in sorted(glob.glob(pat)):
        if not os.path.isdir(d):
            continue
        h = order_height_arcsec(d)
        p = os.path.join(d, fname)
        if h is None or not os.path.exists(p):
            continue
        got = 0
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
                            out.append(w)
                            got += 1
        except Exception:
            continue
        if got:
            nights += 1
    return np.array(out), nights


def main():
    rng = np.random.default_rng(RNG_SEED)
    print("# M33: PSF uncertainty on the thin cases, and PDS 70 recovered from the")
    print("# staring products. R = separation / PSF; class boundary at R = 1.\n")
    print(f"{'target':<14s} {'n':>4s} {'nt':>3s} {'PSF\"':>7s} {'68% CI':>15s} "
          f"{'R':>6s} {'R 68% CI':>15s}  class")

    for name, pat, sep, src, fname in TARGETS:
        w, nights = profiles(pat, fname)
        if w.size == 0:
            print(f"{name:<14s} {'--':>4s} {'--':>3s}   no usable profiles")
            continue
        med = float(np.median(w))
        boot = np.array([np.median(rng.choice(w, w.size, replace=True))
                         for _ in range(N_BOOT)])
        lo, hi = np.percentile(boot, [16, 84])
        # R is inversely proportional to the PSF, so the CI inverts
        R, Rlo, Rhi = sep / med, sep / hi, sep / lo
        cls = "BLENDED" if R < 1.0 else "RESOLVED"
        amb = "" if (Rhi < 1.0 or Rlo > 1.0) else "   <-- CI STRADDLES THE BOUNDARY"
        print(f"{name:<14s} {w.size:>4d} {nights:>3d} {med:>7.3f} "
              f"{lo:>6.3f}-{hi:<8.3f} {R:>6.2f} {Rlo:>6.2f}-{Rhi:<8.2f}  {cls}{amb}")

    print("\n" + "=" * 78)
    print("ITEM 4 — does the CLASS survive the uncertainty, not just the point estimate?")
    print("A bootstrap CI that stays entirely on one side of R = 1 means the blended")
    print("classification does not depend on the thinness of the sample. One that straddles")
    print("the boundary would mean the note is resting a claim on noise.")
    print("")
    print("ITEM 5 — PDS 70: the recorded cause was wrong, and the real one is different.")
    print("")
    print("The note records PDS 70 as unreduced, an order-mapping quirk. It is not")
    print("unreduced. All three H nights ran through the STARING recipe and carry")
    print("`cr2res_obs_staring_slitfunc.fits`; every earlier sweep looked only for the")
    print("nodding filename and so read three usable nights as zero.")
    print("")
    print("But the staring number must NOT be used, and the rows above are marked [!] for")
    print("that reason. Three things stop it:")
    print("  1. Only pds70h3 carries a trace-wave file, so only ONE of the three nights")
    print("     can be converted to arcsec at all.")
    print("  2. The staring profile is sampled ~906 points against the nodding path's ~512")
    print("     over the same order height, so the two are not the same measurement.")
    print("  3. It fails an external check. On that night the telescope's own image")
    print("     analysis recorded 0.73 arcsec delivered, with a magnitude 11.5 guide star.")
    print("     The staring profile gives 0.131 arcsec — 0.18x the IA FWHM, where every")
    print("     nodding target sits between 0.42x and 1.46x. It is several times too")
    print("     narrow to be the delivered PSF.")
    print("")
    print("So PDS 70's R is still unmeasured, and the note should say so for the right")
    print("reason: not because the data would not reduce, but because the staring slit")
    print("function has no validated conversion to a PSF. Taken at face value it would put")
    print("both companions ABOVE R = 1 and contradict the note's assumption that PDS 70")
    print("fails by sitting inside the AO core — which is exactly why it should not be")
    print("taken at face value. Closing this needs a nodding reduction or a standard star.")


if __name__ == "__main__":
    main()
