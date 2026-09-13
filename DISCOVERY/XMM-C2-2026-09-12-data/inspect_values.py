"""Frozen-scope offline ancillary values; never decode photon or other arrays."""

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import itertools
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
PROTOCOL = HERE.parent / "XMM-C2-2026-09-12.md"
C1_PATH = HERE.parent / "XMM-C1-2026-09-12-data/acquire.py"
C1_HASH = "13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5"
C1_OUTCOME = "c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc"
SECONDS, MEMORY_CAP, JSON_CAP, RESERVE = 120, 500000000, 1048576, 65536
PAYLOAD_CAP, GTI_BYTES, EXPOSU_BYTES, CHUNK_ROWS = 97029016, 13328, 97015688, 100000
PASS = "ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED"
IDENTITIES = (("EPN", "S003", tuple(range(1, 13))),
              ("EMOS1", "S001", (1, 2, 4, 5, 7)), ("EMOS2", "S002", tuple(range(1, 8))))
DEADLINE, PEAK = None, 0
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

    spec = importlib.util.spec_from_file_location("c2_c1", C1_PATH, loader=VerifiedLoader("c2_c1", str(C1_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_c1()


def checkpoint():
    global PEAK
    PEAK = max(PEAK, C.peak_memory())
    if PEAK > MEMORY_CAP:
        raise ValueError("STOP_PEAK_MEMORY")
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise ValueError("STOP_TOTAL_DEADLINE")


def sha(path, monitor=True):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
            if monitor:
                checkpoint()
    return digest.hexdigest()


def read(name):
    return json.loads((HERE / name).read_bytes())


def usage(exclude=()):
    return sum(p.stat().st_size for p in HERE.glob("*.json") if p.name not in exclude)


def failure(error):
    code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"STOP_[A-Z0-9_]+", str(error)) else "STOP_INTERNAL"
    return {"status": "STOP", "error_code": code}


def save(name, result, terminal=False, peak_key=None):
    global PEAK
    raw = (json.dumps(result, allow_nan=False, sort_keys=True) + "\n").encode()
    if peak_key:
        # Final reporting must survive a lifetime high-water mark above the cap.
        for _ in range(2):
            PEAK = max(PEAK, C.peak_memory())
            result[peak_key] = PEAK
            if PEAK > MEMORY_CAP:
                result.update(status="STOP", error_code="STOP_PEAK_MEMORY")
            raw = (json.dumps(result, allow_nan=False, sort_keys=True) + "\n").encode()
    if usage() + len(raw) > JSON_CAP - (0 if terminal else RESERVE):
        raise ValueError("STOP_JSON_BUDGET")
    with (HERE / name).open("xb") as stream:
        stream.write(raw)


def header(record):
    with warnings.catch_warnings(record=True) as caught:
        result = Header.fromstring("".join(record["cards"]))
        # Only required metadata are exposed; duplicate semantic/layout keys stop.
        keys = [k for k in result if k not in ("", "HISTORY", "COMMENT")]
        if len(keys) != len(set(keys)) or caught:
            raise ValueError("STOP_HEADER_AMBIGUITY")
    return result


def metadata(h):
    return {k: h.get(k) for k in ("ONTIME", "LIVETIME", "EXPOSURE", "TIMEDEL", "SETDEADT",
                                  "TSTART", "TSTOP", "CCDID", "TIMESYS", "TIMEUNIT", "MJDREF", "TIMEZERO")}


def manifest():
    """Headers-only: hashes header JSON, never opens any scientific product."""
    outcome_path = C1_PATH.with_name("outcome.json")
    if sha(outcome_path) != C1_OUTCOME:
        raise ValueError("STOP_C1_OUTCOME_HASH")
    outcome = json.loads(outcome_path.read_bytes())
    if outcome["status"] != C.PASS or outcome["worker_returncode"] != 0:
        raise ValueError("STOP_C1_NOT_SUCCESS")
    tables = []
    for slot, (instrument, exposure, suffixes) in enumerate(IDENTITIES, 1):
        name = f"headers/slot-{slot}-headers.json"
        path = C1_PATH.parent / name
        if sha(path) != outcome["artifacts"][name]:
            raise ValueError("STOP_C1_HEADER_HASH")
        report = json.loads(path.read_bytes())
        hdus = report["hdus"]
        event = header(next(h for h in hdus if h["extname"] == "EVENTS"))
        if (event.get("OBS_ID"), event.get("INSTRUME"), event.get("EXPIDSTR")) != ("0884250101", instrument, exposure):
            raise ValueError("STOP_CAMERA_EXPOSURE")
        expected_dss = {"DSTYP1": "CCDNR", "DSTYP2": "TIME", "DSVAL2": "TABLE"}
        for ordinal, ccd in enumerate(suffixes, 1):
            prefix = "" if ordinal == 1 else str(ordinal)
            expected_dss.update({f"{prefix}DSVAL1": str(ccd), f"{prefix}DSREF2": f":STDGTI{ccd:02d}"})
        actual_dss = {k: event[k] for k in event if re.fullmatch(r"\d*(DSTYP|DSVAL|DSREF)[12]", k)}
        if actual_dss != expected_dss:
            raise ValueError("STOP_CCD_GTI_MAPPING")
        selected = [h for h in hdus if str(h["extname"]).startswith(("STDGTI", "EXPOSU"))]
        expected_names = {f"{kind}{ccd:02d}" for kind in ("STDGTI", "EXPOSU") for ccd in suffixes}
        if len(selected) != len(expected_names) or {h["extname"] for h in selected} != expected_names:
            raise ValueError("STOP_SUFFIX_SET")
        product = json.loads(C1_PATH.with_name(f"slot-{slot}-result.json").read_bytes())
        filename = product["slot"]["filename"][:-4] + ".fits"
        for record in sorted(selected, key=lambda h: (not h["extname"].startswith("STDGTI"), h["extname"])):
            h = header(record)
            kind, ccd = record["extname"][:-2], int(record["extname"][-2:])
            # MOS GTI headers have no instrument/exposure cards; their identity is
            # the hash-bound parent product plus the explicit EVENTS DSS mapping.
            if any(h[k] != v for k, v in (("INSTRUME", instrument), ("EXPIDSTR", exposure)) if k in h):
                raise ValueError("STOP_TABLE_IDENTITY")
            if (h.get("TIMESYS"), h.get("TIMEUNIT"), h.get("MJDREF"), h.get("TIMEZERO")) != ("TT", "s", 50814.0, 0):
                raise ValueError("STOP_TIME_SCHEMA")
            columns = [("START", "D", "s"), ("STOP", "D", "s")] if kind == "STDGTI" else (
                [("TIME", "D", "s"), ("FRACEXP", "E", "fraction")] if slot == 1 else
                [("TIME", "D", "s"), ("TIMEDEL", "E", "s"), ("FRACEXP", "E", "fraction")])
            width = sum(8 if form == "D" else 4 for _, form, _ in columns)
            if (h.get("XTENSION"), h.get("BITPIX"), h.get("NAXIS"), h.get("NAXIS1"), h.get("TFIELDS"),
                h.get("PCOUNT"), h.get("GCOUNT")) != ("BINTABLE", 8, 2, width, len(columns), 0, 1):
                raise ValueError("STOP_TABLE_LAYOUT")
            if any(re.match(r"(TSCAL|TZERO|TNULL|TDIM)\d+$", k) or k == "THEAP" for k in h):
                raise ValueError("STOP_SCALING_NULL_OR_HEAP")
            for i, (col, form, unit) in enumerate(columns, 1):
                if (h.get(f"TTYPE{i}"), h.get(f"TFORM{i}"), str(h.get(f"TUNIT{i}")).lower()) != (col, form, unit):
                    raise ValueError("STOP_COLUMN_SCHEMA")
            rows = h.get("NAXIS2")
            if type(rows) is not int or rows < 0 or record["data_bytes"] != rows * width:
                raise ValueError("STOP_ROW_BYTES")
            if kind == "EXPOSU" and slot == 1 and type(h.get("TIMEDEL")) not in (int, float):
                raise ValueError("STOP_PN_WIDTH_HEADER")
            tables.append({"table": len(tables) + 1, "slot": slot, "instrument": instrument, "exposure": exposure,
                           "ccdnr": ccd, "kind": kind, "extname": record["extname"], "filename": filename,
                           "file_bytes": report["file_bytes"], "file_sha256": product["expanded"]["sha256"],
                           "header_sha256": outcome["artifacts"][name], "data_offset": record["data_offset"],
                           "data_bytes": record["data_bytes"], "rows": rows, "width": width,
                           "columns": [list(column) for column in columns], "header_metadata": metadata(h), "events_metadata": metadata(event),
                           "events_ccd_livetime": event.get(f"LIVETI{ccd:02d}"), "dss_mapping": expected_dss})
    if (len(tables) != 48 or sum(t["data_bytes"] for t in tables if t["kind"] == "STDGTI") != GTI_BYTES
            or sum(t["data_bytes"] for t in tables if t["kind"] == "EXPOSU") != EXPOSU_BYTES):
        raise ValueError("STOP_EXACT_PAYLOAD_SET")
    return tables


def binding(protocol):
    import astropy

    return {"tables": manifest(), "source_sha256": sha(SOURCE), "tests_sha256": sha(HERE / "test_inspect_values.py"),
            "protocol_sha256": sha(protocol), "c1_source_sha256": C1_HASH, "c1_outcome_sha256": C1_OUTCOME,
            "helper_sha256": sha(C.HELPER), "runtime": {"python": sys.version, "numpy": np.__version__,
             "astropy": astropy.__version__, "executable": str(Path(sys.executable).resolve())},
            "caps": {"seconds": SECONDS, "memory": MEMORY_CAP, "json": JSON_CAP,
                     "payload": PAYLOAD_CAP, "chunk_rows": CHUNK_ROWS}}


def verify_binding():
    if read("run-start.json") != binding(HERE / "protocol.snapshot.md") or sha(C.HELPER) != C.HELPER_HASH:
        raise ValueError("STOP_BINDING")


def verify_c1():
    if sha(C1_PATH.with_name("outcome.json")) != C1_OUTCOME:
        raise ValueError("STOP_C1_OUTCOME_HASH")
    # Frozen C1 replay hashes raw/expanded inputs and rechecks headers only.
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True):
        C.replay()
    checkpoint()


def chunks(stream, table, accounting):
    if table["kind"] not in ("STDGTI", "EXPOSU") or table["extname"] != f"{table['kind']}{table['ccdnr']:02d}":
        raise ValueError("STOP_FORBIDDEN_ARRAY")
    dtype = np.dtype([(col, ">f8" if form == "D" else ">f4") for col, form, _ in table["columns"]])
    if dtype.itemsize != table["width"] or table["rows"] * dtype.itemsize != table["data_bytes"]:
        raise ValueError("STOP_READ_SCHEMA")
    if not 0 <= table["data_offset"] <= table["data_offset"] + table["data_bytes"] <= table["file_bytes"]:
        raise ValueError("STOP_READ_SPAN")
    stream.seek(table["data_offset"])
    for start in range(0, table["rows"], CHUNK_ROWS):
        checkpoint()
        size = min(CHUNK_ROWS, table["rows"] - start) * dtype.itemsize
        if accounting["interpreted_bytes"] + size > PAYLOAD_CAP:
            raise ValueError("STOP_PAYLOAD_CAP")
        raw = stream.read(size)
        accounting["read_bytes"] += len(raw)
        if len(raw) != size:
            raise ValueError("STOP_TRUNCATED_TABLE")
        accounting["interpreted_bytes"] += size
        yield np.frombuffer(raw, dtype=dtype)


def number(value):
    return float(value) if np.isfinite(value) else None


def gti_summary(blocks):
    # This fixed stage has only 833 GTI rows total; no exposure arrays accumulate.
    rows = [(float(a), float(b)) for block in blocks for a, b in zip(block["START"], block["STOP"], strict=True)]
    valid = [(a, b) for a, b in rows if math.isfinite(a) and math.isfinite(b) and b > a]
    union, overlap = [], 0
    for a, b in sorted(valid):
        if union and a < union[-1][1]:
            overlap += 1
        if union and a <= union[-1][1]:
            union[-1][1] = max(union[-1][1], b)
        else:
            union.append([a, b])
    finite = sum(math.isfinite(a) and math.isfinite(b) for a, b in rows)
    result = {"rows": len(rows), "finite_endpoint_rows": finite, "valid_positive_rows": len(valid),
              "nonfinite_rows": len(rows) - finite, "nonpositive_finite_rows": finite - len(valid),
              "nonincreasing_start_adjacent_finite_pairs": sum(a2 <= a1 for (a1, _), (a2, _) in itertools.pairwise(rows)
                                                             if math.isfinite(a1) and math.isfinite(a2)),
              "overlap_rows_in_sorted_valid_intervals": overlap, "valid_union_intervals": len(union),
              "valid_rows_only_union_duration": math.fsum(b - a for a, b in union),
              "first_start": number(rows[0][0]) if rows else None, "last_stop": number(rows[-1][1]) if rows else None,
              "valid_union_start": union[0][0] if union else None, "valid_union_stop": union[-1][1] if union else None}
    result["data_quality_flags"] = [k for k in ("nonfinite_rows", "nonpositive_finite_rows",
        "nonincreasing_start_adjacent_finite_pairs", "overlap_rows_in_sorted_valid_intervals") if result[k]]
    return result, union


def exposure_summary(blocks, table, union):
    result = {k: 0 for k in ("rows", "finite_times", "finite_widths", "finite_fractions", "nonpositive_finite_widths",
              "fractions_outside_unit_interval", "valid_rows", "gti_member_valid_rows", "nonincreasing_adjacent_finite_times",
              "adjacent_duplicate_finite_times")}
    extrema = {k: [] for k in ("width", "fraction", "spacing")}
    sums = {k: [] for k in ("valid_width_sum", "valid_fraction_weighted_width_sum", "gti_member_valid_width_sum",
                           "gti_member_valid_fraction_weighted_width_sum")}
    seen, previous, first, last = set(), None, None, None
    for block in blocks:
        t, f = block["TIME"].astype(float), block["FRACEXP"].astype(float)
        w = (np.full(len(t), table["header_metadata"]["TIMEDEL"], dtype=float) if table["slot"] == 1
             else block["TIMEDEL"].astype(float))
        ft, fw, ff = np.isfinite(t), np.isfinite(w), np.isfinite(f)
        valid = ft & fw & ff & (w > 0) & (f >= 0) & (f <= 1)
        member = np.zeros(len(t), dtype=bool)
        for a, b in union:
            member |= (t >= a) & (t < b)
        member &= valid
        if result["rows"] == 0:
            first = number(t[0])
        last = number(t[-1])
        pairs = np.concatenate(([previous], t)) if previous is not None else t
        d = np.diff(pairs)
        fd = np.isfinite(pairs[:-1]) & np.isfinite(pairs[1:])
        result["nonincreasing_adjacent_finite_times"] += int(np.count_nonzero(fd & (d <= 0)))
        result["adjacent_duplicate_finite_times"] += int(np.count_nonzero(fd & (d == 0)))
        previous = float(t[-1])
        seen.update(t[ft].tolist())
        for key, values in (("width", w[fw]), ("fraction", f[ff]), ("spacing", d[fd])):
            if len(values):
                extrema[key].append((float(np.min(values)), float(np.max(values))))
        for key, mask in (("finite_times", ft), ("finite_widths", fw), ("finite_fractions", ff),
                          ("nonpositive_finite_widths", fw & (w <= 0)),
                          ("fractions_outside_unit_interval", ff & ((f < 0) | (f > 1))),
                          ("valid_rows", valid), ("gti_member_valid_rows", member)):
            result[key] += int(np.count_nonzero(mask))
        result["rows"] += len(t)
        for prefix, mask in (("valid", valid), ("gti_member_valid", member)):
            sums[f"{prefix}_width_sum"].append(float(np.sum(w[mask], dtype=np.float64)))
            sums[f"{prefix}_fraction_weighted_width_sum"].append(float(np.sum(w[mask] * f[mask], dtype=np.float64)))
        checkpoint()
    result.update({k: math.fsum(v) for k, v in sums.items()})
    result.update(first_time=first, last_time=last, global_duplicate_finite_times=result["finite_times"] - len(seen))
    for key, values in extrema.items():
        result[f"min_{key}"] = min(a for a, _ in values) if values else None
        result[f"max_{key}"] = max(b for _, b in values) if values else None
    result["data_quality_flags"] = [k for k in ("nonpositive_finite_widths", "fractions_outside_unit_interval",
        "nonincreasing_adjacent_finite_times", "global_duplicate_finite_times") if result[k]]
    result["data_quality_flags"] += [f"nonfinite_{k}" for k in ("times", "widths", "fractions")
                                     if result[f"finite_{k}"] != result["rows"]]
    result["valid_row_definition"] = "finite TIME,width,FRACEXP; width>0; 0<=FRACEXP<=1"
    result["membership_definition"] = "valid row timestamp in valid GTI union; START<=TIME<STOP; not frame integration"
    benchmarks = {f"table_{k}": table["header_metadata"][k] for k in ("ONTIME", "LIVETIME", "EXPOSURE")}
    benchmarks.update(events_ccd_livetime=table["events_ccd_livetime"],
                      valid_gti_union_duration=math.fsum(b - a for a, b in union))
    result["arithmetic_minus_metadata"] = {key: {k: value - v for k, v in benchmarks.items()
        if isinstance(v, (int, float)) and math.isfinite(v)} for key, value in result.items()
        if key in sums}
    result["semantic_status"] = "DESCRIPTIVE_UNCALIBRATED_NO_DEADTIME_RESCALE"
    return result


def measure(table, unions, accounting):
    with (C1_PATH.parent / "products" / table["filename"]).open("rb") as stream:
        blocks = chunks(stream, table, accounting)
        key = (table["slot"], table["ccdnr"])
        if table["kind"] == "STDGTI":
            summary, unions[key] = gti_summary(blocks)
        else:
            summary = exposure_summary(blocks, table, unions[key])
    if summary["rows"] != table["rows"]:
        raise ValueError("STOP_ROW_ACCOUNTING")
    return summary


def artifact_hashes(exclude=()):
    return {p.name: sha(p, monitor=False) for p in HERE.glob("*.json") if p.name not in exclude}


def ledger(tables, recompute=False):
    rows, stopped, unions, accounting = [], False, {}, {"read_bytes": 0, "interpreted_bytes": 0}
    previous = -1
    for table in tables:
        n = table["table"]
        marker, receipt = HERE / f"table-{n}-start.json", HERE / f"table-{n}-result.json"
        row = {"table": n, "status": "NOT_ATTEMPTED"}
        if marker.exists():
            mark = read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or mark.get("table") != n or type(elapsed) not in (float, int)
                    or not math.isfinite(elapsed) or not previous <= elapsed < SECONDS):
                raise ValueError("STOP_TABLE_ORDER")
            previous = elapsed
            row["status"] = "INTERRUPTED"
            if receipt.exists():
                result = read(receipt.name)
                if result.get("table") != n or result.get("status") not in ("OK", "STOP"):
                    raise ValueError("STOP_TABLE_RECEIPT")
                if recompute and result["status"] == "OK":
                    before = accounting["interpreted_bytes"]
                    summary = measure(table, unions, accounting)
                    expected = {"table": n, "status": "OK", "summary": summary,
                                "interpreted_bytes": accounting["interpreted_bytes"] - before}
                    if result != expected:
                        raise ValueError("STOP_SUMMARY_REPLAY")
                row.update(status=result["status"], interpreted_bytes=result.get("interpreted_bytes", 0))
        elif receipt.exists():
            raise ValueError("STOP_ORPHAN_RECEIPT")
        stopped = stopped or row["status"] != "OK"
        rows.append(row)
    if len(list(HERE.glob("table-*-start.json"))) != sum(r["status"] != "NOT_ATTEMPTED" for r in rows):
        raise ValueError("STOP_EXTRA_TABLE")
    return rows


