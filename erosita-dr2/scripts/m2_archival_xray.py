"""M2: archival X-ray + optical-IR context sweep for every touched candidate.

Inputs: out/m1_candidates.csv (140) + out/m2_vanished_forensics.csv (full 261
vanished list; the 20 M1 vanished rows are deduplicated by name).

Services (all anonymous; one POST per catalog, serial => polite):
  CDS X-Match  http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync  against
    - vizier:J/A+A/588/A103/cat2rxs   2RXS (ROSAT 1990-91 survey), r=40"
    - vizier:IX/71/xmmsl3c            XMM slew XMMSL3 clean (2001-2024), r=20"
    - vizier:IX/70/csc21mas           Chandra CSC 2.1 (through ~2021), r=15"
    - vizier:IX/58/2sxps              Swift-XRT 2SXPS (2005-2018), r=15"
    - vizier:II/365/catwise           CatWISE2020 W1/W2, r=10"
    - vizier:I/358/varisum            Gaia DR3 variability summary, r=10"
  HEASARC TAP  https://heasarc.gsfc.nasa.gov/xamin/vo/tap  upload join against
    - xmmssc                          4XMM serendipitous catalog, r=15"

Output: out/m2_archival_xray.csv - one row per touched source, nearest match per
catalog (name, separation, representative soft flux where the catalog offers one,
plus per-catalog notes columns). Fluxes are NOT homogenized here beyond what each
catalog publishes; the M2 doc says which band each column is.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo
import requests
from astropy.table import Table

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
XMATCH_URL = "http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync"
HEASARC_TAP = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"

# catalog, radius_arcsec, columns to keep (renamed with prefix)
XMATCH_CATS = [
    ("2rxs", "vizier:J/A+A/588/A103/cat2rxs", 40,
     {"2RXS": "id", "Cts": "cts", "ExpTime": "exptime", "HR1": "hr1"}),
    ("xmmsl3", "vizier:IX/71/xmmsl3c", 20,
     {"XMMSL3": "id", "FluxB6": "flux_02_2", "FluxB8": "flux_02_12", "RateB6": "rate_02_2"}),
    ("csc21", "vizier:IX/70/csc21mas", 15,
     {"2CXO": "id", "PFluxb": "flux_b", "PFluxs": "flux_s", "fe": "flag_e", "fv": "flag_var"}),
    ("2sxps", "vizier:IX/58/2sxps", 15,
     {"2SXPS": "id", "CR0": "rate0", "FPO0": "flux_po0", "Det": "det", "PcstS0": "pconst"}),
    ("catwise", "vizier:II/365/catwise", 10,
     {"Name": "id", "W1mproPM": "w1", "W2mproPM": "w2"}),
    ("gvar", "vizier:I/358/varisum", 10,
     {"Source": "id", "Gmagmin": "gmin", "Gmagmax": "gmax", "NG": "ng"}),
    ("gclass", "vizier:I/358/vclassre", 10,
     {"Source": "id", "Class": "class", "ClassSc": "score"}),
]


def build_touched() -> pd.DataFrame:
    c = pd.read_csv(OUT / "m1_candidates.csv")
    c = c[["name", "RA", "DEC", "cand_set"]].copy()
    v = pd.read_csv(OUT / "m2_vanished_forensics.csv")
    v = v[["IAUNAME", "RA", "DEC"]].rename(columns={"IAUNAME": "name"})
    v["cand_set"] = "vanished_full"
    t = pd.concat([c, v], ignore_index=True)
    t = t.drop_duplicates(subset="name", keep="first").reset_index(drop=True)
    t["tid"] = np.arange(len(t)).astype("int32")
    return t


def xmatch_one(t: pd.DataFrame, tag: str, cat: str, radius: float,
               keep: dict[str, str]) -> pd.DataFrame:
    csv_buf = t[["tid", "RA", "DEC"]].to_csv(index=False)
    resp = requests.post(
        XMATCH_URL,
        data={"request": "xmatch", "distMaxArcsec": radius, "RESPONSEFORMAT": "csv",
              "colRA1": "RA", "colDec1": "DEC", "cat2": cat},
        files={"cat1": ("cands.csv", csv_buf)},
        timeout=600,
    )
    resp.raise_for_status()
    g = pd.read_csv(io.StringIO(resp.text), low_memory=False)
    if not len(g):
        return pd.DataFrame(columns=["tid"])
    n = g.groupby("tid").size().rename(f"{tag}_n")
    g = g.sort_values("angDist").groupby("tid", as_index=False).first()
    cols = {"tid": "tid", "angDist": f"{tag}_sep"}
    cols.update({k: f"{tag}_{v}" for k, v in keep.items() if k in g.columns})
    missing = [k for k in keep if k not in g.columns]
    if missing:
        print(f"  [{tag}] missing expected columns: {missing}; have e.g. "
              f"{[c for c in g.columns[:40]]}")
    out = g[list(cols)].rename(columns=cols).merge(n, on="tid", how="left")
    return out


def xmm_heasarc(t: pd.DataFrame) -> pd.DataFrame:
    svc = pyvo.dal.TAPService(HEASARC_TAP)
    up = Table({"tid": t["tid"].to_numpy("int32"),
                "ra": t["RA"].to_numpy("f8"), "dec": t["DEC"].to_numpy("f8")})
    q = """SELECT c.tid, x.name, x.ra, x.dec, x.ep_flux, x.ep_flux_error,
       x.ep_2_flux, x.ep_3_flux, x.n_obs,
       x.error_radius
