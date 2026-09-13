# C9 independent prospective runtime review

**GO for the reviewed bounded recorded-counts implementation, subject to the
parent's exact-byte freeze and explicit execution approval.** This is not a
scientific recovery GO. Review completed on 2026-09-13; stage names retain the
2026-09-12 planning date. No actual photon values, retained product hashes,
source/map arrays or network were accessed in this review.

## Final reviewed anchors

| File | SHA256 |
| --- | --- |
| `XMM-C9-2026-09-12-data/inspect_counts.py` | `bb8d6d8c8a737e2d8be11d6f489091a1d0f7453fd320ad80a761709d56c81d03` |
| `XMM-C9-2026-09-12-data/test_inspect_counts.py` | `9a2cc126dc6e7a48a256f77e99eac5f761651a4680f08269f8874911f3592bff` |
| `XMM-C9-2026-09-12.md` | `9b805b3fb46b3914550bd9d993302631f2c36d429a9f99cf8a4713bbaa308c4d` |
| `XMM-RECORDED-COUNTS-PLAN-2026-09-12.md` | `141a6cbb7d987c1d2179391e50af9a9c306b21347275856696bf2ccb7e397812` |

The complete source, author tests, protocol and counts plan were independently
read, including final receipt-schema changes. Independent final commands:

```
# In DISCOVERY/XMM-C9-2026-09-12-data
../../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_inspect_counts -q
# In repository root; Ruff 0.16.5
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache DISCOVERY/XMM-C9-2026-09-12-data
```

**19 tests PASS; Ruff PASS.** Earlier 11- and 17-test checkpoints are not the
final suite. The intentional STOP fixtures emit safe generic diagnostics,
not the synthetic private exception strings.

## Scope and composition

The implementation binds the three exact C1 event products and header reports,
camera order, full packed schemas, time metadata, pure decoder/geometry/counter
source and test hashes, C1 source/tests, structural reader and deadline helper.
It imports an isolated pinned C8 helper module, but does not invoke an earlier
worker, acquisition plan or numerical replay. C8 outcome and contact-result
hashes are context evidence, not permission to reread the source list. The
unchanged C5 centre construction is protected by source and function-AST checks.

An independent **actual metadata-only** `binding()` smoke test completed under
a `Path.open` guard rejecting every retained `products` path, with old worker
and C8 numerical measurement tripwires: all 16 dependencies verified, 334
chunks, 255 fixed edges and 142,652,840 declared row bytes; zero product opens.
This checks real header compatibility and provenance, not event values or
astrometric calibration. No absolute sky/header values are reproduced here.

The numerical seam uses X/Y-valid rows, not only jointly valid selected rows,
and never projects declared X/Y nulls. Native selected-field completion, returned
projection work, successfully returned histogram computation, accumulation,
and durable chunk completion have distinct counters. Nine selected fields use
28 decoded bytes per row; full-row physical reads necessarily include opaque
unselected bytes. No earlier geometry, source masking or exposure calculation
is silently inserted.

## Failure and reproducibility evidence

The final suite covers full synthetic worker/parent/replay, immutable replay
artifacts, re-invocation, short reads, partial decoder conversion, projection
failure, changed chunk digests, impossible completed-prefix accounting, false
component completion, orphan/extra/nested files, denominator/schema/privacy
checks, nonzero worker status, prelaunch binding failure, terminal memory STOP,
cooperative deadline, output reserve, numerical replay failures and unexpected
structural warnings even under an outer warning-ignore filter. It also checks
top-level private-key rejection and JSON-type-exact camera markers.

Additional independent inline synthetic probes, without editing author files:

- A previously successful three-camera fixture was replayed with a forced
  second-camera projection failure. The emitted additional pass was
  `COMPLETED, FAILED, NOT_ATTEMPTED`, with physical row bytes `[135,68,0]` and
  decoded bytes `[84,56,0]`: **203 returned / 140 decoded bytes**, not zero.
  The failed current projection was explicitly completion-unknown; neither
  histogram nor accumulation had completed. Every artifact hash was unchanged.
- A failure at accumulation after a returned two-row histogram retained
  `histogram_rows_completed=2`, `accumulated_rows=0`, durable rows completed 0,
  and **90 returned / 56 decoded bytes**. The partial progress validator accepted
  this genuine state, and existing artifacts remained byte-identical.
- The final suite's late outcome mismatch occurs after all three complete
  numerical replays. Its failure output retains the full synthetic pass:
  **339 returned / 252 decoded bytes**, with all cameras completed. This is
  distinct from the separately tested failure-artifact-only replay, which
  explicitly performs no numerical reread.

Resolved prefreeze findings are retained as review history: the initial draft
checked chunk digest syntax without comparing each recomputed increment and
progress; lacked complete-prefix/current-chunk arithmetic closure; allowed
unrelated top-level files; and could encounter a final STOP chunk beneath an
OK camera. The final implementation compares exact per-chunk receipts during
parent/replay, checks prefix arithmetic, rejects unexpected files, and rejects
that contradictory STOP/OK combination before numerical reread. Missing C1
test binding and numerical-replay failure tests were also added before freeze.
Synthetic TCDLT card formatting was corrected to preserve the declared exact
scale rather than allowing a FITS formatter to round it. No actual event
measurement had been performed to choose these repairs.

## Resource evidence and its version boundary

The [independent full-size synthetic fit](XMM-C9-INDEPENDENT-SYNTHETIC-FIT.md)
was read in full. Another reviewer exercised physical synthetic files with the
exact whole-file sizes, event offsets/strides and 3,323,958 rows, using real
product hashing, structural parsing, unbuffered row reads, numerical kernels,
the actual subprocess/deadline helper, parent assessment and numerical replay.
That source-bound result was for draft
`562786dae3cc4c835d8d9b3c43a4b4428adcb98d75dc2528ad75b0beb05ec11b`,
not the later receipt-hardening hash above. Its reported run+parent time was
8.828 s, replay 2.937 s, 709,463 JSON bytes, worker peak 73,211,904 bytes and
parent peak 75,014,144 bytes, all below the prospective caps. This reviewer
did not rerun that physical-file benchmark or decode its files.

The later changes tighten receipt schemas/type equality and add tests; the
data paths and scientific selection are unchanged. The parent retains the
decision whether to rerun the synthetic resource check for the final exact
hash. Neither the earlier kernel timing nor the author's mocked-verification
benchmark substitutes for the physical-file test. Its synthetic three-HDU
files and substituted input binding do not measure the exact real metadata
costs. No successful benchmark proves immunity to timeout or memory failure;
the actual 120-second worker tree limit, separate cooperative parent/replay
deadline, monitored 512 MiB peak and 4 MiB JSON cap remain enforced. An abrupt
kill without a terminal receipt leaves unknown work, not invented zero bytes.

## Scientific interpretation boundary

The maximum permitted label remains
`RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY`. All three cameras and all fixed
254-by-5 circle and unmasked-annulus histograms must be retained. Per-field
diagnostics overlap; the ordered rejection ledger is disjoint. Same-centre
circle and annulus are disjoint, but different-centre memberships need not be.
Header time inclusion and half-open bins are not GTI or live-exposure coverage.

C8's north/east/west aperture contacts and all five annulus contacts remain
attached; two usable negative apertures are not established. C5/C7 static-map
results are unchanged. No source masks, GTI/EXPOSU integration, background
subtraction, rates, detector-artifact veto, significance, selected episode,
period or unknown-source discovery follows from this stage. Parent/replay
agreement validates reproducibility, not those missing scientific conditions.
The original stronger recovery gate has not been weakened by this review.
