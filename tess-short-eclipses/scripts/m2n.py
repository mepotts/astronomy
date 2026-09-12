"""Frozen-phase real-data negative diagnostics; no network or unknown mode."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/m2n"
OUT = ROOT / "out"
MANIFEST = DATA / "manifest.json"
PHASES = (.20, .25, .30, .70, .75, .80)
TICS = (450781262, 53206761, 2041210548)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


M = module("m2n_unchanged_m1", ROOT / "scripts/m1.py")


def read(path):
    return json.loads(Path(path).read_bytes())


def dependencies():
    if M.sha(ROOT / "scripts/m1.py") != "22c46cbfd34877ac66d7b1fcd411ecb8b323aca5ea987da58d62ea141ed29115":
        raise ValueError("STOP_M1_CHANGED")
    paths = [Path(__file__), ROOT / "M2n-PROTOCOL-2026-09-12.md",
             ROOT / "tests/test_m2n.py", ROOT / "tests/test_m2n_review.py",
             ROOT / "scripts/m1.py", M.PROTOCOL, ROOT / "scripts/m0.py",
             ROOT / "M0-PROTOCOL-2026-09-12.md", ROOT / "M0b-PROTOCOL-2026-09-12.md",
             ROOT / "scripts/m1d.py", ROOT / "scripts/m1c.py", ROOT / "scripts/m1b.py", M.RUNNER]
    for tic in TICS:
        _, lc = M.read_solution(tic)
        receipt_path = M.DATA / str(tic) / "receipt.json"
        receipt = read(receipt_path)
        tp = receipt_path.parent / receipt["filename"]
        if M.sha(tp) != receipt["sha256"] or tp.stat().st_size != M.CONTROLS[tic][1]:
            raise ValueError("STOP_TPF_PROVENANCE")
        paths.extend([lc, tp, receipt_path, OUT / f"m0b-{tic}.json", OUT / f"m1b-{tic}.json"])
    return {os.path.relpath(p, ROOT).replace("\\", "/"): M.sha(p) for p in paths}


def verify():
    if read(MANIFEST)["dependencies"] != dependencies():
        raise ValueError("STOP_MANIFEST_CHANGED")


def safe_times(t, period, epoch, duration):
    if period <= 0 or duration <= 0 or not np.all(np.isfinite([period, epoch, duration])):
        raise ValueError("STOP_EPHEMERIS")
    distance = np.abs((t - epoch + period / 4) % (period / 2) - period / 4)
    return distance > duration


def cadence_union(t, centers, duration, cadences):
    used = np.zeros(len(t), dtype=bool)
    for center in centers:
        delta = t - center
        used |= ((np.abs(delta) < duration / 2)
                 | ((delta >= -2.5 * duration) & (delta <= -1.5 * duration))
                 | ((delta >= 1.5 * duration) & (delta <= 2.5 * duration)))
    return {int(v) for v in cadences[used]}


def overlap(sets):
    return {"intersection_counts": [[len(a & b) if a is not None and b is not None else None
                                      for b in sets] for a in sets],
            "jaccard": [[len(a & b) / len(a | b) if a is not None and b is not None and a | b
                         else None for b in sets] for a in sets]}


def support(used):
    return {"used_cadences": len(used) if used is not None else None,
            "cadence_sha256": hashlib.sha256(np.array(sorted(used), dtype="<i8").tobytes()).hexdigest()
            if used is not None else None}


def channel(t, cube, errors, args, offset, anchor, aperture, collected, cadences):
    centers, events = M.paired_events(t, cube, errors, *args, offset=offset)
    pixels = collected & np.all(np.isfinite(events), axis=0)
    if pixels.sum() < 25 or not np.all(pixels[aperture]):
        raise ValueError("STOP_PIXEL_COVERAGE")
    blocks, labels = M.day_blocks(centers, events, anchor)
    stats = M.block_statistics(blocks, aperture)
    used = cadence_union(t, centers, args[2], cadences)
    return {"stats": stats, "events": len(events), "centers": centers,
            "day_labels": labels, "block_aperture_amplitudes": blocks[:, aperture].sum(axis=1),
            "mean_image": blocks.mean(axis=0),
            "error_image": blocks.std(axis=0, ddof=1) / np.sqrt(len(blocks)),
            "valid_pixels": pixels}, used


def flags(flux, background, primary):
    result = []
    for label, stats in (("PHASE", flux), ("BACKGROUND", background)):
        if (stats is None or stats["snr"] is None or not np.isfinite(stats["snr"])
                or not np.isfinite(stats["error"]) or stats["error"] <= 0
                or not np.isfinite(stats["amplitude"])):
            result.append(label + "_ERROR_UNDEFINED")
    if "PHASE_ERROR_UNDEFINED" not in result and abs(flux["snr"]) >= 3:
        result.append("PHASE_CONTROL_STRUCTURE")
    if ("BACKGROUND_ERROR_UNDEFINED" not in result and abs(background["snr"]) >= 3
            and abs(background["amplitude"]) > .1 * abs(primary)):
        result.append("BACKGROUND_COHERENCE")
    return result


def load_data(tic):
    solution, lc_path = M.read_solution(tic)
    receipt = read(M.DATA / str(tic) / "receipt.json")
    with fits.open(M.DATA / str(tic) / receipt["filename"]) as tp, fits.open(lc_path) as lc:
        M.check_header(tp, tic)
        td, ld = tp[1].data, lc[1].data
        if any(len(np.unique(d["CADENCENO"])) != len(d) for d in (td, ld)):
            raise ValueError("STOP_DUPLICATE_CADENCES")
        good = (np.isfinite(ld["TIME"]) & np.isfinite(ld["PDCSAP_FLUX"])
                & np.isfinite(ld["PDCSAP_FLUX_ERR"]) & (ld["PDCSAP_FLUX_ERR"] > 0)
                & (ld["QUALITY"] == 0))
        tgood = np.isfinite(td["TIME"]) & (td["QUALITY"] == 0)
        _, li, ti = np.intersect1d(ld["CADENCENO"][good], td["CADENCENO"][tgood], return_indices=True)
        li, ti = np.flatnonzero(good)[li], np.flatnonzero(tgood)[ti]
        t = np.asarray(td["TIME"][ti], dtype=float)
        if len(t) < 1000 or np.any(np.diff(t) <= 0) or np.max(np.abs(t - ld["TIME"][li])) > 1e-7:
            raise ValueError("STOP_CADENCE_ALIGNMENT")
        cubes = [np.asarray(td[k][ti], dtype=float) for k in ("FLUX", "FLUX_ERR", "FLUX_BKG", "FLUX_BKG_ERR")]
        aperture, collected = (tp[2].data.astype(int) & 2) > 0, (tp[2].data.astype(int) & 1) > 0
        if not np.allclose(cubes[0][:, aperture].sum(axis=1), ld["SAP_FLUX"][li], atol=1e-3, rtol=1e-5):
            raise ValueError("STOP_SAP_REPRODUCTION")
        cadences = np.array(td["CADENCENO"][ti], dtype=np.int64)
    sol = solution["solution"]
    return t, cubes, aperture, collected, cadences, (sol["period"], sol["transit_time"], sol["duration"])


def measure(tic):
    t, cubes, aperture, collected, cadences, args = load_data(tic)
    primary, _ = channel(t, *cubes[:2], args, 0, t.min(), aperture, collected, cadences)
    old = read(OUT / f"m1b-{tic}.json")
    if (M.clean(primary["stats"]) != old["primary"] or primary["events"] != old["paired_events"]
            or M.clean(primary["day_labels"]) != old["day_labels"]
            or M.clean(primary["mean_image"]) != old["images"]["difference"]
            or int(aperture.sum()) != old["aperture_pixels"] or len(t) != old["points"]):
        raise ValueError("STOP_PRIMARY_REPLAY")
    mask = safe_times(t, *args)
    anchor = float(t.min())
    phase_results, sets = [], []
    for offset in PHASES:
        row = {"phase": offset}
        memberships = []
        for name, index in (("flux", 0), ("background", 2)):
            used = None
            try:
                record, used = channel(t[mask], cubes[index][mask], cubes[index + 1][mask],
                                       args, offset, anchor, aperture, collected, cadences[mask])
                row[name] = {**record, "status": "MEASURED", **support(used)}
            except ValueError as error:
                row[name] = {"status": "STOP_COVERAGE", "error": str(error), **support(None)}
            memberships.append(used)
        complete = all(v is not None for v in memberships)
        if complete and memberships[0] != memberships[1]:
            raise ValueError("STOP_CHANNEL_TIME_MEMBERSHIP")
        row["flags"] = flags(row["flux"].get("stats"), row["background"].get("stats"),
                             old["primary"]["amplitude"])
        row["status"] = "STOP_COVERAGE" if not complete else "FLAGGED" if row["flags"] else "QUIET_DIAGNOSTIC"
        used = memberships[0] if complete else None
        row.update(support(used))
        phase_results.append(row)
        sets.append(used)
    return {"tic": tic, "status": "STOP_NULL_STRUCTURE_OR_COVERAGE" if any(
        r["status"] != "QUIET_DIAGNOSTIC" for r in phase_results) else
        "WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE",
        "primary_replay_exact": True, "primary_amplitude": old["primary"]["amplitude"],
        "original_points": len(t), "excluded_points": int((~mask).sum()), "anchor": anchor,
        "aperture": aperture, "collected": collected, "phases": phase_results,
        "overlap": overlap(sets), "unknown_search_authorized": False,
        "physical_depth_validated": False, "network_requests": 0}


def execute(tic):
    verify()
    try:
        result = measure(tic)
    except (ValueError, OSError) as error:
        result = {"tic": tic, "status": "STOP_INPUT_OR_MEASUREMENT", "error": str(error),
                  "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0}
    return M.clean({**result, "manifest_sha256": M.sha(MANIFEST)})


def worker(tic, replay):
    start = time.monotonic()
    verify()
    if read(DATA / "run-start.json")["manifest_sha256"] != M.sha(MANIFEST):
        raise ValueError("STOP_RUN_APPROVAL")
    marker = DATA / f"worker-{tic}.json"
    if not replay:
        M.save(marker, {"manifest_sha256": M.sha(MANIFEST), "tic": tic})
    elif read(marker) != {"manifest_sha256": M.sha(MANIFEST), "tic": tic}:
        raise ValueError("STOP_WORKER_MARKER")
    memory = module("m2n_memory", ROOT / "scripts/m1d.py")
    memory.peak_memory()
    result = execute(tic)
    peak = memory.peak_memory()
    if time.monotonic() - start > 180 or len(json.dumps(result).encode()) > 1_000_000:
        raise ValueError("STOP_RESOURCE_CAP")
    path, runtime = OUT / f"m2n-{tic}.json", DATA / f"runtime-{tic}.json"
    if replay:
        if read(path) != result:
            raise ValueError("STOP_EXACT_REPLAY")
    else:
        M.save(path, result)
        M.save(runtime, {"elapsed_seconds": time.monotonic() - start, "peak_working_set_bytes": peak})
    print(json.dumps({"tic": tic, "status": result["status"], "replay": replay}), flush=True)


def run(replay, approval):
    verify()
    if not replay:
        if approval != M.sha(MANIFEST):
            raise ValueError("STOP_APPROVAL_HASH")
        M.save(DATA / "run-start.json", {"manifest_sha256": approval})
    else:
        prior = read(OUT / "m2n-summary.json")
        if (prior["manifest_sha256"] != M.sha(MANIFEST)
                or [r["tic"] for r in prior["outcomes"]] != list(TICS)):
            raise ValueError("STOP_SUMMARY_IDENTITY")
        required = [DATA / "run-start.json"]
        stopped = False
        for row in prior["outcomes"]:
            tic = row["tic"]
            if type(row["returncode"]) is not int or not isinstance(row["output"], str):
                raise ValueError("STOP_OUTCOME_SCHEMA")
            if stopped and (row["returncode"] != 1 or row["output"] != "STOP_NOT_LAUNCHED"):
                raise ValueError("STOP_OUTCOME_ORDER")
            paths = (OUT / f"m2n-{tic}.json", DATA / f"runtime-{tic}.json", DATA / f"worker-{tic}.json")
            if not row["returncode"]:
                if any(not p.is_file() for p in paths):
                    raise ValueError("STOP_MISSING_SUCCESS_ARTIFACT")
                result = read(paths[0])
                expected_output = {"tic": tic, "status": result["status"], "replay": False}
                if (result["tic"] != tic or result["manifest_sha256"] != M.sha(MANIFEST)
                        or json.loads(row["output"]) != expected_output):
                    raise ValueError("STOP_WORKER_OUTPUT_IDENTITY")
                runtime = read(paths[1])
                if (not 0 <= runtime["elapsed_seconds"] <= 180
                        or not 0 < runtime["peak_working_set_bytes"] <= 1_000_000_000):
                    raise ValueError("STOP_RUNTIME_RECEIPT")
            required.extend(p for p in paths if p.is_file())
            stopped |= bool(row["returncode"])
        expected = {os.path.relpath(p, ROOT).replace("\\", "/") for p in required}
        if set(prior["artifacts"]) != expected or prior["unknown_search_authorized"] is not False:
            raise ValueError("STOP_ARTIFACT_CLOSURE")
        for name, digest in prior["artifacts"].items():
            if M.sha(ROOT / name) != digest:
                raise ValueError("STOP_ARTIFACT_HASH")
    outcomes = []
    runner = None
    for tic in TICS:
        if replay and next(r for r in prior["outcomes"] if r["tic"] == tic)["returncode"]:
            print(f"Retained failed/unlaunched worker {tic}; no execution replay", flush=True)
            outcomes.append(next(r for r in prior["outcomes"] if r["tic"] == tic))
            continue
        if outcomes and outcomes[-1]["returncode"]:
            outcomes.append({"tic": tic, "returncode": 1, "output": "STOP_NOT_LAUNCHED"})
            continue
        try:
            if runner is None:
                runner = module("m2n_runner", M.RUNNER)
            command = [sys.executable, "-B", str(Path(__file__).resolve()),
                       "replay" if replay else "run", "--worker", str(tic)]
            code, output = runner.bounded_run(command, 180)
        except Exception:
            logging.getLogger(__name__).exception("M2n worker launch or cleanup failed")
            code, output = 1, traceback.format_exc()
        outcomes.append({"tic": tic, "returncode": code, "output": output})
        print(output, flush=True)
    if not replay:
        paths = [DATA / "run-start.json"]
        for tic in TICS:
            paths.extend(p for p in (OUT / f"m2n-{tic}.json", DATA / f"runtime-{tic}.json",
                                    DATA / f"worker-{tic}.json") if p.exists())
        M.save(OUT / "m2n-summary.json", {"manifest_sha256": M.sha(MANIFEST), "outcomes": outcomes,
               "artifacts": {os.path.relpath(p, ROOT).replace("\\", "/"): M.sha(p) for p in paths},
               "unknown_search_authorized": False})
    if any(r["returncode"] for r in outcomes):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "replay"))
    parser.add_argument("--worker", type=int, choices=TICS)
    parser.add_argument("--approved-manifest-sha256")
    args = parser.parse_args()
    if args.stage == "prepare":
        if args.worker:
            raise ValueError("STOP_WORKER_STAGE")
        M.save(MANIFEST, {"dependencies": dependencies(), "utc": datetime.now(timezone.utc).isoformat()})
    elif args.worker:
        worker(args.worker, args.stage == "replay")
    else:
        run(args.stage == "replay", args.approved_manifest_sha256)


if __name__ == "__main__":
    main()
