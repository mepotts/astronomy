# XMM C2 independent pre-execution review

2026-09-12: **GO for the fixed offline ancillary-value stage only.** The complete
protocol, C1 header adjudication, C2 implementation and tests were read. All 17
tests passed independently, including synthetic data and an actual-header-only
manifest/binding check; pinned Ruff passed. The reviewer decoded no real
scientific payload, made no network request and changed no implementation or
earlier artifact. This review document is the only reviewer-authored file.

## Fixed interpretation boundary

The manifest selects exactly 24 STDGTI and 24 EXPOSU tables from the first three
accepted C1 products, with the stated pn/MOS suffix sets and explicit CCDNR/DSS
associations. Numeric alternative ordinals are not confused with missing MOS1
CCDs. Parent and worker bind C1's original successful outcome and frozen source,
then use C1's read-only provenance/header replay before interpreting values.

The actual-header-only test forbids opening product files while constructing
the manifest and confirms 48 tables and 97029016 allowed bytes. Column names,
big-endian scalar types, row widths, units, layout, heap/scaling/null conventions,
time system and camera/exposure identity are checked before reads. Payload reads
seek to accepted offsets, stay within table spans, use at most 100000 rows per
chunk and account separately for bytes read and bytes successfully decoded.
Guarded synthetic streams reject reads outside the allowed ancillary span.

EVENTS and all other forbidden arrays remain outside this stage. Provenance
hashing traverses product bytes without interpreting other arrays. Parent replay
repeats the same allowed summaries, not a new table selection or expanded scope.

## Arithmetic and data-quality review

- GTI rows retain finite/nonfinite and positive/nonpositive counts. Only finite
  STOP>START rows form the explicitly labelled valid-row union. Original adjacent
  start ordering and sorted-interval overlap findings are reported separately.
- Exposure rows use declared pn TIMEDEL or the MOS TIMEDEL column, never a frame
  width guessed from consecutive timestamps. The valid-row predicate is explicit:
  finite time/width/fraction, positive width and fraction within [0,1]. Invalid
  values remain counted and flagged rather than becoming zeros.
- Adjacent differences retain pairs crossing chunk boundaries. Global duplicate
  finite times are counted separately from adjacent duplicates; nonfinite times
  do not silently bridge unrelated rows.
- Unrestricted and GTI-member width/fraction-weighted sums are both retained.
  Membership is half-open START<=TIME<STOP in the valid GTI union; it is a
  timestamp-membership diagnostic, not integration of finite frame intervals.
- Per-table ONTIME/LIVETIME/EXPOSURE and explicit EVENTS LIVETInn benchmarks stay
  distinct from global EVENTS metadata. Arithmetic differences are reported
  without choosing the better-matching sum or applying a dead-time rescale.

Synthetic tests cover invalid rows, overlapping/unordered GTIs, half-open
boundaries, repeated/non-increasing times across chunks, global duplicates,
empty tables, pn header widths across gaps and explicit byte accounting.

## Material preflight findings resolved

1. The initial manifest stored column descriptors as tuples. JSON converted them
   to lists, so a real worker would have failed binding equality before any
   payload decode. The reviewer independently reproduced this using only retained
   headers. Descriptors are now JSON-native lists, and the complete actual-header
   binding is tested for exact JSON round-trip equality under a no-product-open
   guard. Earlier synthetic worker tests alone would not have caught this.
2. Prelaunch or truncated-marker failures could lose the required 48-table ledger
   by reparsing the same damaged receipt during error handling. A narrow fallback
   now accounts for all 48 slots, distinguishing observed UNVERIFIED_ATTEMPT from
   NOT_ATTEMPTED without parsing damaged files. Dedicated regressions preserve a
   truncated marker and raw worker timeout code. Failure-artifact replay is
   explicitly labelled as leaving summaries unverified, not full summary replay.

The author's final self-audit also moved parent-memory receipt validation before
the failure-artifact replay branch. The reviewer verified that patch and its
zero-peak mutation regression; the final 17-test suite and Ruff pass again.

The synthetic end-to-end fixture verifies completed worker summaries, parent
assessment, full offline summary replay and rejection of tampered accounting;
a nonzero helper return cannot promote worker success. Failure privacy, terminal
memory reporting and output reserve are also tested. No further material
pre-execution blocker was identified.

## Resources, privacy and interpretation limits

The fixed payload allowance is 97029016 bytes per permitted interpretation pass.
The single worker has a 120-second helper deadline and monitored 500000000-byte
peak acceptance ceiling, not an OS allocation guarantee. Output JSON is limited
to 1 MiB including terminal receipts, with a reserve for failures. Source/tests,
protocol snapshot, runtime and input/dependency identities are bound. Exclusive
markers prevent silent resumption; incomplete required reports prevent success.

Outputs contain approved descriptive summaries and selected non-coordinate
metadata, not arrays, coordinates, arbitrary header comments or exception text.
`ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED` would establish measurements and quality
findings only. It does not adopt a live-exposure prescription, prove useful GTIs,
quiet background, aperture geometry, burst recovery, significance or discovery.
Interpretation requires the separate documentary semantics assessment before
counts can use these values. No prior STOP is changed and no new-data request,
publication or submission is authorized.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C2-2026-09-12-data/inspect_values.py` | `357edd17ee84755011e9adb41ecf523063be9303501d060bbfc416ceecd23f68` |
| `XMM-C2-2026-09-12-data/test_inspect_values.py` | `358714cd6998d3a53bf579cfe99ff31fa5d9b5b3bae7c79f8d28b8b482075273` |
| `XMM-C2-2026-09-12.md` | `ba74dd568f177de9f04042b34c9ac3cfac1ef3f9af6009fd66552370bc956f6a` |
