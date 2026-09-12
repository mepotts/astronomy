# SPOC TPF/PRF coordinate audit: no extra 44-column shift

Read-only research audit, September 12, 2026. No FITS data downloads, pixel
measurements, fitting, new catalog queries or changes to frozen artifacts.

**Result:** the directly documented SPOC-TPF workflow uses the physical header
origin plus zero-based stamp coordinates, with **no additional 44-column offset**.
That is the supported implementation contract for a prospective diagnostic.
The local zero-/one-based WCS conversion is exactly determined by our headers.
However, the consulted mission documents do not completely reconcile the absolute
one-pixel detector-label convention across every FFI/TPF/PRF example. Do not
claim a fully validated absolute astrometric registration on this audit alone.

## 1. Direct SPOC example, more relevant than a trimmed-FFI example

Nicole Schanche's TESS Science Support Center tutorial explicitly selects
`pipeline='SPOC'` and a 120-second TPF. It reads origin_col from `1CRV4P`, origin_row
from `2CRV4P`, computes stamp coordinates with `all_world2pix(..., 0)`, adds those
origins, and passes the resulting coordinates directly to TESSPRF.evaluate.
There is no extra 44 or 1 added to either coordinate.
[Support-center PRF/TPF tutorial](https://github.com/lightkurve/lkprf/blob/main/docs/tutorials/lkprf_TPF_example.ipynb)

The package's own [TESS PRF source](https://github.com/lightkurve/lkprf/blob/main/src/lkprf/tessprf.py)
uses the field-grid coordinates from the model headers and marks columns below
45 as collateral. Its [base model](https://github.com/lightkurve/lkprf/blob/main/src/lkprf/prfmodel.py)
reads CRVAL1P/CRVAL2P directly, without a hidden +/-44 coordinate conversion.
The model is a corroborating public implementation, not an independent accuracy
certificate. It was inspected as text only, not installed or executed.

Inference from this explicit workflow: SPOC TPF physical labels already belong
to the detector-column convention used by that PRF implementation; adding 44
again would displace the field-interpolation location. This does not mean that
the 11-by-11 target stamp itself contains 44 collateral columns.

By contrast, the older [MAST PRF retrieval tutorial](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/interm_tess_prf_retrieve/interm_tess_prf_retrieve.html)
adds 44 to a coordinate derived from its TESScut/calibrated-image example, and
describes that input as starting at column 1. Its documented PRF grid starts at
column 45. That instruction must not be transferred to a SPOC TPF without
tracking the input convention. The general archive prose about an offset is not
sufficient to decide a sign or whether an API has already applied it.

## 2. Exact calculation from the retained headers

All three retained APERTURE extensions have:

```
CTYPE1P=RAWX   CTYPE2P=RAWY
CRPIX1P=1     CRPIX2P=1
CDELT1P=1     CDELT2P=1
```

For a zero-based stamp pixel center `(x,y)`, the FITS input coordinates are
`(x+1,y+1)`. Consequently:

```
RAWX = CRVAL1P + ((x + 1) - CRPIX1P) * CDELT1P = CRVAL1P + x
RAWY = CRVAL2P + ((y + 1) - CRPIX2P) * CDELT2P = CRVAL2P + y
```

The `+1` and reference-pixel `1` cancel. Adding another one merely because FITS
pixel coordinates start at one would be an error in this **local-to-native**
transform. Equivalently, `WCS(header, key='P').pixel_to_world_values(x,y)` returns
these same native physical-coordinate values. This is separate from any proposed
conversion between two different instruments' or products' native label systems.

The following are header-derived positions of the existing FITS target coordinate,
not new centroid measurements:

| TIC | Sector/camera/CCD | Stamp origin RAWX,RAWY | Existing target stamp x,y | Native target RAWX,RAWY |
|---|---|---|---|---|
| 450781262 | 99/3/3 | 1720,1488 | 5.003680513,5.634091715 | 1725.003680513,1493.634091715 |
| 53206761 | 72/4/3 | 672,1798 | 5.373462240,5.843987867 | 677.373462240,1803.843987867 |
| 2041210548 | 57/2/3 | 1889,1939 | 5.325923153,5.774010922 | 1894.325923153,1944.774010922 |

Read-only numerical checks found exactly zero difference between the analytic
formula and Astropy's alternate-P result for all three. RAW_CNTS (`1CRV4P/2CRV4P`),
FLUX (`1CRV5P/2CRV5P`) and APERTURE origins agree exactly. The retained stamps are
11-by-11 with unit steps and no alternative-P cross terms. Astropy emitted its
visible unit-spelling normalization warning (`PIXEL` to `pixel`), not a numerical
coordinate correction. We did not suppress the warning.

The relevant files remain under data/m1/<TIC>/ with their previously retained
hash receipts. Stored target positions are in [M1b first](out/m1b-450781262.json),
[second](out/m1b-53206761.json) and [third](out/m1b-2041210548.json) results.

## 3. What the actual mission/export documentation establishes

The mission manual, section 2.5.3, distinguishes image coordinates from alternate-P
physical CCD coordinates. Its Table 4 lists leading virtual columns 1-44, science
columns 45-2092 and science rows 1-2048. However, that same table's FFI example
sets physical CRPIX1P/2P=1 and CRVAL1P/2P=0. Table 9's TPF example uses physical
origins 983,94. These are examples, not an explicit universal statement that all
native physical outputs are zero- or one-based. The two relevant Table 4 pages
(printed 21-22, PDF pages 24-25) were rendered and visually checked; the zero
values are really present, not a text-extraction artifact.
[Mission data-product manual, Rev F](https://archive.stsci.edu/files/live/sites/mast/files/home/missions-and-data/active-missions/tess/_documents/EXP-TESS-ARC-ICD-TM-0014-Rev-F.pdf)

The official [MAST PRF export script](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/export_mat2fits.m)
writes each model's ccdColumn/ccdRow directly to its filename, CCD_CREF/CCD_RREF
and physical CRVAL1P/CRVAL2P. The reference sample is FITS pixel 59 in each axis,
with step 1/9. Thus its zero-based sample (58,58) maps to the exact named detector
reference. No subtraction of 44 occurs in the export script. Its input grid's
one-based-style labels match the filename columns 45,557,1069,1580,2092 and rows
1,513,1025,1536,2048. The source text was read, never executed; no PRF FITS was fetched.

The [release README](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/00README.txt)
describes (1,1) as a lower-left pixel center and mentions a 44-column difference
from science products. Combined with the explicit SPOC example, this is a reason
to document coordinate types, not to apply a universal blind shift. Also, the
public [Astrocut implementation](https://astrocut.readthedocs.io/en/v1.0.0/_modules/astrocut/tess_cube_cutout.html)
sets its physical origin to zero-based cutout limit plus one. Product generation
can therefore establish its own native labels; a shared keyword name alone does
not prove identical conventions across every product/API.

## 4. Residual caveat and precise next validity requirement

Supported now: use the explicit SPOC header transform above; do **not** add 44;
do **not** add one to the stamp-to-native transform. This settles what our
retained headers say and how the support-center PRF example consumes them.

Not established by this restricted audit: whether every PRF native grid label
and every SPOC TPF physical output is globally one-based in the same sense as a
full-frame DS9 array coordinate. The FFI example's zero and the direct PRF/TPF
workflow are not enough to prove that equality at a detector edge. Our three
interior stamps cannot distinguish conventions just by staying within bounds.
It would be misleading to call a small WCS round-trip residual independent proof.

Before an absolute-source claim, obtain one explicit, independent anchor: an
official SPOC exporter definition or a documented same-coordinate reference
showing which TPF native label corresponds to the first imaging pixel and how
that maps to the PRF grid. A small retained/approved boundary-product metadata
example could also discriminate the possibilities. Do not select +/-1 by whichever
choice improves a target centroid or a PRF fit. A global integer shift applied
to both source and stamp preserves relative sampling but changes field weights;
that fact makes visual agreement a weak discriminator, not an excuse to ignore it.

The existing proposed grid rectangles remain unchanged. An erroneous 44-column
shift changes a column interpolation fraction by 44/512 = 0.0859375; a one-pixel
shift changes it by 1/512 = 0.001953125. These are interpolation-weight changes,
not directly astrometric error estimates. Neither magnitude can be converted to
an absolute confidence interval without a calibration test.

## 5. Scope/provenance and outcome

The PDF skill required visual review of the actual table. Web screenshots did
not expose usable images through this tool path, so the primary manual was
retrieved locally. An initial conservative 6 MB documentation cap refused the
download; a read-only HEAD established 8,122,252 bytes, followed by one successful
8.2 MB-capped documentation download and local rendering. This was not a scientific
input retry or a changed scientific-stage limit.

Retained manual: data/coordinate-audit/EXP-TESS-ARC-ICD-TM-0014-Rev-F.pdf, SHA-256
`e8eca77f16ec90f71d41224c7eaad81ebe1a7b4bf54c97e811bf8d863f61eca2`.
Raw documentation/renderings remain ignored locally. Existing TPF, LC, M0/M1/M1b,
M1c and proposal files are unchanged. No generic PRF implementation was installed.

Outcome: **DOCUMENTED_SPOC_MAPPING_SUPPORTED; ABSOLUTE_REFERENCE_CHECK_REMAINS**.
This audit narrows the coordinate gate but does not validate PRF precision, close
neighbor discrimination, catalog completeness or physical eclipse depth. In
particular, it does not eliminate the approximately 2.728-arcsec first-field
competitor or authorize unknown-target scanning.
