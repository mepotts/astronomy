# PRE-REGISTRATION — the December 2026 discriminator re-runs

**Written 2026-08-23. FROZEN on writing.**
*Author: the gaia-dr4 working agent, milestone M7, task 3.
Repo law: sourced-or-UNSOURCED; negative results are results; rules pre-registered.*

---

## 0. Why this document exists, and why today

Three milestones have tested candidate discriminators — X-ray activity (M4), chromospheric
and photometric activity (M5), astrometric quality (M5, M6) — against exactly one verdict
sample: the 65 adjudicated El-Badry+2026 (**EB26**) targets. Every one came back
footprint-, coverage- or power-limited. M6 built the machine that fixes that: the
epoch-vet harness, which manufactures verdicts at O(981) per pass instead of 65 in total.

On **2026-12-02** those verdicts will exist, and every one of these tests will be re-run
against them. At that moment there are four places where a post-hoc choice could turn a
null into a result without anybody lying:

1. **which** verdicts enter the test (harness only? EB26 only? both?);
2. **which** metric within a family is called the primary one;
3. **what counts as** a positive, a null, or "underpowered", chosen after seeing the p-value;
4. **the multiple-comparison correction**, chosen after counting the tests.

M6 named the first of those as the one remaining laundering route: the harness answers
`orbit_reality` and EB26 answers `compact_companion`, they are different questions, and
"pool them" versus "keep them apart" is a free parameter worth roughly a factor of ten in
sample size. This document removes all four, **while no verdict exists** — which is the
only moment at which removing them is worth anything.

**Freeze rule.** Once written, this file is not edited. Later milestones may add a
**declared variant** in a new dated section at the end (a variant is an analysis that was
not pre-registered and is labelled as such wherever it is reported); they may not change,
soften or delete any rule above the variant log. If a rule turns out to be unworkable in
December, the honest move is to record that it was unworkable and report the
pre-registered analysis anyway, alongside whatever replaced it.

**Numbers.** Every sample threshold below is computed by
`scripts/m7_prereg_power.py`, which imports M5's own power routines
(`mwu_power`, `min_detectable_auc`, `fisher_power`, `min_detectable_rate`,
α = 0.05 two-sided, target power 80 %, 5000 MC trials) rather than reimplementing them.
The full output is `out/m7_prereg_power.txt`. A fresh normal-approximation
implementation reproduced M5's published `min_detectable` column only to ~2 %, so the
published routines are used verbatim: two power conventions in one repository is one too
many.

---

## 1. The verdict sample: what enters, what does not

### 1.1 Verdict classes admitted

| producer | scope | admitted to a test | excluded |
|---|---|---|---|
| **harness** (`epoch_vet_harness`) | `orbit_reality` | `CONFIRMED`, `SPURIOUS` | `INCONCLUSIVE`, `NO_DATA`, `ERROR` |
| **EB26** (`elbadry2026`) | `compact_companion` | `CONFIRMED`, `SPURIOUS` | `UNKNOWN`, `MARGINAL`, `NOT_CO`, `OTHER` |

