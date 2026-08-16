"""Attribution: propagate a *known* MPC orbit and predict where it was on an ITF night.

This is the inverse of everything the linker does. ``link/`` starts from tracklets and
hypothesises orbits; here the orbit is already fitted -- by the MPC, from a designated
object's observations -- and the question is which ITF tracklets are consistent with it.
The propagation, observer and frame machinery is :mod:`itf_linker.link.geometry`,
unchanged; this module adds only

* :func:`parse_mpc_orb` -- the MPC orbits API (``data.minorplanetcenter.net/api/get-orb``)
  returns an ``mpc_orb`` block whose ``CAR`` coefficients are a heliocentric cartesian
  state in the **ecliptic** frame (``system_data.refsys: "Ecliptic"``) at an MJD/**TDT**
  epoch. The ITF work is all ICRS equatorial, so the state is rotated here, once, using
  the obliquity the same document declares (84381.448 arcsec -- IAU76, identical to
  :func:`itf_linker.link.geometry.ecliptic_obliquity_matrix`).
* :func:`predict` -- two-body propagation of that state to each requested epoch, with
  light-time iteration, returning geocentric astrometric RA/Dec, sky-plane rates, and a
  rough predicted V. **Two-body is an approximation whose error grows with lookback**;
  it is measured against JPL Horizons in ``scripts/m7_calibration.py`` rather than
  assumed, and the coarse gate radius is set from that measurement. The final arbiter of
  any candidate is never this prediction -- it is a full Find_Orb fit of the object's
  published astrometry plus the ITF tracklet, gated exactly like every other fit in this
  repository.

Geocentric, not topocentric: the parallax of a main-belt object is <= ~9 arcsec/Delta(AU),
two orders below the coarse radii used, and the exact fit re-reduces everything
topocentrically anyway.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..link.geometry import (
    C_AU_PER_DAY,
    TT_MINUS_UTC_DAYS,
    earth_heliocentric_posvel,
    ecliptic_obliquity_matrix,
    propagate_kepler,
    unit_vectors,
)

#: Ecliptic -> equatorial (ICRS) rotation: the transpose of the equatorial -> ecliptic
#: matrix the linker already uses for reporting. Both sides carry the IAU76 obliquity
#: (84381.448"), which is also the value ``system_data`` declares in every mpc_orb
#: document seen from the API -- asserted per-document in :func:`parse_mpc_orb` rather
#: than trusted.
ECL_TO_EQ = ecliptic_obliquity_matrix().T

#: The obliquity the parser accepts, arcsec. A document declaring anything else is a
#: frame this module does not implement, and must fail loudly rather than mis-rotate.
_EXPECTED_OBLIQUITY_ARCSEC = 84381.448


@dataclass(slots=True)
class AttribOrbit:
    """One designated object's current MPC orbit, as an equatorial heliocentric state."""

    requested_desig: str
    primary_desig: str
    packed_primary: str
    all_desigs: list[str] = field(default_factory=list)

    epoch_mjd_tt: float = 0.0
    #: Heliocentric ICRS-equatorial position (AU) and velocity (AU/day) at the epoch.
    r0: np.ndarray = field(default_factory=lambda: np.zeros(3))
    v0: np.ndarray = field(default_factory=lambda: np.zeros(3))

    h_mag: float | None = None
    g_slope: float | None = None
    u_param: int | None = None
    arc_days: float | None = None
    n_obs: int | None = None
    n_opp: int | None = None
    normalized_rms: float | None = None
    orbit_quality: str | None = None
    orbit_type: str | None = None
    moid_earth: float | None = None

    @property
    def a_au(self) -> float:
        """Osculating semi-major axis from the state (two-body energy)."""
        from ..link.geometry import GM_SUN

        r = float(np.linalg.norm(self.r0))
        v2 = float(self.v0 @ self.v0)
        return 1.0 / (2.0 / r - v2 / GM_SUN)

    @property
    def period_days(self) -> float:
        from ..link.geometry import GM_SUN

        a = self.a_au
        return 2.0 * math.pi * math.sqrt(max(a, 1e-9) ** 3 / GM_SUN)


def _parse_arc_days(text: Any) -> float | None:
    """``"108 days"`` -> 108.0. The API writes the unit into the string."""
    if text is None:
        return None
    m = re.match(r"\s*([\d.]+)\s*day", str(text))
    return float(m.group(1)) if m else None


