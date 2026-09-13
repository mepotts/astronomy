"""One documented XSA AIO HEAD; no body reads, raw disposition or downloads."""

import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import logging
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C3c-2026-09-12.md"
C1_PATH = HERE.parent / "XMM-C1-2026-09-12-data/acquire.py"
C1_HASH = "13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5"
URL = ("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&name=ATTTSR"
       "&expflag=X&expno=000&datasubsetno=0&sourceno=000&extension=FTZ")
EXPECTED = "P0884250101OBX000ATTTSR0000.FTZ"
SECONDS, CAP, PASS = 30, 2097152, "XSA_ATT_ENTITY_METADATA_RETAINED"
LOGGER = logging.getLogger(__name__)


def load_c1():
    raw = C1_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != C1_HASH:
        raise ValueError("STOP_C1_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(C1_PATH), "exec")

    spec = importlib.util.spec_from_file_location("c3c_helpers", C1_PATH, loader=VerifiedLoader("c3c_helpers", str(C1_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_c1()
O = C.load_pinned("c3c_http_rules", C.C0D_PATH, C.C0D_HASH)
C.HERE, C.SECONDS, C.CHUNK = HERE, SECONDS, 65536
C.MEMORY_CAP, C.JSON_CAP, C.RESERVE = 500000000, 131072, 32768
SLOT = {"slot": 1, "method": "HEAD", "url": URL}


def binding(protocol):
    import requests

    paths = (C1_PATH, C.C0D_PATH, C.HELPER)
    hashes = {str(p): C.sha(p) for p in paths}
    if list(hashes.values()) != [C1_HASH, C.C0D_HASH, C.HELPER_HASH]:
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"slot": SLOT, "source_sha256": C.sha(SOURCE), "tests_sha256": C.sha(HERE / "test_acquire.py"),
            "protocol_sha256": C.sha(protocol), "dependencies": hashes,
            "configuration": {"output_directory": str(C.HERE), "seconds": C.SECONDS, "hash_chunk": C.CHUNK,
                              "memory": C.MEMORY_CAP, "json": C.JSON_CAP, "reserve": C.RESERVE,
                              "entity_cap": CAP, "deadline_policy": "monotonic worker start plus30; helper30"},
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()), "requests": requests.__version__}}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def disposition(values):
    if not values:
        raise ValueError("STOP_DISPOSITION_MISSING")
    if len(values) > 100 or sum(len(v.encode("utf-8")) for v in values) > 2048:
        raise ValueError("STOP_DISPOSITION_CAP")
    if len(set(values)) != 1:
        raise ValueError("STOP_DISPOSITION_AMBIGUOUS")
    value = values[0]
    if any(ord(c) < 32 or ord(c) > 126 for c in value):
        raise ValueError("STOP_DISPOSITION_CHARACTERS")
    match = re.fullmatch(r'(attachment|inline)\s*;\s*filename\s*=\s*(?:"([A-Za-z0-9._-]+)"|([A-Za-z0-9._-]+))\s*', value, re.IGNORECASE)
    if not match:
        raise ValueError("STOP_DISPOSITION_SYNTAX")
    filename = match[2] or match[3]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", filename) or ".." in filename or filename.endswith("."):
        raise ValueError("STOP_DISPOSITION_BASENAME")
    return {"status": "PARSED", "type": match[1].lower(), "filename": filename, "value_count": len(values)}


def classify(parsed, media_type):
    if set(parsed) != {"status", "type", "filename", "value_count"} or parsed["status"] != "PARSED":
        raise ValueError("STOP_DISPOSITION_RECEIPT")
    if type(parsed["value_count"]) is not int or not 1 <= parsed["value_count"] <= 100:
        raise ValueError("STOP_DISPOSITION_RECEIPT")
    # Independently validate safe derived fields. Raw disposition is intentionally
    # absent; this replays classification, not the discarded raw-field parser.
    reconstructed = disposition([f'{parsed["type"]}; filename="{parsed["filename"]}"'])
    if reconstructed != {**parsed, "value_count": 1}:
        raise ValueError("STOP_DISPOSITION_RECEIPT")
    name = parsed["filename"]
    allowed = {"application/octet-stream", "application/x-download"}
    if name == EXPECTED:
        label = "EXPECTED_RAW_FILENAME_ADVERTISED"
        allowed |= {"application/gzip", "application/x-gzip", "application/fits", "application/x-fits", "image/fits"}
    elif name.lower().endswith((".tar.gz", ".tgz")):
        label = "PACKAGE_ADVERTISED_MEMBERS_UNKNOWN"
        allowed |= {"application/gzip", "application/x-gzip", "application/x-tar"}
    elif name.lower().endswith(".tar"):
        label = "PACKAGE_ADVERTISED_MEMBERS_UNKNOWN"
        allowed |= {"application/x-tar", "application/tar", "application/x-gtar"}
    elif name.lower().endswith(".zip"):
        label = "PACKAGE_ADVERTISED_MEMBERS_UNKNOWN"
        allowed |= {"application/zip", "application/x-zip-compressed"}
    else:
        raise ValueError("STOP_UNRECOGNIZED_PACKAGING")
    if media_type not in allowed:
        raise ValueError("STOP_MEDIA_PACKAGING_MISMATCH")
    return label


def measurement(http):
    if set(http) != {"method", "url", "status", "headers", "disposition"}:
        raise ValueError("STOP_HTTP_SCHEMA")
    size = O.check_http(SLOT, {k: v for k, v in http.items() if k != "disposition"})
    if sum(len(v.encode("utf-8")) for values in http["headers"].values() for v in values) > 65536:
        raise ValueError("STOP_SAFE_HEADER_CAP")
    if not 0 < size <= CAP:
        raise ValueError("STOP_ENTITY_BYTE_CAP")
    media = O.single(http["headers"], "Content-Type").split(";", 1)[0].strip().lower()
    if http["disposition"].get("status") == "REJECTED":
        code = http["disposition"].get("error_code", "")
        raise ValueError(code if re.fullmatch(r"STOP_DISPOSITION_[A-Z_]+", code) else "STOP_DISPOSITION_RECEIPT")
    label = classify(http["disposition"], media)
    return {"advertised_entity_bytes": size, "packaging": label, "filename": http["disposition"]["filename"],
            "body_bytes_read": 0, "package_member_identity_verified": False, "product_get_performed": False}


def collect():
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError("STOP_HEADER_PARSER")
    with requests.Session() as session:
        session.trust_env, session.auth = False, None
        session.cookies.clear()
        C.checkpoint()
        with session.request("HEAD", URL, timeout=(5, 15), stream=True, allow_redirects=False,
                             headers={"Accept-Encoding": "identity"}) as response:
            headers = {k: response.raw.headers.getlist(k) for k in O.SAFE_HEADERS if response.raw.headers.getlist(k)}
            if sum(len(v.encode("utf-8")) for values in headers.values() for v in values) > 65536:
                raise ValueError("STOP_SAFE_HEADER_CAP")
            try:
                parsed = disposition(response.raw.headers.getlist("Content-Disposition"))
            except ValueError as error:
                parsed = {"status": "REJECTED", "error_code": str(error)}
            http = {"method": response.request.method, "url": response.url, "status": response.status_code,
                    "headers": headers, "disposition": parsed}
            C.save("http.json", http)
            return measurement(http)


def artifacts(exclude=()):
    return {p.name: C.sha(p, monitor=False) for p in HERE.iterdir() if p.is_file() and p.name not in exclude
            and (p.suffix == ".json" or p.name == "protocol.snapshot.md")}


def json_usage(exclude=()):
    size = sum(p.stat().st_size for p in HERE.glob("*.json") if p.name not in exclude)
    if size > C.JSON_CAP:
        raise ValueError("STOP_JSON_BUDGET")
    return size


def ledger(verify=True):
    if not (HERE / "request-start.json").exists():
        if (HERE / "request-result.json").exists() or (HERE / "http.json").exists():
            raise ValueError("STOP_ORPHAN_RECEIPT")
        return [{"slot": 1, "status": "NOT_ATTEMPTED"}]
    marker = C.read("request-start.json")
    elapsed = marker.get("elapsed_seconds")
    if (set(marker) != {"slot", "elapsed_seconds"} or marker["slot"] != SLOT
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed < SECONDS):
        raise ValueError("STOP_REQUEST_MARKER")
    if not (HERE / "request-result.json").exists():
        return [{"slot": 1, "status": "INTERRUPTED"}]
    result = C.read("request-result.json")
    if result.get("slot") != SLOT or result.get("status") not in ("OK", "FAILED"):
        raise ValueError("STOP_REQUEST_RECEIPT")
    if result["status"] == "FAILED" and (set(result) != {"slot", "status", "error_type", "error_code"}
            or not isinstance(result["error_type"], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", result["error_type"])
            or (result["error_code"] is not None and (not isinstance(result["error_code"], str)
                or not re.fullmatch(r"STOP_[A-Z0-9_]+", result["error_code"])))):
        raise ValueError("STOP_FAILED_RECEIPT_SCHEMA")
    if result["status"] == "OK" and verify and result != {"slot": SLOT, "status": "OK", **measurement(C.read("http.json"))}:
        raise ValueError("STOP_METADATA_REPLAY")
    return [{"slot": 1, "status": result["status"]}]


def fallback():
    return [{"slot": 1, "status": "UNVERIFIED_ATTEMPT" if any((HERE / n).exists() for n in
             ("request-start.json", "request-result.json", "http.json")) else "NOT_ATTEMPTED"}]


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result = {"status": "STOP"}
    try:
        verify_binding()
        C.save("worker-start.json", {"binding_sha256": C.sha(HERE / "run-start.json")})
        C.checkpoint()
        C.save("request-start.json", {"slot": SLOT, "elapsed_seconds": time.monotonic() - began})
        try:
            value = collect()
            C.save("request-result.json", {"slot": SLOT, "status": "OK", **value})
        except Exception as error:
            C.save("request-result.json", {"slot": SLOT, "status": "FAILED", **O.failure(error)}, terminal=True)
            raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("AIO metadata worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            result["ledger"] = ledger(verify=False)
        except Exception:
            LOGGER.exception("AIO metadata ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=fallback(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(artifacts=artifacts(), json_bytes_before_worker=json_usage())
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    rows = ledger()
    w = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    if w and (w["ledger"] != rows or w["artifacts"] != artifacts(("worker-result.json", "outcome.json"))
              or w["json_bytes_before_worker"] != json_usage(("worker-result.json", "outcome.json"))
              or type(w["peak_memory_bytes"]) is not int or w["peak_memory_bytes"] <= 0):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and w is not None and w["status"] == PASS
    if success and (rows != [{"slot": 1, "status": "OK"}] or w["peak_memory_bytes"] > C.MEMORY_CAP
                    or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}):
        raise ValueError("STOP_FALSE_SUCCESS")
    return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
            "worker_error_code": w.get("error_code") if w else None,
            "worker_peak_memory_bytes": w["peak_memory_bytes"] if w else None,
            "json_bytes_before_outcome": json_usage(("outcome.json",)), "body_bytes_read": 0}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c3c_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("AIO metadata parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error), ledger=fallback())
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
    json_usage()
    if outcome["assessment_completed"] is False:
        if outcome["status"] != "STOP" or outcome["ledger"] != fallback():
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; metadata remains unverified")
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
        LOGGER.exception("AIO metadata command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
