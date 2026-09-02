"""Fetch and safely cache full ZTF alert histories from Fink.

Fink's ``/api/v1/objects`` returns the complete alert history plus broker
cross-matches. Its per-alert ``d:tns`` value is stamped at ingest rather than
back-filled, which is what makes the positive-control rewind possible. The
payload stays at ``data/fink/<oid>.json`` so the existing analysis scripts
remain compatible. A new sidecar at
``data/fink/_meta/<oid>.json`` records the HTTP result, fetch time, source,
validation status, row count, and payload digest.

An empty history is scientifically meaningful only when it came from a valid
HTTP 200 response. Network failures, non-200 responses, and malformed JSON are
therefore never cached as ``[]``. Legacy empty arrays have no success
provenance; they are moved (not deleted) under ``data/fink/_quarantine`` and are
refetched when requested.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import DATA, session  # noqa: E402

FINK_OBJECTS = "https://api.ztf.fink-portal.org/api/v1/objects"
CACHE = DATA / "fink"
CACHE_SCHEMA_VERSION = 1
FETCH_ATTEMPTS = 4
HISTORY_MAX_AGE_SECONDS = 24 * 60 * 60
RESOLVE_MAX_AGE_SECONDS = 24 * 60 * 60
UNIX_EPOCH_JD = 2440587.5
_SAFE_OID = re.compile(r"^[A-Za-z0-9_.-]+$")


class FinkFetchError(RuntimeError):
    """A Fink response could not be proven to be a successful history fetch."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _checked_max_age(max_age_seconds: float) -> float:
    value = float(max_age_seconds)
    if not math.isfinite(value) or value < 0:
        raise ValueError("max_age_seconds must be a finite non-negative number")
    return value


def _metadata_time(meta: dict) -> datetime | None:
    return (_parse_utc(meta.get("fetched_at_utc"))
            or _parse_utc(meta.get("legacy_payload_mtime_utc")))


def _metadata_is_fresh(meta: dict, max_age_seconds: float) -> bool:
    max_age = _checked_max_age(max_age_seconds)
    fetched = _metadata_time(meta)
    if fetched is None:
        return False
    age = (datetime.now(timezone.utc) - fetched).total_seconds()
    if age < 0:
        # Future timestamps can otherwise make copied/tampered cache entries
        # appear fresh indefinitely.  Refetch and replace them with observed
        # HTTP-success provenance.
        return False
    return age <= max_age


def _datetime_to_jd(value: datetime) -> float:
    return value.timestamp() / 86400.0 + UNIX_EPOCH_JD


def _checked_coverage_jd(required_coverage_jd: float | None) -> float | None:
    if required_coverage_jd is None:
        return None
    value = float(required_coverage_jd)
    if not math.isfinite(value):
        raise ValueError("required_coverage_jd must be finite")
    now_jd = _datetime_to_jd(datetime.now(timezone.utc))
    if value > now_jd:
        raise ValueError(
            f"required_coverage_jd {value} is in the future (current JD {now_jd})"
        )
    return value


def _metadata_covers(meta: dict, required_coverage_jd: float | None) -> bool:
    if required_coverage_jd is None:
        return True
    # A pre-contract nonempty payload remains useful for descriptive reads, but
    # its filesystem mtime is not evidence of when Fink was queried.  A
    # completeness-dependent run must refresh it once and obtain a real
    # fetched_at timestamp from this writer.
    if meta.get("status") == "legacy_nonempty":
        return False
    fetched = _parse_utc(meta.get("fetched_at_utc"))
    return fetched is not None and _datetime_to_jd(fetched) >= required_coverage_jd


def _check_oid(oid: str) -> str:
    oid = str(oid)
    if not oid or not _SAFE_OID.fullmatch(oid):
        raise ValueError(f"unsafe Fink object id: {oid!r}")
    return oid


def _payload_path(oid: str) -> Path:
    return CACHE / f"{_check_oid(oid)}.json"


