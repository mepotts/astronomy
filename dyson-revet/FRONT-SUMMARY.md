# dyson-revet — front summary

*The one document to read to pick this front up. Written at the close of **M7**
(2026-08-24), covering M1 → M7. Every number here is emitted by a script in
`scripts/` and lives in `out/` or `catalog/`; nothing is hand-copied, and every
externally-sourced number carries its source or the mark UNSOURCED.*

> **Status: the front is finished pending its dated triggers.** There is no
> open work item before **2026-09-09**, when candidate E's JWST data become
> public. Nothing in this repository has been submitted, posted, or sent
> anywhere.

---

## 1. What this front is

Suazo et al.'s *Project Hephaistos* searched Gaia DR3 × 2MASS × AllWISE for
stars with an extreme mid-infrared excess — the photometric signature a partial
Dyson sphere would leave — and published **seven candidates** (Hephaistos II)
plus later follow-up (III, IV). **This front re-ran that search from public data
alone**, to answer three questions the papers leave open:

1. **Does the published selection reproduce, stage by stage, from public data?**
   Two of its stages — a CNN and a human visual inspection — are not published in
   a reproducible form.
2. **Do the surviving candidates survive independent vetting?**
3. **What is the resulting sample actually good for** — what would it take for
   one of these objects to be real, and what is the screen blind to?

**No telescope time was used and no proposal was written.** Everything here comes
from public archives (Gaia, 2MASS, AllWISE, VizieR, MAST, IRSA), used
anonymously, plus one JWST programme (GO 7199) whose data became public during
the work.

---

## 2. What the re-screen established

### 2.1 The selection reproduces, and the funnel closes to ~12%

| stage | this project | Hephaistos II Table 4 | ratio |
|---|---|---|---|
| RMSE ≤ 0.2 fit | 9,486 | 11,243 | 0.84× |
| + nebular stage | **6,043** | 5,732 *(their CNN)* | **1.05×** |
| + extra cuts | 5,541 | 5,137 | 1.08× |
| **+ S/N ≥ 3.5 — pre-visual** | **411** | **368** | **1.117×** |

**All-sky overproduction went 4.20× → 1.59× → 1.117×** across M4 → M5 → M6,
i.e. **96.3% of the excess over the published yield was removed**, and **every
latitude band now sits within ±50% of the published rate** against 20.89× in the
Galactic plane before any nebular stage. **1.211× on the conservative
area-corrected reading; both are reported and neither is chosen.**

**The whole sky is screened.** M4 closed the last of it — 100% coverage, without
ESAC, via the AIP mirror after ESAC's TAP proved unreliable at scale.

**Three replacement stages were built for the two unpublished ones**, all with
rule-fixed thresholds and **no training set and no new free parameter**:

- **N1** vetoes on the published angular extent of **29,462 nebulae from 14
  VizieR catalogues** — zero free parameters.
- **N2** cuts on AllWISE's own coadd background at a rule-fixed 0.99 percentile.
- **N4** (M6) reads the W3/W4 coadds directly: **S = σ_obs/σ_exp**, the robust
  dispersion of the PSF-smoothed image over what the coadd's *own uncertainty
  image* predicts, in a 12–45″ annulus. **Parameter-free null of 1**, measured
  1.396 (W3) / 1.245 (W4) on 27,876 high-latitude parent stars; threshold is
  N2's rule verbatim; **measured false-positive rate 1.20%**.

**Each passed the same three pre-registered validations**: they flag **none** of
the ten labelled Hephaistos objects (7/7 published candidates preserved); the
flagged fraction falls **monotonically** with |b| (N4: 70.3 → 1.1%); and at
|b| > 50° the flag rate sits **at or below its own false-positive rate** — **the
stages do nothing where M4 proved nothing needs doing.**

**N4 sees what a catalogue veto and a background cut cannot: 486 objects —
5.1% of the RMSE survivors — that no catalogue lists and whose background is not
in the top 1%.** M5 predicted that category and could not measure it.

### 2.2 The candidates

