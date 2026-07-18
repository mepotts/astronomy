"""Gaia DR3 parallax zero-point correction — the #1 science gap closed.

Gaia DR3 parallaxes carry a magnitude-, colour-, and ecliptic-latitude-dependent
systematic offset with a global mean of about **-17 micro-arcsec** (parallaxes are
biased *too small*, i.e. stars look *too far*). At the few-hundred-pc to few-kpc
distances that dominate the SN 1987A ellipsoid crossings, that offset moves the inferred
geocentric distance enough to shift a star's crossing epoch by ~0.7-4.5 yr — larger than
the +/-1-1.6 yr statistical windows the pipeline already reports. Applying the correction
BEFORE inverting ``distance = 1000 / parallax`` is therefore mandatory for honest epochs.

Reference / method
------------------
Lindegren, L., Bastian, U., Biermann, M., et al. 2021, "Gaia Early Data Release 3:
Parallax bias versus magnitude, colour, and position", A&A 649, A4 (DOI
10.1051/0004-6361/202039653). We use the authors' official reference implementation, the
``gaiadr3-zeropoint`` package (``from zero_point import zpt``), which evaluates the Z5/Z6
basis-function interpolation over the published coefficient tables. The correction is
applied as::

    parallax_corrected = parallax_catalogue - Z(G, nu_eff, pseudocolour, ecl_lat, solved)

where ``Z`` is the (typically negative) offset in mas, so the corrected parallax is
*larger* and the inferred distance *smaller*.

Required Gaia input columns (all in ``gaiadr3.gaia_source``; see DATA-SOURCES.md S2):
    phot_g_mean_mag              apparent G magnitude
    nu_eff_used_in_astrometry    effective wavenumber, 5-parameter (31) solutions
    pseudocolour                 effective wavenumber, 6-parameter (95) solutions
    ecl_lat                      ecliptic latitude (deg) -> sin(beta) term
    astrometric_params_solved    3 (2p, uncorrectable), 31 (5p), or 95 (6p)

Validity domain (Lindegren 2021): 6 < G < 21, 1.1 < nu_eff < 1.9, 1.24 < pseudocolour <
1.72. Outside it the correction is undefined; we return NaN there and the pipeline falls
back to the uncorrected parallax (never silently invents a correction).

Note on numpy>=2: ``gaiadr3-zeropoint`` 0.1.0 calls ``np.can_cast`` on Python scalars,
which NEP 50 forbids. We sidestep it by always passing numpy arrays into ``zpt.get_zpt``
(the array code path skips that check), so the correction works unmodified under numpy 2.
"""

from __future__ import annotations

import warnings

import numpy as np

# Documented global mean of the DR3 parallax zero-point (Lindegren et al. 2021).
GAIA_DR3_MEAN_ZEROPOINT_MAS: float = -0.017  # ~ -17 micro-arcsec

# astrometric_params_solved codes for which a zero-point is defined.
_SOLVED_5P: int = 31
_SOLVED_6P: int = 95

# Lazily-initialised handle to the loaded coefficient tables (idempotent).
_TABLES_LOADED: bool = False


def _zpt():
    """Import ``zero_point.zpt`` and load its coefficient tables once (lazily).

    Kept lazy so importing this module (and running ``--help`` / the offline pipeline
    without the correction) does not require the package to be importable.
    """
    global _TABLES_LOADED
    try:
        from zero_point import zpt
    except ImportError as exc:  # pragma: no cover - exercised only without the dep
        raise ImportError(
            "The Gaia DR3 parallax zero-point correction needs the 'gaiadr3-zeropoint' "
            "package (import name 'zero_point'). Install it with "
            "`pip install gaiadr3-zeropoint`, or pass --no-zeropoint to skip the "
            "correction (epochs then carry the ~-17 uas DR3 bias). See "
            "src/seti_ellipsoid_broker/zeropoint.py for the citation."
        ) from exc
    if not _TABLES_LOADED:
        zpt.load_tables()
        _TABLES_LOADED = True
    return zpt


