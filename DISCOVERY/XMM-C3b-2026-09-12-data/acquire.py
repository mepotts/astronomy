"""One new ATT HEAD, then three conditional products; prior C3 STOP stays intact."""

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import math
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C3b-2026-09-12.md"
PRIOR_PATH = HERE.parent / "XMM-C3-2026-09-12-data/acquire.py"
PRIOR_HASH = "7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60"
PRIOR_TEST_HASH = "d322831429e4c613f2d759fe75818c68b9fba1c24abaf08108a37584b646ab1c"
PRIOR_OUTCOME = "62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e"
PASS = "PN_MOS1_GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY"
SECONDS, FREE_BYTES = 120, 268435456
PRIOR_SIZES = [503855, 275217]
LOGGER = logging.getLogger(__name__)


def load_prior(name):
    raw = PRIOR_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PRIOR_HASH:
        raise ValueError("STOP_PRIOR_SOURCE_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(PRIOR_PATH), "exec")

    spec = importlib.util.spec_from_file_location(name, PRIOR_PATH, loader=VerifiedLoader(name, str(PRIOR_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# P retains original paths/budgets for its authorized OFFLINE replay. T is a
# separate module, with its own independently instantiated frozen C1 module.
P, T = load_prior("c3b_original_replay"), load_prior("c3b_current_helpers")
T.HERE = T.C.HERE = HERE
T.C.EXPECTED = PRIOR_SIZES + [2097152]
T.C.EXPANDED_TOTAL_CAP = 100663296
NAMES = (T.NAMES[3], T.NAMES[0], T.NAMES[1], T.NAMES[3])


def prior_evidence():
    if T.C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    with contextlib.redirect_stdout(io.StringIO()):
        P.replay()  # Its original readonly binding/plan validation stays isolated.
    outcome = P.C.read("outcome.json")
    expected_ledger = [{"slot": n, "status": "OK" if n <= 2 else "FAILED" if n == 3 else "NOT_ATTEMPTED"}
                       for n in range(1, 9)]
    if (outcome["status"] != "STOP" or outcome["worker_returncode"] != 1 or outcome["ledger"] != expected_ledger
            or outcome["worker_error_code"] != "STOP_HTTP_IDENTITY_OR_STATUS"
            or outcome["resource_usage"]["compressed_bytes"] != 0 or outcome["resource_usage"]["expanded_bytes"] != 0
            or P.C.read("slot-3-http.json")["status"] != 404):
        raise ValueError("STOP_PRIOR_STATE")
    old_slots = P.C.read("run-start.json")["slots"]
    result = []
    for slot, size in zip(old_slots[:2], PRIOR_SIZES, strict=True):
        n = slot["slot"]
        http, receipt = P.C.read(f"slot-{n}-http.json"), P.C.read(f"slot-{n}-result.json")
        if P.validate_head(slot, http) != receipt or receipt["advertised_compressed_bytes"] != size:
            raise ValueError("STOP_PRIOR_HEAD")
        result.append({"original_slot": slot, "http": http, "receipt": receipt,
                       "http_sha256": T.C.sha(PRIOR_PATH.with_name(f"slot-{n}-http.json")),
                       "receipt_sha256": T.C.sha(PRIOR_PATH.with_name(f"slot-{n}-result.json"))})
    return result


def plan():
    if T.C.sha(T.O.INVENTORY) != T.O.INVENTORY_HASH or T.C.sha(T.O.INDEX) != T.O.INDEX_HASH:
        raise ValueError("STOP_INVENTORY_HASH")
    entries = json.loads(T.O.INVENTORY.read_bytes())["entries"]
    for name in set(NAMES):
        found = [r for r in entries if r["name"] == name]
        if len(found) != 1 or found[0]["url"] != T.O.BASE + name:
            raise ValueError("STOP_INVENTORY_SELECTION")
    return [{"slot": n, "method": "HEAD" if n == 1 else "GET", "url": T.O.BASE + name, "filename": name}
            for n, name in enumerate(NAMES, 1)]


def binding(protocol):
    import astropy
    import requests

    paths = (PRIOR_PATH, PRIOR_PATH.with_name("test_acquire.py"), T.C1_PATH, T.C1_PATH.with_name("test_acquire.py"),
             T.C.C0D_PATH, T.C.STRUCTURE_PATH, T.C.STRUCTURE_TEST, T.C.STRUCTURE_REVIEW, T.C.HELPER)
    expected = (PRIOR_HASH, PRIOR_TEST_HASH, T.C1_HASH, T.C1_TEST_HASH, T.C.C0D_HASH, T.C.STRUCTURE_HASH,
                T.C.STRUCTURE_TEST_HASH, T.C.STRUCTURE_REVIEW_HASH, T.C.HELPER_HASH)
    dependencies = {str(path): T.C.sha(path) for path in paths}
    if list(dependencies.values()) != list(expected):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"slots": plan(), "prior_heads": prior_evidence(), "prior_outcome_sha256": PRIOR_OUTCOME,
            "configuration": T.configuration(), "source_sha256": T.C.sha(SOURCE),
            "tests_sha256": T.C.sha(HERE / "test_acquire.py"), "protocol_sha256": T.C.sha(protocol),
            "dependencies": dependencies, "inventory_sha256": T.O.INVENTORY_HASH, "index_sha256": T.O.INDEX_HASH,
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "requests": requests.__version__, "astropy": astropy.__version__}}


def verify_binding():
    if T.C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def get_plan(start):
    slots, imported = start["slots"], start["prior_heads"]
    if len(imported) != 2 or [r["receipt"]["advertised_compressed_bytes"] for r in imported] != PRIOR_SIZES:
        raise ValueError("STOP_IMPORTED_HEADS")
    head = slots[0]
    http = T.C.read("slot-1-http.json")
    record = T.validate_head(head, http)
    if T.C.read("slot-1-result.json") != record:
        raise ValueError("STOP_ATT_HEAD_GATE")
    all_heads = imported + [{"http": http, "receipt": record}]
    gets = []
    for slot, evidence in zip(slots[1:], all_heads, strict=True):
        source_http, receipt = evidence["http"], evidence["receipt"]
        # Exact URL identity prevents accidentally using the prior 404's length
        # or an accepted size belonging to a different product.
        expected = T.validate_head({**slot, "method": "HEAD"}, source_http)
        if (receipt["status"] != "OK" or source_http["url"] != slot["url"]
                or expected["advertised_compressed_bytes"] != receipt["advertised_compressed_bytes"]):
            raise ValueError("STOP_IMPORTED_HEAD_IDENTITY")
        gets.append({**slot, "expected_bytes": receipt["advertised_compressed_bytes"], "head_headers": source_http["headers"]})
    if sum(g["expected_bytes"] for g in gets) > 2876224:
        raise ValueError("STOP_COMPRESSED_TOTAL")
    return gets


def ledger(start, verify=True):
    rows, stopped, previous, gets = [], False, -1, None
    for original in start["slots"]:
        n = original["slot"]
        row = {"slot": n, "status": "NOT_ATTEMPTED"}
        marker, receipt = HERE / f"slot-{n}-start.json", HERE / f"slot-{n}-result.json"
        if marker.exists():
            mark = T.C.read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or mark.get("slot") != original or set(mark) != {"slot", "elapsed_seconds"}
                    or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not previous <= elapsed < SECONDS):
                raise ValueError("STOP_REQUEST_ORDER")
            previous = elapsed
            if n == 2:
                gets = get_plan(start)
            slot = original if n == 1 else gets[n - 2]
            row["status"] = "INTERRUPTED"
            if receipt.exists():
                record = T.C.read(receipt.name)
                if record.get("slot") != slot or record.get("status") not in ("OK", "FAILED"):
                    raise ValueError("STOP_RECEIPT_IDENTITY")
                if verify and record["status"] == "OK":
                    expected = (T.validate_head(slot, T.C.read(f"slot-{n}-http.json")) if n == 1
                                else T.product_record(slot, verify=True))
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
             else "NOT_ATTEMPTED"} for n in range(1, 5)]