**Of the ten labelled Hephaistos objects, none survives this project as a clean
candidate, and the tally is by measurement rather than citation:**

- **D — contamination confirmed from the imaging, by this project.** M4 measured
  a second source at **1.233″, PA 32.998°**, contrast rising from 0.24 at 5.6 µm
  to **83× at 15 µm**. **D is retired** (M2, append-only, in four places).
- **I — not unrefuted; *unvettable*.** ([`I-dossier.md`](I-dossier.md).) Both
  WISE bands fall **below WISE's own on-ecliptic 5σ limits** (0.44×, 0.62×), both
  sit inside neighbouring sources' upper limits, W3 carries quality flag 'U', an
  independent reduction never detected W4, and the single-exposure detection
  counts are **0 and 1**. Re-stated in flux the excess is **W3 1.3σ, W4 3.3σ,
  joint 3.5σ pre-trials** (a W2 control at 0.5σ caught a colour-sign bug that had
  faked an 8σ W2 excess). **Nothing but WISE has ever observed it above 5 µm.**
  Settling it is **one JWST/MIRI visit, ~1.2 h charged** — Matthew's call.
- **C** reproduces the published refutation to **0.05″**.
- **A** — its GO 7199 data remain under exclusive access until **2027-07-16**;
  M2 found the third GO 7199 target matches candidate A, absent from
  Hephaistos IV, so the JWST-vetted sample becomes 3 when it opens.
- **E** — data open **2026-09-09**; see §6.
- **No object anywhere in this project reached STILL-CLEAN, and none can** — that
  verdict was retired with the centroid axis (§3.2), and no product describes any
  object as clean.

### 2.3 Candidate D's spectrum — an independent extraction exists, and it cannot confirm the published redshift

Hephaistos IV identifies D's contaminant as a galaxy at **z ≈ 0.922** from MIRI/MRS
emission lines. **That spectrum had never been extracted outside the
collaboration**, because the pipeline's own `x1d` is one aperture and blends the
star with the contaminant 1.23″ away.

**M6 reduced the twelve public Level-3 cubes** (4.90–28.70 µm, 11,625 slices
deblended) and **M7 rebuilt the deblend with an empirical, wing-carrying PSF
measured from the same cubes**. The chain of results:

- **The extraction now passes its pre-registered acceptance test 6 of 6** —
  synthetic photometry against independently measured MIRI imaging, ±30% per band
  per component — where M6's parametric version failed 4 of 6. **The test was
  graded by byte-identical code and its tolerance was never moved.**
- **The deblend is validated against a known truth.** Injecting a companion of
  known flux fraction into the cubes: a wingless Gaussian **under-recovers a
  companion at 1% of the primary by 42%** (59% on the resolved sub-bands) and is
  unbiased at 30%; the empirical PSF is flat and unbiased at **1.00** across the
  whole range.
- **And the spectrum still does not pin the redshift.** The blind
  cross-correlation peaks at z = 2.436 at **2.60× the scan rms** — *below* the
  **3.92×** reached by the **star control**, a bare M-dwarf photosphere that
  cannot have PAHs. A ±0.02 dex change in the continuum window moves the answer
  by **Δz ≈ 1.5**. A blind narrow-line consensus scan finds **42.9% of the
  redshift grid does at least as well as z = 0.922**, which is not among the best.
- **What the data do show**: the contaminant is spectroscopically non-stellar
  over 12 sub-bands (×250 rise from 5 to 25 µm), M4's 10–15 µm index reproduces
  (**3.96** vs 3.8), M4's 441 K single blackbody comes out **384 K** rest-frame,
  the 9.7 µm silicate trough lands at z = 0.833, and **7 of 8 features are
  detected at ≥ 5σ at the published z with the right sign** — but the same
  procedure finds comparable evidence at 43% of all redshifts, so that count is
  not evidence.

> **The headline: the published identification of candidate D's contaminant
> cannot be independently checked from public data. With the deblend fixed,
> validated, and excluded as the cause, the limit is the achievable spectral
> fidelity of public MRS Level-3 cubes on a 1.23″ pair.** *This is the front's
> most publishable single result and it is not written up. It is a negative about
> a published claim, so under M5 PR-4's own rule it is **Matthew-gated before it
> leaves this repository**.*

