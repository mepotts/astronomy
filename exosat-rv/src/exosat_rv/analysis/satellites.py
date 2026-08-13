"""Where else the Hoy et al. method can work, and where it provably cannot.

Two questions live here, and they share their physics.

**M7 -- generalising the method.** Hoy et al. detected a satellite by pointing a
spectrograph at a *directly imaged companion* and measuring its reflex wobble. Whether
that works on any other target is a four-way conjunction, and the project had been
tracking only the first two:

1. the wobble is big enough (``rv_semi_amplitude``, already in ``targets.feasibility``);
2. the companion is bright enough to measure it (``lazzoni_threshold_ms``);
3. the satellite orbit is *dynamically allowed* (Roche limit < a < Domingos limit);
4. the satellite orbit is *survivable* -- it has not spiralled into the host (this module).

Condition 4 is new here and it is the one that decides the close-in case entirely.

**M8 -- close-in giants ("hot Jupiters").** The same arithmetic run at small star-planet
separation. The signal is enormous -- an Earth-mass moon on a close orbit around a
1 M_Jup planet gives K ~ 70 m/s, comparable to what Hoy et al. actually measured -- but
the *host planet's spin* decides whether such a moon can still be there.

The mechanism, and it is the whole result:

- A satellite outside the planet's **corotation radius** raises a tidal bulge that leads
  the satellite, and torque pushes it *outward* (our Moon).
- A satellite inside corotation is overtaken by the bulge, torque pushes it *inward*, and
  it is destroyed (Mars's Phobos).
- A close-in giant is tidally spun down by its star until it rotates synchronously with
  its *orbit*. That pushes corotation out to several times the Hill-stability limit, so
  **every dynamically stable satellite ends up inside corotation** and inspirals.

Hence the survival window is open only while the planet still spins fast, and
``tidal_spin_down_yr`` says how long that is. It scales as a^6, which is why the answer
flips completely over a factor of ~3 in orbital distance.

Sign convention throughout: distances in au unless a name says ``_rjup``, times in years,
masses in M_Jup for planets/companions and M_sun for stars, as elsewhere in this package.

Sources, all read into ``papers/``:

- Lazzoni et al. 2022, MNRAS 516, 391 (arXiv:2207.07569) -- the detectability framework,
  reference [11] of Hoy et al. Its eq. 2 is ``rv_semi_amplitude`` in another form, and its
  section 3.2 is ``lazzoni_threshold_ms``.
- Vanderburg, Rappaport & Mayo 2018, AJ 156, 184 (arXiv:1805.01903) -- proposed the method;
  its section 2.4 is ``activity_confusion``.
- Ruffio et al. 2023, AJ 165, 113 (arXiv:2301.04206) -- the achieved sensitivity on
  HR 7672 B, and the ~13 M_Jup brightness cliff.
- Domingos, Winter & Yokoyama 2006, MNRAS 373, 1227 -- the stability limit.
- Barnes & O'Brien 2002, ApJ 575, 1087; Cassidy et al. 2009; Oza et al. 2019
  (arXiv:1908.10732) -- satellite survival around close-in giants.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..targets.feasibility import (
    MEARTH_PER_MJUP,
    MJUP_PER_MSUN,
    domingos_stability_limit_au,
)

G = 6.674e-11
M_JUP_KG = 1.898e27
M_SUN_KG = 1.98892e30
M_EARTH_KG = 5.972e24
R_JUP_M = 7.1492e7
AU_M = 1.495978707e11
SEC_PER_YR = 3.15576e7
SEC_PER_DAY = 86400.0

RHO_JUP_CGS = 1.24
"""1 M_Jup inside 1 R_Jup, g/cm^3.

