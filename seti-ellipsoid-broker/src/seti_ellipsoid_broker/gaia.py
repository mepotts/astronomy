"""Gaia DR3 distance layer: batched astroquery.gaia TAP crossmatch. STUB (M1).

This is the differentiator — the broker carries its own Gaia distances instead of relying
on a broker's (distance-poor) alert schema. Anonymous TAP is fine for DR3 gaia_source.
Endpoint/limits/columns/cuts: DATA-SOURCES.md S2.

M1 implementation sketch (one ADQL upload-join over the night's alert positions):

    from astroquery.gaia import Gaia
    Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
    Gaia.ROW_LIMIT = -1
    job = Gaia.launch_job_async(adql, upload_resource=alerts_votable,
                                upload_table_name="alerts")
    table = job.get_results()
    # -> attach parallax, parallax_over_error, ruwe, pmra/pmdec to each Alert
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .models import Alert, RankedTarget


def crossmatch(alerts: Sequence[Alert], radius_arcsec: float = 5.0) -> Iterable[RankedTarget]:
    raise NotImplementedError(
        "Live Gaia DR3 TAP crossmatch is blocked on network access and is NOT part of the "
        "offline M1 core (it pairs with the live Lasair ingest, which needs LASAIR_TOKEN). "
        "For the offline path, pipeline.synthetic_gaia_fields() provides deterministic "
        "stand-in astrometry. See DATA-SOURCES.md S2 for the real ADQL upload-join."
    )
