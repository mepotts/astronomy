"""Compact review documents must not depend on omitted project history."""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "publication_builder", ROOT / "pta-mpta/scripts/build_publication_packages.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class PublicationScopeTests(unittest.TestCase):
    def test_main_note_omits_companion_and_repository_only_links(self):
        source = (ROOT / "erosita-dr2/draft-rnaas-vanished-census.md").read_text(encoding="utf-8")
        result = M.census_manuscript(source)
        self.assertNotIn("## Companion note B", result)
        self.assertNotIn("](M5-writeup.md)", result)
        self.assertNotIn("](writeup-audit.md)", result)
        self.assertIn("](PACKAGE-MANIFEST.json)", result)
        self.assertIn("107 (+17/−8)", result)
        self.assertIn("not a total uncertainty interval", result)
        self.assertIn("SOURCE-MAPPING-2026-09-05.md", result)

    def test_unexpected_manuscript_structure_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "separator"):
            M.census_manuscript("A completely different document")

    def test_missing_review_attachment_is_rejected(self):
        payload = {"review.md": b"See [audit](missing-audit.md)."}
        self.assertEqual(M.missing_local_links(payload, ["review.md"]),
                         [("review.md", "missing-audit.md")])

    def test_relative_mapping_links_resolve_inside_package(self):
        payload = {
            "review.md": b"[manifest](PACKAGE-MANIFEST.json)",
            "publication/map.md": b"[review](../review.md#scope) [source](https://example.com)",
        }
        self.assertEqual(M.missing_local_links(payload, list(payload)), [])

    def test_scoped_mapping_contains_original_gaia_columns(self):
        mapping = (ROOT / "erosita-dr2/publication/SOURCE-MAPPING-2026-09-05.md").read_text()
        for field in ("I/358/vclassre", "gclass_id", "gclass_class", "gclass_score", "ClassSc"):
            self.assertIn(field, mapping)
        self.assertIn("10-arcsec", mapping)
        self.assertIn("not DSC", mapping)


if __name__ == "__main__":
    unittest.main()
