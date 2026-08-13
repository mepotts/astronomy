"""M28: null calibration + common-mode audit of the blind period search.

Two questions the project has never answered, both asked with machinery already here:

  (1) COMMON MODE. The CD-35 detection sits at ~171 d, and the archival sampling puts
      BERV power 0.66 at that period. If ~171 d were an artifact of the observing
      cadence / telluric season shared by CRIRES+ companion programmes, it should show
      up in OTHER targets' series too. Every reduced target is run through the identical
      recipe and asked what dBIC it carries near 171 d.

  (2) FALSE ALARM. dBIC = +40 is reported as the maximum over a 4000-period search, but
      the BIC penalty (k log n) charges for parameters, not for the search. The honest
      significance is calibrated by permutation: hold the epoch times (and the BERV
      covariate) fixed, permute the base-model residuals -- which destroys any
      time-coherent signal while preserving the sampling, the value distribution and the
      nuisance structure -- and rebuild the max-dBIC distribution.

Recipe is byte-identical to blind_search.py: per-order median / 3-MAD-clipped mean,
per-night binning (tol 0.2 d), internal >3x-spread epoch screen, dBIC of a circular
Keplerian over a constant, optionally with a BERV nuisance column.

Usage: m28_nullcal.py [--nperm N] [--grid N] label=path [label=path ...]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_published import load          # noqa: E402
from m14_score import bin_frames       # noqa: E402

P_MIN, P_MAX = 5.0, 460.0
P_REF = 171.45          # the published CD-35 period; the common-mode question
LOG_TOL = 0.06          # same window blind_search.py uses around P_REF
RNG = np.random.default_rng(20260813)


def series(path, nod=True):
    """Reduce an rvo.dat to per-night combined RVs, exactly as blind_search.py does."""
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    med = np.nanmedian(RV, axis=0)
    mad = 1.4826 * np.nanmedian(np.abs(RV - med), axis=0)
    clip = np.nanmean(np.where(np.abs(RV - med) < 3 * np.maximum(mad, 200.0), RV, np.nan),
                      axis=0)
    spread = np.nanstd(RV - np.nanmedian(RV, axis=0)[None, :], axis=0)
    t, berv = np.asarray(c["BJD"], float), np.asarray(c["BERV"], float)
    if nod:
        t_b, med, berv_b = bin_frames(t, med, berv)
        _, clip, _ = bin_frames(t, clip, berv)
        _, spread, _ = bin_frames(t, spread, berv)
        t, berv = t_b, berv_b
    fin = np.isfinite(spread)
    bad = np.zeros(len(t), bool)
    if fin.any():
        bad = spread > 3 * np.median(spread[fin])
    return t, med, clip, berv, bad, len(orders)


def qr_bank(t, grid, base_cols):
    """Orthonormal bases for the null model and for every trial period."""
    A0 = np.column_stack(base_cols)
    Q0 = np.linalg.qr(A0)[0]
    bank = []
    for P in grid:
        w = 2 * np.pi / P
        A = np.column_stack(base_cols + [np.cos(w * t), np.sin(w * t)])
        bank.append(np.linalg.qr(A)[0])
    return Q0, np.array(bank), A0


def landscape(Q0, bank, Y, n, k0):
    """dBIC(P) for a matrix of series Y (n, M). Returns (n_periods, M)."""
    sy = np.sum(Y * Y, axis=0)
    rss0 = np.maximum(sy - np.sum((Q0.T @ Y) ** 2, axis=0), 1e-300)
    out = np.empty((len(bank), Y.shape[1]))
    for i, Q in enumerate(bank):
        rss = np.maximum(sy - np.sum((Q.T @ Y) ** 2, axis=0), 1e-300)
        out[i] = n * np.log(rss0 / rss) - 2 * np.log(n)
    return out


def run(label, t, y, berv, nperm, ngrid):
    g = np.isfinite(y)
    t, y = t[g], y[g]
    n = len(y)
    if n < 6:
        print(f"  {label:<26s} n={n} -- skipped (need >= 6 epochs)")
        return None
    grid = np.exp(np.linspace(np.log(P_MIN), np.log(P_MAX), ngrid))
    rows = []
    for use_berv in (False, True):
        base = [np.ones(n)] + ([berv[g]] if use_berv else [])
        k0 = len(base)
        Q0, bank, A0 = qr_bank(t, grid, base)

        obs = landscape(Q0, bank, y[:, None], n, k0)[:, 0]
        i_max = int(np.argmax(obs))
        near = np.abs(np.log(grid / P_REF)) < LOG_TOL
        i_ref = int(np.argmax(np.where(near, obs, -np.inf)))

        # permutation null: keep base-model fit, permute its residuals
        b0, *_ = np.linalg.lstsq(A0, y, rcond=None)
        fit, resid = A0 @ b0, y - A0 @ b0
        Y = fit[:, None] + resid[RNG.permuted(
            np.tile(np.arange(n), (nperm, 1)), axis=1).T]
        null = landscape(Q0, bank, Y, n, k0)
        null_max = null.max(axis=0)
        null_ref = null[near].max(axis=0)

        p_max = (1 + np.sum(null_max >= obs[i_max])) / (1 + nperm)
        p_ref = (1 + np.sum(null_ref >= obs[i_ref])) / (1 + nperm)
        rows.append(dict(berv=use_berv, n=n, span=t.max() - t.min(),
                         P_max=grid[i_max], dbic_max=obs[i_max], p_max=p_max,
                         P_ref=grid[i_ref], dbic_ref=obs[i_ref], p_ref=p_ref,
                         null95=np.percentile(null_max, 95),
                         null_ref95=np.percentile(null_ref, 95)))
    for r in rows:
        tag = "+BERV" if r["berv"] else "plain"
        print(f"  {label:<20s} {tag:<6s} n={r['n']:<3d} span={r['span']:6.0f}d  "
              f"peak P={r['P_max']:7.2f} dBIC={r['dbic_max']:+7.2f} p={r['p_max']:.4f} "
              f"(null95={r['null95']:+6.2f}) | near{P_REF:.0f}: P={r['P_ref']:6.1f} "
              f"dBIC={r['dbic_ref']:+7.2f} p={r['p_ref']:.4f} "
              f"(null95={r['null_ref95']:+6.2f})")
    return rows


def main():
    argv = sys.argv[1:]
    nperm = 2000
    ngrid = 4000
    if "--nperm" in argv:
        nperm = int(argv[argv.index("--nperm") + 1])
    if "--grid" in argv:
        ngrid = int(argv[argv.index("--grid") + 1])
    targets = [a for a in argv if "=" in a]
    print(f"# M28 null calibration -- {nperm} permutations, {ngrid} periods, "
          f"{P_MIN:g}-{P_MAX:g} d, reference period {P_REF} d")
    print(f"# p is the permutation false-alarm probability: fraction of shuffled "
          f"series reaching that dBIC.\n")
    summary = {}
    for spec in targets:
        label, path = spec.split("=", 1)
        if not os.path.exists(path):
            print(f"  {label:<26s} MISSING {path}")
            continue
        t, med, clip, berv, bad, nord = series(path)
        print(f"{label}  [{os.path.basename(path)}]  {nord} orders, "
              f"{len(t)} nights, screen drops {int(bad.sum())}")
        keep = ~bad if bad.any() else np.ones(len(t), bool)
        for combine, y in (("median", med), ("clip", clip)):
            r = run(f"{combine}{'/screened' if bad.any() else ''}",
                    t[keep], y[keep], berv[keep], nperm, ngrid)
            if r:
                summary.setdefault(label, {})[combine] = r
        print()
    # common-mode roll-up
    print("\n# COMMON MODE: dBIC near 171 d, every target, median combine, +BERV variant")
    print(f"# {'target':<14s} {'n':>3s} {'P(d)':>7s} {'dBIC':>8s} {'p':>8s}")
    for label, d in summary.items():
        r = [x for x in d.get("median", []) if x["berv"]]
        if r:
            r = r[0]
            print(f"  {label:<14s} {r['n']:>3d} {r['P_ref']:>7.1f} "
                  f"{r['dbic_ref']:>+8.2f} {r['p_ref']:>8.4f}")


if __name__ == "__main__":
    main()
