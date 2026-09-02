# M5 — the activity axis with no footprint penalty, the southern dust closed, and the queue folded into the driver

*2026-08-18. Runs M4's own recommendations. Task 1 re-asks M4's underpowered X-ray
question using Gaia's own indicators, which cover **all 76** El-Badry 2026 targets
instead of eROSITA's 29 of 65 — three families, rules pre-registered, exact power
statements. Task 2 closes the four southern dust rows Bayestar19 could not see with
Vergely+2022. Task 3 makes the day-one epoch-vet queue fall out of the rehearsed driver
instead of a side script. Repo law: sourced-or-UNSOURCED; negative results are results;
rules pre-registered before running. Anonymous HTTP/FTP only; `../erosita-dr2/data/`
untouched this milestone. No accounts, no commits, no submissions.*

---

## 1. The activity axis without the footprint penalty (task 1)

**The premise M4 handed over, and what happened to it.** M4's recommendation #1 read:
"Gaia DR3 itself carries all-sky activity proxies — `activityindex_espcs` … and the
photometric-variability tables — testable against **all 65** EB26 verdicts today."
Half of that is true. The photometric proxies are genuinely all-sky. **ESP-CS is not
even close**, and that is the first result of this milestone.

**Design** (`scripts/m5_activity_discriminator.py`; the full rule set is pre-registered
in its docstring and was written to file before any confirmed-vs-spurious split was
computed). All 76 EB26 followed-up astrometric candidates
(42 CONFIRMED / 23 SPURIOUS / 1 MARGINAL / 2 NOT_CO / 1 OTHER / 7 UNKNOWN); primary
comparison CONFIRMED vs SPURIOUS. Three families kept separate, Holm–Bonferroni
**within** each family at α = 0.05, plus a negative control outside all families.
Continuous metrics: Mann-Whitney two-sided, ≥ 5 finite per side or NOT TESTABLE, effect
size = AUC(spurious > confirmed) with a 10,000-resample bootstrap CI. Binary metrics:
Fisher exact + Wilson. Power for every testable metric at the achieved n (MC for MWU,
exact binomial enumeration for Fisher — M4's routine).

**Footprint: 76 of 76.** That was the point.

| | M4 (eROSITA-DE) | M5 (Gaia's own columns) |
|---|---|---|
| verdicted targets visible | **29 of 65** (16 conf + 13 spur) | **65 of 65** |
| cost | a half-sky X-ray survey | one `gaia_source` column set |

### 1a. Family A — chromospheric activity: NOT TESTABLE, and that is the finding

`activityindex_espcs` (ESP-CS Ca II IRT index, `gaiadr3.astrophysical_parameters`)
exists for **7 of the 76** EB26 targets — **3 confirmed, 1 spurious, 3 unknown** — and
for **44 of the 1,199** candidate + retrieval + EB26 sources pulled. The ESP-CS module
*ran* on far more (`activityindex_espcs_input` is set on 431 of 1,199) but published a
value for ~10 % of them. Under the pre-registered ≥ 5-per-side rule this is **NOT
TESTABLE — not a null.** Nothing may be concluded about chromospheric activity from
DR3 for this sample, in either direction.

The whole family, because at n = 7 the table *is* the result:

| source_id | verdict | activityindex_espcs | ± | G |
|---|---|---|---|---|
| **6281177228434199296** | **SPURIOUS** | **0.0386** | 0.0014 | 11.26 |
| 5283631903842076032 | UNKNOWN | 0.0309 | 0.0020 | 13.31 |
| 5039979680444075392 | CONFIRMED | 0.0149 | 0.0022 | 12.72 |
| 5446310318525312768 | UNKNOWN | 0.0136 | 0.0005 | 10.37 |
| 6687541573416724608 | UNKNOWN | 0.0118 | 0.0017 | 12.07 |
| 1801110822095134848 | CONFIRMED | 0.0075 | 0.0014 | 12.19 |
| 5870569352746779008 (BH2) | CONFIRMED | −0.0015 | 0.0011 | 12.28 |

**Anecdote, n = 1, no test claimed**: the single EB26-SPURIOUS target with an ESP-CS
value is the most chromospherically active of the seven — and it is **6281177228434199296,
one of M4's two X-ray detections** (the class-III-on-the-AMRF-plane row already killed by
the frozen F2 screen). Two independent activity measurements agreeing on one object is a
coincidence you write down, not a result you publish.

### 1b. Family B — photometric variability: a measured, underpowered null

Metric, sourced: **Belokurov et al. 2017** (MNRAS 466, 4711), eq. 2 —
`arXiv:1611.04614`, `clouds_and_bridges.tex` source lines 490–492:

> Amp = log₁₀( √N_obs · σ_Ī_G / Ī_G )

with (lines 495–497) "*N_obs is the number of CCD crossings, σ_Ī_G is the mean G flux
error and Ī_G is the mean G-band flux*". In DR3 columns
`Amp_G = log10(sqrt(phot_g_n_obs) / phot_g_mean_flux_over_error)`. Belokurov et al. 2020
(MNRAS 496, 1922; `arXiv:2003.05467` src line 800) use the same estimator on DR2 and
report it "*nicely correlates with the peak-to-peak light curve amplitude measured by
Gaia*". Amp is strongly magnitude-dependent, so the primary metric is the detrended
residual **ΔAmp_G = Amp_G − median(Amp_G | G)**, the baseline being a rolling median
(±0.75 mag, ≥ 25 stars) over the 1,199-source NSS-candidate population pulled alongside.

| metric | conf median | spur median | MWU p | Holm | AUC(spur>conf) [95 % boot] |
|---|---|---|---|---|---|
| **ΔAmp_G** | −0.061 | +0.066 | **0.035** | 0.141 | **0.659 [0.507–0.805]** |
| ΔAmp_RP | −0.029 | +0.058 | 0.078 | 0.234 | 0.634 [0.484–0.772] |
| ΔAmp_BP | −0.088 | −0.114 | 0.886 | 1.000 | 0.511 [0.353–0.666] |
| `phot_variable_flag` = VARIABLE | 3/42 | 2/23 | 1.000 (Fisher) | 1.000 | OR 1.24 |
| `std_dev_mag_g_fov` | — | — | NOT TESTABLE (3 / 2; only **7 of 76** are in `vari_summary` at all) | | |

> **VERDICT: UNDERPOWERED. Power, computed at the achieved n (42 vs 23): the smallest
> AUC detectable at 80 % power is 0.725; the observed 0.659 sits below it, with a CI
> that touches 0.507.** Nothing enters the config.

Two things are worth carrying forward anyway. **The direction agrees with M4**: the
spurious side is the more photometrically variable one, exactly as the spurious side was
the X-ray-detected one (2/13 vs 0/16). Two independent activity axes, two consistent
directions, neither significant — that is a hypothesis with two weak legs, not a
discriminator. And **the sample it would take is now a number**: at the observed effect,
80 % power needs about **84 confirmed + 46 spurious**, ≈ 2× today's sample. The epoch-vet
loop adjudicates that many candidates in 72 hours.

### 1c. Family C — astrometric quality: this one works, and it points the other way

Family C is explicitly **not activity** — it is "was the single-star astrometry clean".
It was included as a separate family precisely so it could not launder itself into an
activity claim. It is the family that discriminates.

| metric | conf median | spur median | MWU p | Holm (m=6) | AUC(spur>conf) [95 % boot] |
|---|---|---|---|---|---|
| **`astrometric_gof_al`** | **86.7** | **47.1** | **0.0011** | **0.0067 ✓** | **0.254 [0.136–0.386]** |
| **`ruwe`** | **5.36** | **3.40** | **0.0083** | **0.041 ✓** | **0.300 [0.161–0.450]** |
| `astrometric_excess_noise_sig` | 377.9 | 161.2 | 0.025 | 0.100 | 0.330 [0.183–0.478] |
| `phot_bp_rp_excess_factor` | 1.202 | 1.209 | 0.506 | 1.000 | 0.551 |
| `ipd_frac_multi_peak` | 0 | 0 | 0.686 | 1.000 | 0.520 |
| `ipd_gof_harmonic_amplitude` | 0.0211 | 0.0196 | 0.962 | 1.000 | 0.504 |

**Direction, which is the interesting part: EB26-CONFIRMED compact-companion hosts are
the astrometrically *noisier* single-star fits.** A real massive dark companion makes a
large photocentre orbit, so the 5-parameter single-star model fits it badly. The naive
reading — "high RUWE means something is wrong, flag it" — has the sign backwards on this
population. This is the **measured** version of an assertion the config has carried since
v1: `ruwe_cut = "NONE — high RUWE is the orbit signature (BH1 7.6, BH2 9.2)"`. M2 asserted
it from two objects; M5 measures it against 65 verdicts at r_rb −0.40 (`ruwe`) and
−0.49 (`astrometric_gof_al`).

**Negative control**: `phot_g_n_obs` (scan-law geometry) p = 0.144 — clean. The
machinery is not manufacturing signal.

**Pre-registered confound guard, PASSED.** The two groups differ in G (13.72 vs 13.35,
p = 0.044) and distance (624 vs 924 pc, p = 0.034), so a G-median split was required:

| metric | bright (n 19/14) | faint (n 23/9) |
|---|---|---|
| `astrometric_gof_al` | AUC 0.252, p 0.017 | AUC 0.184, p 0.006 |
| `ruwe` | AUC 0.320, p 0.084 | AUC 0.174, p 0.005 |

Same direction in both halves for both metrics; `astrometric_gof_al` significant in both.

**Two caveats, both measured, both post-hoc, both in config v4.** These were added
*after* the confound table showed the group differences; they are reported as caveats
and did not alter the pre-registered decision rule.

1. **Redundancy with `significance`.** The two groups differ enormously in the NSS
   solution's own significance (46.1 vs 10.4, p ≈ 0) — and config v2 already ranks on it.
   A logistic fit of P(spurious) on z(log metric) + z(log significance) + z(G) + z(log d)
   over the 65 gives `log significance` β = −2.87 (p = 0.004) and leaves
   `astrometric_gof_al` at **p = 0.048** and `ruwe` at **p = 0.094**. The flag is largely
   a restatement of a tier the pipeline already has. It breaks ties; it is not an
   independent axis and must never be quoted alongside significance as if it were.
2. **In-list yield: 0 of 7.** Of the 46 EB26-verdicted rows that actually survive the
   frozen screen and sit in the candidate list, the flag marks **2**, and catches **0 of
   the 7 in-list EB26-spurious**. The discrimination was measured across all 65 verdicted
   targets, most of which the screen already removes; on the surviving population it has
   no measured power. **Do not present it as a purity gain.**

**What entered the config.** One flag, the stronger metric only:
`flag_astrom_quiet` = `astrometric_gof_al` below the **25th percentile of the day's own
main candidate bin** (no threshold is fitted to the EB26 verdicts; the cut is a
self-calibrating quartile — 237 of 949 rows on DR3, threshold 36.39). Caution tag and
ranking tiebreaker; **never a cut, never a selection change.** `ruwe` also survives Holm
in the same direction and is deliberately *not* frozen — one flag, not two correlated
ones.

> **HEADLINE ANSWER to the milestone's question: the activity axis still does not
> discriminate — now with the footprint excuse removed.** Chromospheric activity is
> untestable at DR3 coverage (7/76); photometric variability is an underpowered null
> (AUC 0.659 against the 0.725 this n can see), pointing the same way M4's X-ray axis
> pointed. What *does* discriminate is astrometric quality, in the opposite direction,
> and mostly by restating the significance tier the config already ranks on.

## 2. Southern dust closure (task 2) — all four resolved, 0 movements

M4 arbitrated 13 dust-ambiguous far-star rows with Bayestar19 and left **4 south of
dec −30** bracketed and flagged. Bayestar19 has a declination edge; **Vergely, Lallement
& Cox 2022** has only a box edge.

**The product, verified before use** (`scripts/m5_fetch_vergely2022.py`; CDS
J/A+A/664/A174 = 2022A&A...664A.174V, anonymous FTP — the HTTPS view of the same tree
sits behind an Anubis proof-of-work bot check and intermittently refuses plain clients;
anonymous FTP serves the identical files with no challenge, and none was solved):

- ReadMe *Description*: "3D distribution of extinction density at 550nm in a 6kpc by 6kpc
  by 0.8kpc volume around the Sun … Cartesian … Sun at centre X,Y,Z=0,0,0. The X axis is
  directed to the Galactic Centre, the Y axis is along the direction of rotation, and the
  Z axis points to the Northern Galactic Pole."
- ReadMe *Caution*: "read the article for assumptions during the inversion (especially
  the resolution) and errors at large distances or beyond very dense structures."
