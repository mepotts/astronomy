# M1 — reproduce the Hephaistos II selection, vet the survivors, open the SPHEREx axis

*2026-08-18 · workstreams W1 (selection reproduction + throughput), W2 (vetting D and I, control C), W3 (SPHEREx QR2).
Every externally-sourced number carries its source; anything unsourced is marked UNSOURCED. Nothing here has been
reported externally.*

---

## 0. Executive summary

1. **The selection reproduces 7/7 — with one documented boundary.** All seven Hephaistos II candidates
   (A–G) pass my catalog-level implementation of the paper's cuts, and the three Hephaistos III add-ons
   (H, I, J) fail **exactly and only** the W3/W4 SNR ≥ 3.5 cut, as Korn et al. 2026 state. The boundary:
   candidate F (their own refit γ = 0.03 ± 0.008) is **incompatible with the paper's stated initial model
   grid** (γ ≥ 0.1) — no γ ≥ 0.1 model fits F at RMSE ≤ 0.2 (best 0.25; F needs γ ≤ 0.07 admitted).
   The CNN nebular classifier and the final visual inspection are **not reproducible** from the paper
   (weights, training images, and human judgement unpublished) — and the visual step is where 368 → 7
   happens (98% of the final-stage rejection).
2. **The mission premise is stale: D is no longer clean.** Project Hephaistos IV (Zackrisson et al.,
   arXiv:2607.09460, 10 Jul 2026) — JWST/MIRI imaging + MRS — attributes D's mid-IR excess to an
   IR-bright background galaxy at z ≈ 0.9, ~1″ from the star, with an AGN-like spectrum and Hot-DOG-like
   SED. **Candidate I is the last candidate with no direct contamination evidence**, and it was not in
   the JWST GO 7199 program.
3. **Verdicts.** **D: CONTAMINATION-CONFIRMED** (external, JWST; my archival tests correctly show why
   archival methods alone could not see it — a 1″ blend sits below the WISE centroid floor).
   **I: INDETERMINATE** — no identifiable contaminant in Gaia/Legacy-DR10/UKIDSS data, but the W3/W4
   excess photometry itself is too weak (SNR 2.4/3.3) to localize: its centroid directions flip between
   AllWISE and unWISE coadds. The class prior is heavily against it (9 of 10 labelled candidates now
   show contamination evidence; two JWST-confirmed).
   **Control C reproduces the published refutation** (my W3 offset 3.72″ ± 0.30 vs published 3.67″ ± 0.25).
4. **A quotable unit error found in the contamination literature:** Ren et al. 2024 (arXiv:2405.14921)
   state a Hot-DOG surface density of "9 × 10⁻⁶ per square arcsecond" converted from Assef et al. 2015's
   1 per 31 deg². The correct conversion is 2.5 × 10⁻⁹ arcsec⁻²; 9 × 10⁻⁶ is per square **arcminute**
   (a 3600× slip). With the corrected density, *catalogued* Hot DOGs give only ~0.4 expected alignments
   within 3.25″ across all 5 × 10⁶ stars — they cannot explain 7–10 candidates. What does the work is the
   ~10× fainter red-galaxy population (Suazo's own 15,000 sr⁻¹ estimate ⇒ ~60 expected chance blends in
   the full sample), exactly the kind of faint Hot-DOG-like galaxies JWST found at D and E.
5. **SPHEREx QR2 works as a vetting axis, account-free.** 373 spectral-image planes cover D and 287
   cover I (all six detectors). My forced aperture spectrophotometry reproduces catalog J/H/Ks/W1/W2
   fluxes to ~10% and shows **D photospheric through 5 µm** (agreeing with Hephaistos IV's SPHEREx+MIRI
   analysis) — and the same for I (Section 4). SPHEREx cannot see the 100–200 K excess itself (it ends
   at 5 µm; the excess lives at ≥ 10 µm) and cannot resolve arcsecond blends (6.15″ pixels), but it pins
   the stellar continuum independently of 2MASS/WISE and would catch any *hot* (≳ 600 K) component.

---

## 1. The candidate set and where the literature actually stands (2026-08-18)

