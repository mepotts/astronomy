"""Turn candidate links into something Find_Orb and the M1/M2 machinery can consume.

Two jobs, both fiddly enough to deserve their own module:

**Gating.** A proposed link is put through the *same* published MPC pre-fit criteria M1
applied to trkSub-grouped designations, by building a frame with the same column names and
calling the same :func:`itf_linker.fit.candidates.prefit_gate`. Reimplementing the gate for
links would let the two drift apart; the whole point of M1's funnel is that the criteria
are stated once. One extra check applies only to links, and it is the MPC's:
**>= 2 observations per object per night**, which for a link means every constituent
tracklet, not just the first and last.

**Astrometry.** Find_Orb keys objects on columns 1-12 of each record, so feeding it a link
whose tracklets carry four different trkSubs would produce four separate one-night orbits
and no link at all. The original 80-column records are therefore re-emitted with columns
6-12 **rewritten to one temporary identifier per link**. Nothing else on the line is
touched: position, magnitude, catalogue code, note fields and observatory code are the
bytes the MPC published, because M1 established that re-formatting them loses precision
and the astrometric catalogue flag Find_Orb debiases with.

The temporary identifier is deliberately un-designation-like (``lnk`` + base-36 counter,
lower case) so that neither Find_Orb nor a human can mistake it for a packed provisional
designation. **It is not a designation and it is not submitted anywhere.**
"""

from __future__ import annotations

import hashlib
import string
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from ..fit.candidates import gate_summary, prefit_gate
from ..mpc80 import CONTINUATION_NOTE2, F_DESIG, F_NOTE2, F_OBSCODE, LINE_WIDTH, parse_line
from .heliolinc import LinkCandidate

#: MPC guardrail, quoted in ``DISCOVERY/itf-linker.md``: a single position on a night
#: causes the *entire batch* to be auto-rejected, often silently.
MIN_OBS_PER_NIGHT = 2

_B36 = string.digits + string.ascii_lowercase


#: Characters of blake2b hex kept in a ``link_key``. 16 gives 64 bits, so across the 567,838
#: links a full-file run produces the chance of any collision at all is about 1e-8. 12 would
#: have been ~1e-3, which is small but not small enough for something meant to be cited.
#: Member sets are themselves exactly unique -- 0 duplicates in each of the three link tables
#: in this repo -- so the hash width is the only source of ambiguity.
LINK_KEY_CHARS = 16


def link_key(tracklets: Iterable[tuple[str, str, int]], *, prefix: str = "lk") -> str:
    """A **stable, content-addressed** identifier for a link: what it is made of.

    ``link_id`` is a positional counter, so ``lnk034r`` means "the 4,347th row of whichever
    link table this run happened to produce". Re-run the linker, change the slice, or widen
    the grid, and the same string denotes a different link -- across the two link tables in
    this repo, 13,618 ids appear in both and **not one** refers to the same link. Every id
    quoted in M3-M5, in ``SNAPSHOT-VALIDATION.md`` and in the RNAAS drafts is therefore
    meaningless outside the exact parquet it came from, which makes them uncitable and makes
    cross-run comparison silently answer the wrong question.

    A link *is* its set of member tracklets, and a tracklet is ``(desig, obscode, night)`` --
    all three straight from the ITF, none of them positional. Hashing the sorted set gives an
    id that is identical wherever the same link is rediscovered and different whenever it is
    not.

    Summary fields are **not** enough to key on, which is why this takes tracklets. On
    ``link-candidates.parquet``, 197 pairs of genuinely distinct links share their member
    trkSubs, observatory codes, MJD bounds, observation count *and* tracklet count, differing
    only in which tracklet of a trkSub they use: ``lnk0018`` and ``lnk001e`` differ in one
    arrow out of six.
    """
    joined = "\n".join(
        f"{desig}|{obscode}|{night}" for desig, obscode, night in sorted(tracklets)
    )
    digest = hashlib.blake2b(joined.encode("utf-8"), digest_size=16).hexdigest()
    return prefix + digest[:LINK_KEY_CHARS]


