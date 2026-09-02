"""Verified, immutable TNS catalogue snapshots for candidate reproduction.

The public TNS CSV exposes discovery time but not the time a report became
public.  Consequently the strict reproducible claim is a discovery-date-bounded
cross-match against a named registry snapshot, not an exact reconstruction of
the TNS registry at an earlier instant.  Nightly runs require the snapshot to be
harvested shortly after their alert-history ceiling and pin its digest forever.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA = 1
TNS_SNAPSHOT_MAX_LAG_DAYS = 1.0
REQUIRED_COLUMNS = {"ID", "Name", "RA", "DEC", "Discovery Date (UT)"}


def datetime_to_jd(value: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp() / 86400.0 + 2440587.5


def parse_utc(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def discovery_jd(row: dict[str, str]) -> float:
    try:
        return datetime_to_jd(parse_utc(row["Discovery Date (UT)"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"TNS row {row.get('ID', '<unknown>')} has no valid Discovery Date (UT)"
        ) from exc


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _tns_dir() -> Path:
    # Kept local rather than importing tnscommon so snapshot verification remains
    # usable in the requests-only cache CI job.
    return Path(__file__).resolve().parents[1] / "data" / "tns"


def _safe_snapshot_path(tns_dir: Path, relative: str) -> Path:
    root = (tns_dir / "snapshots").resolve()
    candidate = (tns_dir / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"TNS snapshot path escapes {root}: {relative!r}") from exc
    return candidate


def read_snapshot(
    *,
    required_coverage_jd: float,
    reference: dict[str, Any] | None = None,
    max_lag_days: float = TNS_SNAPSHOT_MAX_LAG_DAYS,
    tns_dir: Path | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Load a verified frozen snapshot that brackets the requested ceiling.

    ``reference`` pins an immutable snapshot recorded by a pool manifest.  When
    omitted, the latest pointer is used and its immutable target is returned.
    """
    directory = Path(tns_dir) if tns_dir is not None else _tns_dir()
    if reference is None:
        latest = directory / "tns_12mo.meta.json"
        try:
            metadata = json.loads(latest.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeError(
                "no proved TNS snapshot; run m1_tns_harvest.py after the window closes"
            ) from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid TNS snapshot pointer {latest}: {exc}") from exc
    else:
        metadata = dict(reference)
    required = {
        "schema_version",
        "snapshot_id",
        "snapshot_file",
        "snapshot_sha256",
        "row_count",
        "harvested_at_utc",
        "harvested_at_jd",
        "registry_observed_at_utc_min",
        "registry_observed_at_utc_max",
        "registry_observed_at_jd_min",
        "registry_observed_at_jd_max",
        "discovery_start_date",
        "discovery_end_exclusive",
    }
    if not isinstance(metadata, dict) or not required.issubset(metadata):
        missing = sorted(required - set(metadata if isinstance(metadata, dict) else {}))
        raise RuntimeError(f"invalid TNS snapshot metadata; missing {missing}")
    if metadata.get("schema_version") != SNAPSHOT_SCHEMA:
        raise RuntimeError("unsupported TNS snapshot metadata schema")
    try:
        harvested_jd = float(metadata["harvested_at_jd"])
        observed_min_jd = float(metadata["registry_observed_at_jd_min"])
        observed_max_jd = float(metadata["registry_observed_at_jd_max"])
        ceiling = float(required_coverage_jd)
        lag = observed_max_jd - ceiling
    except (TypeError, ValueError) as exc:
        raise RuntimeError("invalid TNS snapshot/coverage JD") from exc
    if not all(
        math.isfinite(v)
        for v in (harvested_jd, observed_min_jd, observed_max_jd, ceiling, lag)
    ):
        raise RuntimeError("non-finite TNS snapshot/coverage JD")
    if observed_min_jd < ceiling - 1e-8:
        raise RuntimeError(
            f"TNS snapshot {metadata['snapshot_id']} began scanning before the "
            f"history ceiling by {ceiling - observed_min_jd:.5f} d; harvest after "
            "the window closes"
        )
    if lag > max_lag_days:
        raise RuntimeError(
            f"TNS snapshot {metadata['snapshot_id']} is {lag:.5f} d after the "
            f"history ceiling (limit {max_lag_days:.5f} d); the exact registry "
            "state is no longer reconstructible from the rolling CSV. Run a new "
            "window with a fresh snapshot."
        )
    try:
        coverage_end_jd = datetime_to_jd(
            parse_utc(str(metadata["discovery_end_exclusive"]) + "T00:00:00Z")
        )
    except ValueError as exc:
        raise RuntimeError("invalid TNS discovery_end_exclusive") from exc
    if coverage_end_jd <= ceiling:
        raise RuntimeError(
            f"TNS snapshot date query ends at JD {coverage_end_jd}, which does not "
            f"cover inclusive history ceiling {ceiling}"
        )
    snapshot = _safe_snapshot_path(directory, str(metadata["snapshot_file"]))
    try:
        payload = snapshot.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"cannot read pinned TNS snapshot {snapshot}: {exc}") from exc
    if _sha256(payload) != metadata["snapshot_sha256"]:
        raise RuntimeError(f"TNS snapshot digest mismatch for {snapshot}")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        columns = set(reader.fieldnames or [])
        if not REQUIRED_COLUMNS.issubset(columns):
            raise RuntimeError(
                f"TNS snapshot lacks columns {sorted(REQUIRED_COLUMNS - columns)}"
            )
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"TNS snapshot is not UTF-8: {snapshot}") from exc
    try:
        expected_rows = int(metadata["row_count"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("invalid TNS snapshot row count") from exc
    if len(rows) != expected_rows:
        raise RuntimeError(
            f"TNS snapshot row-count mismatch: {len(rows)} != {expected_rows}"
        )
    # Fail the whole run rather than silently exempting malformed catalogue rows.
    for row in rows:
        discovery_jd(row)
        if not str(row.get("RA", "")).strip() or not str(row.get("DEC", "")).strip():
            raise RuntimeError(f"TNS row {row.get('ID')} has no position")
    provenance = {
        key: metadata[key]
        for key in sorted(
            required
            | {"source_url", "date_semantics", "month_inputs"}
        )
        if key in metadata
    }
    provenance["snapshot_lag_days"] = lag
    provenance["as_of_rule"] = "Discovery Date (UT) <= history_jd_ceiling"
    return rows, provenance


def rows_discovered_as_of(
    rows: list[dict[str, str]], jd_ceiling: float
) -> list[dict[str, str]]:
    ceiling = float(jd_ceiling)
    return [row for row in rows if discovery_jd(row) <= ceiling]
