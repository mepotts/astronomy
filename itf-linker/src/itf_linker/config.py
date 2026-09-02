"""Paths and external endpoints. No credentials: every source here is public and anonymous."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Project root = .../itf-linker (this file is src/itf_linker/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# The unattended archive runs from a pinned operations checkout while its irreplaceable
# rolling state lives elsewhere.  Keep the ordinary developer default, but allow the
# scheduler to name that state directory explicitly so changing a development branch can
# never change either the archive code or its storage location.
DATA_DIR = Path(os.environ.get("ITF_DATA_DIR", PROJECT_ROOT / "data")).expanduser().resolve()
RAW_DIR = DATA_DIR / "raw"          # gitignored: the ~135 MB ITF snapshot
PARQUET_DIR = DATA_DIR / "parquet"  # gitignored: typed derivatives
MPEC_DIR = DATA_DIR / "mpec"        # gitignored: cached MPEC HTML

ITF_GZ = RAW_DIR / "itf.txt.gz"
ITF_PROVENANCE = RAW_DIR / "itf.provenance.json"
ITF_PARQUET = PARQUET_DIR / "itf_observations.parquet"
TRACKLET_PARQUET = PARQUET_DIR / "itf_tracklets.parquet"

# M2 vetting. The cache is what makes a vetting run reproducible without asking MPChecker,
# SkyBoT and JPL to recompute answers they have already given.
VET_CACHE_DIR = DATA_DIR / "vet-cache"
VET_ASTROMETRY = DATA_DIR / "vet-astrometry.json"

# M3 linking. A proposed link's astrometry cannot be re-extracted by designation the way
# M1's could: the link's identifier does not exist in the ITF, so the assembled and
# relabelled 80-column lines are written once and reused by the vetting stage.
VET_ASTROMETRY_LINKS = DATA_DIR / "vet-astrometry-links.json"

# --- Endpoints (read-only; no writes are ever performed against these) -------------
ITF_URL = "https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz"
OBSCODES_URL = "https://www.minorplanetcenter.net/iau/lists/ObsCodes.html"
MPEC_URL_TEMPLATE = "https://www.minorplanetcenter.net/mpec/K{yy}/{packed}.html"

USER_AGENT = "itf-linker/0.1 (+https://github.com/; matthew.e.potts@gmail.com) read-only"

# Network and local clocks can differ slightly, but an archive generation hours or days
# in the future can pin lexical "latest" selection and starve every real generation.
SNAPSHOT_FUTURE_TOLERANCE = timedelta(minutes=5)
SNAPSHOT_ID_FORMAT = "%Y%m%dT%H%M%SZ"

#: The three July-2026 identification MPECs the M0 kill-check replays.
KILL_CHECK_MPECS = ("K26O40", "K26O57", "K26O86")


def validate_existing_snapshot_chain(
    data_dir: Path = DATA_DIR,
    *,
    required_full_snapshot: str | None = None,
) -> tuple[int, int]:
    """Prove an unattended run points at an established, recoverable archive.

    A typo in ``ITF_DATA_DIR`` must fail before the fetch: silently starting a fresh
    baseline would break continuity in the one dataset this project cannot regenerate.
    Bootstrap is an explicit shell-script escape hatch and never calls this function.
    """
    snapshots = data_dir / "snapshots"
    if not snapshots.is_dir():
        raise RuntimeError(f"snapshot directory does not exist: {snapshots}")

    state_directories = [
        directory
        for directory in snapshots.iterdir()
        if directory.is_dir()
        and any(
            (directory / filename).exists()
            for filename in ("manifest.json", "delta.parquet", "observations.parquet")
        )
    ]
    now = datetime.now(UTC)
    for directory in state_directories:
        try:
            snapshot_stamp = datetime.strptime(
                directory.name, SNAPSHOT_ID_FORMAT
            ).replace(tzinfo=UTC)
        except ValueError as exc:
            raise RuntimeError(f"invalid snapshot directory id: {directory}") from exc
        if snapshot_stamp > now + SNAPSHOT_FUTURE_TOLERANCE:
            raise RuntimeError(f"future-dated snapshot directory: {directory}")

    record_directories = [
        directory
        for directory in state_directories
        if (directory / "manifest.json").is_file()
        and (directory / "delta.parquet").is_file()
    ]
    if not record_directories:
        raise RuntimeError(
            f"expected an established snapshot chain, found {len(record_directories)} "
            f"complete record(s) under {snapshots}"
        )

    # File presence alone is not continuity: a truncated JSON or zero-byte file would make
    # the next run look protected while leaving no recoverable parent. Read only Parquet
    # footers here, so validating a 175 MB key set stays cheap.
    import pyarrow as pa
    import pyarrow.parquet as pq

    required_keyset_schema = {
        "obs_key": pa.uint64(),
        "desig": pa.large_string(),
        "obscode": pa.large_string(),
        "mjd": pa.float64(),
    }
    required_delta_schema = {
        **required_keyset_schema,
        "change": pa.int8(),
    }

    def schema_matches(schema: pa.Schema, expected: dict[str, pa.DataType]) -> bool:
        return all(
            name in schema.names and schema.field(name).type == expected_type
            for name, expected_type in expected.items()
        )

    full_keysets: list[Path] = []
    for directory in record_directories:
        manifest_path = directory / "manifest.json"
        delta_path = directory / "delta.parquet"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid snapshot manifest: {manifest_path}") from exc
        if not isinstance(manifest, dict) or manifest.get("snapshot_id") != directory.name:
            raise RuntimeError(f"snapshot manifest identity mismatch: {manifest_path}")
        created_utc = manifest.get("created_utc")
        if not isinstance(created_utc, str):
            # This is corrupt external archive state, not a caller argument type error.
            raise RuntimeError(  # noqa: TRY004
                f"snapshot manifest has no creation timestamp: {manifest_path}"
            )
        try:
            created = datetime.fromisoformat(created_utc)
        except ValueError as exc:
            raise RuntimeError(
                f"snapshot manifest has an invalid creation timestamp: {manifest_path}"
            ) from exc
        if created.tzinfo is None or created.utcoffset() is None:
            raise RuntimeError(
                f"snapshot manifest creation timestamp has no timezone: {manifest_path}"
            )
        if created.astimezone(UTC) > now + SNAPSHOT_FUTURE_TOLERANCE:
            raise RuntimeError(
                f"snapshot manifest has a future creation timestamp: {manifest_path}"
            )
        try:
            delta_file = pq.ParquetFile(delta_path)
        except Exception as exc:
            raise RuntimeError(f"invalid snapshot delta parquet: {delta_path}") from exc
        if not schema_matches(delta_file.schema_arrow, required_delta_schema):
            raise RuntimeError(f"snapshot delta has an unexpected schema: {delta_path}")
        byte_manifest = manifest.get("bytes")
        expected_delta_bytes = (
            byte_manifest.get("delta.parquet") if isinstance(byte_manifest, dict) else None
        )
        if (
            not isinstance(expected_delta_bytes, int)
            or expected_delta_bytes <= 0
            or delta_path.stat().st_size != expected_delta_bytes
        ):
            raise RuntimeError(f"snapshot delta size disagrees with manifest: {delta_path}")

        keyset = directory / "observations.parquet"
        if keyset.is_file():
            try:
                keyset_file = pq.ParquetFile(keyset)
            except Exception as exc:
                raise RuntimeError(f"invalid snapshot key-set parquet: {keyset}") from exc
            if not schema_matches(keyset_file.schema_arrow, required_keyset_schema):
                raise RuntimeError(f"snapshot key set has an unexpected schema: {keyset}")
            expected_rows = manifest.get("observations")
            expected_keyset_bytes = (
                byte_manifest.get("observations.parquet")
                if isinstance(byte_manifest, dict)
                else None
            )
            if (
                not isinstance(expected_rows, int)
                or expected_rows <= 0
                or keyset_file.metadata.num_rows != expected_rows
                or not isinstance(expected_keyset_bytes, int)
                or expected_keyset_bytes <= 0
                or keyset.stat().st_size != expected_keyset_bytes
            ):
                raise RuntimeError(
                    f"snapshot key set count/size disagrees with manifest: {keyset}"
                )
            full_keysets.append(keyset)

    if not full_keysets:
        raise RuntimeError(
            f"snapshot chain has no retained observations.parquet key set: {snapshots}"
        )
    if required_full_snapshot is not None:
        required = snapshots / required_full_snapshot / "observations.parquet"
        if required not in full_keysets:
            raise RuntimeError(
                "snapshot returned by this run is not a complete, validated full record: "
                f"{required_full_snapshot}"
            )
    return len(record_directories), len(full_keysets)


def ensure_dirs() -> None:
    for d in (RAW_DIR, PARQUET_DIR, MPEC_DIR):
        d.mkdir(parents=True, exist_ok=True)
