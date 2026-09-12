"""Local directory parsing checks; no requests or science data."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import xmm_inventory as module

NAME = "P0884250101PNS003PIEVLI0000.FTZ"


def page(name=NAME, size="42M"):
    return (f'<title>{module.TITLE}</title><h1>{module.TITLE}</h1><pre>\n'
            f'<a href="{name}">{name}</a> 2024-11-26 14:06 {size}\n'
            '</pre></body></html>').encode()


class InventoryTests(unittest.TestCase):
    def test_rounding_and_identity(self):
        entry = module.parse(page())[0]
        self.assertIsNone(entry["exact_bytes"])
        self.assertEqual(entry["pps_fields"]["product"], "PIEVLI")
        self.assertEqual(entry["pps_fields"]["instrument"], "PN")
        self.assertEqual(entry["pps_fields"]["exposure"], "S003")
        self.assertIsNone(module.parse(page(size="123"))[0]["exact_bytes"])
        self.assertEqual(module.parse(page(size="123"))[0]["display_integer"], 123)

    def test_partial_rejected(self):
        with self.assertRaises(ValueError):
            module.parse(page()[:-8])

    def test_bad_links_rejected(self):
        for name in ("../outside", "https://example.org/a", "%2foutside", "a?b", "a..b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.parse(page(name=name))

    def test_unparsed_anchor_rejected(self):
        with self.assertRaises(ValueError):
            module.parse(page().replace(b'href="', b"href='", 1))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            module.parse(page().replace(b'</pre>', page().split(b'<pre>')[1].split(b'</pre>')[0] + b'</pre>'))

    def test_receipt_and_hash_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            body = page()
            digest = hashlib.sha256(body).hexdigest()
            (directory / "index.html").write_bytes(body)
            worker = {"status": "HTTP_INDEX_RETAINED", "body": {"bytes": len(body), "sha256": digest}}
            http = {"status": 200, "url": module.URL}
            outcome = {"status": "HTTP_INDEX_RETAINED", "worker_returncode": 0,
                       "artifacts": {"index.html": digest}}
            for name, value in (("worker-result", worker), ("http", http), ("outcome", outcome)):
                (directory / f"{name}.json").write_text(json.dumps(value))
            for name in ("worker-result.json", "http.json"):
                outcome["artifacts"][name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
            (directory / "outcome.json").write_text(json.dumps(outcome))
            self.assertEqual(module.inventory(directory)["entries_count"], 1)
            original_http = (directory / "http.json").read_bytes()
            http["unused"] = "semantically successful but modified"
            (directory / "http.json").write_text(json.dumps(http))
            with self.assertRaisesRegex(ValueError, "Artifact provenance mismatch"):
                module.inventory(directory)
            (directory / "http.json").write_bytes(original_http)
            outcome["status"] = "STOP"
            (directory / "outcome.json").write_text(json.dumps(outcome))
            with self.assertRaises(ValueError):
                module.inventory(directory)
            outcome["status"] = "HTTP_INDEX_RETAINED"
            (directory / "outcome.json").write_text(json.dumps(outcome))
            (directory / "index.html").write_bytes(body + b" ")
            with self.assertRaises(ValueError):
                module.inventory(directory)


if __name__ == "__main__":
    unittest.main()
