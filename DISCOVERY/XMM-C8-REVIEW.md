# Independent C8 pre-execution review

September 12, 2026 label. **Scoped GO for parent freeze and separate execution
authorization**, limited to the fixed selected source-list columns and aggregate
association/contact screen. This review did not execute the real worker,
interpret source-list values, open any retained product, read map/event arrays
or make network requests. No frozen source/test or protocol was edited.

Read the complete C8 source, all current tests and prospective protocol, plus
the reused C1 helper functions relevant to pinned imports, I/O, resource checks,
exclusive receipts and safe terminal memory failure. The geometry and selected
reader have separate [core](XMM-SOURCE-GEOMETRY-CORE-REVIEW.md) and
[reader](XMM-SOURCE-ROWS-REVIEW.md) reviews.

## Resolved preflight findings

Parent/reviewer findings were corrected before any value execution:

- Replay now emits its additional selected-pass accounting on success, an
  assessment failure and a later outcome-comparison failure, without rewriting
  saved evidence. Caught parent partial validation remains in its terminal
  receipt; a completed read followed by geometry failure retains complete read
  counters without falsely claiming completed geometry.
- Extra/nested JSON is rejected before a run and during closure checks. Fixed
  exclusive stage files prevent accidental repeat invocation. The missing C1
  test dependency and the final reviewed reader hashes are now bound.
- Successful summaries explicitly require 151 rows and the unchanged five
  aperture plus five annulus labels. Numerical parent comparison additionally
  compares the complete summary and accounting, not only selected headline fields.
- The reviewer supplied a concrete impossible failure receipt with 755 completed
  reads but zero decoded spans. Since the reader stops at its first failed
  span, completed reads may exceed decoded spans by at most one. The author
  added that invariant and a regression. No scientific threshold changed.

## Independent checks

All **16 C8 synthetic tests** independently pass. Root-invoked Ruff 0.16.5
passes on the final wrapper and tests. Tests cover unbuffered synthetic value
access, truncation, missing rows, identity/frame/schema changes, duplicate cards,
safe errors, success and exact replay, nonzero worker return, caught parent
partial failure, orphan state, unexpected JSON, impossible counters, denominator
changes, replay-failure accounting and late parent memory STOP.

Additional reviewer inline checks, not added unittest methods:

1. A complete mocked launch executes the real wrapper worker, parent assessment
   and read-only replay against the synthetic reader fixture. Exactly one launch
   requests the current C8 source with `_worker`, the current interpreter and
   the **60-second** bound. Three selected passes each return/decode 7,852 bytes
   and complete 151 rows: **23,556 synthetic bytes** in total. Replay leaves all
   fixture artifacts byte-identical. Prior acquisition workers/plans/replays and
   network calls are tripwired by the fixture.
2. A launcher returning exit zero but producing no worker outputs cannot be
   promoted to success. It yields STOP with no numerical pass and a
   `NOT_ATTEMPTED` parent validation; read-only replay retains that result.
3. Actual **metadata-only binding** passes all twelve dependency hashes and the
   retained receipt/header contract under a `Path.open` guard prohibiting every
   `products` path. No prohibited open was attempted. The derivative checks
   confirm only 151 rows, 1,131-byte stride, 7,852 selected bytes and the fixed
   label order; no raw cards or coordinates were printed or persisted.

Synthetic fixtures use private temporary files, not retained science data.
Their mocks are process-local and restored. The metadata smoke does not verify
the current product content hash: that operation remains part of authorized
execution, distinct from selected-field interpretation.

## Input and isolation contract

The wrapper checks the exact C1 outcome, slot-4 receipt and header hashes without
calling C1's acquisition plan or replay. It binds only the known retained EPIC
source list. PRIMARY identity/frame and SRCLIST correction metadata are checked
in the appropriate HDUs, followed by the reviewed all-column width derivation
and nine-column selected schema. Planned product verification rehashes the
single source-list file and exactly replays its structural header report;
neither operation loads a FITS data array.

Selected interpretation opens that file with `buffering=0` and invokes the
reviewed five-span reader. No full-row fetch or photometric column is added.
All 151 rows must be returned before geometry. Reader row/span indices are
removed from public progress, while byte/read/span/row-completion counts and
unknown-completion flags remain. Returned column values stay in memory only.

C1 is loaded as a fresh helper module with C8-local output/resource globals.
The wrapper does not invoke the old worker, plan or replay. The C5 centre
function is copied and its complete AST is compared with pinned C5 source;
old C5 code is not imported/executed to construct a centre. This preserves the
published ICRS convention, cardinal 120-arcsecond offsets and FK5/J2000
conversion without fitting, recentering or selecting new coordinates.

## Receipt and scientific limits

The one process-tree worker is externally bounded at 60 seconds using the
existing pinned helper; memory is a monitored 268,435,456-byte high-water cap,
not OS-enforced allocation prevention. Aggregate JSON is limited to 1 MiB with
a 64-KiB terminal reserve. Parent verification has a distinct selected-byte
pass. Every later numerical replay adds another pass and reports its accounting.
Hard interruption without a receipt remains unknown work, not zero; failure
artifact replay is not a substitute for numerical verification.

The runtime retains full scientific validity counts and unresolved association
states rather than turning invalid catalogue values into runtime-clean data.
Corrected positions govern only the fixed positional association; original
positions govern region contacts. The unique-control exemption is confined to
the published aperture. No row filtering, nearest-match choice, adaptive radius,
new aperture, extent-to-radius conversion, catalogue-mask area, map-fraction
multiplication or photon analysis is introduced.

Public summaries contain aggregate diagnostics and the planned scalar relative
offset, not source IDs, current row ordinals, absolute coordinates or a hidden
coordinate cache. Arbitrary exception strings are not persisted; logging uses
substituted safe exceptions. An operationally complete stage can still have
an incomplete association or invalid scientific values. The strongest outcome
remains **`SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`**, not a physical source
identification, calibrated background, recovery gate or discovery.

## Final reviewed anchors

| Artifact | SHA-256 |
| --- | --- |
| C8 wrapper | `bd76ab70fb36ca2ea9c350401ab36991baa8fd30b3bf160c546c788a536ad0e3` |
| C8 tests | `0bd5ba02add739318553de6029147e79d625b8dcde8c5180b3674c9088370733` |
| C8 protocol | `9b4a86517fdafcccf16c1004808a87a457c4c05b63b51f6e9da5163675330c14` |

All three hashes were independently recomputed after the preflight repairs.
No remaining blocking issue was found within this scoped contract. Parent
must preserve exact reviewed dependency bytes, including the previously pinned
counts definition, and freeze before any real selected-column execution.