def worker():
    began = time.monotonic()
    T.C.DEADLINE = began + SECONDS
    result = {"status": "STOP"}
    start = T.C.read("run-start.json")
    try:
        verify_binding()
        T.C.save("worker-start.json", {"binding_sha256": T.C.sha(HERE / "run-start.json")})
        gets = None
        for original in start["slots"]:
            T.C.checkpoint()
            if shutil.disk_usage(HERE).free < FREE_BYTES:
                raise ValueError("STOP_FREE_SPACE")
            n = original["slot"]
            if n == 2:
                gets = get_plan(start)
            slot = original if n == 1 else gets[n - 2]
            T.C.save(f"slot-{n}-start.json", {"slot": original, "elapsed_seconds": time.monotonic() - began})
            try:
                record = T.collect_head(slot) if n == 1 else T.collect_get(slot)
                T.C.save(f"slot-{n}-result.json", record)
            except Exception as error:
                T.C.save(f"slot-{n}-result.json", {"slot": slot, "status": "FAILED", **T.O.failure(error)}, terminal=True)
                raise
        T.C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Eligible-coverage worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(T.O.failure(error))
    finally:
        T.C.DEADLINE = None
        try:
            result["ledger"] = ledger(start, verify=False)
        except Exception:
            LOGGER.exception("Eligible-coverage ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=fallback_ledger(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(artifacts=T.artifacts(), resource_usage=T.C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        T.C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    start = T.C.read("run-start.json")
    rows = ledger(start)
    worker = T.C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    if worker and (worker["ledger"] != rows or worker["artifacts"] != T.artifacts(("worker-result.json", "outcome.json"))
                   or worker["resource_usage"] != T.C.resource_usage(exclude=("worker-result.json", "outcome.json"))
                   or type(worker["peak_memory_bytes"]) is not int or worker["peak_memory_bytes"] <= 0):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and worker is not None and worker["status"] == PASS
    if success and (any(r["status"] != "OK" for r in rows) or worker["peak_memory_bytes"] > T.C.MEMORY_CAP
                    or T.C.read("worker-start.json") != {"binding_sha256": T.C.sha(HERE / "run-start.json")}):
        raise ValueError("STOP_FALSE_SUCCESS")
    if success:
        T.verify_product_set(get_plan(start))
    return {"status": PASS if success else "STOP", "ledger": rows, "worker_returncode": code,
            "worker_error_code": worker.get("error_code") if worker else None,
            "worker_peak_memory_bytes": worker["peak_memory_bytes"] if worker else None,
            "resource_usage": T.C.resource_usage(exclude=("outcome.json",)), "arrays_interpreted": False,
            "prior_c3_status": "STOP_MOS2_HEAD_404_PRESERVED"}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        T.C.checkpoint()
        if shutil.disk_usage(HERE).free < FREE_BYTES:
            raise ValueError("STOP_FREE_SPACE")
        T.C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = T.C.load_pinned("c3b_deadline", T.C.HELPER, T.C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("Eligible-coverage parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(T.O.failure(error), ledger=fallback_ledger())
    finally:
        result.update(artifacts=T.artifacts(("outcome.json",)), source_sha256=T.C.sha(SOURCE, monitor=False))
        T.C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(result["status"])
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = T.C.read("outcome.json")
    if outcome["artifacts"] != T.artifacts(("outcome.json",)) or outcome["source_sha256"] != T.C.sha(SOURCE):
        raise ValueError("STOP_OUTCOME_ARTIFACTS")
    peak = outcome.get("parent_peak_memory_bytes")
    if type(peak) is not int or peak <= 0 or (peak > T.C.MEMORY_CAP and
            (outcome["status"] != "STOP" or outcome.get("error_code") != "STOP_PEAK_MEMORY")):
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    T.C.resource_usage()
    if outcome["assessment_completed"] is False:
        if outcome["status"] != "STOP" or outcome["ledger"] != fallback_ledger():
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; products remain unverified")
        return
    expected = assess(outcome["worker_returncode"])
    if peak > T.C.MEMORY_CAP:
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
        LOGGER.exception("Eligible-coverage command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(T.O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
