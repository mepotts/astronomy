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
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as M1  # noqa: E402
import m2_filter as F2  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

ALERCE = "https://api.alerce.online/ztf/v1/objects/"
FINK_LATESTS = "https://api.ztf.fink-portal.org/api/v1/latests"
FINK_CLASSES = "https://api.ztf.fink-portal.org/api/v1/classes"
FINK_OBJ = "https://api.ztf.fink-portal.org/api/v1/objects"

AMP_ENUM = F2.AMP_MIN          # never deeper than the filter
EPISODE_FLOOR_DAYS = 60.0      # see the note in main(): a candidate pass
                               # must be evaluated on the CURRENT episode
POOL = DATA / "pool"
POOL.mkdir(parents=True, exist_ok=True)

E2_COLS = ("i:objectId,i:jd,i:magpsf,i:magnr,i:fid,i:ra,i:dec,i:drb,i:rb,"
           "i:isdiffpos,i:ndethist,i:jdstarthist,d:cdsxmatch")

# classes that are never worth enumerating whatever the veto list says:
# solar-system (M1 Layer 1 rejects them by construction) and the aggregate
# counters Fink publishes in /statistics but does not serve as classes.
NEVER_ENUMERATE = {"Solar System MPC", "Solar System candidate", "Tracklet",
                   "simbad_gal", "simbad_tot"}


def mjd_to_ut(mjd: float) -> str:
    return pd.Timestamp((mjd + 2400000.5 - 2440587.5) * 86400,
                        unit="s", tz="UTC").strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# which classes does the frozen filter NOT veto?
# --------------------------------------------------------------------------- #
def enumerable_classes(s) -> list[str]:
    r = s.get(FINK_CLASSES, timeout=120)
    r.raise_for_status()
    raw = r.json()
    names: list[str] = []
    for group, lst in raw.items():
        if "TNS" in group:            # already in TNS -> Layer 6 rejects anyway
            continue
        for c in lst:
            names.append(str(c).replace("(SIMBAD) ", "").replace("(CTA) ", ""))
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
    for attempt in range(3):
        try:
            r = s.get(FINK_LATESTS,
                      params={"class": cls, "n": n, "startdate": mjd_to_ut(t0),
                              "stopdate": mjd_to_ut(t1), "columns": E2_COLS},
                      timeout=300)
            if r.status_code == 200:
                j = r.json()
                return pd.DataFrame(j) if j else pd.DataFrame()
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return pd.DataFrame()


def _latests_complete(s, cls: str, t0: float, t1: float, depth: int = 0
                      ) -> pd.DataFrame:
    """One call; if the 1000-row cap binds, bisect the window until it does not."""
    d = _latests(s, cls, t0, t1)
    if len(d) < 1000 or depth >= 7:
        return d
    mid = (t0 + t1) / 2
    return pd.concat([_latests_complete(s, cls, t0, mid, depth + 1),
                      _latests_complete(s, cls, mid, t1, depth + 1)],
                     ignore_index=True)


def arm_e2_outbursts(t0: float, t1: float, tag: str) -> pd.DataFrame:
    cache = POOL / f"e2_{tag}.csv"
    if cache.exists():
        d = pd.read_csv(cache)
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
        return pd.DataFrame(columns=["oid", "meanra", "meandec"])
    a = pd.concat(frames, ignore_index=True)
    print(f"E2: {n_raw} alerts across the window")

    for c in ("i:magpsf", "i:magnr", "i:drb", "i:rb"):
        a[c] = pd.to_numeric(a.get(c), errors="coerce")
    pos = a["i:isdiffpos"].astype(str).str.strip().isin(["t", "1", "T", "true"])
    conf = (a["i:drb"] >= M1.DRB_MIN) | (a["i:drb"].isna()
                                         & (a["i:rb"] >= M1.RB_MIN))
    no_ref = a["i:magnr"].isna() | (a["i:magnr"] >= 99) | (a["i:magnr"] <= 0)
    amp = a["i:magnr"] - a["i:magpsf"]
    sel = pos & conf & (no_ref | (amp >= AMP_ENUM))
    a = a[sel]
    print(f"E2: {int(sel.sum())} alerts pass hygiene + amp>={AMP_ENUM} "
          f"(or no reference source)")
    out = (a.rename(columns={"i:objectId": "oid", "i:ra": "meanra",
                             "i:dec": "meandec"})
            .drop_duplicates(subset=["oid"])[["oid", "meanra", "meandec"]])
    out["arm"] = "E2_outburst"
    out.to_csv(cache, index=False)
    print(f"E2 outburst arm: {len(out)} unique objects")
    return out


