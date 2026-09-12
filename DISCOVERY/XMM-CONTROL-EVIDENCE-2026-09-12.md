# XMM published-control evidence — 2026-09-12

**Recommendation: finish product/mode metadata verification, then design one
published-control recovery experiment; no photon acquisition or unknown search
is ready yet.** The two sources are established literature controls, not our
discoveries. Physical classifications remain candidates. This is bounded research,
not a frozen protocol or a literature-completeness claim.

Read alongside [the eligibility decision](XMM-EXOD-ELIGIBILITY-2026-09-12.md).
Four primary documents were inspected: the EXOD II paper, its magnetar follow-up,
NASA's linked filtering guide and ESA's PPS product specification summary.
Searches located the follow-up; no catalogue coordinate queries, photon files,
science arrays, new implementation or environment changes were made.

## Published evidence: EXOD II

| Observation | Public position and source | Published event description |
|---|---|---|
| `0884250101` | 4XMM J235440.7−373019: Table 6 position `23:54:40.76 −37:30:19.4`; EXOD position `23:54:40.8 −37:30:21` | 2021-05-27, 53 ks; two soft bursts, approximately 1000 s each, separated by approximately 19500 s. Figure 8: 0.2–12 keV, 50-s bins. At 200-s binning, pre-burst rate approximately 0.002 ct/s versus first maximum approximately 0.28 ct/s; authors describe approximately 100-fold variability. |
| `0886121001` | 4XMM J175136.9−275858: `17:51:36.91 −27:58:58.98` | Hard outburst near observation end, approximately 1 ks. Candidate magnetar, not confirmed. |

