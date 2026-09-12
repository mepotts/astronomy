# XMM C0d independent pre-execution review

2026-09-12: **GO for the five fixed metadata requests under the frozen protocol.**
The reviewer read the complete protocol, `metadata.py` and `test_metadata.py`,
independently ran all 17 mocked tests successfully, and verified pinned Ruff
passes. No real HTTP request, product inspection or earlier-artifact edit was
performed. No additional framework or independent test file was needed.

## Scope and safeguards checked

- The pinned local inventory and index select each of the exact five name/URL
  pairs once. Four HEAD slots precede the single summary GET; there is no
  filename fallback, redirect, automatic retry or link following.
- A fresh anonymous session per slot disables environment authentication and
  proxies, clears cookies, has no auth and requests identity encoding.
- The HEAD branch never calls the raw-body reader, including for HTTP errors.
  Raw header value lists preserve duplicate Content-Length values. Positive
  decimal lengths must agree numerically; missing, conflicting, zero, signed,
  exponential or otherwise nondecimal required values STOP.
- HTTP parsing has bounded line/header counts, and retained safe header values
  have a separate 65536-character cap. Only the six protocol allowlisted header
  names are retained. The summary is limited to 262144 retained bytes plus one
  overflow-detection byte; encoded or non-HTML bodies are not consumed.
- One pinned helper invocation bounds the entire worker to 60 seconds. Each
  dispatch also checks elapsed time, with 5/15-second socket timeouts inside
  that total deadline. Helper cleanup allowance is separate, not permission for
  additional requests.
- Exclusive parent/worker/slot markers and protocol/dependency bindings prevent
  a resumed batch. Every slot remains represented after failure or interruption.
  A prelaunch failure preserves five NOT_ATTEMPTED rows; observed markers in an
  exceptional parent path are explicitly UNVERIFIED_ATTEMPT rather than success.
- The parent independently replays each successful slot from HTTP/body receipts,
  checks request order, rejects later requests after STOP, verifies worker
  artifact/ledger closure and dependency identities, and retains the raw worker
  return code. Timeout/nonzero exit cannot become success. Saved outcomes have
  a read-only artifact-hash and semantic replay path for ordinary batch results.

Previously reported parent findings are resolved in the reviewed version:
internal named STOP codes survive sanitized failure accounting, and a summary
requires a final HTML footer plus the control ID in parsed text outside
script/style blocks. Arbitrary exception messages and worker console text are
not persisted, avoiding accidental header/credential leakage. The raw helper
return code and structured internal error type/code remain available; this is
not a promise that every external-library error gets a more specific reason.

Tests include HEAD no-read on success/error, duplicate-length conflicts,
anonymous safe headers, cap-plus-one retention, encoded-summary refusal,
incomplete-footer refusal, full five-slot success and exact replay, first-error
STOP, elapsed deadline, changed HTTP/dependency rejection, late-slot rejection,
prelaunch failure and a single whole-batch timeout. The reviewer did not run
`run`, `_worker` or any live request outside these mocked fixtures.

## Acceptance limits

`SIZE_AND_SUMMARY_METADATA_RETAINED` is not a scientific pass. HEAD lengths are
advertised compressed entity sizes, not downloaded-body hashes, expanded FITS
sizes, RAM requirements or acquisition permission. Request markers count local
attempt starts, while successful_responses counts accepted slot receipts; they
do not erase failed HTTP responses or imply all five requests completed.

The summary check establishes limited control-ID presence and structural
closure, not exposure-level mode, version or timing eligibility. The retained
eligibility remains `METADATA_INCOMPLETE_FOR_CONTROL_CONTRACT` until independent
offline inspection records explicit evidence and missing fields. No GTIs,
simultaneity, usable photon data, recovery or discovery is established here.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C0d-2026-09-12-data/metadata.py` | `de1d481b185067722546edca1a51dadcd6a5a7fd7d328e60f0ad5d6980272af3` |
| `XMM-C0d-2026-09-12-data/test_metadata.py` | `f09483f099ce1be998cc00464842d58e00333da06cd438efe70885ccfc9eb0ed` |
| `XMM-C0d-2026-09-12.md` | `02505d4ac4945ed8284036bf2e952a3e8a51d8072fc7d2d965d09f42cbbf4e34` |

Source, tests and protocol remain author-owned and were not edited by this
reviewer. No remaining material pre-execution blocker was identified.
