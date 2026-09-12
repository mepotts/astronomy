# XMM C0b-1: first request, prospective schema gate

Frozen before the first request, 2026-09-12. Parent adopted C0b-1 in
[the continuation decision](CONTINUATION-2026-09-12.md). This is a new authorized
stage, not an extension of the finished eligibility-research request tranche.

Exactly one anonymous GET is authorized now to
`https://nxsa.esac.esa.int/tap-server/tap/sync`, with `REQUEST=doQuery`,
`LANG=ADQL`, `FORMAT=json`, and this exact `QUERY`:

```sql
SELECT table_name,column_name,datatype,unit,description
FROM TAP_SCHEMA.columns
WHERE table_name IN ('xsa.v_exposure','xsa.v_instrument_mode','xsa.data_product')
ORDER BY table_name,column_name
```

One attempt, no redirects/retries, no publication-table request. Retain at most
131072 response bytes, including partial/error bodies. The entire C0b-1 envelope
remains two requests / 262144 bytes; the second request is not authorized yet.
No coordinates, photon products, product GET/HEAD, accounts, environment installs
or remotely executed code. All new files stay in this note's named data folder.

The existing audited `dyson-revet/scripts/check_e_release.py:bounded_run` is
imported by absolute path, with SHA-256
`11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.
It launches the absolute worker path with a **30-second worker deadline** and
kills only its own process tree on timeout. Tree termination/reporting may take
up to the helper's additional cleanup allowance; it is not a promise that the
parent returns within 30 seconds. Use the verified owner execution context:
restricted-token cleanup was not universally successful in earlier tests.
Requests also have 5-second connect / 15-second read socket timeouts.

Preserve a byte-identical copy of this pre-request note, source/helper hashes,
exclusive run/worker-start markers, HTTP status/headers, partial or complete raw
body, body size/hash, worker return code and final outcome. A second launch must
refuse the existing marker. No timeout, malformed JSON, duplicate column, missing
table, cap overflow or HTTP error becomes success. Validate all three named table
schemas without guessing their columns. No scientific gate depends on the result.

After success, inspect the returned keys and freeze the exact proposed second
query for published control `0884250101`. If the returned schema cannot support
a defensible join and complete product/mode/size accounting, report that gap
instead of inventing a query. Parent review precedes any second request.

Acquisition entry point (network occurs only with `run`):
`XMM-C0b1-2026-09-12-data/schema_acquire.py`.
The immutable pre-request copy is `schema-protocol.snapshot.md`; later outcome
and query interpretation may be appended to this working note, not that copy.

## Executed outcome: STOP, no second request

One approved GET completed HTTP 200 in 0.875 seconds. The raw response is
2034 bytes, SHA-256
`5cccb1603a4e4c4361ba8c6dd9bf974e58bd476fed0d28c51c29db9dd351ceab`.
Worker return code 1, worker `STOP_REQUEST`, parent `STOP_PARENT`, with
`STOP_DUPLICATE_OR_ORDER`. This is a **local schema-validator failure**, not an
HTTP/service outage or evidence that the columns are unavailable. No timeout,
retry, second request, source change or promotion was performed. The first
failure stops this acquisition; remaining request allowance is not automatic
permission to continue.

The response has 21 unique table/column pairs: four product columns, thirteen
exposure columns and four instrument-mode columns. The service places the quoted
column spelling `"level"` after `filepath`, whereas Python's raw-string `sorted`
places its leading quote first. This is sufficient to explain the failed guard;
the actual server collation rules were not established. Requiring Python lexical
equivalence to database metadata ordering was an unjustified implementation
assumption. Keep the failed source/receipt unchanged; an offline revision could
separately validate set membership and duplicate freedom without that assumption,
but is not executed or silently substituted here.

Pre-request protocol SHA-256:
`a72497955efe87a0a4ca8c38d9d01f0899fccd36f90461650c98820576ebb7d4`.
Executed source SHA-256:
`81a4ddcad7e6711f5844e22dcd4243d7279bf4a641c60048ce99047e5c682d82`.
The parent outcome records all eight pre-outcome file hashes. No real process
cleanup was needed; the historical owner-context helper test, not this fast
request, is the evidence for timeout-tree behavior.

### Read-only schema interpretation

| Table | Returned columns relevant to this task | Unresolved |
|---|---|---|
| `xsa.data_product` | `filename`, `filepath`, `"level"`, `obsid`; all char | No byte-size, checksum, product-type or public-rights column; path need not be an HTTP locator. |
| `xsa.v_exposure` | `observation_id`, `observation_oid`, `exposure_id`, `exposure_oid`, `instrument`, `instrument_mode_oid`, `mode_friendly_name`, `start_utc`, `end_utc`, `duration`, `is_scientific`, `filter` | Duration unit is null. The additional background-rate column is scientific metadata and is not proposed for query. |
| `xsa.v_instrument_mode` | `instrument`, `instrument_mode_oid`, `mode`, `mode_friendly_name` | Shared field names support a proposed relation, not demonstrated join integrity. |

Thus even an offline interpretation of the otherwise complete schema would
**not** establish complete product sizes, public access, simultaneous supported
camera modes or actual PPS availability. Do not invent a size column, treat
observation duration as file size, or cross-join every product with every exposure
and call that a product-to-camera match. No science-array value was returned.

### Frozen possible second query: partial diagnostic only, DO NOT EXECUTE

The smallest exact product-list diagnostic using verified column spellings is:

```sql
SELECT obsid,filename,filepath,"level"
FROM xsa.data_product
WHERE obsid = '0884250101'
ORDER BY filename,filepath
```

Use the same endpoint/GET parameters if the parent separately authorizes it,
one attempt, no redirects, hard 30-second worker deadline, at most 131072 bytes.
The lack of `TOP` is intentional: either retrieve the complete single-control
listing inside the cap or retain a capped failure; a truncated list must not
pass completeness. The frozen proposed query contains no unverified join and
no coordinates or science fields. Double-quoted identifier handling is proposed
ADQL syntax, not an executed service compatibility test.

This query cannot satisfy the original advertised-size and exposure-mode gates
by itself. **Recommendation: stop C0b-1 for parent review rather than spend the
last request on a partial diagnostic automatically.** A later approved stage
would need a documented size-bearing metadata interface and independent mode
accounting. That is a concrete metadata-access gap, not a reason to download
products or install SAS. First-request STOP remains the authoritative outcome.

### Integration caution

The retained HTTP receipt includes an anonymous service `Set-Cookie` header.
It was unnecessary for this unauthenticated query and is not needed for replay.
Do not publish that raw receipt without parent privacy review. Preserve the
original locally for this frozen audit; a separately identified redacted public
copy can retain safe headers and the original receipt hash without rewriting
the historical receipt. No cookie value is reproduced in this note.
Parent excluded the exact original `http.json` path from Git and prepared
`http-public.json` as a new redacted artifact. The public bundle intentionally
omits the cookie-bearing original; the outcome still binds its original hash.
Full eight-artifact byte replay requires the locally preserved original, while
public review can inspect the redacted receipt and other unchanged artifacts.

Parent disposition: preserve STOP and do not execute the proposed second query.
The next useful alternative, if separately scoped, is documentation/metadata for
an official archive product manifest or directory listing with advertised sizes,
or an explicitly approved size-only HEAD request. No specific size-bearing
endpoint was verified here, and none was contacted. Do not spend another query
on a listing already known to omit the required size field. Research ends here.

### Parent integration checks

The parent independently inspected all 21 returned rows, the preserved failure
and the executed source. A later pinned Ruff check reports two `BLE001` findings
at the worker and parent broad-exception boundaries. Both boundaries record an
explicit STOP and return failure rather than silently reporting success, but the
probe is not lint-clean under the root policy. The executed source remains
unchanged as a historical failed-attempt artifact; it is not adopted as a reusable
production transport. Any replacement must fix the exception reporting and the
metadata-order assumption before execution. No lint exclusion or safety bypass
was added to make this archived probe pass. TESS's separate tests and lint pass.
