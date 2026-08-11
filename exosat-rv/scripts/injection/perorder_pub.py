"""Per-order regression on the PUBLISHED RVs: which orders transmit the signal?"""
import numpy as np
import sys
sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load, published

pb, pv, pe = published()


def match(bjd):
    idx = []
    for t in bjd:
        i = np.argmin(np.abs(pb - t))
        idx.append(i if abs(pb[i] - t) < 0.05 else -1)
    return np.array(idx)


def reg(x, y):
    g = np.isfinite(x) & np.isfinite(y)
    x, y = x[g], y[g]
    if len(x) < 5:
        return np.nan, np.nan, np.nan, len(x)
    A = np.column_stack([x, np.ones_like(x)])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ b
    se = np.sqrt(np.sum(r**2) / (len(x) - 2) * np.linalg.inv(A.T @ A)[0, 0])
    return b[0], se, r.std(ddof=2), len(x)


for path in sys.argv[1:]:
    c, orders = load(path)
    idx = match(c["BJD"])
    sel = idx >= 0
    pub = np.where(sel, pv[idx], np.nan)
    print(f"=== {path}  (slope of order-RV on published; 1 = full transmission)")
    rows = []
    for o in orders:
        rv = np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0), c[f"rv{o}"], np.nan)
        s, se, rms, n = reg(pub, rv)
        rows.append((o, s, se, rms, n))
        print(f"  o={o:2d}: slope {s:6.2f} +- {se:4.2f}   resid_rms {rms:6.0f}   n={n}")
    ss = [r[1] for r in rows if np.isfinite(r[1])]
    print(f"  order-slope median: {np.nanmedian(ss):.2f}   mean: {np.nanmean(ss):.2f}")
