# RXJ M0 independent prospective review

**Scoped GO for parent exact-byte freeze and a separately approved single
metadata request.** Reviewed 2026-09-13. No live request, product acquisition,
scientific array or previous-stage replay was performed by this reviewer.

## Final anchors and verification

| File | SHA256 |
| --- | --- |
| `XMM-RXJ-M0-2026-09-13-data/listing.py` | `fe664f73447eae02345358b03c6c7754628e7d9f240028c8720ed2786b462a38` |
| `XMM-RXJ-M0-2026-09-13-data/test_listing.py` | `963e082830d97ce2c743d2003799c2d846e0ead7139ea670a7f5ba8df0e9fdb6` |
| `XMM-RXJ-M0-2026-09-13.md` | `b864f9daee136bb27da7d0a94bcd095fdc86c6ea92636ac337f4aab3a1209e18` |

The full protocol, adopted next-control decision, implementation and tests
were read; final changed sections were reread. Independent commands:

```
# In DISCOVERY/XMM-RXJ-M0-2026-09-13-data
../../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_listing -q
# Repository root, Ruff 0.16.5
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache DISCOVERY/XMM-RXJ-M0-2026-09-13-data
```

**17 tests PASS; Ruff PASS.** An actual read-only binding check verified all
four pinned dependencies (decision, C0c source/tests and deadline helper),
with `collect`/`worker` tripwires. No run-start, snapshot or response artifact
was created in the real stage directory.

Operational freeze condition: after the above check, the parent reported a
post-merge checkout newline conversion of the decision file, not a scientific
edit. The pinned original decision hash remains
`beb4a8edda667ad4adb75dad773600a8276278d3d473e276ed5d34b2e3b5b7aa`.
Restore those exact bytes with explicit newline attributes and repeat the
metadata-only binding check before freeze/execution; do not repin the runtime
to incidental checkout conversion. No such restoration is performed by this
reviewer.

## Request and interpretation boundary

The only request is the deliberately constructed observation-directory URL
`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0851180501/`.
It is not treated as an already observed child link. The fresh anonymous
session disables environment credentials and proxy configuration, clears
cookies, has no authentication, disables redirects, and requests identity
content encoding. One GET uses 5/15-second connect/read timeouts; the pinned
process-tree helper supplies the 30-second worker deadline and its existing
cleanup allowance. No old worker, follow-up URL, HEAD or product request is
called. This review did not re-exercise the helper's OS kill behavior.

Status, exact response URL, MIME and content encoding are checked before body
reading. HTTP parser line/header limits are checked. The stream retains at
most 65,536 bytes and reads at most one overflow byte; no decompression or cap
increase is authorized. Complete declared length must match. Safe response
header schema is checked for STOP responses as well as successful ones.
Partial/empty/error responses remain unsuccessful retained evidence.

UTF-8 and the specified narrow index profile are required: one title and h1
with the fixed observation identity, explicit html/body starts and ends,
terminal closing sequence, and exactly one accepted same-observation PPS
anchor. The parser does not repair arbitrary HTML, execute content, follow
links or inspect the PPS directory. A legitimate alternate index format can
receive STOP. Success means only
`OBSERVATION_INDEX_WITH_PPS_LINK_RETAINED`, not proof that any child product
exists or is individually retrievable.

## Receipt, failure and replay review

Exclusive markers and artifact checks prevent automatic re-invocation after
success or failure. The worker marker is an invocation record, not proof of
HTTP completion. Missing terminal evidence after interruption means unknown
transport work; it must not be described as a confirmed empty server response.
Safe exceptions exclude arbitrary messages. Parent retains only encoded worker
output byte count/hash, not its raw text. Receipt caps remain 65,536 bytes each
and 262,144 bytes aggregate; no memory-limit claim is made.

The final suite covers exact anonymous request options, safe header retention,
cap-plus-one overflow, wrong status/redirect URL/MIME/encoding before body
access, declared-length mismatches, forbidden PPS-link alternatives, malformed
identity/footer/anchors, immutable offline replay, exclusive re-invocation,
nonzero worker code, partial failures, orphan/extra/nested files, JSON caps,
scalar-type checks and safe parent failure/output fields. A socket-read failure
fixture preserves exactly 31 returned body bytes and performs no retry.

