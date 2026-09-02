"""M7: measure the two-body attribution-prediction error against JPL Horizons.

The attribution sweep propagates a current MPC orbit backwards with the linker's
two-body propagator and asks "which ITF tracklets sit near the prediction". Two-body
neglects planetary perturbations, so its error **grows with lookback** -- and rather
than assume a radius, this script measures the error directly, in the M1 self-test's
pattern: nothing in the truth values comes from this repository's own code.

Method: for numbered asteroids whose orbits are essentially exact (multi-thousand-obs,
multi-decade arcs -- so the *catalogue orbit* contributes negligible error and any
disagreement is the propagation's), take the current MPC orbit from the same get-orb
API the sweep uses, two-body it back 1/5/10/15 years, and compare against Horizons'
astrometric geocentric RA/Dec at the same instants. Targets sample the Feb-batch
subset's orbit space (a ~ 2.3-3.9 AU).

Writes ``data/raw/rubin/m7-calibration.json`` and drops each target's stripped
``mpc_orb`` block into ``tests/data/attrib/`` as offline test fixtures.

Read-only: 4 get-orb calls + 4 Horizons calls, >= 1.1 s apart, cached on disk.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import requests

from itf_linker.attrib.core import parse_mpc_orb, predict, separation_deg
from itf_linker.fit.verify import HORIZONS_URL, HorizonsError

ORB_URL = "https://data.minorplanetcenter.net/api/get-orb"
USER_AGENT = (
    "itf-linker/0.3 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

#: Numbered main-belt targets spanning the Feb-batch subset's semi-major-axis range.
#: All have arcs over a century and tens of thousands of observations: the catalogue
#: orbit's own uncertainty is microscopic against the propagation error being measured.
TARGETS = {
    "7": "Iris (a=2.39)",
    "170": "Maria (a=2.55)",
    "24": "Themis (a=3.13)",
    "153": "Hilda (a=3.97)",
}

#: Dense inside the first three years -- the first run measured degree-scale error at
#: 5-15 years (Themis 7545" at 15 y, Hilda 6776" at 10 y), which no usable coarse gate
#: can absorb, so the sweep bounds its lookback instead and the grid here is what sets
#: that bound. Kept out to 15 y to document *why* the deep slice needs a perturbed
#: propagator rather than a wider gate.
LOOKBACK_DAYS = [
    91.3, 182.6, 273.9, 365.25, 548.0, 730.5, 913.0, 1096.0, 1278.0, 1461.0,
    1826.25, 3652.5, 5478.75,
]

CACHE = ROOT / "data" / "raw" / "rubin" / "calibration-cache"
FIXTURES = ROOT / "tests" / "data" / "attrib"
OUT = ROOT / "data" / "raw" / "rubin" / "m7-calibration.json"

_last_request = 0.0


def _pace() -> None:
    global _last_request
    wait = 1.1 - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


def get_orb_cached(desig: str) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"orb_{desig}.json"
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))
    _pace()
    resp = requests.get(
        ORB_URL, json={"desig": desig}, headers={"User-Agent": USER_AGENT}, timeout=90
    )
    resp.raise_for_status()
    doc = resp.json()
    dest.write_text(json.dumps(doc), encoding="utf-8")
    return doc


def horizons_tlist_geocentric(command: str, jds_ut: list[float]) -> list[dict]:
    """Astrometric geocentric RA/Dec (deg) at explicit JD(UT) instants, one call."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"hz_{command}_{hash(tuple(round(j, 6) for j in jds_ut)) & 0xFFFFFFFF:x}.json"
    dest = CACHE / key
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))
    _pace()
    tlist = " ".join(f"'{jd:.8f}'" for jd in jds_ut)
    resp = requests.get(
        HORIZONS_URL,
        params={
            "format": "text",
            "COMMAND": f"'{command};'",
            "OBJ_DATA": "'NO'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'OBSERVER'",
            "CENTER": "'500'",  # geocentric, matching the sweep's approximation
            "TLIST": tlist,
            "TLIST_TYPE": "'JD'",
            "TIME_TYPE": "'UT'",
            "QUANTITIES": "'1'",
            "ANG_FORMAT": "'DEG'",
            "EXTRA_PREC": "'YES'",
            "CSV_FORMAT": "'YES'",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=180,
    )
    resp.raise_for_status()
    text = resp.text
    if "$$SOE" not in text:
        raise HorizonsError(f"unexpected Horizons reply: {text[:400]}")
    body = text.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows = []
    for ln in body.splitlines():
        cols = [c.strip() for c in ln.split(",")]
        if len(cols) < 5 or not cols[0]:
            continue
        # CSV columns: date, [flags...], RA(deg), Dec(deg) -- RA/Dec are the last two
        # non-empty numeric columns with ANG_FORMAT=DEG, QUANTITIES=1.
        numeric = [c for c in cols if c and _is_float(c)]
        rows.append({"stamp": cols[0], "ra_deg": float(numeric[-2]), "dec_deg": float(numeric[-1])})
    dest.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def _is_float(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    report: dict = {"targets": {}, "lookback_days": LOOKBACK_DAYS}
    for desig, label in TARGETS.items():
        doc = get_orb_cached(desig)
        orbit = parse_mpc_orb(doc, requested_desig=desig)
        if orbit is None:
            report["targets"][desig] = {"error": "no orbit"}
            continue
        # Fixture: the mpc_orb block only (the envelope's rwo residual tables are large).
        env = doc[0] if isinstance(doc, list) else doc
        fixture = {"mpc_orb": env.get("mpc_orb")}
        (FIXTURES / f"mpc_orb_{desig}.json").write_text(
            json.dumps(fixture), encoding="utf-8"
        )

        # Horizons returns TLIST rows in chronological (ascending) order regardless of
        # the order asked for -- found the hard way: the first run of this script paired
        # the 1-year prediction with the 15-year truth row and reported 65-degree
        # "propagation errors". Sort the lookbacks so predictions share that order.
        lookbacks = sorted(LOOKBACK_DAYS, reverse=True)  # oldest instant first
        mjd_utc = np.array(
            [orbit.epoch_mjd_tt - lb for lb in lookbacks]
        )  # TT-UTC offset is 69 s; negligible against the days-scale sampling here,
        # and predict() applies the proper conversion internally anyway.
        pred = predict(orbit, mjd_utc)
        jds = [m + 2400000.5 for m in mjd_utc]
        truth = horizons_tlist_geocentric(desig, jds)
        if len(truth) != len(jds):
            report["targets"][desig] = {
                "error": f"horizons returned {len(truth)} rows for {len(jds)} instants"
            }
            continue
        seps = separation_deg(
            pred["ra_deg"],
            pred["dec_deg"],
            np.array([t["ra_deg"] for t in truth]),
            np.array([t["dec_deg"] for t in truth]),
        )
        report["targets"][desig] = {
            "label": label,
            "a_au": round(orbit.a_au, 3),
            "epoch_mjd_tt": orbit.epoch_mjd_tt,
            "sep_arcsec_by_lookback": {
                f"{lb / 365.25:.2f}y": round(float(s) * 3600.0, 2)
                for lb, s in zip(lookbacks, seps)
            },
        }
        print(desig, label, report["targets"][desig]["sep_arcsec_by_lookback"], flush=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
