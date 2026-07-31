"""JPL Small-Body Identification -- the independent second opinion on a position.

SBIDENT answers the same question as SkyBoT from a completely different stack: JPL's own
orbit catalogue, JPL's own integrator, JPL's own observatory table. Agreement between the
two is therefore worth much more than two queries against one service would be.

Two things about it had to be measured rather than assumed, and both shape how it is used:

**It does not accept user-supplied orbital elements.** The M2 brief expected it to, and the
published parameter list settles it: the object being identified is always *"whatever JPL
knows about"*, and the user supplies an observer, a time and a field of view. There is no
element-based mode. Element-space corroboration is therefore done afterwards, by resolving
each returned match in the SBDB and comparing its catalogue orbit against the fitted one
(:func:`itf_linker.vet.sbdb.compare_elements`).

**The first pass is not an identification.** With ``two-pass=false`` the API returns a
coarse pre-filter: 5,455 objects for a 2025 Rubin field and **242,791** for a 2006 one,
with quoted positional errors around 1.6 x 10^5 arcsec -- 44 degrees. Those rows are not
candidates; they are the set the second pass will integrate. Only ``two-pass=true`` with
``suppress-first-pass=true`` produces positions worth comparing, and that is what this
module always requests.

The cost of that decision is real and is the reason SBIDENT is used as an escalation
rather than a sweep: the second pass integrates every first-pass survivor, so its runtime
scales with how badly the coarse filter did. Measured: ~35 s for a 2025 epoch, and a
timeout past 180 s for a 2006 epoch, where 20 years of two-body back-propagation leaves the
pre-filter unable to reject anything.
"""

from __future__ import annotations

import time
from typing import Any

from .cache import CachedSession, ServiceUnavailable
from .types import ServiceMatch, angular_sep_arcsec

SBIDENT_URL = "https://ssd-api.jpl.nasa.gov/sb_ident.api"
SERVICE = "sbident"

#: Beyond this many first-pass rows the second pass has too many orbits to integrate and
#: the request times out. Measured directly, by asking for first-pass-only counts on one
#: fixed field from observatory 703 at seven epochs (2026-07-29):
#:
#:     epoch   first-pass rows        epoch   first-pass rows
#:     2026     6,469                 2014     93,390
#:     2023     5,355                 2010    189,980
#:     2020    11,377                 2006    308,897
#:     2017    37,889
#:
#: The count is flat for a few years and then climbs by a factor of ~50 over two decades:
#: the pre-filter propagates catalogue elements with a two-body model, so its positional
#: error grows without bound and it stops being able to reject anything. A two-pass request
#: at a 2025 epoch (5,455 rows) returns in ~35 s; one at a 2006 epoch does not return at
#: all inside 200 s, twice, measured.
FIRST_PASS_BUDGET = 60000

#: How far back SBIDENT is asked at all. Between the 2017 and 2014 rows above the first
#: pass crosses the budget, so a request older than this is refused *before* it is sent.
#: That is a politeness decision as much as a practical one: sending it anyway spends
#: several minutes of JPL's CPU to learn something already measured.
MAX_LOOKBACK_YEARS = 9.0
_DAYS_PER_YEAR = 365.25


def too_old(jd_utc: float, now_jd: float | None = None) -> str | None:
    """Reason to skip SBIDENT at this epoch, or ``None`` if it is worth asking."""
    if now_jd is None:
        now_jd = time.time() / 86400.0 + 2440587.5
    years = (now_jd - jd_utc) / _DAYS_PER_YEAR
    if years <= MAX_LOOKBACK_YEARS:
        return None
    return (
        f"epoch is {years:.1f} years old; SBIDENT's two-pass exceeds its budget beyond "
        f"~{MAX_LOOKBACK_YEARS:.0f} years (first pass grows past {FIRST_PASS_BUDGET:,} rows) "
        "and the request would time out"
    )


def _hms(deg: float) -> str:
    """Degrees -> ``hh-mm-ss.ss``, the FOV-centre format the API documents.

    Rounding happens *before* the split, not inside the format string. Formatting a
    residual 59.996 s as ``%05.2f`` produces ``60.00`` and an hour that never existed --
    which the service would either reject or, worse, silently misread.
    """
    total_s = round((deg % 360.0) / 15.0 * 3600.0, 2) % 86400.0
    h, rem = divmod(total_s, 3600.0)
    m, s = divmod(rem, 60.0)
    return f"{int(h):02d}-{int(m):02d}-{s:05.2f}"


