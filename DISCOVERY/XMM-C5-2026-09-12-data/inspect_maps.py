"""Two frozen local map payloads; fixed aggregate static-support diagnostics."""

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
from astropy import units as u
from astropy.coordinates import FK5, SkyCoord
from astropy.io.fits import Header
from astropy.wcs import WCS

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C5-2026-09-12.md"
PRIOR_PATH = HERE.parent / "XMM-C3e-2026-09-12-data/acquire.py"
PRIOR_HASH = "ad80cb38306388f69e51bce78fe4787279e7ba5402b4b6f7b10b44362b54aa4e"
PRIOR_OUTCOME = "af82c5ae3b7a5cd233589e6bd53eadc8d0ded37137ad6df6dac49d198a581d80"
CORE_PATH = HERE.parent / "xmm_map_support.py"
CORE_HASH = "2c93c225223aacedefd8ce160726c9f363e11626823cb8d9ae34a54dfda2307a"
CORE_TEST = HERE.parent / "test_xmm_map_support.py"
CORE_TEST_HASH = "6ba990522f625472293700c946475192c7d0ab0b5aaae46f44906143caa20bf6"
DEFINITION = HERE.parent / "XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md"
DEFINITION_HASH = "7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e"
MAPS = (
    {"map": 1, "camera": "EPN", "exposure": "S003", "filename": "P0884250101PNS003EXPMAP8000.fits",
     "offset": 46080, "file_bytes": 1728000,
     "sha256": "5a39eee5d2b438fb893e65ff6a9bc2a70896987b7b9f15ba990e24a87a4172dd",
     "header_sha256": "ec3d29a2b4c0428cc1e7e382b4521fdca83019dbc4066b63685bac076f1f3a9a"},
    {"map": 2, "camera": "EMOS1", "exposure": "S001", "filename": "P0884250101M1S001EXPMAP8000.fits",
     "offset": 23040, "file_bytes": 1704960,
     "sha256": "652846bddc9724aacd4a08fda52fc2065820615104536b3545aeb8712b63cb38",
     "header_sha256": "e34274169b7ba4298d12b04b68ba7da197f9b9dada106de2ac7fb773cc93d1e3"})
