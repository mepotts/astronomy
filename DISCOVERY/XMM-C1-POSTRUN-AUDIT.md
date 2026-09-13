# XMM C1 independent post-run audit

2026-09-12: **PASS for CONTROL_BUNDLE_RETAINED_HEADERS_ONLY.** Both worker and
parent report that exact limited status; worker return code is 0 and all four
fixed slots are OK. This audit made no network request, performed no event or
other scientific-array interpretation, exposed no full header cards or
coordinates, and changed no C1 artifact.

## Independent verification

All 32 artifact hashes in the parent outcome match the retained files. The
frozen source's read-only replay returned
`PASS_OFFLINE_REPLAY CONTROL_BUNDLE_RETAINED_HEADERS_ONLY`, including dependency
bindings, original HEAD evidence, slot order, HTTP identities, product hashes,
header-only report reproduction and resource closure. All 33 files present in
the C1 stage at audit start remained byte-identical afterward, with no added
stage files.

Exactly four request markers occur in the fixed order, at approximately 0.047,
20.688, 22.438 and 24.438 seconds after worker start. Every retained HTTP receipt
has GET, the exact fixed URL, status 200 and Content-Length equal to its HEAD
value. Any HEAD-provided ETag/Last-Modified values match. No extra request marker
or failed/unaccounted slot was found.

| Slot | Compressed bytes | Expanded bytes | Header JSON bytes |
| --- | ---: | ---: | ---: |
| PN S003 | 109245605 | 219988800 | 1679959 |
| M1 S001 | 7643540 | 11707200 | 175147 |
| M2 S002 | 9972723 | 15194880 | 227208 |
| EP source list | 120581 | 250560 | 88191 |
| Product totals | 126982449 | 247141440 | 2170505 |

Each expanded file is below 1 GiB, their sum is below 2 GiB, and every header
report is below 2 MiB. Actual final JSON storage is 2191924 bytes, below 10 MiB.
The worker's pre-terminal snapshot of 2181659 JSON bytes and parent's
pre-outcome snapshot of 2186408 bytes independently reconcile with the later
receipt sizes; their different totals are expected, not missing output.

Recorded worker peak working set is 68190208 bytes and parent peak is 61431808
bytes, both below the 1000000000-byte acceptance ceiling. These are retained
measurements from execution, not retrospectively measured peaks. The four
receipts record completed gzip/CRC verification; this audit rehashed compressed
and expanded files and replayed their header reports, but did not rerun gzip
decompression or claim an independent compressed-to-expanded transformation.

The parent outcome SHA-256 is
`c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc`.
Individual compressed, expanded and header-report hashes remain in that compact
receipt rather than being duplicated here.

## Privacy and scientific boundary

Full products and header-card reports remain in the stage's `products/` and
`headers/` directories. The local ignore file declares both directories. An
additional Git ignore/index check was blocked by the sandbox user's differing
repository ownership; no safety exception or Git configuration was changed.
Owner-context integration must confirm those local-only files remain untracked.

The frozen C0d summary STOP remains unchanged; its four successful HEAD facts
were used without reclassifying that earlier stage. C1 establishes retained
known-control files and reproducible header structure, not useful exposure,
valid GTIs, reliable astrometry, background behavior, source recovery, calibrated
significance or a discovery. Scientific counts remain explicitly uncomputed.
Header adjudication and any event selection require their separately defined
offline/scientific scope; this audit grants no publication or submission
authority.
