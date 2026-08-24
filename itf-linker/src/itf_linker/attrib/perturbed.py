"""Perturbed propagation: the backend that opens |Delta-t| > 4 years to attribution.

M7 measured two-body propagation of a current MPC orbit at ~600 arcsec by 4 years of
lookback and *degree scale* by 5-15 (``M7-RESULTS.md`` section 5) -- which locked the
attribution sweep out of the pre-2023 ITF, exactly where M4/M5 located the cross-survey
pool. This module integrates the same heliocentric state with the Sun plus the eight
planets (Mercury..Neptune, Earth+Moon as one barycentric mass) as point masses:

* **Force model**: Newtonian point masses, planet positions from JPL's approximate mean
  elements and DE440 GMs (:mod:`itf_linker.attrib.planets`). No relativity, no asteroid
  perturbers, no non-gravitational terms -- their combined effect is *measured*, not
  assumed, in ``scripts/m8_calibration.py`` against JPL Horizons, and the coarse gate is
  frozen from that measured envelope (m8 measured: <= ~55 arcsec at 15 years on the
  calibration set, vs 7,545 arcsec two-body).
* **Integrator**: fixed-step RK4, vectorised across every orbit in the chunk, planet
  positions precomputed once per time grid and shared. At h = 1.0 day the step error is
  invisible next to the force-model error (halving h changes 15-year predictions by
  < 0.01 arcsec on the calibration set), and a 15-year backward integration of a
  thousand-orbit chunk is seconds, not hours.
* **Dense output**: states are stored every ``dense_every`` steps and evaluated by cubic
  Hermite interpolation, whose worst-case error at 8-day spacing is ~1e-6 AU for an
  a = 0.8 AU orbit (sub-arcsec at any plausible geocentric distance) and orders less
  for the main belt.

Close encounters are the honest limit of any point-mass extrapolation of a *fitted*
orbit: inside a planet's Hill sphere the trajectory diverges from truth faster than any
envelope measured on quiet orbits. The integrator therefore tracks each orbit's minimum
planet distance and flags Hill-sphere entries; the sweep carries the flag into every
candidate so a verdict can never silently rest on a post-encounter prediction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..link.geometry import C_AU_PER_DAY, GM_SUN, TT_MINUS_UTC_DAYS, earth_heliocentric_posvel
from .core import observables_from_states
from .planets import GM_PLANETS, MEAN_ELEMENTS, planet_positions

#: Hill radii of the eight perturbers, AU, computed from the same GM ratios the force
#: model uses (a_p * (GM_p / 3 GM_sun)^(1/3), with a_p from the mean-element table).
HILL_RADII_AU = MEAN_ELEMENTS[:, 0] * (GM_PLANETS / (3.0 * GM_SUN)) ** (1.0 / 3.0)


def _accel(r: np.ndarray, planets_t: np.ndarray, min_d2: np.ndarray | None = None) -> np.ndarray:
    """Heliocentric acceleration of ``r`` (n, 3) given planet positions (8, 3).

    The indirect term (``-GM_p * r_p / |r_p|^3``) is included: the frame is
    heliocentric, and the Sun itself accelerates towards the planets.

    ``min_d2``, when given (n, 8), is updated in place with the squared distance to each
    planet -- the running minimum the encounter flag is built from.
    """
    rn2 = np.einsum("ij,ij->i", r, r)
    a = (-GM_SUN / (rn2 * np.sqrt(rn2)))[:, None] * r
    for p in range(planets_t.shape[0]):
        d = planets_t[p] - r
        dn2 = np.einsum("ij,ij->i", d, d)
        if min_d2 is not None:
            np.minimum(min_d2[:, p], dn2, out=min_d2[:, p])
        pn2 = float(planets_t[p] @ planets_t[p])
        a += GM_PLANETS[p] * (
            d / (dn2 * np.sqrt(dn2))[:, None] - planets_t[p] / (pn2 * np.sqrt(pn2))
        )
    return a


@dataclass(slots=True)
class DenseTrajectory:
    """Perturbed trajectories of a chunk of orbits, evaluable at any time in the span.

    ``node_t`` is ascending MJD(TT); ``node_r``/``node_v`` are (n_nodes, n_orb, 3).
    ``min_planet_dist_au`` (n_orb, 8) is the closest approach to each perturber seen at
    any integration step start; ``encounter`` flags orbits that entered a Hill sphere,
    whose predictions inherit no accuracy claim from the calibration envelope.
    """

    node_t: np.ndarray
    node_r: np.ndarray
    node_v: np.ndarray
    min_planet_dist_au: np.ndarray

    @property
    def n_orbits(self) -> int:
        return self.node_r.shape[1]

    @property
    def encounter(self) -> np.ndarray:
        return np.any(self.min_planet_dist_au < HILL_RADII_AU[None, :], axis=1)

    def state_at(self, t_tt: np.ndarray, orbit_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Cubic-Hermite position/velocity for pairs ``(t_tt[i], orbit_idx[i])``.

        Vectorised over pairs; times may repeat and orbits may repeat. Times must lie
        within the integrated span (one node spacing of slack covers light-time
        iteration at the edges); anything further out raises rather than extrapolates.
        """
        t = np.atleast_1d(np.asarray(t_tt, dtype=float))
        idx = np.atleast_1d(np.asarray(orbit_idx, dtype=np.intp))
        slack = float(self.node_t[1] - self.node_t[0])
        if t.size and (t.min() < self.node_t[0] - slack or t.max() > self.node_t[-1] + slack):
            raise ValueError(
                f"time outside integrated span: [{t.min():.2f}, {t.max():.2f}] vs "
                f"[{self.node_t[0]:.2f}, {self.node_t[-1]:.2f}] MJD(TT)"
            )
        i = np.clip(np.searchsorted(self.node_t, t, side="right") - 1, 0, self.node_t.size - 2)
        t0 = self.node_t[i]
        dt = self.node_t[i + 1] - t0
        s = ((t - t0) / dt)[:, None]
        r0 = self.node_r[i, idx]
        r1 = self.node_r[i + 1, idx]
        v0 = self.node_v[i, idx] * dt[:, None]
        v1 = self.node_v[i + 1, idx] * dt[:, None]
        s2 = s * s
        s3 = s2 * s
        r = (
            (2 * s3 - 3 * s2 + 1) * r0
            + (s3 - 2 * s2 + s) * v0
            + (-2 * s3 + 3 * s2) * r1
            + (s3 - s2) * v1
        )
        v = (
            (6 * s2 - 6 * s) * r0
            + (3 * s2 - 4 * s + 1) * v0
            + (-6 * s2 + 6 * s) * r1
            + (3 * s2 - 2 * s) * v1
        ) / dt[:, None]
        return r, v


