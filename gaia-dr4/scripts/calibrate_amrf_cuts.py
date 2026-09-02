#!/usr/bin/env python
"""M2: validate the AMRF implementation against Shahaf et al. 2023's published
per-source results, then calibrate the false-positive cuts against El-Badry
et al. 2026's follow-up verdicts, and freeze the DR4 day-one config.

Inputs : data/dr3_amrf_triage.parquet          (scripts/amrf_triage.py)
         data/papers/s23_cds/table{1,2}.dat    (CDS J/MNRAS/518/2991)
         fixtures/elbadry2026_astrometric_candidates.csv
Outputs: out/amrf_s23_crosscheck.csv           implementation-level agreement
         out/amrf_cut_variants.csv             purity/completeness tradeoff
         queries/dr4-triage-config.json        the frozen DR4 config
         stdout                                summary tables for the M2 doc

Run    : .venv/Scripts/python.exe scripts/calibrate_amrf_cuts.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amrf
import s23_reference

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGE = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")
EB26 = os.path.join(BASE, "fixtures", "elbadry2026_astrometric_candidates.csv")
OUT_DIR = os.path.join(BASE, "out")
CONFIG_OUT = os.path.join(BASE, "queries", "dr4-triage-config.json")

BASE_INFLATE = 1.15  # the inflate at which amrf_triage.py stored margins
                     # (must match amrf_triage.CONFIG['boundary_inflate'])


def s23_crosscheck(df):
    """Source-by-source comparison with S23's published A and classes."""
    t1 = s23_reference.load_table1()
    t2 = s23_reference.load_table2()
    j = t1.merge(df, on="source_id", how="left", suffixes=("_s23", ""))
    print("\n--- S23 cross-check (implementation validation) ---")
    print(f"S23 clean sample: {len(t1)}; found in our pull: "
          f"{j['amrf'].notna().sum()}")

    # A comparison restricted to sources where we used the same M1 source
    same = j[(j["m1_source"] == "binary_masses") & np.isfinite(j["amrf"])]
    ratio = same["amrf"] / same["A"]
    med, lo, hi = ratio.median(), ratio.quantile(0.01), ratio.quantile(0.99)
    frac_5pct = float(((ratio - 1).abs() < 0.05).mean())
    print(f"A(ours)/A(S23) on binary_masses tier (n={len(same)}): "
          f"median {med:.4f}, 1-99% [{lo:.4f}, {hi:.4f}]; "
          f"within 5%: {frac_5pct:.1%}")

    # their high-purity class-III sample (177) through our pipeline
    t2m = t2.merge(df, on="source_id", how="left")
    for inflate in (1.0, 1.15, 1.25):
        m = t2m["a_tr_margin"] * (BASE_INFLATE / inflate)
        n3 = int((m > 1).sum())
        print(f"S23's 177 class-III recovered as class III at "
              f"inflate={inflate:.2f}: {n3}/177"
              f" (missing: {', '.join(str(s) for s in t2m.loc[~(m > 1), 'source_id'].head(8))}"
              f"{'...' if int((~(m > 1)).sum()) > 8 else ''})")
    t2m["margin_at_1p25"] = t2m["a_tr_margin"]
    out = t2m[["source_id", "s23_label", "m1_used", "m1_source", "amrf",
               "margin_at_1p25", "p_class3_mc", "cuts_core", "cuts_eb26",
               "significance", "goodness_of_fit"]]
    out.to_csv(os.path.join(OUT_DIR, "amrf_s23_crosscheck.csv"), index=False,
               lineterminator="\n")

    # MC-uncertainty sanity: our p3 vs their PIII on the shared sample
    both = j[np.isfinite(j["p_class3_mc"]) & np.isfinite(j["pIII"])
             & (j["m1_source"] == "binary_masses")]
    ours3 = both["p_class3_mc"] >= 0.999
    theirs3 = both["pIII"] >= 99.9
    print(f"P(classIII)>=99.9% agreement on shared sample (n={len(both)}): "
          f"ours {int(ours3.sum())}, S23 {int(theirs3.sum())}, "
          f"both {int((ours3 & theirs3).sum())} "
          f"(note: different boundary curves AND we ignore corr_vec, "
          f"so this is a consistency check, not an identity)")
    return j


