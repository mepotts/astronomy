"""MPChecker -- the MPC's own answer to "is there already a known object here?".

This is the authority the other two services are approximating: it runs against the MPC's
element files, which is the same catalogue an identification would eventually be submitted
against. It is also the crankiest of the three, and four things about it had to be found by
experiment.

**The endpoint in the project plan is the wrong one.** ``checkmp.cgi`` exists and answers,
but answers every well-formed query with *"A serious error has occurred in a WebCS
script... Invalid data (R1/017/000/001)"* and the note that *"any use of WebCS scripts via
a route other than our on-line forms is unsupported"*. The form's own ``ACTION`` is
``/cgi-bin/mpcheck.cgi``, and that one works.

**GET works**, although the form declares ``METHOD=POST``. That matters here because this
project's rule is that every external call is a read-only GET.

**The ``day`` field takes full precision.** ``maxlength=5`` on the form input is a
client-side hint only; ``day=18.093279`` is accepted and moves the returned position by
~15" against ``day=18.09``. Sending the truncated value would have put a 0.01-day (14-minute)
smear -- several arcseconds of main-belt motion -- into every separation this module
reports.

**Comets are not in the catalogue before 2009.** From the form's own notes: for dates
1900-2009 comparisons use *"elements at the nearest 200-day epoch"* and cover only numbered
and perturbed unnumbered minor planets, while *"for more recent dates, all objects are
included (including comets)"*. That is exactly why the 73P-C positive control returns
nothing here and everything from SkyBoT -- a coverage gap, not a negative result, and
:func:`coverage_gap` labels it so the verdict cannot mistake one for the other.

Positions are quoted to 0.1 s in RA and 1" in Dec, so separations from this service have a
~1" quantisation floor. They are computed from those positions rather than from the
``Offsets`` columns, which are rounded to 0.1 arcminute (6").
"""

from __future__ import annotations

import html
import re
from typing import Any

from .cache import CachedSession, ServiceUnavailable
from .types import ServiceMatch, angular_sep_arcsec

MPCHECKER_URL = "https://minorplanetcenter.net/cgi-bin/mpcheck.cgi"
SERVICE = "mpchecker"

#: The MPC's own stated cut: comets (and unperturbed unnumbered objects) are absent from
#: the element files used for dates before this one.
COMET_COVERAGE_FROM_YEAR = 2009
#: Before 1900 only the first 500 numbered minor planets are included.
MINIMAL_COVERAGE_BEFORE_YEAR = 1900

#: Search radius bounds the form enforces, in arcminutes.
RADIUS_MIN_ARCMIN, RADIUS_MAX_ARCMIN = 1.0, 300.0

_PRE = re.compile(r"<pre>(.*?)</pre>", re.DOTALL | re.IGNORECASE)
#: ``(130536) 2000 QV208      20 50 51.3 -22 02 23  19.5   2.8E   2.8N ...``
_ROW = re.compile(
    r"^\s*(?P<name>\S.*?)\s{2,}"
    r"(?P<ra>\d{1,2} \d{2} \d{2}(?:\.\d+)?)\s+"
    r"(?P<dec>[-+]\d{1,2} \d{2} \d{2}(?:\.\d+)?)\s+"
    r"(?P<rest>.*)$"
)
_NO_MATCH = re.compile(r"No known minor planets.*were found", re.IGNORECASE | re.DOTALL)


def coverage_gap(year: int) -> str | None:
    """Why a null answer from MPChecker at ``year`` may not mean "nothing is there"."""
    if year < MINIMAL_COVERAGE_BEFORE_YEAR:
        return "MPChecker covers only the first 500 numbered minor planets before 1900"
    if year < COMET_COVERAGE_FROM_YEAR:
        return (
            f"MPChecker excludes comets and unperturbed unnumbered objects before "
            f"{COMET_COVERAGE_FROM_YEAR}, and uses 200-day element epochs"
        )
    return None


def _sexa_ra(token: str) -> float | None:
    try:
        h, m, s = (float(x) for x in token.split())
    except (TypeError, ValueError):
        return None
    return 15.0 * (h + m / 60.0 + s / 3600.0)


def _sexa_dec(token: str) -> float | None:
    parts = token.split()
    if len(parts) != 3:
        return None
    try:
        d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    except ValueError:
        return None
    sign = -1.0 if parts[0].lstrip().startswith("-") else 1.0
    return sign * (abs(d) + m / 60.0 + s / 3600.0)


