#!/usr/bin/env python3
"""M2 run inventory (H4): aggregate manifest + summary JSONs into one table.

Usage: python scripts/m2_status.py [--json]
"""
import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results" / "m2"
MANIFEST = RESULTS / "manifest"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    for mf in sorted(MANIFEST.glob("*.json")):
        m = json.loads(mf.read_text())
        run_id = m.get("run_id", mf.stem)
        s = {}
        sp = RESULTS / f"{run_id}.summary.json"
        if sp.exists():
            s = json.loads(sp.read_text())
        rows.append(dict(
            run_id=run_id, state=m.get("state"),
            exit=m.get("exit_reason"), pid=m.get("pid"),
            elapsed_min=m.get("elapsed_min"),
            raw_iters=m.get("raw_iters"),
            gate=m.get("gate_met"), eval_ms=m.get("eval_ms"),
            acc=(s.get("chain") or {}).get("acc_rate"),
            stable=(s.get("chain") or {}).get("stable"),
            agree=(f"{s['n_agree']}/{s['n_compared']}"
                   if "n_agree" in s else None),
            verdict=s.get("verdict"),
            load=m.get("loadavg"),
        ))

    if args.json:
        print(json.dumps(rows, indent=2))
        return
    hdr = ["run_id", "state", "exit", "elapsed_min", "raw_iters", "gate",
           "acc", "stable", "agree", "eval_ms", "load"]
    widths = {h: max(len(h), max((len(str(r.get(h))) for r in rows),
                                 default=4)) for h in hdr}
    print("  ".join(h.ljust(widths[h]) for h in hdr))
    for r in rows:
        print("  ".join(str(r.get(h)).ljust(widths[h]) for h in hdr))


if __name__ == "__main__":
    main()
