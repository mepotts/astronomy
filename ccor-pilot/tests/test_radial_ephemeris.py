import importlib.util
import unittest
import zipfile
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("radial", BASE / "scripts/radial_ephemeris.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RadialContracts(unittest.TestCase):
    def test_polynomial_interpolation_and_bounds(self):
        t = np.arange(10, dtype=float)*600
        a = np.column_stack([t, t/600, (t/600)**2, (t/600)**3])
        np.testing.assert_allclose(m.interpolate(a, 4.5*600), [4.5, 4.5**2, 4.5**3])
        for value in (-1, 6000):
            with self.assertRaises(ValueError):
                m.interpolate(a, value)

    def test_archived_metadata_and_wrong_frame(self):
        with zipfile.ZipFile(BASE / "results/solar1-ephemeris-20260906.zip") as z:
            raw = z.read("solar1.oem")
        meta, rows = m.parse(raw)
        self.assertEqual(meta["CENTER_NAME"], "EARTH")
        self.assertGreater(len(rows), 1000)
        with self.assertRaises(ValueError):
            m.parse(raw.replace(b"EME2000", b"UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
