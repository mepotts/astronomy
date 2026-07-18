"""Ingest ZTF transient alerts from the Lasair ZTF REST API. STUB (M1).

Endpoint:  https://lasair-ztf.lsst.ac.uk/api   (token auth; free 10 calls/hr)
Docs/auth/limits: DATA-SOURCES.md S1.

M1 implementation sketch:

    import os
    from lasair import lasair_client
    L = lasair_client(os.environ["LASAIR_TOKEN"],
                      endpoint="https://lasair-ztf.lsst.ac.uk/api")
    rows = L.query(selected="objects.objectId, objects.ramean, objects.decmean, "
                            "objects.gmag, objects.maxtai",
                   tables="objects",
                   conditions="objects.maxtai > %f" % since_mjd,
                   limit=10000)
    # ...normalize each row -> models.Alert, handle limit/offset pagination...
"""

from __future__ import annotations

from collections.abc import Iterable

from ..models import Alert


def fetch_recent_alerts(since_mjd: float, token: str | None) -> Iterable[Alert]:
    raise NotImplementedError(
        "Live Lasair ZTF ingest is blocked on credentials + network and is NOT part of the "
        "offline M1 core. It requires a Lasair API token (set the LASAIR_TOKEN env var; "
        "register at https://lasair-ztf.lsst.ac.uk to obtain one) and network access to the "
        "Lasair REST API. Use pipeline.synthetic_alerts() / `seti-broker run` for the offline "
        "path. See DATA-SOURCES.md S1."
    )
