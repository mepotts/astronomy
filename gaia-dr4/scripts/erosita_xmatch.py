#!/usr/bin/env python
"""M3 task 4: cross the corr_vec-hardened class-III candidate list (v2)
against eROSITA-DE DR2 (eRASS:3 stack) -- an X-ray-detected astrometric
compact-companion candidate would be a day-one headline; zero matches is a
calibrated null.

Data (READ-ONLY, ../erosita-dr2/data/; semantics per erosita-dr2
M1-first-sweep.md):
  eRASS3_Main_v1.3.fits                  1,975,540 rows, 0.2-2.3 keV,
                                         DET_LIKE_0 >= 6, POS_ERR [arcsec]
  eRASS3_Hard_v1.2.fits                  15,980 rows, 2.3-5 keV selection
  eRASSc3_Main_GDR3_Public_*.fits.gz     NWAY probabilistic Gaia DR3
                                         counterparts (GDR3_source_id,
                                         NWAY_p_any/p_i/match_flag)
Footprint: Western Galactic hemisphere, 179.944 < l < 359.944 deg
(M1-first-sweep.md sec. 1).  DR1<->DR2 flux scale offset ~2% (ibid. sec. 2)
-- irrelevant here (all fluxes quoted from the eRASS:3 stack).

Two independent match routes:
  A. NWAY lookup: our candidate source_ids against GDR3_source_id -- the
     consortium's own probabilistic identification (handles proper motion
     and magnitude priors professionally).
  B. positional (house pattern of erosita-dr2/w2): Gaia position propagated
     to epoch 2020.5 (eRASS:3 midpoint) by pmra/pmdec; match radius
     3.44 x POS_ERR (2-D Rayleigh 99.7%), floored at 1", capped at 10";
     chance alignment calibrated by 8 shifted-position controls
     (candidates displaced +-0.5..2.0 deg in dec, same radii).

Per-match report: X-ray flux, log10(f_X/f_opt) [Maccacaro-style with
Gaia G substituted for V: log10(FX) + 0.4*G + 5.37 -- the 5.37 constant is
the Maccacaro et al. 1988 V-band constant, conventional], L_X at the NSS
parallax distance, companion-mass posterior column, EB26 verdict, notes.

Null case: in-footprint candidate count + empirical flux-limit proxy
(ML_FLUX_1 percentiles of threshold detections, DET_LIKE_0 in [6, 8)) +
the L_X limits that implies at the candidates' distances  [computed].

Output: out/erosita_class3_xmatch.csv, out/erosita_xmatch_summary.txt
Run   : .venv/Scripts/python.exe scripts/erosita_xmatch.py
"""

import os
import sys

import numpy as np
import pandas as pd
from astropy.io import fits
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERO = os.path.join(os.path.dirname(BASE), "erosita-dr2", "data")
OUT_DIR = os.path.join(BASE, "out")

L_LO, L_HI = 179.94423568, 359.94423568  # footprint (M1-first-sweep.md)
EPOCH_SHIFT_YR = 4.5                      # 2016.0 -> ~2020.5
R_MIN_AS, R_MAX_AS = 1.0, 10.0
RAYLEIGH = 3.44                           # 2-D 99.7% (house pattern)
DEC_SHIFTS = [-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0]

MACCACARO_C = 5.37  # V-band constant, Maccacaro et al. 1988; G substituted


def unit_vecs(ra_deg, dec_deg):
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    return np.column_stack([np.cos(dec) * np.cos(ra),
                            np.cos(dec) * np.sin(ra),
                            np.sin(dec)])


def match_positional(cand_ra, cand_dec, ero_ra, ero_dec, radius_as):
    """Per-eROSITA-source radius; returns (i_cand, i_ero, sep_arcsec)."""
    tree = cKDTree(unit_vecs(ero_ra, ero_dec))
    cv = unit_vecs(cand_ra, cand_dec)
    rmax = np.radians(R_MAX_AS / 3600.0)
    chord = 2.0 * np.sin(rmax / 2.0)
    pairs = tree.query_ball_point(cv, r=chord)
    ic, ie, sep = [], [], []
    for i, js in enumerate(pairs):
        for j in js:
            d = np.degrees(2.0 * np.arcsin(
                np.linalg.norm(cv[i] - tree.data[j]) / 2.0)) * 3600.0
            if d <= radius_as[j]:
                ic.append(i)
                ie.append(j)
                sep.append(d)
    return np.array(ic, int), np.array(ie, int), np.array(sep, float)


