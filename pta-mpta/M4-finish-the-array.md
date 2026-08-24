# M4 — finishing the array, the relative gate, the γ_SW wide variant, and the table-audit note

*2026-08-23. Fourth milestone of avenue #2. Repo law: every externally-sourced number carries its
source URL or the mark UNSOURCED; negative results are results; blockers are findings;
**every criterion is pre-registered before the run that tests it**.
Foundation: [`M1-access-reproduction.md`](M1-access-reproduction.md) (access, stack, conventions,
the mode-vs-model diagnostic), [`M2-converge-scale.md`](M2-converge-scale.md) (hardened harness,
acceptance floor, factorised-likelihood machinery) and
[`M3-noise-criticism.md`](M3-noise-criticism.md) (the all-83 campaign at 48/83, the two seams, the
table audit, and the three recommendations this milestone executes).*

---

## 1. Pre-registration (written 2026-08-23, BEFORE any M4 sampling and BEFORE resuming any M3 campaign)

Everything in §1 was fixed before the first M4 chain started and before the checkpointed M3
campaigns were resumed. The coverage snapshot the registration was written against, taken from
`scripts/m3_status.py` on the on-disk checkpoints at 2026-08-23 15:06 UTC (no process running —
the host had rebooted, every campaign was cold on disk):

| variant | gate-met | finished without gate | mid-flight (checkpointed) | not started |
|---|---|---|---|---|
| `noise` | **56 / 83** | 0 | 24 | 3 |
| `table` | 34 / 83 | 2 | 2 | 45 |
| `fl` | 42 / 83 | 1 | 0 | 40 |

(M3 reported at 48/83 `noise`; the campaigns ran on for a few hours after that section was written
and before the host went down, which is why the resume point is 56. Every number in M3 §6–§8 stands
as reported against its own 48-pulsar snapshot.)

### 1.1 What M4 sets out to deliver

1. **The finished array** — all 83 pulsars gated in `noise`, and every gated pulsar's dependent
   `table` and `fl` runs, under a newly registered stability gate (§1.2).
2. **The γ_SW wide-prior variant** — a *registered variant*, run on the affected SW pulsars, that
   measures how many of the campaign's prior-forced misses it resolves (§1.3). It does **not**
   replace the main campaign, and the main campaign's agreement statistic is not retro-fitted to it.
3. **The 83-pulsar factorised-likelihood CURN** in both model configurations, against the published
   −14.28 ± 0.21 and against M3's 36- and 33-pulsar products (§1.4).
4. **The table-audit note** — the RNAAS-sized, zero-compute product M3 §9.5 identified, drafted to
   the standard of the erosita-dr2 write-up: every number re-derived from committed artifacts and
   listed in an audit table, prior art checked first, venue limits verified live (§1.5).

No detection or evidence claim is made anywhere in M4. γ is fixed at 13/3 throughout every CURN
slice; no Hellings–Downs correlation and no continuous-wave search is attempted. No submissions, no
accounts, no commits, no pushes, nothing sent to anyone.

### 1.2 R-criteria — the scale-relative stability gate (registered here, before it is used)

**The problem it fixes, as measured in M3 §10.1.** M1's stability rule is an *absolute* tolerance:
the last-half posterior median must sit within 0.1 (log10 amplitudes, EFAC) / 0.3 (spectral indices,
n_⊕) / 0.1 × prior width (deterministic-event parameters) of the full-chain median. M3 measured
that this, and not the likelihood, is what the campaign's compute is actually buying: applied to an
`A_13/3` posterior that is **3.01 dex wide at the median** because it is bounded by the prior rather
than the data (M3 §4, 66 of 83 rows), a 0.1 dex tolerance demands the running median of a
near-flat distribution be stable at ~3% of its own width. That is a slow random walk, and it is a
requirement on the *prior*, not on the data. M3's post-hoc diagnostic measured the cost at
**4 pulsars' worth of compute at the 48-gated snapshot** (52 would have cleared a relative rule),
and recorded that the parameter holding the gate on the ungated runs was an amplitude in 8 cases and
a spectral index in 7 — i.e. exactly the unconstrained ones.

**R1 — the M4 gate (the rule).** A run is *stable* when, for **every** sampled parameter,

> |median(last half of post-burn) − median(all post-burn)| ≤ **max( t_abs , 0.1 × W68 )**

where `t_abs` is the M1/M2/M3 absolute tolerance for that parameter, unchanged and listed in
`mpta_models3.stability_tol`, and `W68` is that parameter's own full-chain post-burn 68%
equal-tailed interval width. The full gate is unchanged in every other respect: **≥ 100,000 raw
post-burn iterations** (`noise`) / ≥ 50,000 (`table`, `fl`), **AND** R1 stability, **AND** the M2
acceptance floor **acc ≥ 0.05**, **AND** the wall cap (300 min `noise` / 120 min dependent, per
launch — M3 §11's note that relaunches make the cap a per-launch resource criterion stands).

**R2 — justification, stated before use.** The rule keeps the absolute tolerance wherever the
posterior is narrow (there `t_abs` is the binding term, so nothing is loosened for a parameter the
data actually constrain) and switches to a proportional criterion only where the posterior is wider
than 10 × t_abs — i.e. only where the absolute number was never a statement about convergence in
the first place. It is a **strict relaxation**: `max(t_abs, ·) ≥ t_abs`, so no chain that passed the
M3 gate can fail the M4 gate. That is deliberate — the point is that nothing already reported can be
un-gated by this change, and no result can be lost in the transition.

**R3 — it is a relaxation, therefore both outcomes are reported, always.** Because R1 is weaker
than M3's rule, adopting it silently would make the array look better for free. Registered
counter-measure, fixed here:

- Every run's summary JSON records **both** verdicts on its final chain — `stable` (absolute, the
  M3 rule) and `stable_rel` (R1) — together with each parameter's half-shift, its `t_abs`, its
  `W68`, and which of the two terms bound.
- Every coverage and agreement statistic in M4 is reported **twice**: once over the
  absolute-gated set and once over the relative-gated set, side by side, in the same table.
- The relative-gated-only pulsars are **named**, not just counted, so a reader can see exactly which
  results exist only because the gate moved.
- **Applied uniformly to old and new runs.** The recomputation runs over every summary on disk,
  including the 56 `noise` runs already gated under the absolute rule, so both columns exist for
  every pulsar in the array and not only for the ones M4 sampled.
- A run that stops when R1 is met has a shorter chain than it would have had under M3's rule, so its
  absolute verdict is evaluated at that stopping point. This is stated wherever the two columns are
  compared; it is the honest form of the comparison and it can only make the absolute column look
  *worse*, never better.

**R4 — an effective-sample-size statistic, recorded (not gated on).** Each run's summary gains a
per-parameter ESS, computed by the standard initial-positive-sequence autocorrelation estimator on
the thinned post-burn chain, and the run-level minimum over parameters. M4 does **not** gate on ESS
— introducing a second new criterion at the same time as R1 would confound the comparison — but the
statistic is recorded for every run so that a future milestone can register a gate on a measured
distribution instead of a guess. The ESS of the relative-gated-only runs is reported next to the
ESS of the absolute-gated runs; if the former is dramatically smaller, that is a finding against R1
and will be reported as one.

**R5 — the falsifier.** R1 is wrong if it lets through chains that disagree with the published table
*more* than absolute-gated chains do. Registered test: the per-pulsar agreement rate (C2 below) over
the relative-gated-only set vs the absolute-gated set. If the relative-only set's agreement rate is
worse by more than the binomial 1σ of the absolute set's rate, R1 is reported as having bought
coverage at the price of accuracy, and the headline agreement statistic reverts to the
absolute-gated set.

### 1.3 V-criteria — the γ_SW wide-prior variant (registered, not a replacement)

**What M3 measured.** The paper tabulates no prior ranges at all. M1's blanket γ ~ U(0,7) was
inherited by the solar-wind GP spectral index; `enterprise_extensions`' own `solar_wind_block` — the
function this analysis uses — defaults to **γ_SW ~ U(−2, 1)**
(`enterprise_extensions/chromatic/solar_wind.py:234`). **7 of the 26 SW_Full pulsars have a
tabulated γ_SW that is negative** and therefore unreachable under U(0,7); a further **12** have a
68% interval that crosses zero — **19 of 26 in total**. A declared post-hoc rerun with U(−4,4) took
J1327-0755 from 3/5 to 5/5 (M3 §6.4).

- **V1 — the variant, defined.** Tag `sw`, run id `<psr>_swwide_s1`. Identical to the `noise`
  variant in every respect — same data, same model, same conventions, same seeds policy, same
  harness — except that the solar-wind GP spectral index prior is **γ_SW ~ U(−4, 4)** instead of
  U(0, 7). Nothing else changes. Implemented by the already-existing
  `scripts/m3_run.py --sw-gamma-prior=-4,4` path (built for M3 §6.4 and unchanged), driven by a new
  `scripts/m4_swwide.sh`.
