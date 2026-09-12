"""Offline bounded-transport checks, not archive or scientific validation."""

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location("xmm_listing", Path(__file__).with_name("listing.py"))
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class Raw(io.BytesIO):
    def read(self, amount=-1, decode_content=False):
        return super().read(amount)


class ListingTests(unittest.TestCase):
    def collect(self, body=b"<html>index</html>", status=200, headers=None):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        response = MagicMock(status_code=status, url=P.URL)
        response.headers = {"Content-Type": "text/html", "Set-Cookie": "do-not-retain", **(headers or {})}
        response.raw = Raw(body)
        response.__enter__.return_value = response
        self.root = root
        self.enterContext(patch.object(P, "HERE", root))
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value = response
        self.enterContext(patch("requests.Session", return_value=session))
        self.session = session
        self.request = session.get
        return P.collect

    def test_exact_request_safe_headers_and_body(self):
        self.collect()()
        self.request.assert_called_once_with(P.URL, timeout=(5, 15), stream=True,
            allow_redirects=False, headers={"Accept-Encoding": "identity"})
        self.assertNotIn("do-not-retain", (self.root / "http.json").read_text())
        self.assertEqual((self.root / "index.html").read_bytes(), b"<html>index</html>")
        self.assertIs(self.session.trust_env, False)
        self.assertIsNone(self.session.auth)
        self.session.cookies.clear.assert_called_once()

    def test_exact_cap_and_single_overflow_byte(self):
        call = self.collect(b"x" * (P.CAP + 100))
        with self.assertRaisesRegex(ValueError, "STOP_BYTE_CAP"):
            call()
        self.assertEqual((self.root / "index.html").stat().st_size, P.CAP)
        self.assertEqual(self.request.return_value.raw.tell(), P.CAP + 1)

    def test_error_body_retained_and_redirect_not_followed(self):
        call = self.collect(b"error", status=302)
        with self.assertRaisesRegex(ValueError, "STOP_HTTP_302"):
            call()
        self.assertEqual((self.root / "index.html").read_bytes(), b"error")
        self.request.assert_called_once()

    def test_declared_length_disagreement_fails(self):
        call = self.collect(headers={"Content-Length": "1000"})
        with self.assertRaisesRegex(ValueError, "STOP_RESPONSE_LENGTH"):
            call()

    def test_second_body_write_refused(self):
        call = self.collect()
        call()
        before = (self.root / "index.html").read_bytes()
        with self.assertRaises(FileExistsError):
            P.save("http.json", {})
        self.assertEqual((self.root / "index.html").read_bytes(), before)

    def test_helper_mismatch_prevents_marker(self):
        with tempfile.TemporaryDirectory() as root, patch.object(P, "HERE", Path(root)), \
                patch.object(P, "sha", return_value="wrong"), self.assertRaisesRegex(ValueError, "STOP_HELPER_HASH"):
            P.run()
        self.assertFalse((Path(root) / "run-start.json").exists())


if __name__ == "__main__":
    unittest.main()
