"""Independent known-star geometry in a separately frozen retrospective pilot."""
import argparse
import hashlib
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from pilot import TRUE_KEYS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/stars-20260907"
OUT = ROOT / "results/stars-20260907"


def fetch(role, url, cap):
    RAW.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    path = OUT / "provenance.json"
    spec = hashlib.sha256((ROOT / "STARS-SPEC-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    manifest = json.loads(path.read_bytes()) if path.exists() else {"spec_sha256": spec, "artifacts": {}}
    if manifest["spec_sha256"] != spec:
        raise ValueError("spec changed")
    if role in manifest["artifacts"]:
        raw = (RAW / role).read_bytes()
        record = manifest["artifacts"][role]
        if record["url"] != url or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("source changed")
        return raw
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    started = datetime.now(timezone.utc).isoformat()
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read(cap+1)
        if response.status != 200 or len(raw) > cap:
            raise ValueError("bad or oversized response")
    (RAW / role).write_bytes(raw)
    manifest["artifacts"][role] = {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "retrieved_utc": started}
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return raw


def catalogue(raw):
    lines = [line for line in raw.decode().splitlines() if line.strip() and not line.startswith("#")]
    if not lines or "HIP" not in lines[0].split("\t"):
        raise ValueError("unexpected catalogue schema")
    keys = [k.strip() for k in lines[0].split("\t")]
    result = []
    for line in lines[3:]:
        values = [v.strip() for v in line.split("\t")]
        if len(values) != len(keys):
            raise ValueError("truncated catalogue row")
        row = dict(zip(keys, values, strict=True))
        if any(not row.get(k) for k in ("HIP", "Vmag", "RAICRS", "DEICRS", "pmRA", "pmDE")):
            continue
        result.append({k: float(row[k]) for k in ("HIP", "Vmag", "RAICRS", "DEICRS", "pmRA", "pmDE")})
    if not result or len(result) >= 1000 or len({r["HIP"] for r in result}) != len(result):
        raise ValueError("empty, truncated or duplicate catalogue")
    return result


def predict(star, header):
    dt = Time(header["DATE-AVG"], scale="utc").jyear-1991.25
    dec = star["DEICRS"]+dt*star["pmDE"]/3600000
    ra = star["RAICRS"]+dt*star["pmRA"]/3600000/np.cos(np.deg2rad(star["DEICRS"]))
    return WCS(header, key="A").all_world2pix([[ra, dec]], 0)[0]


def measure(data, mask, prediction):
    yy, xx = np.indices(data.shape)
    radius = np.hypot(xx-prediction[0], yy-prediction[1])
    valid = np.isfinite(data) & (mask == 0)
    ann = (radius >= 12) & (radius <= 18)
    if (valid & ann).sum() < .8*ann.sum():
        return {"ok": False, "reason": "annular_mask"}
    bg = np.median(data[valid & ann])
    scale = 1.4826*np.median(np.abs(data[valid & ann]-bg))
    support = valid & (radius <= 6)
    if not support.any() or not np.isfinite(scale) or scale <= 0:
        return {"ok": False, "reason": "no_support_or_scale"}
    py, px = np.unravel_index(np.argmax(np.where(support, data, -np.inf)), data.shape)
    contrast = float((data[py, px]-bg)/scale)
    aperture = np.hypot(xx-px, yy-py) <= 2.5
    if contrast < 5 or not valid[aperture].all():
        return {"ok": False, "reason": "contrast_or_source_mask", "contrast": contrast}
    weights = np.where(aperture, np.maximum(data-bg, 0), 0)
    weights = np.nan_to_num(weights)
    if weights.sum() <= 0:
        return {"ok": False, "reason": "no_flux"}
    center = np.array([(weights*xx).sum(), (weights*yy).sum()])/weights.sum()
    return {"ok": bool(np.linalg.norm(center-prediction) <= 6), "centroid": center.tolist(), "contrast": contrast}


def assess(measurements):
    frames = []
    for rows in measurements:
        train = [np.array(r["centroid"])-r["prediction"] for r in rows[:4] if r["ok"]]
        hold = [np.array(r["centroid"])-r["prediction"] for r in rows[4:] if r["ok"]]
        shift = np.median(train, axis=0) if train else np.array([0., 0.])
        residual = [float(np.linalg.norm(v-shift)) for v in hold]
        rms = float(np.sqrt(np.mean(np.square(residual)))) if residual else None
        passed = len(train) >= 3 and len(hold) >= 3 and np.linalg.norm(shift) <= 5 and rms <= 2 and max(residual) <= 3
        frames.append({"training_recovered": len(train), "heldout_recovered": len(hold),
                       "translation": shift.tolist(), "heldout_residuals": residual, "rms": rms, "passed": bool(passed)})
    return {"frames": frames, "gate": "PASS_COARSE_STAR_GEOMETRY" if len(frames) == 4 and all(f["passed"] for f in frames) else "STOP_STAR_GEOMETRY",
            "comet_confirmed": False, "reporter_mapping_resolved": False}


def run():
    records = json.loads((ROOT / "results/retrospective-preflight-20260906.json").read_bytes())["records"]
    headers = [fits.Header.fromstring(r["header_cards_ascii"][1], sep="") for r in records]
    params = {"-source": "I/239/hip_main", "-out": "HIP,Vmag,RAICRS,DEICRS,pmRA,pmDE", "-out.max": "1000",
              "RAICRS": "150..170", "DEICRS": "-2..18", "Vmag": "<=7"}
    raw = fetch("hip.tsv", "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?"+urllib.parse.urlencode(params), 2*1024**2)
    stars = []
    for star in sorted(catalogue(raw), key=lambda s: (s["Vmag"], s["HIP"])):
        positions = [predict(star, h) for h in headers]
        if all(50 <= p[0] < 1998 and 50 <= p[1] < 1870 and 180 <= np.linalg.norm(p-np.array([h["CRPIX1"]-1, h["CRPIX2"]-1])) <= 800 for p, h in zip(positions, headers, strict=True)):
            stars.append({**star, "positions": [p.tolist() for p in positions]})
    stars = stars[:8]
    (OUT / "selection.json").write_text(json.dumps(stars, indent=2), encoding="utf-8")
    if len(stars) < 8:
        raise ValueError(f"STOP_STAR_SELECTION: {len(stars)} stars")
    measurements, arrays = [], {}
    for i, record in enumerate(records):
        raw = fetch(f"frame{i}.fits", record["acquisition"]["url"], 12*1024**2)
        if hashlib.sha256(raw[:65536]).hexdigest() != record["acquisition"]["sha256"]:
            raise ValueError("header prefix changed")
        with fits.open(io.BytesIO(raw)) as hdus:
            hdus.verify("exception")
            h = hdus[1].header
            if (len(hdus) != 3 or any(h.get(k) is not True for k in TRUE_KEYS)
                    or any(h.get(k) != 0 for k in ("BADBLK_N", "MISBLK_N"))
                    or any(abs(h[k]) >= 7 for k in ("SHIFT_X", "SHIFT_Y"))):
                raise ValueError("quality header failure")
            data, mask = hdus[1].data, hdus[2].data
            if data.shape != (1920, 2048) or mask.shape != data.shape or mask.dtype.kind not in "iu":
                raise ValueError("shape or PQF type")
            rows = []
            for j, star in enumerate(stars):
                position = np.array(star["positions"][i])
                origin = np.rint(position).astype(int)-20
                x, y = origin
                patch, pqf = data[y:y+41, x:x+41].copy(), mask[y:y+41, x:x+41].copy()
                local = position-origin
                arrays[f"data_{i}_{j}"] = patch
                arrays[f"mask_{i}_{j}"] = pqf
                arrays[f"prediction_{i}_{j}"] = local
                result = measure(patch, pqf, local)
                negatives = []
                for dx, dy in ((-32, 0), (32, 0), (0, -32), (0, 32)):
                    other = data[y+dy:y+dy+41, x+dx:x+dx+41]
                    other_mask = mask[y+dy:y+dy+41, x+dx:x+dx+41]
                    negatives.append(measure(other, other_mask, local))
                rows.append({**result, "prediction": local.tolist(), "negatives": negatives})
            measurements.append(rows)
    np.savez_compressed(OUT / "known-star-cutouts.npz", **arrays)
    result = {**assess(measurements), "measurements": measurements}
    with (OUT / "results.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "measurements"}, indent=2))


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
