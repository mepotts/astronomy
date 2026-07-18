"""Core data records passed between the ingest -> ellipsoid -> export agents.

Plain dataclasses (no heavy deps) so the M0 skeleton stays import-light.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Alert:
    """A normalized transient alert from any feed (Lasair ZTF / ASAS-SN / CHIME)."""

    source_ref: str          # e.g. ZTF objectId, ASAS-SN id, or CHIME IVORN
    survey: str              # "ZTF" | "ASAS-SN" | "CHIME" | "CSV" | ...
    ra_deg: float
    dec_deg: float
    mjd: float               # detection time, Modified Julian Date
    mag_or_dm: float | None = None   # optical magnitude, or DM (pc/cm^3) for FRBs
    # Optional pre-resolved Gaia DR3 source id (e.g. supplied in a --transients-csv row).
    # When present the Gaia leg joins by id instead of cone-matching on (ra, dec).
    gaia_source_id: int | None = None


@dataclass(slots=True)
class RankedTarget:
    """An alert enriched with Gaia DR3 astrometry and an ellipsoid crossing verdict."""

    source_ref: str
    gaia_source_id: int
    ra_deg: float
    dec_deg: float
    distance_pc: float           # geocentric, ~= 1000 / parallax_mas under quality cuts
    parallax_over_error: float
    ruwe: float
    crossing_epoch_jyear: float  # decimal year the star sits on the ellipsoid shell
    crossing_window_yr: float    # +/- uncertainty on the crossing epoch
    density_bin: int             # local stellar-density bin (higher = denser, more interesting)
    score: float                 # ranking score (crossing proximity x density)
    # On-shell "now" flags (computed against the run's now_jyear; see ellipsoid.is_crossing_now):
    crossing_now: bool = False       # |t_cross - now| <= this star's own crossing window
    crossing_flag_2yr: bool = False  # |t_cross - now| <= coarse CROSSING_WINDOW_FLAG_YR band
    survey: str = ""
    notes: str = ""

    # Convenience: extra columns the exporter may attach without schema churn.
    extra: dict = field(default_factory=dict)
