# Candidate E release follow-up — 2026-09-05

**WAIT_RELEASE, not a completed experiment.** At 14:06:58 UTC the public MAST
proposal query returned 39 E observations, all `EXCLUSIVE_ACCESS`, all with
release date **2026-09-09**. The already-public D chain passed its original seven
acceptance comparisons with return code zero. The frozen outcome-map SHA-256 remains
`fa93e2c852befdb51f661f65a3a6bd92333d8e4cb8b581af33555feab87b937b`.
The [counts-only report](out/e-release-20260905.json) retains the exact check state.
No E science product was retrieved or analyzed.

## Operational correction

The historical `m6_e_ready.py` completed D's seven checks, then its separate MAST
status child stalled. The child was stopped after approximately ten minutes. Its
aggregate `ready` field does not require a successful metadata return, so that
field cannot authorize a release-day run. The historical wrapper and all frozen
scientific scripts are unchanged.

The new [bounded release guard](scripts/check_e_release.py) checks the same public
D control, a fresh proposal-only metadata response, the pinned outcome-map hash,
rights/count conservation, the expected release date, and the actual UTC date.
Failed/empty/malformed responses stop; a date/count/rights change stops for review;
an early public release still waits. It never fetches or analyzes E. Eleven offline
regression tests cover the decision gates and own-process-tree timeout cleanup.
An actual marked Windows venv child with a 15-second sleep was stopped by the
one-second timeout in 1.11 seconds; a process inventory found no marked child
remaining. This tests timeout cleanup, not archive performance.

```powershell
cd dyson-revet
.venv/Scripts/python.exe scripts/check_e_release.py --out out/e-release-latest.json
```

Only `READY_FOR_FROZEN_ANALYSIS` permits proceeding to the already-frozen M5
status/fetch/measure chain, using the [front summary §6](FRONT-SUMMARY.md) and
M5 §5.2–5.3. Apply M7 §1.7's determinacy checks and §1.4's contrast-dependent
bias limitations before interpreting the four outcomes. Passing imaging acceptance
does not validate the defective narrow-line redshift criterion that M7 identified.

The `astronomy-closeout-follow-ups` task checks this on or after September 9.
It records actual execution/verification when the data become public. Until then
the experiment is pending. Candidate A's July 16, 2027 release is a later standing
trigger, not part of today's completed work. All publication, correspondence and
proposal choices remain human-gated.
