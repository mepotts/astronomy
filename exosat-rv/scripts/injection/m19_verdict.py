"""M19 verdict: the beta Pic b 4-epoch series — variability test + K exclusion.

With four epochs a blind period search is over-parameterized (3 fit params), so the
honest statistics are: (1) is the night-binned series consistent with constant RV,
given per-night errors? (2) what companion amplitude K would, at 90% of phases, have
produced more night-to-night scatter than observed? The second is licensed by the
measured ~100% transmission (M17/M19 injection arms): add K sin(2πt/P + φ) to the
real binned series, compare its std against the observed std.

Usage (WSL, ~/viper-src): python m19_verdict.py M19_BPB.rvo.dat
"""
import sys

import numpy as np

sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load  # noqa: E402
from m14_score import bin_frames  # noqa: E402

path = sys.argv[1]
c, orders = load(path)
RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                        c[f"rv{o}"], np.nan) for o in orders])
med = np.nanmedian(RV, axis=0)
spread = np.nanstd(RV - med, axis=0)
t = np.asarray(c["BJD"], float)
berv = np.asarray(c["BERV"], float)

tb, vb, _ = bin_frames(t, med, berv)
# per-night error: frame-level across-order scatter propagated through the combine
_, sb, _ = bin_frames(t, spread / np.sqrt(max(len(orders), 1)), berv)
nb, counts = [], []
i = np.argsort(t)
groups, cur = [], [i[0]]
for j in i[1:]:
    (cur.append(j) if t[j] - t[cur[-1]] < 0.2 else (groups.append(cur), cur := [j]))
groups.append(cur)
counts = np.array([len(g) for g in groups])
errs = sb / np.sqrt(counts)

print(f"nights: {len(tb)}  baseline {tb.max() - tb.min():.0f} d")
for tt, vv, ee, nn in zip(tb, vb, errs, counts):
    print(f"  BJD {tt:.3f}  RV {vv:8.1f} +- {ee:5.1f} m/s   ({nn} frames)")

v0 = vb - np.average(vb, weights=1 / errs**2)
chi2 = float(np.sum(v0**2 / errs**2))
dof = len(vb) - 1
obs_std = float(np.std(vb, ddof=1))
print(f"\nconstant-RV test: chi2 = {chi2:.1f} / {dof} dof   "
      f"night-to-night std = {obs_std:.0f} m/s")

print("\nK exclusion by variance (90% of phases would exceed observed std):")
rng = np.random.default_rng(7)
for P in (20.0, 50.0, 100.0, 200.0, 400.0):
    lo = None
    for K in (100, 150, 200, 250, 300, 400, 500, 700, 1000):
        phis = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        exceed = sum(np.std(vb + K * np.sin(2 * np.pi * tb / P + ph), ddof=1) > obs_std
                     for ph in phis) / len(phis)
        if exceed >= 0.9:
            lo = K
            break
    print(f"  P = {P:5.0f} d:  K90 ≈ {lo if lo else '>1000'} m/s")
