"""Pre-request mirror identity, mask, unit and fixed-tolerance validation."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location("m1c_test", Path(__file__).resolve().parents[1] / "scripts/m1c.py")
m1c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1c)


def fixture(*, units=None, duplicate=False, pmra="1", status="OK", id_type="long"):
    unit_names = {"ra": "deg", "dec": "deg", "ref_epoch": "yr", "pmra": "mas.yr**-1",
                  "pmdec": "mas/yr", "phot_g_mean_mag": "mag"}
    unit_names.update(units or {})
    fields = []
    for name in m1c.m1b.FIELDS:
        unit = f' unit="{unit_names[name]}"' if name in unit_names else ""
        kind = id_type if name == "source_id" else "double"
        fields.append(f'<FIELD name="{name}" datatype="{kind}"{unit}/>')
    row = ('<TR><TD>9007199254741115</TD><TD>150</TD><TD>-30</TD><TD>2016</TD>'
           f'<TD>{pmra}</TD><TD>2</TD><TD>18</TD><TD>1.1</TD></TR>')
    return ('<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.3"><RESOURCE>'
            f'<INFO name="QUERY_STATUS" value="{status}"/><TABLE>{"".join(fields)}'
            f'<DATA><TABLEDATA>{row * (2 if duplicate else 1)}</TABLEDATA></DATA>'
            '</TABLE></RESOURCE></VOTABLE>')


class MirrorParityTests(unittest.TestCase):
    def parse(self, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.xml"
            path.write_text(fixture(**kwargs), encoding="utf-8")
            return m1c.strict_catalog(path)

    def test_int64_and_equivalent_unit_spellings(self):
        table = self.parse()
        self.assertEqual(table["source_id"][0], 9007199254741115)
        self.assertEqual(m1c.compare_tables(table, self.parse(units={"pmra": "mas/yr"}), 1)["status"], "PARITY_PASS")

    def test_wrong_or_missing_units(self):
        for name, unit in (("ra", "rad"), ("pmra", "arcsec/yr"), ("ref_epoch", "d"),
                           ("ra", ""), ("phot_g_mean_mag", ""), ("source_id", "s"), ("ruwe", "mag")):
            with self.subTest(name=name, unit=unit), self.assertRaisesRegex(ValueError, "STOP_CATALOG_UNITS"):
                self.parse(units={name: unit})

    def test_duplicate_source_ids(self):
        with self.assertRaisesRegex(ValueError, "STOP_DUPLICATE_SOURCE_IDS"):
            self.parse(duplicate=True)

    def test_mask_mismatch_and_matched_masks(self):
        masked = self.parse(pmra="")
        self.assertTrue(np.ma.getmaskarray(masked["pmra"])[0])
        self.assertEqual(m1c.compare_tables(masked, masked.copy(), 1)["columns"]["pmra"]["masked"], 1)
        with self.assertRaisesRegex(ValueError, "mask:pmra"):
            m1c.compare_tables(masked, self.parse(), 1)

    def test_changed_numeric_values_and_tolerance(self):
        table = self.parse()
        for name, tolerance in m1c.TOLERANCES.items():
            changed = table.copy()
            changed[name][0] += tolerance / 2
            m1c.compare_tables(table, changed, 1)
            changed[name][0] += tolerance * 2
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, f"value:{name}"):
                m1c.compare_tables(table, changed, 1)

    def test_changed_id_and_wrong_row_count(self):
        table = self.parse()
        changed = table.copy()
        changed["source_id"][0] += 1
        with self.assertRaisesRegex(ValueError, "source_id"):
            m1c.compare_tables(table, changed, 1)
        with self.assertRaisesRegex(ValueError, "row_count"):
            m1c.compare_tables(table, table)

    def test_nonfinite_unmasked_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "STOP_CATALOG_NONFINITE"):
            self.parse(pmra="inf")

    def test_bad_status_and_id_type(self):
        with self.assertRaisesRegex(ValueError, "STOP_CATALOG_STATUS"):
            self.parse(status="OVERFLOW")
        with self.assertRaisesRegex(ValueError, "STOP_SOURCE_ID_TYPE"):
            self.parse(id_type="double")


if __name__ == "__main__":
    unittest.main()
