"""Ingest CHIME/FRB VOEvents (real-time FRB RA/Dec/DM). STUB (M2/M3).

Subscribe: comet broker -> chimefrb.physics.mcgill.ca:8099
Requires a free subscription + a STATIC PUBLIC IP (see OPEN QUESTIONS in BUILD-PLAN.md).
Docs/format: DATA-SOURCES.md S4.

M2/M3 implementation sketch (parse a captured VOEvent XML):

    import voeventparse as vp
    with open(path, "rb") as f:
        v = vp.load(f)
    pos = vp.get_event_position(v)            # ra, dec, err
    toa = vp.get_event_time_as_utc(v)
    dm = float(vp.get_grouped_params(v)["..."]["dm"]["value"])
    # ...-> models.Alert(survey="CHIME", mag_or_dm=dm, ...)
"""

from __future__ import annotations

from collections.abc import Iterable

from ..models import Alert


def parse_voevent(path: str) -> Alert:
    raise NotImplementedError("CHIME VOEvent ingest lands in M2/M3 - see DATA-SOURCES.md S4")


def fetch_recent_alerts(since_mjd: float) -> Iterable[Alert]:
    raise NotImplementedError("CHIME ingest lands in M2/M3 - see DATA-SOURCES.md S4")
