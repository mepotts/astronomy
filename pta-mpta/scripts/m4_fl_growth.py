#!/usr/bin/env python3
"""M4 F5: the registered volatility check on the factorised-likelihood CURN.

M3 saw the 36-pulsar `fl` product move 0.16 dex when the 36th pulsar arrived,
and concluded that a subset product cannot stand in for the full one.  This
measures that directly: the FL MAP and 68% width as a function of how many
pulsars are in the product, adding pulsars in a RANDOM order fixed by seed 4
(pre-registered in M4-finish-the-array.md section 1.4, F5 -- a random order,
not a constraint-strength order, which would manufacture a trend).

Reports the curve, and how much the MAP still moves over the last 10 additions
(the operational meaning of "the product has converged").

    python scripts/m4_fl_growth.py --variant fl
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUTD = REPO / "results" / "m4"
FIG = REPO / "figures"
TAB = json.loads((RES / "published_table.json").read_text())
GRID = np.linspace(-18.0, -11.0, 3001)
GATE = 50_000
SEED = 4          # pre-registered


def stats(dens):
    dens = np.clip(dens, 0, None)
    dens = dens / np.trapezoid(dens, GRID)
    cdf = np.cumsum(dens) * (GRID[1] - GRID[0])
    lo = float(GRID[np.searchsorted(cdf, 0.16)])
    hi = float(GRID[np.searchsorted(cdf, 0.84)])
    return dict(map=float(GRID[int(np.argmax(dens))]),
                median=float(GRID[np.searchsorted(cdf, 0.5)]),
                ci68=[lo, hi], width=round(hi - lo, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="fl", choices=["fl", "table"])
    args = ap.parse_args()
    tag = {"fl": "f1", "table": "t1"}[args.variant]

    usable = []
    for psr in sorted(TAB):
        rid = f"{psr}_{args.variant}_{tag}"
        f, s = RES / f"{rid}.curn.npy", RES / f"{rid}.summary.json"
        if not (f.exists() and s.exists()):
            continue
        summ = json.loads(s.read_text())
        ch = summ.get("chain") or {}
        if summ.get("gate_met") and ch.get("raw_postburn", 0) >= GATE:
            usable.append(psr)

    rng = np.random.default_rng(SEED)
    order = list(rng.permutation(usable))
    logk = {p: np.log(np.clip(gaussian_kde(
        np.load(RES / f"{p}_{args.variant}_{tag}.curn.npy").astype(float)
    )(GRID), 1e-300, None)) for p in order}

    curve, acc = [], np.zeros_like(GRID)
    for i, p in enumerate(order, 1):
        acc = acc + logk[p]
        st = stats(np.exp(acc - acc.max()))
        st.update(n=i, added=p)
        curve.append(st)

    print(f"[{args.variant}] {len(order)} gated pulsars, random order seed "
          f"{SEED}")
    for st in curve:
        if st["n"] % 5 == 0 or st["n"] == len(order):
            print(f"  n={st['n']:3d}  MAP {st['map']:+.3f}  "
                  f"68% [{st['ci68'][0]:.2f}, {st['ci68'][1]:.2f}]  "
                  f"width {st['width']:.2f}  (+{st['added']})")
    if len(curve) >= 11:
        last = [c["map"] for c in curve[-11:]]
        swing = max(last) - min(last)
        print(f"  MAP swing over the final 10 additions: {swing:.3f} dex")
    else:
        swing = None
    out = dict(variant=args.variant, seed=SEED, n=len(order), order=order,
               curve=curve, final=curve[-1] if curve else None,
               map_swing_last10=swing)
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f"fl_growth_{args.variant}.json").write_text(
        json.dumps(out, indent=1))
    print(f"-> results/m4/fl_growth_{args.variant}.json")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ns = [c["n"] for c in curve]
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.6, 5.4), dpi=150,
                                     sharex=True,
                                     gridspec_kw=dict(height_ratios=[2, 1]))
        a1.fill_between(ns, [c["ci68"][0] for c in curve],
                        [c["ci68"][1] for c in curve],
                        color="#8FB4CE", alpha=0.5, label="68% interval")
        a1.plot(ns, [c["map"] for c in curve], color="#20567C", lw=1.8,
                label="MAP")
        a1.axhline(-14.28, color="#C4552D", lw=1.4,
                   label="published 83-psr FL $-14.28$")
        a1.axhspan(-14.49, -14.07, color="#C4552D", alpha=0.12)
        a1.set_ylabel("$\\log_{10} A_{\\rm CURN}$")
        a1.legend(fontsize=8, loc="lower right")
        a1.set_title(f"F5 volatility check: FL product vs pulsar count "
                     f"({args.variant}, random order seed {SEED})")
        a2.plot(ns, [c["width"] for c in curve], color="#7A3E9D", lw=1.8)
        a2.set_ylabel("68% width (dex)")
        a2.set_xlabel("pulsars in the product")
        fig.tight_layout()
        FIG.mkdir(exist_ok=True)
        fig.savefig(FIG / f"m4_fl_growth_{args.variant}.png")
        print(f"[saved] figures/m4_fl_growth_{args.variant}.png")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] figure skipped: {e}")


if __name__ == "__main__":
    main()
