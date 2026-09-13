# Synthetic-only event-row decoder

`xmm_event_rows.py` is a pure packed-scalar decoder, not a photon experiment.
It performs no I/O, WCS transform, GTI selection, energy/FLAG filtering, source
search, count binning or significance calculation. Actual event arrays remain
unread. All three retained header schemas have been constructed metadata-only.

Call `build_schema(header_items, data_offset)` with full keyword/value pairs
from a separately verified EVENTS header so relevant duplicate cards remain
detectable. The frozen schema derives every packed offset from scalar TFORMs,
checks the declared row width and selected field formats, and rejects heaps,
vectors/bit arrays, scaling and dimension metadata. Do not hand-construct or
modify an EventSchema; that is outside the supported contract. Defensive
reconstruction also rejects forged offsets, field formats and layout before
buffer conversion. A later bounded
wrapper must bind exact per-camera schema/product/header hashes and file bounds.

Call `decode_rows(raw_bytes, schema, row_start=..., accounting=progress)` for
an immutable byte buffer of complete rows, at most10000 per call. Use a fresh
empty caller-owned progress dict for each chunk. Returned arrays cover TIME,
RAWX/Y,X/Y,PI,FLAG,PATTERN,CCDNR only; fields are native-endian read-only copies.
Signed32-bit FLAG and its unsigned bit view preserve identical bits. Null
sentinels and nonfinite values remain present, accompanied by separate masks.
`row_valid` means only finite/non-null selected fields: MOS PI=-32768,
PATTERN13 or CCDNR0 may pass this primitive when no matching null is declared.
That does not make them accepted scientific events.

Full-row input includes opaque unselected bytes. A pn row supplies45 bytes,
a MOS row34; selected conversions total28 bytes per complete row. Across the
retained3323958 event rows this would be142652840 opaque row bytes and93070824
selected-field bytes per complete pass. These are prospective bounds, not
measurements performed by this implementation.

Mutable progress records completed field conversions before mask work. If a
conversion fails, its current-field completion is explicitly unknown, while
prior completed fields remain counted. It does not claim zero conversion work
for a failed current field. Buffer bytes supplied are not a file-read receipt;
the caller must separately retain actual I/O counts, truncated rows and killed
passes. Hard termination can prevent persistence of in-memory progress. Public
outputs must exclude working arrays, coordinates and arbitrary exceptions.

Sixteen synthetic tests exercise independent stdlib-struct byte construction,
packed camera offsets, endianness, signed FLAG bits, camera-specific nulls,
readonly outputs, schema rejection, row/cap bounds, and partial mask/conversion
failure accounting and forged-schema rejection. Root has read source/tests;
[Independent review](XMM-EVENT-ROWS-REVIEW.md) passes all16 tests,514 additional
synthetic pn/MOS rows and partial-conversion/schema-failure probes. The root
suite passes all88 current XMM core tests. This core enables a future explicitly frozen
descriptive photon screen; it cannot establish region coverage or satisfy the
unchanged stronger recovery gate by itself.
