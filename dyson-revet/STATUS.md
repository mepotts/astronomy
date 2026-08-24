# dyson-revet — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-24** — **M6 ✓** ([M6-morphology-mrs-completeness.md](M6-morphology-mrs-completeness.md)) —
  **the morphology stage is built and it closes 5.1 of the last 17.8 points, not all of them — and
  the remainder is named.** **N4** reads the AllWISE W3/W4 coadds directly:
  **S = σ_obs/σ_exp** in a 12–45″ annulus, the robust dispersion of the PSF-smoothed image over what
  the coadd's *own uncertainty image* predicts — one line, **no training set, and a parameter-free
  null of 1** (measured **1.396 / 1.245** on 27,876 |b| > 50° parent stars). Its threshold is
  **M5 PR-2's N2 rule verbatim** — percentile in ecliptic bins of the |b| > 50° parent, max over
  bands, 0.99 — so **no new free parameter anywhere**; measured combined FPR **1.20%**. **All three
  validation criteria pass: 7/7 published candidates preserved** (N4 flags 0 of 10 labelled), the
  flagged fraction falls **monotonically** with |b| — **70.3, 36.3, 24.9, 6.0, 2.3, 1.1%** — and at
  |b| > 50° that **1.14% is below the stage's own 1.20% false-positive rate**: it does nothing where
  M4 proved nothing needs doing. **Median structure index 12.50 at |b| < 5° to 1.41 at |b| > 50°**,
  a factor of nine on a statistic whose noise value is 1. **Funnel: pre-visual survivors
  1,545 → 585 (M5) → 411 against the paper's 368; overproduction 4.20× → 1.59× → 1.117×** (1.211×
  area-corrected), **96.3% of the excess removed**, and **every latitude band now within ±50% of the
  published rate** (0.78, 1.19, 1.48, 0.98, 1.13, 1.02×). **But the 17.8 points are only partly
  closed and the doc says so**: at the RMSE gate ours rejects **36.3%** against their CNN's
  **49.0%** — **5.1 points closed, 12.7 remaining**, with the candidates for the residual stated
  rather than guessed. **N4 sees what N1 and N2 cannot: 486 objects — 5.1% of RMSE survivors — that
  no catalogue lists and whose background is not in the top 1%**, exactly the category M5 §3.6
  predicted and could not measure. **Its one failure mode was found before it could matter and
  bounded**: on clean sky S flags **70.1%** of sources brighter than W3 = 5 (PSF wings fill the
  annulus) — and **zero survivors are that bright**; against a **magnitude-matched** expectation the
  enrichment is **289× at |b| < 5°, 88× all sky**. **Candidate D's MRS cubes are reduced — 12 public
  L3 cubes, 4.90–28.70 µm, 11,625 slices deblended, `CAL_VER 2.0.1 / CRDS jwst_1535`, the same newer
  re-reduction M4 found for the imaging — and the first independent extraction of the contaminant's
  spectrum now exists. It cannot settle z ≈ 0.922, and the reason is measured rather than asserted.**
  **PR-2's acceptance test FAILS 4-of-6, and the structure of the failure is the finding: in every
  band the *dominant* member of the pair passes and only the *sub-dominant* one fails** — PSF-wing
  leakage across 1.23″, which is a hard limit on any parametric deblend of a close pair and a direct
  warning for E. **PR-2's consequence is honoured: no redshift is quoted.** The blind
  cross-correlation's best z moves **0.47 → 1.06** for a ±0.02 dex change in the continuum window; a
  blind narrow-line consensus scan finds 3 lines at ≥ 5σ at z = 0.922 while **41.1% of the redshift
  grid does at least as well**; the **star control** throws a spurious peak at **4.16× the scan
  rms**; and **the MRS sub-band stitching offsets reach 11–28% at five of eleven joins — the same
  size as the features being searched for.** What it *does* establish: the contaminant is
  spectroscopically non-stellar over 12 sub-bands (×250 rise from 5 to 25 µm); **M4's 10–15 µm index
  3.8 reproduces exactly at 3.79**; and **M4's 441 K single blackbody is tested for the first time
  and comes out ~10% cooler, 394 K rest-frame**. **The published identification still rests on a
  reduction only the collaboration has done.** **Completeness is measured at last — 75,600
  injections**, real hosts, real per-band uncertainties at the *injected* brightness, the unmodified
  pipeline: **inside the model grid the pre-visual recovery is 50.2% all-sky, 45.8% at |b| > 30°**,
  and **the RMSE fit is not the bottleneck** (it passes 90.3%) — 20.2% are never detected and 31.2%
  fall to the host's own Gaia flags. **Two hard walls are now numbers: γ = 0.01 → 0.00%, 0.02 →
  0.01%, 0.05 → 2.5%, 0.10 → 43.9%** (below γ ≈ 0.05 the screen is *blind*, not inefficient), and
  **T_ds = 1000 K → 0.17% against ~31% inside the [100, 700] K grid — the grid's temperature range
  is a second hard boundary nobody had costed**. **A control the screen had never been given: 8,400
  bare photospheres give an RMSE-gate false-positive rate of 0.00%.** Recovery is **not monotonic**
  in γ — it falls from 44.4% to 39.7% because Eq. 3's obscuration makes a covered star fainter.
  **Catalogue versioned, not clobbered**: `..._v2.csv`, **same 223 rows, 13 new columns**, its own
  [README_v2](catalog/README_v2.md), completeness measured where the injection reaches and still
  **UNMEASURED** where it cannot; **v1, its stats and its README are untouched** (v1's README carries
  only an append-only dated pointer). **Candidate E READY and nothing pre-empted**: M5 §5.3's
  four-case outcome map is **byte-identical to the last committed M5 (SHA-256 verified)**, the
  parameterised chain still reproduces M4 §5 on **all seven checks**, and E is **0 PUBLIC of 39,
  release 2026-09-09**, unchanged. **Route finding paid for in a corrupted cache: IRSA's IBE returns
  HTTP 503 in ~0.1 s under concurrency and the sustained cap is ~12 requests/s per client, which
  splitting across processes does not raise** — a fetcher that reads 503 as "no image" silently
  marks good objects invalid, and it did, for 927 of them; the back-off and the cache repair are now
  in the code. Nothing submitted, posted or sent; no account created anywhere; the Ren+24 note and
  the I dossier remain Matthew-gated, unchanged. **M6 adds no Matthew-gated item.**

