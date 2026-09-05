"""Bounded, counts-only TNS-miner source diagnostics; never a science census.

Eight serial GETs test the Fink blocker and the documented ALeRCE alternative.
Exact response bodies stay in a new ignored data/probes directory. No candidate
IDs, coordinates, or response bodies are printed. The summary cannot seal or
resume a scientific campaign and makes no claim about all-class completeness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import atomic_write, sha256_file, validated_tag
from m2_pool import (
    ALERCE,
    FINK_CLASSES,
    FINK_LATESTS,
    _validated_taxonomy,
    mjd_to_ut,
)
from tnscommon import ROOT, session


def probe_plan(t0: float, t1: float, as_of_mjd: float) -> list[dict]:
    if not all(math.isfinite(value) for value in (t0, t1)) or t1 - t0 != 3:
        raise ValueError("probe window must be exactly three finite MJD days")
    if not math.isfinite(as_of_mjd) or as_of_mjd < t1:
        raise ValueError("alternative enumeration ceiling must cover the alert window")

    def latest(label, cls, start, stop, n):
        return {
            "label": label,
            "url": FINK_LATESTS,
            "params": {
                "class": cls,
                "n": n,
                "startdate": mjd_to_ut(start),
                "stopdate": mjd_to_ut(stop),
                "columns": "i:jd",
            },
            "mjd_bounds": [start, stop],
            "kind": "latest",
        }

    common = {
        "ndet": 2,
        "page": 1,
        "page_size": 1,
        "count": "true",
        "order_by": "oid",
        "order_mode": "ASC",
    }
    return [
        {"label": "taxonomy", "url": FINK_CLASSES, "params": {}, "kind": "taxonomy"},
        latest("em_full_1000", "Em*", t0, t1, 1000),
        latest("em_full_1", "Em*", t0, t1, 1),
        latest("em_16sec_1", "Em*", t0, t0 + 16 / 86400, 1),
        latest("cv_control_1", "CataclyV*", t0, t1, 1),
        {
            "label": "alerce_firstmjd_control",
            "url": ALERCE,
            "params": {**common, "firstmjd": [t0, t1]},
            "kind": "alerce",
        },
        {
            "label": "alerce_lastmjd_alternative",
            "url": ALERCE,
            "params": {**common, "lastmjd": [t0, as_of_mjd]},
            "kind": "alerce",
        },
        {
            "label": "alerce_lastmjd_no_count",
            "url": ALERCE,
            "params": {**common, "lastmjd": [t0, as_of_mjd], "count": "false"},
            "kind": "alerce",
        },
    ]


def public_shape(payload, probe: dict) -> dict:
    """Validate enough shape to distinguish an error from a diagnostic count."""
    kind = probe["kind"]
    if kind == "taxonomy":
        classes = _validated_taxonomy(payload)
        return {"required_classes": len(classes), "em_required": "Em*" in classes}
    if kind == "latest":
        if not isinstance(payload, list):
            raise TypeError("latest response is not a list")
        low, high = (value + 2400000.5 for value in probe["mjd_bounds"])
        for row in payload:
            if not isinstance(row, dict) or isinstance(row.get("i:jd"), bool):
                raise TypeError("latest row has no numeric JD")
            jd = float(row.get("i:jd", "nan"))
            # The API accepts whole seconds; cover only its serialization roundoff.
            if not math.isfinite(jd) or not low - 1e-8 <= jd <= high + 1e-8:
                raise ValueError("latest row lies outside the requested time window")
        return {
            "returned_rows": len(payload),
            "cap_bound": len(payload) >= probe["params"]["n"],
        }
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise TypeError("ALeRCE response has no items list")
    if probe["params"].get("count") == "false":
        return {"returned_rows": len(payload["items"]), "reported_total": None}
    total = payload.get("total")
    if isinstance(total, bool) or not isinstance(total, (int, float)):
        raise TypeError("ALeRCE response has no numeric total")
    if not math.isfinite(total) or total < 0 or int(total) != total:
        raise ValueError("ALeRCE response has invalid total")
    return {"returned_rows": len(payload["items"]), "reported_total": int(total)}


def alternative_plan(plan: list[dict]) -> list[dict]:
    """Three final documented query variants after the ordinary diagnostics."""
    post_probe = {**plan[2], "label": "em_post_full_1", "method": "POST"}
    ordered = []
    for count in ("true", "false"):
        ordered.append({
            **plan[-1],
            "label": f"alerce_lastmjd_ordered_count_{count}",
            "params": {**plan[-1]["params"], "order_by": "lastmjd", "order_mode": "DESC", "count": count},
        })
    return [post_probe, *ordered]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--mjd-end", type=float, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--only-alerce", action="store_true")
    selection.add_argument("--alternatives-only", action="store_true")
    args = parser.parse_args()
    tag = validated_tag(args.tag)
    now = datetime.now(timezone.utc)
    if args.mjd_end > now.timestamp() / 86400 + 40587:
        raise ValueError("probe window has not closed")
    plan = probe_plan(args.mjd_end - 3, args.mjd_end, now.timestamp() / 86400 + 40587)
    if args.only_alerce:
        plan = [probe for probe in plan if probe["kind"] == "alerce"]
    elif args.alternatives_only:
        plan = alternative_plan(plan)
    destination = ROOT / "data" / "probes" / tag
    destination.mkdir(parents=True, exist_ok=False)
    contract = {
        "schema_version": 1,
        "created_at_utc": now.isoformat(),
        "script_sha256": sha256_file(Path(__file__)),
        "requests": plan,
        "max_requests": len(plan),
        "timeout_connect_seconds": 10,
        "timeout_read_seconds": 30,
        "retries": 0,
        "candidate_processing": False,
    }
    atomic_write(destination / "contract.json", json.dumps(contract, indent=2).encode())
    atomic_write(destination / "probe_service_recovery.executed.py", Path(__file__).read_bytes())
    results = []
    with session() as client:
        for probe in plan:
            started = time.monotonic()
            entry = {"label": probe["label"], "started_at_utc": datetime.now(timezone.utc).isoformat()}
            try:
                method = probe.get("method", "GET")
                request_data = {"json" if method == "POST" else "params": probe["params"]}
                response = client.request(
                    method, probe["url"], **request_data, timeout=(10, 30), allow_redirects=False
                )
                raw_path = destination / f"{probe['label']}.response"
                atomic_write(raw_path, response.content)
                entry.update({
                    "http_status": response.status_code,
                    "raw_sha256": hashlib.sha256(response.content).hexdigest(),
                    "raw_bytes": len(response.content),
                })
                if response.status_code == 200:
                    try:
                        entry.update(public_shape(response.json(), probe))
                        entry["validated"] = True
                    except (ValueError, RuntimeError, TypeError):
                        entry.update({"validated": False, "error": "invalid_response_shape"})
                else:
                    entry.update({"validated": False, "error": "non_200_response"})
            except requests.RequestException as exc:
                entry.update({"validated": False, "error": type(exc).__name__})
            entry["elapsed_seconds"] = round(time.monotonic() - started, 3)
            results.append(entry)
            atomic_write(destination / "results.json", json.dumps(results, indent=2).encode())
            print(json.dumps(entry, sort_keys=True), flush=True)
    manifest = {
        "files": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in sorted(destination.iterdir()) if path.is_file()
        ],
        "science_campaign_complete": False,
        "candidate_count": None,
    }
    atomic_write(destination / "manifest.json", json.dumps(manifest, indent=2).encode())
    print(json.dumps({"manifest_sha256": sha256_file(destination / "manifest.json")}))


if __name__ == "__main__":
    main()
