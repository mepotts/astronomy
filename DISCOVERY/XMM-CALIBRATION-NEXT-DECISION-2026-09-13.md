# RXJ calibration: one photon-blind feasibility gate before another counts run

**Decision: after RXJ metadata access, adopt one joint region/relative-exposure
feasibility ledger for `0851180501`, before decoding its EVENTS.** Keep the
published position, four fixed cardinal negatives and the requirement for at
least two usable negatives. Do not demand absolute flux calibration merely
to test same-region temporal counts. Conversely, do not call catalogue/map
screening a proof of quiet sky or accumulated map values per-bin live exposure.

This is a proposal, not an executable protocol or relaxation of the first
control's gates. Only existing aggregate reports and four primary documents
were read; no archive queries, new products, scientific arrays or software.

## What the first control actually taught us

- [C2](XMM-C2-INTERPRETATION.md): valid frame weights approximately reproduce
  the matching EVENTS CCD live-time totals, but residuals reach about16s for
  a MOS CCD. That does not bound an individual200s bin's error or justify
  renormalizing to a scalar. CCD frame exposure is not sky-region exposure.
- [C5](XMM-C5-RESULT-2026-09-12.md) and
  [C7](XMM-C7-RESULT-2026-09-12.md): pn/MOS2 source circles have positive
  static samples, while their source annuli are not wholly positive. A
  fine-grid zero appeared where coarse sampling missed it. Maps neither
  certify continuous support nor identify why another camera is absent.
- [C8](XMM-C8-RESULT-2026-09-12.md): all five annuli contact catalogue-source
  exclusion disks; north/east/west also have potential aperture contacts.
  Contact counts are not union areas or measured contaminating flux.
- [C9](XMM-C9-RESULT-2026-09-12.md): reproducible raw source-circle totals
  are777pn,0MOS1,146MOS2. Source events occupy pnCCD5/MOS2CCD7, not the
  central CCDs used as examples in C2. No rates, significant episodes or
  two usable negatives were established. Photon assignments cannot replace
  a photon-blind CCD-geometry check in the next field.

The transferable missing object is **a region-specific acceptance and
relative-exposure model**, not another bright-source selection or a smaller
error bar on an observation-level exposure total.

## What primary calibration documentation supports

