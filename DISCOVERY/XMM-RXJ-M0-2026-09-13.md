# RXJ M0: one observation-directory metadata request

Prospective, not frozen or executed. Adopted after the completed C9 experiment
under [next-control decision](XMM-NEXT-CONTROL-DECISION-2026-09-12.md). This is
not an acquisition/recovery authorization for this field, and changes nothing
in the first control's preserved results or unresolved gates.

## Exactly one request

One anonymous GET to
`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0851180501/`.
This is the explicitly constructed observation-directory probe in the decision,
not a previously observed child link. No redirects, retries, authentication,
environment credentials, cookies carried into the request, recursive following,
HEADs, PPS requests or scientific products. A fresh requests.Session has
trust_env=False, auth=None and cleared cookies. Accept-Encoding is identity.
Socket timeouts are5seconds connect/15seconds read. The existing hash-pinned
process-tree helper imposes30seconds for the worker plus its existing cleanup
allowance. No background request continues after that helper's cleanup.

HTTP status must be200, the returned URL exact, Content-Encoding absent/identity
and MIME text/html or application/xhtml+xml before body access. Persist only
Content-Type, Content-Length, Content-Encoding, Date, ETag and Last-Modified;
never cookies/authentication headers or arbitrary exception text. HTTP parser
limits must not exceed65536bytes per line/100headers. Safe JSON receipts are
at most65536bytes each and262144bytes aggregate. No memory-limit claim is made.

Retain at most65536body bytes, reading at most one additional byte to detect
overflow. No automatic cap increase. If present Content-Length must be a single
decimal nonnegative integer and match retained complete body length; conflicting
or comma-combined duplicates are unsupported and STOP. No compressed HTTP
content or decompression. Empty, truncated, wrong-MIME or oversized responses
are STOP. A partial index can be retained/hash-bound but is not a complete index.

## Offline interpretation fixed before response

Require UTF-8, one title and one h1 whose normalized text is exactly
`Index of /FTP/xmm/data/rev0/0851180501` (optional trailing slash), explicit
opening/closing html and body and final `</body></html>` allowing whitespace.
This is deliberately a narrow Apache-style profile, not a generic HTML repair
parser; an otherwise useful variant may receive a preserved STOP.

Require exactly one anchor whose href is `PPS/`, the same-observation absolute
path, or the exact HTTPS same-observation PPS URL. No query/fragment/credentials,
encoded or parent-directory substitute; do not follow that anchor. Other index
anchors are counted but never requested. The output is an aggregate anchor
count and the single verified PPS URL, not a PPS inventory or retrieval proof.

Strongest success label: `OBSERVATION_INDEX_WITH_PPS_LINK_RETAINED`.
No camera modes, event filenames, byte sizes, exposures, background usability,
eligibility, counts, recovery or discovery follow from this label.

## One-shot provenance and validation

New isolated folder only. Exclusive run-start, protocol snapshot, worker-start,
HTTP/body, worker-result and outcome artifacts. Existing artifacts prohibit a
second run, including after failure. A worker-start marker records the single
permitted request invocation; if killed before a response, actual transport
completion is unknown, not zero work. No retry is inferred from failure.

Bind runtime source/tests, this protocol/snapshot, the adopted decision and
the original reviewed C0c transport source/tests as implementation lineage,
plus the exact deadline helper and owner Python executable/version. The new
runtime uses the C0c anonymous-session/cap-plus-one pattern but validates HTTP
status/MIME before any body read and uses its own safe errors and index parser.
It does not call any old stage's worker, request or replay.

Parent retains raw worker return code and only output byte count/hash, then
independently validates markers, binding, body bytes/hash, safe HTTP receipt,
complete-index interpretation, exact artifact set and worker result. A nonzero
worker result cannot become success. Named STOP/error-type receipts exclude
arbitrary error messages. Offline replay repeats hash/schema/index checks only;
it never makes a request or rewrites artifacts. Failure-artifact validation is
labelled separately from successful complete-index interpretation.

Synthetic tests and independent review precede root's exact-byte freeze and
the single authorized execution. Any follow-up PPS listing requires a separately
specified request. No automatic observation substitution or bundle acquisition.
