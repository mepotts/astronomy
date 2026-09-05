"""Frozen, fail-closed four-frame CCOR2 pilot; never an unknown-source search."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "CCOR2_1A_20260901T130014_V00_NC.fits",
    "CCOR2_1A_20260901T131514_V00_NC.fits",
    "CCOR2_1A_20260901T133014_V00_NC.fits",
    "CCOR2_1A_20260901T134514_V00_NC.fits",
)
POSITIONS = np.array([[1632, 1400], [1625, 1396], [1622, 1393], [1616, 1389]])
NEGATIVES = np.array(
    [[-64, 0], [64, 0], [0, -64], [0, 64], [-32, -32], [-32, 32], [32, -32], [32, 32]]
)
INJECTION_OFFSET = np.array([64, 64])
CUTOUT = (1520, 1736, 1280, 1496)
TRUE_KEYS = (
    "ISVIABLE",
    "ISNORMAL",
    "DCMPRS_Q",
    "IMGBLK_Q",
    "EPVALID",
    "ATTVALID",
    "SUNPNT_Q",
)

# The report supplies origin and dimensions, but no viewer or processing
# provenance. WCS establishes the FITS orientation, not the reporter's display.
# No CLI flag bypasses this scientific gate. A resolved mapping needs a NEW spec.
REPORT_MAPPING_ESTABLISHED = False


class PilotStop(ValueError):
    """A frozen scientific/input gate failed; this is not negative source truth."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_index(payload: object) -> list:
    """An empty or malformed index is not evidence of successful no-data."""
    if not isinstance(payload, list) or not payload:
        raise PilotStop("STOP_EMPTY_OR_MALFORMED_INDEX")
    return payload


