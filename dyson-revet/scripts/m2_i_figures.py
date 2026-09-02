"""M2: the two candidate-I dossier figures.

  out/m2_I_finder.png -- finder chart. Legacy DR10 grz colour (0.262"/px)
      alongside the AllWISE W1/W3/W4 atlas cutouts on a common 60" field, with
      the Gaia position (proper-motion propagated to the WISE epoch), both
      measured MIR centroids (AllWISE and unWISE bases), the 6.8" NE red PSF
      source, the W3 PSF half-width and the W4 beam. Everything account-free.

  out/m2_I_sed.png -- the SED that the whole candidacy rests on: 179 archival
      VizieR points + the SPHEREx QR2 forced spectrophotometry (this work) +
      the photospheric template + the fitted excess, with the W3/W4 points
      drawn at their true significance and the WISE All-Sky W3 upper limit
      shown alongside the AllWISE W3 "detection".

Inputs are the M1 artifacts (data/cutouts, data/photometry/sed_I.csv,
out/w3_spherex_I_sed.csv, out/w2_centroid_offsets.csv). No accounts, nothing
sent anywhere.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT, CUT = ROOT / "data", ROOT / "out", ROOT / "data" / "cutouts"
sys.path.insert(0, str(ROOT / "scripts"))
from w1_selection import (LAM_UM, ZP_JY, combine, ds_absolute_mags,  # noqa: E402
                          load_pm13, template_grid)

RA_I, DEC_I = 144.976333, 7.007741      # Gaia DR3 J2016.0
PMRA, PMDEC = -4.744241, -14.76036      # mas/yr
EPOCH_W12, EPOCH_W34 = 2010.36, 2010.35
DIST = 169.27722
# Legacy DR10 neighbour (data/photometry/legacy_dr10_I.csv, row 3)
RA_RED, DEC_RED = 144.9774805626649, 7.009232458382757
LS_CUTOUT = "https://www.legacysurvey.org/viewer/cutout.jpg"


def propagate(epoch: float) -> tuple[float, float]:
    dt = epoch - 2016.0
    dec = DEC_I + PMDEC * dt / 3.6e6
    ra = RA_I + PMRA * dt / 3.6e6 / np.cos(np.radians(DEC_I))
    return ra, dec


def sep_pa(ra, dec, ra0=RA_I, dec0=DEC_I):
    dra = (ra - ra0) * np.cos(np.radians(dec0)) * 3600.0
    ddec = (dec - dec0) * 3600.0
    return float(np.hypot(dra, ddec)), float(np.degrees(np.arctan2(dra, ddec)) % 360)


# --------------------------------------------------------------------------
def finder() -> None:
    size_as = 60.0
    jpg = CUT / "I_legacy_dr10.jpg"
    if not jpg.exists():
        px = 0.262
        n = int(round(size_as / px))
        r = requests.get(LS_CUTOUT, params={
            "ra": RA_I, "dec": DEC_I, "layer": "ls-dr10", "pixscale": px,
            "size": n}, timeout=300)
        r.raise_for_status()
        jpg.write_bytes(r.content)
        print(f"  fetched Legacy DR10 cutout ({len(r.content)} bytes, {n} px)")

    cen = pd.read_csv(OUT / "w2_centroid_offsets.csv")
    cen = cen[cen.label == "I"].set_index("band")

    fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.9))

    # --- panel 0: Legacy DR10 grz -----------------------------------------
    import matplotlib.image as mpimg
    im = mpimg.imread(jpg)
    ax = axes[0]
    n = im.shape[0]
    px = size_as / n
    ext = [size_as / 2, -size_as / 2, -size_as / 2, size_as / 2]  # E left, N up
    ax.imshow(im, extent=ext, origin="upper")
    ax.plot(0, 0, marker="*", ms=17, mfc="none", mec="#ffdd00", mew=1.8)
    s_red, pa_red = sep_pa(RA_RED, DEC_RED)
    dx = (RA_RED - RA_I) * np.cos(np.radians(DEC_I)) * 3600.0
    dy = (DEC_RED - DEC_I) * 3600.0
    ax.plot(dx, dy, marker="o", ms=15, mfc="none", mec="#00e5ff", mew=1.8)
    ax.annotate(f"red PSF src\n{s_red:.1f}\" PA {pa_red:.0f}$^\\circ$\n"
                f"$r-z$=4.5", (dx, dy), textcoords="offset points",
                xytext=(9, 6), color="#00e5ff", fontsize=8.5, weight="bold")
    ax.set_title("Legacy Survey DR10  $grz$", fontsize=11)
    ax.set_xlim(size_as / 2, -size_as / 2)
    ax.set_ylim(-size_as / 2, size_as / 2)
    # compass + scale bar
    ax.annotate("", xy=(-22, -18), xytext=(-22, -24),
                arrowprops=dict(arrowstyle="->", color="w", lw=1.4))
    ax.text(-22, -16.5, "N", color="w", ha="center", fontsize=9)
    ax.annotate("", xy=(-16, -24), xytext=(-22, -24),
                arrowprops=dict(arrowstyle="->", color="w", lw=1.4))
    ax.text(-14.5, -24, "E", color="w", va="center", fontsize=9)
    ax.plot([22, 12], [-25, -25], "-", color="w", lw=2.5)
    ax.text(17, -23.5, '10"', color="w", ha="center", fontsize=9)

    # --- panels 1-3: AllWISE W1 / W3 / W4 ---------------------------------
    fwhm = {1: 6.1, 3: 6.5, 4: 12.0}
    for k, band in enumerate([1, 3, 4], start=1):
        ax = axes[k]
        path = CUT / f"I_w{band}_allwise.fits"
        with fits.open(path) as h:
            img = h[0].data.astype(float)
            wcs = WCS(h[0].header)
        _, med, std = sigma_clipped_stats(img, sigma=3.0)
        ep = EPOCH_W12 if band <= 2 else EPOCH_W34
        ra_e, dec_e = propagate(ep)
        xs, ys = wcs.world_to_pixel_values(ra_e, dec_e)
        scale = np.abs(wcs.proj_plane_pixel_scales()[0].to_value("arcsec"))
        half = size_as / 2 / scale
        # asinh stretch: W1 spans a factor ~10^3 between star and sky, and a
        # linear scale turns the star into a black blob that hides the PSF core
        sub = img - med
        norm = matplotlib.colors.AsinhNorm(
            linear_width=2.0 * std, vmin=-1.5 * std,
            vmax=float(np.nanpercentile(sub, 99.98)) if band == 1
            else 6 * std)
        ax.imshow(sub, origin="lower", cmap="gray_r", norm=norm)
        ax.plot(xs, ys, marker="*", ms=17, mfc="none", mec="#cc0000", mew=1.8)
        xr, yr = wcs.world_to_pixel_values(RA_RED, DEC_RED)
        ax.plot(xr, yr, marker="o", ms=15, mfc="none", mec="#0088cc", mew=1.5)
        # measured centroids, both imaging bases
        for tag, col, mk in ((f"W{band}", "#008800", "+"),
                             (f"W{band}u", "#aa00aa", "x")):
            if tag in cen.index:
                row = cen.loc[tag]
                xc, yc = wcs.world_to_pixel_values(row.ra_centroid,
                                                   row.dec_centroid)
                ax.plot(xc, yc, marker=mk, ms=13, mew=2.4, color=col,
                        label=("AllWISE centroid" if mk == "+"
                               else "unWISE centroid"))
        # beam
        ax.add_patch(mpatches.Circle((xs, ys), fwhm[band] / 2 / scale,
                                     fill=False, ec="#cc0000", ls=":", lw=1.2))
        ttl = {1: "AllWISE W1  3.4 $\\mu$m  S/N 44",
               3: "AllWISE W3  12 $\\mu$m  S/N 2.4",
               4: "AllWISE W4  22 $\\mu$m  S/N 3.3"}[band]
        ax.set_title(ttl, fontsize=11)
        ax.set_xlim(xs + half, xs - half)   # E left
        ax.set_ylim(ys - half, ys + half)
        if band == 3:
            ax.legend(loc="lower left", fontsize=8, framealpha=0.85)
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Candidate I = Gaia DR3 3854090071297359616 = AllWISE "
                 "J093954.31+070027.9   |   60\" fields, N up / E left   |   "
                 "star marker = Gaia position propagated to the WISE epoch; "
                 "dotted circle = band PSF FWHM", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "m2_I_finder.png", dpi=145)
    plt.close(fig)
    print("  wrote out/m2_I_finder.png")


# --------------------------------------------------------------------------
def sed() -> None:
    g = pd.read_csv(DATA / "photometry" / "candidates_gaia_chain.csv")
    r = g[g.label == "I"].iloc[0]
    dmod = 5 * np.log10(DIST / 10.0)
    mg_abs = r["phot_g_mean_mag"] - dmod

    # archival VizieR sed
    v = pd.read_csv(DATA / "photometry" / "sed_I.csv")
    v = v[(v.sep_arcsec < 3.0) & v.sed_flux.notna() & (v.sed_flux > 0)]

    # SPHEREx (this work)
    sx = pd.read_csv(OUT / "w3_spherex_I_sed.csv")
    nb = 40
    edges = np.geomspace(sx.lam_um.min(), sx.lam_um.max(), nb + 1)
    sx["_b"] = np.digitize(sx.lam_um, edges)
    sxb = sx.groupby("_b").agg(lam=("lam_um", "median"),
                               f=("flux_jy", "median"),
                               n=("flux_jy", "size")).query("n >= 3")

    # photosphere + excess model (M1 fit: T = 125 K, gamma = 0.085)
    pm = load_pm13()
    tg = template_grid(pm, mg_abs - 0.05, mg_abs + 0.05, step=0.05)
    i0 = 0
    t_ds, gam = 124.7, 0.0852
    dsm = ds_absolute_mags(np.array([t_ds]), np.array([gam]),
                           np.array([tg["logL"][i0]]))
    dim = -2.5 * np.log10(1 - gam)
    lam_pts, f_star, f_tot = [], [], []
    for b in ["J", "H", "Ks", "W1", "W2", "W3", "W4"]:
        ms = tg[b][i0] + dmod
        mt = combine(tg[b][i0] + dim, dsm[b][0]) + dmod
        lam_pts.append(LAM_UM[b])
        f_star.append(ZP_JY[b] * 10 ** (-0.4 * ms))
        f_tot.append(ZP_JY[b] * 10 ** (-0.4 * mt))
    o = np.argsort(lam_pts)
    lam_pts = np.array(lam_pts)[o]
    f_star = np.array(f_star)[o]
    f_tot = np.array(f_tot)[o]
    # Draw the model on a fine grid instead of straight lines between the 7
    # band points: the photosphere is log-log interpolated between bands and
    # the excess is the analytic blackbody, so the 5-12 um behaviour is the
    # model's, not the plotting library's.
    lam_fine = np.geomspace(1.0, 30.0, 400)
    f_star_fine = np.exp(np.interp(np.log(lam_fine), np.log(lam_pts),
                                   np.log(f_star)))
    C_, H_, KB_ = 2.99792458e8, 6.62607015e-34, 1.380649e-23
    nu = C_ / (lam_fine * 1e-6)
    bnu = (2 * H_ * nu ** 3 / C_ ** 2) / np.expm1(H_ * nu / (KB_ * t_ds))
    # normalise the blackbody to pass through the fitted total at W4
    i_w4 = int(np.argmin(np.abs(lam_fine - LAM_UM["W4"])))
    f_exc_fine = bnu / bnu[i_w4] * (f_tot[-1] - f_star[-1])
    f_tot_fine = f_star_fine * (1 - gam) + f_exc_fine

    fig, ax = plt.subplots(figsize=(9.2, 6.0))
    ax.plot(v.lam_um, v.sed_flux, "o", ms=3.4, color="#9aa5b1",
            label=f"archival VizieR photometry ({len(v)} pts, 26 catalogues)")
    ax.plot(sxb.lam, sxb.f, "-", lw=2.0, color="#d95f02",
            label="SPHEREx QR2 forced spectrophotometry (this work, 271 exp.)")
    ax.plot(lam_fine, f_star_fine, "--", color="#1b4f72", lw=1.6,
            label="M3.5V photosphere (empirical template)")
    ax.plot(lam_fine, f_tot_fine, "-", color="#117733", lw=1.6,
            label=f"photosphere + {t_ds:.0f} K blackbody, $\\gamma$={gam:.3f}")

    # the two points the candidacy rests on
    for band, m, sm, col in (("W3", r.w3mpro, r.w3mpro_error, "#cc3311"),
                             ("W4", r.w4mpro, r.w4mpro_error, "#cc3311")):
        f = ZP_JY[band] * 10 ** (-0.4 * m)
        e = f * 0.9210 * sm
        ax.errorbar(LAM_UM[band], f, yerr=e, fmt="s", ms=8, color=col,
                    capsize=4, lw=2, zorder=6,
                    label=("AllWISE W3, W4 (S/N 2.4, 3.3) -- the entire excess"
                           if band == "W3" else None))
    # WISE All-Sky release: W3 is an upper limit, W4 agrees
    f_as3 = ZP_JY["W3"] * 10 ** (-0.4 * 12.015)
    ax.errorbar(LAM_UM["W3"] * 1.06, f_as3, yerr=f_as3 * 0.45, uplims=True,
                fmt="v", ms=9, color="#882255", lw=2, zorder=7,
                label="WISE All-Sky W3: ph_qual 'U' (upper limit, S/N 1.3)")
    f_as4 = ZP_JY["W4"] * 10 ** (-0.4 * 8.594)
    ax.errorbar(LAM_UM["W4"] * 1.06, f_as4, yerr=f_as4 * 0.9210 * 0.366,
                fmt="D", ms=6, color="#882255", lw=1.8, capsize=3, zorder=7,
                label="WISE All-Sky W4 (S/N 3.0)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.3, 40)
    ax.set_ylim(3e-5, 2e-2)
    ax.set_xlabel("wavelength [$\\mu$m]")
    ax.set_ylabel("$F_\\nu$ [Jy]")
    ax.set_title("Candidate I -- the SED the candidacy rests on\n"
                 "photospheric to 5 $\\mu$m; the excess is two WISE points, "
                 "one of which is an upper limit in the earlier reduction",
                 fontsize=11)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=8.4, loc="lower left", framealpha=0.93)
    fig.tight_layout()
    fig.savefig(OUT / "m2_I_sed.png", dpi=150)
    plt.close(fig)
    print("  wrote out/m2_I_sed.png")


if __name__ == "__main__":
    print("finder chart:")
    finder()
    print("SED:")
    sed()
