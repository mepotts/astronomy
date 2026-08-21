"""M4 final: deblended aperture photometry, separation/PA, FWHM, extendedness.

Positions : star = Gaia DR3 2660349163149053824 propagated to the JWST epoch;
            contaminant = quadratic centroid on its own peak.
Photometry: circular apertures at the CRDS EE30/EE50/EE70 radii (from the L3 _cat.ecsv
            aperture_params metadata, i.e. the JWST calibration reference files), local
            sky from a 3.0-4.5" annulus.  The encircled fraction inside each aperture is
            the CRDS value EE = 1/apcorr.  The cross-contamination ("leak") fraction of
            one source's light into the other's aperture is measured EMPIRICALLY from the
            wing profile of the brighter component of the pair, taken in the hemisphere
            pointing away from the fainter one.  A 2x2 linear system then gives the two
            total fluxes directly (no further aperture correction).
"""
import sys, warnings, pickle
sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import Cutout2D
from photutils.aperture import CircularAperture, aperture_photometry
from photutils.centroids import centroid_quadratic

ROOT = "c:/Users/matth/projects/astronomy/dyson-revet/"
RA16, DEC16, PMRA, PMDEC, PLX = 351.96372836, 5.10726195, -30.67371151, -21.61135431, 4.69567256
c16 = SkyCoord(ra=RA16*u.deg, dec=DEC16*u.deg, pm_ra_cosdec=PMRA*u.mas/u.yr,
               pm_dec=PMDEC*u.mas/u.yr, distance=(1000.0/PLX)*u.pc, obstime=Time("J2016.0"))
FILT = ["f560w", "f1000w", "f1500w"]
JDOX = {"f560w": 0.207, "f1000w": 0.328, "f1500w": 0.488}   # JDox MIRI imaging PSF FWHM (arcsec)
BRIGHTER = {"f560w": "star", "f1000w": "gal", "f1500w": "gal"}
ab = lambda jy: -2.5*np.log10(jy/3631.0) if jy > 0 else np.nan


def profile(img, cx, cy, scale, mask, rmax=2.2, dr=0.055):
    """azimuthal median surface-brightness profile (MJy/sr) restricted to `mask`."""
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    r = np.hypot(xx-cx, yy-cy)*scale
    b = np.arange(0, rmax+dr, dr); rc = 0.5*(b[1:]+b[:-1]); pr = np.full(len(rc), np.nan)
    for i in range(len(rc)):
        m = (r >= b[i]) & (r < b[i+1]) & np.isfinite(img) & mask
        if m.sum() >= 2:
            pr[i] = np.median(img[m])
    return rc, pr


def fwhm_of(rc, pr):
    ok = np.isfinite(pr)
    if ok.sum() < 4:
        return np.nan
    pk = np.nanmax(pr[:3]); half = pk/2.0
    k = np.where((pr < half) & ok)[0]
    k = k[k > 0]
    if len(k) == 0:
        return np.nan
    i = k[0]
    return 2*np.interp(half, [pr[i], pr[i-1]], [rc[i], rc[i-1]])


