"""Summarize every M1 worker outcome without rerunning science."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    runs = {}
    for stage in ("fetch", "catalog", "analyze"):
        path = ROOT / "data/m1" / f"{stage}-run.json"
        runs[stage] = {"sha256": digest(path), **json.loads(path.read_bytes())}
    controls = []
    for tic in (450781262, 53206761, 2041210548):
        record = {"tic": tic, "workers": {stage: next(row for row in value["outcomes"] if row["tic"] == tic)
                                           for stage, value in runs.items()}}
        path = ROOT / "out" / f"m1-{tic}.json"
        if path.exists():
            result = json.loads(path.read_bytes())
            record.update({"result_path": str(path.relative_to(ROOT)), "result_sha256": digest(path),
                           "status": result["status"], "primary": result["primary"],
                           "centroid_target_distance_pixels": result["centroid_target_distance_pixels"],
                           "flags": result["flags"]})
        else:
            record["status"] = "STOP_ANALYSIS_NO_RESULT"
        controls.append(record)
    output = {"status": "PARTIAL_CONTROL_CHARACTERIZATION_WITH_RETAINED_FAILURES",
              "unknown_search_authorized": False, "physical_depths_validated": False,
              "protocol_sha256": digest(ROOT / "M1-PROTOCOL-2026-09-12.md"),
              "scientific_source_sha256": digest(ROOT / "scripts/m1.py"),
              "summary_source_sha256": digest(Path(__file__)), "controls": controls,
              "run_receipts": {key: value["sha256"] for key, value in runs.items()}}
    destination = ROOT / "out/m1-summary.json"
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, indent=2)
        stream.write("\n")
    print(destination)


if __name__ == "__main__":
    main()