The exclusions are not judgements about those rows; they are the absence of a
two-class label. `INCONCLUSIVE` in particular is **not** a demotion (it means "too few
epochs to adjudicate") and must never be folded into `SPURIOUS`.

Excluded rows are **counted and reported** in every test's output, so that a shrinking
denominator cannot pass unnoticed.

### 1.2 Confidence

The **primary** analysis uses all admitted `CONFIRMED`/`SPURIOUS` rows regardless of
`verdict_confidence`.

**Declared variant V1** (permitted, must be labelled): the same test restricted to
`verdict_confidence` in {HIGH, MEDIUM}. Declared here so that it is available without
being a choice made after seeing the primary result. If V1 and the primary disagree, both
are reported, with the primary first.

### 1.3 De-duplication

The orbit key is `(source_id, nss_solution_type)` — `source_id` is a key of neither
`nss_two_body_orbit` (98 DR3 sources carry two astrometric solutions) nor `binary_masses`
(M2 landmine #4). A source adjudicated by **both** producers contributes **one row per
(source, scope)**, never two rows to the same group. Where a pooled analysis is run
(§2.3) and a source has both a harness and an EB26 verdict, **the EB26 verdict wins** and
the harness row for that source is dropped — because EB26's is the stronger claim, and
because letting the same object vote twice inflates significance.

---

## 2. Scope pooling — the rule, and the asymmetry it encodes

### 2.1 The two scopes are not the same question

- `compact_companion` (EB26, basis `rv_followup`) — *is there a dark massive companion?*
- `orbit_reality` (harness, basis `epoch_astrometry_f2`) — *does the published photocentre
  orbit have epoch-level support?*

A harness **SPURIOUS** and an EB26 **SPURIOUS** point the same way: the orbit is not real,
so there is no companion to have. A harness **CONFIRMED is strictly weaker** than an EB26
**CONFIRMED**: the orbit is real, the companion's nature is unestablished — it may be a
main-sequence star. The `CONFIRMED` group is therefore **heterogeneous under pooling and
the `SPURIOUS` group is comparatively homogeneous**, and that asymmetry has a statistical
consequence which is the whole reason this section exists.

### 2.2 The rule

> **PRIMARY analyses are SCOPE-PURE.** For each test, the primary analysis is run on
> **harness verdicts alone** (`verdict_scope == 'orbit_reality'`, `verdict_source ==
> 'epoch_vet_harness'`). This is the December sample, it is the powered one, and it is
> fixed here before it exists.
>
> **The frozen EB26 replication is a REGRESSION CHECK, not new evidence.** Each test is
> also re-run on EB26 verdicts alone. Its purpose is to reproduce M4's and M5's frozen
> artifacts byte-identically through the December code. A change there is a **bug report
> about the pipeline**, never a scientific update.
>
> **POOLED analyses are SECONDARY, labelled, and INTERPRETABLE IN ONE DIRECTION ONLY.**
> A pooled analysis (both scopes in both groups, de-duplicated per §1.3) may be reported
> only as a clearly-marked secondary result, and only its **positive** outcome may be
> interpreted. The reason is mechanical: contamination of the pooled `CONFIRMED` group by
> real-orbit-luminous-companion systems dilutes any true effect **toward the null**.
> Therefore
>
>   * a pooled **significant** result is a *conservative* positive — it survived dilution;
>   * a pooled **non-significant** result is **NOT** evidence of absence, must be reported
>     as "pooled: uninterpretable", and must never be quoted as a null.
>
> **A pooled analysis may never be substituted for the scope-pure primary**, before or
> after either is seen. If the scope-pure primary is underpowered, the pre-registered
> answer is **"underpowered"** — not "pool and try again".

### 2.3 Mandatory disclosure

Every reported number from any analysis that carries more than one `(verdict_source,
verdict_scope)` combination prints `verdict_schema.scope_composition_string()` for **both**
groups, immediately adjacent to the number. This is already enforced in the consumers
(M6 §2); the pre-registration makes it a reporting requirement as well as a code path.

---

## 3. The tests

Four families. **Holm–Bonferroni within each family**, exactly as M5 did; **no correction
across families**, because the families ask different questions of different data and
M5's published p-values were corrected that way — changing the correction now would make
December's numbers incomparable with the frozen ones. The number of tests in each family
is fixed **here**, below; adding a metric to a family in December re-inflates that
family's correction and must be declared as a variant.

### D1 — X-ray activity (eROSITA-DE)

| | |
|---|---|
| **question** | are SPURIOUS orbits more likely to have an X-ray counterpart than CONFIRMED ones? |
| **data** | eROSITA-DE DR2 (eRASS:3) + DR1, the frozen M4 crossmatch, `scripts/m4_eb26_erosita_test.py` |
| **primary metric** | in-footprint detection *rate*, SPURIOUS vs CONFIRMED, **Fisher exact two-sided** |
| **family size (Holm m)** | **3**: detection rate (primary), hard-band (2.3–5 keV) detection rate, DR1-only "fader" rate |
| **pre-registered direction** | SPURIOUS **more** often detected (M4 observed 2/13 vs 0/16) |
| **effect under test** | SPURIOUS 0.154 vs CONFIRMED 0.000 (M4's own observation) |
| **footprint cap** | eROSITA-DE is half the sky; M4 found 29 of 65 verdicted targets inside it (45 %). **This is the one test throughput cannot fix.** |

### D2 — Photometric variability

| | |
|---|---|
| **question** | are SPURIOUS orbits photometrically more variable? |
| **data** | DR3 `gaia_source` fluxes, Belokurov+2017 eq. 2 amplitude, magnitude-detrended; `scripts/m5_activity_discriminator.py` family B |
| **primary metric** | **ΔAmp_G**, Mann–Whitney U two-sided, effect reported as AUC(spurious > confirmed) |
| **family size (Holm m)** | **5**, unchanged from M5: ΔAmp_G, ΔAmp_BP, ΔAmp_RP, `phot_variable_flag == VARIABLE`, `std_dev_mag_g_fov` |
| **pre-registered direction** | SPURIOUS **more** variable (M5 observed AUC 0.659, same direction as M4's X-ray) |
| **effect under test** | AUC 0.659 |

### D3 — Astrometric quality (**not** activity)

| | |
|---|---|
| **question** | do the single-star astrometric-quality statistics separate the two classes? |
| **data** | DR3 `gaia_source`; `scripts/m5_activity_discriminator.py` family C |
| **primary metric** | **`astrometric_gof_al`**, Mann–Whitney U two-sided |
| **family size (Holm m)** | **6**, unchanged from M5: `ruwe`, `ipd_frac_multi_peak`, `ipd_gof_harmonic_amplitude`, `astrometric_excess_noise_sig`, `astrometric_gof_al`, `phot_bp_rp_excess_factor` |
| **pre-registered direction** | **EB26-CONFIRMED hosts are the NOISIER fits** — i.e. AUC(spurious > confirmed) **< 0.5** (M5: 0.254 on all-65, M6: 0.344 in-list) |
| **effect under test** | **the in-list effect, AUC 0.344**, not the all-65 AUC 0.254. M6 measured that the two populations give different effects and the day-one sample **is** the in-list population; testing against the larger all-65 effect would make the test look better powered than it is. |
| **carried caveats (from M5, not re-litigated)** | controlling for `significance`/G/distance the metric retains only p = 0.048; the effect is carried by the far-distance half (p 0.011 vs 0.420 near) |

### D4 — `flag_astrom_quiet`, thresholded

| | |
|---|---|
| **question** | does the frozen tiebreaker flag mark spurious rows more often than confirmed ones? |
| **data** | the day-one queue's own `flag_astrom_quiet` column (bottom quartile of `astrometric_gof_al` in the day's own main bin), joined to December's verdicts; `scripts/m6_astrom_quiet_decision.py` |
| **primary metric** | flagged fraction, SPURIOUS vs CONFIRMED, **Fisher exact two-sided** |
| **family size (Holm m)** | **1** (it is its own family; it is a decision about a config entry, not a discovery test) |
| **pre-registered direction** | SPURIOUS **more** often flagged |
| **effect under test** | a SPURIOUS marking rate of **0.30** against the measured in-list CONFIRMED marking rate of **0.075**. **0.30 is declared here, in advance**, as the smallest marking rate that would make the flag worth keeping as a tiebreaker. It is deliberately **not** the observed 0.00 — choosing the effect size after seeing the data is the exact manoeuvre this document exists to prevent. |

**D4's decision rule is the one M6 already froze** (config v5, `astrometric_quality_flag.m6_decision`), restated here unchanged so that it lives in one place:

- **KEEP** — the in-list continuous test reaches p < 0.05 two-sided in the M5 direction
  (AUC < 0.5) **and** the thresholded flag's in-list catch rate beats its marking rate at
  Fisher p < 0.05.
- **REMOVE** — the in-list continuous test is *well powered* (smallest detectable AUC
  ≤ 0.70) **and** the observed in-list AUC is consistent with 0.5.
- **CARRY** — anything else.

### N — the negative control

`phot_g_n_obs` is re-run exactly as M5 ran it, **outside every family and uncorrected**.
It must **not** discriminate.

> **If the negative control reaches p < 0.05 in December, the entire battery is declared
> suspect and no positive result from D1–D4 may be reported as a finding until the
> control is explained.** This rule has teeth precisely because it can veto a result we
> would like to have.

---

## 4. Decisive-sample thresholds

A test is **DECISIVE** when the smallest effect detectable at 80 % power at the achieved
sample size is at least as small as the effect under test (§3). That rule — not a fixed
row count — is the definition; the tables below are what it implies at three plausible
CONFIRMED : SPURIOUS ratios, because the harness's own split cannot be known in advance.
The three ratios are 1:1, the EB26 split 42:23 = 1.83:1, and the M6 pre-release harness
split 3:9 = 0.33:1.

*(All figures from `out/m7_prereg_power.txt`; the same file first reproduces M4's,
M5's and M6's published power statements as a check on the driver.)*

| test | effect under test | 1:1 | 1.83:1 (EB26) | 0.33:1 (harness) |
|---|---|---|---|---|
| **D1** X-ray, in-footprint | 0.154 vs 0.000 | 50 + 50 | 49 + 27 | 32 + 95 |
| **D1** X-ray, in-footprint, vs a 0.02 baseline | 0.154 vs 0.020 | 75 + 75 | 91 + 50 | 46 + 139 |
| **D2** ΔAmp_G | AUC 0.659 | 51 + 51 | 71 + 39 | 34 + 103 |
| **D3** `astrometric_gof_al` | **AUC 0.344 (in-list)** | 54 + 54 | 73 + 40 | 35 + 104 |
| **D3** *(reference only)* | AUC 0.254 (all-65) | 20 + 20 | 29 + 16 | 14 + 41 |
| **D4** flag marking rate | 0.30 vs 0.075 | 52 + 52 | 64 + 35 | 34 + 101 |

*(Read "50 + 50" as "50 CONFIRMED + 50 SPURIOUS".)*

**What one harness pass over the 981-row queue delivers**, at the same three ratios:
~490 + 490, ~633 + 347, or ~245 + 735. **D2, D3 and D4 clear their thresholds at every
ratio.** D1 does not follow, because it is capped by the eROSITA-DE footprint at ~45 % of
whatever is adjudicated — at 981 verdicts that is ~440 in-footprint rows, which clears
D1's thresholds too, but only if the CONFIRMED:SPURIOUS split is not extreme.

> **The honest reading of the table**: the sample-size problem that defeated M4, M5 and M6
> is solved by one harness pass, and it is solved with a large margin. If a December test
> still comes back non-significant, the pre-registered conclusion is a **NULL**, not
> "underpowered" — which is exactly the outcome this repo has never yet been able to
> claim, and it is worth as much as a positive.

---

## 5. Outcome classification — decided now, per test

For each test, exactly one of these six labels is assigned. The label follows
mechanically from the numbers; there is no residual judgement.

| label | condition |
|---|---|
| **POSITIVE** | Holm-corrected p < 0.05 within its family **AND** the effect is in the pre-registered direction **AND** the test is DECISIVE (§4) |
| **POSITIVE (conservative, pooled)** | as POSITIVE but obtained only in the secondary pooled analysis (§2.2); reported with the scope composition and never as the headline |
| **NULL** | not significant **AND** DECISIVE. Meaning: the effect claimed by M4/M5 is *excluded* at 80 % power. This is a result and is reported as one. |
| **UNDERPOWERED** | not significant **AND** not DECISIVE. The smallest detectable effect at the achieved n is reported alongside, as M4/M5/M6 already do. |
| **DIRECTION REVERSAL** | significant but **opposite** to the pre-registered direction. Reported as a reversal, never as a confirmation; it retires the M4/M5 direction rather than supporting it. |
| **NOT TESTABLE** | fewer than 5 rows on either side, or zero rows survive the join to the data the metric needs. The coverage count is the result (this is what M5 family A returned for `activityindex_espcs` at 3 confirmed / 1 spurious). The code emits this rather than raising. |

Two further rules, both aimed at things this repo has actually got wrong before:

- **A null is never quoted without its expected value under the working hypothesis.**
  M6 landmine #6: "0 of 7" was reported as evidence of failure when the *expected* catch
  was 0.60. Every non-detection reports the count the working hypothesis predicts.
- **An agreement threshold is set from the reference's own printed precision**, not from a
  hopeful epsilon (M6 landmine #10). This applies to the regression check in §2.2: the
  EB26 replication must reproduce the frozen artifacts **byte-identically**, and anything
  less is a bug.

---

## 6. The exact commands

These are the December commands, frozen. They are also in
`DR4-DAY-RUNBOOK.md` §3.3, which points here.

**Executability note (2026-08-23).** Every command below was run on the day this file was
written, against the 88-record store that exists today. Several raised, and every one was
fixed before this file was frozen:

* both discriminator tests hard-coded a `== 76` assertion on the verdict join, so the
  **pooled** commands died the moment the store held a second producer. The assertion now
  checks only for join fan-out and drops unjoinable rows with a printed count.
* with today's store the **primary** (harness-only) selection leaves zero testable rows,
  and the tests died on an assertion rather than saying so. They now exit cleanly with
  **NOT TESTABLE plus the coverage count** -- the same answer M5 family A gives for the
  same situation.

All five frozen M4/M5 artifacts reproduce byte-identically through the fixed path,
re-verified after each change. **The commands as written below run.**

```
:: primary -- scope-pure, harness verdicts only
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py  --verdicts all --scopes orbit_reality --sources epoch_vet_harness --out-dir out\dec\primary
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py --verdicts all --scopes orbit_reality --sources epoch_vet_harness --out-dir out\dec\primary

:: regression check -- EB26 alone, MUST reproduce the frozen artifacts byte-identically
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py  --verdicts all --scopes compact_companion --sources elbadry2026 --out-dir out\dec\regression
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py --verdicts all --scopes compact_companion --sources elbadry2026 --out-dir out\dec\regression

:: secondary -- pooled; POSITIVE results only may be interpreted
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py  --verdicts all --out-dir out\dec\pooled
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py --verdicts all --out-dir out\dec\pooled

:: D4 -- the flag decision
.venv\Scripts\python.exe scripts\m6_astrom_quiet_decision.py --verdicts all --scopes orbit_reality
```

---

## 7. What this pre-registration deliberately does **not** cover

Named, so that their absence is a decision rather than an oversight.

1. **The orbital-refit arm's outputs** (M7 task 2). The refit produces an independent
   orbit and a companion-mass posterior; it is a *measurement*, not a hypothesis test, and
   pre-registering a threshold on it would be pre-registering a discovery. Its acceptance
   gate is separately pre-registered in `scripts/orbital_refit_arm.py`'s docstring and was
   passed on 2026-08-23 (Gaia BH3 re-derived to within M1's printed precision).
2. **New discriminator axes.** If December suggests an axis nobody has tested, testing it
   is legitimate and it is a **declared variant** — reported as exploratory, never folded
   into D1–D4's Holm correction retroactively.
3. **The candidate list itself.** Selection, screen, probability method and membership are
   frozen in config v5 (949 + 32) and are not touched by any December analysis.
4. **The 2.4σ offset between the refit arm's Gaia BH3 companion mass and Panuzzo's
   published value.** It is a known, named systematic (the photocentre mass function goes
   as parallax⁻³, and the published headline mass deliberately avoids that route by using
   the RVS-derived `a1`), documented in [`M7-dryrun-refit-prereg.md`](M7-dryrun-refit-prereg.md) §2e. It is not a discriminator question.

---

## 8. Variant log

*Empty on freezing. Later milestones append dated entries here and nowhere else. Each
entry must state: the date, what the variant is, why it was not pre-registered, and that
it is exploratory.*

<!-- BEGIN VARIANT LOG -->
*(no variants declared)*

2026-09-06: [Delegated prospective label/power variant](VARIANT-2026-09-06.md).
The user delegated these local design decisions on September 6. Resolve M8 GAP-1
through GAP-4 in a separate postprocessor, including fixed-pair exact Fisher design
power and a missing-control reporting guard. This was not pre-registered because
the ambiguities and executable edge cases were identified during later synthetic
rehearsals. It is **exploratory**, not the original registration; preserve original
primary outputs, sensitivities, regression, negative-control veto and all frozen
samples/configurations. The historical empty-on-freezing entry above is retained.
<!-- END VARIANT LOG -->
