"""Candidate-free SPHEREx M0 selection, live coverage probe, and summary.

Private coordinates/identifiers and exact raw service responses live only in gitignored
directories. The tracked JSON contains aggregate feasibility statistics and provenance hashes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import os
import statistics
import tempfile
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT.parent
DYSON = REPO / "dyson-revet"
PRIVATE = PROJECT / "data" / "private"
RAW = PROJECT / "data" / "raw"
OUT = PROJECT / "out"

CATALOG = DYSON / "catalog" / "dyson-revet_highlat_extreme_IR_excess_v3.csv"
PM13 = DYSON / "data" / "EEM_dwarf_UBVIJHK_colors_Teff.txt"
CONTROL_CELLS = DYSON / "data" / "w4" / "aip" / "cells"
MANIFEST = PRIVATE / "m0_manifest.csv"
SUMMARY = OUT / "m0_result.json"

TAP_SYNC = "https://irsa.ipac.caltech.edu/TAP/sync"
OFFICIAL_URLS = {
    "irsa_mission": "https://irsa.ipac.caltech.edu/Missions/spherex.html",
    "irsa_spectrophotometry":
        "https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html",
    "aws_registry": "https://registry.opendata.aws/spherex-qr/",
    "aws_level2_list": (
        "https://nasa-irsa-spherex.s3.amazonaws.com/"
        "?list-type=2&prefix=qr2%2Flevel2%2F&delimiter=%2F&max-keys=5"
    ),
}

H = 6.62607015e-34
C = 2.99792458e8
KB = 1.380649e-23
SB = 5.670374419184e-8
L_SUN = 3.828e26
PC = 3.085677581491367e16
WARM_UM = 4.8
EXPECTED_DETECTOR_BANDS = {f"SPHEREx-D{index}" for index in range(1, 7)}
QR2_PIPELINE_VERSIONS = ("6.4", "6.5.3", "6.5.4", "6.5.5", "6.5.6", "6.5.7")


@dataclass(frozen=True)
class Position:
    slot: str
    group: str
    pair: int
    ra: float
    dec: float
    source_id: str
    w2mag: float
    predicted_excess_ujy: float | None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def persist_bytes(path: Path, data: bytes) -> dict[str, int | str]:
    """Atomically store exact response bytes, then prove the bytes on disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.tmp-", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary_path.read_bytes() != data:
            raise RuntimeError(f"temporary artifact differs before replace: {path.name}")
        temporary_path.replace(path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    proof: dict[str, int | str] = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if proof != {"bytes": len(data), "sha256": sha256_bytes(data)}:
        raise RuntimeError(f"stored artifact proof mismatch: {path.name}")
    return proof


def verify_stored_proof(path: Path, proof: dict[str, int | str]) -> None:
    observed = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if observed != proof:
        raise RuntimeError(f"stored artifact changed during run: {path.name}")


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("empty values")
    ordered = sorted(values)
    index = fraction * (len(ordered) - 1)
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def parse_pm13_bytes(data: bytes) -> list[tuple[float, float]]:
    header: list[str] | None = None
    rows: list[tuple[float, float]] = []
    for line in data.decode("utf-8").splitlines():
        if line.startswith("#SpT") and header is None:
            header = line.lstrip("#").split()
        elif header and line and not line.startswith("#"):
            parts = line.split()
            if len(parts) != len(header):
                continue
            row = dict(zip(header, parts))
            try:
                mg = float(row["M_G"].replace(":", ""))
                log_l = float(row["logL"].replace(":", ""))
            except (KeyError, ValueError):
                continue
            if math.isfinite(mg) and math.isfinite(log_l):
                rows.append((mg, log_l))
    if len(rows) < 2:
        raise ValueError("could not parse the PM13 M_G/logL locus")
    return sorted(set(rows))


def parse_pm13(path: Path = PM13) -> list[tuple[float, float]]:
    return parse_pm13_bytes(path.read_bytes())


def interpolate(points: list[tuple[float, float]], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in itertools.pairwise(points):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise AssertionError("interpolation interval not found")


def dust_flux_ujy(row: dict[str, str], locus: list[tuple[float, float]],
                  wavelength_um: float = WARM_UM) -> float:
    """Single-blackbody excess flux, using the screen's bolometric normalization."""
    temperature = float(row["t_ds"])
    gamma = float(row["gamma"])
    distance_pc = float(row["r_med_geo"])
    log_l = interpolate(locus, float(row["M_G"]))
    nu = C / (wavelength_um * 1e-6)
    b_nu = 2 * H * nu**3 / C**2 / math.expm1(H * nu / (KB * temperature))
    f_bol = gamma * 10**log_l * L_SUN / (4 * math.pi * (distance_pc * PC)**2)
    f_nu_jy = f_bol * math.pi * b_nu / (SB * temperature**4) / 1e-26
    return f_nu_jy * 1e6


def angular_sep_deg(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    a1, d1, a2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    cosine = (math.sin(d1) * math.sin(d2)
              + math.cos(d1) * math.cos(d2) * math.cos(a1 - a2))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def load_ranked_targets_proved() -> tuple[
    list[dict[str, str]], list[float], dict[str, dict[str, int | str]]
]:
    pm13_bytes = PM13.read_bytes()
    catalog_bytes = CATALOG.read_bytes()
    locus = parse_pm13_bytes(pm13_bytes)
    rows = list(
        csv.DictReader(io.StringIO(catalog_bytes.decode("utf-8"), newline=""))
    )
    for row in rows:
        row["_predicted_excess_ujy"] = str(dust_flux_ujy(row, locus))
    rows.sort(key=lambda r: float(r["_predicted_excess_ujy"]), reverse=True)
    proofs = {
        "catalog": {
            "bytes": len(catalog_bytes),
            "sha256": sha256_bytes(catalog_bytes),
        },
        "pm13_locus": {
            "bytes": len(pm13_bytes),
            "sha256": sha256_bytes(pm13_bytes),
        },
    }
    return rows, [float(r["_predicted_excess_ujy"]) for r in rows], proofs


def load_ranked_targets() -> tuple[list[dict[str, str]], list[float]]:
    rows, fluxes, _ = load_ranked_targets_proved()
    return rows, fluxes


def is_control_candidate(row: dict[str, str]) -> bool:
    try:
        w1, w2 = (float(row[k]) for k in ("w1mpro", "w2mpro"))
        w2e = float(row["w2mpro_error"])
        return (
            row["cc_flags"].strip() in {"0000", "0"}
            and int(float(row["ext_flag"])) == 0
            and float(row["ruwe"]) < 1.4
            and float(row["classprob_dsc_combmod_star"]) > 0.9
            and abs(w1 - w2) <= 0.15
            and w2e <= 0.12
        )
    except (KeyError, TypeError, ValueError):
        return False


def select_controls(
    targets: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, int | str]]:
    """Greedily choose unique, nearby, W2-matched photospheres from the parent harvest."""
    target_ids = {row["source_id"] for row in targets}
    options: list[list[tuple[float, dict[str, str], float, float]]] = [
        [] for _ in targets
    ]
    tree_hash = hashlib.sha256()
    total_bytes = 0
    paths = sorted(CONTROL_CELLS.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"no control cells under {CONTROL_CELLS}")
    for path in paths:
        data = path.read_bytes()
        total_bytes += len(data)
        digest = sha256_bytes(data)
        tree_hash.update(f"{path.name}\t{len(data)}\t{digest}\n".encode())
        for row in csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")):
            if row.get("datalinkID") in target_ids or not is_control_candidate(row):
                continue
            try:
                ra, dec, w2 = (float(row[k]) for k in ("ra", "dec", "w2mpro"))
            except (KeyError, ValueError):
                continue
            for idx, target in enumerate(targets):
                delta_w2 = abs(w2 - float(target["w2mpro"]))
                if delta_w2 > 0.25:
                    continue
                sep = angular_sep_deg(
                    ra, dec, float(target["ra"]), float(target["dec"])
                )
                if not 0.10 <= sep <= 2.0:
                    continue
                score = (delta_w2 / 0.10)**2 + (sep / 1.0)**2
                options[idx].append((score, row.copy(), sep, delta_w2))
    chosen: list[dict[str, str]] = []
    used: set[str] = set()
    for candidate_options in options:
        for _, row, sep, delta_w2 in sorted(candidate_options, key=lambda item: item[0]):
            source_id = row["datalinkID"]
            if source_id in used:
                continue
            row["_match_sep_deg"] = str(sep)
            row["_match_delta_w2_mag"] = str(delta_w2)
            chosen.append(row)
            used.add(source_id)
            break
        else:
            raise RuntimeError("no unique nearby W2-matched photospheric control")
    return chosen, {
        "files": len(paths),
        "bytes": total_bytes,
        "tree_sha256": tree_hash.hexdigest(),
    }


def current_control_tree_proof() -> dict[str, int | str]:
    paths = sorted(CONTROL_CELLS.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"no control cells under {CONTROL_CELLS}")
    tree_hash = hashlib.sha256()
    total_bytes = 0
    for path in paths:
        data = path.read_bytes()
        total_bytes += len(data)
        tree_hash.update(
            f"{path.name}\t{len(data)}\t{sha256_bytes(data)}\n".encode()
        )
    return {
        "files": len(paths),
        "bytes": total_bytes,
        "tree_sha256": tree_hash.hexdigest(),
    }


def verify_core_input_proofs(proofs: dict[str, dict[str, int | str]]) -> None:
    observed = {
        "catalog": {"bytes": CATALOG.stat().st_size, "sha256": sha256_file(CATALOG)},
        "pm13_locus": {"bytes": PM13.stat().st_size, "sha256": sha256_file(PM13)},
        "control_cells": current_control_tree_proof(),
    }
    if observed != proofs:
        raise RuntimeError("catalog, locus, or control-cell input changed during analysis")


def build_manifest() -> dict[str, object]:
    ranked, fluxes, target_proofs = load_ranked_targets_proved()
    targets = ranked[:3]
    controls, control_tree_proof = select_controls(targets)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for index, (target, control) in enumerate(zip(targets, controls), start=1):
        rows.extend([
            {
                "slot": f"pair_{index:02d}_target",
                "group": "target",
                "pair": index,
                "ra": target["ra"],
                "dec": target["dec"],
                "source_id": target["source_id"],
                "w2mag": target["w2mpro"],
                "predicted_excess_ujy": target["_predicted_excess_ujy"],
                "match_sep_deg": "",
                "match_delta_w2_mag": "",
            },
            {
                "slot": f"pair_{index:02d}_control",
                "group": "control",
                "pair": index,
                "ra": control["ra"],
                "dec": control["dec"],
                "source_id": control["datalinkID"],
                "w2mag": control["w2mpro"],
                "predicted_excess_ujy": "",
                "match_sep_deg": control["_match_sep_deg"],
                "match_delta_w2_mag": control["_match_delta_w2_mag"],
            },
        ])
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest_bytes = buffer.getvalue().encode("utf-8")
    persist_bytes(MANIFEST, manifest_bytes)
    manifest_proof = {
        "bytes": len(manifest_bytes),
        "sha256": sha256_bytes(manifest_bytes),
    }
    return {
        "catalog_rows": len(ranked),
        "ranked_rows": ranked,
        "fluxes_ujy": fluxes,
        "core_input_proofs": {
            **target_proofs,
            "control_cells": control_tree_proof,
        },
        "manifest_sha256": manifest_proof["sha256"],
        "private_manifest_proof": manifest_proof,
        "private_rows": len(rows),
        "control_match_separations_deg": [float(r["_match_sep_deg"]) for r in controls],
        "control_match_delta_w2_mag": [float(r["_match_delta_w2_mag"]) for r in controls],
    }


def parse_manifest_bytes(manifest_bytes: bytes) -> list[Position]:
    rows = list(csv.DictReader(io.StringIO(manifest_bytes.decode("utf-8"))))
    return [
        Position(
            slot=row["slot"], group=row["group"], pair=int(row["pair"]),
            ra=float(row["ra"]), dec=float(row["dec"]), source_id=row["source_id"],
            w2mag=float(row["w2mag"]),
            predicted_excess_ujy=(float(row["predicted_excess_ujy"])
                                  if row["predicted_excess_ujy"] else None),
        )
        for row in rows
    ]


def read_manifest() -> list[Position]:
    return parse_manifest_bytes(MANIFEST.read_bytes())


def get_bytes(url: str, timeout: int = 180) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "astronomy-spherex-m0/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def tap_query(adql: str) -> bytes:
    query = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql,
    })
    return get_bytes(f"{TAP_SYNC}?{query}")


