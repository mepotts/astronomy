"""Pure physics for target triage: how big a wobble, and can we measure it?

Nothing here touches the network or the filesystem, so it is all directly testable --
and the CD-35 2722 B detection itself is the test fixture. If ``rv_semi_amplitude`` does
not reproduce the published system, the ranking built on top of it is worthless.

The counter-intuitive result that shapes this whole project lives in this module:
K scales as M_host^(-2/3), so a *lighter* host gives a *larger* wobble for the same
satellite. Substellar hosts are not a compromise target for satellite RV -- they are the
favourable one.
"""

from __future__ import annotations

import math

MJUP_PER_MSUN = 1047.5673
MEARTH_PER_MJUP = 317.828
DAYS_PER_YEAR = 365.25

# Standard RV normalisation: K [m/s] for m=1 M_Jup, M_total=1 M_sun, P=1 yr, e=0.
_K0 = 28.4329


def rv_semi_amplitude(
    m_sat_mjup: float, m_host_mjup: float, period_d: float, ecc: float = 0.0
) -> float:
    """Reflex semi-amplitude induced on the *host* by a satellite, in m/s.

    ``m_sat_mjup`` is m*sin(i): RV never constrains inclination on its own, so every mass
    this project reports is a minimum mass, exactly as the paper's are.
    """
    if not 0.0 <= ecc < 1.0:
        raise ValueError(f"eccentricity must be in [0, 1), got {ecc}")
    m_total_msun = (m_host_mjup + m_sat_mjup) / MJUP_PER_MSUN
    return (
        _K0
        * m_sat_mjup
        * m_total_msun ** (-2.0 / 3.0)
        * (period_d / DAYS_PER_YEAR) ** (-1.0 / 3.0)
        / math.sqrt(1.0 - ecc * ecc)
    )


def min_detectable_msini(
    m_host_mjup: float, period_d: float, rv_precision_ms: float, snr: float = 3.0
) -> float:
    """Smallest satellite m*sin(i) [M_Jup] whose K clears ``snr`` x the per-epoch error.

    Deliberately crude -- a real threshold depends on epoch count and sampling, which M3's
    injection-recovery will measure properly. This is for ranking a target list, not for
    quoting a limit in a paper.
    """
    if rv_precision_ms <= 0:
        raise ValueError("rv_precision_ms must be positive")
    # K is linear in m_sat once m_sat << m_host, but the (M+m)^-2/3 term bends it for
    # massive satellites, so solve rather than divide.
    target_k = snr * rv_precision_ms
    lo, hi = 1e-6, 200.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if rv_semi_amplitude(mid, m_host_mjup, period_d) < target_k:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def photon_limited_precision(h_mag: float, ref_h_mag: float, ref_precision_ms: float) -> float:
    """Scale an achieved RV precision to a different companion brightness.

    Photon-limited: sigma_RV ~ 1/SNR ~ 10^(0.2 * delta_mag) at fixed exposure time, i.e.
    ~1.585x worse per magnitude. Ignores the read-noise and telluric-systematic floors, so
    it is optimistic for the faintest targets -- which is the correct direction for a
    triage cut (it over-admits rather than wrongly excluding).
    """
    return ref_precision_ms * 10.0 ** (0.2 * (h_mag - ref_h_mag))


def hill_radius_au(m_host_mjup: float, m_star_msun: float, sma_au: float) -> float:
    """Hill radius of the companion within its host star's potential."""
    return sma_au * (m_host_mjup / MJUP_PER_MSUN / (3.0 * m_star_msun)) ** (1.0 / 3.0)


def max_stable_sma_au(m_host_mjup: float, m_star_msun: float, sma_au: float) -> float:
    """Outer edge for prograde satellites: ~0.4 R_Hill (Domingos+ 2006)."""
    return 0.4 * hill_radius_au(m_host_mjup, m_star_msun, sma_au)


def harmonic_offset_sigma(
    fundamental_d: float, candidate_d: float, candidate_err_d: float, order: int = 2
) -> float:
    """How many sigma a candidate period sits from a harmonic of a fundamental.

    The M4 question in one function. A single eccentric Keplerian is not sinusoidal, so it
    leaks power into P/2, P/3, ... A second "planet" landing on such a harmonic is the
    classic false positive. Small return value => the candidate is where a harmonic would
    be, and must be shown to be something else.
    """
    if candidate_err_d <= 0:
        raise ValueError("candidate_err_d must be positive")
    return abs(candidate_d - fundamental_d / order) / candidate_err_d
