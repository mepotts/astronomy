"""M13: build the MPC identifications payload from the review queue. It never sends.

This is the last piece of machinery between a finished ledger and a claim on the record,
and it deliberately stops one step short of making that claim. It reads the review queue,
re-checks every row against the *current* ITF, refuses the ones that cannot safely go, and
writes a JSON file. Uploading that file is a human action, per
``DISCOVERY/itf-linker.md`` §Guardrails item 1: **automated end-to-end submission is out of
scope permanently.** There is no network code in this module and there should never be.

**Why the refusals are the product.** Emitting a payload is fifteen lines. Everything else
here exists because of how the MPC's pipeline fails:

* **Guardrail 5 — fewer than two observations of an object on a night causes the ENTIRE
  batch to be auto-rejected, often silently.** One bad row does not cost you one row, it
  costs you the submission and tells you nothing. So a row that cannot prove it has two
  observations on its night is dropped before it can poison the others.
* **The queue decays underneath you.** M12 measured the ITF draining at 4.4 departures per
  arrival: a row marked ``STILL_LIVE`` when the queue was built on 2026-08-23 may since
  have disappeared from the current file. Absence alone does not prove that the MPC made
  an identification or establish a destination. Every tracklet is therefore re-looked-up
  in the current ITF parquet, and a tracklet that is no longer there is held back pending
  an independent published-record check.
* **Designations must be PACKED** (``K19XXYY``, ``s2334``), which the queue's ``object``
  column is not. A designation that will not pack is dropped rather than sent raw.

**Dropping, not refusing the batch.** A single unsafe row would sink the whole upload, so
the safe batch is the one that excludes it. But nothing is dropped quietly: every drop is
printed with its reason and written to a companion report next to the payload. If *no*
rows survive, the tool writes no payload at all rather than an empty one.

**Dates, and why only three columns are read.** The format spec allows ``YYYYMMDD`` and
says the date "can be from ANY observation in the tracklet", so the date is derived from
the tracklet's own MJD. That leaves this tool needing nothing but ``desig``, ``obscode``
and ``mjd`` -- which is exactly the **slim key set the archive publishes as a GitHub
release asset**, so it runs unchanged on a runner where the MPC is unreachable. The
queue's night integer is never inverted into a date: that arithmetic is
observatory-longitude dependent and would be off by a day at the wrong longitude.

Run ``scripts/m10_refresh.py --series`` first. This tool checks liveness against the ITF
itself, which catches consumption, but the refresh is what updates the queue's own
bookkeeping.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import polars as pl
from m9_reconstruct_snapshot import with_night
from m10_pointed import packed_provisional

from itf_linker.ingest.fetch import fetch_obscodes

#: The MPC auto-rejects a whole batch over a single object-night with one observation.
MIN_OBS_PER_NIGHT = 2

#: ``trksub@obscode/nNIGHT``, as the review queue writes it.
TRACKLET_RE = re.compile(r"^(?P<trksub>[^@]+)@(?P<obscode>[^/]+)/n(?P<night>\d+)$")


def parse_tracklets(cell: str) -> list[dict[str, Any]]:
    out = []
    for part in (p.strip() for p in cell.split(";")):
        if not part:
            continue
        m = TRACKLET_RE.match(part)
        if not m:
            raise ValueError(f"unparseable tracklet cell: {part!r}")
        out.append({"trksub": m.group("trksub"), "obscode": m.group("obscode"),
                    "night": int(m.group("night"))})
    return out


def load_itf_nights(itf: Path) -> pl.DataFrame:
    """Every ITF observation, tagged with the same local night the queue used.

    ``with_night`` is M9's, and the longitude table is the archive's own, so "night" here
    means exactly what it means in every sweep and in the queue's tracklet ids.
    """
    lon = fetch_obscodes()
    lon_df = pl.DataFrame({
        "obscode": list(lon.keys()),
        "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()],
    })
    # Only desig/obscode/mjd are read, which is exactly the SLIM key set the archive
    # publishes as a release asset (`observations-<sid>.parquet`). That matters: it is
    # what lets this run on a GitHub runner, where the MPC is unreachable but the release
    # is not. The full local parquet has year/month/day columns too; they are deliberately
    # not used, so one code path serves both.
    frame = pl.scan_parquet(itf).select("desig", "obscode", "mjd")
    return (
        with_night(frame, lon_df)
        .group_by("desig", "obscode", "night")
        .agg(pl.len().alias("n_obs"), pl.col("mjd").min().alias("mjd"),
             pl.col("mjd").max().alias("mjd_hi"))
        .collect()
    )


#: MJD of the Unix epoch. The date arithmetic below is exact on the integer day.
MJD_UNIX_EPOCH = 40587


def obs_date(mjd: float) -> str:
    """``YYYYMMDD`` for an observation epoch.

    The format spec allows ``YYYYMMDD`` and says the date "can be from ANY observation in
    the tracklet", so the floor of the earliest MJD in the tracklet is a valid answer and
    needs no sub-day precision. Derived from MJD rather than from the queue's night
    integer, which is observatory-longitude dependent and would be off by a day at the
    wrong longitude.
    """
    days = math.floor(mjd) - MJD_UNIX_EPOCH
    return (dt.date(1970, 1, 1) + dt.timedelta(days=days)).strftime("%Y%m%d")


def skybot_reasons(cell: str) -> list[str]:
    """Classify a skybot cell, one segment per tracklet, separated by ``|``.

    Reading this column naively is a trap and it cost a run. ``m10_review_queue.skybot_cell``
    emits ``nearest other N"`` **only when nothing else was found** -- it is the *reassuring*
    branch, reporting how far away the closest unrelated object was -- so a check like
    ``startswith("clean")`` rejects 411 of the queue's 679 perfectly clean rows on the
    strength of their phrasing. The genuinely bad segments are ``CONFLICT`` and, subject to
    adjudication, ``lost-object claimant``.

    ``object itself present`` is also fine: the object being attributed to is *supposed* to
    be in its own cone.

    Anything unrecognised refuses. A cell this code does not understand is not a cell it may
    approve -- which is also what quarantines M7's two manually cone-searched rows.
    """
    out: list[str] = []
    for raw in cell.split("|"):
        seg = raw.strip()
        if not seg:
            continue
        if seg.startswith(("clean", "nearest other", "object itself present")):
            continue                      # all three are clean results
        if seg.startswith("CONFLICT"):
            out.append(f"skybot conflict: {seg}")
        elif "lost-object claimant" in seg:
            continue                      # adjudicated via the ambiguity column, below
        elif seg.startswith("UNAVAILABLE") or seg == "not run":
            out.append(f"skybot check did not run: {seg}")
        else:
            out.append(f"skybot cell not understood, refusing: {seg}")
    return out


#: ``tracklet-used=4/4`` -- how a single-tracklet row spells "fo used every observation".
TRACKLET_USED_RE = re.compile(r"tracklet-used=(\d+)/(\d+)")


def gate_reasons(cell: str) -> list[str]:
    """The three conditions a row must meet, across two different spellings.

    ``strict`` and ``published`` are written the same way everywhere. The third -- **did
    Find_Orb actually use the tracklet** -- is not, and it is the one that matters most:
    M11 §4.2 measured that the entire discriminating power of the chain sits in this gate
    and none in the RMS ceiling (162/300 real vs **0/300** decoy). It appears as
    ``all-members-used=Y`` on a combined multi-tracklet fit and as ``tracklet-used=4/4``
    on a single-tracklet one. Requiring only the first spelling silently refuses every
    tier-B and tier-C row in the queue -- 645 of 679 -- which is safe but useless.
    """
    out: list[str] = []
    for gate in ("strict=Y", "published=Y"):
        if gate not in cell:
            out.append(f"gate not passed: {gate.split('=')[0]}")
    if "all-members-used=Y" in cell:
        return out
    m = TRACKLET_USED_RE.search(cell)
    if m is None:
        out.append(f"no 'fo used the tracklet' gate found in: {cell!r}")
    elif m.group(1) != m.group(2):
        out.append(f"fo used only {m.group(1)} of {m.group(2)} observations")
    return out


#: The MPC's own ITF-to-DES rejection threshold, in days.
MIN_ARC_DAYS_NON_NEO = 0.75


def mpc_criteria_reasons(n_tracklets: int, arc_days: float | None,
                         is_neo: bool) -> list[str]:
    """The MPC's published acceptance criteria for the kind of link we submit.

    ``https://docs.minorplanetcenter.net/mpc-ops-docs/identifications/acceptance-criteria/``
    splits the rules by submission type. Ours are **ITF-to-DES** -- orphan ITF tracklets
    attached to an object that
    already has a designation -- so the harsh ITF-to-ITF rules (3 distinct nights, 3-day
    arc, 15-day ceiling) do **not** apply to us, and neither does the DES-to-DES q > 5.5
    rule. Exactly one criterion does, and it is decisive:

        "Attempting to extend a non-NEO orbit across apparitions using a single tracklet
         with arc length under 0.75 days"  -- rejected.
         "(this criteria does not apply to NEOs)"

    Every arc extension in this queue is across apparitions by construction: the shortest
    is hundreds of days. So the rule reduces to *single tracklet, short arc, not an NEO*,
    and measured against the real queue it rejects **650 of 651** single-tracklet rows --
    the entire B and C tiers. Not one of the 662 objects resolved is an NEO (minimum
    perihelion 1.521 au), so nothing is exempt.

    A submission that would be auto-rejected is not a neutral cost. The MPC tracks
    submitter reputation and bad batches cause *future* reports to be disregarded
    (``DISCOVERY/itf-linker.md`` §Guardrails), so refusing here is the whole point.
    """
    if is_neo:
        return []                       # explicitly exempt, whatever the arc
    if n_tracklets > 1:
        return []                       # the rule is scoped to a *single* tracklet
    if arc_days is None:
        return ["cannot measure the submitted arc, so the 0.75 d rule cannot be cleared"]
    if arc_days < MIN_ARC_DAYS_NON_NEO:
        return [(f"MPC criteria: single tracklet spanning {arc_days * 24:.1f} h "
                 f"(< {MIN_ARC_DAYS_NON_NEO} d) extending a non-NEO across apparitions "
                 "-- auto-rejected")]
    return []


def check_row(row: dict[str, str], nights: dict[tuple, dict],
              neo: dict[str, dict] | None = None) -> tuple[list, list[str]]:
    """Return (trksub triples, refusal reasons). A row with any reason must not be sent."""
    reasons: list[str] = []

    if not row["itf_status"].startswith("STILL_LIVE"):
        reasons.append(f"queue marks it {row['itf_status']}")

    reasons += skybot_reasons(row["skybot"])

    # A lost-object claimant is flagged by skybot and *ruled on* here: across the whole
    # queue the two sets are identical, 130 and 130. RESOLVED_TO_CANDIDATE means the
    # adjudication went our way (M9/M10/M11); STILL_AMBIGUOUS means a rival orbit fits too,
    # and that is a claim nobody should be making by machine.
    amb = row["ambiguity"]
    if amb and amb != "none" and not amb.startswith("RESOLVED_"):
        reasons.append(f"unresolved ambiguity: {amb}")

    if row["pointed_screen"] and row["pointed_screen"] != "clean":
        reasons.append(f"pointed-field screen: {row['pointed_screen']}")

    reasons += gate_reasons(row["gates"])

    packed = packed_provisional(row["object"])
    if not packed:
        reasons.append(f"designation will not pack: {row['object']!r}")

    triples = []
    los: list[float] = []
    his: list[float] = []
    for trk in parse_tracklets(row["tracklets"]):
        key = (trk["trksub"], trk["obscode"], trk["night"])
        got = nights.get(key)
        if got is None:
            # Gone from this ITF snapshot. Disappearance is not proof of identification
            # or of a destination, so the safe response is to hold it for human review.
            reasons.append(f"{trk['trksub']}@{trk['obscode']} no longer in the current "
                           "ITF (reason and destination not established)")
            continue
        if got["n_obs"] < MIN_OBS_PER_NIGHT:
            reasons.append(
                f"{trk['trksub']}@{trk['obscode']} has {got['n_obs']} observation(s) on "
                f"night {trk['night']}; the MPC auto-rejects the WHOLE batch below "
                f"{MIN_OBS_PER_NIGHT}"
            )
            continue
        los.append(got["mjd"])
        his.append(got.get("mjd_hi", got["mjd"]))
        triples.append([trk["trksub"], obs_date(got["mjd"]), trk["obscode"]])

    if not triples and not reasons:
        reasons.append("no usable tracklets")

    # The MPC's own acceptance criteria, applied last: a row can be perfect by every
    # internal gate and still be auto-rejected by the pipeline it is sent to.
    entry = (neo or {}).get(row["object"])
    arc = (max(his) - min(los)) if los else None
    reasons += mpc_criteria_reasons(
        n_tracklets=len(triples) or len(parse_tracklets(row["tracklets"])),
        arc_days=arc,
        is_neo=bool(entry and entry.get("is_neo")),
    )
    return triples, reasons


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--itf", type=Path,
                    default=ROOT / "data" / "parquet" / "itf_observations.parquet")
    ap.add_argument("--tier", action="append", default=None,
                    help="tier to include; repeatable. Default: A only.")
    ap.add_argument("--name", required=True, help="submitter name for the JSON header")
    ap.add_argument("--email", required=True, help="submitter email for the JSON header")
    ap.add_argument("--neo-status", type=Path, default=None,
                    help="sidecar from m13_neo_status.py. Objects absent from it are "
                         "treated as NON-NEO, the restrictive branch.")
    ap.add_argument("--comment", default=None)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    tiers = set(args.tier or ["A"])

    prov = args.itf.with_suffix(".parquet").parent.parent / "raw" / "itf.provenance.json"
    if prov.exists():
        p = json.loads(prov.read_text(encoding="utf-8"))
        print(f"ITF pull: {p.get('last_modified')}  ({p.get('size_bytes'):,} bytes)",
              flush=True)

    rows = list(csv.DictReader(args.queue.open(encoding="utf-8-sig")))
    picked = [r for r in rows if r["tier"] in tiers]
    print(f"queue {args.queue.name}: {len(rows)} rows, {len(picked)} in tier(s) "
          f"{sorted(tiers)}", flush=True)
    if not picked:
        raise SystemExit("no rows in the requested tier(s)")

    print("indexing the current ITF by (trksub, obscode, night)...", flush=True)
    idx = load_itf_nights(args.itf)
    nights = {(r["desig"], r["obscode"], r["night"]): r for r in idx.iter_rows(named=True)}
    print(f"  {len(nights):,} object-nights", flush=True)

    neo = {}
    if args.neo_status and args.neo_status.exists():
        neo = json.loads(args.neo_status.read_text(encoding="utf-8"))["objects"]
        print(f"NEO sidecar: {len(neo)} objects, "
              f"{sum(1 for v in neo.values() if v['is_neo'])} NEOs", flush=True)
    else:
        print("::warning:: no NEO sidecar; every object treated as non-NEO (strict)",
              flush=True)

    links: dict[str, Any] = {}
    dropped: list[dict[str, Any]] = []
    for row in picked:
        triples, reasons = check_row(row, nights, neo)
        if reasons:
            dropped.append({"rank": row["rank"], "object": row["object"],
                            "tier": row["tier"], "reasons": reasons})
            print(f"  DROP rank {row['rank']:>4} {row['object']:14} "
                  f"{reasons[0]}", flush=True)
            for extra in reasons[1:]:
                print(f"       {'':>4} {'':14} {extra}", flush=True)
            continue
        links[f"link_{len(links)}"] = {
            "designations": [packed_provisional(row["object"])],
            "trksubs": triples,
        }

    print(f"\nkept {len(links)}  dropped {len(dropped)}", flush=True)
    if dropped:
        why = Counter(r["reasons"][0].split(":")[0].split("(")[0].strip()
                      for r in dropped)
        for reason, n in why.most_common():
            print(f"  {n:>4}  {reason}", flush=True)

    report = args.out.with_name(args.out.stem + "-dropped.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "queue": str(args.queue), "tiers": sorted(tiers),
        "kept": len(links), "dropped": dropped,
    }, indent=2), encoding="utf-8")
    print(f"drop report -> {report}", flush=True)

    if not links:
        raise SystemExit("every row was dropped; no payload written")

    payload = {
        "header": {"name": args.name, "email": args.email,
                   **({"comment": args.comment} if args.comment else {})},
        "links": links,
    }
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    n_trk = sum(len(v["trksubs"]) for v in links.values())
    print(f"\npayload -> {args.out}", flush=True)
    print(f"  {len(links)} identifications, {n_trk} tracklets", flush=True)
    # The 0.75 d rule is scoped to a *single* tracklet, so a same-night PAIR is exempt on
    # the literal wording while still adding under a day of arc. That is a judgment the
    # human making the submission should get to make, so it is reported, not hidden.
    same_night = sum(1 for v in links.values()
                     if len(v["trksubs"]) > 1 and len({t[1] for t in v["trksubs"]}) == 1)
    if same_night:
        print(f"  NOTE: {same_night} of {len(links)} are multi-tracklet but fall on ONE "
              "date.", flush=True)
        print("        Exempt from the 0.75 d rule only because it says 'single "
              "tracklet'; they still add < 1 day of arc.", flush=True)
    print("\nNOT SENT. Upload it yourself at", flush=True)
    print("  https://minorplanetcenter.net/mpcops/submissions/identifications/",
          flush=True)


if __name__ == "__main__":
    main()
