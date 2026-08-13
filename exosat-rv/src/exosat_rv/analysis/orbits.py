"""Independent Keplerian model comparison on the paper's *published* radial velocities.

This is the reproduction that matters, and it was nearly missed. M2 tried to re-derive RVs
from the archive spectra and fell 25-60x short of the precision needed, which said nothing
about whether the *conclusion* holds. But the preprint publishes its full RV table
(Table 2, "A Full RV dataset"), so the inference can be reproduced directly -- with a
different fitter, on the same numbers, exactly as SPEC promised.

Extraction and inference are separate claims. Failing to reproduce the first does not bear
on the second, and conflating them is how a reproduction attempt reports the wrong verdict.

Model selection here is BIC, not the paper's nested-sampling log evidence. ``delta BIC / 2``
approximates ``delta log Z`` well enough to compare against their numbers, and the agreement
is close (see M6-RESULTS), but it is an approximation and is labelled as one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import DATA
from .aliases import keplerian_rv

PUBLISHED_RVS = DATA / "published" / "hoy2026_table2_rvs.csv"
"""arXiv v1 table: 20 epochs, timestamps wrong by 0.87 d (M12 SS1.1). Kept for M6 continuity."""

PUBLISHED_RVS_NATURE = DATA / "published" / "hoy2026_nature_table2_rvs.csv"
"""Nature (published) table: 23 epochs over 851 d, corrected timestamps. Use this one."""


@dataclass
class RVSet:
    bjd: np.ndarray
    rv: np.ndarray
    erv: np.ndarray

    @property
    def baseline_d(self) -> float:
        return float(self.bjd.max() - self.bjd.min())


def load_published(path: Path | None = None, version: str = "nature") -> RVSet:
    """Read the digitised Table 2 (``version="nature"`` by default, ``"v1"`` for the preprint).

    Parsed by hand rather than with ``genfromtxt(names=True)``: the provenance header
    contains commas, which makes numpy miscount the columns.
    """
    default = PUBLISHED_RVS_NATURE if version == "nature" else PUBLISHED_RVS
    src = Path(path or default)
    rows = []
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "bjd")):
            continue
        b, r, e = line.split(",")
        rows.append((float(b), float(r), float(e)))
    a = np.array(rows, dtype=float)
    return RVSet(a[:, 0], a[:, 1], a[:, 2])


@dataclass
class FitResult:
    periods: tuple[float, ...]
    eccentric: bool
    neg_log_like: float
    n_params: int
    bic: float
    amplitudes: tuple[float, ...]
    jitter_ms: float
    ecc: float | None = None


def _neg_log_like(p, tt, rv, er, periods, eccentric) -> float:
    off, jit = p[0], abs(p[1])
    k, model = 2, np.full_like(tt, off)
    for period in periods:
        if eccentric:
            amp, tp, ecc, omega = p[k:k + 4]
            k += 4
            ecc = min(abs(ecc), 0.85)
        else:
            amp, tp = p[k:k + 2]
            k += 2
            ecc = omega = 0.0
        model = model + keplerian_rv(tt, period, abs(amp), ecc, omega, tp)
    s2 = er**2 + jit**2
    return 0.5 * float(np.sum((rv - model) ** 2 / s2 + np.log(2 * np.pi * s2)))


def fit_fixed_periods(
    data: RVSet, periods: tuple[float, ...], eccentric: bool = False,
    n_starts: int = 400, seed: int = 7,
) -> FitResult:
    """Maximum-likelihood fit with the period(s) held fixed and jitter free.

    Periods are fixed on purpose: letting them float makes every candidate slide into the
    same basin and destroys the comparison the paper actually made, which is between
    *specified* alias periods.
    """
    from scipy.optimize import minimize

    tt = data.bjd - data.bjd.min()
    rng = np.random.default_rng(seed)
    n_par = 2 + len(periods) * (4 if eccentric else 2)
    best = None
    for _ in range(n_starts):
        guess = [rng.normal(0, 50), abs(rng.normal(20, 10))]
        for period in periods:
            guess += [abs(rng.normal(200, 80)), rng.uniform(0, period)]
            if eccentric:
                guess += [rng.uniform(0, 0.5), rng.uniform(0, 2 * np.pi)]
        try:
            r = minimize(_neg_log_like, guess, args=(tt, data.rv, data.erv, periods, eccentric),
                         method="Nelder-Mead",
                         options={"maxiter": 20000, "maxfev": 20000,
                                  "xatol": 1e-6, "fatol": 1e-6})
        except Exception:  # noqa: BLE001,S112 - a failed start is skipped, not fatal
            continue
        if best is None or r.fun < best.fun:
            best = r
    if best is None:
        raise RuntimeError("no optimiser start converged")

    step = 4 if eccentric else 2
    amps = tuple(abs(best.x[2 + i * step]) for i in range(len(periods)))
    ecc = min(abs(best.x[4]), 0.85) if eccentric else None
    return FitResult(
        periods=periods, eccentric=eccentric, neg_log_like=float(best.fun), n_params=n_par,
        bic=float(2 * best.fun + n_par * np.log(len(data.rv))),
        amplitudes=amps, jitter_ms=float(abs(best.x[1])), ecc=ecc,
    )


def delta_logz_proxy(a: FitResult, b: FitResult) -> float:
    """``(BIC_b - BIC_a) / 2`` -- positive means ``a`` is favoured. Approximates dlogZ."""
    return (b.bic - a.bic) / 2.0
