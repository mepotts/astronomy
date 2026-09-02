# gaia-dr4 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-09-02** — **[M9 readiness](M9-full-chain-a0-readiness.md) independently
  reverified; no M10 opened.** ESA's live
  [release calendar](https://www.cosmos.esa.int/web/gaia/release) still gives **2 December
  2026**. The documented nine-stage `rehearse_dr4_day.py` chain was rerun in the pinned
  venv against the live ESA archive: all nine stages were green in **54 s**. Live schema
  introspection found every required DR3 rehearsal column; the patched query returned its
  five-row probe; all 94 cached range chunks reassembled the exact 169,227-solution input;
  compact-companion controls passed; the epoch harness kept 3/3 controls and demoted 9/9
  contaminants; the day-one queue acceptance passed; and 88 records across two producer
  scopes passed the verdict schema and consumer contract. The rehearsal queue has 983
  pre-dust rows, as documented, versus the frozen 981-row production queue after the
  Phase-2 dust re-triage. `out/rehearsal_timings.csv` records this run. **No DR4 data exist
  yet, no prospective source list was published, and release-day code needs no change.**
  Remaining items are still human/operational: the frozen pre-registration rulings, two
  optional accounts, and excluding `data\\epoch_cache\\` from real-time antivirus before
  release day.

- **2026-08-24** — **M8 done** ([`M8-inflation-zeropoint-rehearsal.md`](M8-inflation-zeropoint-rehearsal.md)):
  M7's three recommendations, in M7's order — measure the inflation factor on a real
  sample, close or bound the parallax zero-point, and *run* the pre-registration.
  **(0) THE LITERAL ASK COULD NOT BE RUN, AND SAYING SO IS THE FIRST RESULT: Gaia DR3
  publishes no stellar epoch astrometry**, so the refit arm's Keplerian half cannot be run
  over hundreds of DR3 sources by anyone before 2026-12-02 — the only epoch astrometry in
  existence is the 12-source pre-release file. **(1) THE INFLATION FACTOR IS ×1.4,
  MEASURED FOUR WAYS, AND M7's ×2.3 WAS NOT AN INFLATION FACTOR AT ALL** (it is a median
  |z|; a standard normal has median |z| = 0.674, so M7's own 11 elements imply **×3.4** on
  the median|z|/0.674 convention used throughout now). Against **SB9** (Pourbaix+2004, CDS
  B/sb9, pulled live — ground-based spectroscopy that shares no photons with Gaia),
  **202 element comparisons from 138 systems** passing a pre-registered same-orbit gate
  give **1.40 [1.31, 1.52]**, with **52 % of elements inside 1 σ against the expected
  68 %** and 85 % inside 2 σ against 95 % — *the coverage test the task asked for*. It
  **rises monotonically with NSS `significance`, 0.88 → 1.33 → 1.37 → 1.83**, which is the
  axis this project selects on; it falls with period (1.74 → 1.01); it is flat in G and
  across solution types. Reweighted to the day-one queue's own significance distribution
  it is **1.19** (SB9's stars are G 8.4, the queue's are G 15.0 — the sample mismatch is
  stated, not hidden). **And the route that settles what M7 could not say: 400
  injection–recovery runs through the arm's own fitter** on real pre-release scan geometry
  return **1.05 [1.03, 1.09]** with a correct noise model and **1.51 [1.47, 1.56]** with
  one unit of unmodelled jitter — **so the Laplace/Hessian error bar is right to 5 % and
  the inflation is model misspecification, not a broken Hessian**. The 98 dual-solution
  DR3 sources give 0.89 over 784 comparisons and are reported as the **lower bound** they
  structurally are (shared photons). Named limit: SB9 constrains **P and e**; the mass
  goes as **a₀³** and a₀ still has no external calibration. **(2) THE ZERO-POINT IS CLOSED,
  AND HALF OF M7's CAVEAT WAS A CONVENTION MISMATCH.** Panuzzo's Letter applies a
  **35.4 µas** Lindegren+2021 correction to BH3's *single-star catalogue* parallax
  (Table 1 footnote b) and explicitly does **not** correct the *NSS orbital* parallaxes
  M7 compared against (Table 2: "we do not have enough information at this stage to
  quantify the bias") — so the zero-point cancelled in M7's difference. This
  implementation reproduces their 35.4 µas to **0.006 µas**, matches El-Badry+2026's own
  applied L21 shifts on eight published pairs to a median **2.0 µas**, and rests on EB26's
  direct measurement of the zero-point **for astrometric orbital solutions**
  (**Z = −0.0362 ± 0.0053 mas** vs the L21 median −0.0342, their conclusion: the
  single-star correction "can and should be applied to binary solutions as well").
  **Applying it moves Gaia BH3 from M₂ 34.68 to 32.64 M☉ and the offset from Panuzzo's
  published 32.70 ± 0.82 from +2.42 σ to −0.07 σ — the 2.4 σ CLOSES** — and the corrected
  refit parallax lands on Panuzzo's **zero-point-free** a₀/a₁ parallax (1.6933 ± 0.0164)
  to **+1.9 µas = +0.11 σ**, where the raw one sat **1.90 σ** away. That is a prediction
  that could have failed. Across the 981-row queue the correction moves the median
  companion mass **−1.95 %**, the worst −11.9 %, and it is **distance-dependent**
  (−9.9 % inside 0.5 mas, −0.9 % beyond 5 mas) — so it grows in DR4, exactly as EB26
  forecast. **The M₁-free mass function moves far more — median −4.1 %, worst −33.7 % —
  and six of the ten highest-M₂_min candidates have no M₁ point mass, so f_M is all there
  is to quote for them: their shifts reach −30.6 %.** "About 2 %" is true of the median
  companion and badly wrong about the objects anyone looks at first. **Residual bounded three ways at ≤ 2 µas ⇒ ≤ 0.4 % of a companion mass at
  1.7 mas**: after correction the zero-point is no longer the dominant systematic; the
  ×1.4 inflation is. Wired into the arm as **`--zeropoint`** (default off so M7's frozen
  acceptance reproduces byte-identically; **mandatory for December**), applied to the
  posterior draws as well as the point estimate. **(3) THE PRE-REGISTRATION HAS NOW BEEN
  RUN — **55 command runs, 0 non-zero exits, 77 labels, every targeted expectation met and the frozen EB26 regression byte-identical**** — against **eleven synthetic verdict stores at
  December's projected sample sizes** (633+347, 490+490, 245+735), built on the **real**
  981 queue ids under **declared** nulls and declared effects whose *realised* values are
  recorded (D2 AUC 0.6573 for a target 0.659; D3 0.3440 for 0.344; D1 0.1512 vs 0.0000 for
  0.154 vs 0.000; D4 0.2993/0.0758 for 0.30/0.075), written to `out/verdicts_synth/` and
  **never** into `out/verdicts/` because the December command is `--verdicts all`.
  **Three CODE defects, and the first would have fired on the day: the pre-registered D4
  command does not parse** — `m6_astrom_quiet_decision.py` had no `--scopes`, so it exits 2
  with `unrecognized arguments`, and M7's "the commands as written below run" was true only
  for the four commands M7 actually typed; **`m5_activity_discriminator.py` CRASHES at
  December's sample size** (`TypeError: … no callable log10 method` — the confound guard
  only runs for a metric that discriminates, and at 633+347 a *binary* metric reaches it
  for the first time; `np.clip` on a boolean Series returns object dtype), killing both
  the primary and the pooled run after most of the output; and M7 landmine #14's **third**
  occurrence (m6 announced `out/…` regardless of `--out-dir`). **Four GAPS in the frozen
  registration, reported and not patched**: §5's six labels are **not exhaustive**
  (significant + right direction + not decisive has no label), §5 and §2.2 **disagree**
  (a pooled non-significant result must be reported as "pooled: uninterpretable", which is
  not one of the six), a **pooled significant reversal** is covered by neither, and
  **DECISIVE is ill-defined for the rate tests** when the observed baseline differs from
  the pre-registered one — **and GAP-4 is not cosmetic: it fired 11 times, every time with
  the literal reading saying NOT DECISIVE and the difference reading saying DECISIVE, so
  under the literal rule D4 reads UNDERPOWERED in all three null scenarios where it should
  read NULL. Which sentence of §4 December reads decides whether it can claim a D4 null.**
  **The rehearsal also proves the registration's central promise executes: at all three
  projected ratios the smallest detectable AUC is 0.575 against effects under test of
  0.659 and 0.656, so a non-significant D1/D2/D3 comes back **NULL** — 17 times across the
  run — and not UNDERPOWERED.** `scripts/m8_prereg_labels.py` is §5+§2.2 as one **total,
  deterministic** function — its selftest reaches all six labels, all three
  beyond-the-six cases and the negative-control veto (which no consumer implemented) — and
  the amendments are written up **for Matthew**, never applied. **Also measured, and it
  changes how a December positive is written up: D1 and D2 are NOT independent axes** —
  on the queue's own 489 in-footprint rows the 30 X-ray detections are more photometrically
  variable at **AUC 0.873, p = 7.4×10⁻¹²**, so two positives would be one finding reported
  twice. **(4) runbook + config v6 + rehearsal**: the runbook changed in six places (apply
  the zero-point, inflate by ×1.4, assign the labels *in code*, three new failure branches,
  and a **DR4-specific STOP** — L21 is an EDR3/DR3 calibration and the residual bound is
  unverified for DR4); the rename map
  gains the five zero-point input columns — and reading the DR4 **draft data model** to
  check them turned up a column this repo did not know existed: **`tentative_parallax_bias`
  in both `gaia_source` and `all_source_astrometry`** (draft pp. 20, 74), *"the parallax
  bias correction … to be subtracted from `parallax`"* — **DR4 ships its own zero-point,
  on L21's convention, so December prefers it and keeps L21 as the cross-check**; the same
  read confirms `nu_eff_used_in_astrometry` / `pseudocolour` / `ecl_lat` survive but
  **`astrometric_params_solved` becomes `astrometric_params`**, and that column is the
  31/95 guard that makes `zpt.get_zpt` **raise** rather than return NaN if it is wrong; and
  **config v6** — the first bump since v5 and the first that carries a decision — records
  `parallax_zeropoint_policy`, `error_inflation_policy`, `discriminator_axis_independence`
  and `prereg_execution`, with **selection, screen, probability method and membership
  identical to v2–v5 (949)** and acceptance re-checked (BH1+BH2 top-2 by M₂_min; EB26
  operating point 39/42 + 7/23). **Full nine-stage rehearsal re-run: ALL GREEN in 56 s**,
  plan-B pull **byte-identical for the SIXTH time** (sha256 b3b099a6…dddd5231), stage F
  3/3 kept + 9/9 demoted at max |Δf2| 0.0050, and the five frozen M4/M5 artifacts
  reproduce **byte-identically** through every consumer change. New landmines:
  **a frozen M7 artifact (`out/m7_refit_acceptance.json`) still contains the rounded,
  non-existent DR3 source id** that M7's own landmine #4 describes — fixing the code does
  not fix the artifacts the bug already wrote; **`DataFrame.iterrows()` is the same 2⁵³
  trap** as `.iloc[0].to_dict()`; **two `--out-dir` leaks in one file** wrote over frozen
  artifacts (caught by hashing and by `git status` at close); **a zero-point applied to the
  point estimate but not the posterior** ships a corrected mass inside an uncorrected
  interval; **latent bugs live behind significance gates** — a guard that only runs for
  metrics that discriminate is a code path that only executes at scale; a **synthetic
  control that does not change what the test reads is worse than none** (the first
  `no_coverage` store blanked a column the test never consults, and was caught only
  because its numbers came out byte-identical to the null store); and — the one that eats
  the result — **the pre-registered label `NULL` is pandas' default NA token**, so
  `read_csv` on December's own label file turns all 17 nulls into `NaN` and
  `value_counts()` reports zero of them. Human TODOs unchanged (accounts).
