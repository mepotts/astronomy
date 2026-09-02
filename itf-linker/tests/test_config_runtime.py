"""Runtime-path contracts for the unattended snapshot archive."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _write_record(root: Path, snapshot_id: str, *, keyset: bool = False) -> Path:
    snapshot = root / "snapshots" / snapshot_id
    snapshot.mkdir(parents=True)
    delta_path = snapshot / "delta.parquet"
    pq.write_table(
        pa.table(
            {
                "obs_key": pa.array([1], type=pa.uint64()),
                "change": pa.array([1], type=pa.int8()),
                "desig": pa.array(["fixture"], type=pa.large_string()),
                "obscode": pa.array(["X05"], type=pa.large_string()),
                "mjd": pa.array([60000.0], type=pa.float64()),
            }
        ),
        delta_path,
    )
    keyset_path = snapshot / "observations.parquet"
    if keyset:
        pq.write_table(
            pa.table(
                {
                    "obs_key": pa.array([1], type=pa.uint64()),
                    "desig": pa.array(["fixture"], type=pa.large_string()),
                    "obscode": pa.array(["X05"], type=pa.large_string()),
                    "mjd": pa.array([60000.0], type=pa.float64()),
                }
            ),
            keyset_path,
        )
    (snapshot / "manifest.json").write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "created_utc": "2026-08-01T12:30:00Z",
                "observations": 1,
                "bytes": {
                    "delta.parquet": delta_path.stat().st_size,
                    "observations.parquet": keyset_path.stat().st_size if keyset else 1,
                },
            }
        ),
        encoding="utf-8",
    )
    return snapshot


def test_data_dir_can_be_decoupled_from_the_code_checkout(tmp_path: Path) -> None:
    """The pinned ops checkout must be able to use the existing archive state."""
    state = (tmp_path / "archive state").resolve()
    env = os.environ.copy()
    env["ITF_DATA_DIR"] = str(state)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from itf_linker import config; print(config.DATA_DIR)",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert Path(result.stdout.strip()) == state


def test_unattended_archive_rejects_a_missing_or_empty_state(tmp_path: Path) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    with pytest.raises(RuntimeError, match="does not exist"):
        validate_existing_snapshot_chain(tmp_path / "typo")

    (tmp_path / "empty" / "snapshots").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="established snapshot chain"):
        validate_existing_snapshot_chain(tmp_path / "empty")


def test_unattended_archive_accepts_an_existing_chain_with_a_keyset(tmp_path: Path) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    _write_record(tmp_path, "20260831T122611Z")
    _write_record(tmp_path, "20260901T122612Z", keyset=True)

    assert validate_existing_snapshot_chain(tmp_path) == (2, 1)


def test_first_bootstrap_record_is_enough_for_the_next_normal_run(tmp_path: Path) -> None:
    """A one-time bootstrap must not require a second unsafe bootstrap run."""
    from itf_linker.config import validate_existing_snapshot_chain

    _write_record(tmp_path, "20260830T123000Z", keyset=True)

    assert validate_existing_snapshot_chain(tmp_path) == (1, 1)


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("manifest.json", b"{not json", "invalid snapshot manifest"),
        ("delta.parquet", b"not parquet", "invalid snapshot delta parquet"),
        ("observations.parquet", b"not parquet", "invalid snapshot key-set parquet"),
    ],
)
def test_unattended_archive_rejects_corrupt_chain_files(
    tmp_path: Path, filename: str, content: bytes, message: str
) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    snapshot = _write_record(tmp_path, "20260830T123000Z", keyset=True)
    (snapshot / filename).write_bytes(content)

    with pytest.raises(RuntimeError, match=message):
        validate_existing_snapshot_chain(tmp_path)


def test_unattended_archive_rejects_valid_but_partial_keyset(tmp_path: Path) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    snapshot = _write_record(tmp_path, "20260830T123000Z", keyset=True)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["observations"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="count/size disagrees with manifest"):
        validate_existing_snapshot_chain(tmp_path)


def test_unattended_archive_rejects_wrong_parquet_field_types(tmp_path: Path) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    snapshot = _write_record(tmp_path, "20260830T123000Z", keyset=True)
    keyset = snapshot / "observations.parquet"
    pq.write_table(
        pa.table(
            {
                "obs_key": ["not-a-uint64"],
                "desig": pa.array(["fixture"], type=pa.large_string()),
                "obscode": pa.array(["X05"], type=pa.large_string()),
                "mjd": pa.array([60000.0], type=pa.float64()),
            }
        ),
        keyset,
    )
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bytes"]["observations.parquet"] = keyset.stat().st_size
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="unexpected schema"):
        validate_existing_snapshot_chain(tmp_path)


def test_unattended_archive_rejects_invalid_manifest_timestamp(tmp_path: Path) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    snapshot = _write_record(tmp_path, "20260830T123000Z", keyset=True)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["created_utc"] = "not-a-time"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="invalid creation timestamp"):
        validate_existing_snapshot_chain(tmp_path)


def test_unattended_archive_rejects_future_record_and_recovery_directories(
    tmp_path: Path,
) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    snapshot = _write_record(tmp_path, "20260830T123000Z", keyset=True)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["created_utc"] = "2999-01-01T00:00:00Z"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="future creation timestamp"):
        validate_existing_snapshot_chain(tmp_path)

    manifest["created_utc"] = "2026-08-01T12:30:00Z"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    recovery = tmp_path / "snapshots" / "29990101T000000Z"
    recovery.mkdir()
    (recovery / "observations.parquet").write_bytes(b"future recovery fixture")
    with pytest.raises(RuntimeError, match="future-dated snapshot directory"):
        validate_existing_snapshot_chain(tmp_path)


def test_unattended_archive_can_require_the_snapshot_returned_by_this_run(
    tmp_path: Path,
) -> None:
    from itf_linker.config import validate_existing_snapshot_chain

    _write_record(tmp_path, "20260829T123000Z")
    _write_record(tmp_path, "20260830T123000Z", keyset=True)
    assert validate_existing_snapshot_chain(
        tmp_path, required_full_snapshot="20260830T123000Z"
    ) == (2, 1)
    with pytest.raises(RuntimeError, match="not a complete, validated full record"):
        validate_existing_snapshot_chain(
            tmp_path, required_full_snapshot="20260829T123000Z"
        )


def test_shell_runtime_replaces_inherited_pythonpath_and_checks_code_root() -> None:
    script = (ROOT / "scripts" / "snapshot-local.sh").read_text(encoding="utf-8")

    assert 'export PYTHONPATH="$PROJ/src"' in script
    assert "${PYTHONPATH:+" not in script
    assert "ITF_EXPECTED_PROJECT_ROOT" in script
    assert "validate_existing_snapshot_chain" in script
    assert "archive clone must be separate from the code and state directories" in script
    assert "remote get-url origin" in script
    assert 'show-ref --verify --quiet "refs/heads/$BRANCH"' in script
    assert 'ARCHIVE="$ARCHIVE_ROOT"' in script
    assert 'SNAPSHOT_DATA="$DATA_ROOT/snapshots"' in script
    assert '"$RUNTIME_FULL_KEEP" =~ ^[0-9]+$' in script
    assert script.index("archive clone must be separate") < script.index("ITF_PREFLIGHT_ONLY")
    assert 'ls -1 "$SNAPSHOT_DATA"' not in script
    assert "SNAPSHOT_RESULT" in script
    assert "required_full_snapshot" in script
    assert 'git rev-list --count "origin/$BRANCH..$BRANCH"' in script
    assert script.index('git rev-list --count "origin/$BRANCH..$BRANCH"') < script.index(
        'every snapshot record on disk is committed and published'
    )


def test_retired_cloud_snapshot_cannot_fetch_publish_or_push() -> None:
    workflow = (ROOT.parent / ".github" / "workflows" / "itf-snapshot.yml").read_text(
        encoding="utf-8"
    )

    assert "contents: read" in workflow
    assert "schedule:" not in workflow
    for forbidden in ("snapshot --refetch", "release upload", "git push", "contents: write"):
        assert forbidden not in workflow
