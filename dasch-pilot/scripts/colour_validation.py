"""Frozen matched-colour holdout experiment; raw responses support cold replay."""
import argparse
import hashlib
import json
import math
import statistics
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from m0_extension import API, clean, decimal_year, select_source, summarize, table

BASE = Path(__file__).resolve().parents[1]
SPEC = BASE / "CALIBRATION-SPEC-2026-09-07.md"
OUT = BASE / "data/colour-20260907"
OLD = BASE / "data/stable-normalized-20260906"
CAP = 16 * 1024**2


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def old(role):
    manifest = json.loads((OLD / "provenance.json").read_bytes())
    with zipfile.ZipFile(OLD / "responses.zip") as z:
        raw = z.read(role + ".raw")
    if digest(raw) != manifest["artifacts"][role]["sha256"]:
        raise ValueError("old response changed")
    return raw


def select_twelve(raw):
    stars = []
    for line in raw.decode().splitlines():
        dec = int(line[41:43]) + int(line[44:46])/60 + float(line[47:52])/3600
        dec *= -1 if line[40] == "-" else 1
        if (line[96:104].strip() != "Accepted" or not 0 <= dec <= 60
                or line[77:79].strip() != "<=" or float(line[79:85]) > .010
                or line[105:].strip() not in ("", "---")):
            continue
        stars.append({"spss_id": int(line[:3]), "name": line[4:27].strip(),
                      "ra_deg": 15*(int(line[28:30])+int(line[31:33])/60+float(line[34:39])/3600),
                      "dec_deg": dec})
    return sorted(stars, key=lambda r: r["spss_id"])[:12]


def joined(rows, exposures, quarantine=False):
    index = {}
    for e in exposures:
        if e["mosnum"] == "" or e["solnum"] == "" or int(e["solnum"]) < 0:
            continue
        key = (e["series"], int(e["platenum"]), int(e["mosnum"]), int(e["solnum"]))
        if key in index and index[key] != e:
            raise ValueError("conflicting exposure identity")
        index[key] = e
    result, excluded = [], defaultdict(int)
    good = clean(rows)
    for r in good:
        key = (r["series"], int(r["plate_number"]), int(r["mosaic_number"]), int(r["solution_number"]))
        e = index.get(key)
        if e is None:
            excluded["no_exposure"] += 1
            continue
        if (e["expnum"] not in ("", "-1") and r["exposure_number"] not in ("", "-1")
                and int(e["expnum"]) != int(r["exposure_number"])):
            if not quarantine:
                raise ValueError("exposure number disagrees")
            excluded["exposure_conflict"] += 1
            continue
        try:
            ct = float(e["median_colorterm_apass"])
        except ValueError:
            excluded["missing_colour"] += 1
            continue
        if not math.isfinite(ct):
            excluded["missing_colour"] += 1
            continue
        result.append({"series": r["series"], "year": decimal_year(float(r["date_jd"])),
                       "jd": float(r["date_jd"]), "mag": float(r["magcal_magdep"]), "ct": ct})
    return result, {"clean": len(good), "joined": len(result), "excluded": dict(excluded)}


def window(rows, start, injection=0):
    inside = [r for r in rows if start <= r["year"] < start+5]
    outside = defaultdict(list)
    for r in rows:
        if r["year"] < start-1 or r["year"] >= start+6:
            outside[r["series"]].append(r)
    residuals = defaultdict(list)
    years = []
    for r in inside:
        matches = [m for m in outside[r["series"]] if abs(m["ct"]-r["ct"]) <= .10]
        matches.sort(key=lambda m: (abs(m["ct"]-r["ct"]), m["jd"]))
        matches = matches[:50]
        if len(matches) < 20 or len({int(m["year"]) for m in matches}) < 5:
            continue
        residuals[r["series"]].append(r["mag"]+injection-statistics.median(m["mag"] for m in matches))
        years.append(r["year"])
    eligible_series = {s: statistics.median(v) for s, v in residuals.items() if len(v) >= 5}
    eligible = len(years) >= 10 and max(years, default=0)-min(years, default=0) >= 1 and len(eligible_series) >= 2
    pos = sum(m >= .5 for m in eligible_series.values()) >= 2
    neg = sum(m <= -.5 for m in eligible_series.values()) >= 2
    return {"start": start, "matched_n": len(years), "series_n": {s: len(v) for s, v in residuals.items()},
            "series_medians": eligible_series, "eligible": eligible,
            "positive_flag": eligible and pos, "negative_flag": eligible and neg}


