# Notes on the RNAAS draft (`rnaas-subset-guard.md`)

Working notes for the draft, not part of it. **Nothing has been submitted anywhere.** The
draft is a draft; several things below must be resolved before it could be.

---

## 1. Word count

**1,499 words** for the note (title through references), of which the abstract is 146 —
inside the 1,500 / 150 limits, but only just. It was 1,250 on 2026-08-06; the 2026-08-07
revision spent the margin on correcting the statement of the MPC's criteria in §1 and adding
the ground-truth result to §4. **There is one word of slack.** Anything added now has to
displace something, and the counting method here is deliberately generous (every numeral in
a table cell counts as a word), so the true submitted count will be lower. Reproduce with:

```bash
python -c "
import re
t=open('docs/rnaas-subset-guard.md',encoding='utf-8').read()
i=t.index('\n---\n'); note=t[i+5:]
a=note.split('## Abstract')[1].split('##')[0]
wc=lambda s: len([w for w in re.sub(r'[|*#>_]',' ',s).split() if re.search(r'[A-Za-z0-9]',w)])
print('note',wc(note),'abstract',wc(a),'body',wc(note)-wc(a))"
```

Counts the title, author line, abstract, headings, every table cell, the caption and
footnote, and the references; excludes the front-matter block. Table cells are counted
generously (each numeral is a word), so the true submitted count under most editorial
conventions will be lower, not higher.

## 2. Table, not figure

Stated in the draft's front matter. The short version: the finding is four rates whose
denominators are the whole argument, plus a second rate (guard rejections *among links our
own acceptance gate already accepts*) that is the load-bearing number and is unreadable off a
bar chart. The rejected alternative was a scatter of residual RMS against used-observation
fraction; it shows the mechanism well but carries no denominators and answers a weaker
question. §3 of the draft recovers most of it in two sentences.

---

## 3. Load-bearing claims and where each is verified

Line numbers are as of this writing; section numbers are stable.

| Claim in the draft | Verified at |
|---|---|
| Guard is ≥ 80% of observations used **and** used observations span ≥ 3 nights | `src/itf_linker/fit/collide.py` — `MIN_USED_FRACTION = 0.8` (l. 73), `post_fit_collision_check` (l. 208–233); applied `src/itf_linker/fit/pipeline.py` l. 172–174, counted l. 206–211 |
| Guard is **not** an MPC criterion | `M3-RESULTS.md` §6.4; `M4-RESULTS.md` §9 ("6% → 74% → 84.4%"); the published list is in `DISCOVERY/itf-linker.md` "Published acceptance criteria" and implemented in `src/itf_linker/fit/gates.py` l. 27–81 |
| Eros: 6 of 24 obs, RMS 0.225″, `a` wrong by 9× | `M1-RESULTS.md` §2 item 3 and §6; restated in `collide.py` docstring l. 214–218 |
| **59 / 917 = 6.4%** | `M1-RESULTS.md` §5 table + §6; `m1-report.json` → `fits.failed_subset_guard` = 59, `fits.converged` = 917 |
| **4,413 / 5,950 = 74.2%** | `M3-RESULTS.md` §6.3 table + §6.4; `m3-fits.json` same two keys |
| **9,383 / 11,113 = 84.4%** | `M4-RESULTS.md` §5.3 table + §9; `m4-new.json` same two keys |
| **874 / 1,738 = 50.3%** | `M4-RESULTS.md` §6.3 table; `m4-old.json` same two keys |
| Older slice is a best-ranked 1.08% sample of 412,929 gated links | `M4-RESULTS.md` §6.2 and the §6.3 caveat block |
| Belt band reproduced the earlier run digit for digit | `M4-RESULTS.md` §4.1 (nine figures) and §5.1 (17,060 proposals, 1,427,490 refusals) |
| Horizons: 11/13 vs 4/13, none merged | `M4-RESULTS.md` §3 |
| 6.6× hypotheses → 26 more survivors, 140 vs 141 well constrained | `M4-RESULTS.md` §5.4 table and the §9 summary table (2,555 / 387 = 6.60) |
| 6,029 converged NEO orbits → 2 Amors, both from 1.40/1.70 AU hypotheses | `M4-RESULTS.md` §5.3 (5,547 = 147+3,688+1,712) + §6.3 (482 = 35+291+156) + §9 |
| Convergence rates 94% / 44% / 27% | `M1-RESULTS.md` §5 (917 of 975); `M3-RESULTS.md` §6.3 (43.7%); `M4-RESULTS.md` §5.3 (27.4%) |

### Numbers in the draft that are **not** in any `M*-RESULTS.md`

