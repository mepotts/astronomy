# Independent pure EVENTS geometry review

September 12, 2026 label. **Scoped numerical/header-compatibility GO after
prefreeze repair; no photon execution or coverage/recovery verdict.** Read the complete primary-document-backed
implementation plan, current geometry source and tests, and the selected
EVENTS decoder interface. No retained product, actual event/source/map array,
new coordinate query or network resource was accessed. This reviewer writes
only this report, not the implementation or its tests.

## Coordinate contract

After the synthetic checkpoint below, the parent's three-header-only smoke
found ordinary EVENTS metadata falsely rejected: `TSTART`/`TSTOP` matched the
broad `TS` prefix and pn `DPSCORRF` matched the broad `DP.*` pattern. No event
values were read and source is unfrozen. The existing synthetic header lacked
these innocent metadata cards, so its pass did not establish compatibility.
GO was withheld pending repair. The author now requires an immediate index
digit for the `TS` and `DP/DQ/CPDIS/CQDIS` transformation families; ordinary
metadata no longer collides. A new regression preserves rejection of indexed
parameter and distortion variants, and all prior rejection tests remain.
Final independent **13-test and Ruff reruns pass**. An independent smoke also
rehashed all three pinned header reports and built their selected geometries
under guards prohibiting any product open or projection call. All three pass;
no event values or reference coordinates were printed. This is header-profile
compatibility, not a measured astrometric calibration.

Stored signed X/Y coordinates are passed unchanged to `wcs_pix2world(..., 1)`.
This implements the selected `(X-TCRPX6)*TCDLT6` and
`(Y-TCRPX7)*TCDLT7` linear step, not array row/column indexing. There is no
one-unit/half-unit shift and no second application of attitude correction.

The builder validates selected columns 6/7, scalar J forms, exact nulls, observed
unit spellings, TAN/degrees, the retained negative-X/positive-Y scales and
FK5/equinox 2000. Legacy and modern frame declarations cannot conflict. It
constructs only the verified two-axis image-equivalent header and uses
`fix=False, relax=False`. Unselected DET/RAW scalar metadata is not copied into
the celestial transform. Matrix, rotation, projection-parameter, alternate-axis,
cross-reference, pole, frame-override and distortion families are rejected by
the narrow profile rather than silently discarded.

The immutable private definition stores only four finite reference values;
projection, scale and frame are fixed module constants. Its public metadata
and default representation exclude those absolute references. The builder
does not support arbitrary unequal scales: that planned synthetic variant is
a rejection test, not an additional usable instrument profile.

## Independent synthetic checks

All **13 final author tests** independently pass, as does root-invoked Ruff 0.16.5.
The suite covers the origin/reference point, roundtrip, independent TAN vector
oracle, direct pixel-list WCS comparison, immutable metadata, frame aliases,
signs/scales/schema rejection, unsupported-key families, null/supplied masks,
zero/all-masked/10,000-row inputs, shapes/dtypes/int32 range, region endpoints,
shared membership, warning failure and partial accounting.

Additional reviewer inline experiments, not additional committed unittest
methods:

- **3,000 synthetic events across three invented fields**, including RA wrap
  and near-pole declination, were projected with an independent normalized
  tangent-vector formula. All five-circle and five-annulus classifications
  agreed: **30,000 membership booleans**. Random seed 81623; no catalogue or
  event values informed the fixtures.
- Explicit null sentinels paired with a true supplied mask never reach the
  projection call. An all-false supplied mask produces no projection attempt
  and preserves masked/input/completed-row accounting.
- **25 synthetic points** match a direct table pixel-list WCS using `colsel=[6,7]`
  and unrelated DET metadata exactly. Origin 1 agrees with coordinates shifted
  by minus one and origin 0; unchanged coordinates with origin 0 differ.
- A second direct-table oracle uses native table frame cards `RADE6/EQUI6`,
  emits **no warnings**, verifies FK5/equinox 2000 and agrees exactly at all
  25 points. These cards belong only to the independent synthetic reference,
  not a newly accepted production-header variant.
