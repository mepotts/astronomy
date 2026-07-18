"""SN 1987A SETI Ellipsoid geometry — the scientific core of the broker.

The constants here are REAL and load-bearing (DATA-SOURCES.md S5). M1 implements the
crossing math: `signed_offset` (the signed distance of a star from the expanding shell)
and `crossing_epoch` (the decimal year a star sits on the shell). Both are pure functions
of a star's geometry and use astropy `SkyCoord`/`units`/`Time`.

Modeling choices (made explicit because the precise geometry is the project's scientific
core — DATA-SOURCES.md S5 / SPEC.md):

  Foci of the ellipsoid are {Earth, SN 1987A}, baseline ``d`` = Earth->SN ~= 51.4 kpc.
  For a star at geocentric distance ``r_E`` and angular separation ``theta`` from SN 1987A
  (as seen from Earth), its distance from the supernova follows the law of cosines:

      d2 = sqrt(r_E^2 + d^2 - 2 * r_E * d * cos(theta))                       (SN -> star)

  The SETI ellipsoid shell at elapsed time ``t`` (years since Earth *observed* SN 1987A on
  1987-02-23) is the locus where the total path SN -> star -> Earth equals the direct path
  SN -> Earth plus the elapsed light-travel time:

      r_E + d2  =  d + c * t                                                  (shell)

  We therefore define the SIGNED OFFSET (light-years) as how far the expanding shell front
  has advanced *beyond* the star's total light-travel path -- i.e. the shell radius minus the
  star's path length:

      S(t) = (d + c * t) - (r_E + d2)

  Sign convention (asserted by the tests):
    * S < 0  -> the expanding shell has not yet reached the star  ("inside",  not yet crossed)
    * S = 0  -> the star is exactly on the shell                   (a crossing happens now)
    * S > 0  -> the shell has already swept past the star          ("outside", already crossed)
  Because the shell term ``d + c * t`` grows at exactly c, S(t) increases by c per year
  (1 ly/yr), so the crossing date is fixed by the star's geometry alone.

  The CROSSING EPOCH solves S = 0:

      c * t_cross = r_E + d2 - d   ==>   t_cross_year = ref_year + (r_E + d2 - d) / c

  UNITS: we work internally in light-years for distance and years for time, so c = 1 ly/yr
  and ``c * t`` is numerically the elapsed years. This keeps the arithmetic exact and unit-
  checked via astropy on the way in.

  This is the standard SETI-ellipsoid construction (Davenport 2022; Nilipour et al. 2023):
  to first order ``t_cross - ref ~= r_E * (1 - cos theta) / c``, which peaks for nearby,
  modest-angle stars in the ~2026-2028 window (DATA-SOURCES.md S5, the documented sunset).

  Out of scope for v0 (documented, not modeled here): stellar proper motion / 3D space
  motion of the star between the SN epoch and now, light-bending, and Bailer-Jones
  geometric distances (we invert parallax under the quality cuts). These are M2+ refinements
  and are intentionally omitted so the offline core stays deterministic and dependency-light.
"""

from __future__ import annotations

from typing import overload

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

# --- SN 1987A reference geometry (real values) ------------------------------------

SN1987A_RA_DEG: float = 83.86658      # 05h 35m 27.99s  (ICRS, near 30 Doradus, LMC)
SN1987A_DEC_DEG: float = -69.26961    # -69d 16m 10.6s
SN1987A_DISTANCE_KPC: float = 51.4    # Earth -> SN 1987A baseline (= inter-foci 2C)
SN1987A_DISTANCE_LY: float = 167_700.0  # ~168,000 ly
REFERENCE_EPOCH: str = "1987-02-23"   # date SN 1987A light was OBSERVED at Earth

# Semi-major axis grows at c/2: half a light-year of semi-major axis per calendar year.
SEMI_MAJOR_AXIS_GROWTH_LY_PER_YR: float = 0.5

# Quality-cut thresholds carried from Nilipour/Gallay (also enforced in ranking.py).
RUWE_MAX: float = 1.4
PARALLAX_OVER_ERROR_MIN: float = 5.0

# Flag stars whose crossing-epoch uncertainty window is tighter than this (years).
CROSSING_WINDOW_FLAG_YR: float = 2.0


