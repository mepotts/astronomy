"""One capped exact-name ATT GET, gzip or FITS signature, then headers only."""

import contextlib
import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import io
import logging
import math
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C3d-2026-09-12.md"
PRIOR_PATH = HERE.parent / "XMM-C3c-2026-09-12-data/acquire.py"
PRIOR_HASH = "542fce5755d9ff668d4ccd6e199b23780504368603352243d7e6fb7cfa727f90"
PRIOR_TEST_HASH = "d3fd4d9775c40a094d761dad0f59e4b9e9d556fced7c6c3f7449324b5f4885ed"
PRIOR_OUTCOME = "e1d74b048dd68dce51e52bf964d841ac195ca581011fae881f447cdc129c45e3"
C1_TEST_HASH = "d751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c"
CAP, SECONDS, FREE_BYTES = 2097152, 60, 67108864
PASS = "ATT_PRODUCT_RETAINED_HEADERS_ONLY"
LOGGER = logging.getLogger(__name__)


def load_prior():
    raw = PRIOR_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PRIOR_HASH:
        raise ValueError("STOP_PRIOR_SOURCE_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(PRIOR_PATH), "exec")

    spec = importlib.util.spec_from_file_location("c3d_prior", PRIOR_PATH, loader=VerifiedLoader("c3d_prior", str(PRIOR_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load_prior()
C = P.load_c1()  # Independent current helper instance; P.C keeps original paths.
C.HERE, C.SECONDS, C.CHUNK = HERE, SECONDS, 1048576
C.EXPECTED = [CAP]
C.EXPANDED_FILE_CAP = C.EXPANDED_TOTAL_CAP = 33554432
C.MEMORY_CAP, C.JSON_CAP, C.HEADER_CAP, C.RESERVE = 500000000, 1048576, 2097152, 65536
SLOT = {"slot": 1, "method": "GET", "url": P.URL, "filename": P.EXPECTED}
RAW, EXPANDED = C.paths(SLOT)
HEADER_NAME = "headers/slot-1-headers.json"
MEDIA = {"image/fits", "application/fits", "application/x-fits", "application/octet-stream", "application/gzip", "application/x-gzip"}


def prior_evidence():
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    with contextlib.redirect_stdout(io.StringIO()):
        P.replay()
    outcome, http = P.C.read("outcome.json"), P.C.read("http.json")
    if (outcome["status"] != "STOP" or outcome["worker_returncode"] != 1
            or outcome["ledger"] != [{"slot": 1, "status": "FAILED"}] or outcome["worker_error_code"] != "STOP_SIZE_METADATA"
            or outcome["body_bytes_read"] != 0 or http["status"] != 200 or http["url"] != P.URL
            or "Content-Length" in http["headers"] or http["disposition"]["filename"] != P.EXPECTED):
        raise ValueError("STOP_PRIOR_STATE")
    return {"http": http, "http_sha256": C.sha(PRIOR_PATH.with_name("http.json")), "outcome_sha256": PRIOR_OUTCOME}


def binding(protocol):
    import astropy
    import requests

    paths = (PRIOR_PATH, PRIOR_PATH.with_name("test_acquire.py"), P.C1_PATH, P.C1_PATH.with_name("test_acquire.py"),
             C.C0D_PATH, C.STRUCTURE_PATH, C.STRUCTURE_TEST, C.STRUCTURE_REVIEW, C.HELPER)
    expected = [PRIOR_HASH, PRIOR_TEST_HASH, P.C1_HASH, C1_TEST_HASH, C.C0D_HASH,
                C.STRUCTURE_HASH, C.STRUCTURE_TEST_HASH, C.STRUCTURE_REVIEW_HASH, C.HELPER_HASH]
    hashes = {str(path): C.sha(path) for path in paths}
    if list(hashes.values()) != expected:
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"slot": SLOT, "prior": prior_evidence(), "source_sha256": C.sha(SOURCE),
            "tests_sha256": C.sha(HERE / "test_acquire.py"), "protocol_sha256": C.sha(protocol), "dependencies": hashes,
            "configuration": {"output_directory": str(C.HERE), "seconds": C.SECONDS, "chunk": C.CHUNK,
                              "raw_caps": C.EXPECTED, "expanded_file": C.EXPANDED_FILE_CAP, "expanded_total": C.EXPANDED_TOTAL_CAP,
                              "memory": C.MEMORY_CAP, "json": C.JSON_CAP, "header": C.HEADER_CAP, "reserve": C.RESERVE,
                              "free_bytes": FREE_BYTES, "deadline_policy": "monotonic worker start plus60; helper60"},
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "requests": requests.__version__, "astropy": astropy.__version__}}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def validate_http(http):
    if (set(http) != {"method", "url", "status", "headers", "disposition"} or http["method"] != "GET"
            or http["url"] != P.URL or http["status"] != 200):
        raise ValueError("STOP_HTTP_IDENTITY_OR_STATUS")
    headers = http["headers"]
    if (not set(headers) <= set(P.O.SAFE_HEADERS) or any(not isinstance(v, list) or not v
            or any(not isinstance(x, str) for x in v) for v in headers.values())):
        raise ValueError("STOP_HEADER_SCHEMA")
    if sum(len(x.encode("utf-8")) for values in headers.values() for x in values) > 65536:
        raise ValueError("STOP_SAFE_HEADER_CAP")
    if P.O.single(headers, "Content-Encoding", "identity").lower() not in ("identity", ""):
        raise ValueError("STOP_CONTENT_ENCODING")
    media = P.O.single(headers, "Content-Type").split(";", 1)[0].strip().lower()
    if media not in MEDIA or P.classify(http["disposition"], media) != "EXPECTED_RAW_FILENAME_ADVERTISED":
        raise ValueError("STOP_MEDIA_OR_FILENAME")
    size = P.O.length(headers.get("Content-Length", []), False)
    if size is not None and size > CAP:
        raise ValueError("STOP_ADVERTISED_SIZE_CAP")
    return size


def download():
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError("STOP_HEADER_PARSER")
    with requests.Session() as session:
        session.trust_env, session.auth = False, None
        session.cookies.clear()
        C.checkpoint()
        with session.request("GET", P.URL, timeout=(5, 15), stream=True, allow_redirects=False,
                             headers={"Accept-Encoding": "identity"}) as response:
            headers = {k: response.raw.headers.getlist(k) for k in P.O.SAFE_HEADERS if response.raw.headers.getlist(k)}
            if sum(len(x.encode("utf-8")) for values in headers.values() for x in values) > 65536:
                raise ValueError("STOP_SAFE_HEADER_CAP")
            try:
                parsed = P.disposition(response.raw.headers.getlist("Content-Disposition"))
            except ValueError as error:
                parsed = {"status": "REJECTED", "error_code": str(error)}
            http = {"method": response.request.method, "url": response.url, "status": response.status_code,
                    "headers": headers, "disposition": parsed}
            C.save("http.json", http)
            size = validate_http(http)
            cap, count = CAP if size is None else size, 0
            RAW.parent.mkdir(exist_ok=True)
            with RAW.open("xb") as target:
                while True:
                    C.checkpoint()
                    block = response.raw.read(min(C.CHUNK, cap - count + 1), decode_content=False)
                    if not block:
                        break
                    keep = block[:cap - count]
                    target.write(keep)
                    count += len(keep)
                    if len(block) > len(keep):
                        raise ValueError("STOP_RAW_BYTE_CAP")
            if count <= 0 or (size is not None and count != size):
                raise ValueError("STOP_ACTUAL_LENGTH")


def actual_format():
    with RAW.open("rb") as source:
        prefix = source.read(30)
    if prefix.startswith(b"\x1f\x8b\x08"):
        return "GZIP_WRAPPED_FITS"
    if prefix.startswith(b"SIMPLE  =                    T"):
        return "RAW_FITS"
    raise ValueError("STOP_RAW_SIGNATURE")


def expand():
    kind = actual_format()
    if kind == "GZIP_WRAPPED_FITS":
        C.expand(SLOT)
    else:
        existing = sum(p.stat().st_size for p in RAW.parent.glob("*.fits"))
        cap, count = min(C.EXPANDED_FILE_CAP, C.EXPANDED_TOTAL_CAP - existing), 0
        if cap <= 0:
            raise ValueError("STOP_EXPANDED_TOTAL_CAP")
        with RAW.open("rb") as source, EXPANDED.open("xb") as target:
            while True:
                C.checkpoint()
                block = source.read(min(C.CHUNK, cap - count + 1))
                if not block:
                    break
                keep = block[:cap - count]
                target.write(keep)
                count += len(keep)
                if len(block) > len(keep):
                    raise ValueError("STOP_EXPANDED_BYTE_CAP")
        if C.sha(RAW) != C.sha(EXPANDED):
            raise ValueError("STOP_RAW_FITS_COPY")
    return kind


def product_record(verify=False):
    size = validate_http(C.read("http.json"))
    raw, expanded = C.file_record(RAW), C.file_record(EXPANDED)
    if not 0 < raw["bytes"] <= CAP or (size is not None and raw["bytes"] != size) or not 0 < expanded["bytes"] <= C.EXPANDED_FILE_CAP:
        raise ValueError("STOP_PRODUCT_SIZE")
    kind = actual_format()
    if kind == "RAW_FITS" and raw != expanded:
        raise ValueError("STOP_RAW_FITS_COPY")
    header = C.read(HEADER_NAME)
    if verify and header != C.headers(SLOT):
        raise ValueError("STOP_HEADER_REPLAY")
    return {"slot": SLOT, "status": "OK", "raw": raw, "expanded": expanded, "actual_format": kind,
            "gzip_crc_eof_verified": True if kind == "GZIP_WRAPPED_FITS" else None,
            "raw_fits_copy_hash_equal": True if kind == "RAW_FITS" else None,
            "header_sha256": C.sha(HERE / HEADER_NAME), "header_bytes": (HERE / HEADER_NAME).stat().st_size,
            "hdu_count": header["hdu_count"], "arrays_interpreted": False}


def artifacts(exclude=()):
    return {p.relative_to(HERE).as_posix(): C.sha(p, monitor=False) for p in HERE.rglob("*") if p.is_file()
            and p.name not in exclude and (p.suffix in (".json", ".FTZ", ".fits") or p.name == "protocol.snapshot.md")}


def ledger(verify=True):
    if not (HERE / "request-start.json").exists():
        if any((HERE / n).exists() for n in ("request-result.json", "http.json")) or RAW.exists() or EXPANDED.exists():
            raise ValueError("STOP_ORPHAN_ARTIFACT")
        return [{"slot": 1, "status": "NOT_ATTEMPTED"}]
    marker = C.read("request-start.json")
    elapsed = marker.get("elapsed_seconds")
    if (set(marker) != {"slot", "elapsed_seconds"} or marker["slot"] != SLOT or type(elapsed) not in (int, float)
            or not math.isfinite(elapsed) or not 0 <= elapsed < SECONDS):
        raise ValueError("STOP_REQUEST_MARKER")
    if not (HERE / "request-result.json").exists():
        return [{"slot": 1, "status": "INTERRUPTED"}]
    r = C.read("request-result.json")
    if r.get("slot") != SLOT or r.get("status") not in ("OK", "FAILED"):
        raise ValueError("STOP_REQUEST_RECEIPT")
    if r["status"] == "FAILED" and (set(r) != {"slot", "status", "error_type", "error_code"}
            or not isinstance(r["error_type"], str) or not r["error_type"].isidentifier()
            or (r["error_code"] is not None and (not isinstance(r["error_code"], str)
                or re.fullmatch(r"STOP_[A-Z0-9_]+", r["error_code"]) is None))):
        raise ValueError("STOP_FAILED_RECEIPT")
    if r["status"] == "OK" and verify and r != product_record(verify=True):
        raise ValueError("STOP_PRODUCT_REPLAY")
    return [{"slot": 1, "status": r["status"]}]


def fallback():
    return [{"slot": 1, "status": "UNVERIFIED_ATTEMPT" if any((HERE / n).exists() for n in
             ("request-start.json", "request-result.json", "http.json")) or RAW.exists() else "NOT_ATTEMPTED"}]


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result = {"status": "STOP"}
    try:
        verify_binding()
        C.save("worker-start.json", {"binding_sha256": C.sha(HERE / "run-start.json")})
        C.checkpoint()
        if shutil.disk_usage(HERE).free < FREE_BYTES:
            raise ValueError("STOP_FREE_SPACE")
        C.save("request-start.json", {"slot": SLOT, "elapsed_seconds": time.monotonic() - began})
        try:
            download()
            expand()
            C.save(HEADER_NAME, C.headers(SLOT), header=True)
            C.save("request-result.json", product_record())
        except Exception as error:
            C.save("request-result.json", {"slot": SLOT, "status": "FAILED", **P.O.failure(error)}, terminal=True)
            raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("ATT worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(P.O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            result["ledger"] = ledger(verify=False)
        except Exception:
            LOGGER.exception("ATT ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=fallback(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(artifacts=artifacts(), resource_usage=C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    rows = ledger()
    w = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    if w and (w["ledger"] != rows or w["artifacts"] != artifacts(("worker-result.json", "outcome.json"))
              or w["resource_usage"] != C.resource_usage(exclude=("worker-result.json", "outcome.json"))
              or type(w["peak_memory_bytes"]) is not int or w["peak_memory_bytes"] <= 0):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and w is not None and w["status"] == PASS
    if success:
        products = {p for p in (HERE / "products").rglob("*") if p.is_file()}
        headers = {p for p in (HERE / "headers").rglob("*") if p.is_file()}
        if (rows != [{"slot": 1, "status": "OK"}] or w["peak_memory_bytes"] > C.MEMORY_CAP
                or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}
                or products != {RAW, EXPANDED} or headers != {HERE / HEADER_NAME}):
            raise ValueError("STOP_FALSE_SUCCESS_OR_PRODUCT_SET")
    return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
            "worker_error_code": w.get("error_code") if w else None, "worker_peak_memory_bytes": w["peak_memory_bytes"] if w else None,
            "resource_usage": C.resource_usage(exclude=("outcome.json",)), "arrays_interpreted": False,
            "prior_c3c_status": "STOP_SIZE_METADATA_PRESERVED"}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c3d_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("ATT parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(P.O.failure(error), ledger=fallback())
    finally:
        result.update(artifacts=artifacts(("outcome.json",)), source_sha256=C.sha(SOURCE, monitor=False))
        C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(result["status"])
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = C.read("outcome.json")
    if outcome["artifacts"] != artifacts(("outcome.json",)) or outcome["source_sha256"] != C.sha(SOURCE):
        raise ValueError("STOP_OUTCOME_ARTIFACTS")
    peak = outcome.get("parent_peak_memory_bytes")
    if type(peak) is not int or peak <= 0 or (peak > C.MEMORY_CAP and
            (outcome["status"] != "STOP" or outcome.get("error_code") != "STOP_PEAK_MEMORY")):
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    C.resource_usage()
    if outcome["assessment_completed"] is False:
        if outcome["status"] != "STOP" or outcome["ledger"] != fallback():
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; product remains unverified")
        return
    expected = assess(outcome["worker_returncode"])
    if peak > C.MEMORY_CAP:
        expected["status"] = "STOP"
    if any(outcome.get(k) != v for k, v in expected.items()):
        raise ValueError("STOP_OUTCOME_REPLAY")
    print("PASS_OFFLINE_REPLAY", expected["status"])


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["run"]:
            raise SystemExit(run())
        if sys.argv[1:] == ["_worker"]:
            raise SystemExit(worker())
        if sys.argv[1:] == ["replay"]:
            replay()
        else:
            raise ValueError("STOP_COMMAND")
    except Exception as error:
        LOGGER.exception("ATT command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(P.O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
