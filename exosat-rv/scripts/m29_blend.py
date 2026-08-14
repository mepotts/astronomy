"""M29: roster-wide blending sweep — is each verdict about the companion, or the host?

M29 sec 11 established that three systems whose extractions were treated as companion
measurements are in fact blended pairs: HD 4747 B, HD 206893 B and (as contamination)
beta Pic b. The extraction in a blended pair is dominated by the host, so any verdict drawn
from it is a statement about the host.

Passing an injection gate does not catch this. The gate measures whether the FITTER
transmits an imposed velocity, and it transmits just as well on a bright star as on a faint
companion. That is why "gates 100 +- 0%" appears next to verdicts that may not be companion
measurements at all.

This sweeps every target with a reduction on disk and reports the one quantity that decides
it:

    R = projected separation / delivered PSF FWHM

both measured, not assumed. The PSF comes from the nodding slit function (the spatial
profile along the slit); the separation from a primary source or is marked UNSOURCED.

CLASSIFICATION, fixed before running:
  R < 1.0   BLENDED   -- within one resolution element. No companion spectrum exists to
                         extract at any contrast; the verdict describes the host.
  R >= 1.0  RESOLVED  -- separable; the extraction targets one component.
  no sep    UNKNOWN   -- not classified. A guessed separation is what this sweep exists
                         to stop.

Usage (WSL): python m29_blend.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

PIXSCALE = 0.056
R_BLEND = 1.0

# (target, reduction glob, separation ", source, ledger verdict)
ROSTER = [
    ("CD-35 2722 B", "/home/matth/cr2res/red/night*", 2.800,
     "M0-RESULTS (2.8\" at 22.36 pc)", "CONFIRMED: blind detection, 70-90 m/s"),
    ("eta Tel B", "/home/matth/cr2res/red_etatel/*", 4.210,
     "Lazzoni T1: 4210 mas", "NULL: msini >= 0.5-1.2 MJup, injection-gated"),
    # Bohn+2020: projected physical separation 160 au for the inner companion;
    # SIMBAD parallax 10.6124 mas -> 94.23 pc -> 1.698". (The queue's 1.7" was right.)
    ("YSES 1 b", "/home/matth/cr2res/red_m26/yses1[cd]", 1.698,
     "Bohn+2020 160 au / SIMBAD plx 10.6124 mas", "CLEAN: 34 m/s, gates 101+-2%"),
    ("HIP 81208 B", "/home/matth/cr2res/red_m26/h81208k*", 0.325,
     "Viswanath+2023: 320.9/328.7 mas", "CLEAN: 124 m/s, gates 99+-1%"),
    ("beta Pic b", "/home/matth/cr2res/red_bpb/*", 0.511,
     "Lazzoni T1: 510.8 mas", "CONTAMINATION-LIMITED: km/s, r(BERV)=+0.88"),
    ("HD 206893 B", "/home/matth/cr2res/red_m26/hd206893k", 0.205,
     "Kral+2026 GRAVITY astrometry at the CRIRES epoch", "CLEAN: gates 100-102%, banked"),
    ("HD 4747 B", "/home/matth/cr2res/red_m26/hd4747h", 0.590,
     "Lazzoni T1 / discovery", "n/a - reduced M29 as a test"),
    # SIMBAD basic: SCR J0103-5515 (AB, SB*) at 15.898563 -55.2656231 and
    # SCR J0103-5515C (the companion, LM*) at 15.898250 -55.2651667
    # -> dRA -0.642", dDec +1.643" -> 1.764" at PA 338.7 deg
    ("2M0103AB b", "/home/matth/cr2res/red_m26/m0103a", 1.764,
     "SIMBAD component coordinates", "CLEAN: within-night ~53 m/s, gates 100+-0%"),
    ("CD-35 deep pair", "/home/matth/cr2res/red_m26/cd35d2", None,
     "UNSOURCED", "shelved: M4368 thermal-IR"),
]


def height_arcsec(d):
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


def fwhm_and_wing(v, scale, sep):
    """FWHM of the profile, and its height at +-sep from the peak, both normalised."""
    v = np.nan_to_num(v - np.median(v))
    if v.max() <= 0:
        return None, None
    v = v / v.max()
    i = int(np.argmax(v))

    def cross(rng):
        prev = i
        for j in rng:
            if v[j] < 0.5:
                return prev + (v[prev] - 0.5) / (v[prev] - v[j]) * (j - prev) \
                    if v[prev] != v[j] else float(j)
            prev = j
        return None
    a, b = cross(range(i - 1, -1, -1)), cross(range(i + 1, len(v)))
    w = abs(b - a) * scale if (a is not None and b is not None) else None
    wing = None
    if sep:
        off = int(round(sep / scale))
        k = max(2, int(round(0.06 / scale)))
        vals = [v[max(0, j - k):j + k + 1].max()
                for j in (i - off, i + off) if 0 <= j < len(v)]
        wing = max(vals) if vals else None
    return w, wing


def main():
    print("# M29 roster blending sweep — R = projected separation / delivered PSF FWHM")
    print(f"# classification fixed in advance: R < {R_BLEND} => BLENDED (verdict describes "
          f"the host)\n")
    print(f"{'target':<16s} {'sep(\")':>7s} {'PSF(\")':>7s} {'n':>4s} {'R':>6s} "
          f"{'wing':>6s}  {'class':<9s} ledger verdict")
    flagged = []
    for name, pat, sep, src, verdict in ROSTER:
        widths, wings = [], []
        for d in sorted(glob.glob(pat)):
            h = height_arcsec(d)
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
                            w, g = fwhm_and_wing(v, h / v.size, sep)
                            if w and 0.05 < w < 6.0:
                                widths.append(w)
                                if g is not None:
                                    wings.append(g)
            except Exception:
                continue
        if not widths:
            print(f"{name:<16s} {'-':>7s} {'no slitfunc':>7s} {0:>4d} {'-':>6s} "
                  f"{'-':>6s}  {'NO DATA':<9s} {verdict[:34]}")
            continue
        psf = float(np.median(widths))
        wing = float(np.median(wings)) if wings else None
        if sep is None:
            cls, R = "UNKNOWN", None
        else:
            R = sep / psf
            cls = "BLENDED" if R < R_BLEND else "RESOLVED"
            if cls == "BLENDED":
                flagged.append((name, R, verdict))
        print(f"{name:<16s} {(f'{sep:.3f}' if sep else 'unsrc'):>7s} {psf:>7.3f} "
              f"{len(widths):>4d} {(f'{R:.2f}' if R else '-'):>6s} "
              f"{(f'{wing:.2f}' if wing is not None else '-'):>6s}  {cls:<9s} {verdict[:34]}")

    print("\n" + "=" * 78)
    if flagged:
        print("VERDICTS THAT DESCRIBE THE HOST, NOT THE COMPANION:")
        for n, R, v in sorted(flagged, key=lambda x: x[1]):
            print(f"  {n:<16s} R = {R:.2f}   ledger says: {v}")
        print("\nThese are not companion measurements. Passing injection gates does not")
        print("distinguish them, because the gate tests the fitter, not the target.")
    unk = [r[0] for r in ROSTER if r[2] is None]
    if unk:
        print(f"\nUNCLASSIFIED for want of a sourced separation: {', '.join(unk)}")
        print("Not guessed. Sourcing them is the remaining work.")
    print("\n'wing' is the profile height at the companion offset relative to the peak:")
    print("high (>0.3) means the second source sits inside the first's PSF.")


if __name__ == "__main__":
    main()
