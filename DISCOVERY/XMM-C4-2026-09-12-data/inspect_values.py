"""One local ATTHK payload, bounded decoding and aggregate-only diagnostics."""

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import math
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from astropy.io.fits import Header

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C4-2026-09-12.md"
PRIOR_PATH = HERE.parent / "XMM-C3d-2026-09-12-data/acquire.py"
PRIOR_HASH = "87caca0e856065d33ff4f60404399915eed8a4b50a9afa7d0106f98fb691f825"
PRIOR_OUTCOME = "2a1a7340c89292882f2b205ff48f4babbada46ed4dde210b45ec1bdd4a6bed0d"
PRODUCT = PRIOR_PATH.parent / "products/P0884250101OBX000ATTTSR0000.fits"
PRODUCT_HASH = "ff251ab4e22655bc02b612a599160e40cfe3176cf8de90ce4514668e5bcf7a17"
HEADER_HASH = "a5c5d3a9113b88b63e560be09dc72df0ece14b35c8e91fdefcbc73c77a8d8409"
CORE_PATH = HERE.parent / "xmm_attitude.py"
CORE_HASH = "df6a49a01d20f6b58c275881fea48a95de158ee6e8c04c272b0ef2ac616f7f4a"
CORE_TEST = HERE.parent / "test_xmm_attitude.py"
CORE_TEST_HASH = "1af690f296a88d8e6267d055eb2d17f32e8742d37c68e3f03936fd8e7098027f"
C1_OUTCOME = "c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc"
SECONDS, ROWS, WIDTH, PAYLOAD, CHUNK_ROWS = 60, 51975, 80, 4158000, 10000
PASS = "ATTITUDE_VALUES_SUMMARIZED_UNCALIBRATED"
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

    spec = importlib.util.spec_from_file_location("c4_prior", PRIOR_PATH, loader=VerifiedLoader("c4_prior", str(PRIOR_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load_prior()
C = P.P.load_c1()  # Independent instance: prior replay keeps original directories.
C.HERE, C.SECONDS = HERE, SECONDS
C.MEMORY_CAP, C.JSON_CAP, C.RESERVE = 500000000, 1048576, 65536
O = P.P.O


def header(record):
    with warnings.catch_warnings(record=True) as caught:
        value = Header.fromstring("".join(record["cards"]))
        keys = [k for k in value if k not in ("", "HISTORY", "COMMENT")]
        if caught or len(keys) != len(set(keys)):
            raise ValueError("STOP_HEADER_AMBIGUITY")
    return value


def att_table(report):
    if report["file_bytes"] != 4173120 or report["hdu_count"] != 2 or len(report["hdus"]) != 2:
        raise ValueError("STOP_PRODUCT_LAYOUT")
    primary, record = report["hdus"]
    p, h = header(primary), header(record)
    if p.get("OBS_ID") != "0884250101" or record["extname"] != "ATTHK":
        raise ValueError("STOP_ATT_IDENTITY")
    expected = {"XTENSION": "BINTABLE", "BITPIX": 8, "NAXIS": 2, "NAXIS1": WIDTH,
                "NAXIS2": ROWS, "TFIELDS": 10, "PCOUNT": 0, "GCOUNT": 1}
    if any(h.get(k) != v for k, v in expected.items()):
        raise ValueError("STOP_TABLE_LAYOUT")
    if any(re.fullmatch(r"(TSCAL|TZERO|TNULL|TDIM)\d+", k) or k == "THEAP" for k in h):
        raise ValueError("STOP_SCALING_NULL_OR_HEAP")
    names = ["TIME", "AHFRA", "AHFDEC", "AHFPA", "OMRA", "OMDEC", "OMPA", "DAHFPNT", "DOMPNT", "DAHFOM"]
    columns = [[name, "D", "sec" if i == 1 else "degrees"] for i, name in enumerate(names, 1)]
    for i, column in enumerate(columns, 1):
        if [h.get(f"TTYPE{i}"), h.get(f"TFORM{i}"), h.get(f"TUNIT{i}")] != column:
            raise ValueError("STOP_COLUMN_SCHEMA")
    if any(k in p or k in h for k in ("TIMESYS", "TIMEREF", "TIMEUNIT", "MJDREF", "MJDREFI", "MJDREFF", "TIMEZERO")):
        raise ValueError("STOP_CHANGED_ATT_TIME_REFERENCE")
    if (record["data_offset"], record["data_bytes"]) != (14400, PAYLOAD):
        raise ValueError("STOP_PAYLOAD_SPAN")
    counts = {k: p.get(k) for k in ("NATT", "NGAHF", "NGOM", "NGAHFOM")}
    if any(type(v) is not int or not 0 <= v <= ROWS for v in counts.values()):
        raise ValueError("STOP_HEADER_COUNTS")
    return {"table": 1, "extname": "ATTHK", "rows": ROWS, "width": WIDTH, "columns": columns,
            "data_offset": 14400, "data_bytes": PAYLOAD, "file_bytes": 4173120,
            "file_sha256": PRODUCT_HASH, "header_sha256": HEADER_HASH, "header_counts": counts}


def camera_range(report, camera, exposure):
    records = [r for r in report["hdus"] if r["extname"] == "EVENTS"]
    if len(records) != 1:
        raise ValueError("STOP_EVENTS_COUNT")
    h = header(records[0])
    if (h.get("OBS_ID"), h.get("INSTRUME"), h.get("EXPIDSTR")) != ("0884250101", camera, exposure):
        raise ValueError("STOP_CAMERA_IDENTITY")
    if (h.get("TIMESYS"), h.get("TIMEUNIT"), h.get("MJDREF"), h.get("TIMEZERO")) != ("TT", "s", 50814.0, 0):
        raise ValueError("STOP_CAMERA_TIME_REFERENCE")
    start, stop = h.get("TSTART"), h.get("TSTOP")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (start, stop)) or start >= stop:
        raise ValueError("STOP_CAMERA_TIME_RANGE")
    return {"camera": camera, "start": start, "stop": stop}


def manifest():
    """Header JSON and receipt hashes only; never open any science product."""
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    outcome = json.loads(PRIOR_PATH.with_name("outcome.json").read_bytes())
    if outcome["status"] != P.PASS or outcome["worker_returncode"] != 0:
        raise ValueError("STOP_PRIOR_STATUS")
    att_header = PRIOR_PATH.parent / "headers/slot-1-headers.json"
    if C.sha(att_header) != HEADER_HASH or outcome["artifacts"]["headers/slot-1-headers.json"] != HEADER_HASH:
        raise ValueError("STOP_ATT_HEADER_HASH")
    if outcome["artifacts"]["products/" + PRODUCT.name] != PRODUCT_HASH:
        raise ValueError("STOP_ATT_PRODUCT_HASH_BINDING")
    table = att_table(json.loads(att_header.read_bytes()))
    c1 = P.P.C1_PATH.parent
    if C.sha(c1 / "outcome.json") != C1_OUTCOME:
        raise ValueError("STOP_C1_OUTCOME_HASH")
    old = json.loads((c1 / "outcome.json").read_bytes())
    if old["status"] != C.PASS or old["worker_returncode"] != 0:
        raise ValueError("STOP_C1_STATUS")
    ranges, hashes = [], {}
    for i, (camera, exposure) in enumerate((("EPN", "S003"), ("EMOS1", "S001"), ("EMOS2", "S002")), 1):
        name = f"headers/slot-{i}-headers.json"
        digest = C.sha(c1 / name)
        if digest != old["artifacts"][name]:
            raise ValueError("STOP_C1_HEADER_HASH")
        ranges.append(camera_range(json.loads((c1 / name).read_bytes()), camera, exposure))
        hashes[name] = digest
    return {"table": table, "camera_ranges": ranges, "c1_header_hashes": hashes}


def binding(protocol):
    import astropy

    paths = {CORE_PATH: CORE_HASH, CORE_TEST: CORE_TEST_HASH, PRIOR_PATH: PRIOR_HASH,
             C.HELPER: C.HELPER_HASH, P.P.C1_PATH: P.P.C1_HASH}
    if any(C.sha(path) != digest for path, digest in paths.items()):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"manifest": manifest(), "dependencies": {str(p): h for p, h in paths.items()},
            "source_sha256": C.sha(SOURCE), "tests_sha256": C.sha(HERE / "test_inspect_values.py"),
            "protocol_sha256": C.sha(protocol), "prior_outcome_sha256": PRIOR_OUTCOME, "c1_outcome_sha256": C1_OUTCOME,
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "numpy": np.__version__, "astropy": astropy.__version__},
            "caps": {"seconds": SECONDS, "memory": C.MEMORY_CAP, "json": C.JSON_CAP, "reserve": C.RESERVE,
                     "payload_bytes_per_pass": PAYLOAD, "chunk_rows": CHUNK_ROWS}, "output_directory": str(HERE)}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def verify_prior():
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True):
        P.replay()
    if C.sha(PRODUCT) != PRODUCT_HASH:
        raise ValueError("STOP_PRODUCT_HASH")
    C.checkpoint()


