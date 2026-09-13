"""Synthetic metadata only; no retained HTML or archive access."""

import json
import unittest

import xmm_summary_metadata as M

OBS = "0123456701"
IDENTITY = f"<h1>Observation ID: {OBS}</h1>"
META = '<meta charset="UTF-8">'
HEADER = "<tr><th>Inst.</th><th>Exp Id</th><th>Mode</th><th>Total Duration</th><th>Actual Start</th></tr>"
ROW = "<tr><td>EPN</td><td>S003</td><td>PrimeFullWindow</td><td>42</td><td>2020-01-02T03:04:05</td></tr>"


def parse(body, role="OB"):
    return M.parse_summary((META + IDENTITY + body).encode(), role, OBS)


class MetadataTests(unittest.TestCase):
    def test_identity_requires_label_not_stray_number(self):
        for html in (OBS, f"<title>{OBS}</title>", f"<p>contact {OBS}</p>"):
            self.assertEqual(M.parse_summary(html.encode(), "OB", OBS)["identity"]["status"], "MISSING")
        self.assertEqual(parse("")["identity"]["status"], "MATCH")

    def test_labelled_table_identity_and_wrong_identity(self):
        value = M.parse_summary((META + f"<table><tr><td>Observation ID</td><td>{OBS}</td></tr></table>").encode(), "OB", OBS)
        self.assertEqual(value["identity"]["status"], "MATCH")
        self.assertEqual(parse("<p>OBSID: 9999999901</p>")["identity"]["status"], "CONFLICT_OR_INVALID")

    def test_exposure_rows_missing_units_duplicates_all_retained(self):
        result = parse("<table>" + HEADER + ROW + ROW + "<tr><td></td></tr></table>")
        self.assertEqual(len(result["exposure_rows"]), 3)
        self.assertEqual(result["duplicate_exposure_keys"], 1)
        first = result["exposure_rows"][0]["fields"]
        self.assertIsNone(first["duration"]["unit"])
        self.assertEqual(first["duration"]["value"], "42")
        self.assertFalse(result["exposure_rows"][2]["shape_matches_header"])
        self.assertEqual(result["exposure_rows"][2]["fields"]["exposure_id"]["status"], "MISSING")

    def test_explicit_units_preserved(self):
        result = parse("<table>" + HEADER.replace("Total Duration", "Total Duration [s]") + ROW + "</table>")
        self.assertEqual(result["exposure_rows"][0]["fields"]["duration"]["unit"], "s")

    def test_duplicate_columns_preserve_candidates_without_winner(self):
        result = parse("<table><tr><th>Instrument</th><th>Exposure ID</th><th>Mode</th><th>Mode</th></tr>"
                       "<tr><td>EPN</td><td>S001</td><td>PrimeFullWindow</td><td>PrimeSmallWindow</td></tr></table>")
        field = result["exposure_rows"][0]["fields"]["mode"]
        self.assertEqual(field["status"], "AMBIGUOUS")
        self.assertIsNone(field["value"])
        self.assertEqual([x["value"] for x in field["candidates"]], ["PrimeFullWindow", "PrimeSmallWindow"])
        compared = M.compare_summaries([result], OBS)
        self.assertIn("mode", compared["exposure_groups"][0]["missing_or_unrecognized_fields"])

    def test_no_footer_requirement_unclosed_table_flag(self):
        self.assertEqual(parse("<table>" + HEADER + ROW + "</table></body>")["flags"], [])
        self.assertIn("UNCLOSED_TABLE", parse("<table>" + HEADER + ROW)["flags"])

    def test_encoding_missing_conflict_unsupported_invalid(self):
        self.assertEqual(M.parse_summary(IDENTITY.encode(), "OB", OBS)["encoding"]["status"], "MISSING_ASCII_ONLY")
        self.assertEqual(M.parse_summary(b"\xff", "OB", OBS)["encoding"]["status"], "MISSING_NONASCII")
        for extra in ('<meta charset="latin-1">', '<meta charset="UTF-8" charset="latin-1">'):
            self.assertEqual(parse(extra)["encoding"]["status"], "CONFLICTING")
        self.assertEqual(parse('<meta charset="utf-16">')["encoding"]["status"], "UNSUPPORTED")
        self.assertEqual(M.parse_summary(META.encode() + b"\xff", "OB", OBS)["encoding"]["status"], "DECODE_FAILED")

    def test_http_equiv_declared_latin1(self):
        raw = ('<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">' + IDENTITY + "<p>ignored é</p>").encode("latin1")
        self.assertEqual(M.parse_summary(raw, "OM", OBS)["encoding"]["codec"], "iso8859-1")

    def test_privacy_no_science_contacts_or_unknown_values(self):
        secret = "private@example.invalid"
        result = parse(f"<table><tr><td>RA</td><td>123.456</td><td>Flux</td><td>987654</td></tr><tr><td>Observer</td><td>{secret}</td></tr></table>" + "<table>" + HEADER + ROW.replace("PrimeFullWindow", secret) + "</table>")
        serialized = json.dumps(result, allow_nan=False)
        for forbidden in (secret, "123.456", "987654", "Observer", "Flux"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(result["exposure_rows"][0]["fields"]["mode"]["status"], "UNRECOGNIZED")

    def test_script_style_ignored_and_no_external_actions(self):
        result = parse('<script>Observation ID: 9999999901</script><style>RA 55</style><img src="https://invalid/secret">')
        self.assertEqual(result["identity"]["status"], "MATCH")
        self.assertEqual(result["product_references"], [])

    def test_relevant_observed_refs_only_no_url_or_coordinate(self):
        base = "P" + OBS + "PNS003PIEVLI0000.FTZ"
        refs = parse(f'<a href="https://invalid/private/{base}?contact=secret">x</a><a href="P{OBS}PNS003SRCTSR0001.FTZ">ignored</a>')
        self.assertEqual(refs["product_references"], [base])
        self.assertNotIn("https", json.dumps(refs))

    def test_bound_and_types(self):
        for raw, role, obs in ((b"", "OB", OBS), (b"x" * (M.MAX_BYTES + 1), "OB", OBS), (b"x", [], OBS), (b"x", "OB", True)):
            with self.assertRaises(ValueError):
                M.parse_summary(raw, role, obs)
        with self.assertRaises(TypeError):
            M.parse_summary("not bytes", "OB", OBS)

    def test_cross_role_alias_conflict_missingness_not_chosen(self):
        first = parse("<table>" + HEADER + ROW + "</table>", "OB")
        second = parse("<table>" + HEADER + ROW.replace("EPN", "PN").replace("PrimeFullWindow", "PrimeSmallWindow") + "</table>", "EP")
        compare = M.compare_summaries([first, second], OBS)
        self.assertEqual(compare["roles_missing"], ["OM", "RG"])
        self.assertEqual(len(compare["exposure_groups"]), 1)
        self.assertEqual(compare["exposure_groups"][0]["conflicting_fields"], ["mode"])
        self.assertEqual(compare["exposure_groups"][0]["records"], 2)
        self.assertEqual(compare["exposure_groups"][0]["comparison_scope"], "CROSS_ROLE")
        self.assertIn("duration", compare["exposure_groups"][0]["missing_label_unit_fields"])
        single = M.compare_summaries([first], OBS)
        self.assertEqual(single["exposure_groups"][0]["comparison_scope"], "SINGLE_ROLE_UNMATCHED")

    def test_processing_dates_not_assumed_same_across_roles(self):
        first = parse("<p>Processing Date: 2020-01-02T03:04:05</p>", "OB")
        second = parse("<p>Processing Date: 2021-01-02T03:04:05</p>", "EP")
        compare = M.compare_summaries([first, second], OBS)
        self.assertEqual(compare["observation_conflicting_fields"], [])
        self.assertEqual(compare["processing_comparison"], "ROLE_SCOPED_NOT_ASSUMED_EQUAL")


if __name__ == "__main__":
    unittest.main()
