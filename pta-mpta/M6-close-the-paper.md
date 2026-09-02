# M6 — close the paper: citations, the prior-art re-sweep, the cold read, and the methods note

*2026-08-24. Sixth milestone of avenue #2, and a closing one. Repo law: every externally-sourced
number carries its source URL or the mark UNSOURCED; negative results are results; blockers are
findings; corrections are declared, not retro-edited.
Foundation: [`M1-access-reproduction.md`](M1-access-reproduction.md),
[`M2-converge-scale.md`](M2-converge-scale.md), [`M3-noise-criticism.md`](M3-noise-criticism.md),
[`M4-finish-the-array.md`](M4-finish-the-array.md) and
[`M5-ess-floor-sw-census-and-the-paper.md`](M5-ess-floor-sw-census-and-the-paper.md).
M6 executes M5 §8.2's recommendations 2, 3 and 4, plus the cold read and the final verification
pass. **Recommendation 1 — the archive DOI — is Matthew's and was not taken.**
No new chains were run; M6 is documentation, verification and one external sweep.*

**Goal, as set: both drafts submission-ready the instant the DOI is minted, with nothing left but
pasting it in. That goal is met, and a third document now exists.**

---

## 0. What M6 changed, in one page

| # | thing | outcome |
|---|---|---|
| 1 | Software and facility citations | **DONE.** Every package cited in the form its own authors ask for, versions inline. SARAO's required acknowledgement, the **additional PTUSE acknowledgement**, and Data Central's requested sentence are all quoted verbatim from the policies themselves. |
| 2 | Abstract | **333 → 240 words** (MNRAS's 250-word limit verified live). |
| 3 | Prior-art re-sweep | **Positioning changed on two of four claims** (§2). One is a partial scoop; one is a reframe. Both are folded in and both are declared. |
| 4 | Cold read for tone | **Ten changes** (§3), including the title. |
| 5 | Composition-jackknife methods note | **DRAFTED — NOT SUBMITTED** ([`draft-rnaas-composition-jackknife.md`](draft-rnaas-composition-jackknife.md)), 1,300 words against a live-verified 1,500-word RNAAS limit, with its own numbers script and its own checker. |
| 6 | Final verification | **Paper 119 checks / 0 failures on 137 audited numbers; table-audit note 22 / 0 on 29; methods note 49 / 0 on 42.** The paper's audit grew by 32 rows because a token-level sweep found content numbers it had not reached. |
| 7 | Errors found in our own drafts | **Four** (§5.2), all caught by machine rather than by re-reading: a wrong author list on a reference, two growth-curve range numbers, and 32 uncovered numbers. |
| 8 | What remains | **The DOI. Nothing else.** (§6) |

---

## 1. Citations and acknowledgements (M5 rec 2)

### 1.1 The rule applied

Each package is cited **in the form its own authors ask for**, checked at that project's repository,
`CITATION.cff`, docs or ASCL entry on **2026-08-24** — not in the form convention would suggest, and
not from memory. Where a project asks for a specific release and we ran a different one, the release
they ask for is cited and **the version actually run is printed beside it**. Seven findings worth
recording because each would have produced a wrong citation:

1. **`enterprise`** asks for a Zenodo record (Ellis, Vallisneri, Taylor & Baker 2020, v3.0.0,
   doi:10.5281/zenodo.4059815), **not** its ASCL entry — the ASCL record itself defers to that DOI.
   There are two separate Zenodo series for this package and the GitHub auto-archive one carries a
   machine-harvested creator list including a bot; "the latest Zenodo DOI" would have been wrong.
2. **`enterprise_extensions`** asks to be cited **with no DOI at all** — a GitHub URL, v2.4.3,
   Taylor, Baker, Hazboun, Simon & Vigeland 2021. Its README's DOI lines are commented out with an
   unfilled placeholder and it has no ASCL entry. We ran 3.0.3 and say so.
3. **`PINT` asks for two papers** (Luo et al. 2021 *and* Susobhanan et al. 2024). Its own
   `citation.cff` names only the first, so GitHub's "Cite this repository" widget under-cites it.
4. **`tempo2` asks for papers I and II only** (Hobbs et al. 2006; Edwards et al. 2006). Paper III is
   about gravitational-wave simulation, is not requested, and is not cited. **We also state that we
   never ran `tempo2`** — the setup deferred it deliberately — so it is cited as the origin of the
   release's own fits and nothing more.
5. **`parallel-bilby` is Smith, Ashton, Vajpeyi & Talbot (2020)**, and it has no Zenodo DOI to cite.
6. **`enterprise_warp` has no citation request of any kind** — no paper, no `CITATION.cff`, no ASCL
   or Zenodo record. It is referenced by URL, which is how the MPTA paper references it too.
7. **Geyer (1992)**, *Statistical Science* **7**, 473, doi:10.1214/ss/1177011137 — the initial
   positive-sequence estimator is §3.3 of that paper. The article's own running header says
   "473–511", which spans the published discussion and rejoinder; the article is 473–483.

### 1.2 Exact versions, inline (M5 rec 2, second half)

§2.2 now names them: `enterprise` 3.5.0, `enterprise_extensions` 3.0.3, `PTMCMCSampler` 2.1.4,
`PINT` 1.1.6, Python 3.12.3, NumPy 2.5.2, SciPy 1.18.0, Astropy 8.0.1, Matplotlib 3.11.1 — read from
the environment's own `dist-info`, not from prose. One further sentence was added because it is
checkable rather than assumed: `enterprise` imports a sparse-Cholesky backend at module level which
is **not installed here** and is replaced by a stub that raises on every entry point, so we can state
that every likelihood evaluation behind the paper took the dense `scipy` route.

### 1.3 The facility acknowledgements the data policy actually requires

The instruction was to check what the policy says rather than assume it, and checking changed the
answer three times.

- **SARAO's required wording, verbatim** from two independent primary sources — the SARAO/SKA-Africa
  knowledge base ("Science with MeerKAT", page version 52, last edited 2026-05-25) and the
  controlled document *MeerKAT Telescope and Data Access Guidelines* (SSA-0003C-001 Rev 02, §7.2,
  which uses "required" rather than "requested"):
  > "The MeerKAT telescope is operated by the South African Radio Astronomy Observatory, which is a
  > facility of the National Research Foundation, an agency of the Department of Science and
  > Innovation."

  **A search-result summary gave the department name as "Science, Technology and Innovation", which
  is wrong for the current policy.** The raw page and the PDF both say *Science and Innovation*, and
  so does the MPTA paper itself. This is exactly the class of error the sourced-or-UNSOURCED rule
  exists to catch, and it was caught by reading the source rather than the summary of it.
- **PTUSE requires a second, additional acknowledgement**, and it was not in anyone's brief. The
  User Supplied Equipment page states that publications using PTUSE "should include the following
  statement **in addition to** the standard MeerKAT acknowledgement", and the MPTA data are PTUSE
  data. The full paragraph — funders, system integration, and the OzGrav grant CE170100004 — is now
  in the Acknowledgements. (The S-band statement does **not** apply: this release is L-band. TUSE's
  "please cite Rajwade et al." requirement does not apply either, because that is TUSE, not PTUSE.)
- **Data Central asks for one sentence**, and it is included: *"This paper includes data that has
  been provided by AAO Data Central (datacentral.org.au)."*
- **The MeerTime/MPTA project imposes no re-use obligation of its own.** Its data-release policy is
  internal — membership, release timing, authorship — and states no citation, acknowledgement,
  embargo or permission requirement on an external re-user. The paper's own Data Availability
  section is one sentence pointing at the Data Central DOI, with no conditions. The "cite this paper
  and include the Zenodo DOI" request on the MeerTime site is **TPA-specific**, not MPTA.

### 1.4 A correction to M1: the release IS licensed

**M1 recorded "no license stated". That was right about the web pages and wrong about the dataset.**
The registered DOI metadata carries `"rights": "Creative Commons Attribution 4.0 International"`,
`rightsIdentifier: cc-by-4.0` (`api.datacite.org/dois/10.57891/j0vh-5g31`, retrieved 2026-08-24;
registrant `mqu.dcentral`; metadata last updated 2026-01-12). CC BY carries a real attribution
obligation, so the paper now **cites the dataset itself** — Miles et al. 2024, Data Central,
doi:10.57891/j0vh-5g31 — alongside the paper describing it. This is row 11 of the paper's own
corrections table.

### 1.5 One verification trap, recorded

Fetching the paywalled OUP page for the MPTA paper produced a **fabricated Data Availability
section**, claiming the data live "on the OzStar supercomputer", that users "must comply with the
IPTA data access policy", and that they "should acknowledge the MPTA collaboration and cite this
publication". **None of that is in the paper.** The real section is one sentence and imposes
nothing. It was caught by reading the arXiv HTML of the same paper. A summariser over a page it
cannot actually see will invent the section you asked about; the defence is to demand the verbatim
text and to check it against a source that is not paywalled.

---

## 2. The prior-art re-sweep (M5 rec 3), dated 2026-08-24

**Method.** arXiv (API and full-text grep of the highest-probability candidates), Crossref,
OpenAlex, INSPIRE, GitHub, and the DataCite record. **NASA ADS refused automated access again**
(401 on the API without a token, 405 on the UI), Google Scholar is behind a captcha, and
`academic.oup.com` hard-403s. Coverage is stated with the result, not after it.

### 2.1 The counts, and the blind spot that mattered

| source | citing works | note |
|---|---|---|
| OpenAlex `W4405033984` | 44 | the count M4/M5 used |
| **INSPIRE** `recid 2854865` | **76** | not swept before; enumerated in full |
| Crossref | 52 | — |
| NASA ADS | — | refused |

Nothing has cited the paper since 2026-08-10, and nothing in the 2026-08-20 → 24 window. Enumerating
INSPIRE's 76 found nothing bearing on claims (i)–(iii).

**But the sweep's most important find was not in any citing-works list, and could not have been.**

### 2.2 Claim (iv) is PARTIALLY SCOOPED — and the paper now says so

> **Larsen, B., Mingarelli, C. M. F., Baker, P. T., et al. 2025, MNRAS 542, 3028**
> (arXiv:2503.20949, doi:10.1093/mnras/staf1420), *Rapid construction of joint pulsar timing array
> data sets: the Lite method*. Its **§4.1.4 and Figure 8** perform a drop-one-pulsar analysis of the
> factorised-likelihood common amplitude on **a difference of two products**, and conclude, verbatim
> from the caption: *"Several individual pulsars, when removed by themselves, skew the estimates of
> ΔA, showing the overall discrepancy is sensitive to systematic errors in the individual pulsars."*

That is the qualitative form of what M4/M5 treated as a new observation. Two further pre-statements
of its premise: **Reardon et al. (2023)** write that three named pulsars — including J1909−3744 —
"are likely to dominate the factorized likelihood", and **Johnson et al. (2022)** study how a
factorised *upper limit* responds to pulsar ordering and dropout.

**What survives as new, and it is narrower than M5 wrote:** the composition sensitivity measured on
the *same axis* as the product's own credible interval and compared with it (jackknife SE 0.256 dex
against a 68% width of 0.149 dex, so the tighter product is the more composition-sensitive one); the
accumulation resolved to the single addition at which it happens (1.92 → 0.37 dex at J1909−3744);
and the operational rule that a fixed threshold with no composition term is not a significance test,
with a withdrawal of our own as the worked example.

