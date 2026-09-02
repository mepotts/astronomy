from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from m0_audit import (  # noqa: E402
    EXPECTED_COLUMNS,
    M0Error,
    SURVEY_END_DATE,
    SURVEY_START_DATE,
    _mjd_from_iso_date,
    collapse_events,
    inspect_exposure,
    load_catalog,
    rayleigh_scan,
)


def row(event_id: str, sub_num: int, mjd: float) -> dict[str, str]:
    result = {column: "" for column in EXPECTED_COLUMNS}
    result.update(
        {
            "tns_name": f"FRB{event_id}",
            "repeater_name": "FRBTEST",
            "event_id": event_id,
            "sub_num": str(sub_num),
            "mjd_inf": str(mjd),
            "excluded_flag": "0",
            "sidelobe_flag": "0",
            "citizen_science_flag": "0",
        }
    )
    return result


class CatalogTests(unittest.TestCase):
    def test_collapse_is_order_independent_and_uses_first_arrival(self) -> None:
        events = collapse_events([row("2", 1, 60000.2), row("1", 0, 59000.0), row("2", 0, 60000.1)])
        self.assertEqual([event["event_id"] for event in events], ["1", "2"])
        self.assertEqual(events[1]["subburst_count"], 2)
        self.assertEqual(events[1]["event_mjd_inf"], 60000.1)

    def test_changed_event_invariant_fails_closed(self) -> None:
        first = row("1", 0, 59000.0)
        second = row("1", 1, 59000.1)
        second["repeater_name"] = "FRBOTHER"
        with self.assertRaises(M0Error):
            collapse_events([first, second])

    def test_schema_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["event_id"])
                writer.writeheader()
                writer.writerow({"event_id": "1"})
            with self.assertRaises(M0Error):
                load_catalog(path)


class PeriodTests(unittest.TestCase):
    def test_rayleigh_recovers_synthetic_period_in_bounded_search(self) -> None:
        cycle_numbers = np.array([0, 1, 3, 4, 7, 9, 10, 14, 16, 19, 23, 27, 31, 36, 41])
        jitter = np.array([0.03, -0.07, 0.02, 0.05, -0.04] * 3)
        times = 59000.0 + 17.0 * cycle_numbers + jitter
        result = rayleigh_scan(times, 10.0, 30.0, oversampling=12)
        self.assertAlmostEqual(result["best_period_days"], 17.0, delta=0.25)


