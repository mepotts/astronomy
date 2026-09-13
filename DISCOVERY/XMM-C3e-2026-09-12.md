# C3e: two map GETs from preserved successful C3 HEADs

Prospective September 12, 2026 contract; freeze source/tests/review before
requests. C3 remains STOP at MOS2 HEAD404; its two earlier successful HEADs
authorize only these separate pn/MOS1 GET attempts. No HEAD refresh, MOS2
retry, attitude request, alternate source or filename fallback.

In this order, exactly one anonymous GET each, stopping on the first failure:

1. `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/P0884250101PNS003EXPMAP8000.FTZ`
   — 503855 compressed bytes.
2. `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/P0884250101M1S001EXPMAP8000.FTZ`
   — 275217 compressed bytes.

Bind the exact indexed names/URLs and original C3 source
`7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60`, outcome
`62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e`, and
the original complete eight-slot STOP ledger with zero acquired product bytes.
Replay prior C3 offline in an isolated module; import the exact two successful
HEAD HTTP records/receipts and their hashes, never the 404 length. Both imported
ETag and Last-Modified must be present and nonempty. On each GET require HTTP200,
exact URL, positive identical-decimal Content-Length equal to its fixed size,
identity/absent Content-Encoding, and exact original ETag/Last-Modified matches
before reading any body. These validators are provenance checks, not proof of
physical calibration. Missing/changed fields STOP; do not refresh them.

Fresh requests session per GET: trust_env false, auth None, cookies cleared,
Accept-Encoding identity, stream true, no redirect/retry/Range; socket timeouts
5/15 seconds. Reuse pinned C1 transport: 1MiB chunks, at most one overflow byte
beyond each advertised size, never retain overflow; preserve short/partial
files. Total compressed cap779072 bytes. Gzip CRC/EOF-complete expansion only;
no raw-FITS/package fallback. Expanded cap33554432 per file,67108864 aggregate
including retained partials. Header-only pinned structural reader seeks over
array regions; no map pixels, attitude or photons decoded.

One exclusive batch through the audited process-tree helper:60-second hard
worker deadline plus separate cleanup allowance, checked remaining time before
each request;500000000-byte monitored worker/parent peak (not OS enforcement).
Require134217728 free bytes before each request. Existing C1 JSON rules:
10485760-byte aggregate,2097152-byte per-header cap,262144-byte terminal reserve.
Pin actual configured paths/caps/runtime, source/tests/protocol snapshot,
C3/C1 sources/tests, HTTP rules, structural reader and both test files, deadline
helper and inventory/index. Never invoke old workers, runs or current old plans.
Original prior replay alone retains its original plan for offline validation.

Worker receipts and parent verification close both request slots, exact methods,
URLs, sizes/validators, raw/expanded/header hashes, gzip-completion receipt and
header replay. Success requires exactly two raw, two expanded, two header files,
all resource accounting and both slots OK. Parent does not decompress again;
CRC completion is bound to the frozen worker receipt. Nonzero exit/timeout
cannot pass. Preserve all failure/NOT_ATTEMPTED slots and partials; malformed
markers support only explicitly labelled failure-artifact replay. Final parent
memory-limit STOP cannot be promoted by replay.

Products and full headers are local/ignored before execution. Public receipts
contain allowlisted safe HTTP metadata, sizes/hashes and structural status;
never cookies, raw exception strings, full FITS cards, coordinates or contacts.

Strongest label `PN_MOS1_GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY` means acquisition
and structural feasibility only, not valid exposure units, geometry agreement,
time-dependent aperture coverage, burst recovery or discovery. Prior STOPs
remain immutable. Later header adjudication precedes any map-array contract.
No publication, submission or private-coordinate disclosure.
