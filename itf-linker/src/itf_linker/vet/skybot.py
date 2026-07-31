"""IMCCE SkyBoT cone search -- "what known solar-system object was here, then?".

SkyBoT is the cheapest of the three positional services by a wide margin (a JSON reply in
about a second, against 20+ s for SBIDENT and 5+ s for MPChecker) and it covers 1889-2060,
so it is used as the *primary* sweep: every queried epoch of every candidate goes through
it. The other two corroborate.

It also returns something the others do not: ``Err (arcsec)``, the service's own estimate
of how uncertain the ephemeris it just computed is. That turns a separation into a
meaningful statement -- 30" from an object whose ephemeris is good to 0.7" is a different
claim from 30" from one good to 60" -- and :mod:`itf_linker.vet.verdict` uses it directly.

Endpoint: ``https://ssp.imcce.fr/webservices/skybot/api/conesearch.php``. ``-mime=json``
returns a bare JSON array of matches, or a JSON object carrying an error/`data` key
depending on the failure; both shapes are handled. ``-filter=0`` disables SkyBoT's own
uncertainty cut, because deciding what is too uncertain is this module's job and hiding a
match would silently turn "known" into "unmatched".
"""

from __future__ import annotations

import json
from typing import Any

from .cache import CachedSession, ServiceUnavailable
from .types import ServiceMatch

SKYBOT_URL = "https://ssp.imcce.fr/webservices/skybot/api/conesearch.php"
SERVICE = "skybot"

#: SkyBoT's database epoch coverage, from its own documentation.
COVERAGE_JD = (2411368.0, 2473460.0)  # 1889-01-01 .. 2060-01-01, approximately


def _f(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_conesearch(text: str) -> tuple[list[dict[str, Any]], str | None]:
    """Return ``(rows, error)`` from a ``-mime=json`` cone-search body."""
    body = text.strip()
    if not body:
        return [], None
    try:
        payload = json.loads(body)
    except ValueError:
        # SkyBoT falls back to a plain-text banner on some failures.
        low = body.lower()
        if "no solar system object" in low or "0 objects" in low:
            return [], None
        return [], f"unparseable SkyBoT reply: {body[:160]}"
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)], None
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], list):
            return [r for r in payload["data"] if isinstance(r, dict)], None
        for key in ("error", "message", "flag"):
            if payload.get(key):
                return [], f"SkyBoT error: {payload[key]}"
        return [], None
    return [], f"unexpected SkyBoT payload type {type(payload).__name__}"


def rows_to_matches(rows: list[dict[str, Any]], obs_index: int, mjd: float) -> list[ServiceMatch]:
    out: list[ServiceMatch] = []
    for row in rows:
        out.append(
            ServiceMatch(
                service=SERVICE,
                raw_name=str(row.get("Name", "")).strip(),
                orbit_class=row.get("Class"),
                sep_arcsec=_f(row.get("d (arcsec)")),
                ephem_err_arcsec=_f(row.get("Err (arcsec)")),
                v_mag=_f(row.get("VMag (mag)")),
                obs_index=obs_index,
                mjd_utc=mjd,
            )
        )
    return out


def cone_search(
    session: CachedSession,
    *,
    ra_deg: float,
    dec_deg: float,
    jd_utc: float,
    obscode: str,
    radius_deg: float,
    obs_index: int = -1,
    mjd_utc: float | None = None,
) -> tuple[list[ServiceMatch], str | None]:
    """One cone search. Returns ``(matches, error)``."""
    params = {
        "-ra": f"{ra_deg:.7f}",
        "-dec": f"{dec_deg:+.7f}",
        "-rd": f"{radius_deg:.5f}",
        "-ep": f"{jd_utc:.6f}",
        "-loc": obscode,
        "-mime": "json",
        "-output": "all",
        "-filter": "0",
        "-objFilter": "111",   # asteroids + comets + planets/satellites: exclude nothing
        "-from": "itf-linker-vet",
    }
    try:
        # 45 s, not 90. Measured over ~450 live cone searches, a successful reply takes a
        # median of 4.9 s and never more than 15.4 s, so anything past 45 s is not going to
        # arrive -- and holding the connection open longer only costs IMCCE a worker.
        resp = session.get(SERVICE, SKYBOT_URL, params, timeout=45)
    except ServiceUnavailable as exc:
        return [], str(exc)
    rows, err = parse_conesearch(resp.text)
    if err:
        return [], err
    return rows_to_matches(rows, obs_index, mjd_utc if mjd_utc is not None else jd_utc - 2400000.5), None


def covers(jd_utc: float) -> bool:
    return COVERAGE_JD[0] <= jd_utc <= COVERAGE_JD[1]
