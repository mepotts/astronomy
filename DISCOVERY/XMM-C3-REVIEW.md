# XMM C3 independent pre-execution review

2026-09-12: **GO for the fixed four-HEAD gate followed conditionally by four GETs
and header-only inspection.** The complete protocol, implementation and tests
were independently read. All 12 synthetic integration tests and pinned Ruff
pass, including the final exact-product-set mutation regression. No real HTTP
request, product payload inspection, array decoding or earlier-artifact change
was made by this reviewer. Only this review document was written.

## Phase gate and frozen reuse

The retained inventory/index hashes bind exactly the three named exposure-map
products and one attitude product. Each name/URL occurs once. The eight-slot
plan has four HEADs first, then GETs for those same entities. Missing, conflicting,
oversized or unsuccessful HEAD metadata stops the batch before any GET.
Parent ledger verification independently re-establishes all four HEAD results
before accepting the first GET marker.

HEAD bodies are never consumed, including error responses. Sessions are fresh,
anonymous and environment-isolated, with no redirect/retry or cookie reuse.
The exact GET identity, accepted HEAD length and supplied entity validators are
checked by the reused transport before body consumption. Changed-ETag regression
confirms zero product-body reads. Retained safe headers, parser bounds and raw
identity transfer remain limited to the protocol's contract.

C1 is loaded from verified source bytes without unchecked bytecode reuse.
Only its reviewed transport/expansion/header, memory, save and resource helpers
are used; tests explicitly prohibit the old C1 plan/run. The in-memory output
directory, compressed ceilings, expanded limits, memory/deadline policy, chunk
size, free-space threshold and JSON/report budgets are explicit bound
configuration. Dependency hashes include C1 source/tests, C0d rules, structural
reader/both tests and deadline helper. Full binding survives an exact JSON
round trip; configuration mutation is rejected.

## Resources, closure and failure handling

The implementation enforces at most 2 MiB compressed per entity and 8 MiB
aggregate; GETs retain at most accepted lengths with one overflow-detection
byte. Expanded limits are 32 MiB per file and 128 MiB aggregate, including prior
partials. Streaming gzip must reach verified EOF/CRC. Synthetic overflows and
corrupt gzip leave partial outputs and prevent subsequent GETs.

Free space is checked before dispatch and before every request. One helper call
sets a 120-second worker bound, separate from cleanup allowance. Monitored
worker/parent peak acceptance is 500000000 bytes, not an allocation quota.
Serialized JSON/header caps and terminal-report reserve reuse frozen C1 behavior.
All eight slots remain represented after STOP or timeout. Partial marker JSON
is retained with UNVERIFIED_ATTEMPT fallback; failure-artifact replay explicitly
states that products remain unverified. Raw nonzero/timeout codes cannot become
technical success.

The parent's accepted path rechecks HEAD/GET identity, ordered receipts, raw and
expanded hashes/sizes, reproduced header reports, stage-specific resource
snapshots and artifact closure. The author's final self-audit added an exact
success-only path-set check: precisely four compressed files, four expanded
files and four header reports, with compressed total equal to the four accepted
HEAD lengths. The reviewer agreed this closes the fixed-product contract and
verified the orphan-product rejection regression. Generic aggregate limits alone
are no longer the only protection against extra product files.

## Privacy and scientific limits

Products and full header reports stay under local-only `products/` and
`headers/`; the parent independently confirmed root ignore coverage before
execution. Public receipts contain safe identity/resource/hash information and
HDU counts, not full cards or coordinates. Reused header handling captures
warning categories without arbitrary warning text; exception output is sanitized.

The header reader seeks over declared data spans. Its bounded malformed-header
scan limitation and lack of full FITS/checksum validation remain unchanged.
No exposure-map pixel, attitude sample, photon, source-list value or numerical
WCS region test is interpreted. Structural success cannot establish numerical
band, units, stable pointing, aperture coverage, live exposure, recovered bursts,
unknown-search readiness or discovery. Those require the separate metadata and
geometry adjudication. No publication, submission or coordinate disclosure is
authorized by this review.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C3-2026-09-12-data/acquire.py` | `7a9f6aafe0631137850b991ef8ed990275a050c40e303dbdf9a51d0455315c60` |
| `XMM-C3-2026-09-12-data/test_acquire.py` | `d322831429e4c613f2d759fe75818c68b9fba1c24abaf08108a37584b646ab1c` |
| `XMM-C3-2026-09-12.md` | `ef076fe58242199da9dac4f1b413c90e8af2263367f0e8cfa6cc672e9903ed63` |

No remaining material pre-execution blocker was identified.
