"""Four fixed HEADs gate four bounded GETs; retain headers, never decode arrays."""

import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import json
import logging
import math
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C3-2026-09-12.md"
C1_PATH = HERE.parent / "XMM-C1-2026-09-12-data/acquire.py"
C1_HASH = "13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5"
C1_TEST_HASH = "d751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c"
NAMES = ("P0884250101PNS003EXPMAP8000.FTZ", "P0884250101M1S001EXPMAP8000.FTZ",
         "P0884250101M2S002EXPMAP8000.FTZ", "P0884250101OBX000ATTTSR0000.FTZ")
RAW_CAP, FREE_BYTES, SECONDS = 2097152, 268435456, 120
PASS = "GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY"
LOGGER = logging.getLogger(__name__)


def load_c1():
    raw = C1_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != C1_HASH:
        raise ValueError("STOP_C1_SOURCE_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(C1_PATH), "exec")

    spec = importlib.util.spec_from_file_location("c3_c1", C1_PATH, loader=VerifiedLoader("c3_c1", str(C1_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_c1()
O = C.load_pinned("c3_http_rules", C.C0D_PATH, C.C0D_HASH)


def configure():
    """Only these reviewed functions' module globals are adapted, never C1 files."""
    C.HERE = HERE
    C.EXPECTED = [RAW_CAP] * 4
    C.EXPANDED_FILE_CAP, C.EXPANDED_TOTAL_CAP = 33554432, 134217728
    C.MEMORY_CAP, C.SECONDS, C.CHUNK = 500000000, SECONDS, 1048576
    C.HEADER_CAP, C.JSON_CAP, C.RESERVE = 2097152, 10485760, 262144
    C.DEADLINE = None


configure()


def configuration():
    return {"output_directory": str(C.HERE), "compressed_caps": C.EXPECTED,
            "expanded_file": C.EXPANDED_FILE_CAP, "expanded_total": C.EXPANDED_TOTAL_CAP,
            "memory": C.MEMORY_CAP, "seconds": C.SECONDS, "chunk": C.CHUNK,
            "header_json": C.HEADER_CAP, "json": C.JSON_CAP, "terminal_reserve": C.RESERVE,
            "minimum_free_bytes_each_request": FREE_BYTES,
            "deadline_policy": "worker monotonic start plus seconds; hard helper deadline same seconds"}


def plan():
    if C.sha(O.INVENTORY) != O.INVENTORY_HASH or C.sha(O.INDEX) != O.INDEX_HASH:
        raise ValueError("STOP_INVENTORY_HASH")
    entries = json.loads(O.INVENTORY.read_bytes())["entries"]
    for name in NAMES:
        found = [r for r in entries if r["name"] == name]
        if len(found) != 1 or found[0]["url"] != O.BASE + name:
            raise ValueError("STOP_INVENTORY_SELECTION")
    return [{"slot": n, "method": "HEAD" if n <= 4 else "GET", "url": O.BASE + name, "filename": name}
            for n, name in enumerate(NAMES * 2, 1)]


def binding(protocol):
    import astropy
    import requests

    dependencies = {str(path): C.sha(path) for path in (
        C1_PATH, C1_PATH.with_name("test_acquire.py"), C.C0D_PATH, C.STRUCTURE_PATH,
        C.STRUCTURE_TEST, C.STRUCTURE_REVIEW, C.HELPER)}
    expected = (C1_HASH, C1_TEST_HASH, C.C0D_HASH, C.STRUCTURE_HASH,
                C.STRUCTURE_TEST_HASH, C.STRUCTURE_REVIEW_HASH, C.HELPER_HASH)
    if list(dependencies.values()) != list(expected):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"slots": plan(), "configuration": configuration(), "source_sha256": C.sha(SOURCE),
            "tests_sha256": C.sha(HERE / "test_acquire.py"), "protocol_sha256": C.sha(protocol),
            "dependencies": dependencies, "inventory_sha256": O.INVENTORY_HASH, "index_sha256": O.INDEX_HASH,
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "requests": requests.__version__, "astropy": astropy.__version__}}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def validate_head(slot, http):
    length = O.check_http(slot, http)
    if sum(len(value.encode("utf-8")) for values in http["headers"].values() for value in values) > 65536:
        raise ValueError("STOP_SAFE_HEADER_CAP")
    if not 0 < length <= RAW_CAP:
        raise ValueError("STOP_HEAD_BYTE_CAP")
    return {"slot": slot, "status": "OK", "advertised_compressed_bytes": length, "body_bytes_read": 0}


def collect_head(slot):
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError("STOP_HEADER_PARSER")
    with requests.Session() as session:
        session.trust_env = False
        session.auth = None
        session.cookies.clear()
        C.checkpoint()
        with session.request("HEAD", slot["url"], timeout=(5, 15), stream=True, allow_redirects=False,
                             headers={"Accept-Encoding": "identity"}) as response:
            headers = {k: response.raw.headers.getlist(k) for k in O.SAFE_HEADERS if response.raw.headers.getlist(k)}
            if sum(len(v.encode("utf-8")) for values in headers.values() for v in values) > 65536:
                raise ValueError("STOP_SAFE_HEADER_CAP")
            http = {"method": response.request.method, "url": response.url, "status": response.status_code, "headers": headers}
            C.save(f"slot-{slot['slot']}-http.json", http)
            return validate_head(slot, http)


def get_plan(slots):
    result = []
    for head, get in zip(slots[:4], slots[4:], strict=True):
        http = C.read(f"slot-{head['slot']}-http.json")
        expected = validate_head(head, http)
        if C.read(f"slot-{head['slot']}-result.json") != expected:
            raise ValueError("STOP_HEAD_RECEIPT")
        result.append({**get, "expected_bytes": expected["advertised_compressed_bytes"], "head_headers": http["headers"]})
    if len(result) != 4 or sum(r["expected_bytes"] for r in result) > 4 * RAW_CAP:
        raise ValueError("STOP_HEAD_TOTAL_CAP")
    return result


def product_record(slot, verify=False):
    http = C.read(f"slot-{slot['slot']}-http.json")
    # Reuse strict HEAD schema/encoding/duplicate-length rules for common fields,
    # then independently verify the actual GET identity and its HEAD validators.
    validate_head({**slot, "method": "HEAD"}, {**http, "method": "HEAD"})
    C.validate_http(slot, http)
    raw, expanded = C.paths(slot)
    if (raw.stat().st_size != slot["expected_bytes"] or not 0 < expanded.stat().st_size <= C.EXPANDED_FILE_CAP):
        raise ValueError("STOP_PRODUCT_SIZE")
    header_path = HERE / f"headers/slot-{slot['slot']}-headers.json"
    report = json.loads(header_path.read_bytes())
    if verify and report != C.headers(slot):
        raise ValueError("STOP_HEADER_REPLAY")
    return {"slot": slot, "status": "OK", "raw": C.file_record(raw), "expanded": C.file_record(expanded),
            "gzip_crc_eof_verified": True, "headers_sha256": C.sha(header_path), "headers_bytes": header_path.stat().st_size,
            "hdu_count": report["hdu_count"]}


def collect_get(slot):
    C.download(slot)
    C.expand(slot)
    C.save(f"headers/slot-{slot['slot']}-headers.json", C.headers(slot), header=True)
    return product_record(slot)


def ledger(slots, verify=True):
    rows, stopped, previous, gets = [], False, -1, None
    for original in slots:
        n = original["slot"]
        row = {"slot": n, "status": "NOT_ATTEMPTED"}
        marker = HERE / f"slot-{n}-start.json"
        receipt = HERE / f"slot-{n}-result.json"
        if marker.exists():
            mark = C.read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or mark.get("slot") != original or set(mark) != {"slot", "elapsed_seconds"}
                    or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not previous <= elapsed < SECONDS):
                raise ValueError("STOP_REQUEST_ORDER")
            previous = elapsed
            if n == 5:
                gets = get_plan(slots)  # Independently proves all four HEADs before any GET.
            slot = original if n <= 4 else gets[n - 5]
            row["status"] = "INTERRUPTED"
            if receipt.exists():
                record = C.read(receipt.name)
                if record.get("slot") != slot or record.get("status") not in ("OK", "FAILED"):
                    raise ValueError("STOP_RECEIPT_IDENTITY")
                if verify and record["status"] == "OK":
                    expected = (validate_head(slot, C.read(f"slot-{n}-http.json")) if n <= 4
                                else product_record(slot, verify=True))
                    if record != expected:
                        raise ValueError("STOP_RECEIPT_REPLAY")
                if record["status"] == "FAILED" and set(record) != {"slot", "status", "error_type", "error_code"}:
                    raise ValueError("STOP_FAILED_RECEIPT")
                row["status"] = record["status"]
        elif receipt.exists() or (HERE / f"slot-{n}-http.json").exists():
            raise ValueError("STOP_ORPHAN_RECEIPT")
        stopped = stopped or row["status"] != "OK"
        rows.append(row)
    if len(list(HERE.glob("slot-*-start.json"))) != sum(r["status"] != "NOT_ATTEMPTED" for r in rows):
        raise ValueError("STOP_EXTRA_REQUEST")
    return rows


def fallback_ledger():
    return [{"slot": n, "status": "UNVERIFIED_ATTEMPT" if any(HERE.glob(f"slot-{n}-*.json"))
             else "NOT_ATTEMPTED"} for n in range(1, 9)]


def verify_product_set(gets):
    expected_products = {p for slot in gets for p in C.paths(slot)}
    expected_headers = {HERE / f"headers/slot-{slot['slot']}-headers.json" for slot in gets}
    actual_products = {p for p in (HERE / "products").rglob("*") if p.is_file()}
    actual_headers = {p for p in (HERE / "headers").rglob("*") if p.is_file()}
    usage = C.resource_usage()
    if (actual_products != expected_products or actual_headers != expected_headers
            or usage["compressed_bytes"] != sum(slot["expected_bytes"] for slot in gets)
            or usage["expanded_bytes"] != sum(C.paths(slot)[1].stat().st_size for slot in gets)):
        raise ValueError("STOP_PRODUCT_SET")


def artifacts(exclude=()):
    return {p.relative_to(HERE).as_posix(): C.sha(p, monitor=False) for p in HERE.rglob("*") if p.is_file()
            and p.name not in exclude and (p.suffix in (".json", ".FTZ", ".fits") or p.name == "protocol.snapshot.md")}


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result = {"status": "STOP"}
    slots = C.read("run-start.json")["slots"]
    try:
        verify_binding()
        C.save("worker-start.json", {"binding_sha256": C.sha(HERE / "run-start.json")})
        gets = None
        for original in slots:
            C.checkpoint()
            if shutil.disk_usage(HERE).free < FREE_BYTES:
                raise ValueError("STOP_FREE_SPACE")
            n = original["slot"]
            if n == 5:
                gets = get_plan(slots)
            slot = original if n <= 4 else gets[n - 5]
            C.save(f"slot-{n}-start.json", {"slot": original, "elapsed_seconds": time.monotonic() - began})
            try:
                record = collect_head(slot) if n <= 4 else collect_get(slot)
                C.save(f"slot-{n}-result.json", record)
            except Exception as error:
                C.save(f"slot-{n}-result.json", {"slot": slot, "status": "FAILED", **O.failure(error)}, terminal=True)
                raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Coverage worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            result["ledger"] = ledger(slots, verify=False)
        except Exception:
            LOGGER.exception("Coverage ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=fallback_ledger(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(artifacts=artifacts(), resource_usage=C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    rows = ledger(C.read("run-start.json")["slots"])
    worker = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    if worker and (worker["ledger"] != rows or worker["artifacts"] != artifacts(("worker-result.json", "outcome.json"))
                   or worker["resource_usage"] != C.resource_usage(exclude=("worker-result.json", "outcome.json"))
                   or type(worker["peak_memory_bytes"]) is not int or worker["peak_memory_bytes"] <= 0):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and worker is not None and worker["status"] == PASS
    if success and (any(r["status"] != "OK" for r in rows) or worker["peak_memory_bytes"] > C.MEMORY_CAP
                    or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}):
        raise ValueError("STOP_FALSE_SUCCESS")
    if success:
        verify_product_set(get_plan(C.read("run-start.json")["slots"]))
    return {"status": PASS if success else "STOP", "ledger": rows, "worker_returncode": code,
            "worker_error_code": worker.get("error_code") if worker else None,
            "worker_peak_memory_bytes": worker["peak_memory_bytes"] if worker else None,
            "resource_usage": C.resource_usage(exclude=("outcome.json",)), "arrays_interpreted": False}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        C.checkpoint()
        if shutil.disk_usage(HERE).free < FREE_BYTES:
            raise ValueError("STOP_FREE_SPACE")
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c3_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("Coverage parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error), ledger=fallback_ledger())
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
        if outcome["status"] != "STOP" or outcome["ledger"] != fallback_ledger():
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; products remain unverified")
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
        LOGGER.exception("Coverage command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
