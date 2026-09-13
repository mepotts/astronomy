# RXJ M2 independent prospective review

**Scoped GO for root's exact-byte freeze and separately approved single raw
summary metadata GET.** Reviewed 2026-09-13. No actual request, product access,
summary-body inspection, run preparation or earlier science replay occurred.

## Final anchors and checks

| File | SHA256 |
| --- | --- |
| `XMM-RXJ-M2-2026-09-13-data/listing.py` | `a4620e9d991761276be1b32a6dc693d4a1846999d368bdddb928ab4ff5df24e6` |
| `XMM-RXJ-M2-2026-09-13-data/test_listing.py` | `12c782baacff8e29b160feb4c197ccf2df335a6403d35623c0c80a322d91d186` |
| `XMM-RXJ-M2-2026-09-13.md` | `d26c216910fc9c72f9134e439b012f77d6e2acfc09f3df74eec61f560a5e0871` |
| Stage `.gitignore` | `a3d36689196abc4d80b5b7c7822a45b1b2352762c057ff7cffca28d99f7a3e28` |
| Stage `.gitattributes` | `6479ecb330326a8606dd432356bb0389409f7eb615fbbd97bc6b7324530fbd03` |

Read the complete adopted request design, frozen M0 implementation, deadline
helper, new source, protocol and tests. Independent final commands:

```
# DISCOVERY/XMM-RXJ-M2-2026-09-13-data
../../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_listing -q
# Repository root, Ruff 0.16.5
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache DISCOVERY/XMM-RXJ-M2-2026-09-13-data
```

**11 tests PASS; Ruff PASS.** A separate actual metadata-only binding and JSON
round-trip check passed for all **12 lineage/evidence dependencies** plus the
two stage privacy-file hashes. Session/collect/worker tripwires and an explicit
guard against product and `summary.html` opens were active. No stage artifacts
were created. Source/tests/protocol hashes remained unchanged after the final
privacy-attribute portability edit.

## Scope and inherited-code audit

The sole URL has the adopted `obsno=0851180501`, `level=PPS`, `name=SUMMAR` and
`extension=HTM` selectors. It does not invent an instrument or exposure selector,
exact remote basename, package URL or uniqueness assertion. There is no HEAD,
Range, retry, redirect, linked request or extraction operation. Session credentials
and environment proxies are disabled; cookies are cleared. The pinned helper
provides the reviewed 30-second process-tree timeout and cleanup allowance;
socket timeouts are 5/15 seconds. It is not a memory limit. No new OS timeout
test was performed in this review.

The hash-verified M0 buffer has exactly six body-filename substitutions, one
`.gitignore` allowlist insertion and three science-counter renamings. All are
counted before compilation. Fresh modules prevent mutation of M0 or another
M2 instance; no unchecked source reread/cached-bytecode path is used. The
inherited worker function intentionally runs with isolated M2 paths and
configuration, not the prior-stage worker command. The final protocol clarifies
that distinction. Its HTML semantic parser is replaced, not reused.

Collection checks exact final URL, status200, text/html, absent/identity content
encoding, bounded safe header values and optional positive within-cap decimal
length **before** body access. Wrong final URLs become a boolean mismatch,
not retained arbitrary URL text. Safe headers reject duplicate values and
non-ASCII/control text before persistence. Content-Disposition is parsed
separately; no raw value enters receipts. Missing disposition is permitted;
named dispositions must match the requested observation/product/extension
positions without demanding unobserved instrument/exposure values. Duplicate,
extended, path-bearing, malformed or package-advertising names stop. Only
classification, disposition kind and an accepted basename digest survive.
Replay validates that safe classification, not the discarded raw-header parser.

No body rendering, HTML execution, links, embedded images, decompression or
package extraction is present. Raw body retention is 262,144 bytes, with only
one further byte read to detect overflow and not retained. A terminal EOF
receipt records transport completion independently of semantic completeness
and declared-length agreement; length disagreement can therefore retain EOF
while remaining STOP. A partial/overflow read lacks confirmed EOF.

## Privacy and receipt budgets

Stage `.gitignore` contains `/summary.html`; `.gitattributes` marks that body
binary/no-diff and fixes both privacy files to LF. The parent separately reports
that Git's ignore check confirms the body is ignored. This reviewer inspected
the exact rules and independently verified their binding hashes, not a new
Git invocation. Ignore rules are version-control safeguards, not filesystem
encryption or permission isolation; the raw HTML must remain local.

Receipts retain no body text, contacts, sky coordinates, raw disposition or
arbitrary exception/output strings. Public output is safe codes and encoded
worker-output length/hash. Per-receipt limit remains 65,536 bytes. Ordinary
JSON writes cannot consume the final 65,536-byte reserve within the 1 MiB
aggregate budget; only `outcome.json` may use it. The raw body has a separate
budget. A missing terminal receipt after interruption means unknown work,
not a claim of zero transport activity.

## Synthetic tests and independent adversarial probes

The author suite checks anonymous exact one-GET options, isolated verified
module loading and actual binding, deliberately footerless unadjudicated
success, immutable replay and exclusive re-invocation, PPS disposition choices,
package/status/encoding/length rejection before body reading, duplicate/unsafe
header rejection, no private URL echo, cap-plus-one consumption, partial timeout,
EOF with length mismatch, nonzero worker code, terminal reserve, typed EOF and
private-header mutations. Synthetic body text deliberately contains private
markers and is absent from every JSON receipt.

Four additional independent inline fixtures passed:

- Exact-cap valid response: all **262,144 bytes** retained, EOF true, one mocked
  GET and semantic identity still UNADJUDICATED.
- Remove EOF receipt after synthetic success and update outer hashes: replay
  rejects `STOP_TRANSPORT_INCOMPLETE`, not a transport success inferred from
  the nonempty body.
- Replace EOF byte count by its equal float and update outer hashes: replay
  rejects `STOP_TRANSPORT_RECEIPT`. Both tamper checks left all fixture bytes
  unchanged during replay and had a Session tripwire.
- Two disposition headers cause `STOP_DISPOSITION` with zero body bytes read,
  no body file and only the safe REJECTED classification retained.

Earlier independent loader/disposition probes also accepted an allowed
synthetic summary name and rejected package, parent-path, duplicate filename
and extended-filename cases. None used observed RXJ product content.

## Scientific limit and resolved preflight points

The initial design review called out differences from M0: pre-body length
limits, disposition privacy, ignored body storage, explicit EOF, real terminal
reserve and removal of semantic HTML gates. All are implemented. The parent
requested clarification of inherited-worker wording and LF rules for the two
bound privacy files; final text/rules resolve those points. No post-response
threshold change or repair was made.

The only acquisition label is `SUMMARY_HTML_RETAINED_UNADJUDICATED`. A response
advertised as HTML, including an HTML error page, can satisfy transport without
establishing observation identity, an exposure table, modes or inventory. No
stray observation-number occurrence is promoted to identity. Missing disposition
does not waive later body adjudication. Package rejection may stop a legitimate
packaged archive response; it authorizes no fallback or cap increase.

Later offline semantic inspection needs its own explicit scope. Summary rows
and durations would still not prove actual event-file availability, GTI/live
exposure, clean negatives, calibrated source support or recovery. M0/M1 STOPs,
C9 descriptive results and all stronger scientific gates remain unchanged.
