"""Small, dependency-free provenance contracts for derived cache files.

The science scripts use human-readable tags in filenames.  A tag is a label,
not proof that the bytes were produced from the same time window or object
list.  This module pairs each cache with a SHA-256 sidecar and refuses legacy,
partial, tampered, or differently parameterised entries.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_CONTRACT_SCHEMA = 1
TAG_MAX_LENGTH = 64
_TAG_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_-]{0,62}[A-Za-z0-9])?")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def validated_tag(value: str) -> str:
    """Return a strict filename-safe science-run tag or fail before I/O.

    Tags are deliberately a smaller language than general filenames.  They may
    contain ASCII letters, digits, internal ``_``/``-`` characters, must begin
    and end with an alphanumeric character, and are capped to keep every derived
    cache/output path portable.  Path separators, dots (including ``..``), drive
    syntax, whitespace, and Windows device names are therefore impossible.
    """
    if not isinstance(value, str):
        raise ValueError("run tag must be a string")
    if len(value) > TAG_MAX_LENGTH or _TAG_PATTERN.fullmatch(value) is None:
        raise ValueError(
            "run tag must be 1-64 ASCII letters/digits with only internal '_' "
            "or '-' characters; path separators, dots, spaces, and punctuation "
            "are not allowed"
        )
    if value.upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"run tag {value!r} is a reserved filename")
    return value


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sidecar_path(payload_path: Path) -> Path:
    return payload_path.with_name(payload_path.name + ".meta.json")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def write_cache(
    payload_path: Path,
    payload: bytes,
    *,
    kind: str,
    contract: dict[str, Any],
    row_count: int | None = None,
    metadata_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically write payload then proof sidecar.

    A crash between the two writes leaves an unproved payload.  Readers reject
    it rather than mistaking an incomplete write for a valid empty result.
    """
    metadata: dict[str, Any] = {
        "schema_version": CACHE_CONTRACT_SCHEMA,
        "kind": kind,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "payload_file": payload_path.name,
        "payload_sha256": sha256_bytes(payload),
        "payload_bytes": len(payload),
        "contract": contract,
    }
    if row_count is not None:
        metadata["row_count"] = int(row_count)
    if metadata_extra:
        overlap = set(metadata) & set(metadata_extra)
        if overlap:
            raise ValueError(f"metadata_extra would replace protected keys: {sorted(overlap)}")
        metadata.update(metadata_extra)
    atomic_write(payload_path, payload)
    atomic_write(
        sidecar_path(payload_path),
        (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return metadata


def load_cache_contract(
    payload_path: Path,
    *,
    kind: str,
    expected_contract: dict[str, Any],
) -> dict[str, Any] | None:
    """Return verified metadata, ``None`` when no cache exists, or fail closed."""
    sidecar = sidecar_path(payload_path)
    if not payload_path.exists() and not sidecar.exists():
        return None
    if not payload_path.exists() or not sidecar.exists():
        raise RuntimeError(
            f"unproved cache {payload_path}: payload and sidecar must both exist; "
            "use a new date-derived tag or move the legacy cache aside"
        )
    try:
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid cache sidecar {sidecar}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise RuntimeError(f"invalid cache sidecar {sidecar}: expected an object")
    if metadata.get("schema_version") != CACHE_CONTRACT_SCHEMA:
        raise RuntimeError(f"unsupported cache contract in {sidecar}")
    if metadata.get("kind") != kind:
        raise RuntimeError(
            f"cache kind mismatch for {payload_path}: {metadata.get('kind')!r} != {kind!r}"
        )
    if metadata.get("payload_file") != payload_path.name:
        raise RuntimeError(f"cache payload name mismatch in {sidecar}")
    if metadata.get("contract") != expected_contract:
        raise RuntimeError(
            f"cache input mismatch for tag-derived {payload_path.name}; "
            f"cached={metadata.get('contract')!r}, requested={expected_contract!r}. "
            "Use a unique date-derived tag."
        )
    actual = sha256_file(payload_path)
    if metadata.get("payload_sha256") != actual:
        raise RuntimeError(f"cache digest mismatch for {payload_path}")
    try:
        if int(metadata.get("payload_bytes")) != payload_path.stat().st_size:
            raise RuntimeError(f"cache byte-count mismatch for {payload_path}")
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid cache byte count in {sidecar}") from exc
    return metadata


def load_proved_output(
    payload_path: Path,
    summary_path: Path,
    *,
    kind: str,
    proof_field: str = "candidate_output_provenance",
) -> dict[str, Any]:
    """Authenticate an atomic output and the summary that declares its proof.

    This catches both crash orderings: new/partial payload with an old sidecar,
    and a completed new payload+sidecar paired with an old summary.
    """
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        proof = summary[proof_field]
        contract = proof["contract"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"{summary_path} does not prove completed output {payload_path}"
        ) from exc
    if not isinstance(summary, dict) or not isinstance(proof, dict):
        raise RuntimeError(f"invalid output proof in {summary_path}")
    if proof.get("kind") != kind:
        raise RuntimeError(f"output proof kind mismatch in {summary_path}")
    if not isinstance(contract, dict):
        raise RuntimeError(f"invalid output contract in {summary_path}")
    if kind in {"m1_candidate_output", "m2_candidate_output"}:
        required_digests = {
            "source_pool_summary_sha256",
            "history_cache_provenance_sha256",
            "frozen_tns_provenance_sha256",
            "current_tns_provenance_sha256",
        }
        if kind == "m2_candidate_output":
            required_digests.add("xmatch_provenance_sha256")
        if contract.get("contract_schema_version") != 1 or any(
            not isinstance(contract.get(field), str)
            or re.fullmatch(r"[0-9a-f]{64}", contract[field]) is None
            for field in required_digests
        ):
            raise RuntimeError(f"incomplete candidate input contract in {summary_path}")
        try:
            summary_digests = {
                "history_cache_provenance_sha256": canonical_digest(
                    summary["history_cache_provenance"]
                ),
                "frozen_tns_provenance_sha256": canonical_digest(
                    summary["tns_snapshot_provenance"]["frozen_dedupe"]
                ),
                "current_tns_provenance_sha256": canonical_digest(
                    summary["tns_snapshot_provenance"]["operational_current"]
                ),
            }
            if kind == "m2_candidate_output":
                summary_digests["xmatch_provenance_sha256"] = canonical_digest(
                    summary["xmatch_cache_provenance"]
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                f"candidate summary input provenance is invalid in {summary_path}"
            ) from exc
        if any(contract[field] != digest for field, digest in summary_digests.items()):
            raise RuntimeError(
                f"candidate summary inputs do not match its proof in {summary_path}"
            )
    if summary.get("tag") != contract.get("tag"):
        raise RuntimeError(f"output tag mismatch in {summary_path}")
    if summary.get("n_candidates") != proof.get("row_count"):
        raise RuntimeError(f"output row-count mismatch in {summary_path}")
    if summary.get("history_jd_ceiling") != contract.get("history_jd_ceiling"):
        raise RuntimeError(f"output history ceiling mismatch in {summary_path}")
    actual = load_cache_contract(
        payload_path,
        kind=kind,
        expected_contract=contract,
    )
    if actual is None or actual != proof:
        raise RuntimeError(
            f"output proof in {summary_path} does not match {payload_path}"
        )
    return proof
