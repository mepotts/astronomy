"""Offline numerical and fail-closed tests, not empirical science validation."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.io.fits import Header
from astropy.wcs import WCS

SPEC = importlib.util.spec_from_file_location("vlass_pilot", Path(__file__).parents[1] / "pilot.py")
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def header():
    return Header({"BUNIT": "JY/BEAM", "BMAJ": 3/3600, "BMIN": 2/3600,
                   "BPA": 30.0, "DATE-OBS": "2020-08-22T19:51:26",
                   "HISTORY": "VLASS3.1 synthetic test only", "OBJECT": "synthetic",
                   "NAXIS": 2, "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
                   "CRPIX1": 81., "CRPIX2": 81., "CRVAL1": pilot.TARGET[0],
                   "CRVAL2": pilot.TARGET[1], "CDELT1": -1/3600, "CDELT2": 1/3600})


def synthetic_epoch(amplitude=0.002):
    h = header()
    wcs = WCS(h)
    yy, xx = np.mgrid[:161, :161]
    east, north = -(xx-80), yy-80
    angle = np.radians(h["BPA"])
    u = east*np.sin(angle) + north*np.cos(angle)
    v = east*np.cos(angle) - north*np.sin(angle)
    template = np.exp(-4*np.log(2)*((u/3)**2+(v/2)**2))
    return {"array": amplitude*template + .00001, "rms": np.ones((161, 161))*.0001,
            "header": h, "wcs": wcs, "matrix": wcs.pixel_scale_matrix*3600}


class TestPilot(unittest.TestCase):
    def test_correct_units(self):
        pilot.validate_header(header(), "VLASS3.1")

    def test_wrong_units(self):
        h = header()
        h["BUNIT"] = "MJy/sr"
        with self.assertRaisesRegex(ValueError, "BUNIT"):
            pilot.validate_header(h, "VLASS3.1")

    def test_missing_beam(self):
        h = header()
        del h["BMAJ"]
        with self.assertRaisesRegex(ValueError, "beam"):
            pilot.validate_header(h, "VLASS3.1")

    def test_beam_order(self):
        h = header()
        h["BMIN"] = 10/3600
        with self.assertRaisesRegex(ValueError, "exceeds"):
            pilot.validate_header(h, "VLASS3.1")

    def test_missing_date(self):
        h = header()
        del h["DATE-OBS"]
        with self.assertRaisesRegex(ValueError, "DATE"):
            pilot.validate_header(h, "VLASS3.1")

    def test_projection_known_amplitude(self):
        template = np.array([1., .5, .1])
        self.assertAlmostEqual(pilot.amplitude(2*template + .3, template, .3), 2)

    def test_empty_template(self):
        with self.assertRaises(ValueError):
            pilot.amplitude(np.array([1.]), np.array([0.]), 0)

    def test_gaussian_control_recovered(self):
        result = pilot.photometry(synthetic_epoch(), *pilot.TARGET)
        self.assertTrue(result["recovered"])
        self.assertAlmostEqual(result["amplitude_jy"], .002, places=10)
        self.assertAlmostEqual(result["noise_proxy_jy"], .0001, places=10)
        self.assertAlmostEqual(result["amplitude_over_noise"], 20, places=7)

    def test_negative_flux_not_recovery(self):
        result = pilot.photometry(synthetic_epoch(-.002), *pilot.TARGET)
        self.assertFalse(result["recovered"])
        self.assertLess(result["amplitude_over_noise"], 0)

    def test_nonfinite_patch_rejected(self):
        epoch = synthetic_epoch()
        epoch["array"][80, 80] = np.nan
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            pilot.photometry(epoch, *pilot.TARGET)

    def test_nonpositive_rms_rejected(self):
        epoch = synthetic_epoch()
        epoch["rms"][80, 80] = 0
        with self.assertRaisesRegex(ValueError, "RMS"):
            pilot.photometry(epoch, *pilot.TARGET)

    def test_edge_rejected(self):
        epoch = synthetic_epoch()
        ra, dec = epoch["wcs"].all_pix2world(10, 80, 0)
        with self.assertRaisesRegex(ValueError, "edge"):
            pilot.photometry(epoch, float(ra), float(dec))

    def test_datalink_semantics(self):
        xml = b'<VOTABLE><TABLE><FIELD name="semantics"/><FIELD name="access_url"/>' \
              b'<DATA><TABLEDATA><TR><TD>#this</TD><TD>https://example.test/x</TD></TR>' \
              b'</TABLEDATA></DATA></TABLE></VOTABLE>'
        self.assertEqual(pilot.links(xml), [{"semantics": "#this", "access_url": "https://example.test/x"}])

    def check_files(self, change_rms=None, change_entry=None):
        (pilot.ROOT / "data").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=pilot.ROOT / "data") as folder:
            image_path, rms_path = Path(folder)/"science.fits", Path(folder)/"rms.fits"
            epoch = synthetic_epoch()
            rh = epoch["header"].copy()
            if change_rms:
                change_rms(rh)
            fits.writeto(image_path, epoch["array"], epoch["header"])
            fits.writeto(rms_path, epoch["rms"], rh)
            entry = {"image": str(image_path), "rms": str(rms_path),
                     "campaign": "VLASS3.1", "t_min": 59083.82, "t_max": 59083.85,
                     "obs_id": "VLASS3.1.synthetic"}
            if change_entry:
                change_entry(entry)
            return pilot.load_epoch(entry)

    def test_matching_images_accepted(self):
        self.assertEqual(self.check_files()["array"].shape, (161, 161))

    def test_rms_wcs_mismatch(self):
        with self.assertRaisesRegex(ValueError, "WCS differs"):
            self.check_files(change_rms=lambda rh: rh.__setitem__("CRPIX1", 82))

    def test_observation_date_mismatch(self):
        with self.assertRaisesRegex(ValueError, "contradicts"):
            self.check_files(change_entry=lambda entry: entry.__setitem__("t_min", 60000))

    def test_wrong_field_identity(self):
        with self.assertRaisesRegex(ValueError, "OBJECT contradicts"):
            self.check_files(change_entry=lambda entry: entry.__setitem__("obs_id", "VLASS3.1.wrong"))

    def test_wrong_campaign_identity(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            pilot.validate_header(header(), "VLASS2.1")

    def test_rms_beam_mismatch(self):
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.check_files(change_rms=lambda rh: rh.__setitem__("BPA", 40))

    def test_preserved_science_unchanged_by_replay_fix(self):
        old = json.loads((pilot.ROOT / "measurement-followup-initial.json").read_text())
        new = json.loads((pilot.ROOT / "measurement-followup.json").read_text())
        old.pop("code_sha256")
        new.pop("code_sha256")
        self.assertEqual(old, new)

    def test_both_recorded_source_hashes(self):
        old = json.loads((pilot.ROOT / "measurement-followup-initial.json").read_text())
        new = json.loads((pilot.ROOT / "measurement-followup.json").read_text())
        with zipfile.ZipFile(pilot.ROOT / "pilot-initial.zip") as archive:
            self.assertEqual(hashlib.sha256(archive.read("pilot.py")).hexdigest(), old["code_sha256"])
        self.assertEqual(pilot.sha(pilot.ROOT / "pilot.py"), new["code_sha256"])


if __name__ == "__main__":
    unittest.main()
