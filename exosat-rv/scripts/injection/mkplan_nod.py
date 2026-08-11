"""Build a per-frame injection plan for the per-nodding series.

Reads an rvo.dat (one row per frame, filename in last column), evaluates
v_i = K sin(2pi (bjd_i - t_ref)/P) at each frame's BJD, writes a plan JSON in the
inject_plan_big.json format ({file, bjd, v}). K=1530 and P=171.454 match the M13 arm;
the phase reference is the first frame (the absolute phase is irrelevant to the
recovery-slope metric — only the spread of v matters).

Usage: python mkplan_nod.py RVO OUT.json [K] [P_days]
"""
import json
import os
import sys

import numpy as np

rvo, out = sys.argv[1], sys.argv[2]
K = float(sys.argv[3]) if len(sys.argv) > 3 else 1530.0
P = float(sys.argv[4]) if len(sys.argv) > 4 else 171.454

lines = [ln for ln in open(rvo).read().splitlines() if ln.strip()]
plan = []
t0 = None
for ln in lines[1:]:
    v = ln.split()
    bjd, fname = float(v[0]), os.path.basename(v[-1])
    if t0 is None:
        t0 = bjd
    plan.append({"file": fname, "bjd": bjd,
                 "v": K * float(np.sin(2 * np.pi * (bjd - t0) / P))})
json.dump(plan, open(out, "w"), indent=1)
print(f"wrote {out}: {len(plan)} frames, K={K:.0f}, "
      f"v range [{min(p['v'] for p in plan):.0f}, {max(p['v'] for p in plan):.0f}]")
