"""M7 PR-1: an EMPIRICAL PSF for candidate D's MRS cubes, built from the cubes.

M6 Sec 2.2 failed PR-2's acceptance test 4 of 6, and the failure was
structured: in every band the DOMINANT member of the 1.23 arcsec pair passed
and only the SUB-DOMINANT one failed.  That is the signature of PSF-wing
leakage -- a parametric Gaussian has no wings, so the bright component's real
wings get assigned to the faint component.  M6 Sec 2.5 named the fix and it
needs no new data: each component overwhelmingly dominates the light in SOME
sub-band of the cubes already on disk (the star ~8:1 in Ch1-short, the
contaminant ~40:1 in Ch4), so a wing-carrying PSF can be measured from the
data themselves.

    python scripts/m7_mrs_epsf.py build   --label D --assoc o002
    python scripts/m7_mrs_epsf.py inject  --label D --assoc o002

The extracted spectra are written with the SCHEMA AND FILENAME the M6 grading
code already reads, so M6 PR-2's acceptance test and every downstream test run
through BYTE-IDENTICAL code:

    python scripts/m6_mrs_redshift.py --label D_epsf

METHOD (M7 PR-1, fixed before the run).

* DONOR RULE.  Per sub-band the donor is the component nearer the white-light
  peak; its dominance is measured MODEL-FREE as a background-subtracted
  aperture ratio at r = 0.5 FWHM.  ro_ap >= 3 makes it a donor sub-band.
* CONSTRUCTION.  8 lambda bins per sub-band; slices median-combined; 4
  iterations of {subtract the non-donor model -> median radial profile about
  the donor's FIXED position -> normalise with a fitted power-law tail ->
  re-solve the three linear amplitudes}.  Positions stay fixed at M6 PR-2's
  values.  The plate offset is MEASURED from the donor's centroid in a 3-pixel
  box, HARD-BOUNDED at +-1.0 pixel -- M6's Ch4-long grid search railed at both
  edges of its +-1.5 pixel grid and returned a ratio of 0.86 where its
  neighbour returns 33.5.
* THE PROFILE LIVES ON A SCALED RADIUS u = r_arcsec / FWHM_JDox(lambda), so it
  is the PSF SHAPE with the known instrumental FWHM law divided out; that
  makes it interpolable across a sub-band and directly comparable between the
  star-derived and contaminant-derived profiles.
* VALIDATION.  (a) star-derived vs contaminant-derived encircled energy;
  (b) a 2x2 injection-recovery on synthetic scenes -- inject with the Gaussian
  or the empirical PSF, recover with each -- which prices both the leakage and
  the circularity of injecting and recovering with the same profile.
* THE ACCEPTANCE TEST IS M6 PR-2's, VERBATIM.  Same reference fluxes, same
  +-30%, same six comparisons, PASS requires 6 of 6.  It is not run here; it is
  run by the unmodified M6 script on this script's output.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
MRS = ROOT / "data" / "jwst" / "mrs"

from m6_mrs_reduce import (GAIA_EPOCH, PA_DEG, PROGRAM, SEP_AS,  # noqa: E402
                           mrs_fwhm, propagate, target_astrometry)

NBIN = 8                 # lambda bins per sub-band (each <~3% in lambda)
NITER = 4                # EPSF iterations
DONOR_RHO = 3.0          # model-free aperture ratio that makes a donor sub-band
OFFSET_BOUND = 1.0       # pixels; PR-1's hard bound on the plate offset
U_MAX = 8.0              # scaled-radius grid ceiling, in FWHM units
NU = 160                 # scaled-radius grid points
D_TEL = 6.5              # m, JWST primary (for the declared lambda/D report)
INJ_F = (0.01, 0.02, 0.05, 0.10, 0.30)


def ugrid() -> np.ndarray:
    return np.linspace(0.0, U_MAX, NU)


# ------------------------------------------------------------- geometry ----
def positions(hdr_sci, hdr_pri, tg):
    """Fixed positions: Gaia propagated to EXPSTART, plus M4 Sec 5's offset."""
    from astropy.wcs import WCS
    w = WCS(hdr_sci)
    mjd = float(hdr_pri.get("EXPSTART", hdr_pri.get("MJD-BEG", np.nan)))
    ra, dec = propagate(tg, mjd)
    dra = SEP_AS * np.sin(np.radians(PA_DEG)) / 3600.0 / np.cos(np.radians(dec))
    ddec = SEP_AS * np.cos(np.radians(PA_DEG)) / 3600.0
    xs, ys = [float(v) for v in w.celestial.all_world2pix(ra, dec, 0)]
    xc, yc = [float(v) for v in w.celestial.all_world2pix(ra + dra, dec + ddec, 0)]
    # the injection position: same separation, PA + 90 deg, used NOWHERE in the
    # PSF construction (PR-1)
    dra2 = SEP_AS * np.sin(np.radians(PA_DEG + 90)) / 3600.0 / np.cos(np.radians(dec))
    ddec2 = SEP_AS * np.cos(np.radians(PA_DEG + 90)) / 3600.0
    xi, yi = [float(v) for v in w.celestial.all_world2pix(ra + dra2, dec + ddec2, 0)]
    return (xs, ys), (xc, yc), (xi, yi), mjd


