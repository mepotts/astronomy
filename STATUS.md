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
| exosat-rv M31: HiRISE extraction of HIP 65426 | [#1](DISCOVERY/run3-prospectus.md) | [`exosat-rv/`](exosat-rv/) | **M31 done** (`M31-RESULTS.md`, commit e244cf9) — 27/27 frames extracted through the fibre chain, all three nights PASS contents gates; **night 2 on-sky proven at 11.8σ** (benchmark 9.8σ), nights 1/3 CCFs 5σ/2.9σ at 0 km/s with strong controls (per-night numbers are the honest ones). **Key finding: HIP 65426 b sits 40–130× below the fibre background — planetary-CCF ceiling ~2–3σ — so this corpus is a telluric/sky reference + methods asset, not a companion dataset.** Disk: stayed on ext4 (ESO filenames contain colons; NTFS rejects them), sanctioned cleanup only, science raw + masters kept. Two new traps ledgered | exomoon lever for HIP 65426 b remains the K2192 slit series — Matthew's priority call (M20 §5); M32 scope = coordinate with β Pic thread (injection gate on util_ chain first) |
| eROSITA DR2 candidate vetting | [#5](DISCOVERY/run3-prospectus.md) | [`erosita-dr2/`](erosita-dr2/) | **M3 done** ([`J0944-decision-package.md`](erosita-dr2/J0944-decision-package.md), [`M3-state-bounds.md`](erosita-dr2/M3-state-bounds.md)) — J0944 class revised by sub-band spectrum: peaks 1–2 keV, soft-suppressed at ~Galactic N_H → **Galactic VFXT/subluminous-LMXB or magnetic CV ≳2 kpc**; supersoft/TDE-thermal/Be-HMXB/blazar excluded; assumption-free rise floor **≥×20**; every catalog-testable riser artifact mode excluded (only single-visit detector artifact untestable without event data). DRAFT Swift ToO ready (5 ks XRT+UVOT), NOT sent. **State bounds: zero post-eRASS pointed X-ray data on all five shortlist objects — three never observed by Swift/XMM/Chandra at all**; J0503 = Swift-persistent through 2013, gone by 2020–21. M2 history: 381 verdicts, 1 unexplained survivor (×57 hard-spectrum riser, DET_LIKE_3=197, NWAY p_any≈0 in GDR3+CW2020, zero archival X-ray across 6 catalogs, TNS/SIMBAD/literature empty). Vanished list split 148 artifact / 107 plausible faders / 6 indeterminate (UL-server-calibrated — geometry alone would have mislabeled 94 real faders); M1's top-20 vanished was artifact-selected, corrected; M1's "G=20.6 galaxy" TDE host downgraded (g=23.5 at 7″, p_any=0.002). Several M1 headliners = known transients (ATel/EP/MAXI). Consortium file defect found: `eRASSc3_Main_GDR3` ships `GDR3_source_id` twice | **Matthew: J0944 decision** — approve M3 (Swift archival state bounds + decision package, still nothing sent)? Optional: report the duplicated-column defect to MPE (email = human-gated) |
| Gaia DR4 day-one prep | [#4](DISCOVERY/run3-prospectus.md) | [`gaia-dr4/`](gaia-dr4/) | **M2 running (approved wave, 2026-08-14)** — AMRF compact-companion triage on the full DR3 NSS set; acceptance = recover BH1 + BH2 (BH2 is `AstroSpectroSB1`); false-positive calibration against El-Badry 2026's followed-up sample; freeze the DR4-day config. M1 history: pre-release confirmed, BH3 reproduced, ADQL validated, DataLink/source_id landmines mapped | create Gaia Archive + NOIRLab Data Lab accounts (needs Matthew's email) |

| ITF ↔ Rubin-batch attribution | [#3](DISCOVERY/run3-prospectus.md) | [`itf-linker/`](itf-linker/) | **ACTIVE (approved wave, 2026-08-14)** — agent running: attribution-capability scope check, bounded run of ITF orphans against a Rubin designation batch (validation slice, gated candidates only), + the northern-TNO feasibility stat. Reads HANDOFF first; never touches the archive clone | review gated attribution candidates before any MPC submission (always human-gated); SARC verification only needed for the separate precovery lane |

## Queued fronts (not started)

| Front | Avenue | Where it will live | Blocker / trigger |
|---|---|---|---|
| exosat-rv next milestone | #1 | `exosat-rv/` | **deliberately idle from this session** — concurrent thread owns the folder (M27/M32 active; milestone numbers must not collide); next dated triggers: β Pic header probe 2026-09-25, CD-35 joint-fit campaign from 2026-12-19 |
| NEOCP high-e watcher (4I race) | #3 | `itf-linker/` or sibling | after the attribution slice lands |
| MPTA independent CW search | #2 | new `pta-mpta/` | next wave |
| Dyson-candidate re-vet / SPHEREx | #7, #8 | new folders | next wave |

## Log

- **2026-08-15** — Matthew: "continue with the recommended next steps." Wave 2 launched: eROSITA M3
  (J0944 package + state bounds), gaia-dr4 M2 (AMRF triage), and the ITF↔Rubin attribution front
  promoted from queued to active. exosat-rv deliberately left to the concurrent thread + its dated
  triggers. Branch pushed through f928a91 with Matthew's approval (J0944 now has a public
  timestamped record).
- **2026-08-14 (late)** — **erosita-dr2 M2 ✓** (one API-error crash, resumed with context intact):
  381 verdicts, one survivor — 3eRASS J094452.8−711152, the only GENUINELY-UNEXPLAINED object.
  The vetting corrected M1 twice (top-20 vanished was artifact-selected; TDE host association
  collapsed) — the M1→M2 correction chain is the method working. M31: nights 1–2 banked
  (night 1 on-sky CCF 16.4σ at 0 km/s), night 3 reducing.
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
