# MOS partial windows and a bounded descriptive continuation

**METADATA_INTERPRETATION_ONLY.** Retained C1 header JSON and existing notes
were read, with official instrument/task documentation. No science arrays,
product requests, coordinate query, installation or implementation changes.
The cause of the C5 MOS1 zero-map support is **not established** here.

## What the mode actually means

`PrimePartialW3` is MOS **Large Window**, not Small Window. The official mode
table maps Small Window to `PrimePartialW2`. Both retained MOS exposures are
imaging PrimePartialW3, with central-CCD frame time 900 ms, consistent with
Large Window rather than a timing/collapsed-coordinate exposure.
[ESA Data Files Handbook mode table](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/node71.html)

The nominal MOS large window reads 300 by 300 central-CCD pixels, versus
600 by 600 in full frame. Its nominal pixel scale is 1.1 arcsec and frame time
0.9 seconds; the outer ring remains standard imaging. Thus a source can lie
in an unread part of the central chip while another fixed region intersects
an outer chip. Conversely, the camera-level mode name does not imply that all
off-centre sources are absent. The handbook's generic outer-ring statement
must be qualified by the actual available CCDs in this exposure.
[ESA EPIC operating modes](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/epicmode.html)

Retained C1 metadata is more specific:

| Header location, both MOS cameras | CCD | Readout mode | WINDOWDX by WINDOWDY |
| --- | ---: | --- | --- |
| EXPOSU01 | 1 | PrimePartialW3 | 303 by 298 |
| BADPIX01 | 1 | camera SUBMODE PrimePartialW3 | 310 by 300 |

Both also declare window-origin keywords, but their Y origins differ by one
pixel between these two extensions. Header comments call the origins the
bottom-left corner and the dimensions window sizes. Neither rounding to the
nominal 300-square handbook window nor choosing the more favorable rectangle
is justified. Their differing processing roles/coordinate conventions must be
resolved before using them as the same hard mask; no explanation for the
differences is asserted here. This note publishes no sky/WCS coordinate values.

MOS1 has EXPOSU/BADPIX/STDGTI for CCDs 1,2,4,5,7 only; MOS2 has 1–7. Outer
CCD exposure headers say PrimeFullWindow, with 2700-ms frame time. A missing
MOS1 chip is not created by extending the central readout window. Per-CCD
identity and each EVENTS DSS-to-STDGTI association must be retained.
These are header facts already recorded in `XMM-C1-HEADER-REVIEW.md`; no
physical explanation for the missing chips is inferred from the table layout.

## Can this explain the zero map?

**It is a plausible mechanism, not a demonstrated explanation.** A large-window
central gap, a chip gap/missing chip, pipeline selection masks/GTIs, or a
coordinate/processing mismatch can all matter. Neither the 303-by-298 header
rectangle nor the nominal 5.5-arcmin window width locates the fixed source on
the actual detector. This task did not project its position into RAW coordinates.

C5's all-zero MOS1 source circle and annulus therefore establish a lack of
positive support in that particular PPS map under the fixed numerical
diagnostic. They do not establish zero physical exposure or prove that no
source photons were recorded. C4's sampled attitude movement likewise supplies
no missing absolute detector-to-sky transform. The different map versus event
FLAG/energy/GTI provenance identified in `XMM-MAP-COMPATIBILITY-2026-09-12.md`
remains relevant. MOS2 availability/header inspection and a separately frozen
same-centre map-support measurement are the immediate practical next steps;
there is no reason to build a new calibrated detector projection first.

