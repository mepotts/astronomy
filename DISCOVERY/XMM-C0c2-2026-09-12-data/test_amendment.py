"""Focused offline checks of the cap-only, frozen-core wrapper; no HTTP."""

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location("xmm_cap_amendment", Path(__file__).with_name("listing.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Raw(io.BytesIO):
    def read(self, amount=-1, decode_content=False):
        return super().read(amount)


class AmendmentTests(unittest.TestCase):
    def test_rebinds_only_scope_paths_and_cap(self):
        core = M.load_core()
        self.assertEqual(core.CAP, 1048576)
        self.assertEqual(core.URL, "https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/")
        self.assertEqual(core.HELPER_HASH, "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd")
        self.assertEqual(core.sha(core.HELPER), core.HELPER_HASH)
        for field in ("HERE", "SOURCE", "PROTOCOL"):
            self.assertEqual(getattr(core, field), getattr(M, field))
        self.assertNotEqual(core.HERE, M.CORE.parent)
        self.assertEqual(core.collect.__code__.co_filename, str(M.CORE))
        self.assertEqual(core.run.__code__.co_filename, str(M.CORE))

    def test_parent_rejects_changed_core_before_entry(self):
        with patch.object(M, "CORE_HASH", "wrong"), patch("requests.Session") as session:
            with self.assertRaisesRegex(ValueError, "STOP_FROZEN_CORE_HASH"):
                M.dispatch("run")
            session.assert_not_called()

    def test_verified_buffer_never_uses_loader_source_or_bytecode_reads(self):
        with patch.object(M.importlib.machinery.SourceFileLoader, "get_data",
                          side_effect=AssertionError("Unverified loader read")) as read:
            core = M.load_core()
            self.assertEqual(core.CAP, M.CAP)
            self.assertEqual(core.collect.__code__.co_filename, str(M.CORE))
            read.assert_not_called()

    def test_child_rejects_changed_core_before_entry(self):
        with patch.object(M, "CORE_HASH", "wrong"), patch("requests.Session") as session:
            with self.assertRaisesRegex(ValueError, "STOP_FROZEN_CORE_HASH"):
                M.dispatch("_worker")
            session.assert_not_called()

    def test_both_entries_use_verified_core(self):
        for stage, method in (("run", "run"), ("_worker", "worker")):
            with self.subTest(stage=stage), patch.object(M, "load_core") as loader:
                getattr(loader.return_value, method).return_value = 7
                self.assertEqual(M.dispatch(stage), 7)
                loader.assert_called_once_with()
                getattr(loader.return_value, method).assert_called_once_with()

    def collect(self, body):
        core = M.load_core()
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        core.HERE = root
        response = MagicMock(status_code=200, url=core.URL)
        response.headers = {"Content-Type": "text/html", "Set-Cookie": "synthetic-secret"}
        response.raw = Raw(body)
        response.__enter__.return_value = response
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value = response
        self.enterContext(patch("requests.Session", return_value=session))
        return core, root, response, session

    def test_exact_new_cap_allowed_anonymous_settings_unchanged(self):
        core, root, response, session = self.collect(b"x" * M.CAP)
        core.collect()
        self.assertEqual((root / "index.html").stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP)
        session.get.assert_called_once_with(core.URL, timeout=(5, 15), stream=True,
            allow_redirects=False, headers={"Accept-Encoding": "identity"})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once_with()
        self.assertNotIn("synthetic-secret", (root / "http.json").read_text())

    def test_new_cap_plus_one_stops_and_preserves_exact_partial(self):
        core, root, response, session = self.collect(b"x" * (M.CAP + 100))
        with self.assertRaisesRegex(ValueError, "STOP_BYTE_CAP"):
            core.collect()
        self.assertEqual((root / "index.html").stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP + 1)
        session.get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
