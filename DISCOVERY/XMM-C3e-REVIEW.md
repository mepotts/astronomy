# C3e independent pre-execution review

September 12, 2026. **GO for the frozen two-GET contract.** The initially
missing C3e `products/` and `headers/` ignore rules are now present; the parent
independently verified both with Git before execution. The final format-only
source correction and rerun are documented below. No blocker remains. This
review is not authorization for a HEAD refresh, extra product, pixel analysis
or publication.

## Independent evidence

Read the complete protocol, source and all tests, plus the relevant frozen
C3/C1 transport, configuration, expansion, product-record and exact-file-set
interfaces. The reviewer modified only this document, with no HTTP or map,
attitude or photon values accessed.

- **All 14 tests independently PASS, none skipped.** This includes the actual
  prior C3 offline replay in the exact local runtime, plus the synthetic
  two-GET worker/parent/replay integration and partial/failure cases.
- **Pinned Ruff: PASS.**
- Independently exercised complete real-metadata `binding` and `get_plan`
  with all network sessions forbidden: **PASS**, nine dependencies, exact
  imported sizes `[503855, 275217]`, aggregate **779072** bytes, two GETs.
  Binding is JSON-roundtrip stable and no new run/outcome marker exists.
- Previously verified all 13 original C3 artifact hashes against its pinned
  outcome and re-read the two original successful HEAD receipts. The complete
  binding independently revalidates that prior evidence again without requests.

The synthetic suite proves that first-request failure or a short body leaves
the second request unattempted, changed ETag/Last-Modified/length stops before
body reads, both imported validators are required, another URL or the prior
404's length cannot substitute for either map, and mutated imported hashes
fail binding. It also covers exact product sets, nonzero helper status,
prelaunch two-slot accounting, preserved truncated timeout marker and exclusive
repeat blocking. The original current-module network workers/plans are forbidden
by mocks; only the isolated original module's offline replay retains its plan.

## Scope and implementation assessment

The new plan contains only the indexed pn S003 and MOS1 S001 EXPMAP8000 names,
in that order. It imports the complete original successful HEAD records and
their hashes, not unproven size literals alone. Original validators are:

| Product | Compressed bytes | ETag | Last-Modified (GMT) |
| --- | ---: | --- | --- |
| pn map | 503855 | `"7b02f-627d58844ee00"` | 2024-11-26 19:05:28 |
| MOS1 map | 275217 | `"43311-627d58807e500"` | 2024-11-26 19:05:24 |

The verified C1 downloader compares exact GET identity, length and both supplied
validators before streaming. Each request has a fresh anonymous session, no
environment credential/proxy handling, cleared cookies, identity encoding,
no redirect/Range or configured retry, and 5/15-second socket timeouts.
One extra byte may detect overflow; none is retained beyond the fixed size.
There is no attitude request or dependency on a successful attitude acquisition.

Original C3 replay and current helpers are separate module instances. Original
C3 retains its paths, 120-second deadline and 128-MiB expanded cap. Current
helpers bind the new output directory, 60-second worker, 779072-byte compressed
total, 32-MiB per-file / 64-MiB aggregate expansion caps, 1-MiB chunks and
128-MiB free-space checks. The verified tree helper and terminal memory/JSON
handling remain in use. The 500000000-byte peak limit is monitored acceptance,
not an OS allocation guarantee.

Only gzip CRC/EOF-complete expansion and the pinned structural/header reader
are used. No raw-FITS, archive-package or alternate-filename fallback is added.
Parent success requires both slots OK and exactly two raw, two expanded and two
header files, matching hash/size/resource receipts and header replay. CRC
completion is bound to the worker expansion receipt, not independently repeated
decompression during replay. Header/seek and FITS conformance/checksum limits
of the existing reader remain; skipped map arrays are not interpreted.

The full two-slot failure ledger and labelled failure-artifact-only replay
preserve interrupted/unattempted work. A nonzero or timeout cannot pass; final
parent memory STOP cannot be promoted by replay. Public records omit cookies,
arbitrary exception strings, coordinates and full header cards; complete product
and header files require the pre-execution ignore coverage noted above.

## Final reviewed identities and boundaries

| Reviewed file | SHA-256 |
| --- | --- |
| `XMM-C3e-2026-09-12-data/acquire.py` | `ad80cb38306388f69e51bce78fe4787279e7ba5402b4b6f7b10b44362b54aa4e` |
| `XMM-C3e-2026-09-12-data/test_acquire.py` | `d913c42299305bdb62fba2d0f3e8147e0568cf778f541649fab5adb1de51e825` |
| `XMM-C3e-2026-09-12.md` | `ca3fa37ad01c1542423f7ba3b8ebd1b81cd6a9375eb081728062e2cad45dfc44` |

There is no source change requested by this review and no live outcome was used
to choose these rules. Original C3's MOS2 HEAD404 STOP is immutable. Success
would provide only retained/header-inspected maps, not validated exposure
units, WCS/time compatibility, source/background coverage, recovered bursts or
discovery. Fixed scientific gates and planned multiplicity/unavailable-camera
accounting remain. Actual header adjudication precedes a separate map-value
contract.

### Final pre-freeze formatting/ignore receipt

The parent's whitespace check stopped the freeze before any request. The source
was corrected only at EOF: appending one LF byte to the final source reconstructs
the previously reviewed SHA-256
`5f0e02a09ad1547a3cc1e3957987f9ccfa96fddcc153d193bc10d61618e98210` exactly.
This independently proves the change from the reviewed bytes is formatting-only;
no behavior changed. Tests and protocol hashes are unchanged. The reviewer
reran all **14 tests (none skipped) and pinned Ruff: PASS** against the final
source hash in the table. No run-start marker exists. Both new ignore entries
were independently observed in the root ignore file; the parent reports exact
Git ignore verification. The earlier execution prerequisite is satisfied.
