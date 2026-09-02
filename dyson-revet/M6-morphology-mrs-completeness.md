# M6 — a morphology stage on the coadds, candidate D's MRS spectrum, and the catalogue's completeness measured

*2026-08-24 · follows [M5](M5-nebular-stage-highlat-catalog.md), executing M5 §7's own
recommendations. Every externally-sourced number carries its source; anything unsourced is marked
UNSOURCED. **Nothing in this milestone has been submitted, posted, or sent anywhere.** The
candidate-I dossier and the Ren+24 note remain Matthew-gated and are unchanged by this document.*

---

## 0. Pre-registrations

*Written and timestamped **before** the runs they govern, per repo law. Nothing in §1–§5 was chosen
after seeing a result. Where a threshold exists, the **rule** that sets it is written here and the
number it produces is computed once.*

### PR-1 — N4, the morphology stage: what the statistic is, and how its threshold is chosen

M5 §3.6 measured the residual exactly: **our reproducible nebular stage rejects 31.2% at the RMSE
gate where the paper's unpublished CNN rejects 49.0%**, and named the missing ingredient —
**image structure**. N1 can only remove what somebody has catalogued; N2 measures the background
*level* and is blind to its *shape*. A classifier looking at W3/W4 morphology is not restricted
either way. M5 §1.1's Gator route made per-object image work affordable for the first time.

**N4 is a fourth component of the nebular stage, built on the AllWISE Atlas coadds themselves.**

- **The images.** IRSA IBE `wise/allwise/p3am_cdd` — the AllWISE Atlas coadd intensity image
  (`-int-3.fits`) and its matching uncertainty image (`-unc-3.fits`), in **W3 and W4**, 1.375″/pix,
  cut out **100″ on a side** centred on the source. The tile is the source's own `coadd_id` from
  the AllWISE catalogue, so no image search is needed. These are the same coadds AllWISE's own
  pipeline measured `w3sky`/`w4sky` from, i.e. N2 and N4 read the same data through different
  statistics.

- **The primary statistic — S, the normalised background structure index. Declared primary here,
  before any of the alternatives below has been computed on any survivor.** In an annulus
  **12″ < r < 45″** about the source (12″ is one W4 PSF FWHM, so the source itself and its wings
  are outside the measurement; 45″ is the largest radius a 100″ cutout supports at every position),
  after **3σ iterative clipping** to remove neighbouring point sources:

  > Smooth both the intensity and the variance image with a Gaussian kernel matched to the band's
  > coadd PSF, so uncorrelated pixel noise averages down and real structure does not. Let σ_obs be
  > the robust dispersion (1.4826 × MAD) of the smoothed intensity in the annulus, and σ_exp the
  > dispersion the uncertainty image predicts for the same smoothing. Then
  >
  > **S = σ_obs / σ_exp.**
  >
  > S is dimensionless, needs no training set, and has a **parameter-free null**: on sky whose only
  > structure is noise, S → 1. Values above 1 are spatial structure the pipeline's own noise model
  > does not account for. A raised but *flat* background — the thing N2 already measures — leaves S
  > at 1; a filament, an edge, or a gradient across the beam does not.

- **The threshold rule — M5 PR-2's N2 rule verbatim, applied to S instead of to `w?sky`. No new
  free parameter is introduced.**

  > The calibration population is the **parent sample at |b| > 50°** — the band M4 §4.3 measured
  > this screen to reproduce the paper's yield at 1.05×. Within bins of **|ecliptic latitude|,
  > 10° wide** (coadd depth, and therefore σ_exp, varies with ecliptic latitude through frame
  > coverage), each object is assigned the **percentile rank** of its W3 S and its W4 S in that
  > calibration distribution. Its morphology score is the **larger** of the two ranks. **An object
  > is flagged if its score exceeds 0.99.** The **combined** false-positive rate of the max-of-two
  > rule is *measured* on the calibration set and reported, never assumed.

  Because the |b| > 50° parent is 68,209 stars and each object costs four image cutouts, the
  calibration is run on a **seeded random subsample** (`numpy.random.default_rng(20260824)`),
  **stratified by ecliptic bin at min(4,000, n_bin) per bin**, so that every bin — including the
  thinnest — carries ≥ 2,000 objects and therefore ≥ 20 in the 1% tail it has to locate. The
  sampling rule and the seed are fixed here, before any threshold is computed.

  Scores at **0.95 and 0.999 are computed as a sensitivity band and labelled as such**; the
  delivered funnel is the 0.99 one, exactly as in M5.

- **Reported, and explicitly NOT cut on** (M5's N3 precedent — no published threshold exists to
  anchor one, and inventing one here is the choice this section exists to prevent):
  **A**, the azimuthal asymmetry of the same annulus (dispersion of the 12 azimuthal sector medians,
  over their mean); **G**, the local gradient across the beam (the fitted plane's slope over the
  annulus, in σ_exp per beam); **C**, the source's own concentration against the coadd PSF
  (r < 1 FWHM flux over r < 2 FWHM flux, differenced against the calibration median). These three
  are delivered per object in the artifacts and discussed, and **no verdict and no funnel number
  depends on them.**

- **Cutout validity, declared before the run because this project has been bitten by it.** M3 §3.1
  found that IBE cutouts *silently clip at coadd-tile edges*, manufacturing fake measurements. A
  cutout counts only if it returns the **full requested size** and is **< 2% non-finite** inside
  the measurement annulus. Anything else is `morph_ok = False`, is excluded from **both** the
  calibration and the flagging, and is **counted and reported** whatever the count is. An object
  with no valid cutout is **not flagged** — the stage may only remove objects it has actually
  measured.

**Validation — identical to M5 PR-2's, all three parts fixed in advance:**

  a. **7/7.** N4 must not flag any of the paper's seven published candidates. As in M5 this test is
     **declared weak in advance** (all ten labelled objects lie at |b| > 28.8°); failing it is
     disqualifying, passing it is necessary and nowhere near sufficient.
  b. **The latitude signature.** The fraction N4 flags must **fall with |b|**, and must be
     **at or near the 1% false-positive rate at |b| > 50°**, where M4 proved nothing needs doing.
     A stage that removes a latitude-flat fraction is removing something else and will be reported
     as such. This is the strongest single check and it is the one M5 §3.4 passed.
  c. **No count-peeking.** The threshold comes from the rule above. The funnel is computed once
     with it, at the same position in Table 4's order as N1 ∨ N2.

**Stated in advance, because the arithmetic already bounds it:** the gap to close is 17.8 points at
the RMSE gate. N4 is measured on the **same** 9,486 RMSE survivors, and it overlaps N1 and N2 by
construction — a source inside a catalogued nebula usually also sits on structured sky. **The
deliverable is the union N1 ∨ N2 ∨ N4 and the residual after it, not a claim to have closed the
gap.** If the residual is still large, that is the result, and the named remainder is the
publishable statement.

### PR-2 — candidate D's MRS cubes: what would settle z ≈ 0.922, and what would not

M4 §5.2 confirmed D's contamination from imaging and marked the redshift **UNSOURCED**: it "rests
entirely on the MRS emission lines, which were not reduced here". The cubes are public. Fixed
before the extraction is looked at:

