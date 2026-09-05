from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from probe_service_recovery import (
    alternative_plan,
    probe_plan,
    public_shape,
)


class ServiceRecoveryTests(unittest.TestCase):
    def test_alerce_ranges_use_repeated_numeric_parameters_and_cover_now(self):
        plan = probe_plan(61285, 61288, 61288.5)
        self.assertEqual(len(plan), 8)
        first, last, no_count = plan[-3:]
        prepared = requests.Request("GET", first["url"], params=first["params"]).prepare()
        self.assertEqual(parse_qs(urlparse(prepared.url).query)["firstmjd"], ["61285", "61288"])
        self.assertEqual(last["params"]["lastmjd"], [61285, 61288.5])
        self.assertEqual(no_count["params"]["count"], "false")

    def test_diagnostic_errors_are_not_empty_counts(self):
        probe = probe_plan(61285, 61288, 61288.5)[1]
        for payload, error in (
            ({"error": "unavailable"}, TypeError),
            ([{"i:jd": True}], TypeError),
            ([{"i:jd": 2461280.5}], ValueError),
        ):
            with self.subTest(payload=payload), self.assertRaises(error):
                public_shape(payload, probe)
        self.assertEqual(public_shape([], probe), {"returned_rows": 0, "cap_bound": False})

    def test_count_disabled_has_no_invented_total(self):
        probe = probe_plan(61285, 61288, 61288.5)[-1]
        result = public_shape({"items": [{}], "total": 0}, probe)
        self.assertEqual(result, {"returned_rows": 1, "reported_total": None})

    def test_cap_bound_response_is_not_complete(self):
        probe = probe_plan(61285, 61288, 61288.5)[2]
        self.assertTrue(public_shape([{"i:jd": 2461286.5}], probe)["cap_bound"])

    def test_invalid_or_incomplete_window_rejected(self):
        for args in ((61285, 61289, 61290), (61285, 61288, 61287), (61285, 61288, float("nan"))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                probe_plan(*args)

    def test_alternatives_preserve_read_only_query_and_extended_window(self):
        post, counted, uncounted = alternative_plan(probe_plan(61285, 61288, 61288.5))
        self.assertEqual(post["url"], "https://api.ztf.fink-portal.org/api/v1/latests")
        self.assertEqual(post["method"], "POST")
        self.assertEqual(post["params"]["columns"], "i:jd")
        self.assertEqual(counted["params"]["lastmjd"], [61285, 61288.5])
        self.assertEqual(uncounted["params"]["order_by"], "lastmjd")
        self.assertEqual(uncounted["params"]["count"], "false")


if __name__ == "__main__":
    unittest.main()
