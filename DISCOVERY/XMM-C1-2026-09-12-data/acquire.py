"""Four frozen known-control products: bounded transfer, gzip and FITS headers only."""

import ctypes
import gzip
import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import json
import logging
import math
import os
import shutil
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C1-2026-09-12.md"
C0D_PATH = HERE.parent / "XMM-C0d-2026-09-12-data/metadata.py"
C0D_HASH = "de1d481b185067722546edca1a51dadcd6a5a7fd7d328e60f0ad5d6980272af3"
OUTCOME_HASH = "7895f2fd39ce85ab745fbff40a291abbf7376086e9f58a2245352b2c348453a3"
STRUCTURE_PATH = HERE.parent / "xmm_structure.py"
STRUCTURE_HASH = "96d9497dbdd45d2561fc0bbb27a0c11d6fbad91cd42c0b14191378dd9fd7fa63"
STRUCTURE_TEST = HERE.parent / "test_xmm_structure.py"
STRUCTURE_TEST_HASH = "4b1bb863a29543ecb6957a417b3115155fa74b625c300d86524a4c8ac44af1aa"
STRUCTURE_REVIEW = HERE.parent / "test_xmm_structure_review.py"
STRUCTURE_REVIEW_HASH = "a062ddea63b2c8364395ed61ead99e2cc12031bcec3065aa24ca61dbee1d6b10"
HELPER = HERE.parents[1] / "dyson-revet/scripts/check_e_release.py"
HELPER_HASH = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"
EXPECTED = (109245605, 7643540, 9972723, 120581)
EXPANDED_FILE_CAP = 1073741824
EXPANDED_TOTAL_CAP = 2147483648
HEADER_CAP = 2097152
JSON_CAP = 10485760
RESERVE = 262144
MEMORY_CAP = 1000000000
SECONDS = 300
CHUNK = 1048576
PASS = "CONTROL_BUNDLE_RETAINED_HEADERS_ONLY"
DEADLINE = None
PEAK = 0
LOGGER = logging.getLogger(__name__)


def sha(path, *, monitor=True):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
            if monitor:
                checkpoint()
    return digest.hexdigest()


