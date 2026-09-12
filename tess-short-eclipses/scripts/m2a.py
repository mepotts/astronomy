"""One-shot acquisition and structural validation of twelve fixed TESS PRFs."""

import argparse
import importlib.util
import json
import logging
import sys
import time
import traceback
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m2a_frozen_helpers", ROOT / "scripts/m1.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
DATA = ROOT / "data/m2a"
MANIFEST = DATA / "manifest.json"
SUMMARY = ROOT / "out/m2a-summary.json"
PROTOCOL = ROOT / "M2a-PROTOCOL-2026-09-12.md"
BASE = "https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/"
SOURCE_HASH = "22c46cbfd34877ac66d7b1fcd411ecb8b323aca5ea987da58d62ea141ed29115"
RUNNER_HASH = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"
FIELDS = ((450781262, 99, 3, 2019107181902, (1025, 1536), (1580, 2092), (1720, 1488)),
          (53206761, 72, 4, 2019107181902, (1536, 2048), (557, 1069), (672, 1798)),
          (2041210548, 57, 2, 2019107181901, (1536, 2048), (1580, 2092), (1889, 1939)))
LOGGER = logging.getLogger(__name__)


def read(path):
    return json.loads(path.read_bytes())


def products():
    rows = []
    for tic, _sector, camera, timestamp, grid_rows, columns, _origin in FIELDS:
        for row in grid_rows:
            for column in columns:
                name = f"tess{timestamp}-prf-{camera}-3-row{row:04d}-col{column:04d}.fits"
                rows.append({"tic": tic, "camera": camera, "ccd": 3, "row": row, "column": column,
                             "filename": name, "url": f"{BASE}cam{camera}_ccd3/{name}"})
    return rows


def product(name):
    selected = [row for row in products() if row["filename"] == name]
    if len(selected) != 1:
        raise ValueError("STOP_PRODUCT_SELECTION")
    return selected[0]


def exact(header, key, expected):
    if header.count(key) != 1:
        raise ValueError(f"STOP_KEY_COUNT:{key}")
    actual = header[key]
    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)) or not np.isclose(actual, expected, atol=1e-12, rtol=0):
            raise ValueError(f"STOP_KEY_VALUE:{key}")
    elif actual != expected:
        raise ValueError(f"STOP_KEY_VALUE:{key}")


def physical(header, column, row, reference, step, axis_names):
    exact(header, "WCSNAMEP", "PHYSICAL")
    exact(header, "WCSAXESP", 2)
    for axis, value in ((1, column), (2, row)):
        for key, expected in ((f"CTYPE{axis}P", axis_names[axis - 1]), (f"CUNIT{axis}P", "PIXEL"),
                              (f"CRPIX{axis}P", reference), (f"CRVAL{axis}P", value),
                              (f"CDELT{axis}P", step)):
            exact(header, key, expected)
    if any(key.startswith(("PC1_", "PC2_", "CD1_", "CD2_", "CROTA")) and key.endswith("P") for key in header):
        raise ValueError("STOP_PHYSICAL_CROSS_TERMS")


def context():
    result = []
    for tic, sector, camera, _timestamp, rows, columns, origin in FIELDS:
        old = read(ROOT / f"out/m1b-{tic}.json")
        path = ROOT / "data/m1" / str(tic) / old["input"]["filename"]
        if M.sha(path) != old["input"]["sha256"]:
            raise ValueError("STOP_TPF_HASH")
        with fits.open(path, memmap=True) as hdus:
            for key, value in (("TICID", tic), ("SECTOR", sector), ("CAMERA", camera), ("CCD", 3)):
                exact(hdus[0].header, key, value)
            aperture = hdus[2].header
            exact(aperture, "NAXIS1", 11)
            exact(aperture, "NAXIS2", 11)
            physical(aperture, *origin, 1, 1, ("RAWX", "RAWY"))
            for index in (4, 5):
                for axis, value in ((1, origin[0]), (2, origin[1])):
                    exact(hdus[1].header, f"{axis}CRV{index}P", value)
                    exact(hdus[1].header, f"{axis}CRP{index}P", 1)
                    exact(hdus[1].header, f"{axis}CDL{index}P", 1)
        if not (columns[0] <= origin[0] <= origin[0] + 10 <= columns[1]
                and rows[0] <= origin[1] <= origin[1] + 10 <= rows[1]):
            raise ValueError("STOP_GRID_BRACKET")
        result.append({"tic": tic, "origin": list(origin), "rows": list(rows), "columns": list(columns),
                       "native_target": [origin[i] + old["target_xy_zero_based"][i] for i in range(2)],
                       "extra_column_shift": 0, "extra_index_shift": 0})
    return result


