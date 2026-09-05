"""No network, FITS, optional scientific dependencies, or E products."""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_e_release.py"
SPEC = importlib.util.spec_from_file_location("check_e_release", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ReleaseGateTests(unittest.TestCase):
    def classify(self, metadata, **kwargs):
        options = {"map_ok": True, "control_ok": True, "today": "2026-09-09"}
        options.update(kwargs)
        return M.classify(metadata, **options)

    def metadata(self, public=39):
        return {"count": 39, "rights": {"PUBLIC": public, "EXCLUSIVE_ACCESS": 39-public},
                "release_dates": [M.RELEASE]}

    def test_unavailable_is_not_ready(self):
        self.assertEqual(self.classify(None), "UNAVAILABLE")

    def test_empty_missing_malformed_are_not_ready(self):
        for record in ({}, [], {"count": 0}, self.metadata() | {"count": True}):
            self.assertEqual(self.classify(record), "STOP_METADATA")

    def test_wrong_release_is_not_ready(self):
        record = self.metadata() | {"release_dates": ["2026-09-10"]}
        self.assertEqual(self.classify(record), "STOP_METADATA")

    def test_rights_conservation(self):
        for rights in ({"PUBLIC": 38}, {"UNKNOWN": 39}, {"PUBLIC": "39"}):
            self.assertEqual(self.classify(self.metadata() | {"rights": rights}),
                             "STOP_METADATA")

    def test_early_public_waits(self):
        self.assertEqual(self.classify(self.metadata(), today="2026-09-05"), "WAIT_RELEASE")

    def test_partial_public_waits(self):
        self.assertEqual(self.classify(self.metadata(38)), "WAIT_PUBLIC_PRODUCTS")

    def test_full_ready(self):
        self.assertEqual(self.classify(self.metadata()), "READY_FOR_FROZEN_ANALYSIS")

    def test_failed_procedure_stops(self):
        for option in ("map_ok", "control_ok"):
            self.assertEqual(self.classify(self.metadata(), **{option: False}), "STOP_PROCEDURE")

    def test_acceptance_requires_success_exit(self):
        output = "\n".join(["PASS control"] * 7)
        self.assertTrue(M.acceptance(0, output)["passed"])
        self.assertFalse(M.acceptance(1, output)["passed"])
        self.assertFalse(M.acceptance(0, output + "\nFAIL another")["passed"])
        self.assertFalse(M.acceptance(0, "PASS")["passed"])

    def test_windows_timeout_reaps_own_tree(self):
        child = mock.Mock(pid=12345)
        child.communicate.side_effect = [M.subprocess.TimeoutExpired("probe", 1), ("", "")]
        child.poll.return_value = 1
        with mock.patch.object(M.subprocess, "Popen", return_value=child), \
                mock.patch.object(M.os, "name", "nt"), \
                mock.patch.object(M.subprocess, "run") as terminate:
            self.assertEqual(M.bounded_run(["probe"], 1)[0], 124)
            self.assertEqual(terminate.call_args.args[0],
                             ["taskkill", "/PID", "12345", "/T", "/F"])

    def test_posix_timeout_reaps_own_group(self):
        child = mock.Mock(pid=12345)
        child.communicate.side_effect = [M.subprocess.TimeoutExpired("probe", 1), ("", "")]
        child.poll.return_value = 1
        with mock.patch.object(M.subprocess, "Popen", return_value=child), \
                mock.patch.object(M.os, "name", "posix"), \
                mock.patch.object(M.os, "killpg", create=True) as terminate, \
                mock.patch.object(M.signal, "SIGKILL", 9, create=True):
            self.assertEqual(M.bounded_run(["probe"], 1)[0], 124)
            terminate.assert_called_once_with(12345, M.signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
