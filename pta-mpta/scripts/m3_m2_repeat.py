#!/usr/bin/env python3
"""M3 control: M2's top-10 noise runs and M3's are independent repeats of the
same model on the same data with different seeds. Their median differences
measure OUR OWN sampler reproducibility, which is the yardstick every
"disagreement" with the published table has to beat.
"""
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
M2 = REPO / "results" / "m2"
M3 = REPO / "results" / "m3"
TOP10 = ["J1713+0747", "J2241-5236", "J0437-4715", "J1909-3744",
         "J1744-1134", "J0125-2327", "J1946-5403", "J1600-3053",
         "J1017-7156", "J2129-5721"]
M2TAG = {"J1909-3744": "blind1"}


def meds(path):
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    if not s.get("gate_met"):
        return None
    return {r["param"]: r["median"] for r in s["chain"]["params"]}


def main():
    rows, diffs = [], []
    for psr in TOP10:
        a = meds(M2 / f"{psr}_noise_{M2TAG.get(psr,'c1')}.summary.json")
        b = meds(M3 / f"{psr}_noise_n1.summary.json")
        if not a or not b:
            continue
        for k in sorted(set(a) & set(b)):
            d = b[k] - a[k]
            rows.append(dict(psr=psr, param=k, m2=a[k], m3=b[k], d=d))
            diffs.append(abs(d))
    if not diffs:
        print("no overlapping gated runs yet")
        return
    diffs = np.array(diffs)
    print(f"M2 vs M3 independent repeats: {len(set(r['psr'] for r in rows))} "
          f"pulsars, {len(rows)} parameters")
    print(f"|median difference|: median {np.median(diffs):.4f}, "
          f"90th pct {np.percentile(diffs,90):.3f}, max {diffs.max():.3f}")
    for r in sorted(rows, key=lambda r: -abs(r["d"]))[:10]:
        print(f"  {r['psr']:12s} {r['param']:32s} "
              f"M2 {r['m2']:9.3f} M3 {r['m3']:9.3f}  d {r['d']:+.3f}")
    (M3 / "m2_m3_repeat.json").write_text(json.dumps(dict(
        n_pulsars=len(set(r["psr"] for r in rows)), n_params=len(rows),
        median_abs=float(np.median(diffs)),
        p90_abs=float(np.percentile(diffs, 90)),
        max_abs=float(diffs.max()), rows=rows), indent=1))


if __name__ == "__main__":
    main()
