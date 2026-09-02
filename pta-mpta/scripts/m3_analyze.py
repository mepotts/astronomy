#!/usr/bin/env python3
"""M3 C2/C3 aggregation across the all-83 noise campaign.

Emits results/m3/campaign_table.json and prints the agreement statistics with
every miss classified by the pre-registered C3 rule (M3 doc 1.3).
"""
import glob
import json
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
TAB = json.loads((RES / "published_table.json").read_text())
import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models3 as M  # noqa: E402

DLNL_GENUINE = 10.0
TIGHT_FRAC = 0.25


def relative_stable(ch):
    """POST-HOC diagnostic (declared, not the registered C1): the registered
    stability rule uses ABSOLUTE tolerances (0.1 dex on log10 amplitudes),
    which for a prior-limited posterior 3 dex wide demands median stability at
    3% of its own width. The scale-relative version asks for
    |median shift| <= max(registered tol, 0.1 x 68% width)."""
    if not ch or not ch.get("params"):
        return None, None
    worst = None
    ok = True
    for r in ch["params"]:
        w = abs(r["ci68"][1] - r["ci68"][0])
        tol = max(r["tol"], 0.1 * w)
        good = r["halfshift"] <= tol
        ok &= good
        ratio = r["halfshift"] / tol if tol else 0.0
        if worst is None or ratio > worst[1]:
            worst = (r["param"], ratio)
    return bool(ok), worst


def classify(dlnl, tightness):
    """Pre-registered C3 classification of one pulsar's misses."""
    if dlnl is None:
        return "undiagnosed"
    if dlnl < 0:
        return "sampling shortfall"
    claims = any(v.get("claims_measurement") for v in tightness.values())
    if dlnl > DLNL_GENUINE and claims:
        return "genuine disagreement"
    return "prior/convention finding"