> **Correction, 2026-08-07 — read before quoting any "published criteria" figure below.**
> Throughout this file, "published criteria" means whatever `gates.post_fit_gate` rejected.
> That function is **our** gate and is stricter than the MPC's published rule on three
> counts: it applies the 0.25″ RMS ceiling unconditionally where the MPC applies it only as
> one conjunct of an arc-length bullet; it scopes the σ block to exactly-three-night links
> where the MPC has a separate bullet for more than 3 nights; and it never implemented the
> published `e < 0.5`. **The measurements below are unchanged and correct — they measure our
> gate.** Only the label is wrong. **The draft itself was relabelled on 2026-08-07** and now
> says "our acceptance gate" throughout, with §1 stating the MPC's actual conjunctive rule;
> this file's own tables below still use the old wording and are left as the record of what
> was measured. See `src/itf_linker/fit/gates.py`.

Columns 5 and 6 of Table 1, and all of §3, are derived here from the per-fit records
(`fits.outcomes[]`) in the four report JSONs. Method: a converged fit "meets all published
criteria" iff every entry in its `gate_reasons` is one of the guard's own reason strings
(`fit used only…`, `observations actually used span…`, `observation counts unavailable`);
the published-gate reasons emitted by `gates.post_fit_gate` are textually disjoint from
those. **Validation:** column 5 minus column 6 must equal each report's own
`fits.passed_all_gates`, and does in all four cases — 132−4 = 128, 497−288 = 209,
1,237−983 = 254, 431−313 = 118, matching `M1-RESULTS.md` §5, `M3-RESULTS.md` §6.3,
`M4-RESULTS.md` §5.3 and §6.3 respectively.

Derived figures used in §3, all from `m4-new.json`:

- median RMS 0.3925″ (guard-rejected) vs 0.2126″ (guard-passing), 9,383 vs 1,730 fits;
- 3,842 of 4,802 converged fits with RMS ≤ 0.25″ are subset fits (80.0%);
- 583 of the 983 marginal fits have RMS ≤ 0.10″;
- 11 of the 983 used exactly 3 observations;
- `lnk07em`: 3 nights, codes 095 + G96 + J43, 3 of 11 observations used, RMS 1.78 × 10⁻¹⁰″,
  a = 1.4240 ± 0.0237, e = 0.5026, i = 0.0169° ± 0.0041°, q = 0.7083 ± 0.00661,
  `gate_reasons` = the subset reason only. Find_Orb's own U parameter for it is 9.90.
- per-submitted-link rejection rates 59/975 = 6.1%, 4,413/13,618 = 32.4%,
  9,383/40,623 = 23.1% (§4 of the draft).

The scripts that produced these are throwaway and live in the session scratchpad, not in the
repo. **If the note is ever submitted, they should be committed** so column 6 is reproducible
by a reader. Two of the draft's other numbers now are: `scripts/rescore_gates.py` re-derives
the funnel under either gate from the on-disk fits, and `scripts/guard_vs_confirmed.py`
produces the zero-of-26 ground-truth result in §4.

---

## 4. Discrepancies found while checking, reported rather than silently resolved

1. **"Three times" vs "six and a half times" the hypotheses.** `M4-RESULTS.md` §5.3 says
   *"Three times the hypotheses bought 26 extra survivors"* and §7.3 says *"a grid three
   times denser"*, but §9's summary says *"Six and a half times the hypotheses"*.
   2,555 / 387 = **6.60**; the ≈3× figure is the *proposal* ratio (50,236 / 17,060 = 2.94),
   not the hypothesis ratio. The draft uses **6.6×**.
2. **6% vs 6.4%.** `M3-RESULTS.md` §6.4 and `M4-RESULTS.md` §9 both quote M1's rate as 6%;
   59/917 = 6.43%. The draft uses 6.4% throughout, including in the abstract.
3. **0.874 vs 0.8735 recall.** `M3-RESULTS.md` §4.2 and `M4-RESULTS.md` §4.1 for the same
   run — rounding only, and M4 flags it itself. Not used in the draft.
4. **`M4-RESULTS.md` §9 overclaims one sentence, and the draft does not repeat it.** §9 says
   the guard *"is rejecting more solutions than every published criterion combined"*.
   Measured over converged fits (`m4-new.json`), the published criteria collectively reject
   **9,876** and the guard rejects **9,383**, so as literally written it is false. What is
   true, and what the draft says instead, is that the guard rejects more than the published
   **0.25″ residual ceiling** does (9,383 vs 6,311), and that the ordering reverses on
   survey-made associations (59 vs 263). Full breakdown of converged-fit rejections:

   | Run | Converged | Guard | Any published | RMS ceiling | σ limits |
   |---|---:|---:|---:|---:|---:|
   | M1 | 917 | 59 | 785 | 263 | 761 |
   | M3 | 5,950 | 4,413 | 5,453 | 3,562 | 4,774 |
   | M4 new | 11,113 | 9,383 | 9,876 | 6,311 | 8,590 |
   | M4 old | 1,738 | 874 | 1,307 | 932 | 760 |

   Note the σ column is not an independent comparator: *our gate* applies those limits only
   to exactly-three-night links, and a fit can fail them *because* it fitted a subset. That is
   also why the draft compares against the RMS ceiling, which applies to everything.
