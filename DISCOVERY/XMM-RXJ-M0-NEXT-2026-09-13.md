# After RXJ M0: one ESA structured product-name query

**Recommendation: a new, separately frozen, anonymous ESA TAP query for
product names belonging to the same observation `0851180501`.** Do not retry
the HEASARC index, switch observations, invent PPS filenames, or fetch a data
bundle. This proposal has not been executed.

## What M0 means

The retained HTTP receipt reports404 at2026-09-13 04:35:10GMT for the exact
HEASARC observation-directory URL. M0 stopped before body access, with one
request and zero product fetches; the parent completed a STOP assessment.
`Content-Length:19` describes the rejected HTTP entity, not a scientific file.
No HTML-title or footer parsing was reached, so changing that parser would
not address this failure. The cause of the404 remains unknown.

HEASARC explicitly distinguishes public release from availability in its
mirror and notes that some datasets absent there are available in ESA XSA.
This supports trying the independent official service, **not** assuming this
particular observation is currently retrievable there.
[HEASARC XMMMASTER documentation](https://heasarc.gsfc.nasa.gov/W3Browse/xmm-newton/xmmmaster.html).

## Exact proposed next request

Endpoint: `https://nxsa.esac.esa.int/tap-server/tap/sync`.
One GET with `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=json` and exactly:

```sql
SELECT obsid,filename
FROM xsa.data_product
WHERE obsid = '0851180501'
```

Use proper parameter encoding, not an interpolated product URL. No TOP,
cross-table join, coordinate predicate, count-rate field, quoted `level`, or
unverified size column. Ordering is irrelevant. The proposed target and column
names do not come from inference: the retained
[C0b1 schema response](XMM-C0b1-2026-09-12-data/schema-response.body), SHA256
`5cccb1603a4e4c4361ba8c6dd9bf974e58bd476fed0d28c51c29db9dd351ceab`,
declares `xsa.data_product.obsid` and `.filename` as character columns.
Its previous Python-versus-database sort-order STOP stays unchanged; this
new proposal needs no database collation assumption.

The ESA/ESAC-authored client documents synchronous TAP/ADQL metadata access,
and its implementation identifies the above TAP base URL.
[Official client examples](https://astroquery.readthedocs.io/en/stable/esa/xmm_newton/xmm_newton.html),
[ESA client implementation](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html).
The direct `/sync` GET and JSON representation have additionally succeeded in
this repo's retained earlier [eligibility metadata requests](XMM-EXOD-ELIGIBILITY-2026-09-12-data/receipt.json).
The client itself documents VOTable/CSV output; JSON support here is based on
that observed service response, not an invented client guarantee. The exact
product-row query above remains untested.

## Narrow contract and honest outcome

Suggested new-stage budget: **one attempt,30-second audited process-tree
deadline,5/15-second socket timeouts,1MiB retained response plus one overflow
byte**. Fresh anonymous session, no environment credentials/proxies, redirects,
retries, asynchronous jobs, cookies sent or product following. Keep safe HTTP
headers, exclusive attempt markers and byte hashes; never publish Set-Cookie
or arbitrary server text. A cap failure is retained, not automatic pagination.

Validate the returned structured metadata by column names/types, then all
returned rows: exactly the requested observation string, two scalar strings,
bounded lengths, no control characters and safe filename basenames. Preserve
duplicate/ambiguous name counts instead of silently selecting a version.
Do not require HTML structure or Python lexical equivalence to server order.
HTTP/JSON/schema/row violations produce a named STOP, not a parser repair loop.

Strongest useful result: **the service returns these exact product-name
records for this observation**. No absence/completeness inference is justified
unless the response also establishes that the service did not truncate it;
the existing JSON examples did not establish a general overflow indicator.
An empty result or unproved completeness is not proof that no PPS exists.
Retain all received rows within the cap, and do not add an automatic second
count/schema query to settle an unexpected response.

If the required imaging event/source-list and ancillary names are actually
present and unambiguous, their documented filename components can ground a
later **specific ESA AIO metadata/access contract**. Such a contract must still
freeze the exact intended returned basename, permitted entity format, sizes
or bounded-stream limits, and full failure accounting before any product GET.
Do not execute a filepath, fabricate an exposure number or treat a package
as the identified individual file. No such HEAD/GET is included now.

## Why this is useful despite its limits

The next uncertainty is exact official product identity after the mirror404.
This query addresses it directly, using an already observed schema, instead of
spending another request on an HTML variant or simply confirming an old
observation date. It does **not** satisfy the first control's former size gate:
the verified product schema contains no sizes, checksums, modes or rights.
The new label is deliberately a partial metadata result, not acquisition
eligibility. Actual file access, mode/time/schema checks and the unchanged
clean-negative/exposure prerequisites remain separate.

Exactly three primary documentation pages were read for this note. Local reads
were interface/protocol notes, the retained schema and M0 safe receipts only.
No query for `0851180501`, scientific product request, array inspection,
installation, code change or outward submission was performed. The M0 and
earlier C0b1 STOP receipts remain authoritative and unmodified.

Parent adoption: root read this complete note, independently opened the three
primary documentation sources, and rechecked the retained schema hash and both
character-column declarations. Adopt this same-observation product-name query
as the next separately specified metadata experiment. No archive query or
runtime freeze follows from this note alone. Completeness, rights, exact sizes
and actual individual-file retrieval remain unverified.
