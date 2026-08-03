"""The geometry HelioLinC needs: observers, the distance hypothesis, and propagation.

Everything here is pure numpy over arrays of tracklets and knows nothing about the ITF.
Units are AU, days, and radians unless a name says otherwise; frames are ICRS equatorial
throughout, which is the frame the MPC's RA/Dec are already in, so no rotation is ever
applied to the astrometry.

The chain, for one tracklet and one hypothesis:

1. **Observer.** ``observer_heliocentric`` gives the observatory's heliocentric position
   and velocity: Earth's, from the ephemeris, plus a topocentric offset built from the
   MPC's own parallax constants.
2. **Distance.** A hypothesised heliocentric distance ``r`` turns the observed direction
   into a *position*: the line of sight from the observer pierces the sphere of radius
   ``r`` about the Sun at :func:`solve_rho`.
3. **Velocity.** A hypothesised ``rdot`` closes the system -- see :func:`state_from_hypothesis`.
4. **Propagation.** :func:`propagate_kepler` carries every state to one epoch, where
   tracklets of the same object coincide and can be clustered.

Approximations, with their measured magnitudes, because each one is a silent error if it
turns out to matter:

* **Two-body propagation about the Sun.** Over a two-week window Jupiter displaces a
  main-belt asteroid by ~1e-5 AU, two orders below the clustering radius.
* **Sidereal rotation only** for the topocentric offset -- no polar motion, and the
  true-equator-of-date rotation is applied to a GCRS vector. The observer offset is
  4.3e-5 AU long and the frame discrepancy is ~1e-4 rad, so the error is ~4e-9 AU.
* **UT1 = UTC.** A 0.9 s error rotates the observer by 4e-5 rad x 4.3e-5 AU ~ 2e-9 AU.
* **Light time** is corrected: the state is dated at the time the light left the object.
"""

from __future__ import annotations

import numpy as np

#: Heliocentric gravitational parameter, AU^3/day^2 -- Gauss's constant squared.
GM_SUN = 0.01720209895**2

#: Speed of light in AU/day. Light time across 2.5 AU is 0.0144 d, over which a main-belt
#: asteroid moves 1.4e-4 AU -- comparable to the clustering radius, so it is corrected.
C_AU_PER_DAY = 173.144632674240

#: Earth's equatorial radius in AU, the unit the MPC's parallax constants are given in.
R_EARTH_AU = 4.26352325e-5

#: TT - UTC, in days. Constant to the ~1 s level over the ITF's modern slice; the leap
#: second count has not changed since 2017 and no more are scheduled.
TT_MINUS_UTC_DAYS = 69.184 / 86400.0

#: Smallest topocentric distance a hypothesis may imply, in AU.
#:
#: This guard is not cosmetic. As the hypothesised heliocentric distance approaches the
#: *observer's own* (~1 AU), the line of sight grazes the sphere and ``rho -> 0``: every
#: tracklet collapses onto the observer's own state vector, so every tracklet clusters
#: with every other tracklet, at spreads far tighter than a real object's. Measured
#: directly -- a hypothesis scan over 12 M1-fitted designations, scored by cluster
#: tightness, put four of them at r = 1.02-1.08 AU with a = 1.04 AU against Find_Orb's
#: 2.27-2.59 AU. Every one of those was the degeneracy, not an orbit.
MIN_TOPOCENTRIC_DISTANCE_AU = 0.05


# ----------------------------------------------------------------------------------
# Directions
# ----------------------------------------------------------------------------------

