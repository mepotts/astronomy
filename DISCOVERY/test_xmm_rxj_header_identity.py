"""Synthetic headers only: no files, source coordinates or scientific arrays."""

import copy
import json
import unittest

import xmm_rxj_header_identity as M
from astropy.io.fits import Header


def fixture(camera="EPN", exposure="S001"):
    primary = Header()
    for k, v in (("SIMPLE", True), ("BITPIX", 8), ("NAXIS", 0),
                 ("OBS_ID", M.OBS_ID), ("INSTRUME", camera), ("EXPIDSTR", exposure)):
        primary[k] = v
    events = Header()
    for k, v in (("XTENSION", "BINTABLE"), ("BITPIX", 8), ("NAXIS", 2),
                 ("NAXIS1", 8), ("NAXIS2", 7), ("PCOUNT", 0), ("GCOUNT", 1),
                 ("EXTNAME", "EVENTS"), ("TFIELDS", 1), ("TTYPE1", "TIME"),
                 ("TFORM1", "1D"), ("TUNIT1", "s")):
        events[k] = v
    return [primary, events]


def report(headers):
    return {"status": "HEADER_LAYOUT_ONLY", "declared_data_region_bytes_read": 0,
            "hdu_count": len(headers), "hdus": [
                {"hdu": i, "cards": [str(c) for c in h.cards]} for i, h in enumerate(headers)]}


def check(headers, camera="EPN", exposure="S001"):
    return M.inspect_identity(report(headers), camera, exposure)


