"""Read-only post-run audit using independent interpolation and ledger arithmetic."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]
TICS = (450781262, 53206761, 2041210548)
MANIFEST_HASH = "6cf8d3c0b159d2fab06d5a5e1acf2f2d5924ac1eefff2e9085addfcea219dfed"


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def independent_model(arrays, context, x, y):
    """Padded scalar field blend plus scipy sampler, not the frozen core implementation."""
    column, row = np.asarray(context["origin"]) + [x, y]
    cx = (column - context["columns"][0]) / np.diff(context["columns"])[0]
    ry = (row - context["rows"][0]) / np.diff(context["rows"])[0]
    require(0 <= cx <= 1 and 0 <= ry <= 1, "field bracket")
    weights = [(1 - ry) * (1 - cx), (1 - ry) * cx, ry * (1 - cx), ry * cx]
    combined = sum(w * a for w, a in zip(weights, arrays, strict=True))
    padded = np.pad(combined, 1)

    def evaluate(xx, yy):
        return map_coordinates(padded, [59 + 9 * (yy - y), 59 + 9 * (xx - x)],
                               order=1, mode="constant", cval=0., prefilter=False)

    fy, fx = np.mgrid[int(np.floor(y)) - 8:int(np.floor(y)) + 9,
                     int(np.floor(x)) - 8:int(np.floor(x)) + 9]
    normalization = evaluate(fx, fy).sum()
    yy, xx = np.indices((11, 11))
    return evaluate(xx, yy) / normalization


def classify(fit, rows):
    if fit.get("bound_hit"):
        return "BOUND"
    if not fit.get("success"):
        return "FAILED"
    distances = [(np.hypot(fit["x"] - r["x"], fit["y"] - r["y"]), r["source_id"]) for r in rows]
    distances.sort()
    return "AMBIGUOUS" if distances[1][0] - distances[0][0] <= 1e-12 else distances[0][1]


def trial_ellipse(fit, truth):
    if not fit.get("success") or fit.get("bound_hit") or fit.get("centroid_covariance") is None:
        return None, None
    cov = np.array(fit["centroid_covariance"])
    delta = np.array([fit["x"] - truth["x"], fit["y"] - truth["y"]])
    if cov.shape != (2, 2) or not np.all(np.isfinite(cov)) or np.min(np.linalg.eigvalsh(cov)) <= 0:
        return None, None
    quad = float(delta @ np.linalg.inv(cov) @ delta)
    return bool(quad <= -2 * np.log(.05)), quad


def audit_condition(condition, rows, selection):
    truth, trials, saved = condition["truth"], condition["trials"], condition["summary"]
    require(len(trials) == 20, "trial count")
    counts = dict.fromkeys([r["source_id"] for r in rows] + ["FAILED", "BOUND", "AMBIGUOUS"], 0)
    deltas, coverage, quadratics, sigmas, statuses = [], [], [], [], Counter()
    for trial in trials:
        fit = trial["fit"]
        label = classify(fit, rows)
        require(label == trial["assignment"], "nearest-label arithmetic")
        counts[label] += 1
        statuses[fit["status"]] += 1
        delta = None if label in ("FAILED", "BOUND", "AMBIGUOUS") else [fit["x"] - truth["x"], fit["y"] - truth["y"]]
        require(delta == trial["signed_displacement"], "signed displacement")
        if delta is not None:
            require(np.isclose(np.hypot(*delta), trial["radial_error"], atol=1e-14, rtol=0), "radial error")
            deltas.append(delta)
        covered, quad = trial_ellipse(fit, truth)
        require(covered == trial["nominal_ellipse_covers_truth"], "ellipse arithmetic")
        coverage.append(covered)
        if quad is not None:
            quadratics.append(quad)
            sigmas.extend(np.sqrt(np.diag(fit["centroid_covariance"])).tolist())
    require(counts == saved["counts"], "confusion matrix")
    complete = not any(counts[k] for k in ("FAILED", "BOUND", "AMBIGUOUS"))
    bias = np.mean(deltas, axis=0).tolist() if complete else None
    require(bias == saved["signed_mean_bias"], "vector-mean bias")
    expected_norm = float(np.linalg.norm(bias)) if bias is not None else None
    require(expected_norm == saved["bias_norm"], "bias norm")
    wrong = sum(v for k, v in counts.items() if k not in (truth["source_id"], "FAILED", "BOUND", "AMBIGUOUS"))
    require(wrong / 20 == saved["wrong_row_fraction"], "wrong fraction")
    require(sum(c is True for c in coverage) / 20 == saved["coverage_fraction"], "coverage fraction")
    require(sum(c is None for c in coverage) == saved["undefined_ellipses"], "undefined covariance count")
    require(saved["recorded_slots"] == saved["denominator"] == 20, "slot denominator")
    unmeasured = statuses["NOT_MEASURED_CONDITION_FAILURE"]
    require(saved["attempted_trials"] == 20 - unmeasured, "attempt count")
    require(saved["completed_trials"] == 20 - unmeasured - statuses["STOP_TRIAL"], "completed-record count")
    reasons = []
    if condition["scale"] == 1:
        if wrong >= 2:
            reasons.append("STOP_LOCALIZATION_CONFUSION")
        if (truth["source_id"] in (selection["target_id"], selection["nearest_id"]) and bias is not None
                and np.linalg.norm(bias) > selection["pair_separation"] / 2):
            reasons.append("STOP_LOCALIZATION_BIAS")
        if not complete or any(c is None for c in coverage):
            reasons.append("INCOMPLETE_TRIAL_OR_COVARIANCE")
    require(reasons == saved["reasons"], "condition stop rule")
    return {"truth": truth["source_id"], "roles": truth["roles"], "scale": condition["scale"], "corner": condition["corner"],
            "assignments": {k: v for k, v in counts.items() if v}, "bias": bias, "bias_norm": saved["bias_norm"],
            "coverage": saved["coverage_fraction"], "undefined": saved["undefined_ellipses"], "reasons": reasons,
            "fit_statuses": dict(statuses), "aperture_response": condition.get("aperture_response"),
            "injected_model_amplitude": condition.get("model_amplitude"),
            "quadratic_range": [min(quadratics), max(quadratics)] if quadratics else None,
            "formal_sigma_range": [min(sigmas), max(sigmas)] if sigmas else None}


def audit_field(tic, manifest, acquisition):
    result = read(ROOT / f"out/m2p-{tic}.json")
    original = read(ROOT / f"out/m1b-{tic}.json")
    catalog = read(ROOT / f"out/{'m1b' if tic == TICS[0] else 'm1e'}-{tic}.json")["catalog"]
    rows = sorted(catalog["rows_in_stamp"], key=lambda row: int(row["source_id"]))
    require(result["selection"] == manifest["selection"][str(tic)], "manifest selection")
    require(result["manifest_sha256"] == MANIFEST_HASH and not result["unknown_search_authorized"]
            and not result["physical_depth_validated"] and result["network_requests"] == 0, "science flags")
    n = len(result["negative_day_labels"])
    expected_draws = np.random.default_rng(20260912).integers(0, n, size=(20, n))
    require(np.array_equal(expected_draws, result["day_resampling_indices"]), "paired day draws")
    selection = result["selection"]
    require(len(result["conditions"]) == len(selection["locations"]) * 12, "condition closure")
    conditions = [audit_condition(c, rows, selection) for c in result["conditions"]]
    reasons = sorted({r for c in conditions for r in c["reasons"]})
    primary = result["primary"]
    if any("error" in c for c in result["conditions"]):
        reasons.append("INCOMPLETE_CONDITION")
    if any(not f.get("success") or f.get("bound_hit") for f in [primary["fit"], *primary["leave_one_day_out"]]):
        reasons.append("INCOMPLETE_PRIMARY_FIT")
    if any(not p["fit"].get("success") for p in primary["profile_hypotheses"]):
        reasons.append("INCOMPLETE_PROFILE_HYPOTHESIS")
    require(reasons == result["reasons"], "field reasons")
    expected_status = "STOP_LOCALIZATION_CONFUSION" if any(r.startswith("STOP_LOCALIZATION") for r in reasons) else (
        "VALIDATION_INCOMPLETE" if reasons else "DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE")
    require(expected_status == result["status"], "field status")
    context = next(c for c in acquisition["context"] if c["tic"] == tic)
    arrays = []
    for p in acquisition["products"]:
        if p["tic"] == tic:
            path = ROOT / "data/m2a" / p["filename"].removesuffix(".fits") / p["filename"]
            with fits.open(path, memmap=False) as hdus:
                arrays.append(hdus[0].data.copy())
    image = np.array(original["images"]["difference"])
    error = np.array(original["images"]["block_standard_error"])
    mask = np.array(original["images"]["valid_pixels"], bool)
    aperture = np.array(original["images"]["aperture"], bool)
    yy, xx = np.indices(image.shape)
    plane = np.stack([np.ones_like(image), (xx - 5) / 10, (yy - 5) / 10], axis=-1)
    fit = primary["fit"]
    independent = independent_model(arrays, context, fit["x"], fit["y"])
    prediction = fit["amplitude"] * independent + plane @ np.array(fit["plane"])
    require(np.allclose(prediction, fit["model"], atol=1e-12, rtol=1e-12), "independent primary model")
    require(np.allclose(image[mask] - prediction[mask], np.array(fit["residual"])[mask], atol=1e-12, rtol=0), "primary residual")
    score = float(np.sum(((image[mask] - prediction[mask]) / error[mask])**2))
    require(np.isclose(score, fit["weighted_residual_sum"], atol=1e-9, rtol=1e-10), "primary weighted score")
    require([p["source_id"] for p in primary["profile_hypotheses"]] == [r["source_id"] for r in rows], "all profile rows")
    for row, hypothesis in zip(rows, primary["profile_hypotheses"], strict=True):
        profile = hypothesis["fit"]
        if not profile["success"]:
            continue
        prf = independent_model(arrays, context, row["x"], row["y"])
        design = np.column_stack([prf[mask], plane[mask]]) / error[mask, None]
        values = image[mask] / error[mask]
        coef = np.linalg.solve(design.T @ design, design.T @ values)
        independent_score = float(np.sum((values - design @ coef)**2))
        require(np.isclose(independent_score, profile["weighted_residual_sum"], atol=1e-6, rtol=1e-8), "profile weighted score")
        require(np.isclose(coef[0], profile["amplitude"], atol=1e-6, rtol=1e-7), "profile signed amplitude")
    ranked = sorted([p for p in primary["profile_hypotheses"] if p["fit"]["success"]], key=lambda p: p["fit"]["weighted_residual_sum"])
    target_rank = next(i + 1 for i, p in enumerate(ranked) if p["source_id"] == selection["target_id"])
    require(classify(fit, rows) == primary["nearest_centroid_label"], "primary nearest label")
    loo = primary["leave_one_day_out"]
    negatives = [f for p in result["negative_fits"] for f in (p["flux"], p["background"])]
    return {"tic": tic, "status": expected_status, "reasons": reasons, "locations": selection,
            "condition_count": len(conditions), "trials": sum(c["summary"]["recorded_slots"] for c in result["conditions"]),
            "primary": {"xy": [fit["x"], fit["y"]], "amplitude": fit["amplitude"], "weighted_score": score,
                        "plane": fit["plane"], "source_sap_prediction": float(fit["amplitude"] * independent[aperture].sum()),
                        "plane_sap_prediction": float((plane @ np.array(fit["plane"]))[aperture].sum()),
                        "measured_sap": original["primary"]["amplitude"], "nearest_label": primary["nearest_centroid_label"],
                        "lost_fraction": fit["model_metadata"]["lost_wing_fraction"], "covariance": fit["centroid_covariance"]},
            "profiles": {"count": len(ranked), "target_rank": target_rank,
                         "best_three": [{"id": p["source_id"], "amplitude": p["fit"]["amplitude"],
                                         "score": p["fit"]["weighted_residual_sum"]} for p in ranked[:3]]},
            "loo": {"count": len(loo), "statuses": dict(Counter(f["status"] for f in loo)),
                    "x_range": [min(f["x"] for f in loo if "x" in f), max(f["x"] for f in loo if "x" in f)],
                    "y_range": [min(f["y"] for f in loo if "y" in f), max(f["y"] for f in loo if "y" in f)]},
            "negative_fit_statuses": dict(Counter(f["status"] for f in negatives)),
            "negative_signed_amplitudes": [f.get("amplitude") for f in negatives],
            "observed_amplitude_conditions": [c for c in conditions if c["scale"] == 1],
            "all_trial_fit_statuses": dict(Counter(t["fit"]["status"] for c in result["conditions"] for t in c["trials"]))}


def main():
    manifest_path = ROOT / "data/m2p/manifest.json"
    require(sha(manifest_path) == MANIFEST_HASH, "manifest identity")
    manifest = read(manifest_path)
    summary = read(ROOT / "out/m2p-summary.json")
    protected = {**manifest["dependencies"], **summary["artifacts"], "data/m2p/manifest.json": MANIFEST_HASH}
    for name, digest in protected.items():
        require(sha(ROOT / name) == digest, "input/artifact hash " + name)
    acquisition = read(ROOT / "data/m2a/manifest.json")
    reports = [audit_field(tic, manifest, acquisition) for tic in TICS]
    require(sum(r["condition_count"] for r in reports) == 96 and sum(r["trials"] for r in reports) == 1920, "population closure")
    for name, digest in protected.items():
        require(sha(ROOT / name) == digest, "post-audit mutation " + name)
    print(json.dumps({"audit": "INDEPENDENT_NUMERICAL_AND_LEDGER_PASS", "dependencies": len(manifest["dependencies"]),
                      "artifacts": len(summary["artifacts"]), "protected_files": len(protected), "reports": reports}, indent=2))


if __name__ == "__main__":
    main()
