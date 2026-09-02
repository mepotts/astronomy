from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    import pandas as pd
    import m1_pool
    import m2_pool
    import m2_vet_evidence
    from cache_contract import write_cache
except ModuleNotFoundError:
    pd = None
    m1_pool = None
    m2_pool = None
    m2_vet_evidence = None
    write_cache = None


@unittest.skipUnless(pd is not None, "optional science stack not installed")
class HistoryContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.temp_path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_m1_pool_threads_ceiling_to_cache_and_filter(self):
        oid = "ZTF26contract"
        frame = pd.DataFrame([{"oid": oid, "meanra": 10.0, "meandec": 20.0}])
        verdict = {
            "passed": False,
            "reason": "test rejection",
            "n_clean": 0,
            "n_alerts": 0,
        }
        with (
            mock.patch.object(m1_pool, "POOL", self.temp_path),
            mock.patch.object(m1_pool, "_prefetch") as prefetch,
            mock.patch.object(m1_pool, "session", return_value=object()),
            mock.patch.object(m1_pool, "fetch_one", return_value=[]) as fetch,
            mock.patch.object(m1_pool.F, "evaluate", return_value=verdict) as evaluate,
        ):
            result = m1_pool.enrich_and_filter(
                frame,
                "contract",
                jd_ceiling=2460000.5,
                max_age_seconds=3600,
            )

        self.assertEqual(result["history_jd_ceiling"].tolist(), [2460000.5])
        self.assertEqual(prefetch.call_args.kwargs["required_coverage_jd"], 2460000.5)
        self.assertEqual(fetch.call_args.kwargs["required_coverage_jd"], 2460000.5)
        self.assertEqual(evaluate.call_args.kwargs["jd_cutoff"], 2460000.5)

    def test_m2_pool_applies_both_floor_and_ceiling(self):
        oid = "ZTF26m2contract"
        e1 = pd.DataFrame(
            [{"oid": oid, "meanra": 10.0, "meandec": 20.0, "arm": "E1_new"}]
        )
        e2 = pd.DataFrame(columns=e1.columns)
        verdict = {"passed": False, "reason": "test rejection", "n_clean": 0}
        t0, t1 = 61274.0, 61277.0
        expected_floor = t0 + 2400000.5 - m2_pool.EPISODE_FLOOR_DAYS
        expected_ceiling = t1 + 2400000.5
        for arm, frame in (("e1", e1), ("e2", e2)):
            write_cache(
                self.temp_path / f"{arm}_contract.csv",
                frame.to_csv(index=False, lineterminator="\n").encode("utf-8"),
                kind=f"test_{arm}",
                contract={"test": True},
                row_count=len(frame),
            )
        with (
            mock.patch.object(sys, "argv", ["m2_pool.py", str(t0), str(t1), "contract"]),
            mock.patch.object(m2_pool, "POOL", self.temp_path),
            mock.patch.object(m2_pool, "OUT", self.temp_path),
            mock.patch.object(m2_pool, "arm_e1_new", return_value=e1),
            mock.patch.object(m2_pool, "arm_e2_outbursts", return_value=e2),
            mock.patch.object(m2_pool, "session", return_value=object()),
            mock.patch.object(
                m2_pool,
                "fetch_batch",
                return_value={oid: pd.DataFrame()},
            ) as fetch,
            mock.patch.object(m2_pool.F2, "evaluate", return_value=verdict) as evaluate2,
            mock.patch.object(m2_pool.M1, "evaluate", return_value=verdict) as evaluate1,
            mock.patch.object(m2_pool, "cache_provenance", return_value={}),
        ):
            m2_pool.main()

        self.assertEqual(fetch.call_args.kwargs["required_coverage_jd"], expected_ceiling)
        self.assertEqual(evaluate2.call_args.kwargs["jd_floor"], expected_floor)
        self.assertEqual(evaluate2.call_args.kwargs["jd_cutoff"], expected_ceiling)
        self.assertEqual(evaluate1.call_args.kwargs["jd_floor"], expected_floor)
        self.assertEqual(evaluate1.call_args.kwargs["jd_cutoff"], expected_ceiling)
        saved = pd.read_csv(self.temp_path / "m2_filtered_contract.csv")
        self.assertEqual(saved["history_jd_ceiling"].tolist(), [expected_ceiling])

    def test_evidence_forces_refresh_and_explicit_coverage(self):
        oid = "ZTF26evidence"
        with mock.patch.object(
            m2_vet_evidence,
            "fetch_histories_batch",
            return_value={oid: []},
        ) as fetch:
            got = m2_vet_evidence.fetch_alerts_batch(
                object(),
                [oid],
                refresh=True,
                required_coverage_jd=2460000.5,
            )

        self.assertTrue(got[oid].empty)
        self.assertTrue(fetch.call_args.kwargs["refresh"])
        self.assertEqual(
            fetch.call_args.kwargs["required_coverage_jd"], 2460000.5
        )


if __name__ == "__main__":
    unittest.main()
