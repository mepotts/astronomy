# Draft: counts-only recovery of published QPE control 0884250101

**Prospective draft, not frozen and not executable.** No downloads, archive
queries, photon processing or code execution accompany this document. Its aim
is a small known-source recovery, not an EXOD reproduction, physical QPE
classification or discovery. Header/product feasibility and final review must
precede a separately approved photon run.

The [control evidence note](XMM-CONTROL-EVIDENCE-2026-09-12.md) supplies the
published position, approximate two-burst morphology and unresolved inputs.
The underlying source is [EXOD II §4.1, Table 6 and Figure 8](https://arxiv.org/html/2503.14208v2).
No exact burst epoch or Figure 8 time origin is assumed. All numerical choices
below are proposed engineering decisions, not unpublished facts about the data.

## Decisions to fix before looking at photons

- Observation: `0884250101` only. Source centre: published catalogue position
  `23:54:40.76 −37:30:19.4`, with no recentering on the observed counts.
- A circular source aperture of radius **20 arcsec**; local background annulus
  **60–90 arcsec**. These deliberately simple fixed apertures are not claimed
  to match the paper's extraction, optimize signal-to-noise or enclose a known
  energy fraction. If geometry makes them unusable, record incomplete rather
  than change radii after seeing the light curve.
- Primary band **200 < PI < 12000 eV**, pn PATTERN≤4, MOS PATTERN≤12. Resolve
  exact FLAG/bad-pixel screening below; this draft does not claim to implement
  every EXOD-specific exclusion. No additional discovery bands or spectra.
- Keep eligible pn, MOS1 and MOS2 streams separate. Require pn and at least
  one MOS with usable simultaneous coverage for a successful camera check.
- Single temporal grid: **200-s, non-overlapping, half-open bins**, anchored at
  the verified pn exposure TSTART in a common time system. Preserve the actual
  absolute timestamp of every edge. Do not subtract the first surviving photon
  or shift the grid to maximize a peak. Edge/partial bins remain in the ledger.
- Four spatial negative apertures: same radius, centred 120 arcsec north, east,
  south and west of the published position using a sky-coordinate offset
  operation. Each has its own same-size background annulus. These are fixed
  controls, not a search for new objects; only scalar control diagnostics are
  reported. Do not replace unavailable controls with quieter positions.

Geometry acceptance is photon-blind: use the summary source list, coverage and
detector metadata. Exclude other catalogued-source regions from background
annuli using a fixed 30-arcsec exclusion radius. An unknown valid source radius
or unresolved overlapping source in a source/control aperture makes that region
unavailable, not clean. Require at least two usable negative apertures and
record the other two. The precise coverage and area computation remains a
blocking implementation choice below; a catalogue's absence is not proof that
a region contains no source.

## Minimal count computation

For camera c, region r and bin j, retain integer source-aperture counts S_j,
background-annulus counts B_j, their separate live exposures eS_j/eB_j, and
valid areas AS/AB. Define a=AS/AB and the descriptive net rate

    R_j = S_j/eS_j − a B_j/eB_j.

Never clip negative R_j to zero. Zero/unknown exposure means unmeasured, not
zero counts per second. Do not multiply counts by calibration factors and then
treat the result as an integer Poisson sample.

For each tested bin, the reference is **all other accepted bins in that camera
and region whose intervals lie completely outside [start_j−1000 s,
end_j+1000 s]**. Sum counts and exposures over that reference. Require at least
2000 s of reference live exposure; otherwise mark untestable. This rule is fixed
without knowing burst epochs. A second burst may contaminate the reference,
so it is not an independently known quiescent baseline. Retain that limitation.

An exact conditional *constant total aperture-rate* diagnostic is

    p_j = P[X ≥ S_j],
    X ~ Binomial(S_j + S_ref, eS_j/(eS_j + eS_ref)).

This follows by conditioning two independent Poisson counts with a common rate
on their sum. It tests total aperture variability, **not** intrinsic source
variability after background subtraction. Background variability violates its
null interpretation. Compute the same diagnostic separately for B_j/B_ref and
the background exposures; report the net-rate contrast ΔR=R_j−R_ref.

Set M to the number of all planned camera × five-region × temporal-grid tests,
including later untestable cells. Use the conservative diagnostic threshold
**p_j ≤ 0.01/M**. There is one energy band and one grid. Reference windows
overlap; Bonferroni does not require independent tests, but valid individual
null distributions still require the stated counting assumptions. A small p
is not a calibrated astrophysical false-alarm probability. Do not select the
best camera and forget the others or recompute M after failures.

## Positive recovery and essential negatives

Call a source bin provisionally elevated only when its source-aperture test
passes, ΔR>0, and its background test does **not** pass the same threshold.
Background non-detection is only a veto diagnostic, not proof of a stable
background; retain its counts, uncertainty and light curve. A full likelihood
model separating source and variable background is outside this minimal stage.

Group elevated source bins into episodes when consecutive elevated-bin centres
are separated by at most 1000 s. Report every episode, not only two attractive
ones. For the narrow positive-control outcome, require exactly two pn episodes
with peak-bin-centre separation in **[15600,23400] s** (a deliberately broad
±20% check around the published approximate separation), and elevated bins in
at least one eligible MOS within ±1000 s of each pn peak. The episode peak is
the greatest ΔR, breaking ties by earliest time. These broad morphology checks
do not measure a period or reproduce exact burst durations. Extra/missing
episodes are an explicit non-recovery/incomplete outcome, not permission to
adjust grouping, aperture, grid or tolerance.

For each episode, inspect the already selected events' detector pixel/row/CCD
distribution and camera coverage without recentering or changing masks. A
single-camera, detector-defect or coverage-change explanation prevents clean
recovery. Freeze an objective defect-flag criterion before execution; visual
inspection can flag problems but cannot certify a clean detector by itself.

Run the same temporal test across each available negative aperture. Any elevated
control episode is `CONTROL_CONTAMINATION_OR_BACKGROUND_UNRESOLVED`; it may be
a real source, not necessarily an instrumental false alarm. Preserve it without
following up its coordinates in this stage. Background flares and failed/partial
GTIs stay explicitly accounted for. Non-episode source windows are descriptive
same-data comparisons, not independently selected true negatives.

## Blocking choices to resolve before freeze

1. **Products and modes:** exact imaging event filenames/exposure IDs, PPS
   version, supported submodes, filters, complete advertised byte sizes and
   source-list/coverage products. No wildcard bundles or substitute observation.
2. **Time and exposure:** validate TIME units/system/reference, TIMEZERO,
   TSTART/TSTOP and any barycentric correction; define per-CCD GTI intersection,
   dead-time/live-time handling and camera overlap. Proposed acceptance is at
   least 90% live coverage for each tested 200-s source/background bin; this
   cannot be evaluated from observation duration. Partial/missing bins are not
   silently filled or renormalized to full exposure.
3. **Geometry:** verified sky-to-event/detector mapping, chip/bad-pixel masks,
   source/background area accounting and relevant exposure variation. Geometric
   area scaling alone may not describe spatially varying instrumental background
   or vignetting. If a defensible same-region temporal comparison and local
   background scaling cannot be specified from PPS inputs, stop rather than
   present area subtraction as calibrated flux.
4. **Screening and defects:** exact FLAG semantics and retained bad-pixel/row
   information; a prospectively fixed detector-artifact veto. Neither FLAG==0
   nor a familiar column name alone establishes EXOD equivalence.
5. **Execution:** confirm a tested existing runtime; freeze manifest, maximum
   expanded bytes, peak memory, wall time and output budget from actual products.
   One bounded run with exclusive receipts, all failures retained and read-only
   replay. No SAS/CCF installation, ODF reprocessing or repeated acquisition is
   implicit. Unit-test bins, exposure intersections, Poisson tails, zero counts,
   reference selection and camera/time conversions before any real measurements.

Until these are resolved this is `DRAFT_NOT_READY`, not a pass. A final contract
must record every unresolved choice's resolution before accessing photon counts.

## Allowed conclusions and stops

Missing products/modes, ambiguous time or geometry, absent pn+MOS overlap,
insufficient controls, screening uncertainty or runtime-cap failure produce a
named STOP/incomplete receipt. Statistical non-recovery is retained as such;
it is not evidence that the published source lacks bursts. No automatic retry,
new camera/field, threshold relaxation or larger time search follows.

At most, successful execution supports **published-control counts recovery
with local consistency diagnostics**. It establishes neither confirmed QPE
nature nor a calibrated global false-alarm rate from this one field. The second
published control, independent real-background/artifact trials, source-location
validation and later-literature checks remain separate requirements before
unknown-source discovery work. This draft makes no claim of a new discovery.
