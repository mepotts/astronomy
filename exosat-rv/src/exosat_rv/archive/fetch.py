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


def _safe_name(name: str) -> str:
    """ESO product names embed an ISO timestamp -- ``ADP.2025-06-02T12:44:40.787.fits`` --
    and Windows rejects ``:`` in filenames. Map the characters NTFS forbids to ``-`` so the
    archive's identifier stays readable and reversible by eye."""
    for ch in ':*?"<>|':
        name = name.replace(ch, "-")
    return name.strip() or "product.fits"


@dataclass
class ProductDescription:
    """What one downloaded product turned out to contain."""

    path: Path
    n_hdus: int
    hdu_kinds: list[str]
    columns: list[str]
    n_orders: int | None
    n_points: int | None
    n_segments: int | None = None
    """Distinct (order, detector) extractions found. ``None`` if the product is unlabelled."""
    wav_min_nm: float | None = None
    wav_max_nm: float | None = None
    is_order_merged: bool | None = None
    """True if the product looks like a single merged spectrum rather than per-order data.
    ``None`` when it could not be determined -- never guessed."""

    def verdict(self) -> str:
        if self.is_order_merged is None:
            return "UNDETERMINED - inspect by hand"
        if self.is_order_merged:
            return "ORDER-MERGED - viper likely cannot use this; cr2res may be required"
        seg = f", {self.n_segments} (order,detector) segments" if self.n_segments else ""
        return f"PER-ORDER - native wavelength solution preserved{seg}; viable for viper"


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
    if dest is None:
        name = name.parent / _safe_name(name.name)
    name.write_bytes(r.content)
    return name


def describe(path: Path) -> ProductDescription:
    """Open a product and report its structure without interpreting it charitably.

    The decisive evidence is structural, not statistical: CRIRES+ ADP spectra carry
    ``ORDER``, ``DETEC`` and ``XPOS`` columns alongside a single flat ``WAVE`` array. The
    flat array is *concatenated* per-order data, not a resampled merge -- ``XPOS`` runs
    1..2048 within each (order, detector) segment, preserving the native detector pixel.

    An earlier version of this function counted wavelength *columns*, saw one, and declared
    the product order-merged. That was wrong and would have sent the project off to build
    cr2res for no reason. Spacing uniformity is kept as a secondary check for products that
    lack the ORDER/DETEC labelling.
    """
    import numpy as np
    from astropy.io import fits

    with fits.open(path) as hdul:
        kinds = [type(h).__name__ for h in hdul]
        cols: list[str] = []
        n_orders = n_points = None
        wmin = wmax = None
        merged: bool | None = None
        n_segments = None

        for h in hdul:
            if getattr(h, "columns", None) is None:
                continue
            cols = [c.name for c in h.columns]
            data = h.data
            if data is None or len(data) == 0:
                break

            def col(name: str, _data=data, _cols=cols):
                return np.asarray(_data[name][0]).ravel() if name in _cols else None

            wl_name = next((c for c in cols if c.upper() in ("WAVE", "WAVELENGTH", "WL")), None)
            w = col(wl_name) if wl_name else None
            order, detec = col("ORDER"), col("DETEC")

            if w is not None and len(w):
                w = np.asarray(w, dtype=float)
                n_points = int(w.size)
                wmin, wmax = float(np.nanmin(w)), float(np.nanmax(w))

            if order is not None:
                # Definitive: the product labels each point by echelle order.
                segs = set(zip(order.tolist(), detec.tolist())) if detec is not None                     else set(order.tolist())
                n_segments = len(segs)
                n_orders = len(set(order.tolist()))
                merged = False
            elif w is not None and w.size > 2:
                # Fallback: a resampled merge has near-constant step; a native solution
                # does not, and jumps by whole nm between orders.
                dw = np.diff(w)
                merged = bool(np.std(dw) / np.median(dw) < 0.05)
            break

    return ProductDescription(
        path=path, n_hdus=len(kinds), hdu_kinds=kinds, columns=cols,
        n_orders=n_orders, n_points=n_points, n_segments=n_segments,
        wav_min_nm=wmin, wav_max_nm=wmax, is_order_merged=merged,
    )
