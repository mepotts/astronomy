"""M27/M29: co-add the deep HiRISE frames and test whether the planet trace carries signal.

The extraction (M29 sec 19) gives 21 orders per frame with a wavelength solution, but the
planet is at S/N ~0.7 per pixel in a single 1200 s exposure -- below its own error bar. Two
questions follow, and only the second is about beta Pic b:

  1. Is there ANY real spectral signal on the planet trace, or is it noise at a position?
  2. If there is, what velocity does it carry?

This answers (1), which must come first. The test uses the night's own structure: the 30 s
frames are the HOST down the same fibre minutes earlier (M29 sec 16), so they carry the same
telluric absorption through the same atmosphere and the same instrument profile. Tellurics
sit at rest in the observer frame in both.

So: co-add the deep frames, co-add the host frames, and cross-correlate them. A peak near
zero velocity means the planet trace carries real atmospheric+instrumental structure and the
extraction is landing on sky, not on a detector artefact. No peak means the trace is noise.

This is deliberately a test of the EXTRACTION, not a detection of the companion -- a peak
proves shared tellurics, which any real on-sky spectrum has.

Usage (WSL): python m29_hirise_ccf.py [reddir]
"""
import glob
import os
import sys

import numpy as np
from astropy.io import fits

C_KMS = 299792.458


def load(path):
    """Return {order_key: (wl_nm, flux, err)} for one extraction."""
    out = {}
    with fits.open(path) as h:
        for e in h[1:]:
            if e.data is None:
                continue
            for c in e.data.columns.names:
                if not c.endswith("_SPEC"):
                    continue
                base = c[:-5]
                try:
                    wl = np.asarray(e.data[base + "_WL"], float)
                    fl = np.asarray(e.data[c], float)
                    er = np.asarray(e.data[base + "_ERR"], float)
                except KeyError:
                    continue
                g = np.isfinite(wl) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                if g.sum() > 200:
                    out[f"{e.name}:{base}"] = (wl, fl, er)
    return out


def coadd(files):
    """Inverse-variance co-add on each order's own wavelength grid (frame 1 as reference)."""
    ref = load(files[0])
    acc = {k: (w, np.zeros_like(f), np.zeros_like(f)) for k, (w, f, e) in ref.items()}
    for p in files:
        d = load(p)
        for k, (w, f, e) in d.items():
            if k not in acc:
                continue
            w0, num, den = acc[k]
            fi = np.interp(w0, w, f, left=np.nan, right=np.nan)
            ei = np.interp(w0, w, e, left=np.nan, right=np.nan)
            g = np.isfinite(fi) & np.isfinite(ei) & (ei > 0)
            num[g] += fi[g] / ei[g] ** 2
            den[g] += 1.0 / ei[g] ** 2
    return {k: (w, np.where(den > 0, num / np.maximum(den, 1e-30), np.nan),
                np.where(den > 0, 1 / np.sqrt(np.maximum(den, 1e-30)), np.nan))
            for k, (w, num, den) in acc.items()}


def norm(w, f):
    """Continuum-normalise by a low-order polynomial over finite points."""
    g = np.isfinite(f)
    if g.sum() < 100:
        return None
    x = (w - np.nanmean(w[g])) / max(np.nanstd(w[g]), 1e-9)
    try:
        c = np.polyfit(x[g], f[g], 3)
    except Exception:
        return None
    cont = np.polyval(c, x)
    with np.errstate(all="ignore"):
        r = f / cont - 1.0
    r[~np.isfinite(r)] = 0.0
    return r


def ccf(wl, a, b, vgrid):
    """Cross-correlate two normalised residual spectra on a common wavelength grid."""
    out = np.zeros(len(vgrid))
    for i, v in enumerate(vgrid):
        bs = np.interp(wl, wl * (1 + v / C_KMS), b, left=0.0, right=0.0)
        na, nb = np.linalg.norm(a), np.linalg.norm(bs)
        out[i] = float(a @ bs / (na * nb)) if na > 0 and nb > 0 else 0.0
    return out


def main():
    red = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/cr2res/red_m26/bpbhi")
    raw = os.path.expanduser("~/cr2res/raw_m26/bpbhi")
    files = sorted(glob.glob(os.path.join(red, "ext", "*_extr1D.fits")))
    short, deep = [], []
    for f in files:
        b = os.path.basename(f).split("_extr1D")[0]
        r = os.path.join(raw, b + ".fits")
        if not os.path.exists(r):
            continue
        dit = float(fits.getheader(r).get("HIERARCH ESO DET SEQ1 DIT", 0))
        (short if dit < 100 else deep).append(f)
    print(f"# host frames (short DIT): {len(short)}   planet frames (deep): {len(deep)}")
    if not short or not deep:
        print("missing one class"); return

    H, P = coadd(short), coadd(deep)
    common = sorted(set(H) & set(P))
    print(f"# orders in common: {len(common)}")

    snr_h, snr_p = [], []
    for k in common:
        for store, dd in ((snr_h, H), (snr_p, P)):
            w, f, e = dd[k]
            g = np.isfinite(f) & np.isfinite(e) & (e > 0)
            if g.sum() > 100:
                store.append(np.nanmedian(f[g] / e[g]))
    print(f"# co-added S/N per pixel: host {np.median(snr_h):.1f}   "
          f"planet {np.median(snr_p):.2f}")

    vgrid = np.arange(-150, 150.1, 1.0)
    stack = np.zeros(len(vgrid)); used = 0
    for k in common:
        w, fh, _ = H[k]
        _, fp, _ = P[k]
        a, b = norm(w, fh), norm(w, fp)
        if a is None or b is None:
            continue
        stack += ccf(w, a, b, vgrid); used += 1
    if not used:
        print("no usable orders"); return
    stack /= used
    i = int(np.argmax(stack))
    off = np.abs(vgrid) > 60
    base, sd = np.mean(stack[off]), np.std(stack[off])
    print(f"# orders cross-correlated: {used}")
    print(f"# CCF peak at v = {vgrid[i]:+.1f} km/s, height {stack[i]:.4f}")
    print(f"# off-peak baseline {base:+.4f} +- {sd:.4f}  ->  "
          f"peak significance {(stack[i]-base)/sd:.1f} sigma")
    print("#")
    print("# A peak near 0 km/s means the planet trace shares tellurics with the host,")
    print("# i.e. the extraction is on sky. It is NOT a detection of the companion.")


if __name__ == "__main__":
    main()
