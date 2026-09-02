"""Watcher: has a new Rubin bulk batch landed? One polite check, no scheduling.

Two independent signals, each a single HTTP GET:

1. **Asteroid Institute canonical daily partitions** -- the public GCS bucket
   (``asteroid-institute-public``, ``production/rubin/mpc/obs_sbn/daily/``) grows one
   partition per day the MPC replica ingested X05 rows. Empty days are ~11 kB marker
   parquets; real submission batches are megabytes (the Feb-5 designation batch is
   59 MB, the big April partitions 18-63 MB). A partition that is *new since the last
   run* and above ``--min-bytes`` is the "new bulk batch" event M8's prospectus wants.
   Existing partitions whose bytes/updated change are reported as replica refreshes
   (informational -- the AI re-syncs status/provid columns). Internal
   ``parquet_generations`` shards are explicitly excluded: they are implementation
   generations of a daily partition, not independent Rubin batches.
2. **MPC newsletters** -- the newsletter index page, diffed for new PDF links. The
   February 2026 issue is where the Feb-5 batch and the MPC's designation-time ITF
   sweep were documented; a new issue is worth a human read regardless.

State lives in one JSON file (``--state``, default ``data/watcher-state.json``): the
previous partition listing and newsletter links. Every run rewrites it. Events go to
stdout as one JSON document (``--pretty`` for humans), and the exit code says what
happened: **0** nothing new, **2** new batch-sized partition (the "queue an attribution
run" signal), **3** other news only (refresh/newsletter, including a newsletter-only
check failure after the authoritative bucket check succeeded), **1** the authoritative
bucket check failed. A newsletter-only failure preserves its prior newsletter baseline.

This script never schedules itself, never runs the attribution pipeline, and never
submits anything. Wiring it to a schedule -- and acting on exit code 2 -- is a human
decision; ``docs/watcher.md`` shows how.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]

BUCKET_LIST = "https://storage.googleapis.com/storage/v1/b/asteroid-institute-public/o"
DAILY_PREFIX = "production/rubin/mpc/obs_sbn/daily/"
#: Exactly one public aggregate is authoritative for each date. The bucket also exposes
#: nested ``parquet_generations`` shards; treating those as batches produced 64 false
#: alerts in the 2026-08-19/24 audit.
CANONICAL_PARTITION_RE = re.compile(
    rf"^{re.escape(DAILY_PREFIX)}"
    r"(?P<date>\d{4}-\d{2}-\d{2})/parquet/"
    r"obs_sbn_X05_(?P=date)\.parquet$"
)
#: The MPC front page links its newsletter through Buttondown; the archive page lists
#: one ``/MPC_newsletter/archive/newsletter-<month>-<year>/`` link per issue. (The old
#: ``minorplanetcenter.net/mpcops/newsletters`` and ``/media/newsletters`` paths 404 --
#: checked 2026-08-16; only the per-issue PDFs under /media/newsletters remain live.)
NEWSLETTER_INDEX = "https://buttondown.com/MPC_newsletter/archive/"
USER_AGENT = (
    "itf-linker/0.4 watcher (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)


class WatcherDataError(RuntimeError):
    """A successful transport returned data that cannot prove the watch state."""


def canonical_partition_date(name: str) -> str | None:
    """Return the partition date only for the authoritative daily aggregate."""
    match = CANONICAL_PARTITION_RE.fullmatch(name)
    return match.group("date") if match else None


def list_partitions(timeout: float = 60.0) -> dict[str, dict[str, Any]]:
    """All daily parquet partitions: name -> {bytes, updated}. Paged listing."""
    out: dict[str, dict[str, Any]] = {}
    token: str | None = None
    seen_tokens: set[str] = set()
    while True:
        params: dict[str, str] = {"prefix": DAILY_PREFIX, "maxResults": "1000"}
        if token:
            params["pageToken"] = token
        resp = requests.get(BUCKET_LIST, params=params,
                            headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        try:
            doc = resp.json()
        except ValueError as exc:
            raise WatcherDataError("bucket listing returned malformed JSON") from exc
        if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
            raise WatcherDataError("bucket listing has no schema-valid items array")
        if not doc["items"]:
            raise WatcherDataError("bucket listing returned an empty items array")
        for item in doc["items"]:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise WatcherDataError("bucket listing contains an invalid object row")
            name = item["name"]
            if canonical_partition_date(name) is None:
                continue
            try:
                size = int(item["size"])
            except (KeyError, TypeError, ValueError) as exc:
                raise WatcherDataError(f"canonical partition has invalid size: {name}") from exc
            updated = item.get("updated")
            if size < 0 or not isinstance(updated, str) or not updated.strip():
                raise WatcherDataError(
                    f"canonical partition has invalid size/updated metadata: {name}"
                )
            metadata = {"bytes": size, "updated": updated}
            if name in out and out[name] != metadata:
                raise WatcherDataError(f"canonical partition changed within one listing: {name}")
            out[name] = metadata
        token = doc.get("nextPageToken")
        if not token:
            if not out:
                raise WatcherDataError(
                    "bucket listing contained no canonical daily aggregate partitions"
                )
            return out
        if not isinstance(token, str) or token in seen_tokens:
            raise WatcherDataError("bucket listing returned an invalid/repeated page token")
        seen_tokens.add(token)


def list_newsletters(timeout: float = 60.0) -> list[str]:
    resp = requests.get(NEWSLETTER_INDEX, headers={"User-Agent": USER_AGENT},
                        timeout=timeout)
    resp.raise_for_status()
    links = re.findall(
        r'href="(https?://[^"]*MPC_newsletter/archive/[^"]+)"', resp.text
    )
    current = sorted({ln for ln in links if not ln.rstrip("/").endswith("archive")})
    if not current:
        raise WatcherDataError("newsletter archive returned no issue links")
    return current


def partition_events(partitions: dict[str, dict[str, Any]],
                     old_parts: dict[str, Any], min_bytes: int) -> list[dict[str, Any]]:
    """Diff canonical partitions only; internal generation shards can never alert."""
    events: list[dict[str, Any]] = []
    first_run = not old_parts
    for name, meta in sorted(partitions.items()):
        date = canonical_partition_date(name)
        if date is None:
            continue
        old = old_parts.get(name)
        if old is None:
            if not first_run and meta["bytes"] >= min_bytes:
                events.append({"kind": "new_batch_partition", "date": date,
                               "name": name, **meta})
            elif not first_run:
                events.append({"kind": "new_marker_partition", "date": date,
                               "name": name, **meta})
        elif (old.get("bytes"), old.get("updated")) != (
            meta["bytes"], meta["updated"]
        ):
            events.append({"kind": "partition_refreshed", "date": date, "name": name,
                           "bytes_before": old.get("bytes"),
                           "updated_before": old.get("updated"), **meta})
    return events


def write_state_atomic(path: Path, value: dict[str, Any]) -> None:
    """Replace watcher state atomically; a failed check never erases its baseline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", type=Path, default=ROOT / "data" / "watcher-state.json")
    ap.add_argument("--min-bytes", type=int, default=1_000_000,
                    help="partition size that counts as a real batch (markers are ~11 kB)")
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--skip-newsletter", action="store_true")
    args = ap.parse_args()

    previous: dict[str, Any] = {}
    if args.state.exists():
        previous = json.loads(args.state.read_text(encoding="utf-8"))

    events: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "events": events,
    }

    try:
        partitions = list_partitions()
    except (requests.RequestException, WatcherDataError) as exc:
        print(json.dumps({"error": f"bucket listing failed: {exc}"}), file=sys.stderr)
        return 1

    old_parts: dict[str, Any] = previous.get("partitions", {})
    first_run = not old_parts
    events.extend(partition_events(partitions, old_parts, args.min_bytes))

    newsletters: list[str] = previous.get("newsletters", [])
    if not args.skip_newsletter:
        try:
            current_news = list_newsletters()
            for link in current_news:
                if newsletters and link not in newsletters:
                    events.append({"kind": "new_newsletter", "href": link})
            newsletters = current_news
        except (requests.RequestException, WatcherDataError) as exc:
            events.append({"kind": "newsletter_check_failed", "error": str(exc)})

    write_state_atomic(
        args.state,
        {"partitions": partitions, "newsletters": newsletters,
         "updated_utc": result["checked_utc"]},
    )

    result["partitions_tracked"] = len(partitions)
    result["first_run_baseline"] = first_run
    print(json.dumps(result, indent=2 if args.pretty else None))

    if any(e["kind"] == "new_batch_partition" for e in events):
        return 2
    if events and any(e["kind"] != "new_marker_partition" for e in events):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
