# C3c: one XSA attitude-product HEAD, no download

Prospective September 12, 2026 metadata contract. Freeze source, tests and
independent review before execution. This follows
[the documented alternate-source proposal](XMM-ALTERNATE-PPS-SOURCE-2026-09-12.md).
C3/C3b STOPs remain unchanged. No old network plan, product GET, retry, archive
refresh, coordinates, credentials or body interpretation is authorized.

## Exact one-request scope

```text
HEAD https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&name=ATTTSR&expflag=X&expno=000&datasubsetno=0&sourceno=000&extension=FTZ
```

The ESA/ESAC client explicitly uses HEAD on this AIO service. These are
documented product-field selectors, not an exact remote `filename` argument.
OB is deliberately not supplied as an undocumented instrument value. Actual
availability and package membership are unknown.
[Client source](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html),
[parameter reference](https://astroquery.readthedocs.io/en/stable/api/astroquery.esa.xmm_newton.XMMNewtonClass.html).

One exclusive attempt, one fresh anonymous session; `trust_env=False`, no
authentication, cleared cookies, no redirect/retry/Range, 5/15-second socket
timeouts. Never read the response body, including errors. Use the existing
process-tree helper with a 30-second worker deadline; cleanup allowance is
separate. Frozen helper SHA-256:
`11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.

Require HTTP 200 at the exact requested URL, identity/absent content encoding,
positive unambiguous decimal Content-Length <=2097152, and a packaging-compatible
binary Content-Type from the allowlist below. Length describes the advertised HTTP entity only.
Missing/ambiguous lengths or rejected metadata stop without a fallback GET.

## Safe disposition metadata, not member identity

Retain only the established HTTP allowlist: Content-Type, Content-Length,
Content-Encoding, Date, ETag, Last-Modified. Bound their aggregate UTF-8 bytes
to 65536; keep the stdlib HTTP parser's 65536-line/100-header bounds.
Never persist Set-Cookie or raw Content-Disposition.

Parse Content-Disposition in memory only: maximum 2048 bytes, one unambiguous
value, no control/non-ASCII characters, disposition attachment or inline, one
filename parameter. Extended `filename*`/continuation forms and additional
parameters are conservatively rejected rather than guessed or normalized.
The resulting filename must be an ASCII basename of at most128 characters,
beginning alphanumeric and otherwise only alphanumeric/dot/underscore/hyphen;
reject any `..`, separators or trailing dot. Persist only that basename and
disposition type. Missing/invalid/ambiguous disposition gives a named STOP,
with a safe parser status but no raw field or exception text.

Classify the exact expected basename `P0884250101OBX000ATTTSR0000.FTZ` as
`EXPECTED_RAW_FILENAME_ADVERTISED`; safe `.tar`, `.tar.gz`, `.tgz`, `.zip`
basenames as `PACKAGE_ADVERTISED_MEMBERS_UNKNOWN`; otherwise stop as unrecognized
packaging/filename. These labels do not establish body identity, an archive's
sole member, compressed-member size, actual FITS structure or attitude usability.
A subsequent bounded download/extraction needs a separate frozen contract.

Content-Type uses a packaging-compatible binary allowlist, not merely exclusion
of text. All accepted classes permit application/octet-stream or
application/x-download. TAR additionally permits application/x-tar,
application/tar or application/x-gtar; gzip/TGZ permits application/gzip,
application/x-gzip or application/x-tar; ZIP permits application/zip or
application/x-zip-compressed. The expected raw FTZ permits gzip or FITS media
types (application/fits, application/x-fits, image/fits). JSON/XML and mismatched
package/media combinations stop. Parent replay revalidates the safe derived
disposition and classification; the deliberately discarded raw disposition
cannot itself be independently reparsed from public receipts.

## Receipts and reuse

Use hash-verified C1 JSON/hash/memory helpers and C0d HTTP rules where useful,
not their plans/workers. Pin C1 source
`13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5`
and C0d source
`de1d481b185067722546edca1a51dadcd6a5a7fd7d328e60f0ad5d6980272af3`.
Bind current source/tests, protocol snapshot, dependencies, runtime and actual
output/timeout/budget configuration. JSON <=131072 bytes total, reserve32768
for terminal receipts; monitored worker/parent peak <=500000000 bytes, not an
OS allocation limit. No products or full-header files are written.

Exclusive parent/worker/request markers preserve one slot as completed, failed,
interrupted or unattempted. A helper nonzero/timeout cannot pass. Hash every
retained receipt and preserve partial/truncated metadata after failure. Parent
and offline replay recheck safe HTTP/disposition schema, length, packaging,
resource totals and artifact closure without network. Catastrophic failures
permit only explicitly labelled failure-artifact replay, not product validation.

Strongest result: `XSA_ATT_ENTITY_METADATA_RETAINED`; not actual product
availability by GET, verified package membership, geometry, burst recovery or
discovery. Publication and private-coordinate disclosure remain gated.
