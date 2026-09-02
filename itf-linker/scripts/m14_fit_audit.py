"""Counts-only audit of M14's post-anatomy exploratory fit records.

M14 should have stopped at a two-row anatomy accounting residue. The later 0/100 record
is exploratory; this audit bounds its corrected diagnostic at 0--2/100. It does not rerun or
reclassify fits. It proves the frozen raw lines, exact local observatory-code bytes, and
cached published OBS80, then diagnoses duplicate/selector contamination. Only aggregate
counts are written; candidate identifiers never leave ignored ``data/m14/`` inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m8_verdicts as m8v
from m14_attribution import obs80_cache_path, passes_strict_fully_used
from m14_freeze_itf import M14_RUNS, canonical_json_digest, validate_frozen
from m14_prepare import (
    M14DataError,
    digest_file,
    iso_utc,
    utc_now,
    write_json_atomic,
)

from itf_linker.ingest.fetch import parse_obscodes
from itf_linker.link.assemble import tracklet_line_index
from itf_linker.mpc80 import parse_line

OBSCODES_PATH = ROOT / "data" / "raw" / "ObsCodes.html"
HISTORICAL_OBSCODES_SHA256 = (
    "db5a7cd013245585b26989394479cadfee0a8dfd116ac504ac2154ad32ce8377"
)
HISTORICAL_SNAPSHOT_ID = "20260902T062614Z"
HISTORICAL_RUN_FINGERPRINT = (
    "29051841a7c1c876115daa808d1d5d584d220190ec13b243b47deee5403f25fa"
)
HISTORICAL_FROZEN_ITF_FINGERPRINT = (
    "33db1c004b36430dc2ff50a9190d0e67b9dea9ed02521d4cf10c702d15313f61"
)
HISTORICAL_ATTRIBUTION_SHA256 = (
    "3925d644a7a7fa42fb58a87447cbc563f148e31d3fd7ccbe20a33cb7b2dc304b"
)
HISTORICAL_FIT_STATE_SHA256 = (
    "98410b06efa56ff0ca5553527a62a0f8d96d8b9f93cebca684eb90e2e7fe20d2"
)
HISTORICAL_LEGACY_AUDIT_SHA256 = (
    "f2c9f2ccb7089b2910a526a93d9311ed08e0e4fefa151165ab9af9c341a3bc6f"
)
AUDIT_SOURCE_PATHS = (
    ROOT / "scripts" / "m14_fit_audit.py",
    ROOT / "scripts" / "m14_attribution.py",
    ROOT / "scripts" / "m8_verdicts.py",
    ROOT / "src" / "itf_linker" / "ingest" / "fetch.py",
    ROOT / "src" / "itf_linker" / "link" / "assemble.py",
    ROOT / "src" / "itf_linker" / "mpc80.py",
)


def load_obscodes_proved(
    path: Path = OBSCODES_PATH,
    *,
    expected_sha256: str = HISTORICAL_OBSCODES_SHA256,
) -> tuple[dict[str, float], dict[str, int | str]]:
    """Parse exact local bytes only; never invoke the network-capable cache loader."""

    if not path.is_file():
        raise M14DataError("M14 fit audit requires the exact local ObsCodes bytes")
    proof: dict[str, int | str] = {
        "bytes": path.stat().st_size,
        "sha256": digest_file(path),
    }
    if proof["sha256"] != expected_sha256:
        raise M14DataError("M14 fit audit ObsCodes digest disagrees with the historical run")
    longitudes = parse_obscodes(path.read_text(encoding="utf-8", errors="replace"))
    if not longitudes:
        raise M14DataError("M14 fit audit parsed no observatory longitudes")
    return longitudes, proof


def load_cached_obs80(cache: Path, designation: str) -> tuple[list[str], str]:
    """Load an existing request/digest-bound cache; this audit never goes online."""
    path = obs80_cache_path(cache, designation)
    if not path.is_file():
        raise M14DataError("M14 fit audit found no proved OBS80 cache for a completed fit")
    document = json.loads(path.read_text(encoding="utf-8"))
    block = document.get("obs80")
    if (
        document.get("schema") != 1
        or document.get("requested_desig") != designation
        or not isinstance(block, str)
        or not block.strip()
    ):
        raise M14DataError("M14 fit audit found a malformed OBS80 cache proof")
    digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
    if digest != document.get("sha256"):
        raise M14DataError("M14 fit audit found an OBS80 cache digest mismatch")
    return [line for line in block.splitlines() if line.strip()], digest_file(path)


def overlap_metrics(
    tracklet_lines: list[str],
    published_lines: list[str],
    fit: dict[str, Any],
) -> dict[str, Any]:
    tracklet = [item for item in (parse_line(line, strict=False) for line in tracklet_lines) if item]
    published = [item for item in (parse_line(line, strict=False) for line in published_lines) if item]
    if not tracklet or not published:
        raise M14DataError("M14 fit audit requires parseable tracklet and published astrometry")
    station = tracklet[0].obscode
    if any(item.obscode != station for item in tracklet):
        raise M14DataError("M14 candidate tracklet unexpectedly spans observatory codes")
    jd_low = min(item.mjd for item in tracklet) + 2400000.5 - 2e-4
    jd_high = max(item.mjd for item in tracklet) + 2400000.5 + 2e-4
    published_in_selector = sum(
        1
        for item in published
        if item.obscode == station and jd_low <= item.mjd + 2400000.5 <= jd_high
    )
    duplicates = m8v.count_duplicates(tracklet_lines, published)
    total = len(tracklet)
    used = fit.get("trk_obs_used")
    in_residuals = fit.get("trk_obs_in_resids")
    return {
        "tracklet_total_reparsed": total,
        "fit_tracklet_total": fit.get("trk_obs_total"),
        "fit_tracklet_used": used,
        "fit_tracklet_in_residuals": in_residuals,
        "published_duplicates_2s_2arcsec": duplicates,
        "published_rows_in_residual_selector_window": published_in_selector,
        "full_published_duplicate": duplicates >= total,
        "partial_published_duplicate": 0 < duplicates < total,
        "used_exceeds_tracklet_total": isinstance(used, int) and used > total,
        "residuals_exceed_tracklet_total": (
            isinstance(in_residuals, int) and in_residuals > total
        ),
        "strict_pass": bool((fit.get("gate_strict") or {}).get("passes")),
        "strict_and_fully_used_original": passes_strict_fully_used(fit),
    }


def validate_historical_anchor(
    snapshot_id: str,
    frozen: dict[str, Any],
    report_path: Path,
    state_path: Path,
    legacy_audit_path: Path,
) -> dict[str, str]:
    """Bind the post-run diagnostic to the preserved first-audit byte hashes.

    This anchor was created after the procedural anatomy STOP and is not pre-run
    provenance. It only prevents a mutually consistent edit of the report and
    checkpoint from silently changing the historical diagnostic.
    """

    if snapshot_id != HISTORICAL_SNAPSHOT_ID:
        raise M14DataError("M14 fit audit only authenticates the preserved historical run")
    if not legacy_audit_path.is_file():
        raise M14DataError("M14 fit audit requires the preserved first-audit anchor")
    proofs = {
        "legacy_audit_sha256": digest_file(legacy_audit_path),
        "attribution_report_sha256": digest_file(report_path),
        "fit_state_sha256": digest_file(state_path),
    }
    expected = {
        "legacy_audit_sha256": HISTORICAL_LEGACY_AUDIT_SHA256,
        "attribution_report_sha256": HISTORICAL_ATTRIBUTION_SHA256,
        "fit_state_sha256": HISTORICAL_FIT_STATE_SHA256,
    }
    if proofs != expected:
        raise M14DataError("M14 historical report/checkpoint anchor digest mismatch")
    legacy = json.loads(legacy_audit_path.read_text(encoding="utf-8"))
    legacy_inputs = legacy.get("input_proofs") or {}
    if (
        legacy.get("schema") != 1
        or legacy.get("milestone") != "M14"
        or legacy.get("audit_kind") != "post_hoc_counts_only_fit_usage_audit"
        or legacy.get("snapshot_id") != HISTORICAL_SNAPSHOT_ID
        or legacy.get("run_fingerprint") != HISTORICAL_RUN_FINGERPRINT
        or frozen.get("fingerprint") != HISTORICAL_FROZEN_ITF_FINGERPRINT
        or legacy_inputs.get("frozen_itf_fingerprint")
        != HISTORICAL_FROZEN_ITF_FINGERPRINT
        or legacy_inputs.get("attribution_report_sha256")
        != HISTORICAL_ATTRIBUTION_SHA256
        or legacy_inputs.get("fit_state_sha256") != HISTORICAL_FIT_STATE_SHA256
    ):
        raise M14DataError("M14 preserved first-audit anchor metadata disagrees")
    return proofs


def validate_historical_pairing(
    snapshot_id: str,
    frozen: dict[str, Any],
    report: dict[str, Any],
    state: dict[str, Any],
    fits: list[dict[str, Any]],
) -> None:
    if frozen.get("snapshot_id") != snapshot_id or report.get("snapshot_id") != snapshot_id:
        raise M14DataError("M14 fit audit snapshot identifiers disagree")
    contract = report.get("run_contract")
    if not isinstance(contract, dict):
        raise M14DataError("M14 fit audit report has no run contract")
    contract_source = {key: value for key, value in contract.items() if key != "fingerprint"}
    if canonical_json_digest(contract_source) != contract.get("fingerprint"):
        raise M14DataError("M14 fit audit run contract fingerprint does not reproduce")
    if (
        contract.get("fingerprint") != report.get("run_fingerprint")
        or contract.get("itf_fingerprint") != frozen.get("fingerprint")
        or state.get("run_fingerprint") != report.get("run_fingerprint")
    ):
        raise M14DataError("M14 fit audit input fingerprints disagree")
    records = state.get("records")
    if not isinstance(records, dict) or len(records) != len(fits):
        raise M14DataError("M14 fit report/checkpoint record counts disagree")
    fields = ("orbit_desig", "trksub", "obscode", "night", "link_key", "fit_tag")
    for fit_row in fits:
        fit_key = f"{fit_row['orbit_desig']}|{fit_row['link_key']}"
        record = records.get(fit_key)
        if not isinstance(record, dict) or record.get("fit_key") != fit_key:
            raise M14DataError("M14 fit report has no exact checkpoint record")
        if any(record.get(field) != fit_row.get(field) for field in fields):
            raise M14DataError("M14 fit report/checkpoint identity fields disagree")
        if record.get("fit") != fit_row.get("fit"):
            raise M14DataError("M14 fit report/checkpoint outcomes disagree")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    run_dir = M14_RUNS / args.snapshot_id
    report_path = run_dir / "m14-attribution.json"
    fit_state_path = run_dir / "m14-fit-state.json"
    legacy_audit_path = run_dir / "m14-fit-audit-summary.json"
    frozen_manifest_path = run_dir / "inputs" / "itf-input-manifest.json"
    if not report_path.is_file() or not fit_state_path.is_file():
        raise M14DataError("M14 fit audit requires the stopped attribution report/checkpoint")
    frozen = validate_frozen(frozen_manifest_path)
    historical_anchor = validate_historical_anchor(
        args.snapshot_id,
        frozen,
        report_path,
        fit_state_path,
        legacy_audit_path,
    )
    raw_itf = frozen_manifest_path.parent / frozen["raw"]["filename"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    fits = report.get("fits")
    if not isinstance(fits, list) or not fits:
        raise M14DataError("M14 attribution report contains no completed fits")
    fit_phase = report.get("fit_phase") or {}
    if fit_phase.get("stop_reason") != "trailing_100_pass_rate(0)_below_floor(20)":
        raise M14DataError("M14 fit audit expected the historical exploratory 0/100 record")
    state = json.loads(fit_state_path.read_text(encoding="utf-8"))
    validate_historical_pairing(args.snapshot_id, frozen, report, state, fits)

    longitudes, obscodes_proof = load_obscodes_proved()
    line_index, line_stats = tracklet_line_index(
        {fit["trksub"] for fit in fits}, longitudes, src=raw_itf
    )
    obs80_cache = run_dir / "obs80"
    metrics: list[dict[str, Any]] = []
    cache_proofs: list[str] = []
    for fit_row in fits:
        key = (fit_row["trksub"], fit_row["obscode"], fit_row["night"])
        tracklet_lines = line_index.get(key)
        if not tracklet_lines:
            raise M14DataError("M14 fit audit could not reproduce a frozen tracklet")
        published_lines, cache_digest = load_cached_obs80(
            obs80_cache, fit_row["orbit_desig"]
        )
        cache_proofs.append(cache_digest)
        metrics.append(overlap_metrics(tracklet_lines, published_lines, fit_row["fit"]))

    duplicate_classes = Counter()
    usage_classes = Counter()
    unpublished_fit_grade = 0
    usage_hold_count = 0
    for item in metrics:
        if item["full_published_duplicate"]:
            duplicate_classes["full"] += 1
        elif item["partial_published_duplicate"]:
            duplicate_classes["partial"] += 1
        else:
            duplicate_classes["none"] += 1
        if item["used_exceeds_tracklet_total"]:
            usage_classes["used_exceeds_total"] += 1
        elif item["fit_tracklet_used"] == item["tracklet_total_reparsed"]:
            usage_classes["used_equals_total"] += 1
        else:
            usage_classes["used_below_total"] += 1
        if (
            item["strict_and_fully_used_original"]
            and not item["full_published_duplicate"]
            and not item["partial_published_duplicate"]
            and item["published_rows_in_residual_selector_window"] == 0
        ):
            unpublished_fit_grade += 1
        if item["strict_pass"] and item["used_exceeds_tracklet_total"]:
            usage_hold_count += 1

    unique_cache_proofs = sorted(set(cache_proofs))
    combined_cache_digest = hashlib.sha256("".join(unique_cache_proofs).encode()).hexdigest()
    output: dict[str, Any] = {
        "schema": 1,
        "milestone": "M14",
        "audit_kind": "post_hoc_counts_only_fit_usage_audit",
        "generated_utc": iso_utc(utc_now()),
        "snapshot_id": args.snapshot_id,
        "run_fingerprint": report["run_fingerprint"],
        "input_proofs": {
            "attribution_report_sha256": digest_file(report_path),
            "fit_state_sha256": digest_file(fit_state_path),
            "preserved_post_run_anchor": historical_anchor,
            "frozen_itf_fingerprint": frozen["fingerprint"],
            "fit_to_obs80_cache_associations_verified": len(cache_proofs),
            "unique_proved_obs80_cache_files": len(unique_cache_proofs),
            "unique_obs80_cache_digest_set_sha256": combined_cache_digest,
            "obscodes": obscodes_proof,
            "audit_sources": {
                path.relative_to(ROOT).as_posix(): digest_file(path)
                for path in AUDIT_SOURCE_PATHS
            },
            "tracklets_indexed": line_stats.get("tracklets_indexed"),
        },
        "fits_audited": len(metrics),
        "fit_status": dict(Counter(str(fit["fit"].get("status")) for fit in fits)),
        "strict_gate_passes": sum(item["strict_pass"] for item in metrics),
        "strict_and_fully_used_original": sum(
            item["strict_and_fully_used_original"] for item in metrics
        ),
        "published_duplicate_class": dict(duplicate_classes),
        "usage_class": dict(usage_classes),
        "selector_window_contains_published_rows": sum(
            item["published_rows_in_residual_selector_window"] > 0 for item in metrics
        ),
        "residual_count_exceeds_tracklet_total": sum(
            item["residuals_exceed_tracklet_total"] for item in metrics
        ),
        "used_count_exceeds_tracklet_total": sum(
            item["used_exceeds_tracklet_total"] for item in metrics
        ),
        "fit_total_disagrees_with_reparsed_tracklet": sum(
            item["fit_tracklet_total"] != item["tracklet_total_reparsed"] for item in metrics
        ),
        "strict_fully_used_without_published_overlap": unpublished_fit_grade,
        "post_stop_diagnostic_fit_yield_bounds": {
            "lower": unpublished_fit_grade,
            "upper": unpublished_fit_grade + usage_hold_count,
            "denominator": len(metrics),
            "usage_hold_rows": usage_hold_count,
            "inferential_status": "POST_STOP_NONINFERENTIAL",
        },
        "decision": {
            "status": "STOP_HOLD",
            "valid_stop_gate": "anatomy_accounting_residue_two_rows",
            "exploratory_fit_yield": (
                f"{unpublished_fit_grade}_to_"
                f"{unpublished_fit_grade + usage_hold_count}_of_{len(metrics)}"
            ),
            "historical_recorded_fit_yield": "0_of_100_under_broken_counter",
            "usage_hold_rows": usage_hold_count,
            "candidate_queue_opened": False,
            "thresholds_changed": False,
            "submission_or_publication": False,
        },
        "interpretation": (
            "M8 joint_fit labels published and appended rows with one tag, then identifies "
            "tracklet residuals by station and a broad JD window. Published rows inside "
            "that window can therefore inflate or misassign trk_obs_in_resids/trk_obs_used; "
            "the bug can create false FAILs. Exact count logic bounds the post-stop "
            "diagnostic at 0--2/100 here; only the two above-total strict rows are HOLD. "
            "The earlier anatomy STOP still makes this noninferential."
        ),
        "required_repair": (
            "Before another discovery campaign, preserve row provenance through the fit "
            "input or match residuals one-to-one to exact appended observations; add overlap, "
            "duplicate, and used<=total regression tests. Also close anatomy accounting and "
            "bind every effective input in a newly preregistered future milestone."
        ),
        "identifiers_in_output": False,
    }
    output_path = run_dir / "m14-fit-audit-summary-v3.json"
    if output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        comparable_existing = {
            key: value for key, value in existing.items() if key != "generated_utc"
        }
        comparable_output = {
            key: value for key, value in output.items() if key != "generated_utc"
        }
        if comparable_existing != comparable_output:
            raise M14DataError("existing M14 fit-audit v3 summary disagrees; refusing overwrite")
    else:
        write_json_atomic(output_path, output)
    print(
        f"M14 counts-only fit audit: {len(metrics)} fits; "
        f"{output['used_count_exceeds_tracklet_total']} used-count anomalies; "
        f"{unpublished_fit_grade} historical strict+fully-used rows without published "
        "overlap; STOP/HOLD with a noninferential 0--2/100 diagnostic bound",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except M14DataError as error:
        print(f"M14 fit audit refused: {error}", file=sys.stderr)
        raise SystemExit(1) from error
