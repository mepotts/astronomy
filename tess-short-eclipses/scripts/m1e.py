"""Conditional one-shot missing-field metadata; no new pixels or fitting."""

import argparse
import importlib.util
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1e_fresh_m1d2", ROOT / "scripts/m1d2.py")
D2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D2)
D = D2.BASE
C = D.OLD
M = C.m1
DATA = ROOT / "data/m1e"
MANIFEST = DATA / "manifest.json"
PROTOCOL = ROOT / "M1e-PROTOCOL-2026-09-12.md"
SUMMARY = ROOT / "out/m1e-summary.json"
TARGETS = (53206761, 2041210548)
URL = "https://gaia.ari.uni-heidelberg.de/tap/sync"
LOGGER = logging.getLogger(__name__)
D2_SOURCE_HASH = "6415e4f371a203a2cce7bbf13f356ed0e8beafa90054a57bfee173fa95a71db8"
D2_MANIFEST_HASH = "5a90493fc17e08200c79bb7e12ee9c1c7676bd859f8b66e0e583d7969e1efab0"


def require_parity(result):
    parity = result.get("parity", {})
    if (result.get("status") != "OFFLINE_CATALOG_PARITY_PASS" or result.get("rows") != 1290
            or result.get("network_requests") != 0 or result.get("pixel_recalculation") is not False
            or result.get("unknown_search_authorized") is not False
            or result.get("numeric_decoders") != "unchanged_m1d_struct_and_numpy"
            or parity.get("status") != "PARITY_PASS" or parity.get("rows") != 1290
            or any(parity.get(key) is not True for key in ("source_ids_exact", "masks_exact", "units_validated"))
            or set(parity.get("columns", {})) != set(C.TOLERANCES)):
        raise ValueError("STOP_M1D_PARITY_REQUIRED")
    for name, tolerance in C.TOLERANCES.items():
        column = parity["columns"][name]
        delta = column.get("max_abs_difference")
        if (column.get("absolute_tolerance") != tolerance
                or (delta is not None and (not np.isfinite(delta) or not 0 <= delta <= tolerance))):
            raise ValueError("STOP_M1D_TOLERANCES")


def prerequisite():
    if (M.sha(ROOT / "scripts/m1d2.py") != D2_SOURCE_HASH
            or M.sha(ROOT / "out/m1d2-manifest.json") != D2_MANIFEST_HASH):
        raise ValueError("STOP_M1D2_FROZEN_HASH")
    retained = C.read_json(ROOT / "out/m1d2-result.json")
    require_parity(retained)
    outcome = C.read_json(ROOT / "out/m1d2-worker-outcome.json")
    runtime = C.read_json(ROOT / "out/m1d2-runtime.json")
    if (outcome.get("returncode") != 0 or outcome.get("status") != "WORKER_COMPLETED"
            or not 0 < runtime["peak_working_set_bytes"] <= 1_000_000_000
            or not 0 <= runtime["elapsed_seconds"] <= 60):
        raise ValueError("STOP_M1D_WORKER")
    if D2.execute() != retained:
        raise ValueError("STOP_M1D_EXACT_REPLAY")


def dependencies():
    paths = set(D2.dependencies()) | set(D.dependencies()) | set(C.dependencies())
    paths.update({"scripts/m1e.py", "tests/test_m1e.py", "tests/test_m1e_review.py", PROTOCOL.name,
                  "out/m1d-manifest.json", "out/m1d-result.json", "out/m1d-worker-outcome.json",
                  "out/m1d-runtime.json", "scripts/m0.py", "M0-PROTOCOL-2026-09-12.md",
                  "M0b-PROTOCOL-2026-09-12.md", "out/m1d2-manifest.json", "out/m1d2-result.json",
                  "out/m1d2-worker-outcome.json", "out/m1d2-runtime.json"})
    paths.update(f"out/m0b-{tic}.json" for tic in TARGETS)
    return {path: M.sha(ROOT / path) for path in sorted(paths)}


