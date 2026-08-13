"""Convert an ESO CRIRES+ ADP product into the cr2res-native layout `viper` expects.

`viper` reads the *pipeline's* output, not the archive's. Its `inst_CRIRES.Spectrum` wants
three BinTable extensions -- one per detector -- with columns named ``0<order>_01_SPEC``,
``0<order>_01_ERR`` and ``0<order>_01_WL`` (wavelength in nm; viper multiplies by 10 to get
Angstrom). ESO's archived ADP product carries exactly the same numbers in one flat table
keyed by ``ORDER``/``DETEC``/``XPOS``.

So the two formats are a reshape apart, and this module does the reshape. That is what lets
the reproduction run on public archive data rather than on the authors' intermediate files
-- the difference between a reproduction anyone can repeat and one that needs their disk.

**Nothing is resampled, interpolated or rescaled.** Values are copied verbatim into the new
layout; only the arrangement changes. `verify_roundtrip` asserts that.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

DETECTORS = (1, 2, 3)
TRACE = "01"


def _colname(order: int, kind: str) -> str:
    """cr2res column naming. viper builds the key as ``"0" + str(order)``, so orders must
    stay single-digit (CRIRES+ H-band uses 2-8) for the lookup to line up."""
    return f"0{order}_{TRACE}_{kind}"


def read_adp(path: Path) -> dict:
    """Pull the flat arrays and the primary header out of an ADP spectrum."""
    with fits.open(path) as hdul:
        hdr = hdul[0].header.copy()
        d = hdul[1].data
        out = {k: np.asarray(d[k][0]).ravel() for k in ("WAVE", "FLUX", "ERR", "ORDER", "DETEC")}
    out["header"] = hdr
    return out


def convert(src: Path, dest: Path) -> Path:
    """Write the cr2res-layout equivalent of ``src`` to ``dest``.

    Orders are written in ascending numeric order because `inst_CRIRES` infers the maximum
    order from ``columns.names[-1]`` -- the *last* column decides the detector's order range,
    so column order is load-bearing, not cosmetic.
    """
    a = read_adp(src)
    order, detec = a["ORDER"].astype(int), a["DETEC"].astype(int)

    hdus: list[fits.hdu.base.ExtensionHDU] = [fits.PrimaryHDU(header=a["header"])]
    for det in DETECTORS:
        cols = []
        for o in sorted(set(order[detec == det].tolist())):
            m = (order == o) & (detec == det)
            # SCALAR columns over `n` rows -- NOT one row holding an n-element array.
            # cr2res writes 2048 rows per detector and `inst_CRIRES` indexes the column
            # directly (`hdu[det].data["05_01_WL"]`) with no row index, so an array-cell
            # layout hands it a (1, n) 2-D array. That surfaces far downstream as
            # "truth value of an array is ambiguous" in the observation and
            # "`x` must be 1-dimensional" in the template -- neither of which names the
            # real cause. Getting this wrong cost an afternoon.
            cols += [
                fits.Column(name=_colname(o, "SPEC"), format="D", array=a["FLUX"][m]),
                fits.Column(name=_colname(o, "ERR"), format="D", array=a["ERR"][m]),
                fits.Column(name=_colname(o, "WL"), format="D", array=a["WAVE"][m]),
            ]
        hdu = fits.BinTableHDU.from_columns(cols, name=f"CHIP{det}")
        hdus.append(hdu)

    dest.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList(hdus).writeto(dest, overwrite=True)
    return dest


def verify_roundtrip(src: Path, dest: Path) -> dict:
    """Check the conversion moved every number without altering one.

    Returns per-segment counts and the largest absolute difference found, so a caller can
    assert on it rather than trust the writer.
    """
    a = read_adp(src)
    order, detec = a["ORDER"].astype(int), a["DETEC"].astype(int)
    worst = 0.0
    segments = 0
    with fits.open(dest) as hdul:
        for det in DETECTORS:
            data = hdul[det].data
            for o in sorted(set(order[detec == det].tolist())):
                m = (order == o) & (detec == det)
                for kind, key in (("SPEC", "FLUX"), ("ERR", "ERR"), ("WL", "WAVE")):
                    got = np.asarray(data[_colname(o, kind)]).ravel()
                    ref = a[key][m]
                    if got.size != ref.size:
                        raise ValueError(f"size mismatch det{det} order{o} {kind}")
                    diff = np.nanmax(np.abs(got - ref)) if got.size else 0.0
                    worst = max(worst, float(diff))
                segments += 1
    return {"segments": segments, "max_abs_diff": worst}
