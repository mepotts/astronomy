"""Ancillary service metadata is inert and cannot hide scientific data/status."""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = load("m1d2_test", ROOT / "scripts/m1d2.py")
FIXTURE = load("m1d2_fixture", ROOT / "tests/test_m1d.py")
DESCRIPTOR = (b'<RESOURCE type="meta" utype="adhoc:service" name="Datalink_GaiaDR3">'
              b'<DESCRIPTION>Inert service description</DESCRIPTION>'
              b'<PARAM arraysize="51" datatype="char" name="accessURL" ucd="meta.ref.url" '
              b'value="https://gaia.ari.uni-heidelberg.de/datalink/gaiadr3">'
              b'<DESCRIPTION>Inert URL description</DESCRIPTION></PARAM>'
              b'<GROUP name="inputParams"><PARAM name="sourceid" datatype="long" '
              b'ref="source_id" value=""/></GROUP></RESOURCE>')


def fixture():
    return FIXTURE.fixture().replace(b'ID="SOURCE_ID"', b'ID="source_id"').replace(
        b'</VOTABLE>', DESCRIPTOR + b'</VOTABLE>')


class DescriptorTests(unittest.TestCase):
    def test_metadata_only_adapter_never_invokes_decoder(self):
        with mock.patch.object(M.BASE, "decode", side_effect=AssertionError("no rows")):
            sanitized, audit = M.adapt(fixture())
        self.assertNotIn(b'adhoc:service', sanitized)
        self.assertTrue(audit["original_results_subtree_unchanged"])
        self.assertEqual(audit["ignored_service_url_not_fetched"], M.SERVICE)

    def test_unchanged_decoder_recovers_exact_fixture(self):
        table = M.decode(fixture())
        self.assertEqual(table["source_id"][0], 2**53 + 1)
        self.assertEqual(table["ra"][0], FIXTURE.ROW[1])
        reference = M.BASE.validate(M.BASE.decode(FIXTURE.fixture()))
        self.assertEqual(M.BASE.OLD.compare_tables(reference, table, 1)["status"], "PARITY_PASS")

    def test_metadata_cannot_hide_data_or_status(self):
        for element in (b'<TABLE/>', b'<FIELD name="hidden"/>', b'<DATA/>', b'<STREAM/>',
                        b'<RESOURCE/>', b'<INFO name="QUERY_STATUS" value="OVERFLOW"/>'):
            altered = DESCRIPTOR.replace(b'</RESOURCE>', element + b'</RESOURCE>')
            with self.subTest(element=element), self.assertRaises(ValueError):
                M.adapt(fixture().replace(DESCRIPTOR, altered))

    def test_late_overflow_outside_resource_stops(self):
        with self.assertRaisesRegex(ValueError, "QUERY_STATUS"):
            M.adapt(fixture().replace(b'</VOTABLE>', b'<INFO name="QUERY_STATUS" value="OVERFLOW"/></VOTABLE>'))

    def test_service_profile_url_and_reference_must_be_exact(self):
        for old, new in ((b'type="meta"', b'type="results"'), (b'adhoc:service', b'other'),
                         (b'Datalink_GaiaDR3', b'other'), (b'inputParams', b'other'),
                         (b'ref="source_id"', b'ref="other"'), (b'value=""', b'value="1"'),
                         (M.SERVICE.encode(), b'https://invalid/'), (b'ID="source_id"', b'ID="other"')):
            with self.subTest(new=new), self.assertRaises(ValueError):
                M.adapt(fixture().replace(old, new))

    def test_extra_or_nested_resources_and_duplicate_reference_rejected(self):
        for element in (DESCRIPTOR, b'<RESOURCE/>', b'<PARAM ID="source_id"/>'):
            with self.subTest(element=element), self.assertRaises(ValueError):
                M.adapt(fixture().replace(b'</VOTABLE>', element + b'</VOTABLE>'))
        with self.assertRaises(ValueError):
            M.adapt(fixture().replace(b'</TABLE>', b'</TABLE><RESOURCE type="meta"/>'))

    def test_profile_bounds_encoding_and_foreign_namespace(self):
        for content in (b' ' * 5_000_001, b'<!DOCTYPE VOTABLE>' + fixture(), b'\x00' + fixture(),
                        b'<?xml version="1.0" encoding="ISO-8859-1"?>' + fixture(),
                        fixture().replace(b'</VOTABLE>', b'<TABLE xmlns=""/></VOTABLE>')):
            with self.assertRaises(ValueError):
                M.adapt(content)

    def test_results_schema_is_not_weakened(self):
        with self.assertRaisesRegex(ValueError, "SCHEMA"):
            M.decode(fixture().replace(b'name="ra"', b'name="unexpected"'))
        with self.assertRaisesRegex(ValueError, "CATALOG_UNITS"):
            M.decode(fixture().replace(b'unit="deg"', b'unit="rad"'))


if __name__ == "__main__":
    unittest.main()
