"""A fixed 64-source exploratory screen; identities remain local and ignored."""
import argparse
import hashlib
import json
import math
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from colour_validation import joined, old, select_twelve, window
from m0_extension import API, angular_sep_arcsec, summarize, table

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "data/search-20260907"
CONTROL = BASE / "data/colour-quarantine-20260907"
CAP = 16*1024**2


def select_sources(rows, center):
    chosen = []
    for r in rows:
        values = [float(r[k]) if r[k] else float("nan") for k in ("stdmag", "color", "ra_deg", "dec_deg")]
        mag, color, ra, dec = values
        if (all(map(math.isfinite, values)) and 9 <= mag <= 13.5 and -.3 <= color <= 1.5
                and int(r["num_matches"]) >= 500 and r["v_flag"] == "0" and r["mag_flag"] == "0"
                and angular_sep_arcsec(center["ra_deg"], center["dec_deg"], ra, dec) > 30):
            chosen.append(r)
    if len({r["ref_number"] for r in chosen}) != len(chosen):
        raise ValueError("duplicate source identities")
    return sorted(chosen, key=lambda r: int(r["ref_number"]))[:32]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    gate = json.loads((CONTROL / "results.json").read_bytes())
    if gate["gate"] != "PASS_EXPLORATORY_SCREEN_ONLY":
        raise ValueError("control gate not passed")
    OUT.mkdir(exist_ok=True)
    spec = hashlib.sha256((BASE / "SEARCH-SPEC-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    path = OUT / "provenance.json"
    manifest = json.loads(path.read_bytes()) if path.exists() else {"spec_sha256": spec, "artifacts": {}}
    if manifest["spec_sha256"] != spec:
        raise ValueError("spec changed")

    def fetch(role, endpoint, body):
        url = API+endpoint
        if role in manifest["artifacts"]:
            record = manifest["artifacts"][role]
            raw = (OUT / (role+".raw")).read_bytes()
            if record["url"] != url or record["body"] != body or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError("changed request or response")
            return raw
        if len(manifest["artifacts"]) >= 66:
            raise ValueError("request budget exhausted")
        if args.replay:
            raise ValueError("missing replay source; no network allowed")
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "astronomy-exploratory/1.0"})
        started = datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read(CAP+1)
            if response.status != 200 or len(raw) > CAP:
                raise ValueError("bad or oversized response")
        (OUT / (role+".raw")).write_bytes(raw)
        manifest["artifacts"][role] = {"url": url, "body": body, "bytes": len(raw),
                                       "sha256": hashlib.sha256(raw).hexdigest(), "retrieved_utc": started}
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return raw

    details = []
    for star in [s for s in select_twelve(old("table3")) if s["spss_id"] in (11, 120)]:
        sid = str(star["spss_id"])
        rows = table(fetch(sid+"-field", "querycat", {"refcat": "apass", "ra_deg": star["ra_deg"], "dec_deg": star["dec_deg"], "radius_arcsec": 1800}))
        chosen = select_sources(rows, star)
        with zipfile.ZipFile(CONTROL / "responses.zip") as z:
            raw = z.read(sid+"-exposures.raw")
        cm = json.loads((CONTROL / "provenance.json").read_bytes())
        if hashlib.sha256(raw).hexdigest() != cm["artifacts"][sid+"-exposures"]["sha256"]:
            raise ValueError("exposure cache changed")
        exps = table(raw)
        print(f"Field {sid}: {len(chosen)} targets selected", flush=True)
        for i, source in enumerate(chosen):
            rows = table(fetch(f"{sid}-{i:02d}", "lightcurve", {"refcat": "apass", "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])}))
            summarize(rows, int(source["num_matches"]), source)
            data, account = joined(rows, exps, quarantine=True)
            span = max((r["year"] for r in data), default=0)-min((r["year"] for r in data), default=0)
            windows = [window(data, y) for y in range(1880, 1990, 5)]
            eligible = len(data) >= 100 and span >= 30 and account["excluded"].get("exposure_conflict", 0) <= .02*account["clean"] and any(w["eligible"] for w in windows)
            flags = [w for w in windows if w["positive_flag"] or w["negative_flag"]]
            details.append({"field": sid, "source": source, "accounting": account, "span": span,
                            "eligible": eligible, "windows": windows, "lead": eligible and bool(flags)})
            if not args.replay:
                (OUT / "partial-results.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
            print(f"Completed {len(details)} selected curves", flush=True)
    result = {"spec_sha256": spec, "selected": len(details), "eligible": sum(r["eligible"] for r in details),
              "eligible_windows": sum(w["eligible"] for r in details if r["eligible"] for w in r["windows"]),
              "local_leads": sum(r["lead"] for r in details), "discovery_claim": False,
              "identity_outputs_private": True, "requests": len(manifest["artifacts"])}
    destination = BASE / "data/search-summary-20260907.json"
    if args.replay:
        if result != json.loads(destination.read_bytes()) or details != json.loads((OUT / "partial-results.json").read_bytes()):
            raise ValueError("replay differs")
        print("Local private-source cold replay PASS")
    else:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
