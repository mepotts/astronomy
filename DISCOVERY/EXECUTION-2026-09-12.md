# September 12 execution and decisions

## Results

**No validated new discovery.** Material progress: recovered daily archive,
changed review queue, and independently diagnosed failure of the newly executable
Candidate E experiment. This supersedes September 8's pending-E state.

1. **ITF recovered.** Existing publisher restarted only after verifying it was
   idle. Generation `20260912T182637Z` passed lineage/local-release digest checks;
   existing watch succeeded. **18 ready / 8 held**, two newly held after tracklet
   disappearance and insufficient remaining arc. No identifiers published,
   payload generated, or identification inferred from disappearance.
   [Operational record](../itf-linker/RECOVERY-2026-09-12.md).
2. **E executed, not validated.** Release guard passed: 39 public observations,
   D 7/7, unchanged outcome-map hash. Nine L3 files fetched (135.4 MB). Frozen
   measurement exited 1; F560W's finite fitting patch produces a saddle, not a
   centroid maximum. Independent audit reproduced that and partial bands'
   resolution concerns. No outcome branch or validated contrast.
   [Evidence and limits](../dyson-revet/E-EXECUTION-2026-09-12.md).
3. **Follow-up corrected.** Existing portfolio task changed to Saturdays at
   11:30 local time; stale pending-E instructions replaced. Actual daily ITF
   publisher/watch unchanged. OpenAI Docs guided the in-app schedule update.
   Local scheduled work needs the computer/app available, as
   [official documentation](https://learn.chatgpt.com/docs/automations?surface=app)
   explains. Scheduling is not evidence of completed future analysis.

## Decisions and remaining work

- Close E's **frozen attempt at method failure**, not the unresolved scientific
  question. Defer separate model development; no post-hoc centroid repair or
  threshold change. Required independent controls/injections are stated in the
  E record. E's contamination was already published; this is not a new-object hunt.
- Keep ITF daily. Do not restart stopped attribution work or count ready rows as
  discoveries. Registry reporting remains gated.
- Keep DASCH's failed real-event and bracketed-block designs stopped, CCOR's
  geometry stop, and DR11's insufficient depth-gain stop. More unknown targets
  cannot repair failed controls. See [September 8](EXECUTION-2026-09-08.md) and
  [September 7](EXECUTION-2026-09-07.md).
- Gaia's planned December 2 release and A's July 16, 2027 release remain dated
  dependencies. No redundant full rehearsal this turn.
- PTA author/archive/submission decisions remain human gates. TNS/CHIME need
  their documented missing inputs. SPHEREx/eROSITA remain deferred choices,
  not date-blocked projects.
- A new discovery search remains real work, **not completed by this closeout**.
  Next: bounded control-first selection with public input access, prior-art/novelty
  checks, and fixed false-positive/recovery/resource limits. Prior comparisons
  do not exhaust the internet or establish a globally highest-yield opportunity.

## Verification scope

All 15 Dyson offline release/execution contracts pass; local FITS audit replays
exactly. ITF two-snapshot evaluation independently reproduces the watch's aggregate
transition. Frozen scientific code/outcomes unchanged. Root verification passes
(4 documents, 110 local links, 230 scripts); pinned lint and diff checks pass.
Repository CI is required for integration. CI does not reproduce ignored
JWST inputs; local receipts bind them by size/hash. No scientific publication,
registry submission, or private-coordinate disclosure was performed.
