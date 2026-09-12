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
