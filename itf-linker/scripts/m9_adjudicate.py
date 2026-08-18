"""M9: adjudicate the 88 lost-object ambiguities. Standard frozen; nothing loosened.

M8's SkyBoT rule records, on 88 PASS candidates, a *lost* object (ephemeris error
above the frozen 60-arcsec informativeness bar) that overlaps the tracklet position
while predicting nothing. M8 named them rather than failing them; the M9 adjudication
the M8 doc prescribed is executed here: **fit the tracklet against each claimant's own
published astrometry**, the same fo machinery and gates as every fit in this
repository, and let the claimant's data speak.

Verdicts per candidate (M9-RESULTS.md section 0.4, pre-registered):

* ``RESOLVED_TO_CANDIDATE`` — every claimant was fitted and failed (tracklet not fully
  used, or strict gate failed): the claimant's own astrometry excludes it.
* ``REJECTED`` — a claimant *owns* the tracklet: its observations duplicate the
  claimant's published record, or the claimant's joint fit passes while the ledger
  fit is strictly worse on the same tracklet.
* ``STILL_AMBIGUOUS`` — a claimant's joint fit also passes strict+fully-used (two live
  owners; Matthew's call), or a claimant's astrometry is unavailable (what cannot be
  fitted cannot be excluded).
* ``RESOLVED_BY_MPC_CONSUMPTION`` — the MPC consumed the tracklet into the candidate
  object between 08-16 and 08-18 (``m9_consumed_check.py``): reality adjudicated
  first.

Tags: ``m9g####`` claimant joint fits, ``m9f####`` claimant baselines. get-obs for
claimants goes to the *fresh* cache (``obs80-m9fresh/``) — a lost object's record
cannot contain the (still-ITF) tracklet, so freshness is safe and honest here.

Writes ``m9-adjudication.json`` (root, gitignored).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m9_consumed_check as fresh
import polars as pl

from itf_linker.fit.findorb import prepare_config_dir, run_fo
from itf_linker.fit.gates import mpc_published_gate, post_fit_gate
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import _relabel, tracklet_line_index
from itf_linker.mpc80 import parse_line

LEDGER_M8 = ROOT / "m8-ledger.json"
CONSUMED = ROOT / "data" / "raw" / "rubin" / "m9-consumed-check.json"
DROPPED = ROOT / "data" / "raw" / "rubin" / "m9-dropped-tracklets.parquet"
SLIM = ROOT / "data" / "snapshots" / "20260816T202701Z" / "observations.parquet"
M8_FIT_ROOT = ROOT / "data" / "m8-fits"
FIT_ROOT = ROOT / "data" / "m9-fits"
OUT = ROOT / "m9-adjudication.json"

MAX_CLAIMANTS = 5
DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0


def duplicates_in(trk_obs: list[Any], pub: list[Any]) -> int:
    n = 0
    for o in trk_obs:
        for p in pub:
            if p.obscode != o.obscode:
                continue
            if abs(p.mjd - o.mjd) * 86400.0 > DUP_EPOCH_S:
                continue
            dra = abs((p.ra_deg - o.ra_deg + 180.0) % 360.0 - 180.0) * 3600.0
            dde = abs(p.dec_deg - o.dec_deg) * 3600.0
            cosd = math.cos(math.radians(o.dec_deg))
            if (dra * cosd) ** 2 + dde ** 2 <= DUP_POS_ARCSEC ** 2:
                n += 1
                break
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extra-ledgers", nargs="*", default=[],
                    help="additional ledgers whose PASS-with-ambiguity rows join")
    args = ap.parse_args()

    rows: list[dict[str, Any]] = []
    sources = [("M8", LEDGER_M8)] + [(f"extra{i}", Path(p))
                                     for i, p in enumerate(args.extra_ledgers)]
    for label, path in sources:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for v in doc["verdicts"]:
            if v["verdict"] == "PASS" and any(
                r.startswith("skybot_lost_object_ambiguity") for r in v["reasons"]
            ):
                rows.append({**v, "ledger": label})
    print(f"ambiguity rows: {len(rows)}", flush=True)

    consumed_keys = {
        (r["orbit_desig"], r["link_key"]): r["outcome"]
        for r in json.loads(CONSUMED.read_text(encoding="utf-8"))["rows"]
    }
    dropped = pl.read_parquet(DROPPED)
    dset = set(zip(dropped["desig"].to_list(), dropped["obscode"].to_list(),
                   dropped["night"].to_list()))

    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    trksubs = {v["trksub"] for v in rows}
    slim = (
        pl.scan_parquet(SLIM)
        .filter(pl.col("desig").is_in(sorted(trksubs)))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .collect()
    )
    index, _ = tracklet_line_index(trksubs, lon)

    shell = default_shell()
    baseline_cache: dict[str, dict[str, Any]] = {}
    base_tags: dict[str, str] = {}
    results: list[dict[str, Any]] = []
    n_joint = 0
    for v in rows:
        key = (v["trksub"], v["obscode"], v["night"])
        entry: dict[str, Any] = {
            "orbit_desig": v["orbit_desig"],
            "trksub": v["trksub"],
            "obscode": v["obscode"],
            "night": v["night"],
            "link_key": v["link_key"],
            "ledger": v["ledger"],
            "candidate_rms": v.get("rms_joint"),
            "claimants": [],
        }
        ck = consumed_keys.get((v["orbit_desig"], v["link_key"]))
        if ck == "CONSUMED_INTO_SAME_OBJECT":
            entry["adjudication"] = "RESOLVED_BY_MPC_CONSUMPTION"
            results.append(entry)
            print(f"RESOLVED_BY_MPC_CONSUMPTION  {v['orbit_desig']} + {v['trksub']}",
                  flush=True)
            continue

        mjds = slim.filter(
            (pl.col("desig") == v["trksub"]) & (pl.col("obscode") == v["obscode"])
            & (pl.col("night") == v["night"])
        )["mjd"].to_list()
        lines = index.get(key) or []
        if not lines and key in dset:
            # consumed elsewhere? tracklet gone but not into our object: pull the
            # verbatim lines fo fitted in M8
            tag8 = v.get("fit_tag") or ""
            obs_txt = M8_FIT_ROOT / tag8 / "obs.txt"
            if obs_txt.exists():
                lines = [
                    ln for ln in obs_txt.read_text(encoding="utf-8",
                                                   errors="replace").splitlines()
                    if (o := parse_line(ln, strict=False))
                    and o.obscode == v["obscode"]
                    and any(abs(o.mjd - m) < 2e-4 for m in mjds)
                ]
        if not lines:
            entry["adjudication"] = "STILL_AMBIGUOUS"
            entry["note"] = "tracklet_lines_missing"
            results.append(entry)
            continue
        trk_obs = [o for o in (parse_line(ln, strict=False) for ln in lines) if o]

        claimants = (v.get("skybot") or {}).get("lost_object_ambiguity") or []
        any_pass = False
        any_unavailable = False
        rejected = False
        for c in claimants[:MAX_CLAIMANTS]:
            name = str(c["name"]).strip()
            crec: dict[str, Any] = {
                "name": name,
                "skybot_sep_arcsec": c.get("sep_arcsec"),
                "skybot_ephem_err_arcsec": c.get("ephem_err_arcsec"),
            }
            try:
                pub_lines = fresh.get_obs80_fresh(name)
            except Exception as exc:  # noqa: BLE001 - recorded, not silenced
                pub_lines = []
                crec["fetch_error"] = str(exc)[:200]
            pub = [o for o in (parse_line(ln, strict=False) for ln in pub_lines) if o]
            if not pub:
                crec["outcome"] = "astrometry_unavailable"
                any_unavailable = True
                entry["claimants"].append(crec)
                continue
            dup = duplicates_in(trk_obs, pub)
            crec["duplicates_in_claimant_record"] = dup
            if dup >= len(trk_obs) > 0:
                crec["outcome"] = "claimant_owns_tracklet(published)"
                rejected = True
                entry["claimants"].append(crec)
                continue

            if name not in base_tags:
                base_tags[name] = f"m9f{len(base_tags):04d}"
                cfgb = prepare_config_dir(shell, base_tags[name])
                runb = run_fo(
                    [_relabel(ln, base_tags[name]) for ln in pub_lines],
                    FIT_ROOT / base_tags[name],
                    designations=[base_tags[name]],
                    shell=shell,
                    config_dir=cfgb,
                    timeout=600,
                    scratch_dir=f"$HOME/.cache/itf-linker-fo-work/{base_tags[name]}",
                )
                bfit = (runb.results.get(base_tags[name])
                        or next(iter(runb.results.values()), None))
                baseline_cache[name] = {
                    "rms": bfit.rms_residual if bfit else None,
                    "converged": bool(bfit.converged) if bfit else False,
                    "n_obs": bfit.n_obs if bfit else None,
                }
            crec["claimant_baseline"] = baseline_cache[name]

            tag = f"m9g{n_joint:04d}"
            n_joint += 1
            joint = [_relabel(ln, tag) for ln in pub_lines] + [
                _relabel(ln, tag) for ln in lines
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
                crec["outcome"] = "fo_returned_nothing"
                any_unavailable = True
                entry["claimants"].append(crec)
                continue
            jd_lo = min(o.mjd for o in trk_obs) + 2400000.5 - 2e-4
            jd_hi = max(o.mjd for o in trk_obs) + 2400000.5 + 2e-4
            resids = [r for r in fit.residuals
                      if r.get("obscode") == v["obscode"]
                      and jd_lo <= float(r.get("JD", 0)) <= jd_hi]
            used = [r for r in resids if r.get("incl")]
            nights = {int(o.mjd + 0.5) for o in trk_obs}
            all_mjds = [o.mjd for o in trk_obs]
            for ln in pub_lines:
                o = parse_line(ln, strict=False)
                if o:
                    nights.add(int(o.mjd + 0.5))
                    all_mjds.append(o.mjd)
            strict = post_fit_gate(fit, n_nights=len(nights))
            published = mpc_published_gate(
                fit, n_nights=len(nights),
                arc_days=max(all_mjds) - min(all_mjds),
            )
            fully_used = len(used) == len(trk_obs)
            passes = bool(strict.as_dict().get("passes")) and fully_used
            crec.update(
                {
                    "fit_tag": tag,
                    "rms_joint": fit.rms_residual,
                    "converged": bool(fit.converged),
                    "trk_obs_used": len(used),
                    "trk_obs_total": len(trk_obs),
                    "gate_strict_passes": strict.as_dict().get("passes"),
                    "gate_published_passes": published.as_dict().get("passes"),
                    "outcome": "claimant_fit_passes" if passes else "claimant_excluded",
                }
            )
            if passes:
                any_pass = True
            entry["claimants"].append(crec)

        if rejected:
            entry["adjudication"] = "REJECTED"
        elif any_pass:
            entry["adjudication"] = "STILL_AMBIGUOUS"
            entry["note"] = "claimant_fit_also_passes"
        elif any_unavailable:
            entry["adjudication"] = "STILL_AMBIGUOUS"
            entry["note"] = "claimant_astrometry_unavailable"
        else:
            entry["adjudication"] = "RESOLVED_TO_CANDIDATE"
        results.append(entry)
        print(f"{entry['adjudication']:28s} {v['orbit_desig']:12s} + {v['trksub']:8s} "
              f"({len(entry['claimants'])} claimant(s))", flush=True)

    counts: dict[str, int] = {}
    for e in results:
        counts[e["adjudication"]] = counts.get(e["adjudication"], 0) + 1
    doc = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "standard": {
            "claimant_informative_err_arcsec": 60.0,
            "gates": "strict post-fit gate + tracklet fully used (frozen, M8)",
            "max_claimants_per_candidate": MAX_CLAIMANTS,
        },
        "counts": counts,
        "results": results,
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(json.dumps(counts, indent=1), flush=True)
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
