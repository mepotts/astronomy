"""The ground truth M0 demanded, and the only one the ITF can supply.

M0 established that the obvious validation -- re-deriving a published identification MPEC
-- **cannot work**: all three July-2026 identification MPECs link previously *designated*
objects, and the ITF contains zero designated and zero numbered objects, so their
observations were never in the file on any day. A 200/200 sensitivity control proved the
absence was real rather than a lookup failure.

M0's replacement is the test implemented here: **the ITF already contains 2,515
designations spanning three or more nights under a single trkSub.** Those groupings were
made by survey pipelines from data this linker also has. Hide the trkSub linkage and the
question becomes exactly the one M3 has to answer -- *do these tracklets belong together?*
-- with an answer already on file.

Hiding is not a code path, it is a property of the design: :mod:`itf_linker.link.heliolinc`
never reads a designation. Tracklets enter the linker as an epoch, a direction, a rate and
an observer, and come out grouped or not. The trkSub is used afterwards, and only to mark
the answer sheet.

Two runs, because they measure different things
-----------------------------------------------
**Isolated** -- only the ground-truth designations' own tracklets are present. This
measures recall cleanly and gives a precision figure in a sparse field, where a cluster
mixing two trkSubs is very unlikely to be a genuine undiscovered link.

**Embedded** -- the ground truth sits inside the full production population, sharing the
sky with half a million other tracklets. This measures recall against the *real*
confusion, which is the number that matters.

The one thing this test cannot do
---------------------------------
In the embedded run a cluster that mixes trkSubs is **not** a false positive: joining
tracklets that carry different trkSubs is the entire purpose of M3. So precision measured
against trkSub agreement is a *lower bound*, and it is reported as one. The real precision
filter is the orbit fit, which a chance alignment does not survive.

The ground truth is also not clean, and pretending otherwise would overstate recall. M1
flagged 538 of the 2,515 as trkSub *collisions* -- ``des278`` spans 17 nights over 1,154
days, ``soho183`` 12 nights over 3,555 days, and the longest-arc names are ``T00001``,
``object``, ``UNK``, ``obj01``. A correct linker must **fail** to recover those, so recall
is reported against both the raw set and the collision-screened subset.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from ..fit import collide
from .heliolinc import LinkCandidate


def ground_truth_groups(
    arrows: pl.DataFrame,
    *,
    min_nights: int = 3,
    max_arc_days: float | None = None,
) -> dict[str, frozenset[int]]:
    """``{trkSub: {arrow ids}}`` for designations already spanning ``min_nights`` nights.

    ``max_arc_days`` restricts to groups a windowed linker could reach at all; passing the
    window length makes the "structurally out of reach" population explicit instead of
    charging it to recall.
    """
    per = arrows.group_by("desig").agg(
        pl.col("arrow_id"),
        pl.col("night").n_unique().alias("n_nights"),
        (pl.col("mjd").max() - pl.col("mjd").min()).alias("arc_days"),
    )
    per = per.filter(pl.col("n_nights") >= min_nights)
    if max_arc_days is not None:
        per = per.filter(pl.col("arc_days") <= max_arc_days)
    return {
        r["desig"]: frozenset(int(x) for x in r["arrow_id"])
        for r in per.to_dicts()
    }


def collision_screen(arrows: pl.DataFrame, desigs: set[str]) -> set[str]:
    """The subset of ``desigs`` M1's trkSub-collision screens flag as suspect.

    Reuses :mod:`itf_linker.fit.collide` rather than re-deriving the thresholds, so the
    definition of a suspect name cannot drift between M1 and M3.
    """
    sub = arrows.filter(pl.col("desig").is_in(desigs)).select(
        ["desig", "obscode", "night", "mjd", "ra_deg", "dec_deg"]
    ).rename({"mjd": "mjd_mid"})
    if sub.height == 0:
        return set()
    motion = collide.tracklet_motion(sub)
    per = sub.group_by("desig").agg(
        (pl.col("mjd_mid").max() - pl.col("mjd_mid").min()).alias("arc_days")
    )
    screened = collide.screen(per, motion)
    return set(screened.filter(pl.col("collision_suspect"))["desig"].to_list())


def score_links(
    links: list[LinkCandidate],
    truth: dict[str, frozenset[int]],
    *,
    min_recovered: int = 3,
) -> dict[str, Any]:
    """Compare produced links against the hidden trkSub groupings.

    A truth group counts as

    ``exact``
        some produced link is exactly its arrow set;
    ``pure_partial``
        some produced link is a subset of it with at least ``min_recovered`` tracklets and
        no foreign tracklet -- the grouping was found, but not all of it;
    ``contaminated``
        the only links touching it also carry tracklets from outside it;
    ``missed``
        no produced link touches it at all.

    Precision is computed as the share of produced links whose tracklets all come from one
    truth group. **In the embedded run that is a lower bound**, because a link joining two
    different trkSubs is what M3 exists to find.
    """
    by_arrow: dict[int, str] = {}
    for name, ids in truth.items():
        for i in ids:
            by_arrow[i] = name

    exact: set[str] = set()
    pure_partial: set[str] = set()
    touched: set[str] = set()
    contaminated: set[str] = set()

    pure_links = 0
    mixed_links = 0
    novel_links = 0
    for link in links:
        ids = link.key
        names = {by_arrow.get(i) for i in ids}
        known = {n for n in names if n is not None}
        for n in known:
            touched.add(n)
        if len(names) == 1 and None not in names:
            name = next(iter(known))
            pure_links += 1
            if ids == truth[name]:
                exact.add(name)
            elif len(ids) >= min_recovered:
                pure_partial.add(name)
        elif known:
            mixed_links += 1
            for n in known:
                contaminated.add(n)
        else:
            novel_links += 1

    found = exact | pure_partial
    contaminated -= found
    missed = set(truth) - touched
    n = max(len(truth), 1)
    total_links = max(len(links), 1)
    return {
        "truth_groups": len(truth),
        "recovered_exact": len(exact),
        "recovered_pure_partial": len(pure_partial),
        "contaminated_only": len(contaminated),
        "missed_entirely": len(missed),
        "recall_exact": round(len(exact) / n, 4),
        "recall_pure": round(len(found) / n, 4),
        "recall_touched": round(len(touched) / n, 4),
        "links_total": len(links),
        "links_pure_single_trksub": pure_links,
        "links_mixing_a_truth_group_with_others": mixed_links,
        "links_touching_no_truth_group": novel_links,
        "precision_lower_bound": round(pure_links / total_links, 4),
        "missed_examples": sorted(missed)[:20],
        "contaminated_examples": sorted(contaminated)[:20],
    }
