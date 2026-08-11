"""Per-order screening and recombination of viper RVs -- and the ceiling on what that buys.

**M9 tested a hypothesis and falsified it.** The hypothesis: Hoy et al. state that orders
without enough telluric lines produce "highly erratic results" and must be excluded, M2
applied no such screen, and per-order rms in M2 ranges from 1082 to 4130 m/s -- so order
screening might explain a good part of the 25-60x precision shortfall.

It does not, and the margin is not close. The best screen that **survives the positive
control** takes the combined scatter from **823 m/s to 776 m/s** -- a 6% gain against a
factor of 25 needed. The reason is arithmetic and is the most useful thing this module
records:

    median per-order rms   = 2133 m/s over 10 orders
    naive sqrt(10) floor   =  674 m/s
    viper's actual output  =  823 m/s

**The combination is already working as expected.** The shortfall is entirely in *per-order*
precision, which sits ~100x above the photon limit. No weighting scheme can fix a
systematic that is present in every order.

What M9 did establish, and what this module implements:

1. **viper's per-order formal errors are not merely untrustworthy, they are actively
   harmful.** Weighting by inverse formal variance gives **2620 m/s** against 823 m/s for a
   plain mean, because the single worst order (order 8: rms 4130 m/s) carries the *smallest*
   formal error (101 m/s) and therefore the largest weight. M2 recorded that formal errors
   disagree with scatter by 2-42x; M9 measures what acting on them costs.
2. **One order is pathological and dropping it is safe.** Order 8 (1577.7 nm) has 6x the fit
   rms of any other order and 5x the telluric-abundance error. Dropping it improves the
   target *and* the control.
3. **Two plausible screens fail the control**, and would have looked like successes on the
   target alone. See ``SCREEN_RESULTS``.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

Weighting = Literal["equal", "formal", "empirical"]

PATHOLOGICAL_ORDERS: tuple[int, ...] = (8,)
"""Orders dropped by default. Only order 8 qualifies, and only on evidence:

============  =========  ==========  ============  ===========
order         rms (m/s)  fit prms    e_atm0        med e_rv
============  =========  ==========  ============  ===========
**8**         **4130**   **30.39**   **23.4**      **101**
next worst    3954       7.90        8.76          1221
median        2133       4.94        4.51          446
============  =========  ==========  ============  ===========

Dropping it is worth 823 -> 776 m/s. Small, but it is the only change here that improves
the target *and* the control, so it is the only one adopted.

It is simultaneously the worst-behaved order and the most confidently weighted one. Adding
further orders to this tuple requires re-running the control -- see ``SCREEN_RESULTS`` for
what happens when a screen is adopted without doing so.
"""

SCREEN_RESULTS: dict[str, tuple[float, float, float]] = {
    # label: (CD-35 2722 B combined rms m/s, GJ 229 B control delta-chi2, control K m/s)
    "all orders, equal (viper as-run)": (823.1, 63.8, 6165.0),
    "all orders, inverse formal variance": (2620.0, 20.5, 5421.5),
    "drop order 8, equal": (775.5, 76.5, 5948.1),
    "drop order 8, empirical weights": (513.7, 5.8, 1825.3),
    "telluric-constrained orders only": (1141.8, 46.7, 3620.3),
}
"""Every screen tried, scored on the target **and** on the positive control.

