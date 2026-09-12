"""Synthetic M1e preflight: never read astronomical catalogs or use network."""

import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1e_test", ROOT / "scripts/m1e.py")
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)
FIXTURE_SPEC = importlib.util.spec_from_file_location("m1e_synthetic", ROOT / "tests/test_m1d.py")
F = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(F)
DESCRIPTOR_SPEC = importlib.util.spec_from_file_location("m1e_descriptor", ROOT / "tests/test_m1d2.py")
DF = importlib.util.module_from_spec(DESCRIPTOR_SPEC)
DESCRIPTOR_SPEC.loader.exec_module(DF)


def fixture(rows=(F.ROW,)):
    return F.fixture(rows).replace(b'ID="SOURCE_ID"', b'ID="source_id"').replace(
        b'</VOTABLE>', DF.DESCRIPTOR + b'</VOTABLE>')


def parity_result():
    return {"status": "OFFLINE_CATALOG_PARITY_PASS", "rows": 1290, "network_requests": 0,
            "pixel_recalculation": False, "unknown_search_authorized": False,
            "numeric_decoders": "unchanged_m1d_struct_and_numpy",
            "parity": {"status": "PARITY_PASS", "rows": 1290, "source_ids_exact": True,
                       "masks_exact": True, "units_validated": True,
                       "columns": {name: {"absolute_tolerance": tol, "max_abs_difference": 0., "masked": 0}
                                   for name, tol in E.C.TOLERANCES.items()}}}


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name, value in (("ROOT", self.root), ("DATA", self.root / "data/m1e"),
                            ("MANIFEST", self.root / "data/m1e/manifest.json"),
                            ("SUMMARY", self.root / "out/m1e-summary.json")):
            mocker = patch.object(E, name, value)
            mocker.start()
            self.addCleanup(mocker.stop)
        E.M.save(E.MANIFEST, {"synthetic": True})
        for tic in E.TARGETS:
            E.M.save(E.ROOT / f"data/m1/{tic}/catalog-query.json", {"adql": f"exact retained query {tic}"})

    def start(self, tic):
        E.M.save(E.DATA / "run-start.json", {"approved_manifest_sha256": E.M.sha(E.MANIFEST)})
        E.M.save(E.DATA / str(tic) / "attempt.json", E.plan(tic))

    def response(self, *, status=200, content=None, length=None):
        result = MagicMock()
        result.status_code = status
        result.headers = {} if length is None else {"Content-Length": str(length)}
        result.iter_content.return_value = [fixture() if content is None else content]
        result.__enter__.return_value = result
        return result

    def invoke(self, response, tic=53206761):
        session = MagicMock()
        session.__enter__.return_value = session
        session.post.return_value = response
        with (patch("requests.Session", return_value=session), patch.object(E, "verify"),
              patch.object(E, "diagnostic", return_value={"synthetic": True})):
            E.worker(tic)
        return session

    def test_conditional_gate_and_unchanged_tolerances(self):
        E.require_parity(parity_result())
        for key, value in (("status", "STOP_M1D"), ("rows", 1289), ("network_requests", 1),
                           ("unknown_search_authorized", True), ("numeric_decoders", "only_one")):
            result = parity_result()
            result[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "PARITY_REQUIRED"):
                E.require_parity(result)
        for key in ("source_ids_exact", "masks_exact", "units_validated"):
            result = parity_result()
            result["parity"][key] = False
            with self.assertRaises(ValueError):
                E.require_parity(result)
        result = parity_result()
        result["parity"]["columns"]["ra"]["absolute_tolerance"] *= 2
        with self.assertRaisesRegex(ValueError, "TOLERANCES"):
            E.require_parity(result)

    def test_prerequisite_exact_replay_and_worker_gate(self):
        hashes = patch.object(E.M, "sha", side_effect=lambda path: E.D2_SOURCE_HASH
                             if path.name == "m1d2.py" else E.D2_MANIFEST_HASH)
        hashes.start()
        self.addCleanup(hashes.stop)
        result = parity_result()
        values = [result, {"returncode": 0, "status": "WORKER_COMPLETED"},
                  {"peak_working_set_bytes": 100, "elapsed_seconds": 1}]
        with patch.object(E.C, "read_json", side_effect=values), patch.object(E.D2, "execute", return_value=result):
            E.prerequisite()
        with (patch.object(E.C, "read_json", side_effect=values),
              patch.object(E.D2, "execute", return_value={"different": True}),
              self.assertRaisesRegex(ValueError, "EXACT_REPLAY")):
            E.prerequisite()
        values[1] = {"returncode": 1, "status": "STOP_WORKER"}
        with (patch.object(E.C, "read_json", side_effect=values), patch.object(E.D2, "execute") as execute,
              self.assertRaisesRegex(ValueError, "WORKER")):
            E.prerequisite()
        execute.assert_not_called()

    def test_no_first_field_and_exact_request(self):
        with self.assertRaisesRegex(ValueError, "TARGET"):
            E.plan(450781262)
        tic = E.TARGETS[0]
        self.start(tic)
        session = self.invoke(self.response())
        session.post.assert_called_once_with(E.URL, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                            "FORMAT": "votable", "QUERY": f"exact retained query {tic}"},
                                            stream=True, timeout=(45, 45), allow_redirects=False)
        self.assertEqual(session.mount.call_args.args[1].max_retries.total, 0)
        receipt = E.C.read_json(E.DATA / str(tic) / "catalog-receipt.json")
        self.assertEqual(receipt["rows"], 1)
        E.response_path(tic)

    def test_redirect_failure_recorded_no_retry(self):
        tic = E.TARGETS[0]
        self.start(tic)
        with self.assertLogs(E.LOGGER, level="ERROR"), self.assertRaisesRegex(ValueError, "HTTP:302"):
            self.invoke(self.response(status=302))
        folder = E.DATA / str(tic)
        self.assertTrue((folder / "failure.json").exists())
        self.assertFalse((folder / "catalog-receipt.json").exists())

    def test_attempt_is_exclusive_and_worker_cannot_run_directly(self):
        tic = E.TARGETS[0]
        with patch("requests.Session") as session, self.assertRaises(FileNotFoundError):
            E.worker(tic)
        session.assert_not_called()
        self.start(tic)
        self.invoke(self.response())
        with patch("requests.Session") as session, self.assertRaises(FileExistsError):
            E.worker(tic)
        session.assert_not_called()

    def test_size_cap_and_partial_decode_failure_receipts(self):
        tic = E.TARGETS[0]
        self.start(tic)
        with self.assertLogs(E.LOGGER, level="ERROR"), self.assertRaisesRegex(ValueError, "SIZE"):
            self.invoke(self.response(length=5_000_001))
        self.assertFalse((E.DATA / str(tic) / "catalog-receipt.json").exists())
        other = E.TARGETS[1]
        E.M.save(E.DATA / str(other) / "attempt.json", E.plan(other))
        with self.assertLogs(E.LOGGER, level="ERROR"), self.assertRaises(ET.ParseError):
            self.invoke(self.response(content=b"invalid"), other)
        self.assertTrue((E.DATA / str(other) / "response-receipt.json").exists())
        self.assertTrue((E.DATA / str(other) / "failure.json").exists())

    def test_decoder_preserves_precision_masks_and_rejects_schema(self):
        path = self.root / "synthetic.xml"
        row = list(F.ROW)
        row[4] = float("nan")
        path.write_bytes(fixture((row,)))
        table = E.validated(path)
        self.assertEqual(table["source_id"][0], 2**53 + 1)
        self.assertTrue(np.ma.getmaskarray(table["pmra"])[0])
        for content in (fixture((F.ROW, F.ROW)), fixture().replace(b'unit="deg"', b'unit="rad"'),
                        fixture().replace(b'BINARY>', b'BINARY2>'),
                        fixture().replace(b'name="ra"', b'name="dec"')):
            path.write_bytes(content)
            with self.assertRaises(ValueError):
                E.validated(path)

    def test_descriptor_profile_required_without_network_or_main(self):
        path = self.root / "synthetic.xml"
        for content in (F.fixture(), fixture().replace(b'Datalink_GaiaDR3', b'other'),
                        fixture().replace(b'https://gaia.ari.uni-heidelberg.de/datalink/gaiadr3', b'https://invalid/')):
            path.write_bytes(content)
            with (patch("requests.Session") as network, patch.object(E.D2, "main") as main,
                  self.assertRaises(ValueError)):
                E.validated(path)
            network.assert_not_called()
            main.assert_not_called()

    def test_m1d2_hash_gate_before_parity_decode(self):
        with (patch.object(E.M, "sha", return_value="changed"), patch.object(E.D2, "execute") as execute,
              self.assertRaisesRegex(ValueError, "M1D2_FROZEN_HASH")):
            E.prerequisite()
        execute.assert_not_called()

    def test_adapter_is_restored_when_geometry_raises(self):
        old = {"centroid_surrogate": {"x": 5., "y": 6.}, "target_header_radec": [120., -30.],
               "images": {"difference": [[1., 2.], [3., 4.]]}}
        original = E.M.DATA, E.M.Table
        with (patch.object(E, "response_path"), patch.object(E.C, "context", return_value=(old, object(), 2026.)),
              patch.object(E.M, "catalog_comparison", side_effect=ValueError("synthetic geometry")),
              self.assertRaisesRegex(ValueError, "synthetic geometry")):
            E.diagnostic(E.TARGETS[0])
        self.assertEqual((E.M.DATA, E.M.Table), original)

    def test_run_requires_explicit_matching_manifest_hash(self):
        with patch.object(E, "verify"), self.assertRaisesRegex(ValueError, "GO_REQUIRED"):
            E.run(None)
        self.assertFalse((E.DATA / "run-start.json").exists())

    def test_transport_timeout_retains_attempt_and_failure(self):
        import requests
        tic = E.TARGETS[0]
        self.start(tic)
        session = MagicMock()
        session.__enter__.return_value = session
        session.post.side_effect = requests.Timeout("synthetic timeout")
        with (patch("requests.Session", return_value=session), patch.object(E, "verify"),
              self.assertLogs(E.LOGGER, level="ERROR"), self.assertRaises(requests.Timeout)):
            E.worker(tic)
        self.assertEqual(session.post.call_count, 1)
        self.assertTrue((E.DATA / str(tic) / "attempt.json").exists())
        self.assertTrue((E.DATA / str(tic) / "failure.json").exists())

    def test_response_hash_tampering_rejected(self):
        tic = E.TARGETS[0]
        self.start(tic)
        self.invoke(self.response())
        path = E.DATA / str(tic) / "gaia-dr3.xml"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "PROVENANCE"):
            E.response_path(tic)

    def test_artifact_inventory_includes_partial_data(self):
        tic = E.TARGETS[0]
        self.start(tic)
        path = E.DATA / str(tic) / "gaia-dr3.xml"
        path.write_bytes(b"partial")
        hashes = E.artifact_hashes(tic)
        self.assertIn(f"data/m1e/{tic}/gaia-dr3.xml", hashes)
        self.assertEqual(hashes[f"data/m1e/{tic}/gaia-dr3.xml"], E.M.sha(path))
        json.dumps(hashes, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
