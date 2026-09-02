#!/usr/bin/env python3
"""M5 P2: every number in the paper draft, re-derived from a committed
artifact, with an audit table (claim -> value -> artifact -> field).

This is the `m4_note_numbers.py` procedure applied to the paper.  It does NOT
take any number from prose -- including this repository's own prose.  Each row
names the artifact and field it came from, so a reader can open the file and
check it.  `scripts/m5_paper_check.py` then checks the DRAFTED TEXT back
against this artifact, which is where a hand-written paper actually goes wrong.

    python scripts/m5_paper_numbers.py
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
M3 = REPO / "results" / "m3"
M4 = REPO / "results" / "m4"
M5 = REPO / "results" / "m5"
OUT = M5 / "paper_numbers.json"

rows = []


def add(key, claim, value, artifact, field):
    rows.append(dict(key=key, claim=claim, value=value,
                     artifact=artifact, field=field))
    return value


def main():
    note = json.loads((M4 / "note_numbers.json").read_text())
    agree = json.loads((M4 / "agreement_both_gates.json").read_text())
    sw4 = json.loads((M4 / "swwide.json").read_text())
    grow = json.loads((M4 / "fl_growth_fl.json").read_text())
    cens = json.loads((M5 / "sw_census.json").read_text())
    ess = json.loads((M5 / "ess_floor.json").read_text())
    stab = json.loads((M5 / "curn_stability.json").read_text())
    null = json.loads((M5 / "seamb_subset_null.json").read_text())
    seama = json.loads((M3 / "seam_a.json").read_text())
    tab = json.loads((M3 / "published_table.json").read_text())

    # ---- the release -------------------------------------------------
    add("n_psr", "pulsars in the release", note["n_noise_rows"],
        "results/m4/note_numbers.json", "n_noise_rows")
    add("n_values", "tabulated parameter values with a printed interval",
        note["n_values"], "results/m4/note_numbers.json", "n_values")
    ntoa = 0
    for f in sorted((REPO / "data" / "partim").glob("*.tim")):
        ntoa += sum(1 for ln in f.read_text(errors="ignore").splitlines()
                    if ln[:1] not in ("", "#", "C", "F", "M") and
                    not ln.lstrip().upper().startswith(
                        ("FORMAT", "MODE", "INCLUDE", "JUMP", "EFAC", "EQUAD",
                         "TIME", "SKIP", "NOSKIP")))
    add("n_toa", "sub-banded ToAs in the release (counted from the 83 .tim)",
        ntoa, "data/partim/*.tim", "line count")

    # ---- the model inventory quoted in section 2.2 ---------------------
    m = {p: r["model"] for p, r in tab.items()}
    inv = dict(
        bump=sum(1 for v in m.values() if v.get("bump")),
        annual=sum(1 for v in m.values() if v.get("annual")),
        chrom_free=sum(1 for v in m.values() if v.get("chrom") == "free"),
        chrom_fixed=sum(1 for v in m.values()
                        if v.get("chrom") and v.get("chrom") != "free"),
        dm=sum(1 for v in m.values() if v.get("dm")),
        sw_full=sum(1 for v in m.values() if v.get("sw") == "full"),
        red=sum(1 for v in m.values() if v.get("red")),
        equad=sum(1 for v in m.values() if v.get("equad")),
        ecorr=sum(1 for v in m.values() if v.get("ecorr")))
    for k, label in (("bump", "chromatic Gaussian events"),
                     ("annual", "annual chromatic variations"),
                     ("chrom_free", "free-index chromatic GPs"),
                     ("chrom_fixed", "fixed-index chromatic GPs"),
                     ("dm", "DM GPs"), ("sw_full", "solar-wind GPs"),
                     ("red", "free achromatic red processes"),
                     ("equad", "EQUAD terms"), ("ecorr", "ECORR terms")):
        add(f"inv_{k}", f"model inventory: {label}", inv[k],
            "results/m3/published_table.json", f"model.{k}")

    # ---- A1: do our residuals reproduce the release's own? -------------
    a1 = json.loads((M3 / "a1_summary.json").read_text())["records"]
    comp = [v for v in a1.values() if v["ntoa"] == v["ntoa_pub"]]
    short = [v for v in a1.values() if v["ntoa"] != v["ntoa_pub"]]
    add("a1_complete", "pulsars whose release ships as many ToAs as its "
        "ephemeris was fitted to", len(comp), "results/m3/a1_summary.json",
        "records[].ntoa == ntoa_pub")
    add("a1_short", "pulsars that ship fewer ToAs than their ephemeris "
        "fitted", len(short), "results/m3/a1_summary.json", "records[]")
    add("a1_med_frac_pct", "median |wRMS - TRES| / TRES over the complete "
        "set (%)",
        round(100 * float(np.median([abs(v["frac"]) for v in comp])), 3),
        "results/m3/a1_summary.json", "records[].frac")

    # ---- the reproduction --------------------------------------------
    rel, ab = agree["relative"], agree["absolute"]
    add("cov_rel", "pulsars clearing the registered (relative) gate", rel["n"],
        "results/m4/agreement_both_gates.json", "relative.n")
    add("cov_abs", "pulsars clearing the absolute (M1-M3) gate", ab["n"],
        "results/m4/agreement_both_gates.json", "absolute.n")
    add("agree_params", "parameters agreeing under the registered A2 rule",
        rel["params_agree"], "results/m4/agreement_both_gates.json",
        "relative.params_agree")
    add("agree_total", "parameters compared", rel["params_total"],
        "results/m4/agreement_both_gates.json", "relative.params_total")
    add("agree_pct", "agreement rate (%)", round(rel["pct"], 1),
        "results/m4/agreement_both_gates.json", "relative.pct")
    add("agree_psr", "pulsars agreeing on every tabulated value",
        rel["n_full"], "results/m4/agreement_both_gates.json",
        "relative.n_full")
    add("n_miss", "parameters missing",
        rel["params_total"] - rel["params_agree"],
        "results/m4/agreement_both_gates.json", "derived")
    mk = agree["miss_keys"]
    add("miss_sw", "misses that are solar-wind parameters",
        sum(v for k, v in mk.items() if k.startswith("sw_")),
        "results/m4/agreement_both_gates.json", "miss_keys")
    add("miss_sigma_g", "misses that are the Gaussian-event width",
        sum(v for k, v in mk.items() if "sigma" in k or k.endswith("_s")),
        "results/m4/agreement_both_gates.json", "miss_keys")
    add("miss_keys", "the miss keys themselves", mk,
        "results/m4/agreement_both_gates.json", "miss_keys")
    d = agree["dlnl"]
    add("dlnl_median", "median dlnL(ours - published)", round(d["median"], 2),
        "results/m4/agreement_both_gates.json", "dlnl.median")
    add("dlnl_pos", "pulsars with dlnL > 0", d["n_pos"],
        "results/m4/agreement_both_gates.json", "dlnl.n_pos")
    add("dlnl_neg", "pulsars with dlnL < 0", d["n_neg"],
        "results/m4/agreement_both_gates.json", "dlnl.n_neg")
    add("dlnl_min", "most negative dlnL", round(d["min"], 2),
        "results/m4/agreement_both_gates.json", "dlnl.min")
    add("acc_lo", "lowest acceptance over gated runs", round(rel["acc_min"], 3),
        "results/m4/agreement_both_gates.json", "relative.acc_min")
    add("acc_hi", "highest acceptance over gated runs",
        round(rel["acc_max"], 3), "results/m4/agreement_both_gates.json",
        "relative.acc_max")

    # ---- the solar-wind prior ----------------------------------------
    add("n_swfull", "pulsars whose favoured model samples gamma_SW",
        note["n_swfull"], "results/m4/note_numbers.json", "n_swfull")
    add("sw_neg", "published gamma_SW values that are negative",
        note["n_sw_gamma_negative"], "results/m4/note_numbers.json",
        "n_sw_gamma_negative")
    add("sw_cross", "further rows whose 68% interval crosses zero",
        note["n_sw_gamma_ci_crossing"], "results/m4/note_numbers.json",
        "n_sw_gamma_ci_crossing")
    add("sw_affected", "rows outside or straddling gamma in [0,7]",
        note["n_sw_affected"], "results/m4/note_numbers.json", "n_sw_affected")
    add("sw_below_ee", "published values below the e_e U(-2,1) floor",
        note["n_sw_below_ee_default"], "results/m4/note_numbers.json",
        "n_sw_below_ee_default")
    add("sw_lowest_edge", "lowest printed gamma_SW 68% lower edge",
        note["sw_gamma_lowest_ci_edge"], "results/m4/note_numbers.json",
        "sw_gamma_lowest_ci_edge")
    add("sw_lowest_edge_psr", "the pulsar it belongs to",
        note["sw_gamma_lowest_ci_edge_psr"], "results/m4/note_numbers.json",
        "sw_gamma_lowest_ci_edge_psr")
    add("ee_default", "enterprise_extensions solar_wind_block gamma default",
        note["ee_sw_gamma_default"], "results/m4/note_numbers.json",
        "ee_sw_gamma_default")
    add("swwide_cmp", "SW_Full pulsars with both priors gated (M4 variant)",
        sw4["compared"], "results/m4/swwide.json", "compared")
    add("swwide_miss_reg", "campaign misses covered by the variant",
        sw4["n_miss_registered"], "results/m4/swwide.json",
        "n_miss_registered")
    add("swwide_miss_var", "misses remaining under U(-4,4)",
        sw4["n_miss_variant"], "results/m4/swwide.json", "n_miss_variant")
    add("swwide_created", "misses created by the wide prior",
        len(sw4["created"]), "results/m4/swwide.json", "created")

    # ---- the census (M5) ---------------------------------------------
    add("cens_n", "SW_Full pulsars in the census", cens["n_compared"],
        "results/m5/sw_census.json", "n_compared")
    for k in ("MEASURED", "PRIOR-PROPPED", "UNCONSTRAINED-BOTH", "OTHER"):
        add(f"cens_{k.lower().replace('-', '_')}", f"census class {k}",
            cens["counts"][k], "results/m5/sw_census.json", f"counts.{k}")
    add("cens_primary", "rows that are NOT a measurement of gamma_SW",
        cens["primary"], "results/m5/sw_census.json", "primary")
    add("cens_quote", "how the primary number must be quoted (S4 rule)",
        cens["sensitivity"]["quote"], "results/m5/sw_census.json",
        "sensitivity.quote")
    add("cens_meas_range", "MEASURED count across the sensitivity grid",
        cens["sensitivity"]["measured_range"], "results/m5/sw_census.json",
        "sensitivity.measured_range")
    add("cens_ctrl_n", "re-specified control set size", cens["control"]["n"],
        "results/m5/sw_census.json", "control.n")
    add("cens_ctrl_worst", "worst |d median gamma_SW| over the control set",
        cens["control"]["worst_d_gamma"], "results/m5/sw_census.json",
        "control.worst_d_gamma")
    add("cens_ctrl_verdict", "S2 control verdict", cens["control"]["verdict"],
        "results/m5/sw_census.json", "control.verdict")
    add("cens_tableonly", "rows the printed table alone already flags",
        cens["table_only"]["counts"]["U(-4,4)"], "results/m5/sw_census.json",
        "table_only.counts")
    add("cens_divergent", "rows the printed table alone CANNOT flag",
        cens["table_only"]["divergent"], "results/m5/sw_census.json",
        "table_only.divergent")
    pp = [r["psr"] for r in cens["rows"] if r["klass"] == "PRIOR-PROPPED"]
    add("cens_propped_psr", "the prior-propped pulsars", pp,
        "results/m5/sw_census.json", "rows[].klass")

    # ---- what the table constrains -----------------------------------
    add("a13_prior_limited", "A_13/3 rows whose 68% reaches below -16.5",
        note["n_a13_prior_limited"], "results/m4/note_numbers.json",
        "n_a13_prior_limited")
    add("a13_better", "A_13/3 rows constrained better than 0.7 dex",
        note["n_a13_better_than_0p7"], "results/m4/note_numbers.json",
        "n_a13_better_than_0p7")
    add("a13_median_w", "median 68% width of the prior-bounded A_13/3 rows",
        note["a13_median_width_prior_limited"],
        "results/m4/note_numbers.json", "a13_median_width_prior_limited")
    add("map_outside", "values whose MAP lies outside their own 68% interval",
        note["n_map_outside"], "results/m4/note_numbers.json", "n_map_outside")
    add("map_outside_psr", "pulsars affected", note["n_pulsars_map_outside"],
        "results/m4/note_numbers.json", "n_pulsars_map_outside")
    free = [r for r in seama if r["chrom"] == "free" and r.get("nu_pivot_MHz")]
    add("nupiv", "median decorrelating reference frequency (MHz)",
        int(round(np.median([r["nu_pivot_MHz"] for r in free]))),
        "results/m3/seam_a.json", "nu_pivot_MHz (free-beta rows)")
    add("nupiv_w1400", "median log10A_Chrom 68% width at 1400 MHz (dex)",
        round(float(np.median([r["width_A_1400"] for r in free])), 2),
        "results/m3/seam_a.json", "width_A_1400")
    add("nupiv_wpiv", "the same width at the pivot frequency (dex)",
        round(float(np.median([r["width_A_pivot"] for r in free])), 2),
        "results/m3/seam_a.json", "width_A_pivot")
    add("prior_driven", "free-beta chromatic pulsars that are prior-driven",
        sum(1 for r in seama if r["chrom"] == "free" and r.get("prior_driven")),
        "results/m3/seam_a.json", "prior_driven")
    add("n_free_beta", "free-beta chromatic pulsars",
        sum(1 for r in seama if r["chrom"] == "free"),
        "results/m3/seam_a.json", "chrom == free")

    # ---- the common signal -------------------------------------------
    add("fl_n", "pulsars in the fl factorised-likelihood product",
        stab["fl"]["n"], "results/m5/curn_stability.json", "fl.n")
    add("fl_map", "fl product MAP log10 A_CURN", stab["fl"]["map"],
        "results/m5/curn_stability.json", "fl.map")
    add("fl_ci", "fl product 68% interval", stab["fl"]["ci68"],
        "results/m5/curn_stability.json", "fl.ci68")
    add("fl_width", "fl product 68% width", stab["fl"]["ci68_width"],
        "results/m5/curn_stability.json", "fl.ci68_width")
    add("fl_jk", "fl product jackknife SE over pulsar composition",
        stab["fl"]["jackknife_se"], "results/m5/curn_stability.json",
        "fl.jackknife_se")
    add("tab_n", "pulsars in the table-configuration product",
        stab["table"]["n"], "results/m5/curn_stability.json", "table.n")
    add("tab_map", "table product MAP", stab["table"]["map"],
        "results/m5/curn_stability.json", "table.map")
    add("tab_ci", "table product 68% interval", stab["table"]["ci68"],
        "results/m5/curn_stability.json", "table.ci68")
    add("tab_width", "table product 68% width", stab["table"]["ci68_width"],
        "results/m5/curn_stability.json", "table.ci68_width")
    add("tab_jk", "table product jackknife SE over pulsar composition",
        stab["table"]["jackknife_se"], "results/m5/curn_stability.json",
        "table.jackknife_se")
    sb = stab["seam_b_paired"]
    add("seamb_n", "pulsars in the paired seam-(b) test", sb["n_test"],
        "results/m5/curn_stability.json", "seam_b_paired.n_test")
    add("seamb_down", "of those, moving DOWN", sb["n_down"],
        "results/m5/curn_stability.json", "seam_b_paired.n_down")
    add("seamb_median", "median per-pulsar shift (dex)", sb["median"],
        "results/m5/curn_stability.json", "seam_b_paired.median")
    add("seamb_sign_p", "sign-test p", float(f"{sb['sign_test_p']:.2g}"),
        "results/m5/curn_stability.json", "seam_b_paired.sign_test_p")
    add("seamb_wilcox_p", "Wilcoxon signed-rank p",
        float(f"{sb['wilcoxon_p']:.2g}"), "results/m5/curn_stability.json",
        "seam_b_paired.wilcoxon_p")
    add("seamb_ctrl_n", "control pulsars (same model twice)", sb["n_control"],
        "results/m5/curn_stability.json", "seam_b_paired.n_control")
    add("seamb_ctrl_p", "Wilcoxon p on the control set",
        round(sb["control_wilcoxon_p"], 3), "results/m5/curn_stability.json",
        "seam_b_paired.control_wilcoxon_p")
    add("dmap", "product-level shift (table - fl) on the common set",
        null["dmap_all"], "results/m5/seamb_subset_null.json", "dmap_all")
    add("dmap_n", "pulsars in that comparison", null["n_common"],
        "results/m5/seamb_subset_null.json", "n_common")
    add("dmap_jk", "delete-1 jackknife SE of that shift",
        null["jackknife"]["se"], "results/m5/seamb_subset_null.json",
        "jackknife.se")
    add("dmap_sigma", "the shift in units of its own jackknife SE",
        round(null["dmap_all"] / null["jackknife"]["se"], 1),
        "results/m5/seamb_subset_null.json", "derived")
    add("dmap_f4", "the registered F4 magnitude threshold",
        null["jackknife"]["f4_threshold"],
        "results/m5/seamb_subset_null.json", "jackknife.f4_threshold")
    add("dmap_influential", "single pulsar whose removal moves it most",
        null["jackknife"]["most_influential"][0],
        "results/m5/seamb_subset_null.json", "jackknife.most_influential")

    # F5
    cur = {c["n"]: c for c in grow["curve"]}
    step = max(((n, cur[n]["added"], cur[n - 1]["width"] - cur[n]["width"])
                for n in cur if n - 1 in cur), key=lambda z: z[2])
    add("f5_step_n", "addition at which the FL product leaves the prior rail",
        step[0], "results/m4/fl_growth_fl.json", "curve")
    add("f5_step_psr", "the pulsar responsible", step[1],
        "results/m4/fl_growth_fl.json", "curve")
    add("f5_before", "68% width just before that step (dex)",
        round(cur[step[0] - 1]["width"], 2), "results/m4/fl_growth_fl.json",
        "curve")
    add("f5_after", "68% width just after (dex)", round(cur[step[0]]["width"], 2),
        "results/m4/fl_growth_fl.json", "curve")
    add("f5_swing", "MAP swing over the final ten additions (dex)",
        grow["map_swing_last10"], "results/m4/fl_growth_fl.json",
        "map_swing_last10")

    # ---- the ESS floor ------------------------------------------------
    add("ess_floor", "the registered floor", ess["floor"],
        "results/m5/ess_floor.json", "floor")
    for v in ("noise", "table", "fl", "swwide"):
        c = ess["coverage"][v]
        add(f"ess_{v}", f"{v} runs gated / clearing the floor",
            [c["gated"], c["ess_ok"]], "results/m5/ess_floor.json",
            f"coverage.{v}")
    e5 = ess["e5_falsifier"]
    add("ess_admit_pct", "agreement rate over runs the floor ADMITS",
        e5["admitted"]["pct"], "results/m5/ess_floor.json",
        "e5_falsifier.admitted.pct")
    add("ess_reject_pct", "agreement rate over runs the floor REJECTS",
        e5["rejected"]["pct"], "results/m5/ess_floor.json",
        "e5_falsifier.rejected.pct")
    add("ess_verdict", "E5 falsifier verdict",
        e5["verdict"].split(" --")[0], "results/m5/ess_floor.json",
        "e5_falsifier.verdict")

    # ---- economics ----------------------------------------------------
    hours = 0.0
    nrun = 0
    for f in M3.glob("*.summary.json"):
        s = json.loads(f.read_text())
        if s.get("elapsed_min"):
            hours += s["elapsed_min"] / 60.0
            nrun += 1
    add("core_hours", "core-hours recorded on the final launch of each run",
        round(hours, 1), "results/m3/*.summary.json", "elapsed_min")
    add("n_runs", "runs with a recorded final launch", nrun,
        "results/m3/*.summary.json", "elapsed_min")

    # ---- M6: the remaining content numbers, so that "every number in the
    # ---- paper traces to an artifact" is literally true rather than nearly so.
    # A sweep of every numeric token in the paper body (M6 §5) found these
    # quoted in the text but absent from the audit above.
    seamb3 = json.loads((M3 / "seam_b.json").read_text())
    both = json.loads((M4 / "fl_both_gates.json").read_text())
    add("agree_pct_abs", "agreement rate under the absolute gate (%)",
        round(ab["pct"], 1), "results/m4/agreement_both_gates.json",
        "absolute.pct")

    # census class widths, as printed in the sec 4.3 table
    import statistics as _st
    for klass, key in (("MEASURED", "cls_measured_wA"),
                       ("PRIOR-PROPPED", "cls_propped_wA"),
                       ("UNCONSTRAINED-BOTH", "cls_unconstrained_wA"),
                       ("OTHER", "cls_other_wA")):
        rws = [r for r in cens["rows"] if r["klass"] == klass]
        add(key, f"census class {klass}: median log10A_SW 68% width, "
            f"U(0,7) -> U(-4,4)",
            [round(_st.median(r["wA_narrow"] for r in rws), 2),
             round(_st.median(r["wA_wide"] for r in rws), 2)],
            "results/m5/sw_census.json", f"rows[klass=={klass}].wA_*")

    byname = {r["psr"]: r for r in cens["rows"]}
    add("j1744_pub_gamma", "J1744-1134 published gamma_SW",
        byname["J1744-1134"]["pub_gamma"], "results/m5/sw_census.json",
        "rows[J1744-1134].pub_gamma")
    add("j1744_w", "J1744-1134 gamma_SW 68% width, U(0,7) -> U(-4,4)",
        [round(byname["J1744-1134"]["w_narrow"], 2),
         round(byname["J1744-1134"]["w_wide"], 2)],
        "results/m5/sw_census.json", "rows[J1744-1134].w_narrow/w_wide")
    for psr, key in (("J1614-2230", "j1614_pub_w"), ("J1744-1134", "j1744_pub_w"),
                     ("J1525-5545", "j1525_pub_w")):
        add(key, f"{psr} printed gamma_SW 68% width", byname[psr]["pub_w68"],
            "results/m5/sw_census.json", f"rows[{psr}].pub_w68")
    add("cens_ctrl_worst_logA",
        "worst |d median log10A_SW| over the control set",
        cens["control"]["worst_d_logA"], "results/m5/sw_census.json",
        "control.worst_d_logA")

    j1525 = json.loads((M3 / "J1525-5545_swwide_s1.summary.json").read_text())
    add("j1525_ess", "J1525-5545 minimum ESS on its swwide run",
        int(round(j1525["chain"]["ess_min"])),
        "results/m3/J1525-5545_swwide_s1.summary.json", "chain.ess_min")

    # growth curve: the stretch before the one-pulsar step
    cv = grow["curve"]
    stp = max(range(1, len(cv)),
              key=lambda i: cv[i - 1]["width"] - cv[i]["width"])
    pre = cv[:stp]
    add("f5_pre_w", "68% width range over the additions before the step (dex)",
        [round(min(r["width"] for r in pre), 1),
         round(max(r["width"] for r in pre), 1)],
        "results/m4/fl_growth_fl.json", "curve[:step].width")
    add("f5_pre_map", "mode range over the additions before the step",
        [round(min(r["map"] for r in pre), 1),
         round(max(r["map"] for r in pre), 1)],
        "results/m4/fl_growth_fl.json", "curve[:step].map")

    add("null_sd", "standard deviation of the shift over random thinnings (dex)",
        null["null"]["sd"], "results/m5/seamb_subset_null.json", "null.sd")
    add("dmap_ess", "the shift on the ESS-floored subset (dex)", null["dmap_ess"],
        "results/m5/seamb_subset_null.json", "dmap_ess")
    add("ctrl_bar_12", "per-pulsar control bar, 12 controls (dex)",
        null["control_bar"]["all"]["bar"], "results/m5/seamb_subset_null.json",
        "control_bar.all.bar")
    add("ctrl_bar_6", "per-pulsar control bar, 6 ESS-floored controls (dex)",
        null["control_bar"]["ess"]["bar"], "results/m5/seamb_subset_null.json",
        "control_bar.ess.bar")

    # the withdrawn M3 "width not shift" headline, and what it is now
    m3c = both["m3_common32"]["fl"]["ci68"]
    add("m3_fl_width32", "M3's 32-pulsar fl product 68% width (the withdrawn "
        "width headline) (dex)", round(m3c[1] - m3c[0], 2),
        "results/m4/fl_both_gates.json", "m3_common32.fl.ci68")
    add("fl_width83", "the same width at full coverage (dex)",
        round(stab["fl"]["ci68_width"], 2), "results/m5/curn_stability.json",
        "fl.ci68_width")
    add("j1600_delta", "J1600-3053 seam-b shift, whites held fixed (dex)",
        round([r for r in seamb3["rows"] if r["psr"] == "J1600-3053"][0]["delta"], 2),
        "results/m3/seam_b.json", "rows[J1600-3053].delta")
    add("nupiv_factor", "precision factor gained by re-quoting at the pivot",
        round(rows[[r["key"] for r in rows].index("nupiv_w1400")]["value"]
              / rows[[r["key"] for r in rows].index("nupiv_wpiv")]["value"], 1),
        "results/m3/seam_a.json", "width_A_1400 / width_A_pivot")

    r5 = agree["r5"]
    add("relonly_agree", "parameters agreeing on the pulsars admitted only by "
        "the relaxation", r5["only_agree"],
        "results/m4/agreement_both_gates.json", "r5.only_agree")
    add("relonly_total", "parameters compared on those pulsars", r5["only_total"],
        "results/m4/agreement_both_gates.json", "r5.only_total")
    add("f5_pre_n", "additions before the one-pulsar step", cv[stp]["n"] - 1,
        "results/m4/fl_growth_fl.json", "curve[].n at the step, minus one")
    add("seamb_ctrl_median", "median shift over the control pulsars (dex)",
        stab["seam_b_paired"]["control_median"],
        "results/m5/curn_stability.json", "seam_b_paired.control_median")
    add("sw_below_ee_values", "the published gamma_SW values below the "
        "enterprise_extensions floor of the day",
        sorted(v for _, v in note["sw_negative"]
               if v < note["ee_sw_gamma_default"][0]),
        "results/m4/note_numbers.json", "sw_negative, ee_sw_gamma_default")

    # historical claims quoted in section 7 as our own, superseded numbers
    add("hist_lowest_edge", "M3's pre-registered lowest printed gamma_SW edge, "
        "since corrected", -3.14, "M3-noise-criticism.md",
        "pre-registration 1.3 (superseded; see row 7)")
    add("hist_dmap_82", "M4's product-level shift as first reported (82 psr)",
        0.259, "M4-finish-the-array.md",
        "section B-2 (withdrawn; see row 9)")

    # criteria constants: these are registrations, not measurements, and the
    # committed artifact is the pre-registration document itself.
    add("gate_iters", "registered minimum post-burn iterations", 100000,
        "M3-noise-criticism.md", "section 1 (A1)")
    add("gate_iters_fw", "the same for the fixed-white variants", 50000,
        "M3-noise-criticism.md", "section 1 (A1)")
    add("acc_floor", "registered acceptance floor", 0.05,
        "M2-converge-scale.md", "acceptance floor")

    # ---- emit ---------------------------------------------------------
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({r["key"]: r["value"] for r in rows}
                              | {"_audit": rows}, indent=1))
    if "--markdown" in sys.argv:
        print("| # | claim | value | artifact | field |")
        print("|---|---|---|---|---|")
        for i, r in enumerate(rows, 1):
            v = r["value"]
            v = (json.dumps(v) if isinstance(v, (list, dict)) else str(v))
            v = v.replace("|", "\\|")
            if len(v) > 60:
                v = v[:57] + "..."
            print(f"| {i} | {r['claim']} | {v} | `{r['artifact']}` | "
                  f"`{r['field']}` |")
        return
    w = max(len(r["claim"]) for r in rows)
    print(f"{'#':>3} {'claim':{w}s}  value  <- artifact : field")
    for i, r in enumerate(rows, 1):
        v = r["value"]
        v = (json.dumps(v) if isinstance(v, (list, dict)) else str(v))
        if len(v) > 46:
            v = v[:43] + "..."
        print(f"{i:>3} {r['claim']:{w}s}  {v}  <- {r['artifact']} : {r['field']}")
    print(f"\n{len(rows)} numbers -> {OUT}")


if __name__ == "__main__":
    main()
