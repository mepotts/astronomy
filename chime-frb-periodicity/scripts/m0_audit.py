#!/usr/bin/env python3
"""Execute the CHIME/FRB Catalog 2 periodicity M0 kill checks.

This program deliberately does not scan unknown repeaters.  It verifies the
released inputs, collapses sub-bursts to independent events, runs the published
FRB 20180916B period as a positive control, and decides whether the released
exposure product contains the time-resolved observing window required for a
discovery-grade search.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXPECTED_COLUMNS = (
    "tns_name",
    "previous_name",
    "repeater_name",
    "event_id",
    "sub_num",
    "ra",
    "ra_err",
    "dec",
    "dec_err",
    "ra_dec_notes",
    "gl",
    "gb",
    "exp_up",
    "exp_up_err",
    "exp_low",
    "exp_low_err",
    "exp_notes",
    "bonsai_snr",
    "bonsai_dm",
    "low_ft_68",
    "up_ft_68",
    "low_ft_95",
    "up_ft_95",
    "snr_fitb",
    "dm_fitb",
    "dm_fitb_err",
    "dm_exc_ne2001",
    "dm_exc_ymw16",
    "bc_width",
    "scat_time",
    "scat_time_err",
    "flux",
    "flux_err",
    "fluence",
    "fluence_err",
    "fluence_notes",
    "fluence_win_extended",
    "mjd_400",
    "mjd_400_err",
    "mjd_inf",
    "mjd_inf_err",
    "width_fitb",
    "width_fitb_err",
    "sp_idx",
    "sp_idx_err",
    "sp_run",
    "sp_run_err",
    "high_freq",
    "low_freq",
    "peak_freq",
    "chi_sq",
    "dof",
    "flag_frac",
    "notes_fitb",
    "intrachan_flag",
    "excluded_flag",
    "sidelobe_flag",
    "citizen_science_flag",
    "catalog1_flag",
    "catalog1_param_flag",
)

RELEASE_COUNTS = {
    "subburst_rows": 5045,
    "events": 4539,
    "sources": 3641,
    "repeaters": 83,
    "repeater_events": 981,
}

EVENT_INVARIANTS = (
    "tns_name",
    "previous_name",
    "repeater_name",
    "event_id",
    "excluded_flag",
    "sidelobe_flag",
    "citizen_science_flag",
)

SURVEY_START_DATE = "2018-09-04"
SURVEY_END_DATE = "2023-09-15"
SAFE_HDF5_ATTRIBUTES = frozenset(
    {
        "class",
        "coordsys",
        "description",
        "dimension_labels",
        "end_date",
        "nside",
        "ordering",
        "spatial_scheme",
        "start_date",
        "t_res",
        "time_axis",
        "units",
    }
)


class M0Error(RuntimeError):
    """Raised when an input or invariant fails closed."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _within(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise M0Error(f"manifest path escapes project root: {relative_path}") from exc
    return candidate


