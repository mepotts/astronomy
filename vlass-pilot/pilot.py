"""Bounded, known-control-only VLASS archive and photometry experiment."""

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TARGET = (174.2757916666667, -3.6270277777778)
CAMPAIGNS = ("VLASS1.1", "VLASS2.1", "VLASS3.1", "VLASS4.1")
CAP = 250_000_000
TAP = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/argus/sync"
SODA = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def request_worker(url, destination, limit):
    """One request; caller enforces wall-clock deadline; no silent partial input."""
    request = urllib.request.Request(url, headers={"User-Agent": "astronomy-control-pilot/1"})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise ValueError(f"HTTP status {response.status}")
        content = bytearray()
        while block := response.read(min(1024 * 1024, limit + 1 - len(content))):
            content.extend(block)
            if len(content) > limit:
                raise ValueError("request exceeds remaining acquisition cap")
        destination.write_bytes(content)
        print(json.dumps({"url": url, "final_url": response.url,
                          "status": response.status, "bytes": len(content),
                          "headers": dict(response.headers), "sha256": sha(destination)}))


def get(url, name, limit=2_000_000):
    destination = DATA / name
    if destination.exists():
        raise ValueError(f"Refusing to overwrite raw input {name}")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "_request", url,
         str(destination), str(limit)], capture_output=True, text=True, timeout=75,
        check=True,
    )
    record = json.loads(result.stdout)
    record["path"] = str(destination.relative_to(ROOT))
    return record


def links(xml):
    root = ET.fromstring(xml)
    table = root.find(".//{*}TABLE")
    fields = [field.attrib["name"] for field in table.findall("{*}FIELD")]
    return [dict(zip(fields, [(cell.text or "") for cell in row]))
            for row in table.findall(".//{*}TR")]


def fetch(followup=False):
    global DATA
    if followup:
        DATA = ROOT / "data" / "followup"
    DATA.mkdir(exist_ok=True, parents=True)
    protocol_name = "FOLLOWUP-PROTOCOL.md" if followup else "PROTOCOL.md"
    initial_bytes = json.loads((ROOT / "acquisition.json").read_text())["stored_bytes"] if followup else 0
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(),
                "protocol_sha256": sha(ROOT / protocol_name), "protocol_file": protocol_name,
                "prior_acquisition_bytes": initial_bytes,
                "target_degrees": TARGET, "records": [], "epochs": [],
                "outcome": "INCOMPLETE"}
    manifest_path = ROOT / ("acquisition-followup.json" if followup else "acquisition.json")
    if manifest_path.exists():
        raise ValueError("Existing acquisition: do not overwrite or redownload")
    save(manifest_path, manifest)
    try:
        query = ("SELECT TOP 12 obs_id,t_min,t_max,access_url FROM ivoa.ObsCore "
                 "WHERE obs_collection='VLASS' AND "
                 f"INTERSECTS(s_region,CIRCLE('ICRS',{TARGET[0]},{TARGET[1]},0.001))=1")
        meta = get(TAP + "?" + urllib.parse.urlencode(
            {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}),
            "coverage.csv")
        manifest["records"].append(meta)
        rows = list(csv.DictReader(io.StringIO((ROOT / meta["path"]).read_text())))
        for campaign in (CAMPAIGNS[1:] if followup else CAMPAIGNS):
            selected = [row for row in rows if row["obs_id"].startswith(campaign + ".")
                        and row["access_url"].endswith(".quicklook")]
            if len(selected) != 1:
                raise ValueError(f"{campaign}: expected one unique QL plane, got {len(selected)}")
            row = selected[0]
            entry = {**row, "campaign": campaign}
            manifest["epochs"].append(entry)
            receipt = get(row["access_url"], campaign + "-datalink.xml")
            manifest["records"].append(receipt)
            products = links((ROOT / receipt["path"]).read_bytes())
            image = [p for p in products if p["semantics"] == "#this"
                     and p["content_type"] == "application/fits"]
            rms = [p for p in products if p["semantics"] == "#auxiliary"
                   and ".rms." in p["access_url"] and p["content_type"] == "application/fits"]
            if len(image) != 1 or len(rms) != 1:
                raise ValueError(f"{campaign}: non-unique/missing science or RMS image")
            for kind, product in (("image", image[0]), ("rms", rms[0])):
                identifier = urllib.parse.unquote(product["access_url"].split("/files/", 1)[1])
                if campaign == "VLASS1.1" and ".v2." not in identifier:
                    raise ValueError("QL1.1 is not corrected v2; stop before its pixels")
                remaining = CAP - initial_bytes - sum(record["bytes"] for record in manifest["records"])
                url = SODA + "?" + urllib.parse.urlencode(
                    {"ID": identifier, "CIRCLE": f"{TARGET[0]} {TARGET[1]} 0.2"})
                receipt = get(url, campaign + "-" + kind + ".fits", remaining)
                receipt.update({"kind": kind, "campaign": campaign, "artifact": identifier})
                manifest["records"].append(receipt)
                entry[kind] = receipt["path"]
                save(manifest_path, manifest)
                print(campaign, kind, receipt["bytes"], flush=True)
        manifest["outcome"] = "ACQUIRED"
    except Exception as error:
        manifest["outcome"] = "STOP_ACQUISITION"
        manifest["error"] = str(error)
        raise
    finally:
        manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["stored_bytes"] = sum(record["bytes"] for record in manifest["records"])
        save(manifest_path, manifest)