SAS `eexpmap` uses CCF spatial response, bad-pixel/border selections, chip GTIs,
exposure extensions and rebinned attitude. It respects specified TIME/GTI/CCD/
FLAG selections, and warns that a single representative energy can be poor
for a wide band. Thus a detection-chain map with different selections cannot
silently become our denominator. Its pn TIMEDEL treatment already includes
mode-dependent OOT corrections; adding a generic second factor risks double
correction. [Official eexpmap algorithm](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

`epiclccorr` explicitly separates absolute response/PSF corrections from
time-dependent dead time, GTIs, exposure and background. Its background time
series must use matching times and bins; it requires the generating event
file and uses SAS/ARF calibration for absolute corrections. The manual also
lists limitations including source spectral variability, OOT and pile-up.
It is a documented calibration reference, not proof that simply invoking it
would validate this pipeline or that SAS is installed locally.
[Official epiclccorr description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epiclccorr/node3.html).

`backscale` defines valid region area with CCD gaps and bad pixels removed;
pure geometric area is a different option. Its numerical grid has finite
resolution. This supports computing the **joint** intersection of each region
with masks, rather than multiplying separately estimated catalogue-unmasked
and map-positive fractions. Area alone is not a model of spatial background
brightness. [Official backscale description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/backscale/node3.html).

These current manuals do not by themselves authenticate every older PPS
exporter convention. Read the actual RXJ product history and schema before
transferring column names, nulls, time references or correction factors.

## One concrete next experiment: RXJ joint-region feasibility

After the separately scoped archive metadata steps, freeze a small ancillary-
only contract. No EVENTS values or light-curve inspection is needed for this
decision. Use returned exact product identities and sizes; no automatic bundle
download or SAS/CCF deployment follows this note.

1. **Assemble the minimum geometric inputs.** Verified event headers and their
   CCD/window/BADPIX information; the observation source list's fixed identity,
   original/corrected positions and extent/error fields; the needed camera maps
   and attitude metadata/values. Where needed, separately allowlist per-CCD
   GTI and frame-exposure tables. Establish mode, frame, time and exposure-ID
   joins first. Source coordinates stay local. Do not copy the first control's
   fixed151-row catalogue limit, CCD roster, schema offsets or absolute grid.
2. **Compute one joint regional ledger.** Preserve all five circles and annuli.
   Apply the same unique-control association and fixed30arcsec other-source
   exclusion convention; annulus exclusions are a union, not summed disk
   areas. Intersect that union with usable detector geometry and report each
   region's effective geometric area and uncertainty from the predetermined
   numerical resolution. Retain catalogue extent/identity ambiguity. Match
   region membership to CCDs using validated geometry, not event occupancy.
   Static map signs remain corroborative diagnostics if DSS compatibility is
   missing; they are not an authoritative FLAG==0 detector mask.
3. **Establish the relative time denominator only for geometrically viable
   regions.** Integrate each relevant CCD's documented frame weights against
   its GTIs and the fixed200s grid, retaining boundary/partial-frame accounting.
   Source and annulus may require different CCD combinations. Determine whether
   sampled attitude motion changes region/mask intersections; retain explicitly
   bounded sampling/discretization limitations rather than demand an impossible
   proof of every instant. Freeze tolerances and boundary conventions before
   those ancillary values, never fit them to a successful light curve. Report
   the bin/reference exposure ratios and uncertainty, not an arbitrary global
   efficiency chosen to force agreement with headers.

This stage's positive conclusion is limited: **pn plus one MOS and at least
two fixed negatives have a computable, adequately characterized region/time
acceptance under the declared model**. A required input, mapping, time
convention or region that remains ambiguous yields a named incomplete result.
If exact detector/FLAG handling requires calibration resources not present in
PPS, report that concrete dependency; do not create a homemade detector mask
from empty photon cells or pretend static maps resolved it. Parent can then
decide a separately bounded supported-calibration step or retain descriptive
counts only. No relocation, new field or alternative radius follows a STOP.

## Is the fixed-negative requirement unnecessarily model-specific?

The **exact cardinal geometry and minimum of two** are our prospective
validation design, not a universal SAS requirement or a theorem about detecting
X-ray transients. Their purpose is to constrain selection freedom and expose
local instrumental/background alternatives. They remain binding for the current
recovery design, and this note recommends retaining them for RXJ. Replacing
them with other controls would require a separately named, independently
justified protocol before the new outputs—not rewriting the first failure.

The transferable scientific requirement is representative, independently
specified comparison behavior with known selection/exposure and acknowledged
contamination. No catalogue can prove a region contains no uncatalogued source;
no photon-blind test can prove its future count stream is constant. The
ancillary gate therefore establishes *eligibility for testing negatives*, not
empirical negative success. Later actual negative counts, source/background
comparisons and detector-artifact checks are still necessary.

For a same-region constant-rate test, an unknown genuinely time-constant
multiplicative efficiency cancels from a bin/reference exposure ratio. This
mathematical simplification can avoid unnecessary absolute ARF/flux work; it
does not cancel time-variable losses, additive or spatially differing
background, or spectral changes coupled to detector response. It is not a
justification for using unit exposure or the full unmasked annulus area.

## RXJ-specific risk and stopping point

The2019 RXJ paper documents a targeted pn full-frame/thin observation and
events in all three EPIC cameras. That makes missing outer-field source
coverage less concerning than the first control, **an inference, not a map
measurement**. Exact MOS windows and four offset-region placements remain
unknown. More importantly, the paper reports strong background flares in the
last6.5ks and poor signal-to-noise above2keV; it retained all times for timing
but used0.2–2keV. RXJ is associated with the Coma environment. These facts
make spatial/background representativeness a real risk, not grounds to declare
the planned broad band or late intervals invalid after viewing them.
[Giustini et al., sections1–2 and Table1](https://arxiv.org/pdf/2002.08967).

Do not predict that targeted pointing guarantees two clean negatives. The
proposed ancillary ledger is the smallest useful way to find out what can
be tested before spending another full photon pass. It can also stop early
on catalogue/window geometry, avoiding a repeat of accumulating many
calibration products without a viable comparison design. Four primary sources
were opened, with no additional searches or archive calls. Existing outcomes
and gates are unchanged; no discovery or calibrated recovery is claimed.

## Parent disposition

Root read this complete note and independently opened all four cited primary
sources on2026-09-13. Adopt the ancillary-first joint-region/relative-exposure
feasibility direction after the separately frozen metadata checks. It remains
a design decision, not authorization for unspecified products, a runtime
freeze or a finding that the regions pass. The fixed negatives and original
control outcome remain unchanged. Absolute flux calibration is not the current
objective; defensible temporal acceptance and background controls are.