class Responses:
    def __init__(self, replay=False, quarantine=False):
        self.replay = replay
        self.hash = digest(SPEC.read_bytes().replace(b"\r\n", b"\n"))
        self.path = OUT / "provenance.json"
        OUT.mkdir(exist_ok=True)
        self.manifest = json.loads(self.path.read_bytes()) if self.path.exists() else {
            "spec_sha256": self.hash, "max_requests": 24, "artifacts": {}}
        if self.manifest["spec_sha256"] != self.hash:
            raise ValueError("spec changed")
        if quarantine:
            amendment = digest((BASE / "CALIBRATION-JOIN-AMENDMENT-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n"))
            if self.manifest.get("amendment_sha256", amendment) != amendment:
                raise ValueError("amendment changed")
            self.manifest["amendment_sha256"] = amendment

    def fetch(self, role, endpoint, body):
        url = API + endpoint
        records = self.manifest["artifacts"]
        if role == "11-exposures" and OUT.name == "colour-quarantine-20260907" and role not in records:
            source = BASE / "data/colour-20260907"
            record = json.loads((source / "provenance.json").read_bytes())["artifacts"][role]
            with zipfile.ZipFile(source / "responses.zip") as z:
                raw = z.read(role + ".raw")
            if digest(raw) != record["sha256"] or record["url"] != url or record["body"] != body:
                raise ValueError("original acquisition changed")
            if self.replay:
                raise ValueError("missing replay record")
            with zipfile.ZipFile(OUT / "responses.zip", "a", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr(role + ".raw", raw)
            records[role] = {**record, "reused_from_strict_run": True}
            self.path.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        if role in records:
            record = records[role]
            if record["url"] != url or record["body"] != body:
                raise ValueError("request changed")
            with zipfile.ZipFile(OUT / "responses.zip") as z:
                raw = z.read(role + ".raw")
            if digest(raw) != record["sha256"] or len(raw) != record["bytes"]:
                raise ValueError("response changed")
            return raw
        if self.replay or len(records) >= 24:
            raise ValueError("request not available or budget exhausted")
        self.path.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "astronomy-control/1.0"})
        started = datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read(CAP+1)
            if len(raw) > CAP:
                raise ValueError("response cap exceeded")
            status = response.status
        with zipfile.ZipFile(OUT / "responses.zip", "a", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(role + ".raw", raw)
        records[role] = {"url": url, "body": body, "status": status, "retrieved_utc": started,
                         "bytes": len(raw), "sha256": digest(raw)}
        self.path.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        print(f"Retrieved {role}: {len(raw)} bytes", flush=True)
        return raw


def execute(fetch, quarantine=False):
    results = []
    for i, star in enumerate(select_twelve(old("table3"))):
        sid = str(star["spss_id"])
        development = i < 6
        catraw = old(sid+"-querycat") if development else fetch(sid+"-querycat", "querycat", {
            "refcat": "apass", "ra_deg": star["ra_deg"], "dec_deg": star["dec_deg"], "radius_arcsec": 30})
        source = select_source(table(catraw), star)
        result = {**star, "development": development, "unique_match": source is not None}
        if source is not None:
            raw = old(sid+"-lightcurve") if development else fetch(sid+"-lightcurve", "lightcurve", {
                "refcat": "apass", "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])})
            rows = table(raw)
            summarize(rows, int(source["num_matches"]), source)
            exps = table(fetch(sid+"-exposures", "queryexps", {"ra_deg": star["ra_deg"], "dec_deg": star["dec_deg"]}))
            data, account = joined(rows, exps, quarantine)
            span = max((r["year"] for r in data), default=0)-min((r["year"] for r in data), default=0)
            result.update(accounting=account, span=span, useful_coverage=len(data) >= 100 and span >= 30,
                          windows=[window(data, y) for y in range(1880, 1990, 5)])
            if not development:
                result["injections"] = [{**window(data, y, sign), "injected_mag": sign} for y in (1930, 1950, 1970) for sign in (-1, 1)]
        results.append(result)
    holdout = [r for r in results if not r["development"]]
    injections = [w for r in holdout for w in r.get("injections", []) if w["eligible"]]
    recovered = sum(w["positive_flag"] if w["injected_mag"] > 0 else w["negative_flag"] for w in injections)
    flags = [{"spss_id": r["spss_id"], **w} for r in holdout for w in r.get("windows", []) if w["positive_flag"] or w["negative_flag"]]
    nstars = sum(any(w["eligible"] for w in r.get("injections", [])) for r in holdout)
    coverage = sum(r.get("useful_coverage", False) for r in holdout)
    conflict_gate = all(r.get("accounting", {}).get("excluded", {}).get("exposure_conflict", 0)
                        <= .02*r.get("accounting", {}).get("clean", 0) for r in results)
    passed = coverage >= 4 and nstars >= 3 and len(injections) >= 6 and recovered >= .8*len(injections) and not flags and conflict_gate
    return {"controls": results, "heldout_useful": coverage, "injection_stars": nstars,
            "eligible_signed_injections": len(injections), "recovered": recovered, "heldout_flags": flags,
            "gate": "PASS_EXPLORATORY_SCREEN_ONLY" if passed else "STOP_CALIBRATION_GATE",
            "conflict_gate": conflict_gate, "quarantine_variant": quarantine,
            "century_negative_truth": False, "discovery_claim": False}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--quarantine-conflicts", action="store_true")
    args = parser.parse_args()
    if args.quarantine_conflicts:
        OUT = BASE / "data/colour-quarantine-20260907"
    result = execute(Responses(args.replay, args.quarantine_conflicts).fetch, args.quarantine_conflicts)
    path = OUT / "results.json"
    if args.replay:
        if result != json.loads(path.read_bytes()):
            raise ValueError("replay differs")
        print("Cold replay PASS")
    else:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "controls"}, indent=2))


if __name__ == "__main__":
    main()