def load_pinned(name, path, digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("STOP_DEPENDENCY_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("Unexpected module identity")
            return compile(raw, str(path), "exec")

    spec = importlib.util.spec_from_file_location(name, path, loader=VerifiedLoader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def peak_memory():
    """Small direct reuse of tess-short-eclipses/scripts/m1d.py:178-199's Windows pattern."""
    if os.name != "nt":
        raise RuntimeError("STOP_MEMORY_RUNTIME")
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("peak", "working", "quota_peak_paged", "quota_paged",
             "quota_peak_nonpaged", "quota_nonpaged", "pagefile", "peak_pagefile")]
    record = Counters()
    record.cb = ctypes.sizeof(record)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    library = ctypes.WinDLL("psapi", use_last_error=True)
    library.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
    if not library.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(record), record.cb):
        raise RuntimeError("STOP_MEMORY_MEASUREMENT")
    return int(record.peak)


def checkpoint():
    global PEAK
    PEAK = max(PEAK, peak_memory())
    if PEAK > MEMORY_CAP:
        raise ValueError("STOP_PEAK_MEMORY")
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise ValueError("STOP_TOTAL_DEADLINE")


def read(name):
    return json.loads((HERE / name).read_bytes())


def json_bytes(value, *, monitor=True):
    result = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if monitor:
        checkpoint()
    return result


def save(name, value, *, terminal=False, header=False, peak_key=None):
    global PEAK
    raw = json_bytes(value, monitor=not terminal)
    if peak_key is not None:
        # Terminal receipts must survive a lifetime high-water mark above the ceiling.
        # Sample after serialization as well as after the preceding artifact hashing.
        PEAK = max(PEAK, peak_memory())
        value[peak_key] = PEAK
        if PEAK > MEMORY_CAP:
            value.update(status="STOP", error_code="STOP_PEAK_MEMORY")
        raw = json_bytes(value, monitor=False)
        PEAK = max(PEAK, peak_memory())
        value[peak_key] = PEAK
        if PEAK > MEMORY_CAP:
            value.update(status="STOP", error_code="STOP_PEAK_MEMORY")
        raw = json_bytes(value, monitor=False)
    used = sum(p.stat().st_size for p in HERE.rglob("*.json"))
    if (header and len(raw) > HEADER_CAP) or used + len(raw) > JSON_CAP - (0 if terminal else RESERVE):
        raise ValueError("STOP_JSON_BUDGET")
    destination = HERE / name
    destination.parent.mkdir(exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(raw)


def head_plan():
    old = load_pinned("c1_frozen_metadata", C0D_PATH, C0D_HASH)
    outcome_path = C0D_PATH.with_name("outcome.json")
    if sha(outcome_path) != OUTCOME_HASH:
        raise ValueError("STOP_HEAD_OUTCOME_HASH")
    outcome = json.loads(outcome_path.read_bytes())
    for name, digest in outcome["artifacts"].items():
        if sha(C0D_PATH.with_name(name)) != digest:
            raise ValueError("STOP_HEAD_ARTIFACT_HASH")
    old.assess(outcome["worker_returncode"])
    result = []
    for item, size in zip(old.plan()[:4], EXPECTED, strict=True):
        n = item["slot"]
        http = old.read(f"slot-{n}-http.json")
        receipt = old.read(f"slot-{n}-result.json")
        if old.measurement(item, http) != {"advertised_compressed_bytes": size, "body": None, "body_bytes_read": 0}:
            raise ValueError("STOP_HEAD_SIZE")
        if receipt != {"slot": item, "status": "OK", **old.measurement(item, http)}:
            raise ValueError("STOP_HEAD_RECEIPT")
        result.append({"slot": n, "method": "GET", "url": item["url"],
                       "filename": Path(item["url"]).name, "expected_bytes": size,
                       "head_headers": http["headers"]})
    return result


def binding(protocol):
    if (sha(HELPER) != HELPER_HASH or sha(STRUCTURE_PATH) != STRUCTURE_HASH
            or sha(STRUCTURE_TEST) != STRUCTURE_TEST_HASH or sha(STRUCTURE_REVIEW) != STRUCTURE_REVIEW_HASH):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"plan": head_plan(), "source_sha256": sha(SOURCE), "tests_sha256": sha(HERE / "test_acquire.py"),
            "protocol_sha256": sha(protocol), "c0d_outcome_sha256": OUTCOME_HASH,
            "c0d_source_sha256": C0D_HASH, "structure_sha256": STRUCTURE_HASH,
            "structure_tests_sha256": STRUCTURE_TEST_HASH, "structure_review_tests_sha256": STRUCTURE_REVIEW_HASH,
            "helper_sha256": HELPER_HASH,
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve())},
            "caps": {"seconds": SECONDS, "expanded_file": EXPANDED_FILE_CAP, "expanded_total": EXPANDED_TOTAL_CAP,
                     "peak_memory": MEMORY_CAP, "header_json": HEADER_CAP, "all_json": JSON_CAP}}


def verify_binding():
    if read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def file_record(path):
    return {"bytes": path.stat().st_size, "sha256": sha(path)} if path.exists() else None


def paths(slot):
    return HERE / "products" / slot["filename"], HERE / "products" / (slot["filename"][:-4] + ".fits")


def validate_http(slot, record):
    old = load_pinned("c1_header_rules", C0D_PATH, C0D_HASH)
    headers = record["headers"]
    if (set(record) != {"method", "url", "status", "headers"} or record["method"] != "GET"
            or record["url"] != slot["url"] or record["status"] != 200
            or not set(headers) <= set(old.SAFE_HEADERS)):
        raise ValueError("STOP_HTTP_IDENTITY")
    if (old.single(headers, "Content-Encoding", "identity").lower() not in ("identity", "")
            or old.length(headers.get("Content-Length", []), True) != slot["expected_bytes"]):
        raise ValueError("STOP_HTTP_LENGTH_OR_ENCODING")
    for key in ("ETag", "Last-Modified"):
        if key in slot["head_headers"] and old.single(headers, key) != old.single(slot["head_headers"], key):
            raise ValueError("STOP_CHANGED_PRODUCT")