- FITS headers are self-describing: `UNIT = 'A0(550nm)/parsec'`, `STEP`/`RESOL` 10/25 pc
  (601×601×81) and 20/50 pc (501×501×41, **with a matching density-error cube**),
  `SUN_POSX/Y/Z`. **The cubes are already mag/pc** — the ReadMe's "nanomagnitude per
  parsec" describes the 7.5 GB ASCII `cube_ext.dat`, which we do not download.
- The quantity is monochromatic **A₀ at 550 nm**: arXiv:2205.09087 `3DINTERCAL.tex`
  source line 162, "*The photometric catalogue provides monochromatic extinctions A₀ at
  550 nm, while the spectroscopic catalogues estimate A_V … Both quantities are very
  similar.*"

**Unit chain — one link, and it is the curve the house already uses**, so the arbitration
compares maps rather than coefficient conventions (M4's requirement of Bayestar19,
applied again):

> **E(ZGR23) = A₀(550 nm) / R_ZGR23(550 nm)**, R_ZGR23(550) = **2.6798** (ZGR23 curve,
> `data/papers/zgr23_curve/extinction_curve.txt`, Zenodo 7692680/7811871, linearly
> interpolated — the same table that supplies R_G/R_BP/R_RP/R_V to `dust3d.py`).
> Then Gaia bands via the ZGR23 ratios, exactly as the Edenhofer and SFD tiers.
> ⇒ A_G per mag A₀ = 0.848 (house). **Cross-check chain run in parallel** (M4's rule
> that a verdict counts only if both chains agree): treat A₀ ≈ A_V, convert with SF11's
> A_V = 2.742 E(B−V), apply El-Badry+2026's A_G = 2.66 E(B−V) ⇒ 0.970 per mag A₀ —
> 14 % steeper. **Both chains agree on all 13 rows.**

