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

Caveat that shapes M5: the archive caps companion mass at 30 M_Jup, so CD-35 2722 B
(37 M_Jup) is *not in it*. A target list built from this source alone would exclude the
very object being reproduced. See DATA-SOURCES.md.
"""

DATA = Path(__file__).resolve().parents[2] / "data"

# --- the reproduction target ------------------------------------------------------------


@dataclass(frozen=True)
class Published:
    """Hoy et al. 2026 (arXiv:2607.05193v1) values -- the numbers M3 has to land on.

    PROVENANCE. As of M1 every field is ``[v1]`` (read from the arXiv v1 PDF text, via
    pypdf) or ``[TAP]`` (independently confirmed against a queryable archive). The
    ``[SUMM]`` tier -- values taken from an AI summary of a PDF that would not extract --
    has been **eliminated**, and with it three wrong values that M0 had recorded as fact.
    See M1-RESULTS.md section 1. Do not reintroduce a field without reading the source.

    SCOPE. These are the *preprint* values. The v1 disclaimer states verbatim that "the
    results of the accepted work, specifically **which of the presented satellite models
    is favored** and the exact parameters of those models, have meaningfully changed."
    That is a stronger warning than a parameter shift: the accepted Nature paper may
    prefer a different model entirely. We reproduce v1 because v1's dataset is the one
    that is public.
    """

    # --- host system ---
    star_ra_deg: float = 92.3300338228      # [TAP] SIMBAD
    star_dec_deg: float = -35.82529604851   # [TAP] SIMBAD
    parallax_mas: float = 44.7203           # [TAP] SIMBAD -> 22.36 pc
    star_mass_msun: float = 0.4             # [v1] M-type primary
    bd_mass_mjup: float = 37.0              # [v1]
    bd_h_mag: float = 12.78
    """[lit] MKO H of the companion, Wahhaj et al. 2011 (arXiv:1101.2893), +/- 0.12.
    J = 13.63, K = 12.01. **SPEC previously estimated ~14 and was wrong by 1.2 mag** -- the
    companion is brighter than assumed, which makes the M5 flux argument more favourable,
    not less. That discovery paper also gives 31 +/- 8 M_Jup for the mass, consistent with
    the 37 the RV fit uses."""
    bd_vsini_kms: float = 9.58              # [v1]
    bd_max_prot_days: float = 0.65          # [v1] from vsini; ~260x shorter than the signal

    # The companion's own orbit about the star. Only loosely constrained (2011 imaging
    # discovery, ~5000 yr period), but the high eccentricity is what makes the satellite
    # stability limit as tight as it is -- see `stability_limit_au`.
    bd_projected_sep_arcsec: float = 2.8    # [v1]
    bd_period_yr: float = 5000.0            # [v1] "~5000 years", poorly constrained
    bd_ecc_lower: float = 0.9               # [v1] ">0.9"

    # --- 2-satellite model (the paper's favoured fit) ---
    sat1_msini_mjup: float = 0.743          # [v1] Table 1  +0.005 -0.039
    sat1_period_d: float = 169.45           # [v1] Table 1  +1.1 -1.06
    sat1_period_err_d: float = 1.1          # [v1] upper error
    sat1_amplitude_ms: float = 246.45       # [v1] Table 1  +7.03 -5.02
    sat1_ecc: float = 0.005                 # [v1] Table 1 -- essentially circular
    sat1_sma_au: float = 0.199              # [v1] Table 1  +0.005 -0.004

    sat2_msini_mjup: float = 0.277          # [v1] Table 1  +0.035 -0.042
    sat2_period_d: float = 87.46            # [v1] Table 1  +0.0 -0.63
    sat2_period_err_d: float = 0.63         # [v1] lower error (upper is 0.0)
    sat2_amplitude_ms: float = 113.92       # [v1] Table 1  +14.07 -14.1
    sat2_ecc: float = 0.01                  # [v1] Table 1
    sat2_sma_au: float = 0.129              # [v1] Table 1  +0.003 -0.003

    two_sat_logz: float = -122.654          # [v1] Table 1  +/- 0.952
    two_sat_jitter_ms: float = 16.39        # [v1] Table 1

    # --- eccentric 1-satellite model (the alternative the paper fits AND REJECTS) ---
    # This matters: the "is the second signal just an eccentric single Keplerian?"
    # question is one the paper asked itself, fitted, and answered. See M1-RESULTS.md.
    one_sat_period_d: float = 170.05        # [v1] Table 1
    one_sat_amplitude_ms: float = 283.27    # [v1] Table 1
    one_sat_ecc: float = 0.29               # [v1] Table 1 -- the degeneracy signature
    one_sat_msini_mjup: float = 0.778       # [v1] Table 1
    one_sat_logz: float = -129.295          # [v1] Table 1  +/- 0.920
    one_sat_jitter_ms: float = 24.16        # [v1] Table 1

    # --- model comparison ---
    delta_logz_two_vs_one: float = 6.9
    """[v1] Two satellites over the eccentric single satellite. NOTE: Table 1's own logZ
    values differ by 6.641, not 6.9; the paper quotes 6.9 in the text. Both are recorded
    (`two_sat_logz`, `one_sat_logz`) so the discrepancy stays visible."""

    delta_logz_88_vs_115: float = 2.6
    """[v1] **88-day model over the 115-day model** -- a choice between candidate *periods*
    for the second satellite, NOT evidence that a second satellite exists. M0 recorded this
    the wrong way round; see M1-RESULTS.md section 1.3."""

    alias_periods_d: tuple[float, ...] = (14.0, 70.0, 88.0, 115.0)
    """[v1] The four candidate periods for the second signal. The paper states they "are all
    aliases of each other with our current sampling, due to the two sets of observations
    being almost exactly a year apart", and that new observations avoiding that ~1-year
    spacing are what would break the degeneracy. This -- not harmonic leakage -- is the
    real open question in the data."""

    # --- observing setup ---
    n_epochs_obtained: int = 21             # [v1]
    n_epochs_used: int = 20                 # [v1] one cut for continuum S/N ~5
    baseline: tuple[str, str] = ("2023-10", "2025-01")   # [v1] "fifteen months"
    wav_min_nm: float = 1469.0              # [v1], and [TAP] ObsCore em_min
    wav_max_nm: float = 1780.0              # [v1], and [TAP] ObsCore em_max
    resolving_power: int = 100_000          # [v1]

    rv_err_nodding_ms: float = 31.44
    """[v1] Mean RV error of the paper's FAVOURED method: separate RVs per nodding
    position, then binned. This is what M2 must aim at."""

    rv_err_combined_ms: float = 34.49
    """[v1] Mean RV error from combining the nodding frames into one spectrum first --
    the standard cr2res output, and most likely what ESO's archived calib_level=2 products
    are. Using them therefore costs ~10% precision, which is a quantified penalty rather
    than a blocker. See M1-RESULTS.md section 2."""

    # --- dynamical bounds ---
    roche_limit_rbd: float = 8.4
    """[v1] Maximum Roche limit in units of the companion's radius, at a deliberately
    underestimated density (so a satellite clearing this clears the true limit too)."""

    stability_limit_au: float = 1.07
    """[v1] Prograde coplanar satellite stability limit, Domingos et al. (2006) eq. 5:
    a_E ~ 0.49 R_Hill (1 - 1.0305 e_planet - 0.2738 e_satellite).

    **This is a stability limit, not a Hill radius.** M0 recorded it as a Hill radius, found
    it inconsistent with a circular orbit at the projected separation, and published that as
    a disproof. The disproof was wrong on both counts -- wrong quantity, and wrong orbit
    (the companion has e > 0.9 and a ~ 221 au, not a circular 62.6 au). Retracted in
    M1-RESULTS.md section 1.1."""


PUBLISHED = Published()


@dataclass(frozen=True)
class Gj229B:
    """GJ 229 B (= HD 42581 B), M5's positive control.

    Xuan et al. 2024, "The cool brown dwarf Gliese 229 B is a close binary", Nature
    (doi:10.1038/s41586-024-08064-x, 2024-10-16). Resolved by VLTI/GRAVITY *and* CRIRES+ --
    the same instrument this project uses -- into two brown dwarfs.

    Why it is the control: unlike CD-35 2722 B's satellite, this signal is not in dispute.
    A pipeline that cannot see it is not measuring radial velocities, whatever it prints.
    """

    period_d: float = 12.1                 # [lit]
    sma_au: float = 0.042                  # [lit]
    mass_ba_mjup: float = 38.1             # [lit]
    mass_bb_mjup: float = 34.4             # [lit]
    total_mass_mjup: float = 71.4          # [lit] +/- 0.6, dynamical
    outer_period_yr: float = 250.0         # [lit] Bab about GJ 229 A
    distance_pc: float = 5.8               # [TAP] SIMBAD parallax

    k_ba_ms: float = 18070.0
    """Reflex semi-amplitude of Ba due to Bb, from the masses and period above.

    **Not what a single-template fit measures.** The pair is unresolved and double-lined, so
    the fit tracks a flux-weighted centroid whose amplitude is suppressed because the two
    components move in antiphase. M5 recovered 6165 m/s, which implies L_Bb/L_Ba ~ 0.45 --
    entirely reasonable for 38.1 vs 34.4 M_Jup. The suppression is a feature of the target,
    not a failure of the extraction."""


GJ229B = Gj229B()

SEARCH_RADIUS_DEG = 0.03
"""Cone radius for archive lookups. CD-35 2722 B sits 2.8" from its primary, so anything
wide enough to catch both components is fine; 0.03 deg (108") also catches pointings
logged against the primary's coordinates rather than the companion's."""