def parse_mpc_orb(doc: Any, requested_desig: str = "") -> AttribOrbit | None:
    """Parse one get-orb response (the API's list envelope or a bare mpc_orb dict).

    Returns ``None`` when the document carries no fitted orbit. Raises ``ValueError``
    when the document's declared frame is not the heliocentric ecliptic/ICRF one this
    module implements -- a wrong rotation is a silent position error of up to ~23 deg.
    """
    if isinstance(doc, list):
        doc = doc[0] if doc else {}
    orbs = doc.get("mpc_orb") if isinstance(doc, dict) else None
    if not orbs:
        return None
    orb = orbs[0]

    system = orb.get("system_data") or {}
    obliquity = float(system.get("EclipticObliquityArcseconds", "nan"))
    refsys = str(system.get("refsys", ""))
    if refsys != "Ecliptic" or abs(obliquity - _EXPECTED_OBLIQUITY_ARCSEC) > 0.01:
        raise ValueError(
            f"unsupported mpc_orb frame: refsys={refsys!r} obliquity={obliquity!r}"
        )

    car = orb.get("CAR") or {}
    values = car.get("coefficient_values")
    names = car.get("coefficient_names")
    if not values or names[:6] != ["x", "y", "z", "vx", "vy", "vz"]:
        return None
    state = np.asarray(values[:6], dtype=float)
    r0 = ECL_TO_EQ @ state[:3]
    v0 = ECL_TO_EQ @ state[3:]

    epoch = orb.get("epoch_data") or {}
    if str(epoch.get("timeform")) != "MJD" or str(epoch.get("timesystem")) != "TDT":
        raise ValueError(f"unsupported epoch convention: {epoch!r}")

    desig = orb.get("designation_data") or {}
    stats = orb.get("orbit_fit_statistics") or {}
    mags = orb.get("magnitude_data") or {}
    moids = orb.get("moid_data") or {}
    cat = orb.get("categorization") or {}

    def _f(x: Any) -> float | None:
        try:
            out = float(x)
        except (TypeError, ValueError):
            return None
        return out if math.isfinite(out) else None

    primary = str(desig.get("unpacked_primary_provisional_designation") or requested_desig)
    return AttribOrbit(
        requested_desig=requested_desig or primary,
        primary_desig=primary,
        packed_primary=str(desig.get("packed_primary_provisional_designation") or ""),
        all_desigs=[primary]
        + [str(s) for s in desig.get("unpacked_secondary_provisional_designations") or []],
        epoch_mjd_tt=float(epoch["epoch"]),
        r0=r0,
        v0=v0,
        h_mag=_f(mags.get("H")),
        g_slope=_f(mags.get("G")),
        u_param=int(stats["U_param"]) if stats.get("U_param") is not None else None,
        arc_days=_parse_arc_days(stats.get("arc_length_total")),
        n_obs=stats.get("nobs_total"),
        n_opp=stats.get("nopp"),
        normalized_rms=_f(stats.get("normalized_RMS")),
        orbit_quality=str(stats.get("orbit_quality") or "") or None,
        orbit_type=str(cat.get("orbit_type_str") or "") or None,
        moid_earth=_f(moids.get("Earth")),
    )


