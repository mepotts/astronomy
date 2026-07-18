"""Core data records passed between the ingest -> ellipsoid -> export agents.

Plain dataclasses (no heavy deps) so the M0 skeleton stays import-light.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Alert:
    """A normalized transient alert from any feed (Lasair ZTF / ASAS-SN / CHIME)."""

    source_ref: str          # e.g. ZTF objectId, ASAS-SN id, or CHIME IVORN
    survey: str              # "ZTF" | "ASAS-SN" | "CHIME"
    ra_deg: float
    dec_deg: float
    mjd: float               # detection time, Modified Julian Date
    mag_or_dm: float | None = None   # optical magnitude, or DM (pc/cm^3) for FRBs


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
    survey: str = ""
    notes: str = ""

    # Convenience: extra columns the exporter may attach without schema churn.
    extra: dict = field(default_factory=dict)
