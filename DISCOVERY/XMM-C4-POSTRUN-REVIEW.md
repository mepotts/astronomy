# C4 independent post-run receipt and interpretation review

September 12, 2026. **PASS for the bounded sampled-attitude diagnostic result;
not detector-coverage, clock-validation or burst-recovery acceptance.**

This review read only saved JSON summaries/receipts, source/protocol text and
their hashes. It did not open or hash a FITS product, read another actual
attitude array, invoke numerical replay, or make a network request. The parent
reports execution after freeze commit `19f935c` and one subsequent successful
numerical replay. That replay is distinguished from this independent
receipt/aggregate audit, which does not independently rederive real angles.

## Evidence and closure

Independently verified outcome SHA-256
`67d5cec964c1c36b592202a8faeaa70999b7e53762abced1bf6ecd28f6a0ec55`.
The [outcome](XMM-C4-2026-09-12-data/outcome.json) records worker exit zero,
`assessment_completed=true`, one OK table and
`ATTITUDE_VALUES_SUMMARIZED_UNCALIBRATED`. The
[table receipt](XMM-C4-2026-09-12-data/table-result.json) retains the narrower
summary label `SAMPLED_ATTITUDE_DIAGNOSTICS_NOT_COVERAGE`.

Read-only audit checks passed:

- All six outcome artifact hashes, all five worker artifact hashes and five
  pinned dependency hashes: 16 checks, plus the independently supplied outcome
  hash. The outcome artifact-name set exactly matches the current eligible
  files, not just a matching subset.
- Eight additional source/test/protocol/prior-outcome/C1-header hash checks;
  the worker-start binding hash matches run-start. The table-start marker
  declares table 1 and elapsed 0.094 seconds, within its prospective bound.
- Worker and parent table ledgers agree, as do table/worker read and decoded
  accounting. Receipt resource sizes match the actual files: 9,295 JSON bytes
  before worker/outcome receipts, 10,217 before outcome, 11,460 in total.
  Reported worker/parent monitored peaks are 68,259,840 / 69,058,560 bytes,
  respectively, below the 500,000,000-byte cap.

Final execution bindings match the accepted review:

| Artifact | SHA-256 |
| --- | --- |
| Runtime | `d53d265ebf3ff82832137da2ee7e0fffcf7f1095f143790c655a8fd0f8915e39` |
| Runtime tests | `b37ccf15c5834420c8257b2eb37c4932a8cd14de4bc3449c30a6e8755ffca606` |
| Protocol snapshot | `a4b27125eed686b706126fe502be0147feb18db502cbe3627ef630766a91b4bc` |
| Table result | `144db736240757432cd5496459e907dea23a09be3ae9c2c87ef0da5c95d70e90` |

## Reader scope and pass accounting

The unchanged reviewed decoder selects only the bound ATTHK payload: 51,975
rows, ten scalar big-endian float64 values per row, 80 bytes per row, offset
14,400, and 4,158,000 interpreted bytes per pass. Six bounded requests cover
that span; no complete-FITS array API or EVENTS/map/source-list selection is
used. Provenance hashing is separate byte access, not an additional numerical
decoding claim. In particular, zero compressed/expanded bytes in C4's resource
receipt means no such files stored in this output directory, not zero input
bytes accessed.

There are **three known decoding passes**, not one: worker, independent parent
assessment, and the parent's reported subsequent replay. Each has a separate
4,158,000-byte budget, giving 12,474,000 decoded bytes across those three
passes, from one unique payload. Worker byte accounting is persisted; the
parent-assessment success follows the reviewed recomputation path. The third
pass is reported by the parent, not reconstructed by this receipt-only review.
This review adds no fourth pass. An interrupted run would not justify zero
byte accounting or numerical verification, but this run has a completed table
receipt and successful parent assessment.

## Aggregate findings

All ten columns report 51,975 finite values and zero NaNs/infinities. Both AHF
and OM report 51,975 finite/domain-valid triplets, no partial or domain-failed
triplets, and all 51,974 original adjacent pairs eligible for the fixed
one-second calculation. Reported TIME differences have minimum and maximum
exactly one second, with no nonpositive or non-unit step. Endpoint span is
51,974 seconds, arithmetically consistent with 51,975 samples.

The unchanged time axis brackets each camera's independently bound header
range. Independently recomputed half-open counts from the reported uniform
axis and range endpoints agree with EPN 49,072, EMOS1 50,023 and EMOS2 50,195.
These are sample counts in header intervals, not GTI exposure or camera
simultaneity measurements.

AHF and OM have the same reported aggregate extrema:

| Sampled statistic | Maximum (arcsec) |
| --- | ---: |
| Great-circle distance from first eligible sample | 1.7041471682500233 |
| Consecutive eligible one-second pointing step | 1.2058678464359744 |
| Shortest absolute adjacent PA change | 4.724120624416628 |
| Supplied DAHFPNT / DOMPNT relative-offset column | 1.1063967264563714 |

The supplied DAHFOM column reports zero finite minimum and maximum, with all
rows finite/domain-valid. This records what that product column contains;
equal extrema and summaries do **not** establish elementwise AHF/OM triplet
identity, independent measurement provenance, or the meaning of the header
counter convention. PA change is not a detector-position displacement or a
complete three-dimensional attitude rotation.

The contradiction is preserved: NATT/NGAHF/NGOM each equal 51,975 and match
their measured row/finite counts, while NGAHFOM is zero despite 51,975
measured jointly finite/domain-valid triplets. The receipt explicitly marks
`NGAHFOM_matches_joint_finite=false`. It must not be relabelled all-good or
explained away by equality of the displayed aggregate motion statistics.

## Interpretation and remaining boundary

No blocking inconsistency was found in the receipts or their aggregate
arithmetic. This completes the specified attitude-value diagnostic, not a
science discovery. No absolute pointing or individual angular rows appear in
the reviewed C4 artifacts; the false photon/map-interpretation and
absolute-angle-persistence flags are consistent with the bound code path.

The samples are finite and sane under the predeclared domains. That is not
independent quality certification. Low sampled motion cannot bound motion
between samples, validate aperture coverage near detector boundaries or bad
pixels, or justify silently accepting the counts-recovery geometry.
Missing time-reference keywords remain missing: the TT/MJD50814 convention
was adopted prospectively, not verified by matching ranges. Both
`clock_reference_verified` and `continuous_motion_bound_established` remain
false, as required by the [pre-execution review](XMM-C4-REVIEW.md).

The practical next decision may use these diagnostics alongside separately
validated geometry/exposure evidence. It must not turn this stage into a
continuous-stability pass, calibrated flux measurement, burst detection or
global false-alarm statement. No new acquisition, coordinate query or photon
selection was authorized or performed by this review.
