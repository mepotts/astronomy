# ITF archive recovery — 2026-09-05

## Result

The deployed local task completed a catch-up run successfully on September 5.
Snapshot `20260905T132624Z` is archived and its exact key set is published in the
existing `itf-state` release. The counts-only GitHub monitor passed in
[run 33969829748](https://github.com/mepotts/astronomy/actions/runs/33969829748).
The refreshed standing tier-A queue is **20 ready / 6 held**, unchanged from the
prior monitor state. These are existing gate classifications, not discoveries,
new orbit fits, or approved MPC submissions.

At this repair's completion the September 6 08:30 Eastern unattended cycle remained
pending; the manual trigger did not prove it. **September 6 update: acceptance now
passes**, with exact publisher, lineage, release-hash and scheduled-watch evidence
in [the separate acceptance record](UNATTENDED-ACCEPTANCE-2026-09-06.md).
The task's cadence and action were not changed.

## Cause and exact correction

The September 2 preflight began checking every historical delta's file size.
The recovered August 6 delta was valid, but its manifest retained the original
empty file's size: **608 bytes rather than 437,331 bytes**. The new validation
therefore aborted before fetching, and the public monitor correctly failed its
24-hour freshness check on September 3 and 4.

The correction changes only `bytes.delta.parquet` in that manifest and adds a
dated correction record. Original recovery provenance, scientific counts, and
delta bytes remain unchanged. The previous manifest SHA-256 is preserved in the
correction record and its full content remains in Git history.

- Delta SHA-256: `8988239001731a246c04913d162dac1b812a27f34ab45e4f0bdea1b0b49aa031`.
- Git blob: `651713f9fd95345e7ea44f18c81a00a88cf1aae2`, identical to commit
  `5a1f9a67c38f47acd75667ba78a0de1cbaf906f5` from the original archive recovery.
- Actual delta rows: **25,512 = 3,885 appeared + 21,627 disappeared**, exactly
  matching the existing manifest counts.
- After correction, the unchanged full-chain validator passed **32 records and
  13 retained key sets** before any catch-up fetch.
- The deployed pinned-runtime preflight passed against the actual state and
  separate archive checkout, with **14-generation local/release retention**.

No integrity rule was bypassed or weakened. The sandbox's Polars CPU-detection
error prevented two initial local checks; the same checks ran normally in the
owner environment used by the deployed task. **58 archive/configuration/watcher
tests passed.**

## Catch-up evidence and gap

The installed Windows task was manually triggered at **2026-09-05 09:42:16 EDT**
and completed with `LastTaskResult=0`. It used the existing pinned operations
checkout, state directory and archive publisher.

- Source snapshot timestamp: **2026-09-05 13:26:24 UTC**.
- Parent and immediate predecessor: **20260902T062614Z**.
- Observations: **9,127,430**, with **9,126,362 distinct observation keys**.
- Delta across the entire gap: **6,899 appeared / 12,419 disappeared**.
- Key-set bytes: **174,949,202**.
- Local SHA-256 and GitHub release-asset digest agree:
  `c3cd7ce75896077bdc380a4f0ac9797661a2f44fd1d999b956b64b9ebce833dc`.

The September 2–5 interval is one measured delta. It does not reconstruct the
missed September 3/4 snapshots, identify exactly when within the interval a row
changed, or prove that disappearance means an MPC identification.

## Scientific boundary

M14 remains closed at its procedural STOP. The daily archive and standing queue
monitor do not run new attribution fits; the separate Rubin batch watcher is not
installed as a scheduled task. Fresh discovery work requires a separately frozen
protocol after the documented M14 input/residual-provenance defects are repaired.
Any review/submission packet needs fresh validation and a human submission decision.

The current task's `Astronomy closeout follow-ups` schedule separately verified
the September 6 unattended cycle; this manual restoration remains a distinct event.
