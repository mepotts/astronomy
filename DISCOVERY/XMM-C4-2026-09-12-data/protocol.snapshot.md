# C4: bounded local attitude-value diagnostics, not continuous coverage

Prospective September 12, 2026. Freeze source, numerical core, tests and
independent review before reading the ATTHK payload. This follows the
[retained attitude input](XMM-C3d-RESULT-2026-09-12.md) and
[time-reference/quality interpretation](XMM-ATTITUDE-TIME-REFERENCE-2026-09-12.md).
No network, product acquisition, photon/event/source-list or map-array access.

## Exact inputs and interpretation

Use only C3d's expanded `P0884250101OBX000ATTTSR0000.fits`, SHA-256
`ff251ab4e22655bc02b612a599160e40cfe3176cf8de90ce4514668e5bcf7a17`, and
header report `a5c5d3a9113b88b63e560be09dc72df0ece14b35c8e91fdefcbc73c77a8d8409`.
Preserve and bind C3d outcome
`2a1a7340c89292882f2b205ff48f4babbada46ed4dde210b45ec1bdd4a6bed0d`.
Its offline replay verifies input/header provenance without interpreting arrays.

Require PRIMARY OBS_ID 0884250101, the unique ATTHK extension, exactly 51975
rows of 80 bytes, ten scalar big-endian D columns in this order:
TIME; AHFRA/AHFDEC/AHFPA; OMRA/OMDEC/OMPA; DAHFPNT/DOMPNT/DAHFOM.
TIME unit sec, other units degrees. Validate BINTABLE/8/2, TFIELDS10,
PCOUNT0/GCOUNT1 and absence of TSCAL/TZERO/TNULL/TDIM or heap extensions.
Duplicate relevant semantic/layout keys or ambiguity stop. Derive the offset
from the bound header record, verify exact 4158000-byte payload arithmetic and
its span within the 4173120-byte input. No other array is eligible.

Use hash-bound C1 outcome and only the three existing EVENTS header reports to
obtain independently declared camera identities, TSTART/TSTOP and
TT/MJDREF50814/TIMEZERO0. Never decode those EVENTS or GTI arrays in C4.

Adopt the documented XMM TT seconds since MJD50814 convention provisionally
for the attitude TIME comparison, with no fitted offset or first-sample reset.
This is an explicit interpretation, not a fabricated file keyword. Range
agreement with C1 supports compatibility, not clock/barycentric verification.
Retain the absence of attitude reference keywords and every mismatch.
The header's task history declares timestep1: use one-second cadence with a
prospective 1e-6-second numerical tolerance, not a cadence chosen after values.

## Required aggregate diagnostics

- Count finite, NaN and infinite values for every column. NaN is missing;
  infinity is invalid, and zero is not a missing-value sentinel. Retain all
  rows. Count fully finite, wholly NaN and partially finite triplets separately.
- Apply declared sanity domains RA/PA in [0,360] degrees and declination in
  [-90,90]. Count finite out-of-domain triplets separately before angular math;
  these are engineering sanity exclusions, not proof of instrument quality.
  Do not modulo-normalize a huge finite sentinel into a plausible direction.
- Compute finite and domain-valid AHF/OM and joint counts independently; compare
  finite counts with NATT/NGAHF/NGOM/NGAHFOM without forcing agreement. The
  existing header-counter inconsistency must remain visible.
- Report finite TIME range, finite/nonpositive adjacent steps and non-unit
  positive steps. Compare the unchanged TIME axis with each C1 header range,
  retaining sample counts and whether a finite strictly ordered attitude axis
  brackets it. This is not a GTI, exposure or clock-reference proof.
- For each source, use its first finite-time/domain-valid row as a deterministic
  pointing reference. Report great-circle separation extrema relative to it.
  For adjacent original rows only, require both eligible and one-second cadence
  before computing spherical pointing steps and shortest wrapped PA steps.
  Report measured and unmeasured adjacent-pair counts. Never bridge a missing
  row or gap. PA change is separate, not a full 3D attitude/footprint rotation.
- Report finite degree extrema of the three relative-offset columns and counts
  outside [0,180]; convert only that domain's values to arcseconds. Do not
  export absolute AHF/OM angles, reference coordinates or individual rows.

No motion threshold, clean-region selection, interpolation guarantee or
continuous-displacement bound is asserted. Low sampled movement cannot prove
what occurred between samples. Keep summary status explicitly
`SAMPLED_ATTITUDE_DIAGNOSTICS_NOT_COVERAGE` even when all samples look finite.

## Execution, accounting and verification

One exclusive local attempt, 60-second worker via the pinned process-tree
helper with separate cleanup; monitored worker/parent peak <=500000000 bytes,
not an OS allocation quota. Use direct bounded binary reads and explicit >f8
decoding, at most 10000 rows per chunk. The full selected 4158000-byte table
may reside in memory for numerical diagnostics; no complete FITS-array API.
Exactly that payload is permitted per pass. Track bytes actually read and
decoded, including failure; retain truncated/malformed-marker evidence safely.
If hard termination occurs before a table receipt is saved, exact read/decoded
bytes are unknown, not zero, and bounded above by one payload pass under the
bound decoder. Caught truncation retains exact returned and decoded counts.
Interrupted/unverified attempts permit failure-artifact replay only.

Parent independently rereads/recomputes the one selected table under a new
4158000-byte per-pass budget. Offline replay repeats that same explicitly
additional pass, never a cumulative claim of only one file read. Bind source,
core/tests, protocol snapshot, C3d/C1 evidence/dependencies, runtime and actual
configuration. No old network worker/plan is called; prior replay is read-only.
JSON <=1048576 bytes total with65536 reserved for terminal receipts. No arrays
or absolute pointing in artifacts, exceptions, warning text or worker output.
Exact result/artifact/byte closure and nonzero/timeout handling must be tested.
Failure-artifact-only replay is not numerical verification.

Strongest execution outcome `ATTITUDE_VALUES_SUMMARIZED_UNCALIBRATED` certifies
bounded diagnostic execution and replay, not good attitude, accepted geometry,
camera simultaneity, burst recovery or a new discovery. Frozen failures remain
unchanged. Publication, submission and private-coordinate disclosure are gated.
