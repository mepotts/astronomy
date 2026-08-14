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
| exosat-rv M30: new public CRIRES+ epochs | [#1](DISCOVERY/run3-prospectus.md) | [`exosat-rv/`](exosat-rv/) | agent launched — ledger reconciliation + TAP verification + phase–BERV pre-checks; download only if verified | approve any reduction campaign (M31); HIP 65426 priority call still Matthew's (M20 §5) |
| eROSITA DR2 first sweep | [#5](DISCOVERY/run3-prospectus.md) | [`erosita-dr2/`](erosita-dr2/) | **M1 done** — 632,668 clean DR1↔DR2 pairs via consortium cross-walk (DR2 has no per-eRASS fluxes; catalogue-only); known transients recovered end-to-end (QX Nor ×475, SWIFT J1626.5−5156, V1708 Sco B); **candidates: 3eRASS J094452.8−711152 (×57 rise, no Gaia/SIMBAD), a TDE-like fader on a G=20.6 galaxy, 7 optical-faint vanished sources**; 140-row candidate CSV in `out/`. Next: M2 vetting | review `erosita-dr2/out/m1_candidates.csv` before any follow-up claims |
| Gaia DR4 day-one prep | [#4](DISCOVERY/run3-prospectus.md) | [`gaia-dr4/`](gaia-dr4/) | **M1 done** — pre-release claims all confirmed; `gaiasupdate` 0.1.2 runs on Windows (12/12 fits); **BH3 orbit reproduced** (P 11.45 vs 11.6 yr, M2 34.7 vs 32.7 M☉); 3 day-one ADQL queries DR3-validated; BH1/BH2 fixtures pulled. Landmines: DR4 epoch astrometry is **DataLink-only**, and **source_ids are not stable DR3→DR4**. Next: M2 AMRF triage | create Gaia Archive + NOIRLab Data Lab accounts (needs Matthew's email) |

## Queued fronts (not started)

| Front | Avenue | Where it will live | Blocker / trigger |
|---|---|---|---|
| ITF ↔ Rubin-batch attribution + NEOCP watcher | #3 | `itf-linker/` | next session; SARC verification is a human step |
| MPTA independent CW search | #2 | new `pta-mpta/` | after the three above stabilize |
| Dyson-candidate re-vet / SPHEREx | #7, #8 | new folders | after the three above stabilize |

## Log

- **2026-08-14** — Run-3 sweep folded in ([`DISCOVERY/run3-prospectus.md`](DISCOVERY/run3-prospectus.md)).
  Fronts #1/#5/#4 selected to start (Matthew's call). Folders `erosita-dr2/` and `gaia-dr4/`
  created; three agents launched in parallel. exosat-rv agent instructed to reconcile the
  sweep's TAP findings against `docs/target-queue.md` first — the queued `cd35d1` fix may
  already be the CD-35 2722 Oct-2024 data the sweep reported as new.
