"""Bounded, fail-closed E readiness check; never fetch or analyze E products.

The historical M5/M6 scripts and frozen scientific rules remain unchanged.
Only public proposal metadata and the already-public D acceptance control are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "2026-09-09"
MAP_HASH = "fa93e2c852befdb51f661f65a3a6bd92333d8e4cb8b581af33555feab87b937b"
MARKER = "E_METADATA_JSON="
MAST_QUERY = r'''
import json
from astroquery.mast import Observations
from astropy.time import Time
from collections import Counter
Observations.TIMEOUT = 30
rows = Observations.query_criteria(proposal_id="7199")
rows = rows[["object_e" in str(v).lower() for v in rows["target_name"]]]
result = {"count": len(rows),
          "rights": dict(Counter(str(v).upper() for v in rows["dataRights"])),
          "release_dates": sorted(set(Time(float(v), format="mjd").iso[:10]
                                      for v in rows["t_obs_release"]))}
print("E_METADATA_JSON=" + json.dumps(result))
'''


def outcome_hash(text):
    start = text.index("### 5.3 The outcome map")
    end = text.index("\n## ", start)
    return hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()


def acceptance(returncode, output):
    passes = len(re.findall(r"\bPASS\b", output))
    failures = len(re.findall(r"\bFAIL\b", output))
    return {"returncode": returncode, "passes": passes, "failures": failures,
            "passed": returncode == 0 and passes == 7 and failures == 0}


def classify(metadata, *, map_ok, control_ok, today):
    """No empty, malformed, stale, or failed query can become readiness."""
    if not map_ok or not control_ok:
        return "STOP_PROCEDURE"
    if metadata is None:
        return "UNAVAILABLE"
    if not isinstance(metadata, dict):
        return "STOP_METADATA"
    rights = metadata.get("rights")
    count = metadata.get("count")
    if (type(count) is not int or count != 39 or not isinstance(rights, dict)
            or set(rights) - {"PUBLIC", "EXCLUSIVE_ACCESS"}
            or any(type(v) is not int or v < 0 for v in rights.values())
            or sum(rights.values()) != count
            or metadata.get("release_dates") != [RELEASE]):
        return "STOP_METADATA"
    # An early release never advances the frozen analysis date.
    if date.fromisoformat(today) < date.fromisoformat(RELEASE):
        return "WAIT_RELEASE"
    if rights.get("PUBLIC", 0) != count:
        return "WAIT_PUBLIC_PRODUCTS"
    return "READY_FOR_FROZEN_ANALYSIS"


def bounded_run(command, timeout):
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8",
                               errors="replace", start_new_session=os.name != "nt")
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout + stderr
    except subprocess.TimeoutExpired:
        # Windows venv redirectors can leave a base-Python descendant alive if only
        # the launcher is killed. Target exclusively the tree we just created.
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, check=False, timeout=10)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)
        return 124, f"hard timeout after {timeout} seconds"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 180:
        parser.error("timeout must be between 1 and 180 seconds")
    report = {"checked_utc": datetime.now(timezone.utc).isoformat(),
              "release_date": RELEASE, "expected_observations": 39,
              "scientific_analysis_executed": False}
    frozen = (ROOT / "M5-nebular-stage-highlat-catalog.md").read_text(encoding="utf-8")
    report["outcome_map_sha256"] = outcome_hash(frozen)
    report["map_unchanged"] = report["outcome_map_sha256"] == MAP_HASH
    code, output = bounded_run(
        [sys.executable, "scripts/m5_jwst_target.py", "measure", "--label", "D",
         "--obsprefix", "jw07199-o005", "--validate"], args.timeout)
    report["public_D_control"] = acceptance(code, output)
    # Do not publish coordinate-bearing stdout; keep only the acceptance counts.
    code, output = bounded_run([sys.executable, "-c", MAST_QUERY], args.timeout)
    report["metadata_query_returncode"] = code
    metadata = None
    if code == 0:
        lines = [line for line in output.splitlines() if line.startswith(MARKER)]
        if len(lines) == 1:
            try:
                metadata = json.loads(lines[0][len(MARKER):])
            except json.JSONDecodeError:
                pass
    report["metadata"] = metadata
    report["status"] = classify(
        metadata, map_ok=report["map_unchanged"],
        control_ok=report["public_D_control"]["passed"],
        today=report["checked_utc"][:10])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"].startswith(("WAIT_", "READY_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
