#!/usr/bin/env python3
"""M6: every number in the composition-jackknife methods note, re-derived from
a committed artifact, with an audit table (claim -> value -> artifact -> field).

Same procedure as `m4_note_numbers.py` (the table-audit note) and
`m5_paper_numbers.py` (the paper).  No number is taken from prose, including
this repository's own prose.  `scripts/m6_methods_note_check.py` then checks the
DRAFTED TEXT back against this artifact.

    python scripts/m6_methods_note_numbers.py [--markdown]
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
M4 = REPO / "results" / "m4"
M5 = REPO / "results" / "m5"
M6 = REPO / "results" / "m6"
OUT = M6 / "methods_note_numbers.json"

rows = []


def add(key, claim, value, artifact, field):
    rows.append(dict(key=key, claim=claim, value=value,
                     artifact=artifact, field=field))
    return value


def main():
    M6.mkdir(parents=True, exist_ok=True)
    cs = json.loads((M5 / "curn_stability.json").read_text())
    sn = json.loads((M5 / "seamb_subset_null.json").read_text())
    gr = json.loads((M4 / "fl_growth_fl.json").read_text())

    d = {}
    A_CS = "results/m5/curn_stability.json"
    A_SN = "results/m5/seamb_subset_null.json"
    A_GR = "results/m4/fl_growth_fl.json"

    # --- the two products --------------------------------------------------
    for tag, label in (("fl", "favoured single-pulsar models"),
                       ("table", "every pulsar given a free red process")):
        p = cs[tag]
        d[f"{tag}_n"] = add(f"{tag}_n", f"{label}: pulsars in the product",
                            p["n"], A_CS, f"{tag}.n")
        d[f"{tag}_map"] = add(f"{tag}_map", f"{label}: MAP log10 A",
                              p["map"], A_CS, f"{tag}.map")
        d[f"{tag}_ci"] = add(f"{tag}_ci", f"{label}: 68% interval",
                             p["ci68"], A_CS, f"{tag}.ci68")
        d[f"{tag}_w"] = add(f"{tag}_w", f"{label}: 68% width (dex)",
                            p["ci68_width"], A_CS, f"{tag}.ci68_width")
        d[f"{tag}_jk"] = add(f"{tag}_jk", f"{label}: composition jackknife SE (dex)",
                             p["jackknife_se"], A_CS, f"{tag}.jackknife_se")
        d[f"{tag}_ratio"] = add(f"{tag}_ratio", f"{label}: SE / width",
                                round(p["jackknife_se"] / p["ci68_width"], 2),
                                A_CS, f"{tag}.jackknife_se / {tag}.ci68_width")

    # --- the difference of the two products --------------------------------
    jk = sn["jackknife"]
    d["dmap"] = add("dmap", "difference of the two products' modes (dex)",
                    sn["dmap_all"], A_SN, "dmap_all")
    d["dmap_n"] = add("dmap_n", "pulsars gated in both configurations",
                      sn["n_common"], A_SN, "n_common")
    d["dmap_jk"] = add("dmap_jk", "delete-1 jackknife SE of that difference (dex)",
                       jk["se"], A_SN, "jackknife.se")
    d["dmap_sigma"] = add("dmap_sigma", "the difference in units of its own jackknife SE",
                          round(sn["dmap_all"] / jk["se"], 1), A_SN,
                          "dmap_all / jackknife.se")
    d["f4"] = add("f4", "the pre-registered threshold it was tested against (dex)",
                  jk["f4_threshold"], A_SN, "jackknife.f4_threshold")
    infl = jk["most_influential"][0]
    d["infl_psr"] = add("infl_psr", "single pulsar whose removal moves it most",
                        infl[0], A_SN, "jackknife.most_influential[0]")
    d["infl_val"] = add("infl_val", "the difference with that pulsar removed (dex)",
                        infl[1], A_SN, "jackknife.most_influential[0]")

    # --- the random-thinning null ------------------------------------------
    nl = sn["null"]
    d["null_n"] = add("null_n", "random thinnings drawn", nl["n"], A_SN, "null.n")
    d["null_size"] = add("null_size", "pulsars per thinning", nl["size"], A_SN,
                         "null.size")
    d["null_sd"] = add("null_sd", "standard deviation of the difference over thinnings (dex)",
                       nl["sd"], A_SN, "null.sd")
    d["null_ci95"] = add("null_ci95", "95% band of the difference over thinnings",
                         nl["ci95"], A_SN, "null.ci95")
    d["null_pct"] = add("null_pct", "percentile of our own subset value in that band",
                        nl["percentile_of_ess_value"], A_SN,
                        "null.percentile_of_ess_value")
    d["dmap_ess"] = add("dmap_ess", "the difference on that particular subset (dex)",
                        sn["dmap_ess"], A_SN, "dmap_ess")

    # --- the growth curve ---------------------------------------------------
    curve = gr["curve"]
    step = max(range(1, len(curve)),
               key=lambda i: curve[i - 1]["width"] - curve[i]["width"])
    d["step_n"] = add("step_n", "addition at which the product leaves the prior rail",
                      curve[step]["n"], A_GR, "curve[].width, largest single drop")
    d["step_psr"] = add("step_psr", "the pulsar responsible", curve[step]["added"],
                        A_GR, "curve[].added")
    d["step_before"] = add("step_before", "68% width just before that step (dex)",
                           round(curve[step - 1]["width"], 2), A_GR, "curve[].width")
    d["step_after"] = add("step_after", "68% width just after (dex)",
                          round(curve[step]["width"], 2), A_GR, "curve[].width")
    pre = curve[:step]
    d["pre_w_lo"] = add("pre_w_lo", "narrowest 68% width before the step (dex)",
                        round(min(r["width"] for r in pre), 1), A_GR,
                        "curve[:step].width")
    d["pre_w_hi"] = add("pre_w_hi", "widest 68% width in that stretch (dex)",
                        round(max(r["width"] for r in pre), 1), A_GR,
                        "curve[:step].width")
    d["pre_map_lo"] = add("pre_map_lo", "lowest mode before the step",
                          round(min(r["map"] for r in pre), 1), A_GR,
                          "curve[:step].map")
    d["pre_map_hi"] = add("pre_map_hi", "highest mode before the step",
                          round(max(r["map"] for r in pre), 1), A_GR,
                          "curve[:step].map")
    d["swing10"] = add("swing10", "mode swing over the final ten additions (dex)",
                       round(gr["map_swing_last10"], 3), A_GR, "map_swing_last10")

    # --- the paired per-pulsar test ----------------------------------------
    sb = cs["seam_b_paired"]
    d["paired_n"] = add("paired_n", "pulsars where the two configurations differ",
                        sb["n_test"], A_CS, "seam_b_paired.n_test")
    d["paired_down"] = add("paired_down", "of those, moving DOWN", sb["n_down"],
                           A_CS, "seam_b_paired.n_down")
    d["paired_med"] = add("paired_med", "median per-pulsar shift (dex)",
                          round(sb["median"], 3), A_CS, "seam_b_paired.median")
    d["paired_sign_p"] = add("paired_sign_p", "sign-test p",
                             round(sb["sign_test_p"], 4), A_CS,
                             "seam_b_paired.sign_test_p")
    d["paired_wilcox_p"] = add("paired_wilcox_p", "Wilcoxon signed-rank p",
                               sb["wilcoxon_p"], A_CS, "seam_b_paired.wilcoxon_p")
    d["ctrl_n"] = add("ctrl_n", "control pulsars (same model twice)", sb["n_control"],
                      A_CS, "seam_b_paired.n_control")
    d["ctrl_med"] = add("ctrl_med", "control median shift (dex)", sb["control_median"],
                        A_CS, "seam_b_paired.control_median")
    d["ctrl_p"] = add("ctrl_p", "Wilcoxon p on the control set",
                      round(sb["control_wilcoxon_p"], 2), A_CS,
                      "seam_b_paired.control_wilcoxon_p")

    OUT.write_text(json.dumps(d, indent=1), encoding="utf-8")

    if "--markdown" in sys.argv:
        print("| # | claim | value | artifact | field |")
        print("|---|---|---|---|---|")
        for i, r in enumerate(rows, 1):
            print(f"| {i} | {r['claim']} | {r['value']} | `{r['artifact']}` | "
                  f"`{r['field']}` |")
    else:
        for i, r in enumerate(rows, 1):
            print(f"{i:3d} {r['claim']:66s} {r['value']}  <- {r['artifact']} : "
                  f"{r['field']}")
    print(f"\n{len(rows)} numbers -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
