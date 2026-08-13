"""Paper figures for the CD-35 2722 B reproduction + eta Tel B limit manuscript.

Four SVGs into data/export/. Committed light 'paper sheet' look (preprint-style):
surface #fcfcfb, ink #0b0b0b/#52514e, muted #898781, grid #e1e0d9, axis #c3c2b7.
Series colors are entity-stable across all figures: blue #2a78d6 = this work,
orange #eb6834 = Hoy et al. published values; models/reference lines in gray ink.
"""
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("SVG")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "data" / "export"

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE_FILL = "#cde2fb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 9,
    "figure.facecolor": SURF,
    "axes.facecolor": SURF,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2,
    "axes.titlecolor": INK,
    "axes.titlesize": 10,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "legend.frameon": False,
    "svg.fonttype": "none",
})


def despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def load_csv(name):
    return np.genfromtxt(EXP / name, delimiter=",", names=True)


# ---------- F1: CD-35 RV comparison ----------
d = load_csv("cd35_series.csv")
pub_all = np.genfromtxt(ROOT / "data" / "published" / "hoy2026_nature_table2_rvs.csv",
                        delimiter=",", names=True, skip_header=7)
m = np.isfinite(d["pub"])
off = np.mean(d["rv_mean"][m] - d["pub"][m])
ours = d["rv_mean"] - off   # the adopted (mean) combine — M14 §5
ours_err = d["spread"] / np.sqrt(11)
t0 = 2460000

fig, (a1, a2) = plt.subplots(
    2, 1, figsize=(7.2, 4.6), height_ratios=[3, 1.15], sharex=True,
    gridspec_kw={"hspace": 0.08})
a1.errorbar(pub_all["bjd"] - t0, pub_all["rv_ms"], yerr=pub_all["erv_ms"],
            fmt="o", ms=4.5, color=ORANGE, ecolor=ORANGE, elinewidth=1,
            capsize=0, label="Hoy et al. (published, 23 epochs)", zorder=2)
a1.errorbar(d["bjd"][m] - t0, ours[m], yerr=ours_err[m],
            fmt="o", ms=4.5, color=BLUE, ecolor=BLUE, elinewidth=1, capsize=0,
            mfc=SURF, mew=1.6, label="This work (from raw frames, 17 nights)",
            zorder=3)
a1.set_ylabel("RV  (m s$^{-1}$)")
a1.set_title("CD-35 2722 B: independent extraction against the published series")
a1.legend(loc="upper right", fontsize=8)
a1.annotate("embargoed-epoch\nregion (2026)", xy=(1055, -320), fontsize=7.5,
            color=MUTED, ha="center")
despine(a1)

res = ours[m] - d["pub"][m]
a2.axhspan(-np.std(res), np.std(res), color=BLUE_FILL, alpha=0.45, lw=0)
a2.axhline(0, color=AXIS, lw=0.8)
a2.plot(d["bjd"][m] - t0, res, "o", ms=4, color=BLUE)
a2.set_ylabel("Δ (m s$^{-1}$)")
a2.set_xlabel(f"BJD − {t0}")
a2.annotate(f"rms {np.std(res):.0f} m s$^{{-1}}$", xy=(0.012, 0.82),
            xycoords="axes fraction", fontsize=7.5, color=INK2)
despine(a2)
fig.savefig(EXP / "fig1_cd35_series.svg", bbox_inches="tight")
plt.close(fig)
print("fig1 done")

# ---------- F2: phase fold ----------
P, K_pub = 171.454, 306.0
ph_pub = ((pub_all["bjd"] - pub_all["bjd"][0]) / P) % 1
ph_ours = ((d["bjd"][m] - pub_all["bjd"][0]) / P) % 1
# fit phase+offset of the published circular orbit for the model curve
A = np.column_stack([np.cos(2 * np.pi * ph_pub), np.sin(2 * np.pi * ph_pub),
                     np.ones_like(ph_pub)])
b, *_ = np.linalg.lstsq(A, pub_all["rv_ms"], rcond=None)
phi = np.arctan2(b[1], b[0])
grid = np.linspace(0, 1, 300)
model = K_pub * np.cos(2 * np.pi * grid - phi) + b[2]

fig, ax = plt.subplots(figsize=(7.2, 3.5))
ax.plot(grid, model, "-", lw=1.6, color=INK2, alpha=0.8,
        label=f"published orbit (K = {K_pub:.0f} m s$^{{-1}}$, circular)")
ax.errorbar(ph_pub, pub_all["rv_ms"], yerr=pub_all["erv_ms"], fmt="o", ms=4.5,
            color=ORANGE, elinewidth=1, capsize=0, label="Hoy et al.", zorder=2)
