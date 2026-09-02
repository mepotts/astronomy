#!/usr/bin/env python3
"""M3: aggregate the all-83 A1 (stack acceptance) records."""
import glob
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "m3" / "a1_summary.json"


def main():
    recs = [json.loads(Path(f).read_text())
            for f in glob.glob(str(REPO / "results/m3/a1/*.json"))]
    recs.sort(key=lambda r: r["psr"])
    ok = [r for r in recs if r.get("ok")]
    bad = [r for r in recs if not r.get("ok")]
    print(f"records {len(recs)}  ok {len(ok)}  errors {len(bad)}")
    for r in bad:
        print(f"  ERROR {r['psr']}: {r.get('error','')[-400:]}")
    npass = sum(1 for r in ok if r["a1"] == "PASS")
    print(f"A1 PASS {npass} / {len(ok)}")
    worst = sorted(ok, key=lambda r: -abs(r["frac"]))[:12]
    for r in worst:
        flag = "" if r["a1"] == "PASS" else "  <-- FAIL"
        print(f"  {r['psr']:12s} {r['frac']:+7.2%}  wrms {r['wrms_us']:.4f} "
              f"tres {r['tres_pub']:.4f}  ntoa {r['ntoa']}/{r['ntoa_pub']}"
              f"{flag}")
    tot = sum(r["ntoa"] for r in ok)
    short = [r for r in ok if r["ntoa"] < r["ntoa_pub"]]
    print(f"total ToAs {tot};  {len(short)}/{len(ok)} ship fewer than par NTOA")
    print(f"TRACK stripped in {sum(1 for r in ok if r.get('track_stripped'))}")
    ts = [r["tspan_days"] for r in ok]
    print(f"Tspan d: min {min(ts):.0f} med {np.median(ts):.0f} "
          f"max {max(ts):.0f}")
    OUT.write_text(json.dumps(dict(
        n=len(recs), n_ok=len(ok), n_pass=npass,
        total_toas=tot, n_short=len(short),
        frac_abs_max=max(abs(r["frac"]) for r in ok),
        records={r["psr"]: {k: r[k] for k in
                            ("a1", "frac", "wrms_us", "tres_pub", "ntoa",
                             "ntoa_pub", "tspan_days", "chi2r", "binary")}
                 for r in ok}), indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
