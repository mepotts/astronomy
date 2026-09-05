# PTA publication decision package — 2026-09-05

Status: **ANALYSIS CLOSED; LOCAL REVIEW PACKAGE BUILT; NOT PUBLISHED.**

The three existing text-to-artifact verifiers pass again: table note **22/22**,
paper **119/119**, composition note **49/49**. No chains or additional scientific
experiments were run. These checks verify manuscript consistency with stored
artifacts; they are not a fresh 192-core-hour independent reproduction.
The local raw-input number generators were also rerun: 29 table-note quantities
(the one historical correction remains), 137 paper quantities, and 42 methods
quantities. All three text checks still pass after regeneration. The compact ZIP
was extracted into a separate ignored directory; its documented standard-library
checks passed there, so the package does not depend on the main checkout for them.

## Claim-specific literature refresh

Primary sources checked on September 5: [Miles et al. release](https://arxiv.org/abs/2412.01148)
remains v1; [Larsen et al. §4.1.4/Figure 8](https://arxiv.org/html/2503.20949v2#S4.SS1.SSS4)
already examines pulsar removal in factorized products. The narrower composition
claim and the credit installed in M6 therefore remain necessary. Searches included
`MeerKAT noise reproduction solar wind 2026`, `MeerKAT 576 588`,
`solar wind prior 26 MeerKAT`, and `pulsar composition factorised jackknife`.
No additional directly competing primary study was identified in this bounded
web/arXiv check. This is not an exhaustive ADS/citation-graph certification of novelty.
No generic claim to discovering composition sensitivity is restored.

Surviving local results: 576/588 agreement under the recorded base model; the
solar-wind prior experiment and 16–20/26 prior-sensitive/unconstrained census;
and the explicitly post-hoc composition diagnosis replacing the withdrawn
product-level significance claim. The full paper is the strongest coherent
publication unit. The two notes overlap it and should not automatically be
submitted as three independent contributions.

## Concrete local package

Build from repository root:

```powershell
python pta-mpta/scripts/build_publication_packages.py
```

Local ZIP: `data/publication-review-2026-09-05.zip` (ignored).
The exact member list, byte counts, SHA-256 hashes, archive hash, commands, and
limitations are in [the manifest](publication/manifest-2026-09-05.json).
All ZIP member bytes are verified against their hashes during assembly.
This compact package contains the three drafts, six milestone records, final
per-run summaries/manifests, selected final aggregate results and figures, and
relevant model/audit scripts. It excludes unrelated projects and raw chains.
There are **611 payload files** plus the internal manifest. The extracted
closeout links to that included `PACKAGE-MANIFEST.json`; historical milestone
references to deliberately omitted raw materials remain historical context.

After extraction, from its `pta-mpta` directory:

```powershell
python scripts/m4_note_check.py
python scripts/m5_paper_check.py
python scripts/m6_methods_note_check.py
python scripts/m6_methods_note_numbers.py
```

These commands require only Python's standard library. Full number regeneration
has additional requirements: `m4_note_numbers.py` needs the exact arXiv LaTeX
source, one released par file, and the recorded `enterprise_extensions` source;
`m5_paper_numbers.py` needs NumPy and all 83 original `.tim` files. Its existing
ToA counter does not fail closed when those files are absent, so do not run it
on the compact package. The manifest makes that limitation explicit.
Timing data are available under [DOI 10.57891/j0vh-5g31](https://doi.org/10.57891/j0vh-5g31);
M6 records the original runtime and licensing. Sampling additionally requires
that WSL scientific stack, the converted timing models, and the omitted
posterior/chain files or their regeneration. No portable full-rerun certification
is claimed. Creating a fuller DOI deposit requires reviewing that larger scope.

## Human decisions remaining

1. Choose the full paper, one note, or a clearly differentiated publication sequence.
   Recommendation: review the full paper first; assess overlap before selecting notes.
2. Supply actual author, affiliation, ORCID and venue; placeholders were not invented.
3. Approve the exact archive scope/license and a citable deposit, then paste its DOI.
4. Review the final venue-formatted manuscript and authorize submission separately.
   Any collaboration correspondence remains unsent.

The old M6 phrase “only the DOI” describes analytical readiness, not these
remaining author/editorial choices or a verified clean-machine chain reproduction.
