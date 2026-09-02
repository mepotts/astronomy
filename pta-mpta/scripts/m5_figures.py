#!/usr/bin/env python3
"""M5 figures.

  figures/m5_sw_census.png   the prior-propping census (S3): every SW_Full
      pulsar's gamma_SW 68% width under U(0,7) and under U(-4,4), with the
      25%-of-prior occupancy marks, plus the coupled log10A_SW widths.
  figures/m5_seamb_null.png  the declared post-hoc subset/jackknife diagnostic
      on the seam-(b) product-level shift.

    python scripts/m5_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIG = REPO / "figures"
M5 = REPO / "results" / "m5"

COL = {"MEASURED": "#20567C", "PRIOR-PROPPED": "#C4552D",
       "UNCONSTRAINED-BOTH": "#8A8F98", "OTHER": "#7A3E9D"}


def sw_census():
    d = json.loads((M5 / "sw_census.json").read_text())
    rows = sorted(d["rows"], key=lambda r: r["w_narrow"])
    y = np.arange(len(rows))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 7.2), dpi=150,
                                 sharey=True,
                                 gridspec_kw=dict(width_ratios=[1.35, 1]))
    for i, r in enumerate(rows):
        c = COL[r["klass"]]
        a1.plot([r["w_narrow"], r["w_wide"]], [i, i], color=c, lw=1.4,
                alpha=0.85, zorder=1)
        a1.scatter(r["w_narrow"], i, s=34, facecolor="white", edgecolor=c,
                   lw=1.5, zorder=3)
        a1.scatter(r["w_wide"], i, s=34, color=c, zorder=3)
        a2.plot([r["wA_narrow"], r["wA_wide"]], [i, i], color=c, lw=1.4,
                alpha=0.85)
        a2.scatter(r["wA_narrow"], i, s=30, facecolor="white", edgecolor=c,
                   lw=1.5, zorder=3)
        a2.scatter(r["wA_wide"], i, s=30, color=c, zorder=3)
    a1.axvline(0.25 * 7, color="#20567C", ls=":", lw=1.2)
    a1.axvline(0.25 * 8, color="#C4552D", ls=":", lw=1.2)
    a1.text(0.25 * 7, len(rows) - 0.2, " 25% of U(0,7)", fontsize=7,
            color="#20567C", ha="left", va="top")
    a1.text(0.25 * 8, len(rows) - 2.0, " 25% of U(-4,4)", fontsize=7,
            color="#C4552D", ha="left", va="top")
    a1.set_yticks(y)
    a1.set_yticklabels([r["psr"] for r in rows], fontsize=7.5)
    a1.set_xlabel(r"68% width of $\gamma_{\rm SW}$")
    a2.set_xlabel(r"68% width of $\log_{10}A_{\rm SW}$ (dex)")
    a1.set_xlim(0, 5.6)
    handles = [plt.Line2D([], [], color=c, marker="o", ls="-", lw=1.4,
                          label=f"{k.lower().replace('-', ' ')} "
                                f"({sum(1 for r in rows if r['klass']==k)})")
               for k, c in COL.items()
               if any(r["klass"] == k for r in rows)]
    handles += [plt.Line2D([], [], color="k", marker="o", ls="",
                           markerfacecolor="white", label=r"under U(0,7)"),
                plt.Line2D([], [], color="k", marker="o", ls="",
                           label=r"under U($-4$,4)")]
    a1.legend(handles=handles, fontsize=7.2, loc="lower right", framealpha=0.95)
    fig.suptitle("Solar-wind prior-propping census: what widens when the "
                 r"$\gamma_{\rm SW}$ prior is widened", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "m5_sw_census.png")
    print("[saved] figures/m5_sw_census.png")


def seamb_null():
    d = json.loads((M5 / "seamb_subset_null.json").read_text())
    fig, ax = plt.subplots(figsize=(7.4, 4.0), dpi=150)
    jk = d["jackknife"]
    lo, hi = d["null"]["ci95"]
    ax.axvspan(lo, hi, color="#8FB4CE", alpha=0.35,
               label=f"random {d['n_floored']}-of-{d['n_common']} subsets, "
                     f"95% band")
    ax.axvline(d["dmap_all"], color="#20567C", lw=2.0,
               label=f"all {d['n_common']} common: "
                     f"{d['dmap_all']:+.3f} dex")
    ax.errorbar([d["dmap_all"]], [0.55], xerr=[[jk["se"]], [jk["se"]]],
                fmt="o", color="#20567C", capsize=4,
                label=f"delete-1 jackknife SE {jk['se']:.3f} dex")
    ax.axvline(d["dmap_ess"], color="#C4552D", lw=2.0, ls="--",
               label=f"ESS-floored {d['n_floored']}: "
                     f"{d['dmap_ess']:+.3f} dex")
    ax.axvline(0.21, color="#444", ls=":", lw=1.3,
               label="registered F4 threshold 0.21 dex")
    ax.axvline(-0.21, color="#444", ls=":", lw=1.3)
    ax.axvline(0.0, color="k", lw=0.8)
    ax.set_xlabel(r"$\Delta$MAP $= \log_{10}A^{\rm table}_{\rm CURN} - "
                  r"\log_{10}A^{\rm fl}_{\rm CURN}$  (dex)")
    ax.set_yticks([])
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7.6, loc="upper left", framealpha=0.95)
    ax.set_title("Seam (b) at the product level is not resolved by this data "
                 "set (declared post-hoc diagnostic)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "m5_seamb_null.png")
    print("[saved] figures/m5_seamb_null.png")


if __name__ == "__main__":
    sw_census()
    seamb_null()