LABELS = ("published", "north120", "east120", "south120", "west120")
KINDS = ("circle20", "annulus60_90")
SECONDS, SIDE, PAYLOAD, TOTAL, CHUNK_ROWS = 60, 648, 1679616, 3359232, 16
PASS = "STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE"
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

    spec = importlib.util.spec_from_file_location("c5_prior", PRIOR_PATH, loader=VerifiedLoader("c5_prior", str(PRIOR_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load_prior()
C = P.load_prior("c5_isolated_helpers").C
C.HERE, C.SECONDS = HERE, SECONDS
C.MEMORY_CAP, C.JSON_CAP, C.RESERVE = 500000000, 1048576, 65536
O = P.T.O


def centres():
    """Published ICRS convention and fixed spherical offsets; never persisted."""
    base = SkyCoord("23h54m40.76s", "-37d30m19.4s", frame="icrs")
    values = [base] + [base.directional_offset_by(angle * u.deg, 120 * u.arcsec) for angle in (0, 90, 180, 270)]
    return [tuple(float(v) for v in (c.ra.deg, c.dec.deg)) for c in
            [position.transform_to(FK5(equinox="J2000")) for position in values]]


def map_header(report, item):
    if (report.get("file_bytes") != item["file_bytes"] or report.get("hdu_count") != 1
            or len(report.get("hdus", [])) != 1 or report.get("parser_warning_categories")):
        raise ValueError("STOP_MAP_LAYOUT")
    record = report["hdus"][0]
    expected = {"hdu": 0, "extname": "PRIMARY", "header_offset": 0, "header_bytes": item["offset"],
                "data_offset": item["offset"], "data_bytes": PAYLOAD, "data_span_padded": 1681920}
    if any(record.get(k) != v for k, v in expected.items()):
        raise ValueError("STOP_MAP_SPAN")
    with warnings.catch_warnings(record=True) as caught:
        h = Header.fromstring("".join(record["cards"]))
        keys = [k for k in h if k not in ("", "HISTORY", "COMMENT")]
        if caught or len(keys) != len(set(keys)):
            raise ValueError("STOP_HEADER_AMBIGUITY")
    exact = {"SIMPLE": True, "BITPIX": -32, "NAXIS": 2, "NAXIS1": SIDE, "NAXIS2": SIDE,
             "OBS_ID": "0884250101", "INSTRUME": item["camera"], "EXPIDSTR": item["exposure"],
             "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CUNIT1": "deg", "CUNIT2": "deg",
             "RADECSYS": "FK5", "EQUINOX": 2000.0}
    if any(h.get(k) != v for k, v in exact.items()):
        raise ValueError("STOP_MAP_SCHEMA")
    if any(k in h for k in ("BSCALE", "BZERO", "BLANK", "BUNIT", "RADESYS", "WCSAXES", "LONPOLE", "LATPOLE")):
        raise ValueError("STOP_UNSUPPORTED_MAP_METADATA")
    # Only the declared primary CDELT-only TAN mapping is selected. Retained
    # alternate L/physical coordinates are ignored, never merged with primary.
    if any(re.match(r"^(CD\d+_|PC\d+_|CROTA|PV\d+_|PS\d+_|A_|B_|AP_|BP_|CPDIS|DP\d|D2IM|DET2IM)", k) for k in h):
        raise ValueError("STOP_WCS_DISTORTION_OR_MATRIX")
    numeric = [f"{prefix}{i}" for i in (1, 2) for prefix in ("CRPIX", "CRVAL", "CDELT")]
    if any(type(h.get(k)) not in (float, int) or not math.isfinite(h[k]) for k in numeric):
        raise ValueError("STOP_WCS_NUMERIC")
    if not 0 <= h["CRVAL1"] <= 360 or not -90 <= h["CRVAL2"] <= 90 or not all(h[f"CDELT{i}"] for i in (1, 2)):
        raise ValueError("STOP_WCS_DOMAIN")
    selected = Header()
    for k in numeric + ["CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "EQUINOX"]:
        selected[k] = h[k]
    selected["RADESYS"] = "FK5"  # Explicit equivalent of verified legacy RADECSYS, not an automatic fix.
    with warnings.catch_warnings(record=True) as caught:
        wcs = WCS(selected, naxis=2, fix=False)
        if caught:
            raise ValueError("STOP_WCS_WARNING")
    return wcs


def read_header(item):
    path = PRIOR_PATH.parent / "headers" / f"slot-{item['map']}-headers.json"
    if C.sha(path) != item["header_sha256"]:
        raise ValueError("STOP_MAP_HEADER_HASH")
    return map_header(json.loads(path.read_bytes()), item)


def manifest():
    """Metadata and schema only; no product file is opened here."""
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    outcome = json.loads(PRIOR_PATH.with_name("outcome.json").read_bytes())
    if outcome["status"] != P.PASS or outcome["worker_returncode"] != 0:
        raise ValueError("STOP_PRIOR_STATUS")
    core = C.load_pinned("c5_core_schema", CORE_PATH, CORE_HASH)
    dummy = np.empty((SIDE, SIDE), dtype=np.float32)
    for item in MAPS:
        if (outcome["artifacts"]["products/" + item["filename"]] != item["sha256"]
                or outcome["artifacts"][f"headers/slot-{item['map']}-headers.json"] != item["header_sha256"]):
            raise ValueError("STOP_PRIOR_MAP_BINDING")
        wcs = read_header(item)
        for centre in centres():
            for kind in KINDS:
                core.validate(dummy, wcs, centre, kind)  # Geometry only, no dummy pixel values used.
    return {"maps": list(MAPS), "labels": list(LABELS), "kinds": list(KINDS), "planned_regions": 20,
            "definition_sha256": DEFINITION_HASH, "centre_convention": "published_ICRS_offsets_then_FK5_J2000",
            "wcs_contract": "primary_CDELT_only_RA_DEC_TAN_deg_FK5_J2000_explicit_no_fix",
            "value_contract": "absent_BUNIT_no_scaling_sign_only_no_physical_units", "MOS2": "UNAVAILABLE"}


def binding(protocol):
    import astropy

    paths = {CORE_PATH: CORE_HASH, CORE_TEST: CORE_TEST_HASH, PRIOR_PATH: PRIOR_HASH,
             C.HELPER: C.HELPER_HASH, P.T.C1_PATH: P.T.C1_HASH, DEFINITION: DEFINITION_HASH}
    if any(C.sha(path) != digest for path, digest in paths.items()):
        raise ValueError("STOP_DEPENDENCY_HASH")
    return {"manifest": manifest(), "dependencies": {str(p): h for p, h in paths.items()},
            "source_sha256": C.sha(SOURCE), "tests_sha256": C.sha(HERE / "test_inspect_maps.py"),
            "protocol_sha256": C.sha(protocol), "prior_outcome_sha256": PRIOR_OUTCOME,
            "runtime": {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                        "numpy": np.__version__, "astropy": astropy.__version__},
            "caps": {"seconds": SECONDS, "memory": C.MEMORY_CAP, "json": C.JSON_CAP, "reserve": C.RESERVE,
                     "payload_bytes_per_map": PAYLOAD, "payload_bytes_per_pass": TOTAL, "chunk_rows": CHUNK_ROWS,
                     "subdivisions": [4, 8], "maximum_box_side": 256, "core_chunk_rows": 16},
            "output_directory": str(HERE)}


def verify_binding():
    if C.read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def verify_prior():
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True):
        P.replay()  # Frozen hash/header-only replay, never any prior network worker.
    C.checkpoint()


def zero():
    return {"read_bytes": 0, "decoded_bytes": 0}


def decode(stream, item, accounting, total):
    if item not in MAPS or accounting != zero():
        raise ValueError("STOP_FORBIDDEN_ARRAY_OR_REPEAT")
    data = np.empty((SIDE, SIDE), dtype=np.float32)
    stream.seek(item["offset"])
    for start in range(0, SIDE, CHUNK_ROWS):
        C.checkpoint()
        n = min(CHUNK_ROWS, SIDE - start)
        size = n * SIDE * 4
        if accounting["read_bytes"] + size > PAYLOAD or total["read_bytes"] + size > TOTAL:
            raise ValueError("STOP_PAYLOAD_CAP")
        raw = stream.read(size)
        accounting["read_bytes"] += len(raw)
        total["read_bytes"] += len(raw)
        if len(raw) != size:
            raise ValueError("STOP_TRUNCATED_MAP")
        decoded = np.frombuffer(raw, dtype=">f4").reshape(n, SIDE)
        accounting["decoded_bytes"] += size
        total["decoded_bytes"] += size
        data[start:start + n] = decoded
    C.checkpoint()
    return data


def measure(item, accounting, total):
    core = C.load_pinned("c5_numerical_core", CORE_PATH, CORE_HASH)
    wcs = read_header(item)
    with (PRIOR_PATH.parent / "products" / item["filename"]).open("rb") as stream:
        data = decode(stream, item, accounting, total)
    summaries = []
    for label, centre in zip(LABELS, centres(), strict=True):
        for kind in KINDS:
            C.checkpoint()
            summaries.append({"label": label, "kind": kind, "diagnostic": core.summarize(data, wcs, centre, kind)})
    C.checkpoint()
    return summaries


def artifacts(exclude=()):
    return {p.relative_to(HERE).as_posix(): C.sha(p, monitor=False) for p in HERE.rglob("*")
            if p.is_file() and p.relative_to(HERE).as_posix() not in exclude
            and (p.suffix == ".json" or p.name == "protocol.snapshot.md")}


def fallback():
    return [{"map": n, "status": "UNVERIFIED_ATTEMPT" if any(HERE.glob(f"map-{n}-*.json")) else "NOT_ATTEMPTED",
             "accounting": None} for n in (1, 2)]


def valid_accounting(a, cap):
    return (isinstance(a, dict) and set(a) == {"read_bytes", "decoded_bytes"}
            and all(type(v) is int for v in a.values()) and 0 <= a["decoded_bytes"] <= a["read_bytes"] <= cap
            and a["decoded_bytes"] % (SIDE * 4) == 0)


def validation_state():
    return {"status": "NOT_ATTEMPTED", "accounting": zero(),
            "maps": [{"map": n, "status": "NOT_ATTEMPTED", "accounting": zero()} for n in (1, 2)]}


def validate_validation(record):
    if (not isinstance(record, dict) or set(record) != {"status", "accounting", "maps"}
            or record["status"] not in ("NOT_ATTEMPTED", "ATTEMPTED", "FAILED", "COMPLETED_ELIGIBLE_RECEIPTS")
            or not valid_accounting(record["accounting"], TOTAL) or len(record["maps"]) != 2):
        raise ValueError("STOP_VALIDATION_ACCOUNTING")
    stopped = False
    for n, row in enumerate(record["maps"], 1):
        if (set(row) != {"map", "status", "accounting"} or row["map"] != n
                or row["status"] not in ("NOT_ATTEMPTED", "ATTEMPTED", "FAILED", "COMPLETED")
                or not valid_accounting(row["accounting"], PAYLOAD)
                or (stopped and row["status"] != "NOT_ATTEMPTED")
                or (row["status"] == "NOT_ATTEMPTED" and row["accounting"] != zero())
                or (row["status"] == "COMPLETED" and row["accounting"] != {"read_bytes": PAYLOAD, "decoded_bytes": PAYLOAD})):
            raise ValueError("STOP_VALIDATION_ACCOUNTING")
        stopped = stopped or row["status"] != "COMPLETED"
    if record["accounting"] != aggregate(record["maps"]):
        raise ValueError("STOP_VALIDATION_ACCOUNTING")
    statuses = [r["status"] for r in record["maps"]]
    top = record["status"]
    if ((top == "NOT_ATTEMPTED") != all(s == "NOT_ATTEMPTED" for s in statuses)
            or (top == "FAILED" and "FAILED" not in statuses)
            or (top == "COMPLETED_ELIGIBLE_RECEIPTS" and
                ("COMPLETED" not in statuses or any(s in ("FAILED", "ATTEMPTED") for s in statuses)))
            or (top == "ATTEMPTED" and ("FAILED" in statuses or not any(s in ("ATTEMPTED", "COMPLETED") for s in statuses)))):
        raise ValueError("STOP_VALIDATION_ACCOUNTING")


def ledger(recompute=False, validation=None):
    rows, stopped, previous = [], False, 0.
    validation = validation_state() if validation is None else validation
    replay_accounting = validation["accounting"]
    for item in MAPS:
        n = item["map"]
        marker, receipt = HERE / f"map-{n}-start.json", HERE / f"map-{n}-result.json"
        row = {"map": n, "status": "NOT_ATTEMPTED", "accounting": zero()}
        if marker.exists():
            mark = C.read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or set(mark) != {"map", "elapsed_seconds"} or mark["map"] != n
                    or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not previous <= elapsed < SECONDS):
                raise ValueError("STOP_MAP_ORDER")
            previous = elapsed
            row.update(status="INTERRUPTED", accounting=None)
            if receipt.exists():
                r = C.read(receipt.name)
                if r.get("map") != n or r.get("status") not in ("OK", "STOP") or not valid_accounting(r.get("accounting"), PAYLOAD):
                    raise ValueError("STOP_MAP_RECEIPT")
                row.update(status=r["status"], accounting=r["accounting"])
                if r["status"] == "OK":
                    if r["accounting"] != {"read_bytes": PAYLOAD, "decoded_bytes": PAYLOAD}:
                        raise ValueError("STOP_SUCCESS_ACCOUNTING")
                    if (set(r) != {"map", "status", "accounting", "summaries"} or len(r["summaries"]) != 10
                            or [(s["label"], s["kind"]) for s in r["summaries"]] != [(a, b) for a in LABELS for b in KINDS]):
                        raise ValueError("STOP_REGION_DENOMINATOR")
                    if recompute:
                        state = validation["maps"][n - 1]
                        state["status"] = validation["status"] = "ATTEMPTED"
                        try:
                            expected = measure(item, state["accounting"], replay_accounting)
                            if r["summaries"] != expected or state["accounting"] != r["accounting"]:
                                raise ValueError("STOP_SUMMARY_REPLAY")
                        except Exception:
                            state["status"] = validation["status"] = "FAILED"
                            raise
                        state["status"] = "COMPLETED"
                elif (set(r) != {"map", "status", "accounting", "error_type", "error_code"}
                      or not isinstance(r["error_type"], str) or not r["error_type"].isidentifier()
                      or (r["error_code"] is not None and (not isinstance(r["error_code"], str)
                          or re.fullmatch(r"STOP_[A-Z0-9_]+", r["error_code"]) is None))):
                    raise ValueError("STOP_FAILED_RECEIPT")
        elif receipt.exists():
            raise ValueError("STOP_ORPHAN_RECEIPT")
        rows.append(row)
        stopped = stopped or row["status"] != "OK"
    allowed = {f"map-{n}-{suffix}.json" for n in (1, 2) for suffix in ("start", "result")}
    if any(p.name not in allowed for p in HERE.glob("map-*.json")):
        raise ValueError("STOP_EXTRA_MAP_ARTIFACT")
    if recompute and validation["status"] == "ATTEMPTED":
        validation["status"] = "COMPLETED_ELIGIBLE_RECEIPTS"
    return rows, replay_accounting


def aggregate(rows):
    if any(r["accounting"] is None for r in rows):
        return None
    return {k: sum(r["accounting"][k] for r in rows) for k in zero()}


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result, total = {"status": "STOP"}, zero()
    try:
        verify_binding()
        C.save("worker-start.json", {"binding_sha256": C.sha(HERE / "run-start.json")})
        verify_prior()
        for item in MAPS:
            n, a = item["map"], zero()
            C.save(f"map-{n}-start.json", {"map": n, "elapsed_seconds": time.monotonic() - began})
            try:
                summaries = measure(item, a, total)
                C.save(f"map-{n}-result.json", {"map": n, "status": "OK", "accounting": a, "summaries": summaries})
            except Exception as error:
                C.save(f"map-{n}-result.json", {"map": n, "status": "STOP", "accounting": a, **O.failure(error)}, terminal=True)
                raise
        C.checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Map worker stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error))
    finally:
        C.DEADLINE = None
        try:
            rows, _ = ledger()
        except Exception:
            LOGGER.exception("Map ledger incomplete", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
            rows = fallback()
            result.update(status="STOP", error_code="STOP_LEDGER_UNVERIFIED")
        result.update(ledger=rows, accounting=total, artifacts=artifacts(),
                      resource_usage=C.resource_usage(exclude=("worker-result.json", "outcome.json")))
        C.save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code, validation=None):
    validation = validation_state() if validation is None else validation
    C.DEADLINE = time.monotonic() + SECONDS
    try:
        verify_binding()
        verify_prior()
        rows, additional = ledger(recompute=True, validation=validation)
        w = C.read("worker-result.json") if (HERE / "worker-result.json").exists() else None
        if w and (w["ledger"] != rows or w["artifacts"] != artifacts(("worker-result.json", "outcome.json"))
                  or w["resource_usage"] != C.resource_usage(exclude=("worker-result.json", "outcome.json"))
                  or type(w["peak_memory_bytes"]) is not int or w["peak_memory_bytes"] <= 0
                  or w["accounting"] != aggregate(rows)):
            raise ValueError("STOP_WORKER_CLOSURE")
        success = code == 0 and w is not None and w["status"] == PASS
        if success and (any(r["status"] != "OK" for r in rows) or w["peak_memory_bytes"] > C.MEMORY_CAP
                        or C.read("worker-start.json") != {"binding_sha256": C.sha(HERE / "run-start.json")}):
            raise ValueError("STOP_FALSE_SUCCESS")
        C.checkpoint()
        return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
                "worker_accounting": aggregate(rows), "additional_validation_pass_accounting": additional,
                "validation_pass": validation,
                "worker_peak_memory_bytes": w["peak_memory_bytes"] if w else None,
                "worker_error_code": w.get("error_code") if w else None,
                "resource_usage": C.resource_usage(exclude=("outcome.json",)), "planned_regions": 20,
                "summarized_regions": sum(10 for r in rows if r["status"] == "OK"),
                "absolute_coordinates_or_wcs_persisted": False, "MOS2": "UNAVAILABLE"}
    finally:
        C.DEADLINE = None


