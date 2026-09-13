"""One exact MOS2 EXPMAP request; bounded transport and header identity only."""

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import shutil
import sys
import time
import warnings
from pathlib import Path

from astropy.io.fits import Header

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C6-2026-09-12.md"
TRANSPORT = HERE.parent / "XMM-C3d-2026-09-12-data/acquire.py"
TRANSPORT_HASH = "87caca0e856065d33ff4f60404399915eed8a4b50a9afa7d0106f98fb691f825"
TRANSPORT_TEST_HASH = "8d313d56946a5f68fb30af8b39c41910121a079d646ccff9e074dcbfc809cf56"
C3_PATH = HERE.parent / "XMM-C3-2026-09-12-data/acquire.py"
C3_HASH = "7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60"
C3_OUTCOME = "62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e"
C3_HTTP = "b53c70f2ea0b330f53bb55812cd8d5ac1415b2a31caa6c33466250d569430b27"
C3_RESULT = "7d4b9aa13fbf705b32c3dd8795b5b39c253eca5e16cd7d91f719b571888e4f7a"
C5_PATH = HERE.parent / "XMM-C5-2026-09-12-data/outcome.json"
C5_OUTCOME = "58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36"
SELECTOR_NOTE = HERE.parent / "XMM-MOS2-ALTERNATE-2026-09-12.md"
SELECTOR_HASH = "a816fd84aece2eb4acd4c4cf0dd630416a9563a26af46a4deee24ce33a393760"
URL = ("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS"
       "&instname=M2&expflag=S&expno=002&name=EXPMAP&datasubsetno=8&sourceno=000&extension=FTZ")
EXPECTED = "P0884250101M2S002EXPMAP8000.FTZ"
CAP, SECONDS, FREE_BYTES = 2097152, 60, 67108864
PASS = "MOS2_MAP_RETAINED_HEADERS_ONLY"
LOGGER = logging.getLogger(__name__)


