# RXJ M4 next: authenticate three observed event products from their headers

Decision proposal, 2026-09-13. No acquisition is authorized by this note. This
review read only M4 safe JSON, local public notes and primary client documentation;
it did not reopen the archive or HTML, query an archive, or read scientific arrays.

## Decision and retained evidence

Proceed, after a separate frozen protocol and review, to **three exactly named
event-product GETs followed by header-only validation**. No further HTML repair or
replay is a prerequisite. A reference is sufficient to define a narrow request;
the returned FITS identity, rather than the incomplete HTML identity, must then
authenticate the observation and exposure. This does not retrospectively pass M4
identity checks or any earlier STOP.

M4 outcome is `FOUR_FIXED_METADATA_DOCUMENTS_ACCOUNTED_UNADJUDICATED`, SHA256
`7a571f930679c4077c7a337292ffceadf19e99a71b819f79777e90a88da0cc05`.
All four roles are `METADATA_INCOMPLETE`, with missing declarations and
`MISSING_ASCII_ONLY` decoding evidence. EP/RG/OM identities are missing; OB has
one unrecognized labelled candidate. Its safe candidate hash equals the SHA256
of the synthetic one-character string `:`. This is only a normalized punctuation
comparison: it establishes neither an adjacent value nor observation identity.

EP explicitly records these three basenames:

| Camera | Observed product | OB metadata cross-check, not authenticated FITS identity |
| --- | --- | --- |
| EPN | `P0851180501PNS001PIEVLI0000.FTZ` | S001, PrimeFullWindow, Imaging, Thin1 |
| EMOS1 | `P0851180501M1S002MIEVLI0000.FTZ` | S002, PrimeFullWindow, Imaging, Thin1 |
| EMOS2 | `P0851180501M2S003MIEVLI0000.FTZ` | S003, PrimeFullWindow, Imaging, Thin1 |

OB accounts 93 exposure rows, not just these three. Their duration strings are
45161, 47021 and 47007 respectively, with units missing; they are not certified
live exposures. EP result SHA256 is
`dffd27867686a5226205a0a25c5743c6f9b95ab150e00b86dc18f460859c3615`;
OB result SHA256 is
`3809cc5a1c7524433d018bbcbf9ee64af1dc10ad198bc6b3b6cec2ced75390b5`.

## Documented selector, not an invented filename parameter

The [official ESA astroquery API](https://astroquery.readthedocs.io/en/stable/api/astroquery.esa.xmm_newton.XMMNewtonClass.html)
documents the AIO endpoint and PPS filters: instrument, scheduled/unscheduled
flag, three-digit exposure, product type, subset, source number and extension.
Its `filename` argument controls the local destination, not remote product
selection. The [official client source](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html)
constructs `obsno` plus those filters and parses those fields from PPS filenames.
The following requests instantiate that documented mapping using only the
already observed basenames:

1. `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=PN&expflag=S&expno=001&name=PIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`
2. `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=M1&expflag=S&expno=002&name=MIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`
3. `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=M2&expflag=S&expno=003&name=MIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`

Availability, response size and packaging have not been verified. C3d's successful
raw-named attitude request demonstrates a useful implementation precedent, not
a guarantee for these products. The client convenience download path performs
a HEAD; do not invoke it and accidentally add requests to this three-GET contract.

## Recommended finite acquisition boundary

These are proposed resource limits, not estimates of the files' actual sizes:

- Exactly three anonymous GET slots in the order above, one attempt each; stop
  at first failure and mark remaining slots unattempted. No HEAD, redirects,
  retries, environment credentials, broad bundles or fallback selectors.
- Require HTTP 200, exact final URL, identity content encoding, compatible
  FITS/octet-stream/gzip media type and an unambiguous disposition basename equal
  to the slot's observed name before reading a body. Missing Content-Length is
  allowed under the local cap; a supplied positive decimal length must fit the
  budget and equal the final byte count. No prior validators exist to invent.
- Raw cap 256 MiB per file and 512 MiB aggregate, with one overflow byte detected
  and partials preserved. Expanded cap 1 GiB per file and 2 GiB aggregate. These
  bounded allowances accommodate event products without presuming the previous
  observation's sizes. Refuse insufficient free space before launch; reserve at
  least 3 GiB for retained inputs plus receipts, with additional working margin.
- A 300-second tree-aware worker deadline for the batch, 5/15-second connection/
  read timeouts, at most 1 MiB chunks and monitored peak memory below 500,000,000
  bytes. JSON receipts at most 10 MiB aggregate; full header report at most 2 MiB
  per product. Parent validation gets a separately explicit local-only budget.
- Dispatch by actual magic to gzip (CRC and complete EOF) or raw FITS. No TAR
  extraction or implicit acceptance of a differently packaged entity. A package
  response is a preserved format STOP, not authority to apply M3's observation-
  specific trailer exception to new bytes.
- Hash raw/expanded inputs and retain full cards privately in ignored directories.
  Public receipts contain only allowlisted non-coordinate metadata, bytes,
  hashes and safe error codes. Header parsing seeks over payloads: no EVENTS,
  GTI, BADPIX, exposure, calibration-index or image value decoding.

## What the headers must settle, and what remains later

Use the pinned structural reader to verify complete FITS structure and collect
the primary/EVENTS observation, instrument and exposure identities. The accepted
identities must be 0851180501 and the corresponding EPN/S001, EMOS1/S002 and
EMOS2/S003, using actual documented cards rather than a filename-only inference.
Record actual observing mode/filter and any conflict with OB's three rows.
Inventory the EVENTS scalar schema, null/scaling/unit cards, time reference,
GTI/exposure/bad-pixel extensions and any CALINDEX column schema. Do not copy
the old observation's row counts, offsets or geometry into an acceptance rule.
Missing or contradictory essential identity is a STOP; other missing metadata
is explicitly unestablished, not silently defaulted to FullWindow or a camera.

The strongest success label is `RXJ_EVENT_PRODUCTS_RETAINED_HEADERS_ONLY`.
It does not establish window/bad-pixel validity for an aperture, time-dependent
acceptance, clean negatives, event counts or recovery. If CALINDEX exists, a
separate small, allowlisted row-read proposal can identify the required calibration
constituents; it is not necessary to deploy SAS or download a calibration mirror
before this header inventory. Preserve the pn-plus-MOS and fixed-negative gates;
resolve source-specific geometry and timing prerequisites before photons, as in
[the geometry access note](XMM-RXJ-GEOMETRY-ACCESS-NOTE-2026-09-13.md).

## Parent disposition

Root read the complete note and independently checked the cited client API and
source, including selector construction, filename-field positions and its HEAD
request. Adopt the exact three-product, header-only direction: returned product
headers must establish identity directly, with no M4 repair or additional HTML
pass required. The proposed budgets still require a tested runtime/resource
contract and independent review before any GET. No CALINDEX or scientific array
values are included in that header-only scope. Preserve all prior outcomes and
the original geometry/background/control requirements.