Read the fourth row before trusting any reweighting. **Empirical weights** -- weight each
order by ``1/rms_order^2``, measured from the data -- give the **best number in the table**
on CD-35 2722 B (513.7 m/s, a 1.6x gain on viper's own output) and **destroy the control**:
delta-chi2 collapses from 63.8 to 5.8 and the recovered amplitude falls from 6165 to
1825 m/s on a binary whose existence is not in dispute.

The reason is circularity. For a target with a *real* signal, an order's scatter *is* the
signal, so weighting by inverse scatter systematically downweights exactly the orders
carrying it. On a target with no detected signal that pathology is invisible.

**This is the clearest vindication of HANDOFF's rule that the project has produced: never
report a result from this pipeline without re-running the control.** The screen that looked
best on the science target was the one that worked by deleting the answer.

The telluric screen -- keeping only orders where viper constrains the telluric abundance
(``|atm0| / e_atm0 >= 1``, orders 12/14/15/16) -- is the paper's own stated rule and also
fails: it makes the target *worse* (1142 m/s) and weakens the control (63.8 -> 46.7). Either our
per-order ``atm0`` errors do not mean what they appear to, or the rule cannot be applied
to the combined archive product. Recorded as measured, not resolved.
"""


TEMPLATE_RESULTS: dict[str, tuple[float, float, float]] = {
    # label: (CD-35 2722 B combined rms m/s, GJ 229 B control delta-chi2, control K m/s)
    "0 iterations, tpl_wave=initial (M2/M3 baseline)": (776.0, 76.5, 5948.0),
    "1 iteration, tpl_wave=tell": (852.0, 23.7, 2452.0),
    "2 iterations, tpl_wave=tell (the published recipe)": (620.0, 21.1, 2360.0),
}
"""M11: rebuilding the template the published way, scored on target and control.

**Self-templating absorbs the signal.** Recovered amplitude on GJ 229 B's undisputed
12.1-day binary collapses to **41% of correct after ONE iteration** (5948 -> 2452 m/s) and
does not recover. The template is built by co-adding the target's own spectra aligned by
RVs that were themselves measured against a template already containing the signal, so the
residual is baked in and later velocities are partly the star measured against itself.

CD-35 2722 B meanwhile appears to *improve* (776 -> 620 m/s), because that is what
suppression looks like on a target with no detected signal. It cannot be adopted.

Koehler et al. 2025 section 2.2 flags the hazard -- "the situation becomes more complex when
Doppler shifts are present... an alternative approach is required" -- and their alternative
(RV-correct before co-adding) is what viper implements and what was run. It was not
sufficient at this precision.

**Third change in a row that improved the target and failed the control**, after the two in
``SCREEN_RESULTS``. See ``M11-RESULTS.md``.
"""


@dataclass(frozen=True)
class OrderStats:
    order: int
    wavelength_nm: float
    rms_ms: float
    median_formal_err_ms: float
    median_fit_rms: float
    telluric_snr: float

    @property
    def error_ratio(self) -> float:
        """How badly the formal error understates the real scatter."""
        return self.rms_ms / self.median_formal_err_ms


def read_rvo(path: Path | str) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int]]:
    """Parse a viper ``*.rvo.dat``: returns (bjd, per-order RVs, per-order errors, orders)."""
    rows = [ln.split() for ln in Path(path).read_text(encoding="utf-8").strip().splitlines()]
    hdr, body = rows[0], rows[1:]
    col = {h: i for i, h in enumerate(hdr)}
    orders = sorted(int(h[2:]) for h in hdr if h.startswith("rv") and h[2:].isdigit())
    rv = np.array([[float(r[col[f"rv{o}"]]) for o in orders] for r in body])
    er = np.array([[float(r[col[f"e_rv{o}"]]) for o in orders] for r in body])
    bjd = np.array([float(r[col["BJD"]]) for r in body])
    return bjd, rv, er, orders


def read_par(path: Path | str) -> dict[int, dict[str, list[float]]]:
    """Parse a viper ``*.par.dat`` of per-epoch, per-order fit parameters.

    Blank lines separate epochs and must be dropped, or the row/column alignment silently
    shifts -- the file has 180 data rows (18 epochs x 10 orders) and 17 blank separators.
    """
    rows = [
        r for r in (ln.split() for ln in Path(path).read_text(encoding="utf-8").splitlines()) if r
    ]
    col = {h: i for i, h in enumerate(rows[0])}
    out: dict[int, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for r in rows[1:]:
        order = int(r[col["order"]])
        for key in ("rv", "e_rv", "wave0", "e_wave0", "atm0", "e_atm0", "ip0", "prms"):
            try:
                out[order][key].append(float(r[col[key]]))
            except (ValueError, KeyError):
                out[order][key].append(float("nan"))
    return out


def order_stats(rvo_path: Path | str, par_path: Path | str) -> list[OrderStats]:
    """Per-order diagnostics: scatter, formal error, fit quality, telluric constraint."""
    _, rv, er, orders = read_rvo(rvo_path)
    par = read_par(par_path)

    def med(vals: list[float]) -> float:
        arr = np.asarray(vals, float)
        arr = arr[np.isfinite(arr)]
        return float(np.median(arr)) if arr.size else float("nan")

    stats = []
    for i, o in enumerate(orders):
        col = rv[:, i]
        atm0, e_atm0 = med(par[o]["atm0"]), med(par[o]["e_atm0"])
        stats.append(
            OrderStats(
                order=o,
                wavelength_nm=med(par[o]["wave0"]) / 10.0,
                rms_ms=float(np.nanstd(col[np.isfinite(col)])),
                median_formal_err_ms=med(list(er[:, i])),
                median_fit_rms=med(par[o]["prms"]),
                telluric_snr=abs(atm0) / e_atm0 if e_atm0 > 0 else float("nan"),
            )
        )
    return stats


def combine(
    rv: np.ndarray,
    er: np.ndarray,
    orders: list[int],
    drop: tuple[int, ...] = PATHOLOGICAL_ORDERS,
    weighting: Weighting = "equal",
) -> np.ndarray:
    """Collapse per-order RVs to one RV per epoch.

    ``weighting`` defaults to ``"equal"`` deliberately. ``"formal"`` is worse than useless
    here (it triples the scatter) and ``"empirical"`` fails the positive control. Both are
    kept callable so the failures stay reproducible rather than becoming folklore.
    """
    idx = [i for i, o in enumerate(orders) if o not in drop]
    sub_rv, sub_er = rv[:, idx], er[:, idx]
    per_order_rms = np.array([np.nanstd(sub_rv[:, k]) for k in range(sub_rv.shape[1])])

    out = np.full(sub_rv.shape[0], np.nan)
    for j in range(sub_rv.shape[0]):
        row = sub_rv[j]
        # An order counts only if BOTH its RV and its error are finite and the error is
        # positive -- which is what viper itself does. Masking on the RV alone admits
        # orders viper discarded and shifts the plain mean from 823 to 878 m/s, i.e. it
        # silently stops reproducing M2's published run.
        mask = np.isfinite(row) & np.isfinite(sub_er[j]) & (sub_er[j] > 0)
        if mask.sum() < 2:
            continue
        if weighting == "formal":
            e = sub_er[j][mask]
            w = 1.0 / np.where(e > 0, e, np.inf) ** 2
        elif weighting == "empirical":
            w = 1.0 / per_order_rms[mask] ** 2
        else:
            w = np.ones(int(mask.sum()))
        out[j] = float(np.sum(w * row[mask]) / np.sum(w))
    return out


def combination_ceiling_ms() -> float:
    """Best combined precision from any screen that **passes the control**: 775.5 m/s.

    Measured, not estimated, and deliberately *not* the smallest number in
    ``SCREEN_RESULTS`` -- 513.7 m/s is lower and is an artefact of a screen that deletes
    the signal. Quoting the unvalidated minimum would overstate the achievable precision
    by 1.5x.

    Against the 31.44 m/s the detection needs this is **25x short**, essentially unchanged
    from M2's 823 m/s. Recombination is not a route to reproducing the measurement: that
    is M9's result and the reason this module exists.
    """
    return 775.5