def dependencies():
    if M.sha(ROOT / "scripts/m1.py") != SOURCE_HASH or M.sha(M.RUNNER) != RUNNER_HASH:
        raise ValueError("STOP_HELPER_PROVENANCE")
    paths = ["scripts/m2a.py", "tests/test_m2a.py", "tests/test_m2a_review.py", PROTOCOL.name,
             "scripts/m1.py", "M1-PROTOCOL-2026-09-12.md", "scripts/m1b.py", "M1b-PROTOCOL-2026-09-12.md",
             "NEXT-LOCALIZATION-PROPOSAL.md", "PRF-COORDINATE-AUDIT-2026-09-12.md"]
    paths += [f"out/m1b-{field[0]}.json" for field in FIELDS]
    return {path: M.sha(ROOT / path) for path in paths}


def prepare():
    M.save(MANIFEST, {"dependencies": dependencies(), "runner_sha256": M.sha(M.RUNNER),
                      "context": context(), "products": products(), "unknown_search_authorized": False})


def verify():
    manifest = read(MANIFEST)
    if (manifest["dependencies"] != dependencies() or manifest["runner_sha256"] != M.sha(M.RUNNER)
            or manifest["context"] != context() or manifest["products"] != products()
            or manifest["unknown_search_authorized"] is not False):
        raise ValueError("STOP_MANIFEST_CHANGED")


def validate(path, selected):
    size = path.stat().st_size
    if not 0 < size <= 300_000 or size % 2880:
        raise ValueError("STOP_FITS_SIZE")
    result = []
    with fits.open(path, memmap=False, lazy_load_hdus=False) as hdus:
        hdus.verify("exception")
        if len(hdus) != 2 or type(hdus[0]) is not fits.PrimaryHDU or type(hdus[1]) is not fits.ImageHDU:
            raise ValueError("STOP_HDU_STRUCTURE")
        for index, hdu in enumerate(hdus):
            header = hdu.header
            expected = {"BITPIX": -64, "NAXIS": 2, "NAXIS1": 117, "NAXIS2": 117,
                        "ORIGIN": "MIT", "TELESCOP": "TESS", "CAM": selected["camera"], "CCD": selected["ccd"],
                        "CCD_RREF": selected["row"], "CCD_CREF": selected["column"], "NSAMP": 9, "PRF_RES": 2.35,
                        "DATATYPE": "PRF" if index == 0 else "Uncertainties"}
            if index == 0 or "VERSION" in header:
                expected["VERSION"] = "UPDATED_2.0"
            for key, value in expected.items():
                exact(header, key, value)
            for key, value in (("BSCALE", 1), ("BZERO", 0)):
                if key in header:
                    exact(header, key, value)
            physical(header, selected["column"], selected["row"], 59, 1 / 9, ("RAWX", "RAWY"))
            if ("CHECKSUM" in header and hdu.verify_checksum() != 1) or ("DATASUM" in header and hdu.verify_datasum() != 1):
                raise ValueError("STOP_FITS_CHECKSUM")
            values = hdu.data
            if values.shape != (117, 117) or values.dtype.kind != "f" or values.dtype.itemsize != 8:
                raise ValueError("STOP_ARRAY_SCHEMA")
            if not np.all(np.isfinite(values)):
                raise ValueError("STOP_ARRAY_NONFINITE")
            negative = int(np.count_nonzero(values < 0))
            total = values.sum()
            if (not np.isfinite(total) or (index == 1 and negative)
                    or (index == 0 and (not np.any(values > 0) or total <= 0))):
                raise ValueError("STOP_ARRAY_SUPPORT")
            result.append({"index": index, "shape": list(values.shape), "negative_samples": negative,
                           "bunit": header.get("BUNIT"), "cards": header.tostring(sep="\n", endcard=True, padding=False)})
        info = hdus[-1].fileinfo()
        if info["datLoc"] + info["datSpan"] != size:
            raise ValueError("STOP_TRAILING_OR_TRUNCATED_BYTES")
    return {"status": "PRF_PRODUCT_STRUCTURALLY_VALID", "product": selected, "bytes": size,
            "sha256": M.sha(path), "hdus": result, "reference_sample_zero_based": [58, 58],
            "native_reference": [selected["column"], selected["row"]],
            "localization_validated": False, "unknown_search_authorized": False}


