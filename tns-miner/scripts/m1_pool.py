"""Enumerate a pool of ZTF objects over a window, enrich from Fink, run the filter.

Two uses, same code:
  * the GAP measurement -- a window far enough back (>=30 d) that every TNS report
    for it has already landed, so "passes the filter but is not in TNS" is a real
    count and not a race;
  * the CANDIDATE pass -- the most recent nights.

Enumeration is ALeRCE (`firstmjd` range, tokenless, 1000/page); enrichment is Fink
(full alert packet + VSX/GCVS/SIMBAD/TNS/MPC cross-matches, tokenless).

usage:  python m1_pool.py <mjd_start> <mjd_end> <tag>
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as F  # noqa: E402
from cache_contract import (  # noqa: E402
    atomic_write,
    load_cache_contract,
    sidecar_path,
    validated_tag,
    write_cache,
)
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    cache_is_usable,
    cache_provenance,
    fetch_one,
)
from tnscommon import DATA, OUT, session  # noqa: E402

ALERCE = "https://api.alerce.online/ztf/v1/objects/"
POOL = DATA / "pool"
POOL.mkdir(parents=True, exist_ok=True)
ALERCE_PAGE_SIZE = 1000
ALERCE_MAX_PAGES = 200


def _pool_contract(mjd0: float, mjd1: float) -> dict:
    return {
        "source_url": ALERCE,
        "mjd_start": float(mjd0),
        "mjd_end": float(mjd1),
        "ndet_min": 2,
        "page_size": ALERCE_PAGE_SIZE,
        "pagination": "until_short_page",
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


def enumerate_new_objects(mjd0: float, mjd1: float, tag: str) -> pd.DataFrame:
    """Every ZTF object whose FIRST-EVER detection falls in [mjd0, mjd1], ndet>=2."""
    tag = validated_tag(tag)
    cache = POOL / f"pool_{tag}.csv"
    cached = load_cache_contract(
        cache,
        kind="m1_alerce_pool",
        expected_contract=_pool_contract(mjd0, mjd1),
    )
    if cached is not None:
        df = pd.read_csv(cache)
        if len(df) != int(cached.get("row_count", -1)):
            raise RuntimeError(f"pool cache row-count mismatch: {cache}")
        print(f"pool {tag}: cached {len(df)}")
        return df
    s = session()
    rows, page = [], 1
    reported_total: int | None = None
    page_signatures: set[tuple[str, ...]] = set()
    while True:
        r = s.get(ALERCE, params={"firstmjd": [mjd0, mjd1], "ndet": 2,
                                  "page_size": ALERCE_PAGE_SIZE, "page": page,
                                  "count": "true" if page == 1 else "false"},
                  timeout=180)
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
        if page == 1:
            reported_total = _alerce_total(j.get("total"))
            print(f"pool {tag}: ALeRCE reports total={reported_total}")
        signature = tuple(str(item["oid"]) for item in items)
        if items and signature in page_signatures:
            raise RuntimeError(f"ALeRCE repeated page payload at page {page}")
        page_signatures.add(signature)
        rows.extend(items)
        print(f"  page {page}: {len(items)} (running {len(rows)})", flush=True)
        # has_next is not reliable when count=false.  A short page proves the
        # pagination boundary; a cap-bound last allowed page does not.
        if len(items) < ALERCE_PAGE_SIZE:
            break
        if page >= ALERCE_MAX_PAGES:
            raise RuntimeError(
                f"ALeRCE pagination remained cap-bound at {ALERCE_MAX_PAGES} pages"
            )
        page += 1
        time.sleep(0.3)
    df = pd.DataFrame(rows)
    if not len(df):
        df = pd.DataFrame(columns=["oid", "meanra", "meandec"])
    # ALeRCE pagination can repeat rows across page boundaries; dedupe on oid or
    # every downstream count is inflated.
    before = len(df)
    df = df.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    if len(df) != before:
        print(f"  deduped {before} -> {len(df)} unique oids")
    if reported_total is None or len(df) != reported_total:
        raise RuntimeError(
            f"ALeRCE completeness mismatch: reported {reported_total}, "
            f"retrieved {len(df)} unique OIDs; pool not cached"
        )
    payload = df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    write_cache(
        cache,
        payload,
        kind="m1_alerce_pool",
        contract=_pool_contract(mjd0, mjd1),
        row_count=len(df),
    )
    return df


def fink_unknown_latests(n: int = 1000) -> pd.DataFrame:
    """Second enumerator, complementary to ALeRCE's firstmjd window.

    The firstmjd pool only contains objects whose FIRST-EVER ZTF detection is in
    the window, so it structurally misses a previously-detected CV going into a
    new outburst -- which is most of what DCAP reports.  Fink's `latests` with
    class=Unknown returns the newest N alerts that matched no SIMBAD/VSX/GCVS/MPC
    entry and no Fink classifier, old objects included.  One request, no token.
    n > 1000 returns HTTP 500, so 1000 is the ceiling.
    """
    s = session()
    r = s.get("https://api.ztf.fink-portal.org/api/v1/latests",
              params={"class": "Unknown", "n": min(n, 1000),
                      "columns": "i:objectId,i:jd,i:magpsf,i:ra,i:dec"}, timeout=180)
    r.raise_for_status()
    d = pd.DataFrame(r.json())
    if not len(d):
        return pd.DataFrame(columns=["oid", "meanra", "meandec"])
    d = d.rename(columns={"i:objectId": "oid", "i:ra": "meanra", "i:dec": "meandec"})
    jd = pd.to_numeric(d["i:jd"], errors="coerce")
    print(f"  fink latests: {len(d)} alerts, {d['oid'].nunique()} objects, "
          f"MJD {jd.min()-2400000.5:.3f}..{jd.max()-2400000.5:.3f}")
    return d.drop_duplicates(subset=["oid"])[["oid", "meanra", "meandec"]]


def _prefetch(
    oids: list[str],
    workers: int = 3,
    *,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
    required_coverage_jd: float,
) -> None:
    """Warm the Fink cache.  3 workers ~= 5 req/s against a public REST API --
    deliberately modest; Fink publishes no rate limit but we do not lean on it."""
    from concurrent.futures import ThreadPoolExecutor
    # Existence is not enough: legacy ``[]`` files may be failed requests. The
    # shared cache validator quarantines those and schedules a real refetch.
    todo = [
        o for o in dict.fromkeys(oids)
        if not cache_is_usable(
            o,
            max_age_seconds=max_age_seconds,
            required_coverage_jd=required_coverage_jd,
        )
    ]
    if not todo:
        return
    print(f"  prefetching {len(todo)} Fink histories with {workers} workers", flush=True)
    done = [0]

    def job(oid: str) -> None:
        fetch_one(
            session(),
            oid,
            max_age_seconds=max_age_seconds,
            required_coverage_jd=required_coverage_jd,
        )
        done[0] += 1
        if done[0] % 200 == 0:
            print(f"    {done[0]}/{len(todo)}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(job, todo))


def enrich_and_filter(
    df: pd.DataFrame,
    tag: str,
    *,
    jd_ceiling: float,
    max_age_seconds: float = HISTORY_MAX_AGE_SECONDS,
) -> pd.DataFrame:
    tag = validated_tag(tag)
    s = session()
    out = []
    n = len(df)
    _prefetch(
        df["oid"].tolist(),
        max_age_seconds=max_age_seconds,
        required_coverage_jd=jd_ceiling,
    )
    pos = dict(zip(df["oid"], zip(df.get("meanra", pd.Series(dtype=float)),
                                  df.get("meandec", pd.Series(dtype=float)))))
    for i, oid in enumerate(df["oid"].tolist(), 1):
        alerts = pd.DataFrame(
            fetch_one(
                s,
                oid,
                max_age_seconds=max_age_seconds,
                required_coverage_jd=jd_ceiling,
            )
        )
        v = F.evaluate(alerts, jd_cutoff=jd_ceiling)
        rec = {"oid": oid, **{k: v.get(k) for k in
               ("passed", "channel", "reason", "first_pass_jd", "n_clean",
                "n_alerts", "mag_at_pass", "band_at_pass", "ra", "dec",
                "drb", "sgscore1", "distpsnr1", "distnr", "magnr", "gal_b",
                "simbad")}}
        rec["history_jd_ceiling"] = jd_ceiling
        # generic "sane real transient" layer, independent of our target channels
        rec["hygiene_ok"] = rec["n_clean"] >= F.N_DET_MIN
        # position for EVERY pool object (F.evaluate only reports one on a pass)
        pr, pd_ = pos.get(oid, (None, None))
        rec["pool_ra"], rec["pool_dec"] = pr, pd_
        out.append(rec)
        if i % 100 == 0:
            print(f"  fink {i}/{n}", flush=True)
            pd.DataFrame(out).to_csv(
                POOL / f"filtered_{tag}.checkpoint.csv",
                index=False,
                lineterminator="\n",
            )
        pass
    res = pd.DataFrame(out)
    return res


def main() -> None:
    mjd0, mjd1, tag = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    tag = validated_tag(tag)
    jd_ceiling = mjd1 + 2400000.5
    pool = enumerate_new_objects(mjd0, mjd1, tag)
    if "--fink-latests" in sys.argv:
        raise RuntimeError(
            "--fink-latests is not window-bound and cannot be used in a proved "
            "historical run; use m2_pool.py's complete E2 enumerator"
        )
    pool = pool.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    print(f"pool {tag}: {len(pool)} objects")
    res = enrich_and_filter(
        pool,
        tag,
        jd_ceiling=jd_ceiling,
        max_age_seconds=HISTORY_MAX_AGE_SECONDS,
    )
    if not len(res):
        res = pd.DataFrame(columns=[
            "oid", "passed", "channel", "reason", "first_pass_jd", "n_clean",
            "n_alerts", "mag_at_pass", "band_at_pass", "ra", "dec", "drb",
            "sgscore1", "distpsnr1", "distnr", "magnr", "gal_b", "simbad",
            "history_jd_ceiling", "hygiene_ok", "pool_ra", "pool_dec",
        ])
    enumerator_meta = json.loads(
        sidecar_path(POOL / f"pool_{tag}.csv").read_text(encoding="utf-8")
    )
    filtered_contract = {
        "tag": tag,
        "mjd_window": [mjd0, mjd1],
        "history_jd_ceiling": jd_ceiling,
        "source_enumerator_sha256": enumerator_meta["payload_sha256"],
        "source_row_count": len(pool),
    }
    filtered_meta = write_cache(
        POOL / f"filtered_{tag}.csv",
        res.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        kind="m1_filtered_pool",
        contract=filtered_contract,
        row_count=len(res),
    )
    summary = {
        "tag": tag, "mjd_window": [mjd0, mjd1],
        "history_jd_ceiling": jd_ceiling,
        "history_as_of_mjd": mjd1,
        "history_cache_policy": {
            "refresh": False,
            "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
            "required_coverage_jd": jd_ceiling,
        },
        "history_cache_provenance": cache_provenance(pool["oid"].tolist()),
        "enumerator_cache_provenance": (
            json.loads(
                sidecar_path(POOL / f"pool_{tag}.csv").read_text(encoding="utf-8")
            )
            if sidecar_path(POOL / f"pool_{tag}.csv").exists()
            else None
        ),
        "filtered_output_provenance": filtered_meta,
        "n_pool": int(len(pool)),
        "n_hygiene_ok": int(res["hygiene_ok"].sum()),
        "n_passed_targeted": int(res["passed"].sum()),
        "channels": res.loc[res["passed"], "channel"].value_counts().to_dict(),
    }
    atomic_write(
        OUT / f"m1_pool_{tag}.json",
        (json.dumps(summary, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