def _dms(deg: float) -> str:
    """Degrees -> ``[-]dd-mm-ss.s``, rounded before splitting for the same reason."""
    sign = "-" if deg < 0 else ""
    total_s = round(abs(deg) * 3600.0, 1)
    d, rem = divmod(total_s, 3600.0)
    m, s = divmod(rem, 60.0)
    return f"{sign}{int(d):02d}-{int(m):02d}-{s:04.1f}"


def _f(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_ra(token: str) -> float | None:
    try:
        h, m, s = (float(x) for x in str(token).strip().split(":"))
    except (TypeError, ValueError):
        return None
    return 15.0 * (h + m / 60.0 + s / 3600.0)


def _parse_dec(token: str) -> float | None:
    txt = str(token).strip().replace('"', "").replace("'", " ")
    parts = txt.split()
    if len(parts) < 3:
        return None
    try:
        d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    except ValueError:
        return None
    sign = -1.0 if parts[0].lstrip().startswith("-") else 1.0
    return sign * (abs(d) + m / 60.0 + s / 3600.0)


def parse_identify(
    payload: dict[str, Any],
    *,
    ra_deg: float,
    dec_deg: float,
    obs_index: int,
    mjd_utc: float,
) -> tuple[list[ServiceMatch], str | None, int | None]:
    """Return ``(matches, error, n_first_pass)`` from one ``sb_ident.api`` reply.

    Separations are recomputed here from the returned astrometric RA/Dec rather than read
    from the API's own ``Dist. from center Norm (")`` column: that column is quoted to two
    significant figures (``"1.E4"``), which is useless at the arcsecond scale an
    identification is decided on.
    """
    n_first = payload.get("n_first_pass")
    n_first = int(n_first) if _f(n_first) is not None else None

    fields = payload.get("fields_second")
    rows = payload.get("data_second_pass")
    if fields is None or rows is None:
        if payload.get("warning"):
            return [], None, n_first  # "no matching records" is an answer, not a failure
        if n_first is not None:
            return [], (
                f"no second pass returned (first pass {n_first} rows); "
                "the request most likely exceeded the service's budget"
            ), n_first
        return [], f"unexpected SBIDENT reply keys: {sorted(payload)}", n_first

    idx = {name: i for i, name in enumerate(fields)}
    name_i = idx.get("Object name", 0)
    ra_i = next((i for k, i in idx.items() if k.startswith("Astrometric RA")), None)
    dec_i = next((i for k, i in idx.items() if k.startswith("Astrometric Dec")), None)
    vmag_i = next((i for k, i in idx.items() if k.startswith("Visual magnitude")), None)

    out: list[ServiceMatch] = []
    for row in rows:
        if not isinstance(row, list) or not row:
            continue
        sep = None
        if ra_i is not None and dec_i is not None:
            ra_m, dec_m = _parse_ra(row[ra_i]), _parse_dec(row[dec_i])
            if ra_m is not None and dec_m is not None:
                sep = angular_sep_arcsec(ra_deg, dec_deg, ra_m, dec_m)
        out.append(
            ServiceMatch(
                service=SERVICE,
                raw_name=str(row[name_i]).strip(),
                sep_arcsec=sep,
                v_mag=_f(row[vmag_i]) if vmag_i is not None else None,
                obs_index=obs_index,
                mjd_utc=mjd_utc,
            )
        )
    return out, None, n_first


def identify(
    session: CachedSession,
    *,
    ra_deg: float,
    dec_deg: float,
    jd_utc: float,
    obscode: str,
    hwidth_deg: float,
    obs_index: int = -1,
    mjd_utc: float | None = None,
    timeout: float = 240.0,
) -> tuple[list[ServiceMatch], str | None, int | None]:
    """One two-pass identification. Returns ``(matches, error, n_first_pass)``."""
    params = {
        "mpc-code": obscode,
        "obs-time": f"{jd_utc:.6f}",
        "fov-ra-center": _hms(ra_deg),
        "fov-dec-center": _dms(dec_deg),
        "fov-ra-hwidth": f"{hwidth_deg:.4f}",
        "fov-dec-hwidth": f"{hwidth_deg:.4f}",
        "two-pass": "true",
        "suppress-first-pass": "true",
        "mag-required": "false",
        "req-elem": "false",
    }
    try:
        # One retry, not three: a timeout here means the second pass has more orbits than
        # it can integrate, and repeating a four-minute computation cannot change that.
        resp = session.get(SERVICE, SBIDENT_URL, params, timeout=timeout, max_retries=1)
    except ServiceUnavailable as exc:
        return [], str(exc), None
    try:
        payload = resp.json()
    except ValueError:
        return [], "unparseable SBIDENT reply", None
    return parse_identify(
        payload,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        obs_index=obs_index,
        mjd_utc=mjd_utc if mjd_utc is not None else jd_utc - 2400000.5,
    )
