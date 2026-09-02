#!/usr/bin/env python3
"""M2 factorised-likelihood CURN combination (pre-registered F-criteria).

Method (paper's own; Taylor et al. 2022, 2022PhRvD.105h4049T): with identical
uniform priors on log10_A_CURN in every per-pulsar run, the factorised
posterior is proportional to the product of the per-pulsar marginals.
Implemented as a product of Gaussian KDEs evaluated on the prior support;
pulsars failing the F2 gate are flagged and the product is reported both with
and without them.

Usage: python scripts/m2_fl_combine.py [--tag fl1]
Writes results/m2/fl_curn.json and figures/m2_fl_curn.png.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results" / "m2"
FIGURES = REPO / "figures"

import sys
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models as M

PUB_FL = (-14.28, 0.21)  # published 83-pulsar FL result, arXiv:2412.01148
GRID = np.linspace(-18.0, -11.0, 3001)
F2_GATE = 50_000


def stats(grid, dens):
    dens = np.clip(dens, 0, None)
    Z = np.trapezoid(dens, grid)
    dens = dens / Z
    cdf = np.cumsum(dens) * (grid[1] - grid[0])
    med = grid[np.searchsorted(cdf, 0.5)]
    lo = grid[np.searchsorted(cdf, 0.16)]
    hi = grid[np.searchsorted(cdf, 0.84)]
    mapv = grid[int(np.argmax(dens))]
    return dict(map=float(mapv), median=float(med),
                ci68=[float(lo), float(hi)]), dens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="fl1")
    ap.add_argument("--use", action="append", default=[],
                    help="per-pulsar tag override, e.g. J1909-3744=fl2")
    ap.add_argument("--out", default="fl_curn",
                    help="basename for results JSON and figure")
    args = ap.parse_args()
    override = dict(kv.split("=", 1) for kv in args.use)

    per, flagged = {}, []
    for psr in M.TOP10:
        rid = f"{psr}_fl_{override.get(psr, args.tag)}"
        f = RESULTS / f"{rid}.curn.npy"
        s = RESULTS / f"{rid}.summary.json"
        if not f.exists():
            print(f"[skip] {psr}: no {f.name}")
            flagged.append(psr)
            continue
        samp = np.load(f)
        summ = json.loads(s.read_text()) if s.exists() else {}
        raw_pb = (summ.get("chain") or {}).get("raw_postburn", 0)
        ok = raw_pb >= F2_GATE
        if not ok:
            flagged.append(psr)
        per[psr] = dict(samples=samp, ok=ok, raw_postburn=raw_pb)
        print(f"[{psr}] n={len(samp)} raw_postburn={raw_pb} "
              f"{'ok' if ok else 'FLAGGED (under F2 gate)'} "
              f"median={np.median(samp):.2f}")

    def product(keys):
        logd = np.zeros_like(GRID)
        for k in keys:
            kde = gaussian_kde(per[k]["samples"])
            d = np.clip(kde(GRID), 1e-300, None)
            logd += np.log(d)
        dens = np.exp(logd - logd.max())
        return stats(GRID, dens)

    all_keys = list(per)
    ok_keys = [k for k in all_keys if per[k]["ok"]]
    res_all, dens_all = product(all_keys)
    res = dict(
        n_pulsars=len(all_keys), flagged=flagged,
        fl_all=res_all,
        published_83=dict(map=PUB_FL[0], ci68=[PUB_FL[0] - PUB_FL[1],
                                               PUB_FL[0] + PUB_FL[1]],
                          source="arXiv:2412.01148 (FL, gamma=13/3)"),
        per_pulsar={k: dict(median=float(np.median(v["samples"])),
                            ci68=[float(np.percentile(v["samples"], 16)),
                                  float(np.percentile(v["samples"], 84))],
                            raw_postburn=int(v["raw_postburn"]),
                            ok=bool(v["ok"])) for k, v in per.items()})
    if ok_keys != all_keys and ok_keys:
        res["fl_gated"], dens_ok = product(ok_keys)
        res["gated_pulsars"] = ok_keys

    lo, hi = res_all["ci68"]
    plo, phi = PUB_FL[0] - PUB_FL[1], PUB_FL[0] + PUB_FL[1]
    res["consistent_with_published"] = bool(max(lo, plo) <= min(hi, phi))

    (RESULTS / f"{args.out}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "per_pulsar"},
                     indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
        for k, v in per.items():
            kde = gaussian_kde(v["samples"])
            d = kde(GRID)
            ax.plot(GRID, d / d.max() * 0.35, lw=0.9, alpha=0.6,
                    label=None, color="#8FB4CE")
        ax.plot(GRID, dens_all / dens_all.max(), lw=2.2, color="#20567C",
                label=f"FL product ({len(all_keys)} psr): "
                      f"${res_all['median']:.2f}"
                      f"^{{+{res_all['ci68'][1]-res_all['median']:.2f}}}"
                      f"_{{{res_all['ci68'][0]-res_all['median']:.2f}}}$")
        ax.axvline(PUB_FL[0], color="#C4552D", lw=1.6,
                   label="published 83-psr FL: $-14.28\\pm0.21$")
        ax.axvspan(plo, phi, color="#C4552D", alpha=0.12)
        ax.set_xlim(-17.5, -12.5)
        ax.set_xlabel("$\\log_{10} A_{\\rm CURN}$ ($\\gamma=13/3$)")
        ax.set_ylabel("normalised density")
        ax.set_title("MPTA top-10 factorised-likelihood CURN slice "
                     "(thin: per-pulsar marginals)")
        ax.legend(fontsize=9)
        fig.tight_layout()
        FIGURES.mkdir(exist_ok=True)
        fig.savefig(FIGURES / f"m2_{args.out}.png")
        print(f"[saved] figures/m2_{args.out}.png")
    except Exception as e:
        print(f"[warn] figure skipped: {e}")


if __name__ == "__main__":
    main()