def main():
    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))
    tri = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_amrf_triage.parquet"),
                          columns=["source_id", "nss_solution_type",
                                   "pmra", "pmdec"])
    v2 = v2.merge(tri, on=["source_id", "nss_solution_type"], how="left")
    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    v2 = v2.merge(eb[["source_id", "verdict"]], on="source_id", how="left") \
           .rename(columns={"verdict": "eb26_verdict"})

    infoot = (v2["l"] > L_LO) & (v2["l"] < L_HI)
    print(f"v2 candidates: {len(v2)}; in eROSITA-DE footprint: "
          f"{int(infoot.sum())}")

    # PM-propagated positions (Gaia 2016.0 -> ~2020.5)
    cosd = np.cos(np.radians(v2["dec"].values))
    ra_p = v2["ra"].values + np.nan_to_num(v2["pmra"].values) \
        * EPOCH_SHIFT_YR / 3.6e6 / np.clip(cosd, 1e-6, None)
    dec_p = v2["dec"].values + np.nan_to_num(v2["pmdec"].values) \
        * EPOCH_SHIFT_YR / 3.6e6
    v2["ra_2020"], v2["dec_2020"] = ra_p, dec_p

    # ---- route A: NWAY GDR3 counterpart lookup ---------------------------
    print("loading NWAY GDR3 counterpart catalog (gz)...", flush=True)
    with fits.open(os.path.join(
            ERO, "eRASSc3_Main_GDR3_Public_27Jul2026.fits.gz")) as h:
        # the released file carries GDR3_source_id TWICE (columns 63 and 89,
        # NWAY block + appended Gaia block); numpy dtypes refuse duplicate
        # names.  Dedupe TTYPE in the in-memory header only (mode readonly;
        # the file in ../erosita-dr2/data/ is never written).
        hdr = h[1].header
        seen_names = set()
        for i in range(1, hdr["TFIELDS"] + 1):
            nm = hdr[f"TTYPE{i}"]
            if nm in seen_names:
                hdr[f"TTYPE{i}"] = f"{nm}_dup{i}"
            seen_names.add(nm)
        d = h[1].data
        nway = pd.DataFrame({
            "DETUID": [str(x) for x in d["DETUID"]],
            "IAUNAME": [str(x) for x in d["IAUNAME"]],
            "GDR3_source_id": np.asarray(d["GDR3_source_id"], np.int64),
            "NWAY_p_any": np.asarray(d["NWAY_p_any"], float),
            "NWAY_p_i": np.asarray(d["NWAY_p_i"], float),
            "NWAY_match_flag": np.asarray(d["NWAY_match_flag"], int),
            "NWAY_sep": np.asarray(d["NWAY_Separation_GDR3_ERO"], float),
            "DET_LIKE_0": np.asarray(d["DET_LIKE_0"], float),
            "EXT_LIKE": np.asarray(d["EXT_LIKE"], float),
            "ML_FLUX_1": np.asarray(d["ML_FLUX_1"], float),
            "ML_FLUX_ERR_1": np.asarray(d["ML_FLUX_ERR_1"], float),
            "POS_ERR": np.asarray(d["POS_ERR"], float),
            "FLAG_OPT": np.asarray(d["FLAG_OPT"], int),
            "UID_DR1": np.asarray(d["UID_DR1"], np.int64),
        })
    del d
    hitA = v2.merge(nway, left_on="source_id", right_on="GDR3_source_id",
                    how="inner")
    print(f"route A (NWAY GDR3 id lookup): {len(hitA)} counterpart rows "
          f"for {hitA['source_id'].nunique()} candidates")

    # ---- route B: positional vs eRASS3 Main ------------------------------
    print("loading eRASS3 Main (memmap)...", flush=True)
    with fits.open(os.path.join(ERO, "eRASS3_Main_v1.3.fits"),
                   memmap=True) as h:
        d = h[1].data
        ero = pd.DataFrame({
            "DETUID": [str(x) for x in d["DETUID"]],
            "IAUNAME": [str(x) for x in d["IAUNAME"]],
            "RA": np.asarray(d["RA"], float),
            "DEC": np.asarray(d["DEC"], float),
            "POS_ERR": np.asarray(d["POS_ERR"], float),
            "DET_LIKE_0": np.asarray(d["DET_LIKE_0"], float),
            "EXT_LIKE": np.asarray(d["EXT_LIKE"], float),
            "ML_FLUX_1": np.asarray(d["ML_FLUX_1"], float),
            "ML_FLUX_ERR_1": np.asarray(d["ML_FLUX_ERR_1"], float),
            "FLAG_OPT": np.asarray(d["FLAG_OPT"], int),
            "UID_DR1": np.asarray(d["UID_DR1"], np.int64),
        })
    del d
    radius = np.clip(RAYLEIGH * np.nan_to_num(ero["POS_ERR"].values,
                                              nan=R_MAX_AS),
                     R_MIN_AS, R_MAX_AS)
    ic, ie, sep = match_positional(ra_p, dec_p, ero["RA"].values,
                                   ero["DEC"].values, radius)
    print(f"route B (positional, 3.44xPOS_ERR in [1,10]\"): "
          f"{len(ic)} matches for {len(set(ic))} candidates")

    # shifted-position controls
    ctrl_counts = []
    for ds in DEC_SHIFTS:
        icc, _, _ = match_positional(ra_p, dec_p + ds, ero["RA"].values,
                                     ero["DEC"].values, radius)
        ctrl_counts.append(len(icc))
    ctrl_mean = float(np.mean(ctrl_counts))
    print(f"shifted controls ({len(DEC_SHIFTS)} x +-0.5..2.0 deg dec): "
          f"counts {ctrl_counts} -> mean {ctrl_mean:.2f}")

    # ---- route B vs Hard band -------------------------------------------
    with fits.open(os.path.join(ERO, "eRASS3_Hard_v1.2.fits"),
                   memmap=True) as h:
        d = h[1].data
        hard_ra = np.asarray(d["RA"], float)
        hard_dec = np.asarray(d["DEC"], float)
        hard_pe = np.asarray(d["POS_ERR"], float)
    rad_h = np.clip(RAYLEIGH * np.nan_to_num(hard_pe, nan=R_MAX_AS),
                    R_MIN_AS, R_MAX_AS)
    ich, ieh, seph = match_positional(ra_p, dec_p, hard_ra, hard_dec, rad_h)
    print(f"route B vs Hard: {len(ich)} matches")

    # ---- merge routes, annotate -----------------------------------------
    rows = []
    seen = set()
    for k in range(len(ic)):
        i, j = ic[k], ie[k]
        c = v2.iloc[i]
        e = ero.iloc[j]
        key = (int(c["source_id"]), e["DETUID"])
        seen.add(key)
        rows.append(make_row(c, e, sep[k], "positional"))
    for _, r in hitA.iterrows():
        key = (int(r["source_id"]), r["DETUID"])
        if key in seen:
            for q in rows:
                if (q["source_id"], q["ero_detuid"]) == key:
                    q["route"] = "positional+nway"
                    q["nway_p_any"] = r["NWAY_p_any"]
                    q["nway_p_i"] = r["NWAY_p_i"]
                    q["nway_match_flag"] = r["NWAY_match_flag"]
            continue
        c = v2[v2["source_id"] == r["source_id"]].iloc[0]
        row = make_row(c, r, r["NWAY_sep"], "nway_only")
        row["nway_p_any"] = r["NWAY_p_any"]
        row["nway_p_i"] = r["NWAY_p_i"]
        row["nway_match_flag"] = r["NWAY_match_flag"]
        rows.append(row)
    for k in range(len(ich)):
        c = v2.iloc[ich[k]]
        rows.append({"source_id": int(c["source_id"]),
                     "route": "hard_band_positional",
                     "sep_arcsec": round(float(seph[k]), 2)})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT_DIR, "erosita_class3_xmatch.csv"),
               index=False, lineterminator="\n")

    # ---- sensitivity of the null ----------------------------------------
    pt = ero[(ero["EXT_LIKE"] == 0) & (ero["DET_LIKE_0"] >= 6)
             & (ero["DET_LIKE_0"] < 8) & (ero["ML_FLUX_1"] > 0)]
    flim_med = float(np.median(pt["ML_FLUX_1"]))
    flim_10, flim_90 = (float(np.percentile(pt["ML_FLUX_1"], q))
                        for q in (10, 90))
    d_pc = 1000.0 / v2.loc[infoot, "nss_parallax"]
    lx_lim = 4.0 * np.pi * (d_pc * 3.086e18) ** 2 * flim_med
    summary = [
        f"v2 candidates {len(v2)}, in footprint {int(infoot.sum())}",
        f"route A (NWAY id lookup) matches: {hitA['source_id'].nunique()}",
        f"route B (positional) matches: {len(set(ic))} "
        f"(chance expectation from {len(DEC_SHIFTS)} shifted controls: "
        f"{ctrl_mean:.2f}, counts {ctrl_counts})",
        f"hard-band matches: {len(ich)}",
        f"empirical eRASS:3 threshold-flux proxy (point-like, "
        f"DET_LIKE_0 in [6,8), 0.2-2.3 keV): median {flim_med:.2e} "
        f"erg/s/cm2 (10-90%: {flim_10:.2e}..{flim_90:.2e}) [computed]",
        f"implied L_X limit at candidate distances (median flux limit): "
        f"median {np.median(lx_lim):.2e} erg/s, "
        f"10-90% {np.percentile(lx_lim, 10):.2e}..{np.percentile(lx_lim, 90):.2e}",
    ]
    with open(os.path.join(OUT_DIR, "erosita_xmatch_summary.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary) + "\n")
    print("\n".join(summary))
    if len(out):
        show = [c for c in ["source_id", "route", "ero_iauname",
                            "sep_arcsec", "det_like_0", "ml_flux_1",
                            "log_fx_fopt", "l_x_erg_s", "m2_min_dark_dust",
                            "p_class3_corr", "eb26_verdict", "flag_opt",
                            "nway_p_any"] if c in out.columns]
        print("\nmatches:")
        print(out[show].to_string(index=False))
    return 0


def make_row(c, e, sep_as, route):
    fx = float(e["ML_FLUX_1"])
    g = float(c["phot_g_mean_mag"])
    d_cm = 1000.0 / float(c["nss_parallax"]) * 3.086e18
    return {
        "source_id": int(c["source_id"]),
        "nss_solution_type": c["nss_solution_type"],
        "route": route,
        "ero_detuid": e["DETUID"],
        "ero_iauname": e["IAUNAME"],
        "sep_arcsec": round(float(sep_as), 2),
        "pos_err_arcsec": round(float(e["POS_ERR"]), 2),
        "det_like_0": round(float(e["DET_LIKE_0"]), 1),
        "ext_like": round(float(e["EXT_LIKE"]), 1),
        "ml_flux_1": fx,
        "ml_flux_err_1": float(e["ML_FLUX_ERR_1"]),
        "flag_opt": int(e["FLAG_OPT"]),
        "uid_dr1": int(e["UID_DR1"]),
        "log_fx_fopt": round(np.log10(fx) + 0.4 * g + MACCACARO_C, 2)
        if fx > 0 else np.nan,
        "l_x_erg_s": 4.0 * np.pi * d_cm ** 2 * fx if fx > 0 else np.nan,
        "gaia_g": g,
        "d_pc": round(1000.0 / float(c["nss_parallax"]), 1),
        "period_d": round(float(c["period"]), 2),
        "m1_dust": c["m1_dust"],
        "m2_min_dark_dust": c["m2_min_dark_dust"],
        "p_class3_corr": c["p_class3_corr"],
        "eb26_verdict": c["eb26_verdict"] if isinstance(c["eb26_verdict"],
                                                       str) else "",
        "flag_low_lat": bool(c["flag_low_lat"]),
        "nway_p_any": np.nan,
        "nway_p_i": np.nan,
        "nway_match_flag": np.nan,
    }


if __name__ == "__main__":
    sys.exit(main())
