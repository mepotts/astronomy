"""W3 spot cross-match: top W2 variables vs Gaia DR3 and SIMBAD.

Inputs:  out/w2_ranked_variables.csv (top 100 by rank_amp),
         out/w2_vanished.csv (top 20), out/w2_new_bright.csv (top 20).
Services (both anonymous, one call each; polite):
  - CDS X-Match  http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync
      vs vizier:I/355/gaiadr3 (Gaia DR3 main source catalog), r = 10 arcsec
  - SIMBAD TAP   https://simbad.cds.unistra.fr/simbad/sim-tap
      upload join, r = 15 arcsec (X-ray positions; transient IDs)

Output: out/m1_candidates.csv (committed, < 1 MB).
First-guess class logic (documented in M1 doc):
  1. SIMBAD otype when present (nearest object within 15").
  2. else Gaia counterpart with significant parallax (plx/err >= 3) or proper
     motion (pm/err >= 5)  -> "Galactic-star/CV?" (+ red-dwarf note if BP-RP > 2
     and M_G > 8).
  3. else Gaia counterpart without astrometric significance -> "optical-faint?".
  4. else -> "no-Gaia (extragalactic AGN/TDE? or obscured/compact Galactic)".
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo
import requests
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

XMATCH_URL = "http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync"
SIMBAD_TAP = "https://simbad.cds.unistra.fr/simbad/sim-tap"


def build_candidates() -> pd.DataFrame:
    ranked = pd.read_csv(OUT / "w2_ranked_variables.csv").head(100).copy()
    ranked["cand_set"] = "pair"
    van = pd.read_csv(OUT / "w2_vanished.csv").head(20).copy()
    van["cand_set"] = "vanished"
    van = van.rename(columns={"ML_RATE_1": "ML_RATE_1_D1", "ML_RATE_ERR_1": "ML_RATE_ERR_1_D1",
                              "ML_FLUX_1": "ML_FLUX_1_D1", "ML_EXP_1": "ML_EXP_1_D1",
                              "DET_LIKE_0": "DET_LIKE_0_D1", "IAUNAME": "IAUNAME_D1",
                              "MJD_MIN": "MJD_MIN_D1", "MJD_MAX": "MJD_MAX_D1"})
    nb = pd.read_csv(OUT / "w2_new_bright.csv").head(20).copy()
    nb["cand_set"] = "new_bright"
    cands = pd.concat([ranked, van, nb], ignore_index=True, sort=False)
    cands["cand_id"] = np.arange(len(cands))
    # display name: DR2 IAUNAME for pair/new_bright, DR1 IAUNAME for vanished
    cands["name"] = cands["IAUNAME"].fillna(cands.get("IAUNAME_D1"))
    gal = SkyCoord(cands["RA"].to_numpy("f8") * u.deg,
                   cands["DEC"].to_numpy("f8") * u.deg, frame="icrs").galactic
    cands["l_deg"] = gal.l.deg
    cands["b_deg"] = gal.b.deg
    return cands


def xmatch_gaia(cands: pd.DataFrame) -> pd.DataFrame:
    csv_buf = cands[["cand_id", "RA", "DEC"]].to_csv(index=False)
    resp = requests.post(
        XMATCH_URL,
        data={
            "request": "xmatch",
            "distMaxArcsec": 10,
            "RESPONSEFORMAT": "csv",
            "colRA1": "RA",
            "colDec1": "DEC",
            "cat2": "vizier:I/355/gaiadr3",
        },
        files={"cat1": ("cands.csv", csv_buf)},
        timeout=300,
    )
    resp.raise_for_status()
    g = pd.read_csv(io.StringIO(resp.text))
    if not len(g):
        return pd.DataFrame(columns=["cand_id"])
    g = g.sort_values("angDist").groupby("cand_id", as_index=False).first()
    keep = {
        "cand_id": "cand_id", "angDist": "gaia_sep_arcsec", "Source": "gaia_source_id",
        "Gmag": "gaia_G", "BP-RP": "gaia_bp_rp", "Plx": "gaia_plx", "e_Plx": "gaia_plx_err",
        "pmRA": "gaia_pmra", "e_pmRA": "gaia_pmra_err", "pmDE": "gaia_pmdec",
        "e_pmDE": "gaia_pmdec_err",
    }
    have = {k: v for k, v in keep.items() if k in g.columns}
    return g[list(have)].rename(columns=have)


def simbad_lookup(cands: pd.DataFrame) -> pd.DataFrame:
    up = cands[["cand_id", "RA", "DEC"]].copy()
    up["cand_id"] = up["cand_id"].astype("int32")  # Windows C-long: avoid int64 VOTable nulls
    tab = Table.from_pandas(up)
    svc = pyvo.dal.TAPService(SIMBAD_TAP)
    q = """
    SELECT c.cand_id, b.main_id, b.otype,
           DISTANCE(POINT('ICRS', b.ra, b.dec), POINT('ICRS', c.RA, c.DEC)) * 3600.0
             AS simbad_sep_arcsec
    FROM TAP_UPLOAD.cands AS c
    JOIN basic AS b
      ON 1 = CONTAINS(POINT('ICRS', b.ra, b.dec), CIRCLE('ICRS', c.RA, c.DEC, 15.0/3600.0))
    """
    res = svc.search(q, uploads={"cands": tab}).to_table().to_pandas()
    if not len(res):
        return pd.DataFrame(columns=["cand_id", "simbad_main_id", "simbad_otype",
                                     "simbad_sep_arcsec"])
    res = res.sort_values("simbad_sep_arcsec").groupby("cand_id", as_index=False).first()
    return res.rename(columns={"main_id": "simbad_main_id", "otype": "simbad_otype"})


def classify(row: pd.Series) -> tuple[str, str]:
    caveats = []
    if row.get("containment_violated") is True:
        caveats.append("containment-violated (030 flare-filter/pileup suspect)")
    if row.get("subfloor") is True:
        caveats.append("stacked ratio below switch-off floor (mild containment tension)")
    if row.get("cand_set") == "vanished":
        caveats.append("no DR2 entry: fade OR DR2 confusion dropout (arXiv:2607.27772 S3.2.5)")
    if row.get("cand_set") == "new_bright":
        caveats.append("rise bound uses approx eRASS1 sensitivity (empirical 5th pct)")
    if isinstance(row.get("simbad_otype"), str) and row["simbad_otype"].strip():
        return f"SIMBAD:{row['simbad_otype']}", "; ".join(caveats)
    plx_sig = (row.get("gaia_plx") or 0) / row["gaia_plx_err"] if pd.notna(row.get("gaia_plx_err")) and row.get("gaia_plx_err") else 0
    pm = np.hypot(row.get("gaia_pmra") or 0, row.get("gaia_pmdec") or 0)
    pm_err = np.hypot(row.get("gaia_pmra_err") or 0, row.get("gaia_pmdec_err") or 0)
    pm_sig = pm / pm_err if pm_err else 0
    if pd.notna(row.get("gaia_source_id")):
        if plx_sig >= 3 or pm_sig >= 5:
            note = ""
            if plx_sig >= 3 and pd.notna(row.get("gaia_bp_rp")) and pd.notna(row.get("gaia_G")):
                mg = row["gaia_G"] + 5 * np.log10(max(row["gaia_plx"], 1e-3) / 100.0)
                if row["gaia_bp_rp"] > 2 and mg > 8:
                    note = " (red-dwarf locus: flare star?)"
            return f"Galactic-star/CV?{note}", "; ".join(caveats)
        return "optical-faint?", "; ".join(caveats)
    return "no-Gaia (AGN/TDE? obscured?)", "; ".join(caveats)


def main() -> None:
    cands = build_candidates()
    print(f"candidates: {len(cands)} "
          f"({(cands['cand_set'] == 'pair').sum()} pair / "
          f"{(cands['cand_set'] == 'vanished').sum()} vanished / "
          f"{(cands['cand_set'] == 'new_bright').sum()} new_bright)")
    gaia = xmatch_gaia(cands)
    print(f"gaia matches (<=10 arcsec): {len(gaia)}")
    simbad = simbad_lookup(cands)
    print(f"simbad matches (<=15 arcsec): {len(simbad)}")

    m = cands.merge(gaia, on="cand_id", how="left").merge(simbad, on="cand_id", how="left")
    cls = m.apply(classify, axis=1)
    m["first_guess_class"] = [c[0] for c in cls]
    m["caveats"] = [c[1] for c in cls]

    cols = [
        "cand_set", "name", "RA", "DEC", "POS_ERR", "l_deg", "b_deg",
        "match_type", "direction", "DET_LIKE_0", "DET_LIKE_0_D1",
        "ML_RATE_1", "ML_RATE_1_D1", "ML_FLUX_1", "ML_FLUX_1_D1",
        "R", "epoch_ratio", "amp_cons", "epoch_amp_cons", "rank_amp", "z_var",
        "approx_erass1_rate_lim", "implied_min_rise",
        "gaia_source_id", "gaia_sep_arcsec", "gaia_G", "gaia_bp_rp",
        "gaia_plx", "gaia_plx_err", "gaia_pmra", "gaia_pmdec",
        "simbad_main_id", "simbad_otype", "simbad_sep_arcsec",
        "first_guess_class", "caveats",
    ]
    cols = [c for c in cols if c in m.columns]
    m[cols].to_csv(OUT / "m1_candidates.csv", index=False)
    print("class counts:")
    print(m.groupby(["cand_set", "first_guess_class"]).size().to_string())
    size = (OUT / "m1_candidates.csv").stat().st_size
    print(f"wrote out/m1_candidates.csv ({size:,} bytes)")


if __name__ == "__main__":
    main()
