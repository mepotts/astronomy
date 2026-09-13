# RXJ geometry: supported SAS path and next access boundary

**Recommendation: after M4 establishes usable exposure identities, freeze one
fixed event-product/header-and-calibration-inventory acquisition boundary for
pn and both MOS cameras. Do not yet decode EVENTS, implement a private RAW-to-
sky calibration, request every map, or install SAS/CCFs.** The supported route
below is concrete, but current RXJ product availability, sizes and local SAS
feasibility remain unverified by this task.

This note follows the adopted
[joint-region calibration direction](XMM-CALIBRATION-NEXT-DECISION-2026-09-13.md)
and the unadopted [source-specific recovery draft](XMM-RXJ-RECOVERY-DRAFT-2026-09-13.md).
The published centre, all four negatives, radii/exclusions, pn-plus-MOS and
minimum-two-negative requirements are unchanged.

## What the existing helpers do not provide

The inspected `xmm_event_geometry.py` maps already selected event X/Y through
table TAN WCS into fixed sky-region membership. `xmm_map_support.py` samples
positive/zero/nonfinite static map support. `xmm_attitude.py` describes sampled
relative motion. These are useful separate components, but none supplies a
calibrated sky-to-RAW/CCD/window map or time-dependent bad-pixel acceptance.
Combining their outputs does not manufacture that missing transform. No actual
arrays, header coordinate values or private HTML were read for this note.

## Smallest documented coordinate/area route

**1. Region-to-CCD mapping: `ecoordconv`.** The task explicitly returns
DETX/DETY, RAWX/RAWY, central CCD and the CCDs intersecting an input region.
This is a supported conversion from fixed sky geometry, not a map inferred
from where photons happen to land.
[Description, Table1](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node3.html).

It requires a suitable detector- or sky-coordinate image carrying the expected
primary-header astrometry. Standard pipeline/evselect images are documented
inputs; the source-image section explicitly says exposure maps and spline
background maps require preprocessing. The referenced current comments page
does not supply a concrete exposure-map preprocessing recipe. Therefore prefer
an identified standard pipeline image if later needed; do not claim a minimal
Astropy TAN header or an unchanged EXPMAP is automatically equivalent.
[Source-image requirements](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node5.html),
[current comments](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node14.html).

Its warning defaults matter: unknown SUBMODE can become PrimeFullWindow,
missing INSTRUME can become MOS1, and incomplete reference keywords can receive
defaults. A future wrapper must reject these conditions before trusting output,
not let a numerical CCD label conceal missing calibration metadata.
[Explicit warning behavior](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node10.html).
The documented conversion is not by itself a proof that every mapped detector
pixel is live, nor a trajectory over the whole observation.

**Frame ambiguity remains:** the task's Regions page explicitly labels its
celestial input `FK4 2000`, whereas the repo geometry helpers use FK5/J2000.
Those words must not be treated as an authenticated identical convention or
silently corrected as a typo. Root independently checked this page as well.
Before any future call, establish the actual version's celestial convention
from supported implementation/calibration evidence. An authenticated X/Y input
route may avoid direct celestial-parameter ambiguity, but requires matching
the image's nominal-reference/POS convention to the local WCS, not merely
copying numerical X/Y or RA/Dec values. No new coordinate transform or software
installation is adopted here.
[Accepted coordinate systems, Regions subsection](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node6.html).

**2. Usable area: `backscale`/`arfgen` geometry, with event bad-pixel metadata.**
`backscale` measures a spectrum's selected region minus CCD gaps and bad pixels;
its bad-pixel location is normally the event file. It distinguishes pure
geometric area from masked area, uses a finite grid, and writes BACKSCAL into
the spectrum. It is not a pure no-write arbitrary-region query. Do not run it
on frozen inputs or invent a dummy spectral product without a separate tested
contract. It identifies the supported area calculation we need, not a reason
to extract science spectra now.
[Description and numerical resolution](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/backscale/node3.html).

