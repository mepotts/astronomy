#!/usr/bin/env python3
"""M3: aggregate campaign throughput (total raw iterations and wall seconds
across every run of a variant), for tuning the worker/thread split."""
import glob
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "noise"
    tot_it = tot_s = 0
    n = 0
    for f in glob.glob(str(REPO / f"results/m3/*_{variant}_*.summary.json")):
        s = json.loads(Path(f).read_text())
        ch = s.get("chain") or {}
        tot_it += ch.get("raw_iters", 0)
        tot_s += sum(c["seconds"] for c in s.get("chunks", []))
        n += 1
    print(json.dumps(dict(t=time.time(), runs=n, iters=tot_it,
                          cpu_s=round(tot_s))))


if __name__ == "__main__":
    main()