def prepare():
    prerequisite()
    M.save(MANIFEST, {"dependencies": dependencies(), "url": URL, "targets": list(TARGETS),
                      "utc": datetime.now(timezone.utc).isoformat(),
                      "unknown_search_authorized": False})


def verify():
    prerequisite()
    manifest = C.read_json(MANIFEST)
    if (manifest["dependencies"] != dependencies() or manifest["url"] != URL
            or manifest["targets"] != list(TARGETS) or manifest["unknown_search_authorized"] is not False):
        raise ValueError("STOP_MANIFEST_CHANGED")


def plan(tic):
    if tic not in TARGETS:
        raise ValueError("STOP_TARGET")
    prior = C.read_json(ROOT / f"data/m1/{tic}/catalog-query.json")
    return {"tic": tic, "url": URL, "adql": prior["adql"], "manifest_sha256": M.sha(MANIFEST)}


def validated(path):
    if not 0 < path.stat().st_size <= 5_000_000:
        raise ValueError("STOP_RESPONSE_SIZE")
    return D2.decode(path.read_bytes())


def response_path(tic):
    folder = DATA / str(tic)
    receipt = C.read_json(folder / "catalog-receipt.json")
    path = folder / "gaia-dr3.xml"
    if (receipt["sha256"] != M.sha(path) or receipt["bytes"] != path.stat().st_size
            or receipt["manifest_sha256"] != M.sha(MANIFEST) or receipt["tic"] != tic
            or receipt["url"] != URL or receipt["rows"] != len(validated(path))):
        raise ValueError("STOP_RESPONSE_PROVENANCE")
    return path


def diagnostic(tic):
    response_path(tic)
    old, wcs, epoch = C.context(tic)

    class ValidatedTable:
        @staticmethod
        def read(path, **_kwargs):
            return validated(path)

    saved = M.DATA, M.Table
    fit = old["centroid_surrogate"]
    try:
        M.DATA, M.Table = DATA, ValidatedTable
        catalog = M.catalog_comparison(tic, wcs, old["target_header_radec"], (fit["x"], fit["y"]),
                                       epoch, np.asarray(old["images"]["difference"]).shape)
    finally:
        M.DATA, M.Table = saved
    return M.clean({"tic": tic, "status": "METADATA_DIAGNOSTIC_VALIDATION_INCOMPLETE",
                    "manifest_sha256": M.sha(MANIFEST), "original_result_sha256": M.sha(ROOT / f"out/m1b-{tic}.json"),
                    "fixed_centroid": [fit["x"], fit["y"]], "catalog": catalog,
                    "pixel_recalculation": False, "unknown_search_authorized": False})


def worker(tic):
    import requests
    from requests.adapters import HTTPAdapter

    folder = DATA / str(tic)
    path = folder / "gaia-dr3.xml"
    expected = plan(tic)
    if (C.read_json(folder / "attempt.json") != expected
            or C.read_json(DATA / "run-start.json") != {"approved_manifest_sha256": M.sha(MANIFEST)}):
        raise ValueError("STOP_ATTEMPT")
    M.save(folder / "worker-start.json", expected)
    try:
        verify()
        with requests.Session() as session:
            session.mount("https://", HTTPAdapter(max_retries=0))
            with session.post(URL, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
                                         "QUERY": expected["adql"]}, stream=True, timeout=(45, 45),
                              allow_redirects=False) as response:
                if response.status_code != 200:
                    raise ValueError(f"STOP_HTTP:{response.status_code}")
                size = M.stream_response(response, path, 5_000_000, time.monotonic() + 55)
            raw = {**expected, "bytes": size, "sha256": M.sha(path)}
            M.save(folder / "response-receipt.json", raw)
        table = validated(path)
        M.save(folder / "catalog-receipt.json", {**raw, "rows": len(table)})
        M.save(ROOT / f"out/m1e-{tic}.json", diagnostic(tic))
    except Exception:
        LOGGER.exception("M1e worker stopped; no retry or fallback")
        M.save(folder / "failure.json", {"traceback": traceback.format_exc(),
                                         "partial_bytes": path.stat().st_size if path.exists() else 0})
        raise


