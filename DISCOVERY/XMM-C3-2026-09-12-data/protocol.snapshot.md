# XMM C3: fixed coverage products, conditional acquisition and headers only

Prospective parent decision, September 12. No execution until implementation,
synthetic tests and independent review are frozen in Git. This adopts the
[four-product geometry proposal](XMM-GEOMETRY-NEXT-2026-09-12.md) without changing
any aperture, control field, prior outcome or scientific threshold.

The metadata and acquisition phases have separate acceptance gates below,
both specified before requests. A second implementation/freeze between them
is unnecessary when all four exact advertised sizes meet these prospective
caps; unknown lengths, changed entities or oversized products stop the run.
No fallback download or larger bundle is authorized.

## Exact source and eight-slot order

Bind the retained C0c2 inventory SHA-256
`6ddb4a357439922dbefaa51e365b53802e6d031d079348706274555f4e063c23`
and index SHA-256
`97f9372b999b354ebcbff51a4b42af885433de598795a6a58656ef1e09bac258`.
Require each exact filename/URL pair once in that inventory. Base URL is
`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/`.

| HEAD slot | Conditional GET slot | Exact filename |
| ---: | ---: | --- |
| 1 | 5 | `P0884250101PNS003EXPMAP8000.FTZ` |
| 2 | 6 | `P0884250101M1S001EXPMAP8000.FTZ` |
| 3 | 7 | `P0884250101M2S002EXPMAP8000.FTZ` |
| 4 | 8 | `P0884250101OBX000ATTTSR0000.FTZ` |

First issue all four HEADs sequentially, reading/storing zero response-body
bytes even on error. Each must return HTTP 200, the exact requested final URL,
absent/identity content encoding, and an unambiguous positive Content-Length.
Each compressed length must be at most **2097152 bytes**, total at most
**8388608 bytes**. Rounded directory sizes are not these measurements.

Only after all four HEADs pass may slots 5–8 GET those same four entities in
order. Each GET must match its HEAD length and any supplied ETag/Last-Modified
before body consumption. No redirect, retry, cookie reuse, directory refresh,
Range request, alternative band, replacement exposure or second attempt.
One fresh anonymous session per request, trust_env false, no credentials or
environment/netrc authentication. Safe HTTP fields only: Content-Type,
Content-Length, Content-Encoding, Date, ETag, Last-Modified. Never retain
Set-Cookie or arbitrary headers. Cap safe header values at 65536 bytes and use
the existing bounded HTTP-header parser settings and 5/15-s socket timeouts.

## Transfer, expansion and structural bounds

GET consumption is capped at its accepted compressed length plus at most one
overflow-detection byte; retain no more than that accepted length, including
partial files on failure. Require exact actual length and completed gzip CRC/EOF.
Expanded FITS: **33554432 bytes per file, 134217728 bytes aggregate**, accounting
for existing partial files. Expansion may read one additional byte only to
detect overflow. Use bounded chunks, not full-file decompression in memory.
Require at least 268435456 free bytes before launching any request.

Reuse the reviewed FITS header/declared-layout inspector, not Astropy array
loading. Seek over all declared image/table data; no exposure-map pixels,
attitude samples, photon arrays, source-list values or WCS-based region tests.
Its bounded malformed-header scan and incomplete FITS-conformance/checksum
validation limitations remain explicit. Retain full headers locally, then
perform a separate non-coordinate metadata adjudication after technical success.
Identity, numerical band, units, masks, time references, GTIs, WCS presence and
attitude-column semantics may remain missing/incompatible; do not infer them
from filenames or turn structural success into geometry approval.

Keep raw/expanded products and full header JSON **locally ignored** before
execution, because they may contain coordinates/contact/history. Public records
may contain filenames, hashes, sizes, HDU counts and safe status/resource fields,
but no arbitrary header/exception text, coordinates or array dumps.

## Execution, reuse and verification

One exclusive attempt in `XMM-C3-2026-09-12-data`, at most eight requests.
One **120-second worker** through the existing process-tree deadline helper
SHA-256 `11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`;
cleanup allowance is separate. Monitored worker/parent peak acceptance
**500000000 bytes**, not an OS allocation guarantee. JSON at most **10 MiB**
aggregate including local headers and terminal receipts; each header report
at most **2 MiB**, with **262144 bytes** reserved for terminal reporting.

Prefer narrow reuse of frozen C1 transport/expansion/header functions, loaded
from verified source bytes SHA-256
`13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5`.
Explicitly bind any in-memory execution configuration (output directory,
budgets, deadline and chunk size). Do not invoke C1's old plan/run or mutate its
source/artifacts. Bind C0d HTTP rules, structural reader and tests, helper,
implementation/tests/protocol snapshot, runtime and relevant dependencies.
Use the existing memory and exclusive-write discipline. No installation.

Record all eight slots, including unattempted slots after the first STOP,
worker return/timeout, retained bytes and source/input/artifact hashes. Partial
or truncated receipts must leave an explicit failure ledger, never a success or
silent restart. A nonzero helper return always prevents technical success.
Parent verifies HEAD gate, order, GET/HEAD consistency, raw/expanded hashes,
header replay, artifact and byte/resource closure; explicit offline replay must
reproduce the accepted result without network. Failure-artifact-only replay,
if needed, must say summaries/products remain unverified.

Synthetic tests must exercise the complete HEAD-to-GET path, no body reads for
HEAD, no GET after missing/oversized/failed HEAD, no body after changed GET
entity, transfer/expansion caps and partial retention, header-only behavior,
provenance/runtime binding round-trip, failure accounting, parent/replay closure,
and nonzero/timeout never becoming success. Existing C1 tests may cover unchanged
reused functions, but C3 configuration and phase integration need their own tests.

Strongest technical label: **GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY**.
It is not aperture coverage, pointing stability, a live-exposure recipe,
published-burst recovery, a new-source search or discovery. Publication,
submission and private-coordinate disclosure remain separately gated.
