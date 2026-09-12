# Prospective control protocol, 2026-09-12

Written before downloading or inspecting science pixels. Metadata-only probing
has established CADC coverage for QL epochs 1.1, 2.1, 3.1 and 4.1 around the
published VT 1137-0337 position (11:37:06.19, -03:37:37.3). This phase is limited
to known-source measurement feasibility. It cannot discover an unknown object,
validate physical classification, measure completeness or confirm secular fading.

## Inputs and limits

- Fetch current CADC metadata and datalinks for this one field. Use only one QL
  science image and its RMS product per independent epoch; never treat SE/QL or
  overlapping mosaics as separate observations.
- Anonymous SODA circular cutouts of radius 0.2 degree centred on the published
  control. Do not fall back to whole-sky downloads or unrelated fields.
- Four epochs, at most eight FITS files, total stored input bytes <=250,000,000.
  Each request has a 25-second socket timeout and a 75-second worker deadline;
  no automatic retry loops. Persist hashes, exact URLs, HTTP metadata and protocol
  hash before measurement. If an RMS product is missing, stop that epoch and
  report it rather than manufacture a survey RMS map.

## Identity and geometry gates

Require FITS science arrays with two non-degenerate celestial axes, finite positive
beam BMAJ/BMIN and finite BPA, BUNIT Jy/beam (case-insensitive), expected VLASS
campaign in provenance, finite observation date, positive RMS, matching image/RMS
pixel grids and celestial WCS at corners/centre. Preserve native beam and units.
Require target at least 30 arcsec from cutout edge, target fitting patch fully
finite, and >=95% finite science/RMS pixels overall. Deduplicate by campaign and
metadata observation ID, and report dates (not processing timestamps).

QL1.1 must use reprocessed v2 if offered; a deprecated v1-only product fails the
identity gate. No affected epoch-4 RFI tile is allowed: T01t03,T01t43,T02t47,
T04t28,T04t34,T05t07,T06t01,T06t11,T06t31. The known field is T10t18.

## Frozen basic photometry and recovery

At the fixed published position fit only an amplitude for the header-beam
elliptical Gaussian, plus subtract the median background in a 15--25 arcsec
annulus. Use all finite pixels within 3 major-axis FWHM. This is a native-beam
point-source amplitude in Jy/beam, equivalent to Jy for an unresolved source;
it is NOT extended-source integrated flux. Do not optimize target position.
Report nearest local maximum within 3 arcsec as a separate localization diagnostic.
Conservative noise proxy is max(median RMS-map value, 1.4826*MAD of background).
Do not divide it by sqrt(pixel count): interferometric noise is correlated.
Recovery requires positive amplitude/noise >=5 and peak offset <=1.5 arcsec.
Report native beam, fit residual/noise, background statistics, offsets, and
per-epoch outcomes even when recovery fails. No noise proxy is a calibrated
posterior error or family-wise false-positive bound.

## Same-field comparison/null ensemble

Select on epoch 3.1 only, before looking at cross-epoch flux ratios: local maxima
with pixel/RMS >=15, amplitude <0.1 Jy/beam, at least 45 arcsec from control and
cutout edges; choose up to 12 brightest separated by >=20 arcsec. Apply the same
fixed-position beam-template measurement and retain only reference profiles with
absolute fit residual RMS/noise <=3. These are comparison candidates, not certified
nonvariable sources. Freeze their sky positions in the report. No re-selection
based on whether the epoch ratios look desirable.

Require >=5 comparison candidates with positive >=5-noise amplitudes in *every*
epoch for a provisional median local epoch/reference ratio and MAD scatter.
Report failures/excluded counts; a smaller ensemble means calibration insufficient.
Compute provisional target ratios divided by the local median only as diagnostics,
not proof of variability. Fixed null positions: offsets (east,north) arcsec
(60,60),(-60,60),(60,-60),(-60,-60),(120,0),(-120,0),(0,120),(0,-120).
Do not relocate nulls if contaminated: flag |amplitude/noise|>=5.

No common-beam convolution or definitive morphology rejection is claimed in this
phase. Different native beams plus unresolved-source assumptions remain a gate
before any unknown-target search. Stop promotion if any identity/recovery gate
fails, fewer than five common comparison candidates exist, or null contamination
occurs. Passing grants only MEASUREMENT_FEASIBILITY, not DISCOVERY_READY.

## Prior art and caveats

- [Dong & Hallinan](https://arxiv.org/abs/2206.11911): known radio transient, proposed
  emerging PWN, published fading from dedicated multi-frequency observations.
- [NRAO QL guide](https://science.nrao.edu/vlass/data-access/vlass-epoch-1-quick-look-users-guide):
  flux-scale offsets, ghosts, phase errors and unreliable extended structure.
- [NRAO epoch-4 update](https://science.nrao.edu/vlass/): new epoch, specific RFI tiles.
- [NRAO access guide](https://science.nrao.edu/vlass/vlass-data/basic-data-products):
  CADC alternate access and distinction between QL and SE products.
- [CADC TAP](https://www4.cadc.hia.nrc.gc.ca/en/doc/tap/): public metadata and products.
- [Chen et al.](https://arxiv.org/abs/2410.06210): strong transient-search prior art;
  radio behaviour alone does not resolve TDE/AGN ambiguity.

Further work, only after separate approval/protocol: common-beam and empirical-null
validation, exact published flux comparisons, independent-observation confirmation,
literature/catalogue novelty checks. Publication and submissions remain human-gated.