**Not Jupiter's quoted 1.326.** ``R_JUP_M`` is the equatorial radius (71,492 km), which is
the conventional unit; the 1.326 figure is computed from the volumetric mean radius
(69,911 km). Mixing them is a 7% density error that enters the Roche limit as its cube
root. Kept as a named constant only so the distinction is written down -- densities are
computed from mass and radius, never defaulted."""


# --------------------------------------------------------------------------------------
# 2. Can we measure it?  (Lazzoni's flux-scaled threshold, recalibrated on the detection)
# --------------------------------------------------------------------------------------


def lazzoni_threshold_ms(k_mag: float) -> float:
    """Smallest detectable RV semi-amplitude [m/s] for a companion of magnitude ``k_mag``.

    Lazzoni et al. 2022 section 4.3.2 verbatim: ``0.1 * 10^(0.2 (K_p - 13.5)) km/s``.
    That is 100 m/s at K = 13.5, worsening 10^0.2 = 1.585x per magnitude -- the photon
    scaling already used by ``targets.feasibility.photon_limited_precision``, but anchored
    to a published absolute value rather than to this project's own measurements.

    They flag it as "quite optimistic for actual instrumentation, [but] quite realistic
    for HiRISE", and note it degrades faster than this below K ~ 15 where background
    noise takes over. Treat it as a floor, not a forecast.
    """
    return 100.0 * 10.0 ** (0.2 * (k_mag - 13.5))


def hoy_calibrated_threshold_ms(k_mag: float, snr: float = 3.0) -> float:
    """The same scaling, anchored on the one measurement that actually exists.

    Hoy et al. reached a mean per-epoch error of **31.44 m/s** on CD-35 2722 B, whose
    MKO K magnitude is **12.01** (Wahhaj et al. 2011). Lazzoni's curve predicts 50.3 m/s
    there, so the real instrument beat the published forecast by 1.6x.

    This matters for target selection in the honest direction: anchoring on the forecast
    would *under*-admit targets. Anchoring on the achievement is defensible because it is
    the same instrument, the same band and the same code that any follow-up would use.

    Returns ``snr`` x the per-epoch error, i.e. the amplitude a single epoch resolves.
    A real campaign gains roughly sqrt(N_epochs) on top, which is deliberately not
    included -- see ``M4-RESULTS`` for what sampling does to that naive expectation.
    """
    return snr * 31.44 * 10.0 ** (0.2 * (k_mag - 12.01))


DEUTERIUM_CLIFF_MJUP = 13.0
"""Below ~13 M_Jup a young companion has never burned deuterium and is far fainter, so RV
precision collapses (Ruffio et al. 2023 section 4). Above it, and around 30 Myr, precision
is nearly independent of mass because heavier brown dwarfs cool faster and the cooling
tracks converge. A mass cut is therefore a *brightness* cut in disguise."""


# --------------------------------------------------------------------------------------
# 3. Is the orbit dynamically allowed?
# --------------------------------------------------------------------------------------


def mean_density_cgs(m_mjup: float, r_rjup: float) -> float:
    """Mean density in g/cm^3 from mass and radius.

    Substellar objects are nearly the same *size* over two decades of mass -- electron
    degeneracy pins the radius near 1 R_Jup from ~1 M_Jup to the hydrogen-burning limit --
    so density runs from Jupiter's 1.3 g/cm^3 to well over 100. Defaulting it to Jupiter's
    value understates the Roche limit of a brown dwarf by a factor of ~3.
    """
    m, r = m_mjup * M_JUP_KG, r_rjup * R_JUP_M
    return m / (4.0 / 3.0 * math.pi * r**3) / 1000.0


def roche_limit_au(
    m_host_mjup: float, r_host_rjup: float, rho_sat_cgs: float = 3.0
) -> float:
    """Fluid Roche limit, ``2.456 R_host (rho_host/rho_sat)^(1/3)``.

    Host density is computed from mass and radius rather than passed, because getting it
    wrong is silent: the formula happily returns a plausible number for any density.

    Default satellite density 3.0 g/cm^3 (rocky). Hoy et al. deliberately used *Saturn's*
    0.687 g/cm^3 -- an underestimate -- so that a satellite clearing their limit clears
    the true one too. Pass ``rho_sat_cgs=0.687`` with (37, 1.2) to reproduce their 8.4.
    """
    rho_host = mean_density_cgs(m_host_mjup, r_host_rjup)
    return 2.456 * r_host_rjup * R_JUP_M * (rho_host / rho_sat_cgs) ** (1.0 / 3.0) / AU_M


def satellite_period_d(a_sat_au: float, m_host_mjup: float) -> float:
    """Kepler's third law about the *host companion*, not about the star."""
    a = a_sat_au * AU_M
    return 2.0 * math.pi * math.sqrt(a**3 / (G * m_host_mjup * M_JUP_KG)) / SEC_PER_DAY


