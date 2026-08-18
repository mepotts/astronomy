#!/usr/bin/env python
"""M5-writeup: the single RNAAS figure, built from committed out/ artifacts only.

Input : out/m2_vanished_forensics.csv  (261 vanished bright eRASS1 sources,
        geometry + eROSITA-DR2 upper-limit-server metrics + v2 forensic class)
Output: out/m5w_vanished_census.png  (+ .pdf)

Panel (a): distribution of the upper-limit presence ratio P = UL_B / UL_S at the
           261 positions - the bimodality that separates catalogue dropouts
           (flux still there) from real faders (position blank).
Panel (b): P vs eRASS1 detection likelihood, showing that the artifact fraction
           rises with brightness, with the threshold band that bounds the census.

Usage: .venv/Scripts/python.exe scripts/m5w_figure.py
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

CUT = 1.5          # adopted presence threshold (M2 sec.3)
BAND = (1.3, 2.0)  # threshold band explored for the systematic

FADE = "FADE-CANDIDATE"
INDET = ("INDETERMINATE-HALO", "CONFUSED-IDENTITY")

van = pd.read_csv(os.path.join(OUT, "m2_vanished_forensics.csv"))
cls = van["forensic_class_v2"]
pres = van["ul_presence"].astype(float).to_numpy()
dl = van["DET_LIKE_0"].astype(float).to_numpy()

is_fade = (cls == FADE).to_numpy()
is_indet = cls.isin(INDET).to_numpy()
is_art = ~is_fade & ~is_indet

# the halo row has P = 0 (upper-limit server insensitive inside a bright halo);
# park it at the left edge of the log axis so the panel stays honest about n.
plot_p = np.where(pres <= 0, 0.62, pres)

C_FADE, C_ART, C_IND = "#1f5fa8", "#c2452d", "#8a8a8a"

fig, axes = plt.subplots(
    1, 2, figsize=(7.4, 3.05), gridspec_kw=dict(width_ratios=[1.0, 1.25], wspace=0.30)
)

# ---------------------------------------------------------------- panel (a)
ax = axes[0]
bins = np.logspace(np.log10(0.6), np.log10(120), 34)
ax.hist([plot_p[is_art], plot_p[is_indet], plot_p[is_fade]], bins=bins,
        stacked=True, color=[C_ART, C_IND, C_FADE],
        label=[f"catalogue artifact ({is_art.sum()})",
               f"indeterminate ({is_indet.sum()})",
               f"fade candidate ({is_fade.sum()})"],
        edgecolor="white", linewidth=0.35)
# the faint-end control: steady sources matched to the faders in eRASS1 flux and
# detection likelihood. They must land on the artifact side; they all do.
ctrl_path = os.path.join(OUT, "m5w_faint_validation.csv")
if os.path.exists(ctrl_path):
    cp = pd.read_csv(ctrl_path)["ul_presence"].astype(float)
    cp = cp[np.isfinite(cp) & (cp > 0.01)]
    ax.hist(cp, bins=bins, histtype="step", color="k", lw=1.15, zorder=6,
            label=f"steady flux-matched control ({len(cp)})")
    g1 = float(cp.min())
    ax.axvline(g1, color="k", ls=":", lw=1.0, zorder=5)
    ax.annotate(f"faintest steady\ncontrol, $P$ = {g1:.2f}", xy=(g1 * 1.15, 50),
                fontsize=6.4, ha="left", va="top", color="0.20")
ax.axvline(CUT, color="k", ls="--", lw=1.0, zorder=5)
ax.set_xscale("log")
ax.set_xlabel(r"upper-limit presence ratio  $P = B/S$")
ax.set_ylabel("sources")
ax.set_xlim(0.6, 120)
ax.annotate("adopted cut\n$P$ = 1.5", xy=(CUT * 0.94, 64), fontsize=6.4,
            va="top", ha="right", color="0.20")
ax.legend(fontsize=6.3, frameon=False, loc="upper right", handlelength=1.1,
          borderpad=0.2, labelspacing=0.25)
ax.set_title("(a) blank sky vs. flux still present", fontsize=8.5, loc="left")

# ---------------------------------------------------------------- panel (b)
ax = axes[1]
ax.axvspan(*BAND, color="0.55", alpha=0.16, zorder=0, lw=0)
ax.axvline(CUT, color="k", ls="--", lw=1.0, zorder=1)
ax.scatter(plot_p[is_art], dl[is_art], s=13, c=C_ART, marker="o",
           alpha=0.75, lw=0, zorder=3)
ax.scatter(plot_p[is_indet], dl[is_indet], s=16, c=C_IND, marker="s",
           alpha=0.85, lw=0, zorder=3)
ax.scatter(plot_p[is_fade], dl[is_fade], s=13, c=C_FADE, marker="^",
           alpha=0.80, lw=0, zorder=4)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"upper-limit presence ratio  $P = B/S$")
ax.set_ylabel(r"eRASS1 $\mathrm{DET\_LIKE\_0}$")
ax.set_xlim(0.6, 120)
ax.set_ylim(25, 2000)
dl_fade_max = float(dl[is_fade].max())
ax.axhline(dl_fade_max, color=C_FADE, ls=":", lw=0.9, zorder=2)
ax.text(0.72, dl_fade_max * 1.14, f"brightest fader, DET_LIKE = {dl_fade_max:.0f}",
        fontsize=6.3, color=C_FADE)
handles = [
    Line2D([], [], ls="", marker="^", color=C_FADE, ms=4.5,
           label=f"fade candidate ({is_fade.sum()})"),
    Line2D([], [], ls="", marker="o", color=C_ART, ms=4.5,
           label=f"catalogue artifact ({is_art.sum()})"),
    Line2D([], [], ls="", marker="s", color=C_IND, ms=4.5,
           label=f"indeterminate ({is_indet.sum()})"),
]
ax.legend(handles=handles, fontsize=6.6, frameon=False, loc="upper right",
          handlelength=1.0, borderpad=0.2, labelspacing=0.25)
ax.set_title("(b) the artifact fraction rises with eRASS1 brightness",
             fontsize=8.5, loc="left")

for ax in axes:
    ax.tick_params(labelsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.175)
for ext in ("png", "pdf"):
    p = os.path.join(OUT, f"m5w_vanished_census.{ext}")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    print("wrote", p)

# numbers quoted in the caption, printed so they can be pasted verbatim
n_band_lo = int(((~is_fade & ~is_indet) & (pres > CUT) & (pres <= BAND[1])).sum())
print(f"\ncaption numbers: n={len(van)}  faders={is_fade.sum()}  "
      f"artifacts={is_art.sum()}  indeterminate={is_indet.sum()}")
print(f"fader presence range {pres[is_fade].min():.2f}-{pres[is_fade].max():.2f} "
      f"(median {np.median(pres[is_fade]):.2f})")
print(f"artifact presence range {pres[is_art].min():.2f}-{pres[is_art].max():.2f}")
for thr in (100, dl_fade_max):
    sub = dl > thr
    print(f"  DET_LIKE > {thr:.0f}: n={int(sub.sum())} faders={int((sub & is_fade).sum())} "
          f"artifact+indet frac={100*(1-(sub & is_fade).sum()/max(sub.sum(),1)):.0f}%")