For a genuinely photon-blind detector-window explanation, the minimum extra
evidence would be a verified per-camera/CCD sky-to-RAW projection for the fixed
region and relevant attitude, plus the correct science-window convention and
bad-pixel mask. Event X/Y WCS alone supplies the sky-image relation, not that
full RAW mapping. Official calibration documentation assigns window origins
and dimensions to mode parameters accessed through CAL; this does not justify
inventing a linear detector transform from the four window numbers.
[ESA EMOS mode-parameter definitions](https://xmm-tools.cosmos.esa.int/external/xmm_calibration/calib/documentation/CALHB/node736.html)

BADPIX supplies RAWX/RAWY and strip extent/type information. The task manual
also describes window metadata and CAL bad-pixel inputs. Such tables help test
detector validity, but their rows have not been decoded in this investigation,
and the full usable sky footprint cannot be inferred from their header alone.
[ESA badpixfind output](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/badpixfind/node7.html)

## If both MOS maps have zero source support: a useful finite next step

Do **not** repeatedly change band, radius or pointing until a map is positive.
Preserve the original pn-plus-at-least-one-MOS recovery requirement as unmet.
There is nevertheless a scientifically useful, distinctly labelled **descriptive
recorded-event screen** available from the existing PPS files. It does not
require first solving every exposure-calibration question, because its output
need not be a calibrated rate, significance or recovery result.

The smallest prospective implementation would freeze one bounded local pass
through exactly the existing three EVENTS tables, with only TIME, X, Y, PI,
PATTERN, FLAG, CCDNR and RAWX/RAWY interpreted. No PHA, spectrum, flux fitting,
centroid fitting, image search, alternate regions or event-driven recentering.
The three header row counts sum to **3,323,958**; exact selected-column byte
budget, offsets, runtime and tests must be bound before that first pass.

Minimum preflight, using existing metadata rather than another acquisition:

1. Bind C1 products/outcome/header hashes and exact scalar types, integer/null/
   scaling rules. Validate X/Y binary-table WCS with the actual axis order,
   FK5/equinox and local published-centre transformation. Do not take malformed
   or truncated-looking auxiliary REFX/REFY limits as a footprint; schema and
   WCS validity are separate from incidental range keywords. Reject unknown
   transforms rather than fitting them from photons.
2. Fix the same 20-arcsec aperture, 60–90-arcsec annulus and four 120-arcsec
   directional negatives; keep the 200-second grid anchored at pn TSTART.
   Use TT/MJDREF/TIMEZERO and the actual per-CCD STDGTI unions already examined
   by C2, with half-open interval membership. Keep all planned cameras/regions/
   bins, including empty and untestable ones. No first-event time anchor.
3. Freeze the already proposed numeric calibrated PI band, PATTERN limits and
   FLAG==0 as a **declared descriptive filter**, not EXOD-equivalent screening.
   Count exclusions by reason, including invalid/unknown CCD, invalid time or
   coordinate, and outside that CCD's GTI. Preserve camera/CCD identity; do not
   merge a central-window and full-frame outer CCD into a uniform exposure.
4. Retain aggregate contributing-CCD and RAW-pixel/row concentration diagnostics
   for fixed regions and time bins. RAW values are detector-validity diagnostics,
   not coordinates to use for optimizing apertures. If a window-convention
   mismatch cannot be resolved, label it explicitly and do not claim the events
   prove valid full-aperture coverage. Existing FLAG filtering is not proof
   that every instrumental effect has been removed. SAS emframes derives
   per-node GTIs and flags bad frames for later event rejection; this supports
   the need for the actual per-CCD links, not a global exposure shortcut.
   [ESA emframes](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emframes/node3.html)
5. Initially report **raw retained aperture and annulus counts separately**,
   alongside GTI wall-duration and detector diagnostics. Do not divide by
   guessed live exposure, apply map amplitudes as 200-second denominators,
   background-subtract using an unvalidated area ratio, or attach calibrated
   p-values. Until the separately proposed source-list geometry read supplies
   fixed 30-arcsec exclusions, label annulus counts as unmasked/possibly
   contaminated rather than silently pretending the draft exclusions exist.

This cleanly distinguishes two empirical questions. Positive MOS source-region
counts would establish that some retained events occur in the fixed aperture
and motivate a **specific** map/event-selection or window-mapping check; they
would not prove those events are source photons, unconfused, or continuously
exposed. Zero selected MOS counts would remain an observed absence of selected
events, not a measurement of zero exposure. Neither result permits selection
changes within that frozen pass. The pn screen can remain informative even
when MOS support is unresolved, but must be labelled pn descriptive evidence
rather than successful multi-camera recovery.

## Stronger gates remain separate

The original recovery still needs pn plus a valid MOS comparison and at least
two usable fixed negatives; catalogue confusion/exclusion and region-area
handling; defensible regional exposure/background scaling; fixed detector-
artifact vetoes; and the prospectively specified episode/count tests. A
descriptive pass cannot promote those gates or establish a global false-alarm
rate. No new discovery, physical QPE confirmation or independently calibrated
recovery follows from the proposal above.

The recommendation is therefore executable and bounded: finish the one MOS2
map availability/support check; if it does not resolve support, adopt or reject
the precisely narrower recorded-event screen explicitly. Do not let unresolved
full exposure calibration become either an indefinite prerequisite to reporting
raw counts or an excuse to present those counts as calibrated science.

## Provenance and handling

C1 MOS header-report anchors are
`a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae`
and `4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417`.
No product array was opened. Current official manuals describe the modes and
processing concepts, not a reproduction of the exact retained SAS 21 run.
An initial over-broad local header filter inadvertently displayed reference-WCS
values in the tool transcript; parent was notified. No such values were sent
to an external service or included in this document. Subsequent extraction
used an explicit window-key allowlist; no full headers are published here.
