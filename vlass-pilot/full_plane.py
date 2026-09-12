"""Fixed parent-plane calibration experiment; never an unknown-source search."""

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "full-plane"
CAP = 500_000_000
FROZEN_PILOT_SHA = "953a26cae7845e44811336c6a8553e949aa49dffcc2e69d739f041fd0ff41978"
HELPER_SHA = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


P = module("frozen_vlass_control", ROOT / "pilot.py")
HELPER_PATH = ROOT.parent / "dyson-revet" / "scripts" / "check_e_release.py"
H = module("audited_tree_timeout", HELPER_PATH)


def validate_dependencies():
    if P.sha(ROOT / "pilot.py") != FROZEN_PILOT_SHA:
        raise ValueError("Frozen pilot source changed")
    if P.sha(HELPER_PATH) != HELPER_SHA:
        raise ValueError("Audited process-tree helper changed")


def preflight(prior_bytes, sizes):
    if not sizes or any(type(size) is not int or size <= 0 for size in sizes):
        raise ValueError("Missing/invalid public metadata sizes")
    if prior_bytes < 0 or prior_bytes + sum(sizes) > CAP:
        raise ValueError("Cumulative acquisition cap would be exceeded")
    return prior_bytes + sum(sizes)


def bounded_get(url, destination, size):
    validate_dependencies()
    if destination.exists():
        raise ValueError("Never overwrite a retained input")
    code, output = H.bounded_run(
        [sys.executable, str(ROOT / "pilot.py"), "_request", url,
         str(destination.resolve()), str(size)], 75)
    if code:
        raise RuntimeError(f"bounded request return={code}: {output}")
    receipt = json.loads(output)
    if receipt["bytes"] != size:
        raise ValueError("Downloaded bytes differ from advertised parent plane size")
    receipt["path"] = destination.relative_to(ROOT).as_posix()
    return receipt


def build_plan():
    validate_dependencies()
    initial = json.loads((ROOT / "acquisition.json").read_text())
    old = json.loads((ROOT / "acquisition-recovered.json").read_text())
    if old["outcome"] != "ACQUIRED":
        raise ValueError("Original three-epoch inputs not acquired")
    for rec in old["records"]:
        if P.sha(ROOT / rec["path"]) != rec["sha256"]:
            raise ValueError("Retained metadata/input hash mismatch")
    prior = initial["stored_bytes"] + old["stored_bytes"]
    plan = []
    for epoch in old["epochs"]:
        campaign = epoch["campaign"]
        datalink = ROOT / "data" / "followup" / (campaign + "-datalink.xml")
        links = P.links(datalink.read_bytes())
        for kind, semantics in (("image", "#this"), ("rms", "#auxiliary")):
            rows = [row for row in links if row["semantics"] == semantics
                    and row["content_type"] == "application/fits"
                    and (kind == "image" or ".rms." in row["access_url"])]
            if len(rows) != 1:
                raise ValueError("Parent image/RMS not unique")
            url = rows[0]["access_url"]
            if not url.startswith("https://cadc-west-01.canfar.net/raven/files/nrao:VLASS/"):
                raise ValueError("Unexpected parent-plane host/product prefix")
            if f"{campaign}.ql.T10t18.J113801-033000." not in url:
                raise ValueError("Plan would leave frozen field/epoch")
            plan.append({"campaign": campaign, "kind": kind, "url": url,
                         "bytes": int(rows[0]["content_length"]),
                         "obs_id": epoch["obs_id"], "t_min": epoch["t_min"],
                         "t_max": epoch["t_max"]})
    if len(plan) != 6 or {row["campaign"] for row in plan} != set(P.CAMPAIGNS[1:]):
        raise ValueError("Expected exactly six files from three independent campaigns")
    total = preflight(prior, [row["bytes"] for row in plan])
    return prior, total, plan


def fetch():
    destination = ROOT / "full-plane-acquisition.json"
    if destination.exists():
        raise ValueError("Parent-plane acquisition already attempted; no automatic retries")
    prior, total, plan = build_plan()
    DATA.mkdir(parents=True, exist_ok=True)
    manifest = {"outcome": "INCOMPLETE", "started_utc": datetime.now(timezone.utc).isoformat(),
                "protocol_sha256": P.sha(ROOT / "FULL-PLANE-PROTOCOL.md"),
                "pilot_sha256": FROZEN_PILOT_SHA, "timeout_helper_sha256": HELPER_SHA,
                "driver_sha256": P.sha(Path(__file__)), "prior_retained_bytes": prior,
                "planned_cumulative_bytes": total, "plan": plan, "records": []}
    P.save(destination, manifest)
    try:
        for item in plan:
            receipt = bounded_get(item["url"], DATA/(item["campaign"]+"-"+item["kind"]+".fits"),
                                  item["bytes"])
            manifest["records"].append({**item, **receipt})
            P.save(destination, manifest)
            print(item["campaign"], item["kind"], receipt["bytes"], flush=True)
        manifest["outcome"] = "ACQUIRED"
    except Exception as error:
        manifest["outcome"] = "STOP_ACQUISITION"
        manifest["error"] = str(error)
        raise
    finally:
        manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["retained_cumulative_bytes"] = prior + sum(row["bytes"] for row in manifest["records"])
        P.save(destination, manifest)


