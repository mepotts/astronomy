"""M3: regenerate the full-row appendix of J0944-decision-package.md.

Reads out/j0944_rows.json and rewrites everything below the
FULL-ROWS-BELOW marker with the complete DR2 Main (250 cols), DR2 Hard
(111 cols) and DR1 (252 cols) rows as two-pairs-per-line markdown tables.
Idempotent: safe to re-run after regenerating the JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "J0944-decision-package.md"
MARKER = "<!-- FULL-ROWS-BELOW"


def fmt(v) -> str:
    if v is None:
        return "NaN"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        if v == 0:
            return "0"
        if abs(v) >= 1e5 or abs(v) < 1e-3:
            return f"{v:.6g}"
        return f"{v:.6g}"
    return str(v) if str(v).strip() else "(empty)"


def table(row: dict) -> list[str]:
    items = list(row.items())
    out = ["| column | value | column | value |", "|---|---|---|---|"]
    for i in range(0, len(items), 2):
        chunk = items[i:i + 2]
        cells = []
        for k, v in chunk:
            cells += [f"`{k}`", fmt(v)]
        while len(cells) < 4:
            cells += ["", ""]
        out.append("| " + " | ".join(cells) + " |")
    return out


def main() -> None:
    rows = json.load(open(ROOT / "out" / "j0944_rows.json", encoding="utf-8"))
    text = DOC.read_text(encoding="utf-8")
    head, sep, _ = text.partition(MARKER)
    assert sep, "marker not found in J0944-decision-package.md"
    marker_line = text[len(head):text.index("\n", len(head))]

    parts = [head + marker_line, ""]
    for title, key in [
            ("DR2 Main row (`eRASS3_Main_v1.3.fits`, all 250 columns)",
             "dr2_main_row"),
            ("DR2 Hard row (`eRASS3_Hard_v1.2.fits`, all 111 columns)",
             "dr2_hard_row"),
            ("DR1 row (`eRASS1_Main.v1.2.fits`, all 252 columns)", "dr1_row")]:
        parts.append(f"### {title}")
        parts.append("")
        parts += table(rows[key])
        parts.append("")
    DOC.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"appendix regenerated ({len(rows['dr2_main_row'])} + "
          f"{len(rows['dr2_hard_row'])} + {len(rows['dr1_row'])} columns)")


if __name__ == "__main__":
    main()