def verify_manifest(project_root: Path, manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise M0Error("unsupported provenance manifest schema")

    verified: list[dict[str, Any]] = []
    roles: set[str] = set()
    for entry in manifest.get("files", []):
        role = str(entry.get("role", ""))
        if not role or role in roles:
            raise M0Error(f"missing or duplicate manifest role: {role!r}")
        roles.add(role)
        path = _within(project_root, str(entry["local_path"]))
        if not path.is_file():
            raise M0Error(f"missing raw input for {role}: {path}")
        actual_size = path.stat().st_size
        actual_sha256 = sha256_file(path)
        expected_size = int(entry["bytes"])
        expected_sha256 = str(entry["sha256"]).lower()
        if actual_size != expected_size or actual_sha256 != expected_sha256:
            raise M0Error(
                f"provenance mismatch for {role}: "
                f"bytes={actual_size}/{expected_size}, sha256={actual_sha256}/{expected_sha256}"
            )
        verified.append(
            {
                "role": role,
                "path": Path(str(entry["local_path"])).as_posix(),
                "bytes": actual_size,
                "sha256": actual_sha256,
                "url": entry["url"],
                "retrieved_utc": entry["retrieved_utc"],
            }
        )

    required_roles = {"canonical_catalog_csv", "integrated_exposure_hdf5"}
    if roles != required_roles:
        raise M0Error(f"manifest roles are {sorted(roles)}, expected {sorted(required_roles)}")
    return manifest, verified


def load_catalog(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise M0Error("Catalog 2 CSV columns do not match the frozen 60-column schema")
        rows = list(reader)
    if not rows:
        raise M0Error("Catalog 2 CSV is empty")
    return rows


def _finite_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise M0Error(f"invalid {label}: {value!r}") from exc
    if not math.isfinite(number):
        raise M0Error(f"non-finite {label}: {value!r}")
    return number


def collapse_events(rows: Iterable[dict[str, str]]) -> list[dict[str, Any]]:
    """Collapse sub-burst rows to one event without depending on input order."""
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        event_id = row.get("event_id", "")
        if not event_id:
            raise M0Error("catalog row has no event_id")
        groups[event_id].append(row)

    events: list[dict[str, Any]] = []
    for event_id, subbursts in groups.items():
        for field in EVENT_INVARIANTS:
            values = {row[field] for row in subbursts}
            if len(values) != 1:
                raise M0Error(f"event {event_id} changes invariant field {field}: {sorted(values)}")

        sub_numbers: list[int] = []
        for row in subbursts:
            try:
                sub_numbers.append(int(row["sub_num"]))
            except ValueError as exc:
                raise M0Error(f"event {event_id} has invalid sub_num") from exc
        if len(sub_numbers) != len(set(sub_numbers)):
            raise M0Error(f"event {event_id} repeats a sub_num")

        representative = min(subbursts, key=lambda row: int(row["sub_num"]))
        event = dict(representative)
        event["event_mjd_inf"] = min(
            _finite_float(row["mjd_inf"], f"mjd_inf for event {event_id}") for row in subbursts
        )
        event["subburst_count"] = len(subbursts)
        events.append(event)

    events.sort(key=lambda row: (float(row["event_mjd_inf"]), str(row["event_id"])))
    return events


def is_clean(event: dict[str, Any]) -> bool:
    return all(event[field] == "0" for field in ("excluded_flag", "sidelobe_flag", "citizen_science_flag"))


def summarize_catalog(rows: list[dict[str, str]], events: list[dict[str, Any]]) -> dict[str, Any]:
    repeater_counts = Counter(event["repeater_name"] for event in events if event["repeater_name"])
    nonrepeater_events = sum(not event["repeater_name"] for event in events)
    counts = {
        "subburst_rows": len(rows),
        "events": len(events),
        "sources": nonrepeater_events + len(repeater_counts),
        "repeaters": len(repeater_counts),
        "repeater_events": sum(repeater_counts.values()),
    }
    clean_by_repeater: Counter[str] = Counter(
        event["repeater_name"] for event in events if event["repeater_name"] and is_clean(event)
    )
    clean_days_by_repeater: dict[str, set[int]] = defaultdict(set)
    for event in events:
        if event["repeater_name"] and is_clean(event):
            clean_days_by_repeater[event["repeater_name"]].add(math.floor(float(event["event_mjd_inf"])))

    return {
        "counts": counts,
        "matches_published_release_counts": counts == RELEASE_COUNTS,
        "clean_repeater_events": sum(clean_by_repeater.values()),
        "cohort_sizes": {
            "repeaters_with_at_least_5_clean_events": sum(value >= 5 for value in clean_by_repeater.values()),
            "repeaters_with_at_least_10_clean_events": sum(value >= 10 for value in clean_by_repeater.values()),
            "repeaters_with_at_least_12_clean_events": sum(value >= 12 for value in clean_by_repeater.values()),
            "repeaters_with_at_least_10_clean_active_days": sum(
                len(days) >= 10 for days in clean_days_by_repeater.values()
            ),
        },
        "prospective_source_identifiers_emitted": False,
    }


def rayleigh_scan(
    times: Iterable[float],
    period_min_days: float,
    period_max_days: float,
    oversampling: int = 10,
) -> dict[str, Any]:
    import numpy as np

    values = np.asarray(tuple(times), dtype=float)
    if values.size < 3 or not np.all(np.isfinite(values)):
        raise M0Error("Rayleigh control requires at least three finite times")
    values = values - values.min()
    baseline = float(np.ptp(values))
    if baseline <= period_max_days:
        raise M0Error("Rayleigh control baseline must exceed the maximum trial period")
    frequency_step = 1.0 / (baseline * oversampling)
    frequencies = np.arange(
        1.0 / period_max_days,
        1.0 / period_min_days + frequency_step / 2.0,
        frequency_step,
    )
    phases = 2.0 * np.pi * values[:, None] * frequencies[None, :]
    scores = 2.0 / values.size * (
        np.square(np.cos(phases).sum(axis=0)) + np.square(np.sin(phases).sum(axis=0))
    )
    best_index = int(np.argmax(scores))
    return {
        "sample_size": int(values.size),
        "baseline_days": baseline,
        "period_min_days": period_min_days,
        "period_max_days": period_max_days,
        "oversampling": oversampling,
        "trial_frequencies": int(frequencies.size),
        "best_period_days": float(1.0 / frequencies[best_index]),
        "best_rayleigh_z1_squared": float(scores[best_index]),
    }


def run_positive_control(events: list[dict[str, Any]]) -> dict[str, Any]:
    import numpy as np

    published_period_days = 16.35
    tolerance_days = 0.5
    event_times = [
        float(event["event_mjd_inf"])
        for event in events
        if event["repeater_name"] == "FRB20180916B" and is_clean(event)
    ]
    # A CHIME transit is the independent unit for this smoke test.  Multiple
    # bursts during one UTC day do not become independent period evidence.
    active_transit_days = np.unique(np.floor(np.asarray(event_times)) + 0.5)
    scan = rayleigh_scan(active_transit_days, 2.0, 100.0, oversampling=10)
    difference = abs(scan["best_period_days"] - published_period_days)
    return {
        "control_source": "FRB20180916B",
        "published_period_days": published_period_days,
        "acceptance_tolerance_days": tolerance_days,
        "clean_events": len(event_times),
        "independent_active_days": int(active_transit_days.size),
        **scan,
        "absolute_period_error_days": difference,
        "passes_recovery_gate": difference <= tolerance_days,
        "p_value_reported": False,
        "interpretation": "method smoke test only; unknown observing downtime is not modeled",
    }


def _json_value(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return _json_value(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _mjd_from_iso_date(value: Any) -> float:
    text = str(_json_value(value)).strip()
    instant = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    epoch = datetime(1858, 11, 17, tzinfo=timezone.utc)
    return (instant - epoch).total_seconds() / 86400.0


def _dimension_labels(attributes: dict[str, Any]) -> list[str]:
    labels = attributes.get("DIMENSION_LABELS", [])
    if not isinstance(labels, list):
        labels = [labels]
    return [str(label).lower() for label in labels]


def _safe_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in attributes.items()
        if key.lower() in SAFE_HDF5_ATTRIBUTES
    }


def _attribute(attributes: dict[str, Any], name: str) -> Any:
    wanted = name.lower()
    for key, value in attributes.items():
        if key.lower() == wanted:
            return value
    return None


def _positive_integer(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    try:
        if float(value) != number:
            return None
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _numeric_state_proof(
    dataset: Any, time_axis_index: int
) -> dict[str, Any] | None:
    """Prove a finite state array with a real zero-to-usable temporal transition."""

    import numpy as np

    if not (
        np.issubdtype(dataset.dtype, np.number)
        or np.issubdtype(dataset.dtype, np.bool_)
    ):
        return None
    if not 0 <= time_axis_index < dataset.ndim or dataset.shape[time_axis_index] < 2:
        return None
    spatial_slice_size = dataset.size // dataset.shape[time_axis_index]
    if spatial_slice_size > 10_000_000:
        # A future very-high-resolution product needs a dedicated streaming adapter.
        return None
    selections: Iterable[Any]
    if dataset.chunks is not None:
        selections = dataset.iter_chunks()
    elif dataset.size <= 10_000_000:
        selections = (tuple(slice(None) for _ in dataset.shape),)
    else:
        # A very large contiguous array cannot be exhaustively validated in bounded
        # memory. A future product must be chunked or receive a dedicated adapter.
        return None

    minimum = math.inf
    maximum = -math.inf
    values_seen = 0
    for selection in selections:
        values = np.asarray(dataset[selection])
        if values.size == 0 or not np.all(np.isfinite(values)):
            return None
        minimum = min(minimum, float(np.min(values)))
        maximum = max(maximum, float(np.max(values)))
        values_seen += int(values.size)
    if values_seen != dataset.size or minimum < 0.0 or minimum != 0.0 or maximum <= 0.0:
        return None

    selector = [slice(None)] * dataset.ndim
    selector[time_axis_index] = 0
    first = np.asarray(dataset[tuple(selector)])
    seen_zero = first == 0
    seen_usable = first > 0
    for time_index in range(1, dataset.shape[time_axis_index]):
        selector[time_axis_index] = time_index
        current = np.asarray(dataset[tuple(selector)])
        seen_zero |= current == 0
        seen_usable |= current > 0
    transitioning_elements = int(np.count_nonzero(seen_zero & seen_usable))
    if transitioning_elements == 0:
        # A permanently masked sky pixel plus an otherwise static/positive map is
        # not evidence of temporal downtime.
        return None
    return {
        "values_checked": values_seen,
        "minimum": minimum,
        "maximum": maximum,
        "has_outage_samples": True,
        "has_usable_samples": True,
        "has_temporal_outage_transition": True,
        "transitioning_spatial_elements": transitioning_elements,
    }


def inspect_exposure(path: Path) -> dict[str, Any]:
    import h5py
    import numpy as np

    datasets: list[dict[str, Any]] = []
    valid_time_axes: list[dict[str, Any]] = []
    aligned_operational: list[str] = []
    source_specific: list[str] = []
    operational_proofs: dict[str, dict[str, Any]] = {}
    time_tokens = ("time", "mjd", "date", "day")
    state_tokens = (
        "operational",
        "nominal",
        "sensitivity",
        "uptime",
        "downtime",
        "duty",
        "exposure",
    )
    spatial_tokens = ("healpix", "pixel", "source", "beam", "declination", "transit")
    with h5py.File(path, "r") as handle:
        raw_root_attributes = {
            key: _json_value(value) for key, value in handle.attrs.items()
        }
        root_attributes = _safe_attributes(raw_root_attributes)

        def visitor(name: str, obj: Any) -> None:
            if not isinstance(obj, h5py.Dataset):
                return
            raw_attributes = {
                key: _json_value(value) for key, value in obj.attrs.items()
            }
            datasets.append(
                {
                    "name": name,
                    "shape": list(obj.shape),
                    "dtype": str(obj.dtype),
                    "attributes": _safe_attributes(raw_attributes),
                }
            )

        handle.visititems(visitor)

        frozen_start_mjd = _mjd_from_iso_date(SURVEY_START_DATE)
        frozen_end_mjd = _mjd_from_iso_date(SURVEY_END_DATE)
        frozen_span_days = frozen_end_mjd - frozen_start_mjd
        metadata_span_matches = True
        if _attribute(raw_root_attributes, "start_date") is not None:
            metadata_span_matches = metadata_span_matches and abs(
                _mjd_from_iso_date(_attribute(raw_root_attributes, "start_date"))
                - frozen_start_mjd
            ) <= 1.0
        if _attribute(raw_root_attributes, "end_date") is not None:
            metadata_span_matches = metadata_span_matches and abs(
                _mjd_from_iso_date(_attribute(raw_root_attributes, "end_date"))
                - frozen_end_mjd
            ) <= 1.0
        for item in datasets:
            name = item["name"]
            labels = _dimension_labels(item["attributes"])
            units = str(item["attributes"].get("units", "")).lower()
            searchable = " ".join([name, *labels, units]).lower()
            shape = item["shape"]
            if len(shape) != 1 or shape[0] < 2:
                continue
            if not any(token in searchable for token in time_tokens):
                continue
            if "mjd" not in searchable and "1858-11-17" not in units:
                continue
            if shape[0] > 5_000_000:
                continue
            values = np.asarray(handle[name][...], dtype=float)
            if values.ndim != 1 or not np.all(np.isfinite(values)):
                continue
            differences = np.diff(values)
            if not np.all(differences > 0):
                continue
            median_cadence = float(np.median(differences))
            maximum_cadence = float(np.max(differences))
            if median_cadence > 1.5 or maximum_cadence > 1.5:
                continue
            coverage_ok = (
                metadata_span_matches
                and frozen_start_mjd - 1.0 <= values[0] <= frozen_start_mjd
                and frozen_end_mjd <= values[-1] <= frozen_end_mjd + 1.0
                and np.all(values >= frozen_start_mjd - 1.0)
                and np.all(values <= frozen_end_mjd + 1.0)
                and len(values) >= max(2, int(frozen_span_days * 0.5))
            )
            if coverage_ok:
                valid_time_axes.append(
                    {
                        "name": name,
                        "samples": int(values.size),
                        "min_mjd": float(values[0]),
                        "max_mjd": float(values[-1]),
                        "median_cadence_days": median_cadence,
                        "maximum_cadence_days": maximum_cadence,
                        "expected_span_days": frozen_span_days,
                    }
                )

        for axis in valid_time_axes:
            time_name = axis["name"]
            time_length = axis["samples"]
            for item in datasets:
                if item["name"] == time_name:
                    continue
                attributes = item["attributes"]
                labels = _dimension_labels(attributes)
                description = str(attributes.get("description", "")).lower()
                searchable = " ".join([item["name"], *labels, description]).lower()
                if "integrated" in searchable:
                    continue
                if not any(token in searchable for token in state_tokens):
                    continue
                dataset = handle[item["name"]]
                if len(labels) != dataset.ndim:
                    continue
                matching_axes = [
                    index
                    for index, length in enumerate(item["shape"])
                    if length == time_length
                    and index < len(labels)
                    and any(token in labels[index] for token in time_tokens)
                ]
                if not matching_axes:
                    continue
                time_axis_index = matching_axes[0]
                time_reference = _attribute(attributes, "time_axis")
                referenced_name = str(time_reference or "").lstrip("/")
                attached_scales = {
                    scale.name.lstrip("/")
                    for scale in dataset.dims[time_axis_index].values()
                }
                if time_name not in {referenced_name, *attached_scales}:
                    continue
                state_proof = _numeric_state_proof(dataset, time_axis_index)
                if state_proof is None:
                    continue
                aligned_operational.append(item["name"])
                operational_proofs[item["name"]] = {
                    "time_axis": time_name,
                    "time_axis_index": time_axis_index,
                    "state": state_proof,
                }
                other_indices = [
                    index for index in range(len(labels)) if index not in matching_axes
                ]
                for spatial_index in other_indices:
                    spatial_label = labels[spatial_index]
                    if not any(token in spatial_label for token in spatial_tokens):
                        continue
                    combined_attributes = {**raw_root_attributes, **attributes}
                    scheme = str(
                        _attribute(combined_attributes, "spatial_scheme") or spatial_label
                    ).lower()
                    if "healpix" not in scheme and "pixel" not in scheme:
                        continue
                    nside = _positive_integer(_attribute(combined_attributes, "nside"))
                    ordering = str(
                        _attribute(combined_attributes, "ordering") or ""
                    ).upper()
                    coordsys = str(
                        _attribute(combined_attributes, "coordsys") or ""
                    ).upper()
                    is_power_of_two = nside is not None and (nside & (nside - 1)) == 0
                    if not (
                        is_power_of_two
                        and dataset.shape[spatial_index] == 12 * nside * nside
                        and ordering in {"RING", "NESTED", "NEST"}
                        and coordsys in {"C", "CELESTIAL", "ICRS", "EQUATORIAL"}
                    ):
                        continue
                    source_specific.append(item["name"])
                    operational_proofs[item["name"]]["spatial_mapping"] = {
                        "scheme": "HEALPIX",
                        "axis_index": spatial_index,
                        "nside": nside,
                        "ordering": ordering,
                        "coordsys": coordsys,
                        "all_sky_mapping": True,
                    }
                    break

    integrated_only = bool(datasets) and all(
        item["attributes"].get("class") == "HEALPIX"
        and "integrated exposure" in str(item["attributes"].get("description", "")).lower()
        for item in datasets
    )
    has_valid_time_axis = bool(valid_time_axes)
    has_aligned_operational_series = bool(set(aligned_operational))
    has_source_specific_exposure = bool(set(source_specific))
    has_time_resolved_window = (
        has_valid_time_axis
        and has_aligned_operational_series
        and has_source_specific_exposure
    )
    failures: list[str] = []
    if not has_valid_time_axis:
        failures.append("no validated monotonic survey-spanning MJD axis at <=1.5-day cadence")
    if not has_aligned_operational_series:
        failures.append("no operational/nominal-sensitivity series aligned to the time axis")
    if not has_source_specific_exposure:
        failures.append("no aligned beam/transit/spatial exposure information for per-source windows")
    return {
        "root_attributes": root_attributes,
        "datasets": datasets,
        "valid_time_axes": valid_time_axes,
        "aligned_operational_dataset_names": sorted(set(aligned_operational)),
        "source_specific_exposure_dataset_names": sorted(set(source_specific)),
        "operational_dataset_proofs": operational_proofs,
        "frozen_required_span": {
            "start_date": SURVEY_START_DATE,
            "end_date": SURVEY_END_DATE,
            "start_mjd": frozen_start_mjd,
            "end_mjd": frozen_end_mjd,
        },
        "integrated_sky_maps_only": integrated_only,
        "has_valid_time_axis": has_valid_time_axis,
        "has_aligned_operational_series": has_aligned_operational_series,
        "has_source_specific_exposure": has_source_specific_exposure,
        "has_time_resolved_observing_window": has_time_resolved_window,
        "passes_window_gate": has_time_resolved_window and not integrated_only,
        "window_gate_failures": failures,
        "note": "A time coordinate alone is insufficient; finite values, explicit time linkage, a zero-to-usable transition in at least one spatial element, and an all-sky mapping are all required.",
    }


def execute(project_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest, verified = verify_manifest(project_root, manifest_path)
    paths = {
        entry["role"]: _within(project_root, entry["path"])
        for entry in verified
    }
    rows = load_catalog(paths["canonical_catalog_csv"])
    events = collapse_events(rows)
    catalog = summarize_catalog(rows, events)
    control = run_positive_control(events)
    exposure = inspect_exposure(paths["integrated_exposure_hdf5"])

    _, verified_after = verify_manifest(project_root, manifest_path)
    if verified_after != verified:
        raise M0Error("raw inputs changed while the analysis was running")

    integrity_gate = catalog["matches_published_release_counts"]
    control_gate = control["passes_recovery_gate"]
    window_gate = exposure["passes_window_gate"]
    window_input_ready = integrity_gate and control_gate and window_gate
    # M0 is only a feasibility audit. A complete, separately committed M1 statistical
    # preregistration is deliberately absent, so this program can never authorize an
    # unknown-source scan.
    eligible = False
    if not integrity_gate:
        verdict = "CATALOG_INTEGRITY_FAILURE"
    elif not control_gate:
        verdict = "POSITIVE_CONTROL_FAILURE"
    elif not window_gate:
        verdict = "BLOCKED_AT_WINDOW_FUNCTION_GATE"
    else:
        verdict = "WINDOW_INPUT_READY_M1_PREREGISTRATION_REQUIRED"
    return {
        "schema_version": 1,
        "executed_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_doi": manifest["dataset_doi"],
        "journal_doi": manifest["journal_doi"],
        "provenance": {
            "passes": True,
            "verified_files": verified,
            "post_analysis_reverified": True,
        },
        "catalog": catalog,
        "known_period_positive_control": control,
        "exposure_window": exposure,
        "gates": {
            "input_integrity": integrity_gate,
            "known_period_recovery": control_gate,
            "time_resolved_observing_window": window_gate,
            "complete_m1_preregistration": False,
        },
        "window_input_ready_for_m1_design": window_input_ready,
        "discovery_scan_eligible": eligible,
        "discovery_scan_status": "NOT_RUN",
        "candidate_identifiers_disclosed": False,
        "verdict": verdict,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="project directory (defaults to the parent of scripts/)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="provenance manifest (defaults to data/provenance.json under project root)",
    )
    parser.add_argument("--output", type=Path, help="write the aggregate JSON result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    manifest_path = (args.manifest or project_root / "data" / "provenance.json").resolve()
    try:
        result = execute(project_root, manifest_path)
    except (M0Error, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "INPUT_FAILURE", "error": str(exc)}, indent=2))
        return 1

    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
