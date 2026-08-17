# M3 — covariance-aware probabilities, the dust tier, the December-2 dress rehearsal, and the eROSITA join

*2026-08-16. Closes the two knowingly-open M2 seams (corr_vec-free MC; extinction-free
tier-2 M₁), rehearses the day-one pipeline end-to-end against DR3 as-if-DR4, and runs the
first genuinely new cross: the class-III candidate list × eROSITA-DE DR2. Repo law:
sourced-or-UNSOURCED; negative results are results. Anonymous TAP + anonymous HTTP only;
`../erosita-dr2/data/` consumed strictly READ-ONLY.*

---

## 1. corr_vec → honest Pr(class III)  (task 1)

**Reference implementation.** `nsstools` **0.1.12** (PyPI, verified 2026-08-16; latest of
13 releases; homepage gitlab.obspm.fr/gaia/nsstools; authors Halbwachs, Babusiaux,
Leclerc — the DPAC NSS tooling). `NssSource(row).covmat()` rebuilds the full fitted-parameter
covariance from `corr_vec` × published errors, **encoding the per-type parameter order**
(`Orbital`: …ecc, P, t_peri; `OrbitalAlternative*/TargetedSearch*`: …P, ecc, t_peri;
`AstroSpectroSB1`: …com_velocity, ecc, P, t_peri — the ordering subtlety is exactly why the
task pinned this package). Installed into `.venv`; version printed at runtime by
`scripts/corrvec_probs.py`.

**Data.** `scripts/pull_dr3_nss_corrvec.py`: targeted sync-VOTable pull (corr_vec is an
array column; CSV would mangle it) of all 34 nsstools-consumable columns for **4,203
solution rows** = 951 class-III ∪ 239 retrieval ∪ 76 El-Badry ∪ 3,000-source seeded
validation sample (S23 table1 × triage parquet, `binary_masses` tier, seed 20261202).
11 chunks ≤ 400 ids, 0.5 s gaps, **74 s total**; exact-count-guarded against the M2 parquet
(4,203 = 4,203, dual-solution sources return both rows). Landmine logged: the Gaia archive
returns `source_id` as **`SOURCE_ID`** in VOTable output (lower-cased on ingest).
Observed corr_vec lengths: 66 (12-param `Orbital`) and 105 (15-param `AstroSpectroSB1`) —
exactly the nsstools layouts; the count check passed on **4,203/4,203** (nsstools filters
exact-zero entries, which would break the count — none occurred).

**Propagation** (`scripts/corrvec_probs.py`): per row, the 6×6 block over
(ϖ, A, B, F, G, P) + mean vector → 10⁴ multivariate-normal draws (Cholesky succeeded on
4,203/4,203; the eigenvalue-clip fallback never fired) → a₀ per draw (Halbwachs eq. 12–14)
→ M₁ per the M2 tier policy, with one improvement: **tier-2 M₁ is now recomputed per draw
from the drawn parallax** (the M₁–ϖ coupling M2 ignored; 10 % scatter retained) → 𝒜 vs the
frozen ×1.15 boundary. Validation rows use 2×10³ draws.

**Three independent checks, all pass:**

| check | result |
|---|---|
| covmat diagonal == published errors² | 4,203/4,203 exact |
| nsstools `campbell()` a₀/σ(a₀) vs archive `significance` | median ratio **1.0000** (10–90 %: 0.923–1.000) — the covariance machinery reproduces the archive's own significance |
| σ(𝒜) vs S23's covariance-aware `e_A` (3,002 validation rows) | median ratio **1.027** — the M2 overestimate is closed (M2 measured 2.27× on its full shared-source sample; the independent-error twin on *this* validation sample: 1.65×) |

**The residual tail, diagnosed to its mechanism.** The validation ratio has a fat right
tail (90 % at 2.84). It is *not* the M₁-scatter term (removing it: tail unchanged) and
*not* an implementation error: it is confined to solutions whose individual Thiele-Innes
coefficients are barely constrained while their *combination* is (near-circular and/or
near-1-yr orbits — the classic TI degeneracy; worst-case example: A = 1.83 ± 2.87 mas yet
significance 92.6). There a Gaussian draw in TI space travels far along the degenerate
direction and the nonlinear a₀ inflates: MC-σ ≫ linearized-σ, and S23's `e_A` is evidently
the linearized (local) error. **The marker is S23's own σ_TI²** (measured on validation):

