"""Offline, fixed-schema VOTable repair; preserves all M1c bytes and stop rules."""

import argparse
import base64
import binascii
import importlib.util
import json
import logging
import os
import re
import struct
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.table import MaskedColumn, Table

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1d_old", ROOT / "scripts/m1c.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
NS = "{http://www.ivoa.net/xml/VOTable/v1.3}"
NAMES = tuple(OLD.m1b.FIELDS)
TYPES = ("long", "double", "double", "double", "double", "double", "float", "float")
FORMATS = (">i8", ">f8", ">f8", ">f8", ">f8", ">f8", ">f4", ">f4")
ROW = struct.Struct(">qdddddff")
ARI = ROOT / "data/m1c/450781262/gaia-dr3.xml"
ARI_HASH = "17c3c8a22488bb9b40a37d77b47807aa900decc28486e04bc5a48c0739ad2639"
MANIFEST = ROOT / "out/m1d-manifest.json"
RESULT = ROOT / "out/m1d-result.json"
ATTEMPT = ROOT / "out/m1d-attempt.json"
WORKER_START = ROOT / "out/m1d-worker-start.json"
OUTCOME = ROOT / "out/m1d-worker-outcome.json"
LOGGER = logging.getLogger(__name__)


def schema(content):
    if len(content) > 5_000_000 or b"<!DOCTYPE" in content or b"<!ENTITY" in content:
        raise ValueError("STOP_XML_BOUND_OR_DECLARATION")
    text = content.decode("utf-8")
    if "\x00" in text:
        raise ValueError("STOP_XML_ENCODING")
    declaration = re.match(r"\ufeff?<\?xml\s.*?\?>", text, flags=re.DOTALL)
    if declaration:
        encoding = re.search(r"encoding\s*=\s*(['\"])(.*?)\1", declaration.group())
        if encoding and encoding.group(2).lower().replace("-", "") != "utf8":
            raise ValueError("STOP_XML_ENCODING")
    root = ET.fromstring(text)
    if any(not element.tag.startswith(NS) for element in root.iter()):
        raise ValueError("STOP_FOREIGN_NAMESPACE")
    if root.tag != NS + "VOTABLE" or root.get("version") != "1.4":
        raise ValueError("STOP_XML_VERSION")
    resources, tables = root.findall(".//" + NS + "RESOURCE"), root.findall(".//" + NS + "TABLE")
    if len(resources) != 1 or resources[0].get("type") != "results" or len(tables) != 1:
        raise ValueError("STOP_TABLE_STRUCTURE")
    if tables[0] not in list(resources[0]) or resources[0] not in list(root):
        raise ValueError("STOP_TABLE_STRUCTURE")
    statuses = root.findall(".//" + NS + "INFO[@name='QUERY_STATUS']")
    if not statuses or any(item.get("value") != "OK" for item in statuses):
        raise ValueError("STOP_QUERY_STATUS")
    fields = tables[0].findall(NS + "FIELD")
    if len(fields) != 8 or len(root.findall(".//" + NS + "FIELD")) != 8:
        raise ValueError("STOP_FIELDS")
    for field, name, kind in zip(fields, NAMES, TYPES, strict=True):
        if field.get("name") != name or field.get("datatype") != kind or field.get("arraysize") is not None:
            raise ValueError("STOP_SCHEMA")
        if field.get("xtype") is not None:
            raise ValueError("STOP_EXTENDED_TYPE")
    values = fields[0].findall(NS + "VALUES")
    if len(values) != 1 or not re.fullmatch(r"[+-]?[0-9]+", values[0].get("null", "")):
        raise ValueError("STOP_INTEGER_NULL")
    null = int(values[0].get("null"))
    if not -(2**63) <= null < 2**63 or values[0].get("ref") is not None:
        raise ValueError("STOP_INTEGER_NULL")
    if any(field.findall(NS + "VALUES") for field in fields[1:]):
        raise ValueError("STOP_UNSUPPORTED_FLOAT_VALUES")
    data = tables[0].findall(NS + "DATA")
    if (len(data) != 1 or len(root.findall(".//" + NS + "DATA")) != 1
            or len(data[0]) != 1 or data[0][0].tag != NS + "BINARY"):
        raise ValueError("STOP_BINARY_STRUCTURE")
    binary = data[0][0]
    if len(binary) != 1 or binary[0].tag != NS + "STREAM":
        raise ValueError("STOP_STREAM")
    stream = binary[0]
    if stream.attrib != {"encoding": "base64"} or len(stream):
        raise ValueError("STOP_EXTERNAL_OR_UNSUPPORTED_STREAM")
    try:
        encoded = re.sub(rb"[ \t\r\n]", b"", (stream.text or "").encode("ascii"))
        raw = base64.b64decode(encoded, validate=True)
    except (UnicodeError, binascii.Error) as error:
        raise ValueError("STOP_BASE64") from error
    if base64.b64encode(raw) != encoded:
        raise ValueError("STOP_NONCANONICAL_BASE64")
    count, remainder = divmod(len(raw), ROW.size)
    if remainder or not 0 < count < 5001:
        raise ValueError("STOP_ROW_COUNT")
    nrows = tables[0].get("nrows")
    if nrows is not None and (not re.fullmatch(r"[0-9]+", nrows) or int(nrows) != count):
        raise ValueError("STOP_DECLARED_ROWS")
    return raw, fields, null


