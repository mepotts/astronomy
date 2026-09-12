"""Bounded known-control recovery. No unknown-target or submission mode."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import numpy as np
from astropy.io import fits
from astropy.timeseries import BoxLeastSquares

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROTOCOL = ROOT / "M0-PROTOCOL-2026-09-12.md"
CONTROLS = {450781262: (99, .09388575), 53206761: (72, .13280937),
            2041210548: (57, .29092036)}
DURATIONS = np.array([4., 8., 16.]) / 1440
MAX_BYTES = 20_000_000
RUNNER = ROOT.parent / "dyson-revet/scripts/check_e_release.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bounded_worker(stage, tic, timeout):
    # Reuse the repository's tested Windows process-tree / POSIX group cleanup.
    spec = importlib.util.spec_from_file_location("tess_process_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bounded_run([sys.executable, "-B", __file__, stage, "--worker", str(tic)], timeout)


def validate_product(product):
    name = product["filename"]
    if Path(name).name != name or "/" in name or "\\" in name or not name.endswith("_lc.fits"):
        raise ValueError("STOP_UNSAFE_PRODUCT_PATH")
    if product["uri"] != "mast:TESS/product/"+name or not 0 < product["bytes"] <= MAX_BYTES:
        raise ValueError("STOP_PRODUCT_URI_OR_SIZE")
    return name


def prepare(t, y, dy, quality):
    t, y, dy, quality = map(np.asarray, (t, y, dy, quality))
    use = np.isfinite(t) & np.isfinite(y) & np.isfinite(dy) & (dy > 0) & (quality == 0)
    t, y, dy = t[use], y[use], dy[use]
    order = np.argsort(t)
    t, y, dy = t[order], y[order], dy[order]
    if len(t) < 1000 or np.ptp(t) < 10:
        raise ValueError("STOP_COVERAGE")
    if np.any(np.diff(t) <= 0):
        raise ValueError("STOP_DUPLICATE_TIMES")
    if not np.any(y > 0):
        raise ValueError("STOP_NORMALIZATION")
    scale = float(np.median(y[y > 0]))
    return t, y/scale, dy/scale


def validate_header(primary, header, tic, sector):
    if int(primary["TICID"]) != tic or int(primary["SECTOR"]) != sector:
        raise ValueError("STOP_PRODUCT_IDENTITY")
    if header["TIMEUNIT"] != "d" or header["TIMESYS"] != "TDB":
        raise ValueError("STOP_TIME_REFERENCE")
    if header["BJDREFI"] != 2457000 or header.get("BJDREFF", 0.) != 0.:
        raise ValueError("STOP_TIME_REFERENCE")
    if not np.isclose(header["TIMEDEL"]*86400, 120., rtol=1e-4):
        raise ValueError("STOP_CADENCE")


def period_grid(baseline):
    if not np.isfinite(baseline) or baseline <= 0:
        raise ValueError("invalid baseline")
    count = int(np.ceil(np.log(1/.05) / (DURATIONS[0]/(3*baseline))))
    return np.geomspace(.05, 1., count+1)


def search(t, y, dy, periods=None, chunk=2000):
    periods = period_grid(np.ptp(t)) if periods is None else np.asarray(periods)
    model = BoxLeastSquares(t, y, dy)
    winner = None
    for duration in DURATIONS:
        allowed = periods[duration/periods <= .15]
        for start in range(0, len(allowed), chunk):
            p = allowed[start:start+chunk]
            r = model.power(p, float(duration), objective="likelihood", oversample=10)
            valid = np.isfinite(r.power) & np.isfinite(r.depth) & (r.depth > 0)
            if not valid.any():
                continue
            i = int(np.argmax(np.where(valid, r.power, -np.inf)))
            row = {k: float(r[k][i]) for k in
                   ("power", "period", "duration", "transit_time", "depth", "depth_err", "depth_snr")}
            if not all(np.isfinite(v) for v in row.values()):
                continue
            if winner is None or row["power"] > winner["power"]:
                winner = row
    if winner is None:
        raise ValueError("STOP_NO_FINITE_SOLUTION")
    return winner


def depth_stats(t, y, dy, solution):
    period, epoch, duration = (solution[k] for k in ("period", "transit_time", "duration"))
    phase = (t-epoch+.5*period) % period - .5*period
    inside = np.abs(phase) < .5*duration
    if not inside.any() or inside.all():
        return {"depth": None, "error": None, "snr": None,
                "in_points": int(inside.sum()), "sampled_events": 0}
    w = dy**-2
    depth = np.average(y[~inside], weights=w[~inside]) - np.average(y[inside], weights=w[inside])
    error = np.sqrt(1/w[inside].sum() + 1/w[~inside].sum())
    cycles = np.floor((t[inside]-epoch)/period+.5).astype(np.int64)
    return {"depth": float(depth), "error": float(error), "snr": float(depth/error),
            "in_points": int(inside.sum()), "sampled_events": len(np.unique(cycles))}


def grade(solution, full, halves, reference):
    errors = {label: abs(solution["period"]/(reference*factor)-1)
              for label, factor in (("exact", 1), ("half", .5), ("double", 2))}
    alias = min(errors, key=errors.get)
    passed = (errors[alias] <= .001 and solution["depth_snr"] >= 10
              and full["in_points"] >= 20 and full["sampled_events"] >= 10
              and all(h["snr"] is not None and h["snr"] >= 5
                      and h["sampled_events"] >= 5 for h in halves))
    return {"passed": bool(passed), "period_match": alias if errors[alias] <= .001 else "none",
            "best_fractional_period_error": float(errors[alias])}


def acquire(tic):
    from astroquery.mast import Observations
    Observations.TIMEOUT = 30
    sector, _ = CONTROLS[tic]
    folder = DATA / str(tic)
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "receipt.json").exists():
        raise ValueError("receipt exists; do not reacquire")
    table = Observations.query_criteria(obs_collection="TESS", target_name=str(tic),
                                       dataproduct_type="timeseries")
    table.write(folder / "observations.ecsv", format="ascii.ecsv")
    obs = [{"obsid": int(r["obsid"]), "sector": int(r["sequence_number"]),
            "exposure": float(r["t_exptime"]), "rights": str(r["dataRights"]),
            "obs_id": str(r["obs_id"]), "start_mjd": float(r["t_min"]),
            "end_mjd": float(r["t_max"])} for r in table]
    eligible = [r for r in obs if r["rights"] == "PUBLIC" and r["exposure"] == 120.]
    if not eligible or max(r["sector"] for r in eligible) != sector:
        raise ValueError("STOP_SELECTION_METADATA_CHANGED")
    selected = max((r for r in eligible if r["sector"] == sector), key=lambda r: r["obsid"])
    products = Observations.get_product_list(str(selected["obsid"]))
    products.write(folder / "products.ecsv", format="ascii.ecsv")
    lc = [{"filename": str(r["productFilename"]), "uri": str(r["dataURI"]),
           "bytes": int(r["size"])} for r in products if r["productType"] == "SCIENCE"
          and r["productSubGroupDescription"] == "LC" and str(r["productFilename"]).endswith("_lc.fits")]
    if not lc:
        raise ValueError("STOP_NO_LC")
    product = max(lc, key=lambda r: r["filename"])
    validate_product(product)
    save(folder / "metadata.json", {"observations": obs, "selected": selected, "lc_products": lc})


def download(tic):
    import astropy
    import astroquery
    import requests
    folder = DATA / str(tic)
    metadata = json.loads((folder / "metadata.json").read_bytes())
    selected = metadata["selected"]
    product = max(metadata["lc_products"], key=lambda r: r["filename"])
    name = validate_product(product)
    sector = CONTROLS[tic][0]
    url = "https://mast.stsci.edu/api/v0.1/Download/file?uri="+quote(product["uri"], safe=":/")
    path = folder / name
    started, total = time.monotonic(), 0
    with requests.get(url, stream=True, timeout=(15, 45)) as response:
        response.raise_for_status()
        if int(response.headers.get("Content-Length", 0)) > MAX_BYTES:
            raise ValueError("STOP_SIZE")
        with path.open("xb") as stream:
            for block in response.iter_content(65536):
                total += len(block)
                if total > MAX_BYTES or time.monotonic()-started > 45:
                    raise ValueError("STOP_DOWNLOAD_LIMIT")
                stream.write(block)
    if total != product["bytes"]:
        raise ValueError("STOP_SIZE_MISMATCH")
    with fits.open(path) as hdus:
        validate_header(hdus[0].header, hdus[1].header, tic, sector)
    save(folder / "receipt.json", {"tic": tic, "sector": sector, "obsid": selected["obsid"],
                                  "filename": name, "url": url, "bytes": total,
                                  "sha256": sha(path), "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                                  "start_mjd": selected["start_mjd"], "end_mjd": selected["end_mjd"],
                                  "versions": {"astropy": astropy.__version__, "astroquery": astroquery.__version__,
                                               "requests": requests.__version__}})


def analyze(tic):
    import astropy
    folder = DATA / str(tic)
    receipt = json.loads((folder / "receipt.json").read_bytes())
    path = folder / receipt["filename"]
    if sha(path) != receipt["sha256"]:
        raise ValueError("STOP_INPUT_HASH")
    with fits.open(path) as hdus:
        validate_header(hdus[0].header, hdus[1].header, tic, CONTROLS[tic][0])
        data = hdus[1].data
        t, y, dy = prepare(data["TIME"], data["PDCSAP_FLUX"], data["PDCSAP_FLUX_ERR"], data["QUALITY"])
    solution = search(t, y, dy)
    full = depth_stats(t, y, dy, solution)
    first = t < (t.min()+t.max())/2
    halves = [depth_stats(t[m], y[m], dy[m], solution) for m in (first, ~first)]
    result = {"tic": tic, "input": receipt, "points": len(t), "baseline_days": float(np.ptp(t)),
              "solution": solution, "full": full, "halves": halves,
              "grade": grade(solution, full, halves, CONTROLS[tic][1]),
              "protocol_sha256": sha(PROTOCOL), "script_sha256": sha(__file__),
              "runner_sha256": sha(RUNNER),
              "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "astropy": astropy.__version__}}
    save(ROOT / "out" / f"m0-{tic}.json", result)
    print(json.dumps({"tic": tic, "period": solution["period"], **result["grade"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fetch", "analyze", "metadata", "download"])
    parser.add_argument("--worker", type=int, choices=list(CONTROLS))
    args = parser.parse_args()
    if args.worker:
        {"metadata": acquire, "analyze": analyze, "download": download}[args.stage](args.worker)
        return
    if args.stage in ("download", "metadata"):
        parser.error("internal acquisition stage requires a known-control worker")
    outcomes = []
    for tic in CONTROLS:
        stages = [("metadata", 120), ("download", 45)] if args.stage == "fetch" else [("analyze", 600)]
        runs = []
        for stage, timeout in stages:
            code, output = bounded_worker(stage, tic, timeout)
            runs.append({"stage": stage, "returncode": code, "output": output})
            if code:
                break
        row = {"tic": tic, "returncode": code, "runs": runs}
        outcomes.append(row)
        print(json.dumps(row), flush=True)
    save(DATA / f"{args.stage}-run.json", {"utc": datetime.now(timezone.utc).isoformat(), "outcomes": outcomes})
    if any(r["returncode"] != 0 for r in outcomes):
        raise SystemExit(1)
    if args.stage == "analyze":
        rows = [json.loads((ROOT / "out" / f"m0-{tic}.json").read_bytes()) for tic in CONTROLS]
        passed = sum(r["grade"]["passed"] for r in rows)
        summary = {"status": "GO_LOCALIZATION_CONTROLS_ONLY" if passed == 3 else "STOP_CONTROL_RECOVERY",
                   "passed": passed, "total": 3, "unknown_search_authorized": False,
                   "protocol_sha256": sha(PROTOCOL), "script_sha256": sha(__file__),
                   "runner_sha256": sha(RUNNER)}
        save(ROOT / "out" / "m0-summary.json", summary)
        print(json.dumps(summary), flush=True)
        if passed != 3:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
