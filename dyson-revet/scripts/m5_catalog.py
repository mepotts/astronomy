"""M5: the finished verdict table over all 1,545 survivors, and the
high-latitude extreme-IR-excess catalogue as a standalone product.

Two deliverables, one pass over the same table:

  1. THE VERDICT TABLE (M5 Sec 2).  All 1,545 full-sky pre-visual survivors,
     with M3 PR-3's four applicable gates, the M5 nebular flags, and the M4
     Sec 5 caveat carried per row: V5 is retired (PR-5), STILL-CLEAN requires
     a valid centroid, so NO OBJECT CAN REACH STILL-CLEAN.  What the surviving
     set is, is stated in those words: objects with no *detectable*
     contamination evidence given a method with a known blind spot.

  2. THE HIGH-LATITUDE CATALOGUE (M5 Sec 4).  |b| > 30 deg, with the
     |b| > 50 deg subsample flagged as the calibrated core (M4 Sec 4.3
     measured 1.05x [0.94-1.17] there against 1.36x [1.24-1.49] at 30-50 deg).
     Every survivor in the footprint, INCLUDING the ones this project's own
     gates convict, each carrying its verdict and the evidence behind it.

Run:  python scripts/m5_catalog.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
CAT = ROOT / "catalog"
CAT.mkdir(exist_ok=True)
CELLS = ROOT / "data" / "w4" / "aip" / "cells"

from m5_nebular import galactic, ecliptic_lat, SKY_DEG2     # noqa: E402
from m5_funnel_nebular import BANDS, band_area, PAPER_RATE  # noqa: E402

TAG = "m4_g0.1"
HIGHLAT = 30.0
CORE = 50.0
# Suazo et al. 2024 Sec 3.1's own faint red-galaxy density, 15000 sr^-1
RHO_REDGAL_DEG2 = 15000.0 / (180.0 / np.pi) ** 2


def load() -> pd.DataFrame:
    """The vetted survivor table, plus the M5 nebular flags, plus 2MASS and
    the photometric errors from the harvest (which the funnel's own output
    drops)."""
    sv = pd.read_csv(OUT / f"m3_survivor_table_{TAG}.csv")
    nb = pd.read_csv(OUT / "m5_nebular_flags_previsual.csv")
    assert len(sv) == len(nb)
    assert (sv["source_id"].to_numpy() == nb["source_id"].to_numpy()).all(), \
        "survivor table and nebular flags are not row-aligned"
    keep = ["n1_flag", "n1_ncat", "n1_cat", "n1_name", "n1_sep_as", "n1_r_as",
            "n2_score", "n2_flag", "nebular_flag", "w3sky", "w4sky",
            "w3conf", "w4conf", "glat"]   # ecl_lat is already in the vetted table
    d = pd.concat([sv.reset_index(drop=True), nb[keep].reset_index(drop=True)],
                  axis=1)
    l, _ = galactic(d["ra"].to_numpy(), d["dec"].to_numpy())
    d["glon"] = l
    # 2MASS + photometric errors from the harvest cells
    cols = ["datalinkID", "w1mpro_error", "w2mpro_error", "w3mpro_error",
            "w4mpro_error", "tmass_designation", "j_m", "h_m", "ks_m",
            "phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag",
            "pmra", "pmdec", "parallax", "parallax_error",
            "classprob_dsc_combmod_star"]
    want = set(d["source_id"].astype("int64"))
    parts = []
    for p in sorted(CELLS.glob("*.csv")):
        c = pd.read_csv(p, usecols=cols)
        c = c[c["datalinkID"].isin(want)]
        if len(c):
            parts.append(c)
    extra = (pd.concat(parts, ignore_index=True)
             .rename(columns={"datalinkID": "source_id"})
             .drop_duplicates("source_id"))
    print(f"  attached harvest photometry for {len(extra):,} of {len(d):,}")
    return d.merge(extra, on="source_id", how="left")


def main() -> None:
    d = load()
    d["ab"] = np.abs(d["glat"])
    n = len(d)

    # ------------------------------------------------- 1. the verdict table
    print(f"\n== THE VERDICT TABLE: all {n:,} full-sky pre-visual survivors ==")
    vc = d["verdict"].value_counts()
    for k in ("CONTAMINATION-CONSISTENT", "INDETERMINATE", "SUB-THRESHOLD",
              "STILL-CLEAN"):
        print(f"  {k:28s} {int(vc.get(k, 0)):5,d}  "
              f"({100 * vc.get(k, 0) / n:5.1f}%)")
    print("  STILL-CLEAN is 0 BY CONSTRUCTION, not by measurement: it requires "
          "a valid\n  centroid and V5 is retired (M5 PR-5, M4 Sec 5.3).")

    print("\n  verdict x Galactic latitude:")
    hdr = ["|b|", "n"] + list(vc.index) + ["nebular"]
    print("   " + "".join(f"{h:>26s}" if h in vc.index else f"{h:>10s}"
                          for h in hdr))
    lat_rows = []
    for lo, hi in BANDS:
        s = d[(d["ab"] >= lo) & (d["ab"] < hi)]
        row = {"band": f"{lo}-{hi}", "n": len(s)}
        line = f"   {lo:3d}-{hi:<4d}{len(s):>7d}"
        for k in vc.index:
            c = int((s["verdict"] == k).sum())
            row[k] = c
            line += f"{c:>20d} ({100 * c / max(len(s), 1):4.1f}%)"
        row["nebular"] = int(s["nebular_flag"].sum())
        line += f"{int(s['nebular_flag'].sum()):>10d}"
        print(line)
        lat_rows.append(row)

    print("\n  verdict x nebular flag (the two axes are independent by "
          "construction --\n  the nebular stage looks at the FIELD, the "
          "verdict gates look at the SOURCE):")
    ct = pd.crosstab(d["verdict"], d["nebular_flag"])
    print(ct.to_string())

    # what the surviving set actually is
    surv = d[d["verdict"] == "INDETERMINATE"]
    surv_neb = surv[~surv["nebular_flag"]]
    print(f"\n  The surviving set: {len(surv):,} INDETERMINATE, of which "
          f"{len(surv_neb):,} also survive the\n  nebular stage. These are "
          f"objects with NO DETECTABLE CONTAMINATION EVIDENCE given a\n  "
          f"method with a known blind spot (M4 Sec 5.3: at a 1\" floor "
          f"~10% and at a 2\"\n  floor ~40% of chance-aligned contaminants "
          f"are invisible at any brightness).\n  Not one of them is a "
          f"candidate for anything, and none is Matthew-gated.")

    d.to_csv(OUT / f"m5_verdict_table_{TAG}.csv", index=False)

    # ------------------------------------------ 2. the high-latitude catalog
    hl = d[d["ab"] >= HIGHLAT].copy().reset_index(drop=True)
    hl["b_band"] = np.where(hl["ab"] >= CORE, "core_b50", "outer_b30_50")
    print(f"\n== THE HIGH-LATITUDE CATALOGUE: |b| > {HIGHLAT:.0f} deg ==")
    print(f"  {len(hl):,} objects; calibrated core |b| > {CORE:.0f} deg: "
          f"{int((hl['b_band'] == 'core_b50').sum()):,}")

    # per-object flags, spelled out rather than left as raw column names
    hl["flag_v1_w3nm0"] = (pd.to_numeric(hl.get("w3nm_aw"), errors="coerce") == 0)
    hl["flag_v1_w4nm0"] = (pd.to_numeric(hl.get("w4nm_aw"), errors="coerce") == 0)
    hl["flag_v1_w3flg32"] = (pd.to_numeric(hl.get("w3flg_aw"), errors="coerce") == 32)
    hl["flag_v1_w4flg32"] = (pd.to_numeric(hl.get("w4flg_aw"), errors="coerce") == 32)
    pq_as = hl.get("ph_qual_as", pd.Series([""] * len(hl))).fillna("").astype(str)
    pq_aw = hl.get("ph_qual_aw", pd.Series([""] * len(hl))).fillna("").astype(str)
    hl["flag_v2_release_inconsistent"] = [
        len(a) == 4 and len(w) == 4 and any(a[i] == "U" and w[i] != "U" for i in (2, 3))
        for a, w in zip(pq_as, pq_aw)]
    s3 = pd.to_numeric(hl.get("w3snr_aw"), errors="coerce").fillna(hl["snr3"])
    s4 = pd.to_numeric(hl.get("w4snr_aw"), errors="coerce").fillna(hl["snr4"])
    hl["flag_v3_subthreshold"] = (s3 < 5.0) & (s4 < 5.0)
    hl["v5_centroid"] = "RETIRED (M5 PR-5) — not measured, not usable near the floor"

    cols = [
        # identity
        ("source_id", "Gaia DR3 source_id"),
        ("designation_aw", "AllWISE designation"),
        ("tmass_designation", "2MASS designation"),
        ("ra", "ICRS RA, deg (Gaia DR3, epoch J2016.0)"),
        ("dec", "ICRS Dec, deg"),
        ("glon", "Galactic longitude, deg"),
        ("glat", "Galactic latitude, deg"),
        ("ecl_lat", "ecliptic latitude, deg"),
        ("b_band", "core_b50 (calibrated) | outer_b30_50"),
        # astrometry / distance
        ("parallax", "Gaia DR3 parallax, mas"),
        ("parallax_error", "parallax uncertainty, mas"),
        ("pmra", "proper motion in RA*cos(dec), mas/yr"),
        ("pmdec", "proper motion in Dec, mas/yr"),
        ("r_med_geo", "Bailer-Jones EDR3 geometric distance, pc (exact, not proxied)"),
        ("ruwe", "Gaia DR3 RUWE"),
        # photometry
        ("phot_g_mean_mag", "Gaia G, mag"), ("phot_bp_mean_mag", "Gaia BP, mag"),
        ("phot_rp_mean_mag", "Gaia RP, mag"), ("M_G", "absolute G, mag"),
        ("j_m", "2MASS J, mag"), ("h_m", "2MASS H, mag"), ("ks_m", "2MASS Ks, mag"),
        ("w1mpro", "AllWISE W1, mag"), ("w1mpro_error", "W1 uncertainty, mag"),
        ("w2mpro", "AllWISE W2, mag"), ("w2mpro_error", "W2 uncertainty, mag"),
        ("w3mpro", "AllWISE W3, mag"), ("w3mpro_error", "W3 uncertainty, mag"),
        ("w4mpro", "AllWISE W4, mag"), ("w4mpro_error", "W4 uncertainty, mag"),
        ("snr3", "W3 signal-to-noise (screen, from w3mpro_error)"),
        ("snr4", "W4 signal-to-noise"),
        ("w3snr_aw", "W3 S/N, AllWISE catalogue"),
        ("w4snr_aw", "W4 S/N, AllWISE catalogue"),
        # the excess model
        ("rmse", "RMSE of the 10-band star+Dyson-sphere fit, mag"),
        ("t_ds", "fitted Dyson-sphere/dust temperature, K"),
        ("gamma", "fitted covering fraction (model grid floor 0.10)"),
        ("gvar", "Gaia G variability statistic (Suazo Eq. 4)"),
        # vetting
        ("verdict", "M3 PR-3 verdict"),
        ("verdict_reason", "the evidence behind the verdict"),
        ("flag_v1_w3nm0", "V1: never detected in a single W3 exposure"),
        ("flag_v1_w4nm0", "V1: never detected in a single W4 exposure"),
        ("flag_v1_w3flg32", "V1: W3 aperture photometry is a 95% upper limit"),
        ("flag_v1_w4flg32", "V1: W4 aperture photometry is a 95% upper limit"),
        ("ph_qual_aw", "AllWISE ph_qual"),
        ("ph_qual_as", "WISE All-Sky Release ph_qual (same photons, earlier pipeline)"),
        ("flag_v2_release_inconsistent", "V2: excess band is 'U' in All-Sky but not in AllWISE"),
        ("flag_v3_subthreshold", "V3: both excess bands below WISE's own 5-sigma standard"),
        ("p_chance_1as", "V4: P(>=1 faint red galaxy within 1 arcsec), Suazo's own density"),
        ("v5_centroid", "V5: RETIRED — see M5 PR-5"),
        # nebular stage
        ("n1_flag", "N1: inside the published extent of a catalogued nebula"),
        ("n1_cat", "N1: which catalogue"), ("n1_name", "N1: which object"),
        ("n1_sep_as", "N1: separation from that object's centre, arcsec"),
        ("n1_r_as", "N1: that object's published radius, arcsec"),
        ("n2_score", "N2: max percentile rank of w3sky/w4sky in the |b|>50 parent"),
        ("n2_flag", "N2: score > 0.99"),
        ("nebular_flag", "N1 or N2"),
        ("w3sky", "AllWISE median background in the W3 profile-fit annulus, DN"),
        ("w4sky", "AllWISE median background in the W4 profile-fit annulus, DN"),
        ("w3conf", "AllWISE W3 sky confusion from the uncertainty images"),
        ("w4conf", "AllWISE W4 sky confusion"),
    ]
    have = [(c, dsc) for c, dsc in cols if c in hl.columns]
    missing = [c for c, _ in cols if c not in hl.columns]
    if missing:
        print(f"  NOTE: columns absent from the inputs and omitted: {missing}")
    out = hl[[c for c, _ in have]].copy()
    for c in out.columns:
        if out[c].dtype.kind == "f":
            out[c] = out[c].round(6)
    path = CAT / "dyson-revet_highlat_extreme_IR_excess_v1.csv"
    out.to_csv(path, index=False)
    print(f"  wrote {path.relative_to(ROOT)}  "
          f"({len(out):,} rows x {len(out.columns)} columns, "
          f"{path.stat().st_size / 1024:.0f} KB)")

    # ------------------------------------------ completeness / contamination
    stats = catalog_stats(d, hl, have)
    (CAT / "catalog_stats.json").write_text(json.dumps(stats, indent=2))
    print("\n== completeness and contamination, measured ==")
    print(json.dumps(stats, indent=2)[:3000])

    (OUT / f"m5_verdict_summary_{TAG}.json").write_text(json.dumps({
        "n_survivors": n,
        "verdicts": {k: int(v) for k, v in vc.items()},
        "still_clean_unreachable": True,
        "still_clean_reason": ("V5 retired (M5 PR-5, M4 Sec 5.3): the archival "
                               "centroid is wrong in direction as well as "
                               "magnitude near the floor, so STILL-CLEAN's "
                               "positive-evidence requirement cannot be met"),
        "by_latitude": lat_rows,
        "verdict_x_nebular": {str(k): {str(kk): int(vv) for kk, vv in v.items()}
                              for k, v in ct.to_dict("index").items()},
    }, indent=2))
    print(f"\nwrote out/m5_verdict_table_{TAG}.csv, "
          f"out/m5_verdict_summary_{TAG}.json, catalog/catalog_stats.json")


def catalog_stats(d: pd.DataFrame, hl: pd.DataFrame, have) -> dict:
    area30 = sum(band_area(lo, hi) for lo, hi in BANDS if lo >= 30)
    area50 = band_area(50, 90)
    core = hl[hl["b_band"] == "core_b50"]
    vc = hl["verdict"].value_counts()
    # the denominator the S/N cut acts on: extra-cut survivors in the footprint
    rm = pd.read_csv(OUT / "w4_rmse_survivors_m4_g0.1.csv")
    _, rb = galactic(rm["ra"].to_numpy(), rm["dec"].to_numpy())
    n_extra30 = int((rm["extra_ok"].astype(bool) & (np.abs(rb) >= HIGHLAT)).sum())
    sm = json.loads((OUT / "m5_nebular_skymask.json").read_text())
    m3050 = sm["bands"]["30-50"]["masked_fraction"]
    m5090 = sm["bands"]["50-90"]["masked_fraction"]
    a3050, a5090 = band_area(30, 50), band_area(50, 90)
    mask30 = (m3050 * a3050 + m5090 * a5090) / (a3050 + a5090)
    mask50 = m5090
    # expected chance alignments inside Suazo's own 3.25" W3 aperture radius
    rho_as2 = RHO_REDGAL_DEG2 / 3600.0 ** 2
    p325 = 1.0 - np.exp(-rho_as2 * np.pi * 3.25 ** 2)
    p1 = 1.0 - np.exp(-rho_as2 * np.pi * 1.0 ** 2)
    return {
        "footprint": {
            "definition": "|b| > 30 deg", "area_deg2": area30,
            "n": int(len(hl)),
            "calibrated_core": {"definition": "|b| > 50 deg",
                                "area_deg2": area50, "n": int(len(core))},
        },
        "columns": len(have),
        "selection_function": {
            "parent": ("Gaia DR3 x AllWISE x 2MASS, Bailer-Jones EDR3 "
                       "r_med_geo < 300 pc, W3 AND W4 profile-fit detections, "
                       "AllWISE cc_flags clean, full 10-band photometry, "
                       "inside the template M_G window [0.5, 14.0]"),
            "model": ("star + blackbody Dyson-sphere grid, RMSE <= 0.2 mag over "
                      "10 bands, covering fraction gamma >= 0.10 -- the paper's "
                      "own stated grid floor"),
            "cuts": "Gvar < 2, RUWE < 1.4, ext_flg = 0, classprob > 0.9, W3 and W4 S/N >= 3.5",
            "nebular_stage": "M5 N1 (catalogue veto) | N2 (coadd background percentile > 0.99)",
        },
        "completeness": {
            "statement": ("This is a SELECTION-FUNCTION-DEFINED catalogue, not a "
                          "complete one. Every number below is a known way it is "
                          "incomplete, measured or cited, never estimated."),
            "gamma_floor": ("objects with covering fraction gamma < 0.10 are not "
                            "selected at all. M3 measured that dropping the floor "
                            "to gamma >= 0.01 multiplies RMSE survivors by 5.83x "
                            "and pre-visual survivors by 2.93x, so the catalogue "
                            "misses the majority of weaker excesses by construction"),
            "snr_floor": (f"W3 and W4 S/N >= 3.5. In this footprint that cut "
                          f"alone removes {100 * (1 - len(hl) / max(n_extra30, 1)):.1f} "
                          f"per cent of the {n_extra30:,} objects that reach it"),
            "tenband_requirement": ("full G/BP/RP/J/H/Ks/W1-W4 photometry is "
                                    "required; 326,540 of 328,937 parent rows "
                                    "(99.27 per cent) have it"),
            "distance_cut": "r_med_geo < 300 pc; nothing beyond is in the parent",
            "sky": (f"100 per cent of the sky is screened (M4 Sec 6.1), so there "
                    f"is no coverage incompleteness; the N1 catalogue veto masks "
                    f"{100 * mask30:.2f} per cent of the |b| > 30 deg sky and "
                    f"{100 * mask50:.2f} per cent of the |b| > 50 deg core"),
            "not_measured": ("no injection-recovery completeness has been run; "
                             "the fraction of real extreme-excess objects the "
                             "10-band RMSE fit recovers is UNMEASURED by this "
                             "project"),
        },
        "contamination": {
            "own_gates": {k: int(v) for k, v in vc.items()},
            "contamination_consistent_frac": float((hl["verdict"] == "CONTAMINATION-CONSISTENT").mean()),
            "subthreshold_frac": float((hl["verdict"] == "SUB-THRESHOLD").mean()),
            "chance_alignment": {
                "density_deg2": RHO_REDGAL_DEG2,
                "source": ("Suazo et al. 2024 Sec 3.1's own faint-red-galaxy "
                           "density, 15000 sr^-1 -- NOT Ren et al. 2024's "
                           "3600x-slipped value (M1)"),
                "p_within_1as": float(p1),
                "p_within_3p25as": float(p325),
                "expected_in_footprint_1as": float(p1 * len(hl)),
                "expected_in_footprint_3p25as": float(p325 * len(hl)),
                "expected_over_the_whole_parent_3p25as": float(p325 * 328937),
                "reading": ("With Suazo et al.'s own density the expected number "
                            "of chance-aligned faint red galaxies is 3.8 over the "
                            "ENTIRE 328,937-star parent and 0.003 inside this "
                            "footprint. That population therefore cannot account "
                            "for a catalogue of 223 objects, and V4 is a weak axis "
                            "at this sample size -- which M3 already recorded. What "
                            "our gates do convict these objects on is photometric: "
                            "single-exposure non-detections, release-dependent "
                            "photometry and sub-5-sigma bands (V1-V3). The fainter "
                            "red-galaxy population M1 identified as the real "
                            "contaminant class has no published density and is "
                            "NOT quantified here."),
            },
            "centroid_blind_spot": ("V5 is retired (M5 PR-5). M4 Sec 5.3 measured "
                                    "sep_thr(rho) = F (1 + 1/rho): at a 1\" floor "
                                    "~10% and at a 2\" floor ~40% of chance-aligned "
                                    "contaminants inside Suazo's own 3.25\" aperture "
                                    "are invisible to archival centroid vetting at "
                                    "ANY brightness. No object in this catalogue can "
                                    "be called clean."),
            "residual_overproduction": ("after the M5 nebular stage the |b| > 50 deg "
                                        "yield is 1.05x the paper's all-sky rate and "
                                        "the 30-50 deg band is 1.32x; the excess over "
                                        "a calibrated screen in this footprint is "
                                        "therefore small but not zero"),
            "jwst_ground_truth": ("of the ten labelled Hephaistos objects, five have "
                                  "an identified contaminant (B, C, D, E, G), two of "
                                  "them confirmed by JWST. The base rate of "
                                  "contamination among published candidates of this "
                                  "kind is high."),
        },
        "scientific_use_beyond_technosignatures": [
            "Extreme debris disks: main-sequence stars within 300 pc with 12 and "
            "22 micron excesses far above the photosphere. The fitted blackbody "
            "temperature t_ds and covering fraction gamma are in the table.",
            "White-dwarf and low-mass-star dust pollution: candidate infrared "
            "excesses around evolved and very-low-mass objects, selected without "
            "any prior on host type beyond the M_G window.",
            "Extreme M-dwarf mid-IR excesses: the sample is dominated by "
            "M_G 10-12 dwarfs, a regime where WISE excess samples are sparse.",
            "A measured false-positive set for WISE-excess searches: the objects "
            "our gates convict are a catalogued, position-resolved sample of the "
            "ways AllWISE manufactures a 22 micron excess -- single-exposure "
            "non-detections, release-dependent photometry, sub-5-sigma bands, "
            "and blends below the archival centroid floor.",
            "A calibration set for the archival contamination floor: paired with "
            "the JWST measurement of candidate D (M4 Sec 5), these are the objects "
            "on which sep_thr(rho) = F (1 + 1/rho) can be tested if imaging "
            "becomes available.",
        ],
    }


if __name__ == "__main__":
    main()
