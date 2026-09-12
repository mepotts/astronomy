# Independent M2a pre-execution review

Date: 2026-09-12. Reviewer: next_route_research agent. Scope is acquisition and
structural validation of twelve fixed PRF products, not fitting or scientific
acceptance. No PRF FITS, unknown pixels or coordinates were requested. No prepare,
run, Git action, environment installation or remote code execution was performed.
Only this review and `tests/test_m2a_review.py` are reviewer-owned changes.

## Initial checkpoint: findings, not GO

Read the complete project operating rules, README, M2a protocol, implementation
and author tests, NEXT-LOCALIZATION-PROPOSAL, coordinate audit, and the reused
stream/save and process-tree helper implementations. Independently read the
actual official [exporter source](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/export_mat2fits.m)
and [release README](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/00README.txt)
as text. The web tool could not open them; the initial sandbox exporter request
was denied before connection. Approved owner-context documentation requests then
returned both complete texts. No downloaded code was executed or installed.

The exporter supports two double-precision 117-by-117 image HDUs, primary PRF and
extension uncertainties, primary-only required VERSION, and the specified
physical header keys. It does not promise BUNIT or checksum cards. The protocol
correctly avoids requiring those undocumented fields. Its numeric sampling,
identity, finite/support checks and no-clipping rule are consistent with a
structural-only stage. Real products may still disagree; a disagreement must
remain a STOP, not trigger a schema relaxation during acquisition.

The explicit twelve-URL enumeration agrees with the proposal's selected corners.
Thirty-second socket timeouts and the 45-second worker deadline are different
limits; the latter includes hash/header validation. Cleanup can take additional
time and depends on the verified owner context. This review does not newly prove
universal process-tree cleanup under restricted Windows tokens.

Read-only `context()` and dependency evaluation passed on retained TPFs, checking
their hashes/headers without a new pixel fit. All three 11-by-11 stamps remain
inside the fixed rectangles and use no extra 44-column or one-pixel shift.
The documented absolute-coordinate caveat remains; this is not independent
astrometric calibration. Thirteen local dependencies plus the separately pinned
runner are presently checked by the draft.

### Reproduced initial defects

The first independent 12-test run produced six passes and six failures:

1. Replay accepted `unknown_search_authorized=true` and
   `localization_validated=true` in the summary.
2. Replay accepted a success summary above failed/unlaunched product outcomes.
3. A successful worker-start marker with the wrong manifest identity was accepted
   when the artifact inventory correctly hashed that malformed marker.
4. A response receipt with a wrong body hash/size was likewise accepted.
5. A missing successful response receipt was accepted if the inventory listed
   only remaining artifacts.
6. A synthetic exit code zero without any required worker output caused the
   parent to launch all twelve products and report success, rather than stop.

The receipt mutation fixtures intentionally update inventory hashes: they test
semantic validity, not an adversarial ability to defeat cryptographic hashes.
Hashing a bad or missing receipt is not a replacement for verifying its required
identity/content. The author was asked to validate complete successful receipts
before launching the next product, share those checks with replay, and enforce
terminal flags/status and stop-first-failure ordering.

Three additional reviewer tests cover post-failure second-launch rejection,
changed partial-byte rejection and full-body structural-failure retention. The
review suite now has 15 tests; all are offline synthetic/mocked requests and
temporary receipts. The fixture builder is reused from the author suite, whereas
URL expectations, failure sequences and mutation assertions are independently
specified. Pinned Ruff 0.16.5 passed for the review test file.

This checkpoint is not final signoff. Final source/protocol/test hashes and a
complete rerun after author repairs must be recorded below before preparation.

## Final preflight receipt: GO for manifest preparation only

All reproduced findings above are resolved in the reviewed revision. The new
`complete_product()` verifies successful attempt/worker identities, required raw
receipt and retained bytes, absence of conflicting failure, and complete
recomputed validation. The parent invokes it after exit zero and before the next
launch, preserving the original worker return code if parent validation fails.
Replay uses the same validator. New terminal checks reject promoted flags,
inconsistent exit/status fields, invalid elapsed values, post-failure launches
and a summary status inconsistent with the outcomes. The manifest's ordered
twelve-product identity is also checked during replay.

Independently re-read the revised implementation/protocol and added author tests.
No FITS schema, product, coordinate rule, scientific threshold or byte/network
limit was loosened. In-memory synthetic full-success, partial-success/failure,
import failure and reservation failure all remain fully accounted for. Successful
and stopped replay paths were exercised without network; the independent partial
success test also compares every temporary file byte before/after replay.

Independent execution:

```text
dyson-revet/.venv/Scripts/python.exe -B -m unittest discover \
  -s tess-short-eclipses/tests -p "test_m2a*.py" -v
33/33 PASS (18 author + 15 reviewer), 0.940 seconds reported test runtime

dasch-pilot/.venv/Scripts/ruff.exe check \
  tess-short-eclipses/scripts/m2a.py \
  tess-short-eclipses/tests/test_m2a.py \
  tess-short-eclipses/tests/test_m2a_review.py
Ruff 0.16.5: PASS
```