**Pre-registered geometry gate** (`out/m5_vergely_geometry_gate.txt`). The reader is new
code and a swapped axis would produce plausible-looking numbers, so the convention had to
*beat* its corruptions before being used, on 4,000 seeded candidate sightlines with
200 ≤ d ≤ 1250 pc (inside both maps):

| gate | requirement | measured |
|---|---|---|
| G1 declared convention vs X↔Y swap / X flip / Y flip, Spearman ρ against Edenhofer23 | margin ≥ 0.20 | **ρ 0.9656 vs 0.4113 / 0.3840 / 0.3964 — margin +0.554** |
| G2 median E_V22 / E_Edenhofer | ∈ [0.5, 2.0] | **1.010** (10–90 %: 0.706–1.457) |
| G3 median E_V22(25 pc) / E_V22(50 pc) | ∈ [0.8, 1.25] | **0.977** |

**Control before conclusion**: on the 9 rows Bayestar19 already arbitrated, V22
reproduces B19's class-III verdict at the central value **9 of 9** on both chains
(median E_V22/E_B19 = 1.253 — V22 runs ~25 % higher on these low-|b| far sightlines).
Only then are the southern rows read.

**The four southern rows** (E in ZGR23-equivalent units; ±1 σ from the map's own error
cube, integrated with fully-correlated errors, i.e. deliberately maximal):

