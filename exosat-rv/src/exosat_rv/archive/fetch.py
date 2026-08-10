"""Retrieve ESO reduced products and describe what is actually inside them.

The M1 kill-check lives here: ESO's ``calib_level=2`` CRIRES+ products are what let this
project skip the raw reduction, but only if they preserve what a forward-modelling RV code
needs -- per-order extracted spectra with their wavelength solution intact. If they are
order-merged and resampled onto a common grid, `viper` cannot use them.

Known before writing this, from the preprint (M1-RESULTS section 2): the authors did *not*
use the standard combined output. They ran cr2res but kept the individual nodding frames as
separate observations, which bought them 31.44 m/s mean error against 34.49 m/s for the
combined spectrum. ESO's archived product is the combined one, so working from it costs
~10% precision by construction. That is a quantified penalty, not a blocker -- but it means
"reproduces the paper" has an expected offset baked in, and M3 must not read that offset as
a disagreement.

Nothing here has been exercised against a live URL: ``archive.eso.org`` was unreachable for
the whole of the M1 attempt (connect timeout; ``www.eso.org`` and other TAP services were
fine). Treat the datalink branch as untested.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests

from ..config import DATA

SPECTRA = DATA / "spectra"
TIMEOUT = 60


@dataclass
class ProductDescription:
    """What one downloaded product turned out to contain."""

    path: Path
    n_hdus: int
    hdu_kinds: list[str]
    columns: list[str]
    n_orders: int | None
    n_points: int | None
    wav_min_nm: float | None
    wav_max_nm: float | None
    is_order_merged: bool | None
    """True if the product looks like a single merged spectrum rather than per-order data.
    ``None`` when it could not be determined -- never guessed."""

    def verdict(self) -> str:
        if self.is_order_merged is None:
            return "UNDETERMINED - inspect by hand"
        if self.is_order_merged:
            return "ORDER-MERGED - viper likely cannot use this; cr2res may be required"
        return "PER-ORDER - wavelength solution preserved; viable for viper"


def download(access_url: str, dest: Path | None = None) -> Path:
    """Fetch one product. Follows a datalink document to its first FITS link if needed."""
    SPECTRA.mkdir(parents=True, exist_ok=True)
    r = requests.get(access_url, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()

    ctype = r.headers.get("Content-Type", "")
    if "xml" in ctype or r.content[:5] == b"<?xml":
        # Datalink document: pull the first #this / application/fits access URL out of it.
        import xml.etree.ElementTree as ET

        root = ET.fromstring(r.content)
        urls = [
            td.text
            for td in root.iter()
            if td.tag.endswith("TD") and td.text and td.text.startswith("http")
        ]
        if not urls:
            raise RuntimeError(f"datalink document held no retrievable URL: {access_url}")
        return download(urls[0], dest)

    name = dest or SPECTRA / (
        r.headers.get("Content-Disposition", "").partition("filename=")[2].strip('"; ')
        or access_url.rstrip("/").rsplit("/", 1)[-1]
        or "product.fits"
    )
    name = Path(name)
    name.write_bytes(r.content)
    return name


def describe(path: Path) -> ProductDescription:
    """Open a product and report its structure without interpreting it charitably."""
    from astropy.io import fits

    with fits.open(path) as hdul:
        kinds = [type(h).__name__ for h in hdul]
        cols: list[str] = []
        n_orders = n_points = None
        wmin = wmax = None
        merged: bool | None = None

        for h in hdul:
            if getattr(h, "columns", None) is not None:
                cols = [c.name for c in h.columns]
                data = h.data
                if data is not None and len(data) > 0:
                    # CRIRES+ per-order products name columns like "0300_01_WL"/"SPEC";
                    # a merged product typically carries a single WAVE/FLUX pair.
                    wl_cols = [c for c in cols if "WL" in c.upper() or "WAVE" in c.upper()]
                    n_orders = len(wl_cols) or None
                    merged = len(wl_cols) <= 1 if wl_cols else None
                    try:
                        w = data[wl_cols[0]]
                        w = w[0] if getattr(w, "ndim", 1) > 1 else w
                        n_points = len(w)
                        wmin, wmax = float(min(w)), float(max(w))
                    except (IndexError, KeyError, TypeError, ValueError):
                        pass
                break

    return ProductDescription(
        path=path, n_hdus=len(kinds), hdu_kinds=kinds, columns=cols,
        n_orders=n_orders, n_points=n_points,
        wav_min_nm=wmin, wav_max_nm=wmax, is_order_merged=merged,
    )
