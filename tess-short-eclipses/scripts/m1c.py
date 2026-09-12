"""One-shot Gaia mirror parity and catalog-only reassessment; no pixel estimator."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/m1c"
PROTOCOL = ROOT / "M1c-PROTOCOL-2026-09-12.md"
MANIFEST = DATA / "manifest.json"
TARGETS = (450781262, 53206761, 2041210548)
URL = "https://gaia.ari.uni-heidelberg.de/tap/sync"
REFERENCE = ROOT / "data/m1/450781262/gaia-dr3.xml"
REFERENCE_HASH = "d4a1069cfb5244c28db6dfc354df326ab1a5db611e36612b536b7f914d105098"
SPEC = importlib.util.spec_from_file_location("m1c_preserved_m1b", ROOT / "scripts/m1b.py")
m1b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1b)
m1 = m1b.m1
FROZEN = {"scripts/m1.py": m1b.M1_SOURCE_HASH,
          "M1-PROTOCOL-2026-09-12.md": m1b.M1_PROTOCOL_HASH,
          "scripts/m1b.py": "82ce3730897ed3479351004105e785cc0f75316ef1d481ae121e5a81d616db0c",
          "M1b-PROTOCOL-2026-09-12.md": "388d9f2a779c6536aad3abf82fd5f91c3b6048ef5da7f9401f16f79cf8c15ed9"}
UNITS = {"source_id": u.dimensionless_unscaled, "ra": u.deg, "dec": u.deg,
         "ref_epoch": u.yr, "pmra": u.mas / u.yr, "pmdec": u.mas / u.yr,
         "phot_g_mean_mag": u.mag, "ruwe": u.dimensionless_unscaled}
TOLERANCES = {"ra": 1e-10, "dec": 1e-10, "ref_epoch": 1e-9, "pmra": 1e-5,
              "pmdec": 1e-5, "phot_g_mean_mag": 1e-5, "ruwe": 1e-5}


def read_json(path):
    return json.loads(path.read_bytes())


def strict_catalog(path):
    table = m1b.strict_catalog(path)
    ids = np.asarray(table["source_id"])
    if len(np.unique(ids)) != len(ids):
        raise ValueError("STOP_DUPLICATE_SOURCE_IDS")
    for name, expected in UNITS.items():
        column = table[name]
        try:
            actual = u.Unit(str(column.unit or ""), parse_strict="raise")
            if actual != expected:
                raise ValueError("scaled or incompatible unit")
        except (ValueError, TypeError) as error:
            raise ValueError(f"STOP_CATALOG_UNITS:{name}") from error
        values = np.asarray(column)[~np.ma.getmaskarray(column)]
        if not np.all(np.isfinite(values)):
            raise ValueError(f"STOP_CATALOG_NONFINITE:{name}")
    if np.any((table["ra"] < 0) | (table["ra"] >= 360)) or np.any(np.abs(table["dec"]) > 90):
        raise ValueError("STOP_CATALOG_POSITIONS")
    return table


def compare_tables(reference, mirror, expected_rows=1290):
    if len(reference) != expected_rows or len(mirror) != expected_rows:
        raise ValueError("STOP_CATALOG_PARITY:row_count")
    tables = [table[np.argsort(np.asarray(table["source_id"]))] for table in (reference, mirror)]
    for table in tables:
        ids = np.asarray(table["source_id"])
        if ids.dtype.kind != "i" or ids.dtype.itemsize != 8 or len(np.unique(ids)) != len(ids):
            raise ValueError("STOP_CATALOG_PARITY:ids")
    if not np.array_equal(tables[0]["source_id"], tables[1]["source_id"]):
        raise ValueError("STOP_CATALOG_PARITY:source_id")
    stats = {}
    for name in m1b.FIELDS:
        left, right = (table[name] for table in tables)
        mask = np.ma.getmaskarray(left)
        if not np.array_equal(mask, np.ma.getmaskarray(right)):
            raise ValueError(f"STOP_CATALOG_PARITY:mask:{name}")
        if name == "source_id":
            continue
        delta = np.abs(np.asarray(left)[~mask] - np.asarray(right)[~mask])
        if not np.all(np.isfinite(delta)) or np.any(delta > TOLERANCES[name]):
            raise ValueError(f"STOP_CATALOG_PARITY:value:{name}")
        stats[name] = {"max_abs_difference": float(delta.max()) if len(delta) else None,
                       "masked": int(mask.sum()), "absolute_tolerance": TOLERANCES[name]}
    return {"status": "PARITY_PASS", "rows": expected_rows, "columns": stats,
            "source_ids_exact": True, "masks_exact": True, "units_validated": True}


def parity():
    if m1.sha(REFERENCE) != REFERENCE_HASH:
        raise ValueError("STOP_REFERENCE_HASH")
    return compare_tables(strict_catalog(REFERENCE), strict_catalog(verified_response(TARGETS[0])))


def verified_response(tic):
    folder = DATA / str(tic)
    receipt = read_json(folder / "catalog-receipt.json")
    path = folder / "gaia-dr3.xml"
    if (m1.sha(path) != receipt["sha256"] or path.stat().st_size != receipt["bytes"]
            or receipt["bytes"] > 5_000_000 or receipt["manifest_sha256"] != m1.sha(MANIFEST)):
        raise ValueError("STOP_CATALOG_HASH")
    return path


def dependencies():
    paths = list(FROZEN) + ["scripts/m1c.py", PROTOCOL.name]
    paths += [f"out/m1b-{tic}.json" for tic in TARGETS]
    paths += [f"data/m1/{tic}/catalog-query.json" for tic in TARGETS]
    return {path: m1.sha(ROOT / path) for path in paths}


def verify():
    if any(m1.sha(ROOT / path) != digest for path, digest in FROZEN.items()):
        raise ValueError("STOP_FROZEN_PROVENANCE")
    manifest = read_json(MANIFEST)
    if manifest["dependencies"] != dependencies() or manifest["runner_sha256"] != m1.sha(m1.RUNNER):
        raise ValueError("STOP_MANIFEST_CHANGED")
    if m1.sha(REFERENCE) != REFERENCE_HASH:
        raise ValueError("STOP_REFERENCE_HASH")
    return manifest


def prepare():
    if any(m1.sha(ROOT / path) != digest for path, digest in FROZEN.items()):
        raise ValueError("STOP_FROZEN_PROVENANCE")
    if len(strict_catalog(REFERENCE)) != 1290 or m1.sha(REFERENCE) != REFERENCE_HASH:
        raise ValueError("STOP_REFERENCE")
    m1.save(MANIFEST, {"utc": datetime.now(timezone.utc).isoformat(), "dependencies": dependencies(),
                      "runner_sha256": m1.sha(m1.RUNNER), "url": URL,
                      "unknown_search_authorized": False})


def fetch(tic):
    import requests
    verify()
    if tic != TARGETS[0]:
        parity()
    folder = DATA / str(tic)
    folder.mkdir(parents=True, exist_ok=True)
    prior = read_json(ROOT / f"data/m1/{tic}/catalog-query.json")
    m1.save(folder / "attempt.json", {"tic": tic, "url": URL, "adql": prior["adql"],
                                    "utc": datetime.now(timezone.utc).isoformat(),
                                    "manifest_sha256": m1.sha(MANIFEST)})
    path = folder / "gaia-dr3.xml"
    try:
        with requests.post(URL, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
                                      "QUERY": prior["adql"]}, stream=True, timeout=(45, 45),
                           allow_redirects=False) as response:
            if response.status_code != 200:
                raise ValueError(f"STOP_HTTP:{response.status_code}")
            size = m1.stream_response(response, path, 5_000_000, time.monotonic() + 55)
        table = strict_catalog(path)
        m1.save(folder / "catalog-receipt.json", {"tic": tic, "bytes": size, "rows": len(table),
                                                "sha256": m1.sha(path), "url": URL,
                                                "manifest_sha256": m1.sha(MANIFEST)})
    except Exception as error:
        m1.save(folder / "failure.json", {"type": type(error).__name__, "error": str(error),
                                         "partial_bytes": path.stat().st_size if path.exists() else 0})
        raise


def context(tic):
    """Reproduce time selection only; never read FLUX arrays or call pixel fitting."""
    old = read_json(ROOT / f"out/m1b-{tic}.json")
    _, lc_path = m1.read_solution(tic)
    tp_path = ROOT / "data/m1" / str(tic) / old["input"]["filename"]
    if m1.sha(tp_path) != old["input"]["sha256"]:
        raise ValueError("STOP_TPF_HASH")
    with fits.open(tp_path) as tp, fits.open(lc_path) as lc:
        td, ld = tp[1].data, lc[1].data
        if any(len(np.unique(d["CADENCENO"])) != len(d) for d in (td, ld)):
            raise ValueError("STOP_DUPLICATE_CADENCES")
        lg = (np.isfinite(ld["TIME"]) & np.isfinite(ld["PDCSAP_FLUX"])
              & np.isfinite(ld["PDCSAP_FLUX_ERR"]) & (ld["PDCSAP_FLUX_ERR"] > 0) & (ld["QUALITY"] == 0))
        tg = np.isfinite(td["TIME"]) & (td["QUALITY"] == 0)
        _, _, ti = np.intersect1d(ld["CADENCENO"][lg], td["CADENCENO"][tg], return_indices=True)
        times = td["TIME"][np.flatnonzero(tg)[ti]]
        if len(times) != old["points"]:
            raise ValueError("STOP_TIME_SELECTION")
        epoch = Time(2457000 + (times.min() + times.max()) / 2, format="jd", scale="tdb").jyear
        wcs = WCS(tp[2].header)
    if tic == TARGETS[0] and epoch != old["catalog"]["epoch_jyear"]:
        raise ValueError("STOP_EPOCH_REPRODUCTION")
    return old, wcs, epoch


def diagnostic(tic):
    verify()
    verified_response(tic)
    old, wcs, epoch = context(tic)

    class ValidatedTable:
        @staticmethod
        def read(path, **kwargs):
            return strict_catalog(path)

    saved_data, saved_table = m1.DATA, m1.Table
    try:
        m1.DATA, m1.Table = DATA, ValidatedTable
        fit = old["centroid_surrogate"]
        catalog = m1.catalog_comparison(tic, wcs, old["target_header_radec"], (fit["x"], fit["y"]),
                                        epoch, np.asarray(old["images"]["difference"]).shape)
    finally:
        m1.DATA, m1.Table = saved_data, saved_table
    return m1.clean({"tic": tic, "status": "METADATA_DIAGNOSTIC_VALIDATION_INCOMPLETE",
                     "manifest_sha256": m1.sha(MANIFEST), "original_result_sha256": m1.sha(ROOT / f"out/m1b-{tic}.json"),
                     "pixel_recalculation": False, "unknown_search_authorized": False,
                     "fixed_centroid": [fit["x"], fit["y"]], "catalog": catalog})


def run():
    verify()
    m1.save(DATA / "run-start.json", {"manifest_sha256": m1.sha(MANIFEST)})
    spec = importlib.util.spec_from_file_location("m1c_bounded_runner", m1.RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    outcomes = []
    parity_result = None
    for tic in TARGETS:
        try:
            code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                               "run", "--worker", str(tic)], 60)
        except Exception as error:
            code, output = 1, f"worker launch/cleanup failure: {type(error).__name__}: {error}"
        row = {"tic": tic, "returncode": code, "output": output}
        if code == 0:
            try:
                if tic == TARGETS[0]:
                    parity_result = parity()
                    m1.save(ROOT / "out/m1c-parity.json", parity_result)
                result = diagnostic(tic)
                m1.save(ROOT / f"out/m1c-{tic}.json", result)
                row["catalog_status"] = result["catalog"]["status"]
            except Exception as error:
                row.update(returncode=1, diagnostic_error=str(error))
        outcomes.append(row)
        m1.save(DATA / f"outcome-{tic}.json", row)
        print(json.dumps(row), flush=True)
        if tic == TARGETS[0] and (row["returncode"] or parity_result is None):
            break
    m1.save(ROOT / "out/m1c-summary.json", {"manifest_sha256": m1.sha(MANIFEST), "outcomes": outcomes,
                                          "parity": parity_result, "unknown_search_authorized": False,
                                          "status": "STOP_CATALOG_PARITY" if parity_result is None else "VALIDATION_INCOMPLETE"})


def replay():
    verify()
    summary = read_json(ROOT / "out/m1c-summary.json")
    if summary["manifest_sha256"] != m1.sha(MANIFEST):
        raise ValueError("STOP_SUMMARY_HASH")
    if summary["parity"] is not None and parity() != summary["parity"]:
        raise ValueError("STOP_PARITY_REPLAY")
    for row in summary["outcomes"]:
        if read_json(DATA / f"outcome-{row['tic']}.json") != row:
            raise ValueError("STOP_OUTCOME_REPLAY")
        attempt_path = DATA / str(row["tic"]) / "attempt.json"
        if attempt_path.exists():
            attempt = read_json(attempt_path)
            prior = read_json(ROOT / f"data/m1/{row['tic']}/catalog-query.json")
            if (attempt["adql"] != prior["adql"] or attempt["url"] != URL
                    or attempt["manifest_sha256"] != m1.sha(MANIFEST)):
                raise ValueError("STOP_ATTEMPT_REPLAY")
        if row["returncode"] == 0:
            if diagnostic(row["tic"]) != read_json(ROOT / f"out/m1c-{row['tic']}.json"):
                raise ValueError("STOP_DIAGNOSTIC_REPLAY")
    print(json.dumps({"retained_replay": "PASS", "first_field_parity": summary["parity"],
                      "pixel_recalculation": False, "network": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "replay"))
    parser.add_argument("--worker", type=int, choices=TARGETS)
    args = parser.parse_args()
    if args.worker:
        if args.stage != "run":
            raise ValueError("STOP_WORKER_STAGE")
        fetch(args.worker)
    else:
        {"prepare": prepare, "run": run, "replay": replay}[args.stage]()


if __name__ == "__main__":
    main()