**Both the paper (§6.2) and the methods note now lead with the credit**, and the paper's corrections
table gains row 13: *"We described both of §6.2's composition measurements as new" → Narrowed.*

**Why the earlier sweep could not have found it.** Larsen et al. is an IPTA DR2 paper and **does not
cite the MPTA release**, so it appears in no citing-works list for it. A sweep built from citation
graphs is structurally blind to parallel work that does not cite you. That lesson is now a sentence
in the paper's threats-to-validity section, not just in this document.

### 2.3 Claim (ii) is NOT scooped, but it is REFRAMED — the prior is public, as uncited code

The sweep reported, and **this session verified directly** rather than taking it on trust:

```
$ curl -s https://api.github.com/repos/MattTMiles/MPTAGW   →  public, license: None,
                                created 2022-08-18, last push 2025-01-28
$ grep -n "gamma_sw\|log10_A_sw\|n_earth" enterprise_run.py
  454:    n_earth    = parameter.Uniform(0, 20)
  462:    log10_A_sw = parameter.Uniform(-10, 1)
  463:    gamma_sw   = parameter.Uniform(-4, 4)          [6 occurrences in the file]
```

The repository belongs to the paper's first author, is titled "Scripts relating to GW search in the
MPTA", and has **no README, no licence, no release tag and no DOI**; it is cited by no MPTA
publication and is not part of the archived release.

**Three consequences, all now in the paper.**

1. **"Undocumented" survives; "unreachable" does not.** The paper's §4.1 now states plainly that the
   number is *not unknowable, only undocumented* — it appears in no paper, in no data product, and
   in nothing either of them points a reader towards. Every "cannot be reached" framing was checked;
   the §4.1 heading is now *"Seven published values lie outside the prior a reproducer would guess"*.
2. **Our blind choice was their choice.** We registered U(−4, 4) to bracket the published column
   before knowing the repository existed. It is the range the code sets. Our declared
   log₁₀A_SW prior, U(−10, 1), is *also* identical to it; our n_earth prior, U(0, 30), is wider than
   its U(0, 20), and n_earth agreed everywhere under both. **This strengthens the diagnosis** — the
   twelve disagreements really are a prior mismatch and nothing else — and the paper says so in
   §4.2 while stating that it cannot confirm the repository is the pipeline behind the table.
