"""M9: verdict chain v2 over the M9 fits — appends to the candidate ledger, never rewrites.

Two fit populations feed it, each tagged with its provenance:

* ``M9-partitions`` — the unconsumed-partition queue (``m9-attribution.json``).
* ``M9-extension`` — the M8 queue extended past rank 901 (``m8-attribution.json``
  after the extension run). Fits whose (orbit, link_key) already carry an M8 ledger
  verdict are skipped — their rows live in ``m8-ledger.json``, which this script never
  touches (M9 task law: append with m9 tags, never rewrite).

The chain is ``scripts/m8_verdicts.py``'s exactly (its functions are imported): the
"did fo actually use the tracklet" question first, duplicate check against the
object's published record, strict + published gates, SkyBoT cone search with the
frozen informative-claimant rule, lost-object ambiguities named.

``m9-ledger.json`` is written self-contained for review: M9 verdict rows, M7's held
candidates verbatim, the consumed-candidate ground-truth block
(``m9_consumed_check.py``), and a freshness note — every M9 row also carries
``in_itf_20260818`` so a reviewer can see instantly whether the tracklet still exists
in the current ITF.
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

import m8_verdicts as m8v
import polars as pl

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index
from itf_linker.mpc80 import parse_line
from itf_linker.vet.cache import CachedSession

M9_REPORT = ROOT / "m9-attribution.json"
M8_REPORT = ROOT / "m8-attribution.json"
M8_LEDGER = ROOT / "m8-ledger.json"
CONSUMED = ROOT / "data" / "raw" / "rubin" / "m9-consumed-check.json"
DROPPED = ROOT / "data" / "raw" / "rubin" / "m9-dropped-tracklets.parquet"
VET_CACHE = ROOT / "data" / "vet-cache"
OUT = ROOT / "m9-ledger.json"


def orbit_desig_map() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for pq in (ROOT / "data" / "raw" / "rubin" / "m8-orbits.parquet",
               ROOT / "data" / "raw" / "rubin" / "m9-orbits.parquet"):
        if pq.exists():
            df = pl.read_parquet(pq, columns=["primary", "all_desigs"])
            out.update(zip(df["primary"].to_list(), df["all_desigs"].to_list()))
    return out


def main() -> None:
    fits: list[tuple[str, dict[str, Any]]] = []
    m9doc = json.loads(M9_REPORT.read_text(encoding="utf-8"))
    for f in m9doc.get("fits") or []:
        fits.append(("M9-partitions", f))

    m8_ledgered = {
        (v["orbit_desig"], v["link_key"])
        for v in json.loads(M8_LEDGER.read_text(encoding="utf-8"))["verdicts"]
    }
    m8doc = json.loads(M8_REPORT.read_text(encoding="utf-8"))
    n_skipped_m8 = 0
    for f in m8doc.get("fits") or []:
        if (f["orbit_desig"], f.get("link_key")) in m8_ledgered:
            n_skipped_m8 += 1
            continue
        fits.append(("M9-extension", f))
    print(f"fits to adjudicate: {len(fits)} "
          f"(skipped {n_skipped_m8} already in m8-ledger.json)", flush=True)
    if not fits:
        print("nothing to do")
        return

    lon = fetch_obscodes()
    wanted = {f["trksub"] for _, f in fits}
    index, _ = tracklet_line_index(wanted, lon)
    session = CachedSession(VET_CACHE)
    desigs = orbit_desig_map()

    dropped = pl.read_parquet(DROPPED)
    dset = set(zip(dropped["desig"].to_list(), dropped["obscode"].to_list(),
                   dropped["night"].to_list()))

    verdicts = []
    n_skybot = 0
    for provenance, f in fits:
        fit = f.get("fit") or {}
        key = (f["trksub"], f["obscode"], f["night"])
        trk_lines = index.get(key) or []
        pub = m8v.published_obs(f["orbit_desig"])
        dup = m8v.count_duplicates(trk_lines, pub) if trk_lines else 0
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
            fully_used = fit.get("trk_obs_used", 0) == fit.get("trk_obs_total", -1)
            if not fully_used:
                reasons.append(
                    f"tracklet_not_fully_used({fit.get('trk_obs_used')}/"
                    f"{fit.get('trk_obs_total')})"
                )
            if not fit.get("converged"):
                reasons.append(f"not_converged({fit.get('status')})")
            gate = fit.get("gate_strict") or {}
            if not gate.get("passes"):
                reasons.append("strict_gate:" + "; ".join(gate.get("reasons") or ["?"]))
            n_obs, n_used = fit.get("n_obs") or 0, fit.get("n_used") or 0
            if not n_obs or n_used / n_obs < m8v.MIN_USED_FRACTION:
                reasons.append(f"joint_set_not_used({n_used}/{n_obs})")

            published_ok = bool((fit.get("gate_mpc_published") or {}).get("passes"))
            rms = fit.get("rms_joint")
            only_strict_failed = (
                reasons
                and all(r.startswith("strict_gate:") for r in reasons)
                and published_ok
                and rms is not None
                and rms <= 0.25 + m8v.BORDERLINE_RMS_ARCSEC
            )
            if not reasons:
                verdict = "PASS"
            elif only_strict_failed:
                verdict = "BORDERLINE"
            else:
                verdict = "FAIL"

            if verdict in ("PASS", "BORDERLINE") and trk_lines:
                skybot = m8v.skybot_check(
                    session, trk_lines, f["orbit_desig"],
                    desigs.get(f["orbit_desig"], []),
                )
                n_skybot += 1
                if skybot.get("conflicts"):
                    verdict = "SKYBOT_CONFLICT"
                    reasons.append(
                        "skybot_conflict:"
                        + "; ".join(
                            f"{c['name']} at {c['sep_arcsec']}\""
                            for c in skybot["conflicts"]
                        )
                    )
                elif skybot.get("status") != "ok":
                    reasons.append(f"skybot_{skybot.get('status')}")
                if skybot.get("lost_object_ambiguity"):
                    reasons.append(
                        "skybot_lost_object_ambiguity:"
                        + "; ".join(
                            f"{c['name']} (err {c['ephem_err_arcsec']}\")"
                            for c in skybot["lost_object_ambiguity"][:3]
                        )
                    )

        verdicts.append(
            {
                "provenance": provenance,
                "orbit_desig": f["orbit_desig"],
                "trksub": f["trksub"],
                "obscode": f["obscode"],
                "night": f["night"],
                "link_key": f.get("link_key"),
                "partitions": f.get("partitions"),
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
                "in_itf_20260818": key not in dset,
            }
        )

    counts: dict[str, dict[str, int]] = {}
    for v in verdicts:
        c = counts.setdefault(v["provenance"], {})
        c[v["verdict"]] = c.get(v["verdict"], 0) + 1

    ledger = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generated_from": [M9_REPORT.name, M8_REPORT.name],
        "m8_ledger_untouched": M8_LEDGER.name,
        "rules": {
            "dup_epoch_s": m8v.DUP_EPOCH_S,
            "dup_pos_arcsec": m8v.DUP_POS_ARCSEC,
            "min_used_fraction": m8v.MIN_USED_FRACTION,
            "borderline_rms_arcsec": m8v.BORDERLINE_RMS_ARCSEC,
            "skybot_radius_deg": m8v.SKYBOT_RADIUS_DEG,
            "skybot_claim_arcsec": m8v.SKYBOT_CLAIM_ARCSEC,
            "skybot_claimant_max_err_arcsec": m8v.SKYBOT_CLAIMANT_MAX_ERR_ARCSEC,
            "note": "identical to m8-ledger.json rules; nothing loosened",
        },
        "counts_m9": counts,
        "skybot_calls": n_skybot,
        "consumed_check": json.loads(CONSUMED.read_text(encoding="utf-8"))["summary"],
        "held_from_m7": m8v.M7_HELD,
        "verdicts": verdicts,
    }
    OUT.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    print(f"M9 verdicts: {json.dumps(counts)}; SkyBoT calls: {n_skybot}")
    for v in verdicts:
        if v["verdict"] not in ("FAIL",):
            print(
                f"{v['verdict']:15s} [{v['provenance']:13s}] {v['orbit_desig']:12s} "
                f"+ {v['trksub']:8s} {v['obscode']} n{v['night']}  "
                f"dt {v['dt_years']:+6.2f}y  sep {v['sep_arcsec']:7.1f}\"  "
                f"rms {v['rms_joint']}  used {v['trk_obs_used']}/{v['trk_obs_total']}"
                f"  {v['link_key']}"
            )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
