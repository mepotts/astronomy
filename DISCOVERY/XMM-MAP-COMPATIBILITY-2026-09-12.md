# C3e map compatibility: useful spatial screening, not matched exposure calibration

September 12, 2026. Read-only adjudication of retained pn/MOS1 map headers,
C1 EVENTS headers, C2/exposure notes and the counts-recovery draft. No FITS
array, photon, source-list coordinate or attitude-value reads; no new product
request. Official documentation was inspected for the narrow task/DSS semantics.
This is not a claim that every pipeline version or possible route was searched.

## Decision

**Proceed to a small fixed-region map-support diagnostic, but do not use these
maps as the exposure denominator for FLAG==0, 200<PI<12000 counts.** The maps
have useful accumulated spatial information despite demonstrably incomplete
selection equivalence. A same-aperture counts screening experiment need not
first obtain absolutely calibrated flux or a perfectly matched broad-band map.
Its conclusion must remain detection/recovery screening unless local temporal
response and background explanations are resolved.

The draft still calls FLAG screening an unresolved choice. Here FLAG==0 is the
parent's proposed prospective choice, not an already frozen photon selection.
Do not alter that choice, energy endpoints or apertures to fit these maps.

## Bound retained evidence

C3e outcome SHA-256
`af82c5ae3b7a5cd233589e6bd53eadc8d0ded37137ad6df6dac49d198a581d80`.
Map-header hashes, independently matched to the outcome:

- pn: `ec3d29a2b4c0428cc1e7e382b4521fdca83019dbc4066b63685bac076f1f3a9a`.
- MOS1: `e34274169b7ba4298d12b04b68ba7da197f9b9dada106de2ac7fb773cc93d1e3`.

Both are one-HDU 648x648 float32 sky images with TAN celestial axes and
4-arcsec pixel scale, matching observation0884250101, pnS003/MOS1S001,
Thin1 imaging, PPS21.51 and SAS21 pipeline identifiers. Neither has BUNIT,
TSTART, TSTOP or ONTIME. Do not manufacture those missing cards. WCS reference
coordinates remain private/local and were not reproduced here.

| Check | pn band8 map | MOS1 band8 map |
| --- | --- | --- |
| Creation history retained | imweightadd over five band1–5 exposure maps; two addattribute operations | eexpmap4.12.1 using the matching IMAGE_8000, MIEVLI and ATTTSR; two addattribute operations |
| Energy provenance | Five named constituent bands; no surviving PI DSS | pimin200/pimax12000 for band8, plus PI DSVAL `(200:12000` |
| FLAG/PATTERN DSS | None retained | Two FLAG masks and PATTERN `:12` |
| Time-selection provenance | No surviving DSS/GTI reference | CCD1,2,4,5,7 reference GTI00006,GTI00106,GTI00206,GTI00306,GTI00406 |
| GTI tables physically in map | None | None |
| Scalar EXPOSURE |33730.1879012585, comment max of ONTIMEnn |40974.4891108274, same comment |
| OOT metadata | OOTCORR=true, OOTFRAC0.936444342136383 | Neither present |

The pn EXPOSURE is smaller than C1's maximum per-CCD ONTIME47364.3920340538;
MOS1's is smaller than49418.8922661543. Those are scalar comparisons, not
reconstruction of excluded intervals or proof that background flares are the
only cause. C2 summarized the original per-CCD STDGTIs, not these map/image GTIs.

## Exact selection differences

MOS1 repeats the C1 EVENTS FLAG mask
`b000x00xxx0x0x0x0x0xxxxxxxxxxxxx` and adds
`b000x00xx00x0x0x0x0xxxxxxxxxxxxx`. Neither is literal FLAG==0: wildcard bits
are not all required zero. FLAG==0 is a stricter all-bits-clear selection;
positive exposure under a less restrictive mask does not certify all of its
support survives the stricter mask. No unverified numeric bit-position mapping
or claim of complete EXOD equivalence is needed for that distinction.

DSS filters within a component combine by AND; components combine by OR.
Therefore retain the five CCD/time associations, not a camera-wide OR of all
GTIs independent of CCD. C1 MOS1 references STDGTI01/02/04/05/07; none of the
map's GTI00006-style tables appears in either retained C1 MOS1 or this single-HDU
map. Their naming is not a join to C2. The metadata are incomplete for exact
time-mask equivalence, not evidence that the map is corrupt.
[Official DSS description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/dsslib.pdf).

MOS PATTERN `:12` is consistent with the proposed upper bound12. The retained
PI spelling `(200:12000` is lower-open and upper-unmarked; interpreted with the
usual default-inclusive range endpoint, it corresponds to200<PI<=12000, not
the draft's strict upper bound. This compact DSS spelling was not round-tripped
through the retained SAS executable here. Official selectlib explicitly
distinguishes closed and open endpoints. Preserve the literal DSS and the
one-channel endpoint distinction; neither a quiet assumption of exact equality
nor a change to the draft is justified. It does not block coarse footprint
screening. [SAS interval definitions](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/selectlib/node21.html).

pn has no surviving DSS from which to establish its band-dependent PATTERN,
FLAG or GTI selections. The C1 pn EVENTS DSS records only CCD-specific standard
GTIs, so it cannot restore the map's image-generation selections by itself.