def folder_for(name):
    product(name)
    return DATA / name.removesuffix(".fits")


def attempt(name):
    return {"product": product(name), "manifest_sha256": M.sha(MANIFEST)}


def worker(name):
    import requests
    from requests.adapters import HTTPAdapter

    folder = folder_for(name)
    planned = attempt(name)
    if (read(folder / "attempt.json") != planned
            or read(DATA / "run-start.json") != {"approved_manifest_sha256": M.sha(MANIFEST)}):
        raise ValueError("STOP_ATTEMPT")
    M.save(folder / "worker-start.json", planned)
    path = folder / name
    try:
        verify()
        with requests.Session() as session:
            session.mount("https://", HTTPAdapter(max_retries=0))
            with session.get(planned["product"]["url"], timeout=(30, 30), stream=True, allow_redirects=False) as response:
                if response.status_code != 200:
                    raise ValueError(f"STOP_HTTP:{response.status_code}")
                size = M.stream_response(response, path, 300_000, time.monotonic() + 40)
                length = response.headers.get("Content-Length")
            M.save(folder / "response-receipt.json", {**planned, "bytes": size, "sha256": M.sha(path),
                                                      "http_content_length": length})
        M.save(folder / "validation.json", validate(path, planned["product"]))
    except Exception:
        LOGGER.exception("M2a worker stopped without retry or substitution")
        M.save(folder / "failure.json", {"traceback": traceback.format_exc(),
                                         "partial_bytes": path.stat().st_size if path.exists() else 0})
        raise


def artifacts(name):
    return {str(path.relative_to(ROOT)).replace("\\", "/"): M.sha(path)
            for path in sorted(folder_for(name).glob("*")) if path.is_file()}


def complete_product(name):
    """Verify successful worker evidence, not merely its process exit code."""
    folder = folder_for(name)
    planned = attempt(name)
    if read(folder / "attempt.json") != planned or read(folder / "worker-start.json") != planned:
        raise ValueError("STOP_WORKER_RECEIPT")
    if (folder / "failure.json").exists():
        raise ValueError("STOP_CONFLICTING_FAILURE")
    path = folder / name
    raw = read(folder / "response-receipt.json")
    length = raw.get("http_content_length")
    if length is not None and (not isinstance(length, str) or not length.isascii()
                               or not length.isdecimal() or not 0 <= int(length) <= 300_000):
        raise ValueError("STOP_HTTP_LENGTH_RECEIPT")
    if raw != {**planned, "bytes": path.stat().st_size, "sha256": M.sha(path), "http_content_length": length}:
        raise ValueError("STOP_RESPONSE_RECEIPT")
    actual = validate(path, product(name))
    if read(folder / "validation.json") != actual:
        raise ValueError("STOP_VALIDATION_REPLAY")
    return actual


def terminal_checks(summary):
    expected_keys = {"manifest_sha256", "outcomes", "status", "localization_validated", "unknown_search_authorized"}
    if (set(summary) != expected_keys or summary["localization_validated"] is not False
            or summary["unknown_search_authorized"] is not False):
        raise ValueError("STOP_SUMMARY_FLAGS")
    stopped = False
    for row in summary["outcomes"]:
        if set(row) != {"filename", "returncode", "worker_returncode", "status", "output", "elapsed_seconds", "artifacts"}:
            raise ValueError("STOP_OUTCOME_KEYS")
        code, worker_code, status = row["returncode"], row["worker_returncode"], row["status"]
        if (type(code) is not int or (worker_code is not None and type(worker_code) is not int)
                or not isinstance(row["output"], str) or not isinstance(row["elapsed_seconds"], (int, float))
                or not np.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0):
            raise ValueError("STOP_OUTCOME_TYPES")
        if stopped and status != "STOP_NOT_LAUNCHED":
            raise ValueError("STOP_LAUNCH_SEQUENCE")
        if status == "PRF_PRODUCT_STRUCTURALLY_VALID":
            if code != 0 or worker_code != 0:
                raise ValueError("STOP_SUCCESS_CODE")
        elif status in ("STOP_PRF_PRODUCT", "STOP_NOT_LAUNCHED"):
            if code == 0 or (status == "STOP_NOT_LAUNCHED" and worker_code is not None):
                raise ValueError("STOP_FAILURE_CODE")
            stopped = True
        else:
            raise ValueError("STOP_OUTCOME_STATUS")
    expected = "STOP_PRF_PRODUCT" if stopped else "PRF_PRODUCTS_STRUCTURALLY_VALID"
    if summary["status"] != expected:
        raise ValueError("STOP_SUMMARY_STATUS")


