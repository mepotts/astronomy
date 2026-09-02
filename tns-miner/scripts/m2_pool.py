"""M2 fix (b): a real outburst enumerator, plus the full-chain pool builder.

THE DEFECT M1 IDENTIFIED
    ALeRCE's `firstmjd` window enumerates only objects whose FIRST EVER ZTF
    detection lies in the window.  A catalogued CV going into a new outburst --
    which M1-02 measures as most of DCAP's actual business -- has a first
    detection years ago and is structurally invisible to it.  M1-05 patched
    around it with Fink `latests?class=Unknown&n=1000`, which returns only the
    newest 1000 alerts of a single class: a few hours of one night.

THE FIX (pre-registered, M2-01 B2)
    Two arms whose union covers a night:

    E1  new sources      -- ALeRCE /objects/ firstmjd in window, ndet >= 2 (M1's).
    E2  known sources erupting -- Fink /api/v1/latests DOES accept startdate /
        stopdate (verified 2026-08-24; undocumented in M1).  For every Fink class
        that the frozen Layer 3 does NOT veto, pull the window; when a call
        returns exactly n the cap is binding, so bisect the window until every
        slice is under cap.  An alert enters the pool if

            isdiffpos = t  and  drb >= 0.90  and
            ( magnr - magpsf >= AMP_ENUM      # a known source, now brighter
              or magnr is null / >= 99 )      # nothing in the reference at all

        The amplitude test is per-band by construction: one alert is one filter.

    Which classes are enumerated is DERIVED from the filter's own veto list, not
    chosen -- no new free parameter, and if the veto changes the enumerator
    follows.  AMP_ENUM == AMP_MIN so the enumerator never cuts deeper than the
    filter.

usage:  python m2_pool.py <mjd_start> <mjd_end> <tag>
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as M1  # noqa: E402
import m2_filter as F2  # noqa: E402
from cache_contract import (  # noqa: E402
    atomic_write,
    canonical_digest,
    load_cache_contract,
    sidecar_path,
    validated_tag,
    write_cache,
)
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    cache_provenance,
    fetch_histories_batch,
)
from tnscommon import DATA, OUT, session  # noqa: E402

ALERCE = "https://api.alerce.online/ztf/v1/objects/"
FINK_LATESTS = "https://api.ztf.fink-portal.org/api/v1/latests"
FINK_CLASSES = "https://api.ztf.fink-portal.org/api/v1/classes"

AMP_ENUM = F2.AMP_MIN          # never deeper than the filter
EPISODE_FLOOR_DAYS = 60.0      # see the note in main(): a candidate pass
                               # must be evaluated on the CURRENT episode
POOL = DATA / "pool"
POOL.mkdir(parents=True, exist_ok=True)
ALERCE_PAGE_SIZE = 1000
ALERCE_MAX_PAGES = 200
FINK_CAP = 1000
FINK_MAX_BISECT_DEPTH = 14
FINK_MAX_SLICE_CALLS = 4096

E2_COLS = ("i:objectId,i:jd,i:magpsf,i:magnr,i:fid,i:ra,i:dec,i:drb,i:rb,"
           "i:isdiffpos,i:ndethist,i:jdstarthist,d:cdsxmatch")

# classes that are never worth enumerating whatever the veto list says:
# solar-system (M1 Layer 1 rejects them by construction) and the aggregate
# counters Fink publishes in /statistics but does not serve as classes.
NEVER_ENUMERATE = {"Solar System MPC", "Solar System candidate", "Tracklet",
                   "simbad_gal", "simbad_tot"}
FINK_TAXONOMY_CONTRACT_VERSION = 1
FINK_TAXONOMY_MIN_NON_TNS_CLASSES = 250
# Deliberate cross-family sentinels from the Fink class catalogue observed when
# E2 was designed.  Additions are enumerated automatically.  Removing/renaming
# one of these requires a reviewed version bump rather than silently proving a
# partial HTTP-200 catalogue as complete.
FINK_TAXONOMY_REQUIRED_FAMILIES = {
    "simbad_target": frozenset({"CataclyV*"}),
    "simbad_host_veto": frozenset({"Galaxy"}),
    "fink_science": frozenset({"Early SN Ia candidate"}),
    "solar_system": frozenset({"Solar System candidate"}),
}


def _e1_contract(t0: float, t1: float) -> dict:
    return {
        "source_url": ALERCE,
        "mjd_start": float(t0),
        "mjd_end": float(t1),
        "ndet_min": 2,
        "page_size": ALERCE_PAGE_SIZE,
        "pagination": "until_short_page",
    }


def _e2_contract(t0: float, t1: float) -> dict:
    policy = {
        "columns": E2_COLS,
        "never_enumerate": sorted(NEVER_ENUMERATE),
        "hard_veto": sorted(F2.SIMBAD_HARD_VETO),
        "amp_min": float(AMP_ENUM),
        "drb_min": float(M1.DRB_MIN),
        "rb_min": float(M1.RB_MIN),
        "cap": FINK_CAP,
        "max_bisect_depth": FINK_MAX_BISECT_DEPTH,
        "max_slice_calls": FINK_MAX_SLICE_CALLS,
        "taxonomy_contract_version": FINK_TAXONOMY_CONTRACT_VERSION,
        "taxonomy_min_non_tns_classes": FINK_TAXONOMY_MIN_NON_TNS_CLASSES,
        "taxonomy_required_families": {
            family: sorted(classes)
            for family, classes in FINK_TAXONOMY_REQUIRED_FAMILIES.items()
        },
    }
    return {
        "source_url": FINK_LATESTS,
        "classes_url": FINK_CLASSES,
        "mjd_start": float(t0),
        "mjd_end": float(t1),
        "enumerator_policy_sha256": canonical_digest(policy),
        "cap_completion_rule": "bisect_until_strictly_under_cap_or_abort",
    }


def _alerce_total(value) -> int:
    if isinstance(value, bool):
        raise RuntimeError("ALeRCE total is not a non-negative integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("ALeRCE total is not a non-negative integer") from exc
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise RuntimeError("ALeRCE total is not a non-negative integer")
    return int(number)


def _validate_latest_payload(
    payload,
    *,
    cls: str,
    t0: float,
    t1: float,
) -> list[dict]:
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise RuntimeError("response is not a JSON list of alert objects")
    jd_min, jd_max = t0 + 2400000.5, t1 + 2400000.5
    required = {
        "i:objectId", "i:jd", "i:magpsf", "i:magnr", "i:fid", "i:ra", "i:dec",
        "i:isdiffpos",
    }
    for index, row in enumerate(payload):
        missing = required - set(row)
        if missing:
            raise RuntimeError(
                f"{cls!r} row {index} lacks fields {sorted(missing)}"
            )
        oid = row["i:objectId"]
        if not isinstance(oid, str) or not oid.strip():
            raise RuntimeError(f"{cls!r} row {index} has invalid object ID")
        numeric: dict[str, float] = {}
        for field in ("i:jd", "i:magpsf", "i:fid", "i:ra", "i:dec"):
            if isinstance(row[field], bool):
                raise RuntimeError(f"{cls!r} row {index} has invalid {field}")
            try:
                numeric[field] = float(row[field])
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"{cls!r} row {index} has invalid {field}") from exc
            if not math.isfinite(numeric[field]):
                raise RuntimeError(f"{cls!r} row {index} has non-finite {field}")
        if not jd_min - 1e-8 <= numeric["i:jd"] <= jd_max + 1e-8:
            raise RuntimeError(
                f"{cls!r} row {index} JD {numeric['i:jd']} lies outside "
                f"requested [{jd_min}, {jd_max}]"
            )
        if not numeric["i:fid"].is_integer() or int(numeric["i:fid"]) not in (1, 2, 3):
            raise RuntimeError(f"{cls!r} row {index} has invalid filter ID")
        if not 0 <= numeric["i:ra"] <= 360 or not -90 <= numeric["i:dec"] <= 90:
            raise RuntimeError(f"{cls!r} row {index} has invalid coordinates")
        magnr = row["i:magnr"]
        if magnr is not None and str(magnr).strip().lower() not in {"", "nan", "null"}:
            try:
                if not math.isfinite(float(magnr)):
                    raise ValueError
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"{cls!r} row {index} has invalid i:magnr") from exc
        scores = []
        for field in ("i:drb", "i:rb"):
            try:
                score = float(row.get(field))
            except (TypeError, ValueError):
                continue
            if math.isfinite(score):
                scores.append(score)
        if not scores:
            raise RuntimeError(f"{cls!r} row {index} has no finite drb/rb")
        if str(row["i:isdiffpos"]).strip().lower() not in {
            "t", "f", "true", "false", "1", "0",
        }:
            raise RuntimeError(f"{cls!r} row {index} has invalid subtraction sign")
    return payload


def mjd_to_ut(mjd: float) -> str:
    return pd.Timestamp((mjd + 2400000.5 - 2440587.5) * 86400,
                        unit="s", tz="UTC").strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# which classes does the frozen filter NOT veto?
# --------------------------------------------------------------------------- #
def enumerable_classes(s) -> list[str]:
    r = s.get(FINK_CLASSES, timeout=120)
    r.raise_for_status()
    try:
        raw = r.json()
    except ValueError as exc:
        raise RuntimeError("Fink class taxonomy returned malformed JSON") from exc
    if not isinstance(raw, dict) or not raw:
        raise RuntimeError("Fink class taxonomy is empty or not an object")
    names: list[str] = []
    for group, lst in raw.items():
        if not isinstance(group, str) or not group.strip():
            raise RuntimeError("Fink class taxonomy has an invalid group name")
        if not isinstance(lst, list) or not lst:
            raise RuntimeError(
                f"Fink class taxonomy group {group!r} is not a nonempty list"
            )
        if any(not isinstance(item, str) or not item.strip() for item in lst):
            raise RuntimeError(
                f"Fink class taxonomy group {group!r} has an invalid class name"
            )
        if "TNS" in group:            # already in TNS -> Layer 6 rejects anyway
            continue
        for c in lst:
            names.append(c.replace("(SIMBAD) ", "").replace("(CTA) ", ""))
    available = set(names)
    missing_families = {
        family: sorted(required - available)
        for family, required in FINK_TAXONOMY_REQUIRED_FAMILIES.items()
        if not required.issubset(available)
    }
    if (
        len(raw) < 2
        or len(available) < FINK_TAXONOMY_MIN_NON_TNS_CLASSES
        or missing_families
    ):
        raise RuntimeError(
            "Fink class taxonomy does not satisfy pinned baseline contract "
            f"v{FINK_TAXONOMY_CONTRACT_VERSION}: "
            f"missing={missing_families}, groups={len(raw)}, "
            f"non_tns_classes={len(available)} "
            f"(minimum {FINK_TAXONOMY_MIN_NON_TNS_CLASSES}). Review the live "
            "taxonomy and bump the contract explicitly before E2 can run"
        )
    names.append("Unknown")
    keep = []
    for c in sorted(set(names)):
        if c in NEVER_ENUMERATE:
            continue
        if c in F2.SIMBAD_HARD_VETO:   # Layer 3 would reject every object in it
            continue
        keep.append(c)
    return keep


# --------------------------------------------------------------------------- #
# arm E2 -- known sources erupting
# --------------------------------------------------------------------------- #
def _latests(s, cls: str, t0: float, t1: float, n: int = 1000) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            r = s.get(FINK_LATESTS,
                      params={"class": cls, "n": n, "startdate": mjd_to_ut(t0),
                              "stopdate": mjd_to_ut(t1), "columns": E2_COLS},
                      timeout=300)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            j = _validate_latest_payload(r.json(), cls=cls, t0=t0, t1=t1)
            if not j:
                return pd.DataFrame()
            return pd.DataFrame(j)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 < 3:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(
        f"Fink latests failed for class={cls!r}, MJD {t0}-{t1}; "
        "the E2 arm is incomplete and will not be cached"
    ) from last_error


def _latests_complete(
    s,
    cls: str,
    t0: float,
    t1: float,
    depth: int = 0,
    _state: dict[str, int] | None = None,
) -> pd.DataFrame:
    """One call; if the 1000-row cap binds, bisect the window until it does not."""
    state = _state if _state is not None else {"calls": 0}
    state["calls"] += 1
    if state["calls"] > FINK_MAX_SLICE_CALLS:
        raise RuntimeError(
            f"Fink latests exceeded {FINK_MAX_SLICE_CALLS} slices for class={cls!r}; "
            "completeness unproved"
        )
    d = _latests(s, cls, t0, t1)
    if len(d) < FINK_CAP:
        return d
    if len(d) > FINK_CAP:
        raise RuntimeError(f"Fink returned {len(d)} rows above its {FINK_CAP}-row cap")
    if depth >= FINK_MAX_BISECT_DEPTH:
        raise RuntimeError(
            f"Fink latests remained cap-bound after {FINK_MAX_BISECT_DEPTH} "
            f"bisections for class={cls!r}, MJD {t0}-{t1}; completeness unproved"
        )
    mid = (t0 + t1) / 2
    if not t0 < mid < t1:
        raise RuntimeError(f"cannot further bisect cap-bound MJD interval {t0}-{t1}")
    return pd.concat(
        [
            _latests_complete(s, cls, t0, mid, depth + 1, state),
            _latests_complete(s, cls, mid, t1, depth + 1, state),
        ],
        ignore_index=True,
    )


def arm_e2_outbursts(t0: float, t1: float, tag: str) -> pd.DataFrame:
    tag = validated_tag(tag)
    cache = POOL / f"e2_{tag}.csv"
    cached = load_cache_contract(
        cache,
        kind="m2_fink_e2_pool",
        expected_contract=_e2_contract(t0, t1),
    )
    if cached is not None:
        d = pd.read_csv(cache)
        if len(d) != int(cached.get("row_count", -1)):
            raise RuntimeError(f"E2 cache row-count mismatch: {cache}")
        print(f"E2 outburst arm: cached {len(d)} objects")
        return d
    s = session()
    classes = enumerable_classes(s)
    print(f"E2: enumerating {len(classes)} non-vetoed Fink classes over "
          f"MJD {t0}-{t1}")
    frames, n_raw = [], 0
    for i, c in enumerate(classes, 1):
        d = _latests_complete(s, c, t0, t1)
        if not len(d):
            continue
        n_raw += len(d)
        frames.append(d)
        if len(d) > 200:
            print(f"    [{i}/{len(classes)}] {c}: {len(d)} alerts", flush=True)
    if not frames:
        out = pd.DataFrame(columns=["oid", "meanra", "meandec", "arm"])
    else:
        a = pd.concat(frames, ignore_index=True)
        print(f"E2: {n_raw} alerts across the window")

        for column in ("i:magpsf", "i:magnr", "i:drb", "i:rb"):
            a[column] = pd.to_numeric(a.get(column), errors="coerce")
        pos = (
            a["i:isdiffpos"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin({"t", "1", "true"})
        )
        conf = (a["i:drb"] >= M1.DRB_MIN) | (
            a["i:drb"].isna() & (a["i:rb"] >= M1.RB_MIN)
        )
        no_ref = (
            a["i:magnr"].isna() | (a["i:magnr"] >= 99) | (a["i:magnr"] <= 0)
        )
        amp = a["i:magnr"] - a["i:magpsf"]
        sel = pos & conf & (no_ref | (amp >= AMP_ENUM))
        a = a[sel]
        print(
            f"E2: {int(sel.sum())} alerts pass hygiene + amp>={AMP_ENUM} "
            "(or no reference source)"
        )
        out = (
            a.rename(
                columns={"i:objectId": "oid", "i:ra": "meanra", "i:dec": "meandec"}
            )
            .drop_duplicates(subset=["oid"])[["oid", "meanra", "meandec"]]
        )
        out["arm"] = "E2_outburst"
    payload = out.to_csv(index=False, lineterminator="\n").encode("utf-8")
    write_cache(
        cache,
        payload,
        kind="m2_fink_e2_pool",
        contract=_e2_contract(t0, t1),
        row_count=len(out),
        metadata_extra={
            "enumerated_classes": classes,
            "enumerated_classes_sha256": canonical_digest(classes),
            "taxonomy_contract_version": FINK_TAXONOMY_CONTRACT_VERSION,
            "n_raw_alert_rows": n_raw,
        },
    )
    print(f"E2 outburst arm: {len(out)} unique objects")
    return out


# --------------------------------------------------------------------------- #
# arm E1 -- new sources (M1's enumerator, unchanged)
# --------------------------------------------------------------------------- #
def arm_e1_new(t0: float, t1: float, tag: str) -> pd.DataFrame:
    tag = validated_tag(tag)
    cache = POOL / f"e1_{tag}.csv"
    cached = load_cache_contract(
        cache,
        kind="m2_alerce_e1_pool",
        expected_contract=_e1_contract(t0, t1),
    )
    if cached is not None:
        d = pd.read_csv(cache)
        if len(d) != int(cached.get("row_count", -1)):
            raise RuntimeError(f"E1 cache row-count mismatch: {cache}")
        print(f"E1 new-source arm: cached {len(d)} objects")
        return d
    s = session()
    rows, page = [], 1
    reported_total: int | None = None
    page_signatures: set[tuple[str, ...]] = set()
    while True:
        r = s.get(ALERCE, params={"firstmjd": [t0, t1], "ndet": 2,
                                  "page_size": ALERCE_PAGE_SIZE, "page": page,
                                  "count": "true" if page == 1 else "false"},
                  timeout=300)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError as exc:
            raise RuntimeError(f"ALeRCE page {page} returned malformed JSON") from exc
        if not isinstance(j, dict) or not isinstance(j.get("items"), list):
            raise RuntimeError(f"ALeRCE page {page} returned an invalid object schema")
        items = j["items"]
        for item in items:
            if not isinstance(item, dict) or not {
                "oid", "meanra", "meandec"
            }.issubset(item):
                raise RuntimeError(f"ALeRCE page {page} has an invalid row")
        rows.extend(items)
        if page == 1:
            reported_total = _alerce_total(j.get("total"))
            print(f"  ALeRCE reports total={reported_total}")
        signature = tuple(str(item["oid"]) for item in items)
        if items and signature in page_signatures:
            raise RuntimeError(f"ALeRCE repeated page payload at page {page}")
        page_signatures.add(signature)
        # TRAP: with count=false ALeRCE does not populate has_next reliably, so a
        # loop that trusts it stops after one page and silently truncates the arm
        # at page_size.  Page until a page comes back short instead.
        if len(items) < ALERCE_PAGE_SIZE:
            break
        if page >= ALERCE_MAX_PAGES:
            raise RuntimeError(
                f"ALeRCE pagination remained cap-bound at {ALERCE_MAX_PAGES} pages"
            )
        page += 1
        time.sleep(0.3)
    d = pd.DataFrame(rows)
    if not len(d):
        d = pd.DataFrame(columns=["oid", "meanra", "meandec", "arm"])
    else:
        d = d.drop_duplicates(subset=["oid"])[["oid", "meanra", "meandec"]]
        d["arm"] = "E1_new"
    if reported_total is None or len(d) != reported_total:
        raise RuntimeError(
            f"ALeRCE completeness mismatch: reported {reported_total}, "
            f"retrieved {len(d)} unique OIDs; E1 not cached"
        )
    payload = d.to_csv(index=False, lineterminator="\n").encode("utf-8")
    write_cache(
        cache,
        payload,
        kind="m2_alerce_e1_pool",
        contract=_e1_contract(t0, t1),
        row_count=len(d),
    )
    print(f"E1 new-source arm: {len(d)} objects")
    return d


# --------------------------------------------------------------------------- #
def fetch_batch(
    s,
    oids: list[str],
    chunk: int = 60,
    *,
    refresh: bool = False,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float | None = None,
) -> dict:
    histories = fetch_histories_batch(
        s,
        oids,
        chunk=chunk,
        refresh=refresh,
        max_age_seconds=max_age_seconds,
        required_coverage_jd=required_coverage_jd,
    )
    return {oid: pd.DataFrame(records) for oid, records in histories.items()}


def main() -> None:
    t0, t1, tag = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    tag = validated_tag(tag)
    jd_floor = t0 + 2400000.5 - EPISODE_FLOOR_DAYS
    jd_ceiling = t1 + 2400000.5
    e1 = arm_e1_new(t0, t1, tag)
    e2 = arm_e2_outbursts(t0, t1, tag)
    pool = pd.concat([e1, e2], ignore_index=True)
    n1, n2 = len(e1), len(e2)
    pool = pool.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    overlap = n1 + n2 - len(pool)
    print(f"pool {tag}: E1 {n1} + E2 {n2} - {overlap} overlap = {len(pool)} objects")

    s = session()
    hist = fetch_batch(
        s,
        pool["oid"].tolist(),
        max_age_seconds=HISTORY_MAX_AGE_SECONDS,
        required_coverage_jd=jd_ceiling,
    )

    # BUG FOUND AT M2-04, inherited from M1: evaluating a candidate pass with no
    # jd_floor makes the trigger the object's ALL-TIME first passing epoch, which
    # for a recurrent CV is an eruption years ago.  Every epoch-dependent column --
    # mag_at_pass, first_pass_jd, per-band amplitude, peak-to-peak, and the
    # flat-residual veto -- then describes that old outburst instead of tonight's.
    # On the first M2 run 41 of 44 candidates had a trigger epoch more than a year
    # before the enumeration window.  Floor the visible history at the episode
    # convention M1-04 already used (60 d) so the filter fires on the CURRENT
    # episode.  This moves no threshold.
    rows = []
    for _, r in pool.iterrows():
        a = hist.get(r["oid"], pd.DataFrame())
        v = F2.evaluate(
            a,
            F2.M2_FULL,
            jd_cutoff=jd_ceiling,
            jd_floor=jd_floor,
        )
        v_m1 = M1.evaluate(
            a,
            jd_cutoff=jd_ceiling,
            jd_floor=jd_floor,
        )
        rows.append({
            "oid": r["oid"], "arm": r["arm"],
            "pool_ra": r.get("meanra"), "pool_dec": r.get("meandec"),
            "history_jd_floor": jd_floor,
            "history_jd_ceiling": jd_ceiling,
            "m1_passed": bool(v_m1.get("passed")),
            **{k: v.get(k) for k in
               ("passed", "channel", "reason", "first_pass_jd", "n_clean",
                "n_alerts", "mag_at_pass", "band_at_pass", "ra", "dec", "drb",
                "sgscore1", "distpsnr1", "distnr", "magnr", "ndethist", "gal_b",
                "simbad", "amp", "ptp_band", "neg_frac", "n_neg", "n_conf",
                "hist_span_days", "n_alerts_60d_maxband")},
            "flags": json.dumps(v.get("flags") or {}),
            "hygiene_ok": v.get("n_clean", 0) >= M1.N_DET_MIN,
        })
    res = pd.DataFrame(rows)
    if not len(res):
        res = pd.DataFrame(columns=[
            "oid", "arm", "pool_ra", "pool_dec", "history_jd_floor",
            "history_jd_ceiling", "m1_passed", "passed", "channel", "reason",
            "first_pass_jd", "n_clean", "n_alerts", "mag_at_pass", "band_at_pass",
            "ra", "dec", "drb", "sgscore1", "distpsnr1", "distnr", "magnr",
            "ndethist", "gal_b", "simbad", "amp", "ptp_band", "neg_frac",
            "n_neg", "n_conf", "hist_span_days", "n_alerts_60d_maxband", "flags",
            "hygiene_ok",
        ])
    enumerator_meta = {
        arm: json.loads(
            sidecar_path(POOL / f"{arm}_{tag}.csv").read_text(encoding="utf-8")
        )
        for arm in ("e1", "e2")
    }
    filtered_contract = {
        "tag": tag,
        "mjd_window": [t0, t1],
        "history_jd_floor": jd_floor,
        "history_jd_ceiling": jd_ceiling,
        "source_e1_sha256": enumerator_meta["e1"]["payload_sha256"],
        "source_e2_sha256": enumerator_meta["e2"]["payload_sha256"],
        "source_row_counts": {"e1": n1, "e2": n2, "union": len(pool)},
    }
    filtered_meta = write_cache(
        POOL / f"m2_filtered_{tag}.csv",
        res.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        kind="m2_filtered_pool",
        contract=filtered_contract,
        row_count=len(res),
    )
    summary = {
        "tag": tag, "mjd_window": [t0, t1],
        "episode_floor_days": EPISODE_FLOOR_DAYS,
        "history_jd_floor": jd_floor,
        "history_jd_ceiling": jd_ceiling,
        "history_as_of_mjd": t1,
        "history_cache_policy": {
            "refresh": False,
            "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
            "required_coverage_jd": jd_ceiling,
        },
        "history_cache_provenance": cache_provenance(pool["oid"].tolist()),
        "enumerator_cache_provenance": {
            arm: enumerator_meta[arm] for arm in ("e1", "e2")
        },
        "filtered_output_provenance": filtered_meta,
        "n_E1_new": n1, "n_E2_outburst": n2, "n_overlap": overlap,
        "n_pool": int(len(pool)),
        "n_hygiene_ok": int(res["hygiene_ok"].sum()),
        "n_pass_M2": int(res["passed"].sum()),
        "n_pass_M1_baseline": int(res["m1_passed"].sum()),
        "pass_by_arm": res.loc[res["passed"], "arm"].value_counts().to_dict(),
        "channels": res.loc[res["passed"], "channel"].value_counts().to_dict(),
        "top_reject_reasons": (res.loc[~res["passed"], "reason"]
                               .astype(str).str.replace(r"[\d.]+", "N", regex=True)
                               .value_counts().head(12).to_dict()),
    }
    atomic_write(
        OUT / f"m2_pool_{tag}.json",
        (json.dumps(summary, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
