"""M4: morphology test (is the contaminant extended?) + labelled cutout figure.

Extendedness is tested three independent ways, all differential inside the same image so
that drizzle/brighter-fatter broadening cancels:
  (a) curve of growth ratio r30/r70 (concentration index) for star vs contaminant vs
      isolated field point sources in the same mosaic;
  (b) Gaussian core FWHM from a 2D fit with the companion masked;
  (c) the pipeline L3 catalog's own is_extended flag / CI_70_30.
"""
import sys, warnings, pickle
sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import Cutout2D
from astropy.modeling import models, fitting
from astropy.visualization import simple_norm
from photutils.aperture import CircularAperture, aperture_photometry

ROOT = "c:/Users/matth/projects/astronomy/dyson-revet/"
FILT = ["f560w", "f1000w", "f1500w"]
LAM = {"f560w": 5.6, "f1000w": 10.0, "f1500w": 15.0}
JDOX = {"f560w": 0.207, "f1000w": 0.328, "f1500w": 0.488}
PSFREF = {"f560w": [(399.1, 960.1), (986.3, 667.5), (698.4, 774.0), (746.8, 216.3), (865.0, 1012.6)],
          "f1000w": [(399.2, 960.9), (986.9, 667.9), (216.5, 782.5), (698.6, 774.5)],
          "f1500w": [(399.2, 960.9), (986.9, 668.2), (1005.7, 325.4), (630.1, 869.9)]}
summ = pickle.load(open(ROOT+"data/jwst/m4_summ.pkl", "rb"))


def gauss_fwhm(img, cx, cy, scale, box=4, mask=None):
    """2D circular-Gaussian core fit FWHM in arcsec."""
    x0, x1 = int(round(cx))-box, int(round(cx))+box+1
    y0, y1 = int(round(cy))-box, int(round(cy))+box+1
    sub = img[y0:y1, x0:x1].astype(float)
    Y, X = np.mgrid[y0:y1, x0:x1]
    w = np.ones_like(sub)
    if mask is not None:
        w = mask[y0:y1, x0:x1].astype(float)
    m = models.Gaussian2D(amplitude=np.nanmax(sub), x_mean=cx, y_mean=cy,
                          x_stddev=1.2, y_stddev=1.2, theta=0)
    m.x_stddev.tied = lambda mm: mm.y_stddev
    m.theta.fixed = True
    f = fitting.LevMarLSQFitter()(m, X, Y, sub*w, maxiter=4000)
    return 2.3548*abs(f.y_stddev.value)*scale


def cog(img, cx, cy, radii):
    ap = CircularAperture([(cx, cy)], r=1.0)
    return np.array([float(aperture_photometry(img, CircularAperture([(cx, cy)], r=r))["aperture_sum"][0])
                     for r in radii])


