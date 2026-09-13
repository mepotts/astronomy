# XMM C3b independent pre-execution review

**GO for the separately frozen one-HEAD/three-GET subset stage, headers only.**
The complete protocol, source and tests were independently read. All 11 tests
passed, including the actual prior-STOP offline replay test in the exact local
runtime; no tests were skipped in this review. Pinned Ruff passed. No new HTTP
request, product-array inspection, earlier-artifact change or implementation
edit was performed by this reviewer. Only this review document was written.

## Prior evidence and isolation

Two distinct verified-byte C3 modules each instantiate their own frozen C1
module. The prior-replay instance retains C3's original output paths, budgets
and dependency/runtime binding. The current-helper instance has only the new
output directory and reduced compressed/expanded totals configured. Tests verify
that these module objects and their C1 globals are independent.

The original C3 outcome hash and full offline replay establish the preserved
two-OK/one-404-FAILED/five-NOT_ATTEMPTED ledger, worker exit 1 and zero downloaded
products. Only the two successful prior HEADs are imported, including complete
safe HTTP/receipt records and their hashes. Actual advertised sizes are checked
against 503855 and 275217, not merely copied as unverified literals. Tests reject
changed prior outcome identity, a substituted URL, modified binding evidence
and misuse of the 404's 19-byte error length.

Old network workers/runs are forbidden by test guards. Original C3's read-only
plan/binding validation is necessarily invoked inside its authorized offline
replay; it is not a new request or use of the old acquisition plan for C3b.

## New phase gate and limits

Exactly one new attitude HEAD is followed conditionally by pn, MOS1 and attitude
GETs. No pn/MOS1 HEAD refresh or MOS2 retry occurs. The attitude HEAD must pass
before any GET; each GET must match its applicable HEAD identity/length and any
supplied validators before body consumption. The missing-attitude and changed
prior-entity fixtures confirm that no disallowed GET/body read follows failure.
Fresh isolated anonymous sessions, safe headers, no redirects/retries and
exclusive markers reuse the reviewed frozen helpers.

The current binding includes exact imported HEAD evidence, source/tests,
protocol, runtime, inventory/index and nine relevant source/test/helper
dependencies. Its configuration is JSON-native and round-trips exactly.
Compressed ceilings total 2876224 bytes; expanded ceilings are 32 MiB per file
and 96 MiB aggregate. The 120-second worker deadline, 500000000-byte monitored
peak acceptance, 1-MiB chunks, 256-MiB free-space requirement, 10-MiB JSON cap,
2-MiB header cap and terminal reserve remain explicit configured limits.

Parent assessment rechecks prior provenance, ordered four-slot ledger, the
attitude gate, HEAD/GET consistency, retained hashes/lengths, header replay,
resource snapshots and artifact closure. Reused exact-product validation accepts
precisely three compressed, three expanded and three header-report paths, with
totals matching the three accepted heads; an orphan file is rejected. Nonzero
worker/timeout cannot become success. Truncated markers and prelaunch failures
retain all four slots, and failure-artifact-only replay explicitly leaves
products unverified. The full synthetic worker/parent/replay path passes.

## Privacy and scientific boundary

The parent independently confirmed root ignore coverage for C3b products and
full headers before execution. Public receipts retain safe names, hashes,
lengths, HDU counts and resource/status fields, not coordinates or arbitrary
cards/warnings/exception text. The inherited header-only reader and its
malformed-header, checksum and FITS-conformance limitations remain unchanged.

This subset is consistent with the original pn-plus-at-least-one-eligible-MOS
minimum, not a C3 pass or waiver of missing MOS2 geometry. Fixed regions,
required negatives, simultaneous coverage, thresholds and original multiplicity
accounting remain unchanged. No photons or geometry outcomes selected this
availability-based subset. Technical acquisition would still require separate
identity/band/unit/mask/time/WCS adjudication and a frozen geometry-value
experiment. It would establish neither stable aperture coverage nor burst
recovery, unknown-source readiness or discovery. Publication, submission and
private-coordinate disclosure remain separately gated.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C3b-2026-09-12-data/acquire.py` | `bc8f6ab039234e98347329412e706547c0c91e543ebffbfe9d8a4d1f5a4b7b92` |
| `XMM-C3b-2026-09-12-data/test_acquire.py` | `e3295401c6801193a11a2d046acecfc80ceabb9348a685984203e970f7cefaff` |
| `XMM-C3b-2026-09-12.md` | `7025a0af3a2714528b8a4360487760972e5977c48eb232a236c8ec239a2ff18a` |

No remaining material pre-execution blocker was identified.
