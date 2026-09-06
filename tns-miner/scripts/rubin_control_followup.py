"""Finite public-control diagnostic, not an unknown-object or population scan."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parents[1] / "data/probes"
OUT = BASE / "20260906_rubin_followup"
OID = "313761043604045880"
MAX_BYTES = 16 * 1024**2


def run():
    OUT.mkdir(exist_ok=False)
    old = json.loads((BASE / "20260905_rubin_metadata/fink_documented_sources.response").read_bytes())
    tab = json.loads((BASE / "20260905_rubin_tap/known_detections.response").read_bytes())
    columns = [c["name"] for c in tab["columns"]]
    alerce = [dict(zip(columns, r)) for r in tab["data"] if str(r[0]) == OID]
    ids = {str(r["r:diaSourceId"]) for r in old}
    missing = sorted((r for r in alerce if str(r["measurement_id"]) not in ids), key=lambda r: r["mjd"])
    contract = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "known_oid": OID,
        "fixed_new_public_names": ["Z Cha", "HL CMa"],
        "selection": "earliest ALeRCE-only detection and earliest shared detection from frozen Sept 5 inputs",
        "missing_probe": missing[0], "shared_probe": min(old, key=lambda r: r["r:midpointMjdTai"]),
        "max_requests": 13, "max_response_bytes": MAX_BYTES, "retries": 0,
        "scope": "3 source diagnostics, forced photometry, 3 source files, 2 resolvers and 4 cones",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    records = []

    def get(label, url, params=None):
        if len(records) >= 13:
            raise ValueError("request budget exhausted")
        rec = {"label": label, "url": url, "params": params or {},
               "started_utc": datetime.now(timezone.utc).isoformat()}
        records.append(rec)
        body = None
        try:
            with requests.get(url, params=params, timeout=(10, 30), stream=True,
                              allow_redirects=False) as response:
                rec["status"] = response.status_code
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        raise ValueError("response exceeds cap")
                (OUT / f"{label}.response").write_bytes(data)
                rec.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                if response.status_code == 200:
                    try:
                        body = json.loads(data)
                        rec["rows"] = len(body) if isinstance(body, list) else len(body.get("data", []))
                    except ValueError:
                        rec["format"] = "text"
        except (requests.RequestException, ValueError) as exc:
            rec["error"] = str(exc)
        (OUT / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        print(json.dumps(rec), flush=True)
        return body

    url = "https://api.lsst.fink-portal.org/api/v1/"
    get("sources_all_columns", url + "sources", {"diaObjectId": OID})
    get("missing_epoch", url + "sources", {"diaObjectId": OID, "midpointMjdTai": str(missing[0]["mjd"])})
    get("shared_epoch", url + "sources", {"diaObjectId": OID, "midpointMjdTai": str(contract["shared_probe"]["r:midpointMjdTai"])})
    get("forced_all_columns", url + "fp", {"diaObjectId": OID})
    for part in ("sources/utils.py", "fp/utils.py", "sources/api.py"):
        get(part.replace("/", "_"), "https://raw.githubusercontent.com/astrolabsoftware/fink-object-api/main/apps/routes/v1/lsst/" + part)
    for name in contract["fixed_new_public_names"]:
        label = name.replace(" ", "_")
        resolved = get(label + "_resolver", url + "resolver",
                       {"resolver": "simbad", "name_or_id": name, "reverse": "true", "nmax": 2})
        if not isinstance(resolved, list) or len(resolved) != 1:
            continue
        ra, dec = resolved[0]["jradeg"], resolved[0]["jdedeg"]
        get(label + "_fink", url + "conesearch", {
            "ra": ra, "dec": dec, "radius": 3, "n": 10, "kind": "across",
            "startdate": "2025-01-01", "stopdate": "2026-09-06",
            "columns": "r:diaObjectId,r:midpointMjdTai"})
        get(label + "_alerce", "https://tap.alerce.online/tap/sync", {
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json", "MAXREC": 1,
            "QUERY": f"SELECT COUNT(*) AS n FROM alerce_tap.object WHERE sid=1 AND 1=CONTAINS(POINT('ICRS',meanra,meandec),CIRCLE('ICRS',{ra},{dec},0.0008333333333333334))"})
        time.sleep(0.2)
    manifest = {"files": [{"name": p.name, "bytes": p.stat().st_size,
                            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in sorted(OUT.iterdir()) if p.is_file()]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run()
