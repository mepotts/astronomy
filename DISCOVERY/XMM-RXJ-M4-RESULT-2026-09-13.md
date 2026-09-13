# RXJ M4: four metadata documents accounted, identity parsing incomplete

Executed once after freeze `d9e9571`, using the reviewed
[offline protocol](XMM-RXJ-M4-2026-09-13.md). Worker return code0, parent
assessment complete, runtime status
`FOUR_FIXED_METADATA_DOCUMENTS_ACCOUNTED_UNADJUDICATED`.
Root invoked exactly one explicit offline replay: PASS with the same status.
No request, archive extraction, linked resource or scientific array was read.
M3's `STOP_TAR_HTML_SIZE` remains unchanged; its nonzero trailer is quarantined.

## What the metadata establishes and does not establish

All four fixed slices were parsed and retained separately. All four parser
statuses are `METADATA_INCOMPLETE`: no in-page encoding declaration was found,
and the bytes decoded strictly as ASCII (`MISSING_ASCII_ONLY`). This is explicit
missing encoding evidence, not a silently inferred declaration.

| Role | Selected bytes per pass | Labelled identity result | Exposure rows | Relevant references |
| --- | ---: | --- | ---: | ---: |
| EP | 872917 | MISSING | 0 | 30 |
| OB | 48229 | CONFLICT_OR_INVALID; one unrecognized value | 93 | 3 |
| RG | 25265 | MISSING | 0 | 8 |
| OM | 86689 | MISSING | 0 | 5 |

The OB result does **not** contain two contradictory observation IDs. Its sole
selected identity value is unrecognized, and its retained normalized-value hash
`e7ac0786668e0ff0f02b62bd04f45ff636fd82db63b1104601c975dc005f3a67`
equals the independently computed hash of the synthetic punctuation `:`.
The current adjacent-pair parser can select a separator instead of a value in
a three-cell label/separator/value layout. That is a supported explanation to
investigate, not a new inspection of the underlying layout. No raw HTML was
reopened for this diagnosis, and the frozen parser/result was not repaired.
Observation-level processing/timing fields are similarly unrecognized. The
archive headers and explicit product references carry requested-observation
identity; they do not retroactively verify the page's labelled identity.

The OB exposure table retains93 rows, no duplicate instrument/exposure keys,
no row/header shape mismatches and no unjoinable keys. Instrument row counts:
EMOS1=1, EMOS2=1, EPN=14, OM=13, RGS1=32, RGS2=32. All93 comparison groups are
single-role/unmatched. Zero reported conflicting groups therefore does not
establish independent cross-document agreement. No exposure table was identified
in the other roles; this is not proof that those documents contain no such data.

## Three imaging exposure rows and observed event references

These are all OB rows labelled Imaging for the three EPIC cameras, not a
photon-selected subset. Each is scheduled Y, `PrimeFullWindow`, `Thin1`.

| Camera | Exposure | OB row | Displayed duration | Actual Start | Actual Stop |
| --- | --- | ---: | ---: | --- | --- |
| EMOS1 | S002 | 1 | 47021 | 2019-05-30T21:00:32 | 2019-05-31T10:04:13 |
| EMOS2 | S003 | 2 | 47007 | 2019-05-30T21:00:54 | 2019-05-31T10:04:21 |
| EPN | S001 | 4 | 45161 | 2019-05-30T21:26:14 | 2019-05-31T09:58:55 |

Duration units and timestamp timezone labels are absent from the recognized
headers. Values above remain as displayed, not relabelled live exposure or UTC.
Other offset/diagnostic/RGS/OM rows remain in the public receipt. This does not
prove geometric coverage, eligible negatives or usable per-bin exposure.

The EP document explicitly references these basenames:

- `P0851180501PNS001PIEVLI0000.FTZ`
- `P0851180501M1S002MIEVLI0000.FTZ`
- `P0851180501M2S003MIEVLI0000.FTZ`

These are observed names, not guesses based solely on naming conventions.
They agree with the three exposure IDs after the documented camera aliases.
They are not yet authenticated event headers, verified downloadable bytes or
confirmed complete inventory. A separately bounded exact-product header stage
could test identity directly; no new request follows automatically from M4.

## Execution and accounting

Each of the worker, parent and one explicit root replay completed all four
slots: exactly1,033,100 selected bytes per pass, or3,099,300 across these three
M4 passes. Each additionally read1,044,480 opaque hash bytes,2,048 header bytes
and8,192 tail bytes. Three-pass totals are3,133,440 opaque,6,144 header and24,576
tail bytes. These are separate I/O categories; do not combine them into a
claim that the full archive was scientifically interpreted. Subsequent root
and reviewer JSON reading is receipt interpretation, not another HTML pass.

Worker peak30,904,320 bytes; parent peak30,674,944 bytes, below256MiB. The saved
13 JSON receipts total97,636 bytes, below1MiB. Child output was empty. No private
HTML copies were created. The original ignored archive remains immutable.
Exact17 source/test/protocol/privacy/dependency files matched committed bytes
before execution; binding preparation did not open the archive.

Outcome SHA256:
`7a571f930679c4077c7a337292ffceadf19e99a71b819f79777e90a88da0cc05`.
See [outcome](XMM-RXJ-M4-2026-09-13-data/outcome.json),
[OB metadata](XMM-RXJ-M4-2026-09-13-data/slot-2-result.json),
[EP references](XMM-RXJ-M4-2026-09-13-data/slot-1-result.json),
[cross-document diagnostics](XMM-RXJ-M4-2026-09-13-data/comparison.json) and
[independent review](XMM-RXJ-M4-REVIEW.md).

No new source recovery, calibrated significance or discovery. The useful advance
is explicit candidate product identities and full-window metadata for all three
EPIC cameras, with identity-parser missingness preserved rather than concealed.
