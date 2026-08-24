"""M7 figures, generated from the committed artifacts only.

    python scripts/m7_figures.py

  m7_fig_epsf.png        the empirical PSF, the acceptance test before/after,
                         and PR-1's 2x2 injection-recovery
  m7_fig_families.png    the completeness function for three SED families
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
BANDS = ("f560w_star", "f560w_con", "f1000w_star", "f1000w_con",
         "f1500w_star", "f1500w_con")


def fig_epsf() -> None:
    psfs = json.load(open(OUT / "m7_epsf_psfs.json"))
    inj = pd.read_csv(OUT / "m7_epsf_injection.csv")
    a6 = json.load(open(OUT / "m6_mrs_D_redshift.json"))["acceptance"]
    a7 = json.load(open(OUT / "m6_mrs_D_epsf_redshift.json"))["acceptance"]
    u = np.linspace(0, 8, 160)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))

    # (a) the profiles
    for b, d in sorted(psfs.items()):
        if not d["is_donor"]:
            continue
        p = np.median([bb["prof"] for bb in d["bins"]], axis=0)
        ax[0].semilogy(u, np.maximum(p, 1e-8),
                       color="C0" if d["donor"] == "star" else "C3",
                       lw=1.0, alpha=0.8)
    g = np.exp(-0.5 * (u / (1 / 2.3548)) ** 2)
    g = g / np.trapezoid(g * 2 * np.pi * u, u)
    ax[0].semilogy(u, np.maximum(g, 1e-8), "k--", lw=2,
                   label="M6 Gaussian (no wings)")
    ax[0].plot([], [], color="C0", label="empirical, star-derived")
    ax[0].plot([], [], color="C3", label="empirical, contaminant-derived")
    ax[0].set_xlim(0, 5)
    ax[0].set_ylim(1e-4, 3)
    ax[0].set_xlabel("radius / PSF FWHM")
    ax[0].set_ylabel("normalised profile")
    ax[0].set_title("(a) the empirical PSF, measured from the cubes")
    ax[0].legend(fontsize=8, loc="upper right")
    ax[0].grid(alpha=0.25)

    # (b) the acceptance test
    x = np.arange(len(BANDS))
    r6 = [a6[k]["ratio"] for k in BANDS]
    r7 = [a7[k]["ratio"] for k in BANDS]
    ax[1].axhspan(0.7, 1.3, color="0.88", label="PR-2 tolerance, +-30%")
    ax[1].axhline(1.0, color="k", lw=0.8)
    ax[1].plot(x, r6, "o", ms=9, color="C1", label="M6 Gaussian: 4 of 6")
    ax[1].plot(x, r7, "s", ms=9, color="C2", label="M7 empirical: 6 of 6")
    for i in range(len(BANDS)):
        ax[1].plot([x[i], x[i]], [r6[i], r7[i]], color="0.6", lw=1, zorder=0)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([k.replace("_", "\n") for k in BANDS], fontsize=8)
    ax[1].set_ylabel("MRS / M4 imaging flux ratio")
    ax[1].set_title("(b) M6 PR-2's acceptance test, unchanged")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.25, axis="y")

    # (c) the 2x2 injection-recovery
    for (ip, rp), g2 in inj.groupby(["inject_psf", "recover_psf"]):
        m = g2.groupby("f_true")["ratio"].median()
        sty = "-o" if ip == "epsf" else "--s"
        col = "C2" if rp == "epsf" else "C1"
        ax[2].plot(m.index, m.values, sty, color=col, ms=6,
                   label="inject %s -> recover %s" % (ip, rp))
    ax[2].axhline(1.0, color="k", lw=0.8)
    ax[2].set_xscale("log")
    ax[2].set_ylim(0.3, 1.4)
    ax[2].set_xlabel("true companion flux fraction")
    ax[2].set_ylabel("recovered / true")
    ax[2].set_title("(c) PR-1 injection-recovery on the cubes")
    ax[2].legend(fontsize=8, loc="lower right")
    ax[2].grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(OUT / "m7_fig_epsf.png", dpi=130)
    print("-> out/m7_fig_epsf.png")


def fig_families() -> None:
    w = pd.read_csv(OUT / "m7_injection_families_walls.csv")
    hd = pd.read_csv(OUT / "m7_injection_families_headline.csv")
    lab = {("single_bb", 0.0): "single blackbody (control)",
           ("two_temp", 0.3): "two-temperature, f_warm 0.3",
           ("two_temp", 0.5): "two-temperature, f_warm 0.5",
           ("two_temp", 0.7): "two-temperature, f_warm 0.7",
           ("modbb", 1.0): r"optically thin, $\beta$=1",
           ("modbb", 2.0): r"optically thin, $\beta$=2"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))

    for i, (axis, xl) in enumerate((("gamma", "covering fraction $\\gamma$"),
                                    ("t_ds", "dust temperature $T$ (K)"))):
        s = w[w["axis"] == axis]
        for (fam, par), g in s.groupby(["family", "par"]):
            g = g.sort_values("value")
            ax[i].plot(g["value"], 100 * g["previsual"], "-o", ms=4,
                       label=lab.get((fam, par), "%s %s" % (fam, par)),
                       lw=2.2 if fam == "single_bb" else 1.3,
                       color="k" if fam == "single_bb" else None,
                       zorder=5 if fam == "single_bb" else 2)
        ax[i].set_xscale("log" if axis == "gamma" else "linear")
        ax[i].set_xlabel(xl)
        ax[i].set_ylabel("pre-visual recovery (%)")
        ax[i].grid(alpha=0.25)
        ax[i].set_title("(%s) the %s wall, per SED family"
                        % ("ab"[i], "$\\gamma$" if axis == "gamma" else "T"))
    ax[0].legend(fontsize=7, loc="upper left")

    y = np.arange(len(hd))
    c = ["k" if f == "single_bb" else ("C0" if f == "two_temp" else "C3")
         for f in hd["family"]]
    ax[2].barh(y, 100 * hd["ingrid_b_gt_30"], color=c, alpha=0.85)
    ax[2].axvline(45.85, color="C2", lw=2, ls="--",
                  label="M6's single-blackbody 45.8%")
    ax[2].set_yticks(y)
    ax[2].set_yticklabels([lab.get((f, p), "%s %s" % (f, p))
                           for f, p in zip(hd["family"], hd["par"])],
                          fontsize=8)
    ax[2].set_xlabel("in-grid pre-visual recovery, |b| > 30 deg (%)")
    ax[2].set_title("(c) the catalogue's completeness number")
    ax[2].legend(fontsize=8)
    ax[2].grid(alpha=0.25, axis="x")

    fig.tight_layout()
    fig.savefig(OUT / "m7_fig_families.png", dpi=130)
    print("-> out/m7_fig_families.png")


if __name__ == "__main__":
    fig_epsf()
    try:
        fig_families()
    except FileNotFoundError as e:
        print("families figure skipped:", e)
