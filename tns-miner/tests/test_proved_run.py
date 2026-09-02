from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cache_contract import load_cache_contract  # noqa: E402
from run_proved_window import (  # noqa: E402
    ExclusiveRunLock,
    _build_closed_tns_window,
    _validate_closed_year,
)


class ProvedRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_closed_window_is_exactly_twelve_month_boundaries(self):
        _validate_closed_year(date(2025, 9, 1), date(2026, 9, 1))
        for start, end in (
            (date(2025, 9, 2), date(2026, 9, 2)),
            (date(2025, 9, 1), date(2026, 8, 1)),
            (date(2025, 9, 1), date(2026, 10, 1)),
        ):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                _validate_closed_year(start, end)

    def test_exclusive_lock_rejects_a_second_campaign(self):
        lock_path = self.root / "campaign.lock"
        with (
            ExclusiveRunLock(lock_path),
            self.assertRaisesRegex(RuntimeError, "already running"),
        ):
            with ExclusiveRunLock(lock_path):
                self.fail("second lock should not be acquired")

    def test_closed_tns_corpus_is_filtered_and_digest_proved(self):
        data = self.root / "data"
        tns = data / "tns"
        snapshots = tns / "snapshots"
        snapshots.mkdir(parents=True)
        source = snapshots / "fresh.csv"
        text = (
            "ID,Name,RA,DEC,Discovery Date (UT)\n"
            "1,AT old,12:00:00,+10:00:00,2025-08-31 23:59:59\n"
            "2,AT first,12:00:01,+10:00:01,2025-09-01 00:00:00\n"
            "3,AT last,12:00:02,+10:00:02,2026-08-31 23:59:59\n"
            "4,AT next,12:00:03,+10:00:03,2026-09-01 00:00:00\n"
        )
        source.write_text(text, encoding="utf-8", newline="\n")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        pointer = {
            "snapshot_id": "fresh",
            "snapshot_file": "snapshots/fresh.csv",
            "snapshot_sha256": digest,
            "discovery_start_date": "2025-08-01",
            "discovery_end_exclusive": "2026-09-03",
        }
        (tns / "tns_12mo.meta.json").write_text(json.dumps(pointer), encoding="utf-8")

        output, proof = _build_closed_tns_window(
            data,
            start=date(2025, 9, 1),
            end_exclusive=date(2026, 9, 1),
        )

        frame = pd.read_csv(output)
        self.assertEqual(frame["ID"].tolist(), [2, 3])
        actual = load_cache_contract(
            output,
            kind="tns_closed_twelve_month_window",
            expected_contract=proof["contract"],
        )
        self.assertEqual(actual, proof)
        self.assertEqual(proof["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
