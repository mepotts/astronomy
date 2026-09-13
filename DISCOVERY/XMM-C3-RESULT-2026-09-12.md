# XMM C3 stopped at the MOS2 map HEAD; no products downloaded

**STOP_HTTP_IDENTITY_OR_STATUS: HTTP 404 on the third HEAD.** The
[reviewed contract](XMM-C3-2026-09-12.md), implementation and tests were frozen
in commit `060a1f7` before the single run. The eight-slot gate behaved as
specified: two successful size checks, one failed size check, five unattempted
slots. No retry, substitution, redirect or product-body read.

| Slot | Request | Observed outcome |
| ---: | --- | --- |
| 1 | pn S003 EXPMAP8 HEAD | HTTP 200, 503855 advertised compressed bytes |
| 2 | MOS1 S001 EXPMAP8 HEAD | HTTP 200, 275217 advertised compressed bytes |
| 3 | MOS2 S002 EXPMAP8 HEAD | HTTP 404; error body not consumed |
| 4 | Observation ATTTSR HEAD | Not attempted |
| 5–8 | Four conditional GETs | Not attempted |

The retained MOS2 response has the exact requested URL, HTTP 404 and date
2026-09-13 00:38:53 GMT. Its 19-byte Content-Length describes an unread error
entity, not the size of an exposure map. The requested filename/URL occurs
exactly once in the earlier retained inventory, where its size is displayed
as 401K. Direct comparison found no request construction mismatch. An older
listing entry does not overrule the actual response or establish the cause
of the discrepancy. Permanent absence, transient serving behavior and archive
changes remain unproved; do not label this a scientific data-quality failure.

Parent assessment completed and an explicit offline replay returned
`PASS_OFFLINE_REPLAY STOP`. This verifies the failure record, not acquisition
success. Worker exit was 1; peak working set 50540544 bytes, parent 48324608,
under the monitored 500000000-byte limit. Compressed/expanded product bytes
are both zero. Final aggregate JSON is 11032 bytes, below 10 MiB. All eight
slots remain accounted for. [Independent audit](XMM-C3-POSTRUN-REVIEW.md).

## Consequence for the discovery work

Preserve this C3 run unchanged. The original
[counts draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md) already requires pn
and at least one eligible MOS, not all three cameras. A separate photon-blind
continuation can therefore use the successful pn/MOS1 size receipts and check
the still-unattempted attitude product, retaining MOS2 as unavailable for this
geometry path. This is not permission to retry the failed slot or claim the
map permanently missing. Keep all originally planned camera/region/time tests
in the multiplicity denominator, including unavailable cells, and retain the
minimum of two usable negative apertures. No aperture or detection threshold
changes; no inference from photons or favorable geometry.

The [attitude semantics](XMM-ATTITUDE-SEMANTICS-2026-09-12.md),
[conservative frame-boundary proposal](XMM-FRAME-BOUNDARIES-2026-09-12.md)
and [prospective screening choice](XMM-SCREENING-DECISION-2026-09-12.md)
advance the later control design. None supplies measured aperture coverage
or executed burst recovery. The discovery goal remains active.

## Frozen identity

| Artifact | SHA-256 |
| --- | --- |
| Source | `7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60` |
| Tests | `d322831429e4c613f2d759fe75818c68b9fba1c24abaf08108a37584b646ab1c` |
| Protocol snapshot | `ef076fe58242199da9dac4f1b413c90e8af2263367f0e8cfa6cc672e9903ed63` |
| Run start | `b6bac1fd675d2d1887f60b76e340129f55ef83a897e9dc55f78fbab77b0d53ee` |
| Worker result | `b695ac5717a535effbde20345063d7ad39382c8535397b23ac9dc5e39795a79f` |
| Outcome | `62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e` |
