"""M8: attribute ITF tracklets to the FULL Rubin batches, perturbed. NOTHING IS SUBMITTED.

The M7 chain at production scale, with the two-body coarse gate replaced by the
perturbed backend (:mod:`itf_linker.attrib.perturbed`):

1. **Orbits** -- ``data/raw/rubin/m8-orbits.parquet`` (``scripts/m8_fetch_bulk.py``):
   every Feb + Apr batch object with a current MPC orbit, bulk-parsed and verified
   against the API route. U > 6 excluded, as M7.
2. **Tracklets** -- |t - epoch| <= 15 years: the lookback the *perturbed* calibration
   measured (``scripts/m8_calibration.py``; envelope <= ~94 arcsec, vs degree-scale
   two-body). Beyond 15 y is unmeasured and stays closed.
3. **Coarse sweep** -- per orbit chunk: one vectorised RK4 integration across the whole
   window, then a night-level dec-strip stage and an exact per-tracklet-epoch stage
   (light-time corrected, position + rate-vector gates). Gate radius: the M7 formula
   with the perturbed envelope -- floor 120" (orbit cross-track uncertainty + geocentric
   parallax, unchanged: it was never about the propagator) + 1.5 x envelope(|dt|) +
   the same U-runoff term.
4. **Control** -- the identical sweep against every orbit half a period out of phase.
   At M7's scale the coarse stage was chance-dominated (914 real vs 944 decoy); the
   control prices the fit queue here too.
5. **Joint fits** -- ranked by separation/gate (the best predictor of survival),
   batched, **checkpointed to disk after every fit** (``data/m8-fit-state.jsonl``) so a
   rerun resumes, and bounded by ``--max-fits`` / ``--time-budget-min`` with coverage
   reported honestly. Fit machinery is M7's: object's full published astrometry
   (get-obs OBS80, cache shared with M7) + verbatim ITF lines, relabelled under one
   7-char tag, fo with perturbers 7fe/DE-440, strict + published gates, and the
   "did fo actually use the tracklet" question as primary.

Outputs ``m8-attribution.json`` (root, gitignored). Candidates are candidates;
``scripts/m8_verdicts.py`` turns fits into the gated ledger v2.
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
sys.path.insert(0, str(ROOT / "scripts"))

import m7_attribution as m7run
import numpy as np
import polars as pl
import requests

from itf_linker import config
from itf_linker.attrib.perturbed import (
    DenseTrajectory,
    integrate_dense,
    predict_dense,
)
from itf_linker.fit.findorb import prepare_config_dir, run_fo
from itf_linker.fit.gates import mpc_published_gate, post_fit_gate
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import _relabel, link_key, tracklet_line_index
from itf_linker.link.geometry import TT_MINUS_UTC_DAYS, earth_heliocentric_posvel, propagate_kepler
from itf_linker.mpc80 import parse_line

ORBITS_PARQUET = ROOT / "data" / "raw" / "rubin" / "m8-orbits.parquet"
CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m8-calibration.json"
OBS80_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80"  # shared with M7
FIT_ROOT = ROOT / "data" / "m8-fits"
FIT_STATE = ROOT / "data" / "m8-fit-state.jsonl"
OUT = ROOT / "m8-attribution.json"

OBS_URL = "https://data.minorplanetcenter.net/api/get-obs"
USER_AGENT = (
    "itf-linker/0.4 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

#: Lookback bound, days: the range scripts/m8_calibration.py measured. NOT a preference.
MAX_LOOKBACK_DAYS = 15.0 * 365.25

#: Gate pieces -- M7's formula, M8's measured envelope. Floor and U-runoff unchanged:
#: they model the *orbit's* uncertainty and the geocentric approximation, which the
#: propagator swap does not touch.
GATE_FLOOR_ARCSEC = 120.0
GATE_ENVELOPE_SAFETY = 1.5
MAX_U_PARAM = 6

RATE_BASE_ARCSEC_HR = 3.0
RATE_FRACTION = 0.25
RATE_ASTROM_ERR_ARCSEC = 0.3

#: Orbits per integration chunk. 1,500 orbits x ~700 dense nodes x 6 doubles ~ 50 MB
#: and ~7 s of RK4; the night-stage arrays stay comfortably in memory.
ORBIT_CHUNK = 1500

SEP_BINS = [0.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1000.0, float("inf")]


# ----------------------------------------------------------------------------------
# Orbits
# ----------------------------------------------------------------------------------

def load_orbit_table() -> tuple[pl.DataFrame, dict[str, Any]]:
    df = pl.read_parquet(ORBITS_PARQUET)
    stats = {"rows": df.height}
    keep = df.filter(pl.col("u_param") <= MAX_U_PARAM)
    stats["u_excluded"] = df.height - keep.height  # u_param = -1 encodes "no U": kept
    stats["swept"] = keep.height
    stats["by_source"] = dict(keep.group_by("source").len().rows())
    return keep, stats


def orbit_arrays(df: pl.DataFrame) -> dict[str, np.ndarray]:
    return {
        "primary": np.array(df["primary"].to_list()),
        "epoch": df["epoch_mjd_tt"].to_numpy(),
        "r0": np.array(df["r0"].to_list(), dtype=float),
        "v0": np.array(df["v0"].to_list(), dtype=float),
        "h": df["h_mag"].fill_null(np.nan).to_numpy().astype(float),
        "g": df["g_slope"].fill_null(0.15).to_numpy().astype(float),
        "u": df["u_param"].to_numpy().astype(int),
    }


def control_states(r0: np.ndarray, v0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Half-period phase shift for every orbit at once (the amplitude-matched decoy)."""
    from itf_linker.link.geometry import GM_SUN

    r_norm = np.linalg.norm(r0, axis=1)
    v2 = np.einsum("ij,ij->i", v0, v0)
    a = 1.0 / (2.0 / r_norm - v2 / GM_SUN)
    half_period = np.pi * np.sqrt(np.clip(a, 1e-6, None) ** 3 / GM_SUN)
    r_new, v_new, conv = propagate_kepler(r0.copy(), v0.copy(), half_period)
    if not np.all(conv):  # pragma: no cover - bound MPC orbits always propagate
        bad = int((~conv).sum())
        raise RuntimeError(f"{bad} control propagations failed")
    return r_new, v_new