3. **The recommendation gets cheaper, not weaker.** §9's first fix now notes that the ranges are
   already written down in at least two machine-readable places, so printing them is transcription.

A related nuance, also folded in and turned against ourselves: **γ ∈ [0, 7] is the convention for
*dispersion-measure and achromatic red* indices, not for the solar wind.** Where a numerical
solar-wind index prior is printed in the literature it is wider and admits negatives — Susarla et
al. (2024), A&A 692, A18, Table 1: γ_SW ~ U(−6, 5). §2.3 now makes that point against our own
choice rather than leaving it for a referee.

### 2.4 Everything else the sweep checked, and found unchanged

- **No erratum.** Crossref reports `update-to: None`, `updated-by: None`, `relation: {}` on
  doi:10.1093/mnras/stae2572 — meaningful, because Crossref does register MNRAS corrections.
- **arXiv:2412.01148, 2412.01153 and 2412.01214 are all still v1**, no ancillary files.
- **No second public MPTA release.** MPTA-DR3 exists but is internal: Di Marco et al. (2026) state
  verbatim that their data set "is an internal, preliminary version… not yet publicly available".
- **The Data Central DOI still holds exactly four files**, 83 `.par` + 83 `.tim` and no
  configuration or prior file of any kind.
- **`enterprise_extensions`' `solar_wind_block` is unchanged** since the September 2025 widening to
  U(−6, 5). Two commits have touched the file since; neither goes near the prior. A bonus finding:
  at the commit contemporaneous with the paper the default was U(−2, 1), which two published values
  fall below and most of the rest fall above — **independent evidence that the collaboration did not
  use the library default of the day**, which corroborates the MPTAGW range.
- **The two nearest neighbours are still not competitors.** Mishra et al. (2026, now MNRAS) has no
  tables at all and zero occurrences of "uniform"; Di Marco et al. (2026) works on one pulsar of the
  *internal* DR3, excludes solar wind entirely, and reports agreement.
- **Kulkarni et al. (2025, MNRAS 544, 2795)** test scattering-variation fidelity on this same
  release. It is the nearest MPTA-internal work and is now cited in §5, because it points the same
  way from a different direction.

### 2.5 One doubt raised by the sweep, resolved in our favour

The sweep's PDF text extraction of the published tables yielded "roughly 510–520" values rather than
588, and flagged it as cheap to re-check. **It re-checks clean.** Our 588 comes from an independent
parse of the arXiv **LaTeX source** (not the PDF) counting every `${x}_{-a}^{+b}` cell across both
longtables — 83 noise rows plus 23 deterministic rows — and it is cross-checked against a second,
separately written parser at **504 noise values, 0 mismatches**. A PDF extraction dropping cells
across column breaks is the likelier explanation, and the LaTeX parse is the better instrument.

### 2.6 Verdicts

| claim | verdict at 2026-08-24 |
|---|---|
| (i) value-by-value reproduction, 576/588 | **NOT SCOOPED** |
| (ii) γ_SW undocumented + the prior-propping census | **NOT SCOOPED, REFRAMED** (§2.3) |
| (iii) the size of the misspecification-mitigation trade | **NOT SCOOPED** |
| (iv) composition sensitivity of factorised products | **PARTIALLY SCOOPED** (§2.2) — credited, and the claim narrowed |

---

## 3. The cold read (M5 rec, and the M6 instruction)

Read once end to end as if by an author of the table being measured. The paper was already fair —
a grep for loaded language returned three hits and all three were about *our* mistake — so the
changes are about framing, precision, and making our own withdrawals louder. Ten changes:

| # | where | before → after | why |
|---|---|---|---|
| 1 | **Title** | *"How much of a pulsar timing array noise table is a measurement?"* → *"Which entries in a pulsar timing array noise table are measurements?"* | The first asks how much of your table is worthless; the second asks a per-row question, which is the one the paper actually answers. |
| 2 | §4.1 heading | *"Seven published values cannot be reached"* → *"…lie outside the prior a reproducer would guess"* | Puts the agency on the reproducer, where §2.3 already admits it belongs. |
| 3 | §5 heading | *"How much of the rest of the table is prior?"* → *"What else in the table is bounded by the prior"* | Descriptive rather than rhetorical. |
| 4 | §9 heading | *"What would fix it"* → *"Three changes that would make the table self-contained"* | Names the remedy rather than implying a defect. |
| 5 | §5, MAP-outside paragraph | *"A MAP outside its interval is not a typographical accident"* → *"Both numbers are right, and they describe different features of the same distribution"* | The old form is defensive on the reader's behalf and faintly condescending; the new one just gives the mechanism, and credits the caption that already flags it. |
| 6 | §4.3 census blockquote | scope added inline | The scope limit lived a section away in §4.4. It now rides with the number wherever the number is quoted. |
| 7 | §4.4 opening | *"most of the published γ_SW column carries no information about γ_SW"* → *"most of the γ_SW column is unconstrained under both priors we tried"* | The first is a claim about their column; the second is what we measured. |
| 8 | §7 preamble | added a count | *"Thirteen claims we made earlier are withdrawn, narrowed or reinstated below, and two of them were headline results of ours"* — naming which two. Our retractions were a table; now they are a number a reader meets first. |
| 9 | §4.1 | added *"that the code is public at all is more than most published analyses offer. The gap is not secrecy, it is the absence of a pointer."* | Naming an individual's personal repository in a paper about documentation needs the direction of the point made explicit, or it reads as exposure. |
| 10 | **Abstract** | added *"We withdraw one array-level claim of our own."* | The strongest available statement of the standard being applied inward, in the one place everybody reads. |

**One structural change**, made because MNRAS requires it rather than for tone: a **Conclusions**
section (§10) now exists as the final numbered section, with Data availability renumbered to §11 and
the non-paper sections to §12–§13. Every cross-reference was updated.

---

## 4. The composition-jackknife methods note (M5 rec 4)

[`draft-rnaas-composition-jackknife.md`](draft-rnaas-composition-jackknife.md) — **DRAFT — NOT
SUBMITTED**, placeholder author fields, nothing sent to anyone.

### 4.1 Headline, venue and shape

> **A factorised-likelihood product's credible interval understates its dependence on which pulsars
> are in the set — the tighter of our two 83-pulsar products has a 68% width of 0.149 dex and a
> delete-one composition jackknife of 0.256 dex — so a difference of two such products tested
> against a fixed threshold is not a significance test.**

