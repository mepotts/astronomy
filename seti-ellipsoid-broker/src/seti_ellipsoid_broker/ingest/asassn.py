"""Ingest optical light curves from ASAS-SN Sky Patrol V2 (corroboration). STUB (M2).

Client: pyasassn.client.SkyPatrolClient (no auth). Install: extras `asassn`.
Docs/limits: DATA-SOURCES.md S3.

M2 implementation sketch:

    from pyasassn.client import SkyPatrolClient
    client = SkyPatrolClient()
    lcs = client.cone_search(ra_deg=ra, dec_deg=dec, radius=0.5,
                             catalog="stellar_main", download=True)
    # ...derive a variability flag, attach to the matching Alert as corroboration...
"""

from __future__ import annotations

from collections.abc import Iterable

from ..models import Alert


def fetch_recent_alerts(since_mjd: float) -> Iterable[Alert]:
    raise NotImplementedError("ASAS-SN ingest lands in M2 - see docstring and DATA-SOURCES.md S3")