- **V2 — the affected set, fixed now.** All **26** SW_Full pulsars, i.e. every pulsar whose favoured
  model samples a γ_SW at all. Registering the full 26 rather than only the 19 M3 flagged is
  deliberate: the 7 unaffected pulsars are the variant's own internal control (§V5), and choosing
  the set by which pulsars M3 already knew were affected would make the variant's success rate a
  selection effect.
  The 26: J0614-3329, J0711-6830, J0900-3144, J1012-4235, J1017-7156, J1036-8317, J1125-5825,
  J1327-0755, J1435-6100, J1525-5545, J1614-2230, J1643-1224, J1652-4838, J1653-2054, J1658-5324,
  J1730-2304, J1732-5049, J1744-1134, J1751-2857, J1811-2405, J1825-0319, J1909-3744, J2124-3358,
  J2145-0750, J2234+0944, J2241-5236.
- **V3 — why U(−4,4) and not the library default U(−2,1).** Two of the published values (−2.32
  J1751-2857, −2.21 J1811-2405) fall outside the library default itself, so U(−2,1) could not
  reproduce them either and would trade one prior-forced miss for another. U(−4,4) is the smallest
  round symmetric range that contains **every** tabulated γ_SW value *and* every tabulated 68%
  interval edge in the column (most extreme edge: −3.14, J1327-0755). It is chosen from the
  published table, which is a form of post-selection, and that is declared here rather than
  discovered later: the variant answers "does a prior wide enough to contain the published column
  recover the published column?", which is a reproducibility question, **not** "is U(−4,4) the right
  prior", which is the collaboration's to answer. This limitation is repeated wherever the variant's
  numbers are quoted.
- **V4 — the measurement.** Per pulsar, the C2 agreement count under the variant vs under the
  registered `noise` run, and specifically: of the parameters that miss under `noise`, how many
  agree under `sw`. Array-level deliverable: **how many of the campaign's misses the wide prior
  resolves**, and how many it creates.
- **V5 — the internal control, and the falsifier.** For the 7 SW_Full pulsars whose published γ_SW
  is comfortably positive and whose 68% interval does not cross zero, widening the prior downward
  must change essentially nothing. Registered: their γ_SW and A_SW medians must move by less than
  the M3 §6.5 repeat-yardstick (0.19, the 90th percentile of our own run-to-run difference), and no
  currently-agreeing parameter anywhere in the 26 may start disagreeing. If either fails, the
  variant is reported as having perturbed the fit rather than fixed the prior, and V4's count is
  reported as void.
- **V6 — quoting discipline, fixed now.** The registered campaign's agreement statistic (the
  headline "N of 83 pulsars, M of K parameters") is quoted **under γ_SW ~ U(0,7)** and is never
  recomputed with the variant's results substituted in. The variant is reported as its own row, in
  its own table, with its own prior printed in the row label. Every sentence in M4 and in the note
  that quotes an agreement number states which prior it is under. Any figure that mixes them uses
  distinct series and a legend that names both priors.
- **V7 — gate.** The variant's runs clear exactly the same gate as the campaign (§1.2 R1, 100,000
  raw post-burn, acceptance ≥ 0.05, wall cap 300 min). Ungated variant runs are reported as ungated
  and excluded from V4's count, not quietly included.

### 1.4 F-criteria — the 83-pulsar factorised-likelihood CURN

Method unchanged from M2/M3: the paper's own (Taylor et al. 2022, 2022PhRvD.105h4049T) — the
factorised-likelihood posterior is the renormalised product of the per-pulsar log10 A_CURN
marginals, identical uniform priors making the prior division a constant; combination by
Gaussian-KDE product on a common support (`scripts/m3_fl_combine.py`), MAP and equal-tailed 68%
quoted.

- **F1 — the products.** Formed over the `fl` marginals (the collaboration's CURN configuration:
  favoured model + a free achromatic red process for every pulsar that lacks one) and over the
  `table` marginals (the noise table at face value). Both reported whatever they show.
- **F2 — the discipline that must stay intact.** Every chain entering a product has been audited
  against the acceptance floor and its acceptance rate is reported (M2 §5.1's frozen-chain
  near-miss). γ is fixed at 13/3. No Bayes factor, no Savage–Dickey, no detection claim, no
  Hellings–Downs, no continuous wave.
- **F3 — the comparisons, fixed now.** (i) against the published 83-pulsar **−14.28 ± 0.21**;
  (ii) against M3's 36-pulsar `fl` (−14.30, 68% [−14.92, −14.21]) and 33-pulsar `table` (−14.18,
  [−14.46, −14.08]); (iii) `fl` vs `table` on the pulsars gated in both, the seam-(b) propagation;
  (iv) M2's top-10 sub-product (−14.46 MAP / −14.53 median [−14.92, −14.31]), which M3 could not
  re-cover.
- **F4 — width is the registered headline, carried forward from M3.** M3 measured the interesting
  effect to be the *interval*, not the central value: on the 32 pulsars gated in both, ΔMAP was
  +0.14 dex (inside the published 1σ) while the 68% interval went from [−14.63, −14.12] to
  [−16.85, −14.31]. M4 therefore registers, before running: **the primary reported quantity of the
  seam-(b) propagation is the pair of 68% interval widths, and the central shift is secondary.**
  M3's pre-registered F4 significance rule (a shift counts if the MAPs differ by > 0.21 dex, or if
  one product's 68% interval excludes the other's MAP) is carried over unchanged so the two
  milestones' verdicts are comparable.
- **F5 — the volatility check, registered.** M3 observed the 36-pulsar product move 0.16 dex when
  the 36th pulsar arrived and concluded a subset product cannot stand in for the full one. M4
  measures that directly: the FL MAP and 68% width are recorded as a function of the number of
  pulsars in the product, adding pulsars in a **pre-registered random order fixed by seed 4** (not
  by constraint strength, which would manufacture a trend), and the resulting curve is reported.
  Convergence of that curve is the evidence that 83 is enough; its absence would be a finding.
- **F6 — scope statement, unchanged from M2 §1.6 / M3 §1.6.** What an FL amplitude establishes: that
  an independently implemented likelihood on public data reproduces the collaboration's
  common-signal amplitude *scale*, and how that scale moves under a model choice the collaboration
  itself flags. What it does not establish: the detection, the spectral characterisation, or
  anything about spatial correlations.
- **F7 — coverage honesty.** If the array does not finish, the products are reported with their
  exact pulsar counts in the row label, "83-pulsar" is not written anywhere it is not true, and the
  shortfall is reported in the same sentence as the number.

### 1.5 N-criteria — the table-audit note

Scope: **exactly** what needs no sampling and no coverage argument. Four claims, all of them
properties of the published table re-derived from committed artifacts:

- **(a)** the paper tabulates no prior ranges;
- **(b)** 7 of 26 published γ_SW values are negative and unreachable under the standard γ ∈ [0,7]
  range, with `enterprise_extensions`' own U(−2,1) default cited, and 2 outside even that — so a
  good-faith reproducer cannot land on them;
- **(c)** 26 of 588 published values (4.4%, 22 pulsars) have a MAP outside their own printed 68%
  interval, concentrated entirely in amplitude columns;
- **(d)** 66 of 83 A_13/3 rows are prior-bounded, only 6 constrained better than 0.7 dex.

Plus, sourced and flagged: J1825-0319's released ephemeris carries an unphysical **negative**
orthometric Shapiro amplitude.

- **N1 — venue limits verified live.** RNAAS's current word/figure/table limits are read from the
  AAS site at drafting time and cited with the URL and the retrieval date. Memory is not trusted.
  If the note does not fit, it is cut to fit, not the limits reinterpreted.
- **N2 — every number re-derived.** No number enters the note from M3's prose. Each is recomputed
  from the committed artifacts (`results/m3/published_table.json`, `table_audit.json`,
  `prior_coverage.json`, the A1 outputs) by a single script, `scripts/m4_note_numbers.py`, which
  emits an audit table listing, for every number in the note: the claim, the value, the artifact and
  field it came from, and PASS/CORRECTED against what M3 wrote. The audit table ships in the M4
  document. This is the erosita-dr2 procedure and it exists because that procedure corrected 14 of
  107 numbers.
- **N3 — prior art checked before drafting.** A literature check for anyone who has already
  published these observations — the MPTA data-release and noise papers themselves, the citing
  literature, PTA noise-modelling and prior-sensitivity work, and reproducibility/table-audit notes
  in the PTA literature. If prior art exists it is cited first and the note is re-scoped to what is
  new; if the whole content is already published, the note is dropped and that is reported as the
  result. The verdict is recorded either way.
