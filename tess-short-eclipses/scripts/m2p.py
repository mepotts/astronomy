"""Control-only PRF localization and corner-shape real-noise stress experiment."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
spec_path = ROOT / "scripts/m2n.py"

SPEC = importlib.util.spec_from_file_location("m2p_frozen_negative", spec_path)
N = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(N)
M = N.M
DATA = ROOT / "data/m2p"
OUT = ROOT / "out"
MANIFEST = DATA / "manifest.json"
TICS = N.TICS
SCALES = (.5, 1., 2.)
TRIALS = 20
OUTPUT_CAP = 100_000_000
RECEIPT_RESERVE = 1_000_000


def read(path):
    return json.loads(Path(path).read_bytes())


def serialized_size(value):
    return len((json.dumps(M.clean(value), indent=2, allow_nan=False) + "\n").encode())


def save(path, value, *, terminal=False):
    size = serialized_size(value)
    paths = list(DATA.rglob("*.json")) + [p for p in OUT.glob("m2p-*.json") if p.is_file()]
    cap = OUTPUT_CAP if terminal else OUTPUT_CAP - RECEIPT_RESERVE
    if (terminal and (Path(path) != OUT / "m2p-summary.json" or size > RECEIPT_RESERVE)
            or size + sum(p.stat().st_size for p in paths) > cap):
        raise RuntimeError("STOP_OUTPUT_CAP")
    M.save(path, value)


def catalog(tic):
    name = f"m1b-{tic}.json" if tic == TICS[0] else f"m1e-{tic}.json"
    value = read(OUT / name)["catalog"]
    rows = value["rows_in_stamp"]
    ids = [r["source_id"] for r in rows]
    if (len(set(ids)) != len(ids) or any(int(v) <= 0 for v in ids)
            or any(not np.all(np.isfinite([r["x"], r["y"]])) for r in rows)):
        raise ValueError("STOP_CATALOG_ROWS")
    matches = [r for r in rows if r["source_id"] == value["provisional_target_id"]]
    if len(matches) != 1 or len(rows) < 2:
        raise ValueError("STOP_CATALOG_ASSOCIATION")
    return sorted(rows, key=lambda r: int(r["source_id"])), matches[0]


def locations(rows, target):
    others = [r for r in rows if r["source_id"] != target["source_id"]]
    def distance(r):
        return float(np.hypot(r["x"] - target["x"], r["y"] - target["y"]))
    nearest = min(others, key=lambda r: (distance(r), int(r["source_id"])))
    chosen = [("target", target), ("nearest_other", nearest)]
    bright = [r for r in others if distance(r) <= 1 and r["g_mag"] is not None and np.isfinite(r["g_mag"])]
    if bright:
        chosen.append(("brightest_other_within_one_pixel", min(bright, key=lambda r: (r["g_mag"], int(r["source_id"])))))
    unique = {}
    for role, row in chosen:
        unique.setdefault(row["source_id"], {"source_id": row["source_id"], "x": row["x"], "y": row["y"], "roles": []})["roles"].append(role)
    return {"locations": list(unique.values()), "target_id": target["source_id"],
            "nearest_id": nearest["source_id"], "pair_separation": distance(nearest),
            "missing_bright_role": not bright, "planned_trials": len(unique) * 3 * 4 * TRIALS}


def dependencies():
    if (M.sha(N.MANIFEST) != "bf1e1b949a03422981d175991bdfcbf1f9a32544df6bbe48cedc76a483846b98"
            or M.sha(ROOT / "data/m2a/manifest.json") != "f63e087a88054ac1336b71dce9956324de48acacc5ffed25b5f1f01697a6e816"):
        raise ValueError("STOP_PREREQUISITE_MANIFEST")
    paths = set(N.dependencies())
    for stage in ("m2a", "m1e"):
        manifest = ROOT / f"data/{stage}/manifest.json"
        paths.update(read(manifest)["dependencies"])
        paths.add(str(manifest.relative_to(ROOT)).replace("\\", "/"))
        paths.add(f"out/{stage}-summary.json")
        paths.add(f"data/{stage}/run-start.json")
        for row in read(ROOT / f"out/{stage}-summary.json")["outcomes"]:
            if row["returncode"] != 0:
                raise ValueError("STOP_PREREQUISITE_OUTCOME")
            paths.update(row["artifacts"])
            paths.add(f"data/{stage}/{row['filename']}.outcome.json" if stage == "m2a"
                      else f"data/{stage}/outcome-{row['tic']}.json")
    paths.update(read(OUT / "m2n-summary.json")["artifacts"])
    paths.update(["data/m2n/manifest.json", "out/m2n-summary.json", "scripts/m2p.py",
                  "scripts/prf_model.py", "PRF-MODEL-DESIGN.md", "M2p-PROTOCOL-2026-09-12.md",
                  "tests/test_m2p.py", "tests/test_m2p_review.py", "tests/test_prf_model.py",
                  "tests/test_prf_model_review.py", "scripts/m2a.py", "scripts/m1e.py"])
    return {name: M.sha(ROOT / name) for name in sorted(paths)}


def verify():
    manifest = read(MANIFEST)
    if (manifest["dependencies"] != dependencies()
            or manifest["selection"] != {str(t): locations(*catalog(t)) for t in TICS}):
        raise ValueError("STOP_MANIFEST_CHANGED")


def blocks(t, cube, errors, args, offset, anchor, aperture, collected):
    centers, events = M.paired_events(t, cube, errors, *args, offset=offset)
    valid = collected & np.all(np.isfinite(events), axis=0)
    if valid.sum() < 25 or not np.all(valid[aperture]):
        raise ValueError("STOP_PIXEL_COVERAGE")
    grouped, labels = M.day_blocks(centers, events, anchor)
    return grouped, labels, valid, centers


def assignment(fit, rows):
    if fit.get("bound_hit"):
        return "BOUND"
    if not fit.get("success"):
        return "FAILED"
    distances = sorted((float(np.hypot(r["x"] - fit["x"], r["y"] - fit["y"])), r["source_id"]) for r in rows)
    if len(distances) > 1 and abs(distances[0][0] - distances[1][0]) <= 1e-12:
        return "AMBIGUOUS"
    return distances[0][1]


def ellipse(fit, truth):
    covariance = fit.get("centroid_covariance")
    if not fit.get("success") or fit.get("bound_hit") or covariance is None:
        return None
    cov = np.asarray(covariance, dtype=float)
    if cov.shape != (2, 2) or not np.all(np.isfinite(cov)) or np.min(np.linalg.eigvalsh(cov)) <= 0:
        return None
    delta = np.array([fit["x"] - truth["x"], fit["y"] - truth["y"]])
    return bool(delta @ np.linalg.solve(cov, delta) <= -2 * np.log(.05))


def compact(fit):
    return {k: v for k, v in fit.items() if k not in ("model", "residual", "model_image", "residual_image")}


def failed_trial(status, error):
    return {"fit": {"success": False, "status": status, "error": str(error)},
            "assignment": "FAILED", "signed_displacement": None, "radial_error": None,
            "nominal_ellipse_covers_truth": None}


def condition_summary(trials, truth, rows, pair_ids, separation, scale):
    counts = dict.fromkeys([r["source_id"] for r in rows] + ["FAILED", "BOUND", "AMBIGUOUS"], 0)
    for trial in trials:
        counts[trial["assignment"]] += 1
    complete = len(trials) == TRIALS and not any(counts[k] for k in ("FAILED", "BOUND", "AMBIGUOUS"))
    valid_xy = [trial["signed_displacement"] for trial in trials if trial["signed_displacement"] is not None]
    bias = np.mean(valid_xy, axis=0) if complete and len(valid_xy) == TRIALS else None
    wrong = sum(v for k, v in counts.items() if k not in (truth["source_id"], "FAILED", "BOUND", "AMBIGUOUS"))
    cov_missing = sum(t["nominal_ellipse_covers_truth"] is None for t in trials)
    reasons = []
    if scale == 1:
        if wrong / TRIALS > .05:
            reasons.append("STOP_LOCALIZATION_CONFUSION")
        if truth["source_id"] in pair_ids and bias is not None and np.linalg.norm(bias) > separation / 2:
            reasons.append("STOP_LOCALIZATION_BIAS")
        if not complete or cov_missing:
            reasons.append("INCOMPLETE_TRIAL_OR_COVARIANCE")
    unmeasured = sum(t.get("fit", {}).get("status") == "NOT_MEASURED_CONDITION_FAILURE" for t in trials)
    exceptions = sum(t.get("fit", {}).get("status") == "STOP_TRIAL" for t in trials)
    return {"counts": counts, "denominator": TRIALS, "recorded_slots": len(trials),
            "attempted_trials": len(trials) - unmeasured,
            "completed_trials": len(trials) - unmeasured - exceptions,
            "wrong_row_fraction": wrong / TRIALS, "signed_mean_bias": bias,
            "bias_norm": float(np.linalg.norm(bias)) if bias is not None else None,
            "coverage_fraction": sum(t["nominal_ellipse_covers_truth"] is True for t in trials) / TRIALS,
            "undefined_ellipses": cov_missing, "reasons": reasons}


def injection_mask(t, args):
    period, epoch, duration = args
    return np.abs((t - epoch - .25 * period + period / 2) % period - period / 2) < duration / 2


def measure(tic, emit):
    A = N.module("m2p_acquisition", ROOT / "scripts/m2a.py")
    E = N.module("m2p_catalog", ROOT / "scripts/m1e.py")
    with contextlib.redirect_stdout(io.StringIO()):
        A.replay()
        E.replay()
    prior = read(OUT / f"m2n-{tic}.json")
    if N.execute(tic) != prior or prior["status"] != "WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE":
        raise ValueError("STOP_NEGATIVE_PREREQUISITE")
    core = N.module("m2p_prf", ROOT / "scripts/prf_model.py")
    arrays = []
    for p in [p for p in A.products() if p["tic"] == tic]:
        with fits.open(A.folder_for(p["filename"]) / p["filename"], memmap=False) as hdus:
            arrays.append(np.array(hdus[0].data, dtype=float))
    ctx = next(v for v in read(A.MANIFEST)["context"] if v["tic"] == tic)
    grid = core.PRFGrid(np.asarray(arrays), ctx["rows"], ctx["columns"], ctx["origin"])
    rows, target = catalog(tic)
    selection = locations(rows, target)
    t, cubes, aperture, collected, _cadences, args = N.load_data(tic)
    anchor = t.min()
    primary_blocks, labels, valid, _ = blocks(t, cubes[0], cubes[1], args, 0, anchor, aperture, collected)
    error = primary_blocks.std(axis=0, ddof=1) / np.sqrt(len(labels))
    image = primary_blocks.mean(axis=0)
    primary_fit = core.fit(image, error, valid, grid)
    loo = [compact(core.fit(np.delete(primary_blocks, i, axis=0).mean(axis=0), error, valid, grid)) for i in range(len(labels))]
    profiles = [{"source_id": r["source_id"], "fit": compact(core.fixed_hypothesis(image, error, valid, grid, r["x"], r["y"]))} for r in rows]
    primary = {"fit": primary_fit, "day_labels": labels, "leave_one_day_out": loo,
               "profile_hypotheses": profiles, "nearest_centroid_label": assignment(primary_fit, rows)}
    emit("primary", primary)
    negatives = [{"phase": p["phase"], **{name: core.fit(np.asarray(p[name]["mean_image"]),
                   np.asarray(p[name]["error_image"]), np.asarray(p[name]["valid_pixels"]), grid)
                   for name in ("flux", "background")}} for p in prior["phases"]]
    emit("negatives", negatives)
    keep = N.safe_times(t, *args)
    nt, flux, errors = t[keep], cubes[0][keep], cubes[1][keep]
    original_blocks, neg_labels, neg_valid, _ = blocks(nt, flux, errors, args, .25, anchor, aperture, collected)
    neg_error = original_blocks.std(axis=0, ddof=1) / np.sqrt(len(neg_labels))
    draws = np.random.default_rng(20260912).integers(0, len(neg_labels), size=(TRIALS, len(neg_labels)))
    inject = injection_mask(nt, args)
    conditions = []
    for li, truth in enumerate(selection["locations"]):
        for scale in SCALES:
            for corner in range(4):
                trials = []
                record = {"truth": truth, "scale": scale, "corner": corner}
                try:
                    model, metadata = grid.image(truth["x"], truth["y"], aperture.shape, corner=corner)
                    fraction = float(model[aperture].sum())
                    if not np.isfinite(fraction) or fraction <= 0:
                        raise ValueError("STOP_INJECTION_APERTURE_RESPONSE")
                    amplitude = scale * prior["primary_amplitude"] / fraction
                    perturbed = flux.copy()
                    perturbed[inject] -= amplitude * model
                    new_blocks, new_labels, new_valid, _ = blocks(nt, perturbed, errors, args, .25, anchor, aperture, collected)
                    if not np.array_equal(new_labels, neg_labels) or not np.array_equal(new_valid, neg_valid):
                        raise ValueError("STOP_INJECTION_MEMBERSHIP")
                    record.update(model_metadata=metadata, aperture_response=fraction, model_amplitude=amplitude)
                    for draw in draws:
                        try:
                            fit = core.fit(new_blocks[draw].mean(axis=0), neg_error, neg_valid, grid)
                            label = assignment(fit, rows)
                            delta = [fit["x"] - truth["x"], fit["y"] - truth["y"]] if label not in ("FAILED", "BOUND", "AMBIGUOUS") else None
                            trials.append({"fit": compact(fit), "assignment": label, "signed_displacement": delta,
                                           "radial_error": float(np.linalg.norm(delta)) if delta is not None else None,
                                           "nominal_ellipse_covers_truth": ellipse(fit, truth)})
                        except (ValueError, np.linalg.LinAlgError) as exc:
                            trials.append(failed_trial("STOP_TRIAL", exc))
                except (ValueError, np.linalg.LinAlgError) as exc:
                    record.update(error=str(exc), status="STOP_CONDITION", planned_trials=TRIALS)
                    trials.extend(failed_trial("NOT_MEASURED_CONDITION_FAILURE", exc) for _ in range(TRIALS - len(trials)))
                record.update(trials=trials, summary=condition_summary(trials, truth, rows,
                              (selection["target_id"], selection["nearest_id"]), selection["pair_separation"], scale))
                conditions.append(record)
                emit(f"condition-{li}-{scale}-{corner}", record)
    reasons = sorted({reason for c in conditions for reason in c.get("summary", {}).get("reasons", [])})
    if any("error" in c for c in conditions):
        reasons.append("INCOMPLETE_CONDITION")
    if any(not f.get("success") or f.get("bound_hit") for f in [primary_fit, *loo]):
        reasons.append("INCOMPLETE_PRIMARY_FIT")
    if any(not p["fit"].get("success") for p in profiles):
        reasons.append("INCOMPLETE_PROFILE_HYPOTHESIS")
    status = "STOP_LOCALIZATION_CONFUSION" if any(r.startswith("STOP_LOCALIZATION") for r in reasons) else (
        "VALIDATION_INCOMPLETE" if reasons else "DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE")
    return {"tic": tic, "status": status, "reasons": reasons, "selection": selection, "primary": primary,
            "negative_fits": negatives, "conditions": conditions, "day_resampling_indices": draws,
            "negative_day_labels": neg_labels, "planned_trials": selection["planned_trials"],
            "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0}


def worker(tic, replay):
    started = time.monotonic()
    verify()
    digest = M.sha(MANIFEST)
    if read(DATA / "run-start.json") != {"manifest_sha256": digest}:
        raise ValueError("STOP_RUN_APPROVAL")
    marker = DATA / f"worker-{tic}.json"
    if replay:
        if read(marker) != {"tic": tic, "manifest_sha256": digest}:
            raise ValueError("STOP_WORKER_MARKER")
    else:
        M.save(marker, {"tic": tic, "manifest_sha256": digest})
    memory = N.module("m2p_peak", ROOT / "scripts/m1d.py")
    memory.peak_memory()

    def emit(name, value):
        path = DATA / str(tic) / f"{name}.json"
        clean = M.clean(value)
        if serialized_size(clean) > 2_000_000:
            raise RuntimeError("STOP_CHECKPOINT_SIZE")
        if replay:
            if read(path) != clean:
                raise RuntimeError("STOP_CHECKPOINT_REPLAY")
        else:
            save(path, clean)

    try:
        result = measure(tic, emit)
    except (ValueError, OSError, np.linalg.LinAlgError) as error:
        result = {"tic": tic, "status": "STOP_INPUT_OR_MEASUREMENT", "error": str(error),
                  "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0}
    result = M.clean({**result, "manifest_sha256": digest})
    if time.monotonic() - started > 600 or serialized_size(result) > 25_000_000:
        raise ValueError("STOP_RESOURCE_CAP")
    path = OUT / f"m2p-{tic}.json"
    if replay:
        if read(path) != result:
            raise ValueError("STOP_RESULT_REPLAY")
    else:
        save(path, result)
    peak = memory.peak_memory()
    if not 0 < peak <= 1_000_000_000 or time.monotonic() - started > 600:
        raise ValueError("STOP_RESOURCE_CAP")
    if not replay:
        save(DATA / f"runtime-{tic}.json", {"elapsed_seconds": time.monotonic() - started, "peak_working_set_bytes": peak})
    print(json.dumps({"tic": tic, "status": result["status"], "replay": replay}), flush=True)


def artifacts():
    paths = [p for p in DATA.rglob("*.json") if p != MANIFEST]
    paths += [OUT / f"m2p-{t}.json" for t in TICS if (OUT / f"m2p-{t}.json").exists()]
    if sum(p.stat().st_size for p in paths) > 100_000_000:
        raise ValueError("STOP_OUTPUT_CAP")
    return {os.path.relpath(p, ROOT).replace("\\", "/"): M.sha(p) for p in sorted(paths)}


def completed(tic, output, replay):
    result = read(OUT / f"m2p-{tic}.json")
    runtime = read(DATA / f"runtime-{tic}.json")
    digest = M.sha(MANIFEST)
    statuses = {"STOP_INPUT_OR_MEASUREMENT", "STOP_LOCALIZATION_CONFUSION", "VALIDATION_INCOMPLETE",
                "DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE"}
    if (result["status"] not in statuses
            or (OUT / f"m2p-{tic}.json").stat().st_size > 25_000_000
            or json.loads(output) != {"tic": tic, "status": result["status"], "replay": replay}
            or result["tic"] != tic or result["manifest_sha256"] != digest
            or result["unknown_search_authorized"] is not False
            or result["physical_depth_validated"] is not False or result["network_requests"] != 0
            or read(DATA / f"worker-{tic}.json") != {"tic": tic, "manifest_sha256": digest}
            or not 0 <= runtime["elapsed_seconds"] <= 600
            or not 0 < runtime["peak_working_set_bytes"] <= 1_000_000_000):
        raise ValueError("STOP_OUTCOME_RECEIPT")
    if result["status"] != "STOP_INPUT_OR_MEASUREMENT":
        selection = read(MANIFEST)["selection"][str(tic)]
        names = {"primary", "negatives"} | {f"condition-{li}-{scale}-{corner}" for li in range(len(selection["locations"]))
                                             for scale in SCALES for corner in range(4)}
        if ({p.stem for p in (DATA / str(tic)).glob("*.json")} != names
                or result["selection"] != selection
                or result["planned_trials"] != selection["planned_trials"]
                or len(result["conditions"]) != len(names) - 2):
            raise ValueError("STOP_CHECKPOINT_CLOSURE")
        for key, value in (("primary", result["primary"]), ("negatives", result["negative_fits"])):
            if read(DATA / str(tic) / f"{key}.json") != value:
                raise ValueError("STOP_CHECKPOINT_CONTENT")
        expected = [(li, truth, scale, corner) for li, truth in enumerate(selection["locations"])
                    for scale in SCALES for corner in range(4)]
        rows, _ = catalog(tic)
        for condition, (li, truth, scale, corner) in zip(result["conditions"], expected, strict=True):
            if (condition["truth"] != truth or condition["scale"] != scale or condition["corner"] != corner
                    or len(condition["trials"]) != TRIALS
                    or condition["summary"] != M.clean(condition_summary(condition["trials"], truth, rows,
                       (selection["target_id"], selection["nearest_id"]), selection["pair_separation"], scale))
                    or read(DATA / str(tic) / f"condition-{li}-{scale}-{corner}.json") != condition):
                raise ValueError("STOP_CONDITION_RECEIPT")


def output_receipt(output):
    raw = output.encode()
    return {"output": raw[:16_000].decode(errors="ignore"), "output_bytes": len(raw),
            "output_sha256": hashlib.sha256(raw).hexdigest(), "output_truncated": len(raw) > 16_000}


def validate_output_receipt(row):
    if (not isinstance(row, dict)
            or not {"output", "output_bytes", "output_sha256", "output_truncated"} <= row.keys()
            or not isinstance(row["output"], str)):
        raise ValueError("STOP_OUTPUT_RECEIPT")
    raw = row["output"].encode()
    digest = row["output_sha256"]
    if (type(row["output_bytes"]) is not int or type(row["output_truncated"]) is not bool
            or row["output_bytes"] < len(raw) or len(raw) > 16_000
            or not isinstance(digest, str) or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
            or row["output_truncated"] != (row["output_bytes"] > 16_000)):
        raise ValueError("STOP_OUTPUT_RECEIPT")
    if not row["output_truncated"] and (row["output_bytes"] != len(raw)
            or digest != hashlib.sha256(raw).hexdigest()):
        raise ValueError("STOP_OUTPUT_RECEIPT")


def run(replay, approved):
    verify()
    digest = M.sha(MANIFEST)
    summary_path = OUT / "m2p-summary.json"
    if replay:
        prior = read(summary_path)
        if (prior["manifest_sha256"] != digest or prior["artifacts"] != artifacts()
                or [r["tic"] for r in prior["outcomes"]] != list(TICS)
                or prior["unknown_search_authorized"] is not False):
            raise ValueError("STOP_SUMMARY_REPLAY")
        stopped = False
        for row in prior["outcomes"]:
            validate_output_receipt(row)
            if "worker_output" in row:
                validate_output_receipt(row["worker_output"])
            if stopped and (row["returncode"] == 0 or row["output"] != "STOP_NOT_LAUNCHED"):
                raise ValueError("STOP_OUTCOME_ORDER")
            if row["returncode"] == 0:
                if row["worker_returncode"] != 0 or row["output_truncated"]:
                    raise ValueError("STOP_SUCCESS_RECEIPT")
                if row["worker_output"] != output_receipt(row["output"]):
                    raise ValueError("STOP_SUCCESS_RECEIPT")
                completed(row["tic"], row["output"], False)
            stopped = stopped or row["returncode"] != 0
    else:
        if approved != digest:
            raise ValueError("STOP_APPROVAL_HASH")
        M.save(DATA / "run-start.json", {"manifest_sha256": digest})
    outcomes = []
    for tic in TICS:
        old = next((r for r in prior["outcomes"] if r["tic"] == tic), None) if replay else None
        if (old and old["returncode"]) or (outcomes and outcomes[-1]["returncode"]):
            outcomes.append(old or {"tic": tic, "returncode": 1, "worker_returncode": None,
                                    **output_receipt("STOP_NOT_LAUNCHED")})
            continue
        worker_code = None
        worker_output = ""
        try:
            runner = N.module("m2p_deadline", M.RUNNER)
            code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                               "replay" if replay else "run", "--worker", str(tic)], 600)
            worker_code, worker_output = code, output
            if code == 0:
                completed(tic, output, replay)
        except Exception:
            logging.getLogger(__name__).exception("M2p launch or cleanup failed")
            code, output = 1, traceback.format_exc()
        outcomes.append({"tic": tic, "returncode": code, "worker_returncode": worker_code,
                         **output_receipt(output), "worker_output": output_receipt(worker_output)})
        print(output, flush=True)
    if not replay:
        save(summary_path, {"manifest_sha256": digest, "outcomes": outcomes, "artifacts": artifacts(),
                              "unknown_search_authorized": False}, terminal=True)
    if any(row["returncode"] for row in outcomes):
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
        save(MANIFEST, {"dependencies": dependencies(), "selection": {str(t): locations(*catalog(t)) for t in TICS}})
    elif args.worker:
        worker(args.worker, args.stage == "replay")
    else:
        run(args.stage == "replay", args.approved_manifest_sha256)


if __name__ == "__main__":
    main()
