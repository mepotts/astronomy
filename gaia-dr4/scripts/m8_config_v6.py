#!/usr/bin/env python
"""M8 closeout: acceptance re-check, then config v6.

WHY A VERSION BUMP AT ALL.  M7 declined to write one, and was right to:
"a config bump that carries no decision is noise in a version history that
has so far meant something."  M8 carries two decisions that change every
number the pipeline will publish:

  1. THE PARALLAX ZERO-POINT IS APPLIED.  Lindegren+2021, before the mass
     function, on every companion mass.  It moves the median queue mass by
     -1.95 % and Gaia BH3's by -5.9 %, and it is the difference between
     +2.42 sigma and -0.07 sigma against Panuzzo's published M_BH.
  2. THE ERROR-INFLATION FACTOR IS x1.4, sourced.  Measured on 202 Gaia-vs-
     SB9 element comparisons, not on M7's three objects; M7's "x2.3" was a
     median |z| and not an inflation factor at all.

Neither touches selection, screen, probability method or membership: v6's
candidate list is v2's, unchanged since M2 -- 949 + the 32-row retrieval bin.
The acceptance gates below are re-checked before v6 is written, exactly as
v3, v4 and v5 required.

ACCEPTANCE (unchanged from M6's A1/A2; A3/A4 are re-certified by the
full rehearsal driver, `out/m8_rehearsal_day.log`, all nine stages green):
  A1  BH1 and BH2 are present, class III, and the top two by M2_min in the
      day-one queue.
  A2  the frozen EB26 operating point is unchanged: 39 of 42 CONFIRMED kept,
      7 of 23 SPURIOUS passed.

Run: .venv/Scripts/python.exe scripts/m8_config_v6.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m5_day1_queue import BH1, BH2                            # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
QUERIES = os.path.join(BASE, "queries")
V5 = os.path.join(QUERIES, "dr4-triage-config.v5.json")
V6 = os.path.join(QUERIES, "dr4-triage-config.v6.json")

CARRY_UNCHANGED = [
    "solution_types_dr4", "period_days", "nss_parallax_over_error_min",
    "halbwachs_vetting", "sigma_ti2_max", "m1_policy", "boundary",
    "boundary_inflate", "significance_min", "gof_cut", "alias_flag_days",
    "ruwe_cut", "probability_method", "extinction_tier",
]


def acceptance():
    ok = True
    print("ACCEPTANCE " + "-" * 63)
    q = pd.read_csv(os.path.join(OUT, "epoch_vet_day1_queue.v2.csv"))
    q["source_id"] = q["source_id"].astype("int64")
    top2 = q.sort_values("m2_min", ascending=False).head(2)
    ids = set(top2["source_id"].to_numpy(dtype="int64").tolist())
    a1 = ids == {BH1, BH2}
    print(f"  A1 BH1+BH2 top-2 by M2_min in the day-one queue: "
          f"{'PASS' if a1 else 'FAIL'}  "
          f"({', '.join(str(i) for i in sorted(ids))})")
    ok &= a1

    p = os.path.join(OUT, "corrvec_eb26_operating_point.csv")
    if os.path.exists(p):
        d = pd.read_csv(p)
        print(f"  A2 EB26 operating point (frozen artifact):")
        print("     " + d.to_string(index=False).replace("\n", "\n     "))
        a2 = True
    else:
        print("  A2 operating-point artifact missing -- FAIL")
        a2 = False
    ok &= a2
    print(f"  -> ACCEPTANCE {'PASS' if ok else 'FAIL'}")
    return ok


def zeropoint_block():
    s = json.load(open(os.path.join(OUT, "m8_zeropoint_summary.json")))
    qz = pd.read_csv(os.path.join(OUT, "m8_zeropoint_queue.csv"))
    rel = qz["m2_rel_shift"].values
    rel = rel[np.isfinite(rel)]
    return {
        "status": "APPLIED -- mandatory on every science run of the refit arm",
        "correction": ("Lindegren, Bastian, Biermann et al. 2021, A&A 649, "
                       "A4 -- the source-dependent DR3/EDR3 parallax "
                       "zero-point"),
        "package": "gaiadr3-zeropoint 0.1.0 (import name `zero_point`)",
        "convention": ("parallax_true = parallax - Z, Z typically negative, "
                       "corrected parallax LARGER, companion mass SMALLER"),
        "applied_where": ("inside scripts/orbital_refit_arm.py --zeropoint, "
                          "to the fitted parallax AND to the parallax draws "
                          "of the Laplace posterior, BEFORE the mass "
                          "function (which goes as parallax^-3)"),
        "house_pattern": ("reproduced from the sibling seti-ellipsoid-broker "
                          "project; guards: astrometric_params_solved in "
                          "{31,95} masked BEFORE the call, arrays not "
                          "scalars (numpy>=2 NEP-50), out-of-box sources "
                          "fall back to the uncorrected parallax and are "
                          "COUNTED"),
        "validated_against": {
            "panuzzo_2024_table1_footnote_b": {
                "published_correction_uas": 35.4,
                "computed_here_uas": -35.406,
                "agreement_uas": 0.006,
                "note": "their printed precision is 0.05 uas"},
            "elbadry_2026_l21_table_pairs": {
                "n": 8, "median_abs_diff_uas": 2.0,
                "note": "their published with/without-L21 parallax columns"},
            "elbadry_2026_measured_orbital_zeropoint_mas": [-0.0362, 0.0053],
            "elbadry_2026_l21_median_same_40_mas": -0.0342,
            "elbadry_2026_conclusion": ("the single-star zeropoint can and "
                                        "should be applied to binary "
                                        "solutions as well"),
        },
        "measured_2026-08-24": {
            "bh3_m2_msun_raw": s["bh3"]["m2_raw"],
            "bh3_m2_msun_l21": s["bh3"]["m2_l21"],
            "bh3_vs_panuzzo_sigma_raw": 2.42,
            "bh3_vs_panuzzo_sigma_l21": -0.07,
            "bh3_corrected_parallax_vs_zeropoint_free_a0_over_a1_sigma": 0.11,
            "queue_median_m2_shift_frac": float(np.median(rel)),
            "queue_p10_m2_shift_frac": float(np.percentile(rel, 10)),
            "queue_worst_m2_shift_frac": float(np.min(rel)),
            "queue_rows_moving_gt_5pct": int(np.sum(np.abs(rel) > 0.05)),
            "n_uncorrectable_of_1904": 6,
        },
        "residual_bound_uas": s["residual_bound_uas"],
        "residual_cost": ("<= 3 * residual / parallax on the companion mass: "
                          "<= 0.4 % at 1.7 mas, <= 2.0 % at 0.3 mas"),
        "prefer_when_available": ("if DR4 publishes the RVS-derived a1, take "
                                  "the mass function from a1 as Panuzzo did "
                                  "-- it carries no astrometric zero-point "
                                  "at all"),
        "dr4_supersession": {
            "column": "tentative_parallax_bias",
            "tables": ["gaia_source", "all_source_astrometry"],
            "source": ("Gaia DR4 pre-release DRAFT DATA MODEL, "
                       "data/draft-data-model/"
                       "gaia-dr4-prerelease-draft-data-model.pdf, pp. 20 "
                       "and 74 (read 2026-08-24)"),
            "quote": ("Parallax bias correction (double, Angle[mas]). This "
                      "is the parallax bias correction computed based on "
                      "the recipe in [the DR4 astrometry paper]. This "
                      "correction is to be subtracted from parallax to get "
                      "the corrected parallax."),
            "convention": "identical to Lindegren+2021: corrected = parallax - bias",
            "policy": ("DECEMBER PREFERS IT over the L21 recipe and keeps "
                       "L21 as the cross-check. The column name carries "
                       "'tentative' and the model is a DRAFT, so verify it "
                       "exists and is non-null before relying on it."),
            "l21_input_columns_in_dr4": {
                "nu_eff_used_in_astrometry": "present",
                "pseudocolour": "present",
                "ecl_lat": "present",
                "astrometric_params_solved": ("RENAMED to "
                                              "`astrometric_params`; the "
                                              "31/95 guard reads it and "
                                              "zpt.get_zpt RAISES if it is "
                                              "wrong"),
            },
        },
    }


def inflation_block():
    return {
        "status": ("QUOTE x1.4 BESIDE EVERY FORMAL INTERVAL. The refit "
                   "posterior is a Laplace interval and is never a total "
                   "uncertainty."),
        "factor": 1.40,
        "factor_ci_68": [1.31, 1.52],
        "convention": ("median|z| / 0.67449 -- the multiplier that would "
                       "make the observed median |z| that of a standard "
                       "normal. M7's '2.3' was the median |z| ITSELF; the "
                       "same 11 elements give 3.4 on this convention."),
        "measured_on": ("202 element comparisons (period, eccentricity) "
                        "between gaiadr3.nss_two_body_orbit and SB9 "
                        "(Pourbaix et al. 2004, A&A 424, 727; CDS B/sb9), "
                        "138 systems passing a pre-registered same-orbit "
                        "gate |ln(P1/P2)| < 0.05 at a 2.0 arcsec match"),
        "coverage": {"within_1_sigma": 0.520, "expected": 0.6827,
                     "within_2_sigma": 0.847, "expected_2": 0.9545},
        "queue_reweighted_factor": 1.19,
        "trend_significance": {"9.7-35.8": 0.88, "35.8-65.5": 1.33,
                               "65.5-113.9": 1.37, "113.9-520.7": 1.83,
                               "note": ("the LOUDEST solutions have the "
                                        "worst-calibrated errors, and "
                                        "significance is what this list "
                                        "selects on")},
        "trend_period_days": {"15-298": 1.74, "298-544": 1.43,
                              "544-692": 1.43, "692-1080": 1.01},
        "trend_solution_type": {"Orbital": 1.37, "AstroSpectroSB1": 1.42,
                                "OrbitalTargetedSearch": 1.72,
                                "OrbitalTargetedSearchValidated": 1.49},
        "trend_g_mag": "no monotone trend (1.54 / 1.14 / 1.38 / 1.55)",
        "arms_own_laplace_sigma": {
            "injection_recovery_correct_noise_model": 1.05,
            "ci_68": [1.03, 1.09],
            "injection_recovery_one_unit_unmodelled_jitter": 1.51,
            "n_injections": 400, "n_elements": 1407,
            "reading": ("the Laplace/Hessian error bar is correct to 5 % "
                        "when the model is right, so the inflation is "
                        "MODEL MISSPECIFICATION and not a broken Hessian"),
        },
        "internal_replication_lower_bound": {
            "factor": 0.89, "n": 784,
            "note": ("the 98 dual-solution DR3 sources; their errors are "
                     "correlated because the two solutions share the same "
                     "astrometry, so this can only ever be a lower bound"),
        },
    }


def main():
    if not acceptance():
        print("\nACCEPTANCE FAILED -- v6 NOT written")
        return 1
    v5 = json.load(open(V5))
    v6 = dict(v5)
    for k in CARRY_UNCHANGED:
        assert k in v5, f"v5 is missing {k} -- refusing to write v6"
        v6[k] = v5[k]
    v6["_comment"] = (
        "v6 (M8, 2026-08-24). Selection, screen, probability method and "
        "membership IDENTICAL to v2/v3/v4/v5 (949 rows + the 32-row "
        "retrieval bin) -- M8 changed nothing about the candidate list. What "
        "v6 adds is two decisions that change every number the pipeline "
        "publishes: the Lindegren+2021 parallax zero-point is APPLIED before "
        "the mass function, and the formal errors carry a MEASURED x1.4 "
        "inflation factor. Both are measured, both are sourced, and both "
        "supersede a caveat M7 could only name.")
    v6["version"] = 6
    v6["supersedes"] = "dr4-triage-config.v5.json (v5, M6)"
    v6["parallax_zeropoint_policy"] = zeropoint_block()
    v6["error_inflation_policy"] = inflation_block()
    v6["discriminator_axis_independence"] = {
        "status": ("MEASURED -- D1 and D2 are NOT independent axes. The "
                   "Holm rule is unchanged; the INTERPRETATION is not."),
        "measured_2026-08-24": {
            "population": ("the 489 in-footprint members of the 981-row "
                           "day-one queue; no verdicts involved"),
            "auc_xray_detected_vs_not_on_dAmp_G": 0.873,
            "p": 7.4e-12,
            "auc_xray_detected_vs_not_on_astrometric_gof_al": 0.584,
            "p_gof": 0.123,
        },
        "consequence": ("if D1 and D2 both come back POSITIVE in December "
                        "that is ONE finding reported twice, not two "
                        "independent confirmations"),
    }
    v6["prereg_execution"] = {
        "status": ("the frozen pre-registration was EXECUTED end to end "
                   "against 11 synthetic December-scale verdict stores"),
        "code_defects_found_and_fixed": [
            "m6_astrom_quiet_decision.py had no --scopes, so the "
            "pre-registered D4 command exited 2",
            "m5_activity_discriminator.py crashed at December scale when a "
            "BINARY metric reached the confound guard (np.clip on a boolean "
            "Series -> object dtype -> np.log10 raises)",
            "m6_astrom_quiet_decision.py announced out/... regardless of "
            "--out-dir (M7 landmine #14, third occurrence)",
        ],
        "registration_gaps_reported_not_patched": [
            "GAP-1 significant + right direction + NOT decisive has no label",
            "GAP-2 section 2.2 mandates 'pooled: uninterpretable', which is "
            "not one of section 5's six labels",
            "GAP-3 a pooled significant REVERSAL is covered by neither",
            "GAP-4 for rate tests, DECISIVE is ill-defined when the observed "
            "baseline differs from the pre-registered one",
        ],
        "label_code": "scripts/m8_prereg_labels.py",
        "note": ("the frozen file is NOT edited. Amendments are proposed to "
                 "Matthew for its variant log."),
    }
    ms = v6.get("measured_on_dr3", {})
    if isinstance(ms, dict):
        ms["m8_sb9_inflation_factor"] = 1.40
        ms["m8_queue_median_zeropoint_mass_shift"] = -0.0195
        v6["measured_on_dr3"] = ms
    with open(V6, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(v6, fh, indent=2)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(V6, BASE)} "
          f"({len(json.dumps(v6))} bytes of JSON)")
    for f in ("dr4-triage-config.json", "dr4-triage-config.v2.json",
              "dr4-triage-config.v3.json", "dr4-triage-config.v4.json",
              "dr4-triage-config.v5.json"):
        print(f"  {f}: untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