def decode(stream, table, accounting):
    if (table["extname"], table["rows"], table["width"], table["data_offset"], table["data_bytes"], table["file_bytes"]) != (
            "ATTHK", ROWS, WIDTH, 14400, PAYLOAD, 4173120):
        raise ValueError("STOP_FORBIDDEN_ARRAY_OR_SPAN")
    data = np.empty((ROWS, 10), dtype=float)
    stream.seek(table["data_offset"])
    for start in range(0, ROWS, CHUNK_ROWS):
        C.checkpoint()
        n = min(CHUNK_ROWS, ROWS - start)
        size = n * WIDTH
        if accounting["read_bytes"] + size > PAYLOAD:
            raise ValueError("STOP_PAYLOAD_CAP")
        raw = stream.read(size)
        accounting["read_bytes"] += len(raw)
        if len(raw) != size:
            raise ValueError("STOP_TRUNCATED_TABLE")
        decoded = np.frombuffer(raw, dtype=">f8").reshape(n, 10)
        accounting["decoded_bytes"] += size
        data[start:start + n] = decoded
    C.checkpoint()
    return data


def measure(plan, accounting):
    core = C.load_pinned("c4_numerical_core", CORE_PATH, CORE_HASH)
    with PRODUCT.open("rb") as stream:
        data = decode(stream, plan["table"], accounting)
    result = core.summarize(data, plan["camera_ranges"], plan["table"]["header_counts"])
    C.checkpoint()
    return result


