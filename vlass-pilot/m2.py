"""M2 common-beam calibration on retained data only. No network code."""

import argparse
import gc
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from scipy.signal import fftconvolve

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("m2_frozen_full_plane", ROOT/"full_plane.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)
P = F.P
SIGMA = 3.5 / math.sqrt(8*math.log(2))
BEAM_AREA = 2*math.pi*SIGMA**2
START = time.monotonic()


def limits():
    if time.monotonic()-START > 1800:
        raise RuntimeError("M2 30-minute compute cap")
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "peak", "working", "quota_peak_paged", "quota_paged",
                    "quota_peak_nonpaged", "quota_nonpaged", "pagefile", "peak_pagefile")]
        record = Counters()
        record.cb = ctypes.sizeof(record)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        library = ctypes.WinDLL("psapi", use_last_error=True)
        library.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
        if not library.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(record), record.cb):
            raise RuntimeError("Cannot enforce process memory bound")
        if record.peak > 2_000_000_000:
            raise RuntimeError("M2 2 GB peak-memory cap")
        return int(record.peak)
    raise RuntimeError("This M2 memory-cap implementation was validated for Windows only")


def save(name, value):
    encoded = json.dumps(value, indent=2, allow_nan=False)+"\n"
    existing = sum(path.stat().st_size for path in ROOT.glob("m2-*.json") if path.name != name)
    encoded_bytes = len(encoded.encode()) + (encoded.count("\n") if os.name == "nt" else 0)
    if existing + encoded_bytes > 200_000_000:
        raise RuntimeError("M2 output cap")
    (ROOT/name).write_text(encoded)


def epochs_metadata():
    manifest = json.loads((ROOT/"full-plane-acquisition.json").read_text())
    result = []
    for campaign in P.CAMPAIGNS[1:]:
        rows = [row for row in manifest["records"] if row["campaign"] == campaign]
        entry = {key: rows[0][key] for key in ("campaign", "obs_id", "t_min", "t_max")}
        entry.update({row["kind"]: row["path"] for row in rows})
        result.append(entry)
    return result, manifest


