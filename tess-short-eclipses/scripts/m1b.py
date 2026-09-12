"""Strict metadata adapter; preserves and calls the unchanged M1 pixel estimator."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from astropy.table import Table

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/m1b"
PROTOCOL = ROOT / "M1b-PROTOCOL-2026-09-12.md"
SPEC = importlib.util.spec_from_file_location("preserved_m1", ROOT / "scripts/m1.py")
m1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1)
FIELDS = ["source_id", "ra", "dec", "ref_epoch", "pmra", "pmdec", "phot_g_mean_mag", "ruwe"]
M1_SOURCE_HASH = "22c46cbfd34877ac66d7b1fcd411ecb8b323aca5ea987da58d62ea141ed29115"
M1_PROTOCOL_HASH = "95ebebc25aedda27ad2818589951efae73344e7c8ff83ce6f3177c49e9ec8ef0"
PIXEL_FIELDS = ["points", "paired_events", "day_labels", "pixels", "aperture_pixels",
                "target_header_radec", "target_xy_zero_based", "primary", "background",
                "phase_controls", "centroid_surrogate", "centroid_target_distance_pixels",
                "bootstrap_valid", "bootstrap_total", "bootstrap_radial_95_pixels",
                "bootstrap_xy", "calibration", "images"]


def verify_base():
    if m1.sha(ROOT / "scripts/m1.py") != M1_SOURCE_HASH or m1.sha(m1.PROTOCOL) != M1_PROTOCOL_HASH:
        raise ValueError("STOP_M1_CHANGED")


def adapter_provenance():
    return {"metadata_adapter_sha256": m1.sha(__file__), "metadata_amendment_sha256": m1.sha(PROTOCOL),
            "pixel_estimator_unchanged_sha256": M1_SOURCE_HASH}


def strict_catalog(path):
    root = ET.parse(path).getroot()
    ns = {"v": "http://www.ivoa.net/xml/VOTable/v1.3"}
    status = root.findall(".//v:INFO[@name='QUERY_STATUS']", ns)
    if not status or any(item.get("value") != "OK" for item in status):
        raise ValueError("STOP_CATALOG_STATUS")
    fields = root.findall(".//v:TABLE/v:FIELD", ns)
    names = [field.get("name") for field in fields]
    if len(names) != len(FIELDS) or len(set(names)) != len(names) or set(names) != set(FIELDS):
        raise ValueError("STOP_CATALOG_FIELDS")
    if next(field for field in fields if field.get("name") == "source_id").get("datatype") != "long":
        raise ValueError("STOP_SOURCE_ID_TYPE")
    table = Table.read(path, format="votable", use_names_over_ids=True)
    if set(table.colnames) != set(FIELDS) or len(table) == 0 or len(table) >= 5001:
        raise ValueError("STOP_CATALOG_FIELDS")
    ids = table["source_id"]
    if ids.dtype.kind != "i" or ids.dtype.itemsize != 8 or np.any(np.ma.getmaskarray(ids)) or np.any(ids <= 0):
        raise ValueError("STOP_SOURCE_ID_TYPE")
    if any(np.any(np.ma.getmaskarray(table[k])) or not np.all(np.isfinite(table[k])) for k in ("ra", "dec", "ref_epoch")):
        raise ValueError("STOP_CATALOG_POSITIONS")
    return table


class FieldNameTable:
    @staticmethod
    def read(path, **kwargs):
        return strict_catalog(path) if kwargs.get("format") == "votable" else Table.read(path, **kwargs)


def install_adapter():
    verify_base()
    m1.Table = FieldNameTable
    original_save = m1.save
    original_catalog_comparison = m1.catalog_comparison

    def save(path, value):
        if path.name == "catalog-query.json":
            prior = json.loads((ROOT / "data/m1" / path.parent.name / "catalog-query.json").read_bytes())
            if value["adql"] != prior["adql"] or value["url"] != prior["url"]:
                raise ValueError("STOP_QUERY_CHANGED")
        if "images" in value:
            tic = value["tic"]
            prior = ROOT / "out" / f"m1-{tic}.json"
            if prior.exists():
                old = json.loads(prior.read_bytes())
                if any(m1.clean(value[key]) != old[key] for key in PIXEL_FIELDS):
                    raise ValueError("STOP_PIXEL_REPLAY_CHANGED")
                value["pixel_replay_exact_match"] = True
                value["original_pixel_result_sha256"] = m1.sha(prior)
            else:
                value["pixel_replay_exact_match"] = None
                value["original_pixel_result_missing_reason"] = "M1 source_id parser prevented serialization"
            path = ROOT / "out" / f"m1b-{tic}.json"
        original_save(path, {**value, **adapter_provenance()})

    def comparison(*args, **kwargs):
        original_data = m1.DATA
        try:
            m1.DATA = DATA
            return original_catalog_comparison(*args, **kwargs)
        finally:
            m1.DATA = original_data

    m1.save = save
    m1.catalog_comparison = comparison


def prepare():
    tic = 450781262
    old = ROOT / "data/m1" / str(tic)
    new = DATA / str(tic)
    new.mkdir(parents=True, exist_ok=True)
    receipt = json.loads((old / "catalog-receipt.json").read_bytes())
    original = old / "gaia-dr3.xml"
    if m1.sha(original) != receipt["sha256"]:
        raise ValueError("STOP_ORIGINAL_CATALOG_HASH")
    strict_catalog(original)
    destination = new / "gaia-dr3.xml"
    if destination.exists():
        raise ValueError("STOP_REUSE_ALREADY_EXISTS")
    shutil.copyfile(original, destination)
    m1.save(new / "catalog-receipt.json", {**receipt,
                                         "reused_from": "data/m1/450781262/gaia-dr3.xml",
                                         "original_receipt_sha256": m1.sha(old / "catalog-receipt.json")})


def worker(stage, tic):
    install_adapter()
    if stage == "retry":
        if tic not in (53206761, 2041210548):
            raise ValueError("STOP_RETRY_TARGET")
        m1.DATA = DATA
        m1.catalog(tic)
    else:
        m1.analyze(tic)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "retry", "analyze"])
    parser.add_argument("--worker", type=int, choices=list(m1.CONTROLS))
    args = parser.parse_args()
    verify_base()
    if args.worker:
        worker(args.stage, args.worker)
        return
    if args.stage == "prepare":
        install_adapter()
        prepare()
        return
    spec = importlib.util.spec_from_file_location("m1b_runner", m1.RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    outcomes = []
    targets = (53206761, 2041210548) if args.stage == "retry" else tuple(m1.CONTROLS)
    for tic in targets:
        code, output = runner.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()),
                                           args.stage, "--worker", str(tic)], 60 if args.stage == "retry" else 600)
        row = {"tic": tic, "returncode": code, "output": output}
        outcomes.append(row)
        print(json.dumps(row), flush=True)
    summary = {**adapter_provenance(), "unknown_search_authorized": False,
               "outcomes": outcomes, "stage": args.stage}
    m1.save(ROOT / "out" / f"m1b-{args.stage}-run.json", summary)
    if any(row["returncode"] for row in outcomes):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