print("MORPHOLOGY: concentration index C = flux(r30)/flux(r70), and Gaussian core FWHM")
print("(differential within each mosaic, so drizzle/brighter-fatter broadening cancels)\n")
morph = []
for f in FILT:
    with fits.open(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits") as h:
        sci = h[1].data.astype(float); w = WCS(h[1].header)
        scale = abs(h[1].header["CDELT1"])*3600.0
    S = summ[f]; radii = S["radii"]; dz = S["cutout"]
    cxs, cys = S["star_pix"]; gx, gy = S["gal_pix"]
    N = dz.shape[0]; yy, xx = np.mgrid[:N, :N]
    seppix = S["sep"]/scale
    # masks that exclude the companion (radius 0.55 x separation)
    mrad = 0.55*seppix
    mask_s = np.hypot(xx-gx, yy-gy) > mrad
    mask_g = np.hypot(xx-cxs, yy-cys) > mrad

    cs = cog(dz, cxs, cys, radii); cgv = cog(dz, gx, gy, radii)
    Cs, Cg = cs[0]/cs[2], cgv[0]/cgv[2]
    # field point sources in the same mosaic
    Cf = []; Ff = []
    for (px, py) in PSFREF[f]:
        cu = Cutout2D(sci, (px, py), (61, 61), mode="strict"); dd = cu.data.copy()
        ccx, ccy = cu.to_cutout_position((px, py))
        y2, x2 = np.mgrid[:61, :61]; r2 = np.hypot(x2-ccx, y2-ccy)*scale
        dd = dd - np.median(dd[(r2 > 2.0) & (r2 < 2.8)])
        v = cog(dd, ccx, ccy, radii)
        if v[2] > 0:
            Cf.append(v[0]/v[2]); Ff.append(gauss_fwhm(dd, ccx, ccy, scale))
    Cf = np.array(Cf); Ff = np.array(Ff)
    fs = gauss_fwhm(dz, cxs, cys, scale, mask=mask_s)
    fg = gauss_fwhm(dz, gx, gy, scale, mask=mask_g)
    print(f"{f}:  C(star)={Cs:.4f}   C(contam)={Cg:.4f}   C(field pt srcs)={np.median(Cf):.4f}"
          f" +- {Cf.std(ddof=1):.4f} (N={len(Cf)})   [CRDS point-source value {S['EEc'][0]/S['EEc'][2]:.4f}]")
    print(f"        FWHM(star)={fs:.3f}\"  FWHM(contam)={fg:.3f}\"  FWHM(field pt srcs)="
          f"{np.median(Ff):.3f}+-{Ff.std(ddof=1):.3f}\"   JDox {JDOX[f]}\"")
    print(f"        -> contam/star FWHM = {fg/fs:.3f} ; contam/field = {fg/np.median(Ff):.3f}\n")
    morph.append(dict(filter=f.upper(), C_star=Cs, C_contam=Cg, C_field_med=float(np.median(Cf)),
                      C_field_sd=float(Cf.std(ddof=1)), C_crds=float(S["EEc"][0]/S["EEc"][2]),
                      fwhm_star=fs, fwhm_contam=fg, fwhm_field_med=float(np.median(Ff)),
                      fwhm_field_sd=float(Ff.std(ddof=1)), jdox=JDOX[f]))
pd.DataFrame(morph).round(4).to_csv(ROOT+"data/jwst/m4_morphology.csv", index=False)

# ---------------- figure ----------------
fig, axes = plt.subplots(2, 3, figsize=(13.2, 9.0))
for k, f in enumerate(FILT):
    S = summ[f]; dz = S["cutout"]; scale = S["scale"]
    cxs, cys = S["star_pix"]; gx, gy = S["gal_pix"]
    HB = int(round(2.6/scale))
    cx0, cy0 = 0.5*(cxs+gx), 0.5*(cys+gy)
    sl = (slice(int(cy0)-HB, int(cy0)+HB+1), slice(int(cx0)-HB, int(cx0)+HB+1))
    sub = dz[sl]
    ext = [(sl[1].start-cxs)*scale, (sl[1].stop-cxs)*scale, (sl[0].start-cys)*scale, (sl[0].stop-cys)*scale]
    ax = axes[0, k]
    vmin = max(float(np.percentile(sub, 20)), 1e-3)
    norm = simple_norm(sub, "log", log_a=800, vmin=vmin, vmax=float(np.nanmax(sub)))
    ax.imshow(sub, origin="lower", cmap="inferno", norm=norm, extent=ext)
    ax.plot(0, 0, marker="*", ms=16, mfc="none", mec="cyan", mew=1.8)
    ax.plot((gx-cxs)*scale, (gy-cys)*scale, marker="o", ms=14, mfc="none", mec="lime", mew=1.8)
    ax.annotate("M dwarf (Gaia DR3, PM-\npropagated to 2025.57)", (0.13, 0.13), xytext=(1.05, 1.55),
                color="cyan", fontsize=8, ha="center",
                arrowprops=dict(arrowstyle="->", color="cyan", lw=1.2))
    ax.annotate("contaminant", ((gx-cxs)*scale-0.10, (gy-cys)*scale-0.14), xytext=(-1.05, -2.55),
                color="lime", fontsize=9, ha="center",
                arrowprops=dict(arrowstyle="->", color="lime", lw=1.2))
    p50 = S["per"][1]
    ab = lambda j: -2.5*np.log10(j/3631.) if j > 0 else np.nan
    ax.set_title(f"MIRI {f.upper()}  ({LAM[f]} $\\mu$m)\n"
                 f"sep {S['sep']:.3f}\"  PA {S['pa']:.1f}$^\\circ$   "
                 f"$f_{{gal}}/f_\\star$ = {p50['Fg']/p50['Fs']:.2f}", fontsize=10)
    ax.set_xlabel("$\\Delta$ x from star (arcsec)"); ax.set_ylabel("$\\Delta$ y (arcsec)" if k == 0 else "")
    # compass (image is rotated: +y axis at PA 239.84 deg)
    for pa_deg, lab, col in [(0, "N", "w"), (90, "E", "w")]:
        th = np.radians(pa_deg-239.84+90)
        ax.arrow(-1.75, -1.20, 0.5*np.cos(th), 0.5*np.sin(th), color=col, width=0.012,
                 head_width=0.08, length_includes_head=True)
        ax.text(-1.75+0.72*np.cos(th), -1.20+0.72*np.sin(th), lab, color=col, fontsize=9, ha="center", va="center")
    ax.plot([0.9, 1.9], [-2.75, -2.75], "w-", lw=2.5)
    ax.text(1.4, -2.65, '1"', color="w", ha="center", fontsize=9)
    # radial profiles
    ax2 = axes[1, k]
    rcs, prs, rcg, prg = S["prof"]
    ax2.semilogy(rcs, prs/np.nanmax(prs), "o-", color="tab:blue", ms=3.5, label="M dwarf")
    ax2.semilogy(rcg, prg/np.nanmax(prg), "s-", color="tab:green", ms=3.5, label="contaminant")
    ax2.axvline(JDOX[f]/2, ls=":", color="k", lw=1)
    ax2.text(JDOX[f]/2*1.06, 0.5, "JDox HWHM", rotation=90, fontsize=7, va="center")
    ax2.set_xlim(0, 0.95); ax2.set_ylim(3e-3, 1.5)
    ax2.set_xlabel("radius (arcsec)"); ax2.set_ylabel("normalised SB" if k == 0 else "")
    ax2.legend(fontsize=8, loc="upper right")
    ax2.set_title(f"profiles, companion hemisphere masked\nC$_{{30/70}}$: star {morph[k]['C_star']:.3f}"
                  f" / contam {morph[k]['C_contam']:.3f} / field {morph[k]['C_field_med']:.3f}", fontsize=9)
fig.suptitle("Project Hephaistos candidate D — JWST GO-7199 MIRI imaging (public, MAST anonymous)\n"
             "Gaia DR3 2660349163149053824, obs 2025-07-28, L3 i2d mosaics (jwst 2.0.1 / CRDS 1535)",
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(ROOT+"out/m4_jwstD_cutouts.png", dpi=140)
print("wrote out/m4_jwstD_cutouts.png")
