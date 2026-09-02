"""M12: where the departures go. A random sample, attributed and then confirmed.

M12's series (``m12_series.py``) establishes the *shape* of the drain -- 167,829 genuine
departures, 99.6% of them whole designations vanishing at once -- but shape is not
destination. Two readings fit it equally well: the MPC is linking tracklets into known
objects (the ITF working as designed, and the thing that makes the candidate ledger
perishable), or it is discarding them (data loss, and a different story entirely).

The project already has a published-linkage confirmation, but only on rows it had
proposed: M9 checked 30 consumed candidates and M11 checked 103, matching each against
the named object's fresh published record. Those are ledger rows -- fitted, gated,
selected -- and there is no reason to assume a selected sample decays like the file. This
script runs the same confirmation on departures drawn at random from the file itself.

**Why a two-stage attribution.** Finding which object absorbed a tracklet means searching
the whole catalogue, and the MPC's own APIs will not do it: ``get-obs`` takes a
designation and rejects an ITF trksub outright ("Bad Label from designation identifier"),
so there is no trksub -> object lookup to call. The search is therefore local:

1. **Two-body prefilter.** Every MPCORB orbit is propagated by Kepler to the tracklet's
   epoch at once (vectorised over orbits, not epochs) and anything beyond
   ``PREFILTER_DEG`` is dropped. Two-body error over these lookbacks is large -- M7/M8
   measured 491-7,545 arcsec at 15-25 y -- which is exactly why the radius is degrees
   and not arcminutes. This stage is allowed to be sloppy; it is not allowed to be
   tight, and it must hand its survivors on **sorted by separation** (the first version
   did not, and confirmed 1 of 10 because the cap below then took an arbitrary subset).
2. **Perturbed refine.** The survivors are re-integrated with the real force model
   (``integrate_dense``, sun + 8 planets) and ranked by true separation. This is M8's
   backend, measured to 0.1-94 arcsec at 15 y.

**Why the confirmation is separate from the attribution.** A separation match says an
object *was in the right place*, which at a degree of tolerance is not evidence of
anything. The claim only becomes a claim when the object's **published record** turns out
to contain the departed observations themselves -- same station, within
``MATCH_SECONDS`` and ``MATCH_ARCSEC``, M9's duplicate rule. Attribution proposes;
get-obs disposes. A tracklet whose best attribution is 3 arcsec away but whose
observations are absent from that object's record counts as UNCONFIRMED, not as a hit.

**What this cannot see, stated up front.** A tracklet linked into an object that does not
exist in MPCORB -- a brand-new designation created by the link itself -- is invisible to a
catalogue search, and will be reported as UNCONFIRMED rather than as a refutation. The
sample's unconfirmed fraction is therefore an upper bound on "not a linkage", never a
measurement of it.

Writes ``m12-crosswalk.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
import polars as pl
import requests

from itf_linker.attrib.core import observables_from_states, separation_deg
from itf_linker.attrib.perturbed import integrate_dense, predict_dense
from itf_linker.link.geometry import (
    TT_MINUS_UTC_DAYS,
    earth_heliocentric_posvel,
    propagate_kepler,
)
from itf_linker.mpc80 import Mpc80ParseError, parse_line

OBS_URL = "https://data.minorplanetcenter.net/api/get-obs"
USER_AGENT = "itf-linker/M12 (matthew.e.potts@gmail.com) archive-series study"

# Deliberately loose: M7/M8 measured two-body error at 491-7,545 arcsec over 15-25 y, so
# a radius that sounds generous can still exclude the right object. The stage is allowed
# to be sloppy; it is not allowed to be tight.
PREFILTER_DEG = 3.0
# The CLOSEST this many by two-body separation (see prefilter). Measured on a 10-tracklet
# pilot: 60 confirmed 4, 400 confirmed 6, and the wall clock did not move -- the prefilter's
# 1.56M Kepler propagations dominate and the perturbed refine is nearly free by comparison.
# Set above the typical survivor count so the cap effectively never binds.
REFINE_KEEP = 4000
MATCH_SECONDS = 2.0        # M9's duplicate rule, both halves
MATCH_ARCSEC = 2.0
CONFIRM_DEPTH = 10         # how deep down the ranking get-obs is asked
SPAN_MARGIN_DAYS = 90.0    # light-time headroom on the integration span -- see refine()
REQUEST_SPACING_S = 1.2    # the MPC is a small free service; do not hammer it


# ----------------------------------------------------------------------------------
# Orbit catalogue
# ----------------------------------------------------------------------------------

def build_orbit_table(mpcorb_gz: Path, out: Path) -> pl.DataFrame:
    """Parse the whole extended file into the array layout the sweep wants, once."""
    from itf_linker.attrib.bulk import iter_mpcorb_objects, mpcorb_to_orbit

    if out.exists():
        print(f"orbit table cached: {out}", flush=True)
        return pl.read_parquet(out)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    t0 = time.monotonic()
    for i, obj in enumerate(iter_mpcorb_objects(mpcorb_gz)):
        orbit = mpcorb_to_orbit(obj)
        if orbit is None or orbit.primary_desig in seen:
            continue
        seen.add(orbit.primary_desig)
        rows.append({
            "primary": orbit.primary_desig,
            "epoch_mjd_tt": orbit.epoch_mjd_tt,
            "r0": list(orbit.r0),
            "v0": list(orbit.v0),
            "h_mag": orbit.h_mag,
            "g_slope": orbit.g_slope if orbit.g_slope is not None else 0.15,
            "u_param": orbit.u_param if orbit.u_param is not None else -1,
        })
        if (i + 1) % 200_000 == 0:
            print(f"  parsed {i + 1:,} objects, kept {len(rows):,} "
                  f"({time.monotonic() - t0:.0f} s)", flush=True)
    df = pl.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out, compression="zstd")
    print(f"orbit table: {df.height:,} orbits in {time.monotonic() - t0:.0f} s -> {out}",
          flush=True)
    return df


def orbit_arrays(df: pl.DataFrame) -> dict[str, np.ndarray]:
    return {
        "primary": np.array(df["primary"].to_list()),
        "epoch": df["epoch_mjd_tt"].to_numpy(),
        "r0": np.array(df["r0"].to_list(), dtype=float),
        "v0": np.array(df["v0"].to_list(), dtype=float),
        "h": df["h_mag"].fill_null(np.nan).to_numpy().astype(float),
        "g": df["g_slope"].fill_null(0.15).to_numpy().astype(float),
    }


# ----------------------------------------------------------------------------------
# The two stages
# ----------------------------------------------------------------------------------

def prefilter(arr: dict[str, np.ndarray], mjd: float, ra: float, dec: float) -> np.ndarray:
    """Indices of orbits within PREFILTER_DEG of (ra, dec) at ``mjd``, two-body,
    **sorted nearest first**.

    The sort is not cosmetic. The refine stage keeps only ``REFINE_KEEP`` of these, and
    the first version returned them in catalogue order -- so any tracklet with more
    survivors than the cap was refined against an arbitrary subset that did not contain
    the right object. It confirmed 1 of 10, and the one that worked was the only tracklet
    whose candidate count fell under the cap.
    """
    n = arr["epoch"].shape[0]
    e_pos, e_vel = earth_heliocentric_posvel(np.array([mjd]))
    dt = np.full(n, mjd + TT_MINUS_UTC_DAYS) - arr["epoch"]
    r, v, ok = propagate_kepler(arr["r0"].copy(), arr["v0"].copy(), dt)
    obs = observables_from_states(
        r, v, np.broadcast_to(e_pos, (n, 3)), np.broadcast_to(e_vel, (n, 3)),
        arr["h"], arr["g"],
    )
    sep = separation_deg(obs["ra_deg"], obs["dec_deg"],
                         np.full(n, ra), np.full(n, dec))
    hit = np.flatnonzero(ok & (sep < PREFILTER_DEG))
    return hit[np.argsort(sep[hit])]


def refine(arr: dict[str, np.ndarray], idx: np.ndarray, mjd: float,
           ra: float, dec: float) -> list[dict[str, Any]]:
    """Perturbed separations for the prefilter survivors, best first."""
    if idx.size == 0:
        return []
    idx = idx[:REFINE_KEEP]
    epochs = arr["epoch"][idx]
    epoch_common = float(epochs.max())
    r0, v0 = arr["r0"][idx].copy(), arr["v0"][idx].copy()
    if float(np.ptp(epochs)) > 1e-6:
        r0, v0, conv = propagate_kepler(r0, v0, epoch_common - epochs)
        if not np.all(conv):
            keep = conv
            idx, r0, v0 = idx[keep], r0[keep], v0[keep]
            if idx.size == 0:
                return []
    # integrate_dense requires the span to bracket the epoch. Every departed observation
    # here predates the MPCORB epoch, so only the backward leg is ever used -- but a span
    # that assumed that would silently extrapolate the day it stopped being true.
    #
    # SPAN_MARGIN_DAYS is not padding. predict_dense asks the trajectory for
    # ``t - tau``, and tau is the light time to the object: a 3-degree prefilter over a
    # 1.56M-orbit catalogue will sometimes admit something hundreds of AU out, where tau
    # is *days*. A 2 d margin died mid-run at 2,389 AU. 90 d covers ~15,600 AU, past any
    # MPCORB aphelion, and costs nothing against a multi-year span.
    t_target = mjd + TT_MINUS_UTC_DAYS
    traj = integrate_dense(r0, v0, epoch_common,
                           min(t_target, epoch_common) - SPAN_MARGIN_DAYS,
                           max(t_target, epoch_common) + SPAN_MARGIN_DAYS,
                           h_days=1.0, dense_every=8)
    # predict_dense works on PAIRS (orbit_idx[i], mjd_utc[i]): every orbit in the
    # trajectory, all at the one epoch.
    pairs = np.arange(idx.size, dtype=np.intp)
    pred = predict_dense(traj, pairs, np.full(idx.size, mjd),
                         h_mag=arr["h"][idx], g_slope=arr["g"][idx])
    sep = separation_deg(
        pred["ra_deg"].ravel(), pred["dec_deg"].ravel(),
        np.full(idx.size, ra), np.full(idx.size, dec),
    )
    order = np.argsort(sep)
    return [
        {"primary": str(arr["primary"][idx[k]]),
         "sep_arcsec": float(sep[k] * 3600.0),
         "v_pred": float(np.ravel(pred["v_pred"])[k]),
         "delta_au": float(np.ravel(pred["delta_au"])[k])}
        for k in order
    ]


# ----------------------------------------------------------------------------------
# Confirmation against the published record
# ----------------------------------------------------------------------------------

def get_obs80(desig: str, cache: Path) -> list[str]:
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not dest.exists():
        time.sleep(REQUEST_SPACING_S)
        resp = requests.get(OBS_URL, json={"desigs": [desig], "output_format": ["OBS80"]},
                            headers={"User-Agent": USER_AGENT}, timeout=120)
        if resp.status_code != 200:
            dest.write_text("", encoding="utf-8", newline="\n")
            return []
        doc = resp.json()
        block = (doc[0] if isinstance(doc, list) else doc).get("OBS80") or ""
        dest.write_text(block, encoding="utf-8", newline="\n")
    return [ln for ln in dest.read_text(encoding="utf-8").splitlines() if ln.strip()]


def confirm(obs: pl.DataFrame, desig: str, cache: Path) -> dict[str, Any]:
    """M9's rule: an observation went to this object if its record has a row at the same
    station within MATCH_SECONDS and MATCH_ARCSEC."""
    lines = get_obs80(desig, cache)
    pub = []
    for ln in lines:
        # A published block can hold roving-observer and satellite-parallax continuation
        # lines that are not optical astrometry; the parser rejects them and they are not
        # candidates for a match anyway.
        try:
            rec = parse_line(ln)
        except Mpc80ParseError:
            continue
        if rec is None or rec.mjd is None:
            continue
        pub.append((rec.obscode, rec.mjd, rec.ra_deg, rec.dec_deg))
    hits = 0
    tol_days = MATCH_SECONDS / 86400.0
    for row in obs.iter_rows(named=True):
        for oc, mjd, ra, dec in pub:
            if oc != row["obscode"] or abs(mjd - row["mjd"]) > tol_days:
                continue
            if float(separation_deg(np.array([ra]), np.array([dec]),
                                    np.array([row["ra_deg"]]),
                                    np.array([row["dec_deg"]]))[0]) * 3600.0 <= MATCH_ARCSEC:
                hits += 1
                break
    return {"published_rows": len(pub), "matched": hits, "of": obs.height}


# ----------------------------------------------------------------------------------

def write_doc(args, pick, desigs, results, *, partial: bool) -> dict[str, Any]:
    """Serialise what has been measured so far. Called every ten tracklets.

    The sample takes the better part of an hour, and the first full pass raised inside
    ``refine`` twenty minutes in and wrote nothing at all -- fifty completed tracklets,
    every one of them a paid-for MPC query, gone. ``partial`` marks a checkpoint so a
    half-finished file can never be read as a finished one.
    """
    n_ok = sum(r["confirmed"] for r in results)
    prov = args.mpcorb.with_suffix(".gz.provenance.json")
    doc = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "partial": partial,
        "rules": {
            "prefilter_deg": PREFILTER_DEG,
            "refine_keep": REFINE_KEEP,
            "confirm_depth": getattr(args, "confirm_depth", CONFIRM_DEPTH),
            "match_seconds": MATCH_SECONDS,
            "match_arcsec": MATCH_ARCSEC,
            "note": "UNCONFIRMED is an upper bound on 'not a linkage': a link into an "
                    "object absent from MPCORB cannot be seen by a catalogue search.",
        },
        "mpcorb": (json.loads(prov.read_text(encoding="utf-8"))
                   if prov.exists() else None),
        "sample_requested": len(pick),
        "sample_done": len(results),
        "population": len(desigs),
        "confirmed": n_ok,
        "confirmed_fraction": n_ok / len(results) if results else None,
        "refine_errors": sum(1 for r in results if r.get("refine_error")),
        "rows": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--departed", type=Path, required=True,
                    help="parquet of departed observations with astrometry")
    ap.add_argument("--mpcorb", type=Path, required=True)
    ap.add_argument("--orbit-table", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--confirm-depth", type=int, default=CONFIRM_DEPTH,
                    help="how far down the ranking to ask get-obs")
    ap.add_argument("--only", nargs="*", default=None,
                    help="run these designations instead of drawing a sample")
    args = ap.parse_args()

    df = pl.read_parquet(args.departed)
    desigs = df["desig"].unique().sort().to_list()
    if args.only:
        missing = [d for d in args.only if d not in set(desigs)]
        if missing:
            raise SystemExit(f"not in the departed table: {missing}")
        pick = list(args.only)
        print(f"re-running {len(pick)} named designations at confirm depth "
              f"{args.confirm_depth}", flush=True)
    else:
        rng = np.random.default_rng(args.seed)
        pick = [desigs[i] for i in rng.choice(len(desigs),
                                              size=min(args.sample, len(desigs)),
                                              replace=False)]
        print(f"{len(desigs):,} departed designations available; sampling {len(pick)}",
              flush=True)

    orbits = build_orbit_table(args.mpcorb, args.orbit_table)
    arr = orbit_arrays(orbits)
    print(f"catalogue: {arr['epoch'].shape[0]:,} orbits", flush=True)

    results: list[dict[str, Any]] = []
    t0 = time.monotonic()
    for i, d in enumerate(pick, 1):
        obs = df.filter(pl.col("desig") == d).sort("mjd")
        mid = obs.row(obs.height // 2, named=True)
        idx = prefilter(arr, mid["mjd"], mid["ra_deg"], mid["dec_deg"])
        # One tracklet must never cost the run. The first full pass lost 50 completed
        # tracklets to a single ValueError raised 20 minutes in; an UNATTRIBUTABLE row is
        # a result, an aborted sample is not.
        failure: str | None = None
        try:
            cands = refine(arr, idx, mid["mjd"], mid["ra_deg"], mid["dec_deg"])
        except (ValueError, RuntimeError) as exc:
            cands, failure = [], f"{type(exc).__name__}: {exc}"
            print(f"  ! {d}: refine failed -- {failure}", flush=True)
        rec: dict[str, Any] = {
            "desig": d,
            "n_obs": obs.height,
            "obscode": mid["obscode"],
            "mjd": mid["mjd"],
            "prefilter_candidates": int(idx.size),
            "refine_error": failure,
            "best": cands[0] if cands else None,
        }
        # Confirm the best few, not just the best: the perturbed separation ranking is
        # good but not perfect at these lookbacks, and the published record is the judge.
        # The pilot confirmed one tracklet whose best separation was 141.7 arcsec, so a
        # ranking-only answer would have thrown away a real linkage. The loop breaks on
        # the first hit, so the extra queries are paid only by tracklets that fail.
        rec["confirmation"] = None
        for cand in cands[:args.confirm_depth]:
            c = confirm(obs, cand["primary"], args.cache)
            if c["matched"] > 0:
                rec["confirmation"] = {"object": cand["primary"],
                                       "sep_arcsec": cand["sep_arcsec"], **c}
                break
        rec["confirmed"] = rec["confirmation"] is not None
        results.append(rec)
        if i % 10 == 0 or i == len(pick):
            n_ok = sum(r["confirmed"] for r in results)
            print(f"  {i}/{len(pick)}  confirmed {n_ok}  "
                  f"({time.monotonic() - t0:.0f} s)", flush=True)
            # Checkpoint. The sample takes the better part of an hour and the run that
            # crashed at 50 of 150 had written nothing at all.
            write_doc(args, pick, desigs, results, partial=True)

    doc = write_doc(args, pick, desigs, results, partial=False)
    n_ok = doc["confirmed"]
    print(f"confirmed {n_ok}/{len(results)} = "
          f"{100 * n_ok / len(results):.1f}%", flush=True)
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