# --------------------------------------------------------------------------- #
# arm E1 -- new sources (M1's enumerator, unchanged)
# --------------------------------------------------------------------------- #
def arm_e1_new(t0: float, t1: float, tag: str) -> pd.DataFrame:
    cache = POOL / f"e1_{tag}.csv"
    if cache.exists():
        d = pd.read_csv(cache)
        print(f"E1 new-source arm: cached {len(d)} objects")
        return d
    s = session()
    rows, page = [], 1
    while True:
        r = s.get(ALERCE, params={"firstmjd": [t0, t1], "ndet": 2,
                                  "page_size": 1000, "page": page,
                                  "count": "true" if page == 1 else "false"},
                  timeout=300)
        r.raise_for_status()
        j = r.json()
        items = j.get("items", [])
        rows.extend(items)
        if page == 1:
            print(f"  ALeRCE reports total={j.get('total')}")
        # TRAP: with count=false ALeRCE does not populate has_next reliably, so a
        # loop that trusts it stops after one page and silently truncates the arm
        # at page_size.  Page until a page comes back short instead.
        if len(items) < 1000 or page > 40:
            break
        page += 1
        time.sleep(0.3)
    d = pd.DataFrame(rows)
    if not len(d):
        return pd.DataFrame(columns=["oid", "meanra", "meandec", "arm"])
    d = d.drop_duplicates(subset=["oid"])[["oid", "meanra", "meandec"]]
    d["arm"] = "E1_new"
    d.to_csv(cache, index=False)
    print(f"E1 new-source arm: {len(d)} objects")
    return d


# --------------------------------------------------------------------------- #
def fetch_batch(s, oids: list[str], chunk: int = 60) -> dict:
    cache = DATA / "fink"
    cache.mkdir(exist_ok=True)
    out: dict[str, pd.DataFrame] = {}
    todo = []
    for o in oids:
        p = cache / f"{o}.json"
        if p.exists():
            try:
                out[o] = pd.DataFrame(json.loads(p.read_text(encoding="utf-8")))
                continue
            except Exception:
                pass
        todo.append(o)
    print(f"  fink: {len(out)} cached, {len(todo)} to fetch")
    for i in range(0, len(todo), chunk):
        part = todo[i:i + chunk]
        got, ok = {}, False
        for attempt in range(3):
            try:
                r = s.post(FINK_OBJ, json={"objectId": ",".join(part),
                                           "output-format": "json",
                                           "withupperlim": "False"}, timeout=300)
                if r.status_code == 200:
                    d = pd.DataFrame(r.json())
                    if len(d):
                        for oid, g in d.groupby("i:objectId"):
                            got[str(oid)] = g.reset_index(drop=True)
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(3 * (attempt + 1))
        # TRAP, paid for once: a batch that times out must NOT be cached as "this
        # object has no alerts".  That poisons the cache permanently and every
        # later run silently drops the whole batch.  Fall back to one-at-a-time,
        # and only write an empty file when a single-object fetch also came back
        # empty.
        if not ok:
            print(f"    batch of {len(part)} failed -- falling back to "
                  f"per-object", flush=True)
            for o in part:
                try:
                    r = s.post(FINK_OBJ, json={"objectId": o,
                                               "output-format": "json",
                                               "withupperlim": "False"},
                               timeout=180)
                    if r.status_code == 200:
                        got[o] = pd.DataFrame(r.json())
                except Exception:
                    pass
                time.sleep(0.2)
        for o in part:
            g = got.get(o, pd.DataFrame())
            (cache / f"{o}.json").write_text(g.to_json(orient="records"),
                                             encoding="utf-8")
            out[o] = g
        if (i // chunk) % 5 == 0:
            print(f"    fink {min(i+chunk, len(todo))}/{len(todo)}", flush=True)
    return out


def main() -> None:
    t0, t1, tag = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    e1 = arm_e1_new(t0, t1, tag)
    e2 = arm_e2_outbursts(t0, t1, tag)
    pool = pd.concat([e1, e2], ignore_index=True)
    n1, n2 = len(e1), len(e2)
    pool = pool.drop_duplicates(subset=["oid"]).reset_index(drop=True)
    overlap = n1 + n2 - len(pool)
    print(f"pool {tag}: E1 {n1} + E2 {n2} - {overlap} overlap = {len(pool)} objects")

    s = session()
    hist = fetch_batch(s, pool["oid"].tolist())

    # BUG FOUND AT M2-04, inherited from M1: evaluating a candidate pass with no
    # jd_floor makes the trigger the object's ALL-TIME first passing epoch, which
    # for a recurrent CV is an eruption years ago.  Every epoch-dependent column --
    # mag_at_pass, first_pass_jd, per-band amplitude, peak-to-peak, and the
    # flat-residual veto -- then describes that old outburst instead of tonight's.
    # On the first M2 run 41 of 44 candidates had a trigger epoch more than a year
    # before the enumeration window.  Floor the visible history at the episode
    # convention M1-04 already used (60 d) so the filter fires on the CURRENT
    # episode.  This moves no threshold.
    jd_floor = t0 + 2400000.5 - EPISODE_FLOOR_DAYS
    rows = []
    for _, r in pool.iterrows():
        a = hist.get(r["oid"], pd.DataFrame())
        v = F2.evaluate(a, F2.M2_FULL, jd_floor=jd_floor)
        v_m1 = M1.evaluate(a, jd_floor=jd_floor)
        rows.append({
            "oid": r["oid"], "arm": r["arm"],
            "pool_ra": r.get("meanra"), "pool_dec": r.get("meandec"),
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
    res.to_csv(POOL / f"m2_filtered_{tag}.csv", index=False)
    summary = {
        "tag": tag, "mjd_window": [t0, t1],
        "episode_floor_days": EPISODE_FLOOR_DAYS,
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
    write_text(OUT / f"m2_pool_{tag}.json", json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
