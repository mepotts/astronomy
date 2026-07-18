"""Live TAP_SCHEMA resolver with a local JSON cache and a committed offline fixture.

For the chosen endpoint we read the service's self-describing ``TAP_SCHEMA`` (DATA-SOURCES.md S2):
``TAP_SCHEMA.tables`` / ``columns`` (names, units, UCDs, datatypes) and ``keys`` / ``key_columns``
(the declared foreign keys that tell us the *legitimate* JOIN keys — used by the linter's
MISSING_JOIN_KEY rule).

``load_schema`` resolution order (per the M1 spec):

    1. **cache**  — ``schemas/<key>.json`` next to the repo (gitignored, regenerable)
    2. **live**   — ``pyvo.dal.TAPService(url)`` query against ``TAP_SCHEMA`` (then written to cache)
    3. **fixture** — the committed offline snapshot bundled in ``adql_copilot/fixtures/<key>.json``

The live path is fully wired. In environments where outbound HTTP is blocked (e.g. a sandbox) the
live fetch raises and we transparently fall back to the bundled fixture, logging that the live path
is wired but unverified — so the linter is always testable offline.
"""

from __future__ import annotations

import json
import logging
from importlib import resources
from pathlib import Path

from .endpoints import ENDPOINTS
from .models import ColumnMeta, ForeignKey, Schema

logger = logging.getLogger("adql_copilot.schema")

# On-disk cache lives at <repo>/schemas/<key>.json (gitignored). schema.py is at
# src/adql_copilot/schema.py, so the repo root is three parents up.
_CACHE_DIR = Path(__file__).resolve().parents[2] / "schemas"


def cache_path(endpoint_key: str) -> Path:
    return _CACHE_DIR / f"{endpoint_key}.json"


def load_schema(endpoint_key: str, *, refresh: bool = False) -> Schema:
    """Return the :class:`Schema` for an endpoint, trying cache -> live -> fixture.

    ``refresh=True`` skips the cache and forces a live fetch (falling back to the fixture if the
    network is unavailable). Raises ``KeyError`` for an unknown endpoint key.
    """
    if endpoint_key not in ENDPOINTS:
        raise KeyError(f"unknown endpoint {endpoint_key!r}; known: {list(ENDPOINTS)}")

    # 1) cache
    if not refresh:
        cached = _load_cache(endpoint_key)
        if cached is not None:
            logger.info(
                "schema[%s] loaded from cache %s (%d columns, %d keys)",
                endpoint_key, cache_path(endpoint_key), len(cached.columns), len(cached.keys),
            )
            return cached

    # 2) live (then persist to cache on success)
    try:
        live = _fetch_live(endpoint_key)
        _write_cache(endpoint_key, live)
        logger.info(
            "schema[%s] fetched live (%d columns, %d keys); cached to %s",
            endpoint_key, len(live.columns), len(live.keys), cache_path(endpoint_key),
        )
        return live
    except Exception as exc:  # noqa: BLE001 - any live failure (network/parse) -> fixture fallback
        logger.warning(
            "schema[%s] live TAP fetch unavailable (%s: %s); the live path is wired but "
            "UNVERIFIED in this environment. Falling back to the bundled offline fixture.",
            endpoint_key, type(exc).__name__, exc,
        )

    # 3) fixture
    fixture = _load_fixture(endpoint_key)
    if fixture is None:
        raise RuntimeError(
            f"no schema available for {endpoint_key!r}: cache miss, live fetch failed, and no "
            f"bundled fixture (expected adql_copilot/fixtures/{endpoint_key}.json)."
        )
    logger.info("schema[%s] loaded from bundled offline fixture", endpoint_key)
    return fixture


# --- 1) cache ---------------------------------------------------------------------------


