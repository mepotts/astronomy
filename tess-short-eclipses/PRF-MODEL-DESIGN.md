# Prospective PRF numerical core: synthetic-only development

New PRF-MODEL core for a separately frozen M2p experiment. This design is not
scientific execution, public preregistration or a localization acceptance. No real
PRF array was evaluated during development; the module has no file/network I/O.
The caller must bind the reviewed M2a products and M1/M2n input provenance, enforce
worker/resource budgets, preserve every attempted hypothesis/trial and freeze
scientific thresholds before reading real fits. Earlier artifacts remain unchanged.

## Interfaces and coordinates

`PRFGrid(arrays, rows, columns, origin)` copies four finite 117x117 arrays and
stores read-only copies. Rows/columns are strictly increasing pairs. Corner order:
low-row/low-column, low-row/high-column, high-row/low-column, high-row/high-column.
`origin=(native_column_at_stamp_0,native_row_at_stamp_0)`. All `(x,y)` arguments
are zero-based stamp source positions, not array `(row,column)` order.

`grid.image(x,y,shape,corner=None)` returns `(cropped_model, metadata)`.
`corner=0..3` chooses a single corner for prescribed mismatch injections only;
it does not authorize extrapolation. Otherwise use bilinear field weights at
`origin+(x,y)`, with no blind +44 or +1. Outside the true row/column rectangle
raises STOP_FIELD_EXTRAPOLATION. Stamp dimensions are integers 1..128.

