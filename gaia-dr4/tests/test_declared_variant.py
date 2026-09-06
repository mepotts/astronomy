import hashlib
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/declared_variant_20260906.py"
spec = importlib.util.spec_from_file_location("variant", path)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class VariantContracts(unittest.TestCase):
    def test_original_registration_body_is_unchanged(self):
        raw = (path.parents[1] / "PREREG-2026-08-23-december-discriminators.md").read_bytes()
        body = raw.replace(b"\r\n", b"\n").split(b"<!-- BEGIN VARIANT LOG -->")[0]
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "f00cdf484c0c57613639611d1793e03485bfb12514e1e7968a514e2bb2ee7666")

    def row(self, **kw):
        return {"test": "D1", "analysis": "primary", "n_conf": "100", "n_spur": "100",
            "p_holm": ".01", "effect": ".154", "min_detectable": ".2", "control_p": ".5",
            "label": "original label", "decisive_by_diff": "False", "defect": "GAP-4", **kw}

    def test_fixed_pair_contract(self):
        self.assertEqual(v.PAIRS, {"D1": (.154, 0), "D4": (.30, .075)})
        calls = []
        def power(*args):
            calls.append(args)
            return .9
        row = self.row()
        result = v.translate(row, power)
        self.assertEqual(calls, [("D1", 100, 100)])
        self.assertEqual(result["variant_label"], "POSITIVE")
        self.assertEqual(result["original"], row)
        self.assertEqual(row["label"], "original label")

    def test_power_boundary_and_gap1(self):
        self.assertEqual(v.translate(self.row(), lambda *a: .8)["variant_label"], "POSITIVE")
        result = v.translate(self.row(), lambda *a: .799)
        self.assertIn("NOT DESIGN-DECISIVE", result["variant_label"])
        self.assertFalse(result["positive_finding_reportable"])

    def test_veto_including_gap1_and_missing_control(self):
        for power in (.2, .9):
            r = v.translate(self.row(control_p=".01"), lambda *a, power=power: power)
            self.assertIn("VETOED", r["variant_label"])
            self.assertFalse(r["positive_finding_reportable"])
        r = v.translate(self.row(control_p="nan"), lambda *a: .9)
        self.assertIn("NOT REPORTABLE", r["variant_label"])
        self.assertFalse(r["positive_finding_reportable"])

    def test_pooled_rules(self):
        for power in (.2, .9):
            r = v.translate(self.row(analysis="pooled", p_holm=".5"), lambda *a, power=power: power)
            self.assertEqual(r["variant_label"], "POOLED: UNINTERPRETABLE")
        r = v.translate(self.row(analysis="pooled", effect="-.1"), lambda *a: .9)
        self.assertIn("POOLED REVERSAL", r["variant_label"])

    def test_nonsignificance_and_missing(self):
        self.assertEqual(v.translate(self.row(p_holm=".05"), lambda *a: .9)["variant_label"], "NULL")
        for kw in ({"p_holm": "nan"}, {"effect": ""}, {"n_spur": "4"}):
            self.assertEqual(v.translate(self.row(**kw))["variant_label"], "NOT TESTABLE")

    def test_auc_direction_and_original_power(self):
        r = v.translate(self.row(test="D3", effect=".344", min_detectable=".6"))
        self.assertEqual(r["variant_label"], "POSITIVE")
        r = v.translate(self.row(test="D3", effect=".66", min_detectable=".6"))
        self.assertEqual(r["variant_label"], "DIRECTION REVERSAL")

    def test_regression_passthrough(self):
        r = v.translate(self.row(analysis="regression"))
        self.assertEqual(r["variant_label"], "original label")
        self.assertTrue(r["regression_passthrough"])

    def test_invalid_input_and_power_fail_closed(self):
        for kw in ({"test": "D5"}, {"analysis": "unknown"}, {"n_conf": "-1"}, {"p_holm": "2"}):
            with self.assertRaises(ValueError):
                v.translate(self.row(**kw))
        with self.assertRaises(ValueError):
            v.translate(self.row(), lambda *a: float("nan"))


if __name__ == "__main__":
    unittest.main()
