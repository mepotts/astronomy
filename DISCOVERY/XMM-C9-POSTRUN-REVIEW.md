# C9 independent receipt and aggregate postrun audit

**PASS: receipt/provenance closure and aggregate arithmetic.** The scientific
status remains `RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY`. This review on
2026-09-13 follows the parent-reported exact-byte freeze `e4c069d` and successful
C9 execution. It does not constitute a fourth numerical pass or a recovery
claim.

## Scope and independently checked anchors

Only saved receipts, aggregate summaries, source/protocol/test files and
metadata bindings were read. An explicit `Path.open` guard rejected retained
`products` paths; `measure`, `verify_product` and numerical `replay` had raising
tripwires. No product opens, photon/ancillary arrays, network requests, earlier
stage replay, source-coordinate output, top-bin ranking or episode search.
All stage file hashes were identical before and after the audit.

| Evidence | SHA256 |
| --- | --- |
| `outcome.json` | `f27b9848b470cf8adf693f3a106e8b88d85c802f6e1effff67667773eb20d109` |
| `run-start.json` | `d5c85c7046ab15e5d479341a0fed9d4ccd0dfa64fc939f972be756fcf14cf77a` |
| `worker-result.json` | `c8c4290f4fd1465431332cb1f859bda9b247afb1d054e18eff7e05d32da6ac69` |
| `camera-1-result.json` | `2965dc30e333fd3dcba8a3a354047d88399000c076ca0cec25465239ec411aa7` |
| `camera-2-result.json` | `06aa216a86dd4ed41f7e75130b0628a433963ad8c3064433aad9d14d0e46e8d2` |
| `camera-3-result.json` | `f0084736361b7ffafe2d46fefecedbc81c8987191591c7ae3ae00fc0017e3959` |

The saved manifest exactly matches independently recomputed metadata-only
binding: 16 dependency hashes, final source
`bb8d6d8c8a737e2d8be11d6f489091a1d0f7453fd320ad80a761709d56c81d03`,
tests `9a2cc126dc6e7a48a256f77e99eac5f761651a4680f08269f8874911f3592bff`,
and protocol snapshot
`9b805b3fb46b3914550bd9d993302631f2c36d429a9f99cf8a4713bbaa308c4d`.
The C1 provenance and C8 contact-result bindings are unchanged. This verifies
their saved evidence, not their product payloads anew.

Outcome and worker inventories contain **1,355 verified artifact-hash
references** in total (overlapping inventories, not 1,355 unique files).
Exactly 334 exclusive chunk start/result pairs are present in the required
270/28/36 camera order. Every complete chunk has exact row/byte bounds,
complete decoder and geometry, completed histogram and accumulation counts,
and a syntactically valid increment hash. The audit did **not** recompute
increment hashes from photons; that numerical comparison belongs to the
recorded parent pass and parent-reported numerical replay.

## Completion, accounting and resources

Worker return code is 0; worker and outcome have the permitted descriptive
status. All camera receipts are OK, and all parent camera validation records
are COMPLETED with exact matching verification and numerical accounting.
Each current-chunk pointer is null. The independent aggregate audit checked
exact summary schemas using the reviewed receipt validator and separately
recalculated denominators and histogram/CCD arithmetic with scalar sums.

| Camera | Rows | Physical row bytes per pass | Selected decoded bytes per pass |
| --- | ---: | ---: | ---: |
| pn | 2,694,388 | 121,247,460 | 75,442,864 |
| MOS1 | 273,441 | 9,296,994 | 7,656,348 |
| MOS2 | 356,129 | 12,108,386 | 9,971,612 |
| Total | 3,323,958 | 142,652,840 | 93,070,824 |

Worker and parent receipts establish two complete numerical passes. The parent
separately reports one successful complete numerical replay; this review did
not invoke or independently repeat it. Thus the known three-pass total is
**427,958,520 physical row bytes / 279,212,472 selected decoded bytes**.
This audit adds zero. Full-product hash reads and structural header reads are
separate opaque/structural I/O: per recorded pass 246,890,880 and 1,990,080
bytes respectively, not extra decoded photons.