def download(slot):
    import requests

    old = load_pinned("c1_safe_headers", C0D_PATH, C0D_HASH)
    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError("STOP_HEADER_PARSER")
    with requests.Session() as session:
        session.trust_env = False
        session.auth = None
        session.cookies.clear()
        checkpoint()
        with session.get(slot["url"], timeout=(5, 15), stream=True, allow_redirects=False,
                         headers={"Accept-Encoding": "identity"}) as response:
            headers = {k: response.raw.headers.getlist(k) for k in old.SAFE_HEADERS if response.raw.headers.getlist(k)}
            if sum(len(x) for values in headers.values() for x in values) > 65536:
                raise ValueError("STOP_SAFE_HEADER_CAP")
            http = {"method": response.request.method, "url": response.url,
                    "status": response.status_code, "headers": headers}
            save(f"slot-{slot['slot']}-http.json", http)
            validate_http(slot, http)
            count = 0
            paths(slot)[0].parent.mkdir(exist_ok=True)
            with paths(slot)[0].open("xb") as stream:
                while True:
                    checkpoint()
                    block = response.raw.read(min(CHUNK, slot["expected_bytes"] - count + 1), decode_content=False)
                    if not block:
                        break
                    keep = block[:slot["expected_bytes"] - count]
                    stream.write(keep)
                    count += len(keep)
                    if len(block) > len(keep):
                        raise ValueError("STOP_RAW_BYTE_CAP")
            if count != slot["expected_bytes"]:
                raise ValueError("STOP_RAW_LENGTH")
    checkpoint()


def expand(slot):
    raw, expanded = paths(slot)
    existing = sum(p.stat().st_size for p in (HERE / "products").glob("*.fits"))
    cap = min(EXPANDED_FILE_CAP, EXPANDED_TOTAL_CAP - existing)
    if cap <= 0:
        raise ValueError("STOP_EXPANDED_TOTAL_CAP")
    count = 0
    with gzip.open(raw, "rb") as source, expanded.open("xb") as destination:
        while True:
            checkpoint()
            chunk = source.read(min(CHUNK, cap - count + 1))
            if not chunk:
                break
            keep = chunk[:cap - count]
            destination.write(keep)
            count += len(keep)
            if len(chunk) > len(keep):
                raise ValueError("STOP_EXPANDED_BYTE_CAP")
    checkpoint()
    return {"gzip_crc_eof_verified": True, "expanded": file_record(expanded)}


def headers(slot):
    reader = load_pinned("c1_structure", STRUCTURE_PATH, STRUCTURE_HASH)
    path = paths(slot)[1]
    checkpoint()
    with path.open("rb") as stream, warnings.catch_warnings(record=True) as captured:
        result = reader.structure(stream, path.stat().st_size)
    # Warning text can contain header values; retain no such text in public output.
    result["parser_warning_categories"] = [w.category.__name__ for w in captured]
    checkpoint()
    return result


def artifacts(*, monitor=True):
    return {p.relative_to(HERE).as_posix(): sha(p, monitor=monitor) for p in HERE.rglob("*") if p.is_file() and
            (p.name.startswith("slot-") or p.suffix in (".FTZ", ".fits") or p.name == "worker-start.json")}


