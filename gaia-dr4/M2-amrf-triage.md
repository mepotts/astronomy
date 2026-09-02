# M2 — AMRF compact-companion triage built and validated on DR3 (W2)

*2026-08-16. Workstream W2: the December-2 triage exists, passes its acceptance gate
(Gaia BH1 + BH2 in class III), and is calibrated against the only follow-up ground truth
that exists (El-Badry et al. 2026). Repo law: every externally-sourced number carries its
source or the mark UNSOURCED. Data pulls: anonymous TAP only — async where the queue
cooperates, polite sync windows where it does not (§2).*

## 1. Method

**The statistic** (verified from the papers' LaTeX sources, local copies in `data/papers/`):
the astrometric mass-ratio function of Shahaf, Mazeh, Faigler & Holl 2019
([MNRAS 487, 5610](https://doi.org/10.1093/mnras/stz1636), arXiv:1905.08542, their eq. 4),

> **𝒜 = (a₀/ϖ) · (M₁/M☉)^(−1/3) · (P/yr)^(−2/3)**

with a₀ the *photocentre* angular semi-major axis, and the astrometry equation (their eq. 6)
𝒜 = q(1+q)^(−2/3)·[1 − 𝒮(1+q)/(q(1+𝒮))], q = M₂/M₁, 𝒮 = F₂/F₁ the G-band flux ratio.
Applied to DR3 orbits by Shahaf et al. 2023 ([MNRAS 518, 2991](https://doi.org/10.1093/mnras/stac3290),
arXiv:2209.00828; "S23" below). Classes: **I** (𝒜 < 𝒜_MS: single-MS companion possible),
**II** (𝒜_MS < 𝒜 < 𝒜_tr: close-binary MS companion possible), **III** (𝒜 > 𝒜_tr: neither works
→ compact-object candidate). A dark companion has mass ratio q_min = the unique positive
root of 𝒜⁻³q³ − q² − 2q − 1 (S19 eq. 3); M₂_min = q_min·M₁.

**a₀ from Thiele-Innes coefficients** (both `Orbital` and `AstroSpectroSB1` publish A,B,F,G
in mas — the C,H of AstroSpectroSB1 are *not* needed for a₀, so **BH2's solution type drops
nothing**): u = (A²+B²+F²+G²)/2, v = AG−BF, a₀ = √(u+√(u²−v²))
(Halbwachs et al. 2023, [A&A 674, A9](https://doi.org/10.1051/0004-6361/202243969),
arXiv:2206.05726, eq. 12–14). Parallax: the NSS-solution parallax (what S23 used — verified
by reproducing their per-source 𝒜 digit-for-digit, §4).

**M₁, three tiers** (`scripts/amrf_triage.py::compute_m1`):
1. `gaiadr3.binary_masses` m1 with `m1_ref='IsocLum'` — DPAC's isochrone-luminosity mass,
   exactly S23's choice. DR4 equivalent: `nss_masses` (draft data model §10.3).
2. Photometric MS mass: absolute G from the NSS parallax → mass via the Pecaut & Mamajek
   2013 ([ApJS 208, 9](https://doi.org/10.1088/0067-0049/208/1/9)) mean dwarf sequence
   (EEM table v2022.04.16, local copy `data/papers/EEM_dwarf_UBVIJHK_colors_Teff.txt`),
   gated by the CMD main-sequence cut of El-Badry et al. 2026 (their eq. 1:
   M_G > 4.5 or M_G > −9.37 + 13.42·(BP−RP)). **No extinction correction** — documented
   bias: reddening pushes M₁ low and 𝒜 high (false-positive direction), so class-III
   candidates at |b| < 10° carry a `flag_low_lat`. Scatter: σ(M₁)/M₁ ≈ 10% adopted
   (UNSOURCED engineering estimate for the MC; the tier-1/tier-2 comparison on the real
   sample, §4, measures the actual agreement).
3. **Evolved-primary bracket**: sources failing the MS cut get *no* point M₁; the class is
   the worst case over M₁ ∈ [0.8, 2.6] M☉ (lower bound: a red giant younger than the
   universe; upper: the EEM table's M_G+mass coverage ends at B9V/2.75 M☉). This is the
   tier that keeps **Gaia BH2 (its primary is a ~1 M☉ red giant — El-Badry et al. 2023,
   [MNRAS 521, 4323](https://doi.org/10.1093/mnras/stad799), arXiv:2302.07880 abstract)**
   in the triage instead of silently dropping it — MS-only photometric pipelines fail
   exactly there (El-Badry 2026's own crude MS-relation mass for BH2 is 2.30 M☉, their
   astrometric-candidate table).

**Class boundaries**: 𝒜_MS(M₁) and 𝒜_tr(M₁) computed from scratch by forward-modelling
S19's three cases with the EEM G-band sequence (𝒮(q) from interpolated M_G(mass); triple
case = equal-mass close pair, valid until 𝒮=1): `scripts/amrf.py::boundary_curves`.
At M₁ = 1 M☉ this gives 𝒜_MS = 0.386, 𝒜_tr = 0.597 — matching S23's Fig. 1–2 (≈0.4 /
≈0.55–0.6). S23's *adopted* curve is a conservative 99.9% MIST-ensemble envelope published
only in paywalled supplementary material, so it was **reconstructed empirically** from
their per-source published probabilities (CDS J/MNRAS/518/2991 table1: in narrow M₁ bins,
the 𝒜 at which their Pr(III) crosses 50%): the S23 envelope sits at 1.05–1.26× the Mamajek
curve (median 1.14), highest below 0.5 M☉ where they padded the MLR. The triage therefore
carries a single knob, `boundary_inflate`; 1.15 (the S23 envelope's typical level) is the
frozen value after calibration, and 1.25 (its maximum) was tested and rejected — it
over-rejects with zero measured purity gain (§4–5; `scripts/s23_reference.py`).

**Quality cuts** — all implemented as *flags*, never in-query, so every rejected population
stays countable (El-Badry 2026 lesson):
- Halbwachs et al. 2023 vetting (as used by S23 §3.1): σₑ < 0.079·ln(P/d) − 0.244;
  ϖ/σϖ > 20000·(P/d)⁻¹; `significance` (= a₀/σ_a₀) > 158·(P/d)^(−1/2).
- S23 Thiele-Innes criterion: σ_TI² = Σ(σ/value)² over A,B,F,G ≤ 36.
- El-Badry 2026 spurious-solution discriminators (their §7 + Fig. 15): a `significance`
  tier ("a majority of sources with significance > 20 have reliable orbits" — tiers 5/10/20
  tested in §5, **10 frozen**: 20 rejects Gaia BH1) and the magnitude-split
  goodness-of-fit cut (F2 < 6 at G < 13, F2 < 4 at G > 13 — "most sources in our sample
  with F2 > 6 and G < 13 turned out to have spurious orbits, as did sources with F2 > 4
  and G > 13").
- **Period window [10, 1500] d for the DR3 validation** — *not* S23's P < 1000 d, which
  would drop BH2 (P = 1352 d) outright; S23's own comparison section records four El-Badry
  BH candidates lost to that cut ("their orbital periods are longer than 1000 day").
  DR4: [10, 2200] d (66-month baseline ≈ 2011 d).
- **No RUWE cut, ever**: the host's inflated single-star RUWE *is* the orbit signature
  (BH1 ruwe = 7.64, BH2 = 9.22, `fixtures/`).
- 1-yr alias window [330, 400] d and |b| < 10° are flags, not cuts.

Classification is deterministic (best-fit 𝒜 vs the curves) plus a per-source Monte-Carlo
Pr(class III) (10³ draws over TI coefficients, parallax, period, M₁; `mc_seed` pinned).
The DR3 `corr_vec` correlations are **not** used — accepted simplification, checked against
S23's published per-source σ(𝒜) in §4.

## 2. The data pull (and an operational finding about the anonymous queue)

Universe: all six DR3 astrometric-orbit solution types (169,227 rows; §7.3), joined with
`gaia_source` host photometry/astrometry and LEFT-joined with `binary_masses` — 78 columns,
no science cuts in-query. Two supported paths, identical schema:

- `scripts/pull_dr3_nss_orbits.py` — the intended single anonymous **async** job.
  **Operational finding (2026-08-16, Sat evening):** the anonymous async queue held both a
  169k-row join job and a trivial 195k-row single-table job for **>100 minutes without
  completion** while the sync endpoint answered in seconds — M1's "async for anything big"
  guidance is not reliable close to a deadline. On DR4 day, assume the queue is worse.
- `scripts/pull_dr3_nss_orbits_windowed.py` — fallback v1, the README's "window or async"
  convention: keyset-paginated **sync** windows (TOP 2000 + ORDER BY, resumable). Worked
  but slow — the server re-sorts the joined set every window (**68 s/window ≈ 100 min
  total**); superseded mid-run by v2.
- `scripts/pull_dr3_nss_orbits_ranged.py` — **fallback v2, the path that delivered**: one
  3-second server-side aggregate maps rows per `source_id` bucket (FLOOR(id/2^52): 1,536
  non-empty buckets, max 566 rows), buckets are packed into 94 ranges of ≤1,900 expected
  rows, and each range is pulled by plain indexed predicate — no ORDER BY, no sort cost,
  and **no silent-truncation risk** (each range's row count is hard-checked against the
  aggregate; the assembly is hard-checked against the live total). Resumable; 0.5 s
  politeness gap. This is the day-one recipe if the DR4 queue melts.
- `scripts/pull_dr3_subset_sync.py` — de-risk pull of the 206 *named* sources this
  milestone's gates depend on (BH1 + BH2 + El-Badry's 76 + S23's 177, overlaps removed);
  one sync call, seconds. **All 206 exist in the six-type universe** — no named source is
  outside the query.

Result: `data/dr3_nss_amrf_input.parquet` — **169,227 solution rows over 169,129 distinct
sources**, 78 columns, hard-checked against the live exact `COUNT(*)`; sha256 + query in
`data/dr3_nss_amrf_input.NOTE.md`. All acceptance/calibration numbers below were computed
on the named-source subset first and re-verified identical on the full pull.

## 3. Acceptance: BH1 + BH2 — **PASS**, with margins

Frozen config (boundary_inflate = 1.15, §6). Pipeline output, `scripts/amrf_triage.py`:

| | **Gaia BH1** | **Gaia BH2** |
|---|---|---|
| solution type | `Orbital` | `AstroSpectroSB1` (nothing dropped — a₀ needs only A,B,F,G) |
| a₀ (Thiele-Innes) | 2.9775 mas | 3.8800 mas |
| ϖ (NSS), P | 2.0955 mas, 185.77 d | 0.8592 mas, 1352.29 d |
| M₁ | 0.955 M☉ (`binary_masses` IsocLum) | **no point M₁** — giant, fails MS cut (M_G=1.95) → evolved bracket [0.8, 2.6] M☉ |
| **AMRF 𝒜** | **2.265** | **1.498** (at the bracket's least-favourable mass) |
| 𝒜_tr at M₁ (×1.15) | 0.671 | evaluated across the bracket |
| **class** | **III**, margin **3.38×**, Pr(III)=1.0000 | **III at every bracket mass**, worst-case margin **2.44×**, Pr(III)=1.0000 |
| q_min, M₂_min | 13.42 → **12.81 M☉** (S23 published the same 12.81±2.60 from this inversion; El-Badry 2026's joint astrometry+RV fit gives **9.18±0.13** with a₀ revised 2.98→2.63 mas — the DR3 Gaia-only orbit runs hot, a *triage* statistic inherits that) | 4.88 → **9.76 M☉** conservative bracket value (true value 8.9±0.3, and true P = 1277 d vs Gaia's 1352 — El-Badry et al. 2023, arXiv:2302.07880 abstract) |
| core gates | all pass; **slimmest margins in the whole milestone**: ϖ/σϖ = 120.0 vs 107.7 needed (1.11×), a₀-sig 13.6 vs 11.6 (1.17×) | all pass, wide: 47.0 vs 14.8; 39.8 vs 4.3 |
| EB26 screen | sig > 10 ✓ (13.6), **sig > 20 ✗** — see §5 | all tiers ✓ (39.8), F2 = 3.07 ✓ |

Both targets land in class III on the *first end-to-end run* — no cut was loosened to make
them pass. Two designed-in decisions were load-bearing (made from the papers before running,
§1): the P-window past 1352 d, and the evolved-primary bracket. The headline acceptance
finding is about the *screen*, not the class: **El-Badry's strictest spurious-screen tier
(significance > 20) would reject Gaia BH1 itself** (sig = 13.6) — quantified in §5, and the
reason the frozen config sets 10, not 20.

## 4. Implementation validation against Shahaf et al. 2023

Against their published per-source table (CDS J/MNRAS/518/2991, table1 = 101,380 sources,
table2 = the 177 class-III sample; local copies + parser `scripts/s23_reference.py`):

- **𝒜 agreement: exact.** On every shared source where the pipeline uses the same M₁ tier
  (`binary_masses`): median 𝒜(ours)/𝒜(S23) = 1.0000, 1–99% range [1.0000, 1.0000], 100%
  within 5% — **n = 101,440 joined rows on the full pull** (their whole 101,380-source
  clean sample; the 60 extra rows are dual-solution sources joining twice, §7.4). BH1:
  ours 2.26497 vs their printed 2.264966683016366. Same a₀ route, same NSS parallax, same
  M₁ — the implementation *is* S23's statistic.
- **Their class-III sample: 177/177 recovered as class III** at inflate 1.00 and 1.15;
  inflate 1.25 loses 12/177 — one of two reasons 1.25 was rejected (§5 has the other).
- **Boundary reconstruction** (their adopted conservative curve exists only in paywalled
  supplementary material): from the Pr(III) 50%-crossings in their table1, their envelope =
  1.05–1.26× the from-scratch Mamajek curve (median 1.14) over M₁ = 0.35–1.1 M☉ —
  `boundary_inflate` = 1.15 sits on their typical level by construction, not by fit to the
  acceptance targets.
- **Uncertainty honesty:** the pipeline's MC draws ignore the DR3 `corr_vec` correlations.
  Measured against S23's covariance-aware e_𝒜 on the shared sources: σ(𝒜) overestimated by
  a median 2.27× (10–90%: 1.03–6.75×; BH1 itself mild, 0.165 vs 0.174). Consequence:
  `p_class3_mc` is a *pessimistic diagnostic*; the selection is deterministic (best-fit 𝒜
  vs boundary + cut flags) and unaffected. DR4-grade probabilities need the covariance
  (nsstools implements it) — an M3 work item.

## 5. False-positive calibration against El-Badry et al. 2026

Ground truth: the 76 astrometrically-selected candidates of El-Badry et al. 2026
(arXiv:2608.06453, "Spectroscopic follow-up of compact object binary candidates from Gaia
DR3"), parsed from the paper's LaTeX source into
`fixtures/elbadry2026_astrometric_candidates.csv` by `scripts/parse_elbadry2026_table.py`:
**42 CONFIRMED** compact-object hosts (their "Good solution" + BH1/BH2/NS1 + one
"solution OK, residual scatter"), **23 SPURIOUS** (RVs inconsistent / ruled out),
1 MARGINAL, 2 NOT_CO (eclipsing-binary triples), 1 OTHER (sdB primary), 7 UNKNOWN (no or
incomplete follow-up). Their headline: ~60% of astrometric candidates reliable; "no simple
set of cuts cleanly divides reliable and spurious orbits", but significance–F2 cuts remove
a majority of spurious ones (their §7).

Caveat stated up front: this ground truth is *selection-biased toward the triage's own
candidate region* (they selected high-M₂ systems), so "completeness" below means
completeness *of confirmed compact objects*, and "spurious pass-rate" is measured on
solutions weird enough to have been followed up — the honest reading is relative between
cut variants, not absolute.

**The tradeoff, measured** (`out/amrf_cut_variants.csv`; all variants sit on top of the
core gates — Halbwachs vetting + σ_TI ≤ 6² + window + parallax sanity — which alone reject
2/23 spurious and 1/42 confirmed¹):

| boundary | signif. | F2 cut | DR3 class-III | confirmed kept /42 | spurious passed /23 | note |
|---|---|---|---|---|---|---|
| ×1.15 | ≥0 | none | 1,355 | 41 (97.6%) | 21 (91.3%) | AMRF class alone barely rejects follow-up-selected spurious solutions |
| ×1.15 | >0 | mag-split | 1,190 | 41 (97.6%) | 14 (60.9%) | F2 helps everywhere |
| **×1.15** | **>10** | **mag-split** | **951** | **39 (92.9%)** | **7 (30.4%)** | **frozen** — keeps BH1 (13.6), BH2 (39.8), NS1 (89.9) |
| ×1.15 | >20 | mag-split | 711 | 34 (81.0%) | 3 (13.0%) | **rejects Gaia BH1**; −5 more confirmed |
| ×1.25 | >10 | mag-split | 582 | 30 (71.4%) | 7 (30.4%) | boundary over-reach: −9 confirmed vs ×1.15, zero purity gain |

¹ Losses have names, not just rates: the core gates cost **6054379247042197504** ("Good
solution", evolved primary, σ_TI² > 36 — a genuinely ill-constrained TI solution that
happens to be real). significance > 10 additionally costs **1007185297091149824**
(sig = 9.8, M₂_min = 2.12 — a probable NS!) and **1732878914341314944** (sig = 6.8). These
are exactly the systems the DR4 epoch-vetting loop (§8) re-rescues: keep a *retrieval bin*
of class-III sources failing only the significance tier, and let epoch astrometry decide.
Of the 7 surviving spurious, one (5839182174066052224, P = 332 d) is caught by the 1-yr
alias flag; two (6001459821083925120, 6092954989675820416) are clean on **every** Gaia
metric — El-Badry's "no simple set of cuts cleanly divides" in the flesh; only epoch-level
or spectroscopic vetting kills those.

Inflate 1.15 vs 1.00 changes *nothing* on the EB26 confirmed set (no confirmed source sits
between the two boundaries) while being the reconstructed level of S23's conservative
envelope — conservatism for free. 1.25 costs 9 confirmed + 12 of S23's own class-III for
zero measured purity gain: rejected.

## 6. The frozen DR4 config

`queries/dr4-triage-config.json` (machine-readable, consumed by the day-one run):

> **Selection**: all DR4 astrometric-orbit types incl. `AstroSpectroSB1`/`AstroSpectroSB2`
> and — in a retrieval bin, not the headline list — `OrbitalPoorlyConstrained`; P ∈ [10,
> 2200] d; NSS ϖ/σϖ ≥ 3. **Core gates**: Halbwachs Δe/ϖ-sig/a₀-sig, σ_TI² ≤ 36. **M₁**:
> `nss_masses` → photometric MS (EEM) → evolved bracket [0.8, 2.6] M☉ worst-case.
> **Class III**: 𝒜 > 𝒜_tr(M₁) × **1.15** (Mamajek-curve base). **Screen**: significance
> > **10**; F2 < 6 (G < 13) / < 4 (G ≥ 13); flags (never cuts): 1-yr alias [330, 400] d,
> |b| < 10°, RUWE untouched. **Expected operating point (measured on DR3 against El-Badry
> 2026): ~93% completeness of confirmed compact objects, ~30% spurious pass-through,
> before epoch-level vetting** — which DR3 never had and DR4 provides on day one.
DR3-wide yield under the frozen config (`out/amrf_class3_candidates.csv`): **951 class-III
solutions** (M₁ tiers: 783 `binary_masses` / 141 evolved-bracket / 27 photometric-MS), of
which 39 are EB26-confirmed compact objects and 7 are EB26-spurious survivors. Sub-tiers
for prioritisation: **147** also have MC Pr(III) ≥ 99.9% (the S23-comparable high-purity
core — theirs had 177 with covariance-aware MC), **711** sit in the `flag_sig_gt20`
high-purity tier, 7 carry the 1-yr-alias flag and **270 (28%) the low-|b| extinction
flag** — the known false-positive reservoir of the uncorrected tier-2 M₁. The **retrieval
bin** (class III, core + F2 pass, significance below 10) holds **239** more
(`out/amrf_class3_lowsig_retrieval.csv`). Funnel: 169,227 solutions → 142,497 core-clean
(class III 1,355) → 104,202 screened (class III 951); plots `out/amrf_plane.png`,
`out/amrf_class_distribution.png`. Ranked by M₂_min, **the frozen list's top two entries
are Gaia BH1 (12.81 M☉) and Gaia BH2 (9.76 M☉)** — and #3 is 3509370326763016704, a
*known EB26-refuted spurious* at significance 76: the cleanest possible demonstration that
the screen's residue is exactly what the epoch-vetting loop (§8) exists to kill. Caveats
carried: no extinction correction in tier-2 M₁ (`flag_low_lat`), corr_vec-free MC
(diagnostic only), ranged-sync fallback pull ready for day one.

## 7. Corrections to M1 (a refuted landmine) and new landmines found

1. **M1's "source_ids are not stable DR3→DR4, BH3 was renumbered" is REFUTED.**
   Panuzzo et al. 2024 prints `Gaia DR3 4318465066420528000` (verified in the
   arXiv:2404.10486 LaTeX source, line 174) — not `...896`, which exists nowhere in
   `gaiadr3.gaia_source`. All **12 of 12** pre-release epoch-astrometry sources carry
   their DR3 source_ids unchanged (TAP id-match + cone-search + SIMBAD, 2026-08-16;
   Gaia-4 = `Gaia DR3 1457486023639239296` per SIMBAD). What survives: DR4 rebuilds its
   source list and ships the `dr3_neighbourhood` crosswalk (draft model §7.3), so
   resolve-before-use stays as cheap insurance — but no renumbering has actually been
   observed, and nothing may *depend* on ids changing. `M1-prerelease.md` and
   `queries/dr3-to-dr4-tables.md` carry dated corrections. (Found because this very
   milestone tripped over it: the vetting-loop script tagged Gaia-4 with a from-memory
   DR3 id and the f2 gate exposed the mismatch — the id that failed was the *fabricated*
   one, `1712614124767394816`, which belongs to an unrelated star at δ=+75°.)
2. **BH2 has no `gaiadr3.binary_masses` row** (verified by TAP, 2026-08-16). S23's exact
   recipe (require `m1_ref='IsocLum'`) plus their P < 1000 d window loses BH2 twice over.
   Any DR4 triage that hard-requires an `nss_masses` row will have the same failure mode —
   hence the three-tier M₁ policy. (BH1 does have a row: m1 = 0.954 ± 0.06, m2 = 12.81.)
3. **DR3 solution-type strings verified live** (GROUP BY on `gaiadr3.nss_two_body_orbit`,
   2026-08-16): `Orbital` 134,598; `AstroSpectroSB1` 33,467; `OrbitalAlternative` 619 +
   `OrbitalAlternativeValidated` 10; `OrbitalTargetedSearch` 345 +
   `OrbitalTargetedSearchValidated` 188 — the two `*Validated` variants exist as separate
   strings (the M2 task brief's 4-type list would have silently missed 198 solutions).
   Total pulled universe: 169,227.
4. **`source_id` is a primary key in NEITHER `nss_two_body_orbit` NOR `binary_masses`**
   (live counts 2026-08-16: 169,227 rows / 169,129 distinct sources for the six
   astrometric types; 195,315 / 195,239 in `binary_masses`). **98 sources carry BOTH an
   `AstroSpectroSB1` and an `OrbitalTargetedSearch(Validated)` solution** — two genuine
   independent orbits; a `drop_duplicates(source_id)` silently deletes 98 orbits (it did,
   once — caught by the exact-count guard). And a plain `binary_masses` LEFT JOIN fans out
   +76 rows (resolved by preferring the mass row whose `combination_method` matches the
   solution type). DR4's `nss_two_body_orbit`/`nss_masses` must be assumed multi-row per
   source too.
5. **ADQL integer→double rounding breaks bucket arithmetic** for `source_id` > 2^53:
   `FLOOR(source_id/2^52.0)` computes in double precision, so per-bucket counts wobble ±1
   at boundaries. Any range-partitioned pull must **tile** the id space (no "empty-bucket"
   gaps) and verify against an exact integer `COUNT(*)`, not the histogram sum.

## 8. Stretch: the epoch-level vetting loop (prototyped, PASS)

`scripts/vet_epoch_astrometry.py` — the December workflow for class-III candidates:
resolve ids (`dr3_neighbourhood`) → check `has_epoch_astrometry` → DataLink fetch
(`retrieval_type='EPOCH_ASTROMETRY'`; **not** a TAP table, M1 finding #1 stands) →
`gaiasupdate` single-star fit → goodness-of-fit **f2** as the badness statistic
(`excess_noise` is None in gaiasupdate 0.1.2): |f2| ≤ gate ⇒ no epoch-level wobble
supporting the claimed photocentre orbit ⇒ **demote** (spurious-orbit suspect); f2 ≫ gate
⇒ wobble real ⇒ keep, hand to the orbital refit (M1's BH3 script). DR3 has no epoch data,
so the prototype runs on the only epoch astrometry in existence, the 2026-06-26 pre-release
file: with the gate at |f2| > 5, **exactly the 3 orbit-category sources survive**
(Gaia BH3 f2 = 894.0, HD 114762 f2 = 186.5, Gaia-4 f2 = 31.5) **and all 9 quiet sources
are demoted** (|f2| ≤ 1.55) — `out/epoch_vetting_prototype.csv`. This is the
false-positive killer that DR3 candidates never had: El-Badry 2026 needed four years of
spectroscopy to reach verdicts that DR4 epoch astrometry + a 30-second fit will produce
on day one for every candidate with epoch data.

## 9. Files

| artifact | what |
|---|---|
| `scripts/pull_dr3_nss_orbits.py` | the async TAP pull → `data/dr3_nss_amrf_input.parquet` + NOTE (rows, sha256, query) |
| `scripts/pull_dr3_nss_orbits_windowed.py` | same pull as resumable 2000-row sync windows (the queue-congestion fallback that actually delivered) |
| `scripts/pull_dr3_subset_sync.py` | de-risk sync pull of the 206 named acceptance/calibration sources |
| `scripts/amrf.py` | the AMRF library: a₀, 𝒜, q_min, EEM MLR, boundary curves, MS cut |
| `scripts/amrf_triage.py` | the triage pipeline: M₁ tiers, classes, MC Pr(III), cut flags, plots, **BH1+BH2 acceptance gate** |
| `scripts/s23_reference.py` | S23 CDS tables loader + empirical boundary reconstruction |
| `scripts/parse_elbadry2026_table.py` | El-Badry 2026 LaTeX table → verdict fixture |
| `scripts/calibrate_amrf_cuts.py` | S23 cross-check + cut-variant calibration + config freeze |
| `scripts/vet_epoch_astrometry.py` | stretch: epoch-level vetting loop (f2 gate) |
| `fixtures/elbadry2026_astrometric_candidates.csv` | 76 candidates with follow-up verdicts |
| `queries/dr4-triage-config.json` | the frozen DR4 day-one config |
| `out/amrf_plane.png`, `out/amrf_class_distribution.png` | 𝒜–M₁ plane; class counts |
| `out/amrf_class3_candidates.csv`, `out/amrf_class3_lowsig_retrieval.csv`, `out/amrf_class_counts.csv`, `out/amrf_cut_variants.csv`, `out/amrf_s23_crosscheck.csv`, `out/epoch_vetting_prototype.csv` | tables backing §3–§6, §8 (incl. the epoch-vet retrieval bin) |
| `data/papers/` (gitignored) | arXiv LaTeX sources: 1905.08542, 2209.00828, 2309.15143, 2608.06453, 2404.10486; CDS J/MNRAS/518/2991; EEM table |

## 10. Recommended M3

**Close the two knowingly-open seams, then dress-rehearse December 2.**
1. **corr_vec / nsstools**: consume the DR3 covariance so Pr(III) is S23-grade (the 2.27×
   σ(𝒜) overestimate, §4); re-emit the candidate list with honest probabilities and an
   FDR threshold à la S23.
2. **Extinction tier**: bolt a dust map onto tier-2 M₁ (El-Badry used Green19/Lallement19;
   `dustmaps` package) and measure how many low-|b| class-III candidates it kills — the
   flag_low_lat population is the false-positive reservoir.
3. **Dress rehearsal**: run the frozen config end-to-end against DR3 *as if* it were DR4
   (rename map applied, `nss_masses`→`binary_masses` shim, epoch-vet loop on the
   pre-release file), producing the day-one candidate bulletin format; time it. Then the
   erosita-dr2 × class-III cross-match (an X-ray-detected class-III system would be a
   headline candidate on day one).
