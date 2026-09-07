"""Prospective all-brick metadata screen, before galaxy selection or image access."""
import argparse
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/footprint-20260907"
META = ROOT / "results/footprint-provenance-20260907.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    spec = hashlib.sha256((ROOT / "FOOTPRINT-SPEC-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    manifest = json.loads(META.read_bytes()) if META.exists() else {"spec_sha256": spec, "artifacts": {}}
    if manifest["spec_sha256"] != spec:
        raise ValueError("spec changed")
    for release in ("dr10", "dr11"):
        path = RAW / (release + ".fits.gz")
        url = f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/{release}/south/survey-bricks-{release}-south.fits.gz"
        if release in manifest["artifacts"]:
            if sha(path) != manifest["artifacts"][release]["sha256"]:
                raise ValueError("source changed")
            continue
        META.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.monotonic()
        n = 0
        with urllib.request.urlopen(url, timeout=30) as response, path.open("xb") as stream:
            if response.status != 200:
                raise ValueError("unexpected response status")
            while block := response.read(1024**2):
                n += len(block)
                if n > 160*1024**2 or time.monotonic()-t0 > 600:
                    raise ValueError("download cap")
                stream.write(block)
        manifest["artifacts"][release] = {"url": url, "bytes": n, "sha256": sha(path), "retrieved_utc": started}
        META.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Retrieved {release}: {n} bytes", flush=True)


def screen(replay=False):
    manifest = json.loads(META.read_bytes())
    tables = {}
    for release in ("dr10", "dr11"):
        path = RAW / (release + ".fits.gz")
        if sha(path) != manifest["artifacts"][release]["sha256"]:
            raise ValueError("source changed")
        with fits.open(path) as hdus:
            rows = hdus[1].data
            tables[release] = {str(r["brickname"]): (float(r["ra"]), float(r["dec"]), int(r["nexp_r"]), bool(r["survey_primary"])) for r in rows}
            if len(tables[release]) != len(rows):
                raise ValueError("duplicate brick names")
    old, new = tables["dr10"], tables["dr11"]
    common = old.keys() & new.keys()
    selected = [{"brick": k, "ra": new[k][0], "dec": new[k][1], "old_r": old[k][2], "new_r": new[k][2]}
                for k in sorted(common) if old[k][3] and new[k][3] and old[k][2] >= 1
                and new[k][2] >= old[k][2]+3 and new[k][2] >= 1.5*old[k][2]]
    result = {"common_bricks": len(common), "old_only": len(old.keys()-new.keys()),
              "new_only": len(new.keys()-old.keys()), "qualifying": len(selected), "first_twenty": selected[:20],
              "image_depth_measured": False, "spec_sha256": manifest["spec_sha256"]}
    out = ROOT / "results/footprint-20260907.json"
    if replay:
        if result != json.loads(out.read_bytes()):
            raise ValueError("footprint replay differs")
        with np.load(ROOT / "evidence/footprint-20260907.npz", allow_pickle=False) as z:
            np.testing.assert_array_equal(z["brick"], [r["brick"] for r in selected])
            np.testing.assert_array_equal(z["values"], [[r[k] for k in ("ra", "dec", "old_r", "new_r")] for r in selected])
        print("Full-source footprint replay PASS")
        return
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
    np.savez_compressed(ROOT / "evidence/footprint-20260907.npz",
                        brick=np.array([r["brick"] for r in selected]),
                        values=np.array([[r[k] for k in ("ra", "dec", "old_r", "new_r")] for r in selected]))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    if args.fetch and args.replay:
        parser.error("replay must not use network")
    if args.fetch:
        acquire()
    screen(args.replay)
