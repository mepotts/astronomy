"""Prospective, bounded pixel/background controls. No unknown-target mode."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time
from astropy.wcs import WCS
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/m1"
PROTOCOL = ROOT / "M1-PROTOCOL-2026-09-12.md"
RUNNER = ROOT.parent / "dyson-revet/scripts/check_e_release.py"
CONTROLS = {450781262: (99, 48_807_360), 53206761: (72, 44_818_560),
            2041210548: (57, 50_742_720)}
MAX_PIXEL_BYTES = 65_000_000
MAX_CATALOG_BYTES = 5_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(clean(value), stream, indent=2, allow_nan=False)
        stream.write("\n")


def read_solution(tic):
    path = ROOT / "out" / f"m0b-{tic}.json"
    result = json.loads(path.read_bytes())
    if not result["grade"]["passed"] or result["script_sha256"] != sha(ROOT / "scripts/m0.py"):
        raise ValueError("STOP_M0B_PROVENANCE")
    expected = {"protocol_sha256": ROOT / "M0b-PROTOCOL-2026-09-12.md",
                "base_protocol_sha256": ROOT / "M0-PROTOCOL-2026-09-12.md",
                "runner_sha256": RUNNER}
    if any(result[key] != sha(value) for key, value in expected.items()):
        raise ValueError("STOP_M0B_PROVENANCE")
    receipt = result["input"]
    lc = ROOT / receipt["input_path"] if "input_path" in receipt else ROOT / "data/m0b" / str(tic) / receipt["filename"]
    if sha(lc) != receipt["sha256"]:
        raise ValueError("STOP_LC_HASH")
    return result, lc


def provenance(tic):
    return {"tic": tic, "protocol_sha256": sha(PROTOCOL), "script_sha256": sha(__file__),
            "runner_sha256": sha(RUNNER), "m0b_result_sha256": sha(ROOT / "out" / f"m0b-{tic}.json")}


def bounded_worker(stage, tic):
    spec = importlib.util.spec_from_file_location("m1_bounded_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import sys
    limit = {"fetch": 90, "catalog": 60, "analyze": 600}[stage]
    return module.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()), stage,
                               "--worker", str(tic)], limit)


def stream_response(response, path, maximum, deadline):
    response.raise_for_status()
    if int(response.headers.get("Content-Length", 0)) > maximum:
        raise ValueError("STOP_SIZE")
    total = 0
    with path.open("xb") as stream:
        for chunk in response.iter_content(65536):
            total += len(chunk)
            if total > maximum or time.monotonic() > deadline:
                raise ValueError("STOP_TRANSFER_LIMIT")
            stream.write(chunk)
    return total


def fetch(tic):
    import requests
    result, _ = read_solution(tic)
    rows = Table.read(ROOT / "data/m0b" / str(tic) / "products.ecsv", format="ascii.ecsv")
    name = result["input"]["filename"].replace("_lc.fits", "_tp.fits")
    selected = [r for r in rows if str(r["productFilename"]) == name
                and str(r["productSubGroupDescription"]) == "TP"
                and str(r["productType"]) == "SCIENCE" and str(r["dataRights"]) == "PUBLIC"
                and int(r["obsID"]) == result["input"]["obsid"]]
    if len(selected) != 1 or int(selected[0]["size"]) != CONTROLS[tic][1]:
        raise ValueError("STOP_TP_SELECTION")
    if sum(v[1] for v in CONTROLS.values()) + 3 * MAX_CATALOG_BYTES > 200_000_000:
        raise ValueError("STOP_TOTAL_BYTES")
    if Path(name).name != name or "/" in name or "\\" in name or ":" in name:
        raise ValueError("STOP_UNSAFE_PATH")
    uri = str(selected[0]["dataURI"])
    if uri != "mast:TESS/product/" + name:
        raise ValueError("STOP_URI")
    folder = DATA / str(tic)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    url = "https://mast.stsci.edu/api/v0.1/Download/file?uri=" + quote(uri, safe=":/")
    save(folder / "fetch-plan.json", {**provenance(tic), "filename": name,
                                     "bytes": int(selected[0]["size"]), "url": url})
    with requests.get(url, stream=True, timeout=(15, 45)) as response:
        size = stream_response(response, path, MAX_PIXEL_BYTES, time.monotonic() + 85)
    if size != int(selected[0]["size"]):
        raise ValueError("STOP_SIZE_MISMATCH")
    with fits.open(path) as hdus:
        check_header(hdus, tic)
    save(folder / "receipt.json", {**provenance(tic), "filename": name, "bytes": size,
                                  "sha256": sha(path), "url": url,
                                  "retrieved_utc": datetime.now(timezone.utc).isoformat()})


def catalog(tic):
    import requests
    _, lc = read_solution(tic)
    with fits.open(lc) as hdus:
        ra, dec = hdus[0].header["RA_OBJ"], hdus[0].header["DEC_OBJ"]
    query = ("SELECT TOP 5001 source_id,ra,dec,ref_epoch,pmra,pmdec,phot_g_mean_mag,ruwe "
             "FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
             f"CIRCLE('ICRS',{ra:.12f},{dec:.12f},0.05)) ORDER BY source_id")
    folder = DATA / str(tic)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "gaia-dr3.xml"
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    save(folder / "catalog-query.json", {**provenance(tic), "url": url, "adql": query,
                                        "utc": datetime.now(timezone.utc).isoformat()})
    with requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
                                  "QUERY": query}, stream=True, timeout=(15, 45)) as response:
        size = stream_response(response, path, MAX_CATALOG_BYTES, time.monotonic() + 55)
    table = Table.read(path, format="votable")
    if len(table) >= 5001 or b'OVERFLOW' in path.read_bytes() or len(table) == 0:
        raise ValueError("STOP_CATALOG_COMPLETENESS")
    save(folder / "catalog-receipt.json", {**provenance(tic), "bytes": size, "rows": len(table),
                                          "sha256": sha(path), "complete_response": True})


def check_header(hdus, tic):
    primary, header = hdus[0].header, hdus[1].header
    if int(primary["TICID"]) != tic or int(primary["SECTOR"]) != CONTROLS[tic][0]:
        raise ValueError("STOP_PRODUCT_IDENTITY")
    if (header["TIMEUNIT"] != "d" or header["TIMESYS"] != "TDB"
            or header["BJDREFI"] != 2457000 or header.get("BJDREFF", 0) != 0
            or not np.isclose(header["TIMEDEL"] * 86400, 120, rtol=1e-4)):
        raise ValueError("STOP_TIME_REFERENCE")
    if hdus[1].columns["FLUX"].unit != "e-/s" or hdus[1].columns["FLUX_BKG"].unit != "e-/s":
        raise ValueError("STOP_FLUX_UNITS")


def window_mean(t, cube, errors, mask):
    values, uncertainty = cube[mask], errors[mask]
    valid = np.isfinite(values) & np.isfinite(uncertainty) & (uncertainty > 0)
    weights = np.zeros_like(uncertainty, dtype=float)
    np.divide(1, uncertainty**2, out=weights, where=valid)
    total = weights.sum(axis=0)
    good = (valid.sum(axis=0) >= 2) & (total > 0)
    mean = np.full(total.shape, np.nan)
    mean_time = np.full(total.shape, np.nan)
    np.divide(np.where(valid, values, 0).__mul__(weights).sum(axis=0), total, out=mean, where=good)
    np.divide((t[mask, None, None] * weights).sum(axis=0), total, out=mean_time, where=good)
    return mean, mean_time


def paired_events(t, cube, errors, period, epoch, duration, offset=0):
    epoch += offset * period
    cycles = np.arange(int(np.floor((t.min() - epoch) / period)),
                       int(np.ceil((t.max() - epoch) / period)) + 1)
    images, centers = [], []
    for cycle in cycles:
        center = epoch + cycle * period
        delta = t - center
        masks = [np.abs(delta) < duration / 2,
                 (delta >= -2.5 * duration) & (delta <= -1.5 * duration),
                 (delta >= 1.5 * duration) & (delta <= 2.5 * duration)]
        if any(np.count_nonzero(mask) < 2 for mask in masks):
            continue
        (inside, ti), (left, tl), (right, tr) = [window_mean(t, cube, errors, m) for m in masks]
        with np.errstate(invalid="ignore", divide="ignore"):
            alpha = (ti - tl) / (tr - tl)
            difference = (1 - alpha) * left + alpha * right - inside
        difference[(alpha < 0) | (alpha > 1)] = np.nan
        images.append(difference)
        centers.append(center)
    if len(images) < 20:
        raise ValueError("STOP_PAIRED_EVENTS")
    return np.asarray(centers), np.asarray(images)


def day_blocks(centers, images, anchor):
    labels = np.floor(centers - anchor).astype(int)
    unique = np.unique(labels)
    if len(unique) < 10:
        raise ValueError("STOP_DAY_COVERAGE")
    return np.array([images[labels == value].mean(axis=0) for value in unique]), unique


def block_statistics(blocks, aperture):
    values = blocks[:, aperture].sum(axis=1)
    error = float(values.std(ddof=1) / np.sqrt(len(values)))
    return {"amplitude": float(values.mean()), "error": error,
            "snr": float(values.mean() / error) if error > 0 else None,
            "blocks": len(values)}


def gaussian_plane(parameters, xx, yy):
    amplitude, cx, cy, sx, sy, angle, base, slope_x, slope_y = parameters
    dx, dy = xx - cx, yy - cy
    xp = dx * np.cos(angle) + dy * np.sin(angle)
    yp = -dx * np.sin(angle) + dy * np.cos(angle)
    return amplitude * np.exp(-0.5 * ((xp / sx)**2 + (yp / sy)**2)) + base + slope_x * xx + slope_y * yy


def fit_centroid(image, error, pixels):
    yy, xx = np.indices(image.shape)
    valid = pixels & np.isfinite(image) & np.isfinite(error) & (error > 0)
    if valid.sum() < 25:
        return {"success": False, "reason": "STOP_FIT_PIXELS"}
    peak = np.unravel_index(np.argmax(np.where(valid, image, -np.inf)), image.shape)
    base = float(np.median(image[valid]))
    initial = [max(float(image[peak] - base), 1e-10), float(peak[1]), float(peak[0]),
               1., 1., 0., base, 0., 0.]
    lower = [0, -.5, -.5, .4, .4, -np.inf, -np.inf, -np.inf, -np.inf]
    upper = [np.inf, image.shape[1] - .5, image.shape[0] - .5, 3., 3., np.inf,
             np.inf, np.inf, np.inf]
    result = least_squares(lambda p: (gaussian_plane(p, xx, yy)[valid] - image[valid]) / error[valid],
                           initial, bounds=(lower, upper), max_nfev=300)
    success = bool(result.success and np.all(np.isfinite(result.x)))
    bound_hit = bool(np.any(result.active_mask != 0))
    result.x[5] = (result.x[5] + np.pi / 2) % np.pi - np.pi / 2
    return {"success": success, "bound_hit": bound_hit, "x": float(result.x[1]),
            "y": float(result.x[2]), "parameters": result.x,
            "descriptive_reduced_residual": float(np.sum(result.fun**2) / (valid.sum() - len(initial))),
            "evaluations": result.nfev}


def catalog_comparison(tic, wcs, target, center, epoch, shape):
    folder = DATA / str(tic)
    if not (folder / "catalog-receipt.json").exists():
        return {"status": "STOP_CATALOG_UNAVAILABLE", "clean": False}
    receipt = json.loads((folder / "catalog-receipt.json").read_bytes())
    path = folder / "gaia-dr3.xml"
    if sha(path) != receipt["sha256"]:
        raise ValueError("STOP_CATALOG_HASH")
    table = Table.read(path, format="votable")
    rows = []
    for row in table:
        ra, dec = float(row["ra"]), float(row["dec"])
        pmra = float(row["pmra"]) if not np.ma.is_masked(row["pmra"]) else np.nan
        pmdec = float(row["pmdec"]) if not np.ma.is_masked(row["pmdec"]) else np.nan
        motion_known = bool(np.isfinite(pmra) and np.isfinite(pmdec))
        if motion_known:
            elapsed = epoch - float(row["ref_epoch"])
            ra += elapsed * pmra / (3.6e6 * np.cos(np.deg2rad(dec)))
            dec += elapsed * pmdec / 3.6e6
        x, y = wcs.world_to_pixel_values(ra, dec)
        if not (-.5 <= x <= shape[1] - .5 and -.5 <= y <= shape[0] - .5):
            continue
        separation = float(SkyCoord(ra, dec, unit="deg").separation(SkyCoord(*target, unit="deg")).arcsec)
        rows.append({"source_id": str(row["source_id"]), "x": float(x), "y": float(y),
                     "g_mag": float(row["phot_g_mean_mag"]), "proper_motion_known": motion_known,
                     "target_separation_arcsec": separation,
                     "centroid_separation_pixels": float(np.hypot(x - center[0], y - center[1]))})
    matches = [r for r in rows if r["target_separation_arcsec"] <= 2.]
    provisional = matches[0]["source_id"] if len(matches) == 1 else None
    nearby = [r for r in rows if r["centroid_separation_pixels"] <= 1.]
    competitors = [r for r in nearby if r["source_id"] != provisional]
    clean_catalog = len(matches) == 1 and not competitors and all(r["proper_motion_known"] for r in nearby)
    return {"status": "CATALOG_CONSISTENT_DIAGNOSTIC" if clean_catalog else "CATALOG_UNRESOLVED",
            "clean": clean_catalog, "provisional_target_id": provisional,
            "target_matches": matches, "competitors_within_one_pixel": competitors,
            "rows_in_stamp": rows, "receipt": receipt,
            "epoch_jyear": epoch, "unresolved_or_uncatalogued_sources_excluded": False}


def analyze(tic):
    import astropy
    import scipy
    result, lc_path = read_solution(tic)
    receipt = json.loads((DATA / str(tic) / "receipt.json").read_bytes())
    path = DATA / str(tic) / receipt["filename"]
    if sha(path) != receipt["sha256"]:
        raise ValueError("STOP_TP_HASH")
    with fits.open(path) as tp, fits.open(lc_path) as lc:
        check_header(tp, tic)
        td, ld = tp[1].data, lc[1].data
        if any(len(np.unique(d["CADENCENO"])) != len(d) for d in (td, ld)):
            raise ValueError("STOP_DUPLICATE_CADENCES")
        lgood = (np.isfinite(ld["TIME"]) & np.isfinite(ld["PDCSAP_FLUX"])
                 & np.isfinite(ld["PDCSAP_FLUX_ERR"]) & (ld["PDCSAP_FLUX_ERR"] > 0)
                 & (ld["QUALITY"] == 0))
        tgood = np.isfinite(td["TIME"]) & (td["QUALITY"] == 0)
        _, li, ti = np.intersect1d(ld["CADENCENO"][lgood], td["CADENCENO"][tgood], return_indices=True)
        li, ti = np.flatnonzero(lgood)[li], np.flatnonzero(tgood)[ti]
        t = np.asarray(td["TIME"][ti], dtype=float)
        if len(t) < 1000 or np.any(np.diff(t) <= 0) or np.max(np.abs(t - ld["TIME"][li])) > 1e-7:
            raise ValueError("STOP_CADENCE_ALIGNMENT")
        flux, errors, bkg, bkg_errors = (np.asarray(td[k][ti], dtype=float) for k in
                                        ("FLUX", "FLUX_ERR", "FLUX_BKG", "FLUX_BKG_ERR"))
        aperture = (tp[2].data.astype(int) & 2) > 0
        collected = (tp[2].data.astype(int) & 1) > 0
        sap = np.asarray(ld["SAP_FLUX"][li], dtype=float)
        reconstructed = flux[:, aperture].sum(axis=1)
        if not np.allclose(reconstructed, sap, atol=1e-3, rtol=1e-5, equal_nan=False):
            raise ValueError("STOP_SAP_REPRODUCTION")
        wcs = WCS(tp[2].header)
        target = (float(tp[0].header["RA_OBJ"]), float(tp[0].header["DEC_OBJ"]))
        target_xy = tuple(float(v) for v in wcs.world_to_pixel_values(*target))
        header_info = {k: tp[0].header.get(k) for k in ("TICID", "SECTOR", "CAMERA", "CCD", "PROCVER")}
        crowd = float(lc[1].header["CROWDSAP"])
        fraction = float(lc[1].header["FLFRCSAP"])
    sol = result["solution"]
    args = (sol["period"], sol["transit_time"], sol["duration"])
    centers, events = paired_events(t, flux, errors, *args)
    pixels = collected & np.all(np.isfinite(events), axis=0)
    if pixels.sum() < 25 or not np.all(pixels[aperture]):
        raise ValueError("STOP_PIXEL_COVERAGE")
    blocks, labels = day_blocks(centers, events, t.min())
    primary = block_statistics(blocks, aperture)
    image = blocks.mean(axis=0)
    error = blocks.std(axis=0, ddof=1) / np.sqrt(len(blocks))
    fit = fit_centroid(image, error, pixels)
    flags = []
    if primary["snr"] is None or primary["snr"] < 5:
        flags.append("PRIMARY_LOW_BLOCK_SNR")
    bc, be = paired_events(t, bkg, bkg_errors, *args)
    bb, _ = day_blocks(bc, be, t.min())
    background = block_statistics(bb, aperture)
    if background["snr"] is None:
        flags.append("BACKGROUND_ERROR_UNDEFINED")
    elif abs(background["snr"]) >= 3 and abs(background["amplitude"]) > .1 * abs(primary["amplitude"]):
        flags.append("BACKGROUND_COHERENCE")
    phase_controls = []
    for offset in (.25, .75):
        oc, oe = paired_events(t, flux, errors, *args, offset=offset)
        ob, _ = day_blocks(oc, oe, t.min())
        stats = block_statistics(ob, aperture)
        phase_controls.append({"offset_periods": offset, **stats})
        if stats["snr"] is None or abs(stats["snr"]) >= 3:
            flags.append("PHASE_CONTROL_STRUCTURE")
    boot = []
    rng = np.random.default_rng(20260912)
    if fit["success"]:
        for _ in range(250):
            indices = rng.integers(0, len(blocks), len(blocks))
            boot_fit = fit_centroid(blocks[indices].mean(axis=0), error, pixels)
            if boot_fit["success"] and not boot_fit["bound_hit"]:
                boot.append([boot_fit["x"], boot_fit["y"]])
        spread = float(np.quantile(np.linalg.norm(np.array(boot) - [fit["x"], fit["y"]], axis=1), .95)) if boot else None
        distance = float(np.hypot(fit["x"] - target_xy[0], fit["y"] - target_xy[1]))
        if fit["bound_hit"] or len(boot) < 225 or spread is None or spread > .5:
            flags.append("CENTROID_UNSTABLE_OR_BOUND")
        if distance > .75:
            flags.append("COARSE_CENTROID_OFF_TARGET")
        neighbors = catalog_comparison(tic, wcs, target, (fit["x"], fit["y"]),
                                       Time(2457000 + (t.min() + t.max()) / 2, format="jd", scale="tdb").jyear,
                                       image.shape)
    else:
        spread, distance = None, None
        flags.append("CENTROID_FIT_FAILED")
        neighbors = {"clean": False, "status": "NO_CENTROID"}
    if not neighbors["clean"]:
        flags.append("CATALOG_CONFUSION_UNRESOLVED")
    calibration = {"sap_reproduction_max_abs_e_per_s": float(np.max(np.abs(reconstructed - sap))),
                   "sap_median": float(np.median(reconstructed)),
                   "sap_negative_fraction": float(np.mean(reconstructed < 0)),
                   "background_sum_median": float(np.median(bkg[:, aperture].sum(axis=1))),
                   "calibrated_pre_background_sum_median": float(np.median((flux + bkg)[:, aperture].sum(axis=1))),
                   "crowdsap": crowd, "flfrcsap": fraction,
                   "physical_fractional_depth_validated": False}
    yy, xx = np.indices(image.shape)
    model = gaussian_plane(fit["parameters"], xx, yy) if fit["success"] else np.full(image.shape, np.nan)
    output = {**provenance(tic), "status": "CONTROL_CHARACTERIZED_NEEDS_PRF_AND_EMPIRICAL_NULL",
              "unknown_search_authorized": False, "input": receipt, "headers": header_info,
              "points": len(t), "paired_events": len(events), "day_labels": labels,
              "pixels": int(pixels.sum()), "aperture_pixels": int(aperture.sum()),
              "target_header_radec": target, "target_xy_zero_based": target_xy,
              "primary": primary, "background": background, "phase_controls": phase_controls,
              "centroid_surrogate": fit, "centroid_target_distance_pixels": distance,
              "bootstrap_valid": len(boot), "bootstrap_total": 250,
              "bootstrap_radial_95_pixels": spread, "bootstrap_xy": boot,
              "catalog": neighbors, "calibration": calibration,
              "coarse_target_consistent_diagnostic": not flags, "flags": sorted(set(flags)),
              "images": {"difference": image, "block_standard_error": error,
                         "background_difference": bb.mean(axis=0), "gaussian_plane_model": model,
                         "residual": image - model, "valid_pixels": pixels, "aperture": aperture},
              "versions": {"numpy": np.__version__, "astropy": astropy.__version__, "scipy": scipy.__version__}}
    save(ROOT / "out" / f"m1-{tic}.json", output)
    print(json.dumps(clean({k: output[k] for k in ("tic", "paired_events", "primary", "centroid_target_distance_pixels",
                                                  "bootstrap_radial_95_pixels", "flags")})), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fetch", "catalog", "analyze"])
    parser.add_argument("--worker", type=int, choices=list(CONTROLS))
    args = parser.parse_args()
    if args.worker:
        {"fetch": fetch, "catalog": catalog, "analyze": analyze}[args.stage](args.worker)
        return
    outcomes = []
    for tic in CONTROLS:
        code, output = bounded_worker(args.stage, tic)
        row = {"tic": tic, "returncode": code, "output": output}
        outcomes.append(row)
        print(json.dumps(row), flush=True)
    save(DATA / f"{args.stage}-run.json", {"utc": datetime.now(timezone.utc).isoformat(),
                                         "outcomes": outcomes, "script_sha256": sha(__file__),
                                         "protocol_sha256": sha(PROTOCOL)})
    if any(r["returncode"] != 0 for r in outcomes):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
