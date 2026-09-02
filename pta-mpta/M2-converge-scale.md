# M2 — converge J1909-3744, scale the noise campaign to the top-10, factorised-likelihood CURN slice

*2026-08-18. Second milestone of avenue #2. Repo law: every externally-sourced number carries its
source URL or the mark UNSOURCED; negative results are results; blockers are findings.
Foundation: [`M1-access-reproduction.md`](M1-access-reproduction.md) — the sudo-free PINT/enterprise
stack, A1 PASS on both anchors, J2241-5236 5/5, J1909-3744 5/9 with the diagnosed sampler shortfall
(our own likelihood scores the published solution ΔlnL = +22.4 above the best point M1's chain
visited).*

---

## 1. Pre-registration (written 2026-08-18, BEFORE any M2 sampling)

### 1.1 Target selection: "top-10 best-timed"

Rule, fixed before sampling: rank the 83 released pulsars by the in-release tempo2 `TRES` value in
their par files (weighted RMS, µs — the release's own ground truth, measured in M1's A1), take the
10 lowest. Measured ranking (par `TRES` µs / shipped ToAs):

| # | Pulsar | TRES | ToAs | # | Pulsar | TRES | ToAs |
|---|---|---|---|---|---|---|---|
| 1 | J1713+0747 | 0.165 | 1,273 | 6 | J0125-2327 | 0.654 | 3,170 |
| 2 | J2241-5236 | 0.167 | 3,405 | 7 | J1946-5403 | 0.705 | 1,815 |
| 3 | J0437-4715 | 0.234 | 3,517 | 8 | J1600-3053 | 0.851 | 6,200 |
| 4 | J1909-3744 | 0.257 | 7,199 | 9 | J1017-7156 | 0.910 | 3,321 |
| 5 | J1744-1134 | 0.397 | 2,957 | 10 | J2129-5721 | 0.961 | 3,039 |

