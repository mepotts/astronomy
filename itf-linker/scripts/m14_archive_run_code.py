"""Archive the exact source bytes named by a completed M14 run fingerprint."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from m14_freeze_itf import M14_RUNS
from m14_prepare import M14DataError, digest_file, iso_utc, utc_now, write_json_atomic


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    run_dir = M14_RUNS / args.snapshot_id
    report_path = run_dir / "m14-attribution.json"
    if not report_path.is_file():
        raise M14DataError("M14 attribution report is missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = ((report.get("run_contract") or {}).get("code"))
    if not isinstance(expected, dict) or not expected:
        raise M14DataError("M14 report has no source-code hash contract")
    code_dir = run_dir / "code"
    manifest_path = code_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("run_fingerprint") != report.get("run_fingerprint"):
            raise M14DataError("archived M14 source belongs to another run fingerprint")
        for relative, expected_hash in expected.items():
            if digest_file(code_dir / relative) != expected_hash:
                raise M14DataError(f"archived M14 source digest mismatch: {relative}")
        archived = manifest.get("archived_files")
        if not isinstance(archived, dict) or not archived:
            raise M14DataError("archived M14 source manifest has no complete file map")
        for relative, expected_hash in archived.items():
            if digest_file(code_dir / relative) != expected_hash:
                raise M14DataError(f"archived M14 file digest mismatch: {relative}")
        print(f"M14 source archive already verified: {len(archived)} files")
        return 0
    if code_dir.exists() and any(code_dir.iterdir()):
        raise M14DataError("partial M14 source archive exists without a manifest")
    copied: dict[str, str] = {}
    for relative, expected_hash in expected.items():
        source = ROOT / relative
        if not source.is_file() or digest_file(source) != expected_hash:
            raise M14DataError(f"working source no longer matches M14 run: {relative}")
        destination = code_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if digest_file(destination) != expected_hash:
            raise M14DataError(f"copied M14 source digest mismatch: {relative}")
        copied[relative] = expected_hash
    write_json_atomic(
        manifest_path,
        {
            "schema": 1,
            "generated_utc": iso_utc(utc_now()),
            "run_fingerprint": report["run_fingerprint"],
            "contract_code_files": expected,
            "archived_files": copied,
        },
    )
    print(f"M14 source archive created and verified: {len(copied)} files")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except M14DataError as error:
        print(f"M14 source archive refused: {error}", file=sys.stderr)
        raise SystemExit(1) from error
