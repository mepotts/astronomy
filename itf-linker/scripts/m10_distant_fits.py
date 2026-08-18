"""M10: fit the all-sky distant candidates that survive both screens. Bounded.

M9 fitted three scoping candidates and lost all three, two of them to a confound it
discovered on the way out. M10's all-sky sweep produces a larger head, and §6 screens it
twice — for pointed fields and for self-designation artefacts — *before* anything is
fitted. What is left is what the distant regime actually offers, and this fits it.

Bounded by construction: only rows in the screened head that sit **under 5 arcsec**,
which the decoy prices at 2 chance matches against 11 real. That is a handful of fo
runs, not a campaign. Machinery is ``m8_attribution.joint_fit`` unchanged; tags
``mAh####`` (joint) / ``mAi####`` (baseline) under ``data/m10-fits``.

Writes ``m10-distant-fits.json``.
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

import m8_attribution as m8run

from itf_linker import config
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index

POINTED = ROOT / "data" / "raw" / "rubin" / "m10-pointed.json"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
OUT = ROOT / "m10-distant-fits.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-sep-arcsec", type=float, default=5.0)
    args = ap.parse_args()

    config.ITF_PARQUET = RECONSTRUCTED
    m8run.FIT_ROOT = ROOT / "data" / "m10-fits"

    sweep = json.loads(POINTED.read_text(encoding="utf-8"))["allsky_sweep"]
    cands = [
        m for m in sweep["top"]
        if m["sep_arcsec"] < args.max_sep_arcsec
        and not m["pointed_screen"]["screened_out"]
        and not m["self_designation"]["self_designation"]
    ]
    screened = [
        m for m in sweep["top"]
        if m["sep_arcsec"] < args.max_sep_arcsec
        and (m["pointed_screen"]["screened_out"]
             or m["self_designation"]["self_designation"])
    ]
    print(f"under {args.max_sep_arcsec}\": {len(cands) + len(screened)} rows, "
          f"{len(screened)} removed by the screens, {len(cands)} to fit", flush=True)

    lon = fetch_obscodes()
    index, _ = tracklet_line_index({c["trksub"] for c in cands}, lon)
    shell = default_shell()
    baseline_cache: dict[str, Any] = {}
    results = []
    for i, c in enumerate(cands):
        lines = index.get((c["trksub"], c["obscode"], c["night"]))
        if not lines:
            results.append({**c, "fit": {"status": "tracklet_lines_missing"}})
            print(f"  {c['orbit_desig']} + {c['trksub']}: tracklet lines missing",
                  flush=True)
            continue
        tag, base_tag = f"mAh{i:04d}", f"mAi{i:04d}"
        print(f"fit {tag}: {c['orbit_desig']} (a={c['orbit_a_au']} AU) + "
              f"{c['trksub']}/{c['obscode']}/n{c['night']} "
              f"sep {c['sep_arcsec']:.2f}\"/{c['gate_radius_arcsec']:.0f}\" "
              f"dt {c['dt_days'] / 365.25:+.2f}y", flush=True)
        outcome = m8run.joint_fit(tag, base_tag, c["orbit_desig"], lines, shell,
                                  baseline_cache)
        ok = bool(outcome.get("gate_strict", {}).get("passes")
                  and outcome.get("trk_obs_used", 0) == outcome.get("trk_obs_total", -1))
        results.append({**c, "fit": outcome, "fit_tag": tag,
                        "passes_strict_and_fully_used": ok})
        print(f"  -> rms {outcome.get('rms_joint')} (baseline "
              f"{(outcome.get('baseline') or {}).get('rms')}) used "
              f"{outcome.get('trk_obs_used')}/{outcome.get('trk_obs_total')} "
              f"strict={outcome.get('gate_strict', {}).get('passes')} "
              f"PASS-grade={ok}", flush=True)

    n_pass = sum(1 for r in results if r.get("passes_strict_and_fully_used"))
    OUT.write_text(json.dumps({
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "all-sky distant head, both screens applied before fitting "
                "(M10-RESULTS.md section 6)",
        "max_sep_arcsec": args.max_sep_arcsec,
        "n_candidates": len(cands),
        "n_removed_by_screens": len(screened),
        "removed_by_screens": [
            {"orbit_desig": m["orbit_desig"], "trksub": m["trksub"],
             "obscode": m["obscode"], "sep_arcsec": m["sep_arcsec"],
             "pointed": m["pointed_screen"]["flags"],
             "self_designation": m["self_designation"]["self_designation"]}
            for m in screened
        ],
        "n_pass_grade": n_pass,
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"PASS-grade: {n_pass}/{len(cands)}")
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