**Venue: Research Notes of the AAS.** Limits verified live at
<https://journals.aas.org/research-notes/> on **2026-08-24**: *"1,500 words or fewer"*, *"no more
than a single figure or table (but not both)"*, abstract required since 2020-05-01, *"moderated but
not edited"* and not peer reviewed, *"searchable in ADS and fully citable"*. Its stated scope
includes "comments and clarifications" and "null results", which is what this is. **The note proper
is 1,300 words** and spends its one graphic on Table 1, because the ratio of jackknife SE to
credible interval is the whole claim and needs both numbers side by side for both products.

### 4.2 Why it is separate, and how it is positioned

It is the only result in this project that is **not about the MPTA**: it is about an estimator that
pulsar timing arrays use widely, it costs no new compute, and inside the paper it is four paragraphs
of §6.2–§6.3 that a reader interested in the technique would never find. It leads with the Larsen et
al. (2025) credit of §2.2 and states exactly what it adds; the note itself records that the
positioning changed on 2026-08-24 and why, and says plainly that if a referee judges the remainder
too thin, the note should not run. The paper keeps §6.2 and §6.3 — a withdrawal belongs where the
claim was made — and cites the note for the general treatment.

### 4.3 Its own machinery

`scripts/m6_methods_note_numbers.py` re-derives **42 numbers** from committed artifacts (audit table
§4.4); `scripts/m6_methods_note_check.py` checks the drafted text back against them:
**49 checks, 0 failures.** The checker also enforces the venue: it fails if the note proper exceeds
1,500 words, if the note ever contains more than one figure-or-table, if the artifact stops saying
the jackknife exceeds the interval, or if the factorised-likelihood reference reverts to the wrong
author list.

**The checker was falsification-tested rather than assumed live.** Perturbing `0.256` to `0.156` in
a scratch copy of the note produced `49 checks, 1 FAILED`; restoring it returned 0. It had already
earned its keep before that, by catching the growth-curve mode range (§5.2).

### 4.4 The methods-note number audit (42 rows)

Emitted by `scripts/m6_methods_note_numbers.py --markdown`.

| # | claim | value | artifact | field |
|---|---|---|---|---|
| 1 | favoured single-pulsar models: pulsars in the product | 83 | `results/m5/curn_stability.json` | `fl.n` |
| 2 | favoured single-pulsar models: MAP log10 A | -14.439 | `results/m5/curn_stability.json` | `fl.map` |
| 3 | favoured single-pulsar models: 68% interval | [-14.642, -14.348] | `results/m5/curn_stability.json` | `fl.ci68` |
| 4 | favoured single-pulsar models: 68% width (dex) | 0.294 | `results/m5/curn_stability.json` | `fl.ci68_width` |
| 5 | favoured single-pulsar models: composition jackknife SE (dex) | 0.137 | `results/m5/curn_stability.json` | `fl.jackknife_se` |
| 6 | favoured single-pulsar models: SE / width | 0.47 | `results/m5/curn_stability.json` | `fl.jackknife_se / fl.ci68_width` |
| 7 | every pulsar given a free red process: pulsars in the product | 83 | `results/m5/curn_stability.json` | `table.n` |
| 8 | every pulsar given a free red process: MAP log10 A | -14.183 | `results/m5/curn_stability.json` | `table.map` |
| 9 | every pulsar given a free red process: 68% interval | [-14.283, -14.134] | `results/m5/curn_stability.json` | `table.ci68` |
| 10 | every pulsar given a free red process: 68% width (dex) | 0.149 | `results/m5/curn_stability.json` | `table.ci68_width` |
| 11 | every pulsar given a free red process: composition jackknife SE (dex) | 0.256 | `results/m5/curn_stability.json` | `table.jackknife_se` |
| 12 | every pulsar given a free red process: SE / width | 1.72 | `results/m5/curn_stability.json` | `table.jackknife_se / table.ci68_width` |
| 13 | difference of the two products' modes (dex) | 0.257 | `results/m5/seamb_subset_null.json` | `dmap_all` |
| 14 | pulsars gated in both configurations | 83 | `results/m5/seamb_subset_null.json` | `n_common` |
| 15 | delete-1 jackknife SE of that difference (dex) | 0.212 | `results/m5/seamb_subset_null.json` | `jackknife.se` |
| 16 | the difference in units of its own jackknife SE | 1.2 | `results/m5/seamb_subset_null.json` | `dmap_all / jackknife.se` |
| 17 | the pre-registered threshold it was tested against (dex) | 0.21 | `results/m5/seamb_subset_null.json` | `jackknife.f4_threshold` |
| 18 | single pulsar whose removal moves it most | J2129-5721 | `results/m5/seamb_subset_null.json` | `jackknife.most_influential[0]` |
| 19 | the difference with that pulsar removed (dex) | 0.075 | `results/m5/seamb_subset_null.json` | `jackknife.most_influential[0]` |
| 20 | random thinnings drawn | 400 | `results/m5/seamb_subset_null.json` | `null.n` |
| 21 | pulsars per thinning | 52 | `results/m5/seamb_subset_null.json` | `null.size` |
| 22 | standard deviation of the difference over thinnings (dex) | 0.34 | `results/m5/seamb_subset_null.json` | `null.sd` |
| 23 | 95% band of the difference over thinnings | [0.002, 0.407] | `results/m5/seamb_subset_null.json` | `null.ci95` |
| 24 | percentile of our own subset value in that band | 5.5 | `results/m5/seamb_subset_null.json` | `null.percentile_of_ess_value` |
| 25 | the difference on that particular subset (dex) | 0.04 | `results/m5/seamb_subset_null.json` | `dmap_ess` |
| 26 | addition at which the product leaves the prior rail | 58 | `results/m4/fl_growth_fl.json` | `curve[].width, largest single drop` |
| 27 | the pulsar responsible | J1909-3744 | `results/m4/fl_growth_fl.json` | `curve[].added` |
| 28 | 68% width just before that step (dex) | 1.92 | `results/m4/fl_growth_fl.json` | `curve[].width` |
| 29 | 68% width just after (dex) | 0.37 | `results/m4/fl_growth_fl.json` | `curve[].width` |
| 30 | narrowest 68% width before the step (dex) | 1.9 | `results/m4/fl_growth_fl.json` | `curve[:step].width` |
| 31 | widest 68% width in that stretch (dex) | 2.4 | `results/m4/fl_growth_fl.json` | `curve[:step].width` |
| 32 | lowest mode before the step | -17.1 | `results/m4/fl_growth_fl.json` | `curve[:step].map` |
| 33 | highest mode before the step | -14.5 | `results/m4/fl_growth_fl.json` | `curve[:step].map` |
| 34 | mode swing over the final ten additions (dex) | 0.03 | `results/m4/fl_growth_fl.json` | `map_swing_last10` |
| 35 | pulsars where the two configurations differ | 70 | `results/m5/curn_stability.json` | `seam_b_paired.n_test` |
| 36 | of those, moving DOWN | 49 | `results/m5/curn_stability.json` | `seam_b_paired.n_down` |
| 37 | median per-pulsar shift (dex) | -0.073 | `results/m5/curn_stability.json` | `seam_b_paired.median` |
| 38 | sign-test p | 0.0011 | `results/m5/curn_stability.json` | `seam_b_paired.sign_test_p` |
| 39 | Wilcoxon signed-rank p | 5.828541412592046e-06 | `results/m5/curn_stability.json` | `seam_b_paired.wilcoxon_p` |
| 40 | control pulsars (same model twice) | 12 | `results/m5/curn_stability.json` | `seam_b_paired.n_control` |
| 41 | control median shift (dex) | 0.0004 | `results/m5/curn_stability.json` | `seam_b_paired.control_median` |
| 42 | Wilcoxon p on the control set | 0.68 | `results/m5/curn_stability.json` | `seam_b_paired.control_wilcoxon_p` |

