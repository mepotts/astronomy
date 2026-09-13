# C9 prospective runtime contract: recorded counts only

**Not yet frozen or executed.** This contract adopts the complete immutable
selection/output specification in
[recorded-counts plan](XMM-RECORDED-COUNTS-PLAN-2026-09-12.md). Both documents
must be hashed in the final runtime manifest. Independent review, synthetic
full-size benchmarking, final dependency pins and a committed exact-byte
runtime/tests/protocol freeze precede any actual EVENTS value access.

## Scientific interpretation fixed before photons

Only observation0884250101, the known published control. All three C1 imaging
event products remain in scope in pn/MOS1/MOS2 order. Five unchanged C5 centres,
20arcsec circles and **unmasked**60–90arcsec annuli; no new coordinates or shifts.
C8 outcome82cd6df3d673c86059494e9d38a3bfd1312ee9ce8b19301873309dfc995ad16e
and its complete aggregate table result must accompany the result by binding.
North/east/west aperture contacts and all five annulus contacts remain explicit;
two usable negative regions have not been established. C5/C7 static-map findings
remain unchanged, not exposure estimates. Do not reread those maps in C9.

The stronger recovery draft remains unchanged at
7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e.
No counts-to-rate conversion, area subtraction, source-exclusion mask, GTI or
EXPOSU integration, detector-artifact veto, significance, episode search,
calibrated recovery, unknown-source search or discovery claim is authorized.
The strongest label is `RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY`.

## Exact inputs and metadata verification

Use only C1 slots1–3 expanded retained products, with exact byte/hash/header
anchors and camera time intervals in the implementation plan. Independently
verify C1 outcome, slot receipts, full products and structural header reports.
Hash/header reads are opaque/structural I/O, not decoded-field counts.
Do not replay any earlier acquisition or numerical stage to do this.

Use the reviewed `xmm_event_rows` full packed schema, `xmm_event_geometry`
selected X/Y TAN adapter and `xmm_recorded_counts` fixed counter, each with
source/test hashes fixed before execution. Runtime binds structural/helper
dependencies and C1 source/tests. All table framing, offsets, camera/frame/time
identity, TFORM/units/nulls and row bounds must match the pinned reports, not
merely a filename or the first convenient HDU. Require zero new structural
parser warnings and no dropped conflicting WCS declaration.

Centres are copied from exact frozen C5 construction with full-function AST
equality and source hash, preserving the published ICRS convention and FK5/J2000
transform. Neither direct frame relabelling nor a source-list-derived offset.
Project only X/Y-valid rows with unchanged stored coordinates and FITS origin1;
never project a declared null. Geometry warnings/nonfinite outputs STOP rather
than becoming outside-aperture counts. Keep geometry completion separate from
decoder conversion and histogram accumulation.

## Counts and fixed output grid

Edges are exactly `738530124.914825 + 200*k`, k=-8..246 inclusive,254 bins.
Every bin is half-open, every absolute edge retained. Preserve all camera/
region cells, zeros and header-edge partial intervals. No bin shifts or cuts
chosen from observed counts. If header-overlap durations are included, label
them as header overlap, never wall-clock GTI coverage/live exposure.

Use the plan's six ordered disjoint rejection categories: selected missingness,
unsupported CCD, outside inclusive camera header time interval, outside strict
200<PI<12000, PATTERN above4pn/12MOS, nonzero FLAG. Retain overlapping per-field
null/nonfinite diagnostics as well as the disjoint total ledger. Do not infer
GTI validity, calibration quality, clean detector or EXOD-equivalent cuts.

Return all254x5 integer circle and annulus histograms per camera, unchanged
label order, accepted/inside-grid/outside-grid totals, the rejection ledger and
aggregate accepted/per-region CCD totals. All increments and sums are checked
integers. Same-centre circle and annulus cannot overlap; different-centre
memberships may overlap and are not an exclusive partition. Geometry-valid
membership must cover every decoder-row-valid event and never include X/Y nulls.
Verify per-camera/per-CCD/histogram/row closure, not just headline totals.

No source IDs/absolute sky coordinates, per-photon timestamp arrays, pixel
lists, row ordinals of interesting events or hidden position cache in outputs.
Predeclared bin edges and aggregate count arrays/CCD labels are allowed.
Do not publish top bins or infer a period in this stage.

## Streaming, receipts and caps

Stream at most10000 complete rows per unbuffered read. Exact payload accounting:

| Camera | Rows | Opaque row bytes | Decoded selected bytes | Chunks |
| --- | ---: | ---: | ---: | ---: |
| pn | 2694388 | 121247460 | 75442864 | 270 |
| MOS1 | 273441 | 9296994 | 7656348 | 28 |
| MOS2 | 356129 | 12108386 | 9971612 | 36 |
| Total | 3323958 | 142652840 | 93070824 | 334 |

Whole-row reads physically include unselected bytes; only the nine declared
fields are decoded. Worker and parent are distinct passes. A full numerical
replay is a third pass:427958520 opaque row bytes and279212472 selected bytes
over three complete passes. No implicit fourth pass for audit/integration.
Report incomplete reads/conversions and failed parent/replay work separately.

One exclusive worker processes all three cameras under the existing pinned
process-tree deadline helper: **120seconds**, plus its existing cleanup allowance.
Parent/replay numerical assessment has a separate120second cooperative deadline,
not an OS-enforced CPU limit. Monitored peak memory **536870912bytes** for
worker and parent; no claim of OS allocation prevention. Aggregate JSON cap
**4194304bytes**, terminal reserve **262144bytes**. These prospective caps
need a synthetic-only full-size fit check before freeze; no post-failure
increase/retry follows automatically from this contract.

Exclusive run/worker/camera and per-chunk start/result receipts. Exactly three
ordered camera stages and334 known complete chunks on success. Retain a safe
current partial read/decoder/geometry/accumulation state on caught failures.
Advance returned-byte counters immediately after reads and decoder completion
counters before later storage. A hard-killed active chunk with no terminal
receipt means unknown work, not zero. Per-chunk IDs/order are operational
progress, not IDs of scientifically selected photon rows.

Parent recomputes numerical summaries without rewriting worker receipts;
independently checks all dependencies, labels, grids, shapes, histograms,
ledger, resources and artifact closure. Parent failure retains partial-pass
counters. Read-only replay emits additional-pass accounting on success **and
failure**, including a late comparison failure after complete reads. Failure
artifact-only replay is separately labelled and cannot validate numbers.
Reject extra/nested JSON, orphan markers, changed inputs, missing/duplicate
chunks, impossible accounting, unexpected files and exclusive re-invocation.
No product copies, network access or unsafe exception payloads in receipts.

## Completion and next decision

Operational success reports raw recorded counts only, with C8 contact warnings
and unavailable stronger gates attached. A raw burst-looking pattern does not
establish exposure-corrected variability or scientific novelty. No attractive
camera/region may replace the planned denominator. A non-recovery-looking
result is retained without shifting the grid, radius, energy cuts or field.
Scientific continuation requires a separately specified experiment rather than
silently turning this descriptive screen into the original recovery test.
