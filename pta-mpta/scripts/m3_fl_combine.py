#!/usr/bin/env python3
"""M3 factorised-likelihood CURN combination over the whole array, formed
twice: once from the `fl` runs (the collaboration's own common-signal
configuration -- favoured model PLUS a free achromatic red process where
absent) and once from the `table` runs (the published noise table taken at
face value -- favoured model exactly as tabulated).

Pre-registered F-criteria: M3-noise-criticism.md section 1.6.
Method: the paper's own (Taylor et al. 2022, 2022PhRvD.105h4049T) -- with
identical uniform priors on log10 A_CURN in every run, the factorised
posterior is the renormalised product of the per-pulsar marginals.

Usage:
    python scripts/m3_fl_combine.py                 # all gated pulsars
    python scripts/m3_fl_combine.py --subset top10  # M2's exact ten
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
FIG = REPO / "figures"
TAB = json.loads((RES / "published_table.json").read_text())

PUB_FL = (-14.28, 0.21)   # arXiv:2412.01148, FL, gamma = 13/3
M2_FL = dict(map=-14.46, median=-14.53, ci68=[-14.92, -14.31])
GRID = np.linspace(-18.0, -11.0, 3001)
GATE = 50_000
TOP10 = ["J1713+0747", "J2241-5236", "J0437-4715", "J1909-3744",
         "J1744-1134", "J0125-2327", "J1946-5403", "J1600-3053",
         "J1017-7156", "J2129-5721"]


def stats(grid, dens):
    dens = np.clip(dens, 0, None)
    dens = dens / np.trapezoid(dens, grid)
    cdf = np.cumsum(dens) * (grid[1] - grid[0])
    return dict(map=float(grid[int(np.argmax(dens))]),
                median=float(grid[np.searchsorted(cdf, 0.5)]),
                ci68=[float(grid[np.searchsorted(cdf, 0.16)]),
                      float(grid[np.searchsorted(cdf, 0.84)])]), dens


def load(variant, tag, psrs):
    per, flagged = {}, []
    for psr in psrs:
        rid = f"{psr}_{variant}_{tag}"
        f, s = RES / f"{rid}.curn.npy", RES / f"{rid}.summary.json"
        if not (f.exists() and s.exists()):
            flagged.append(psr)
            continue
        summ = json.loads(s.read_text())
        ch = summ.get("chain") or {}
        ok = bool(summ.get("gate_met")) and ch.get("raw_postburn", 0) >= GATE
        if not ok:
            flagged.append(psr)
        per[psr] = dict(samples=np.load(f).astype(float), ok=ok,
                        raw_postburn=ch.get("raw_postburn", 0),
                        acc=ch.get("acc_rate"))
    return per, flagged


def product(per, keys):
    logd = np.zeros_like(GRID)
    for k in keys:
        kde = gaussian_kde(per[k]["samples"])
        logd += np.log(np.clip(kde(GRID), 1e-300, None))
    return stats(GRID, np.exp(logd - logd.max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", choices=["all", "top10"], default="all")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    psrs = TOP10 if args.subset == "top10" else sorted(TAB)
    out = args.out or f"fl_curn_{args.subset}"

    res = dict(subset=args.subset, n_requested=len(psrs),
               published_83=dict(map=PUB_FL[0],
                                 ci68=[PUB_FL[0] - PUB_FL[1],
                                       PUB_FL[0] + PUB_FL[1]],
                                 source="arXiv:2412.01148 FL gamma=13/3"),
               m2_top10=M2_FL, variants={})
    dens_store = {}
    loaded = {v: load(v, tg, psrs) for v, tg in (("fl", "f1"),
                                                 ("table", "t1"))}
    # the fl-vs-table comparison is only meaningful on the SAME pulsars:
    # both products are additionally formed on the intersection of the two
    # gated sets, and that intersection is what the seam-(b) shift uses.
    common = sorted(set(k for k, v in loaded["fl"][0].items() if v["ok"])
                    & set(k for k, v in loaded["table"][0].items()
                          if v["ok"]))
    res["common_set"] = common
    res["n_common"] = len(common)
    for variant, tag in (("fl", "f1"), ("table", "t1")):
        per, flagged = loaded[variant]
        ok = [k for k in per if per[k]["ok"]]
        if not ok:
            print(f"[{variant}] no gated runs yet")
            continue
        if common:
            r_c, _ = product(per, common)
            res.setdefault("common", {})[variant] = r_c
        r, dens = product(per, ok)
        dens_store[variant] = (dens, ok, per)
        res["variants"][variant] = dict(
            n_used=len(ok), n_flagged=len(flagged), flagged=flagged,
            result=r,
            per_pulsar={k: dict(median=float(np.median(v["samples"])),
                                ci68=[float(np.percentile(v["samples"], 16)),
                                      float(np.percentile(v["samples"], 84))],
                                raw_postburn=int(v["raw_postburn"]),
                                acc=v["acc"], ok=bool(v["ok"]))
                        for k, v in per.items()})
        lo, hi = r["ci68"]
        plo, phi = PUB_FL[0] - PUB_FL[1], PUB_FL[0] + PUB_FL[1]
        res["variants"][variant]["consistent_with_published"] = bool(
            max(lo, plo) <= min(hi, phi))
        print(f"[{variant}] {len(ok)} pulsars -> MAP {r['map']:.2f} "
              f"median {r['median']:.2f} 68% "
              f"[{r['ci68'][0]:.2f}, {r['ci68'][1]:.2f}]  "
              f"consistent with published: "
              f"{res['variants'][variant]['consistent_with_published']}")

    if {"fl", "table"} <= set(res.get("common", {})):
        a = res["common"]["fl"]
        b = res["common"]["table"]
        d_map = b["map"] - a["map"]
        excl = not (a["ci68"][0] <= b["map"] <= a["ci68"][1]) or \
               not (b["ci68"][0] <= a["map"] <= b["ci68"][1])
        res["seam_b_shift"] = dict(
            d_map_table_minus_fl=float(d_map),
            d_median=float(b["median"] - a["median"]),
            criterion="significant iff |dMAP| > 0.21 dex or either 68% "
                      "excludes the other MAP (M3 doc 1.6 F4)",
            significant=bool(abs(d_map) > 0.21 or excl))
        print(f"[seam b] on the {len(common)} pulsars gated in BOTH: "
              f"fl MAP {a['map']:.2f} 68% [{a['ci68'][0]:.2f},"
              f"{a['ci68'][1]:.2f}] vs table MAP {b['map']:.2f} 68% "
              f"[{b['ci68'][0]:.2f},{b['ci68'][1]:.2f}]")
        print(f"[seam b] table - fl: dMAP {d_map:+.3f} dex, "
              f"significant={res['seam_b_shift']['significant']}")

    (RES / f"{out}.json").write_text(json.dumps(res, indent=1))
    print(f"-> results/m3/{out}.json")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=150)
        cols = {"fl": "#20567C", "table": "#7A3E9D"}
        labs = {"fl": "favoured + free red (the collaboration's CURN config)",
                "table": "favoured model as tabulated (noise table at face "
                         "value)"}
        for variant, (dens, ok, per) in dens_store.items():
            if variant == "fl":
                for k in ok:
                    kde = gaussian_kde(per[k]["samples"])
                    d = kde(GRID)
                    ax.plot(GRID, d / d.max() * 0.30, lw=0.6, alpha=0.35,
                            color="#8FB4CE")
            r = res["variants"][variant]["result"]
            ax.plot(GRID, dens / dens.max(), lw=2.2, color=cols[variant],
                    label=f"{labs[variant]}\n  MAP {r['map']:.2f}, "
                          f"68% [{r['ci68'][0]:.2f}, {r['ci68'][1]:.2f}] "
                          f"({res['variants'][variant]['n_used']} psr)")
        ax.axvline(PUB_FL[0], color="#C4552D", lw=1.6,
                   label="published 83-psr FL: $-14.28\\pm0.21$")
        ax.axvspan(PUB_FL[0] - PUB_FL[1], PUB_FL[0] + PUB_FL[1],
                   color="#C4552D", alpha=0.12)
        ax.set_xlim(-16.0, -13.0)
        ax.set_xlabel("$\\log_{10} A_{\\rm CURN}$ ($\\gamma = 13/3$)")
        ax.set_ylabel("normalised density")
        ax.set_title("MPTA factorised-likelihood CURN under two model choices")
        ax.legend(fontsize=7.5, loc="upper left")
        fig.tight_layout()
        FIG.mkdir(exist_ok=True)
        fig.savefig(FIG / f"m3_{out}.png")
        print(f"[saved] figures/m3_{out}.png")
    except Exception as e:
        print(f"[warn] figure skipped: {e}")


if __name__ == "__main__":
    main()
