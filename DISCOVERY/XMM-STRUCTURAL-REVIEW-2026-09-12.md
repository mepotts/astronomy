# XMM structural-only preflight review — 2026-09-12

**The counts-recovery draft is not ready to freeze.** The next useful result is
a small, hash-bound inventory of the actual selected PPS files, not a photon
light curve or an expanding ancillary-data campaign. The existing literature
does not resolve their headers, coverage or exposure semantics.

This review reads the [event-structure evidence](XMM-EVENT-STRUCTURE-2026-09-12.md),
[control evidence](XMM-CONTROL-EVIDENCE-2026-09-12.md),
[recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md) and earlier
[eligibility decision](XMM-EXOD-ELIGIBILITY-2026-09-12.md). It is a fresh
consistency review of my own draft, not a claim of independent authorship.
The initial review used no new web source, archive query, data download, code or
photon calculation. Its corrections were proposed without changing the draft;
the parent subsequently clarified the unfrozen draft's coverage/duty-cycle rule.
The separately dated reader review below adds synthetic tests and one primary
FITS reference. No real data were inspected in either review.

## Actual draft problems to fix

### 1. The proposed 90% live-coverage cut is ambiguous and potentially wrong

The draft mixes bin coverage with detector duty cycle. These are distinct:

    G_j = duration([bin_start,bin_end) ∩ valid time intervals)
    C_j = G_j / 200 s
    E_j = integrated effective exposure within those intervals
    D_j = E_j / G_j, when G_j > 0.

C measures missing/truncated wall time; D can include legitimate detector
readout/dead-time effects. Requiring E_j/200 ≥ 0.9 can reject an otherwise fully
observed bin merely because its valid instrument duty cycle is below that value.
Do **not** freeze the literal live-fraction rule. If a 90% wall-coverage rule is
retained, name it C explicitly; exposure normalization must still use the
correct E. This is a pre-data correction, not relaxation of a failed result.

The precise E integral is not yet known. The structure note describes frame
central times, integration lengths and effective fractions; these fields must
be mapped without multiplying a duty correction twice. Standard per-CCD GTIs,
additional time-subspace restrictions and flare-screening GTIs are not
interchangeable. The warning about combined-camera FRACEXP exceeding one does
not justify accepting that range in a different per-CCD quantity.

### 2. One area ratio and one exposure per aperture need justification

The draft's `S/eS − (AS/AB) B/eB` is descriptive, not a generally valid correction
for a region spanning differently exposed CCDs, changing masks or variable
coverage. A fixed area ratio cannot repair a time-varying valid footprint. Nor
is area-averaged exposure automatically the exposure of a point source whose
PSF intersects a gap or moves with attitude.

The minimal later implementation should either establish fixed valid geometry
and the applicable region exposure, or specify a justified subregion/CCD
integration. If neither is supported, report geometry/exposure incomplete.
Do not infer a bad pixel, exposed area or point-source aperture throughput from
absence of events. Fixed radii are proposed choices, not calibrated encircled
energy fractions; no scientific reason has been established to alter them now.

### 3. Background non-detection cannot validate the source statistic

The conditional binomial expression in the draft is correct for two disjoint
Poisson samples with a common **total aperture rate** and known exposure ratio.
It is not an exact test of a constant astrophysical source in a variable
background. A non-significant background comparison may simply have insufficient
power. Geometry and camera agreement help diagnose this, but do not supply a
missing joint source/background null model.

Keep that statistic as a restricted recovery diagnostic. If the final contract
requires calibrated source-variability significance under changing background,
the draft is insufficient; that would require a different prospectively tested
statistical model, not wording that promotes its p-values.

### 4. Several bookkeeping choices still need precise meanings

- Multiple pn exposures: “pn TSTART” is ambiguous until an exact selected
  exposure/anchor is specified. Do not concatenate gaps or choose the earliest
  surviving photon. Record all exposure IDs, including unsupported ones.
- The draft counts five aperture tests per camera/bin in M, but also computes
  five background tests. State that its Bonferroni family covers only aperture
  positives; if claiming family control over both families, count both. A
  background veto is not itself another positive source detection.
- “Unknown valid source radius” is not a reproducible geometry rule. Replace it
  with concrete schema/overlap criteria in the final contract; the proposed
  30-arcsec exclusion is not proof of absent PSF-wing contamination.