def parse_coverage_csv(data: bytes) -> dict[str, dict[str, float]]:
    text = data.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        lower = {key.lower(): value for key, value in row.items()}
        band = lower["band"].strip()
        if not band:
            raise ValueError("coverage response contains an empty band")
        if band in result:
            raise ValueError(f"duplicate coverage band: {band}")
        count_text = lower["n_images"].strip()
        if not count_text.isdigit():
            raise ValueError(f"coverage count is not a nonnegative integer: {count_text!r}")
        count = int(count_text)
        min_mjd = float(lower["min_mjd"])
        max_mjd = float(lower["max_mjd"])
        if not math.isfinite(min_mjd) or not math.isfinite(max_mjd):
            raise ValueError("coverage MJD bounds must be finite")
        if min_mjd > max_mjd:
            raise ValueError("coverage MJD bounds are inverted")
        result[band] = {
            "n_images": count,
            "min_mjd": min_mjd,
            "max_mjd": max_mjd,
        }
    return result


def validate_qr2_versions(data: bytes) -> list[str]:
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    versions = sorted(
        {
            str(row.get("provenance_version", "")).strip()
            for row in rows
            if str(row.get("provenance_version", "")).strip()
        }
    )
    missing = sorted(set(QR2_PIPELINE_VERSIONS) - set(versions))
    if missing:
        raise ValueError(f"frozen QR2 pipeline versions absent from TAP: {missing}")
    return versions