**3. Region/time acceptance: `eexpmap` plus per-CCD timing evidence.** The
documented calculation uses CAL/CCF field-of-view and spatial-response data,
event BADPIX/OFFSETS/EXPOSURE, image selection metadata/GTIs and attitude.
FLAG-selected borders and bad-pixel surroundings matter. Sky projection
accumulates rebinned-attitude contributions; an observation-integrated product
does not identify each200s bin's acceptance. Its PI midpoint approximation and
pn OOT treatment also prevent treating any convenient map as a universal
denominator or applying a second generic duty correction.
[Algorithm and selection handling](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

The input-file page explicitly lists an EPIC image with instrument/mode/filter/
GTI/WCS, an atthkgen attitude file, and event EXPOSURE/BADPIX extensions. It has
an outdated-looking statement that other DSS filters are not implemented,
whereas the description enumerates supported filters. Resolve the actual
installed-version behavior with a bounded synthetic/metadata fixture rather
than assuming either sentence authenticates an older PPS exporter.
[Input files](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node7.html).

## Concrete resources, not a demand for all ODFs

The required *kinds* of input are known; exact RXJ filenames/versions/bytes are
not supplied by this research:

| Resource | Why needed | What must be checked before use |
| --- | --- | --- |
| Selected pn/MOS imaging event products | Camera/exposure metadata; per-CCD BADPIX, window/offset information, GTI and EXPOSU lineage | Actual extensions, dimensions, units, flags, timing and calibration inventory; do not assume the first control's schema |
| Standard same-exposure pipeline image | Supported astrometric input to region-to-CCD conversion | Required primary/reference/instrument/mode cards and provenance; no intensity-based geometry selection |
| Observation attitude product | Sampled pointing/roll and time matching | Actual time reference, quality, camera alignment and sampling limitations |
| Relevant calibration index and referenced CCF constituents | Calibrated detector geometry/FOV and other task-specific CAL dependencies | Exact constituent names/versions, availability and coherent calibration context, not just an index filename |
| Observation source-list geometry fields | Fixed control association and union of other-source exclusions | New row/schema limits and ambiguity; no flux/variability selection |

The pn pipeline output specification explicitly includes BADPIXnn, EXPOSUnn,
STDGTInn, OFFSETS and CALINDEX listing relevant EPN/XRT3/XMM CCF entries.
This is a good reason to inspect the event product's metadata first, not proof
that every delivered RXJ PPS file retains identical contents or that a CALINDEX
contains the referenced calibration files themselves.
[EPIC-pn output specification](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epchain/node14.html).
For MOS, inspect the actual product's retained equivalents; do not invent
constituent names or copy pn alignment/correction constants.

The supported route requires an operational compatible SAS/CAL context and the
referenced calibration resources. This task neither tested nor installed that
environment. Documentation of a task is not evidence that it runs in the current
Windows workspace. A full ODF mirror is not established as necessary merely
because these tasks need calibration and attitude; a small metadata inventory
can determine which specific resources are missing before any deployment choice.

## Relative timing and the important multi-CCD limit

The current `epiclccorr` documentation uses per-CCD GTIs, FRACEXP from EXPOSUnn,
and mode frame/live-time information for relative corrections.
[Relative corrections](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epiclccorr/node6.html).
This supports matching actual mapped CCDs to the frame tables, not using a
global LIVETIME or CCD membership inferred from EVENTS occupancy. The existing
[exposure-semantics note](XMM-EXPOSURE-SEMANTICS-2026-09-12.md) preserves the
remaining exporter and boundary-allocation issues.

For regions spanning CCDs, `epiclccorr` explicitly needs per-CCD effective area
and describes a point-source assumption; it warns about substantial background
contributions. Thus geometric area fractions alone are not generally the
point-source PSF weights, and point-source weights are not a justified model
for a diffuse annulus or a negative aperture.
[Multi-CCD algorithm and limitations](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epiclccorr/node4.html).

Practical inference: if a fixed source circle is shown to remain safely within
one usable CCD and its relevant acceptance is stable within a prospectively
justified uncertainty, its per-CCD relative timing is the simpler case.
Annuli/negatives may still span CCDs and require separate geometric/background
weights. Do not relocate them to force this simplifying case. If boundaries
matter, use the supported calibration path or report the exact incomplete
acceptance; no inferred empty-pixel mask or count-fitted efficiency.

## One next acquisition boundary, conditional on M4

After M4 supplies explicit same-observation exposure IDs and relevant product
references, parent can freeze **one header-only acquisition stage for the
fixed pn and two MOS imaging event products**. Keep both MOS slots and every
failure; do not choose a camera using photon results. Resolve exact documented
selectors/returned product identities and conservative transfer/expanded caps
before that stage. Missing product references/ambiguous exposures require a
specific metadata decision, not guessed filenames or a wildcard bundle.

The permitted inspection should stop at structural headers and a separately
allowlisted calibration-index inventory, if present. CALINDEX rows are metadata
but still need an explicit byte/schema budget before reading; they are not
automatically part of a generic FITS-header pass. No EVENTS, BADPIX, GTI or
EXPOSU values, maps, catalogue values or attitude values in that acquisition
stage. Compressed transfer/expansion/hash I/O remains fully accounted even
though scientific arrays are not interpreted.

Its result should answer: which exact camera modes/CCDs/window descriptors and
ancillary tables exist; which calibration files/task versions are referenced;
and whether the documented conversion path can be supported locally. Only then
request a missing standard image/attitude/source-list or named CCF inventory
under explicit caps. A coordinate-conversion smoke test with already fixed
regions can follow a reviewed environment decision; it must not silently read
science arrays or expose coordinate-bearing SAS console output.

This ordering deliberately defers unnecessary map variants and full reprocessing.
It does not promise three event products are presently obtainable, replace the
joint-region gate, or make metadata-only success a recovery pass. No archive
query, scientific product/private HTML read, download, installation or code edit
was performed. Research was confined to existing design/helper source and the
referenced official SAS task documentation.

## Parent disposition

Root read this complete note and independently opened all cited SAS pages.
Adopt the supported-calibration direction and conditional three-camera
event-header/inventory boundary, subject to actual M4 identities/references
and a finite acquisition contract. No product request, CALINDEX row read,
software installation or coordinate conversion is authorized by this note.
The frame/default/DSS ambiguities and missing calibrated detector transform
remain explicit; existing sky-membership helpers do not resolve them.
