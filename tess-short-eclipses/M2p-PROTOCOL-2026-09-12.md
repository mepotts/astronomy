# M2p: continuous PRF and real-noise localization stress test

Prospective stage after M2a acquisition and M2n fixed off-phase results. No PRF
fit or injection outcome may be inspected until this protocol, numerical core,
driver and author/independent tests are reviewed, committed and hash-bound.
This is local prospective ordering, not public preregistration. Prior frozen
protocols/results remain unchanged. No requests or unknown targets are allowed.

## Fixed population, prerequisites and coordinate contract

Use all three existing known controls, order450781262,53206761,2041210548, with
unchanged LC/TPF bytes, M0b ephemerides, M1 cadence/error/quality rules, SAP aperture,
event estimator and original day anchor. Require exact original primary image,
event/day counts and SAP statistics, and all six M2n FLUX/background diagnostics
to replay BEFORE any PRF fit. All PRFs must pass unchanged M2a structural replay.
Hash-bind all required prior inputs and complete execution receipts plus new code,
tests/protocol and model design. Use existing M1b catalogue for first field and
M1e catalogues for the others; no new positions or uncertainties are queried.
The previously propagated epoch/positions and all stamp rows are fixed inputs.

Use direct SPOC physical origin plus zero-based stamp position, without +44/+1.
This follows the coordinate audit and its retained absolute-registration caveat.
The experiment measures sensitivity under this documented mapping, not a validated
absolute sky-position confidence region. A residual shift is not permission to
adjust the origin or choose a convention on fit outcomes.

## Frozen numerical estimator

The separate PRF-MODEL-DESIGN.md specifies/test-binds exact interpolation and
optimization. Four corner images, ordered low-row/low-column, low/high, high/low,
high/high, are bilinearly weighted at native origin+(x,y). Subpixel evaluation uses
continuous bilinear sampling at indices58+9*(pixel-position minus source-position).
The finite array boundary has an explicitly documented one-sample zero-node
linear taper. Normalize on complete finite detector-pixel MODEL support before
cropping to11x11; retain captured/lost fraction. This is not an infinite-support
stellar flux calibration. No clipping, re-aperturing or uncertainty-image noise
interpretation is permitted.

Fit signed amplitude times PRF plus constant/x/y plane, with a single deterministic
catalogue-independent initial position: largest absolute plane-subtracted valid
pixel, row-major tie ordering. Nonlinear variable-projection least-squares varies
only x,y within stamp/grid bounds; linear amplitude/plane are unconstrained.
No target-coordinate seed, multistart, retry or sign selection. At most120
nonlinear evaluations per fit. Keep solver failures/bounds/rank diagnostics.
The bound flag is numerical: solver active bounds or fitted distance <=1e-5pixel
from a bound. A false flag is not proof that the true source is away from an edge;
the core design preserves a noiseless edge counterexample illustrating finite
optimizer tolerance. Nominal ellipses are not used to certify edge separation.
The diagonal weights are the corresponding original day-block standard errors;
do not rescale errors to obtain a desirable residual or confidence.

Record local full-six-parameter weighted-Jacobian inverse covariance without
residual rescaling, extracting centroid2x2 only after nuisance coupling. Singular,
ill-conditioned or nonfinite covariance stays undefined. The nominal95% ellipse
uses quadratic displacement <= -2*log(.05). This is a DIAGONAL-ERROR formal stress
diagnostic, not calibrated coverage of correlated pixels/days, absolute astrometry
or model mismatch. It is not used to claim a source-association probability.

## Known signals and negative-image diagnostics

Fit the unchanged primary mean difference image and every leave-one-day-out mean
using the fixed full-primary error image and valid mask. Retain each fit; no
bootstrap failure is discarded. Leave-one-day-out agreement is persistence, not
independent confirmation. For the primary image also profile the same signed
amplitude/plane at EVERY catalogue row in the stamp. Keep all fixed-position
residual scores, including failures. Rankings are descriptive, not chi-square
probabilities. A nearest-free-centroid catalogue label is a separate geometric
diagnostic and is never called the profile-score winner.

Fit all six M2n FLUX and six background mean images with each channel's original
error/valid mask. Signed amplitudes and the sign-symmetric deterministic seed
retain either sign without selecting a favorable result. Off-phase centroids
are descriptive noise diagnostics, not newly detected sources. M2n quiet aperture
ratios do not establish these PRF fits or a population false-positive rate.

## Locations, injections and paired day draws

Before fits choose: the unique provisional catalogue target, its closest other
stamp source, and the brightest finite-G other source within one pixel of target.
Sort ties by exact integer source ID; deduplicate repeated IDs without replacing
missing roles. Record all role/ID/position choices in the preparation manifest.
Missing/ambiguous target or no alternative is an explicit inability to complete
this control test, not a purity pass. No positions are chosen using new centroids.

