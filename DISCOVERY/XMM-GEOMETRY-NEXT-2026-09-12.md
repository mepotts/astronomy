# Minimal XMM geometry continuation

September 12, 2026. Metadata-only proposal, not an acquisition or geometry pass.
Read the [recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md),
[C1 header review](XMM-C1-HEADER-REVIEW.md), and retained C0c2 inventory; inspected
three direct official documentation pages. No product HEAD/GET, array access,
coordinate query or SAS installation. No pointing/WCS values or full cards are
reproduced here. C2 timing/exposure-value work remains independent.

## Recommendation

**Prefer existing per-exposure PPS exposure maps for accumulated footprint
checks, supplemented by the listed attitude timeseries if attempting stable
coverage rather than a static diagnostic.** This is smaller and less error-prone
than constructing a sky exposure map from RAW bad pixels and windows ourselves.
Neither route has yet established that the fixed source, background or negative
regions are usable. Static maps alone cannot validate every 200-s bin.

The next proposed acquisition scope is three specific band-8 map products and
one observation attitude product, after a separately approved exact-size check.
Header inspection must precede a separately specified array/geometry stage.
Keep the already chosen apertures; do not use the maps to move controls into
more favorable regions. No images, light curves, spectra or source-specific
regions are needed for this initial check.

## Exact observed inventory, not guessed availability

Source: `XMM-C0c2-2026-09-12-data/inventory.json`, SHA-256
`6ddb4a357439922dbefaa51e365b53802e6d031d079348706274555f4e063c23`.
All rows below have `exact_bytes: null`; K sizes are rounded directory displays,
not transfer or expanded-memory budgets. No server freshness check was made.

| Proposed product | Displayed size | Intended role |
| --- | ---: | --- |
| `P0884250101PNS003EXPMAP8000.FTZ` | 492K | pn S003 accumulated exposure geometry |
| `P0884250101M1S001EXPMAP8000.FTZ` | 269K | MOS1 S001 accumulated exposure geometry |
| `P0884250101M2S002EXPMAP8000.FTZ` | 401K | MOS2 S002 accumulated exposure geometry |
| `P0884250101OBX000ATTTSR0000.FTZ` | 148K | Observation attitude metadata, not an exposure map |

Their display-size sum is 1310K, only an order-of-magnitude guide. Exact lengths,
expanded sizes, array shapes, units, band definitions and processing settings
remain unknown. A prospective resource contract must set explicit caps rather
than convert these rounded strings into alleged byte lengths.

Each selected exposure additionally lists FITS EXPMAP subsets 1–5, not just 8:

| Exact filename stem, followed by suffix shown | 1000.FTZ | 2000.FTZ | 3000.FTZ | 4000.FTZ | 5000.FTZ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `P0884250101PNS003EXPMAP` | 491K | 492K | 489K | 489K | 499K |
| `P0884250101M1S001EXPMAP` | 269K | 268K | 268K | 269K | 272K |
| `P0884250101M2S002EXPMAP` | 400K | 400K | 399K | 399K | 402K |

Thus each has six FITS maps plus a band-8 PNG, not seven independent FITS maps.
The PNG is not needed. Filename subset 8 is an energy-band identifier, not an
assertion here of the product's actual numerical energy limits; verify headers.
The PPS filename specification distinguishes EXPMAP, merged MEXPMP, observation
OEXPMP, detection masks and footprint regions.
[PPS filename/product definitions](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/pps.html).

Other observed options are not proposed as substitutes:

- `P0884250101EPX000OEXPMP8000.FTZ` (566K) combines observation coverage and
  loses the direct per-camera/per-exposure isolation needed here.
- `P0884250101EPX000OFTPRT8000.ASC` (19K) is an observation footprint region,
  not a bad-pixel, per-CCD or time-resolved mask.
- PN/M1/M2 X000 DETMSK subsets 1–5 are present at 28–33K, and their X000
  MEXPMP subsets 1–5 are present. Detection eligibility and merged products
  should not be silently treated as the fixed exposure's full physical coverage.

## What the maps provide, and the important limitations

