"""Prove the Find_Orb build is correct, end to end, against an independent authority.

"It compiled" is not evidence that an orbit solver works. This module runs a closed loop:

1. ask **JPL Horizons** for astrometric RA/Dec of a *known* minor planet, as seen from a
   real observatory code, on a realistic set of nights;
2. write those positions as MPC 80-column astrometry;
3. fit them with the freshly built ``fo``;
4. ask Horizons for the object's **osculating elements at the exact epoch Find_Orb chose**
   and compare.

Step 4 is what makes this a test rather than a demonstration. Nothing about the truth
values comes from Find_Orb, and the epoch is not negotiated in advance -- Find_Orb picks
it, and Horizons is then asked about that instant.

Each target is fitted at two cadences (a ~9-day arc, matching the ITF population M1
actually fits, and a ~49-day arc where the orbit is heavily over-determined), and at each
cadence twice:

* **noise-free** -- residuals should collapse to the quantisation floor of the 80-column
  format (0.001s in RA, 0.01" in Dec) and the elements should match Horizons to many
  digits.
* **noisy** -- 0.30" Gaussian error per coordinate, fixed seed. This is the run that tests
  the *uncertainties*, which is what the MPC's sigma(a)/sigma(q)/sigma(i)/sigma(e) gate
  consumes.

Both runs declare the true per-coordinate error to Find_Orb with a ``#Posn sigma``
directive, so every case is judged on one uniform criterion: each element must lie within
4 of Find_Orb's *own* reported sigmas of the JPL value. A fixed absolute tolerance would
be meaningless over a 9-day arc, where the semimajor axis is genuinely undetermined
(sigma(a) ~ 0.1 AU) however good the astrometry is.

Network use is a read-only HTTPS GET against the public Horizons API. Nothing is submitted.
"""

from __future__ import annotations

import math
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from .. import config
from .findorb import FitResult, run_fo
from .mpcfmt import format_line
from .wsl import Shell, default_shell

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

_MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
}

_SOE, _EOE = "$$SOE", "$$EOE"
#: Horizons writes elements as ``EC= 2.29e-01`` but also ``A = 2.38e+00`` -- the space
#: before ``=`` is not optional in the format and must not be in the pattern.
_ELEM_RE = re.compile(r"\b([A-Z]{1,2})\s*=\s*([-+0-9.Ee]+)")
#: An ephemeris row starts with its timestamp; ``$$SOE`` blocks also contain cut-off
#: banners such as ``>..... Daylight Cut-off Requested .....<``.
_ROW_RE = re.compile(r"^\s*\d{4}-[A-Z][a-z]{2}-\d{2}\s")

#: Astrometric error injected in the noisy run, per coordinate, in arcseconds.
NOISE_ARCSEC = 0.30

#: Positional sigma declared on the noise-free runs, so Find_Orb's reported sigmas
#: describe the data it was actually given rather than the ~0.5" it assumes for
#: observatory 703.
#:
#: Not set to the format's true floor (RA to 0.001s = 0.015" x cos dec, Dec to 0.01"):
#: Find_Orb's weighted least-squares destabilises below about 0.05". Measured on the
#: 8-day Eros arc, holding the astrometry fixed and varying only this directive:
#:
#:     declared   used    RMS       a          sigma(a)
#:     0.01"     15/15   0.208"   3.330 AU     0.25
#:     0.02"     10/15   0.099"   3.452 AU     0.287
#:     0.05"     15/15   0.0037"  1.4576 AU    0.0106
#:     0.1"      15/15   0.0036"  1.4575 AU    0.0207
#:     0.5"      15/15   0.0036"  1.4575 AU    0.103     (truth a = 1.45822 AU)
#:
#: At and above 0.05" the solution is stable and sigma(a) scales linearly with the
#: declared sigma, exactly as a correct covariance must. Below it the normal matrix
#: (weights go as 1/sigma^2) is ill-conditioned and the fit diverges. Real astrometry is
#: never this precise, so the limit does not bind in practice -- but it does mean a
#: too-optimistic sigma is a way to silently break a fit.
CLEAN_SIGMA_ARCSEC = 0.05

#: Minimum elevation for a sample to be treated as observable (airmass ~2.4).
ELEV_CUT_DEG = 25


