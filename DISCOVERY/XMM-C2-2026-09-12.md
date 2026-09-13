# XMM C2: offline exposure and good-time values, no photons

Prospective parent decision, September 12. Freeze implementation, tests and
independent review before execution. The continuing authorized discovery work
permits this bounded inspection of already retained published-control data.
No network, new download, installation, publication or submission.

## Inputs and exact interpretation scope

Bind C1 outcome SHA-256
`c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc`
and verify its artifact closure using the frozen C1 source SHA-256
`13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5`.
Do not modify any C1 file or raw product. Use its accepted header offsets and
the first three expanded files; the fourth source-list product is out of scope.

Decode only the 24 EXPOSU and 24 STDGTI binary-table payloads already declared
by those headers: pn suffixes 01–12, MOS1 01,02,04,05,07, MOS2 01–07. Verify
the exact camera/exposure identity and suffix sets rather than inferring missing
chips. Header CCDID is not a unique pn detector identifier. Bind explicit
EVENTS data-subspace CCDNR-to-STDGTI alternatives, including numeric prefixes.

EXPOSU declares 97015688 payload bytes in total; STDGTI declares 13328 bytes.
Total newly interpreted payload allowance: **97029016 bytes**. Hashing original
inputs traverses bytes for integrity but does not interpret their other arrays.
This is the unique selected payload and the maximum per measurement pass;
worker measurement, parent verification and explicit offline replay each read
only that same set, with separate counters. Verification is not a new-table
allowance, and the reported worker byte total is not an aggregate of all replays.
Do not decode EVENTS, OFFSETS, BADPIX, DLIMAP, HKAUX, CALINDEX or SRCLIST.
No event counts, energy selection, positions, aperture geometry, light curves,
source ranking, new-source follow-up or photon-driven parameter choice.

Use a narrow reader that seeks directly to accepted table offsets and decodes
bounded fixed-width rows. Accept only the observed scalar schemas: pn EXPOSU
TIME D / FRACEXP E; MOS EXPOSU TIME D / TIMEDEL E / FRACEXP E; STDGTI START D /
STOP D, with explicit big-endian storage and verified row widths. Reject
unexpected FITS scaling/null conventions, columns, heap layouts or identities
rather than guessing conversions. Floating non-finite values are reported as
data-quality findings, not silently converted to zero.

## Measurements, not a calibrated exposure prescription

For every GTI table report row count, finite and positive-length validity,
ordering/overlap findings, endpoints and union duration. Invalid rows remain
counted; any union over only valid rows must be labelled as such. Do not claim
all rows valid from a summary that silently dropped failures.

For every exposure table report finite-time/width/fraction counts, nonpositive
widths, fraction range and outside-[0,1] counts, duplicates/non-increasing times,
first/last time and min/max consecutive spacing. pn candidate widths come from
the explicitly declared TIMEDEL header; MOS widths come from its TIMEDEL column.
Record width sums and fraction-weighted width sums over explicitly counted
valid rows, with min/max widths and fractions. These are descriptive arithmetic
diagnostics, **not an adopted live-exposure algorithm**. Compare with the exact
per-CCD ONTIME/LIVETIME/EXPOSURE metadata without fitting a scale to agreement.
Preserve differing global EVENTS and per-CCD quantities as different metadata.
Also retain each explicit EVENTS LIVETInn value and a separately labelled sum
of width times fraction for valid rows whose TIME lies in the matching valid
GTI union (half-open START <= TIME < STOP). This is a timestamp-membership
diagnostic, not exact integration of frame intervals at GTI boundaries. Compare
both unrestricted and GTI-member sums; do not choose whichever happens to match.

No nominal frame duration is inferred from adjacent times across gaps. No
dead-time factor is applied again because SETDEADT or a global ratio looks
plausible. The separate documentary semantics assessment must explain whether
and how these values support relative exposure before a counts protocol uses
them. Semantic findings do not authorize threshold tuning or another field.

## Resource and execution contract

- Offline only, one exclusive attempt in `XMM-C2-2026-09-12-data`.
- At most 100000 rows per read chunk; at most the exact allowed payload bytes.
  Tests must guard all other array spans and account for actual interpreted bytes.
- A 120-second worker deadline through the existing process-tree helper,
  SHA-256 `11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.
  Cleanup allowance is separate. Use the verified C1 memory-measurement pattern;
  monitored worker peak acceptance at most 500000000 bytes, not an OS allocation
  guarantee. No full-file or combined-camera array load.
- At most 1 MiB aggregate output JSON, including terminal receipts. Preserve
  a terminal-report reserve and partial results on failure. No array dumps,
  coordinates or arbitrary header/comment/exception text in public output.
- Bind source, tests, protocol snapshot, input outcome, relevant dependencies
  and runtime. Exclusive parent/worker markers prevent silent resumption.
  Record every planned table as completed, failed, interrupted or not attempted.
  Any nonzero worker exit or incomplete required report prevents technical success.
- Parent independently verifies input hashes unchanged, table manifest/byte
  accounting, receipt closure, resource outcomes and an offline replay of the
  same summaries. No changes to previous STOPs or C1 outcomes.

Strongest label: `ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED`. It establishes
observed metadata values and quality findings, not validated per-bin exposure,
quiet background, usable aperture geometry, recovered bursts or discovery.
Review these measurements and documentary semantics together, then define the
smallest remaining geometry/exposure step toward an actual counts experiment.
