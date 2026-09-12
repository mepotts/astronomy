# M2: same-data common-beam and empirical-control calibration

Status: frozen before real M2 outputs, 2026-09-12. This is method development on
already inspected data, not a blind discovery search. Only the six retained full
QL2.1/3.1/4.1 planes and existing known VT1137 target/references are allowed.
No network, extra input, unknown-target search, or changes to old files.

## Exact sample and split

The companion m2-plan.json fixes exactly 200 sky positions, using the QL3.1 FITS
header only: zero-based pixels x=200+240*c, y=200+240*r, c=0..13, r=0..14,
row-major, first 200 entries. Convert those positions through the retained header
WCS once; record all coordinates. Development/held-out split is spatial-block
checkerboarding: (floor(r/3)+floor(c/3)) modulo 2 is 0 for development, 1 for
held-out. Stratum index is sample_index modulo 5: constant celestial fluxes
0.3, 0.5, 1, 3 and 10 mJy, exactly 40 trials per stratum before exclusions.
Each location supplies a blank-sky measurement and one constant-source triplet.
Those paired measurements and repeated epochs are not independent sky trials.

Apply screening on original QL3.1 only, before M2 cross-epoch measurements:
exclude a grid location within 45 arcsec of the known target or one of the fixed
12 reference positions; within 45 arcsec of a parent-plane edge; with nonfinite
data/nonpositive RMS in its 89x89 native patch; or with any native image/RMS
response >=5 within 15 arcsec of its centre. Record every reason and never replace
an excluded location. A finite source or artifact appearing in a different epoch
is retained, not retrospectively masked. No manual blank-sky selection.

## Geometry, units and numerical tests

Use a circular common beam of 3.5 arcsec FWHM. Compute each local WCS Jacobian
from celestial east/north offsets of neighbouring pixels; construct native
Gaussian covariance from header BMAJ/BMIN/BPA. Require target-minus-native
covariance positive definite. Kernel support is 8 sigma, sampled at native pixel
centres and normalized to unit sum. Convert Jy/native-beam to Jy/pixel, convolve,
then convert to Jy/common-beam. Process 89x89 local patches only; require enough
valid interior after convolution for the original 30-arcsec photometry patch.
No resampling onto another grid and no NaN filling. Record any geometric failure.

Before real measurements, noiseless point-source tests must pass at phases
0,0.25,0.5,0.75 pixels in both axes, each of the three native beams and 5 fixed
locations (centre and four inset corners). Every recovered amplitude must agree
within 1%, peak offset <=1 arcsec (a diagnostic on a 1-arcsec pixel grid), and
flux-normalized kernel sum within 1e-12. Include negative covariance, wrong
units, missing pixels and wrong-WCS-handedness tests. Failure stops M2; no kernel,
phase subset or beam adjustment after a failed test.

## Measurement and morphology

Use existing immutable fixed-position beam-template photometry and 15--25 arcsec
background annulus on common-beam patches. Noise proxy is the common-image
annulus's 1.4826*MAD, not an independently propagated per-pixel RMS. Record the
actual empirical null distributions; do not claim this proxy is a posterior error.
Never divide noise by sqrt(Npixel), and do not convolve an RMS map with a
white-noise assumption. Injected point sources use each epoch's native beam
and the same celestial flux, before common-beam convolution.

For the known target, original 12 references and original 8 nulls, report native
and common measurements. Reference morphology pass requires common-beam
residual/noise<=3 and peak offset<=1.5 arcsec in all epochs; exclusion must not
depend on flux ratios. At least five common morphology-passing references are
required. Retain all 12 source records and rejected counts. Report fixed alternate
RA-rank halves and leave-one-out scales without picking the better set.
This all-epoch common-beam morphology gate is an explicitly new M2 quality test;
M1 selected morphology in native QL3.1 only. It is frozen before real M2 outputs,
and does not use cross-epoch flux ratios to choose reference sources.

## Explicit selection-conditioning test

