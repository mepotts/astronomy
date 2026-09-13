# C4 measured complete one-second sampled attitude, not continuous coverage

**ATTITUDE_VALUES_SUMMARIZED_UNCALIBRATED.** The
[protocol](XMM-C4-2026-09-12.md), numerical core, wrapper, 24 tests and
[independent review](XMM-C4-REVIEW.md) were frozen in commit `19f935c`
before the sole local attempt. Worker exit 0, parent assessment completed,
one OK table. Root's subsequent offline numerical replay passed exactly.
This is the first actual ATTHK-value interpretation, not an event-count run.
[Independent postrun audit](XMM-C4-POSTRUN-REVIEW.md) verifies receipt/hash
closure and aggregate arithmetic without adding another numerical data pass.

## Measured evidence and decision

All **51975 rows** are finite in all ten columns, with no NaN, infinity or
angle-domain failure. TIME is strictly increasing from 738528542.1840001 to
738580516.1840001 in the prospectively adopted mission convention. All 51974
adjacent steps are exactly one second. The unchanged axis brackets all three
C1 EVENTS header ranges; their half-open ranges contain 49072 pn, 50023 MOS1
and 50195 MOS2 samples. There was no fitted time offset.

Both AHF and OM aggregate diagnostics report the following:

| Sampled diagnostic | Maximum, arcseconds |
| --- | ---: |
| Separation from first eligible direction | 1.7041471682500233 |
| Consecutive one-second direction change | 1.2058678464359744 |
| Consecutive wrapped position-angle change | 4.724120624416628 |
| Recorded offset from nominal pointing | 1.1063967264563714 |

All adjacent pairs were measurable under the declared rules. DAHFOM has zero
minimum and maximum throughout its finite domain. Equal aggregate results do
not independently establish identical raw streams or independent sensors.
No absolute direction, reference angle or individual row is exported.

The header's **NGAHFOM=0 disagrees with 51975 jointly finite triplets**; the
other three finite-count comparisons agree. This resolves the specific
question of whether missing/nonfinite values explain that zero: they do not.
It does not resolve the producer's bookkeeping semantics or certify quality.

The outcome supports proceeding to fixed-region map diagnostics: no sampled
time gap, nonfinite-angle obstacle or large sampled drift was found. It does
not establish between-sample displacement, calibrated clock reference,
instantaneous detector masks, stable live exposure or burst recovery. Do not
convert the measured 1.70-arcsecond maximum into a guaranteed continuous
motion bound. Map/filter compatibility is the next practical adjudication.
The [map adjudication](XMM-MAP-COMPATIBILITY-2026-09-12.md) now supports a
static fixed-region screen, but rejects using the retained maps as matched
FLAG-zero per-bin exposure denominators. Source/background geometry and a
separately frozen photon-stage interpretation still need implementation.

## Accounting and provenance

Only the exact 4158000-byte ATTHK span was decoded, in six bounded chunks.
Worker, parent independent numerical assessment and root offline replay each
read and decoded **4158000 payload bytes**: three separate passes totaling
12474000 decoded bytes. Product hashing/header validation also reads bytes
but does not interpret scientific arrays; this is not a total filesystem-I/O
claim. No network, photon, map-pixel, GTI or source-list array access occurred.

Recorded worker/parent peaks are 68259840/69058560 bytes, below 500000000.
Final JSON totals 11460 bytes, below the 1048576-byte stage budget.
The worker retains its 60-second bound and separate cleanup. A hard-killed
attempt without a receipt would have unknown, not zero, read counts; this
successful attempt has exact per-pass receipts and numerical replay.

| Artifact | SHA-256 |
| --- | --- |
| Runtime | `d53d265ebf3ff82832137da2ee7e0fffcf7f1095f143790c655a8fd0f8915e39` |
| Runtime tests | `b37ccf15c5834420c8257b2eb37c4932a8cd14de4bc3449c30a6e8755ffca606` |
| Numerical core | `df6a49a01d20f6b58c275881fea48a95de158ee6e8c04c272b0ef2ac616f7f4a` |
| Core tests | `1af690f296a88d8e6267d055eb2d17f32e8742d37c68e3f03936fd8e7098027f` |
| Protocol snapshot | `a4b27125eed686b706126fe502be0147feb18db502cbe3627ef630766a91b4bc` |
| Aggregate table result | `144db736240757432cd5496459e907dea23a09be3ae9c2c87ef0da5c95d70e90` |
| Outcome | `67d5cec964c1c36b592202a8faeaa70999b7e53762abced1bf6ecd28f6a0ec55` |

The preserved C3d input and all prior STOPs remain unchanged. No discovery or
scientific submission has been made. The larger discovery goal remains active.