## pn combination and map meaning

The pn retained command names exactly EXPMAP1000 through5000, `withweights=no`,
`weightstyle=user`, and an empty weights list. It is not a direct single-band8
eexpmap history. The official archived MakePNImage pipeline explicitly forms
band8 by unweighted addition of five exposure maps followed by division by5.
That older19.16 pipeline source supports an averaging convention, but the
retained PPS21.51 header does **not** itself record fcarith/division. Thus neither
an exact sum nor an exact mean normalization is independently proved for these
pixels. A common positive divisor would not change binary support, which is why
this uncertainty need not block a support diagnostic.
[Official archived pipeline implementation](https://xmm-tools.cosmos.esa.int/external/xmm_products/pipeline/doc/19.16_20210326_1200/modules/MakePNImage_pm.html).

The current imweightadd manual uses a different parameter vocabulary
(`calculateweights`) and contains both weighted-average introductory notation
and summed-output parameter descriptions. Do not silently replace the actual
`withweights` invocation with a current-manual parameter interpretation or
derive a calibrated broadband exposure from its title.
[imweightadd manual](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/imweightadd.pdf).

MOS1's actual eexpmap command uses vignetting, sky coordinates, attrebin2,
usefastpixelization=no and usedlimap=no. eexpmap accounts for spatial response,
selected bad/border pixels, per-chip exposure and rebinned attitude; it reads
TIME/GTI/CCD/FLAG selection information. Its broad-band efficiency uses an
energy approximation, not an arbitrary source's measured spectrum. pn TIMEDEL
already includes the OOT treatment recorded by OOTCORR; do not apply it again.
These facts support integrated-response interpretation, not seconds of live
time in each200-s bin. [eexpmap algorithm](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

## Smallest actionable geometry step

Freeze a **static support and proximity diagnostic**, not an exposure-calibration
pass, using only the two already retained map arrays under a separate bounded
protocol. Keep the published centre,20-arcsec apertures,60–90 annuli and four
120-arcsec cardinal offsets unchanged. Before pixels, test WCS round trips,
row/column order, pixel areas and fractional region intersections synthetically.
Report out-of-image, nonfinite, negative, zero and positive intersected pixels,
area fractions and distances to unsupported boundaries; keep all five regions
and both cameras. A fixed pixel subdivision can carry a boundary-discretization
error ledger; do not pretend a4-arcsec raster resolves subpixel bad-pixel loss.
No percentile-based relocation or post-map threshold optimization.

Map zeros/edges are useful warning flags; positives are only accumulated support.
Do not divide by a map maximum to obtain valid geometric area or use a summed
map value as a source/background bin exposure. The missing GTIs and stricter
FLAG choice prevent a formal matched-mask certification, but a clearly labelled
screen need not manufacture such a certification to be useful.

Use C4's independently reported sampled motion as an additional diagnostic,
not an unobserved continuous-motion bound. The SAS matching note says exact
sky-image correspondence needs much finer attitude rebinning than MOS1's2;
it does not supply a universal safe one-pixel margin for this product. Report
separation from boundaries at the measured resolution and preserve uncertain
regions. [Map/event matching guidance](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node4.html).

The now-completed [C4 aggregate result](XMM-C4-RESULT-2026-09-12.md) reports51975
finite/domain-valid samples, exact one-second adjacency and all three header
ranges bracketed. Maximum sampled shift from the first direction is1.704arcsec;
maximum adjacent direction/PA changes are1.206/4.724arcsec. This removes the
specific missing-sample/large-sampled-drift concern and makes the static screen
worth doing. It is not a reason to demand unmeasurable continuous proof before
any descriptive counts work, nor to pretend that such proof was obtained.

After this screen, the economical next decision is either a bounded
**published-control raw-count recovery with instrumental/background explanations
unresolved**, or a narrowly justified stricter exposure test. The former uses
integer aperture counts, C2/frame diagnostics, separate backgrounds/cameras and
fixed negatives; it must not advertise calibrated binomial false-alarm
probabilities or intrinsic flux. Constant unknown throughput can cancel in
same-region temporal ratios, but unknown time-variable spatial losses cannot
be wished away. Absolute ARF calibration, all-band reacquisition or full ODF/SAS
reprocessing is not automatically required. A map intersection problem can
make that fixed region unavailable; it does not authorize moving it.

A descriptive counts screen is scientifically useful: it tests whether the
published two-episode morphology is recoverable from the fixed integer-count
streams and whether obvious coincident camera/background/negative-region
activity explains it. **It requires a new prospective, explicitly narrower
contract**, listing the original calibration/geometry gates still unmet rather
than silently marking them passed. Keep the original draft unchanged/unexecuted
as a distinct intended validation level. Numerical test statistics may be
reported as conditional diagnostics with assumptions, not calibrated detection
probabilities. Neither descriptive recovery nor static support licenses an
unknown-source discovery claim; independent validation remains required.

Additional source-list geometry would require its own column allowlist and
local-only handling before claiming uncontaminated annuli. Photon-empty pixels
are never exposure evidence. No new arrays were read or thresholds frozen by
this adjudication, and the counts draft itself remains unchanged.