def freeze():
    if (ROOT/"m2-plan.json").exists():
        raise ValueError("M2 positions already frozen")
    entries, manifest = epochs_metadata()
    header = fits.getheader(ROOT/entries[1]["image"])
    wcs = WCS(header).celestial
    positions = []
    for i in range(200):
        row, col = divmod(i, 14)
        x, y = 200+240*col, 200+240*row
        ra, dec = map(float, wcs.all_pix2world(x, y, 0))
        positions.append({"id": i, "x": x, "y": y, "ra": ra, "dec": dec,
                          "row": row, "col": col, "block": f"{row//3}:{col//3}",
                          "split": "development" if (row//3+col//3)%2 == 0 else "heldout",
                          "flux_jy": [.0003, .0005, .001, .003, .01][i%5]})
    plan = {"protocol_sha256": P.sha(ROOT/"m2-protocol.md"),
            "full_manifest_sha256": P.sha(ROOT/"full-plane-acquisition.json"),
            "full_result_sha256": P.sha(ROOT/"full-plane-measurement.json"),
            "reference_header_sha256": __import__("hashlib").sha256(header.tostring().encode()).hexdigest(),
            "input_hashes": {rec["path"]: rec["sha256"] for rec in manifest["records"]},
            "positions": positions}
    save("m2-plan.json", plan)
    print("FROZEN", len(positions), {s: sum(p["split"] == s for p in positions)
                                   for s in ("development", "heldout")})


def jacobian(wcs, ra, dec):
    x, y = map(float, wcs.all_world2pix(ra, dec, 0))
    target = SkyCoord(ra, dec, unit="deg")
    coordinates = wcs.all_pix2world([[x, y], [x+1, y], [x, y+1]], 0)
    sky = SkyCoord(coordinates[:, 0], coordinates[:, 1], unit="deg")
    east, north = target.spherical_offsets_to(sky)
    matrix = np.array([[east[1].arcsec-east[0].arcsec, east[2].arcsec-east[0].arcsec],
                       [north[1].arcsec-north[0].arcsec, north[2].arcsec-north[0].arcsec]])
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-8:
        raise ValueError("Invalid local celestial Jacobian")
    return matrix


def covariance(header):
    theta = np.deg2rad(header["BPA"])
    rotation = np.array([[np.sin(theta), np.cos(theta)], [np.cos(theta), -np.sin(theta)]])
    sigma = np.array([header["BMAJ"], header["BMIN"]])*3600/math.sqrt(8*math.log(2))
    return rotation @ np.diag(sigma**2) @ rotation.T


def kernel(header, matrix):
    difference = np.eye(2)*SIGMA**2-covariance(header)
    if np.min(np.linalg.eigvalsh(difference)) <= 0:
        raise ValueError("Common beam cannot sharpen native image")
    inverse = np.linalg.inv(matrix)
    pixels = inverse @ difference @ inverse.T
    radius = math.ceil(8*math.sqrt(np.max(np.linalg.eigvalsh(pixels))))
    yy, xx = np.mgrid[-radius:radius+1, -radius:radius+1]
    offsets = np.array([xx, yy])
    model = np.exp(-.5*np.einsum("ikl,ij,jkl->kl", offsets, np.linalg.inv(pixels), offsets))
    model /= model.sum()
    return model, radius


def point_model(wcs, header, shape, ra, dec):
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    coords = wcs.all_pix2world(np.column_stack([xx.ravel(), yy.ravel()]), 0)
    target = SkyCoord(ra, dec, unit="deg")
    sky = SkyCoord(coords[:, 0], coords[:, 1], unit="deg")
    east, north = target.spherical_offsets_to(sky)
    offsets = np.array([east.arcsec.reshape(shape), north.arcsec.reshape(shape)])
    return np.exp(-.5*np.einsum("ikl,ij,jkl->kl", offsets, np.linalg.inv(covariance(header)), offsets))


def patch(epoch, ra, dec):
    x, y = map(float, epoch["wcs"].all_world2pix(ra, dec, 0))
    ix, iy = round(x), round(y)
    startx, starty = ix-44, iy-44
    if startx < 0 or starty < 0 or ix+44 >= epoch["array"].shape[1] or iy+44 >= epoch["array"].shape[0]:
        raise ValueError("M2 patch exceeds parent-plane edge")
    array = epoch["array"][starty:iy+45, startx:ix+45].copy()
    rms = epoch["rms"][starty:iy+45, startx:ix+45].copy()
    if not np.isfinite(array).all() or not np.isfinite(rms).all() or np.any(rms <= 0):
        raise ValueError("M2 nonfinite data/invalid RMS patch")
    wcs = epoch["wcs"].deepcopy()
    wcs.wcs.crpix -= [startx, starty]
    return {"array": array, "rms": rms, "wcs": wcs, "header": epoch["header"].copy(),
            "matrix": np.asarray(wcs.pixel_scale_matrix)*3600}


def common(native, ra, dec, flux=0, injection_position=None):
    matrix = jacobian(native["wcs"], ra, dec)
    convolution, radius = kernel(native["header"], matrix)
    if radius+math.ceil(30/min(np.linalg.svd(matrix)[1]))+1 > 43:
        raise ValueError("Insufficient uncontaminated convolution support")
    if native["header"].get("BUNIT", "").strip().lower() != "jy/beam":
        raise ValueError("M2 requires Jy/beam")
    array = native["array"].copy()
    if flux:
        source_ra, source_dec = injection_position or (ra, dec)
        array += flux*point_model(native["wcs"], native["header"], array.shape, source_ra, source_dec)
    native_area = 2*math.pi*math.sqrt(np.linalg.det(covariance(native["header"])))
    pixel_area = abs(np.linalg.det(matrix))
    transformed = fftconvolve(array*pixel_area/native_area, convolution, mode="same")*BEAM_AREA/pixel_area
    header = native["header"].copy()
    header["BMAJ"] = header["BMIN"] = 3.5/3600
    header["BPA"] = 0.
    x, y = native["wcs"].all_world2pix(ra, dec, 0)
    yy, xx = np.mgrid[:array.shape[0], :array.shape[1]]
    east, north = np.einsum("ij,jkl->ikl", matrix, np.array([xx-x, yy-y]))
    distance = np.hypot(east, north)
    background = transformed[(distance >= 15) & (distance <= 25)]
    noise = float(1.4826*np.median(np.abs(background-np.median(background))))
    if not np.isfinite(noise) or noise <= 0:
        raise ValueError("M2 background MAD undefined")
    result = {"array": transformed, "rms": np.full_like(array, noise), "wcs": native["wcs"],
              "header": header, "matrix": matrix}
    return result, {"kernel_radius_pixels": radius, "kernel_sum": float(convolution.sum()),
                    "local_jacobian": matrix.tolist(), "native_beam_area_arcsec2": native_area}


def stats(values):
    a = np.array(values, dtype=float)
    if not len(a):
        return {"n": 0, "median": None, "mad": None, "max_abs": None, "tail5": None}
    median = float(np.median(a))
    return {"n": len(a), "median": median, "mad": float(1.4826*np.median(np.abs(a-median))),
            "max_abs": float(np.max(np.abs(a))), "tail5": int(np.sum(np.abs(a) >= 5))}


def insertion_rank(peak, baseline):
    return 1+sum(value >= peak for value in baseline)


def local_maximum(array, x, y):
    return bool(array[y, x] == np.max(array[y-10:y+11, x-10:x+11]))


def numerical_tests(entries):
    trials = []
    for entry in entries:
        h = fits.getheader(ROOT/entry["image"])
        wcs = WCS(h).celestial
        for x0, y0 in [(1861, 1861), (200, 200), (3500, 200), (200, 3500), (3500, 3500)]:
            for dx in [0, .25, .5, .75]:
                for dy in [0, .25, .5, .75]:
                    ra, dec = map(float, wcs.all_pix2world(x0+dx, y0+dy, 0))
                    pwcs = wcs.deepcopy()
                    pwcs.wcs.crpix -= [x0-44, y0-44]
                    native = {"array": np.zeros((89, 89)), "rms": np.ones((89, 89)),
                              "wcs": pwcs, "header": h, "matrix": pwcs.pixel_scale_matrix*3600}
                    # A vanishing flat background leaves a positive numerical MAD;
                    # no stochastic uncertainty claim is made for noiseless tests.
                    native["array"] = point_model(pwcs, h, (89, 89), ra, dec)
                    transformed, diagnostic = common(native, ra, dec)
                    template = point_model(pwcs, transformed["header"], (89, 89), ra, dec)
                    amplitude = P.amplitude(transformed["array"], template, 0)
                    fixed_measurement = P.photometry(transformed, ra, dec)
                    peak = np.unravel_index(np.argmax(transformed["array"]), (89, 89))
                    pra, pdec = pwcs.all_pix2world(peak[1], peak[0], 0)
                    offset = float(SkyCoord(ra, dec, unit="deg").separation(
                        SkyCoord(pra, pdec, unit="deg")).arcsec)
                    trials.append({"campaign": entry["campaign"], "pixel": [x0, y0],
                                   "phase": [dx, dy], "amplitude": amplitude,
                                   "fixed_estimator_amplitude": fixed_measurement["amplitude_jy"],
                                   "offset_arcsec": offset, "kernel_sum": diagnostic["kernel_sum"]})
    passed = all(abs(t["amplitude"]-1) <= .01
                 and abs(t["fixed_estimator_amplitude"]-1) <= .01 and t["offset_arcsec"] <= 1
                 and abs(t["kernel_sum"]-1) <= 1e-12 for t in trials)
    return {"passed": passed, "trials": trials}


def screen_reference(epoch, positions, references):
    # Exact original selection identity is checked before isolated insertion ranks.
    baseline = P.ensemble_positions(epoch)
    if not np.allclose(baseline, references, rtol=0, atol=1e-12):
        raise ValueError("Original global top-12 reference identity changed")
    baseline_peaks = []
    for ra, dec in references:
        x, y = map(float, epoch["wcs"].all_world2pix(ra, dec, 0))
        baseline_peaks.append(float(epoch["array"][round(y), round(x)]))
    protected = SkyCoord([P.TARGET, *references], unit="deg")
    output = []
    for position in positions:
        record = {**position, "screen_reasons": [], "selection": None}
        sky = SkyCoord(position["ra"], position["dec"], unit="deg")
        if np.min(sky.separation(protected).arcsec) < 45:
            record["screen_reasons"].append("PROTECTED_POSITION")
        if min(position["x"], position["y"], epoch["array"].shape[1]-1-position["x"],
               epoch["array"].shape[0]-1-position["y"]) < 45:
            record["screen_reasons"].append("REFERENCE_EDGE")
        try:
            native = patch(epoch, position["ra"], position["dec"])
            x, y = native["wcs"].all_world2pix(position["ra"], position["dec"], 0)
            yy, xx = np.mgrid[:89, :89]
            east, north = np.einsum("ij,jkl->ikl", native["matrix"], np.array([xx-x, yy-y]))
            near = np.hypot(east, north) <= 15
            if np.any((native["array"]/native["rms"])[near] >= 5):
                record["screen_reasons"].append("REFERENCE_PEAK_5")
        except ValueError as error:
            record["screen_reasons"].append("REFERENCE_INVALID_PATCH")
            record["screen_error"] = str(error)
        record["usable"] = not record["screen_reasons"]
        if record["usable"]:
            try:
                injected = {**native, "array": native["array"] + position["flux_jy"]*
                            point_model(native["wcs"], native["header"], (89, 89),
                                        position["ra"], position["dec"])}
                near = np.hypot(east, north) <= 3
                iy, ix = np.unravel_index(np.argmax(np.where(near, injected["array"], -np.inf)), (89, 89))
                peak = float(injected["array"][iy, ix])
                maximum = local_maximum(injected["array"], int(ix), int(iy))
                pra, pdec = map(float, native["wcs"].all_pix2world(ix, iy, 0))
                fitted = P.photometry(injected, pra, pdec)
                gx, gy = map(float, epoch["wcs"].all_world2pix(pra, pdec, 0))
                tx, ty = map(float, epoch["wcs"].all_world2pix(*P.TARGET, 0))
                scale = float(min(np.linalg.svd(epoch["matrix"])[1]))
                separated = all(math.hypot(gx-rx, gy-ry)*scale >= 20 for rx, ry in
                                [epoch["wcs"].all_world2pix(*ref, 0) for ref in references])
                geometry = (min(gx, gy, epoch["array"].shape[1]-1-gx,
                                epoch["array"].shape[0]-1-gy)*scale >= 45
                            and math.hypot(gx-tx, gy-ty)*scale >= 45 and separated)
                local_eligible = bool(maximum and peak/native["rms"][iy, ix] >= 15
                                      and peak < .1 and fitted["residual_over_noise"] <= 3 and geometry)
                rank = insertion_rank(peak, baseline_peaks)
                record["selection"] = {"local_maximum_21": maximum,
                    "local_eligible": local_eligible, "global_rank": rank,
                    "global_selected": local_eligible and rank <= 12,
                    "selected_ra": pra, "selected_dec": pdec, "selected_geometry_pass": geometry,
                    "native_reference_measurement": fitted}
            except ValueError as error:
                # Once original-data screening passes, injected-stage failure
                # stays in the experimental denominator and stops selection validity.
                record["selection_error"] = str(error)
        output.append(record)
    return output


def measured(epoch, ra, dec, flux=0, injection_position=None):
    native = patch(epoch, ra, dec)
    transformed, diagnostic = common(native, ra, dec, flux, injection_position)
    result = P.photometry(transformed, ra, dec)
    result["convolution"] = diagnostic
    return result


def morphology(value):
    return bool(value and "error" not in value and value["amplitude_over_noise"] >= 5
                and value["residual_over_noise"] <= 3 and value["peak_offset_arcsec"] <= 1.5)


def summarize(report, references):
    epochs = report["epochs"]
    screened = report["reference_screen"]
    failed = []
    if any(p["usable"] and p["selection"] is None for p in screened):
        failed.append("INVALID_INJECTED_SELECTION_TEST")
    if not all(ep["target"].get("recovered", False) for ep in epochs):
        failed.append("COMMON_TARGET_RECOVERY")
    if any("error" in item or abs(item["amplitude_over_noise"]) >= 5
           for ep in epochs for item in ep["fixed_nulls"]):
        failed.append("FIXED_NULL")
    good = [i for i in range(12) if all(morphology(ep["references"][i]) for ep in epochs)]
    report["morphology_reference_indices"] = good
    if len(good) < 5:
        failed.append("INSUFFICIENT_COMMON_MORPHOLOGY_REFERENCES")
    ordered = sorted(range(12), key=lambda i: references[i][0])
    halves = [[i for i in ordered[offset::2] if i in good] for offset in (0, 1)]
    report["fixed_reference_halves"] = halves
    if min(map(len, halves)) < 3:
        failed.append("INSUFFICIENT_REFERENCE_HALF")
    if len(good) >= 5 and min(map(len, halves)) >= 3:
        for ep in epochs:
            ratios = {i: ep["references"][i]["amplitude_jy"] /
                      epochs[1]["references"][i]["amplitude_jy"] for i in good}
            median = float(np.median(list(ratios.values())))
            half = [float(np.median([ratios[i] for i in group])) for group in halves]
            difference = abs(half[0]-half[1])/np.mean(half)
            leave = [float(np.median([v for key, v in ratios.items() if key != i])) for i in good]
            leave_difference = max(abs(value-median)/median for value in leave)
            ep["reference_scale"] = {"median": median, "half_medians": half,
                                      "half_relative_difference": float(difference),
                                      "leave_one_out": leave,
                                      "max_leave_one_out_relative_difference": leave_difference}
            if difference > .1:
                failed.append(ep["campaign"]+"_HALF_SCALE")
            if leave_difference > .05:
                failed.append(ep["campaign"]+"_LEAVE_ONE_OUT_SCALE")
    usable = [p["id"] for p in screened if p["usable"]]
    heldout = [i for i in usable if screened[i]["split"] == "heldout"]
    report["sample_accounting"] = {"planned": 200, "usable_reference_screen": len(usable),
        "excluded_reference_screen": 200-len(usable), "heldout_usable": len(heldout),
        "reference_screened_nulls_not_unconditional_sky": True}
    complete = [i for i in heldout if all("error" not in ep["grid"][i] for ep in epochs)]
    report["sample_accounting"]["heldout_complete"] = len(complete)
    if len(complete) < 60:
        failed.append("INSUFFICIENT_HELDOUT_CONTROLS")
    if len(complete) != len(heldout):
        failed.append("HELDOUT_MEASUREMENT_FAILURE")
    for ep in epochs:
        summaries = {}
        for split in ("development", "heldout"):
            ids = [i for i in usable if screened[i]["split"] == split]
            measured_ids = [i for i in ids if "error" not in ep["grid"][i]]
            values = [ep["grid"][i]["blank"]["amplitude_over_noise"] for i in measured_ids]
            summary = stats(values)
            summary["expected_denominator"] = len(ids)
            summary["measurement_failures"] = len(ids)-len(measured_ids)
            summary["spatial_blocks"] = {block: stats([ep["grid"][i]["blank"]["amplitude_over_noise"]
                for i in measured_ids if screened[i]["block"] == block])
                for block in sorted({screened[i]["block"] for i in ids})}
            summaries[split] = summary
        ep["null_summaries"] = summaries
        h = summaries["heldout"]
        if h["median"] is None or abs(h["median"]) > .5 or h["mad"] > 1.5 or h["tail5"] != 0:
            failed.append(ep["campaign"]+"_HELDOUT_NULL")
        strata = []
        for flux in [.0003, .0005, .001, .003, .01]:
            ids = [i for i in heldout if screened[i]["flux_jy"] == flux]
            valid = [i for i in ids if "error" not in ep["grid"][i]]
            recovered = sum(ep["grid"][i]["injected"]["recovered"] for i in valid)
            fraction = recovered/len(ids) if ids else None
            bias = (float(np.median([(ep["grid"][i]["injected"]["amplitude_jy"]-flux)/flux for i in valid]))
                    if valid and len(valid) == len(ids) else None)
            strata.append({"flux_jy": flux, "expected_denominator": len(ids),
                           "measured": len(valid), "recovered": recovered,
                           "recovery_fraction": fraction, "unconditional_median_fractional_bias": bias})
            if len(ids) < 10:
                failed.append(ep["campaign"]+f"_STRATUM_{flux}_SMALL")
            if flux >= .003 and (fraction is None or fraction < .95 or bias is None or abs(bias) > .05):
                failed.append(ep["campaign"]+f"_BRIGHT_INJECTION_{flux}")
        ep["heldout_strata"] = strata
    joint = []
    for flux in [.0003, .0005, .001, .003, .01]:
        ids = [i for i in heldout if screened[i]["flux_jy"] == flux]
        recovered = sum(all("error" not in ep["grid"][i] and ep["grid"][i]["injected"]["recovered"]
                            for ep in epochs) for i in ids)
        fraction = recovered/len(ids) if ids else None
        joint.append({"flux_jy": flux, "expected_denominator": len(ids),
                      "joint_recovered": recovered, "joint_recovery_fraction": fraction})
        if flux >= .003 and (fraction is None or fraction < .95):
            failed.append(f"JOINT_BRIGHT_INJECTION_{flux}")
    report["heldout_joint_strata"] = joint
    conditioning = []
    for flux in [.0003, .0005, .001, .003, .01]:
        for split in ("development", "heldout"):
            ids = [i for i in usable if screened[i]["flux_jy"] == flux and screened[i]["split"] == split]
            conditions = {
                "unconditional_after_reference_screen": ids,
                "native_local_eligible": [i for i in ids if screened[i]["selection"]
                                          and screened[i]["selection"]["local_eligible"]],
                "native_global_top12": [i for i in ids if screened[i]["selection"]
                                        and screened[i]["selection"]["global_selected"]]}
            conditions["global_top12_and_final_common_morphology"] = [
                i for i in conditions["native_global_top12"] if all(
                    "error" not in ep["grid"][i]
                    and morphology(ep["grid"][i].get("selected_position_injected")) for ep in epochs)]
            for condition, selected in conditions.items():
                biases = []
                for ep in epochs:
                    measurement_key = ("injected" if condition == "unconditional_after_reference_screen"
                                       else "selected_position_injected")
                    complete_values = [ep["grid"][i][measurement_key]["amplitude_jy"]/flux-1
                                       for i in selected if "error" not in ep["grid"][i]
                                       and measurement_key in ep["grid"][i]]
                    biases.append(float(np.median(complete_values))
                                  if complete_values and len(complete_values) == len(selected) else None)
                conditioning.append({"flux_jy": flux, "split": split, "condition": condition,
                                     "denominator": len(selected), "median_fractional_bias_by_epoch": biases})
    report["selection_conditioning"] = conditioning
    report["failed_gates"] = failed
    report["outcome"] = "STOP_M2" if failed else "COMMON_BEAM_CALIBRATION_FEASIBILITY"


def execute(replay=False):
    F.validate_dependencies()
    plan = json.loads((ROOT/"m2-plan.json").read_text())
    if P.sha(ROOT/"m2-protocol.md") != plan["protocol_sha256"]:
        raise ValueError("M2 protocol changed")
    for name, key in [("full-plane-acquisition.json", "full_manifest_sha256"),
                      ("full-plane-measurement.json", "full_result_sha256")]:
        if P.sha(ROOT/name) != plan[key]:
            raise ValueError("M2 parent receipt changed")
    for path, digest in plan["input_hashes"].items():
        if P.sha(ROOT/path) != digest:
            raise ValueError("M2 retained input hash changed")
    destination = ROOT/"m2-result.json"
    expected = json.loads(destination.read_text()) if replay else None
    if destination.exists() and not replay:
        raise ValueError("M2 result exists; use replay")
    entries, _ = epochs_metadata()
    numerical = numerical_tests(entries)
    if not numerical["passed"]:
        raise ValueError("STOP_M2_NUMERICAL: prospective numerical gates failed")
    report = {"protocol_sha256": plan["protocol_sha256"], "plan_sha256": P.sha(ROOT/"m2-plan.json"),
              "driver_sha256": P.sha(Path(__file__)), "pilot_sha256": F.FROZEN_PILOT_SHA,
              "helper_sha256": F.HELPER_SHA, "full_driver_sha256": P.sha(ROOT/"full_plane.py"),
              "numerical_tests": numerical, "epochs": [], "outcome": "INCOMPLETE_M2",
              "interpretation": "same-data calibration development; not discovery or unknown-search readiness"}
    references = json.loads((ROOT/"full-plane-measurement.json").read_text())["reference_positions"]
    reference = P.load_epoch(entries[1])
    report["reference_screen"] = screen_reference(reference, plan["positions"], references)
    del reference
    gc.collect()
    target = SkyCoord(*P.TARGET, unit="deg")
    nulls = [target.spherical_offsets_by(e*u.arcsec, n*u.arcsec)
             for e, n in [(60, 60), (-60, 60), (60, -60), (-60, -60),
                          (120, 0), (-120, 0), (0, 120), (0, -120)]]
    try:
        for entry in entries:
            limits()
            epoch = P.load_epoch(entry)
            record = {"campaign": entry["campaign"], "target": measured(epoch, *P.TARGET),
                      "references": [measured(epoch, *position) for position in references],
                      "fixed_nulls": [measured(epoch, float(pos.ra.deg), float(pos.dec.deg)) for pos in nulls],
                      "grid": []}
            for position in report["reference_screen"]:
                limits()
                result = {"id": position["id"], "reference_screen_excluded": not position["usable"]}
                if position["usable"]:
                    try:
                        ra, dec = position["ra"], position["dec"]
                        result["blank"] = measured(epoch, ra, dec)
                        result["injected"] = measured(epoch, ra, dec, position["flux_jy"])
                        if position["selection"]:
                            chosen = position["selection"]
                            result["selected_position_injected"] = measured(
                                epoch, chosen["selected_ra"], chosen["selected_dec"],
                                position["flux_jy"], injection_position=(ra, dec))
                    except ValueError as error:
                        result["error"] = str(error)
                record["grid"].append(result)
            report["epochs"].append(record)
            print(entry["campaign"], "200 slots accounted", flush=True)
            del epoch
            gc.collect()
        summarize(report, references)
    except Exception as error:
        report["outcome"] = "STOP_M2_EXECUTION"
        report["error"] = str(error)
        raise
    finally:
        if replay:
            if expected != json.loads(json.dumps(report, allow_nan=False)):
                raise ValueError("M2 full replay differs")
        else:
            save("m2-result.json", report)
            save("m2-runtime.json", {"elapsed_seconds": time.monotonic()-START,
                                    "peak_working_set_bytes": limits(),
                                    "output_bytes": (ROOT/"m2-result.json").stat().st_size})
    print(report["outcome"], report["failed_gates"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "numerical", "run", "_run", "replay"])
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze()
    elif args.mode == "numerical":
        result = numerical_tests(epochs_metadata()[0])
        save("m2-numerical.json", result)
        print(result["passed"], len(result["trials"]))
    elif args.mode == "_run":
        execute()
    elif args.mode == "replay":
        execute(replay=True)
    else:
        F.validate_dependencies()
        status, output = F.H.bounded_run([sys.executable, str(Path(__file__).resolve()), "_run"], 1800)
        print(output)
        raise SystemExit(status)