def satellite_sma_au(period_d: float, m_host_mjup: float) -> float:
    """Inverse of :func:`satellite_period_d`."""
    n = 2.0 * math.pi / (period_d * SEC_PER_DAY)
    return (G * m_host_mjup * M_JUP_KG / n**2) ** (1.0 / 3.0) / AU_M


# --------------------------------------------------------------------------------------
# 4. Is the orbit survivable?  -- the part that decides the close-in case
# --------------------------------------------------------------------------------------


def corotation_radius_au(m_host_mjup: float, p_spin_d: float) -> float:
    """Radius where a satellite's orbital period equals the host's spin period.

    The sign of every tidal torque flips here. Outside: the satellite migrates outward and
    lives. Inside: it migrates inward and dies. Nothing else in this module matters as much.
    """
    return satellite_sma_au(p_spin_d, m_host_mjup)


def tidal_spin_down_yr(
    m_planet_mjup: float,
    r_planet_rjup: float,
    m_star_msun: float,
    sma_au: float,
    p_spin_d: float,
    q_planet: float = 1e5,
    k2: float = 0.34,
    alpha: float = 0.26,
) -> float:
    """Time for the *star* to despin the planet from ``p_spin_d`` towards synchronous.

    Order-of-magnitude: spin angular momentum ``alpha M R^2 Omega`` divided by the tidal
    torque ``(3/2)(k2/Q) G M_star^2 R^5 / a^6``.

    **The a^6 is the whole story.** Every other parameter here is uncertain by a factor of
    a few; ``a`` moves the answer by six orders of magnitude across the range of interest.
    A 1 M_Jup planet spinning at 10 h despins in ~0.3 Myr at 0.05 au and ~1 Gyr at 0.2 au.
    So "is this planet still spinning fast?" is answered almost entirely by its separation,
    and only weakly by Q -- which is fortunate, because Q is the least known number in
    planetary science (10^5 to 10^7 are all defended in the literature).

    ``alpha = 0.26`` is the moment-of-inertia factor of an n = 1 polytrope, ``k2 = 0.34``
    Jupiter's Love number.
    """
    omega = 2.0 * math.pi / (p_spin_d * SEC_PER_DAY)
    m_p, r_p = m_planet_mjup * M_JUP_KG, r_planet_rjup * R_JUP_M
    torque = 1.5 * (k2 / q_planet) * G * (m_star_msun * M_SUN_KG) ** 2 * r_p**5 / (sma_au * AU_M) ** 6
    return alpha * m_p * r_p**2 * omega / torque / SEC_PER_YR


def moon_inspiral_yr(
    m_sat_mearth: float,
    m_host_mjup: float,
    r_host_rjup: float,
    a_sat_au: float,
    q_planet: float = 1e5,
    k2: float = 0.34,
) -> float:
    """Time for a satellite *inside* corotation to spiral in from ``a_sat_au`` to contact.

    ``da/dt ~ -(9/2)(k2/Q)(m_s/M_p) sqrt(G M_p) R_p^5 a^(-11/2)``, integrated, so the
    time goes as ``a^(13/2)`` and inversely as satellite mass.

    **Massive satellites die fastest.** That is the cruel part of the close-in case: RV
    detects big moons, and big moons are exactly the ones tides remove first. A 10 M_Earth
    moon at 3 R_Jup around a 1 M_Jup planet is gone in a few thousand years.
    """
    a = a_sat_au * AU_M
    m_p, r_p = m_host_mjup * M_JUP_KG, r_host_rjup * R_JUP_M
    c = 4.5 * (k2 / q_planet) * (m_sat_mearth * M_EARTH_KG / m_p) * math.sqrt(G * m_p) * r_p**5
    return (2.0 / 13.0) * a**6.5 / c / SEC_PER_YR