| σ_TI² bin | n | median σ(𝒜)_corr/e_A | 90 % |
|---|---|---|---|
| < 5 | 2,421 | **1.011** | 1.94 |
| 5–20 | 442 | 1.54 | 7.1 |
| 20–36 | 139 | 2.00 | 10.0 |

The candidate list lives in the validated regime (median σ_TI² = 0.95; 55 of 949 rows
above 20 — for those, `p_class3_corr` is *conservative*: over-spread pulls high
probabilities down, never up past truth). Documented, not patched.

**Effect on the census** (M2 M₁, before dust; `data/dr3_corrvec_probs.parquet`):

- **Harden**: of the 951, **293 now reach Pr(III) ≥ 99.9 %** vs 147 under M2's
  independent-error MC — the honest covariance *doubles* the high-purity core
  (404 at ≥ 99 %, 664 at ≥ 90 %).
- **Dissolve**: **0** of 951 fall below Pr 50 % (M2's diagnostic had 2 — both recover
  under the true covariance). Median Δ(corr − indep) = **+0.017**: the M2 MC was, as
  suspected, a pessimistic diagnostic.
- **Retrieval bin** (239 low-significance): **32 at Pr ≥ 99.9 %**, median 0.90 — headed
  by **1007185297091149824 at Pr = 0.9997**, the EB26-confirmed probable NS (sig 9.8)
  that the significance screen costs (M2 §5): the covariance MC now *quantifies* why the
  epoch-vet loop must re-adjudicate this bin on day one.
