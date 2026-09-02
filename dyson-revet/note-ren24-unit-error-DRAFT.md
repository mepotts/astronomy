# DRAFT — NOT SUBMITTED

*Prepared 2026-08-18 in `dyson-revet` (milestone M2). This is a working draft for
Matthew's decision. It has **not** been submitted anywhere, shown to anyone, or posted.
Author and affiliation are placeholders. Nothing in this repository is sent externally
without explicit human approval.*

**Target venue if it is ever submitted:** Research Notes of the AAS (RNAAS).
**Format compliance** (checked against
<https://journals.aas.org/research-note-preparation-guidelines/>, 2026-08-18):

| RNAAS rule (quoted) | This draft |
|---|---|
| "1,500 words or fewer" and "The 1,500 word count limit includes title, headers, captions, and references with 150 words reserved for the required abstract." | **1,048 words** by the same inclusive counting (title + abstract + body + table + caption + references), measured on the note section only; abstract **135**. 450 words of headroom. AAS note: "the AAS Editorial office's word count is the final arbiter", and their recommended tool is `texcount -v3 -merge -incbib -dir -sub=none -utf8 -sum` on the `.tex` — re-count after AASTeX conversion |
| "no more than a single figure or table (but not both)" | **one table, no figure** |
| "as of May 1st, 2020 submission must included an abstract" | abstract present, 135 words |
| "*RNAAS* style for single author papers is first person singular — 'I' not 'we'." | first person singular used |
| "please do not use line numbers" | none |
| "not peer reviewed … unable to publish substantially novel theories, though short theoretical works building on work already published in mainstream journals are still welcome" | this is a correction/clarification of published arithmetic — squarely inside the stated scope ("comments and clarifications, null results") |

Submission, if ever, is via <http://aas.msubmit.net> in AASTeX v7+. **Not done.**

---

## A Factor-3600 Unit Conversion in the Hot DOG Surface Density Invoked to Explain the Project Hephaistos Dyson Sphere Candidates

**[AUTHOR NAME — PLACEHOLDER]**
**[AFFILIATION — PLACEHOLDER]**
**[ORCID — PLACEHOLDER]**

### Abstract

Ren, Garrett & Siemion (2024) proposed that background hot dust-obscured galaxies
(Hot DOGs) account for the seven Dyson sphere candidates of Suazo et al. (2024),
quoting a Hot DOG surface density of "approximately 1 per 31 square degrees …
which translates to about 9 × 10⁻⁶ per square arcsecond." That conversion is
high by a factor of 3600: 1/31 deg⁻² = 2.49 × 10⁻⁹ arcsec⁻², and 9 × 10⁻⁶ is the
value per square *arcminute*. Using the density as printed, one expects ~1500
chance alignments within 3.25″ among 5 × 10⁶ stars; using the correct conversion
of the same catalogue, 0.41. Catalogued Hot DOGs therefore account for about
0.4 of the seven candidates, not all of them. The paper's qualitative conclusion
survives, but through a fainter population — one whose density Suazo et al.
themselves estimated, and which JWST has since resolved directly.

### 1. The statement

Suazo et al. (2024) selected seven candidate Dyson spheres from ~5 × 10⁶
Gaia × 2MASS × WISE stars within 300 pc. Ren et al. (2024) replied that background
Hot DOGs could reproduce the sample, writing: "Hot DOGs also have a surface density
of approximately 1 per 31 square degrees (Assef et al. 2015), which translates to
about 9 × 10⁻⁶ per square arcsecond. This density is therefore sufficient to explain
the levels of contamination observed."

### 2. The conversion

One square degree contains 3600² = 1.296 × 10⁷ square arcseconds, so

  1/31 deg⁻² = 0.03226 deg⁻² = **2.49 × 10⁻⁹ arcsec⁻²**.

The printed 9 × 10⁻⁶ is 3616 times larger. It is exactly the per-square-*arcminute*
value: 0.03226/3600 = 8.96 × 10⁻⁶ arcmin⁻². The slip is a single missing conversion
step, and the correct figure is recoverable from the sentence itself.

### 3. What it changes

Treating background sources as a Poisson field of density ρ, the probability that a
given star has at least one within radius r is 1 − exp(−ρπr²). Table 1 evaluates this
for every density in the discussion, at the 3.25″ W3 PSF half-width used by
Suazo et al. and at the ~1″ separations JWST has since measured.

Read the first two rows together: as printed, the density implies ~1500 contaminants
among 5 × 10⁶ stars — a number so far above 7 that no candidate could survive, and
one that would also have contaminated a large fraction of the whole parent sample.
Correctly converted, the same catalogue yields **0.41** — catalogued Hot DOGs
explain roughly 6% of one of the seven candidates. Blain's (2024) larger WISE Hot DOG
compilation raises this only to 1.28. The conclusion "sufficient to explain" does not
follow from the cited number; it follows from the mis-converted one.

### 4. The conclusion survives, with a different contaminant

This is not a refutation of the physical suggestion. The last two rows of Table 1
show where the contamination budget actually comes from. Suazo et al. (2024)
independently estimated ~15000 sr⁻¹ = 4.57 deg⁻² for *faint* background galaxies with
W4 fluxes and W3 − W4 colours comparable to their candidates' — objects roughly an
order of magnitude fainter than Assef et al.'s catalogued Hot DOGs. That density
predicts 5.5 blends within 1″ among 5 × 10⁶ stars, against the 5.78 deg⁻² required to
produce all seven at that separation. Zackrisson et al. (2026), using the correct
0.032 deg⁻² for catalogued Hot DOGs, reach the same place from the other side: those
"numbers fall short by several orders of magnitude", and the contaminants must be
Hot-DOG-*like* objects fainter than any targeted by Hot DOG surveys. JWST/MIRI imaging
and spectroscopy then found precisely that at two candidates — an AGN-like galaxy at
z ≈ 0.9 about 1″ from candidate D, and a dusty-starburst-like galaxy at z ≈ 0.4 about
1″ from candidate E (Zackrisson et al. 2026).

So the corrected arithmetic is not merely bookkeeping: it points at a specific and
much fainter contaminant population, and that population is the one that was found.
The mis-converted number reached the right verdict for a reason that does not hold.

### 5. The state of the record

The error has been noticed once. Blain (2024, footnote 6) writes: "Ren, Garrett &
Siemion 2024 quote 0.032 deg⁻² = 9 × 10⁻⁶ arcsec⁻² (sic); however, the full HotDOG
catalogue is a little larger, with 2220 found over 70 per cent of the sky, yielding
0.1 deg⁻² = 7.7 × 10⁻⁹ arcsec⁻²." His own conversion is correct. That "(sic)" appears
to be the only public notice; I have found no erratum or corrigendum registered with
Crossref for doi:10.3847/2515-5172/ad5017, no second arXiv version of 2405.14921, and
no restatement of the correction in any citing paper. The sentence stands unchanged in
the version of record and — because it also appears in the abstract — in every
abstract service that indexes it.

The authors have, in effect, already moved on: Ren et al. (2025) and Ren et al. (2026)
carry the conclusion forward while attributing it to Blain's analysis rather than to
their own density estimate, and two of the three (with Assef, whose catalogue supplied
the number) are co-authors of the JWST paper that uses 0.032 deg⁻² correctly. Nothing
here is in dispute between us; what is missing is a citable correction, and this note
is meant to be one.

### Table 1

*Chance-alignment expectations for a Poisson background field. N is the number of the
5 × 10⁶ Suazo et al. (2024) stars expected to have at least one background source
within r. The last line is the density required to produce all seven candidates.*

| Population | ρ (deg⁻²) | N (r = 3.25″) | N (r = 1.0″) |
|---|---|---|---|
| Ren et al. (2024), as printed | 116.6 | 1493 | 141 |
| Assef et al. (2015) Hot DOGs, converted correctly | 0.0323 | 0.41 | 0.039 |
| Blain (2024) full WISE Hot DOG sample | 0.100 | 1.28 | 0.12 |
| Li et al. (2025) z < 0.5 Hot DOGs | 0.0024 | 0.031 | 0.0029 |
| Suazo et al. (2024) faint red galaxies | 4.57 | 58.5 | 5.5 |
| *required for all seven candidates* | *0.547 (r = 3.25″); 5.78 (r = 1.0″)* | *7* | *7* |

### References

Assef, R. J., et al. 2015, ApJ, 804, 27.
Blain, A. W. 2024, arXiv:2409.11447.
Li, G., et al. 2025, ApJ, 981, 104.
Ren, T., Garrett, M. A., & Siemion, A. P. V. 2024, RNAAS, 8, 145,
doi:10.3847/2515-5172/ad5017.
Ren, T., Garrett, M. A., & Siemion, A. P. V. 2025, MNRAS, 538, L56.
Ren, T., et al. 2026, arXiv:2607.03619.
Suazo, M., et al. 2024, MNRAS, 531, 695.
Zackrisson, E., et al. 2026, arXiv:2607.09460.

---

## Working notes (NOT part of the note — strip before any submission)

**Provenance of every number in Table 1.** Generated by
`scripts/m2_note_table.py` → `out/m2_note_table.csv`; the same conversions are
independently reproduced in `scripts/w2_chance_alignment.py` →
`out/w2_chance_alignment.csv` (M1). All Poisson, ρπr².

**Quotes and how they were obtained** (research done 2026-08-18):

- Ren et al. 2024 sentence: verified **identical in the arXiv preprint and in the
  version of record**, the latter read from the deposited PDF in the Oxford ORA
  record (uuid:b28a00fc-642e-4b94-affd-6106a6735429). The sentence is also in the
  abstract.
- Blain 2024 footnote 6: read from arXiv:2409.11447 (v1, 17 Sep 2024; sole author;
  **still an unpublished preprint** — no journal-ref, no DOI beyond arXiv, absent
  from Crossref).
- Zackrisson et al. 2026 §5.1 quotes ("fall short by several orders of magnitude";
  the ≥0.5 / ≥6 deg⁻² requirements): read from arXiv:2607.09460.
- No erratum: Crossref record for 10.3847/2515-5172/ad5017 has empty `update-to`
  and empty `relation`; ORA record shows none. **Caveat — could not check:**
  iopscience.iop.org is bot-blocked (Radware), so the live IOP article page was
  never viewed for a correction banner; PubPeer returns 403, so a post-publication
  comment there would have been invisible. **Both should be checked in a browser
  before this is ever submitted.** NASA ADS was also unreachable (405/401), so the
  citing-paper list came from OpenAlex + Semantic Scholar + direct full-text reads,
  which may be incomplete.
- Zackrisson et al. 2026 §5.1 contains its own copy-paste slip: both the ≥0.5 and
  the ≥6 deg⁻² requirements are parenthesised "within 3.25 arcsec"; the second
  should read "within 1 arcsec" (π(1″)² × 5 × 10⁶ = 1.21 deg² ⇒ 7/1.21 = 5.8).
  Reproduced here in Table 1's last line. **Not** mentioned in the note — it is a
  typo in an unrefereed preprint that will likely be caught in proof.

**Honest novelty assessment.** Blain flagged the arithmetic in September 2024. What
is not anywhere in the literature: the magnitude and nature of the slip (3600×; the
printed value is the per-arcmin² one), and the fact that it *inverts* the stated
conclusion — Zackrisson et al. (2026) use the same Assef et al. number in the
correct unit and get "falls short by several orders of magnitude" where Ren et al.
got "sufficient". §5 of the draft credits Blain explicitly and first. If Matthew
would rather not publish a correction that is 60% pre-empted, the fallback is to
fold §§2–4 into the candidate-I dossier and drop the note.

**Precedent for the venue:** Mullan (2026), RNAAS 10, 162, is a short RNAAS note
commenting on these same Hephaistos candidates (a different hypothesis — M-dwarf
flares), so RNAAS demonstrably accepts commentary in this thread.
