# C8: one fixed source-list association and contact screen

Prospective contract. Review/test and commit a source/tests/protocol freeze
before any source-list values. No map or photon reads, no network or catalogue
query. Preserve all previous camera/control outcomes and recovery gates.

## Exact retained entity and schema

Only C1 expanded `P0884250101EPX000OBSMLI0000.fits`,250560 bytes, SHA256
`7ee2302307c5336d2e4699c4997e711eda197483f6bec9a62598c0490bcf7677`.
C1 outcome `c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc`;
slot4result `10fd4dd339100c29fa08af477dbdc1622295b3f6aa24dfb9e4750a33c3adb677`;
header `d19ede1f11156b75954e4fa5de3d29c7ce0222bcfa816dc64ed88d7be6c78c3e`.
Validate these directly, without replaying other C1 products or any acquisition.
Whole-file hashes and pinned structural header replay are separate opaque I/O.

Require exact twoHDUs, zero parser warnings, no ambiguous header cards.
PRIMARY:8640 header bytes,NAXIS0,BITPIX8,OBS_ID0884250101,INSTRUME EPIC,
RADECSYS FK5,EQUINOX2000, no conflicting RADESYS. SRCLIST starts8640,
header69120 bytes,dataoffset77760,payload170781,padded172800; NAXIS2,BITPIX8,
151rows,1131bytes/row,266columns,PCOUNT0,GCOUNT1,POSCOROKtrue,REFCATUSNO.
Frame/identity are PRIMARY metadata, not invented SRCLIST keywords.

Derive every packed column offset from all266 TFORM widths; unselected repeated
strings contribute width only. Check exactly these selected column positions:

| Index/name | Form | Unit | Row offset |
| --- | --- | --- | ---: |
| 1 SRC_NUM | J | absent | 0 |
| 6 RA | D | deg | 20 |
| 7 DEC | D | deg | 28 |
| 8 RADEC_ERR | E | arcsec | 36 |
| 146 EP_EXTENT | E | image pixels | 596 |
| 147 EP_EXT_ERR | E | image pixels | 600 |
| 261 RA_CORR | D | deg | 1088 |
| 262 DEC_CORR | D | deg | 1096 |
| 265 SYSERRCC | E | arcsec | 1120 |

Reject selected null/scaling/dimension ambiguity or any heap. No photometric,
variability, likelihood, flux, radius or other scientific field is decoded.

## Exactly bounded value access

Open the expanded file unbuffered (`buffering=0`). For every row i=0..150,
seek to77760+1131*i plus each fixed span offset and read only:
`(0,4),(20,20),(596,8),(1088,16),(1120,4)`.
Exactly755 span reads and7852 selected bytes per successful pass. Decode
big-endian struct fields, keep SRC_NUM signed integer; return all151 rows.
No whole-row fetch, buffered read-ahead, full FITS array loader or map read.

Track returned read bytes, decoded bytes, completed spans and completed rows
separately. Count decoding before later storage failures. A short span retains
its actual returned bytes and previous decoded spans; never manufacture a
complete zero-filled row. Parent numerical validation is a separate7852-byte
pass; worker+parent15704 bytes. Any later numerical replay adds another7852.
On caught parent failure preserve partial validation counters; unrecorded hard
termination means unknown attempted work, not0. Header/hash I/O is separate.

## Frozen geometry and interpretation

Use reviewed `xmm_source_geometry.py`, SHA256
`33f483e69dd78ad64a6b015ecfa02a1e49bf5e2aa8da83f7869f560ecb0059be` and tests
`c013dbc2c7d0599b07b7fb7b76094d26f7ffbc1f7567085d941ed63ae80bf68d`.
Require exactly151 rows in the runtime although pure-core tests allow fewer.
Five centre labels/order remain published,north120,east120,south120,west120.
Use unchanged C5 centre construction, pinned source
`5e7af10b0d8ac5ea8272229efb8a618a392c92d802e6efc401e6b3a54cb5a05b`:
predeclared published ICRS convention,120arcsec cardinal offsets, then FK5/J2000.
Either isolate that function or preserve its exact AST with a synthetic
equivalence check; no importing old run/worker or numerical replay.
Counts-definition remains `7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e`.

Association uses corrected coordinates <=5arcsec. Unique positional association
requires all IDs positive unique signed32-range and all corrected coordinates
valid, with exactlyone matching row. Zero/multiple/incomplete matches remain
explicit; no nearest/brightest choice, enlarged radius or error-weighted match.
Original coordinates determine uncorrected map/event-region contacts, with
invalid originals separately counted as incomplete. Report the unique row's
original-distance/within20arcsec diagnostic without recentering.

All151 rows remain in denominators. Exempt only a uniquely associated row from
the published aperture's other-source counts, never any negative or annulus.
Centre contacts <=20arcsec;30arcsec-disk aperture contacts <=50arcsec; disk/annulus
contacts30<=distance<=120arcsec. Literal inclusive computed-float64 comparisons,
no added tolerance. Tangency is a contact flag, not positive area. Retain
point-model zero/positive extended/invalid extents and separate nonnegative
error/extent diagnostics. Model extent is not an enclosing radius. No fitted
source wings, clean-sky verdict, union masks, supported area or map-fraction
multiplication. Fixed recipe contacts cannot certify absent contamination.

## Execution, output and failure contract

One exclusive60-second process-tree worker via pinned existing deadline helper,
its separate cleanup allowance; worker/parent monitored peak268435456 bytes,
not OS enforcement. JSON1048576 aggregate,65536 terminal reserve. No new product
copies or full-header derivatives needed. Runtime binds source/tests/protocol
snapshot, selected-span reader/tests, geometry core/tests, C1/helper/structural
source/tests and actual runtime/configuration. All inputs immutable.

Exclusive run/worker/table start and terminal receipts. Public results only
fixed-region aggregate diagnostics, association multiplicity/status, scalar
relative-distance/error summaries, hashes and resource counters. No source IDs,
row ordinals, coordinate arrays, absolute WCS, event values, raw exceptions or
hidden coordinate cache. Parent independently verifies numerical summaries,
exact artifact/label/row/span closure and single-table accounting.

Nonzero worker, timeout, hash/schema mismatch, missing row or receipt mismatch
cannot pass. Completed scientific-screen diagnostics may explicitly contain
invalid scientific values or unresolved association; execution completion is
not clean-sky/recovery success. Failed-artifact replay cannot certify unverified
values or unrecorded reads. Strongest label SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY.
This does not authorize photons, calibrated rates/significance, unknown-source
search, correspondence, publication or scientific submission.
