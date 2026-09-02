#!/usr/bin/env python3
"""M3 C3 diagnostic: our own likelihood evaluated at the published MAP vector
vs at our chain's best point, for ONE pulsar.

  dlnL = lnL(our best point) - lnL(published MAP)
    dlnL < 0  -> our sampler under-performed        -> sampling shortfall
    dlnL > 0  -> our likelihood prefers a different solution
                 -> prior/convention finding, or (per the pre-registered rule,
                    M3 doc 1.3 C3) a genuine disagreement when dlnL > 10 AND
                    the disagreeing parameter's published 68% interval is
                    narrower than 25% of its prior range.

Run for EVERY pulsar, agreeing or not, so the array-wide distribution of the
diagnostic is known rather than only its tail.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models3 as M  # noqa: E402


def main():
    psr = sys.argv[1]
    out = RES / "diag"
    out.mkdir(parents=True, exist_ok=True)
    summ_p = RES / f"{psr}_noise_n1.summary.json"
    if not summ_p.exists():
        print(f"{psr}: no campaign summary")
        return
    summ = json.loads(summ_p.read_text())
    pta, meta = M.build_pta(psr, str(REPO / "data/partim_tdb"),
                            str(REPO / "data/partim"), variant="noise")
    names = list(pta.param_names)
    rec = dict(psr=psr, params=names)

    xpub, missing = M.published_vector(pta, psr)
    if xpub is None:
        rec["error"] = f"no published value for {missing}"
        (out / f"{psr}.json").write_text(json.dumps(rec, indent=1))
        print(f"{psr}: SKIP ({rec['error']})")
        return
    rec["lnl_published"] = float(np.asarray(
        pta.get_lnlikelihood(xpub)).reshape(-1)[0])

    best = summ.get("best_point")
    xbest = np.array([best[n] for n in names])
    rec["lnl_best"] = float(np.asarray(
        pta.get_lnlikelihood(xbest)).reshape(-1)[0])
    rec["lnl_best_recorded"] = summ.get("lnl_best")

    # median point too (a fairer "where our posterior sits" reference)
    meds = {r["param"]: r["median"] for r in summ["chain"]["params"]}
    xmed = np.array([meds[n] for n in names])
    rec["lnl_median"] = float(np.asarray(
        pta.get_lnlikelihood(xmed)).reshape(-1)[0])

    rec["dlnl_best_minus_pub"] = rec["lnl_best"] - rec["lnl_published"]
    rec["dlnl_median_minus_pub"] = rec["lnl_median"] - rec["lnl_published"]
    rec["n_agree"] = summ.get("n_agree")
    rec["n_compared"] = summ.get("n_compared")
    rec["misses"] = [r["param"] for r in summ.get("a2", [])
                     if r.get("agree") is False]

    # pre-registered "is the table claiming a measurement" test per miss
    tight = {}
    for r in summ.get("a2", []):
        if r.get("agree") is not False:
            continue
        key = r["key"]
        pr = M.PRIORS.get(key)
        pub = M.PUBLISHED[psr].get(key)
        if pr and isinstance(pub, list):
            width = abs(pub[2] - pub[1])
            tight[r["param"]] = dict(
                pub_ci_width=width, prior_width=pr[1] - pr[0],
                frac=width / (pr[1] - pr[0]),
                claims_measurement=bool(width / (pr[1] - pr[0]) < 0.25))
    rec["miss_tightness"] = tight
    (out / f"{psr}.json").write_text(json.dumps(rec, indent=1))
    print(f"{psr}: dlnL(best-pub) = {rec['dlnl_best_minus_pub']:+.2f}  "
          f"dlnL(median-pub) = {rec['dlnl_median_minus_pub']:+.2f}  "
          f"agree {rec['n_agree']}/{rec['n_compared']}")


if __name__ == "__main__":
    main()
