# ITF unattended-cycle acceptance - 2026-09-06

**PASS.** The first daily cycle after the September 5 repair completed without an
agent-triggered task run. The local publisher and subsequent scheduled GitHub
watch used the same fresh generation. This closes the pending unattended check in
[the repair record](ARCHIVE-REPAIR-2026-09-05.md), not the stopped M14 science pilot.

## Publisher and lineage

Checked after 15:30 UTC on September 6:

- Windows task `ITF snapshot (daily)`: `LastRunTime=2026-09-06 08:30:01 EDT`,
  `LastTaskResult=0`, `NumberOfMissedRuns=0`; next run September 7 at 08:30 EDT.
- Task action still names the pinned operations checkout and its Python runtime,
  explicit existing state directory, and separate archive clone. Operations code
  remains `8a7d15449018d44e54769b2232de93f4fd5890b3`; no deployment change was made.
- Local log starts at **12:30:02 UTC**, fetches at 12:30:09, constructs the record
  at 12:30:25, publishes the key set and ends `DONE: committed and pushed`.
- Snapshot **20260906T122623Z**, matching MPC `Last-Modified=12:26:23 UTC`.
  Parent, immediate predecessor and delta target are all **20260905T132624Z**;
  `is_baseline=false`, delta computed, no skipped/pruned ancestor.
- Manifest counts: **9,131,935 observations**, **9,130,867 distinct keys**,
  **1,068 duplicates**. Independent Parquet footer read confirms 9,131,935 rows.
- Delta: **12,660 appeared / 8,155 disappeared**; independent `change` column
  counts agree, and the net +4,505 agrees with the parent observation count.
- Permanent archive commit: `c4d1c3b` on main. Published and local delta Git blobs
  both equal `38eeb9bc17c5f943abd88a3e9d94ce8f0b1e3afa`.

Scheduler operational-event history is disabled on this machine, so there is no
Event 107 trigger record to cite. Acceptance rests on the unchanged daily trigger,
matching task/log timestamps, completed outputs, and no manual trigger in this
follow-up. No history setting was changed. The local log is ignored runtime state;
the committed manifest/delta and public run below are the durable cross-checks.

## Exact publication identity

The local key set and the GitHub `itf-state` asset
`observations-20260906T122623Z.parquet` agree:

- Bytes: **175,037,113**.
- SHA-256: `d0bf4abe4acc52bdfe3a121fc760ef26e2833ce0056c95d76ed4fe7cee35e929`.
- Release asset ID: **547170299**, uploaded 12:30:27-12:30:39 UTC.
- Delta: **310,067 bytes**, SHA-256
  `5fbc8dfb83003595973e2800c09580a19ea02a00dfa273f2abefb7a2f57e431b`.

The pinned no-network chain validator passed **34 complete records / 12 retained
key sets**, requiring this exact latest full snapshot. This is an integrity and
schema check, not a rerun of attribution fits. Its first direct invocation omitted
the launcher's source import path; using the pinned `itf-linker/src` path then
passed without changing code, dependencies or validation rules.

## Scheduled consumer

[GitHub watch run 34041245835](https://github.com/mepotts/astronomy/actions/runs/34041245835)
has event **schedule**, created **15:06:09 UTC**, conclusion **success**. Its log
explicitly selects snapshot `20260906T122623Z` and reports:

- Generation state **advanced**, age **2.6719549553 hours**.
- **20 ready / 6 held**, newly ready **0**, no longer ready **0**.
- `candidate_changed=false`; `freshness_alert=false`.

Unchanged review counts are a successful fresh measurement, not stale input, a
new candidate list, a scientific null, or evidence of no undiscovered objects.
Observation disappearance is not proof of an MPC identification.

## Remaining work

The single existing publisher continues daily; follow-ups now need only material
ITF failures, freshness problems or changed review counts. Do not manually run a
competing publisher or repeat this acceptance campaign on healthy unchanged days.
M14 remains stopped and scientific submissions remain human-gated. Dyson E stays
behind September 9 and its public-release guard; Gaia's protocol decisions remain
unresolved. The existing follow-up schedule remains daily until the September 9
experiment closes, as already specified; no automation change is needed today.
