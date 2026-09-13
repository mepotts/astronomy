# Next XMM positive control: choose a metadata preflight, not another claimed recovery

Status: **RESEARCH_ONLY_PROPOSAL_NOT_EXECUTED**. Three literature controls
compared; no scientific products, arrays, catalogue queries or archive product
requests. This is a bounded comparison, not an exhaustive search or discovery.

## Decision

Recommend **RX J1301.9+2747, observation `0851180501`**, for the next independently
frozen control's metadata preflight after the current `0884250101` work. It has
the strongest combination here of a documented pn imaging mode, substantial
published counting statistics, and repeated events on the approximate timescale
our 200-second diagnostic resolves. Keep `0886121001` as a later hard/short-event
stress test, not the preferred next generic recovery control. This priority
change is a proposal requiring parent adoption, not an automatic observation
substitution.

Parent adoption: prefer this known observation's metadata preflight **after**
the current C9 recorded-count experiment is completed or reaches a preserved
STOP. Root independently checked the cited primary papers, including the
preferred observation's Table1 and three-camera timing description. This
changes the next-control priority, not the current target or recovery gates.
No metadata probe or product acquisition has been executed by this decision.

**None is presently eligible for acquisition or certified recovery:** current
exact products, sizes, MOS submodes, and two usable fixed negatives have not
been verified for any of these three in this task. A second known field does
not repair or erase a failed gate in the first.

## Evidence and tradeoffs

### Preferred: RX J1301.9+2747 / `0851180501`

Giustini et al. identify a targeted 2019 observation, pn **full-frame, thin
filter**, and three eruptions detected by all three EPIC cameras near 7, 27
and 40 ks. Typical FWHM is about 1200 s. Table 1 gives 45,170 s pn exposure
and 0.2–2 keV source-plus-background rate 0.171 +/- 0.002 ct/s; the background
rate is 0.0063 +/- 0.0005 ct/s. Their product implies roughly **7,724 recorded
source-plus-background counts**, an inference from rounded publication values,
not an exact event total or forecast under our aperture/cuts. This supports
counting feasibility. The paper retains the whole observation for timing,
although the final 6.5 ks has high background. MOS submodes are not established
by this text. The source is associated with the Coma environment; targeted
pointing does not prove spatially uniform or uncontaminated backgrounds.
[Giustini et al., sections 2–2.1, Table 1 and Figure 1](https://arxiv.org/pdf/2002.08967).

### Previously planned: 4XMM J175136.8-275858 / `0886121001`

Webbe et al. report detection in all three EPIC cameras during this 23-ks
observation, at about 11 arcmin off-axis. A roughly 1-ks outburst contains
15 clustered flares lasting approximately 10–100 s, with reported average
rates 0.2–1.7 ct/s. The brightest example lasts about 33 s at 1.7 ct/s
(roughly 56 counts by multiplication, not an exact integer extraction).
The published onset reference is XMM timestamp 781623400. Detection used
50-s bins/0.5–12 keV, whereas the pn plot uses 20-s bins/0.2–12 keV.
Exact camera submodes were not found in the inspected article. The reported
73.4-ms pn resolution is not a substitute for actual mode headers. Its
off-axis placement makes fixed negative-aperture geometry especially important.
The magnetar classification remains a candidate. This is a useful later
hard-spectrum/time-resolution test; 200-s bins cannot validate recovery of
all 15 short flares, and its onset clock convention still needs header checks.
[Webbe et al., sections 2–3.1 and Figures 1, 3–4](https://academic.oup.com/mnras/article/539/4/3046/8122109).

### Reserve alternative: GSN 069 / `0831790701`

Miniutti et al. list this 2019 observation with 134 ks usable pn exposure.
Their repeated-eruption analysis includes 200-s binned, corrected 0.4–1 keV
light curves and uses pn only for simplicity. Thus this is a well-documented
temporal control, but the inspected methods do not establish the exact MOS
submodes or camera-concordance bundle. The longer exposure increases the
time span to process; it does **not** establish a larger file size without
metadata. There is no demonstrated practical advantage over the preferred
shorter observation. Neither corrected rates nor narrow-band amplitudes are
an exact target for our uncorrected broad-band histograms.
[Miniutti et al., section 2, Table 1 and Figure 1](https://arxiv.org/pdf/2207.07511).

## Smallest next executable metadata step, if adopted

Freeze **one anonymous directory-index GET** for the preferred known observation:

`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0851180501/`

This is a **constructed metadata-only probe** under the archive layout already
verified for the first control, not an observed link or verified current
availability. It is not a guessed event filename. Suggested limits: one attempt,
30-second audited process-tree deadline, 5/15-second socket timeouts, 64 KiB
retained body plus one overflow byte, no redirects, environment credentials or
recursive following. Retain hashes and safe response metadata; keep cookie-bearing
headers private. Accept only a complete index identifying the fixed observation
with an explicit same-observation PPS child. Otherwise record a named STOP;
do not automatically switch to another observation or download a bundle.
The [previous interface investigation](XMM-SIZE-INTERFACE-2026-09-12.md) records
the verified layout and the distinction between release and mirror availability.

After parent review, a separate PPS-listing/summary contract can establish
actual event/source-list/map/attitude filenames, modes, exposures and processing
versions. Use only returned exact links. Size-only HEADs must be separately
specified; rounded directory sizes are not byte lengths. The first control's
404s demonstrate that an index alone is not successful individual retrieval.
No exact event-size, storage or runtime forecast is justified yet.

## What transfers, and what must not be weakened

The reviewed scalar decoding, spherical geometry and integer counting design
can transfer as methods, with newly frozen schema/header-specific configurations.
The current hard-coded camera row counts, time edges and null definitions cannot
be copied to another observation. Require fresh header validation and synthetic
binding tests. Keep the same fixed source radius, four cardinal negative offsets,
annuli, band/cuts and whole-exposure 200-s grid rule unless a separately named
prospective experiment explicitly changes them **before** seeing that field.

Preserve the stronger requirement of pn plus at least one eligible MOS and
**at least two usable negative apertures**. Photon-blind source association,
source-exclusion geometry, detector validity and simultaneous per-region timing/
exposure checks must establish usability. Keep all four negatives, including
failures; do not replace them with quieter locations. Published target detection
in three cameras certifies none of those negative-region conditions.

The first control's exactly-two-episode/separation rule is source-specific,
not a transferable detector test. A new recovery contract must predeclare the
new source's literature-appropriate morphology/time family, multiplicity and
background/defect tests without tuning to its measured photons. Approximate
paper peak times are not exact absolute windows. Raw unmasked counts can
precede calibrated recovery under a separate descriptive contract; they cannot
pass the unchanged two-negative gate by relabelling zero counts as quiet sky.

C7 currently supplies pn/MOS2 static source support for the original field,
but not validated exposure or two usable negatives; C8 records catalogue
contacts in all five annuli. Finish that bounded work, retain its outcomes,
and do not let this second-control proposal become a reason to abandon useful
first-control diagnostics. No recovery outcome or physical discovery is
predicted here.

## Research accounting

Read existing control evidence, recovery draft, search/leverage/eligibility
records, size-interface note, recorded-count plan and C7 result. Primary web
content inspected: EXOD II, Webbe et al., Giustini et al. and Miniutti et al.;
one two-query search batch located the alternatives. Publisher HTML/PDF views
of the GSN paper returned 403 and the Giustini DOI view failed the browser's
safe-open check; author arXiv copies supplied the evidence instead. No failed
view is evidence of missing archive data. No scientific products were requested,
no current archive availability was newly tested, and no code was written.