def number(header: dict, key: str) -> float:
    try:
        value = float(header[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise PilotStop(f"missing/nonnumeric {key}") from exc
    if not math.isfinite(value) or value == -9999:
        raise PilotStop(f"invalid/fill {key}")
    return value


def header_errors(header: dict, filename: str, hdu_count: int) -> list[str]:
    errors = []
    if hdu_count != 2:
        errors.append(f"expected 2 operational HDUs, got {hdu_count}")
    for key in TRUE_KEYS:
        if header.get(key) is not True:
            errors.append(f"{key} is missing/not true: {header.get(key)!r}")
    for key in ("BADBLK_N", "MISBLK_N"):
        if header.get(key) != 0 or isinstance(header.get(key), bool):
            errors.append(f"{key} is missing/not zero: {header.get(key)!r}")
    for key in ("SHIFT_X", "SHIFT_Y"):
        try:
            if abs(number(header, key)) >= 7:
                errors.append(f"{key} reached/exceeded the +/-7 pixel limit")
        except PilotStop as exc:
            errors.append(str(exc))
    if (header.get("NAXIS1"), header.get("NAXIS2")) != (2048, 1920):
        errors.append("unexpected/missing 2048x1920 extension shape")
    try:
        expected = datetime.strptime(filename.split("_")[2], "%Y%m%dT%H%M%S").replace(
            tzinfo=timezone.utc
        )
        actual = datetime.fromisoformat(header["DATE-OBS"].replace("Z", "+00:00"))
        if actual.tzinfo is None:
            actual = actual.replace(tzinfo=timezone.utc)
        if abs((actual - expected).total_seconds()) > 1:
            errors.append("DATE-OBS differs from frozen filename by >1 second")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        errors.append(f"invalid/missing DATE-OBS: {exc}")
    return errors


def display_flips(header: dict) -> tuple[bool, bool]:
    """Return x,y flips needed for solar west-right, north-up display.

    This DOES NOT resolve whether the NRL report used that display.
    FITS/NumPy origin conventions are not guessed from source brightness.
    """
    if not str(header.get("CTYPE1", "")).startswith("HPLN") or not str(
        header.get("CTYPE2", "")
    ).startswith("HPLT"):
        raise PilotStop("STOP_WCS_NOT_HELIOPROJECTIVE")
    if "CD1_1" in header or "CD2_2" in header:
        matrix = np.array(
            [
                [number(header, "CD1_1"), number(header, "CD1_2")],
                [number(header, "CD2_1"), number(header, "CD2_2")],
            ]
        )
    else:
        matrix = np.array(
            [
                [
                    number(header, "CDELT1") * float(header.get("PC1_1", 1)),
                    number(header, "CDELT1") * float(header.get("PC1_2", 0)),
                ],
                [
                    number(header, "CDELT2") * float(header.get("PC2_1", 0)),
                    number(header, "CDELT2") * float(header.get("PC2_2", 1)),
                ],
            ]
        )
    if not np.isfinite(matrix).all() or matrix[0, 0] == 0 or matrix[1, 1] == 0:
        raise PilotStop("STOP_INVALID_WCS_MATRIX")
    if (
        abs(matrix[0, 1] / matrix[0, 0]) >= 0.01
        or abs(matrix[1, 0] / matrix[1, 1]) >= 0.01
    ):
        raise PilotStop("STOP_WCS_ROTATION_REQUIRES_UNFROZEN_RESAMPLING")
    return bool(matrix[0, 0] < 0), bool(matrix[1, 1] > 0)


def display_to_fits(positions: np.ndarray, header: dict) -> np.ndarray:
    flip_x, flip_y = display_flips(header)
    result = np.array(positions, dtype=float, copy=True)
    if flip_x:
        result[:, 0] = 2047 - result[:, 0]
    if flip_y:
        result[:, 1] = 1919 - result[:, 1]
    return result


def detector_motion_rms(headers: list[dict]) -> dict[str, float]:
    fits_positions = np.array(
        [display_to_fits(POSITIONS[i : i + 1], h)[0] for i, h in enumerate(headers)]
    )
    relative_positions = fits_positions - fits_positions[0]
    shifts = np.array([[number(h, "SHIFT_X"), number(h, "SHIFT_Y")] for h in headers])
    relative_shifts = shifts - shifts[0]
    return {
        label: float(
            np.sqrt(
                np.mean(
                    np.sum((relative_positions - sign * relative_shifts) ** 2, axis=1)
                )
            )
        )
        for label, sign in (("plus_shift", 1), ("minus_shift", -1))
    }


def gate_records(records: list[dict]) -> dict:
    if len(records) != 4 or [r.get("filename") for r in records] != list(FILES):
        raise PilotStop("STOP_NOT_THE_FOUR_FROZEN_FRAMES")
    quality = [
        {
            "filename": r["filename"],
            "errors": header_errors(r["header"], r["filename"], r["hdu_count"]),
        }
        for r in records
    ]
    result = {
        "quality": quality,
        "report_mapping_established": REPORT_MAPPING_ESTABLISHED,
    }
    if any(row["errors"] for row in quality):
        return {
            **result,
            "outcome": "STOP_METADATA_QUALITY",
            "real_pixels_scored": False,
        }
    try:
        flips = [display_flips(r["header"]) for r in records]
    except PilotStop as exc:
        return {**result, "outcome": str(exc), "real_pixels_scored": False}
    result["fits_to_north_up_flips_xy"] = flips
    if not REPORT_MAPPING_ESTABLISHED:
        return {
            **result,
            "outcome": "STOP_ORIENTATION_UNRESOLVED",
            "real_pixels_scored": False,
        }
    rms = detector_motion_rms([r["header"] for r in records])
    result["detector_motion_rms_pixels"] = rms
    if min(rms.values()) <= 2:
        return {
            **result,
            "outcome": "STOP_DETECTOR_FIXED_COMPATIBLE",
            "real_pixels_scored": False,
        }
    return {
        **result,
        "outcome": "READY_FOR_FROZEN_MEASUREMENT",
        "real_pixels_scored": False,
    }


def masks(
    shape: tuple[int, int], position: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    x, y = map(float, position)
    if x - 12 < 0 or y - 12 < 0 or x + 12 >= shape[1] or y + 12 >= shape[0]:
        raise PilotStop("STOP_APERTURE_OUTSIDE_CUTOUT")
    yy, xx = np.indices(shape)
    radius2 = (xx - x) ** 2 + (yy - y) ** 2
    return radius2 <= 9, (radius2 >= 64) & (radius2 <= 144)


def robust_scale(values: np.ndarray) -> float:
    if not np.isfinite(values).all():
        raise PilotStop("STOP_NONFINITE_PIXELS")
    scale = float(1.4826 * np.median(np.abs(values - np.median(values))))
    if not math.isfinite(scale) or scale <= 0:
        raise PilotStop("STOP_NONPOSITIVE_ANNULAR_SCALE")
    return scale


def residuals(cube: np.ndarray) -> np.ndarray:
    if cube.ndim != 3 or cube.shape[0] != 4:
        raise PilotStop("STOP_NOT_FOUR_PIXEL_FRAMES")
    return np.array(
        [cube[i] - np.median(np.delete(cube, i, axis=0), axis=0) for i in range(4)]
    )


def track_score(residual_cube: np.ndarray, positions: np.ndarray) -> dict:
    if residual_cube.shape[0] != 4 or np.shape(positions) != (4, 2):
        raise PilotStop("STOP_INVALID_TRACK_SHAPE")
    scores = []
    for frame, position in zip(residual_cube, positions, strict=True):
        aperture, annulus = masks(frame.shape, position)
        values = frame[aperture]
        background = frame[annulus]
        if not np.isfinite(values).all():
            raise PilotStop("STOP_NONFINITE_PIXELS")
        sigma = robust_scale(background)
        z = float(
            (values.sum() - values.size * np.median(background))
            / (sigma * np.sqrt(values.size))
        )
        scores.append(z)
    return {"z": scores, "Q": float(np.sum(scores) / 2)}


def measure_frozen_cube(cube: np.ndarray) -> dict:
    """Fixed statistic, used on synthetic arrays unless every scientific gate passes."""
    if cube.shape != (4, 216, 216):
        raise PilotStop("STOP_NOT_FIXED_CUTOUT_SHAPE")
    positions = POSITIONS - np.array([CUTOUT[0], CUTOUT[2]])
    difference = residuals(cube)
    source = track_score(difference, positions)
    negative = [
        {"offset_xy": offset.tolist(), **track_score(difference, positions + offset)}
        for offset in NEGATIVES
    ]
    injection_positions = positions + INJECTION_OFFSET
    baseline = track_score(difference, injection_positions)
    injected = np.array(cube, dtype=float, copy=True)
    yy, xx = np.indices(cube.shape[1:])
    peaks = []
    for i, position in enumerate(injection_positions):
        _, annulus = masks(cube.shape[1:], position)
        peak = 10 * robust_scale(cube[i][annulus])
        peaks.append(peak)
        injected[i] += peak * np.exp(
            -0.5 * ((xx - position[0]) ** 2 + (yy - position[1]) ** 2)
        )
    injection = track_score(residuals(injected), injection_positions)
    delta_z = np.array(injection["z"]) - np.array(baseline["z"])
    delta_q = injection["Q"] - baseline["Q"]
    injection_pass = delta_q >= 8 and np.count_nonzero(delta_z >= 3) >= 3
    source_pass = (
        source["Q"] >= 8
        and np.count_nonzero(np.array(source["z"]) >= 3) >= 3
        and source["Q"] > max(row["Q"] for row in negative)
    )
    return {
        "primary": source,
        "negative_tracks": negative,
        "injection": {
            "offset_xy": INJECTION_OFFSET.tolist(),
            "peaks": peaks,
            "baseline": baseline,
            "injected": injection,
            "delta_z": delta_z.tolist(),
            "delta_Q": delta_q,
            "pass": bool(injection_pass),
        },
        "reported_source_recovery_gate_pass": bool(source_pass),
        "outcome": "STOP_INJECTION_CONTROL"
        if not injection_pass
        else (
            "REPORTED_SOURCE_CONDITIONAL_RECOVERY"
            if source_pass
            else "NO_FIXED_GATE_RECOVERY"
        ),
        "not_a_significance_or_comet_truth_test": True,
    }


def load_header_records(raw_root: Path, ledger: dict) -> list[dict]:
    from astropy.io import fits

    sources = ledger.get("sources", [])
    if ledger.get("status") != "DOWNLOADED_FOUR_FROZEN_FRAMES" or [
        r["filename"] for r in sources
    ] != list(FILES):
        raise PilotStop("STOP_INCOMPLETE_OR_UNFROZEN_DOWNLOAD")
    if ledger["spec_sha256"] != sha256(ROOT / "SPEC-2026-09-05.md"):
        raise PilotStop("STOP_SPEC_CHANGED_AFTER_FREEZE")
    records = []
    for source in sources:
        path = raw_root / source["filename"]
        if path.stat().st_size != source["bytes"] or sha256(path) != source["sha256"]:
            raise PilotStop("STOP_RAW_HASH_OR_SIZE_MISMATCH")
        with fits.open(path, memmap=False, lazy_load_hdus=True) as hdus:
            # CompImageHDU.header exposes logical image metadata without reading
            # hdus[1].data (decompression). Preserve headers even on a gate stop.
            header = dict(hdus[1].header)
            header.pop("COMMENT", None)
            header.pop("HISTORY", None)
            records.append({**source, "hdu_count": len(hdus), "header": header})
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence",
        type=Path,
        help="Replay the tracked header-only evidence, without network/raw FITS",
    )
    args = parser.parse_args()
    if args.evidence:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
        if evidence["spec_sha256"] != sha256(ROOT / "SPEC-2026-09-05.md"):
            raise PilotStop("STOP_SPEC_EVIDENCE_MISMATCH")
        result = gate_records(evidence["records"])
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0

    result_dir = ROOT / "results"
    result_dir.mkdir(exist_ok=True)
    evidence_path = result_dir / "header-evidence.json"
    result_path = result_dir / "result.json"
    if evidence_path.exists() or result_path.exists():
        raise PilotStop("STOP_EXISTING_SINGLE_ATTEMPT_RESULT")
    ledger = json.loads(
        (ROOT / "data/download-ledger.json").read_text(encoding="utf-8-sig")
    )
    records = load_header_records(ROOT / "data/raw", ledger)
    result = gate_records(records)
    evidence = {
        "freeze_utc": ledger["freeze_utc"],
        "spec_sha256": ledger["spec_sha256"],
        "script_sha256": sha256(Path(__file__)),
        "records": records,
    }
    evidence_path.write_text(
        json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    # Mapping is unresolved in the frozen attempt. Do not decompress the images
    # or make a cutout/score under an assumed transform.
    if result["outcome"] == "READY_FOR_FROZEN_MEASUREMENT":
        raise PilotStop("STOP_NEW_MAPPING_REQUIRES_NEW_PROSPECTIVE_SPEC")
    result.update(
        {
            "spec_sha256": ledger["spec_sha256"],
            "header_evidence_sha256": sha256(evidence_path),
            "raw_bytes_total": sum(r["bytes"] for r in records),
            "images_decompressed": 0,
            "real_track_scores": None,
            "real_injection_scores": None,
            "report_truth": "POTENTIAL_COMET_NOT_CONFIRMED",
            "source_absence_inference_permitted": False,
        }
    )
    result_path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