def decode(content):
    raw, fields, null = schema(content)
    rows = list(ROW.iter_unpack(raw))
    oracle = np.frombuffer(raw, dtype=np.dtype(list(zip(NAMES, FORMATS, strict=True))))
    table = Table(masked=True)
    for index, (name, dtype, field) in enumerate(zip(NAMES, FORMATS, fields, strict=True)):
        # Never build a mixed row ndarray: that would round int64 source IDs.
        values = np.asarray([row[index] for row in rows], dtype=np.dtype(dtype).newbyteorder("="))
        other = oracle[name].astype(values.dtype)
        if values.dtype.kind == "i":
            equal = np.array_equal(values, other)
            mask = values == null
        else:
            equal = (np.array_equal(values, other, equal_nan=True)
                     and np.array_equal(np.signbit(values[values == 0]), np.signbit(other[values == 0])))
            mask = np.isnan(values)
        if not equal:
            raise ValueError("STOP_DECODER_DISAGREEMENT")
        table[name] = MaskedColumn(values, mask=mask, unit=field.get("unit"))
    return table


def validate(table):
    if tuple(table.colnames) != NAMES or not 0 < len(table) < 5001:
        raise ValueError("STOP_CATALOG_SHAPE")
    ids = table["source_id"]
    if (ids.dtype.kind != "i" or ids.dtype.itemsize != 8 or np.any(np.ma.getmaskarray(ids))
            or np.any(ids <= 0) or len(np.unique(np.asarray(ids))) != len(ids)):
        raise ValueError("STOP_CATALOG_IDS")
    for name, expected in OLD.UNITS.items():
        if u.Unit(str(table[name].unit or ""), parse_strict="raise") != expected:
            raise ValueError("STOP_CATALOG_UNITS")
        mask = np.ma.getmaskarray(table[name])
        if name in ("ra", "dec", "ref_epoch") and np.any(mask):
            raise ValueError("STOP_CATALOG_REQUIRED_MASK")
        if not np.all(np.isfinite(np.asarray(table[name])[~mask])):
            raise ValueError("STOP_CATALOG_NONFINITE")
    if np.any((table["ra"] < 0) | (table["ra"] >= 360)) or np.any(np.abs(table["dec"]) > 90):
        raise ValueError("STOP_CATALOG_POSITIONS")
    return table


def dependencies():
    OLD.verify()
    if (OLD.m1.sha(OLD.MANIFEST) != "3c1ae14e1e5c2b4372942089762c4783b5019e185de9e38483b24599562fc149"
            or OLD.m1.sha(ARI) != ARI_HASH):
        raise ValueError("STOP_OLD_PROVENANCE")
    paths = [Path(__file__), ROOT / "tests/test_m1d.py", ROOT / "M1d-PROTOCOL-2026-09-12.md",
             ROOT / "tests/test_m1d_review.py", OLD.MANIFEST, OLD.REFERENCE, ARI,
             ROOT / "out/m1c-summary.json", OLD.m1.RUNNER]
    return {os.path.relpath(path, ROOT).replace("\\", "/"): OLD.m1.sha(path) for path in paths}


