"""M29: telluric removal on the HiRISE pair, and what survives it.

M29 sec 20 found a 9.8 sigma cross-correlation between the planet trace and the host at
exactly 0 km/s. That proved the extraction is on sky, but the peak is MADE of the tellurics
that any companion measurement must first divide out.

The night supplies its own reference: the host went down the same fibre minutes earlier,
through the same atmosphere and instrument, so its spectrum carries the same telluric
absorption and the same instrument profile. Dividing the planet by the host should therefore
remove both.

The test is falsifiable in the right direction. If the division works, the 0 km/s peak must
COLLAPSE -- there is nothing left to correlate. If the peak survives, the removal has failed
and nothing downstream can be trusted.

What division leaves behind, and why no detection is claimed here:
  - the ratio of the two SEDs (smooth, removed by continuum normalisation);
  - the HOST's own photospheric lines, imprinted inverted. beta Pic is A6V, so in H band
    that is mainly the Brackett series -- few lines, but real;
  - the planet's own lines, Doppler-shifted by its systemic plus orbital velocity;
  - noise, amplified wherever the host spectrum is small (deep telluric cores).

Usage (WSL): python m29_hirise_telluric.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

C_KMS = 299792.458
RED = os.path.expanduser("~/cr2res/red_m26/bpbhi")
RAW = os.path.expanduser("~/cr2res/raw_m26/bpbhi")


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


def coadd(files):
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


def ccf(w, a, b, vmax=150.0, dv=1.0):
    v = np.arange(-vmax, vmax + dv, dv)
    cc = np.zeros(len(v))
    na = np.linalg.norm(a)
    for i, vv in enumerate(v):
        bs = np.interp(w, w * (1 + vv / C_KMS), b, left=0.0, right=0.0)
        nb = np.linalg.norm(bs)
        cc[i] = float(a @ bs / (na * nb)) if na > 0 and nb > 0 else 0.0
    return v, cc


def report(label, v, stack):
    i = int(np.argmax(stack))
    off = np.abs(v) > 60
    base, sd = np.mean(stack[off]), np.std(stack[off])
    sig = (stack[i] - base) / sd if sd > 0 else np.nan
    print(f"  {label:<34s} peak v={v[i]:+7.1f} km/s  height={stack[i]:+.4f}  "
          f"significance={sig:5.1f} sigma")
    return sig


def main():
    short, deep = [], []
    for f in sorted(glob.glob(os.path.join(RED, "ext", "*_extr1D.fits"))):
        b = os.path.basename(f).split("_extr1D")[0]
        r = os.path.join(RAW, b + ".fits")
        if not os.path.exists(r):
            continue
        dit = float(fits.getheader(r).get("HIERARCH ESO DET SEQ1 DIT", 0))
        (short if dit < 100 else deep).append(f)
    # drop the fibre-transition frames identified in M29 sec 21 by timestamp
    keep = []
    for f in short:
        b = os.path.basename(f).split("_extr1D")[0]
        mjd = float(fits.getheader(os.path.join(RAW, b + ".fits")).get("MJD-OBS", 0))
        if mjd < 60708.1560:
            keep.append(f)
    print(f"# host frames {len(short)} -> {len(keep)} after dropping the fibre-transition "
          f"window;  planet frames {len(deep)}")

    H, P = coadd(keep), coadd(deep)
    common = sorted(set(H) & set(P))
    print(f"# orders in common: {len(common)}\n")

    v = None
    raw_stack = np.zeros(301); div_stack = np.zeros(301); n = 0
    for k in common:
        w, fh = H[k]
        _, fp = P[k]
        a = norm(w, fh)
        b_raw = norm(w, fp)
        # telluric removal: ratio of the raw co-added fluxes, then normalise
        with np.errstate(all="ignore"):
            ratio = np.where(np.abs(fh) > 1e-6, fp / fh, np.nan)
        b_div = norm(w, ratio)
        if a is None or b_raw is None or b_div is None:
            continue
        v, c1 = ccf(w, a, b_raw)
        _, c2 = ccf(w, a, b_div)
        raw_stack += c1; div_stack += c2; n += 1
    raw_stack /= n; div_stack /= n
    print(f"# cross-correlated against the host, {n} orders")
    s1 = report("planet, tellurics PRESENT", v, raw_stack)
    s2 = report("planet / host, tellurics REMOVED", v, div_stack)
    print()
    if np.isfinite(s1) and np.isfinite(s2):
        print(f"# the telluric peak drops {s1:.1f} -> {s2:.1f} sigma "
              f"({100*(1-s2/s1):.0f}% of the correlation removed)")
    print("#")
    print("# A collapse is the PASS condition: it means the host reference removed the")
    print("# shared atmosphere. It is not evidence about the companion, which would appear")
    print("# displaced from 0 km/s and requires an atmosphere template this project lacks.")


if __name__ == "__main__":
    main()