- **What "reduce" means, stated so the claim can be graded.** The products are STScI's public
  **Level-3 `_s3d.fits` calibrated cubes**; this project does not re-run `calwebb_spec3` from the
  uncalibrated ramps, which would need a multi-GB CRDS cache and would reproduce STScI's own
  product. **The `CAL_VER` and `CRDS_CTX` actually used are read from the headers and reported**,
  exactly as M4 §5.1 did for the imaging. What is new, and what nobody has published, is the
  **spatially resolved extraction**: the pipeline's own `x1d` is one aperture on the target and
  therefore **blends the star with the contaminant 1.23″ away**. This is the first separation of
  the two.

- **The extraction is M4 §5's deblend, per wavelength slice.** Two fixed-position Gaussians plus a
  constant, solved linearly; positions from the Gaia position propagated to each cube's own
  `EXPSTART` and that position plus M4 §5's **measured** (1.233″, PA 32.998°) — **not refitted
  here**; one plate offset per cube solved from the white-light image so a pointing error cannot be
  read as a flux ratio.

- **The acceptance test, before any redshift is quoted.** The extraction is accepted only if the
  MRS spectra, integrated over the MIRI imaging bandpasses, reproduce M4 §5.1's **independently
  measured** F560W / F1000W / F1500W fluxes for **both** components. The tolerance is fixed here at
  **±30%** per band per component, which is the aperture systematic M4 §5.4 already measured on the
  imaging (~0.2 mag ≈ 20%) plus room for the Gaussian-PSF approximation. **If it fails, no redshift
  is quoted from these data and the failure is the result.**

- **What counts as confirming z ≈ 0.922.** A redshift is claimed only from **≥ 2 independent
  spectral features** identified with the **same** z to within **±0.01**, each detected at
  **≥ 5σ** against the local continuum. Anything less is reported as **consistent-with** or
  **not-tested**, in the same posture M4 §5.2 took. **A single feature is not a redshift.**
  The line list is fixed here, before the search: the mid-IR features a dusty AGN / Hot DOG at
  z ≈ 0.9 must show — PAH 6.2, 7.7, 8.6, 11.3, 12.7 µm; silicate absorption 9.7 µm;
  [Ar II] 6.985, [Ar III] 8.991, [S IV] 10.511, [Ne II] 12.814, [Ne III] 15.555, [S III] 18.713,
  [O IV] 25.890 µm; H₂ S(1) 17.035, S(2) 12.279, S(3) 9.665 µm.
- **The blind search is run first and reported first.** A redshift grid over **0 < z < 3** is
  scored by cross-correlation against that fixed line list before the z = 0.922 hypothesis is
  evaluated, so the answer is not read off a prior. **Whatever the grid's best z is, it is
  reported** — including if it is 0.922, and including if it is nothing at all.

### PR-3 — injection–recovery: the completeness function, and what may be claimed from it

`catalog/catalog_stats.json` marks completeness **UNMEASURED**. Fixed before the run:

- **What is injected.** Synthetic star + blackbody SEDs built by the **selection code's own
  forward model** (`w1_selection.py`'s template locus and dust-shell grid), over a factorial
  parameter space declared here: **covering fraction γ ∈ {0.01, 0.02, 0.05, 0.10, 0.15, 0.20,
  0.30, 0.50}** × **dust temperature T_ds ∈ {100, 150, 200, 300, 450, 700, 1000 K}** ×
  **host W3 magnitude in 1-mag bins over the parent's own range** × **|b| band** (the six M4 §4.3
  bands). The host photometry, its per-band uncertainties, and its sky background are taken from
  **real parent rows**, not simulated, so the recovery fraction is measured against the real error
  distribution and the real latitude-dependent background.
- **What "recovered" means.** The injected row is pushed through the **unmodified** pipeline — the
  same RMSE fit, the same γ ≥ 0.10 grid, the same extra cuts, the same S/N ≥ 3.5 gate — and is
  recovered if it survives to the pre-visual stage. **No stage is re-tuned for the injection.**
- **What may be claimed.** The deliverable is the recovery fraction as a function of (γ, T_ds,
  magnitude, |b|), and the catalogue's completeness statement is updated **only where the
  injection actually measures it**. The nebular stage's own effect on completeness is measured
  separately, because it is a *sky* cut and not a *photometry* cut. **Anything the injection does
  not reach stays UNMEASURED and stays marked so.**
- **Versioning.** The catalogue is re-issued as **v2** alongside an unmodified **v1**; v1 is not
  edited, not moved, and not deleted. If v2's selection differs from v1's by so much as one row,
  the difference is enumerated in the v2 README.

### PR-4 — candidate E: a readiness re-check, and nothing else

E's data open **2026-09-09**, sixteen days after this milestone. **Nothing about E is pre-empted.**
The only actions permitted here are: (i) re-run M5 §5.2's parameterised chain against D and confirm
all seven checks still pass; (ii) re-check E's MAST status; (iii) verify M5 §5.3's four-case
outcome map is on disk and **byte-identical** to what M5 committed. Any edit to that map would
destroy its point, so the check is a hash, and the hash is recorded. **If E's data have become
public early, they are not analysed in this milestone** — the map says the analysis happens on or
after the release date, and moving it forward is exactly the kind of after-the-fact choice the map
exists to prevent.

### PR-5 — what this milestone may not do

Unchanged and restated: no account is created anywhere; nothing is submitted, posted, or sent; the
Ren+24 note and the candidate-I dossier stay Matthew-gated and untouched; **V5 stays retired**
(M5 §6) and nothing here re-enables, re-tunes or re-scores it; **STILL-CLEAN stays unreachable**
and no object in any product is described as clean.

---

*(Everything below is written after the runs. Numbers are emitted by the scripts named, never
hand-copied.)*

---

## 0b. What M6 established

1. **A training-free morphology stage exists, and it closes 5.1 of the 17.8
   points — not all of them.** N4 reads the AllWISE W3/W4 coadds directly and
   rejects **24.8%** at the RMSE gate on its own; the union N1 ∨ N2 ∨ N4 rejects
   **36.3%** where the paper's unpublished CNN rejects **49.0%**. **The
   remainder is 12.7 points and it is named, not hand-waved** (§1.7).
2. **At the stage that decides the yield, the same union closes 96.3% of the
   excess.** Pre-visual survivors **1,545 → 585 (M5) → 411 (M6)** against the
   paper's **368**; all-sky overproduction **4.20× → 1.59× → 1.117×** (1.211×
   area-corrected). **Both numbers are reported and neither is chosen** — they
   answer different questions and they disagree because the paper's CNN and our
   stage reject different objects that survive the later cuts differently (§1.5,
   §1.7).
3. **The statistic is one line and has a parameter-free null.**
   **S = σ_obs/σ_exp** in a 12″–45″ annulus: the robust dispersion of the
   PSF-smoothed coadd divided by what the coadd's own uncertainty image predicts
   under the same smoothing. On noise-only sky S → 1; **measured on 27,876
   |b| > 50° parent stars it is 1.396 (W3) and 1.245 (W4)** (§1.2). Its
   threshold is **M5 PR-2's N2 rule verbatim** — percentile rank in ecliptic
   bins of the |b| > 50° parent, max over the bands, 0.99 — so **no new free
   parameter is introduced anywhere**.
4. **All three of PR-1's validation criteria pass.** **(a) 7/7** — N4 flags
   **none** of the ten labelled objects. **(b)** The flagged fraction falls
   **monotonically** with |b| — **70.3, 36.3, 24.9, 6.0, 2.3, 1.1%** — and at
   |b| > 50° the rate is **1.14% against a measured false-positive rate of
   1.20%**: **the stage does nothing at high latitude, where M4 proved nothing
   needs doing.** **(c)** The 0.95/0.99/0.999 band gives **262/411/533**, which
   is **wider than N2's** and is reported as a weakness rather than buried
   (§1.4).
