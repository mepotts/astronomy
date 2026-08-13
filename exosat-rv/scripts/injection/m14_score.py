"""M14 scorer: per-order centering, robust combines, and per-nodding A/B binning.

Extends median_test.py with two operations, both blind to the published values:

* --center : subtract each order's own median ACROSS NIGHTS before combining.
  Removes the *static* part of the per-order zero-points, so the median over orders
  mixes orders instead of repeatedly electing the same central ones. Signal-safe by
  construction: it subtracts one constant per order (the signal is common-mode across
  orders, so the constant contains the same signal mean for every order and shifts
  the combined series by ~one constant, which the scorer removes anyway). Injection
  validation still required before adopting (M9 rule) — re-scorable on the existing
  G13 injection outputs without new viper runs.

* --nod : treat rows as per-nodding FRAMES; after combining orders per frame, bin
  frames within 0.2 d of each other (A+B of one night) by plain mean. The paper's
  favoured extraction ("Binned Separate Nodding RVs", its Fig. 4).

* --ref RUN.rvo.dat : also score the reference run restricted to the SAME matched
  nights, so a 5-night nod run compares paired against M13_G's same 5 epochs.

Usage examples (WSL):
  python m14_score.py M13_G.rvo.dat --center
  python m14_score.py M14_nod.rvo.dat --nod --ref M13_G.rvo.dat
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_published import load, published  # noqa: E402

pb, pv, pe = published()


def order_matrix(path):
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    return c["BJD"], np.asarray(c["BERV"], float), RV, orders


def combine(RV, how):
    if how == "mean":
        return np.nanmean(RV, axis=0)
    if how == "median":
        return np.nanmedian(RV, axis=0)
    med = np.nanmedian(RV, axis=0)
    mad = 1.4826 * np.nanmedian(np.abs(RV - med), axis=0)
    keep = np.abs(RV - med) < 3 * np.maximum(mad, 200.0)
    return np.nanmean(np.where(keep, RV, np.nan), axis=0)


def bin_frames(t, v, berv, tol=0.2):
    """Group frames closer than tol days; plain mean per group."""
    i = np.argsort(t)
    t, v, berv = t[i], v[i], berv[i]
    groups, cur = [], [0]
    for j in range(1, len(t)):
        if t[j] - t[cur[-1]] < tol:
            cur.append(j)
        else:
            groups.append(cur); cur = [j]
    groups.append(cur)
    tb = np.array([t[g].mean() for g in groups])
    vb = np.array([np.nanmean(v[g]) for g in groups])
    bb = np.array([np.nanmean(berv[g]) for g in groups])
    return tb, vb, bb


def match_pub(t, v, restrict=None):
    ours, pub, keep_t = [], [], []
    for tt, x in zip(t, v):
        if not np.isfinite(x):
            continue
        i = np.argmin(np.abs(pb - tt))
        if abs(pb[i] - tt) >= 0.05:
            continue
        if restrict is not None and np.min(np.abs(restrict - pb[i])) > 1e-6:
            continue
        ours.append(x); pub.append(pv[i]); keep_t.append(pb[i])
    return np.array(ours), np.array(pub), np.array(keep_t)


def stats(ours, pub):
    d = ours - pub
    rms_pub = np.std(d - d.mean(), ddof=0)
    A = np.column_stack([pub, np.ones_like(pub)])
    b, *_ = np.linalg.lstsq(A, ours, rcond=None)
    sig2 = np.sum((ours - A @ b) ** 2) / max(len(ours) - 2, 1)
    se = np.sqrt(sig2 * np.linalg.inv(A.T @ A)[0, 0])
    r = np.corrcoef(pub, ours)[0, 1] if len(ours) > 2 else np.nan
    return rms_pub, b[0], se, r


def series_for(path, how, center, nod):
    t, berv, RV, orders = order_matrix(path)
    if center:
        RV = RV - np.nanmedian(RV, axis=1, keepdims=True)
    v = combine(RV, how)
    if nod:
        t, v, berv = bin_frames(t, v, berv)
    return t, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--center", action="store_true")
    ap.add_argument("--nod", action="store_true")
    ap.add_argument("--ref", default=None,
                    help="reference rvo scored on the same matched nights")
    ap.add_argument("--both", action="store_true",
                    help="show centered AND uncentered variants")
    args = ap.parse_args()

    variants = [(False, "raw"), (True, "ctr")] if args.both else \
               [(args.center, "ctr" if args.center else "raw")]

    print(f"{'series':<34}{'n':>3}{'rms_pub':>9}{'slope':>7}{'+-':>6}{'r_pub':>7}")
    print("-" * 66)
    matched_nights = None
    for center, cname in variants:
        for how in ("mean", "median", "clip"):
            t, v = series_for(args.run, how, center, args.nod)
            ours, pub, nights = match_pub(t, v)
            if matched_nights is None:
                matched_nights = nights
            if len(ours) < 3:
                print(f"{args.run}[{cname},{how}]  n={len(ours)} too few")
                continue
            rp, sl, se, r = stats(ours, pub)
            print(f"{os.path.basename(args.run)+'['+cname+','+how+']':<34}"
                  f"{len(ours):>3}{rp:>9.0f}{sl:>7.2f}{se:>6.2f}{r:>7.2f}")

    if args.ref and matched_nights is not None and len(matched_nights) >= 3:
        print(f"\nreference on the same {len(matched_nights)} nights:")
        for center, cname in [(False, "raw"), (True, "ctr")]:
            for how in ("mean", "median", "clip"):
                t, v = series_for(args.ref, how, center, False)
                ours, pub, _ = match_pub(t, v, restrict=matched_nights)
                if len(ours) < 3:
                    continue
                rp, sl, se, r = stats(ours, pub)
                print(f"{os.path.basename(args.ref)+'['+cname+','+how+']':<34}"
                      f"{len(ours):>3}{rp:>9.0f}{sl:>7.2f}{se:>6.2f}{r:>7.2f}")


if __name__ == "__main__":
    main()