def run():
    if artifacts():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    validation = validation_state()
    try:
        C.save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c5_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code, validation))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("Map parent stopped", exc_info=(RuntimeError, RuntimeError("Safe receipt only"), None))
        result.update(O.failure(error), ledger=fallback(), worker_accounting=None,
                      additional_validation_pass_accounting=validation["accounting"], validation_pass=validation)
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
    validate_validation(outcome["validation_pass"])
    if outcome["additional_validation_pass_accounting"] != outcome["validation_pass"]["accounting"]:
        raise ValueError("STOP_VALIDATION_ACCOUNTING")
    if outcome["assessment_completed"] is False:
        if outcome["status"] != "STOP" or outcome["ledger"] != fallback():
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; numerical summaries and interrupted read counts unverified")
        return
    validation = validation_state()
    try:
        expected = assess(outcome["worker_returncode"], validation)
        if peak > C.MEMORY_CAP:
            expected["status"] = "STOP"
        if any(outcome.get(k) != v for k, v in expected.items()):
            raise ValueError("STOP_OUTCOME_REPLAY")
    except Exception:
        # Read-only replay cannot alter the original terminal receipt. Its safe
        # structured console receipt retains this extra pass even when it fails.
        print("STOP_OFFLINE_REPLAY_PASS", json.dumps(validation, allow_nan=False))
        raise
    print("PASS_OFFLINE_REPLAY", expected["status"], json.dumps(expected["additional_validation_pass_accounting"]))


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
        LOGGER.exception("Map command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