def _meta_path(oid: str) -> Path:
    return CACHE / "_meta" / f"{_check_oid(oid)}.json"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        tmp.write_text(text, encoding="utf-8", newline="\n")
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _validate_records(raw: Any, expected_oids: set[str]) -> list[dict]:
    if not isinstance(raw, list):
        raise ValueError(f"expected a JSON list, got {type(raw).__name__}")
    for index, record in enumerate(raw):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} is not a JSON object")
        oid = record.get("i:objectId")
        if not isinstance(oid, str) or oid not in expected_oids:
            raise ValueError(
                f"record {index} has unexpected i:objectId {oid!r}"
            )
        required_numeric = ("i:jd", "i:candid", "i:magpsf", "i:fid", "i:ra", "i:dec")
        numeric: dict[str, float] = {}
        for field in required_numeric:
            value = record.get(field)
            if isinstance(value, bool):
                raise ValueError(f"record {index} has non-numeric {field}")
            try:
                numeric[field] = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"record {index} has non-numeric {field}") from exc
            if not math.isfinite(numeric[field]):
                raise ValueError(f"record {index} has non-finite {field}")
        if numeric["i:jd"] < 2_000_000:
            raise ValueError(f"record {index} has implausible i:jd")
        if numeric["i:candid"] <= 0 or not numeric["i:candid"].is_integer():
            raise ValueError(f"record {index} has invalid i:candid")
        if int(numeric["i:fid"]) not in (1, 2, 3) or not numeric["i:fid"].is_integer():
            raise ValueError(f"record {index} has invalid i:fid")
        if not (0 <= numeric["i:ra"] <= 360 and -90 <= numeric["i:dec"] <= 90):
            raise ValueError(f"record {index} has invalid sky coordinates")
        isdiffpos = str(record.get("i:isdiffpos", "")).strip().lower()
        if isdiffpos not in {"t", "f", "true", "false", "1", "0"}:
            raise ValueError(f"record {index} has invalid i:isdiffpos")
        scores = []
        for field in ("i:drb", "i:rb"):
            try:
                score = float(record.get(field))
            except (TypeError, ValueError):
                continue
            if math.isfinite(score):
                scores.append(score)
        if not scores:
            raise ValueError(f"record {index} has neither numeric i:drb nor i:rb")
    return raw


def _write_cache(
    oid: str,
    records: list[dict],
    *,
    request_mode: str,
    requested_object_count: int,
) -> None:
    """Persist only a response already validated from an HTTP 200 request."""
    oid = _check_oid(oid)
    payload = json.dumps(records, separators=(",", ":"), allow_nan=True)
    meta = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "object_id": oid,
        "status": "ok_empty" if not records else "ok",
        "fetched_at_utc": _utc_now(),
        "source_url": FINK_OBJECTS,
        "http_status": 200,
        "request_mode": request_mode,
        "requested_object_count": requested_object_count,
        "response_validated": True,
        "row_count": len(records),
        "payload_sha256": _digest(payload),
    }
    fetched = _parse_utc(meta["fetched_at_utc"])
    meta["fetched_at_jd"] = _datetime_to_jd(fetched) if fetched else None
    # Payload first is fail-safe: if interrupted before the sidecar is written,
    # a new empty payload is treated as unproven and refetched.
    _atomic_write(_payload_path(oid), payload)
    _atomic_write(_meta_path(oid), json.dumps(meta, indent=2, sort_keys=True))


def _quarantine(oid: str, reason: str) -> Path:
    """Move suspect cache material aside without deleting it."""
    oid = _check_oid(oid)
    payload_path = _payload_path(oid)
    meta_path = _meta_path(oid)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination = CACHE / "_quarantine" / f"{stamp}_{oid}"
    destination.mkdir(parents=True, exist_ok=False)
    if payload_path.exists():
        payload_path.replace(destination / payload_path.name)
    if meta_path.exists():
        meta_path.replace(destination / "metadata.json")
    _atomic_write(
        destination / "quarantine.json",
        json.dumps(
            {
                "object_id": oid,
                "quarantined_at_utc": _utc_now(),
                "reason": reason,
                "original_payload": str(payload_path),
                "original_metadata": str(meta_path),
            },
            indent=2,
            sort_keys=True,
        ),
    )
    return destination


def _legacy_metadata(oid: str, payload: str, records: list[dict]) -> dict:
    """Adopt a structurally valid nonempty cache written by the old client."""
    payload_path = _payload_path(oid)
    mtime = datetime.fromtimestamp(
        payload_path.stat().st_mtime, tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")
    meta = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "object_id": oid,
        "status": "legacy_nonempty",
        "fetched_at_utc": None,
        "legacy_payload_mtime_utc": mtime,
        "source_url": FINK_OBJECTS,
        # The former writer persisted nonempty data only inside its HTTP-200
        # branch. This is inferred provenance, not a newly observed response.
        "http_status": 200,
        "request_mode": "legacy_single_or_batch",
        "requested_object_count": None,
        "response_validated": True,
        "provenance": "inferred_from_pre_sidecar_writer",
        "row_count": len(records),
        "payload_sha256": _digest(payload),
    }
    _atomic_write(_meta_path(oid), json.dumps(meta, indent=2, sort_keys=True))
    return meta


