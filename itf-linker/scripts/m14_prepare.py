"""M14: authenticate the 2026-08-19/24 Rubin batches and build a fresh orbit set.

This is deliberately anatomy-first.  A large canonical aggregate can be numbered-object
bookkeeping rather than a designation batch, so byte size is only a watcher trigger.  The
script proves the exact GCS generation and checksum, measures the two aggregates, records
prior M8--M11 coverage without excluding those objects from a fresh sweep, and only then
scans an MPCORB corpus whose ``Last-Modified`` time is later than both generations.

All outputs are under gitignored ``data/`` or match the root ``m[0-9]*.json`` ignore rule.
The script performs public, anonymous GETs only.  It never submits or publishes anything.
No candidate or object identifier is printed; identifiers remain in local ignored artifacts.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import polars as pl
import requests

from itf_linker.attrib.bulk import iter_mpcorb_objects, mpcorb_to_orbit
from itf_linker.attrib.core import AttribOrbit, parse_mpc_orb

RUBIN_DIR = ROOT / "data" / "raw" / "rubin"
M14_DIR = ROOT / "data" / "m14"
INPUT_DIR = M14_DIR / "inputs"

BATCH_DATES = ("2026-08-19", "2026-08-24")
GCS_BUCKET = "asteroid-institute-public"
GCS_LIST = f"https://storage.googleapis.com/storage/v1/b/{GCS_BUCKET}/o"
GCS_MEDIA = f"https://storage.googleapis.com/download/storage/v1/b/{GCS_BUCKET}/o"
MPCORB_URL = "https://www.minorplanetcenter.net/Extended_Files/mpcorb_extended.json.gz"

MPCORB_PATH = INPUT_DIR / "m14-mpcorb_extended.json.gz"
OUT_PARQUET = M14_DIR / "m14-orbits.parquet"
OUT_PROVENANCE = M14_DIR / "m14-orbits.parquet.provenance.json"
OUT_REPORT = M14_DIR / "m14-prepare.json"
GETORB_CACHE = M14_DIR / "getorb"

PRIOR_ORBIT_TABLES = (
    RUBIN_DIR / "m8-orbits.parquet",
    RUBIN_DIR / "m9-orbits.parquet",
)
PRIOR_LEDGERS = (
    ROOT / "m8-ledger.json",
    ROOT / "m9-ledger.json",
    ROOT / "m10-shell-ledger.json",
    ROOT / "m11-deep-ledger.json",
)

MPCORB_MIN_BYTES = 100 << 20
BATCH_MIN_BYTES = 1_000_000
DEFAULT_FALLBACK_CAP = 2_000
DEFAULT_VERIFY_SAMPLE = 24
MIN_INTERVAL_S = 1.1
UNKNOWN_U_PARAM = 99
FUTURE_TOLERANCE = timedelta(minutes=5)
USER_AGENT = (
    "itf-linker/M14 anatomy-first attribution "
    "(read-only; contact matthew.e.potts@gmail.com) python-requests"
)

ORBIT_SCHEMA = {
    "primary": pl.Utf8,
    "matched_provids": pl.List(pl.Utf8),
    "all_desigs": pl.List(pl.Utf8),
    "epoch_mjd_tt": pl.Float64,
    "r0": pl.List(pl.Float64),
    "v0": pl.List(pl.Float64),
    "h_mag": pl.Float64,
    "g_slope": pl.Float64,
    "u_param": pl.Int64,
    "arc_days": pl.Float64,
    "n_obs": pl.Int64,
    "n_opp": pl.Int64,
    "rms": pl.Float64,
    "orbit_type": pl.Utf8,
    "source": pl.Utf8,
    "partitions": pl.List(pl.Utf8),
}


class M14DataError(RuntimeError):
    """An input failed a provenance, completeness, or scientific-scope gate."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_iso_utc(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise M14DataError(f"{label} is missing or not a timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise M14DataError(f"{label} is not an ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise M14DataError(f"{label} has no timezone: {value!r}")
    parsed = parsed.astimezone(UTC)
    if parsed > utc_now() + FUTURE_TOLERANCE:
        raise M14DataError(f"{label} is future-dated: {value!r}")
    return parsed


def parse_http_utc(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise M14DataError(f"{label} is missing")
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise M14DataError(f"{label} is not an HTTP date: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    parsed = parsed.astimezone(UTC)
    if parsed > utc_now() + FUTURE_TOLERANCE:
        raise M14DataError(f"{label} is future-dated: {value!r}")
    return parsed


def canonical_partition_name(day: str) -> str:
    try:
        parsed = date.fromisoformat(day)
    except ValueError as exc:
        raise M14DataError(f"invalid Rubin partition date: {day!r}") from exc
    if parsed.isoformat() != day:
        raise M14DataError(f"non-canonical Rubin partition date: {day!r}")
    return (
        f"production/rubin/mpc/obs_sbn/daily/{day}/parquet/"
        f"obs_sbn_X05_{day}.parquet"
    )


def file_hashes(path: Path) -> dict[str, Any]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            size += len(chunk)
            sha256.update(chunk)
            md5.update(chunk)
    return {
        "bytes": size,
        "sha256": sha256.hexdigest(),
        "md5_base64": base64.b64encode(md5.digest()).decode("ascii"),
    }


def digest_file(path: Path) -> str:
    return str(file_hashes(path)["sha256"])


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_gcs_metadata(
    payload: Any,
    *,
    expected_name: str,
    min_bytes: int = BATCH_MIN_BYTES,
) -> dict[str, Any]:
    """Return the one exact canonical GCS object or fail closed."""
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise M14DataError("GCS metadata response has no items array")
    items = payload["items"]
    if len(items) != 1 or not isinstance(items[0], dict):
        raise M14DataError(
            f"expected one exact GCS object for {expected_name}, found {len(items)}"
        )
    item = items[0]
    if item.get("name") != expected_name or item.get("bucket") != GCS_BUCKET:
        raise M14DataError("GCS metadata did not resolve to the requested canonical object")
    try:
        size = int(item["size"])
        generation = int(item["generation"])
    except (KeyError, TypeError, ValueError) as exc:
        raise M14DataError("GCS metadata has invalid size/generation") from exc
    if size < min_bytes or generation <= 0:
        raise M14DataError(
            f"canonical GCS object is incomplete: {size} bytes, generation {generation}"
        )
    md5_base64 = item.get("md5Hash")
    try:
        decoded_md5 = base64.b64decode(md5_base64, validate=True)
    except (TypeError, ValueError) as exc:
        raise M14DataError("GCS metadata has no valid base64 MD5") from exc
    if len(decoded_md5) != 16:
        raise M14DataError("GCS metadata MD5 is not 128 bits")
    updated = parse_iso_utc(item.get("updated"), label="GCS updated")
    created = parse_iso_utc(item.get("timeCreated"), label="GCS timeCreated")
    if updated < created:
        raise M14DataError("GCS object updated time predates its creation time")
    required_strings = ("crc32c", "etag")
    if any(not isinstance(item.get(key), str) or not item[key] for key in required_strings):
        raise M14DataError("GCS metadata is missing crc32c/etag")
    return {
        "bucket": GCS_BUCKET,
        "name": expected_name,
        "generation": str(generation),
        "metageneration": str(item.get("metageneration", "")),
        "bytes": size,
        "md5_base64": md5_base64,
        "crc32c": item["crc32c"],
        "etag": item["etag"],
        "time_created": iso_utc(created),
        "updated": iso_utc(updated),
    }


def get_gcs_metadata(session: requests.Session, name: str) -> dict[str, Any]:
    response = session.get(
        GCS_LIST,
        params={"prefix": name, "maxResults": "2"},
        headers={"User-Agent": USER_AGENT},
        timeout=(30, 120),
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise M14DataError("GCS metadata endpoint returned malformed JSON") from exc
    return parse_gcs_metadata(payload, expected_name=name)


def _verify_local_proof(path: Path, proof: dict[str, Any]) -> dict[str, Any]:
    hashes = file_hashes(path)
    for key in ("bytes", "sha256"):
        if hashes[key] != proof.get(key):
            raise M14DataError(f"cached file failed {key} proof: {path}")
    if proof.get("md5_base64") and hashes["md5_base64"] != proof["md5_base64"]:
        raise M14DataError(f"cached file failed MD5 proof: {path}")
    return hashes


def fetch_gcs_generation(
    session: requests.Session,
    metadata: dict[str, Any],
    destination: Path,
) -> dict[str, Any]:
    """Download exactly one immutable GCS generation and bind it to two hashes."""
    proof_path = destination.with_suffix(destination.suffix + ".provenance.json")
    if destination.exists() or proof_path.exists():
        if not destination.is_file() or not proof_path.is_file():
            raise M14DataError(f"partial cached GCS artifact: {destination}")
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        for key in ("bucket", "name", "generation", "bytes", "md5_base64"):
            if proof.get(key) != metadata.get(key):
                raise M14DataError(
                    f"cached GCS proof no longer matches live metadata ({key}): {destination}"
                )
        _verify_local_proof(destination, proof)
        return proof

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part-{os.getpid()}")
    encoded = quote(str(metadata["name"]), safe="")
    url = f"{GCS_MEDIA}/{encoded}"
    try:
        with session.get(
            url,
            params={"alt": "media", "generation": metadata["generation"]},
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=(30, 300),
        ) as response:
            response.raise_for_status()
            response_generation = response.headers.get("x-goog-generation")
            if response_generation != metadata["generation"]:
                raise M14DataError(
                    "GCS media response did not prove the requested object generation"
                )
            sha256 = hashlib.sha256()
            md5 = hashlib.md5(usedforsecurity=False)
            size = 0
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    sha256.update(chunk)
                    md5.update(chunk)
                    size += len(chunk)
        local_md5 = base64.b64encode(md5.digest()).decode("ascii")
        if size != metadata["bytes"] or local_md5 != metadata["md5_base64"]:
            raise M14DataError(
                f"GCS payload checksum/size mismatch: got {size} bytes and {local_md5}"
            )
        proof = {
            **metadata,
            "source": "GCS JSON object metadata + generation-pinned media GET",
            "url": url,
            "fetched_utc": iso_utc(utc_now()),
            "sha256": sha256.hexdigest(),
        }
        temporary.replace(destination)
        write_json_atomic(proof_path, proof)
        return proof
    finally:
        if temporary.exists():
            temporary.unlink()


def _mpcorb_headers(headers: Any) -> dict[str, Any]:
    modified_raw = headers.get("Last-Modified")
    modified = parse_http_utc(modified_raw, label="MPCORB Last-Modified")
    try:
        size = int(headers.get("Content-Length"))
    except (TypeError, ValueError) as exc:
        raise M14DataError("MPCORB response has no valid Content-Length") from exc
    etag = headers.get("ETag")
    if size < MPCORB_MIN_BYTES or not isinstance(etag, str) or not etag:
        raise M14DataError("MPCORB response failed minimum size/ETag gates")
    return {
        "last_modified": iso_utc(modified),
        "bytes": size,
        "etag": etag,
    }


def fetch_mpcorb(
    session: requests.Session,
    destination: Path,
    *,
    newer_than: datetime,
) -> dict[str, Any]:
    """Pin one complete MPCORB whose server time postdates the batch generations."""
    proof_path = destination.with_suffix(destination.suffix + ".provenance.json")
    if destination.exists() or proof_path.exists():
        if not destination.is_file() or not proof_path.is_file():
            raise M14DataError(f"partial cached MPCORB artifact: {destination}")
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        modified = parse_iso_utc(proof.get("last_modified"), label="cached MPCORB time")
        if modified <= newer_than:
            raise M14DataError("cached M14 MPCORB does not postdate both Rubin generations")
        _verify_local_proof(destination, proof)
        return proof

    head = session.head(
        MPCORB_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=(30, 120),
        allow_redirects=True,
    )
    head.raise_for_status()
    metadata = _mpcorb_headers(head.headers)
    modified = parse_iso_utc(metadata["last_modified"], label="MPCORB Last-Modified")
    if modified <= newer_than:
        raise M14DataError(
            "latest MPCORB is not newer than both authenticated Rubin aggregates"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part-{os.getpid()}")
    try:
        with session.get(
            MPCORB_URL,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=(30, 300),
        ) as response:
            response.raise_for_status()
            get_metadata = _mpcorb_headers(response.headers)
            if get_metadata != metadata:
                raise M14DataError("MPCORB changed between HEAD and the pinned GET")
            sha256 = hashlib.sha256()
            size = 0
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    sha256.update(chunk)
                    size += len(chunk)
        if size != metadata["bytes"]:
            raise M14DataError(
                f"MPCORB body length {size} does not match Content-Length {metadata['bytes']}"
            )
        proof = {
            "source": "MPC Extended Files",
            "url": MPCORB_URL,
            **metadata,
            "fetched_utc": iso_utc(utc_now()),
            "sha256": sha256.hexdigest(),
        }
        temporary.replace(destination)
        write_json_atomic(proof_path, proof)
        return proof
    finally:
        if temporary.exists():
            temporary.unlink()


def batch_anatomy(path: Path) -> tuple[set[str], dict[str, Any]]:
    """Return useful unnumbered designations plus an identifier-free anatomy summary."""
    required = {"provid", "permid", "obstime", "created_at", "disc"}
    try:
        schema = pl.read_parquet_schema(path)
    except Exception as exc:
        raise M14DataError(f"not a readable Parquet aggregate: {path}") from exc
    missing = required - set(schema)
    if missing:
        raise M14DataError(f"Rubin aggregate is missing required columns: {sorted(missing)}")
    frame = pl.read_parquet(path, columns=sorted(required))
    if frame.height <= 0:
        raise M14DataError(f"Rubin aggregate contains no rows: {path}")
    has_provid = pl.col("provid").is_not_null() & (
        pl.col("provid").str.strip_chars() != ""
    )
    with_provid = frame.filter(has_provid)
    unclassified = frame.height - with_provid.height
    if unclassified:
        raise M14DataError(
            f"Rubin aggregate has {unclassified} observations without provid; "
            "accounting residue stops M14"
        )
    unnumbered = with_provid.filter(
        pl.col("permid").is_null() | (pl.col("permid").str.strip_chars() == "")
    )
    objects = {str(value).strip() for value in unnumbered["provid"].unique().to_list()}
    objects.discard("")
    years: Counter[str] = Counter()
    for designation in objects:
        prefix = designation.split()[0] if " " in designation else designation[:4]
        if len(prefix) == 4 and prefix.isdigit():
            years[prefix] += 1
        else:
            years["other"] += 1
    discovery = int((with_provid["disc"] == "*").sum()) if with_provid.height else 0
    stats = {
        "observations": frame.height,
        "with_provid": with_provid.height,
        "unclassified_observations": unclassified,
        "numbered_observations": with_provid.height - unnumbered.height,
        "unnumbered_observations": unnumbered.height,
        "distinct_unnumbered_objects": len(objects),
        "discovery_asterisks": discovery,
        "obstime_span": (
            [str(with_provid["obstime"].min()), str(with_provid["obstime"].max())]
            if with_provid.height
            else None
        ),
        "created_at_span": [str(frame["created_at"].min()), str(frame["created_at"].max())],
        "designation_years_top": dict(years.most_common(8)),
        "schema": {name: str(dtype) for name, dtype in schema.items()},
    }
    return objects, stats


def _iter_string_lists(values: Iterable[Any]) -> Iterable[str]:
    for value in values:
        if value is None:
            continue
        if not isinstance(value, list):
            raise M14DataError("prior orbit designation column is not list-valued")
        for item in value:
            if isinstance(item, str) and item.strip():
                yield item.strip()


def load_prior_coverage() -> tuple[set[str], set[str], set[tuple[str, str]], dict[str, Any]]:
    """All prior orbit aliases, ledger objects, and exact candidate keys."""
    orbit_designations: set[str] = set()
    orbit_primaries: set[str] = set()
    sources: dict[str, Any] = {"orbit_tables": {}, "ledgers": {}}
    for path in PRIOR_ORBIT_TABLES:
        if not path.is_file():
            raise M14DataError(f"required prior orbit table is missing: {path}")
        frame = pl.read_parquet(path, columns=["primary", "matched_provids", "all_desigs"])
        primaries = {str(value).strip() for value in frame["primary"].to_list()}
        orbit_primaries.update(primaries)
        orbit_designations.update(primaries)
        orbit_designations.update(_iter_string_lists(frame["matched_provids"].to_list()))
        orbit_designations.update(_iter_string_lists(frame["all_desigs"].to_list()))
        sources["orbit_tables"][path.name] = {
            "rows": frame.height,
            "sha256": digest_file(path),
        }

    ledger_objects: set[str] = set()
    ledger_pairs: set[tuple[str, str]] = set()
    for path in PRIOR_LEDGERS:
        if not path.is_file():
            raise M14DataError(f"required prior ledger is missing: {path}")
        document = json.loads(path.read_text(encoding="utf-8"))
        verdicts = document.get("verdicts")
        if not isinstance(verdicts, list):
            raise M14DataError(f"prior ledger has no verdict list: {path}")
        rows = [*verdicts]
        held = document.get("held_from_m7") or []
        if not isinstance(held, list):
            raise M14DataError(f"prior ledger held_from_m7 is malformed: {path}")
        rows.extend(held)
        valid_pairs = 0
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("orbit_desig"), str):
                raise M14DataError(f"prior ledger contains an invalid candidate row: {path}")
            orbit = row["orbit_desig"].strip()
            if not orbit:
                raise M14DataError(f"prior ledger contains an empty orbit designation: {path}")
            ledger_objects.add(orbit)
            link = row.get("link_key")
            if isinstance(link, str) and link:
                ledger_pairs.add((orbit, link))
                valid_pairs += 1
        sources["ledgers"][path.name] = {
            "verdicts": len(verdicts),
            "rows_with_candidate_key": valid_pairs,
            "sha256": digest_file(path),
        }
    return orbit_designations, orbit_primaries | ledger_objects, ledger_pairs, sources


def orbit_row(orbit: AttribOrbit, *, matched: Iterable[str], source: str) -> dict[str, Any]:
    return {
        "primary": orbit.primary_desig,
        "matched_provids": sorted(set(matched)),
        "all_desigs": orbit.all_desigs,
        "epoch_mjd_tt": orbit.epoch_mjd_tt,
        "r0": orbit.r0.tolist(),
        "v0": orbit.v0.tolist(),
        "h_mag": orbit.h_mag,
        "g_slope": orbit.g_slope,
        # Unknown uncertainty must be excluded by the U<=6 quality gate, never
        # represented by a low sentinel that passes it.
        "u_param": UNKNOWN_U_PARAM if orbit.u_param is None else orbit.u_param,
        "arc_days": orbit.arc_days,
        "n_obs": orbit.n_obs,
        "n_opp": orbit.n_opp,
        "rms": orbit.normalized_rms,
        "orbit_type": orbit.orbit_type,
        "source": source,
        "partitions": [],
    }


def _getorb_cache_path(designation: str) -> Path:
    digest = hashlib.sha256(designation.encode("utf-8")).hexdigest()
    return GETORB_CACHE / f"{digest}.json"


def _cached_getorb(designation: str) -> dict[str, Any] | None:
    path = _getorb_cache_path(designation)
    if not path.exists():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("requested_desig") != designation:
        raise M14DataError(f"M14 get-orb cache proof mismatch: {path}")
    response = document.get("response")
    canonical = json.dumps(response, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if digest != document.get("response_sha256"):
        raise M14DataError(f"M14 get-orb cache digest mismatch: {path}")
    parse_iso_utc(document.get("fetched_utc"), label="get-orb fetched_utc")
    return document


def fetch_getorb(
    session: requests.Session,
    designation: str,
    *,
    wait_since: float | None,
) -> tuple[AttribOrbit | None, float]:
    """Fetch one current orbit with a content-bound ignored cache."""
    document = _cached_getorb(designation)
    last_request = wait_since or 0.0
    if document is None:
        wait = MIN_INTERVAL_S - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        response = session.get(
            "https://data.minorplanetcenter.net/api/get-orb",
            json={"desig": designation},
            headers={"User-Agent": USER_AGENT},
            timeout=(30, 120),
        )
        last_request = time.monotonic()
        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = {"error_text": response.text[:400]}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        document = {
            "schema": 1,
            "requested_desig": designation,
            "fetched_utc": iso_utc(utc_now()),
            "status": response.status_code,
            "response": payload,
            "response_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
        write_json_atomic(_getorb_cache_path(designation), document)
    if document.get("status") != 200:
        return None, last_request
    orbit = parse_mpc_orb(document["response"], requested_desig=designation)
    return orbit, last_request


def deterministic_sample(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    by_u: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if row["source"] == "mpcorb":
            by_u.setdefault(int(row["u_param"]), []).append(row)
    for values in by_u.values():
        values.sort(key=lambda row: hashlib.sha256(row["primary"].encode()).hexdigest())
    sample: list[dict[str, Any]] = []
    while len(sample) < min(size, sum(len(values) for values in by_u.values())):
        advanced = False
        for u_param in sorted(by_u):
            if by_u[u_param]:
                sample.append(by_u[u_param].pop(0))
                advanced = True
            if len(sample) >= size:
                break
        if not advanced:
            break
    return sample


def verify_orbit_sample(
    session: requests.Session,
    rows: list[dict[str, Any]],
    *,
    sample_size: int,
) -> dict[str, Any]:
    """Compare a U-stratified MPCORB sample to current get-orb states."""
    sample = deterministic_sample(rows, sample_size)
    if not sample:
        return {"sampled": 0, "compared": 0, "gate": "not_applicable_no_mpcorb_rows"}
    from itf_linker.attrib.perturbed import integrate_dense

    residuals: list[float] = []
    last_request: float | None = None
    for row in sample:
        current, last_request = fetch_getorb(
            session, row["primary"], wait_since=last_request
        )
        if current is None:
            raise M14DataError("live get-orb verification returned no orbit for a sample row")
        gap = float(row["epoch_mjd_tt"] - current.epoch_mjd_tt)
        if abs(gap) < 1e-6:
            reference = current.r0
        else:
            trajectory = integrate_dense(
                current.r0[None, :],
                current.v0[None, :],
                current.epoch_mjd_tt,
                min(current.epoch_mjd_tt, row["epoch_mjd_tt"]) - 1.0,
                max(current.epoch_mjd_tt, row["epoch_mjd_tt"]) + 1.0,
                h_days=1.0,
                dense_every=1,
            )
            reference_arr, _ = trajectory.state_at(
                np.array([row["epoch_mjd_tt"]]), np.array([0])
            )
            reference = reference_arr[0]
        residuals.append(float(np.linalg.norm(np.asarray(row["r0"]) - reference)))
    values = np.asarray(residuals)
    median = float(np.median(values))
    fraction_below_005 = float((values < 0.05).sum() / values.size)
    maximum = float(values.max())
    passed = median < 1e-3 and fraction_below_005 >= 0.95 and maximum < 0.1
    report = {
        "sampled": len(sample),
        "compared": int(values.size),
        "dr_au_median": median,
        "dr_au_p95": float(np.quantile(values, 0.95)),
        "dr_au_max": maximum,
        "fraction_below_0_05_au": fraction_below_005,
        "gate": {
            "median_lt_0_001_au": median < 1e-3,
            "fraction_below_0_05_au_gte_0_95": fraction_below_005 >= 0.95,
            "max_lt_0_1_au": maximum < 0.1,
            "passes": passed,
        },
    }
    if not passed:
        raise M14DataError(f"MPCORB/get-orb state verification failed: {report['gate']}")
    return report


def _write_orbits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pl.DataFrame(rows, schema=ORBIT_SCHEMA, strict=False)
    temporary = OUT_PARQUET.with_name(f".{OUT_PARQUET.name}.tmp-{os.getpid()}.parquet")
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    try:
        frame.write_parquet(temporary)
        hashes = file_hashes(temporary)
        temporary.replace(OUT_PARQUET)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"rows": frame.height, **hashes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-cap", type=int, default=DEFAULT_FALLBACK_CAP)
    parser.add_argument("--verify-sample", type=int, default=DEFAULT_VERIFY_SAMPLE)
    args = parser.parse_args()
    if args.fallback_cap < 0 or args.verify_sample < 0:
        raise SystemExit("fallback and verification limits must be non-negative")
    completed_artifacts = (OUT_PARQUET, OUT_PROVENANCE, OUT_REPORT)
    if any(path.exists() for path in completed_artifacts):
        state = "complete" if all(path.is_file() for path in completed_artifacts) else "partial"
        raise M14DataError(
            f"an M14 preparation artifact set already exists ({state}); refusing to "
            "overwrite the recorded input proof"
        )

    started = time.monotonic()
    session = requests.Session()
    report: dict[str, Any] = {
        "schema": 1,
        "milestone": "M14",
        "generated_utc": iso_utc(utc_now()),
        "scope": {
            "batch_dates": list(BATCH_DATES),
            "anatomy_first": True,
            "identifiers_public": False,
            "submission_or_publication": False,
        },
        "batches": {},
    }

    per_batch_objects: dict[str, set[str]] = {}
    batch_proofs: dict[str, dict[str, Any]] = {}
    newest_generation = datetime.min.replace(tzinfo=UTC)
    for day in BATCH_DATES:
        name = canonical_partition_name(day)
        metadata = get_gcs_metadata(session, name)
        destination = INPUT_DIR / (
            f"obs_sbn_X05_{day}.g{metadata['generation']}.parquet"
        )
        proof = fetch_gcs_generation(session, metadata, destination)
        objects, anatomy = batch_anatomy(destination)
        newest_generation = max(
            newest_generation,
            parse_iso_utc(proof["updated"], label=f"{day} GCS updated"),
        )
        anatomy["provenance"] = {
            key: proof[key]
            for key in (
                "name", "generation", "bytes", "md5_base64", "crc32c", "etag",
                "time_created", "updated", "sha256", "fetched_utc",
            )
        }
        report["batches"][day] = anatomy
        per_batch_objects[day] = objects
        batch_proofs[day] = proof
        print(
            f"{day}: {anatomy['observations']:,} observations; "
            f"{anatomy['numbered_observations']:,} numbered; "
            f"{anatomy['distinct_unnumbered_objects']:,} unnumbered objects",
            flush=True,
        )

    orbit_aliases, prior_objects, prior_pairs, prior_sources = load_prior_coverage()
    union = set().union(*per_batch_objects.values())
    # Re-sweep every object carried by the two authenticated batches.  A designation
    # seen in M8/M9 can have an improved orbit and the pinned M14 ITF can contain a new
    # tracklet.  Prior work is therefore removed at the candidate-pair stage in
    # m14_attribution.py, never here at the orbit stage.
    wanted = set(union)
    for day, objects in per_batch_objects.items():
        report["batches"][day]["objects_prior_covered"] = len(
            objects & (orbit_aliases | prior_objects)
        )
        report["batches"][day]["objects_new_before_current_alias_resolution"] = len(
            objects - orbit_aliases - prior_objects
        )
    report["prior_coverage"] = {
        **prior_sources,
        "covered_designations": len(orbit_aliases),
        "covered_orbit_objects": len(prior_objects),
        "candidate_keys": len(prior_pairs),
    }
    report["objects"] = {
        "union": len(union),
        "prior_covered_objects": len(union & (orbit_aliases | prior_objects)),
        "objects_to_resolve_and_resweep": len(wanted),
    }
    print(
        f"batch union: {len(union):,}; prior-covered objects retained for re-sweep: "
        f"{len(union & (orbit_aliases | prior_objects)):,}",
        flush=True,
    )

    mpcorb_proof = fetch_mpcorb(session, MPCORB_PATH, newer_than=newest_generation)
    report["mpcorb"] = mpcorb_proof

    rows_by_primary: dict[str, dict[str, Any]] = {}
    matched: set[str] = set()
    resolved_to_prior: set[str] = set()
    scanned = unparsable = 0
    parse_started = time.monotonic()
    for raw in iter_mpcorb_objects(MPCORB_PATH):
        scanned += 1
        principal = str(raw.get("Principal_desig") or "").strip()
        other = {
            str(value).strip()
            for value in (raw.get("Other_desigs") or [])
            if str(value).strip()
        }
        hit = ({principal} | other) & wanted
        if not hit:
            continue
        orbit = mpcorb_to_orbit(raw)
        if orbit is None:
            unparsable += 1
            continue
        matched.update(hit)
        aliases = {orbit.primary_desig, *orbit.all_desigs}
        if orbit.primary_desig in prior_objects or aliases & orbit_aliases:
            resolved_to_prior.update(hit)
        existing = rows_by_primary.get(orbit.primary_desig)
        if existing is None:
            rows_by_primary[orbit.primary_desig] = orbit_row(
                orbit, matched=hit, source="mpcorb"
            )
        else:
            existing["matched_provids"] = sorted(
                set(existing["matched_provids"]) | hit
            )
    report["mpcorb_parse"] = {
        "objects_scanned": scanned,
        "matched_provids": len(matched),
        "current_unique_orbits": len(rows_by_primary),
        "resolved_to_prior_object": len(resolved_to_prior),
        "unparsable_matches": unparsable,
        "seconds": round(time.monotonic() - parse_started, 2),
    }
    print(
        f"MPCORB: scanned {scanned:,}; resolved {len(matched):,} requested aliases; "
        f"built {len(rows_by_primary):,} current unique orbit rows",
        flush=True,
    )

    unmatched = sorted(wanted - matched)
    if len(unmatched) > args.fallback_cap:
        report["fallback"] = {
            "unmatched_provids": len(unmatched),
            "cap": args.fallback_cap,
            "status": "refused_above_cap",
        }
        write_json_atomic(OUT_REPORT, report)
        raise M14DataError(
            f"{len(unmatched)} MPCORB misses exceed fallback cap {args.fallback_cap}"
        )
    fallback_resolved = fallback_missing = fallback_to_prior = 0
    last_request: float | None = None
    for designation in unmatched:
        orbit, last_request = fetch_getorb(
            session, designation, wait_since=last_request
        )
        if orbit is None:
            fallback_missing += 1
            continue
        fallback_resolved += 1
        matched.add(designation)
        aliases = {orbit.primary_desig, *orbit.all_desigs}
        if orbit.primary_desig in prior_objects or aliases & orbit_aliases:
            fallback_to_prior += 1
            resolved_to_prior.add(designation)
        existing = rows_by_primary.get(orbit.primary_desig)
        if existing is None:
            rows_by_primary[orbit.primary_desig] = orbit_row(
                orbit, matched=[designation], source="get-orb"
            )
        else:
            existing["matched_provids"] = sorted(
                set(existing["matched_provids"]) | {designation}
            )
    still_missing = wanted - matched
    if len(still_missing) != fallback_missing:
        raise M14DataError("fallback accounting did not close")
    report["fallback"] = {
        "unmatched_provids": len(unmatched),
        "cap": args.fallback_cap,
        "resolved": fallback_resolved,
        "resolved_to_prior_object": fallback_to_prior,
        "no_current_orbit": fallback_missing,
        "status": "complete",
    }
    print(
        f"fallback: {len(unmatched):,} requested; {fallback_resolved:,} resolved; "
        f"{fallback_missing:,} have no current orbit",
        flush=True,
    )

    designation_to_batches: dict[str, set[str]] = {}
    for day, objects in per_batch_objects.items():
        for designation in objects:
            designation_to_batches.setdefault(designation, set()).add(day)
    rows = list(rows_by_primary.values())
    for row in rows:
        memberships: set[str] = set()
        for designation in [*row["matched_provids"], *(row["all_desigs"] or [])]:
            memberships.update(designation_to_batches.get(designation, set()))
        row["partitions"] = sorted(memberships)
        if not row["partitions"]:
            raise M14DataError("an M14 orbit row lost all authenticated batch membership")

    report["verification"] = verify_orbit_sample(
        session, rows, sample_size=args.verify_sample
    )
    output_proof = _write_orbits(rows)
    u_histogram = Counter(int(row["u_param"]) for row in rows)
    sweepable = sum(count for u, count in u_histogram.items() if 0 <= u <= 6)
    report["orbits"] = {
        "written": len(rows),
        "sweepable_u_lte_6": sweepable,
        "u_excluded": len(rows) - sweepable,
        "u_histogram": {str(key): value for key, value in sorted(u_histogram.items())},
        "by_source": dict(Counter(row["source"] for row in rows)),
        "resolved_to_prior_object": len(resolved_to_prior),
        "output": output_proof,
    }
    report["coverage_accounting"] = {
        "objects_to_resolve_and_resweep": len(wanted),
        "resolved_current": len(matched),
        "no_current_orbit": len(still_missing),
        "closed": len(wanted) == len(matched) + len(still_missing),
    }
    if not report["coverage_accounting"]["closed"]:
        raise M14DataError("M14 object coverage accounting did not close")
    report["elapsed_s"] = round(time.monotonic() - started, 2)

    provenance = {
        "schema": 1,
        "generated_utc": iso_utc(utc_now()),
        "output": output_proof,
        "mpcorb": {
            key: mpcorb_proof[key]
            for key in ("url", "last_modified", "bytes", "etag", "sha256")
        },
        "batches": {
            day: {
                key: batch_proofs[day][key]
                for key in ("name", "generation", "bytes", "md5_base64", "sha256", "updated")
            }
            for day in BATCH_DATES
        },
        "prior_inputs": prior_sources,
        "report": OUT_REPORT.name,
    }
    write_json_atomic(OUT_PROVENANCE, provenance)
    write_json_atomic(OUT_REPORT, report)
    print(
        f"M14 prepared {len(rows):,} orbit rows ({sweepable:,} sweepable); "
        f"all provenance and accounting gates passed in {report['elapsed_s']} s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (requests.RequestException, M14DataError) as error:
        print(f"M14 preparation refused: {error}", file=sys.stderr)
        raise SystemExit(1) from error