# ----------------------------------------------------------------------------------
# Gate
# ----------------------------------------------------------------------------------

def envelope_fn() -> Any:
    """Monotonic max-over-targets *perturbed* error (arcsec) vs |lookback| (days)."""
    doc = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    grid = {
        float(k.rstrip("y")) * 365.25: float(v)
        for k, v in doc["perturbed_envelope_arcsec"].items()
    }
    xs = np.array(sorted(grid))
    ys = np.maximum.accumulate(np.array([grid[x] for x in xs]))

    def env(dt_days: np.ndarray) -> np.ndarray:
        return np.interp(np.abs(dt_days), xs, ys, left=ys[0], right=ys[-1])

    return env


def gate_radius_arcsec(dt_days: np.ndarray, u_param: np.ndarray, env: Any) -> np.ndarray:
    """Vectorised over (pair) arrays; u_param -1 (unknown) takes the M7 default of 5."""
    u = np.where(u_param < 0, 5, u_param)
    runoff_per_decade = 0.01 * 10 ** (0.868 * u)
    return (
        GATE_FLOOR_ARCSEC
        + GATE_ENVELOPE_SAFETY * env(dt_days)
        + runoff_per_decade * np.abs(dt_days) / 3652.5
    )


# ----------------------------------------------------------------------------------
# The sweep
# ----------------------------------------------------------------------------------

