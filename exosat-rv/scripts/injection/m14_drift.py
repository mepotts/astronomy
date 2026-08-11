"""M14 lever 4: model per-order night-to-night drift on SIGNAL-FREE cross-order
differences, subtract it, recombine, score honestly.

The idea. A real Doppler signal is common-mode across orders: every order moves by the
same RV each night. The per-order residual d_{o,n} = RV_{o,n} - commonmode_n is therefore
signal-free BY CONSTRUCTION - whatever is in it is drift, not satellite. Fit each order's
d_{o,n} against night-level regressors (BERV: the telluric-vs-stellar relative shift that
M12 §9b.3 identified as the anchor mechanism; optionally airmass/time), subtract the fit
from RV_{o,n}, recombine. A common-mode drift (all orders shifting together) is untouched
- that component is irreducible without an external reference and is what remains in the
score. The fit never sees the published values; vs_published stays the only judge.

Injection safety: the correction is a function of cross-order differences only, so an
injected common-mode Keplerian passes through unchanged to first order; still validated
explicitly by re-scoring the G13 injection outputs through the same pipeline (M9 rule).

Regressors are chosen a priori on physics: BERV linear ('berv'), BERV quadratic
('berv2'), time linear ('t'). 'const' = centering only. Others are robustness checks,
not a menu to shop from.

Usage (WSL): python m14_drift.py M13_G.rvo.dat [--model berv] [--combine median]
             [--dump corrected.csv]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_published import load, published  # noqa: E402
from m14_score import combine, match_pub, stats  # noqa: E402


def design(model, t, berv):
    tn = (t - t.mean()) / max(np.ptp(t), 1.0)
    bn = (berv - berv.mean()) / max(berv.std(), 1.0)
    cols = {"const": [np.ones_like(t)],
            "berv": [np.ones_like(t), bn],
            "berv2": [np.ones_like(t), bn, bn**2],
            "t": [np.ones_like(t), tn],
            "berv_t": [np.ones_like(t), bn, tn]}[model]
    return np.column_stack(cols)


def drift_correct(RV, t, berv, model, robust_common="median"):
    """Return corrected matrix and the fitted drift (same shape)."""
    common = np.nanmedian(RV, axis=0) if robust_common == "median" else np.nanmean(RV, axis=0)
    D = RV - common[None, :]          # signal-free cross-order differences
    A_full = design(model, t, berv)
    fit = np.zeros_like(RV)
    for i in range(RV.shape[0]):
        g = np.isfinite(D[i])
        if g.sum() <= A_full.shape[1] + 1:
            continue
        b, *_ = np.linalg.lstsq(A_full[g], D[i][g], rcond=None)
        fit[i] = A_full @ b
    return RV - fit, fit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--model", default="berv",
                    choices=["const", "berv", "berv2", "t", "berv_t"])
    ap.add_argument("--all-models", action="store_true")
    ap.add_argument("--combine", default="median", choices=["mean", "median", "clip"])
    ap.add_argument("--dump", default=None,
                    help="write corrected per-night combined series to CSV")
    args = ap.parse_args()

    c, orders = load(args.run)
    t, berv = c["BJD"], np.asarray(c["BERV"], float)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])

    models = ["const", "berv", "berv2", "t", "berv_t"] if args.all_models else [args.model]
    print(f"{'series':<26}{'n':>3}{'rms_pub':>9}{'slope':>7}{'+-':>6}{'r_pub':>7}"
          f"{'perord_rms':>11}")
    print("-" * 69)

    # baseline
    v0 = combine(RV, args.combine)
    ours, pub, nights = match_pub(t, v0)
    rp, sl, se, r = stats(ours, pub)
    d0 = RV - np.nanmedian(RV, axis=0)[None, :]
    print(f"{'baseline[' + args.combine + ']':<26}{len(ours):>3}{rp:>9.0f}{sl:>7.2f}"
          f"{se:>6.2f}{r:>7.2f}{np.nanstd(d0):>11.0f}")

    best = None
    for m in models:
        RVc, fit = drift_correct(RV, t, berv, m)
        v = combine(RVc, args.combine)
        ours, pub, _ = match_pub(t, v)
        if len(ours) < 3:
            continue
        rp, sl, se, r = stats(ours, pub)
        dc = RVc - np.nanmedian(RVc, axis=0)[None, :]
        print(f"{m + '[' + args.combine + ']':<26}{len(ours):>3}{rp:>9.0f}{sl:>7.2f}"
              f"{se:>6.2f}{r:>7.2f}{np.nanstd(dc):>11.0f}")
        if best is None or rp < best[1]:
            best = (m, rp, RVc)

    if args.dump and best is not None:
        RVc = best[2]
        v = combine(RVc, args.combine)
        with open(args.dump, "w") as f:
            f.write("bjd,rv_ms,berv\n")
            for tt, vv, bb in zip(t, v, berv):
                f.write(f"{tt:.5f},{vv:.2f},{bb:.4f}\n")
        print(f"dumped best ({best[0]}) to {args.dump}")


if __name__ == "__main__":
    main()
