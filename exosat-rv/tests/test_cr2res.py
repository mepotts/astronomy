"""ADP -> cr2res conversion. The reshape that lets viper read public archive data.

The layout detail these tests exist to protect: cr2res writes **scalar columns over N rows**,
not one row holding an N-element array. Getting that backwards produced errors far from the
cause -- "truth value of an array is ambiguous" for observations, "`x` must be 1-dimensional"
for templates -- and cost an afternoon. See M2-RESULTS.
"""

import numpy as np
import pytest
from astropy.io import fits

from exosat_rv.archive.cr2res import DETECTORS, _colname, convert, read_adp, verify_roundtrip

NPIX = 64


def make_adp(tmp_path, orders=(2, 3), dets=(1, 2, 3), npix=NPIX):
    n = len(orders) * len(dets) * npix
    rng = np.random.default_rng(11)
    wave, flux, err, order, detec = [], [], [], [], []
    start = 1469.0
    for o in orders:
        for d in dets:
            seg = start + np.arange(npix) * 5.2e-3
            wave.append(seg)
            flux.append(rng.normal(100, 5, npix))
            err.append(np.full(npix, 5.0))
            order.append(np.full(npix, o))
            detec.append(np.full(npix, d))
            start = seg[-1] + 0.8
    cols = [
        fits.Column(name="WAVE", format=f"{n}D", array=[np.concatenate(wave)]),
        fits.Column(name="FLUX", format=f"{n}D", array=[np.concatenate(flux)]),
        fits.Column(name="ERR", format=f"{n}D", array=[np.concatenate(err)]),
        fits.Column(name="ORDER", format=f"{n}J", array=[np.concatenate(order)]),
        fits.Column(name="DETEC", format=f"{n}J", array=[np.concatenate(detec)]),
    ]
    hdr = fits.Header({"DATE-OBS": "2024-01-03T01:17:40.0", "HIERARCH ESO INS WLEN ID": "H1567"})
    path = tmp_path / "adp.fits"
    fits.HDUList([fits.PrimaryHDU(header=hdr),
                  fits.BinTableHDU.from_columns(cols)]).writeto(path)
    return path


def test_conversion_is_lossless(tmp_path):
    src = make_adp(tmp_path)
    dest = convert(src, tmp_path / "out.fits")
    r = verify_roundtrip(src, dest)
    assert r["segments"] == 6
    assert r["max_abs_diff"] == 0.0


def test_columns_are_scalar_over_rows_not_array_cells(tmp_path):
    """The bug that cost an afternoon, pinned."""
    dest = convert(make_adp(tmp_path), tmp_path / "out.fits")
    with fits.open(dest) as h:
        col = h[1].data[_colname(2, "WL")]
        assert col.ndim == 1, "column must be 1-D; viper indexes it without a row index"
        assert col.shape == (NPIX,)
        assert h[1].data.shape[0] == NPIX


def test_three_detector_extensions_are_written(tmp_path):
    dest = convert(make_adp(tmp_path), tmp_path / "out.fits")
    with fits.open(dest) as h:
        assert [x.name for x in h] == ["PRIMARY", "CHIP1", "CHIP2", "CHIP3"]


def test_last_column_encodes_the_maximum_order(tmp_path):
    """`inst_CRIRES` infers each detector's order range from `columns.names[-1]`, so column
    ordering is load-bearing rather than cosmetic."""
    dest = convert(make_adp(tmp_path, orders=(2, 3, 4)), tmp_path / "out.fits")
    with fits.open(dest) as h:
        for det in DETECTORS:
            assert int(h[det].columns.names[-1].split("_")[0]) == 4


def test_primary_header_is_preserved(tmp_path):
    """viper reads RA/DEC/DATE-OBS/WLEN ID/PRO CATG from the primary header."""
    src = make_adp(tmp_path)
    dest = convert(src, tmp_path / "out.fits")
    with fits.open(dest) as h:
        assert h[0].header["HIERARCH ESO INS WLEN ID"] == "H1567"
        assert h[0].header["DATE-OBS"].startswith("2024-01-03")


def test_column_naming_matches_vipers_key_construction(tmp_path):
    """viper builds the key as `"0" + str(order)`, so single-digit orders are required."""
    assert _colname(5, "WL") == "05_01_WL"
    dest = convert(make_adp(tmp_path), tmp_path / "out.fits")
    with fits.open(dest) as h:
        assert "02_01_SPEC" in h[1].columns.names


def test_roundtrip_detects_corruption(tmp_path):
    src = make_adp(tmp_path)
    dest = convert(src, tmp_path / "out.fits")
    with fits.open(dest, mode="update") as h:
        h[1].data[_colname(2, "SPEC")][0] += 1.0
    assert verify_roundtrip(src, dest)["max_abs_diff"] == pytest.approx(1.0)


def test_read_adp_returns_flat_arrays(tmp_path):
    a = read_adp(make_adp(tmp_path))
    assert a["WAVE"].ndim == 1
    assert a["WAVE"].size == 2 * 3 * NPIX