class ExposureTests(unittest.TestCase):
    def survey_axis(self) -> np.ndarray:
        return np.arange(
            _mjd_from_iso_date(SURVEY_START_DATE),
            _mjd_from_iso_date(SURVEY_END_DATE) + 1.0,
        )

    def test_integrated_healpix_maps_fail_window_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exposure.h5"
            with h5py.File(path, "w") as handle:
                dataset = handle.create_dataset("upper", data=np.zeros(12))
                dataset.attrs["class"] = "HEALPIX"
                dataset.attrs["description"] = "Integrated exposure time over the survey"
                dataset.attrs["DIMENSION_LABELS"] = ["pixel"]
            result = inspect_exposure(path)
            self.assertTrue(result["integrated_sky_maps_only"])
            self.assertFalse(result["passes_window_gate"])

    def test_short_time_coordinate_fails_frozen_survey_span(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            with h5py.File(path, "w") as handle:
                dataset = handle.create_dataset("mjd", data=np.arange(58849.0, 58859.0))
                dataset.attrs["DIMENSION_LABELS"] = ["time"]
                dataset.attrs["units"] = "MJD"
            result = inspect_exposure(path)
            self.assertFalse(result["has_valid_time_axis"])
            self.assertFalse(result["passes_window_gate"])

    def test_survey_spanning_time_coordinate_alone_fails_window_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            with h5py.File(path, "w") as handle:
                dataset = handle.create_dataset("mjd", data=self.survey_axis())
                dataset.attrs["DIMENSION_LABELS"] = ["time"]
                dataset.attrs["units"] = "MJD"
            result = inspect_exposure(path)
            self.assertTrue(result["has_valid_time_axis"])
            self.assertFalse(result["has_aligned_operational_series"])
            self.assertFalse(result["passes_window_gate"])

    def test_aligned_time_and_spatial_sensitivity_pass_window_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            with h5py.File(path, "w") as handle:
                handle.attrs["start_date"] = SURVEY_START_DATE
                handle.attrs["end_date"] = SURVEY_END_DATE
                handle.attrs["contact"] = "must-not-appear@example.invalid"
                time_values = self.survey_axis()
                time = handle.create_dataset("mjd", data=time_values)
                time.attrs["DIMENSION_LABELS"] = ["time"]
                time.attrs["units"] = "MJD"
                values = np.ones((time_values.size, 12))
                values[::7, :] = 0.0
                state = handle.create_dataset(
                    "nominal_sensitivity", data=values, chunks=(64, 12)
                )
                state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                state.attrs["description"] = "Per-pixel nominal sensitivity"
                state.attrs["time_axis"] = "mjd"
                state.attrs["spatial_scheme"] = "HEALPIX"
                state.attrs["NSIDE"] = 1
                state.attrs["ORDERING"] = "RING"
                state.attrs["COORDSYS"] = "ICRS"
            result = inspect_exposure(path)
            self.assertTrue(result["has_valid_time_axis"])
            self.assertTrue(result["has_aligned_operational_series"])
            self.assertTrue(result["has_source_specific_exposure"])
            self.assertTrue(result["passes_window_gate"])
            self.assertNotIn("contact", result["root_attributes"])

    def test_unusable_or_unmapped_state_values_fail_window_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            with h5py.File(path, "w") as handle:
                time_values = self.survey_axis()
                time = handle.create_dataset("mjd", data=time_values)
                time.attrs["DIMENSION_LABELS"] = ["time"]
                time.attrs["units"] = "MJD"
                state = handle.create_dataset(
                    "nominal_sensitivity",
                    data=np.zeros((time_values.size, 12), dtype=float),
                )
                state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                state.attrs["time_axis"] = "mjd"
                state.attrs["NSIDE"] = 1
                state.attrs["ORDERING"] = "RING"
                state.attrs["COORDSYS"] = "ICRS"
            result = inspect_exposure(path)
            self.assertFalse(result["has_aligned_operational_series"])
            self.assertFalse(result["passes_window_gate"])

    def test_future_unlinked_no_outage_and_fake_mapping_all_fail(self) -> None:
        cases = ("future", "unlinked", "no_outage", "fake_mapping")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "window.h5"
                with h5py.File(path, "w") as handle:
                    time_values = self.survey_axis()
                    if case == "future":
                        time_values = time_values + 365.0
                    time = handle.create_dataset("mjd", data=time_values)
                    time.attrs["DIMENSION_LABELS"] = ["time"]
                    time.attrs["units"] = "MJD"
                    values = np.ones((time_values.size, 12))
                    if case != "no_outage":
                        values[::7, :] = 0.0
                    state = handle.create_dataset(
                        "nominal_sensitivity", data=values, chunks=(64, 12)
                    )
                    state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                    if case != "unlinked":
                        state.attrs["time_axis"] = "mjd"
                    state.attrs["spatial_scheme"] = "HEALPIX"
                    state.attrs["NSIDE"] = 2 if case == "fake_mapping" else 1
                    state.attrs["ORDERING"] = "RING"
                    state.attrs["COORDSYS"] = "ICRS"
                result = inspect_exposure(path)
                self.assertFalse(result["passes_window_gate"])

    def test_super_window_with_multiyear_gap_fails_time_axis_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            start = _mjd_from_iso_date(SURVEY_START_DATE)
            end = _mjd_from_iso_date(SURVEY_END_DATE)
            time_values = np.concatenate((np.arange(start - 1000.0, start + 1.0), [end + 1000.0]))
            with h5py.File(path, "w") as handle:
                time = handle.create_dataset("mjd", data=time_values)
                time.attrs["DIMENSION_LABELS"] = ["time"]
                time.attrs["units"] = "MJD"
                values = np.ones((time_values.size, 12))
                values[::7, :] = 0.0
                state = handle.create_dataset("nominal_sensitivity", data=values)
                state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                state.attrs["time_axis"] = "mjd"
                state.attrs["spatial_scheme"] = "HEALPIX"
                state.attrs["NSIDE"] = 1
                state.attrs["ORDERING"] = "RING"
                state.attrs["COORDSYS"] = "ICRS"
            result = inspect_exposure(path)
            self.assertFalse(result["has_valid_time_axis"])
            self.assertFalse(result["passes_window_gate"])

    def test_static_spatial_mask_is_not_temporal_outage_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            with h5py.File(path, "w") as handle:
                time_values = self.survey_axis()
                time = handle.create_dataset("mjd", data=time_values)
                time.attrs["DIMENSION_LABELS"] = ["time"]
                time.attrs["units"] = "MJD"
                static_mask = np.ones((time_values.size, 12))
                static_mask[:, 0] = 0.0
                state = handle.create_dataset(
                    "nominal_sensitivity", data=static_mask, chunks=(64, 12)
                )
                state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                state.attrs["time_axis"] = "mjd"
                state.attrs["spatial_scheme"] = "HEALPIX"
                state.attrs["NSIDE"] = 1
                state.attrs["ORDERING"] = "RING"
                state.attrs["COORDSYS"] = "ICRS"
            result = inspect_exposure(path)
            self.assertFalse(result["has_aligned_operational_series"])
            self.assertFalse(result["passes_window_gate"])

    def test_axis_missing_both_survey_boundary_days_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.h5"
            time_values = self.survey_axis()[1:-1]
            with h5py.File(path, "w") as handle:
                time = handle.create_dataset("mjd", data=time_values)
                time.attrs["DIMENSION_LABELS"] = ["time"]
                time.attrs["units"] = "MJD"
                values = np.ones((time_values.size, 12))
                values[::7, :] = 0.0
                state = handle.create_dataset("nominal_sensitivity", data=values)
                state.attrs["DIMENSION_LABELS"] = ["time", "healpix_pixel"]
                state.attrs["time_axis"] = "mjd"
                state.attrs["spatial_scheme"] = "HEALPIX"
                state.attrs["NSIDE"] = 1
                state.attrs["ORDERING"] = "RING"
                state.attrs["COORDSYS"] = "ICRS"
            result = inspect_exposure(path)
            self.assertFalse(result["has_valid_time_axis"])
            self.assertFalse(result["passes_window_gate"])


if __name__ == "__main__":
    unittest.main()
