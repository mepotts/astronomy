# M2a: twelve PRF calibration products, acquisition and structure only

Prospective preparation, September 12, 2026. **Not executed or publicly
preregistered.** Parent review/GO is required before preparing the manifest, and
another explicit reviewed-manifest GO before any FITS request. Preserve all prior
protocols, software, data and results. No fitting, interpolation, injection,
source localization, science-pixel acquisition or unknown search is authorized.

## Fixed products and resource envelope

Acquire only the Cartesian grid corners listed in NEXT-LOCALIZATION-PROPOSAL.md,
in the table order below, ascending row then ascending column within each field.

| Existing control | Camera/CCD | Filename prefix | Rows | Columns |
|---|---|---|---|---|
| 450781262, sector 99 | 3/3 | tess2019107181902-prf-3-3 | 1025,1536 | 1580,2092 |
| 53206761, sector 72 | 4/3 | tess2019107181902-prf-4-3 | 1536,2048 | 0557,1069 |
| 2041210548, sector 57 | 2/3 | tess2019107181901-prf-2-3 | 1536,2048 | 1580,2092 |

Append `-rowRRRR-colCCCC.fits`. Fixed base URL:
`https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/`,
then `cam<CAM>_ccd3/` and the exact filename. No HEAD request, directory refresh,
tarball, MATLAB file, alternate model, endpoint, retry or redirect during execution.
Exactly twelve selected products, at most one GET each. A failed product stops
launching the remainder; their explicit outcomes are STOP_NOT_LAUNCHED. There is
no automatic recovery, even if a failure appears transient or structural only.

Per product: 300,000 decoded/retained response bytes; 30-second connect/read socket
timeouts; 45-second owner-context process-tree deadline including structural
validation. Twelve request caps sum to 3,600,000 bytes, below the 4,000,000-byte
stage ceiling; serial worker deadlines sum to at most 540 seconds. Use the existing
tested bounded_run tree helper and streaming byte limiter. Explicit zero HTTP
retries and no redirects. Require HTTP 200; reject an announced oversized body
before writing, and preserve any partial streamed body on failure. Socket timeouts
are not claimed to be total worker deadlines. No new runtime/library installation.

Freeze source, tests, independent review tests when available, this protocol,
proposal, coordinate audit, prior M1b result/source/protocol and helper hashes in
an exclusive manifest. Before requests, recheck the complete manifest and each
retained TPF hash/header identity. Exclusive run-start, per-product attempt and
worker-start markers prevent reruns, including direct worker repeats. Parent
outcomes retain success/failure, traceback or deadline, elapsed launch time and
all artifact hashes. Preserve raw worker exit code separately from the parent's
accepted outcome. A zero worker exit alone never authorizes the next launch:
the parent must verify matching attempt/worker-start manifest and product identity,
complete byte/hash/HTTP-length receipt, absence of conflicting failure, and exact
recomputed structural-validation receipt. Any mismatch stops the remaining queue.
Launcher/reservation errors account for unlaunched products.
Storage failures may prevent receipts and must be surfaced, never retried silently.

## Schema derived before observing any PRF FITS

The official [export_mat2fits.m](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/export_mat2fits.m)
was inspected as text only. It creates exactly two double-precision image HDUs,
each 117 by 117: a primary PRF and an image-extension uncertainty array. This is
not a primary-with-no-data plus two extensions. Both have ORIGIN=MIT, TELESCOP=TESS,
CAM/CCD matching the filename, CCD_RREF/CREF equal to the selected row/column,
NSAMP=9 and PRF_RES=2.35. Primary DATATYPE=PRF and VERSION=UPDATED_2.0; extension
DATATYPE=Uncertainties. The exporter does not set extension VERSION, BUNIT,
DATASUM or CHECKSUM: do not demand missing undocumented keywords. If extension
VERSION exists it must agree; checksum cards, if present, must verify. Record
any BUNIT without inferring physical flux units or a covariance model from it.

Both physical WCS headers must have WCSNAMEP=PHYSICAL, WCSAXESP=2, CTYPE1P=RAWX,
CTYPE2P=RAWY, CUNIT1P/2P=PIXEL, CRPIX1P/2P=59, CRVAL1P=selected column,
CRVAL2P=selected row and CDELT1P/2P=1/9. Use absolute tolerance 1e-12 and rtol zero
for decimal header serialization only. Reject duplicate required keywords,
nonidentity scaling (BSCALE/BZERO), unsupported physical cross terms, different
image dimensions/precision, extra HDUs, truncation or unexplained trailing bytes.
Require finite values throughout both arrays, nonnegative uncertainties, and
finite array totals and some positive PRF support with positive total. Signed PRF samples are retained;
negative counts are reported, not clipped. These are structural usability checks,
not fits or normalization/uncertainty calibration. Record complete header cards,
array shapes/negative counts and native reference coordinates; do not normalize,
resample, crop or compute an interpolated PRF.

The [release README](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/00README.txt)
assigns this release to sectors 4 onward. The 117 samples represent 13 physical
pixels at nine samples per pixel, not a 117-pixel sky cutout. Its 2018 commissioning
models do not establish contemporary color/temperature or centroid accuracy.
No uncertainties are interpreted as independent-pixel noise or flux fractions.

## Coordinate check and outcome boundary

Use the already documented direct SPOC mapping in PRF-COORDINATE-AUDIT-2026-09-12.md:
native RAWX/RAWY equals APERTURE CRVAL1P/CRVAL2P plus zero-based stamp x/y, since
the retained CRPIX values and steps are one. No extra 44 or one is added.
Require RAW_CNTS, FLUX and APERTURE reference headers to agree and whole 11x11
stamp bounds to lie within the fixed rectangle. Check the retained identity,
origin and header-derived target position, not a fitted source location.
PRF sample (58,58) maps to its native selected column/row because FITS CRPIX=59.
This checks local arithmetic and bracketing, not an independent absolute-reference
anchor; the coordinate audit's unresolved absolute-registration caveat remains.

Save only new data/m2a receipts/files and out/m2a-summary.json. Complete success
is PRF_PRODUCTS_STRUCTURALLY_VALID, with localization_validated=false and
unknown_search_authorized=false. Failure is STOP_PRF_PRODUCT with all remaining
products accounted for and original/partial bytes untouched. No scientific GO
follows from product availability. Numerical fits, field/subpixel interpolation,
empirical negatives and confusion calibration require separate prospective stages.

Before freeze, synthetic tests and pinned Ruff 0.16.5 must pass and independent
review must accept schema, exact requests, bounds, one-attempt behavior, failures
and replay. Offline replay verifies dependencies, all attempts/outcomes/artifact
hashes and rederives complete successful structural validation from retained bytes;
it also verifies receipt semantics (not only their stored hashes), false scientific
flags, consistent exit/status fields, the stop-first-failure launch sequence and
the summary status derived from all twelve outcomes. It never makes requests or
writes files. Review does not waive strict schema checks
if actual products disagree: record STOP and seek a separately labelled amendment.
