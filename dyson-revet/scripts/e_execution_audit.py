"""Audit the failed frozen E measurement, without changing or rescuing its method.

The full FITS check is local-only. The status function uses the standard library
so unavailable/failed measurements cannot be promoted by offline CI.
"""
import argparse
import hashlib
import json
import math
import re
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/jwst"
OUT = ROOT / "out/e-execution-20260912.json"
PREFIX = "jw07199-o006_t008_miri_"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execution_status(returncode, rows):
    if returncode != 0:
        return "STOP_FROZEN_MEASUREMENT"
    if len(rows) != 3 or any(not r.get("centroid_finite", False) for r in rows):
        return "STOP_INCOMPLETE_MEASUREMENT"
    return "REQUIRES_FULL_SCIENTIFIC_VALIDATION"


def finite_or_none(value):
    return float(value) if math.isfinite(float(value)) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--reuse-log", action="store_true", help="Re-audit the retained failure without rerunning the frozen script")
    args = parser.parse_args()
    import astropy.units as u
    import m5_jwst_target as frozen
    import numpy as np
    from astropy.coordinates import SkyCoord
    from astropy.io import fits
    from astropy.nddata import Cutout2D
    from astropy.time import Time
    from astropy.wcs import WCS
    from check_e_release import bounded_run
    from photutils.centroids import centroid_quadratic

    release = json.loads((ROOT / "out/e-release-20260912.json").read_bytes())
    if release["status"] != "READY_FOR_FROZEN_ANALYSIS":
        raise ValueError("release gate not passed")
    logpath = RAW / "e-frozen-execution-20260912.log"
    receipt = RAW / "e-frozen-execution-20260912.json"
    if args.replay or args.reuse_log:
        run = json.loads(receipt.read_bytes())
        if run["log_sha256"] != digest(logpath):
            raise ValueError("frozen log changed")
    else:
        if receipt.exists() or OUT.exists():
            raise ValueError("execution receipt exists; use --replay")
        code, output = bounded_run([sys.executable, "scripts/m5_jwst_target.py", "measure",
                                    "--label", "E", "--obsprefix", "jw07199-o006"], 45)
        logpath.write_text(output, encoding="utf-8")
        run = {"returncode": code, "log_sha256": digest(logpath),
               "executed_utc": datetime.now(timezone.utc).isoformat(),
               "note": "Second identical execution, retained to verify/reproduce the initial failure."}
        receipt.write_text(json.dumps(run, indent=2)+"\n", encoding="utf-8")

    target = frozen.target_astrometry("E")
    c16 = SkyCoord(ra=target["ra"]*u.deg, dec=target["dec"]*u.deg,
                   pm_ra_cosdec=target["pmra"]*u.mas/u.yr, pm_dec=target["pmdec"]*u.mas/u.yr,
                   distance=(1000/target["parallax"])*u.pc, obstime=Time("J2016.0"))
    rows, inputs = [], []
    for filt in ("f560w", "f1000w", "f1500w"):
        for suffix in ("i2d.fits", "cat.ecsv", "segm.fits"):
            p = RAW / (PREFIX+filt+"_"+suffix)
            inputs.append({"name": p.name, "bytes": p.stat().st_size, "sha256": digest(p)})
        path = RAW / (PREFIX+filt+"_i2d.fits")
        with fits.open(path) as h:
            image = np.asarray(h["SCI"].data, dtype=float)
            wcs = WCS(h["SCI"].header)
            scale = abs(h["SCI"].header["CDELT1"])*3600
            position = c16.apply_space_motion(new_obstime=Time(h[0].header["EXPSTART"], format="mjd"))
            xs, ys = (float(v) for v in wcs.world_to_pixel(position))
            cut = Cutout2D(image, (xs, ys), (121, 121), wcs=wcs, mode="strict")
            x0, y0 = cut.to_cutout_position((xs, ys))
            yy, xx = np.indices(cut.data.shape)
            radius = np.hypot(xx-x0, yy-y0)*scale
            annulus = (radius > 3.) & (radius < 4.5)
            d = cut.data-np.median(cut.data[annulus])
            ring = (radius > .5) & (radius < 2.2)
            iy, ix = np.unravel_index(np.argmax(np.where(ring, d, -1e9)), d.shape)
            with warnings.catch_warnings(record=True) as messages:
                warnings.simplefilter("always")
                center = centroid_quadratic(d, xpeak=ix, ypeak=iy, fit_boxsize=7)
            # Independent centered-coordinate least-squares Hessian on the same
            # 7x7 fitting patch; no alternative centroid is used for photometry.
            patch = d[iy-3:iy+4, ix-3:ix+4]
            py, px = np.mgrid[-3:4, -3:4]
            design = np.column_stack([np.ones(49), px.ravel(), py.ravel(),
                                      (px*py).ravel(), (px*px).ravel(), (py*py).ravel()])
            coeff = np.linalg.lstsq(design, patch.ravel(), rcond=None)[0]
            eigenvalues = np.linalg.eigvalsh([[2*coeff[4], coeff[3]], [coeff[3], 2*coeff[5]]])
            finite = bool(np.isfinite(center).all())
            sep = float(position.separation(cut.wcs.pixel_to_world(*center)).arcsec) if finite else None
            row = {"filter": filt, "cal_ver": h[0].header.get("CAL_VER"),
                   "crds": h[0].header.get("CRDS_CTX"), "bunit": h["SCI"].header.get("BUNIT"),
                   "image_shape": list(image.shape), "pixel_scale_arcsec": float(scale),
                   "cutout_finite_pixels": int(np.isfinite(cut.data).sum()), "cutout_pixels": int(cut.data.size),
                   "quadratic_patch_finite_pixels": int(np.isfinite(patch).sum()),
                   "ring_peak_sigma": float(d[iy, ix]/np.std(cut.data[annulus])),
                   "ring_peak_radius_arcsec": float(radius[iy, ix]),
                   "centroid_finite": finite, "separation_arcsec_diagnostic": sep,
                   "quadratic_hessian_eigenvalues": eigenvalues.tolist(),
                   "quadratic_is_local_maximum": bool(np.all(eigenvalues < 0)),
                   "centroid_warnings": [str(m.message) for m in messages],
                   "separation_over_nominal_psf_fwhm": sep/frozen.JDOX[filt] if finite else None}
            if finite:
                gx, gy = center
                vx, vy = gx-x0, gy-y0
                for label, cx, cy, away in (("star", x0, y0, (xx-x0)*vx+(yy-y0)*vy < 0),
                                            ("second", gx, gy, (xx-gx)*(-vx)+(yy-gy)*(-vy) < 0)):
                    r, prof = frozen.profile(d, cx, cy, scale, away, rmax=1., dr=.0555)
                    width = frozen.fwhm_of(r, prof)
                    row[label+"_fwhm_arcsec"] = finite_or_none(width)
                    row["separation_over_"+label+"_fwhm"] = finite_or_none(sep/width)
            rows.append(row)
    log = logpath.read_text(encoding="utf-8")
    fluxpairs = re.findall(r"star\s+([-\d.]+) uJy .*?second\s+([-\d.]+) uJy", log)
    measured = [(float(s), float(c)) for s, c in fluxpairs]
    result = {"status": execution_status(run["returncode"], rows), "frozen_execution": run,
              "scientific_scripts_changed": False, "four_outcome_branch_assigned": False,
              "validated_contrast_available": False, "discovery_claim": False,
              "release_report_sha256": digest(ROOT / "out/e-release-20260912.json"),
              "executed_script_sha256": digest(ROOT / "scripts/m5_jwst_target.py"),
              "audit_script_sha256": digest(Path(__file__)), "inputs": inputs, "per_filter": rows,
              "completed_aperture_pairs_in_failed_run": len(measured),
              "negative_completed_aperture_pairs": sum(s < 0 or c < 0 for s, c in measured),
              "mrs_negative_slice_fraction": None,
              "limit": "M7 MRS negative-slice fractions are not imaging-aperture fractions. No E MRS extraction performed."}
    if args.replay:
        prior = json.loads(OUT.read_bytes())
        if result != prior:
            raise ValueError("E execution audit replay differs")
        print("E failure/validity audit replay PASS")
    else:
        with OUT.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({"status": result["status"], "per_filter": rows}, indent=2))


if __name__ == "__main__":
    main()