5. **`m4-new.json` `fits.rms_le_0.25` = 4,801; the true count is 4,802.** Cause:
   `pipeline.py` l. 190 uses `(o.fit.rms_residual or 9e9) <= 0.25`, so an RMS of exactly
   `0.0` is falsy and is replaced by 9e9. Exactly one record is affected — `lnk0mj2`, which
   used 3 of 12 observations and reports RMS 0.0. It fails both the three-night σ gate and
   the subset guard, so **no conclusion anywhere changes**; but the draft says 4,802 where
   the report says 4,801 and the difference is this. **Fixed 2026-08-07** in both
   `fit/pipeline.py` and `link/run.py`, with a test. The stored `m4-new.json` still says
   4,801 — it was written by the old code — so the draft's 4,802 is right and any *re-run*
   will now agree with it.

---

## 5. What was cut, and why

Everything below is real and defensible; none of it is about *this* finding, and 1,500 words
does not stretch.

- **29P/Schwassmann-Wachmann 1** (`M4-RESULTS.md` §7.4) — four tracklets, 620 + 644, twelve
  days apart in July 2002, never associated, 1.2″ at 3 of 3 epochs, elements to 1.3σ. The
  best single result in M4 and the most quotable thing in the repo. Cut because it is
  evidence that the *linker assembles real objects*, not evidence about the guard, and
  stating it responsibly (it is an identification, not a discovery; one constituent trkSub
  is literally `000029P`) costs ~90 words. It belongs in a different note.
- **In-file ground-truth recall 0.8735 → 0.9302** (§4.1/§4.3) — measures the linker's recall,
  not the guard's behaviour. Cut.
- **The seven changes required to widen the grid** (§2) — the near root inside 1 AU, the
  geometric distance step, per-band window lengths from the curvature limit, the ρ̇ range,
  the grazing-ray guard, three scaling rewrites. A separate paper's worth of material.
- **The older slice's cross-observatory dominance** (94% vs 36%, §6.3) — arguably M4's most
  important result, and entirely orthogonal.
- **Vetting** (§7): SBIDENT's 9-year epoch limit, 2026 OB4 / 2026 DK65, "unmatched is not
  unknown", `orbit_too_poorly_constrained` as an independent instrument agreeing with the σ
  column. Cut wholesale.
- **The refusal counts** (1.4M → 129M → 900M non-discriminating neighbourhoods, §5.1/§6.1).
- Kept, at a cost of ~110 words, because each closes an obvious objection: **Horizons 11/13
  vs 4/13** (else "your grid simply cannot reach NEOs"), and **6,029 NEO orbits → 2 Amors /
  140 vs 141** (else "so what if the guard rejects a lot?").

---

## 6. Weaknesses a moderator or a reader will raise

Ordered roughly by how much damage each does.

1. **The guard's *own* accuracy is never measured.** "84.4% rejected" is not "84.4% were
   wrong associations". Nothing in the repo measures the guard's false-rejection rate — the
   in-file trkSub validation measures the linker's recall, not the guard's precision. The
   draft is careful to say "rejected" and never "were wrong", but a reader is entitled to
   ask, and the honest answer is that the number is a rejection rate and nothing more.
   `M4-RESULTS.md` §5.3 concedes the same shape from the other side: 27 of the 225 survivors
   have a fitted arc under 60% of the link's arc and passed anyway.
