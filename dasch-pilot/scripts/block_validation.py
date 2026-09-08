"""Separate, bracketed long-event development and prospective real-event holdout."""
import argparse
import json
import statistics
import zipfile
from collections import defaultdict

import real_controls as rc
from colour_validation import joined, old, select_twelve
from m0_extension import select_source, summarize, table

BASE = rc.BASE
OUT = BASE / "data/block-validation-20260908"
SPEC = BASE / "BLOCK-VALIDATION-SPEC-2026-09-08.md"
CONTROL = BASE / "data/colour-quarantine-20260907"
HOLDOUT = {"name": "J075731.1+201735", "ra_deg": 119.37958333333333,
           "dec_deg": 20.293055555555558}
GRID = [(y, length) for length in (10, 20, 40) for y in range(1880, 1991-length, 5)]


def contract():
    return {**rc.contract(), **{p.name: rc.sha(p.read_bytes().replace(b"\r\n", b"\n"))
                              for p in (SPEC, BASE / "scripts/block_validation.py")}}


def block(rows, start, duration):
    end = start+duration
    before, after = defaultdict(list), defaultdict(list)
    for r in rows:
        if r["year"] < start-1:
            before[r["series"]].append(r)
        elif r["year"] >= end+1:
            after[r["series"]].append(r)
    residuals, years = defaultdict(list), []
    missing_before = missing_after = missing_years = 0
    for r in rows:
        if not start <= r["year"] < end:
            continue
        left = [m for m in before[r["series"]] if abs(m["ct"]-r["ct"]) <= .10]
        right = [m for m in after[r["series"]] if abs(m["ct"]-r["ct"]) <= .10]
        if len(left) < 10:
            missing_before += 1
        if len(right) < 10:
            missing_after += 1
        if min(len(left), len(right)) < 10:
            continue
        for side in (left, right):
            side.sort(key=lambda m: (abs(m["ct"]-r["ct"]), m["jd"]))
        baseline = left[:25]+right[:25]
        if len({int(m["year"]) for m in baseline}) < 5:
            missing_years += 1
            continue
        residuals[r["series"]].append(r["mag"]-statistics.median(m["mag"] for m in baseline))
        years.append(r["year"])
    medians = {s: statistics.median(v) for s, v in residuals.items() if len(v) >= 5}
    eligible = len(years) >= 10 and max(years, default=0)-min(years, default=0) >= 1 and len(medians) >= 2
    return {"start": start, "duration": duration, "matched_n": len(years),
            "series_n": {s: len(v) for s, v in residuals.items()}, "series_medians": medians,
            "missing_before": missing_before, "missing_after": missing_after, "missing_years": missing_years,
            "eligible": eligible, "positive_flag": eligible and sum(v >= .5 for v in medians.values()) >= 2,
            "negative_flag": eligible and sum(v <= -.5 for v in medians.values()) >= 2}


def analyse(source, rows, exposures):
    census = summarize(rows, int(source["num_matches"]), source)
    rc.unique_imaging_keys(rows)
    data, accounting = joined(rows, exposures, quarantine=True)
    span = max((r["year"] for r in data), default=0)-min((r["year"] for r in data), default=0)
    blocks = [block(data, start, duration) for start, duration in GRID]
    coverage = (len(data) >= 100 and span >= 30
                and accounting["excluded"].get("exposure_conflict", 0) <= .02*accounting["clean"]
                and any(b["eligible"] for b in blocks))
    return data, {"source": source, "census": census, "accounting": accounting,
                  "span_years": span, "coverage_pass": coverage, "blocks": blocks}


def cached(directory, role):
    manifest = json.loads((directory / "provenance.json").read_bytes())
    record = manifest["artifacts"][role]
    with zipfile.ZipFile(directory / "responses.zip") as z:
        raw = z.read(role+".raw")
    if rc.sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
        raise ValueError("cached validation bytes changed")
    return raw


