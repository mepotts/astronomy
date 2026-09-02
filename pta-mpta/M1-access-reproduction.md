# M1 — MPTA access verified, stack build, pre-registered reproduction slice

*2026-08-16. First milestone of avenue #2 ([`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md)).
Repo law: every externally-sourced number carries its source URL or the mark UNSOURCED; negative
results are results; blockers are findings.*

---

## 1. W1a — Access verdict: PASSED (TOAs + ephemerides fully public, account-free)

The run-3 claim ("83 MSPs, TOAs + profiles public") **verifies**, with one correction: the data are
not hosted on the GitHub site itself but on Data Central (AAO/Macquarie); and the release ships **no
noise chains or posteriors of any kind** (see §1.3).

### 1.1 What the 4.5-yr release actually ships

Entry point: <https://mpta-gw.github.io/> → data page <https://mpta-gw.github.io/data.html> →
access docs <https://docs.datacentral.org.au/meerkat-pulsar-timing-array/45-year/accessing-the-data/>
(last updated 2024-11-01). Four direct-download files, **no account, no gate** (verified by HTTP HEAD
and full download 2026-08-16; sizes are measured Content-Length):

| File | URL | Size | Contents (verified by extraction) |
|---|---|---|---|
| `partim.tar.gz` | <https://docs.datacentral.org.au/documents/52/partim.tar.gz> | 7,283,924 B (6.9 MiB) | **83 `.par` + 83 `.tim`** — the full timing release |
| `archives.tar.gz` | <https://docs.datacentral.org.au/documents/51/archives.tar.gz> | 867,068,478 B (827 MiB) | **10,014** per-epoch PSRFITS fold-mode archives (`*_zap.928chI.fluxcal[.dly]`, under `data_august23_32ch/<PSR>/`) for **85** pulsars — the 83 released **plus J1103-5403 and J1705-1903** (profiles only, no par/tim; J1103-5403 is the mode-changing MSP discussed in the paper's ECORR section) |
| `portraits.tar.gz` | <https://docs.datacentral.org.au/documents/53/portraits.tar.gz> | 3,922,099 B (3.7 MiB) | 83 PSRFITS 2-D template portraits (`2D.<PSR>.notebook_version.ar`), 1:1 with the pars |
| `MPTA_Anisotropy_supplement.zip` | <https://docs.datacentral.org.au/documents/54/MPTA_Anisotropy_supplement.zip> | 443,539,544 B (423 MiB) | **9 MP4 movies only** (CGW/GWB S/N sky maps, 3 frequency bins each) — *not* chains |

All four are in `data/` (gitignored), total 1.25 GiB; C: had 722 GiB free before download.

**Format details** (verified by inspection of `J1909-3744.{par,tim}`):

- `.par`: tempo2 format, `UNITS TCB`, `EPHEM DE440`, `CLK TT(BIPM2020)`, `TIMEEPH IF99`,
  `T2CMETHOD IAU2000B`, `CORRECT_TROPOSPHERE Y`, `PLANET_SHAPIRO Y`; binary models incl. ELL1;
  DM as Taylor series (`DM_SERIES TAYLOR`, DM1/DM2); per-window `JUMP`s; **no noise parameters**
  (no TNEF/TNEQ/TNECORR lines). Each par carries tempo2's own fit stats — e.g. J1909-3744:
  `TRES 0.257` (µs), `CHI2R 12.5512 7179`, `NTOA 7199` — which gives an in-release, per-pulsar
  ground truth for the stack acceptance test (A1 below).
- `.tim`: `FORMAT 1` (tempo2), IPTA-style metadata flags; **frequency-resolved sub-banded ToAs,
  32 channels per epoch** (`-nch 32 -chan k`), one backend/receiver (`-f KAT_MKBF`, `-fe KAT`),
  per-ToA `-snr`, `-gof`, `-tmplt`. The paper (§data release) calls this "IPTA defined metadata";
  ToA counts: J1909-3744 7,199; J0437-4715 3,519; J2241-5236 3,407; J1017-7156 3,323;
  J0125-2327 3,172 (measured).

