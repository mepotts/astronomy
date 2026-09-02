#!/usr/bin/env python3
"""M4: verify that the drafted note's own text and table agree with the
artifact they were derived from.

scripts/m4_note_numbers.py checks the ARTIFACT against the paper.  This checks
the NOTE against the artifact -- i.e. it catches transcription slips between
`results/m4/note_numbers.json` and `draft-rnaas-mpta-table-audit.md`, which is
where a hand-written note actually goes wrong.

    python scripts/m4_note_check.py
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTE = REPO / "draft-rnaas-mpta-table-audit.md"
NUM = REPO / "results" / "m4" / "note_numbers.json"

MINUS = "−"     # the note uses U+2212 MINUS SIGN in numbers and names


def norm(s):
    return s.replace(MINUS, "-").replace("–", "-").replace(
        "—", "-").replace(" ", " ")


def main():
    d = json.loads(NUM.read_text())
    txt = norm(NOTE.read_text(encoding="utf-8"))
    fails, checks = [], 0

    def want(substr, why):
        nonlocal checks
        checks += 1
        if substr not in txt:
            fails.append(f"{why}: expected to find {substr!r}")

    # headline counts
    want(f"{d['n_map_outside']} of {d['n_values']}", "claim (c) fraction")
    want(f"{d['n_pulsars_map_outside']} of 83 pulsars", "claim (c) pulsars")
    want(f"{d['n_a13_prior_limited']} of the 83 tabulated", "claim (d) count")
    want(f"{d['n_swfull']} pulsars whose favoured model", "SW_Full count")
    want("median width 3.01 dex", "A_13/3 median width")

    # the seven negative gamma_SW rows, value by value, in Table 1
    for psr, g in d["sw_negative"]:
        checks += 1
        pat = re.compile(r"\|\s*" + re.escape(psr) + r"\s*\|\s*"
                         + re.escape(f"{g:.2f}") + r"\s*\|")
        if not pat.search(txt):
            fails.append(f"Table 1 row {psr}: gamma_SW {g:.2f} not found")

    # the six best-constrained A_13/3 rows and their widths
    for r in d["a13_best"]:
        checks += 1
        s = f"{r['psr']} ({r['width']:.2f})"
        if s not in txt:
            fails.append(f"claim (d) best-row {s!r} not in the note")

    # the enterprise_extensions default and the lowest interval edge
    checks += 1
    lo, hi = d["ee_sw_gamma_default"]
    if f"U({lo:.0f}, {hi:.0f})" not in txt.replace("U(-2, 1)", "U(-2, 1)"):
        fails.append(f"e_e default U({lo:.0f}, {hi:.0f}) not quoted")
    want(f"{d['sw_gamma_lowest_ci_edge']:.2f}", "lowest gamma_SW interval edge")

    # J1825-0319
    checks += 1
    if "-0.45" not in txt:
        fails.append("J1825-0319 implied companion mass -0.45 not in the note")

    # every number in the note's own word-count claim
    m = re.search(r"reference list: ([\d,]+)\*\*", txt)
    if m:
        checks += 1
        stated = int(m.group(1).replace(",", ""))
        start = txt.index("**Title:**")
        end = txt.index("### Table 1")
        body = re.sub(r"[*#>`]", "", txt[start:end])
        actual = len(body.split())
        if abs(actual - stated) > 5:
            fails.append(f"word count says {stated}, measured {actual}")

    print(f"{checks} note-vs-artifact checks, {len(fails)} FAILED")
    for f in fails:
        print("  FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
