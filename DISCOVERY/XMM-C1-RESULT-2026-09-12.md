# XMM C1: four published-control products retained, headers only

**CONTROL_BUNDLE_RETAINED_HEADERS_ONLY. No discovery or burst recovery yet.**
The [reviewed C1 protocol](XMM-C1-2026-09-12.md), source and tests were frozen
in commit `c5d11de` before execution. Exactly four anonymous GETs completed,
all HTTP 200, with no retry, redirect or replacement. Response dates span
2026-09-12 23:49:22–23:49:46 GMT. Worker exit was zero; parent verification
and a separate read-only replay both accepted the same structural outcome.

| Fixed published-control input | Compressed bytes | Expanded bytes | HDUs | Declared main-table rows |
| --- | ---: | ---: | ---: | ---: |
| pn S003 | 109245605 | 219988800 | 64 | EVENTS: 2694388 |
| MOS1 S001 | 7643540 | 11707200 | 19 | EVENTS: 273441 |
| MOS2 S002 | 9972723 | 15194880 | 25 | EVENTS: 356129 |
| EPIC source list | 120581 | 250560 | 2 | SRCLIST: 151 |
| Total | 126982449 | 247141440 | 110 | — |

These row counts come from headers, not event selection or detection analysis.
Every compressed file matched its prior HEAD length and supplied ETag and
Last-Modified. Gzip completed with CRC/EOF verification. Expanded products and
full header reports were hash-bound and independently replayed by the parent.
The structural reader accessed 2067840 header bytes and skipped declared data
spans; no scientific array was interpreted. Its documented malformed-header
and incomplete FITS-conformance limitations remain in force.

Measured worker peak working set was **68190208 bytes**, parent peak 61431808,
both below the monitored 1000000000-byte ceiling. All expanded files were below
1 GiB individually and 2 GiB collectively. The largest header JSON was 1679959
bytes, below 2 MiB; pre-outcome aggregate JSON usage was 2186408 bytes, below
10 MiB. The run used the pinned 300-second worker deadline, not a new runtime
or package installation.

## What the actual headers establish

All three event products identify observation `0884250101` and the expected
camera/exposure. pn is PrimeFullWindow; MOS1 and MOS2 are PrimePartialW3, all
Thin1 imaging. The event headers share TT seconds, MJDREF 50814.0, TIMEZERO 0,
TIMEREF LOCAL, TASSIGN SATELLITE and CLOCKAPP true. Creator strings identify
`xmmsas_20241108_1150-21.0.0`; this is not inferred from a directory date.

pn retains twelve sets of exposure, bad-pixel, discarded-line and standard-GTI
extensions. Its exposure tables have TIME/FRACEXP columns and a TIMEDEL header
value; numeric frame contents and the exact integration convention are not yet
validated. MOS exposure tables include TIME/TIMEDEL/FRACEXP columns. MOS1 has
five retained CCD sets (1,2,4,5,7), MOS2 seven. Neither absent CCD extensions nor
header LIVETIME automatically establish aperture coverage or per-bin exposure.
Actual MOS PI units are labelled CHAN, unlike pn's eV. Parent follow-up to the
header review establishes the standard numeric-eV convention from the actual
PI column comments and explicit official MOS selection examples in
[HEASARC's imaging guide, section 7.2](https://heasarc.gsfc.nasa.gov/docs/xmm/abc/node9.html).
The [unit-resolution note](XMM-MOS-PI-UNITS-2026-09-12.md) records that decision.
This permits the conventional numerical energy cut in a prospective protocol;
it does not independently validate physical calibration. pn CCDID alone is
not unique across quadrants. Actual metadata remain essential.
The [independent header adjudication](XMM-C1-HEADER-REVIEW.md) records exact
CCD-to-GTI alternatives and distinguishes rounded pn frame-time metadata from
its exposure-entry interval. The non-coordinate summary helper was corrected
to include numeric-prefix DSS keys; no executed C1 code or data was changed.

The [counts-feasibility assessment](XMM-COUNTS-FEASIBILITY-2026-09-12.md)
supports a conditional same-aperture timing test without requiring absolute
flux calibration first. Next: resolve the actual per-CCD relative exposure,
GTI associations and stable source/background geometry with a separately
bounded ancillary-metadata inspection, then freeze and run the counts test.
Do not read EVENTS or optimize apertures while resolving those choices.

## Provenance and limits

Outcome SHA-256:
`c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc`.
The [pre-execution review](XMM-C1-REVIEW.md) records all final code/test hashes,
15 acquisition tests and 15 structural tests. Root separately ran the full
22-test XMM utility suite and Ruff. GitHub CI now includes XMM synthetic checks;
the real retained-input provenance test explicitly skips without the local-only
C0d summary. CI is not a reproduction of the public-data download.

Raw compressed/expanded products and full header cards remain immutable,
local and Git-ignored. Public receipts retain hashes/lengths, not coordinates
or observer contacts. Full replay needs these local inputs. No raw products,
scientific counts, candidate coordinates, publication or submission were sent.
Root's integration check confirms all twelve raw/header files are ignored and
none is in the index; the original C0d summary is likewise untracked. The
[independent post-run audit](XMM-C1-POSTRUN-AUDIT.md) verifies all 32 outcome
artifact hashes and all 33 stage files unchanged, with final JSON usage of
2191924 bytes. It verifies the recorded gzip receipts and retained hashes,
not a second independent decompression.
The preceding C0d metadata STOP remains unchanged; this independent stage does
not retroactively turn it into success.