FROM TAP_UPLOAD.pos AS c JOIN xmmssc AS x
ON 1=CONTAINS(POINT('ICRS', x.ra, x.dec), CIRCLE('ICRS', c.ra, c.dec, 15.0/3600.0))"""
    res = svc.search(q, uploads={"pos": up}).to_table().to_pandas()
    # HEASARC prefixes output columns with the table alias: c_tid, x_name, ...
    res.columns = [c.lower().split("_", 1)[1] if c.lower().startswith(("c_", "x_"))
                   else c.lower() for c in res.columns]
    if not len(res):
        return pd.DataFrame(columns=["tid"])
    # separation + nearest
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    tt = t.set_index("tid")
    c1 = SkyCoord(tt.loc[res["tid"], "RA"].to_numpy("f8") * u.deg,
                  tt.loc[res["tid"], "DEC"].to_numpy("f8") * u.deg)
    c2 = SkyCoord(res["ra"].to_numpy("f8") * u.deg, res["dec"].to_numpy("f8") * u.deg)
    res["sep"] = c1.separation(c2).arcsec
    n = res.groupby("tid").size().rename("xmmssc_n")
    res = res.sort_values("sep").groupby("tid", as_index=False).first()
    res["ep_soft_flux"] = res["ep_2_flux"] + res["ep_3_flux"]  # 0.5-2 keV
    # NOTE: HEASARC xmmssc currently serves 5XMM-era source names (checked
    # 2026-08-14: returned names begin "5XMM J..."), i.e. the same catalog
    # generation the DR2 paper compares against.
    out = res[["tid", "name", "sep", "ep_flux", "ep_flux_error", "ep_soft_flux",
               "n_obs"]].rename(columns={
        "name": "xmmssc_id", "sep": "xmmssc_sep", "ep_flux": "xmmssc_flux_02_12",
        "ep_flux_error": "xmmssc_flux_err", "ep_soft_flux": "xmmssc_flux_05_2",
        "n_obs": "xmmssc_nobs"})
    return out.merge(n, on="tid", how="left")


def main() -> None:
    import sys
    t = build_touched()
    print(f"touched sources: {len(t)}")
    if "xmm-only" in sys.argv:
        # merge the 4XMM/5XMM join into the already-written CSV (X-Match part done)
        merged = pd.read_csv(OUT / "m2_archival_xray.csv")
        merged = merged[[c for c in merged.columns
                         if not c.startswith(("4xmm", "xmmssc"))]]
        res = xmm_heasarc(t)
        print(f"  matched {len(res)} sources")
        merged = merged.merge(res, on="tid", how="left")
        merged.to_csv(OUT / "m2_archival_xray.csv", index=False)
        print("updated out/m2_archival_xray.csv with 4XMM/5XMM columns")
        return
    merged = t.copy()
    for tag, cat, radius, keep in XMATCH_CATS:
        print(f"xmatch {tag} ({cat}, r={radius}\") ...", flush=True)
        try:
            res = xmatch_one(t, tag, cat, radius, keep)
            print(f"  matched {len(res)} sources")
        except Exception as e:
            print(f"  FAILED: {type(e).__name__} {e}")
            res = pd.DataFrame(columns=["tid"])
        merged = merged.merge(res, on="tid", how="left")
        time.sleep(2)
    print("heasarc 4xmm upload join ...", flush=True)
    try:
        res = xmm_heasarc(t)
        print(f"  matched {len(res)} sources")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__} {e}")
        res = pd.DataFrame(columns=["tid"])
    merged = merged.merge(res, on="tid", how="left")
    merged.to_csv(OUT / "m2_archival_xray.csv", index=False)
    have_prior = merged[[c for c in merged.columns
                         if c.endswith("_sep") and not c.startswith(("catwise", "gvar"))]]
    n_prior = (have_prior.notna().any(axis=1)).sum()
    print(f"wrote out/m2_archival_xray.csv; {n_prior}/{len(merged)} touched sources "
          f"have >=1 prior X-ray catalog entry")


if __name__ == "__main__":
    main()
