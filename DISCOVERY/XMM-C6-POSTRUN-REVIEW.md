# C6 independent post-run receipt audit

September 12, 2026. **PASS for the recorded bounded MOS2 acquisition and
header-identity result; scientific compatibility and pixel support remain
unadjudicated.** The parent reports execution after freeze `d54ec04` and a
successful parent offline replay.

This audit read saved receipts, source/test/protocol and header-report hashes,
plus filesystem names/sizes. It did not open or hash a product's contents,
decompress it again, read any actual array, construct a new actual WCS or make
a network request. Consequently it independently verifies receipt integrity
and consistency, not a second product-content or numerical validation.

## Receipt closure and recorded operation

Independently computed [outcome](XMM-C6-2026-09-12-data/outcome.json) SHA-256:
`8cd766cd9ec4e2a54548248bd6b8aa0805c94678e1e066ba3c560713e03e0caa`.
It records `MOS2_MAP_RETAINED_HEADERS_ONLY`, worker exit zero, completed parent
assessment, one OK slot and `arrays_interpreted=false`.

Checks passed:

- 28 nonproduct artifact/dependency hash checks and seven additional
  source/test/protocol/prior-receipt bindings. Product entries were deliberately
  excluded from new content hashing; their hashes agree across the worker,
  request and outcome receipts and filesystem sizes match the recorded sizes.
- Exact eligible artifact-name closure, worker-start binding hash and exact
  request-slot identity. The request marker's elapsed time is approximately
  0.094 seconds, within the prospective limit.
- Header hash/size consistency and structural aggregate arithmetic. There is
  exactly one primary HDU and zero parser warning categories. The report's
  declared data-region bytes read is zero, consistent with the bound reader's
  seeking rather than image-value decoding.
- JSON accounting: 34,916 bytes before worker/outcome receipts, 36,091 before
  outcome and 37,762 total, below the 1-MiB budget. Reported worker/parent
  monitored peaks are 67,444,736 / 63,692,800 bytes, below the fixed cap.

The [HTTP receipt](XMM-C6-2026-09-12-data/http.json) records HTTP200 at the exact
frozen ESA URL and an unambiguous inline disposition with the required
`P0884250101M2S002EXPMAP8000.FTZ` basename. Content-Type is image/fits; no
Content-Length or Content-Encoding is recorded. Thus 410,115 is an observed
retained body size under the prospective local cap, **not a successfully
matched size advertisement**. No ETag or Last-Modified identity was invented.
The one-slot receipt and unchanged reviewed source support the one-GET,
no-redirect/no-retry execution contract; this audit did not repeat that GET.

## Product and header-identity result

The [request result](XMM-C6-2026-09-12-data/request-result.json) records actual
format `GZIP_WRAPPED_FITS` and successful worker gzip CRC/EOF verification.
The raw entity is 410,115 bytes and its expanded file is 1,707,840 bytes,
both below their fixed limits. Header replay is not an additional gzip
decompression; this audit relies on the bound successful worker path and the
parent's reported product replay for that integrity claim.

| Recorded artifact | SHA-256 |
| --- | --- |
| Raw entity | `1db2fad3238cabb71157ac4f39ea10949f7c42842788a363e01f272648721205` |
| Expanded FITS | `a92d6907db2e9e4def19b124c19da6056d20a06e3465da7103a23fb5dcd36983` |
| Header report | `6cc4bfa1b08d93a31f8f89ba49274511e9ef0052634d64cb1235fdde739e2285` |

The safe identity summary is observation 0884250101, EMOS2, S002, primary
BITPIX -32, shape 648 by 648. This shape was observed after acquisition,
not assumed from pn/MOS1. Its arithmetic is consistent:

    648 × 648 × 4 = 1,679,616 declared image bytes
    25,920 header bytes + 1,681,920 padded image span = 1,707,840 file bytes

The result explicitly retains `wcs_and_scientific_compatibility=NOT_ADJUDICATED`.
The source/test/protocol bindings match the [accepted preflight](XMM-C6-REVIEW.md):
source `4ed7d10e229a38f4356f34386ee70e510915049c1468b006841908ecaf1cbfdb`,
tests `f46468825846e68649ccb48d2592163b0151476de6a49609f315af2141c31ccf`,
protocol `464a53d8ce733ce080a1962f2245a80a11a7593b1c5c1045c9f70898c7cbd9cb`.

## Independent scientific limits

The documented alternate returned this specific product successfully. That
does not retrospectively invalidate the preserved original C3 HEASARC HEAD404
STOP or identify its cause. The bound C3 outcome/failed MOS2 HTTP and result
receipts remain unchanged. C5's outcome hash and zero sampled MOS1 source
support remain unchanged; a newly retained MOS2 file is not a MOS1 repair.

No scientific array has been interpreted in C6. Opaque transport, expansion,
hashing and header scanning nevertheless involve real I/O; scientific decode
count zero does not mean zero bytes accessed. Full header cards remain local;
this report publishes no absolute pointing or WCS values.

The next eligible task is header compatibility adjudication: primary WCS/frame,
units/scaling, processing provenance and band/FLAG/GTI/exposure semantics.
Matching observation/instrument/exposure, basename and dimensions cannot alone
establish compatibility with the strict proposed photon cuts. If that review
supports a separately frozen fixed-region value stage, it may determine
static MOS2 map support; acquisition itself says nothing about positivity,
per-bin live exposure, simultaneous camera coverage, source-list contamination
or detector artifacts.

The pn-plus-at-least-one-MOS recovery requirement and all original controls
remain in force. This is neither multi-camera control recovery nor discovery,
and authorizes no recentering, changed apertures, replacement controls,
unbounded archive requests or unknown-source search.
