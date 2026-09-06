import importlib.util
import json
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/preflight.py"
spec = importlib.util.spec_from_file_location("preflight", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Contracts(unittest.TestCase):
    def test_archived_result_replays(self):
        root = MODULE.parents[1]
        expected = json.loads((root / "results/preflight-20260906.json").read_bytes())
        # JSON represents the tuples in the pure comparator as lists.
        actual = json.loads(json.dumps(mod.replay(root / "evidence/ccds-20260906.zip")))
        self.assertEqual(actual, expected)

    def test_same_or_removed_stops(self):
        a = [("decam", 1, "N1", "r"), ("decam", 2, "N1", "r")]
        for b in (a, a[:1], list(reversed(a))):
            self.assertEqual(mod.compare(a, b)["status"], "STOP_NO_NEW_R_INPUTS")

    def test_g_only_does_not_promote(self):
        a = [("decam", 1, "N1", "r")]
        self.assertEqual(mod.compare(a, a + [("decam", 2, "N1", "g")])["status"],
                         "STOP_NO_NEW_R_INPUTS")

    def test_r_addition_is_not_depth_pass(self):
        a = [("decam", 1, "N1", "r")]
        result = mod.compare(a, a + [("decam", 2, "N1", "r")])
        self.assertEqual(result["status"], "READY_IMAGE_SPEC")
        self.assertFalse(result["validated_depth_or_recovery"])

    def test_duplicate_empty_invalid_fail(self):
        a = [("decam", 1, "N1", "r")]
        for bad in ([], a * 2, [("decam", 0, "N1", "r")]):
            with self.assertRaises(ValueError):
                mod.compare(a, bad)


if __name__ == "__main__":
    unittest.main()