def coverage_metrics(bands: dict[str, dict[str, float]]) -> dict[str, object]:
    positive_detectors = {
        band
        for band, values in bands.items()
        if band in EXPECTED_DETECTOR_BANDS and int(values["n_images"]) > 0
    }
    return {
        "positive_detector_count": len(positive_detectors),
        "has_all_d1_d6": positive_detectors == EXPECTED_DETECTOR_BANDS,
        "has_d5_d6": {"SPHEREx-D5", "SPHEREx-D6"}.issubset(positive_detectors),
    }


def decide_coverage_verdict(
    n_above_floor: int,
    targets: list[dict[str, object]],
    controls: list[dict[str, object]],
) -> str:
    """Apply detector/runtime gates to every row needed by the next experiment."""

    target_by_pair = {int(row["pair"]): row for row in targets}
    control_by_pair = {int(row["pair"]): row for row in controls}
    if (
        len(targets) != 3
        or len(controls) != 3
        or set(target_by_pair) != {1, 2, 3}
        or set(control_by_pair) != {1, 2, 3}
    ):
        return "BLOCKED"

    def warm_ready(row: dict[str, object]) -> bool:
        return bool(row["has_d5_d6"]) and float(row["warm_runtime_hours_est"]) <= 6

    lead = target_by_pair[1]
    if n_above_floor == 0 or not bool(lead["has_d5_d6"]):
        return "KILL"
    if n_above_floor >= 10:
        return (
            "GO"
            if all(bool(row["has_all_d1_d6"]) for row in targets)
            and statistics.median(
                float(row["warm_runtime_hours_est"]) for row in targets
            )
            <= 6
            and all(warm_ready(row) for row in controls)
            else "KILL"
        )

    if n_above_floor != 1:
        # With two to nine above-floor rows, pair 2 is not the frozen
        # second-ranked subthreshold falsifier. A new manifest/protocol is needed.
        return "BLOCKED"

    # NARROW's exact next experiment is lead target + pair-1 control + the
    # second-ranked subthreshold target. All three must be executable now.
    if (
        bool(lead["has_all_d1_d6"])
        and warm_ready(lead)
        and warm_ready(control_by_pair[1])
        and warm_ready(target_by_pair[2])
    ):
        return "NARROW/PIVOT"
    return "KILL"


