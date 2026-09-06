"""Bounded independent SPSS-label feasibility; never claims century-scale truth."""
import argparse
import hashlib
import json
import statistics
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from m0_extension import API, clean, decimal_year, select_source, summarize, table

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "data/stable-20260906"
SPEC = BASE / "STABLE-SPEC-2026-09-06.md"
CAP = 16 * 1024**2


def select(raw, normalize_missing=False):
    stars = []
    for line in raw.decode().splitlines():
        if not line.strip():
            continue
        if len(line) < 104:
            raise ValueError("short catalogue row")
        dec = (int(line[41:43]) + int(line[44:46])/60 + float(line[47:52])/3600)
        dec *= -1 if line[40] == "-" else 1
        if (line[96:104].strip() != "Accepted" or not 0 <= dec <= 60
                or line[77:79].strip() != "<=" or float(line[79:85]) > .010
                or line[105:].strip() not in (("", "---") if normalize_missing else ("",))):
            continue
        ra = 15 * (int(line[28:30]) + int(line[31:33])/60 + float(line[34:39])/3600)
        stars.append({"spss_id": int(line[:3]), "name": line[4:27].strip(),
                      "ra_deg": ra, "dec_deg": dec, "amp_upper_mag": float(line[79:85])})
    if len({s["spss_id"] for s in stars}) != len(stars):
        raise ValueError("duplicated catalogue identities")
    return sorted(stars, key=lambda x: x["spss_id"])[:6]


def excursions(rows):
    good = clean(rows)
    if not good:
        return {"eligible_years": 0, "flagged_years": []}
    baseline = statistics.median(float(r["magcal_magdep"]) for r in good)
    years = defaultdict(list)
    for r in good:
        years[int(decimal_year(float(r["date_jd"])))].append(float(r["magcal_magdep"]))
    usable = {y: m for y, m in years.items() if len(m) >= 5}
    return {"eligible_years": len(usable), "flagged_years": [
        {"year": y, "n": len(m), "median_minus_baseline_mag": statistics.median(m)-baseline}
        for y, m in sorted(usable.items()) if abs(statistics.median(m)-baseline) >= .5]}


def execute(fetch, normalize_missing=False):
    stars = select(fetch("table3", "https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/462/3616/table3.dat"), normalize_missing)
    fetch("readme", "https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/462/3616/ReadMe")
    results = []
    for star in stars:
        key = str(star["spss_id"])
        cat = table(fetch(key + "-querycat", API + "querycat", {
            "refcat": "apass", "ra_deg": star["ra_deg"], "dec_deg": star["dec_deg"], "radius_arcsec": 30}))
        source = select_source(cat, star)
        result = {**star, "unique_match": source is not None, "useful_coverage": False}
        if source is not None:
            rows = table(fetch(key + "-lightcurve", API + "lightcurve", {
                "refcat": "apass", "ref_number": int(source["ref_number"]),
                "gsc_bin_index": int(source["gsc_bin_index"])}))
            summary = summarize(rows, int(source["num_matches"]), source)
            # summarize is the unchanged M0 quality/accounting code. Its variable
            # label is deliberately not propagated to independently stable controls.
            summary.pop("coverage_verdict")
            summary.pop("access_gate")
            result.update(summary=summary, excursions=excursions(rows),
                          useful_coverage=summary["clean_detections"] >= 100 and summary["clean_span_years"] >= 30)
        results.append(result)
    useful = sum(r["useful_coverage"] for r in results)
    return {"controls": results, "selected": len(stars), "useful_coverage": useful,
            "coverage_gate": "PASS_FEASIBILITY_ONLY" if useful >= 4 else "STOP_COVERAGE",
            "century_scale_false_positive_rate_measured": False,
            "blind_search_authorized": False}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--normalize-missing-notes", action="store_true")
    args = parser.parse_args()
    if args.normalize_missing_notes:
        OUT = BASE / "data/stable-normalized-20260906"
    spec_hash = hashlib.sha256(SPEC.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    amendment_hash = hashlib.sha256((BASE / "STABLE-PARSER-AMENDMENT-2026-09-06.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    manifest_path = OUT / "provenance.json"
    if args.replay:
        manifest = json.loads(manifest_path.read_bytes())
        if manifest["spec_sha256"] != spec_hash:
            raise ValueError("spec changed")
        if args.normalize_missing_notes and manifest.get("amendment_sha256") != amendment_hash:
            raise ValueError("amendment changed")
        archive = zipfile.ZipFile(OUT / "responses.zip")

        def fetch(role, url, body=None):
            record = manifest["artifacts"][role]
            if record["url"] != url or record["body"] != body:
                raise ValueError("request changed")
            if archive.getinfo(role + ".raw").file_size > CAP:
                raise ValueError("oversize source")
            raw = archive.read(role + ".raw")
            if hashlib.sha256(raw).hexdigest() != record["sha256"] or len(raw) != record["bytes"]:
                raise ValueError("source changed")
            return raw
        result = execute(fetch, args.normalize_missing_notes)
        if result != json.loads((OUT / "results.json").read_bytes()):
            raise ValueError("replay differs")
        print("Cold replay PASS")
    else:
        OUT.mkdir(exist_ok=False)
        manifest = {"spec_sha256": spec_hash, "max_requests": 14, "artifacts": {}}
        if args.normalize_missing_notes:
            manifest["amendment_sha256"] = amendment_hash

        def fetch(role, url, body=None):
            if len(manifest["artifacts"]) >= 14:
                raise ValueError("request budget exhausted")
            req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "astronomy-known-control/1.0"})
            started = datetime.now(timezone.utc).isoformat()
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(CAP+1)
                if len(raw) > CAP:
                    raise ValueError("response exceeds cap")
                record = {"url": url, "body": body, "status": response.status,
                          "retrieved_utc": started, "bytes": len(raw),
                          "sha256": hashlib.sha256(raw).hexdigest()}
            (OUT / (role + ".raw")).write_bytes(raw)
            manifest["artifacts"][role] = record
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"Retrieved {role}: {len(raw)} bytes", flush=True)
            return raw
        result = execute(fetch, args.normalize_missing_notes)
        (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        with zipfile.ZipFile(OUT / "responses.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for role in manifest["artifacts"]:
                archive.write(OUT / (role + ".raw"), role + ".raw")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
