"""CT Cha B order screen: keep only orders stable in BOTH M17 injection arms,
then re-verdict the 3-epoch series on the screened set.

Screen rule (a priori, injection-only — the sanctioned M13 drop): an order
survives if |recovery − 100| ≤ 15 points AND its arm scatter ≤ 25 points in both
the K=1530 and K=300 arms (n≥1 epochs each). Runs entirely on existing outputs.

Usage (WSL, ~/viper-src): python ctcha_screen.py
"""
import json
import os
import sys

import numpy as np

SC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SC)
from vs_published import load  # noqa: E402


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


def arm_recovery(arm, ref, plan_path):
    plan = json.load(open(plan_path))
    per = {}
    for i, p in enumerate(plan):
        f = os.path.basename(p["file"])
        v = p["v"]
        if abs(v) < 50:
            continue
        path = f"{arm}_inj{i:02d}.rvo.dat"
        if not os.path.exists(path) or f not in ref:
            continue
        inj, orders = rvo_rows(path)
        if not inj:
            continue
        di = next(iter(inj.values()))
        dr = ref[f]
        for o in orders:
            if ok(di, o) and ok(dr, o):
                per.setdefault(o, []).append((di[f"rv{o}"] - dr[f"rv{o}"]) / v)
    return {o: (100 * np.mean(r), 100 * (np.std(r, ddof=1) if len(r) > 1 else 0.0))
            for o, r in per.items()}


ref, _ = rvo_rows("ctchab_RV.rvo.dat")
ref = {os.path.basename(k): v for k, v in ref.items()}
a15 = arm_recovery("ctchab_K15", ref, f"{SC}/inject_plan_ctchab_K15.json")
a3 = arm_recovery("ctchab_K3", ref, f"{SC}/inject_plan_ctchab_K3.json")

keep = []
print(f"{'o':>3} {'K15 rec':>9} {'K3 rec':>9}  verdict")
for o in sorted(set(a15) | set(a3)):
    m15_, s15 = a15.get(o, (np.nan, np.nan))
    m3, s3 = a3.get(o, (np.nan, np.nan))
    good = (abs(m15_ - 100) <= 15 and s15 <= 25 and
            abs(m3 - 100) <= 15 and s3 <= 25)
    if good:
        keep.append(o)
    print(f"{o:>3} {m15_:6.0f}±{s15:<3.0f} {m3:6.0f}±{s3:<3.0f}  {'KEEP' if good else 'drop'}")
print("\nscreened oset:", ",".join(map(str, keep)))

c, orders = load("ctchab_RV.rvo.dat")
RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                        c[f"rv{o}"], np.nan) for o in orders if o in keep])
med = np.nanmedian(RV, axis=0)
spread = np.nanstd(RV - med, axis=0)
t = np.asarray(c["BJD"], float)
err = spread / np.sqrt(max(len(keep), 1))
print(f"\nscreened series ({len(keep)} orders):")
for tt, vv, ee in zip(t, med, err):
    print(f"  BJD {tt:.3f}  RV {vv:8.1f} +- {ee:6.1f} m/s")
g = np.isfinite(med)
if g.sum() >= 2:
    w = 1 / np.maximum(err[g], 1) ** 2
    v0 = med[g] - np.average(med[g], weights=w)
    chi2 = float(np.sum(v0**2 * w))
    print(f"\nconstant-RV: chi2 = {chi2:.1f} / {g.sum() - 1} dof   "
          f"std = {np.std(med[g], ddof=1):.0f} m/s over {np.ptp(t[g]):.0f} d")
