"""Synthetic FITS structural checks, explicitly guarding data-array reads."""

import io
import unittest
from unittest.mock import patch

import numpy as np
import xmm_structure as module
from astropy.io import fits


def fixture():
    output = io.BytesIO()
    table = fits.BinTableHDU.from_columns([
        fits.Column(name="TIME", format="D", unit="s", array=np.arange(10, dtype=float)),
        fits.Column(name="PI", format="J", unit="eV", array=np.arange(10)),
    ], name="EVENTS")
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(output)
    return output.getvalue()


class DataGuard(io.BytesIO):
    def read(self, size=-1):
        if self.tell() >= 2 * module.BLOCK:
            raise AssertionError("Attempted EVENTS data read")
        return super().read(size)


class StructureTests(unittest.TestCase):
    def test_headers_only_and_column_metadata(self):
        body = fixture()
        result = module.structure(DataGuard(body), len(body))
        self.assertEqual(result["hdu_count"], 2)
        self.assertEqual(result["header_bytes_read"], 5760)
        self.assertEqual(result["declared_data_region_bytes_read"], 0)
        self.assertEqual(result["hdus"][1]["extname"], "EVENTS")
        self.assertTrue(any("TIME" in card for card in result["hdus"][1]["cards"]))

    def test_size_alignment_and_actual_length(self):
        body = fixture()
        for length in (0, len(body) - 1, len(body) + module.BLOCK, module.MAX_FILE_BYTES + module.BLOCK):
            with self.subTest(length=length), self.assertRaises(ValueError):
                module.structure(io.BytesIO(body), length)

    def test_truncated_array_rejected_without_read(self):
        body = fixture()[:5760]
        with self.assertRaisesRegex(ValueError, "STOP_DATA_SPAN"):
            module.structure(DataGuard(body), len(body))

    def test_header_cap(self):
        body = b" " * 5760
        with patch.object(module, "MAX_HEADER_BLOCKS", 1), self.assertRaisesRegex(ValueError, "STOP_HEADER_CAP"):
            module.structure(io.BytesIO(body), len(body))

    def test_hdu_cap(self):
        body = fixture()
        with patch.object(module, "MAX_HDUS", 1), self.assertRaisesRegex(ValueError, "STOP_HDU_CAP"):
            module.structure(io.BytesIO(body), len(body))

    def test_duplicate_layout_key_rejected(self):
        body = fixture()
        header = fits.Header.fromstring(body[:2880].decode())
        header.append(("BITPIX", 8))
        changed = header.tostring().encode() + body[2880:]
        with self.assertRaisesRegex(ValueError, "STOP_DUPLICATE_LAYOUT_KEY"):
            module.structure(io.BytesIO(changed), len(changed))


if __name__ == "__main__":
    unittest.main()