def validate_public_sources(
    payloads: dict[str, bytes], schema_raw: bytes
) -> dict[str, bool]:
    required_markers = {
        "irsa_mission": (b"SPHEREx: An All-Sky Spectral Survey", b"overview_qr.html"),
        "irsa_spectrophotometry": (b"Spectrophotometry Tool", b"The Tractor"),
        "aws_registry": (b"SPHEREx Quick Release", b"nasa-irsa-spherex/qr2/level2"),
        "aws_level2_list": (b"<ListBucketResult", b"<Prefix>qr2/level2/</Prefix>"),
    }
    checks: dict[str, bool] = {}
    for name, markers in required_markers.items():
        payload = payloads.get(name, b"")
        passed = all(marker in payload for marker in markers)
        if not passed:
            raise ValueError(f"official source validation failed: {name}")
        checks[name] = True

    schema_rows = list(
        csv.DictReader(io.StringIO(schema_raw.decode("utf-8-sig")))
    )
    observed = {
        (row.get("table_name", "").lower(), row.get("column_name", "").lower())
        for row in schema_rows
    }
    required_columns = {
        ("spherex.plane", "planeid"),
        ("spherex.plane", "energy_bandpassname"),
        ("spherex.plane", "time_bounds_lower"),
        ("spherex.plane", "poly"),
        ("spherex.plane", "dataproducttype"),
        ("spherex.plane", "calibrationlevel"),
        ("spherex.plane", "provenance_version"),
        ("spherex.artifact", "planeid"),
        ("spherex.artifact", "producttype"),
    }
    if not required_columns.issubset(observed):
        missing = sorted(required_columns - observed)
        raise ValueError(f"IRSA TAP schema lacks required columns: {missing}")
    checks["irsa_tap_required_columns"] = True
    return checks


