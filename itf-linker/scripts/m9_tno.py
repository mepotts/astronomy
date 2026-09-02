"""M9: TNO-niche feasibility slice — a bounded scoping sweep, not a campaign.

M7 section 9 sized the slow-northern pool (Dec > +30, endpoint rate < 10 arcsec/hr) at
5,435 tracklets, dominated by T09 Subaru and 645 SDSS, reaching back to 1998-2003 —
epochs two-body could never touch. ``scripts/m9_calibration.py`` measured the perturbed
backend on four numbered TNOs: **<= 0.45 arcsec at 28 years** (two-body <= ~300), so
the whole pool is inside a *measured* window for the distant population.

This script asks one scoping question: swept against every distant orbit the MPC
publishes (a >= 25 AU, bound, U <= 6, from the cached 2026-08-16 MPCORB), does the
slow-northern pool show a decoy-priced excess anywhere? It runs the M8 sweep machinery
with a TNO-specific gate (same formula; the *TNO* envelope measured this milestone —
the frozen M8 main-belt gate is not touched, and no main-population sweep runs beyond
M8's 15-year window). **No fits are run**: the deliverable is coarse counts, the decoy
price, and a ranked top list for a possible M10 fit campaign.

Writes ``m9-tno-scoping.json`` (root, gitignored).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m7_attribution as m7run
import m8_attribution as m8run
import m8_fetch_bulk as m8fb
import numpy as np
import polars as pl

from itf_linker import config
from itf_linker.attrib.bulk import iter_mpcorb_objects, mpcorb_to_orbit
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import link_key
from itf_linker.link.geometry import GM_SUN

RECONSTRUCTED = ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m9-calibration.json"
OUT = ROOT / "m9-tno-scoping.json"

MIN_A_AU = 25.0
MAX_LOOKBACK_DAYS = 28.0 * 365.25  # measured: scripts/m9_calibration.py, TNO targets
DEC_MIN = 30.0
RATE_MAX_ARCSEC_HR = 10.0


def tno_envelope() -> Any:
    doc = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    grid = {
        float(k.rstrip("y")) * 365.25: float(v)
        for k, v in doc["perturbed_envelope_arcsec_tno_25y"].items()
    }
    xs = np.array(sorted(grid))
    ys = np.maximum.accumulate(np.array([grid[x] for x in xs]))

    def env(dt_days: np.ndarray) -> np.ndarray:
        return np.interp(np.abs(dt_days), xs, ys, left=ys[0], right=ys[-1])

    return env


def distant_orbits() -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    rows = []
    stats = {"scanned": 0, "distant_bound": 0, "u_excluded": 0}
    for obj in iter_mpcorb_objects(m8fb.MPCORB_GZ):
        stats["scanned"] += 1
        # Cheap pre-filter on the file's own semimajor axis before the full parse
        # (Kepler solve per object x 1.56M would dominate the run for no reason).
        try:
            if float(obj.get("a") or 0.0) < MIN_A_AU * 0.98:
                continue
        except (TypeError, ValueError):
            pass
        orbit = mpcorb_to_orbit(obj)
        if orbit is None:
            continue
        r = np.linalg.norm(orbit.r0)
        v2 = float(orbit.v0 @ orbit.v0)
        denom = 2.0 / r - v2 / GM_SUN
        if denom <= 0:  # unbound
            continue
        a = 1.0 / denom
        if a < MIN_A_AU:
            continue
        stats["distant_bound"] += 1
        if orbit.u_param is not None and orbit.u_param > m8run.MAX_U_PARAM:
            stats["u_excluded"] += 1
            continue
        rows.append(
            {
                "primary": orbit.primary_desig,
                "epoch": orbit.epoch_mjd_tt,
                "r0": orbit.r0,
                "v0": orbit.v0,
                "h": orbit.h_mag if orbit.h_mag is not None else np.nan,
                "g": orbit.g_slope if orbit.g_slope is not None else 0.15,
                "u": -1 if orbit.u_param is None else orbit.u_param,
                "a_au": a,
            }
        )
    stats["swept"] = len(rows)
    u_hist: dict[str, int] = {}
    for r in rows:
        u_hist[str(r["u"])] = u_hist.get(str(r["u"]), 0) + 1
    stats["u_histogram"] = dict(sorted(u_hist.items()))
    arrays = {
        "primary": np.array([r["primary"] for r in rows]),
        "epoch": np.array([r["epoch"] for r in rows]),
        "r0": np.array([r["r0"] for r in rows]),
        "v0": np.array([r["v0"] for r in rows]),
        "h": np.array([r["h"] for r in rows], dtype=float),
        "g": np.array([r["g"] for r in rows], dtype=float),
        "u": np.array([r["u"] for r in rows], dtype=int),
        "a_au": np.array([r["a_au"] for r in rows], dtype=float),
    }
    return arrays, stats


def slow_north_tracklets(mjd_min: float, mjd_max: float) -> pl.DataFrame:
    trk = m7run.load_tracklets(mjd_min, mjd_max)
    rate = (
        (pl.col("rate_ra_cosdec_deg_day").pow(2)
         + pl.col("rate_dec_deg_day").pow(2)).sqrt() * 3600.0 / 24.0
    )
    return trk.filter(
        (pl.col("dec_deg") > DEC_MIN)
        & pl.col("rate_ra_cosdec_deg_day").is_not_null()
        & (rate < RATE_MAX_ARCSEC_HR)
        & (pl.col("span_days") > 0)
    )


def main() -> None:
    t0 = time.monotonic()
    config.ITF_PARQUET = RECONSTRUCTED
    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "itf_parquet": str(RECONSTRUCTED),
        "parameters": {
            "min_a_au": MIN_A_AU,
            "max_lookback_days": MAX_LOOKBACK_DAYS,
            "dec_min_deg": DEC_MIN,
            "rate_max_arcsec_hr": RATE_MAX_ARCSEC_HR,
            "gate": "120\" + 1.5 x TNO envelope(|dt|) + U-runoff (M9-measured envelope)",
            "fits": "none -- scoping only",
        },
    }

    arrays, stats = distant_orbits()
    report["orbits"] = stats
    print(f"distant orbits: {stats}", flush=True)

    mjd_min = float(arrays["epoch"].min() - MAX_LOOKBACK_DAYS)
    mjd_max = float(arrays["epoch"].max() + 1.0)
    trk = slow_north_tracklets(mjd_min, mjd_max)
    report["slow_north_tracklets"] = trk.height
    by_code = dict(
        trk.group_by("obscode").len().sort("len", descending=True).head(8).rows()
    )
    report["slow_north_by_obscode_top8"] = by_code
    print(f"slow-northern tracklets in window: {trk.height} (top: {by_code})",
          flush=True)

    lon = fetch_obscodes()
    nightindex = m8run.NightIndex(trk, lon)
    report["nights"] = len(nightindex.night_mjd)
    env = tno_envelope()

    # The shared sweep machinery reads its lookback bound from the module attribute;
    # widen it for THIS process only, to the TNO-measured 28 years.
    m8run.MAX_LOOKBACK_DAYS = MAX_LOOKBACK_DAYS

    print("real sweep:", flush=True)
    real, t_real = m8run.run_sweep(arrays, nightindex, env, decoy=False,
                                   label="tno real")
    print("control sweep:", flush=True)
    fake, t_fake = m8run.run_sweep(arrays, nightindex, env, decoy=True,
                                   label="tno control")
    report["sweep_timing"] = {"real": t_real, "control": t_fake}
    report["coarse"] = {"real": m8run.summarise(real), "control": m8run.summarise(fake)}
    print(json.dumps(report["coarse"], indent=1), flush=True)

    keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid",
                      "mag_mean").rows()
    a_by_primary = dict(zip(arrays["primary"].tolist(), arrays["a_au"].tolist()))
    for m in real:
        desig, obscode, night, n_obs, mjd_mid, mag = keys[m["row"]]
        m["trksub"] = desig
        m["obscode"] = obscode
        m["night"] = int(night)
        m["trk_n_obs"] = int(n_obs)
        m["trk_mjd_mid"] = float(mjd_mid)
        m["trk_mag_mean"] = None if mag is None else float(mag)
        m["link_key"] = link_key([(desig, obscode, int(night))])
        m["orbit_a_au"] = round(a_by_primary.get(m["orbit_desig"], float("nan")), 2)
        del m["row"]
    for m in fake:
        m.pop("row", None)
    real.sort(key=lambda m: (m["encounter"],
                             m["sep_arcsec"] / m["gate_radius_arcsec"]))
    report["real_matches"] = real
    report["control_matches_sample"] = fake[:100]
    report["top20"] = [
        {k: m[k] for k in ("orbit_desig", "orbit_a_au", "trksub", "obscode", "night",
                           "sep_arcsec", "gate_radius_arcsec", "dt_days", "link_key")}
        for m in real[:20]
    ]
    report["elapsed_s"] = round(time.monotonic() - t0, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT} in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