ax.errorbar(ph_ours, ours[m], yerr=ours_err[m], fmt="o", ms=4.5, color=BLUE,
            elinewidth=1, capsize=0, mfc=SURF, mew=1.6, label="this work",
            zorder=3)
ax.set_xlabel(f"orbital phase  (P = {P} d)")
ax.set_ylabel("RV  (m s$^{-1}$)")
ax.set_title("Phase-folded at the published period")
ax.legend(loc="lower left", fontsize=8)
despine(ax)
fig.savefig(EXP / "fig2_phasefold.svg", bbox_inches="tight")
plt.close(fig)
print("fig2 done")

# ---------- F3: ΔBIC landscapes ----------
cd = load_csv("cd35_landscape.csv")
et = load_csv("etatel_landscape.csv")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.3), sharey=True,
                             gridspec_kw={"wspace": 0.06})
for ax, dd, title, ann in (
        (a1, cd, "CD-35 2722 B (17 nights)", "detection"),
        (a2, et, "eta Tel B (17 nights)", "null")):
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.axhline(10, color=MUTED, lw=0.8, ls=(0, (4, 3)))
    ax.plot(dd["P_d"], dd["dbic"], lw=1.4, color=BLUE, label="blind search")
    ax.plot(dd["P_d"], dd["dbic_berv"], lw=1.4, color=ORANGE,
            label="+ BERV covariate")
    ax.axvline(171.45, color=MUTED, lw=0.8, ls=":")
    ax.set_xscale("log")
    ax.set_xlabel("trial period  (d)")
    ax.set_title(title, fontsize=9.5)
    despine(ax)
a1.set_ylabel("ΔBIC vs constant")
a1.annotate("published period", xy=(171.45, -12), fontsize=7, color=MUTED,
            ha="center", rotation=90, va="bottom")
a1.annotate(f"peak +{cd['dbic'].max():.0f}\n(+{cd['dbic_berv'].max():.0f} w/ BERV)",
            xy=(171.45, cd["dbic"].max()), xytext=(445, 33), fontsize=7.5,
            ha="right", color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
a2.annotate("ΔBIC = 10", xy=(6.2, 11), fontsize=7, color=MUTED)
a1.legend(loc="upper left", fontsize=8)
fig.suptitle("Blind period search, internally screened series", fontsize=10,
             color=INK, y=1.02)
fig.savefig(EXP / "fig3_landscapes.svg", bbox_inches="tight")
plt.close(fig)
print("fig3 done")

# ---------- F4: eta Tel sensitivity ----------
import json

lim = json.loads((ROOT / "data" / "m15-limit.json").read_text())
Ps = np.array(lim["periods"], float)
G, MSUN, MJUP = 6.674e-11, 1.989e30, 1.898e27


def msini(K, P_d, M_mjup=47.0):
    return (K * (M_mjup * MJUP) ** (2 / 3)
            * (P_d * 86400 / (2 * np.pi * G)) ** (1 / 3)) / MJUP


K90 = []
for P_ in Ps:
    fr = lim["detfrac"][str(P_) if str(P_) in lim["detfrac"] else f"{P_:.1f}"]
    ks = sorted((float(k), v) for k, v in fr.items())
    K90.append(next((k for k, v in ks if v >= 0.9), np.nan))
K90 = np.array(K90)
m90 = msini(K90, Ps)

fig, ax = plt.subplots(figsize=(7.2, 3.5))
ax.fill_between(Ps, m90, 4.0, color=BLUE_FILL, alpha=0.55, lw=0)
ax.plot(Ps, m90, "-o", lw=1.6, ms=5, color=BLUE, label="90% exclusion (this work)")
ax.plot([171.45], [0.918], "D", ms=7, color=ORANGE, mec=SURF, mew=1.2,
        label="CD-35 2722 B satellite (for scale)")
ax.annotate("excluded", xy=(45, 2.4), fontsize=9, color="#1c5cab")
ax.annotate("M7 survey forecast (3.3 M$_{Jup}$)", xy=(21, 3.35), fontsize=7.5,
            color=MUTED)
ax.axhline(3.3, color=MUTED, lw=0.8, ls=(0, (4, 3)))
ax.set_xscale("log")
ax.set_xlim(18, 330)
ax.set_ylim(0, 4.0)
ax.set_xticks([20, 30, 60, 100, 200, 300])
ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.minorticks_off()
ax.set_xlabel("orbital period  (d)")
ax.set_ylabel(r"companion $m\,\sin i$  (M$_{Jup}$)")
ax.set_title("eta Tel B: first radial-velocity companion limit")
ax.legend(loc="lower right", fontsize=8)
despine(ax)
fig.savefig(EXP / "fig4_limit.svg", bbox_inches="tight")
plt.close(fig)
print("fig4 done")