def artifact_hashes(tic):
    folder = DATA / str(tic)
    paths = list(folder.glob("*")) + [ROOT / f"out/m1e-{tic}.json"]
    return {str(path.relative_to(ROOT)).replace("\\", "/"): M.sha(path)
            for path in sorted(paths) if path.is_file()}


def run(approved_hash):
    verify()
    if approved_hash != M.sha(MANIFEST):
        raise ValueError("STOP_EXPLICIT_REVIEW_GO_REQUIRED")
    M.save(DATA / "run-start.json", {"approved_manifest_sha256": approved_hash})
    try:
        runner_spec = importlib.util.spec_from_file_location("m1e_runner", M.RUNNER)
        runner = importlib.util.module_from_spec(runner_spec)
        runner_spec.loader.exec_module(runner)
    except Exception:
        LOGGER.exception("M1e launcher import failed before requests")
        runner, prelaunch_error = None, traceback.format_exc()
    else:
        prelaunch_error = None
    outcomes = []
    for tic in TARGETS:
        if prelaunch_error is None:
            try:
                M.save(DATA / str(tic) / "attempt.json", plan(tic))
            except Exception:
                LOGGER.exception("M1e attempt reservation failed; remaining fields not launched")
                prelaunch_error = traceback.format_exc()
        if prelaunch_error is not None:
            code, output, status = 1, prelaunch_error, "STOP_NOT_LAUNCHED"
        else:
            try:
                code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                                   "run", "--worker", str(tic)], 60)
            except Exception:
                LOGGER.exception("M1e worker launch/cleanup failed")
                code, output = 1, traceback.format_exc()
            status = "METADATA_DIAGNOSTIC_VALIDATION_INCOMPLETE" if code == 0 else "STOP_CATALOG_UNAVAILABLE"
        row = {"tic": tic, "returncode": code, "output": output,
               "status": status,
               "artifacts": artifact_hashes(tic)}
        M.save(DATA / f"outcome-{tic}.json", row)
        outcomes.append(row)
        print(json.dumps(row), flush=True)
    M.save(SUMMARY, {"manifest_sha256": M.sha(MANIFEST), "outcomes": outcomes,
                     "status": "STOP_PRELAUNCH" if prelaunch_error else "VALIDATION_INCOMPLETE", "pixel_recalculation": False,
                     "unknown_search_authorized": False})


def replay():
    verify()
    summary = C.read_json(SUMMARY)
    if (summary["manifest_sha256"] != M.sha(MANIFEST)
            or [row["tic"] for row in summary["outcomes"]] != list(TARGETS)
            or C.read_json(DATA / "run-start.json") != {"approved_manifest_sha256": M.sha(MANIFEST)}):
        raise ValueError("STOP_SUMMARY")
    for row in summary["outcomes"]:
        tic = row["tic"]
        if (C.read_json(DATA / f"outcome-{tic}.json") != row
                or artifact_hashes(tic) != row["artifacts"]):
            raise ValueError("STOP_OUTCOME_REPLAY")
        if row["status"] != "STOP_NOT_LAUNCHED" and C.read_json(DATA / str(tic) / "attempt.json") != plan(tic):
            raise ValueError("STOP_ATTEMPT_REPLAY")
        if row["returncode"] == 0 and diagnostic(tic) != C.read_json(ROOT / f"out/m1e-{tic}.json"):
            raise ValueError("STOP_DIAGNOSTIC_REPLAY")
    print("EXACT_M1E_REPLAY_PASS: no network, no writes, no pixel recalculation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "replay"))
    parser.add_argument("--worker", type=int, choices=TARGETS)
    parser.add_argument("--approved-manifest-sha256")
    args = parser.parse_args()
    if args.worker is not None:
        if args.stage != "run":
            raise ValueError("STOP_WORKER_STAGE")
        worker(args.worker)
    elif args.stage == "run":
        run(args.approved_manifest_sha256)
    else:
        {"prepare": prepare, "replay": replay}[args.stage]()


if __name__ == "__main__":
    main()
