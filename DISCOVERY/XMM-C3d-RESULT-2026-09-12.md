# C3d retained the attitude product; scientific coverage remains unvalidated

**ATT_PRODUCT_RETAINED_HEADERS_ONLY.** The [contract](XMM-C3d-2026-09-12.md),
implementation, 15 tests and [independent review](XMM-C3d-REVIEW.md) were frozen
in commit `a6c7911` before the sole GET. ESA returned HTTP 200 at
2026-09-13 01:30:25 GMT, the exact expected safe filename and `image/fits`,
again without Content-Length or entity validators. This separate capped
transfer does not change [C3c's missing-length STOP](XMM-C3c-RESULT-2026-09-12.md).

The actual body is gzip-wrapped FITS: **151713 compressed bytes**, **4173120
expanded bytes**, with worker CRC/EOF verification. Parent header/hash replay
passes independently; replay does not decompress the gzip again. No package
extraction, redirect, retry, other product or scientific array interpretation.
Worker exit 0, parent assessment completed, one OK slot. Recorded worker/parent
peaks are 62509056/59228160 bytes. Final JSON, including local full headers, is
21476 bytes. Raw/expanded products and coordinate-bearing headers remain ignored.
[Independent postrun audit](XMM-C3d-POSTRUN-REVIEW.md).

## Actual header adjudication

The safe header derivative confirms XMM observation `0884250101`, POINTING,
dates 2021-05-27T18:47:53 through 2021-05-28T09:14:07, and creator
`atthkgen-1.22.1`, SAS 21.0.0 (`xmmsas_20241108_1150`). There are two HDUs:
PRIMARY plus ATTHK. The structural reader read 14400 header bytes and zero
declared data-region bytes. This is layout inspection, not full FITS checksum
or calibration validation.

ATTHK declares **51975 rows, 80 bytes per row**, and ten scalar D columns:
TIME (sec), AHFRA/AHFDEC/AHFPA, OMRA/OMDEC/OMPA, DAHFPNT/DOMPNT/DAHFOM
(all nine in degrees). This matches the documented task schema in the
[format note](XMM-PPS-ATTITUDE-FORMAT-2026-09-12.md), allowing explicit
column selection for a later bounded metadata-value pass.

Two issues prevent treating the header as a quality/coverage pass:

- Neither HDU supplies TIMESYS, TIMEZERO, MJDREF or TIMEREF. A TIME unit of
  seconds is not itself an epoch/time-scale declaration. Establish the task's
  convention and inspect actual TIME support before comparing it with C1/C2.
- NATT, NGAHF and NGOM each equal 51975, while NGAHFOM is 0. Their comments
  name total, good AHF, good OM and good AHF+OM entries. These summaries do not
  independently establish component validity or a shared good interval. Inspect
  actual NULL/component patterns; do not silently infer complete joint quality.

No absolute pointing or WCS values are published here.
The [time-reference follow-up](XMM-ATTITUDE-TIME-REFERENCE-2026-09-12.md)
identifies TT/MJD 50814 as the documented mission convention to test, not a
recovered file keyword. It also explains why the quality counters cannot all
be literal good-set/intersection counts on the same row universe. Their cause
remains unresolved; neither all-good nor no-joint-good rows may be inferred.

## Next execution priority

The attitude acquisition obstacle is cleared. Next, freeze a small local
attitude TIME/quality/sample-movement inspection and acquire the already-sized
pn/MOS1 exposure maps under a new two-product contract using retained prior
HEAD receipts. Neither map was downloaded by C3/C3b. Preserve the missing MOS2
camera and original multiplicity/negative-control requirements.

The synthetic frame-bound/tail helpers are available but have not been applied
to real frames. Product identity and schema alone do not prove continuous
pointing, spatial acceptance, valid live exposures or recovered bursts. The
known-control counts test and unknown-source search remain unexecuted; no
discovery or scientific submission is claimed.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| Source | `87caca0e856065d33ff4f60404399915eed8a4b50a9afa7d0106f98fb691f825` |
| Tests | `8d313d56946a5f68fb30af8b39c41910121a079d646ccff9e074dcbfc809cf56` |
| Protocol snapshot | `8bee82d6c849bd94479f40615817cc2d14776d439b80b62a8b47c84871beed6a` |
| Raw FTZ | `963a0188c833a74fbe2d86f3288e9f1b6e70e038135dc05e57daa8d4256d7ccc` |
| Expanded FITS | `ff251ab4e22655bc02b612a599160e40cfe3176cf8de90ce4514668e5bcf7a17` |
| Full header report (local) | `a5c5d3a9113b88b63e560be09dc72df0ece14b35c8e91fdefcbc73c77a8d8409` |
| Outcome | `2a1a7340c89292882f2b205ff48f4babbada46ed4dde210b45ec1bdd4a6bed0d` |