def execute():
    manifest = OLD.read_json(MANIFEST)
    if manifest["dependencies"] != dependencies():
        raise ValueError("STOP_MANIFEST_CHANGED")
    result = {"manifest_sha256": OLD.m1.sha(MANIFEST), "network_requests": 0,
              "pixel_recalculation": False, "unknown_search_authorized": False}
    try:
        mirror = validate(decode(ARI.read_bytes()))
        parity = OLD.compare_tables(OLD.strict_catalog(OLD.REFERENCE), mirror)
    except (ValueError, ET.ParseError, OSError) as error:
        result.update(status="STOP_M1D", error_type=type(error).__name__, error=str(error))
    else:
        result.update(status="OFFLINE_CATALOG_PARITY_PASS", parity=parity,
                      numeric_decoders="struct_and_numpy_exact", rows=len(mirror))
    return result


def peak_memory():
    if os.name != "nt":
        raise RuntimeError("Execution memory receipt requires the validated Windows runtime")
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "peak", "working", "quota_peak_paged", "quota_paged",
                "quota_peak_nonpaged", "quota_nonpaged", "pagefile", "peak_pagefile")]
    record = Counters()
    record.cb = ctypes.sizeof(record)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    library = ctypes.WinDLL("psapi", use_last_error=True)
    library.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
    if not library.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(record), record.cb):
        raise RuntimeError("Cannot verify peak memory")
    if record.peak > 1_000_000_000:
        raise RuntimeError(f"STOP_PEAK_MEMORY:{record.peak}")
    return int(record.peak)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "replay"))
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    start = time.monotonic()
    if args.stage == "prepare":
        if args.worker:
            raise ValueError("STOP_WORKER_STAGE")
        OLD.m1.save(MANIFEST, {"dependencies": dependencies(), "scope": "offline_first_field_only",
                              "prepared_utc": datetime.now(timezone.utc).isoformat()})
        return
    if not args.worker:
        if args.stage == "run":
            if RESULT.exists() or OUTCOME.exists() or WORKER_START.exists():
                raise ValueError("STOP_EXISTING_RUN")
            OLD.m1.save(ATTEMPT, {"manifest_sha256": OLD.m1.sha(MANIFEST),
                                 "utc": datetime.now(timezone.utc).isoformat()})
        runner_spec = importlib.util.spec_from_file_location("m1d_deadline", OLD.m1.RUNNER)
        runner = importlib.util.module_from_spec(runner_spec)
        try:
            runner_spec.loader.exec_module(runner)
            code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                               args.stage, "--worker"], 60)
        except Exception:
            LOGGER.exception("M1d worker launch/cleanup failed")
            code, output = 1, traceback.format_exc()
        if args.stage == "run":
            OLD.m1.save(OUTCOME, {"returncode": code, "output": output,
                                 "status": "WORKER_COMPLETED" if code == 0 else "STOP_WORKER",
                                 "unknown_search_authorized": False})
        print(output)
        raise SystemExit(code)
    if args.stage == "run":
        if RESULT.exists() or OLD.read_json(ATTEMPT)["manifest_sha256"] != OLD.m1.sha(MANIFEST):
            raise ValueError("STOP_WORKER_ATTEMPT")
        OLD.m1.save(WORKER_START, {"manifest_sha256": OLD.m1.sha(MANIFEST)})
    peak_memory()
    result = execute()
    peak = peak_memory()
    if time.monotonic() - start > 60 or len(json.dumps(result)) > 1_000_000:
        raise ValueError("STOP_RESOURCE_CAP")
    if args.stage == "replay":
        if OLD.read_json(RESULT) != result:
            raise ValueError("STOP_REPLAY_DIFFERENT")
        print("EXACT_REPLAY_PASS")
    else:
        OLD.m1.save(RESULT, result)
        OLD.m1.save(ROOT / "out/m1d-runtime.json", {"elapsed_seconds": time.monotonic() - start,
                                                  "peak_working_set_bytes": peak})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
