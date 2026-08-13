"""M28: leave-one-out robustness of the CD-35 2722 B period detection.

A referee's first question about a 17-epoch detection is whether one night carries it.
This drops each epoch in turn and re-runs the identical blind search (median combine,
internal screen already applied, with and without the BERV covariate), reporting the
peak period and dBIC each time.

Usage (WSL): python m28_jackknife.py [series.rvo.dat]
"""
import sys

import numpy as np

SC = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection"
sys.path.insert(0, SC)
from m28_nullcal import series, qr_bank, landscape, P_REF, LOG_TOL  # noqa: E402


def peak(t, y, berv, grid, use_berv):
    g = np.isfinite(y)
    t, y = t[g], y[g]
    base = [np.ones(len(y))] + ([berv[g]] if use_berv else [])
    Q0, bank, _ = qr_bank(t, grid, base)
    land = landscape(Q0, bank, y[:, None], len(y), len(base))[:, 0]
    i = int(np.argmax(land))
    near = np.abs(np.log(grid / P_REF)) < LOG_TOL
    return grid[i], land[i], land[near].max()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "M14_NODT2.rvo.dat"
    t, med, clip, berv, bad, _ = series(path)
    keep = ~bad if bad.any() else np.ones(len(t), bool)
    t, y, berv = t[keep], med[keep], berv[keep]
    grid = np.exp(np.linspace(np.log(5), np.log(460), 4000))
    n = len(t)
    print(f"# leave-one-out on {path}: n={n}, median combine, internal screen applied")
    P0, d0, r0 = peak(t, y, berv, grid, False)
    P1, d1, r1 = peak(t, y, berv, grid, True)
    print(f"# full series: plain peak P={P0:.2f} dBIC={d0:+.2f} | "
          f"+BERV peak P={P1:.2f} dBIC={d1:+.2f}\n")
    print(f"# {'dropped':>10s} {'BJD-2460000':>12s} | {'plainP':>8s} {'plaindBIC':>10s} "
          f"| {'bervP':>8s} {'bervdBIC':>9s} {'near171':>9s}")
    rows = []
    for j in range(n):
        m = np.ones(n, bool)
        m[j] = False
        Pa, da, _ = peak(t[m], y[m], berv[m], grid, False)
        Pb, db, rb = peak(t[m], y[m], berv[m], grid, True)
        rows.append((Pa, da, Pb, db, rb))
        flag = "" if abs(np.log(Pb / P_REF)) < LOG_TOL else "   <-- peak moves off 171 d"
        print(f"  {'epoch ' + str(j):>10s} {t[j] - 2460000:>12.3f} | {Pa:>8.2f} "
              f"{da:>+10.2f} | {Pb:>8.2f} {db:>+9.2f} {rb:>+9.2f}{flag}")
    a = np.array(rows)
    print(f"\n# plain  dBIC across the {n} jackknifes: min {a[:, 1].min():+.2f} "
          f"max {a[:, 1].max():+.2f}   peak within 6% of 171 d in "
          f"{int(np.sum(np.abs(np.log(a[:, 0] / P_REF)) < LOG_TOL))}/{n}")
    print(f"# +BERV dBIC across the {n} jackknifes: min {a[:, 3].min():+.2f} "
          f"max {a[:, 3].max():+.2f}   peak within 6% of 171 d in "
          f"{int(np.sum(np.abs(np.log(a[:, 2] / P_REF)) < LOG_TOL))}/{n}")


if __name__ == "__main__":
    main()
