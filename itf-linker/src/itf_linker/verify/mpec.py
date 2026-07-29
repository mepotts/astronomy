"""Extract the constituent observations of a published MPEC.

An identification MPEC exposes its input astrometry in one of two ways:

1. **Full 80-column blocks** (``Additional Observations:`` / ``Observations:``) -- exact
   times, positions, magnitudes. Parsed with the same :mod:`itf_linker.mpc80` code that
   reads the ITF, which is the point: one parser, both sides of the comparison.

2. **A residuals table** (``Residuals in seconds of arc``) -- one entry per constituent
   observation, giving ``YYMMDD`` + observatory code + the O-C residuals, laid out in
   two or three side-by-side columns. No positions, but a complete *inventory* of which
   observatory contributed how many observations on which night. That is exactly the
   (night, observatory) decomposition a tracklet reconstruction must reproduce.

Most identification MPECs carry only (2), so the residual table is the primary source
here and the 80-column block is a bonus when present.
"""

from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from ..mpc80 import Mpc80ParseError, Observation, gregorian_to_mjd, parse_line

_TAG_RE = re.compile(r"<[^>]+>")
_PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.DOTALL | re.IGNORECASE)

# "170924 F51  0.1+  0.1+"  /  "260722 M21    9-   10-"
_RESIDUAL_RE = re.compile(
    r"(?<![\d.])(\d{6})\s+([A-Z0-9]{3})\s{1,6}"
    r"(\d{1,3}(?:\.\d{1,2})?[+-]?)\s{1,6}(\d{1,3}(?:\.\d{1,2})?[+-]?)"
)
_MPEC_ID_RE = re.compile(r"M\.P\.E\.C\.\s+(\d{4}-[A-Z]\d+)", re.IGNORECASE)
_ID_CREDIT_RE = re.compile(r"^\s*Id\.\s+(.+?)\s*$", re.MULTILINE)

_RESID_HEADER = "Residuals in seconds of arc"
#: An MPEC can carry a *second*, much shorter residual table under this header, showing
#: only the first and last observations against the prior prediction. Those rows duplicate
#: entries already in the main table -- counting both inflates the constituent-observation
#: total (MPEC 2026-O57: 51 instead of 49). Blocks under this header are skipped.
_FIRST_LAST_HEADER = "First and last observations above in comparison with prediction"

#: Two-digit years below this pivot are read as 20xx, at or above it as 19xx.
YEAR_PIVOT = 50


def strip_html(text: str) -> str:
    """Return the MPEC's <pre> content as plain text, tags removed and entities decoded."""
    blocks = _PRE_RE.findall(text)
    body = "\n".join(blocks) if blocks else text
    return _html.unescape(_TAG_RE.sub("", body))


def _yymmdd_to_date(token: str) -> date:
    yy, mm, dd = int(token[0:2]), int(token[2:4]), int(token[4:6])
    year = 2000 + yy if yy < YEAR_PIVOT else 1900 + yy
    return date(year, mm, dd)


@dataclass
class ResidualEntry:
    """One constituent observation as listed in an MPEC residuals table."""

    obs_date: date
    obscode: str
    resid_ra: str
    resid_dec: str

    @property
    def mjd_midnight(self) -> float:
        return gregorian_to_mjd(self.obs_date.year, self.obs_date.month, self.obs_date.day)


@dataclass
class Mpec:
    """A parsed MPEC: identity, credit line, and constituent observations."""

    packed: str
    mpec_id: str | None
    headline: str | None
    identified_by: str | None
    residuals: list[ResidualEntry] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    text: str = ""

    @property
    def n_constituent(self) -> int:
        return len(self.residuals)


def _extract_headline(text: str) -> str | None:
    # The object line sits alone, centred, between the ISSN banner and the first section.
    marker = "ISSN 1523-6714"
    idx = text.find(marker)
    if idx < 0:
        return None
    for line in text[idx + len(marker) :].splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def residual_blocks(text: str) -> list[str]:
    """Return the body of each *main* ``Residuals in seconds of arc`` table.

    Scoping the regex to these blocks does two things: it drops the duplicated
    first/last-observation mini-table, and it stops ephemeris rows or orbital-element
    lines from ever being mistaken for residual entries.
    """
    lines = text.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith(_RESID_HEADER):
            preceding = [ln for ln in lines[max(0, i - 3) : i] if ln.strip()]
            is_first_last = any(_FIRST_LAST_HEADER in ln for ln in preceding)
            j = i + 1
            body: list[str] = []
            while j < len(lines) and lines[j].strip():
                body.append(lines[j])
                j += 1
            if not is_first_last:
                blocks.append("\n".join(body))
            i = j
        else:
            i += 1
    return blocks