- **2026-08-23** — **M7 done** ([`M7-dryrun-refit-prereg.md`](M7-dryrun-refit-prereg.md)):
  M6's three recommendations, in M6's order — the clock is a number, the headline arm is a
  pipeline, and December is pre-registered. **(1) THE CLOCK HAS A MEASURED CENTRE, and the
  half of M6's band that a better experiment could remove is removed: M6's models A and B
  were never rivals — they are the two terms of one cost model**, and
  the probe that could not separate them was collinear by construction. A **981-source dry
  run through the production harness** (`scripts/m7_day1_dryrun.py`, DR3
  `EPOCH_PHOTOMETRY`) at a *fixed* batch 20 with payload deliberately varied **4.7×**
  across batches (48 of 50 batches serving exactly 20 sources; batch time then varies
  **6.0×** where a flat model predicts 1.0×, and correlates 0.83 with served transits
  against 0.26 with source count) separates them: **`t = 2.42 ±0.81 s + 0.215 ±0.100 s/source × n + 0.1424
  ±0.0105 s/KiB × KiB`** (100 requests, R² 0.878; per-byte term **13.5 σ**, per-source
  2.2 σ; at fixed n the flat model explains **R² 0.000**). At DR4's real 50.9 KiB/source
  the bytes cost 7.25 s/source against the source term's 0.22 s ⇒ **468 sources/hour, the
  981-row queue in 2.1 h — a measured central value where M6 had none**. A band remains,
  126–803/hour (1.2–7.8 h), and the width is honestly similar to M6's; what changed is
  what the width *means*. M6's was a model ambiguity with no defensible centre, spanned by
  two extrapolations neither of which had been observed; **M7's is archive weather, every
  edge of it is an archive state somebody measured, and a SUSTAINED run varies by only
  ±8 %** (the two halves of phase B, 2,626 and 2,236 sources/hour) because a 50-batch
  wall clock averages single-request extremes away. The half of the uncertainty a better
  experiment could remove has been removed; the half only release day can settle has not.
  **M6's 78-h worst branch is superseded: the same 10× degradation now costs 20.2 h**, so
  every branch fits inside 72 h. Also measured, and each one corrects M6: the empty-request
  overhead is **0.65 s** (14 requests that served nothing), not 2.3–6.0 s; **only 74 of the
  981 queue members (7.5 %) have DR3 epoch photometry at all**, which is why a
  payload-stratified control set had to be built; **resume was exercised at real scale**
  (stopped at 400, restarted, `581 to do`, picked up at batch 20 of 50); the fit half
  sustained **981 consecutive fits at 0.123 s** with drift −0.011 s/1000 and f2
  bit-identical on repeats; and archive weather over **60 requests spanning 2.0 h** spans
  2.8× (median 26.9 s, p90 34.3 s) with **0 failures** and no monotone trend. **(2) THE ORBITAL-REFIT ARM
  EXISTS** (`scripts/orbital_refit_arm.py`): epoch astrometry → Keplerian orbit → M₁-free
  mass function → **companion-mass posterior** (Laplace, from kepmodel's log-likelihood
  Hessian, 20,000 draws), M₁ taken from the *triage's own three-tier ladder* with the rung
  recorded, output as **verdict-record v2** (`scripts/verdict_schema_v2.py`, 74 cols =
  v1's 39 + 35 `refit_*`; v1 untouched, every v1 record valid v2 after `upgrade()`, round
  trip verified on the frozen EB26 store). **Pre-registered acceptance PASS**: Gaia BH3
  re-derived to **P 11.45429 yr, e 0.727816, M₂ 34.68425 M☉** — inside M1's *printed*
  precision on all three (|Δ| 0.00029 / 0.000016 / 0.00425) — plus the posterior M1 never
  had, 68 % [34.20, 35.17]. On the trio: **BH3 every Campbell element within 1.1 σ of
  Panuzzo's astrometric solution** (and BH3 has **no DR3 NSS row at all**, which is why
  the Letter needed preliminary DR4 astrometry); **HD 114762 M₂ 0.2334 [0.2205, 0.2456]
  lands 1.5 σ from Winn 2022's 0.215 ± 0.013 and excludes Kiefer's 0.10–0.14 at 7–10 σ
  (3.2–4.5 σ even after inflating the formal error by the measured ×2.3)**; **Gaia-4 10.8
  M_Jup vs Stefánsson 2025's 11.8 ± 0.7**, with the `binary_masses` M₁ rung reproducing
  their EXOFASTv2 host mass to −0.20 σ. **Two measured caveats now ride with every mass:
  the formal errors are lower bounds by a median factor 2.3** (11 elements vs published;
  only 4 of 11 inside 1 σ), and **all three refit parallaxes ran 5–41 µas LOW** — the
  mass function goes as ϖ⁻³, which *is* the arm's +2.4 σ offset from Panuzzo's published
  M_BH, and Panuzzo avoided the same trap by taking the headline mass from the combined
  astrometry+RVS solution via `a1`. **(3) DECEMBER IS PRE-REGISTERED AND FROZEN**
  ([`PREREG-2026-08-23-december-discriminators.md`](PREREG-2026-08-23-december-discriminators.md)):
  **primary analyses are scope-pure** (harness verdicts alone; the EB26-only run is a
  byte-identity regression check, not evidence), and **a pooled analysis is interpretable
  in one direction only** — pooled significance is a conservative positive because
  dilution biases toward the null, pooled non-significance may never be reported as a
  null. Each test then gets one of **six pre-assigned labels** (POSITIVE / POSITIVE
  (conservative, pooled) / **NULL** / UNDERPOWERED / DIRECTION REVERSAL / NOT TESTABLE)
  where NULL
  requires the test to be *decisive*. Holm family sizes fixed now (D1 3, D2 5, D3 6,
  D4 1), directions fixed, `INCONCLUSIVE` never folded into `SPURIOUS`, and the negative
  control `phot_g_n_obs` given a **veto**. Thresholds computed by importing **M5's own
  power routines** (`scripts/m7_prereg_power.py`; a fresh implementation reproduced M5's
  published column only to ~2 %): at the EB26 ratio **D2 needs 71+39, D3 73+40 (at M6's
  weaker *in-list* AUC 0.344, the binding one), D4 64+35, D1 49+27 in-footprint** — and
  one harness pass gives ~633+347. **So a non-significant December result on D2/D3/D4 is
  a NULL, the outcome this project has never been able to claim; D1 alone stays
  footprint-capped.** **(4) runbook + rehearsal**: the measured clock, a new **§3.4 = the
  refit arm** with both caveats, §3.3 rewritten to STOP-and-read the pre-registration with
  the three-way primary/regression/pooled command set, five new failure branches — and
  **running those commands found the runbook's own December command was broken**: both
  discriminator tests hard-coded `== 76` on the verdict join, so `--verdicts all` raised
  the moment the store held a second producer and the *pooled* half of "run each twice"
  would have died on the day. Both now assert only no-fan-out and drop unjoinable rows
  with a printed count; **all five frozen M4/M5 artifacts still reproduce
  BYTE-IDENTICALLY** through the fixed path, and the pooled run works (10 of 88 rows
  dropped, scope composition printed). **Full rehearsal re-run after every change: all
  nine stages OK (358 s, then 722 s on a re-run after the consumer fixes — the difference is ESAC weather, stage A alone 128 s then 292 s)**, stage F 3/3 kept + 9/9 demoted at max |Δf2| 0.0050 through
  the refactored fetch layer, plan-B pull **byte-identical for the FIFTH time**
  (sha256 b3b099a6…dddd5231, 169,227 rows); stage A took 128 s because **ESAC's
  `TAP_SCHEMA` path was unusable again** and failed over to ARI, exactly as M5's branch
  prescribes.
  **No config written — M7 moved nothing about the list, and a version bump that carries
  no decision is noise.** New landmines: **`DataFrame.iloc[0].to_dict()` rounds
  `source_id` past 2^53** (BH3's DR3 id came back as a source that does not exist — the
  pandas twin of M2's ADQL landmine); **Newton diverges on the mass-function cubic** from
  its natural starting guess and returned M₂ = 1e−9 for BH3, caught only by the
  cross-check against `pystrometry.pjGet_m2`; the astronomical mass function and
  pystrometry's SI chain differ by 1e−4; **`min_detectable_rate` takes the fixed-rate
  group first** (0.60 vs M6's published 0.55, caught only by the reproduction block); and
  a CSV appender that does not align columns corrupts silently. Human TODOs unchanged
  (accounts) — but at 468 sources/hour a logged-in quota now buys **depth beyond the
  queue**, not the queue itself.
- **2026-08-21** — **M6 done** ([`M6-verdict-harness.md`](M6-verdict-harness.md)):
  the verdict *factory* exists, the record it emits is frozen, and the day-one clock is
  measured instead of assumed. **(1) the production epoch-vet harness**
  (`scripts/epoch_vet_harness.py`): batched DataLink (RAW, one request per batch —
  `gaiasupdate`'s own helper sends **one id per request**), per-source atomic parquet
  cache + append-only verdict ledger (**resume demonstrated**: 5 sources then 7 over the
  same ledger, 12 records, acceptance PASS), 6× retry with `Retry-After` honoured, and
  timings written every run. **Measured: the `gaiasupdate` single-star fit costs
  0.036 s/source steady state (~100,000/hour, 22 fits over two runs) and is NOT the
  bottleneck; DataLink is, at 3.9 s/source.**
  **Projected day-one throughput at batch 20: a BAND of 125–857 sources/hour ⇒ the
  983-row queue in 1.1–7.9 h** (78 h on the 10×-degraded branch — the only branch that
  misses 72 h). The band is two models fitted to the same calls (per-source server work
  vs per-byte transport) because **the DataLink service is server-work-limited, not
  bandwidth-limited (~1.8 KiB/s effective)** and DR4's real payload (50.9 KiB/source
  zipped, measured on the pre-release file) is 6.8× the DR3 proxy's. A 5-request soak
  spanned **3.2× with no monotone rise — archive LOAD, not throttling**, so the answer to
  a slow DataLink is patience plus the resumable cache, and any single-call timing is
  worthless for planning. Because the queue is ranked, a slow archive costs **depth, not
  the headline**. **(2) the day-one verdict record** (`schemas/day1_verdict_record.v1.json`
  + `scripts/verdict_schema.py`): identity / orbit provenance / fit statistics / verdict +
  confidence / seven caution flags / provenance-versioning, with a mandatory
  **`verdict_scope`** — EB26 answers `compact_companion`, the harness answers
  `orbit_reality`, a harness SPURIOUS ≈ an EB26 SPURIOUS but **a harness CONFIRMED is
  WEAKER than an EB26 CONFIRMED**, so pooling is asymmetric and every consumer prints the
  scope composition the moment the store holds more than one producer. **(3) consumers
  rewired and verified**: M4 and M5 read verdicts from the store, and **all five frozen
  artifacts reproduce BYTE-IDENTICALLY** (`out/m6_refactor_check/SHA256SUMS.txt`) — M4
  2/13 vs 0/16 at Fisher p 0.1921; M5 family A 7/76 NOT TESTABLE, family B AUC 0.659 →
  Holm 0.1409, family C `astrometric_gof_al` Holm 0.0067. **(4) end-to-end validation**:
  the harness reproduces M3's prototype through the production path — 3/3 kept
  (BH3 893.97, HD 114762 186.50, Gaia-4 31.53), 9/9 demoted, all HIGH confidence, max
  |Δf2| **0.005** = the prototype's own 2-dp rounding. **(5) `flag_astrom_quiet`: CARRY,
  and now for a measured reason.** M5 measured it on all 65 verdicts; the flag operates on
  the *queue*, where the screen leaves 48 verdicted rows (40 conf / 8 spur — M5's 46/2/
  0-of-7 reproduce exactly as the main-bin subset). There the metric gives AUC 0.344
  (p 0.17) against a smallest-detectable AUC of **0.80**, and the thresholded flag gives
  Fisher p 1.000 against a smallest-detectable spurious marking-rate of **0.55**. **M5's
  "0 of 7" was never evidence of failure: at the measured 7.5 % marking rate the expected
  catch among 8 spurious rows is 0.60.** Decision rule for December pre-registered
  (KEEP/REMOVE/CARRY) and in the config; one harness pass takes the in-list verdict count
  from 48 to O(981), which clears both required sample sizes (80+16, or 160+32).
  **(6) acceptance PASS on all four gates** (BH1/BH2 top-2 at Pr 1.0000; EB26 operating
  point 39/42 + 7/23 **read through the store**; schema validation; harness end-to-end)
  gating **config v5** — selection/screen/membership identical to v2/v3/v4 (949), adding
  `verdict_schema`, `epoch_vet_policy` and the flag decision. **(7) runbook + rehearsal**:
  Phase 3 rewritten as a first-class harness phase with a new **Phase 3.0** and six
  measured failure branches; driver **stage F now runs the production harness** and
  **new stage I** builds + validates the verdict store; **full rehearsal re-run, all 9
  stages, COMPLETE in 82 s**, plan-B pull **byte-identical for the fourth time**
  (sha256 b3b099a6…dddd5231, 169,227 rows) — but the 82 s is archive weather, not a
  speedup (M5's 1,150 s was ESAC's worst afternoon; stage A 179 → 7.3 s, B 291 → 4.0 s,
  while stage D ranged 59.0 / 89.6 / 104.2 s across three runs today purely on CPU
  contention). What the rehearsal certifies is the nine statuses, and all nine are green.
  **New landmine, and it is the day-one one: DataLink returns
  HTTP 500 "Unknown retrieval type: 'EPOCH_ASTROMETRY'"** for both `Gaia DR4` and
  `Gaia DR4_INT4` today, while **astroquery 0.4.11 accepts the type client-side** — a
  deterministic rejection dressed as a transient failure. The harness now reads the error
  *body* and fails fast; the runbook makes a one-source DataLink probe a hard gate before
  the harness starts. Human TODOs unchanged (accounts) — but a logged-in DataLink quota is
  now a measured lever, not a hypothetical one.
- **2026-08-18** — **M5 done** ([`M5-activity-axis.md`](M5-activity-axis.md)):
  **(1) the activity axis with the footprint penalty removed — 65 of 65 verdicts
  instead of M4's 29** (rules pre-registered in
  `scripts/m5_activity_discriminator.py`; three families, Holm within each; negative
  control `phot_g_n_obs` clean at p = 0.14). **A — chromospheric `activityindex_espcs`:
  NOT TESTABLE, and that refutes M4's own premise** — it exists for **7 of 76** EB26
  targets (3 confirmed / 1 spurious) and 44 of 1,199 candidates; the ESP-CS module ran
  on 431 and published a value for ~10 % of them. **B — photometric variability
  (Belokurov+2017 eq. 2 amplitude, magnitude-detrended): UNDERPOWERED NULL** — ΔAmp_G
  AUC(spur>conf) 0.659 [0.507–0.805], p 0.035 → **Holm 0.141**, against a
  smallest-detectable AUC of **0.725**; direction (spurious = more variable) **agrees
  with M4's X-ray direction** — two activity axes, two consistent directions, neither
  significant; it needs ≈ 2× the sample (**84 + 46**). **C — astrometric quality (not
  activity): WORKS, and points the OTHER way** — `astrometric_gof_al` p 0.0011 (Holm
  0.0067, AUC 0.254) and `ruwe` p 0.0083 (Holm 0.041): **EB26-CONFIRMED hosts are the
  NOISIER single-star fits** (the measured version of `ruwe_cut = NONE` since v1). Passes
  the pre-registered G-stratified guard; two measured post-hoc caveats carried in the
  config — controlling for `significance`/G/d it retains only p 0.048, and on the 46
  verdicted rows that survive the screen it flags 2 and catches **0 of 7** in-list
  spurious. **One flag frozen, tiebreaker only: `flag_astrom_quiet`** (bottom quartile of
  `astrometric_gof_al` in the day's own main bin). **(2) southern dust CLOSED** with
  Vergely+2022 (CDS J/A+A/664/A174, anonymous FTP; A₀(550 nm) unit chain sourced to the
  paper + FITS headers; **pre-registered geometry gate**: declared axes ρ 0.966 vs
  0.38–0.41 for the three corruptions, E_V22/E_Eden 1.010, 25/50 pc cubes 0.977): **all 4
  southern rows SURVIVE class III on both chains, V22 reproduces Bayestar19 9/9 at the
  central value, 12 of 13 clean, 1 σ-fragile (rank 27, M₂_min 2.30 — flagged, not
  frozen), 0 die → 0 movements, the v2 list (949) stands.** `flag_dust_unresolved_south`
  4 → **0**. **(3) acceptance re-run PASS** (BH1/BH2 Pr 1.0000 top-2; EB26 operating
  point 39/42 + 7/23 identical) gating **config v4** (selection/membership identical to
  v2/v3; adds the all-sky extinction arbitration, the measured activity policy — *no*
  activity flag — and the astrometric flag with both caveats inside the config).
  **(4) queue folded into the driver**: shared builder `scripts/m5_day1_queue.py`,
  rehearsal **stage H**, production copy `out/epoch_vet_day1_queue.v2.csv` (981 rows;
  M4's file untouched); the builder asserts BH1/BH2 itself. **Rehearsal re-run
  end-to-end and still green — all 8 stages OK in 1,150 s**, acceptance PASS, and the
  plan-B pull came back **byte-identical for the third time** (sha256 b3b099a6…dddd5231,
  169,227 rows) — stage C resumed from its 94 cached chunks, which the timings CSV now
  says out loud in a new `note` column; the driver also takes `--stages` so a partial run
  is recorded as SKIPPED-with-reason and cannot be mistaken for a green one.
  **New landmine, and it is
  the operational one: the ESAC TAP endpoint was effectively down for hours** (HTTP 500
  and 90 s read-timeouts on one-row indexed queries) while the **ARI and AIP DR3 mirrors
  answered in 0.6–2 s** — ARI reproduced ESAC to 0.000e+00 under a new mirror-validation
  gate; every sync helper now retries 4× with backoff; the mirrors have DR3, **not DR4**,
  so December's only defences are the retry and the resumable pull. Human TODOs
  unchanged (accounts).
- **2026-08-18** — **M4 done** ([`M4-xray-discriminator.md`](M4-xray-discriminator.md)):
  **(1) the activity-vs-spuriousness test** — all 76 EB26 targets × eROSITA-DE DR2+DR1
  with shifted controls (rules pre-registered): in-footprint detections **2/13 SPURIOUS
  vs 0/16 CONFIRMED** (+0/7 other verdicts; chance 0.12), both real counterparts
  (p_any ≥ 0.98), both coronal-soft, 0 hard-band, 0 accretors, 0 DR1-only faders —
  direction consistent with M3's n=1 (which reproduces as the loudest), but Fisher
  **p = 0.19: UNDERPOWERED** (only a spurious rate ≥ 0.40 was detectable at 80 % power
  on the half-sky footprint; observed 0.154). **No X-ray flag enters the config**; the
  hypothetical cut measured and rejected (drops 30 rows: 0 confirmed, 1 spurious, 29
  unverdicted). Bonus: the 2nd X-ray spurious (6281…) is class III but already killed by
  the frozen F2 screen — gate and tag agree. **(2) dust dozen** — the Bayestar19 chain
  M3 refused to guess is now paper-exact (Green19 line 399 + table: 1 unit =
  E(gP1−rP1) 0.901 = **1.000 × E(B−V)_SFD** by construction, SF11 Table 6 PS1 g−r;
  → 2.742 → ZGR23 ratios; EB26's 2.66/1.33 chain run in parallel): of the **13** (not
  12 — M3 count corrected, the 13th is a dust mover-in) ambiguous rows, **9 SURVIVE
  under both chains** (B19 ≈ Edenhofer floor ≪ SFD: the SFD ceiling was mostly
  background dust), 4 are south of the B19 footprint (stay bracketed + flagged),
  **0 movements → the v2 list stands, no v3 CSV**. Argonaut web API is DEAD (HTTP 500
  both formats) — local bayestar2019.h5 (0.73 GB, md5-pinned) + healpy-free reader.
  **(3) acceptance re-run PASS** (BH1/BH2 Pr 1.0000, top-2; EB26 operating point
  re-measured 39/42 + 7/23 identical) gating **config v3** (selection/membership
  identical to v2; adds `bayestar19_chain` + `xray_policy` caution-tag). **(4) day-one
  queue built**: `out/epoch_vet_day1_queue.csv` — 981 rows (949 v2 + retrieval bin's 32
  at Pr ≥ 0.999, incl. 4 never-vetted Pr = 1.0000 objects at M₂_min 2.9–3.6), all
  caution flags; runbook updated (v3 config, B19 arbitration step, queue pointer, M4
  baselines in the 24-h bulletin). M3's "retrieval bin headed by the probable-NS"
  corrected: it rides at rank 276; four bin members outrank it at Pr 1.0000. Human
  TODOs unchanged (accounts).
- **2026-08-16** — **M3 done** ([`M3-corrvec-rehearsal.md`](M3-corrvec-rehearsal.md)):
  the two M2 seams are closed and December 2 is rehearsed. **(1) corr_vec**: `nsstools`
  0.1.12 (PyPI, verified) rebuilds the full NSS covariance; validation vs S23's e_A goes
  from 2.27× overestimate to **median ratio 1.027** (the residual fat tail is confined to
  TI-degenerate solutions, marker = S23's own σ_TI² — the candidate list lives at median
  0.95, i.e. in the validated regime); the 951's **Pr≥99.9 % core doubles 147 → 293**,
  **0 dissolve** below 50 %, the retrieval bin yields 32 more at ≥ 99.9 % (headed by the
  EB26 probable-NS at 0.9997), BH1/BH2 = 1.0000/1.0000 — and a clean negative: **Pr
  thresholds don't improve the EB26 operating point** (precise wrong orbits have Pr ≈ 1;
  the frozen screen stands, Pr is a ranking tier in config **v2**, v1 untouched).
  **(2) dust tier**: Edenhofer23 3D (≤ 1.25 kpc, all-sky, healpy-free reader) + far-star
  Edenhofer-floor/SFD bracketing (Bayestar rejected: unsourced Gaia-band chain; the 12
  dust-ambiguous rows are counted instead); only 91 of the 270 flagged are even movable
  (179 are binary_masses-tier) — **8 out / 6 in** at best estimate → **v2 list = 949**
  (one knife-edge entrant honestly at Pr 0.495); top-3 unchanged (BH1 12.81, BH2 9.76,
  then the EB26-refuted spurious at Pr 1.0000 — still the epoch-vet poster child).
  **(3) rehearsal**: schema-pin → rename-patch (live-probed) → plan-B ranged pull re-run
  in full (38.7 min, **byte-identical sha256 to the M2 production pull**; the raw ranges
  over-count by exactly the histogram wobble + the bm fan-out and the guard chain
  assembles 169,227 on the nose) → triage acceptance **PASS** (BH1+BH2, 65 s) →
  epoch-vet **PASS** (3/3 keep, 9/9 demote) → bulletin; **40 min end-to-end**, timings in
  `out/rehearsal_timings.csv`; the operational playbook is **`DR4-DAY-RUNBOOK.md`**.
  **(4) eROSITA join** (471 of 949 in-footprint): **30 X-ray counterparts vs 1.38
  chance** (8 shifted controls), 0 hard-band, all in the coronal f_X/f_opt locus
  (−4.3…−1.2) — **no accretor found** down to a median L_X reach 3.8×10²⁹ erg/s; the
  X-ray-loudest-relative match is the EB26-refuted 1-yr-alias spurious (p_any 0.9995):
  on this sample X-ray = activity/spurious-risk tag, not compact-companion evidence.
  New landmines: VOTable `SOURCE_ID` upper-casing; duplicate `GDR3_source_id` column in
  eRASSc3; dustmaps' wrong ZGR23-curve DOI; sfdmap2's silent 0.86 rescale; healpy has no
  Windows build. Human TODOs unchanged (accounts).
- **2026-08-16** — **M2 done** ([`M2-amrf-triage.md`](M2-amrf-triage.md)): the AMRF triage
  exists, is validated, and its DR4 config is frozen (`queries/dr4-triage-config.json`).
  **Acceptance PASS on the first end-to-end run**: BH1 class III (𝒜 = 2.265, margin 3.38×,
  M₂_min = 12.81 M☉), BH2 class III via the evolved-primary bracket (worst-case margin
  2.44×, M₂_min ≥ 9.76) — the two designed-around landmines were S23's P < 1000 d cut
  (BH2 is at 1352 d) and MS-only M₁ (BH2's primary is a giant **and has no binary_masses
  row**). Implementation = S23 digit-for-digit (𝒜 ratio 1.0000 on every shared source;
  177/177 of their class-III recovered at the frozen boundary). Calibration vs El-Badry
  2026's follow-up verdicts (42 confirmed / 23 spurious): frozen config keeps **39/42
  (92.9%)** and passes **7/23 (30.4%)** spurious; the strictest screen (significance > 20)
  would have rejected **Gaia BH1 itself** (sig 13.6) — frozen at 10 with the tradeoff
  table on record. DR3-wide yield: **951 class-III solutions** (147 also at MC
  Pr(III) ≥ 99.9% — the S23-comparable core; 270 low-|b| extinction-flagged) + a 239-row
  low-significance retrieval bin; ranked by M₂_min the list's top two are BH1 and BH2, and
  #3 is a known EB26-refuted spurious at significance 76 — the epoch-vet loop's poster
  child. Stretch PASS: the epoch-vetting loop on the pre-release file keeps exactly the
  3 orbit sources (f2 894/187/32) and demotes all 9 quiet ones — the DR4-day
  false-positive killer works end-to-end. **M1 correction**: the "BH3 renumbered DR3→DR4"
  claim is REFUTED (Panuzzo prints `...000`; all 12 pre-release ids are unchanged DR3 ids;
  crosswalk stays as insurance). New landmines: **source_id is a key in neither
  `nss_two_body_orbit` (98 sources carry two astrometric solutions) nor `binary_masses`
  (join fans out +76)**, and ADQL bucket arithmetic on source_id rounds in double
  precision past 2^53. Operational: the anonymous async queue sat >100 min on two jobs;
  the range-partitioned sync fallback (`scripts/pull_dr3_nss_orbits_ranged.py`: 3-s bucket
  histogram + 94 indexed range pulls, exact-count-guarded) delivered the 169,227-row pull
  in ~35 min — assume the queue is worse on 2026-12-02. Human TODOs unchanged (accounts).
- **2026-08-14** — **M1 done** ([`M1-prerelease.md`](M1-prerelease.md)): all four pre-release
  claims CONFIRMED (release 2026-12-02; 12-source epoch-astrometry sample of 2026-06-26; official
  package = `gaiasupdate` 0.1.2 on PyPI; draft data model = 1231-pp PDF). ESA tooling runs
  end-to-end on Windows: 12/12 single-star fits, and the BH3 orbital refit reproduces the
  published orbit (P 11.45 vs 11.6 yr, e 0.728 vs 0.729, M2 34.7 vs 32.70±0.82 M☉) —
  `out/*.png`. Three day-one ADQL queries drafted in `queries/` and their DR3 twins validated on
  anonymous TAP (all HTTP 200); rename map in `queries/dr3-to-dr4-tables.md`. W2 fixtures pulled:
  BH1/BH2 DR3 NSS + gaia_source rows in `fixtures/`. Landmines found: DR4 `epoch_astrometry` is
  **DataLink-only** (no TAP joins), and **source_ids are not stable DR3→DR4** (BH3 renumbered in
  the pre-release file) — resolve via `dr3_neighbourhood`. Next: M2 = AMRF triage, acceptance =
  recover BH1+BH2 (note BH2 is `AstroSpectroSB1`, not `Orbital`). Human TODOs still open:
  Gaia Archive + Data Lab accounts (Matthew).
- **2026-08-14** — Folder created from run-3 avenue #4. First agent launched: W1 (verify +
  install pre-release sample and official fitting package, run a demo fit) and W3 (draft the
  day-one ADQL, syntax-validated on DR3 via anonymous TAP). W2 acceptance target on record:
  recover Gaia BH1/BH2 from DR3 NSS before December. Human TODOs open: Gaia Archive +
  Data Lab accounts (see README).
