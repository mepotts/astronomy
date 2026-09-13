# Independent C1 header adjudication

September 12, 2026. Read-only review of the four retained
`XMM-C1-2026-09-12-data/headers/slot-*-headers.json` reports, the original
[C1 protocol](XMM-C1-2026-09-12.md), and the
[counts-feasibility assessment](XMM-COUNTS-FEASIBILITY-2026-09-12.md).
No FITS file or array was opened, no network request made, and no coordinate,
pointing/WCS value, observer contact or full header card is reproduced here.
Metadata were reduced through `xmm_header_summary.py`, with additional explicitly
selected non-coordinate timing and data-subspace keys inspected locally.
Transport/hash replay is the separate acquisition reviewer's responsibility.

## Outcome

**The retained headers support the selected observation/product identities and
an imaging-mode metadata-value continuation. They do not yet support freezing
the photon-count recovery.** Important questions have become narrower: pn does
have an exposure-interval keyword; CCD-to-GTI associations are explicit; MOS
energy units and exposure/dead-time semantics still need resolution. No extra
acquisition or SAS installation is justified merely by this header review.

| Slot | Header identity | Mode/filter | HDUs | Declared main-table rows |
| --- | --- | --- | ---: | ---: |
| 1 | EPN, observation 0884250101, S003 / EXP_ID 0884250101003 | IMAGING, PrimeFullWindow, Thin1 | 64 | EVENTS: 2,694,388 |
| 2 | EMOS1, same observation, S001 / EXP_ID 0884250101001 | IMAGING, PrimePartialW3, Thin1 | 19 | EVENTS: 273,441 |
| 3 | EMOS2, same observation, S002 / EXP_ID 0884250101002 | IMAGING, PrimePartialW3, Thin1 | 25 | EVENTS: 356,129 |
| 4 | EPIC, same observation, observation source list | IMAGING; no single-camera submode | 2 | SRCLIST: 151 |

These counts come from table headers, not decoded photons or source rows. The
source-list primary EXP_ID matches pn S003; its EPIC identity and per-camera
columns are consistent with a combined product, not a fourth event exposure.
All three event-product primary creators identify `evlistcomb-4.20` in
`xmmsas_20241108_1150-21.0.0`; the source list identifies `srcmatch-3.26` in the
same SAS build. This records processing provenance, not validation of calibration.

## Timing and energy: established versus unresolved

Where present, event and time-bearing ancillary headers agree on TT, seconds,
MJDREF 50814.0, zero TIMEZERO, TIMEREF LOCAL, TASSIGN SATELLITE and CLOCKAPP true.
Integer versus floating zero is not a discrepancy. These declarations support
using a shared spacecraft-time basis; they do not indicate barycentric timing
or prove payload timestamps conform. Some primary/ancillary headers omit time
keys, so require documented inheritance rather than treating absence as a new
time system. The source list is not a timeseries and has no such common clock.

EVENTS TSTOP-minus-TSTART is approximately 49,071.590458 s (pn), 50,023.683535 s
(MOS1) and 50,194.643767 s (MOS2). This is neither live exposure nor the paper's
rounded observation duration. Their nominal windows overlap; usable simultaneous
GTI coverage has not been measured. The unique selected pn S003 TSTART can anchor
the prospective grid once time validation is complete; no first-photon anchor
or guess at published burst times is needed.

All three have TIME, PI, FLAG, PATTERN, CCDNR and sky/detector coordinate columns.
pn PI is explicitly `eV`; both MOS PI units are `CHAN`. Therefore the pn unit
ambiguity in the generic documentation is resolved by this product, but the
MOS version remains: establish calibrated MOS PI's numerical energy convention
from authoritative processing semantics before interpreting the same numerical
200–12000 cut as eV. Do not infer it from a plausible maximum, copy pn units,
or read a distribution to select a convenient conversion.

Basic binary-table sky WCS fields for X/Y are present in each EVENTS header.
Presence is not an astrometric/round-trip validation or sky-to-RAW detector mask.
MOS X/Y and DETX/DETY column units say `pixel`, while pn lists `0.05 arcsec`;
use each actual WCS, not a universal literal TUNIT interpretation. Coordinate
values and any future local geometry derivative must stay local.

## Actual ancillary inventory and the important associations

- pn has twelve each of EXPOSU, BADPIX, DLIMAP, HKAUX and STDGTI, plus OFFSETS
  and CALINDEX. EXPOSU columns are TIME(D seconds), FRACEXP(E fraction).
  All twelve carry TIMEDEL = 0.0687021985650063 s, described as the exposure-entry
  interval length. EXPOSU FRMTIME = 73 ms is explicitly rounded; FRAMETIM =
  73.36496 ms is nominal. STDGTI FRMTIME = 73.36496 ms is also nominal. Thus
  these two FRMTIME values are not an unexplained conflicting clock. The
  remaining question is how exposure-entry width, nominal frame spacing and
  FRACEXP combine without losing or double-correcting duty time.
- pn CCDID repeats 0,1,2 in quadrants 0,1,2,3. CCDID alone is not a unique CCD
  key. The EVENTS data-subspace alternatives explicitly link event CCDNR 1–12
  to STDGTI01–12. Preserve those associations, extension suffixes and quadrant
  metadata together; do not join twelve tables on the three-valued CCDID.