class NightIndex:
    """Per-night tracklet arrays, dec-sorted, for the vectorised strip search.

    Earth's heliocentric state at every night midpoint is precomputed here in **one**
    vectorised astropy call: the sweep visits each night once per orbit chunk, and a
    per-night scalar ephemeris call (~ms of astropy Time overhead each) would cost
    minutes across 5k nights x tens of chunks x two sweeps.
    """

    def __init__(self, trk: pl.DataFrame, lon: dict[str, float]):
        self.cols = {
            c: trk[c].to_numpy()
            for c in ("ra_deg", "dec_deg", "mjd_mid", "span_days",
                      "rate_ra_cosdec_deg_day", "rate_dec_deg_day", "mag_mean")
        }
        night_col = trk["night"].to_numpy()
        self.night_ids = np.unique(night_col)
        self.per_night: dict[int, dict[str, np.ndarray]] = {}
        self.night_mjd: dict[int, float] = {}
        for n in self.night_ids:
            mask = night_col == n
            rows = np.nonzero(mask)[0]
            order = np.argsort(self.cols["dec_deg"][rows])
            rows = rows[order]
            self.per_night[int(n)] = {
                "rows": rows,
                "dec": self.cols["dec_deg"][rows],
                "ra": self.cols["ra_deg"][rows],
            }
            self.night_mjd[int(n)] = float(np.median(self.cols["mjd_mid"][rows]))
        ts = np.array([self.night_mjd[int(n)] for n in self.night_ids])
        e_pos, e_vel = earth_heliocentric_posvel(ts)
        self.earth = {
            int(n): (e_pos[i], e_vel[i]) for i, n in enumerate(self.night_ids)
        }