Additional independent inline synthetic probes passed:

- A complete valid index padded to exactly **65,536 bytes**, with matching
  Content-Length, succeeds; exactly that many body bytes are consumed.
- An empty response stops as `STOP_EMPTY_INDEX` after exactly one mocked GET.
- A helper return code 124 with no worker terminal receipt remains STOP with
  `STOP_WORKER_INTERRUPTED`; offline replay makes no request.
- Replacing a worker body byte count with its numerically equal float is
  rejected as `STOP_WORKER_RECEIPT`.

The reviewer independently reproduced one prefreeze defect: after a legitimate
wrong-MIME STOP, adding a forbidden Set-Cookie field to retained HTTP metadata
and updating the artifact hash still passed offline STOP replay. Final code
separates safe HTTP schema validation from successful-response gates and checks
retained response artifacts on both replay paths; the regression now rejects
that mutation. HTTP/body artifacts without a request marker and a body without
HTTP metadata also stop. Root's scalar-type and parent-error findings were
fixed before freeze using exact JSON comparisons, typed return/output fields,
and safe failure patterns. No actual response was used to choose these fixes.

Failure-artifact-only replay remains explicitly unverified index interpretation.
Successful-index replay recomputes the parser result and receipt closure but
never repeats the GET. A syntactically valid output hash is not independent
reconstruction of discarded raw worker output; it is the parent's recorded
receipt. These limits do not prevent the bounded metadata step.

## Scientific conclusion

This is a preflight for a published known control, not a new-source search.
No camera modes, exact event filenames/byte sizes, exposures, clean negatives,
counts, eligibility, calibrated recovery or discovery can be inferred from
its permitted success label. A PPS listing or product request requires a new
scoped contract and approval. No automatic target substitution follows STOP.

The first control's completed C9 results and stronger missing gates remain
unchanged. Its final result write-up was separately claim-checked against the
receipt/aggregate audit, including the per-CCD assignments; no discrepancy
was found and no extra photon pass or episode search was performed.

## Postrun: preserved HTTP 404 STOP

The parent restored the original LF decision bytes and froze M0 at `6512188`
before the single execution. This reviewer independently repeated the complete
four-dependency metadata binding check after execution; the newline condition
above is now resolved without repinning source or changing the decision.

**PASS, receipt-only audit of a STOP outcome.** The exact fixed observation
directory returned HTTP **404**, `text/plain; charset=utf-8`, with declared
Content-Length **19**. The code rejected status before any body read. There is
no `index.html`; the worker body record is null. Thus 19 is an advertised
response length, not a downloaded or parsed index length. Zero index-body
bytes were retained; this does not make a claim about transport-level buffering.

One worker-start invocation is recorded. Worker return code is 1, its named
failure is `STOP_HTTP_STATUS`, and parent assessment completed with status
STOP, `index=null`, `products_fetched=0`. Parent reports offline replay
`PASS_OFFLINE_REPLAY STOP`; this reviewer did not invoke another replay or
request. The retained worker-output receipt contains 53 encoded bytes and a
hash only, not the raw output text.

Independently checked all five artifact-hash references, exact worker marker
and STOP receipt, safe HTTP schema, four dependency hashes, snapshot/source/
test binding and absence of any body artifact. Five JSON files total **2,518
bytes**, below both per-file and aggregate caps. All stage file hashes remained
unchanged across the audit. `collect`, `worker` and `replay` tripwires and a
product-open guard were active throughout; no products or network were opened.

Outcome SHA256:
`57e0e1ec8a149a6e90a1e1847f089c1a4d3529480f1416704f3ac964f37d82c7`.
Run binding SHA256:
`7bc6f5658753058f9369cabca6aa33b962b2739f5855c44046d07637f653dbed`.
HTTP receipt SHA256:
`decbfbc7e9ed32a3fde544849b6cc5bb2e40f02c64998f24a85bee4225f76ff8`.

This is a negative result for **one constructed mirror path**, not evidence
that RX J1301.9+2747, observation0851180501, its public data, or all alternative
archive routes are unavailable. No PPS link was established, no link was
followed, and no recovery or availability inference is justified. The frozen
attempt remains used; no retry, redirect or alternate observation is authorized
by its failure.
