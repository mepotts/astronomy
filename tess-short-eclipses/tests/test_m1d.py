"""Synthetic serialization tests; no retained catalog or network access."""

import base64
import importlib.util
import struct
import unittest
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location("m1d_test", Path(__file__).parents[1] / "scripts/m1d.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
UNIT = (None, "deg", "deg", "yr", "mas/yr", "mas.yr**-1", "mag", None)
ROW = (2**53 + 1, 120.5, -30.2, 2016., -0., 1.5, 18.2, 1.1)


def fixture(rows=(ROW,), raw=None):
    fields = []
    for i, (name, kind, unit) in enumerate(zip(M.NAMES, M.TYPES, UNIT, strict=True)):
        attributes = f'name="{name}" ID="{name.upper()}" datatype="{kind}"'
        if unit:
            attributes += f' unit="{unit}"'
        null = '<VALUES null="-9223372036854775808"/>' if i == 0 else ""
        fields.append(f'<FIELD {attributes}>{null}</FIELD>')
    payload = raw if raw is not None else b"".join(struct.pack(">q5d2f", *row) for row in rows)
    return (f'<VOTABLE xmlns="{M.NS[1:-1]}" version="1.4"><RESOURCE type="results">'
            '<INFO name="QUERY_STATUS" value="OK"/><TABLE>' + "".join(fields)
            + '<DATA><BINARY><STREAM encoding="base64">' + base64.b64encode(payload).decode()
            + '</STREAM></BINARY></DATA></TABLE></RESOURCE></VOTABLE>').encode()


class BinaryDecoderTests(unittest.TestCase):
    def test_exact_ids_no_mixed_float_coercion(self):
        ids = (2**53 + 1, 2**53 + 2, -1, -(2**63), 2**63 - 1)
        table = M.decode(fixture(tuple((value, *ROW[1:]) for value in ids)))
        np.testing.assert_array_equal(np.asarray(table["source_id"]), ids)
        np.testing.assert_array_equal(np.ma.getmaskarray(table["source_id"]), [False, False, False, True, False])
        self.assertEqual(table["source_id"].dtype.itemsize, 8)

    def test_valid_units_names_and_signed_zero(self):
        table = M.validate(M.decode(fixture()))
        self.assertEqual(tuple(table.colnames), M.NAMES)
        self.assertTrue(np.signbit(table["pmra"][0]))
        self.assertEqual(table["source_id"][0], ROW[0])

    def test_null_optional_fields_not_zero_filled(self):
        for index in (4, 5, 6, 7):
            row = list(ROW)
            row[index] = float("nan")
            table = M.validate(M.decode(fixture((row,))))
            self.assertTrue(np.ma.getmaskarray(table[M.NAMES[index]])[0])

    def test_required_nan_and_infinities_fail_catalog(self):
        for index, value in ((1, float("nan")), (2, float("nan")), (3, float("nan")),
                             (4, float("inf")), (6, float("-inf"))):
            row = list(ROW)
            row[index] = value
            with self.subTest(index=index), self.assertRaises(ValueError):
                M.validate(M.decode(fixture((row,))))

    def test_id_null_negative_zero_duplicate_rejected(self):
        for ids in ((-1,), (0,), (-(2**63),), (ROW[0], ROW[0])):
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, "CATALOG_IDS"):
                M.validate(M.decode(fixture(tuple((value, *ROW[1:]) for value in ids))))

    def test_special_ieee_payload_and_subnormal(self):
        raw = bytearray(struct.pack(">q5d2f", *ROW))
        raw[32:40] = bytes.fromhex("fff8000000000001")
        raw[40:48] = bytes.fromhex("0000000000000001")
        raw[48:52] = bytes.fromhex("7fc00001")
        table = M.validate(M.decode(fixture(raw=bytes(raw))))
        self.assertTrue(table["pmra"].mask[0])
        self.assertTrue(table["phot_g_mean_mag"].mask[0])
        self.assertEqual(table["pmdec"][0], np.nextafter(0., 1.))

    def test_wrong_units_and_positions(self):
        with self.assertRaisesRegex(ValueError, "UNITS"):
            M.validate(M.decode(fixture().replace(b'unit="deg"', b'unit="rad"')))
        with self.assertRaisesRegex(ValueError, "POSITIONS"):
            M.validate(M.decode(fixture(((ROW[0], 361., *ROW[2:]),))))

    def test_schema_and_null_declaration_rejections(self):
        replacements = [(b'datatype="long"', b'datatype="double"'),
                        (b'name="ra"', b'name="dec"'), (b'datatype="float"', b'datatype="double"'),
                        (b'name="ra"', b'name="ra" arraysize="1"'),
                        (b'name="ra"', b'name="ra" xtype="x"'),
                        (b'-9223372036854775808', b'-9223372036854775809'),
                        (b'-9223372036854775808', b'1.0'),
                        (b'<VALUES null=', b'<VALUES ref="elsewhere" null='),
                        (b'<DATA>', b'<FIELD name="extra" datatype="float"/><DATA>')]
        for old, new in replacements:
            with self.subTest(new=new), self.assertRaises(ValueError):
                M.decode(fixture().replace(old, new))

    def test_structural_and_remote_rejections(self):
        replacements = [(b'<STREAM encoding="base64">', b'<STREAM encoding="base64" href="https://invalid/">'),
                        (b'encoding="base64"', b'encoding="gzip"'), (b'BINARY>', b'BINARY2>'),
                        (b'</TABLE>', b'</TABLE><TABLE/>'),
                        (b'</BINARY>', b'<STREAM encoding="base64"/></BINARY>'),
                        (b'</RESOURCE>', b'<INFO name="QUERY_STATUS" value="OVERFLOW"/></RESOURCE>'),
                        (b'<VOTABLE', b'<!DOCTYPE VOTABLE [<!ENTITY x "y">]><VOTABLE')]
        for old, new in replacements:
            with self.subTest(new=new), self.assertRaises(ValueError):
                M.decode(fixture().replace(old, new))

    def test_row_lengths_counts_and_base64(self):
        raw = struct.pack(">q5d2f", *ROW)
        for body in (b"", raw[:-1], raw + b"x", raw * 5001):
            with self.subTest(size=len(body)), self.assertRaises(ValueError):
                M.decode(fixture(raw=body))
        for value in (b'2', b'1.0', b'-1'):
            with self.assertRaisesRegex(ValueError, "DECLARED_ROWS"):
                M.decode(fixture().replace(b'<TABLE>', b'<TABLE nrows="' + value + b'">'))
        with self.assertRaisesRegex(ValueError, "BASE64"):
            M.decode(fixture().replace(b'</STREAM>', b'!</STREAM>'))
        M.decode(fixture().replace(b'</STREAM>', b' \r\n\t</STREAM>'))

    def test_fixed_parity_detects_changed_values(self):
        table = M.validate(M.decode(fixture()))
        self.assertEqual(M.OLD.compare_tables(table, table.copy(), 1)["status"], "PARITY_PASS")
        other = table.copy()
        other["ra"][0] += 1e-8
        with self.assertRaisesRegex(ValueError, "value:ra"):
            M.OLD.compare_tables(table, other, 1)


if __name__ == "__main__":
    unittest.main()
