# dyson-revet — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-18** — **M2 ◐** ([M2-dossier-and-screen.md](M2-dossier-and-screen.md)) — three
  deliverables done, W4 running. **D formally retired** everywhere (README premise block, dated
  annotation on M1, §3.2 closure note): contamination-confirmed by JWST/Hephaistos IV, kept only as
  the *calibration* of the centroid method's blind spot (a real 1.0″ contaminant moved the AllWISE
  centroid by 0.5–1.4″). **[I-dossier.md](I-dossier.md) written** (Matthew-gated) — headline: *the
  last candidate standing is unvettable, not unrefuted*. Five new findings, all pointing the same
  way: both W3 and W4 are **sub-5σ against WISE's own on-ecliptic sensitivity** (0.44× and 0.62×;
  the target sits at β = −6.6°); the "detections" (0.375, 3.36 mJy) fall **inside the 95% upper
  limits of all nine AllWISE neighbours** (0.31–0.58, 2.07–3.79 mJy — the nearest neighbour's W4
  *limit* is brighter than I's *detection*); W3 is a **non-detection (ph_qual 'U', S/N 1.3) in the
  WISE All-Sky release** of the same photons; **w3nm = 0, w4nm = 1** (never seen in a single
  exposure); and the **independent aperture photometry never detected W4** (w4flg = 32 = 95% upper
  limit). Excess restated in flux: W3 **1.3σ**, W4 **3.3σ**, joint 3.5σ pre-trials — the "12σ" W1−W4
  colour excess is a 3.3σ flux measurement. **Nothing but WISE has ever observed this position above
  5 µm** — Spitzer, JWST, Herschel and ISO footprints all checked with positive controls: not
  covered. What settles it: **JWST/MIRI imaging, 2 filters, one visit, ≈1.2 h charged** (711× the
  F2100W sensitivity limit; 0.685″ FWHM vs WISE's 12″). Finder chart + SED: `out/m2_I_finder.png`,
  `out/m2_I_sed.png`. **New: JWST GO 7199 has a THIRD target — candidate A (0.95″ match), observed
  14 Jul 2026, absent from Hephaistos IV.** **Ren+24 unit-error note drafted, NOT SUBMITTED**
  (1,048 words vs RNAAS's 1,500 inclusive limit, one table): corrected, catalogued Hot DOGs give
  0.41 of the 7 candidates, not all; Suazo's own faint red-galaxy density gives 5.5 within 1″ against
  5.78 deg⁻² required — which is what JWST found. **Prior art exists**: Blain 2024 fn 6 flagged it
  "(sic)"; no erratum, no v2, sentence still in the abstract of record. **W4 route corrected —
  anonymous ESA async is dead** (HTTP 500 on every job; M1 costed a leg it never measured); sync has
  a ~181 s wall that is **independent of tile size**, so retry beats splitting. Screen now runs
  6-table server-side joins (deletes M1's ~10⁴ chunked-lookup stage), checkpointed per tile,
  resumable, tiles issued in pseudo-random sky order so a partial screen is unbiased. **γ-floor
  finding: the paper's stated γ ≥ 0.1 grid reproduces its own funnel to ~1.4× at every stage; the
  γ ≥ 0.01 floor needed to admit their candidate F inflates survivors ~9×** (97 → 850 RMSE
  survivors, 5 → 25 pre-visual finalists on the same 1,762 stars; at γ ≥ 0.10 the 5 finalists are
  Poisson-consistent with the 6.7 the paper's rate predicts for this area). Screen runs at γ ≥ 0.10. **W4 progress at
  session end: 4/192 tiles, 752 deg² (1.82% of sky), 6,422 W3W4-detected rows, ~7 h projected to finish** — resume with one command (M2 §4.4).

- **2026-08-18** — **M1 ✓** ([M1-reproduce-and-vet.md](M1-reproduce-and-vet.md)). Selection
  reproduced **7/7** (catalog cuts as code; H/I/J fail exactly the SNR cut as Heph III states);
  boundary documented — candidate F (γ=0.03) is incompatible with the paper's stated γ≥0.1 model
  grid, the CNN + visual stages are unpublishable-irreproducible, and Heph II Table 5 swaps C/D's
  Gvar↔RUWE. **Premise correction: D was killed by JWST on 10 Jul 2026** (Hephaistos IV,
  arXiv:2607.09460 — z≈0.9 galaxy 1″ away; my centroid test shows why archival methods can't see
  1″ blends). **I is the last candidate standing: verdict INDETERMINATE** (2σ excess, centroid
  directions flip between AllWISE/unWISE coadds, no contaminant in Legacy DR10/UKIDSS; new: a very
  red PSF source 6.8″ NE). Control C reproduces the published refutation to 0.05″ (W3 3.72″ vs
  3.67″). Found + verified a **3600× unit error** in Ren et al. 2024's hot-DOG density (9e-6 is per
  arcmin², not arcsec²): catalogued Hot DOGs explain ~0.4 candidates, not all 7 — the contaminant
  class is the ~10× fainter red-galaxy population (S24's own 15000/sr ⇒ ~60 expected among 5M).
  **SPHEREx QR2 axis opened, account-free**: 373/287 planes at D/I, forced spectrophotometry
  validates to ~10% vs catalogs, both stars photospheric through 5 µm — but the 100–200 K excess
  band is beyond SPHEREx; the discriminating axis stays ≥10 µm (JWST). Throughput measured on a
  99.5 deg² field: funnel rates match the paper stage-for-stage (12,783 in-sample vs 12,060
  expected; 6.1% W3W4-detection vs their 6.4%; 0 finalists vs 0.02 expected) — **W4 full screen
  costs 2–4 days wall, zero money** (24 ESA async strips + chunked lookups + 3 h local grid).
  CDS sed main host still half-broken (truncated VOTables); CFA mirror works; IRSA catwise_2020
  cone queries took ~25 min of queueing but landed (10/10). Next (M2
  proposal in doc §6): I dossier as the deliverable (Matthew-gated), W4 via async strips +
  centroid stage with the JWST-calibrated 1–2″ floor.

- **2026-08-17** — Folder created from run-3 avenue #7 (wave 4). First agent launched: W1
  (reproduce the Hephaistos II selection; acceptance = recover all 7 published candidates) +
  W2 on the two surviving candidates (D, I: centroid-offset + density priors) + W3 coverage
  check (SPHEREx QR2 at candidate positions). Nothing verified yet.
