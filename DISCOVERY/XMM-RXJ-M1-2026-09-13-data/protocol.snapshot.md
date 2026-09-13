# RXJ M1: one anonymous product-name metadata query

Prospective, unexecuted. Preserve the frozen M0 HTTP404 STOP and observation
0851180501. This is metadata only, not eligibility or product acquisition.
The adopted [next-step note](XMM-RXJ-M0-NEXT-2026-09-13.md) supplies the retained
schema and primary documentation. No new schema, count, or product request.

## Exact request and limits

One GET to `https://nxsa.esac.esa.int/tap-server/tap/sync`, parameter-encoded
REQUEST=doQuery, LANG=ADQL, FORMAT=json and exactly this query:

```sql
SELECT obsid,filename
FROM xsa.data_product
WHERE obsid = '0851180501'
```

No TOP, ordering, pagination, retry, async job or followed link. Fresh anonymous
requests Session with trust_env=False, auth=None, cleared cookies, no redirect,
identity encoding and 5/15 second socket timeouts. The inherited audited helper
enforces a 30-second worker process-tree deadline. Raw response cap is 1,048,576
bytes, with only one additional byte read to detect overflow. HTTP parser caps
remain 65,536 bytes per line and 100 headers. Save only the existing safe header
allowlist, never Set-Cookie or arbitrary exception/output text. HTTP200, exact
encoded URL, application/json MIME and absent/identity encoding are required
before body access. Optional Content-Length must be decimal and equal actual
complete bytes. Errors, partial reads and overflow remain STOP; no retry.

## Deliberately narrow JSON profile

UTF-8 JSON with exactly metadata and data keys; duplicate JSON object keys STOP.
Exactly two columns named obsid and filename, in either declared order. Each
column has exactly the eight metadata keys observed in the retained JSON schema,
datatype char, arraysize *, xtype null. Other descriptive metadata is null or a
control-free string of at most 1,024 characters. Rows are two scalar strings:
obsid exactly 0851180501, filename an ASCII basename of 1–255 characters matching
`[A-Za-z0-9][A-Za-z0-9_.-]{0,254}`. No paths, URL characters, whitespace, nulls,
numeric coercions or extra columns. A differing service representation stops;
it does not establish scientific absence or justify changing this frozen parser.

Retain every returned row in response.body, including duplicates and original
order. Small receipts contain row and unique-name counts, excess duplicate rows,
duplicate-name group count, and case-insensitive groups containing multiple
distinct spellings. A SHA256 of sorted exact filename/multiplicity pairs gives
an order-independent checksum; it does not silently select among duplicates.
No raw names or unvalidated server strings are echoed in errors or stdout.

The only successful label is
RETURNED_PRODUCT_NAME_RECORDS_ONLY_COMPLETENESS_UNKNOWN. Empty is permitted and
completeness remains UNKNOWN for every response. No inference about absence,
availability, exact size, rights, observing mode or actual file contents. The
raw response may later support a separately frozen exact-product contract.

## Minimal reviewed composition and proof

Load the frozen M0 source from a hash-verified byte buffer with a fresh module,
never unchecked rereads or cached bytecode. Exactly six quoted index.html
literals become response.body; no other inherited source text changes. Override
stage paths, URL, raw cap, PASS label, binding, JSON interpretation and MIME
validation only. The legacy receipt key index holds the small product-record
summary; it is not an HTML claim. Transport, one-shot markers, safe STOP schemas,
exclusive receipts, return-code checks, artifact allowlist and offline replay
remain inherited. Each receipt stays capped at 65,536 bytes; all receipt JSON
stays capped at 262,144 bytes. Raw body is a separate explicit cap, not JSON
receipt budget. Parent subprocess output is retained only as length and SHA256.

Bind the frozen M0 source/tests/protocol/outcome, adoption note, retained schema
and observed JSON-format evidence, M0's inherited C0c/deadline/decision lineage,
current source/tests/protocol and owner Python runtime. No old worker or old
network request is called. Before execution, synthetic tests must prove exact
query/module isolation, malformed/duplicate schema rejection, row identity,
basename/duplicate accounting, 1MiB+1 behavior, one anonymous GET, safe partial
failure, exclusive attempt, complete worker-parent-replay and tampering rejection.
The root freezes exact bytes before run. Replay is read-only metadata/hash
validation, with no network or scientific product access.
