"""M15: turn the eta Tel B null into an injection-calibrated companion limit.

Part 1 (end-to-end check): assemble the single-epoch injection outputs
(ETR2K3_inj*, a real K=300 m/s, P=200 d Keplerian pushed through the full
pipeline via template shifts) into one series and run the same blind search the
null ran. If the machinery detects its own 300 m/s injection at rank 1, the null
on the real series is meaningful.

Part 2 (sensitivity curve): transmission is measured at ~100% with 12-23 m/s
repeatability, which licenses post-extraction injection for the grid: add
K sin(2 pi t / P + phi) to the REAL median-combine series (internal screen
applied), refit the blind-search BIC at the injected period, marginalize over
phi, and report per period the smallest K whose median dBIC clears the bar.
The bar is dBIC >= 10 AND the injected period ranking first among peaks.

Part 3: convert K_lim(P) to companion msini for M_host = 47 M_Jup.

Usage (WSL): python m15_limit.py [--assemble-only]
Writes /mnt/c/.../data/m15-limit.json and prints the tables.
"""
import glob
import json
import os
import sys

import numpy as np

SC = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection"
sys.path.insert(0, SC)
from vs_published import load  # noqa: E402

OUT = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/m15-limit.json"
G = 6.674e-11
MSUN = 1.989e30
MJUP = 1.898e27
M_HOST = 47.0 * MJUP


def assemble(arm, dest):
    files = sorted(glob.glob(f"{arm}_inj*.rvo.dat"))
    rows, hdr = [], None
    for f in files:
        lines = [ln for ln in open(f).read().splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        if hdr is None:
            hdr = lines[0]
        rows.append(lines[1])
    with open(dest, "w") as f:
        f.write(hdr + "\n" + "\n".join(rows) + "\n")
    print(f"assembled {dest}: {len(rows)} epochs")
    return dest


def series(path):
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    med = np.nanmedian(RV, axis=0)
    spread = np.nanstd(RV - med, axis=0)
    keep = spread <= 3 * np.nanmedian(spread)
    return np.asarray(c["BJD"])[keep], med[keep]


def bic_peak(t, y, P_grid):
    n = len(y)
    b0, *_ = np.linalg.lstsq(np.ones((n, 1)), y, rcond=None)
    rss0 = np.sum((y - b0[0]) ** 2)
    bic0 = n * np.log(rss0 / n) + np.log(n)
    out = []
    for P in P_grid:
        w = 2 * np.pi / P
        A = np.column_stack([np.ones(n), np.cos(w * t), np.sin(w * t)])
        b, *_ = np.linalg.lstsq(A, y, rcond=None)
        rss = np.sum((y - A @ b) ** 2)
        out.append(bic0 - (n * np.log(rss / n) + 3 * np.log(n)))
    return np.array(out)


def detected(t, y, P_inj, grid):
    d = bic_peak(t, y, grid)
    i_inj = np.argmin(np.abs(np.log(grid / P_inj)))
    near = np.abs(np.log(grid / P_inj)) < 0.06
    best_near = d[near].max()
    return best_near >= 10 and best_near >= d.max() - 0.01


def msini_mjup(K, P_days):
    P = P_days * 86400.0
    return (K * (M_HOST) ** (2 / 3) * (P / (2 * np.pi * G)) ** (1 / 3)) / MJUP


def main():
    print("[1] end-to-end: blind search on the assembled K=300/P=200 injection")
    dest = assemble("ETR2K3", "ETR2K3_series.rvo.dat")
    os.system(f"~/viperenv/bin/python {SC}/blind_search.py {dest} 2>&1 | "
              f"grep -A3 'internal screen\\]' | head -20")

    print("\n[2] sensitivity curve on the real series (post-extraction grid)")
    t, y = series("E15_R2.rvo.dat")
    print(f"  base series: n={len(y)} rms={np.std(y):.0f} m/s")
    grid = np.exp(np.linspace(np.log(5), np.log(460), 2000))
    periods = [20.0, 60.0, 120.0, 200.0, 300.0]
    Ks = [60, 90, 120, 150, 200, 250, 300, 400]
    phis = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    table = {}
    for P in periods:
        frac = []
        for K in Ks:
            hits = sum(detected(t, y + K * np.sin(2 * np.pi * t / P + ph), P, grid)
                       for ph in phis)
            frac.append(hits / len(phis))
        table[P] = dict(zip(Ks, frac))
        lim = next((K for K, f in zip(Ks, frac) if f >= 0.9), None)
        msini = f"{msini_mjup(lim, P):.1f}" if lim else ">4-equivalent"
        print(f"  P={P:5.0f} d: det frac {['%.2f' % f for f in frac]}  "
              f"K90={lim}  msini_lim={msini} MJup")

    json.dump({"periods": periods, "Ks": Ks, "detfrac": table,
               "note": "det = dBIC>=10 AND top peak at injected period; "
                       "phi marginalized over 12 phases; series = E15_R2 median, "
                       "internal 3x screen"},
              open(OUT, "w"), indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
