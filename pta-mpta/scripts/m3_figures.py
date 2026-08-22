#!/usr/bin/env python3
"""M3 figures: the array-wide agreement panel and the seam-(a) ridge panel."""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
FIG = REPO / "figures"
BLUE, RED, PUR, GREY = "#20567C", "#C4552D", "#7A3E9D", "#8FB4CE"


def fig_agreement():
    rows = json.loads((RES / "campaign_table.json").read_text())
    g = [r for r in rows if r.get("gate")]
    if not g:
        return
    audit = json.loads((RES / "table_audit.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), dpi=150)

    ax = axes[0]
    frac = [r["n_agree"] / r["n_compared"] for r in g if r["n_compared"]]
    ax.hist(frac, bins=np.linspace(0, 1.0001, 21), color=BLUE)
    ax.set_xlabel("fraction of a pulsar's tabulated parameters that agree")
    ax.set_ylabel("pulsars")
    na = sum(r["n_agree"] for r in g)
    nc = sum(r["n_compared"] for r in g)
    ax.set_title(f"{sum(1 for f in frac if f == 1)}/{len(g)} pulsars agree in "
                 f"full\n{na}/{nc} parameters ({100*na/nc:.1f}%)")

    ax = axes[1]
    dl = [r["dlnl"] for r in g if r["dlnl"] is not None]
    if dl:
        lo, hi = min(dl), max(dl)
        bins = np.linspace(min(lo, -5), max(hi, 5), 40)
        full = [r["dlnl"] for r in g
                if r["dlnl"] is not None and r["full"]]
        part = [r["dlnl"] for r in g
                if r["dlnl"] is not None and not r["full"]]
        ax.hist(full, bins=bins, color=BLUE, label="agrees in full")
        ax.hist(part, bins=bins, color=RED, label="has >=1 miss")
        ax.axvline(0, color="0.3", lw=1)
        ax.set_yscale("log")
        ax.set_xlabel("$\\Delta \\ln L$ = our best point $-$ published MAP\n"
                      "(our own likelihood; $<0$ = sampling shortfall)")
        ax.set_ylabel("pulsars")
        ax.legend(fontsize=8)
        ax.set_title("the mode-vs-model diagnostic, run on every pulsar")
    fig.tight_layout()
    fig.savefig(FIG / "m3_agreement.png")
    print("[saved] figures/m3_agreement.png")


def fig_seam_a():
    rows = json.loads((RES / "seam_a.json").read_text())
    free = [r for r in rows if r["chrom"] == "free" and "r_Abeta" in r]
    if not free:
        return
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)

    ax = axes[0]
    ax.hist([r["r_Abeta"] for r in free], bins=np.linspace(-1, 0, 21),
            color=BLUE)
    ax.set_xlabel("Pearson $r(\\log_{10}A_{\\rm Chrom},\\ \\beta)$")
    ax.set_ylabel("pulsars")
    ax.set_title(f"S1: the ridge is universal ({len(free)} free-$\\beta$ psr)")

    ax = axes[1]
    ax.hist([100 * r["beta_frac68"] for r in free],
            bins=np.linspace(0, 60, 25), color=BLUE, label="68% CI")
    ax.hist([100 * r["beta_frac95"] for r in free],
            bins=np.linspace(0, 60, 25), color=GREY, alpha=0.6,
            label="95% CI")
    ax.set_xlabel("$\\beta$ credible-interval width as % of the U(0,14) prior")
    ax.set_ylabel("pulsars")
    ax.legend(fontsize=8)
    ax.set_title("S2: is $\\beta$ measured or prior-shaped?")

    ax = axes[2]
    x = [r["max_dA"] or 0 for r in free]
    y = [r["pub_A_half68"] or 0 for r in free]
    ax.scatter(y, x, s=26, color=BLUE, zorder=3)
    m = max(max(x), max(y)) * 1.1 + 0.01
    ax.plot([0, m], [0, m], color=RED, lw=1.2, ls="--",
            label="prior-driven above this line")
    ax.set_xlim(0, m)
    ax.set_ylim(0, m)
    ax.set_xlabel("published 68% half-width of $\\log_{10}A_{\\rm Chrom}$ (dex)")
    ax.set_ylabel("largest median shift under a\nnarrower $\\beta$ prior (dex)")
    ax.legend(fontsize=8)
    ax.set_title("S4: prior-driven or data-driven?")
    fig.tight_layout()
    fig.savefig(FIG / "m3_seam_a.png")
    print("[saved] figures/m3_seam_a.png")


def fig_table_audit():
    """The published A_13/3 column, sorted, against the paper's own
    'clearly disfavoured' point. No sampling involved - this is a picture of
    the table itself."""
    tab = json.loads((RES / "published_table.json").read_text())
    rows = []
    for psr, rec in tab.items():
        v = rec["pub"].get("gw13_log10_A")
        if isinstance(v, list):
            rows.append((psr, v[0], v[0] + v[1], v[0] + v[2]))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(7.2, 9.0), dpi=150)
    y = np.arange(len(rows))
    lim = [r for r in rows if r[2] < -16.5]
    for i, (psr, m, lo, hi) in enumerate(rows):
        c = RED if lo < -16.5 else BLUE
        ax.plot([max(lo, -18), hi], [i, i], color=c, lw=2.0,
                solid_capstyle="butt", alpha=0.85)
        ax.plot([m], [i], "o", color=c, ms=3.2)
    ax.axvline(-16.5, color="0.25", lw=1.4, ls="--")
    ax.text(-16.45, len(rows) * 0.02,
            "the paper's own\n'clearly disfavoured' point",
            fontsize=8, color="0.25")
    ax.axvline(-18, color="0.6", lw=1.0)
    ax.text(-17.95, len(rows) * 0.86, "our prior floor", fontsize=8,
            color="0.5", rotation=90, va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=5.5)
    ax.set_ylim(-1, len(rows))
    ax.set_xlim(-18.3, -12.2)
    ax.set_xlabel("published $\\log_{10} A_{13/3}$ with its 68% interval")
    ax.set_title(f"{len(lim)} of {len(rows)} tabulated per-pulsar CURN "
                 f"amplitudes\nare bounded by the prior, not the data")
    fig.tight_layout()
    fig.savefig(FIG / "m3_a13_column.png")
    print("[saved] figures/m3_a13_column.png")


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    for f in (fig_table_audit, fig_agreement, fig_seam_a):
        try:
            f()
        except Exception as e:
            print(f"[warn] {f.__name__}: {e}")
