import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import real_controls as rc


class RealControlTests(unittest.TestCase):
    def test_fixed_public_targets_and_events(self):
        self.assertEqual(len(rc.TARGETS), 3)
        self.assertEqual(rc.TARGETS[1]["starts"], [1930, 1935])
        self.assertAlmostEqual(rc.TARGETS[0]["ra_deg"], 15*(8+30/60+38.5/3600))

    def test_catalogue_diagnostic_does_not_admit_flagged_or_faint_control(self):
        source = {"stdmag": "12", "color": "1.2", "num_matches": "1000", "v_flag": "0", "mag_flag": "0"}
        self.assertEqual(rc.catalogue_rejections(source), [])
        source.update(stdmag="14", v_flag="1")
        self.assertEqual(rc.catalogue_rejections(source), ["stdmag", "v_flag"])
        source.update(color="nan")
        self.assertIn("color", rc.catalogue_rejections(source))

    def test_duplicate_measurements_fail(self):
        row = {"series": "a", "plate_number": "1", "mosaic_number": "0", "solution_number": "0"}
        with patch.object(rc, "clean", return_value=[row, row]), \
                self.assertRaisesRegex(ValueError, "duplicate clean"):
            rc.unique_imaging_keys([row, row])

    def test_missing_replay_never_networks(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(rc.urllib.request, "urlopen") as network:
            archive = rc.Archive(Path(tmp), replay=True)
            with self.assertRaisesRegex(ValueError, "network forbidden"):
                archive.fetch("0-catalogue", "querycat", {})
            network.assert_not_called()

    def test_failed_attempt_is_not_automatically_retried(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(rc.time, "sleep"), \
                patch.object(rc.urllib.request, "urlopen", side_effect=OSError("offline")) as network:
            archive = rc.Archive(Path(tmp))
            with self.assertRaises(OSError):
                archive.fetch("0-catalogue", "querycat", {})
            archive = rc.Archive(Path(tmp))
            self.assertEqual(archive.manifest["attempts"][0]["state"], "FAILED")
            with self.assertRaisesRegex(ValueError, "no automatic retry"):
                archive.fetch("0-catalogue", "querycat", {})
            self.assertEqual(network.call_count, 1)

    def test_protocol_mutation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = rc.Archive(Path(tmp))
            archive.manifest["contract"] = {}
            archive.save()
            with self.assertRaisesRegex(ValueError, "code changed"):
                rc.Archive(Path(tmp), replay=True)

    def test_cache_checks_request_hash_and_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = rc.Archive(Path(tmp))
            raw = b'["a,b","1,2"]'
            archive.manifest["artifacts"]["r"] = {"url": rc.API+"querycat", "body": {},
                                                   "sha256": rc.sha(raw), "bytes": len(raw)}
            with zipfile.ZipFile(Path(tmp)/"responses.zip", "w") as z:
                z.writestr("r.raw", raw)
            archive.save()
            self.assertEqual(archive.fetch("r", "querycat", {}), raw)
            with self.assertRaisesRegex(ValueError, "cached request"):
                archive.fetch("r", "querycat", {"changed": True})
            archive.manifest["artifacts"]["r"]["bytes"] += 1
            with self.assertRaisesRegex(ValueError, "cached request"):
                archive.fetch("r", "querycat", {})

    def test_gate_requires_two_full_selection_recoveries(self):
        missing_catalogue = json.dumps(["ra_deg,dec_deg", "0,0"]).encode()
        result = rc.execute(lambda *args: missing_catalogue)
        self.assertEqual(result["selected_controls"], 3)
        self.assertEqual(result["recovered_by_full_selection"], 0)
        self.assertEqual(result["gate"], "STOP_REAL_EVENT_TRANSFER")

    def test_recovery_requires_correct_epoch_sign_coverage_and_catalogue(self):
        source = {"stdmag": "12", "color": "1.2", "num_matches": "1000", "v_flag": "0", "mag_flag": "0"}
        data = [{"year": 1900+i, "mag": 12.} for i in range(100)]
        cases = [(1930, True, False, {}, "0", True, True),
                 (1960, True, False, {}, "0", False, False),
                 (1930, False, True, {}, "0", False, False),
                 (1930, True, False, {}, "1", True, False),
                 (1930, True, False, {"exposure_conflict": 3}, "0", False, False)]
        for epoch, positive, negative, excluded, flag, diagnostic, full in cases:
            with self.subTest(epoch=epoch, flag=flag, excluded=excluded), \
                    patch.object(rc, "summarize", return_value={}), \
                    patch.object(rc, "unique_imaging_keys"), \
                    patch.object(rc, "joined", return_value=(data, {"clean": 100, "excluded": excluded})), \
                    patch.object(rc, "window", side_effect=lambda rows, start, positive=positive, negative=negative, epoch=epoch: {
                        "start": start, "eligible": True, "positive_flag": positive and start == epoch,
                        "negative_flag": negative and start == epoch}):
                result = rc.evaluate(rc.TARGETS[1], {**source, "v_flag": flag}, [], [])
                self.assertEqual(result["recovered_event_diagnostic"], diagnostic)
                self.assertEqual(result["recovered_by_full_selection"], full)
                self.assertEqual(data[50]["mag"], 12.)  # Injections never mutate real inputs.


if __name__ == "__main__":
    unittest.main()
