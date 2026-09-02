"""Reproduce a published T CrB high state from frozen DASCH DR7 responses.

This is a feasibility/positive-control audit. It does not search unknown sources.
Only aggregate statistics are written to the output JSON.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STANDARD_BAD_AFLAGS = 64 | 2048 | 4096 | 8192 | 32768
ASTROMETRIC_LIMIT_ARCSEC = 15.0
BASELINE_WINDOW = (1924.0, 1938.0)
HIGH_STATE_WINDOW = (1938.0, 1946.0)
MIN_WINDOW_DETECTIONS = 20
MIN_BRIGHTENING_MAG = 0.5
MIN_FIELD_WINDOW_DETECTIONS = 10
MAX_FIELD_SHIFT_MAG = 0.3
MIN_DIFFERENTIAL_BRIGHTENING_MAG = 0.7
ANALYSIS_INPUT_ROLES = (
    "target_querycat",
    "target_lightcurve",
    "field_querycat",
    "field_lightcurve",
)
REQUIRED_PROVENANCE_ROLES = frozenset((*ANALYSIS_INPUT_ROLES, "api_health"))
EXPECTED_ANALYSIS_ID = "dasch-m0-tcrb-20260902"
EXPECTED_TARGET_NAME = "T CrB"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_api_table(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path}: expected a nonempty JSON list")
    if not all(isinstance(item, str) for item in payload):
        raise ValueError(f"{path}: API rows must be JSON strings")

    reader = csv.DictReader(io.StringIO("\n".join(payload)))
    rows = list(reader)
    if reader.fieldnames is None:
        raise ValueError(f"{path}: missing CSV header")
    if any(None in row for row in rows):
        raise ValueError(f"{path}: malformed CSV row")
    return rows


def maybe_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def maybe_int(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)


def decimal_year(jd: float) -> float:
    instant = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=jd - 2440587.5
    )
    year_start = datetime(instant.year, 1, 1, tzinfo=timezone.utc)
    next_start = datetime(instant.year + 1, 1, 1, tzinfo=timezone.utc)
    return instant.year + (instant - year_start) / (next_start - year_start)


def angular_sep_arcsec(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    ra1 = math.radians(ra1_deg)
    dec1 = math.radians(dec1_deg)
    ra2 = math.radians(ra2_deg)
    dec2 = math.radians(dec2_deg)
    cosine = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine)))) * 3600.0


def robust_stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "median_mag": None, "mad_mag": None}
    median = statistics.median(values)
    return {
        "n": len(values),
        "median_mag": median,
        "mad_mag": statistics.median(abs(value - median) for value in values),
    }


def _verify_file(path: Path, artifact: dict[str, Any], *, role: str) -> None:
    observed_size = path.stat().st_size
    observed_hash = sha256_file(path)
    if observed_size != artifact["bytes"]:
        raise ValueError(
            f"size mismatch for {role}: {observed_size} != {artifact['bytes']}"
        )
    if observed_hash != artifact["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {role}")


def _verify_provenance(
    provenance_path: Path,
    base_dir: Path,
    supplied_paths: dict[str, Path],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    """Bind the manifest, stored artifacts, and every effective analysis input."""

    manifest_bytes = provenance_path.read_bytes()
    provenance = json.loads(manifest_bytes.decode("utf-8"))
    if provenance.get("schema_version") != 1:
        raise ValueError("unsupported provenance schema")
    if provenance.get("analysis_id") != EXPECTED_ANALYSIS_ID:
        raise ValueError("provenance manifest is not the frozen DASCH M0 analysis")
    if (provenance.get("target") or {}).get("name") != EXPECTED_TARGET_NAME:
        raise ValueError("provenance manifest has the wrong positive-control target")
    artifacts = provenance.get("artifacts")
    if not isinstance(artifacts, list):
        raise TypeError("provenance artifacts must be a list")

    by_role: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        role = artifact.get("role")
        if not isinstance(role, str) or not role:
            raise ValueError("every provenance artifact must have a role")
        if role in by_role:
            raise ValueError(f"duplicate provenance role: {role}")
        by_role[role] = artifact
    if set(by_role) != REQUIRED_PROVENANCE_ROLES:
        raise ValueError(
            "provenance roles differ from the frozen M0 contract: "
            f"{sorted(by_role)}"
        )
    if set(supplied_paths) != set(ANALYSIS_INPUT_ROLES):
        raise ValueError("all four effective analysis inputs must be role-bound")

    resolved_base = base_dir.resolve()
    effective_paths: dict[str, Path] = {}
    proof_artifacts: dict[str, dict[str, int | str]] = {}
    for role, artifact in by_role.items():
        stored_path = (base_dir / artifact["path"]).resolve()
        try:
            stored_path.relative_to(resolved_base)
        except ValueError as exc:
            raise ValueError(f"provenance path escapes pilot directory: {role}") from exc
        _verify_file(stored_path, artifact, role=f"stored {role}")

        effective_path = supplied_paths.get(role, stored_path).resolve()
        _verify_file(effective_path, artifact, role=f"effective {role}")
        effective_paths[role] = effective_path
        proof_artifacts[role] = {
            "bytes": artifact["bytes"],
            "sha256": artifact["sha256"],
        }

    proof = {
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "artifacts": proof_artifacts,
    }
    return provenance, proof, effective_paths


def _require_catalog_identity(
    catalog_row: dict[str, str], request: dict[str, Any], *, label: str
) -> None:
    for key in ("ref_number", "gsc_bin_index"):
        if maybe_int(catalog_row.get(key), -1) != request[key]:
            raise ValueError(f"{label} catalog identity disagrees with {key}")


def summarize_lightcurve(rows: list[dict[str, str]]) -> dict[str, Any]:
    detections: list[dict[str, float | int]] = []
    rejected_aflags = 0
    rejected_astrometry = 0

    for row in rows:
        magnitude = maybe_float(row.get("magcal_magdep"))
        if magnitude is None:
            continue
        if row.get("aflags") in (None, ""):
            raise ValueError("detected light-curve row is missing aflags")
        aflags = maybe_int(row["aflags"])
        if aflags & STANDARD_BAD_AFLAGS:
            rejected_aflags += 1
            continue

        ra_deg = maybe_float(row.get("ra_deg"))
        dec_deg = maybe_float(row.get("dec_deg"))
        cat_ra = maybe_float(row.get("ra_cat_corrected"))
        cat_dec = maybe_float(row.get("dec_cat_corrected"))
        if None in (ra_deg, dec_deg, cat_ra, cat_dec):
            rejected_astrometry += 1
            continue
        separation = angular_sep_arcsec(ra_deg, dec_deg, cat_ra, cat_dec)
        if separation > ASTROMETRIC_LIMIT_ARCSEC:
            rejected_astrometry += 1
            continue

        detections.append(
            {
                "year": decimal_year(float(row["date_jd"])),
                "magnitude": magnitude,
                "separation_arcsec": separation,
            }
        )

    baseline_mags = [
        float(point["magnitude"])
        for point in detections
        if BASELINE_WINDOW[0] <= point["year"] < BASELINE_WINDOW[1]
    ]
    high_state_mags = [
        float(point["magnitude"])
        for point in detections
        if HIGH_STATE_WINDOW[0] <= point["year"] < HIGH_STATE_WINDOW[1]
    ]
    baseline = robust_stats(baseline_mags)
    high_state = robust_stats(high_state_mags)

    brightening = None
    if baseline["median_mag"] is not None and high_state["median_mag"] is not None:
        brightening = float(baseline["median_mag"]) - float(
            high_state["median_mag"]
        )

    detected_count = sum(
        maybe_float(row.get("magcal_magdep")) is not None for row in rows
    )
    standard_clean_count = detected_count - rejected_aflags
    return {
        "raw_lightcurve_rows": len(rows),
        "quality_flow": {
            "detections": detected_count,
            "rejected_by_standard_aflags": rejected_aflags,
            "after_standard_aflags": standard_clean_count,
            "rejected_by_astrometry_after_aflags": rejected_astrometry,
            "analysis_detections": len(detections),
            "standard_bad_aflags_mask": STANDARD_BAD_AFLAGS,
            "astrometric_limit_arcsec": ASTROMETRIC_LIMIT_ARCSEC,
        },
        "baseline_1924_1937": baseline,
        "published_high_state_1938_1945": high_state,
        "median_brightening_mag": brightening,
    }


def analyze(
    querycat_path: Path,
    lightcurve_path: Path,
    field_querycat_path: Path,
    field_lightcurve_path: Path,
    provenance_path: Path,
) -> dict[str, Any]:
    pilot_dir = provenance_path.parent.parent
    supplied_paths = {
        "target_querycat": querycat_path,
        "target_lightcurve": lightcurve_path,
        "field_querycat": field_querycat_path,
        "field_lightcurve": field_lightcurve_path,
    }
    provenance, proof_before, verified_paths = _verify_provenance(
        provenance_path, pilot_dir, supplied_paths
    )
    target = provenance["target"]

    health = json.loads(verified_paths["api_health"].read_text(encoding="utf-8"))
    if health.get("status") != "ready":
        raise ValueError("frozen DASCH API health response was not ready")

    catalog_rows = load_api_table(verified_paths["target_querycat"])
    if len(catalog_rows) != 1:
        raise ValueError(f"expected one source match, found {len(catalog_rows)}")
    catalog_row = catalog_rows[0]
    target_request = next(
        artifact["request"]
        for artifact in provenance["artifacts"]
        if artifact["role"] == "target_lightcurve"
    )
    _require_catalog_identity(catalog_row, target_request, label="target")
    catalog_offset = angular_sep_arcsec(
        target["ra_deg"],
        target["dec_deg"],
        float(catalog_row["ra_deg"]),
        float(catalog_row["dec_deg"]),
    )

    eligible_field_rows = [
        row
        for row in load_api_table(verified_paths["field_querycat"])
        if maybe_int(row.get("class"), -1) == 0
        and maybe_int(row.get("v_flag"), -1) == 0
    ]
    if not eligible_field_rows:
        raise ValueError("field query contains no eligible non-variable stellar control")
    field_catalog_row = min(
        eligible_field_rows,
        key=lambda row: (-maybe_int(row.get("num_matches")), row["ref_text"]),
    )
    expected_request = next(
        artifact["request"]
        for artifact in provenance["artifacts"]
        if artifact["role"] == "field_lightcurve"
    )
    _require_catalog_identity(field_catalog_row, expected_request, label="field control")

    target_summary = summarize_lightcurve(
        load_api_table(verified_paths["target_lightcurve"])
    )
    field_summary = summarize_lightcurve(
        load_api_table(verified_paths["field_lightcurve"])
    )
    target_detections = target_summary["quality_flow"]["detections"]
    field_detections = field_summary["quality_flow"]["detections"]
    if target_detections != maybe_int(catalog_row.get("num_matches"), -1):
        raise ValueError("target querycat/lightcurve detection accounting does not close")
    if field_detections != maybe_int(field_catalog_row.get("num_matches"), -1):
        raise ValueError("field querycat/lightcurve detection accounting does not close")
    target_brightening = target_summary["median_brightening_mag"]
    field_shift = field_summary["median_brightening_mag"]
    differential = None
    if target_brightening is not None and field_shift is not None:
        differential = target_brightening - field_shift

    positive_control_pass = (
        target_summary["baseline_1924_1937"]["n"] >= MIN_WINDOW_DETECTIONS
        and target_summary["published_high_state_1938_1945"]["n"]
        >= MIN_WINDOW_DETECTIONS
        and target_brightening is not None
        and target_brightening >= MIN_BRIGHTENING_MAG
    )
    field_control_pass = (
        field_summary["baseline_1924_1937"]["n"] >= MIN_FIELD_WINDOW_DETECTIONS
        and field_summary["published_high_state_1938_1945"]["n"]
        >= MIN_FIELD_WINDOW_DETECTIONS
        and field_shift is not None
        and abs(field_shift) <= MAX_FIELD_SHIFT_MAG
    )
    differential_pass = (
        differential is not None
        and differential >= MIN_DIFFERENTIAL_BRIGHTENING_MAG
    )
    feasibility_pass = positive_control_pass and field_control_pass and differential_pass

    _, proof_after, _ = _verify_provenance(
        provenance_path, pilot_dir, supplied_paths
    )
    if proof_after != proof_before:
        raise ValueError("provenance or an effective input changed during analysis")

    return {
        "schema_version": 1,
        "analysis_role": "published_positive_control_with_nearby_field_control",
        "input_provenance": proof_after,
        "api_health": {
            "status": health["status"],
            "ready": True,
        },
        "target": target["name"],
        "catalog_match": {
            "matches": len(catalog_rows),
            "offset_arcsec": catalog_offset,
            "catalog_reported_detections": maybe_int(catalog_row.get("num_matches")),
        },
        "target_summary": target_summary,
        "field_control": {
            "selection": "highest-detection APASS class=0, v_flag=0 source in frozen 600-arcsec field",
            "catalog_reported_detections": maybe_int(
                field_catalog_row.get("num_matches")
            ),
            "summary": field_summary,
        },
        "differential_brightening_mag": differential,
        "acceptance": {
            "minimum_detections_per_window": MIN_WINDOW_DETECTIONS,
            "minimum_brightening_mag": MIN_BRIGHTENING_MAG,
            "minimum_field_detections_per_window": MIN_FIELD_WINDOW_DETECTIONS,
            "maximum_absolute_field_shift_mag": MAX_FIELD_SHIFT_MAG,
            "minimum_differential_brightening_mag": MIN_DIFFERENTIAL_BRIGHTENING_MAG,
            "positive_control_pass": positive_control_pass,
            "field_control_pass": field_control_pass,
            "differential_pass": differential_pass,
            "feasibility_pass": feasibility_pass,
        },
        "verdict": (
            "TARGETED_DASCH_FEASIBILITY_PASS"
            if feasibility_pass
            else "TARGETED_DASCH_FEASIBILITY_FAIL"
        ),
        "discovery_scan": "NOT_RUN",
        "candidate_identifiers_emitted": 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    pilot_dir = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--querycat",
        type=Path,
        default=pilot_dir / "data/raw/tcrb-querycat.json",
    )
    parser.add_argument(
        "--lightcurve",
        type=Path,
        default=pilot_dir / "data/raw/tcrb-lightcurve.json",
    )
    parser.add_argument(
        "--field-querycat",
        type=Path,
        default=pilot_dir / "data/raw/tcrb-field-querycat.json",
    )
    parser.add_argument(
        "--field-lightcurve",
        type=Path,
        default=pilot_dir / "data/raw/field-control-lightcurve.json",
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=pilot_dir / "data/provenance.json",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze(
        args.querycat,
        args.lightcurve,
        args.field_querycat,
        args.field_lightcurve,
        args.provenance,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["acceptance"]["feasibility_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