- “Exactly two episodes” and the broad separation interval are morphology
  checks proposed from published approximate behavior, not measured sensitivity
  or event-time ground truth. Extra episodes mean failed/incomplete recovery
  under that contract, not automatic evidence of an instrumental false positive.

## Smallest structural-only acquisition report

After the parent verifies exact public product identities and size caps, inspect
only the selected control's immutable event files and observation source-list
product. Start with what is already embedded; do not fetch an all-products
bundle merely because documentation mentions optional ancillary files.

The report needs one file receipt and one compact table per selected camera:

| Item | Minimum retained evidence | What it establishes |
|---|---|---|
| Transport/container | Exact selected URL/product/exposure; compressed bytes/hash; bounded expanded bytes/hash; gzip completion/CRC; worker outcome | Byte identity and successful bounded transport, not scientific calibration |
| FITS inventory | HDU index, EXTNAME/EXTVER, type, header, table row count, column names/types/units/dimensions; structural validation outcome | Actual PPS schema rather than an assumed task-output layout |
| Identity | Observation, camera, exposure, mode/filter, processing/calibration identifiers, filename-to-header agreement | Which documented mode/product contract can apply |
| Time | Relevant extension TIMEUNIT/TIMESYS/MJDREF or split reference/TIMEZERO/TSTART/TSTOP and correction indicators, with conflicts recorded | Whether a single time-coordinate mapping can be specified |
| Spatial coordinates | Actual event-column WCS keywords, axis units/projection/reference/index conventions; detector/CCD columns and window metadata | Whether the published sky position can later be mapped without a guessed scale or axis shift |
| Coverage/exposure | Names and schemas of each CCD's exposure, standard GTI, extra GTI/data-subspace, bad-pixel and discarded-row information; explicit linkage keys | Whether live-time and mask integration are implementable from these files |
| Source list | Schema, coordinate conventions and available source/extent/region metadata | Whether a later deterministic contamination/geometry rule can be specified |

Do not access EVENTS columns, PI distributions, source/background event counts,
light curves, images or candidate peaks in this structural stage. Event-table
row counts are file-structure metadata, not aperture photon measurements.
Headers and schema alone also do not establish that GTI rows are sorted, finite,
nonoverlapping or within exposure bounds, or that effective-exposure values are
valid. Explicitly report those content checks as **not performed**. If numeric
GTI/exposure/mask contents are needed before the counts contract, ask for a
separately scoped metadata-content inspection rather than quietly reading them
under a header-only promise.

The same distinction applies to WCS. Presence of keywords is not a verified
transformation; a sky/pixel round-trip can prove internal invertibility but not
absolute astrometry or correct detector coverage. Binary-table WCS is not
automatically an image-header WCS, and column numbering must follow the actual
table. Missing/contradictory WCS is a named unresolved item, not permission to
substitute the documented 0.05-arcsec scale alone.

## Bounded decisions after that report

- `STRUCTURE_MAPPED_COUNTS_NOT_AUTHORIZED`: selected file identities and
  supported schemas are understood well enough to specify the next stage;
  list all untested content-level and geometry assumptions.
- `STOP_STRUCTURE_AMBIGUOUS`: a required time/WCS/CCD/GTI/quality-field mapping
  is missing or contradictory; identify the exact header/column or document
  needed, not a general request for more data.
- `STOP_PRODUCT_OR_RESOURCE`: transport, decompression, identity or size/runtime
  verification failed. Preserve partial data and receipts; no silent retry or
  replacement product.

None means exposure coverage, stable background, useful sensitivity, recovered
QPE, calibrated false-alarm rate, source localization or discovery. Do not
claim raw ODFs, SAS installation or a large calibration download are necessary
merely because an optional PPS extension is absent. First identify the smallest
specific missing input and whether the restricted control calculation truly
needs it. This keeps the next work a concrete structural feasibility check,
not another framework-building exercise.

## Header-reader review checkpoint — 2026-09-12, before real files

Independently read the complete initial `xmm_structure.py` and its six author
tests. The small design is appropriate for a later bounded inventory: explicit
2880-byte reads, a 64-block per-header cap, 128-HDU cap, actual/file-size check,
2-GiB size cap, Astropy header parsing and size calculation, followed by seeks
over declared payloads. It does not use HDU `.data`, photon arrays, hashing or
network access. External wall-time/memory limits remain the acquisition
driver's responsibility; no new transport layer is needed here.

