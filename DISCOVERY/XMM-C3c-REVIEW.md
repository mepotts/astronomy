# C3c independent pre-execution review

September 12, 2026. **GO for the frozen, single metadata-only HEAD contract.**
No remaining material blocker was identified. This is not permission for a
GET, redirect, retry, archive extraction, geometry analysis or publication.
No live request or scientific array access occurred during this review.

## Scope and evidence

Read the complete alternate-source proposal, C3c protocol, implementation and
all authored tests, together with the relevant frozen C0d/C1 HTTP, JSON,
resource and process-tree deadline helpers. The reviewer changed only this
document, not source, tests or earlier artifacts.

Independently executed:

- All **12 synthetic authored tests: PASS**, including mocked single HEAD,
  worker/parent assessment/offline replay, nonzero helper status, prelaunch
  unattempted accounting and a preserved truncated marker after timeout.
- **19 additional in-memory rejection checks: PASS**, covering disposition
  traversal, repeated parameters/conflicting values, unsupported extended
  filename, control characters, basename/length failures, HTTP method/status/
  URL changes, size ambiguity/overflow, encoding and media mismatch. A valid
  package advertisement and configured helper caps also passed.
- Pinned Ruff on the C3c data directory: **PASS**.

The tests mock every network call; response `raw.read`, `content`, `text` and
`iter_content` are forbidden. The positive worker fixture issues exactly one
HEAD, and checks that neither raw Content-Disposition nor Set-Cookie appears
in retained metadata. Existing C1 network plans/workers are forbidden by mocks.

## Contract review

The sole URL and HEAD method are fixed, with a fresh anonymous session,
environment credential/proxy handling disabled, cleared cookies, no redirects,
no Range, and 5/15-second socket timeouts. The source neither configures a
retry adapter nor calls a downloader. Its response branch never reads a body,
including on HTTP errors. Exact status/URL/method checks and duplicate-preserving
Content-Length parsing precede acceptance; the 2-MiB limit is advertised entity
size, not a promise about an embedded product.

The safe-header and disposition byte limits are distinct. Content-Disposition
is parsed in memory into a narrow safe basename/type/count, or a named rejected
status. Raw disposition and arbitrary exception/worker output are discarded.
Unsupported extended/continuation parameters are deliberately STOP cases.
Accepted MIME classes are restricted by packaging, not merely non-text.

Parent assessment independently recomputes accepted metadata from retained
safe fields and validates the success receipt. Because raw disposition is
deliberately absent, replay validates the derived schema and classification;
it cannot independently reparse the original raw disposition. This limitation
is now explicit in the protocol and must remain explicit in any result.

Exclusive parent/worker/request markers prevent a second attempt. Worker
nonzero/timeout cannot promote a metadata success. One-slot failure accounting
distinguishes an unattempted request from an unverified partial attempt; the
catastrophic-failure replay label does not certify metadata. Failed receipts
have exact keys, safe exception identifiers and named STOP codes or null.
Artifact closure, runtime/source/test/protocol/dependency bindings and JSON
accounting are replayed without network.

The reused helpers are isolated to the new directory and configured for a
30-second worker, 131072-byte JSON budget with 32768-byte terminal reserve,
65536-byte hash chunks and 500000000-byte peak-memory acceptance. The verified
process-tree helper provides the hard worker timeout with separate cleanup;
memory monitoring is not an OS allocation quota. No product/header files are
created by this stage.

## Pre-freeze corrections and final identities

Before any request, the author removed an obsolete overwritten hash constant,
fixed two lint findings, and aligned protocol wording with the explicit binary
MIME allowlist and unsupported extended disposition forms. The parent's exact
failed-receipt schema check and regression are present and independently pass.
These corrections were reviewed before sign-off; no thresholds were chosen
from a live response.

| Reviewed file | SHA-256 |
| --- | --- |
| `XMM-C3c-2026-09-12-data/acquire.py` | `542fce5755d9ff668d4ccd6e199b23780504368603352243d7e6fb7cfa727f90` |
| `XMM-C3c-2026-09-12-data/test_acquire.py` | `d3fd4d9775c40a094d761dad0f59e4b9e9d556fced7c6c3f7449324b5f4885ed` |
| `XMM-C3c-2026-09-12.md` | `cd75f4717291df12bdbc7f34f34b6398dfe36b7aa9885db1849416f60bb9609d` |

Even `XSA_ATT_ENTITY_METADATA_RETAINED` would establish only a bounded advertised
entity. It would not verify package members, body identity, GET availability,
FITS structure, attitude usability, geometry, burst recovery or discovery.
Preserve C3/C3b STOPs; any later acquisition requires its own prospective
contract and cannot silently weaken HEAD or scientific eligibility gates.