def sweep_chunk(
    traj: DenseTrajectory,
    epochs: np.ndarray,
    u_param: np.ndarray,
    nightindex: NightIndex,
    env: Any,
    *,
    h_mag: np.ndarray | None = None,
    g_slope: np.ndarray | None = None,
    stage2_batch: int = 200_000,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Coarse candidates for one integrated chunk.

    Returns ``(orbit_local_idx, trk_row, stage2 dict)`` for pairs passing the exact
    position + rate gates at the tracklet's own epoch.
    """
    n_orb = traj.n_orbits
    night_ids = np.array(sorted(nightindex.night_mjd))
    night_ts = np.array([nightindex.night_mjd[int(n)] for n in night_ids])
    t_lo, t_hi = float(traj.node_t[0]), float(traj.node_t[-1])
    usable = (night_ts + TT_MINUS_UTC_DAYS >= t_lo) & (night_ts + TT_MINUS_UTC_DAYS <= t_hi)

    # Stage 1: per night, all chunk orbits at once; dec strip then exact separation.
    pair_orb: list[np.ndarray] = []
    pair_row: list[np.ndarray] = []
    all_idx = np.arange(n_orb)
    for night, t_night in zip(night_ids[usable], night_ts[usable]):
        dt = t_night + TT_MINUS_UTC_DAYS - epochs
        in_window = np.abs(dt) <= MAX_LOOKBACK_DAYS
        if not np.any(in_window):
            continue
        idx = all_idx[in_window]
        r_obj, v_obj = traj.state_at(
            np.full(idx.size, t_night + TT_MINUS_UTC_DAYS), idx
        )
        # Geocentric direction without light time; the margin absorbs it (<= rate*0.04 d,
        # far under the 0.7 d within-night allowance).
        e_pos, e_vel = nightindex.earth[int(night)]
        dvec = r_obj - e_pos
        delta = np.linalg.norm(dvec, axis=1)
        dec_pred = np.degrees(np.arcsin(np.clip(dvec[:, 2] / delta, -1, 1)))
        ra_pred = np.degrees(np.arctan2(dvec[:, 1], dvec[:, 0])) % 360.0
        # Apparent-rate *upper bound* for the margin: |v_obj - v_earth| / delta bounds
        # the tangential component. Earth's own 0.017 AU/day dominates a main-belt
        # object's apparent motion, so it must be inside the bound, not outside it.
        rate_deg_day = np.degrees(np.linalg.norm(v_obj - e_vel, axis=1) / delta)
        radius = gate_radius_arcsec(dt[in_window], u_param[in_window], env)
        margin = radius / 3600.0 + rate_deg_day * 0.7

        night_data = nightindex.per_night[int(night)]
        dec_sorted = night_data["dec"]
        lo = np.searchsorted(dec_sorted, dec_pred - margin, side="left")
        hi = np.searchsorted(dec_sorted, dec_pred + margin, side="right")
        cnt = hi - lo
        keep = cnt > 0
        if not np.any(keep):
            continue
        lo, cnt = lo[keep], cnt[keep]
        kept_idx = idx[keep]
        kept_ra = ra_pred[keep]
        kept_dec = dec_pred[keep]
        kept_margin = margin[keep]
        # Ragged expansion in bounded slices: a dense survey night whose tracklets sit
        # in a narrow dec band can put a large fraction of the night inside every
        # orbit's strip -- expanding all kept orbits at once would allocate
        # multi-GB pair arrays. 4M pairs/slice keeps the peak under ~200 MB.
        total = int(cnt.sum())
        cuts = [0]
        if total > 4_000_000:
            acc = 0
            for k, c in enumerate(cnt):
                acc += int(c)
                if acc >= 4_000_000:
                    cuts.append(k + 1)
                    acc = 0
        cuts.append(cnt.size)
        for a, b in itertools.pairwise(dict.fromkeys(cuts)):
            lo_s, cnt_s = lo[a:b], cnt[a:b]
            if not cnt_s.size:
                continue
            starts = np.cumsum(cnt_s) - cnt_s
            offs = np.arange(int(cnt_s.sum())) - np.repeat(starts, cnt_s)
            cand = np.repeat(lo_s, cnt_s) + offs
            # exact separation on the dec-strip candidates
            ra_t = night_data["ra"][cand]
            dec_t = dec_sorted[cand]
            rep = np.repeat(np.arange(a, b), cnt_s)
            dra = np.abs((ra_t - kept_ra[rep] + 180.0) % 360.0 - 180.0)
            cosd = np.cos(np.radians(kept_dec[rep]))
            sep2 = (dra * cosd) ** 2 + (dec_t - kept_dec[rep]) ** 2
            ok = sep2 <= kept_margin[rep] ** 2
            if not np.any(ok):
                continue
            pair_orb.append(kept_idx[rep[ok]])
            pair_row.append(night_data["rows"][cand[ok]])

    if not pair_orb:
        empty = np.array([], dtype=int)
        return empty, empty, {}

    orb_all = np.concatenate(pair_orb)
    row_all = np.concatenate(pair_row)

    # Stage 2: exact, light-time-corrected prediction at each tracklet's own epoch.
    keep_orb: list[np.ndarray] = []
    keep_row: list[np.ndarray] = []
    keep_data: dict[str, list[np.ndarray]] = {
        k: [] for k in ("dt_days", "sep_arcsec", "gate_radius_arcsec", "pr_ra", "pr_de",
                        "tr_ra", "tr_de", "drate", "rate_known", "v_pred", "delta_au",
                        "encounter")
    }
    cols = nightindex.cols
    for s in range(0, orb_all.size, stage2_batch):
        oi = orb_all[s : s + stage2_batch]
        ri = row_all[s : s + stage2_batch]
        t_mid = cols["mjd_mid"][ri]
        pred = predict_dense(
            traj, oi, t_mid,
            h_mag=None if h_mag is None else h_mag[oi],
            g_slope=None if g_slope is None else g_slope[oi],
        )
        dt_exact = t_mid + TT_MINUS_UTC_DAYS - epochs[oi]
        radius = gate_radius_arcsec(dt_exact, u_param[oi], env)
        dra = np.abs((cols["ra_deg"][ri] - pred["ra_deg"] + 180.0) % 360.0 - 180.0)
        cosd = np.cos(np.radians(pred["dec_deg"]))
        sep = 3600.0 * np.hypot(dra * cosd, cols["dec_deg"][ri] - pred["dec_deg"])
        pos_ok = sep <= radius

        to_ash = 3600.0 / 24.0
        pr_ra = pred["rate_ra_cosdec_deg_day"] * to_ash
        pr_de = pred["rate_dec_deg_day"] * to_ash
        tr_ra = cols["rate_ra_cosdec_deg_day"][ri] * to_ash
        tr_de = cols["rate_dec_deg_day"][ri] * to_ash
        span_hr = np.maximum(cols["span_days"][ri] * 24.0, 1e-6)
        noise = 2.0 * RATE_ASTROM_ERR_ARCSEC / span_hr
        tol = RATE_BASE_ARCSEC_HR + RATE_FRACTION * np.hypot(pr_ra, pr_de) + noise
        drate = np.hypot(pr_ra - tr_ra, pr_de - tr_de)
        rate_known = np.isfinite(tr_ra) & np.isfinite(tr_de)
        rate_ok = ~rate_known | (drate <= tol)

        final = pos_ok & rate_ok
        keep_orb.append(oi[final])
        keep_row.append(ri[final])
        keep_data["dt_days"].append(dt_exact[final])
        keep_data["sep_arcsec"].append(sep[final])
        keep_data["gate_radius_arcsec"].append(radius[final])
        keep_data["pr_ra"].append(pr_ra[final])
        keep_data["pr_de"].append(pr_de[final])
        keep_data["tr_ra"].append(tr_ra[final])
        keep_data["tr_de"].append(tr_de[final])
        keep_data["drate"].append(drate[final])
        keep_data["rate_known"].append(rate_known[final])
        keep_data["v_pred"].append(pred["v_pred"][final])
        keep_data["delta_au"].append(pred["delta_au"][final])
        keep_data["encounter"].append(pred["encounter"][final])

    return (
        np.concatenate(keep_orb),
        np.concatenate(keep_row),
        {k: np.concatenate(v) for k, v in keep_data.items()},
    )


def run_sweep(
    arrays: dict[str, np.ndarray],
    nightindex: NightIndex,
    env: Any,
    *,
    decoy: bool,
    label: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    n = arrays["epoch"].shape[0]
    r0, v0 = arrays["r0"], arrays["v0"]
    if decoy:
        r0, v0 = control_states(r0, v0)
    matches: list[dict[str, Any]] = []
    timing = {"integrate_s": 0.0, "sweep_s": 0.0, "encounter_orbits": 0}
    night_ts = np.array(sorted(nightindex.night_mjd.values()))
    for start in range(0, n, ORBIT_CHUNK):
        sl = slice(start, min(start + ORBIT_CHUNK, n))
        epochs = arrays["epoch"][sl]
        epoch0 = float(np.median(epochs))
        if np.ptp(epochs) > 1e-6:
            # Mixed epochs inside a chunk (get-orb fallback rows): integrate from the
            # newest epoch; each orbit is first two-body'd to the common epoch over its
            # tiny epoch gap (<= months, error << floor).
            epoch_common = float(epochs.max())
            dt0 = epoch_common - epochs
            r_c, v_c, conv = propagate_kepler(
                r0[sl].copy(), v0[sl].copy(), dt0
            )
            if not np.all(conv):
                raise RuntimeError("epoch-alignment propagation failed")
        else:
            epoch_common = epoch0
            r_c, v_c = r0[sl], v0[sl]
        t_min = float(min(night_ts.min() + TT_MINUS_UTC_DAYS,
                          epoch_common - MAX_LOOKBACK_DAYS)) - 2.0
        t_min = max(t_min, epoch_common - MAX_LOOKBACK_DAYS - 2.0)
        t0 = time.monotonic()
        traj = integrate_dense(r_c, v_c, epoch_common, t_min, epoch_common,
                               h_days=1.0, dense_every=8)
        timing["integrate_s"] += time.monotonic() - t0
        timing["encounter_orbits"] += int(traj.encounter.sum())
        t0 = time.monotonic()
        oi, ri, data = sweep_chunk(
            traj, epochs, arrays["u"][sl], nightindex, env,
            h_mag=arrays["h"][sl], g_slope=arrays["g"][sl],
        )
        timing["sweep_s"] += time.monotonic() - t0
        for j in range(oi.size):
            g = int(oi[j]) + start
            matches.append(
                {
                    "orbit_desig": str(arrays["primary"][g]),
                    "orbit_row": g,
                    "row": int(ri[j]),
                    "dt_days": float(data["dt_days"][j]),
                    "sep_arcsec": float(data["sep_arcsec"][j]),
                    "gate_radius_arcsec": float(data["gate_radius_arcsec"][j]),
                    "rate_pred_arcsec_hr": [float(data["pr_ra"][j]), float(data["pr_de"][j])],
                    "rate_obs_arcsec_hr": (
                        [float(data["tr_ra"][j]), float(data["tr_de"][j])]
                        if bool(data["rate_known"][j]) else None
                    ),
                    "drate_arcsec_hr": float(data["drate"][j]) if bool(data["rate_known"][j]) else None,
                    "rate_gated": bool(data["rate_known"][j]),
                    "v_pred": float(data["v_pred"][j]),
                    "delta_au": float(data["delta_au"][j]),
                    "encounter": bool(data["encounter"][j]),
                }
            )
        done = min(start + ORBIT_CHUNK, n)
        print(f"  {label}: {done}/{n} orbits, {len(matches)} matches "
              f"(int {timing['integrate_s']:.0f} s, sweep {timing['sweep_s']:.0f} s)",
              flush=True)
    return matches, timing


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
        "encounter_flagged": int(sum(1 for m in matches if m.get("encounter"))),
        "sep_arcsec_median": float(np.median(seps)),
        "dt_days_median": float(np.median([abs(m["dt_days"]) for m in matches])),
        "dt_years_beyond_m7_window": int(
            sum(1 for m in matches if abs(m["dt_days"]) > 4.0 * 365.25)
        ),
        "sep_arcsec_hist": hist,
    }


# ----------------------------------------------------------------------------------
# Joint fits (M7's machinery, M8's tags and roots -- M7's artefacts stay untouched)
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
    base_tag: str,
    orbit_desig: str,
    trk_lines: list[str],
    shell: Any,
    baseline_cache: dict[str, Any],
) -> dict[str, Any]:
    """Identical logic to M7's joint_fit; own tags/roots so M7's runs stay pristine."""
    obj_lines = get_obs80_cached(orbit_desig)

    if orbit_desig not in baseline_cache:
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
        baseline_cache[orbit_desig] = {
            "rms": fit.rms_residual if fit else None,
            "converged": bool(fit.converged) if fit else False,
            "n_used": fit.n_used if fit else None,
        }
    baseline = baseline_cache[orbit_desig]

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

    trk_obs = [o for o in (parse_line(ln, strict=False) for ln in trk_lines) if o]
    jd_lo = min(o.mjd for o in trk_obs) + 2400000.5 - 2e-4
    jd_hi = max(o.mjd for o in trk_obs) + 2400000.5 + 2e-4
    obscode = trk_obs[0].obscode
    # fo's residual records name the station ``obscode`` (M7 trap 4).
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
    all_mjds = [o.mjd for o in trk_obs]
    for ln in obj_lines:
        o = parse_line(ln, strict=False)
        if o:
            nights.add(int(o.mjd + 0.5))
            all_mjds.append(o.mjd)
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


def load_fit_state() -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    if FIT_STATE.exists():
        for line in FIT_STATE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                state[rec["fit_key"]] = rec
    return state


def append_fit_state(rec: dict[str, Any]) -> None:
    FIT_STATE.parent.mkdir(parents=True, exist_ok=True)
    with FIT_STATE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


# ----------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-fits", type=int, default=1200)
    ap.add_argument("--time-budget-min", type=float, default=120.0,
                    help="fit-phase budget; the sweep always completes")
    ap.add_argument("--skip-fits", action="store_true")
    ap.add_argument("--resume-sweep", action="store_true",
                    help="reuse the coarse sweep in an existing m8-attribution.json")
    ap.add_argument("--itf-parquet", type=Path, default=None,
                    help="observation table override (M9: the daily archive re-pulls "
                         "the ITF under this repo, so a resumed queue must point back "
                         "at the snapshot it was built from -- see "
                         "scripts/m9_reconstruct_snapshot.py)")
    ap.add_argument("--max-new-fits", type=int, default=None,
                    help="cap on fits actually run this invocation (checkpoint reuse "
                         "does not count). Default: no cap beyond --max-fits")
    ap.add_argument("--pass-floor-per-100", type=int, default=None,
                    help="M9 pre-registered stopping rule: after every 100 new fits, "
                         "stop when the trailing-100 strict+fully-used pass rate "
                         "drops below this floor. Default: off (M8 behaviour)")
    args = ap.parse_args()

    if args.itf_parquet is not None:
        config.ITF_PARQUET = args.itf_parquet  # m7run.load_tracklets reads this module attr

    t_start = time.monotonic()
    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "itf_provenance": json.loads(config.ITF_PROVENANCE.read_text(encoding="utf-8")),
        "parameters": {
            "itf_parquet": str(config.ITF_PARQUET),
            "max_lookback_days": MAX_LOOKBACK_DAYS,
            "gate_floor_arcsec": GATE_FLOOR_ARCSEC,
            "gate_envelope_safety": GATE_ENVELOPE_SAFETY,
            "max_u_param": MAX_U_PARAM,
            "rate_base_arcsec_hr": RATE_BASE_ARCSEC_HR,
            "rate_fraction": RATE_FRACTION,
            "rate_astrom_err_arcsec": RATE_ASTROM_ERR_ARCSEC,
            "orbit_chunk": ORBIT_CHUNK,
            "backend": "perturbed (sun + 8 planets, RK4 h=1d, dense hermite)",
        },
    }

    if args.resume_sweep and OUT.exists():
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        real = prev["real_matches"]
        report.update({k: prev[k] for k in
                       ("orbits", "tracklets_in_window", "coarse", "sweep_timing",
                        "nights_in_window")
                       if k in prev})
        report["control_matches_sample"] = prev.get("control_matches_sample", [])
        # The resumed report must carry the queue forward: the 2026-08-17 tranche-2 run
        # dropped ``real_matches`` from the final write because this line was missing,
        # which silently destroyed the ranked queue a later --resume-sweep depends on
        # (M9 rebuilt it from the reconstructed snapshot).
        report["real_matches"] = real
        print(f"resumed sweep: {len(real)} real matches from {OUT.name}", flush=True)
    else:
        df, orbit_stats = load_orbit_table()
        report["orbits"] = orbit_stats
        print(f"orbits: {orbit_stats}", flush=True)
        arrays = orbit_arrays(df)

        mjd_min = float(arrays["epoch"].min() - MAX_LOOKBACK_DAYS)
        mjd_max = float(arrays["epoch"].max() + 1.0)
        trk = m7run.load_tracklets(mjd_min, mjd_max)
        report["tracklets_in_window"] = trk.height
        print(f"tracklets in window [{mjd_min:.0f}, {mjd_max:.0f}]: {trk.height}",
              flush=True)

        lon = fetch_obscodes()
        nightindex = NightIndex(trk, lon)
        report["nights_in_window"] = len(nightindex.night_mjd)
        env = envelope_fn()

        print("real sweep:", flush=True)
        real, t_real = run_sweep(arrays, nightindex, env, decoy=False, label="real")
        print("control sweep (half-period phase shift):", flush=True)
        fake, t_fake = run_sweep(arrays, nightindex, env, decoy=True, label="control")
        report["sweep_timing"] = {"real": t_real, "control": t_fake}
        report["coarse"] = {"real": summarise(real), "control": summarise(fake)}
        print(json.dumps(report["coarse"], indent=1), flush=True)

        # Attach tracklet identity; rank by separation normalised to the gate.
        keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid",
                          "mag_mean").rows()
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
        real.sort(key=lambda m: (m["encounter"],
                                 m["sep_arcsec"] / m["gate_radius_arcsec"]))
        report["real_matches"] = real
        report["control_matches_sample"] = fake[:100]
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"sweep written to {OUT.name}; {len(real)} real coarse candidates",
              flush=True)

    if args.skip_fits or not real:
        report.setdefault("real_matches", real if real else [])
        report["elapsed_s"] = round(time.monotonic() - t_start, 1)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {OUT} in {report['elapsed_s']} s (fits skipped)", flush=True)
        return

    # ---- fit phase: ranked, budgeted, checkpointed --------------------------------
    shell = default_shell()
    lon = fetch_obscodes()
    state = load_fit_state()
    queue = [m for m in real]
    wanted = {m["trksub"] for m in queue[: args.max_fits]}
    index, idx_stats = tracklet_line_index(wanted, lon)
    report["line_index_stats"] = {
        k: v for k, v in idx_stats.items() if not isinstance(v, (list, dict))
    }
    baseline_cache: dict[str, Any] = {}
    base_tags: dict[str, str] = {}
    fits: list[dict[str, Any]] = []
    new_outcomes: list[bool] = []  # strict+fully-used per NEW fit (stopping-rule input)
    stop_reason = None
    fit_deadline = time.monotonic() + args.time_budget_min * 60.0
    n_run = n_reused = 0
    t_fit_phase = time.monotonic()
    for i, m in enumerate(queue[: args.max_fits]):
        fit_key = f"{m['orbit_desig']}|{m['link_key']}"
        if fit_key in state:
            fits.append({**m, "fit": state[fit_key]["fit"],
                         "fit_tag": state[fit_key].get("fit_tag"), "reused": True})
            n_reused += 1
            continue
        if args.max_new_fits is not None and n_run >= args.max_new_fits:
            stop_reason = f"hard_budget({args.max_new_fits})"
            print(f"new-fit budget reached after {n_run} fits", flush=True)
            break
        if (args.pass_floor_per_100 is not None and n_run
                and n_run % 100 == 0 and len(new_outcomes) >= 100):
            rate = sum(new_outcomes[-100:])
            print(f"[rule] trailing-100 pass rate: {rate}/100", flush=True)
            if rate < args.pass_floor_per_100:
                stop_reason = (
                    f"trailing_100_pass_rate({rate})_below_floor({args.pass_floor_per_100})"
                )
                break
        if time.monotonic() > fit_deadline:
            stop_reason = f"time_budget({args.time_budget_min}min)"
            print(f"time budget reached after {n_run} fits", flush=True)
            break
        lines = index.get((m["trksub"], m["obscode"], m["night"]))
        if not lines:
            outcome: dict[str, Any] = {"status": "tracklet_lines_missing"}
        else:
            if m["orbit_desig"] not in base_tags:
                base_tags[m["orbit_desig"]] = f"m8b{len(base_tags):04d}"
            tag = f"m8a{i:04d}"  # 7 chars: the trkSub field width (M7 trap 5)
            print(f"fit {tag} [{i + 1}/{min(len(queue), args.max_fits)}]: "
                  f"{m['orbit_desig']} + {m['trksub']}/{m['obscode']}/n{m['night']} "
                  f"sep {m['sep_arcsec']:.0f}\"/{m['gate_radius_arcsec']:.0f}\"",
                  flush=True)
            outcome = joint_fit(tag, base_tags[m["orbit_desig"]], m["orbit_desig"],
                                lines, shell, baseline_cache)
        rec = {"fit_key": fit_key, "fit_tag": tag if lines else None, "fit": outcome,
               "orbit_desig": m["orbit_desig"], "trksub": m["trksub"],
               "obscode": m["obscode"], "night": m["night"],
               "link_key": m["link_key"]}
        append_fit_state(rec)
        state[fit_key] = rec
        fits.append({**m, "fit": outcome, "fit_tag": rec["fit_tag"]})
        new_outcomes.append(bool(
            outcome.get("gate_strict", {}).get("passes")
            and outcome.get("trk_obs_used", 0) == outcome.get("trk_obs_total", -1)
        ))
        n_run += 1
        if n_run % 25 == 0:
            report["fits"] = fits
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fit_phase_s = time.monotonic() - t_fit_phase
    report["fits"] = fits
    report["fit_phase"] = {
        "queued": len(queue),
        "cap": args.max_fits,
        "run": n_run,
        "reused_from_checkpoint": n_reused,
        "coverage_of_coarse": round(len(fits) / max(len(queue), 1), 4),
        "seconds": round(fit_phase_s, 1),
        "s_per_new_fit": round(fit_phase_s / n_run, 2) if n_run else None,
        "stop_reason": stop_reason or "cap_or_queue_end",
        "tranche_pass_rates_per_100": [
            sum(new_outcomes[k:k + 100])
            for k in range(0, len(new_outcomes), 100)
        ],
    }
    passing = [
        f for f in fits
        if f.get("fit", {}).get("gate_strict", {}).get("passes")
        and f["fit"].get("trk_obs_used", 0) == f["fit"].get("trk_obs_total", -1)
    ]
    report["fits_passing_strict_and_fully_used"] = len(passing)
    report["elapsed_s"] = round(time.monotonic() - t_start, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"fits: {len(fits)} ({n_run} new, {n_reused} checkpointed), "
          f"passing strict+fully-used: {len(passing)}", flush=True)
    print(f"wrote {OUT} in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
