# RXJ M1 independent prospective review

**Scoped GO for root's exact-byte freeze and separately approved single ESA
metadata GET.** Review completed 2026-09-13. No live request, product access,
scientific array, run preparation or earlier-stage replay was performed.

## Final anchors

| File | SHA256 |
| --- | --- |
| `XMM-RXJ-M1-2026-09-13-data/listing.py` | `953d28ef3c079faf11a660bdae8c7c32cd1d8e0259c72bde9c0f794d30b5fb91` |
| `XMM-RXJ-M1-2026-09-13-data/test_listing.py` | `0885a3b200f4a4f1bd8281b963e19362b2bce41e995ebc7aafc0d79df5ae57ae` |
| `XMM-RXJ-M1-2026-09-13.md` | `64fe04e56f8dac954a1394ab65934fd8eb4d88797d0b4701fe645d0a2c009fc4` |

Full protocol, adoption note, source and tests were read. Final changed source
sections and the complete protocol were reread. Independent commands:

```
# DISCOVERY/XMM-RXJ-M1-2026-09-13-data
../../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_listing -q
# Repository root, Ruff 0.16.5
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache DISCOVERY/XMM-RXJ-M1-2026-09-13-data
```

**All 11 tests PASS; Ruff PASS.** The final actual metadata-only binding and
JSON round trip passed with **12 dependencies**, a product-open guard and
Session/collect/worker tripwires. No real stage artifacts were created.

## Request and composition

The encoded query contains only `SELECT obsid,filename FROM xsa.data_product
WHERE obsid = '0851180501'`, preserving the protocol's exact whitespace in
the bound query string. Its endpoint is the official synchronous ESA TAP
service; REQUEST, LANG, FORMAT and QUERY are properly parameter encoded.
No TOP, ordering, count, extra column, pagination, asynchronous job, second
request, redirect or link-following path is introduced.

The source is loaded from the exact frozen M0 byte buffer into a fresh module.
The six audited quoted `index.html` literals alone become `response.body`:
artifact list, collection path, body-record path, worker parser input, parent
parser input and response-artifact existence check. Compilation uses this
verified buffer, not an unchecked reread or cached bytecode. Each core load
is a separate module; the isolation test modifies one instance's cap and
confirms another is unchanged. The frozen M0 file is not edited.

Stage paths, source/URL/raw cap/status, binding, parser and successful MIME
validation are rebound consistently. Inherited functions resolve those fresh
module globals. The HTML parser is not used for M1 interpretation; the legacy
receipt key `index` contains the JSON product-record summary and implies no
HTML index. The child command points to M1's source, not M0's entrypoint.
M0's source/tests/protocol/STOP outcome and lineage remain hash-bound evidence,
not a call to its old request or worker.

Fresh anonymous session, disabled environment credentials/proxies, cleared
cookies, identity encoding, no redirects, 5/15-second socket timeouts and the
30-second pinned process-tree helper remain inherited. Successful HTTP requires
the exact encoded URL, status 200, JSON MIME and no content compression before
body access. The raw response cap is **1,048,576 retained bytes plus one
overflow byte**. JSON receipts remain separately capped at 65,536 bytes each
and 262,144 bytes total; changing the raw cap does not increase those limits.
This review did not independently exercise OS timeout cleanup.

## Parser and independent synthetic evidence

The parser rejects duplicate JSON object keys, wrong/extra metadata or data
keys, malformed two-column definitions, unexpected field types and row shapes.
It accepts either declared column order, not an inferred row ordering. Every
row must have the exact observation string and an ASCII basename within the
fixed 255-character rule. Path separators, URL syntax, whitespace, nulls and
coercions are rejected. Descriptive metadata rejects C0/C1 control characters.
These checks certify the declared metadata profile, not a valid XMM instrument
filename convention or an accessible file; the returned names are not executed.

All received rows remain in the bounded raw body, with duplicates and original
order intact. Summary multiplicities count exact strings. Case-insensitive
ambiguity counts groups of distinct spellings, not duplicate rows. Since
filenames are ASCII, lowercase grouping suffices here. The digest sorts exact
filename/multiplicity pairs and is independent of server row order. It is not
a product checksum or proof of complete inventory.

Beyond the final author suite, independent inline probes passed:

- Seed 9121301 generated 401 rows across 27 names. A separate Counter/digest
  calculation matched 374 excess duplicate rows, 27 duplicate-name groups and
  one case-insensitive ambiguous group. Shuffling rows and reversing declared
  column order preserved the complete summary and digest.
- A valid empty metadata response padded with JSON whitespace to exactly
  1,048,576 bytes passed the full mocked worker/parent path, retained exactly
  that body length, and kept small receipts below their unchanged budget.
  Its completeness stayed UNKNOWN; empty did not become an absence claim.
- After a successful synthetic run, the raw filename was changed and both
  body receipt and artifact inventory were rehashed. Offline replay still
  rejected the stale semantic digest as `STOP_INDEX_REPLAY`, without requesting
  data or changing any artifact. This distinguishes semantic verification from
  merely comparing the outer raw-file hash.

The author suite additionally verifies cap-plus-one consumption, no repeated
GET, partial timeout retention, raw nonzero helper code, safe failure headers,
schema/type/filename rejections, immutable full replay, one-shot guards and
receipt tampering. Actual product names were not queried to construct tests.

## Resolved prefreeze findings

An early draft incorrectly asserted seven body-filename literals. The
independent actual pinned-source load stopped as `STOP_ADAPTER_LITERAL_COUNT`;
inspection found six. Source, binding, protocol and regression were corrected
before any request. The earlier parser also omitted Unicode C1 controls from
its stated control-free descriptive fields; the final range check closes that
small contract mismatch without changing science selection.

One intermediate 11-test run had ten passes and one dependency-hash STOP from
checkout line endings in the adoption note. Root restored its exact committed
LF bytes; final binding verifies
`b4358d05d0d1cd4cf945867514b9c5bd3c6bd859dfe17069b5b52d86a8842e14`.
All 11 final tests then passed. These are local preflight defects and repairs,
not failed or repeated archive attempts. No frozen M0 result was altered.

## Scientific boundary

The only successful label is
`RETURNED_PRODUCT_NAME_RECORDS_ONLY_COMPLETENESS_UNKNOWN`. Completeness remains
UNKNOWN even for nonempty results; the protocol does not establish an overflow
indicator or authorize a second count query. An empty response, rejected
representation or unavailable endpoint cannot establish absence of public PPS.

Names and multiplicities alone establish neither actual retrieval, exact byte
sizes, rights, modes, exposures, file schema, clean negatives nor calibrated
recovery. A later product/access contract must be separately specified from
the actually returned names. M0's mirror 404, C9's descriptive counts and all
missing scientific gates remain preserved; this metadata route replaces none
of their results and authorizes no discovery claim.
