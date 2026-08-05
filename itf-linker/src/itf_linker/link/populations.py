"""Does the widened hypothesis grid actually reach the populations it claims to?

M3's grid ran 1.4-5.6 AU and M3's own assessment named the consequence: no NEO and nothing
beyond Jupiter could be found, whatever else the linker did. M4 widens it. The claim that
follows -- "NEOs and TNOs are now reachable" -- is a claim about geometry, and it is
checkable without waiting for an ITF candidate to turn up.

The check is the same closed loop M1 used on Find_Orb, pointed at the linker instead:

1. ask **JPL Horizons** for astrometric RA/Dec of *real* objects of known dynamical class,
   from a real observatory code, on real observable nights;
2. hand the linker nothing but directions, rates, epochs and observer codes -- no
   designation, no distance, no orbit;
3. see which objects come back as a link, in which band, and at what hypothesised distance.

The objects are observed **jointly**, in one arrow set, so the run also measures whether
the widened grid merges unrelated objects: a Centaur and an Apollo in the same sweep are
exactly the confusion a wider grid risks introducing.

Nothing about the truth comes from this repo: the astrometry is Horizons', the classes are
the IAU's, and a recovered link is scored against the object identity Horizons was asked
about. Network use is a read-only HTTPS GET against the public Horizons API.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

from ..fit.verify import _ephem_rows, _horizons, horizons_astrometry
from ..index.tracklets import signed_longitude
from .arrows import build_arrows
from .heliolinc import LinkCandidate
from .pipeline import Band, link_bands


@dataclass(frozen=True, slots=True)
class PopulationTarget:
    """A real object of known class, to be re-linked from its astrometry alone.

    ``max_arc_days`` is set per target rather than globally because the bands do not share
    a window: a 12-day arc is a good test of the 21-day outer window and simply cannot be
    recovered inside the 7.75-day NEO one, so one cadence everywhere would measure the
    cadence rather than the grid.
    """

    command: str            # Horizons target specifier; the trailing ';' forces small-body
    label: str
    population: str         # what the IAU calls it
    desig: str              # <= 7 chars, the answer sheet only
    obscode: str = "F51"
    start_date: str = "2024-03-01"
    search_days: int = 200
    n_nights: int = 4
    max_arc_days: float = 10.0
    obs_per_night: int = 3
    #: Scan for the object's closest approach before choosing observing nights. An NEO
    #: spends most of its orbit at main-belt distances -- (1862) Apollo sits at 2.20 AU in
    #: March 2024 -- so testing "can the NEO band find an NEO" at an arbitrary date tests
    #: nothing. The scan is what makes the target's *observed* r match its class.
    seek_close_approach: bool = False
    scan_start: str = "2023-01-01"
    scan_days: int = 1460


#: Spread across every class the widened grid claims to reach, plus two main-belt controls
#: that M3's grid already found -- if those stop being recovered, widening has cost
#: something and the run says so directly.
_NEO = {"n_nights": 3, "max_arc_days": 4.0, "seek_close_approach": True}
_BELT = {"n_nights": 4, "max_arc_days": 10.0}
_OUTER = {"n_nights": 4, "max_arc_days": 16.0}

DEFAULT_POPULATION_TARGETS: tuple[PopulationTarget, ...] = (
    PopulationTarget("163693;", "(163693) Atira", "atira", "PATIRA", **_NEO),
    PopulationTarget("2062;", "(2062) Aten", "aten", "P2062", **_NEO),
    PopulationTarget("1862;", "(1862) Apollo", "apollo", "P1862", **_NEO),
    PopulationTarget("3200;", "(3200) Phaethon", "apollo", "P3200", **_NEO),
    PopulationTarget("433;", "(433) Eros", "amor", "P433", **_NEO),
    PopulationTarget("1036;", "(1036) Ganymed", "amor", "P1036", **_NEO),
    PopulationTarget("7;", "(7) Iris", "inner_belt", "P7", **_BELT),
    PopulationTarget("324;", "(324) Bamberga", "outer_belt", "P324", **_BELT),
    PopulationTarget("588;", "(588) Achilles", "jupiter_trojan", "P588", **_OUTER),
    PopulationTarget("2060;", "(2060) Chiron", "centaur", "P2060", **_OUTER),
    PopulationTarget("10199;", "(10199) Chariklo", "centaur", "P10199", **_OUTER),
    PopulationTarget("50000;", "(50000) Quaoar", "tno", "P50000", **_OUTER),
    PopulationTarget("20000;", "(20000) Varuna", "tno", "P20000", **_OUTER),
)

_FLOAT_RE = re.compile(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?")


def band_for_distance(r_au: float | None, bands: Sequence[Band]) -> str | None:
    """Which band's distance grid contains ``r_au`` -- the band that *should* find it."""
    if r_au is None:
        return None
    for band in bands:
        if band.grid.r_au[0] <= r_au <= band.grid.r_au[-1]:
            return band.label
    return None