Use M2n's fixed primary/half-period exclusions and +0.25-period phase. Inject by
SUBTRACTING each corner PRF from the retained FLUX at eligible in-event timestamps,
BEFORE the unchanged paired estimator. Preserve actual FLUX_ERR, gaps and pixels.
For each corner and location scale by its own fixed-SAP model sum to obtain0.5,1,2
times the exact retained M1b primary SAP decrement. This is an aperture decrement,
not a physical fractional eclipse depth. Nonpositive/nonfinite aperture response
stops that condition; never choose a different aperture/location/corner.

Use20 whole-day resamples per condition. For each field independently initialize
NumPy default_rng(20260912), generate20 arrays of n day indices sampled with
replacement, and reuse these exact draws for all locations/amplitudes/corners.
Keep indices and day labels. Error image/mask remain those of unmodified+0.25
negative blocks for all trials. This preserves paired comparisons, not independent
trials or an observational distribution of calibration errors. Four grid-corner
shapes are stress extremes, not independent contemporary color/epoch calibrators.
Maximum3fields*3locations*3amplitudes*4corners*20 =2160 trials before deduplication.

Each trial reports fit status, signed x/y displacement and radial error, formal
ellipse coverage and geometric nearest-to-free-centroid assignment among ALL stamp
catalogue rows. Distance ties within1e-12 pixel are AMBIGUOUS; failed/bound fits
have explicit FAILED/BOUND columns. Confusion matrices include every catalogue ID
plus these categories, with exactly20 counts per truth/amplitude/corner. Undefined
covariance is uncovered and explicitly incomplete, not omitted from coverage.
An ordinary numerical exception is retained for that draw and the next distinct
draw proceeds without retrying it. Condition-setup failures retain twenty explicit
unmeasured FAILED slots. Recorded, attempted and completed counts are separate;
unmeasured placeholders are never called completed fits.

## Predeclared interpretation and stop rules

Report all conditions and all fields, even after a scientific failure. At observed
amplitude1x, for every shape and injected location, wrong-ANY-catalogue-row fraction
>5% (at least2/20) gives STOP_LOCALIZATION_CONFUSION. This strengthens the proposal's
pair-only check prospectively so mistakes to third sources cannot escape it.
Also stop when norm(mean(signed x/y displacement)) exceeds half the target-to-nearest
separation for either member of that pair. Do not replace this with mean radial
error or nanmean of survivors. Missing/failed/bound/ambiguous fits or undefined
covariance at1x give VALIDATION_INCOMPLETE even if a computed confusion fraction
is small. Report lower/higher amplitudes without selecting them as the gate.
Coverage fractions remain descriptive; no newly tuned numerical coverage gate.

Any failed primary/leave-one-day-out/profile fit is likewise incomplete;
bound primary or leave-one-day-out fits also prevent complete characterization.
Negative-image fits retain failures/bounds/undefined centroids descriptively:
a quiet image need not have an identifiable point-source centroid. Do not turn
that expected null degeneracy into either a detection or a source-purity pass.
the core numerical readiness is not a science acceptance. Confusion STOP takes
priority over an incomplete label, but retain ALL reasons. No result sets
unknown_search_authorized=true. Even a complete stress pass does not supply
population negatives, absolute registration, catalogue completeness, unresolved
or uncatalogued-source exclusion, physical depth or source-specific novelty.

## Resource envelope, provenance and replay

No new network response bytes. Up to600seconds per field/1800seconds serial workers,
using the existing owner-context process-tree helper; <=1GB measured Windows peak
working-set acceptance (not an allocation quota), <=25MB scientific output per
field and <=100MB total new outputs including checkpoints. No new installations.
Reserve 1MB within that 100MB for the terminal outcome summary; ordinary outputs
stop at 99MB. Worker output/error receipts retain at most 16KB text apiece, with
full byte length and SHA-256 when truncated. Preserve the raw worker return code
separately if parent-side completion validation subsequently fails.
Before run: prepare exclusive manifest, commit reviewed source/tests/protocol, then
explicit parent GO for the manifest hash. Exclusive run/worker markers prevent
reruns. Write new data/m2p checkpoints after primary, negatives and each condition
so a later worker/resource failure retains completed evidence. Never alter a
partial attempt; a nonzero worker stops later launches with explicit accounting.

Replay is read-only, verifying exact dependency/receipt closure and successful
worker results/checkpoints by full recomputation under the same time bounds.
Runtime receipts are separate from deterministic results. Failed/unlaunched
workers remain recorded failures, not restarted under the word replay. Synthetic
test success is software evidence only. Results, including failed hypotheses,
must be independently audited before repository integration or choosing new work.