def centroid_offset(img, x0, y0, half=3):
    """Flux-weighted centroid in a box, minus the predicted position.

    PR-1: the plate offset is measured, not grid-searched, and hard-bounded at
    +-OFFSET_BOUND pixels.  Returns (dx, dy, hit_bound).
    """
    ny, nx = img.shape
    i0, i1 = max(int(round(y0)) - half, 0), min(int(round(y0)) + half + 1, ny)
    j0, j1 = max(int(round(x0)) - half, 0), min(int(round(x0)) + half + 1, nx)
    sub = img[i0:i1, j0:j1]
    if sub.size < 9 or not np.isfinite(sub).any():
        return 0.0, 0.0, False
    v = np.where(np.isfinite(sub), sub, np.nan)
    v = v - np.nanmedian(v)
    v = np.clip(np.nan_to_num(v), 0, None)
    if v.sum() <= 0:
        return 0.0, 0.0, False
    yy, xx = np.mgrid[i0:i1, j0:j1]
    dx = float((v * xx).sum() / v.sum() - x0)
    dy = float((v * yy).sum() / v.sum() - y0)
    hit = bool(abs(dx) >= OFFSET_BOUND or abs(dy) >= OFFSET_BOUND)
    return (float(np.clip(dx, -OFFSET_BOUND, OFFSET_BOUND)),
            float(np.clip(dy, -OFFSET_BOUND, OFFSET_BOUND)), hit)


def aperture_flux(img, x0, y0, rad):
    ny, nx = img.shape
    yy, xx = np.mgrid[:ny, :nx]
    r = np.hypot(xx - x0, yy - y0)
    m = (r <= rad) & np.isfinite(img)
    bg = (r > 3 * rad) & (r <= 5 * rad) & np.isfinite(img)
    if m.sum() < 3:
        return np.nan
    b = np.nanmedian(img[bg]) if bg.sum() > 5 else 0.0
    return float(np.sum(img[m] - b))


# --------------------------------------------------------------- profile ---
def eval_profile(u_prof, p_prof, r_pix, fwhm_pix):
    """Evaluate a SCALE-FREE profile at pixel radii.

    Profiles are stored normalised on the scaled radius u = r/FWHM, i.e. with
    `int p 2 pi u du = 1`.  The integral over the PIXEL plane is therefore
    FWHM^2 times that, so the conversion to a unit-flux model image divides by
    FWHM^2 here.  Storing the shape scale-free and applying the scaling at
    evaluation is what keeps the normalisation exact when a profile measured in
    one lambda bin is evaluated at another bin's FWHM -- doing it the other way
    round leaves a systematic of order 2 x (dFWHM/FWHM) across each sub-band.
    """
    f = max(float(fwhm_pix), 1e-6)
    u = r_pix / f
    return np.interp(u, u_prof, p_prof, left=p_prof[0], right=0.0) / f ** 2