def distance_track(
    command: str, obscode: str, start: str, stop: str, step: str = "10d"
) -> list[tuple[str, float]]:
    """``(date, r_helio)`` from Horizons quantity 19, sampled across a date range."""
    text = _horizons(
        {
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "'NO'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'OBSERVER'",
            "CENTER": f"'{obscode}'",
            "START_TIME": f"'{start}'",
            "STOP_TIME": f"'{stop}'",
            "STEP_SIZE": f"'{step}'",
            "QUANTITIES": "'19'",
            "CSV_FORMAT": "'YES'",
        }
    )
    out: list[tuple[str, float]] = []
    for row in _ephem_rows(text):
        head, _, tail = row.partition(",")
        found = _FLOAT_RE.findall(tail)
        if found:
            out.append((head.strip(), float(found[0])))
    return out


def heliocentric_distance(command: str, obscode: str, start: str, stop: str) -> float | None:
    """Mean heliocentric distance over a date range.

    Reported so a recovered link can be compared against the distance the object was
    *actually* at, rather than against the class it was filed under -- (1862) Apollo is an
    Apollo by perihelion and a main-belt object by where it happens to be in March 2024.
    """
    track = distance_track(command, obscode, start, stop)
    return float(np.mean([r for _, r in track])) if track else None


def closest_approach_start(target: PopulationTarget) -> str:
    """Start date placing the object's observing run near its minimum distance.

    Backs off 40 days from the minimum so the elevation and daylight cuts still have a
    couple of months of candidate nights to choose from: an object at its very closest is
    often at a small solar elongation and therefore unobservable.
    """
    stop = _add_days(target.scan_start, target.scan_days)
    track = distance_track(target.command, target.obscode, target.scan_start, stop)
    if not track:
        return target.start_date
    best = min(track, key=lambda kv: kv[1])[0]
    # Horizons stamps are "2024-Jan-05 00:00"; keep the date half.
    from ..fit.verify import _MONTHS

    date_part = best.split(" ")[0]
    y, mon, d = date_part.split("-")
    iso = f"{int(y):04d}-{_MONTHS[mon]:02d}-{int(d):02d}"
    return _add_days(iso, -40)


def _add_days(date: str, days: int) -> str:
    y, m, d = (int(x) for x in date.split("-"))
    from datetime import date as _date
    from datetime import timedelta

    return (_date(y, m, d) + timedelta(days=days)).isoformat()


def pick_nights(
    ephem: Sequence[dict[str, Any]], target: PopulationTarget
) -> list[dict[str, Any]]:
    """Choose ``n_nights`` observable nights inside ``max_arc_days``, spread out.

    Two things this must get right, both learned the hard way on the first run:

    * **A night with one usable instant is not a tracklet.** The linker needs a sky-plane
      rate, so a night contributing a single detection is dropped by
      :mod:`~itf_linker.link.arrows` and the target silently loses a night. Only dates with
      at least ``obs_per_night`` observable samples are eligible.
    * **Consecutive *observable* dates are not consecutive dates.** Indexing into the list
      of observable dates gave (1862) Apollo a 151-day arc, which no window can hold. The
      selection is by elapsed time, not by list position.
    """
    by_date: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for row in ephem:
        by_date.setdefault((row["year"], row["month"], int(row["day"])), []).append(row)
    usable = sorted(k for k, v in by_date.items() if len(v) >= target.obs_per_night)
    if not usable:
        return []
    days = [_mjd(y, m, float(d)) for y, m, d in usable]

    best: list[int] = []
    for i in range(len(usable)):
        window = [j for j in range(i, len(usable)) if days[j] - days[i] <= target.max_arc_days]
        if len(window) < target.n_nights:
            continue
        spread = np.linspace(0, len(window) - 1, target.n_nights).round().astype(int)
        picks = sorted(set(spread.tolist()))
        candidate = [window[p] for p in picks]
        if len(candidate) >= target.n_nights:
            best = candidate
            break
    if not best:  # take whatever there is, and let the scoring record the shortfall
        best = list(range(min(target.n_nights, len(usable))))

    chosen: list[dict[str, Any]] = []
    for j in best:
        chosen.extend(by_date[usable[j]][: target.obs_per_night])
    return chosen


