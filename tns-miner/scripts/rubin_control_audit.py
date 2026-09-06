"""Cold-replay aggregate audit of public Rubin controls; no network calls."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unique(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("measurement IDs must remain exact integers")
        if value in result:
            raise ValueError("duplicate measurement ID")
        result[value] = row
    return result


def run(bundle):
    with zipfile.ZipFile(bundle) as z:
        def read(folder, name):
            info = z.getinfo(folder + "/" + name)
            if info.file_size > 16 * 1024**2:
                raise ValueError("oversize input")
            return z.read(info)
        folders = ["20260905_rubin_metadata", "20260905_rubin_access", "20260905_rubin_tap",
                   "20260906_rubin_followup", "20260906_rubin_recovery"]
        manifests = {}
        for folder in folders:
            raw = read(folder, "manifest.json")
            manifests[folder] = hashlib.sha256(raw).hexdigest()
            manifest = json.loads(raw)
            for item in manifest["files"]:
                payload = read(folder, item["name"])
                if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
                    raise ValueError("mutated input: " + item["name"])
        def data(folder, name):
            return json.loads(read(folder, name + ".response"))
        def tap(name):
            d = data("20260905_rubin_tap", name)
            cols = [c["name"] for c in d["columns"]]
            return [dict(zip(cols, r)) for r in d["data"] if r[0] == 313761043604045880]
        old = unique(data(folders[0], "fink_documented_sources"), "r:diaSourceId")
        fresh = unique(data(folders[3], "sources_all_columns"), "r:diaSourceId")
        af = unique(tap("known_detections"), "measurement_id")
        ff = unique(data(folders[3], "forced_all_columns"), "r:diaForcedSourceId")
        ap = unique(tap("known_forced"), "measurement_id")
        extra = sorted(set(af) - set(fresh))
        extra_fp = sorted(set(ap) - set(ff))
        if set(old) != set(fresh) or set(fresh) - set(af) or set(ff) - set(ap):
            raise ValueError("control set changed unexpectedly")
        if any(fresh[k]["r:psfFlux"] != af[k]["psfflux"] for k in fresh):
            raise ValueError("shared detection flux changed")
        counts = {}
        for label in ("Z_Cha", "HL_CMa"):
            fink = data(folders[4], label)
            alerce = data(folders[3], label + "_alerce")
            counts[label] = {"fink_returned_rows": len(fink), "alerce_object_count": alerce["data"][0][0]}
        return {"manifests_sha256": manifests, "fink_detections": len(fresh),
                "alerce_detections": len(af), "extra_detection_ids": extra,
                "extra_detection_mjd_tai_range": [min(af[k]["mjd"] for k in extra), max(af[k]["mjd"] for k in extra)],
                "fink_forced": len(ff), "alerce_forced": len(ap), "extra_forced_ids": extra_fp,
                "extra_forced_mjd_tai_range": [min(ap[k]["mjd"] for k in extra_fp), max(ap[k]["mjd"] for k in extra_fp)],
                "all_columns_query_recovers_missing_rows": False,
                "shared_detection_flux_max_difference_njy": 0,
                "timestamp_lookup_shared_control_rows": len(data(folders[3], "shared_epoch")),
                "timestamp_lookup_missing_rows": len(data(folders[3], "missing_epoch")),
                "new_public_cv_cones": counts,
                "discrepancy_cause": "UNRESOLVED_UPSTREAM_OR_STORAGE_NOT_ESTABLISHED",
                "population_coverage_proved": False, "unknown_search_authorized": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "research/rubin-controls-20260906.zip")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = json.dumps(run(args.bundle), indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(result)
    print(result)
