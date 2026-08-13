"""Scale an injection plan's velocities (e.g. K=1530 -> 306: factor 0.2).

Usage: python scale_plan.py inject_plan_big.json 0.2 inject_plan_k306.json
"""
import json
import sys

src, factor, dst = sys.argv[1], float(sys.argv[2]), sys.argv[3]
plan = json.load(open(src))
for d in plan:
    d["v"] = d["v"] * factor
json.dump(plan, open(dst, "w"), indent=1)
print(f"wrote {dst}: {len(plan)} epochs, |v|max = {max(abs(d['v']) for d in plan):.0f} m/s")
