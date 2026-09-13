# C8 postrun receipt and aggregate audit

**ACCEPTED_WITHIN_SOURCE_GEOMETRY_SCREEN_SCOPE.** This is an independent
recalculation of saved receipt/hash/aggregate consistency by the wrapper author,
not another numerical source-list replay or a claim of independent scientific
replication. The separate pre-execution reviewers assessed the reader, geometry
core and wrapper. Parent reports execution after freeze `860115a`.

No source-list product, map, EVENTS payload or numerical reader was opened or
executed during this audit. Only source/test/protocol files, saved stage JSON,
and C1 outcome/slot/header receipt bytes were inspected or hashed. All executed
files remain unchanged. The product hash was checked against its bound C1
receipt, **not** independently rehashed from the scientific product here.

## Identity and closure checks

All **12 dependency hashes** match the frozen run-start manifest, including
C1 source/tests, selected-span reader/tests, geometry core/tests, C5 centre
source, counts-definition document, bounded worker helper and structural
reader plus both test files. Wrapper source/tests and protocol/snapshot hashes
also match. Current Python executable/version, NumPy/Astropy versions and
output directory match the recorded execution binding.

The C5 and C8 `centres()` ASTs are identical without executing either function.
All 266 packed column offsets are contiguous and sum to 1,131 bytes. The nine
selected names/formats/units/offsets/widths and absent selected nulls match the
contract. Manifest rows/data offset/selected bytes/read count remain
151 / 77,760 / 7,852 / 755.

There are exactly six stage JSON files, no nested or extra JSON. All six
outcome-bound artifact hashes and five worker-bound artifact hashes verify;
each includes the appropriate snapshot/earlier receipts, without circular
self-hashing. Worker start binds the exact run-start hash. The sole table
marker has elapsed time 0.0470000000022992 seconds, within the 60-second bound.
This marker time is not an independently measured total runtime.

| Artifact | SHA-256 |
| --- | --- |
| outcome.json | `82cd6df3d673c86059494e9d38a3bfd1312ee9ce8b19301873309dfc995ad16e` |
| run-start.json | `a9ec6186835d402a41b2483518be45b43a47cd218cf4bdc37c556320ed7d2e6a` |
| table-result.json | `719afedaca93f82f85a5e7003564bab7f02bf1c23065d871d80b3bae53f16cfa` |
| wrapper source | `bd76ab70fb36ca2ea9c350401ab36991baa8fd30b3bf160c546c788a536ad0e3` |
| wrapper tests | `0bd5ba02add739318553de6029147e79d625b8dcde8c5180b3674c9088370733` |
| frozen protocol snapshot | `9b4a86517fdafcccf16c1004808a87a457c4c05b63b51f6e9da5163675330c14` |

The first audit assertion incorrectly restricted dependencies to `.py`; the
bound counts-definition `.md` correctly caused that assertion to fail. The
inspection-only assertion was corrected to admit `.py` and `.md`, then all
hash checks passed. This was an audit-harness assumption, not a changed stage
artifact, failed scientific gate or rerun of the numerical experiment.

## Accounting and resources

Worker return code is 0, parent assessment is true, table status is OK, and
worker/outcome/summary agree on `SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`.
Worker table and parent-validation counters separately report:

- 7,852 returned and decoded selected bytes;
- 755 attempted/completed reads and decoded spans;
- 151 completed rows;
- COMPLETE status/phase and both current-completion-unknown flags false.

These receipts directly account for **15,704 selected bytes across worker and
parent**. Parent additionally reports exactly one explicit successful numerical
replay, adding 7,852, for **23,556 selected bytes over three passes**. That replay
prints its own additional-pass counters rather than adding an immutable stage
JSON file. This audit did not rerun it and adds **zero** selected bytes. Opaque
product-hash and structural-header I/O are not included in the selected-byte
figures.

Worker/parent peak receipts are **69,726,208 / 70,422,528 bytes**, below the
268,435,456-byte monitored ceiling. No new compressed/expanded products were
created. The resource snapshots reconcile exactly:

| JSON accounting point | Bytes |
| --- | ---: |
| Before worker-result/outcome | 57,060 |
| Including worker-result, excluding outcome | 58,181 |
| Final six JSON files, including outcome | **60,118** |

Final file sizes are run-start 48,956; table-result 7,955; table-start 58;
worker-start 91; worker-result 1,121; outcome 1,937 bytes. All remain within
the 1,048,576-byte aggregate budget. Snapshot Markdown is not JSON and is
separately hash-bound. Privacy flags remain false for photon/map interpretation
and persisted source coordinates/IDs. Summary content contains aggregates,
fixed labels and relative-distance/error statistics, not a source catalogue.

## Exact aggregate findings

All 151 original and corrected positions are reported valid. Identity invalid
rows and all duplicate-ID counts are zero. There is **one** corrected-position
match under the unchanged 5-arcsec rule. Its original-position separation is
**2.8441692831480774 arcsec**, within the unchanged 20-arcsec aperture. This is
a positional association and an original-position consistency diagnostic, not
a confidence probability or physical-identification proof.

The fixed label order, 151-row denominator and zero invalid-original count
appear in all five aperture and all five annulus records. Exactly the published
aperture exempts the associated control row. Annuli and negatives do not.

| Fixed region | Other centres <=20 arcsec | 30-arcsec disk/aperture contacts | Disk/annulus contacts |
| --- | ---: | ---: | ---: |
| published | 0 | 0 | 1 |
| north120 | 0 | 1 | 2 |
| east120 | 0 | 1 | 1 |
| south120 | 0 | 0 | 3 |
| west120 | 0 | 2 | 5 |

Every contact record's extent categories sum exactly to its row count. All
reported contacting rows fall in the finite-zero/point-model extent category;
none is categorized extended or invalid extent. That model category is not
evidence of zero PSF wings or negligible contaminating flux.

Each error/extent diagnostic retains its 151-row denominator. RADEC_ERR and
SYSERRCC each have 151 positive finite values, respectively spanning
0.34629032015800476–7.18759298324585 and
0.2703244984149933–0.42384302616119385 arcsec. No new error-dependent matching
radius was used. EP_EXTENT has 145 zero and six positive values. EP_EXT_ERR
has **145 nonfinite and six positive** values. Matching marginal counts do
not establish that the nonfinite errors and zero extents belong to the same
rows, nor identify why errors are nonfinite. No such explanation, substitution
or cleanliness inference is made.

## Scientific next constraint

The ambiguity-dependent association path is no longer blocked by this screen,
but calibrated extraction remains unvalidated. In particular, the published
background annulus and all four negative-region annuli have catalogue disk
contacts. The original draft's fixed exclusion union must therefore actually
be implemented before claiming its masked-background extraction; contact totals
do not supply the masked area or its overlap with positive map pixels. Do not
sum disk areas or multiply independent aggregate map/source-mask fractions.

A next separately frozen **descriptive** recorded-event screen may report raw
aperture and explicitly unmasked/possibly contaminated annulus counts while
that calculation remains pending. It must not call those calibrated
background-subtracted rates, clean controls or successful recovery. A later
masked-area stage needs the authorized source-position spans and map pixels
jointly; C8 deliberately created no hidden coordinate cache.

The stronger pn-plus-MOS comparison, at least two usable fixed negatives,
regional exposure/background scaling and detector-artifact checks remain
unchanged. No-contact flags alone cannot establish uncontaminated sky, and
this result is not a new discovery or a calibrated recovery result.
