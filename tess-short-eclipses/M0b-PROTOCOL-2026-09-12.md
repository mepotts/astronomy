# M0b: corrected single-sector metadata eligibility

Specified after M0's [acquisition failure](M0-ACQUISITION-RESULT-2026-09-12.md),
before any control flux was read, searched or plotted. Initial source/protocol
are preserved in commit `c2f0307`. This is a metadata correction, not a relaxed
scientific test. [Original M0 search and acceptance](M0-PROTOCOL-2026-09-12.md)
remain unchanged and are incorporated by reference, including its explicit limits.

## Uniform eligibility amendment

For all three fixed TICs, require PUBLIC TESS SPOC provenance, 120 seconds,
and a single-sector observation ID of the documented form
`tess{date-time}-s{sector}-{TIC}-{processing}-{cr}` (cosmic-ray suffix one of
x/s/a/b). Parsed TIC/sector must match metadata and the specified control.
Exclude multi-sector DV bundles **before** ranking by sector then obsid.
Keep newest eligible sector and greatest obsid; then the original SCIENCE LC
product/lexical filename rule. Stop if the fixed sector changes or LC is missing.
See [MAST data-product naming](https://archive.stsci.edu/missions-and-data/tess/data-products).

Selected sectors remain 99/72/57 for TIC 450781262/53206761/2041210548.
The expected correction for the second target is from multi-sector DV obsid
208734076 to single-sector obsid 198789561. This is not a target substitution.

Retain M0 metadata/results unchanged. M0b metadata and input receipts use
`data/m0b/`; results use `out/m0b-*.json`. Reuse an original file only if amended
selection gives exactly its obsid/filename/size and its bytes match its recorded
hash. Record the original receipt path/hash plus the newly checked input hash;
do not rewrite the original receipt. Other input requires bounded acquisition.
The same three-product total cap applies; reused bytes are counted as inputs,
not newly downloaded network bytes.

Independent review accepted this pre-flux correction and supplied tests/identity
requirements. Before first flux analysis, the implementation also filters every
required BLS output for finiteness before maximization (not after discarding an
invalid winning row), with no change to grid, thresholds or grading.