def link_id(index: int, prefix: str = "lnk") -> str:
    """A 7-character temporary identifier for a link: ``lnk`` plus base-36 counter.

    **Run-local.** See :func:`link_key` for one that is not, and prefer it for anything that
    leaves this run -- a citation, a cross-run join, or a published table.
    """
    n = len(prefix)
    width = 7 - n
    digits = []
    value = index
    for _ in range(width):
        digits.append(_B36[value % 36])
        value //= 36
    if value:
        raise ValueError(f"link index {index} does not fit in {width} base-36 characters")
    return prefix + "".join(reversed(digits))


def _tracklet_lookup(arrows: pl.DataFrame | None) -> dict[int, tuple[str, str, int]] | None:
    """``arrow_id -> (desig, obscode, night)``, the stable identity of one tracklet."""
    if arrows is None or arrows.height == 0:
        return None
    needed = ("arrow_id", "desig", "obscode", "night")
    if any(c not in arrows.columns for c in needed):
        return None
    return {
        int(a): (str(d), str(o), int(n))
        for a, d, o, n in zip(
            arrows["arrow_id"], arrows["desig"], arrows["obscode"], arrows["night"],
            strict=True,
        )
    }


def links_frame(
    candidates: Sequence[LinkCandidate], arrows: pl.DataFrame | None = None
) -> pl.DataFrame:
    """A per-link frame shaped exactly like M1's per-designation frame.

    ``arrows`` is the table the links were built from. Given it, every row also carries a
    ``link_key`` -- a content-addressed id derived from the member tracklets, stable across
    runs where ``desig`` is not. See :func:`link_key`. Without it ``link_key`` is null, and
    the frame is exactly what it always was.

    ``first_night`` / ``last_night`` / ``arc_days_night`` carry a **different quantity here
    than in the per-designation frame**, and the shared column names hide it. There they are
    local-night indices from :func:`itf_linker.index.tracklets.add_night`, which is the
    boundary the MPC's night counting uses. Here a :class:`LinkCandidate` has only
    ``mjd_first`` / ``mjd_last``, so they are ``int(mjd)`` -- a **UTC-day truncation**, which
    splits differently for any observatory whose night crosses UTC midnight.

    Nothing reads them: the night count that matters is ``n_nights``, computed upstream on
    real nights, and the pre-fit gate measures ``arc_days``. They exist for frame-shape
    parity. Do not start using them, and do not join the two frames on them -- populate them
    from a real night index first. Noted 2026-08-07.
    """
    lookup = _tracklet_lookup(arrows)
    rows = []
    for i, c in enumerate(candidates):
        key = None
        if lookup is not None:
            members = [lookup[a] for a in c.arrow_ids if a in lookup]
            # All or nothing: a key built from a partial member set would be a *different*
            # link's key, which is worse than not having one.
            if len(members) == len(c.arrow_ids):
                key = link_key(members)
        rows.append(
            {
                "desig": link_id(i),
                "link_key": key,
                "n_tracklets": len(c.arrow_ids),
                "n_nights": c.n_nights,
                "n_obscodes": c.n_obscodes,
                "obscodes": list(c.obscodes),
                "n_obs": c.n_obs,
                "first_night": int(c.mjd_first),
                "last_night": int(c.mjd_last),
                "first_mjd": c.mjd_first,
                "last_mjd": c.mjd_last,
                "first_trk_n_obs": c.first_trk_n_obs,
                "last_trk_n_obs": c.last_trk_n_obs,
                "min_trk_n_obs": c.min_trk_n_obs,
                "arc_days": c.arc_days,
                "arc_days_night": float(int(c.mjd_last) - int(c.mjd_first)),
                "arrow_ids": list(c.arrow_ids),
                "source_desigs": list(c.desigs),
                "cross_observatory": c.cross_observatory,
                "cross_designation": c.cross_designation,
                "pos_spread_au": c.pos_spread_au,
                "vel_spread_au_per_day": c.vel_spread_au_per_day,
                "r_au": c.r_au,
                "near_branch": c.near_branch,
                "band": str(c.extra.get("band", "belt")),
                "a_au": c.a_au,
                "e": c.e,
                "incl_deg": c.incl_deg,
                "n_hypotheses_found": c.n_hypotheses_found,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "desig": pl.String, "link_key": pl.String,
                "n_tracklets": pl.Int64, "n_nights": pl.Int64,
                "n_obscodes": pl.Int64, "obscodes": pl.List(pl.String), "n_obs": pl.Int64,
                "first_night": pl.Int64, "last_night": pl.Int64, "first_mjd": pl.Float64,
                "last_mjd": pl.Float64, "first_trk_n_obs": pl.Int64,
                "last_trk_n_obs": pl.Int64, "min_trk_n_obs": pl.Int64,
                "arc_days": pl.Float64, "arc_days_night": pl.Float64,
                "arrow_ids": pl.List(pl.Int64), "source_desigs": pl.List(pl.String),
                "cross_observatory": pl.Boolean, "cross_designation": pl.Boolean,
                "pos_spread_au": pl.Float64, "vel_spread_au_per_day": pl.Float64,
                "r_au": pl.Float64, "near_branch": pl.Boolean, "band": pl.String,
                "a_au": pl.Float64, "e": pl.Float64,
                "incl_deg": pl.Float64, "n_hypotheses_found": pl.Int64,
            }
        )
    return pl.DataFrame(rows)


