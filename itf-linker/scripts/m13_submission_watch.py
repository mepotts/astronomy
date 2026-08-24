"""M13: watch the submission queue and say when it changes. Runs on a GitHub runner.

The payload builder answers "what could go today". This answers "what changed since
yesterday", which is the thing worth an email.

**Why this can run on GitHub at all**, when the daily snapshot cannot. The MPC blocks
datacenter IP ranges -- ``.github/workflows/itf-snapshot.yml`` documents the ConnectTimeout
that killed the archive cron on 2026-08-04 -- so nothing here may touch
``minorplanetcenter.net``. It does not need to:

* the **review queue** is committed;
* the **key set** is a GitHub *release asset* (``observations-<sid>.parquet``), fetched
  from GitHub, not the MPC;
* the **observatory table** is committed alongside it;
* and the payload builder was written to need only ``desig``/``obscode``/``mjd``, which is
  exactly what that slim asset carries.

So the split is: the local scheduled task does the one thing that requires a residential
IP (pull the ITF, publish the key set), and everything downstream of it runs in the cloud.
The honest consequence is that **this watcher is only as fresh as the last snapshot the
local task published** -- if that machine is off for three days, this reports the same
state three times and says so, rather than inventing news.

**What counts as news.** Three things, and decay is the common one:

* rows **consumed** since the last run -- the MPC made the identification first, and that
  candidate is gone. M12 measured the file draining at 4.4 departures per arrival, so this
  is the expected daily signal and it is a clock, not an error;
* rows **newly submittable** -- only appears when a new sweep has extended the queue;
* the **queue itself changing**, e.g. a new versioned CSV.

Writes a markdown report, a fresh payload, and the new state. It sends nothing and it
submits nothing; the workflow around it opens a GitHub issue, and a human uploads.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from m13_submit_payload import (
    check_row,
    load_itf_nights,
    packed_provisional,
)

SUBMIT_URL = "https://www.minorplanetcenter.net/mpcops/submissions/identifications/"


def row_id(row: dict[str, str]) -> str:
    """A stable id for a queue row: the content-addressed link keys are the citation."""
    return f"{row['object']}|{row['link_keys']}"


def build(queue: Path, itf: Path, tiers: set[str],
          neo: dict | None = None) -> tuple[dict, list, list]:
    rows = list(csv.DictReader(queue.open(encoding="utf-8-sig")))
    picked = [r for r in rows if r["tier"] in tiers]
    nights = {(r["desig"], r["obscode"], r["night"]): r
              for r in load_itf_nights(itf).iter_rows(named=True)}
    links: dict[str, Any] = {}
    ready: list[dict] = []
    dropped: list[dict] = []
    for row in picked:
        triples, reasons = check_row(row, nights, neo)
        if reasons:
            dropped.append({"id": row_id(row), "rank": row["rank"], "tier": row["tier"],
                            "object": row["object"], "reasons": reasons})
            continue
        links[f"link_{len(links)}"] = {
            "designations": [packed_provisional(row["object"])],
            "trksubs": triples,
        }
        ready.append({"id": row_id(row), "rank": row["rank"], "tier": row["tier"],
                      "object": row["object"], "arc_days": row["arc_extension_days"],
                      "n_obs": row["n_new_obs"]})
    return links, ready, dropped


def render(snapshot: str, queue: Path, ready: list, dropped: list,
           gone: list, fresh: list, payload: dict, first_run: bool) -> str:
    n = len(ready)
    out = [
        f"**{n} identifications ready to submit** as of ITF snapshot `{snapshot}`.",
        "",
        f"- queue: `{queue.name}`",
        f"- ready: **{n}**  ·  held back: {len(dropped)}",
    ]
    if first_run:
        out.append("- *(first run — establishing the baseline, so nothing is reported as new)*")
    out.append("")

    if gone:
        out += [
            f"### {len(gone)} consumed since the last run",
            "",
            ("The MPC made these identifications itself while they sat in the queue. "
             "Nothing to do — they are gone, and this is the clock M12 measured "
             "(the ITF drains at 4.4 departures per arrival)."),
            "",
            "| rank | object | why |",
            "|---|---|---|",
        ]
        out += [f"| {g.get('rank','?')} | {g['object']} | {g['reasons'][0]} |"
                for g in gone[:25]]
        if len(gone) > 25:
            out.append(f"| … | *{len(gone) - 25} more* | |")
        out.append("")

    if fresh:
        out += [
            f"### {len(fresh)} newly ready",
            "",
            "| rank | tier | object | arc extension (d) | new obs |",
            "|---|---|---|---:|---:|",
        ]
        out += [f"| {f['rank']} | {f['tier']} | {f['object']} | {f['arc_days']} | "
                f"{f['n_obs']} |" for f in fresh[:25]]
        if len(fresh) > 25:
            out.append(f"| … | | *{len(fresh) - 25} more* | | |")
        out.append("")

    top = sorted(ready, key=lambda r: -float(r["arc_days"] or 0))[:10]
    out += ["### Top 10 by arc extension", "",
            "| rank | tier | object | arc extension (d) | new obs |",
            "|---|---|---|---:|---:|"]
    out += [f"| {t['rank']} | {t['tier']} | {t['object']} | {t['arc_days']} | "
            f"{t['n_obs']} |" for t in top]
    out += ["", "### The payload", "",
            f"Upload at <{SUBMIT_URL}> — nothing has been sent.", "",
            "<details><summary>submission JSON (click to expand)</summary>", "",
            "```json", json.dumps(payload, indent=2), "```", "", "</details>", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--itf", type=Path, required=True)
    ap.add_argument("--snapshot-id", required=True)
    ap.add_argument("--state", type=Path, required=True)
    ap.add_argument("--tier", action="append", default=None)
    ap.add_argument("--neo-status", type=Path, default=None,
                    help="sidecar from m13_neo_status.py; absence of an "
                         "object means NON-NEO, the restrictive branch")
    ap.add_argument("--name", required=True)
    ap.add_argument("--email", required=True)
    ap.add_argument("--out-payload", type=Path, required=True)
    ap.add_argument("--out-report", type=Path, required=True)
    ap.add_argument("--github-output", type=Path, default=None,
                    help="write changed=true/false here for the workflow to gate on")
    args = ap.parse_args()
    tiers = set(args.tier or ["A"])

    neo = (json.loads(args.neo_status.read_text(encoding="utf-8"))["objects"]
           if args.neo_status and args.neo_status.exists() else {})
    links, ready, dropped = build(args.queue, args.itf, tiers, neo)
    payload = {"header": {"name": args.name, "email": args.email,
                          "comment": "archival ITF tracklets attributed to known objects"},
               "links": links}

    prev = (json.loads(args.state.read_text(encoding="utf-8"))
            if args.state.exists() else None)
    first_run = prev is None
    prev_ready = set(prev["ready"]) if prev else set()
    prev_queue = prev.get("queue") if prev else None
    now_ready = {r["id"] for r in ready}

    fresh = [] if first_run else [r for r in ready if r["id"] not in prev_ready]
    gone_ids = set() if first_run else prev_ready - now_ready
    by_id = {d["id"]: d for d in dropped}
    gone = [by_id.get(i, {"id": i, "object": i.split("|")[0], "rank": "?",
                          "reasons": ["no longer in the queue"]}) for i in sorted(gone_ids)]

    same_snapshot = bool(prev and prev.get("snapshot") == args.snapshot_id)
    changed = bool(first_run or fresh or gone or prev_queue != str(args.queue))

    report = render(args.snapshot_id, args.queue, ready, dropped, gone, fresh,
                    payload, first_run)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.write_text(report, encoding="utf-8")
    args.out_payload.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.state.write_text(json.dumps({
        "snapshot": args.snapshot_id, "queue": str(args.queue),
        "tiers": sorted(tiers), "ready": sorted(now_ready),
        "n_ready": len(ready), "n_held": len(dropped),
    }, indent=2), encoding="utf-8")

    print(f"snapshot {args.snapshot_id}  ready {len(ready)}  held {len(dropped)}")
    print(f"  newly ready {len(fresh)}   consumed since last run {len(gone)}")
    if same_snapshot:
        print("  NOTE: same snapshot as the previous run -- the local archive task has "
              "not published a newer key set (that machine may be off).")
    print(f"  changed: {changed}")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\n")
            fh.write(f"ready={len(ready)}\n")
            fh.write(f"gone={len(gone)}\n")
            fh.write(f"fresh={len(fresh)}\n")
            fh.write(f"snapshot={args.snapshot_id}\n")


if __name__ == "__main__":
    main()