### 1.2 What the release does NOT ship (all verified absent from the four files)

- **No noise-model chains or posteriors** (single-pulsar or common-signal). The anisotropy
  supplement is presentation movies only. Consequence: reproduction option (b) — "compare against
  released common-signal posteriors" — is **impossible for MPTA**; the comparison target is the
  published tables of arXiv:2412.01148 (option (a)).
- **No DM time series** as a data product (DM enters via par Taylor terms + the paper's DM-GP
  analysis, whose chains are not released).
- **No noise-model par extensions** — an independent analysis must build noise models from scratch
  (which is exactly the credibility exercise W2 wants).

### 1.3 License / citation

**No license is stated** on the access page or the MPTA docs index (checked 2026-08-16; the index
says "Info coming soon"). Treat as: fine for analysis, **verify licensing with the collaboration
before redistributing any derived data product**. The canonical citation anchors (from the paper's
Data Availability section): DOI <https://doi.org/10.57891/j0vh-5g31> (verified 2026-08-16: 302 →
the accessing-the-data page above) and the data paper
[arXiv:2412.01148](https://arxiv.org/abs/2412.01148) (Miles et al., "The MeerKAT Pulsar Timing
Array: The 4.5-year data release and the noise and stochastic signals of the millisecond pulsar
population"). The 2.5-yr release has its own DOI (<http://dx.doi.org/10.26185/6392814b27073>).

---

## 2. Published targets for the reproduction (source: arXiv:2412.01148 LaTeX source, retrieved 2026-08-16 from <https://arxiv.org/e-print/2412.01148>, file `mnras_template.tex`)

Headline common-signal results (abstract + §results):

- CURN, spectral index free: `log10_A_CURN = -14.25 (+0.21/-0.36)`, `gamma_CURN = 3.60 (+1.31/-0.89)`
- CURN, gamma fixed at 13/3: `log10_A_CURN = -14.28 (+0.21/-0.21)`, `ln(B) = 4.46`
- Free-spectrum: 30 frequencies from 1/T (~7.04 nHz); only the first two bins constrained.

Analysis conventions (paper §methods):

- Sampling: single-pulsar noise via **enterprise + parallel-bilby** (nested, via enterprise_warp /
  parallel_nested_sampling_pta); full-PTA CURN via **PTMCMC**.
- Fourier GPs: **120 components** for time-correlated processes (chosen so max fluctuation
  frequency ~ 1/14 d, the observing cadence), fundamental 1/Tspan.
- White noise: EFAC (E_F), EQUAD (E_Q), ECORR (E_C); E_C 100% correlated across sub-bands of an
  epoch, uncorrelated between epochs. **All terms sampled simultaneously per pulsar** (table
  caption), not fixed-then-searched.
- Every per-pulsar model also carries a fixed-index achromatic term at gamma = 13/3 with free
  amplitude, reported as `log10_A_13/3`.
- DM & SW GP realisations referenced to 1400 MHz. Deterministic solar wind density `n_earth`
  sampled per pulsar.
- Prior ranges: **not tabulated in the paper source** (UNSOURCED; we use standard wide log-uniform
  priors and record them in §3 — a declared assumption of this reproduction).

Per-pulsar noise values (MAP with 68% CI), from `Table: MPTA noise models` rows, to be used as the
comparison targets:

| Pulsar | E_F | E_Q | E_C | log10A_Red | γ_Red | log10A_DM | γ_DM | log10A_Chrom | γ_Chrom | β | log10A_SW | γ_SW | log10A_13/3 | n_earth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| J1909-3744 | 1.04 (-0.02,+0.00) | -7.17 (-0.03,-0.00) | -7.17 (-0.06,+0.02) | — | — | -13.60 (±0.07) | 2.04 (-0.18,+0.28) | — | — | — | -6.43 (-0.19,+0.10) | 1.39 (-0.42,+0.21) | -14.28 (-0.21,+0.17) | 4.96 (-1.24,+0.86) |
| J2241-5236 | 1.05 (±0.01) | — | — | — | — | — | — | — | — | — | -6.16 (-0.10,+0.06) | 1.81 (-0.30,+0.18) | -14.82 (-1.57,+0.28) | 5.86 (-2.32,+1.59) |

(J0437-4715 and J1017-7156 rows also extracted but not targeted in-session: both carry chromatic /
deterministic-event terms that make a first reproduction slice needlessly model-fragile.)

---

## 3. W2 pre-registration (written 2026-08-16, BEFORE any sampling run)

**Targets.** (1) **J2241-5236** — simplest favoured model in the best-timed set (EFAC + solar wind
+ fixed-γ term; 5 sampled parameters), cheap, run first. (2) **J1909-3744** — the MPTA flagship
(EFAC + EQUAD + ECORR + DM-GP + SW + fixed-γ term; 9 sampled parameters).

**Model implementation** (enterprise + enterprise_extensions, PINT backend):

- EFAC/EQUAD: `MeasurementNoise` with TempoNest-convention EQUAD (tnequad), log10 seconds.
  *Declared risk:* if the paper used the t2equad convention the EQUAD comparison shifts by
  O(E_F factor); with E_F ≈ 1.04 this is small vs the CI width.
- ECORR: epoch-quantised kernel (all 32 sub-bands of an epoch correlated) — enterprise
  `EcorrKernelNoise` / basis model, log10 seconds.
- DM GP: Fourier-basis power law, **120 components**, DM basis (1400 MHz reference), for J1909 only.
- Solar wind: enterprise_extensions `solar_wind_block` — deterministic n_earth (uniform prior)
  + SW perturbation GP (power law). *Declared risk:* if MPTA's SW-GP amplitude convention differs
  from e_e's, `log10A_SW`/`γ_SW` may disagree systematically while all other parameters match;
  such an outcome is reported as a convention finding, not silently dropped.
- Fixed-γ achromatic red process at γ = 13/3, free log10A (their `A_13/3`).
- Timing model analytically marginalised (`TimingModel`); ephemeris DE440 as in the pars.
- Priors (assumption, recorded): EFAC U(0.1, 5); log10_EQUAD, log10_ECORR U(-10, -5);
  log10_A_DM U(-18, -11); log10_A_13/3 U(-18, -11); γ U(0, 7); SW per e_e defaults
  (n_earth U(0, 20), log10_A_SW U(-10, 1)).
  *Amendment 2026-08-16, before any sampling:* n_earth prior corrected to **U(0, 30)** — that is
  the actual e_e `solar_wind_block` default (the 0–20 above mis-stated it); and the SW GP basis is
  declared **linear-spaced** (`logf=False`, 120 components, full Tspan): the paper specifies
  "harmonically related sinusoids" with fundamental 1/Tspan, while e_e's solar basis defaults to
  log-spaced — a convention divergence we resolve in the paper's favour. The paper's SW model is
  Hazboun et al. 2022 (cited as 2022ApJ...929...39H in the tex), which is the model e_e's
  `solar_wind_block` implements.
- Sampler: **PTMCMCSampler** (2-core workstation budget). *Declared deviation:* the paper used
  parallel-bilby nested sampling for single-pulsar noise; we compare **posteriors only**, never
  evidences, so sampler choice affects convergence speed, not the target quantities.

**Acceptance criteria** (registered before running):

- **A1 (stack acceptance, W1b).** PINT loads par+tim for J1909-3744; the weighted RMS of PINT
  residuals must be within **15%** of the par file's own tempo2 `TRES` value (0.257 µs), and the
  residual plot is committed as PNG. The pars are TCB; PINT converts to TDB on read — if the
  conversion degrades the fit beyond the 15% tolerance, that is a documented blocker finding and
  the fallback comparison is tempo2-in-WSL.
- **A2 (per-parameter agreement).** A parameter "agrees" iff the published MAP lies within our 68%
  equal-tailed credible interval, OR our posterior median lies within the published 68% CI.
  The slice **passes** for a pulsar if ≥ 4 of 5 (J2241-5236) / ≥ 7 of 9 (J1909-3744) parameters
  agree. Anything less is reported as-is (a negative result is a result).
- **A3 (convergence gate / feasibility fallback).** Wall-clock cap **90 min per pulsar** of
  sampling. Converged = ≥ 5,000 post-burn-in samples (25% burn) AND last-half vs full-chain medians
  shift < 0.1 (log10-amplitudes, EFAC) / < 0.3 (γ). If not converged within cap → declare option
  (c) for that pulsar: report measured likelihood evals/sec, acceptance rate, and projected time to
  convergence. That measurement is then the M1 result — pre-registered as an acceptable outcome.
- **Economics (recorded regardless).** Single-eval likelihood time and sustained evals/sec for both
  pulsars; projected cost of (i) all-83 single-pulsar noise runs, (ii) a full-PTA fixed-white-noise
  CURN run — these numbers pick W3.

**What this slice does and does not establish.** Two pulsars ≠ 83; agreement here validates the
*likelihood implementation and data handling* (formats, units, GP bases, white-noise kernels)
against the collaboration's, on the array's most informative pulsar plus its simplest clean case.
It does **not** reproduce the CURN detection, the model selection (their codified Bayesian
analysis), or any evidence value — those are W3-scale statements.

---

## 4. W1b — stack build log (what mattered)

Scripts: `scripts/setup_wsl_env.sh` (phase 1), `setup_wsl_env_phase2.sh`, `setup_wsl_env_phase3.sh`.
Environment: WSL2 Ubuntu (kernel 6.6.87.2-microsoft), Python 3.12.3, 32 cores, 30 GB RAM visible.

1. **WSL disk constraint (found before building):** the Ubuntu WSL root vdisk is **100% full
   (5.4 GB free of 1007 GB)** — it is someone's working space; nothing was deleted. The venv, pip
   cache, and pip TMPDIR all live on `/mnt/c` (722 GB free). Cost: slow venv creation/imports
   (9p filesystem); sampling is numpy-bound and unaffected.
2. **Phase 1 (plain pip) failed exactly where the classic PTA install pain is:**
   `pip install enterprise-pulsar` dies building **scikit-sparse**, which needs system SuiteSparse
   headers (`libsuitesparse-dev`) — and this WSL has **no passwordless sudo**, so no apt. Gate
   documented; routed around rather than escalated:
3. **Route-around (phase 2/3), validated by reading enterprise 3.5.0 source:** in
   `signals/signal_base.py`, the sparse CHOLMOD path is only exercised when the PTA has
   `_commonsignals` (cross-pulsar correlated signals); for single-pulsar models the likelihood
   uses scipy dense `cho_factor`. `libstempo` is import-guarded (PINT backend instead). So:
   `pip install --no-deps enterprise-pulsar enterprise_extensions` + explicit deps
   (`ephem healpy scikit-learn h5py ptmcmcsampler pyarrow la-forge`) + a **loud-failure shim** for
   `sksparse.cholmod` (`scripts/sksparse_shim/`, copied into site-packages) that raises with a
   clear message if any sparse-cholesky path is ever reached. A future multi-pulsar/common-signal
   milestone on this machine **must install real scikit-sparse** (needs sudo, or a micromamba
   user-space env — the documented upgrade path) — the sparse branch concerns exactly the full-PTA
   GWB likelihood. *(Note: enterprise's dense fallback `LogLikelihoodDenseCholesky` also covers
   common-signal PTAs without sksparse; slower for large arrays but available.)*
4. **Final stack (imports verified):** PINT 1.1.6 · enterprise 3.5.0 · enterprise_extensions 3.0.3
   · PTMCMCSampler 2.1.4 · la_forge 1.1.0 · corner 2.3.0 · healpy 1.20.0 ·
   fastshermanmorrison-pulsar 0.5.5 · numpy 2.5.2 · scipy 1.18.0 · astropy 8.0.1 (all wheels).
5. **tempo2: deliberately not built.** A1 passed on PINT alone (below), so the classic tempo2
   compile was not needed for M1. It becomes relevant only if a future slice needs exact tempo2
   semantics (e.g. T2CMETHOD details) — record: nothing in M1 required it.

## 5. Results

### 5.1 A1 — stack acceptance: PASS on both targets

PINT reads the TCB pars (auto-converted to TDB, **no refit needed**) and reproduces tempo2's own
in-release weighted RMS:

| Pulsar | ToAs loaded | PINT wRMS | par TRES (tempo2) | diff | A1 (≤15%) |
|---|---|---|---|---|---|
| J1909-3744 | 7,199 / 7,199 | 0.2579 µs | 0.2570 µs | **+0.35%** | PASS |
| J2241-5236 | 3,405 | 0.1679 µs | 0.1670 µs | **+0.51%** | PASS |

Reduced χ² 12.61 vs par's 12.55 (J1909) — the ~12× excess over 1 is expected pre-noise-model
(no EFAC/EQUAD/ECORR applied at this stage). Committed figures:
`figures/w1b_J1909-3744_residuals.png`, `figures/w1b_J2241-5236_residuals.png`. PINT warnings on
record: `DILATEFREQ Y`, `TIMEEPH IF99`, `DM_SERIES TAYLOR`, `EPHVER 5` unsupported/unrecognized —
none material at the 0.5% level. The pars' `JUMP -MJD_* -1` selectors match **zero** ToA flags in
the shipped tims (the flags don't exist there) — inert for tempo2 and PINT alike, noted as a
release quirk.

### 5.2 Release inventory findings (beyond the access table)

- **245,907 ToAs total** across the 83 shipped `.tim` files (measured).
- **63/83 pulsars: par `NTOA` equals the shipped ToA count exactly.** 20/83 ship *fewer* ToAs than
  the par records — extreme case J2241-5236 (3,405 shipped vs `NTOA 6688`; its `CHI2R` dof line
  matches the larger set too). The pars evidently retain fit metadata from a richer internal
  dataset. Practical effect: for those 20, in-par TRES/CHI2R are approximate (not exact) ground
  truth for the shipped tims — J2241's TRES still matched to +0.51%.

### 5.3 W2 — reproduction slice results

**Run environment caveat (measured, first-class):** the Windows host ran a AAA game at 100% CPU
for the whole session (32-core box; `tlou-i` topping the process table). Every absolute rate below
is a **contention-contaminated lower bound**; relative comparisons (free- vs fixed-white) survive.

#### J2241-5236 (5 sampled parameters; 30,066 PTMCMC iterations in 33.9 min, acc. 0.34)

Pre-registered A2 comparison — **5/5 parameters agree** (needed ≥4):

| Parameter | Ours: median [68% CI] | Published MAP [68% CI] | Agree |
|---|---|---|---|
| EFAC | 1.050 [1.037, 1.064] | 1.05 [1.04, 1.06] | yes |
| log10 A_13/3 | -14.82 [-15.51, -14.47] | -14.82 [-16.39, -14.54] | yes |
| γ_SW | 1.74 [1.50, 2.01] | 1.81 [1.51, 1.99] | yes |
| log10 A_SW | -6.19 [-6.28, -6.10] | -6.16 [-6.26, -6.10] | yes |
| n_earth | 5.05 [3.04, 6.89] | 5.86 [3.54, 7.45] | yes |

Not just medians: the posterior **widths** match the published intervals nearly edge-for-edge
(e.g. A_SW CI edges within 0.01–0.02 dex), and the A_13/3 marginal reproduces the peak-plus-flat-tail
shape that explains the paper's asymmetric (-1.57, +0.28) interval. The solar-wind pair matching at
this precision also confirms the declared convention choices (linear-spaced harmonics; Hazboun-style
SW GP). Corner plot with published MAPs overlaid: `figures/w2_J2241-5236_corner.png`.

**Formal verdict per pre-registration: NOT-CONVERGED → feasibility result (A3).** The strict gate
required ≥5,000 post-burn chain samples; the run produced 2,256 (thin=10; = 22,550 post-burn raw
iterations) with the median-stability check **passing**. The gate as written keyed on thinned rows
— a registration lesson recorded for M2 (specify raw vs thinned next time). What this run
establishes regardless: the independent likelihood implementation (data handling, white-noise
kernels, GP bases, SW model) reproduces the collaboration's posterior for this pulsar; what it does
NOT establish: formal convergence diagnostics, evidences, model selection, or anything array-scale.

#### J1909-3744 (9 sampled parameters; 11,697 PTMCMC iterations)

Run history, honestly: the first attempt was killed at ~60 min by the session harness (task
ceiling), the relaunch's iteration budget was sized from a bench taken in the last minutes of the
host game (494 ms/eval) — the final clean run benched 436 ms/eval on the freed host and was sized
to 11,697 iterations ≈ 85 min, but sustained throughput fell to ~1.3 it/s under renewed host load:
**actual sampling wall-clock 155 min, exceeding the registered 90-min cap** (the cap was enforced
by iteration sizing, not a wall-clock abort — an M2 harness fix, recorded). Verdict unaffected:
the run lands on the A3 feasibility outcome either way.

Pre-registered A2 comparison — **5/9 agree** (needed ≥7):

| Parameter | Ours: median [68% CI] | Published MAP [68% CI] | Agree |
|---|---|---|---|
| EFAC | 1.028 [1.019, 1.042] | 1.04 [1.02, 1.04] | yes |
| log10 EQUAD (tn) | -7.185 [-7.202, -7.173] | -7.17 [-7.20, -7.17] | yes |
| log10 ECORR | -7.165 [-7.197, -7.131] | -7.17 [-7.23, -7.15] | yes |
| **log10 A_13/3** | **-14.288 [-14.414, -14.125]** | **-14.28 [-14.49, -14.11]** | **yes** |
| γ_DM | 2.75 [1.53, 3.38] | 2.04 [1.86, 2.32] | yes |
| log10 A_DM | -15.06 [-15.36, -14.01] | -13.60 [-13.67, -13.53] | **no** |
| γ_SW | 2.73 [2.46, 2.93] | 1.39 [0.97, 1.60] | **no** |
| log10 A_SW | -5.57 [-5.63, -5.50] | -6.43 [-6.62, -6.33] | **no** |
| n_earth | 22.3 [21.1, 22.8] | 4.96 [3.72, 5.82] | **no** |

The four disagreements are **one coupled block**: the chain parked in a solar-wind-dominated local
mode (n_earth railed at ~22 cm⁻³, SW GP inflated ~0.9 dex) with the DM GP correspondingly
suppressed — precisely the DM↔SW degeneracy the paper itself warns about (its §solar-wind text and
the J1327-0755 anecdote). J2241-5236's dead-on SW agreement rules out an SW-convention bug.

**Mode diagnostic (post-run, `scripts/w2_j1909_mode_diag.py`): our own likelihood scores the
published MAP at Δ lnL = +22.4 above the best point the 11.7k-iteration chain ever visited**
(97,306.1 vs 97,283.6). The likelihood implementation *prefers* the collaboration's DM-dominated
solution; the short chain simply never found the global mode. The J1909 chromatic-block
disagreement is therefore a **measured sampling shortfall, not a model error** — fully consistent
with (and anticipated by) the pre-registered A3 outcome:
**NOT-CONVERGED → feasibility result** (1,170 thinned rows; 878 post-burn; stability check fails
on the chromatic block). Corner: `figures/w2_J1909-3744_corner.png` (published values sit at/off
the panel edges of the chromatic trio; every other marginal has the red line through its peak).

Meanwhile the five agreeing parameters include everything a common-signal search consumes from
this pulsar: the three white-noise terms and — dead-on to 0.008 dex with matching CI widths —
**A_13/3, the pulsar's fixed-γ CURN-reference amplitude (ours -14.288, published -14.28)**, which
for the MPTA's best pulsar is the single most GW-relevant number in the table.

### 5.4 Runtime economics (decides W3)

Measured on this box (32-core WSL2; quiet-host numbers marked ✔, game-contended marked ⚠):

| Configuration | eval time | evals/s | Sustained PTMCMC |
|---|---|---|---|
| J2241-5236 single-pulsar noise, 5 params, 3,405 ToAs | 100 ms ⚠ | 10.0 | 14.8 it/s ⚠ |
| J1909-3744 single-pulsar noise, 9 params (SW GP + ECORR), 7,199 ToAs | 436 ms ✔ | 2.3 | 1.3 it/s ⚠ |
| J1909-class free-white (7 params, no SW) | 89 ms ✔ | 11.2 | — |
| **J1909-class fixed-white (TNT cached)** | **1.4 ms ✔** | **716** | — |

- **Fixed-white is 64× cheaper than free-white** — enterprise's TNT caching with constant N works
  as advertised. Projection: a full-83-pulsar CURN-style eval ≈ 0.12 s → **1M PTMCMC iterations
  ≈ 1.3 days** on this workstation (`results/w3_econ_J1909-3744.json`). A CURN (uncorrelated
  common) run keeps enterprise's dense per-pulsar branch — **no scikit-sparse needed**.
- All-83 single-pulsar noise campaign: at 0.1–0.4 s/eval and ~10⁵ iterations/pulsar, ≈ 3–12 h per
  pulsar sequential; 16-way parallel (30 GB RAM comfortably holds it) ≈ **~1 day wall-clock** for a
  first converged pass, ~1 week at 10⁶ iterations. Feasible.
- Hellings–Downs-correlated searches and CW: hit enterprise's sparse-CHOLMOD branch → require real
  scikit-sparse (the no-sudo shim forbids it loudly) via micromamba or sudo — **economics not yet
  measured; an M2 task, not an M1 promise.**
- Session lesson, now recorded for the M2 harness: size runs by **wall-clock abort**, not iteration
  count (host load changed 10× mid-session: a game occupied all cores for most of it); run
  campaigns when the host is idle; and pre-register sample-count gates in **raw iterations**, not
  thinned rows.

## 6. Recommended M2 (and the honest W3 pick)

**M2 — "converge and scale": noise models at scale + the factorised-likelihood CURN amplitude.**

1. Harness hardening (from §5.4 lessons): wall-clock abort + resume; idle-host scheduling; gates in
   raw iterations.
2. **Converge J1909-3744** — the mode diagnostic defines success: the chain must recover the
   published DM-dominated mode (which our likelihood already prefers by ΔlnL = 22). Target 9/9
   agreement or an explained residual.
3. Scale to the ~10 best-timed pulsars in parallel, comparing against the published table
   throughout (the M1 machinery does this per-pulsar automatically).
4. **Factorised-likelihood CURN amplitude**: every per-pulsar model already samples A_13/3; the FL
   product over pulsars reproduces the paper's headline `log10 A_CURN = -14.28 ± 0.21` **without**
   the full-PTA correlated likelihood — the paper's own primary method (its Fig. "CRN_FL" route),
   and it is embarrassingly parallel. M1 evidence it will work: both pulsars' A_13/3 posteriors
   already match the published table.

**W3 pick (economics-driven, in order):**
- **First product: cross-PTA noise-model criticism** — per-pulsar work (the regime this stack is
  now validated in), targeting the live chromatic/solar-wind misspecification fight; MPTA's
  SW-heavy models vs NANOGrav 15-yr public noise chains (chain-level on their side, no resampling).
  Plays directly to the house specialty (model criticism with controls).
- **Second: full-array CURN posterior as a ~days-scale background campaign** (1.3 d/1M iters
  measured, fixed-white; no sparse stack needed) — reproducing `-14.25^{+0.21}_{-0.36}`,
  `γ = 3.60` end-to-end.
- **Deferred: CW upper-limit map and HD-correlation work** until the scikit-sparse upgrade lands
  and its economics are measured. IPTA DR3 (~2027) readiness rides on the same per-pulsar
  parameterisation.
