# Paired empirical diffuse-light depth around ESO197-018

Frozen before DR10/DR11 science pixels. The prospectively selected brick0306m510
adds six physical r exposures (24 CCD footprints). The published table identifies
a known stream but the inspected figure/appendix does not give this object's
usable sky aperture. Therefore measure *depth only*, not stream recovery.
Do not choose a stream aperture by inspecting the images under evaluation.

Retrieve native r image, r inverse variance and maskbits for DR10/DR11 south,
six files <=80 MiB each, 30-second socket timeout. Preserve bytes/hashes and
matching WCS grids (corner plus centre transforms to <=1e-6 deg), expected
3600x3600 shape, image units nanomaggies/pixel and native 0.262 arcsec/pixel.

Use a grid of disjoint 38x38-pixel (~9.956 arcsec square) apertures, starting at
native pixel (0,0), centers 180..360 arcseconds from catalogue host coordinates
(30.6285,-50.9319), without tuning locations to blank-looking regions. Require
every pixel finite, inverse variance positive in both releases, and no combined
maskbits in {0,1,3,6,10,11,12,13}. These are primary-area/bright/saturated-r/
allmasked-r/bailout/medium/large-galaxy/cluster exclusions. No further pixel-value
clipping, detected-source mask, aperture reselection, or fitted background.

Measure each aperture's mean surface brightness flux in nanomaggies/arcsec^2.
Estimate empirical scatter as 1.4826*MAD of aperture means separately for each
release, using exactly the same paired apertures. Report median offsets and
formal inverse-variance errors too; formal errors do not include covariance.
Require >=30 paired apertures and DR11 scatter<=0.9*DR10 for material improvement.
The 3-scatter surface-brightness scale is 22.5-2.5 log10(3*scatter); it is a local
empirical scale, not a Gaussian completeness limit. Residual unresolved sources
and sky structure remain in the scatter. No probability or independent-trial
claim. Upstream sky subtraction can erase streams despite lower sky scatter.

Keep full products ignored. Commit paired fluxes, formal errors, grid positions,
mask acceptance counts, source provenance and the gate result. A depth pass alone
does not authorize unknown-stream discoveries: independent stream aperture,
injection completeness upstream of sky subtraction and prior-art checks remain.
