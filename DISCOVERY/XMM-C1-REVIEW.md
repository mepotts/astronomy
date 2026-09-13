# XMM C1 independent pre-execution review

2026-09-12: **GO for the four fixed known-control acquisitions and header-only
structural inspection under the reviewed protocol.** The complete acquisition
source, protocol, author tests and pinned structural reader/tests were read.
The independent run passed all 15 acquisition tests and all 15 structural tests;
pinned Ruff passed for acquisition source/tests. No live GET, decompression of
astronomical products, array interpretation or earlier-artifact change was made
by this reviewer. No additional test framework was introduced.

## Verified scope and resource safeguards

- Selection binds the original C0d outcome and every artifact it lists, replays
  its preserved STOP and checks the four individually successful HEAD receipts.
  Exact known URLs and advertised lengths remain fixed; C0d is not promoted to
  success. Verified-buffer loading binds the original metadata rules, structural
  reader, both structural test files and process-tree helper.
- Four sequential, single-attempt anonymous GETs use fresh isolated sessions,
  no redirects or retries, raw identity-encoded transfer and safe header lists.
  Method/URL/status, duplicate length agreement, exact expected bytes and any
  HEAD-provided ETag/Last-Modified are checked before body reading. A changed
  validator regression confirms zero body reads. Overflow retains only the
  per-file cap and consumes at most one extra byte.
- Aggregate compressed allowance is 126982449 bytes. Streaming gzip limits each
  expanded file to 1 GiB and all expanded files, including prior partials, to
  2 GiB. EOF is read to establish gzip completion/CRC; a corrupted CRC cannot
  produce success. There is no tar/zip extraction or footer-size inference.
- A single pinned helper bounds the acquisition/decompression/header worker to
  300 seconds, with additional local checkpoints and 5/15-second socket limits.
  Helper cleanup allowance is separate. At least 3 GiB free space is required.
  The 1000000000-byte working-set ceiling is monitored acceptance, not an OS
  allocation limit. Chunked hashes and decompression avoid whole-product loads.
- Exact serialized header JSON is capped at 2 MiB per file and all JSON at
  10 MiB, with terminal-receipt reserve. Exclusive files/markers prevent a resumed
  attempt. Failure stops later slots and preserves partial products and hashes.
- Parent verification rechecks order, HTTP receipts, compressed/expanded hashes
  and sizes, header report identity/replay, measured peak, artifact closure and
  stage-specific resource snapshots. A nonzero worker return code or missing
  required result cannot become a successful bundle.

## Material findings resolved before GO

1. Persistent over-limit memory checkpoints during terminal hashing/serialization
   could suppress the failure receipt. Terminal reporting now avoids rethrowing
   the same high-water limit and samples memory after reporting work, retaining
   the measured peak and STOP. The helper still bounds the worker process tree.
2. Replay originally skipped all recorded resource totals. It now compares the
   worker snapshot excluding the subsequently written worker/outcome receipts,
   and the parent snapshot excluding its subsequent outcome receipt. Actual
   total JSON usage is also checked. A tampered expanded-byte total is rejected.
3. A memory limit first crossed during final parent serialization could leave an
   authentic STOP that replay rejected because the worker had succeeded. The
   narrow regression now preserves worker success, parent STOP_PEAK_MEMORY and
   the above-cap parent peak; a fresh-process-style replay reproduces the STOP.

The single retained-input provenance test is explicitly skipped only when the
local-only C0d summary is absent in public CI. It ran and passed in this review.
The remaining transfer/resource/structure tests are synthetic and do not depend
on downloading scientific products.

## Privacy and scientific limits

Compressed/expanded products and full header-card reports reside in ignored
`products/` and `headers/` directories. Public receipts retain hashes and byte
lengths, not pointing/WCS coordinates or observer contacts. Warning categories
are captured without warning text; exception console text is sanitized. A
synthetic coordinate fixture verifies that full cards stay out of public JSON.

The structural reader seeks over data spans declared by accepted headers; tests
guard reads between multiple HDUs. Its documented malformed-header limitation
remains: bounded scanning can encounter payload bytes before detecting a missing
header terminator. Hashing/gzip verification traverse bytes without interpreting
arrays. No EVENTS, source-list, GTI, exposure, bad-pixel, image or count values
are analyzed. FITS checksum/conformance and payload validity are not established.

`CONTROL_BUNDLE_RETAINED_HEADERS_ONLY` would not mean control recovery, valid
exposure, calibrated significance, unknown-search readiness or discovery. Further
offline header adjudication and a separately frozen counts protocol remain
required. This review authorizes neither scientific publication nor submission.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C1-2026-09-12-data/acquire.py` | `13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5` |
| `XMM-C1-2026-09-12-data/test_acquire.py` | `d751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c` |
| `XMM-C1-2026-09-12.md` | `b8bcf2201d311f4ebb3281d48f569ca846be154cb49359177022be01e97385f3` |
| `xmm_structure.py` | `96d9497dbdd45d2561fc0bbb27a0c11d6fbad91cd42c0b14191378dd9fd7fa63` |
| `test_xmm_structure.py` | `4b1bb863a29543ecb6957a417b3115155fa74b625c300d86524a4c8ac44af1aa` |
| `test_xmm_structure_review.py` | `a062ddea63b2c8364395ed61ead99e2cc12031bcec3065aa24ca61dbee1d6b10` |

The reviewer changed only this review document. No remaining material
pre-execution blocker was identified.
