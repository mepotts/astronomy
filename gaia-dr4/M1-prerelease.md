# M1 — DR4 pre-release verified, ESA's fitting stack runs end-to-end, day-one ADQL validated

*2026-08-14. Workstreams W1 (verify + run) and W3 (canned ADQL), plus the W2 fixtures.
Repo law applies: every externally-sourced number below carries its source or the mark UNSOURCED.*

## 1. Claim-by-claim verification (W1a)

| Claim (2026-08-14 sweep) | Verdict | Evidence |
|---|---|---|
| DR4 releases **2026-12-02** | **CONFIRMED** | "Gaia DR4 (based on 66 months of data) 2 December 2026" — [release page](https://www.cosmos.esa.int/web/gaia/release) |
| ESA published a **pre-release sample of epoch_astrometry** (~Jun 2026) | **CONFIRMED** (singular: one file, 12 sources) | [DR4 pre-release page](https://www.cosmos.esa.int/web/gaia/dr4-prerelease): published 29 June 2026; `gaia-dr4-prerelease-epoch-astrometry_2026-06-26.zip` (625,651 B; unzips to a 1,183,282 B VOTable tagged `Gaia DR4_RC3`), [download](https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-epoch-astrometry_2026-06-26.zip). 12 sources in 4 categories: parallax (~1 mas at G≈9/14/19), magnitude (G≈14 at ~1/5/10 mas), qso (3 CRF3 QSOs), orbit (Gaia BH3, HD 114762, Gaia-4) |
| An **official Python package** for single-star epoch-astrometry fitting | **CONFIRMED** | **`gaiasupdate` 0.1.2** ("Gaia Source Update"), PyPI-installable, ESA-PL Permissive v2.4, authors J. Sahlmann & A. Delgado (ESA); repo [esa/gaia-supdate](https://github.com/esa/gaia-supdate), docs [esa.github.io/gaia-supdate](https://esa.github.io/gaia-supdate), homepage [cosmos.esa.int/web/gaia/gaia-source-update](https://www.cosmos.esa.int/web/gaia/gaia-source-update). Tutorial notebook: [esa/gaia-jupyter-notebooks → data-release-4-tutorials](https://github.com/esa/gaia-jupyter-notebooks/tree/main/data-release-4-tutorials). **Bonus not in the claim:** ESA also published an official *orbital*-fit recipe — [esa/gaia-bhthree, branch `gaia-dr4-prerelease`](https://github.com/esa/gaia-bhthree/tree/gaia-dr4-prerelease) refits Gaia BH3 on this very sample |
| **Draft DR4 data model** published | **CONFIRMED** | `gaia-dr4-prerelease-draft-data-model_2026-06-26.zip` (2,840,832 B) → one PDF, 1231 pp, issue D rev 0 dated 2026-05-20, [download](https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-draft-data-model_2026-06-26.zip); local copy in `data/draft-data-model/`. Draft warns contents may change without notification |
| **Source-count update** on the DR4 page | **CONFIRMED** (as counts, not a named document) | [DR4 contents page](https://www.cosmos.esa.int/web/gaia/dr4): `gaia_source` ≈ 2 billion sources; ≈ 2.8 billion processed in total (the new `all_source_*` tables cover the full 2.8B) |

## 2. ESA's tooling runs end-to-end on Windows (W1b)

Environment: `.venv/`, Python 3.12.10, `gaiasupdate` 0.1.2 + astropy 7.2.2, astroquery 0.4.11,
pandas 2.3.3, matplotlib 3.11.1; orbital stack kepmodel 1.0.8 / spleaf 2.1.17 / pystrometry 0.6.1
— **all pip-installed cleanly on Windows 11, no WSL needed** (ESA's own environment.yml uses conda,
but pip wheels worked).

**Single-star fits** (`scripts/fit_prerelease_single_star.py`, mirrors the official tutorial):
`GaiaEpochAstrometryArchive.supdate()` ran on **all 12 sources, 12/12 converged**
(`6p_constrained_colour` model) → `out/supdate_results.csv`, `out/source_inventory.csv`.
The design validates itself: parallax-category sources come out at ≈1 mas across G=9/14/19,
magnitude-category at ≈1/5/10 mas, QSOs at ≈0 mas parallax and <0.4 mas/yr PM, and the three
orbit-category sources are exactly the ones the single-star model fails on
(goodness-of-fit f2 = 894 / 187 / 32 vs |f2| < 1.6 for all nine others).
Caveat: `excess_noise` in the returned dict is `None` in v0.1.2 — rank badness by `f2`.
Diagnostic plot: `out/supdate_4318465066420528000.png`.

**Orbital fit** (`scripts/fit_prerelease_orbit_bh3.py`, mirrors ESA's BH3 notebook):
periodogram of single-star residuals → FAP≈0 peak → Keplerian fit, on Gaia BH3:

| quantity | this fit (astrometry-only) | published (Panuzzo et al. 2024, [A&A 686, L2](https://doi.org/10.1051/0004-6361/202449763)) |
|---|---|---|
| P | 4183.7 d = 11.45 yr | 11.6 yr |
| e | 0.728 | 0.729 |
| companion mass (m1 = 0.76 M☉) | 34.7 M☉ | 32.70 ± 0.82 M☉ (incl. RVs) |

Outputs: `out/bh3_orbit_fit.txt`, `out/bh3_orbit_fit.png` (residuals + periodogram + orbit signal).
**Verdict: we can run ESA's own DR4 tooling today, single-star AND orbital, on this machine.**

## 3. Findings that change day-one plans

1. **`epoch_astrometry` is DataLink-only, not a TAP table** (draft data model §3.1: "not
   available through the main archive TAP interface"; astroquery
   `retrieval_type='EPOCH_ASTROMETRY'`). Bulk epoch fetches must be planned as DataLink
   batches keyed on `has_epoch_astrometry`, not as ADQL joins.
2. **source_id is NOT stable DR3 → DR4.** Gaia BH3 is `4318465066420528896` in DR3
   (Panuzzo et al. 2024) but `4318465066420528000` in the pre-release file (int64, verified in
   the VOTable and in ESA's notebook). Crosswalk = `dr3_neighbourhood` (§7.3). Every stored
   DR3 id (exosat-rv hosts, fixtures) must be resolved before use.
   **⚠ CORRECTED 2026-08-16 (M2, see [`M2-amrf-triage.md`](M2-amrf-triage.md) §7):** the
   BH3 example is false — Panuzzo et al. 2024 prints `Gaia DR3 4318465066420528000`
   (arXiv:2404.10486 source), `...000` is the live DR3 id, `...896` exists nowhere in DR3,
   and all 12 pre-release sources carry their DR3 ids **unchanged**. The `dr3_neighbourhood`
   crosswalk and the resolve-before-use practice stay (DR4's source list is rebuilt, so ids
   *may* change), but as insurance, not as a reaction to any observed renumbering.
3. **DR4 `nss_two_body_orbit` publishes Campbell elements + `mass_function` directly**, and a
   new **`nss_masses`** table carries m1/m2 posteriors, `fluxratio`, and
   `exoplanet_candidate_hrd_proba` / `lowmass_candidate_hrd_proba` (§10.3) — the AMRF triage
   gets both easier inputs and a DPAC-computed comparator to beat.
4. **Renames/removals for our cuts** (full list: `queries/dr3-to-dr4-tables.md`):
   `nss_solution_type`→`solution_type`, `goodness_of_fit`→`gof`,
   `astrometric_params_solved`→`astrometric_params`; `astrometric_excess_noise_sig` and
   `phot_bp_rp_excess_factor` **removed** from gaia_source (Marchetti's `_sig ≤ 2` cut needs a
   replacement — we use `astrometric_gof_al` + `ruwe`). New solution type
   `OrbitalPoorlyConstrained` (significance < 5) is exactly the bin BH3-like systems fall into —
   keep it retrievable (El-Badry et al. 2026, [arXiv:2608.06453](https://arxiv.org/abs/2608.06453)).
5. **DR4 reference epoch is J2017.5 TCB** (ESA BH3 notebook; DR3 was J2016.0).

## 4. Day-one ADQL state (W3)

`queries/`, one DR4 file + one DR3-validated twin each; all three twins ran against the
anonymous TAP (`https://gea.esac.esa.int/tap-server/tap/sync`, TOP 10, CSV) on **2026-08-14,
all HTTP 200**:

| query | DR4 file | DR3 validation |
|---|---|---|
| (a) NSS compact-companion triage input (Shahaf+19 AMRF style, El-Badry+26 lessons; cuts parameterized; joins `nss_masses`) | `01_nss_compact_companion_triage.sql` | 10 rows, Thiele-Innes a0 math verified in-ADQL |
| (b) 6D hypervelocity input (Marchetti+19 cuts; `vtan` computed in-query) | `02_hypervelocity_6d.sql` | 10 rows, all vtan ≥ 300 km/s or \|RV\| ≥ 300 km/s |
| (c) epoch-astrometry fetch for a named source list (+ `dr3_neighbourhood` resolver; DataLink recipe in header) | `03_epoch_astrometry_fetch.sql` | IN-list pattern returned exactly BH1 + BH2 |
| (d) diff-auditor overlap | noted in each header; shared artifact = `dr3-to-dr4-tables.md` | — |

## 5. W2 fixtures (pulled, triage itself deferred to M2)

`fixtures/gaia_bh1_bh2_dr3_nss_two_body_orbit.csv` — full DR3 NSS rows:
Gaia BH1 `4373465352415301632` (Orbital, P=185.77 d, e=0.489, ϖ=2.095 mas),
Gaia BH2 `5870569352746779008` (AstroSpectroSB1, P=1352.3 d, e=0.532, ϖ=0.859 mas)
(ids per El-Badry et al. 2023, [MNRAS 518, 1057](https://doi.org/10.1093/mnras/stac3140) and
[MNRAS 521, 4323](https://doi.org/10.1093/mnras/stad799); rows pulled from `gaiadr3.nss_two_body_orbit` 2026-08-14).
`fixtures/gaia_bh1_bh2_dr3_gaia_source.csv` — host rows (BH1 ruwe 7.64, BH2 ruwe 9.22).
Both pass query 01's input cuts — the M2 acceptance precondition ("the cut must keep BH1+BH2") holds
at the selection stage. Note BH2 is `AstroSpectroSB1`, so a triage that only reads `Orbital`
solutions would lose it.

## 6. Corrections / additions to `DISCOVERY/run3-prospectus.md`

No claim was wrong. Precision updates worth folding in:
- "pre-release **samples**" → one sample file, 12 sources, epoch astrometry only (no epoch
  photometry/spectra in the pre-release).
- The official package has a name and a scope: `gaiasupdate` (PyPI) does **single-star** fitting
  only; the **orbital** recipe lives in the separate `esa/gaia-bhthree` pre-release branch
  (kepmodel/spleaf, not an ESA package).
- Add findings 1–2 above (DataLink-only epoch astrometry; unstable source_ids) to the
  day-one plan — both change tooling assumptions.
- El-Badry follow-up arXiv:2608.06453 verified to exist with the claimed ~60%/~50% numbers
  (title: "Spectroscopic follow-up of compact object binary candidates from Gaia DR3").

## 7. Human TODOs (unchanged, still open — agents must not create accounts)

- [ ] Gaia Archive account (lifts the 2,000-row sync cap; enables user tables) — **Matthew**
- [ ] NOIRLab Astro Data Lab account (`mydb` + billion-row crossmatch) — **Matthew**

## 8. Recommended M2

**Build the AMRF triage offline and pass the acceptance gate**: async-pull the full DR3
`nss_two_body_orbit` orbital set (~1.7×10⁵ orbits, Halbwachs et al. 2023,
[arXiv:2206.05726](https://arxiv.org/abs/2206.05726)) with query 01's DR3 twin un-capped,
implement A = (a0/ϖ)·M1^(−1/3)·(P/yr)^(−2/3) with an M1 estimator, and demand **BH1 + BH2
recovered** above the compact-companion boundary while measuring the false-positive rate
against El-Badry et al. 2026's confirmed/spurious lists (arXiv:2608.06453) — that paper is
the free training set for the December false-positive killer. Stretch: prototype the epoch-level
vetting loop (query 03 → gaiasupdate → f2/jitter) on the pre-release orbit sources, which is the
exact loop DR4 candidates will get.
