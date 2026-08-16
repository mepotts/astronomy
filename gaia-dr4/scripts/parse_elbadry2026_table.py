#!/usr/bin/env python
"""M2: parse El-Badry et al. 2026 (arXiv:2608.06453) Table 'Astrometrically
selected Gaia DR3 compact-object candidates' from the paper's LaTeX source
(data/papers/2608.06453/astrometric_candidate_table.tex) into a fixture CSV.

The Notes column is mapped onto a calibration verdict:
  CONFIRMED  - many-epoch RVs validate the Gaia orbit and the companion is
               dark: 'Good solution', 'Solution OK; some residual scatter',
               Gaia BH1 / BH2 / NS1.
  MARGINAL   - 'RVs marginally consistent with astrometric orbit'.
  SPURIOUS   - 'RVs inconsistent with orbital solution' or
               'BH candidate ruled out by ...'.
  NOT_CO     - orbit may be real but companion is not a compact object
               (eclipsing-binary triples): 'EB with ...', 'Possible EB'.
  OTHER      - special primary (sdB; MS-based M1 invalid).
  UNKNOWN    - 'No RV follow-up' / 'RV follow-up incomplete'.

Output: fixtures/elbadry2026_astrometric_candidates.csv

Run   : .venv/Scripts/python.exe scripts/parse_elbadry2026_table.py
"""

import os
import re
import sys

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(BASE, "data", "papers", "2608.06453",
                   "astrometric_candidate_table.tex")
OUT = os.path.join(BASE, "fixtures", "elbadry2026_astrometric_candidates.csv")

ROW_RE = re.compile(
    r"(?P<und>\\underline\{)?\\texttt\{(?P<sid>\d+)\}\}?\s*&\s*"
    r"(?P<P>[\d.]+)\s*&\s*(?P<e>[\d.]+)\s*&\s*(?P<A>[\d.]+)\s*&\s*"
    r"(?P<M1>[\d.]+)\s*&\s*(?P<M2>[\d.]+)\s*&\s*(?P<sig>[\d.]+)\s*&\s*"
    r"(?P<G>[\d.]+)\s*&\s*(?P<EBV>[\d.]+)\s*&\s*(?P<spec>[^&]*)&\s*"
    r"(?P<notes>.*?)\s*\\\\"
)


def clean_tex(s: str) -> str:
    s = re.sub(r"\\citep?\{[^}]*\}", "", s)
    s = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", s)
    s = s.replace("{", "").replace("}", "").replace("$", "").replace("\\,", " ")
    s = s.replace("\\rm", "").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def verdict(notes: str) -> str:
    n = notes.lower()
    if "gaia bh1" in n or "gaia bh2" in n or "gaia ns1" in n:
        return "CONFIRMED"
    if "good solution" in n or "solution ok" in n:
        return "CONFIRMED"
    if "marginally consistent" in n:
        return "MARGINAL"
    if "inconsistent with orbital solution" in n or "ruled out" in n:
        return "SPURIOUS"
    if n.startswith("eb with") or "possible eb" in n:
        return "NOT_CO"
    if "sdb" in n:
        return "OTHER"
    if "no rv follow-up" in n or "follow-up incomplete" in n:
        return "UNKNOWN"
    raise ValueError(f"unmapped note: {notes!r}")


def main():
    rows = []
    with open(TEX, encoding="utf-8") as fh:
        for line in fh:
            m = ROW_RE.search(line)
            if not m:
                continue
            notes = clean_tex(m.group("notes"))
            rows.append({
                "source_id": int(m.group("sid")),
                "period_d": float(m.group("P")),
                "ecc": float(m.group("e")),
                "amrf_eb26": float(m.group("A")),
                "m1_phot_eb26": float(m.group("M1")),
                "m2_phot_eb26": float(m.group("M2")),
                "significance": float(m.group("sig")),
                "g_mag": float(m.group("G")),
                "ebv": float(m.group("EBV")),
                "many_epoch_followup": bool(m.group("und")),
                "spectroscopy": clean_tex(m.group("spec")),
                "notes": notes,
                "verdict": verdict(notes),
            })
    df = pd.DataFrame(rows)
    assert len(df) == 76, f"expected 76 rows, parsed {len(df)}"
    assert df["source_id"].is_unique
    df.to_csv(OUT, index=False, lineterminator="\n")
    print(f"Wrote {OUT}: {len(df)} rows")
    print(df["verdict"].value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
