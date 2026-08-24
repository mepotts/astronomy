# pta-mpta — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-24** — **M6 complete — THE CLOSING MILESTONE**
  ([`M6-close-the-paper.md`](M6-close-the-paper.md)). **All three documents are submission-ready and
  the only blocker left is the DOI.** No chains were run: M6 is citations, one external sweep,
  a cold read, a new note, and verification.
  **THE PRIOR-ART RE-SWEEP CHANGED THE POSITIONING ON TWO OF FOUR CLAIMS, AND BOTH ARE DECLARED.**
  (1) **Claim (iv) is PARTIALLY SCOOPED.** **Larsen et al. 2025 (MNRAS 542, 3028, arXiv:2503.20949)
  §4.1.4 and Fig. 8 already publish a drop-one-pulsar analysis of a DIFFERENCE of two
  factorised-likelihood products**, concluding verbatim that "the overall discrepancy is sensitive to
  systematic errors in the individual pulsars"; Reardon et al. 2023 already name the three pulsars
  that "dominate the factorized likelihood". **The paper's §6.2 and the new methods note both now
  lead with that credit**, and the paper's corrections table gains row 13. What survives as new is
  narrower and is stated as such: the jackknife measured on the SAME AXIS as the product's own
  credible interval (0.256 vs 0.149 dex), the one-pulsar transition, and the threshold rule.
  **Larsen does not cite the MPTA release, so it is in no citing-works list — a citation-graph sweep
  is structurally blind to parallel work that does not cite you**, and that sentence is now in the
  paper's threats section. INSPIRE carries **76** citing works against OpenAlex's 44; enumerating
  all 76 found nothing else. NASA ADS refused automated access again.
  (2) **Claim (ii) is REFRAMED: the missing prior is public, as uncited code.** Verified in-session,
  not taken on trust: **`github.com/MattTMiles/MPTAGW`** (the first author's repo — no README, no
  licence, no tag, no DOI, cited by no MPTA paper) sets **`gamma_sw = parameter.Uniform(-4, 4)`** at
  six places, plus `log10_A_sw = Uniform(-10, 1)`. **"Undocumented" survives; "unreachable" does
  not**, and every such phrasing was fixed. **Our blind registered variant chose U(−4,4) — their
  range exactly — and our declared log₁₀A_SW prior U(−10,1) is identical too**, which STRENGTHENS the
  diagnosis that the twelve disagreements are a prior mismatch and nothing else. Also folded in
  against ourselves: γ∈[0,7] is the convention for DM/red indices, not the solar wind — the one
  printed γ_SW prior in the literature is Susarla et al. 2024's U(−6,5). No erratum, no second
  release, no prior file, `enterprise_extensions` unchanged since Sept 2025; and at the commit
  contemporaneous with the paper the default was U(−2,1), which the published values straddle — so
  the collaboration demonstrably did not use the library default of the day.
  **CITATIONS AND ACKNOWLEDGEMENTS FILLED — the draft's last UNSOURCED slots are gone.** Every
  package cited **in the form its own authors ask for** (seven traps recorded: `enterprise` wants a
  Zenodo record not its ASCL entry; `enterprise_extensions` wants **no DOI**; PINT wants **two**
  papers and its own `citation.cff` under-cites; tempo2 wants papers I and II only — **and we never
  ran tempo2**; `parallel-bilby` is Smith, Ashton, **Vajpeyi** & Talbot; `enterprise_warp` has no
  citation request at all), with **exact versions inline** in §2.2. **The facility policy was read,
  not assumed, and it added a requirement nobody had listed: PTUSE demands a second acknowledgement
  paragraph "in addition to" SARAO's** — both are now quoted verbatim, along with Data Central's
  sentence. **M1's "no license stated" is CORRECTED: the release is CC BY 4.0** in its DataCite
  metadata, so the dataset is now cited in its own right. Two verification traps recorded: a search
  summary gave SARAO's department name wrongly, and a fetch of the paywalled OUP page **fabricated an
  entire Data Availability section**.
  **THE COLD READ MADE TEN CHANGES**, including the title (*"How much of a PTA noise table is a
  measurement?"* → *"Which entries in a PTA noise table are measurements?"*), three section headings,
  the MAP-outside paragraph (from defensive to mechanistic), scope moved inline to ride with the
  census number, and — the one that matters most — **"We withdraw one array-level claim of our own"
  now appears in the abstract**. Abstract trimmed **333 → 240 words** (MNRAS's 250 verified live;
  A&A's site refused access, recorded). A **Conclusions** section was added because MNRAS requires
  one as the final numbered section.
  **THE METHODS NOTE IS DRAFTED — NOT SUBMITTED**
  ([`draft-rnaas-composition-jackknife.md`](draft-rnaas-composition-jackknife.md)), RNAAS, **1,300
  words** against limits verified live today, one table, its own numbers script and its own checker
  (**42 numbers, 49 checks, 0 failures**, and falsification-tested). Headline: *a factorised-likelihood
  product's credible interval understates its dependence on which pulsars are in the set, so a
  difference of two such products against a fixed threshold is not a significance test* — with our
  own withdrawn B-2 claim as the worked example.
  **FINAL VERIFICATION: paper 137 numbers / 119 checks / 0 failures; table-audit note 29 / 22 / 0;
  methods note 42 / 49 / 0.** **The pass found four real errors in our own drafts:** the
  factorised-likelihood reference had **the wrong author list** (we had "Taylor, van Haasteren &
  Wang"; it is Taylor, Simon, Schult, Pol & Lamb — caught against the release's own `ref.bib`); two
  growth-curve range numbers did not survive re-derivation (1.9–2.2 → **1.9–2.4** dex, −16.7 →
  **−17.1**); **the paper's own audit did not cover the paper** — a token-level sweep found 32
  content numbers untraced, and all 32 were added rather than excused (105 → 137 rows, 92 → 119
  checks); and the audit script itself had a hard-coded fallback, now a real artifact read.
  **READINESS: only the DOI blocks the paper.** The two RNAAS notes need an AAS account and author
  details; the methods note additionally needs Matthew's go/no-go on its narrowed novelty. **No
  measurement, chain, check or citation is outstanding in any of the three.** ⚠ The table-audit note
  is now **1,451 of 1,500 words** (was 1,391) — about forty words of headroom left. The drafted
  collaboration paragraph was **rewritten** to say we later found U(−4,4) in their own repo, because
  sending "you never said which prior" would have been wrong. Campaign total unchanged at ≥192.4
  core-hours over 277 runs. No commits, no accounts, no submissions, nothing sent.

- **2026-08-24** — **M5 complete**
  ([`M5-ess-floor-sw-census-and-the-paper.md`](M5-ess-floor-sw-census-and-the-paper.md)).
  **THE CAMPAIGN IS FINISHED AND SAYS SO ON DISK: 83/83 `noise`, 83/83 `table`, 83/83 `fl`,
  26/26 `swwide`** — the tail was two runs and both were the same pulsar, J1525-5545 (the array's
  slowest model, 300–430 ms per likelihood evaluation against an array median of 68 ms). A
  **completion sentinel** now exists (`results/m4/CAMPAIGN_COMPLETE.json`, plus a per-round
  heartbeat in `CAMPAIGN_STATE.json`): M4's supervisor expired silently at `MAX_ROUNDS` with work
  outstanding and nothing on disk distinguished that from success — **absence of the COMPLETE file
  now means unfinished, and a stale heartbeat means the supervisor is dead.**
  `scripts/m5_supervise.sh` also closes the double-write hole M4's guard left open: it checks for
  live `m3_run.py` workers **by tag**, not only for a live pool driver, and it declined to relaunch
  on its very first round because orphaned samplers were on the process table with no driver — the
  exact state a session disruption produces. **One correction to M4's own STATUS line, declared
  rather than retro-edited:** it says the γ_SW variant compared "24 of 26" and that "5 of 24" rows
  widen; M4's document §4.1 and its artifact `results/m4/swwide.json` both say **25**, and they are
  right. At full coverage it is 5 of 26.
  **ESS FLOOR REGISTERED AND APPLIED (M4's R4 successor): ESS_min ≥ 100**, derived before use from
  the Monte-Carlo error of a 68% interval edge (1.51/√N ≤ 15% of the half-width), cross-checked
  against M4's measured medians (347 absolute-gated / 105 relative-only, both re-derived
  digit-identically). **65 of 83 `noise`, 63 of 83 `table`, 56 of 83 `fl` and 18 of 26 `swwide` runs
  clear it. Its registered falsifier came back NEGATIVE and is reported as one: the runs the floor
  REJECTS agree with the published table slightly BETTER (98.4%) than the ones it ADMITS (97.7%)**,
  so ESS_min is not diagnostic of fidelity to the published table here — the floor is kept only as a
  bound on our own Monte-Carlo error, and that is the only claim made for it.
  **ONE M4 HEADLINE MOVES AND IS WITHDRAWN.** M4's B-2 number — the seam-(b) product-level shift of
  **+0.259 dex**, declared "significant" against a pre-registered 0.21 dex threshold — reads +0.040
  dex on the ESS-floored subset. The declared post-hoc diagnosis is bigger than the floor: a
  **delete-1 jackknife over the 83 pulsars gated in both configurations gives +0.257 ± 0.212 dex —
  1.2σ, and the threshold rule never had an uncertainty attached**; removing one pulsar
  (J2129-5721) takes it to +0.075, and random equal-sized thinnings give a 0.34 dex spread.
  **The product-level magnitude is withdrawn.** What replaces it is
  stronger and was already in the data: the **paired per-pulsar** form of the same question —
  **49 of 70 pulsars move DOWN, sign test p = 0.0011, Wilcoxon p = 5.8 × 10⁻⁶, against a 12-pulsar
  control consistent with zero (p = 0.68)**. Same root cause behind two more rows: the `table` CURN
  product's **composition jackknife (0.256 dex) exceeds its own 68% width (0.149 dex)**, and the F5
  one-pulsar step survives as structure but not as an identity. **A factorised product's credible
  interval understates how much it depends on which pulsars are in it** — a methods result in its own
  right.
  **SOLAR-WIND CONTROL RE-SPECIFIED, AND IT PASSES: M4's V4 count is REINSTATED.** Defining
  "measured" by posterior/prior width instead of the published value's sign gives five control
  pulsars; over them the wider prior moves γ_SW by at most **0.135** and log₁₀A_SW by 0.035 (yardstick
  0.19) and breaks nothing — so **γ_SW ~ U(−4,4) resolving 10 of 10 solar-wind misses and creating
  none no longer carries a VOID, now over all 26.** **THE PRIOR-PROPPING CENSUS, the publishable
  number: of the 26 published γ_SW rows, only FIVE are measurements of γ_SW** — 5 more have an
  apparent constraint that is the prior edge (their log₁₀A_SW widths go 0.47 → 2.14 dex) and 15 were
  never constrained under either prior. **20 of 26 are not measurements (quoted as a range 16–20 per
  the registered sensitivity rule; the measured count is 4–7 across the whole grid).**
  **A reader can flag 18 of the 20 from the printed table alone — but not J1614-2230 and
  J1744-1134**, which print narrow intervals around *positive* values and are prior-propped, which is
  also exactly why M4's sign-based control failed.
  **THE PAPER IS DRAFTED — NOT SUBMITTED**
  ([`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md)), A&A/MNRAS
  short-paper shape, placeholder authors and DOI. Headline: *an independent reproduction agrees with
  576 of 588 published values, every disagreement traces to one undocumented prior, and that
  column is mostly not a measurement.* **105 numbers re-derived from committed artifacts with an
  audit table (`m5_paper_numbers.py`), and the drafted text checked back against it:
  `m5_paper_check.py` = 92 checks, 0 failures.** Prior art positioned as registered — Goncharov &
  Sardana 2025 and van Haasteren 2024 own the general claim and the paper says *"This paper claims
  none of that"*; the γ_SW unreachability and the census are what is new. **A ten-row
  "corrections to our own earlier analysis" section** carries every claim this project has withdrawn,
  narrowed or reinstated. Two accuracy fixes found while drafting: the collaboration's single-pulsar
  posteriors come from **nested sampling** (`parallel-bilby` via `enterprise_warp`), not MCMC — so
  the reproduction crosses sampler families, which is a stronger check and is now said — and the
  paper's own methods sentence shows the prior ranges exist machine-readably in their pipeline.
  **No number in the RNAAS note changed**: re-derived (29 audited, 1 CORRECTED — the same M4 row)
  and re-checked (22 checks, 0 failures), because every claim in it is table-only and needs no
  sampling; only a short non-note addendum was added, recording the review and pointing at the
  paper. **Venue bar: 3 of 4, and the gap is still B-4 (a citable DOI), still a human step.**
  ≥192.4 core-hours over 277 runs. **M6 rec: mint the DOI, fill the paper's software citations
  (its only UNSOURCED slots), re-run the prior-art sweep at submission time, and consider a short
  methods note on the composition jackknife.** No commits, no accounts, no submissions, nothing sent.

- **2026-08-23** — **M4 complete** ([`M4-finish-the-array.md`](M4-finish-the-array.md)).
  **THE ARRAY IS FINISHED: 83/83 pulsars gated, and the reproduction agrees with the published
  noise table on 576 of its 588 values (98.0%), 73 of 83 pulsars in full** — every DM GP,
  chromatic GP, chromatic Gaussian event, annual chromatic term, solar-wind GP and free red process
  in the release, rebuilt from public data. **All 12 misses are explained by exactly two named
  causes:** 10 are the solar-wind spectral index (or the amplitude coupled to it) on the 8 pulsars
  whose published γ_SW is negative or crosses zero — outside the prior a reproducer must guess —
  and **2 are the same parameter on exactly the two rows the paper prints in bold because their
  values come from the CURN analysis, not the favoured model.** ΔlnL(ours − published) median
  **+0.70**, 79 positive / 4 negative over 83 — our sampler never under-performs the published
  solution anywhere. **The relative gate was registered before resuming and both outcomes are
  reported side by side throughout: 83/83 under it, 76/83 under M3's absolute rule, and the
  agreement rate is identical (98.0% vs 97.9%)**; its falsifier passes (relative-only pulsars agree
  61/62 = 98.4%) and its honest cost is measured (median minimum ESS 105 vs 347). **γ_SW wide
  variant, registered not post-hoc: 24 of 26 SW_Full pulsars compared — including all 7 with a
  negative published γ_SW — and U(−4,4) resolves ALL 10 of the campaign's solar-wind misses and
  creates none**; eight pulsars go from partial to full agreement, and **after the variant the only
  disagreements left in the whole 588-value table are the two σ_g values on the two bold rows the
  paper itself sources from the CURN analysis.**
  **Its registered control FAILED and the failure is a finding**: the control was defined by the
  sign of the published γ_SW, and that is not a proxy for "measured" — **5 of 24 solar-wind rows
  widen their γ_SW interval by >2× when the prior is widened (one of them, J1744-1134, with a
  *positive* published value), so their apparent constraint is the prior edge**; a post-hoc control
  built from genuinely data-constrained rows passes at 0.135. **CURN: the 83-pulsar factorised
  likelihood gives log10 A_CURN = −14.44 MAP, 68% [−14.64, −14.35], consistent with the published
  83-pulsar −14.28 ± 0.21** — the first independent reproduction of an MPTA common-signal amplitude
  at array scale — and M2's top-ten reproduces to 0.02 dex. **M3's "the effect is the width, not the
  shift" headline is WITHDRAWN**: at 82 common pulsars the 2.54-dex blow-up is gone (0.29 dex) and
  what remains is a **real +0.259 dex shift** clearing the pre-registered significance test. The
  reason is measured: **the FL product's 68% interval stays pinned to the prior floor until
  J1909-3744 enters and then collapses from 1.92 to 0.37 dex in ONE step** — the array's strongest
  single constraint does it alone, and any subset amplitude without it is not yet a measurement.
  Seam (a) holds (2 of 12 free-β pulsars prior-driven; ν_piv 860 MHz buys a factor 2.5 in A_Chrom
  precision); seam (b)'s bar triples with a 12-pulsar null control (0.463 dex) and **M2's withdrawn
  J1600-3053 claim is partly reinstated at −1.22 dex**, on a relative-gate-only run, which is said
  plainly. **The RNAAS table-audit note is DRAFTED — NOT SUBMITTED**
  ([`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md), 1,391 words + one table,
  RNAAS limits verified live): **NOT SCOOPED on all four claims** (44 citing works checked, no
  erratum, no prior file anywhere in the release — verified by opening the tarballs), 29 numbers
  re-derived by an independent parser with **1 correction, and it was in M4's own pre-registration**.
  The `enterprise_extensions` γ_SW default is now version-stamped (U(−2,1) in v2.4.3–v3.0.3, widened
  to U(−6,5) in Sept 2025). A plainly-worded paragraph Matthew could send the MPTA is **DRAFTED —
  NOT SENT** inside the note. **Venue bar: 3 of M3's 4 conditions now MET; the only gap is B-4, a
  citable DOI, which is a human step.** ≥183 core-hours recorded. **M5 rec: the Zenodo DOI, finish
  the 2 outstanding `swwide` runs, register an ESS floor from M4's measured distribution,
  re-specify the solar-wind control and finish the prior-propping census, then write the paper.**
  No commits, no accounts, no submissions, nothing sent.

- **2026-08-21** — **M3 in progress → reported** ([`M3-noise-criticism.md`](M3-noise-criticism.md)).
  **The all-83 campaign is 48/83 gated and agrees with the published table on 296 of 299
  parameters (99.0%), 46 of 48 pulsars in full** — including 9 chromatic Gaussian events, 4 annual
  chromatic terms, 7 free-β chromatic GPs, 21 DM GPs and 10 free red processes, all rebuilt from
  public data. **The mode-vs-model diagnostic was run on every gated pulsar, not just the misses:
  ΔlnL(ours − published) median +0.40, 45 positive / 3 negative, range −0.67 to +8.56** — our
  sampler never under-performs the published solution anywhere, and the largest ΔlnL values sit on
  pulsars that agree on everything (the diagnostic's noise floor).
  **All 3 misses are the same parameter, γ_SW, on the 2 pulsars whose published value is NEGATIVE
  and therefore outside the prior we declared.** Root cause found and measured: the paper tabulates
  **no prior ranges at all**, M1's blanket γ ~ U(0,7) was applied to the solar-wind GP, and
  **enterprise_extensions' own `solar_wind_block` defaults to γ_SW ~ U(−2,1)** — so **7 of 26
  tabulated γ_SW values (27%) cannot be reached by a good-faith reproducer** (19 of 26 affected once
  interval-crossings are counted). A declared post-hoc rerun with γ_SW ~ U(−4,4) turns J1327-0755
  from **3/5 to 5/5**. **Table audit (no sampling): 26 of 588 published values (4.4%, 22 pulsars)
  have a MAP outside their own printed 68% interval** — 13 of them in the A_13/3 column, 5 of 20 in
  E_Q, zero in every non-amplitude column — **and 66 of 83 A_13/3 rows are bounded by the prior**
  (68% interval reaching below −16.5, the paper's own "clearly disfavoured" point); only **6** are
  constrained to better than 0.7 dex. **Seam (a): the A–β ridge is universal** (median r = −0.90,
  slope −0.21 dex per unit β) **but only 2 of 9 free-β pulsars are prior-driven** — J0437-4715
  (A_Chrom moves 0.38 dex, and its A_13/3 0.17 dex, under a U(0,7) β prior) and J1802-2124.
  **This corrects M2: J1017-7156 is data-driven, not the prior finding M2 called it** (0.00 dex
  under every alternative prior). Exploratory bonus: the amplitude–β covariance vanishes at a
  **reference frequency of ~855 MHz, not the tabulated 1400** — re-quoting there halves the
  amplitude uncertainty (0.46 → 0.21 dex) for free. **Seam (b): real, one-directional, and smaller
  than M2 thought.** With a proper whites-fixed control isolating the added red process, Δ(A_13/3)
  has median −0.03 dex, range −0.77 to +0.12, **8 of 26 above the 6-pulsar null control's 0.144 dex
  threshold, 18 of 26 moving DOWN**; the two biggest movers (J1721-2457, J1547-5709) are among the
  six best-constrained rows in the table. **M2's "J1600's A_13/3 drops 1.3 dex" is withdrawn** — it
  was confounded by simultaneously fixing the white noise. **CURN: FL product −14.30 (36 psr, `fl`
  config) and −14.18 (33 psr, `table` config), both consistent with the published −14.28 ± 0.21;
  on the 32 pulsars gated in both, ΔMAP = +0.14 dex** — inside the published 1σ, but flagged
  significant by the pre-registered exclusion clause, and **the real effect is the width**:
  [−14.63,−14.12] → [−16.85,−14.31]. Adding the collaboration's own mitigation costs sensitivity,
  and this is a number for that cost. **83-pulsar FL NOT reached** (coverage 48/83).
  **A1 extended to all 83: 82/83 PASS**; the 63 pulsars whose release is internally complete match
  tempo2's own TRES to a median of **0.02%**, and every material discrepancy traces to the 20 that
  ship fewer ToAs than their par fitted. Three ephemeris defects found: 8 pars miss their own TRES
  until one WLS refit (7 recovered), **J1825-0319 ships an unphysical negative Shapiro amplitude**
  (H3 = −2.98e−7 s ⇒ M2 < 0; PINT refuses to build it), `TRACK -2` confirmed inert array-wide.
  Economics corrected: **86 CPU-hours** so far; the binding cost is not the likelihood but the
  **absolute** stability tolerance applied to 3-dex-wide prior-limited posteriors (a relative rule
  would have passed 52 rather than 48). **Venue: bar NOT yet cleared** — coverage fails, the CURN
  result is a width not a shift; the table audit alone is an RNAAS-sized, finished product.
  **M4 rec: finish the array (60–100 more core-hours), register the relative gate, run γ_SW wide as
  a registered variant, then write up.** No commits, no accounts, no submissions.

- **2026-08-18** — **M2 complete** ([`M2-converge-scale.md`](M2-converge-scale.md)).
  **J1909-3744 CONVERGED 9/9** — and *both blind chains found the mode unaided* (the informed
  chain, started at the published MAP, only confirms it stays and mixes); M1's ΔlnL = +22.4
  shortfall closed by sampler machinery alone (per-signal jump groups + per-block prior draws +
  an enforced wall-clock budget), likelihood untouched (digit-identical lnL at the reference
  point). All three chains beat the published MAP's own likelihood (97,308.3 vs 97,306.1); the
  chromatic block lands dead-on (A_DM −13.600 vs −13.60; n_earth 4.94 vs 4.96).
  **Top-10 campaign: 10/10 cleared the gate, 9/10 full agreement, 76/78 parameters agree** —
  including every hard structure (free-β chromatic GPs, two chromatic Gaussian events, an annual
  chromatic term). The only miss, J1017-7156's chromatic A–γ pair, is diagnosed the M1 way and
  is **the mirror of M1's case: our likelihood prefers OUR point by ΔlnL = +4.8** → a
  prior/convention finding on a flat A–β ridge, not a sampling failure, and far too small to
  contradict the table. **Factorised-likelihood CURN (10 psr): log10 A_CURN = −14.46 MAP /
  −14.53 median [−14.92, −14.31] — consistent with the published 83-psr −14.28 ± 0.21**;
  no detection/evidence claim (γ fixed at 13/3, no HD/CW). **Near-miss caught:** a frozen chain
  (acceptance 0.016) *passed* the pre-registered gate — not moving is maximally "stable" — and
  would have published −14.95 [−16.47, −14.54], flagged inconsistent; rerun at a tighter jump
  scale gave 0.189 acceptance and the number above. All 23 runs audited (others 0.167–0.489); the
  gate now carries an acceptance floor. **Harness hardened and proven:** wall-clock chunking,
  checkpoint/resume (six runs recovered from mid-flight kills), summary-on-every-exit, nice-19 +
  thread pinning, manifest inventory. **Three environment/library defects found and fixed:** an
  **enterprise 3.5.0 bug** (varying-basis params zero the GP prior matrix → guaranteed crash when
  sampling a chromatic index), e_e 3.0.3 jump proposals broken under numpy 2, and WSL killing
  detached campaigns (two layers). A1 extended to all top-10: 10/10 PASS (J0437's tempo2-`T2`
  binary and 12 pars' inert `TRACK -2` cleared). **Economics remeasured: M1's J1909 eval was 4.5×
  pessimistic** (97 ms 1-thread / 43 ms 4-thread, not 436 ms) → all-83 noise campaign is an
  overnight job; full-array CURN 2.5–5 d. **M3 rec:** cross-PTA noise criticism (the two seams M2
  exposed) → all-83 campaign → 83-pulsar FL → full-PTA CURN; CW/HD still behind the sparse stack.
  No commits, no accounts, no submissions.

- **2026-08-16/17** — **M1 complete** ([`M1-access-reproduction.md`](M1-access-reproduction.md)).
  **W1a access: PASSED** — the 4.5-yr release is fully public, account-free at Data Central
  (DOI 10.57891/j0vh-5g31): 83 par + 83 tim (245,907 sub-banded ToAs, 32-ch), 10,014 epoch
  PSRFITS archives (85 psr incl. 2 profile-only extras), 83 portraits; **no noise/common-signal
  chains ship at all** (the "anisotropy supplement" is 9 MP4 movies) → chain-level lanes are
  MPTA-dead, likelihood-level lanes are wide open; no license stated. **W1b stack: BUILT** in WSL
  without sudo (PINT 1.1.6 + enterprise 3.5.0 via --no-deps + loud-failure sksparse shim +
  e_e 3.0.3 + PTMCMC; WSL root disk was 100% full → venv on /mnt/c). **A1 PASS:** PINT weighted
  RMS matches tempo2's in-release TRES to +0.35% (J1909-3744) / +0.51% (J2241-5236). **W2
  (pre-registered): J2241-5236 5/5 parameters agree** with the published noise table (posterior
  widths match nearly edge-for-edge; SW conventions validated); **J1909-3744 5/9** — whites +
  A_13/3 dead-on (-14.288 vs -14.28), the chromatic DM↔SW block stuck in a local mode, and the
  post-run diagnostic shows our own likelihood prefers the published solution by ΔlnL = +22 →
  sampling shortfall, not model error; both formally land the pre-registered A3 feasibility
  verdict (chains under the sample gate; host ran a game at 100% CPU most of the session).
  **Economics measured:** fixed-white eval 1.4 ms (64× cheaper than free-white) → full-83 CURN
  ~1.3 d/1M iters, no sksparse needed; all-83 noise campaign ~1 day wall at 16-way parallel; CW/HD
  needs the sparse-stack upgrade first. **Recommended M2:** converge J1909 + scale to top-10 +
  factorised-likelihood CURN amplitude; W3 = cross-PTA noise criticism first, full-array CURN
  campaign second, CW/HD deferred. Data 1.25 GiB in `data/` (gitignored); scripts LF,
  committed-ready; no commits made (Matthew's call), no accounts, no submissions.