def artifacts(exclude=()):
    return {p.name: C.sha(p, monitor=False) for p in HERE.iterdir() if p.is_file() and p.name not in exclude
            and (p.suffix == ".json" or p.name == "protocol.snapshot.md")}


def fallback():
    return [{"table": 1, "status": "UNVERIFIED_ATTEMPT" if any((HERE / n).exists() for n in
            ("table-start.json", "table-result.json")) else "NOT_ATTEMPTED"}]


def ledger(recompute=False):
    if not (HERE / "table-start.json").exists():
        if (HERE / "table-result.json").exists():
            raise ValueError("STOP_ORPHAN_RECEIPT")
        return [{"table": 1, "status": "NOT_ATTEMPTED"}]
    marker = C.read("table-start.json")
    elapsed = marker.get("elapsed_seconds")
    if (set(marker) != {"table", "elapsed_seconds"} or marker["table"] != 1 or type(elapsed) not in (int, float)
            or not math.isfinite(elapsed) or not 0 <= elapsed < SECONDS):
        raise ValueError("STOP_TABLE_MARKER")
    if not (HERE / "table-result.json").exists():
        return [{"table": 1, "status": "INTERRUPTED"}]
    record = C.read("table-result.json")
    if record.get("table") != 1 or record.get("status") not in ("OK", "STOP"):
        raise ValueError("STOP_TABLE_RECEIPT")
    a = record["accounting"]
    if (set(a) != {"read_bytes", "decoded_bytes"} or any(type(v) is not int for v in a.values())
            or not 0 <= a["decoded_bytes"] <= a["read_bytes"] <= PAYLOAD or a["decoded_bytes"] % WIDTH):
        raise ValueError("STOP_ACCOUNTING_RECEIPT")
    if record["status"] == "OK":
        if a != {"read_bytes": PAYLOAD, "decoded_bytes": PAYLOAD}:
            raise ValueError("STOP_SUCCESS_ACCOUNTING")
        if recompute:
            accounting = {"read_bytes": 0, "decoded_bytes": 0}
            expected = {"table": 1, "status": "OK", "summary": measure(C.read("run-start.json")["manifest"], accounting),
                        "accounting": accounting}
            if record != expected:
                raise ValueError("STOP_SUMMARY_REPLAY")
    elif (set(record) != {"table", "status", "error_type", "error_code", "accounting"}
          or not isinstance(record["error_type"], str) or not record["error_type"].isidentifier()
          or (record["error_code"] is not None and not re.fullmatch(r"STOP_[A-Z0-9_]+", record["error_code"]))):
        raise ValueError("STOP_FAILED_RECEIPT")
    return [{"table": 1, "status": record["status"], "accounting": a}]


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result, accounting = {"status": "STOP"}, {"read_bytes": 0, "decoded_bytes": 0}
    try:
        verify_binding()
        C.save("worker-start.json", {"binding_sha256": C.sha(HERE / "run-start.json")})
        verify_prior()
        C.checkpoint()
        C.save("table-start.json", {"table": 1, "elapsed_seconds": time.monotonic() - began})
        try:
            summary = measure(C.read("run-start.json")["manifest"], accounting)
            C.save("table-result.json", {"table": 1, "status": "OK", "summary": summary, "accounting": accounting})
        except Exception as error:
            C.save("table-result.json", {"table": 1, "status": "STOP", **O.failure(error), "accounting": accounting}, terminal=True)
            raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Attitude worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            result["ledger"] = ledger()
        except Exception:
            LOGGER.exception("Attitude ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=fallback(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(accounting=accounting, artifacts=artifacts(), resource_usage=C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    C.DEADLINE = time.monotonic() + SECONDS
    try:
        verify_binding()
        verify_prior()
        rows = ledger(recompute=True)
        w = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
        if w and (w["ledger"] != rows or w["artifacts"] != artifacts(("worker-result.json", "outcome.json"))
                  or w["resource_usage"] != C.resource_usage(exclude=("worker-result.json", "outcome.json"))
                  or type(w["peak_memory_bytes"]) is not int or w["peak_memory_bytes"] <= 0
                  or w["accounting"] != rows[0].get("accounting", {"read_bytes": 0, "decoded_bytes": 0})):
            raise ValueError("STOP_WORKER_CLOSURE")
        success = code == 0 and w is not None and w["status"] == PASS
        if success and (rows[0]["status"] != "OK" or w["peak_memory_bytes"] > C.MEMORY_CAP
                        or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}):
            raise ValueError("STOP_FALSE_SUCCESS")
        C.checkpoint()
        return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
                "worker_peak_memory_bytes": w["peak_memory_bytes"] if w else None, "worker_error_code": w.get("error_code") if w else None,
                "resource_usage": C.resource_usage(exclude=("outcome.json",)), "photons_or_map_pixels_interpreted": False,
                "absolute_angles_persisted": False}
    finally:
        C.DEADLINE = None


def run():
    if any((HERE / name).exists() for name in ("run-start.json", "outcome.json", "protocol.snapshot.md",
            "worker-start.json", "worker-result.json", "table-start.json", "table-result.json")):
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c4_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("Attitude parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error), ledger=fallback())
    finally:
        result.update(artifacts=artifacts(("outcome.json",)), source_sha256=C.sha(SOURCE, monitor=False))
        C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(result["status"])
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = C.read("outcome.json")
    if type(outcome.get("assessment_completed")) is not bool:
        raise ValueError("STOP_ASSESSMENT_FLAG")
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
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; table remains unverified")
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
        LOGGER.exception("Attitude command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