The new [independent tests](test_xmm_structure_review.py) initially produced two
passing checks and four failing rejection checks. All fixtures are synthetic:

| Check | Initial observed result | Meaning |
|---|---|---|
| Valid primary image, binary table, then image | PASS: only the three header blocks read; intervening arrays skipped | Concrete guard against accidentally reading well-declared arrays |
| Missing END in the table header | Scanner attempts a guarded payload read before termination | Unknown bytes can be consumed during malformed-header scanning |
| BINTABLE BITPIX=16 | Incorrectly accepted | Type-specific layout check needed |
| BINTABLE GCOUNT=2 | Incorrectly accepted | General nonnegative/group-size checks are insufficient |
| BINTABLE PCOUNT absent | Incorrectly defaulted/accepted | Mandatory extension metadata cannot be inferred from a default |
| BINTABLE TFORM1 absent | Incorrectly accepted | A declared row byte span is not a validated column schema |

Binary tables require their fixed mandatory keyword sequence, BITPIX=8,
NAXIS=2, GCOUNT=1, PCOUNT and TFIELDS, with required TFORM definitions.
[NASA-hosted FITS standard §7.3, Table 7.5](https://fits.gsfc.nasa.gov/standard30/htmlfiles/fits_standard3000064.html).
This is a layout reference, not verification of any actual PPS file.

The parent accepted these preflight findings and is correcting the reader.
Prefer a narrow explicit supported-HDU contract to implementing a custom
general FITS validator. In particular, rejecting unsupported ASCII tables is
more honest than accepting their layout with unverified binary assumptions.
If validating binary row widths with Astropy's column-format machinery, test
packed-bit X and variable-array P/Q descriptor formats explicitly; a pointed-to
array's size is not its descriptor's row width.

The initial unconditional `data_region_bytes_read: 0` must not be presented as
proof that arbitrary malformed bytes contain no photon payload. The defensible
statement is **no reads inside payload spans declared by accepted headers**.
A damaged/misleading header can hide the true boundary; malformed-header scans
may read unknown blocks up to the cap before STOP. Likewise, seeking over a
declared payload cannot verify that its bytes really match the schema, checksum
or column contents. The acquisition report must disclose these limits.

The missing-END synthetic test deliberately records this limitation rather
than requiring impossible classification of untrusted bytes. An earlier safe
STOP is also acceptable. This checkpoint does not authorize real-file execution;
the outstanding four malformed-header cases require resolution or a clearly
narrowed claim before the reader is used in the acquisition contract.

### Resolved preflight checkpoint — 2026-09-12

Read the complete amended reader. All four malformed binary-table cases now
STOP; row widths are checked through Astropy's format parser, ASCII extensions
are explicitly unsupported, and the result field is now
`declared_data_region_bytes_read`. The function docstring discloses the bounded
malformed-header scan limitation. The initial failure checkpoint above remains
part of the audit history.

Independently ran **15/15 synthetic tests PASS**: six author tests and nine
reviewer tests. Added checks cover a packed `14X` field, `1PE`/`1QD` variable-array
descriptors, character/complex formats, an intervening heap's seek-only skip,
row-width mismatch rejection and unsupported ASCII rejection. Header guards
also verify separate image/table payloads are skipped. Pinned Ruff 0.16.5 passes.
The missing-END test preserves the disclosed limitation, not a stronger
zero-payload-read guarantee.

Accepted as a **bounded declared-header inventory reader** for incorporation in
a separately reviewed acquisition contract, not as complete FITS conformance
validation. It still does not validate all mandatory-card ordering, heap
descriptor contents, header/data checksums, semantic WCS, GTI/exposure values,
or scientific correctness. These omissions do not require a new framework;
report them, and perform only the specifically authorized downstream checks.

Reviewed source SHA-256:
`96d9497dbdd45d2561fc0bbb27a0c11d6fbad91cd42c0b14191378dd9fd7fa63`.
Reviewer-test SHA-256:
`a062ddea63b2c8364395ed61ead99e2cc12031bcec3065aa24ca61dbee1d6b10`.
No real data, photon arrays or network acquisition were accessed by these tests.