def gate_links(
    candidates: Sequence[LinkCandidate], arrows: pl.DataFrame | None = None
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Apply the MPC's published pre-fit criteria, plus the >= 2-per-night rule.

    ``arrows`` is passed through to :func:`links_frame` so gated links carry a stable
    ``link_key``; see :func:`link_key` for why the positional ``desig`` is not enough.
    """
    frame = links_frame(candidates, arrows)
    if frame.height == 0:
        return frame, {"designations_considered": 0, "prefit_pass": 0}
    gated = prefit_gate(frame).with_columns(
        (pl.col("min_trk_n_obs") < MIN_OBS_PER_NIGHT).alias("reject_thin_night")
    )
    gated = gated.with_columns(
        (pl.col("prefit_pass") & ~pl.col("reject_thin_night")).alias("link_pass")
    )
    summary = gate_summary(gated)
    summary["reject_reasons"]["fewer_than_2_obs_on_some_night"] = int(
        gated["reject_thin_night"].sum()
    )
    passing = gated.filter(pl.col("link_pass"))
    summary["link_pass"] = passing.height
    summary["link_pass_cross_observatory"] = int(passing["cross_observatory"].sum())
    summary["link_pass_same_observatory"] = passing.height - int(
        passing["cross_observatory"].sum()
    )
    summary["link_pass_joins_more_than_one_trksub"] = int(passing["cross_designation"].sum())
    if "band" in gated.columns:
        # The gate bites differently per band -- a 5-day NEO window cannot produce the long
        # arcs a 21-day outer window can, so the arc rule rejects far more of the former.
        summary["by_band"] = {
            str(r["band"]): {"proposed": int(r["proposed"]), "gate_pass": int(r["passed"])}
            for r in gated.group_by("band")
            .agg(pl.len().alias("proposed"), pl.col("link_pass").sum().alias("passed"))
            .sort("proposed", descending=True)
            .to_dicts()
        }
    return gated, summary


# ----------------------------------------------------------------------------------
# Astrometry assembly
# ----------------------------------------------------------------------------------

def _night_index(mjd: float, lon_deg: float) -> int:
    import math

    return math.floor(mjd + lon_deg / 360.0 + 0.5)


def tracklet_line_index(
    designations: Iterable[str],
    obscode_lon: dict[str, float],
    src: Path | None = None,
) -> tuple[dict[tuple[str, str, int], list[str]], dict[str, Any]]:
    """Index the ITF's original 80-column records by ``(trkSub, observatory, night)``.

    One streaming pass over ``itf.txt.gz`` via :func:`itf_linker.fit.extract.extract_lines`,
    then a re-derivation of the local-night index from each record so that the lines can
    be attributed to the exact tracklet a link names. Continuation records travel with the
    observation they belong to.
    """
    from ..fit.extract import extract_lines
    from ..index.tracklets import signed_longitude

    groups, stats = extract_lines(designations, src=src)
    index: dict[tuple[str, str, int], list[str]] = {}
    dropped = 0
    for desig, lines in groups.items():
        current: tuple[str, str, int] | None = None
        for line in lines:
            note2 = line[F_NOTE2[0]]
            if note2 in CONTINUATION_NOTE2:
                if current is not None:
                    index[current].append(line)
                continue
            parsed = parse_line(line.ljust(LINE_WIDTH), strict=False)
            if parsed is None:
                dropped += 1
                current = None
                continue
            code = line[F_OBSCODE[0] : F_OBSCODE[0] + F_OBSCODE[1]].strip()
            lon = signed_longitude(obscode_lon.get(code, 0.0))
            key = (desig, code, _night_index(parsed.mjd, lon))
            index.setdefault(key, []).append(line)
            current = key
    stats["unparsable_lines"] = dropped
    stats["tracklets_indexed"] = len(index)
    return index, stats


class LineIndex:
    """The ITF's 80-column records, indexed once and reusable across many link batches.

    Building it costs one streaming pass over ``itf.txt.gz``. Fitting 400,000 links means
    fitting them in batches, and a batch that re-read the 9.36M-line file to fetch its own
    few thousand tracklets would spend more wall clock on gzip than on Find_Orb.
    """

    __slots__ = ("by_arrow", "lines", "stats")

    def __init__(
        self,
        by_arrow: dict[int, tuple[str, str, int]],
        lines: dict[tuple[str, str, int], list[str]],
        stats: dict[str, Any],
    ) -> None:
        self.by_arrow = by_arrow
        self.lines = lines
        self.stats = stats


def build_line_index(
    gated: pl.DataFrame,
    arrows: pl.DataFrame,
    obscode_lon: dict[str, float],
    src: Path | None = None,
) -> LineIndex:
    """One gz pass covering every tracklet ``gated`` names, keyed for :func:`link_astrometry`."""
    wanted_ids = sorted({int(i) for row in gated["arrow_ids"].to_list() for i in row})
    lookup = (
        arrows.filter(pl.col("arrow_id").is_in(wanted_ids))
        .select(["arrow_id", "desig", "obscode", "night"])
        .to_dicts()
    )
    by_arrow = {r["arrow_id"]: (r["desig"], r["obscode"], int(r["night"])) for r in lookup}
    index, stats = tracklet_line_index(
        {v[0] for v in by_arrow.values()}, obscode_lon, src=src
    )
    return LineIndex(by_arrow, index, stats)


def link_astrometry(
    gated: pl.DataFrame,
    arrows: pl.DataFrame,
    obscode_lon: dict[str, float],
    src: Path | None = None,
    line_index: LineIndex | None = None,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """``{link_id: [80-column lines]}`` with columns 6-12 rewritten to the link id.

    ``gated`` must carry ``desig`` (the link id) and ``arrow_ids``; ``arrows`` is the arrow
    table, which maps an arrow id back to its ``(trkSub, observatory, night)``.
    ``line_index`` reuses a :class:`LineIndex` built over a superset of ``gated``.
    """
    prebuilt = line_index is not None
    idx = line_index or build_line_index(gated, arrows, obscode_lon, src=src)
    by_arrow, index, stats = idx.by_arrow, idx.lines, dict(idx.stats)
    stats["line_index_reused"] = prebuilt

    out: dict[str, list[str]] = {}
    missing = 0
    for row in gated.select(["desig", "arrow_ids"]).to_dicts():
        new_desig = row["desig"]
        lines: list[str] = []
        ok = True
        for arrow_id in row["arrow_ids"]:
            key = by_arrow.get(int(arrow_id))
            found = index.get(key) if key else None
            if not found:
                ok = False
                break
            lines.extend(_relabel(ln, new_desig) for ln in found)
        if ok and lines:
            out[new_desig] = lines
        else:
            missing += 1
    stats["links_with_astrometry"] = len(out)
    stats["links_without_astrometry"] = missing
    return out, stats


def _relabel(line: str, new_desig: str) -> str:
    """Replace columns 1-12 with a blank number and the link's temporary identifier."""
    padded = line.ljust(LINE_WIDTH)
    start, width = F_DESIG
    return " " * start + new_desig.ljust(width)[:width] + padded[start + width :]
