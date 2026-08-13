"""Is the >1 slope vs published a BERV systematic in disguise?

1. corr(published RV, BERV) over the 17 matched epochs — degeneracy of confound.
2. Per-order and combined slope on published, WITH a BERV column in the regressor.
3. K at published period on the MATCHED median/clip series (kfit redo without the
   unmatched epoch).
"""
import numpy as np
import sys
sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load, published

P = 171.454
pb, pv, pe = published()


def matched(path):
    c, orders = load(path)
    idx, keep = [], []
    for j, t in enumerate(c["BJD"]):
        i = np.argmin(np.abs(pb - t))
        if abs(pb[i] - t) < 0.05:
            idx.append(i); keep.append(j)
    keep = np.array(keep)
    return c, orders, keep, pv[np.array(idx)]


def slope2(y, pub, berv=None):
    g = np.isfinite(y)
    cols = [pub[g], np.ones(g.sum())]
    if berv is not None:
        cols.append(berv[g])
    A = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(A, y[g], rcond=None)
    r = y[g] - A @ b
    se = np.sqrt(np.sum(r**2) / max(len(r) - A.shape[1], 1)
                 * np.linalg.inv(A.T @ A)[0, 0])
    return b[0], se


path = sys.argv[1]
c, orders, keep, pub = matched(path)
berv = c["BERV"][keep]
print(f"corr(published RV, BERV) over matched epochs: "
      f"{np.corrcoef(pub, berv)[0,1]:+.2f}   (n={len(pub)})")

RV = np.array([np.where(np.isfinite(c[f'e_rv{o}']) & (c[f'e_rv{o}'] > 0),
                        c[f'rv{o}'], np.nan)[keep] for o in orders])
med = np.nanmedian(RV, axis=0)
mad = 1.4826 * np.nanmedian(np.abs(RV - med), axis=0)
clip = np.nanmean(np.where(np.abs(RV - med) < 3 * np.maximum(mad, 200.0), RV, np.nan),
                  axis=0)

print("\ncombine   slope_raw        slope_BERVctrl")
for name, y in (("median", med), ("clip", clip), ("mean", np.nanmean(RV, axis=0))):
    s1, e1 = slope2(y, pub)
    s2, e2 = slope2(y, pub, berv)
    print(f"{name:<8} {s1:5.2f}+-{e1:4.2f}      {s2:5.2f}+-{e2:4.2f}")

print("\nper-order slope on published, BERV-controlled:")
for o, y in zip(orders, RV):
    s1, e1 = slope2(y, pub)
    s2, e2 = slope2(y, pub, berv)
    print(f"  o={o:2d}: raw {s1:6.2f}+-{e1:4.2f}   ctrl {s2:6.2f}+-{e2:4.2f}")

# K at published period on matched series
w = 2 * np.pi / P
t = c["BJD"][keep]


def kfit(y, use_berv=False):
    g = np.isfinite(y)
    cols = [np.cos(w * t[g]), np.sin(w * t[g]), np.ones(g.sum())]
    if use_berv:
        cols.append(berv[g])
    A = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(A, y[g], rcond=None)
    r = y[g] - A @ b
    sig2 = np.sum(r**2) / max(len(r) - A.shape[1], 1)
    cov = sig2 * np.linalg.inv(A.T @ A)
    K = np.hypot(b[0], b[1])
    J = np.array([b[0] / K, b[1] / K])
    return K, float(np.sqrt(J @ cov[:2, :2] @ J)), r.std()


print("\nK at P=171.454 on MATCHED epochs:")
for name, y in (("median", med), ("clip", clip)):
    K, eK, r = kfit(y)
    K2, eK2, r2 = kfit(y, True)
    print(f"{name:<8} K={K:4.0f}+-{eK:3.0f} resid={r:3.0f}   "
          f"+BERV: K={K2:4.0f}+-{eK2:3.0f} resid={r2:3.0f}")
print(f"published K1=306 (2-sat circ); table-itself K=273+-30 resid=91")
