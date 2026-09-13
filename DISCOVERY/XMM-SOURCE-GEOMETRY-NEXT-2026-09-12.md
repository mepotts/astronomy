# XMM source-list geometry: smallest next read

Status: **METADATA_ONLY_PROPOSAL_NOT_EXECUTED**. Observation `0884250101`,
published control only. This note inspected retained header JSON and receipts,
not source-list rows, event values, images or photon counts. No product request,
coordinate query or new source selection was made. Numerical matching choices
below are prospective engineering choices for parent review, not measured
properties of this field.

## Decision

Read nine geometry/identity columns from all 151 existing EPIC source-list
rows, once under a separately frozen contract. Use a fixed **5-arcsec** absolute
position association to identify the published control; retain zero/multiple
matches rather than choosing the nearest or brightest. Use the original
image-coordinate positions for fixed **30-arcsec** catalogue exclusion disks.
Keep the published source centre, four fixed negative centres, 20-arcsec
apertures and 60–90-arcsec annuli unchanged.

This supplies a useful `SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`, not a calibrated
contamination or recovery verdict. The draft's stronger requirement concerning
unknown valid source radii is not automatically satisfied by this list.

## Retained product and exact schema

C1 slot 4 is `P0884250101EPX000OBSMLI0000.FTZ`, retained compressed size
120,581 bytes, expanded FITS size 250,560 bytes. Its two HDUs are PRIMARY and
SRCLIST. PRIMARY declares OBS_ID `0884250101`, INSTRUME `EPIC`, RADECSYS `FK5`
and EQUINOX `2000.0`. SRCLIST has 151 rows of 1,131 bytes, 266 columns,
PCOUNT 0 and GCOUNT 1. Its data starts at absolute byte offset **77,760**;
declared table payload is 170,781 bytes. There are no TSCAL, TZERO, TDIM or
THEAP cards. The nine selected columns have no TNULL cards.

Offsets below are zero-based within a row; FITS column numbers are one-based.
`J`, `E`, `D` mean signed big-endian int32, float32 and float64 respectively.

| Column number | Name | TFORM | Declared unit | Byte offset | Bytes |
| --- | --- | --- | --- | ---: | ---: |
| 1 | SRC_NUM | J | absent | 0 | 4 |
| 6 | RA | D | deg | 20 | 8 |
| 7 | DEC | D | deg | 28 | 8 |
| 8 | RADEC_ERR | E | arcsec | 36 | 4 |
| 146 | EP_EXTENT | E | image pixels | 596 | 4 |
| 147 | EP_EXT_ERR | E | image pixels | 600 | 4 |
| 261 | RA_CORR | D | deg | 1088 | 8 |
| 262 | DEC_CORR | D | deg | 1096 | 8 |
| 265 | SYSERRCC | E | arcsec | 1120 | 4 |

The list contains no `CUTRAD`, `SRC_RAD` or `EFF` column. Do not infer one
from flux, likelihood, MASKFRAC, detection flags or a map pixel size. Those
columns, and every count/rate/flux/hardness/variability field, are outside this
proposed read. The original detection merge's ML/BOX identifiers are unnecessary
for an all-row screen; the immutable row ordinal plus checked SRC_NUM suffice.

Five disjoint spans per row are sufficient: `(0,4)`, `(20,20)`, `(596,8)`,
`(1088,16)`, `(1120,4)`, each expressed as `(offset,length)`. At
`77760 + 1131 * row_index`, these total **52 bytes per row, 7,852 bytes per
measurement pass**, 755 reads. Use unbuffered bounded seeks/reads if that exact
payload-read boundary is adopted; do not load entire rows and then discard
photometric fields. Whole-file cryptographic hashing is a separate byte-only
provenance operation, not column interpretation.

Verified local receipt anchors:

- C1 outcome: `c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc`.
- Header JSON (88,191 bytes): `d19ede1f11156b75954e4fa5de3d29c7ce0222bcfa816dc64ed88d7be6c78c3e`.
- Expanded product hash recorded by C1: `7ee2302307c5336d2e4699c4997e711eda197483f6bec9a62598c0490bcf7677`.
- Compressed product hash recorded by C1: `3b7610f18a24e29d4d285e755f98500c1505146242f8f9d81d7414d99af1c7ab`.

The first two were rehashed during this note. Product hashes were read from
the retained slot receipt, not freshly verified by opening the FITS products.

## Coordinate and extent semantics

The retained SRCLIST says POSCOROK true and REFCAT `USNO`. SAS eposcorr adds
separate RA_CORR/DEC_CORR columns; it does not replace RA/DEC. Therefore use
corrected positions only for association with the published absolute position,
and original RA/DEC for relative geometry against uncorrected event/map WCS.
Do not silently apply the catalogue correction to the maps, fit an offset, or
recenter the fixed apertures. Explicitly transform the published position into
the declared FK5/J2000 comparison frame locally; preserve any unresolved
published-frame convention as a limitation.
[ESA eposcorr documentation](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eposcorr.pdf)

