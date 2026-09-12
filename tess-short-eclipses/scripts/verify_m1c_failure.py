"""Read-only replay of M1c's stopped parser outcome, not a catalog parity pass."""

import ctypes
import importlib.util
import json
import struct
from pathlib import Path

from astropy.io.votable.converters import fast_binparse_long

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1c_failure_replay", ROOT / "scripts/m1c.py")
m1c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1c)
RESPONSE_HASH = "17c3c8a22488bb9b40a37d77b47807aa900decc28486e04bc5a48c0739ad2639"


def main():
    m1c.replay()
    response = m1c.DATA / "450781262/gaia-dr3.xml"
    if m1c.m1.sha(response) != RESPONSE_HASH or response.stat().st_size != 100482:
        raise ValueError("STOP_RETAINED_RESPONSE_CHANGED")
    summary = m1c.read_json(ROOT / "out/m1c-summary.json")
    if (summary["parity"] is not None or summary["status"] != "STOP_CATALOG_PARITY"
            or [row["tic"] for row in summary["outcomes"]] != [450781262]):
        raise ValueError("STOP_OUTCOME_CHANGED")
    if any((m1c.DATA / str(tic)).exists() for tic in (53206761, 2041210548)):
        raise ValueError("STOP_UNEXPECTED_LATER_REQUEST")
    failure = m1c.read_json(m1c.DATA / "450781262/failure.json")
    try:
        m1c.strict_catalog(response)
    except OverflowError as error:
        if str(error) != failure["error"] or failure["type"] != "OverflowError":
            raise ValueError("STOP_FAILURE_DIFFERENT") from error
    else:
        raise ValueError("STOP_EXPECTED_PARSER_FAILURE_NOT_REPRODUCED")
    raw = struct.pack(">q", 5346312514819760896)
    if fast_binparse_long(raw, 0, 0, False) != (5346312514819760896, False):
        raise ValueError("STOP_INT64_PROBE")
    try:
        fast_binparse_long(raw, 0, -(2**63), True)
    except OverflowError:
        pass
    else:
        raise ValueError("STOP_NULL_SENTINEL_FAILURE_NOT_REPRODUCED")
    print(json.dumps({"failure_replay": "PASS", "catalog_parity_established": False,
                      "raw_response_sha256": RESPONSE_HASH, "bytes": 100482,
                      "C_long_bytes": ctypes.sizeof(ctypes.c_long), "int64_bytes": struct.calcsize("q"),
                      "requests": 1, "later_requests": 0, "network": False,
                      "unknown_search_authorized": False}))


if __name__ == "__main__":
    main()
