"""Fixed paired-aperture depth test; never a known-stream recovery claim."""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/depth-20260907"
OUT = ROOT / "results/depth-20260907"
BITS = sum(1 << b for b in (0, 1, 3, 6, 10, 11, 12, 13))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def acquire():
    RAW.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    path = OUT / "provenance.json"
    spec = hashlib.sha256((ROOT / "DEPTH-SPEC-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    manifest = json.loads(path.read_bytes()) if path.exists() else {"spec_sha256": spec, "artifacts": {}}
    if manifest["spec_sha256"] != spec:
        raise ValueError("spec changed")
    for release in ("dr10", "dr11"):
        for product in ("image-r", "invvar-r", "maskbits"):
            role = release+"-"+product+".fits.fz"
            dest = RAW / role
            url = f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/{release}/south/coadd/030/0306m510/legacysurvey-0306m510-{product}.fits.fz"
            if role in manifest["artifacts"]:
                if digest(dest) != manifest["artifacts"][role]["sha256"]:
                    raise ValueError("source changed")
                continue
            path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            started = datetime.now(timezone.utc).isoformat()
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = response.read(80*1024**2+1)
                if response.status != 200 or len(raw) > 80*1024**2:
                    raise ValueError("source status or cap")
            dest.write_bytes(raw)
            manifest["artifacts"][role] = {"url": url, "bytes": len(raw), "sha256": digest(dest), "retrieved_utc": started}
            path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"Retrieved {role}: {len(raw)} bytes", flush=True)


def summary(pairs):
    result = {"paired_apertures": len(pairs), "releases": {}}
    for release in ("dr10", "dr11"):
        values = np.array([p[release]["mean_nmgy_arcsec2"] for p in pairs])
        median = float(np.median(values)) if len(values) else None
        scatter = float(1.4826*np.median(np.abs(values-median))) if len(values) else None
        limit = float(22.5-2.5*np.log10(3*scatter)) if scatter and scatter > 0 else None
        result["releases"][release] = {"median": median, "scatter": scatter, "three_scatter_sb_mag_arcsec2": limit}
    a, b = (result["releases"][k]["scatter"] for k in ("dr10", "dr11"))
    ratio = b/a if a and b else None
    result.update(scatter_ratio=ratio, gate="PASS_LOCAL_DEPTH_ONLY" if len(pairs) >= 30 and ratio is not None and ratio <= .9 else "STOP_NO_MATERIAL_DEPTH_GAIN",
                  stream_recovery_measured=False, discovery_claim=False)
    return result


def measure(replay=False):
    manifest = json.loads((OUT / "provenance.json").read_bytes())
    for role, record in manifest["artifacts"].items():
        if digest(RAW / role) != record["sha256"]:
            raise ValueError("source changed")
    data, headers = {}, []
    for release in ("dr10", "dr11"):
        data[release] = {}
        for product in ("image-r", "invvar-r", "maskbits"):
            with fits.open(RAW / (release+"-"+product+".fits.fz")) as hdus:
                hdu = next(h for h in hdus if h.data is not None and h.data.shape == (3600, 3600))
                data[release][product] = hdu.data.copy()
                headers.append(hdu.header.copy())
    locations = np.array([[0, 0], [3599, 0], [0, 3599], [3599, 3599], [1800, 1800]])
    ref = WCS(headers[0]).all_pix2world(locations, 0)
    for h in headers:
        if np.max(np.abs(WCS(h).all_pix2world(locations, 0)-ref)) > 1e-6:
            raise ValueError("different image grids")
    if headers[0].get("BUNIT", "").strip().lower() not in ("nanomaggy", "nanomaggies") or headers[3].get("BUNIT", "").strip().lower() not in ("nanomaggy", "nanomaggies"):
        raise ValueError("unexpected image units")
    wcs = WCS(headers[0])
    host = wcs.all_world2pix([[30.6285, -50.9319]], 0)[0]
    scale = np.sqrt(abs(np.linalg.det(wcs.pixel_scale_matrix)))*3600
    if not np.isclose(scale, .262, rtol=1e-5):
        raise ValueError("unexpected pixel scale")
    pairs, considered = [], 0
    for y in range(0, 3600-37, 38):
        for x in range(0, 3600-37, 38):
            distance = np.linalg.norm(np.array([x+18.5, y+18.5])-host)*scale
            if not 180 <= distance <= 360:
                continue
            considered += 1
            pair = {"x": x, "y": y}
            for release, products in data.items():
                image = products["image-r"][y:y+38, x:x+38]
                ivar = products["invvar-r"][y:y+38, x:x+38]
                mask = products["maskbits"][y:y+38, x:x+38]
                if not (np.isfinite(image).all() and np.isfinite(ivar).all() and (ivar > 0).all() and ((mask & BITS) == 0).all()):
                    break
                pair[release] = {"mean_nmgy_arcsec2": float(image.mean(dtype=np.float64)/scale**2),
                                 "formal_error": float(np.sqrt((1/ivar.astype(float)).sum())/image.size/scale**2)}
            if "dr10" in pair and "dr11" in pair:
                pairs.append(pair)
    result = {**summary(pairs), "considered_apertures": considered, "pairs": pairs}
    if replay:
        if result != json.loads((OUT / "results.json").read_bytes()):
            raise ValueError("pixel replay differs")
        print("Full-pixel depth replay PASS")
    else:
        with (OUT / "results.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "pairs"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    if not args.replay:
        acquire()
    measure(args.replay)