def fetch_coordinate_free_sources() -> tuple[
    dict[str, dict[str, object]],
    dict[str, bool],
    dict[Path, dict[str, int | str]],
]:
    """Fetch, atomically persist, and prove every coordinate-free live input."""

    RAW.mkdir(parents=True, exist_ok=True)
    source_digests: dict[str, dict[str, object]] = {}
    source_payloads: dict[str, bytes] = {}
    raw_proofs: dict[Path, dict[str, int | str]] = {}
    for name, url in OFFICIAL_URLS.items():
        path = RAW / f"official_{name}.raw"
        proof = persist_bytes(path, get_bytes(url))
        raw_proofs[path] = proof
        source_payloads[name] = path.read_bytes()
        source_digests[name] = {"url": url, **proof}

    schema_adql = (
        "SELECT table_name, column_name, datatype FROM TAP_SCHEMA.columns "
        "WHERE table_name = 'spherex.plane' OR table_name = 'spherex.artifact' "
        "ORDER BY table_name, column_name"
    )
    schema_path = RAW / "tap_schema.csv"
    schema_proof = persist_bytes(schema_path, tap_query(schema_adql))
    raw_proofs[schema_path] = schema_proof
    schema_raw = schema_path.read_bytes()
    source_digests["irsa_tap_schema"] = {
        "url": TAP_SYNC,
        "query_sha256": sha256_bytes(schema_adql.encode()),
        **schema_proof,
    }

    versions_adql = (
        "SELECT DISTINCT provenance_version FROM spherex.plane "
        "WHERE dataproducttype = 'image' AND calibrationlevel = 2 "
        "ORDER BY provenance_version"
    )
    versions_path = RAW / "tap_pipeline_versions.csv"
    versions_proof = persist_bytes(versions_path, tap_query(versions_adql))
    raw_proofs[versions_path] = versions_proof
    observed_versions = validate_qr2_versions(versions_path.read_bytes())
    source_digests["irsa_tap_pipeline_versions"] = {
        "url": TAP_SYNC,
        "query_sha256": sha256_bytes(versions_adql.encode()),
        "observed_versions": observed_versions,
        "frozen_qr2_versions": list(QR2_PIPELINE_VERSIONS),
        **versions_proof,
    }

    public_source_validation = validate_public_sources(source_payloads, schema_raw)
    public_source_validation["frozen_qr2_versions_observed"] = True
    return source_digests, public_source_validation, raw_proofs


def coverage_query(position: Position) -> str:
    versions = ", ".join(f"'{version}'" for version in QR2_PIPELINE_VERSIONS)
    return f"""
SELECT p.energy_bandpassname AS band, COUNT(DISTINCT p.planeid) AS n_images,
       MIN(p.time_bounds_lower) AS min_mjd, MAX(p.time_bounds_lower) AS max_mjd
FROM spherex.plane p JOIN spherex.artifact a ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {position.ra:.10f}, {position.dec:.10f}), p.poly)
  AND p.dataproducttype = 'image' AND p.calibrationlevel = 2
  AND p.provenance_version IN ({versions}) AND a.producttype = 'science'
GROUP BY p.energy_bandpassname
""".strip()


def warm_reference_paths() -> list[Path]:
    paths = sorted((DYSON / "out").glob("w3_spherex_*_sed.csv"))
    if len(paths) != 2:
        raise ValueError(f"expected two existing QR2 reference extractions, found {len(paths)}")
    return paths


