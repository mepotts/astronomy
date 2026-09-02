"""M3: present-day state bounds for the M2 shortlist items 1-5.

Question per object: has ANY pointed X-ray instrument covered the position
since (or before) the eRASS window, and what do the most recent public
detections/limits say about its state today?

Services (all anonymous, no accounts):
  1. HEASARC Xamin TAP (https://heasarc.gsfc.nasa.gov/xamin/vo/tap), upload
     join against the observation master catalogs:
       swiftmastr  r = 12 arcmin (XRT FOV radius ~11.8'),
       xmmmaster   r = 15 arcmin (EPIC FOV),
       chanmaster  r = 10 arcmin (ACIS field, off-axis PSF caveat).
     Only rows with a real start time count as performed coverage.
  2. Swift-XRT LSXPS living catalog via the swifttools python package
     (v4.0.2, unauthenticated - registration is only needed for XRT product
     builds/ToO, which we do NOT touch):
       - cone search r = 30 arcsec for catalogued detections;
       - the SXPS upper-limit server (getUpperLimits, whichData='all',
         3 sigma, total band 0.3-10 keV) - per-dataset limits with dates =
         the live present-day bound where Swift has data.
     Note: python 3.12 needs `setuptools` installed for swifttools' distutils
     import (done in the venv).

Output: out/m3_state_bounds.csv (one row per object) +
out/m3_state_bounds_detail.json (full per-observation records).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo
from astropy.table import Table
from astropy.time import Time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
HEASARC_TAP = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"

TARGETS = [
    ("3eRASS J094452.8-711152", 146.22033015318507, -71.19802286286726),
    ("3eRASS J155100.8-453347", 237.75364824786325, -45.56326785295143),
    ("3eRASS J060622.5-624814", 91.59383843034584, -62.80399358684873),
    ("1eRASS J050338.2-304513", 75.90941019162457, -30.75362190505544),
    ("1eRASS J051910.4-253443", 79.79373375742396, -25.57881066390798),
]

MASTERS = [
    # table, radius_deg, time_col, expo_col, extra cols
    # swiftmastr r=17': XRT FOV is a 23.6'x23.6' square, so pointings up to
    # the ~16.7' half-diagonal can still cover the position in a corner; the
    # LSXPS UL server (actual images) is authoritative for on-position data.
    ("swiftmastr", 17 / 60.0, "start_time", "xrt_exposure", ["obsid", "name"]),
    ("xmmmaster", 15 / 60.0, "time", "duration", ["obsid", "name", "status",
                                                  "public_date"]),
    ("chanmaster", 10 / 60.0, "time", "exposure", ["obsid", "name", "status",
                                                   "public_date"]),
]


def mjd_to_date(mjd) -> str:
    try:
        if mjd is None or not np.isfinite(mjd) or mjd <= 0:
            return ""
        return Time(mjd, format="mjd").iso[:10]
    except Exception:
        return ""


def heasarc() -> dict:
    svc = pyvo.dal.TAPService(HEASARC_TAP)
    up = Table({"tid": np.arange(len(TARGETS)).astype("int32"),
                "ra": np.array([t[1] for t in TARGETS], "f8"),
                "dec": np.array([t[2] for t in TARGETS], "f8")})
    out: dict = {}
    for table, rad, tcol, ecol, extra in MASTERS:
        cols = ", ".join(f"x.{c}" for c in [tcol, ecol, "ra", "dec"] + extra)
        q = (f"SELECT c.tid, {cols} FROM TAP_UPLOAD.pos AS c JOIN {table} AS x "
             f"ON 1=CONTAINS(POINT('ICRS', x.ra, x.dec), "
             f"CIRCLE('ICRS', c.ra, c.dec, {rad}))")
        res = svc.search(q, uploads={"pos": up}).to_table().to_pandas()
        res.columns = [c.lower().split("_", 1)[1]
                       if c.lower().startswith(("c_", "x_")) else c.lower()
                       for c in res.columns]
        out[table] = res
        print(f"  {table}: {len(res)} rows")
        time.sleep(1)
    return out


def lsxps(ra: float, dec: float) -> dict:
    from swifttools.ukssdc.query import SXPSQuery
    import swifttools.ukssdc.data.SXPS as sx

    r: dict = {}
    q = SXPSQuery(cat="LSXPS", silent=True)
    q.addConeSearch(ra=ra, dec=dec, radius=30, units="arcsec")
    q.submit()
    if q.results is None or not len(q.results):
        r["sources"] = []
    else:
        df = q.results
        keep = [c for c in ["LSXPS_ID", "IAUName", "Err90", "_r",
                            "Rate_band0", "Rate_band0_pos", "Rate_band0_neg",
                            "FirstObsDate", "LastObsDate",
                            "FirstDetDate", "LastDetDate", "NumObs",
                            "NumDetObs"] if c in df.columns]
        r["sources"] = json.loads(df[keep].to_json(orient="records"))

    ul = sx.getUpperLimits(RA=ra, Dec=dec, cat="LSXPS", bands=("total",),
                           whichData="all", timeFormat="MJD", sigma=3.0,
                           silent=True)
    if isinstance(ul, dict) and ul.get("NotObserved"):
        r["ul"] = "NotObserved"
    else:
        # swifttools returns {'ULData': DataFrame-like, ...} or a DataFrame
        df = None
        if isinstance(ul, pd.DataFrame):
            df = ul
        elif isinstance(ul, dict):
            for v in ul.values():
                if isinstance(v, pd.DataFrame):
                    df = v
                    break
        if df is None:
            r["ul"] = {"raw": str(ul)[:2000]}
        else:
            r["ul"] = json.loads(df.to_json(orient="records"))
    return r


def main() -> None:
    print("HEASARC master-catalog joins ...")
    masters = heasarc()

    detail: dict = {}
    rows = []
    for tid, (name, ra, dec) in enumerate(TARGETS):
        rec: dict = {"name": name, "ra": ra, "dec": dec}
        det: dict = {}

        sw = masters["swiftmastr"]
        sw = sw[(sw["tid"] == tid) & (sw["start_time"] > 0)
                & (sw["xrt_exposure"] > 0)]
        rec["swift_nobs"] = len(sw)
        rec["swift_xrt_expo_ks"] = round(sw["xrt_exposure"].sum() / 1e3, 2)
        rec["swift_first"] = mjd_to_date(sw["start_time"].min()) if len(sw) else ""
        rec["swift_last"] = mjd_to_date(sw["start_time"].max()) if len(sw) else ""
        det["swiftmastr"] = json.loads(sw.to_json(orient="records"))

        xm = masters["xmmmaster"]
        xm = xm[(xm["tid"] == tid) & (xm["time"] > 0)]
        rec["xmm_nobs"] = len(xm)
        rec["xmm_last"] = mjd_to_date(xm["time"].max()) if len(xm) else ""
        rec["xmm_statuses"] = ";".join(sorted(set(
            str(s) for s in xm.get("status", pd.Series(dtype=str))))) if len(xm) else ""
        det["xmmmaster"] = json.loads(xm.to_json(orient="records"))

        ch = masters["chanmaster"]
        ch = ch[(ch["tid"] == tid) & (ch["time"] > 0)]
        rec["chandra_nobs"] = len(ch)
        rec["chandra_last"] = mjd_to_date(ch["time"].max()) if len(ch) else ""
        rec["chandra_statuses"] = ";".join(sorted(set(
            str(s) for s in ch.get("status", pd.Series(dtype=str))))) if len(ch) else ""
        det["chanmaster"] = json.loads(ch.to_json(orient="records"))

        print(f"{name}: LSXPS query ...", flush=True)
        try:
            ls = lsxps(ra, dec)
        except Exception as e:
            ls = {"error": f"{type(e).__name__}: {e}"}
        det["lsxps"] = ls
        srcs = ls.get("sources", [])
        rec["lsxps_nsrc_30as"] = len(srcs) if isinstance(srcs, list) else -1
        rec["lsxps_last_det"] = (srcs[0].get("LastDetDate", "")
                                 if srcs else "")
        rec["lsxps_rate_band0"] = (srcs[0].get("Rate_band0", np.nan)
                                   if srcs else np.nan)
        ul = ls.get("ul")
        rec["xrt_ul_latest_date"] = ""
        rec["xrt_ul_latest_3sig_ct_s"] = np.nan
        rec["xrt_ul_deepest_3sig_ct_s"] = np.nan
        if ul == "NotObserved":
            rec["xrt_ul_state"] = "never observed"
        elif isinstance(ul, list) and ul and "SourceName" in ul[0]:
            # UL server refuses: a catalogued LSXPS source sits at the position
            rec["xrt_ul_state"] = (f"catalogued source {ul[0]['SourceName']} "
                                   f"at {ul[0].get('Distance', '?')}\"")
        elif isinstance(ul, list) and ul:
            u = pd.DataFrame(ul)
            ratecol = next((c for c in u.columns if "UpperLimit" in c), None)
            # stacked-image datasets (ObsID '1000...') carry stack-wide
            # Start/StopTime; date the coverage from individual obs only
            ind = u[~u["ObsID"].astype(str).str.startswith("1000")] \
                if "ObsID" in u.columns else u
            if ratecol:
                rec["xrt_ul_state"] = (f"{len(u)} datasets "
                                       f"({len(u) - len(ind)} stacked)")
                if len(ind) and "StopTime" in ind.columns:
                    last = ind.sort_values("StopTime").iloc[-1]
                    rec["xrt_ul_latest_date"] = mjd_to_date(last["StopTime"])
                    rec["xrt_ul_latest_3sig_ct_s"] = float(last[ratecol])
                rec["xrt_ul_deepest_3sig_ct_s"] = float(u[ratecol].min())
            else:
                rec["xrt_ul_state"] = f"{len(u)} datasets (no UL col?)"
        else:
            rec["xrt_ul_state"] = "query failed" if "error" in ls else "none"

        rows.append(rec)
        detail[name] = det
        time.sleep(2)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "m3_state_bounds.csv", index=False)
    with open(OUT / "m3_state_bounds_detail.json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1, default=str)
    print(df.to_string(index=False))
    print("wrote out/m3_state_bounds.csv + m3_state_bounds_detail.json")


if __name__ == "__main__":
    main()