def _leg_boundaries(t0: float, t_end: float, h_abs: float) -> np.ndarray:
    """Step boundary times from ``t0`` towards ``t_end``, last step possibly short."""
    n_full = int(abs(t_end - t0) // h_abs)
    sign = 1.0 if t_end >= t0 else -1.0
    ts = t0 + sign * h_abs * np.arange(n_full + 1)
    if abs(float(ts[-1]) - t_end) > 1e-9:
        ts = np.append(ts, t_end)
    return ts


def _integrate_leg(
    r: np.ndarray,
    v: np.ndarray,
    ts: np.ndarray,
    dense_every: int,
    min_d2: np.ndarray,
) -> tuple[list[float], list[np.ndarray], list[np.ndarray]]:
    """RK4 along the boundary times ``ts`` (uniform except possibly the last step)."""
    mids = (ts[:-1] + ts[1:]) / 2.0
    p_full = planet_positions(ts)
    p_half = planet_positions(mids)
    nodes_t: list[float] = []
    nodes_r: list[np.ndarray] = []
    nodes_v: list[np.ndarray] = []
    n_steps = ts.size - 1
    for k in range(n_steps):
        h = float(ts[k + 1] - ts[k])
        p0, ph, p1 = p_full[k], p_half[k], p_full[k + 1]
        k1v = _accel(r, p0, min_d2)
        k2r = v + 0.5 * h * k1v
        k2v = _accel(r + 0.5 * h * v, ph)
        k3r = v + 0.5 * h * k2v
        k3v = _accel(r + 0.5 * h * k2r, ph)
        k4r = v + h * k3v
        k4v = _accel(r + h * k3r, p1)
        r = r + (h / 6.0) * (v + 2 * k2r + 2 * k3r + k4r)
        v = v + (h / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
        if (k + 1) % dense_every == 0 or k == n_steps - 1:
            nodes_t.append(float(ts[k + 1]))
            nodes_r.append(r.copy())
            nodes_v.append(v.copy())
    return nodes_t, nodes_r, nodes_v


def integrate_dense(
    r0: np.ndarray,
    v0: np.ndarray,
    epoch_mjd_tt: float,
    t_min_tt: float,
    t_max_tt: float,
    *,
    h_days: float = 1.0,
    dense_every: int = 8,
) -> DenseTrajectory:
    """Integrate every orbit of a chunk across ``[t_min, t_max]`` MJD(TT).

    ``r0``/``v0`` are (n_orb, 3) heliocentric ICRS-equatorial states at a **common**
    epoch (the bulk MPCORB file quotes one standard epoch; the handful of exceptions are
    integrated in their own chunks by the caller). Backward and forward legs run from
    the epoch so the fitted state is never extrapolated through itself.
    """
    r0 = np.atleast_2d(np.asarray(r0, dtype=float))
    v0 = np.atleast_2d(np.asarray(v0, dtype=float))
    if not (t_min_tt <= epoch_mjd_tt <= t_max_tt):
        raise ValueError(
            f"epoch {epoch_mjd_tt} outside requested span [{t_min_tt}, {t_max_tt}]"
        )
    min_d2 = np.full((r0.shape[0], GM_PLANETS.size), np.inf)
    all_t: list[float] = [epoch_mjd_tt]
    all_r: list[np.ndarray] = [r0.copy()]
    all_v: list[np.ndarray] = [v0.copy()]
    if t_min_tt < epoch_mjd_tt:
        ts = _leg_boundaries(epoch_mjd_tt, t_min_tt, h_days)
        nt, nr, nv = _integrate_leg(r0.copy(), v0.copy(), ts, dense_every, min_d2)
        all_t += nt
        all_r += nr
        all_v += nv
    if t_max_tt > epoch_mjd_tt:
        ts = _leg_boundaries(epoch_mjd_tt, t_max_tt, h_days)
        nt, nr, nv = _integrate_leg(r0.copy(), v0.copy(), ts, dense_every, min_d2)
        all_t += nt
        all_r += nr
        all_v += nv
    order = np.argsort(np.asarray(all_t))
    return DenseTrajectory(
        node_t=np.asarray(all_t)[order],
        node_r=np.stack(all_r)[order],
        node_v=np.stack(all_v)[order],
        min_planet_dist_au=np.sqrt(min_d2),
    )


def predict_dense(
    traj: DenseTrajectory,
    orbit_idx: np.ndarray,
    mjd_utc: np.ndarray,
    h_mag: np.ndarray | float | None = None,
    g_slope: np.ndarray | float | None = None,
    *,
    light_time_iterations: int = 2,
) -> dict[str, np.ndarray]:
    """Geocentric astrometric prediction for pairs ``(orbit_idx[i], mjd_utc[i])``.

    The perturbed twin of :func:`itf_linker.attrib.core.predict`: identical epoch
    conventions (UTC in, TT internally), identical light-time iteration, and the
    observable arithmetic is literally the same function
    (:func:`~itf_linker.attrib.core.observables_from_states`).
    """
    mjd_utc = np.atleast_1d(np.asarray(mjd_utc, dtype=float))
    idx = np.atleast_1d(np.asarray(orbit_idx, dtype=np.intp))
    e_pos, e_vel = earth_heliocentric_posvel(mjd_utc)
    t_tt = mjd_utc + TT_MINUS_UTC_DAYS
    tau = np.zeros(mjd_utc.shape[0])
    for _ in range(max(1, light_time_iterations) + 1):
        r_obj, v_obj = traj.state_at(t_tt - tau, idx)
        delta_vec = r_obj - e_pos
        tau = np.linalg.norm(delta_vec, axis=1) / C_AU_PER_DAY
    h_arr = None
    if h_mag is not None:
        # Arrays pass through (NaN entries yield NaN v_pred, silently and correctly);
        # scalars broadcast to the pair count.
        h_arr = np.broadcast_to(np.atleast_1d(np.asarray(h_mag, dtype=float)),
                                (mjd_utc.shape[0],))
    g_arr = 0.15 if g_slope is None else g_slope
    out = observables_from_states(r_obj, v_obj, e_pos, e_vel, h_arr, g_arr)
    out["encounter"] = traj.encounter[idx]
    return out