def unit_vectors(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    """Unit vectors towards ``(ra, dec)``, shape ``(n, 3)``."""
    ra = np.radians(np.asarray(ra_deg, dtype=float))
    dec = np.radians(np.asarray(dec_deg, dtype=float))
    cd = np.cos(dec)
    return np.stack([cd * np.cos(ra), cd * np.sin(ra), np.sin(dec)], axis=-1)


def unit_vector_rates(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    ra_rate_deg_per_day: np.ndarray,
    dec_rate_deg_per_day: np.ndarray,
) -> np.ndarray:
    """``d(rho_hat)/dt`` from a sky-plane rate, shape ``(n, 3)``.

    ``ra_rate`` is the *great-circle* rate ``d(alpha)/dt * cos(dec)``, i.e. already
    corrected for the convergence of the meridians -- the quantity :mod:`~itf_linker.link.arrows`
    fits. Using ``d(alpha)/dt`` here instead would inflate every rate near the pole by
    ``1/cos(dec)``.
    """
    ra = np.radians(np.asarray(ra_deg, dtype=float))
    dec = np.radians(np.asarray(dec_deg, dtype=float))
    mu_a = np.radians(np.asarray(ra_rate_deg_per_day, dtype=float))
    mu_d = np.radians(np.asarray(dec_rate_deg_per_day, dtype=float))
    sa, ca = np.sin(ra), np.cos(ra)
    sd, cd = np.sin(dec), np.cos(dec)
    e_ra = np.stack([-sa, ca, np.zeros_like(sa)], axis=-1)
    e_dec = np.stack([-sd * ca, -sd * sa, cd], axis=-1)
    return mu_a[:, None] * e_ra + mu_d[:, None] * e_dec


# ----------------------------------------------------------------------------------
# Observers
# ----------------------------------------------------------------------------------

def earth_heliocentric_posvel(mjd_utc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Earth's heliocentric ICRS position (AU) and velocity (AU/day), shape ``(n, 3)``.

    Imported lazily so the pure-geometry functions stay usable without astropy's
    ephemeris machinery.
    """
    from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris
    from astropy.time import Time

    mjd = np.atleast_1d(np.asarray(mjd_utc, dtype=float))
    with solar_system_ephemeris.set("builtin"):
        t = Time(mjd, format="mjd", scale="utc").tdb
        e_p, e_v = get_body_barycentric_posvel("earth", t)
        s_p, s_v = get_body_barycentric_posvel("sun", t)
    pos = (e_p - s_p).xyz.to("AU").value.T
    vel = (e_v - s_v).xyz.to("AU/d").value.T
    return np.ascontiguousarray(pos), np.ascontiguousarray(vel)


def greenwich_sidereal_radians(mjd_utc: np.ndarray) -> np.ndarray:
    """Greenwich apparent sidereal time, radians, via ERFA's IAU-2006/2000A model."""
    import erfa

    mjd = np.atleast_1d(np.asarray(mjd_utc, dtype=float))
    ut1a = np.full_like(mjd, 2400000.5)
    ut1b = mjd
    tta = ut1a
    ttb = mjd + TT_MINUS_UTC_DAYS
    return np.asarray(erfa.gst06a(ut1a, ut1b, tta, ttb), dtype=float)


def topocentric_offset(
    mjd_utc: np.ndarray,
    lon_east_deg: np.ndarray,
    rho_cos_phi: np.ndarray,
    rho_sin_phi: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Observatory position and velocity relative to Earth's centre, AU and AU/day.

    Built from the MPC's published parallax constants (``rho cos phi'``, ``rho sin phi'``
    in Earth radii) rather than from geodetic coordinates, because those constants are
    what ``ObsCodes.html`` actually publishes and they already fold in the Earth's
    flattening.

    Observatories with no parallax constants -- space telescopes and roving observers --
    should be passed zeros by the caller and are then treated as geocentric. That is
    wrong for a satellite, and it is why :mod:`itf_linker.link.arrows` excludes
    space-based tracklets rather than quietly mis-placing them by up to 0.01 AU.
    """
    theta = greenwich_sidereal_radians(mjd_utc) + np.radians(np.asarray(lon_east_deg, dtype=float))
    rc = np.asarray(rho_cos_phi, dtype=float) * R_EARTH_AU
    rs = np.asarray(rho_sin_phi, dtype=float) * R_EARTH_AU
    ct, st = np.cos(theta), np.sin(theta)
    pos = np.stack([rc * ct, rc * st, rs], axis=-1)
    omega = 2 * np.pi * 1.00273781191135448  # Earth rotation, radians/day
    vel = np.stack([-omega * rc * st, omega * rc * ct, np.zeros_like(rs)], axis=-1)
    return pos, vel


def observer_heliocentric(
    mjd_utc: np.ndarray,
    lon_east_deg: np.ndarray,
    rho_cos_phi: np.ndarray,
    rho_sin_phi: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Heliocentric position/velocity of each observatory at each epoch."""
    e_pos, e_vel = earth_heliocentric_posvel(mjd_utc)
    t_pos, t_vel = topocentric_offset(mjd_utc, lon_east_deg, rho_cos_phi, rho_sin_phi)
    return e_pos + t_pos, e_vel + t_vel


# ----------------------------------------------------------------------------------
# The distance hypothesis
# ----------------------------------------------------------------------------------

def solve_rho(
    obs_pos: np.ndarray, rho_hat: np.ndarray, r_helio: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Distance along the line of sight to the sphere of heliocentric radius ``r_helio``.

    Solves ``|R + rho * rho_hat| = r`` for the **far** root, which is the physical one for
    anything beyond the Earth: the near root is the same sphere pierced on the way in,
    behind the observer or between the observer and the Sun.

    Returns ``(rho, valid)``. ``valid`` is False where the line of sight misses the sphere
    entirely (the hypothesis is closer than the object's minimum possible distance in that
    direction) or where the far root is behind the observer.
    """
    b = np.einsum("ij,ij->i", obs_pos, rho_hat)
    r_obs2 = np.einsum("ij,ij->i", obs_pos, obs_pos)
    disc = b * b - r_obs2 + np.asarray(r_helio, dtype=float) ** 2
    valid = disc > 0.0
    root = np.sqrt(np.where(valid, disc, 0.0))
    rho = -b + root
    return rho, valid & (rho > 0.0)


def state_from_hypothesis(
    obs_pos: np.ndarray,
    obs_vel: np.ndarray,
    rho_hat: np.ndarray,
    rho_hat_dot: np.ndarray,
    r_helio: np.ndarray,
    rdot_helio: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Promote a tracklet to a heliocentric state under a ``(r, rdot)`` hypothesis.

    The position follows from :func:`solve_rho`. The velocity needs one more equation, and
    the hypothesised radial velocity supplies it. Differentiating ``|r_vec| = r``::

        r_vec . v_vec = r * rdot

    with ``r_vec = R + rho * rho_hat`` and ``v_vec = R' + rho' * rho_hat + rho * rho_hat'``.
    Using ``rho_hat . rho_hat = 1`` and ``rho_hat . rho_hat' = 0`` this collapses to a
    linear equation in the one unknown ``rho'``::

        rho' = [r*rdot - R.R' - rho*(R.rho_hat' + R'.rho_hat)] / (R.rho_hat + rho)

    whose denominator is ``r_vec . rho_hat``, i.e. the square root taken in
    :func:`solve_rho` -- strictly positive on the far root, so the solve never degenerates.

    Returns ``(r_vec, v_vec, rho, valid)``.
    """
    rho, valid = solve_rho(obs_pos, rho_hat, r_helio)
    valid &= rho > MIN_TOPOCENTRIC_DISTANCE_AU
    r_vec = obs_pos + rho[:, None] * rho_hat

    denom = np.einsum("ij,ij->i", r_vec, rho_hat)
    rhs = (
        np.asarray(r_helio, dtype=float) * np.asarray(rdot_helio, dtype=float)
        - np.einsum("ij,ij->i", obs_pos, obs_vel)
        - rho
        * (
            np.einsum("ij,ij->i", obs_pos, rho_hat_dot)
            + np.einsum("ij,ij->i", obs_vel, rho_hat)
        )
    )
    safe = np.where(np.abs(denom) > 1e-12, denom, 1.0)
    rho_dot = np.where(np.abs(denom) > 1e-12, rhs / safe, 0.0)
    v_vec = obs_vel + rho_dot[:, None] * rho_hat + rho[:, None] * rho_hat_dot
    return r_vec, v_vec, rho, valid


# ----------------------------------------------------------------------------------
# Two-body propagation
# ----------------------------------------------------------------------------------

def stumpff(psi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Stumpff functions ``C(psi)`` and ``S(psi)``, valid for all conic types.

    The closed forms lose precision through cancellation near ``psi = 0``, so the series
    is used there instead. The switch point is chosen where the two agree to ~1e-15.
    """
    psi = np.asarray(psi, dtype=float)
    c2 = np.empty_like(psi)
    c3 = np.empty_like(psi)

    pos = psi > 1e-6
    neg = psi < -1e-6
    small = ~(pos | neg)

    if np.any(pos):
        s = np.sqrt(psi[pos])
        c2[pos] = (1.0 - np.cos(s)) / psi[pos]
        c3[pos] = (s - np.sin(s)) / (s * psi[pos])
    if np.any(neg):
        s = np.sqrt(-psi[neg])
        c2[neg] = (np.cosh(s) - 1.0) / (-psi[neg])
        c3[neg] = (np.sinh(s) - s) / (s * (-psi[neg]))
    if np.any(small):
        p = psi[small]
        c2[small] = 0.5 - p / 24.0 + p * p / 720.0
        c3[small] = 1.0 / 6.0 - p / 120.0 + p * p / 5040.0
    return c2, c3


def propagate_kepler(
    r_vec: np.ndarray,
    v_vec: np.ndarray,
    dt: np.ndarray,
    mu: float = GM_SUN,
    *,
    max_iter: int = 60,
    tol: float = 1e-11,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Advance states by ``dt`` on their two-body orbits. Returns ``(r, v, converged)``.

    Universal variables (Stumpff/Battin formulation), so ellipses, parabolas and
    hyperbolas all take the same code path -- which matters here because a wrong distance
    hypothesis routinely produces an unbound state, and that must propagate to *something*
    rather than raise.
    """
    r_vec = np.atleast_2d(np.asarray(r_vec, dtype=float))
    v_vec = np.atleast_2d(np.asarray(v_vec, dtype=float))
    dt = np.broadcast_to(np.asarray(dt, dtype=float), (r_vec.shape[0],)).astype(float)

    sqrt_mu = np.sqrt(mu)
    r0 = np.linalg.norm(r_vec, axis=1)
    v0sq = np.einsum("ij,ij->i", v_vec, v_vec)
    rdotv = np.einsum("ij,ij->i", r_vec, v_vec)
    alpha = 2.0 / np.maximum(r0, 1e-12) - v0sq / mu          # = 1/a
    sigma0 = rdotv / sqrt_mu

    # Initial guess: the elliptic one works for every case here because |alpha*dt| stays
    # modest over the windows this linker uses; a few extra Newton steps cost nothing.
    chi = sqrt_mu * dt * alpha
    near_parabolic = np.abs(alpha) < 1e-8
    chi = np.where(near_parabolic, sqrt_mu * dt / np.maximum(r0, 1e-12), chi)

    converged = np.zeros(r0.shape, dtype=bool)
    for _ in range(max_iter):
        psi = chi * chi * alpha
        c2, c3 = stumpff(psi)
        r = chi * chi * c2 + sigma0 * chi * (1.0 - psi * c3) + r0 * (1.0 - psi * c2)
        r = np.where(np.abs(r) < 1e-12, 1e-12, r)
        f = (
            chi * chi * chi * c3
            + sigma0 * chi * chi * c2
            + r0 * chi * (1.0 - psi * c3)
            - sqrt_mu * dt
        )
        step = -f / r
        chi = chi + step
        converged = np.abs(step) < tol
        if np.all(converged):
            break

    psi = chi * chi * alpha
    c2, c3 = stumpff(psi)
    r = chi * chi * c2 + sigma0 * chi * (1.0 - psi * c3) + r0 * (1.0 - psi * c2)
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)

    f_l = 1.0 - chi * chi * c2 / np.maximum(r0, 1e-12)
    g_l = dt - chi * chi * chi * c3 / sqrt_mu
    gdot = 1.0 - chi * chi * c2 / r
    fdot = sqrt_mu / (r * np.maximum(r0, 1e-12)) * chi * (psi * c3 - 1.0)

    r_new = f_l[:, None] * r_vec + g_l[:, None] * v_vec
    v_new = fdot[:, None] * r_vec + gdot[:, None] * v_vec
    return r_new, v_new, converged


# ----------------------------------------------------------------------------------
# Elements, for reporting and for cross-checking against a fitted orbit
# ----------------------------------------------------------------------------------

def state_to_elements(r_vec: np.ndarray, v_vec: np.ndarray, mu: float = GM_SUN) -> dict[str, np.ndarray]:
    """Osculating ``a``, ``e``, ``i``, ``q`` (AU, degrees) from heliocentric states.

    Used to sanity-check the geometry against an independently fitted orbit, and to give
    a candidate link a first-look orbit before Find_Orb ever runs. Not a substitute for
    the fit: there is no least squares here and no perturbations.
    """
    r_vec = np.atleast_2d(np.asarray(r_vec, dtype=float))
    v_vec = np.atleast_2d(np.asarray(v_vec, dtype=float))
    r = np.linalg.norm(r_vec, axis=1)
    v2 = np.einsum("ij,ij->i", v_vec, v_vec)
    energy = v2 / 2.0 - mu / r
    a = -mu / (2.0 * energy)
    h_vec = np.cross(r_vec, v_vec)
    h = np.linalg.norm(h_vec, axis=1)
    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r[:, None]
    e = np.linalg.norm(e_vec, axis=1)
    incl = np.degrees(np.arccos(np.clip(h_vec[:, 2] / np.where(h > 0, h, 1.0), -1.0, 1.0)))
    q = a * (1.0 - e)
    return {"a": a, "e": e, "incl": incl, "q": q}


def ecliptic_obliquity_matrix() -> np.ndarray:
    """Rotation from ICRS equatorial to ecliptic-of-J2000, for reporting inclinations."""
    eps = np.radians(23.4392911111)
    c, s = np.cos(eps), np.sin(eps)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, s], [0.0, -s, c]])
