#!/usr/bin/env python3
"""M2 campaign analysis: agreement table (C2) + mode-vs-model diagnostics for
every miss (C3) + updated economics. Run after the campaign.

Usage: python scripts/m2_analyze.py [--runs TAGMAP] [--no-diag]
By default reads <psr>_noise_c1 for the nine, J1909-3744_noise_blind1/blind2/
informed for the flagship, and writes results/m2/campaign_table.json.
The C3 diagnostic rebuilds each miss's PTA and evaluates lnL at the published
MAP vector vs the chain's best point (M1's w2_j1909_mode_diag generalised).
"""
import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results" / "m2"
CHAINS = REPO / "chains" / "m2"
PARTIM = REPO / "data" / "partim"
TDBDIR = REPO / "data" / "partim_tdb"

import sys
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models as M


def load_summary(run_id):
    p = RESULTS / f"{run_id}.summary.json"
    return json.loads(p.read_text()) if p.exists() else None


def diagnose(psr, summary):
    """C3: lnL(published MAP) - lnL(chain best) under our likelihood."""
    pta, _ = M.build_pta(psr, str(TDBDIR), str(PARTIM))
    xpub, missing = M.published_vector(pta, psr)
    if xpub is None:
        return dict(error=f"no published value for {missing}")

    def _f(v):  # enterprise may return a size-1 KernelMatrix (numpy 2.x)
        return float(np.asarray(v).reshape(-1)[0])

    ll_pub = _f(pta.get_lnlikelihood(xpub))
    best = summary.get("best_point")
    xbest = np.array([best[p] for p in pta.param_names])
    ll_best = _f(pta.get_lnlikelihood(xbest))
    return dict(lnl_published=ll_pub, lnl_chain_best=ll_best,
                delta=ll_pub - ll_best,
                reading=("sampling shortfall (published solution scores "
                         "higher under our likelihood)" if ll_pub > ll_best
                         else "our likelihood prefers our solution -> "
                              "convention/model finding"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-diag", action="store_true",
                    help="skip lnL diagnostics (no PTA rebuilds)")
    args = ap.parse_args()

    runs = {psr: f"{psr}_noise_c1" for psr in M.TOP10}
    runs["J1909-3744"] = "J1909-3744_noise_blind1"
    extra = ["J1909-3744_noise_blind2", "J1909-3744_noise_informed"]

    table, n_full, n_gate = [], 0, 0
    for psr in M.TOP10:
        s = load_summary(runs[psr])
        if s is None:
            table.append(dict(psr=psr, run=runs[psr], missing=True))
            continue
        gate = bool(s.get("gate_met"))
        n_gate += gate
        full = s.get("n_agree") == s.get("n_compared")
        n_full += bool(full and s.get("n_compared"))
        misses = [r for r in s.get("a2", [])
                  if r.get("agree") is False]
        row = dict(psr=psr, run=runs[psr], gate_met=gate,
                   raw_iters=(s.get("chain") or {}).get("raw_iters"),
                   stable=(s.get("chain") or {}).get("stable"),
                   agree=f"{s.get('n_agree')}/{s.get('n_compared')}",
                   full_agreement=bool(full),
                   eval_ms=s.get("eval_ms"),
                   elapsed_min=s.get("elapsed_min"),
                   exit=s.get("exit_reason"),
                   misses=[m["param"] for m in misses])
        if misses and not args.no_diag:
            print(f"[diag] {psr}: {len(misses)} miss(es), evaluating "
                  "mode-vs-model ...")
            row["diagnostic"] = diagnose(psr, s)
        table.append(row)
        print(f"[{psr}] gate={gate} agree={row['agree']} "
              f"misses={row['misses']}")

    j1909 = {}
    for rid in [runs["J1909-3744"]] + extra:
        s = load_summary(rid)
        if s is None:
            continue
        ch = s.get("chain") or {}
        j1909[rid] = dict(
            exit=s.get("exit_reason"), gate=s.get("gate_met"),
            raw=ch.get("raw_iters"), stable=ch.get("stable"),
            lnl_best=s.get("lnl_best"),
            frac_dm_mode=s.get("frac_n_earth_lt_15"),
            agree=f"{s.get('n_agree')}/{s.get('n_compared')}",
            x0_kind=s.get("x0_kind"))

    out = dict(
        generated_utc=__import__("time").strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  __import__("time").gmtime()),
        n_gate_met=n_gate, n_full_agreement=n_full, table=table,
        j1909_chains=j1909,
        published_source="arXiv:2412.01148 Tables 'MPTA noise models' + "
                         "'MPTA determinstic models' (LaTeX source, "
                         "retrieved 2026-08-16)")
    (RESULTS / "campaign_table.json").write_text(json.dumps(out, indent=2))
    print(f"[saved] results/m2/campaign_table.json  "
          f"(gate {n_gate}/10, full agreement {n_full}/10)")


if __name__ == "__main__":
    main()