def _as_float_array(x) -> np.ndarray:
    """1-D float array (NaN for None); the shape drives the whole computation."""
    arr = np.atleast_1d(np.asarray(x, dtype=float))
    return arr


def parallax_zeropoint(
    phot_g_mean_mag,
    nu_eff_used_in_astrometry,
    pseudocolour,
    ecl_lat,
    astrometric_params_solved,
):
    """Gaia DR3 parallax zero-point offset ``Z`` in mas (Lindegren et al. 2021).

    Returns the offset(s) to SUBTRACT from the catalogue parallax. Scalar in -> float out,
    array in -> ndarray out. NaN where the correction is undefined: 2-parameter solutions
    (``astrometric_params_solved`` not in {31, 95}) and sources outside the calibrated
    magnitude/colour domain.

    The five arguments are the Gaia columns of the same name; ``nu_eff_used_in_astrometry``
    is used for 5-parameter (31) sources and ``pseudocolour`` for 6-parameter (95) sources,
    so the unused one may be NaN/None for a given source (as in the catalogue).
    """
    zpt = _zpt()
    g = _as_float_array(phot_g_mean_mag)
    nu = _as_float_array(nu_eff_used_in_astrometry)
    pc = _as_float_array(pseudocolour)
    ecl = _as_float_array(ecl_lat)
    solved = _as_float_array(astrometric_params_solved)

    shapes = {a.shape for a in (g, nu, pc, ecl, solved)}
    if len(shapes) != 1:
        raise ValueError(
            f"parallax_zeropoint inputs must share one shape; got {sorted(shapes)}"
        )

    out = np.full(g.shape, np.nan, dtype=float)
    correctable = (solved == _SOLVED_5P) | (solved == _SOLVED_6P)
    if np.any(correctable):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # out-of-range -> NaN (via _warnings=False)
            z = zpt.get_zpt(
                g[correctable],
                nu[correctable],
                pc[correctable],
                ecl[correctable],
                solved[correctable].astype(int),
                _warnings=False,
            )
        out[correctable] = np.asarray(z, dtype=float)

    if np.isscalar(phot_g_mean_mag) or np.ndim(phot_g_mean_mag) == 0:
        return float(out[0])
    return out


def apply_parallax_zeropoint(
    parallax_mas,
    phot_g_mean_mag,
    nu_eff_used_in_astrometry,
    pseudocolour,
    ecl_lat,
    astrometric_params_solved,
    *,
    fallback_to_uncorrected: bool = True,
):
    """Zero-point-corrected parallax in mas: ``parallax - Z`` (Lindegren et al. 2021).

    ``Z`` is the (usually negative) offset from :func:`parallax_zeropoint`, so the returned
    parallax is typically slightly LARGER than the catalogue value (star slightly closer).
    Scalar in -> float out; array in -> ndarray out.

    Where ``Z`` is undefined (2p solutions / outside the calibrated domain) and
    ``fallback_to_uncorrected`` is True (default), the ORIGINAL parallax is returned
    unchanged rather than NaN, so a star is never dropped merely because it sits outside
    the calibration box — the correction is simply not applied there. Set it False to get
    NaN and drop such sources explicitly.
    """
    parallax = _as_float_array(parallax_mas)
    z = parallax_zeropoint(
        phot_g_mean_mag,
        nu_eff_used_in_astrometry,
        pseudocolour,
        ecl_lat,
        astrometric_params_solved,
    )
    z = np.atleast_1d(np.asarray(z, dtype=float))
    if z.shape != parallax.shape:
        raise ValueError(
            f"parallax shape {parallax.shape} != zero-point shape {z.shape}"
        )
    corrected = parallax - z
    if fallback_to_uncorrected:
        corrected = np.where(np.isnan(z), parallax, corrected)

    if np.isscalar(parallax_mas) or np.ndim(parallax_mas) == 0:
        return float(corrected[0])
    return corrected