# --- Cached unit conversions (computed once; astropy keeps the units honest) -------

_KPC_TO_LY: float = (1.0 * u.kpc).to_value(u.lyr)
_PC_TO_LY: float = (1.0 * u.pc).to_value(u.lyr)
_D_LY: float = SN1987A_DISTANCE_KPC * _KPC_TO_LY  # Earth->SN baseline in light-years


def reference_epoch_jyear() -> float:
    """Decimal (Julian) year of the SN 1987A observation epoch (``REFERENCE_EPOCH``)."""
    return Time(REFERENCE_EPOCH, format="iso", scale="utc").jyear


# Module-level constant for the reference epoch as a decimal year (used in the math below).
REFERENCE_EPOCH_JYEAR: float = reference_epoch_jyear()


def sn1987a_skycoord(distance: bool = False) -> SkyCoord:
    """SkyCoord of SN 1987A. With ``distance=True`` it carries the 51.4 kpc baseline."""
    if distance:
        return SkyCoord(
            ra=SN1987A_RA_DEG * u.deg,
            dec=SN1987A_DEC_DEG * u.deg,
            distance=SN1987A_DISTANCE_KPC * u.kpc,
            frame="icrs",
        )
    return SkyCoord(ra=SN1987A_RA_DEG * u.deg, dec=SN1987A_DEC_DEG * u.deg, frame="icrs")


def separation_from_sn_deg(coord: SkyCoord) -> np.ndarray | float:
    """Angular separation (degrees) of ``coord`` from SN 1987A, as seen from Earth."""
    sep = coord.separation(sn1987a_skycoord())
    return sep.to_value(u.deg)


# --- The geometry ------------------------------------------------------------------