def target_rows(
    target: PopulationTarget,
    obscodes: dict[str, tuple[float, float, float]],
    start_date: str | None = None,
) -> list[dict[str, Any]]:
    """Observation rows for one target, shaped like the parsed ITF frame."""
    start = start_date or target.start_date
    stop = _add_days(start, target.search_days)
    ephem = horizons_astrometry(target.command, target.obscode, start, stop, step="15m")
    chosen = pick_nights(ephem, target)
    lon = signed_longitude(obscodes[target.obscode][0])
    rows: list[dict[str, Any]] = []
    for row in chosen:
        mjd = _mjd(row["year"], row["month"], row["day"])
        rows.append(
            {
                "desig": target.desig,
                "obscode": target.obscode,
                "mjd": mjd,
                "ra_deg": row["ra_deg"],
                "dec_deg": row["dec_deg"],
                "mag": 20.0,
                "note2": "C",
                "night": int(np.floor(mjd + lon / 360.0 + 0.5)),
            }
        )
    return rows


def _iso_from_mjd(mjd: float) -> str:
    from datetime import date, timedelta

    return (date(1858, 11, 17) + timedelta(days=int(np.floor(mjd)))).isoformat()


def _mjd(year: int, month: int, day: float) -> float:
    from ..mpc80 import gregorian_to_mjd

    return gregorian_to_mjd(year, month, day)


def run_population_check(
    bands: Sequence[Band],
    obscodes: dict[str, tuple[float, float, float]],
    *,
    targets: Sequence[PopulationTarget] = DEFAULT_POPULATION_TARGETS,
    with_distances: bool = True,
    link_workers: int = 1,
    **link_kwargs: Any,
) -> dict[str, Any]:
    """Fetch, link and score. Returns one JSON-able report."""
    rows: list[dict[str, Any]] = []
    per_target: dict[str, dict[str, Any]] = {}
    bands = list(bands)
    for target in targets:
        start = (
            closest_approach_start(target)
            if target.seek_close_approach
            else target.start_date
        )
        got = target_rows(target, obscodes, start_date=start)
        rows.extend(got)
        entry: dict[str, Any] = {
            "label": target.label,
            "population": target.population,
            "obscode": target.obscode,
            "start_date": start,
            "observations": len(got),
            "nights": len({r["night"] for r in got}),
            "arc_days": (
                round(max(r["mjd"] for r in got) - min(r["mjd"] for r in got), 2)
                if got else 0.0
            ),
        }
        if with_distances and got:
            entry["r_helio_au"] = heliocentric_distance(
                target.command, target.obscode,
                _iso_from_mjd(min(r["mjd"] for r in got)),
                _iso_from_mjd(max(r["mjd"] for r in got) + 1.0),
            )
            entry["expected_band"] = band_for_distance(entry["r_helio_au"], bands)
        per_target[target.desig] = entry

    frame = pl.DataFrame(rows).with_columns(pl.col("night").cast(pl.Int32))
    arrows = build_arrows(frame, obscodes)
    links, report = link_bands(
        arrows, bands, link_workers=link_workers, **link_kwargs
    )
    truth = _truth_groups(arrows.table)
    for desig, entry in per_target.items():
        entry.update(_score_one(desig, truth.get(desig, frozenset()), links))

    recovered = [e for e in per_target.values() if e["recovered_exactly"]]
    return {
        "bands": [b.as_dict() for b in bands],
        "targets": len(targets),
        "arrows": arrows.table.height,
        "arrow_build": arrows.stats,
        "links": len(links),
        "recovered_exactly": len(recovered),
        "merged_with_a_stranger": sum(
            1 for e in per_target.values() if e["mixed_with_other_targets"]
        ),
        "by_target": per_target,
        "linking": report,
    }


def _truth_groups(table: pl.DataFrame) -> dict[str, frozenset[int]]:
    """Which arrow ids belong to each target -- the answer sheet, used only for scoring."""
    out: dict[str, frozenset[int]] = {}
    for desig, sub in table.group_by("desig"):
        name = desig[0] if isinstance(desig, tuple) else desig
        out[str(name)] = frozenset(int(i) for i in sub["arrow_id"].to_list())
    return out


def _score_one(
    desig: str, truth: frozenset[int], links: Sequence[LinkCandidate]
) -> dict[str, Any]:
    """Was this target recovered, by which band, at which hypothesised distance?"""
    exact: LinkCandidate | None = None
    partial: LinkCandidate | None = None
    mixed = False
    for cand in links:
        overlap = cand.key & truth
        if not overlap:
            continue
        if cand.key - truth:
            mixed = True
            continue
        if cand.key == truth:
            exact = cand
        elif partial is None or len(cand.key) > len(partial.key):
            partial = cand
    best = exact or partial
    return {
        "recovered_exactly": exact is not None,
        "recovered_partially": exact is None and partial is not None,
        "mixed_with_other_targets": mixed,
        "found_in_band": None if best is None else str(best.extra.get("band")),
        "hypothesis_r_au": None if best is None else round(best.r_au, 3),
        "hypothesis_near_branch": None if best is None else best.near_branch,
        "tracklets_in_link": None if best is None else len(best.arrow_ids),
        "tracklets_available": len(truth),
    }
