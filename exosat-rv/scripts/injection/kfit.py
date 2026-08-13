"""Fit K at the published period to our median-combined series; compare to K1_pub.

Circular orbit at fixed P => linear model a*cos + b*sin + c (+ d*BERV optionally).
K = hypot(a, b). Analytic covariance from residual variance.
"""
import numpy as np
import sys
sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load, published

P = 171.454          # published 2-sat period
K_PUB = 305.959      # published K1 (2-sat, circular)

pb, pv, pe = published()


def median_series(path):
    c, orders = load(path)
    RV = np.array([c["rv%d" % o] for o in orders])
    ER = np.array([c["e_rv%d" % o] for o in orders])
    ok = np.isfinite(RV) & np.isfinite(ER) & (ER > 0)
    v = np.nanmedian(np.where(ok, RV, np.nan), axis=0)
    return c["BJD"], v, c["BERV"]


def kfit(t, y, berv=None):
    g = np.isfinite(y)
    t, y = t[g], y[g]
    w = 2 * np.pi / P
    cols = [np.cos(w * t), np.sin(w * t), np.ones_like(t)]
    if berv is not None:
        cols.append(berv[g])
    A = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ b
    sig2 = np.sum(r ** 2) / (len(y) - A.shape[1])
    cov = sig2 * np.linalg.inv(A.T @ A)
    K = np.hypot(b[0], b[1])
    # error on K: delta method
    J = np.array([b[0] / K, b[1] / K])
    eK = np.sqrt(J @ cov[:2, :2] @ J)
    return K, eK, np.std(r, ddof=A.shape[1]), (b[3] if berv is not None else np.nan)


for path in sys.argv[1:]:
    t, v, berv = median_series(path)
    K1, e1, r1, _ = kfit(t, v)
    K2, e2, r2, bb = kfit(t, v, berv)
    print("%-20s  K=%4.0f+-%3.0f resid=%3.0f | +BERV: K=%4.0f+-%3.0f resid=%3.0f bervcoef=%+.0f m/s per km/s"
          % (path, K1, e1, r1, K2, e2, r2, bb))
print("published K1 = %.0f m/s (2-sat circular); 1-sat eccentric K = 318.5" % K_PUB)

# same fit on the published table itself as sanity
t, y = pb, pv
K, eK, r, _ = kfit(t, y)
print("published table itself:  K=%.0f+-%.0f resid=%.0f" % (K, eK, r))
