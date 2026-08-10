"""Endpoints, constants, and the published values this project is checking itself against.

No credentials anywhere: every endpoint here is anonymous-access.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --- endpoints -------------------------------------------------------------------------

ESO_TAP = "https://archive.eso.org/tap_obs"
"""ESO archive TAP. Two tables matter:

``dbo.raw``      one row per raw frame (what was *observed*).
``ivoa.ObsCore`` one row per product, ``calib_level=2`` being pipeline-reduced spectra
                 (what we can actually *use* without running esorex ourselves).

The two disagree -- M0 measures by how much. Raw frames exist for nights that have no
reduced product, and those nights are the ones that would need the cr2res pipeline.
"""

NEA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP"
"""NASA Exoplanet Archive. ``pscomppars`` with ``discoverymethod='Imaging'``.

Caveat that shapes M1: the archive caps companion mass at 30 M_Jup, so CD-35 2722 B
(~31-37 M_Jup) is *not in it*. A target list built from this source alone would exclude
the very object being reproduced. See DATA-SOURCES.md.
"""

DATA = Path(__file__).resolve().parents[2] / "data"

# --- the reproduction target ------------------------------------------------------------


@dataclass(frozen=True)
class Published:
    """Hoy et al. 2026 (arXiv:2607.05193v1) values -- the numbers M3 has to land on.

    These are the *preprint* values. arXiv's own comment states results changed
    meaningfully in the accepted Nature version; press coverage of the accepted paper
    quotes ~0.9 M_Jup and 23 epochs to Feb 2026. We reproduce v1 because v1's dataset is
    the one that is public. Any comparison to the Nature numbers is apples-to-oranges
    until the Dec-2025-onward frames leave their proprietary period.

    PROVENANCE -- read before trusting any field here.

    ``[TAP]``  independently confirmed against a queryable archive by this project.
    ``[v1]``   transcribed from the arXiv v1 abstract, which was read directly.
    ``[SUMM]`` taken from an AI summary of the paper body, **not** verified against the
               source text. Treat as a hint, never as ground truth, and never assert a
               test against one.

    M0 already caught one ``[SUMM]`` value that cannot be right: a Hill radius of 1.07 au
    implies the companion orbits at 3.7 au, but it is directly imaged at 2.8" = 62.6 au,
    where the Hill radius is ~18 au. See M0-RESULTS.md. Every remaining ``[SUMM]`` field
    is suspect until someone reads the actual PDF.
    """

    # host system
    star_ra_deg: float = 92.3300338228   # [TAP] SIMBAD
    star_dec_deg: float = -35.82529604851  # [TAP] SIMBAD
    parallax_mas: float = 44.7203        # [TAP] SIMBAD -> 22.36 pc
    bd_mass_mjup: float = 37.0           # [SUMM]
    bd_vsini_kms: float = 9.58           # [SUMM]
    bd_max_prot_days: float = 0.65       # [SUMM] from vsini; 260x shorter than the signal

    # satellite candidate 1 -- the strong detection
    sat1_msini_mjup: float = 0.743       # [v1]
    sat1_period_d: float = 169.45        # [v1]
    sat1_period_err_d: float = 1.1       # [SUMM]
    sat1_sma_au: float = 0.199           # [SUMM]

    # satellite candidate 2 -- the marginal one M4 exists to interrogate
    sat2_msini_mjup: float = 0.277       # [v1]
    sat2_period_d: float = 87.46         # [v1]
    sat2_period_err_d: float = 0.63      # [SUMM]
    sat2_sma_au: float = 0.129           # [SUMM]
    sat2_delta_logz: float = 2.6         # Bayes factor ~14: "positive", not decisive

    # observing setup
    n_epochs: int = 20                   # [SUMM], corroborated by [TAP] night count
    baseline: tuple[str, str] = ("2023-10", "2025-01")
    wav_min_nm: float = 1469.0           # [TAP] ObsCore em_min
    wav_max_nm: float = 1780.0           # [TAP] ObsCore em_max
    resolving_power: int = 100_000       # [SUMM]
    rv_err_min_ms: float = 18.0
    rv_err_max_ms: float = 54.0
    rv_err_mean_ms: float = 30.0         # [SUMM]

    # Stability bounds. Both [SUMM]; hill_radius_au is DISPROVEN by M0 -- retained only
    # so the contradiction stays visible instead of being silently dropped. Do not use it.
    roche_limit_rbd: float = 8.4         # [SUMM]
    hill_radius_au: float = 1.07         # [SUMM] INCONSISTENT -- see M0-RESULTS.md


PUBLISHED = Published()

SEARCH_RADIUS_DEG = 0.03
"""Cone radius for archive lookups. CD-35 2722 B sits 2.8" from its primary, so anything
wide enough to catch both components is fine; 0.03 deg (108") also catches pointings
logged against the primary's coordinates rather than the companion's."""