- **2026-08-23** — **M5 ✓** ([M5-nebular-stage-highlat-catalog.md](M5-nebular-stage-highlat-catalog.md)) —
  **the last irreproducible stage now has a reproducible replacement, and it closes 81.6% of the
  gap.** M4 localised the whole 4.2× overproduction to the paper's unpublished nebular CNN; M5
  builds a stage out of public data and measures what it does. **Pre-visual survivors 1,545 → 585
  against the paper's 368: 4.20× → 1.59×** (1.72× on the conservative area-corrected reading), and
  by latitude **20.89× → 2.62× at |b| < 5°** while **|b| > 50° is untouched at 1.05×** — the stage
  does nothing where M4 proved nothing needed doing, which is the strongest single check on it.
  Three components, every threshold fixed by a stated rule before any count was looked at:
  **N1**, a veto on the **published angular extent** of **29,462 nebulae from 14 VizieR catalogues**
  (no free parameter — the radius is the catalogue's own); **N2**, the percentile rank of AllWISE's
  own coadd background (`w3sky`/`w4sky`, measured by their pipeline, delivered as a catalogue
  column) against the **|b| > 50° parent binned by ecliptic latitude**, cut at 0.99; **N3**, the
  local source density, **reported and not cut** exactly as pre-registered. **Validation passes on
  all three criteria: 7/7 published candidates preserved** (10/10 labelled, N1 flags none, N2 flags
  none), the rejected fraction **falls monotonically** with |b| (87.5, 61.3, 59.7, 37.0, 3.0, 0.0%)
  and overproduction moves toward 1.0 in **every** band, and the 0.95/0.99/0.999 sensitivity band
  gives 557/585/609 — **±0.05 on the threshold moves the answer ±5%**. **N1 is not just a sky mask
  and the enrichment statistic proves it**: it flags 56.4% of 10–20° survivors while masking 9.5% of
  that sky (**enrichment 5.93**), and the whole veto masks 7.77% of the sky but **0.03% of the
  |b| > 50° core**. **N2 is measuring the plane and not the zodiacal light, shown not asserted**: in
  *every* ecliptic bin the |b| < 5° background sits 2.5–21% above the clean-sky median of the same
  bin while |b| > 50° sits on it, and **60.6% of |b| < 5° survivors are in the top 1% of clean sky
  against a measured 1.29% false-positive rate**. **Stated in advance and true: it does not close
  the plane** — ours rejects **31.2%** at the RMSE gate where their CNN rejects **49.0%**, and that
  **17.8-point difference is the publishable statement** about what the unpublished stage was doing:
  roughly 1.6× more than every catalogued nebula on the sky plus a 1%-FPR background cut. **The
  vetting of the 1,545 is finished — 719 CONTAMINATION-CONSISTENT, 584 INDETERMINATE, 242
  SUB-THRESHOLD, 0 STILL-CLEAN** (M4's own status line was wrong: the run completed 31 minutes after
  M4's document was written). **The zero is by construction, not measurement** — V5 is retired, so
  the surviving set is *objects with no detectable contamination evidence given a method with a
  known blind spot*, never "clean". **A route finding worth more than the milestone: IRSA's Gator
  multi-position upload is anonymous and does the same cross-match at 0.0027 s/position against
  TAP's 3.5 s — ~1,300×.** The V1+V2 pass M4 costed at 3 hours takes **8.1 s**; the 9,486-position
  background pull that would have been 9 hours takes **23 s**. It counted only after PR-1's
  acceptance test: **1,545/1,545 designations identical on both releases, 0 disagreements**,
  photometry to float32 rounding. M4 §7.1's checkpointing hazard is **fixed anyway** (per-chunk
  cache with resume). **The positive deliverable is delivered**:
  [`catalog/`](catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv) — **223 extreme mid-IR-excess
  stars within 300 pc at |b| > 30°, 62 columns**, with the **90-object |b| > 50° calibrated core
  flagged per row**, per-object vetting flags, its own [README](catalog/README.md), and
  completeness/contamination as measured numbers (γ ≥ 0.10 floor misses most weaker excesses; S/N
  cut removes 92.8%; injection-recovery **UNMEASURED** and marked so; 38.1% convicted by our own
  gates, and the rejects are **kept in the table with their evidence**). **V4's chance-alignment
  prior is measured locally for the first time and a global constant cannot carry it**: Suazo's own
  colour band runs **1,830 deg⁻² at |b| < 5° to 255 at |b| > 50°** against V4's single 4.57 —
  6.7 expected interlopers among 1,545 versus 0.018, a factor **372** — and even that upper bound is
  far short of 585, so **the interlopers that matter are the ones AllWISE never resolves**, exactly
  candidate D's 1.23″ companion. **V5 formally retired** (M5 §6, append-only, annotated onto M3 and
  into the vetting code) with M4 §5 as the reason and `sep_thr(ρ) = F(1+1/ρ)` as the replacement;
  the falsifier that would un-retire it is written down. **Candidate E is ready**: the D chain is
  parameterised and reproduces M4 §5 on **all seven checks** (sep 1.233″ vs 1.230″, PA 33.00°,
  ρ = 0.236/7.242/83.135, pull 1.179″), E's MAST status re-checked today (**39 obs, 0 public, all
  EXCLUSIVE_ACCESS, release 2026-09-09**, imaging in the **same three filters on
  `jw07199-o006_t008`**), three commands, and a **four-case outcome map written before the data
  open**. Nothing submitted, posted or sent; no account created anywhere; the Ren+24 note and the
  I dossier remain Matthew-gated, unchanged. **M5 adds no Matthew-gated item — no object reached
  STILL-CLEAN and none can.**

