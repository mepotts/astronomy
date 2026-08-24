#!/usr/bin/env python3
"""M4 C2 + R3 + R5: agreement statistics over the noise campaign, reported
under BOTH stability gates side by side.

Pre-registration: M4-finish-the-array.md 1.2 (R3 requires both columns
always; R5 is the falsifier -- if the relative-only pulsars agree with the
published table WORSE than the absolute-gated ones, the relaxation bought
coverage at the price of accuracy and the headline reverts).

Reads each run's summary directly (they carry both `stable` and `stable_rel`
after scripts/m4_regate.py --write, and natively for runs sampled by M4).

    python scripts/m4_analyze.py
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m4" / "agreement_both_gates.json"
TAB = json.loads((RES / "published_table.json").read_text())
GATE_RAW = 100_000
MIN_ACC = 0.05


def load():
    rows = []
    diag = {}
    for f in (RES / "diag").glob("*.json"):
        d = json.loads(f.read_text())
        diag[d["psr"]] = d
    for psr in sorted(TAB):
        p = RES / f"{psr}_noise_n1.summary.json"
        if not p.exists():
            rows.append(dict(psr=psr, state="not-started"))
            continue
        s = json.loads(p.read_text())
        ch = s.get("chain") or {}
        base = (ch.get("raw_postburn", 0) >= GATE_RAW
                and (ch.get("acc_rate") or 0) >= MIN_ACC)
        rows.append(dict(
            psr=psr, state=s.get("state"), exit=s.get("exit_reason"),
            raw=ch.get("raw_postburn", 0), acc=ch.get("acc_rate"),
            ess_min=ch.get("ess_min"),
            gate_abs=bool(base and ch.get("stable")),
            gate_rel=bool(base and ch.get("stable_rel")),
            n_agree=s.get("n_agree"), n_compared=s.get("n_compared"),
            misses=[m["key"] for m in s.get("a2", [])
                    if m.get("agree") is False],
            dlnl=diag.get(psr, {}).get("dlnl_best_minus_pub"),
            elapsed=s.get("elapsed_min"), eval_ms=s.get("eval_ms")))
    return rows


def block(rows, key, label):
    sel = [r for r in rows if r.get(key)]
    if not sel:
        print(f"  {label}: 0 pulsars")
        return dict(n=0)
    with_a2 = [r for r in sel if r.get("n_compared")]
    full = [r for r in with_a2 if r["n_agree"] == r["n_compared"]]
    na = sum(r["n_agree"] for r in with_a2)
    nc = sum(r["n_compared"] for r in with_a2)
    accs = [r["acc"] for r in sel if r["acc"] is not None]
    ess = [r["ess_min"] for r in sel if r.get("ess_min")]
    print(f"  {label}: {len(sel)}/83 gated | "
          f"{len(full)}/{len(with_a2)} pulsars agree in full | "
          f"{na}/{nc} parameters ({100*na/nc:.1f}%) | "
          f"acceptance {min(accs):.3f}-{max(accs):.3f}"
          + (f" | min-ESS median {int(np.median(ess))}" if ess else ""))
    return dict(n=len(sel), n_full=len(full), n_with_a2=len(with_a2),
                params_agree=na, params_total=nc,
                pct=round(100 * na / nc, 2),
                acc_min=min(accs), acc_max=max(accs),
                ess_min_median=(float(np.median(ess)) if ess else None),
                pulsars=[r["psr"] for r in sel])


def main():
    rows = load()
    started = [r for r in rows if r.get("state") not in (None, "not-started")]
    print(f"COVERAGE: {len(started)}/83 started, "
          f"{83-len(started)} never started")
    print("\nR3 -- BOTH GATES, SIDE BY SIDE "
          "(the relative rule is a strict relaxation, so it can only add):")
    res = dict(absolute=block(rows, "gate_abs", "ABSOLUTE  (M1/M2/M3 rule)"),
               relative=block(rows, "gate_rel", "RELATIVE  (M4 R1 rule)   "))

    only = [r for r in rows if r.get("gate_rel") and not r.get("gate_abs")]
    lost = [r for r in rows if r.get("gate_abs") and not r.get("gate_rel")]
    res["relative_only"] = [r["psr"] for r in only]
    res["lost_under_relative"] = [r["psr"] for r in lost]
    print(f"\n  relative-only pulsars ({len(only)}): "
          + (", ".join(r["psr"] for r in only) or "none"))
    if lost:
        print(f"  !! LOST under relative: {[r['psr'] for r in lost]} "
              "-- impossible unless mis-implemented")

    # R5 falsifier: does the relative-only set agree WORSE?
    if only:
        oa = [r for r in only if r.get("n_compared")]
        na = sum(r["n_agree"] for r in oa)
        nc = sum(r["n_compared"] for r in oa)
        base = res["absolute"]
        p0 = base["params_agree"] / base["params_total"]
        sig = (p0 * (1 - p0) / base["params_total"]) ** 0.5
        p1 = na / nc if nc else float("nan")
        verdict = ("PASS" if not nc or p1 >= p0 - sig
                   else "FAIL -- headline reverts to the absolute-gated set")
        print(f"\n  R5 falsifier: relative-only agreement "
              f"{na}/{nc} ({100*p1:.1f}%) vs absolute-gated {100*p0:.1f}% "
              f"(1 sigma {100*sig:.1f}%) -> {verdict}")
        res["r5"] = dict(only_agree=na, only_total=nc, only_pct=100 * p1,
                         abs_pct=100 * p0, one_sigma_pct=100 * sig,
                         verdict=verdict)
        ess_o = [r["ess_min"] for r in only if r.get("ess_min")]
        ess_a = [r["ess_min"] for r in rows
                 if r.get("gate_abs") and r.get("ess_min")]
        if ess_o and ess_a:
            print(f"  R4 (recorded, not gated): min-ESS median "
                  f"{np.median(ess_o):.0f} (relative-only) vs "
                  f"{np.median(ess_a):.0f} (absolute-gated)")
            res["r4"] = dict(ess_only=float(np.median(ess_o)),
                             ess_abs=float(np.median(ess_a)))

    # misses, under the registered (relative) gate
    part = [r for r in rows if r.get("gate_rel") and r.get("n_compared")
            and r["n_agree"] != r["n_compared"]]
    keyc = Counter(k for r in part for k in r["misses"])
    print(f"\nMISSES under the registered M4 gate: {len(part)} pulsars, "
          f"{sum(len(r['misses']) for r in part)} parameters -> "
          f"{dict(keyc.most_common())}")
    for r in sorted(part, key=lambda r: -(r["dlnl"] or 0)):
        print(f"  {r['psr']:13s} {r['n_agree']:3d}/{r['n_compared']:<3d} "
              f"dlnL={r['dlnl'] if r['dlnl'] is not None else float('nan'):+8.2f}"
              f"  {', '.join(r['misses'])}")
    res["misses"] = [dict(psr=r["psr"], n_agree=r["n_agree"],
                          n_compared=r["n_compared"], keys=r["misses"],
                          dlnl=r["dlnl"]) for r in part]
    res["miss_keys"] = dict(keyc)

    dl = [r["dlnl"] for r in rows if r.get("gate_rel")
          and r.get("dlnl") is not None]
    if dl:
        print(f"\ndlnL(ours - published) over {len(dl)} gated pulsars: "
              f"median {np.median(dl):+.2f}, "
              f"{sum(1 for x in dl if x > 0)} positive / "
              f"{sum(1 for x in dl if x < 0)} negative, "
              f"range {min(dl):+.2f}..{max(dl):+.2f}")
        res["dlnl"] = dict(n=len(dl), median=float(np.median(dl)),
                           n_pos=sum(1 for x in dl if x > 0),
                           n_neg=sum(1 for x in dl if x < 0),
                           min=min(dl), max=max(dl))

    cpu = sum(r.get("elapsed") or 0 for r in rows) / 60.0
    res["noise_campaign_hours_this_variant"] = round(cpu, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
