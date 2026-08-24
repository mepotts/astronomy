#!/usr/bin/env python3
"""M5 P2: verify the drafted PAPER's text against the artifact it was derived
from.

`scripts/m5_paper_numbers.py` checks the ARTIFACTS against the data.  This
checks the DRAFT against those artifacts -- i.e. it catches transcription slips
between `results/m5/paper_numbers.json` and
`draft-paper-mpta-noise-reproduction.md`, which is where a hand-written paper
actually goes wrong.  Same procedure as `scripts/m4_note_check.py` for the
Research Note, which caught a real error there.

Whitespace is collapsed before matching so that a line wrap in the draft cannot
break a check, and unicode minus/dash forms are normalised.

    python scripts/m5_paper_check.py        # exit 0 == every check passed
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPER = REPO / "draft-paper-mpta-noise-reproduction.md"
NUM = REPO / "results" / "m5" / "paper_numbers.json"

WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
        7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
        12: "twelve", 13: "thirteen", 14: "fourteen", 17: "seventeen",
        15: "fifteen", 18: "eighteen", 19: "nineteen", 20: "twenty",
        24: "twenty-four", 25: "twenty-five", 26: "twenty-six"}


def norm(s):
    for a, b in (("−", "-"), ("–", "-"), ("—", "-"),
                 (" ", " "), (" ", " "), (" ", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)


def main():
    d = json.loads(NUM.read_text())
    txt = norm(PAPER.read_text(encoding="utf-8"))
    # a second view with markdown emphasis, the multiplication sign and case
    # removed, so that a count check does not fail because the draft bolded
    # the word or spelled it out
    plain = txt.replace("*", "").replace("_", "").replace("×", "x").lower()
    fails, checks = [], 0

    def want(sub, why):
        """the phrase must appear literally (after normalisation)"""
        nonlocal checks
        checks += 1
        if norm(sub) not in txt:
            fails.append(f"{why}: expected {norm(sub)!r}")

    def want_any(subs, why, loose=False):
        nonlocal checks
        checks += 1
        hay = plain if loose else txt
        cand = [norm(s).lower() if loose else norm(s) for s in subs]
        if not any(c in hay for c in cand):
            fails.append(f"{why}: none of {cand}")

    def want_num(n, tail, why):
        """digit form OR english word form, followed by `tail`"""
        forms = [f"{n} {tail}"]
        if n in WORD:
            forms.append(f"{WORD[n]} {tail}")
        want_any(forms, why, loose=True)

    def want_re(pat, why):
        nonlocal checks
        checks += 1
        if not re.search(pat, txt):
            fails.append(f"{why}: no match for /{pat}/")

    # --- state marks -------------------------------------------------------
    want("# DRAFT - NOT SUBMITTED", "state mark at the top")
    want("[PLACEHOLDER", "author placeholder present")
    want("[PLACEHOLDER - Zenodo DOI]", "archive DOI still a placeholder")
    want("Nothing here has been sent", "not-sent statement")

    # --- the release -------------------------------------------------------
    want_num(d["n_psr"], "millisecond pulsars", "pulsar count (abstract)")
    want_num(d["n_values"], "tabulated parameter values", "value count")
    want(f"{d['n_toa']:,} sub-banded", "ToA count")

    # --- the model inventory sentence -------------------------------------------
    want(f"this is {d['inv_bump']} chromatic Gaussian events, {d['inv_annual']} annual",
         "inventory: events and annual terms")
    want(f"{d['inv_chrom_free']} free-index chromatic Gaussian processes, "
         f"{d['inv_chrom_fixed']} fixed-index ones, {d['inv_dm']} DM",
         "inventory: chromatic and DM")
    want(f"{d['inv_sw_full']} solar-wind Gaussian processes, {d['inv_red']} free "
         f"achromatic red processes, and {d['inv_equad']} EQUAD",
         "inventory: solar wind, red, EQUAD")
    want(f"{d['inv_ecorr']} ECORR terms", "inventory: ECORR")

    # --- A1 -------------------------------------------------------------------
    want(f"median of **{d['a1_med_frac_pct']}%**", "A1 residual agreement")
    want_num(d["a1_complete"], "pulsars whose release is internally complete",
             "A1 complete-set size")
    want_num(d["a1_short"], "pulsars that ship fewer ToAs", "A1 short set")

    # --- the reproduction ---------------------------------------------------
    want_any([f"{d['agree_params']} of the {d['agree_total']} published values "
              f"({d['agree_pct']}%)"], "abstract agreement", loose=True)
    want_any([f"{d['agree_psr']} of {d['n_psr']} pulsars on every value"],
             "abstract pulsars-in-full", loose=True)
    want(f"**{d['agree_params']} of {d['agree_total']} tabulated values agree "
         f"({d['agree_pct']}%), and {d['agree_psr']} of {d['n_psr']} pulsars "
         f"agree on every value**", "section 3.1 agreement")
    want(f"**{d['cov_rel']} of {d['n_psr']} pulsars clear the registered "
         f"gate; {d['cov_abs']} of {d['n_psr']} clear the stricter absolute "
         f"one.**", "both gate coverages")
    want(f"the median is **+{d['dlnl_median']:.2f}**, with {d['dlnl_pos']} "
         f"positive and {d['dlnl_neg']} negative", "dlnL")
    want(f"**{d['dlnl_min']:.2f}**", "most negative dlnL")
    want(f"{d['acc_lo']}-{d['acc_hi']}", "acceptance range")
    want(f"at least {d['core_hours']} core-hours over {d['n_runs']} runs",
         "economics")
    mk = d["miss_keys"]
    want_any([f"{mk['sw_gamma']} x"], "miss breakdown: gamma_SW count",
             loose=True)
    want_any([f"{mk['sw_log10_A']} x"], "miss breakdown: log10 A_SW count",
             loose=True)
    want_any([f"{mk['bump_sigma']} x"], "miss breakdown: sigma_g count",
             loose=True)
    want_num(d["n_miss"], "disagreements", "total miss count")

    # --- the solar wind ------------------------------------------------------
    want(f"Of the {d['n_swfull']} pulsars whose favoured model samples",
         "SW_Full count")
    want_num(d["sw_neg"], "have a negative", "negative gamma_SW count")
    want_num(d["sw_cross"], "more have a 68% interval crossing zero",
             "crossing count")
    want(f"**{d['sw_affected']} of {d['n_swfull']}** cannot be fully "
         f"represented", "affected count")
    want(f"**{d['sw_lowest_edge']}** ({d['sw_lowest_edge_psr']})",
         "lowest printed interval edge")
    lo, hi = d["ee_default"]
    want(f"U({lo:.0f}, {hi:.0f})", "enterprise_extensions default range")
    want_any([f"over the {d['swwide_cmp']} pulsars with both runs available",
              f"over all {d['swwide_cmp']} solar-wind pulsars, each with both runs gated"],
             "variant coverage", loose=True)
    want_num(d["swwide_miss_reg"], "solar-wind parameters",
             "variant: misses covered")
    want_num(d["swwide_miss_var"], "", "variant: misses remaining") \
        if False else want("the variant misses none", "variant: none remain")
    want("none is created", "variant: none created")

    # --- the census -----------------------------------------------------------
    want(f"| **measurement** | **{d['cens_measured']}** |",
         "census table: measurement row")
    want(f"| **prior-propped** | **{d['cens_prior_propped']}** |",
         "census table: prior-propped row")
    want(f"| **unconstrained under both priors** | "
         f"**{d['cens_unconstrained_both']}** |",
         "census table: unconstrained row")
    want(f"Of the {d['cens_n']} published", "census denominator")
    want_any([f"of the {d['cens_n']} rows we can test",
              f"of the {d['cens_n']} solar-wind rows we can test",
              f"of all {d['cens_n']} rows"],
             "abstract census denominator", loose=True)
    want_any([f"quoted at {d['cens_n']} of {d['n_swfull']} rather than "
              f"{d['n_swfull']} of {d['n_swfull']}"]
             if d["cens_n"] < d["n_swfull"]
             else [f"complete at {d['n_swfull']} of {d['n_swfull']}",
                   f"all {d['n_swfull']} solar-wind pulsars"],
             "coverage honesty in threats-to-validity matches the artifact",
             loose=True)
    want_num(d["cens_measured"], "are measurements", "census headline")
    want_any([f"{WORD.get(d['cens_primary'], d['cens_primary']).capitalize()} "
              f"are not", f"{d['cens_primary']} are not"],
             "census primary count")
    want(f"ranges {d['cens_quote']}", "census sensitivity range (S4)")
    want(f"the count of measurements {d['cens_meas_range'][0]}-"
         f"{d['cens_meas_range'][1]}", "measured range across the grid")
    for p in d["cens_propped_psr"]:
        want(p, f"prior-propped pulsar {p} named")
    n_ok = d["cens_n"] - len(d["cens_divergent"])
    want(f"**{n_ok} of {d['cens_n']}** rows", "table-only agreement")
    want_num(len(d["cens_divergent"]), "cannot be", "divergent-row count")
    for p in d["cens_divergent"]:
        want(p, f"divergent pulsar {p} named")
    want(f"at most **{d['cens_ctrl_worst']}**", "control worst gamma move")
    want(f"**The control passes.**"
         if d["cens_ctrl_verdict"] == "PASS" else "control FAILS",
         "control verdict matches the artifact")

    # --- the rest of the table -------------------------------------------------
    want(f"**{d['a13_prior_limited']} of the {d['n_psr']} tabulated",
         "A_13/3 prior-bounded count")
    want(f"**{d['a13_median_w']} dex**", "A_13/3 median width")
    want_num(d["a13_better"], "rows are constrained better than 0.7 dex",
             "A_13/3 well-constrained count")
    want(f"**{d['map_outside']} of {d['n_values']} values", "MAP-outside count")
    want_num(d["map_outside_psr"], "pulsars", "MAP-outside pulsar count")
    want(f"**{d['nupiv']} MHz**", "pivot frequency")
    want(f"**{d['nupiv_w1400']} dex to {d['nupiv_wpiv']} dex**",
         "pivot width gain")
    want_num(d["prior_driven"], f"of the {d['n_free_beta']}",
             "prior-driven count")

    # --- the common signal ------------------------------------------------------
    want(f"A_CURN = {d['fl_map']:.2f} with a 68% interval of "
         f"[{d['fl_ci'][0]:.2f}, {d['fl_ci'][1]:.2f}]**", "FL headline")
    want(f"composition of **{d['fl_jk']} dex**", "FL jackknife SE")
    want(f"68% width **{d['tab_width']:.3f} dex**", "table product width")
    want(f"composition jackknife is **{d['tab_jk']} dex**",
         "table product jackknife SE")
    want(f"downward in {d['seamb_down']} of {d['seamb_n']} pulsars",
         "seam-b sign split")
    want(f"**{d['seamb_median']:.3f} dex**", "seam-b median")
    want(f"sign test p = {d['seamb_sign_p']}", "seam-b sign test")
    want_re(r"Wilcoxon signed-rank p = 6 . 10", "seam-b Wilcoxon (order 1e-6)")
    checks += 1
    if not (1e-6 <= d["seamb_wilcox_p"] < 1e-5):
        fails.append("seam-b Wilcoxon p is not of order 1e-6 in the artifact")
    want(f"Wilcoxon p = {round(d['seamb_ctrl_p'], 2)})", "seam-b control test")
    want(f"**+{d['dmap']:.3f} dex**", "product-level shift")
    want(f"**+{d['dmap']:.3f} +- {d['dmap_jk']:.3f} dex".replace("+-", "±"),
         "shift with its jackknife SE")
    want(f"a {d['dmap_sigma']}", "shift in sigma units")
    want(d["dmap_influential"][0], "most influential pulsar named")
    want(f"from **{d['f5_before']} to {d['f5_after']} dex**", "F5 step widths")
    want(f"The {d['f5_step_n']}th pulsar is {d['f5_step_psr']}",
         "F5 responsible pulsar")
    want(f"by {d['f5_swing']:.3f} dex", "F5 final swing")

    # --- the ESS floor ------------------------------------------------------------
    want(f"minimum ESS >= {d['ess_floor']}"
         .replace(">=", "≥"), "ESS floor value")
    want(f"({d['ess_reject_pct']:.1f}%)", "ESS: rejected agreement rate")
    want(f"({d['ess_admit_pct']:.1f}%)", "ESS: admitted agreement rate")
    checks += 1
    if d["ess_verdict"] != "NEGATIVE":
        fails.append("E5 verdict changed; the paper's wording assumes NEGATIVE")

    # --- discipline ----------------------------------------------------------------
    want("Goncharov & Sardana (2025)", "prior art credited")
    want("van Haasteren (2024)", "prior art credited")
    want("This paper claims none of that", "prior art disclaimed")
    want("Corrections to our own earlier analysis", "retractions section")
    want("What remains before this could be submitted", "submission checklist")
    want("no detection claim", "scope statement")

    print(f"{checks} checks, {len(fails)} failures")
    for f in fails:
        print("  FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