def ledger(plan, *, verify=True):
    rows = []
    stopped = False
    elapsed_previous = -1
    for slot in plan:
        n = slot["slot"]
        marker = HERE / f"slot-{n}-start.json"
        row = {"slot": n, "status": "NOT_ATTEMPTED"}
        if marker.exists():
            mark = read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or mark.get("slot") != slot or type(elapsed) not in (int, float)
                    or not math.isfinite(elapsed) or not elapsed_previous <= elapsed < SECONDS):
                raise ValueError("STOP_SLOT_ORDER")
            elapsed_previous = elapsed
            row["status"] = "INTERRUPTED"
            if (HERE / f"slot-{n}-result.json").exists():
                recorded = read(f"slot-{n}-result.json")
                if recorded["slot"] != slot or recorded["status"] not in ("OK", "FAILED"):
                    raise ValueError("STOP_SLOT_RECEIPT")
                if verify and recorded["status"] == "OK":
                    validate_http(slot, read(f"slot-{n}-http.json"))
                    raw, expanded = paths(slot)
                    report = read(f"headers/slot-{n}-headers.json")
                    if (recorded["raw"] != file_record(raw) or recorded["raw"]["bytes"] != slot["expected_bytes"]
                            or recorded["expanded"] != file_record(expanded)
                            or not 0 < recorded["expanded"]["bytes"] <= EXPANDED_FILE_CAP
                            or recorded["gzip_crc_eof_verified"] is not True
                            or recorded["headers_sha256"] != sha(HERE / f"headers/slot-{n}-headers.json")
                            or recorded["headers_bytes"] != (HERE / f"headers/slot-{n}-headers.json").stat().st_size
                            or report != headers(slot)):
                        raise ValueError("STOP_PRODUCT_REPLAY")
                row.update({k: v for k, v in recorded.items() if k != "slot"})
            stopped = row["status"] != "OK"
        else:
            if any(HERE.glob(f"slot-{n}-*.json")) or any(p.exists() for p in paths(slot)):
                raise ValueError("STOP_ORPHAN_ARTIFACT")
            stopped = True
        rows.append(row)
    if len(list(HERE.glob("slot-*-start.json"))) != sum(r["status"] != "NOT_ATTEMPTED" for r in rows):
        raise ValueError("STOP_EXTRA_SLOT")
    return rows


def resource_usage(*, exclude=()):
    usage = {"compressed_bytes": sum(p.stat().st_size for p in (HERE / "products").glob("*.FTZ")),
             "expanded_bytes": sum(p.stat().st_size for p in (HERE / "products").glob("*.fits")),
             "json_bytes": sum(p.stat().st_size for p in HERE.rglob("*.json") if p.name not in exclude)}
    if (usage["compressed_bytes"] > sum(EXPECTED) or usage["expanded_bytes"] > EXPANDED_TOTAL_CAP
            or usage["json_bytes"] > JSON_CAP
            or any(p.stat().st_size > HEADER_CAP for p in (HERE / "headers").glob("*.json"))
            or any(p.stat().st_size > EXPANDED_FILE_CAP for p in (HERE / "products").glob("*.fits"))):
        raise ValueError("STOP_RESOURCE_TOTAL")
    return usage


