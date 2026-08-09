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

The script **fetches and archives into the development checkout** (that is where the
snapshot data, the rolling windows and the venv live) but **commits from a separate clone**
at `c:/Users/matth/projects/astronomy-archive`. Create it once:

```bash
git clone --branch main https://github.com/mepotts/astronomy.git \
  c:/Users/matth/projects/astronomy-archive
```

Nothing human is ever edited there; the task owns it. Until 2026-08-06 the script ran
`git checkout main` in the *shared* tree whenever that tree was clean — so committing your
work on a feature branch and leaving it clean overnight was enough for the 08:30 task to
move you to `main` and push from it. The dirty-tree guard only ever protected *uncommitted*
work. Branch state in the development checkout is now irrelevant to the archive, and vice
versa.

Recreate the task with:

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
| `observations.parquet` | ~178 MB | release asset `itf-state`, one per snapshot, rolling window of 4 | Needed only to diff the *next* pull |
| `itf.txt.gz` | ~135 MB | local, rolling window | Re-fetchable |

Assets are named `observations-<snapshot-id>.parquet`. They used to be a single
`observations.parquet` overwritten each run, which meant exactly one generation of the
irreplaceable key set existed anywhere at any moment — and `gh release upload --clobber`
deletes the existing asset *before* uploading, so a failed upload destroyed it. `gh` takes
an asset's name from the file's basename (the `file#label` suffix sets only a display
label), so the script hardlinks the key set to its per-snapshot name before uploading.

The pre-2026-08-06 asset is still called `observations.parquet` with no snapshot id. The
prune step matches `observations-*` only, so it is never deleted automatically.

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

**Publishing the key set used to depend on git succeeding.** In the local script the
upload sat *after* the commit-and-push block, and three ordinary paths returned before
reaching it: a dirty development tree, an unchanged ITF ("nothing new"), and a failed push.
So the step that makes the *next* delta computable was skipped by bookkeeping outcomes that
have nothing to do with it. Observed on 2026-08-06: the archive on disk had reached
`20260806T122651Z` while the newest published key set was still 08-04, because the 08-06
run found the tree dirty and exited before publishing. The publish now runs **before** any
git work and independently of it, retries three times, and a failure sets a non-zero exit
so the task's `LastTaskResult` shows it. The Actions workflow's publish step carries
`if: always()` for the same reason.

**A failed `git add` used to report success.** The local script ran
`git add -f … 2>/dev/null` and then treated an empty `git diff --cached` as "nothing new".
A discarded add error therefore surfaced as the *success* message for "the ITF has not
changed" — the same unmeasurable-state-recorded-as-a-measured-null shape as the zero delta
above. The add is no longer silenced, its exit status is checked, and `git ls-files
--error-unmatch` proves both paths actually reached the index before an empty diff is
allowed to mean anything.

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
independently confirmed **21 of M3's proposed tracklet groupings** (26 on a 2026-08-09
re-run, and unchanged under the stricter "nothing of the member survives" test) — 14 of them
cross-observatory — by recording their members leaving the ITF once other people linked
them. That is the only validation in the project independent of the pipeline's own
fitting and vetting.
