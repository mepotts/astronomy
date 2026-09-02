"""M7 PR-1 sensitivities on candidate D's MRS extraction.

Two things, neither of which touches the PRIMARY result: M6 PR-2's acceptance
test is graded on the primary extraction by the unmodified M6 code, and nothing
here re-grades it.

  1. THE UNRESOLVED-PAIR DIAGNOSTIC.  The pair is 1.233 arcsec apart and the
     MRS PSF FWHM runs 0.28 arcsec at 5 um to 0.98 arcsec at 26.5 um, so the
     separation falls from 4.4 to 1.3 PSF FWHM across the cubes.  Where it is
     small the two-component design matrix is nearly collinear and NO deblend
     is determined -- by either method.  The model-free symptom is an
     UNPHYSICAL NEGATIVE fitted flux.  This measures the negative fraction per
     sub-band for M6's Gaussian extraction and M7's empirical one, and emits a
     band-restricted copy of each spectrum dropping the sub-bands where it
     exceeds 20% of slices, so the whole downstream chain can be re-run on the
     restricted set by the UNCHANGED M6 grader.

  2. PR-1's DECLARED STAR-SCALED SENSITIVITY.  The primary extraction adopts
     the DONOR-derived profile per sub-band.  The declared alternative is the
     STAR-derived profile -- the star is a known point source -- scaled to
     every sub-band on the r/FWHM grid.  Both acceptance outcomes are printed.

    python scripts/m7_mrs_sensitivity.py resolved
    python scripts/m7_mrs_sensitivity.py starscaled
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

from m6_mrs_reduce import SEP_AS, mrs_fwhm  # noqa: E402

NEG_MAX = 0.20            # sub-band is dropped if >20% of slices go negative


def band_table(tag: str) -> pd.DataFrame:
    df = pd.read_csv(OUT / ("m6_mrs_D%s_spectra.csv" % tag))
    rows = []
    for band, g in df.groupby("band"):
        lam = float(g["lam_um"].median())
        fw = float(mrs_fwhm(lam))
        rows.append({"band": band, "lam_med_um": lam, "fwhm_as": fw,
                     "sep_over_fwhm": SEP_AS / fw, "n_slices": int(len(g)),
                     "neg_frac_star": float((g["f_star_jy"] < 0).mean()),
                     "neg_frac_con": float((g["f_con_jy"] < 0).mean()),
                     "med_f_star_jy": float(g["f_star_jy"].median()),
                     "med_f_con_jy": float(g["f_con_jy"].median())})
    t = pd.DataFrame(rows).sort_values("lam_med_um").reset_index(drop=True)
    t["neg_frac_max"] = t[["neg_frac_star", "neg_frac_con"]].max(axis=1)
    t["determined"] = t["neg_frac_max"] <= NEG_MAX
    return t


def cmd_resolved(a) -> None:
    res = {"criterion": "a sub-band is reported as NOT DETERMINED if more than "
                        "%.0f%% of its slices give a negative fitted flux for "
                        "either component -- an unphysical value, and the only "
                        "model-free symptom of a collinear two-component "
                        "design matrix" % (100 * NEG_MAX),
           "separation_arcsec": SEP_AS}
    for tag, name in (("", "M6_gaussian"), ("_epsf", "M7_empirical")):
        t = band_table(tag)
        res[name] = json.loads(t.to_json(orient="records"))
        print("\n%s" % name)
        print(t.round(4).to_string(index=False))
        keep = list(t.loc[t["determined"], "band"])
        drop = list(t.loc[~t["determined"], "band"])
        res[name + "_dropped"] = drop
        df = pd.read_csv(OUT / ("m6_mrs_D%s_spectra.csv" % tag))
        md = pd.read_csv(OUT / ("m6_mrs_D%s_cubes.csv" % tag))
        lab = "D%s_res" % tag
        df[df["band"].isin(keep)].to_csv(
            OUT / ("m6_mrs_%s_spectra.csv" % lab), index=False)
        md[md["band"].isin(keep)].to_csv(
            OUT / ("m6_mrs_%s_cubes.csv" % lab), index=False)
        print("  dropped: %s  -> band-restricted label %s" % (drop or "none", lab))
    (OUT / "m7_mrs_resolved.json").write_text(json.dumps(res, indent=2))
    print("\n-> out/m7_mrs_resolved.json")
    print("Re-grade the restricted sets with the UNCHANGED M6 code:")
    print("  python scripts/m6_mrs_redshift.py --label D_res")
    print("  python scripts/m6_mrs_redshift.py --label D_epsf_res")


def cmd_starscaled(a) -> None:
    """Rebuild the extraction forcing the STAR-derived profile everywhere."""
    import m7_mrs_epsf as E
    from astropy.io import fits
    psfs = json.load(open(OUT / "m7_epsf_psfs.json"))
    star_bands = [b for b, d in psfs.items()
                  if d["donor"] == "star" and d["is_donor"]]
    if not star_bands:
        raise SystemExit("no star-donor sub-band; the sensitivity cannot run")
    stack = np.array([bb["prof"] for b in star_bands for bb in psfs[b]["bins"]])
    star_prof = np.median(stack, axis=0)
    # renormalise the median profile on a representative FWHM; the profile is
    # dimensionless in u = r/FWHM, so any FWHM normalises it consistently
    # scale-free normalisation, matching E.eval_profile's convention
    star_prof = star_prof / max(float(np.trapezoid(
        star_prof * 2 * np.pi * E.ugrid(), E.ugrid())), 1e-30)
    print("star-scaled profile from %d bins in %s" % (len(stack), star_bands))
    u = E.ugrid()
    tg = E.target_astrometry("D")
    rows, meta = [], []
    for cf in sorted(E.MRS.glob("jw%05d-%s*_s3d.fits" % (int(E.PROGRAM), a.assoc))):
        with fits.open(cf) as hd:
            h0, h1 = hd[0].header, hd["SCI"].header
            cube = hd["SCI"].data.astype(float)
            err = (hd["ERR"].data.astype(float) if "ERR" in hd
                   else np.ones_like(cube))
            band = "%s-%s" % (h0.get("CHANNEL", "?"),
                              str(h0.get("BAND", "?")).lower())
            (xs0, ys0), (xc0, yc0), _, mjd = E.positions(h1, h0, tg)
            nz = cube.shape[0]
            lam = h1["CRVAL3"] + (np.arange(nz) + 1 - h1["CRPIX3"]) * h1["CDELT3"]
            if h1["CDELT3"] < 1e-5:
                lam = lam * 1e6
            scale = abs(h1["CDELT1"]) * 3600.0
            sr_pix = ((abs(h1["CDELT1"]) * np.pi / 180)
                      * (abs(h1["CDELT2"]) * np.pi / 180))
            white = np.nanmedian(cube, axis=0)
            fin = np.isfinite(white)
            donor = psfs[band]["donor"] if band in psfs else "con"
            dx, dy, _ = E.centroid_offset(
                white, xs0 if donor == "star" else xc0,
                ys0 if donor == "star" else yc0)
            xs, ys, xc, yc = xs0 + dx, ys0 + dy, xc0 + dx, yc0 + dy
            ny_, nx_ = white.shape
            yy, xx = np.mgrid[:ny_, :nx_]
            sep_pix = float(np.hypot(xc0 - xs0, yc0 - ys0))
            fw_med = float(np.nanmedian(mrs_fwhm(lam))) / scale
            region = (np.hypot(xx - 0.5 * (xs + xc), yy - 0.5 * (ys + yc))
                      <= max(4.0 * fw_med, 2.0 * sep_pix))
            r_s = np.hypot(xx - xs, yy - ys)
            r_c = np.hypot(xx - xc, yy - yc)
            for kz in range(nz):
                im = cube[kz]
                if not np.isfinite(im).any():
                    continue
                sg = err[kz]
                wg = np.where(np.isfinite(sg) & (sg > 0) & region & fin,
                              1.0 / sg ** 2, 0.0)
                fw_z = float(mrs_fwhm(lam[kz])) / scale
                ps = E.eval_profile(u, star_prof, r_s, fw_z)
                pc = E.eval_profile(u, star_prof, r_c, fw_z)
                As, Ac, B, chi, (eas, eac) = E.solve3(im, wg, ps, pc)
                rows.append({"band": band, "lam_um": float(lam[kz]),
                             "f_star_jy": As * sr_pix * 1e6,
                             "f_con_jy": Ac * sr_pix * 1e6,
                             "e_con_jy": eac * sr_pix * 1e6,
                             "bkg_mjysr": B, "resid_rms": chi,
                             "sr_pix": sr_pix, "scale_as": scale})
            meta.append({"file": cf.name, "band": band,
                         "cal_ver": h0.get("CAL_VER"),
                         "crds_ctx": h0.get("CRDS_CTX"),
                         "lam_min": float(lam.min()),
                         "lam_max": float(lam.max()), "scale_as": scale,
                         "sep_pix": sep_pix, "dx_pix": dx, "dy_pix": dy,
                         "psf_k": np.nan, "psf_beta": "star-scaled",
                         "psf_fwhm_as": float(np.nanmedian(mrs_fwhm(lam))),
                         "nz": int(nz)})
            print("  %-12s done" % band)
    pd.DataFrame(rows).sort_values("lam_um").to_csv(
        OUT / "m6_mrs_D_starscaled_spectra.csv", index=False)
    pd.DataFrame(meta).to_csv(OUT / "m6_mrs_D_starscaled_cubes.csv", index=False)
    print("-> out/m6_mrs_D_starscaled_spectra.csv")
    print("Grade it with the UNCHANGED M6 code:")
    print("  python scripts/m6_mrs_redshift.py --label D_starscaled")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("resolved")
    s = sub.add_parser("starscaled")
    s.add_argument("--assoc", default="o002")
    a = ap.parse_args()
    {"resolved": cmd_resolved, "starscaled": cmd_starscaled}[a.cmd](a)


if __name__ == "__main__":
    main()