Sources: Hephaistos II = Suazo et al. 2024, MNRAS 531, 695
([arXiv:2405.02927](https://arxiv.org/abs/2405.02927), [OUP](https://academic.oup.com/mnras/article/531/1/695/7665761));
Ren et al. 2024 ([arXiv:2405.14921](https://arxiv.org/abs/2405.14921)); Ren et al. 2025
([arXiv:2501.05152](https://arxiv.org/abs/2501.05152)); Ren et al. 2026, MNRAS accepted
([arXiv:2607.03619](https://arxiv.org/abs/2607.03619)); Hephaistos III = Korn et al. 2026
([arXiv:2607.25701](https://arxiv.org/abs/2607.25701)); Hephaistos IV = Zackrisson et al. 2026
([arXiv:2607.09460](https://arxiv.org/abs/2607.09460)). Label → Gaia DR3 mapping: Heph II Table 5 (A–G),
Ren 2026 Table 1 (A–J, J2016 positions), Heph III Table 3 (H–J).

| Label | Gaia DR3 | Origin | Status (evidence) |
|---|---|---|---|
| A | 3496509309189181184 | Heph II | Suggestive contamination — radio counterpart ~4.9″ off, α = 0.40 ± 0.35 (Ren 24; Ren 26 Table 12) |
| B | 4843191593270342656 | Heph II | **Contaminated** (strong) — radio counterpart ~0.4″, power-law α = 0.63 ± 0.11 (Ren 26) |
| C | 4649396037451459712 | Heph II | **Contaminated** (strong) — NIR companion at 3.75″; W3/W4 centroids off 3.7″/5.0″ (Ren 26) — *our control, Section 4* |
| D | 2660349163149053824 | Heph II | **Contaminated — JWST-confirmed**: background galaxy at z ≈ 0.9, ~1″ away, AGN-like MIRI spectrum, Hot-DOG-like SED (Heph IV) |
| E | 3190232820489766656 | Heph II | **Contaminated — JWST-confirmed**: z ≈ 0.4 dusty-starburst-like galaxy ~1″ away (Heph IV); Ren 26 had it "ambiguous" |
| F | 2956570141274256512 | Heph II | Ambiguous (Ren 26): W3/W4 offsets not significant; nearest catalogued sources > 5″ |
| G | 2644370304260053376 | Heph II | **Contaminated** — background AGN (VLASS J233532.86−000424.9), EVN T_b > 10⁸ K (Ren 25) |
| H | 2437221214075471744 | Heph III | Ambiguous (Ren 26): W3 offset 2.6″ at ~2σ; PSF-profile Legacy source ~5″ NE |
| I | 3854090071297359616 | Heph III | **Weakest contamination evidence of all ten** (Ren 26 Table 12); *not* in JWST GO 7199 — the live target |
| J | 651765552072217216 | Heph III | Ambiguous (Ren 26): W3–W4 centroids ~7″ apart; uncatalogued companion at stellar fringe |

Key correction to this project's own README/prospectus (both say "D & I still clean"): that phrasing came
from Ren et al. 2026 (submitted ~3 Jul 2026); **Hephaistos IV appeared 10 Jul 2026 and removed D**. Also:
H, I, J are *not* Hephaistos II candidates — they failed its SNR cut (W3/W4 SNR 2.4/3.3, 2.4/3.3, 2.2/2.8;
Heph III Table 3, "did not meet the WISE-observations SNR criterion") and entered via NOT/ALFOSC
spectroscopy follow-up. Candidate I shows Hα in emission (EW ≈ −2.8 Å) at a level consistent with
ordinary M-dwarf activity, not accretion (Heph III Sec 3.2).

A second stale item: the prospectus says the screen is "Gaia DR3 × CatWISE2020 × 2MASS".
**CatWISE2020 contains only W1/W2** — it cannot host a W3/W4-excess selection. Hephaistos II used
**AllWISE** (their Sec 2.1), and so does my implementation. (A CatWISE2020 W1/W2 side-pull for the ten
candidates — useful later for PM-aware W1/W2 checks — did land after ~25 min of IRSA queueing:
`data/photometry/candidates_catwise.csv`, one match per candidate. Nothing in W1 acceptance depends
on it.)

## 2. W1 — the selection, reproduced (and its reproducibility boundary)

Implementation: `scripts/w1_fetch_candidates.py` (data), `scripts/w1_selection.py` (cuts + model grid),
`scripts/w1_fetch_locus.py` (empirical template colors). Services: ESA Gaia TAP and IRSA TAP, both
anonymous. The cross-match chain is the same one the paper says it used (Gaia-hosted
`allwise_best_neighbour`, `tmass_psc_xsc_best_neighbour`/`join` tables; Heph II Sec 2.1).

### 2.1 The cuts as code (paper section → implementation)

| # | Paper | Cut | Reproducible? |
|---|---|---|---|
| C1 | 2.1 | Bailer-Jones EDR3 geometric distance < 300 pc (`external.gaiaedr3_distance.r_med_geo`) | yes |
| C2 | 2.1 | W3 **and** W4 detections (AllWISE `ph_qual[2:4]` in A/B/C) + contamination-free (`cc_flags = '0000'`) | yes |
| C3 | 2.2–2.3 | star+Dyson-sphere grid fit, RMSE ≤ 0.2 mag over the 10-band BP…W4 SED (Suazo Eqs 1–3) | **partly** — see boundary |
| C4 | 2.4 | CNN nebular-image classifier (11243 → 5732) | **no** — weights + 960 training images unpublished |
| C5a | 2.5.1 | reject Hα pEW < 0 at 3σ (`ew_espels_halpha` ± uncertainty, Gaia DR3 astrophysical_parameters) | yes |
| C5b | 2.5.2 | G_var < 2 (Vioque et al. 2020 Eq; flux-matched median reference) | yes (definition-sensitive, ±0.3) |
| C5c | 2.5.3 | RUWE < 1.4 | yes |
| C5d | 2.5.4 | AllWISE `ext_flg` = 0 | yes |
| C5e | 2.5.5 | `classprob_dsc_combmod_star` > 0.9 | yes |
| C6 | 2.6 | AllWISE W3 SNR ≥ 3.5 **and** W4 SNR ≥ 3.5 | yes |
| C7 | 2.7 | visual inspection of 368 survivors → 7 (89% rejected as blends by eye) | **no** — human judgement |

### 2.2 Acceptance result: 7/7, and H/I/J fail exactly C6

`out/w1_acceptance.csv`. All of A–G pass C1–C6 (C4/C7 cannot gate a 7-object validation — all seven are,
by construction, C4/C7 survivors). H, I, J pass everything except C6 (their W3 SNR 2.2–2.4 < 3.5),
reproducing Heph III's statement precisely.

Cross-checks against published values (all from my pulls, `data/photometry/candidates_gaia_chain.csv` +
`candidates_allwise_irsa.csv`):

- **W3/W4 SNR: exact for all 10 candidates** (e.g. A 22.5/16.6, G 5.0/3.5, I 2.4/3.3 — identical to
  Heph II Table 5 / Heph III Table 3). Side identity established: the published S/N values equal
  1.0857/σ(mpro) from AllWISE to ±0.2 for all 20 values — useful because the Gaia-archive AllWISE copy
  lacks snr columns.
- Distances (Bailer-Jones r_med_geo) and m_G match Table 5 to the printed digits for all ten.
- Hα pEWs match to the printed digits (A +0.248 ± 0.076 nm, E +0.049 ± 0.100, F +0.020 ± 0.068,
  G +0.024 ± 0.097; B/C/D absent in DR3 → cut passes by construction, as the paper notes for >1000
  sources).
- **Erratum-level find: Heph II Table 5 swaps the Gvar and RUWE values for C and D.** Gaia DR3's own
  RUWE for C is 0.909 and for D 0.975; the paper prints C: Gvar 0.90/RUWE 1.21 and D: 0.97/0.96.
  The printed "Gvar" values are the RUWE values (and vice versa). No selection consequence (both < 1.4
  and < 2 either way).
- My G_var values run 1.02–1.36 vs their 0.90–1.03: my median-reference sample is a random all-sky
  G-mag-matched pull (116,075 stars), theirs was presumably in-sample. All < 2 → identical cut outcome;
  the observable's exact value is reference-sample-dependent (worth remembering for W4).

### 2.3 The reproducibility boundary (the finding)

**(i) The model-grid floor contradicts the paper's own candidate F.** The stated initial grid is
T_DS ∈ [100, 700] K, **γ ≥ 0.1** (Heph II Sec 2.2); the stated gate is best-model RMSE ≤ 0.2 mag
(Sec 2.3). F's published refit is γ = 0.03 ± 0.008 (Table 5) — 9σ below the stated grid floor. With my
templates, *no* γ ≥ 0.1 model fits F at RMSE ≤ 0.2 (best 0.255; the model W4 overshoots by 0.69 mag);
the gate opens only when models with γ ≤ 0.07 are admitted (γ floor 0.07 → RMSE 0.170; 0.01 → 0.081).
So either their initial grid actually extended below γ = 0.1, or their template pool absorbed the
difference in a way the description does not capture. My implementation therefore runs C3 with the
γ floor relaxed to 0.01 (documented in-code); with the floor *as stated*, the acceptance is 6/7.

**(ii) The 265 template stars are not published.** I substituted: optical/NIR/W1 template magnitudes
from the Pecaut & Mamajek 2013 empirical dwarf locus
([EEM table v2022.04.16](https://www.pas.rochester.edu/~emamajek/EEM_dwarf_UBVIJHK_colors_Teff.txt)),
which however has **no W1−W2/W1−W3/W1−W4 colors for K6V–M4.5V** — exactly the candidates' range — so the
photospheric MIR colors come from my own empirical locus: 1320 clean dwarfs within 30 pc with
significant W3/W4 (`scripts/w1_fetch_locus.py`; validated where PM13 exists: locus W1−W3 = −0.01 at
M_G 6.75 vs PM13 K5V −0.029). Blackbody MIR colors are *wrong* for this (+0.2 mag at K5V — checked, and
that is why the model is empirical-template-based in the first place). Template diversity matters: the
fit admits ±1σ of the locus's per-star MIR color scatter (0.03–0.16 mag), emulating "best of 265 real
stars". With these substitutions the refined-grid refits land near the published (T_DS, γ) for all ten
(e.g. D: 184 K/0.17 vs published 178 ± 20 K/0.16 ± 0.03; F: 144 K/0.042 vs 137 ± 16 K/0.03 ± 0.008;
H: 138 K/0.098 vs 130 ± 21 K/0.103 ± 0.027; `out/w1_ds_fits.csv`).

**(iii) C4 (CNN) and C7 (visual) are irreproducible-by-design,** and they carry most of the late-stage
selectivity: 11243 → 5732 (CNN) and 368 → 7 (eyes; 89.1% of the 368 rejected as blends, Heph II
Sec 2.7). Any W4 re-screen must replace these with something auditable — which is this project's
whole thesis (centroid tests + contamination priors as code).

**(iv) Approximations in my C3** (documented, none gate-relevant at the 0.2-mag level): monochromatic
band fluxes at isophotal wavelengths (Wright et al. 2010 Table 1; Cohen et al. 2003 2MASS zero points;
W1–W4 zero points 309.540/171.787/31.674/8.363 Jy per the AllWISE Explanatory Supplement IV.4.h /
Jarrett et al. 2011); no extinction correction (the paper does not deredden either; A_G ≈ 0.2–0.3 for
these stars per Gaia GSP-Phot, absorbed by template choice and the equal-weight RMSE).

### 2.4 Throughput on a bounded field and the honest W4 cost

Field: RA [140°, 150°] × Dec [0°, 10°] = 99.5 deg² (contains candidate I; |b| ≈ 30–45°).
`scripts/w1_throughput.py`, `out/w1_throughput.json`.

| Stage | This field (99.5 deg²) | Paper full sky (Table 4) | Rate check |
|---|---|---|---|
| Gaia×2MASS×AllWISE sample, < 300 pc | 12,783 | ~5 × 10⁶ | 5e6/41253 × 99.49 = 12,060 expected → **+6%** ✓ |
| … with AllWISE best-neighbour | 11,444 | — | — |
| W3 **and** W4 detections | 783 | ~3.2 × 10⁵ | 6.1% vs their 6.4% ✓ |
| cc_flags clean | 730 | (folded into above) | — |
| RMSE ≤ 0.2 (fitted subset) | 10 of 207 fitted | 11,243 of ~3.2 × 10⁵ | 4.8% vs 3.5% (see note) |
| + extra cuts (C5a–C5e) | 9 | 5732 → 5137 | — |
| + SNR ≥ 3.5 (C6) | **0** | 368 | 368/41253 × 99.49 = 0.89 expected; P(0) = 0.41 ✓ |
| final candidates | 0 | 7 | 0.017 expected per field |

Note: my RMSE stage only fits stars inside the template locus validity (M_G 6–14.5, i.e. K/M dwarfs;
207 of the 707 stars with full 10-band photometry) — the paper's 265 templates spanned M_G 0–13.6.
For throughput accounting the unfitted 500 earlier-type stars would add ~15 s of grid time; for W4 the
locus needs extending blueward (same query, wider M_G window, more W3W4-detected templates available).

Timings, measured 2026-08-18 (ESA load-variable — T0 took 23 s at one point and 116 s at another):
server queries 407 s total for the field (T0 count 116 s; T1 count 90 s; T2 star pull 44 s; chunked
AllWISE/2MASS/Hα PK lookups 157 s), local cuts + RMSE grid 7 s (33 ms/star × 207).

**Honest full-screen (W4) cost.** Naive per-field TAP scaling: 407 s × 415 fields ≈ **47 h** of serial
anonymous queries — but today's session showed byte-identical queries varying 4–5× with server load and
sync jobs timing out outright; the realistic per-field TAP figure is 2–6 days of babysat, retry-taxed
querying. The right route is **~24 sky-strip async jobs** on the 3-table join (each ≈ 220k rows;
~5.3 × 10⁶ rows / ~1–2 GB total — matching the paper's parent-sample size), then chunked PK lookups for
the W3W4-detected ~330k (≈ 660 queries), then local: RMSE grid ≈ 3 h single-core (embarrassingly
parallel), Gvar from in-sample binned medians (free), C5/C6 trivial. New vetting stages on survivors
only: ~370 expected pre-visual survivors × 4 AllWISE cutouts ≈ 1500 IRSA IBE fetches ≈ 2–4 h, plus the
chance-alignment budget fitted from the screen's own detected population. **Total: 2–4 days wall-clock,
zero money, no accounts — dominated by archive-side queueing, not compute.** (For contrast: a bulk
download of the AllWISE source table from IRSA's bulk distribution would remove the chunked-lookup
stage at the cost of a very large download; not needed at this scale.)

## 3. W2 — vetting: control C, then D and I

Method per Ren et al. 2026: compare Gaia DR3 positions (epoch-propagated to the per-band AllWISE mean
epoch with Gaia PMs) against MIR emission centroids measured from AllWISE Atlas cutouts (IRSA IBE,
account-free), with unWISE full-depth coadds (Lang 2014; unwise.me) as a second imaging basis.
`scripts/w2_centroids.py`; figures `out/w2_cutout_{C,D,I}.png`; table `out/w2_centroid_offsets.csv`.
Centroiding uncertainty = FWHM/(2.355·SNR) (Ren 26 Eq 1) with aperture SNR measured against
random-aperture scatter (correlated-noise honest; a per-pixel estimate flatters SNR by ~5–10×).

### 3.1 Control: candidate C reproduces the published refutation

| Band | This work (AllWISE) | This work (unWISE) | Ren 2026 published |
|---|---|---|---|
| W1 | 0.74″ ± 0.11 | — | 0.82″ ± 0.09 |
| W2 | 0.69″ ± 0.20 | — | 0.76″ ± 0.13 |
| W3 | **3.72″ ± 0.30** | 3.60″ ± 0.26 | **3.67″ ± 0.25** |
| W4 | **4.80″ ± 1.67** | 5.18″ ± 1.54 | **4.98″ ± 2.15** |

The signature — W1/W2 on the star, W3/W4 centroids pulled ~4–5″ toward the NIR companion (VMC
J045603.25−741010.66 at 3.75″, Ren 26) — reproduces on both coadd bases, by eye in the cutout figure
and numerically to ≲ 0.2″. The machinery is validated. (Note: the companion itself is *not* in Legacy
DR10 within 8″ — my Datalab query returns only the star and an unrelated source at 7.8″ — it is
NIR-detected only. Deep optical catalogs alone would have missed C's contaminant.)

### 3.2 Candidate D — contamination confirmed externally; what archival data alone says

- My offsets: W1 0.15″ ± 0.04, W2 0.23″ ± 0.07, W3 1.41″ ± 0.21 (unWISE: 1.07″ ± 0.22),
  W4 2.55″ ± 0.50 (unWISE: 2.15″ ± 0.97). Ren 26: 0.53/0.46/0.75 ± 0.22/1.80 ± 1.80 — same story:
  **the smallest offsets of the whole set** (their Rayleigh test: indistinguishable from control stars).
- **JWST (Heph IV) settles it**: the excess belongs to a background galaxy at z ≈ 0.9 at ~1″ projected
  separation; the M dwarf is photospheric in F560W/F1000W/F1500W (star contributes ≈ 80/10/2% of the
  MIRI flux); the galaxy is point-like with an AGN-indicating MIRI spectrum, Hot-DOG-like SED, hot-dust
  component ≈ 90 K.
- **The method lesson (JWST-calibrated):** a real contaminant at 1.0″ produced AllWISE centroid offsets
  of only ~0.5–1.4″ (band- and basis-dependent) — *below* any defensible detection threshold against
  the ~0.2–0.5″ control-star floor. Heph IV Sec 5.2 says it outright: the centroid method "provided no
  evidence for interloper contamination in the case of candidate D". **Centroid vetting has a hard
  sensitivity floor at roughly 1–2″ separations; blends inside it pass every archival test.** This
  number belongs in any W4 re-screen design.
- My Legacy DR10 check (`data/photometry/legacy_dr10_D.csv`, NOIRLab Datalab TAP): nothing catalogued
  at ~1″; nearest source is the known REX galaxy at 2.97″ SE (Ren 26's Legacy 10995494344987809). The
  z ≈ 0.9 galaxy that kills D is **invisible to the deepest wide-field optical survey** — it took MIRI.
- Photosphere+excess decomposition (`out/w2_sed_D.png`): T_excess = 184 K, γ = 0.17, RMSE 0.135 over
  147 archival VizieR points from 26 catalogs — a perfectly good "Dyson sphere" fit that is, per JWST,
  a z ≈ 0.9 AGN. **An SED fit alone cannot distinguish the two; only resolution can.**
- Per-position chance-alignment odds (from `out/w2_chance_alignment.csv`): P(≥1 background red galaxy
  within the JWST-measured 1.0″) = 1.1 × 10⁻⁶ per star at Suazo's 15,000 sr⁻¹ density — i.e. ~6
  expected among the 5 × 10⁶ parent stars (Heph IV's number). D being one of them is unremarkable;
  under catalogued-Hot-DOG densities (corrected Ren 24 / Assef 15) the same probability is 8 × 10⁻⁹,
  which is *why the contaminant had to be a fainter object than any catalogued Hot DOG* — as observed.

**Verdict D: CONTAMINATION-CONFIRMED** (Zackrisson et al. 2026, JWST GO 7199) — was *not* recoverable
from archival data alone; archival-only grading (Ren 26 and this work) correctly said "weak evidence".

### 3.3 Candidate I — the last one standing

- My offsets: W1 0.21″ ± 0.02, W2 0.33″ ± 0.06 (star-locked); W3 2.64″ ± 1.15 at aperture SNR 2.4
  (Ren 26: 2.10″ ± 0.62 at ~2σ — they call the W3 emission "an extended stripe", centroid taken on the
  SE peak); W4 5.49″ ± 0.99 at SNR 5.2 pointing NNW (Ren 26: 3.22″ ± 2.15, also N).
- **The two coadd bases disagree**: unWISE gives W3 4.29″ ± 1.43 (SNR 1.9) and W4 1.11″ ± 2.23
  (SNR 2.3) — the W3 and W4 centroid *directions flip* between AllWISE and unWISE. At SNR 2–5 the
  excess cannot be localized; the offsets are noise-dominated. (Consistent with Ren 26's Rayleigh-test
  non-detection of significant offsets.)
- Deep catalogs: Ren 26 find no companion within 3″ in Legacy/UKIDSS. My Datalab pull
  (`legacy_dr10_I.csv`) confirms nothing within 6.5″ of the star — but flags **an extremely red
  PSF-profile source 6.77″ NE (PA 37°)**: g = 25.6, r = 24.8, z = 20.26 (r−z ≈ 4.5), Tractor-forced
  W4 comparable to the star's. Caveats: Tractor's forced W4 splits one unresolved 12″-beam blob between
  positions, so its W4 brightness is a deblending outcome, not independent evidence; at 6.8″ it lies
  outside the W3 PSF half-width (3.25″) though inside the W4 beam, on the same side as the (unstable)
  northward W4 centroid pull. Worth one line in any follow-up proposal; not evidence today.
- SED (`out/w2_sed_I.png`, 179 archival points): clean M3.5-dwarf photosphere from 0.4 to 4.6 µm;
  excess fit T = 125 K, γ = 0.085 (published: 99 ± 20 K, 0.147 ± 0.046). **The entire excess rests on
  two photometric points at SNR 2.4 and 3.3** — the fit is unconstrained between "cool Dyson sphere",
  "faint background Hot-DOG-like galaxy", and "W3/W4 noise fluctuations on a faint-star aperture".
- Chance-alignment context (Section 3.4): among 5 × 10⁶ stars, ~40–60 chance superpositions with faint
  red galaxies inside the W3 beam are *expected* (using Suazo's own background density); ten candidates
  were found. At the population level, chance alignment fully accounts for the candidate yield — no
  candidate-specific rescue is needed. Per-position: P(≥1 red background galaxy within I's measured
  2.64″ W3 offset) = 7.7 × 10⁻⁶ per star at 15,000 sr⁻¹ (≈ 39 expected in 5 × 10⁶; ≈ 1.5 in the
  2 × 10⁵ SNR-cut subsample); within the 3.25″ W3 half-width, 1.2 × 10⁻⁵ per star.

**Verdict I: INDETERMINATE.** No direct contaminant identified (unlike A–E, G, H, J) — *and* no
detectable excess robust enough to vet. The honest statement: I's excess is a 2–3σ W3/W4 measurement
whose centroid cannot be stabilized between coadd generations; its siblings' fate (9/10 with
contamination evidence, 2 JWST-confirmed) and the population-level chance-alignment budget make
background contamination the default hypothesis, but nothing in the archival record singles out a
culprit. What would settle it: JWST/MIRI imaging (as for D/E — I is *not* in GO 7199), or a deep
10–25 µm ground shot; SPHEREx cannot (Section 4).

### 3.4 Chance-alignment arithmetic, re-derived (`scripts/w2_chance_alignment.py`)

All published internal numbers reproduce: Suazo's 1.1 × 10⁻⁵ per star within r = 3.25″ at their
15,000 sr⁻¹ red-galaxy density, and their "~2 expected" in the 2 × 10⁵ SNR-cut subsample; Heph IV's
"~60 expected" when (correctly, since blends *create* W3/W4 detections) applied to the full 5 × 10⁶;
Heph IV's required densities ≥ 0.55 deg⁻² (r = 3.25″) or ≥ 5.8 deg⁻² (r = 1″) for 7 candidates.

**The unit error:** Ren et al. 2024's "surface density of approximately 1 per 31 square degrees (Assef
et al. 2015), which translates to about 9 × 10⁻⁶ per square arcsecond" is wrong by 3600×:
1/31 deg⁻² = 2.49 × 10⁻⁹ arcsec⁻² = 8.96 × 10⁻⁶ **arcmin⁻²**. Consequence: with the density *as
printed*, one expects ~1500 chance alignments within 3.25″ among 5 × 10⁶ stars — "explains everything"
trivially; with the *correct* conversion of the same catalogued-Hot-DOG density, one expects **0.41**
— catalogued Hot DOGs explain *nothing like* all seven. The qualitative conclusion survives only via
Heph IV's argument: the contaminants are Hot-DOG-*like* galaxies ~1–5 mag fainter than the catalogued
samples (exactly what MIRI found at D and E), needing number counts ~10–100× higher at the faint end —
plausible but *unmeasured*. The re-screen (W4) should treat the faint-red-galaxy density as a parameter
to be fit from our own data, not a literature constant.

## 4. W3 — SPHEREx QR2 at D and I

Route (`scripts/w3_spherex.py`, all account-free): IRSA TAP `spherex.plane` ⋈ `spherex.artifact` for
science-image URIs at each position; server-side cutouts via `…fits?center={ra},{dec}d&size=120arcsec`;
per-exposure wavelength from the WCS-WAVE extension (key "W") at the target pixel; flux = background-
subtracted 2-px (12.3″) aperture sum, MJy/sr → Jy via pixel solid angle; errors from the VARIANCE
extension. (Discovered via the IRSA SPHEREx docs + `irsa-tutorials` cutout notebook; Heph IV used the
IRSA spectrophotometry tool for the same QR2 data at D/E, so this axis has a published precedent.)

- **Coverage: D 373 planes, I 287 planes, all six detectors (D1–D6, 0.75–5.0 µm), MJDs 60790–61213**
  (2025-04 → 2026-06; both targets have ≥ 2 sky passes).
- **Extraction validation (D):** medians vs catalog — J 1.71/1.62, H 1.90/1.89, Ks 1.58/1.41,
  W1 0.96/0.93, W2 0.63/0.67 mJy → ~10% agreement with no aperture correction. Known bit-21 flag set on
  essentially all pixels (informational; exact bit meanings live in the SPHEREx Explanatory Supplement
  §3.2.4 at IRSA — treated empirically here, only other bits masked).

- **Results (D, 352 kept exposures; I, 271 kept):** both stars show a clean M-dwarf spectral shape
  from 0.75 to 5.0 µm that tracks the 2MASS/WISE photometry and **declines photospherically through
  the last SPHEREx bin (4.8–5.0 µm: D 0.62 mJy, I 0.60 mJy)** — no excess onset, no hot component.
  For D this independently reproduces Hephaistos IV's SPHEREx result (their Fig. 2); **for I this is,
  to my knowledge, the first extraction of its SPHEREx spectrum** (I was not in Heph IV).
  Numeric validation vs catalog (medians, mJy):

  | window | D SPHEREx | D catalog | I SPHEREx | I catalog |
  |---|---|---|---|---|
  | J 1.15–1.35 µm | 1.71 | 1.62 | 2.74 | 2.73 |
  | H 1.55–1.75 µm | 1.90 | 1.89 | 3.11 | 2.82 |
  | Ks 2.0–2.3 µm | 1.58 | 1.41 | 2.45 | 2.27 |
  | W1 3.2–3.5 µm | 0.96 | 0.93 | 1.27 | 1.30 |
  | W2 4.4–4.8 µm | 0.63 | 0.67 | 0.92 | 0.85 |
  | 4.8–5.0 µm | 0.62 | — | 0.60 | — |

  Figure: `out/w3_spherex_seds.png`; per-exposure tables `out/w3_spherex_{D,I}_sed.csv`.
  Cost datum for scaling this axis: ~370 (D) + ~290 (I) server-side cutouts, ≈ 45 min per target
  wall-clock at IRSA's pace on 2026-08-18, ~100 KB per cutout cached locally.

**What SPHEREx can and cannot contribute to this vetting problem** (the honest scoping): the candidate
excesses are 100–200 K blackbodies peaking at 15–30 µm with essentially zero flux below 5 µm — *outside
SPHEREx's band*. And with 6.15″ pixels (measured from the cutout WCS; PSF of order a pixel), SPHEREx
blends star+contaminant exactly as WISE W1/W2 do. What it does
provide: (i) an independent 102-band check that the *photosphere* model used in every excess claim is
right (it is, for D and I); (ii) sensitivity to *hot* components (≳ 600 K dust or a very red companion
would bend the 3–5 µm continuum — none seen at either target); (iii) for the W4 re-screen, a
photosphere-anchoring axis that does not exist in the 2MASS→WISE gap. The "smooth thermal MIR rise vs
blend" discrimination the prospectus hoped for needs ≥ 10 µm resolution (JWST/MIRI), not SPHEREx.

## 5. Cost plan for W4 (the full ~5M-star re-screen)

Summarized from Section 2.4's measurements: **2–4 days wall-clock, zero money, no accounts.**
Sequence: (1) ~24 ESA async strip jobs → the 5.3M-row parent sample with `allwise_oid` (~1–2 GB CSV,
gitignored); (2) chunked PK lookups for the ~330k W3W4-detected rows (AllWISE mags/flags, 2MASS, Hα);
(3) local coded cuts C1–C6 incl. the RMSE grid (~3 h single-core; template locus extended blueward
first); (4) the *new* stages this project exists for, on the ~10²–10³ survivors: AllWISE+unWISE
centroid offsets with the JWST-calibrated 1–2″ sensitivity floor stated per object, per-object
chance-alignment priors fitted from the screen's own W3W4 population (not literature constants — see
the Ren 24 unit error), Legacy-DR10/VHS/UKIDSS neighbor pulls, and SPHEREx photosphere anchoring where
useful. Deliverable either way: a vetted extreme-IR-excess catalog with per-object contamination
priors, or a calibrated null on the method's yield. Risks: ESA/IRSA queue variance (observed 4–5×
today, incl. outright sync timeouts); the CNN/visual stages are *not* reproduced — their replacement
(coded centroid + prior stages) is the point, but it means my funnel and the paper's diverge after C6
by design.

## 6. Recommended M2

1. **Retire D formally; make I the single-object deliverable.** Assemble the I dossier as a short
   RNAAS-style note *candidate-level claim, Matthew-gated*: the SNR-2.4 excess, the coadd-basis
   centroid instability (new, this work), the 6.8″ red neighbor (new), the SPHEREx photosphere
   (new — first published SPHEREx spectrum of I), and the population-level chance-alignment budget.
   The honest framing: "the last uncontaminated Dyson-sphere candidate is an unvettable 2σ excess" —
   which is itself the technosignature-hygiene result.
2. **W4 proper**: bulk-download route (Gaia×AllWISE best-neighbour + AllWISE via bulk files, not TAP),
   coded cuts C1–C6 + **centroid-offset stage with the JWST-calibrated 1–2″ floor documented** +
   chance-alignment budget fitted from the screen's own W3W4-detected population. Deliverable either
   way: the vetted extreme-IR-excess catalog with per-object contamination priors, or the calibrated
   null on the method's yield.
3. **SPHEREx axis generalization** (cheap now that the extractor exists): run the forced
   spectrophotometry on all ten candidates + the F/H/J ambiguity tier; a hot-component non-detection
   across the set is a publishable constraint on the "warm structure" corner of DS parameter space.

## 7. File index

- `scripts/w1_fetch_candidates.py` — Gaia chain + IRSA AllWISE/CatWISE pulls (10 candidates)
- `scripts/w1_fetch_locus.py` — empirical M-dwarf photospheric WISE-color locus (1320 stars < 30 pc)
- `scripts/w1_selection.py` — the cuts + star+DS grid (Suazo Eqs 1–3); acceptance table
- `scripts/w1_throughput.py` — 99.5 deg² field funnel + timings
- `scripts/w2_centroids.py` — AllWISE/unWISE centroid offsets (C, D, I) + cutout figures
- `scripts/w2_chance_alignment.py` — density conversions + expectations (all variants)
- `scripts/w2_sed.py` — VizieR sed harvest (CDS; CFA mirror fallback — main sed backend still
  half-broken on 2026-08-18, truncated VOTables with Postgres errors) + photosphere/excess fits
- `scripts/w3_spherex.py` — SPHEREx QR2 forced aperture spectrophotometry (D, I)
- `out/w1_acceptance.csv`, `out/w1_ds_fits.csv`, `out/w1_throughput.json`,
  `out/w2_centroid_offsets.csv`, `out/w2_chance_alignment.csv`, `out/w2_sed_fits.csv`,
  `out/w2_cutout_{C,D,I}.png`, `out/w2_sed_{C,D,I}.png`,
  `out/w3_spherex_{D,I}_sed.csv`, `out/w3_spherex_seds.png`
- `data/` (gitignored): papers (arXiv HTML+txt), photometry pulls, AllWISE/unWISE cutouts, SPHEREx
  cutout cache (~500 × ~100 KB), Legacy DR10 neighbor lists
