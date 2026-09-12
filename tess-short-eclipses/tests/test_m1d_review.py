"""Independent synthetic M1d adversarial checks; never opens retained payloads."""

import base64
import importlib.util
import itertools
import struct
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

SPEC = importlib.util.spec_from_file_location("independent_m1d", Path(__file__).parents[1] / "scripts/m1d.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

NAMES = ("source_id", "ra", "dec", "ref_epoch", "pmra", "pmdec", "phot_g_mean_mag", "ruwe")
KINDS = ("long", "double", "double", "double", "double", "double", "float", "float")
UNITS = (None, "deg", "deg", "yr", "mas/yr", "mas/yr", "mag", None)


def row_bytes(identifier=9007199254740993):
    # Independent writer: explicit integer bytes plus independently packed scalar
    # fields, not the decoder's ROW format object or its schema constants.
    return identifier.to_bytes(8, "big", signed=True) + b"".join(
        struct.pack(">d", v) for v in (12.5, -23.25, 2016., -4.5, 0.25)
    ) + struct.pack(">f", 18.5) + struct.pack(">f", 1.25)


def xml(payload=None, *, sentinel="-9223372036854775808"):
    fields = []
    for i, (name, kind, unit) in enumerate(zip(NAMES, KINDS, UNITS, strict=True)):
        attributes = f'name="{name}" ID="column{i}" datatype="{kind}"'
        if unit is not None:
            attributes += f' unit="{unit}"'
        body = f'<VALUES null="{sentinel}"/>' if i == 0 else ""
        fields.append(f"<FIELD {attributes}>{body}</FIELD>")
    encoded = base64.b64encode(row_bytes() if payload is None else payload).decode("ascii")
    return ('<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.4">'
            '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/><TABLE>'
            + "".join(fields) + '<DATA><BINARY><STREAM encoding="base64">' + encoded
            + '</STREAM></BINARY></DATA></TABLE></RESOURCE></VOTABLE>').encode("utf-8")


class IndependentDecoderTests(unittest.TestCase):
    def test_explicit_offsets_values_and_storage_types(self):
        table = M.validate(M.decode(xml()))
        self.assertEqual(tuple(table.colnames), NAMES)
        self.assertEqual(M.ROW.size, 56)
        self.assertEqual(int(table["source_id"][0]), 9007199254740993)
        for name, expected, size in zip(NAMES[1:], (12.5, -23.25, 2016., -4.5, .25, 18.5, 1.25),
                                       (8, 8, 8, 8, 8, 4, 4), strict=True):
            self.assertEqual(float(table[name][0]), expected)
            self.assertEqual(table[name].dtype.itemsize, size)

    def test_positive_int64_max_and_adjacent_large_ids(self):
        ids = (2**53 + 1, 2**53 + 2, 2**63 - 2, 2**63 - 1)
        table = M.validate(M.decode(xml(b"".join(row_bytes(i) for i in ids))))
        self.assertEqual(tuple(map(int, table["source_id"])), ids)

    def test_custom_positive_null_sentinel_is_respected(self):
        table = M.decode(xml(row_bytes(17), sentinel="17"))
        self.assertTrue(np.ma.getmaskarray(table["source_id"])[0])
        self.assertEqual(int(np.asarray(table["source_id"])[0]), 17)
        with self.assertRaisesRegex(ValueError, "CATALOG_IDS"):
            M.validate(table)

    def test_infinities_are_not_masked_in_any_float_column(self):
        for index, start in enumerate((8, 16, 24, 32, 40, 48, 52), 1):
            code = ">d" if index <= 5 else ">f"
            for value in (float("inf"), -float("inf")):
                raw = bytearray(row_bytes())
                encoded = struct.pack(code, value)
                raw[start:start + len(encoded)] = encoded
                with self.subTest(column=NAMES[index], value=value):
                    table = M.decode(xml(raw))
                    self.assertFalse(np.ma.getmaskarray(table[NAMES[index]])[0])
                    with self.assertRaisesRegex(ValueError, "NONFINITE"):
                        M.validate(table)

    def test_distinct_nan_payloads_each_optional_column(self):
        for index, start in ((4, 32), (5, 40), (6, 48), (7, 52)):
            patterns = ("7ff8000000000001", "fff0000000000001") if index <= 5 else ("7fc00001", "ff800001")
            for pattern in patterns:
                raw = bytearray(row_bytes())
                raw[start:start + len(bytes.fromhex(pattern))] = bytes.fromhex(pattern)
                with self.subTest(column=NAMES[index], pattern=pattern):
                    table = M.validate(M.decode(xml(raw)))
                    self.assertTrue(np.ma.getmaskarray(table[NAMES[index]])[0])

    def test_float32_subnormal_and_negative_zero_survive(self):
        raw = bytearray(row_bytes())
        raw[48:52], raw[52:56] = bytes.fromhex("00000001"), bytes.fromhex("80000000")
        table = M.validate(M.decode(xml(raw)))
        self.assertEqual(table["phot_g_mean_mag"][0], np.nextafter(np.float32(0), np.float32(1)))
        self.assertTrue(np.signbit(table["ruwe"][0]))

    def test_oracle_value_corruption_forces_stop(self):
        original = M.np.frombuffer

        def corrupted(*args, **kwargs):
            array = original(*args, **kwargs).copy()
            array["source_id"][0] += 1
            return array

        with mock.patch.object(M.np, "frombuffer", side_effect=corrupted), \
                self.assertRaisesRegex(ValueError, "DECODER_DISAGREEMENT"):
            M.decode(xml())

    def test_oracle_signed_zero_corruption_forces_stop(self):
        raw = bytearray(row_bytes())
        raw[32:40] = bytes.fromhex("8000000000000000")
        original = M.np.frombuffer

        def corrupted(*args, **kwargs):
            array = original(*args, **kwargs).copy()
            array["pmra"][0] = 0.
            return array

        with mock.patch.object(M.np, "frombuffer", side_effect=corrupted), \
                self.assertRaisesRegex(ValueError, "DECODER_DISAGREEMENT"):
            M.decode(xml(raw))

    def test_byte_swapped_payload_does_not_recover_original_identity(self):
        raw = row_bytes()
        offsets = (0, 8, 16, 24, 32, 40, 48, 52, 56)
        swapped = b"".join(raw[a:b][::-1] for a, b in itertools.pairwise(offsets))
        table = M.decode(xml(swapped))
        self.assertNotEqual(int(table["source_id"][0]), 9007199254740993)

    def test_missing_and_referenced_null_are_rejected(self):
        for body in (b"", b'<VALUES ref="someOtherValues"/>', b'<VALUES null=""/>',
                     b'<VALUES null="9223372036854775808"/>'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                M.decode(xml().replace(b'<VALUES null="-9223372036854775808"/>', body))

    def test_floating_null_declaration_not_silently_ignored(self):
        data = xml().replace(b'ID="column4" datatype="double" unit="mas/yr"></FIELD>',
                             b'ID="column4" datatype="double" unit="mas/yr"><VALUES null="-4.5"/></FIELD>')
        self.assertNotEqual(data, xml())
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_FLOAT_VALUES"):
            M.decode(data)

    def test_all_unit_scale_mismatches_rejected(self):
        for old, new in ((b'unit="deg"', b'unit="arcsec"'), (b'unit="yr"', b'unit="d"'),
                         (b'unit="mas/yr"', b'unit="arcsec/yr"'), (b'unit="mag"', b'unit=""'),
                         (b'name="ruwe"', b'name="ruwe" unit="mag"'),
                         (b'name="source_id"', b'name="source_id" unit="s"')):
            with self.subTest(new=new), self.assertRaises(ValueError):
                M.validate(M.decode(xml().replace(old, new)))

    def test_numeric_field_order_is_not_inferred_from_values(self):
        data = xml().replace(b'name="ra"', b'name="temporary"').replace(b'name="dec"', b'name="ra"').replace(b'name="temporary"', b'name="dec"')
        with self.assertRaisesRegex(ValueError, "SCHEMA"):
            M.decode(data)

    def test_missing_status_and_late_error_stop(self):
        for data in (xml().replace(b'<INFO name="QUERY_STATUS" value="OK"/>', b""),
                     xml().replace(b'</RESOURCE>', b'<INFO name="QUERY_STATUS" value="ERROR"/></RESOURCE>')):
            with self.assertRaisesRegex(ValueError, "QUERY_STATUS"):
                M.decode(data)

    def test_no_remote_or_nested_stream_content(self):
        for replacement in (b'<STREAM encoding="base64" href="file:///private">',
                            b'<STREAM encoding="base64" xmlns:x="urn:x" x:href="https://invalid/">',
                            b'<STREAM encoding="base64"><child/>'):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                M.decode(xml().replace(b'<STREAM encoding="base64">', replacement))

    def test_canonical_padding_bits_required(self):
        encoded = base64.b64encode(row_bytes())
        alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        malformed = encoded[:-2] + bytes([alphabet[alphabet.index(encoded[-2]) + 1]]) + b"="
        self.assertEqual(base64.b64decode(encoded), base64.b64decode(malformed))
        with self.assertRaisesRegex(ValueError, "NONCANONICAL_BASE64"):
            M.decode(xml().replace(encoded, malformed))

    def test_bounds_and_null_encoding_before_xml_parser(self):
        with mock.patch.object(M.ET, "fromstring") as parser:
            for content in (b" " * 5_000_001, b"<!DOCTYPE VOTABLE>", b"<!ENTITY x 'y'>"):
                with self.assertRaisesRegex(ValueError, "XML_BOUND_OR_DECLARATION"):
                    M.decode(content)
            parser.assert_not_called()
        with self.assertRaisesRegex(ValueError, "XML_ENCODING"):
            M.decode(b"\x00" + xml())

    def test_unexpected_namespace_structural_nodes_rejected(self):
        for element in (b'<TABLE xmlns=""/>', b'<DATA xmlns=""/>', b'<FIELD xmlns="" name="extra"/>'):
            with self.subTest(element=element), self.assertRaises(ValueError):
                M.decode(xml().replace(b'</RESOURCE>', element + b'</RESOURCE>'))

    def test_non_utf8_xml_declaration_is_rejected(self):
        data = b'<?xml version="1.0" encoding="ISO-8859-1"?>' + xml()
        with self.assertRaises(ValueError):
            M.decode(data)


class IndependentHarnessTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        root = Path(directory)
        self.stack.enter_context(mock.patch.object(M, "ROOT", root))
        for name in ("MANIFEST", "RESULT", "ATTEMPT", "WORKER_START", "OUTCOME"):
            self.stack.enter_context(mock.patch.object(M, name, root / (name.lower() + ".json")))
        M.OLD.m1.save(M.MANIFEST, {"dependencies": {"synthetic": "digest"}})
        self.decode = self.stack.enter_context(mock.patch.object(M, "decode"))
        self.real_execute = M.execute
        self.execute = self.stack.enter_context(mock.patch.object(M, "execute", return_value={"status": "SYNTHETIC"}))
        self.stack.enter_context(mock.patch.object(M, "peak_memory", return_value=10_000))
        self.stack.enter_context(mock.patch("builtins.print"))

    def main(self, *arguments):
        with mock.patch.object(M.sys, "argv", ["synthetic_m1d.py", *arguments]):
            return M.main()

    def runner(self, *, return_value=(0, "synthetic completed"), side_effect=None):
        fake = SimpleNamespace(bounded_run=mock.Mock(return_value=return_value, side_effect=side_effect))
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=mock.Mock()))
        self.stack.enter_context(mock.patch.object(M.importlib.util, "spec_from_file_location", return_value=spec))
        self.stack.enter_context(mock.patch.object(M.importlib.util, "module_from_spec", return_value=fake))
        return fake

    def attempt(self):
        M.OLD.m1.save(M.ATTEMPT, {"manifest_sha256": M.OLD.m1.sha(M.MANIFEST)})

    def test_existing_run_markers_prevent_launch_or_decode(self):
        for name in ("RESULT", "OUTCOME", "WORKER_START", "ATTEMPT"):
            path = getattr(M, name)
            M.OLD.m1.save(path, {"synthetic_marker": True})
            with self.subTest(name=name), self.assertRaises((ValueError, FileExistsError)):
                self.main("run")
            path.unlink()
        self.execute.assert_not_called()
        self.decode.assert_not_called()

    def test_parent_deadline_failure_is_retained_and_not_retried(self):
        runner = self.runner(return_value=(124, "synthetic deadline exceeded"))
        with self.assertRaises(SystemExit) as stopped:
            self.main("run")
        self.assertEqual(stopped.exception.code, 124)
        self.assertTrue(M.ATTEMPT.exists())
        outcome = M.OLD.read_json(M.OUTCOME)
        self.assertEqual(outcome["status"], "STOP_WORKER")
        self.assertEqual(outcome["returncode"], 124)
        self.assertIn("deadline", outcome["output"])
        self.assertFalse(outcome["unknown_search_authorized"])
        with self.assertRaisesRegex(ValueError, "EXISTING_RUN"):
            self.main("run")
        runner.bounded_run.assert_called_once()
        self.execute.assert_not_called()

    def test_parent_launch_exception_is_retained(self):
        self.runner(side_effect=OSError("synthetic launch failure"))
        with self.assertLogs(M.LOGGER, level="ERROR"), self.assertRaises(SystemExit) as stopped:
            self.main("run")
        self.assertEqual(stopped.exception.code, 1)
        outcome = M.OLD.read_json(M.OUTCOME)
        self.assertEqual(outcome["status"], "STOP_WORKER")
        self.assertIn("synthetic launch failure", outcome["output"])
        self.decode.assert_not_called()

    def test_worker_marker_written_before_resource_check_and_prevents_retry(self):
        self.attempt()
        with mock.patch.object(M, "peak_memory", side_effect=RuntimeError("synthetic memory failure")), \
                self.assertRaisesRegex(RuntimeError, "memory"):
            self.main("run", "--worker")
        self.assertTrue(M.WORKER_START.exists())
        self.execute.assert_not_called()
        with self.assertRaises(FileExistsError):
            self.main("run", "--worker")
        self.execute.assert_not_called()

    def test_worker_rejects_changed_manifest_before_execute(self):
        M.OLD.m1.save(M.ATTEMPT, {"manifest_sha256": "incorrect"})
        with self.assertRaisesRegex(ValueError, "WORKER_ATTEMPT"):
            self.main("run", "--worker")
        self.assertFalse(M.WORKER_START.exists())
        self.execute.assert_not_called()

    def test_dependency_failure_and_mismatch_precede_any_payload_decode(self):
        for configuration in ({"side_effect": ValueError("STOP_OLD_PROVENANCE")},
                              {"return_value": {"synthetic": "changed"}}):
            with mock.patch.object(M, "dependencies", **configuration), self.assertRaises(ValueError):
                self.real_execute()
        self.decode.assert_not_called()

    def test_decoder_failure_yields_stop_not_empty_comparison(self):
        self.decode.side_effect = ValueError("synthetic invalid metadata")
        synthetic = SimpleNamespace(read_bytes=mock.Mock(return_value=b"synthetic"))
        with mock.patch.object(M, "dependencies", return_value={"synthetic": "digest"}), \
                mock.patch.object(M, "ARI", synthetic), mock.patch.object(M.OLD, "compare_tables") as compare:
            result = self.real_execute()
        self.assertEqual(result["status"], "STOP_M1D")
        self.assertEqual(result["error_type"], "ValueError")
        self.assertFalse(result["unknown_search_authorized"])
        compare.assert_not_called()

    def test_worker_output_bound_stops_without_scientific_result(self):
        self.attempt()
        self.execute.return_value = {"status": "x" * 1_000_001}
        with self.assertRaisesRegex(ValueError, "RESOURCE_CAP"):
            self.main("run", "--worker")
        self.assertFalse(M.RESULT.exists())
        self.assertTrue(M.WORKER_START.exists())

    def test_replay_exact_and_different_leave_all_receipts_unchanged(self):
        M.OLD.m1.save(M.RESULT, {"status": "SYNTHETIC"})
        before = {p.name: p.read_bytes() for p in M.ROOT.iterdir()}
        self.main("replay", "--worker")
        self.execute.return_value = {"status": "CHANGED"}
        with self.assertRaisesRegex(ValueError, "REPLAY_DIFFERENT"):
            self.main("replay", "--worker")
        self.assertEqual(before, {p.name: p.read_bytes() for p in M.ROOT.iterdir()})


if __name__ == "__main__":
    unittest.main()