5. **The median structure index runs 12.50 at |b| < 5° to 1.41 at |b| > 50°** —
   a factor of nine on a statistic whose noise-only value is 1 — and after the
   union **every latitude band sits within ±50% of the published rate**, against
   20.89× before any nebular stage (§1.5).
6. **N4's failure mode was found before it could matter, and bounded.** On clean
   sky S flags **70.1%** of sources brighter than W3 = 5, because a bright PSF's
   wings fill the annulus. **Zero of the 9,482 RMSE survivors and zero of the
   1,545 pre-visual survivors are that bright**; the sample's median is W3 =
   12.4, where the clean-sky rate is 0.38%. Compared against a **magnitude-
   matched** expectation the enrichment is **289× at |b| < 5° and 88× all sky**
   (§1.3).
7. **N4 sees something N1 and N2 cannot: 486 objects — 5.1% of the RMSE
   survivors — that no catalogue lists and whose background is not in the top
   1%.** M5 §3.6 predicted that category exactly and could not measure it (§1.6).
8. **Candidate D's MRS cubes are reduced — 12 public Level-3 cubes,
   4.90–28.70 µm, 11,625 slices deblended — and the first independent extraction
   of the contaminant's spectrum exists.** The cubes carry `CAL_VER 2.0.1 /
   CRDS jwst_1535`, the same newer re-reduction M4 §5.1 found for the imaging
   (§2.1).
9. **PR-2's acceptance test FAILS, 4 of 6, and the structure of the failure is
   the finding: in every band the *dominant* member of the pair passes and only
   the *sub-dominant* one fails.** That is PSF-wing leakage across 1.23″, and it
   is a quantitative limit on what a parametric deblend of a close pair can do —
   directly relevant to candidate E (§2.2, §4).
10. **PR-2's consequence is honoured: no redshift is quoted from these data.**
    **The reduction cannot settle z ≈ 0.922, and the reason is measured rather
    than asserted**: the blind cross-correlation's best z moves from **0.47 to
    1.06** when the continuum window changes by ±0.02 dex; a blind narrow-line
    consensus scan finds **3 lines at ≥ 5σ at z = 0.922 while 41.1% of the
    redshift grid does at least as well**; the star control produces a spurious
    peak at **4.16× the scan rms**; and the **MRS sub-band stitching offsets
    reach 11–28% at five of eleven joins, the same size as the features being
    searched for** (§2.3–§2.5).
11. **What the reduction does establish**: the contaminant is spectroscopically
    non-stellar over 12 sub-bands (a factor ≈ 250 rise from 5 to 25 µm);
    **M4 §5.2's 10–15 µm index of 3.8 reproduces exactly at 3.79**; and
    **M4's 441 K single blackbody is tested for the first time and comes out
    ~10% cooler, 394 K rest-frame** (§2.6). **The published identification still
    rests on a reduction only the collaboration has done.**
12. **The catalogue's completeness is measured. 75,600 injections**, real hosts,
    real per-band uncertainties at the injected brightness, the unmodified
    pipeline. **Inside the model grid the pre-visual recovery is 50.2% all-sky
    and 45.8% at |b| > 30°**, and **the RMSE fit is not the bottleneck** — it
    passes 90.3%; the losses are 20.2% never detected and 31.2% removed by the
    host's own Gaia quality flags (§3.3).
13. **Two hard walls are now numbers rather than adjectives.** **γ = 0.01 →
    0.00% recovered, γ = 0.02 → 0.01%, γ = 0.05 → 2.5%, γ = 0.10 → 43.9%**: the
    grid floor is a cliff, and below γ ≈ 0.05 the screen is *blind*, not
    inefficient. And **T_ds = 1000 K → 0.17%**, against ~31% everywhere inside
    the [100, 700] K grid — **the grid's temperature range is a second hard
    boundary and nobody had costed it** (§3.2).
14. **A control the screen had never been given: 8,400 bare photospheres through
    the unmodified pipeline give an RMSE-gate false-positive rate of 0.00%.**
    Nothing in this project's survivor list is a photosphere scattered over the
    line by noise (§3.1).
15. **Recovery is not monotonic in the thing being selected for**: it *falls*
    from 44.4% at γ = 0.15 to 39.7% at γ = 0.50, because Suazo Eq. 3's
    obscuration makes a heavily-covered star fainter and the undetected fraction
    climbs 5.7% → 15.9% (§3.2).
16. **The catalogue is versioned, not clobbered**: `…_v2.csv` — **same 223 rows,
    13 new columns**, N4's statistics and flag per row, completeness measured
    where the injection reaches and still marked UNMEASURED where it does not.
    **v1, its stats file and its README are untouched** (§3.4, `catalog/`).
17. **Candidate E is READY and nothing about it was pre-empted.** M5 §5.3's
    four-case outcome map is **byte-identical to the last committed M5**
    (SHA-256 verified); the parameterised chain still reproduces M4 §5 on **all
    seven checks**; E is **0 PUBLIC of 39, release 2026-09-09**, unchanged
    (§4).
18. **A route finding, paid for in a corrupted cache: IRSA's IBE returns
    HTTP 503 in ~0.1 s under concurrency and the sustained cap is ~12
    requests/s per client, which splitting across processes does not raise.**
    A fetcher that reads 503 as "no image" silently marks good objects invalid —
    it did, for 927 of them — and both the back-off and the cache-repair are now
    in the code (§1.1).

---

## 1. N4 — a training-free structure statistic on the coadds, and how much of the 17.8 points it closes

*`scripts/m6_morph.py` (`coadd`, `stats`, `calibrate`, `apply`, `funnel`);
artifacts `out/m6_morph_{rmse,candidates}.csv`, `data/morph/m6_morph_calib.csv`,
`out/m6_morph_flags_{rmse,candidates}.csv`, `out/m6_morph_thresholds.csv`,
`out/m6_morph_calibration.json`, `out/m6_morph_enrichment.json`,
`out/m6_funnel_morph.json`, `out/m6_rmse_survivors_morph_m4_g0.1.csv`,
`out/m6_fig_morph.png`. Every image was pulled anonymously from IRSA's IBE —
no account, nothing sent.*

### 1.1 What was measured, and what it cost

**About 150,000 AllWISE Atlas coadd cutouts**, W3 and W4 intensity and uncertainty,
100″ on a side, for **9,486 RMSE survivors**, a **27,876-object |b| > 50°
calibration sample** and the **10 labelled candidates A–J**. The coadd tile
comes from each source's own `coadd_id`, pulled in bulk through M5 §1.1's Gator
route (28,000 positions in 53 s), so no image search was ever issued.

**Validity is high and the failures are counted, not hidden**: **9,482 of
9,486** RMSE survivors (**100.0%** to one decimal) and **27,876 of 28,000**
calibration objects (**99.56%**) returned a cutout that passed PR-1's validity
test — full requested size, < 2% non-finite inside the annulus. The 128 that
did not are `morph_ok = False`, are excluded from both the calibration and the
flagging, and **are not flagged by a stage that never measured them**.

**A route finding, paid for the hard way.** IBE answers **HTTP 503 in ~0.1 s**
when a client exceeds its concurrency limit — the same instant-failure
signature M3 §1.1 diagnosed on ESAC. A first pass at 32 threads triggered it,
and because the fetcher treated a 503 like a missing image it **wrote 927 good
objects into the cache as permanently invalid**. Both halves are fixed: 5xx/429
now back off exponentially and then *raise*, and the resume logic **drops any
cached row whose cutout never arrived** rather than trusting it. The sustained
ceiling is measured at **~12 requests/s per client**, and splitting the work
across two processes does not raise it — 1.5 + 1.6 obj/s against 3.1 obj/s for
one process, i.e. the cap is per client, not per connection. *This is the
opposite of M5 §1.1's Gator finding and worth recording next to it: the
catalogue service is 1,300× cheaper than TAP, and the image service is hard
capped.*

### 1.2 The statistic, and what its null is

PR-1's **S = σ_obs / σ_exp**, measured in the 12″–45″ annulus on the
PSF-smoothed image after 3σ clipping, with σ_exp propagated from the coadd's own
uncertainty image through the identical smoothing.

**On nebulosity-free sky the null is measured, not assumed**: on the
27,876-object |b| > 50° calibration set the median is **S(W3) = 1.396,
S(W4) = 1.245**. Both sit slightly above the parameter-free null of 1 because
AllWISE coadd noise is spatially correlated by the resampling and the per-pixel
uncertainty image does not carry that correlation. **The percentile rule absorbs
it**, which is why the rule is a percentile and not a value.

**The two bands are nearly independent, which N2's were not.** Spearman
ρ(S_W3, S_W4) = **0.300**, against **0.9991** for M5's `w3sky`/`w4sky`. The
max-of-two rule is therefore doing real work here, and its **measured** combined
false-positive rate at the 0.99 threshold is **1.20%** (7.18% at 0.95, 0.13% at
0.999) — reported, never derived from an independence assumption.

### 1.3 The failure mode of S, found and bounded before it could matter

S has one clear failure mode, and the calibration set exposes it. **On
nebulosity-free sky the flag rate is strongly magnitude-dependent at the bright
end**, because a very bright source's PSF wings fill the annulus and no clip
removes a smooth wing:

| W3 mag | 4–5 | 5–6 | 6–7 | 7–8 | 8–9 | 9–10 | 10–11 | 11–12 | 12–13 |
|---|---|---|---|---|---|---|---|---|---|
| flagged on \|b\| > 50° sky | **70.1%** | 7.1% | 0.65% | 0.11% | 0.00% | 0.04% | 0.13% | 0.34% | 0.38% |
| median S(W3) | 8.80 | 4.26 | 2.12 | 1.52 | 1.37 | 1.35 | 1.36 | 1.32 | 1.29 |

**S is not usable for sources brighter than W3 ≈ 6, and this is stated as a
limitation.** It does not touch this screen: **zero of the 9,482 RMSE survivors
and zero of the 1,545 pre-visual survivors are brighter than W3 = 6**, and the
sample's median is **W3 = 12.4**, where the clean-sky flag rate is **0.38%** —
below the nominal 1%.

**So the flag rate is compared with a magnitude-matched expectation rather than
with a flat 1%**, which is the only fair comparison and is the N4 analogue of
M5 §3.2's enrichment statistic:

| \|b\| | n | N4 flags | expected, magnitude-matched | **enrichment** |
|---|---|---|---|---|
| 0–5° | 1,942 | 1,366 | 4.7 | **289×** |
| 5–10° | 1,037 | 376 | 3.1 | **121×** |
| 10–20° | 1,930 | 481 | 5.7 | **84×** |
| 20–30° | 1,227 | 74 | 3.7 | **19.9×** |
| 30–50° | 1,940 | 44 | 5.6 | **7.9×** |
| 50–90° | 1,406 | 16 | 3.9 | **4.1×** |
| all sky | 9,482 | 2,357 | 26.7 | **88×** |

**N4 is not a brightness statistic in disguise.** Among the |b| > 50° survivors
the correlation between S and the source's own W3 magnitude is **−0.012**
(Spearman) — indistinguishable from zero.

### 1.4 PR-1's validation, all three parts

**(a) 7/7 preserved.** **N4 flags none of the ten labelled objects A–J**, and
therefore none of the paper's seven published candidates. Scores: A 0.855,
B 0.426, C 0.657, D 0.730, E 0.313, F 0.715, G 0.512, H 0.619, I 0.790,
J 0.515 — all far below the 0.99 cut. As in M5 this test is **weak by
construction**, all ten lying at |b| > 28.8°; failing it would have been
disqualifying.

**(b) The latitude signature holds, and this is the strongest single check.**
The flagged fraction falls **monotonically** with |b| — **70.3%, 36.3%, 24.9%,
6.0%, 2.3%, 1.1%** — and at |b| > 50° the rate is **1.14% against a measured
false-positive rate of 1.20%**, i.e. **N4 does at high latitude what a stage
with no signal there should do: nothing distinguishable from its own noise
floor.** *What little it does do is real rather than random — the enrichment
there is 4.1× and the 16 objects move the |b| > 50° overproduction from 1.05×
to 1.02×, toward 1.0 rather than away from it.*

**(c) No count-peeking.** The threshold is PR-1's 0.99, from M5 PR-2's rule
verbatim. The sensitivity band, **labelled sensitivity and not selection**:
0.95 → **262** pre-visual survivors, **0.99 → 411**, 0.999 → **533**. *This band
is wider than M5's N2 band (557/585/609): a ±0.05 move on N4's threshold moves
the answer by −36% / +30%, against N2's ±5%. That is a genuine weakness of a
statistic whose distribution has a long tail, and it is reported rather than
buried — the delivered number is the 0.99 one and no other.*

### 1.5 The funnel with N4 in place

| stage | ours (M5, N1∨N2) | **ours (M6, N1∨N2∨N4)** | Hephaistos II Table 4 | ratio |
|---|---|---|---|---|
| RMSE ≤ 0.2 | 9,486 | **9,486** | 11,243 | 0.84× |
| + nebular stage | 6,529 | **6,043** | 5,732 *(their CNN)* | **1.05×** |
| + extra cuts | 5,943 | **5,541** | 5,137 | 1.08× |
| **+ S/N ≥ 3.5 — pre-visual** | 585 | **411** | **368** | **1.117×** |

**Pre-visual survivors 1,545 → 585 (M5) → 411 (M6) against the paper's 368.
All-sky overproduction 4.20× → 1.59× → 1.117×** (1.211× on the conservative
area-corrected reading, which divides by the sky N1's mask leaves). **Excess
over the paper's 368: 1,177 → 217 → 43. 96.3% of it removed** (93.4%
area-corrected), against M5's 81.6%.

| \|b\| | n RMSE | N4 flags | median max(S) | pre (M5) | **pre (M6)** | x before | x M5 | **x M6** |
|---|---|---|---|---|---|---|---|---|
| 0–5° | 1,942 | 70.3% | **12.50** | 84 | **25** | 20.89× | 2.62× | **0.78×** |
| 5–10° | 1,037 | 36.3% | 4.37 | 84 | **38** | 6.82× | 2.64× | **1.19×** |
| 10–20° | 1,930 | 24.9% | 2.33 | 135 | **92** | 5.41× | 2.18× | **1.48×** |
| 20–30° | 1,227 | 6.0% | 1.58 | 63 | **57** | 1.72× | 1.08× | **0.98×** |
| 30–50° | 1,940 | 2.3% | 1.45 | 129 | **111** | 1.36× | 1.32× | **1.13×** |
| **50–90°** | 1,406 | **1.1%** | **1.41** | 90 | **88** | 1.05× | 1.05× | **1.02×** |

**The median structure index runs 12.50 in the innermost plane to 1.41 at
|b| > 50°** — a factor of nine, on a statistic whose noise-only value is 1 — and
**the overproduction now sits within ±50% of the published rate in every single
latitude band**, against 20.89× before any nebular stage and 2.62× after M5's.
At |b| < 5° it has crossed to **0.78×**: the union now removes slightly *more*
than the paper's pipeline did there, which is stated because it is what the
numbers say.

### 1.6 What N4 adds that N1 and N2 could not see

On the 9,482 survivors with a valid cutout: **N1 ∨ N2 flags 2,956; adding N4
takes it to 3,442. N4's own new rejections are 486 — 5.1% of the RMSE
survivors.** The overlap is large and that is the point: a source inside a
catalogued nebula usually *also* sits on structured sky.

| flagged by | n |
|---|---|
| N1 only | 618 |
| N2 only | 369 |
| **N4 only** | **486** |
| N1 and N4 | 1,424 |
| N2 and N4 | 1,276 |
| any of the three | 3,442 |

**N4-only 486 is the measurement of what "structure nobody catalogued, on sky
whose background level is not in the top 1%" is worth.** M5 §3.6 predicted
exactly this category and could not measure it; it is 5.1% of the RMSE
survivors and it is a third of what N4 rejects in total.

### 1.7 The honest answer on the 17.8 points: partially closed, remainder named

**At the RMSE gate — the place where the 17.8 points was defined:**

| | rejected at the RMSE gate |
|---|---|
| M5's N1 ∨ N2 | 31.2% |
| **N4 alone** | **24.8%** |
| **M6's N1 ∨ N2 ∨ N4** | **36.3%** |
| the paper's CNN | **49.0%** |

**5.1 of the 17.8 points are closed. 12.7 points remain.** That is a **28.7%**
close on the gap as M5 defined it, and it is the number that should be quoted
when the claim is about the classifier.

**At the pre-visual stage — the place where the yield is defined — the same
stage closes 96.3% of the excess** and takes the all-sky overproduction to
**1.117×**. The two numbers are not in conflict: the paper's CNN rejects a
larger *fraction* at the RMSE gate, but what it rejects and what N4 rejects
survive the later cuts differently, and the object counts that reach the
pre-visual stage end up nearly equal.

**Both are reported, and neither is chosen.** The honest sentence is: **a
catalogue veto, a background percentile and a coadd structure index, all with
rule-fixed thresholds and no training set, together reproduce the paper's
pre-visual yield to 1.12× while rejecting 12.7 points less than its unpublished
classifier at the RMSE gate.** What that residual 12.7 points is remains
unmeasured, and the candidates for it are stated rather than guessed:
morphology of the *source* rather than of its field, which S deliberately
excludes by starting its annulus at one W4 FWHM; nebulosity on scales larger
than the 45″ aperture, which a fixed-window statistic cannot see; and whatever a
classifier trained on 960 hand-labelled images learned that no closed-form
statistic encodes.

---

## 2. Candidate D's MRS cubes — the reduction is done, and it cannot settle z ≈ 0.922

*`scripts/m6_mrs_reduce.py` (`fetch`, `extract`), `scripts/m6_mrs_redshift.py`;
artifacts `out/m6_mrs_D_spectra.csv` (11,625 slices), `out/m6_mrs_D_cubes.csv`,
`out/m6_mrs_D_{contaminant,star}_spectrum.csv`, `out/m6_mrs_D_redshift.json`,
`out/m6_mrs_D_zscan.csv`, `out/m6_mrs_D_narrow_consensus.csv`,
`out/m6_fig_mrs_D.png`, `out/m6_fig_zscan_D.png`. All products fetched
anonymously from public MAST — no account, no token, nothing submitted.*

M4 §5.2 confirmed D's contamination from imaging and marked the redshift
**UNSOURCED**: *"the redshift rests entirely on the MRS emission lines, which were
not reduced here."* Hephaistos IV's z = 0.922 rests on a spectrum nobody outside
the collaboration has extracted. **The cubes are public and are now reduced.**

### 2.1 What was fetched, and what "reduced" means here

**All 39 of D's GO 7199 observations are PUBLIC**, including **24 MIRI/IFU
Level-3 cubes** on the target — twelve on the science association
`jw07199-o002_t003` and twelve on the combined `jw07199-c1001_t003`. The twelve
`o002` `_s3d.fits` cubes were downloaded (439 MB) and all twelve carry
**`CAL_VER 2.0.1` / `CRDS jwst_1535.pmap`** — **the same newer re-reduction M4
§5.1 found for the imaging**, not the 1.20.2 / 1364 the paper used. Wavelength
coverage **4.900–28.699 µm**, complete, with no gap.

**Stated plainly, per PR-2 and repo law.** These are STScI's pipeline Level-3
products; this project did not re-run `calwebb_spec3` from the uncalibrated
ramps, which needs a multi-GB CRDS cache and reproduces STScI's own file. **What
is new — and what nobody has published — is the spatially resolved extraction.**
The pipeline's own `x1d` is one aperture on the target and therefore *blends*
the star with the contaminant 1.23″ away. This is the first separation of the
two: **11,625 wavelength slices, each deblended** by the linear two-component
fit of PR-2, with both positions fixed at M4 §5's measured
(1.233″, PA 32.998°) and one plate offset per cube solved from the white light.

*One methodological change was made **because the acceptance test caught it**,
not to make a number come out: the PSF width scale and wing index are **fitted
per sub-band from each cube's own white-light image** rather than assumed from
the JDox FWHM relation, because a too-narrow model dumps the bright component's
wings into the faint one. The fitted widths run 1.0–1.6× the JDox value
(0.31″ at 5 µm to 1.57″ at 26 µm), and a Gaussian beat every Moffat on
white-light residual in every sub-band. **The test still fails**, and §2.2
reports it failing.*

### 2.2 PR-2's acceptance test — FAILED, and where

The extracted spectra were integrated over the real MIRI bandpasses (SVO Filter
Profile Service, anonymous) and compared with M4 §5.1's independently measured
imaging photometry. **Tolerance fixed in advance at ±30% per band per
component.**

| | MRS, µJy | M4 imaging, µJy | ratio | which component | |
|---|---|---|---|---|---|
| F560W star | 287.7 | 300.6 | **0.96** | dominant | **PASS** |
| F560W contaminant | 48.8 | 70.9 | 0.69 | sub-dominant | **FAIL** |
| F1000W star | 95.8 | 124.0 | 0.77 | sub-dominant | PASS |
| F1000W contaminant | 750.1 | 898.2 | **0.84** | dominant | **PASS** |
| F1500W star | 75.9 | 50.0 | 1.52 | sub-dominant | **FAIL** |
| F1500W contaminant | 3135.5 | 4159.1 | **0.75** | dominant | **PASS** |

**Result: FAIL — 4 of 6 within tolerance.** The structure of the failure is
clean and is itself the finding: **in every band the *dominant* member of the
pair passes, and only the *sub-dominant* one ever fails.** That is the signature
of PSF-wing leakage across a 1.23″ separation, and it is a quantitative
statement about what a parametric deblend of a pair at 2–6 PSF FWHM can and
cannot do — directly useful for candidate E's chain, where the same geometry is
expected.

*Two of the three reference values are themselves fragile, which is worth
recording but is **not** used here to reinterpret the test: M4 §5.4 flags the
F1500W star flux as "marginal; its leak correction is ~50% of the raw aperture
signal, and the paper's own value is a limit for the same reason", and the
F560W contaminant has now been measured three times independently — 118 µJy
(the paper), 70.9 µJy (M4), 48.8 µJy (here) — a factor 2.5 spread.*

**PR-2 fixed the consequence in advance and it is honoured: no redshift is
quoted from these data.** Everything in §2.3–§2.5 is reported as *what the data
show*, never as a measured redshift.

### 2.3 The blind redshift scan — it does not pin z, and that is the result

The contaminant's spectrum was continuum-normalised by a **z-independent** local
quadratic regression in log F vs log λ (window ±0.08 dex, a fixed *fractional*
width, so a rest feature seen at 12 µm is treated exactly as the same feature
seen at 24 µm), on the range where that window is two-sided — **5.89–23.81 µm**.
PR-2's fixed 15-feature list was cross-correlated over **0 < z < 3 at
Δz = 0.0005, 6,001 grid points**.

| | |
|---|---|
| blind best z | **1.0460** |
| peak / scan rms | **3.27** |
| score at the published z = 0.922 | 281.7, against a peak of 342.0 |
| five best separated peaks | 1.046, 1.016, 1.076, 0.976, 0.946 |
| **best z vs continuum window** | **0.4675 (±0.06 dex), 1.0565 (±0.08), 1.0255 (±0.10)** |

**The last row is the finding.** A ±0.02 dex change in the continuum
estimator — a change that cannot absorb any feature in the list — moves the best
redshift by **Δz ≈ 0.6**. The scan is dominated by the broad PAH complex, whose
centroid is degenerate with the continuum, and it does not converge. **The blind
cross-correlation does not measure a redshift for this object.**

**The star control says the same thing from the other side.** The identical scan
on the *star* — a bare M-dwarf photosphere (M4 §5.2) that must show no PAH
pattern at all — produces a peak at z = 1.926 at **4.16× the scan rms**, i.e. a
peak *higher* in relative terms than the contaminant's. **Peaks of this height
are noise**, and the control is what proves it rather than an assertion.

### 2.4 A sharper blind test on the same fixed list — and it is negative

Because the broad PAHs are the problem, a second blind test used **only the
narrow features** from the same fixed list (fine-structure and H₂), whose
centroids are not degenerate with the continuum, and the same fixed 5σ detection
rule, scanned blind over 0.05 < z < 2.5:

- the most narrow lines detected at ≥ 5σ at **any** redshift is **8**;
- at the published **z = 0.922 it is 3** (summed SNR 37.4);
- **41.1% of the redshift grid does at least as well.**

**z = 0.922 is not special in these data.** Testing the published hypothesis
directly does find seven of eight features at ≥ 5σ with the right sign —
PAH 6.2, 7.7, 8.6, 11.3, [Ar II], [S IV], H₂ S(3) — but their fitted centroids
scatter over **z = 0.88–1.03 (σ = 0.048)**, so PR-2's criterion (≥ 2 features,
each ≥ 5σ, agreeing on z to ±0.01) is **not met**, at the published z or at the
blind best z. The 9.7 µm silicate trough lands at **17.78 µm → z = 0.833**,
0.09 from the published value, and is explicitly not counted towards the
criterion.

### 2.5 Why it cannot settle it — one number, and it is not the noise

The noise is not the limit: the empirical high-frequency scatter is **26.7 µJy**
against a formal **25.0 µJy**, an inflation factor of **1.00**, so the per-slice
errors are honest. The limit is the **sub-band flux calibration of the deblended
spectrum**. Measured in the eleven MRS sub-band overlaps, the ratio of the redder
band to the bluer one runs

> **1.276, 1.171, 1.235, 0.892, 0.921, 0.999, 0.891, 0.984, 1.222, …**

— **stitching offsets of 11–28% at five of the eleven joins**, against feature
amplitudes of **10–25%** of the continuum. *The steps between sub-bands are the
same size as the features being searched for.* No redshift can be extracted from
a spectrum whose piecewise flux scale is uncertain at the amplitude of its own
features, and the offsets are reported rather than fitted away because removing
them would be a free parameter this project has not earned.

**So the answer to "what redshift do the data support" is: on this reduction,
none — and the reason is specific, measured, and fixable.** What would fix it is
named in §6: an **empirical PSF built from these same cubes** — each component
overwhelmingly dominates in some sub-band (the star ~8:1 in Ch1-short, the
contaminant ~40:1 in Ch4), so a wing-carrying PSF can be measured from the data
with no external model — which is the same fix the acceptance failure points at.

### 2.6 What the reduction *does* establish, and it is not nothing

1. **The identification no longer rests on data nobody outside the team has
   touched.** The cubes are reduced, and the contaminant's spectrum is extracted
   and in this repository.
2. **The contaminant is spectroscopically non-stellar, over 12 sub-bands instead
   of 3 photometric points.** Its flux rises by a factor ≈ 250 from 5 to 25 µm;
   a photosphere goes as λ⁻².
3. **M4 §5.2's power-law slopes reproduce, and one of them exactly**: the
   10–15 µm index is **3.79** here against M4's **3.8** from imaging. The
   5.9–10 µm index is **7.12** against M4's 4.4 over 5.6–10 µm — steeper,
   because the MRS range starts inside the rising wing rather than at the pivot.
4. **M4 §5.2's 441 K single blackbody is tested for the first time, and it is
   ~10% too hot.** The best single blackbody over 11,625 slices is
   **T_obs = 205 K → 394 K rest-frame** granting z = 0.922, against M4's
   **441 K** from three points. *A single blackbody is a poor description of a
   PAH-bearing, silicate-absorbed spectrum, which is itself the point: the number
   M4 quoted was never going to be better than the model behind it.*
5. **A publishable negative with a named remainder.** An independent extraction
   exists; it is consistent with a dust-obscured, PAH-bearing galaxy; and it
   **cannot confirm z ≈ 0.922** at a bar fixed before the data were touched.
   **The published identification still rests on a reduction only the
   collaboration has done.**

---

## 3. Injection–recovery — the catalogue's completeness, measured

*`scripts/m6_injection.py` (`run`, `report`); artifacts
`data/injection/m6_injection_table.csv` (75,600 rows, gitignored bulk),
`out/m6_injection_completeness.json`, `out/m6_injection_by_*.csv`,
`out/m6_fig_completeness.png`. **No network was used at any point** — M5 §7
item 4's own observation.*

M5 §4 marked the high-latitude catalogue's completeness **UNMEASURED** and called
it the biggest hole in the positive deliverable. **75,600 synthetic
star + blackbody SEDs** were injected onto real parent hosts and pushed through
the **unmodified** pipeline: **67,200** across PR-3's declared factorial space
(8 covering fractions × 7 dust temperatures × 6 |b| bands × 200 hosts) plus
**8,400 γ = 0 controls**.

**The host is real, and so is the noise.** Each injection takes a real parent
row's distance, M_G, Gvar, RUWE, `ext_flg`, `classprob` and Galactic latitude.
Per-band uncertainties for W1–W4 are drawn from a **real parent row of the same
band, the same |b| band, and the same magnitude to ±0.25 mag**, i.e. at the
*injected* brightness rather than the host's — which is what makes the S/N ≥ 3.5
gate mean anything. Gaia and 2MASS carry adopted floors (0.005–0.03 mag),
documented rather than fitted, and far below the 0.2 mag RMSE gate. **If the
injected W3 or W4 magnitude is fainter than anything the survey detects in that
band and latitude, the object is recorded UNDETECTED and counted as not
recovered** — a real part of the selection function, not a failure of the code.

### 3.1 The control: the RMSE gate admits nothing on noise alone

**8,400 bare photospheres (γ = 0) were pushed through the same pipeline. The
RMSE ≤ 0.2 gate passed 0.00% of them; the pre-visual chain passed 0.00%.** The
gate's own false-positive rate on the real photometric error distribution is
**zero to 1 part in 8,400**. Whatever the 1,545 pre-visual survivors are, they
are not photospheres scattered over the line by noise.

### 3.2 The completeness function

| γ injected | n | RMSE gate | **pre-visual** | undetected |
|---|---|---|---|---|
| 0.01 | 8,400 | 0.0000 | **0.0000** | 11.2% |
| 0.02 | 8,400 | 0.0014 | **0.0001** | 8.3% |
| 0.05 | 8,400 | 0.0750 | **0.0246** | 5.6% |
| **0.10** | 8,400 | **0.8127** | **0.4385** | 5.7% |
| 0.15 | 8,400 | 0.8155 | **0.4438** | 6.0% |
| 0.20 | 8,400 | 0.7992 | **0.4410** | 7.1% |
| 0.30 | 8,400 | 0.7608 | **0.4340** | 10.2% |
| 0.50 | 8,400 | 0.6985 | **0.3973** | 15.9% |

| T_ds injected | RMSE gate | **pre-visual** | | \|b\| band | RMSE gate | **pre-visual** | undetected |
|---|---|---|---|---|---|---|---|
| 100 K | 0.568 | **0.307** | | 0–5° | 0.500 | **0.246** | 12.8% |
| 150 K | 0.561 | **0.324** | | 5–10° | 0.532 | **0.292** | 5.8% |
| 200 K | 0.540 | **0.311** | | 10–20° | 0.529 | **0.295** | 4.4% |
| 300 K | 0.581 | **0.326** | | 20–30° | 0.536 | **0.304** | 3.1% |
| 450 K | 0.611 | **0.330** | | 30–50° | 0.434 | **0.249** | 13.3% |
| 700 K | 0.593 | **0.307** | | 50–90° | 0.441 | **0.250** | 13.1% |
| **1000 K** | **0.013** | **0.0017** | | | | | |

**Four things fall out, and three of them were not known.**

1. **The γ ≥ 0.10 model-grid floor is a cliff, and it now has a number.**
   Recovery is **0.00% at γ = 0.01, 0.01% at γ = 0.02, 2.5% at γ = 0.05, and
   43.9% at γ = 0.10.** M5 §4 said the catalogue "misses the majority of weaker
   excesses by construction"; the measurement is harsher than that —
   **it misses essentially *all* of them.** Below γ = 0.05 the screen is not
   inefficient, it is blind.

2. **The grid's *temperature* range is a second hard boundary nobody had
   costed.** At **T_ds = 1000 K, outside the pipeline's own [100, 700] K grid,
   recovery collapses to 0.17%** — from ~31% at every temperature inside it.
   The screen is as blind to hot shells as it is to thin ones, and this is a
   property of the **grid**, not of the photometry: the RMSE gate itself passes
   only 1.3% of them because no in-grid model can fit the SED.

3. **Recovery *falls* at high covering fraction**, 44.4% at γ = 0.15 to 39.7% at
   γ = 0.50, and the reason is in the last column: Suazo Eq. 3's obscuration
   dims the star by −2.5 log(1−γ), so a heavily-covered object is *fainter*, and
   the undetected fraction climbs **5.7% → 15.9%**. **The selection is not
   monotonic in the thing it is selecting for.**

4. **The latitude dependence is mild and it is not monotonic**: 24.6% at
   |b| < 5°, rising to 30.4% at 20–30°, then falling to **24.9% at |b| > 30°**.
   The plane loses objects to background and crowding; **the high-latitude
   sample loses them to depth** — 13.3% of injections at |b| > 30° are simply
   too faint in W3 or W4 to be detected at all, against 3.1% at 20–30°. This is
   the same fact M5 §2.1 read off the SUB-THRESHOLD rate rising with |b|, now
   measured from the other direction.

### 3.3 The number the catalogue needs

Averaging over the declared space mixes in cells the pipeline cannot reach by
construction, so the headline is reported **inside the model grid** — γ ≥ 0.10
*and* 100 ≤ T_ds ≤ 700 K, the region the pipeline's own model can represent
(n = 36,000):

| | pre-visual recovery |
|---|---|
| all sky | **50.2%** |
| \|b\| < 10° | 49.6% |
| **\|b\| > 30° — the catalogue's footprint** | **45.8%** |
| **\|b\| > 50° — the calibrated core** | **45.8%** |

**Where the other 54% goes, at |b| > 30°**: 20.2% never detected in W3 or W4;
31.2% removed by the extra cuts (Gvar, RUWE, `ext_flg`, `classprob`, all
inherited from the real host); 3.2% removed by the S/N ≥ 3.5 gate; the RMSE
gate itself passes 90.3%. **The RMSE fit is not the bottleneck — the host's own
Gaia quality flags are.**

*Across the full declared space, including the cells outside the grid, the
|b| > 30° recovery is **24.9%**. Both numbers are in
`catalog/catalog_stats_v2.json`; the in-grid one is the one that answers "if a
real object of the kind this screen models existed, would we find it".*

### 3.4 What is now measured, and what stays UNMEASURED

**Measured**: the recovery fraction as a function of (γ, T_ds, W3 magnitude,
|b|) for the model family the selection itself assumes — a single blackbody
shell around a main-sequence photosphere — with the survey's own noise and the
real hosts' own quality flags.

**Still UNMEASURED, and marked so in v2**: excesses whose SED is *not* of that
family. A two-temperature debris disk, a silicate-featured disk, an edge-on
system, anything with structure the 10-band photometry cannot represent — the
injection cannot reach them, because it can only inject what the forward model
can generate. **An injection–recovery test measures the pipeline against its own
model, and saying so is part of the measurement.**

---

## 4. Candidate E — READY, and nothing about it pre-empted

*`scripts/m6_e_ready.py`; artifacts `out/m6_e_readiness.json`,
`out/m6_e_ready_validate.log`, `out/m6_e_ready_status.log`.*

PR-4 permits exactly three actions and no analysis. All three were run today.

**1. The outcome map is unedited, and the check is a hash rather than an
assertion.** M5 §5.3's four-case outcome map is only worth something if it has
not moved since it was written. §5.3 of the working-tree M5 document is
**3,586 characters**, SHA-256 `fa93e2c852befdb5…`, and it is **byte-identical to
the same section of the last committed M5** (`4c50380`). **All four cases are
present** — contaminant above the archival floor, contaminant below it, no
contaminant, data unusable. Nothing in M6 touches it.

**2. The procedure still runs, and still reproduces M4 §5 on all seven checks.**
M5 §5.2's parameterised chain was re-pointed at candidate D and re-graded:

| check | M5 chain, re-run today | M4 §5 | tolerance | |
|---|---|---|---|---|
| separation | 1.233″ | 1.230″ | ±0.02 | **PASS** |
| position angle | 32.998° | 33.000° | ±1.0 | **PASS** |
| ρ F560W | 0.236 | 0.236 | ±0.02 | **PASS** |
| ρ F1000W | 7.242 | 7.242 | ±0.145 | **PASS** |
| ρ F1500W | 83.135 | 83.134 | ±1.66 | **PASS** |
| ρ(W3, 12 µm) | 21.811 | 21.800 | ±1.5 | **PASS** |
| predicted W3 pull | 1.179″ | 1.180″ | ±0.03 | **PASS** |

**7 of 7. READY.**

**3. E's data are still embargoed, exactly as M5 recorded.** Anonymous MAST,
`proposal_id = 7199`, target `Object_E`: **0 PUBLIC of 39**, single release date
**2026-09-09**, unchanged from M5 §5.1. **Nothing was fetched and nothing was
analysed.** The script is written so that it would *still* stop even if E had
become public early, because M5 PR-4 fixed the analysis to on-or-after the
release date and moving it forward is exactly the after-the-fact choice the
outcome map exists to prevent.

**One thing M6 adds to E's file, from §2, and it is a warning rather than a
change.** D's MRS acceptance test failed on the **sub-dominant** member of the
pair in two of three bands (§2.2). E's imaging has D's geometry — the same three
filters, the same exposure time, hosted on the same `_background` observation —
so if E's contaminant is *fainter* than E's star in a band, that band's contrast
should be treated as uncertain at the tens-of-percent level rather than at the
±10% M4 §5.4 quoted for D's ratios. **This does not alter the outcome map**,
which turns on (separation, contrast) at the order-of-magnitude level and on
whether the archival centroid points at the real contaminant, neither of which a
30% contrast error can flip.

---

## 5. Recommended M7

1. **Finish D's redshift with an empirical PSF — the fix §2.5 names, and it needs
   no new data.** The acceptance test failed on the *sub-dominant* component in
   two of three bands, and the sub-band stitching offsets reach 28%; both are
   symptoms of a parametric PSF with no wings. **The cure is in the cubes
   already downloaded**: the star outshines the contaminant ~8:1 in Ch1-short
   and the contaminant outshines the star ~40:1 in Ch4, so a wing-carrying
   empirical PSF can be built per sub-band from the data themselves and iterated
   against the deblend. If the acceptance test then passes at the *unchanged*
   ±30%, the redshift may be quoted; if it still fails, the reduction's ceiling
   is real and that becomes the statement. **Highest value per hour in the
   project that does not have a date.**
2. **Candidate E on 2026-09-09.** §4's three commands, M5 §5.3's outcome map
   (hash-verified unedited), and the falsifier for M5 §6's retirement of V5
   written down in advance. Add §2.2's warning: treat any band's contrast as
   uncertain at the tens-of-percent level when the contaminant is the fainter
   member there.
3. **Extend the injection–recovery beyond the model family.** §3.4's stated
   limit: the test measures the pipeline against its own forward model. Injecting
   **two-temperature** and **silicate-featured** SEDs — which the fit cannot
   represent — would convert "UNMEASURED for other SED families" into a number,
   and it is the same code with a different generator.
4. **Re-cost the γ ≥ 0.01 floor with §3's completeness in hand.** M3 measured
   that dropping the floor multiplies survivors by 2.93×; §3 now shows the
   recovery *at* γ = 0.01 is **0.0000**, so the two statements together bound
   what a lower floor would buy and what it would cost. One run, no network.
5. **Separate galaxies from stars in N3** — carried unchanged from M5 §7 item 5.
   §3.3's interloper density is still an upper bound because it counts sources.
6. **The two small items carried forward from M5 §7 item 6**: (a) M4 §7.7's ~3%
   parent residual; (b) the γ ≥ 0.01 sensitivity on the full sky.
7. **Matthew's calls, unchanged and still waiting** (M2 §5.5, M3 §7.6, M4 §7.8,
   M5 §7.7): (a) whether the Ren+24 unit-error note is worth submitting given
   Blain's prior "(sic)", and if so the three manual browser checks first;
   (b) whether the candidate-I dossier becomes a JWST DDT / small-GO proposal,
   an RNAAS note, or stays internal. **M6 adds no new Matthew-gated item.** No
   object reached STILL-CLEAN and none can; the catalogue is a repository
   product; and §2's result is a negative about a published claim, which under
   M5 PR-4's own rule would be gated only if it were to leave this repository —
   it is not.

---

## 6. File index (new in M6)

**Document:** `M6-morphology-mrs-completeness.md` (this).

**Product:**

- `catalog/dyson-revet_highlat_extreme_IR_excess_v2.csv` — the high-latitude
  catalogue, **v2**: same 223 rows, N4's coadd-morphology statistics and flag
  added per row
- `catalog/catalog_stats_v2.json` — completeness **measured** where §3 measures
  it, still UNMEASURED where it does not
- `catalog/README_v2.md` — v2's own README, with the v1 → v2 difference
  enumerated
- `catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv`, `catalog_stats.json`,
  `README.md` — **unmodified**, per PR-3

**Scripts (new):**

- `scripts/m6_morph.py` — N4: `coadd` (coadd_id per position through Gator),
  `stats` (the IBE cutouts and S / A / G / C), `calibrate` (PR-1's threshold
  rule), `apply`
- `scripts/m6_mrs_reduce.py` — D's MRS cubes: `fetch`, `extract` (the
  per-slice two-component deblend with a fitted PSF)
- `scripts/m6_mrs_redshift.py` — the acceptance test, the blind z scan, the
  narrow-line consensus scan, the star control, the feature fits, the
  continuum-shape test
- `scripts/m6_injection.py` — `run` / `report`: injection–recovery completeness
- `scripts/m6_catalog_v2.py` — the v2 catalogue build and its diff against v1
- `scripts/m6_e_ready.py` — PR-4's three checks (outcome-map hash, procedure
  re-grade, MAST status)
- `scripts/m6_figures.py` — the four figures, from the artifacts

**Scripts changed:** none. M5's and M4's scripts are untouched, so their runs
reproduce exactly as they were issued. `m6_morph.py` carries its own
`parse_ipac_keepstr` rather than widening `m5_nebular.parse_ipac`'s string-column
whitelist, for the same reason.

**Artifacts:**

- `out/m6_morph_{rmse,candidates}.csv`, `out/m6_morph_flags_*.csv`,
  `out/m6_morph_thresholds.csv`, `out/m6_morph_calibration.json`,
  `out/m6_morph_enrichment.json`, `out/m6_funnel_morph.json`,
  `out/m6_rmse_survivors_morph_m4_g0.1.csv`
- `out/m6_mrs_D_spectra.csv`, `out/m6_mrs_D_cubes.csv`,
  `out/m6_mrs_D_{contaminant,star}_spectrum.csv`,
  `out/m6_mrs_D_redshift.json`, `out/m6_mrs_D_zscan.csv`,
  `out/m6_mrs_D_narrow_consensus.csv`
- `out/m6_injection_completeness.json`, `out/m6_injection_by_*.csv`
- `out/m6_e_readiness.json`, `out/m6_e_ready_{validate,status}.log`
- `out/m6_fig_{mrs_D,zscan_D,morph,completeness}.png`
- `data/jwst/mrs/*.fits` — the twelve L3 MRS cubes (439 MB) and
  `data/morph/` — the coadd_id tables and the per-object cutout statistics.
  Bulk intermediates live under `data/` and are gitignored per repo convention:
  the twelve MRS cubes, the per-object cutout statistics, the 28,000-row N4
  calibration table (`data/morph/m6_morph_calib.csv`, 12 MB) and the 75,600-row
  injection table (`data/injection/m6_injection_table.csv`, 36 MB). What is
  committed is the derived tables and figures in `out/`.

**Nothing in this milestone has been submitted, posted, or sent anywhere. No
account was created at IRSA, MAST, SVO or anywhere else; every service was used
anonymously. The candidate-I dossier and the Ren+24 note remain Matthew-gated
and unchanged.**