| source_id | dec | d [pc] | E Edenhofer floor | **E V22** | E SFD ceiling | class (house / EB26) | verdict |
|---|---|---|---|---|---|---|---|
| 5541388898616068224 | −36.6 | 2281 | 0.214 | **0.304 ± 0.040** | 0.997 | 3 / 3 | **SURVIVES** |
| 5547414810758429056 | −33.5 | 2838 | 0.307 | **0.381 ± 0.052** | 0.845 | 3 / 3 | **SURVIVES** |
| 5858664081383081600 | −65.7 | 2506 | 0.241 | **0.316 ± 0.015** | 0.883 | 3 / 3 | **SURVIVES** |
| 5984963087901124352 | −46.4 | 1643 | 0.563 | **0.523 ± 0.050** | 1.144 | 3 / 3 | **SURVIVES** |

Same story M4 found in the north: the true 3D column sits near the Edenhofer floor and
far below the SFD 2D ceiling, because most of the SFD column on these low-|b| sightlines
is dust *behind* the star. The SFD ceiling was the pessimist.

**Summary over all 13**: **12 SURVIVE class III on both chains, 0 die, 1 σ-fragile,
0 unresolved.** `flag_dust_unresolved_south` goes from 4 to **0**. Membership movements:
**0** — the v2 list (949) stands, no v3 CSV, `amrf_class3_candidates_v2.csv` untouched.