def development():
    giants, standards = [], []
    archive = rc.Archive(replay=True)
    for i, target in enumerate(rc.TARGETS):
        pos = {k: target[k] for k in ("ra_deg", "dec_deg")}
        source = select_source(table(archive.fetch(f"{i}-catalogue", "querycat", {
            "refcat": "apass", **pos, "radius_arcsec": 30})), target)
        if source is None:
            raise ValueError("development control lost unique match")
        rows = table(archive.fetch(f"{i}-lightcurve", "lightcurve", {"refcat": "apass",
                     "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])}))
        exps = table(archive.fetch(f"{i}-exposures", "queryexps", pos))
        _, result = analyse(source, rows, exps)
        credited = (i in (1, 2) and result["coverage_pass"] and any(
            b["positive_flag"] and 1930 <= b["start"] and b["start"]+b["duration"] <= 1955
            for b in result["blocks"]))
        giants.append({**target, **result, "development_event_recovered": credited})
    for target in [s for s in select_twelve(old("table3")) if s["spss_id"] in (44, 113, 116, 120)]:
        sid = str(target["spss_id"])
        source = select_source(table(cached(CONTROL, sid+"-querycat")), target)
        if source is None:
            raise ValueError("instrumental control lost unique match")
        data, result = analyse(source, table(cached(CONTROL, sid+"-lightcurve")),
                               table(cached(CONTROL, sid+"-exposures")))
        injections = []
        for start in (1930, 1950):
            for sign in (-1, 1):
                altered = [{**r, "mag": r["mag"]+(sign if start <= r["year"] < start+20 else 0)} for r in data]
                injections.append({"injected_mag": sign, **block(altered, start, 20)})
        standards.append({**target, **result, "injections": injections})
    eligible = [b for s in standards for b in s["injections"] if b["eligible"]]
    recovered = sum(b["positive_flag"] if b["injected_mag"] > 0 else b["negative_flag"] for b in eligible)
    stars = sum(any(b["eligible"] for b in s["injections"]) for s in standards)
    flags = sum(b["positive_flag"] or b["negative_flag"] for s in standards for b in s["blocks"])
    dev_recovered = sum(g["development_event_recovered"] for g in giants)
    passed = (dev_recovered >= 1 and all(s["coverage_pass"] for s in standards)
              and flags == 0 and len(eligible) >= 6 and stars >= 3 and recovered >= .8*len(eligible))
    return {"contract": contract(), "giants_development_only": giants, "reused_instrumental_controls": standards,
            "development_events_recovered": dev_recovered, "instrumental_flagged_blocks": flags,
            "eligible_signed_injections": len(eligible), "injection_stars": stars, "injections_recovered": recovered,
            "gate": "PASS_BLOCK_DEVELOPMENT_ONLY" if passed else "STOP_BLOCK_DEVELOPMENT",
            "discovery_claim": False}


class HoldoutArchive(rc.Archive):
    def __init__(self, replay=False):
        self.directory, self.replay = OUT / "holdout", replay
        self.path = self.directory / "provenance.json"
        if not replay:
            self.directory.mkdir(parents=True, exist_ok=True)
        self.manifest = json.loads(self.path.read_bytes()) if self.path.exists() else {
            "contract": contract(), "max_attempts": 3, "attempts": [], "artifacts": {}}
        if self.manifest["contract"] != contract():
            raise ValueError("frozen block contract changed")

    def fetch(self, role, endpoint, body):
        if role not in self.manifest["artifacts"] and len(self.manifest["attempts"]) >= 3:
            raise ValueError("three-attempt holdout budget exhausted")
        return super().fetch(role, endpoint, body)


def holdout(replay=False):
    dev = json.loads((OUT / "development.json").read_bytes())
    if dev["contract"] != contract() or dev["gate"] != "PASS_BLOCK_DEVELOPMENT_ONLY":
        raise ValueError("development did not pass; holdout acquisition forbidden")
    fetch = HoldoutArchive(replay=replay).fetch
    pos = {k: HOLDOUT[k] for k in ("ra_deg", "dec_deg")}
    source = select_source(table(fetch("catalogue", "querycat", {"refcat": "apass", **pos, "radius_arcsec": 30})), pos)
    result = {"unique_match": source is not None}
    recovered = False
    if source is not None:
        rows = table(fetch("lightcurve", "lightcurve", {"refcat": "apass",
                     "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])}))
        exposures = table(fetch("exposures", "queryexps", pos))
        _, measured = analyse(source, rows, exposures)
        result.update(measured)
        recovered = measured["coverage_pass"] and any(
            b["negative_flag"] and b["duration"] == 10 and b["start"] in (1940, 1945)
            for b in measured["blocks"])
    return {"contract": contract(), **HOLDOUT, **result, "real_event_recovered": recovered,
            "gate": "PASS_BLOCK_TRANSFER_ONLY" if recovered else "STOP_BLOCK_HOLDOUT", "discovery_claim": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("development", "holdout"))
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    result = development() if args.phase == "development" else holdout(args.replay)
    destination = OUT / (args.phase+".json")
    if args.replay:
        if result != json.loads(destination.read_bytes()):
            raise ValueError("block cold replay differs")
        print(f"Block {args.phase} cold replay PASS")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if not isinstance(v, (list, dict))}, indent=2))


if __name__ == "__main__":
    main()
