"""Offline product-boundary tests; no network calls."""
import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SPEC = importlib.util.spec_from_file_location("m0_acquisition_test", Path(__file__).resolve().parents[1]/"scripts/m0.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class AcquisitionTests(unittest.TestCase):
    def test_product_bounds(self):
        good = {"filename": "tess-example_lc.fits", "uri": "mast:TESS/product/tess-example_lc.fits", "bytes": 100}
        self.assertEqual(M.validate_product(good), good["filename"])
        for key, value in (("filename", "../bad_lc.fits"), ("filename", "..\\bad_lc.fits"),
                           ("filename", "C:\\bad_lc.fits"), ("filename", "anything.py"),
                           ("uri", "https://example.com/file"), ("bytes", 0),
                           ("bytes", M.MAX_BYTES+1)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                M.validate_product({**good, key: value})

    def test_receipts_are_never_overwritten(self):
        with TemporaryDirectory() as temp:
            p = Path(temp)/"receipt.json"
            M.save(p, {"status": "STOP"})
            before = p.read_bytes()
            with self.assertRaises(FileExistsError):
                M.save(p, {"status": "GO"})
            self.assertEqual(p.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