def worker():
    global DEADLINE
    began = time.monotonic()
    DEADLINE = began + SECONDS
    result, accounting = {"status": "STOP"}, {"read_bytes": 0, "interpreted_bytes": 0}
    tables = read("run-start.json")["tables"]
    try:
        verify_binding()
        save("worker-start.json", {"binding_sha256": sha(HERE / "run-start.json")})
        verify_c1()
        unions = {}
        for table in tables:
            checkpoint()
            n = table["table"]
            save(f"table-{n}-start.json", {"table": n, "elapsed_seconds": time.monotonic() - began})
            before = accounting["interpreted_bytes"]
            try:
                summary = measure(table, unions, accounting)
                save(f"table-{n}-result.json", {"table": n, "status": "OK", "summary": summary,
                                               "interpreted_bytes": accounting["interpreted_bytes"] - before})
            except Exception as error:
                save(f"table-{n}-result.json", {"table": n, **failure(error),
                                               "interpreted_bytes": accounting["interpreted_bytes"] - before}, terminal=True)
                raise
        if accounting != {"read_bytes": PAYLOAD_CAP, "interpreted_bytes": PAYLOAD_CAP}:
            raise ValueError("STOP_FINAL_BYTE_ACCOUNTING")
        checkpoint()
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Ancillary worker stopped", exc_info=(RuntimeError, RuntimeError("Details withheld; safe receipt only"), None))
        result.update(failure(error))
    finally:
        DEADLINE = None
        result.update(ledger=ledger(tables), accounting=accounting, json_bytes_before_worker_result=usage(),
                      artifacts=artifact_hashes())
        save("worker-result.json", result, terminal=True, peak_key="peak_memory_bytes")
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    verify_c1()
    rows = ledger(read("run-start.json")["tables"], recompute=True)
    worker = read("worker-result.json") if (HERE / "worker-result.json").exists() else None
    success = code == 0 and worker is not None and worker["status"] == PASS
    if worker:
        if (worker["ledger"] != rows or worker["artifacts"] != artifact_hashes(("worker-result.json", "outcome.json"))
                or worker["json_bytes_before_worker_result"] != usage(("worker-result.json", "outcome.json"))
                or type(worker["peak_memory_bytes"]) is not int or worker["peak_memory_bytes"] <= 0):
            raise ValueError("STOP_WORKER_CLOSURE")
        completed = sum(r.get("interpreted_bytes", 0) for r in rows)
        a = worker["accounting"]
        if (set(a) != {"read_bytes", "interpreted_bytes"} or any(type(v) is not int for v in a.values())
                or not 0 <= completed == a["interpreted_bytes"] <= a["read_bytes"] <= PAYLOAD_CAP):
            raise ValueError("STOP_ACCOUNTING_RECEIPT")
    if success and (any(r["status"] != "OK" for r in rows) or worker["peak_memory_bytes"] > MEMORY_CAP
                    or worker["accounting"] != {"read_bytes": PAYLOAD_CAP, "interpreted_bytes": PAYLOAD_CAP}
                    or read("worker-start.json") != {"binding_sha256": sha(HERE / "run-start.json")}):
        raise ValueError("STOP_FALSE_SUCCESS")
    return {"status": PASS if success else "STOP", "worker_returncode": code, "ledger": rows,
            "worker_peak_memory_bytes": worker["peak_memory_bytes"] if worker else None,
            "worker_error_code": worker.get("error_code") if worker else None,
            "json_bytes_before_outcome": usage(("outcome.json",)), "photons_interpreted": False}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "assessment_completed": False}
    try:
        checkpoint()
        start = binding(PROTOCOL)
        save("run-start.json", start)
        with (HERE / "protocol.snapshot.md").open("xb") as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned("c2_deadline", C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
        result["assessment_completed"] = True
    except Exception as error:
        LOGGER.exception("Ancillary parent stopped", exc_info=(RuntimeError, RuntimeError("Details withheld; safe receipt only"), None))
        result.update(failure(error))
        # A killed worker may leave truncated JSON. Do not parse it again while
        # trying to persist the authoritative failure and all planned slots.
        result["ledger"] = fallback_ledger()
    finally:
        result["artifacts"] = artifact_hashes(("outcome.json",))
        result["source_sha256"] = sha(SOURCE, monitor=False)
        result["snapshot_sha256"] = sha(HERE / "protocol.snapshot.md", monitor=False) if (HERE / "protocol.snapshot.md").exists() else None
        save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
    print(result["status"])
    return 0 if result["status"] == PASS else 1


def fallback_ledger():
    return [{"table": n, "status": "UNVERIFIED_ATTEMPT" if
             (HERE / f"table-{n}-start.json").exists() or (HERE / f"table-{n}-result.json").exists()
             else "NOT_ATTEMPTED"} for n in range(1, 49)]


def replay():
    outcome = read("outcome.json")
    snapshot = HERE / "protocol.snapshot.md"
    if (outcome["artifacts"] != artifact_hashes(("outcome.json",)) or outcome["source_sha256"] != sha(SOURCE)
            or outcome["snapshot_sha256"] != (sha(snapshot) if snapshot.exists() else None)):
        raise ValueError("STOP_OUTCOME_ARTIFACTS")
    peak = outcome.get("parent_peak_memory_bytes")
    if type(peak) is not int or peak <= 0 or (peak > MEMORY_CAP and
            (outcome["status"] != "STOP" or outcome.get("error_code") != "STOP_PEAK_MEMORY")):
        raise ValueError("STOP_PARENT_MEMORY_RECEIPT")
    if outcome.get("assessment_completed") is False:
        if (outcome["status"] != "STOP" or outcome["ledger"] != fallback_ledger()
                or not re.fullmatch(r"STOP_[A-Z0-9_]+", outcome.get("error_code", "")) or usage() > JSON_CAP):
            raise ValueError("STOP_FAILURE_ARTIFACT_REPLAY")
        print("PASS_FAILURE_ARTIFACT_REPLAY STOP; summaries remain unverified")
        return
    check = assess(outcome["worker_returncode"])
    if peak > MEMORY_CAP:
        check["status"] = "STOP"
    if any(outcome.get(k) != v for k, v in check.items()) or usage() > JSON_CAP:
        raise ValueError("STOP_OUTCOME_REPLAY")
    print("PASS_OFFLINE_REPLAY", check["status"])


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
        LOGGER.exception("Ancillary command stopped", exc_info=(RuntimeError, RuntimeError("Details withheld; safe code only"), None))
        print(failure(error)["error_code"])
        raise SystemExit(1) from None
