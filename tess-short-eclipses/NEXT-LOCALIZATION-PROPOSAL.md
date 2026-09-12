# Next localization experiment: small calibration pilot, not discovery GO

Research proposal, September 12, 2026. **Not an executed or frozen protocol.**
M0/M1/M1b inputs, source, protocols and results remain unchanged. This investigation
read primary documentation, three small official directory-index pages and local
headers/results only. No new PRF FITS, catalog rows, light curves or pixels were
acquired; no new scientific fit was performed.

Recommendation: first attempt a separately labelled Gaia mirror parity check;
then test measured PRFs on the same three known controls with injections and
within-field negative windows. The useful outcome is a measured limit on source
identification, including an honest failure to separate close competitors.
Neither stage by itself authorizes unknown-target scanning.

## 1. Applicable official calibration products

The MAST release README assigns `start_s0004/`, VERSION `UPDATED_2.0`, to sector
4 onward, accounting for improved pointing. Its commissioning observations were
collected in July 2018. FITS products contain a PRF image and uncertainty image;
each 117-by-117 interleaved array represents 13-by-13 physical pixels at 9-by-9
subpixel positions. Field interpolation is described as accurate to 1–5 percent;
that is **not** a centroid error bound. [MAST release README](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/00README.txt)

NASA describes substantial field dependence, some chromatic dependence and
temperature dependence. The PRF includes pointing jitter during an exposure.
The pixel scale is approximately 21 arcsec. The documented sector applicability
does not establish a contemporaneous, color-matched astrometric calibration for
our 2022–2026 observations. No newer epoch-specific PRF availability was verified.
[NASA instrument description](https://heasarc.gsfc.nasa.gov/docs/tess/telescope_information.html)

The following instrument identities and physical reference coordinates were read
from retained FITS headers. `RAWX/RAWY` below are APERTURE alternate-P WCS values
at the zero-based stamp origin; they are not assumed to be PRF request coordinates.
The file grid rectangle is the Cartesian product of the two rows and two columns.

| Published TIC | Sector / camera / CCD | Stamp origin RAWX, RAWY | PRF filename prefix | Grid rows | Grid columns |
|---|---|---|---|---|---|
| 450781262 | 99 / 3 / 3 | 1720, 1488 | tess2019107181902-prf-3-3 | 1025, 1536 | 1580, 2092 |
| 53206761 | 72 / 4 / 3 | 672, 1798 | tess2019107181902-prf-4-3 | 1536, 2048 | 0557, 1069 |
| 2041210548 | 57 / 2 / 3 | 1889, 1939 | tess2019107181901-prf-2-3 | 1536, 2048 | 1580, 2092 |

Each filename ends `-rowRRRR-colCCCC.fits`. All twelve entries are present in the
official [camera 3/CCD 3](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/cam3_ccd3/),
[camera 4/CCD 3](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/cam4_ccd3/)
and [camera 2/CCD 3](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/cam2_ccd3/)
directory listings checked today. Each listing says **225K**, a rounded display,
not an exact byte receipt. Twelve files are approximately 2.8 MB. Downloading whole
camera tarballs or MATLAB products is unnecessary for this pilot.

### Coordinate and interpolation prerequisites

The official tutorial uses file-grid columns 45, 557, 1069, 1580, 2092 and adds 44
to a trimmed TESScut/FFI column. Its sample implementation rounds subpixel phase to
the nearest ninth-pixel sample. That example is useful for interpreting the
interleaved arrays, but is not a continuous subpixel centroid estimator.
[MAST PRF tutorial](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/interm_tess_prf_retrieve/interm_tess_prf_retrieve.html)

Before fitting, independently reconcile the release README's physical-coordinate
description with **SPOC TPF RAWX**, not merely the tutorial's trimmed cutout. Record
whether the TPF alternate-P value already includes collateral columns; apply an
offset once, if required. Confirm against PRF FITS headers and a documented mission
coordinate example. A WCS round trip alone tests arithmetic, not the correct offset.
The rectangles above remain the same under either 44-column convention for these
three stamps; their interpolation weights do not. Therefore availability/byte
planning can proceed, but a scientific fit cannot proceed with this unresolved.

Software tests must check row/column order, zero-/one-based origins, all 81 exact
subpixel grid values, continuous interpolation across pixel boundaries (including
integer-center shifts), true bracketing rather than unconstrained nearest points,
flux normalization before cropping, and uncertainty-image dimensions/units.
Never normalize the cropped 11-by-11 model to unity and then call its amplitude
the source's total flux. Retain the lost-wing fraction. Do not execute downloaded
tutorial code or transfer its rounding rule into the scientific estimator.

## 2. Official Gaia mirror: recover metadata with a parity control

ESA lists ARI as a Gaia partner data centre integrated with catalog access; this
is a documented alternate access route to the **same Gaia release**, not new
independent astrometry. [ESA access description](https://www.cosmos.esa.int/web/gaia/data-access)
ARI documents POST queries to `https://gaia.ari.uni-heidelberg.de/tap/sync` against
`gaiadr3.gaia_source`. Its documentation also identifies overflow flags and service
limits. Reachable documentation is not proof that our queries will finish.
[ARI service help](https://gaia.ari.uni-heidelberg.de/help.html)

Propose a new metadata-only stage, with no implicit retry of M1b:

1. Freeze exact code, adapter, queries, limits and comparisons first. Submit the
   **identical retained eight-column ADQL** for TIC 450781262 to ARI once: same
   0.05-degree cone, retained LC center, TOP 5001 and source_id ordering; retain
   `gaiadr3.gaia_source`, not a lite table or another release. No catalog upload.
2. Require exactly the retained 1,290 source IDs, preserving signed int64, and
   identical optional-value masks. Match columns by unique VOTable FIELD NAME,
   with the M1b datatype/status checks. Compare finite RA/Dec with absolute
   tolerance 1e-10 degree, ref_epoch 1e-9 year, PM 1e-5 mas/year, G and RUWE 1e-5,
   all with relative tolerance zero. These are proposed serialization tolerances,
   not astrometric errors; test them synthetically before requests. Reject duplicate
   IDs, mismatched units, overflow, 5,001 rows or altered null semantics.
3. Only if parity passes, request each of the two missing fields exactly once,
   reusing their exact retained ADQL. Apply the same strict parser and size/status
   gates. Compare parsed values, not XML bytes: a mirror may serialize the same
   table differently. Preserve the first ESA response hash
   `d4a1069cfb5244c28db6dfc354df326ab1a5db611e36612b536b7f914d105098`.
4. Limit each request to 45-second socket timeout, 60-second process-tree deadline
   and 5,000,000 streamed response bytes: at most three requests, 180 seconds and
   15 MB. No fallback endpoint, async job, relaxed parity or further retry. Preserve
   failures separately; missing catalogs are not empty fields.

Use existing epoch propagation only as a reproducibility baseline. Eight columns
do not provide positional/proper-motion covariance, parallax or a full crowded-field
astrometric validation. Missing motion near a candidate, a questionable association
or insufficient uncertainty information remains an explicit source-identification
gate; a mirror success does not fix it. Obtaining additional astrometric columns
would require a separately specified metadata extension, not a silent query change.

## 3. What can this actually distinguish?

From the retained first-field positions and APERTURE sky WCS, the provisional
target (Gaia 5346312514819760896) and nearest target-position competitor
(5346312519131403776) are **0.129367 pixel, or 2.728308 arcsec**, apart. This differs
from the 2.454918-arcsec competitor-to-FITS-header separation stored in M1b.
The existing Gaussian bootstrap radius is 0.080548 pixel; it measures resampling
spread, not absolute astrometric coverage. Another bright listed source (G=13.34)
is about a pixel away, and 26 listed alternatives lie within one pixel of the
existing difference centroid. These are potential alternatives, not independently
validated physical blends. [Retained first-field result](out/m1b-450781262.json)

Inference: a calibrated variable-component centroid could reject a distant bright
neighbor even when two steady images are unresolved. Twenty-one-arcsec sampling
does not categorically prevent subpixel localization. Conversely, a narrow fit
interval cannot create resolved photometry or rule out the closest approximately
2.7-arcsec alternative without validated PRF, WCS and catalog systematics. The
current nominal spread is already a substantial fraction of that separation.

A failed close-pair injection test should end attempts to claim identification
from this stamp. A successful self-injection test is only a necessary condition:
it cannot bound real color/focus/model mismatch. Resolving an actual ambiguous
new source may require suitable independently resolved imaging or timed ground
photometry showing **which star eclipses**. No suitable unused archive exposure
or guaranteed ground observation has been established here. The current objects
are already published controls, not discoveries awaiting our identification.

## 4. Smallest proposed PRF, injection and empirical-negative pilot

Preserve the M0b periods, epochs, durations and M1 quality/cadence/event rules;
retain all 121 collected pixels and fixed SAP apertures. Use the original three
TPFs, totaling 144,368,640 bytes, by hash. No new astronomical pixels are necessary.
Freeze the new estimator/protocol before any PRF fit or injection outcome is read.

### A. Calibration preflight and known-control diagnostic

Acquire only the twelve listed FITS with one attempt each: 300,000-byte/file cap,
4,000,000-byte total cap, 30-second socket and 45-second process-tree deadline per
file. Record exact URLs, HTTP sizes, streamed bytes, hashes, headers and any partial
failure. No model substitution if VERSION, identity, grid or coordinate checks fail.

Replace the Gaussian only in a **new** diagnostic with a continuously interpolated
PRF plus constant/x/y plane. Use a deterministic, catalog-independent initialization
and bounded optimizer; fix these details in code/tests before data fitting. Fit
the unchanged day-block difference images and retain residuals, fits and failures.
Report leave-one-day-out stability as persistence, not independent confirmation.
Compare fixed-position hypotheses for the provisional target and all catalog
alternatives in the stamp, not just the nearest convenient competitor. Do not
convert correlated weighted residual differences into a chi-square probability.

### B. Injection stress test, with model mismatch exposed

For each field with a valid catalog, preselect three injection locations from
catalog geometry alone: provisional target, closest listed alternative to that
target, and brightest other G source within one pixel of that target. Deduplicate
without replacing missing cases. Do not choose positions from a new fitted centroid.

At each location use amplitudes 0.5, 1 and 2 times the retained M1b **fixed-SAP
decrement** (4.560365814, 4.242996517, 4.834921325 e-/s respectively). Scale each
injected PRF to that decrement through the unchanged aperture; it is not a physical
fractional eclipse depth. Inject only at fixed +0.25-period event centers, using
the off-event exclusions below, before the paired estimator; retain the actual
errors, gaps and whole-day covariance. Do not switch phase if coverage fails.
Use 20 seeded whole-day resamples per condition, seed 20260912.

Use each of the four bracketing grid PRFs in turn as the injection shape at the
same subpixel position, while fitting the field-interpolated PRF: at most
3 locations x 3 amplitudes x 4 shapes x 20 resamples x 3 fields = **2,160 trials**.
This tests model sensitivity, not an observationally justified distribution of
PRF errors: grid corners are not independent epoch/color calibrations. Separate
identical-model injections belong in software tests and must never count as
empirical localization validation. Do not treat the PRF uncertainty image as a
known independent-pixel random-error covariance without documentation.

Report signed x/y bias, radial errors, bound/failure fraction, uncertainty coverage,
and the complete target/competitor confusion matrix at every amplitude and shape.
Count optimizer failures as failures, not discarded trials. A proposed diagnostic
stop is any target/nearest-neighbor confusion above 5% at the observed amplitude
in any shape family, or systematic displacement exceeding half their separation.
Passing these deliberately small stress tests does not certify a 1% false-association
rate. Even zero errors in 20 independent trials permits about 14% at the one-sided
95% binomial upper bound; our resampled trials are not independent in that sense.

### C. Actual-data negative windows, not Gaussian noise

Use fixed phase offsets 0.20, 0.25, 0.30, 0.70, 0.75, 0.80 of the retained period.
Before pairing, exclude samples within one retained duration of primary and
half-period event centers, including all in/side windows. These exclusions protect
against known eclipses but do not assume the binary has no other variability.
Never repair a failed phase by choosing another. Require the existing 20-event,
10-day and valid-pixel thresholds. Apply the same paired estimator to unmodified
FLUX and FLUX_BKG, giving at most 18 aggregate off-phase tests, plus the injected
versions above. Keep all signed amplitudes; fit positive and negative structures
symmetrically for diagnostics. Retain the M1 three-error phase flag and its
background-coherence definition rather than tuning them on these data.

These are empirical **within-field** negative diagnostics: they retain real
cadence/noise/background and can expose false localization. Their overlapping
windows and common day blocks are correlated. Report overlaps and failures, not
18 independent nonvariable stars or a population false-alarm rate. If these fields
show off-phase structure or insufficient clean windows, stop the proposed null
calibration instead of subtracting a fitted eclipse to manufacture a null.
An unknown survey still needs separately preselected real negative fields and
search-wide trial accounting; this small test cannot supply that gate.

### D. Hard execution envelope and terminal labels

Proposed ceiling: 19 MB new network responses (15 MB catalogs + 4 MB PRFs), no
new LC/TPF; at most 720 seconds of serial network-worker deadlines, 1,800 seconds
total analysis and 600 seconds per field, 2 GB analysis memory and 100 MB new
outputs. These are caps, not benchmarked runtime promises. Use process-tree
cleanup, bounded optimizer evaluations and streamed receipts; stop at the first
budget breach and preserve incomplete results. Plot/render verification is local.

Terminal labels should distinguish `STOP_CATALOG_PARITY`, `STOP_COORDINATE_MAP`,
`STOP_PRF_PRODUCT`, `STOP_NULL_STRUCTURE_OR_COVERAGE`, `STOP_LOCALIZATION_CONFUSION`,
`STOP_RESOURCE`, and `DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE`. No label sets
`unknown_search_authorized=true`. Exact new implementation choices and synthetic
acceptance tests must be finalized in a separate frozen protocol before execution;
this proposal is not retrospective preregistration.

## 5. What remains regardless of the pilot outcome

PRF localization does not repair the third control's negative absolute baseline:
12.63% of SAP samples are negative, with median SAP 4.175 e-/s against modeled
aperture background 391.294 e-/s. No physical PDC depth should be inferred.
[M1b result and limitations](M1b-RESULT-2026-09-12.md)

The smallest useful advance is therefore bounded metadata recovery plus measured
localization sensitivity, not another unconstrained search. Population negatives,
absolute registration/astrometric uncertainty, color/epoch PRF systematics,
background zero point and unresolved-source evidence remain separate gates.
The [sector-106 incremental-coverage opportunity](../DISCOVERY/TESS-INCREMENTAL-COVERAGE-2026-09-12.md)
is a possible later sample, conditional on these validity checks and its own
source-specific novelty review. None of this guarantees a new discovery.
