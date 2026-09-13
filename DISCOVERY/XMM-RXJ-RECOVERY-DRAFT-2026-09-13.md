# RXJ known-control recovery: source-specific draft

**DRAFT_NOT_READY_FOR_PHOTONS.** Proposal for observation0851180501 only,
not an adopted protocol, acquisition authorization or modification of the
first control. No products, coordinates, photon values or executable science
were accessed. This draft follows the adopted
[ancillary-first calibration direction](XMM-CALIBRATION-NEXT-DECISION-2026-09-13.md)
and preserves the original
[0884250101 recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md).

## Outcome worth testing

The smallest useful result is **recovery of the published three-eruption
pattern in pn and an eligible MOS, with measured local background/control
diagnostics and defensible relative exposure**. It need not reproduce absolute
flux, spectral physics or a survey false-alarm probability. It must not label
raw-count peaks alone as calibrated intrinsic-source detections.

Giustini et al. identify0851180501 in section2, paper page2. They retain the
whole observation for timing despite strong background flares in its final
6.5ks, and use0.2–2keV because higher-energy signal-to-noise is poor.
Section2.1 reports three eruptions in all three EPIC cameras near7,27,40ks;
the abstract gives approximate ordered separations20ks and13ks. Table1 on
page3 establishes pn full-frame/thin, not MOS submodes. Figure1 on page3
shows background-corrected300s light curves. Section2.1 and Figure2 describe
energy-dependent durations and peak times; an average1200s Gaussian FWHM
is not a universal episode-width requirement.
[Giustini, Miniutti & Saxton2020, pages1–4](https://arxiv.org/pdf/2002.08967).

## Proposed changes and retained constraints

Adopt, if approved, a **separately named RXJ soft-band variant** with strict
`200 < PI < 2000` in the verified calibrated-eV convention. Retain200s bins
to test the existing counting method, explicitly differing from the published
display. No simultaneous broad-band discovery test, energy scan or rebinning
search. This is justified before RXJ photons, not a retrospective alteration
of the first control's200–12000 cuts.

Retain the fixed published centre locally, no recentering;20arcsec source and
four120arcsec cardinal comparison circles;60–90arcsec annuli;30arcsec
other-source exclusion disks; pn PATTERN<=4, MOS<=12 and FLAG==0 after actual
schema/null/flag checks. Keep all five regions and both MOS records. Require
pn plus at least one eligible MOS and **at least two usable fixed negatives**.
No choice of the quietest controls or replacement coordinates after counts.

These radii/cardinal placements and minimum number of negatives are deliberate
repo conventions, not instrumental laws or the paper's extraction recipe.
They prevent selection freedom and remain binding in this proposed variant.
The transferable science is representative local controls with characterized
acceptance, not the cardinal directions themselves. Failure does not authorize
their removal. The first control's exactly-two-episode criterion, however,
is not the morphology of RXJ and must not be copied.

## Finite prerequisites before the recovery photon pass

1. **Product identity and supported mode.** Obtain only separately authorized
   exact products. Verify observation/exposure IDs, imaging modes, filters,
   processing versions, sizes, scalar schemas and nulls. pn full-frame/thin
   is a literature expectation to check, not a replacement for metadata.
   MOS mode and window validity remain unestablished. Bind the actual source
   position's reference/frame without exporting it.
2. **Joint region geometry.** Establish source association and contamination
   from geometry columns, detector/CCD mapping and selected-region masks.
   Compute the union of annular source exclusions intersected with usable
   detector area. Preserve ambiguous catalogue extent and unavailable regions.
   The source and two negatives must be geometrically eligible in pn and at
   least one same MOS used for the camera check. Static maps with different
   DSS/GTI/FLAG provenance are corroboration, not the denominator. Do not infer
   a mask or CCD mapping from photon occupancy.
3. **Time and relative acceptance.** Verify clock/reference/TIMEZERO and
   per-CCD GTI/frame semantics. Anchor all half-open200s bins at pn TSTART;
   extend by integer bins to cover all selected camera-header intervals and
   retain every edge/partial bin. Compute separate source/annulus/negative
   wall-GTI coverage and effective-exposure ratios. Retain the original90%
   wall-coverage proposal, not a90% live-duty requirement. Specify uncertain
   frame-boundary allocation, sampled attitude and area errors before their
   ancillary measurements. No global rescaling to force a header total.
4. **Background transfer and artifact rules.** Specify how the masked annulus
   represents the aperture's time-variable background, including area, CCD,
   response and uncertainty limitations. Region area alone cannot establish
   this relation. Freeze a concrete detector/CCD/bad-row veto before photons;
   FLAG==0 and cross-camera agreement are not complete defect proofs. Exact
   acceptable systematic bounds and detector-concentration thresholds remain
   **unestablished**; identify them from the supported geometry/calibration and
   synthetic tests, not a desired light curve. No catalogued neighbour does
   not mean proven empty sky.
5. **Frozen, tested measurement and resource contract.** Resolve the proposed
   scientific choices below, test zero exposure/counts and all denominators,
   bind actual schemas/configuration and set acquisition-independent numerical
   byte/time/memory/output caps. Preserve every planned camera/region/bin,
   failure and additional verification pass. The original334chunks, row counts
   and absolute grid do not transfer. Review and freeze before real counts.

This is a small set of necessary objects, not a demand to rebuild SAS or prove
continuous coverage at every instant. A locally supported calibration product
may supply an object if its applicable selections and assumptions are verified.
If PPS cannot establish one essential object, stop at that concrete dependency.
An explicitly separate descriptive-count stage could still be proposed; it
would not be this recovery experiment.

SAS `epiclccorr` distinguishes relative corrections for GTIs/dead time/exposure
and background from absolute response/PSF corrections. It requires compatible
background times/bins and documents limitations including spectral variability,
OOT and pile-up. This supports prioritizing temporal acceptance, while not
claiming that invoking the task automatically validates our result.
[Official epiclccorr description and limitations](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epiclccorr/node3.html).
The repo's [exposure semantics note](XMM-EXPOSURE-SEMANTICS-2026-09-12.md)
records which constant factors may cancel and why time-variable or spatially
different losses do not. Absolute ARF/spectral fitting is not a prerequisite
for this narrower result.

## Minimal measured recovery rule, proposed for review

Keep integer aperture/annulus counts and separately computed exposures/areas.
Report net-rate contrasts without clipping negatives. Use the original
all-other-bins reference outside each bin's +/-1000s neighbourhood, requiring
at least2000s reference live exposure. This is a defined reference, not a
known quiescent state; other eruptions can contribute. Retain the full span,
including late backgrounds. Do not select a new GTI by looking at the source.

For continuity with the earlier draft, the exact conditional binomial tail
can remain a **constant total-aperture-rate diagnostic**, with0.01/M and M
fixed from every planned camera x five-region x bin cell before exclusions.
Apply and report the analogous annulus diagnostic. A positive net contrast,
aperture diagnostic crossing and no annulus crossing may flag a provisional
bin, but these conditions alone do not prove an intrinsic-source event:
background non-detection can simply have low power. Show counts, exposure,
background uncertainty and negative-region behaviour for every flagged bin.
If the background-transfer uncertainty can explain the net contrast, label
that episode unresolved rather than turning the total-aperture tail into a
background-corrected significance.

Proposed morphology convention: group flagged-bin centres separated by at
most1000s. Retain **all** episodes; exactly three pn episodes are required
for the narrow complete-pattern outcome. Use maximum net-rate contrast as
the episode locator, earliest-time tie break, and propose ordered peak gaps
in[16000,24000]s then[10400,15600]s. Require an eligible MOS flagged bin
within+/-1000s of every pn locator, with valid simultaneous source/background
coverage. These +/-20% gap bands, grouping and camera tolerance are
**engineering proposals, not published uncertainty intervals**. They require
explicit adoption and synthetic fragmentation/timing tests before photons.
Do not impose an exact FWHM, amplitude ratio, absolute7/27/40ks window or
strict periodicity. The paper's approximate relative origin does not provide
an authenticated absolute-time template.

Extra/missing episodes or an unmatched camera give non-recovery/incomplete,
not a search for a favourable three-episode subset. Missing coverage is
untestable, not absence of an eruption. Do not combine MOS counts to hide a
failed camera. A successful pn-plus-one-MOS result still reports the other
camera independently.

Apply the same temporal procedure to all eligible fixed negatives. Any elevated
negative episode leaves `CONTROL_CONTAMINATION_OR_BACKGROUND_UNRESOLVED`;
preserve it without follow-up coordinates. Require at least two eligible
negatives with no flagged episode for the original local-consistency gate.
Report their uncertainty/detection sensitivity: absence of flags is not a
calibrated equivalence-to-zero result. Their relevance to a source episode
also requires actual simultaneous acceptance, not just observation-wide area.
Low-information controls cannot certify a quantified false-alarm rate.

## What can wait, and what cannot

Later robustness can include alternative grids/bands, calibrated spectral/PSF
fits, comparison with an independently generated SAS light curve, injected
signals in real backgrounds, and multiple separate quiet/artifact controls.
They are not all prerequisites for the limited published-pattern diagnostic;
they become necessary as appropriate before promoting it into an unknown-source
search with sensitivity or false-alarm claims. This one known field cannot
supply those population guarantees.

An exploratory statistical improvement would replace the total-aperture
diagnostic with an explicitly background-aware count model or conservative
simultaneous Poisson-mean intervals for aperture/annulus bin/reference counts.
For the latter, a family-corrected lower bound on net contrast could propagate
exposure and background-transfer uncertainty. It would require its own tested
coverage assumptions and predeclared systematic bounds. **Do not make a new
likelihood/Monte-Carlo framework an automatic prerequisite for the current
metadata work, or call an unimplemented estimator calibrated.**

What cannot wait until an attractive curve appears: source/negative placement,
band/grid, exposure handling, background-transfer assumptions, eligibility,
defect rules, multiplicity/grouping and every claimed acceptance threshold.
Exact unresolved tolerances keep this draft unready for a recovery run. Strongest
future successful label is `PUBLISHED_RXJ_PATTERN_WITH_LOCAL_DIAGNOSTICS`, not
new discovery, physical QPE confirmation or a calibrated survey false alarm.

Research accounting: prior repo recovery/decision/calibration/geometry/count
notes and two primary sources read (paper plus SAS description). No archive
query, acquisition, candidate data, coordinate disclosure, software change or
science execution. Only this draft was written.

## Parent disposition

Root read the full draft and independently checked the two primary sources.
Adopt the direction of a separately named soft-band RXJ control experiment,
with the retained fixed-region and pn-plus-MOS requirements; preserve the
first control's broad-band outcomes. Do not execute recovery yet. The draft's
numerical grouping/gap thresholds and systematic/defect acceptance criteria
still require a complete reviewed protocol and synthetic validation. Metadata
M2 neither reads photons nor freezes those unresolved scientific choices.