---

## 5. Final verification (M6 instruction 5)

### 5.1 The three verifiers, all green

| document | numbers re-derived | text-vs-artifact checks | failures |
|---|---|---|---|
| [`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md) | **137** (`m5_paper_numbers.py`) | **119** (`m5_paper_check.py`) | **0** |
| [`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md) | **29** audited, 1 CORRECTED (`m4_note_numbers.py`) | **22** (`m4_note_check.py`) | **0** |
| [`draft-rnaas-composition-jackknife.md`](draft-rnaas-composition-jackknife.md) | **42** (`m6_methods_note_numbers.py`) | **49** (`m6_methods_note_check.py`) | **0** |

The one CORRECTED row in the note's audit is the same M4 pre-registration row it has always been
(−3.14 → −3.21) and is reported as a correction by design, not as a failure.

### 5.2 Four errors in our own drafts, all found by machine

M5 recorded that its six checker mismatches were "all checker-side rather than wrong numbers in the
draft", and observed that a checker which has never failed has not been tested. M6's pass failed on
real content four times:

1. **A wrong author list on a reference we relied on.** The draft cited the factorised likelihood as
   *"Taylor, S. R., van Haasteren, R. & Wang, Y. 2022, PhRvD 105, 084049"*. That bibcode is
   **Taylor, Simon, Schult, Pol & Lamb (2022)** — same volume, same page, different authors — and it
   is the reference the MPTA paper itself gives. Caught by checking our reference list against the
   release's own `ref.bib` rather than against our memory of it. Corrected in the paper, in the
   methods note, and recorded as row 12 of the paper's corrections table.
2. **Two growth-curve range numbers did not survive re-derivation.** The paper said the 68% interval
   "stays 1.9–2.2 dex wide … while the mode lurches between −16.7 and −14.5" over the first 57
   additions. Re-derived from `results/m4/fl_growth_fl.json` over exactly that range the answers are
   **1.9–2.4 dex** and **−17.1 to −14.5**. Both corrected in both documents. This is the error the
   new checker caught first, before it had checked anything else.
3. **The paper's number audit did not cover the paper.** A token-level sweep of every numeric string
   in the body against `results/m5/paper_numbers.json` found **71 uncovered tokens**, of which **32
   were real content numbers** — the absolute-gate agreement rate, the census class widths, the two
   printed γ_SW intervals a reader cannot flag, the control bars, the withdrawn width blow-up, the
   reinstated J1600−3053 shift, and the registered gate constants among them. All 32 were **added to
   the audit rather than excused**, taking it from 105 rows to 137 and the checker from 92 to 119.
   What the sweep now leaves uncovered is software version strings, section numbers, the OzGrav
   grant number, and the two prior ranges quoted from code in §4.1 — each carrying its source in the
   text.
4. **A hard-coded fallback in the audit script itself.** The first version of the J1525−5545
   minimum-ESS row read `... else 86` — i.e. it would have printed the right answer even if the
   lookup failed, which is not an audit. Replaced with a direct read of
   `results/m3/J1525-5545_swwide_s1.summary.json` → `chain.ess_min`.

### 5.3 Traceability, stated exactly