- **Gaia BH1 / BH2**: Pr(III|corr) = **1.0000 / 1.0000**; BH1 σ(𝒜) = 0.178 vs S23's
  published 0.174 (M2's uncorrelated 0.165).

**Operating point: a clean negative result.** Adding a Pr(III|corr) threshold to the
frozen screen, measured on the EB26 verdicts (`out/corrvec_eb26_operating_point.csv`):

| screen | confirmed kept /42 | spurious passed /23 |
|---|---|---|
| frozen (M2) | 39 | 7 |
| + Pr ≥ 0.5 | 39 | 7 |
| + Pr ≥ 0.9 | 38 | 7 |
| + Pr ≥ 0.99 | 35 | 7 |
| + Pr ≥ 0.999 | 32 | 6 |

Pr thresholds shed confirmed systems without killing spurious ones — El-Badry's "no simple
set of cuts" holds against honest probabilities too, because the surviving spurious
solutions have *precise wrong orbits*: of the 7 in-list EB26-spurious, **6 sit at
Pr ≥ 0.999 (median 1.0000, min 0.9965)** — including the list's #3, refuted
3509370326763016704 at Pr = 1.0000 — while the 39 in-list confirmed span down to 0.8687
(32 at ≥ 0.999). A probability computed from a wrong orbit is confidently wrong. **The
frozen screen is unchanged; Pr(III|corr) enters config v2 as a priority/ranking tier, not
a cut.** The false-positive killer remains the epoch-vet loop.

## 2. The dust tier for M₁  (task 2)

**What extinction can and cannot move.** Of the 951, only the **168** rows with
photometry-dependent M₁ (27 `photometric_ms` + 141 `evolved_bracket`) are movable;
**783 are `binary_masses` tier** (DPAC IsocLum M₁ — its own extinction treatment,
documented limitation). Consequently the "270-flag reservoir" was always smaller than its
flag count: **only 91 of the 270** low-|b| class-III rows are photometry-dependent.

**Per-star map choice, justified by geometry** (`scripts/dust3d.py` +
`scripts/dust_retriage.py`; scope = all 22,256 screened photometry-dependent rows + the
951):

| tier | rows in scope | map |
|---|---|---|
| 69 ≤ d ≤ 1250 pc | 17,519 | **Edenhofer et al. 2023** 3D mean map (the only *all-sky* 3D map covering the sample — no declination split needed inside its volume; NSIDE 256, 516 radial bins, mean_and_std_healpix.fits, Zenodo 8187943, md5-verified) |
| d < 69 pc | 54 | linear ramp of Edenhofer's integrated inner column (extinction ≈ 0 there) |
| d > 1250 pc | 5,466 | **bracketed, not guessed**: lower = Edenhofer to its edge (misses background dust); upper = SFD98 full 2D column (counts background dust — the overestimate direction for foreground stars; additionally unreliable at \|b\| < 5°, flagged). **Bayestar19 deliberately not used**: north-only (dec > −30° covers just 2,756 of the 5,466) and its unit chain to Gaia bands would add an unsourced link; the set it could arbitrate is instead *counted* (12 rows, below). |

Windows landmine: healpy has no build (dustmaps hard-depends on it) → the Edenhofer reader
replicates dustmaps 1.0.14 `edenhofer2023.py` with `astropy_healpix` bilinear weights
(6 s load+integrate). Second landmine: the dustmaps docstring cites the ZGR23 extinction
curve at DOI 10.5281/zenodo.**6674521**, which resolves to *GaiaXPy* — the real curve is at
Zenodo **7692680/7811871** (`extinction_curve.txt`, local copy `data/papers/zgr23_curve/`).

**Unit chain, every constant sourced.** Map unit E(ZGR23) → A_λ = R(λ)·E with the ZGR23
curve at the Gaia EDR3 pivot wavelengths (Riello et al. 2021): **R_G = 2.2732,
R_BP = 3.0362, R_RP = 1.6480**, R_V(540 nm) = 2.7791 — reproducing the paper's rounded
"×2.8 → A_V" (Edenhofer et al. 2024, A&A 685 A82, arXiv:2308.01295 source line 591,
archived to `data/papers/2308.01295/`). SFD tier: raw E(B−V)_SFD98 (sfdmap2, scaling=1.0
to avoid the package's silent 0.86 recalibration) × **2.742** = A_V (Schlafly & Finkbeiner
2011, Table 6, F99 R_V = 3.1), then the same ZGR23 band ratios. Point-evaluation at pivots
≈ band-integrated coefficients at the few-% level (documented approximation). External
cross-check: on the 53-source EB26 overlap, my E(B−V)-equivalent vs their `ebv` column:
median ratio 1.095 (10–90 %: 0.54–2.24) — same scale, no systematic disaster.

**Re-triage movements** (photometry-dependent rows; `out/dust_movements_summary.csv`):

| bound | class-III before | out | out at low-\|b\| | in | class-III after |
|---|---|---|---|---|---|
| lower (= best estimate ≤ 1.25 kpc) | 168 | **8** | 5 | **6** | 166 |
| upper (SFD for far stars) | 168 | 20 | 17 | 5 | 153 |

- The 8 movers-out are tier-2 stars whose de-reddened M₁ rose (e.g. 0.90 → 1.48 M☉),
  margins 1.00–1.26 → below 1; all marginal candidates, none in the top ranks.
- The 6 movers-in are the subtler mechanism, predicted by the reddening geometry: the
  CMD cut line (slope 13.42) is much steeper than the reddening vector (≈ 1.64), so
  **reddening pushes MS stars off the MS cut into the evolved bracket**; de-reddening
  returns them to tier-2 point masses (1.32–1.84 M☉) whose class is III where the
  bracket's worst case said II. All six are thin-margin (1.001–1.065) NS-range
  (M₂_min 1.7–1.9 M☉) additions — and the covariance MC prices that honestly:
  one (4481997904678998912, margin 1.0015) lands at Pr(III) = 0.495. Tier switches in
  scope overall: 4,654 bracket→MS, 97 MS→bracket.
- **Dust-ambiguous: 12** far-star class-III rows survive the Edenhofer floor but die
  under the SFD full column — the set a far 3D map would arbitrate; kept in v2 with
  `class_det_dust_upper` = 2 on record. 900 of 5,466 far sightlines have SFD *below* the
  Edenhofer floor (map tension at low \|b\|, where SFD is known-unreliable; upper bound
  clamped to the floor there).
- **The flagged-reservoir verdict**: of the 270 low-\|b\| candidates, extinction can move
  only 91; the honest correction kills **5** of them (17 under the far-star upper bound).
  The reservoir was real but ~4× smaller than the flag count implied — most flagged rows
  are `binary_masses`-tier and immune to *our* photometry. Gaia BH2 (evolved bracket,
  A_G = 0.41 mag): class III at every bracket mass, untouched. BH1 (`binary_masses`):
  immune by tier.

**v2 list** (`scripts/build_v2_list.py` → `out/amrf_class3_candidates_v2.csv`; M2's
951-row CSV untouched): membership under the dust lower bound = **949 rows**
(951 − 8 + 6); corr_vec mini-pulled for the 6 entrants; Pr recomputed with dust-corrected
inputs for the 29 rows whose M₁ inputs changed. **292 of 949 at Pr ≥ 99.9 %.** Ranked by
M₂_min the top three are unchanged: **BH1 (12.81 M☉, Pr 1.0000), BH2 (9.76, 1.0000)** —
and #3 is still the EB26-refuted spurious at Pr 1.0000, the epoch-vet poster child.

## 3. December-2 dress rehearsal  (task 3)

`scripts/rehearse_dr4_day.py` ran the frozen pipeline end-to-end against DR3 *as if it
were DR4*, into `data/rehearsal/` (M2 production artifacts untouched). Stage semantics and
timings (also `out/rehearsal_timings.csv`):

| stage | rehearsed | status |
|---|---|---|
| A — schema pin (TAP_SCHEMA, 3 tables, column diff) | 7.5 s | OK |
| B — rename-map patch of the DR4 query + live TOP-5 probe | 2.1 s | OK |
| C — plan-B ranged pull, full scale (94 ranges, 169,227 rows) | **2,323 s (38.7 min)** | OK |
| D — AMRF triage + **BH1/BH2 acceptance gate** | 64.5 s | **PASS** |
| E — corr_vec pull + covariance MC (measured same day, not re-run) | 74 s + 10 s | OK |
| F — epoch-vet loop (pre-release file, f2 gate) | 6.5 s | **PASS** (3/3 kept, 9/9 demoted) |
| G — day-one bulletin CSV | 0.2 s | OK |
| **total driver** | **2,404 s ≈ 40 min** | OK |

Two findings worth the rehearsal by themselves: (i) the rehearsal pull is
**byte-identical to the M2 production pull** (same sha256,
`b3b099a6…dddd5231`) — plan B is deterministic and the archive stable across days and
daytime-vs-evening load; (ii) the guard chain was *seen working*: the raw range total came
to 169,303 rows — the histogram's double-precision wobble (+1 on 47 of 94 ranges) plus the
`binary_masses` fan-out (+76, M2 landmine #4) — and the (source_id, solution_type) dedupe
+ exact-`COUNT(*)` check assembled precisely 169,227.

- **A — schema pin** (6–8 s): `TAP_SCHEMA.schemas` + per-table `TAP_SCHEMA.columns`,
  mechanically verifying every column the day-one query needs (incl. `corr_vec`) — the
  executable form of the `queries/dr3-to-dr4-tables.md` checklist.
- **B — rename patch** (2 s): the DR4-named `01_nss_compact_companion_triage.sql` was
  machine-patched to DR3 (`gaiadr4.`→`gaiadr3.`, `solution_type`→`nss_solution_type`,
  `gof`→`goodness_of_fit`, `nss_masses`→`binary_masses`, DR4-only columns stripped) and
  probed live (TOP 5, HTTP 200, 38 columns) — proving December 2 is a patch, not a
  rewrite. Patch lessons now encoded in the script: inline `--` comments must be stripped
  before token surgery, and column-name tokens need a `(?!\w)` guard
  (`semi_major_axis` almost ate `semi_major_axis_error`).
- **C — plan-B ranged pull**, exercised in full a second time (the M2 production run was
  the first): bucket histogram + 94 indexed sync ranges + exact-count guard; the
  rehearsal pull's 169,227 rows match the M2 production pull id-for-id (checksum on
  source_id sum) — the archive is stable and the fallback is reproducible.
- **D — triage + acceptance**: full AMRF triage on the rehearsal parquet;
  **BH1 + BH2 class III, PASS** on rehearsal outputs.
- **E — corr_vec + covariance MC**: measured separately the same day (74 s pull for
  4,203 rows + 10 s MC); not re-run in the driver (politeness — identical bytes).
- **F — epoch-vet loop** on the pre-release epoch file (the DataLink stand-in): the f2
  gate keeps exactly the 3 orbit sources, demotes all 9 quiet ones — PASS.
- **G — bulletin**: the day-one deliverable CSV assembled from rehearsal triage +
  covariance Pr + dust columns.

The operational playbook — command sequence, expected timings, failure branches (async
hang → ranged pull; join fan-outs; DataLink; corr_vec at DR4 scale), and the first-24/72 h
checklist — is **[`DR4-DAY-RUNBOOK.md`](DR4-DAY-RUNBOOK.md)** (M3's runbook deliverable).

## 4. The eROSITA-DE DR2 join  (task 4) — 30 X-ray counterparts, none accreting

`scripts/erosita_xmatch.py`, against `../erosita-dr2/data/` (read-only; column semantics
and the ~2 % DR1↔DR2 flux-scale note per `../erosita-dr2/M1-first-sweep.md` — the scale
note is moot here, all fluxes quoted from the eRASS:3 stack).

**Geometry.** 471 of the 949 v2 candidates lie in the eROSITA-DE footprint
(179.94° < l < 359.94°). Gaia positions PM-propagated 2016.0 → 2020.5.

**Two independent routes.** (A) identity lookup in the released NWAY Gaia-DR3 counterpart
catalog (`eRASSc3_Main_GDR3`, 2,176,277 rows) — landmine: the file carries
`GDR3_source_id` **twice** (NWAY block + appended Gaia block), which numpy dtypes reject;
deduped in-memory. (B) positional match vs eRASS3 Main v1.3 (1,975,540 rows), radius
3.44 × POS_ERR (2-D Rayleigh 99.7 %, the erosita-dr2 house pattern) floored at 1″, capped
at 10″.

**Result: 30 positional matches** (29 of them also NWAY-listed; 19/27 with
NWAY p_any ≥ 0.5), **0 hard-band matches**, against a chance expectation of
**1.38 ± 1.2** from 8 shifted-position controls (counts 3,2,0,1,2,1,0,2 at dec-shifts
±0.5–2.0°). The excess is real X-ray emission from the candidate systems, at a 6.4 % match
rate vs 0.3 % chance. Two NWAY-only rows (p_any 0.00 and 0.31 at 36″/14″) are non-matches,
kept in the CSV for the record.

**What they are (per-object notes in `out/erosita_class3_xmatch.csv`).** Every match has
log₁₀(f_X/f_opt,G) between **−4.3 and −1.2** (Maccacaro-style with G for V; the 5.37
constant is Maccacaro et al. 1988's V-band value — conventional, marked), L_X (0.2–2.3 keV,
at the NSS-parallax distance) between 9×10²⁸ and 2×10³¹ erg s⁻¹, median 2.9×10²⁹ —
**the stellar-corona locus. No match requires accretion luminosity; the X-ray flags none
of these as an X-ray binary.** Standouts:

| candidate | P [d] | G | M₂_min | Pr(III) | L_X [erg/s] | log f_X/f_opt | read |
|---|---|---|---|---|---|---|---|
| 5616598899870232704 | 545 | 9.7 | 2.71 | 1.000 | 2.0×10³¹ | −3.85 | evolved primary, low-\|b\|, most X-ray-luminous of the set — RS CVn-class active-giant binary territory; NS-range dark-companion posterior; RV follow-up target |
| 6291420068303688832 | 843 | 8.8 | 2.14 | 1.000 | 2.9×10³⁰ | −4.16 | active evolved binary, NWAY p_any 0.95 |
| 5051409687931408384 | 627 | 8.3 | 2.14 | 1.000 | 3.8×10³⁰ | −4.27 | same class, significance 121 |
| **5839182174066052224** | **332** | 13.0 | 1.59 | 0.996 | 2.1×10³⁰ | **−2.43** | **the cautionary object**: EB26-verdicted SPURIOUS, 1-yr-alias flag, and the tightest X-ray identification of the set (sep 0.36″, p_any 0.9995) — an X-ray-loud active star whose activity plausibly *produced* the spurious orbit |
| 2963110964149213184 etc. | 700–900 | 16–17 | 0.4–0.7 | 0.98–0.99 | ~10²⁹ | −1.2…−1.6 | M-dwarf hosts with WD-range M₂_min: active-M-dwarf corona vs pre-CV ambiguity — cheap spectroscopy targets |

Nine matches have M₂_min ≥ 1.4 M☉; 23/30 sit in the significance > 20 high-purity tier;
2 carry the 1-yr-alias flag; FLAG_OPT = 0 for all 30 (no optical-loading artifacts).

**The transferable lesson** (fed to the runbook): on this sample, an eROSITA detection of
a class-III host is **evidence of magnetic activity, not of a compact companion** — and
activity is a known spurious-orbit *risk factor* (starspot photocentre jitter; the one
EB26-refuted match is the X-ray-loudest relative to its star). On December 2 the X-ray
cross tags candidates for *caution* first, headline second; an accreting companion would
have announced itself at log f_X/f_opt ≳ 0, and none did.

**Sensitivity of the "no accretor" statement** [computed]: empirical eRASS:3 threshold-flux
proxy (point-like, DET_LIKE_0 ∈ [6, 8), 0.2–2.3 keV): median 1.8×10⁻¹⁴ erg s⁻¹ cm⁻²
(10–90 %: 0.96–2.6×10⁻¹⁴); at the 471 in-footprint candidates' distances that is a median
L_X reach of **3.8×10²⁹ erg s⁻¹** (10–90 %: 5.9×10²⁸–4.8×10³⁰) — deep enough that a
companion at quiescent-neutron-star-binary luminosities (~10³¹⁻³³ erg/s; UNSOURCED
order-of-magnitude from memory, to be pinned before any external use) would have been seen
for essentially every in-footprint candidate, while the faintest quiescent-BH regime
(~10³⁰) is excluded only for the nearer half. `out/erosita_xmatch_summary.txt` carries the
full statement.

## 5. Files

| artifact | what |
|---|---|
| `scripts/pull_dr3_nss_corrvec.py` | targeted corr_vec pull (VOTable, exact-count-guarded) → `data/dr3_nss_corrvec.parquet` + NOTE |
| `scripts/corrvec_probs.py` | covariance MC: Pr(III\|corr), σ(𝒜), campbell/diag checks → `data/dr3_corrvec_probs.parquet`, `out/corrvec_validation.csv`, `out/corrvec_eb26_operating_point.csv` |
| `scripts/fetch_dust_data.py` | Edenhofer mean+std (3.25 GB, md5-pinned) + SFD data downloads |
| `scripts/dust3d.py` | healpy-free Edenhofer reader (dustmaps-1.0.14-equivalent) + ZGR23 band coefficients |
| `scripts/dust_retriage.py` | extinction tiers + re-triage → `out/dust_retriage.csv`, `out/dust_movements_summary.csv` |
| `scripts/build_v2_list.py` | v2 candidate list + versioned config → `out/amrf_class3_candidates_v2.csv`, `queries/dr4-triage-config.v2.json` |
| `scripts/rehearse_dr4_day.py` | the dress rehearsal driver → `data/rehearsal/*`, `out/rehearsal_timings.csv` |
| `scripts/erosita_xmatch.py` | the eROSITA join → `out/erosita_class3_xmatch.csv`, `out/erosita_xmatch_summary.txt` |
| `DR4-DAY-RUNBOOK.md` | the December-2 operational runbook |
| `queries/dr4-triage-config.v2.json` | config **v2** — selection/screen identical to v1 (which stays frozen on disk); adds the covariance probability method (priority tier Pr ≥ 0.999) and the extinction tier |
| `data/papers/2308.01295/`, `data/papers/zgr23_curve/` | Edenhofer 2024 LaTeX source; ZGR23 extinction curve |

M2 outputs are untouched (v2 files are new; `amrf_class3_candidates.csv` remains the M2
record).

## 6. Corrections and new landmines

1. **Gaia TAP VOTable upper-cases `source_id` → `SOURCE_ID`** (CSV output does not);
   any VOTable consumer must normalize.
2. **`eRASSc3_Main_GDR3` carries a duplicate `GDR3_source_id` column** — numpy/astropy
   refuse the dtype; dedupe TTYPE in memory before touching `.data`.
3. **dustmaps 1.0.14 cites the wrong DOI for the ZGR23 extinction curve** (6674521 =
   GaiaXPy; the curve lives at 7692680/7811871).
4. **healpy does not install on Windows** (no wheel, source build fails) — dustmaps is
   therefore unusable here; `astropy_healpix` covers the need.
5. **sfdmap2 silently applies the 0.86 SF11 rescaling by default** — double-counting
   hazard with the SF11 2.742 coefficient; pass `scaling=1.0`.
6. **MC-σ vs linearized-σ diverge on TI-degenerate solutions** (σ_TI² ≳ 5): Gaussian
   sampling in TI space is conservative there. S23's e_A is the linearized error; both are
   "right" — they are different statistics. Known, measured, marked — not a bug.

## 7. Recommended M4

1. **The 30 X-ray-matched candidates as a mini-paper axis**: activity vs spurious-orbit
   incidence is testable *today* — cross the EB26 spurious/confirmed sets (all 76, not
   just class-III survivors) against eRASS:3; if spurious solutions are systematically
   X-ray-louder, that is a new, cheap DR4-day discriminator nobody has published.
   (The one in-list case is suggestive, n = 1.)
2. **Epoch-vet dress on the 12 dust-ambiguous + 55 high-σ_TI² rows** once DR4 epoch
   astrometry exists; until then, pin down the ambiguous 12 with Bayestar19 *after*
   sourcing its Gaia-band chain (the one link that kept it out of M3).
3. **The retrieval bin's 32 Pr ≥ 99.9 % sources** (headed by the probable NS at 0.9997)
   into the day-one epoch-vet queue ahead of the main list's tail.
4. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew) — the runbook's
   async-quota branch assumes anonymous until then.
