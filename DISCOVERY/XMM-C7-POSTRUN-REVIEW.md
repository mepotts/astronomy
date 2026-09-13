# Independent C7 post-run receipt and aggregate review

September 12, 2026. **PASS for the recorded static-support diagnostic, not
exposure, burst recovery or discovery.** Reviewed saved receipts and all ten
region summaries following the parent-reported pre-execution freeze `6c7d456`.
This audit made no network requests, read no FITS product contents or actual
map arrays, and performed no additional numerical map replay. Frozen evidence
was not modified.

## Integrity, scope and accounting

Independently verified 22 artifact/dependency hash entries: six in the outcome,
five in the worker result and eleven in the run-start dependency map. Five
additional checks verified the supplied outcome anchor, current C7 source,
tests, protocol and C6 outcome against their saved bindings. The outcome's
artifact inventory exactly closes over the stage JSON files other than itself
plus the protocol snapshot. The worker-start binding matches run-start.

The source, tests and protocol still match the final
[preflight review](XMM-C7-REVIEW.md). The manifest contains only EMOS2/S002,
one persisted map ledger, and all five fixed labels with both region types.
There is no map-2 artifact or additional camera in the recorded denominator.
The C5 outcome remains a bound, unchanged dependency, not a C7 numerical input.
No product-content hash was independently recomputed in this receipt-only
audit; product validation remains the recorded execution/replay evidence.

Worker exit code is zero, assessment is completed, and the validation state
is `COMPLETED_ELIGIBLE_RECEIPTS` with one completed map. Worker, map ledger,
parent additional validation and validation-state counters each consistently
record **1,679,616 returned bytes and 1,679,616 decoded bytes per pass**. The
parent reports one subsequent numerical replay in addition to the worker and
parent validation: **three known passes, 5,038,848 bytes** returned and decoded
in total. This audit did not add a fourth pass. Input hashing and header I/O
are distinct from those payload counters.

The final JSON inventory is 42,284 bytes; excluding outcome it is 40,350,
and excluding both outcome and worker result it is 39,427. These reproduce
the recorded accounting stages. Worker and parent peak-memory receipts are
79,699,968 and 80,154,624 bytes, below the 500,000,000-byte cap. No new product
copy or network acquisition belongs to this stage.

## All ten regions, both fixed resolutions

The following are spherical-area **sign-fraction estimates**, not fractions
of live exposure. Values are rounded here; saved JSON retains full precision.
Negative, nonfinite and out-of-image counts and areas are zero in every one
of the twenty region-resolution records. Thus the remainder of each positive
fraction is the zero-valued category.

| Fixed region | Positive fraction, 4 | Positive fraction, 8 | Zero fraction, 8 |
| --- | ---: | ---: | ---: |
| Published circle | 1.00000000 | 1.00000000 | 0.00000000 |
| Published annulus | 0.65107844 | 0.65106407 | 0.34893593 |
| North circle | 1.00000000 | 1.00000000 | 0.00000000 |
| North annulus | 1.00000000 | 1.00000000 | 0.00000000 |
| East circle | 0.65577678 | 0.65533680 | 0.34466320 |
| East annulus | 0.68860519 | 0.68850629 | 0.31149371 |
| South circle | 0.00000000 | 0.00000000 | 1.00000000 |
| South annulus | 0.12666276 | 0.12654722 | 0.87345278 |
| West circle | 1.00000000 | 1.00000000 | 0.00000000 |
| West annulus | 1.00000000 | 1.00000000 | 0.00000000 |

Independently checked exact region order/completeness, fixed subdivisions
4 and 8, nominal subdivision 8, all twenty resolution records and their
100 categories. Areas sum to reported totals, fractions reproduce area/total
and sum to one, and subpixel counts respect the corresponding sampled base
pixel counts. Recorded fine-minus-coarse and fine-minus-analytical areas also
agree arithmetically. These checks use saved aggregates, not reconstructed
pixel membership.

The largest positive-fraction change between resolutions is
0.0004399810394569714 (east circle), or 0.0439981 percentage points. The
largest nominal total-area deviation from the analytical spherical area is
0.0878326% (east circle). Neither comparison calibrates quadrature error or
proves absence of smaller unsupported features.

## Scientific interpretation and retained limits

The published circle contains 1,259 positive selected subpixels at subdivision
4 and 5,029 at subdivision 8, with no sampled remainder. Together with the
previous pn circle, this supplies positive static source-region sampling in
pn and one MOS camera. It resolves that particular missing static diagnostic;
it does **not** establish simultaneous, continuous or per-bin live exposure.
The primary-CDELT TAN/FK5 construction and explicit ICRS-convention conversion
remain as reviewed, not a new astrometric calibration.

The nominal published annulus is **34.893593451129007% zero-valued**. Using its
full geometric area or accumulated-map amplitude as a calibrated temporal
background scale would not follow from this result. The nearest unsupported
pixel centre is 35.139370540543176 arcseconds from the source; subtracting the
20-arcsecond radius is not a guaranteed distance to a finite pixel boundary.
For an annulus, a centre-distance minimum can also concern its central hole,
so it cannot replace the annulus's direct sign-category estimates.

North and west circle/annulus pairs have wholly positive MOS2 sampling, but
this is not evidence they are source-free or temporally stable negative
controls. The east regions remain partly zero and the south circle wholly
zero. Preserve all fixed controls without replacements or denominator cuts.
Previous MOS1 zeros and pn partial-zero regions, including the fine-grid pn
west-circle zero sample, remain relevant; no automatic two-negative or
multi-camera recovery pass follows.

Read the complete [parent result](XMM-C7-RESULT-2026-09-12.md); its numerical
table, accounting and stated limits agree with this audit. No blocking
receipt or aggregate inconsistency was found. A separately scoped descriptive
photon step need not be called calibrated recovery: source association,
matched masks, regional temporal exposure and detector/background explanations
remain separate scientific requirements. This audit neither executes nor
authorizes that next stage.

## Outcome anchors

| Artifact | SHA-256 |
| --- | --- |
| Outcome | `3916067cc6a32722ed35d13d6c0bef2a391134890c87d936d01685a1c2d2b621` |
| Map aggregate result | `a2a7e0a7c0f9cd7c142bcf61ad6409deea6ed100eb81a6129ccf653b813735b4` |
| Run-start binding | `046754310a37f11d3d58cb53922bc86dc0c3f13a72b13b2d1f5a0e5f9d71f266` |

No absolute sky coordinates, pointing/WCS cards or product array values are
reproduced in this review.
