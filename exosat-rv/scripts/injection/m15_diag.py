"""M15 internal diagnostics for an eta Tel B series. INFORMATIONAL ONLY.

No published RVs exist for this target, so nothing here may drive an adoption
decision (M9/M12 rules) — that is the injection harness's job. This prints epoch
counts, combine scatters, across-order spreads, the internal 3x screen verdict,
and r(BERV).

Usage (WSL, from ~/viper-src): python m15_diag.py E15_R1.rvo.dat [more.rvo.dat ...]
"""
import sys

import numpy as np

sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load  # noqa: E402

for path in sys.argv[1:]:
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    med = np.nanmedian(RV, axis=0)
    mean = np.nanmean(RV, axis=0)
    spread = np.nanstd(RV - med, axis=0)
    berv = np.asarray(c["BERV"], float)
    g = np.isfinite(mean)
    r = np.corrcoef(berv[g], mean[g])[0, 1] if g.sum() > 2 else np.nan
    bad = spread > 3 * np.nanmedian(spread)
    print(f"{path}: n_epochs={RV.shape[1]} n_orders={len(orders)}")
    print(f"  epoch rms: mean-combine {np.nanstd(mean):6.0f}   "
          f"median-combine {np.nanstd(med):6.0f} m/s")
    print(f"  across-order spread: median {np.nanmedian(spread):6.0f}   "
          f"max {np.nanmax(spread):6.0f} m/s")
    print(f"  r(mean, BERV) = {r:+.2f}")
    drops = [f"{t - 2460000:.3f}" for t, b in zip(c["BJD"], bad) if b]
    print(f"  internal 3x screen drops {int(bad.sum())} epoch(s): {drops}")