@dataclass(frozen=True, slots=True)
class SelfTestTarget:
    """A known object to re-derive.

    ``command`` is a Horizons target specifier and **must** carry the trailing ``;`` that
    forces a small-body lookup. Without it, ``COMMAND='7'`` resolves to *Uranus*, and the
    test quietly compares a fit of Uranus against the elements of Uranus -- a round trip
    that proves nothing about asteroid orbits.
    """

    command: str
    label: str
    desig: str          # <=7 chars: goes in columns 6-12
    obscode: str = "703"
    start_date: str = "2024-01-05"
    n_nights: int = 5
    night_gap_days: int = 2
    obs_per_night: int = 3
    search_days: int = 150   # window scanned for observable nights; see run_selftest

    def with_cadence(self, n_nights: int, night_gap_days: int) -> SelfTestTarget:
        return SelfTestTarget(
            command=self.command,
            label=self.label,
            desig=self.desig,
            obscode=self.obscode,
            start_date=self.start_date,
            n_nights=n_nights,
            night_gap_days=night_gap_days,
            obs_per_night=self.obs_per_night,
            search_days=self.search_days,
        )


#: Deliberately spread across dynamical classes -- a solver can be right for a main-belt
#: orbit and wrong for a Trojan, and the ITF contains both.
DEFAULT_TARGETS: tuple[SelfTestTarget, ...] = (
    SelfTestTarget(command="433;", label="(433) Eros [NEO]", desig="T433"),
    SelfTestTarget(command="7;", label="(7) Iris [inner main belt]", desig="T7"),
    SelfTestTarget(command="588;", label="(588) Achilles [Jupiter Trojan]", desig="T588"),
)

#: The regime M1 actually fits: 5 nights at 2-day intervals, 3 detections a night -- a
#: ~9-day arc, against the 1,046 gated ITF designations' median of 7 days.
COMPACT_CADENCE = (5, 2)

#: A much wider arc: 8 nights at weekly intervals, ~49 days. Not representative of the
#: ITF, but it is where an orbit is over-determined enough that clean data pins every
#: element to many digits -- the strongest available statement that the build is correct.
WIDE_CADENCE = (8, 7)


class HorizonsError(RuntimeError):
    pass


