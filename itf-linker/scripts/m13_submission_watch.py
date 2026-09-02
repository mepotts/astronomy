"""M13: monitor submission-queue counts and snapshot freshness. Never sends a payload.

This watcher is deliberately less capable than :mod:`m13_submit_payload`. It answers
two operational questions for a public CI run:

* did the set of rows that clears the local submission gates change; and
* did the local archive publish a newer ITF key set?

Those signals are independent. A newer snapshot is persisted even when the candidate
set is unchanged, and a repeated snapshot is a freshness warning rather than candidate
news. Public output contains counts and status only: no designation, tracklet, link key,
submitter identity, or submission JSON is rendered. A human who elects to review a batch
must run ``m13_submit_payload.py`` locally and keep its output private until publication is
explicitly approved.

The state stores SHA-256 fingerprints rather than row identifiers. That is enough to
measure additions and removals without turning the CI state into a second candidate list.
It is written atomically after every successful observation. The workflow persists it in
an Actions cache; it never commits runtime state to the repository or races the local
snapshot publisher on ``main``.

Absence from the current ITF means only **no longer present in this snapshot**. It does
not, by itself, establish that the MPC identified the tracklet or where it went.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from m13_submit_payload import check_row, load_itf_nights

STATE_VERSION = 2
SNAPSHOT_FORMAT = "%Y%m%dT%H%M%SZ"


def row_id(row: dict[str, str]) -> str:
    """The stable queue-row identity used only as input to a one-way fingerprint."""
    return f"{row['object']}|{row['link_keys']}"


def fingerprint(value: str) -> str:
    """Return a stable, privacy-safer state key for a candidate row."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def queue_fingerprint(queue: Path) -> str:
    return hashlib.sha256(queue.read_bytes()).hexdigest()


def evaluate(queue: Path, itf: Path, tiers: set[str],
             neo: dict | None = None) -> tuple[set[str], int]:
    """Return fingerprints of ready rows and the number held back."""
    rows = list(csv.DictReader(queue.open(encoding="utf-8-sig")))
    picked = [row for row in rows if row["tier"] in tiers]
    nights = {
        (row["desig"], row["obscode"], row["night"]): row
        for row in load_itf_nights(itf).iter_rows(named=True)
    }
    ready: set[str] = set()
    held = 0
    for row in picked:
        try:
            _, reasons = check_row(row, nights, neo)
        except (KeyError, TypeError, ValueError):
            # Some parser errors include the offending designation/tracklet in their
            # message. Preserve the fail-closed behavior without copying that detail into
            # a public Actions traceback; the exact exception is reproducible locally.
            raise RuntimeError(
                "candidate evaluation failed; rerun the watcher locally for private details"
            ) from None
        if reasons:
            held += 1
        else:
            ready.add(fingerprint(row_id(row)))
    return ready, held


def _previous_ready(state: dict[str, Any]) -> set[str]:
    """Read v2 state, migrating the old exact-id state without retaining exact ids."""
    candidate = state.get("candidate", {})
    if candidate.get("ready_sha256") is not None:
        return set(candidate["ready_sha256"])
    return {fingerprint(value) for value in state.get("ready", [])}


def _previous_snapshot(state: dict[str, Any]) -> str | None:
    return state.get("freshness", {}).get("latest_snapshot") or state.get("snapshot")


def snapshot_status(previous: str | None, current: str) -> str:
    if previous is None:
        return "baseline"
    if current == previous:
        return "repeated"
    if current > previous:
        return "advanced"
    return "regressed"


def snapshot_age_hours(snapshot: str, now: dt.datetime) -> float | None:
    """Age of a standard archive id, or ``None`` for a non-standard id."""
    try:
        stamp = dt.datetime.strptime(snapshot, SNAPSHOT_FORMAT).replace(tzinfo=dt.UTC)
    except ValueError:
        return None
    age_hours = (now - stamp).total_seconds() / 3600.0
    return age_hours if age_hours >= 0.0 else None


def should_alert_freshness(status: str, age_hours: float | None) -> bool:
    """Freshness is based on age, independently of candidate or transition status."""
    return status == "regressed" or age_hours is None or age_hours >= 24.0