def normalise(u, v, fwhm_pix=1.0, tail_lo=0.66, u_min_ok=1.5):
    """Normalise a raw radial profile to unit integral over the pixel plane.

    PR-1's rule, with "the measured range" made explicit: the profile is
    measured out to the FIRST radial bin whose median is non-positive -- beyond
    that the PSF is not detected and what is there is background, which
    multiplied by 2*pi*r would dominate the integral.  The measured range is
    integrated numerically; beyond it a power law fitted to the outer third of
    THAT range is integrated analytically.  The truncation radius and the
    tail's fractional contribution are both returned and reported, because a
    large tail is a caveat on the absolute flux scale rather than a detail.
    """
    r = u * fwhm_pix                       # scale-free when fwhm_pix = 1
    v = np.where(np.isfinite(v), v, 0.0).astype(float)
    pos = v > 0
    if not pos.any():
        return None, np.nan, np.nan, np.nan
    first_bad = np.argmax(~pos & (u > 0.5)) if (~pos & (u > 0.5)).any() else len(u)
    ncut = max(int(first_bad), 5)
    if u[ncut - 1] < u_min_ok:             # too little of the PSF is detected
        return None, np.nan, np.nan, float(u[ncut - 1])
    vv = v.copy()
    vv[ncut:] = 0.0
    core = float(np.trapezoid(vv[:ncut] * 2 * np.pi * r[:ncut], r[:ncut]))
    # power-law tail from the outer third of the measured range
    ulo = tail_lo * u[ncut - 1]
    sel = (u[:ncut] >= ulo) & (vv[:ncut] > 0) & (u[:ncut] > 0)
    tail, slope = 0.0, np.nan
    if sel.sum() >= 4:
        s, b = np.polyfit(np.log10(r[:ncut][sel]), np.log10(vv[:ncut][sel]), 1)
        slope = float(s)
        if s < -2.0:
            vend = 10 ** (b + s * np.log10(r[ncut - 1]))
            tail = float(2 * np.pi * vend * r[ncut - 1] ** 2 / (-s - 2.0))
    tot = core + tail
    if not np.isfinite(tot) or tot <= 0:
        return None, np.nan, np.nan, float(u[ncut - 1])
    return vv / tot, float(tail / tot), slope, float(u[ncut - 1])


def radial_median(img, wgt, x0, y0, fwhm_pix, rmax_pix, step=0.25):
    """Median radial profile on the scaled grid u = r / FWHM."""
    ny, nx = img.shape
    yy, xx = np.mgrid[:ny, :nx]
    r = np.hypot(xx - x0, yy - y0)
    good = np.isfinite(img) & (wgt > 0) & (r <= rmax_pix)
    if good.sum() < 30:
        return None
    u = r[good] / fwhm_pix
    val = img[good]
    edges = np.arange(0.0, rmax_pix / fwhm_pix + step, step)
    cen = 0.5 * (edges[:-1] + edges[1:])
    prof = np.full(len(cen), np.nan)
    for k in range(len(cen)):
        m = (u >= edges[k]) & (u < edges[k + 1])
        if m.sum() >= 3:
            prof[k] = np.median(val[m])
        elif m.sum() >= 1:
            prof[k] = np.mean(val[m])
    ok = np.isfinite(prof)
    if ok.sum() < 5:
        return None
    return np.interp(ugrid(), cen[ok], prof[ok],
                     left=prof[ok][0], right=0.0)


def solve3(img, wgt, pa, pb):
    """Weighted linear solve for (A_a, A_b, background)."""
    good = np.isfinite(img) & np.isfinite(wgt) & (wgt > 0)
    if good.sum() < 30:
        return (np.nan,) * 5
    w = np.sqrt(wgt[good])
    A = np.column_stack([pa[good] * w, pb[good] * w, w])
    y = img[good] * w
    try:
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    except np.linalg.LinAlgError:
        return (np.nan,) * 5
    resid = y - A @ coef
    chi = float(np.sqrt(np.mean(resid ** 2)))
    try:
        cov = np.linalg.inv(A.T @ A)
        ea, eb = float(np.sqrt(cov[0, 0])), float(np.sqrt(cov[1, 1]))
    except np.linalg.LinAlgError:
        ea = eb = np.nan
    return float(coef[0]), float(coef[1]), float(coef[2]), chi, (ea, eb)


