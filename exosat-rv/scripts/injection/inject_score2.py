"""Score a generic injection arm: slope of (RV_injected - RV_reference) on v.

Usage: inject_score2.py ARMNAME REF_RVO
Reads {ARM}_injNN.rvo.dat from cwd (viper-src) and the reference multi-epoch run.
Matches epochs by source filename. Reports overall and per-order recovery.
"""
import json
import os
import sys

import numpy as np

SP = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(SP, "inject_plan_big.json")))


def rvo_rows(path):
    lines = [ln for ln in open(path).read().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, []
    hdr = lines[0].split()
    orders = sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit())
    out = {}
    for ln in lines[1:]:
        v = ln.split()
        out[v[-1]] = {n: float(x) for n, x in zip(hdr[:-1], v[:-1])}
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


arm, ref_path = sys.argv[1], sys.argv[2]
ref, ref_orders = rvo_rows(ref_path)

v_all, d_all, per_order = [], [], {}
for i, p in enumerate(PLAN):
    f = p["file"]
    inj_path = f"{arm}_inj{i:02d}.rvo.dat"
    if not os.path.exists(inj_path) or f not in ref:
        continue
    inj, orders = rvo_rows(inj_path)
    if not inj:
        continue
    di = next(iter(inj.values()))
    dr = ref[f]
    xs = [di[f"rv{o}"] for o in orders if ok(di, o)]
    ys = [dr[f"rv{o}"] for o in orders if ok(dr, o)]
    if xs and ys:
        v_all.append(p["v"])
        d_all.append(np.mean(xs) - np.mean(ys))
    for o in orders:
        if ok(di, o) and ok(dr, o):
            per_order.setdefault(o, []).append((p["v"], di[f"rv{o}"] - dr[f"rv{o}"]))

s, se, rms, n = fit(v_all, d_all)
print(f"{arm}: n={n}  recovery={100*s:.0f}% +- {100*se:.0f}%  resid_rms={rms:.0f} m/s")
print("per-order recovery (%):")
for o in sorted(per_order):
    so, seo, rmso, no = fit([a for a, _ in per_order[o]], [b for _, b in per_order[o]])
    print(f"  o={o:2d}: {100*so:6.0f}% +- {100*seo:3.0f}%  rms={rmso:6.0f}  n={no}")
