import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rubin_audit", ROOT / "scripts/rubin_control_audit.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RubinControls(unittest.TestCase):
    def test_cold_replay(self):
        result = m.run(ROOT / "research/rubin-controls-20260906.zip")
        expected = json.loads((ROOT / "research/rubin-control-audit-20260906.json").read_bytes())
        self.assertEqual(result, expected)
        self.assertEqual(len(result["extra_detection_ids"]), 49)
        self.assertEqual(len(result["extra_forced_ids"]), 9)
        self.assertFalse(result["population_coverage_proved"])

    def test_exact_ids_not_floats_or_duplicates(self):
        for rows in ([{"id": 170028490639278144.0}], [{"id": 1}, {"id": 1}]):
            with self.assertRaises((ValueError, TypeError)):
                m.unique(rows, "id")


if __name__ == "__main__":
    unittest.main()
