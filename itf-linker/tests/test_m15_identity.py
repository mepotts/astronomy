"""Synthetic identities only: no private astrometry and no network dependencies."""

import json
import sys
import unittest
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import m15_identity as identity


def obs(number=1, *, source="a", seconds="03.123", note=" ", day="12.123456"):
    line = list(" " * 80)
    for start, text in ((12, " " + note + "C"), (15, "2026 09 " + day),
                        (32, "01 02 " + seconds.ljust(6)), (44, "+04 05 06.78 "),
                        (77, "500")):
        line[start:start + len(text)] = text
    return identity.observation("".join(line), source_sha256=source * 64, row_number=number)


def resid(row, *, incl=1):
    return dict(zip(identity.IDENTITY_FIELDS, (str(row.jd), str(row.ra), str(row.dec),
                row.station, row.note1, row.note2, row.discovery), strict=True), incl=incl)


CONTRACT = identity.ExportContract("f" * 64, D("1e-8"), D("1e-8"), D("1e-8"))


class IdentityTests(unittest.TestCase):
    def assertHold(self, result):
        self.assertEqual(result["status"], "HOLD")
        self.assertIsNone(result["used"])
        self.assertEqual(result["pairs"], [])

    def test_nearby_published_same_epoch_different_position(self):
        a = obs()
        p = obs(source="b", seconds="03.124")  # 0.015 arcsec in RA, not 1.5 arcsec!
        result = identity.match([p], [a], [resid(a), resid(p, incl=0)], CONTRACT)
        self.assertEqual(result["status"], "MATCHED")
        self.assertEqual(result["used"], 1)
        self.assertEqual(result["pairs"], [(0, 1), (1, 0)])

    def test_exact_published_duplicate_rejected_before_fitting(self):
        result = identity.match([obs(source="b")], [obs()], [])
        self.assertEqual(result["status"], "ALREADY_PUBLISHED")
        self.assertIsNone(result["used"])

    def test_duplicate_with_different_written_precision(self):
        p = obs(source="b", seconds="03.12", day="12.12345 ")
        a = obs(seconds="03.120", day="12.123450")
        self.assertEqual(identity.match([p], [a], [])["status"], "ALREADY_PUBLISHED")

    def test_repeated_equal_time_distinct_rows_consumed_once(self):
        a, b = obs(), obs(2, seconds="03.124")
        result = identity.match([], [a, b], [resid(b, incl=0), resid(a)], CONTRACT)
        self.assertEqual(result["status"], "MATCHED")
        self.assertEqual(result["used"], 1)
        self.assertEqual(len({j for _, j in result["pairs"]}), 2)

    def test_repeated_identical_occurrences_are_ambiguous_not_order_matched(self):
        a, b = obs(), obs(2)
        self.assertHold(identity.match([], [a, b], [resid(a), resid(b)], CONTRACT))

    def test_one_residual_cannot_satisfy_two_inputs(self):
        a, b = obs(), obs(2)
        self.assertHold(identity.match([], [a, b], [resid(a)], CONTRACT))

    def test_two_inputs_competing_for_same_residual_hold(self):
        a, b = obs(), obs(2)
        other = resid(obs(3, seconds="04.000"))
        self.assertHold(identity.match([], [a, b], [resid(a), other], CONTRACT))

    def test_nontransitive_tolerance_does_not_greedily_resolve_unique_global_map(self):
        # A--R1--B--R2 is a nontransitive compatibility chain. A global perfect
        # map exists, but this intentionally conservative prototype still HOLDs.
        from itertools import permutations
        a = replace(obs(), ra=D(10), ra_quantum=D("1e-10"))
        b = replace(obs(2), ra=D("10.000000018"), ra_quantum=D("1e-10"))
        r1, r2 = resid(a), resid(b)
        r1["RA"], r2["RA"] = "10.000000009", "10.000000027"
        for inputs in permutations((a, b)):
            for residuals in permutations((r1, r2)):
                self.assertHold(identity.match([], list(inputs), list(residuals), CONTRACT))

    def test_multiple_full_assignments_hold_for_every_order(self):
        from itertools import permutations
        a = replace(obs(), ra=D(10), ra_quantum=D("1e-10"))
        b = replace(obs(2), ra=D("10.000000015"), ra_quantum=D("1e-10"))
        r1, r2 = resid(a), resid(b, incl=0)
        r1["RA"], r2["RA"] = "10.000000007", "10.000000008"
        for inputs in permutations((a, b)):
            for residuals in permutations((r1, r2)):
                self.assertHold(identity.match([], list(inputs), list(residuals), CONTRACT))

    def test_unmatched_residual_holds_even_if_counts_equal(self):
        a = obs()
        self.assertHold(identity.match([], [a], [resid(obs(seconds="04.000"))], CONTRACT))

    def test_extra_residual_cannot_inflate_used(self):
        a = obs()
        self.assertHold(identity.match([], [a], [resid(a), resid(a)], CONTRACT))

    def test_missing_published_residual_also_holds(self):
        a, p = obs(), obs(source="b", seconds="04.000")
        self.assertHold(identity.match([p], [a], [resid(a)], CONTRACT))

    def test_no_guessed_export_contract(self):
        a = obs()
        self.assertHold(identity.match([], [a], [resid(a)]))

    def test_missing_every_required_field_holds(self):
        a = obs()
        for key in (*identity.IDENTITY_FIELDS, "incl"):
            with self.subTest(key=key):
                r = resid(a)
                del r[key]
                self.assertHold(identity.match([], [a], [r], CONTRACT))

    def test_inclusion_must_be_explicit_integer_zero_or_one(self):
        a = obs()
        for value in (None, True, "1", "0", 2, -1, 0.0):
            with self.subTest(value=value):
                self.assertHold(identity.match([], [a], [resid(a, incl=value)], CONTRACT))

    def test_flags_never_substitute_for_incl(self):
        a = obs()
        r = resid(a, incl=0)
        r["flags"] = 999
        self.assertEqual(identity.match([], [a], [r], CONTRACT)["used"], 0)

    def test_notes_and_discovery_are_part_of_identity(self):
        a = obs()
        for key, value in (("note1", "X"), ("note2", "B"), ("discovery_asterisk", "*")):
            with self.subTest(key=key):
                r = resid(a)
                r[key] = value
                self.assertHold(identity.match([], [a], [r], CONTRACT))

    def test_nonfinite_or_binary_float_identity_holds(self):
        a = obs()
        for key in ("JD", "RA", "Dec"):
            for value in ("NaN", "Infinity", 3.0, None):
                with self.subTest(key=key, value=value):
                    r = resid(a)
                    r[key] = value
                    self.assertHold(identity.match([], [a], [r], CONTRACT))

    def test_declared_export_rounding_not_astrometric_matching_tolerance(self):
        a = obs()
        r = resid(a)
        r["JD"] = str(a.jd + D("0.000000009"))
        self.assertEqual(identity.match([], [a], [r], CONTRACT)["status"], "MATCHED")
        r["JD"] = str(a.jd + D("0.00000002"))
        self.assertHold(identity.match([], [a], [r], CONTRACT))

    def test_bad_contracts_hold(self):
        a = obs()
        for changes in ({"evidence_sha256": ""}, {"timescale": "TDB"},
                        {"complete_rows": False}, {"notes_verbatim": False},
                        {"jd_error": D("0.0002")}, {"ra_error": D("NaN")},
                        {"dec_error": D("-1e-9")}):
            with self.subTest(changes=changes):
                self.assertHold(identity.match([], [a], [resid(a)], replace(CONTRACT, **changes)))

    def test_reusing_input_occurrence_holds(self):
        a = obs()
        self.assertHold(identity.match([], [a, a], [resid(a), resid(a)], CONTRACT))

    def test_all_permutations_and_inclusion_patterns_preserve_bound(self):
        from itertools import permutations, product
        rows = [obs(i + 1, seconds=f"0{i + 1}.000") for i in range(3)]
        for order in permutations(range(3)):
            for used in product((0, 1), repeat=3):
                residuals = [resid(rows[i], incl=used[i]) for i in order]
                result = identity.match([], rows, residuals, CONTRACT)
                self.assertEqual(result["status"], "MATCHED")
                self.assertEqual(result["used"], sum(used))
                self.assertLessEqual(result["used"], result["appended_total"])
                self.assertEqual(len(set(result["pairs"])), 3)

    def test_obs80_retains_source_occurrence_precision_notes(self):
        a = obs(4, note="X")
        self.assertEqual(a.source_sha256, "a" * 64)
        self.assertEqual(a.row_number, 4)
        self.assertEqual(a.jd_quantum, D("1e-6"))
        self.assertEqual(a.ra_quantum, D("0.001") / 240)
        self.assertEqual(a.note1, "X")
        self.assertTrue(identity.valid_hash(a.line_sha256))

    def test_unsupported_row_types_do_not_disappear(self):
        for value in ("S", "s", "V", "v", "R", "r", " "):
            line = " " * 14 + value + " " * 65
            with self.assertRaises(identity.IdentityHold):
                identity.observation(line, source_sha256="a" * 64, row_number=1)

    def test_decimal_json_load_preserves_written_precision(self):
        doc = json.loads('{"JD":2461295.12345600}', parse_float=D)
        self.assertEqual(identity.quantum(doc["JD"]), D("1e-8"))

    def test_malformed_residual_containers_hold(self):
        a = obs()
        for row in (None, [], "not a row"):
            self.assertHold(identity.match([], [a], [row], CONTRACT))
        for key in ("note2", "discovery_asterisk"):
            r = resid(a)
            r[key] = []
            self.assertHold(identity.match([], [a], [r], CONTRACT))

    def test_counts_only_audit_does_not_echo_identifiers_or_values(self):
        from tempfile import TemporaryDirectory
        a = obs()
        # This file is a generated synthetic fixture, never retained science data.
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            document = {"objects": {"SYNTHETIC-PRIVATE-TOKEN": {
                "observations": {"residuals": [resid(a)]}}}}
            (folder / "total.json").write_text(json.dumps(document), encoding="utf-8")
            (folder / "obs.txt").write_text("synthetic fixture", encoding="utf-8")
            result = identity.compatibility_audit(folder)
            output = json.dumps(result)
            self.assertNotIn("SYNTHETIC-PRIVATE-TOKEN", output)
            self.assertNotIn(str(a.jd), output)
            self.assertNotIn(str(a.ra), output)
            self.assertEqual(result["status"], "HOLD_EXPORT_CONTRACT")
            self.assertEqual(result["scientific_rows_regraded"], 0)
            self.assertEqual(result["manifest_entries"], 2)


if __name__ == "__main__":
    unittest.main()