def analyze(replay=False):
    import astropy.units as u
    import numpy as np
    from astropy.coordinates import SkyCoord

    validate_dependencies()
    manifest_path = ROOT / "full-plane-acquisition.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["outcome"] != "ACQUIRED":
        raise ValueError("Full parent planes not acquired")
    if manifest["protocol_sha256"] != P.sha(ROOT / "FULL-PLANE-PROTOCOL.md"):
        raise ValueError("Full-plane protocol changed")
    original = json.loads((ROOT / "acquisition.json").read_text())
    if original["protocol_sha256"] != P.sha(ROOT / "PROTOCOL.md"):
        raise ValueError("Referenced original protocol changed")
    output = ROOT / "full-plane-measurement.json"
    expected = json.loads(output.read_text()) if replay else None
    if output.exists() and not replay:
        raise ValueError("Never overwrite recorded analysis")
    for record in manifest["records"]:
        if P.sha(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("Parent-plane input hash mismatch")
    report = {"outcome": "STOP_IDENTITY", "protocol_sha256": manifest["protocol_sha256"],
              "driver_sha256": P.sha(Path(__file__)), "pilot_sha256": FROZEN_PILOT_SHA,
              "timeout_helper_sha256": HELPER_SHA, "acquisition_sha256": P.sha(manifest_path),
              "claim": "same-field calibration feasibility only", "epochs": []}
    try:
        epochs = []
        for campaign in P.CAMPAIGNS[1:]:
            records = [row for row in manifest["records"] if row["campaign"] == campaign]
            entry = {key: records[0][key] for key in ("campaign", "obs_id", "t_min", "t_max")}
            entry.update({row["kind"]: row["path"] for row in records})
            epochs.append(P.load_epoch(entry))
        positions = P.ensemble_positions(epochs[1])
        report["reference_positions"] = positions
        target = SkyCoord(*P.TARGET, unit="deg")
        nulls = [target.spherical_offsets_by(e*u.arcsec, n*u.arcsec)
                 for e, n in [(60, 60), (-60, 60), (60, -60), (-60, -60),
                              (120, 0), (-120, 0), (0, 120), (0, -120)]]
        for epoch in epochs:
            report["epochs"].append({"campaign": epoch["campaign"], "mjd": epoch["mjd"],
                "shape": list(epoch["array"].shape), "finite_fraction": epoch["finite_fraction"],
                "beam_arcsec_deg": [float(epoch["header"][key])*(3600 if key != "BPA" else 1)
                                    for key in ("BMAJ", "BMIN", "BPA")],
                "target": P.photometry(epoch, *P.TARGET),
                "ensemble": [P.photometry(epoch, *pos) for pos in positions],
                "nulls": [P.photometry(epoch, float(pos.ra.deg), float(pos.dec.deg)) for pos in nulls]})
        common = [i for i in range(len(positions)) if all(
            epoch["ensemble"][i]["amplitude_over_noise"] >= 5 for epoch in report["epochs"])]
        report["common_reference_indices"] = common
        report["common_comparison_count"] = len(common)
        if len(common) >= 5:
            ref = report["epochs"][1]
            for epoch in report["epochs"]:
                ratios = [epoch["ensemble"][i]["amplitude_jy"] / ref["ensemble"][i]["amplitude_jy"]
                          for i in common]
                median = float(np.median(ratios))
                epoch["local_scale_to_reference"] = median
                epoch["local_scale_mad"] = float(1.4826*np.median(np.abs(np.array(ratios)-median)))
                epoch["diagnostic_target_ratio_locally_scaled"] = (
                    epoch["target"]["amplitude_jy"] / ref["target"]["amplitude_jy"] / median)
        failed = []
        if len(common) < 5:
            failed.append("INSUFFICIENT_ENSEMBLE")
        if not all(epoch["target"]["recovered"] for epoch in report["epochs"]):
            failed.append("TARGET_RECOVERY")
        if any(abs(null["amplitude_over_noise"]) >= 5
               for epoch in report["epochs"] for null in epoch["nulls"]):
            failed.append("NULL_CONTAMINATION")
        report["failed_gates"] = failed
        report["outcome"] = "STOP_CALIBRATION" if failed else "CALIBRATION_FEASIBILITY"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        if replay:
            if expected != json.loads(json.dumps(report, allow_nan=False)):
                raise ValueError("Full-plane replay differs")
        else:
            P.save(output, report)
    print(report["outcome"], report["common_comparison_count"], report["failed_gates"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["fetch", "measure", "replay"])
    args = parser.parse_args()
    if args.mode == "fetch":
        fetch()
    else:
        analyze(args.mode == "replay")
