"""W4 diagnostic: why did every pyvo run_async against ESA Gaia TAP 500?

M1's cost plan assumed 24 anonymous ASYNC strip jobs, but M1 only ever
exercised the SYNC endpoint. First async attempt: 500 on job creation.
This isolates the cause before committing the screen to a route.
"""
from __future__ import annotations

import sys
import time
import warnings

import pyvo
import requests

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

TAP = "https://gea.esac.esa.int/tap-server/tap"
svc = pyvo.dal.TAPService(TAP)


def t(tag, fn):
    t0 = time.time()
    try:
        r = fn()
        print(f"  [{tag}] {time.time()-t0:6.1f} s  OK  {r}")
        return r
    except Exception as e:  # noqa: BLE001
        print(f"  [{tag}] {time.time()-t0:6.1f} s  FAIL {type(e).__name__}: "
              f"{str(e)[:400]}")
        return None


print("== 1. trivial sync ==")
t("sync TOP 5", lambda: len(svc.search(
    "SELECT TOP 5 source_id FROM gaiadr3.gaia_source").to_table()))

print("== 2. trivial async via pyvo ==")
t("async TOP 5", lambda: len(svc.run_async(
    "SELECT TOP 5 source_id FROM gaiadr3.gaia_source").to_table()))

print("== 3. raw POST to /async (see the server's actual message) ==")
try:
    r = requests.post(TAP + "/async", data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
        "PHASE": "RUN",
        "QUERY": "SELECT TOP 5 source_id FROM gaiadr3.gaia_source"},
        timeout=120, allow_redirects=False)
    print(f"  status={r.status_code}  loc={r.headers.get('Location')}")
    print("  body[:800]:", r.text[:800].replace("\n", " "))
except Exception as e:  # noqa: BLE001
    print("  raw POST failed:", type(e).__name__, str(e)[:300])

print("== 4. ESA's own /tap-server/tap async (submit then poll manually) ==")
try:
    s = requests.Session()
    r = s.post(TAP + "/async", data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
        "QUERY": "SELECT TOP 5 source_id FROM gaiadr3.gaia_source"},
        timeout=120)
    print(f"  submit status={r.status_code}  url={r.url}")
    print("  body[:500]:", r.text[:500].replace("\n", " "))
except Exception as e:  # noqa: BLE001
    print("  submit failed:", type(e).__name__, str(e)[:300])

print("== 5. SYNC on the 4- and 6-table joins, tiny strip ==")
BASE = """FROM gaiadr3.gaia_source g
JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id"""
WJ = "JOIN gaiadr1.allwise_original_valid w ON w.allwise_oid = ab.allwise_oid"
TJ = ("JOIN gaiadr3.tmass_psc_xsc_best_neighbour tb ON tb.source_id = g.source_id "
      "JOIN gaiadr1.tmass_original_valid t ON t.designation = tb.original_ext_source_id")
WH = "WHERE g.dec BETWEEN 0.0 AND 0.08 AND d.r_med_geo < 300"
WD = "AND w.w3mpro_error IS NOT NULL AND w.w4mpro_error IS NOT NULL"

t("sync 3-table count", lambda: svc.search(
    f"SELECT COUNT(*) AS n {BASE} {WH}").to_table()["n"][0])
t("sync 4-table count", lambda: svc.search(
    f"SELECT COUNT(*) AS n {BASE} {WJ} {WH} {WD}").to_table()["n"][0])
t("sync 6-table count", lambda: svc.search(
    f"SELECT COUNT(*) AS n {BASE} {WJ} {TJ} {WH} {WD}").to_table()["n"][0])
t("sync 6-table rows", lambda: len(svc.search(
    f"""SELECT g.source_id, g.ra, g.dec, d.r_med_geo, ab.allwise_oid,
        w.w3mpro, w.w4mpro, t.j_m {BASE} {WJ} {TJ} {WH} {WD}""").to_table()))