This set deliberately includes the model-fragile cases M1 deferred (J0437's free-β chromatic noise;
J1017's and J1600's chromatic Gaussian events; J2129's annual chromatic variation) — scaling to
them is the point of M2.

### 1.2 Per-pulsar models (favoured models transcribed from the published tables)

Source: arXiv:2412.01148 LaTeX source (retrieved 2026-08-16, preserved locally), Tables
"MPTA noise models" and "MPTA determinstic models" [sic]. Solar-wind model classes per the paper's
§Solar-wind models: **SW_Full** = deterministic n_earth + SW GP, both sampled; **SW_Det** =
n_earth sampled, no SW GP; **SW_Fixed** = deterministic solar wind held at n_earth = 4 cm⁻³
(the tempo2 default the paper cites), nothing sampled. A "4" without CI in the table's n_⊕ or β
column denotes the fixed value; every model also carries the fixed-γ=13/3 free-amplitude
achromatic term (paper §Codified bayesian analysis).

| Pulsar | Whites | Time-correlated | SW class | Deterministic extras | Sampled params |
|---|---|---|---|---|---|
| J1713+0747 | EF, EC | Chrom (β=4 fixed) | SW_Fixed | — | 6 |
| J2241-5236 | EF | — | SW_Full | — | 5 |
| J0437-4715 | EF, EC | DM + Chrom (β free) | SW_Fixed | — | 8 |
| J1909-3744 | EF, EQ, EC | DM | SW_Full | — | 9 |
| J1744-1134 | EF, EQ, EC | — | SW_Full | — | 7 |
| J0125-2327 | EF, EQ, EC | DM | SW_Fixed | — | 6 |
| J1946-5403 | EF | — | SW_Fixed | — | 2 |
| J1600-3053 | EF, EQ | DM + Chrom (β=4 fixed) | SW_Det | chrom Gaussian event (+) | 12 |
| J1017-7156 | EF, EQ, EC | Red + Chrom (β free) | SW_Full | chrom Gaussian event (+) | 16 |
| J2129-5721 | EF | Chrom (β=4 fixed) | SW_Det | annual chrom variation | 8 |

(Sampled-param counts include the 13/3 amplitude; every pulsar's comparison set = all its sampled
parameters that appear in the published tables.)

Conventions carried unchanged from M1 (validated by J2241's 5/5 with edge-for-edge CI widths):
PINT backend on the TCB→TDB-converted pars, DE440; EFAC `MeasurementNoise`, TNEquad, epoch-quantised
`EcorrKernelNoise`; DM GP = Fourier power law, 120 components, full Tspan, 1400 MHz DM basis;
SW = e_e `solar_wind` deterministic (n_earth U(0,30)) + Hazboun-style SW GP with **linear-spaced**
harmonics, 120 components; fixed-γ=13/3 achromatic `FourierBasisGP`, 120 components; timing model
analytically marginalised with SVD. Sampler PTMCMC (declared M1 deviation from the paper's
parallel-bilby stands: we compare posteriors, never evidences).

New model components for M2, with declared conventions:

- **Chromatic GP** (scattering): the paper's PSD carries (ν/ν_ref)^(−2β) so the *delay* basis
  scales as (1400 MHz/ν)^β — enterprise's `createfourierdesignmatrix_chromatic` with `idx = β`,
  120 components, full Tspan. β fixed at 4 where the table prints "4"; sampled where the table
  gives a CI.
- **Chromatic Gaussian event** (paper Eq. under §Other deterministic models; the printed equation
  omits the minus sign in the exponent — implemented as a decaying Gaussian):
  t(t) = sign·10^log10_Ag · exp(−(t−t0)²/2σ_g²) · (1400/ν)^β_g, sign fixed to the published column
  (+ for both J1017-7156 and J1600-3053). e_e 3.0.3 ships no Gaussian-bump waveform → implemented
  as a local `@signal_base.function` in `scripts/mpta_models.py`.
- **Annual chromatic variation**: e_e `chrom_yearly_sinusoid` (sin(2π f_yr t + φ)·(1400/ν)^β_s).
- **Priors not tabulated in the paper** (UNSOURCED, declared as assumptions, chosen to contain
  every published 68% interval in the comparison set): chrom log10_A U(−18,−11), γ_chrom U(0,7),
  β U(0,14); bump log10_Ag U(−10,−4) (log10 s), β_g U(0,14), t0 U(ToA span) MJD,
  σ_g U(10, 2000) d; annual log10_As U(−18,−4) (J2129-5721's published CI reaches −16.1, so the
  collaboration's prior floor must sit at or below that; a −10 floor would clip it), β_s U(0,14),
  φ U(0,2π). Whites/DM/SW/13/3 priors as in M1 §3. *Known residual prior-floor risk, declared:*
  J1713+0747's published chrom-amplitude CI reaches −18.05, marginally below our −18 amplitude
  floor — for that unconstrained-below marginal the tail shape depends on the floor; flagged if it
  decides an agreement call.
- The released pars carry `NE_SW 0` (verified, all 83) — the deterministic solar-wind delay lives
  entirely in the enterprise model; no double-counting with the timing model.

### 1.3 Harness-hardening acceptance (H-criteria — built and smoke-tested before the campaign)

M1 lessons implemented: size by wall-clock not iterations; gates in **raw iterations**; assume the
host may be contended.

- **H1 (wall-clock bound):** sampling proceeds in chunks (PTMCMC `resume=True` replay-continuation;
  chunk sized from measured throughput, ~10 min each, iteration counts kept multiples of
  isave=1000). The run stops within one chunk of its wall budget. A `STOP` file in the run
  directory (or global `STOP_ALL`) aborts cleanly at the next chunk boundary; SIGINT/SIGTERM abort
  immediately with the summary still written.
- **H2 (checkpoint/resume):** after a hard kill (SIGKILL), relaunching with the same run-id resumes
  from the on-disk chain; chain files whose row count violates PTMCMC's resume alignment
  (1 + k·isave/thin rows) are trimmed to the last valid block first. Verified by a smoke test
  (run → kill −9 → resume → chain grows monotonically).
- **H3 (summary on every exit):** a per-run summary JSON is (re)written after every chunk and on
  every exit path (gate met, wall-clock, stop file, signal, exception-with-traceback), carrying:
  state, exit reason, raw iterations, chain rows, acceptance rate, per-parameter medians + 68% CIs,
  max lnL visited, elapsed, measured eval time, host load samples.
- **H4 (niceness + inventory):** every sampling process runs under `nice -n 19` with BLAS/OMP
  threads pinned (1–2 per process, ≤ ~16 threads total) so Matthew's foreground use is not
  degraded; each run writes a manifest JSON (`results/m2/manifest/<run_id>.json`: pid, pulsar,
  kind, start, budget, state, heartbeat) and `scripts/m2_status.py` aggregates the inventory.

### 1.4 J1909-3744 convergence: success criterion (the "converge" task)

M1 measured, under our own likelihood: lnL(published MAP) = 97,306.1 vs 97,283.6 at the best point
M1's 11.7k-iteration chain visited (ΔlnL = +22.4), the miss being one coupled DM↔SW block parked at
the n_earth ≈ 22 prior-edge local mode. M2 runs **three chains** under the hardened harness, all
with per-signal jump groups (e_e `get_parameter_groups`) and prior-draw jump proposals on the
degenerate blocks (e_e `JumpProposal`: global prior draws + per-block draws on {DM}, {SW, n_earth},
{13/3}) — legitimate sampler improvements, no likelihood change:

- `blind1`, `blind2`: random prior starts, independent seeds — can our sampler find the mode blind?
- `informed`: started exactly at the published MAP vector (declared openly per the task contract);
  it must **stay and mix**, not merely sit.

**Success requires, on at least one chain** (each criterion evaluated post-burn, burn = first 25%):

- **S1 (mode reached):** the chain visits lnL ≥ 97,306.1 − 2 (it attains the published solution's
  likelihood level under our implementation).
- **S2 (9/9 agreement):** the M1 A2 rule — published MAP inside our 68% equal-tailed CI, OR our
  median inside the published 68% CI — holds for **all 9** sampled parameters.
- **S3 (stays and mixes):** ≥ 50,000 raw post-burn iterations; ≥ 90% of post-burn samples in the
  DM-dominated mode (membership: n_earth < 15 — the two modes sit at ~5 and ~22, cleanly split);
  last-half vs full-chain medians shift < 0.1 (log10-amplitudes, EFAC) / < 0.3 (γ, n_earth).
- **S4 (independence honesty):** the verdict states which chains satisfied S1–S3. If only
  `informed` does, the claim is correspondingly weaker — "the published mode is stable, preferred
  by ΔlnL, and reproduced 9/9 when found, but our sampler did not find it blind within budget" —
  reported as such, not as full convergence.

Failure of all three chains → the pre-registered alternative outcome: a persistent, diagnosed
discrepancy documented via the M1 mode-vs-model machinery (lnL at published MAP vs chain best,
plus where the chains actually went).

### 1.5 Top-10 campaign acceptance (C-criteria)

All 10 pulsars run fresh under the hardened harness (J1909's `blind1` doubles as its campaign run;
J2241 reruns at full length — its M1 run was 30k iterations under a mis-keyed gate).

- **C1 (convergence gate, raw iterations):** wall-clock cap **8 h sampling** per pulsar
  (chunked, abortable). Gate: ≥ 100,000 raw post-burn iterations AND the stability rule — medians
  last-half vs full-chain shift < 0.1 for log10-amplitudes and EFAC, < 0.3 for γ, β, and n_earth,
  and < 0.1 × prior width for the deterministic-event parameters (t0, σ_g, φ — parameters whose
  natural scales are set by their priors). Gate unmet at cap → that pulsar lands the M1-style A3
  feasibility verdict (measured evals/s, projection), reported as-is.
- **C2 (agreement):** per parameter, the A2 rule against the published tables. A pulsar "fully
  agrees" when **every** compared parameter agrees. Report per-pulsar x/y and the count of fully
  agreeing pulsars. (The paper itself notes some MAPs fall outside their printed CIs; such
  parameters are flagged where they occur.)
- **C3 (every miss diagnosed the M1 way):** for each disagreeing block, evaluate our lnL at the
  published MAP vector (fixed values β=4 / n_earth=4 entering as constants) vs the chain's best
  point. ΔlnL > 0 → sampling shortfall (ours); ΔlnL ≤ 0 → our likelihood genuinely prefers a
  different solution → convention/model finding. Either way it is documented, with the paper's
  MAP-outside-CI caveat checked before calling anything a contradiction.

### 1.6 Factorised-likelihood CURN slice (F-criteria) — runs only if ≥ 7/10 pulsars clear C1

Per the paper (§CURN, §Search for common processes; method = Taylor et al. 2022,
2022PhRvD.105h4049T): per-pulsar runs of the favoured model **plus a free achromatic red-noise
process where not already present** (log10_A U(−18,−11), γ U(0,7)), with the 13/3 fixed-γ term
playing the CURN role (log10_A_CURN U(−18,−11)); the factorised-likelihood posterior is the
renormalised product of the per-pulsar log10_A_CURN marginals (identical uniform priors make the
prior-division a constant).

- **F1 (models/declared deviation):** white noise **fixed at our own campaign posterior medians**
  (self-contained — no published values enter our chains). The paper says the common-signal search
  "re-sampled all time-correlated noise processes simultaneously", which we read as whites held
  fixed; if that reading is wrong the effect is a modest widening of intrinsic-noise posteriors,
  not a shift of the CURN amplitude — declared as this slice's main convention risk. Deterministic
  chromatic events and n_earth are re-sampled.
- **F2 (per-pulsar gate):** ≥ 50,000 raw post-burn iterations per FL run; pulsars under the gate
  are flagged and the product is reported both with and without them.
- **F3 (combination):** Gaussian-KDE product over pulsars on the common support, MAP and
  equal-tailed 68% quoted.
- **F4 (comparison + scope statement):** compared against the published 83-pulsar FL result
  `log10 A_CURN = −14.28 ± 0.21`. Pre-declared expectation: **consistency** (overlapping 68%
  intervals), plausibly with a wider interval. What a 10-pulsar FL slice establishes: the
  per-pulsar CURN-slice machinery and the FL combination reproduce the collaboration's amplitude
  scale on the array's most informative subset (J1909's A_13/3 is the single strongest per-pulsar
  constraint). What it does **not** establish: the detection (no evidence/Savage–Dickey claim), the
  spectral characterisation (γ fixed at 13/3), any spatial-correlation statement, or the 83-pulsar
  number itself.

### 1.7 Economics (recorded regardless of outcomes)

Per-run measured eval time and sustained it/s go into every summary JSON; the campaign updates the
all-83 projection and the full-array CURN projection from ≥ 10 measured pulsars instead of M1's 2.

---

*Results below this line were written after the runs; nothing above §2 was edited after sampling
started (git history is the audit trail).*

## 2. Harness hardening — BUILT, smoke-tested, all H-criteria PASS

Scripts (committed, LF): `scripts/mpta_harness.py` (chunked wall-clock driver),
`scripts/mpta_models.py` (top-10 models + published table + A2 machinery),
`scripts/m2_run.py` (per-run CLI), `scripts/m2_campaign.sh` (nice-19,
thread-pinned launcher), `scripts/m2_status.py` (inventory), `scripts/m2_analyze.py`
(C2/C3 analysis), `scripts/m2_fl_combine.py` (FL product), `scripts/m2_smoke_h2.sh`
(kill/resume/STOP smoke test).

Smoke-test evidence (J2241-5236, 2026-08-18):

- **H1/H3:** 4-min budget run: two chunks (5,000 + 9,000 iters), gate-met exit,
  summary JSON on disk after each chunk with state/exit/medians/economics;
  verdict computed (5/5 agreement at 14k iterations, matching M1's answer).
- **H2:** SIGKILL at 75 s left 901 rows; relaunch resumed from disk
  ("Resuming with 901 samples"), grew monotonically to 2,501 rows; `STOP` file
  then aborted cleanly (`exit_reason: stop_file`, summary written). Chain-file
  trimming to PTMCMC's 1+k·100-row alignment verified in the same test.
- **H4:** all runs `nice -n 19`, OMP/OPENBLAS pinned (1 thread light /
  4 threads heavy pulsars), per-run manifest JSONs aggregated by
  `m2_status.py`.
- **Error path validated for real** (below): the first smoke attempt crashed
  inside a jump proposal and the harness still wrote the summary with the full
  traceback (`state: error`) — and it was those on-disk tracebacks that let the
  two campaign crashes be diagnosed without re-running anything.
- **Gate** (as pre-registered): raw post-burn iterations + per-parameter
  median stability; an acceptance floor (`min_acc = 0.05`) was added *after*
  the campaign for future runs — see §5.1 for why and for the audit showing it
  changes none of M2's verdicts.
- **Campaign scale achieved:** 23 sampling runs (12 noise + 11 FL) managed by
  the harness across one session, including 12-way parallel execution, six
  mid-flight kills recovered from checkpoints, and two crash-diagnose-fix-relaunch
  cycles — with the foreground desktop usable throughout.

### 2.1 Findings bagged while hardening (all measured, none assumed)

1. **enterprise_extensions 3.0.3 jump proposals are broken under numpy 2.5.2**
   (this venv): every `JumpProposal` draw closure ends `float(lqxy)` where
   `lqxy` is a size-1 array (the pmap slice), and numpy ≥ 2 refuses the
   conversion → `TypeError` at the first custom jump. Replaced with
   self-contained scalar prior-draw proposals in `mpta_harness.py`
   (`_prior_draw_factory`; same behaviour, index-safe). e_e's
   `get_parameter_groups` is pure indexing and is kept.
2. **`pta.get_lnlikelihood` can return a size-1 `KernelMatrix`** (ndarray
   subclass) rather than a float — harmless in PTMCMC's float-array stores,
   but `float()`/`round()` on it crash under numpy 2; all analysis code
   coerces via `np.asarray(...).reshape(-1)[0]`.
3. **Model-refactor equivalence check:** the M2 `mpta_models` J1909-3744 build
   scores the published MAP at **lnL = 97306.06, digit-identical to M1's**
   `w2_j1909_mode_diag` reference — the ΔlnL = +22.4 mode-gap target carries
   over unchanged.
4. **Two release quirks cleared for the new pulsars** (fixes in
   `w1b_residuals.py`, A1-gated):
   - **J0437-4715 ships `BINARY T2`** (with KIN/KOM Kopeikin terms); PINT has
     no T2 model → loaded with `allow_T2=True` (auto-maps to DDK).
     A1: PINT wRMS 0.2337 µs vs TRES 0.2340 µs = **−0.11%** — the mapping is
     faithful.
   - **`TRACK -2` in 12/83 pars** (J1600-3053 among them) asks tempo2 to use
     tim-file pulse numbers that the released tims don't carry → PINT refuses
     to form residuals. Stripping the directive gives A1 **−0.03%**
     (0.8507 vs 0.8510 µs) — it was inert for the shipped data. Recorded for
     the future all-83 campaign.
5. **A1 (stack acceptance) extended to all top-10** — 10/10 PASS:
   J1713+0747 +12.15% (the outlier: shortest dataset, reduced-χ² 1.89 vs par's
   1.50; within tolerance), J1744-1134 +0.04%, J0125-2327 −0.02%,
   J1946-5403 −9.65% (1,815 of NTOA 2,185 ToAs shipped — the M1 §5.2
   partial-release pattern), J1017-7156 +0.05%, J2129-5721 +0.08%,
   J0437-4715 −0.11%, J1600-3053 −0.03%, plus M1's J1909 +0.35% and
   J2241 +0.51%.
6. **WSL kills detached campaigns (measured the hard way):** WSL2 tears the
   VM down when the last `wsl.exe` session exits — the first campaign launch
   `nohup`-ed 12 runs and returned, and every process was SIGKILLed within
   seconds (0-byte logs, no manifests; the smoke tests had survived only
   because their session stayed open). Fix, now part of the harness:
   `scripts/m2_campaign_wait.sh` launches the campaign and **stays alive as
   the keepalive session**, polling the manifests until every run is
   terminal. Second layer, measured an hour later when the keepalive session
   itself was externally killed: children die with their launching session
   **despite nohup** (six of ten runs lost mid-flight; the checkpoint/resume
   machinery recovered every one from its on-disk chain). Launcher now uses
   `setsid nohup`, so runs survive their session as long as *any* session
   keeps the VM alive. Any future runner on this box needs both layers.
7. **enterprise 3.5.0 bug: varying-BASIS parameters zero the GP prior matrix
   (found because it crashed the campaign's two free-β pulsars).**
   In `gp_signals.BasisGP`, `_construct_basis` — re-run whenever a basis
   parameter (here the chromatic index β) changes — reallocates `self._phi`
   to a zero `KernelMatrix`; but `_construct_prior`, the code that fills phi,
   is cached on **prior params only** (`cache_call("prior_params")`).
   A proposal that changes β without touching (log10_A, γ) — every SCAM
   single-parameter jump — rebuilds the basis, zeroes phi, hits the stale
   prior cache, and returns an all-zero phi block → `phiinv = inf` →
   `cho_factor: array must not contain infs or NaNs`. Diagnosed by bisection
   (60 full prior draws pass — every draw re-keys both caches — while a
   β-only step fails deterministically; `results/m2` first-launch error
   summaries hold the tracebacks). **Fix:** `mpta_models.py` subclasses the
   free-β chromatic `BasisGP` with `_construct_prior` cached on
   `["prior_params", "basis_params"]` (body verbatim), plus `combine=False`
   so β sampling through exactly 2.0 can't merge the chromatic basis into the
   DM basis mid-run (column-count change). Verified: β-only jumps finite,
   identical draws give digit-identical lnL before/after (caching fix only).
   J0437-4715 and J1017-7156 relaunched clean. Upstream-relevant: any
   enterprise analysis sampling a chromatic index with single-parameter
   jumps hits this crash; worth reporting to the enterprise maintainers
   (Matthew's call — repo law: no submissions by agents).
8. **M1's "quiet-host" J1909 bench was still contaminated:** on the genuinely
   idle host the 9-parameter eval costs **97 ms** (1 BLAS thread) / 63 ms (2) /
   **43 ms (4)**, not M1's 436 ms — a 4.5× correction that reprices every M1
   projection (see §6). J2241's 5-parameter eval: 13 ms vs M1's 100 ms.

## 3. J1909-3744: CONVERGED — 9/9 on all three chains, blind chains found the mode unaided

Verdict against the pre-registered S-criteria (§1.4), all three chains, 2026-08-18:

| Criterion | blind1 (prior start) | blind2 (prior start) | informed (published start) |
|---|---|---|---|
| S1: reach lnL ≥ 97,304.1 | **97,308.4** ✓ | **97,308.2** ✓ | **97,308.2** ✓ |
| S2: A2 agreement | **9/9** ✓ | **9/9** ✓ | **9/9** ✓ |
| S3: post-burn in DM mode | **100%** (n_earth < 15) ✓ | 100% ✓ | 100% ✓ |
| S3: raw post-burn / stable | 102,010 / stable ✓ | 101,260 / stable ✓ | 104,260 / stable ✓ |
| Exit | gate_met (106 min) | gate_met (105 min) | gate_met (105 min) |

**S4 statement: the strongest form.** Both *blind* chains found the DM-dominated global mode
without any information about the published solution — the informed start was not needed (it
serves as confirmation that the mode is stable under continued mixing: started at the published
MAP, it stayed, mixed, and reproduced the same posterior). All three chains exceed the published
MAP's own likelihood level (max lnL ≈ 97,308.3 vs 97,306.1 at the published values — the chain
finds the mode's true peak, ~2 lnL above the table's rounded MAP vector).

M1's diagnosed ΔlnL = +22.4 sampling shortfall is therefore **resolved by sampler machinery
alone** — per-signal jump groups + per-block prior-draw proposals (the DM↔SW mode-hop lever) +
a wall-clock budget the harness actually enforces; the likelihood was untouched (§2.1 item 3:
digit-identical at the reference point). The chromatic block that M1 could not reach lands
dead-on: `log10 A_DM = −13.600 [−13.665, −13.531]` vs published −13.60 (−13.67, −13.53);
`n_earth = 4.94 [3.78, 6.01]` vs 4.96 (3.72, 5.82); the SW pair and γ_DM inside the published
intervals; and the GW-relevant `A_13/3 = −14.29 [−14.48, −14.11]` vs −14.28 (−14.49, −14.11) —
CI edges matching to ~0.01 dex. Cross-chain medians agree to 0.005–0.03 across all 9 parameters —
an informal 3-chain convergence check on top of the registered gates.
Corner: `figures/m2_J1909-3744_noise_blind1_corner.png`.

## 4. Top-10 campaign: 10/10 converged, 9/10 in full agreement, 76/78 parameters agree

Every run cleared the pre-registered C1 gate (≥100k raw post-burn + stability) — none needed the
A3 feasibility fallback. Agreement against the published tables (C2; A2 rule per parameter):

| Pulsar | Sampled/compared | Agree | Raw iters | Verdict |
|---|---|---|---|---|
| J1713+0747 | 6 / 5 | **5/5** | 228,000 | full agreement |
| J2241-5236 | 5 / 5 | **5/5** | 167,000 | full agreement (M1 confirmed at 5.5× the iterations) |
| J0437-4715 | 8 / 8 | **8/8** | 140,000 | full agreement — free-β chromatic recovered (β = 7.95 pub) |
| J1909-3744 | 9 / 9 | **9/9** | 136,000 | full agreement (§3; blind1 = campaign run) |
| J1744-1134 | 7 / 7 | **7/7** | 151,000 | full agreement |
| J0125-2327 | 6 / 6 | **6/6** | 153,000 | full agreement |
| J1946-5403 | 2 / 2 | **2/2** | 218,000 | full agreement |
| J1600-3053 | 12 / 12 | **12/12** | 201,000 | full agreement — incl. all 4 chromatic-Gaussian-event params + n_earth |
| J1017-7156 | 16 / 16 | **14/16** | 182,000 | two chromatic misses, diagnosed below |
| J2129-5721 | 8 / 8 | **8/8** | 401,000 | full agreement — incl. all 3 annual-chromatic params |

Parameter-level total: **76/78 agree**. The two hard deterministic structures the paper models —
J1600-3053's and J1017-7156's chromatic Gaussian events (amplitude, chromatic index, epoch, width)
and J2129-5721's annual chromatic sinusoid — all reproduce inside the published intervals, from
scratch, on public data. `results/m2/campaign_table.json` holds the full machine-readable table;
corners with published MAPs overlaid: `figures/m2_<run>_corner.png`.

### 4.1 The named miss, diagnosed (C3): J1017-7156's chromatic pair — a ridge, not a shortfall

The only misses in 78 comparisons are J1017-7156's scattering-noise pair:

| | chrom log10_A | γ_chrom | β (agrees) |
|---|---|---|---|
| Ours | −13.70 [−13.98, −13.46] | 1.20 [0.86, 1.55] | 4.40 [3.63, 5.09] |
| Published | −13.42 [−13.62, −13.16] | 1.57 [1.27, 1.77] | 3.85 [2.86, 4.28] |

Both A2 routes fail by only 0.03–0.08 dex (the raw intervals overlap), and the offsets sit exactly
along the A–β anti-correlation the (1400 MHz/ν)^β parameterisation forces: our chain prefers a
slightly steeper chromatic index (β 4.40 vs 3.85) paired with a lower 1400-MHz amplitude.
**Mode-vs-model diagnostic (the M1 machinery, C3): our likelihood scores our chain's best point
ΔlnL = +4.8 ABOVE the published MAP vector** (41,454.5 vs 41,449.8) — the mirror image of M1's
J1909 case. This is therefore **not a sampling shortfall**: our sampler found a mildly better
point on the same ridge under our likelihood. Reading, per pre-registration: a
**convention/prior finding** — the paper does not tabulate its priors (β prior unknown; our
declared U(0,14)), J1017 carries the release's most complex model (16 parameters: free-β chromatic
GP + free achromatic red + SW_Full + a chromatic Gaussian event), and the paper itself warns some
MAPs fall outside their printed CIs. A ~5 lnL preference on a 16-parameter, 3,321-ToA fit is far
too small to call a contradiction of the published table; it is exactly the size of effect a
different β/amplitude prior or sampler (nested vs MCMC) would produce along a flat ridge. The
other 14 parameters of the same fit — including all four Gaussian-event parameters — agree.

## 5. Factorised-likelihood CURN on 10 pulsars: −14.46, consistent with the published −14.28 ± 0.21

All ten FL runs (favoured model + a free achromatic red process where absent, whites fixed at our
own campaign medians, γ = 13/3 CURN term) cleared the F2 gate — none flagged. The FL product
(F3: renormalised product of the per-pulsar log10_A_CURN marginals; identical uniform priors):

| | MAP | median | 68% CI |
|---|---|---|---|
| **This work, 10 best-timed MPTA pulsars** | **−14.46** | **−14.53** | **[−14.92, −14.31]** |
| Published, 83 pulsars (arXiv:2412.01148, FL, γ=13/3) | −14.28 | — | [−14.49, −14.07] |

**Consistent** (F4): the intervals overlap over [−14.49, −14.31]; our MAP sits 0.18 dex below the
published one, well inside a combined uncertainty, and our interval is wider on the low side as
expected from 1/8 of the array. Per-pulsar CURN medians span −14.06 (J2129-5721) to −16.24
(J1744-1134); the product is driven, correctly, by the pulsars with genuinely constrained
amplitudes rather than by the many that only bound it from above.
Figure: `figures/m2_fl_curn.png` (per-pulsar marginals + product + published band);
data: `results/m2/fl_curn.json`, per-pulsar samples in `results/m2/*.curn.npy`.

**What this establishes:** the per-pulsar CURN-slice machinery and the paper's own FL combination
reproduce the collaboration's common-signal amplitude scale on the array's most informative
subset, built from public data with an independently implemented likelihood — and, notably, the
CURN amplitude survives adding a free intrinsic red process to every pulsar (the paper's own
misspecification mitigation).
**What it does NOT establish:** the *detection* (no Bayes factor / Savage–Dickey computed — the
pre-registration forbade an evidence claim), the spectral characterisation (γ was fixed at 13/3),
anything about spatial correlations (no HD, no CW — the sparse-stack lanes are still deferred),
and not the 83-pulsar number itself. A 10-pulsar FL estimate is an intermediate milestone: it
validates the pipeline that the full-array run will use, and its agreement is evidence about the
*machinery*, not an independent confirmation of the MPTA detection.

### 5.1 A frozen chain nearly produced a wrong headline number (and the registered gate did not catch it)

J1909-3744's first FL run (`fl1`) passed the pre-registered F2/C1-style gate — 90,010 raw
post-burn iterations, every parameter's last-half vs full-chain median stable — while running at
**acceptance 0.016**: the initial jump covariance (0.25 × prior std) is far too wide for a
fixed-white FL posterior, so the chain barely moved, and *not moving is maximally "stable"*. Its
CURN marginal came out at median −17.11 (vs −14.29 for the same pulsar's own A_13/3 in the noise
campaign — a 2.8 dex error). Combined, that chain would have given
**log10 A_CURN = −14.75 (MAP), median −14.95, 68% [−16.47, −14.54] — flagged "not consistent"
with the published value** (artifact kept: `results/m2/fl_curn_frozen_j1909.json`).

Diagnosis and fix: rerun with `--cov-scale0 0.05` (`fl2`) → acceptance **0.189**, 350,000 raw
iterations in 17 min, CURN median −14.40, in line with its own noise-campaign A_13/3 of −14.29.
The reported result uses `fl2`; `fl1` is retained in `results/m2/` rather than deleted.

**The registration lesson, recorded:** a median-stability criterion cannot distinguish a converged
chain from a frozen one — M1 pre-registered gates in thinned rows and M2 fixed that to raw
iterations, but both versions were blind to acceptance rate. Any future gate in this project must
carry an **acceptance-rate floor (or an effective-sample-size requirement)** alongside the
stability check. Caught here only because the FL number disagreed with the same pulsar's noise-run
amplitude — an accidental control; the harness now records `acc_rate` in every summary, which is
what made the diagnosis a two-minute job.

**Audit of every other run (done before reporting anything):** acceptance rates across all 23 M2
runs are 0.167–0.489 except `fl1`'s 0.016 — no other chain is frozen, and the 22 healthy runs
include every number reported in §3–§5. The harness gate now carries a `min_acc = 0.05` floor
(added *after* the campaign; M2's verdicts stand exactly as pre-registered, and the floor would
not have changed any of them — it only rejects `fl1`).

## 6. Economics, remeasured at 10 pulsars (repricing every M1 projection)

Quiet-host, `nice -n 19`, threads as noted; all values from run summaries
(`results/m2/*.summary.json`, `bench` fields = first-eval-warmed medians):

| Pulsar (params) | noise eval | FL eval (whites fixed) | noise gate wall |
|---|---|---|---|
| J1946-5403 (2) | 8.3 ms | 0.36 ms | 6 min |
| J1713+0747 (6) | 15.6 ms | 1.3 ms | 7 min |
| J2129-5721 (8) | 34.4 ms | 3.1 ms | 32 min¹ |
| J2241-5236 (5) | 41.6 ms | 3.5 ms | 5 min¹ |
| J1744-1134 (7) | 46.1 ms | 2.5 ms | 6 min¹ |
| J0125-2327 (6) | 49.6 ms | 1.6 ms | 7 min¹ |
| J1600-3053 (12) | 51.9 ms | 9.7 ms | 75 min |
| J1017-7156 (16) | 66.9 ms | 50.6 ms² | 60 min |
| J0437-4715 (8) | 78.3 ms | 78.0 ms² | 61 min |
| J1909-3744 (9) | 89–115 ms | 13.3 ms | 105 min |

¹ resumed runs: wall shown is the final session; each also carried ~60 min of pre-kill sampling.
² free-β chromatic basis forces a full TNT rebuild per eval even with fixed whites — the fixed-white
speedup does not apply to varying-basis models (a real constraint M1's 1.4 ms bench could not see).

- **All-83 single-pulsar noise campaign:** the top-10 — which contains the release's four heaviest
  models — cleared its gates in one afternoon at 12-way parallel on a shared desktop. The
  remaining 73 pulsars are lighter (fewer ToAs, mostly simpler models): a full-array campaign is
  an **overnight job**, not M1's "~1 day at 16-way" (which was extrapolated from a
  contention-poisoned 436 ms eval).
- **Full-array CURN (fixed-white PTMCMC):** per-pulsar CURN-config evals measured here average
  ~2–5 ms for typical models (not M1's minimal-model 1.4 ms) → full-83 eval ≈ 0.2–0.4 s →
  1M iterations ≈ **2.5–5 days** background. Still feasible; the FL route (per-pulsar parallel,
  hours total) is now the validated cheap primary, with the full-PTA run as confirmation.
- **CW/HD-correlated work:** unchanged from M1 — needs the sparse stack (micromamba route);
  economics still unmeasured, deliberately not promised.

## 7. Recommended M3 / W3 (updated by M2's findings)

1. **W3 first product — cross-PTA noise-model criticism, now de-risked:** M2 proved the house
   stack reproduces MPTA's per-pulsar models end-to-end including the hard chromatic machinery
   (free-β GPs, Gaussian events, annual terms). The two seams M2 exposed are exactly where a
   criticism paper lives: (i) the chromatic A–β ridge (J1017: our likelihood prefers a point
   ΔlnL = +4.8 off the published MAP — prior-sensitive, tabulate-your-priors material), and
   (ii) intrinsic-red vs 13/3 absorption (J1600's A_13/3 drops 1.3 dex when a free-γ red process
   is added — the paper's own mitigation, §Search for common processes, and a live
   misspecification lever). NANOGrav 15-yr public noise chains are the comparison set.
2. **All-83 noise campaign** (overnight, hardened harness) → **83-pulsar FL CURN** — the honest
   full reproduction of −14.28 ± 0.21. M2's 10-pulsar slice validates the machinery;
   the number itself needs the array.
3. **Full-PTA CURN posterior** (PTMCMC, 2.5–5 d background) as the slow confirmation, after 2.
4. **Harness follow-ups:** the acceptance floor is **already implemented** (`min_acc = 0.05`,
   §5.1) — remaining: per-model default `cov_scale0` (fixed-white FL models want ~0.05, free-white
   0.25) so no future FL run starts frozen, and an effective-sample-size statistic alongside
   acceptance. Also outstanding, Matthew's call: an upstream bug report to the enterprise
   maintainers for the varying-basis phi-cache defect (§2.1 item 7).
5. **Deferred, unchanged:** CW upper-limit map and HD work until the sparse stack lands;
   IPTA DR3 readiness rides the same per-pulsar parameterisation.
