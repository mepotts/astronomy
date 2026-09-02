#!/usr/bin/env python3
"""M4: apply the pre-registered scale-relative stability rule (R1) uniformly to
every run on disk -- old and new -- and report BOTH gate outcomes side by side.

Pre-registration: pta-mpta/M4-finish-the-array.md section 1.2.

  absolute (M1/M2/M3):  |median_lasthalf - median_full| <= t_abs
  relative (M4, R1):    |median_lasthalf - median_full| <= max(t_abs, 0.1*W68)

R1 is a STRICT RELAXATION, so it can only add runs, never remove them.  That is
exactly why R3 requires both columns to be printed together: adopting the new
rule silently would make the array look better for free.

Every quantity needed is already stored per-parameter in each run's summary
JSON (median, ci68, halfshift, tol), so the re-gate is exact and needs no chain
reload.  ESS (R4, recorded not gated) is computed from the chain when
--ess is given.

Usage:
    python scripts/m4_regate.py                 # re-gate + report
    python scripts/m4_regate.py --write         # also write the fields back
    python scripts/m4_regate.py --write --ess   # ... and compute ESS
"""
import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m4" / "regate.json"
VARIANTS = [("noise", "n1", 100_000), ("table", "t1", 50_000),
            ("fl", "f1", 50_000), ("swwide", "s1", 100_000)]


def verdicts(summ, gate_raw, min_acc=0.05):
    """Recompute (abs, rel) gate outcomes from a summary's stored fields."""
    ch = summ.get("chain")
    if not ch:
        return None
    ok_size = ch.get("raw_postburn", 0) >= gate_raw
    ok_acc = (ch.get("acc_rate") or 0.0) >= min_acc
    st_abs, st_rel = True, True
    rows = []
    for p in ch["params"]:
        lo, hi = p["ci68"]
        w68 = float(hi - lo)
        tol = float(p["tol"])
        tol_rel = max(tol, 0.1 * w68)
        shift = float(p["halfshift"])
        a, r = shift <= tol, shift <= tol_rel
        st_abs &= a
        st_rel &= r
        rows.append(dict(param=p["param"], halfshift=shift, tol=tol,
                         w68=round(w68, 4), tol_rel=round(tol_rel, 4),
                         stable=a, stable_rel=r,
                         bound_by=("abs" if tol >= 0.1 * w68 else "rel"),
                         ess=p.get("ess")))
    return dict(ok_size=ok_size, ok_acc=ok_acc,
                stable=st_abs, stable_rel=st_rel,
                gate_abs=bool(ok_size and ok_acc and st_abs),
                gate_rel=bool(ok_size and ok_acc and st_rel),
                raw_postburn=ch.get("raw_postburn", 0),
                acc=ch.get("acc_rate"), params=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write stable_rel / gate_met_abs / gate_met_rel back "
                         "into each summary JSON")
    ap.add_argument("--ess", action="store_true",
                    help="also compute per-parameter ESS from the chain files")
    args = ap.parse_args()

    if args.ess:
        import sys
        import numpy as np
        sys.path.insert(0, str(Path(__file__).parent))
        import mpta_harness as H

    allrows = {}
    for variant, tag, gate_raw in VARIANTS:
        rows = []
        for f in sorted(RES.glob(f"*_{variant}_{tag}.summary.json")):
            psr = f.name.split("_")[0]
            s = json.loads(f.read_text())
            v = verdicts(s, gate_raw)
            if v is None:
                continue
            v["psr"] = psr
            v["state"] = s.get("state")
            v["exit"] = s.get("exit_reason")
            v["gate_met_recorded"] = bool(s.get("gate_met"))
            v["gate_rule_used"] = s.get("gate_rule", "absolute")
            if args.ess:
                cf = H._chain_file(REPO / "chains" / "m3"
                                   / f"{psr}_{variant}_{tag}")
                if cf is not None:
                    try:
                        ch = np.loadtxt(cf, ndmin=2)
                        nd = len(s["chain"]["params"])
                        post = ch[len(ch) // 4:, :nd]
                        for i, pr in enumerate(v["params"]):
                            pr["ess"] = round(H._ess(post[:, i]), 1)
                        v["ess_min"] = min(pr["ess"] for pr in v["params"])
                    except Exception as e:  # noqa: BLE001
                        v["ess_error"] = repr(e)
            if args.write:
                ch = s["chain"]
                ch["stable_rel"] = v["stable_rel"]
                for pr, src in zip(ch["params"], v["params"]):
                    pr["w68"] = src["w68"]
                    pr["tol_rel"] = src["tol_rel"]
                    pr["stable_rel"] = src["stable_rel"]
                    pr["bound_by"] = src["bound_by"]
                    if src.get("ess") is not None:
                        pr["ess"] = src["ess"]
                if v.get("ess_min") is not None:
                    ch["ess_min"] = v["ess_min"]
                s["gate_met_abs"] = v["gate_abs"]
                s["gate_met_rel"] = v["gate_rel"]
                # `gate_met` is what every downstream tool reads (campaign
                # skip logic, m3_status, m3_analyze, the FL products).  M4's
                # REGISTERED gate is the relative rule, so that is what it
                # now carries; the M3-as-reported value is preserved beside
                # it so the audit trail is not overwritten.
                s.setdefault("gate_met_m3", bool(s.get("gate_met")))
                # A run killed mid-flight has a harness-written summary but no
                # POST-PROCESSING (no a2 comparison, no curn marginal, no
                # saved posterior) because m3_run.py never returned.  Marking
                # such a run gate_met would make the campaign skip it and
                # silently drop it from every downstream product, so it is
                # left ungated and the pool finishes it.
                need = "a2" if variant in ("noise", "swwide") else "curn"
                post_ok = need in s
                s["postprocessed"] = bool(post_ok)
                s["gate_met"] = bool(v["gate_rel"] and post_ok)
                s["gate_rule"] = "relative"
                tmp = f.with_suffix(".tmp")
                tmp.write_text(json.dumps(s, indent=2))
                tmp.replace(f)
            rows.append(v)
        allrows[variant] = rows

        ga = [r for r in rows if r["gate_abs"]]
        gr = [r for r in rows if r["gate_rel"]]
        only = [r["psr"] for r in rows if r["gate_rel"] and not r["gate_abs"]]
        lost = [r["psr"] for r in rows if r["gate_abs"] and not r["gate_rel"]]
        print(f"[{variant}] {len(rows)} runs with a chain: "
              f"absolute gate {len(ga)}, relative gate {len(gr)}")
        if only:
            print(f"  relative-only ({len(only)}): {', '.join(sorted(only))}")
        if lost:
            print(f"  !! LOST under relative ({len(lost)}): {lost} "
                  f"-- impossible unless the rule was mis-implemented")
        # which parameter holds the absolute gate on the runs it blocks
        held = {}
        for r in rows:
            if r["gate_rel"] and not r["stable"]:
                for p in r["params"]:
                    if not p["stable"]:
                        held[p["param"].split("_", 1)[-1]] = \
                            held.get(p["param"].split("_", 1)[-1], 0) + 1
        if held:
            top = sorted(held.items(), key=lambda kv: -kv[1])[:8]
            print("  absolute rule held by: "
                  + ", ".join(f"{k}x{v}" for k, v in top))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(allrows, indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
