# Independent map-support numerical checkpoint

September 12, 2026. **Numerical core accepted for the proposed static
approximation; C5 runtime review and execution approval remain pending.**
No actual map pixels, FITS products, attitude/event arrays or network data
were read for this review. Only synthetic inputs, source/tests and the full
[C5 draft](XMM-C5-2026-09-12.md) were inspected. The draft was not frozen at
this checkpoint.

## Verification and exact reviewed code

Read `xmm_map_support.py` and `test_xmm_map_support.py` completely.
Independently reran all 14 synthetic unittest methods successfully and
root-invoked Ruff 0.16.5 passed on both files.

| File | SHA-256 |
| --- | --- |
| Numerical core | `2c93c225223aacedefd8ce160726c9f363e11626823cb8d9ae34a54dfda2307a` |
| Author tests | `6ba990522f625472293700c946475192c7d0ab0b5aaae46f44906143caa20bf6` |

An additional independent inline oracle used NumPy seed 2931 and synthetic
positive/zero/negative/NaN maps. It covered two linear transforms (diagonal
and skew), both fixed regions, and both subdivisions: eight combinations.
The oracle constructed Cartesian gnomonic directions directly from plane
coordinates, measured angular distance with cross/dot `atan2`, and used
`abs(det(matrix)) / (1 + u*u + v*v)**1.5` for its area weights. It did not
call the core's world transform, separation or raster routine for these
oracle calculations. Its search box extended three pixels beyond each edge
of the core's enclosing box.

All five category subpixel counts matched exactly; each corresponding area
matched within 1e-8 square arcseconds absolute tolerance. This is an
independent synthetic arithmetic check, not a measured scientific error
bound. The inline oracle is not an additional committed unittest method.

## Mathematical interpretation

For the restricted undistorted near-axis TAN model, the enclosing radius's
`sec(theta)**2 / minimum_singular_scale` factor appropriately bounds the
largest local angular-to-pixel stretch. Fixed padding and the 256-pixel side
stop prevent unbounded region evaluation. The midpoint solid-angle factor
`cos(theta)**3` correctly converts tangent-plane area to spherical area.
Circle and annulus membership use angular distance, not a fixed projected
pixel radius. Array indexing is row/column while WCS coordinates are x/y.

The five categories partition the sampled region, including samples outside
the image. Changing a positive pixel's amplitude does not change area or
support classification. Each sampled parent pixel is counted once per
category/resolution even if several of its subpixels are selected. Sixteen
base rows are processed at a time; the full input image remains caller-owned.
These are algorithmic shape/chunk bounds, not a measured peak-memory claim.

The author tests also cover longitude wrap, rotated anisotropic transforms,
off-image regions, masked/invalid image input, non-TAN/distorted WCS rejection,
round-trip failure, chunk invariance, and coordinate-free serialization.
No numerical blocker was found for the stated restricted model.

## Approximation and proximity limits

Four and eight subdivisions are both retained; eight is fixed as nominal.
Differences between them and the analytical full spherical area are diagnostic
discretization comparisons, not certified error bounds or a reason to choose
the more favorable resolution. A sampled intersected-pixel count does not
enumerate every arbitrarily small true pixel/region intersection.

The proximity routine searches all unsupported image pixel centres, with
chunked rows, plus image-border samples at one-pixel spacing including
corners. It deliberately does not calculate the true nearest pixel-edge or
continuous-border distance. Radius-subtracted values therefore are not
guaranteed clearance or eligibility. For the annulus, an unsupported pixel
inside its central hole can still be the nearest unsupported centre; that
proximity statistic is not an annulus-intersection test. The separate sampled
annulus category estimates retain their own meaning.

The returned `region_centre_inside_image_rectangle` boolean is solely a
geometric point/rectangle fact. It is not a clean-aperture or coverage flag.
The core's fixed status `STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE` and
interpretive labels correctly avoid those stronger claims.

## C5 alignment and remaining caller obligations

The inspected draft matches the two allowed region types, subdivisions,
chunk/box limits, spherical/Jacobian approximation and modest proximity
semantics. It keeps source-list contaminant exclusions absent, MOS2
unavailable, and map positivity distinct from live or FLAG-zero exposure.
None of these limitations is removed by a successful core calculation.

The parent separately specified that the published ICRS centre will be
explicitly transformed to the maps' declared FK5/J2000 frame before use.
That adoption still belongs in the prospective protocol and runtime tests;
it was not present in the draft read at this checkpoint. The pure core has
no source-frame metadata and cannot validate that relationship itself.
Header-to-WCS construction, RADECSYS/equinox interpretation, units, origin,
fixed spherical negative-centre offsets and private-coordinate serialization
must be tested in the wrapper. This review neither constructs an actual map
WCS nor infers frame agreement from nearly similar numerical coordinates.

One nonblocking input-contract observation was sent to the author and parent:
the core explicitly rejects masked images, but converts centre input directly
to floating point. That permits masked-centre mask loss and numeric-string or
boolean coercion. The parent chose a fixed, prospectively safe numeric caller
rather than treating this as a numerical-stage blocker. The wrapper must
supply its validated two finite numeric transformed coordinates; this
checkpoint does not approve arbitrary user-supplied centre objects.

No runtime source, real-payload decoder, worker accounting, provenance chain,
privacy-safe failure path or actual map result is accepted by this numerical
GO. Those require their separate C5 pre-execution review and freeze. No
exposure calibration, source-free background, continuous coverage, photon
recovery or discovery claim follows from this checkpoint.

## Current draft alignment clarification

Reread the updated C5 draft after the numerical checkpoint above. It now
explicitly adopts ICRS as an uncertain prospective convention, creates the
fixed cardinal offsets there, and transforms them to FK5/J2000 before map
evaluation. It does not present the published position's frame as independently
established or fit a map-dependent correction. The draft also specifies the
primary celestial WCS only, no silent WCS fixes, safe warning handling,
conflicting-primary-representation rejection, and acceptance of absent BUNIT
solely for sign-based support without invented physical units. These additions
resolve the earlier wording-pending observation and align with the pure-core
contract. Wrapper construction/transport-free decoding and their tests still
require independent review; this is not runtime GO. No tests were restarted
or actual pixels read for this wording clarification.