def predict(
    orbit: AttribOrbit,
    mjd_utc: np.ndarray,
    *,
    light_time_iterations: int = 2,
) -> dict[str, np.ndarray]:
    """Geocentric astrometric prediction of ``orbit`` at each UTC epoch.

    Returns arrays: ``ra_deg``, ``dec_deg``, great-circle sky rates
    ``rate_ra_cosdec_deg_day`` / ``rate_dec_deg_day`` (the same convention as
    :mod:`itf_linker.link.arrows`), ``delta_au``, ``r_au``, ``v_pred`` (H/G apparent
    magnitude), and ``kepler_ok`` (the universal-variable solver converged).

    Astrometric = light-time corrected, no aberration of the observer (matching the
    astrometric place the MPC's astrometry is reduced to). Epochs are UTC and converted
    to TT internally, mirroring :func:`itf_linker.link.geometry.observer_heliocentric`.
    """
    mjd_utc = np.atleast_1d(np.asarray(mjd_utc, dtype=float))
    n = mjd_utc.shape[0]
    e_pos, e_vel = earth_heliocentric_posvel(mjd_utc)

    dt0 = (mjd_utc + TT_MINUS_UTC_DAYS) - orbit.epoch_mjd_tt
    r_obj = np.broadcast_to(orbit.r0, (n, 3))
    v_obj = np.broadcast_to(orbit.v0, (n, 3))

    tau = np.zeros(n)
    ok = np.ones(n, dtype=bool)
    for _ in range(max(1, light_time_iterations) + 1):
        r_obj, v_obj, conv = propagate_kepler(
            np.broadcast_to(orbit.r0, (n, 3)).copy(),
            np.broadcast_to(orbit.v0, (n, 3)).copy(),
            dt0 - tau,
        )
        ok &= conv
        delta_vec = r_obj - e_pos
        delta = np.linalg.norm(delta_vec, axis=1)
        tau = delta / C_AU_PER_DAY

    rho_hat = delta_vec / delta[:, None]
    ra = np.degrees(np.arctan2(rho_hat[:, 1], rho_hat[:, 0])) % 360.0
    dec = np.degrees(np.arcsin(np.clip(rho_hat[:, 2], -1.0, 1.0)))

    # Sky-plane angular rate from the relative velocity, projected on the local
    # (e_ra, e_dec) basis -- the same basis unit_vector_rates uses, run in reverse.
    v_rel = v_obj - e_vel
    v_tan = v_rel - np.einsum("ij,ij->i", v_rel, rho_hat)[:, None] * rho_hat
    mu_vec = v_tan / delta[:, None]  # rad/day in the tangent plane
    ra_r = np.radians(ra)
    dec_r = np.radians(dec)
    e_ra = np.stack([-np.sin(ra_r), np.cos(ra_r), np.zeros_like(ra_r)], axis=-1)
    e_dec = np.stack(
        [-np.sin(dec_r) * np.cos(ra_r), -np.sin(dec_r) * np.sin(ra_r), np.cos(dec_r)],
        axis=-1,
    )
    rate_ra_cosdec = np.degrees(np.einsum("ij,ij->i", mu_vec, e_ra))
    rate_dec = np.degrees(np.einsum("ij,ij->i", mu_vec, e_dec))

    r_helio = np.linalg.norm(r_obj, axis=1)
    v_pred = np.full(n, np.nan)
    if orbit.h_mag is not None:
        g = orbit.g_slope if orbit.g_slope is not None else 0.15
        cos_alpha = np.clip(
            np.einsum("ij,ij->i", r_obj, delta_vec) / (r_helio * delta), -1.0, 1.0
        )
        alpha = np.arccos(cos_alpha)
        # Bowell H,G phase function (the MPC's own photometric model).
        ta2 = np.tan(alpha / 2.0)
        phi1 = np.exp(-3.33 * ta2**0.63)
        phi2 = np.exp(-1.87 * ta2**1.22)
        phase = np.where(
            (1 - g) * phi1 + g * phi2 > 0,
            -2.5 * np.log10(np.clip((1 - g) * phi1 + g * phi2, 1e-12, None)),
            np.inf,
        )
        v_pred = orbit.h_mag + 5.0 * np.log10(r_helio * delta) + phase

    return {
        "ra_deg": ra,
        "dec_deg": dec,
        "rate_ra_cosdec_deg_day": rate_ra_cosdec,
        "rate_dec_deg_day": rate_dec,
        "delta_au": delta,
        "r_au": r_helio,
        "v_pred": v_pred,
        "kepler_ok": ok,
    }


def separation_deg(
    ra1_deg: np.ndarray, dec1_deg: np.ndarray, ra2_deg: np.ndarray, dec2_deg: np.ndarray
) -> np.ndarray:
    """Great-circle separation, degrees, vectorised (dot of unit vectors -- exact)."""
    u1 = unit_vectors(np.asarray(ra1_deg, float), np.asarray(dec1_deg, float))
    u2 = unit_vectors(np.asarray(ra2_deg, float), np.asarray(dec2_deg, float))
    return np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", u1, u2), -1.0, 1.0)))


def control_orbit(orbit: AttribOrbit) -> AttribOrbit:
    """The amplitude-matched decoy: the same orbit half a period out of phase.

    Propagating the epoch state by P/2 keeps every element -- a, e, i, node, argperi --
    and therefore the same sky-rate statistics and the same time spent in each part of
    the sky, while decoupling *where the object actually was* on any given night. Match
    rates against real tracklets under this decoy measure the coarse gate's chance-
    coincidence background. (An amplitude-matched control is house law: an unmatched one
    screens nothing -- see exosat-rv M9.)
    """
    half = orbit.period_days / 2.0
    r_new, v_new, conv = propagate_kepler(
        orbit.r0[None, :].copy(), orbit.v0[None, :].copy(), np.array([half])
    )
    if not bool(conv[0]):  # pragma: no cover - a bound MPC orbit always propagates
        raise ValueError(f"control propagation failed for {orbit.primary_desig}")
    out = AttribOrbit(
        requested_desig=orbit.requested_desig,
        primary_desig=orbit.primary_desig + " [CONTROL]",
        packed_primary=orbit.packed_primary,
        all_desigs=list(orbit.all_desigs),
        epoch_mjd_tt=orbit.epoch_mjd_tt,
        r0=r_new[0],
        v0=v_new[0],
        h_mag=orbit.h_mag,
        g_slope=orbit.g_slope,
        u_param=orbit.u_param,
        arc_days=orbit.arc_days,
        n_obs=orbit.n_obs,
        n_opp=orbit.n_opp,
        normalized_rms=orbit.normalized_rms,
        orbit_quality=orbit.orbit_quality,
        orbit_type=orbit.orbit_type,
        moid_earth=orbit.moid_earth,
    )
    return out