def main():
    diags = {}
    for f in glob.glob(str(RES / "diag/*.json")):
        d = json.loads(Path(f).read_text())
        diags[d["psr"]] = d

    rows = []
    for psr in sorted(TAB):
        p = RES / f"{psr}_noise_n1.summary.json"
        if not p.exists():
            rows.append(dict(psr=psr, state="not-started"))
            continue
        s = json.loads(p.read_text())
        ch = s.get("chain") or {}
        d = diags.get(psr, {})
        relok, relworst = relative_stable(ch)
        misses = [r for r in s.get("a2", []) if r.get("agree") is False]
        row = dict(psr=psr, state=s.get("state"), exit=s.get("exit_reason"),
                   gate=bool(s.get("gate_met")),
                   raw_postburn=ch.get("raw_postburn"),
                   acc=ch.get("acc_rate"), stable=ch.get("stable"),
                   rel_stable=relok,
                   rel_worst=(list(relworst) if relworst else None),
                   gate_rel=bool(relok
                                 and (ch.get("acc_rate") or 0) >= 0.05
                                 and (ch.get("raw_postburn") or 0) >= 100000),
                   elapsed_min=s.get("elapsed_min"), eval_ms=s.get("eval_ms"),
                   n_agree=s.get("n_agree"), n_compared=s.get("n_compared"),
                   full=bool(s.get("n_agree") == s.get("n_compared")
                             and s.get("n_compared")),
                   n_sampled=TAB[psr]["n_sampled"],
                   # the deterministic table prints two pulsars in BOLD:
                   # "the parameter values we report are taken from the CURN
                   # Bayesian analysis" - a DIFFERENT model from the favoured
                   # one, so those rows are not a like-for-like target.
                   curn_sourced=bool(TAB[psr].get("curn_sourced")),
                   misses=[dict(param=r["param"], key=r["key"],
                                median=r["median"], ci68=r["ci68"],
                                published_map=r.get("published_map"),
                                published_ci=r.get("published_ci"))
                           for r in misses],
                   dlnl=d.get("dlnl_best_minus_pub"),
                   dlnl_median=d.get("dlnl_median_minus_pub"),
                   miss_class=(classify(d.get("dlnl_best_minus_pub"),
                                        d.get("miss_tightness", {}))
                               if misses else None))
        rows.append(row)

    started = [r for r in rows if r.get("state") and r["state"] != "not-started"]
    gated = [r for r in started if r["gate"]]
    full = [r for r in gated if r["full"]]
    print(f"COVERAGE: {len(started)}/{len(rows)} started, "
          f"{len(gated)} cleared the C1 gate, "
          f"{len(started)-len(gated)} finished without it, "
          f"{len(rows)-len(started)} never started")
    if gated:
        na = sum(r["n_agree"] for r in gated)
        nc = sum(r["n_compared"] for r in gated)
        print(f"AGREEMENT: {len(full)}/{len(gated)} pulsars agree in full; "
              f"{na}/{nc} parameters agree ({100*na/nc:.1f}%)")
        accs = [r["acc"] for r in gated]
        print(f"acceptance over gated runs: {min(accs):.3f}-{max(accs):.3f} "
              f"(floor 0.05)")
        part = [r for r in gated if not r["full"]]
        cls = Counter(r["miss_class"] for r in part)
        print(f"MISSES: {len(part)} pulsars with >=1 miss "
              f"({sum(len(r['misses']) for r in part)} parameters) -> {dict(cls)}")
        keyc = Counter(m["key"] for r in part for m in r["misses"])
        print(f"  misses by parameter: {dict(keyc.most_common())}")
        cs = [r for r in part if r.get("curn_sourced")]
        if cs:
            print(f"  NOT like-for-like ({len(cs)}): the deterministic table "
                  f"prints these in bold, meaning their values come from the "
                  f"CURN analysis, not the favoured single-pulsar model: "
                  + ", ".join(r["psr"] for r in cs))
        print(f"\n{'psr':13s} {'agree':>7s} {'dlnL':>9s} {'class':<24s} misses")
        for r in sorted(part, key=lambda r: -(r["dlnl"] or 0)):
            print(f"{r['psr']:13s} {r['n_agree']:3d}/{r['n_compared']:<3d} "
                  f"{(r['dlnl'] if r['dlnl'] is not None else float('nan')):+9.2f} "
                  f"{str(r['miss_class']):<24s} "
                  f"{', '.join(m['key'] for m in r['misses'])}")
        dl = [r["dlnl"] for r in gated if r["dlnl"] is not None]
        if dl:
            print(f"\ndlnL(best - published) over {len(dl)} gated pulsars: "
                  f"median {np.median(dl):+.2f}, "
                  f"{sum(1 for x in dl if x > 0)} positive, "
                  f"{sum(1 for x in dl if x < 0)} negative, "
                  f"range {min(dl):+.1f}..{max(dl):+.1f}")
    rel = [r for r in started if r.get("gate_rel")]
    extra = [r for r in rel if not r["gate"]]
    print(f"\nPOST-HOC diagnostic (declared, not the registered gate): under "
          f"a scale-RELATIVE stability rule\n  |median shift| <= max("
          f"registered tol, 0.1 x 68% width), {len(rel)} runs would clear "
          f"({len(extra)} more than the registered {len(gated)})")
    if extra:
        blk = Counter(r["rel_worst"][0].split("_")[-1] if r["rel_worst"]
                      else "?" for r in started if not r["gate"])
        print(f"  parameter holding the registered gate, over runs that miss "
              f"it: {dict(blk.most_common(6))}")
    nogate = [r for r in started if not r["gate"]]
    for r in nogate:
        print(f"  NO-GATE {r['psr']}: exit={r['exit']} raw={r['raw_postburn']} "
              f"acc={r['acc']} stable={r['stable']}")
    (RES / "campaign_table.json").write_text(json.dumps(rows, indent=1))
    print(f"\n-> {RES/'campaign_table.json'}")


if __name__ == "__main__":
    main()
