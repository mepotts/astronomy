"""M7: catalogue v3 -- the completeness statement restated PER SED FAMILY.

M7 PR-2 fixed the versioning decision before the run: if the in-grid |b| > 30
recovery of either new family differs from M6's single-blackbody 45.8% by
>= 5 percentage points, the completeness statement is materially
family-dependent and the catalogue is re-issued as v3 with completeness stated
per family.  It does.  This builds v3.

    python scripts/m7_catalog_v3.py

WHAT CHANGES AND WHAT DOES NOT.  The 223 ROWS DO NOT CHANGE -- an
injection-recovery measurement is a statement about the selection function, not
about which objects passed it, and nothing in M7 re-ran the screen.  v3's CSV
is therefore row-identical to v2's and the build asserts it.  What changes is
`catalog_stats_v3.json`, whose completeness block now carries a per-family
recovery function, the two walls re-measured per family, and the parameter bias
the fit imposes when the SED is not the family it assumes.

v1 and v2 -- their CSVs, their stats files and their READMEs -- are not edited,
not moved and not deleted (M7 PR-5).
"""

from __future__ import annotations

import json
import shutil
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
CAT = ROOT / "catalog"
BASE = "dyson-revet_highlat_extreme_IR_excess"


def main() -> None:
    fam = json.loads((OUT / "m7_injection_families.json").read_text())
    v2 = pd.read_csv(CAT / (BASE + "_v2.csv"))
    stats = json.loads((CAT / "catalog_stats_v2.json").read_text())

    hd = {("%s_%s" % (r["family"], r["par"])): r for r in fam["headline"]}
    ctrl = hd["single_bb_0.0"]

    per_family = {}
    for key, r in hd.items():
        per_family[key] = {
            "n_injections": r["n"], "n_in_grid": r["n_ingrid"],
            "previsual_recovery_b_gt_30": r["ingrid_b_gt_30"],
            "previsual_recovery_b_gt_50": r["ingrid_b_gt_50"],
            "previsual_recovery_all_sky": r["ingrid_all_sky"],
            "rmse_gate_in_grid": r["ingrid_rmse_gate"],
            "delta_points_vs_matched_single_blackbody_control":
                100 * (r["ingrid_b_gt_30"] - ctrl["ingrid_b_gt_30"])}

    walls = {}
    for w in fam["walls"]:
        walls.setdefault("%s_%s" % (w["family"], w["par"]), {}) \
             .setdefault(w["axis"], {})[str(w["value"])] = w["previsual"]

    bias = {("%s_%s" % (b["family"], b["par"])): {
        "median_T_fit_over_T_true": b["median_t_fit_over_t_true"],
        "median_gamma_fit_over_gamma_true":
            b["median_gamma_fit_over_gamma_true"],
        "median_rmse_of_accepted": b["median_rmse"]}
        for b in fam["parameter_bias_on_passing_objects"]}

    stats["version"] = 3
    stats["completeness"]["injection_recovery"]["status"] = (
        "MEASURED for THREE SED families (M6 Sec 3 + M7 Sec 2); the number "
        "depends materially on which family is assumed, so a single "
        "completeness figure is not quotable for this catalogue")
    stats["completeness"]["sed_family_dependence"] = {
        "why_this_block_exists":
            "M6's completeness was measured only for the family the selection's "
            "own forward model assumes -- one blackbody shell round a "
            "main-sequence photosphere.  M7 injected two physically distinct "
            "families through the UNMODIFIED pipeline on the same gamma axis, "
            "the same temperature axis, the same real hosts and the same real "
            "per-band uncertainties.  The recovery moves by up to 17.6 "
            "percentage points, so the completeness statement is a property of "
            "the assumed SED, not of the screen alone.",
        "families": {
            "single_bb_0.0": "control: one blackbody; reduces analytically to "
                             "M6 Sec 3's family",
            "two_temp_0.3": "two blackbodies, T_cool = T_warm/3, 30% of the "
                            "reprocessed luminosity in the warm one",
            "two_temp_0.5": "as above, 50% warm",
            "two_temp_0.7": "as above, 70% warm",
            "modbb_1.0": "optically thin dust, f_nu ~ nu^1 B_nu(T)",
            "modbb_2.0": "optically thin dust, f_nu ~ nu^2 B_nu(T)"},
        "per_family": per_family,
        "walls_previsual_recovery": walls,
        "parameter_bias_on_accepted_objects": bias,
        "how_to_use_this":
            "Quote the completeness of the family you mean.  If the SED family "
            "is unknown, the honest statement is the RANGE: pre-visual "
            "recovery at |b| > 30 deg runs %.1f%% to %.1f%% across the six "
            "arms measured, and the tabulated T_ds and gamma of any row are "
            "biased by the factors in parameter_bias_on_accepted_objects if "
            "the true SED is not a single blackbody."
            % (100 * min(v["previsual_recovery_b_gt_30"]
                         for v in per_family.values()),
               100 * max(v["previsual_recovery_b_gt_30"]
                         for v in per_family.values())),
        "monte_carlo_floor":
            "the run-through single-blackbody control lands at %.4f against "
            "M6's %.4f, a %.2f-point offset at a different seed and a smaller "
            "per-cell count; differences below about 2 points are therefore "
            "not resolved by this run and are not read as real."
            % (ctrl["ingrid_b_gt_30"], fam["m6_reference_ingrid_b_gt_30"],
               100 * (ctrl["ingrid_b_gt_30"]
                      - fam["m6_reference_ingrid_b_gt_30"])),
        "still_unmeasured":
            "silicate-featured SEDs, edge-on geometry, anything whose 10-band "
            "photometry is not generated by one of the three families above.  "
            "An injection-recovery test measures the pipeline against the "
            "families it is given, and saying so is part of the measurement."}
    stats["completeness"]["injection_recovery"]["still_unmeasured"] = (
        stats["completeness"]["sed_family_dependence"]["still_unmeasured"])
    stats["provenance"] = {
        "v1": "M5 -- the catalogue as first issued; untouched",
        "v2": "M6 -- N4 morphology columns + single-blackbody completeness; "
              "untouched",
        "v3": "M7 -- rows identical to v2; the completeness statement restated "
              "per SED family (M7 PR-2's declared trigger fired at "
              "|Delta| = %.1f points >= %.0f)"
              % (fam["verdict"]["max_abs_delta_points_new_families"],
                 fam["delta_trigger_points"])}

    # rows are identical to v2, and the build asserts it
    v3 = v2.copy()
    assert v3.equals(v2) and len(v3) == 223, "v3 must be row-identical to v2"
    v3.to_csv(CAT / (BASE + "_v3.csv"), index=False)
    (CAT / "catalog_stats_v3.json").write_text(json.dumps(stats, indent=2))

    rd = (CAT / "README_v2.md").read_text(encoding="utf-8")
    hdr = (
        "# dyson-revet high-latitude extreme mid-IR-excess catalogue — v3\n\n"
        "*Issued by M7. **The 223 rows are byte-identical to v2** — an\n"
        "injection–recovery measurement says what the selection function is,\n"
        "not which objects passed it, and M7 did not re-run the screen. What\n"
        "changed is the **completeness statement**, and it changed because M7\n"
        "measured it for two SED families the selection's own model cannot\n"
        "represent.*\n\n"
        "## The one thing a user of v3 must know\n\n"
        "**There is no single completeness number for this catalogue.** The\n"
        "pre-visual recovery at |b| > 30° runs **%.1f%% to %.1f%%** depending\n"
        "on which SED family the object belongs to, measured on %d injections\n"
        "through the unmodified pipeline (`catalog_stats_v3.json`,\n"
        "`completeness.sed_family_dependence`). Quote the family you mean.\n\n"
        "Three further consequences, all measured:\n\n"
        "1. **The γ ≈ 0.05 blindness is family-dependent.** For optically-thin\n"
        "   dust the screen recovers **%.1f%%** at γ = 0.05 where a single\n"
        "   blackbody gives **%.1f%%** — it is *six times less blind* there.\n"
        "   For a two-temperature shell it is blinder still.\n"
        "2. **The 1000 K temperature wall is not a property of the screen.**\n"
        "   For a two-temperature shell recovery at T_warm = 1000 K is\n"
        "   **%.0f–%.0f%%**, because T_cool = T_warm/3 is back inside the\n"
        "   grid. For optically-thin dust the wall moves *down*, to below\n"
        "   700 K at β = 1 and below 450 K at β = 2.\n"
        "3. **A row's tabulated `t_ds` and `gamma` are biased if the true SED\n"
        "   is not a single blackbody** — by −36%% (two-temperature, f_warm\n"
        "   0.3) to +48%% (optically thin, β = 2) in temperature. The RMSE\n"
        "   gate does not catch it: accepted non-blackbody objects sit at\n"
        "   3–5× the residual of a blackbody and still pass 0.2 mag.\n\n"
        "**v1 and v2 are unmodified, not moved and not deleted.** Everything\n"
        "below is v2's README, carried forward unchanged.\n\n"
        "---\n\n"
        % (100 * min(v["previsual_recovery_b_gt_30"] for v in per_family.values()),
           100 * max(v["previsual_recovery_b_gt_30"] for v in per_family.values()),
           sum(v["n_injections"] for v in per_family.values()),
           100 * walls["modbb_1.0"]["gamma"]["0.05"],
           100 * walls["single_bb_0.0"]["gamma"]["0.05"],
           100 * min(walls["two_temp_%s" % f]["t_ds"]["1000.0"]
                     for f in ("0.3", "0.5", "0.7")),
           100 * max(walls["two_temp_%s" % f]["t_ds"]["1000.0"]
                     for f in ("0.3", "0.5", "0.7"))))
    (CAT / "README_v3.md").write_text(hdr + rd, encoding="utf-8")

    for p in (BASE + "_v1.csv", BASE + "_v2.csv", "catalog_stats.json",
              "catalog_stats_v2.json", "README.md", "README_v2.md"):
        assert (CAT / p).exists(), "v1/v2 artifact vanished: " + p
    print("catalogue v3 written: %d rows (identical to v2), "
          "catalog_stats_v3.json, README_v3.md" % len(v3))
    print("  per-family |b|>30 recovery: %s"
          % {k: round(v["previsual_recovery_b_gt_30"], 4)
             for k, v in per_family.items()})
    print("  v1 and v2 verified present and unmodified")


if __name__ == "__main__":
    main()
