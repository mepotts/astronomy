#!/usr/bin/env python3
"""M3: prior-coverage audit of the published tables.

The paper tabulates no prior ranges (verified: the string "prior" appears in
arXiv:2412.01148 only in method prose, never as a range). A reproducer must
therefore guess them. This asks the sharp question: how many published values
fall OUTSIDE the standard wide priors M1/M2 declared -- i.e. how many table
entries a good-faith reproducer literally cannot reach?

Prior set audited = scripts/mpta_models3.PRIORS (M2 doc 1.2, declared
UNSOURCED).
"""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models3 as M  # noqa: E402

OUT = REPO / "results" / "m3" / "prior_coverage.json"


def main():
    tab = M._T
    bad_map, bad_ci = [], []
    per_key = Counter()
    n = 0
    for psr, rec in sorted(tab.items()):
        for key, v in rec["pub"].items():
            if not isinstance(v, list) or len(v) != 3:
                continue
            pr = M.PRIORS.get(key)
            if pr is None:
                continue
            n += 1
            m, lo, hi = v
            if not (pr[0] <= m <= pr[1]):
                bad_map.append(dict(psr=psr, key=key, map=m, prior=list(pr)))
                per_key[key] += 1
            elif not (pr[0] <= m + lo and m + hi <= pr[1]):
                bad_ci.append(dict(psr=psr, key=key, map=m,
                                   ci=[m + lo, m + hi], prior=list(pr)))
    print(f"{len(bad_map)} of {n} tabulated values have a MAP outside the "
          f"declared prior range ({100*len(bad_map)/n:.1f}%)")
    print(f"  by parameter: {dict(per_key.most_common())}")
    for b in sorted(bad_map, key=lambda b: (b["key"], b["psr"])):
        print(f"    {b['psr']:12s} {b['key']:16s} MAP {b['map']:8.2f}  "
              f"prior {b['prior']}")
    print(f"\n{len(bad_ci)} further values sit inside the prior but have a 68% "
          f"interval that runs past one of its edges")
    kc = Counter(b["key"] for b in bad_ci)
    print(f"  by parameter: {dict(kc.most_common())}")
    OUT.write_text(json.dumps(dict(
        n_checked=n, priors={k: list(v) for k, v in M.PRIORS.items()},
        map_outside=bad_map, ci_crossing=bad_ci), indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