2. **The 0.8 threshold is arbitrary and unswept.** No sensitivity analysis exists at 0.6,
   0.7 or 0.9, and the headline rate is certainly a function of it. Nor is the ≥ 3-used-nights
   half of the rule separated out (it is the sole cause of 193 of the new slice's 9,383
   rejections, and of 28 of M1's 59 — a much larger share of the small number).
3. **The four rows differ in more than one variable.** Row 1's associations were made by
   surveys rather than any grid *and* cover the whole file *and* are mostly
   single-observatory *and* passed a trkSub collision pre-screen; rows 2–3 cover only the
   2023–2026 slice. So 6.4% → 74.2% measures provenance and population jointly. Only rows 2
   and 3 are a clean single-axis comparison, and even they changed band structure and window
   length along with the grid — mitigated, but not eliminated, by the belt band reproducing
   the earlier run digit for digit (§4.1).
4. **The conditioning is doing work.** Rates are per *converged* fit, and convergence itself
   falls from 94% to 44% to 27% as the grid widens. Per link submitted the guard's
   rejections go 6.1% → 32.4% → **23.1%**, which is not monotonic: the wider grid's bad
   proposals more often fail to converge at all rather than converging on a subset.
   Conditioning on convergence is the right choice for the argument (a fit that never
   converges never reaches an RMS gate) but it should be, and is, stated.
5. **Row 4 is a 1.08% best-ranked sample.** Its 50.3% is an underestimate by construction,
   and it breaks the tidy monotone story: the *same* wide grid rejects five-sixths on one
   slice and half on the other, so the rate is not a function of hypothesis count alone.
   Partly defused by the marginal column (72.6% vs 79.5%, much closer) — which is itself a
   reason to trust the marginal statistic more than the headline one.
6. **Size of the hypothesis space is confounded with *where* the hypotheses are.**
   `M4-RESULTS.md` §5.3 says it outright: the new hypotheses sit near 1 AU, where "tracklets
   that agree at 1.1 AU agree for many more reasons than tracklets that agree at 2.7 AU". So
   the driver may be the discriminating power of the added geometry rather than the count.
   The draft says "speculativeness", which is closer to right than "size", but it is a
   hedge, not a measurement.
7. **The guard cannot distinguish a wrong association from bad astrometry.** A fit that drops
   observations because one tracklet is genuinely mismeasured looks identical to one that
   drops observations because the tracklet belongs to another object. The `lnk07em` example
   in §3 is presented as an artefact of the fit, which the near-zero inclination supports,
   but the note cannot prove the association is wrong — only that the solution does not
   describe it.
8. **One fitter.** Everything may be a property of Find_Orb's specific outlier-rejection
   policy. No second orbit-determination code was run. This is the single cheapest
   improvement available and it was not done.
9. **The phenomenon is not new; only the quantification is.** "Check that the solution used
   all the observations" is old orbit-determination practice. A moderator may reasonably ask
   what is being reported. The answer must be the *measured provenance dependence* and the
   fact that it is invisible to the published criteria — not the existence of subset fits.
   The draft's title risks implying the latter. It was also changed from "does **not** raise
   the residuals" — M4 §9's phrasing — to "**need not**", because §3 measures that
   guard-rejected fits do have a higher median RMS (0.39″ vs 0.21″). The absolute form is
   contradicted by the project's own data and should not be reused anywhere.
10. **One snapshot, one machine, one author, no replication.** A single ITF pull
    (`Last-Modified` 2026-07-29), a single Find_Orb build, no run-to-run variance measured,
    and the guard was invented by the same project that now measures its effect. Binomial
    errors on the rates are negligible at these N; systematic ones are unbounded.
11. **"Meets all published criteria" in column 5 means the *post-fit* criteria.** The pre-fit
    ones (≥ 3 nights, ≥ 3-day arc, the singleton-tracklet rule) were applied before fitting,
    so every fit in the table already satisfies them. True, but not said in the draft; if a
    referee asks, that is the answer.
12. **A stricter RMS cut is the obvious counter-proposal** — "just use 0.10″ instead of
    0.25″". Checked: 583 of the 983 marginal fits are already inside 0.10″, so it does not
    work. Only that one alternative was tested.
13. **Availability.** `CITATION.cff` points at
    `https://github.com/mepotts/astronomy/tree/main/itf-linker`; the work described here is
    on the unpushed `advance-portfolio` branch and `main` does not contain M4. There is no
    DOI. A Zenodo deposit of the pipeline **and the four report JSONs** would be needed
    before the availability statement in the draft is true.
14. **The reference list is unverified.** Gray (Find_Orb) and the MPC criteria URL are safe.
    The HelioLinC citation (Holman, Payne, Blankley, Janssen & Kuindersma 2018, AJ, 156, 135)
    and FindPOTATOs (Nugent, Tan & Bauer 2025, PSJ, 6, 18 — DOI 10.3847/PSJ/ad9c6d, from
    `CITATION.cff`) were written from repository metadata and **must be checked against ADS**
    before submission. The draft calls the linker "HelioLinC-style", which is accurate as a
    description of the approach and should not be read as a claim to use that codebase.

---

## 7. If this goes further

- Run the guard at 0.6 / 0.7 / 0.9 and report the curve — cheap, and it converts the
  single most obvious objection into a measurement.
- Split the two halves of the guard (used fraction vs used nights) in the table.
- Re-fit a sample with a second OD code.
- Commit the derivation scripts for Table 1 columns 5–6.
- Decide whether the older-slice row belongs in the table at all; it is the honest row and
  the confusing one.
- Correct the sentence in `M4-RESULTS.md` §9 identified in §4 item 4 above. **Not done
  here** —
  the `M*-RESULTS.md` files belong to another agent this session — but it is a factual
  error in the milestone report and it is the one sentence a reader would most likely quote.
