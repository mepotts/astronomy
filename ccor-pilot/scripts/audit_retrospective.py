"""Separate, header-only preflight. This cannot promote a recovery experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = (
    "ISVIABLE",
    "ISNORMAL",
    "DCMPRS_Q",
    "IMGBLK_Q",
    "EPVALID",
    "ATTVALID",
    "SUNPNT_Q",
    "TMTIME_Q",
    "ADCS_Q",
    "EPTIME_Q",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def first_two_headers(data: bytes) -> list[bytes]:
    """Read FITS cards, never the compressed image payload. Primary must be empty."""
    result = []
    offset = 0
    for index in range(2):
        start = offset
        while True:
            if offset + 80 > len(data):
                raise ValueError("Truncated FITS header")
            card = data[offset : offset + 80]
            card.decode("ascii")
            offset += 80
            if card[:8] == b"END     ":
                break
        end = ((offset + 2879) // 2880) * 2880
        if end > len(data):
            raise ValueError("Truncated FITS header padding")
        header = data[start:end]
        if index == 0:
            cards = [header[i : i + 80] for i in range(0, len(header), 80)]
            axes = [c[10:30].strip() for c in cards if c[:8] == b"NAXIS   "]
            if axes != [b"0"]:
                raise ValueError("Primary data are not empty")
        result.append(header)
        offset = end
    return result


def assess(header: dict) -> dict:
    missing = [key for key in FLAGS if key not in header]
    not_true = [key for key in FLAGS if key in header and header[key] is not True]
    position = [header.get(key) for key in ("HEEX_OBS", "HEEY_OBS", "HEEZ_OBS")]
    distance = header.get("DSUN_OBS")
    ratio = None
    if all(isinstance(x, (int, float)) and math.isfinite(x) for x in position):
        norm = math.hypot(*position)
        if norm > 0 and isinstance(distance, (int, float)) and math.isfinite(distance):
            ratio = distance / norm
    return {
        "missing_documented_flags": missing,
        "flags_not_boolean_true": not_true,
        "quality_counts": {key: header.get(key) for key in ("BADBLK_N", "MISBLK_N")},
        "wcs_a_types": [header.get("CTYPE1A"), header.get("CTYPE2A")],
        "wcs_b_types": [header.get("CTYPE1B"), header.get("CTYPE2B")],
        "celestial_reference_metadata": {
            key: header.get(key)
            for key in ("RADESYS", "RADESYSA", "EQUINOX", "EQUINOXA")
        },
        "dsun_m_divided_by_hee_numeric_norm": ratio,
        "observer_units_consistent_if_both_meters": ratio is not None
        and abs(ratio - 1) < 0.01,
        "star_calibration_metadata": {
            key: header.get(key)
            for key in ("SCALDATE", "SCALDOF", "STARERR", "NSTARS", "WCSUPDT")
        },
        "measurement_authorized": False,
    }


def collect() -> dict:
    # Astropy is only used to parse header cards; no image HDU or data access.
    from astropy.io import fits

    raw = ROOT / "data/raw/unblock-20260906"
    ledger = json.loads((raw / "ledger.json").read_text(encoding="utf-8-sig"))
    records = []
    for record in ledger["records"]:
        if not record["file"].endswith(".prefix"):
            continue
        data = (raw / record["file"]).read_bytes()
        if len(data) != 65536 or digest(data) != record["sha256"]:
            raise ValueError("Prefix identity mismatch")
        cards = first_two_headers(data)
        headers = [fits.Header.fromstring(h.decode("ascii")) for h in cards]
        parsed = [
            {key: h[key] for key in h if key not in ("COMMENT", "HISTORY", "")}
            for h in headers
        ]
        records.append(
            {
                "acquisition": record,
                "header_cards_ascii": [h.decode("ascii") for h in cards],
                "header_sha256": [digest(h) for h in cards],
                "headers": parsed,
                "assessment": assess(parsed[1]),
            }
        )
    return {
        "purpose": "Retrospective header-only preflight; not a rerun of the frozen pilot",
        "images_decompressed": 0,
        "image_prefix_bytes_received": 4 * 65536,
        "collect_script_sha256": digest(Path(__file__).read_bytes()),
        "acquisition_ledger": ledger,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Read ignored header prefixes; refuse to overwrite evidence",
    )
    args = parser.parse_args()
    path = ROOT / "results/retrospective-preflight-20260906.json"
    if args.collect:
        if path.exists():
            raise ValueError("Refusing to overwrite preflight evidence")
        result = collect()
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    else:
        result = json.loads(path.read_text(encoding="utf-8"))
    for record in result["records"]:
        if record["assessment"] != assess(record["headers"][1]):
            raise ValueError("Assessment replay differs")
        for cards, expected in zip(
            record["header_cards_ascii"], record["header_sha256"], strict=True
        ):
            if digest(cards.encode("ascii")) != expected:
                raise ValueError("Header cards differ")
        print(record["acquisition"]["file"], json.dumps(record["assessment"]))


if __name__ == "__main__":
    main()
