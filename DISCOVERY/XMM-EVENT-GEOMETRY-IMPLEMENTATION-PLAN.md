# Selected EVENTS sky geometry: implementation plan, not photon execution

Prepared 2026-09-12 from retained header JSON and primary documentation only.
No event, map, attitude or source-list values were read. No product request,
detector fit, count experiment or new implementation file was made.

## Decision and origin proof

Use the stored **X/Y values unchanged with origin=1**, not array row/column
indices. The selected linear step is `(X-TCRPX6)*TCDLT6` and
`(Y-TCRPX7)*TCDLT7`, followed by TAN projection. FITS section8.2 says table
pixel-list WCS uses the same rules as image WCS; equations9-10 use the pixel
coordinate minus its reference point. Table22 maps TCRPX/TCRVL/TCDLT/TCTYP/TCUNI
to image CRPIX/CRVAL/CDELT/CTYPE/CUNIT. Its frame table identifies RADECSYS as
the deprecated spelling of RADESYS. These are published conventions, not an
offset inferred from this observation. [FITS standard3.0, sections8.1-8.3 and
Table22](https://fits.gsfc.nasa.gov/standard30/fits_standard30aa.pdf).

Astropy's low-level `wcs_pix2world(xy, 1)` takes FITS coordinates;
`wcs_pix2world(xy-1, 0)` is equivalent. Passing unchanged values with origin0
introduces an unintended one-unit shift in both axes. Do not add half a pixel.
`fix=False, relax=False` prevents automatic repairs/informal header acceptance;
duplicate cards must be rejected before construction because Astropy can use
the last duplicate. Direct table construction would require `keysel=['pixel']`
and `colsel=[6,7]`; the narrower proposed adapter constructs only the verified
two-axis image-equivalent header. [Astropy WCS API](https://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html).

SAS attcalc documents X/Y as attitude-corrected sky coordinates, with their
table WCS cards in EVENTS. This is not an instruction to apply an attitude
correction again, nor proof of an external astrometric correction.
[SAS attcalc output](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/attcalc/node7.html).

## Retained metadata checks

All three selected table-WCS tuples are exactly equal in the retained reports.
No absolute sky reference values are reproduced here. X/Y are signed J fields
in columns6/7 with null sentinel -99999999, TAN RA/Dec, degree TCUNI, FK5 and
equinox2000. The scale is0.05arcsec per coordinate unit; MOS's TUNIT spelling
`pixel` does not replace TCDLT. Actual pn TUNIT is `0.05 arcsec` with a space.

The initial preflight prose mislabelled columns4/5. Direct checks establish
RAWX/RAWY in2/3, DETX/DETY in4/5, and X/Y in6/7. Root corrected that prose with
history; no decoder or measured result changed. DETX/DETY have their own WCS.

Header-only SHA-256 anchors:

- pn: `a6d78ea07324eeef06ed544555525ebb4e071f069eb428ed050913d6cbcbf0ba`
- MOS1: `a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae`
- MOS2: `4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417`
- Corrected [preflight](XMM-EVENT-WCS-PREFLIGHT-2026-09-12.md):
  `3ae8f861e113365ab5f0d171d0aa40d493a00a294fee028219be63778776865c`
- [Decoder preparation](XMM-EVENT-DECODER-NEXT-2026-09-12.md):
  `8e936efe2cb6e57bd67a4cf00192a3215431c3858376394e0d68e80ff1d8a95e`
- [Pure decoder](xmm_event_rows.py):
  `9a5b86117956f98e1dcabec197fd70bab148ed9bba93048793680b7b6c448f4c`

## Small implementation contract

Proposed APIs, not implemented here:

1. `build_geometry(header_pairs)` returns a private immutable selected-axis
   definition. Preserve duplicate cards while validating. Require exact
   TTYPE6=X, TTYPE7=Y, scalar J, expected nulls, finite numeric reference fields,
   nonzero increments with the retained signs/scale, exact TAN/degrees and
   FK5/equinox2000. Require the full EVENTS decoder schema independently.
   No fallback to primary REFX/REFY cards or DET/RAW coordinates when a selected
   table card is absent.
2. Construct a fresh minimal image-equivalent header: selected columns6/7 become
   axes1/2. Explicitly map the validated legacy RADECSYS=FK5 to RADESYS=FK5;
   reject conflicting legacy/modern frame declarations. Retain numerical
   EQUINOX=2000, no inferred default frame. Do not pass the complete table header
   into an image WCS constructor. Capture warning categories only; unexpected
   construction warnings or non-2D/noncelestial results STOP before photons.
3. `classify_xy(x, y, xy_valid, geometry, centres_fk5)` accepts at most the
   decoder's10000 rows, exact signed-integer coordinate arrays and aligned bool
   masks, and returns same-length local masks plus scalar accounting. Apply
   both explicit null sentinels and supplied masks before any projection.
   No masked coordinate reaches WCS; do not turn invalid rows into outside rows.
   Transform only valid coordinates to local float64 sky arrays, compute
   spherical separations, and discard those arrays after classification.
   Unexpected nonfinite output among attempted valid rows is a recorded STOP,
   not a silently lost event. All-masked and empty chunks need defined outputs.
4. Keep the five fixed centres from C5, using its already adopted ICRS
   convention and explicit transformation to FK5/J2000. This changes frame,
   not the astrophysical target or aperture. Astropy supports an explicit
   `transform_to(FK5(equinox='J2000'))`; merely relabelling ICRS numbers is not
   that operation. [Astropy coordinate transformations](https://docs.astropy.org/en/stable/coordinates/transforming.html).
5. For unchanged circle20 and annulus60_90 definitions use true angular
   separations, with declared inclusive boundaries20,60,90arcsec. Do not use a
   constant-radius circle in X/Y as a replacement for a spherical aperture.
   Source-list exclusions require their separately frozen frame/identity rules;
   this component must not invent an astrometric shift or exempt another source.

Receipt metadata contains axis labels, origin, schema/header hashes and scalar
counts only, never CRVAL values, transformed photon positions or centre arrays.
The wrapper owns file identities, full-row returned bytes, durable per-pass
accounting, deadline and output limits. Geometry records input/masked/attempted/
completed rows separately; no photon count is yet authorized by this plan.

## Narrow rejection profile before projection

This is an engineering allowlist for these retained headers, not a general FITS
reader. Before discarding unselected cards, reject unsupported transformations
that could otherwise be silently dropped:

- Any selected-axis scaling/dimensions, duplicate required card, alternate
  selected-axis WCS, unexpected selected units/projection, or ambiguous frame.
- Table matrix families `TPCn_k`/`TPn_k`, `TCDn_k`/`TCn_k` and `TCROTn`;
  projection-parameter families `TPVn_m`/`TVn_m`, `TPSn_m`/`TSn_m`, including
  alternate-version suffixes. A simple initial implementation can reject these
  families anywhere in EVENTS; the retained headers contain none. Do not use
  a broad `TCD*` rejection that accidentally rejects required `TCDLT6/7`.
- Table cross-references WCST/WCSX, explicit pole overrides LONP/LATP or image
  LONPOLE/LATPOLE, axis-specific RADE/EQUI overrides, mixed image-WCS matrices
  or parameters, SIP, lookup/distortion CPDIS/CQDIS/DP/DQ/D2IM/DET2IM families.
  Reject unknown transformation-bearing variants rather than ignore them.
  Metadata-only WCS names/errors or bounds do not create a calibration or
  coverage claim. Exact regexes must be reviewed against Table22, not guessed
  by prefix length. The required scalar DETX/DETY metadata may remain present
  but is not copied into the selected transform.

## Synthetic validation before any event execution

A disposable in-memory check compared Astropy against an independent TAN
vector formula, using three invented tangent points including RA-wrap/high
declination cases and25 offsets each. For unit tangent vector z, east vector e
and north vector n, the independent sky direction is
`normalize(z + radians(dx*CDELT1)*e + radians(dy*CDELT2)*n)`.
All75 synthetic points agreed within1.374e-10arcsec. Deliberately using origin0
on unchanged reference coordinates displaced the synthetic answer by about
0.070710678arcsec. This demonstrates the sign of the origin mistake, not
astrometric accuracy or an error allowance for real data.

The implementation's retained synthetic suite should cover reference-point
identity, origin equivalence and wrong-origin discrimination; RA wrap; swapped
axes/signs; invented unequal scales; high declination; the independent vector
oracle; roundtrip; all null/masked inputs; masked sentinel never passed to WCS;
malformed shapes/dtypes; transform failure accounting; exact and just-inside/
outside aperture boundaries; disjoint own-circle/own-annulus membership;
all five centres and shared membership across different centres; and every
unsupported-key family above. Compare a synthetic table with colsel6/7 to the
minimal adapter, including unrelated DETX/DETY metadata, to expose axis leaks.

## Scientific boundary

Successful projection gives geometric membership only. It does not establish
live detector area, GTI/time-bin exposure, defect freedom, complete PSF wings,
source-exclusion support, equal camera sensitivity, a rate or a significance.
TLMIN/TLMAX and observed photon occupancy are not exposure maps. No RAW fit,
recentring, event-dependent aperture, camera waiver or retry follows from this
plan. A separately reviewed count protocol must retain the original recovery
requirements and distinguish a raw-count screen from calibrated recovery.
