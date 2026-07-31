"""Adapters that turn *something* into :class:`~itf_linker.vet.types.VetCandidate`.

The vetting stage is deliberately ignorant of where candidates come from, so every source
needs a small translation here rather than a special case inside the stage. Three exist:

* :func:`from_mpc80_lines` -- the universal one. Any producer that can emit MPC 80-column
  astrometry (ITF extraction, a linker, DAD's pre-generated records, a hand-typed field)
  goes through this.
* :func:`from_m1_report` -- attaches M1's fitted orbits to the ITF astrometry, so element
  comparison is available for the designations M1 ranked.
* :func:`horizons_control` -- synthesises a candidate for a *known* object from JPL
  Horizons astrometry. This is the negative-control generator: an object whose right answer
  is known in advance, pushed through the identical code path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..mpc80 import LINE_WIDTH, parse_line
from .types import OrbitElements, VetCandidate, VetObservation

_ELEMENT_FIELDS = (
    "epoch_jd", "a", "e", "incl", "q", "asc_node", "arg_per", "mean_anom",
    "sigma_a", "sigma_e", "sigma_i", "sigma_q",
)


def elements_from_fit(row: dict[str, Any], source: str = "Find_Orb (itf-linker M1)") -> OrbitElements:
    """Read a fitted orbit out of an M1 ``ranked``/``outcomes`` row."""
    return OrbitElements(**{k: row.get(k) for k in _ELEMENT_FIELDS}, source=source)


def from_mpc80_lines(
    desig: str,
    lines: list[str],
    *,
    elements: OrbitElements | None = None,
    origin: str = "",
) -> VetCandidate:
    """Build a candidate from its original 80-column records.

    Continuation lines (``s``/``v``/``r``) are skipped: they carry a spacecraft's geocentric
    x/y/z in the RA/Dec columns, not a sky position, and feeding one to a cone search would
    query a point that does not exist.
    """
    obs: list[VetObservation] = []
    for raw in lines:
        line = raw.ljust(LINE_WIDTH)
        parsed = parse_line(line, strict=False)
        if parsed is None or parsed.ra_deg is None or parsed.dec_deg is None:
            continue
        obs.append(
            VetObservation(
                mjd_utc=parsed.mjd,
                ra_deg=parsed.ra_deg,
                dec_deg=parsed.dec_deg,
                obscode=parsed.obscode,
                mag=parsed.mag,
                band=parsed.band,
            )
        )
    obs.sort(key=lambda o: o.mjd_utc)
    return VetCandidate(
        desig=desig,
        observations=tuple(obs),
        elements=elements,
        origin=origin,
        mpc80_lines=tuple(lines),
    )


def from_m1_report(
    report_path: Path,
    astrometry_path: Path,
    *,
    section: str = "ranked",
    limit: int | None = None,
    origin: str = "itf-linker M1",
) -> list[VetCandidate]:
    """Every designation in an M1 report section, with its fitted orbit and its astrometry.

    ``astrometry_path`` is the JSON produced by
    ``itf-linker vet-extract`` -- the original 80-column lines pulled back out of the ITF
    snapshot, which is the only faithful source for them (see ``fit/extract.py``).
    """
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    lines_by_desig = json.loads(Path(astrometry_path).read_text(encoding="utf-8"))["lines"]
    rows = report["fits"][section]
    if limit:
        rows = rows[:limit]
    out: list[VetCandidate] = []
    for row in rows:
        desig = row["desig"]
        lines = lines_by_desig.get(desig)
        if not lines:
            continue
        out.append(
            from_mpc80_lines(
                desig, lines, elements=elements_from_fit(row), origin=origin
            )
        )
    return out


def horizons_control(
    label: str,
    horizons_rows: list[dict[str, Any]],
    obscode: str,
    *,
    nights: int = 3,
    per_night: int = 1,
    origin: str = "positive control (JPL Horizons)",
) -> VetCandidate:
    """A candidate synthesised from Horizons positions for an object we already know.

    The point is that the vetting stage must not be able to tell this apart from a real
    candidate: same dataclass, same query plan, same classifier. If it fails to identify an
    object whose position came from JPL's own ephemeris, the stage is broken.
    """
    by_date: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for row in horizons_rows:
        by_date.setdefault((row["year"], row["month"], int(row["day"])), []).append(row)
    chosen: list[VetObservation] = []
    for key in sorted(by_date)[:nights]:
        for row in by_date[key][:per_night]:
            mjd = _gregorian_mjd(row["year"], row["month"], row["day"])
            chosen.append(
                VetObservation(
                    mjd_utc=mjd, ra_deg=row["ra_deg"], dec_deg=row["dec_deg"],
                    obscode=obscode, night=key[2],
                )
            )
    return VetCandidate(desig=label, observations=tuple(chosen), origin=origin)


def _gregorian_mjd(year: int, month: int, day: float) -> float:
    from ..mpc80 import gregorian_to_mjd

    return gregorian_to_mjd(year, month, day)