def gauss_profile(fwhm_pix):
    """M6's parametric profile on the same normalised grid, for comparison."""
    u = ugrid()
    sig_u = 1.0 / 2.3548          # unit FWHM on the scaled-radius grid
    v = np.exp(-0.5 * (u / sig_u) ** 2)
    p, tail, slope, ucut = normalise(u, v)
    return p


# ----------------------------------------------------------------- build ---
def cmd_build(a) -> None:
    from astropy.io import fits
    tg = target_astrometry(a.label)
    cubes = sorted(MRS.glob("jw%05d-%s*_s3d.fits" % (int(PROGRAM), a.assoc)))
    if not cubes:
        raise SystemExit("no cubes for assoc " + a.assoc)
    u = ugrid()
    rows, meta, psfs, diag = [], [], {}, []
    for cf in cubes:
        with fits.open(cf) as hd:
            h0, h1 = hd[0].header, hd["SCI"].header
            cube = hd["SCI"].data.astype(float)
            err = (hd["ERR"].data.astype(float) if "ERR" in hd
                   else np.ones_like(cube))
            band = "%s-%s" % (h0.get("CHANNEL", "?"),
                              str(h0.get("BAND", "?")).lower())
            (xs0, ys0), (xc0, yc0), (xi0, yi0), mjd = positions(h1, h0, tg)
            nz = cube.shape[0]
            lam = h1["CRVAL3"] + (np.arange(nz) + 1 - h1["CRPIX3"]) * h1["CDELT3"]
            if h1["CDELT3"] < 1e-5:
                lam = lam * 1e6
            scale = abs(h1["CDELT1"]) * 3600.0
            sr_pix = ((abs(h1["CDELT1"]) * np.pi / 180)
                      * (abs(h1["CDELT2"]) * np.pi / 180))
            sep_pix = float(np.hypot(xc0 - xs0, yc0 - ys0))
            white = np.nanmedian(cube, axis=0)
            fw_med = float(np.nanmedian(mrs_fwhm(lam))) / scale     # pixels

            # ---- donor rule: nearer the white-light peak, ro_ap model-free --
            fin = np.isfinite(white)
            pk = np.unravel_index(np.nanargmax(np.where(fin, white, -np.inf)),
                                  white.shape)
            d_star = np.hypot(pk[1] - xs0, pk[0] - ys0)
            d_con = np.hypot(pk[1] - xc0, pk[0] - yc0)
            donor = "star" if d_star < d_con else "con"
            f_star = aperture_flux(white, xs0, ys0, 0.5 * fw_med)
            f_con = aperture_flux(white, xc0, yc0, 0.5 * fw_med)
            rho_ap = (f_star / f_con if donor == "star" else f_con / f_star)
            is_donor = bool(np.isfinite(rho_ap) and rho_ap >= DONOR_RHO)

            # ---- plate offset: measured from the donor's centroid, bounded --
            dx, dy, hit = centroid_offset(
                white, xs0 if donor == "star" else xc0,
                ys0 if donor == "star" else yc0)
            xs, ys, xc, yc = xs0 + dx, ys0 + dy, xc0 + dx, yc0 + dy
            xi, yi = xi0 + dx, yi0 + dy

            # ---- fit region: finite pixels near the pair midpoint -----------
            mx, my = 0.5 * (xs + xc), 0.5 * (ys + yc)
            ny_, nx_ = white.shape
            yy, xx = np.mgrid[:ny_, :nx_]
            rfit = max(4.0 * fw_med, 2.0 * sep_pix)
            region = np.hypot(xx - mx, yy - my) <= rfit
            r_s = np.hypot(xx - xs, yy - ys)
            r_c = np.hypot(xx - xc, yy - yc)
            r_i = np.hypot(xx - xi, yy - yi)
            rmax_pix = float(np.nanpercentile(
                (r_s if donor == "star" else r_c)[region & fin], 92))

            # ---- lambda bins ----------------------------------------------
            edges = np.linspace(0, nz, NBIN + 1).astype(int)
            band_psf = []
            for k in range(NBIN):
                sl = slice(edges[k], edges[k + 1])
                if edges[k + 1] - edges[k] < 5:
                    continue
                img = np.nanmedian(cube[sl], axis=0)
                n_s = max(int(edges[k + 1] - edges[k]), 1)
                sig = np.nanmedian(err[sl], axis=0) * 1.253 / np.sqrt(n_s)
                wgt = np.where(np.isfinite(sig) & (sig > 0) & region & fin,
                               1.0 / sig ** 2, 0.0)
                lam_k = float(np.median(lam[sl]))
                fw_k = float(mrs_fwhm(lam_k)) / scale          # pixels
                p = gauss_profile(fw_k)
                tail = slope = ucut = np.nan
                As = Ac = np.nan
                for it in range(NITER):
                    ps = eval_profile(u, p, r_s, fw_k)
                    pc = eval_profile(u, p, r_c, fw_k)
                    As, Ac, B, chi, (eas, eac) = solve3(img, wgt, ps, pc)
                    if not np.isfinite(As) or not np.isfinite(Ac):
                        break
                    if it == NITER - 1:
                        break
                    # subtract the NON-donor and the background; what is left
                    # is the donor's own PSF
                    if donor == "star":
                        resid = img - Ac * pc - B
                        x0, y0 = xs, ys
                    else:
                        resid = img - As * ps - B
                        x0, y0 = xc, yc
                    v = radial_median(resid, wgt, x0, y0, fw_k, rmax_pix)
                    if v is None:
                        break
                    pn, tail, slope, ucut = normalise(u, v)
                    if pn is None:
                        break
                    p = pn
                band_psf.append({"lam_um": lam_k, "fwhm_pix": fw_k,
                                 "prof": p.copy(), "tail_frac": tail,
                                 "tail_slope": slope, "n_slices": n_s,
                                 "u_cut": ucut})
            if not band_psf:
                raise SystemExit("no usable lambda bin in " + band)
            psfs[band] = {"donor": donor, "is_donor": is_donor,
                          "rho_ap": float(rho_ap), "scale_as": scale,
                          "bins": band_psf}
            diag.append({"band": band, "donor": donor, "rho_ap": float(rho_ap),
                         "is_donor": is_donor, "dx_pix": dx, "dy_pix": dy,
                         "offset_hit_bound": hit, "sep_pix": sep_pix,
                         "rfit_pix": float(rfit), "rmax_pix": rmax_pix,
                         "rmax_fwhm": float(rmax_pix / fw_med),
                         "tail_frac_med": float(np.nanmedian(
                             [b["tail_frac"] for b in band_psf])),
                         "tail_slope_med": float(np.nanmedian(
                             [b["tail_slope"] for b in band_psf])),
                         "u_cut_med_fwhm": float(np.nanmedian(
                             [b.get("u_cut", np.nan) for b in band_psf])),
                         "d_peak_star_pix": float(d_star),
                         "d_peak_con_pix": float(d_con)})
            print("  %-12s donor=%-4s rho_ap=%6.1f %-9s dx,dy=%+.2f,%+.2f%s  "
                  "rmax=%.1f ucut=%.1f FWHM  tail=%.3f (slope %.2f)"
                  % (band, donor, rho_ap, "DONOR" if is_donor else "(borrows)",
                     dx, dy, " BOUND" if hit else "", rmax_pix / fw_med,
                     np.nanmedian([b.get("u_cut", np.nan) for b in band_psf]),
                     np.nanmedian([b["tail_frac"] for b in band_psf]),
                     np.nanmedian([b["tail_slope"] for b in band_psf])))

            meta.append({"file": cf.name, "band": band,
                         "cal_ver": h0.get("CAL_VER"),
                         "crds_ctx": h0.get("CRDS_CTX"),
                         "crds_ver": h0.get("CRDS_VER"), "s_region_ok": True,
                         "expstart": mjd, "nz": int(nz),
                         "lam_min": float(lam.min()), "lam_max": float(lam.max()),
                         "scale_as": scale, "nx": int(cube.shape[2]),
                         "ny": int(cube.shape[1]), "dx_pix": dx, "dy_pix": dy,
                         "psf_k": np.nan, "psf_beta": "empirical",
                         "psf_fwhm_as": float(np.nanmedian(mrs_fwhm(lam))),
                         "sep_pix": sep_pix, "date_obs": h0.get("DATE-OBS"),
                         "targname": h0.get("TARGNAME"),
                         "bunit": h1.get("BUNIT"), "donor": donor,
                         "rho_ap": float(rho_ap), "is_donor_subband": is_donor,
                         "rmax_fwhm": float(rmax_pix / fw_med)})

            # ---- per-slice extraction with the empirical PSF ---------------
            lam_bins = np.array([b["lam_um"] for b in band_psf])
            prof_stack = np.array([b["prof"] for b in band_psf])
            for kz in range(nz):
                im = cube[kz]
                if not np.isfinite(im).any():
                    continue
                sg = err[kz]
                wg = np.where(np.isfinite(sg) & (sg > 0) & region & fin,
                              1.0 / sg ** 2, 0.0)
                fw_z = float(mrs_fwhm(lam[kz])) / scale
                j = int(np.argmin(np.abs(lam_bins - lam[kz])))
                if len(lam_bins) > 1:
                    # linear interpolation of the profile between bins
                    jj = np.clip(np.searchsorted(lam_bins, lam[kz]) - 1,
                                 0, len(lam_bins) - 2)
                    t = np.clip((lam[kz] - lam_bins[jj])
                                / max(lam_bins[jj + 1] - lam_bins[jj], 1e-9),
                                0.0, 1.0)
                    p = (1 - t) * prof_stack[jj] + t * prof_stack[jj + 1]
                else:
                    p = prof_stack[j]
                ps = eval_profile(u, p, r_s, fw_z)
                pc = eval_profile(u, p, r_c, fw_z)
                As, Ac, B, chi, (eas, eac) = solve3(im, wg, ps, pc)
                rows.append({"band": band, "lam_um": float(lam[kz]),
                             "f_star_jy": As * sr_pix * 1e6,
                             "f_con_jy": Ac * sr_pix * 1e6,
                             "e_con_jy": eac * sr_pix * 1e6,
                             "bkg_mjysr": B, "resid_rms": chi,
                             "sr_pix": sr_pix, "scale_as": scale})

    lab = a.label + "_epsf"
    df = pd.DataFrame(rows).sort_values("lam_um").reset_index(drop=True)
    df.to_csv(OUT / ("m6_mrs_%s_spectra.csv" % lab), index=False)
    pd.DataFrame(meta).to_csv(OUT / ("m6_mrs_%s_cubes.csv" % lab), index=False)
    pd.DataFrame(diag).to_csv(OUT / "m7_epsf_diagnostics.csv", index=False)

    # ---- the profiles themselves, and the star-vs-contaminant check --------
    prow = []
    for band, d in psfs.items():
        for b in d["bins"]:
            prow.append({"band": band, "donor": d["donor"],
                         "is_donor": d["is_donor"], "lam_um": b["lam_um"],
                         "tail_frac": b["tail_frac"],
                         "tail_slope": b["tail_slope"],
                         **{("p%03d" % i): float(b["prof"][i])
                            for i in range(0, NU, 2)}})
    pd.DataFrame(prow).to_csv(OUT / "m7_epsf_profiles.csv", index=False)

    def ee(prof, fwhm_pix, u_at):
        r = ugrid()                       # profiles are scale-free
        c = np.concatenate([[0.0], np.cumsum(
            0.5 * (prof[1:] * 2 * np.pi * r[1:] + prof[:-1] * 2 * np.pi * r[:-1])
            * np.diff(r))])
        return float(np.interp(u_at, ugrid(), c))

    check = {"declared": "PR-1's star-derived vs contaminant-derived profile"}
    star_bands = [b for b, d in psfs.items()
                  if d["donor"] == "star" and d["is_donor"]]
    con_bands = [b for b, d in psfs.items()
                 if d["donor"] == "con" and d["is_donor"]]
    check["star_donor_subbands"] = star_bands
    check["contaminant_donor_subbands"] = con_bands
    for who, bl in (("star", star_bands), ("contaminant", con_bands)):
        ees, lds = [], []
        for b in bl:
            for bb in psfs[b]["bins"]:
                for uu in (1.0, 2.0, 3.0):
                    ees.append((uu, ee(bb["prof"], bb["fwhm_pix"], uu)))
                # the DECLARED lambda/D report
                ld_as = bb["lam_um"] * 1e-6 / D_TEL * 206265.0
                fw_as = bb["fwhm_pix"] * psfs[b]["scale_as"]
                for nn in (2.0, 4.0, 6.0):
                    lds.append((nn, ee(bb["prof"], bb["fwhm_pix"],
                                       nn * ld_as / fw_as)))
        check["ee_at_%s_FWHM" % who] = {
            str(uu): float(np.median([v for u_, v in ees if u_ == uu]))
            for uu in (1.0, 2.0, 3.0)} if ees else {}
        check["ee_at_%s_lambda_over_D" % who] = {
            str(nn): float(np.median([v for n_, v in lds if n_ == nn]))
            for nn in (2.0, 4.0, 6.0)} if lds else {}
    a1 = check.get("ee_at_star_FWHM", {})
    a2 = check.get("ee_at_contaminant_FWHM", {})
    if a1 and a2:
        check["contaminant_minus_star_EE_at_2FWHM"] = float(a2["2.0"] - a1["2.0"])
        check["contaminant_broader"] = bool(a2["2.0"] < a1["2.0"])
        check["note"] = (
            "encircled energy at 2 FWHM: a SMALLER value for the contaminant "
            "means its light is spread wider than the star's, i.e. it is "
            "either spatially resolved or the profile carries a PSF error. "
            "The primary extraction adopts the DONOR-derived profile per "
            "sub-band (PR-1); the star-scaled variant is a declared "
            "sensitivity.")
    (OUT / "m7_epsf_psf_check.json").write_text(
        json.dumps(check, indent=2, default=str))
    np.save(OUT / "m7_epsf_stack.npy",
            np.array([b["prof"] for d in psfs.values() for b in d["bins"]]))
    with open(OUT / "m7_epsf_psfs.json", "w") as fh:
        json.dump({b: {"donor": d["donor"], "is_donor": d["is_donor"],
                       "rho_ap": d["rho_ap"], "scale_as": d["scale_as"],
                       "bins": [{"lam_um": x["lam_um"],
                                 "fwhm_pix": x["fwhm_pix"],
                                 "tail_frac": x["tail_frac"],
                                 "u_cut": x.get("u_cut"),
                                 "prof": list(map(float, x["prof"]))}
                                for x in d["bins"]]}
                   for b, d in psfs.items()}, fh)
    print("\n%d slices -> out/m6_mrs_%s_spectra.csv" % (len(df), lab))
    print("PSF check:", json.dumps(
        {k: v for k, v in check.items() if k.startswith("ee_at")
         or k.startswith("contaminant_")}, indent=2))
    print("\nNow run the UNCHANGED M6 grader:")
    print("  python scripts/m6_mrs_redshift.py --label %s" % lab)


