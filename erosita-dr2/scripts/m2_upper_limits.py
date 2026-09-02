"""M2: DR2 (eRASS:3 cumulative) upper limits at every vanished-source position.

API (documented at https://erosita.mpe.mpg.de/erodat/apis/#upper-limits, verified
2026-08-14): POST https://erosita.mpe.mpg.de/erodat/upperlimit/service_multi with a
JSON array of {ra, dec, band, dr_survey}; band 024 = 0.2-2.3 keV (the catalogs'
1B band); dr_survey DR2_eRASSc3 = cumulative eRASS:3. Response per position:
Exposure [s], UL_B, UL_S [erg/cm2/s], Flag_pos, field, healpix.
Method paper: Tubin-Arenas et al. 2024 (ads 2024A&A...682A..35T): UL_B is the
Bayesian (Kraft) one-sided upper limit from the counts actually present in the
aperture; UL_S is the local sensitivity estimate. Empirically (probe 2026-08-14):
at the position of a persisting 2.6e-11 source, UL_B = 2.5e-11 while UL_S =
2.7e-13 - i.e. UL_B/UL_S >> 1 flags real counts at the position.

Physics of the test (M1 Sect. 2): the eRASS:3 stack CONTAINS the eRASS1 photons,
so even a source that switched off right after eRASS1 must leave ~F1*t1/t3 of
time-averaged flux. Therefore per vanished source:
  presence  = UL_B / UL_S          >> 1: counts present at the position
  fade_frac = UL_B / F1(eRASS1)    ~1: still bright (catalog dropout);
                                   ~t1/t3 (~0.2-0.5): switched off, residual only;
                                   << t1/t3: containment anomaly (flare filter?)
Calibration: the same POST includes N_CAL steady DR1xDR2 pairs (|R-1|<0.05,
z_var<1, 20-sigma bright) - their fade_frac distribution shows where "unchanged"
lands in this metric.

Output: out/m2_vanished_forensics.csv gains UL columns (rewritten in place);
calibration rows go to out/m2_ul_calibration.csv.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DATA = ROOT / "data"
URL = "https://erosita.mpe.mpg.de/erodat/upperlimit/service_multi"
N_CAL = 25


def main() -> None:
    van = pd.read_csv(OUT / "m2_vanished_forensics.csv")
    pairs = pd.read_parquet(DATA / "w2_pairs.parquet",
                            columns=["IAUNAME", "RA", "DEC", "R", "z_var",
                                     "ML_RATE_1", "ML_RATE_ERR_1", "ML_FLUX_1",
                                     "ML_FLUX_1_D1", "ML_EXP_1", "ML_EXP_1_D1"])
    cal = pairs[(np.abs(pairs["R"] - 1) < 0.05) & (pairs["z_var"] < 1)
                & (pairs["ML_RATE_1"] / pairs["ML_RATE_ERR_1"] >= 20)]
    cal = cal.sample(n=min(N_CAL, len(cal)), random_state=42).reset_index(drop=True)
    print(f"vanished: {len(van)}; calibration steady pairs: {len(cal)}")

    if "ul_b_flux" in van.columns and van["ul_b_flux"].notna().all() \
            and (OUT / "m2_ul_calibration.csv").exists():
        print("UL columns already present - reusing cached server results")
        cal = pd.read_csv(OUT / "m2_ul_calibration.csv")
    else:
        body = [{"ra": float(r), "dec": float(d), "band": "024",
                 "dr_survey": "DR2_eRASSc3"}
                for r, d in zip(van["RA"], van["DEC"])]
        body += [{"ra": float(r), "dec": float(d), "band": "024",
                  "dr_survey": "DR2_eRASSc3"}
                 for r, d in zip(cal["RA"], cal["DEC"])]
        resp = requests.post(URL, json=body, timeout=600)
        resp.raise_for_status()
        js = resp.json()
        if js.get("error") not in (None, "None"):
            raise RuntimeError(f"UL server error: {js['error']}")
        lim = js["limits"]
        assert len(lim) == len(body), (len(lim), len(body))
        ul = pd.DataFrame(lim)

        vu = ul.iloc[:len(van)].reset_index(drop=True)
        van["ul_exposure_s"] = vu["Exposure"]
        van["ul_b_flux"] = vu["UL_B"]
        van["ul_s_flux"] = vu["UL_S"]
        van["ul_flag_pos"] = vu["Flag_pos"]
        van["ul_presence"] = van["ul_b_flux"] / van["ul_s_flux"]
        van["ul_fade_frac"] = van["ul_b_flux"] / van["ML_FLUX_1"]
        # rough t1/t3 from DR1 vignetted exposure vs UL exposure (both ~seconds
        # at position; conventions differ slightly -> indicative only)
        van["t1_over_t3_approx"] = van["ML_EXP_1"] / van["ul_exposure_s"]

        cu = ul.iloc[len(van):].reset_index(drop=True)
        cal["ul_exposure_s"] = cu["Exposure"]
        cal["ul_b_flux"] = cu["UL_B"]
        cal["ul_s_flux"] = cu["UL_S"]
        cal["ul_flag_pos"] = cu["Flag_pos"]
        cal["ul_presence"] = cal["ul_b_flux"] / cal["ul_s_flux"]
        cal["ul_fade_frac"] = cal["ul_b_flux"] / cal["ML_FLUX_1_D1"]
        cal.to_csv(OUT / "m2_ul_calibration.csv", index=False)

    print("calibration fade_frac (steady sources, UL_B / F1):")
    print(cal["ul_fade_frac"].describe().round(3).to_string())

    # ---- refined classification: geometry x UL evidence ---------------------
    # The purely geometric pass over-calls confusion: a "similarly bright
    # neighbor" 50-120" away cannot absorb a source's counts (survey PSF HEW
    # ~30"). The UL presence metric tests directly whether flux remains at the
    # position. Tree (documented in M2-vetting.md):
    #   1. DR2 source of any kind within 15"          -> ARTIFACT-SPLIT/MOVED
    #   2. ul_presence == 0 (insensitive: bright halo) -> INDETERMINATE-HALO
    #   3. ul_presence > 1.5 (counts present)          -> ARTIFACT (flux persists,
    #      erbox/extended-absorption dropout; subclass by geometry)
    #   4. blank position (presence <= 1.5):
    #      a. bright neighbor within 40" (~PSF)        -> CONFUSED-IDENTITY
    #      b. else                                     -> FADE-CANDIDATE
    presence = van["ul_presence"]
    is_split = van["in_dr2_any_sep"] <= 15.0
    is_halo = ~is_split & (presence <= 0.01)
    counts_present = ~is_split & ~is_halo & (presence > 1.5)
    geom_conf = van["nn2_bright_sep_arcsec"] <= 120.0
    geom_ext = van["next_sep_arcsec"] <= 120.0
    blank = ~is_split & ~is_halo & ~counts_present
    near_psf = van["nn2_bright_sep_arcsec"] <= 40.0
    van["forensic_class_v2"] = np.select(
        [is_split,
         is_halo,
         counts_present & geom_conf,
         counts_present & ~geom_conf & geom_ext,
         counts_present & ~geom_conf & ~geom_ext,
         blank & near_psf,
         blank & ~near_psf],
        ["ARTIFACT-SPLIT/MOVED", "INDETERMINATE-HALO",
         "ARTIFACT-CONFUSION", "ARTIFACT-EXTENDED", "ARTIFACT-UNCLEAR-PERSIST",
         "CONFUSED-IDENTITY", "FADE-CANDIDATE"],
        default="FADE-CANDIDATE",
    )
    van.to_csv(OUT / "m2_vanished_forensics.csv", index=False)
    print("\nrefined split (v2):")
    print(van["forensic_class_v2"].value_counts().to_string())
    print("\nFADE-CANDIDATEs, individually:")
    pf = van[van["forensic_class_v2"] == "FADE-CANDIDATE"].sort_values(
        "DET_LIKE_0", ascending=False)
    print(pf[["IAUNAME", "DET_LIKE_0", "ML_FLUX_1", "ul_b_flux", "ul_fade_frac",
              "ul_presence", "nn2_bright_sep_arcsec", "ul_flag_pos"]].to_string(index=False))


if __name__ == "__main__":
    main()
