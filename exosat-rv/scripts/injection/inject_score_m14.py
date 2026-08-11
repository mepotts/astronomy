"""Score an M14 injection arm through the ADOPTED combine (median), not just the mean.

Usage: inject_score_m14.py ARMNAME REF_RVO PLAN [combine]
Matches epochs by source filename (last column of rvo rows). Reports overall recovery
through mean AND median combines, plus per-order recovery.
"""
import json
import os
import sys

import numpy as np

arm, ref_path, plan_path = sys.argv[1], sys.argv[2], sys.argv[3]
PLAN = json.load(open(plan_path))


def rvo_rows(path):
    lines = [ln for ln in open(path).read().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, []
    hdr = lines[0].split()
    orders = sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit())
    out = {}
    for ln in lines[1:]:
        v = ln.split()
        out[os.path.basename(v[-1])] = {n: float(x) for n, x in zip(hdr[:-1], v[:-1])}
    return out, orders


def ok(d, o):
    return (np.isfinite(d.get(f"rv{o}", np.nan)) and
            np.isfinite(d.get(f"e_rv{o}", np.nan)) and d[f"e_rv{o}"] > 0)


def fit(v, y):
    v, y = np.asarray(v, float), np.asarray(y, float)
    g = np.isfinite(v) & np.isfinite(y)
    v, y = v[g], y[g]
    if len(v) < 4:
        return np.nan, np.nan, np.nan, len(v)
    A = np.column_stack([v, np.ones_like(v)])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ b
    se = np.sqrt(np.sum(r ** 2) / (len(v) - 2) * np.linalg.inv(A.T @ A)[0, 0])
    return b[0], se, r.std(ddof=2), len(v)


ref, ref_orders = rvo_rows(ref_path)
ref = {os.path.basename(k): v for k, v in ref.items()}

v_all, d_mean, d_med, per_order = [], [], [], {}
for i, p in enumerate(PLAN):
    f = os.path.basename(p["file"])
    inj_path = f"{arm}_inj{i:02d}.rvo.dat"
    if not os.path.exists(inj_path) or f not in ref:
        continue
    inj, orders = rvo_rows(inj_path)
    if not inj:
        continue
    di = next(iter(inj.values()))
    dr = ref[f]
    both = [o for o in orders if ok(di, o) and ok(dr, o)]
    if not both:
        continue
    v_all.append(p["v"])
    d_mean.append(np.mean([di[f"rv{o}"] for o in both])
                  - np.mean([dr[f"rv{o}"] for o in both]))
    d_med.append(np.median([di[f"rv{o}"] for o in both])
                 - np.median([dr[f"rv{o}"] for o in both]))
    for o in both:
        per_order.setdefault(o, []).append((p["v"], di[f"rv{o}"] - dr[f"rv{o}"]))

for name, d in (("mean", d_mean), ("median", d_med)):
    s, se, rms, n = fit(v_all, d)
    print(f"{arm} [{name} combine]: n={n}  recovery={100*s:.0f}% +- {100*se:.0f}%  "
          f"resid_rms={rms:.0f} m/s")
print("per-order recovery (%):")
for o in sorted(per_order):
    so, seo, rmso, no = fit([a for a, _ in per_order[o]], [b for _, b in per_order[o]])
    print(f"  o={o:2d}: {100*so:6.0f}% +- {100*seo:3.0f}%  rms={rmso:6.0f}  n={no}")
