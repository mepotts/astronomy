"""Score a viper run the way the paper does.

Kohler et al. 2025 Eq.(1), quoted as Eq.(1) in Hoy et al. (Nature version):
    eps_RV = sqrt( 1/(No-1) * sum(eps_o^-2 (RV_o - RVbar)^2) / sum(eps_o^-2) )
with RVbar the *weighted* mean.  Published value for CD-35 2722 B: 57.68 m/s.

Note this statistic is INVARIANT to a common-mode RV shift: a real signal moves every
order together and cancels in (RV_o - RVbar).  It therefore cannot be improved by
deleting the signal -- unlike epoch-to-epoch rms, which is what M9's empirical
weighting gamed.
"""
import numpy as np, os, sys
from scipy.stats import pearsonr
P_GJ = 12.1621

def load(p):
    hdr = open(p).readline().split()
    d = np.genfromtxt(p, skip_header=1, usecols=range(len(hdr)-1))
    return ({n: d[:, i] for i, n in enumerate(hdr[:-1])},
            sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit()))

def combine(c, o, drop=()):
    u = [x for x in o if x not in drop]
    rv = np.array([c[f"rv{x}"] for x in u]); er = np.array([c[f"e_rv{x}"] for x in u])
    ok = np.isfinite(rv) & np.isfinite(er) & (er > 0)
    RV, EPS, MEAN = [], [], []
    for j in range(rv.shape[1]):
        m = ok[:, j]; n = m.sum()
        if n < 2: RV.append(np.nan); EPS.append(np.nan); MEAN.append(np.nan); continue
        x, e = rv[m, j], er[m, j]; w = e**-2.0
        xb = np.sum(w*x)/np.sum(w)
        EPS.append(np.sqrt(np.sum(w*(x-xb)**2)/np.sum(w)/(n-1)))
        RV.append(xb); MEAN.append(np.mean(x))
    return np.array(MEAN), np.array(RV), np.array(EPS)

def sine_fit(t, y, P):
    g = np.isfinite(t) & np.isfinite(y); t, y = t[g], y[g]
    X = np.column_stack([np.cos(2*np.pi*t/P), np.sin(2*np.pi*t/P), np.ones_like(t)])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(np.hypot(b[0], b[1]))

def night_rms(t, y):
    g = np.isfinite(y); t, y = t[g], y[g]; i = np.argsort(t); t, y = t[i], y[i]
    n = np.floor(t - t[0] + 0.25); r = []
    for k in np.unique(n):
        m = n == k
        if m.sum() > 1: r.extend(y[m] - y[m].mean())
    return float(np.std(r, ddof=1)) if len(r) > 1 else np.nan

def target(p):
    c, o = load(p); mean, wm, eps = combine(c, o); b = c["BERV"]
    g = np.isfinite(mean) & np.isfinite(b)
    r, pv = pearsonr(b[g], mean[g])
    det = (mean[g] - np.polyval(np.polyfit(b[g], mean[g], 1), b[g])).std(ddof=0)
    return dict(n=len(o), rms=np.nanstd(mean, ddof=0), eq1=np.nanmean(eps),
                r=r, p=pv, det=det)

def control(p):
    c, o = load(p); mean, wm, eps = combine(c, o)
    return dict(K=sine_fit(c["BJD"], mean, P_GJ), night=night_rms(c["BJD"], mean),
                eq1=np.nanmean(eps))

if __name__ == "__main__":
    rows = [a.split("=") for a in sys.argv[1:]]
    print(f"{'config':<22}|{'ord':>4}{'rms':>7}{'Eq1':>7}{'r(BERV)':>9}{'p':>7}{'detr':>7} "
          f"|{'ctrl K':>8}{'%base':>7}{'ctrl night':>11}")
    print("-"*94)
    K0 = None
    for lab, xf, cf in [(r[0], r[1], r[2]) for r in rows]:
        s = f"{lab:<22}|"
        if os.path.exists(xf):
            t = target(xf)
            s += f"{t['n']:>4}{t['rms']:>7.0f}{t['eq1']:>7.0f}{t['r']:>9.2f}{t['p']:>7.3f}{t['det']:>7.0f} |"
        else: s += f"{'-':>4}{'-':>7}{'-':>7}{'-':>9}{'-':>7}{'-':>7} |"
        if os.path.exists(cf):
            k = control(cf)
            if K0 is None: K0 = k["K"]
            s += f"{k['K']:>8.0f}{100*k['K']/K0:>6.0f}%{k['night']:>11.0f}"
        else: s += f"{'-':>8}{'-':>7}{'-':>11}"
        print(s)