def _horizons(params: dict[str, str], timeout: float = 180.0) -> str:
    resp = requests.get(
        HORIZONS_URL,
        params={"format": "text", **params},
        headers={"User-Agent": config.USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    if "$$SOE" not in resp.text:
        raise HorizonsError(f"unexpected Horizons reply: {resp.text[:400]}")
    return resp.text


def _rows(text: str) -> list[str]:
    body = text.split(_SOE, 1)[1].split(_EOE, 1)[0]
    return [ln for ln in body.splitlines() if ln.strip()]


def _ephem_rows(text: str) -> list[str]:
    return [ln for ln in _rows(text) if _ROW_RE.match(ln)]


def _hms_to_deg(token: str) -> float:
    h, m, s = (float(x) for x in token.split())
    return 15.0 * (h + m / 60.0 + s / 3600.0)


def _dms_to_deg(token: str) -> float:
    parts = token.split()
    sign = -1.0 if parts[0].startswith("-") else 1.0
    d, m, s = abs(float(parts[0])), float(parts[1]), float(parts[2])
    return sign * (d + m / 60.0 + s / 3600.0)


def horizons_astrometry(
    command: str, obscode: str, start: str, stop: str, step: str = "30m"
) -> list[dict[str, Any]]:
    """Astrometric (light-time + aberration corrected, airless) RA/Dec from a site.

    Horizons quantity 1 is the ICRF astrometric place -- the same quantity an observer
    reports to the MPC after reducing against a star catalogue.

    ``SKIP_DAYLT`` and ``ELEV_CUT`` restrict the output to instants when the object was
    genuinely observable from that site. This is not cosmetic: Find_Orb refuses
    observations taken in daylight or below the horizon, and a naive fixed-UT-hour sampling
    had every one of Eros's 24 synthetic observations thrown out as below the horizon,
    leaving a "fit" of zero observations that still emitted plausible-looking elements.
    """
    text = _horizons(
        {
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "'NO'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'OBSERVER'",
            "CENTER": f"'{obscode}'",
            "START_TIME": f"'{start}'",
            "STOP_TIME": f"'{stop}'",
            "STEP_SIZE": f"'{step}'",
            "QUANTITIES": "'1'",
            "ANG_FORMAT": "'HMS'",
            "EXTRA_PREC": "'YES'",
            "CSV_FORMAT": "'YES'",
            "SKIP_DAYLT": "'YES'",
            "ELEV_CUT": f"'{ELEV_CUT_DEG}'",
        }
    )
    out: list[dict[str, Any]] = []
    for row in _ephem_rows(text):
        cols = [c.strip() for c in row.split(",")]
        stamp = cols[0]  # "2024-Jan-05 06:00"
        date_part, _, time_part = stamp.partition(" ")
        y, mon, d = date_part.split("-")
        hh, mm = (int(x) for x in time_part.split(":")[:2])
        ra_txt, dec_txt = cols[3], cols[4]
        out.append(
            {
                "year": int(y),
                "month": _MONTHS[mon],
                "day": int(d) + (hh + mm / 60.0) / 24.0,
                "utc": stamp,
                "ra_deg": _hms_to_deg(ra_txt),
                "dec_deg": _dms_to_deg(dec_txt),
            }
        )
    return out


def horizons_elements(command: str, jd_tdb: float) -> dict[str, float]:
    """Heliocentric J2000-ecliptic osculating elements at one instant -- the truth values.

    ``CENTER='500@10'`` is the Sun's body centre and ``REF_PLANE='ECLIPTIC'`` the J2000
    ecliptic, matching what Find_Orb reports (``"central body": "Sun"``,
    ``"frame": "J2000 ecliptic"``). Horizons works in TDB and Find_Orb in TT; they differ
    by under 2 ms, which is far below the precision being compared.
    """
    text = _horizons(
        {
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "'NO'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'ELEMENTS'",
            "CENTER": "'500@10'",
            "REF_PLANE": "'ECLIPTIC'",
            "REF_SYSTEM": "'ICRF'",
            "OUT_UNITS": "'AU-D'",
            "TLIST": f"{jd_tdb:.9f}",
            "TLIST_TYPE": "'JD'",
            "CSV_FORMAT": "'NO'",
        }
    )
    body = "\n".join(_rows(text))
    found = {k: float(v) for k, v in _ELEM_RE.findall(body)}
    # Horizons names: EC e, QR q, IN i, OM node, W arg.peri, MA mean anomaly, A a, AD Q,
    # N mean motion, TP time of perihelion, PR period.
    return {
        "e": found.get("EC"),
        "q": found.get("QR"),
        "incl": found.get("IN"),
        "asc_node": found.get("OM"),
        "arg_per": found.get("W"),
        "mean_anom": found.get("MA"),
        "a": found.get("A"),
        "aphelion": found.get("AD"),
        "mean_motion": found.get("N"),
        "period_days": found.get("PR"),
    }


def select_epochs(rows: Sequence[dict[str, Any]], target: SelfTestTarget) -> list[dict[str, Any]]:
    """Thin an observable-times ephemeris to ``obs_per_night`` samples on ``n_nights``.

    ``rows`` has already been filtered by Horizons to instants when the object was above
    :data:`ELEV_CUT_DEG` and the Sun was down, so the first few samples of each UTC date
    are real observations. At Catalina an observing night runs roughly 01:00-13:00 UT and
    therefore does not straddle UTC midnight; grouping by UTC date is safe here (it is
    *not* safe in general, which is why the ITF tracklet index uses local nights).
    """
    by_date: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for r in rows:
        by_date.setdefault((r["year"], r["month"], int(r["day"])), []).append(r)
    keys = sorted(by_date)
    chosen: list[dict[str, Any]] = []
    for night in range(target.n_nights):
        idx = night * target.night_gap_days
        if idx >= len(keys):
            break
        chosen.extend(by_date[keys[idx]][: target.obs_per_night])
    return chosen


def build_astrometry(
    target: SelfTestTarget,
    epochs: Sequence[dict[str, Any]],
    *,
    noise_arcsec: float = 0.0,
    seed: int = 20260729,
) -> list[str]:
    """Turn Horizons positions into 80-column records, optionally with Gaussian error.

    The true per-coordinate uncertainty is always declared with a ``#Posn sigma``
    directive. Without it Find_Orb falls back to its per-observatory table (~0.5" for 703),
    which would make every reported sigma a statement about an error budget the data does
    not have, and any "within N sigma" comparison meaningless.
    """
    rng = random.Random(seed)
    declared = max(noise_arcsec, CLEAN_SIGMA_ARCSEC)
    lines: list[str] = [f"#Posn sigma {declared:g}"]
    for ep in epochs:
        ra, dec = ep["ra_deg"], ep["dec_deg"]
        if noise_arcsec > 0:
            cos_dec = max(math.cos(math.radians(dec)), 1e-6)
            ra += rng.gauss(0.0, noise_arcsec) / 3600.0 / cos_dec
            dec += rng.gauss(0.0, noise_arcsec) / 3600.0
        lines.append(
            format_line(
                desig=target.desig,
                year=ep["year"],
                month=ep["month"],
                day=ep["day"],
                ra_deg=ra,
                dec_deg=dec,
                obscode=target.obscode,
                mag=None,
                catalog="X",  # Gaia-EDR3: the catalogue with zero applied bias correction
            )
        )
    return lines


_COMPARE = ("a", "e", "incl", "q", "asc_node", "arg_per", "mean_anom")

#: Elements are angles or lengths with different natural scales; comparing "how many
#: reported sigmas away" is the only scale-free statement, and it is also exactly the
#: quantity the MPC's gates depend on being honest.
_SIGMA_ATTR = {
    "a": "sigma_a",
    "e": "sigma_e",
    "incl": "sigma_i",
    "q": "sigma_q",
    "asc_node": "sigma_asc_node",
    "arg_per": "sigma_arg_per",
    "mean_anom": "sigma_M",
}


def compare(fit: FitResult, truth: dict[str, float]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name in _COMPARE:
        got, want = getattr(fit, name, None), truth.get(name)
        if got is None or want is None:
            rows[name] = {
                "fit": got, "truth": want, "diff": None, "rel_diff": None,
                "sigma": getattr(fit, _SIGMA_ATTR[name], None), "n_sigma": None,
            }
            continue
        diff = got - want
        if name in ("asc_node", "arg_per", "mean_anom"):  # wrap to (-180, 180]
            diff = (diff + 180.0) % 360.0 - 180.0
        sigma = getattr(fit, _SIGMA_ATTR[name], None)
        rows[name] = {
            "fit": got,
            "truth": want,
            "diff": diff,
            "rel_diff": (diff / want) if want else None,
            "sigma": sigma,
            "n_sigma": (abs(diff) / sigma) if sigma else None,
        }
    return rows


@dataclass
class SelfTestCase:
    label: str
    desig: str
    obscode: str
    n_obs: int
    noise_arcsec: float
    fit: FitResult | None
    cadence: str = "gating"
    truth: dict[str, float] = field(default_factory=dict)
    comparison: dict[str, Any] = field(default_factory=dict)
    passed: bool = False
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "desig": self.desig,
            "obscode": self.obscode,
            "cadence": self.cadence,
            "n_obs": self.n_obs,
            "noise_arcsec": self.noise_arcsec,
            "passed": self.passed,
            "failures": self.failures,
            "fit": self.fit.as_dict() if self.fit else None,
            "truth": self.truth,
            "comparison": self.comparison,
        }


def _judge(case: SelfTestCase, *, max_n_sigma: float, rms_range: tuple[float, float]) -> None:
    """Score one case, on one criterion, uniformly.

    Every element must sit within ``max_n_sigma`` of the JPL value **using Find_Orb's own
    reported sigma**. That is the only scale-free comparison available, and it is the
    right one: a fixed absolute tolerance on ``a`` is meaningless over a 9-day arc, where
    the semimajor axis is genuinely undetermined (sigma(a) ~ 0.1-0.5 AU) no matter how
    good the astrometry. It is also exactly the quantity the MPC's three-night gate relies
    on, so a solver whose sigmas were optimistic would fail here rather than downstream.
    """
    fit = case.fit
    if fit is None or not fit.converged:
        case.failures.append(f"fit did not converge ({fit.status if fit else 'no result'})")
        case.passed = False
        return
    if fit.n_used is not None and fit.n_used < case.n_obs:
        case.failures.append(f"only {fit.n_used} of {case.n_obs} observations used")
    lo, hi = rms_range
    if fit.rms_residual is None or not (lo <= fit.rms_residual <= hi):
        case.failures.append(f'residual RMS {fit.rms_residual}" outside [{lo}, {hi}]"')

    for name, row in case.comparison.items():
        if row.get("truth") is None:
            case.failures.append(f"{name}: no truth value from Horizons")
            continue
        n_sigma = row.get("n_sigma")
        if n_sigma is None:
            case.failures.append(f"{name}: no sigma reported, cannot judge")
        elif n_sigma > max_n_sigma:
            case.failures.append(f"{name}: {n_sigma:.1f} sigma from Horizons truth")
    case.passed = not case.failures


def run_selftest(
    workroot: Path,
    *,
    targets: Sequence[SelfTestTarget] = DEFAULT_TARGETS,
    shell: Shell | None = None,
    noise_arcsec: float = NOISE_ARCSEC,
    include_wide: bool = True,
) -> dict[str, Any]:
    """Run the full Horizons round-trip for every target and return a JSON-able report.

    Each target is fitted twice per cadence -- once on noise-free positions and once with
    ``noise_arcsec`` injected -- so that both the solution and its uncertainty are tested.
    """
    shell = shell or default_shell()
    workroot.mkdir(parents=True, exist_ok=True)
    cases: list[SelfTestCase] = []
    cadences = [("compact", COMPACT_CADENCE)]
    if include_wide:
        cadences.append(("wide", WIDE_CADENCE))

    for base in targets:
        # One astrometry request per target covers every cadence: ask for a long window,
        # let Horizons drop the un-observable instants, and thin afterwards. Objects go
        # through solar conjunction, so a fixed short window is not enough -- (7) Iris
        # returned zero observable samples from a 58-day window starting in January.
        y, m, d = (int(x) for x in base.start_date.split("-"))
        rows = horizons_astrometry(
            base.command,
            base.obscode,
            start=base.start_date,
            stop=_add_days(y, m, d, base.search_days),
            step="30m",
        )
        for cadence_name, (n_nights, gap) in cadences:
            target = base.with_cadence(n_nights, gap)
            epochs = select_epochs(rows, target)
            for noise in (0.0, noise_arcsec):
                tag = "clean" if noise == 0 else f"noise{noise:g}"
                lines = build_astrometry(target, epochs, noise_arcsec=noise)
                wd = workroot / f"{target.desig}_{cadence_name}_{tag}"
                run = run_fo(lines, wd, designations=[target.desig], shell=shell)
                fit = run.results.get(target.desig)
                case = SelfTestCase(
                    label=f"{target.label} [{cadence_name}/{tag}]",
                    desig=target.desig,
                    obscode=target.obscode,
                    cadence=cadence_name,
                    n_obs=len(epochs),
                    noise_arcsec=noise,
                    fit=fit,
                )
                if fit and fit.epoch_jd:
                    case.truth = horizons_elements(target.command, fit.epoch_jd)
                    case.comparison = compare(fit, case.truth)
                # Noise-free: the only error left is the 80-column quantisation floor
                # (0.001s in RA, 0.01" in Dec), so the RMS must be tiny. Noisy: the fit
                # RMS should reproduce the injected sigma to within a factor of two, and
                # every element must sit within 4 sigma of truth.
                _judge(
                    case,
                    max_n_sigma=4.0,
                    rms_range=(0.5 * noise, 2.0 * noise) if noise else (0.0, 0.05),
                )
                cases.append(case)

    n_pass = sum(1 for c in cases if c.passed)
    by_cadence = {
        name: {
            "passed": sum(1 for c in cases if c.cadence == name and c.passed),
            "cases": sum(1 for c in cases if c.cadence == name),
        }
        for name, _ in cadences
    }
    return {
        "find_orb": shell.version(),
        "cadences": {
            name: {"n_nights": spec[0], "night_gap_days": spec[1]} for name, spec in cadences
        },
        "noise_arcsec": noise_arcsec,
        "declared_clean_sigma_arcsec": CLEAN_SIGMA_ARCSEC,
        "n_cases": len(cases),
        "n_passed": n_pass,
        "all_passed": bool(cases) and n_pass == len(cases),
        "by_cadence": by_cadence,
        "failures": [
            {"label": c.label, "reasons": c.failures} for c in cases if not c.passed
        ],
        "cases": [c.as_dict() for c in cases],
    }


def _add_days(year: int, month: int, day: int, days: int) -> str:
    from datetime import date, timedelta

    return (date(year, month, day) + timedelta(days=days)).isoformat()
