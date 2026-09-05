# eROSITA census publication closeout — 2026-09-05

Status: **CENSUS ANALYSIS CLOSED; INTERPRETATION CORRECTED; LOCAL REVIEW PACKAGE BUILT.**

The historical audit reran with the existing project virtual environment and
local bulk inputs: initially **107 quantities, 93 VERIFIED / 14 CORRECTED**,
matching M5. Numerical agreement did not catch the following scientific issues.
After the declared interpretation withdrawal below its arithmetic audit reports
**92 VERIFIED / 15 CORRECTED**. Historical milestone reports retain their dates.

## Corrections before publication

1. **Prior-art framing withdrawn.** [DR2 §5.1](https://arxiv.org/html/2607.27772v1#S5.SS1)
   already discusses intrinsic/Poisson variability and counterpart probabilities.
   M5 and the draft were wrong to say it treats all unmatched sources as spurious.
   The draft now claims the bounded 261-position bright-source upper-limit/geometry
   census. Broad DR2 variability or vanished-source priority is not claimed.
2. **Candidate contamination bound withdrawn.** Zero of 60 steady controls gives
   `1 - 0.05**(1/60) = 0.04870`, a one-sided binomial bound for misclassification
   in that control population. It does not bound the fraction of false candidates
   among the 107 selected rows; that requires prevalence, completeness and a
   representative validation design. “Fewer than 6” was an invalid inversion.
   The script now writes null for `implied_max_contaminants`, and the historical
   audit explicitly marks that claim corrected. The 0/60 observation survives.
3. **Physical interpretation narrowed.** The 107 rows are fade candidates;
   0.09% is their selected fraction of the parent sample, not a measured switch-off
   rate. Poisson effects, reprocessing and confusion prevent guaranteed physical
   fading or a physical lower bound. No candidate has follow-up confirmation.
4. **Classifier attribution fixed from code.** `m2_archival_xray.py` queries
   [VizieR I/358/vclassre](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=I%2F358%2Fvclassre),
   the Gaia variability classifier, not DSC. The draft now cites
   [Rimoldini et al. 2023](https://arxiv.org/abs/2211.17238), A&A 674, A14, and
   [Marocco et al. 2021](https://arxiv.org/abs/2012.13084), ApJS 253, 8, for CatWISE2020.
   The uncertain DR2 journal issue has been replaced by its exact accepted arXiv
   reference, so a guessed bibliographic detail no longer blocks local completion.
5. **Bright-end class percentages corrected.** The old “71%/100% artifacts”
   counted indeterminate sources as artifacts. Above DET_LIKE 100 there are
   19 artifacts, one indeterminate and eight candidates: 68% artifacts. Above
   242 there are five artifacts and one indeterminate, not six artifacts.
   The abstract/body now keep these classes separate, and the scoped verifier
   checks the exact counts. The original figure caption already made this distinction.
6. **Remaining wording and package dependencies corrected in independent review.**
   The 261 sources are unmatched through `UID_DR1`, not devoid of all DR2
   counterparts. The +17/-8 threshold sensitivity is not a total uncertainty
   interval or a demonstrated dominant systematic. The packaged main note now
   links only to included review documents, and the exact Gaia/CatWISE column
   mappings and nearest-match rules are included in a separate scoped record.

The exact-input tally remains **148 artifacts / 107 candidates / 6 indeterminate**;
replaying the classification gives **99–124** candidates across cuts 1.3–2.0.
No new candidate search was performed. The updated draft is suitable for a
human decision about a modest methodological census note; “discovery paper”
would overstate its evidence.

## Primary-literature scope

Checked the release full text and primary indexed searches for `eRASS:3 vanished`,
`eROSITA vanished DR2`, `eRASS1 eRASS:3 variability`, and `eRASS:3 upper faders`.
No additional exact bright-census competitor was found in this bounded check.
It is not an exhaustive ADS review. The release itself was the material prior-art
correction; generic “unmined DR2” language is retired in the project README.

## Reproduce and review

From repository root, the existing broad audit is:

```powershell
erosita-dr2/.venv/Scripts/python.exe erosita-dr2/scripts/m5w_audit.py
python erosita-dr2/scripts/verify_census_package.py
python pta-mpta/scripts/build_publication_packages.py
```

The original audit needs NumPy, pandas, Astropy and pyarrow plus the wider local
`data/` and `out/` products. System Python lacks Astropy here; the existing
project environment worked. That historical audit returns zero even when rows
are corrected or unavailable; read its verdicts. The new scoped verifier fails
on headline/row/replay drift and on reintroduction of the withdrawn prose.

Local ZIP: `data/publication-review-2026-09-05.zip` (ignored).
[The manifest](publication/manifest-2026-09-05.json) records every file size/hash,
archive hash, exact commands and omissions. Contents are the main note only,
the 261-row census, 60 controls, aggregate selection record, census-only projection
of archival counterparts, the existing figure and figure code, and the scoped
verifier and [source mapping](publication/SOURCE-MAPPING-2026-09-05.md), for
**12 payload files** plus the internal manifest. No whole `out/` tree, riser material, fenced target packet, or XROM
photometry is included. Companion B is removed from the packaged manuscript.

From an extracted `erosita-dr2` directory:

```powershell
python scripts/verify_census_package.py
python scripts/m5w_figure.py
```

The verifier is standard-library-only. Figure regeneration needs NumPy/pandas/
Matplotlib; their original environment is not bundled. Parent selection, the
2% scale offset and counterpart retrieval are not independently regenerated by
this small archive; bulk FITS, the 198 MB pair table and remote response caches
remain external requirements. This distinction is explicit in its manifest.
The extracted ZIP passed the scoped verifier and regenerated the figure using
the existing runtime (NumPy 2.5.2, pandas 3.0.5, Matplotlib 3.11.1). The figure
was visually checked. The broader audit additionally used Astropy 8.0.1 and
pyarrow 25.0.1. Nine regression tests cover classification priority, missing
neighbours, the refusal to report candidate purity, scoped manuscript generation,
and self-contained review links/mappings.

## Human decisions

Choose whether the corrected narrow note merits submission; supply actual author
metadata and choose the venue; approve archive scope/license/DOI; review final
format and submit only after explicit authorization. The optional OGLE note and
all fenced follow-up proposals are separate decisions. No correspondence,
account, DOI, upload or submission occurred in this closeout.