The retained processing history records `srcmatch` 3.26, SAS 21, and
`extentunit=image`. The current official srcmatch documentation supports image
versus sky extent units. Official emldetect documentation describes extent as
a Gaussian sigma or beta-model core radius, not an enclosing radius, and
RADEC_ERR as a combined positional error. Thus neither EP_EXTENT nor its error
proves a finite 30-arcsec contaminant boundary. Current manuals are semantic
guidance, not a rerun of this exact archived software. Do not import a numerical
image-pixel conversion from the separately generated exposure maps.
[ESA srcmatch](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/srcmatch/node3.html),
[ESA emldetect output columns](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emldetect/node8.html)

## Prospective deterministic association and masks

1. Retain all 151 rows. Require positive, unique SRC_NUM values; preserve row
   ordinals as the unambiguous file identity. Validate finite coordinates with
   RA in `[0,360)` and Dec in `[-90,90]`. Invalid original positions make the
   catalogue screen incomplete, not distant/clean. Invalid corrected positions
   prevent a complete control association. Retain nonfinite/negative error or
   extent counts; never interpret them as zero. Zero error is not proof of
   exact astrometry.
2. Collect **every** valid corrected catalogue position at great-circle
   separation **<=5 arcsec** from the fixed published control position.
   Exactly one is a unique *positional association*, not an independently
   proved physical identity. Zero or multiple matches remain unresolved;
   do not widen the radius, choose the closest, use flux, compare variability,
   or switch to uncorrected coordinates to obtain a preferred match. Keep
   RADEC_ERR and SYSERRCC as separately labelled diagnostics; this note does
   not assign a confidence probability or combine them without a validated
   definition. Large errors remain an explicit association caveat even for
   a unique geometric match.
3. Construct 30-arcsec spherical disks at **every original RA/DEC position**
   for annulus exclusions. Subtract their union, intersected with each fixed
   60–90-arcsec annulus and the separately fixed map-support rule; overlapping
   disks are not subtracted twice. Including the control in this annulus union
   is deliberate: it must not contaminate a negative region's background.
   There is no catalogue exception for negative apertures.
4. For the source aperture, exempt only the uniquely associated control row
   from the *other-source* list. If association is unresolved, do not exempt
   any row or label the region clean. For each of the five apertures report
   other catalogue centres within **20 arcsec**, and separately any fixed
   exclusion disk intersecting it (**distance <=50 arcsec**, inclusive touch).
   These are distinct centre/engineering-mask flags, not measured contaminating
   flux. For annuli, disk contact occurs for centre separations **30–120 arcsec**,
   inclusive; exact spherical membership should determine sampled union area.
5. Preserve point-model (finite zero extent), extended-model (finite positive
   extent), and invalid/unknown-extent categories for relevant intersecting
   rows. No extent likelihood cut is allowed. A positive or unknown extent is
   not converted into a convenient source radius. The fixed disks can still
   be applied descriptively, but an unresolved overlapping source or unknown
   valid radius remains unavailable under the stronger recovery draft. Even
   point-model zero extent does not certify negligible PSF wings outside 30
   arcsec, and absence from this catalogue does not prove empty sky.

If implemented with the existing static geometry approach, report both fixed
4-by-4 and 8-by-8 subpixel union-area estimates and their difference; do not
choose the more favorable result. The current map-support core does not yet
implement source-disk union masks: that is a small separate synthetic-tested
extension, not permission to change its frozen behavior. No clean/pass boolean,
source coordinates, WCS values, individual coordinate arrays or alternative
centres should be exported. Counts of rows/flags, aggregate areas and explicit
unresolved reasons are sufficient public outputs.

## Smallest execution contract and remaining gates

Next authorization should cover only the selected source-list spans, fixed
coordinate transforms/associations and aggregate geometry. Bind the existing
C1 outcome, slot receipt, expanded file and header hashes; check the exact
schema again before decoding. Suggested limits are 60 seconds per worker,
256 MiB peak memory and 1 MiB aggregate JSON, with the 7,852-byte selected
payload cap per pass and one separately declared parent verification pass.
Retain failed/invalid rows in the denominator, account partial reads, and keep
any coordinate vectors in local memory only. No EVENTS, photometry, new
products, external catalogue joins, new centre selection or automatic retries.
These are proposed limits, not a frozen runtime or authorization to execute.

This stage can make a separately prospective descriptive known-control count
screen more informative: it supplies fixed background exclusions and flags
obvious catalogue overlaps without tuning on photons. It cannot promote the
existing `DRAFT_NOT_READY` recovery contract by itself. Still unresolved are
valid contaminant/PSF radii and association limitations; exact event-to-detector
geometry; support for the chosen event FLAG/energy/GTI selections rather than
the different PPS-map selections; per-region time/live-exposure and background
scaling; a fixed detector-artifact veto; and at least two genuinely usable
negative apertures with pn plus at least one MOS. C4's sampled attitude stability
and C5's static support diagnostics do not establish those stronger conditions.
Any narrower count screen must say which conditions remain unresolved and must
not claim calibrated source recovery, a global false-alarm rate or discovery.

References within the repo: `XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md`,
`XMM-C1-HEADER-REVIEW.md`, `XMM-MAP-COMPATIBILITY-2026-09-12.md`,
`XMM-C4-RESULT-2026-09-12.md`. No exhaustive literature or catalogue search is
claimed by this note.