The intentionally truncated FITS fixture emitted its visible Astropy warning and
was rejected as expected. Tests use mocked requests/process results; they do not
newly measure public-server behavior or repeat the separately established
owner-context real descendant-cleanup test. No actual M2a manifest/run was made.

Reviewed SHA-256 values:

| File | SHA-256 |
|---|---|
| `scripts/m2a.py` | `610a150f031266d1d1728ac8356b8061a45627cb4f0f40f36c2a424737a9491c` |
| `M2a-PROTOCOL-2026-09-12.md` | `737e7ea72216fe358da4cd95b3556944209c47a41e50547ddec4e741c1c54986` |
| `tests/test_m2a.py` | `382bc30c884792d23391b44170aa6525a5ae912f87afa0b69941cd108d2933df` |
| `tests/test_m2a_review.py` | `2b6f717c95fd486105c7b30cb40a67b740abd7d84f084c9aeba3110038f6b8da` |

**Final scoped review: no remaining pre-execution blocker identified.** Parent
may approve manifest preparation against these bytes. Acquiring the twelve FITS
still requires the separately reviewed manifest GO and verified owner execution
context. Any actual structural or transport failure must preserve STOP and partial
bytes; this signoff does not pre-authorize an amendment/retry. Product validation
cannot authorize localization claims, physical depth or an unknown-target search.

## Independent post-acquisition audit

The parent authorized this audit after completing acquisition against manifest
`f63e087a88054ac1336b71dce9956324de48acacc5ffed25b5f1f01697a6e816`.
On September 12 the reviewer invoked the frozen `m2a.py replay` **once**, read-only:

```text
EXACT_M2A_REPLAY_PASS: no network, no writes, no fit
```

That replay rechecked the manifest dependencies, original TPF hashes/header
context, attempt/worker/response semantics, all outcome artifacts, and all 24
retained PRF/uncertainty HDUs through the unchanged structural validator. It did
not interpolate, normalize or fit a PRF. No new request or acquisition was made.

A separate PowerShell audit, without importing the author validator, verified:

- All **13 dependency hashes**, the separately pinned runner hash, the exact
  approved manifest hash, and the summary's manifest binding and false science
  flags.
- **12 ordered outcomes**, each identical to its separate outcome receipt, each
  with worker and accepted return codes zero; **12 attempts**, **12 worker-start
  markers**, and **zero failure receipts**. The unchanged frozen replay also
  checks the ordered filenames against the exact twelve-product selection.
- **60 artifact hashes**: exactly five actual files per product directory, namely
  attempt, worker-start, response receipt, validation receipt and FITS body.
  Attempt/worker identities agree and bind the approved manifest/product.
- Raw-body, response and validation hashes/sizes agree. Each Content-Length is
  **230,400 bytes**, matching its retained body and validation receipt; the twelve
  bodies total **2,764,800 bytes**. Every file is below 300,000 bytes and the total
  is below both the summed 3,600,000-byte per-request cap and stage ceiling.
- Saved validation receipts describe **24 arrays of 117 by 117**, all with
  `BITPIX=-64`, `NSAMP=9`, **zero negative samples in either array**, and absent
  BUNIT. The full native-coordinate/identity/schema and finite/support checks
  passed the unchanged replay. No independent new array statistics were computed.
- The three original TPF byte hashes remain equal to their M1b receipts; their
  total remains **144,368,640 bytes**. Native target coordinates are exactly the
  stored header-derived stamp positions plus the retained physical origins, with
  no new centroid or coordinate adjustment.

| TIC | Original TPF bytes | Unchanged SHA-256 |
|---|---:|---|
| 450781262 | 48,807,360 | `5efa81b8e8c4546d9f2a1a3315e3af460f37eb8c7d03339730383fb9d7ea40ab` |
| 53206761 | 44,818,560 | `bb6e6079ebb8b9433775a6962a9881f4df502e0e0e7c91af9e6ac2b651506a2e` |
| 2041210548 | 50,742,720 | `e6a130778c6c793bcff621e95bd53c0444c534353960e8055aecd567e1129b9a` |

Parent-recorded elapsed time per product ranges from approximately **1.141 to
1.204 seconds**. These are retained outcome timings, not a separate reviewer
network benchmark or a newly demonstrated deadline-cleanup test.

Audit implementation note: an initial ad hoc header-string assertion expected
integer-form `NSAMP=9` and stopped on the valid exporter serialization `9.`.
The reviewer inspected the saved header cards and compared numeric values in the
read-only checker; the completed independent audit passed. This was a reviewer
text-check defect, not a failed scientific-stage gate. The frozen validator
already correctly accepts equivalent numeric serialization; **no protocol,
source, tests, inputs or result receipts were altered**.

Final audited summary SHA-256:
`df8d51790225a99d3a240c33dcc6e56561e3d6b4fda5422e1e17eed288a50ffb`.
The preflight source/protocol/test hashes above remain unchanged. Only this
review was appended during post-audit work.

**Result: acquisition and structural replay independently verified.** The
appropriate terminal label remains `PRF_PRODUCTS_STRUCTURALLY_VALID`, with
`localization_validated=false` and `unknown_search_authorized=false`. Absent units,
uncertainty covariance, absolute registration, model mismatch and empirical
source-confusion/negative-control validity remain unresolved scientific questions.
