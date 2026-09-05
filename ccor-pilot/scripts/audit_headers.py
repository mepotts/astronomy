"""Preserve a non-pixel audit of independent gates after the first gate stopped.

Does not overwrite the original frozen result or modify measurement criteria.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pilot


def main() -> None:
    from astropy.io import fits

    evidence_path = pilot.ROOT / "results/header-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence["spec_sha256"] != pilot.sha256(pilot.ROOT / "SPEC-2026-09-05.md"):
        raise pilot.PilotStop("STOP_SPEC_EVIDENCE_MISMATCH")
    audits = []
    for record in evidence["records"]:
        path = pilot.ROOT / "data/raw" / record["filename"]
        if pilot.sha256(path) != record["sha256"]:
            raise pilot.PilotStop("STOP_RAW_HASH_MISMATCH")
        with fits.open(path, memmap=False, lazy_load_hdus=True) as hdus:
            primary = dict(hdus[0].header)
            primary.pop("COMMENT", None)
            primary.pop("HISTORY", None)
            isviable_any_hdu = [
                i for i, hdu in enumerate(hdus) if "ISVIABLE" in hdu.header
            ]
        header = record["header"]
        try:
            flips = pilot.display_flips(header)
            wcs_outcome = "PASS_FLIP_ONLY_WCS"
        except pilot.PilotStop as exc:
            flips = None
            wcs_outcome = str(exc)
        audits.append(
            {
                "filename": record["filename"],
                "primary_header": primary,
                "hdu_indices_containing_ISVIABLE": isviable_any_hdu,
                "default_wcs_cross_axis_ratios": [
                    abs(header["PC1_2"] / header["PC1_1"]),
                    abs(header["PC2_1"] / header["PC2_2"]),
                ],
                "default_wcs_rotation_degrees": float(
                    np.degrees(np.arctan2(header["PC2_1"], header["PC1_1"]))
                ),
                "frozen_wcs_gate": wcs_outcome,
                "flip_xy_if_gate_passes": flips,
            }
        )
    output = {
        "purpose": "Post-stop header-only evidence enrichment; not a second recovery attempt",
        "header_evidence_sha256": pilot.sha256(evidence_path),
        "audit_script_sha256": pilot.sha256(Path(__file__)),
        "images_decompressed": 0,
        "audits": audits,
    }
    target = pilot.ROOT / "results/header-audit.json"
    if target.exists():
        raise pilot.PilotStop("STOP_EXISTING_HEADER_AUDIT")
    target.write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