---

## 3. What the re-screen could **not** establish

**These are the front's limits, stated as measurements rather than caveats.**

### 3.1 The 12.7-point residual at the RMSE gate

At the gate where the comparison is cleanest, **this project's nebular stage
rejects 36.3% where the paper's unpublished CNN rejects 49.0%.** M5's two
components closed 5.1 points of the original 17.8; **12.7 points remain and they
are unmeasured.** The named candidates, stated rather than guessed:

- morphology of the **source** rather than of its field, which N4's statistic
  deliberately excludes by starting its annulus at one W4 FWHM;
- nebulosity on scales **larger than the 45″ aperture**, which a fixed-window
  statistic cannot see;
- whatever a classifier trained on 960 hand-labelled images encodes that no
  closed-form statistic does.

**The residual is itself a published measurement of what the unpublished stage
was doing** — roughly 1.6× more than every catalogued nebula on the sky plus a
1%-FPR background cut. That is the front's clearest statement about
reproducibility, and it points both ways: the pre-visual *yield* reproduces to
1.12×, but the *classifier* does not reproduce.

### 3.2 The centroid blind spot — the axis that had to be retired

M2 measured it on the one object with ground truth: **a JWST-confirmed
contaminant at 1.0″ moved the WISE centroid by only 0.5–1.4″**, i.e. the
archival centroid resolution floor is **1–2″**. **The direction is wrong too**:
M4 measured the W3 centroid at **PA 82.9°** against the real contaminant's
**PA 33.0°** — a **49.9° error**, i.e. the axis is uninformative in direction as
well as in magnitude near the floor. **The V5 centroid axis is formally retired
(M5 §6), and with it the STILL-CLEAN verdict, whose positive-evidence
requirement can no longer be met by anything.**

The consequence is structural and is carried in every product: the surviving
objects are **"no *detectable* contamination given a method with a known blind
spot"**, never "clean". Geometrically the blind fraction is **≈10% at a 1″ floor
and ≈40% at 2″**, and that estimate rests on an assumed uniform background —
candidate E is the one chance to give it an empirical anchor (§6).

M5 also measured V4's chance-alignment prior locally for the first time — a
**factor 372** away from a single global value — and it is still far short. **The
interlopers that matter are the ones AllWISE never resolves.**

### 3.3 The completeness walls, and the fact that they move with the model

The selection function was measured by injection–recovery — **176,400 synthetic
objects in total** across M6 and M7, on real hosts with the survey's own noise at
the injected brightness, through the **unmodified** pipeline.

**Inside the model grid the pre-visual recovery is 45.8% at |b| > 30° for the
family the selection assumes** (one blackbody shell round a main-sequence
photosphere) — and **26.1% to 44.4% once other SED families are allowed.**

Three walls, all measured:

1. **The γ floor is absolute below 0.02**: recovery is **0.00%** at γ = 0.01 and
   ≤ 0.05% at γ = 0.02 in every family. **The screen is blind, not inefficient,
   to weak excesses.**
2. **At γ = 0.05 the wall is family-dependent** — 1.8% for a blackbody, **11.3%**
   for optically-thin dust, 0.05–0.14% for a two-temperature shell.
3. **The temperature wall belongs to the family, not to the screen.** M6 found
   recovery collapsing to 0.17% at T = 1000 K and called it a hard boundary. For a
   **two-temperature** shell it is **30–37%** at T_warm = 1000 K (the cool
   component is back inside the grid); for **optically-thin dust** the wall moves
   *down*, to below 700 K at β = 1 and below 450 K at β = 2. **Every family has
   its own wall at its own temperature.**

**Still UNMEASURED**: silicate-featured SEDs, edge-on geometry, and anything
whose 10-band photometry none of the three tested families can generate. **An
injection–recovery test measures the pipeline against the families it is given,
and saying so is part of the measurement.**

### 3.4 What was never attempted