def parse_result(
    body: str, *, ra_deg: float, dec_deg: float, obs_index: int, mjd_utc: float
) -> tuple[list[ServiceMatch], str | None]:
    """Return ``(matches, error)`` from one MPChecker HTML page."""
    text = html.unescape(body)
    if "Error from WebCS Script" in text:
        note = re.search(r'error message is "(.*?)"', text, re.DOTALL)
        return [], f"MPChecker rejected the query: {note.group(1).strip() if note else 'unknown'}"
    block = _PRE.search(text)
    if block is None:
        if _NO_MATCH.search(text) or "were found in the" not in text:
            return [], None
        return [], "MPChecker returned no <pre> table and no recognised 'none found' banner"

    out: list[ServiceMatch] = []
    for line in block.group(1).splitlines():
        if not line.strip() or "Object designation" in line or line.lstrip().startswith("h  m"):
            continue
        m = _ROW.match(line.rstrip())
        if not m:
            continue
        ra_m, dec_m = _sexa_ra(m.group("ra")), _sexa_dec(m.group("dec"))
        if ra_m is None or dec_m is None:
            continue
        rest = m.group("rest").split()
        v_mag: float | None = None
        if rest and re.fullmatch(r"\d+\.\d+", rest[0]):
            v_mag = float(rest[0])
        orbit_desc = next((tok for tok in rest if re.fullmatch(r"\d+[od]|V", tok)), None)
        out.append(
            ServiceMatch(
                service=SERVICE,
                raw_name=m.group("name").strip(),
                sep_arcsec=angular_sep_arcsec(ra_deg, dec_deg, ra_m, dec_m),
                v_mag=v_mag,
                orbit_class=orbit_desc,   # oppositions / arc-days / Vaisala, MPC's own tag
                obs_index=obs_index,
                mjd_utc=mjd_utc,
            )
        )
    return out, None


def check_position(
    session: CachedSession,
    *,
    year: int,
    month: int,
    day: float,
    ra_deg: float,
    dec_deg: float,
    obscode: str,
    radius_arcmin: float = 5.0,
    limit_mag: float = 25.0,
    obs_index: int = -1,
    mjd_utc: float | None = None,
    timeout: float = 180.0,
) -> tuple[list[ServiceMatch], str | None]:
    """One MPChecker query at one position and instant. Returns ``(matches, error)``."""
    radius = min(max(radius_arcmin, RADIUS_MIN_ARCMIN), RADIUS_MAX_ARCMIN)
    params = {
        "year": f"{year:04d}",
        "month": f"{month:02d}",
        "day": f"{day:09.6f}",
        "which": "pos",
        "ra": _fmt_ra(ra_deg),
        "decl": _fmt_dec(dec_deg),
        "TextArea": "",
        "radius": f"{radius:g}",
        "limit": f"{limit_mag:.1f}",
        "oc": obscode,
        "sort": "d",
        "mot": "h",
        "tmot": "s",
        "pdes": "u",
        "needed": "f",
        "ps": "n",
        "type": "p",
    }
    try:
        resp = session.get(SERVICE, MPCHECKER_URL, params, timeout=timeout)
    except ServiceUnavailable as exc:
        return [], str(exc)
    return parse_result(
        resp.text,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        obs_index=obs_index,
        mjd_utc=mjd_utc if mjd_utc is not None else 0.0,
    )


def _fmt_ra(deg: float) -> str:
    """``HH MM SS.dd`` -- one of the input forms the form's own notes list as valid."""
    total_s = round((deg % 360.0) / 15.0 * 3600.0, 2) % 86400.0
    h, rem = divmod(total_s, 3600.0)
    m, s = divmod(rem, 60.0)
    return f"{int(h):02d} {int(m):02d} {s:05.2f}"


def _fmt_dec(deg: float) -> str:
    """``sDD MM SS.d`` -- the sign is mandatory, per the form's notes."""
    sign = "-" if deg < 0 else "+"
    total_s = round(abs(deg) * 3600.0, 1)
    d, rem = divmod(total_s, 3600.0)
    m, s = divmod(rem, 60.0)
    return f"{sign}{int(d):02d} {int(m):02d} {s:04.1f}"


def parse_objects_checked(body: str) -> int | None:
    """How many objects the MPC actually compared against -- a truncation guard it asks for."""
    m = re.search(r"Number of objects checked\s*=\s*(\d+)", body)
    return int(m.group(1)) if m else None


def as_dict(matches: list[ServiceMatch]) -> list[dict[str, Any]]:
    return [m.as_dict() for m in matches]
