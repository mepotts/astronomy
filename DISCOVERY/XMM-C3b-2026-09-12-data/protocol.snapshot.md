# XMM C3b: retain the eligible pn/MOS1 geometry path

Prospective parent amendment after the preserved C3 MOS2-HEAD 404. Freeze code,
tests and independent review before execution. The original counts design
requires pn plus at least one eligible MOS; this does not lower that criterion.
No photons or geometry results informed this availability-only choice. MOS2
remains unavailable on this path, not a clean negative or a removed planned
test. All fixed regions, at least two usable negatives, simultaneous coverage,
thresholds and original camera/region/time multiplicity accounting remain.

## Prior evidence and four new requests

Bind and replay the unchanged C3 STOP using source SHA-256
`7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60`
and outcome SHA-256
`62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e`.
Verify artifact/dependency closure and the exact prior ledger: slots 1/2 OK,
slot 3 FAILED with HTTP 404, slots 4–8 NOT_ATTEMPTED, no downloaded products.
Reuse only successful prior HEADs for pn (503855 bytes) and MOS1 (275217 bytes),
including their original safe headers/validators. Never convert the prior
404's 19-byte error Content-Length into a product length.

Require exact name/URL pairs in the same frozen inventory/index as C3. The
base is `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/`.
No refresh of successful prior HEADs, retry of MOS2, alternate band or new field.

| New slot | Method | Filename |
| ---: | --- | --- |
| 1 | HEAD | `P0884250101OBX000ATTTSR0000.FTZ` |
| 2 | Conditional GET | `P0884250101PNS003EXPMAP8000.FTZ` |
| 3 | Conditional GET | `P0884250101M1S001EXPMAP8000.FTZ` |
| 4 | Conditional GET | `P0884250101OBX000ATTTSR0000.FTZ` |

The first HEAD was never attempted in C3. Require exact URL, HTTP 200,
identity/absent encoding and an unambiguous positive size <=2097152 bytes.
Read/store zero HEAD-body bytes, including on failure. Only after prior HEAD
closure and this HEAD pass may any GET run. Each GET must match its applicable
HEAD size and supplied ETag/Last-Modified before body reading; a changed product
stops, without a fresh HEAD or retry. Exactly four new requests maximum.

## Unchanged transport safeguards and reduced total scope

Apply C3's fresh anonymous sessions, trust_env false/no credentials, no
redirect/retry/cookie reuse, safe HTTP allowlist/header bounds, 5/15-s socket
timeouts and exclusive markers. Keep partials and all four slots after STOP.
Compressed retained bytes <=**2876224** total (503855+275217+2097152); each GET
retains at most its accepted length plus no retained overflow byte. A single
extra read byte may detect overflow. Verify exact length and completed gzip
CRC/EOF. Expanded cap **33554432 per file**, **100663296 total** including partials.

One **120-second worker**, the same verified process-tree helper and separate
cleanup allowance. Monitored worker/parent peak acceptance **500000000 bytes**;
not an OS allocation guarantee. Same 1-MiB streaming chunks, 10-MiB aggregate
JSON, 2-MiB per header report, 262144-byte terminal reserve and 268435456-byte
free-space check before launch/each request. No installation or larger budget.

Only structural/header inspection with the existing pinned reader: no map,
attitude, source-list or photon arrays. Preserve the reader's documented
malformed-header/checksum/conformance limits. Full headers and all raw/expanded
products must be locally ignored before execution. Public outputs omit
coordinates, full cards, arbitrary warnings/exception text and contact fields.

## Implementation and verification

Use narrow verified C3/C1 helper reuse where useful; explicitly bind in-memory
output/budget configuration. Do not invoke old network workers/plans or modify
prior files. Prior C3 replay is offline and may use a separate verified module
instance so its original configuration stays isolated from C3b. Bind C3 and C1
source/tests, C0d HTTP rules, structural reader/tests, helper, current source/tests,
protocol snapshot, inventory/index, prior outcome and runtime dependencies.
Bind imported HEAD records exactly, rather than trust copied size literals alone.

Parent verification must reproduce prior evidence, phase/order gate, HEAD/GET
identity and entity validators, raw/expanded hashes/sizes, header reports,
exact three raw/three expanded/three header path sets, byte/resource and artifact
closure. Nonzero/timeout cannot pass. Offline replay must verify the accepted
result; damaged-receipt fallback is explicitly failure-artifact-only and keeps
all four slots, not silent success/resumption. One exclusive C3b attempt.

Synthetic tests must cover complete one-HEAD/three-GET worker-parent-replay,
the two bound prior successful HEADs, prior evidence mutation/404 misuse,
ATT HEAD failure preventing every GET, changed prior product validators stopping
before body read, reduced config/byte limits, exact product set and nonzero/
truncated-marker failure accounting. Reused frozen helper tests remain relevant;
new phase/provenance integration still requires independent review.

Strongest label: **PN_MOS1_GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY**.
It is not a C3 pass, complete three-camera coverage, stable aperture acceptance,
burst recovery, unknown-source scan or discovery. After acquisition, adjudicate
actual identities, bands, units, WCS/time/mask provenance before a separately
specified geometry-value experiment. Scientific publication, submission and
private-coordinate disclosure remain gated.