**Every number in all three documents traces to a committed artifact**, with these declared
exceptions, each of which carries its source in the text where it appears: package version strings
(read from the environment's `dist-info`); section, table and figure numbers; bibliographic data in
the reference lists (each verified against Crossref or the publisher, 2026-08-24); the OzGrav grant
number inside SARAO's own required wording; and the prior ranges quoted from `MattTMiles/MPTAGW` and
from our own model module in §4.1–§4.2, which name the file and the retrieval date. Three of the
audit's 137 rows are registrations rather than measurements — the gate's iteration counts and the
acceptance floor — and they name the pre-registration document as their artifact.

### 5.4 The paper number audit (137 rows)

| # | claim | value | artifact | field |
|---|---|---|---|---|
| 1 | pulsars in the release | 83 | `results/m4/note_numbers.json` | `n_noise_rows` |
| 2 | tabulated parameter values with a printed interval | 588 | `results/m4/note_numbers.json` | `n_values` |
| 3 | sub-banded ToAs in the release (counted from the 83 .tim) | 245907 | `data/partim/*.tim` | `line count` |
| 4 | model inventory: chromatic Gaussian events | 15 | `results/m3/published_table.json` | `model.bump` |
| 5 | model inventory: annual chromatic variations | 8 | `results/m3/published_table.json` | `model.annual` |
| 6 | model inventory: free-index chromatic GPs | 13 | `results/m3/published_table.json` | `model.chrom_free` |
| 7 | model inventory: fixed-index chromatic GPs | 10 | `results/m3/published_table.json` | `model.chrom_fixed` |
| 8 | model inventory: DM GPs | 49 | `results/m3/published_table.json` | `model.dm` |
| 9 | model inventory: solar-wind GPs | 26 | `results/m3/published_table.json` | `model.sw_full` |
| 10 | model inventory: free achromatic red processes | 12 | `results/m3/published_table.json` | `model.red` |
| 11 | model inventory: EQUAD terms | 20 | `results/m3/published_table.json` | `model.equad` |
| 12 | model inventory: ECORR terms | 29 | `results/m3/published_table.json` | `model.ecorr` |
| 13 | pulsars whose release ships as many ToAs as its ephemeris was fitted to | 63 | `results/m3/a1_summary.json` | `records[].ntoa == ntoa_pub` |
| 14 | pulsars that ship fewer ToAs than their ephemeris fitted | 20 | `results/m3/a1_summary.json` | `records[]` |
| 15 | median |wRMS - TRES| / TRES over the complete set (%) | 0.015 | `results/m3/a1_summary.json` | `records[].frac` |
| 16 | pulsars clearing the registered (relative) gate | 83 | `results/m4/agreement_both_gates.json` | `relative.n` |
| 17 | pulsars clearing the absolute (M1-M3) gate | 76 | `results/m4/agreement_both_gates.json` | `absolute.n` |
| 18 | parameters agreeing under the registered A2 rule | 576 | `results/m4/agreement_both_gates.json` | `relative.params_agree` |
| 19 | parameters compared | 588 | `results/m4/agreement_both_gates.json` | `relative.params_total` |
| 20 | agreement rate (%) | 98.0 | `results/m4/agreement_both_gates.json` | `relative.pct` |
| 21 | pulsars agreeing on every tabulated value | 73 | `results/m4/agreement_both_gates.json` | `relative.n_full` |
| 22 | parameters missing | 12 | `results/m4/agreement_both_gates.json` | `derived` |
| 23 | misses that are solar-wind parameters | 10 | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 24 | misses that are the Gaussian-event width | 2 | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 25 | the miss keys themselves | {"bump_sigma": 2, "sw_gamma": 8, "sw_log10_A": 2} | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 26 | median dlnL(ours - published) | 0.7 | `results/m4/agreement_both_gates.json` | `dlnl.median` |
| 27 | pulsars with dlnL > 0 | 79 | `results/m4/agreement_both_gates.json` | `dlnl.n_pos` |
| 28 | pulsars with dlnL < 0 | 4 | `results/m4/agreement_both_gates.json` | `dlnl.n_neg` |
| 29 | most negative dlnL | -0.67 | `results/m4/agreement_both_gates.json` | `dlnl.min` |
| 30 | lowest acceptance over gated runs | 0.158 | `results/m4/agreement_both_gates.json` | `relative.acc_min` |
| 31 | highest acceptance over gated runs | 0.527 | `results/m4/agreement_both_gates.json` | `relative.acc_max` |
| 32 | pulsars whose favoured model samples gamma_SW | 26 | `results/m4/note_numbers.json` | `n_swfull` |
| 33 | published gamma_SW values that are negative | 7 | `results/m4/note_numbers.json` | `n_sw_gamma_negative` |
| 34 | further rows whose 68% interval crosses zero | 12 | `results/m4/note_numbers.json` | `n_sw_gamma_ci_crossing` |
| 35 | rows outside or straddling gamma in [0,7] | 19 | `results/m4/note_numbers.json` | `n_sw_affected` |
| 36 | published values below the e_e U(-2,1) floor | 2 | `results/m4/note_numbers.json` | `n_sw_below_ee_default` |
| 37 | lowest printed gamma_SW 68% lower edge | -3.21 | `results/m4/note_numbers.json` | `sw_gamma_lowest_ci_edge` |
| 38 | the pulsar it belongs to | J1811-2405 | `results/m4/note_numbers.json` | `sw_gamma_lowest_ci_edge_psr` |
| 39 | enterprise_extensions solar_wind_block gamma default | [-2.0, 1.0] | `results/m4/note_numbers.json` | `ee_sw_gamma_default` |
| 40 | SW_Full pulsars with both priors gated (M4 variant) | 26 | `results/m4/swwide.json` | `compared` |
| 41 | campaign misses covered by the variant | 10 | `results/m4/swwide.json` | `n_miss_registered` |
| 42 | misses remaining under U(-4,4) | 0 | `results/m4/swwide.json` | `n_miss_variant` |
| 43 | misses created by the wide prior | 0 | `results/m4/swwide.json` | `created` |
| 44 | SW_Full pulsars in the census | 26 | `results/m5/sw_census.json` | `n_compared` |
| 45 | census class MEASURED | 5 | `results/m5/sw_census.json` | `counts.MEASURED` |
| 46 | census class PRIOR-PROPPED | 5 | `results/m5/sw_census.json` | `counts.PRIOR-PROPPED` |
| 47 | census class UNCONSTRAINED-BOTH | 15 | `results/m5/sw_census.json` | `counts.UNCONSTRAINED-BOTH` |
| 48 | census class OTHER | 1 | `results/m5/sw_census.json` | `counts.OTHER` |
| 49 | rows that are NOT a measurement of gamma_SW | 20 | `results/m5/sw_census.json` | `primary` |
| 50 | how the primary number must be quoted (S4 rule) | 16-20 | `results/m5/sw_census.json` | `sensitivity.quote` |
| 51 | MEASURED count across the sensitivity grid | [4, 7] | `results/m5/sw_census.json` | `sensitivity.measured_range` |
| 52 | re-specified control set size | 5 | `results/m5/sw_census.json` | `control.n` |
| 53 | worst |d median gamma_SW| over the control set | 0.135 | `results/m5/sw_census.json` | `control.worst_d_gamma` |
| 54 | S2 control verdict | PASS | `results/m5/sw_census.json` | `control.verdict` |
| 55 | rows the printed table alone already flags | 19 | `results/m5/sw_census.json` | `table_only.counts` |
| 56 | rows the printed table alone CANNOT flag | ["J1614-2230", "J1744-1134"] | `results/m5/sw_census.json` | `table_only.divergent` |
| 57 | the prior-propped pulsars | ["J1327-0755", "J1614-2230", "J1744-1134", "J1811-2405", ... | `results/m5/sw_census.json` | `rows[].klass` |
| 58 | A_13/3 rows whose 68% reaches below -16.5 | 66 | `results/m4/note_numbers.json` | `n_a13_prior_limited` |
| 59 | A_13/3 rows constrained better than 0.7 dex | 6 | `results/m4/note_numbers.json` | `n_a13_better_than_0p7` |
| 60 | median 68% width of the prior-bounded A_13/3 rows | 3.01 | `results/m4/note_numbers.json` | `a13_median_width_prior_limited` |
| 61 | values whose MAP lies outside their own 68% interval | 26 | `results/m4/note_numbers.json` | `n_map_outside` |
| 62 | pulsars affected | 22 | `results/m4/note_numbers.json` | `n_pulsars_map_outside` |
| 63 | median decorrelating reference frequency (MHz) | 857 | `results/m3/seam_a.json` | `nu_pivot_MHz (free-beta rows)` |
| 64 | median log10A_Chrom 68% width at 1400 MHz (dex) | 0.46 | `results/m3/seam_a.json` | `width_A_1400` |
| 65 | the same width at the pivot frequency (dex) | 0.19 | `results/m3/seam_a.json` | `width_A_pivot` |
| 66 | free-beta chromatic pulsars that are prior-driven | 2 | `results/m3/seam_a.json` | `prior_driven` |
| 67 | free-beta chromatic pulsars | 13 | `results/m3/seam_a.json` | `chrom == free` |
| 68 | pulsars in the fl factorised-likelihood product | 83 | `results/m5/curn_stability.json` | `fl.n` |
| 69 | fl product MAP log10 A_CURN | -14.439 | `results/m5/curn_stability.json` | `fl.map` |
| 70 | fl product 68% interval | [-14.642, -14.348] | `results/m5/curn_stability.json` | `fl.ci68` |
| 71 | fl product 68% width | 0.294 | `results/m5/curn_stability.json` | `fl.ci68_width` |
| 72 | fl product jackknife SE over pulsar composition | 0.137 | `results/m5/curn_stability.json` | `fl.jackknife_se` |
| 73 | pulsars in the table-configuration product | 83 | `results/m5/curn_stability.json` | `table.n` |
| 74 | table product MAP | -14.183 | `results/m5/curn_stability.json` | `table.map` |
| 75 | table product 68% interval | [-14.283, -14.134] | `results/m5/curn_stability.json` | `table.ci68` |
| 76 | table product 68% width | 0.149 | `results/m5/curn_stability.json` | `table.ci68_width` |
| 77 | table product jackknife SE over pulsar composition | 0.256 | `results/m5/curn_stability.json` | `table.jackknife_se` |
| 78 | pulsars in the paired seam-(b) test | 70 | `results/m5/curn_stability.json` | `seam_b_paired.n_test` |
| 79 | of those, moving DOWN | 49 | `results/m5/curn_stability.json` | `seam_b_paired.n_down` |
| 80 | median per-pulsar shift (dex) | -0.0728 | `results/m5/curn_stability.json` | `seam_b_paired.median` |
| 81 | sign-test p | 0.0011 | `results/m5/curn_stability.json` | `seam_b_paired.sign_test_p` |
| 82 | Wilcoxon signed-rank p | 5.8e-06 | `results/m5/curn_stability.json` | `seam_b_paired.wilcoxon_p` |
| 83 | control pulsars (same model twice) | 12 | `results/m5/curn_stability.json` | `seam_b_paired.n_control` |
| 84 | Wilcoxon p on the control set | 0.677 | `results/m5/curn_stability.json` | `seam_b_paired.control_wilcoxon_p` |
| 85 | product-level shift (table - fl) on the common set | 0.257 | `results/m5/seamb_subset_null.json` | `dmap_all` |
| 86 | pulsars in that comparison | 83 | `results/m5/seamb_subset_null.json` | `n_common` |
| 87 | delete-1 jackknife SE of that shift | 0.212 | `results/m5/seamb_subset_null.json` | `jackknife.se` |
| 88 | the shift in units of its own jackknife SE | 1.2 | `results/m5/seamb_subset_null.json` | `derived` |
| 89 | the registered F4 magnitude threshold | 0.21 | `results/m5/seamb_subset_null.json` | `jackknife.f4_threshold` |
| 90 | single pulsar whose removal moves it most | ["J2129-5721", 0.075] | `results/m5/seamb_subset_null.json` | `jackknife.most_influential` |
| 91 | addition at which the FL product leaves the prior rail | 58 | `results/m4/fl_growth_fl.json` | `curve` |
| 92 | the pulsar responsible | J1909-3744 | `results/m4/fl_growth_fl.json` | `curve` |
| 93 | 68% width just before that step (dex) | 1.92 | `results/m4/fl_growth_fl.json` | `curve` |
| 94 | 68% width just after (dex) | 0.37 | `results/m4/fl_growth_fl.json` | `curve` |
| 95 | MAP swing over the final ten additions (dex) | 0.0303333333333331 | `results/m4/fl_growth_fl.json` | `map_swing_last10` |
| 96 | the registered floor | 100 | `results/m5/ess_floor.json` | `floor` |
| 97 | noise runs gated / clearing the floor | [83, 65] | `results/m5/ess_floor.json` | `coverage.noise` |
| 98 | table runs gated / clearing the floor | [83, 63] | `results/m5/ess_floor.json` | `coverage.table` |
| 99 | fl runs gated / clearing the floor | [83, 56] | `results/m5/ess_floor.json` | `coverage.fl` |
| 100 | swwide runs gated / clearing the floor | [26, 18] | `results/m5/ess_floor.json` | `coverage.swwide` |
| 101 | agreement rate over runs the floor ADMITS | 97.74 | `results/m5/ess_floor.json` | `e5_falsifier.admitted.pct` |
| 102 | agreement rate over runs the floor REJECTS | 98.42 | `results/m5/ess_floor.json` | `e5_falsifier.rejected.pct` |
| 103 | E5 falsifier verdict | NEGATIVE | `results/m5/ess_floor.json` | `e5_falsifier.verdict` |
| 104 | core-hours recorded on the final launch of each run | 192.4 | `results/m3/*.summary.json` | `elapsed_min` |
| 105 | runs with a recorded final launch | 277 | `results/m3/*.summary.json` | `elapsed_min` |
| 106 | agreement rate under the absolute gate (%) | 97.9 | `results/m4/agreement_both_gates.json` | `absolute.pct` |
| 107 | census class MEASURED: median log10A_SW 68% width, U(0,7) -> U(-4,4) | [0.29, 0.3] | `results/m5/sw_census.json` | `rows[klass==MEASURED].wA_*` |
| 108 | census class PRIOR-PROPPED: median log10A_SW 68% width, U(0,7) -> U(-4,4) | [0.47, 2.14] | `results/m5/sw_census.json` | `rows[klass==PRIOR-PROPPED].wA_*` |
| 109 | census class UNCONSTRAINED-BOTH: median log10A_SW 68% width, U(0,7) -> U(-4,4) | [2.75, 3.04] | `results/m5/sw_census.json` | `rows[klass==UNCONSTRAINED-BOTH].wA_*` |
| 110 | census class OTHER: median log10A_SW 68% width, U(0,7) -> U(-4,4) | [2.38, 2.12] | `results/m5/sw_census.json` | `rows[klass==OTHER].wA_*` |
| 111 | J1744-1134 published gamma_SW | 0.91 | `results/m5/sw_census.json` | `rows[J1744-1134].pub_gamma` |
| 112 | J1744-1134 gamma_SW 68% width, U(0,7) -> U(-4,4) | [1.52, 4.42] | `results/m5/sw_census.json` | `rows[J1744-1134].w_narrow/w_wide` |
| 113 | J1614-2230 printed gamma_SW 68% width | 1.73 | `results/m5/sw_census.json` | `rows[J1614-2230].pub_w68` |
| 114 | J1744-1134 printed gamma_SW 68% width | 1.47 | `results/m5/sw_census.json` | `rows[J1744-1134].pub_w68` |
| 115 | J1525-5545 printed gamma_SW 68% width | 3.44 | `results/m5/sw_census.json` | `rows[J1525-5545].pub_w68` |
| 116 | worst |d median log10A_SW| over the control set | 0.035 | `results/m5/sw_census.json` | `control.worst_d_logA` |
| 117 | J1525-5545 minimum ESS on its swwide run | 86 | `results/m3/J1525-5545_swwide_s1.summary.json` | `chain.ess_min` |
| 118 | 68% width range over the additions before the step (dex) | [1.9, 2.4] | `results/m4/fl_growth_fl.json` | `curve[:step].width` |
| 119 | mode range over the additions before the step | [-17.1, -14.5] | `results/m4/fl_growth_fl.json` | `curve[:step].map` |
| 120 | standard deviation of the shift over random thinnings (dex) | 0.34 | `results/m5/seamb_subset_null.json` | `null.sd` |
| 121 | the shift on the ESS-floored subset (dex) | 0.04 | `results/m5/seamb_subset_null.json` | `dmap_ess` |
| 122 | per-pulsar control bar, 12 controls (dex) | 0.463 | `results/m5/seamb_subset_null.json` | `control_bar.all.bar` |
| 123 | per-pulsar control bar, 6 ESS-floored controls (dex) | 0.144 | `results/m5/seamb_subset_null.json` | `control_bar.ess.bar` |
| 124 | M3's 32-pulsar fl product 68% width (the withdrawn width headline) (dex) | 2.54 | `results/m4/fl_both_gates.json` | `m3_common32.fl.ci68` |
| 125 | the same width at full coverage (dex) | 0.29 | `results/m5/curn_stability.json` | `fl.ci68_width` |
| 126 | J1600-3053 seam-b shift, whites held fixed (dex) | -1.22 | `results/m3/seam_b.json` | `rows[J1600-3053].delta` |
| 127 | precision factor gained by re-quoting at the pivot | 2.4 | `results/m3/seam_a.json` | `width_A_1400 / width_A_pivot` |
| 128 | parameters agreeing on the pulsars admitted only by the relaxation | 61 | `results/m4/agreement_both_gates.json` | `r5.only_agree` |
| 129 | parameters compared on those pulsars | 62 | `results/m4/agreement_both_gates.json` | `r5.only_total` |
| 130 | additions before the one-pulsar step | 57 | `results/m4/fl_growth_fl.json` | `curve[].n at the step, minus one` |
| 131 | median shift over the control pulsars (dex) | 0.0004 | `results/m5/curn_stability.json` | `seam_b_paired.control_median` |
| 132 | the published gamma_SW values below the enterprise_extensions floor of the day | [-2.32, -2.21] | `results/m4/note_numbers.json` | `sw_negative, ee_sw_gamma_default` |
| 133 | M3's pre-registered lowest printed gamma_SW edge, since corrected | -3.14 | `M3-noise-criticism.md` | `pre-registration 1.3 (superseded; see row 7)` |
| 134 | M4's product-level shift as first reported (82 psr) | 0.259 | `M4-finish-the-array.md` | `section B-2 (withdrawn; see row 9)` |
| 135 | registered minimum post-burn iterations | 100000 | `M3-noise-criticism.md` | `section 1 (A1)` |
| 136 | the same for the fixed-white variants | 50000 | `M3-noise-criticism.md` | `section 1 (A1)` |
| 137 | registered acceptance floor | 0.05 | `M2-converge-scale.md` | `acceptance floor` |

---

## 6. State of readiness

**Nothing in this section is a plan. It is a list of what is left, per document, and who must do it.**

### 6.1 [`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md) — *Which entries in a pulsar timing array noise table are measurements?*

| item | who | blocking? |
|---|---|---|
| **The archive DOI** — deposit priors, models, harness, per-run summaries, the parsed table, the CURN marginals and the pre-registrations; paste it over the placeholder in §11 | **Matthew** | **YES — the only blocker** |
| Author, affiliation, ORCID | Matthew | no |
| Venue choice + 1–6 MNRAS keywords | Matthew | no |
| If A&A is chosen: verify its abstract limit (its site refused automated access 2026-08-24) | Matthew | no |
| Whether to send the collaboration paragraph first | Matthew | no |
| Post-publication: send bibliographic details to SARAO's publications address | Matthew | no |
| **Analysis work owed** | — | **NONE** |

Shape: abstract **240 words** (MNRAS limit 250, verified live), ten numbered sections plus
Conclusions, Acknowledgements, Data Availability, references, two appendices, three tables, four
figures. All figures exist in `figures/`. 137 numbers audited, 119 checks at 0 failures.

### 6.2 [`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md) — the table audit

| item | who | blocking? |
|---|---|---|
| Author, affiliation, ORCID; an AAS account | **Matthew** | **YES** |
| The archive DOI, **only if** the note is to point at the audit products | Matthew | no |
| Whether to send the collaboration paragraph, and in what order | Matthew | no |
| **Analysis work owed** | — | **NONE** |

**One thing changed in it, and it matters to Matthew's decision.** Claim (a) now records that the
γ_SW range is readable in the first author's public repository, and **the drafted collaboration
paragraph was rewritten to say so** — sending a note that says "you never said which prior" when the
number is in your own public code would have been a bad look, and it is now the letter's second
paragraph instead of a landmine. **Watch the word budget: the note proper is now 1,451 words against
RNAAS's 1,500** (it was 1,391). There is room for about forty more words and no more; the checker
enforces the stated count but not the limit, so any further addition needs a deletion.

### 6.3 [`draft-rnaas-composition-jackknife.md`](draft-rnaas-composition-jackknife.md) — the methods note

| item | who | blocking? |
|---|---|---|
| Author, affiliation, ORCID; an AAS account | **Matthew** | **YES** |
| A judgement call: **is what remains after the Larsen et al. credit enough for a note?** The note argues yes and states the case for no | **Matthew** | **YES, in the sense that it is a go/no-go** |
| The archive DOI, only if the note is to point at the per-pulsar marginals | Matthew | no |
| Submission order relative to the other two | Matthew | no |
| **Analysis work owed** | — | **NONE** |

1,300 words against a live-verified 1,500 limit, one table, 42 numbers audited, 49 checks at 0
failures.

### 6.4 The one-line answer

> **Only the DOI blocks the paper.** The two research notes need an AAS account and author details,
> which are the same class of human step, and the methods note additionally needs a go/no-go on its
> narrowed novelty. No measurement, no chain, no check and no citation is outstanding in any of the
> three.

---

## 7. Economics

M6 ran **no chains**. Everything in it is post-processing, document work and one external sweep;
the campaign total is unchanged at **≥ 192.4 core-hours over 277 runs**. The verifiers together run
in a few seconds on one core. The expensive thing in this project has always been the chains, and
the cheapest thing in it — a token-level sweep of the paper's own numbers — is what found 32
untraced values and a wrong author list.

---

## 8. What M6 did not do

No submissions, no accounts, no outward sends, no emails, no commits, no pushes, no new chains. All
three documents carry **DRAFT — NOT SUBMITTED**; the collaboration paragraph is still **DRAFTED —
NOT SENT** and still has no addressee. The Zenodo DOI was not minted — it is Matthew's step and it
is deliberately the last one. The `enterprise` 3.5.0 upstream bug report M2 identified is still
unfiled and still his call.