**The one new caveat, honestly earned.** Row **4161042729638132096** (the highest-column
row, E = 1.29 against an SFD ceiling of 1.49) is class III at the central value on both
chains — agreeing with B19 — but flips to class 2 at **+1 σ** of the V22 error cube. M4's
Bayestar pass never applied a ±1 σ test, so this is a new test finding a new fragility,
not a disagreement between maps. It is flagged `flag_dust_sigma_fragile` in the queue,
not frozen either way — and it is not a tail object: it rides at **rank 27 of 981** with
M₂_min = 2.30 M☉, squarely in the NS range. It goes to the front of the epoch-vet line.

## 3. Acceptance re-run and config v4

The acceptance gates the config write, as in M4 (`scripts/m5_acceptance_and_queue.py`):

- **Gaia BH1**: present, Pr(III|corr) = 1.0000, M₂_min = 12.81 — **PASS**
- **Gaia BH2**: present, Pr(III|corr) = 1.0000, M₂_min = 9.76 — **PASS**
- top-2 by M₂_min = BH1 + BH2 — **PASS**
- **EB26 operating point re-measured: 39/42 confirmed kept, 7/23 spurious passed** —
  identical to the frozen M2 numbers, as it must be (membership unchanged).
- negative control clean (p = 0.144) — a run whose negative control fired at p < 0.01
  would have been voided before anything was written.

**`queries/dr4-triage-config.v4.json`** (v1, v2, v3 untouched on disk). Selection,
screen, probability method and membership **identical to v2/v3 — 949 rows**. What v4
adds:

1. `extinction_tier.d_gt_1250pc` rewritten: far stars are arbitrated by *whichever far 3D
   map covers the sightline* — Bayestar19 north of −30 (M4) **and Vergely+2022 all-sky**
   (M5) — with the σ-fragile flag; v3's "south of −30 stays bracketed and flagged" is
   superseded and had to be, because it is no longer true.
2. `extinction_tier.vergely2022_chain`: the full sourced chain above plus the geometry
   gate's numbers.
3. `activity_policy`: **no activity flag enters the config**, with family A's coverage
   (7/76), family B's power numbers, and the direction agreement with M4 on record.
4. `astrometric_quality_flag`: `flag_astrom_quiet`, its definition, its evidence, and
   both caveats (redundancy with `significance`; 0-of-7 in-list yield) in the config
   itself, so nobody reads the flag without them.

