"""M6 figures, generated from the committed artifacts (never hand-drawn).

  fig 1  out/m6_fig_mrs_D.png       -- candidate D's deblended MRS spectra,
         the star and the contaminant, the continuum, the residual, and where
         PR-2's fixed feature list falls at the published z = 0.922
  fig 2  out/m6_fig_zscan_D.png     -- the blind redshift scan and the star
         control on the same axes
  fig 3  out/m6_fig_morph.png       -- N4's structure index: the |b| > 50 deg
         calibration distribution, and S versus Galactic latitude
  fig 4  out/m6_fig_completeness.png-- the injection-recovery completeness
         function, gamma x T_ds and gamma x |b|

    python scripts/m6_figures.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt              # noqa: E402
import numpy as np                           # noqa: E402
import pandas as pd                          # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
Z = 0.922


def fig_mrs():
    from m6_mrs_redshift import LINES, continuum, prep
    con = pd.read_csv(OUT / "m6_mrs_D_contaminant_spectrum.csv")
    star = pd.read_csv(OUT / "m6_mrs_D_star_spectrum.csv")
    lam, f, e, c, _ = prep(con)
    ls, fs, _, cs, _ = prep(star)
    fig, ax = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                           gridspec_kw={"height_ratios": [2, 1]})
    ax[0].plot(lam, f * 1e6, lw=0.6, color="#1f4e79", label="contaminant (deblended)")
    ax[0].plot(lam, c * 1e6, lw=1.3, color="#d95f02", label="continuum (LOESS, z-independent)")
    ax[0].plot(ls, fs * 1e6, lw=0.6, color="#7f7f7f", alpha=0.8, label="star (deblended)")
    ax[0].set_yscale("log")
    ax[0].set_ylabel(r"$F_\nu$  [$\mu$Jy]")
    ax[0].legend(loc="upper left", fontsize=9, frameon=False)
    ax[0].set_title("Candidate D, JWST/MIRI MRS -- first independent extraction "
                    "of the 1.23\" contaminant", fontsize=11)
    r = f / c - 1.0
    ax[1].axhline(0, color="k", lw=0.6)
    ax[1].plot(lam, r, lw=0.6, color="#1f4e79")
    for lr, fw, kind, nm in LINES:
        lo = lr * (1 + Z)
        if not (lam.min() < lo < lam.max()):
            continue
        col = "#d95f02" if kind == "pah" else "#2a7f3e"
        ax[1].axvline(lo, color=col, lw=0.8, ls="--", alpha=0.75)
        ax[1].text(lo, 0.62, nm, rotation=90, fontsize=7, color=col,
                   ha="right", va="top")
    sl = 9.7 * (1 + Z)
    if lam.min() < sl < lam.max():
        ax[1].axvspan(sl - 1.0, sl + 1.0, color="#888888", alpha=0.16)
        ax[1].text(sl, -0.28, "silicate 9.7", fontsize=7, ha="center",
                   color="#444444")
    ax[1].set_ylim(-0.35, 0.7)
    ax[1].set_xlabel(r"observed wavelength [$\mu$m]")
    ax[1].set_ylabel(r"$F/C - 1$")
    ax[1].set_title("residual, with PR-2's fixed feature list drawn at the "
                    "PUBLISHED z = 0.922 (a hypothesis test, not a fit)",
                    fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "m6_fig_mrs_D.png", dpi=140)
    plt.close(fig)
    print("  -> m6_fig_mrs_D.png")


def fig_zscan():
    zc = pd.read_csv(OUT / "m6_mrs_D_zscan.csv")
    nc = pd.read_csv(OUT / "m6_mrs_D_narrow_consensus.csv")
    res = json.loads((OUT / "m6_mrs_D_redshift.json").read_text())
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(zc["z"], zc["score"], lw=0.8, color="#1f4e79")
    ax[0].axvline(Z, color="#d95f02", lw=1.2, ls="--",
                  label="published z = 0.922")
    ax[0].axvline(res["blind_scan"]["z_best"], color="#2a7f3e", lw=1.0,
                  label="blind best z = %.3f" % res["blind_scan"]["z_best"])
    ax[0].set_ylabel("matched-filter score")
    ax[0].legend(fontsize=9, frameon=False)
    ax[0].set_title("Blind redshift scan on the fixed feature list "
                    "(peak/rms = %.1f -- it does not pin z)"
                    % res["blind_scan"]["peak_over_scan_rms"], fontsize=11)
    ax[1].plot(nc["z"], nc["n_5sigma"], lw=0.7, color="#555555")
    ax[1].axvline(Z, color="#d95f02", lw=1.2, ls="--")
    ax[1].set_xlim(0, 2.5)
    ax[1].set_xlabel("redshift")
    ax[1].set_ylabel(r"narrow lines at $\geq 5\sigma$")
    n922 = res["narrow_consensus_scan"]["n_at_published_z"]
    frac = res["narrow_consensus_scan"]["fraction_of_grid_reaching_n_at_published_z"]
    ax[1].set_title("Narrow-line consensus, blind in z: %d lines at z = 0.922, "
                    "and %.0f%% of the grid does at least as well"
                    % (n922, 100 * frac), fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "m6_fig_zscan_D.png", dpi=140)
    plt.close(fig)
    print("  -> m6_fig_zscan_D.png")


def fig_morph():
    cal = pd.read_csv(ROOT / "data" / "morph" / "m6_morph_calib.csv")
    rm = pd.read_csv(OUT / "m6_morph_flags_rmse.csv")
    cal = cal[cal["morph_ok"].fillna(False)]
    rm = rm[rm["morph_ok"].fillna(False)]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    bins = np.linspace(0.4, 4.0, 90)
    for b, col in (("w3_S", "#1f4e79"), ("w4_S", "#d95f02")):
        ax[0].hist(cal[b].clip(0.4, 4.0), bins=bins, histtype="step", lw=1.3,
                   color=col, density=True, label=b.replace("_S", " structure index S"))
    ax[0].axvline(1.0, color="k", lw=0.8, ls=":")
    ax[0].text(1.02, ax[0].get_ylim()[1] * 0.92, "S = 1: pure noise", fontsize=8)
    ax[0].set_xlabel("S = $\\sigma_{obs}/\\sigma_{exp}$")
    ax[0].set_ylabel("density")
    ax[0].set_title("N4 calibration, |b| > 50$^\\circ$ parent", fontsize=10)
    ax[0].legend(fontsize=8, frameon=False)
    bands = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]
    ab = np.abs(rm["glat"])
    xs, med, hi = [], [], []
    for lo, h in bands:
        s = rm[(ab >= lo) & (ab < h)]
        if not len(s):
            continue
        xs.append("%d-%d" % (lo, h))
        med.append(np.nanmedian(np.maximum(s["w3_S"], s["w4_S"])))
        hi.append(100 * float(s["n4_flag"].mean()))
    a2 = ax[1]
    a2.bar(xs, hi, color="#1f4e79", alpha=0.85)
    a2.set_ylabel("% of RMSE survivors N4 flags", color="#1f4e79")
    a2.set_xlabel("|b| band [deg]")
    a3 = a2.twinx()
    a3.plot(xs, med, "o-", color="#d95f02")
    a3.set_ylabel("median max(S)", color="#d95f02")
    a2.set_title("N4 acts in the plane and not at the pole", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "m6_fig_morph.png", dpi=140)
    plt.close(fig)
    print("  -> m6_fig_morph.png")


def fig_completeness():
    d = pd.read_csv(ROOT / "data" / "injection" / "m6_injection_table.csv")
    d = d[d["gamma_true"] > 0]
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
    p = d.pivot_table(index="gamma_true", columns="t_ds_true", values="recovered")
    im = ax[0].imshow(p.values, origin="lower", aspect="auto", cmap="viridis",
                      vmin=0, vmax=1)
    ax[0].set_xticks(range(len(p.columns)))
    ax[0].set_xticklabels([int(c) for c in p.columns])
    ax[0].set_yticks(range(len(p.index)))
    ax[0].set_yticklabels(p.index)
    ax[0].set_xlabel("$T_{DS}$ [K]")
    ax[0].set_ylabel("$\\gamma$ injected")
    ax[0].set_title("pre-visual recovery fraction", fontsize=10)
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            ax[0].text(j, i, "%.2f" % p.values[i, j], ha="center", va="center",
                       fontsize=7,
                       color="w" if p.values[i, j] < 0.55 else "k")
    fig.colorbar(im, ax=ax[0])
    lbl = ["0-5", "5-10", "10-20", "20-30", "30-50", "50-90"]
    for g in sorted(d["gamma_true"].unique()):
        s = d[d["gamma_true"] == g].groupby("bband")["recovered"].mean()
        ax[1].plot([lbl[int(i)] for i in s.index], s.values, "o-", lw=1.2,
                   label="$\\gamma$ = %.2f" % g, ms=3)
    ax[1].set_xlabel("|b| band [deg]")
    ax[1].set_ylabel("pre-visual recovery fraction")
    ax[1].set_title("completeness against Galactic latitude", fontsize=10)
    ax[1].legend(fontsize=7, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "m6_fig_completeness.png", dpi=140)
    plt.close(fig)
    print("  -> m6_fig_completeness.png")


if __name__ == "__main__":
    for fn in (fig_mrs, fig_zscan, fig_morph, fig_completeness):
        try:
            fn()
        except Exception as ex:                          # noqa: BLE001
            print("  SKIP %s: %s: %s" % (fn.__name__, type(ex).__name__, ex))
