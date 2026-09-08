# Discovery follow-through - September 8

**Two further validation experiments completed; no new discovery.** This is not
an assertion that every possible research programme has been exhausted. The work
materially narrows which DASCH searches the earlier validation supports.

1. **ITF daily operations verified healthy.** Windows publisher ran September 8
   at 08:30:01 local, result 0, missed runs 0. GitHub watch
   [34242760554](https://github.com/mepotts/astronomy/actions/runs/34242760554)
   succeeded. Actual log: snapshot `20260908T122624Z`, advanced, age 2.7037 hours,
   20 ready / 6 held, no count change and no freshness alert. No competing
   publisher, queue mutation, attribution search, or discovery claim.
2. **DASCH real-event transfer test: STOP.** Three published long-term variables,
   nine new public archive responses. The unchanged matched-colour detector
   recovers 0/3 specified real events, including zero before catalogue vetoes.
   All three have source-level coverage; event-level support and residual
   amplitudes expose limits missed by five-year injections.
3. **DASCH separate bracketed-block development: STOP.** Entire event intervals
   excluded from comparison baselines, with observations required on both sides.
   No development event recovered; 4/4 eligible signed injections span only two
   stars, below the fixed gate, and one instrumental control has no eligible
   block. Reserved real-event holdout never requested. Our control-ID mapping
   typo stopped the first execution and was corrected against the original
   usable-control record, with an explicit history and regression test.

[Full outcomes, limitations, source citations, plot and replay commands](../dasch-pilot/RESULTS-2026-09-08.md).
The original September 7 42-source null, 16/16 injection result, and both new
failed experiments are retained without threshold changes or retrospective passes.
No new unknown-source sample, candidate-coordinate payload or scientific upload.

## Next decisions

- **Dyson E remains first**, on/after September 9, under the already frozen
  [release guard and experiment](../dyson-revet/E-FOLLOWUP-2026-09-05.md). Do not
  access E science products early or substitute a readiness check for analysis.
  Existing daily follow-up remains unchanged; no duplicate automation created.
- **Do not scale these DASCH detectors.** A future same-plate ensemble/series-overlap
  calibration experiment is materially different research, not another threshold
  tweak. Defer it behind E. Current data show that artificial five-year recovery
  alone is inadequate evidence for searching long historical changes.
- CCOR/DR11 stay at their recorded failed search-readiness gates. Gaia's planned
  December release, TNS/CHIME's missing inputs and the publication gates remain.
  PTA full paper stays the chosen publication unit; no consent/endorsement/DOI
  or submission was invented. eROSITA and SPHEREx remain deferred by choice.

## Verification

52 DASCH tests (18 new); unchanged real-control and new block-development cold
replays; root document/link/syntax verification; pinned Ruff. CI is extended with
the two public, network-free numerical replays. The generated evidence plot was
visually reviewed. Hosted checks and exact integration outcome are reported only
after they actually complete, in the task handoff.
