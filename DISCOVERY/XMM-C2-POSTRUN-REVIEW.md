# XMM C2 independent post-run review

2026-09-12: **PASS for ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED.** Independent
review covered retained receipts, manifest and summaries only; no scientific
array was decoded again and no request or earlier-artifact change was made.
Integrity hashing traversed original product bytes without interpreting arrays.

## Provenance and accounting

All 99 C2 outcome artifact hashes, 98 worker artifact hashes and 32 C1 outcome
artifact hashes match. C2 source/tests/protocol snapshot, C1 source/outcome,
helper identity and worker-start binding agree with the saved run manifest.
Worker exit code is 0, parent assessment completed, both statuses have the exact
limited label above, and photons_interpreted is false.

All 48 planned tables have one ordered start marker and an OK result. Each
summary row count equals its manifest row count; each receipt byte count equals
rows times the accepted fixed row width. The 24 STDGTI and 24 EXPOSU tables
account for exactly 97029016 read and interpreted bytes per measurement pass.
No extra table marker or unaccounted planned table was found. The final table
start marker is at approximately 2.14 worker seconds, below the 120-second bound;
that marker is not itself a measurement of total runtime.

Actual aggregate JSON is 162891 bytes, below 1 MiB. The worker's 138589-byte
pre-worker-result snapshot and parent's 150569-byte pre-outcome snapshot
independently reconcile with the later receipt sizes. Recorded worker peak is
131837952 bytes and parent peak 131719168 bytes, below 500000000. These are the
execution's retained measurements, not newly measured historical peaks.

All 137 files initially present across C1 and C2 remained byte-identical after
this audit, with no additions inside either stage. This audit did not perform
another actual-array replay; the parent's existing successful replay remains a
separate numerical-verification receipt rather than being claimed as reviewer
execution.

## Findings from retained summaries

Every table's data_quality_flags list is empty. All 833 GTI rows are reported
finite, positive-length, ordered and non-overlapping within their own tables.
All 7986902 exposure rows are reported valid under the explicit finite-time,
positive-width and fraction-in-[0,1] predicate, with no timestamp duplicates or
non-increasing adjacent timestamps. These statements describe retained C2
summaries and the verified frozen method, not an independent payload decode.

| Camera | GTI rows | EXPOSU rows | Per-CCD valid GTI union duration range, seconds |
| --- | ---: | ---: | ---: |
| pn | 564 | 7693686 | 46745.118–47364.392 |
| MOS1 | 114 | 128045 | 49343.262–49418.892 |
| MOS2 | 155 | 165171 | 49494.471–49586.276 |

Every valid exposure-row timestamp is in its matching valid GTI union. Thus
the unrestricted and GTI-member fraction-weighted width sums are identical in
these retained results. This does not establish exact frame-interval integration
at GTI boundaries, nor simultaneous good time across cameras or CCDs.

Fraction-weighted width sums minus explicit EVENTS per-CCD LIVETInn range from
approximately +0.048 to +0.319 seconds for pn, +7.990 to +13.328 seconds for MOS1,
and +0.000014 to +16.026 seconds for MOS2. In contrast, those same sums are below
per-table EXPOSU LIVETIME by roughly 6538–6897 seconds for pn and 108–412 seconds
for MOS. Global EVENTS scalars and per-CCD scalars remain different metadata;
none is silently substituted for another or rescaled to force agreement.

Near agreement with one benchmark is useful descriptive evidence, not validation
of an exposure prescription. Documentary semantics must establish how TIMEDEL,
FRACEXP, frame spacing and already-applied dead-time corrections should be used.
Do not select a correction because it best matches an observed scalar. Per-CCD
GTI durations also cannot simply be summed into one aperture's live exposure.

## Identity and next scientific boundary

Outcome SHA-256:
`bd69d5df9effd0a4097016a324f971467b4934b9ff048d1dd58eb17a1b8fff39`.
Source SHA-256:
`357edd17ee84755011e9adb41ecf523063be9303501d060bbfc416ceecd23f68`.
Executed protocol snapshot SHA-256:
`ba74dd568f177de9f04042b34c9ac3cfac1ef3f9af6009fd66552370bc956f6a`.

The next step remains the separately defined exposure-semantics and minimal
geometry assessment toward a prospective counts experiment. C2 does not prove
quiet background, source isolation, useful sensitivity, recovered bursts,
calibrated significance or a discovery. No photon selection, exposure correction,
threshold tuning, new field, publication or submission follows automatically.
