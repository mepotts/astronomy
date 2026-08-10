"""Spectral window function and alias structure of the CD-35 2722 B cadence.

This is M4, and it needs **no radial velocities at all** -- only the times at which the
target was observed. That is what makes it the one piece of the reproduction that can be
done before `viper` runs.

The preprint states the open question plainly:

    "There are 4 possible solutions at periods of 14 days, 70 days, 88 days, and 115 days.
     These periods are all aliases of each other with our current sampling, due to the two
     sets of observations being almost exactly a year apart."

An alias pair satisfies ``f_alias = f_true +/- m * f_sampling``. If the four candidate
periods really are one signal seen through a yearly window, they must lie on that comb --
and which one a periodogram prefers is then a property of the sampling, not of the data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

YEAR_D = 365.25
SIDEREAL_DAY_D = 0.99726957


def window_function(times_d: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Normalised spectral window ``|W(f)| = |mean(exp(-2*pi*i*f*t))|``.

    Peaks mark the frequencies at which the sampling itself injects power. A peak at
    1/365.25 d^-1 is what turns one true signal into a comb of yearly aliases.
    """
    t = np.asarray(times_d, dtype=float)
    t = t - t.mean()
    phase = np.exp(-2j * np.pi * np.outer(np.asarray(freqs, float), t))
    return np.abs(phase.mean(axis=1))


def alias_frequencies(f_true: float, f_sampling: float, orders: int = 30) -> np.ndarray:
    """The comb ``f_true +/- m * f_sampling`` for m = 1..orders, positive frequencies only."""
    m = np.arange(1, orders + 1)
    out = np.concatenate([f_true + m * f_sampling, f_true - m * f_sampling])
    return np.sort(out[out > 0])


@dataclass
class AliasMatch:
    """One candidate period, tested against the comb built on another."""

    period_d: float
    order: int
    """``m`` in ``f = f_true +/- m * f_sampling``. 0 means it *is* the reference."""
    implied_sampling_period_d: float
    """The sampling period this pairing implies, if the alias relation is taken as exact."""
    period_error_d: float
    """How far the comb tooth lands from the candidate, in days."""


def match_alias_comb(
    candidates_d: list[float], reference_d: float, f_sampling: float, orders: int = 40
) -> list[AliasMatch]:
    """For each candidate period, find the comb order that best explains it.

    Reported as a *period* error rather than a frequency error because that is the quantity
    the paper quotes and the quantity a reader can check by eye.
    """
    f_ref = 1.0 / reference_d
    out: list[AliasMatch] = []
    for p in candidates_d:
        f = 1.0 / p
        if np.isclose(f, f_ref):
            out.append(AliasMatch(p, 0, np.inf, 0.0))
            continue
        m_real = (f - f_ref) / f_sampling
        m = round(m_real)
        if m == 0:
            out.append(AliasMatch(p, 0, np.inf, abs(p - reference_d)))
            continue
        f_pred = f_ref + m * f_sampling
        out.append(
            AliasMatch(
                period_d=p,
                order=m,
                implied_sampling_period_d=abs(m / (f - f_ref)),
                period_error_d=abs(p - 1.0 / f_pred) if f_pred > 0 else np.inf,
            )
        )
    return out


def season_split(times_d: np.ndarray, min_gap_d: float = 100.0) -> list[np.ndarray]:
    """Split epochs into observing seasons at gaps longer than ``min_gap_d``."""
    t = np.sort(np.asarray(times_d, float))
    idx = np.where(np.diff(t) > min_gap_d)[0]
    return np.split(t, idx + 1)


def season_separation_d(times_d: np.ndarray, min_gap_d: float = 100.0) -> float | None:
    """Mean-to-mean separation of the first two seasons -- the paper's "~1 year"."""
    seasons = season_split(times_d, min_gap_d)
    if len(seasons) < 2:
        return None
    return float(seasons[1].mean() - seasons[0].mean())


# --- injection-recovery -------------------------------------------------------------------


def kepler_E(M: np.ndarray, e: float, tol: float = 1e-10, itmax: int = 100) -> np.ndarray:
    """Solve Kepler's equation by Newton iteration. Vectorised over mean anomaly."""
    E = M + e * np.sin(M)
    for _ in range(itmax):
        d = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= d
        if np.max(np.abs(d)) < tol:
            break
    return E


def keplerian_rv(
    t: np.ndarray, period: float, k: float, ecc: float = 0.0,
    omega: float = 0.0, tp: float = 0.0,
) -> np.ndarray:
    """Radial velocity of a single Keplerian, in the same units as ``k``."""
    m = 2 * np.pi * (np.asarray(t, float) - tp) / period
    if ecc < 1e-8:
        return k * np.cos(m + omega)
    e_anom = kepler_E(np.mod(m, 2 * np.pi), ecc)
    nu = 2 * np.arctan2(np.sqrt(1 + ecc) * np.sin(e_anom / 2),
                        np.sqrt(1 - ecc) * np.cos(e_anom / 2))
    return k * (np.cos(nu + omega) + ecc * np.cos(omega))


def gls(t: np.ndarray, y: np.ndarray, dy: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Generalised Lomb-Scargle power (astropy's implementation, floating mean)."""
    from astropy.timeseries import LombScargle

    return LombScargle(t, y, dy).power(freqs)


def fit_and_remove_sinusoid(
    t: np.ndarray, y: np.ndarray, dy: np.ndarray, period: float
) -> np.ndarray:
    """Least-squares removal of a circular signal at a *fixed* period, plus an offset.

    Deliberately a sinusoid and not a full Keplerian: this models what happens when a
    slightly imperfect primary model is subtracted, which is the mechanism under test.
    """
    w = 1.0 / np.asarray(dy, float) ** 2
    ph = 2 * np.pi * np.asarray(t, float) / period
    a = np.column_stack([np.cos(ph), np.sin(ph), np.ones_like(t)])
    aw = a * w[:, None]
    coef = np.linalg.lstsq(a.T @ aw, aw.T @ y, rcond=None)[0]
    return y - a @ coef


def recover_secondary(
    t: np.ndarray, rng: np.random.Generator, *,
    primary_period: float, primary_k: float,
    secondary_period: float | None, secondary_k: float,
    noise_ms: float, freqs: np.ndarray, candidates_d: tuple[float, ...],
) -> tuple[float, float, float]:
    """One trial: inject, subtract the primary, and report the winning candidate period.

    Returns ``(winning_period, its_power, max_power_anywhere)``. The winner alone measures
    how often the *sampling* picks the answer; the powers say whether the pick was
    significant at all, which matters for the no-injection control.
    """
    dy = np.full(t.size, noise_ms)
    y = keplerian_rv(t, primary_period, primary_k, tp=rng.uniform(0, primary_period))
    if secondary_period is not None:
        y = y + keplerian_rv(t, secondary_period, secondary_k,
                             tp=rng.uniform(0, secondary_period))
    y = y + rng.normal(0.0, noise_ms, t.size)

    resid = fit_and_remove_sinusoid(t, y, dy, primary_period)
    power = gls(t, resid, dy, freqs)
    # Search a window of +/- half a GLS peak width (1/T) around each candidate. A narrower
    # window samples the tail rather than the peak; a wider one lets neighbouring aliases,
    # which here sit only ~1.2 peak widths apart, claim each other's power.
    half = 0.5 / (t.max() - t.min())
    best = {}
    for c in candidates_d:
        sel = np.abs(freqs - 1.0 / c) <= half
        best[c] = power[sel].max() if sel.any() else 0.0
    winner = max(best, key=best.get)
    return winner, float(best[winner]), float(power.max())