def _extract_observation_lines(text: str) -> list[Observation]:
    out: list[Observation] = []
    for line in text.splitlines():
        raw = line.rstrip("\r\n")
        if len(raw) < 78 or len(raw) > 82:
            continue
        # Cheap discriminator before the full parse: cols 16-19 must be a plausible year.
        if not raw[15:19].isdigit():
            continue
        try:
            obs = parse_line(raw, strict=True)
        except Mpc80ParseError:
            # An MPEC <pre> block is mostly prose, orbital elements and ephemerides; most
            # 78-82 char lines are not astrometry. Failing to parse is the normal case
            # here and simply means "not an observation line".
            continue
        if obs is not None and obs.obscode:
            out.append(obs)
    return out


def parse_mpec(path: Path | str, packed: str | None = None) -> Mpec:
    """Parse a cached MPEC HTML file."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_html(raw)

    mpec_id_m = _MPEC_ID_RE.search(text)
    credit_m = _ID_CREDIT_RE.search(text)

    residuals = [
        ResidualEntry(
            obs_date=_yymmdd_to_date(m.group(1)),
            obscode=m.group(2),
            resid_ra=m.group(3),
            resid_dec=m.group(4),
        )
        for block in residual_blocks(text)
        for m in _RESIDUAL_RE.finditer(block)
    ]

    return Mpec(
        packed=packed or path.stem,
        mpec_id=mpec_id_m.group(1) if mpec_id_m else None,
        headline=_extract_headline(text),
        identified_by=credit_m.group(1).strip() if credit_m else None,
        residuals=residuals,
        observations=_extract_observation_lines(text),
        text=text,
    )


def residual_tracklets(mpec: Mpec) -> list[dict[str, Any]]:
    """Collapse an MPEC's residual entries into (night, observatory) tracklets.

    This is the MPEC's own tracklet decomposition, reconstructed independently -- the
    thing :func:`itf_linker.index.tracklets.build_tracklets` must be able to reproduce.
    """
    buckets: dict[tuple[date, str], int] = {}
    for entry in mpec.residuals:
        key = (entry.obs_date, entry.obscode)
        buckets[key] = buckets.get(key, 0) + 1
    rows = [
        {
            "obs_date": d.isoformat(),
            "obscode": code,
            "n_obs": n,
            "mjd_midnight": gregorian_to_mjd(d.year, d.month, d.day),
        }
        for (d, code), n in buckets.items()
    ]
    return sorted(rows, key=lambda r: (r["obs_date"], r["obscode"]))


def acceptance_summary(tracklets: list[dict[str, Any]]) -> dict[str, Any]:
    """Score a tracklet decomposition against the MPC's published ITF-link criteria.

    Auto-reject if: < 3 distinct nights; arc < 3 days; exactly 3 nights with arc > 15 days;
    or the arc both starts *and* ends with a single-detection tracklet.
    """
    if not tracklets:
        return {"nights": 0, "passes": False, "reasons": ["no tracklets"]}
    nights = sorted({t["obs_date"] for t in tracklets})
    mjds = [t["mjd_midnight"] for t in tracklets]
    arc = max(mjds) - min(mjds)
    ordered = sorted(tracklets, key=lambda t: t["mjd_midnight"])
    reasons: list[str] = []
    if len(nights) < 3:
        reasons.append(f"only {len(nights)} distinct nights (< 3)")
    if arc < 3:
        reasons.append(f"arc {arc:.1f} d < 3 d")
    if len(nights) == 3 and arc > 15:
        reasons.append(f"exactly 3 nights with arc {arc:.1f} d > 15 d")
    if ordered[0]["n_obs"] == 1 and ordered[-1]["n_obs"] == 1:
        reasons.append("arc both starts and ends with a single-detection tracklet")
    return {
        "nights": len(nights),
        "tracklets": len(tracklets),
        "observations": sum(t["n_obs"] for t in tracklets),
        "arc_days": round(arc, 2),
        "observatories": sorted({t["obscode"] for t in tracklets}),
        "passes": not reasons,
        "reasons": reasons,
    }
