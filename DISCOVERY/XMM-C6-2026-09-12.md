# C6: one documented ESA MOS2 exposure-map acquisition

Prospective contract, September 12, 2026. Freeze source, tests and this protocol
after independent review, before any request. Preserve original C3 MOS2 HEAD404
STOP and C5's zero sampled MOS1 source support. No recovery or discovery claim.

## Exact operation and provenance

One anonymous GET, no preceding HEAD, redirects, retries or fallback:

```text
https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&instname=M2&expflag=S&expno=002&name=EXPMAP&datasubsetno=8&sourceno=000&extension=FTZ
```

The [primary-source selector note](XMM-MOS2-ALTERNATE-2026-09-12.md), bound as
SHA256 `a816fd84aece2eb4acd4c4cf0dd630416a9563a26af46a4deee24ce33a393760`,
establishes these filename fields. It does not establish current availability.
Require returned safe basename `P0884250101M2S002EXPMAP8000.FTZ` before body reads.
Bind original C3 outcome `62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e`,
MOS2 HTTP/result receipts and original index/inventory identity. Original C3
replay is receipt-only, with zero products. C5 outcome is hash-bound only:
`58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36`.
Do not numerically replay C5 or run any old network worker.

## Transport and resource limits

Reuse frozen C3d transport/format/receipt helpers in a fresh module instance,
rebinding only current paths, exact slot, limits and product identity validation.
Own C6 worker, parent, binding and replay; never invoke C3d ATT prior/run/worker.
Fresh session, trust_env false, no credentials or cookie reuse, no Range;
5/15-second socket timeouts, identity Accept-Encoding. Require HTTP200/exact URL,
absent or identity Content-Encoding, strict safe disposition, and media type
image/fits, application/fits, application/x-fits, application/octet-stream,
application/gzip or application/x-gzip. Persist allowlisted metadata only, not
cookies, raw disposition or arbitrary exception text. Header parser cap65536.

Content-Length optional; if present, unambiguous positive decimal <=2097152
and exact retained-byte equality. Stream at most this 2MiB cap plus one overflow
detection byte; do not retain overflow. No invented ETag/Last-Modified.
Accept only gzip signature or standard SIMPLE primary FITS prefix. Gzip requires
CRC-checked EOF under33554432 expanded bytes; raw FITS requires identical copy.
One overflow detection byte allowed for expansion. Preserve all partials and STOPs.
No tar/zip extraction or alternative product/package contract is authorized here.
Failure storage ledgers measure retained bytes, not exact received/decompressed
bytes: an overflow byte can be inspected without retention, and interruption
before a receipt can leave work unknown. Never relabel unknown work as zero.

One exclusive attempt, 60-second process-tree worker via pinned helper and its
separate cleanup allowance. Monitored worker/parent peak <=500000000 bytes, not
OS enforcement. Chunk1048576; require67108864 free bytes before request.
Aggregate JSON cap1048576 including full local headers and terminal receipts,
65536 terminal reserve; nominal per-header2097152 subordinate to aggregate cap.
Raw/expanded/full-header artifacts ignored before request; public receipts only
safe metadata, structural identity, hashes and sizes. No coordinates or WCS output.

## Header identity and parent checks

Use pinned structural reader, seeking over arrays. Require exactly one primary
HDU, no parser warnings or ambiguous non-commentary cards, SIMPLE true,
BITPIX -32, NAXIS2-dimensional, OBS_ID0884250101, INSTRUME EMOS2, EXPIDSTR S002.
Both dimensions positive integers; declared payload equals rows*columns*4 and
fits under expanded cap. **Do not assume648-square geometry from other cameras.**
This is storage/entity validation, not approval of scaling, WCS, band, GTI,
exposure normalization or science compatibility. Those must be adjudicated
from retained headers before any separately frozen pixel-value stage.

Bind source/tests/protocol snapshot, dependency source/test/reader/review/helper
hashes, runtime and configuration. Parent independently checks request receipt,
single-slot ledger, actual format, product hashes/sizes, header replay, and exact
one-raw/one-expanded/one-header set. Gzip completion relies on frozen worker CRC
record; header replay is not a second decompression. Require worker0, positive
in-cap measured peaks and all closure checks for MOS2_MAP_RETAINED_HEADERS_ONLY.
Timeout/nonzero/conflicting or truncated receipts cannot pass. Catastrophic
failures permit labelled artifact-only replay, not product validity claims.

No map/attitude/source-list/photon arrays interpreted. Opaque transport, expansion,
hashing and header reads are real I/O even though scientific decode count is zero.
Retain pn/MOS1 results, all fixed controls and test denominator. Success permits
only header compatibility adjudication next; the pn-plus-MOS recovery gate and
exposure/confusion/detector validation remain unmet.
