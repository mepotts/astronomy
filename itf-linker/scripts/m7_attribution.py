"""M7: attribute ITF tracklets to Rubin (X05) Feb-5-batch orbits. NOTHING IS SUBMITTED.

The run, end to end:

1. **Orbits** -- parse the cached get-orb responses (``scripts/m7_fetch_orbits.py``),
   dedupe on the MPC's primary designation (the batch is already partly merged), drop
   U >= 7 orbits whose along-track runoff exceeds any workable gate.
2. **Tracklets** -- today's tracklet table, restricted to |t - epoch| <= 4 years: the
   lookback bound *measured* by ``scripts/m7_calibration.py``, beyond which two-body
   propagation of a current orbit carries degree-scale error and no coarse gate is
   usable. Per-tracklet sky rates come from the tracklet's first/last observation.
3. **Coarse sweep** -- per orbit, per night: two-body prediction (geocentric,
   light-time corrected); position gate with the measured, lookback- and U-dependent
   radius; then an exact per-tracklet-epoch pass with a rate-vector gate.
4. **Control** -- the identical sweep against each orbit half a period out of phase
   (same elements, same rate statistics, wrong place). Its match count is the measured
   chance-coincidence background of the coarse gate. House law: a control must be
   amplitude-matched to screen anything.
5. **Joint fits** -- for real coarse candidates: the object's full published astrometry
   (MPC get-obs, OBS80) plus the ITF tracklet's verbatim 80-column lines, relabelled and
   fitted together by Find_Orb exactly as every link in this repository is fitted. Gates:
   the project's strict post-fit gate and the MPC's published rule, reported side by
   side, plus the subset guard's question -- did the fit actually *use* the tracklet?
   A converged fit that excluded the new observations attributes nothing.

Outputs ``m7-attribution.json`` at the repo root (gitignored by the ``/m[0-9]*.json``
pattern) and prints a summary. Candidates are candidates; the deliverable is a gated
list for human review, never a submission.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import polars as pl
import requests

from itf_linker import config
from itf_linker.attrib.core import (
    AttribOrbit,
    control_orbit,
    parse_mpc_orb,
    predict,
    separation_deg,
)
from itf_linker.fit.findorb import prepare_config_dir, run_fo
from itf_linker.fit.gates import mpc_published_gate, post_fit_gate
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import _relabel, link_key, tracklet_line_index
from itf_linker.mpc80 import parse_line

ORBIT_CACHE = ROOT / "data" / "raw" / "rubin" / "orbits"
OBS80_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80"
CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m7-calibration.json"
FIT_ROOT = ROOT / "data" / "m7-fits"
OUT = ROOT / "m7-attribution.json"

OBS_URL = "https://data.minorplanetcenter.net/api/get-obs"
USER_AGENT = (
    "itf-linker/0.3 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

#: Hard lookback bound, days. Source: scripts/m7_calibration.py -- the measured two-body
#: error envelope stays under ~600 arcsec inside 4 years and reaches degrees by 5-15.
MAX_LOOKBACK_DAYS = 4.0 * 365.25

#: Coarse position gate: floor + safety * measured envelope + U-parameter runoff.
#: The floor absorbs the single-opposition orbit's own cross-track uncertainty and the
#: geocentric approximation (<= ~9 arcsec/AU parallax); 1.5x the envelope covers the
#: object-to-object spread of the four calibration targets (N=4 -- a small sample, which
#: is why the control exists to measure what the radius actually admits).
GATE_FLOOR_ARCSEC = 120.0
GATE_ENVELOPE_SAFETY = 1.5
#: Exclude orbits whose MPC U parameter implies runoff no gate survives.
MAX_U_PARAM = 6

#: Rate gate: |predicted - observed| rate vector, with a noise term from the tracklet's
#: own endpoints (2 x 0.3" astrometric error over the span).
RATE_BASE_ARCSEC_HR = 3.0
RATE_FRACTION = 0.25
RATE_ASTROM_ERR_ARCSEC = 0.3

#: Cap on Find_Orb joint fits per run; the coarse list is ranked by separation first.
MAX_FITS = 200


# ----------------------------------------------------------------------------------
# Phase A: orbits
# ----------------------------------------------------------------------------------

def load_orbits() -> tuple[list[AttribOrbit], dict[str, Any]]:
    stats = {"cached_responses": 0, "no_orbit": 0, "u_excluded": 0, "merged_duplicates": 0}
    by_primary: dict[str, AttribOrbit] = {}
    for path in sorted(ORBIT_CACHE.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        stats["cached_responses"] += 1
        if doc.get("status") != 200:
            stats["no_orbit"] += 1
            continue
        orbit = parse_mpc_orb(doc["doc"], requested_desig=doc.get("requested_desig", ""))
        if orbit is None:
            stats["no_orbit"] += 1
            continue
        if orbit.u_param is not None and orbit.u_param > MAX_U_PARAM:
            stats["u_excluded"] += 1
            continue
        if orbit.packed_primary in by_primary:
            stats["merged_duplicates"] += 1
            continue
        by_primary[orbit.packed_primary] = orbit
    stats["orbits"] = len(by_primary)
    return list(by_primary.values()), stats


# ----------------------------------------------------------------------------------
# Phase B: tracklets with rates
# ----------------------------------------------------------------------------------

def load_tracklets(mjd_min: float, mjd_max: float) -> pl.DataFrame:
    """Tracklets in the window, with endpoint sky rates (deg/day)."""
    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    obs = (
        pl.scan_parquet(config.ITF_PARQUET)
        .filter(pl.col("mjd").is_between(mjd_min - 1.0, mjd_max + 1.0))
        .filter(pl.col("desig") != "")
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
    )
    trk = (
        obs.group_by("desig", "obscode", "night")
        .agg(
            pl.len().alias("n_obs"),
            pl.col("mjd").min().alias("mjd_first"),
            pl.col("mjd").max().alias("mjd_last"),
            pl.col("ra_deg").sort_by("mjd").first().alias("ra_first"),
            pl.col("ra_deg").sort_by("mjd").last().alias("ra_last"),
            pl.col("dec_deg").sort_by("mjd").first().alias("dec_first"),
            pl.col("dec_deg").sort_by("mjd").last().alias("dec_last"),
            pl.col("ra_deg").mean().alias("ra_deg"),
            pl.col("dec_deg").mean().alias("dec_deg"),
            pl.col("mag").mean().alias("mag_mean"),
        )
        .with_columns(
            ((pl.col("mjd_first") + pl.col("mjd_last")) / 2).alias("mjd_mid"),
            (pl.col("mjd_last") - pl.col("mjd_first")).alias("span_days"),
        )
        .filter(pl.col("n_obs") >= 2)
        .collect()
    )
    # Endpoint rates; RA wrapped to +-180 so a tracklet straddling 0h does not
    # fabricate a 360-degree sprint. The RA component is the great-circle rate
    # (d(alpha)/dt * cos(dec)), matching itf_linker.link.arrows and predict().
    dra = ((pl.col("ra_last") - pl.col("ra_first") + 180.0) % 360.0) - 180.0
    span = pl.col("span_days")
    trk = trk.with_columns(
        pl.when(span > 0)
        .then(dra * (pl.col("dec_deg").radians()).cos() / span)
        .otherwise(None)
        .alias("rate_ra_cosdec_deg_day"),
        pl.when(span > 0)
        .then((pl.col("dec_last") - pl.col("dec_first")) / span)
        .otherwise(None)
        .alias("rate_dec_deg_day"),
    )
    return trk


# ----------------------------------------------------------------------------------
# Phase C/D: the sweep
# ----------------------------------------------------------------------------------

def envelope_fn() -> Any:
    """Piecewise-linear max-over-targets two-body error (arcsec) vs lookback (days)."""
    doc = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    grid: dict[float, float] = {}
    for tgt in doc["targets"].values():
        for label, arcsec in (tgt.get("sep_arcsec_by_lookback") or {}).items():
            days = float(label.rstrip("y")) * 365.25
            grid[days] = max(grid.get(days, 0.0), float(arcsec))
    xs = np.array(sorted(grid))
    ys = np.array([grid[x] for x in xs])
    # Enforce a monotonic envelope: the per-object curves oscillate with synodic
    # geometry, but a *gate* that shrinks with lookback would claim precision the
    # calibration never demonstrated.
    ys = np.maximum.accumulate(ys)

    def env(dt_days: np.ndarray) -> np.ndarray:
        return np.interp(np.abs(dt_days), xs, ys, left=ys[0], right=ys[-1])

    return env


def gate_radius_arcsec(dt_days: np.ndarray, u_param: int | None, env: Any) -> np.ndarray:
    runoff_per_decade = 0.01 * 10 ** (0.868 * (u_param if u_param is not None else 5))
    return (
        GATE_FLOOR_ARCSEC
        + GATE_ENVELOPE_SAFETY * env(dt_days)
        + runoff_per_decade * np.abs(dt_days) / 3652.5
    )


def sweep_orbit(
    orbit: AttribOrbit,
    trk: pl.DataFrame,
    nights: dict[int, np.ndarray],
    night_mjd: dict[int, float],
    env: Any,
) -> list[dict[str, Any]]:
    """Coarse candidates for one orbit: night-level cut, then exact per-tracklet gate."""
    cols = {
        c: trk[c].to_numpy()
        for c in (
            "ra_deg", "dec_deg", "mjd_mid", "span_days",
            "rate_ra_cosdec_deg_day", "rate_dec_deg_day", "mag_mean",
        )
    }
    night_ids = np.array(sorted(nights))
    night_ts = np.array([night_mjd[n] for n in night_ids])
    dt = night_ts + config_tt_offset() - orbit.epoch_mjd_tt
    in_window = np.abs(dt) <= MAX_LOOKBACK_DAYS
    if not np.any(in_window):
        return []
    pred_n = predict(orbit, night_ts[in_window])
    radius_n = gate_radius_arcsec(dt[in_window], orbit.u_param, env)
    rate_n = np.hypot(
        pred_n["rate_ra_cosdec_deg_day"], pred_n["rate_dec_deg_day"]
    )  # deg/day
    margin_deg = radius_n / 3600.0 + rate_n * 0.7  # within-night motion allowance

    stage1_rows: list[np.ndarray] = []
    stage1_dt: list[np.ndarray] = []
    for i, night in enumerate(night_ids[in_window]):
        idx = nights[int(night)]
        sep = separation_deg(
            np.full(idx.shape, pred_n["ra_deg"][i]),
            np.full(idx.shape, pred_n["dec_deg"][i]),
            cols["ra_deg"][idx],
            cols["dec_deg"][idx],
        )
        keep = sep <= margin_deg[i]
        if np.any(keep):
            stage1_rows.append(idx[keep])
            stage1_dt.append(np.full(int(keep.sum()), dt[in_window][i]))
    if not stage1_rows:
        return []
    rows = np.concatenate(stage1_rows)
    # Exact pass at each surviving tracklet's own epoch.
    t_mid = cols["mjd_mid"][rows]
    pred = predict(orbit, t_mid)
    dt_exact = t_mid + config_tt_offset() - orbit.epoch_mjd_tt
    radius = gate_radius_arcsec(dt_exact, orbit.u_param, env)
    sep_arcsec = 3600.0 * separation_deg(
        pred["ra_deg"], pred["dec_deg"], cols["ra_deg"][rows], cols["dec_deg"][rows]
    )
    pos_ok = (sep_arcsec <= radius) & pred["kepler_ok"]

    # Rate-vector gate, arcsec/hr; inactive where the tracklet cannot measure a rate.
    to_ash = 3600.0 / 24.0
    pr_ra = pred["rate_ra_cosdec_deg_day"] * to_ash
    pr_de = pred["rate_dec_deg_day"] * to_ash
    tr_ra = cols["rate_ra_cosdec_deg_day"][rows] * to_ash
    tr_de = cols["rate_dec_deg_day"][rows] * to_ash
    span_hr = np.maximum(cols["span_days"][rows] * 24.0, 1e-6)
    noise = 2.0 * RATE_ASTROM_ERR_ARCSEC / span_hr
    tol = RATE_BASE_ARCSEC_HR + RATE_FRACTION * np.hypot(pr_ra, pr_de) + noise
    drate = np.hypot(pr_ra - tr_ra, pr_de - tr_de)
    rate_known = np.isfinite(tr_ra) & np.isfinite(tr_de)
    rate_ok = ~rate_known | (drate <= tol)

    out = []
    for j in np.nonzero(pos_ok & rate_ok)[0]:
        r = int(rows[j])
        out.append(
            {
                "row": r,
                "dt_days": float(dt_exact[j]),
                "sep_arcsec": float(sep_arcsec[j]),
                "gate_radius_arcsec": float(radius[j]),
                "rate_pred_arcsec_hr": [float(pr_ra[j]), float(pr_de[j])],
                "rate_obs_arcsec_hr": (
                    [float(tr_ra[j]), float(tr_de[j])] if rate_known[j] else None
                ),
                "drate_arcsec_hr": float(drate[j]) if rate_known[j] else None,
                "rate_gated": bool(rate_known[j]),
                "v_pred": float(pred["v_pred"][j]),
                "delta_au": float(pred["delta_au"][j]),
            }
        )
    return out


def config_tt_offset() -> float:
    from itf_linker.link.geometry import TT_MINUS_UTC_DAYS

    return TT_MINUS_UTC_DAYS


# ----------------------------------------------------------------------------------
# Phase E: joint Find_Orb fits
# ----------------------------------------------------------------------------------

def get_obs80_cached(desig: str) -> list[str]:
    OBS80_CACHE.mkdir(parents=True, exist_ok=True)
    dest = OBS80_CACHE / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not dest.exists():
        time.sleep(1.1)
        resp = requests.get(
            OBS_URL,
            json={"desigs": [desig], "output_format": ["OBS80"]},
            headers={"User-Agent": USER_AGENT},
            timeout=120,
        )
        resp.raise_for_status()
        doc = resp.json()
        block = (doc[0] if isinstance(doc, list) else doc).get("OBS80") or ""
        dest.write_text(block, encoding="utf-8", newline="\n")
    return [ln for ln in dest.read_text(encoding="utf-8").splitlines() if ln.strip()]


def joint_fit(
    tag: str,
    orbit: AttribOrbit,
    trk_lines: list[str],
    shell: Any,
    baseline_cache: dict[str, Any],
) -> dict[str, Any]:
    """Fit object astrometry + tracklet lines together; also the object-only baseline."""
    obj_lines = get_obs80_cached(orbit.primary_desig)

    if orbit.primary_desig not in baseline_cache:
        # 7 characters (trkSub field width), and the lines are RELABELLED under it: a
        # merged object's published astrometry carries two or three packed designations
        # (2025 MH98 = K25M98H + K25N71B + K25PC6D), and unrelabelled lines would be
        # fitted by fo as separate fragments -- a "baseline" of the wrong thing.
        base_tag = f"m7b{len(baseline_cache):04d}"
        cfg = prepare_config_dir(shell, base_tag)
        run = run_fo(
            [_relabel(ln, base_tag) for ln in obj_lines],
            FIT_ROOT / base_tag,
            designations=[base_tag],
            shell=shell,
            config_dir=cfg,
            timeout=600,
            scratch_dir=f"$HOME/.cache/itf-linker-fo-work/{base_tag}",
        )
        fit = run.results.get(base_tag) or next(iter(run.results.values()), None)
        baseline_cache[orbit.primary_desig] = {
            "rms": fit.rms_residual if fit else None,
            "converged": bool(fit.converged) if fit else False,
            "n_used": fit.n_used if fit else None,
        }
    baseline = baseline_cache[orbit.primary_desig]

    joint = [_relabel(ln, tag) for ln in obj_lines] + [
        _relabel(ln, tag) for ln in trk_lines
    ]
    cfg = prepare_config_dir(shell, tag)
    run = run_fo(
        joint,
        FIT_ROOT / tag,
        designations=[tag],
        shell=shell,
        config_dir=cfg,
        timeout=600,
        scratch_dir=f"$HOME/.cache/itf-linker-fo-work/{tag}",
    )
    fit = run.results.get(tag) or next(iter(run.results.values()), None)
    if fit is None:
        return {"status": "fo_returned_nothing", "baseline": baseline}

    # Which residual rows are the tracklet's? Match on obscode + JD window.
    trk_obs = [o for o in (parse_line(ln, strict=False) for ln in trk_lines) if o]
    jd_lo = min(o.mjd for o in trk_obs) + 2400000.5 - 2e-4
    jd_hi = max(o.mjd for o in trk_obs) + 2400000.5 + 2e-4
    obscode = trk_obs[0].obscode
    # Field name is ``obscode`` in fo's residual records (verified against a live
    # total.json -- ``obs_code`` matches nothing and would silently report every
    # tracklet as unused).
    trk_resids = [
        r
        for r in fit.residuals
        if r.get("obscode") == obscode and jd_lo <= float(r.get("JD", 0)) <= jd_hi
    ]
    used = [r for r in trk_resids if r.get("incl")]
    max_trk_resid = None
    for r in used:
        d = (float(r.get("dRA", 0)) ** 2 + float(r.get("dDec", 0)) ** 2) ** 0.5
        max_trk_resid = d if max_trk_resid is None else max(max_trk_resid, d)

    nights = {int(o.mjd + 0.5) for o in trk_obs}
    for ln in obj_lines:
        o = parse_line(ln, strict=False)
        if o:
            nights.add(int(o.mjd + 0.5))
    all_mjds = [o.mjd for o in trk_obs] + [
        o.mjd for o in (parse_line(ln, strict=False) for ln in obj_lines) if o
    ]
    arc_days = max(all_mjds) - min(all_mjds)

    strict = post_fit_gate(fit, n_nights=len(nights))
    published = mpc_published_gate(fit, n_nights=len(nights), arc_days=arc_days)

    return {
        "status": fit.status,
        "converged": bool(fit.converged),
        "rms_joint": fit.rms_residual,
        "n_obs": fit.n_obs,
        "n_used": fit.n_used,
        "a": fit.a,
        "e": fit.e,
        "incl": fit.incl,
        "trk_obs_total": len(trk_obs),
        "trk_obs_in_resids": len(trk_resids),
        "trk_obs_used": len(used),
        "trk_max_resid_arcsec": max_trk_resid,
        "arc_days_joint": arc_days,
        "n_nights_joint": len(nights),
        "gate_strict": strict.as_dict(),
        "gate_mpc_published": published.as_dict(),
        "baseline": baseline,
        "perturbers": fit.perturbers_label,
    }


# ----------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-fits", type=int, default=MAX_FITS)
    ap.add_argument("--skip-fits", action="store_true", help="coarse sweep + control only")
    args = ap.parse_args()

    t0 = time.monotonic()
    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "itf_provenance": json.loads(
            config.ITF_PROVENANCE.read_text(encoding="utf-8")
        ),
        "parameters": {
            "max_lookback_days": MAX_LOOKBACK_DAYS,
            "gate_floor_arcsec": GATE_FLOOR_ARCSEC,
            "gate_envelope_safety": GATE_ENVELOPE_SAFETY,
            "max_u_param": MAX_U_PARAM,
            "rate_base_arcsec_hr": RATE_BASE_ARCSEC_HR,
            "rate_fraction": RATE_FRACTION,
            "rate_astrom_err_arcsec": RATE_ASTROM_ERR_ARCSEC,
        },
    }

    orbits, orbit_stats = load_orbits()
    report["orbits"] = orbit_stats
    print(f"orbits: {orbit_stats}", flush=True)

    epochs = np.array([o.epoch_mjd_tt for o in orbits])
    mjd_min = float(epochs.min() - MAX_LOOKBACK_DAYS)
    mjd_max = float(epochs.max() + MAX_LOOKBACK_DAYS)
    trk = load_tracklets(mjd_min, mjd_max)
    report["tracklets_in_window"] = trk.height
    print(f"tracklets in window [{mjd_min:.0f}, {mjd_max:.0f}]: {trk.height}", flush=True)

    night_col = trk["night"].to_numpy()
    mjd_col = trk["mjd_mid"].to_numpy()
    nights: dict[int, np.ndarray] = {}
    night_mjd: dict[int, float] = {}
    for n in np.unique(night_col):
        mask = night_col == n
        nights[int(n)] = np.nonzero(mask)[0]
        night_mjd[int(n)] = float(np.median(mjd_col[mask]))

    env = envelope_fn()

    def run_sweep(orbit_list: list[AttribOrbit], label: str) -> list[dict[str, Any]]:
        found = []
        for k, orbit in enumerate(orbit_list):
            for m in sweep_orbit(orbit, trk, nights, night_mjd, env):
                m["orbit_desig"] = orbit.primary_desig
                found.append(m)
            if (k + 1) % 50 == 0:
                print(f"  {label}: {k + 1}/{len(orbit_list)} orbits, "
                      f"{len(found)} matches", flush=True)
        return found

    print("real sweep:", flush=True)
    real = run_sweep(orbits, "real")
    print(f"real coarse matches: {len(real)}", flush=True)

    print("control sweep (half-period phase shift):", flush=True)
    controls = [control_orbit(o) for o in orbits]
    fake = run_sweep(controls, "control")
    print(f"control coarse matches: {len(fake)}", flush=True)

    #: Bin edges chosen so the smallest bin is well inside the measured short-lookback
    #: two-body error (a true attribution at |dt| < 1 y should land < 60"), while chance
    #: matches scale with enclosed area and pile into the outer bins.
    SEP_BINS = [0.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1000.0, 2000.0, float("inf")]

    def summarise(matches: list[dict[str, Any]]) -> dict[str, Any]:
        if not matches:
            return {"n": 0}
        seps = np.array([m["sep_arcsec"] for m in matches])
        hist = {
            f"[{int(lo)},{int(hi) if hi != float('inf') else 'inf'})": int(
                ((seps >= lo) & (seps < hi)).sum()
            )
            for lo, hi in itertools.pairwise(SEP_BINS)
        }
        return {
            "n": len(matches),
            "n_orbits_with_match": len({m["orbit_desig"] for m in matches}),
            "rate_gated": int(sum(1 for m in matches if m["rate_gated"])),
            "sep_arcsec_median": float(np.median(seps)),
            "dt_days_median": float(np.median([abs(m["dt_days"]) for m in matches])),
            "sep_arcsec_hist": hist,
        }

    report["coarse"] = {"real": summarise(real), "control": summarise(fake)}

    # Attach tracklet identity to the real matches, and rank by separation.
    keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid", "mag_mean").rows()
    for m in real:
        desig, obscode, night, n_obs, mjd_mid, mag = keys[m["row"]]
        m["trksub"] = desig
        m["obscode"] = obscode
        m["night"] = int(night)
        m["trk_n_obs"] = int(n_obs)
        m["trk_mjd_mid"] = float(mjd_mid)
        m["trk_mag_mean"] = None if mag is None else float(mag)
        m["link_key"] = link_key([(desig, obscode, int(night))])
        del m["row"]
    for m in fake:
        m.pop("row", None)
    real.sort(key=lambda m: m["sep_arcsec"])
    report["real_matches"] = real
    report["control_matches_sample"] = fake[:50]

    if not args.skip_fits and real:
        shell = default_shell()
        lon = fetch_obscodes()
        wanted = {m["trksub"] for m in real[: args.max_fits]}
        index, idx_stats = tracklet_line_index(wanted, lon)
        report["line_index_stats"] = {
            k: v for k, v in idx_stats.items() if not isinstance(v, (list, dict))
        }
        baseline_cache: dict[str, Any] = {}
        by_primary = {o.primary_desig: o for o in orbits}
        fits = []
        for i, m in enumerate(real[: args.max_fits]):
            # 7 characters exactly: the trkSub field is columns 6-12 and _relabel
            # truncates -- an 8-character tag would silently label the obs file with a
            # different name than the tag (harmless in these single-object runs, since
            # each fit has its own directory and the result is keyed by fallback, but
            # the 2026-08-16 run's obs.txt files carry truncated names because of it).
            tag = f"m7a{i:04d}"
            lines = index.get((m["trksub"], m["obscode"], m["night"]))
            if not lines:
                fits.append({**m, "fit": {"status": "tracklet_lines_missing"}})
                continue
            orbit = by_primary[m["orbit_desig"]]
            print(f"fit {tag}: {orbit.primary_desig} + {m['trksub']}/{m['obscode']}"
                  f"/night {m['night']}", flush=True)
            outcome = joint_fit(tag, orbit, lines, shell, baseline_cache)
            fits.append({**m, "fit": outcome, "fit_tag": tag})
        report["fits"] = fits
        passing = [
            f for f in fits
            if f.get("fit", {}).get("gate_strict", {}).get("passes")
            and f["fit"].get("trk_obs_used", 0) == f["fit"].get("trk_obs_total", -1)
        ]
        report["fits_passing_strict_and_fully_used"] = len(passing)
        print(f"fits: {len(fits)}, passing strict gate with tracklet fully used: "
              f"{len(passing)}", flush=True)

    report["elapsed_s"] = round(time.monotonic() - t0, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT} in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
