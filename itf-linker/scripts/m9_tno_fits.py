"""M9: fit the three TNO scoping candidates through the standard chain. Bounded.

``scripts/m9_tno.py`` found exactly three coarse candidates against a zero decoy
background inside 300 arcsec. Three fits is not a campaign; it is the difference
between "a scoping histogram" and "three named, gated, reviewable candidates" for the
M10 decision. Machinery is ``m8_attribution.joint_fit`` unchanged (fo, perturbers,
strict + published gates, the fully-used question first); fit artifacts go under
``data/m9-fits`` with tags ``m9h####`` (joint) / ``m9i####`` (baselines).

Writes ``m9-tno-fits.json`` (root, gitignored). Nothing is submitted.
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

import m8_attribution as m8run

from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index

SCOPING = ROOT / "m9-tno-scoping.json"
OUT = ROOT / "m9-tno-fits.json"


def main() -> None:
    m8run.FIT_ROOT = ROOT / "data" / "m9-fits"
    doc = json.loads(SCOPING.read_text(encoding="utf-8"))
    cands = doc["real_matches"]
    print(f"TNO candidates to fit: {len(cands)}", flush=True)

    lon = fetch_obscodes()
    index, _ = tracklet_line_index({c["trksub"] for c in cands}, lon)
    shell = default_shell()
    baseline_cache: dict[str, Any] = {}
    results = []
    for i, c in enumerate(cands):
        lines = index.get((c["trksub"], c["obscode"], c["night"]))
        if not lines:
            results.append({**c, "fit": {"status": "tracklet_lines_missing"}})
            continue
        tag, base_tag = f"m9h{i:04d}", f"m9i{i:04d}"
        print(f"fit {tag}: {c['orbit_desig']} (a={c['orbit_a_au']} AU) + "
              f"{c['trksub']}/{c['obscode']}/n{c['night']} "
              f"sep {c['sep_arcsec']:.0f}\" dt {c['dt_days'] / 365.25:+.1f}y",
              flush=True)
        outcome = m8run.joint_fit(tag, base_tag, c["orbit_desig"], lines, shell,
                                  baseline_cache)
        ok = bool(outcome.get("gate_strict", {}).get("passes")
                  and outcome.get("trk_obs_used", 0) == outcome.get("trk_obs_total", -1))
        results.append({**c, "fit": outcome, "fit_tag": tag,
                        "passes_strict_and_fully_used": ok})
        print(f"  -> rms {outcome.get('rms_joint')} used "
              f"{outcome.get('trk_obs_used')}/{outcome.get('trk_obs_total')} "
              f"strict={outcome.get('gate_strict', {}).get('passes')} "
              f"PASS-grade={ok}", flush=True)

    OUT.write_text(json.dumps({
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "three scoping candidates fitted; not a campaign (M9-RESULTS §8)",
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
