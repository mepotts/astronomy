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
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as F  # noqa: E402
from m1_fetch_fink import fetch_one  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

ALERCE = "https://api.alerce.online/ztf/v1/objects/"
POOL = DATA / "pool"
POOL.mkdir(parents=True, exist_ok=True)


def enumerate_new_objects(mjd0: float, mjd1: float, tag: str) -> pd.DataFrame:
    """Every ZTF object whose FIRST-EVER detection falls in [mjd0, mjd1], ndet>=2."""
    cache = POOL / f"pool_{tag}.csv"
    if cache.exists():
        df = pd.read_csv(cache)
        print(f"pool {tag}: cached {len(df)}")
        return df
    s = session()
    rows, page = [], 1
    while True:
        r = s.get(ALERCE, params={"firstmjd": [mjd0, mjd1], "ndet": 2,
                                  "page_size": 1000, "page": page,
                                  "count": "true" if page == 1 else "false"},
                  timeout=180)
        r.raise_for_status()
        j = r.json()
        items = j.get("items", [])
        if page == 1:
            print(f"pool {tag}: ALeRCE reports total={j.get('total')}")
        rows.extend(items)
        print(f"  page {page}: {len(items)} (running {len(rows)})", flush=True)
        if not j.get("has_next") or not items:
            break
        page += 1
        if page > 40:
            break
        time.sleep(0.3)
    df = pd.DataFrame(rows)
    # ALeRCE pagination can repeat rows across page boundaries; dedupe on oid or
    # every downstream count is inflated.
    before = len(df)
    df = df.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    if len(df) != before:
        print(f"  deduped {before} -> {len(df)} unique oids")
    df.to_csv(cache, index=False)
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


def _prefetch(oids: list[str], workers: int = 3) -> None:
    """Warm the Fink cache.  3 workers ~= 5 req/s against a public REST API --
    deliberately modest; Fink publishes no rate limit but we do not lean on it."""
    from concurrent.futures import ThreadPoolExecutor
    todo = [o for o in oids if not (DATA / "fink" / f"{o}.json").exists()]
    if not todo:
        return
    print(f"  prefetching {len(todo)} Fink histories with {workers} workers", flush=True)
    done = [0]

    def job(oid: str) -> None:
        fetch_one(session(), oid)
        done[0] += 1
        if done[0] % 200 == 0:
            print(f"    {done[0]}/{len(todo)}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(job, todo))


def enrich_and_filter(df: pd.DataFrame, tag: str, jd_cutoff: float | None = None
                      ) -> pd.DataFrame:
    s = session()
    out = []
    n = len(df)
    _prefetch(df["oid"].tolist())
    pos = dict(zip(df["oid"], zip(df.get("meanra", pd.Series(dtype=float)),
                                  df.get("meandec", pd.Series(dtype=float)))))
    for i, oid in enumerate(df["oid"].tolist(), 1):
        alerts = pd.DataFrame(fetch_one(s, oid))
        v = F.evaluate(alerts, jd_cutoff=jd_cutoff)
        rec = {"oid": oid, **{k: v.get(k) for k in
               ("passed", "channel", "reason", "first_pass_jd", "n_clean",
                "n_alerts", "mag_at_pass", "band_at_pass", "ra", "dec",
                "drb", "sgscore1", "distpsnr1", "distnr", "magnr", "gal_b",
                "simbad")}}
        # generic "sane real transient" layer, independent of our target channels
        rec["hygiene_ok"] = rec["n_clean"] >= F.N_DET_MIN
        # position for EVERY pool object (F.evaluate only reports one on a pass)
        pr, pd_ = pos.get(oid, (None, None))
        rec["pool_ra"], rec["pool_dec"] = pr, pd_
        out.append(rec)
        if i % 100 == 0:
            print(f"  fink {i}/{n}", flush=True)
            pd.DataFrame(out).to_csv(POOL / f"filtered_{tag}.csv", index=False)
        pass
    res = pd.DataFrame(out)
    res.to_csv(POOL / f"filtered_{tag}.csv", index=False)
    return res


def main() -> None:
    mjd0, mjd1, tag = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    pool = enumerate_new_objects(mjd0, mjd1, tag)
    if "--fink-latests" in sys.argv:
        extra = fink_unknown_latests()
        n0 = len(pool)
        pool = pd.concat([pool, extra], ignore_index=True)
        pool = pool.drop_duplicates(subset=["oid"]).reset_index(drop=True)
        print(f"  + Fink latests: {n0} -> {len(pool)} objects")
    pool = pool.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    print(f"pool {tag}: {len(pool)} objects")
    res = enrich_and_filter(pool, tag)
    summary = {
        "tag": tag, "mjd_window": [mjd0, mjd1],
        "n_pool": int(len(pool)),
        "n_hygiene_ok": int(res["hygiene_ok"].sum()),
        "n_passed_targeted": int(res["passed"].sum()),
        "channels": res.loc[res["passed"], "channel"].value_counts().to_dict(),
    }
    write_text(OUT / f"m1_pool_{tag}.json", json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
