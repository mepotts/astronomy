"""Independent M1d2 metadata and harness-isolation tests; synthetic inputs only."""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

SPEC = importlib.util.spec_from_file_location("m1d2_review_fixture", Path(__file__).with_name("test_m1d2.py"))
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)
M = F.M


class IndependentAdapterTests(unittest.TestCase):
    def test_reference_cannot_be_redirected_to_param_or_duplicate_field(self):
        for content in (
            F.fixture().replace(b'ID="source_id"', b'ID="other"').replace(
                b'</TABLE>', b'</TABLE><PARAM ID="source_id" name="source_id"/>'),
            F.fixture().replace(b'</TABLE>', b'<FIELD ID="source_id" name="source_id"/></TABLE>'),
        ):
            with self.assertRaisesRegex(ValueError, "SERVICE_REFERENCE"):
                M.adapt(content)

    def test_descriptor_deep_children_attributes_and_external_references_stop(self):
        for old, new in (
            (b'<DESCRIPTION>Inert service description</DESCRIPTION>', b'<DESCRIPTION><LINK href="https://invalid/"/></DESCRIPTION>'),
            (b'<GROUP name="inputParams">', b'<GROUP name="inputParams" ref="external">'),
            (b'ref="source_id" value=""/>', b'ref="source_id" value=""><VALUES null="0"/></PARAM>'),
            (b'<DESCRIPTION>Inert URL description</DESCRIPTION>', b'<DESCRIPTION href="file:///private"/>'),
            (b'<DESCRIPTION>Inert URL description</DESCRIPTION>', b'<DESCRIPTION><INFO name="QUERY_STATUS" value="ERROR"/></DESCRIPTION>'),
        ):
            with self.subTest(new=new), self.assertRaises(ValueError):
                M.adapt(F.fixture().replace(old, new))

    def test_table_stream_and_field_metadata_preserved_exactly_in_memory(self):
        original = M.ET.fromstring(F.fixture())
        table = original.find('.//' + M.NS + 'TABLE')
        before = M.ET.tostring(table)
        stream_before = table.find('.//' + M.NS + 'STREAM').text
        with mock.patch.object(M.BASE, "decode", side_effect=AssertionError("numeric decoding forbidden")):
            sanitized, receipt = M.adapt(F.fixture())
        after = M.ET.fromstring(sanitized).find('.//' + M.NS + 'TABLE')
        self.assertEqual(before, M.ET.tostring(after))
        self.assertEqual(stream_before, after.find('.//' + M.NS + 'STREAM').text)
        self.assertTrue(receipt["original_results_subtree_unchanged"])

    def test_extra_table_outside_descriptor_still_rejected_by_original_decoder(self):
        content = F.fixture().replace(b'</VOTABLE>', b'<TABLE/></VOTABLE>')
        with self.assertRaisesRegex(ValueError, "TABLE_STRUCTURE"):
            M.decode(content)


class IndependentHarnessIsolationTests(unittest.TestCase):
    def test_stage_rebindings_and_runtime_redirect_do_not_mutate_fresh_original(self):
        harness = M.original()
        untouched = M.original()
        original_decode = harness.decode
        original_root = harness.ROOT
        capture = mock.Mock()

        def check_bound_harness():
            for name in ("MANIFEST", "RESULT", "ATTEMPT", "WORKER_START", "OUTCOME"):
                self.assertEqual(getattr(harness, name), Path(str(getattr(untouched, name)).replace("m1d-", "m1d2-")))
            self.assertEqual(harness.__file__, M.__file__)
            self.assertIs(harness.execute, M.execute)
            self.assertIs(harness.dependencies, M.dependencies)
            self.assertIs(harness.decode, original_decode)
            self.assertEqual(harness.ROOT, original_root)
            harness.OLD.m1.save(M.ROOT / "out/m1d-runtime.json", {"synthetic": 1})
            harness.OLD.m1.save(M.ROOT / "out/unrelated.json", {"synthetic": 2})

        with mock.patch.object(M, "BASE", harness), mock.patch.object(harness, "main", side_effect=check_bound_harness), \
                mock.patch.object(harness.OLD.m1, "save", capture):
            M.main()
            self.assertIs(harness.OLD.m1.save, capture)
        self.assertEqual(capture.call_args_list, [
            mock.call(M.ROOT / "out/m1d2-runtime.json", {"synthetic": 1}),
            mock.call(M.ROOT / "out/unrelated.json", {"synthetic": 2}),
        ])
        self.assertEqual(untouched.RESULT.name, "m1d-result.json")
        self.assertEqual(untouched.MANIFEST.name, "m1d-manifest.json")
        self.assertEqual(Path(untouched.__file__).name, "m1d.py")
        self.assertIsNot(untouched.execute, M.execute)
        self.assertIsNot(untouched.dependencies, M.dependencies)

    def test_stage_save_restored_even_on_worker_exception(self):
        harness = M.original()
        save = harness.OLD.m1.save
        with mock.patch.object(M, "BASE", harness), \
                mock.patch.object(harness, "main", side_effect=RuntimeError("synthetic worker failure")), \
                self.assertRaisesRegex(RuntimeError, "synthetic worker failure"):
            M.main()
        self.assertIs(harness.OLD.m1.save, save)

    def test_dependency_collector_rechecks_original_manifest_and_stop(self):
        preserved = M.original()
        with mock.patch.object(M, "original", return_value=preserved), \
                mock.patch.object(preserved, "dependencies", return_value={"old": "changed"}), \
                mock.patch.object(preserved.OLD, "read_json", return_value={"dependencies": {"old": "frozen"}}), \
                self.assertRaisesRegex(ValueError, "M1D_PROVENANCE"):
            M.dependencies()
        with mock.patch.object(M, "original", return_value=preserved), \
                mock.patch.object(preserved, "dependencies", return_value={"old": "frozen"}), \
                mock.patch.object(preserved.OLD, "read_json", side_effect=[{"dependencies": {"old": "frozen"}}, {"error": "unexpected"}]), \
                self.assertRaisesRegex(ValueError, "M1D_OUTCOME"):
            M.dependencies()


if __name__ == "__main__":
    unittest.main()
