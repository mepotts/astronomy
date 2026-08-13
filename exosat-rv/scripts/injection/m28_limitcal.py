"""M28: calibrate the detection bar behind the eta Tel B companion limit.

M15 defines a detection as "dBIC >= 10 at the injected period AND that peak ranks
first". The rank-1 clause carries most of the protection, but the dBIC >= 10 bar was
never calibrated: m28_nullcal.py shows a signal-free series with this sampling reaches
max dBIC ~ 19 at the 95th percentile, so 10 is well inside the noise.

This measures the false-alarm probability of the criterion as written, finds the bar
that actually delivers 5% and 1% FAP, and re-derives K90 at each bar with a finer phase
and amplitude grid than M15 used (12 phases -> 36, 8 amplitudes -> 19).

Null realizations permute the real series against fixed epoch times: signal-free by
construction, with the true sampling, value distribution and window function preserved.

Usage (WSL): python m28_limitcal.py [series.rvo.dat] [--nperm N]
"""
import sys

import numpy as np

SC = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection"
sys.path.insert(0, SC)
from vs_published import load  # noqa: E402

G = 6.674e-11
MJUP = 1.898e27
M_HOST = 47.0 * MJUP
RNG = np.random.default_rng(20260813)

PERIODS = [20.0, 60.0, 120.0, 200.0, 300.0]
KS = [40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250,
      300, 350, 400, 500, 600, 800]
NPHI = 36
LOG_TOL = 0.06


def series(path):
    """The M15 recipe, unchanged: median order combine + internal 3x spread screen."""
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    med = np.nanmedian(RV, axis=0)
    spread = np.nanstd(RV - med, axis=0)
    keep = spread <= 3 * np.nanmedian(spread)
    return np.asarray(c["BJD"], float)[keep], med[keep]


def qr_bank(t, grid):
    Q0 = np.linalg.qr(np.ones((len(t), 1)))[0]
    bank = np.array([np.linalg.qr(np.column_stack(
        [np.ones(len(t)), np.cos(2 * np.pi / P * t), np.sin(2 * np.pi / P * t)]))[0]
        for P in grid])
    return Q0, bank


def landscape(Q0, bank, Y, n):
    """dBIC(P) for a column-stack of series Y (n, M) -> (n_periods, M)."""
    sy = np.sum(Y * Y, axis=0)
    rss0 = np.maximum(sy - np.sum((Q0.T @ Y) ** 2, axis=0), 1e-300)
    out = np.empty((len(bank), Y.shape[1]))
    for i, Q in enumerate(bank):
        rss = np.maximum(sy - np.sum((Q.T @ Y) ** 2, axis=0), 1e-300)
        out[i] = n * np.log(rss0 / rss) - 2 * np.log(n)
    return out


def fires(land, grid, P_inj, bar):
    """M15's criterion, vectorized: peak within tol of P_inj, >= bar, and global max."""
    near = np.abs(np.log(grid / P_inj)) < LOG_TOL
    best_near = land[near].max(axis=0)
    return (best_near >= bar) & (best_near >= land.max(axis=0) - 0.01)


def msini_mjup(K, P_days):
    P = P_days * 86400.0
    return (K * M_HOST ** (2 / 3) * (P / (2 * np.pi * G)) ** (1 / 3)) / MJUP


def main():
    path = next((a for a in sys.argv[1:] if not a.startswith("--")), "E15_R2.rvo.dat")
    nperm = 2000
    if "--nperm" in sys.argv:
        nperm = int(sys.argv[sys.argv.index("--nperm") + 1])
    t, y = series(path)
    n = len(y)
    grid = np.exp(np.linspace(np.log(5), np.log(460), 2000))
    Q0, bank = qr_bank(t, grid)
    print(f"# series {path}: n={n}, span={t.max() - t.min():.0f} d, "
          f"rms={np.std(y):.0f} m/s, {nperm} null permutations\n")

    # ---- null landscapes -------------------------------------------------
    Y = y[RNG.permuted(np.tile(np.arange(n), (nperm, 1)), axis=1).T]
    null = landscape(Q0, bank, Y, n)
    nmax = null.max(axis=0)
    print("# max dBIC of a SIGNAL-FREE series with this sampling")
    for q in (50, 90, 95, 99):
        print(f"#   {q}th percentile: {np.percentile(nmax, q):+.2f}")
    print()

    print("# FALSE-ALARM PROBABILITY of the M15 criterion (dBIC >= bar AND rank 1)")
    print(f"# {'P_inj':>7s} " + " ".join(f"{'bar=' + str(b):>10s}"
                                         for b in (10, 15, 20, 25)))
    bars_fap = {}
    for P in PERIODS:
        row = []
        for b in (10, 15, 20, 25):
            row.append(fires(null, grid, P, b).mean())
        bars_fap[P] = row
        print(f"  {P:>7.0f} " + " ".join(f"{v:>10.4f}" for v in row))

    # bar giving <=5% and <=1% FAP, per period
    print("\n# calibrated bars")
    cal = {}
    for P in PERIODS:
        vals = []
        for target in (0.05, 0.01):
            lo, hi = 0.0, 60.0
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                if fires(null, grid, P, mid).mean() > target:
                    lo = mid
                else:
                    hi = mid
            vals.append(hi)
        cal[P] = vals
        print(f"  P={P:5.0f} d:  FAP 5% needs dBIC >= {vals[0]:5.2f};  "
              f"FAP 1% needs dBIC >= {vals[1]:5.2f}")

    # ---- K90 at each bar --------------------------------------------------
    phis = np.linspace(0, 2 * np.pi, NPHI, endpoint=False)
    print(f"\n# K90 (smallest K detected in >= 90% of {NPHI} phases), by bar")
    print(f"# {'P(d)':>6s} {'K90@10':>8s} {'msini':>7s} | {'K90@5%':>8s} {'msini':>7s} "
          f"| {'K90@1%':>8s} {'msini':>7s}")
    results = {}
    for P in PERIODS:
        cols = np.column_stack([y + K * np.sin(2 * np.pi * t / P + ph)
                                for K in KS for ph in phis])
        land = landscape(Q0, bank, cols, n)
        out = []
        for bar in (10.0, cal[P][0], cal[P][1]):
            hit = fires(land, grid, P, bar).reshape(len(KS), NPHI).mean(axis=1)
            k90 = next((K for K, f in zip(KS, hit) if f >= 0.9), None)
            out.append(k90)
        results[P] = out
        cells = []
        for k in out:
            cells.append(f"{k:>8}" if k else f"{'>800':>8}")
            cells.append(f"{msini_mjup(k, P):>7.2f}" if k else f"{'--':>7s}")
        print(f"  {P:>6.0f} " + " | ".join(" ".join(cells[i:i + 2])
                                           for i in range(0, 6, 2)))

    print("\n# M15 published (bar=10, 12 phases): K90 = 300/250/250/300/300 m/s "
          "-> msini 0.5/0.6/0.8/1.1/1.2 MJup")


if __name__ == "__main__":
    main()
