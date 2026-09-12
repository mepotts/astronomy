# Smallest same-data next validation (proposal only; not executed)

Scope: the six already retained full planes and the existing known target,
12 comparison candidates and fixed nulls. No downloads, extra field, new epochs
or unknown-target scan. The target and comparison ratios are already seen:
this remains method development, not blind evidence for discovery.

## 1. Common-beam identity and flux conservation

Proposed target beam: circular **3.5 arcsec FWHM**, wider than all three measured
native major axes (largest 3.085 arcsec). Before convolution, construct the native
beam covariance from BMAJ/BMIN/BPA in celestial tangent-plane coordinates and
require target-minus-native covariance to be positive definite at every evaluated
position. Transform through the local WCS Jacobian; do not assume identical pixel
origins or rotate PA as an image angle without accounting for WCS handedness.

Convert Jy/native-beam to Jy/pixel using pixel area/native-beam area, convolve
with a unit-integral matching kernel, then convert to Jy/common-beam. Convolving
Jy/beam values without the beam-area conversion changes point-source fluxes.
Keep each epoch's native grid and measure at identical sky coordinates; no extra
reprojection is necessary for fixed-position photometry. Track edges and NaNs;
mask any kernel footprint lacking valid input rather than filling it with zero.

Before real-source results, run noiseless injected Gaussian tests over multiple
subpixel phases and across the field. Require proposed 1% point-source amplitude
agreement and 0.1 arcsec localization agreement with the known injection. This
checks numerical handling only. Report kernel support/truncation error and local
WCS distortion; fail rather than sharpen an image or change the beam after results.

## 2. Morphology and reference robustness

Use the existing fixed target, all 12 references and null positions, and the same
background annulus/fitting support rules. At common resolution, compare fixed
PSF amplitudes with a free elliptical-profile diagnostic; report extendedness,
centroid displacement and residual maps. A small formal chi-square from treating
pixels as independent is invalid. Calibrate morphology diagnostics against the
injected-source/noise trials below, not an arbitrary pixel-count degrees of freedom.

Do not discard references because their ratios are inconvenient. First report all
12; predefine any morphology-based exclusion rule using only reference-epoch
shape and simulations, then apply it before re-examining epoch ratios. Require
at least five surviving common references under the existing amplitude criterion.
Because this dataset has already been inspected, no surviving set becomes a
certified invariant calibration population.

As a minimal robustness diagnostic, split the existing references deterministically
by ascending RA rank into alternating halves (six each). Estimate local scale from
one half and evaluate constant-source consistency in the other, then reverse.
Also report leave-one-out scales. Treat disagreement between halves as unresolved
calibration, not a reason to pick the preferable half. Precision targets and any
promotion rule must be set in the execution protocol before new measurements.

## 3. Correlated-noise and selection-bias calibration

Retain the original eight null positions without relocation. Add a fixed,
reproducible grid or hash-seeded list of proposed **200 control sky positions**
inside the existing plane. Define edge/known-bright-source masking using reference
epoch only and record every excluded position. Position spacing should exceed
several beams, but do not assume this removes tile-scale calibration or sidelobe
correlations. Evaluate both signed responses and robust distribution tails.

Use the actual common-beam images' forced-amplitude background distributions,
stratified by local RMS/bright-source environment. Do **not** convolve an RMS map
as though pixel errors were independent, use sqrt(Npixel) errors, or count every
convolved pixel as an independent trial. Spatial block resampling can expose
field-level instability; the few blocks in one plane limit its precision.

Inject proposed **200 constant point-source triplets** at those pre-fixed control
positions into copies of the three native images, then perform the complete
convolution/measurement chain. Use fixed flux strata spanning the known target's
~5-noise regime and the references' >=15-noise regime. Re-run the *same reference
selection* on the reference-epoch injected images, retaining failures as well as
successes. This directly measures flux boosting, centroid-selection effects and
the bias introduced by selecting references on QL3.1; injecting only into a final
light-curve vector would not test these effects. The same celestial flux is used
across epochs, with each epoch's beam/units correctly applied.

Separate development and held-out control positions by fixed spatial blocks so
threshold tuning and evaluation are not performed on the same injected objects.
Mask contamination by a predeclared rule, never by whether a null has a large
response. Report both unmasked and rule-masked counts and the effective usable
sample. Multiple trials at one noisy sky location are not independent controls.

## Interpretation and cost

Only success label proposed: **COMMON_BEAM_CALIBRATION_FEASIBILITY**. Do not
claim target variability, historical fading, completeness or discovery readiness.
Two hundred independent nulls with zero false alarms would still only constrain
the false-alarm probability at roughly the percent level; correlated samples are
weaker. That cannot calibrate a large unknown survey. Any future search needs a
prospectively fixed trial count, population and multiple-testing criterion plus
enough held-out empirical controls and independent observing confirmation.

No extra input storage; existing retained data remain 383,028,223 bytes. Proposed
compute is CPU convolution and local fitting, processing one epoch at a time;
bound work before execution and avoid saving hundreds of full injected mosaics.
Temporary model patches and convolution kernels suffice. Exact runtime and memory
use have not been benchmarked. Stop on failed geometry/flux-conservation tests,
unstable calibration, inadequate surviving references or insufficient empirical
control coverage; no automatic new-field expansion.

This is a proposal awaiting parent review and a full execution specification.