def empirical_warm_errors_ujy() -> tuple[list[float], list[dict[str, int | str]]]:
    errors: list[float] = []
    paths = warm_reference_paths()
    proofs_before = [
        {
            "path": path.relative_to(REPO).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in paths
    ]
    for path in paths:
        invvar = 0.0
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if float(row["lam_um"]) < 4.4:
                    continue
                if int(row["center_flag"]) & ~(1 << 21):
                    continue
                error_ujy = float(row["err_jy"]) * 1e6
                if math.isfinite(error_ujy) and error_ujy > 0:
                    invvar += 1.0 / error_ujy**2
        if invvar <= 0:
            raise ValueError("an existing extraction has no usable warm-window errors")
        errors.append(1.0 / math.sqrt(invvar))
    proofs_after = [
        {
            "path": path.relative_to(REPO).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in paths
    ]
    if proofs_after != proofs_before:
        raise RuntimeError("warm-error reference input changed during analysis")
    return errors, proofs_after


def aggregate(values: Iterable[float]) -> dict[str, float]:
    seq = list(values)
    return {
        "min": min(seq), "median": statistics.median(seq), "max": max(seq),
    }


def require_manifest_authorization(observed_sha256: str, authorized_sha256: str | None) -> None:
    """Require an exact, explicit authorization token before exporting positions."""
    if not authorized_sha256:
        raise PermissionError(
            "coordinate-bearing probe requires --authorize-private-manifest-sha256"
        )
    if authorized_sha256.lower() != observed_sha256.lower():
        raise PermissionError(
            "authorized private-manifest SHA-256 does not match the exact outbound payload"
        )


def run_probe(authorized_manifest_sha256: str | None = None) -> dict[str, object]:
    manifest_stats = build_manifest()
    manifest_bytes = MANIFEST.read_bytes()
    observed_manifest_sha256 = sha256_bytes(manifest_bytes)
    if {
        "bytes": len(manifest_bytes),
        "sha256": observed_manifest_sha256,
    } != manifest_stats["private_manifest_proof"]:
        raise RuntimeError("private manifest changed after local construction")
    require_manifest_authorization(
        observed_manifest_sha256, authorized_manifest_sha256
    )
    positions = parse_manifest_bytes(manifest_bytes)
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    source_digests, public_source_validation, raw_proofs = (
        fetch_coordinate_free_sources()
    )

    coverage: list[dict[str, object]] = []
    response_digests: list[str] = []
    for index, position in enumerate(positions, start=1):
        raw = tap_query(coverage_query(position))
        raw_path = RAW / f"coverage_{index:02d}.csv"
        raw_proof = persist_bytes(raw_path, raw)
        raw_proofs[raw_path] = raw_proof
        digest = str(raw_proof["sha256"])
        response_digests.append(digest)
        bands = parse_coverage_csv(raw_path.read_bytes())
        detector_metrics = coverage_metrics(bands)
        total = sum(int(item["n_images"]) for item in bands.values())
        warm = sum(
            int(item["n_images"]) for band, item in bands.items()
            if band.upper().endswith(("D5", "D6"))
        )
        coverage.append({
            "group": position.group,
            "pair": position.pair,
            "band_count": len(bands),
            **detector_metrics,
            "total_images": total,
            "warm_images_d5_d6": warm,
            "all_band_runtime_hours_est": 0.000463 * total + 0.013,
            "warm_runtime_hours_est": 0.000463 * warm + 0.013,
            "raw_sha256": digest,
        })

    ranked = list(manifest_stats.pop("ranked_rows"))
    fluxes = list(manifest_stats.pop("fluxes_ujy"))
    warm_errors, warm_reference_proofs = empirical_warm_errors_ujy()
    five_sigma_floor = 5 * max(warm_errors)
    n_above_floor = sum(value >= five_sigma_floor for value in fluxes)
    targets = [row for row in coverage if row["group"] == "target"]
    controls = [row for row in coverage if row["group"] == "control"]
    verdict = decide_coverage_verdict(n_above_floor, targets, controls)

    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "claim_scope": (
            "aggregate feasibility; target ranking is reconstructible from the existing "
            "tracked upstream catalog"
        ),
        "inputs": {
            "catalog": {
                "rows": len(fluxes),
                **manifest_stats["core_input_proofs"]["catalog"],
            },
            "pm13_locus": manifest_stats["core_input_proofs"]["pm13_locus"],
            "warm_error_references": warm_reference_proofs,
            "control_cells": manifest_stats["core_input_proofs"]["control_cells"],
            "private_manifest_sha256": manifest_stats["private_manifest_proof"]["sha256"],
        },
        "official_sources": source_digests,
        "public_source_validation": public_source_validation,
        "physical_kill_check": {
            "fitted_temperature_k": aggregate(
                float(row["t_ds"]) for row in ranked
            ),
            "predicted_4p8um_excess_ujy": {
                **aggregate(fluxes),
                "p90": percentile(fluxes, 0.90),
                "second_highest": sorted(fluxes, reverse=True)[1],
            },
            "existing_aperture_stacked_1sigma_ujy": aggregate(warm_errors),
            "conservative_5sigma_floor_ujy": five_sigma_floor,
            "rows_above_floor": n_above_floor,
        },
        "blinded_probe": {
            "target_rows": len(targets),
            "control_rows": len(controls),
            "control_selection_quality": {
                "count": len(controls),
                "all_separations_within_frozen_bounds": all(
                    0.10 <= value <= 2.0
                    for value in manifest_stats["control_match_separations_deg"]
                ),
                "all_w2_deltas_within_frozen_bound": all(
                    value <= 0.25
                    for value in manifest_stats["control_match_delta_w2_mag"]
                ),
            },
            "target_full_six_detector_count": sum(
                bool(row["has_all_d1_d6"]) for row in targets
            ),
            "control_full_six_detector_count": sum(
                bool(row["has_all_d1_d6"]) for row in controls
            ),
            "target_total_images": aggregate(
                float(row["total_images"]) for row in targets
            ),
            "target_warm_images_d5_d6": aggregate(
                float(row["warm_images_d5_d6"]) for row in targets
            ),
            "target_all_band_runtime_hours_est": aggregate(
                float(row["all_band_runtime_hours_est"]) for row in targets
            ),
            "target_warm_runtime_hours_est": aggregate(
                float(row["warm_runtime_hours_est"]) for row in targets
            ),
            "control_total_images": aggregate(
                float(row["total_images"]) for row in controls
            ),
            "raw_coverage_response_sha256": response_digests,
        },
        "decision": {
            "old_premise": "KILL: forced photometry is an official IRSA capability, not novelty",
            "survey_scale": "KILL: the catalogue-wide cold-excess use case is below 5 microns",
            "surviving_test": (
                "Run only the leading warm-tail row, its nearby photospheric control, and the "
                "second-ranked subthreshold falsifier through the official IRSA Spectrophotometry "
                "Tool over D5+D6; grade flags, fit_ql, flux_bkg, and the predeclared flux contrast."
            ),
            "publication_or_submission_authorized": False,
            "privacy_note": (
                "The existing tracked upstream catalog and tracked ranking code make the target "
                "ranking reproducible. The gate protects the exact outbound IRSA payload and "
                "gitignored control identities; it does not claim target secrecy from readers."
            ),
        },
    }
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    forbidden = ("source_id", '"ra"', '"dec"', "designation")
    if any(token in serialized.lower() for token in forbidden):
        raise AssertionError("tracked summary contains an identifier/coordinate field")
    verify_core_input_proofs(manifest_stats["core_input_proofs"])
    verify_stored_proof(MANIFEST, manifest_stats["private_manifest_proof"])
    for path, proof in raw_proofs.items():
        verify_stored_proof(path, proof)
    summary_proof = persist_bytes(SUMMARY, serialized.encode("utf-8"))
    verify_stored_proof(SUMMARY, summary_proof)
    return result


def run_public_probe() -> dict[str, object]:
    """Run the coordinate-free part of M0 and stop honestly at the privacy gate."""
    manifest_stats = build_manifest()  # local-only; proves controls can be selected
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    source_digests, public_source_validation, raw_proofs = (
        fetch_coordinate_free_sources()
    )

    ranked = list(manifest_stats.pop("ranked_rows"))
    fluxes = list(manifest_stats.pop("fluxes_ujy"))
    warm_errors, warm_reference_proofs = empirical_warm_errors_ujy()
    five_sigma_floor = 5 * max(warm_errors)
    n_above_floor = sum(value >= five_sigma_floor for value in fluxes)
    if n_above_floor == 0:
        scientific_disposition = "KILL"
    elif n_above_floor == 1:
        scientific_disposition = "NARROW/PIVOT"
    elif n_above_floor < 10:
        scientific_disposition = "BLOCKED_PROTOCOL_REQUIRES_SUBTHRESHOLD_FALSIFIER"
    else:
        scientific_disposition = "GO"

    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "BLOCKED",
        "scientific_disposition_before_coverage_gate": scientific_disposition,
        "claim_scope": (
            "aggregate feasibility; target ranking is reconstructible from the existing "
            "tracked upstream catalog"
        ),
        "inputs": {
            "catalog": {
                "rows": len(fluxes),
                **manifest_stats["core_input_proofs"]["catalog"],
            },
            "pm13_locus": manifest_stats["core_input_proofs"]["pm13_locus"],
            "warm_error_references": warm_reference_proofs,
            "control_cells": manifest_stats["core_input_proofs"]["control_cells"],
            "private_manifest_sha256": manifest_stats["private_manifest_proof"]["sha256"],
        },
        "official_sources": source_digests,
        "public_source_validation": public_source_validation,
        "physical_kill_check": {
            "fitted_temperature_k": aggregate(float(row["t_ds"]) for row in ranked),
            "predicted_4p8um_excess_ujy": {
                **aggregate(fluxes),
                "p90": percentile(fluxes, 0.90),
                "second_highest": sorted(fluxes, reverse=True)[1],
            },
            "existing_aperture_stacked_1sigma_ujy": aggregate(warm_errors),
            "conservative_5sigma_floor_ujy": five_sigma_floor,
            "rows_above_floor": n_above_floor,
        },
        "blinded_probe": {
            "private_rows_prepared_locally": manifest_stats["private_rows"],
            "target_rows": 3,
            "control_rows": 3,
            "control_selection_quality": {
                "count": 3,
                "all_separations_within_frozen_bounds": all(
                    0.10 <= value <= 2.0
                    for value in manifest_stats["control_match_separations_deg"]
                ),
                "all_w2_deltas_within_frozen_bound": all(
                    value <= 0.25
                    for value in manifest_stats["control_match_delta_w2_mag"]
                ),
            },
            "position_coverage_status": "NOT_QUERIED_OUTBOUND_QUERY_GATE",
            "coordinates_sent_externally": 0,
        },
        "decision": {
            "old_premise": "KILL: forced photometry is an official IRSA capability, not novelty",
            "survey_scale": "KILL: the catalogue-wide cold-excess use case is below 5 microns",
            "why_blocked": (
                "The preregistered position-coverage test would send six target/control "
                "coordinates to IRSA. That exact outward payload was not authorized, so no "
                "coordinate-bearing request was sent."
            ),
            "exact_unblock_action": (
                "Approve anonymous IRSA TAP coverage queries for the six rows in the gitignored "
                "private manifest; then rerun the probe and apply the frozen coverage/runtime gates."
            ),
            "next_science_step_if_unblocked": (
                "If the coverage gate passes, run only the leading warm-tail row, its nearby "
                "photospheric control, and the second-ranked subthreshold falsifier through the "
                "official IRSA Spectrophotometry Tool over D5+D6; grade flags, fit_ql, flux_bkg, "
                "and the predeclared flux contrast."
            ),
            "publication_or_submission_authorized": False,
            "privacy_note": (
                "The existing tracked upstream catalog and tracked ranking code make the target "
                "ranking reproducible. The gate protects the exact outbound IRSA payload and "
                "gitignored control identities; it does not claim target secrecy from readers."
            ),
        },
    }
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    forbidden = ("source_id", '"ra"', '"dec"', "designation")
    if any(token in serialized.lower() for token in forbidden):
        raise AssertionError("tracked summary contains an identifier/coordinate field")
    verify_core_input_proofs(manifest_stats["core_input_proofs"])
    verify_stored_proof(MANIFEST, manifest_stats["private_manifest_proof"])
    for path, proof in raw_proofs.items():
        verify_stored_proof(path, proof)
    summary_proof = persist_bytes(SUMMARY, serialized.encode("utf-8"))
    verify_stored_proof(SUMMARY, summary_proof)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("manifest", "public-probe", "probe"))
    parser.add_argument(
        "--authorize-private-manifest-sha256",
        help=(
            "exact SHA-256 of the locally prepared six-row private manifest; required "
            "for the coordinate-bearing probe after explicit approval of that payload"
        ),
    )
    args = parser.parse_args()
    if args.command == "manifest":
        stats = build_manifest()
        print(json.dumps({
            "catalog_rows": stats["catalog_rows"],
            "manifest_sha256": stats["manifest_sha256"],
            "private_rows": stats["private_rows"],
        }, indent=2))
    elif args.command == "public-probe":
        result = run_public_probe()
        print(json.dumps({
            "verdict": result["verdict"],
            "scientific_disposition_before_coverage_gate":
                result["scientific_disposition_before_coverage_gate"],
            "result": str(SUMMARY),
        }, indent=2))
    else:
        result = run_probe(args.authorize_private_manifest_sha256)
        print(json.dumps({
            "verdict": result["verdict"],
            "result": str(SUMMARY),
        }, indent=2))


if __name__ == "__main__":
    main()