def validate_header(header, campaign):
    unit = str(header.get("BUNIT", "")).strip().lower()
    if unit != "jy/beam":
        raise ValueError("BUNIT must be Jy/beam")
    for key in ("BMAJ", "BMIN"):
        if not math.isfinite(float(header.get(key, float("nan")))) or header[key] <= 0:
            raise ValueError(f"Missing/nonpositive beam {key}")
    if header["BMIN"] > header["BMAJ"]:
        raise ValueError("BMIN exceeds BMAJ")
    if not math.isfinite(float(header.get("BPA", float("nan")))):
        raise ValueError("Missing/nonfinite beam angle")
    if not header.get("DATE-OBS"):
        raise ValueError("Missing DATE-OBS")
    if not campaign.startswith("VLASS"):
        raise ValueError("Invalid campaign")
    if campaign not in str(header):
        raise ValueError("Expected campaign absent from FITS provenance")


def recover():
    """Explicitly authorized one-time retry of only the failed epoch-4 RMS request."""
    global DATA
    DATA = ROOT / "data" / "followup"
    source = ROOT / "acquisition-followup.json"
    destination = ROOT / "acquisition-recovered.json"
    if destination.exists():
        raise ValueError("One retry already attempted; no retry loop")
    manifest = json.loads(source.read_text())
    if manifest["outcome"] != "STOP_ACQUISITION" or "timed out after 75" not in manifest["error"]:
        raise ValueError("Not the approved timeout state")
    if (DATA / "VLASS4.1-rms.fits").exists():
        raise ValueError("Unexpected original file exists; preserve and inspect")
    manifest["recovery"] = {"source_manifest_sha256": sha(source),
                            "authorization": "parent-approved single identical transport retry",
                            "started_utc": datetime.now(timezone.utc).isoformat()}
    manifest["outcome"] = "INCOMPLETE_RECOVERY"
    save(destination, manifest)
    try:
        entry = next(ep for ep in manifest["epochs"] if ep["campaign"] == "VLASS4.1")
        products = links((DATA / "VLASS4.1-datalink.xml").read_bytes())
        rms = [p for p in products if p["semantics"] == "#auxiliary"
               and ".rms." in p["access_url"] and p["content_type"] == "application/fits"]
        if len(rms) != 1:
            raise ValueError("Original RMS link is not unique")
        identifier = urllib.parse.unquote(rms[0]["access_url"].split("/files/", 1)[1])
        url = SODA + "?" + urllib.parse.urlencode(
            {"ID": identifier, "CIRCLE": f"{TARGET[0]} {TARGET[1]} 0.2"})
        remaining = CAP - manifest["stored_bytes"] - manifest["prior_acquisition_bytes"]
        receipt = get(url, "VLASS4.1-rms-attempt2.fits", remaining)
        receipt.update({"kind": "rms", "campaign": "VLASS4.1", "artifact": identifier,
                        "attempt": 2})
        manifest["records"].append(receipt)
        entry["rms"] = receipt["path"]
        manifest["outcome"] = "ACQUIRED"
    except Exception as error:
        manifest["outcome"] = "STOP_RECOVERY"
        manifest["recovery"]["error"] = str(error)
        raise
    finally:
        manifest["recovery"]["completed_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["stored_bytes"] = sum(record["bytes"] for record in manifest["records"])
        save(destination, manifest)
    print(manifest["outcome"], manifest["stored_bytes"])


def amplitude(values, template, background):
    """Fixed-position least-squares amplitude; no independent-pixel noise claim."""
    import numpy as np

    denominator = float(np.sum(template * template))
    if denominator <= 0:
        raise ValueError("Empty template")
    return float(np.sum((values - background) * template) / denominator)


def load_epoch(entry):
    import numpy as np
    from astropy.io import fits
    from astropy.time import Time
    from astropy.wcs import WCS

    with fits.open(ROOT / entry["image"], memmap=False) as hdus:
        array = np.squeeze(hdus[0].data).astype(float)
        header = hdus[0].header.copy()
    with fits.open(ROOT / entry["rms"], memmap=False) as hdus:
        rms = np.squeeze(hdus[0].data).astype(float)
        rh = hdus[0].header.copy()
    validate_header(header, entry["campaign"])
    validate_header(rh, entry["campaign"])
    for key in ("BMAJ", "BMIN", "BPA", "DATE-OBS", "OBJECT"):
        if header.get(key) != rh.get(key):
            raise ValueError(f"Science/RMS identity differs: {key}")
    if header.get("OBJECT") != entry["obs_id"].rsplit(".", 1)[-1]:
        raise ValueError("FITS OBJECT contradicts archive observation ID")
    if any(tile in entry["obs_id"] for tile in (
        "T01t03", "T01t43", "T02t47", "T04t28", "T04t34", "T05t07",
        "T06t01", "T06t11", "T06t31")) and entry["campaign"] == "VLASS4.1":
        raise ValueError("Epoch-4 RFI-affected tile")
    if array.ndim != 2 or array.shape != rms.shape:
        raise ValueError("Science/RMS dimension mismatch")
    wcs = WCS(header).celestial
    rwcs = WCS(rh).celestial
    if wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2:
        raise ValueError("Expected celestial WCS")
    ys, xs = array.shape
    points = np.array([[0, 0], [xs - 1, 0], [0, ys - 1], [xs - 1, ys - 1],
                       [xs / 2, ys / 2]])
    mapped = rwcs.all_world2pix(wcs.all_pix2world(points, 0), 0)
    if not np.allclose(points, mapped, atol=1e-5, rtol=0):
        raise ValueError("Science/RMS WCS differs")
    finite = np.isfinite(array) & np.isfinite(rms) & (rms > 0)
    if np.mean(finite) < 0.95:
        raise ValueError("Less than 95% finite science/positive RMS")
    mjd = float(Time(header["DATE-OBS"]).mjd)
    if not float(entry["t_min"]) - 0.01 <= mjd <= float(entry["t_max"]) + 0.01:
        raise ValueError("Header observation date contradicts archive epoch")
    # CD matrix used to map pixel displacements into local tangent-plane angles.
    matrix = np.asarray(wcs.pixel_scale_matrix) * 3600
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-6:
        raise ValueError("Invalid pixel angular transform")
    return {"array": array, "rms": rms, "wcs": wcs, "header": header,
            "matrix": matrix, "finite_fraction": float(np.mean(finite)),
            "mjd": mjd, "campaign": entry["campaign"]}


def photometry(epoch, ra, dec):
    import numpy as np

    x, y = [float(v) for v in epoch["wcs"].all_world2pix(ra, dec, 0)]
    matrix = epoch["matrix"]
    minscale = float(np.min(np.linalg.svd(matrix)[1]))
    ny, nx = epoch["array"].shape
    if min(x, y, nx - 1 - x, ny - 1 - y) * minscale < 30:
        raise ValueError("Source does not have 30 arcsec edge clearance")
    radius = math.ceil(30 / minscale)
    ix, iy = round(x), round(y)
    if ix-radius < 0 or iy-radius < 0 or ix+radius >= nx or iy+radius >= ny:
        raise ValueError("Rounded fitting patch crosses image edge")
    yy, xx = np.mgrid[iy-radius:iy+radius+1, ix-radius:ix+radius+1]
    east, north = np.einsum("ij,jkl->ikl", matrix, np.array([xx-x, yy-y]))
    distance = np.hypot(east, north)
    values = epoch["array"][yy, xx]
    rms = epoch["rms"][yy, xx]
    annulus = (distance >= 15) & (distance <= 25)
    if not np.isfinite(values).all() or not np.isfinite(rms).all() or np.any(rms <= 0):
        raise ValueError("Nonfinite fitting/background patch or invalid RMS")
    background = float(np.median(values[annulus]))
    noise = max(float(np.median(rms)),
                float(1.4826 * np.median(np.abs(values[annulus] - background))))
    major = epoch["header"]["BMAJ"] * 3600
    minor = epoch["header"]["BMIN"] * 3600
    theta = np.radians(epoch["header"]["BPA"])
    u = east * np.sin(theta) + north * np.cos(theta)
    v = east * np.cos(theta) - north * np.sin(theta)
    template = np.exp(-4 * np.log(2) * ((u / major)**2 + (v / minor)**2))
    fit = distance <= 3 * major
    amp = amplitude(values[fit], template[fit], background)
    residual = float(np.sqrt(np.mean((values[fit] - background - amp*template[fit])**2)))
    peak_region = distance <= 3
    pi = np.unravel_index(np.argmax(np.where(peak_region, values, -np.inf)), values.shape)
    offset = float(distance[pi])
    return {"ra": ra, "dec": dec, "amplitude_jy": amp,
            "noise_proxy_jy": noise, "amplitude_over_noise": amp/noise,
            "background_jy_per_beam": background, "residual_over_noise": residual/noise,
            "peak_offset_arcsec": offset,
            "recovered": bool(amp/noise >= 5 and offset <= 1.5)}


def ensemble_positions(reference):
    import numpy as np
    from scipy.ndimage import maximum_filter

    array, rms = reference["array"], reference["rms"]
    scale = float(np.min(np.linalg.svd(reference["matrix"])[1]))
    local = maximum_filter(np.nan_to_num(array, nan=-np.inf), size=21)
    selected = (array == local) & (array/rms >= 15) & (array < .1)
    yy, xx = np.where(selected)
    order = np.argsort(array[yy, xx])[::-1]
    tx, ty = [float(v) for v in reference["wcs"].all_world2pix(*TARGET, 0)]
    points, pixels = [], []
    for i in order:
        x, y = int(xx[i]), int(yy[i])
        if min(x, y, array.shape[1]-1-x, array.shape[0]-1-y) * scale < 45:
            continue
        if math.hypot(x-tx, y-ty) * scale < 45:
            continue
        if any(math.hypot(x-px, y-py)*scale < 20 for px, py in pixels):
            continue
        ra, dec = [float(v) for v in reference["wcs"].all_pix2world(x, y, 0)]
        result = photometry(reference, ra, dec)
        if result["residual_over_noise"] > 3:
            continue
        points.append((ra, dec))
        pixels.append((x, y))
        if len(points) == 12:
            break
    return points


def measure(followup=False, replay=False):
    import astropy.units as u
    import numpy as np
    from astropy.coordinates import SkyCoord

    manifest_path = ROOT / ("acquisition-followup.json" if followup else "acquisition.json")
    if followup and (ROOT / "acquisition-recovered.json").exists():
        manifest_path = ROOT / "acquisition-recovered.json"
    report_path = ROOT / ("measurement-followup.json" if followup else "measurement.json")
    expected = json.loads(report_path.read_text()) if replay else None
    if report_path.exists() and not replay:
        raise ValueError("Existing result: use replay; never overwrite the original result")
    manifest = json.loads(manifest_path.read_text())
    if manifest["outcome"] != "ACQUIRED":
        raise ValueError("Acquisition did not pass")
    if followup:
        original = json.loads((ROOT / "acquisition.json").read_text())
        if sha(ROOT / "PROTOCOL.md") != original["protocol_sha256"]:
            raise ValueError("Referenced initial protocol hash changed")
    if sha(ROOT / manifest.get("protocol_file", "PROTOCOL.md")) != manifest["protocol_sha256"]:
        raise ValueError("Protocol hash changed after acquisition")
    for record in manifest["records"]:
        if sha(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("Raw-input hash mismatch")
    report = {"protocol_sha256": manifest["protocol_sha256"], "code_sha256": sha(Path(__file__)),
              "acquisition_sha256": sha(manifest_path),
              "outcome": "STOP_IDENTITY", "epochs": [], "scientific_claim": "none"}
    try:
        epochs = [load_epoch(entry) for entry in manifest["epochs"]]
        if len({ep["campaign"] for ep in epochs}) != len(epochs):
            raise ValueError("Duplicate observing campaign")
        if len({ep["mjd"] for ep in epochs}) != len(epochs):
            raise ValueError("Duplicate observation date")
        reference = next(ep for ep in epochs if ep["campaign"] == "VLASS3.1")
        positions = ensemble_positions(reference)
        report["reference_selected_positions"] = positions
        target = SkyCoord(*TARGET, unit="deg")
        nulls = [target.spherical_offsets_by(e*u.arcsec, n*u.arcsec)
                 for e, n in [(60, 60), (-60, 60), (60, -60), (-60, -60),
                              (120, 0), (-120, 0), (0, 120), (0, -120)]]
        for epoch in epochs:
            report["epochs"].append({"campaign": epoch["campaign"], "mjd": epoch["mjd"],
                "shape": list(epoch["array"].shape), "finite_fraction": epoch["finite_fraction"],
                "beam_arcsec_deg": [float(epoch["header"][key])*(3600 if key != "BPA" else 1)
                                    for key in ("BMAJ", "BMIN", "BPA")],
                "target": photometry(epoch, *TARGET),
                "ensemble": [photometry(epoch, *pos) for pos in positions],
                "nulls": [photometry(epoch, float(pos.ra.deg), float(pos.dec.deg)) for pos in nulls]})
        common = [i for i in range(len(positions)) if all(
            ep["ensemble"][i]["amplitude_over_noise"] >= 5 for ep in report["epochs"])]
        report["common_comparison_count"] = len(common)
        ref = next(ep for ep in report["epochs"] if ep["campaign"] == "VLASS3.1")
        if len(common) >= 5:
            for ep in report["epochs"]:
                ratios = [ep["ensemble"][i]["amplitude_jy"] / ref["ensemble"][i]["amplitude_jy"]
                          for i in common]
                median = float(np.median(ratios))
                ep["local_scale_to_reference"] = median
                ep["local_scale_mad"] = float(1.4826*np.median(np.abs(np.array(ratios)-median)))
                ep["diagnostic_target_ratio_locally_scaled"] = (
                    ep["target"]["amplitude_jy"] / ref["target"]["amplitude_jy"] / median)
        failures = []
        if not all(ep["target"]["recovered"] for ep in report["epochs"]):
            failures.append("TARGET_RECOVERY")
        if len(common) < 5:
            failures.append("INSUFFICIENT_ENSEMBLE")
        if any(abs(null["amplitude_over_noise"]) >= 5
               for ep in report["epochs"] for null in ep["nulls"]):
            failures.append("NULL_CONTAMINATION")
        report["failed_gates"] = failures
        report["outcome"] = "STOP_MEASUREMENT" if failures else "MEASUREMENT_FEASIBILITY"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        if replay:
            # The on-disk JSON uses arrays; in-memory coordinate pairs are tuples.
            if expected != json.loads(json.dumps(report, allow_nan=False)):
                raise ValueError("Replay differs from recorded result")
        else:
            save(report_path, report)
    print(json.dumps({key: report[key] for key in ("outcome", "failed_gates", "common_comparison_count")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["fetch", "measure", "replay", "recover", "_request"])
    parser.add_argument("--followup", action="store_true")
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()
    if args.mode == "fetch":
        fetch(args.followup)
    elif args.mode == "recover":
        recover()
    elif args.mode in ("measure", "replay"):
        measure(args.followup, replay=args.mode == "replay")
    else:
        request_worker(args.args[0], Path(args.args[1]), int(args.args[2]))
