# XMM counts-control feasibility without SAS

September 12, 2026. Documentation-only assessment for published control
`0884250101`; no photon or ancillary arrays inspected, no science products
downloaded and no recovery protocol frozen. The [recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md)
and [structural evidence](XMM-EVENT-STRUCTURE-2026-09-12.md) were read in full.
Exactly four official documentation pages were opened for this assessment.

## Decision

**A PPS-only counts-control is conditionally feasible without SAS, an ARF or an
exposure map. Headers alone do not establish that these particular products
meet the conditions.** The smallest defensible experiment compares counts from
the same fixed aperture over time, keeps cameras/exposures separate, and checks
local background and fixed negative apertures separately. It need not first
recover physical flux or an infinite-aperture count rate.

The condition is verifiable relative exposure and sufficiently stable detector
response for each retained aperture. Do not replace this with an assumption
that every sky aperture has the global header EXPOSURE, or that GTIs alone
describe all live-time changes. Conversely, do not make full photometric
calibration a prerequisite if the relevant multiplicative factors are constant.

## Four primary-document findings

1. The pn imaging handbook describes per-CCD EXPOSU, BADPIX and standard GTI
   extensions, with additional GTIs associated with data-subspace time filters.
   Their CCD numbering conventions differ. Science-window coordinates and
   dimensions can appear in EXPOSU headers; discarded-line information may also
   exist. Its EXPOSU table lists central frame TIME and effective FRACEXP but
   does not list the integration-time column shown in the MOS description.
   This is a concrete width/semantics question for the actual product, not
   permission to infer a frame duration from adjacent timestamps across gaps.
   [pn imaging structure](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/evpnima.html).
2. The MOS description supplies per-chip EXPOSU TIME, TIMEDEL and FRACEXP,
   BADPIX detector positions/extents, and standard/additional GTIs. Its event
   lists retain events requiring subsequent screening. Sky X/Y and linearized
   detector coordinates are not the RAWX/RAWY pixel coordinates used by the
   bad-pixel tables. Task-generated examples remain a guide, not a certificate
   that an individual PPS product has the same schema.
   [MOS imaging structure](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/evmosima.html).
3. `evselect` uses data-subspace information and EXPOSUnn extensions to update
   exposure metadata. Its rate/spectrum EXPOSURE is a count-weighted average
   of contributing CCD live times; image EXPOSURE instead uses the maximum
   available CCD on-time. A scalar copied from either product is therefore
   not automatically a region-specific, time-bin exposure.
   [Exposure-information handling](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/evselect/node14.html).
4. `epiclccorr` distinguishes absolute corrections, including vignetting,
   bad pixels, chip gaps, PSF and quantum efficiency, from relative corrections
   involving dead time, GTIs, exposure and background. Its absolute correction
   path uses calibration tools including `arfgen`. This distinction motivates
   the narrower test below; it does not establish that all these factors are
   constant in the selected field.
   [Light-curve correction description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epiclccorr/node3.html).

## What can cancel, and what cannot

Mathematical inference, not a claim of measured instrument stability: under a
constant total aperture-rate null, write expected counts as

    E[N_j] = lambda * k * L_j
    E[N_ref] = lambda * k * L_ref.

Here L describes the verified relative observing exposure and k is an unknown
constant throughput factor. Conditioning independent Poisson counts on their
sum gives binomial probability `L_j / (L_j + L_ref)`: k cancels. An unknown
constant aperture fraction or constant mode duty factor does not by itself
prevent this timing diagnostic. If k varies with time, that cancellation fails.
Energy-dependent throughput also need not be calibrated into flux merely to
test constancy of observed counts; spectral changes complicate interpretation
as intrinsic luminosity, not the definition of the observed-count diagnostic.

Keep raw integer counts. Report source-aperture temporal contrast and a
separate background temporal diagnostic first. Area-scaled subtraction can be
a descriptive addition after valid areas/exposures are known, not a prerequisite
for the temporal contrast. Neither diagnostic supplies physical flux. A background
test that does not reject its null does not establish stable background.
Changing background can invalidate an intrinsic-source interpretation even
when the total-aperture calculation is numerically correct.

## Smallest inspection before a photon-count freeze

The current header-only reader can establish names, fields and declared sizes,
not the following values. A separately scoped next inspection should read only
the necessary **non-EVENTS metadata arrays**, retaining their bytes/provenance
and exact validation failures. No source light curve is needed to make these
choices.

| Input | Minimum question to resolve |
| --- | --- |
| Event and extension headers | Which camera, imaging submode, exposure, filter and CCDs? Do time reference, units, TIMEZERO, barycentric status and data-subspace restrictions agree? Is the binary-table sky WCS usable at the published fixed position? |
| STDGTI and relevant additional GTI START/STOP | Which intervals apply to each selected CCD and exposure? Are values finite, ordered and consistently referenced? Define union/intersection explicitly; do not double-count overlapping intervals or ignore additional TIME restrictions. |
| EXPOSU TIME, integration width, FRACEXP and relevant headers | What interval does each row cover, and does effective fraction already include each required loss term? Resolve pn integration width and any separate dead-time factor. Check gaps, duplicate/overlapping frames, units and finite fractions under the actual per-CCD schema. Do not multiply a loss twice. |
| BADPIX, available discarded-line/window metadata | Which detector pixels/rows and windows are unusable, and is their applicability static or time-dependent? Translate the fixed sky regions only with established coordinate/attitude semantics. |
| Existing source-list/region and footprint metadata, if present | Are fixed source/control apertures and masked annuli usable, sufficiently isolated, and stably covered? Establish area accounting without choosing quieter positions or modifying radii after counts. |

For a verified frame interval I_f, a possible relative-exposure calculation is

    L_j = sum_f q_f * duration(bin_j intersect GTI_CCD intersect I_f),

**only after** q_f's documented meaning and interval convention are resolved.
It is not yet a prescribed `FRACEXP * TIMEDEL` implementation. Sum over a
single CCD only unless a justified region-weighting rule is available. GTI
wall coverage and detector duty fraction remain different quantities; the
draft's proposed 90% cut applies to the former, not detector readout duty.

## Concrete remaining decisions and economical stops

Sky WCS maps sky coordinates into event X/Y. It does not alone establish a
RAWX/RAWY bad-pixel mask for a sky aperture throughout changing attitude.
BADPIX and GTIs are therefore not sufficient merely because their extensions
exist. Prefer fixed regions wholly on one well-behaved CCD/window when the
existing geometry supports that conclusion. This is an eligibility check on
the already proposed regions, not permission to move or shrink them.

If ancillary metadata cannot establish that mapping/coverage, record the exact
missing detector/attitude or footprint input before requesting anything else.
A geometry-only event-column inspection could later test coordinate
consistency, but observed photons cannot prove that unpopulated pixels had
exposure. Do not automatically escalate to an ODF bundle, SAS installation or
exposure-map production; first identify the smallest specific missing input.

Unresolved integration width, contradictory time/DSS associations, or unknown
time-variable detector loss blocks a calibrated relative-rate test. Unresolved
geometry blocks a clean control acceptance, but a separately labelled raw-count
diagnostic may still be useful under a new explicit protocol: **counts recovered,
instrumental/background explanation unresolved**, not validated recovery.

Once these finite metadata questions are answered, freeze the count grid,
screening, reference rule, region eligibility and negative checks, then perform
one bounded photon run. No counts were examined in choosing this path. A
successful result would recover a published control with local consistency
checks; it would not reproduce all EXOD processing, establish QPE nature,
calibrate a global false-alarm probability from one field, or claim a discovery.
