# XMM C0c independent transport review

## Pre-execution decision — 2026-09-12

**GO for the single protocol-defined directory-index request only.** No actual
HTTP request was made by this reviewer. Review covered the complete protocol,
worker and parent harness, six author tests and six independent mocked tests.
All 12 tests pass; pinned Ruff passes for all three Python files.

Two material preflight findings were corrected before this signoff:

- Ambient netrc/environment authentication could violate anonymous acquisition.
  The worker now uses a fresh session with `trust_env=False`, no authentication
  and cleared cookies. An independent prepared-request test checks that ambient
  netrc credentials are not consulted and no authentication/cookie headers occur.
- A worker success receipt alone did not establish transport success. The parent
  now verifies HTTP status, exact URL, safe headers, encoding/type/length, body
  size/hash, exclusive worker and parent markers, source/protocol snapshot and
  pinned helper identity. A forged success over HTTP 503 and a missing worker
  marker both produce STOP while preserving the raw worker return code.

Additional independent fixtures verify complete artifact receipts and a
byte-identical protocol snapshot, refusal of a second launch, hard-helper timeout
accounting without retry, and failed-worker marker/body accounting. Author tests
cover the exact request, safe headers, cap-plus-one overflow detection, redirect
refusal with retained error body, declared-length mismatch, exclusive outputs and
helper mismatch before a launch marker. Tests use synthetic temporary fixtures;
they do not inspect a live directory or request science products.

### Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C0c-2026-09-12-data/listing.py` | `6dfc1715fa477a69687fd54a01a6cd61abd26be99519f18fd4e9297cd3091e31` |
| `XMM-C0c-2026-09-12-data/test_listing.py` | `30475b5119844d1f28300bd03d40e1efeb404603d963c2580055079a934acbb1` |
| `XMM-C0c-2026-09-12-data/test_listing_review.py` | `fffc8a4d622cc097ad5c620df65bb992786aab0bd2c3dc30b6082954fcff6036` |
| `XMM-C0c-2026-09-12.md` | `3870ba101568699c4e36e71af829575a8e96299138b320bce734109f3bc50cfc` |

The independently reviewed test file is stable for the parent's freeze. Source
and protocol remain parent-owned; this reviewer changed neither.

### Scope and limitations

`HTTP_INDEX_RETAINED` proves only the specified transport/body contract, not HTML
product validity or scientific readiness. Offline inspection must still verify
directory identity and exact same-directory product links, excluding navigation,
sort/query and external links. Human-readable K/M/G sizes are not exact bytes
without an independently established unit/rounding contract. Missing/ambiguous
sizes must remain explicit. Availability does not establish instrument modes,
camera overlap, good-time intervals, photon content or a usable control bundle.

The 30-second worker-tree deadline has a separate cleanup allowance; it is not a
promise that the parent returns within 30 seconds. A failed attempt authorizes
neither a retry nor any linked-product request. Frozen C0b-1 records remain
unchanged. This signoff does not authorize new science measurements or discovery
claims.
