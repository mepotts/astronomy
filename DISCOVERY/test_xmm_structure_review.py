"""Independent synthetic reader guards; never opens astronomical data."""

import io
import unittest

import numpy as np
import xmm_structure as reader
from astropy.io import fits


def table_file():
    stream = io.BytesIO()
    table = fits.BinTableHDU.from_columns([
        fits.Column(name="TIME", format="D", unit="s", array=np.arange(10.)),
    ], name="EVENTS")
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(stream)
    return stream.getvalue()


def altered_table(key, value=None, delete=False):
    body = table_file()
    header = fits.Header.fromstring(body[2880:5760].decode("ascii"))
    if delete:
        del header[key]
    else:
        header[key] = value
    return body[:2880] + header.tostring().encode("ascii") + body[5760:]


class HeaderRangeGuard(io.BytesIO):
    def __init__(self, content, allowed):
        super().__init__(content)
        self.allowed = allowed
        self.calls = []

    def read(self, size=-1):
        span = (self.tell(), self.tell() + size)
        self.calls.append(span)
        if size != 2880 or span not in self.allowed:
            raise AssertionError("payload read attempted")
        return super().read(size)


class IndependentStructureTests(unittest.TestCase):
    def test_arrays_between_headers_are_skipped(self):
        output = io.BytesIO()
        table = fits.BinTableHDU.from_columns([
            fits.Column(name="VALUE", format="D", array=np.arange(10.))])
        fits.HDUList([fits.PrimaryHDU(np.ones((3, 3))), table,
                      fits.ImageHDU(np.ones((3, 3)))]).writeto(output)
        body = output.getvalue()
        allowed = [(0, 2880), (5760, 8640), (11520, 14400)]
        stream = HeaderRangeGuard(body, allowed)
        result = reader.structure(stream, len(body))
        self.assertEqual(result["hdu_count"], 3)
        self.assertEqual(stream.calls, allowed)
        self.assertEqual(result["declared_data_region_bytes_read"], 0)
        self.assertNotIn("data_region_bytes_read", result)

    def test_missing_end_cannot_guarantee_no_payload_reads(self):
        body = table_file()
        header = body[2880:5760].replace(b"END" + b" " * 77, b" " * 80)
        body = body[:2880] + header + body[5760:]
        stream = HeaderRangeGuard(body, [(0, 2880), (2880, 5760)])
        # Explicitly demonstrates the malformed-header limitation, not a desired
        # feature. A future early rejection is also a safe resolution.
        try:
            reader.structure(stream, len(body))
        except ValueError:
            return
        except AssertionError as exc:
            self.assertIn("payload read attempted", str(exc))
            return
        self.fail("malformed header reported success")

    def test_binary_table_bitpix_must_be_eight(self):
        body = altered_table("BITPIX", 16)
        with self.assertRaises(ValueError):
            reader.structure(io.BytesIO(body), len(body))

    def test_binary_table_gcount_must_be_one(self):
        body = altered_table("GCOUNT", 2)
        with self.assertRaises(ValueError):
            reader.structure(io.BytesIO(body), len(body))

    def test_binary_table_required_pcount_not_defaulted(self):
        body = altered_table("PCOUNT", delete=True)
        with self.assertRaises(ValueError):
            reader.structure(io.BytesIO(body), len(body))

    def test_binary_table_required_tform_present(self):
        body = altered_table("TFORM1", delete=True)
        with self.assertRaises(ValueError):
            reader.structure(io.BytesIO(body), len(body))

    def test_packed_bits_variable_descriptors_and_heap_skip(self):
        formats = ["14X", "1PE", "1QD", "16A", "2C", "3M"]
        # Independent expected row widths: 2 + 8 + 16 + 16 + 16 + 48 = 106.
        # The heap is skipped; this fixture does not claim valid pointed-to data.
        cards = [("XTENSION", "BINTABLE"), ("BITPIX", 8), ("NAXIS", 2),
                 ("NAXIS1", 106), ("NAXIS2", 1), ("PCOUNT", 2890),
                 ("GCOUNT", 1), ("TFIELDS", len(formats))]
        cards += [(f"TFORM{i}", value) for i, value in enumerate(formats, 1)]
        primary = fits.PrimaryHDU().header.tostring().encode("ascii")
        header = fits.Header(cards).tostring().encode("ascii")
        final = fits.ImageHDU().header.tostring().encode("ascii")
        body = primary + header + b"\0" * 5760 + final
        allowed = [(0, 2880), (2880, 5760), (11520, 14400)]
        stream = HeaderRangeGuard(body, allowed)
        result = reader.structure(stream, len(body))
        self.assertEqual(stream.calls, allowed)
        self.assertEqual(result["hdus"][1]["data_bytes"], 2996)
        self.assertEqual(result["hdus"][1]["data_span_padded"], 5760)

    def test_row_width_mismatch_rejected(self):
        body = altered_table("NAXIS1", 9)
        with self.assertRaisesRegex(ValueError, "STOP_BINARY_TABLE_WIDTH"):
            reader.structure(io.BytesIO(body), len(body))

    def test_ascii_tables_explicitly_unsupported(self):
        body = altered_table("XTENSION", "TABLE")
        with self.assertRaisesRegex(ValueError, "STOP_EXTENSION_TYPE"):
            reader.structure(io.BytesIO(body), len(body))


if __name__ == "__main__":
    unittest.main()