# ---------------------------------------------------------------- inject ---
def cmd_inject(a) -> None:
    """PR-1's 2x2 injection-recovery: does the deblend recover a KNOWN ratio?"""
    from astropy.io import fits
    tg = target_astrometry(a.label)
    psfs = json.load(open(OUT / "m7_epsf_psfs.json"))
    u = ugrid()
    rng = np.random.default_rng(20260825)
    rows = []
    for cf in sorted(MRS.glob("jw%05d-%s*_s3d.fits" % (int(PROGRAM), a.assoc))):
        with fits.open(cf) as hd:
            h0, h1 = hd[0].header, hd["SCI"].header
            cube = hd["SCI"].data.astype(float)
            err = (hd["ERR"].data.astype(float) if "ERR" in hd
                   else np.ones_like(cube))
            band = "%s-%s" % (h0.get("CHANNEL", "?"),
                              str(h0.get("BAND", "?")).lower())
            if band not in psfs or not psfs[band]["is_donor"]:
                continue
            (xs0, ys0), (xc0, yc0), (xi0, yi0), _ = positions(h1, h0, tg)
            scale = abs(h1["CDELT1"]) * 3600.0
            nz = cube.shape[0]
            lam = h1["CRVAL3"] + (np.arange(nz) + 1 - h1["CRPIX3"]) * h1["CDELT3"]
            if h1["CDELT3"] < 1e-5:
                lam = lam * 1e6
            white = np.nanmedian(cube, axis=0)
            fin = np.isfinite(white)
            donor = psfs[band]["donor"]
            xd, yd = (xs0, ys0) if donor == "star" else (xc0, yc0)
            dx, dy, _ = centroid_offset(white, xd, yd)
            xd, yd, xi, yi = xd + dx, yd + dy, xi0 + dx, yi0 + dy
            sep_pix = float(np.hypot(xc0 - xs0, yc0 - ys0))
            ny_, nx_ = white.shape
            yy, xx = np.mgrid[:ny_, :nx_]
            b0 = psfs[band]["bins"][len(psfs[band]["bins"]) // 2]
            fw = b0["fwhm_pix"]
            pe = np.asarray(b0["prof"], float)
            pg = gauss_profile(fw)
            mx, my = 0.5 * (xd + xi), 0.5 * (yd + yi)
            region = np.hypot(xx - mx, yy - my) <= max(4.0 * fw, 2.0 * sep_pix)
            r_d = np.hypot(xx - xd, yy - yd)
            r_i = np.hypot(xx - xi, yy - yi)
            noise = float(np.nanmedian(np.nanmedian(err, axis=0)[region & fin]))
            amp = float(np.nansum(white[region & fin])) / 1.0
            for f in INJ_F:
                for pin, nin in ((pg, "gauss"), (pe, "epsf")):
                    scene = (amp * eval_profile(u, pin, r_d, fw)
                             + f * amp * eval_profile(u, pin, r_i, fw))
                    scene = np.where(region & fin, scene, np.nan)
                    scene = scene + rng.normal(0.0, noise, scene.shape)
                    wg = np.where(np.isfinite(scene) & region & fin,
                                  1.0 / noise ** 2, 0.0)
                    for pre, nre in ((pg, "gauss"), (pe, "epsf")):
                        pd_, pi_ = (eval_profile(u, pre, r_d, fw),
                                    eval_profile(u, pre, r_i, fw))
                        Ad, Ai, B, chi, _ = solve3(scene, wg, pd_, pi_)
                        rows.append({"band": band, "donor": donor,
                                     "f_true": f, "inject_psf": nin,
                                     "recover_psf": nre,
                                     "f_rec": (Ai / Ad) if Ad else np.nan,
                                     "ratio": ((Ai / Ad) / f) if Ad and f
                                     else np.nan, "lam_um": b0["lam_um"]})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "m7_epsf_injection.csv", index=False)
    piv = t.groupby(["inject_psf", "recover_psf", "f_true"])["ratio"].median()
    print("PR-1 INJECTION-RECOVERY 2x2  (recovered/true flux ratio; 1.00 = "
          "unbiased)\n")
    print(piv.unstack("f_true").round(3).to_string())
    summ = t.groupby(["inject_psf", "recover_psf"])["ratio"].agg(
        ["median", "mean", "std", "count"])
    print("\n" + summ.round(3).to_string())
    (OUT / "m7_epsf_injection.json").write_text(json.dumps(
        {"by_f": json.loads(piv.reset_index().to_json(orient="records")),
         "summary": json.loads(summ.reset_index().to_json(orient="records")),
         "f_grid": list(INJ_F),
         "note": "synthetic scenes: donor + a companion of KNOWN fraction f at "
                 "the same 1.233 arcsec separation but PA+90 deg, a position "
                 "used nowhere in the PSF construction.  The gauss/gauss cell "
                 "grades M6's method against a known truth; the off-diagonal "
                 "cells price the circularity of injecting and recovering with "
                 "the same profile."}, indent=2))
    print("-> out/m7_epsf_injection.{csv,json}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "inject"):
        p = sub.add_parser(name)
        p.add_argument("--label", default="D")
        p.add_argument("--assoc", default="o002")
    a = ap.parse_args()
    {"build": cmd_build, "inject": cmd_inject}[a.cmd](a)


if __name__ == "__main__":
    main()
