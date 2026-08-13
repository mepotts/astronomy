"""Small-n injection scorer: per-epoch recovery ratios, no regression needed.

For 2-8 epoch spot-check targets the slope-fit scorer (inject_score_m14) has no
leverage. Here recovery = (rv_inj - rv_ref) / v_injected per epoch per order,
reported as per-order mean +- scatter and as the combined (median-over-orders)
per-epoch ratio. Valid for any n >= 1 as long as |v| is not near zero (use a
phase-90 plan).

Usage: m17_score.py ARM REF_RVO PLAN
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


ref, _ = rvo_rows(ref_path)
ref = {os.path.basename(k): v for k, v in ref.items()}

per_order, combined = {}, []
for i, p in enumerate(PLAN):
    f = os.path.basename(p["file"])
    v = p["v"]
    if abs(v) < 50:
        continue
    inj_path = f"{arm}_inj{i:02d}.rvo.dat"
    if not os.path.exists(inj_path) or f not in ref:
        continue
    inj, orders = rvo_rows(inj_path)
    if not inj:
        continue
    di = next(iter(inj.values()))
    dr = ref[f]
    ratios = []
    for o in orders:
        if ok(di, o) and ok(dr, o):
            ratio = (di[f"rv{o}"] - dr[f"rv{o}"]) / v
            per_order.setdefault(o, []).append(ratio)
            ratios.append(ratio)
    if ratios:
        combined.append(np.median(ratios))

c = np.array(combined)
print(f"{arm}: n_epochs={len(c)}  combined recovery (median-over-orders) = "
      f"{100 * c.mean():.0f}% +- {100 * c.std(ddof=min(1, len(c) - 1)) if len(c) > 1 else 0:.0f}%")
print("per-order recovery (%):")
for o in sorted(per_order):
    r = np.array(per_order[o])
    sd = 100 * r.std(ddof=1) if len(r) > 1 else 0.0
    print(f"  o={o:2d}: {100 * r.mean():7.0f} +- {sd:5.0f}   n={len(r)}")
