"""Does a robust (median / clipped-mean) order combination beat the plain mean?"""
import numpy as np
import sys
sys.path.insert(0, "/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection")
from vs_published import load, published

pb, pv, pe = published()


def series(path, how):
    c, orders = load(path)
    RV = np.array([c["rv%d" % o] for o in orders])
    ER = np.array([c["e_rv%d" % o] for o in orders])
    ok = np.isfinite(RV) & np.isfinite(ER) & (ER > 0)
    RVm = np.where(ok, RV, np.nan)
    if how == "mean":
        v = np.nanmean(RVm, axis=0)
    elif how == "median":
        v = np.nanmedian(RVm, axis=0)
    elif how == "clip":  # sigma-clip around median, then mean
        med = np.nanmedian(RVm, axis=0)
        mad = 1.4826 * np.nanmedian(np.abs(RVm - med), axis=0)
        keep = np.abs(RVm - med) < 3 * np.maximum(mad, 200.0)
        v = np.nanmean(np.where(keep, RVm, np.nan), axis=0)
    return c["BJD"], v


def score(bjd, v):
    ours, pub = [], []
    for t, x in zip(bjd, v):
        if not np.isfinite(x):
            continue
        i = np.argmin(np.abs(pb - t))
        if abs(pb[i] - t) < 0.05:
            ours.append(x)
            pub.append(pv[i])
    ours, pub = np.array(ours), np.array(pub)
    d = ours - pub
    rms_pub = np.std(d - d.mean(), ddof=0)
    A = np.column_stack([pub, np.ones_like(pub)])
    b, *_ = np.linalg.lstsq(A, ours, rcond=None)
    sig2 = np.sum((ours - A @ b) ** 2) / max(len(ours) - 2, 1)
    se = np.sqrt(sig2 * np.linalg.inv(A.T @ A)[0, 0])
    return len(ours), np.std(ours, ddof=0), rms_pub, b[0], se


print("%-22s %-7s %3s %7s %9s %7s" % ("run", "combine", "n", "rms", "rms_pub", "slope"))
for path in sys.argv[1:]:
    for how in ("mean", "median", "clip"):
        try:
            bjd, v = series(path, how)
            n, rms, rp, sl, se = score(bjd, v)
            print("%-22s %-7s %3d %7.0f %9.0f %5.2f+-%.2f" % (path, how, n, rms, rp, sl, se))
        except Exception as e:
            print(path, how, "FAIL", repr(e)[:50])