For a detector pixel center `(pixel_x,pixel_y)`, evaluate the stored PRF array at
`(row,column)=(58+9*(pixel_y-y),58+9*(pixel_x-x))`. Thus increasing source x moves
the model peak toward increasing stamp columns, and increasing y moves it toward
increasing rows. This follows the M2a-exporter physical reference CRPIX=59
(zero-based 58) and step1/9. PRF samples are already pixel-response values:
do not integrate another 9x9 box or treat samples as independent sky pixels.
The [official exporter](https://archive.stsci.edu/missions/tess/models/prf_fitsfiles/start_s0004/export_mat2fits.m)
defines the axes/reference; the [MAST tutorial](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/interm_tess_prf_retrieve/interm_tess_prf_retrieve.html)
illustrates interleaved phase extraction. Its phase rounding is not copied.

Use continuous bilinear interpolation of samples and field corners. All 81
ninth-pixel phase combinations must reproduce the exact interleaved samples,
including asymmetric arrays that detect sign/transposition errors. `sample(...)`
exposes unnormalized sampled values for these tests; it is not a normalized fit.

## Finite boundary and normalization contract

The supplied nonzero samples can extend to offsets +/-58/9 pixels. An abrupt
zero outside those outer centers would produce discontinuities. We explicitly
extend the nodal lattice by zero at index -1 and117, then interpolate through
the one-sample exterior interval. Response is exactly zero at and beyond offsets
+/-59/9. This is a declared continuous, piecewise-bilinear finite-support model,
not evidence about actual wings outside the product. Derivatives can jump at knots.

For every source position, evaluate **all integer detector centers** inside that
finite support before normalizing their sum to one. This is typically13 or14
samples per axis depending on phase. Only then evaluate/crop the requested stamp.
Changing the support's included integer endpoints is continuous because entering
or departing samples are zero at the boundary. Return the raw full-support sum,
integer support bounds/shape, field weights, captured fraction and
`lost_wing_fraction=1-sum(cropped_model)`. Never renormalize the crop to one.

The fitted amplitude is total response in this finite model's detector lattice,
**not true infinite-support stellar flux, fractional eclipse depth or isolated
source flux**. Signed PRF samples, if present, are not clipped; their reported
captured/lost fractions are algebraic and may not lie in[0,1]. A nonpositive or
nonfinite full-support sum is an explicit failure. No uncertainty-image covariance
is inferred by this module. The coordinate audit's absolute-registration caveat
and commissioning-epoch/color/model mismatch remain unresolved externally.

## Signed model and deterministic bounded fit

`fixed_hypothesis(image,error,valid,grid,x,y,corner=None)` solves four unconstrained
linear coefficients: signed PRF amplitude and constant/x/y plane. Plane x/y are
centered at the stamp midpoint and divided by dimension-minus-one (minimum divisor1).
Reject fewer than25 valid pixels, nonboolean masks, invalid selected data/errors,
nonpositive selected errors, or rank-deficient weighted design. Invalid pixels
remain excluded rather than filled. Outside-stamp or outside-field hypotheses
return explicit failed records; callers must not discard them.

`fit(image,error,valid,grid)` uses weighted linear variable projection while
optimizing only x/y. The single deterministic, catalog-independent seed is the
maximum **absolute** plane-subtracted valid pixel, with row-major tie breaking;
it is clipped just inside the intersection of stamp bounds[-0.5,n-0.5] and field
bounds. This supersedes the initial unimplemented25-point seed suggestion before
any real computation. Both signs use the same procedure, not positive-only maxima.

Use bounded trust-region least squares with ftol/xtol/gtol=1e-9, relative finite
difference step1e-4 and max_nfev=120. Also enforce a hard480 residual-model-call
cap, since SciPy nfev excludes finite-difference evaluations. Report both counts,
optimizer message, initial position and `optimizer_active_mask` (-1/0/+1 per axis).
As specified prospectively by the root protocol, `bound_hit` is true if either
solver axis is active OR the fitted coordinate is within1e-5 pixel of a bound.
Both tests are numerical solution flags, not true-position classification. Boundary
hits or optimizer failure yield success=false while retaining available fit outputs.
This is a flag on the fitted coordinate, not proof that the true source is away
from an edge. A retained synthetic counterexample (true x=-0.5, amplitude7 and
unit pixel errors) converges at x=-0.499953827694, outside the1e-5 flag distance:
gtol stopping can occur before a boundary coordinate is reached. The flag is not
retuned to this one example. A caller requiring uncertainty regions to remain
inside the stamp must prospectively specify that additional rule; nominal error
ellipses and scientific position-identification remain separate diagnostics.
No alternate seed, catalog-based initialization, clipping or retry is performed.
One local optimum is not a guarantee of the global minimum; failures/confusion
must be counted in the proposed empirical tests. Parent process deadlines remain
necessary; this core makes no real-data runtime promise.

Results include x/y, signed amplitude, plane3, weighted_residual_sum, point count,
model metadata, full predicted `model` image and data-minus-prediction `residual`
(null outside valid pixels). Weighted residual sums are descriptive comparisons,
not chi-square probabilities under correlated errors. Every fit/hypothesis retains
localization_validated=false. Invalid inputs/numerical-rank failures return an
explicit status; successful flat/no-amplitude fits do not imply source detection.

## Nominal centroid covariance, not calibrated astrometry

At the fitted point compute the full six-parameter model Jacobian in order
amplitude,x,y,constant,xplane,yplane. Use fixed1e-4-pixel numerical PRF differences
(one-sided interval if needed at bounds), multiply coordinate columns by signed
amplitude, and divide every column by the supplied per-pixel errors. SVD produces
the algebraic inverse of J-transpose-J without squaring its condition numerically.
Require full rank6, condition<=1e12 and a positive finite centroid2x2 submatrix.
No residual-variance rescaling is applied.

Return `centroid_covariance` or null with `covariance_status`; a failed covariance
is not silently a covered trial. The nominal2D95% ellipse uses quadratic error
<=-2log(0.05), returned as `nominal_ellipse_threshold`. This assumes independent
diagonal pixel errors and local linearity despite bilinear knots; correlated noise,
PRF/WCS/epoch/color errors and absolute astrometric calibration are not included.
It supports only explicitly labelled synthetic/stress coverage diagnostics, not
probabilistic source identification or calibrated95% astrophysical coverage.

Independent synthetic tests must pass before M2p freeze: all81 phase samples,
axes/signs, field corners/bracketing, integer shifts and edge continuity, full
support versus crop, signed fit/plane recovery, error scaling and covariance,
masked pixels, rank failure, bound/evaluation stops and deterministic repetition.
Only the root experiment protocol can specify new real-data measurements.
