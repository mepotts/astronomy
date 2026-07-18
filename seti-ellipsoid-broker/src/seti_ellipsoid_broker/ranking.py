"""Quality cuts and ranking of ellipsoid-crossing candidates.

Provides the real M1 ranking layer plus the mocked rows the CLI's legacy demo path uses.

The pipeline (see `pipeline.build_ranked_targets`) feeds each crossmatched alert through:
  1. `passes_quality_cuts`   - Nilipour/Gallay astrometric gate (RUWE<1.4, p/sigma>5).
  2. `density_bin`           - coarse local-stellar-density bin (1..10), higher = denser field.
  3. `score`                 - crossing-proximity x density (the dossier's ranking rule).

`score` rewards (a) a crossing epoch close to "now" (we are most interested in stars crossing
in the live window, not decades away) and (b) a tight crossing-uncertainty window and (c) a
dense stellar neighbourhood. All deterministic and monotonic so artifacts are reproducible.
"""

from __future__ import annotations

from collections.abc import Sequence

from . import ellipsoid
from .models import RankedTarget

# Reference "now" for crossing-proximity scoring. Kept as a module constant (not
# datetime.now()) so artifacts are byte-for-byte reproducible; callers may override.
DEFAULT_NOW_JYEAR: float = 2026.46  # ~2026-06-15, the project's current epoch

# Proximity falloff: a crossing this many years from "now" loses ~half its proximity weight.
PROXIMITY_HALFLIFE_YR: float = 1.5


def passes_quality_cuts(parallax_over_error: float, ruwe: float) -> bool:
    """Nilipour/Gallay astrometric quality gate (RUWE<1.4 AND parallax_over_error>5)."""
    return (
        parallax_over_error > ellipsoid.PARALLAX_OVER_ERROR_MIN
        and ruwe < ellipsoid.RUWE_MAX
    )


def density_bin(neighbor_count: int) -> int:
    """Map a local stellar-neighbour count to a coarse density bin in 1..10.

    The neighbour count is the number of quality Gaia stars in the same field (the broker
    fills this from the crossmatch; in the offline pipeline it comes from the synthetic
    fixture). Binning is a log-ish ladder so very dense LMC-direction fields score highest.
    Higher bin = denser = more interesting (more potential transmitters in the beam).
    """
    if neighbor_count < 0:
        raise ValueError("neighbor_count must be non-negative")
    # Boundaries (inclusive upper) -> bin. Coarse, deterministic, monotonic.
    ladder = (1, 2, 5, 10, 25, 50, 100, 250, 500)
    for i, edge in enumerate(ladder, start=1):
        if neighbor_count <= edge:
            return i
    return 10


def proximity_weight(crossing_epoch_jyear: float, now_jyear: float = DEFAULT_NOW_JYEAR) -> float:
    """Weight in (0, 1]: 1.0 for a crossing exactly now, decaying for crossings far away.

    Symmetric in |t_cross - now| with a half-life of ``PROXIMITY_HALFLIFE_YR``. A crossing
    that already happened (or is far in the future) is down-weighted, never negative.
    """
    dt = abs(crossing_epoch_jyear - now_jyear)
    return float(0.5 ** (dt / PROXIMITY_HALFLIFE_YR))


def score(
    crossing_window_yr: float,
    density_bin_value: int,
    crossing_epoch_jyear: float | None = None,
    now_jyear: float = DEFAULT_NOW_JYEAR,
) -> float:
    """Ranking score: higher = better target.

    Combines three deterministic, monotonic factors:
      * stellar density (linear in the density bin),
      * crossing proximity to "now" (``proximity_weight``; omitted -> treated as 1.0 so the
        legacy 2-arg call ``score(window, bin)`` still works), and
      * tightness of the crossing-uncertainty window (1 / window).

        score = density_bin * proximity_weight * (1 / max(window, eps))
    """
    window = max(crossing_window_yr, 1e-3)
    prox = 1.0 if crossing_epoch_jyear is None else proximity_weight(
        crossing_epoch_jyear, now_jyear
    )
    return float(density_bin_value) * prox / window


def rank(targets: Sequence[RankedTarget]) -> list[RankedTarget]:
    """Return ``targets`` sorted by descending score (stable; ties keep input order)."""
    return sorted(targets, key=lambda t: t.score, reverse=True)


def mock_reactive_target() -> RankedTarget:
    """A single plausible REACT-mode row, for the M0 skeleton (no network)."""
    return RankedTarget(
        source_ref="ZTF24aabcxyz",
        gaia_source_id=4657701054736643840,  # a real-format LMC-direction Gaia DR3 id
        ra_deg=83.91,
        dec_deg=-69.18,
        distance_pc=812.4,
        parallax_over_error=11.3,
        ruwe=1.07,
        crossing_epoch_jyear=2027.3,
        crossing_window_yr=1.4,
        density_bin=7,
        score=score(1.4, 7),
        survey="ZTF",
        notes="MOCK row (M0 skeleton) - not from live data",
    )


def mock_predicted_crossing() -> RankedTarget:
    """A single plausible PREDICT-mode (Window Predictor) row, for the M0 skeleton."""
    return RankedTarget(
        source_ref="(predicted)",
        gaia_source_id=4657690012345678976,
        ra_deg=84.05,
        dec_deg=-69.41,
        distance_pc=455.9,
        parallax_over_error=23.8,
        ruwe=0.98,
        crossing_epoch_jyear=2026.9,
        crossing_window_yr=0.6,
        density_bin=9,
        score=score(0.6, 9),
        survey="(none - proactive sweep)",
        notes="MOCK forward-calendar crossing (M0 skeleton)",
    )
