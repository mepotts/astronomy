"""Persist M1b failures, exact pixel replay and still-unresolved scientific gates."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = []
    for tic in (450781262, 53206761, 2041210548):
        path = ROOT / "out" / f"m1b-{tic}.json"
        result = json.loads(path.read_bytes())
        rows.append({"tic": tic, "paired_events": result["paired_events"],
                     "day_blocks": result["primary"]["blocks"], "primary": result["primary"],
                     "centroid_target_distance_pixels": result["centroid_target_distance_pixels"],
                     "bootstrap_radial_95_pixels": result["bootstrap_radial_95_pixels"],
                     "catalog_status": result["catalog"]["status"],
                     "catalog_competitors_within_one_pixel": len(result["catalog"].get("competitors_within_one_pixel", []))
                     if "rows_in_stamp" in result["catalog"] else None,
                     "pixel_replay_exact_match": result["pixel_replay_exact_match"], "flags": result["flags"]})
    retry = json.loads((ROOT / "out/m1b-retry-run.json").read_bytes())
    analysis = json.loads((ROOT / "out/m1b-analyze-run.json").read_bytes())
    summary = {"status": "PIXEL_CONTROLS_RECOVERED_CATALOG_CONFUSION_UNRESOLVED",
               "pixel_characterizations": 3, "clean_catalog_passes": 0,
               "unknown_search_authorized": False, "physical_depths_validated": False,
               "controls": rows, "metadata_retry_run": retry, "analysis_run": analysis,
               "remaining_requirements": ["independent target/neighbor association for all three fields",
                                          "measured-PRF and injected localization calibration",
                                          "empirical negative controls",
                                          "independent angular-resolution/photometric validation"]}
    path = ROOT / "out/m1b-summary.json"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    print(path)


if __name__ == "__main__":
    main()