rows = []; summ = {}
for f in FILT:
    with fits.open(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits") as h:
        sci = h[1].data.astype(float); err = h[2].data.astype(float); w = WCS(h[1].header)
        scale = abs(h[1].header["CDELT1"])*3600.0
        pixar = h[1].header["PIXAR_SR"]
        t = Time(h[0].header["EXPSTART"], format="mjd")
    cat = ascii.read(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv")
    apm = cat.meta["aperture_params"]
    radii = np.asarray(apm["aperture_radii"], float)
    apcorr = np.asarray(apm["aperture_corrections"], float)
    EEc = 1.0/apcorr                       # CRDS encircled-energy fractions at those radii

    cobs = c16.apply_space_motion(new_obstime=t)
    xs, ys = [float(v) for v in w.world_to_pixel(cobs)]
    cut = Cutout2D(sci, (xs, ys), (121, 121), wcs=w, mode="strict")
    ecut = Cutout2D(err, (xs, ys), (121, 121), mode="strict")
    d = cut.data.copy(); e = ecut.data.copy()
    cxs, cys = cut.to_cutout_position((xs, ys))
    N = d.shape[0]; yy, xx = np.mgrid[:N, :N]
    rs = np.hypot(xx-cxs, yy-cys)*scale
    ann = (rs > 3.0) & (rs < 4.5)
    sky = np.median(d[ann]); skyrms = np.std(d[ann]); dz = d-sky

    ring = (rs > 0.5) & (rs < 2.2)
    iy, ix = np.unravel_index(np.argmax(np.where(ring, dz, -1e9)), dz.shape)
    cg = centroid_quadratic(dz, xpeak=ix, ypeak=iy, fit_boxsize=7)
    gx, gy = float(cg[0]), float(cg[1])
    scg = cut.wcs.pixel_to_world(gx, gy)
    sep = cobs.separation(scg).arcsec; pa = cobs.position_angle(scg).deg
    seppix = sep/scale

    # hemispheres pointing AWAY from the companion
    vgx, vgy = gx-cxs, gy-cys
    away_s = ((xx-cxs)*vgx + (yy-cys)*vgy) < 0
    away_g = ((xx-gx)*(-vgx) + (yy-gy)*(-vgy)) < 0

    print("\n" + "="*78)
    print(f"{f}  scale={scale:.5f} arcsec/pix  sky={sky:.4f}+-{skyrms:.4f} MJy/sr  epoch {t.decimalyear:.3f}")
    print(f"  star (Gaia-propagated) pix=({cxs:.3f},{cys:.3f})   contaminant pix=({gx:.3f},{gy:.3f})")
    print(f"  SEPARATION = {sep:.4f} arcsec   PA = {pa:.2f} deg   ({seppix:.3f} pix)")
    print(f"  CRDS EE radii (arcsec) = {(radii*scale).round(4)}   EE = {EEc.round(4)}")

    # ---------- empirical wing profile of the BRIGHTER component ----------
    if BRIGHTER[f] == "star":
        bx, by, bm = cxs, cys, away_s
    else:
        bx, by, bm = gx, gy, away_g
    rc, pr = profile(dz, bx, by, scale, bm)
    # normalise: total flux of that component from its own EE50 aperture
    apb = CircularAperture([(bx, by)], r=radii[1])
    Fb = float(aperture_photometry(dz, apb)["aperture_sum"][0])/EEc[1]
    prn = pr/Fb                                   # normalised SB per pixel-area unit
    # leak: integrate the normalised profile over an aperture of radius r centred at `sep`
    def leak(r_pix):
        gg = np.mgrid[-int(r_pix)-2:int(r_pix)+3, -int(r_pix)-2:int(r_pix)+3]
        dxp, dyp = gg[1], gg[0]
        inside = np.hypot(dxp, dyp) <= r_pix
        dd = np.hypot(dxp[inside]+seppix, dyp[inside])*scale
        v = np.interp(dd, rc[np.isfinite(prn)], prn[np.isfinite(prn)], left=np.nan, right=0.0)
        return float(np.nansum(v))
    print(f"  wing profile from the {BRIGHTER[f]} (away hemisphere); normalised SB at r=sep: "
          f"{np.interp(sep, rc[np.isfinite(prn)], prn[np.isfinite(prn)]):.3e} /pix")

    per = []
    for j, rp in enumerate(radii):
        L = leak(rp)
        A = np.array([[EEc[j], L], [L, EEc[j]]])
        aps = CircularAperture([(cxs, cys), (gx, gy)], r=rp)
        ph = aperture_photometry(dz, aps, error=e)
        m = np.array([float(ph["aperture_sum"][0]), float(ph["aperture_sum"][1])])
        me = np.array([float(ph["aperture_sum_err"][0]), float(ph["aperture_sum_err"][1])])
        Fs, Fg = np.linalg.solve(A, m)
        eF = np.abs(np.linalg.solve(A, me))
        # add a systematic from the leak model: 30% uncertainty on L
        dL = np.abs(np.linalg.solve(np.array([[EEc[j], 1.3*L], [1.3*L, EEc[j]]]), m) - np.array([Fs, Fg]))
        Jy = lambda v: v*pixar*1e6
        per.append(dict(r_pix=rp, r_arcsec=rp*scale, ee=EEc[j], apcorr=apcorr[j], leak=L,
                        raw_s=m[0], raw_g=m[1], Fs=Fs, Fg=Fg,
                        Jy_s=Jy(Fs), Jy_g=Jy(Fg),
                        Jy_s_e=Jy(np.hypot(eF[0], dL[0])), Jy_g_e=Jy(np.hypot(eF[1], dL[1]))))
        print(f"   r={rp*scale:.4f}\" EE={EEc[j]:.4f} leak={L:.5f} | raw s={m[0]:9.2f} g={m[1]:9.2f}"
              f" -> total s={Fs:9.2f} g={Fg:9.2f}   g/s={Fg/Fs:8.3f}"
              f"   [s={Jy(Fs)*1e6:8.2f} uJy AB {ab(Jy(Fs)):.2f} | g={Jy(Fg)*1e6:9.2f} uJy AB {ab(Jy(Fg)):.2f}]")

    rat = np.array([p["Fg"]/p["Fs"] for p in per])
    print(f"  contrast g/s (EE30,EE50,EE70) = {rat.round(3)}")

    # ---------- FWHM ----------
    rcs, prs = profile(dz, cxs, cys, scale, away_s, rmax=1.0, dr=0.0555)
    rcg, prg = profile(dz, gx, gy, scale, away_g, rmax=1.0, dr=0.0555)
    fs, fg = fwhm_of(rcs, prs), fwhm_of(rcg, prg)
    print(f"  FWHM(away-hemisphere azimuthal): star={fs:.3f}\"  contaminant={fg:.3f}\"  | JDox point source {JDOX[f]}\"")

    summ[f] = dict(sep=sep, pa=pa, scale=scale, sky=sky, skyrms=skyrms, per=per,
                   fwhm_s=fs, fwhm_g=fg, jdox=JDOX[f], epoch=float(t.decimalyear),
                   star_pix=(cxs, cys), gal_pix=(gx, gy),
                   gal_sky=(float(scg.ra.deg), float(scg.dec.deg)),
                   gaia_sky=(float(cobs.ra.deg), float(cobs.dec.deg)),
                   pixar=pixar, cutout=dz, prof=(rcs, prs, rcg, prg), radii=radii, EEc=EEc)
    for p in per:
        r = p["Fg"]/p["Fs"]
        rows.append(dict(filter=f.upper(), ee_aperture=f"EE{int(round(p['ee']*100))}",
                         r_arcsec=round(p["r_arcsec"], 4), crds_ee=round(p["ee"], 4),
                         crds_apcorr=round(p["apcorr"], 4), leak_frac=round(p["leak"], 5),
                         star_flux_uJy=round(p["Jy_s"]*1e6, 3), star_flux_err_uJy=round(p["Jy_s_e"]*1e6, 3),
                         gal_flux_uJy=round(p["Jy_g"]*1e6, 3), gal_flux_err_uJy=round(p["Jy_g_e"]*1e6, 3),
                         star_ABmag=round(ab(p["Jy_s"]), 3), gal_ABmag=round(ab(p["Jy_g"]), 3),
                         ratio_gal_over_star=round(r, 4),
                         dmag_gal_minus_star=round(-2.5*np.log10(r), 3) if r > 0 else np.nan,
                         sep_arcsec=round(sep, 4), PA_deg=round(pa, 2),
                         fwhm_star_arcsec=round(fs, 4) if np.isfinite(fs) else np.nan,
                         fwhm_gal_arcsec=round(fg, 4) if np.isfinite(fg) else np.nan,
                         fwhm_jdox_arcsec=JDOX[f],
                         sky_MJysr=round(sky, 4), skyrms_MJysr=round(skyrms, 4),
                         epoch_dyr=round(t.decimalyear, 4)))

pd.DataFrame(rows).to_csv(ROOT+"out/m4_jwstD_photometry.csv", index=False)
pickle.dump(summ, open(ROOT+"data/jwst/m4_summ.pkl", "wb"))
print("\nwrote out/m4_jwstD_photometry.csv")
s = np.array([summ[f]["sep"] for f in FILT]); p = np.array([summ[f]["pa"] for f in FILT])
print(f"\nSEPARATION: {s.round(4)}  mean {s.mean():.4f} sd {s.std(ddof=1):.4f} arcsec")
print(f"PA        : {p.round(2)}  mean {p.mean():.2f} sd {p.std(ddof=1):.2f} deg")
print("\n--- comparison with Hephaistos IV Table 2 (AB mag) ---")
PAP = {"f560w": (17.5, 18.7), "f1000w": (18.5, 16.6), "f1500w": (None, 14.9)}
for f in FILT:
    p50 = summ[f]["per"][1]
    print(f"  {f:7s} star: mine {ab(p50['Jy_s']):6.2f}  paper {PAP[f][0]}   |  "
          f"galaxy: mine {ab(p50['Jy_g']):6.2f}  paper {PAP[f][1]}")
