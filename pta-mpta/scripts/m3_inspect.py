#!/usr/bin/env python3
"""M3: per-parameter gate detail for named runs (which criterion is holding)."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main():
    variant = sys.argv[1]
    tag = {"noise": "n1", "table": "t1", "fl": "f1"}[variant]
    for p in sys.argv[2:]:
        f = REPO / f"results/m3/{p}_{variant}_{tag}.summary.json"
        if not f.exists():
            print(f"{p}: no summary")
            continue
        s = json.loads(f.read_text())
        ch = s.get("chain") or {}
        print(f"{p}: raw_postburn={ch.get('raw_postburn')} "
              f"acc={ch.get('acc_rate')} stable={ch.get('stable')} "
              f"gate={s.get('gate_met')} exit={s.get('exit_reason')}")
        for r in ch.get("params", []):
            mark = "" if r["stable"] else "   <-- FAILS"
            print(f"   {r['param']:30s} med={r['median']:9.3f} "
                  f"ci=[{r['ci68'][0]:.2f},{r['ci68'][1]:.2f}] "
                  f"halfshift={r['halfshift']:.3f} tol={r['tol']}{mark}")


if __name__ == "__main__":
    main()
