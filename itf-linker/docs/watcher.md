# The Rubin batch watcher

`scripts/watch_rubin_batches.py` answers one question with two HTTP GETs: **has a new
Rubin bulk batch landed since last time?** It exists because M8's attribution pipeline
is only worth re-running when there are new orbits to attribute against, and the two
places that show first are:

| Signal | Source | What counts |
|---|---|---|
| New canonical daily partition ≥ `--min-bytes` (default 1 MB) | GCS bucket `asteroid-institute-public`, prefix `production/rubin/mpc/obs_sbn/daily/` (the Asteroid Institute's public replica of the MPC obs table, found via `ls.st/ast` → `b612.ai/rubin-mpc-downloads/`) | Only an exact `YYYY-MM-DD/parquet/obs_sbn_X05_YYYY-MM-DD.parquet` aggregate can be a batch. Empty aggregates are ~11 kB markers. Nested `parquet_generations` shards are internal storage generations and are ignored regardless of size. |
| New newsletter link | `buttondown.com/MPC_newsletter/archive/` | The MPC documents bulk-batch handling there (the February 2026 issue is the primary source for M7's headwind section). |

## Running it

```
.venv\Scripts\python.exe scripts\watch_rubin_batches.py --pretty
```

- First run writes a **baseline** to `data/watcher-state.json` and reports nothing (it
  cannot know what is "new" until it has a past).
- Every later run diffs against the state file, rewrites it, prints one JSON document,
  and exits with a meaningful code:

| Exit | Meaning | Sensible reaction |
|---|---|---|
| `0` | Nothing new | Nothing |
| `2` | **New batch-sized partition** | A human queues `scripts/m8_fetch_bulk.py` (with the new partition added) + `scripts/m8_attribution.py`; per-batch human review always |
| `3` | Other news (partition refreshed / new newsletter), or only the newsletter check failed after a valid bucket check; the prior newsletter baseline is preserved | Read it; investigate a newsletter failure without discarding the valid partition observation |
| `1` | The authoritative bucket check failed; prior state is left untouched | Investigate; do not retry in a tight loop |

Event kinds emitted: `new_batch_partition`, `new_marker_partition`,
`partition_refreshed` (the replica re-syncs status/provid columns in place —
informational), `new_newsletter`, `newsletter_check_failed`.

Every partition event includes a parsed `date`. A parquet object that does not match the
canonical path exactly is discarded before state diffing; it cannot emit any event.

## Scheduling — deliberately not installed

The MPC newsletter is monthly and Rubin's bulk submissions have been roughly
February / April / June / August 2026 so far, so **daily is more than enough** and
weekly is defensible. On Windows the schedule would be one line, run as the logged-in
user:

```
schtasks /create /tn "rubin-batch-watch" /sc daily /st 09:00 ^
  /tr "C:\Users\matth\projects\astronomy\itf-linker\.venv\Scripts\python.exe C:\Users\matth\projects\astronomy\itf-linker\scripts\watch_rubin_batches.py"
```

**No scheduled task is installed by this repo, and the watcher never triggers the
pipeline itself.** Exit code 2 is a signal to a human (or to Matthew's orchestrator, if
he wires it); the attribution run, the fit queue and anything downstream stay behind
per-batch human review, per standing constraint 1. The watcher performs two GET
requests per run and writes nothing outside `--state`.

## What it found on its own first baseline (2026-08-16)

The bucket already shows post-April bulk partitions the milestones have not consumed:
`2026-06-04` (47 MB), `2026-08-03` (13 MB), `2026-08-06` (13 MB), **`2026-08-10`
(100 MB — the largest since February)**. Those are exactly the events this watcher
would have flagged, and they are listed in `M8-RESULTS.md` as candidate input for a
future M9 run.

## 2026-09-02 audit correction

The bucket later exposed nested `parquet_generations` objects beneath the daily prefix.
The original watcher accepted every `.parquet` object, so a current-state diff appeared
to contain **66** new batch-sized partitions. That was false: **64 were internal shards**.
The exact-path rule now rejects them before they enter state or event logic, with the
mixed bucket response pinned in `tests/data/rubin_bucket_listing.json`.

After that correction, exactly two genuine canonical aggregates remain unprocessed:
**2026-08-19** and **2026-08-24**. They are explicit regression expectations in
`tests/test_rubin_batch_watch.py`. Exit code 2 means a human may queue those two dates for
the existing M8/M9 attribution workflow; it still does not start that workflow itself.