- **No spectroscopy of any candidate was obtained** — the front is archival.
- **The published CNN and visual stages were never reproduced**, only replaced
  and the difference measured (§3.1).
- **N3 does not separate galaxies from stars**, so its interloper density is an
  upper bound because it counts sources.
- **M4's ~3% parent-sample residual** is unresolved.

---

## 4. What the catalogue is, and is not, usable for

**`catalog/dyson-revet_highlat_extreme_IR_excess_v3.csv` — 223 objects at
|b| > 30° (20,626 deg²), of which 90 are the calibrated core at |b| > 50°
(9,651 deg²).** Versions v1 (M5), v2 (M6) and v3 (M7) all exist and **earlier
versions are never edited, moved or deleted**; **v3's rows are byte-identical to
v2's** — only the completeness statement changed.

**It IS usable for:**

- **A reproducible, sky-complete, selection-function-defined sample** of extreme
  mid-IR-excess stars within 300 pc, with every stage's rule written down and
  every threshold rule-fixed.
- **A target list for follow-up**, provided the user reads §3.2: these are objects
  with **no detectable contamination**, which is not the same as objects with no
  contamination.
- **Rejects are kept in-table with their evidence**, so the catalogue documents
  what was thrown away and why — 85 CONTAMINATION-CONSISTENT, 75 INDETERMINATE,
  63 SUB-THRESHOLD inside the footprint (1,545 objects vetted overall: 719 / 584 /
  242, and **0 still-clean by construction**).
- **A measured selection function**, per SED family, with the walls above.

**It is NOT usable for:**

- **Any statement of the form "these are Dyson-sphere candidates."** No object in
  it is a candidate for anything beyond "has an unexplained mid-IR excess and no
  contaminant detectable at archival resolution". The strongest published
  candidates all acquired contaminants when better data arrived.
- **A completeness-corrected space density.** There is **no single completeness
  number** — it runs 26.1% to 44.4% at |b| > 30° depending on the assumed SED —
  and the walls in §3.3 mean whole regions of (γ, T) are unreachable.
- **Reading a row's `t_ds` and `gamma` at face value.** If the true SED is not a
  single blackbody those are biased by **−36% to +48%** in temperature, and **the
  RMSE gate does not catch it** — accepted non-blackbody objects sit at 3–5× the
  residual of a blackbody and still clear 0.2 mag.
- **Anything below γ = 0.05**, where the screen is effectively blind.
- **The Galactic plane**, which the catalogue deliberately excludes; the nebular
  stage's residual there is a different problem (§3.1).

---

## 5. Method findings worth carrying to other fronts

These cost time to learn and generalise beyond this project.

1. **A wingless PSF silently steals flux from the fainter member of a close
   pair, and the bias scales with contrast** — 42% at 1:100, 1% at 1:3. **Build
   the PSF from the data**: whichever component dominates in some band is a free
   empirical PSF for that band.
2. **A two-component deblend is only determined while the pair is resolved.**
   Below ≈ 2 PSF FWHM the design matrix is collinear; the model-free symptom is an
   **unphysical negative fitted flux**, which reached 86% of slices at D's
   longest wavelengths. **Check sep/FWHM and the negative fraction before quoting
   any contrast.**
3. **A pre-registered criterion can be structurally undecidable, and only an
   audit finds it.** M6's "≥ 2 features agreeing on z to ±0.01" was satisfied
   *vacuously* by narrow lines (whose fitted centroid cannot move by more than
   0.0028) and *impossible* for broad ones (PAH 7.7 roams ±0.112). **Audit what
   range your fitter is allowed to search before you write a tolerance.**
4. **A control that out-scores the signal is the finding.** D's star control
   peaks higher than D's contaminant on the same redshift scan; that is what
   turns "we did not find a redshift" into "this statistic cannot find one here".
5. **An injection–recovery test measures the pipeline against its own model.**
   Adding one physically distinct family moved the completeness by up to 17.6
   points and withdrew a wall. **Always inject at least one family the fit cannot
   represent.**
