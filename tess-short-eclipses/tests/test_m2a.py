"""Synthetic PRF structure and transport tests; no downloaded calibration data."""

import importlib.util
import tempfile
import unittest
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import requests
from astropy.io import fits

SPEC = importlib.util.spec_from_file_location("m2a_test", Path(__file__).parents[1] / "scripts/m2a.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def fixture(selected=None):
    selected = selected or A.products()[0]
    hdus = fits.HDUList([fits.PrimaryHDU(np.ones((117, 117))), fits.ImageHDU(np.ones((117, 117)) * .01)])
    for index, hdu in enumerate(hdus):
        h = hdu.header
        for key, value in {"ORIGIN": "MIT", "TELESCOP": "TESS", "CAM": selected["camera"],
                           "CCD": selected["ccd"], "CCD_RREF": selected["row"], "CCD_CREF": selected["column"],
                           "NSAMP": 9, "PRF_RES": 2.35, "DATATYPE": "PRF" if index == 0 else "Uncertainties",
                           "WCSNAMEP": "PHYSICAL", "WCSAXESP": 2}.items():
            h[key] = value
        if index == 0:
            h["VERSION"] = "UPDATED_2.0"
        for axis, name, value in ((1, "RAWX", selected["column"]), (2, "RAWY", selected["row"])):
            for key, val in ((f"CTYPE{axis}P", name), (f"CUNIT{axis}P", "PIXEL"), (f"CRPIX{axis}P", 59),
                             (f"CRVAL{axis}P", value), (f"CDELT{axis}P", 1 / 9)):
                h[key] = val
    return hdus


class StructuralTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "synthetic.fits"
        self.selected = A.products()[0]

    def validate(self, hdus):
        hdus.writeto(self.path, overwrite=True)
        return A.validate(self.path, self.selected)

    def test_exact_twelve_grid_products(self):
        products = A.products()
        self.assertEqual(len(products), 12)
        self.assertEqual(len({p["filename"] for p in products}), 12)
        self.assertEqual(products[4]["filename"], "tess2019107181902-prf-4-3-row1536-col0557.fits")
        self.assertEqual(products[-1]["filename"], "tess2019107181901-prf-2-3-row2048-col2092.fits")
        self.assertTrue(all(p["url"].startswith(A.BASE) for p in products))
        self.assertLessEqual(len(products) * 300_000, 4_000_000)
        with self.assertRaisesRegex(ValueError, "SELECTION"):
            A.product("../unexpected.fits")

    def test_export_schema_no_extension_version_or_invented_units(self):
        result = self.validate(fixture())
        self.assertEqual(result["bytes"], 230400)
        self.assertEqual(result["status"], "PRF_PRODUCT_STRUCTURALLY_VALID")
        self.assertEqual(result["reference_sample_zero_based"], [58, 58])
        self.assertEqual(result["native_reference"], [1580, 1025])
        self.assertEqual([r["bunit"] for r in result["hdus"]], [None, None])
        self.assertFalse(result["localization_validated"])

    def test_wrong_identity_sampling_version_and_axis_rejected(self):
        for key, value in (("CAM", 4), ("CCD", 4), ("CCD_RREF", 1026), ("CCD_CREF", 1624),
                           ("NSAMP", 8), ("VERSION", "OLD"), ("CRPIX1P", 58), ("CRVAL1P", 1581),
                           ("CDELT1P", .1), ("CTYPE1P", "RAWY"), ("CUNIT1P", "deg")):
            hdus = fixture()
            hdus[0].header[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "KEY_VALUE"):
                self.validate(hdus)

    def test_extension_identity_and_optional_version_agree(self):
        hdus = fixture()
        hdus[1].header["VERSION"] = "UPDATED_2.0"
        self.validate(hdus)
        for key, value in (("DATATYPE", "PRF"), ("VERSION", "WRONG"), ("CAM", 1), ("CRVAL2P", 1026)):
            hdus = fixture()
            hdus[1].header[key] = value
            with self.assertRaisesRegex(ValueError, "KEY_VALUE"):
                self.validate(hdus)

    def test_shape_precision_extra_hdu_and_scaling_rejected(self):
        for data in (np.ones((116, 117)), np.ones((117, 117), dtype=np.float32), np.ones((1, 117, 117))):
            hdus = fixture()
            hdus[0].data = data
            with self.assertRaises(ValueError):
                self.validate(hdus)
        hdus = fixture()
        hdus.append(fits.ImageHDU())
        with self.assertRaisesRegex(ValueError, "HDU_STRUCTURE"):
            self.validate(hdus)
        hdus = fixture()
        hdus[0].header["BSCALE"] = 2
        with self.assertRaisesRegex(ValueError, "KEY_VALUE"):
            self.validate(hdus)

    def test_duplicate_physical_cross_terms_and_wrong_units_rejected(self):
        hdus = fixture()
        hdus[0].header.append(("CAM", 3))
        with self.assertRaisesRegex(ValueError, "KEY_COUNT"):
            self.validate(hdus)
        hdus = fixture()
        hdus[1].header["PC1_1P"] = 1
        with self.assertRaisesRegex(ValueError, "CROSS_TERMS"):
            self.validate(hdus)

    def test_signed_prf_retained_uncertainty_negative_nonfinite_stop(self):
        hdus = fixture()
        hdus[0].data[0, 0] = -.1
        self.assertEqual(self.validate(hdus)["hdus"][0]["negative_samples"], 1)
        for index, value in ((0, np.nan), (1, np.inf), (1, -.01)):
            hdus = fixture()
            hdus[index].data[0, 0] = value
            with self.assertRaises(ValueError):
                self.validate(hdus)
        hdus = fixture()
        hdus[0].data[:] = 0
        with self.assertRaisesRegex(ValueError, "SUPPORT"):
            self.validate(hdus)
        hdus[0].data[:] = 1e308
        with self.assertWarns(RuntimeWarning), self.assertRaisesRegex(ValueError, "SUPPORT"):
            self.validate(hdus)

    def test_checksums_optional_but_verified_if_present(self):
        fixture().writeto(self.path, checksum=True)
        A.validate(self.path, self.selected)
        raw = bytearray(self.path.read_bytes())
        raw[2880 + 100] ^= 1
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "CHECKSUM"):
            A.validate(self.path, self.selected)

    def test_truncation_extra_bytes_and_byte_cap_rejected(self):
        self.validate(fixture())
        raw = self.path.read_bytes()
        for content in (raw[:-1], raw[:-2880], raw + b"x", b"x" * 300001):
            self.path.write_bytes(content)
            with self.assertRaises((ValueError, OSError)):
                A.validate(self.path, self.selected)

    def test_physical_reference_no_added_offset(self):
        h = fixture()[0].header
        self.assertEqual(h["CRVAL1P"] + ((58 + 1) - h["CRPIX1P"]) * h["CDELT1P"], 1580)
        self.assertEqual(h["CRVAL2P"] + ((58 + 1) - h["CRPIX2P"]) * h["CDELT2P"], 1025)


class TransportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for key, value in (("ROOT", self.root), ("DATA", self.root / "data"),
                           ("MANIFEST", self.root / "manifest.json"), ("SUMMARY", self.root / "summary.json")):
            item = patch.object(A, key, value)
            item.start()
            self.addCleanup(item.stop)
        A.M.save(A.MANIFEST, {"synthetic": True})
        self.name = A.products()[0]["filename"]
        self.folder = A.folder_for(self.name)
        self.verify = patch.object(A, "verify")
        self.verify.start()
        self.addCleanup(self.verify.stop)
        logger = patch.object(A.LOGGER, "exception")
        logger.start()
        self.addCleanup(logger.stop)

    def reserve(self):
        A.M.save(A.DATA / "run-start.json", {"approved_manifest_sha256": A.M.sha(A.MANIFEST)})
        A.M.save(self.folder / "attempt.json", A.attempt(self.name))

    def response(self, *, status=200, chunks=None, length=None):
        buffer = BytesIO()
        fixture().writeto(buffer)
        response = MagicMock()
        response.status_code = status
        response.headers = {} if length is None else {"Content-Length": str(length)}
        response.iter_content.return_value = [buffer.getvalue()] if chunks is None else chunks
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value.__enter__.return_value = response
        return session

    def test_exact_one_get_no_retry_redirect_and_validated_receipt(self):
        self.reserve()
        session = self.response()
        with patch("requests.Session", return_value=session):
            A.worker(self.name)
            with self.assertRaises(FileExistsError):
                A.worker(self.name)
        session.get.assert_called_once_with(A.product(self.name)["url"], timeout=(30, 30),
                                           stream=True, allow_redirects=False)
        self.assertEqual(session.mount.call_args.args[1].max_retries.total, 0)
        self.assertTrue((self.folder / "response-receipt.json").exists())
        self.assertTrue((self.folder / "validation.json").exists())

    def test_direct_worker_and_wrong_review_hash_never_request(self):
        with patch("requests.Session") as network, self.assertRaises(FileNotFoundError):
            A.worker(self.name)
        network.assert_not_called()
        with self.assertRaisesRegex(ValueError, "REVIEW_GO"):
            A.run("wrong")
        self.assertFalse((A.DATA / "run-start.json").exists())

    def test_redirect_failure_retained(self):
        self.reserve()
        with patch("requests.Session", return_value=self.response(status=302)), self.assertRaisesRegex(ValueError, "HTTP"):
            A.worker(self.name)
        self.assertTrue((self.folder / "failure.json").exists())
        self.assertFalse((self.folder / "validation.json").exists())

    def test_streamed_cap_preserves_partial_and_stops_validation(self):
        self.reserve()
        session = self.response(chunks=[b"a" * 200000, b"b" * 200000])
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "TRANSFER_LIMIT"):
            A.worker(self.name)
        self.assertEqual((self.folder / self.name).stat().st_size, 200000)
        self.assertFalse((self.folder / "response-receipt.json").exists())
        self.assertTrue((self.folder / "failure.json").exists())

    def test_socket_timeout_retains_exclusive_attempt(self):
        self.reserve()
        session = self.response()
        session.get.side_effect = requests.Timeout("synthetic")
        with patch("requests.Session", return_value=session), self.assertRaises(requests.Timeout):
            A.worker(self.name)
        self.assertTrue((self.folder / "failure.json").exists())
        with patch("requests.Session") as network, self.assertRaises(FileExistsError):
            A.worker(self.name)
        network.assert_not_called()

    def test_parent_first_failure_accounts_all_and_readonly_replay(self):
        runner, loader = MagicMock(), MagicMock()
        runner.bounded_run.return_value = (124, "synthetic deadline")
        with (patch.object(A.importlib.util, "spec_from_file_location", return_value=SimpleNamespace(loader=loader)),
              patch.object(A.importlib.util, "module_from_spec", return_value=runner), redirect_stdout(StringIO())):
            A.run(A.M.sha(A.MANIFEST))
        self.assertEqual(runner.bounded_run.call_count, 1)
        self.assertEqual(runner.bounded_run.call_args.args[1], 45)
        summary = A.read(A.SUMMARY)
        self.assertEqual(len(summary["outcomes"]), 12)
        self.assertEqual([r["status"] for r in summary["outcomes"]][1:], ["STOP_NOT_LAUNCHED"] * 11)
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch("requests.Session") as network, redirect_stdout(StringIO()):
            A.replay()
        network.assert_not_called()
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_parent_all_twelve_synthetic_receipts_replay_and_raw_codes(self):
        runner, loader = MagicMock(), MagicMock()

        def successful(command, _deadline):
            name = command[-1]
            buffer = BytesIO()
            fixture(A.product(name)).writeto(buffer)
            session = self.response(chunks=[buffer.getvalue()], length=str(len(buffer.getvalue())))
            with patch("requests.Session", return_value=session):
                A.worker(name)
            return 0, "synthetic success"

        runner.bounded_run.side_effect = successful
        with (patch.object(A.importlib.util, "spec_from_file_location", return_value=SimpleNamespace(loader=loader)),
              patch.object(A.importlib.util, "module_from_spec", return_value=runner), redirect_stdout(StringIO())):
            A.run(A.M.sha(A.MANIFEST))
        self.assertEqual(runner.bounded_run.call_count, 12)
        summary = A.read(A.SUMMARY)
        self.assertEqual(summary["status"], "PRF_PRODUCTS_STRUCTURALLY_VALID")
        self.assertTrue(all(r["worker_returncode"] == r["returncode"] == 0 for r in summary["outcomes"]))
        with patch("requests.Session") as network, redirect_stdout(StringIO()):
            A.replay()
        network.assert_not_called()

    def test_terminal_codes_and_per_row_science_promotions_rejected(self):
        row = {"filename": self.name, "returncode": 0, "worker_returncode": 0,
               "status": "PRF_PRODUCT_STRUCTURALLY_VALID", "output": "", "elapsed_seconds": .1, "artifacts": {}}
        summary = {"manifest_sha256": "synthetic", "outcomes": [row], "status": "PRF_PRODUCTS_STRUCTURALLY_VALID",
                   "localization_validated": False, "unknown_search_authorized": False}
        A.terminal_checks(summary)
        for key, value in (("returncode", 1), ("worker_returncode", None), ("elapsed_seconds", float("nan")),
                           ("status", "STOP_NOT_LAUNCHED"), ("unknown_search_authorized", True)):
            changed = {**summary, "outcomes": [{**row, key: value}]}
            with self.subTest(key=key), self.assertRaises(ValueError):
                A.terminal_checks(changed)


if __name__ == "__main__":
    unittest.main()
