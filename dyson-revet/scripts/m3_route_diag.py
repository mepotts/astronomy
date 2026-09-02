"""M3 route diagnostic: ESAC's sync wall MOVED, so re-measure before resuming.

M2 measured the ESA Gaia sync endpoint failing at a ~181 s wall that was
INDEPENDENT of tile size (queue/load), which made retry the correct response
and splitting a waste. On 2026-08-21 the resume met a different failure:

    DALQueryError: Job timeout/aborted   at 61.9, 61.9, 62.2 s (3 of 4)

That is a server-side JOB TIME LIMIT, not a queue wall -- and unlike a queue
wall it IS size-dependent, so the M2 rule ("retry, never split") may now be
exactly backwards. This script measures, rather than assumes:

  1. is anonymous ASYNC back? (M2: HTTP 500 on every job) -- if yes, the whole
     tiling problem disappears: async has no 60 s limit.
  2. what is the current sync wall, timed precisely?
  3. what tile AREA fits inside it for the real 6-table screen query?

Output: out/m3_route_diag.json + a printed recommendation.

Run with the pull STOPPED (one anonymous connection is the polite load).
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

TAP = "https://gea.esac.esa.int/tap-server/tap"
svc = pyvo.dal.TAPService(TAP)

from w4_screen import COLS, COLS_2MASS, FROM3, JOIN_W, JOIN_T, WDET  # noqa: E402


def tile_query(dec0: float, dec1: float, ra0: float, ra1: float) -> str:
    w = (f"WHERE g.dec BETWEEN {dec0:.8f} AND {dec1:.8f} "
         f"AND g.ra >= {ra0:.8f} AND g.ra < {ra1:.8f} AND d.r_med_geo < 300")
    return (f"SELECT {COLS + COLS_2MASS} {FROM3} {JOIN_W} {JOIN_T} {w} {WDET}")


def area_of(dec0: float, dec1: float, ra0: float, ra1: float) -> float:
    s0, s1 = np.sin(np.radians([dec0, dec1]))
    return float((ra1 - ra0) / 360.0 * 4 * np.pi * (s1 - s0) / 2
                 * (180 / np.pi) ** 2)


def timed(tag: str, fn) -> dict:
    t0 = time.time()
    try:
        n = fn()
        dt = time.time() - t0
        print(f"  [{tag}] {dt:6.1f} s  OK   {n} rows", flush=True)
        return {"tag": tag, "ok": True, "seconds": round(dt, 1), "n": n}
    except Exception as e:  # noqa: BLE001
        dt = time.time() - t0
        print(f"  [{tag}] {dt:6.1f} s  FAIL {type(e).__name__}: "
              f"{str(e)[:120]}", flush=True)
        return {"tag": tag, "ok": False, "seconds": round(dt, 1),
                "error": f"{type(e).__name__}: {str(e)[:200]}"}


res = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "tests": []}

print("== 1. baseline: is the service answering at all? ==")
res["tests"].append(timed("sync TOP 5", lambda: len(
    svc.search("SELECT TOP 5 source_id FROM gaiadr3.gaia_source").to_table())))

print("== 2. anonymous ASYNC (M2 found HTTP 500 on every job) ==")
res["tests"].append(timed("async TOP 5", lambda: len(
    svc.run_async("SELECT TOP 5 source_id FROM gaiadr3.gaia_source").to_table())))

# use an UNDONE tile's footprint so nothing is wasted: d17r02 is outstanding
DEC0, DEC1 = 12.024699, 16.955707      # band d17 (approx, recomputed below)
print("== 3. sync 6-table screen query vs tile AREA ==")
# a real outstanding tile: dec band 17 of 24, RA sector 2 of 8 (90-135 deg)
s = np.linspace(-1.0, 1.0, 25)
decs = np.degrees(np.arcsin(s))
DEC0, DEC1 = float(decs[17]), float(decs[18])
print(f"   (dec band {DEC0:.3f} to {DEC1:.3f}, the real d17rXX footprint)")
for frac, ra0, ra1 in [(1.0, 90.0, 135.0), (0.5, 90.0, 112.5),
                       (0.25, 90.0, 101.25), (0.125, 90.0, 95.625)]:
    a = area_of(DEC0, DEC1, ra0, ra1)
    r = timed(f"sync {a:6.1f} deg2 (RA {ra0:.1f}-{ra1:.1f})",
              lambda ra0=ra0, ra1=ra1: len(
                  svc.search(tile_query(DEC0, DEC1, ra0, ra1)).to_table()))
    r["area_deg2"] = round(a, 1)
    res["tests"].append(r)
    if r["ok"]:
        print(f"      -> {a:.1f} deg2 FITS inside the wall "
              f"({r['seconds']} s); larger tiles are the problem, not load")
        break

print("== 4. async on a real tile (the route that would end the tiling) ==")
if res["tests"][1]["ok"]:
    a = area_of(DEC0, DEC1, 90.0, 135.0)
    r = timed(f"async {a:.1f} deg2", lambda: len(
        svc.run_async(tile_query(DEC0, DEC1, 90.0, 135.0)).to_table()))
    r["area_deg2"] = round(a, 1)
    res["tests"].append(r)
else:
    print("   skipped: async is still unavailable")

ok_areas = [t["area_deg2"] for t in res["tests"]
            if t.get("ok") and "area_deg2" in t]
fail_areas = [t["area_deg2"] for t in res["tests"]
              if not t.get("ok") and "area_deg2" in t]
res["largest_ok_area"] = max(ok_areas) if ok_areas else None
res["smallest_fail_area"] = min(fail_areas) if fail_areas else None
res["async_available"] = bool(res["tests"][1]["ok"])

print("\n== RECOMMENDATION ==")
if res["async_available"]:
    print("  ASYNC IS BACK -> switch to --mode async; the 60 s sync limit "
          "stops mattering.")
elif res["largest_ok_area"]:
    # 8 RA sectors gives 214.9 deg2 tiles; work out the split that fits
    need = 214.9 / res["largest_ok_area"]
    rasplit = int(8 * 2 ** np.ceil(np.log2(max(need, 1.0))))
    print(f"  sync only. Largest tile that fits: "
          f"{res['largest_ok_area']} deg2; smallest that fails: "
          f"{res['smallest_fail_area']}. -> re-tile with --rasplit {rasplit} "
          f"({214.9 * 8 / rasplit:.1f} deg2 per tile).")
    res["recommend_rasplit"] = rasplit
else:
    print("  nothing succeeded -- the service is degraded; hold and re-probe.")

(OUT / "m3_route_diag.json").write_text(json.dumps(res, indent=2))
print(f"\nwrote {OUT / 'm3_route_diag.json'}")
