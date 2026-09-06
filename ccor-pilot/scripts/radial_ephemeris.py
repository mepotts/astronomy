"""Independent coarse radial unit diagnostic; no image-plane access."""
import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[1]
DIGEST = "f8e2a5e881a9b2561d925c78e8a7629c1e68bd582f8778d337a7005ad45151af"


def epoch(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()


def parse(raw):
    meta, rows = {}, []
    for line in raw.decode("ascii").splitlines():
        if "=" in line:
            key, value = (v.strip() for v in line.split("=", 1))
            if key != "COMMENT" and key in meta:
                raise ValueError("multiple metadata blocks are not supported")
            meta[key] = value
        elif line.startswith("20"):
            parts = line.split()
            if len(parts) != 7:
                raise ValueError("unexpected state row")
            rows.append([epoch(parts[0]), *map(float, parts[1:])])
    expected = {"OBJECT_NAME": "SWFO", "CENTER_NAME": "EARTH", "REF_FRAME": "EME2000",
                "TIME_SYSTEM": "UTC", "INTERPOLATION": "LAGRANGE", "INTERPOLATION_DEGREE": "7"}
    if any(meta.get(k) != v for k, v in expected.items()):
        raise ValueError("unsupported object/frame/time/interpolation")
    a = np.asarray(rows)
    if len(a) < 8 or not np.isfinite(a).all() or not np.all(np.diff(a[:, 0]) > 0):
        raise ValueError("invalid or unordered ephemeris")
    return meta, a


def interpolate(rows, time):
    if time < rows[0, 0] or time > rows[-1, 0]:
        raise ValueError("no extrapolation")
    start = min(max(int(np.searchsorted(rows[:, 0], time))-4, 0), len(rows)-8)
    nodes = rows[start:start+8]
    offsets = (nodes[:, 0]-time)/600
    weights = np.ones(8)
    for j in range(8):
        for k in range(8):
            if j != k:
                weights[j] *= -offsets[k]/(offsets[j]-offsets[k])
    return weights @ nodes[:, 1:4]


def run():
    import astropy.units as u
    from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
    from astropy.time import Time
    with zipfile.ZipFile(BASE / "results/solar1-ephemeris-20260906.zip") as z:
        if z.getinfo("solar1.oem").file_size > 8*1024**2:
            raise ValueError("oversize OEM")
        raw = z.read("solar1.oem")
    if hashlib.sha256(raw).hexdigest() != DIGEST:
        raise ValueError("OEM hash mismatch")
    meta, rows = parse(raw)
    source = BASE / "results/retrospective-preflight-20260906.json"
    records = json.loads(source.read_bytes())["records"]
    result = []
    for record in records:
        h = record["headers"][1]
        t = Time(h["DATE-OBS"], scale="utc")
        geocentric = interpolate(rows, epoch(h["DATE-OBS"]))
        with solar_system_ephemeris.set("builtin"):
            earth = (get_body_barycentric("earth", t) - get_body_barycentric("sun", t)).xyz.to_value(u.km)
        distance = float(np.linalg.norm(earth + geocentric))
        hee = float(np.linalg.norm([h[k] for k in ("HEEX_OBS", "HEEY_OBS", "HEEZ_OBS")]))
        comparisons = {"dsun_as_m": float(h["DSUN_OBS"])/1000, "hee_as_m": hee/1000, "hee_as_km": hee}
        errors = {k: abs(v-distance)/distance for k, v in comparisons.items()}
        result.append({"utc": h["DATE-OBS"], "independent_distance_km": distance,
                       "header_distance_km": comparisons, "relative_errors": errors})
    supported = len(result) == 4 and all(r["relative_errors"]["dsun_as_m"] < .01
        and r["relative_errors"]["hee_as_km"] < .01 and r["relative_errors"]["hee_as_m"] > .9 for r in result)
    return {"status": "SUPPORTS_KM_INTERPRETATION" if supported else "UNRESOLVED",
            "oem_sha256": DIGEST, "metadata": meta, "samples": len(rows), "results": result,
            "headers_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "wcs_validated": False, "images_decompressed": 0, "official_metadata_corrected": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = json.dumps(run(), indent=2, allow_nan=False) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(result)
    print(result)