There are **678 JSON files, 709,146 bytes total**, below the 4,194,304-byte cap
with ample space for the prospective terminal reserve. Excluding the outcome
gives exactly its recorded 634,626 bytes; excluding both terminal outcomes
also exactly matches the worker resource receipt. Recorded worker peak is
78,946,304 bytes and parent peak 79,577,088 bytes, below 536,870,912 bytes.
Success is not proof of an OS allocation ceiling or a continuous timing bound;
the reviewed worker tree deadline and cooperative parent limit retain their
documented distinction. The postrun receipts are not a wall-time benchmark.

## Full-grid aggregate arithmetic

All nine selected fields have zero recorded null/nonfinite rows in all three
cameras. This is selected-column validity, not clean events or live exposure.
The six disjoint rejection categories close exactly to each input denominator.
Selected-field-invalid, unsupported-CCD and outside-header-interval categories
are all zero. The remaining ordered rejection totals are:

| Camera | Outside energy band | Pattern above limit | Nonzero flag | Accepted |
| --- | ---: | ---: | ---: | ---: |
| pn | 576,021 | 306,704 | 356,619 | 1,455,044 |
| MOS1 | 82,379 | 717 | 30,127 | 160,218 |
| MOS2 | 119,134 | 1,174 | 40,791 | 195,030 |

These are ordered, exclusive cuts, not marginal counts for each quality defect.
All accepted rows lie within the fixed histogram grid; that does not establish
GTI membership. All six 254-by-5 integer arrays, exact five-label order, per-CCD
accepted/inside/outside closure, and every region's histogram-to-CCD total were
checked. Same-centre circle-plus-annulus totals do not exceed the accepted
inside-grid denominator. Different-centre counts are not mutually exclusive.

Only full-grid sums are shown; no peak or time-local feature was selected:

| Fixed region | pn circle / annulus | MOS1 circle / annulus | MOS2 circle / annulus |
| --- | ---: | ---: | ---: |
| published | 777 / 7,924 | 0 / 0 | 146 / 899 |
| north120 | 939 / 8,889 | 0 / 643 | 146 / 1,539 |
| east120 | 972 / 9,493 | 78 / 1,053 | 93 / 1,017 |
| south120 | 338 / 9,651 | 0 / 0 | 0 / 133 |
| west120 | 996 / 9,527 | 0 / 0 | 115 / 1,341 |

Circle radius is 20 arcsec; annuli remain **unmasked** 60–90 arcsec. These are
selected recorded-event totals, not background-subtracted source counts.
Unequal region areas, coverage, camera responses and selections prevent direct
physical comparison or subtraction of the displayed totals.

## Preserved scientific and privacy limits

No extra sky/source IDs, per-photon coordinate/time arrays, or selected-event
ordinal lists were introduced by the checked aggregate/receipt schemas.
Absolute fixed bin edges, camera/CCD identifiers and operational chunk offsets
are allowed protocol fields. All three inference flags remain false: source
masks applied, exposure/significance computed, and private event/sky values
persisted. The bound manifest also retains `recovery_requirements_met=false`.

The MOS1 published-region zero is a genuine recorded-count result under these
fixed cuts. It is not evidence of astrophysical absence, zero exposure at every
instant, or an independently diagnosed chip cause. Likewise, positive pn/MOS2
totals do not establish a burst, persistence, calibrated detection or QPE
recovery. C5/C7 static support is not live exposure. C8's north/east/west
aperture contacts and all annulus contacts still prevent treating those regions
as established clean controls; two usable negative apertures remain missing.

No GTI/EXPOSU correction, source-exclusion mask, background subtraction,
detector-artifact veto, calibrated significance, episode identification,
period, unknown-source search or novelty conclusion was performed. The
original stronger recovery gate is unchanged. A later scientific experiment
must explicitly address its missing conditions rather than relabel these
descriptive counts as a recovery or discovery.