def update_snapshot_history(previous: dict[str, Any], snapshot: str,
                            observed_utc: str) -> list[dict[str, Any]]:
    """Record every observation while keeping one compact entry per snapshot id."""
    history = [
        dict(item)
        for item in previous.get("freshness", {}).get("snapshots_observed", [])
    ]
    legacy = previous.get("snapshot")
    if legacy and not history:
        history.append({
            "snapshot": legacy,
            "first_observed_utc": None,
            "last_observed_utc": None,
            "runs_seen": 1,
        })

    for item in history:
        if item.get("snapshot") == snapshot:
            item["last_observed_utc"] = observed_utc
            item["runs_seen"] = int(item.get("runs_seen", 1)) + 1
            return history

    history.append({
        "snapshot": snapshot,
        "first_observed_utc": observed_utc,
        "last_observed_utc": observed_utc,
        "runs_seen": 1,
    })
    return history


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    """Replace state atomically so an interrupted run cannot leave partial JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def render(*, snapshot: str, status: str, age_hours: float | None,
           ready: int, held: int, new_ready: int, no_longer_ready: int,
           queue_changed: bool, first_run: bool) -> str:
    """Render a public-safe report containing only counts and operational status."""
    age = "unknown" if age_hours is None else f"{age_hours:.1f} h"
    candidate_status = (
        "baseline established; candidate changes are not reported on the first run"
        if first_run
        else f"{new_ready} newly ready; {no_longer_ready} no longer ready"
    )
    return "\n".join([
        "## ITF submission-watch status",
        "",
        f"- snapshot: `{snapshot}`",
        f"- snapshot status: **{status}**",
        f"- snapshot age at check: {age}",
        f"- ready: **{ready}**",
        f"- held back: **{held}**",
        f"- candidate status: {candidate_status}",
        f"- queue file changed: **{'yes' if queue_changed else 'no'}**",
        "",
        ("This public report intentionally contains counts and status only. It contains "
         "no candidate identifiers or submission payload. Build any review payload "
         "locally with `scripts/m13_submit_payload.py`; nothing has been sent."),
        "",
        ("A row reported as no longer ready may simply be absent from the current ITF. "
         "Disappearance alone does not prove an MPC identification or its destination."),
        "",
    ])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--itf", type=Path, required=True)
    ap.add_argument("--snapshot-id", required=True)
    ap.add_argument("--state", type=Path, required=True)
    ap.add_argument("--tier", action="append", default=None)
    ap.add_argument("--neo-status", type=Path, default=None,
                    help="sidecar from m13_neo_status.py; absence of an object means "
                         "NON-NEO, the restrictive branch")
    ap.add_argument("--out-report", type=Path, required=True)
    ap.add_argument("--github-output", type=Path, default=None,
                    help="write independent candidate/freshness outputs for the workflow")
    args = ap.parse_args()
    tiers = set(args.tier or ["A"])

    neo = (json.loads(args.neo_status.read_text(encoding="utf-8"))["objects"]
           if args.neo_status and args.neo_status.exists() else {})
    ready, held = evaluate(args.queue, args.itf, tiers, neo)

    previous = (json.loads(args.state.read_text(encoding="utf-8"))
                if args.state.exists() else {})
    first_run = not previous
    previous_ready = _previous_ready(previous)
    previous_queue = (previous.get("candidate", {}).get("queue_sha256")
                      or previous.get("queue_sha256"))
    current_queue = queue_fingerprint(args.queue)
    new_ready = set() if first_run else ready - previous_ready
    no_longer_ready = set() if first_run else previous_ready - ready
    queue_changed = bool(not first_run and previous_queue != current_queue)
    candidate_changed = bool(new_ready or no_longer_ready or queue_changed)

    previous_snapshot = _previous_snapshot(previous)
    status = snapshot_status(previous_snapshot, args.snapshot_id)
    now = dt.datetime.now(dt.UTC)
    observed_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    age_hours = snapshot_age_hours(args.snapshot_id, now)
    freshness_alert = should_alert_freshness(status, age_hours)

    report = render(
        snapshot=args.snapshot_id,
        status=status,
        age_hours=age_hours,
        ready=len(ready),
        held=held,
        new_ready=len(new_ready),
        no_longer_ready=len(no_longer_ready),
        queue_changed=queue_changed,
        first_run=first_run,
    )
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.write_text(report, encoding="utf-8")

    state = {
        "version": STATE_VERSION,
        "candidate": {
            "queue_sha256": current_queue,
            "tiers": sorted(tiers),
            "ready_sha256": sorted(ready),
            "n_ready": len(ready),
            "n_held": held,
        },
        "freshness": {
            "latest_snapshot": args.snapshot_id,
            "last_observed_utc": observed_utc,
            "snapshot_status": status,
            "snapshots_observed": update_snapshot_history(
                previous, args.snapshot_id, observed_utc
            ),
        },
    }
    write_json_atomic(args.state, state)

    print(f"snapshot {args.snapshot_id}  status {status}  age {age_hours}")
    print(f"ready {len(ready)}  held {held}")
    print(f"newly ready {len(new_ready)}  no longer ready {len(no_longer_ready)}")
    print(f"candidate changed: {candidate_changed}")
    print(f"freshness alert: {freshness_alert}")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as fh:
            fh.write(f"candidate_changed={'true' if candidate_changed else 'false'}\n")
            fh.write(f"snapshot_status={status}\n")
            fh.write(f"snapshot_advanced={'true' if status == 'advanced' else 'false'}\n")
            fh.write(f"freshness_alert={'true' if freshness_alert else 'false'}\n")
            fh.write(f"ready={len(ready)}\n")
            fh.write(f"held={held}\n")
            fh.write(f"no_longer_ready={len(no_longer_ready)}\n")
            fh.write(f"new_ready={len(new_ready)}\n")
            fh.write(f"snapshot={args.snapshot_id}\n")


if __name__ == "__main__":
    main()
