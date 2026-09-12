import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("manifest_test", Path(__file__).parents[1]/"scripts/sector106_manifest.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
NAME = "tess2026192221110-s0106-0000000000000001-0300-s_lc.fits"
LINE = f"curl -C - -L -o {NAME} https://mast.stsci.edu/api/v0.1/Download/file/?uri=mast:TESS/product/{NAME}"


class ManifestTests(unittest.TestCase):
    def test_valid_and_duplicates_accounted(self):
        result = M.inspect_manifest(("#!/bin/sh\n"+LINE+"\n"+LINE).encode())
        self.assertEqual(result["commands_parsed_not_executed"], 2)
        self.assertEqual(result["unique_tic_ids"], 1)
        self.assertEqual(result["duplicate_product_entries"], 1)
        self.assertEqual(result["light_curves_downloaded"], 0)

    def test_unexpected_content_is_not_coverage(self):
        for text in ("", "<html>outage</html>", LINE.replace("s0106", "s0107"),
                     LINE.replace("mast.stsci.edu", "example.test"), LINE.replace("curl", "sh")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                M.inspect_manifest(text.encode())


if __name__ == "__main__":
    unittest.main()
