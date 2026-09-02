#!/usr/bin/env python3
"""M4 F1/F3/F4 + R3: the factorised-likelihood CURN products, formed under
BOTH stability gates.

The M4 registered gate is the scale-relative rule (M4 doc 1.2 R1), and for the
`fl` variant it is worth far more coverage than for `noise` -- so the headline
83-pulsar product leans on it heavily.  R3 forbids reporting that without the
absolute-gated product beside it, which is what this does.

Method unchanged from M2/M3: the paper's own factorised likelihood (Taylor
et al. 2022) -- the renormalised product of the per-pulsar log10 A_CURN
marginals, identical uniform priors making the prior division a constant.
gamma fixed at 13/3 throughout; no Bayes factor, no detection claim, no HD,
no CW.

    python scripts/m4_fl_both_gates.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m4" / "fl_both_gates.json"
FIG = REPO / "figures"
TAB = json.loads((RES / "published_table.json").read_text())
GRID = np.linspace(-18.0, -11.0, 3001)
GATE_RAW = 50_000
MIN_ACC = 0.05
PUB = (-14.28, 0.21)
M2_TOP10 = dict(map=-14.46, median=-14.53, ci68=[-14.92, -14.31])
M3_FL = dict(n=36, map=-14.30, ci68=[-14.92, -14.21])
M3_TABLE = dict(n=33, map=-14.18, ci68=[-14.46, -14.08])
M3_COMMON = dict(n=32, fl=dict(map=-14.34, ci68=[-16.85, -14.31]),
                 table=dict(map=-14.19, ci68=[-14.63, -14.12]))
TOP10 = ["J1713+0747", "J2241-5236", "J0437-4715", "J1909-3744",
         "J1744-1134", "J0125-2327", "J1946-5403", "J1600-3053",
         "J1017-7156", "J2129-5721"]


def stats(dens):
    dens = np.clip(dens, 0, None)
    dens = dens / np.trapezoid(dens, GRID)
    cdf = np.cumsum(dens) * (GRID[1] - GRID[0])
    lo = float(GRID[np.searchsorted(cdf, 0.16)])
    hi = float(GRID[np.searchsorted(cdf, 0.84)])
    return dict(map=round(float(GRID[int(np.argmax(dens))]), 3),
                median=round(float(GRID[np.searchsorted(cdf, 0.5)]), 3),
                ci68=[round(lo, 3), round(hi, 3)], width=round(hi - lo, 3))


def gated(variant, tag, key):
    out = []
    for psr in sorted(TAB):
        rid = f"{psr}_{variant}_{tag}"
        f, s = RES / f"{rid}.curn.npy", RES / f"{rid}.summary.json"
        if not (f.exists() and s.exists()):
            continue
        summ = json.loads(s.read_text())
        ch = summ.get("chain") or {}
        if (ch.get("raw_postburn", 0) >= GATE_RAW
                and (ch.get("acc_rate") or 0) >= MIN_ACC
                and ch.get(key) and "curn" in summ):
            out.append(psr)
    return out


def product(variant, tag, psrs):
    logd = np.zeros_like(GRID)
    for p in psrs:
        s = np.load(RES / f"{p}_{variant}_{tag}.curn.npy").astype(float)
        logd += np.log(np.clip(gaussian_kde(s)(GRID), 1e-300, None))
    return stats(np.exp(logd - logd.max()))


def consistent(a):
    lo, hi = a["ci68"]
    return bool(max(lo, PUB[0] - PUB[1]) <= min(hi, PUB[0] + PUB[1]))


def main():
    res = dict(published=dict(n=83, map=PUB[0],
                              ci68=[PUB[0] - PUB[1], PUB[0] + PUB[1]],
                              source="arXiv:2412.01148 FL, gamma=13/3"),
               m2_top10=M2_TOP10, m3_fl=M3_FL, m3_table=M3_TABLE,
               m3_common32=M3_COMMON, gates={})
    for gkey, gname in (("stable", "absolute"), ("stable_rel", "relative")):
        g = {}
        sets = {}
        for variant, tag in (("fl", "f1"), ("table", "t1")):
            psrs = gated(variant, tag, gkey)
            sets[variant] = psrs
            g[variant] = dict(n=len(psrs), result=product(variant, tag, psrs),
                              pulsars=psrs)
            g[variant]["consistent_with_published"] = consistent(
                g[variant]["result"])
        common = sorted(set(sets["fl"]) & set(sets["table"]))
        g["common"] = dict(n=len(common))
        for variant, tag in (("fl", "f1"), ("table", "t1")):
            g["common"][variant] = product(variant, tag, common)
        a, b = g["common"]["fl"], g["common"]["table"]
        d = b["map"] - a["map"]
        excl = not (a["ci68"][0] <= b["map"] <= a["ci68"][1]) or \
               not (b["ci68"][0] <= a["map"] <= b["ci68"][1])
        g["seam_b"] = dict(d_map_table_minus_fl=round(d, 3),
                           width_fl=a["width"], width_table=b["width"],
                           significant=bool(abs(d) > 0.21 or excl),
                           rule="M3 doc 1.6 F4, carried over unchanged")
        t10 = [p for p in TOP10 if p in sets["fl"]]
        g["top10_fl"] = dict(n=len(t10),
                             result=(product("fl", "f1", t10) if t10 else None),
                             pulsars=t10)
        res["gates"][gname] = g

        print(f"\n=== {gname.upper()} gate ===")
        for variant in ("fl", "table"):
            r = g[variant]["result"]
            print(f"  {variant:5s} {g[variant]['n']:3d} psr -> MAP {r['map']:+.2f} "
                  f"median {r['median']:+.2f} 68% [{r['ci68'][0]:.2f}, "
                  f"{r['ci68'][1]:.2f}] width {r['width']:.2f}  "
                  f"consistent with published: "
                  f"{g[variant]['consistent_with_published']}")
        print(f"  seam (b) on the {len(common)} gated in BOTH: "
              f"fl MAP {a['map']:+.2f} 68% [{a['ci68'][0]:.2f},{a['ci68'][1]:.2f}] "
              f"(w {a['width']:.2f}) vs table MAP {b['map']:+.2f} "
              f"68% [{b['ci68'][0]:.2f},{b['ci68'][1]:.2f}] (w {b['width']:.2f})")
        print(f"  dMAP(table - fl) = {d:+.3f} dex, "
              f"significant={g['seam_b']['significant']}")
        if t10:
            r = g["top10_fl"]["result"]
            print(f"  M2 top-10 sub-product: {len(t10)}/10 gated -> "
                  f"MAP {r['map']:+.2f} 68% [{r['ci68'][0]:.2f}, "
                  f"{r['ci68'][1]:.2f}]  (M2: -14.46 / [-14.92,-14.31])")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n-> {OUT}")

    # ---- figure: both gates, both configurations, vs published ----------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8.6, 5.0), dpi=150)
        style = {("relative", "fl"): ("#20567C", "-", 2.4),
                 ("relative", "table"): ("#7A3E9D", "-", 2.4),
                 ("absolute", "fl"): ("#20567C", "--", 1.4),
                 ("absolute", "table"): ("#7A3E9D", "--", 1.4)}
        for gname, g in res["gates"].items():
            for variant in ("fl", "table"):
                psrs = g[variant]["pulsars"]
                if not psrs:
                    continue
                tag = "f1" if variant == "fl" else "t1"
                logd = np.zeros_like(GRID)
                for p in psrs:
                    s = np.load(RES / f"{p}_{variant}_{tag}.curn.npy"
                                ).astype(float)
                    logd += np.log(np.clip(gaussian_kde(s)(GRID), 1e-300,
                                           None))
                d = np.exp(logd - logd.max())
                c, ls, lw = style[(gname, variant)]
                r = g[variant]["result"]
                lab = ("favoured + free red" if variant == "fl"
                       else "favoured model as tabulated")
                ax.plot(GRID, d / d.max(), color=c, ls=ls, lw=lw,
                        label=f"{lab} — {gname} gate, {g[variant]['n']} psr\n"
                              f"  MAP {r['map']:.2f}, 68% [{r['ci68'][0]:.2f}, "
                              f"{r['ci68'][1]:.2f}]")
        ax.axvline(PUB[0], color="#C4552D", lw=1.6,
                   label="published 83-psr FL: $-14.28\\pm0.21$")
        ax.axvspan(PUB[0] - PUB[1], PUB[0] + PUB[1], color="#C4552D",
                   alpha=0.12)
        ax.set_xlim(-16.0, -13.2)
        ax.set_xlabel("$\\log_{10} A_{\\rm CURN}$ ($\\gamma = 13/3$)")
        ax.set_ylabel("normalised density")
        ax.set_title("MPTA factorised-likelihood CURN: two model choices, "
                     "two stability gates")
        ax.legend(fontsize=7, loc="upper left")
        fig.tight_layout()
        FIG.mkdir(exist_ok=True)
        fig.savefig(FIG / "m4_fl_curn_both_gates.png")
        print("[saved] figures/m4_fl_curn_both_gates.png")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] figure skipped: {e}")


if __name__ == "__main__":
    main()