6. **Route economics, measured, and they point opposite ways.** IRSA Gator's
   anonymous multi-position upload runs **0.0027 s/position against TAP's 3.5 s —
   ~1,300× faster** (a 3-hour pass in 8.1 s). IRSA's **IBE image service is hard
   capped at ~12 requests/s per client**, returns **HTTP 503 in ~0.1 s** under
   concurrency, and splitting across processes does not raise it. **A fetcher that
   read 503 as "no image" silently marked 927 good objects invalid**; both the
   back-off and the cache repair are now in the code. ESAC's TAP was unreliable at
   scale and the AIP mirror was not.
7. **Optimise nothing you have not controlled.** M6's and M7's own bugs were
   caught by internal checks (an encircled energy > 1; a sensitivity coming out a
   uniform factor 6 low), not by the headline test — which passed either way.

---

## 6. Standing triggers

| when | what | where |
|---|---|---|
| **2026-09-09** | **Candidate E's JWST GO 7199 data become public** (0 PUBLIC of 39 today). Run M6 §4's three commands, then M5 §5.3's **four-case outcome map**, which is **hash-verified unedited** (SHA-256 `fa93e2c852befdb5…`) across two milestones. Add M7 §1.7's determinacy check to the procedure and M7 §1.4's contrast-dependent bias to its interpretation. **The chain reproduces M4 §5 on 7 of 7 and is READY.** | `scripts/m6_e_ready.py`, M5 §5.2–5.3, M7 §3 |
| **2027-07-16** | **Candidate A's GO 7199 exclusive access ends** — would make the JWST-vetted sample 3 | M2 |
| **Matthew** | **Is the Ren+24 unit-error note worth submitting** given Blain 2024 fn 6's prior "(sic)"? The error is real (a 3600× arcmin²/arcsec² slip that *inverts* the conclusion) and the note is **DRAFTED, NOT SUBMITTED**; three verification checks were bot-blocked and are flagged must-do first | [`note-ren24-unit-error-DRAFT.md`](note-ren24-unit-error-DRAFT.md) |
| **Matthew** | **Does the candidate-I dossier become a JWST DDT / small-GO proposal, an RNAAS note, or stay internal?** Settling I is one MIRI visit, ~1.2 h charged | [`I-dossier.md`](I-dossier.md) |
| **Matthew** | **Should §2.3's negative be written up?** An acceptance-validated independent extraction that cannot confirm a published redshift, with the deblend excluded as the cause. Gated because it is a negative about a published claim | M7 §1 |

**E's outcome map matters more than E's data.** Its most consequential branch is
**Outcome 2** — a contaminant detected *below* the archival floor — which would be
a direct measurement of an object inside the blind spot and would convert §3.2's
blind-fraction estimate from geometry into something with an empirical anchor.
Its **falsifier is written down**: if E's archival centroid points *at* the real
contaminant, M5 §6's retirement of the centroid axis is too strong and must be
revisited.

---

## 7. Where everything is

| | |
|---|---|
| **Milestones** | `M1-reproduce-and-vet.md` → `M7-empirical-psf-completeness-close.md`. Each carries its own pre-registrations, written before the runs they govern. |
| **Products** | `catalog/` — v1, v2, v3, each with its own README and stats file; earlier versions never edited |
| **Matthew-gated** | `I-dossier.md`, `note-ren24-unit-error-DRAFT.md` — **DRAFT, not submitted, unchanged since M2** |
| **Code** | `scripts/` — `w*_` (M1–M2), `m3_`–`m7_`. **No milestone edits an earlier milestone's scripts**, which is what makes each milestone's numbers re-runnable as issued |
| **Artifacts** | `out/` — derived tables, JSON and figures, committed. `data/` — bulk intermediates (cubes, cutouts, injection tables), gitignored |
| **Repo law** | sourced-or-UNSOURCED; negative results are results; pre-registered acceptance tests are never weakened after seeing results; nothing submitted, posted or sent without Matthew's explicit per-item approval |

---

*Nothing in this front has been submitted, posted, or sent anywhere. No account
was created at any archive; every service was used anonymously.*
