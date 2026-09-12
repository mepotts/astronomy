"""Cap guards and tree-aware transport checks before parent-plane download."""

import ctypes
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SPEC = importlib.util.spec_from_file_location("full_plane", Path(__file__).parents[1]/"full_plane.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class TestFullPlane(unittest.TestCase):
    def test_dependency_hashes(self):
        M.validate_dependencies()

    def test_positive_known_plan(self):
        self.assertEqual(M.preflight(50_235_583, [55_431_360, 55_431_360, 55_480_320,
                                                55_483_200, 55_483_200, 55_483_200]), 383_028_223)

    def test_cap_before_download(self):
        with self.assertRaisesRegex(ValueError, "cap"):
            M.preflight(50_235_583, [450_000_000])

    def test_missing_sizes(self):
        for sizes in ([], [0], [-1], [None], [True]):
            with self.assertRaises(ValueError):
                M.preflight(0, sizes)

    def test_timeout_cannot_be_success(self):
        with mock.patch.object(M.H, "bounded_run", return_value=(124, "hard timeout")), \
                self.assertRaisesRegex(RuntimeError, "124"):
            M.bounded_get("https://example.test/control", M.DATA/"does-not-exist.fits", 100)

    def test_absolute_worker_and_exact_deadline(self):
        receipt = {"bytes": 100, "status": 200}
        with mock.patch.object(M.H, "bounded_run", return_value=(0, json.dumps(receipt))) as worker:
            M.bounded_get("https://example.test/control", M.DATA/"does-not-exist.fits", 100)
            command, timeout = worker.call_args.args
            self.assertEqual(timeout, 75)
            self.assertTrue(Path(command[0]).is_absolute())
            self.assertTrue(Path(command[1]).is_absolute())
            self.assertTrue(Path(command[4]).is_absolute())

    def test_exact_windows_tree_on_timeout(self):
        process = mock.Mock(pid=12345)
        process.communicate.side_effect = [subprocess.TimeoutExpired("probe", 1), ("", "")]
        process.poll.return_value = 1
        with mock.patch.object(M.H.subprocess, "Popen", return_value=process), \
                mock.patch.object(M.H.os, "name", "nt"), \
                mock.patch.object(M.H.subprocess, "run") as terminate:
            self.assertEqual(M.H.bounded_run(["probe"], 1)[0], 124)
            self.assertEqual(terminate.call_args.args[0], ["taskkill", "/PID", "12345", "/T", "/F"])

    def test_full_result_source_and_protocol_receipts(self):
        report = json.loads((M.ROOT/"full-plane-measurement.json").read_text())
        self.assertEqual(report["driver_sha256"], M.P.sha(M.ROOT/"full_plane.py"))
        self.assertEqual(report["protocol_sha256"], M.P.sha(M.ROOT/"FULL-PLANE-PROTOCOL.md"))
        self.assertEqual(report["acquisition_sha256"], M.P.sha(M.ROOT/"full-plane-acquisition.json"))

    def test_full_plane_target_matches_retained_cutout(self):
        full = json.loads((M.ROOT/"full-plane-measurement.json").read_text())
        small = json.loads((M.ROOT/"measurement-followup.json").read_text())
        for old, new in zip(small["epochs"], full["epochs"]):
            self.assertEqual(old["campaign"], new["campaign"])
            for key in ("amplitude_jy", "noise_proxy_jy", "peak_offset_arcsec"):
                self.assertTrue(math.isclose(old["target"][key], new["target"][key],
                                             rel_tol=1e-9, abs_tol=1e-12))

    @unittest.skipUnless(os.name == "nt", "Real Windows venv process-tree regression")
    def test_real_windows_descendant_is_reaped(self):
        (M.ROOT/"data").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=M.ROOT/"data") as folder:
            marker = Path(folder)/"owned-child-pid.txt"
            child_code = ("import os,time; from pathlib import Path; "
                          f"Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(30)")
            worker_code = ("import subprocess,sys,time; "
                           f"subprocess.Popen([sys._base_executable,'-c',{child_code!r}]); "
                           "time.sleep(30)")
            code, _ = M.H.bounded_run([sys.executable, "-c", worker_code], 2)
            self.assertEqual(code, 124)
            self.assertTrue(marker.exists(), "Owned descendant did not start")
            child_pid = int(marker.read_text())
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(0x1000, False, child_pid)
            if handle:
                status = ctypes.c_uint32()
                ok = kernel.GetExitCodeProcess(handle, ctypes.byref(status))
                kernel.CloseHandle(handle)
                self.assertTrue(ok)
                if status.value == 259:
                    # Only this test's recorded owned descendant; no broad process kill.
                    subprocess.run(["taskkill", "/PID", str(child_pid), "/T", "/F"],
                                   capture_output=True, timeout=10, check=False)
                    self.fail("Owned descendant survived bounded_run timeout")
            else:
                self.assertEqual(ctypes.get_last_error(), 87, "Inaccessible process is not proof of exit")


if __name__ == "__main__":
    unittest.main()