# --------------------------------------------------------------------------------------
# False positives -- Vanderburg et al. 2018 section 2.4
# --------------------------------------------------------------------------------------


def activity_amplitude_ms(vsini_kms: float, spot_filling: float = 0.02) -> float:
    """Spurious RV from inhomogeneities rotating across the host, ``F_spot x v sin i``.

    Vanderburg et al. 2018 eq. 9. Brown dwarfs and giant planets vary by a few per cent
    peak-to-peak with v sin i of 10-25 km/s, giving "up to a few hundred metres per
    second" -- the *same order as the exomoon signal*. Amplitude alone never separates
    them; only timescale does. See :func:`activity_confusion`.
    """
    return spot_filling * vsini_kms * 1000.0


def activity_confusion(p_sat_d: float, p_rot_d: float, n_harmonics: int = 3) -> float:
    """Fractional distance from the nearest rotation harmonic -- 0.0 means coincident.

    Vanderburg et al. 2018: activity and centre-of-mass signals are hardest to separate
    when the orbital period lands within ~10% of the rotation period or its harmonics,
    with the 1st and 2nd harmonics dominating. Returns ``min |P_sat/(P_rot/k) - 1|`` over
    ``k = 1..n_harmonics``; **< 0.1 is the danger zone.**

    This is what saves the wide-companion case and what threatens the close-in one.
    CD-35 2722 B rotates in <= 0.65 d against satellite periods of 87 and 169 d -- a
    ratio of 130, utterly clear. A close-in giant's satellites are confined to periods of
    hours by their tiny Hill sphere, which is the same regime as the planet's spin.
    """
    return min(abs(p_sat_d / (p_rot_d / k) - 1.0) for k in range(1, n_harmonics + 1))


# --------------------------------------------------------------------------------------
# The conjunction
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SurvivalWindow:
    """Range of satellite semi-major axes that are stable, intact, and not inspiralling."""

    a_in_au: float
    a_out_au: float
    roche_au: float
    corotation_au: float
    stability_au: float
    synchronised: bool
    p_spin_d: float
    spin_down_yr: float

    @property
    def is_open(self) -> bool:
        return self.a_out_au > self.a_in_au

    @property
    def decades(self) -> float:
        """Width in dex. Zero or negative means no satellite can survive at all."""
        return math.log10(self.a_out_au / self.a_in_au) if self.is_open else 0.0


def survival_window(
    m_planet_mjup: float,
    r_planet_rjup: float,
    m_star_msun: float,
    sma_au: float,
    age_myr: float,
    p_spin_primordial_d: float = 10.0 / 24.0,
    p_orbit_d: float | None = None,
    ecc_planet: float = 0.0,
    q_planet: float = 1e5,
    rho_sat_cgs: float = 3.0,
) -> SurvivalWindow:
    """Satellite orbits that are simultaneously stable, intact and non-inspiralling.

    The planet's spin state is **derived, not assumed**: if the star has had time to despin
    it (``tidal_spin_down_yr < age_myr``), the planet is taken as synchronous with its
    orbit and corotation moves out accordingly. That single branch is what closes the
    window for classic hot Jupiters and leaves it open for young warm ones.

    ``p_spin_primordial_d`` defaults to 10 hours -- the observed spin of young directly
    imaged giants (beta Pic b, 2M1207 b) and of Jupiter itself.
    """
    p_orb = p_orbit_d if p_orbit_d is not None else 365.25 * math.sqrt(
        sma_au**3 / (m_star_msun + m_planet_mjup / MJUP_PER_MSUN)
    )
    spin_down = tidal_spin_down_yr(
        m_planet_mjup, r_planet_rjup, m_star_msun, sma_au, p_spin_primordial_d, q_planet
    )
    synchronised = spin_down < age_myr * 1e6
    p_spin = p_orb if synchronised else p_spin_primordial_d

    roche = roche_limit_au(m_planet_mjup, r_planet_rjup, rho_sat_cgs)
    corot = corotation_radius_au(m_planet_mjup, p_spin)
    stab = domingos_stability_limit_au(m_planet_mjup, m_star_msun, sma_au, ecc_planet)
    return SurvivalWindow(
        a_in_au=max(roche, corot),
        a_out_au=stab,
        roche_au=roche,
        corotation_au=corot,
        stability_au=stab,
        synchronised=synchronised,
        p_spin_d=p_spin,
        spin_down_yr=spin_down,
    )