## 4. Runbook hardening (task 3)

**The queue now falls out of the driver.** `scripts/m5_day1_queue.py` is a single shared
builder; `scripts/rehearse_dr4_day.py` **stage H** calls it on the rehearsal's own triage
output, and `scripts/m5_acceptance_and_queue.py` calls it on the production v2 list. The
builder asserts the BH1/BH2 acceptance itself and refuses to write a queue that has lost
them. December 2 no longer depends on anyone remembering to run a second script.

Production queue: **`out/epoch_vet_day1_queue.v2.csv`** — 981 rows (949 + 32), ranks 1–2
BH1/BH2, rank 3 the EB26-refuted spurious poster child, `flag_dust_unresolved_south`
4 → **0**, plus the new `flag_dust_sigma_fragile` (1, at rank 27) and
`flag_astrom_quiet` (255 of 981). M4's `out/epoch_vet_day1_queue.csv` is left
byte-identical (versioned-outputs law).

**Rehearsal, re-run** (timings in `out/rehearsal_timings.csv`, now with a `note` column;
the driver takes `--stages` so a partial run is recorded as partial and can never be
mistaken for a green one):

| stage | seconds | status | note |
|---|---|---|---|
| A — schema pin | **179.1** | OK | ESAC's `TAP_SCHEMA` path was unusable; introspection failed over to **ari**, then ESAC recovered mid-stage — served by both |
| B — rename patch + live TOP-5 probe | **290.9** | OK | one HTTP 500, retried; 5 rows / 38 cols |
| C — plan-B ranged pull | **632.3** | OK | **RESUMED from 94 cached chunks** — this timing is cache validation + live histogram + live exact-`COUNT(*)`, not a fresh pull. Result **byte-identical again**: sha256 `b3b099a6…dddd5231`, 169,227 rows, id-sum match |
| D — triage + BH1/BH2 acceptance | **43.6** | **PASS** | BH1 class III margin 3.38×, BH2 2.44×, both Pr 1.0000 |
| E — corr_vec (measured, not re-run) | 74 + 10 | OK(measured) | politeness; identical bytes |
| F — epoch-vet loop | **3.4** | **PASS** | 3/3 kept, 9/9 demoted |
| G — bulletin | 0.2 | OK | 951 candidates |
| **H — day-one queue (new)** | **0.1** | **PASS** | 983 rows, BH1/BH2 top-2 asserted inside the builder |
| **total driver** | **1,150 s ≈ 19 min** | **COMPLETE** | vs M3's 40 min — the difference is entirely stage C resuming from cache, offset by ~8 min of archive retries in A and B |

An earlier attempt the same evening had to be abandoned: with ESAC-only schema queries at a 300 s timeout, stage A spent ten minutes and three retries getting `TAP_SCHEMA.schemas` to answer once and then stalled. The driver now also takes `--stages`, so a run that skips the network stages is written into the timings CSV as `SKIPPED` with the reason — **a partial rehearsal cannot be mistaken for a green one.** (That path was exercised too: `--stages DEFGH` ran green while ESAC was down.)

Stage H is the new one and it does what it was built to do: from the rehearsal's own
triage output it assembles **983 rows** (951 pre-dust main + the retrieval bin's 32 at
Pr ≥ 0.999), computes `flag_astrom_quiet` from the day's own quartile (threshold 36.36;
256 rows), carries all seven caution flags, ranks BH1 and BH2 first and second, and passes
the acceptance assertion that lives *inside* the builder. It differs from the production
queue's 981 by exactly the two dust movers, because the rehearsal driver stops before the
Phase-2 dust re-triage — stated in the stage's own output rather than smoothed over.

