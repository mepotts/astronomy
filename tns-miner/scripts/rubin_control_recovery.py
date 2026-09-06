"""Two corrected public cones; preserve the failed first requests unchanged."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parents[1] / "data/probes"


def main():
    out = BASE / "20260906_rubin_recovery"
    out.mkdir(exist_ok=False)
    plan = []
    for label in ("Z_Cha", "HL_CMa"):
        resolved = json.loads((BASE / "20260906_rubin_followup" / f"{label}_resolver.response").read_bytes())[0]
        plan.append({"label": label, "params": {
            "ra": resolved["jradeg"], "dec": resolved["jdedeg"], "radius": 3, "n": 10,
            "kind": "across", "startdate": "2025-01-01", "stopdate": "2026-09-06",
            "columns": "r:diaObjectId,r:midpointMjdTai,f:firstDiaSourceMjdTaiFink"}})
    (out / "contract.json").write_text(json.dumps({"plan": plan, "max_requests": 2,
        "reason": "HTTP 400 explicitly requires the first-detection field for date filtering",
        "created_utc": datetime.now(timezone.utc).isoformat(), "retries": 0}, indent=2))
    for item in plan:
        with requests.get("https://api.lsst.fink-portal.org/api/v1/conesearch", params=item["params"],
                          timeout=(10, 30), stream=True, allow_redirects=False) as response:
            raw = response.raw.read(1024**2 + 1)
            if len(raw) > 1024**2:
                raise ValueError("response exceeds cap")
            (out / (item["label"] + ".response")).write_bytes(raw)
            item.update(status=response.status_code, bytes=len(raw),
                        sha256=hashlib.sha256(raw).hexdigest())
            if response.status_code == 200:
                item["rows"] = len(json.loads(raw))
        print(json.dumps(item), flush=True)
    (out / "results.json").write_text(json.dumps(plan, indent=2))
    manifest = {"files": [{"name": p.name, "bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
