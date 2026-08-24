"""M7: turn raw joint-fit outcomes into per-candidate verdicts. Pure post-processing.

Reads ``m7-attribution.json`` (the sweep + fit report), the cached OBS80 records, and
the ITF tracklet lines, and classifies every fitted candidate:

``ALREADY_LINKED``
    The tracklet's observations are already present in the object's *published* MPC
    record (same obscode, epoch within 2 s, position within 2"). The MPC's own
    designation-time ITF sweep (Feb 2026 newsletter) made this association and the
    ITF copy is stale. Not a new attribution -- but each one is a **positive
    control**: the pipeline independently re-derived a linkage the MPC accepted,
    which is the only external ground truth this capability can have. (These joint
    fits also double-weight the duplicated epochs, so their statistics are quoted
    for identification only, never as fit quality.)

``PASS``
    A candidate attribution: joint fit converged, the strict M1-M5 RMS gate passes,
    every tracklet observation was *used* by the fit (a converged fit that excluded
    the new data attributes nothing -- the subset-guard lesson), at least 90% of the
    joint observation set was used overall (a fit that discarded the object's own
    astrometry to accommodate the tracklet is a different object's orbit), and the
    tracklet is NOT already in the published record.

``FAIL(<reasons>)``
    Everything else, with the failing conditions named.

Writes ``m7-verdicts.json`` and prints the verdict table.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index
from itf_linker.mpc80 import parse_line

REPORT = ROOT / "m7-attribution.json"
OBS80_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80"
OUT = ROOT / "m7-verdicts.json"

#: "Same observation" tolerances for the already-published check.
DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0
#: Minimum fraction of the joint set the fit must use.
MIN_USED_FRACTION = 0.90


def published_obs(desig: str) -> list[Any]:
    path = OBS80_CACHE / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        o = parse_line(ln, strict=False)
        if o is not None:
            out.append(o)
    return out


def count_duplicates(trk_lines: list[str], pub: list[Any]) -> int:
    """Tracklet observations already present in the published record."""
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
            import math

            cosd = math.cos(math.radians(o.dec_deg))
            if (dra * cosd) ** 2 + ddec**2 <= DUP_POS_ARCSEC**2:
                n += 1
                break
    return n


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    fits = report.get("fits") or []
    if not fits:
        print("no fits in report; run scripts/m7_attribution.py first")
        return

    lon = fetch_obscodes()
    wanted = {f["trksub"] for f in fits}
    index, _ = tracklet_line_index(wanted, lon)

    verdicts = []
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
        if dup and n_trk and dup >= n_trk:
            verdict = "ALREADY_LINKED"
        else:
            if dup:
                reasons.append(f"partial_duplicate({dup}/{n_trk})")
            if not fit.get("converged"):
                reasons.append(f"not_converged({fit.get('status')})")
            gate = fit.get("gate_strict") or {}
            if not gate.get("passes"):
                reasons.append("strict_gate:" + "; ".join(gate.get("reasons") or ["?"]))
            if fit.get("trk_obs_used", 0) != fit.get("trk_obs_total", -1):
                reasons.append(
                    f"tracklet_not_fully_used({fit.get('trk_obs_used')}/"
                    f"{fit.get('trk_obs_total')})"
                )
            n_obs, n_used = fit.get("n_obs") or 0, fit.get("n_used") or 0
            if not n_obs or n_used / n_obs < MIN_USED_FRACTION:
                reasons.append(f"joint_set_not_used({n_used}/{n_obs})")
            verdict = "PASS" if not reasons else "FAIL"

        verdicts.append(
            {
                "orbit_desig": f["orbit_desig"],
                "trksub": f["trksub"],
                "obscode": f["obscode"],
                "night": f["night"],
                "link_key": f.get("link_key"),
                "sep_arcsec": round(f["sep_arcsec"], 1),
                "dt_days": round(f["dt_days"], 1),
                "rms_joint": fit.get("rms_joint"),
                "rms_baseline": (fit.get("baseline") or {}).get("rms"),
                "duplicates_in_published": dup,
                "trk_obs_total": n_trk,
                "verdict": verdict,
                "reasons": reasons,
                "mpc_published_gate_passes": (fit.get("gate_mpc_published") or {}).get(
                    "passes"
                ),
            }
        )

    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    out = {
        "generated_from": str(REPORT.name),
        "rules": {
            "dup_epoch_s": DUP_EPOCH_S,
            "dup_pos_arcsec": DUP_POS_ARCSEC,
            "min_used_fraction": MIN_USED_FRACTION,
        },
        "counts": counts,
        "verdicts": verdicts,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"verdicts: {counts}")
    for v in verdicts:
        if v["verdict"] != "FAIL":
            print(
                f"{v['verdict']:14s} {v['orbit_desig']:12s} + {v['trksub']:8s}"
                f" {v['obscode']} night {v['night']}  sep {v['sep_arcsec']:7.1f}\""
                f"  rms {v['rms_joint']}  dup {v['duplicates_in_published']}"
                f"/{v['trk_obs_total']}  key {v['link_key']}"
            )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