def _metadata_authenticates(
    meta: Any,
    *,
    oid: str,
    payload: str,
    records: list[dict],
) -> bool:
    allowed_statuses = {"ok", "ok_empty", "legacy_nonempty"}
    return (
        isinstance(meta, dict)
        and meta.get("cache_schema_version") == CACHE_SCHEMA_VERSION
        and meta.get("object_id") == oid
        and meta.get("status") in allowed_statuses
        and meta.get("http_status") == 200
        and meta.get("response_validated") is True
        and meta.get("row_count") == len(records)
        and meta.get("payload_sha256") == _digest(payload)
        and ((meta.get("status") == "ok_empty") == (not records))
        and _metadata_time(meta) is not None
    )


def load_cached_history(
    oid: str,
    *,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> list[dict] | None:
    """Return a validated, fresh cache entry or ``None`` when fetch is required."""
    max_age_seconds = _checked_max_age(max_age_seconds)
    required_coverage_jd = _checked_coverage_jd(required_coverage_jd)
    oid = _check_oid(oid)
    payload_path = _payload_path(oid)
    if not payload_path.exists():
        return None

    try:
        payload = payload_path.read_text(encoding="utf-8")
        records = _validate_records(json.loads(payload), {oid})
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _quarantine(oid, f"invalid payload: {exc}")
        return None

    meta_path = _meta_path(oid)
    if not meta_path.exists():
        if not records:
            _quarantine(oid, "legacy empty cache has no HTTP-success provenance")
            return None
        meta = _legacy_metadata(oid, payload, records)
        return records if (
            _metadata_is_fresh(meta, max_age_seconds)
            and _metadata_covers(meta, required_coverage_jd)
        ) else None

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not _metadata_authenticates(
            meta, oid=oid, payload=payload, records=records
        ):
            raise ValueError("metadata does not authenticate this payload")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _quarantine(oid, f"invalid metadata: {exc}")
        return None
    if not _metadata_is_fresh(meta, max_age_seconds):
        return None
    if not _metadata_covers(meta, required_coverage_jd):
        return None
    return records


def cache_is_usable(
    oid: str,
    *,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> bool:
    """Whether an object has a validated cache entry (empty or nonempty)."""
    return load_cached_history(
        oid,
        max_age_seconds=max_age_seconds,
        required_coverage_jd=required_coverage_jd,
    ) is not None


def history_as_of(records: list[dict], jd_ceiling: float) -> list[dict]:
    """Return only alerts available at an explicit inclusive JD ceiling."""
    ceiling = float(jd_ceiling)
    if not math.isfinite(ceiling):
        raise ValueError("jd_ceiling must be finite")
    return [record for record in records if float(record["i:jd"]) <= ceiling]


def require_single_jd_ceiling(values: list[Any], source: str) -> float:
    """Require one finite history ceiling in a persisted intermediate table."""
    ceilings: set[float] = set()
    for value in values:
        try:
            ceiling = float(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"{source} has a missing/invalid history ceiling") from exc
        if not math.isfinite(ceiling):
            raise RuntimeError(f"{source} has a missing/invalid history ceiling")
        ceilings.add(ceiling)
    if len(ceilings) != 1:
        raise RuntimeError(
            f"{source} must contain exactly one history_jd_ceiling; found "
            f"{sorted(ceilings)}"
        )
    return next(iter(ceilings))


def cache_provenance(oids: list[str]) -> dict:
    """Persist exact per-object inputs plus a convenient aggregate summary."""
    statuses: dict[str, int] = {}
    modes: dict[str, int] = {}
    fetched: list[datetime] = []
    missing: list[str] = []
    object_inputs: dict[str, dict] = {}
    unique_oids = list(dict.fromkeys(_check_oid(oid) for oid in oids))
    for oid in unique_oids:
        path = _meta_path(oid)
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            payload = _payload_path(oid).read_text(encoding="utf-8")
            records = json.loads(payload)
            if not _metadata_authenticates(
                meta, oid=oid, payload=payload, records=records
            ):
                raise ValueError("sidecar does not authenticate current payload")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            missing.append(oid)
            continue
        status = str(meta.get("status", "unknown"))
        mode = str(meta.get("request_mode", "unknown"))
        statuses[status] = statuses.get(status, 0) + 1
        modes[mode] = modes.get(mode, 0) + 1
        timestamp = _metadata_time(meta)
        if timestamp is not None:
            fetched.append(timestamp)
        object_inputs[oid] = {
            key: meta.get(key)
            for key in (
                "cache_schema_version",
                "status",
                "fetched_at_utc",
                "legacy_payload_mtime_utc",
                "source_url",
                "http_status",
                "request_mode",
                "requested_object_count",
                "row_count",
                "payload_sha256",
                "response_validated",
                "provenance",
            )
            if key in meta
        }
    if missing:
        raise FinkFetchError(
            "cannot write output provenance: current cache payload/sidecar failed "
            f"authentication for {len(missing)} object(s), sample={missing[:10]}"
        )
    manifest_payload = json.dumps(
        object_inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return {
        "n_objects": len(unique_oids),
        "n_metadata_missing": len(missing),
        "metadata_missing_sample": missing[:10],
        "statuses": statuses,
        "request_modes": modes,
        "object_inputs": object_inputs,
        "object_inputs_sha256": _digest(manifest_payload),
        "fetched_at_utc_min": (
            min(fetched).isoformat().replace("+00:00", "Z") if fetched else None
        ),
        "fetched_at_utc_max": (
            max(fetched).isoformat().replace("+00:00", "Z") if fetched else None
        ),
    }


def _request_once(
    s: requests.Session, requested_oids: list[str], timeout: int
) -> list[dict]:
    r = s.post(
        FINK_OBJECTS,
        json={
            "objectId": ",".join(requested_oids),
            "output-format": "json",
            "withupperlim": "False",
        },
        timeout=timeout,
    )
    if r.status_code != 200:
        raise FinkFetchError(f"HTTP {r.status_code}")
    try:
        raw = r.json()
    except ValueError as exc:
        raise FinkFetchError(f"malformed JSON: {exc}") from exc
    try:
        return _validate_records(raw, set(requested_oids))
    except ValueError as exc:
        raise FinkFetchError(f"invalid response: {exc}") from exc


def fetch_one(
    s: requests.Session,
    oid: str,
    refresh: bool = False,
    *,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> list[dict]:
    """Fetch one history, failing closed when success cannot be established."""
    oid = _check_oid(oid)
    max_age_seconds = _checked_max_age(max_age_seconds)
    required_coverage_jd = _checked_coverage_jd(required_coverage_jd)
    if not refresh:
        cached = load_cached_history(
            oid,
            max_age_seconds=max_age_seconds,
            required_coverage_jd=required_coverage_jd,
        )
        if cached is not None:
            return cached

    failures: list[str] = []
    for attempt in range(FETCH_ATTEMPTS):
        try:
            records = _request_once(s, [oid], timeout=120)
            _write_cache(
                oid,
                records,
                request_mode="single",
                requested_object_count=1,
            )
            return records
        except (requests.RequestException, FinkFetchError) as exc:
            failures.append(f"attempt {attempt + 1}: {exc}")
        if attempt + 1 < FETCH_ATTEMPTS:
            time.sleep(2 * (attempt + 1))
    raise FinkFetchError(
        f"Fink history fetch failed for {oid}; no empty cache was written "
        f"({'; '.join(failures)})"
    )


def fetch_histories_batch(
    s: requests.Session,
    oids: list[str],
    chunk: int = 60,
    *,
    refresh: bool = False,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> dict[str, list[dict]]:
    """Fetch histories efficiently while proving every empty result separately.

    A valid batch response can prove the rows it contains, but an omitted object
    is ambiguous. Missing objects are therefore retried one at a time; only a
    valid single-object HTTP 200 may create an ``ok_empty`` cache entry.
    """
    max_age_seconds = _checked_max_age(max_age_seconds)
    required_coverage_jd = _checked_coverage_jd(required_coverage_jd)
    unique_oids = list(dict.fromkeys(_check_oid(oid) for oid in oids))
    out: dict[str, list[dict]] = {}
    todo: list[str] = []
    for oid in unique_oids:
        cached = None if refresh else load_cached_history(
            oid,
            max_age_seconds=max_age_seconds,
            required_coverage_jd=required_coverage_jd,
        )
        if cached is None:
            todo.append(oid)
        else:
            out[oid] = cached

    print(f"  fink: {len(out)} validated cached, {len(todo)} to fetch")
    errors: dict[str, str] = {}
    for offset in range(0, len(todo), chunk):
        part = todo[offset : offset + chunk]
        batch_records: list[dict] | None = None
        for attempt in range(3):
            try:
                batch_records = _request_once(s, part, timeout=300)
                break
            except (requests.RequestException, FinkFetchError):
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))

        found: dict[str, list[dict]] = {}
        if batch_records is not None:
            for record in batch_records:
                found.setdefault(record["i:objectId"], []).append(record)
            for oid, records in found.items():
                _write_cache(
                    oid,
                    records,
                    request_mode="batch",
                    requested_object_count=len(part),
                )
                out[oid] = records
            individually = [oid for oid in part if oid not in found]
        else:
            print(
                f"    batch of {len(part)} failed -- falling back to per-object",
                flush=True,
            )
            individually = part

        for oid in individually:
            try:
                out[oid] = fetch_one(
                    s,
                    oid,
                    refresh=True,
                    max_age_seconds=max_age_seconds,
                    required_coverage_jd=required_coverage_jd,
                )
            except FinkFetchError as exc:
                errors[oid] = str(exc)

        if (offset // chunk) % 5 == 0:
            print(
                f"    fink {min(offset + chunk, len(todo))}/{len(todo)}",
                flush=True,
            )

    if errors:
        sample = "; ".join(f"{oid}: {msg}" for oid, msg in list(errors.items())[:3])
        raise FinkFetchError(
            f"{len(errors)} Fink histories could not be verified; aborting the "
            f"science pass. First failures: {sample}"
        )
    return out


def fetch_many(
    oids: list[str],
    refresh: bool = False,
    sleep: float = 0.15,
    *,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> dict[str, list[dict]]:
    s = session()
    out: dict[str, list[dict]] = {}
    unique_oids = list(dict.fromkeys(oids))
    for index, oid in enumerate(unique_oids, 1):
        out[oid] = fetch_one(
            s,
            oid,
            refresh=refresh,
            max_age_seconds=max_age_seconds,
            required_coverage_jd=required_coverage_jd,
        )
        if index % 25 == 0:
            print(f"  fink {index}/{len(unique_oids)}", flush=True)
        time.sleep(sleep)
    return out


def quarantine_legacy_empty_caches() -> int:
    """Quarantine every unproven legacy ``[]`` entry; return the count moved."""
    CACHE.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in sorted(CACHE.glob("ZTF*.json")):
        oid = path.stem
        try:
            payload = path.read_text(encoding="utf-8")
            raw = json.loads(payload)
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if raw == []:
            meta_path = _meta_path(oid)
            proved_empty = False
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    proved_empty = _metadata_authenticates(
                        meta, oid=oid, payload=payload, records=raw
                    )
                except (OSError, UnicodeError, json.JSONDecodeError):
                    proved_empty = False
            if proved_empty:
                continue
            _quarantine(
                oid,
                "bulk migration: empty cache has no valid HTTP-success provenance",
            )
            moved += 1
    return moved


CONE = "https://api.ztf.fink-portal.org/api/v1/conesearch"
RESOLVE_CACHE_SCHEMA_VERSION = 1


def _resolve_paths() -> tuple[Path, Path]:
    return CACHE / "_resolve.json", CACHE / "_resolve_meta.json"


def _resolve_digest(key: str, query: dict, resolved: str | None) -> str:
    return _digest(json.dumps(
        {"query_key": key, "query": query, "resolved_oid": resolved},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ))


def _resolve_proof_authenticates(
    proof: Any,
    *,
    key: str,
    query: dict,
    resolved: Any,
    max_age_seconds: float,
) -> bool:
    if not isinstance(proof, dict):
        return False
    if resolved is not None and (
        not isinstance(resolved, str) or not _SAFE_OID.fullmatch(resolved)
    ):
        return False
    expected_status = "ok" if resolved is not None else "ok_empty"
    row_count = proof.get("row_count")
    if isinstance(row_count, bool) or not isinstance(row_count, int):
        return False
    return (
        proof.get("cache_schema_version") == RESOLVE_CACHE_SCHEMA_VERSION
        and proof.get("query_key") == key
        and proof.get("query") == query
        and proof.get("status") == expected_status
        and proof.get("http_status") == 200
        and proof.get("source_url") == CONE
        and proof.get("response_validated") is True
        and proof.get("resolved_oid") == resolved
        and proof.get("query_value_sha256")
        == _resolve_digest(key, query, resolved)
        and row_count >= (1 if resolved is not None else 0)
        and (resolved is not None or row_count == 0)
        and _metadata_is_fresh(proof, max_age_seconds)
    )


def resolve_oid(
    s: requests.Session,
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float = 3.0,
    *,
    refresh: bool = False,
    max_age_seconds: float = RESOLVE_MAX_AGE_SECONDS,
) -> str | None:
    """Resolve a position against Fink without caching transport failures."""
    max_age_seconds = _checked_max_age(max_age_seconds)
    key = f"{ra_deg:.6f}_{dec_deg:.6f}_{radius_arcsec}"
    query = {
        "ra": str(ra_deg),
        "dec": str(dec_deg),
        "radius_arcsec": radius_arcsec,
    }
    cache_path, meta_path = _resolve_paths()
    cache: dict[str, str | None] = {}
    meta: dict[str, dict] = {}
    if cache_path.exists():
        try:
            loaded_cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(loaded_cache, dict):
                cache = loaded_cache
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    if meta_path.exists():
        try:
            loaded_meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded_meta, dict):
                meta = loaded_meta
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass

    if not refresh and key in cache and _resolve_proof_authenticates(
        meta.get(key),
        key=key,
        query=query,
        resolved=cache[key],
        max_age_seconds=max_age_seconds,
    ):
        return cache[key]

    failures: list[str] = []
    for attempt in range(FETCH_ATTEMPTS):
        try:
            r = s.post(
                CONE,
                json={
                    "ra": str(ra_deg),
                    "dec": str(dec_deg),
                    "radius": radius_arcsec,
                    "output-format": "json",
                    "columns": "i:objectId,i:jd",
                },
                timeout=120,
            )
            if r.status_code != 200:
                raise FinkFetchError(f"HTTP {r.status_code}")
            try:
                rows = r.json()
            except ValueError as exc:
                raise FinkFetchError(f"malformed JSON: {exc}") from exc
            if not isinstance(rows, list):
                raise FinkFetchError("invalid cone-search response")

            counts: dict[str, int] = {}
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise FinkFetchError(
                        f"invalid cone-search record {index}"
                    )
                oid = row.get("i:objectId")
                try:
                    jd = float(row.get("i:jd"))
                except (TypeError, ValueError) as exc:
                    raise FinkFetchError(
                        f"invalid cone-search record {index}"
                    ) from exc
                if (not isinstance(oid, str) or not _SAFE_OID.fullmatch(oid)
                        or not math.isfinite(jd)):
                    raise FinkFetchError(
                        f"invalid cone-search record {index}"
                    )
                counts[oid] = counts.get(oid, 0) + 1
            resolved = max(counts, key=counts.get) if counts else None
            cache[key] = resolved
            fetched_at = _utc_now()
            meta[key] = {
                "cache_schema_version": RESOLVE_CACHE_SCHEMA_VERSION,
                "query_key": key,
                "query": query,
                "status": "ok" if resolved else "ok_empty",
                "http_status": 200,
                "fetched_at_utc": fetched_at,
                "source_url": CONE,
                "response_validated": True,
                "resolved_oid": resolved,
                "query_value_sha256": _resolve_digest(key, query, resolved),
                "row_count": len(rows),
            }
            _atomic_write(cache_path, json.dumps(cache, sort_keys=True))
            _atomic_write(meta_path, json.dumps(meta, indent=2, sort_keys=True))
            return resolved
        except (requests.RequestException, FinkFetchError) as exc:
            failures.append(f"attempt {attempt + 1}: {exc}")
        if attempt + 1 < FETCH_ATTEMPTS:
            time.sleep(2 * (attempt + 1))

    raise FinkFetchError(
        "Fink cone search failed; no unresolved result was cached "
        f"({'; '.join(failures)})"
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--quarantine-legacy-empty"]:
        print(f"quarantined {quarantine_legacy_empty_caches()} legacy empty caches")
    else:
        ids = sys.argv[1:]
        got = fetch_many(ids)
        for object_id, history in got.items():
            print(object_id, len(history))
