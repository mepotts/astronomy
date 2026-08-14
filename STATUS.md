# STATUS — live research dashboard

*The one file to read to know what's running across this repo. Updated by the orchestrating
session whenever agents launch or report; per-project detail lives in each folder's own
`STATUS.md` (new projects) or `M*-RESULTS.md` (exosat-rv convention). Ranking and evidence
for why these three fronts: [`DISCOVERY/run3-prospectus.md`](DISCOVERY/run3-prospectus.md).*

**House gates (always on):** nothing submitted anywhere (MPC, TNS, journals, emails) and
nothing pushed/merged to main without Matthew's explicit per-item approval. Agents verify
before building — sweep-reported facts are treated as claims until re-checked with this
repo's own tooling. Every externally-sourced number carries its source or the mark
UNSOURCED (exosat-rv LESSONS §5b, repo-wide law).

## Active fronts — 2026-08-14

| Front | Avenue | Folder | State | Next human gate |
|---|---|---|---|---|
| **exosat-rv M32: eta Tel B RNAAS note** | writeup | [`exosat-rv/`](exosat-rv/) | **PREPARED, NOT SUBMITTED** (`docs/paper/rnaas-etatel-draft.md`, ~1,050 words, one table, numbers regenerate from `scripts/m32_etatel_numbers.py`). Limit re-verified: msini 0.51-1.27 M_Jup, P 20-300 d, FAP <= 0.85%. Sourcing it corrected four repo numbers: eta Tel B mass attribution (Lazzoni **2020**, and DISPUTED 47 vs Chai+2024's 29), **K 13.2 -> K_s 11.6** (1.6 mag), parallax 21.11 -> 20.6028, separation confirmed. Result got stronger: orbit is near edge-on (i=79-82 deg) so limits are true-mass to 2%. **Spillover: Lazzoni's magnitude column is wrong in 2 of 3 checked cases and it is the contrast-wall's x-axis for all 31 companions** - wall note item 0, recommend standing on the resolution gate alone | **Matthew's: whether to submit at all** (vs folding into the method paper), author/affiliation/ORCID, AAS account. Plus a targeted ADS check that no prior eta Tel B RV exists |
| exosat-rv M31: HiRISE extraction of HIP 65426 | [#1](DISCOVERY/run3-prospectus.md) | [`exosat-rv/`](exosat-rv/) | **M31 APPROVED (Matthew, 2026-08-14) — agent running**: minimal calibs from M30's banked URL lists, util_ fibre path per M29 §15, verify by table contents + host-telluric CCF. Disk reconciled: C: has >300 GB (Matthew); the tight volume is the ~1 TB data volume — agent routes around it, no cross-thread deletions. M30 history: sweep's blocks all already ledgered (corrected in place); CD-35 joint-fit protocol on record | HIP 65426 publication priority still Matthew's (M20 §5) — reduction approved, publication not yet in question |
| eROSITA DR2 candidate vetting | [#5](DISCOVERY/run3-prospectus.md) | [`erosita-dr2/`](erosita-dr2/) | **M2 running (review delegated by Matthew, 2026-08-14)** — per-candidate verdicts on the M1 set: NWAY counterparts, archival X-ray history, ASAS-SN light curves, TNS/ATel already-reported checks, §3.2.5 vanished-source forensics. M1 stands: 632,668 pairs, known transients recovered, headliner 3eRASS J094452.8−711152 (×57, no counterpart) | review the M2 shortlist + verdicts when they land; anything live/report-worthy gets flagged, never auto-reported |
| Gaia DR4 day-one prep | [#4](DISCOVERY/run3-prospectus.md) | [`gaia-dr4/`](gaia-dr4/) | **M1 done** — pre-release claims all confirmed; `gaiasupdate` 0.1.2 runs on Windows (12/12 fits); **BH3 orbit reproduced** (P 11.45 vs 11.6 yr, M2 34.7 vs 32.7 M☉); 3 day-one ADQL queries DR3-validated; BH1/BH2 fixtures pulled. Landmines: DR4 epoch astrometry is **DataLink-only**, and **source_ids are not stable DR3→DR4**. Next: M2 AMRF triage | create Gaia Archive + NOIRLab Data Lab accounts (needs Matthew's email) |

## Queued fronts (not started)

| Front | Avenue | Where it will live | Blocker / trigger |
|---|---|---|---|
| ITF ↔ Rubin-batch attribution + NEOCP watcher | #3 | `itf-linker/` | next session; SARC verification is a human step |
| MPTA independent CW search | #2 | new `pta-mpta/` | after the three above stabilize |
| Dyson-candidate re-vet / SPHEREx | #7, #8 | new folders | after the three above stabilize |

## Log

- **2026-08-14 (night)** — Matthew: **M31 approved**, M1-candidate review delegated, and a disk
  correction — **C: has >300 GB free**; the volume M30 saw at 7.2 GB is the ~1 TB data volume
  holding `~/cr2res` (the concurrent thread's 17 GB of products live there). Two agents launched:
  exosat-rv M31 (HiRISE extraction, disk-reconciliation first, no cross-thread deletions) and
  erosita-dr2 M2 (per-candidate verdicts; nothing gets reported externally without Matthew).
- **2026-08-14 (evening)** — All three fronts reported and committed. **gaia-dr4 M1 ✓**: every
  pre-release claim confirmed; BH3 orbit reproduced with ESA's own package; DataLink-only epoch
  astrometry + unstable source_ids now on the map. **erosita-dr2 M1 ✓**: 632,668 clean DR1↔DR2
  pairs; known transients recovered end-to-end; unidentified candidates delivered (headliner:
  3eRASS J094452.8−711152, ×57 rise, no counterpart). **exosat-rv M30 ✓** with the day's biggest
  lesson: run-3 avenue #1's dataset claims were all already ledgered and its counts wrong —
  corrected in place; the verify-first gate cost hours instead of wasted campaigns. A concurrent
  session opened M27 mid-M30 (first validated HiRISE extraction); both threads merged their ledger
  edits additively. Open human gates: M31 approval, m1_candidates review, two accounts, disk
  cleanup (7.2 GB free).
- **2026-08-14** — Run-3 sweep folded in ([`DISCOVERY/run3-prospectus.md`](DISCOVERY/run3-prospectus.md)).
  Fronts #1/#5/#4 selected to start (Matthew's call). Folders `erosita-dr2/` and `gaia-dr4/`
  created; three agents launched in parallel. exosat-rv agent instructed to reconcile the
  sweep's TAP findings against `docs/target-queue.md` first — the queued `cd35d1` fix may
  already be the CD-35 2722 Oct-2024 data the sweep reported as new.
