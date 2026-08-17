#!/usr/bin/env python
"""M3: assemble the v2 class-III candidate list = frozen M2 selection
+ dust-corrected M1 (task 2) + covariance-aware Pr(class III) (task 1).

Membership (dust lower bound = best estimate; the SFD upper bound lives in
out/dust_retriage.csv as *_upper columns):
  class_det_dust == 3  AND  cuts_eb26   ->  951 - 8 + 6 = 949 rows.

Covariance Pr:
  - rows whose M1 inputs are unchanged by dust (binary_masses tier, or
    photometric tiers with A_G below 0.01 mag) reuse
    data/dr3_corrvec_probs.parquet;
  - rows with dust-shifted M1 (or dust-switched tier, incl. the 6 new
    members) get a fresh MC via corrvec_probs.process_row with the
    dust-corrected G magnitude / tier; corr_vec for the 6 new members is
    mini-pulled (same query/format as scripts/pull_dr3_nss_corrvec.py).

Output: out/amrf_class3_candidates_v2.csv (M2 CSV column set + dust +
        covariance columns + provenance)
        queries/dr4-triage-config.v2.json (versioned; v1 untouched)
Run   : .venv/Scripts/python.exe scripts/build_v2_list.py
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corrvec_probs import process_row, SEED, NDRAW_MAIN
from pull_dr3_nss_corrvec import sync_votable, COLS, TYPES

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "out")
TRIAGE_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")
CORRVEC_PARQUET = os.path.join(BASE, "data", "dr3_nss_corrvec.parquet")
PROBS_PARQUET = os.path.join(BASE, "data", "dr3_corrvec_probs.parquet")
V2_CSV = os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv")
CONFIG_V2 = os.path.join(BASE, "queries", "dr4-triage-config.v2.json")

KEY = ["source_id", "nss_solution_type"]


def main():
    tri = pd.read_parquet(TRIAGE_PARQUET)
    dust = pd.read_csv(os.path.join(OUT_DIR, "dust_retriage.csv"))
    cv = pd.read_parquet(CORRVEC_PARQUET)
    probs = pd.read_parquet(PROBS_PARQUET)

    members = dust[(dust["class_det_dust"] == 3) & dust["cuts_eb26"]].copy()
    print(f"v2 membership: {len(members)} solution rows "
          f"(M2 had 951; dust moved out "
          f"{int(((dust['class_det'] == 3) & dust['cuts_eb26'] & (dust['class_det_dust'] != 3)).sum())}, "
          f"in {int(((dust['class_det'] != 3) & dust['cuts_eb26'] & (dust['class_det_dust'] == 3)).sum())})")

    # ---- corr_vec for members not in the M3 pull (the dust-ins) ----------
    have = set(map(tuple, cv[KEY].itertuples(index=False)))
    need = members[~members[KEY].apply(tuple, axis=1).isin(have)]
    if len(need):
        ids = sorted(set(need["source_id"].astype(np.int64)))
        print(f"mini-pull corr_vec for {len(ids)} new members...")
        q = (f"SELECT {', '.join(COLS)} FROM gaiadr3.nss_two_body_orbit "
             f"WHERE nss_solution_type IN ({TYPES}) "
             f"AND source_id IN ({','.join(str(x) for x in ids)})")
        tab = sync_votable(q)
        d = {}
        for c in COLS:
            if c == "corr_vec":
                d[c] = [np.asarray(r).astype(float).tolist() for r in tab[c]]
            elif c in ("source_id", "bit_index"):
                d[c] = np.asarray(tab[c]).astype(np.int64)
            elif c == "nss_solution_type":
                d[c] = [str(x) for x in tab[c]]
            else:
                col = np.ma.filled(tab[c].astype(float), np.nan) \
                    if hasattr(tab[c], "mask") else np.asarray(tab[c], float)
                d[c] = col
        mini = pd.DataFrame(d)
        mini["is_validation_sample"] = False
        cv = pd.concat([cv, mini], ignore_index=True)
        print(f"  got {len(mini)} rows")

    cv_k = cv.set_index(KEY)
    tri_k = tri.set_index(KEY)
    probs_k = probs.set_index(KEY)

    # ---- per-member Pr: reuse or recompute -------------------------------
    rows = []
    t0 = time.time()
    n_recomputed = 0
    for m in members.to_dict("records"):
        key = (m["source_id"], m["nss_solution_type"])
        dust_changed = (m["m1_source_dust"] != m["m1_source"]) or \
            (m["m1_source_dust"] == "photometric_ms"
             and m["a_g_lower"] > 0.01)
        if not dust_changed and key in probs_k.index:
            p = probs_k.loc[key]
            rows.append({**{k: m[k] for k in KEY},
                         "p_class3_corr": p["p_class3_corr"],
                         "sigma_A_corr": p["sigma_A_corr"],
                         "pr_provenance": "task1_mc"})
            continue
        # recompute with dust-corrected inputs
        cvrow = cv_k.loc[key]
        if isinstance(cvrow, pd.DataFrame):
            cvrow = cvrow.iloc[0]
        cvrow = dict(cvrow)
        cvrow["source_id"], cvrow["nss_solution_type"] = key
        tri_row = tri_k.loc[key]
        if isinstance(tri_row, pd.DataFrame):
            tri_row = tri_row.iloc[0]
        tri_mod = tri_row.copy()
        tri_mod["m1_source"] = m["m1_source_dust"]
        tri_mod["m1_used"] = m["m1_dust"]
        tri_mod["m1_sigma"] = 0.10 * m["m1_dust"] \
            if np.isfinite(m["m1_dust"]) else np.nan
        tri_mod["phot_g_mean_mag"] = tri_row["phot_g_mean_mag"] \
            - m["a_g_lower"]
        rng = np.random.default_rng(
            [SEED, int(key[0]) & 0xFFFFFFFF, int(key[0]) >> 32,
             len(key[1])])
        r = process_row(cvrow, tri_mod, NDRAW_MAIN, rng)
        n_recomputed += 1
        rows.append({**{k: m[k] for k in KEY},
                     "p_class3_corr": r.get("p_class3_corr", np.nan),
                     "sigma_A_corr": r.get("sigma_A_corr", np.nan),
                     "pr_provenance": "dust_recomputed"})
    pr = pd.DataFrame(rows)
    print(f"Pr attached: {len(pr)} rows ({n_recomputed} recomputed with "
          f"dust-corrected M1; {time.time()-t0:.0f}s)")

    # ---- assemble the CSV -----------------------------------------------
    m2cols = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates.csv"),
                         nrows=1).columns.tolist()
    base_cols = [c for c in m2cols if c not in ("m1_used", "m1_source")]
    v2 = members.merge(tri.reset_index()[
        [c for c in set(m2cols) | {"source_id", "nss_solution_type"}
         if c in tri.columns or c in KEY]],
        on=KEY, how="left", suffixes=("", "_tri"))
    v2 = v2.merge(pr, on=KEY, how="left")

    keep = ["source_id", "ra", "dec", "l", "b", "nss_solution_type",
            "period", "eccentricity", "a0_mas", "nss_parallax",
            "significance", "goodness_of_fit", "sigma_ti2",
            "phot_g_mean_mag", "bp_rp", "ruwe",
            "m1_dust", "m1_source_dust", "margin_dust",
            "m1_used", "m1_source", "class_det",
            "dust_tier", "a_g_lower", "a_g_upper", "class_det_dust_upper",
            "p_class3_mc", "p_class3_corr", "sigma_A_corr",
            "pr_provenance", "flag_alias_1yr", "flag_low_lat",
            "flag_sig_gt20"]
    for c in ("ra", "dec", "eccentricity", "a0_mas", "significance",
              "goodness_of_fit", "sigma_ti2", "ruwe", "p_class3_mc"):
        if c not in v2.columns and c + "_tri" in v2.columns:
            v2[c] = v2[c + "_tri"]
    # recompute q_min/m2_min with the dusted M1
    import amrf
    aval = amrf.amrf(v2["a0_mas"].values, v2["nss_parallax"].values,
                     np.where(np.isfinite(v2["m1_dust"]), v2["m1_dust"],
                              np.nan),
                     v2["period"].values)
    q = amrf.q_min_dark(np.where(np.isfinite(aval), aval, np.nan))
    v2["amrf_dust"] = aval
    v2["m2_min_dark_dust"] = q * v2["m1_dust"].values
    # evolved-bracket rows: keep the M2 worst-case values
    evb = v2["m1_source_dust"] == "evolved_bracket"
    v2.loc[evb, "amrf_dust"] = v2.loc[evb, "amrf"] \
        if "amrf" in v2.columns else np.nan
    v2.loc[evb, "m2_min_dark_dust"] = v2.loc[evb, "m2_min_dark"]
    keep = ["amrf_dust", "m2_min_dark_dust"] + keep
    keep = [c for c in keep if c in v2.columns]
    v2 = v2.sort_values("m2_min_dark_dust", ascending=False)
    v2[keep].to_csv(V2_CSV, index=False, lineterminator="\n")
    print(f"wrote {V2_CSV} ({len(v2)} rows)")

    top = v2[["source_id", "m2_min_dark_dust", "p_class3_corr",
              "m1_source_dust"]].head(5)
    print("top 5 by M2_min:")
    print(top.to_string(index=False))
    n999 = int((v2["p_class3_corr"] >= 0.999).sum())
    print(f"v2 priority tier Pr(III|corr) >= 99.9%: {n999} of {len(v2)}")

    # ---- versioned config -----------------------------------------------
    with open(os.path.join(BASE, "queries", "dr4-triage-config.json"),
              encoding="utf-8") as fh:
        v1 = json.load(fh)
    v2cfg = dict(v1)
    v2cfg["_comment"] = (
        "v2 (M3, 2026-08-16). Selection/screen IDENTICAL to v1 (frozen M2); "
        "adds the covariance-aware probability method and the extinction "
        "tier for photometric M1. v1 kept alongside; see "
        "gaia-dr4/M3-corrvec-rehearsal.md.")
    v2cfg["version"] = 2
    v2cfg["supersedes"] = "dr4-triage-config.json (v1, M2)"
    v2cfg["m1_policy"] = [
        "nss_masses (DR4) / binary_masses (DR3) IsocLum",
        "photometric EEM MS (CMD cut, extinction-corrected per "
        "extinction_tier -- v2 change)",
        "evolved bracket 0.8-2.6 Msun, worst-case class"]
    v2cfg["probability_method"] = {
        "covariance": "nss_two_body_orbit corr_vec via nsstools 0.1.12 "
                      "(PyPI) NssSource.covmat(); 6x6 block "
                      "(parallax, A,B,F,G, period)",
        "mc_draws": NDRAW_MAIN,
        "mc_seed": SEED,
        "priority_tier": "p_class3_corr >= 0.999",
        "note": "Pr threshold is a RANKING tier, not a cut: measured on "
                "EB26 it only removes confirmed systems (M3 doc sec. 1)."}
    v2cfg["extinction_tier"] = {
        "d_le_1250pc": "Edenhofer+23 3D (mean, integrated; all-sky)",
        "d_gt_1250pc": "bracketed: Edenhofer-to-edge (lower) vs SFD full "
                       "column x SF11 2.742 (upper); dust-ambiguous "
                       "flagged, Bayestar deliberately unused (unit chain)",
        "bands": "ZGR23 curve at Gaia EDR3 pivots: R_G=2.2732, "
                 "R_BP=3.0362, R_RP=1.6480, R_V=2.7791",
        "applies_to": "photometric-M1 tiers only (binary_masses/nss_masses "
                      "M1 is DPAC's, unchanged)"}
    v2cfg["measured_on_dr3"] = dict(v1.get("measured_on_dr3", {}))
    v2cfg["measured_on_dr3"].update({
        "n_class3_dr3_v2": int(len(v2)),
        "n_priority_pr999": n999,
        "dust_moved_out_lower": 8, "dust_moved_in_lower": 6})
    with open(CONFIG_V2, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(v2cfg, fh, indent=2)
    print(f"wrote {CONFIG_V2} (v1 untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
