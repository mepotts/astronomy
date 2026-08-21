# dyson-revet — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-21** — **M3 ◐** ([M3-full-screen.md](M3-full-screen.md)) — **the screen is delivered on
  48.18% of the sky and reported as such; the pull could not be finished because ESAC is down for
  joins.** Coverage unchanged at **93 tiles / 19,874 deg²**: ESAC served **zero** tiles in ~3.5 h
  across two resume attempts, answering `SELECT TOP 5` in 1.3 s while killing every query touching
  the join tables — a bare 3-table `COUNT(*)` died at 79.8 s, and the wall is **size-independent**
  (13.4–214.9 deg² all die at 61.5–62.7 s), so splitting cannot help. **The 2026-08-19 stall is
  diagnosed**: 679 of 680 outage failures returned in **0.2–0.3 s** vs **181.6 ± 0.3 s** for real
  load failures, and the driver spent 99 tiles' retry budgets in seconds; instant failures now cost
  no retries, an outage breaker stops cleanly, and **no tile is abandoned** (100 sit in `retry`,
  resumable). Two funnel-corrupting bugs fixed: `repair` resurrected the descendants it had just
  deleted, and parent/child **area was double-counted**. **Funnel at γ ≥ 0.10 with Poisson
  intervals**: 220,632 W3W4-detected → 4,773 RMSE (**0.88×** the paper) → 4,257 → **845 pre-visual
  survivors against 177 expected = 4.77× [4.60–4.94]**; the pilot's RMSE deficit really was the
  truncated template window. **The ~9× γ-floor finding is corrected to 5.83×** (and 5.0× → 2.93× at
  the pre-visual gate). **Flagged, not explained: the parent sample is 1.43× the paper's** —
  457,960 projected vs ~3.2 × 10⁵ — so no absolute sky-wide yield should be quoted yet.
  **845 finalists vetted with the coded gates: 416 CONTAMINATION-CONSISTENT, 326 INDETERMINATE,
  103 SUB-THRESHOLD, 0 STILL-CLEAN — no Matthew-gated candidate.** M2's two invented axes measured
  at scale: **18.3% were never detected in a single W4 exposure**, and **13.3% have an excess band
  the All-Sky release calls a non-detection and AllWISE promotes — with the reverse happening zero
  times.** **The centroid axis was refused a vote**: at scale its 10″ peak search locks onto
  brighter neighbours (a 9.51″ "offset" is a 2.4×-brighter source at 10.24″; an 11.89″ one is a
  14×-brighter source at 16.36″), so it was disabled rather than retuned — hundreds would otherwise
  have been convicted on an unrelated neighbour. Also fixed: the centroid cutout silently **clipped
  at coadd-tile edges** (IBE's first row is often a corner tile) which manufactured 7.6–11.9″ fake
  offsets; control C still reproduces at **3.72″ vs published 3.67″**. **Both method caveats
  closed**: `ew_espels_halpha` is negative-for-emission (three sources) and the implementation was
  **already correct** — but the cut is **near-inert** (0.001 recovery for active M dwarfs) and
  **3 of the paper's 7 candidates were never testable by it** (G > 17.65; D misses by 0.011 mag);
  and the template locus is **extended blueward** from PM13's own tabulated colours (validated to
  rms 0.050 mag = 0.022 mag in the 10-band RMSE, **zero regression** on M1's 7/7), taking the fitted
  fraction from 32% to **98.6%**. **GO 7199's third target: still unpublished** — the JWST-vetted
  sample is **still 2, not 3**; candidate A's data are closed until **2027-07-16**, but **D's are
  already public** and **E's open 2026-09-09**. **M4 route measured**: the **AIP mirror** hosts every
  needed catalogue and **anonymous async works with no account** (30 s cap ⇒ ~27 deg² tiles); its
  only gap, Bailer-Jones distances, is covered by a parallax proxy calibrated here to **99.09%
  recall** (purity still unmeasured). Nothing submitted, posted or sent; the Ren+24 note and the
  I dossier remain Matthew-gated, unchanged.

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
