"""Strict field-name parsing and 64-bit identifier preservation."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("m1b_tests", Path(__file__).resolve().parents[1] / "scripts/m1b.py")
m1b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1b)


def fixture(source_type="long", extra="", status="OK"):
    columns = ''.join(f'<FIELD name="{name}" datatype="double"/>' for name in m1b.FIELDS[1:])
    return (f'<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.3"><RESOURCE>'
            f'<INFO name="QUERY_STATUS" value="{status}"/><TABLE>'
            f'<FIELD ID="SOURCE_ID" name="source_id" datatype="{source_type}"/>{columns}{extra}'
            '<DATA><TABLEDATA><TR><TD>9007199254741115</TD><TD>150</TD><TD>-30</TD>'
            '<TD>2016</TD><TD>1</TD><TD>2</TD><TD>18</TD><TD>1.1</TD>'
            '</TR></TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>')


class StrictCatalogTests(unittest.TestCase):
    def parse_fixture(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.xml"
            path.write_text(text, encoding="utf-8")
            return m1b.strict_catalog(path)

    def test_names_override_uppercase_ids_without_precision_loss(self):
        table = self.parse_fixture(fixture())
        self.assertEqual(table.colnames, m1b.FIELDS)
        self.assertEqual(int(table["source_id"][0]), 9007199254741115)
        self.assertEqual(table["source_id"].dtype.itemsize, 8)

    def test_duplicate_field_names_rejected_before_table_parsing(self):
        with self.assertRaisesRegex(ValueError, "STOP_CATALOG_FIELDS"):
            self.parse_fixture(fixture(extra='<FIELD name="source_id" datatype="long"/>'))

    def test_floating_source_identifiers_rejected(self):
        with self.assertRaisesRegex(ValueError, "STOP_SOURCE_ID_TYPE"):
            self.parse_fixture(fixture(source_type="double"))

    def test_overflow_and_error_status_rejected(self):
        for status in ("ERROR", "OVERFLOW"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "STOP_CATALOG_STATUS"):
                self.parse_fixture(fixture(status=status))

    def test_missing_required_field_rejected(self):
        with self.assertRaisesRegex(ValueError, "STOP_CATALOG_FIELDS"):
            self.parse_fixture(fixture().replace('name="ruwe"', 'name="unexpected"'))


if __name__ == "__main__":
    unittest.main()
