"""Watcher: has a new Rubin bulk batch landed? One polite check, no scheduling.

Two independent signals, each a single HTTP GET:

1. **Asteroid Institute daily partitions** -- the public GCS bucket
   (``asteroid-institute-public``, ``production/rubin/mpc/obs_sbn/daily/``) grows one
   partition per day the MPC replica ingested X05 rows. Empty days are ~11 kB marker
   parquets; real submission batches are megabytes (the Feb-5 designation batch is
   59 MB, the big April partitions 18-63 MB). A partition that is *new since the last
   run* and above ``--min-bytes`` is the "new bulk batch" event M8's prospectus wants.
   Existing partitions whose bytes/updated change are reported as replica refreshes
   (informational -- the AI re-syncs status/provid columns).
2. **MPC newsletters** -- the newsletter index page, diffed for new PDF links. The
   February 2026 issue is where the Feb-5 batch and the MPC's designation-time ITF
   sweep were documented; a new issue is worth a human read regardless.

State lives in one JSON file (``--state``, default ``data/watcher-state.json``): the
previous partition listing and newsletter links. Every run rewrites it. Events go to
stdout as one JSON document (``--pretty`` for humans), and the exit code says what
happened: **0** nothing new, **2** new batch-sized partition (the "queue an attribution
run" signal), **3** other news only (refresh/newsletter), **1** the check itself failed.

This script never schedules itself, never runs the attribution pipeline, and never
submits anything. Wiring it to a schedule -- and acting on exit code 2 -- is a human
decision; ``docs/watcher.md`` shows how.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]

BUCKET_LIST = "https://storage.googleapis.com/storage/v1/b/asteroid-institute-public/o"
DAILY_PREFIX = "production/rubin/mpc/obs_sbn/daily/"
#: The MPC front page links its newsletter through Buttondown; the archive page lists
#: one ``/MPC_newsletter/archive/newsletter-<month>-<year>/`` link per issue. (The old
#: ``minorplanetcenter.net/mpcops/newsletters`` and ``/media/newsletters`` paths 404 --
#: checked 2026-08-16; only the per-issue PDFs under /media/newsletters remain live.)
NEWSLETTER_INDEX = "https://buttondown.com/MPC_newsletter/archive/"
USER_AGENT = (
    "itf-linker/0.4 watcher (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)


def list_partitions(timeout: float = 60.0) -> dict[str, dict[str, Any]]:
    """All daily parquet partitions: name -> {bytes, updated}. Paged listing."""
    out: dict[str, dict[str, Any]] = {}
    token: str | None = None
    while True:
        params: dict[str, str] = {"prefix": DAILY_PREFIX, "maxResults": "1000"}
        if token:
            params["pageToken"] = token
        resp = requests.get(BUCKET_LIST, params=params,
                            headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        doc = resp.json()
        for item in doc.get("items", []):
            name = item["name"]
            if not name.endswith(".parquet"):
                continue
            out[name] = {"bytes": int(item.get("size", 0)),
                         "updated": item.get("updated")}
        token = doc.get("nextPageToken")
        if not token:
            return out


def list_newsletters(timeout: float = 60.0) -> list[str]:
    resp = requests.get(NEWSLETTER_INDEX, headers={"User-Agent": USER_AGENT},
                        timeout=timeout)
    resp.raise_for_status()
    links = re.findall(
        r'href="(https?://[^"]*MPC_newsletter/archive/[^"]+)"', resp.text
    )
    return sorted({ln for ln in links if not ln.rstrip("/").endswith("archive")})


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
    except requests.RequestException as exc:
        print(json.dumps({"error": f"bucket listing failed: {exc}"}), file=sys.stderr)
        return 1

    old_parts: dict[str, Any] = previous.get("partitions", {})
    first_run = not old_parts
    for name, meta in sorted(partitions.items()):
        old = old_parts.get(name)
        if old is None:
            if not first_run and meta["bytes"] >= args.min_bytes:
                events.append({"kind": "new_batch_partition", "name": name, **meta})
            elif not first_run:
                events.append({"kind": "new_marker_partition", "name": name, **meta})
        elif old.get("bytes") != meta["bytes"] and meta["bytes"] >= args.min_bytes:
            events.append({"kind": "partition_refreshed", "name": name,
                           "bytes_before": old.get("bytes"), **meta})

    newsletters: list[str] = previous.get("newsletters", [])
    if not args.skip_newsletter:
        try:
            current_news = list_newsletters()
            for link in current_news:
                if newsletters and link not in newsletters:
                    events.append({"kind": "new_newsletter", "href": link})
            newsletters = current_news
        except requests.RequestException as exc:
            events.append({"kind": "newsletter_check_failed", "error": str(exc)})

    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(
        json.dumps({"partitions": partitions, "newsletters": newsletters,
                    "updated_utc": result["checked_utc"]}),
        encoding="utf-8",
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
