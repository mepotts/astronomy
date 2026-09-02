"""Freeze one archive generation as M14's matched raw/full-Parquet ITF input pair.

The daily archive stores an immutable raw ``itf.txt.gz`` and a slim observations keyset.
The attribution sweep needs the full astrometric columns, while Find_Orb line extraction
needs the matching raw 80-column records.  This script reparses the archived raw file into
a run-local full Parquet and binds both files, the archive manifest, and parser source to a
single fingerprint.  It is local-only and performs no network or publication action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import polars as pl
from m14_prepare import M14DataError, file_hashes, iso_utc, utc_now, write_json_atomic

from itf_linker.ingest.parse import parse_itf

M14_RUNS = ROOT / "data" / "m14" / "runs"
REQUIRED_COLUMNS = {"desig", "obscode", "mjd", "ra_deg", "dec_deg", "mag"}


def canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_snapshot_id(snapshot_id: str) -> None:
    try:
        parsed = datetime.strptime(snapshot_id, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise M14DataError(f"invalid archive snapshot id: {snapshot_id!r}") from exc
    if parsed > utc_now():
        raise M14DataError(f"archive snapshot id is future-dated: {snapshot_id}")


def load_archive_manifest(snapshot_id: str) -> tuple[Path, dict[str, Any]]:
    validate_snapshot_id(snapshot_id)
    source = ROOT / "data" / "snapshots" / snapshot_id
    manifest_path = source / "manifest.json"
    raw_path = source / "itf.txt.gz"
    if not manifest_path.is_file() or not raw_path.is_file():
        raise M14DataError(f"archive generation is incomplete: {source}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("snapshot_id") != snapshot_id:
        raise M14DataError("archive manifest snapshot_id does not match its directory")
    try:
        observations = int(manifest["observations"])
        expected_raw_bytes = int(manifest["bytes"]["itf.txt.gz"])
        provenance_bytes = int(manifest["provenance"]["size_bytes"])
    except (KeyError, TypeError, ValueError) as exc:
        raise M14DataError("archive manifest lacks required counts/byte proofs") from exc
    if observations <= 0 or expected_raw_bytes <= 0 or provenance_bytes != expected_raw_bytes:
        raise M14DataError("archive manifest has invalid observation/raw-byte accounting")
    if raw_path.stat().st_size != expected_raw_bytes:
        raise M14DataError("archived raw ITF size does not match its manifest")
    return source, manifest


def validate_frozen(manifest_path: Path) -> dict[str, Any]:
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("milestone") != "M14":
        raise M14DataError(f"invalid M14 frozen-input manifest: {manifest_path}")
    base = manifest_path.parent
    for key in ("raw", "parquet"):
        proof = document.get(key)
        if not isinstance(proof, dict) or not isinstance(proof.get("filename"), str):
            raise M14DataError(f"frozen-input manifest has no {key} proof")
        path = base / proof["filename"]
        if not path.is_file():
            raise M14DataError(f"frozen M14 {key} input is missing: {path}")
        hashes = file_hashes(path)
        if hashes["bytes"] != proof.get("bytes") or hashes["sha256"] != proof.get("sha256"):
            raise M14DataError(f"frozen M14 {key} input failed its digest proof")
    fingerprint_source = {key: value for key, value in document.items() if key != "fingerprint"}
    if canonical_json_digest(fingerprint_source) != document.get("fingerprint"):
        raise M14DataError("frozen-input manifest fingerprint does not reproduce")
    return document


def freeze(snapshot_id: str) -> dict[str, Any]:
    source, archive_manifest = load_archive_manifest(snapshot_id)
    destination = M14_RUNS / snapshot_id / "inputs"
    proof_path = destination / "itf-input-manifest.json"
    raw_destination = destination / "itf.txt.gz"
    parquet_destination = destination / "itf_observations.parquet"
    existing = [path.exists() for path in (proof_path, raw_destination, parquet_destination)]
    if any(existing):
        if not all(existing):
            raise M14DataError(f"partial frozen M14 input set: {destination}")
        return validate_frozen(proof_path)

    destination.mkdir(parents=True, exist_ok=True)
    raw_temporary = destination / f".itf.txt.gz.tmp-{os.getpid()}"
    parquet_temporary = destination / f".itf_observations.tmp-{os.getpid()}.parquet"
    try:
        shutil.copyfile(source / "itf.txt.gz", raw_temporary)
        source_raw = file_hashes(source / "itf.txt.gz")
        copied_raw = file_hashes(raw_temporary)
        if source_raw != copied_raw:
            raise M14DataError("run-local raw ITF copy does not match the archive source")
        ingest = parse_itf(src=raw_temporary, dest=parquet_temporary)
        if ingest["observations"] != int(archive_manifest["observations"]):
            raise M14DataError(
                "full M14 parse count does not match the archive generation manifest"
            )
        schema = pl.read_parquet_schema(parquet_temporary)
        missing = REQUIRED_COLUMNS - set(schema)
        if missing:
            raise M14DataError(f"full M14 Parquet lacks required columns: {sorted(missing)}")
        parquet_proof = file_hashes(parquet_temporary)
        raw_temporary.replace(raw_destination)
        parquet_temporary.replace(parquet_destination)

        source_files = {
            "ingest_parse.py": file_hashes(ROOT / "src" / "itf_linker" / "ingest" / "parse.py"),
            "mpc80.py": file_hashes(ROOT / "src" / "itf_linker" / "mpc80.py"),
        }
        document: dict[str, Any] = {
            "schema": 1,
            "milestone": "M14",
            "snapshot_id": snapshot_id,
            "generated_utc": iso_utc(utc_now()),
            "archive_manifest": {
                "filename": str((source / "manifest.json").relative_to(ROOT)),
                "sha256": file_hashes(source / "manifest.json")["sha256"],
                "observations": int(archive_manifest["observations"]),
                "provenance": archive_manifest["provenance"],
            },
            "raw": {"filename": raw_destination.name, **source_raw},
            "parquet": {
                "filename": parquet_destination.name,
                **parquet_proof,
                "observations": ingest["observations"],
                "raw_lines": ingest["raw_lines"],
                "dropped_lines": ingest["dropped_lines"],
                "schema": {name: str(dtype) for name, dtype in schema.items()},
            },
            "parser_sources": source_files,
        }
        document["fingerprint"] = canonical_json_digest(document)
        write_json_atomic(proof_path, document)
        return document
    finally:
        for temporary in (raw_temporary, parquet_temporary):
            if temporary.exists():
                temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    document = freeze(args.snapshot_id)
    print(
        f"M14 froze ITF snapshot {document['snapshot_id']}: "
        f"{document['parquet']['observations']:,} observations; "
        f"fingerprint {document['fingerprint']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except M14DataError as error:
        print(f"M14 ITF freeze refused: {error}", file=sys.stderr)
        raise SystemExit(1) from error
