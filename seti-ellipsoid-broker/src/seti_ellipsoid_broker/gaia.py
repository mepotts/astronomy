"""Gaia DR3 distance layer: batched ``astroquery.gaia`` TAP crossmatch (LIVE, account-free).

This is the broker's differentiator — it carries its own Gaia DR3 astrometry instead of
relying on a broker's distance-poor alert schema. Anonymous TAP is sufficient for DR3
``gaia_source`` (no login, no token), which is exactly why the account-free live path
(``--transients-csv``) can run end to end. Endpoint / limits / columns: DATA-SOURCES.md S2.

Given a set of transient counterparts — either pre-resolved Gaia ``source_id``s or
``(ra, dec)`` to cone-match — :func:`crossmatch` fetches, per source, the astrometry the
pipeline needs (``parallax``, ``parallax_error``, ``parallax_over_error``, ``pmra``,
``pmdec``, ``ruwe``, ``phot_g_mean_mag``) plus the four columns the Gaia DR3 parallax
zero-point correction requires (``nu_eff_used_in_astrometry``, ``pseudocolour``,
``ecl_lat``, ``astrometric_params_solved`` — see :mod:`.zeropoint`).

Testability: every function that would hit the network takes an injectable ``launch``
callable ``(adql: str) -> astropy.table.Table``. The default (:func:`_default_launch`)
runs an anonymous ``astroquery.gaia`` async job; unit tests pass a fake that returns a
small canned table, so the suite stays fully OFFLINE. A single live smoke test lives in
``tests/test_gaia_live.py`` and is skipped unless ``SETI_GAIA_LIVE=1``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from .models import Alert

# Gaia DR3 columns we SELECT, in a fixed order (astrometry + zero-point inputs).
GAIA_COLUMNS: tuple[str, ...] = (
    "source_id",
    "ra",
    "dec",
    "parallax",
    "parallax_error",
    "parallax_over_error",
    "pmra",
    "pmdec",
    "ruwe",
    "phot_g_mean_mag",
    "nu_eff_used_in_astrometry",
    "pseudocolour",
    "ecl_lat",
    "astrometric_params_solved",
)

MAIN_GAIA_TABLE: str = "gaiadr3.gaia_source"
DEFAULT_CONE_RADIUS_ARCSEC: float = 5.0

# astroquery/TAP source-id batch soft cap (DATA-SOURCES.md S2).
_ID_BATCH: int = 5000

Launch = Callable[[str], "object"]  # (adql) -> astropy.table.Table


@dataclass(slots=True)
class GaiaSource:
    """One Gaia DR3 source's astrometry + the parallax zero-point input columns.

    ``nu_eff_used_in_astrometry`` is populated for 5-parameter solutions and
    ``pseudocolour`` for 6-parameter solutions, so exactly one of the pair is typically
    NULL for a given source (mirrors the catalogue). ``astrometric_params_solved`` is 3
    (2p), 31 (5p) or 95 (6p).
    """

    source_id: int
    ra: float
    dec: float
    parallax: float | None
    parallax_error: float | None
    parallax_over_error: float | None
    pmra: float | None
    pmdec: float | None
    ruwe: float | None
    phot_g_mean_mag: float | None
    nu_eff_used_in_astrometry: float | None
    pseudocolour: float | None
    ecl_lat: float | None
    astrometric_params_solved: int | None


# --- ADQL builders (pure; unit-tested without network) ------------------------------

def build_source_id_adql(source_ids: Sequence[int], table: str = MAIN_GAIA_TABLE) -> str:
    """ADQL selecting :data:`GAIA_COLUMNS` for an explicit list of Gaia ``source_id``s."""
    if not source_ids:
        raise ValueError("source_ids must be non-empty")
    ids = ", ".join(str(int(s)) for s in source_ids)
    cols = ", ".join(GAIA_COLUMNS)
    return f"SELECT {cols}\nFROM {table}\nWHERE source_id IN ({ids})"


def build_cone_adql(
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float = DEFAULT_CONE_RADIUS_ARCSEC,
    table: str = MAIN_GAIA_TABLE,
    top: int = 20,
) -> str:
    """ADQL for a cone of ``radius_arcsec`` around ``(ra_deg, dec_deg)`` (nearest picked later)."""
    if radius_arcsec <= 0:
        raise ValueError("radius_arcsec must be positive")
    radius_deg = radius_arcsec / 3600.0
    cols = ", ".join(GAIA_COLUMNS)
    return (
        f"SELECT TOP {int(top)} {cols}\n"
        f"FROM {table}\n"
        f"WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra_deg!r}, {dec_deg!r}, {radius_deg!r}))"
    )


# --- table -> records ---------------------------------------------------------------

def _get_float(row, name: str) -> float | None:
    """Pull a float column value, mapping masked / None / NaN to None."""
    try:
        v = row[name]
    except (KeyError, ValueError, IndexError):
        return None
    if v is None or np.ma.is_masked(v):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) else f


def _get_int(row, name: str) -> int | None:
    """Pull an integer column value WITHOUT going through float (preserves 19-digit ids)."""
    try:
        v = row[name]
    except (KeyError, ValueError, IndexError):
        return None
    if v is None or np.ma.is_masked(v):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _row_to_source(row) -> GaiaSource:
    return GaiaSource(
        source_id=_get_int(row, "source_id"),
        ra=_get_float(row, "ra"),
        dec=_get_float(row, "dec"),
        parallax=_get_float(row, "parallax"),
        parallax_error=_get_float(row, "parallax_error"),
        parallax_over_error=_get_float(row, "parallax_over_error"),
        pmra=_get_float(row, "pmra"),
        pmdec=_get_float(row, "pmdec"),
        ruwe=_get_float(row, "ruwe"),
        phot_g_mean_mag=_get_float(row, "phot_g_mean_mag"),
        nu_eff_used_in_astrometry=_get_float(row, "nu_eff_used_in_astrometry"),
        pseudocolour=_get_float(row, "pseudocolour"),
        ecl_lat=_get_float(row, "ecl_lat"),
        astrometric_params_solved=_get_int(row, "astrometric_params_solved"),
    )


def _table_to_sources(table) -> list[GaiaSource]:
    return [_row_to_source(row) for row in table]


# --- the live launcher (only place that imports astroquery) -------------------------

def _default_launch(adql: str):
    """Run an anonymous ``astroquery.gaia`` async job and return the results Table.

    Imported lazily so the module (and the offline pipeline) load without astroquery, and
    so unit tests can inject a fake launcher and never touch the network.
    """
    from astroquery.gaia import Gaia  # local import: keeps network dep off the import path

    Gaia.MAIN_GAIA_TABLE = MAIN_GAIA_TABLE
    Gaia.ROW_LIMIT = -1
    job = Gaia.launch_job_async(adql)
    return job.get_results()


# --- crossmatch entry points --------------------------------------------------------

def crossmatch_by_source_id(
    source_ids: Sequence[int], *, launch: Launch | None = None
) -> dict[int, GaiaSource]:
    """Fetch Gaia astrometry for explicit source ids. Returns {source_id: GaiaSource}."""
    launch = launch or _default_launch
    unique = list(dict.fromkeys(int(s) for s in source_ids))
    out: dict[int, GaiaSource] = {}
    for i in range(0, len(unique), _ID_BATCH):
        batch = unique[i : i + _ID_BATCH]
        table = launch(build_source_id_adql(batch))
        for src in _table_to_sources(table):
            if src.source_id is not None:
                out[src.source_id] = src
    return out


def crossmatch_cone(
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float = DEFAULT_CONE_RADIUS_ARCSEC,
    *,
    launch: Launch | None = None,
) -> GaiaSource | None:
    """Return the Gaia source NEAREST to ``(ra_deg, dec_deg)`` within the cone, or None."""
    launch = launch or _default_launch
    table = launch(build_cone_adql(ra_deg, dec_deg, radius_arcsec))
    sources = _table_to_sources(table)
    if not sources:
        return None
    return min(sources, key=lambda s: _ang_sep_deg(ra_deg, dec_deg, s.ra, s.dec))


def crossmatch(
    alerts: Sequence[Alert],
    radius_arcsec: float = DEFAULT_CONE_RADIUS_ARCSEC,
    *,
    launch: Launch | None = None,
) -> dict[str, GaiaSource]:
    """Crossmatch alerts to Gaia DR3, returning ``{alert.source_ref: GaiaSource}``.

    Alerts carrying a ``gaia_source_id`` are resolved together in one batched id query;
    the rest are cone-matched to their nearest Gaia neighbour within ``radius_arcsec``.
    Alerts with no Gaia counterpart are simply absent from the result. Empty input
    returns ``{}`` without any network call.
    """
    alerts = list(alerts)
    if not alerts:
        return {}
    launch = launch or _default_launch

    by_ref: dict[str, GaiaSource] = {}

    ided = [a for a in alerts if a.gaia_source_id is not None]
    if ided:
        id_map = crossmatch_by_source_id(
            [a.gaia_source_id for a in ided], launch=launch
        )
        for a in ided:
            src = id_map.get(int(a.gaia_source_id))
            if src is not None:
                by_ref[a.source_ref] = src

    for a in alerts:
        if a.gaia_source_id is not None:
            continue
        src = crossmatch_cone(a.ra_deg, a.dec_deg, radius_arcsec, launch=launch)
        if src is not None:
            by_ref[a.source_ref] = src

    return by_ref


def _ang_sep_deg(ra1: float, dec1: float, ra2: float | None, dec2: float | None) -> float:
    """Small-angle-safe angular separation in degrees (haversine). NaN coords sort last."""
    if ra2 is None or dec2 is None:
        return float("inf")
    lon1, lat1, lon2, lat2 = np.radians([ra1, dec1, ra2, dec2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(np.degrees(2 * np.arcsin(np.sqrt(h))))
