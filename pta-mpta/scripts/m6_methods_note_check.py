#!/usr/bin/env python3
"""M6: verify the drafted composition-jackknife METHODS NOTE against the
artifact it was derived from.

`scripts/m6_methods_note_numbers.py` checks the ARTIFACTS against the data;
this checks the DRAFT against those artifacts, i.e. it catches transcription
slips between `results/m6/methods_note_numbers.json` and
`draft-rnaas-composition-jackknife.md`.  Same procedure as
`scripts/m4_note_check.py` and `scripts/m5_paper_check.py`, and it earned its
keep the same way: it caught the growth-curve mode range, which the prose had
as -16.7 where the artifact says -17.1.

Whitespace is collapsed and unicode minus/dash forms normalised before matching,
so a line wrap cannot break a check.

    python scripts/m6_methods_note_check.py     # exit 0 == every check passed
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTE = REPO / "draft-rnaas-composition-jackknife.md"
NUM = REPO / "results" / "m6" / "methods_note_numbers.json"

RNAAS_WORD_LIMIT = 1500


def norm(s):
    for a, b in (("−", "-"), ("–", "-"), ("—", "-"),
                 (" ", " "), (" ", " "), (" ", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)


def main():
    d = json.loads(NUM.read_text())
    raw = NOTE.read_text(encoding="utf-8")
    txt = norm(raw)
    plain = txt.replace("*", "").replace("_", "").replace("×", "x").lower()
    fails, checks = [], 0

    def want(sub, why):
        nonlocal checks
        checks += 1
        if norm(sub) not in txt:
            fails.append(f"{why}: expected {norm(sub)!r}")

    def want_loose(sub, why):
        nonlocal checks
        checks += 1
        if norm(sub).lower() not in plain:
            fails.append(f"{why}: expected {norm(sub)!r}")

    # --- state marks --------------------------------------------------------
    want("# DRAFT - NOT SUBMITTED", "state mark at the top")
    want("[PLACEHOLDER", "author placeholder present")
    want("Nothing here has been sent", "not-sent statement")
    want("DRAFT - NOT SUBMITTED.** Submission would additionally need",
         "state section")

    # --- venue limits, as verified live -------------------------------------
    want("1,500 words or fewer", "RNAAS word limit quoted verbatim")
    want("no more than a single\nfigure or table (but not both)".replace("\n", " "),
         "RNAAS single-graphic limit quoted verbatim")
    want("journals.aas.org/research-notes", "venue source URL")
    want("verified live from the AAS site on 2026-08-24", "venue check dated")

    # --- the two products ---------------------------------------------------
    want(f"68% width is **{d['table_w']:.3f} dex**", "table product width")
    want(f"composition jackknife is **{d['table_jk']:.3f} dex**",
         "table product jackknife SE")
    want(f"**{d['table_ratio']:.2f}**", "table product ratio")
    want(f"the jackknife is **{d['fl_jk']:.3f} dex**", "fl product jackknife SE")
    want(f"a width of **{d['fl_w']:.3f} dex**", "fl product width")
    want(f"ratio of {d['fl_ratio']:.2f}", "fl product ratio")
    checks += 1
    if not (d["table_jk"] > d["table_w"]):
        fails.append("the note's headline assumes the table product's jackknife "
                     "SE EXCEEDS its own 68% width; the artifact no longer says so")

    # --- Table 1 rows -------------------------------------------------------
    want(f"| {d['fl_n']} | {d['fl_map']:.2f} | "
         f"[{d['fl_ci'][0]:.2f}, {d['fl_ci'][1]:.2f}] | {d['fl_w']:.3f} dex | "
         f"{d['fl_jk']:.3f} dex | {d['fl_ratio']:.2f} |", "Table 1: fl row")
    want(f"| {d['table_n']} | {d['table_map']:.2f} | "
         f"[{d['table_ci'][0]:.2f}, {d['table_ci'][1]:.2f}] | "
         f"**{d['table_w']:.3f} dex** | **{d['table_jk']:.3f} dex** | "
         f"**{d['table_ratio']:.2f}** |", "Table 1: table row")

    # --- the difference and its jackknife -----------------------------------
    want(f"threshold of **{d['f4']:.2f} dex**", "pre-registered threshold")
    want(f"measured **+{d['dmap']:.3f} dex**", "measured difference")
    want(f"**+{d['dmap']:.3f} ± {d['dmap_jk']:.3f} dex - {d['dmap_sigma']}σ**",
         "difference with its jackknife SE and sigma")
    want(d["infl_psr"].replace("-", "−"), "most influential pulsar named")
    want(f"**+{d['infl_val']:.3f} dex**", "difference with that pulsar removed")

    # --- the random-thinning null -------------------------------------------
    # the draft may spell the draw count out; accept either form
    checks += 1
    _forms = [f"{d['null_n']} random {d['null_size']}-of-{d['dmap_n']} thinnings",
              f"four hundred random {d['null_size']}-of-{d['dmap_n']} thinnings"]
    if not any(norm(f).lower() in plain for f in _forms):
        fails.append(f"thinning draw count and size: none of {_forms}")
    want(f"standard deviation of **{d['null_sd']:.3f} dex**", "thinning spread")
    want(f"[{d['null_ci95'][0]:.3f}, {d['null_ci95'][1]:.3f}]", "thinning 95% band")
    want(f"{d['null_pct']}th percentile", "percentile of our subset value")
    want(f"**+{d['dmap_ess']:.2f} dex**", "the subset value itself")

    # --- the growth curve ---------------------------------------------------
    want(f"**{d['step_n']}th** addition", "growth-curve step index")
    want(f"The {d['step_n']}th pulsar is {d['step_psr'].replace('-', chr(0x2212))}",
         "growth-curve pulsar named")
    want(f"**{d['step_before']:.2f} to {d['step_after']:.2f} dex**",
         "growth-curve widths either side of the step")
    want(f"{d['pre_w_lo']}-{d['pre_w_hi']} dex wide", "pre-step width range")
    want(f"between {d['pre_map_lo']} and {d['pre_map_hi']}", "pre-step mode range")
    want(f"**{d['swing10']:.3f} dex**", "mode swing over the last ten additions")

    # --- the paired per-pulsar test -----------------------------------------
    want(f"**down in {d['paired_down']} of\n{d['paired_n']}**".replace("\n", " "),
         "paired sign split")
    want(f"median **{d['paired_med']:.3f} dex**".replace("-", "−"),
         "paired median")
    want(f"sign test *p* = {d['paired_sign_p']}", "paired sign test")
    checks += 1
    if not re.search(r"Wilcoxon signed-rank\s*\n?\s*\*p\* = 5\.8 . 10", txt):
        fails.append("paired Wilcoxon p not quoted as 5.8 x 10^-6")
    checks += 1
    if not (1e-6 <= d["paired_wilcox_p"] < 1e-5):
        fails.append("paired Wilcoxon p is not of order 1e-6 in the artifact")
    want(f"the **{d['ctrl_n']}** pulsars", "control set size")
    want(f"median\n+{d['ctrl_med']}".replace("\n", " "), "control median")
    want(f"Wilcoxon *p* = {d['ctrl_p']}", "control Wilcoxon p")

    # --- scope and fairness --------------------------------------------------
    want("no detection, evidence or spatial-correlation claim", "scope statement")
    want("We withdraw the product-level magnitude", "our own withdrawal stated")
    want("It does not claim that any published factorised-likelihood amplitude is\nwrong"
         .replace("\n", " "), "no-error-claim statement")
    want("doi:10.57891/j0vh-5g31", "data release cited")
    want("Taylor, S. R., Simon, J., Schult, L., Pol, N. & Lamb, W. G. 2022",
         "factorised-likelihood reference has the correct author list")

    # --- the note's own word-count claim -------------------------------------
    m = re.search(r"reference list:\s*([\d,]+)\*\*", txt)
    checks += 1
    if not m:
        fails.append("no word-count claim found in the note")
    else:
        stated = int(m.group(1).replace(",", ""))
        start = raw.index("**Title:**")
        end = raw.index("### Table 1")
        body = re.sub(r"[*#>`]", "", raw[start:end])
        actual = len(body.split())
        if abs(actual - stated) > 5:
            fails.append(f"word count says {stated}, measured {actual}")
        checks += 1
        if actual > RNAAS_WORD_LIMIT:
            fails.append(f"note proper is {actual} words, over the RNAAS "
                         f"limit of {RNAAS_WORD_LIMIT}")

    # --- RNAAS allows one figure OR one table, not both ----------------------
    checks += 1
    n_tables = len(re.findall(r"\n### Table \d", raw))
    n_figs = len(re.findall(r"\n### Figure \d", raw))
    if n_tables + n_figs != 1:
        fails.append(f"RNAAS permits one figure or table; note has "
                     f"{n_tables} table(s) and {n_figs} figure(s)")

    print(f"{checks} methods-note-vs-artifact checks, {len(fails)} FAILED")
    for f in fails:
        print("  FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
