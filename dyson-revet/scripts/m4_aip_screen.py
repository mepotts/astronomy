"""M4 -- finish the sky through the AIP Gaia mirror (gaia.aip.de/tap).

WHY THIS EXISTS.  ESAC will not complete a query that touches the crossmatch
tables (M3 §1.2: size-independent kill at ~62 s, a bare 3-table COUNT(*) at
79.8 s, still true on 2026-08-21).  M3 measured the AIP mirror as the route to
the other 52% of sky.  This driver executes that route -- and corrects four
properties of it, all MEASURED here (see `probe`); three of the four would have
silently corrupted the harvest:

  1. AIP's 30 s cap is NOT a UWS executionDuration limit.  `executionduration`
     accepts 300 / 3600 / 86400 s anonymously and reports them back, but the
     backend kills the query anyway with "canceling statement due to statement
     timeout" at ~30 s.  It is a Postgres statement_timeout.  The consequence
     is the same (jobs must fit in ~30 s of DB time) but the lever is not the
     one M3 named.

  2. The tiling that fits is NOT ~27 deg2 sky boxes.  A dec/ra box makes the
     planner scan gaia_source: a 215 deg2 box costs ~27 s of DB time before a
     single join.  A **source_id range** hits the primary key instead, and
     because Gaia's source_id is (HEALPix level-12 index) * 2^35 + sequence, a
     contiguous source_id range IS a contiguous sky region of exactly
     (span / 12*2^59) of the sphere.  MEASURED: a ~298 deg2 source_id range
     runs the whole 5-table join in 18.7 s of DB time and returns 10,003 rows.
     So the tiles here are HEALPix cells addressed as source_id ranges, and
     the sky-area bookkeeping is exact by construction.

  3. **The W3/W4 detection predicate does not transfer.**  At ESAC,
     `w3mpro_error IS NOT NULL` is exactly `ph_qual[W3] != 'U'` (verified: 0 of
     220,632 harvested rows carry a 'U' in W3 or W4).  In AIP's `catalogs.allwise`
     the null is stored as a **sentinel 0.0**, so `w3sigmpro IS NOT NULL` is
     true for every row and the cut silently does nothing -- it returned 32x
     too many rows per deg2 before this was caught.  The correct AIP predicate
     is `w3sigmpro > 0 AND w4sigmpro > 0`.  Nothing else in this file matters
     more than that line.

  4. **The 2MASS join must go through `designation`, not the oid.**  AIP's
     `catalogs.tmass` carries a `tmass_oid`, and `gaiadr3.tmass_psc_xsc_best_neighbour`
     carries a `clean_tmass_psc_xsc_oid`, and on the first few rows of the
     catalogue the two agree -- because both orderings happen to start at the
     south celestial pole.  **They are different keys.**  Joined on the oid,
     the acceptance test found ZERO of 41,844 designations matching ESAC and a
     median J-magnitude error of **+5.55 mag** (it returns a different 2MASS
     star at a similar declination), while Gaia and AllWISE columns matched
     ESAC exactly.  The correct join is
     `catalogs.tmass.designation = tmass_psc_xsc_best_neighbour.original_ext_source_id`.
     That string join times out when the query is driven by a dec/ra box, but
     it completes in 24.3 s when driven by a **source_id range** -- so point 2
     above is what makes point 4 affordable.  VERIFIED after the fix: on cell
     h2c00083, 2,497 rows overlapping the ESAC harvest have **100% identical
     2MASS designations** and |Δj_m| ≤ 9e-7.
     `catalogs.tmass_orig` looks like the ESA-numbered table and would have
     been the natural fix, but it is listed in TAP_SCHEMA and is **not
     queryable** ("Table tmass_orig not found").

THE DISTANCE CUT.  AIP has no EDR3 Bailer-Jones distances (only
`gaiadr2_contrib.geometric_distance`, keyed on DR2 source_ids).  Two routes,
in this order of preference:
  * EXACT: harvest with the lossless parallax superset and then look
    `r_med_geo` up at ESAC.  ESAC's *single-table* PK lookups on
    `external.gaiaedr3_distance` work fine (MEASURED 2,000 ids in 3.6 s) even
    while its joins are dead.  This reproduces C1 exactly.  `distances` mode.
  * PROXY: `1000/parallax < 300`.  M3 measured its recall (99.09%); `purity`
    mode here measures the other half, on a sample that contains the
    complement, which M3 could not do.

Anonymous throughout: no account, no token, no credentials.  If AIP ever
demands registration this driver stops rather than registering.

Usage:
    python scripts/m4_aip_screen.py probe
    python scripts/m4_aip_screen.py pull [--budget-min 600] [--level 2]
    python scripts/m4_aip_screen.py status
    python scripts/m4_aip_screen.py distances [--budget-min 120]
    python scripts/m4_aip_screen.py purity
    python scripts/m4_aip_screen.py accept
    python scripts/m4_aip_screen.py select [--source aip] [--jobs 12]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import traceback
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from astropy.io.votable import parse_single_table

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
W4 = ROOT / "data" / "w4"
AIPDIR = W4 / "aip"
CELLS = AIPDIR / "cells"
MANIFEST = AIPDIR / "manifest_aip.json"
DIST = AIPDIR / "distances"
AIPDIR.mkdir(parents=True, exist_ok=True)
CELLS.mkdir(parents=True, exist_ok=True)
DIST.mkdir(parents=True, exist_ok=True)

AIP_TAP = "https://gaia.aip.de/tap"
ESAC_TAP = "https://gea.esac.esa.int/tap-server/tap"
UWS = "{http://www.ivoa.net/xml/UWS/v1.0}"
SKY_DEG2 = 41252.96
# Gaia source_id = healpix_level12 * 2^35 + sequence; healpix12 in [0, 12*4^12)
SIDMAX = 12 * (2 ** 59)          # 6,917,529,027,641,081,856
# MEASURED on 220,632 ESAC-harvested rows that all satisfy r_med_geo < 300:
# the minimum parallax is 3.2668 mas, so parallax > 2.5 is a LOSSLESS superset
# with 0.77 mas of margin.  Never raise this without re-measuring.
PLX_SUPERSET = 2.5

COLS = """g.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.parallax,
 g.parallax_error, g.ruwe, g.phot_g_mean_mag, g.phot_bp_mean_mag,
 g.phot_rp_mean_mag, g.phot_g_mean_flux, g.phot_g_mean_flux_error,
 g.phot_g_n_obs, g.classprob_dsc_combmod_star, ab.allwise_oid,
 w.w1mpro, w.w2mpro, w.w3mpro, w.w4mpro,
 w.w1sigmpro AS w1mpro_error, w.w2sigmpro AS w2mpro_error,
 w.w3sigmpro AS w3mpro_error, w.w4sigmpro AS w4mpro_error,
 w.cc_flags, w.ext_flg AS ext_flag, w.ph_qual,
 t.designation AS tmass_designation, t.j_m, t.h_m, t.k_m AS ks_m"""
FROM5 = """FROM gaiadr3.gaia_source g
 JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id
 JOIN catalogs.allwise w ON w.allwise_oid = ab.allwise_oid
 JOIN gaiadr3.tmass_psc_xsc_best_neighbour tb ON tb.source_id = g.source_id
 JOIN catalogs.tmass t ON t.designation = tb.original_ext_source_id"""
# THE line that matters -- see module docstring point 3.
WDET = "AND w.w3sigmpro > 0 AND w.w4sigmpro > 0"


def cell_query(a: int, b: int) -> str:
    return (f"SELECT {COLS} {FROM5} WHERE g.source_id BETWEEN {a} AND {b - 1} "
            f"AND g.parallax > {PLX_SUPERSET} {WDET}")


# ------------------------------------------------------------ AIP async ----
def aip_async(q: str, timeout: float = 300.0, poll: float = 0.5) -> dict:
    """Run one anonymous async job.  No credentials are ever sent."""
    t0 = time.time()
    r = requests.post(AIP_TAP + "/async",
                      data={"REQUEST": "doQuery", "LANG": "ADQL",
                            "FORMAT": "votable", "MAXREC": "5000000",
                            "QUERY": q},
                      allow_redirects=False, timeout=60)
    if r.status_code == 401 or r.status_code == 403:
        raise RuntimeError(
            f"AIP asked for credentials (HTTP {r.status_code}). The project's "
            f"hard rule forbids creating an account; stopping.")
    job = r.headers.get("Location")
    if not job:
        return dict(state="NOJOB", wall=time.time() - t0, http=r.status_code,
                    err=r.text[:200])
    requests.post(job + "/phase", data={"PHASE": "RUN"}, timeout=30)
    phase = "?"
    while time.time() - t0 < timeout:
        phase = requests.get(job + "/phase", timeout=30).text.strip()
        if phase in ("COMPLETED", "ERROR", "ABORTED"):
            break
        time.sleep(poll)
    o = dict(state=phase, wall=time.time() - t0, job=job)
    try:
        x = ET.fromstring(requests.get(job, timeout=30).content)
        f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        o["db"] = round((f(x.findtext(UWS + "endTime"))
                         - f(x.findtext(UWS + "startTime"))).total_seconds(), 1)
    except Exception:  # noqa: BLE001
        o["db"] = None
    if phase == "COMPLETED":
        res = requests.get(job + "/results/result", timeout=600)
        if b'value="OVERFLOW"' in res.content:
            raise RuntimeError("AIP returned OVERFLOW -- result truncated")
        o["table"] = parse_single_table(io.BytesIO(res.content)).to_table().to_pandas()
    else:
        o["err"] = requests.get(job + "/error", timeout=30).text[-200:]
    return o


# ------------------------------------------------------------- manifest ----
def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"cells": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "params": {}}


def save_manifest(m: dict) -> None:
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=1, default=str))
    tmp.replace(MANIFEST)


def make_cells(level: int) -> list[dict]:
    """HEALPix nested cells at `level`, addressed as source_id ranges.

    A contiguous source_id range is exactly a contiguous run of level-12
    HEALPix cells, so its sky area is exactly (span / SIDMAX) of the sphere.
    Cells are issued in a fixed pseudo-random order so that a PARTIAL run is
    an unbiased sample of the sky (the same law as M2 §4.2 for the ESAC tiles).
    """
    n = 12 * 4 ** level
    span = SIDMAX // n
    cells = [dict(id=f"h{level}c{i:05d}", a=i * span, b=(i + 1) * span,
                  area=SKY_DEG2 / n) for i in range(n)]
    cells[-1]["b"] = SIDMAX
    rng = np.random.default_rng(20260821)
    return [cells[k] for k in rng.permutation(n)]


def covered_area(cells: dict) -> float:
    """Sky covered by DONE cells, never double-counting a child inside a done
    ancestor (ids are prefix-nested, as in w4_screen.covered_area)."""
    done = {k: v for k, v in cells.items() if v.get("status") == "done"}
    return sum(v.get("area", 0.0) for k, v in done.items()
               if not any(k != j and k.startswith(j) for j in done))


def split_cell(c: dict) -> list[dict]:
    mid = (c["a"] + c["b"]) // 2
    return [dict(c, id=c["id"] + "a", b=mid, area=c["area"] / 2),
            dict(c, id=c["id"] + "b", a=mid, area=c["area"] / 2)]


# ----------------------------------------------------------------- probe ---
def probe(_a: argparse.Namespace) -> None:
    """Verify the route before trusting a single row of it."""
    rep = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "tests": {}}
    print("=== AIP route verification (anonymous, no account) ===")

    print("\n[1] every catalogue the screen joins is hosted here")
    tt = aip_async("SELECT table_name FROM TAP_SCHEMA.tables")["table"]
    have = {str(t).strip() for t in tt["table_name"]}
    need = ["gaiadr3.gaia_source", "gaiadr3.allwise_best_neighbour",
            "catalogs.allwise", "gaiadr3.tmass_psc_xsc_best_neighbour",
            "catalogs.tmass"]
    for t in need:
        print(f"    {t:44s} {'OK' if t in have else 'MISSING'}")
    rep["tests"]["tables"] = {t: (t in have) for t in need}
    rep["tests"]["bailer_jones_edr3"] = any(
        "gaiaedr3_distance" in t or "edr3_distance" in t for t in have)
    print(f"    {'EDR3 Bailer-Jones distances':44s} "
          f"{'PRESENT' if rep['tests']['bailer_jones_edr3'] else 'ABSENT (expected)'}")

    print("\n[2] anonymous async, no credentials of any kind")
    o = aip_async("SELECT TOP 3 source_id FROM gaiadr3.gaia_source "
                  "WHERE parallax > 100")
    print(f"    trivial async job: {o['state']} in {o['wall']:.1f} s "
          f"(db {o['db']} s)")
    rep["tests"]["anon_async"] = o["state"]

    print("\n[3] the real per-job limit")
    r = requests.post(AIP_TAP + "/async",
                      data={"REQUEST": "doQuery", "LANG": "ADQL",
                            "FORMAT": "votable",
                            "QUERY": "SELECT TOP 1 source_id FROM gaiadr3.gaia_source"},
                      allow_redirects=False, timeout=60)
    job = r.headers.get("Location")
    got = {}
    for want in ("30", "300", "3600", "86400"):
        requests.post(job + "/executionduration",
                      data={"EXECUTIONDURATION": want}, timeout=30)
        got[want] = requests.get(job + "/executionduration", timeout=30).text.strip()
    requests.post(job + "/phase", data={"PHASE": "ABORT"}, timeout=30)
    print(f"    UWS executionDuration accepted: {got}")
    print("    ... but a long query is still killed by the backend:")
    o = aip_async("SELECT COUNT(*) AS n FROM gaiadr3.gaia_source "
                  "WHERE parallax BETWEEN 2.0 AND 2.5")
    print(f"    all-sky COUNT: {o['state']} after {o.get('db')} s db "
          f"-- {o.get('err', '')[-90:].strip()}")
    rep["tests"]["executionduration_accepted"] = got
    rep["tests"]["statement_timeout_state"] = o["state"]
    rep["tests"]["statement_timeout_db_s"] = o.get("db")

    print("\n[4] the detection predicate -- does ESAC's transfer? (it does not)")
    o = aip_async("SELECT TOP 2000 ph_qual, w3sigmpro, w4sigmpro "
                  "FROM catalogs.allwise WHERE allwise_oid BETWEEN 1000000 AND 1010000")
    d = o["table"]
    u3 = d["ph_qual"].str[2] == "U"
    print(f"    rows with ph_qual[W3]='U' : {int(u3.sum())}")
    print(f"      of those, w3sigmpro IS NULL : "
          f"{int(d.loc[u3, 'w3sigmpro'].isna().sum())}")
    print(f"      of those, w3sigmpro == 0.0  : "
          f"{int((d.loc[u3, 'w3sigmpro'] == 0).sum())}   <-- sentinel, not NULL")
    print("    => the AIP-correct predicate is  w3sigmpro > 0 AND w4sigmpro > 0")
    rep["tests"]["u_rows"] = int(u3.sum())
    rep["tests"]["u_rows_null_sig"] = int(d.loc[u3, "w3sigmpro"].isna().sum())
    rep["tests"]["u_rows_zero_sig"] = int((d.loc[u3, "w3sigmpro"] == 0).sum())

    print("\n[5] cell size against the ~30 s statement timeout")
    sizes = []
    for level in (1, 2, 3):
        n = 12 * 4 ** level
        span = SIDMAX // n
        a = 2_000_000_000_000_000_000
        t0 = time.time()
        o = aip_async(cell_query(a, a + span))
        ok = o["state"] == "COMPLETED"
        nrow = len(o["table"]) if ok else None
        print(f"    level {level}: {SKY_DEG2 / n:8.1f} deg2/cell, {n:5d} cells "
              f"-> {o['state']:9s} db={o.get('db')} s wall={time.time() - t0:.1f} s "
              f"rows={nrow}")
        sizes.append(dict(level=level, deg2=SKY_DEG2 / n, ncells=n,
                          state=o["state"], db=o.get("db"), rows=nrow))
    rep["tests"]["cell_sizes"] = sizes

    print("\n[6] ESAC single-table PK lookup (the exact-distance route)")
    import pyvo
    s = pyvo.dal.TAPService(ESAC_TAP)
    ids = pd.read_csv(W4 / "tiles" / "d13r04.csv")["source_id"].astype("int64")[:2000]
    t0 = time.time()
    try:
        n = len(s.search("SELECT source_id, r_med_geo FROM "
                         "external.gaiaedr3_distance WHERE source_id IN ("
                         + ",".join(map(str, ids)) + ")").to_table())
        print(f"    2,000 source_ids -> {n} rows in {time.time() - t0:.1f} s  OK")
        rep["tests"]["esac_pk_lookup_s"] = round(time.time() - t0, 1)
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED: {type(e).__name__} {str(e)[:120]}")
        rep["tests"]["esac_pk_lookup_s"] = None

    p = OUT / "m4_aip_route_probe.json"
    p.write_text(json.dumps(rep, indent=2, default=str))
    print(f"\nwrote {p}")


# ------------------------------------------------------------------ pull ---
def pull(a: argparse.Namespace) -> None:
    m = load_manifest()
    m["params"] = dict(level=a.level, plx=PLX_SUPERSET, budget_min=a.budget_min,
                       service=AIP_TAP)
    base = make_cells(a.level)
    base_ids = {c["id"] for c in base}
    queue = [c for c in base
             if m["cells"].get(c["id"], {}).get("status") not in ("done", "split")]
    for cid, rec in m["cells"].items():
        if cid in base_ids or rec.get("status") in ("done", "split"):
            continue
        queue.append({k: rec[k] for k in ("id", "a", "b", "area")})
    print(f"AIP pull: {len(queue)} cells to go (level {a.level}, "
          f"{SKY_DEG2 / (12 * 4 ** a.level):.0f} deg2 each), "
          f"budget {a.budget_min} min")

    t_start = time.time()
    n_done = n_fail = rows_total = 0
    consec_instant = failed_probes = 0
    cooldown = a.cooldown_sec
    stop_reason = "queue exhausted (all sky attempted)"
    while queue:
        if (time.time() - t_start) / 60.0 > a.budget_min:
            stop_reason = (f"wall-clock budget of {a.budget_min} min reached "
                           f"with {len(queue)} cells outstanding")
            print(f"\n[budget] {stop_reason}. Re-run to resume.")
            break
        c = queue.pop(0)
        rec = m["cells"].get(c["id"], {})
        if rec.get("status") == "done":
            continue
        t0 = time.time()
        try:
            o = aip_async(cell_query(c["a"], c["b"]))
            dt = time.time() - t0
            if o["state"] != "COMPLETED":
                raise RuntimeError(f"{o['state']}: {o.get('err', '')[-140:]}")
            df = o["table"]
            path = CELLS / f"{c['id']}.csv"
            df.to_csv(path, index=False)
            rows_total += len(df)
            n_done += 1
            m["cells"][c["id"]] = dict(c, status="done", n=len(df),
                                       seconds=round(dt, 1), db=o.get("db"),
                                       file=path.name)
            save_manifest(m)
            consec_instant = failed_probes = 0
            cooldown = a.cooldown_sec
            area = covered_area(m["cells"])
            print(f"  [{c['id']}] {dt:6.1f}s db={o.get('db')}s {len(df):7d} rows "
                  f"({c['area']:.0f} deg2)  cov={100 * area / SKY_DEG2:5.2f}%  "
                  f"queue={len(queue)}")
        except Exception as e:  # noqa: BLE001
            dt = time.time() - t0
            msg = f"{type(e).__name__}: {str(e)[:150]}"
            if "credentials" in str(e):
                print(f"\nSTOP: {e}")
                stop_reason = "AIP demanded an account"
                break
            tries = rec.get("tries", 0) + 1
            # Ported from w4_screen.py (M3 PR-1): a failure that returns
            # instantly is the service handing back an error page and says
            # NOTHING about this cell, so it must not consume retry budget.
            instant = dt < a.instant_sec
            if instant and rec.get("instant_tries", 0) < a.max_instant:
                consec_instant += 1
                m["cells"][c["id"]] = dict(
                    c, status="retry", tries=rec.get("tries", 0),
                    instant_tries=rec.get("instant_tries", 0) + 1,
                    last_error=msg)
                save_manifest(m)
                print(f"  [{c['id']}] {dt:6.1f}s FAIL (instant "
                      f"#{consec_instant}, no retry consumed) {msg[:90]}")
                queue.append(c)
                if consec_instant >= a.instant_trigger:
                    print(f"      [breaker] cooling {cooldown:.0f}s then probing")
                    time.sleep(cooldown)
                    try:
                        ok = aip_async("SELECT TOP 1 source_id FROM "
                                       "gaiadr3.gaia_source")["state"] == "COMPLETED"
                    except Exception:  # noqa: BLE001
                        ok = False
                    if ok:
                        print("      [breaker] service answered -- resuming")
                        consec_instant = failed_probes = 0
                        cooldown = a.cooldown_sec
                    else:
                        failed_probes += 1
                        cooldown = min(cooldown * 2, a.cooldown_max)
                        print(f"      [breaker] probe {failed_probes}/"
                              f"{a.stall_probes} FAILED")
                        if failed_probes >= a.stall_probes:
                            stop_reason = (f"outage breaker: {a.stall_probes} "
                                           f"probes failed -- AIP is down; "
                                           f"stopping cleanly at partial coverage")
                            print(f"[breaker] {stop_reason}")
                            break
                continue
            print(f"  [{c['id']}] {dt:6.1f}s FAIL ({tries}) {msg[:110]}")
            # A statement timeout IS size-dependent here (unlike ESAC's wall),
            # so splitting is the correct response -- measured in `probe`.
            timeout_like = ("statement timeout" in msg or "ERROR" in msg
                            or "ABORTED" in msg)
            if timeout_like and c["area"] > a.min_area:
                kids = split_cell(c)
                m["cells"][c["id"]] = dict(c, status="split", tries=tries,
                                           last_error=msg,
                                           children=[k["id"] for k in kids])
                queue = kids + queue
                print(f"      -> split into {kids[0]['id']}/{kids[1]['id']} "
                      f"({kids[0]['area']:.1f} deg2 each)")
            elif tries < a.retries:
                m["cells"][c["id"]] = dict(c, status="retry", tries=tries,
                                           last_error=msg)
                queue.append(c)
            else:
                n_fail += 1
                m["cells"][c["id"]] = dict(c, status="failed", tries=tries,
                                           last_error=msg)
                print(f"      -> GIVING UP on {c['id']} ({c['area']:.2f} deg2)")
            save_manifest(m)

    area = covered_area(m["cells"])
    print(f"\nSTOP REASON: {stop_reason}")
    print(f"pull: {n_done} cells this session, {area:.0f} deg2 total "
          f"({100 * area / SKY_DEG2:.2f}% of sky), {rows_total} rows this "
          f"session, {n_fail} cells abandoned")
    save_manifest(m)


def status(_a: argparse.Namespace) -> None:
    m = load_manifest()
    if not m["cells"]:
        print("no AIP manifest yet")
        return
    by: dict = {}
    for r in m["cells"].values():
        by.setdefault(r.get("status", "?"), []).append(r)
    print(f"params: {m.get('params')}")
    for k, v in sorted(by.items()):
        print(f"  {k:8s} {len(v):5d} cells  "
              f"{sum(x.get('area', 0) for x in v):9.1f} deg2  "
              f"{sum(x.get('n', 0) for x in v):10d} rows")
    area = covered_area(m["cells"])
    done = by.get("done", [])
    secs = sum(r.get("seconds", 0) for r in done)
    print(f"\ncoverage {100 * area / SKY_DEG2:.2f}% of sky ({area:,.0f} deg2); "
          f"{secs / 60:.1f} min of query time")
    if area > 0 and secs > 0:
        print(f"projected for the remaining sky: "
              f"{secs / area * (SKY_DEG2 - area) / 3600:.1f} h")


def read_cell(p: Path) -> pd.DataFrame:
    """Read one harvested cell, undoing AIP's column rename.

    AIP's TAP attaches a DataLink service descriptor keyed on the Gaia
    source_id and, as a side effect, emits that column in the VOTable under the
    name **`datalinkID`** rather than `source_id` -- for every query, and no
    SQL alias overrides it (`AS source_id` and `AS gsid` both come back as
    `datalinkID`).  Left unhandled this silently removes the join key from
    every downstream stage.  VERIFIED equal to source_id: on cell h2c00083,
    2,497 rows match ESAC-harvested source_ids with max |dra| = 0.0 and
    max |dW3| = 0.0.
    """
    d = pd.read_csv(p)
    if "source_id" not in d.columns and "datalinkID" in d.columns:
        d = d.rename(columns={"datalinkID": "source_id"})
    return d


def load_aip_rows() -> pd.DataFrame:
    m = load_manifest()
    done = [r for r in m["cells"].values() if r.get("status") == "done"]
    if not done:
        raise SystemExit("nothing harvested from AIP yet")
    fr = [read_cell(CELLS / r["file"]) for r in done
          if (CELLS / r["file"]).exists()]
    return pd.concat(fr, ignore_index=True).drop_duplicates(subset="source_id")


# ------------------------------------------------------------- distances ---
def distances(a: argparse.Namespace) -> None:
    """Attach the EXACT EDR3 Bailer-Jones r_med_geo from ESAC by PK lookup.

    ESAC's crossmatch joins are dead but its single-table PK lookups are not
    (MEASURED: 2,000 ids in 3.6 s).  This reproduces cut C1 exactly instead of
    relying on the parallax proxy.
    """
    import pyvo
    rows = load_aip_rows()
    # No source with r_med_geo < 300 can have parallax <= 3.0: the minimum
    # parallax over 220,632 such ESAC-harvested rows is 3.2668 mas.  Looking up
    # the rest would be ~3x the queries for zero possible admissions.
    need = rows.loc[rows["parallax"] > 3.0, "source_id"].astype("int64").unique()
    have = set()
    for p in sorted(DIST.glob("*.csv")):
        # A file can be truncated if the session died mid-write; drop the
        # partial row rather than crashing, and let those ids be re-fetched.
        d = pd.read_csv(p)
        if "source_id" not in d.columns:
            continue
        d = d.dropna(subset=["source_id", "r_med_geo"])
        have |= set(d["source_id"].astype("int64"))
    todo = np.array(sorted(set(need.tolist()) - have), dtype="int64")
    print(f"distances: {len(need):,} candidates, {len(have):,} already looked "
          f"up, {len(todo):,} to go")
    svc = pyvo.dal.TAPService(ESAC_TAP)
    t0 = time.time()
    # Name the next file by the first FREE index, not by the file count: if a
    # file is ever removed (e.g. a truncated one), a count-based name silently
    # OVERWRITES an existing batch. That happened once and cost 2,000 lookups,
    # of which the acceptance test found 263 in the ESAC-overlap region.
    k = 0
    while (DIST / f"d{k:05d}.csv").exists():
        k += 1
    for i in range(0, len(todo), a.batch):
        if (time.time() - t0) / 60 > a.budget_min:
            print(f"[budget] stopped with {len(todo) - i:,} ids outstanding")
            break
        chunk = todo[i:i + a.batch]
        q = ("SELECT source_id, r_med_geo, r_lo_geo, r_hi_geo FROM "
             "external.gaiaedr3_distance WHERE source_id IN ("
             + ",".join(map(str, chunk)) + ")")
        for attempt in range(a.retries):
            try:
                d = svc.search(q).to_table().to_pandas()
                d.to_csv(DIST / f"d{k:05d}.csv", index=False)
                k += 1
                while (DIST / f"d{k:05d}.csv").exists():
                    k += 1
                print(f"  [{i + len(chunk):>8,}/{len(todo):,}] {len(d):5d} rows "
                      f"({time.time() - t0:.0f}s)")
                break
            except Exception as e:  # noqa: BLE001
                print(f"    retry {attempt + 1}: {type(e).__name__} {str(e)[:90]}")
                time.sleep(10 * (attempt + 1))
    print("done")


# ---------------------------------------------------------------- purity ---
def purity(a: argparse.Namespace) -> None:
    """Measure the parallax proxy's PURITY -- what M3 could not.

    M3 measured recall (99.09%) on the ESAC harvest, but that harvest was cut
    at r_med_geo < 300 server-side, so it contained no objects OUTSIDE the cut
    and could not bound contamination.  The AIP harvest is cut only at
    parallax > 2.5, so it DOES contain the complement.
    """
    rows = load_aip_rows()
    dfs = [pd.read_csv(p) for p in sorted(DIST.glob("*.csv"))]
    if not dfs:
        raise SystemExit("run `distances` first")
    dist = (pd.concat(dfs, ignore_index=True)
            .dropna(subset=["source_id", "r_med_geo"])
            .drop_duplicates(subset="source_id"))
    j = rows.merge(dist, on="source_id", how="inner")
    print(f"purity sample: {len(j):,} AIP rows with an ESAC r_med_geo "
          f"(of {len(rows):,} harvested)")
    truth = j["r_med_geo"] < 300.0
    rep = {"n": int(len(j)), "n_true": int(truth.sum()),
           "variants": {}}
    print(f"  truly inside C1 (r_med_geo < 300): {int(truth.sum()):,} "
          f"({100 * truth.mean():.2f}%)")
    print(f"\n  {'proxy':28s} {'selected':>9s} {'TP':>8s} {'FP':>7s} "
          f"{'purity':>8s} {'recall':>8s} {'F1':>7s}")
    for name, thr in [("1000/plx < 300", 1000.0 / 300.0),
                      ("parallax > 3.0", 3.0),
                      ("parallax > 3.2", 3.2),
                      ("parallax > 3.5", 3.5)]:
        sel = j["parallax"] > thr
        tp = int((sel & truth).sum())
        fp = int((sel & ~truth).sum())
        fn = int((~sel & truth).sum())
        pur = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        f1 = 2 * pur * rec / max(pur + rec, 1e-9)
        print(f"  {name:28s} {int(sel.sum()):9,} {tp:8,} {fp:7,} "
              f"{100 * pur:7.2f}% {100 * rec:7.2f}% {f1:7.4f}")
        rep["variants"][name] = dict(threshold=thr, selected=int(sel.sum()),
                                     tp=tp, fp=fp, fn=fn, purity=pur,
                                     recall=rec, f1=f1)
    # a signal-to-noise-aware variant: the contaminants are scattered-up
    # distant stars, which have poor parallax S/N
    for snr in (5, 10):
        sel = (j["parallax"] > 1000.0 / 300.0) & (j["parallax"] / j["parallax_error"] > snr)
        tp = int((sel & truth).sum()); fp = int((sel & ~truth).sum())
        fn = int((~sel & truth).sum())
        pur = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
        name = f"1000/plx<300 & plx/err>{snr}"
        print(f"  {name:28s} {int(sel.sum()):9,} {tp:8,} {fp:7,} "
              f"{100 * pur:7.2f}% {100 * rec:7.2f}% "
              f"{2 * pur * rec / max(pur + rec, 1e-9):7.4f}")
        rep["variants"][name] = dict(selected=int(sel.sum()), tp=tp, fp=fp,
                                     fn=fn, purity=pur, recall=rec)
    p = OUT / "m4_proxy_purity.json"
    p.write_text(json.dumps(rep, indent=2, default=str))
    print(f"\nwrote {p}")


# ---------------------------------------------------------------- accept ---
def accept(a: argparse.Namespace) -> None:
    """The acceptance test M3 defined: does AIP return the same source_id set
    as ESAC on sky ESAC already delivered?"""
    aip = load_aip_rows()
    m = json.loads((W4 / "manifest.json").read_text())
    done = [r for r in m["tiles"].values() if r.get("status") == "done"]
    esac = pd.concat([pd.read_csv(W4 / "tiles" / r["file"]) for r in done],
                     ignore_index=True).drop_duplicates(subset="source_id")
    dfs = [pd.read_csv(p) for p in sorted(DIST.glob("*.csv"))]
    dist = (pd.concat(dfs, ignore_index=True)
            .dropna(subset=["source_id", "r_med_geo"])
            .drop_duplicates(subset="source_id")
            if dfs else pd.DataFrame(columns=["source_id", "r_med_geo"]))
    aipd = aip.merge(dist, on="source_id", how="left")

    # Restrict BOTH sides to the INTERSECTION of the two coverages, otherwise
    # "ESAC only" is dominated by sky AIP has not reached yet and the number
    # means nothing. AIP's coverage is a set of source_id ranges; ESAC's is a
    # set of dec/ra tiles.
    box = np.zeros(len(aipd), dtype=bool)
    for r in done:
        box |= ((aipd["dec"] >= r["dec0"]) & (aipd["dec"] <= r["dec1"])
                & (aipd["ra"] >= r["ra0"]) & (aipd["ra"] < r["ra1"]))
    sub = aipd[box & (aipd["r_med_geo"] < 300)]
    cells = [c for c in load_manifest()["cells"].values()
             if c.get("status") == "done"]
    esid = esac["source_id"].astype("int64").to_numpy()
    inrange = np.zeros(len(esac), dtype=bool)
    for c in cells:
        inrange |= (esid >= c["a"]) & (esid < c["b"])
    esac = esac[inrange]
    A = set(sub["source_id"].astype("int64"))
    E = set(esac["source_id"].astype("int64"))
    print(f"acceptance test on the intersection of the two coverages "
          f"({len(done)} ESAC tiles x {len(cells)} AIP cells):")
    print(f"  ESAC rows              {len(E):,}")
    print(f"  AIP rows in same sky   {len(A):,}")
    print(f"  in both                {len(A & E):,}")
    print(f"  ESAC only              {len(E - A):,}")
    print(f"  AIP only               {len(A - E):,}")
    print(f"  Jaccard                {len(A & E) / max(len(A | E), 1):.5f}")
    rep = dict(n_esac=len(E), n_aip=len(A), n_both=len(A & E),
               n_esac_only=len(E - A), n_aip_only=len(A - E),
               jaccard=len(A & E) / max(len(A | E), 1))
    both = sub[sub["source_id"].isin(list(A & E))].merge(
        esac, on="source_id", suffixes=("_aip", "_esac"))
    for c in ("w3mpro", "w4mpro", "j_m", "phot_g_mean_mag"):
        d = both[f"{c}_aip"] - both[f"{c}_esac"]
        print(f"  {c:18s} median diff {np.nanmedian(d):+.5f}  "
              f"max|diff| {np.nanmax(np.abs(d)):.5f}")
        rep[f"{c}_median_diff"] = float(np.nanmedian(d))
        rep[f"{c}_max_absdiff"] = float(np.nanmax(np.abs(d)))
    p = OUT / "m4_aip_acceptance.json"
    p.write_text(json.dumps(rep, indent=2, default=str))
    print(f"\nwrote {p}")


# ------------------------------------------------------- parallel fitting --
_PM = None


def _init_worker(locus: str) -> None:
    """Per-process setup: the template locus is module state in w1_selection,
    so every worker has to select the same one."""
    global _PM                                            # noqa: PLW0603
    sys.path.insert(0, str(ROOT / "scripts"))
    from w1_selection import load_pm13, use_locus         # noqa: PLC0415
    use_locus(locus)
    _PM = load_pm13()


def _fit_chunk(args):
    """Fit one chunk of stars.  fit_ds is deterministic and row-independent,
    so this is exactly the serial result in a different order -- verified with
    --jobs 1 vs --jobs N on the same input (see M4 §1)."""
    from w1_selection import fit_ds                       # noqa: PLC0415
    rows, gfloor = args
    out = []
    for r in rows:
        oa = {b: r[b] - r["dmod"] for b in
              ("BP", "G", "RP", "J", "H", "Ks", "W1", "W2", "W3", "W4")}
        f = fit_ds(oa, _PM, 100, 700, gfloor, 0.90, nt=60, ng=30)
        out.append((r["i"], f["rmse"], f["t_ds"], f["gamma"]))
    return out


# ---------------------------------------------------------------- select ---
def select(a: argparse.Namespace) -> None:
    """The local funnel (C2b..C6) on the COMBINED ESAC + AIP parent sample.

    The AIP rows carry the exact ESAC `r_med_geo` where `distances` has fetched
    it; rows without one are cut by the proxy and counted separately, so the
    proxy-limited fraction of the parent is always visible rather than hidden.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from w1_selection import use_locus                     # noqa: PLC0415
    use_locus(a.locus)

    m = load_manifest()
    aip_area = covered_area(m["cells"])
    aip = load_aip_rows()
    dfs = [pd.read_csv(p) for p in sorted(DIST.glob("*.csv"))]
    dist = (pd.concat(dfs, ignore_index=True)
            .dropna(subset=["source_id", "r_med_geo"])
            .drop_duplicates(subset="source_id")
            if dfs else pd.DataFrame(columns=["source_id", "r_med_geo"]))
    aip = aip.merge(dist[["source_id", "r_med_geo"]], on="source_id", how="left")
    n_exact = int(aip["r_med_geo"].notna().sum())
    # C1, exact where we have it, proxy where we do not
    proxy = aip["r_med_geo"].isna() & (aip["parallax"] > 1000.0 / 300.0)
    keep = (aip["r_med_geo"] < 300.0) | proxy
    print(f"AIP parent: {len(aip):,} harvested -> {int(keep.sum()):,} inside C1 "
          f"({n_exact:,} rows had an exact r_med_geo; "
          f"{int(proxy.sum()):,} fell back to the parallax proxy)")
    aip = aip[keep].copy()
    aip["_prov"] = np.where(proxy[keep], "AIP-proxy", "AIP-exact")

    esac_m = json.loads((W4 / "manifest.json").read_text())
    esac_done = [r for r in esac_m["tiles"].values() if r.get("status") == "done"]
    esac_area = sum(v.get("area", 0.0) for k, v in esac_m["tiles"].items()
                    if v.get("status") == "done"
                    and not any(k != j and k.startswith(j)
                                for j, w in esac_m["tiles"].items()
                                if w.get("status") == "done"))
    # AREA BOOKKEEPING.  An AIP cell's area is EXACT by construction (a
    # source_id range is a whole number of HEALPix level-12 cells), whereas
    # the union of the AIP cells with the ESAC dec/ra tiles is not exactly
    # computable without a HEALPix<->box intersection.  So the default funnel
    # runs on the AIP harvest ALONE, whose denominator is exact and whose
    # equivalence to the ESAC harvest is measured (`accept`: Jaccard 1.00000,
    # zero photometric disagreement).  --source combined is available but its
    # area is only a lower bound, so it is never the quoted funnel.
    if a.source == "combined":
        esac = pd.concat([pd.read_csv(W4 / "tiles" / r["file"])
                          for r in esac_done], ignore_index=True)
        esac["_prov"] = "ESAC"
        rows = (pd.concat([aip, esac], ignore_index=True)
                .drop_duplicates(subset="source_id", keep="first")
                .reset_index(drop=True))
        area = (SKY_DEG2 if aip_area > SKY_DEG2 * 0.999
                else max(aip_area, esac_area))
        print(f"combined parent (area is a LOWER BOUND): {len(rows):,} rows "
              f"over >= {area:,.0f} deg2; AIP {aip_area:,.0f}, "
              f"ESAC {esac_area:,.0f} deg2")
    else:
        rows = aip.reset_index(drop=True)
        area = SKY_DEG2 if aip_area > SKY_DEG2 * 0.999 else aip_area
        print(f"AIP-only parent: {len(rows):,} rows over {area:,.0f} deg2 "
              f"({100 * area / SKY_DEG2:.2f}% of sky, exact by construction); "
              f"ESAC's {esac_area:,.0f} deg2 is held back as the cross-check")

    funnel = {"_area_deg2": area, "_sky_fraction": area / SKY_DEG2,
              "_aip_area": aip_area, "_esac_area": esac_area,
              "_n_exact_dist": n_exact, "_n_proxy_dist": int(proxy.sum()),
              "T2_w34det": int(len(rows))}
    rows["cc_ok"] = rows["cc_flags"].astype(str).str.strip().isin(["0000", "0"])
    funnel["T3_ccflags"] = int(rows["cc_ok"].sum())
    bins = np.arange(np.nanmin(rows["phot_g_mean_mag"]) - 0.1,
                     np.nanmax(rows["phot_g_mean_mag"]) + 0.3, 0.2)
    rows["_bin"] = np.digitize(rows["phot_g_mean_mag"], bins)
    med = rows.groupby("_bin").agg(
        fp=("phot_g_mean_flux", "median"),
        ep=("phot_g_mean_flux_error", "median"),
        np_=("phot_g_n_obs", "median")).reset_index()
    rows = rows.merge(med, on="_bin", how="left")
    rows["gvar"] = (rows["fp"] * rows["phot_g_mean_flux_error"]
                    * np.sqrt(rows["phot_g_n_obs"])
                    / (rows["phot_g_mean_flux"] * rows["ep"] * np.sqrt(rows["np_"])))
    rows["snr3"] = 1.0857 / rows["w3mpro_error"]
    rows["snr4"] = 1.0857 / rows["w4mpro_error"]
    rows["snr_ok"] = (rows["snr3"] >= 3.5) & (rows["snr4"] >= 3.5)
    rows["extra_ok"] = ((rows["gvar"] < 2) & (rows["ruwe"] < 1.4)
                        & (rows["ext_flag"] == 0)
                        & (rows["classprob_dsc_combmod_star"] > 0.9))
    need = ["phot_bp_mean_mag", "phot_rp_mean_mag", "j_m", "h_m", "ks_m",
            "w1mpro", "w2mpro", "w3mpro", "w4mpro", "r_med_geo"]
    pre = rows[rows["cc_ok"]].dropna(subset=[c for c in need
                                             if c != "r_med_geo"]).copy()
    # proxy rows have no r_med_geo; use the parallax distance for the modulus
    pre["dist"] = np.where(pre["r_med_geo"].notna(), pre["r_med_geo"],
                           1000.0 / pre["parallax"])
    funnel["T2_full10band"] = int(len(pre))
    pre["dmod"] = 5 * np.log10(pre["dist"] / 10.0)
    pre["M_G"] = pre["phot_g_mean_mag"] - pre["dmod"]
    infit = pre[(pre["M_G"] >= a.mg_lo) & (pre["M_G"] <= a.mg_hi)]
    funnel["T3_in_template_window"] = int(len(infit))
    funnel["_mg_window"] = [a.mg_lo, a.mg_hi]
    funnel["_locus"] = a.locus
    funnel["_gamma_floor"] = a.gamma_floor

    infit = infit.reset_index(drop=True)
    cmap = {"BP": "phot_bp_mean_mag", "G": "phot_g_mean_mag",
            "RP": "phot_rp_mean_mag", "J": "j_m", "H": "h_m", "Ks": "ks_m",
            "W1": "w1mpro", "W2": "w2mpro", "W3": "w3mpro", "W4": "w4mpro"}
    work = [dict({b: float(infit.at[i, c]) for b, c in cmap.items()},
                 dmod=float(infit.at[i, "dmod"]), i=i) for i in range(len(infit))]
    chunks = [(work[k:k + 250], a.gamma_floor)
              for k in range(0, len(work), 250)]
    t0 = time.time()
    print(f"  fitting {len(work):,} stars on {a.jobs} process(es)...")
    results = []
    if a.jobs <= 1:
        _init_worker(a.locus)
        for m_, ch in enumerate(chunks):
            results += _fit_chunk(ch)
            if m_ % 40 == 0:
                print(f"    {len(results):,}/{len(work):,} "
                      f"({time.time() - t0:.0f} s)")
    else:
        import multiprocessing as mp                       # noqa: PLC0415
        with mp.Pool(a.jobs, initializer=_init_worker,
                     initargs=(a.locus,)) as pool:
            for m_, res in enumerate(pool.imap_unordered(_fit_chunk, chunks)):
                results += res
                if m_ % 40 == 0:
                    print(f"    {len(results):,}/{len(work):,} "
                          f"({time.time() - t0:.0f} s)", flush=True)
    fits = {i: (rm, td, gm) for i, rm, td, gm in results}
    keep_rows = []
    for i, (rm, td, gm) in fits.items():
        if rm > 0.2:
            continue
        r = infit.iloc[i]
        keep_rows.append(dict(
            source_id=int(r["source_id"]), ra=r["ra"], dec=r["dec"],
            rmse=rm, t_ds=td, gamma=gm, M_G=r["M_G"], snr3=r["snr3"],
            snr4=r["snr4"], gvar=r["gvar"], ruwe=r["ruwe"],
            extra_ok=bool(r["extra_ok"]), snr_ok=bool(r["snr_ok"]),
            r_med_geo=r["dist"], w1mpro=r["w1mpro"], w2mpro=r["w2mpro"],
            w3mpro=r["w3mpro"], w4mpro=r["w4mpro"], prov=r["_prov"]))
    funnel["_fit_n"] = len(fits)
    funnel["_fit_seconds"] = round(time.time() - t0, 1)
    funnel["_jobs"] = a.jobs
    surv = pd.DataFrame(keep_rows).sort_values("source_id").reset_index(drop=True)
    funnel["T3_rmse"] = int(len(surv))
    tag = a.tag or f"m4_g{a.gamma_floor:g}"
    if len(surv):
        s2 = surv[surv["extra_ok"]]
        funnel["T4_extra"] = int(len(s2))
        fin = s2[s2["snr_ok"]]
        funnel["T5_snr"] = int(len(fin))
        surv.to_csv(OUT / f"w4_rmse_survivors_{tag}.csv", index=False)
        fin.to_csv(OUT / f"w4_previsual_candidates_{tag}.csv", index=False)
    else:
        funnel["T4_extra"] = funnel["T5_snr"] = 0
    fsky = area / SKY_DEG2
    funnel["_paper_expected"] = {
        "w34det_post_cc_3.2e5": 3.2e5 * fsky, "rmse_11243": 11243 * fsky,
        "cnn_5732": 5732 * fsky, "extra_5137": 5137 * fsky,
        "snr_368": 368 * fsky, "final_7": 7 * fsky}
    OUT.joinpath(f"w4_funnel_{tag}.json").write_text(
        json.dumps(funnel, indent=2, default=str))
    print(json.dumps(funnel, indent=2, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe"); p.set_defaults(func=probe)
    p = sub.add_parser("status"); p.set_defaults(func=status)
    p = sub.add_parser("pull")
    p.add_argument("--level", type=int, default=2)
    p.add_argument("--budget-min", dest="budget_min", type=float, default=600.0)
    p.add_argument("--retries", type=int, default=6)
    p.add_argument("--min-area", dest="min_area", type=float, default=1.0)
    p.add_argument("--instant-sec", dest="instant_sec", type=float, default=5.0)
    p.add_argument("--instant-trigger", dest="instant_trigger", type=int, default=8)
    p.add_argument("--max-instant", dest="max_instant", type=int, default=60)
    p.add_argument("--cooldown-sec", dest="cooldown_sec", type=float, default=120.0)
    p.add_argument("--cooldown-max", dest="cooldown_max", type=float, default=900.0)
    p.add_argument("--stall-probes", dest="stall_probes", type=int, default=6)
    p.set_defaults(func=pull)
    p = sub.add_parser("distances")
    p.add_argument("--batch", type=int, default=2000)
    p.add_argument("--budget-min", dest="budget_min", type=float, default=180.0)
    p.add_argument("--retries", type=int, default=4)
    p.set_defaults(func=distances)
    p = sub.add_parser("purity"); p.set_defaults(func=purity)
    p = sub.add_parser("accept"); p.set_defaults(func=accept)
    p = sub.add_parser("select")
    p.add_argument("--gamma-floor", dest="gamma_floor", type=float, default=0.10)
    p.add_argument("--tag", default="")
    p.add_argument("--locus", default="wise_locus_extended.csv")
    p.add_argument("--mg-lo", dest="mg_lo", type=float, default=0.5)
    p.add_argument("--mg-hi", dest="mg_hi", type=float, default=14.0)
    p.add_argument("--source", choices=["aip", "combined"], default="aip",
                   help="aip = the AIP harvest alone (exact area); combined "
                        "also folds in the ESAC tiles (area is a lower bound)")
    p.add_argument("--jobs", type=int, default=1,
                   help="parallel fitting processes; fit_ds is deterministic "
                        "and row-independent so --jobs N == --jobs 1")
    p.set_defaults(func=select)
    a = ap.parse_args()
    try:
        a.func(a)
    except KeyboardInterrupt:
        print("\ninterrupted -- manifest is current, re-run to resume")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
