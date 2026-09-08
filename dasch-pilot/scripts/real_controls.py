"""Prospective real-event transfer test of the unchanged September 7 detector."""
import argparse
import hashlib
import json
import math
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from colour_validation import joined, window
from m0_extension import API, clean, select_source, summarize, table

BASE = Path(__file__).resolve().parents[1]
SPEC = BASE / "REAL-CONTROLS-SPEC-2026-09-08.md"
OUT = BASE / "data/real-controls-20260908"
CAP = 16 * 1024**2
TARGETS = (
    {"name": "J083038.5+140713", "ra_deg": 127.66041666666666,
     "dec_deg": 14.120277777777778, "starts": [1965, 1970, 1975, 1980, 1985]},
    {"name": "J075445.9+164141", "ra_deg": 118.69125,
     "dec_deg": 16.69472222222222, "starts": [1930, 1935]},
    {"name": "J073606.5+211411", "ra_deg": 114.02708333333334,
     "dec_deg": 21.23638888888889, "starts": [1930, 1935, 1940, 1945, 1950]},
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def contract():
    paths = [SPEC, *(BASE / "scripts" / name for name in (
        "real_controls.py", "colour_validation.py", "m0_extension.py", "m0_dasch_pilot.py"))]
    return {p.name: sha(p.read_bytes().replace(b"\r\n", b"\n")) for p in paths}


class Archive:
    def __init__(self, directory=OUT, replay=False):
        self.directory, self.replay = directory, replay
        self.path = directory / "provenance.json"
        if not replay:
            directory.mkdir(parents=True, exist_ok=True)
        self.manifest = json.loads(self.path.read_bytes()) if self.path.exists() else {
            "contract": contract(), "max_attempts": 9, "attempts": [], "artifacts": {}}
        if self.manifest["contract"] != contract():
            raise ValueError("frozen protocol or analysis code changed")

    def save(self):
        self.path.write_text(json.dumps(self.manifest, indent=2)+"\n", encoding="utf-8")

    def fetch(self, role, endpoint, body):
        url = API+endpoint
        records = self.manifest["artifacts"]
        if role in records:
            record = records[role]
            with zipfile.ZipFile(self.directory / "responses.zip") as bundle:
                raw = bundle.read(role+".raw")
            if (record["url"] != url or record["body"] != body
                    or record["sha256"] != sha(raw) or record["bytes"] != len(raw)):
                raise ValueError("cached request or bytes changed")
            return raw
        if self.replay:
            raise ValueError("missing replay response; network forbidden")
        if any(a["role"] == role for a in self.manifest["attempts"]):
            raise ValueError("previous incomplete/failed attempt; no automatic retry")
        if len(self.manifest["attempts"]) >= 9:
            raise ValueError("request attempt budget exhausted")
        time.sleep(1)
        attempt = {"role": role, "url": url, "body": body,
                   "started_utc": datetime.now(timezone.utc).isoformat(), "state": "STARTED"}
        self.manifest["attempts"].append(attempt)
        self.save()
        request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
            "Content-Type": "application/json", "User-Agent": "astronomy-known-control/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(CAP+1)
                if response.status != 200 or len(raw) > CAP:
                    raise ValueError("bad or oversized response")
            table(raw)  # Reject malformed/empty responses before calling acquisition successful.
            with zipfile.ZipFile(self.directory / "responses.zip", "a", zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr(role+".raw", raw)
            records[role] = {"url": url, "body": body, "sha256": sha(raw), "bytes": len(raw),
                             "retrieved_utc": attempt["started_utc"]}
            attempt["state"] = "SUCCESS"
        except Exception as exc:
            attempt.update(state="FAILED", error_type=type(exc).__name__)
            self.save()
            raise
        self.save()
        print(f"Retrieved {role}: {len(raw)} bytes", flush=True)
        return raw


def catalogue_rejections(source):
    reasons = []
    for name, low, high in (("stdmag", 9, 13.5), ("color", -.3, 1.5)):
        value = float(source[name]) if source[name] else float("nan")
        if not math.isfinite(value) or not low <= value <= high:
            reasons.append(name)
    if int(source["num_matches"]) < 500:
        reasons.append("num_matches")
    for name in ("v_flag", "mag_flag"):
        if source[name] != "0":
            reasons.append(name)
    return reasons


def unique_imaging_keys(rows):
    keys = [(r["series"], int(r["plate_number"]), int(r["mosaic_number"]),
             int(r["solution_number"])) for r in clean(rows)]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate clean imaging key")


def evaluate(target, source, rows, exposures):
    census = summarize(rows, int(source["num_matches"]), source)
    unique_imaging_keys(rows)
    data, accounting = joined(rows, exposures, quarantine=True)
    span = max((r["year"] for r in data), default=0)-min((r["year"] for r in data), default=0)
    windows = [window(data, y) for y in range(1880, 1990, 5)]
    coverage = (len(data) >= 100 and span >= 30
                and accounting["excluded"].get("exposure_conflict", 0) <= .02*accounting["clean"]
                and any(w["eligible"] for w in windows))
    event = [w for w in windows if w["start"] in target["starts"]]
    recovered = coverage and any(w["positive_flag"] for w in event)
    reasons = catalogue_rejections(source)
    injections = []
    for start, duration in ((1950, 5), (1930, 20), (1950, 20)):
        altered = [{**r, "mag": r["mag"]+(1. if start <= r["year"] < start+duration else 0.)}
                   for r in data]
        injections.append({"start": start, "duration": duration, "amplitude_mag": 1.,
                           "windows": [window(altered, y) for y in range(start, start+duration, 5)]})
    return {**target, "unique_match": True, "source": source, "census": census,
            "accounting": accounting, "joined_span_years": span, "coverage_pass": coverage,
            "catalogue_rejections": reasons, "windows": windows,
            "eligible_event_windows": sum(w["eligible"] for w in event),
            "recovered_event_diagnostic": recovered,
            "recovered_by_full_selection": recovered and not reasons, "injections": injections}


def execute(fetch):
    controls = []
    for i, target in enumerate(TARGETS):
        position = {k: target[k] for k in ("ra_deg", "dec_deg")}
        source = select_source(table(fetch(f"{i}-catalogue", "querycat", {
            "refcat": "apass", **position, "radius_arcsec": 30})), target)
        if source is None:
            controls.append({**target, "unique_match": False, "recovered_by_full_selection": False})
            continue
        rows = table(fetch(f"{i}-lightcurve", "lightcurve", {"refcat": "apass",
                     "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])}))
        exposures = table(fetch(f"{i}-exposures", "queryexps", position))
        controls.append(evaluate(target, source, rows, exposures))
        print(f"Completed known control {i+1}/3", flush=True)
    recovered = sum(c["recovered_by_full_selection"] for c in controls)
    return {"contract": contract(), "selected_controls": 3, "controls": controls,
            "recovered_by_full_selection": recovered,
            "gate": "PASS_REAL_EVENT_TRANSFER_ONLY" if recovered >= 2 else "STOP_REAL_EVENT_TRANSFER",
            "discovery_claim": False, "population_completeness_claim": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    result = execute(Archive(replay=args.replay).fetch)
    destination = OUT / "results.json"
    if args.replay:
        if result != json.loads(destination.read_bytes()):
            raise ValueError("cold replay differs")
        print("Real-event cold replay PASS")
    else:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("controls", "contract")}, indent=2))


if __name__ == "__main__":
    main()
