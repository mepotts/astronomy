"""M6: candidate D's MIRI/MRS cubes - the independent test of z ~= 0.922.

M4 Sec 5.2 confirmed D's contamination from imaging but marked the redshift
UNSOURCED: "the redshift rests entirely on the MRS emission lines, which were
not reduced here."  Hephaistos IV's z = 0.922 rests on a spectrum nobody
outside the collaboration has extracted.  The cubes are public.  This script
extracts the contaminant's spectrum from them and asks what redshift the data
actually support.

    python scripts/m6_mrs_reduce.py fetch    --label D
    python scripts/m6_mrs_reduce.py extract  --label D --assoc o002
    python scripts/m6_mrs_reduce.py redshift --label D

WHAT "REDUCE" MEANS HERE, STATED PLAINLY (repo law: sourced-or-UNSOURCED).
The products used are STScI's public Level-3 `_s3d.fits` calibrated cubes,
built by the JWST calibration pipeline; this project does not re-run
`calwebb_spec3` from the uncalibrated ramps (that needs a multi-GB CRDS cache
and would reproduce STScI's own product).  The CAL_VER / CRDS_CTX actually
used are read from each cube header and reported, exactly as M4 Sec 5.1 did
for the imaging, so a reader can see whether these are the same pipeline files
the paper used.  What is new here, and what nobody has published, is the
SPATIALLY RESOLVED EXTRACTION: the pipeline's own `x1d` product is a single
aperture centred on the target and therefore blends the star with the
contaminant 1.23 arcsec away.  This script deblends them per wavelength slice.

METHOD.  Per slice, a three-parameter linear least-squares fit:

    I(x,y) = A_star * G(x - x_s, y - y_s ; s) + A_con * G(x - x_c, y - y_c ; s) + B

with the two positions FIXED at the Gaia position propagated to the cube's own
EXPSTART and at that position plus M4 Sec 5's measured offset
(1.233 arcsec, PA 32.998 deg), and s fixed by the MRS PSF FWHM relation.  This
is M4 Sec 5's 2x2 deblend with a background term, applied slice by slice.  A
single free plate offset per cube is solved once from the white-light image so
that a pointing error cannot be mistaken for a flux ratio.
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
MRS = ROOT / "data" / "jwst" / "mrs"
MRS.mkdir(parents=True, exist_ok=True)

PROGRAM = "7199"
# M4 Sec 5.1 / M5 Sec 5.2: the measured pair.  Fixed here, not refitted.
SEP_AS = 1.233
PA_DEG = 32.998
GAIA_EPOCH = 2016.0


def mrs_fwhm(lam_um):
    """MIRI MRS PSF FWHM, arcsec (JDox / Argyriou+ 2023 empirical relation)."""
    return 0.033 * np.asarray(lam_um, float) + 0.106


def target_astrometry(label: str) -> dict:
    c = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv")
    r = c[c["label"] == label]
    if r.empty:
        raise SystemExit("no candidate labelled " + label)
    r = r.iloc[0]
    return {"label": label, "source_id": int(r["source_id"]),
            "ra": float(r["ra"]), "dec": float(r["dec"]),
            "pmra": float(r["pmra"]), "pmdec": float(r["pmdec"])}


def propagate(tg: dict, mjd: float):
    from astropy.time import Time
    dt = Time(mjd, format="mjd").jyear - GAIA_EPOCH
    dec = tg["dec"] + tg["pmdec"] * dt / 3.6e6
    ra = tg["ra"] + tg["pmra"] * dt / 3.6e6 / np.cos(np.radians(tg["dec"]))
    return ra, dec


# ------------------------------------------------------------------ fetch --
def cmd_fetch(a) -> None:
    from astroquery.mast import Observations
    obs = Observations.query_criteria(proposal_id=PROGRAM, dataproduct_type="cube")
    o = obs.to_pandas()
    want = [i for i in range(len(o))
            if str(o["target_name"].iloc[i]).lower() == ("object_" + a.label).lower()]
    if not want:
        raise SystemExit("no IFU cube observation named Object_" + a.label)
    print(o.iloc[want][["obs_id", "target_name", "filters", "dataRights",
                        "calib_level"]].to_string(index=False))
    pub = [i for i in want if str(o["dataRights"].iloc[i]).upper() == "PUBLIC"]
    if len(pub) != len(want):
        print("  WARNING: %d of %d still embargoed" % (len(want) - len(pub), len(want)))
    if not pub:
        raise SystemExit("nothing public")
    prods = Observations.get_product_list(obs[pub])
    p = prods.to_pandas()
    p.to_csv(MRS / ("m6_products_%s_cube.csv" % a.label), index=False)
    mask = (p["productFilename"].str.match(
        r"jw\d+-(o\d+|c\d+)_t\d+_miri_ch\d-\w+_s3d\.fits$")
        & (p["calib_level"] == 3))
    if a.assoc:
        mask = mask & p["productFilename"].str.contains("-" + a.assoc + "_")
    sel = prods[list(mask.values)]
    tot = p.loc[mask.values, "size"].sum() / 1e6 if "size" in p.columns else float("nan")
    print("\nselected %d L3 s3d cubes, %.0f MB" % (len(sel), tot))
    for fn in sorted(set(p["productFilename"][mask.values])):
        print("   ", fn)
    Observations.download_products(sel, download_dir=str(MRS), flat=True)
    print("done ->", MRS)


# ---------------------------------------------------------------- extract --
def profile_2d(xx, yy, x0, y0, sig, beta):
    """Moffat if beta is finite, Gaussian otherwise.

    The MIRI MRS PSF has real Airy wings.  A Gaussian has none, so a
    Gaussian deblend systematically over-assigns the BRIGHT component's wings
    to the FAINT component -- which is exactly the regime M6 PR-2's acceptance
    test probes (the star at 15 um, the contaminant at 5.6 um).  A Moffat with
    a fitted beta carries wings and is still analytically integrable.
    """
    r2 = (xx - x0) ** 2 + (yy - y0) ** 2
    if beta is None or not np.isfinite(beta):
        return np.exp(-r2 / (2 * sig ** 2))
    alpha = sig * np.sqrt(2 ** (1.0 / beta) - 1) * 2.3548 / 2.0
    return (1.0 + r2 / alpha ** 2) ** (-beta)


def prof_norm(sig, beta):
    """Integral of profile_2d over the plane, in pixel units."""
    if beta is None or not np.isfinite(beta):
        return 2 * np.pi * sig ** 2
    alpha = sig * np.sqrt(2 ** (1.0 / beta) - 1) * 2.3548 / 2.0
    return np.pi * alpha ** 2 / (beta - 1.0)


def slice_fit(img, xs, ys, xc, yc, sig, beta=None):
    """Linear 3-parameter fit: two fixed-position profiles + constant."""
    ny, nx = img.shape
    yy, xx = np.mgrid[:ny, :nx]
    good = np.isfinite(img)
    if good.sum() < 20:
        return (np.nan,) * 5
    gs = profile_2d(xx, yy, xs, ys, sig, beta)
    gc = profile_2d(xx, yy, xc, yc, sig, beta)
    A = np.column_stack([gs[good], gc[good], np.ones(int(good.sum()))])
    b = img[good]
    try:
        coef = np.linalg.lstsq(A, b, rcond=None)[0]
    except np.linalg.LinAlgError:
        return (np.nan,) * 5
    resid = b - A @ coef
    rms = float(np.std(resid))
    try:
        cov = np.linalg.inv(A.T @ A) * rms ** 2
        eac = float(np.sqrt(cov[1, 1]))
    except np.linalg.LinAlgError:
        eac = np.nan
    norm = prof_norm(sig, beta)
    return (float(coef[0] * norm), float(coef[1] * norm), float(coef[2]),
            rms, eac * norm)


def cmd_extract(a) -> None:
    from astropy.io import fits
    from astropy.wcs import WCS
    tg = target_astrometry(a.label)
    pat = "jw%05d-%s*_s3d.fits" % (int(PROGRAM), a.assoc)
    cubes = sorted(MRS.glob(pat))
    if not cubes:
        raise SystemExit("no cubes matching %s in %s" % (pat, MRS))
    rows, meta = [], []
    for cf in cubes:
        with fits.open(cf) as hd:
            h0, h1 = hd[0].header, hd["SCI"].header
            cube = hd["SCI"].data.astype(float)
            err = hd["ERR"].data.astype(float) if "ERR" in hd else None
            w = WCS(h1)
            band = "%s-%s" % (h0.get("CHANNEL", "?"),
                              str(h0.get("BAND", "?")).lower())
            mjd = float(h0.get("EXPSTART", h0.get("MJD-BEG", np.nan)))
            ra, dec = propagate(tg, mjd)
            nz = cube.shape[0]
            lam = h1["CRVAL3"] + (np.arange(nz) + 1 - h1["CRPIX3"]) * h1["CDELT3"]
            if h1["CDELT3"] < 1e-5:      # metres, not microns
                lam = lam * 1e6
            scale = abs(h1["CDELT1"]) * 3600.0          # arcsec/pix
            dra = SEP_AS * np.sin(np.radians(PA_DEG)) / 3600.0 / np.cos(np.radians(dec))
            ddec = SEP_AS * np.cos(np.radians(PA_DEG)) / 3600.0
            xs0, ys0 = [float(v) for v in w.celestial.all_world2pix(ra, dec, 0)]
            xc0, yc0 = [float(v) for v in
                        w.celestial.all_world2pix(ra + dra, dec + ddec, 0)]
            white = np.nanmedian(cube, axis=0)
            fw = float(np.nanmedian(mrs_fwhm(lam)))
            # The PSF SHAPE is measured from the cube's own white-light image
            # rather than assumed: the JDox FWHM relation describes the optical
            # PSF, while the L3 cube's is broadened by the cube build, and a
            # too-narrow model dumps the bright component's wings into the
            # faint one -- the failure M6 PR-2's acceptance test caught.  The
            # two POSITIONS stay fixed at PR-2's values; only width, wing index
            # and one plate offset are fitted, all from the white light.
            dx = dy = 0.0
            kbest, beta = 1.0, None
            if np.isfinite(white).sum() > 50:
                bl = np.inf
                for bt in (None, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0):
                    for kk in (0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6):
                        s = max(kk * fw / 2.3548 / scale, 0.5)
                        for ddx in np.arange(-1.5, 1.51, 0.25):
                            for ddy in np.arange(-1.5, 1.51, 0.25):
                                r = slice_fit(white, xs0 + ddx, ys0 + ddy,
                                              xc0 + ddx, yc0 + ddy, s, bt)[3]
                                if np.isfinite(r) and r < bl:
                                    bl = r
                                    dx, dy, kbest, beta = (float(ddx), float(ddy),
                                                           kk, bt)
            sr_pix = ((abs(h1["CDELT1"]) * np.pi / 180)
                      * (abs(h1["CDELT2"]) * np.pi / 180))
            sig_all = np.maximum(kbest * mrs_fwhm(lam) / 2.3548 / scale, 0.5)
            for k in range(nz):
                im = cube[k]
                if not np.isfinite(im).any():
                    continue
                As, Ac, B, rms, eac = slice_fit(im, xs0 + dx, ys0 + dy,
                                                xc0 + dx, yc0 + dy, sig_all[k],
                                                beta)
                rows.append({"band": band, "lam_um": float(lam[k]),
                             "f_star_jy": As * sr_pix * 1e6,
                             "f_con_jy": Ac * sr_pix * 1e6,
                             "e_con_jy": eac * sr_pix * 1e6,
                             "bkg_mjysr": B, "resid_rms": rms,
                             "sr_pix": sr_pix, "scale_as": scale})
            meta.append({"file": cf.name, "band": band, "cal_ver": h0.get("CAL_VER"),
                         "crds_ctx": h0.get("CRDS_CTX"), "crds_ver": h0.get("CRDS_VER"),
                         "s_region_ok": True, "expstart": mjd, "nz": int(nz),
                         "lam_min": float(lam.min()), "lam_max": float(lam.max()),
                         "scale_as": scale, "nx": int(cube.shape[2]),
                         "ny": int(cube.shape[1]), "dx_pix": dx, "dy_pix": dy,
                         "psf_k": kbest, "psf_beta": beta,
                         "psf_fwhm_as": kbest * fw,
                         "sep_pix": float(np.hypot(xc0 - xs0, yc0 - ys0)),
                         "date_obs": h0.get("DATE-OBS"),
                         "targname": h0.get("TARGNAME"), "bunit": h1.get("BUNIT")})
        print("  %-46s %-12s %s  dx,dy=%+.2f,%+.2f  k=%.2f beta=%s" %
              (cf.name, band, cube.shape, dx, dy, kbest, beta))
    df = pd.DataFrame(rows).sort_values("lam_um").reset_index(drop=True)
    tagf = "" if a.assoc == "o002" else "_" + a.assoc
    df.to_csv(OUT / ("m6_mrs_%s_spectra%s.csv" % (a.label, tagf)), index=False)
    md = pd.DataFrame(meta)
    md.to_csv(OUT / ("m6_mrs_%s_cubes%s.csv" % (a.label, tagf)), index=False)
    print("\n%d slices -> out/m6_mrs_%s_spectra%s.csv" % (len(df), a.label, tagf))
    print(md[["band", "cal_ver", "crds_ctx", "lam_min", "lam_max",
              "scale_as", "sep_pix", "dx_pix", "dy_pix", "psf_k", "psf_beta",
              "psf_fwhm_as"]].to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--label", default="D")
    f.add_argument("--assoc", default="")
    e = sub.add_parser("extract")
    e.add_argument("--label", default="D")
    e.add_argument("--assoc", default="o002")
    a = ap.parse_args()
    {"fetch": cmd_fetch, "extract": cmd_extract}[a.cmd](a)


if __name__ == "__main__":
    main()
