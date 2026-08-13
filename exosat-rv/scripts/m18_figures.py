"""M18: the H26 figure-match set — one figure of ours for each figure of theirs.

`m16_figures.py` makes the four figures the draft needs to tell its own story. This module
makes the eight that answer a different question: *what does H26's figure N look like when
we make it?* Numbering continues from m16 (Figs. 5-12) and every caption records the H26
figure it answers.

  Fig.  5  <-> H26 Fig. 1  periodogram of the RVs, and of the model residuals
  Fig.  6  <-> H26 Fig. 2  RVs with the one- and two-satellite models drawn over them
  Fig.  7  <-> H26 Fig. 4  per-nodding versus combined-spectrum extraction
  Fig.  8  <-> H26 Fig. 5  period posterior for the second signal, wide then windowed
  Fig.  9  <-> H26 Fig. 6  the high-evidence two-satellite models
  Fig. 10  <-> H26 Fig. 7  GLS of every viper output -- plus the BERV panel they omit
  Fig. 11  <-> H26 Fig. 8  corner plot, large satellite
  Fig. 12  <-> H26 Fig. 9  corner plot, small satellite

H26 Fig. 3 (slit-viewer PSF fits and the stellar-contamination contrast curve) has no
counterpart here: it needs the SV imaging, which this project has never reduced.

Colours are entity-stable with m16: blue #2a78d6 = this work, orange #eb6834 = H26.

Usage: python scripts/m18_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from astropy.timeseries import LombScargle

import matplotlib

matplotlib.use("SVG")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
EXP = ROOT / "data" / "export"

from m18_posteriors import msini_jup  # noqa: E402
from exosat_rv.analysis.aliases import keplerian_rv  # noqa: E402

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE_FILL, ORANGE_FILL = "#cde2fb", "#fbdccd"
RED = "#b0473a"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 9,
    "figure.facecolor": SURF,
    "axes.facecolor": SURF,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2,
    "axes.titlecolor": INK,
    "axes.titlesize": 9.5,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "legend.frameon": False,
    # Glyphs as paths, not <text>: these figures are embedded in an HTML page
    # whose reader may not have DejaVu Sans, and matplotlib writes per-run x
    # positions from its own metrics -- a substituted face makes mathtext-bearing
    # titles come out unevenly letter-spaced. Costs ~10% file size, buys fidelity.
    "svg.fonttype": "path",
})

P_PUB = 171.454          # H26 Table 1, two-satellite fit
P2_PUB = 87.349
K_PUB, K2_PUB = 306.0, 104.0


def despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def tag(ax, text, xy=(0.015, 0.9), colour=None, size=7.8, ha="left", weight=None):
    """Annotation on an opaque patch, so labels never fight the data underneath."""
    return ax.annotate(text, xy=xy, xycoords="axes fraction", fontsize=size, ha=ha,
                       va="center", color=colour or INK, weight=weight or "normal",
                       bbox=dict(fc=SURF, ec="none", alpha=0.82, pad=1.6))


def _dec(v, n=2):
    """Decimal places that show v to n significant figures."""
    if v == 0 or not np.isfinite(v):
        return 1
    return max(0, n - 1 - int(np.floor(np.log10(abs(v)))))


def quantile_label(q, unit=""):
    """'171.6 +1.0 -1.2 d' — median quoted to the precision its errors justify."""
    lo, mid, hi = q
    d = max(_dec(hi - mid), _dec(mid - lo))
    return (f"{mid:.{d}f}$^{{+{hi - mid:.{d}f}}}_{{-{mid - lo:.{d}f}}}$"
            f"{' ' + unit if unit else ''}")


def save(fig, name):
    fig.savefig(EXP / name, bbox_inches="tight")
    fig.savefig(EXP / name.replace(".svg", ".png"), bbox_inches="tight", dpi=160)
    plt.close(fig)
    print(f"  wrote {name}")


# ----------------------------------------------------------------- data loading
def load_all():
    pub = np.genfromtxt(ROOT / "data" / "published" / "hoy2026_nature_table2_rvs.csv",
                        delimiter=",", names=True, skip_header=7)
    ser = np.genfromtxt(EXP / "cd35_series.csv", delimiter=",", names=True)
    rvo = np.genfromtxt(ROOT / "data" / "viper" / "it2.rvo.dat", names=True,
                        dtype=None, encoding="utf-8")
    par = np.genfromtxt(ROOT / "data" / "viper" / "it2.par.dat", names=True)
    post = np.load(ROOT / "data" / "m18-posteriors.npz", allow_pickle=True)
    meta = json.loads((ROOT / "data" / "m18-posteriors.json").read_text(encoding="utf-8"))

    # BERV per night, matched from the archive-route file onto our night list.
    berv = np.array([rvo["BERV"][np.argmin(abs(rvo["BJD"] - b))] for b in ser["bjd"]])

    matched = np.isfinite(ser["pub"])
    off = np.mean(ser["rv_mean"][matched] - ser["pub"][matched])
    ours = ser["rv_mean"] - off
    ours_err = ser["spread"] / np.sqrt(11)

    # The internal quality screen of M14: drop the night whose across-order scatter is
    # far above the median (independently, the one archival night H26 also omit).
    keep = ser["spread"] < 3 * np.median(ser["spread"])
    return dict(pub=pub, ser=ser, rvo=rvo, par=par, post=post, meta=meta, berv=berv,
                matched=matched, ours=ours, ours_err=ours_err, keep=keep, offset=off)


FREQS = 1.0 / np.exp(np.linspace(np.log(5.0), np.log(460.0), 4000))
PGRID = 1.0 / FREQS


def gls(t, y, dy=None):
    g = np.isfinite(y)
    ls = LombScargle(t[g], y[g]) if dy is None else LombScargle(t[g], y[g], dy[g])
    return ls, ls.power(FREQS)


def fap_levels(ls, levels=(0.1, 0.01, 0.001)):
    try:
        return {lv: float(ls.false_alarm_level(lv)) for lv in levels}
    except Exception:                                    # pragma: no cover - tiny n
        return {}


def remove_circular(t, y, periods):
    """Least-squares removal of an offset plus one circular signal per period."""
    cols = [np.ones_like(t)]
    for P in periods:
        cols += [np.cos(2 * np.pi * t / P), np.sin(2 * np.pi * t / P)]
    A = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ b


def pgram_panel(ax, t, y, colour, dy=None, label=None):
    ls, pw = gls(t, y, dy)
    ax.plot(PGRID, pw, lw=1.0, color=colour)
    ax.set_xscale("log")
    ax.axvline(P_PUB, color=INK2, lw=0.9, ls=":", zorder=0)
    # 10 / 1 / 0.1 % false-alarm levels, bottom to top. Left unlabelled on the plot --
    # three short dashed rules read better than three boxes of text fighting the peaks;
    # the caption says which is which.
    for val in fap_levels(ls).values():
        ax.axhline(val, color=MUTED, lw=0.6, ls="--", zorder=0)
    i = int(np.argmax(pw))
    ax.plot([PGRID[i]], [pw[i]], "v", ms=5, color=colour, clip_on=False)
    ax.set_xlim(5, 460)
    if label:
        tag(ax, label, xy=(0.015, 0.92))
    despine(ax)
    return ls, pw, PGRID[i], pw[i]


# --------------------------------------------- Fig. 5  <->  H26 Fig. 1 periodograms
def fig5(D):
    pub, ser, keep = D["pub"], D["ser"], D["keep"]
    ours, oerr = D["ours"], D["ours_err"]
    tp, yp, ep = pub["bjd"], pub["rv_ms"], pub["erv_ms"]
    to, yo, eo = ser["bjd"][keep], ours[keep], oerr[keep]

    fig, axs = plt.subplots(3, 2, figsize=(7.4, 5.6), sharex=True,
                            gridspec_kw={"hspace": 0.18, "wspace": 0.1})
    rows = [
        ("RVs", []),
        ("residuals, 1-satellite fit", [P_PUB]),
        ("residuals, 2-satellite fit", [P_PUB, P2_PUB]),
    ]
    tops = {}
    for r, (name, rem) in enumerate(rows):
        yy_p = remove_circular(tp, yp, rem) if rem else yp
        yy_o = remove_circular(to, yo, rem) if rem else yo
        _, pw_p, Pp, pwp = pgram_panel(axs[r, 0], tp, yy_p, ORANGE, ep, name)
        _, pw_o, Po, pwo = pgram_panel(axs[r, 1], to, yy_o, BLUE, eo, name)
        tops[name] = (Pp, pwp, Po, pwo)
        hi = 1.22 * max(pw_p.max(), pw_o.max())        # shared scale within the row
        for c, (P, pwv, col) in enumerate([(Pp, pwp, ORANGE), (Po, pwo, BLUE)]):
            axs[r, c].set_ylim(0, hi)
            axs[r, c].annotate(f"{P:.1f} d", xy=(P, pwv), xytext=(7, 1),
                               textcoords="offset points", fontsize=7.5, color=col)
        axs[r, 0].set_ylabel("GLS power")
        axs[r, 1].tick_params(labelleft=False)
    axs[0, 0].set_title("H26's published RV table (23 epochs)", color=ORANGE)
    axs[0, 1].set_title("this work, from raw frames (17 nights)", color=BLUE)
    for c in (0, 1):
        axs[2, c].set_xlabel("period (d)")
    save(fig, "fig5_periodograms.svg")
    return tops


# ------------------------------------------ Fig. 6  <->  H26 Fig. 2 RVs with models
def fig6(D):
    pub, ser, keep, post = D["pub"], D["ser"], D["keep"], D["post"]
    ours, oerr = D["ours"], D["ours_err"]
    t0 = float(pub["bjd"].min())
    grid = np.linspace(0, pub["bjd"].max() - t0, 1400)

    s1 = post["sat1_ecc__samples"]
    l1 = list(post["sat1_ecc__labels"])
    med1 = np.median(s1, axis=0)
    g = dict(zip(l1, med1))
    m1 = g["offset"] + keplerian_rv(grid, g["P1"], g["K1"], g["e1"], g["om1"],
                                    g["tpf1"] * g["P1"])

    s2 = post["win88__samples"]
    l2 = list(post["win88__labels"])
    g2 = dict(zip(l2, np.median(s2, axis=0)))
    m2 = (g2["offset"]
          + keplerian_rv(grid, g2["P1"], g2["K1"], 0.0, g2["om1"], 0.0)
          + keplerian_rv(grid, g2["P2"], g2["K2"], 0.0, g2["om2"], 0.0))

    fig, axs = plt.subplots(2, 1, figsize=(7.4, 5.2), sharex=True, sharey=True,
                            gridspec_kw={"hspace": 0.1})
    for ax, model, ttl in (
            (axs[0], m1, f"one satellite  ·  P = {g['P1']:.2f} d, "
                         f"K = {g['K1']:.0f} m s$^{{-1}}$, e = {g['e1']:.2f}"),
            (axs[1], m2, f"two satellites  ·  P$_1$ = {g2['P1']:.2f} d, "
                         f"P$_2$ = {g2['P2']:.2f} d")):
        ax.plot(grid, model, "-", lw=1.4, color=INK2, alpha=0.85, zorder=1,
                label="this work, posterior median model")
        ax.errorbar(pub["bjd"] - t0, pub["rv_ms"], yerr=pub["erv_ms"], fmt="o", ms=4.2,
                    color=ORANGE, elinewidth=1, capsize=0, zorder=2,
                    label="H26 published RVs")
        ax.errorbar(ser["bjd"][keep] - t0, ours[keep], yerr=oerr[keep], fmt="o", ms=4.2,
                    color=BLUE, elinewidth=1, capsize=0, mfc=SURF, mew=1.5, zorder=3,
                    label="this work, from raw")
        ax.set_ylabel("RV  (m s$^{-1}$)")
        tag(ax, ttl, xy=(0.013, 0.93), size=8.5)
        despine(ax)
    axs[0].legend(loc="upper center", fontsize=7.5, ncol=3,
                  bbox_to_anchor=(0.5, 1.30))
    axs[1].set_xlabel(f"BJD − {t0:.0f}")
    save(fig, "fig6_models.svg")


# ------------------------------------- Fig. 7  <->  H26 Fig. 4 nodding vs combined
# H26's Fig. 4 asks one question: how much does extracting each nodding position
# separately buy you over combining the spectra first? Their answer is a percentage.
#
# Ours cannot be drawn as their time series from committed data -- the per-order RVs of
# the *tuned* archive route live in the viper working tree, and the snapshot committed in
# data/viper/ is an untuned earlier run (per-order scatter 300-5000 m/s), so plotting it
# against the per-nodding series would charge a recipe difference to the nodding choice.
# What the project actually measured is below, from M14 SS3 (paired, 5 nights, identical
# config) and M14 SS8 (all 17 matched nights, full paper recipe).
NODDING = {
    "h26_nature": ("H26, Nature", 60.50, 57.68, "mean internal RV error (m s⁻¹)"),
    "h26_v1": ("H26, arXiv v1", 34.49, 31.44, "mean internal RV error (m s⁻¹)"),
    # (label, combined-first, per-nodding) as rms against the published series
    "ours_paired": ("this work — paired, 5 nights\n(M14 §3, identical config)",
                    179.0, 142.0, "rms vs published (m s⁻¹)"),
    "ours_mean": ("this work — 17 nights, mean combine\n(M14 §8)",
                  85.0, 90.0, "rms vs published (m s⁻¹)"),
    "ours_robust": ("this work — 17 nights, robust combine\n(M14 §8, centered clip)",
                    85.0, 70.0, "rms vs published (m s⁻¹)"),
}


def fig7(D):
    """One panel, because the gain is the only quantity the two papers share.

    H26 measure the mean internal RV error; we measure rms against their published
    series. The absolutes are not comparable, the percentage improvement is, so the
    percentage is the axis and the absolutes are printed on each bar.
    """
    groups = [("h26_nature", ORANGE), ("h26_v1", ORANGE),
              ("ours_paired", BLUE), ("ours_mean", BLUE), ("ours_robust", BLUE)]
    rows = []
    for key, col in groups:
        lab, comb, nod, unit = NODDING[key]
        rows.append((lab, 100 * (comb - nod) / comb, comb, nod, unit, col))

    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[1] for r in rows], height=0.5,
            color=[ORANGE_FILL if r[5] == ORANGE else BLUE_FILL for r in rows],
            edgecolor=[r[5] for r in rows], lw=1.0)
    ax.axvline(0, color=INK2, lw=0.9)
    for yy, (lab, g, comb, nod, unit, col) in zip(y, rows):
        ax.annotate(f"{g:+.0f}%", xy=(g, yy), xytext=(7 if g >= 0 else -7, 0),
                    textcoords="offset points", fontsize=8.5, va="center",
                    ha="left" if g >= 0 else "right",
                    color=RED if g < 0 else col, weight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r[0]}\n{r[2]:.0f} → {r[3]:.0f}  {r[4]}" for r in rows],
                       fontsize=7.2)
    ax.set_xlim(-13, 34)
    ax.set_xlabel("improvement from extracting the two nodding positions separately "
                  "rather than combining the spectra first  (%)", fontsize=8)
    ax.set_title("The measurement H26's Fig. 4 makes, made again", fontsize=9.5)
    ax.grid(axis="y", visible=False)
    despine(ax)
    save(fig, "fig7_nodding.svg")
    return {k: 100 * (v[1] - v[2]) / v[1] for k, v in NODDING.items()}


# --------------------------------- Fig. 8  <->  H26 Fig. 5 second-signal posteriors
def fig8(D):
    post, meta = D["post"], D["meta"]
    peaks = meta["fig5_peaks"]

    fig = plt.figure(figsize=(7.4, 4.7))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.35, 1], hspace=0.72, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    s = post["two_wideP2__samples"]
    lab = list(post["two_wideP2__labels"])
    P2 = s[:, lab.index("P2")]
    ax.hist(P2, bins=np.exp(np.linspace(np.log(5), np.log(150), 90)),
            color=BLUE_FILL, edgecolor=BLUE, lw=0.7)
    ax.set_xscale("log")
    for pk in peaks:
        ax.axvline(pk, color=ORANGE, lw=1.0, ls="--", zorder=0)
        ax.annotate(f"{pk:g} d", xy=(pk, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(3, -8), textcoords="offset points", fontsize=7,
                    color=ORANGE, va="top")
    ax.set_xlabel("period of the second signal (d)")
    ax.set_ylabel("posterior samples")
    ax.set_title("Second-signal period posterior, wide prior P$_2$ ~ U(5, 150) d "
                 "— dashed: the four peaks H26 report")
    despine(ax)

    for i, pk in enumerate(peaks):
        a = fig.add_subplot(gs[1, i])
        key = f"win{pk:g}"
        ss = post[f"{key}__samples"]
        ll = list(post[f"{key}__labels"])
        v = ss[:, ll.index("P2")]
        a.hist(v, bins=32, color=BLUE_FILL, edgecolor=BLUE, lw=0.6)
        a.axvline(pk, color=ORANGE, lw=1.0, ls="--")
        d = meta["runs"][key]["dlogz_vs_1sat"]
        a.set_title(f"window {i + 1}: {pk:g} d", fontsize=8.5)
        tag(a, f"ΔlnZ = {d:+.1f}", xy=(0.5, 0.90), colour=RED, size=8,
            ha="center", weight="bold")
        a.set_yticks([])
        a.set_xlabel("P$_2$ (d)", fontsize=8)
        a.tick_params(labelsize=7)
        despine(a)
    save(fig, "fig8_p2posteriors.svg")


# ------------------------------- Fig. 9  <->  H26 Fig. 6 high-evidence 2-sat models
def fig9(D):
    pub, post, meta = D["pub"], D["post"], D["meta"]
    peaks = meta["fig5_peaks"]
    t0 = float(pub["bjd"].min())
    tt = pub["bjd"] - t0
    grid = np.linspace(0, tt.max(), 2500)

    fig, axs = plt.subplots(2, 2, figsize=(7.4, 4.4), sharex=True, sharey=True,
                            gridspec_kw={"hspace": 0.16, "wspace": 0.08})
    for a, pk in zip(axs.ravel(), peaks):
        key = f"win{pk:g}"
        ss = post[f"{key}__samples"]
        ll = list(post[f"{key}__labels"])
        g = dict(zip(ll, np.median(ss, axis=0)))
        model = (g["offset"]
                 + keplerian_rv(grid, g["P1"], g["K1"], 0.0, g["om1"], 0.0)
                 + keplerian_rv(grid, g["P2"], g["K2"], 0.0, g["om2"], 0.0))
        a.plot(grid, model, "-", lw=1.1, color=INK2, alpha=0.9)
        a.errorbar(tt, pub["rv_ms"], yerr=pub["erv_ms"], fmt="o", ms=3.4,
                   color=ORANGE, elinewidth=0.8, capsize=0, zorder=3)
        d = meta["runs"][key]["dlogz_vs_1sat"]
        tag(a, f"P$_2$ = {g['P2']:.1f} d   K$_2$ = {g['K2']:.0f} m s$^{{-1}}$",
            xy=(0.02, 0.93), size=7.5)
        tag(a, f"ΔlnZ vs one satellite = {d:+.1f}", xy=(0.02, 0.07), colour=RED,
            size=7.5, weight="bold")
        despine(a)
    for a in axs[1, :]:
        a.set_xlabel(f"BJD − {t0:.0f}")
    for a in axs[:, 0]:
        a.set_ylabel("RV  (m s$^{-1}$)")
    save(fig, "fig9_windowmodels.svg")


# ------------------------- Fig. 10  <->  H26 Fig. 7 GLS of every viper output + BERV
def fig10(D):
    ser, par, berv, keep = D["ser"], D["par"], D["berv"], D["keep"]
    ours = D["ours"]
    bj = np.unique(par["BJD"])

    def per_epoch(col):
        v = np.array([np.nanmedian(par[col][par["BJD"] == b]) for b in bj])
        return v

    panels = [("RV (this work)", ser["bjd"][keep], ours[keep], BLUE),
              ("BERV", ser["bjd"], berv, RED)]
    for col, name in [("norm0", "continuum norm₀"), ("norm1", "continuum norm₁"),
                      ("wave0", "wavelength λ₀"), ("wave1", "wavelength λ₁"),
                      ("ip0", "instrumental profile"), ("atm0", "airmass/atm₀"),
                      ("atm1", "atm₁"), ("atm3", "atm₃"),
                      ("bkg0", "background"), ("prms", "fit rms")]:
        panels.append((name, bj, per_epoch(col), INK2))

    ncol = 3
    nrow = int(np.ceil(len(panels) / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(7.4, 1.62 * nrow), sharex=True,
                            gridspec_kw={"hspace": 0.3, "wspace": 0.18})
    for a, (name, t, y, col) in zip(axs.ravel(), panels):
        g = np.isfinite(y)
        if g.sum() < 6 or np.nanstd(y[g]) == 0:
            a.set_axis_off()
            continue
        ls, pw = gls(t, y)
        a.plot(PGRID, pw, lw=0.9, color=col)
        a.axvline(P_PUB, color=INK2, lw=0.9, ls=":", zorder=0)
        i = int(np.argmax(pw))
        a.plot([PGRID[i]], [pw[i]], "v", ms=4, color=col, clip_on=False)
        j = int(np.argmin(abs(PGRID - P_PUB)))
        a.set_xscale("log")
        a.set_xlim(5, 460)
        a.set_ylim(0, 1.62 * pw.max())
        tag(a, name, xy=(0.03, 0.91), size=7.5)
        tag(a, f"peak {PGRID[i]:.0f} d · power at 171 d = {pw[j]:.2f}", xy=(0.03, 0.75),
            size=6.3, colour=RED if pw[j] > 0.45 else MUTED)
        a.tick_params(labelsize=7)
        a.set_yticks([])
        despine(a)
    for a in axs.ravel()[len(panels):]:
        a.set_axis_off()
    for a in axs[-1, :]:
        a.set_xlabel("period (d)", fontsize=8)
    fig.suptitle("GLS periodograms of every viper output, and of the barycentric "
                 "correction", fontsize=9.5, color=INK, y=0.995)
    save(fig, "fig10_viper_gls.svg")


# ------------------------------------------- Figs. 11-12  <->  H26 Figs. 8-9 corners
def corner(samples, labels, truths, truth_labels, colour, fill, title, fname,
           units=None):
    n = samples.shape[1]
    fig, axs = plt.subplots(n, n, figsize=(1.42 * n + 0.7, 1.42 * n + 0.7),
                            gridspec_kw={"hspace": 0.07, "wspace": 0.07})
    lims = [np.percentile(samples[:, i], [0.5, 99.5]) for i in range(n)]
    for i in range(n):
        for j in range(n):
            a = axs[i, j]
            if j > i:
                a.set_axis_off()
                continue
            if i == j:
                a.hist(samples[:, i], bins=34, range=lims[i], color=fill,
                       edgecolor=colour, lw=0.6)
                q = np.percentile(samples[:, i], [16, 50, 84])
                for v in q:
                    a.axvline(v, color=colour, lw=0.7, ls=":")
                if truths[i] is not None:
                    a.axvline(truths[i], color=ORANGE, lw=1.3)
                u = units[i] if units and units[i] else ""
                a.set_title(quantile_label(q, u), fontsize=7.5, color=INK, pad=3)
                a.set_yticks([])
                a.set_xlim(*lims[i])
            else:
                a.hist2d(samples[:, j], samples[:, i], bins=36,
                         range=[lims[j], lims[i]], cmap="Blues", rasterized=True)
                if truths[j] is not None and truths[i] is not None:
                    a.plot(truths[j], truths[i], "P", ms=7, color=ORANGE,
                           mec="white", mew=0.8, zorder=5)
                elif truths[j] is not None:
                    a.axvline(truths[j], color=ORANGE, lw=1.1)
                elif truths[i] is not None:
                    a.axhline(truths[i], color=ORANGE, lw=1.1)
                a.set_xlim(*lims[j])
                a.set_ylim(*lims[i])
            a.tick_params(labelsize=6.5)
            if i < n - 1:
                a.set_xticklabels([])
            else:
                a.set_xlabel(labels[j], fontsize=8)
                for lb in a.get_xticklabels():
                    lb.set_rotation(40)
                    lb.set_ha("right")
            if j > 0 or i == 0:
                a.set_yticklabels([])
            if j == 0 and i > 0:
                a.set_ylabel(labels[i], fontsize=8)
            despine(a)
    handles = [Line2D([], [], color=ORANGE, lw=2, label=truth_labels)]
    fig.legend(handles=handles, loc="upper right", fontsize=8,
               bbox_to_anchor=(0.99, 0.995))
    fig.suptitle(title, fontsize=9.5, color=INK, x=0.5, y=1.035)
    save(fig, fname)


def fig11_12(D):
    post, meta = D["post"], D["meta"]
    mh = meta["host_mass_mjup"] * 1.89813e27
    h = meta["h26"]

    # Fig. 11 -- large satellite, one-satellite eccentric fit (H26 Fig. 8).
    s = post["sat1_ecc__samples"]
    lab = list(post["sat1_ecc__labels"])
    P = s[:, lab.index("P1")]
    K = s[:, lab.index("K1")]
    e = s[:, lab.index("e1")]
    m = msini_jup(P, K, e, mh)
    corner(np.column_stack([P, K, e, m]),
           ["P (d)", "K (m s$^{-1}$)", "e", "m sin i (M$_{Jup}$)"],
           [h["P1_1sat"], h["K1_1sat"], h["e1_1sat"], h["msini1_1sat"]],
           "H26 Table 1 (Nature)", BLUE, BLUE_FILL,
           "Large satellite — one-satellite eccentric fit on H26's own RV table",
           "fig11_corner_sat1.svg", units=["d", "m/s", "", "M$_J$"])

    # Fig. 12 -- small satellite, two-satellite fit in H26's own 88 d window (Fig. 9).
    s = post["sat2_win88__samples"]
    lab = list(post["sat2_win88__labels"])
    P = s[:, lab.index("P2")]
    K = s[:, lab.index("K2")]
    e = s[:, lab.index("e2")]
    m = msini_jup(P, K, e, mh)
    corner(np.column_stack([P, K, e, m]),
           ["P$_2$ (d)", "K$_2$ (m s$^{-1}$)", "e$_2$", "m sin i (M$_{Jup}$)"],
           [h["P2"], None, h["e2"], h["msini2"]],
           "H26 Table 1 (Nature)", BLUE, BLUE_FILL,
           "Small satellite — two-satellite fit, P$_2$ in H26's own 75–100 d window",
           "fig12_corner_sat2.svg", units=["d", "m/s", "", "M$_J$"])


def main():
    print("M18 figures ->", EXP)
    D = load_all()
    tops = fig5(D)
    fig6(D)
    nod = fig7(D)
    fig8(D)
    fig9(D)
    fig10(D)
    fig11_12(D)

    print("\nnumbers for the captions")
    for k, (Pp, pwp, Po, pwo) in tops.items():
        print(f"  {k:28s} H26 peak {Pp:7.2f} d (power {pwp:.3f}) | "
              f"ours {Po:7.2f} d (power {pwo:.3f})")
    print("  nodding gain (%):", {k: round(v, 1) for k, v in nod.items()})


if __name__ == "__main__":
    main()