- **2026-08-21** — **M4 ✓** ([M4-sky-parent-gvar-jwst.md](M4-sky-parent-gvar-jwst.md)) — **the sky
  is finished: 41,253 deg², 100.00%, 220 cells, 0 abandoned**, harvested anonymously through the
  **AIP mirror** with no account while ESAC's join tables stayed dead all day (a 3-table `COUNT(*)`
  still died at 61 s). **The route needed four corrections and three would have corrupted the
  harvest silently**: the 30 s cap is a Postgres *statement* timeout, not the UWS
  `executionDuration` M3 named (it accepts 86400 s and ignores it), and what beats it is a
  **`source_id` range** — a HEALPix cell, exact sky area by construction — not a sky box
  (215 deg² box = 27 s of DB time before a single join; 298 deg² source_id range = 18.7 s for the
  whole 5-table join); **AIP stores AllWISE's null uncertainty as a sentinel 0.0**, so ESAC's
  `IS NOT NULL` detection cut silently passes everything and inflated the parent **32×**; **the
  2MASS join key is the designation, not the oid** — on the oid, **0 of 41,844** designations
  matched ESAC and J was wrong by a median **+5.55 mag** while Gaia and AllWISE matched exactly;
  and AIP renames `source_id` to `datalinkID` in every VOTable. **Then the acceptance test passed
  exactly: all 220,632 ESAC rows recovered, Jaccard 1.00000, 0 unmatched either way, photometry to
  max |diff| = 0.00000.** It also caught a **file-index collision** in our own ESAC distance cache
  that had destroyed 2,000 lookups. **The proxy's purity is measured at last — 98.46%** (recall
  98.99%) on 507,382 rows containing the complement — **and it is not needed**: ESAC's single-table
  PK lookups work while its joins do not, so **all 439,923 parent rows carry an exact
  Bailer-Jones distance and none falls back to the proxy**. **The 1.43× parent discrepancy is
  settled and it was a stage-alignment error** — Suazo §2.1 says Table 4's "W3/W4 detection
  ∼3.2×10⁵" row is *after* the contamination flag, so the like-for-like parent is
  **328,937 vs 320,000 = 1.03×**; the paper's independent "∼200,000" cross-check lands at 1.011×.
  **An absolute sky-wide yield may now be quoted.** **The Gvar reference gap is closed and was never
  the largest factor**: M3's "the paper rejects 54%" was the **CNN** (Table 4 puts the nebular
  classifier *between* the RMSE gate and the extra cuts, which reject **10.4%** against our
  **11.15%**), our Gvar rejects **more** than the paper's, the reference offset is **reconstructed
  from the paper's own published Gvar values (ours/paper = 1.2097, n=7)**, and a **reference-free
  monotonicity bound caps the whole question at 12 survivors of 1,557 — 0.77%**. **What the 4.2×
  actually is: the nebular CNN, localised by Galactic latitude.** Every reproducible stage
  reproduces (parent 1.03×, RMSE 0.84×, extras 0.84×) and the pre-visual yield per deg² runs from
  **20.9× the paper's mean at |b|<5°** to **1.05× [0.94–1.17] at |b|>50°**, where the conditional
  S/N pass rate is 6.9% against their 7.2% (0.96 ± 0.10×) — and **all 7 of the paper's 7 published
  candidates lie at |b|>30°** (p=0.008 isotropic). **M3's own explanation for that gap is refuted**:
  **zero** of the 8,428 extra-cut survivors lie blueward of M_G = 6. Full-sky funnel at γ ≥ 0.10:
  **439,923 W3W4-detected → 328,937 parent → 9,486 RMSE → 8,428 → 1,545 pre-visual survivors.**
  **Candidate D's JWST data analysed — the first archival verdict graded against the imaging that
  settled it.** From the public GO 7199 MIRI mosaics (a *newer re-reduction* than the paper's):
  **separation 1.23 ± 0.07″ at PA 33 ± 1°** (Hephaistos IV says only "≈1 arcsec" and no PA),
  contrast **0.236 / 7.24 / 83.1** at 5.6/10/15 μm, contaminant point-like and
  F<sub>ν</sub> ∝ λ<sup>+4.4</sup>, supplying **88% of the 10 μm and 98.8% of the 15 μm flux**; the
  star is photospheric. **Contamination CONFIRMED; z ≈ 0.9 NOT independently confirmed** (it rests
  on the MRS spectrum, unreduced — UNSOURCED here). **The calibration**: the pull is
  `sep·ρ/(1+ρ)`, so the geometric ceiling is the separation, **1.23″** — and **our archival W4
  offset (2.55 ± 0.50″) and Ren+26's (1.8″) both exceed it**, while our W3 offset points at
  **PA 82.9°, 50° away from the real contaminant**, where MIRI shows nothing. **The archival
  centroid is unreliable in direction as well as magnitude near the floor**, which retires M3's
  plan to retune it. **The floor now has a number**: `sep_thr(ρ) = F(1+1/ρ)`, asymptoting to F
  itself, so **≈10% (1″ floor) to ≈40% (2″ floor) of chance-aligned contaminants are invisible at
  any brightness**. Free by-product: **M3's extrapolation from 48% was good to a few percent, not
  to Poisson** (+2.0% on the parent, +13.5% on pre-visual survivors, against quoted ±0.2%).
  **Vetting of the 1,545 survivors was still running at session end** (IRSA costs ~3.5 s/position;
  V5 stays disabled and §5 is now the reason) — resume with
  `python scripts/m3_vet_survivors.py --tag m4_g0.1 --skip-centroid`. **No object can reach
  STILL-CLEAN while the centroid axis is invalid, so there is no Matthew-gated candidate.** Nothing
  submitted, posted or sent; no account created anywhere; the Ren+24 note and the I dossier remain
  Matthew-gated, unchanged.

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
