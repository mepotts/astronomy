#!/usr/bin/env python3
"""M4: the table-audit figure -- the published log10 A_13/3 column, all 83
rows, sorted by 68% width, with the paper's own -16.5 "clearly disfavoured"
point marked.

This is the RNAAS note's ALTERNATIVE single graphic (the venue permits one
figure OR one table, not both); the note currently spends its allowance on
Table 1, and this figure lives in the repo.

    python scripts/m4_audit_figure.py
"""
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
FIG = REPO / "figures"
FLOOR = -16.5


def main():
    tab = json.loads((RES / "published_table.json").read_text())
    rows = []
    for psr, rec in tab.items():
        v = rec["pub"].get("gw13_log10_A")
        if not isinstance(v, list):
            continue
        m, lo, hi = v
        rows.append(dict(psr=psr, map=m, lo=m + lo, hi=m + hi,
                         width=hi - lo))
    rows.sort(key=lambda r: r["width"])
    lim = [r for r in rows if r["lo"] < FLOOR]
    print(f"{len(rows)} rows, {len(lim)} prior-bounded, "
          f"{sum(1 for r in rows if r['width'] < 0.7)} narrower than 0.7 dex")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.4, 8.6), dpi=150)
    y = np.arange(len(rows))
    for i, r in enumerate(rows):
        pb = r["lo"] < FLOOR
        ax.plot([r["lo"], r["hi"]], [i, i], lw=2.0,
                color=("#B8B3AD" if pb else "#20567C"),
                solid_capstyle="butt", zorder=2)
        ax.plot([r["map"]], [i], marker="|", ms=7, mew=1.4,
                color=("#8A857F" if pb else "#0D3550"), zorder=3)
    ax.axvline(FLOOR, color="#C4552D", lw=1.5, ls="--", zorder=1,
               label="$-16.5$: the paper's own 'clearly disfavoured' point")
    ax.axvline(-14.28, color="#2E7D5B", lw=1.2, zorder=1,
               label="published 83-psr FL CURN, $-14.28$")
    ax.set_yticks(y)
    ax.set_yticklabels([r["psr"] for r in rows], fontsize=5.0)
    ax.set_ylim(-1, len(rows))
    ax.set_xlim(-18.2, -11.5)
    ax.set_xlabel("published $\\log_{10}\\mathrm{A}_{13/3}$ "
                  "(MAP tick, 68% interval bar)")
    n_out = sum(1 for r in rows if not (r["lo"] <= r["map"] <= r["hi"]))
    ax.set_title("MPTA noise table, $\\log_{10}\\mathrm{A}_{13/3}$ column: "
                 f"{len(lim)} of {len(rows)} rows are prior-bounded\n"
                 "(grey = 68% interval reaches below $-16.5$; "
                 "blue = bounded on both sides)\n"
                 f"the {n_out} rows whose MAP tick sits off its own bar are "
                 "the claim-(c) cases", fontsize=9.5)
    ax.legend(fontsize=7.5, loc="lower left")
    ax.grid(axis="x", alpha=0.25, lw=0.5)
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "m4_table_audit_a13.png")
    print("[saved] figures/m4_table_audit_a13.png")


if __name__ == "__main__":
    main()
