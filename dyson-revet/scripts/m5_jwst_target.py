"""M5: the parameterised JWST/MIRI chain — the candidate-E procedure, runnable
the day E's data open (2026-09-09), and validated today by re-running D.

M4 Sec 5 measured candidate D's contaminant from the public GO 7199 mosaics
through a chain of hard-coded single-purpose scripts (m4_jwstD_*.py).  This is
the same measurement with the target as an argument, so that E can be analysed
without writing new code, and so that nothing about E's analysis is chosen
after seeing E's data (M5 PR-4).

    python scripts/m5_jwst_target.py status --label E     # what is public, when
    python scripts/m5_jwst_target.py fetch  --label E     # anonymous MAST download
    python scripts/m5_jwst_target.py measure --label E    # the measurement
    python scripts/m5_jwst_target.py measure --label D --validate
                                                          # reproduce M4 Sec 5

Everything is anonymous: no MAST account, no token, nothing submitted.

PRE-REGISTERED DETECTION CRITERION (M5 PR-4, fixed before E's data exist):
a second source is DETECTED if the brightest pixel in the 0.5-2.2 arcsec
annulus around the propagated stellar position exceeds the 3.0-4.5 arcsec
annulus background by at least 5x that annulus's RMS, in at least two of the
three filters.  If it is not detected, the deliverable is an upper limit on
the contrast at the separation where a contaminant would have to sit, and
"no contaminant" is a reportable outcome, not a failure.
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
OUT = ROOT / "out"
JW = ROOT / "data" / "jwst"
JW.mkdir(parents=True, exist_ok=True)

PROGRAM = "7199"
FILT_ORDER = ["f560w", "f1000w", "f1500w", "f770w", "f1130w", "f1800w", "f2100w"]
# JDox MIRI imaging PSF FWHM, arcsec
JDOX = {"f560w": 0.207, "f770w": 0.269, "f1000w": 0.328, "f1130w": 0.375,
        "f1500w": 0.488, "f1800w": 0.591, "f2100w": 0.674}
PIVOT_UM = {"f560w": 5.6, "f770w": 7.7, "f1000w": 10.0, "f1130w": 11.3,
            "f1500w": 15.0, "f1800w": 18.0, "f2100w": 21.0}
DETECT_SIGMA = 5.0          # PR-4's fixed detection criterion
DETECT_MIN_FILTERS = 2
# M4 Sec 5.3: the archival centroid floor this measurement calibrates
FLOORS = (1.0, 2.0)
SUAZO_APERTURE_AS = 3.25


def ab(jy: float) -> float:
    return -2.5 * np.log10(jy / 3631.0) if jy and jy > 0 else float("nan")


def target_astrometry(label: str) -> dict:
    c = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv")
    r = c[c["label"] == label]
    if r.empty:
        raise SystemExit(f"no candidate labelled {label} in candidates_gaia_chain.csv")
    r = r.iloc[0]
    return {"label": label, "source_id": int(r["source_id"]),
            "ra": float(r["ra"]), "dec": float(r["dec"]),
            "pmra": float(r["pmra"]), "pmdec": float(r["pmdec"]),
            "parallax": float(r["parallax"]),
            "w3mpro": float(r["w3mpro"]), "w4mpro": float(r["w4mpro"])}


# ------------------------------------------------------------------ status --
def cmd_status(a: argparse.Namespace) -> None:
    from astroquery.mast import Observations              # noqa: PLC0415
    tg = target_astrometry(a.label)
    print(f"candidate {a.label}: Gaia DR3 {tg['source_id']} at "
          f"{tg['ra']:.6f} {tg['dec']:+.6f}")
    obs = Observations.query_criteria(proposal_id=PROGRAM).to_pandas()
    mine = obs[obs["target_name"].astype(str).str.contains(f"Object_{a.label}",
                                                           case=False, na=False)]
    if mine.empty:
        print(f"  no GO {PROGRAM} observation named Object_{a.label}")
        return
    cols = ["obs_id", "target_name", "instrument_name", "filters",
            "dataproduct_type", "calib_level", "t_exptime", "dataRights",
            "t_obs_release"]
    cols = [c for c in cols if c in mine.columns]
    print(mine[cols].to_string(index=False))
    pub = mine[mine["dataRights"].astype(str).str.upper() == "PUBLIC"]
    print(f"\n  PUBLIC observations: {len(pub)} of {len(mine)}")
    if "t_obs_release" in mine.columns:
        from astropy.time import Time                     # noqa: PLC0415
        rel = pd.to_numeric(mine["t_obs_release"], errors="coerce").dropna()
        if len(rel):
            print("  release dates (MJD -> ISO):")
            for m in sorted(rel.unique()):
                print(f"    {m:.2f}  {Time(m, format='mjd').iso[:10]}")
    (JW / f"m5_status_{a.label}.csv").write_text(mine[cols].to_csv(index=False))


# ------------------------------------------------------------------- fetch --
def cmd_fetch(a: argparse.Namespace) -> None:
    from astroquery.mast import Observations              # noqa: PLC0415
    obs = Observations.query_criteria(proposal_id=PROGRAM, dataproduct_type="image")
    o = obs.to_pandas()
    idx = [i for i in range(len(o))
           if f"object_{a.label}".lower() in str(o["target_name"].iloc[i]).lower()]
    if not idx:
        raise SystemExit(f"no image observation for Object_{a.label}")
    print(o.iloc[idx][["obs_id", "target_name", "filters", "dataRights"]]
          .to_string(index=False))
    prods = Observations.get_product_list(obs[idx])
    p = prods.to_pandas()
    p.to_csv(JW / f"m5_products_{a.label}.csv", index=False)
    mask = p["productFilename"].str.contains(
        r"_miri_f\d+w_(?:i2d\.fits|cat\.ecsv|segm\.fits)$", regex=True, na=False)
    sel = prods[list(mask.values)]
    print(f"\nselected {len(sel)} L3 products:")
    for fn in p["productFilename"][mask.values]:
        print("   ", fn)
    if not len(sel):
        raise SystemExit("no L3 mosaics available (still embargoed?)")
    m = Observations.download_products(sel, download_dir=str(JW), flat=True)
    print(m)


# ----------------------------------------------------------------- measure --
def profile(img, cx, cy, scale, mask, rmax=2.2, dr=0.055):
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    r = np.hypot(xx - cx, yy - cy) * scale
    b = np.arange(0, rmax + dr, dr)
    rc = 0.5 * (b[1:] + b[:-1])
    pr = np.full(len(rc), np.nan)
    for i in range(len(rc)):
        m = (r >= b[i]) & (r < b[i + 1]) & np.isfinite(img) & mask
        if m.sum() >= 2:
            pr[i] = np.median(img[m])
    return rc, pr


def fwhm_of(rc, pr):
    ok = np.isfinite(pr)
    if ok.sum() < 4:
        return np.nan
    pk = np.nanmax(pr[:3])
    k = np.where((pr < pk / 2.0) & ok)[0]
    k = k[k > 0]
    if not len(k):
        return np.nan
    i = k[0]
    return 2 * np.interp(pk / 2.0, [pr[i], pr[i - 1]], [rc[i], rc[i - 1]])


def cmd_measure(a: argparse.Namespace) -> None:
    from astropy.io import fits, ascii                    # noqa: PLC0415
    from astropy.wcs import WCS                           # noqa: PLC0415
    from astropy.coordinates import SkyCoord              # noqa: PLC0415
    import astropy.units as u                             # noqa: PLC0415
    from astropy.time import Time                         # noqa: PLC0415
    from astropy.nddata import Cutout2D                   # noqa: PLC0415
    from photutils.aperture import CircularAperture, aperture_photometry  # noqa: PLC0415, E501
    from photutils.centroids import centroid_quadratic    # noqa: PLC0415

    tg = target_astrometry(a.label)
    c16 = SkyCoord(ra=tg["ra"] * u.deg, dec=tg["dec"] * u.deg,
                   pm_ra_cosdec=tg["pmra"] * u.mas / u.yr,
                   pm_dec=tg["pmdec"] * u.mas / u.yr,
                   distance=(1000.0 / tg["parallax"]) * u.pc,
                   obstime=Time("J2016.0"))
    mosaics = sorted(JW.glob("*_miri_f*w_i2d.fits"))
    if a.obsprefix:
        mosaics = [m for m in mosaics if m.name.startswith(a.obsprefix)]
    if not mosaics:
        raise SystemExit(f"no MIRI i2d mosaics in {JW} "
                         f"(run `fetch --label {a.label}` first)")
    # keep only mosaics whose footprint contains the target
    use = []
    for m in mosaics:
        with fits.open(m) as h:
            try:
                w = WCS(h[1].header)
                x, y = w.world_to_pixel(c16.apply_space_motion(
                    new_obstime=Time(h[0].header["EXPSTART"], format="mjd")))
                if 60 < x < h[1].data.shape[1] - 60 and 60 < y < h[1].data.shape[0] - 60:
                    use.append(m)
            except Exception:  # noqa: BLE001
                pass
    if not use:
        raise SystemExit("the target does not land inside any downloaded mosaic")
    print(f"candidate {a.label}: {len(use)} mosaic(s) contain the target")

    rows, summ = [], {}
    for path in use:
        f = next(k for k in FILT_ORDER if f"_{k}_" in path.name)
        with fits.open(path) as h:
            sci = h[1].data.astype(float)
            err = h[2].data.astype(float)
            w = WCS(h[1].header)
            scale = abs(h[1].header["CDELT1"]) * 3600.0
            pixar = h[1].header["PIXAR_SR"]
            t = Time(h[0].header["EXPSTART"], format="mjd")
            calver = h[0].header.get("CAL_VER", "?")
            crds = h[0].header.get("CRDS_CTX", "?")
        capath = path.with_name(path.name.replace("_i2d.fits", "_cat.ecsv"))
        if capath.exists():
            apm = ascii.read(capath).meta["aperture_params"]
            radii = np.asarray(apm["aperture_radii"], float)
            apcorr = np.asarray(apm["aperture_corrections"], float)
        else:
            raise SystemExit(f"missing {capath.name}: the CRDS encircled-energy "
                             f"radii come from the L3 catalogue's metadata and "
                             f"are not invented here")
        EEc = 1.0 / apcorr

        cobs = c16.apply_space_motion(new_obstime=t)
        xs, ys = [float(v) for v in w.world_to_pixel(cobs)]
        cut = Cutout2D(sci, (xs, ys), (121, 121), wcs=w, mode="strict")
        ecut = Cutout2D(err, (xs, ys), (121, 121), mode="strict")
        d, e = cut.data.copy(), ecut.data.copy()
        cxs, cys = cut.to_cutout_position((xs, ys))
        N = d.shape[0]
        yy, xx = np.mgrid[:N, :N]
        rs = np.hypot(xx - cxs, yy - cys) * scale
        ann = (rs > 3.0) & (rs < 4.5)
        sky, skyrms = np.median(d[ann]), np.std(d[ann])
        dz = d - sky

        # PR-4's detection criterion
        ring = (rs > 0.5) & (rs < 2.2)
        peak = float(np.nanmax(np.where(ring, dz, -np.inf)))
        detected = peak >= DETECT_SIGMA * skyrms
        iy, ix = np.unravel_index(np.argmax(np.where(ring, dz, -1e9)), dz.shape)
        cg = centroid_quadratic(dz, xpeak=ix, ypeak=iy, fit_boxsize=7)
        gx, gy = float(cg[0]), float(cg[1])
        scg = cut.wcs.pixel_to_world(gx, gy)
        sep = cobs.separation(scg).arcsec
        pa = cobs.position_angle(scg).deg
        seppix = sep / scale

        print("\n" + "=" * 78)
        print(f"{f}  {path.name}  CAL_VER {calver} / {crds}  epoch {t.decimalyear:.3f}")
        print(f"  scale {scale:.5f} \"/pix   sky {sky:.4f}+-{skyrms:.4f} MJy/sr")
        print(f"  second source: peak {peak:.4f} = {peak / skyrms:.1f} sigma  "
              f"-> {'DETECTED' if detected else 'NOT DETECTED'} "
              f"(PR-4 threshold {DETECT_SIGMA:.0f} sigma)")
        print(f"  SEPARATION {sep:.4f}\"  PA {pa:.2f} deg")

        vgx, vgy = gx - cxs, gy - cys
        away_s = ((xx - cxs) * vgx + (yy - cys) * vgy) < 0
        away_g = ((xx - gx) * (-vgx) + (yy - gy) * (-vgy)) < 0
        # the brighter component decides whose wing profile models the leak;
        # measured, never assumed
        ap50 = CircularAperture([(cxs, cys), (gx, gy)], r=radii[1])
        ph50 = aperture_photometry(dz, ap50)
        brighter = ("star" if float(ph50["aperture_sum"][0])
                    >= float(ph50["aperture_sum"][1]) else "gal")
        bx, by, bm = ((cxs, cys, away_s) if brighter == "star"
                      else (gx, gy, away_g))
        rc, pr = profile(dz, bx, by, scale, bm)
        Fb = float(aperture_photometry(
            dz, CircularAperture([(bx, by)], r=radii[1]))["aperture_sum"][0]) / EEc[1]
        prn = pr / Fb
        good = np.isfinite(prn)

        def leak(r_pix: float) -> float:
            gg = np.mgrid[-int(r_pix) - 2:int(r_pix) + 3, -int(r_pix) - 2:int(r_pix) + 3]
            dxp, dyp = gg[1], gg[0]
            inside = np.hypot(dxp, dyp) <= r_pix
            dd = np.hypot(dxp[inside] + seppix, dyp[inside]) * scale
            return float(np.nansum(np.interp(dd, rc[good], prn[good],
                                             left=np.nan, right=0.0)))

        per = []
        for j, rp in enumerate(radii):
            L = leak(rp)
            A = np.array([[EEc[j], L], [L, EEc[j]]])
            aps = CircularAperture([(cxs, cys), (gx, gy)], r=rp)
            ph = aperture_photometry(dz, aps, error=e)
            m = np.array([float(ph["aperture_sum"][0]), float(ph["aperture_sum"][1])])
            me = np.array([float(ph["aperture_sum_err"][0]),
                           float(ph["aperture_sum_err"][1])])
            Fs, Fg = np.linalg.solve(A, m)
            eF = np.abs(np.linalg.solve(A, me))
            dL = np.abs(np.linalg.solve(
                np.array([[EEc[j], 1.3 * L], [1.3 * L, EEc[j]]]), m)
                - np.array([Fs, Fg]))
            jy = lambda v: v * pixar * 1e6                       # noqa: E731
            per.append(dict(r_arcsec=rp * scale, ee=EEc[j], leak=L, Fs=Fs, Fg=Fg,
                            Jy_s=jy(Fs), Jy_g=jy(Fg),
                            Jy_s_e=jy(np.hypot(eF[0], dL[0])),
                            Jy_g_e=jy(np.hypot(eF[1], dL[1]))))
            print(f"   r={rp * scale:.4f}\" EE={EEc[j]:.4f} leak={L:.5f} -> "
                  f"star {jy(Fs) * 1e6:9.2f} uJy (AB {ab(jy(Fs)):6.2f})   "
                  f"second {jy(Fg) * 1e6:10.2f} uJy (AB {ab(jy(Fg)):6.2f})   "
                  f"rho = {Fg / Fs:8.3f}")
        rcs, prs = profile(dz, cxs, cys, scale, away_s, rmax=1.0, dr=0.0555)
        rcg, prg = profile(dz, gx, gy, scale, away_g, rmax=1.0, dr=0.0555)
        fs, fg = fwhm_of(rcs, prs), fwhm_of(rcg, prg)
        print(f"  FWHM star {fs:.3f}\"  second {fg:.3f}\"  | JDox point source "
              f"{JDOX.get(f, float('nan'))}\"")

        p50 = per[1]
        summ[f] = dict(sep=sep, pa=pa, rho=p50["Fg"] / p50["Fs"],
                       detected=bool(detected), peak_sigma=float(peak / skyrms),
                       brighter=brighter, fwhm_star=fs, fwhm_second=fg,
                       jdox=JDOX.get(f), epoch=float(t.decimalyear),
                       cal_ver=calver, crds=crds, um=PIVOT_UM.get(f))
        for p in per:
            r = p["Fg"] / p["Fs"]
            rows.append(dict(label=a.label, filter=f.upper(),
                             ee_aperture=f"EE{int(round(p['ee'] * 100))}",
                             r_arcsec=round(p["r_arcsec"], 4),
                             crds_ee=round(p["ee"], 4), leak_frac=round(p["leak"], 5),
                             star_flux_uJy=round(p["Jy_s"] * 1e6, 3),
                             star_flux_err_uJy=round(p["Jy_s_e"] * 1e6, 3),
                             second_flux_uJy=round(p["Jy_g"] * 1e6, 3),
                             second_flux_err_uJy=round(p["Jy_g_e"] * 1e6, 3),
                             star_ABmag=round(ab(p["Jy_s"]), 3),
                             second_ABmag=round(ab(p["Jy_g"]), 3),
                             rho_second_over_star=round(r, 4),
                             sep_arcsec=round(sep, 4), PA_deg=round(pa, 2),
                             detected=bool(detected),
                             peak_sigma=round(float(peak / skyrms), 2),
                             fwhm_star_arcsec=round(fs, 4) if np.isfinite(fs) else np.nan,
                             fwhm_second_arcsec=round(fg, 4) if np.isfinite(fg) else np.nan,
                             epoch_dyr=round(t.decimalyear, 4)))

    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"m5_jwst{a.label}_photometry.csv", index=False)

    # ------------------------------------------------------- the calibration
    ndet = sum(1 for v in summ.values() if v["detected"])
    seps = np.array([v["sep"] for v in summ.values()])
    pas = np.array([v["pa"] for v in summ.values()])
    res: dict = {"label": a.label, "source_id": tg["source_id"],
                 "n_filters": len(summ), "n_detected": ndet,
                 "detection_criterion": (f"peak in the 0.5-2.2\" annulus >= "
                                         f"{DETECT_SIGMA:.0f}x the 3.0-4.5\" "
                                         f"annulus RMS, in >= {DETECT_MIN_FILTERS} "
                                         f"filters (M5 PR-4)"),
                 "second_source_detected": bool(ndet >= DETECT_MIN_FILTERS),
                 "per_filter": summ}
    if len(summ) >= 1:
        res["separation_arcsec_mean"] = float(seps.mean())
        res["separation_arcsec_sd"] = float(seps.std(ddof=1)) if len(seps) > 1 else None
        res["PA_deg_mean"] = float(pas.mean())
        res["PA_deg_sd"] = float(pas.std(ddof=1)) if len(pas) > 1 else None
    print("\n" + "=" * 78)
    print(f"SEPARATION {seps.round(4)}  mean {seps.mean():.4f}"
          + (f" sd {seps.std(ddof=1):.4f}" if len(seps) > 1 else "") + " arcsec")
    print(f"PA         {pas.round(2)}  mean {pas.mean():.2f}"
          + (f" sd {pas.std(ddof=1):.2f}" if len(pas) > 1 else "") + " deg")

    # rho(lambda) power law and the W3/W4 extrapolation, as M4 Sec 5.3 did
    ums = np.array([v["um"] for v in summ.values() if v["um"]])
    rhos = np.array([v["rho"] for v in summ.values() if v["um"]])
    ok = np.isfinite(ums) & np.isfinite(rhos) & (rhos > 0)
    if ok.sum() >= 2:
        k, b = np.polyfit(np.log10(ums[ok]), np.log10(rhos[ok]), 1)
        rho_w3 = 10 ** (k * np.log10(12.0) + b)
        rho_w4 = 10 ** (k * np.log10(22.0) + b)
        res["rho_powerlaw_index"] = float(k)
        res["rho_W3_12um"] = float(rho_w3)
        res["rho_W4_22um"] = float(rho_w4)
        sepm = float(seps.mean())
        res["predicted_centroid_pull_W3_arcsec"] = sepm * rho_w3 / (1 + rho_w3)
        res["predicted_centroid_pull_W4_arcsec"] = sepm * rho_w4 / (1 + rho_w4)
        res["geometric_ceiling_arcsec"] = sepm
        print(f"\nrho ∝ lambda^{k:+.2f};  rho(W3,12um) = {rho_w3:.1f}, "
              f"rho(W4,22um) = {rho_w4:.1f} (extrapolated)")
        print(f"predicted centroid pull  W3 {sepm * rho_w3 / (1 + rho_w3):.2f}\"  "
              f"W4 {sepm * rho_w4 / (1 + rho_w4):.2f}\"   "
              f"geometric ceiling = the separation itself, {sepm:.2f}\"")
        # M4 Sec 5.3's threshold locus, for THIS object
        thr = {str(F): {"sep_thr_arcsec": F * (1 + 1 / rho_w3),
                        "blind_fraction": min(1.0, (F * (1 + 1 / rho_w3)
                                                    / SUAZO_APERTURE_AS) ** 2),
                        "this_object_visible": bool(sepm > F * (1 + 1 / rho_w3))}
               for F in FLOORS}
        res["archival_floor"] = thr
        for F, v in thr.items():
            print(f"  floor {F}\": sep_thr = {v['sep_thr_arcsec']:.3f}\", "
                  f"this object {'CLEARS' if v['this_object_visible'] else 'is INVISIBLE'} it")
    # the archival centroid this project measured, for comparison
    ao = OUT / "w2_centroid_offsets.csv"
    if ao.exists():
        aoff = pd.read_csv(ao)
        m = aoff[aoff.astype(str).apply(
            lambda r: r.str.contains(a.label, case=False, na=False).any(), axis=1)]
        if len(m):
            res["archival_centroid_rows"] = m.to_dict("records")
            print("\narchival centroid offsets measured by this project:")
            print(m.to_string(index=False))

    (OUT / f"m5_jwst{a.label}_summary.json").write_text(json.dumps(res, indent=2,
                                                                   default=float))
    print(f"\nwrote out/m5_jwst{a.label}_photometry.csv, "
          f"out/m5_jwst{a.label}_summary.json")

    if a.validate and a.label == "D":
        validate_against_m4(res, df)


def validate_against_m4(res: dict, df: pd.DataFrame) -> None:
    """PR-4: the parameterised path must reproduce M4 Sec 5's D numbers before
    it is declared ready for E."""
    print("\n" + "=" * 78)
    print("PR-4 VALIDATION: parameterised chain vs M4 Sec 5's hard-coded chain")
    m4 = pd.read_csv(OUT / "m4_jwstD_photometry.csv")
    ref = {"separation": 1.23, "sep_sd": 0.07, "PA": 33.0,
           "rho_f560w": 0.236, "rho_f1000w": 7.24, "rho_f1500w": 83.1,
           "rho_W3": 21.8, "pull_W3": 1.18, "pull_W4": 1.23}
    ok = True
    checks = []

    def chk(name, got, want, tol):
        nonlocal ok
        good = np.isfinite(got) and abs(got - want) <= tol
        ok &= bool(good)
        checks.append({"check": name, "M5": float(got), "M4": float(want),
                       "tol": tol, "pass": bool(good)})
        print(f"  {'PASS' if good else 'FAIL'}  {name:24s} "
              f"M5 {got:9.3f}   M4 {want:9.3f}   tol +-{tol}")

    chk("separation (arcsec)", res["separation_arcsec_mean"], ref["separation"], 0.02)
    chk("PA (deg)", res["PA_deg_mean"], ref["PA"], 1.0)
    # the EE50 row is the SECOND of the three CRDS apertures; its label rounds
    # to EE49 or EE50 depending on the filter, so select by position, not name
    for f, want in (("F560W", ref["rho_f560w"]), ("F1000W", ref["rho_f1000w"]),
                    ("F1500W", ref["rho_f1500w"])):
        s = df[df["filter"] == f]
        m = m4[m4["filter"] == f]
        if len(s) > 1 and len(m) > 1:
            chk(f"rho {f}", float(s["rho_second_over_star"].iloc[1]),
                float(m["ratio_gal_over_star"].iloc[1]), 0.02 * max(want, 1))
    chk("rho(W3, 12um)", res.get("rho_W3_12um", np.nan), ref["rho_W3"], 1.5)
    chk("pull W3 (arcsec)", res.get("predicted_centroid_pull_W3_arcsec", np.nan),
        ref["pull_W3"], 0.03)
    print(f"\n  PR-4 readiness: {'READY for candidate E' if ok else 'NOT READY'}")
    (OUT / "m5_jwstD_validation.json").write_text(
        json.dumps({"ready": bool(ok), "checks": checks}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("status", "fetch"):
        s = sub.add_parser(c)
        s.add_argument("--label", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--label", required=True)
    m.add_argument("--obsprefix", default="",
                   help="restrict to mosaics whose filename starts with this "
                        "(e.g. jw07199-o005 for D)")
    m.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    {"status": cmd_status, "fetch": cmd_fetch, "measure": cmd_measure}[a.cmd](a)


if __name__ == "__main__":
    main()