Do not run a global top-12 selector on 200 simultaneous injections: that would
make artificial sources compete with each other. Treat each injection separately
against the unchanged original QL3.1 field. The reference-only blank screening
precludes a pre-existing >=5-noise peak near the injection; all 12 original
references are >=45 arcsec away, so the localized injected model cannot alter
their peaks or their pairwise-separation ordering at numerical precision.

Evaluate each injected native QL3.1 candidate at its brightest pixel within
3 arcsec using the original cuts: it must also equal the 21x21 local maximum
in the injected reference image, peak/native RMS>=15, peak<0.1 Jy/beam,
fixed beam-template residual/noise<=3, and original edge/separation conditions.
Compute its global rank against the *original 12 selected peak brightnesses*;
rank<=12 and all local cuts are necessary for entry. Ties lose to an original
reference. This is an exact insertion into the original selected top-12 list
under the stated isolated-insertion conditions, not a recovery claim for faint
controls that never enter that bright reference list. If isolation or baseline
selection identity fails, mark selection test invalid rather than approximate it.
Report all injected measurements unconditionally, separately conditioned on local
eligibility and global selection. Empty selected strata are NOT zero bias.
The finite-support synthetic model is zero outside its 89x89 patch.

Pre-output parent-authorized clarification: reapply the original target/edge and
selected-reference separation criteria at the selected QL3.1 peak pixel, using
the original selector's full-plane pixel-scale convention, as well as its 21x21
maximum-filter test. Report unconditional injected triplets at true positions
AND additional triplets measured at the frozen selected QL3.1 coordinates while
keeping the injected source at its original true sky position. Conditioned bias
must use those selected-position measurements, including centroid-selection
effects. Separately report native local eligibility, global top-12 entry and
global entry plus final all-epoch common morphology eligibility. A failure after
original-data screening stays in denominators and invalidates selection testing;
it is never recast as an allowed blank-screen exclusion. Empty selected strata
have unmeasured bias, not zero bias.

## Promotion thresholds (fixed before outputs)

- All numerical geometry/flux-conservation tests above pass.
- Known target positive amplitude/noise>=5 and peak offset<=1.5 arcsec in all
  three common-beam epochs; no original fixed null |amplitude/noise|>=5.
- At least 5 common morphology-passing references; at least 3 in each fixed
  RA-rank half. Half-scale discrepancy <=10% relative to their mean in each
  epoch; every leave-one-out scale differs <=5% from the full-reference median.
- At least 60 held-out grid locations remain usable in every epoch and at least
  10 held-out examples per flux stratum. Any failed injection remains a failure,
  never dropped from its stratum's denominator.
- Held-out unmasked nulls: |median signed response|<=0.5 and normalized robust
  scatter<=1.5 in each epoch, and zero |response|>=5. Also report development
  values, contamination/exclusion rates, all tails and spatial-block summaries.
- For held-out 3 and 10 mJy injections: >=95% recover at amplitude/noise>=5 and
  peak offset<=1.5 arcsec JOINTLY in all three epochs, with failures retained in
  the triplet denominator. Also retain each per-epoch recovery rate. Absolute
  median fractional flux bias
  <=5% per epoch. Lower strata are reported without a minimum recovery gate.
- Never tune using development results during this execution. Both splits and
  all predetermined gates are reported. Stop at STOP_M2 if any fixed gate fails.

Strongest label: COMMON_BEAM_CALIBRATION_FEASIBILITY. No discovery, validated
variability, population completeness or unknown-search readiness. Nulls share
field/epoch systematics; per-pixel, per-epoch or reused-location counts do not
create independent trials. Report spatial block counts and scatter; no unjustified
survey-wide false-alarm extrapolation or bootstrap precision from few blocks.

## Bounds and replay

Hard 30-minute worker bound through the tested tree-aware helper in owner context;
runtime checks <=2 GB peak working set and <=200 MB new derived outputs. Keep
local patches/results only, process at most one full epoch at a time, and never
save hundreds of injected mosaics. Scientific functions, raw hashes, plan,
protocol, helper and executing script hashes bind all outputs. Full replay must
match scientific outputs exactly; timing/memory are a separate execution receipt.
If limits or fixed gates fail, preserve outputs and diagnose without retuning.