- MOS1 has EXPOSU/BADPIX/STDGTI only for 1,2,4,5,7; MOS2 has all 1–7. These
  are also the CCD sets declared by each EVENTS data subspace. Missing MOS1
  3 and 6 are not a transport failure inferred from this layout and must not
  be synthesized as full-coverage chips. No physical cause is claimed here.
- MOS EXPOSU has TIME(D seconds), TIMEDEL(E seconds), FRACEXP(E fraction).
  CCD1 is PrimePartialW3 with FRMTIME 900 ms; available outer CCDs are
  PrimeFullWindow with FRMTIME 2700 ms. Camera-level SUBMODE is not a uniform
  per-CCD exposure prescription. SETDEADT=1 explicitly records that
  `emframes` applied its dead-time option; do not apply an additional mode
  correction until the actual FRACEXP/TIMEDEL meaning is established.
- STDGTI tables have START/STOP doubles in seconds. No additional GTI-named
  extensions occur in these files. The numeric-prefix DSS alternatives
  (`2DSVAL1`, `2DSREF2`, etc.) must be parsed: the simple summary helper's
  `startswith` list omits them. Reading only DSREF2 would incorrectly use CCD1
  for every detector. Both MOS event headers additionally declare a FLAG
  subspace; pn declares CCDNR and TIME. Recorded screening is not a complete
  final FLAG/PATTERN policy or proof of EXOD-equivalent filtering.

Parent integration: the non-coordinate summary helper has since been corrected
to recognize numeric-prefix DSS keys, with a regression test. The executed C1
reader and all retained reports remain unchanged; the exact CCD associations
above were established from the original full local headers.

Parent unit-resolution addendum: a separate follow-up opened
[HEASARC's imaging guide, section 7.2](https://heasarc.gsfc.nasa.gov/docs/xmm/abc/node9.html)
and [ESA's command-line guide](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/sas_usg/USG/workcommandline.html).
Their explicit calibrated MOS PI selections associate numerical 200–12000 with
eV and PI > 10000 with the above-10-keV band. The actual MOS PI column comments
also identify measured energy in eV. The parent adopts that documented numeric
convention despite the generic CHAN unit label; no spectrum was inspected to
choose it. This resolves the numerical-unit choice, not the calibration accuracy,
relative-exposure or geometry requirements. The earlier concern above records
what the initial header-only review alone could establish.

BADPIX fields are RAWX, RAWY, TYPE, YEXTENT, BADFLAG; pn DLIMAP fields are
DLIODF/DLISAS, and HKAUX fields TIME/DSLIN. Their rows have not been decoded.
SRCLIST offers position/error and corrected-position columns, per-camera
mask/extent/quality metadata and many photometric/variability fields. Its
presence supports a narrowly selected geometry inspection, not authorization
to examine fluxes, source variability or identify new candidates.

## Smallest next metadata-value scope

Freeze a separate offline, bounded, explicitly allowlisted reader for the
existing files. Initially decode GTI START/STOP and EXPOSU TIME/TIMEDEL/FRACEXP
where supplied, preserving missing-value and interval failures. There are
97,015,688 declared EXPOSU payload bytes across the three files and 13,328 GTI
bytes; the pn frame table is not a tiny header addendum. Use per-table/streamed
processing and an explicit memory budget, not a nested EVENTS-array read.

Validate each CCD's timestamps, widths, gaps/overlaps, fractional values and
applicable GTIs; compare integrated summaries with declared ONTIME/LIVETIME
without forcing equality through an invented scale. In particular pn EVENTS
LIVETIME is about 40,782 s whereas per-CCD EXPOSU LIVETIME is about
46,701–47,320 s: their semantics/aggregation differ or require explanation,
and neither scalar can simply replace every aperture's bin exposure.

Next, only if required by the prospective geometry check, inspect the existing
BADPIX/window/DLIMAP metadata and a fixed, minimal geometry-only SRCLIST column
set. Retain source coordinates locally; report only eligibility and mask/area
diagnostics. HKAUX/DSLIN is available if discarded-line timing needs it, but
its mere presence is not a validated exposure algorithm. Source rows are not
detector footprints and do not replace an attitude/RAW mapping. No global
exposure map or additional product is required automatically; name the precise
missing input if existing metadata cannot establish stable aperture coverage.

This continuation can resolve timing/geometry choices before touching EVENTS.
Until then, retain `HEADERS_ADJUDICATED_COUNTS_NOT_READY`: no GTI-validity,
source isolation, count recovery, quiet background, useful sensitivity,
calibrated significance or discovery claim follows from these headers.

## Exact local header-report anchors

SHA-256 of the reports read, not an independent rehash of the FITS products:

| Slot | SHA-256 |
| --- | --- |
| 1 | `a6d78ea07324eeef06ed544555525ebb4e071f069eb428ed050913d6cbcbf0ba` |
| 2 | `a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae` |
| 3 | `4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417` |
| 4 | `d19ede1f11156b75954e4fa5de3d29c7ce0222bcfa816dc64ed88d7be6c78c3e` |
