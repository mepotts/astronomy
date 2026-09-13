# After RXJ M1: one filtered observation-summary request

**Recommend a separately frozen, single ESA AIO GET selecting only PPS SUMMAR
HTML for observation0851180501.** This is a product-family metadata request,
not an exact-file lookup or a repair/retry of M1. No request or implementation
was performed for this note.

## Why not repair the TAP parser?

The retained363-byte M1 response declares `obsid` as `char` of arraysize10 and
`filename` as variable-length `char`. Its two rows contain `0851180501.tar.gz`
and `*/*`, not individual PPS basenames. The executed result remains
`STOP_COLUMN_SCHEMA`, worker1, one request, zero products. Accepting fixed-width
character metadata offline would not make these records the required inventory;
the wildcard is not a URL or an instruction to download everything.

Directly checked local anchors:

- [M1 outcome](XMM-RXJ-M1-2026-09-13-data/outcome.json), SHA256
  `159ee0322ae964ec20e4f79471e927dc7dc93a08adcb0a1f8b2b751ca843b384`.
- [Retained response](XMM-RXJ-M1-2026-09-13-data/response.body), SHA256
  `75d75114d209795f7177124f3eb44fc5c6f6d15e3aa4f485d36364df9aeab635`.

## Exact selector provenance

The ESA/ESAC-authored client's stable API documents the AIO endpoint, `PPS`
level, six-character `name` product selector and `HTM` extension. Its `filename`
argument is a local destination, not a remote filename parameter. Instrument
selection is optional; the documented list does not include OB.
[Stable API,0.4.11](https://astroquery.readthedocs.io/en/stable/api/astroquery.esa.xmm_newton.XMMNewtonClass.html).

The implementation's `_create_link` sends `obsno` and the selected keyword
parameters to AIO. It also exposes TAR-oriented retrieval/extraction methods;
a filtered request is therefore not documented to guarantee a single raw file.
Its convenience downloader performs HEAD first and its response branch expects
non-text content. Do not invoke that convenience workflow for a one-request
HTML contract, or copy that branch as a claim that HTML is invalid metadata.
[ESA client implementation,0.4.12.dev710+g038841faa](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html).

`SUMMAR` is grounded in the earlier official HEASARC product actually retained
by [C0d](XMM-C0d-2026-09-12.md):
`P0884250101OBX000SUMMAR0000.HTM`. Its observation/exposure metadata was
[separately adjudicated](XMM-C0d-OFFLINE-2026-09-12.md). The client examples do
not enumerate SUMMAR specifically. Combining an observed PPS product type
with the documented type selector is the explicit inference here; no live
RXJ summary availability or uniqueness has been established.

Proposed exact operation, **not executed**:

```text
GET https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&name=SUMMAR&extension=HTM
```

Do not supply `instname=OB`, exposure number/flag, subset or source fields
inferred from a different observation. Do not construct an expected RXJ
basename and then claim it was observed. The four parameters above restrict
the observation, pipeline level, product type and representation; they do not
prove there is exactly one matching product. The earlier successful C3d/C6
raw-file responses are transport precedents, not guarantees for HTML packaging.

## Smallest bounded next contract

One anonymous GET, no preliminary HEAD, retry, redirect, Range, credentials,
environment authentication/proxies, cookie reuse or linked-resource fetching.
Use the audited tree-aware helper with30seconds total worker deadline and
5/15second socket timeouts. Its cleanup allowance is not another request.
Freeze exact URL/source/tests/runtime, M1 anchors and this decision before
execution; preserve exclusive markers, every partial and the original STOPs.

Require HTTP200 and exact final URL. Admit only `text/html` with absent/identity
Content-Encoding. Bound safe response-header parsing; never persist raw
Content-Disposition or cookies. If disposition has a filename, require one
unambiguous safe basename identifying the requested observation, SUMMAR type
and HTM extension using the documented PPS field positions, without imposing
unobserved instrument/exposure values. Missing disposition is not alone a
failure for an inline HTML page; body identity still needs offline adjudication.
Reject malformed/conflicting disposition or a package-advertising basename.

**Raw-HTML-only contract:** TAR/ZIP/gzip/octet-stream or other unexpected media
and package advertisements stop before body access. Do not extract packages,
change the media policy after the response, or follow an archive link. This
may stop a valid but packaged service response; it deliberately tests a small
metadata route, not a broad bundle. Packaging support would require its own
explicit, bounded decision rather than an automatic fallback.

Stream at most262144 retained bytes plus one overflow-detection byte. Do not
retain the overflow byte. If Content-Length is present, require unambiguous
positive decimal, within cap and exact received-length equality; absent length
uses the prospective local cap. Record complete transport EOF separately from
semantic completeness. Do not invent validators from M1 or C0d. Reserve64KiB
within a1MiB JSON budget for terminal reporting; body storage is separate.

Keep the HTML local/ignored before execution because it may include observer
contacts and sky coordinates. Public receipts contain safe HTTP metadata,
hashes, byte counts and status only. Do not open it in a browser or execute
scripts, images or links. Parent receipt replay can verify hashes, one-slot
accounting, byte bounds and transport conclusions without a second request.

## Useful result without another brittle parser gate

Strongest acquisition label: `SUMMARY_HTML_RETAINED_UNADJUDICATED`, not modes
verified, complete inventory or recovery. A nonempty HTML error page could
satisfy transport checks; it must never pass observation identity on a stray
occurrence of the requested number alone.

Next, offline and without linked fetches, inspect explicit labelled observation
identity and complete exposure-table rows. Account for every row; retain
missing/ambiguous fields. Report per-exposure instrument, scheduled flag/ID,
mode/data mode, filter, stated timing and processing labels with original
units. Do not assume an exact heading, column order, literal `</html>` footer,
exposure count or filename list before seeing the exporter. C0d demonstrates
why transport EOF and a literal closing tag are different questions. Missing
usable tables or inconsistent observation identity yields a metadata-incomplete
adjudication, not a sequence of parser repairs and new downloads.

Explicit exposure IDs/modes could then ground a separately proposed narrow
PPS acquisition. Summary durations are not GTI/live exposure; rows are not
proof of public event-file availability or calibrated source support. No
photon acquisition, clean-negative claim, pn-plus-MOS waiver or discovery is
authorized by this note.

Research accounting: existing C0d/C6/alternate-selector notes and retained M1
JSON only; exactly two primary client documentation pages read, with in-page
searches. No archive/product request, new TAP query, actual scientific values,
account or outward submission.

Parent disposition: adopted as the next prospective metadata route after full
note review and independent primary-document checks. Implementation, tests,
independent review and exact-byte freeze remain prerequisites. No request was
made by this adoption, and the executed M1 STOP remains authoritative.
