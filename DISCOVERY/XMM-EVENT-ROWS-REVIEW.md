# EVENTS scalar decoder: independent pre-integration review

2026-09-12 label; reviewed 2026-09-13 UTC. Scope: pure decoder and synthetic tests only. No actual event buffers, product/header payloads, network requests, source edits or scientific selections were used in this review.

## Verdict

**GO for integration into a separately reviewed, bounded reader.** No remaining concrete blocker in the final pure-decoder implementation. This is not authorization to read real EVENTS or a verdict on event quality, exposure, instrument screening, recovery or discovery.

Reviewed identities:

- `xmm_event_rows.py`: `9a5b86117956f98e1dcabec197fd70bab148ed9bba93048793680b7b6c448f4c`.
- `test_xmm_event_rows.py`: `205752eb49855c029dadd99ae9961dd9a028091e23423f3c5386e0cba8b9aa3d`.

Both files were read completely in their final form. Independently ran all **16 authored tests**, PASS, and pinned Ruff, PASS. Files were rehashed after testing and matched the author's final candidate.

## Material finding resolved before integration

Initially, `decode_rows` accepted any constructible `EventSchema`. A frozen dataclass alone did not enforce builder-derived offsets, scalar types, row width or an immutable columns tuple. The author added `_validate_schema`, which reconstructs the declared schema through the strict builder and compares it before `np.frombuffer`. Its regression rejects forged offsets/formats/row widths, mutable column lists, boolean row counts and unaligned offsets. An independent failure probe also forbade `np.frombuffer` and confirmed a forged offset was rejected first, with zero completed conversion bytes.

The author also completed the planned optional in-place progress receipt: complete field conversions are counted before mask work; a currently failing conversion is distinctly unknown. This avoids representing a later allocation/mask failure as zero decoding.

## Independent numerical and failure evidence

Beyond the authored suite, used Python `struct` formats specified independently of the schema's derived offsets to generate **257 synthetic pn-format rows and 257 MOS-format rows**, seed 20260912. The tested packed row widths were 45 and 34 bytes. All nine selected decoded arrays exactly matched the independent expected values; signed FLAG values reinterpreted as uint32 matched `signed_value & 0xffffffff` for every row. The synthetic values exercised full signed integer ranges, unsigned byte values and varied finite doubles. These are fixture identities, not an audit of an actual camera header.

Independent injected failures at the third selected field verified:

- Native-copy failure retained 10 known completed bytes per one-row buffer (TIME and RAWX), named RAWY as the in-progress conversion, and marked its completion unknown.
- Mask failure after RAWY conversion retained 12 known completed bytes, phase MASKING and no unknown current conversion. No arbitrary exception text was copied into progress.

Also independently decoded exactly 10,000 synthetic rows: the permitted chunk boundary succeeded with 280,000 selected field bytes. The authored suite separately rejects oversized chunks, partial rows and row-range overflow; it covers null/nonfinite masks, camera-dependent declared nulls, scalar-width derivation, duplicate/invalid schema cards, cross-row offsets and read-only returned arrays.

## Correct boundaries and integration obligations

The builder derives packed offsets from all scalar columns, including unselected scalar widths, checks total row width and selected formats, and rejects unsupported vector/bit/variable-length layouts, scaling, dimensions and heaps. Integer FITS nulls remain values with separate masks; floating nonfinite values are also preserved and masked. No null sentinel is invented when a camera's header does not declare one.

TIME is decoded as float64; RAWX/RAWY/PI as signed int16; X/Y/FLAG as signed int32; PATTERN/CCDNR as unsigned bytes. Native-endian conversion precedes unsigned FLAG reinterpretation, preserving the high bit and all-bits-set cases. A negative signed FLAG is not an invalid numerical value by itself. Callers must apply its null mask and their independently fixed bit policy.

`row_valid` means only selected values are non-null and finite. It does **not** establish a valid CCD, detector window, calibrated coordinate, accepted PI/PATTERN/FLAG, GTI membership or usable exposure. Unit strings are retained, not converted or scientifically certified. The consuming stage must bind exact product/camera/header identity, offsets, rows and units before decoding, and supply the fixed scientific policy separately.

This function does no I/O. Supplied full-row buffers physically contain unselected bytes even though only 28 bytes per row are converted into selected fields. The reader must count **all returned row bytes**, not advertise a 28-byte-only read. It must enforce ordered one-time chunk consumption and total read budgets; the decoder's range checks alone do not prevent a caller from requesting the same valid row range twice.

The caller must pass a fresh empty progress dict when partial accounting is needed, preserve it on caught failures, and distinguish completed-field byte counts from unknown work in a failed current conversion. The in-memory dict cannot survive an unrecorded hard process termination by itself. No scientific row is returned as complete after a partial exception. Durable exclusive markers, deadline/peak bounds, complete row denominators, private-array handling and parent replay remain responsibilities of the new reader, not guarantees added by this pure core.

Returned arrays are marked read-only for normal consumers; this is not a security boundary against code deliberately modifying Python/NumPy internals. Coordinates and individual event values remain local working data and must not be serialized as public receipts. No additional prerequisite framework or scientific threshold change is recommended by this review.
