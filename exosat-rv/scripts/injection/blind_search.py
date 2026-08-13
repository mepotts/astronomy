"""Blind period search on OUR from-raw series. No published values enter.

For each trial period: fit K*cos + K*sin + const (linear), compute BIC against the
constant-only model. Report the ΔBIC(P) landscape and where ~171 d ranks.
Variants: median / clip combine, with / without a BERV covariate, 18 / 17 epochs
(the 17 drops the epoch with no counterpart in the published table — identified
here only by its BJD, not by using any published number in the fit).
"""
import numpy as np
import sys
sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load, published

path = sys.argv[1]
NOD = "--nod" in sys.argv[2:]   # rows are per-nodding frames: bin within-night after combine
c, orders = load(path)
RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                        c[f"rv{o}"], np.nan) for o in orders])
med = np.nanmedian(RV, axis=0)
mad = 1.4826 * np.nanmedian(np.abs(RV - med), axis=0)
clip = np.nanmean(np.where(np.abs(RV - med) < 3 * np.maximum(mad, 200.0), RV, np.nan),
                  axis=0)
t_all, berv_all = c["BJD"], c["BERV"]
if NOD:
    from m14_score import bin_frames
    t_all, med, berv_med = bin_frames(np.asarray(t_all), med, np.asarray(berv_all, float))
    _, clip, _ = bin_frames(np.asarray(c["BJD"]), clip, np.asarray(berv_all, float))
    berv_all = berv_med

# which of our epochs has no published counterpart (report only; fits don't use pub)
pb, _, _ = published()
unmatched = [j for j, t in enumerate(t_all)
             if np.min(np.abs(pb - t)) >= 0.05]
print(f"epochs: {len(t_all)}, unmatched vs published table: "
      f"{[f'{t_all[j]-2460000:.3f}' for j in unmatched]}")


def bic_landscape(t, y, berv=None):
    g = np.isfinite(y)
    t, y = t[g], y[g]
    n = len(y)
    base_cols = [np.ones(n)]
    if berv is not None:
        base_cols.append(berv[g])
    A0 = np.column_stack(base_cols)
    b0, *_ = np.linalg.lstsq(A0, y, rcond=None)
    rss0 = np.sum((y - A0 @ b0) ** 2)
    bic0 = n * np.log(rss0 / n) + A0.shape[1] * np.log(n)

    periods = np.exp(np.linspace(np.log(5), np.log(460), 4000))
    out = []
    for P in periods:
        w = 2 * np.pi / P
        A = np.column_stack(base_cols + [np.cos(w * t), np.sin(w * t)])
        b, *_ = np.linalg.lstsq(A, y, rcond=None)
        rss = np.sum((y - A @ b) ** 2)
        bic = n * np.log(rss / n) + A.shape[1] * np.log(n)
        out.append((P, bic0 - bic, np.hypot(b[-2], b[-1])))
    return np.array(out), n


def report(label, t, y, berv=None):
    land, n = bic_landscape(t, y, berv)
    # peaks: local maxima in dBIC, separated by >5% in period
    order_ix = np.argsort(-land[:, 1])
    peaks = []
    for i in order_ix:
        P = land[i, 0]
        if all(abs(np.log(P / p)) > 0.05 for p, _, _ in peaks):
            peaks.append(tuple(land[i]))
        if len(peaks) == 6:
            break
    near171 = land[np.abs(np.log(land[:, 0] / 171.45)) < 0.06]
    best171 = near171[np.argmax(near171[:, 1])] if len(near171) else (np.nan,) * 3
    print(f"\n[{label}] n={n}")
    print("  top peaks (P d, dBIC vs const, K m/s): "
          + "  ".join(f"({p:.1f}, {d:+.1f}, {k:.0f})" for p, d, k in peaks))
    r = next((i + 1 for i, (p, _, _) in enumerate(peaks)
              if abs(np.log(p / 171.45)) < 0.06), ">6")
    print(f"  near-171d best: P={best171[0]:.1f}  dBIC={best171[1]:+.1f}  "
          f"K={best171[2]:.0f}   rank among peaks: {r}")


mean = np.nanmean(RV, axis=0)
if NOD:
    _, mean, _ = bin_frames(np.asarray(c["BJD"]), mean, np.asarray(c["BERV"], float))

# INTERNAL epoch screen (no published data): drop epochs whose across-order spread
# exceeds 3x the median spread. On the T2 series this isolates exactly BJD 2460604.821
# (7.3x median; the next-worst epoch sits at 1.16x), the same epoch the matched-only
# variant drops — but identified from our own data alone.
spread_frame = np.nanstd(RV - np.nanmedian(RV, axis=0)[None, :], axis=0)
if NOD:
    _, spread_night, _ = bin_frames(np.asarray(c["BJD"]), spread_frame,
                                    np.asarray(c["BERV"], float))
else:
    spread_night = spread_frame
bad = spread_night > 3 * np.median(spread_night[np.isfinite(spread_night)])
print(f"internal screen: dropping {bad.sum()} epoch(s) with spread >3x median: "
      f"{[f'{t-2460000:.3f}' for t, b in zip(t_all, bad) if b]}")

for label, y in (("mean", mean), ("median", med), ("clip", clip)):
    report(f"{label}, all epochs", t_all, y)
    report(f"{label}, +BERV covariate", t_all, y, berv_all)
    if bad.any():
        keep = ~bad
        report(f"{label}, internal screen", t_all[keep], y[keep])
        report(f"{label}, screened, +BERV", t_all[keep], y[keep], berv_all[keep])
    if unmatched and len(t_all) - len(unmatched) >= 5:
        keep = np.array([j for j in range(len(t_all)) if j not in unmatched])
        report(f"{label}, matched only", t_all[keep], y[keep])
        report(f"{label}, matched, +BERV", t_all[keep], y[keep], berv_all[keep])
