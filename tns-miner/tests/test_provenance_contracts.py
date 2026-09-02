from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cache_contract import (  # noqa: E402
    canonical_digest,
    load_cache_contract,
    load_proved_output,
    validated_tag,
    write_cache,
)
from tns_snapshot import (  # noqa: E402
    SNAPSHOT_SCHEMA,
    datetime_to_jd,
    read_snapshot,
    rows_discovered_as_of,
)


class ProvenanceContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_tag_cache_requires_exact_window_and_digest(self):
        path = self.root / "pool_tonight.csv"
        contract = {"mjd_start": 61274.0, "mjd_end": 61277.0}
        write_cache(
            path,
            b"oid,ra\nZTF26x,1\n",
            kind="test_pool",
            contract=contract,
            row_count=1,
        )

        self.assertIsNotNone(
            load_cache_contract(
                path, kind="test_pool", expected_contract=contract
            )
        )
        with self.assertRaisesRegex(RuntimeError, "input mismatch"):
            load_cache_contract(
                path,
                kind="test_pool",
                expected_contract={"mjd_start": 61275.0, "mjd_end": 61278.0},
            )
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(RuntimeError, "digest mismatch"):
            load_cache_contract(
                path, kind="test_pool", expected_contract=contract
            )

    def test_run_tags_are_strict_portable_slugs(self):
        for tag in ("a", "20260902", "night_2026-09-02", "DCAP_group195"):
            self.assertEqual(validated_tag(tag), tag)

        invalid = (
            "", ".", "..", "../escape", "..\\escape", "a/b", "a\\b",
            " drive", "drive ", "a.b", "a:b", "_leading", "trailing-",
            "CON", "nul", "COM1", "x" * 65,
        )
        for tag in invalid:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                validated_tag(tag)

    def test_m1_candidate_partial_payload_cannot_reuse_old_summary(self):
        payload = self.root / "m1_candidates_same.csv"
        summary = payload.with_suffix(".json")
        history = {"object_inputs": {}}
        frozen = {"snapshot_id": "frozen"}
        current = {"snapshot_id": "current"}
        contract = {
            "contract_schema_version": 1,
            "tag": "same",
            "history_jd_ceiling": 2460000.5,
            "source_pool_summary_sha256": "a" * 64,
            "history_cache_provenance_sha256": canonical_digest(history),
            "frozen_tns_provenance_sha256": canonical_digest(frozen),
            "current_tns_provenance_sha256": canonical_digest(current),
        }
        proof = write_cache(
            payload,
            b"oid\nZTF26x\n",
            kind="m1_candidate_output",
            contract=contract,
            row_count=1,
        )
        summary.write_text(json.dumps({
            "tag": "same",
            "n_candidates": 1,
            "history_jd_ceiling": 2460000.5,
            "history_cache_provenance": history,
            "tns_snapshot_provenance": {
                "frozen_dedupe": frozen,
                "operational_current": current,
            },
            "candidate_output_provenance": proof,
        }), encoding="utf-8")
        load_proved_output(
            payload, summary, kind="m1_candidate_output"
        )

        payload.write_bytes(b"oid\n")
        with self.assertRaisesRegex(RuntimeError, "digest mismatch"):
            load_proved_output(
                payload, summary, kind="m1_candidate_output"
            )

    def test_m2_candidate_new_same_tag_proof_rejects_old_summary(self):
        payload = self.root / "m2_candidates_same.csv"
        summary = payload.with_suffix(".json")
        history = {"object_inputs": {}}
        xmatch = None
        frozen = {"snapshot_id": "frozen"}
        current = {"snapshot_id": "current"}
        old_contract = {
            "contract_schema_version": 1,
            "tag": "same",
            "history_jd_ceiling": 2460000.5,
            "source_pool_summary_sha256": "a" * 64,
            "history_cache_provenance_sha256": canonical_digest(history),
            "xmatch_provenance_sha256": canonical_digest(xmatch),
            "frozen_tns_provenance_sha256": canonical_digest(frozen),
            "current_tns_provenance_sha256": canonical_digest(current),
        }
        old_proof = write_cache(
            payload,
            b"oid\nZTF26old\n",
            kind="m2_candidate_output",
            contract=old_contract,
            row_count=1,
        )
        summary.write_text(json.dumps({
            "tag": "same",
            "n_candidates": 1,
            "history_jd_ceiling": 2460000.5,
            "history_cache_provenance": history,
            "xmatch_cache_provenance": xmatch,
            "tns_snapshot_provenance": {
                "frozen_dedupe": frozen,
                "operational_current": current,
            },
            "candidate_output_provenance": old_proof,
        }), encoding="utf-8")

        new_contract = {**old_contract, "source_pool_summary_sha256": "b" * 64}
        write_cache(
            payload,
            b"oid\nZTF26new\n",
            kind="m2_candidate_output",
            contract=new_contract,
            row_count=1,
        )
        with self.assertRaisesRegex(RuntimeError, "input mismatch"):
            load_proved_output(
                payload, summary, kind="m2_candidate_output"
            )

    def _snapshot(
        self,
        name: str,
        *,
        ceiling: float,
        observed_offset: float = 0.1,
        end_date: str = "2026-09-04",
        rows: list[tuple[str, str]] | None = None,
        latest: bool = True,
    ) -> dict:
        rows = rows or [
            ("AT 2026old", "2026-09-01 12:00:00"),
            ("AT 2026future", "2026-09-03 12:00:00"),
        ]
        text = "ID,Name,RA,DEC,Discovery Date (UT)\n" + "".join(
            f"{index},{obj},12:00:00,+10:00:00,{discovery}\n"
            for index, (obj, discovery) in enumerate(rows, 1)
        )
        payload = text.encode("utf-8")
        import hashlib

        digest = hashlib.sha256(payload).hexdigest()
        snapdir = self.root / "snapshots"
        snapdir.mkdir(exist_ok=True)
        path = snapdir / f"{name}.csv"
        path.write_bytes(payload)
        observed_min = ceiling + observed_offset
        observed_max = observed_min + 0.01
        observed_dt = datetime.fromtimestamp(
            (observed_min - 2440587.5) * 86400, tz=timezone.utc
        )
        observed_max_dt = datetime.fromtimestamp(
            (observed_max - 2440587.5) * 86400, tz=timezone.utc
        )
        metadata = {
            "schema_version": SNAPSHOT_SCHEMA,
            "snapshot_id": name,
            "snapshot_file": f"snapshots/{name}.csv",
            "snapshot_sha256": digest,
            "row_count": len(rows),
            "harvested_at_utc": observed_max_dt.isoformat().replace("+00:00", "Z"),
            "harvested_at_jd": observed_max,
            "registry_observed_at_utc_min": observed_dt.isoformat().replace(
                "+00:00", "Z"
            ),
            "registry_observed_at_utc_max": observed_max_dt.isoformat().replace(
                "+00:00", "Z"
            ),
            "registry_observed_at_jd_min": observed_min,
            "registry_observed_at_jd_max": observed_max,
            "discovery_start_date": "2025-09-01",
            "discovery_end_exclusive": end_date,
        }
        if latest:
            (self.root / "tns_12mo.meta.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
        return metadata

    def test_snapshot_filters_obvious_future_discoveries_and_pins_bytes(self):
        ceiling = datetime_to_jd(
            datetime(2026, 9, 2, tzinfo=timezone.utc)
        )
        frozen = self._snapshot("frozen", ceiling=ceiling)
        rows, provenance = read_snapshot(
            required_coverage_jd=ceiling, tns_dir=self.root
        )
        self.assertEqual(provenance["snapshot_id"], "frozen")
        self.assertEqual(
            [row["Name"] for row in rows_discovered_as_of(rows, ceiling)],
            ["AT 2026old"],
        )

        self._snapshot(
            "later",
            ceiling=ceiling,
            observed_offset=0.5,
            rows=[("AT 2026later", "2026-09-01 10:00:00")],
        )
        pinned_rows, pinned_provenance = read_snapshot(
            required_coverage_jd=ceiling,
            reference=frozen,
            tns_dir=self.root,
        )
        self.assertEqual(pinned_provenance["snapshot_id"], "frozen")
        self.assertEqual({row["Name"] for row in pinned_rows}, {
            "AT 2026old", "AT 2026future"
        })

    def test_snapshot_requires_scan_and_query_interval_to_cover_ceiling(self):
        ceiling = datetime_to_jd(
            datetime(2026, 9, 2, 12, tzinfo=timezone.utc)
        )
        self._snapshot("pre", ceiling=ceiling, observed_offset=-0.01)
        with self.assertRaisesRegex(RuntimeError, "began scanning before"):
            read_snapshot(required_coverage_jd=ceiling, tns_dir=self.root)

        self._snapshot(
            "short-query",
            ceiling=ceiling,
            observed_offset=0.1,
            end_date="2026-09-02",
        )
        with self.assertRaisesRegex(RuntimeError, "does not cover"):
            read_snapshot(required_coverage_jd=ceiling, tns_dir=self.root)

    def test_snapshot_lag_and_payload_tampering_fail_closed(self):
        ceiling = datetime_to_jd(
            datetime(2026, 9, 2, tzinfo=timezone.utc)
        )
        metadata = self._snapshot("late", ceiling=ceiling, observed_offset=1.1)
        with self.assertRaisesRegex(RuntimeError, "after the history ceiling"):
            read_snapshot(required_coverage_jd=ceiling, tns_dir=self.root)

        metadata["registry_observed_at_jd_min"] = ceiling + 0.1
        metadata["registry_observed_at_jd_max"] = ceiling + 0.2
        (self.root / "snapshots" / "late.csv").write_bytes(b"changed")
        with self.assertRaisesRegex(RuntimeError, "digest mismatch"):
            read_snapshot(
                required_coverage_jd=ceiling,
                reference=metadata,
                tns_dir=self.root,
            )


if __name__ == "__main__":
    unittest.main()
