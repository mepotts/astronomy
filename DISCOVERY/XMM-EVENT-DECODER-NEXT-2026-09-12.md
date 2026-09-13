# Photon-reader preparation: exact retained schema, no event values read

Metadata-only inspection of the three C1 EVENTS header reports after C4.
This is a decoder/resource planning record, not authorization or a frozen
photon experiment. The [recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md)
still has unresolved geometry, exposure and defect-screening requirements.

## Exact payload bounds from the retained headers

| Camera | Rows | Bytes per row | Data offset | Event payload bytes |
| --- | ---: | ---: | ---: | ---: |
| pn | 2694388 | 45 | 63360 | 121247460 |
| MOS1 | 273441 | 34 | 40320 | 9296994 |
| MOS2 | 356129 | 34 | 40320 | 12108386 |

Total EVENTS payload is **142652840 bytes per full three-camera pass**, not
the complete files' 247141440 expanded bytes. The difference includes headers
and ancillary tables; it is not missing event data. A future row-streaming
reader may read each bounded row as opaque bytes while decoding only its
allowlisted fields. Account returned row bytes separately from decoded field
bytes if adopting that method. Do not claim unselected columns were never
physically read when full rows were fetched.

Common selected formats are TIME D, RAWX/RAWY I, X/Y J, PI I, FLAG J,
PATTERN B and CCDNR B. X/Y are columns6/7, PI9, FLAG10 and PATTERN11;
CCDNR is column14 for pn and12 for MOS. Derive exact byte offsets from **all**
TFORM declarations and verify the complete row length; never assume identical
camera layouts or C-struct padding. The actual FLAG fields are signed32-bit
integer J, not FITS X bit arrays. FLAG==0 can be tested directly without an
invented unsigned scaling convention.

## Nulls and units to preserve before any geometry

- All three X/Y columns declare TNULL=-99999999. Reject/count those sentinels
  before any coordinate transformation; a finite integer is not necessarily
  a valid position.
- pn PI declares TNULL=-32768 and PATTERN declares TNULL=13. These differ
  from MOS, which has no corresponding TNULL cards. Retain explicit per-camera
  missingness before applying the unchanged energy/pattern cuts.
- No TSCAL/TZERO is declared for these selected columns. TIME is seconds;
  pn PI is labelled eV, MOS PI CHAN. The
  [earlier unit-resolution addendum](XMM-C1-HEADER-REVIEW.md) already adopted
  calibrated numerical MOS PI as eV from official guides and column comments.
  Do not infer a conversion from the future observed PI distribution.
- X/Y have their own TCTYP/TCRPX/TCRVL/TCDLT/TCUNI header metadata. Their
  differing TUNIT spellings do not justify a universal coordinate scale or
  ignoring the per-camera table WCS. Validate the actual transform and frame
  against fixed sky positions using synthetic tests before photons.

The source-list geometry and C5 accumulated-map diagnostics are independent
pending inputs, not event-occupancy substitutes. No actual event byte was
decoded here, no light curve was viewed and no numerical selection changed.

## Header identities

| Camera | Header-report SHA-256 |
| --- | --- |
| pn | `a6d78ea07324eeef06ed544555525ebb4e071f069eb428ed050913d6cbcbf0ba` |
| MOS1 | `a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae` |
| MOS2 | `4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417` |

These are the existing C1 header anchors; future execution must independently
verify them and the matching product/outcome hashes before using this schema.