**The archive itself was the day's biggest operational finding.** ESAC's TAP sync
endpoint spent 2026-08-18 alternating between 30–80 s replies, **HTTP 500**, and 90 s
read-timeouts — *on one-row indexed queries*. Two official Gaia partner-data-centre DR3
mirrors answered the identical ADQL in 0.6–2 s throughout:
`https://gaia.ari.uni-heidelberg.de/tap/sync` (CSV) and `https://gaia.aip.de/tap/sync`
(**ignores `FORMAT=csv` and returns VOTable**). ARI reproduced ESAC's `ruwe`,
`phot_g_mean_mag` and `ipd_frac_multi_peak` for all 76 EB26 targets to **0.000e+00**
relative — a mirror validation gate that now runs before any mirror is trusted. Folded
into the runbook: a Phase-0.0 endpoint probe with the mirror table and the validation
gate, a failure branch, and **6× retry with backoff in every sync helper**
(`pull_dr3_nss_orbits_ranged.py`, `rehearse_dr4_day.py`) — a 94-request pull cannot
survive a no-retry policy against an archive in that state.

The rehearsal then had to survive it in practice, and the line drawn is the interesting
part. ESAC's `TAP_SCHEMA` path was effectively unusable (the first rehearsal attempt spent
ten minutes and three retries getting `TAP_SCHEMA.schemas` to answer once, then stalled on
the first `TAP_SCHEMA.columns` query and was abandoned). **Stage A — schema introspection
only — was given endpoint failover; stages B and C, the data path, were deliberately not.**
Asking "does column X exist in `gaiadr3`" is answered identically by a DR3 mirror; pulling
the rows is not, because the rehearsal parquet has to stay byte-identical to the M2/M3
production pull, and **on 2026-12-02 only ESAC will have DR4 at all**. The distinction is
written into the code as a comment and into which helper each stage calls
(`sync_csv_schema` vs `sync_csv`), and the timings CSV records when failover actually
fired. **The caveat that matters for December**: the mirrors host DR3 and will not have
DR4 on release day. They rescue the DR3-side work; the DR4 pull has no mirror, and its
only defences are the retry and the fact that the ranged pull is resumable.

Runbook also updated: Phase 2's dust step now runs both far maps and the geometry gate;
Phase 3 gains step 5 (the Gaia-indicator pull with the M5 DR3 baselines and the
sign warning on RUWE); the first-24 h list gains the indicator table, the all-sky dust
arbitration line and the driver-emitted queue; the 72-h list gains "re-run the M5 test on
day-one epoch-vet verdicts" with the 84 + 46 target.

## 5. Files

| artifact | what |
|---|---|
| `scripts/m5_pull_activity_columns.py` | the activity/variability/quality pull (endpoint failover + mirror validation gate) → `data/dr3_activity_columns.parquet` + NOTE |
| `scripts/m5_activity_discriminator.py` | the three-family test, rules pre-registered in the docstring → `out/m5_activity_eb26_table.csv`, `out/m5_activity_metric_results.csv`, `out/m5_activity_discriminator_stats.txt` |
| `scripts/m5_fetch_vergely2022.py` | anonymous-FTP fetch of the V22 cubes + ReadMe/list.dat → `data/dustmaps/vergely2022/` (gitignored) |
| `scripts/m5_vergely_south.py` | the V22 line-of-sight integrator, the pre-registered geometry gate, and the southern arbitration → `out/m5_vergely_dust_south.csv`, `out/m5_vergely_geometry_gate.txt` |
| `scripts/m5_day1_queue.py` | the shared queue builder (acceptance asserted inside) |
| `scripts/m5_acceptance_and_queue.py` | acceptance re-run → gates the queue + config write → `out/epoch_vet_day1_queue.v2.csv`, `queries/dr4-triage-config.v4.json` |
| `scripts/rehearse_dr4_day.py` | **stage H added**; retry-hardened `sync_csv`; cache-resume noted in the timings |
| `scripts/pull_dr3_nss_orbits_ranged.py` | retry-hardened `sync_csv` (behaviour unchanged; every range still count-checked) |
| `data/papers/2205.09087/`, `1611.04614/`, `2003.05467/` | Vergely+22, Belokurov+17 (the Amp definition), Belokurov+20 LaTeX sources |

