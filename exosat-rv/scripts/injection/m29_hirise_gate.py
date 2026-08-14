"""M29: the velocity gate for the HiRISE (fibre) extraction path.

This project's standing rule is that no limit or detection counts until injection recovery
has measured the pipeline's velocity transmission. That has been done for the slit path and
says nothing about the fibre path, which uses different recipes entirely (util_calib ->
util_trace -> util_extract).

The slit-path gate shifts a template and re-runs the fit. That does not transfer: the util_*
chain performs no fit and knows nothing about velocity -- it extracts flux against
wavelength. So the fibre path is gated two ways, both measured here:

  ARM 1, TRANSMISSION.  Take a real extracted spectrum, shift it by a known velocity,
  cross-correlate against the unshifted original, and recover the shift. This tests the
  wavelength solution and the correlation machinery end to end. Recovery should be ~100%
  and the residual sets the method floor.

  ARM 2, REPEATABILITY.  Cross-correlate each host frame against the co-added host. The 30
  host frames span about an hour, over which BERV moves by well under 100 m/s, so their
  frame-to-frame velocity scatter IS the path's per-frame RV precision. This is the number
  that decides whether a companion velocity is reachable, and nothing else in this project
  measures it for fibre data.

Arm 2 is the honest one: arm 1 can only fail if the arithmetic is wrong, while arm 2
includes every real instability the path has.

Usage (WSL): python m29_hirise_gate.py [reddir]
"""
import glob
import os
import sys

import numpy as np
from astropy.io import fits

C_KMS = 299792.458


def load(path):
    out = {}
    with fits.open(path) as h:
        for e in h[1:]:
            if e.data is None:
                continue
            for c in e.data.columns.names:
                if not c.endswith("_SPEC"):
                    continue
                b = c[:-5]
                try:
                    wl = np.asarray(e.data[b + "_WL"], float)
                    fl = np.asarray(e.data[c], float)
                    er = np.asarray(e.data[b + "_ERR"], float)
                except KeyError:
                    continue
                g = np.isfinite(wl) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                if g.sum() > 200:
                    out[f"{e.name}:{b}"] = (wl, fl, er)
    return out


def norm(w, f):
    g = np.isfinite(f)
    if g.sum() < 100:
        return None
    x = (w - np.nanmean(w[g])) / max(np.nanstd(w[g]), 1e-9)
    try:
        c = np.polyfit(x[g], f[g], 3)
    except Exception:
        return None
    r = f / np.polyval(c, x) - 1.0
    r[~np.isfinite(r)] = 0.0
    return r


def ccf_peak(wl, a, b, vmax=40.0, dv=0.25):
    """Cross-correlate and return the parabola-refined peak velocity in km/s."""
    v = np.arange(-vmax, vmax + dv, dv)
    cc = np.empty(len(v))
    na = np.linalg.norm(a)
    for i, vv in enumerate(v):
        bs = np.interp(wl, wl * (1 + vv / C_KMS), b, left=0.0, right=0.0)
        nb = np.linalg.norm(bs)
        cc[i] = float(a @ bs / (na * nb)) if na > 0 and nb > 0 else 0.0
    i = int(np.argmax(cc))
    if 0 < i < len(v) - 1:
        y0, y1, y2 = cc[i - 1], cc[i], cc[i + 1]
        d = y0 - 2 * y1 + y2
        if d != 0:
            return v[i] - 0.5 * dv * (y2 - y0) / d, cc[i]
    return v[i], cc[i]


def coadd(files, keys=None):
    ref = load(files[0])
    acc = {k: (w, np.zeros_like(f), np.zeros_like(f)) for k, (w, f, e) in ref.items()}
    for p in files:
        for k, (w, f, e) in load(p).items():
            if k not in acc:
                continue
            w0, num, den = acc[k]
            fi = np.interp(w0, w, f, left=np.nan, right=np.nan)
            ei = np.interp(w0, w, e, left=np.nan, right=np.nan)
            g = np.isfinite(fi) & np.isfinite(ei) & (ei > 0)
            num[g] += fi[g] / ei[g] ** 2
            den[g] += 1.0 / ei[g] ** 2
    return {k: (w, np.where(den > 0, num / np.maximum(den, 1e-30), np.nan))
            for k, (w, num, den) in acc.items()}


def main():
    red = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/cr2res/red_m26/bpbhi")
    raw = os.path.expanduser("~/cr2res/raw_m26/bpbhi")
    short = []
    for f in sorted(glob.glob(os.path.join(red, "ext", "*_extr1D.fits"))):
        b = os.path.basename(f).split("_extr1D")[0]
        r = os.path.join(raw, b + ".fits")
        if os.path.exists(r) and float(
                fits.getheader(r).get("HIERARCH ESO DET SEQ1 DIT", 0)) < 100:
            short.append(f)
    print(f"# host frames: {len(short)}")
    if len(short) < 5:
        print("too few"); return

    REF = coadd(short)
    keys = [k for k in REF if norm(*REF[k]) is not None]
    print(f"# usable orders: {len(keys)}")

    # ---- ARM 1: known-shift recovery -------------------------------------
    print("\n# ARM 1 -- transmission: recover a numerically imposed shift")
    print(f"  {'injected':>9s} {'recovered':>10s} {'recovery':>9s}")
    for vin in (-5.0, -1.0, 1.0, 5.0, 15.0):
        outs = []
        for k in keys:
            w, f = REF[k]
            a = norm(w, f)
            shifted = np.interp(w, w * (1 + vin / C_KMS), a, left=0.0, right=0.0)
            v, _ = ccf_peak(w, a, shifted, vmax=abs(vin) + 25)
            outs.append(-v)
        m = float(np.median(outs))
        print(f"  {vin:>+9.2f} {m:>+10.3f} {100*m/vin:>8.1f}%")

    # ---- ARM 2: frame-to-frame repeatability -----------------------------
    print("\n# ARM 2 -- repeatability: each host frame against the co-add")
    vs = []
    for p in short:
        d = load(p)
        per = []
        for k in keys:
            if k not in d:
                continue
            w, f = REF[k]
            a = norm(w, f)
            b = norm(d[k][0], np.interp(w, d[k][0], d[k][1], left=np.nan, right=np.nan))
            if a is None or b is None:
                continue
            v, _ = ccf_peak(w, a, b, vmax=25.0)
            per.append(v)
        if per:
            vs.append(float(np.median(per)))
    vs = np.array(vs)
    print(f"  frames measured: {len(vs)}")
    print(f"  median velocity : {np.median(vs)*1000:+8.1f} m/s")
    print(f"  scatter (rms)   : {np.std(vs, ddof=1)*1000:8.1f} m/s")
    print(f"  robust (1.48 MAD): {1.4826*np.median(np.abs(vs-np.median(vs)))*1000:7.1f} m/s")
    print(f"  min / max       : {vs.min()*1000:+.1f} / {vs.max()*1000:+.1f} m/s")
    print("\n# Arm 2 is the path's per-frame RV precision on a bright target. BERV moves")
    print("# by well under 100 m/s across this hour, so the scatter is instrumental plus")
    print("# photon noise, not astrophysical.")


if __name__ == "__main__":
    main()
