"""M14 input proofs, frozen-run contract, and prior-ledger deduplication."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pl = pytest.importorskip("polars")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m14_attribution as attribution
import m14_fit_audit as fit_audit
import m14_freeze_itf as freeze
import m14_prepare as prepare


def valid_gcs_item(name: str) -> dict[str, str]:
    return {
        "name": name,
        "bucket": prepare.GCS_BUCKET,
        "generation": "1787684133561106",
        "metageneration": "1",
        "size": "112384392",
        "md5Hash": base64.b64encode(b"0" * 16).decode("ascii"),
        "crc32c": "yhCxhw==",
        "etag": "etag-value",
        "timeCreated": "2026-08-25T18:55:33.606Z",
        "updated": "2026-08-25T18:55:33.606Z",
    }


def test_canonical_batch_metadata_binds_exact_name_generation_and_hash() -> None:
    name = prepare.canonical_partition_name("2026-08-24")
    parsed = prepare.parse_gcs_metadata({"items": [valid_gcs_item(name)]}, expected_name=name)
    assert parsed["name"] == name
    assert parsed["generation"] == "1787684133561106"
    assert parsed["bytes"] == 112_384_392
    assert parsed["md5_base64"] == base64.b64encode(b"0" * 16).decode("ascii")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda item: {},
        lambda item: {"items": []},
        lambda item: {"items": [item, dict(item)]},
        lambda item: {"items": [{**item, "name": item["name"] + ".part"}]},
        lambda item: {"items": [{**item, "size": "999"}]},
        lambda item: {"items": [{**item, "md5Hash": "not-base64"}]},
        lambda item: {"items": [{**item, "updated": "2999-01-01T00:00:00Z"}]},
    ],
)
def test_canonical_batch_metadata_fails_closed(mutate) -> None:
    name = prepare.canonical_partition_name("2026-08-24")
    item = valid_gcs_item(name)
    with pytest.raises(prepare.M14DataError):
        prepare.parse_gcs_metadata(mutate(item), expected_name=name)


def test_local_proof_recomputes_digest_and_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "input.bin"
    path.write_bytes(b"authenticated bytes")
    proof = prepare.file_hashes(path)
    assert prepare._verify_local_proof(path, proof)["sha256"] == proof["sha256"]
    path.write_bytes(b"tampered bytes")
    with pytest.raises(prepare.M14DataError):
        prepare._verify_local_proof(path, proof)


def test_batch_anatomy_measures_content_not_bytes(tmp_path: Path) -> None:
    path = tmp_path / "batch.parquet"
    pl.DataFrame(
        {
            "provid": ["2026 AA", "2026 AA", "2026 BB", "2020 CC", "2026 BB"],
            "permid": [None, None, None, "12345", None],
            "obstime": [1, 2, 3, 4, 5],
            "created_at": [10, 10, 10, 10, 10],
            "disc": ["*", None, "*", None, None],
        }
    ).write_parquet(path)
    objects, stats = prepare.batch_anatomy(path)
    assert objects == {"2026 AA", "2026 BB"}
    assert stats["observations"] == 5
    assert stats["with_provid"] == 5
    assert stats["unclassified_observations"] == 0
    assert stats["numbered_observations"] == 1
    assert stats["distinct_unnumbered_objects"] == 2
    assert stats["discovery_asterisks"] == 2


def test_batch_anatomy_rejects_any_designation_accounting_residue(
    tmp_path: Path,
) -> None:
    path = tmp_path / "residue.parquet"
    pl.DataFrame(
        {
            "provid": ["2026 AA", None],
            "permid": [None, "12345"],
            "obstime": [1, 2],
            "created_at": [10, 10],
            "disc": [None, None],
        }
    ).write_parquet(path)
    with pytest.raises(prepare.M14DataError, match="accounting residue"):
        prepare.batch_anatomy(path)


def test_batch_anatomy_rejects_missing_schema_and_empty_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.parquet"
    pl.DataFrame({"provid": ["2026 AA"]}).write_parquet(missing)
    with pytest.raises(prepare.M14DataError):
        prepare.batch_anatomy(missing)

    empty = tmp_path / "empty.parquet"
    pl.DataFrame(
        schema={
            "provid": pl.String,
            "permid": pl.String,
            "obstime": pl.Int64,
            "created_at": pl.Int64,
            "disc": pl.String,
        }
    ).write_parquet(empty)
    with pytest.raises(prepare.M14DataError):
        prepare.batch_anatomy(empty)


def test_prior_coverage_binds_orbit_aliases_ledgers_and_held_rows(
    tmp_path: Path, monkeypatch
) -> None:
    orbit_path = tmp_path / "old-orbits.parquet"
    pl.DataFrame(
        {
            "primary": ["2026 AA"],
            "matched_provids": [["2026 AB"]],
            "all_desigs": [["2026 AA", "2026 AC"]],
        }
    ).write_parquet(orbit_path)
    ledger_path = tmp_path / "old-ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "verdicts": [
                    {"orbit_desig": "2026 AA", "link_key": "lk-one"},
                    {"orbit_desig": "2026 DD", "link_key": "lk-two"},
                ],
                "held_from_m7": [
                    {"orbit_desig": "2026 EE", "link_key": "lk-held"}
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(prepare, "PRIOR_ORBIT_TABLES", (orbit_path,))
    monkeypatch.setattr(prepare, "PRIOR_LEDGERS", (ledger_path,))
    aliases, objects, pairs, sources = prepare.load_prior_coverage()
    assert aliases == {"2026 AA", "2026 AB", "2026 AC"}
    assert objects == {"2026 AA", "2026 DD", "2026 EE"}
    assert pairs == {
        ("2026 AA", "lk-one"),
        ("2026 DD", "lk-two"),
        ("2026 EE", "lk-held"),
    }
    assert sources["orbit_tables"][orbit_path.name]["rows"] == 1
    assert len(sources["ledgers"][ledger_path.name]["sha256"]) == 64


def test_prior_dedup_uses_current_alias_and_retains_alternate_orbit_collision() -> None:
    orbit_frame = pl.DataFrame(
        {
            "primary": ["2026 NEW"],
            "matched_provids": [["2026 OLD"]],
            "all_desigs": [["2026 NEW", "2026 OLD"]],
        }
    )
    matches = [
        {"orbit_desig": "2026 NEW", "link_key": "lk-exact"},
        {"orbit_desig": "2026 NEW", "link_key": "lk-alternate"},
        {"orbit_desig": "2026 NEW", "link_key": "lk-fresh"},
    ]
    prior = {("2026 OLD", "lk-exact"), ("2026 OTHER", "lk-alternate")}
    kept, stats = attribution.deduplicate_prior_pairs(matches, orbit_frame, prior)
    assert [row["link_key"] for row in kept] == ["lk-alternate", "lk-fresh"]
    assert kept[0]["prior_tracklet_alternate_orbit"] is True
    assert kept[1]["prior_tracklet_alternate_orbit"] is False
    assert stats == {
        "raw_real_matches": 3,
        "exact_prior_alias_link_pairs_removed": 1,
        "alternate_orbit_same_tracklet_retained": 1,
        "remaining": 2,
    }


def test_fit_checkpoint_is_atomic_and_fingerprint_bound(tmp_path: Path) -> None:
    path = tmp_path / "fit-state.json"
    records = {"orbit|link": {"fit_key": "orbit|link", "fit": {"status": "ok"}}}
    attribution.save_fit_state(path, records, "fingerprint-a")
    assert attribution.load_fit_state(path, "fingerprint-a") == records
    with pytest.raises(prepare.M14DataError):
        attribution.load_fit_state(path, "fingerprint-b")
    assert not list(tmp_path.glob(".fit-state.json.tmp-*"))


def test_m14_is_retired_and_proof_failures_are_nonzero() -> None:
    with pytest.raises(prepare.M14DataError, match="M14 is retired"):
        attribution.refuse_retired_m14_run()
    assert attribution.fit_stop_exit_code("trailing_100_pass_rate(0)_below_floor(20)") == 0
    assert attribution.fit_stop_exit_code("time_budget(90min)_after_50_fits") == 0
    assert attribution.fit_stop_exit_code("hard_cap_or_queue_exhausted") == 0
    assert attribution.fit_stop_exit_code("input_proof_failure_at_rank_2") == 1
    assert (
        attribution.fit_stop_exit_code(
            "refused_missing_pinned_tracklet_lines_at_rank_2"
        )
        == 1
    )


def test_strict_usage_gate_enforces_closed_count_interval() -> None:
    passing = {
        "gate_strict": {"passes": True},
        "trk_obs_total": 2,
        "trk_obs_used": 2,
    }
    assert attribution.passes_strict_fully_used(passing) is True
    assert attribution.passes_strict_fully_used({**passing, "trk_obs_used": 3}) is False
    assert attribution.passes_strict_fully_used({**passing, "trk_obs_used": -1}) is False
    assert attribution.passes_strict_fully_used({**passing, "trk_obs_used": None}) is False


def test_unknown_orbit_uncertainty_uses_fail_closed_sentinel() -> None:
    orbit = SimpleNamespace(
        primary_desig="2026 TEST",
        all_desigs=["2026 TEST"],
        epoch_mjd_tt=60_000.0,
        r0=SimpleNamespace(tolist=lambda: [1.0, 0.0, 0.0]),
        v0=SimpleNamespace(tolist=lambda: [0.0, 1.0, 0.0]),
        h_mag=20.0,
        g_slope=0.15,
        u_param=None,
        arc_days=2.0,
        n_obs=3,
        n_opp=1,
        normalized_rms=0.5,
        orbit_type="MBA",
    )
    row = prepare.orbit_row(orbit, matched=["2026 TEST"], source="test")
    assert row["u_param"] == prepare.UNKNOWN_U_PARAM
    assert row["u_param"] > 6


def test_future_contract_binds_effective_tracklet_and_obscode_inputs() -> None:
    declared = {
        path.relative_to(attribution.ROOT).as_posix()
        for path in attribution.code_proof_paths()
    }
    assert "scripts/m7_attribution.py" in declared
    assert "src/itf_linker/ingest/fetch.py" in declared
    assert "data/raw/ObsCodes.html" in declared
    assert "M14-PLAN.md" in declared


def test_frozen_input_manifest_rejects_tampered_file(tmp_path: Path) -> None:
    raw = tmp_path / "itf.txt.gz"
    parquet = tmp_path / "itf.parquet"
    raw.write_bytes(b"raw")
    parquet.write_bytes(b"parquet")
    document = {
        "schema": 1,
        "milestone": "M14",
        "snapshot_id": "20260902T062614Z",
        "raw": {"filename": raw.name, **prepare.file_hashes(raw)},
        "parquet": {"filename": parquet.name, **prepare.file_hashes(parquet)},
    }
    document["fingerprint"] = freeze.canonical_json_digest(document)
    manifest = tmp_path / "itf-input-manifest.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    assert freeze.validate_frozen(manifest)["snapshot_id"] == "20260902T062614Z"
    raw.write_bytes(b"changed")
    with pytest.raises(prepare.M14DataError):
        freeze.validate_frozen(manifest)


def test_obs80_cached_proof_is_identifier_and_digest_bound(
    tmp_path: Path, monkeypatch
) -> None:
    designation = "2026 TEST"
    block = (
        "     TEST001  C2026 01 01.00000 00 00 00.00 +00 00 00.0          20.0 V      500\n"
        "     TEST001  C2026 01 02.00000 00 00 01.00 +00 00 00.0          20.0 V      500\n"
    )
    path = attribution.obs80_cache_path(tmp_path, designation)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "requested_desig": designation,
                "fetched_utc": "2026-09-02T12:00:00Z",
                "sha256": hashlib.sha256(block.encode()).hexdigest(),
                "obs80": block,
            }
        ),
        encoding="utf-8",
    )
    # The synthetic lines need only exercise proof loading; parser behavior is covered
    # by the real ITF fixtures elsewhere.
    monkeypatch.setattr(attribution, "parse_line", lambda line, strict=False: object())
    assert attribution.get_obs80_proved(tmp_path, designation) == block.splitlines()
    document = json.loads(path.read_text(encoding="utf-8"))
    document["requested_desig"] = "different"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(prepare.M14DataError):
        attribution.get_obs80_proved(tmp_path, designation)


def test_fit_audit_detects_published_rows_inside_residual_selector(
    monkeypatch,
) -> None:
    rows = {
        "t1": SimpleNamespace(mjd=60_000.0, obscode="500", ra_deg=1.0, dec_deg=2.0),
        "t2": SimpleNamespace(mjd=60_000.0001, obscode="500", ra_deg=1.1, dec_deg=2.1),
        "p1": SimpleNamespace(mjd=60_000.00005, obscode="500", ra_deg=3.0, dec_deg=4.0),
    }
    monkeypatch.setattr(
        fit_audit, "parse_line", lambda line, strict=False: rows.get(line)
    )
    monkeypatch.setattr(fit_audit.m8v, "count_duplicates", lambda lines, published: 0)
    metrics = fit_audit.overlap_metrics(
        ["t1", "t2"],
        ["p1"],
        {
            "trk_obs_total": 2,
            "trk_obs_used": 3,
            "trk_obs_in_resids": 3,
            "gate_strict": {"passes": True},
        },
    )
    assert metrics["published_duplicates_2s_2arcsec"] == 0
    assert metrics["published_rows_in_residual_selector_window"] == 1
    assert metrics["used_exceeds_tracklet_total"] is True
    assert metrics["residuals_exceed_tracklet_total"] is True
    assert metrics["strict_and_fully_used_original"] is False


def test_fit_audit_historical_anchor_rejects_coedited_report_and_state(
    tmp_path: Path, monkeypatch
) -> None:
    report_path = tmp_path / "m14-attribution.json"
    state_path = tmp_path / "m14-fit-state.json"
    legacy_path = tmp_path / "m14-fit-audit-summary.json"
    report_path.write_text('{"report":"original"}', encoding="utf-8")
    state_path.write_text('{"state":"original"}', encoding="utf-8")
    frozen = {"fingerprint": "frozen-fingerprint"}
    legacy = {
        "schema": 1,
        "milestone": "M14",
        "audit_kind": "post_hoc_counts_only_fit_usage_audit",
        "snapshot_id": "snapshot",
        "run_fingerprint": "run-fingerprint",
        "input_proofs": {
            "attribution_report_sha256": fit_audit.digest_file(report_path),
            "fit_state_sha256": fit_audit.digest_file(state_path),
            "frozen_itf_fingerprint": "frozen-fingerprint",
        },
    }
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
    monkeypatch.setattr(fit_audit, "HISTORICAL_SNAPSHOT_ID", "snapshot")
    monkeypatch.setattr(fit_audit, "HISTORICAL_RUN_FINGERPRINT", "run-fingerprint")
    monkeypatch.setattr(
        fit_audit, "HISTORICAL_FROZEN_ITF_FINGERPRINT", "frozen-fingerprint"
    )
    monkeypatch.setattr(
        fit_audit, "HISTORICAL_ATTRIBUTION_SHA256", fit_audit.digest_file(report_path)
    )
    monkeypatch.setattr(
        fit_audit, "HISTORICAL_FIT_STATE_SHA256", fit_audit.digest_file(state_path)
    )
    monkeypatch.setattr(
        fit_audit, "HISTORICAL_LEGACY_AUDIT_SHA256", fit_audit.digest_file(legacy_path)
    )
    fit_audit.validate_historical_anchor(
        "snapshot", frozen, report_path, state_path, legacy_path
    )

    report_path.write_text('{"report":"co-edited"}', encoding="utf-8")
    state_path.write_text('{"state":"co-edited"}', encoding="utf-8")
    with pytest.raises(prepare.M14DataError, match="anchor digest mismatch"):
        fit_audit.validate_historical_anchor(
            "snapshot", frozen, report_path, state_path, legacy_path
        )
