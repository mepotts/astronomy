#!/usr/bin/env python3
"""M3 seam (a) machinery validation on M2's already-finished J1017-7156 chain
(the known A-beta ridge case, M2 doc 4.1) before M3's own posteriors exist.

Checks: (i) the ridge is there; (ii) importance reweighting to a narrower beta
prior is numerically sane (ESS, weight concentration); (iii) the S5 fairness
control - EFAC must not move when only the beta prior changes.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PSR = sys.argv[1] if len(sys.argv) > 1 else "J1017-7156"
CH = REPO / "chains" / "m2" / f"{PSR}_noise_c1" / "chain_1.txt"
SUM = REPO / "results" / "m2" / f"{PSR}_noise_c1.summary.json"

ALT = {"U(0,10)": (0, 10), "U(0,7)": (0, 7), "U(2,6)": (2, 6)}


def wmed(x, w):
    i = np.argsort(x)
    x, w = x[i], w[i]
    return float(np.interp(0.5, np.cumsum(w) / w.sum(), x))


def main():
    s = json.loads(SUM.read_text())
    names = [r["param"] for r in s["chain"]["params"]]
    ch = np.loadtxt(CH, ndmin=2)
    ndim = len(names)
    post = ch[len(ch) // 4:, :ndim]
    idx = {n.replace(f"{PSR}_", ""): i for i, n in enumerate(names)}
    a, g, b = (post[:, idx["chrom_gp_log10_A"]], post[:, idx["chrom_gp_gamma"]],
               post[:, idx["chrom_gp_idx"]])
    ef = post[:, idx["efac"]]
    a13 = post[:, idx["gw13_log10_A"]]
    print(f"post-burn samples {len(post)}")
    print(f"S1 ridge: r(A, beta) = {np.corrcoef(a, b)[0,1]:+.3f}, "
          f"slope {np.polyfit(b, a, 1)[0]:+.3f} dex per unit beta; "
          f"r(A, gamma) = {np.corrcoef(a, g)[0,1]:+.3f}")
    print(f"S2 beta: median {np.median(b):.2f} 68% "
          f"[{np.percentile(b,16):.2f}, {np.percentile(b,84):.2f}] "
          f"= {(np.percentile(b,84)-np.percentile(b,16))/14*100:.0f}% of the "
          f"U(0,14) prior; 95% "
          f"[{np.percentile(b,2.5):.2f}, {np.percentile(b,97.5):.2f}]")
    print(f"baseline medians: A {np.median(a):.3f}  gamma {np.median(g):.3f}  "
          f"EFAC {np.median(ef):.4f}  A13/3 {np.median(a13):.3f}")
    for lab, (lo, hi) in ALT.items():
        w = ((b >= lo) & (b <= hi)).astype(float)
        if w.sum() == 0:
            print(f"  {lab}: no samples in support")
            continue
        w /= w.sum()
        ess = 1.0 / np.sum(w ** 2)
        print(f"  {lab}: ESS {ess:8.0f}  dA {wmed(a,w)-np.median(a):+.3f}  "
              f"dgamma {wmed(g,w)-np.median(g):+.3f}  "
              f"dbeta {wmed(b,w)-np.median(b):+.3f}  "
              f"dEFAC {wmed(ef,w)-np.median(ef):+.5f}  "
              f"dA13/3 {wmed(a13,w)-np.median(a13):+.3f}")
    pub = json.loads((REPO / "results/m3/published_table.json").read_text())
    pa = pub[PSR]["pub"]["chrom_log10_A"]
    print(f"published A_Chrom {pa[0]} ({pa[1]:+}, {pa[2]:+}) -> 68% half-width "
          f"{(abs(pa[1])+abs(pa[2]))/2:.3f} dex (the S4 threshold)")


if __name__ == "__main__":
    main()