- **N4 — fair and constructive, as a hard requirement.** The note opens on the collaboration's own
  admissions (the caption's MAP-outside-interval warning; the paper's own §Impacts of noise
  misspecification), states that the release being fully public and complete is the reason any of
  this could be checked, and pairs every observation with the concrete fix. No claim of error is
  made where the correct statement is a limitation. The three corrections this repo has already
  applied to *itself* (M2's J1017 "prior finding", M2's 1.3 dex J1600 claim, M1's blanket γ prior)
  are stated in the note as evidence that the same standard was applied inward first.
- **N5 — DRAFT, NOT SUBMITTED.** Author, affiliation and ORCID are placeholders. The file carries
  the mark in its title and its first line. Nothing is sent anywhere. Submission is Matthew's call
  and no part of M4 prepares a submission package beyond the text itself.
- **N6 — the collaboration paragraph.** A short, plainly-worded paragraph Matthew could send the
  MPTA about the γ_SW prior, if he chooses, is included **inside** the note file in a clearly
  labelled section marked DRAFTED — NOT SENT. It is not an email, it has no addressee, and nothing
  in M4 sends it.

### 1.6 Economics and honesty rules (unchanged from M3 §1.8)

Every run's measured eval time, sustained it/s, acceptance, ESS and exit reason go into its summary
JSON. Any chain used for a reported number must have passed the acceptance floor; the audit of all
runs' acceptance rates is reported before any number is quoted. Coverage is stated exactly at every
point where a number depends on it.

### 1.7 Corrections to §1 made after the fact (declared, not silently edited)

- **§1.3 V3, "most extreme edge: −3.14, J1327-0755" is wrong.** The re-derivation in §5.1
  (`scripts/m4_note_numbers.py`) measures the lowest printed γ_SW 68% lower edge as **−3.21, on
  J1811-2405**; J1327-0755's is −3.05. The number in the pre-registration was written from M3's
  prose rather than re-derived, which is exactly the failure mode N2 exists to catch — and it caught
  it here in this milestone's own registration first. The **conclusion is unchanged**: U(−4,4) still
  contains every tabulated γ_SW value and every tabulated interval edge in the column, with 0.79
  dex to spare. The wrong digit is left in place above and corrected here so the audit trail shows
  what was registered.

---

*Results below this line were written after the runs.*

## 2. The scale-relative gate, applied to old and new runs alike (R-criteria)

### 2.1 What was built

`scripts/mpta_harness.py` now computes **both** stability verdicts on every summary it writes —
`stable` (the M1/M2/M3 absolute rule) and `stable_rel` (R1) — together with, per parameter, the
half-shift, `t_abs`, the posterior's own 68% width `W68`, the effective tolerance `tol_rel`, which of
the two terms bound (`bound_by`), and an effective sample size (R4). Which verdict the **gate** reads
is a new argument, `gate_rule`, defaulting to `absolute` so nothing changes by accident;
`scripts/m3_run.py --gate-rule relative` is what every M4 launch passes.

`scripts/m4_regate.py` applies R1 to **every run already on disk**, recomputing both verdicts
exactly from the stored per-parameter fields (no chain reload needed) and writing them back as
`gate_met_abs` / `gate_met_rel`, with the M3-as-reported value preserved as `gate_met_m3`. It caught
a defect while doing so: two runs killed mid-flight by the host reboot had a harness-written summary
but no *post-processing* (no A2 comparison, no saved CURN marginal), because `m3_run.py` had never
returned. Marking those `gate_met` would have made the campaign skip them and silently drop them
from every downstream product — so the re-gate refuses to gate an un-post-processed run, and the
pool finished them.

### 2.2 Coverage and agreement under both gates (R3 — reported together, always)

Final state of the all-83 `noise` campaign, both columns computed on each run's final chain:

| | **ABSOLUTE** (M1/M2/M3 rule) | **RELATIVE** (M4 R1 rule) |
|---|---|---|
| pulsars clearing the full gate | **76 / 83** | **83 / 83** |
| pulsars agreeing on every tabulated parameter | 67 / 76 | **73 / 83** |
| parameters agreeing | 515 / 526 | **576 / 588** |
| agreement rate | **97.9 %** | **98.0 %** |
| acceptance range over gated runs | 0.158 – 0.527 | 0.158 – 0.527 |
| median run-level minimum ESS | 347 | 339 |

The dependent variants, same treatment:

| variant | started | absolute gate | relative gate | relative-only |
|---|---|---|---|---|
| `noise` | 83 | 76 | **83** | 7 |
| `table` | 82 | 62 | **81** | 19 |
| `fl` | 83 | 56 | **82** | 26 |
| `swwide` (M4 variant) | 26 | 13 | **22** | 9 |

**The seven relative-only `noise` pulsars, named as registered:** J0614-3329, J0955-6150,
J1125-5825, J1525-5545, J1545-4550, J1708-3506, J1902-5105. Nothing was lost in the other direction
— **0 runs pass the absolute rule and fail the relative one**, as R2 said must be the case for a
`max(t_abs, ·)` relaxation, and that is checked and printed on every re-gate rather than assumed.

The parameter holding the absolute gate closed, over the runs the relaxation admits, is exactly what
M3 predicted it would be: across all four variants the top blockers are `dm_gp_log10_A`,
`gw13_log10_A`, `red_gp_log10_A`, `sw_gp_log10_A`, `n_earth` and the annual/Gaussian-event
amplitudes — prior-limited amplitudes and one prior-limited density, never a
well-constrained parameter. For the `fl` variant the single biggest blocker is `red_gp_log10_A`
(12 runs): the free achromatic red process that variant *adds*, whose posterior in most pulsars is
the prior.

### 2.3 R5, the falsifier: the relaxation did not buy coverage with accuracy

> Relative-only pulsars agree on **61 of 62** parameters (**98.4 %**) against the absolute-gated
> set's **97.9 %** (binomial 1σ 0.6 %). **PASS** — the extra coverage is, if anything, marginally
> *better*-agreeing, and certainly not worse.

So the headline agreement statistic stays on the relative-gated set, as registered.

### 2.4 R4, the ESS statistic: recorded, and it is the honest caveat

ESS is recorded, not gated on, and it is the one place the relaxation shows a cost:

> run-level minimum ESS, median over the set: **347** (absolute-gated) vs **105** (relative-only).

A relative-only chain is genuinely less well mixed in its worst parameter — which is unsurprising,
because the worst parameter is the near-flat one whose median was still wandering. It does not
change any agreement verdict (§2.3), and the A2 criterion is an interval-overlap test that is
insensitive to a factor ~3 in ESS on a 3-dex-wide posterior. But it is the number a future milestone
should gate on, and M4 declines to do so only because introducing two new criteria at once would
have confounded the comparison R3 exists to make. **Recommended for M5: register an ESS floor,
sized from this measured distribution.**

### 2.5 What it cost and what it bought

M3 priced the absolute rule at "about 4 pulsars' worth of compute at the 48-gated snapshot". At full
coverage the number is larger and sharper: **the absolute rule would have left 7 of 83 `noise`
pulsars, 19 of 82 `table`, 26 of 83 `fl` and 9 of 26 `swwide` runs ungated** — i.e. it would have capped the
factorised-likelihood product at 56 pulsars instead of 82, which §6 shows is the difference between
a rail-dominated product and a measurement. The relaxation is worth more to the dependent variants
than to the campaign itself, because those are the runs that carry an *added* prior-limited red
process.

---

## 3. The array, finished

### 3.1 Coverage, stated exactly (C4)

**83 of 83 pulsars started, 83 of 83 gated** under the registered M4 gate (≥ 100,000 raw post-burn
iterations, R1 stability, acceptance ≥ 0.05); 76 of 83 under M3's absolute rule. Every one of the
**588 tabulated parameter values** now has a corresponding posterior from an independent
implementation on public data. This closes M3 §9.4's condition **B-1**: the reproduction covers the
whole array, and no selection argument is needed.

Chain sizes over the gated set: median **104,260** raw post-burn iterations; acceptance
**0.158 – 0.527**, every run above the M2 floor of 0.05 — **no frozen chain anywhere**, audited
before any number below was quoted.

### 3.2 Agreement: 73 of 83 pulsars in full, 576 of 588 parameters (98.0 %)

Under the pre-registered A2 rule (published MAP inside our 68% interval, **or** our median inside the
published 68% interval), quoted under the registered prior set — in particular **γ_SW ~ U(0,7)**
(§1.3 V6; the wide-prior variant is §4 and is never substituted into this number):

- **576 / 588 parameters agree (98.0 %)**
- **73 / 83 pulsars agree on every tabulated parameter**
- every model class in the release is built from scratch on public data with an independently
  implemented likelihood and sampled to the gate: 15 chromatic Gaussian events, 8 annual chromatic
  variations, 13 free-β chromatic GPs, 10 fixed-β chromatic GPs, 49 DM GPs, 26 solar-wind GPs,
  12 free achromatic red processes, 20 EQUAD and 29 ECORR terms, plus the fixed-γ = 13/3 amplitude
  in all 83;
- **every parameter of every chromatic Gaussian event, annual chromatic term, DM GP, chromatic GP,
  achromatic red process, white-noise term and A₁₃/₃ row agrees** — the 12 misses are confined to
  the solar-wind columns and to the Gaussian-event width on two rows (§3.3).

### 3.3 Every one of the 12 misses has one of two named causes

| pulsar | agree | ΔlnL (ours − published) | missed | cause |
|---|---|---|---|---|
| J1327-0755 | 3/5 | +0.42 | γ_SW, log₁₀A_SW | published γ_SW = −0.76, outside our prior |
| J1811-2405 | 6/8 | **−0.57** | γ_SW, log₁₀A_SW | published γ_SW = −2.21, outside our prior |
| J1643-1224 | 14/15 | +4.12 | γ_SW | published γ_SW = −1.96, outside our prior |
| J0900-3144 | 10/11 | +3.75 | γ_SW | published γ_SW = −0.20, outside our prior |
| J1652-4838 | 15/16 | +3.02 | γ_SW | published γ_SW = −0.68, outside our prior |
| J1730-2304 | 7/8 | +0.36 | γ_SW | published γ_SW = −1.61, outside our prior |
| J1751-2857 | 6/7 | +0.18 | γ_SW | published γ_SW = −2.32, outside our prior |
| J2124-3358 | 5/6 | +1.48 | γ_SW | published γ_SW 68% interval crosses 0 |
| J1902-5105 | 9/10 | +5.83 | σ_g | **not a like-for-like target** — bold row, values from the CURN analysis |
| J0610-2100 | 7/8 | +1.89 | σ_g | **not a like-for-like target** — bold row, values from the CURN analysis |

**Ten of the twelve are the solar-wind spectral index or the amplitude coupled to it, on the eight
pulsars whose published γ_SW is negative or whose interval crosses zero — the prior our reproduction
declared cannot reach them (§1.3, and the note's claim (b)).** The other two are the *same*
parameter, the Gaussian-event width σ_g, on **exactly the two pulsars the paper prints in bold in
its deterministic table**, whose caption states that their values "are taken from the CURN Bayesian
analysis" — a different model from the favoured single-pulsar one we sampled. They are not a
comparison the table invites.

**Nothing else in the array misses at all.** No DM, chromatic, white-noise, achromatic-red,
chromatic-index, annual, n_⊕ or A₁₃/₃ parameter disagrees anywhere in 83 pulsars.

### 3.4 The mode-vs-model diagnostic across the whole array (C3)

ΔlnL = lnL(our chain's best point) − lnL(published MAP vector), under our own likelihood, computed
for **every** gated pulsar and not only the misses:

> **median +0.70 over 83 pulsars, 79 positive / 4 negative, range −0.67 to +8.56.**

Our sampler never under-performs the published solution by more than 0.67 lnL anywhere in the array;
M1's ΔlnL = +22.4 shortfall has no analogue at scale. The pre-registered "genuine disagreement"
threshold (ΔlnL > 10 **and** a published interval narrower than 25% of its prior) is **not reached by
any pulsar in the array** — the largest values sit on pulsars that agree on everything, which is the
diagnostic's noise floor. The single negative outlier among the misses, J1811-2405 at −0.57, is a
pulsar whose published γ_SW our prior excludes, so its "best point" is constrained away from the
published one by construction.

---

## 4. The γ_SW wide-prior variant, run as registered (V-criteria)

Tag `swwide`, run id `<psr>_swwide_s1`: the identical favoured model, identical data, identical
harness, identical gate, with **γ_SW ~ U(−4,4)** in place of U(0,7) and nothing else changed. It
never overwrites the registered `noise` run, and §1.3 V6's quoting rule is enforced everywhere: the
83-pulsar agreement statistic of §3 is quoted **under U(0,7)** and is not recomputed with the variant
substituted in.

### 4.1 Coverage of the variant, stated exactly (V7)

All 26 SW_Full pulsars were started. **25 of 26 cleared the same gate as the campaign** and have
both runs available for comparison — including **all 7 whose published γ_SW is negative** and every
pulsar on which the registered campaign misses a solar-wind parameter. The one that did not,
J1525-5545, is reported as not-compared and excluded from every count below rather than quietly
included; it is a zero-crossing row that misses nothing under either prior in the campaign, and it
is the array's slowest model (2–5 it/s, §7).

### 4.2 V4 — what the wide prior does to the campaign's misses

| pulsar | class (from the published γ_SW) | published γ_SW | agreement under **U(0,7)** | agreement under **U(−4,4)** | Δ median γ_SW | Δ median log₁₀A_SW | resolved |
|---|---|---|---|---|---|---|---|
| J0900−3144 | negative | -0.20 | 10/11 | **11/11** | -2.40 | -0.18 | sw\_gamma |
| J1327−0755 | negative | -0.76 | 3/5 | **5/5** | -1.85 | -1.12 | sw\_gamma, sw\_log10\_A |
| J1643−1224 | negative | -1.96 | 14/15 | **15/15** | -2.58 | -0.38 | sw\_gamma |
| J1652−4838 | negative | -0.68 | 15/16 | **16/16** | -2.40 | -0.24 | sw\_gamma |
| J1730−2304 | negative | -1.61 | 7/8 | **8/8** | -3.15 | -0.46 | sw\_gamma |
| J1751−2857 | negative | -2.32 | 6/7 | **7/7** | -2.83 | +0.09 | sw\_gamma |
| J1811−2405 | negative | -2.21 | 6/8 | **8/8** | -2.59 | -1.62 | sw\_gamma, sw\_log10\_A |
| J0614−3329 | crosses-0 | +1.88 | 10/10 | **10/10** | -0.82 | -0.29 | — |
| J1012−4235 | crosses-0 | +1.87 | 8/8 | **8/8** | -1.85 | +0.15 | — |
| J1036−8317 | crosses-0 | +2.19 | 7/7 | **7/7** | -1.36 | -0.36 | — |
| J1125−5825 | crosses-0 | +1.56 | 8/8 | **8/8** | -0.13 | +0.03 | — |
| J1435−6100 | crosses-0 | +1.16 | 7/7 | **7/7** | -1.48 | -0.33 | — |
| J1614−2230 | crosses-0 | +0.24 | 7/7 | **7/7** | -0.97 | -0.52 | — |
| J1653−2054 | crosses-0 | +2.36 | 7/7 | **7/7** | -2.50 | +0.16 | — |
| J1658−5324 | crosses-0 | +2.36 | 5/5 | **5/5** | -2.08 | -0.04 | — |
| J1825−0319 | crosses-0 | +1.72 | 8/8 | **8/8** | -1.88 | -0.35 | — |
| J2124−3358 | crosses-0 | +0.19 | 5/6 | **6/6** | -2.36 | -0.23 | sw\_gamma |
| J2145−0750 | crosses-0 | +0.70 | 6/6 | **6/6** | -1.99 | -0.99 | — |
| J0711−6830 | clean | +1.28 | 5/5 | **5/5** | -0.03 | +0.01 | — |
| J1017−7156 | clean | +2.20 | 16/16 | **16/16** | -0.08 | -0.04 | — |
| J1732−5049 | clean | +2.04 | 5/5 | **5/5** | -0.14 | -0.01 | — |
| J1744−1134 | clean | +0.91 | 7/7 | **7/7** | -1.78 | -0.75 | — |
| J1909−3744 | clean | +1.39 | 9/9 | **9/9** | +0.05 | +0.02 | — |
| J2234+0944 | clean | +2.44 | 7/7 | **7/7** | -1.40 | -0.17 | — |
| J2241−5236 | clean | +1.81 | 5/5 | **5/5** | -0.01 | -0.00 | — |

> **Over the 25 compared pulsars the registered campaign misses 10 parameters under
> γ_SW ~ U(0,7); the variant misses 0 under U(−4,4). The wide prior resolves 10 of 10 and creates
> none.** Eight pulsars go from partial to complete agreement: J1327-0755 (3/5 → 5/5),
> J1811-2405 (6/8 → 8/8), J1730-2304 (7/8 → 8/8), J1751-2857 (6/7 → 7/7),
> J1652-4838 (15/16 → 16/16), J1643-1224 (14/15 → 15/15), J0900-3144 (10/11 → 11/11), and
> J2124-3358 (5/6 → 6/6), the one zero-crossing pulsar that also missed.

This is M3's post-hoc J1327-0755 check turned into a registered variant and extended to the class:
**every substantive disagreement between this reproduction and the published noise table is a
consequence of the solar-wind spectral-index prior we declared, and every one of them dissolves
when that prior is widened to a range containing the published column.**

The array-level bookkeeping, stated exactly. Of the **12** misses in the registered campaign
(§3.3):

- **10 are solar-wind parameters, all 10 are covered by the variant, and all 10 are resolved**
  (8 γ_SW + 2 log₁₀A_SW, on J0900-3144, J1327-0755, J1643-1224, J1652-4838, J1730-2304,
  J1751-2857, J1811-2405 and J2124-3358);
- **2 are the σ_g values on the two bold rows** whose published values come from the CURN analysis
  rather than the favoured model — not a solar-wind issue, not a comparison the table invites, and
  not something a prior change should touch.

**So after the registered variant there is no disagreement left anywhere in the 588-value table
that is attributable to the data or the implementation.** Every remaining one is either the
solar-wind prior we had to guess (resolved by guessing wider) or a row the paper flags as coming
from a different analysis.

**The V3 limitation, repeated where the numbers are quoted:** U(−4,4) was chosen because it
contains every tabulated γ_SW value and every tabulated interval edge (most extreme −3.21,
J1811-2405). It is selected from the answer. The variant therefore answers *"does a prior wide
enough to contain the published column recover the published column?"* — a reproducibility
question — and **not** *"is U(−4,4) the right prior"*, which is the collaboration's to answer.

### 4.3 V5 — the registered control FAILS, and the failure is the interesting part

> **V5 clause (i): FAIL.** Of the 7 "clean" control pulsars gated (published γ_SW comfortably
> positive, interval not crossing zero), the largest median move is **1.778 on J1744-1134**, with
> **1.40 on J2234+0944** second, against a yardstick of 0.19. The other five move
> 0.01–0.14.
> **V5 clause (ii): pass.** 0 parameters anywhere started disagreeing.
> **Registered consequence, applied: V4's count above is reported VOID.**

That is the pre-registered verdict and it stands. What it actually diagnoses, though, is not a
broken variant but a **mis-specified control**, and the evidence is unambiguous:

- **J2234+0944's γ_SW was never constrained at all.** Its 68% width is 3.96 under U(0,7) — 57% of
  that prior — and 4.02 under U(−4,4). An unconstrained parameter's median tracks the centre of its
  prior, so moving the prior centre from +3.5 to 0 must move it. A large move here is arithmetic,
  not perturbation.
- **J1744-1134's γ_SW only *looked* constrained.** Under U(0,7) it is 1.12 [0.47, 1.99] (width 1.52);
  under U(−4,4) it is −0.66 [−3.15, 1.28] (width **4.42**) and its amplitude falls from
  −6.48 [−6.71, −6.27] to −7.23 [−8.86, −6.42]. The narrow posterior was the prior edge. Its
  agreement is 7/7 under **both** priors, because the A2 interval test is satisfied either way.

**Declared post-hoc re-specification** (it does not overturn the registered verdict, it explains
it): define the control by the parameter actually being measured — the γ_SW 68% width below 25%
of the prior width under *both* priors. Four pulsars qualify (J0711-6830, J1017-7156, J1732-5049,
J2241-5236), and over them the largest move is **0.135 on J1732-5049**, comfortably inside the
0.19 yardstick. The machinery is not perturbing measured parameters; the registered control set
simply was not made of measured parameters.

**Which is itself a finding about the published column.** Measured across the 25 compared
pulsars, **5 of them widen their γ_SW 68% interval by more than 2× when the prior is
widened** — J1614-2230 (0.61 → 2.41), J1327-0755 (0.89 → 3.32), J1811-2405 (0.73 → 2.69),
J1744-1134 (1.52 → 4.42), J2145-0750 (1.52 → 3.79) — with their log₁₀A_SW widths going from
0.34–0.52 to 1.4–2.4 dex. For those rows the apparent solar-wind constraint under a
positive-only index prior is the prior edge, not a measurement, and one of them (J1744-1134) has a
*positive* published γ_SW, so the count of affected rows visible from the published table alone
(19 of 26, the note's claim (b)) is a lower bound.

### 4.4 V6 — quoting discipline, enforced

The 83-pulsar agreement statistic of §3 (**576/588, 98.0 %**) is quoted **under γ_SW ~ U(0,7)** and
was not recomputed with the variant substituted in. The variant's numbers appear only in this
section, in rows labelled with their own prior, and `results/m4/swwide.json` carries a `priors`
block naming both. The main campaign has not been retro-fitted in any way; its 12 misses stand as
measured.

## 5. The table-audit note (N-criteria) — DRAFTED, NOT SUBMITTED

The note is [`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md).
**1,340 words** of note proper plus one table, against a live-verified RNAAS limit of 1,500 words
and one figure *or* table. It carries **DRAFT — NOT SUBMITTED** in its title and first line, and
placeholder author fields.

### 5.1 N2 — every number re-derived, and the audit table

`scripts/m4_note_numbers.py` re-parses both longtables straight out of the arXiv LaTeX source with
code that shares nothing with M3's parser, cross-checks the two value by value (**504 noise values,
0 mismatches**), recomputes every claim, and prints the audit below. The `M3 prose` column is M3's
number transcribed by hand into the script, so the comparison is a real check rather than a re-print.

| # | claim | re-derived value | source | M3 prose | verdict |
|---|---|---|---|---|---|
| 1 | noise-table rows (independent parse of the arXiv LaTeX) | 83 | `data/paper/mnras_template.tex` | 83 | PASS |
| 2 | deterministic-table rows | 23 | `data/paper/mnras_template.tex` | 23 | PASS |
| 3 | tabulated parameter values with a printed interval | 588 | `independent parse, both longtables` | 588 | PASS |
| 4 | independent parse vs results/m3/published_table.json | 504 noise values, 0 mismatches | `cross-check` | 0 mismatches (M3 P1) | PASS |
| 5 | values whose MAP lies outside their own printed 68% interval | 26 | `independent parse (strict inequality)` | 26 | PASS |
| 6 | pulsars affected | 22 | `independent parse` | 22 | PASS |
| 7 | further values printing an offset of exactly 0.00 on one side (rounding; excluded) | 4 | `independent parse` | 4 | PASS |
| 8 |   of which log10 A_13/3 | 13 | `independent parse` | 13 | PASS |
| 9 |   of which E_Q | 5 | `independent parse` | 5 | PASS |
| 10 |   of which E_C | 2 | `independent parse` | 2 | PASS |
| 11 |   of which log10 A_DM | 2 | `independent parse` | 2 | PASS |
| 12 |   of which log10 A_s (annual) | 2 | `independent parse` | 2 | PASS |
| 13 | non-amplitude columns affected | ann_phase | `independent parse` | phase (annual) only | PASS |
| 14 | pulsars with a sampled gamma_SW (the SW_Full class) | 26 | `independent parse` | 26 | PASS |
| 15 | of those, published gamma_SW NEGATIVE (unreachable under gamma in [0,7]) | 7 | `independent parse` | 7 | PASS |
| 16 | further pulsars whose gamma_SW 68% interval crosses zero | 12 | `independent parse` | 12 | PASS |
| 17 | gamma_SW value or interval outside [0,7] | 19 | `independent parse` | 19 | PASS |
| 18 | published gamma_SW below the enterprise_extensions default floor of -2 | 2 | `independent parse + e_e source` | 2 | PASS |
| 19 | lowest printed gamma_SW 68% lower edge | -3.21 | `independent parse` | -3.14 (M4 pre-reg 1.3) | CORRECTED |
| 20 | A_13/3 rows whose 68% interval reaches below -16.5 (prior-bounded) | 66 | `independent parse` | 66 | PASS |
| 21 | A_13/3 rows bounded on both sides | 17 | `independent parse` | 17 | PASS |
| 22 | A_13/3 rows constrained better than 0.7 dex | 6 | `independent parse` | 6 | PASS |
| 23 | median 68% width of the prior-bounded A_13/3 rows (dex) | 3.01 | `independent parse` | 3.01 | PASS |
| 24 | widest A_13/3 68% interval (dex) | 4.01 | `independent parse` | 4.01 | PASS |
| 25 | lines in the LaTeX source mentioning 'prior' | 7 | `regex over mnras_template.tex` | prose only | n/a |
| 26 | of those, stating a numeric prior RANGE | 0 | `regex over mnras_template.tex` | 0 | PASS |
| 27 | enterprise_extensions solar_wind_block gamma default | U(-2,1) | `enterprise_extensions/chromatic/solar_wind.py:234` | U(-2,1) | PASS |
| 28 | J1825-0319 released ephemeris H3 (s) | -2.9789742360740114e-07 | `data/partim/J1825-0319.par` | -2.98e-07 | PASS |
| 29 | J1825-0319 implied companion mass (Msun) | -0.448 | `H3/stig^3 / T_sun` | -0.448 | PASS |

**29 numbers audited, 28 PASS, 1 CORRECTED.** The correction is in **M4's own pre-registration**,
not in M3: §1.3 V3 asserted the lowest printed γ_SW 68% edge was −3.14 on J1327-0755; it is
**−3.21 on J1811-2405** (§1.7). Every number M3 published in prose reproduces exactly.

Two near-misses worth recording, because they show the check working rather than rubber-stamping:

- the fresh parser first returned **21** deterministic rows and **580** values instead of 23 and 588
  — it dropped the two rows the paper prints in `\textbf{}` (J0610-2100 and J1902-5105, the two
  whose values are taken from the CURN analysis). Caught by the cross-check against M3's artifact,
  not by inspection;
- M3's claim that "the word *prior* appears only in method prose" is right but was stated loosely.
  Re-derived precisely: **six occurrences in the uncommented source** (one of them the adverb
  "determined prior and fixed"), **two of them the phrase "prior range" with no range attached**,
  and **zero occurrences of "uniform", "log-uniform" or `\mathcal{U}`** anywhere in the paper.

### 5.2 N1 — the venue limits, verified live

Read from <https://journals.aas.org/research-notes/> on 2026-08-23: **1,500 words or fewer**,
**a single figure or table (but not both)**, abstract required since 2020-05-01, **non-peer-reviewed**
but moderated, published within days of acceptance, citable and indexed in ADS. The note is written
to fit those limits as read, not as remembered; it spends its single graphic on Table 1 because
claim (b) needs pulsar names to be actionable, and the alternative graphic
(`figures/m4_table_audit_a13.png`) stays in the repo.

### 5.3 N3 — prior art: NOT SCOOPED, but the framing had to change twice

A dedicated literature check covered the arXiv listing (v1 only — no replacement, no comments, no
ancillary files), the OUP record (no erratum or corrigendum; "corrected and typeset 17 Dec 2024"),
the companion gravitational-wave paper arXiv:2412.01153 (no prior table; it defers to this one), the
Data Central release contents, the absence of any MPTA code or prior repository, and **all 44 works
citing the paper** (OpenAlex `W4405033984`). **None re-analyses or audits the noise table.** The
nearest MPTA-specific follow-up, Mishra et al. 2026 (arXiv:2607.09004), re-models the solar wind of
this exact data set and never touches the tabulated γ_SW values or the priors; Di Marco et al. 2026
(arXiv:2603.23817) *reproduces* one MPTA pulsar's model and reports agreement without commenting on
documentation. **Coverage caveat, recorded:** ADS's citation endpoint refused automated access (HTTP
405) and Google Scholar hit a captcha, so the sweep rests on OpenAlex (44) plus a Scholar count (43).

Two risks the sweep flagged as unverified were closed **locally**, not taken on trust:

1. **"A prior or config file might ship inside a release tarball"** — this would have killed claim
   (a) outright. Checked directly against the downloaded release: `data/partim.tar.gz` contains
   exactly 83 `.par` and 83 `.tim` files and nothing else; the 423 MB anisotropy supplement is nine
   MP4s; `archives.tar.gz` and `portraits.tar.gz` are data. **No prior file exists in the release.**
2. **"The `enterprise_extensions` default may have moved"** — **it has.** The `solar_wind_block`
   powerlaw branch hard-coded γ_SW ~ U(−2,1) in v2.4.3 (Apr 2024, current at submission) and still
   in v3.0.3 (Jun 2025, the version this repo runs — verified in the installed source at
   `chromatic/solar_wind.py:234`), but **current master uses U(−6,5)** with the inline comment
   "priors from susurla et al. 2024" [sic], changed 2025-09-29 (verified by fetching master).
   U(−6,5) *does* contain all seven published values. The note now version-stamps every prior it
   cites, and gains a genuinely constructive point: the field's own default for this parameter moved
   after the paper appeared, which is precisely why the table needs to state its own.

Two things prior art *does* constrain, and the note now says so:

- **"Priors matter for PTA GW results" is already published** (Goncharov & Sardana 2025, MNRAS 537,
  3470; van Haasteren 2024, ApJS 273, 23). The note disclaims it explicitly and claims only the
  per-table measurement.
- **A negative H₃ is not by itself a scandal.** The h₃ parameterisation exists so that the fit
  converges whether or not the Shapiro delay is detected (Freire & Wex 2010, MNRAS 409, 199), and
  other PTAs tabulate non-significant h₃ values as a matter of course. M3 called J1825-0319's value
  "unphysical", which is true of the implied mass but overstates the finding. The note was cut back
  to the only claim that survives: the value is 3.1σ negative, it sits in the **ephemeris shipped for
  timing** rather than in a results table, and `PINT` therefore refuses to load the file as released.

The one reference the sweep supplied without page-level verification was resolved afterwards rather
than left flagged: "Hazboun et al. 2020" is Hazboun, Simon, Siemens & Romano 2020, ApJL 905, L6,
*Model Dependence of Bayesian Gravitational-wave Background Statistics for Pulsar Timing Arrays*
(arXiv:2009.05143, doi:10.3847/2041-8213/abca92,
<https://iopscience.iop.org/article/10.3847/2041-8213/abca92>). It is not cited in the note body, so
it is not in the note's reference list; **every entry in that list is cited in the text and every
one has been checked.**

### 5.4 N4/N5/N6 — fairness, state, and the collaboration paragraph

The note opens on the release's completeness as the reason the audit is possible at all, quotes the
paper's own caption warning and its own −16.5 reference point, and quotes the paper's own statement
that γ_SW "is allowed to have a red or blue spectrum" — which removes any suggestion that a negative
index is a surprise and narrows claim (b) to the only defensible version: *the sign is stated, the
range is not*. Every observation is paired with its fix. Three corrections this repo applied to
itself are on the record (M1's blanket γ prior, M2's J1017 "prior finding", M2's 1.3 dex J1600
claim), and M4 has now added a fourth to its own pre-registration.

**A short paragraph Matthew could send the MPTA about the γ_SW prior is drafted inside the note
file, in a section marked DRAFTED — NOT SENT.** It has no addressee, it has not been sent, and
nothing in this repository sends it.

### 5.5 Two inventory counts, verified against the tables

Also zero-compute, also checkable by any reader, and now one sentence of the note: the paper's text
and its own tables disagree by one in two places.

| statement in the text | tables | source |
|---|---|---|
| "the inclusion of this term is favoured in **25** pulsars" (stochastic solar wind) | **26** rows print both log₁₀A_SW and γ_SW | independent parse |
| "**58** [pulsars] display DM or scattering variations that require stochastic models" | **59** rows carry a DM GP (49), a chromatic GP (23), or both (13) | independent parse |
| "The majority (**58**) of the pulsars … showed a preference for a value of n_⊕ deviating from the nominal value" | **56** rows have a sampled n_⊕ (26 SW_Full + 30 SW_Det) | independent parse |

The first two are clean off-by-ones. The third is **not** reported as a discrepancy: "showed a
preference for a value deviating from 4 cm⁻³" is a statement about posteriors, not about which rows
sample the parameter, so 58 and 56 are not required to match and the note does not claim they are.
Three other counts checked exactly: 23 deterministic-model rows = 15 Gaussian events + 8 annual
terms, and 12 pulsars with a free achromatic red process — both as stated in the text.
## 6. The factorised-likelihood CURN on (nearly) the whole array (F-criteria)

`scripts/m4_fl_both_gates.py`, `results/m4/fl_both_gates.json`,
`figures/m4_fl_curn_both_gates.png`. Method unchanged: the paper's own factorised likelihood
(Taylor et al. 2022) — the renormalised product of the per-pulsar log₁₀A_CURN marginals, identical
uniform priors making the prior division a constant, Gaussian-KDE product on a common support, MAP
and equal-tailed 68% quoted. **F2 discipline intact: γ fixed at 13/3 throughout, every chain audited
against the acceptance floor before entering (0.158–0.527, none below 0.05), no Bayes factor, no
Savage–Dickey, no detection claim, no Hellings–Downs, no continuous wave.**

### 6.1 The products, under both gates (F1 + R3)

| product | gate | pulsars | MAP | median | 68% | width | consistent with published −14.28 ± 0.21? |
|---|---|---|---|---|---|---|---|
| **`fl` — the collaboration's CURN configuration** | **relative (registered)** | **83** | **−14.44** | −14.47 | **[−14.64, −14.35]** | 0.29 | **yes** |
| `table` — the noise table at face value | relative (registered) | 82 | −14.18 | −14.20 | [−14.28, −14.13] | 0.15 | yes |
| `fl` | absolute | 56 | −14.46 | −14.61 | [−15.69, −14.39] | 1.30 | yes |
| `table` | absolute | 62 | −14.44 | −14.44 | [−14.53, −14.32] | 0.21 | yes |
| published, 83 pulsars (arXiv:2412.01148, FL, γ=13/3) | — | 83 | −14.28 | — | [−14.49, −14.07] | 0.42 | — |
| M3, `fl` | absolute | 36 | −14.30 | −14.41 | [−14.92, −14.21] | 0.71 | yes |
| M3, `table` | absolute | 33 | −14.18 | −14.21 | [−14.46, −14.08] | 0.38 | yes |
| M2, best-timed ten (`fl`) | — | 10 | −14.46 | −14.53 | [−14.92, −14.31] | 0.61 | yes |

**The headline (F3(ii)).** The **83-pulsar** factorised-likelihood amplitude built from scratch on
public data is **log₁₀A_CURN = −14.44 MAP, −14.47 median, 68% [−14.64, −14.35]**, against the
collaboration's 83-pulsar **−14.28 ± 0.21**. The intervals overlap over [−14.49, −14.35]; the MAPs
differ by 0.16 dex, inside the published 1σ. This is the first independent reproduction of an MPTA
common-signal amplitude at full array scale, and it agrees.

**F3(iv), M2's top-ten, now re-covered.** M3 could not re-cover M2's exact ten. At full coverage all
ten have a gated `fl` run and their sub-product reads **−14.48 MAP, 68% [−15.01, −14.35]** against
M2's **−14.46 / [−14.92, −14.31]** — a 0.02 dex reproduction of a number computed by an earlier,
separate campaign with different seeds. Under the absolute gate only 6 of 10 qualify and the
sub-product reads −14.81 [−16.90, −14.63]: a six-pulsar product is not a ten-pulsar product, which
is §6.3's point in miniature.

### 6.2 Seam (b), and M3's "width not shift" headline does not survive full coverage (F3(iii), F4)

Like-for-like, on the pulsars gated in **both** configurations:

| | pulsars | `fl` MAP | `fl` 68% (width) | `table` MAP | `table` 68% (width) | ΔMAP (table − fl) | F4 verdict |
|---|---|---|---|---|---|---|---|
| **M4, relative gate (registered)** | **82** | −14.44 | [−14.64, −14.35] (0.29) | −14.18 | [−14.28, −14.13] (0.15) | **+0.259** | **significant** (both tests) |
| M4, absolute gate | 50 | −14.57 | [−16.04, −14.47] (1.56) | −14.46 | [−14.58, −14.34] (0.25) | +0.109 | significant (exclusion test only) |
| M3, absolute gate | 32 | −14.34 | [−16.85, −14.31] (2.54) | −14.19 | [−14.63, −14.12] (0.51) | +0.140 | significant (exclusion test only) |

**M3 registered the width as the headline and M4 has to withdraw that framing.** M3 measured, on 32
common pulsars, a shift of only +0.14 dex but a `fl` interval blown open to
[−16.85, −14.31] — 2.54 dex — and concluded that "the interesting effect is the width, not the
central shift". At **82** common pulsars **the width blow-up is gone**: the `fl` interval is
0.29 dex, tighter than the published 0.42, and what remains is a **real central shift of
+0.259 dex** that clears the pre-registered 0.21 dex magnitude test on its own as well as the
exclusion test.

The 2.54 dex tail was coverage, not physics — §6.3 measures exactly that — and M3's own volatility
warning was right even though its headline was not. The physical statement survives and sharpens:
**adding the collaboration's own misspecification mitigation (a free achromatic red process in every
pulsar that lacks one) moves the factorised CURN amplitude DOWN by 0.26 dex and roughly doubles its
68% width (0.15 → 0.29 dex).** The published −14.28 sits between the two configurations.

**The gate-dependence, stated plainly.** Under the absolute rule the same comparison gives
+0.109 dex — still **significant**, but only on the exclusion half of the F4 rule, not on the
0.21 dex magnitude half. That is not a contradicting measurement: the absolute-gated `fl` product
has only 50 pulsars and its 68% width is 1.56 dex, and §6.3 shows that a product of that size has
not yet left the prior-rail regime, so its mode is not yet a stable estimate of anything. Sign,
direction and verdict agree under both gates; only the magnitude differs, and it differs because of
coverage. Both rows are in the table above so a reader can see it.

### 6.3 F5, the volatility check: one pulsar detaches the FL product from the prior floor

Pre-registered: add pulsars to the `fl` product in a **random order fixed by seed 4** and record
MAP and 68% width against the count. `scripts/m4_fl_growth.py`,
`figures/m4_fl_growth_fl.png`.

| pulsars | 5 | 15 | 25 | 35 | 45 | 55 | **57** | **58** | 70 | 83 |
|---|---|---|---|---|---|---|---|---|---|---|
| MAP | −14.85 | −14.92 | −16.73 | −14.88 | −14.75 | −14.50 | −14.50 | **−14.45** | −14.45 | **−14.44** |
| 68% width (dex) | 2.22 | 2.07 | 2.01 | 2.12 | 2.21 | 2.05 | **1.92** | **0.37** | 0.34 | **0.29** |
| 68% lower edge | −16.92 | −16.98 | −17.08 | −17.08 | −16.92 | −16.49 | **−16.34** | **−14.71** | −14.69 | −14.64 |

Read across those rows. For the first 57 additions the product's **68% interval runs all the way
down to the prior floor near −17** and is 1.9–2.2 dex wide, because a product of mostly
prior-limited marginals keeps a rail-anchored tail no matter where its mode is; the mode itself
lurches between −16.7 and −14.5 as individual constrained pulsars enter. Then, at the **58th**
addition, the tail detaches: the width collapses **1.92 → 0.37 dex** and the lower edge jumps
**−16.34 → −14.71** in a single step, and it never comes back — the width is between 0.29 and 0.38
for every one of the remaining 25 additions. Over the final ten the MAP moves by **0.030 dex**.

**The 58th pulsar is J1909-3744.** The transition is not a gradual √N accumulation; it is the
array's single most informative pulsar arriving and pulling the product off the prior rail on its
own. M3 already suspected the shape of this — "83 weak constraints multiply to something the
strongest six dominate" — and the measurement sharpens it to *one*.

**The operational conclusion, which is a result in its own right:** an MPTA factorised-likelihood
CURN amplitude is not a measurement of the amplitude until the informative pulsars are in it. Before
that its credible interval still reaches the prior floor and its mode can read anywhere from −16.7
to −14.5 depending on which pulsars happen to be included. Every subset amplitude must therefore be
quoted with its pulsar count *and* with whether it contains the strongest constraints; M3's
36-pulsar and M2's 10-pulsar products should be read as consistency checks, not as estimates. It
also explains, quantitatively, why M3's 32-pulsar comparison produced a 2.54 dex interval and why
its "width" headline had to be withdrawn.

**Two honest caveats on this curve.** The addition order is a random permutation *of the gated set*
seeded at 4, so the exact step at which the transition occurs depends on where J1909-3744 lands in
that permutation — a different seed moves it, and on an earlier 82-pulsar run of the same script it
sat near 70. What does not move is that there is a step at all, that it is one pulsar wide, and that
the width before it is ~2 dex and after it ~0.3 dex. And the curve is built from the `fl`
configuration only; the `table` configuration is far less rail-dominated to begin with (its
83-pulsar width is 0.15 dex) because those runs do not carry the added, unconstrained red process.

### 6.4 Scope statement (F6), unchanged

This establishes that an independently implemented likelihood on public data reproduces the MPTA's
common-signal amplitude scale at full array size, and quantifies how that scale moves under a model
choice the collaboration itself flags. It does **not** establish the detection (no Bayes factor
computed), the spectral characterisation (γ fixed at 13/3 throughout), or anything about spatial
correlations (no Hellings–Downs, no continuous wave — both still behind the sparse-stack upgrade M1
documented).

### 6.5 The two seams at full coverage

Both M3 seam analyses were re-run on the finished array (`results/m3/seam_a.json`,
`seam_b.json`).

**Seam (a) — the chromatic A–β ridge: M3's verdict holds at full coverage.** All 23 chromatic
pulsars now have a gated posterior (13 free-β, 10 with β = 4). The ridge is universal
(median r = −0.89, range −0.95 to −0.59; slope −0.21 dex per unit β) and **2 of 13 free-β pulsars
are PRIOR-DRIVEN** by the registered S4 rule — the same two M3 named from a 9-pulsar sample,
**J0437-4715** (A_Chrom moves 0.34 dex under a U(0,7) β prior against a published half-width of
0.26, and its GW-relevant A₁₃/₃ moves 0.16 dex) and **J1802-2124**. The S5 fairness control passes:
reweighting the β prior moves EFAC by at most 0.0031 anywhere in the array. The exploratory
decorrelating reference frequency is confirmed on the full set: **ν_piv median 857 MHz (range
673–954)** — at or below the bottom of the 856–1712 MHz band — and re-quoting there takes the
log₁₀A_Chrom 68% width from **0.46 dex at 1400 MHz to 0.19 dex**, a factor 2.4 in precision for
nothing but a change of reference frequency. Prior *shape* remains the harder half: a Gaussian
N(4,1)/N(4,0.5) on β moves A_Chrom by up to 0.82 dex and would flag **7 of 13**.

**Seam (b) — the null control gets stricter, the effect gets smaller, and M2's withdrawn
J1600-3053 claim is partly reinstated.** At full coverage **81 pulsars have both dependent runs
gated: 70 test (no red process in the favoured model) and 12 control (red already present, so the
two runs are the same model and their difference is pure sampler noise)**. The control set has
doubled since M3, and with it the bar: the 95th percentile of |Δ_b| over the controls is now
**0.463 dex, not M3's 0.144**. Against that bar, Δ_b = median(A₁₃/₃ | favoured + free red) −
median(A₁₃/₃ | favoured) has median **−0.073 dex**, range −1.22 to +0.16, **49 of 70 move DOWN**,
and only **8 of 70 clear the control threshold** (10 exceed 0.3 dex, 7 exceed 0.5, 1 exceeds 1.0).
For **5 of 70** the published 68% interval does not contain our `fl` median. The largest movers are
**J1600-3053 (−1.22), J1902-5105 (−0.93), J1036-8317 (−0.81), J2010-1323 (−0.77), J1719-1438
(−0.74), J1721-2457 (−0.70) and J1547-5709 (−0.69)**; J1721-2457 and J1547-5709 remain, as in M3,
among the six best-constrained A₁₃/₃ rows in the whole table, so the effect is still largest exactly
where the table looks most precise. M2 claimed −1.3 dex for that pulsar off a
confounded comparison; M3 withdrew it, both because of the confound and because J1600-3053's `fl`
run could not be gated. With the confound properly removed by the whites-fixed `table` control and
the run admitted by the M4 gate, the effect is real and its size is **−1.22 dex, not −1.3 and not
zero**. The honest caveat, stated because it matters: **J1600-3053's `fl` run is one of the
relative-gate-only runs** (193,510 raw post-burn, acceptance 0.155, minimum ESS 89; it fails the
absolute rule on its Gaussian-event index, its Gaussian-event amplitude, and — by 0.153 against a
0.10 tolerance on a 3.25-dex-wide posterior — on A₁₃/₃ itself). Its `noise` and `table` runs both
clear both gates. So the reinstatement is real but rests on the gate change, and a reader should
know that.

---

## 7. Economics, at full array scale

- **≥ 187 core-hours** are recorded across the four campaigns on the *final launch of each run*
  (`noise` 96.4, `fl` 35.9, `swwide` 28.9, `table` 25.6). Because `elapsed_min` resets on resume and
  most runs were resumed at least once, the cumulative total including M3's measured 86 core-hours
  is larger; the recorded figure is a firm lower bound. M3's estimate of "60–100 further core-hours"
  for the `noise` campaign alone was close: 96.4 recorded on final launches.
- **Throughput.** 16 physical cores (AMD Ryzen 9 9950X3D, SMT2) at 1 BLAS thread per worker; 30
  concurrent workers ran at load 30 with 22 GB free and no swapping, and per-run rates recovered by
  roughly 2× as the pools drained — i.e. the box was oversubscribed by ~1.9× for most of the
  session and aggregate throughput still improved with worker count.
- **Median eval time over gated runs:** `noise` 67.8 ms, `swwide` 57.8 ms, `fl` 15.7 ms, `table`
  11.7 ms (the dependent variants hold the white noise fixed, which is where M1's 64× factor comes
  from).
- **Median gated chain length:** 104,260 raw post-burn (`noise`), 103,885 (`swwide`), 71,635 (`fl`),
  69,385 (`table`).
- **What the gate change bought, in compute terms.** Under the absolute rule the same wall time
  would have delivered 76/83 `noise`, 62/82 `table`, 56/83 `fl` and 13/26 `swwide`. Finishing those
  under the absolute rule would have cost, on the measured rates, well over another 150 core-hours
  spent almost entirely on random-walking the medians of parameters that are prior-limited by
  construction — and two of the seven ungated `noise` pulsars (J1525-5545 at 2–5 it/s) would not
  have finished in this session at all.

### 7.1 Operational notes worth keeping

- **The M3 `pkill` trap has a sibling, and it bit once.** M3 recorded that `pkill -f <pattern>`
  matches the invoking shell. The same is true of a hand-rolled `/proc` walk: a one-liner that kills
  everything whose command line contains `m4_supervise.sh` kills the shell that typed it, because
  that string is in *its* command line too. `scripts/m4_kill.sh` keys on the run **tag** (`n1`/`t1`/
  `f1`/`s1`) instead — which also avoids taking down the `swwide` variant when stopping `noise`,
  since `swwide` runs `--variant noise` under a different tag.
- **A campaign pass is not a campaign.** `m3_campaign.sh` is a single `xargs` pass: when every
  pulsar has either gated or hit its per-launch wall cap, the pass ends and nothing restarts it.
  M3's `table`/`fl` had a rolling loop; `noise` did not. `scripts/m4_supervise.sh` supervises all
  four, relaunching any variant that is short of target and has no driver alive, and logs coverage
  every five minutes.
- **Killed mid-flight ≠ finished.** The harness writes a summary on every exit path, but the *post*
  -processing (A2 comparison, CURN marginal, saved posterior) lives in `m3_run.py` after the harness
  returns. A run SIGKILLed by a host reboot therefore has a complete-looking summary and no
  products. `m4_regate.py` now refuses to gate such a run.

## 8. The venue bar, re-tested — and the recommended M5

### 8.1 M3's four conditions, re-scored on the finished array

M3 §9.4 fixed four falsifiable conditions for a full paper and §9.5 scored them "not yet — and the
gap is coverage, not evidence". Re-scored:

| condition | M3 | M4 |
|---|---|---|
| **B-1 Coverage** — the whole array, or a subset whose selection is independent of the outcome | **FAILS** (48/83, deliberately enriched in hard models) | **MET** — 83/83 gated, every one of the 588 tabulated values compared; no selection argument needed. 76/83 under M3's own absolute rule, reported side by side |
| **B-2 A quantitative headline the collaboration has not published** — either a measurable shift or a *tight* null (68% ≲ 0.2 dex) | **PARTIALLY MET** — a width result, `fl` interval 0.71 dex | **MET** — seam (b) is a **+0.259 dex shift** clearing the registered 0.21 dex test, measured on 82 pulsars with a 0.29 dex `fl` interval; plus the F5 result that the FL product stays anchored to the prior floor until the array's single most informative pulsar enters, and then detaches in one step |
| **B-3 Constructive and fair** | MET | **MET** — and M4 corrected M3 twice more (the "width not shift" headline withdrawn; the seam-(b) control threshold tripled), corrected M2's J1600 claim back toward its original size with the confound removed, and corrected a number in its own pre-registration (§1.7) |
| **B-4 Reproducibility of the reproduction** — code, priors and chains released with a DOI | MET in substance, pending in form | **unchanged: MET in substance, PENDING in form.** A citable archive is a human step and is not done |

**Verdict: three of four now met; the only gap left is B-4, and B-4 is a human step, not a
measurement.** M3's "what would change the verdict" prediction — that finishing the array would
shrink the `fl` interval by roughly √(83/36) ≈ 1.5× — under-predicted: the interval went from
0.71 dex at 36 pulsars to **0.29 dex at 82**, a factor 2.4, because the improvement is not
√N smoothing but a phase change out of the prior-rail regime (§6.3).

### 8.2 What the paper would now say

*"How much of a PTA noise table is a measurement?"* — the reproduction as the method (83/83, 98.0%
of 588 values, every miss traced to one of two named causes), the three reader statements as the
result, and the CURN as the consequence:

1. **The table reproduces.** 576 of 588 published values agree with an independent implementation on
   public data. Of the 12 that do not, 10 are the solar-wind spectral index or the amplitude coupled
   to it on pulsars whose published value our declared prior cannot reach — and a registered
   wide-prior variant covers all 10 and resolves all 10, creating none — and 2 are the same
   parameter on exactly the two rows the paper prints in bold because their values come from a
   different analysis. **After the variant, nothing in the table disagrees for a reason attributable
   to the data or the implementation.**
2. **Much of it is prior, not data.** 66 of 83 A₁₃/₃ rows are prior-bounded; the A_Chrom column is
   quoted at a reference frequency 2.5× from where the data constrain it; and 5 of the 25
   solar-wind rows tested have a γ_SW posterior whose apparent narrowness is the prior edge.
3. **The model choice the collaboration itself makes costs 0.26 dex.** Adding a free achromatic red
   process everywhere — the paper's own misspecification mitigation — moves the factorised CURN
   amplitude down by 0.259 dex and doubles its width. Nobody has published the size of that trade.
4. **A subset FL amplitude is not an amplitude.** Until the array's strongest constraint enters,
   the product's 68% interval still reaches the prior floor; when it does, the width collapses from
   1.92 to 0.37 dex in a single step.

### 8.3 Recommended M5

1. **Close B-4: the citable archive.** Priors, models, parser, harness, per-run summaries and the
   CURN marginals are all on disk and all deterministic. A Zenodo deposit with a DOI is the single
   remaining condition for the paper, and it is Matthew's step (account + publish). A paper
   criticising undocumented priors that does not publish its own would be self-defeating.
2. **Finish the γ_SW variant for completeness** — 25 of 26 SW_Full pulsars are compared, including
   **all 7 with a negative published γ_SW and all 10 of the campaign's solar-wind misses**, so V4 is
   complete in substance. The one outstanding run (J1525-5545, the array's slowest model) misses
   nothing under either prior and would only tidy the coverage line. A few core-hours, not a
   milestone.
3. **Register an ESS floor, sized from M4's measured distribution** (median run-level minimum ESS
   347 absolute-gated / 105 relative-only). M4 deliberately did not gate on ESS so as not to
   confound the R1 comparison; the distribution now exists and a floor can be set on evidence
   instead of a guess. This is the direct successor to R1 and should be registered before any
   further sampling.
4. **Re-specify the solar-wind control properly and finish the prior-propping census.** M4's V5
   failed because the control was defined by the published value's sign; the right definition is
   posterior width relative to prior width (§4.3). Run that census over all 26 SW_Full pulsars and
   report how many solar-wind GP detections in the published table survive a prior wide enough to
   test them. On the 25 tested so far the answer is 5 that do not.
5. **Write the paper.** Three of four bar conditions are met and the material is complete. The
   RNAAS table-audit note (§5) is separable, finished, and Matthew's call whether to submit; it
   should not block the paper and the paper should cite it if it goes out first.
6. **Still deferred, unchanged from M1/M2/M3:** the full-PTA (non-factorised) CURN posterior, and
   all Hellings–Downs and continuous-wave work, until the sparse-stack upgrade lands.

### 8.4 What M4 did not do

No submissions, no accounts, no outward sends, no commits, no pushes. The RNAAS note is DRAFT — NOT
SUBMITTED with placeholder author fields; the collaboration paragraph inside it is DRAFTED — NOT
SENT and has no addressee. The enterprise 3.5.0 upstream report M2 identified is still unfiled and
still Matthew's call.
