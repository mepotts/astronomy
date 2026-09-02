"""Bulk MPCORB ingestion (M8): streaming parse and elements-to-state conversion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from itf_linker.attrib.bulk import (
    elements_to_state,
    iter_mpcorb_objects,
    mpcorb_to_orbit,
)
from itf_linker.link.geometry import GM_SUN, propagate_kepler, state_to_elements

ROW = {
    "Principal_desig": "2025 MA1",
    "Other_desigs": ["2025 NB2"],
    "Epoch": 2461200.5,
    "M": 123.456,
    "Peri": 20.0,
    "Node": 30.0,
    "i": 5.0,
    "e": 0.1,
    "a": 2.5,
    "H": 18.5,
    "G": 0.15,
    "U": "6",
    "Num_obs": 26,
    "Num_opps": 1,
    "Arc_length": 30.0,
    "rms": 0.2,
    "Orbit_type": "MBA",
}


def write_gz(tmp_path: Path, objs: list[dict]) -> Path:
    p = tmp_path / "mpcorb.json.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write("\n  " + json.dumps(objs))
    return p


# ----------------------------------------------------------------------------------
# Streaming parse
# ----------------------------------------------------------------------------------

def test_stream_parse_survives_tiny_chunks_and_braces_in_strings(tmp_path: Path) -> None:
    tricky = dict(ROW, Principal_desig='X "with ] and } and , chars')
    objs = [ROW, tricky, dict(ROW, Principal_desig="2025 PZ9")]
    got = list(iter_mpcorb_objects(write_gz(tmp_path, objs), chunk_bytes=5))
    assert [o["Principal_desig"] for o in got] == [
        "2025 MA1", 'X "with ] and } and , chars', "2025 PZ9"
    ]


def test_stream_parse_raises_on_truncation(tmp_path: Path) -> None:
    p = tmp_path / "broken.json.gz"
    text = json.dumps([ROW, ROW])
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write(text[: len(text) - 30])  # cut inside the second object
    with pytest.raises(json.JSONDecodeError):
        list(iter_mpcorb_objects(p, chunk_bytes=64))


# ----------------------------------------------------------------------------------
# Elements -> state
# ----------------------------------------------------------------------------------

def test_elements_roundtrip_a_e() -> None:
    r, v = elements_to_state(2.5, 0.1, 5.0, 30.0, 20.0, 123.456)
    el = state_to_elements(r[None, :], v[None, :])
    assert float(el["a"][0]) == pytest.approx(2.5, rel=1e-12)
    assert float(el["e"][0]) == pytest.approx(0.1, rel=1e-10)


def test_elements_state_period_consistency() -> None:
    """Propagating one full period returns the state -- anomaly conventions check out."""
    r, v = elements_to_state(2.2, 0.25, 12.0, 100.0, 250.0, 77.0)
    period = 2 * np.pi * np.sqrt(2.2**3 / GM_SUN)
    r2, v2, conv = propagate_kepler(r[None, :], v[None, :], np.array([period]))
    assert bool(conv[0])
    assert float(np.linalg.norm(r2[0] - r)) < 1e-8
    assert float(np.linalg.norm(v2[0] - v)) < 1e-10


def test_elements_reject_unbound() -> None:
    with pytest.raises(ValueError, match="not an elliptic orbit"):
        elements_to_state(2.5, 1.02, 5.0, 30.0, 20.0, 10.0)


# ----------------------------------------------------------------------------------
# Row -> AttribOrbit
# ----------------------------------------------------------------------------------

def test_mpcorb_to_orbit_fields() -> None:
    orbit = mpcorb_to_orbit(ROW)
    assert orbit is not None
    assert orbit.primary_desig == "2025 MA1"
    assert orbit.all_desigs == ["2025 MA1", "2025 NB2"]
    assert orbit.epoch_mjd_tt == 61200.0  # JD 2461200.5 (TT) -> MJD
    assert orbit.a_au == pytest.approx(2.5, rel=1e-12)
    assert orbit.u_param == 6
    assert orbit.arc_days == 30.0
    assert orbit.h_mag == 18.5


def test_mpcorb_u_blank_and_letter_are_none() -> None:
    assert mpcorb_to_orbit(dict(ROW, U=""))  # parses
    assert mpcorb_to_orbit(dict(ROW, U="")).u_param is None
    assert mpcorb_to_orbit(dict(ROW, U="E")).u_param is None


def test_mpcorb_arc_years_fallback() -> None:
    row = dict(ROW)
    del row["Arc_length"]
    row["Arc_years"] = 2.0
    assert mpcorb_to_orbit(row).arc_days == pytest.approx(730.5)


def test_mpcorb_missing_elements_is_none() -> None:
    row = dict(ROW)
    del row["a"]
    assert mpcorb_to_orbit(row) is None
