# Independent selected source-column reader review

September 12, 2026 label. Synthetic-only review of `xmm_source_rows.py` and
`test_xmm_source_rows.py`, against the previously reviewed implementation plan.
No actual product, source-list, map, event or other scientific array was read;
no network operation occurred. This review concerns only the selected-span
reader, not the future C8 worker, its execution authority or any science result.

## Schema and read boundary

The implementation derives widths and cumulative offsets from all 266 declared
fixed-width columns. Repeat counts contribute their full byte width, including
opaque strings/logicals that are never interpreted. It requires the declared
1,131-byte row, 151 rows, zero heap and nine exact selected names, scalar types,
units and offsets. Repeated schema cards, duplicate column names, unsupported
variable-length/bit-array forms, extra axes, scaling/dimension/heap variants
and selected-column null declarations are rejected. An unselected integer null
may be retained as schema metadata without decoding its field.

The reader revalidates a supplied immutable schema rather than trusting a
forged offset. It reads only these five spans per row at
`77760 + 1131 * row`: `(0,4)`, `(20,20)`, `(596,8)`, `(1088,16)` and `(1120,4)`.
The resulting **755 reads, 52 bytes per row, 7,852 bytes per complete pass**
do not include intervening columns, entire-row fetches or table padding.
There is no FITS array loader, photometric interpretation or hidden retry.

Signed big-endian int32 IDs remain Python integers. Float32/float64 scientific
values, including negative values and NaN/Infinity, are retained for the
separately reviewed geometry core to classify; invalid rows are not removed
here. Returned tuples are private local working data, not public artifacts.

## Verification and failure accounting

All **11 author synthetic tests** independently pass. Their guarded stream
asserts every requested offset and size, and selected output agrees with an
independent NumPy structured-dtype oracle, including endian types and row
stride. Tests also cover schema mutations, repeats, integer-null semantics,
nonfinite values, full signed-ID endpoints, schema forgery, buffered-stream
rejection, seek errors, checkpoint stops and fresh accounting requirements.

Additional reviewer inline experiments, not committed unittest methods:

- **755 truncation cases**, one for each possible selected span, each returning
  exactly one byte less than requested. Every case preserves the full prefix
  of returned bytes, only fully decoded prior spans, correct completed-row
  count and current row/span. No read beyond the failed span occurs. Known
  short returns do not become unknown-completion flags or zero-filled rows.
- **Five storage failures**, one at each span of the third row, confirm decoded
  counters advance before storage, include the just-decoded span, and do not
  incorrectly mark the incomplete row completed. Temporary process-local mocks
  were restored and no source was changed by the reviewer.

Checkpoint or seek failure records no extra read. A read exception marks its
completion unknown; an unpack exception marks decoding completion unknown.
Known returned byte counts are retained separately from successfully decoded
bytes. Stored values are not exposed in the accounting dictionary. This is
caught-exception accounting, not proof that a receipt survives process death.

## Caller preconditions and limits

The pure function rejects common buffered/text wrappers but intentionally
accepts a caller-guaranteed raw equivalent and synthetic `BytesIO`. It cannot
prove an arbitrary object's hidden I/O behavior. The real runtime must open
the exact bound file with `buffering=0` and must not replace the stream with
a buffering or read-ahead adapter. Resource checks and durable accounting
belong to that runtime. For the normal raw-file contract, a read cannot return
more than requested; a malicious custom stream is not an alternative scientific
input supported by this review.

PRIMARY/observation/product identity, header framing and declared data offset,
file size/hash, coordinate frame/equinox, POSCOROK/correction provenance and
the full selected-column acquisition contract remain caller checks. This
function validates table layout, not full FITS payload validity or scientific
field validity. It does not validate header framing, decode unselected logical
values, apply coordinate corrections or evaluate source association.

The caller must retain partial accounting on failure, avoid automatic retries,
sanitize exceptions, and never serialize the returned coordinate/ID tuples.
It must count each numerical replay as an additional selected-byte pass and
distinguish byte-only product hashing from selected-field interpretation.
Process interruption without a returned receipt remains unknown, not zero.

## Review disposition

**Scoped GO for the reader, not C8 execution.** No selected-span or accounting
correctness blocker was found. The reviewer identified a root-Ruff `TRY004`
exception-type issue in buffered-stream rejection. The author changed that
branch and its regression expectation from `ValueError` to `TypeError`; this
does not change accepted input or scientific behavior. Final independent
reruns pass all 11 tests and root Ruff 0.16.5.

| Artifact | Final SHA-256 |
| --- | --- |
| `xmm_source_rows.py` | `33acfedec1328cac1517abc703ee9644c653330648630edb8d96b6235562a927` |
| `test_xmm_source_rows.py` | `4fd4b13b5698c2d40a476d390b780b47cc8e899c2ad6fe39024d6cff9f0ef272` |

Hashes were independently recomputed after that repair. No reader source or
test was edited by the reviewer. The separately constructed C8 wrapper still
requires its own full review and synthetic failure-accounting tests.
