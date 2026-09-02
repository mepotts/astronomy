"""M8: verdict chain v2 -- fits to gated candidate ledger, SkyBoT folded in. Pure post-run.

Extends ``scripts/m7_verdicts.py`` in three ways:

* **SkyBoT is part of the chain, not a manual step.** M7 ran the PD152 cone search by
  hand; here every candidate that survives the fit gates gets an automated SkyBoT cone
  search at its tracklet's own epoch and position (the M2 vetting layer's client,
  cache and politeness). A *different* known object close enough to claim the
  detections is a named failure (``SKYBOT_CONFLICT``), the candidate object itself
  showing up under its own designation is confirmation, and "SkyBoT unavailable" is
  recorded as exactly that -- never silently treated as "no conflict".
* **The primary gate is explicit.** "Did fo actually use the tracklet" (the subset-guard
  question) is checked first and named first: convergence and the published rule are
  nearly vacuous for attribution joint fits (M7 measured 149/150 passing both).
* **The ledger carries every verdict with provenance**, plus M7's HELD candidates
  carried forward verbatim -- their verdicts are Matthew's to decide and are not
  re-litigated here (M8 task law).

Verdicts: ``ALREADY_LINKED`` (positive control), ``PASS``, ``BORDERLINE`` (strict gate
missed within BORDERLINE_RMS_ARCSEC while the published rule passes and the tracklet is
fully used -- the human's call, M7's MQ241 precedent), ``SKYBOT_CONFLICT``, ``FAIL``.
Encounter-flagged orbits keep their verdict but carry ``encounter: true`` -- their
coarse-gate provenance inherits no accuracy claim from the calibration.

Reads ``m8-attribution.json``; writes ``m8-ledger.json`` (candidate ledger v2).
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index
from itf_linker.mpc80 import parse_line
from itf_linker.vet.cache import CachedSession
from itf_linker.vet.skybot import cone_search

REPORT = ROOT / "m8-attribution.json"
OBS80_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80"
VET_CACHE = ROOT / "data" / "vet-cache"
OUT = ROOT / "m8-ledger.json"

DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0
MIN_USED_FRACTION = 0.90
#: Strict-gate RMS overshoot that earns BORDERLINE instead of FAIL (M7's MQ241 was
#: 0.0007" over; anything past 0.005" is a plain failure, not a judgement call).
BORDERLINE_RMS_ARCSEC = 0.005
#: SkyBoT cone: search radius, and the separation at which a *different* known object
#: is close enough to claim a detection (its ephemeris error is added on top).
SKYBOT_RADIUS_DEG = 0.1
SKYBOT_CLAIM_ARCSEC = 15.0
#: A claimant is *competitive* only while its own ephemeris is informative. This is
#: the PD152 standard made explicit: M7 cleared that candidate because the only
#: neighbour had a 0.22"-accurate ephemeris AND sat 105" away -- accuracy was part of
#: the argument. An object SkyBoT places with a 20,000" (or 3.9-million-arcsec)
#: uncertainty is *lost*; it blankets the sky and can "claim" every ecliptic tracklet
#: while predicting none of them, and the joint fit at ~0.08" RMS has already
#: discriminated against a prior that flat. Such neighbours do not fail the candidate
#: -- they are recorded on it as a named ambiguity for the human (and for the M9
#: adjudication step: fit the tracklet against the claimant's astrometry too).
SKYBOT_CLAIMANT_MAX_ERR_ARCSEC = 60.0

#: M7's three HELD candidates, verbatim from M7-RESULTS.md section 8. Carried forward,
#: never recomputed: their disposition is Matthew's pending decision.
M7_HELD = [
    {
        "provenance": "M7", "status": "HELD (Matthew's decision pending)",
        "verdict": "PASS", "orbit_desig": "2025 PD152", "trksub": "P11zG98",
        "obscode": "F51", "night": 59854, "link_key": "lk6230bd2f8b02f30d",
        "dt_days": -3.14 * 365.25, "sep_arcsec": 197.0, "rms_joint": 0.086,
        "trk_obs_total": 4, "note": "combined 33/33-used fit at 0.0905 with sibling",
    },
    {
        "provenance": "M7", "status": "HELD (Matthew's decision pending)",
        "verdict": "PASS", "orbit_desig": "2025 PD152", "trksub": "P11zFtH",
        "obscode": "F51", "night": 59854, "link_key": "lk6fa8132ffbde598b",
        "dt_days": -3.14 * 365.25, "sep_arcsec": 203.0, "rms_joint": 0.091,
        "trk_obs_total": 3, "note": "combined 33/33-used fit at 0.0905 with sibling",
    },
    {
        "provenance": "M7", "status": "HELD (Matthew's decision pending)",
        "verdict": "BORDERLINE", "orbit_desig": "2025 MQ241", "trksub": "nf2088",
        "obscode": "W76", "night": 60880, "link_key": "lkd3386eec6d56df1d",
        "dt_days": -0.33 * 365.25, "sep_arcsec": 3.5, "rms_joint": 0.2507,
        "trk_obs_total": 3, "note": "0.0007 arcsec over the frozen strict ceiling",
    },
]


def published_obs(desig: str) -> list[Any]:
    path = OBS80_CACHE / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            o = parse_line(ln, strict=False)
            if o is not None:
                out.append(o)
    return out


def count_duplicates(trk_lines: list[str], pub: list[Any]) -> int:
    n = 0
    for ln in trk_lines:
        o = parse_line(ln, strict=False)
        if o is None:
            continue
        for p in pub:
            if p.obscode != o.obscode:
                continue
            if abs(p.mjd - o.mjd) * 86400.0 > DUP_EPOCH_S:
                continue
            dra = abs((p.ra_deg - o.ra_deg + 180.0) % 360.0 - 180.0) * 3600.0
            ddec = abs(p.dec_deg - o.dec_deg) * 3600.0
            cosd = math.cos(math.radians(o.dec_deg))
            if (dra * cosd) ** 2 + ddec**2 <= DUP_POS_ARCSEC**2:
                n += 1
                break
    return n


def _norm_name(name: str) -> str:
    return "".join(str(name).split()).upper()


def skybot_check(
    session: CachedSession,
    trk_lines: list[str],
    orbit_desig: str,
    all_desigs: list[str],
) -> dict[str, Any]:
    """Cone-search the tracklet's first epoch/position; classify what comes back."""
    obs = [o for o in (parse_line(ln, strict=False) for ln in trk_lines) if o]
    if not obs:
        return {"status": "no_parseable_obs"}
    o = obs[0]
    matches, err = cone_search(
        session,
        ra_deg=o.ra_deg,
        dec_deg=o.dec_deg,
        jd_utc=o.mjd + 2400000.5,
        obscode=o.obscode,
        radius_deg=SKYBOT_RADIUS_DEG,
        mjd_utc=o.mjd,
    )
    if err:
        return {"status": "unavailable", "error": err}
    own = {_norm_name(d) for d in [orbit_desig, *all_desigs]}
    self_rows = []
    conflicts = []
    lost_ambiguous = []
    others = []
    for m in matches:
        row = {
            "name": m.raw_name,
            "sep_arcsec": m.sep_arcsec,
            "ephem_err_arcsec": m.ephem_err_arcsec,
            "v_mag": m.v_mag,
        }
        err = m.ephem_err_arcsec or 0.0
        positionally_consistent = (
            m.sep_arcsec is not None and m.sep_arcsec <= SKYBOT_CLAIM_ARCSEC + err
        )
        if _norm_name(m.raw_name) in own:
            self_rows.append(row)
        elif positionally_consistent and err <= SKYBOT_CLAIMANT_MAX_ERR_ARCSEC:
            conflicts.append(row)
        elif positionally_consistent:
            lost_ambiguous.append(row)  # cannot be excluded; cannot claim either
        else:
            others.append(row)
    return {
        "status": "ok",
        "n_matches": len(matches),
        "self": self_rows,
        "conflicts": conflicts,
        "lost_object_ambiguity": lost_ambiguous,
        "nearest_other": min(
            (r for r in others), key=lambda r: r["sep_arcsec"] or 1e9, default=None
        ),
    }


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    fits = report.get("fits") or []
    if not fits:
        print("no fits in report; run scripts/m8_attribution.py first")
        return

    lon = fetch_obscodes()
    wanted = {f["trksub"] for f in fits}
    index, _ = tracklet_line_index(wanted, lon)
    session = CachedSession(VET_CACHE)

    orbit_desigs: dict[str, list[str]] = {}
    orbits_parquet = ROOT / "data" / "raw" / "rubin" / "m8-orbits.parquet"
    if orbits_parquet.exists():
        import polars as pl

        odf = pl.read_parquet(orbits_parquet, columns=["primary", "all_desigs"])
        orbit_desigs = dict(zip(odf["primary"].to_list(), odf["all_desigs"].to_list()))

    verdicts = []
    n_skybot = 0
    for f in fits:
        fit = f.get("fit") or {}
        key = (f["trksub"], f["obscode"], f["night"])
        trk_lines = index.get(key) or []
        pub = published_obs(f["orbit_desig"])
        dup = count_duplicates(trk_lines, pub) if trk_lines else 0
        n_trk = fit.get("trk_obs_total") or len(
            [ln for ln in trk_lines if parse_line(ln, strict=False)]
        )

        reasons: list[str] = []
        skybot: dict[str, Any] | None = None
        if dup and n_trk and dup >= n_trk:
            verdict = "ALREADY_LINKED"
        else:
            if dup:
                reasons.append(f"partial_duplicate({dup}/{n_trk})")
            # The primary gate first: a converged fit that excluded the new data
            # attributes nothing (the subset-guard lesson, M1 -> M7).
            fully_used = fit.get("trk_obs_used", 0) == fit.get("trk_obs_total", -1)
            if not fully_used:
                reasons.append(
                    f"tracklet_not_fully_used({fit.get('trk_obs_used')}/"
                    f"{fit.get('trk_obs_total')})"
                )
            if not fit.get("converged"):
                reasons.append(f"not_converged({fit.get('status')})")
            gate = fit.get("gate_strict") or {}
            strict_ok = bool(gate.get("passes"))
            if not strict_ok:
                reasons.append("strict_gate:" + "; ".join(gate.get("reasons") or ["?"]))
            n_obs, n_used = fit.get("n_obs") or 0, fit.get("n_used") or 0
            if not n_obs or n_used / n_obs < MIN_USED_FRACTION:
                reasons.append(f"joint_set_not_used({n_used}/{n_obs})")

            published_ok = bool((fit.get("gate_mpc_published") or {}).get("passes"))
            rms = fit.get("rms_joint")
            only_strict_failed = (
                reasons
                and all(r.startswith("strict_gate:") for r in reasons)
                and published_ok
                and rms is not None
                and rms <= 0.25 + BORDERLINE_RMS_ARCSEC
            )
            if not reasons:
                verdict = "PASS"
            elif only_strict_failed:
                verdict = "BORDERLINE"
            else:
                verdict = "FAIL"

            # SkyBoT enters the chain for anything still standing.
            if verdict in ("PASS", "BORDERLINE") and trk_lines:
                skybot = skybot_check(
                    session, trk_lines, f["orbit_desig"],
                    orbit_desigs.get(f["orbit_desig"], []),
                )
                n_skybot += 1
                if skybot.get("conflicts"):
                    verdict = "SKYBOT_CONFLICT"
                    reasons.append(
                        "skybot_conflict:"
                        + "; ".join(
                            f"{c['name']} at {c['sep_arcsec']}\"" for c in skybot["conflicts"]
                        )
                    )
                elif skybot.get("status") != "ok":
                    reasons.append(f"skybot_{skybot.get('status')}")
                if skybot.get("lost_object_ambiguity"):
                    # Named caveat, not a fail: a lost object (ephemeris error above
                    # SKYBOT_CLAIMANT_MAX_ERR_ARCSEC) overlaps the position but
                    # predicts nothing. M9 adjudicates by fitting the tracklet
                    # against the claimant's own astrometry.
                    reasons.append(
                        "skybot_lost_object_ambiguity:"
                        + "; ".join(
                            f"{c['name']} (err {c['ephem_err_arcsec']}\")"
                            for c in skybot["lost_object_ambiguity"][:3]
                        )
                    )

        verdicts.append(
            {
                "provenance": "M8",
                "orbit_desig": f["orbit_desig"],
                "trksub": f["trksub"],
                "obscode": f["obscode"],
                "night": f["night"],
                "link_key": f.get("link_key"),
                "sep_arcsec": round(f["sep_arcsec"], 1),
                "gate_radius_arcsec": round(f.get("gate_radius_arcsec", 0.0), 1),
                "dt_days": round(f["dt_days"], 1),
                "dt_years": round(f["dt_days"] / 365.25, 2),
                "encounter": bool(f.get("encounter")),
                "rms_joint": fit.get("rms_joint"),
                "rms_baseline": (fit.get("baseline") or {}).get("rms"),
                "trk_obs_used": fit.get("trk_obs_used"),
                "trk_obs_total": n_trk,
                "duplicates_in_published": dup,
                "verdict": verdict,
                "reasons": reasons,
                "mpc_published_gate_passes": (fit.get("gate_mpc_published") or {}).get("passes"),
                "skybot": skybot,
                "fit_tag": f.get("fit_tag"),
            }
        )

    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1

    ledger = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generated_from": REPORT.name,
        "rules": {
            "dup_epoch_s": DUP_EPOCH_S,
            "dup_pos_arcsec": DUP_POS_ARCSEC,
            "min_used_fraction": MIN_USED_FRACTION,
            "borderline_rms_arcsec": BORDERLINE_RMS_ARCSEC,
            "skybot_radius_deg": SKYBOT_RADIUS_DEG,
            "skybot_claim_arcsec": SKYBOT_CLAIM_ARCSEC,
            "skybot_claimant_max_err_arcsec": SKYBOT_CLAIMANT_MAX_ERR_ARCSEC,
        },
        "counts_m8": counts,
        "pass_with_lost_object_ambiguity": sum(
            1 for v in verdicts
            if v["verdict"] == "PASS"
            and any(r.startswith("skybot_lost_object_ambiguity") for r in v["reasons"])
        ),
        "skybot_calls": n_skybot,
        "skybot_session": session.summary() if hasattr(session, "summary") else None,
        "held_from_m7": M7_HELD,
        "verdicts": verdicts,
    }
    OUT.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    print(f"M8 verdicts: {counts}; SkyBoT calls: {n_skybot}")
    for v in verdicts:
        if v["verdict"] not in ("FAIL",):
            print(
                f"{v['verdict']:15s} {v['orbit_desig']:12s} + {v['trksub']:8s}"
                f" {v['obscode']} n{v['night']}  dt {v['dt_years']:+6.2f}y"
                f"  sep {v['sep_arcsec']:7.1f}\"  rms {v['rms_joint']}"
                f"  used {v['trk_obs_used']}/{v['trk_obs_total']}"
                f"{'  ENCOUNTER' if v['encounter'] else ''}  {v['link_key']}"
            )
    print(f"held from M7 (not re-litigated): {len(M7_HELD)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
