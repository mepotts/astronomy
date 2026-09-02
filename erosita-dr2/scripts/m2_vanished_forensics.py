"""M2: full census regeneration + vanished-source forensics (paper Sect. 3.2.5).

Regenerates the FULL vanished (DR1 clean, DET_LIKE_0 >= 30, no DR2 counterpart via
UID_DR1) and new-bright lists (M1 committed only the top 100 of each), then scores
every vanished source against the DR2 release paper's confusion-dropout mechanism:

  arXiv:2607.27772 Sect. 3.2.5: bright sources missing from eRASS:3 are "typically
  located in the vicinity (~1') of other similarly bright sources and were filtered
  out during the erbox peak finding stage"; ~200 such dropouts expected catalog-wide.
  Sect. 5.3 advises manual inspection near complex regions.

Per vanished source, against the DR2 Main catalog (local FITS):
  - nn2_sep_arcsec / nn2_rate / nn2_detlike : nearest DR2 point source
  - nn2_bright_sep_arcsec : nearest DR2 source with ML_RATE_1 >= 0.5 * DR1 rate
      ("similarly bright" neighbor - the erbox dropout signature when within ~60-120")
  - next_sep_arcsec / next_extlike : nearest DR2 EXTENDED source (EXT_LIKE > 0)
  - n2_within_120 : DR2 source count within 2'
  - dr1_nn_sep_arcsec / dr1_nn_bright_sep_arcsec : same-epoch DR1 neighbors (was the
      field crowded already in eRASS1?)
  - in_dr2_any_sep : nearest DR2 source of ANY kind (incl. flagged/extended) - a
      close (<10-15") DR2 source NOT linked by UID_DR1 means the cross-walk missed
      it (split/moved centroid), not that the flux vanished.

Classification (documented in M2-vetting.md):
  ARTIFACT-CONFUSION   nn2_bright within 120" (erbox mechanism, Sect. 3.2.5)
  ARTIFACT-SPLIT/MOVED a DR2 source of any kind within 15" (cross-walk miss)
  ARTIFACT-EXTENDED    DR2 extended source within 120" (source absorbed into it)
  PLAUSIBLE-FADER      none of the above -> the flux itself is gone at DR2 depth

Output: out/m2_vanished_forensics.csv (261 rows), out/m2_new_bright_full.csv (286),
plus summary counts on stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

FLAGS = [
    "FLAG_SP_SNR", "FLAG_SP_BPS", "FLAG_SP_LGA", "FLAG_SP_GC_CONS",
    "FLAG_NO_RADEC_ERR", "FLAG_NO_CTS_ERR", "FLAG_OPT",
]


def load_fits_cols(path: Path, cols: list[str]) -> pd.DataFrame:
    with fits.open(path, memmap=True) as h:
        d = h[1].data
        out = {}
        for c in cols:
            v = d[c]
            if v.dtype.kind in ("S", "U"):
                out[c] = np.char.strip(v.astype("U32"))
            elif v.dtype.kind == "b":
                out[c] = v.astype(bool)
            else:
                out[c] = v.byteswap().view(v.dtype.newbyteorder("="))
        return pd.DataFrame(out)


def clean_mask(df: pd.DataFrame) -> pd.Series:
    m = df["EXT_LIKE"] == 0
    for f in FLAGS:
        m &= ~df[f].astype(bool)
    return m


def main() -> None:
    print("loading DR2 ...", flush=True)
    dr2 = load_fits_cols(DATA / "eRASS3_Main_v1.3.fits",
                         ["IAUNAME", "DETUID", "UID", "UID_DR1", "RA", "DEC",
                          "DET_LIKE_0", "EXT_LIKE", "ML_RATE_1", "ML_EXP_1"] + FLAGS)
    print("loading DR1 ...", flush=True)
    dr1 = load_fits_cols(DATA / "eRASS1_Main.v1.2.fits",
                         ["IAUNAME", "UID", "RA", "DEC", "POS_ERR", "DET_LIKE_0",
                          "EXT_LIKE", "ML_RATE_1", "ML_RATE_ERR_1", "ML_FLUX_1",
                          "ML_EXP_1", "MJD_MIN", "MJD_MAX"] + FLAGS)

    # ---- full vanished list (same construction as W2) -----------------------
    matched_uids = set(np.abs(dr2.loc[dr2["UID_DR1"] != 0, "UID_DR1"]).tolist())
    van = dr1[clean_mask(dr1) & (dr1["DET_LIKE_0"] >= 30)].copy()
    van = van[~van["UID"].isin(matched_uids)].reset_index(drop=True)
    print(f"full vanished list: {len(van)}")

    # ---- full new-bright list (same construction as W2) ---------------------
    nb = dr2[clean_mask(dr2) & (dr2["UID_DR1"] == 0) & (dr2["DET_LIKE_0"] >= 30)
             & (dr2["ML_RATE_1"] > 0.2)].copy()
    nb = nb.sort_values("ML_RATE_1", ascending=False).reset_index(drop=True)
    print(f"full new-bright (rate>0.2) list: {len(nb)}")
    nb[["IAUNAME", "DETUID", "RA", "DEC", "DET_LIKE_0", "ML_RATE_1", "ML_EXP_1"]].to_csv(
        OUT / "m2_new_bright_full.csv", index=False)

    # ---- neighbor structures ------------------------------------------------
    cv = SkyCoord(van["RA"].to_numpy("f8") * u.deg, van["DEC"].to_numpy("f8") * u.deg)

    dr2_all = SkyCoord(dr2["RA"].to_numpy("f8") * u.deg, dr2["DEC"].to_numpy("f8") * u.deg)
    dr2_pt = dr2[dr2["EXT_LIKE"] == 0].reset_index(drop=True)
    c2_pt = SkyCoord(dr2_pt["RA"].to_numpy("f8") * u.deg, dr2_pt["DEC"].to_numpy("f8") * u.deg)
    dr2_ext = dr2[dr2["EXT_LIKE"] > 0].reset_index(drop=True)
    c2_ext = SkyCoord(dr2_ext["RA"].to_numpy("f8") * u.deg, dr2_ext["DEC"].to_numpy("f8") * u.deg)
    dr1_pt = dr1[dr1["EXT_LIKE"] == 0].reset_index(drop=True)
    c1_pt = SkyCoord(dr1_pt["RA"].to_numpy("f8") * u.deg, dr1_pt["DEC"].to_numpy("f8") * u.deg)

    # nearest DR2 source of any kind
    i_any, d_any, _ = cv.match_to_catalog_sky(dr2_all)
    van["in_dr2_any_sep"] = d_any.arcsec
    van["in_dr2_any_name"] = dr2["IAUNAME"].to_numpy()[i_any]
    van["in_dr2_any_rate"] = dr2["ML_RATE_1"].to_numpy()[i_any]
    van["in_dr2_any_extlike"] = dr2["EXT_LIKE"].to_numpy()[i_any]
    van["in_dr2_any_detlike"] = dr2["DET_LIKE_0"].to_numpy()[i_any]

    # nearest DR2 point source (excluding a potential self-match is moot: these
    # have no DR2 counterpart by construction, but a <15" match IS the artifact)
    i_pt, d_pt, _ = cv.match_to_catalog_sky(c2_pt)
    van["nn2_sep_arcsec"] = d_pt.arcsec
    van["nn2_rate"] = dr2_pt["ML_RATE_1"].to_numpy()[i_pt]
    van["nn2_detlike"] = dr2_pt["DET_LIKE_0"].to_numpy()[i_pt]

    # nearest DR2 extended source
    if len(dr2_ext):
        i_ex, d_ex, _ = cv.match_to_catalog_sky(c2_ext)
        van["next_sep_arcsec"] = d_ex.arcsec
        van["next_extlike"] = dr2_ext["EXT_LIKE"].to_numpy()[i_ex]
        van["next_rate"] = dr2_ext["ML_RATE_1"].to_numpy()[i_ex]

    # counts within 2' and "similarly bright" neighbor within 2'
    # (search_around_sky on the point-source catalog)
    idx_v, idx_c, sep2d, _ = c2_pt.search_around_sky(cv, 120 * u.arcsec)
    n120 = np.zeros(len(van), dtype=int)
    bright_sep = np.full(len(van), np.nan)
    bright_name = np.array([""] * len(van), dtype=object)
    bright_rate = np.full(len(van), np.nan)
    v_rate = van["ML_RATE_1"].to_numpy("f8")
    for k in range(len(idx_v)):
        i = idx_v[k]
        j = idx_c[k]
        n120[i] += 1
        # eRASS1 rate vs DR2 stacked rate of the neighbor: "similarly bright"
        # = neighbor stacked rate >= half the vanished source's eRASS1 rate
        if dr2_pt["ML_RATE_1"].iat[j] >= 0.5 * v_rate[i]:
            s = sep2d[k].arcsec
            if not (bright_sep[i] <= s):
                bright_sep[i] = s
                bright_name[i] = dr2_pt["IAUNAME"].iat[j]
                bright_rate[i] = dr2_pt["ML_RATE_1"].iat[j]
    van["n2_within_120"] = n120
    van["nn2_bright_sep_arcsec"] = bright_sep
    van["nn2_bright_name"] = bright_name
    van["nn2_bright_rate"] = bright_rate

    # DR1 same-epoch neighbors (2nd-nearest = nearest other source)
    i1b, d1b, _ = cv.match_to_catalog_sky(c1_pt, nthneighbor=2)
    van["dr1_nn_sep_arcsec"] = d1b.arcsec
    van["dr1_nn_rate"] = dr1_pt["ML_RATE_1"].to_numpy()[i1b]

    # ---- classification -----------------------------------------------------
    is_split = van["in_dr2_any_sep"] <= 15.0
    is_conf = ~is_split & (van["nn2_bright_sep_arcsec"] <= 120.0)
    is_ext = ~is_split & ~is_conf & (van.get("next_sep_arcsec", pd.Series(np.inf, index=van.index)) <= 120.0)
    van["forensic_class"] = np.select(
        [is_split, is_conf, is_ext],
        ["ARTIFACT-SPLIT/MOVED", "ARTIFACT-CONFUSION", "ARTIFACT-EXTENDED"],
        default="PLAUSIBLE-FADER",
    )
    print(van["forensic_class"].value_counts().to_string())
    # likelihood regime of the plausible faders
    pf = van[van["forensic_class"] == "PLAUSIBLE-FADER"]
    print("\nplausible faders DET_LIKE_0 quartiles:",
          np.percentile(pf["DET_LIKE_0"], [25, 50, 75]).round(1))
    print("plausible faders with DET_LIKE_0 >= 100:", int((pf["DET_LIKE_0"] >= 100).sum()))

    van.sort_values("DET_LIKE_0", ascending=False).to_csv(
        OUT / "m2_vanished_forensics.csv", index=False)
    print(f"\nwrote out/m2_vanished_forensics.csv ({len(van)} rows) and "
          f"out/m2_new_bright_full.csv ({len(nb)} rows)")


if __name__ == "__main__":
    main()
