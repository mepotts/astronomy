#!/usr/bin/env python3
"""Regenerate M5 section 6 (the paper's number-audit table) in place from
`results/m5/paper_numbers.json`, so the milestone document can never drift from
the artifact it quotes.

    python scripts/m5_refresh_audit_section.py
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "M5-ess-floor-sw-census-and-the-paper.md"
NUM = REPO / "results" / "m5" / "paper_numbers.json"
START = "## 6. P2 — the paper number audit"
END = "## 7. Economics"


def main():
    n = len(json.loads(NUM.read_text())["_audit"])
    table = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "m5_paper_numbers.py"),
         "--markdown"], capture_output=True, text=True, check=True,
        cwd=REPO).stdout.rstrip("\n")
    checks = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "m5_paper_check.py")],
        capture_output=True, text=True, cwd=REPO).stdout.strip()
    n_checks = checks.split()[0] if checks else "?"
    n_fail = checks.split(",")[1].split()[0] if "," in checks else "?"

    body = (
        f"{START} ({n} rows)\n\n"
        "Emitted by `scripts/m5_paper_numbers.py --markdown`, which re-derives every number in\n"
        "[`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md) from a\n"
        "committed artifact. No number in the paper is transcribed from prose, including this\n"
        "repository's own. `scripts/m5_paper_check.py` then checks the drafted text back against this\n"
        f"artifact: **{n_checks} checks, {n_fail} failures.**\n\n"
        f"{table}\n\n---\n\n")

    t = DOC.read_text(encoding="utf-8")
    i, j = t.index(START), t.index(END)
    # keep whatever separator precedes section 6
    DOC.write_text(t[:i] + body + t[j:], encoding="utf-8")
    print(f"section 6 refreshed: {n} rows, {n_checks} checks, {n_fail} failures")


if __name__ == "__main__":
    main()
