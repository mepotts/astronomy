"""M9: extend the perturbed calibration to 25 years; measure the TNO regime. Read-only.

Two questions, both answered the M7/M8 way (current get-orb orbit propagated back,
compared against JPL Horizons astrometric geocentric truth; TLIST sorted oldest-first
because Horizons replies chronologically regardless of request order):

1. **Does the 15-year wall move?** M8 measured its envelope on a 16-point grid ending
   at 15 y because that is where its grid ended, not where the physics ends. Four
   added lookbacks (18/20/22.5/25 y) on the same seven M8 calibrators say whether the
   main-population window can open further. The M8 gate stays frozen; a wider gate is
   an M10 decision to take from these numbers, not something M9 applies retroactively.

2. **What does the perturbed backend do on distant objects?** The M7 slow-northern TNO
   pool (5,435 tracklets, Dec > +30, < 10 arcsec/hr) reaches back to 1998-2003 -- 23-28
   years before the current orbit epochs. Four numbered TNOs with ~25-year arcs and
   thousands of observations calibrate that regime separately: (20000) Varuna,
   (28978) Ixion, (50000) Quaoar, (136199) Eris. Their envelope is reported apart from
   the main-belt one -- a TNO sweep gated by main-belt errors would be nonsense in both
   directions (TNO perturbed error should be far smaller; two-body may even suffice,
   which is also worth knowing and is measured here too).

Writes ``data/raw/rubin/m9-calibration.json``. Never touches ``m8-calibration.json``
(the frozen M8 gate). <= 11 get-orb + <= 11 Horizons calls, paced, cached.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m7_calibration as m7
import m8_calibration as m8
import numpy as np

from itf_linker.attrib.core import parse_mpc_orb, predict, separation_deg
from itf_linker.attrib.perturbed import integrate_dense, predict_dense

MAINBELT_TARGETS = dict(m8.TARGETS)

TNO_TARGETS = {
    "20000": "Varuna (TNO a=43)",
    "28978": "Ixion (TNO a=39)",
    "50000": "Quaoar (TNO a=43)",
    "136199": "Eris (SDO a=68 e=0.44)",
}

#: M8's 16 lookbacks plus 18/20/22.5/25 y — and 26.5/28 y, because the M7
#: slow-northern pool's oldest tracklets (1998-2000) sit 26-28 years before current
#: TNO orbit epochs; a 25-year grid would leave the pool's deep end unmeasured.
LOOKBACK_DAYS = sorted(m8.LOOKBACK_DAYS + [6574.5, 7305.0, 8218.1, 9131.25,
                                           9679.1, 10227.0])

OUT = ROOT / "data" / "raw" / "rubin" / "m9-calibration.json"


def measure(desig: str, label: str) -> dict:
    doc = m7.get_orb_cached(desig)
    orbit = parse_mpc_orb(doc, requested_desig=desig)
    if orbit is None:
        return {"error": "no orbit", "label": label}
    lookbacks = sorted(LOOKBACK_DAYS, reverse=True)  # oldest instant first (M7 trap)
    mjd_utc = np.array([orbit.epoch_mjd_tt - lb for lb in lookbacks])
    jds = [m + 2400000.5 for m in mjd_utc]
    truth = m7.horizons_tlist_geocentric(desig, jds)
    if len(truth) != len(jds):
        return {"error": f"horizons returned {len(truth)} rows for {len(jds)}",
                "label": label}
    truth_ra = np.array([t["ra_deg"] for t in truth])
    truth_dec = np.array([t["dec_deg"] for t in truth])

    pred2 = predict(orbit, mjd_utc)
    sep2 = separation_deg(pred2["ra_deg"], pred2["dec_deg"], truth_ra, truth_dec)

    traj = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        float(mjd_utc.min() - 3.0), orbit.epoch_mjd_tt, h_days=1.0,
    )
    predp = predict_dense(traj, np.zeros(len(lookbacks), dtype=int), mjd_utc,
                          h_mag=orbit.h_mag, g_slope=orbit.g_slope)
    sepp = separation_deg(predp["ra_deg"], predp["dec_deg"], truth_ra, truth_dec)

    return {
        "label": label,
        "a_au": round(orbit.a_au, 3),
        "epoch_mjd_tt": orbit.epoch_mjd_tt,
        "encounter": bool(traj.encounter[0]),
        "twobody_arcsec_by_lookback": {
            f"{lb / 365.25:.2f}y": round(float(s) * 3600.0, 2)
            for lb, s in zip(lookbacks, sep2)
        },
        "perturbed_arcsec_by_lookback": {
            f"{lb / 365.25:.2f}y": round(float(s) * 3600.0, 2)
            for lb, s in zip(lookbacks, sepp)
        },
    }


def envelope(targets: dict[str, dict], key: str) -> dict[str, float]:
    grid: dict[str, float] = {}
    for tgt in targets.values():
        if tgt.get("error") or tgt.get("encounter"):
            continue
        for k, v in tgt[key].items():
            grid[k] = max(grid.get(k, 0.0), float(v))
    return dict(sorted(grid.items(), key=lambda kv: float(kv[0].rstrip("y"))))


def main() -> None:
    report: dict = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lookback_days": LOOKBACK_DAYS,
        "integrator": {"h_days": 1.0, "dense_every": 8,
                       "force_model": "sun + 8 planets (EMB), JPL mean elements + DE440 GM"},
        "mainbelt_targets": {},
        "tno_targets": {},
    }
    for desig, label in MAINBELT_TARGETS.items():
        entry = measure(desig, label)
        report["mainbelt_targets"][desig] = entry
        print(desig, label, flush=True)
        if "error" not in entry:
            print("  perturbed:", entry["perturbed_arcsec_by_lookback"],
                  "ENCOUNTER" if entry["encounter"] else "", flush=True)
    for desig, label in TNO_TARGETS.items():
        entry = measure(desig, label)
        report["tno_targets"][desig] = entry
        print(desig, label, flush=True)
        if "error" not in entry:
            print("  two-body :", entry["twobody_arcsec_by_lookback"], flush=True)
            print("  perturbed:", entry["perturbed_arcsec_by_lookback"],
                  "ENCOUNTER" if entry["encounter"] else "", flush=True)

    report["perturbed_envelope_arcsec_mainbelt_25y"] = envelope(
        report["mainbelt_targets"], "perturbed_arcsec_by_lookback")
    report["perturbed_envelope_arcsec_tno_25y"] = envelope(
        report["tno_targets"], "perturbed_arcsec_by_lookback")
    report["twobody_envelope_arcsec_tno_25y"] = envelope(
        report["tno_targets"], "twobody_arcsec_by_lookback")
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("main-belt 25y envelope:",
          report["perturbed_envelope_arcsec_mainbelt_25y"], flush=True)
    print("TNO 25y envelope (perturbed):",
          report["perturbed_envelope_arcsec_tno_25y"], flush=True)
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
