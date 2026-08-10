"""Product structure classification, against synthetic FITS built to match both shapes.

This exists because the first version of `describe` got it backwards: it counted wavelength
*columns*, found one, and reported the real ESO product as order-merged. Acting on that
would have sent the project off to rebuild cr2res for 20 nights it did not need to.
"""

import numpy as np
import pytest
from astropy.io import fits

from exosat_rv.archive.fetch import _safe_name, describe


def _write(tmp_path, cols, name="p.fits"):
    hdu = fits.BinTableHDU.from_columns(cols)
    path = tmp_path / name
    fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(path)
    return path


def _crires_like(n_orders=7, n_det=3, npix=2048):
    """A CRIRES+ ADP spectrum: one flat array, labelled by ORDER/DETEC/XPOS."""
    wave, order, detec, xpos = [], [], [], []
    start = 1469.0
    for o in range(2, 2 + n_orders):
        for d in range(1, 1 + n_det):
            # Curved (quadratic) solution per segment, as a real dispersion is.
            px = np.arange(npix)
            seg = start + 5.2e-3 * px + 4e-8 * px**2
            wave.append(seg)
            order.append(np.full(npix, o))
            detec.append(np.full(npix, d))
            xpos.append(px + 1)
            start = seg[-1] + 0.8  # inter-segment gap
    return [np.concatenate(a) for a in (wave, order, detec, xpos)]


def test_crires_like_product_is_classified_per_order(tmp_path):
    w, o, d, x = _crires_like()
    n = w.size
    path = _write(tmp_path, [
        fits.Column(name="WAVE", format=f"{n}D", array=[w]),
        fits.Column(name="FLUX", format=f"{n}D", array=[np.ones(n)]),
        fits.Column(name="ORDER", format=f"{n}J", array=[o]),
        fits.Column(name="DETEC", format=f"{n}J", array=[d]),
        fits.Column(name="XPOS", format=f"{n}J", array=[x]),
    ])
    desc = describe(path)
    assert desc.is_order_merged is False
    assert desc.n_orders == 7
    assert desc.n_segments == 21
    assert desc.n_points == 21 * 2048
    assert "PER-ORDER" in desc.verdict()
    assert "21" in desc.verdict()


def test_resampled_merge_is_classified_merged(tmp_path):
    """No ORDER column and a constant step -- the shape that would defeat viper."""
    w = np.linspace(1469.0, 1780.0, 40000)
    path = _write(tmp_path, [
        fits.Column(name="WAVE", format=f"{w.size}D", array=[w]),
        fits.Column(name="FLUX", format=f"{w.size}D", array=[np.ones(w.size)]),
    ])
    desc = describe(path)
    assert desc.is_order_merged is True
    assert desc.n_segments is None
    assert "ORDER-MERGED" in desc.verdict()


def test_unlabelled_but_non_uniform_is_not_called_merged(tmp_path):
    """Concatenated orders without ORDER labels: irregular step, so not a resampled merge."""
    w, _, _, _ = _crires_like()
    path = _write(tmp_path, [
        fits.Column(name="WAVE", format=f"{w.size}D", array=[w]),
        fits.Column(name="FLUX", format=f"{w.size}D", array=[np.ones(w.size)]),
    ])
    assert describe(path).is_order_merged is False


def test_verdict_never_guesses_when_undetermined(tmp_path):
    path = _write(tmp_path, [fits.Column(name="JUNK", format="1J", array=[[0]])])
    desc = describe(path)
    assert desc.is_order_merged is None
    assert "UNDETERMINED" in desc.verdict()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ADP.2025-06-02T12:44:40.787.fits", "ADP.2025-06-02T12-44-40.787.fits"),
        ("a<b>c|d?e*f.fits", "a-b-c-d-e-f.fits"),
        ("   ", "product.fits"),
    ],
)
def test_windows_illegal_characters_are_mapped(raw, expected):
    """ESO product names embed an ISO timestamp; NTFS rejects the colons."""
    assert _safe_name(raw) == expected
