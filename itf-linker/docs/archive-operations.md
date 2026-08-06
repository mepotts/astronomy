# Operating the ITF snapshot archive

The archive answers "which observations left the ITF, and when". The MPC serves only the
**current** file, so that question is answerable *only* if something captured each version
at the time. A day not captured is unrecoverable — there is no MPC history endpoint, and
the Internet Archive holds **13 captures of `itf.txt.gz` in total**, so it is not a
fallback.

This is the one dataset in the project that cannot be regenerated. Everything below exists
to protect it.

---

## 1. How it runs today

**A Windows scheduled task on the local machine**, daily at 08:30, invoking
[`scripts/snapshot-local.sh`](../scripts/snapshot-local.sh).

Recreate it with:

```powershell
$name    = "ITF snapshot (daily)"
$bash    = "C:\Program Files\Git\bin\bash.exe"
$script  = "c:/Users/matth/projects/astronomy/itf-linker/scripts/snapshot-local.sh"
$action  = New-ScheduledTaskAction -Execute $bash -Argument "-lc `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 8:30am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
              -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger `
  -Settings $settings -Force
```

`-StartWhenAvailable` matters: without it a missed 08:30 is skipped entirely rather than
run at next boot.

Check it: `Get-ScheduledTaskInfo -TaskName "ITF snapshot (daily)"` — `LastTaskResult` 0 is
success. The script's own log is `data/snapshot-local.log` (gitignored).

## 2. Why not GitHub Actions

It was, until 2026-08-04. Every run since has failed with:

```
ConnectTimeout: HTTPSConnectionPool(host='www.minorplanetcenter.net', port=443)
Connection to www.minorplanetcenter.net timed out. (connect timeout=300)
```

The TCP connection never establishes — packets dropped, not refused — while the identical
request completes in **0.03 s** from a residential connection. In the same failing job,
PyPI and GitHub were both reachable, so it is host-specific, not a runner egress fault.
That is an IP-range block on datacenter traffic.

Small free scientific services do this routinely when someone points a scraper at them
from a cloud provider, and they are entitled to. **Do not attempt to route around it** —
proxying or IP rotation against a service you may later want to submit observations to is
a bad trade at any odds. The workflow is kept, cron commented out, in
[`.github/workflows/itf-snapshot.yml`](../../.github/workflows/itf-snapshot.yml), ready to
re-enable if reachability returns.

A retry/backoff was added to `fetch._get` before the block was correctly diagnosed. It is
worth keeping for genuine transient errors but **it was not the fix**, and the commit
history says so.

## 3. Storage, and why it is split

| Artefact | Size | Where | Why |
|---|---:|---|---|
| `manifest.json` | ~1 KB | **committed** | Permanent record |
| `delta.parquet` | ~1 KB | **committed** | What appeared/disappeared — the payload |
| `observations.parquet` | ~178 MB | release asset `itf-state`, overwritten | Needed only to diff the *next* pull |
| `itf.txt.gz` | ~135 MB | local, rolling window | Re-fetchable |

~2 KB/day committed is ~700 KB/year of permanently useful history. The key set in git
would be ~60 GB/year of near-identical binaries, and GitHub hard-rejects files over
100 MB.

## 4. Failure modes seen in practice

**A delta of zero can mean two different things.** `{appeared: 0, disappeared: 0}` is a
legitimate result — the ITF genuinely did not change between 2026-07-29 07:26 and 09:26.
It was *also*, until 2026-08-06, what got written when the parent's key set was missing
and the delta could not be computed at all. That silently recorded a step where 21,627
observations had left as "nothing happened".

Every manifest now carries **`delta_status`**, always present:

```json
"delta_status": {"computed": true, "against": "20260804T072639Z",
                 "skipped_pruned_ancestors": []}
```

`computed: false` carries a `reason` distinguishing a baseline from an unmeasurable step.
The delta is now taken against the newest ancestor that **retains a key set**, not merely
the newest ancestor, so a missing intermediate widens the interval rather than destroying
the measurement. Pinned by `tests/test_snapshot_delta_status.py`.

**Key sets vanish across machines.** A snapshot built on a runner commits only
`manifest.json` and `delta.parquet`; its key set exists solely as the overwritten release
asset. On any other machine it looks pruned. This is why the walk-back exists, and it was
misdiagnosed as over-aggressive retention first — `snaps[:-full_keep]` is correct.

**Recovering a lost delta.** If the release asset still holds the relevant key set, a
delta can be recomputed after the fact. Done once, on 2026-08-06: downloaded the asset,
recomputed against the current snapshot, wrote `delta.parquet`, and recorded a
`delta_recovered` block in the manifest rather than presenting the figures as natively
computed. Cross-checked against that manifest's own observation count.

## 5. If you contact the MPC

Reachability is worth raising once, framed as a report rather than a request. Draft:

> **Subject: Automated ITF fetches timing out from cloud IP ranges**
>
> I'm an independent researcher doing archival linkage work on the Isolated Tracklet File.
> I wanted to flag a connectivity change in case it is not intentional, and to ask how you
> would prefer I fetch.
>
> Since around 4 August 2026, HTTPS requests to
> `https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz` time out at the TCP connect stage
> from GitHub Actions runners, while the same request completes in about 0.1 s from a
> residential connection. The connection is dropped rather than refused, which looks like
> an IP-range block on datacenter traffic rather than an outage.
>
> If that block is deliberate, I completely understand and have already moved my fetches
> to a home machine — I am not looking for a way around it, and I mention it only because
> other archival users on cloud infrastructure are likely hitting the same wall without a
> clear error to diagnose.
>
> My usage is modest and I would rather size it to whatever suits you: one fetch of
> `itf.txt.gz` per day, roughly 135 MB, to maintain a local archive of which observations
> leave the ITF over time. If a lower cadence, a mirror, or a different endpoint would be
> preferable, I will switch to it.

Not sent as of 2026-08-06.

## 6. What the archive has produced

See [`../SNAPSHOT-VALIDATION.md`](../SNAPSHOT-VALIDATION.md). In eight days it
independently confirmed **21 of M3's proposed tracklet groupings** — 14 of them
cross-observatory — by recording their members leaving the ITF once other people linked
them. That is the only validation in the project independent of the pipeline's own
fitting and vetting.
