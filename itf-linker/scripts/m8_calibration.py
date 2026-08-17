"""M8: measure the *perturbed* attribution-prediction error against JPL Horizons.

Extends ``scripts/m7_calibration.py`` (whose fetch/cache/pacing machinery it imports)
in three ways:

1. **Both backends on every target.** Two-body (the M7 gate's basis) and the new
   perturbed propagator (:mod:`itf_linker.attrib.perturbed`) are compared against the
   same Horizons astrometric geocentric truth at the same instants, so the improvement
   is a measured column pair, not a claim.
2. **Three added targets** stretch the orbit space the Feb/Apr Rubin batches actually
   contain beyond M7's four main-belt calibrators: (433) Eros (a=1.46 Amor -- the NEO
   end), (588) Achilles (a=5.2 Jupiter Trojan -- deepest into Jupiter's mean-element
   error), and (944) Hidalgo (a=5.7, e=0.66 Jupiter-crosser -- deliberately hostile:
   the case the encounter flag exists for).
3. **A denser 4-15 y grid** (6.5/8/12 y added), because that is where the perturbed
   gate has to hold and the two-body one measurably does not.

The output envelope (max over non-encounter targets, monotonicised) is what
``scripts/m8_attribution.py`` freezes its position gate from. Encounter-flagged targets
are excluded from the envelope and reported separately: an orbit that entered a Hill
sphere inherits no accuracy claim from this calibration (and Hidalgo demonstrates why).

Traps inherited from M7, still live here: Horizons TLIST replies come back
**chronological regardless of request order** (sort the lookbacks); ``mpc_orb`` states
are heliocentric ecliptic at MJD/TDT.

Read-only: <= 7 get-orb + <= 7 Horizons calls, >= 1.1 s apart, cached on disk.
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
import numpy as np

from itf_linker.attrib.core import parse_mpc_orb, predict, separation_deg
from itf_linker.attrib.perturbed import integrate_dense, predict_dense

#: M7's four calibrators, plus the three stretch targets. Labels carry the role.
TARGETS = dict(m7.TARGETS) | {
    "433": "Eros (a=1.46 Amor, NEO end)",
    "588": "Achilles (a=5.2 Trojan)",
    "944": "Hidalgo (a=5.7 e=0.66 Jupiter-crosser; encounter stress case)",
}

#: M7's 13 lookbacks plus 6.5/8/12 y -- density where the perturbed gate must hold.
LOOKBACK_DAYS = sorted(m7.LOOKBACK_DAYS + [2374.1, 2922.0, 4383.0])

OUT = ROOT / "data" / "raw" / "rubin" / "m8-calibration.json"
FIXTURES = ROOT / "tests" / "data" / "attrib"


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lookback_days": LOOKBACK_DAYS,
        "integrator": {"h_days": 1.0, "dense_every": 8,
                       "force_model": "sun + 8 planets (EMB), JPL mean elements + DE440 GM"},
        "targets": {},
    }
    for desig, label in TARGETS.items():
        doc = m7.get_orb_cached(desig)
        orbit = parse_mpc_orb(doc, requested_desig=desig)
        if orbit is None:
            report["targets"][desig] = {"error": "no orbit"}
            continue
        env = doc[0] if isinstance(doc, list) else doc
        (FIXTURES / f"mpc_orb_{desig}.json").write_text(
            json.dumps({"mpc_orb": env.get("mpc_orb")}), encoding="utf-8"
        )

        # Oldest instant first: Horizons returns TLIST rows chronologically no matter
        # what order was requested (the M7 trap), so predictions share that order.
        lookbacks = sorted(LOOKBACK_DAYS, reverse=True)
        mjd_utc = np.array([orbit.epoch_mjd_tt - lb for lb in lookbacks])
        jds = [m + 2400000.5 for m in mjd_utc]
        truth = m7.horizons_tlist_geocentric(desig, jds)
        if len(truth) != len(jds):
            report["targets"][desig] = {
                "error": f"horizons returned {len(truth)} rows for {len(jds)} instants"
            }
            continue
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

        entry = {
            "label": label,
            "a_au": round(orbit.a_au, 3),
            "epoch_mjd_tt": orbit.epoch_mjd_tt,
            "encounter": bool(traj.encounter[0]),
            "min_planet_dist_au": {
                name: round(float(d), 3)
                for name, d in zip(
                    ("mercury", "venus", "emb", "mars", "jupiter", "saturn",
                     "uranus", "neptune"),
                    traj.min_planet_dist_au[0],
                )
            },
            "twobody_arcsec_by_lookback": {
                f"{lb / 365.25:.2f}y": round(float(s) * 3600.0, 2)
                for lb, s in zip(lookbacks, sep2)
            },
            "perturbed_arcsec_by_lookback": {
                f"{lb / 365.25:.2f}y": round(float(s) * 3600.0, 2)
                for lb, s in zip(lookbacks, sepp)
            },
        }
        report["targets"][desig] = entry
        print(desig, label, flush=True)
        print("  two-body :", entry["twobody_arcsec_by_lookback"], flush=True)
        print("  perturbed:", entry["perturbed_arcsec_by_lookback"],
              "encounter" if entry["encounter"] else "", flush=True)

    # The frozen envelope: max perturbed error over non-encounter targets, per
    # lookback, monotonicised by the sweep's envelope_fn at load time.
    grid: dict[str, float] = {}
    for tgt in report["targets"].values():
        if tgt.get("error") or tgt.get("encounter"):
            continue
        for k, v in tgt["perturbed_arcsec_by_lookback"].items():
            grid[k] = max(grid.get(k, 0.0), float(v))
    report["perturbed_envelope_arcsec"] = dict(sorted(grid.items(), key=lambda kv: float(kv[0].rstrip("y"))))
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"envelope (non-encounter max): {report['perturbed_envelope_arcsec']}", flush=True)
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