- An explicit projection warning stops classification with no completed
  membership rows and an unknown-completion projection flag. No warning is
  waived in the production builder or projection path.

The initial direct-table test used global image-frame cards and suppressed
their expected WCSLIB table warnings. The author adopted the reviewer's
warning-free table-native reference and now asserts zero warnings plus explicit
frame/equinox. At that intermediate checkpoint, all 12 tests and Ruff passed;
the subsequent metadata-prefix regression brings the final suite to 13. This
test-only repair does not change the production allowlist, coordinate recipe
or scientific scope.

## Nulls, membership and progress

Input coordinates must be aligned signed-integer arrays within int32 range;
the supplied validity array must be Boolean. Masked-array inputs are rejected.
Both explicit null sentinels are applied in addition to the supplied mask,
before building the projected coordinate buffer. All-masked and empty chunks
return correctly shaped local masks and zero attempted projection rows.

Invalid rows have false membership entries **and a false validity mask**;
downstream code must not collapse them into valid outside-aperture events.
Unexpected nonfinite, malformed or out-of-domain returned sky coordinates
cause STOP rather than silent row loss. Membership uses spherical separation,
with literal inclusive comparisons at 20, 60 and 90 arcseconds. These are
computed-float comparisons, not an epsilon-adjusted assertion of exact
mathematical tangency. A row cannot enter its own circle and annulus together,
but may legitimately belong to regions around different centres.

All output arrays are local, read-only working masks; the input arrays are not
modified. The fresh scalar accounting dictionary survives caught exceptions
without coordinate values or arbitrary exception strings. The author clarified
that `projection_completed_rows` counts a **returned projection call before
output validation**, not certified valid sky rows. A returned nonfinite output
can therefore have a completed-call count but zero `rows_completed` and FAILED
status. An exception during the call marks its completion unknown. This is
not durable accounting through a killed process; the future runtime owns that.

## Conditions left to the eventual runtime

This module performs no I/O and intentionally does not duplicate full EVENTS
row-schema validation. The caller must bind the exact product/header, full
decoder schema, camera, null declarations, frame convention and unchanged
five-centre construction. Numerically valid replacement reference values
cannot be identified as the wrong observation by this pure function alone.

The runtime must pass correct X/Y validity masks, preserve all input/invalid
denominators, enforce its byte/chunk/deadline/receipt limits, and keep reference
values, transformed sky arrays and local masks out of public coordinate caches.
Independent energy, FLAG/PATTERN, CCD/window, GTI and time-selection decisions
are not made here. A successful transform is neither live detector area nor
proof of source association, source-exclusion support, stable background,
complete wings, equal camera sensitivity, a count rate or a significance.
Photon occupancy and coordinate bounds must not substitute for exposure.

## Final anchors

| Artifact | SHA-256 |
| --- | --- |
| Geometry source | `8adcb227f61c2f86855652ada4d66b5f677e84caa0cb16b5dd182be3081de9da` |
| Final reviewed 13-test suite | `e1e1d41daffec25ada03fd155f958082c62f09c62cef4cdd83ee2cd8fa14f538` |

The above bytes were independently hashed after the metadata-prefix repair.
For failure history, the initial synthetic source checkpoint was
`583634be4806b9070d50d6500b3bbc1cba7f260c78984605510e1b464288a3b5`;
its initial test checkpoint was
`5195d827497501301d447480981bf586eec5966a98c84279b5d102faf3233a94`,
then `05bd0a8a209a65960290b30d6f8cbfb72651f03a2751d2e9590bd3534923a3e1`
after the warning-free oracle change. These checkpoints preceded the parent's
actual-header compatibility finding and were not a frozen photon run.
No remaining scoped blocker was found. A subsequent runtime or protocol needs
its own review and exact binding; this report does not authorize reading photons.
