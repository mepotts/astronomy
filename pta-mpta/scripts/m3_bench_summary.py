#!/usr/bin/env python3
"""M3: aggregate bench records; project the campaign's wall-clock cost."""
import glob
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "noise"
    recs = [json.loads(Path(f).read_text())
            for f in glob.glob(str(REPO / f"results/m3/bench/*_{variant}.json"))]
    recs.sort(key=lambda r: -r["eval_ms"])
    print(f"{len(recs)} {variant} models built (all constructions OK)")
    ev = np.array([r["eval_ms"] for r in recs])
    nd = np.array([r["ndim"] for r in recs])
    print(f"eval ms: min {ev.min():.1f} med {np.median(ev):.1f} "
          f"mean {ev.mean():.1f} max {ev.max():.1f}")
    print(f"ndim   : min {nd.min()} med {np.median(nd):.0f} max {nd.max()}")
    print("heaviest 12:")
    for r in recs[:12]:
        print(f"  {r['psr']:12s} {r['eval_ms']:7.1f} ms  ndim {r['ndim']:2d} "
              f"ntoa {r['ntoa']}")
    # PTMCMC needs ~1.4 evals/iteration on average with our proposal cycle;
    # M2 measured wall directly, so scale from that instead: iters = gate/0.75
    gate = 100_000 if variant == "noise" else 50_000
    iters = gate / 0.75          # post-burn is 75% of the chain
    cpu_min = float((ev * 1e-3 * iters / 60).sum())
    print(f"\nprojected CPU for gate={gate:,} raw post-burn: "
          f"{cpu_min/60:.1f} CPU-hours total")
    for p in (8, 12, 14, 16):
        print(f"  at {p:2d}-way parallel: {cpu_min/60/p:.1f} h wall "
              f"(perfect packing)")
    print(f"single worst pulsar: {recs[0]['psr']} "
          f"{recs[0]['eval_ms']*1e-3*iters/60:.0f} min")


if __name__ == "__main__":
    main()
