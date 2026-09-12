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
