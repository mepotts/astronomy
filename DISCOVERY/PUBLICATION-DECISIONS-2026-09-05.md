# Publication and parked-front decisions — 2026-09-05

Executed local closeout of the existing PTA manuscripts, eROSITA census note,
and CHIME observing-window question. No publication, account, DOI, upload,
submission, or correspondence was performed.

| Front | Executed result | Current decision |
|---|---|---|
| PTA full paper | 137 quantities regenerated locally; 119 text checks passed; scoped package assembled and checked after extraction | **Analysis closed.** Recommend reviewing this as the primary publication unit. Author/venue/archive/DOI/submission decisions remain. |
| PTA table note | Independent source-table audit: 29 quantities; 22 text checks passed | **Analysis closed.** Choose whether this is an alternative or sufficiently distinct companion to the paper. |
| PTA composition note | 42 quantities regenerated; 49 text checks passed; existing Larsen credit remains necessary | **Analysis closed.** Human go/no-go on the narrowed contribution and overlap with the paper. |
| eROSITA vanished census | Original 107-row audit rerun; interpretation repaired; 148/107/6 and threshold 99–124 reproduce; scoped verifier and extracted figure pass | **Corrected local review package ready.** A modest census/method note, not 107 confirmed discoveries. |
| CHIME periodicity | Targeted official-source input check still yields no authenticated time-resolved observing product | **Parked.** Restart only on the specified data product and a new complete M1 protocol. |

The eROSITA closeout changed the scientific claim. The release paper already
discusses variability; the earlier claim that it ignored it was wrong. Zero of
60 steady controls does not determine contamination among 107 selected candidates.
The physical switch-off rate remains unknown. Gaia classification attribution and
bright-end artifact/indeterminate percentages were also corrected. Historical
M5 reports are prominently marked as superseded for those interpretations.

Review the concrete packages here:

- [PTA closeout](../pta-mpta/PUBLICATION-CLOSEOUT-2026-09-05.md) and
  [exact manifest](../pta-mpta/publication/manifest-2026-09-05.json).
- [eROSITA corrections and closeout](../erosita-dr2/PUBLICATION-CLOSEOUT-2026-09-05.md) and
  [exact manifest](../erosita-dr2/publication/manifest-2026-09-05.json).
- [CHIME park/restart record](../chime-frb-periodicity/PARKED-2026-09-05.md).

The local ZIPs live under each project's ignored `data/` directory. Manifests
give all member/ZIP byte counts and SHA-256 digests. PTA includes 611 explicitly
selected files; eROSITA includes 12, including its scoped Gaia/CatWISE source
mapping. Current compact-review links resolve to included files. The census archival table is projected to
exact census membership; no blanket `out/` archive, riser packet, private target
material, XROM photometry, or optional companion B is packaged. Raw chains,
bulk catalogues, some remote inputs and environments are intentionally omitted,
and the commands distinguish artifact checks from full raw-data reproduction.
The rebuilt local ZIPs are **1,526,425 bytes (PTA)** and **242,812 bytes (eROSITA)**,
including their internal manifests. Both were independently extracted and
checked: all member/archive hashes and current review links passed; PTA's
22/119/49 verifiers and 42-number methods generator passed, as did eROSITA's
28 scoped checks. The eROSITA regression suite now has nine passing tests.

Bounded literature refreshes are documented with primary-source links and
search terms in the closeouts. No exhaustive internet/ADS novelty claim is made.
The evidence supports closing these fronts for decisions and directing new
compute toward the separately ranked discovery pilot.