TOKADJIAN_SPIN_RATIO = 1.0 / 0.198
"""A moon can hold its planet's spin fast only if ``P_spin < P_orbit / 5.05``.

Tokadjian & Piro 2023 (A&A 672 A5, arXiv:2302.04646) eq. 9: ``n_p < 0.198 theta_dot_p
(1 - 1.03 e_p)^(3/2)``. Below that ratio the moon-synchronised state puts the synchronous
radius inside the reduced Hill radius, and the pair is self-consistent.

**This is the mechanism ``survival_window`` originally missed, and it runs the opposite
way to naive intuition.** Treating the planet's spin as evolving under stellar tides alone
makes massive moons die fastest (``moon_inspiral_yr`` goes as 1/m_sat). But a massive moon
torques the planet too, and a moon of ~1% of the planet's mass can *synchronise the planet
to itself*, overpowering the star and holding corotation inside the moon's orbit
indefinitely. Tokadjian & Piro's conclusion is therefore that **massive moons are more
likely to survive** -- and massive moons are exactly the ones RV detects.

So the close-in case has two regimes, and which one a system is in depends on the moon:
light moons inspiral on the ``moon_inspiral_yr`` clock, heavy moons may latch the system
into a stable configuration. This module reports both rather than choosing.
"""


def moon_can_synchronise_planet(p_spin_d: float, p_orbit_d: float, ecc_planet: float = 0.0) -> bool:
    """Tokadjian & Piro 2023 eq. 9 -- is a moon-synchronised end state self-consistent?"""
    return p_spin_d < p_orbit_d * (1.0 - 1.03 * ecc_planet) ** 1.5 * 0.198


def hrccs_velocity_swing_kms(
    sma_au: float, m_star_msun: float, t_obs_hr: float = 8.0
) -> float:
    """Line-of-sight velocity change of the planet over one observation, km/s.

    ``2 v_orb sin(pi t / P)``, evaluated across a window centred on conjunction where the
    swing is largest. This is the observable that makes high-resolution cross-correlation
    spectroscopy work at all: the planet's lines must walk across the detector far enough
    to separate from the static stellar and telluric lines.

    **Horstman et al. 2025 (arXiv:2505.09781) put the bar at Delta v ~ 30-60 km/s** for a
    6-sigma Keck/KPIC detection (30 for an ultra-hot Jupiter, 50 classical, 60 hot Saturn),
    against a 9 km/s instrumental resolution, and note the threshold scales with resolution.

    For small ``t/P`` this reduces to ``Delta v ~ G M_star t / a^2``, which combined with
    ``tau_spin_down ~ a^6 / M_star^2`` gives ``tau_spin_down ~ M_star t^3 / Delta v^3``:
    **every factor 2 gained in observability costs a factor 8 in satellite survival time.**
    That single scaling is the whole close-in story.
    """
    a = sma_au * AU_M
    v = math.sqrt(G * m_star_msun * M_SUN_KG / a)
    p = 2.0 * math.pi * math.sqrt(a**3 / (G * m_star_msun * M_SUN_KG))
    return 2.0 * v * math.sin(math.pi * t_obs_hr * 3600.0 / p) / 1000.0


HRCCS_MIN_SWING_KMS = 30.0
"""Most optimistic of Horstman et al. 2025's three thresholds (ultra-hot Jupiter model).
Used as the admission cut so the close-in survey over-admits rather than wrongly excludes."""