`eexpmap` combines calibrated spatial efficiency, bad pixels and relevant
selection masks with per-chip exposure and an attitude histogram, accumulating
onto sky pixels. Input TIME/GTI/CCD/FLAG selections matter. The result is an
energy-dependent integrated exposure, not an unweighted detector-area mask;
broad-band response also depends on the assumed energy treatment.
[Exposure-map algorithm](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

Inference: these products can reveal aperture intersection with low/zero
accumulated coverage, gross window edges and chip gaps without using photon
occupancy. They can support a fixed-region interior/edge classification.
Positive accumulated exposure only proves some contributing exposure, not
continuous exposure or constant local response. Do not divide the map by its
maximum and call that a geometric area fraction, and do not use a spatial
exposure-map integral as the 200-s live exposure for every bin.

The matching documentation notes that event-coordinate randomization and
attitude rebinning can affect map/event edge correspondence; its exact matching
guidance depends on processing settings. Do not shift maps to fit observed
counts or assume a universal one-pixel border cures every mismatch.
[Map/event coordinate matching](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node4.html).

Already retained BADPIX/window metadata are valuable checks but live in detector
coordinates. Event sky WCS is not a complete time-dependent RAW-to-sky transform.
Building an independent exposure map would additionally require calibrated
detector geometry and attitude projection. The existing PPS maps contain the
pipeline's projection and exclusions; they are therefore the practical starting
point, subject to validating their provenance and compatibility with our masks.
**Photon-empty image pixels are never evidence of no exposure.**

## Smallest defensible geometry stage after header validation

1. Verify each map's observation, camera, exposure, band, units, image WCS,
   processing/version and TIME/GTI/FLAG provenance against C1/C2. Do not assume
   PPS source-detection GTIs equal the full event-list GTIs: flare filtering may
   make the map an integrated diagnostic over a different time selection.
2. Freeze the geometry algorithm before map-array inspection: local published
   centre, unchanged aperture/annulus/control offsets, deterministic pixel-area
   treatment and reporting of unsupported/partial regions. Validate map/event
   sky transformations without printing their coordinate values. Use retained
   source-list geometry columns only under a separate allowlist for fixed
   contaminant exclusions; do not inspect its variability/flux columns.
3. For each fixed region, report invalid/zero-coverage intersections and distance
   to problematic map boundaries at actual map resolution, retaining fractional
   boundary pixels. These are geometry diagnostics, not point-source encircled
   energy or physical-flux corrections. Binary support can miss partially exposed
   or attitude-smeared bad pixels; preserve that limitation.
4. Inspect attitude time/quality and relative movement over relevant CCD GTIs,
   with coordinates local. Establish a conservatively justified displacement
   envelope including rotation over each region and map/WCS uncertainty.
   A fixed aperture safely interior to supported coverage throughout that
   envelope is more defensible than a region touching a moving edge. Static
   maps plus movement do not reconstruct time-dependent bad-pixel losses;
   unresolved local structure still prevents a stability claim.
5. If headers lack compatible masks/GTIs, attitude lacks adequate quality/time
   support, or any required region's geometry cannot be bounded, report that
   specific incomplete outcome. Do not automatically fetch all maps, reprocess
   ODFs, optimize apertures or waive the fixed negative-control requirement.

The exposure maps may be sufficient for a **static coverage** diagnostic; a
clean temporal control requires C2's per-CCD exposure validity plus the
additional stability evidence above. A diagnostic stage can finish usefully
even if temporal stability remains unresolved. This is not discovery validation.

## Exposure-semantics refinement from the geometry documentation

The same `eexpmap` description explicitly states that pn TIMEDEL incorporates
mode-dependent out-of-time-event corrections and that map OOTCORR/OOTFRAC
metadata prevent subsequent double correction. MOS uses its TIMEDEL column;
pn uses the keyword. Thus the pn 0.936444 effective/nominal-width ratio must
not be described solely as ordinary readout dead time.
[Exposure-map correction semantics](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

A read-only scan of all 64 retained pn HDU headers found **no OOT-prefixed
keywords**. No exposure-map header is retained yet. The safe scalar ratios are
EXPOSU01 LIVETIME/ONTIME = 0.9990562200546274 and
TIMEDEL/(FRAMETIM/1000) = 0.9364442993631604; their quotient is
0.9373289316110325. Out-of-time accounting is a plausible reason these differ,
not a demonstrated exact decomposition. The documentation does not prove a
later mutation of the retained event file, nor supply the product's exact OOT
settings without its map metadata. Do not normalize away this distinction or
apply a second correction while C2 is testing the retained frame weights.