def worker():
    global DEADLINE
    began = time.monotonic()
    DEADLINE = began + SECONDS
    result = {"status": "STOP"}
    plan = read("run-start.json")["plan"]
    old = load_pinned("c1_failures", C0D_PATH, C0D_HASH)
    try:
        verify_binding()
        save("worker-start.json", {"binding_sha256": sha(HERE / "run-start.json")})
        for slot in plan:
            checkpoint()
            save(f"slot-{slot['slot']}-start.json", {"slot": slot, "elapsed_seconds": time.monotonic() - began})
            try:
                download(slot)
                decompressed = expand(slot)
                save(f"headers/slot-{slot['slot']}-headers.json", headers(slot), header=True)
                record = {"slot": slot, "status": "OK", "raw": file_record(paths(slot)[0]), **decompressed,
                          "headers_sha256": sha(HERE / f"headers/slot-{slot['slot']}-headers.json"),
                          "headers_bytes": (HERE / f"headers/slot-{slot['slot']}-headers.json").stat().st_size}
            except Exception as error:
                LOGGER.exception("Known-control slot stopped; details in safe receipt", exc_info=(
                    RuntimeError, RuntimeError("Original exception text withheld for header privacy"), None))
                record = {"slot": slot, "status": "FAILED", **old.failure(error)}
                save(f"slot-{slot['slot']}-result.json", record, terminal=True)
                raise
            save(f"slot-{slot['slot']}-result.json", record)
        checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Known-control worker stopped; details in safe receipt", exc_info=(
            RuntimeError, RuntimeError("Original exception text withheld for header privacy"), None))
        result.update(old.failure(error))
    finally:
        DEADLINE = None
        result.update(ledger=ledger(plan, verify=False), artifacts=artifacts(monitor=False),
                      resource_usage=resource_usage(exclude=("worker-result.json", "outcome.json")))
        save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    plan = read("run-start.json")["plan"]
    rows = ledger(plan)
    worker_path = HERE / "worker-result.json"
    result = read(worker_path.name) if worker_path.exists() else None
    if result and (result["ledger"] != rows or result["artifacts"] != artifacts()
                   or result["resource_usage"] != resource_usage(exclude=("worker-result.json", "outcome.json"))
                   or type(result["peak_memory_bytes"]) is not int or result["peak_memory_bytes"] <= 0
                   or (result["status"] == PASS and result["peak_memory_bytes"] > MEMORY_CAP)):
        raise ValueError("STOP_WORKER_CLOSURE_OR_MEMORY")
    success = code == 0 and result is not None and result["status"] == PASS
    if success and (any(r["status"] != "OK" for r in rows)
                    or read("worker-start.json") != {"binding_sha256": sha(HERE / "run-start.json")}):
        raise ValueError("STOP_FALSE_SUCCESS")
    return {"status": PASS if success else "STOP", "ledger": rows,
            "peak_memory_bytes": result["peak_memory_bytes"] if result else None,
            "worker_error_code": result.get("error_code") if result else None,
            "resource_usage": resource_usage(exclude=("outcome.json",)), "scientific_counts_computed": False}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None}
    old = load_pinned("c1_parent_failures", C0D_PATH, C0D_HASH)
    try:
        checkpoint()
        if shutil.disk_usage(HERE).free < 3 * 1024**3:
            raise ValueError("STOP_FREE_SPACE")
        save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = load_pinned("c1_deadline", HELPER, HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
    except Exception as error:
        LOGGER.exception("Known-control parent stopped; details in safe receipt", exc_info=(
            RuntimeError, RuntimeError("Original exception text withheld for header privacy"), None))
        result.update(old.failure(error))
        result.setdefault("ledger", [{"slot": i, "status": "UNVERIFIED_ATTEMPT" if
                           (HERE / f"slot-{i}-start.json").exists() else "NOT_ATTEMPTED"} for i in range(1, 5)])
    finally:
        result["artifacts"] = {p.relative_to(HERE).as_posix(): sha(p, monitor=False)
                               for p in HERE.rglob("*") if p.is_file()}
        save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(json.dumps(result))
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = read("outcome.json")
    for name, digest in outcome["artifacts"].items():
        if sha(HERE / name) != digest:
            raise ValueError("STOP_ARTIFACT_HASH")
    check = assess(outcome["worker_returncode"])
    parent_peak = outcome.get("parent_peak_memory_bytes")
    if type(parent_peak) is not int or parent_peak <= 0:
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    if parent_peak > MEMORY_CAP:
        if outcome.get("error_code") != "STOP_PEAK_MEMORY":
            raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
        check["status"] = "STOP"
    elif outcome.get("error_code") == "STOP_PEAK_MEMORY":
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    for key, value in check.items():
        if outcome.get(key) != value:
            raise ValueError("STOP_OUTCOME_REPLAY")
    resource_usage()
    print("PASS_OFFLINE_REPLAY", check["status"])


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        raise SystemExit(run())
    if sys.argv[1:] == ["_worker"]:
        raise SystemExit(worker())
    if sys.argv[1:] == ["replay"]:
        replay()
    else:
        raise SystemExit("Expected run, internal _worker, or replay")
