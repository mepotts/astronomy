"""M10: the pointed-field screen — the confound M9 found on its way out of the TNO niche.

M9 section 8 fitted three distant scoping candidates and lost all three. Two of them
failed for a reason no previous sweep had met: the object's **own published record**
contained same-station observations at the *same exposure instants* as the ITF
tracklet, ~30" away. The survey was **following the known object**; the real detections
are the published rows, and the ITF tracklet is other material in the pointed field.

That is a confound the decoy control structurally cannot price. The decoy is a
half-period phase shift of each orbit, so its sky position coincides with nobody's
pointed fields; it measures chance alignment against the survey footprint, which is a
different and easier question. A candidate whose object was being *tracked* has
position-correlated debris around it by construction.

The screen, per M10-RESULTS section 0.4 (**written before this file existed**):

* ``POINTED_FIELD`` — the attributed object's published record holds an observation
  from the **same station** within **+/- 1 hour** of any of the tracklet's own
  observation instants. One hour is comfortably inside a night and far outside any
  plausible clock error, and M9's two failures sat at *zero* seconds.
* ``SAME_NIGHT_FIELD`` — the weaker version at +/- 1 day: the station observed the
  object that night, but not in the same exposure.
* ``DUPLICATE`` — the published row *is* the tracklet observation (within the ledger's
  2 s / 2" duplicate rule). That is ``ALREADY_LINKED``, not a pointed field, and is
  reported separately so the two are never confused.

Modes:

``--validate``  run the screen against M9's three failed candidates and check it
                against the target declared in advance: flag CT190 and VV130, do not
                flag EZ90. Anything else means the screen is wrong, and that is what
                gets printed.
``--sweep``     the all-sky distant sweep M9 section 12 item 2 recommended (its own
                scoping run was restricted to the slow-northern pool), with the screen
                applied to the ranked queue *before* anything is fitted.

Writes ``data/raw/rubin/m10-pointed.json``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import polars as pl

from itf_linker import config
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import link_key, tracklet_line_index
from itf_linker.mpc80 import parse_line

TNO_FITS = ROOT / "m9-tno-fits.json"
OBS80 = ROOT / "data" / "raw" / "rubin" / "obs80"
OBS80_FRESH = ROOT / "data" / "raw" / "rubin" / "obs80-m10fresh"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
OUT = ROOT / "data" / "raw" / "rubin" / "m10-pointed.json"

POINTED_HOURS = 1.0
SAME_NIGHT_DAYS = 1.0
DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0


def sep_arcsec(a: Any, b: Any) -> float:
    dra = abs((a.ra_deg - b.ra_deg + 180.0) % 360.0 - 180.0) * 3600.0
    dde = abs(a.dec_deg - b.dec_deg) * 3600.0
    return math.hypot(dra * math.cos(math.radians(b.dec_deg)), dde)


def pointed_field_flags(trk_obs: list[Any], pub_obs: list[Any]) -> dict[str, Any]:
    """The screen. Pure geometry and clocks; no reference to which side 'looks right'."""
    same_instant: list[dict[str, Any]] = []
    same_night: list[dict[str, Any]] = []
    duplicates = 0
    for t in trk_obs:
        for p in pub_obs:
            if p.obscode != t.obscode:
                continue
            dsec = abs(p.mjd - t.mjd) * 86400.0
            if dsec > SAME_NIGHT_DAYS * 86400.0:
                continue
            s = sep_arcsec(p, t)
            if dsec <= DUP_EPOCH_S and s <= DUP_POS_ARCSEC:
                duplicates += 1
                continue
            rec = {"obscode": t.obscode, "trk_mjd": round(t.mjd, 6),
                   "pub_mjd": round(p.mjd, 6), "dt_seconds": round(dsec, 2),
                   "sep_arcsec": round(s, 1)}
            (same_instant if dsec <= POINTED_HOURS * 3600.0 else same_night).append(rec)
    flags = []
    if same_instant:
        flags.append("POINTED_FIELD")
    elif same_night:
        flags.append("SAME_NIGHT_FIELD")
    if duplicates:
        flags.append("DUPLICATE")
    return {
        "flags": flags,
        "screened_out": "POINTED_FIELD" in flags,
        "n_same_instant": len(same_instant),
        "n_same_night": len(same_night),
        "n_duplicate": duplicates,
        "min_dt_seconds": min((r["dt_seconds"] for r in same_instant + same_night),
                              default=None),
        "evidence": sorted(same_instant + same_night,
                           key=lambda r: r["dt_seconds"])[:4],
    }


#: The MPC's base-62 alphabet for packed cycle counts (digits, UPPER, lower).
#: Shared with :mod:`itf_linker.verify.killcheck`, which verified it against MPEC 2026-O57.
_BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def packed_provisional(desig: str) -> str | None:
    """MPC packed form of a provisional designation: 2018 KH3 -> K18K03H."""
    m = re.match(r"^(\d{4}) ([A-Z])([A-Z])(\d*)$", desig.strip())
    if not m:
        return None
    yr, half, order, num = m.groups()
    n = int(num or 0)
    century = {"18": "I", "19": "J", "20": "K"}.get(yr[:2])
    if century is None:
        return None
    # Columns 5-6 carry the cycle count in the MPC's base-62 alphabet: digits, then
    # UPPERCASE, then lowercase. The arithmetic version of this was wrong past cycle 359
    # because `chr(ord("A") + 26)` walks off the end of the alphabet into ASCII
    # punctuation -- `[ \ ] ^ _ ` ` -- and then into lowercase shifted by six. Two
    # different failures came out of that: 360-419 produced a malformed designation, and
    # >=420 produced a **well-formed designation for a different object** (2015 KP488
    # packed as K15Kg8P, which reads back as 2015 KP428). 59 of the 663 objects in the
    # M11 review queue were affected. Use the same table `verify.killcheck` uses -- it is
    # the one checked against a real MPEC -- so there is one encoding in this repository
    # rather than two.
    if n < 100:
        cycle = f"{n:02d}"
    elif n < 620:
        cycle = _BASE62[n // 10] + str(n % 10)
    else:
        # Beyond 619 the original scheme is exhausted; the extended `_PD0000` form
        # applies and this function does not implement it, so refuse rather than guess.
        return None
    return f"{century}{yr[2:]}{half}{cycle}{order}"


def self_designation(orbit_desig: str, trksub: str) -> dict[str, Any]:
    """Is this "candidate" just the object's own packed designation wearing a hat?

    The all-sky distant sweep's head is full of trkSubs like ``/18K03H`` sitting
    0.5-2.6" from **2018 KH3**, whose packed designation is ``K18K03H``: the same seven
    characters with the century byte replaced. These are the object's own observations
    parked in the ITF under a placeholder designation, and they would sail through every
    gate in this repository -- tiny separation (it *is* the object), a clean joint fit,
    and a SkyBoT cone search that finds the object itself and records it as
    *confirmation*. Nothing here is wrong; it is simply not an attribution, and counting
    it as one would inflate any distant-sweep yield with bookkeeping.

    Measured 2026-08-18: **0 of the 1,971 M8/M9/M10-shell ledger rows** match this
    pattern, so the main-belt ledger and ``out/review-queue.csv`` are clean of it. It is
    a distant-sweep phenomenon.
    """
    pk = packed_provisional(orbit_desig)
    if pk and len(trksub) == 7 and trksub[1:] == pk[1:]:
        return {"self_designation": True, "packed": pk, "trksub": trksub,
                "differs_only_in": "leading century byte"}
    return {"self_designation": False}


def published(desig: str) -> list[Any]:
    for root in (OBS80, OBS80_FRESH):
        path = root / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
        if path.exists():
            return [
                o for o in (parse_line(ln, strict=False)
                            for ln in path.read_text(encoding="utf-8").splitlines()
                            if ln.strip()) if o
            ]
    return []


def tracklet_obs(index: dict, key: tuple[str, str, int]) -> list[Any]:
    return [o for o in (parse_line(ln, strict=False) for ln in index.get(key) or []) if o]


def validate(index: dict) -> dict[str, Any]:
    """Against the target declared in M10-RESULTS section 0.4, before the screen existed."""
    target = {
        ("2008 CT190", "LA1140"): True,
        ("2004 VV130", "DT20B11"): True,
        ("2011 EZ90", "s25473"): False,
    }
    doc = json.loads(TNO_FITS.read_text(encoding="utf-8"))
    rows = []
    for r in doc["results"]:
        key = (r["trksub"], r["obscode"], int(r["night"]))
        trk = tracklet_obs(index, key)
        res = pointed_field_flags(trk, published(r["orbit_desig"]))
        want = target.get((r["orbit_desig"], r["trksub"]))
        rows.append({
            "orbit_desig": r["orbit_desig"], "trksub": r["trksub"],
            "obscode": r["obscode"], "night": r["night"],
            "trk_obs_parsed": len(trk),
            "expected_screened_out": want,
            "screened_out": res["screened_out"],
            "agrees_with_preregistered_target": res["screened_out"] == want,
            **{k: v for k, v in res.items() if k != "screened_out"},
        })
        print(f"  {r['orbit_desig']:12s} + {r['trksub']:8s}: "
              f"flags={res['flags'] or ['none']} "
              f"min_dt={res['min_dt_seconds']}s "
              f"expected_screened={want} got={res['screened_out']} "
              f"{'OK' if res['screened_out'] == want else 'MISMATCH'}", flush=True)
    passed = sum(1 for r in rows if r["agrees_with_preregistered_target"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "verdict": "screen validated 3/3" if passed == len(rows)
                       else f"SCREEN FAILED VALIDATION ({passed}/{len(rows)})"}


def screen_ledger() -> dict[str, Any]:
    """Apply the screen retroactively to every still-live PASS row Matthew will review.

    M9 section 8 called the pointed-field confound "a measured confound the main-belt
    sweeps never had". That was an inference from how the two regimes differ, not a
    measurement of the main-belt ledger — and the ledger is what is about to be
    submitted. This measures it. Any row that flags here is one a reviewer must see
    before it goes anywhere.
    """
    refresh = json.loads(
        (ROOT / "data" / "raw" / "rubin" / "m10-refresh.json").read_text(encoding="utf-8")
    )
    live = {
        (r["trksub"], r["obscode"], int(r["night"]))
        for r in refresh["rows"]
        if r["itf_status"] == "STILL_LIVE" and r["verdict"] in ("PASS", "BORDERLINE")
    }
    rows: list[dict[str, Any]] = []
    for path in (ROOT / "m8-ledger.json", ROOT / "m9-ledger.json"):
        for v in json.loads(path.read_text(encoding="utf-8"))["verdicts"]:
            key = (v["trksub"], v["obscode"], int(v["night"]))
            if key in live:
                rows.append(v)
    print(f"screening {len(rows)} live PASS/BORDERLINE ledger rows", flush=True)

    lon = fetch_obscodes()
    idx, _ = tracklet_line_index({r["trksub"] for r in rows}, lon)
    flagged: list[dict[str, Any]] = []
    counts = {"POINTED_FIELD": 0, "SAME_NIGHT_FIELD": 0, "DUPLICATE": 0, "clean": 0,
              "no_tracklet_lines": 0, "no_published_record": 0}
    for v in rows:
        trk = tracklet_obs(idx, (v["trksub"], v["obscode"], int(v["night"])))
        pub = published(v["orbit_desig"])
        if not trk:
            counts["no_tracklet_lines"] += 1
            continue
        if not pub:
            counts["no_published_record"] += 1
            continue
        res = pointed_field_flags(trk, pub)
        if not res["flags"]:
            counts["clean"] += 1
            continue
        for f in res["flags"]:
            counts[f] = counts.get(f, 0) + 1
        flagged.append({
            "orbit_desig": v["orbit_desig"], "trksub": v["trksub"],
            "obscode": v["obscode"], "night": v["night"],
            "link_key": v.get("link_key"), "verdict": v["verdict"],
            "dt_years": v.get("dt_years"), "rms_joint": v.get("rms_joint"),
            **res,
        })
        print(f"  {res['flags']} {v['orbit_desig']:12s} + {v['trksub']:8s} "
              f"{v['obscode']} min_dt={res['min_dt_seconds']}s", flush=True)
    return {"n_screened": len(rows), "counts": counts, "flagged": flagged}


def allsky_sweep() -> dict[str, Any]:
    """M9 section 12 item 2: the all-sky distant sweep, screen applied before ranking."""
    import m7_attribution as m7run
    import m8_attribution as m8run
    import m9_tno as tno

    config.ITF_PARQUET = RECONSTRUCTED
    arrays, ostats = tno.distant_orbits()
    print(f"distant orbits: {ostats}", flush=True)

    mjd_min = float(arrays["epoch"].min() - tno.MAX_LOOKBACK_DAYS)
    mjd_max = float(arrays["epoch"].max() + 1.0)
    # All-sky: M9's scoping run kept only Dec > +30 and rate < 10"/hr (the M7 pool).
    # The only cut kept here is a measurable rate, which the gate's rate test needs.
    trk = m7run.load_tracklets(mjd_min, mjd_max).filter(pl.col("span_days") > 0)
    print(f"all-sky tracklets in window: {trk.height}", flush=True)

    lon = fetch_obscodes()
    nightindex = m8run.NightIndex(trk, lon)
    env = tno.tno_envelope()
    m8run.MAX_LOOKBACK_DAYS = tno.MAX_LOOKBACK_DAYS
    m8run.MIN_LOOKBACK_DAYS = 0.0

    print("real sweep:", flush=True)
    real, t_real = m8run.run_sweep(arrays, nightindex, env, decoy=False, label="allsky")
    print("control sweep:", flush=True)
    fake, t_fake = m8run.run_sweep(arrays, nightindex, env, decoy=True, label="control")

    keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid", "mag_mean").rows()
    a_by = dict(zip(arrays["primary"].tolist(), arrays["a_au"].tolist()))
    for m in real:
        desig, obscode, night, n_obs, mjd_mid, _mag = keys[m["row"]]
        m.update({"trksub": desig, "obscode": obscode, "night": int(night),
                  "trk_n_obs": int(n_obs), "trk_mjd_mid": float(mjd_mid),
                  "link_key": link_key([(desig, obscode, int(night))]),
                  "orbit_a_au": round(a_by.get(m["orbit_desig"], float("nan")), 2)})
        del m["row"]
    for m in fake:
        m.pop("row", None)
    real.sort(key=lambda m: (m["encounter"], m["sep_arcsec"] / m["gate_radius_arcsec"]))

    # ---- the screen, applied to the ranked queue BEFORE anything is fitted ----------
    head = real[:200]
    idx, _ = tracklet_line_index({m["trksub"] for m in head}, lon,
                                 src=None)
    screened = n_self = 0
    for m in head:
        res = pointed_field_flags(
            tracklet_obs(idx, (m["trksub"], m["obscode"], m["night"])),
            published(m["orbit_desig"]),
        )
        m["pointed_screen"] = res
        m["self_designation"] = self_designation(m["orbit_desig"], m["trksub"])
        screened += int(res["screened_out"])
        n_self += int(m["self_designation"]["self_designation"])

    survivors = [
        m for m in head
        if not m["pointed_screen"]["screened_out"]
        and not m["self_designation"]["self_designation"]
    ]
    return {
        "orbits": ostats,
        "tracklets": trk.height,
        "nights": len(nightindex.night_mjd),
        "sweep_timing": {"real": t_real, "control": t_fake},
        "coarse": {"real": m8run.summarise(real), "control": m8run.summarise(fake)},
        "n_real": len(real),
        "screened_head": len(head),
        "screened_out": screened,
        "self_designation_matches": n_self,
        "survivors": len(survivors),
        "survivors_sub60": sum(1 for m in survivors if m["sep_arcsec"] < 60.0),
        "control_sub60": sum(1 for m in fake if m["sep_arcsec"] < 60.0),
        "top": [
            {k: m[k] for k in ("orbit_desig", "orbit_a_au", "trksub", "obscode",
                               "night", "sep_arcsec", "gate_radius_arcsec", "dt_days",
                               "link_key", "pointed_screen", "self_designation")}
            for m in head[:25]
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--ledger", action="store_true",
                    help="apply the screen retroactively to every still-live PASS row")
    args = ap.parse_args()

    out: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "screen": {
            "pointed_hours": POINTED_HOURS,
            "same_night_days": SAME_NIGHT_DAYS,
            "dup_epoch_s": DUP_EPOCH_S,
            "dup_pos_arcsec": DUP_POS_ARCSEC,
            "preregistered": "M10-RESULTS.md section 0.4",
        },
    }
    if OUT.exists():
        out = {**json.loads(OUT.read_text(encoding="utf-8")), **out}

    if args.validate:
        config.ITF_PARQUET = RECONSTRUCTED
        doc = json.loads(TNO_FITS.read_text(encoding="utf-8"))
        lon = fetch_obscodes()
        idx, _ = tracklet_line_index({r["trksub"] for r in doc["results"]}, lon)
        print("validating the screen against M9's three failed candidates:", flush=True)
        out["validation"] = validate(idx)
        print(out["validation"]["verdict"], flush=True)
    if args.ledger:
        config.ITF_PARQUET = RECONSTRUCTED
        out["ledger_screen"] = screen_ledger()
        print(json.dumps(out["ledger_screen"]["counts"], indent=1), flush=True)
    if args.sweep:
        if (out.get("validation") or {}).get("passed") != 3:
            print("screen has not passed its pre-registered validation; "
                  "not running the sweep", flush=True)
        else:
            out["allsky_sweep"] = allsky_sweep()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
