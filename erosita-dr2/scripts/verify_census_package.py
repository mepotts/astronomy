"""Offline verification of the scoped vanished-source publication package.

Uses only the census, steady controls, and declared aggregate selection count.
This is an artifact/text consistency check, not independent confirmation of faders.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def classify(row, cut):
    presence = float(row["ul_presence"])
    # Empty geometric fields mean no matching neighbour, as in the original CSV.
    def distance(key):
        return float(row[key]) if row[key] else math.inf

    if distance("in_dr2_any_sep") <= 15:
        return "ARTIFACT-SPLIT/MOVED"
    if presence <= 0.01:
        return "INDETERMINATE-HALO"
    if presence > cut:
        if distance("nn2_bright_sep_arcsec") <= 120:
            return "ARTIFACT-CONFUSION"
        if distance("next_sep_arcsec") <= 120:
            return "ARTIFACT-EXTENDED"
        return "ARTIFACT-UNCLEAR-PERSIST"
    if distance("nn2_bright_sep_arcsec") <= 40:
        return "CONFUSED-IDENTITY"
    return "FADE-CANDIDATE"


def audit(root):
    rows = read_rows(root / "out/m2_vanished_forensics.csv")
    controls = read_rows(root / "out/m5w_faint_validation.csv")
    stats = json.loads((root / "out/w2_stats.json").read_text(encoding="utf-8"))
    fail = []
    checks = []

    def check(name, actual, expected):
        okay = actual == expected
        checks.append(dict(name=name, actual=actual, expected=expected, passed=okay))
        if not okay:
            fail.append(name)

    check("census rows", len(rows), 261)
    check("unique census identifiers", len({r["IAUNAME"] for r in rows}), 261)
    check("finite nonnegative presence", all(math.isfinite(float(r["ul_presence"]))
          and float(r["ul_presence"]) >= 0 for r in rows), True)
    check("classification replay", sum(classify(r, 1.5) != r["forensic_class_v2"]
          for r in rows), 0)
    counts = Counter(r["forensic_class_v2"] for r in rows)
    check("faders", counts["FADE-CANDIDATE"], 107)
    check("indeterminate", counts["INDETERMINATE-HALO"] + counts["CONFUSED-IDENTITY"], 6)
    check("artifacts", sum(n for key, n in counts.items() if key.startswith("ARTIFACT")), 148)
    for cut, number in [(1.3, 99), (2.0, 124)]:
        check(f"threshold {cut}", sum(classify(r, cut) == "FADE-CANDIDATE" for r in rows), number)
    cp = [float(r["ul_presence"]) for r in controls]
    check("controls", len(cp), 60)
    check("finite control values", all(math.isfinite(p) and p > 0 for p in cp), True)
    check("controls below cut", sum(p <= 1.5 for p in cp), 0)
    check("control minimum", round(min(cp), 2), 2.03)
    check("control median", round(statistics.median(cp), 2), 2.60)
    check("control maximum", round(max(cp), 2), 3.78)
    check("bright parent count (stored aggregate)", stats["n_dr1_clean_detlike30"], 118253)
    check("candidate selection percent", round(107 / stats["n_dr1_clean_detlike30"] * 100, 2), 0.09)
    for threshold, artifacts, indeterminate in [(100, 19, 1), (242, 5, 1)]:
        bright = [r for r in rows if float(r["DET_LIKE_0"]) > threshold]
        check(f"artifacts above {threshold}",
              sum(r["forensic_class_v2"].startswith("ARTIFACT") for r in bright), artifacts)
        check(f"indeterminate above {threshold}",
              sum(r["forensic_class_v2"] in ["INDETERMINATE-HALO", "CONFUSED-IDENTITY"]
                  for r in bright), indeterminate)
    draft = (root / "draft-rnaas-vanished-census.md").read_text(encoding="utf-8")
    normalized_draft = " ".join(draft.split())
    for phrase in ["treating every unmatched eRASS1 source as", "variability is not considered",
                   "fewer than 6 of", "sources genuinely switched off", "Gaia DSC class",
                   "no DR2 counterpart at all", "its dominant systematic is the presence threshold"]:
        check(f"withdrawn phrase absent: {phrase}", phrase in normalized_draft, False)
    return dict(schema_version=1, checks=checks, failure_count=len(fail),
                steady_control_error_95ul=1 - 0.05 ** (1 / len(cp)),
                selected_candidate_contamination=None,
                confirmed_physical_faders=None,
                scope="stored-artifact consistency; parent selection not regenerated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['checks'])} census-package checks; {result['failure_count']} failures")
    if result["failure_count"]:
        for row in result["checks"]:
            if not row["passed"]:
                print(row)
    return bool(result["failure_count"])


if __name__ == "__main__":
    raise SystemExit(main())
