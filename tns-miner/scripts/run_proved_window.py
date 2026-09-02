"""Run and seal one private, provenance-proved TNS-miner campaign.

This is the publication-quality entry point.  It gives every campaign its own
gitignored data/output directories, holds an inter-process lock for the entire
run, captures detailed child output privately, authenticates the completed
products, and writes a digest inventory of every retained byte.

No TNS write endpoint exists in this workflow.  Candidate coordinates and
identifiers are never printed by this orchestrator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import (  # noqa: E402
    atomic_write,
    load_cache_contract,
    load_proved_output,
    sha256_file,
    validated_tag,
    write_cache,
)
from tns_snapshot import REQUIRED_COLUMNS, read_snapshot  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
LOCK = ROOT / "data" / ".proved-run.lock"
RUN_SCHEMA = 1
SECONDS_PER_DAY = 86400.0
UNIX_EPOCH_MJD = 40587.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date {value!r}") from exc


def _validate_closed_year(start: date, end_exclusive: date) -> None:
    if start.day != 1 or end_exclusive.day != 1:
        raise ValueError("closed TNS interval must begin and end on month boundaries")
    if end_exclusive != date(start.year + 1, start.month, 1):
        raise ValueError("closed TNS interval must be exactly twelve calendar months")


def _current_mjd() -> float:
    return datetime.now(timezone.utc).timestamp() / SECONDS_PER_DAY + UNIX_EPOCH_MJD


class ExclusiveRunLock:
    """Portable non-blocking advisory lock held for the full campaign."""

    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self) -> "ExclusiveRunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0, os.SEEK_END)
        if self.handle.tell() == 0:
            self.handle.write(b"\0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise RuntimeError(
                "another TNS-miner proved campaign is already running"
            ) from exc
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        if self.handle is None:
            return
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()
        self.handle = None


def _script_digests() -> dict[str, str]:
    return {
        path.name: sha256_file(path) for path in sorted((ROOT / "scripts").glob("*.py"))
    }


def _campaign_contract(
    *,
    tag: str,
    mjd_start: float,
    mjd_end: float,
    closed_start: date,
    closed_end_exclusive: date,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_SCHEMA,
        "tag": tag,
        "alert_mjd_start": float(mjd_start),
        "alert_mjd_end": float(mjd_end),
        "closed_tns_discovery_start": closed_start.isoformat(),
        "closed_tns_discovery_end_exclusive": closed_end_exclusive.isoformat(),
        "code_sha256": _script_digests(),
        "private": True,
        "submission_allowed": False,
    }


def _prepare_run(
    run_root: Path,
    contract: dict[str, Any],
    *,
    resume: bool,
) -> tuple[Path, Path, Path]:
    contract_path = run_root / "run-contract.json"
    sealed_path = run_root / "SEALED.json"
    if sealed_path.exists():
        raise RuntimeError(f"proved run is already sealed: {run_root}")
    if run_root.exists():
        if not resume:
            raise RuntimeError(
                f"run directory already exists: {run_root}; inspect it, then use --resume"
            )
        try:
            saved = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"cannot authenticate resumable run {run_root}") from exc
        if saved.get("campaign") != contract:
            raise RuntimeError("resume contract or science-code digest changed")
    else:
        run_root.mkdir(parents=True)
        atomic_write(
            contract_path,
            (
                json.dumps(
                    {
                        "created_at_utc": _utc_now(),
                        "host": socket.gethostname(),
                        "campaign": contract,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
        )
    data_dir = run_root / "data"
    out_dir = run_root / "out"
    data_dir.mkdir(exist_ok=True)
    out_dir.mkdir(exist_ok=True)
    return data_dir, out_dir, run_root / "private-run.log"


def _pump_private_output(stream, destination) -> None:
    for block in iter(lambda: stream.read(64 * 1024), b""):
        destination.write(block)
        destination.flush()


def _run_step(
    label: str,
    script: str,
    arguments: list[str],
    *,
    environment: dict[str, str],
    log_path: Path,
) -> None:
    print(f"{label}: started; detailed output is private", flush=True)
    started = time.monotonic()
    with log_path.open("ab") as log:
        log.write(f"\n[{_utc_now()}] {label}\n".encode("utf-8"))
        log.flush()
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts" / script), *arguments],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert process.stdout is not None
        reader = threading.Thread(
            target=_pump_private_output,
            args=(process.stdout, log),
            daemon=True,
        )
        reader.start()
        next_heartbeat = time.monotonic() + 45
        try:
            while process.poll() is None:
                time.sleep(1)
                if time.monotonic() >= next_heartbeat:
                    elapsed = (time.monotonic() - started) / 60
                    print(f"{label}: still running ({elapsed:.1f} min)", flush=True)
                    next_heartbeat = time.monotonic() + 45
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
            raise
        finally:
            reader.join(timeout=15)
        if process.returncode:
            raise RuntimeError(
                f"{label} failed closed with exit {process.returncode}; "
                f"details remain in {log_path}"
            )
    elapsed = (time.monotonic() - started) / 60
    print(f"{label}: complete ({elapsed:.1f} min)", flush=True)


def _build_closed_tns_window(
    data_dir: Path,
    *,
    start: date,
    end_exclusive: date,
) -> tuple[Path, dict[str, Any]]:
    tns_dir = data_dir / "tns"
    pointer = json.loads((tns_dir / "tns_12mo.meta.json").read_text(encoding="utf-8"))
    source = (tns_dir / str(pointer["snapshot_file"])).resolve()
    source.relative_to((tns_dir / "snapshots").resolve())
    if sha256_file(source) != pointer.get("snapshot_sha256"):
        raise RuntimeError("fresh TNS source snapshot digest mismatch")
    if date.fromisoformat(pointer["discovery_start_date"]) > start:
        raise RuntimeError("fresh TNS source snapshot begins after closed interval")
    if date.fromisoformat(pointer["discovery_end_exclusive"]) < end_exclusive:
        raise RuntimeError("fresh TNS source snapshot does not cover closed interval")

    frame = pd.read_csv(source, dtype=str)
    if not REQUIRED_COLUMNS.issubset(frame.columns):
        raise RuntimeError("fresh TNS source snapshot lacks required columns")
    discovery = pd.to_datetime(frame["Discovery Date (UT)"], errors="coerce", utc=True)
    if discovery.isna().any():
        raise RuntimeError("fresh TNS source snapshot has invalid discovery timestamps")
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end_exclusive, tz="UTC")
    closed = frame.loc[(discovery >= start_ts) & (discovery < end_ts)].copy()
    if closed.empty:
        raise RuntimeError(
            "closed twelve-month TNS interval unexpectedly has zero rows"
        )

    output = (
        tns_dir / "closed_windows" / f"tns_{start:%Y%m%d}_{end_exclusive:%Y%m%d}.csv"
    )
    contract = {
        "discovery_start": start.isoformat(),
        "discovery_end_exclusive": end_exclusive.isoformat(),
        "source_snapshot_id": pointer["snapshot_id"],
        "source_snapshot_sha256": pointer["snapshot_sha256"],
        "selection": "Discovery Date (UT) in half-open UTC interval",
    }
    proof = write_cache(
        output,
        closed.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        kind="tns_closed_twelve_month_window",
        contract=contract,
        row_count=len(closed),
    )
    return output, proof


def _authenticate_raw_entry(
    base: Path,
    entry: dict,
    *,
    kind: str,
) -> int:
    try:
        relative = entry["path"]
        proof = entry["proof"]
        path = (base / relative).resolve()
        path.relative_to(base.resolve())
        actual = load_cache_contract(
            path,
            kind=kind,
            expected_contract=proof["contract"],
        )
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise RuntimeError(f"retained raw {kind} input failed authentication") from exc
    if actual != proof:
        raise RuntimeError(f"retained raw {kind} input proof changed")
    if proof.get("exact_http_entity_bytes") is not True:
        raise RuntimeError(f"retained raw {kind} input is not exact HTTP entity bytes")
    return path.stat().st_size


def _authenticate_and_seal(
    run_root: Path,
    data_dir: Path,
    out_dir: Path,
    *,
    tag: str,
    closed_path: Path,
    closed_proof: dict[str, Any],
) -> dict[str, Any]:
    pool_path = out_dir / f"m2_pool_{tag}.json"
    candidate_path = out_dir / f"m2_candidates_{tag}.csv"
    candidate_summary_path = out_dir / f"m2_candidates_{tag}.json"
    pin_path = out_dir / f"m2_candidates_{tag}.tns-input.json"
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    candidates = json.loads(candidate_summary_path.read_text(encoding="utf-8"))
    pin = json.loads(pin_path.read_text(encoding="utf-8"))

    load_proved_output(
        candidate_path,
        candidate_summary_path,
        kind="m2_candidate_output",
    )
    filtered_proof = pool["filtered_output_provenance"]
    actual_filtered = load_cache_contract(
        data_dir / "pool" / f"m2_filtered_{tag}.csv",
        kind="m2_filtered_pool",
        expected_contract=filtered_proof["contract"],
    )
    if actual_filtered != filtered_proof:
        raise RuntimeError("filtered pool proof changed before sealing")
    enumerator_proofs = pool["enumerator_cache_provenance"]
    for arm in ("e1", "e2"):
        proof = enumerator_proofs[arm]
        actual = load_cache_contract(
            data_dir / "pool" / f"{arm}_{tag}.csv",
            kind="m2_alerce_e1_pool" if arm == "e1" else "m2_fink_e2_pool",
            expected_contract=proof["contract"],
        )
        if actual != proof:
            raise RuntimeError(f"{arm} enumerator proof changed before sealing")

    raw_counts = {"fink_taxonomy": 0, "fink_e2_slices": 0, "tns_pages": 0}
    raw_bytes = 0
    e2_raw = enumerator_proofs["e2"]["raw_input_provenance"]
    raw_bytes += _authenticate_raw_entry(
        data_dir / "pool",
        e2_raw["taxonomy"],
        kind="m2_fink_taxonomy_raw",
    )
    raw_counts["fink_taxonomy"] = 1
    for entry in e2_raw["slices"]:
        raw_bytes += _authenticate_raw_entry(
            data_dir / "pool",
            entry,
            kind="m2_fink_latest_slice_raw",
        )
        raw_counts["fink_e2_slices"] += 1

    os.environ["TNS_MINER_DATA_DIR"] = str(data_dir)
    frozen_rows, frozen = read_snapshot(
        required_coverage_jd=float(pool["history_jd_ceiling"]),
        reference=pin["snapshot"],
    )
    current_rows, current = read_snapshot(
        required_coverage_jd=float(pool["history_jd_ceiling"]),
        max_lag_days=math.inf,
    )
    if frozen != candidates["tns_snapshot_provenance"]["frozen_dedupe"]:
        raise RuntimeError("frozen TNS snapshot proof changed before sealing")
    if current != candidates["tns_snapshot_provenance"]["operational_current"]:
        raise RuntimeError("current TNS snapshot proof changed before sealing")

    for month in frozen.get("month_inputs", []):
        for entry in month.get("raw_page_inputs", []):
            raw_bytes += _authenticate_raw_entry(
                data_dir / "tns",
                entry,
                kind="tns_search_page_raw",
            )
            raw_counts["tns_pages"] += 1

    from m1_fetch_fink import authenticate_raw_inputs, cache_provenance

    oids = list(pool["history_cache_provenance"]["object_inputs"])
    if cache_provenance(oids) != pool["history_cache_provenance"]:
        raise RuntimeError("Fink history inputs changed before sealing")
    history_raw = authenticate_raw_inputs(
        pool["history_cache_provenance"], require_exact=True
    )
    raw_counts["fink_history_responses"] = history_raw["n_raw_responses"]
    raw_bytes += history_raw["n_raw_bytes"]
    actual_closed = load_cache_contract(
        closed_path,
        kind="tns_closed_twelve_month_window",
        expected_contract=closed_proof["contract"],
    )
    if actual_closed != closed_proof:
        raise RuntimeError("closed TNS interval proof changed before sealing")

    inventory = []
    excluded = {"run-manifest.json", "run-manifest.sha256", "SEALED.json"}
    for path in sorted(run_root.rglob("*")):
        if path.is_file() and path.name not in excluded:
            inventory.append(
                {
                    "path": path.relative_to(run_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    manifest = {
        "schema_version": RUN_SCHEMA,
        "sealed_at_utc": _utc_now(),
        "private": True,
        "tag": tag,
        "files": inventory,
        "n_files": len(inventory),
        "n_bytes": sum(item["bytes"] for item in inventory),
        "authentication": {
            "candidate_output": "verified",
            "enumerator_inputs": "verified",
            "filtered_pool": "verified",
            "fink_histories": "verified",
            "tns_frozen_snapshot": "verified",
            "tns_current_snapshot": "verified",
            "closed_twelve_month_window": "verified",
            "exact_http_entity_inputs": "verified",
        },
        "raw_input_counts": raw_counts,
        "raw_input_bytes": raw_bytes,
    }
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write(run_root / "run-manifest.json", payload)
    manifest_digest = hashlib.sha256(payload).hexdigest()
    atomic_write(run_root / "run-manifest.sha256", (manifest_digest + "\n").encode())

    public_summary = {
        "schema_version": RUN_SCHEMA,
        "tag": tag,
        "private_candidate_details": True,
        "alert_mjd_window": pool["mjd_window"],
        "history_jd_ceiling": pool["history_jd_ceiling"],
        "closed_tns_discovery_window": closed_proof["contract"],
        "closed_tns_rows": closed_proof["row_count"],
        "tns_snapshot_id": frozen["snapshot_id"],
        "tns_snapshot_sha256": frozen["snapshot_sha256"],
        "tns_snapshot_rows": len(frozen_rows),
        "tns_current_snapshot_rows": len(current_rows),
        "n_E1_new": pool["n_E1_new"],
        "n_E2_outburst": pool["n_E2_outburst"],
        "n_overlap": pool["n_overlap"],
        "n_pool": pool["n_pool"],
        "n_hygiene_ok": pool["n_hygiene_ok"],
        "n_pass_M1_baseline": pool["n_pass_M1_baseline"],
        "n_pass_M2": pool["n_pass_M2"],
        "n_candidates_after_frozen_tns_veto": candidates["n_candidates"],
        "exact_raw_input_counts": raw_counts,
        "exact_raw_input_bytes": raw_bytes,
        "run_manifest_sha256": manifest_digest,
    }
    atomic_write(
        run_root / "SEALED.json",
        (json.dumps(public_summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return public_summary


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--mjd-start", required=True, type=float)
    parser.add_argument("--mjd-end", required=True, type=float)
    parser.add_argument("--closed-start", required=True, type=_parse_date)
    parser.add_argument("--closed-end-exclusive", required=True, type=_parse_date)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    tag = validated_tag(args.tag)
    _validate_closed_year(args.closed_start, args.closed_end_exclusive)
    if not all(math.isfinite(value) for value in (args.mjd_start, args.mjd_end)):
        raise ValueError("alert MJD bounds must be finite")
    if args.mjd_end - args.mjd_start != 3.0:
        raise ValueError("proved alert window must be exactly three days")
    if args.mjd_end > _current_mjd():
        raise ValueError("alert window has not closed yet")
    contract = _campaign_contract(
        tag=tag,
        mjd_start=args.mjd_start,
        mjd_end=args.mjd_end,
        closed_start=args.closed_start,
        closed_end_exclusive=args.closed_end_exclusive,
    )
    run_root = RUNS / tag

    with ExclusiveRunLock(LOCK):
        data_dir, out_dir, log_path = _prepare_run(
            run_root, contract, resume=args.resume
        )
        environment = dict(os.environ)
        environment.update(
            {
                "PYTHONUNBUFFERED": "1",
                "TNS_MINER_DATA_DIR": str(data_dir.resolve()),
                "TNS_MINER_OUT_DIR": str(out_dir.resolve()),
            }
        )
        _run_step(
            "Fresh full TNS registry snapshot",
            "m1_tns_harvest.py",
            [],
            environment=environment,
            log_path=log_path,
        )
        closed_path, closed_proof = _build_closed_tns_window(
            data_dir,
            start=args.closed_start,
            end_exclusive=args.closed_end_exclusive,
        )
        print(
            "Closed twelve-month TNS corpus: complete and retained privately",
            flush=True,
        )
        _run_step(
            "M2 alert enumeration and history proof",
            "m2_pool.py",
            [str(args.mjd_start), str(args.mjd_end), tag],
            environment=environment,
            log_path=log_path,
        )
        _run_step(
            "M2 candidate build and catalogue proof",
            "m2_candidates.py",
            [tag],
            environment=environment,
            log_path=log_path,
        )
        summary = _authenticate_and_seal(
            run_root,
            data_dir,
            out_dir,
            tag=tag,
            closed_path=closed_path,
            closed_proof=closed_proof,
        )
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
