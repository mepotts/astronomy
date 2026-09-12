"""Independent offline acquisition/replay regressions; only synthetic PRF arrays."""

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

BASE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reviewed_m2a", BASE / "scripts/m2a.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
FSPEC = importlib.util.spec_from_file_location("m2a_fixture_only", BASE / "tests/test_m2a.py")
F = importlib.util.module_from_spec(FSPEC)
FSPEC.loader.exec_module(F)


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for key, value in (("ROOT", self.root), ("DATA", self.root / "data"),
                           ("MANIFEST", self.root / "manifest.json"), ("SUMMARY", self.root / "summary.json")):
            item = patch.object(A, key, value)
            item.start()
            self.addCleanup(item.stop)
        for target, name in ((A, "verify"), (A.LOGGER, "exception")):
            item = patch.object(target, name)
            item.start()
            self.addCleanup(item.stop)
        A.M.save(A.MANIFEST, {"synthetic": True})
        self.name = A.products()[0]["filename"]
        self.folder = A.folder_for(self.name)

    def reserve(self):
        A.M.save(A.DATA / "run-start.json", {"approved_manifest_sha256": A.M.sha(A.MANIFEST)})
        A.M.save(self.folder / "attempt.json", A.attempt(self.name))

    def session(self, chunks=None, headers=None):
        response = MagicMock()
        response.status_code = 200
        response.headers = headers or {}
        if chunks is None:
            buffer = BytesIO()
            F.fixture(A.products()[0]).writeto(buffer)
            chunks = [buffer.getvalue()]
        response.iter_content.return_value = chunks
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value.__enter__.return_value = response
        return session

    def run_fake(self, action=None, import_error=None):
        runner, loader = MagicMock(), MagicMock()
        loader.exec_module.side_effect = import_error
        runner.bounded_run.side_effect = action
        runner.bounded_run.return_value = (124, "synthetic deadline")
        with (patch.object(A.importlib.util, "spec_from_file_location", return_value=SimpleNamespace(loader=loader)),
              patch.object(A.importlib.util, "module_from_spec", return_value=runner), redirect_stdout(StringIO())):
            A.run(A.M.sha(A.MANIFEST))
        return runner

    def first_success_then_stop(self):
        count = 0

        def action(command, timeout):
            nonlocal count
            count += 1
            if count == 1:
                with patch("requests.Session", return_value=self.session()):
                    A.worker(command[-1])
                return 0, ""
            return 124, "synthetic deadline"

        return self.run_fake(action)

    def rewrite(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def sync_artifacts(self):
        summary = A.read(A.SUMMARY)
        row = summary["outcomes"][0]
        row["artifacts"] = A.artifacts(self.name)
        self.rewrite(A.DATA / (self.name + ".outcome.json"), row)
        self.rewrite(A.SUMMARY, summary)

    def replay(self):
        with patch("requests.Session") as network, redirect_stdout(StringIO()):
            A.replay()
        network.assert_not_called()

    def test_all_twelve_exact_urls_independently_enumerated(self):
        names = [
            "tess2019107181902-prf-3-3-row1025-col1580.fits",
            "tess2019107181902-prf-3-3-row1025-col2092.fits",
            "tess2019107181902-prf-3-3-row1536-col1580.fits",
            "tess2019107181902-prf-3-3-row1536-col2092.fits",
            "tess2019107181902-prf-4-3-row1536-col0557.fits",
            "tess2019107181902-prf-4-3-row1536-col1069.fits",
            "tess2019107181902-prf-4-3-row2048-col0557.fits",
            "tess2019107181902-prf-4-3-row2048-col1069.fits",
            "tess2019107181901-prf-2-3-row1536-col1580.fits",
            "tess2019107181901-prf-2-3-row1536-col2092.fits",
            "tess2019107181901-prf-2-3-row2048-col1580.fits",
            "tess2019107181901-prf-2-3-row2048-col2092.fits",
        ]
        prefix = "https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/"
        expected = [prefix + f"cam{camera}_ccd3/" + name
                    for camera, name in zip([3] * 4 + [4] * 4 + [2] * 4, names, strict=True)]
        self.assertEqual([p["url"] for p in A.products()], expected)

    def test_announced_oversize_writes_no_body(self):
        self.reserve()
        with (patch("requests.Session", return_value=self.session(headers={"Content-Length": "300001"})),
              self.assertRaisesRegex(ValueError, "STOP_SIZE")):
            A.worker(self.name)
        self.assertFalse((self.folder / self.name).exists())
        self.assertEqual(A.read(self.folder / "failure.json")["partial_bytes"], 0)

    def test_midstream_connection_failure_preserves_exact_partial(self):
        self.reserve()

        def chunks():
            yield b"partial-prefix"
            raise requests.ConnectionError("synthetic interrupted stream")

        with (patch("requests.Session", return_value=self.session(chunks())),
              self.assertRaises(requests.ConnectionError)):
            A.worker(self.name)
        self.assertEqual((self.folder / self.name).read_bytes(), b"partial-prefix")
        self.assertEqual(A.read(self.folder / "failure.json")["partial_bytes"], 14)

    def test_parent_import_failure_accounts_all_unlaunched(self):
        runner = self.run_fake(import_error=ImportError("synthetic"))
        runner.bounded_run.assert_not_called()
        rows = A.read(A.SUMMARY)["outcomes"]
        self.assertEqual([r["status"] for r in rows], ["STOP_NOT_LAUNCHED"] * 12)
        self.replay()

    def test_reservation_failure_never_launches_and_accounts_all(self):
        (self.folder).mkdir(parents=True)
        A.M.save(self.folder / "attempt.json", {"existing": "preserve"})
        runner = self.run_fake()
        runner.bounded_run.assert_not_called()
        self.assertEqual(A.read(self.folder / "attempt.json"), {"existing": "preserve"})
        self.assertEqual(len(A.read(A.SUMMARY)["outcomes"]), 12)
        self.replay()

    def test_partial_success_failure_then_exact_readonly_replay(self):
        runner = self.first_success_then_stop()
        self.assertEqual(runner.bounded_run.call_count, 2)
        rows = A.read(A.SUMMARY)["outcomes"]
        self.assertEqual([r["status"] for r in rows],
                         ["PRF_PRODUCT_STRUCTURALLY_VALID", "STOP_PRF_PRODUCT"] + ["STOP_NOT_LAUNCHED"] * 10)
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.replay()
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_replay_rejects_promoted_science_flags(self):
        self.run_fake()
        summary = A.read(A.SUMMARY)
        summary["unknown_search_authorized"] = True
        summary["localization_validated"] = True
        self.rewrite(A.SUMMARY, summary)
        with self.assertRaises(ValueError):
            self.replay()

    def test_replay_rejects_success_summary_over_stopped_outcomes(self):
        self.run_fake()
        summary = A.read(A.SUMMARY)
        summary["status"] = "PRF_PRODUCTS_STRUCTURALLY_VALID"
        self.rewrite(A.SUMMARY, summary)
        with self.assertRaises(ValueError):
            self.replay()

    def test_replay_checks_worker_start_semantics_not_only_hash(self):
        self.first_success_then_stop()
        receipt = A.read(self.folder / "worker-start.json")
        receipt["manifest_sha256"] = "not-the-manifest"
        self.rewrite(self.folder / "worker-start.json", receipt)
        self.sync_artifacts()
        with self.assertRaises(ValueError):
            self.replay()

    def test_replay_checks_response_receipt_semantics_not_only_hash(self):
        self.first_success_then_stop()
        receipt = A.read(self.folder / "response-receipt.json")
        receipt["sha256"] = "not-the-file"
        receipt["bytes"] = 1
        self.rewrite(self.folder / "response-receipt.json", receipt)
        self.sync_artifacts()
        with self.assertRaises(ValueError):
            self.replay()

    def test_replay_rejects_missing_success_receipt(self):
        self.first_success_then_stop()
        (self.folder / "response-receipt.json").unlink()
        self.sync_artifacts()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.replay()

    def test_success_exit_without_validation_stops_before_next_launch(self):
        runner = self.run_fake(lambda *_args: (0, "synthetic missing worker output"))
        self.assertEqual(runner.bounded_run.call_count, 1)
        self.assertEqual(A.read(A.SUMMARY)["status"], "STOP_PRF_PRODUCT")

    def test_replay_rejects_second_launch_after_prior_failure(self):
        self.run_fake()
        summary = A.read(A.SUMMARY)
        row = summary["outcomes"][1]
        name = row["filename"]
        A.M.save(A.folder_for(name) / "attempt.json", A.attempt(name))
        row["status"] = "STOP_PRF_PRODUCT"
        row["artifacts"] = A.artifacts(name)
        self.rewrite(A.DATA / (name + ".outcome.json"), row)
        self.rewrite(A.SUMMARY, summary)
        with self.assertRaises(ValueError):
            self.replay()

    def test_replay_detects_changed_partial_bytes(self):
        def action(command, _timeout):
            path = A.folder_for(command[-1]) / command[-1]
            path.write_bytes(b"original synthetic partial")
            return 124, "synthetic deadline"

        self.run_fake(action)
        (self.folder / self.name).write_bytes(b"changed synthetic partial")
        with self.assertRaisesRegex(ValueError, "OUTCOME_REPLAY"):
            self.replay()

    def test_failed_structure_preserves_response_and_raw_bytes(self):
        self.reserve()
        with (patch("requests.Session", return_value=self.session([b"not FITS"])),
              self.assertRaisesRegex(ValueError, "FITS_SIZE")):
            A.worker(self.name)
        self.assertEqual((self.folder / self.name).read_bytes(), b"not FITS")
        receipt = A.read(self.folder / "response-receipt.json")
        self.assertEqual(receipt["sha256"], A.M.sha(self.folder / self.name))
        self.assertTrue((self.folder / "failure.json").exists())
        self.assertFalse((self.folder / "validation.json").exists())


if __name__ == "__main__":
    unittest.main()