def load_transport():
    raw = TRANSPORT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != TRANSPORT_HASH:
        raise ValueError("STOP_TRANSPORT_SOURCE_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(TRANSPORT), "exec")

    spec = importlib.util.spec_from_file_location("c6_transport", TRANSPORT, loader=VerifiedLoader("c6_transport", str(TRANSPORT)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Only pure transport/format/receipt helpers from this new independent module
# are used. Neither its old worker/run nor its ATT prior-evidence function runs.
T = load_transport()
C = T.C
T.HERE = C.HERE = HERE
T.P.URL, T.P.EXPECTED = URL, EXPECTED
T.CAP, T.SECONDS, T.FREE_BYTES = CAP, SECONDS, FREE_BYTES
C.SECONDS, C.CHUNK = SECONDS, 1048576
C.EXPECTED = [CAP]
C.EXPANDED_FILE_CAP = C.EXPANDED_TOTAL_CAP = 33554432
C.MEMORY_CAP, C.JSON_CAP, C.HEADER_CAP, C.RESERVE = 500000000, 1048576, 2097152, 65536
T.SLOT = {"slot": 1, "method": "GET", "url": URL, "filename": EXPECTED}
T.RAW, T.EXPANDED = C.paths(T.SLOT)
O = T.P.O
BASE_PRODUCT_RECORD = T.product_record


def prior_evidence():
    if (C.sha(C3_PATH.with_name("outcome.json")) != C3_OUTCOME
            or C.sha(C3_PATH.with_name("slot-3-http.json")) != C3_HTTP
            or C.sha(C3_PATH.with_name("slot-3-result.json")) != C3_RESULT
            or C.sha(C5_PATH) != C5_OUTCOME):
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    prior = C.load_pinned("c6_original_c3_replay", C3_PATH, C3_HASH)
    with contextlib.redirect_stdout(io.StringIO()):
        prior.replay()  # Original C3 had zero products: receipt-only, no array access.
    outcome = prior.C.read("outcome.json")
    http, receipt = prior.C.read("slot-3-http.json"), prior.C.read("slot-3-result.json")
    if (outcome["status"] != "STOP" or outcome["worker_returncode"] != 1
            or outcome["worker_error_code"] != "STOP_HTTP_IDENTITY_OR_STATUS"
            or http["status"] != 404 or http["method"] != "HEAD"
            or not http["url"].endswith("/" + EXPECTED) or receipt["status"] != "FAILED"
            or outcome["resource_usage"]["compressed_bytes"] != 0 or outcome["resource_usage"]["expanded_bytes"] != 0):
        raise ValueError("STOP_PRIOR_MOS2_STATE")
    entries = json.loads(prior.O.INVENTORY.read_bytes())["entries"]
    selected = [r for r in entries if r["name"] == EXPECTED]
    if len(selected) != 1 or selected[0]["url"] != http["url"]:
        raise ValueError("STOP_INVENTORY_IDENTITY")
    return {"c3_outcome_sha256": C3_OUTCOME, "c3_mos2_http_sha256": C3_HTTP,
            "c3_mos2_result_sha256": C3_RESULT, "inventory_sha256": prior.O.INVENTORY_HASH,
            "index_sha256": prior.O.INDEX_HASH, "c5_outcome_sha256": C5_OUTCOME,
            "c3_state": "STOP_MOS2_HEAD_404_PRESERVED", "c5_action": "hash_only_no_numerical_replay"}


def binding(protocol):
    import astropy
    import requests

    paths = {TRANSPORT: TRANSPORT_HASH, TRANSPORT.with_name("test_acquire.py"): TRANSPORT_TEST_HASH,
             T.PRIOR_PATH: T.PRIOR_HASH, T.PRIOR_PATH.with_name("test_acquire.py"): T.PRIOR_TEST_HASH,
             T.P.C1_PATH: T.P.C1_HASH, T.P.C1_PATH.with_name("test_acquire.py"): T.C1_TEST_HASH,
             C.C0D_PATH: C.C0D_HASH, C.STRUCTURE_PATH: C.STRUCTURE_HASH, C.STRUCTURE_TEST: C.STRUCTURE_TEST_HASH,
             C.STRUCTURE_REVIEW: C.STRUCTURE_REVIEW_HASH, C.HELPER: C.HELPER_HASH,
             C3_PATH: C3_HASH, SELECTOR_NOTE: SELECTOR_HASH}
    if any(C.sha(p) != h for p, h in paths.items()):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"slot": T.SLOT, "prior": prior_evidence(), "dependencies": {str(p): h for p, h in paths.items()},
            "source_sha256": C.sha(SOURCE), "tests_sha256": C.sha(HERE / "test_acquire.py"),
            "protocol_sha256": C.sha(protocol),
            "configuration": {"output_directory": str(C.HERE), "seconds": C.SECONDS, "chunk": C.CHUNK,
                              "raw_caps": C.EXPECTED, "expanded_file": C.EXPANDED_FILE_CAP, "expanded_total": C.EXPANDED_TOTAL_CAP,
                              "memory": C.MEMORY_CAP, "json": C.JSON_CAP, "header": C.HEADER_CAP, "reserve": C.RESERVE,
                              "free_bytes": FREE_BYTES, "image_contract": "one_primary_float32_positive_2D_under_expanded_cap",
                              "deadline_policy": "monotonic worker start plus60; helper60"},
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "astropy": astropy.__version__, "requests": requests.__version__}}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def map_identity(report):
    if (report.get("hdu_count") != 1 or len(report.get("hdus", [])) != 1
            or report.get("parser_warning_categories")):
        raise ValueError("STOP_MAP_HDU_IDENTITY")
    record = report["hdus"][0]
    if record.get("hdu") != 0 or record.get("extname") != "PRIMARY":
        raise ValueError("STOP_MAP_HDU_IDENTITY")
    with warnings.catch_warnings(record=True) as caught:
        h = Header.fromstring("".join(record["cards"]))
        keys = [k for k in h if k not in ("", "HISTORY", "COMMENT")]
        if caught or len(keys) != len(set(keys)):
            raise ValueError("STOP_MAP_HEADER_AMBIGUITY")
    exact = {"SIMPLE": True, "BITPIX": -32, "NAXIS": 2,
             "OBS_ID": "0884250101", "INSTRUME": "EMOS2", "EXPIDSTR": "S002"}
    if any(h.get(k) != v for k, v in exact.items()):
        raise ValueError("STOP_MAP_ENTITY")
    shape = [h.get("NAXIS2"), h.get("NAXIS1")]
    if any(type(n) is not int or n <= 0 for n in shape) or shape[0] * shape[1] * 4 > C.EXPANDED_FILE_CAP:
        raise ValueError("STOP_MAP_SHAPE")
    if record.get("data_bytes") != shape[0] * shape[1] * 4:
        raise ValueError("STOP_MAP_DATA_LAYOUT")
    return {"observation": "0884250101", "instrument": "EMOS2", "exposure": "S002",
            "primary_bitpix": -32, "shape_rows_columns": shape, "declared_image_bytes": record["data_bytes"],
            "wcs_and_scientific_compatibility": "NOT_ADJUDICATED"}


def product_record(verify=False):
    result = BASE_PRODUCT_RECORD(verify=verify)
    result["map_identity"] = map_identity(C.read(T.HEADER_NAME))
    return result


T.product_record = product_record  # Its read-only ledger must validate the extra entity contract too.


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
        C.save("request-start.json", {"slot": T.SLOT, "elapsed_seconds": time.monotonic() - began})
        try:
            T.download()
            T.expand()
            C.save(T.HEADER_NAME, C.headers(T.SLOT), header=True)
            C.save("request-result.json", product_record())
        except Exception as error:
            C.save("request-result.json", {"slot": T.SLOT, "status": "FAILED", **O.failure(error)}, terminal=True)
            raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("MOS2 worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            result["ledger"] = T.ledger(verify=False)
        except Exception:
            LOGGER.exception("MOS2 ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            result.update(status="STOP", ledger=T.fallback(), error_code="STOP_LEDGER_UNVERIFIED")
        result.update(artifacts=T.artifacts(), resource_usage=C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    rows = T.ledger()
    w = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    if w and (w["ledger"] != rows or w["artifacts"] != T.artifacts(("worker-result.json", "outcome.json"))
              or w["resource_usage"] != C.resource_usage(exclude=("worker-result.json", "outcome.json"))
              or type(w["peak_memory_bytes"]) is not int or w["peak_memory_bytes"] <= 0):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and w is not None and w["status"] == PASS
    if success:
        products = {p for p in (HERE / "products").rglob("*") if p.is_file()}
        headers = {p for p in (HERE / "headers").rglob("*") if p.is_file()}
        if (rows != [{"slot": 1, "status": "OK"}] or w["peak_memory_bytes"] > C.MEMORY_CAP
                or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}
                or products != {T.RAW, T.EXPANDED} or headers != {HERE / T.HEADER_NAME}):
            raise ValueError("STOP_FALSE_SUCCESS_OR_PRODUCT_SET")
    return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
            "worker_error_code": w.get("error_code") if w else None, "worker_peak_memory_bytes": w["peak_memory_bytes"] if w else None,
            "resource_usage": C.resource_usage(exclude=("outcome.json",)), "arrays_interpreted": False,
            "prior_c3_status": "STOP_MOS2_HEAD_404_PRESERVED", "prior_c5_outcome_sha256": C5_OUTCOME}


def run():
    if T.artifacts():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c6_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("MOS2 parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error), ledger=T.fallback())
    finally:
        result.update(artifacts=T.artifacts(("outcome.json",)), source_sha256=C.sha(SOURCE, monitor=False))
        C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(result["status"])
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = C.read("outcome.json")
    if type(outcome.get("assessment_completed")) is not bool:
        raise ValueError("STOP_ASSESSMENT_FLAG")
    if outcome["artifacts"] != T.artifacts(("outcome.json",)) or outcome["source_sha256"] != C.sha(SOURCE):
        raise ValueError("STOP_OUTCOME_ARTIFACTS")
    peak = outcome.get("parent_peak_memory_bytes")
    if type(peak) is not int or peak <= 0 or (peak > C.MEMORY_CAP and
            (outcome["status"] != "STOP" or outcome.get("error_code") != "STOP_PEAK_MEMORY")):
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    C.resource_usage()
    if outcome["assessment_completed"] is False:
        if outcome["status"] != "STOP" or outcome["ledger"] != T.fallback():
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
        LOGGER.exception("MOS2 command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
