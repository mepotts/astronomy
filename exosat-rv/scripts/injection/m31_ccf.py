"""M31: the M29 sec 20 on-sky test, applied to the HIP 65426 HiRISE nights.

Same question, same machinery, same statistics as m29_hirise_ccf.py (bpbhi benchmark:
peak at 0.0 km/s, 9.8 sigma): do the deep-frame extractions share telluric absorption
with a bright host spectrum taken down the same fibre? A peak at ~0 km/s proves the
extraction lands on sky; it is NOT a detection of the companion.

Differences from the bpbhi script, forced by these nights' structure (M31):
  - DITs come from the night's tags.tsv (classify.py wrote them), not raw headers,
    so the test survives sanctioned raw cleanup;
  - deep = the night's maximum DIT; host = short-DIT frames whose measured flux per
    second exceeds 3x the deep rate. The M30 raw probe showed the short-DIT class is
    NOT all host here: h65hi2/3 carry faint trailing short frames (sky/offset) and
    h65hi1 has no bright frame at all;
  - --host-from <other_reddir> borrows the host stack from another night (needed for
    h65hi1; tellurics sit at 0 km/s in both frames regardless of night);
  - --control cross-correlates one half of the host stack against the other -- a
    positive control of the machinery that involves no deep frame;
  - --deep-split cross-correlates one half of the deep stack against the other:
    shared sky structure (OH emission at 0 km/s) is an on-sky proof for the deep
    position that needs no host at all -- relevant because HIP 65426 b sits at
    Delta H2 = 11.14 +- 0.05 (Chauvin et al. 2017 Table F.1, papers/text/
    chauvin2017_hip65426b.txt), ~25x fainter relative to host than beta Pic b,
    so the host-vs-deep CCF may be photon-starved here.

Usage (WSL): m31_ccf.py <reddir> [--host-from <reddir2>] [--control] [--deep-split]
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


def classify(red):
    """Split a night's extr1Ds into (host_bright, deep, short_faint) by tags.tsv DIT
    and measured flux per second."""
    dits = {}
    with open(os.path.join(red, "tags.tsv")) as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4 and p[1] in ("OBS_STARING_OTHER", "OBS_NODDING_OTHER"):
                b = os.path.basename(p[0]).replace(".fits", "")
                try:
                    dits[b] = float(p[3])
                except ValueError:
                    pass
    files = sorted(glob.glob(os.path.join(red, "ext", "*_extr1D.fits")))
    rate = {}
    for f in files:
        b = os.path.basename(f).split("_extr1D")[0]
        if b not in dits:
            continue
        d = load(f)
        med = np.nanmedian([np.nanmedian(fl) for (_, fl, _) in d.values()]) if d else np.nan
        rate[f] = (dits[b], med / dits[b] if np.isfinite(med) else 0.0)
    max_dit = max((v[0] for v in rate.values()), default=None)
    deep = [f for f, v in rate.items() if v[0] == max_dit]
    deep_rate = np.median([rate[f][1] for f in deep]) if deep else np.nan
    host, faint = [], []
    for f, (dit, r) in rate.items():
        if dit == max_dit:
            continue
        (host if r > 3 * abs(deep_rate) else faint).append(f)
    return sorted(host), sorted(deep), sorted(faint), max_dit


def run_ccf(H, P, label):
    common = sorted(set(H) & set(P))
    print(f"# orders in common: {len(common)}")
    snr_h, snr_p = [], []
    for k in common:
        for store, dd in ((snr_h, H), (snr_p, P)):
            w, f, e = dd[k]
            g = np.isfinite(f) & np.isfinite(e) & (e > 0)
            if g.sum() > 100:
                store.append(np.nanmedian(f[g] / e[g]))
    print(f"# co-added S/N per pixel: A {np.median(snr_h):.1f}   B {np.median(snr_p):.2f}")
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
    i0 = int(np.argmin(np.abs(vgrid)))
    print(f"# orders cross-correlated: {used}")
    print(f"# [{label}] CCF peak at v = {vgrid[i]:+.1f} km/s, height {stack[i]:.4f}")
    print(f"# off-peak baseline {base:+.4f} +- {sd:.4f}  ->  "
          f"peak significance {(stack[i]-base)/sd:.1f} sigma")
    print(f"# [{label}] CCF at v=0: {stack[i0]:.4f}  ->  "
          f"{(stack[i0]-base)/sd:.1f} sigma")


def main():
    args = sys.argv[1:]
    control = "--control" in args
    if control:
        args.remove("--control")
    deep_split = "--deep-split" in args
    if deep_split:
        args.remove("--deep-split")
    host_from = None
    if "--host-from" in args:
        i = args.index("--host-from")
        host_from = args[i + 1]
        del args[i:i + 2]
    red = args[0]

    host, deep, faint, max_dit = classify(red)
    print(f"# {os.path.basename(red.rstrip('/'))}: host-bright {len(host)}, "
          f"deep(DIT={max_dit}) {len(deep)}, short-faint {len(faint)}")
    if host_from:
        host, _, _, _ = classify(host_from)
        print(f"# host stack borrowed from {os.path.basename(host_from.rstrip('/'))}: "
              f"{len(host)} frames")

    if control:
        if len(host) < 2:
            print("control needs >= 2 host frames"); return
        h1, h2 = host[0::2], host[1::2]
        print(f"# CONTROL: host split {len(h1)} vs {len(h2)}")
        run_ccf(coadd(h1), coadd(h2), "host-vs-host control")
        return

    if deep_split:
        if len(deep) < 2:
            print("deep split needs >= 2 deep frames"); return
        d1, d2 = deep[0::2], deep[1::2]
        print(f"# DEEP SPLIT: {len(d1)} vs {len(d2)}")
        run_ccf(coadd(d1), coadd(d2), "deep-vs-deep")
        return

    if not host or not deep:
        print("missing one class (host or deep)"); return
    run_ccf(coadd(host), coadd(deep), "host-vs-deep")
    print("#")
    print("# A peak near 0 km/s means the deep trace shares tellurics with the host,")
    print("# i.e. the extraction is on sky. It is NOT a detection of the companion.")


if __name__ == "__main__":
    main()
