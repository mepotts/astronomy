"""Score viper runs against the paper's PUBLISHED RVs (Nature Table 2) — the honest metric.

M12 §9b.4's rule: every internal proxy tried in this project (epoch rms, A-B repeatability,
GJ 229 B amplitude, anchor screens) has been wrong by a factor >= 6 at least once.
The published per-night RVs are the only external truth available. This scorer reports:

  - n_match : archive epochs matched to published epochs (|dBJD| < 0.05 d)
  - rms_pub : rms of (ours - published) after removing one constant offset  [m/s]
  - slope   : regression of ours on published (1 = we transmit their signal at full
              amplitude; 0 = we do not see what they see)
  - r_pub   : Pearson r between ours and published
  - eq1     : the paper's Eq. (1) statistic, mean over epochs (their mean: 57.68 m/s;
              their combined-spectrum arm, which is what the archive route uses: 60.50)
  - rms     : epoch-to-epoch scatter of our RVs
  - r_berv  : correlation of our RVs with BERV (paper reports none)

Usage:  python vs_published.py label=path/to/run.rvo.dat [more label=path ...]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import combine  # noqa: E402


def load(p):
    """Chunk-tolerant rvo.dat loader: rv7 or rv7-0 columns both become entries."""
    hdr = open(p).readline().split()
    d = np.genfromtxt(p, skip_header=1, usecols=range(len(hdr) - 1),
                      invalid_raise=False)
    if d.ndim == 1:
        d = d[None, :]
    keys = [n[2:] for n in hdr if n.startswith("rv") and n != "rv"]
    cols = {}
    for i, n in enumerate(hdr[:-1]):
        cols[n] = d[:, i]
    # normalise: map rvX-Y / e_rvX-Y onto integer pseudo-order X*10+Y when chunked
    out = {k: v for k, v in cols.items() if not k[2:].replace("-", "").isdigit()
           or not (k.startswith("rv") or k.startswith("e_rv"))}
    orders = []
    for k in keys:
        if k.isdigit():
            o = int(k)
        elif k.replace("-", "").isdigit():
            a, b = k.split("-")
            o = int(a) * 10 + int(b)
        else:
            continue
        orders.append(o)
        out[f"rv{o}"] = cols[f"rv{k}"]
        out[f"e_rv{o}"] = cols[f"e_rv{k}"]
    for k in ("BJD", "RV", "e_RV", "BERV"):
        if k in cols:
            out[k] = cols[k]
    return out, sorted(orders)

PUB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "data", "published", "hoy2026_nature_table2_rvs.csv")


def published():
    rows = []
    with open(PUB, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("bjd"):
                continue
            rows.append([float(x) for x in line.split(",")])
    a = np.array(rows)
    return a[:, 0], a[:, 1], a[:, 2]


def score(path):
    c, orders = load(path)
    mean, wmean, eps = combine(c, orders)
    bjd, berv = c["BJD"], c["BERV"]
    pb, pv, pe = published()

    ours_t, ours_v, pub_v, pub_e = [], [], [], []
    for t, v in zip(bjd, mean):
        if not np.isfinite(v):
            continue
        i = np.argmin(np.abs(pb - t))
        if abs(pb[i] - t) < 0.05:
            ours_t.append(t); ours_v.append(v); pub_v.append(pv[i]); pub_e.append(pe[i])
    ours_v, pub_v = np.array(ours_v), np.array(pub_v)

    out = dict(n=len(orders), n_match=len(ours_v),
               rms=float(np.nanstd(mean, ddof=0)), eq1=float(np.nanmean(eps)))
    g = np.isfinite(mean) & np.isfinite(berv)
    if g.sum() > 2:
        out["r_berv"] = float(np.corrcoef(berv[g], mean[g])[0, 1])
    if len(ours_v) > 2:
        d = ours_v - pub_v
        out["rms_pub"] = float(np.std(d - d.mean(), ddof=0))
        A = np.column_stack([pub_v, np.ones_like(pub_v)])
        b, res, *_ = np.linalg.lstsq(A, ours_v, rcond=None)
        out["slope"] = float(b[0])
        n = len(ours_v)
        sig2 = float(np.sum((ours_v - A @ b) ** 2)) / max(n - 2, 1)
        cov = sig2 * np.linalg.inv(A.T @ A)
        out["e_slope"] = float(np.sqrt(cov[0, 0]))
        out["r_pub"] = float(np.corrcoef(pub_v, ours_v)[0, 1])
    return out


if __name__ == "__main__":
    print(f"{'config':<26}|{'ord':>4}{'match':>6}{'rms':>7}{'Eq1':>7}{'r_berv':>8} "
          f"|{'rms_pub':>8}{'slope':>7}{'+-':>6}{'r_pub':>7}")
    print("-" * 92)
    for a in sys.argv[1:]:
        lab, path = a.split("=", 1)
        if not os.path.exists(path):
            print(f"{lab:<26}| MISSING {path}")
            continue
        s = score(path)
        row = (f"{lab:<26}|{s['n']:>4}{s['n_match']:>6}{s['rms']:>7.0f}{s['eq1']:>7.0f}"
               f"{s.get('r_berv', float('nan')):>8.2f} |")
        if "rms_pub" in s:
            row += (f"{s['rms_pub']:>8.0f}{s['slope']:>7.2f}{s['e_slope']:>6.2f}"
                    f"{s['r_pub']:>7.2f}")
        print(row)
