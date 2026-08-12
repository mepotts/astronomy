"""Export the final M14/M15 series + blind-search landscapes to CSVs for the paper.

Runs in WSL (reads ~/viper-src rvo files), writes to data/export/ on the repo side.

Products:
  cd35_series.csv       binned per-nodding nights (NODT2): bjd, rv_med, rv_mean, pub, epub
  cd35_landscape.csv    dBIC(P) for the screened series, with and without BERV (mean combine)
  etatel_series.csv     binned per-nodding nights (E15_NOD): bjd, rv_med, rv_mean, screened flag
  etatel_landscape.csv  dBIC(P) with/without BERV (median combine, screened)
"""
import os
import sys

import numpy as np

SC = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection"
sys.path.insert(0, SC)
from vs_published import load, published  # noqa: E402
from m14_score import bin_frames  # noqa: E402

OUT = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/export"
os.makedirs(OUT, exist_ok=True)


def series(path, nod=True):
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    med = np.nanmedian(RV, axis=0)
    mean = np.nanmean(RV, axis=0)
    spread = np.nanstd(RV - med, axis=0)
    t = np.asarray(c["BJD"], float)
    berv = np.asarray(c["BERV"], float)
    if nod:
        tb, medb, bervb = bin_frames(t, med, berv)
        _, meanb, _ = bin_frames(t, mean, berv)
        _, spreadb, _ = bin_frames(t, spread, berv)
        return tb, medb, meanb, spreadb, bervb
    return t, med, mean, spread, berv


def landscape(t, y, berv=None, lo=5, hi=460, n=3000):
    g = np.isfinite(y)
    t, y = t[g], y[g]
    nn = len(y)
    cols = [np.ones(nn)] + ([berv[g]] if berv is not None else [])
    A0 = np.column_stack(cols)
    b0, *_ = np.linalg.lstsq(A0, y, rcond=None)
    bic0 = nn * np.log(np.sum((y - A0 @ b0) ** 2) / nn) + A0.shape[1] * np.log(nn)
    P = np.exp(np.linspace(np.log(lo), np.log(hi), n))
    out = np.empty_like(P)
    for i, p in enumerate(P):
        w = 2 * np.pi / p
        A = np.column_stack(cols + [np.cos(w * t), np.sin(w * t)])
        b, *_ = np.linalg.lstsq(A, y, rcond=None)
        out[i] = bic0 - (nn * np.log(np.sum((y - A @ b) ** 2) / nn)
                         + A.shape[1] * np.log(nn))
    return P, out


# ---- CD-35: NODT2 binned, matched to published ----
t, med, mean, spread, berv = series(os.path.expanduser("~/viper-src/M14_NODT2.rvo.dat"))
pb, pv, pe = published()
rows = []
for i, tt in enumerate(t):
    j = np.argmin(np.abs(pb - tt))
    match = abs(pb[j] - tt) < 0.05
    rows.append((tt, med[i], mean[i], spread[i],
                 pv[j] if match else np.nan, pe[j] if match else np.nan))
with open(f"{OUT}/cd35_series.csv", "w") as f:
    f.write("bjd,rv_med,rv_mean,spread,pub,epub\n")
    for r in rows:
        f.write(",".join(f"{x:.3f}" for x in r) + "\n")
print(f"cd35_series: {len(rows)} nights")

keep = spread <= 3 * np.nanmedian(spread)
P, d0 = landscape(t[keep], mean[keep])
_, d1 = landscape(t[keep], mean[keep], berv[keep])
with open(f"{OUT}/cd35_landscape.csv", "w") as f:
    f.write("P_d,dbic,dbic_berv\n")
    for a, b, c2 in zip(P, d0, d1):
        f.write(f"{a:.4f},{b:.3f},{c2:.3f}\n")
print("cd35_landscape written")

# ---- eta Tel: E15_NOD binned ----
t, med, mean, spread, berv = series(os.path.expanduser("~/viper-src/E15_NOD.rvo.dat"))
keep = spread <= 3 * np.nanmedian(spread)
with open(f"{OUT}/etatel_series.csv", "w") as f:
    f.write("bjd,rv_med,rv_mean,spread,kept\n")
    for i, tt in enumerate(t):
        f.write(f"{tt:.3f},{med[i]:.3f},{mean[i]:.3f},{spread[i]:.3f},{int(keep[i])}\n")
print(f"etatel_series: {len(t)} nights ({keep.sum()} kept)")

P, d0 = landscape(t[keep], med[keep])
_, d1 = landscape(t[keep], med[keep], berv[keep])
with open(f"{OUT}/etatel_landscape.csv", "w") as f:
    f.write("P_d,dbic,dbic_berv\n")
    for a, b, c2 in zip(P, d0, d1):
        f.write(f"{a:.4f},{b:.3f},{c2:.3f}\n")
print("etatel_landscape written")
