"""M3: J0944 decision package, part 1 - everything the LOCAL catalogs know.

For 3eRASS J094452.8-711152 (M2 shortlist #1, GENUINELY-UNEXPLAINED) extract:
  1. the full DR2 Main row (all 250 columns, eRASS3_Main_v1.3.fits),
  2. the full DR2 Hard row (all 111 columns, eRASS3_Hard_v1.2.fits),
  3. the full DR1 (eRASS1) row resolved via UID_DR1 (incl. MJD/MJD_MIN/MJD_MAX -
     DR2 ships no epoch columns, so DR1 carries the only public timestamps),
  4. neighbour context from both catalogs (riser-side artifact checks):
     - all DR2 Main sources within 5 arcmin (rates, likelihoods, EXT_LIKE, flags);
     - nearest extended DR2 source within 30 arcmin;
     - all DR1 sources within 5 arcmin + which of them lack a DR2 counterpart
       (merge test: could a vanished bright DR1 neighbour have been re-assigned
       to this DR2 detection?);
     - any OTHER DR2 source sharing |UID_DR1| (crosswalk duplicate / split test);
     - any second DR2 source within 60 arcsec (tile-edge duplicate test).
  5. sub-band spectral summary: P1-P9 rates -> crude hardness ratios with errors.

Output: out/j0944_rows.json (full rows + context, JSON) and an ASCII summary to
stdout. Band definitions (data model
https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.html):
1: 0.2-2.3 | P1: 0.2-0.5 | P2: 0.5-1.0 | P3: 1.0-2.0 | P4: 2.0-5.0 | P5: 5.0-8.0
| P6: 4.0-10.0 | P7: 5.1-6.1 | P8: 6.2-7.1 | P9: 7.2-8.2 keV.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

TARGET = "3eRASS J094452.8-711152"
RA, DEC = 146.22033015318507, -71.19802286286726


def native(v):
    """FITS scalar -> JSON-safe python scalar."""
    if isinstance(v, (bytes, np.bytes_)):
        return v.decode().strip()
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        f = float(v)
        return None if np.isnan(f) else f
    return str(v).strip()


def row_to_dict(rec, i) -> dict:
    return {n: native(rec[n][i]) for n in rec.columns.names}


def cat_arrays(d, cols):
    out = {}
    for c in cols:
        v = d[c]
        if v.dtype.kind in ("S", "U"):
            out[c] = np.char.strip(v.astype("U32"))
        else:
            out[c] = v.byteswap().view(v.dtype.newbyteorder("="))
    return out


def main() -> None:
    res: dict = {"target": TARGET, "ra": RA, "dec": DEC}

    # ---- DR2 Main ----------------------------------------------------------
    with fits.open(DATA / "eRASS3_Main_v1.3.fits") as h:
        d = h[1].data
        names = np.char.strip(d["IAUNAME"].astype("U32"))
        idx = np.where(names == TARGET)[0]
        assert len(idx) == 1, f"expected 1 Main row, got {len(idx)}"
        i = int(idx[0])
        res["dr2_main_row"] = row_to_dict(d, i)
        uid_dr1 = int(d["UID_DR1"][i])
        uid_main = int(d["UID"][i])

        # neighbour context needs a handful of arrays over the whole catalog
        a = cat_arrays(d, ["IAUNAME", "RA", "DEC", "DET_LIKE_0", "ML_RATE_1",
                           "EXT_LIKE", "UID_DR1", "UID"])
    cc = SkyCoord(RA * u.deg, DEC * u.deg)
    call = SkyCoord(a["RA"] * u.deg, a["DEC"] * u.deg)
    sep = cc.separation(call).arcsec

    near = np.where((sep < 300) & (sep > 0.5))[0]  # 5 arcmin, excl. self
    near = near[np.argsort(sep[near])]
    res["dr2_neighbors_5arcmin"] = [
        {"name": str(a["IAUNAME"][j]), "sep_arcsec": round(float(sep[j]), 2),
         "det_like_0": float(a["DET_LIKE_0"][j]),
         "ml_rate_1": float(a["ML_RATE_1"][j]),
         "ext_like": float(a["EXT_LIKE"][j])} for j in near]

    ext = np.where((a["EXT_LIKE"] > 0) & (sep < 1800))[0]
    if len(ext):
        j = ext[np.argmin(sep[ext])]
        res["nearest_dr2_extended_30arcmin"] = {
            "name": str(a["IAUNAME"][j]), "sep_arcsec": round(float(sep[j]), 1),
            "ext_like": float(a["EXT_LIKE"][j]),
            "det_like_0": float(a["DET_LIKE_0"][j])}
    else:
        res["nearest_dr2_extended_30arcmin"] = None

    # split/duplicate tests
    dup = np.where((a["UID_DR1"] != 0)
                   & (np.abs(a["UID_DR1"]) == abs(uid_dr1))
                   & (a["UID"] != uid_main))[0]
    res["other_dr2_sharing_uid_dr1"] = [str(a["IAUNAME"][j]) for j in dup]
    res["second_dr2_within_60arcsec"] = [
        {"name": str(a["IAUNAME"][j]), "sep_arcsec": round(float(sep[j]), 2)}
        for j in near if sep[j] <= 60]

    del a, call, sep

    # ---- DR2 Hard ----------------------------------------------------------
    with fits.open(DATA / "eRASS3_Hard_v1.2.fits") as h:
        d = h[1].data
        names = np.char.strip(d["IAUNAME"].astype("U32"))
        idx = np.where(names == TARGET)[0]
        assert len(idx) == 1, f"expected 1 Hard row, got {len(idx)}"
        res["dr2_hard_row"] = row_to_dict(d, int(idx[0]))

    # ---- DR1 (eRASS1) ------------------------------------------------------
    with fits.open(DATA / "eRASS1_Main.v1.2.fits") as h:
        d = h[1].data
        uid = d["UID"].byteswap().view(d["UID"].dtype.newbyteorder("="))
        idx = np.where(uid == abs(uid_dr1))[0]
        assert len(idx) == 1, f"expected 1 DR1 row, got {len(idx)}"
        i = int(idx[0])
        res["dr1_row"] = row_to_dict(d, i)
        res["uid_dr1_link"] = {"uid_dr1": uid_dr1,
                               "strong": uid_dr1 > 0,
                               "dr1_iauname": res["dr1_row"]["IAUNAME"]}
        a = cat_arrays(d, ["IAUNAME", "RA", "DEC", "DET_LIKE_0", "ML_RATE_1",
                           "EXT_LIKE", "UID"])
    call = SkyCoord(a["RA"] * u.deg, a["DEC"] * u.deg)
    sep = cc.separation(call).arcsec
    dr1sep = float(sep[i])
    near1 = np.where(sep < 300)[0]
    near1 = near1[np.argsort(sep[near1])]

    # which DR1 neighbours have a DR2 counterpart? (merge test)
    with fits.open(DATA / "eRASS3_Main_v1.3.fits") as h:
        u3 = h[1].data["UID_DR1"]
        u3 = np.abs(u3.byteswap().view(u3.dtype.newbyteorder("=")))
        claimed = set(int(x) for x in u3[u3 != 0])
    res["dr1_neighbors_5arcmin"] = [
        {"name": str(a["IAUNAME"][j]), "sep_arcsec": round(float(sep[j]), 2),
         "det_like_0": float(a["DET_LIKE_0"][j]),
         "ml_rate_1": float(a["ML_RATE_1"][j]),
         "ext_like": float(a["EXT_LIKE"][j]),
         "uid": int(a["UID"][j]),
         "has_dr2_counterpart": int(a["UID"][j]) in claimed,
         "is_target_dr1_row": bool(j == i)} for j in near1]
    res["dr1_separation_from_dr2_position_arcsec"] = round(dr1sep, 2)

    # ---- sub-band spectral summary (DR2 Main row) --------------------------
    m = res["dr2_main_row"]
    bands = {"P1": "0.2-0.5", "P2": "0.5-1.0", "P3": "1.0-2.0", "P4": "2.0-5.0",
             "P5": "5.0-8.0", "P6": "4.0-10.0", "P7": "5.1-6.1", "P8": "6.2-7.1",
             "P9": "7.2-8.2"}
    spec = {}
    for p, rng in bands.items():
        spec[p] = {"keV": rng,
                   "det_like": m[f"DET_LIKE_{p}"],
                   "rate": m[f"ML_RATE_{p}"], "rate_err": m[f"ML_RATE_ERR_{p}"],
                   "flux": m[f"ML_FLUX_{p}"], "flux_err": m[f"ML_FLUX_ERR_{p}"]}
    res["dr2_subband_spectrum"] = spec

    def hr(ra_, ea, rb, eb):
        if None in (ra_, ea, rb, eb) or (ra_ + rb) <= 0:
            return None, None
        h_ = (rb - ra_) / (ra_ + rb)
        e = 2.0 * np.sqrt((rb * ea) ** 2 + (ra_ * eb) ** 2) / (ra_ + rb) ** 2
        return round(float(h_), 3), round(float(e), 3)

    # soft = P2+P3 (0.5-2.0), hard = P4 (2.0-5.0); plus P1 vs P2+P3 absorption HR
    s_r = (spec["P2"]["rate"] or 0) + (spec["P3"]["rate"] or 0)
    s_e = float(np.hypot(spec["P2"]["rate_err"] or 0, spec["P3"]["rate_err"] or 0))
    hr1, hr1e = hr(spec["P1"]["rate"], spec["P1"]["rate_err"], s_r, s_e)
    hr2, hr2e = hr(s_r, s_e, spec["P4"]["rate"], spec["P4"]["rate_err"])
    res["hardness"] = {
        "HR_P1_vs_P23 (0.2-0.5 vs 0.5-2.0)": {"hr": hr1, "err": hr1e},
        "HR_P23_vs_P4 (0.5-2.0 vs 2.0-5.0)": {"hr": hr2, "err": hr2e}}

    OUT.mkdir(exist_ok=True)
    with open(OUT / "j0944_rows.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)

    # ---- ASCII summary -----------------------------------------------------
    print(f"target {TARGET}  UID_DR1={uid_dr1} (strong={uid_dr1 > 0})")
    print(f"DR2 Main: DET_LIKE_0={m['DET_LIKE_0']:.1f} rate={m['ML_RATE_1']:.4f}"
          f" flux={m['ML_FLUX_1']:.3e} POS_ERR={m['POS_ERR']:.2f}\"")
    print(f"  flags: SNR={m['FLAG_SP_SNR']} BPS={m['FLAG_SP_BPS']}"
          f" SCL={m['FLAG_SP_SCL']} LGA={m['FLAG_SP_LGA']} GC={m['FLAG_SP_GC_CONS']}"
          f" OPT={m['FLAG_OPT']} EXT_LIKE={m['EXT_LIKE']}")
    hh = res["dr2_hard_row"]
    print(f"DR2 Hard: DET_LIKE_3={hh['DET_LIKE_3']:.1f} rate3={hh['ML_RATE_3']:.4f}"
          f" flux3={hh['ML_FLUX_3']:.3e} (2.3-5 keV)")
    d1 = res["dr1_row"]
    print(f"DR1: {d1['IAUNAME']} DET_LIKE={d1['DET_LIKE_0']:.1f}"
          f" rate={d1['ML_RATE_1']:.4f} flux={d1['ML_FLUX_1']:.3e}"
          f" sep={dr1sep:.2f}\" MJD={d1['MJD']:.1f} [{d1['MJD_MIN']:.1f}"
          f"-{d1['MJD_MAX']:.1f}]")
    print(f"DR2 neighbors <5': {len(res['dr2_neighbors_5arcmin'])};"
          f" within 60\": {len(res['second_dr2_within_60arcsec'])};"
          f" sharing UID_DR1: {len(res['other_dr2_sharing_uid_dr1'])}")
    print(f"DR1 neighbors <5' (excl. target): "
          f"{len(res['dr1_neighbors_5arcmin']) - 1}")
    for nb in res["dr1_neighbors_5arcmin"]:
        if not nb["is_target_dr1_row"] and not nb["has_dr2_counterpart"]:
            print(f"  DR1 neighbor WITHOUT DR2 counterpart: {nb}")
    print(f"nearest extended DR2 <30': {res['nearest_dr2_extended_30arcmin']}")
    print("sub-band detections (DET_LIKE >= 6):")
    for p, s in spec.items():
        if s["det_like"] is not None and s["det_like"] >= 6:
            print(f"  {p} ({s['keV']} keV): DET_LIKE={s['det_like']:.1f}"
                  f" rate={s['rate']:.4f}+-{s['rate_err']:.4f}")
    print(f"hardness: {res['hardness']}")
    print("wrote out/j0944_rows.json")


if __name__ == "__main__":
    main()