Methods require imaging `EVLI` and `OBSMLI`. Supported pn submodes:
PrimeFullWindow, PrimeFullWindowExtended, PrimeLargeWindow; MOS excludes
FastUncompressed/FastCompressed. Cuts: pn PATTERN≤4, MOS≤12, 200<PI<12000;
additional warm-pixel, bad-row, partial-MOS-central-CCD and pn-edge exclusions.
Twenty-arcsecond spatial cells combine simultaneous instruments. These are
algorithm rules, not verified modes of either control.
[EXOD II §§2.1–2.3, 4.1–4.2, Table 6, Figure 8](https://arxiv.org/html/2503.14208v2).

## Published evidence: detailed magnetar follow-up

The later name is 4XMM J175136.8−275858; the published precise position matches
above. All three EPIC cameras detect the source in `0886121001` (2022-10-08,
23 ks). Detection is reported at 5σ using 50-s bins and **0.5–12 keV**.

Onset reference: XMM timestamp **781623400**, approximately **2022-10-08
13:35:30 UTC**, about 18.5 ks after observing began. Figure 3 instead labels
time relative to pn exposure start: 20-s bins, 0.2–12 keV. Figure 4 uses 10-s
bins from 18 ks, with 0.2–2, 2–4.5 and 4.5–12 keV bands.

Fifteen photon-cluster flares span approximately 10–100 s; reported rates
0.2–1.7 ct/s and enhancements 20–170. The second lasts approximately 33 s,
averaging approximately 1.7 ct/s. Clustering requires ten photons, alpha 0.75.
Timing searches use barycentric correction and pn 0.1-s bins; these are separate
from broad-burst recovery. No exact camera submodes or complete per-flare
start/end table were established in the inspected text.
[Webbe et al. §§2.1–3.1, Table 1, Figures 3–4](https://academic.oup.com/mnras/article/539/4/3046/8122109).

## Product and filtering references

ESA identifies `PIEVLI` as pn imaging events, `MIEVLI` as MOS imaging events,
and `TIEVLI` as timing events. Thus the paper's `EVLI` shorthand is not a
complete six-character product identity. Other documented products include
`OBSMLI`, `REGION`, `FBKTSR`, `EXPMAP`/`OEXPMP`, `DETMSK`, `ATTTSR`,
`PINDEX` and `PPSSUM`. Exposure and instrument identifiers are encoded in
filenames; event lists are exposure-level, while the EPIC summary source list
is observation-level. Actual filenames, bytes and availability must come from
the archive manifest, not synthesized strings.
[ESA Data Files Handbook, PPS](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/pps.html).

NASA's linked guide explains PATTERN, PI and FLAG filtering, with separate
MOS/pn expressions and optional conservative FLAG==0. Its generic pn expression
uses a different energy ceiling and PATTERN choice from the EXOD recipe.
Consequently, citing this guide does not make a Python implementation's mask
equivalent to EXOD. Exact bitmask semantics and all additional exclusions need
independent specification before execution.
[NASA standard-filter guide](https://heasarc.gsfc.nasa.gov/docs/xmm/hera_guide/node33.html).

## Missing inputs: do not guess

| Required contract field | Current evidence status / consequence |
|---|---|
| Exact pn/MOS exposure IDs, submodes, filters and simultaneous live coverage | **MISSING** for both controls in this study. Publication detection is not a per-exposure eligibility manifest. |
| QPE absolute burst epochs, exact interval endpoints and Figure 8 time-zero convention | **UNSOURCED** here. Approximate durations/separation are not executable absolute windows. Do not digitize a plot by eye into apparently exact timestamps. |
| Magnetar absolute-to-relative time conversion | Reference exists, but **UNVERIFIED** against actual event headers. Inspect TIME units, TIMESYS, MJDREFI/MJDREFF or equivalent, TIMEZERO, TSTART/TSTOP and barycentric status before translating the published number. The approximate UTC value is not an exact conversion test. |
| Exact per-flare intervals | **UNSOURCED** as a complete numeric list. Re-running clustering would be a new analysis choice, not literal interval replay. |
| Extraction radii, background geometry, area/live-time corrections and camera combination for the QPE plotted count rates | **MISSING** as a complete reproducible recipe. Do not make exact count-rate agreement an acceptance gate yet. |
| Per-event FLAG definitions, hot-pixel lists and exposure/CCD good-time semantics | **MISSING** for the proposed local implementation. A familiar column name is not sufficient. |
| Product sizes, usable count rates, PPS compatibility and local runtime | Parent's separate metadata/feasibility work; **NOT ESTABLISHED by this literature study**. |
| Null-region/time choices and empirical false-positive threshold | **NOT PREDECLARED**. Must be prospective, with all failures retained. |

The small difference between the QPE catalogue and EXOD coordinates must be
recorded. Choose one published localization in advance and state the matching
tolerance; do not choose whichever aperture recovers more photons. Likewise,
do not silently exchange the magnetar's detection, plotted-light-curve and
spectral-analysis bands.

## Smallest defensible next stage — recommendation, not execution

First retain the existing one-control metadata scope. After that passes, a
separate contract can choose `0884250101` for a fixed-position, whole-exposure
burst-recovery demonstration. Without exact literature epochs, it must honestly
be labeled a bounded time search at a **known published position**, with its
entire time-bin family and multiplicity correction fixed beforehand. It is not
an exact-window replay. Alternatively, resolving the magnetar's time reference
makes it the more precisely anchored timing control, but switching first
control requires an explicit scope decision rather than silent substitution.

The smallest scientific input set I recommend is:

1. All selected supported imaging event lists covering that control, keeping
   pn/MOS streams separate initially; retain embedded exposure/GTI and detector
   metadata. At least pn plus one overlapping MOS is preferable for a first
   camera-concordance test; missing overlap is an explicit incomplete result.
2. The observation's EPIC summary source list for neighbour masking and fixed
   source association. This plus the event lists is the paper-algorithm minimum,
   not automatically the full validation bundle.
3. Exact source/background region geometry and an exposure/CCD coverage route.
   Use documented PPS regions/maps where suitable or freeze an event-derived
   method first. Add only the specifically needed products to the manifest;
   an all-products archive bundle is unnecessary. A pipeline light curve or
   image alone cannot validate event-level screening or camera concordance.

A counts-only recovery should not require a new spectral fit, response matrix,
luminosity estimate, distance assumption, pulsation search or raw-ODF reprocessing.
Whether PPS alone supports the selected code remains a feasibility gate, not a
promise. Set byte, memory and wall caps from verified products before acquiring
any events; this document supplies no guessed photon-data budget.

Essential negatives for that first contract should include **time-matched local
background**, separate detector/camera behavior, nearby source-free control
regions, and fixed non-burst source windows. Regions must avoid masked sources,
chip gaps and invalid live exposure by declared geometry rules. Inspect whether
an apparent sky burst is driven by a single detector pixel/row or broad-field
background change. Keep high-background and unavailable intervals explicitly
accounted for rather than turning their deletion into successful recovery.

These are proposed validity requirements, not claims of already quiet controls.
Do not use Gaussian count errors uncritically in sparse bins; define the source
plus background counting model and exposure scaling before seeing photons.
One positive plus same-observation negatives demonstrates only local feasibility.
The second published control and independent real-background/artefact tests
remain necessary before an unknown-observation search. Reproducing a published
flare does not establish its physical nature or create a new discovery.
