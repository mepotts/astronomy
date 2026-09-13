# C3d: one capped XSA ATTTSR GET after a preserved missing-length STOP

Prospective September 12, 2026 contract. Freeze code/tests/review before the
single GET. C3c correctly stopped: HTTP200/image-fits and the expected inline
basename, but no Content-Length. This amendment permits bounded streaming
without an advertised size; it does not turn that prior HEAD into a pass.

Bind/replay C3c source `542fce5755d9ff668d4ccd6e199b23780504368603352243d7e6fb7cfa727f90`
and outcome `e1d74b048dd68dce51e52bf964d841ac195ca581011fae881f447cdc129c45e3`.
Require the preserved single FAILED slot, worker1, STOP_SIZE_METADATA, zero
body bytes, exact expected safe disposition, and absent length. Imported
safe HTTP metadata and its hash remain bound. No HEAD retry or other product.

```text
GET https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&name=ATTTSR&expflag=X&expno=000&datasubsetno=0&sourceno=000&extension=FTZ
```

Fresh anonymous session, trust_env false, no credentials/cookie reuse,
redirect/retry/Range, 5/15-second socket timeouts. Require exact URL and HTTP200,
identity/absent HTTP content encoding, and the same safe parsed basename
`P0884250101OBX000ATTTSR0000.FTZ`. Reuse the reviewed strict Content-Disposition
parser; never persist its raw value, cookies or arbitrary exception text.
Allowed media: image/fits, application/fits, application/x-fits,
application/octet-stream, application/gzip, application/x-gzip. No package.
Use the existing safe-header allowlist and 65536-byte/header-parser bounds.

Content-Length is optional. If present, require an unambiguous positive decimal
<=2097152 and exact equality with bytes actually retained. Otherwise stream
until EOF under that same cap. Read at most one additional overflow-detection
byte, retain none beyond the applicable cap, preserve partials and STOP without
retry. No HEAD ETag/Last-Modified values exist: do not invent entity validators.

Identify only these raw signatures: gzip `1f8b08`, or the exact standard FITS
primary-card prefix `SIMPLE  =                    T`. Record actual format.
Gzip requires chunked CRC/EOF-complete expansion. Raw FITS is copied byte-for-byte
with matching hash. Expanded limit33554432 bytes, including any retained partial;
one overflow read byte is allowed. No TAR/ZIP extraction, signature guess or
alternative filename is authorized. After expansion use the pinned header-only
reader, seeking over declared arrays. No attitude/map/photon values interpreted.

One exclusive attempt; 60-second worker through the existing hash-pinned
process-tree helper, separate cleanup allowance; 500000000-byte monitored
worker/parent peak, not OS enforcement. Chunk size1048576. Require67108864 free
bytes before request. JSON<=1048576 total including local full headers, with65536
terminal reserve. Per-header nominal ceiling2097152 is subordinate to the
stricter aggregate budget. Raw, expanded and full-header files are locally
ignored before execution; public records contain safe metadata, hashes/sizes
and format/structural status only.

Use independent module instances for unchanged prior replay and configured
current C1 hash/memory/save/expansion/header helpers. Bind source/tests/protocol,
prior outcome/safe HTTP evidence, C3c/C1 sources/tests, HTTP rules, structural
reader/tests, helper, runtime and actual configuration. Never invoke old
network workers or plans. Parent checks request/receipt/order/byte closure,
actual magic, raw/expanded hashes, raw-FITS copy equality where applicable,
header replay and exact one raw/one expanded/one header file set. CRC completion
is the frozen worker's recorded gzip check, not a second decompression during
header replay. Nonzero/timeout cannot pass; preserve partial/truncated artifacts
and a single-slot failure ledger. Catastrophic failures support only explicitly
labelled failure-artifact replay.

Strongest label `ATT_PRODUCT_RETAINED_HEADERS_ONLY`: not a C3c pass, attitude
quality, compatible time/coordinates, stable aperture geometry, burst recovery
or discovery. Subsequent metadata adjudication precedes any new value-reading
contract. No publication, submission or private-coordinate disclosure.
