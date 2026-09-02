#!/usr/bin/env python3
"""M3: per-run chunk throughput, for tuning the campaign's worker/thread mix."""
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "noise"
    for f in sorted(glob.glob(str(REPO / f"results/m3/*_{variant}_*.summary.json"))):
        s = json.loads(Path(f).read_text())
        cs = s.get("chunks", [])
        parts = " ".join(f"{c['iters']}it/{round(c['seconds'])}s"
                         f"={c['it_per_s']:.2f}/s" for c in cs[-4:])
        print(f"{s['meta']['psr']:13s} eval={s.get('eval_ms'):8.1f}ms "
              f"nchunk={len(cs):3d}  {parts}")


if __name__ == "__main__":
    main()