def run(approved):
    verify()
    if approved != M.sha(MANIFEST):
        raise ValueError("STOP_REVIEW_GO_REQUIRED")
    M.save(DATA / "run-start.json", {"approved_manifest_sha256": approved})
    stopped = None
    try:
        spec = importlib.util.spec_from_file_location("m2a_runner", M.RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
    except Exception:
        LOGGER.exception("M2a launcher import failed")
        stopped = traceback.format_exc()
    outcomes = []
    for selected in products():
        name = selected["filename"]
        start = time.monotonic()
        worker_code = None
        if stopped is None:
            try:
                M.save(folder_for(name) / "attempt.json", attempt(name))
            except Exception:
                LOGGER.exception("M2a attempt reservation failed")
                stopped = traceback.format_exc()
        if stopped is not None:
            code, output, status = 1, stopped, "STOP_NOT_LAUNCHED"
        else:
            try:
                code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                                   "run", "--worker", name], 45)
                worker_code = code
            except Exception:
                LOGGER.exception("M2a worker launch/cleanup failed")
                code, output = 1, traceback.format_exc()
            if code == 0:
                try:
                    complete_product(name)
                except Exception:
                    LOGGER.exception("M2a successful exit lacked valid complete product evidence")
                    code, output = 1, output + "\nParent validation failure:\n" + traceback.format_exc()
            status = "PRF_PRODUCT_STRUCTURALLY_VALID" if code == 0 else "STOP_PRF_PRODUCT"
            if code:
                stopped = f"Prior product {name} failed; no further launch"
        row = {"filename": name, "returncode": code, "worker_returncode": worker_code, "status": status, "output": output,
               "elapsed_seconds": time.monotonic() - start, "artifacts": artifacts(name)}
        M.save(DATA / (name + ".outcome.json"), row)
        outcomes.append(row)
        print(json.dumps(row), flush=True)
    summary = {"manifest_sha256": M.sha(MANIFEST), "outcomes": outcomes,
               "status": "STOP_PRF_PRODUCT" if stopped else "PRF_PRODUCTS_STRUCTURALLY_VALID",
               "localization_validated": False, "unknown_search_authorized": False}
    terminal_checks(summary)
    M.save(SUMMARY, summary)


def replay():
    verify()
    summary = read(SUMMARY)
    terminal_checks(summary)
    if (summary["manifest_sha256"] != M.sha(MANIFEST)
            or [row["filename"] for row in summary["outcomes"]] != [p["filename"] for p in products()]
            or read(DATA / "run-start.json") != {"approved_manifest_sha256": M.sha(MANIFEST)}):
        raise ValueError("STOP_SUMMARY")
    for row in summary["outcomes"]:
        name = row["filename"]
        folder = folder_for(name)
        if row != read(DATA / (name + ".outcome.json")) or row["artifacts"] != artifacts(name):
            raise ValueError("STOP_OUTCOME_REPLAY")
        if row["status"] != "STOP_NOT_LAUNCHED" and read(folder / "attempt.json") != attempt(name):
            raise ValueError("STOP_ATTEMPT_REPLAY")
        if row["returncode"] == 0:
            complete_product(name)
    print("EXACT_M2A_REPLAY_PASS: no network, no writes, no fit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "replay"))
    parser.add_argument("--worker", choices=[p["filename"] for p in products()])
    parser.add_argument("--approved-manifest-sha256")
    args = parser.parse_args()
    if args.worker:
        if args.stage != "run":
            raise ValueError("STOP_WORKER_STAGE")
        worker(args.worker)
    elif args.stage == "run":
        run(args.approved_manifest_sha256)
    else:
        {"prepare": prepare, "replay": replay}[args.stage]()


if __name__ == "__main__":
    main()