M2/M3/M4 outputs untouched: `amrf_class3_candidates.csv`, `…_v2.csv`,
`epoch_vet_day1_queue.csv`, `m4_bayestar_dozen.csv` and configs v1–v3 are all as their
milestones left them.

## 6. Corrections and new landmines

1. **M4's recommendation #1 rested on a false premise, corrected here**:
   `activityindex_espcs` is *not* an all-sky proxy usable on this sample — 7 of 76 EB26
   targets, 44 of 1,199 candidates. The chromospheric axis is untestable in DR3, not null.
2. **The sign of the astrometric-quality signal is opposite to intuition**: EB26-confirmed
   compact-companion hosts have *higher* RUWE and *higher* `astrometric_gof_al` than
   spurious solutions. Anyone reaching for "high RUWE = suspicious" on an NSS candidate
   list has it backwards.
3. **The ESAC TAP endpoint can be effectively down for hours** (HTTP 500 / 90 s timeouts
   on trivial indexed queries, 2026-08-18) while the ARI and AIP DR3 mirrors are healthy.
   New landmine, new failure branch, retries added.
4. **`gaia.aip.de` ignores `FORMAT=csv`** and returns VOTable regardless — an endpoint
   probe must check the *body*, not just HTTP 200.
5. **CDS's HTTPS `/ftp/` tree is behind an Anubis proof-of-work bot check** (2026-08-18)
   and intermittently refuses plain clients; **anonymous FTP to `cdsarc.cds.unistra.fr`
   serves the identical files with no challenge.** No challenge was solved.
6. **The Vergely+2022 FITS cubes are in mag/pc, not the ReadMe's nanomag/pc** — that unit
   applies to the ASCII `cube_ext.dat`. The FITS `UNIT` keyword is authoritative; trusting
   the ReadMe would have produced a 10⁹ error that the geometry gate's G2 would have
   caught, which is why G2 exists.
7. **`SUN_POSX/Y/Z` are pixel-edge coordinates**: the Sun sits at 0-based index
   `SUN_POS − 0.5` (601-pixel axis, SUN 300.5 → index 300, the exact middle). Off by one
   half-pixel is 5 pc; off by one convention is the whole map.
8. **`vari_summary` covers 7 of 76** EB26 targets (91 of 1,199) — the variability
   statistics are for pipeline-selected variables, not a general-purpose scatter table.
   `phot_variable_flag` is `NOT_AVAILABLE` for 69 of 76.
9. **The EB26 fixture and the triage parquet both carry `significance`** — a naive merge
   silently produces `significance_x`/`significance_y` and a `KeyError` three functions
   later. Rename before merging.

## 7. Recommended M6

1. **Stop asking DR3 and build the day-one measurement instead.** Every axis tried so far
   — X-ray (M4), chromospheric, photometric variability (M5) — is either footprint-,
   coverage-, or power-limited on 65 verdicts. The one machine that produces verdicts at
   scale is the epoch-vet loop. M6 should build the **verdict-harvesting harness**: run
   the loop against the pre-release epoch file at full queue scale, define the day-one
   verdict schema, and wire the M4 + M5 tests to consume it automatically so that on
   2026-12-03 the discriminator questions are re-asked with 2–10× the sample and no new
   code.
2. **Close `astrometric_gof_al` properly or drop it.** It survived Holm and passed the
   confound guard but catches 0 of 7 in-list spurious and mostly restates `significance`.
   A single well-designed test on day-one verdicts settles whether `flag_astrom_quiet`
   earns its column or should be removed in v5 — either outcome is publishable-grade
   methodology and both are cheap.
3. **The σ-fragile row and the 55 high-σ_TI² rows** are now the only knowingly-soft
   membership in the list. Epoch-vet them first when DR4 epoch astrometry exists; until
   then they are flagged, not fixed.
4. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew) — and note that the
   async-quota branch matters more after watching the anonymous endpoint behave the way
   it did today.