PLANET_MASS_CEILING_MJUP = 13.0
"""A "hot Jupiter" host need not be 1 M_Jup -- the planetary range runs to the
deuterium-burning limit, and **using it is the single cheapest fix to M8's problem.**

How planet mass enters, which is not obvious because two effects cancel and a third does not:

- **The geometry is self-similar.** The Roche limit, the corotation radius and the
  Hill-stability limit *all* scale as ``M_p^(1/3)``. So the survival window's width in dex
  and the satellite periods inside it are **independent of planet mass** -- a 13 M_Jup
  planet does not have a proportionally roomier satellite system, just a bigger one at the
  same periods.
- **Spin-down does not.** ``tau_spin_down ~ M_p R_p^-3 a^6``, i.e. it goes as the planet's
  *mean density*, and electron degeneracy pins R_p near 1.2 R_Jup across the whole
  1-13 M_Jup range. So ``tau_spin_down ~ M_p`` directly: **a 13 M_Jup planet resists
  despinning 13x longer than a 1 M_Jup one.** The critical distance therefore moves *in*
  as ``a_crit ~ (age/M_p)^(1/6)``, and since ``Delta v ~ 1/a^2``, observability improves as
  ``M_p^(1/3)``.
- **Sensitivity pays for it.** At the scaled orbit ``K ~ m_sat / M_p^(2/3)``.

Net over 1 -> 13 M_Jup: **Delta v improves 2.35x, minimum satellite mass worsens 5.5x.**
The first is what matters, because Delta v faces a hard threshold (30 km/s or no detection
at all) while satellite mass is a continuous sensitivity limit. **From ~5 M_Jup upward the
observability bar clears at the pessimistic Q = 1e5**, with no favourable tidal assumption
required -- which is what turns M8 from Q-limited into merely difficult.

Part of the 5.5x is bought back: a 13 M_Jup young planet is far brighter than a 1 M_Jup one,
and cross-correlation velocity precision is photon-limited. Just above this ceiling sits
``DEUTERIUM_CLIFF_MJUP``, where objects have burned deuterium and are brighter again -- but
those are brown dwarfs, and at wide separation they are M7's targets, not M8's.

**13 M_Jup is therefore the optimum for this method: the most massive object that is still
a planet.** Prefer high-mass hosts when ranking close-in candidates.
"""


def min_detectable_sat_mearth(
    m_host_mjup: float, a_sat_au: float, threshold_ms: float
) -> float:
    """Lightest satellite whose reflex amplitude clears ``threshold_ms``, in M_Earth.

    Lazzoni et al. 2022 eq. 2 rearranged: ``K = (m_s/M_p) sqrt(G M_p / a_s)``, valid while
    ``m_s << M_p`` (the regime every real candidate is in).
    """
    m_p = m_host_mjup * M_JUP_KG
    v_orb = math.sqrt(G * m_p / (a_sat_au * AU_M))
    return threshold_ms / v_orb * m_p / M_EARTH_KG


def satellite_mass_ratio_expectation(m_host_mjup: float) -> float:
    """Expected satellite/host mass ratio from circumplanetary-disc formation.

    ``q ~ 1e-4 sqrt(M/M_Jup)`` -- the Canup & Ward (2006) gas-starved disc ratio of 1e-4,
    scaled by Batygin & Morbidelli (2020)'s ``q ~ sqrt(M)``, as Ruffio et al. 2023 use it.
    Measured once: the PDS 70 c circumplanetary disc masses 5e-5 of its planet.

    This is the *core-accretion* expectation and it is brutally small -- 1e-4 of 37 M_Jup
    is 1.2 M_Earth. Hoy et al.'s satellites sit at q = 0.02 and 0.007, two to three orders
    of magnitude above it, which is why the paper attributes them to gravitational
    instability instead (its reference [21], Inderbitzi et al. 2020).
    """
    return 1e-4 * math.sqrt(m_host_mjup)


def expected_sat_mass_mearth(m_host_mjup: float) -> float:
    """:func:`satellite_mass_ratio_expectation` converted to M_Earth."""
    return satellite_mass_ratio_expectation(m_host_mjup) * m_host_mjup * MEARTH_PER_MJUP
