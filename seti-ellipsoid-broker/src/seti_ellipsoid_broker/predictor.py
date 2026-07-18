"""Window Predictor (PREDICT mode): proactive forward-crossing calendar. STUB (M3).

The dossier's adjacent angle: instead of waiting for an alert, sweep Gaia DR3 stars near
the SN 1987A line of sight, solve each star's ellipsoid crossing epoch (reusing
ellipsoid.crossing_epoch), and emit a rolling forward calendar + iCal (.ics) feed + a small
ephemeris JSON/CSV API artifact. This is the cleaner publication differentiator.

M3 implementation sketch:
  - ADQL cone/box around (SN1987A_RA_DEG, SN1987A_DEC_DEG) with quality cuts
  - for each star: t_cross = ellipsoid.crossing_epoch(distance_pc, sep_deg)
  - keep those crossing within the next N months; sort by date
  - render ephemeris.csv/json + crossings.ics (extras: `ical`)
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import RankedTarget


def upcoming_crossings(months_ahead: int = 12) -> Iterable[RankedTarget]:
    raise NotImplementedError("Window Predictor lands in M3 - see module docstring")