def _resolve_geometry(
    distance_pc, sep_deg
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize the two call styles into (distance_pc, sep_deg) numpy arrays.

    Accepts either:
      * a single ``SkyCoord`` (carrying a distance) in ``distance_pc`` and ``sep_deg=None``
        -> distance and angular separation from SN 1987A are read off the coordinate; or
      * scalar / array-like ``distance_pc`` (parsecs) and ``sep_deg`` (degrees).
    """
    if isinstance(distance_pc, SkyCoord):
        if sep_deg is not None:
            raise TypeError("pass either a SkyCoord or (distance_pc, sep_deg), not both")
        coord = distance_pc
        if coord.distance is None or np.any(coord.distance.value == 0):
            raise ValueError("SkyCoord must carry a non-zero distance")
        dist = np.atleast_1d(coord.distance.to_value(u.pc)).astype(float)
        sep = np.atleast_1d(separation_from_sn_deg(coord)).astype(float)
        return dist, sep
    if sep_deg is None:
        raise TypeError("sep_deg is required when distance_pc is not a SkyCoord")
    dist = np.atleast_1d(np.asarray(distance_pc, dtype=float))
    sep = np.atleast_1d(np.asarray(sep_deg, dtype=float))
    _validate_nonneg(dist, sep)
    return np.broadcast_arrays(dist, sep)[0].copy(), np.broadcast_arrays(dist, sep)[1].copy()


def _validate_nonneg(distance_pc: np.ndarray, sep_deg: np.ndarray) -> None:
    if np.any(distance_pc < 0):
        raise ValueError(f"distance_pc must be non-negative, got {distance_pc!r}")
    if np.any(sep_deg < 0):
        raise ValueError(f"sep_deg must be non-negative, got {sep_deg!r}")


def _path_excess_ly(distance_pc: np.ndarray, sep_deg: np.ndarray) -> np.ndarray:
    """``(r_E + d2) - d`` in light-years — the 'ellipsoid depth' for each star.

    This is exactly ``c * (t_cross - ref)`` and equals the light-years the shell must grow
    (beyond the direct SN->Earth path) to reach the star.
    """
    r_ly = distance_pc * _PC_TO_LY
    theta = np.radians(sep_deg)
    d2 = np.sqrt(r_ly**2 + _D_LY**2 - 2.0 * r_ly * _D_LY * np.cos(theta))
    return (r_ly + d2) - _D_LY


def _unwrap(arr: np.ndarray, scalar_in: bool):
    """Return a Python float if the original input was scalar, else the numpy array."""
    if scalar_in:
        return float(arr[0])
    return arr


@overload
def crossing_epoch(distance_pc: SkyCoord) -> float | np.ndarray: ...
@overload
def crossing_epoch(distance_pc: float, sep_deg: float) -> float: ...


def crossing_epoch(distance_pc, sep_deg=None):
    """Decimal year at which a star lies on the current SN 1987A ellipsoid shell.

    Solves ``r_E + d2 = d + c * t_cross`` (see module docstring) and returns the crossing
    epoch as a decimal year. Accepts either a ``SkyCoord`` (carrying distance) or
    ``(distance_pc, sep_deg)`` scalars/arrays; returns a float for scalar input, else an
    array.
    """
    scalar_in = (not isinstance(distance_pc, SkyCoord)) and np.isscalar(distance_pc) \
        and (sep_deg is None or np.isscalar(sep_deg))
    if isinstance(distance_pc, SkyCoord):
        scalar_in = distance_pc.isscalar
    dist, sep = _resolve_geometry(distance_pc, sep_deg)
    years = REFERENCE_EPOCH_JYEAR + _path_excess_ly(dist, sep)  # c = 1 ly/yr
    return _unwrap(years, scalar_in)


@overload
def signed_offset(distance_pc: SkyCoord, sep_deg: None, epoch_jyear: float) -> float | np.ndarray: ...
@overload
def signed_offset(distance_pc: float, sep_deg: float, epoch_jyear: float) -> float: ...


def signed_offset(distance_pc, sep_deg, epoch_jyear):
    """Signed distance (light-years) of a star from the ellipsoid shell at ``epoch_jyear``.

    ``S(t) = (d + c * t) - (r_E + d2)``.  Negative => the shell has not yet reached the star
    (not yet crossed); positive => the shell has passed it (already crossed); ~0 => on the
    shell (crossing now). S grows at +c (1 ly/yr) with time. See the module docstring for the
    sign convention.
    """
    if isinstance(distance_pc, SkyCoord):
        scalar_in = distance_pc.isscalar
        dist, sep = _resolve_geometry(distance_pc, None)
    else:
        scalar_in = np.isscalar(distance_pc) and np.isscalar(sep_deg)
        dist, sep = _resolve_geometry(distance_pc, sep_deg)
    elapsed = np.asarray(epoch_jyear, dtype=float) - REFERENCE_EPOCH_JYEAR  # years = c*t (ly)
    s = elapsed - _path_excess_ly(dist, sep)
    return _unwrap(np.atleast_1d(s), scalar_in)


def crossing_window_years(distance_pc, sep_deg, parallax_over_error: float):
    """Symmetric +/- uncertainty (years) on the crossing epoch from the parallax error.

    The dominant uncertainty in v0 is the geocentric distance, whose fractional error is
    ``1 / parallax_over_error`` (distance ~= 1000/parallax, so d(distance)/distance equals
    the fractional parallax error). We propagate that into the ellipsoid depth:

        sigma_t ~= |d(path_excess)/d(r_E)| * sigma_r   with   sigma_r = r_E / (p/sigma_p)

    and ``d(path_excess)/d(r_E) = 1 - (d * cos theta - r_E) / d2`` (-> ``1 - cos theta`` for
    r_E << d). Reported in years (c = 1 ly/yr). Tighter parallax => tighter window.
    """
    if parallax_over_error <= 0:
        raise ValueError("parallax_over_error must be positive")
    dist, sep = _resolve_geometry(distance_pc, sep_deg)
    r_ly = dist * _PC_TO_LY
    theta = np.radians(sep)
    d2 = np.sqrt(r_ly**2 + _D_LY**2 - 2.0 * r_ly * _D_LY * np.cos(theta))
    # d(path_excess)/d(r_E):
    dpath_dr = 1.0 - (_D_LY * np.cos(theta) - r_ly) / d2
    sigma_r = r_ly / float(parallax_over_error)
    sigma_t = np.abs(dpath_dr) * sigma_r  # years
    scalar_in = np.isscalar(distance_pc) and np.isscalar(sep_deg)
    return _unwrap(np.atleast_1d(sigma_t), scalar_in)