def _load_cache(endpoint_key: str) -> Schema | None:
    path = cache_path(endpoint_key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = _schema_from_dict(data, endpoint_key=endpoint_key, default_source="cache")
        schema.source = "cache"
        return schema
    except Exception as exc:  # noqa: BLE001 - a corrupt cache should not be fatal
        logger.warning("schema[%s] cache at %s is unreadable (%s); ignoring it.",
                       endpoint_key, path, exc)
        return None


def _write_cache(endpoint_key: str, schema: Schema) -> None:
    path = cache_path(endpoint_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = schema.model_dump()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - failure to cache is non-fatal
        logger.warning("schema[%s] could not be cached to %s (%s).", endpoint_key, path, exc)


# --- 2) live ----------------------------------------------------------------------------


def _fetch_live(endpoint_key: str) -> Schema:
    """Fetch TAP_SCHEMA columns + foreign keys via pyvo. Raises on any network/parse problem."""
    import pyvo as vo  # imported lazily so offline use never needs the network stack at import time

    url = ENDPOINTS[endpoint_key].tap_url
    svc = vo.dal.TAPService(url)

    columns = _fetch_live_columns(svc)
    keys = _fetch_live_keys(svc)
    return Schema(endpoint_key=endpoint_key, source="live", columns=columns, keys=keys)


def _fetch_live_columns(svc):
    """Fetch TAP_SCHEMA.columns. Retries without ``description`` if that free-text field carries
    non-ASCII bytes (e.g. the Gaia model uses ``±`` / ``°``) that trip pyvo's VOTable decoder."""
    full = (
        "SELECT table_name, column_name, datatype, unit, ucd, description "
        "FROM TAP_SCHEMA.columns"
    )
    minimal = (
        "SELECT table_name, column_name, datatype, unit, ucd FROM TAP_SCHEMA.columns"
    )
    try:
        rows = svc.search(full).to_table()
        has_description = True
    except Exception as exc:  # noqa: BLE001 - DALFormatError wrapping a UnicodeDecodeError, etc.
        logger.warning(
            "TAP_SCHEMA.columns with descriptions failed to decode (%s); retrying without the "
            "free-text description field.", type(exc).__name__,
        )
        rows = svc.search(minimal).to_table()
        has_description = False

    out: list[ColumnMeta] = []
    for r in rows:
        out.append(
            ColumnMeta(
                table_name=_s(r, "table_name"),
                column_name=_s(r, "column_name"),
                datatype=_s(r, "datatype") or None,
                unit=_s(r, "unit") or None,
                ucd=_s(r, "ucd") or None,
                description=(_s(r, "description") or None) if has_description else None,
            )
        )
    return out


def _fetch_live_keys(svc) -> list[ForeignKey]:
    """Join TAP_SCHEMA.keys (which declares from_table/target_table) with TAP_SCHEMA.key_columns
    (which declares from_column/target_column) to recover full foreign-key relationships."""
    try:
        krows = svc.search(
            "SELECT key_id, from_table, target_table FROM TAP_SCHEMA.keys"
        ).to_table()
        kcrows = svc.search(
            "SELECT key_id, from_column, target_column FROM TAP_SCHEMA.key_columns"
        ).to_table()
    except Exception as exc:  # noqa: BLE001 - some services restrict these; keys are optional
        logger.warning("could not read TAP_SCHEMA.keys/key_columns (%s); JOIN-key checks limited.",
                       exc)
        return []

    cols_by_key: dict[str, list[tuple[str, str]]] = {}
    for r in kcrows:
        cols_by_key.setdefault(_s(r, "key_id"), []).append(
            (_s(r, "from_column"), _s(r, "target_column"))
        )

    out: list[ForeignKey] = []
    for r in krows:
        kid = _s(r, "key_id")
        for from_col, target_col in cols_by_key.get(kid, []):
            out.append(
                ForeignKey(
                    from_table=_s(r, "from_table"),
                    target_table=_s(r, "target_table"),
                    from_column=from_col,
                    target_column=target_col,
                )
            )
    return out


def _s(row, name: str) -> str:
    """Coerce one astropy-table cell to a stripped str, tolerating bytes / masked values."""
    try:
        val = row[name]
    except Exception:  # noqa: BLE001 - column absent in this service's TAP_SCHEMA
        return ""
    if val is None:
        return ""
    if isinstance(val, bytes):
        val = val.decode("utf-8", "replace")
    s = str(val).strip()
    return "" if s in ("--", "None", "masked") else s


# --- 3) fixture -------------------------------------------------------------------------


def load_fixture_schema(endpoint_key: str) -> Schema:
    """Load *only* the bundled offline fixture, bypassing cache and live entirely.

    Useful for deterministic tests and for development on a machine where the live snapshot would
    otherwise be cached. Raises ``FileNotFoundError`` if no fixture is bundled for the key.
    """
    fixture = _load_fixture(endpoint_key)
    if fixture is None:
        raise FileNotFoundError(
            f"no bundled fixture for {endpoint_key!r} (expected "
            f"adql_copilot/fixtures/{endpoint_key}.json)."
        )
    return fixture


def _load_fixture(endpoint_key: str) -> Schema | None:
    """Load the committed offline snapshot from adql_copilot/fixtures/<key>.json, if present."""
    try:
        files = resources.files("adql_copilot.fixtures")
        resource = files / f"{endpoint_key}.json"
        if not resource.is_file():
            return None
        data = json.loads(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError):
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("schema[%s] fixture unreadable (%s).", endpoint_key, exc)
        return None
    schema = _schema_from_dict(data, endpoint_key=endpoint_key, default_source="fixture")
    schema.source = "fixture"
    return schema


# --- shared (dict -> Schema) ------------------------------------------------------------


def _schema_from_dict(data: dict, *, endpoint_key: str, default_source: str) -> Schema:
    """Build a Schema from a cache/fixture dict, ignoring documentation keys like ``_comment``."""
    columns = [ColumnMeta(**c) for c in data.get("columns", [])]
    keys = [ForeignKey(**k) for k in data.get("keys", [])]
    return Schema(
        endpoint_key=data.get("endpoint_key", endpoint_key),
        source=data.get("source", default_source),
        columns=columns,
        keys=keys,
    )
