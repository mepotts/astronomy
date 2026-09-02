from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    import numpy as np
    import pandas as pd
    import m1_pool
    import m1_candidates
    import m1_tns_harvest
    import m2_candidates
    import m2_pool
    import m2_vet_evidence
except ModuleNotFoundError:
    np = None
    pd = None
    m1_pool = None
    m1_candidates = None
    m1_tns_harvest = None
    m2_candidates = None
    m2_pool = None
    m2_vet_evidence = None


class StubResponse:
    def __init__(self, status_code=200, payload=None, text="", content=None):
        self.status_code = status_code
        self.payload = payload
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")


class StubSession:
    def __init__(self, get_replies=None, post_replies=None):
        self.get_replies = list(get_replies or [])
        self.post_replies = list(post_replies or [])

    def get(self, *_args, **_kwargs):
        return self.get_replies.pop(0)

    def post(self, *_args, **_kwargs):
        return self.post_replies.pop(0)


@unittest.skipUnless(pd is not None, "optional science stack not installed")
class RuntimeFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_traversal_tags_fail_before_representative_writers(self):
        pos = pd.DataFrame([{"id": 0, "oid": "ZTF26x", "ra": 10.0, "dec": 20.0}])
        with (
            mock.patch.object(m1_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m1_candidates, "POOL", self.root),
            mock.patch.object(m1_candidates, "OUT", self.root),
            mock.patch.object(m2_vet_evidence, "DATA", self.root),
        ):
            with self.assertRaises(ValueError):
                m1_pool.enumerate_new_objects(61274.0, 61277.0, "../escape")
            with self.assertRaises(ValueError):
                m2_pool.arm_e2_outbursts(61274.0, 61277.0, "..\\escape")
            with self.assertRaises(ValueError):
                m1_candidates._load_filtered("nested/escape")
            with self.assertRaises(ValueError):
                m2_vet_evidence.xmatch(object(), pos, "C:\\escape")

    def test_first_of_month_harvest_covers_current_utc_day(self):
        windows = m1_tns_harvest._month_windows(date(2026, 9, 1))

        self.assertEqual(windows[0][0], date(2025, 9, 1))
        self.assertEqual(windows[-1], (date(2026, 9, 1), date(2026, 9, 2)))
        self.assertTrue(
            all(left[1] == right[0] for left, right in zip(windows, windows[1:]))
        )

    def test_closed_tns_month_cannot_be_header_only(self):
        empty = pd.DataFrame(columns=["ID", "Name"])
        with self.assertRaisesRegex(RuntimeError, "closed TNS month"):
            m1_tns_harvest._window_state(
                empty,
                date(2026, 8, 1),
                date(2026, 9, 1),
                end_exclusive=date(2026, 9, 3),
            )
        self.assertEqual(
            m1_tns_harvest._window_state(
                empty,
                date(2026, 9, 1),
                date(2026, 9, 3),
                end_exclusive=date(2026, 9, 3),
            ),
            "current_partial",
        )

    def test_tns_cross_month_id_overlap_aborts_instead_of_deduping(self):
        seen = {"1", "2"}
        later = pd.DataFrame([{"ID": "2", "Name": "AT 2026duplicate"}])
        with self.assertRaisesRegex(RuntimeError, "windows overlap"):
            m1_tns_harvest._add_disjoint_window_ids(
                seen,
                later,
                d0=date(2026, 9, 1),
                d1=date(2026, 9, 3),
            )
        self.assertEqual(seen, {"1", "2"})

    def test_tns_repeated_page_ids_abort_snapshot_window(self):
        page = (
            '"ID","Name","Discovery Date (UT)"\n'
            '"1","AT 2026a","2026-08-02 01:00:00"\n'
            '"2","AT 2026b","2026-08-03 01:00:00"\n'
        )
        replies = [StubResponse(text=page), StubResponse(text=page)]
        with (
            mock.patch.object(m1_tns_harvest, "PAGE", 2),
            mock.patch.object(m1_tns_harvest, "tns_get", side_effect=replies),
        ):
            with self.assertRaisesRegex(RuntimeError, "repeated or overlapped"):
                m1_tns_harvest.fetch_window(
                    object(), date(2026, 8, 1), date(2026, 9, 1)
                )

    def test_tns_page_rejects_discovery_date_outside_requested_window(self):
        page = (
            '"ID","Name","Discovery Date (UT)"\n"1","AT 2026a","2026-09-01 00:00:00"\n'
        )
        with mock.patch.object(
            m1_tns_harvest, "tns_get", return_value=StubResponse(text=page)
        ):
            with self.assertRaisesRegex(RuntimeError, "outside"):
                m1_tns_harvest.fetch_window(
                    object(), date(2026, 8, 1), date(2026, 9, 1)
                )

    def test_tns_short_nonempty_page_requires_explicit_empty_page(self):
        header = '"ID","Name","Discovery Date (UT)"\n'
        replies = [
            StubResponse(text=header + '"1","AT 2026a","2026-08-02 01:00:00"\n'),
            StubResponse(text=header + '"2","AT 2026b","2026-08-03 01:00:00"\n'),
            StubResponse(text=header),
        ]
        with (
            mock.patch.object(m1_tns_harvest, "PAGE", 2),
            mock.patch.object(m1_tns_harvest, "tns_get", side_effect=replies),
        ):
            result = m1_tns_harvest.fetch_window(
                object(), date(2026, 8, 1), date(2026, 9, 1)
            )

        self.assertEqual(result["ID"].tolist(), ["1", "2"])

    def test_tns_retains_exact_data_and_terminal_page_bytes(self):
        header = '"ID","Name","Discovery Date (UT)"\n'
        page = header + '"1","AT 2026a","2026-08-02 01:00:00"\n'
        replies = [StubResponse(text=page), StubResponse(text=header)]
        raw_dir = self.root / "raw" / "run" / "window"
        provenance = []
        with (
            mock.patch.object(m1_tns_harvest, "PAGE", 2),
            mock.patch.object(m1_tns_harvest, "TNSDIR", self.root),
            mock.patch.object(m1_tns_harvest, "tns_get", side_effect=replies),
        ):
            result = m1_tns_harvest.fetch_window(
                object(),
                date(2026, 8, 1),
                date(2026, 9, 1),
                raw_dir=raw_dir,
                raw_provenance=provenance,
            )

        self.assertEqual(result["ID"].tolist(), ["1"])
        self.assertEqual([item["proof"]["row_count"] for item in provenance], [1, 0])
        self.assertTrue(
            all(item["proof"]["exact_http_entity_bytes"] for item in provenance)
        )
        self.assertEqual((raw_dir / "page_0000.csv").read_bytes(), page.encode())
        self.assertEqual((raw_dir / "page_0001.csv").read_bytes(), header.encode())

    def test_empty_fink_taxonomy_writes_no_e2_cache(self):
        response = StubResponse(payload={})
        with (
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "session", return_value=StubSession([response])),
        ):
            with self.assertRaisesRegex(RuntimeError, "taxonomy is empty"):
                m2_pool.arm_e2_outbursts(61274.0, 61277.0, "taxonomy")
        self.assertFalse((self.root / "e2_taxonomy.csv").exists())
        self.assertFalse((self.root / "e2_taxonomy.csv.meta.json").exists())

    def test_fink_taxonomy_requires_lists_and_pinned_class_markers(self):
        cases = [
            ({"SIMBAD": []}, "nonempty list"),
            ({"SIMBAD": ["(SIMBAD) CataclyV*"]}, "baseline contract"),
        ]
        for payload, message in cases:
            with (
                self.subTest(payload=payload),
                self.assertRaisesRegex(RuntimeError, message),
            ):
                m2_pool.enumerable_classes(StubSession([StubResponse(payload=payload)]))

        filler = [
            f"Synthetic baseline class {index}"
            for index in range(m2_pool.FINK_TAXONOMY_MIN_NON_TNS_CLASSES - 4)
        ]
        classes = m2_pool.enumerable_classes(
            StubSession(
                [
                    StubResponse(
                        payload={
                            "SIMBAD": ["(SIMBAD) CataclyV*", "(SIMBAD) Galaxy"],
                            "Fink science": [
                                "Early SN Ia candidate",
                                "Solar System candidate",
                                *filler,
                            ],
                        }
                    )
                ]
            )
        )
        self.assertIn("CataclyV*", classes)
        self.assertIn("Early SN Ia candidate", classes)
        self.assertIn("Unknown", classes)

    def test_m1_all_tns_deduped_returns_schema_stable_zero_candidates(self):
        source = pd.DataFrame(
            [
                {
                    "oid": "ZTF26known",
                    "passed": True,
                    "history_jd_ceiling": 2461277.5,
                }
            ]
        )
        frozen = {"snapshot_id": "frozen"}
        with (
            mock.patch.object(m1_candidates, "_load_filtered", return_value=source),
            mock.patch.object(m1_candidates, "_pin_tns_reference", return_value=frozen),
            mock.patch.object(
                m1_candidates,
                "apply_tns_contract",
                return_value=(
                    source.iloc[0:0].copy(),
                    {"n_removed_frozen_discovery_date_bounded": 1},
                ),
            ),
            mock.patch.object(m1_candidates, "session") as open_session,
        ):
            result = m1_candidates.build("deduped")

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), m1_candidates.CANDIDATE_COLUMNS)
        open_session.assert_not_called()

    def test_m2_no_pass_returns_schema_stable_zero_candidates(self):
        source = pd.DataFrame(
            [
                {
                    "oid": "ZTF26fail",
                    "passed": False,
                    "m1_passed": False,
                    "history_jd_ceiling": 2461277.5,
                }
            ]
        )
        frozen = {"snapshot_id": "frozen"}
        with (
            mock.patch.object(m2_candidates, "_load_filtered", return_value=source),
            mock.patch.object(m2_candidates, "_pin_tns_reference", return_value=frozen),
            mock.patch.object(m2_candidates, "session") as open_session,
        ):
            result = m2_candidates.build("no_pass")

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), m2_candidates.CANDIDATE_COLUMNS)
        open_session.assert_not_called()

    def test_m2_all_tns_deduped_returns_schema_stable_zero_candidates(self):
        source = pd.DataFrame(
            [
                {
                    "oid": "ZTF26known",
                    "passed": True,
                    "m1_passed": True,
                    "history_jd_ceiling": 2461277.5,
                }
            ]
        )
        frozen = {"snapshot_id": "frozen"}
        with (
            mock.patch.object(m2_candidates, "_load_filtered", return_value=source),
            mock.patch.object(m2_candidates, "_pin_tns_reference", return_value=frozen),
            mock.patch.object(
                m2_candidates,
                "apply_tns_contract",
                return_value=(
                    source.iloc[0:0].copy(),
                    {"n_removed_frozen_discovery_date_bounded": 1},
                ),
            ),
            mock.patch.object(m2_candidates, "session") as open_session,
        ):
            result = m2_candidates.build("deduped")

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), m2_candidates.CANDIDATE_COLUMNS)
        open_session.assert_not_called()

    def test_m1_repeated_tag_cannot_relabel_a_different_window(self):
        first = StubSession([StubResponse(payload={"items": [], "total": 0})])
        with (
            mock.patch.object(m1_pool, "POOL", self.root),
            mock.patch.object(m1_pool, "session", return_value=first),
        ):
            m1_pool.enumerate_new_objects(61274.0, 61277.0, "tonight")
            with self.assertRaisesRegex(RuntimeError, "input mismatch"):
                m1_pool.enumerate_new_objects(61275.0, 61278.0, "tonight")

    def test_m1_short_page_cannot_contradict_reported_total(self):
        response = StubResponse(payload={"items": [], "total": 1})
        with (
            mock.patch.object(m1_pool, "POOL", self.root),
            mock.patch.object(m1_pool, "session", return_value=StubSession([response])),
        ):
            with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
                m1_pool.enumerate_new_objects(61274.0, 61277.0, "short")
        self.assertFalse((self.root / "pool_short.csv").exists())

    def test_m1_repeated_alerce_page_aborts(self):
        items = [
            {"oid": "ZTF26a", "meanra": 10.0, "meandec": 20.0},
            {"oid": "ZTF26b", "meanra": 11.0, "meandec": 21.0},
        ]
        replies = [
            StubResponse(payload={"items": items, "total": 3}),
            StubResponse(payload={"items": items}),
        ]
        with (
            mock.patch.object(m1_pool, "POOL", self.root),
            mock.patch.object(m1_pool, "ALERCE_PAGE_SIZE", 2),
            mock.patch.object(m1_pool, "session", return_value=StubSession(replies)),
            mock.patch.object(m1_pool.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "repeated page"):
                m1_pool.enumerate_new_objects(61274.0, 61277.0, "repeat")
        self.assertFalse((self.root / "pool_repeat.csv").exists())

    def test_m2_short_page_cannot_contradict_reported_total(self):
        response = StubResponse(payload={"items": [], "total": 1})
        with (
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "session", return_value=StubSession([response])),
        ):
            with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
                m2_pool.arm_e1_new(61274.0, 61277.0, "short")
        self.assertFalse((self.root / "e1_short.csv").exists())

    def test_m2_repeated_alerce_page_aborts(self):
        items = [
            {"oid": "ZTF26a", "meanra": 10.0, "meandec": 20.0},
            {"oid": "ZTF26b", "meanra": 11.0, "meandec": 21.0},
        ]
        replies = [
            StubResponse(payload={"items": items, "total": 3}),
            StubResponse(payload={"items": items}),
        ]
        with (
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "ALERCE_PAGE_SIZE", 2),
            mock.patch.object(m2_pool, "session", return_value=StubSession(replies)),
            mock.patch.object(m2_pool.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "repeated page"):
                m2_pool.arm_e1_new(61274.0, 61277.0, "repeat")
        self.assertFalse((self.root / "e1_repeat.csv").exists())

    def test_m1_interruption_leaves_checkpoint_not_candidate_final(self):
        frame = pd.DataFrame(
            [
                {"oid": f"ZTF26{x:03d}", "meanra": 10.0, "meandec": 20.0}
                for x in range(101)
            ]
        )
        verdict = {
            "passed": False,
            "reason": "test rejection",
            "n_clean": 0,
            "n_alerts": 0,
        }
        evaluations = [verdict] * 100 + [RuntimeError("interrupted")]
        with (
            mock.patch.object(m1_pool, "POOL", self.root),
            mock.patch.object(m1_pool, "_prefetch"),
            mock.patch.object(m1_pool, "session", return_value=object()),
            mock.patch.object(m1_pool, "fetch_one", return_value=[]),
            mock.patch.object(m1_pool.F, "evaluate", side_effect=evaluations),
        ):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                m1_pool.enrich_and_filter(frame, "crash", jd_ceiling=2460000.5)
        self.assertTrue((self.root / "filtered_crash.checkpoint.csv").exists())
        self.assertFalse((self.root / "filtered_crash.csv").exists())

    def test_candidate_rejects_unproved_filtered_csv(self):
        (self.root / "filtered_bad.csv").write_text(
            "oid,passed,history_jd_ceiling\nZTF26x,True,2460000.5\n",
            encoding="utf-8",
        )
        (self.root / "m1_pool_bad.json").write_text(
            '{"tag":"bad","mjd_window":[1,2],"history_jd_ceiling":2460000.5}',
            encoding="utf-8",
        )
        with (
            mock.patch.object(m1_candidates, "POOL", self.root),
            mock.patch.object(m1_candidates, "OUT", self.root),
        ):
            with self.assertRaisesRegex(RuntimeError, "does not prove"):
                m1_candidates._load_filtered("bad")

    def test_e2_http_failure_writes_no_empty_pool_cache(self):
        replies = [
            StubResponse(status_code=503) for _ in range(m2_pool.FINK_FETCH_ATTEMPTS)
        ]
        with (
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "session", return_value=StubSession(replies)),
            mock.patch.object(m2_pool, "enumerable_classes", return_value=["Unknown"]),
            mock.patch.object(m2_pool, "FINK_MAX_BISECT_DEPTH", 0),
            mock.patch.object(m2_pool.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                m2_pool.arm_e2_outbursts(61274.0, 61277.0, "outage")
        self.assertFalse((self.root / "e2_outage.csv").exists())
        self.assertFalse((self.root / "e2_outage.csv.meta.json").exists())

    def test_retryable_e2_outage_bisects_without_calling_it_zero(self):
        left = pd.DataFrame([self._latest_row(jd=2461275.0)])
        right_row = self._latest_row(jd=2461276.0)
        right_row["i:objectId"] = "ZTF26right"
        right = pd.DataFrame([right_row])
        with mock.patch.object(
            m2_pool,
            "_latests",
            side_effect=[
                m2_pool.FinkLatestsUnavailable("HTTP 504"),
                left,
                right,
            ],
        ) as latest:
            result = m2_pool._latests_complete(object(), "Unknown", 61274.0, 61277.0)

        self.assertEqual(result["i:objectId"].tolist(), ["ZTF26valid", "ZTF26right"])
        self.assertEqual(latest.call_count, 3)

    def test_successful_e2_slice_is_retained_and_reused(self):
        row = self._latest_row()
        session = StubSession([StubResponse(payload=[row])])
        cache = self.root / "slices"

        first = m2_pool._latests(
            session,
            "Unknown",
            61274.0,
            61277.0,
            cache_dir=cache,
        )
        second = m2_pool._latests(
            StubSession([]),
            "Unknown",
            61274.0,
            61277.0,
            cache_dir=cache,
        )

        self.assertEqual(first["i:objectId"].tolist(), ["ZTF26valid"])
        self.assertEqual(second["i:objectId"].tolist(), ["ZTF26valid"])
        self.assertEqual(len(list(cache.glob("*.json"))), 2)

    def test_cap_bound_e2_slice_aborts_instead_of_truncating(self):
        capped = pd.DataFrame([{"i:objectId": f"ZTF{x}"} for x in range(1000)])
        with mock.patch.object(m2_pool, "_latests", return_value=capped):
            with self.assertRaisesRegex(RuntimeError, "completeness unproved"):
                m2_pool._latests_complete(
                    object(),
                    "Unknown",
                    61274.0,
                    61277.0,
                    depth=m2_pool.FINK_MAX_BISECT_DEPTH,
                )

    @staticmethod
    def _latest_row(jd=2461276.0):
        return {
            "i:objectId": "ZTF26valid",
            "i:jd": jd,
            "i:magpsf": 18.0,
            "i:magnr": 20.0,
            "i:fid": 1,
            "i:ra": 10.0,
            "i:dec": 20.0,
            "i:drb": 0.99,
            "i:rb": None,
            "i:isdiffpos": "t",
        }

    def test_e2_validates_every_row_not_only_first(self):
        good = self._latest_row()
        bad = self._latest_row()
        bad["i:objectId"] = "ZTF26bad"
        del bad["i:jd"]
        with self.assertRaisesRegex(RuntimeError, "row 1 lacks"):
            m2_pool._validate_latest_payload(
                [good, bad], cls="Unknown", t0=61274.0, t1=61277.0
            )

    def test_e2_rejects_alert_outside_requested_window(self):
        with self.assertRaisesRegex(RuntimeError, "outside"):
            m2_pool._validate_latest_payload(
                [self._latest_row(jd=2461278.0)],
                cls="Unknown",
                t0=61274.0,
                t1=61277.0,
            )

    def test_e2_json_boolean_true_is_selected_as_positive_subtraction(self):
        row = self._latest_row()
        row["i:isdiffpos"] = True
        frame = pd.DataFrame([row])
        taxonomy = self.root / "e2_inputs_boolean-true" / "taxonomy.json"
        m2_pool.write_cache(
            taxonomy,
            b"{}",
            kind="m2_fink_taxonomy_raw",
            contract=m2_pool._taxonomy_contract(),
            row_count=1,
        )
        with (
            mock.patch.object(m2_pool, "POOL", self.root),
            mock.patch.object(m2_pool, "session", return_value=object()),
            mock.patch.object(m2_pool, "enumerable_classes", return_value=["Unknown"]),
            mock.patch.object(m2_pool, "_latests_complete", return_value=frame),
        ):
            result = m2_pool.arm_e2_outbursts(61274.0, 61277.0, "boolean-true")

        self.assertEqual(result["oid"].tolist(), ["ZTF26valid"])

    def test_xmatch_failure_does_not_cache_empty_catalogues(self):
        pos = pd.DataFrame([{"id": 0, "oid": "ZTF26x", "ra": 10.0, "dec": 20.0}])
        replies = [StubResponse(status_code=503) for _ in range(3)]
        with (
            mock.patch.object(m2_vet_evidence, "DATA", self.root),
            mock.patch.object(
                m2_vet_evidence, "XCATS", [("gaia", "vizier:test", 3.0, ["Name"])]
            ),
            mock.patch.object(m2_vet_evidence.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no cache written"):
                m2_vet_evidence.xmatch(
                    StubSession(post_replies=replies), pos, "tonight"
                )
        self.assertFalse((self.root / "xmatch_tonight.json").exists())

    def test_xmatch_missing_catalogue_column_fails_closed(self):
        pos = pd.DataFrame([{"id": 0, "oid": "ZTF26x", "ra": 10.0, "dec": 20.0}])
        replies = [StubResponse(text="id,angDist\n0,1.0\n") for _ in range(3)]
        with (
            mock.patch.object(m2_vet_evidence, "DATA", self.root),
            mock.patch.object(
                m2_vet_evidence, "XCATS", [("gaia", "vizier:test", 3.0, ["Name"])]
            ),
            mock.patch.object(m2_vet_evidence.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no cache written"):
                m2_vet_evidence.xmatch(
                    StubSession(post_replies=replies), pos, "missing-col"
                )
        self.assertFalse((self.root / "xmatch_missing-col.json").exists())

    def test_xmatch_out_of_radius_row_fails_closed(self):
        pos = pd.DataFrame([{"id": 0, "oid": "ZTF26x", "ra": 10.0, "dec": 20.0}])
        replies = [StubResponse(text="id,angDist,Name\n0,3.1,test\n") for _ in range(3)]
        with (
            mock.patch.object(m2_vet_evidence, "DATA", self.root),
            mock.patch.object(
                m2_vet_evidence, "XCATS", [("gaia", "vizier:test", 3.0, ["Name"])]
            ),
            mock.patch.object(m2_vet_evidence.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no cache written"):
                m2_vet_evidence.xmatch(
                    StubSession(post_replies=replies), pos, "outside-radius"
                )
        self.assertFalse((self.root / "xmatch_outside-radius.json").exists())

    def test_cutout_failure_does_not_cache_zero_image(self):
        replies = [StubResponse(status_code=503) for _ in range(3)]
        with (
            mock.patch.object(m2_vet_evidence, "CUTCACHE", self.root),
            mock.patch.object(m2_vet_evidence.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no null image was cached"):
                m2_vet_evidence.fetch_cutouts(
                    StubSession(post_replies=replies), "ZTF26x", "123"
                )
        self.assertFalse((self.root / "ZTF26x_123.npz").exists())


if __name__ == "__main__":
    unittest.main()