def variant_table(df, eb):
    """Purity/completeness of class-III selection variants against the
    El-Badry 2026 astrometric follow-up verdicts."""
    ebj = eb.merge(df, on="source_id", how="left", suffixes=("_eb", ""))
    missing = ebj[ebj["amrf"].isna()]
    if len(missing):
        print(f"WARNING: {len(missing)} EB26 sources not in our pull: "
              f"{missing['source_id'].tolist()}")

    confirmed = ebj["verdict"] == "CONFIRMED"
    spurious = ebj["verdict"] == "SPURIOUS"
    n_conf, n_spur = int(confirmed.sum()), int(spurious.sum())

    variants = []
    for inflate in (1.0, 1.15, 1.25):
        for sig_min in (0.0, 5.0, 10.0, 20.0):
            for gof_mode in ("none", "flat10", "magsplit"):
                variants.append((inflate, sig_min, gof_mode))

    def gof_pass(sub, mode):
        gof = sub["goodness_of_fit"]
        if mode == "none":
            return pd.Series(True, index=sub.index)
        if mode == "flat10":
            return gof < 10.0
        bright = sub["phot_g_mean_mag"] < 13.0
        return np.where(bright, gof < 6.0, gof < 4.0)

    rows = []
    for inflate, sig_min, gof_mode in variants:
        m = ebj["a_tr_margin"] * (BASE_INFLATE / inflate)
        sel = (m > 1) & ebj["cuts_core"].fillna(False) \
            & (ebj["significance"] > sig_min) & gof_pass(ebj, gof_mode)
        # DR3-wide candidate count under the same variant
        mall = df["a_tr_margin"] * (BASE_INFLATE / inflate)
        sel_all = (mall > 1) & df["cuts_core"] \
            & (df["significance"] > sig_min) & gof_pass(df, gof_mode)
        rows.append({
            "inflate": inflate, "sig_min": sig_min, "gof": gof_mode,
            "n_class3_dr3": int(sel_all.sum()),
            "conf_kept": int((sel & confirmed).sum()),
            "conf_total": n_conf,
            "spur_kept": int((sel & spurious).sum()),
            "spur_total": n_spur,
            "completeness": round(float((sel & confirmed).sum()) / n_conf, 3),
            "fp_passrate": round(float((sel & spurious).sum()) / n_spur, 3),
        })
    vt = pd.DataFrame(rows)
    vt.to_csv(os.path.join(OUT_DIR, "amrf_cut_variants.csv"), index=False,
              lineterminator="\n")
    print("\n--- cut variants vs El-Badry 2026 verdicts "
          f"(confirmed n={n_conf}, spurious n={n_spur}) ---")
    print(vt.to_string(index=False))
    return vt, ebj


def freeze_config(vt):
    """Pick and write the frozen DR4 config with its measured operating point."""
    pick = vt[(vt["inflate"] == 1.15) & (vt["sig_min"] == 10.0)
              & (vt["gof"] == "magsplit")].iloc[0]
    cfg = {
        "_comment": "Frozen M2 DR4-day-one AMRF triage config. Sources: "
                    "Shahaf+19 (MNRAS 487,5610) eq.4/6; Shahaf+23 (MNRAS 518,"
                    "2991) Halbwachs vetting + sigma_TI; El-Badry+26 "
                    "(arXiv:2608.06453) significance/F2 discriminators; "
                    "calibration in gaia-dr4/M2-amrf-triage.md.",
        "solution_types_dr4": ["Orbital", "OrbitalPoorlyConstrained",
                               "OrbitalAlternative", "AstroSpectroSB1",
                               "AstroSpectroSB2"],
        "period_days": [10.0, 2200.0],
        "period_note": "DR4 baseline ~66 mo = 2011 d; DR3 validation used "
                       "1500 d. BH2 (P=1352 d) proves P<1000 d is too tight.",
        "nss_parallax_over_error_min": 3.0,
        "halbwachs_vetting": True,
        "sigma_ti2_max": 36.0,
        "m1_policy": ["nss_masses (DR4) / binary_masses (DR3) IsocLum",
                      "photometric EEM MS (CMD cut, no extinction corr)",
                      "evolved bracket 0.8-2.6 Msun, worst-case class"],
        "boundary": "Mamajek/EEM A_tr curve x inflate",
        "boundary_inflate": float(pick["inflate"]),
        "significance_min": float(pick["sig_min"]),
        "gof_cut": "F2 < 6 if G < 13 else F2 < 4 (El-Badry 2026)",
        "alias_flag_days": [330.0, 400.0],
        "ruwe_cut": "NONE -- high RUWE is the orbit signature (BH1 7.6, BH2 9.2)",
        "measured_on_dr3": {
            "n_class3_dr3": int(pick["n_class3_dr3"]),
            "eb26_completeness": float(pick["completeness"]),
            "eb26_spurious_passrate": float(pick["fp_passrate"]),
        },
        "followup_gate_not_selection": "G<15 (spectrograph feasibility)",
    }
    with open(CONFIG_OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    print(f"\nfroze {CONFIG_OUT}")
    print(json.dumps(cfg["measured_on_dr3"], indent=2))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else TRIAGE
    subset_mode = path != TRIAGE
    if subset_mode:
        print(f"SUBSET MODE ({path}): EB26/S23 per-source numbers valid; "
              f"'n_class3_dr3' counts cover ONLY the named subset; "
              f"config not frozen")
    df = pd.read_parquet(path)
    eb = pd.read_csv(EB26)
    s23_crosscheck(df)
    vt, _ = variant_table(df, eb)
    if not subset_mode:
        freeze_config(vt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