class IdentityTests(unittest.TestCase):
    def test_three_cameras_primary_only_identity(self):
        for camera, exposure in M.EXPOSURES.items():
            result = check(fixture(camera, exposure), camera, exposure)
            self.assertEqual(result["status"], "HEADER_IDENTITY_AUTHENTICATED")
            self.assertEqual(result["identity"][1]["fields"]["OBS_ID"]["state"], "MISSING")

    def test_events_only_and_split_identity(self):
        for keys in (("OBS_ID", "INSTRUME", "EXPIDSTR"), ("OBS_ID",)):
            h = fixture()
            for key in keys:
                h[1][key] = h[0][key]
                del h[0][key]
            self.assertEqual(check(h)["status"], "HEADER_IDENTITY_AUTHENTICATED")

    def test_missing_and_not_replaced_by_numeric_exp_id(self):
        h = fixture()
        del h[0]["EXPIDSTR"]
        h[0]["EXP_ID"] = int(M.OBS_ID + "001")
        self.assertEqual(check(h)["status"], "STOP_HEADER_IDENTITY_MISSING")

    def test_cross_hdu_conflict_and_duplicate(self):
        for key, value in (("OBS_ID", "0000000000"), ("INSTRUME", "EMOS1"),
                           ("EXPIDSTR", "U001"), ("EXP_ID", 999)):
            h = fixture()
            h[1][key] = value
            self.assertEqual(check(h)["status"], "STOP_HEADER_IDENTITY_CONFLICT")
        h = fixture()
        h[0].append(("OBS_ID", M.OBS_ID))
        self.assertEqual(check(h)["status"], "STOP_HEADER_IDENTITY_CONFLICT")

    def test_optional_exp_id_forms_and_boolean(self):
        for value in (M.OBS_ID + "001", int(M.OBS_ID + "001")):
            h = fixture()
            h[1]["EXP_ID"] = value
            self.assertEqual(check(h)["status"], "HEADER_IDENTITY_AUTHENTICATED")
        h[1]["EXP_ID"] = True
        self.assertEqual(check(h)["status"], "STOP_HEADER_IDENTITY_CONFLICT")

    def test_sole_events_required_and_duplicate_extname(self):
        h = fixture()
        for headers in (h[:1], h + [copy.deepcopy(h[1])]):
            self.assertEqual(check(headers)["status"], "STOP_HEADER_IDENTITY_CONFLICT")
        h[1].append(("EXTNAME", "EVENTS"))
        self.assertEqual(check(h)["status"], "STOP_HEADER_IDENTITY_CONFLICT")

    def test_metadata_missing_unknown_not_identity_failure(self):
        h = fixture()
        h[1]["SUBMODE"] = "future-mode"
        h[1]["FILTER"] = "Thin1"
        result = check(h)
        self.assertEqual(result["status"], "HEADER_IDENTITY_AUTHENTICATED")
        meta = result["hdus"][1]["metadata"]
        self.assertEqual(meta["SUBMODE"]["candidates"][0]["state"], "UNRECOGNIZED")
        self.assertEqual(meta["FILTER"]["candidates"][0]["value"], "Thin1")
        self.assertEqual(meta["TIMESYS"]["state"], "MISSING")

    def test_privacy_arbitrary_metadata_columns_comments(self):
        h = fixture()
        canary = "PRIVATE_CONTACT_OR_COORDINATE"
        for key in ("SUBMODE", "FILTER", "CREATOR", "SAS_CCF", "OBSERVER", "TTYPE1", "TUNIT1"):
            h[1][key] = canary
        h[1]["RA_PNT"] = 123.456789
        h[1]["TCRVL1"] = 234.567891
        h[1].add_comment(canary)
        text = json.dumps(check(h), allow_nan=False)
        for forbidden in (canary, "123.456789", "234.567891", "RA_PNT"):
            self.assertNotIn(forbidden, text)

    def test_hash_only_provenance_missing_and_duplicate(self):
        h = fixture()
        h[1]["CREATOR"] = "PRIVATE_GENERATOR"
        h[1].append(("CREATOR", "PRIVATE_OTHER_GENERATOR"))
        h[1]["SAS_CCF"] = "PRIVATE_CALIBRATION_PATH"
        result = check(h)
        fields = result["hdus"][1]["provenance"]
        self.assertEqual(fields["SAS_VER"]["state"], "MISSING")
        self.assertEqual(fields["CREATOR"]["state"], "DUPLICATE")
        self.assertEqual(fields["CREATOR"]["count"], 2)
        for candidate in fields["CREATOR"]["candidates"] + fields["SAS_CCF"]["candidates"]:
            self.assertEqual(candidate["state"], "INTENTIONALLY_HASHED")
            self.assertIsNone(candidate["value"])
            self.assertEqual(len(candidate["sha256"]), 64)
        self.assertNotIn("PRIVATE_", json.dumps(result))

    def test_schema_null_scaling_and_duplicates_preserved(self):
        h = fixture()
        h[1]["TSCAL1"] = 2
        h[1]["TZERO1"] = 0
        h[1]["TNULL1"] = -99
        h[1].append(("TUNIT1", "sec"))
        column = check(h)["hdus"][1]["columns"][0]
        self.assertEqual(column["scale"]["candidates"][0]["value"], 2)
        self.assertEqual(column["null"]["candidates"][0]["value"], -99)
        self.assertEqual(column["unit"]["count"], 2)

    def test_ancillary_missingness_and_unknown_names(self):
        h = fixture()
        extra = Header()
        extra["EXTNAME"] = "PRIVATE_EXTENSION"
        extra["TFIELDS"] = 0
        h.append(extra)
        result = check(h)
        self.assertEqual(result["hdu_count"], 3)
        self.assertNotIn("PRIVATE_EXTENSION", json.dumps(result))

    def test_config_and_report_caps(self):
        for camera, exposure, obs in ((True, "S001", M.OBS_ID), ("EPN", "S002", M.OBS_ID),
                                      ("EPN", "S001", "0000000000")):
            with self.assertRaisesRegex(ValueError, "STOP_EXPECTED_IDENTITY_CONFIG"):
                M.inspect_identity(report(fixture()), camera, exposure, obs)
        for key, value in (("status", "SCIENCE"), ("hdu_count", 999),
                           ("declared_data_region_bytes_read", 1)):
            r = report(fixture())
            r[key] = value
            with self.assertRaises(ValueError):
                M.inspect_identity(r, "EPN", "S001")

    def test_input_immutable_and_no_array_api(self):
        r = report(fixture())
        old = copy.deepcopy(r)
        M.inspect_identity(r, "EPN", "S001")
        self.assertEqual(r, old)


if __name__ == "__main__":
    unittest.main()
