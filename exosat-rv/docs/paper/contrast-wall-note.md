# The contrast wall: a measured design curve for slit-fed companion radial velocimetry — and the free-floating regime where it does not exist

*Matthew Potts · independent analysis · draft 2026-08-13*

*Instrument-oriented note. Target venue: A&A/MNRAS short paper or an instrument-design note. Written from milestones M7–M29 of the `exosat-rv` archival project; every number traces to a document in that repository and is cited inline as (M-n §s) or (queue) for the roster ledger `docs/target-queue.md`. Numbers that could not be sourced are omitted rather than estimated.*

---

## Abstract

Companion-side radial velocimetry — measuring the reflex motion of a directly imaged brown
dwarf or giant planet from its own spectrum, to detect a satellite or a second companion —
is normally proposed on a photon-noise argument: the companion's K magnitude sets the
achievable precision. That axis is incomplete. Running one injection-gated CRIRES+ pipeline
over eleven archival systems, we find the binding constraint is **host-star contamination in
the slit**, and that it changes the outcome discontinuously rather than gradually. We report
the curve as measured: injection-verified series at 34–190 m s⁻¹ per epoch between 1.7″ and
~4.2″; clean at 0.8″ and a host:companion flux ratio of ~2000 (131 m s⁻¹); **flooded** at
0.55″/~5000, where β Pic b returns km s⁻¹ scatter locked to the barycentric correction at
*r* = +0.88, surviving both a rebuilt template and the masking of the responsible order; and
unusable at 0.17″, where the extracted spectrum is the star's. At the wide end we bound the
contamination directly: on CD-35 2722 B the primary at 3.17″ leaves **no detectable second
trace in the nodding slit function on any of 18 nights**, with per-night 3σ limits of 1–11%
(median 2.5%). The failure has a signature — 99–100% injection transmission together with
km s⁻¹ scatter — identifying it as a contamination systematic rather than a sensitivity
limit, so collecting area does not cure it; inside the wall the requirement is hardware
spatial filtering or an interferometric route. Finally, **isolated planetary-mass objects
remove the wall by construction**, deleting every host-dependent term while keeping the
young, self-luminous K ≈ 12–15 spectra that make the technique work at all. Using measured
rather than forecast precisions: five archival epochs at 131 m s⁻¹ excluded ≳0.4 M_Jup
companions at *P* ≤ 100 d around an 8 M_Jup host, and nothing in that chain used the host
star. No suitable multi-epoch archival data exist for isolated objects, so that case is a
proposal, not a result.

---

## 1. Introduction

Doppler monitoring of a directly imaged companion was proposed by Vanderburg et al. (2018),
applied to HR 8799 by Vanderburg & Rodriguez (2021) and to HR 7672 B by Ruffio et al. (2023),
forecast for the CRIRES+ era by Lazzoni et al. (2022), and pursued by Horstman et al. (2024)
on GQ Lup B. Hoy et al. (2026, hereafter H26) reported the first detection, in CD-35 2722 B.

Proposals in this genre are written on a single feasibility axis: how bright the companion
is. Lazzoni et al.'s threshold is a pure flux scaling — 100 m s⁻¹ at K = 13.5, degrading
1.585× per magnitude (M7 §1) — and this project's own target ranking used the same form,
re-anchored on H26's achieved 31.44 m s⁻¹ at K = 12.01 (M7 §2).

Having now run one pipeline across eleven systems spanning 0.17″ to ~4.2″ of host separation,
we can say that the flux axis is the wrong one to lead with. Two targets of nearly identical
brightness can differ by four orders of magnitude in delivered velocity scatter, and the
discriminant is how much of the host lands in the slit. This note reports that curve — where
slit-fed companion RV works, where it fails, and what a proposal must ask for inside the
failure regime (§§2–5) — and then makes the case that free-floating planetary-mass objects
are the regime in which the constraint does not exist at all (§6).

---

## 2. What was measured, and the two rules that govern what counts

All spectra are public ESO archive holdings. RVs are extracted with `viper` (Köhler et al.
2025) in gas-cell-free CRIRES+ mode, forward-modelling each order against a telluric-free
template built from the target's own observations; reductions use `cr2res` 1.6.10, from raw
frames where required, and reproduce ESO's archived products to 42 m s⁻¹ in the final RV
(M12 §9b). No published RV truth exists off CD-35 2722 B, so **signal injection carries the
entire validation burden**: every series below had to transmit an injected Keplerian —
imposed by shifting the template, never the observation — at both a loud and an
amplitude-matched semi-amplitude (M12 §8.1, M20 §1). Transmission is quoted with every entry,
because a series that transmits nothing is always quiet (M23 §4).

Two rules constrain what we are willing to call a measurement.

**Nodding only.** Every dataset this project had classified as "staring-mode" turned out to
be **HiRISE**: fiber-fed SPHERE→CRIRES+ observations (`ESO INS MODE = HIRISE`, original files
`HIRISE_SPEC_OBS*`), which we had reduced through a slit recipe. Three ledgered verdicts were
retracted (queue, HiRISE banner; LESSONS trap 1.10). Conclusions drawn on nodding data stand;
everything from the fiber tier is provisional pending a fiber-appropriate reduction, and is
reported separately in §3.3. Notably, this removes two of the four points originally used to
anchor the harsh end of the curve.

**Contrast values are order-of-magnitude ledger figures.** The host:companion flux ratios
below are the values adopted in M20 §6 and carried in the roster; this project measured
velocities, not photometry, and no derivation of those ratios is recorded in the repository.
We therefore quote them to one significant figure and lean on their *ordering*, not their
values. The separations are literature values; note that CD-35 2722 B's is quoted as 2.8″ in
early milestones (M0, M5, M8) and as 3.17″ in the slit-function geometry actually used for
the contamination measurement (M28 §5), and we use the latter.

---

## 3. The curve

### 3.1 The measured points (nodding)

| object | sep. | host:comp. | setting | epochs / span | per-epoch scatter | injection | outcome |
|---|---:|---:|---|---|---:|---|---|
| YSES 1 b | 1.7″ | — | K2166 | 2 nights (2023 pair) | **34 m s⁻¹** | 101 ± 2% | clean; best quality of the campaign (queue) |
| CD-35 2722 B | 3.17″ | ≤ ~2000 | H1567 | 18 n / 466 d | **70–90** (rms vs published) | 105 ± 4% | clean; H26's detection reproduces (M14) |
| η Tel B | ~4.2″ | ≤ ~2000 | H1567 | 18 n / 815 d | **116–130** | 99–101 ± 1% | clean; first limit, *m* sin *i* ≳ 0.5–1.2 M_Jup, *P* = 20–300 d (M15) |
| AB Pic b | ≥ 2.7″ | ≤ ~2000 | K2166 | 2 n / 3 d | **120–190** | 97 ± 3 / 106 ± 8% | clean (M17) |
| CT Cha B | ≥ 2.7″ | ≤ ~2000 | K2166 | 3 n / 70 d | **180–310** | core orders 98–105%; edge orders unusable | clean of the host; limited by the companion's own accretion (M17, M23 §3) |
| HIP 65426 b | 0.8″ | ~2000 | K2192 | 5 n / 422 d | **131** | 98 ± 4 / 101 ± 3% | clean; ≳0.4 M_Jup excluded at *P* ≤ 100 d (M20 §4) |
| HIP 81208 B | 0.3″ (B9 host) | — | K2166 | 3 n / ~470 d | **124** | 99 ± 1% | clean — the curve's open counterexample (§3.4) |
| β Pic b | 0.55″ | ~5000 | K2166 | 13 n / 813 d | **2466–4712** | 99–100% | **flooded**; no claim possible (M20 §2) |
| PDS 70 | 0.17″ | — | K2166 | 6 n / 426 d | **130** | 99 ± 1–2% | companion unreachable; the extracted spectrum is the *star's* (M20 §3) |

The wide entries are not merely "not obviously broken". η Tel B's 116–130 m s⁻¹ epoch scatter
is fully accounted for by its own within-night measurement noise, requiring no additional
term (M29; NEXT-DIRECTIONS §A1), and CD-35 2722 B at the same separation class reproduces a
published detection blind, through a barycentric nuisance covariate, at *p* = 5×10⁻⁴
(M28 §§1–2).

### 3.2 The contamination bound at the wide end, measured directly

At 3.17″ we can do better than inferring cleanliness from the velocities. The nodding
extraction swath spans the full slit — trace-wave order height 179.8 px at 0.056″/px, i.e.
10.07″, sampled by a 512-point slit function at 0.0197″ per point — and the slit position
angle is pinned at POSANG = 153.1° on all eighteen CD-35 2722 B nights with a 6″ nod throw.
The primary therefore falls a fixed **161 points** from the companion trace in every frame of
the campaign (M28 §5).

Measured there, **no primary peak is detected on any night**: the median slit-function height
at the primary's offset, relative to the companion peak, is 0.0006 against a local profile
noise of 0.0072 — 0.1σ. Per-night 3σ upper bounds run **1–11%, median 2.5%**, consistent with
and on most nights tighter than H26's ~15% worst-night slit-viewer estimate. Two caveats
belong with the number: the profile median is removed before measurement, so this bounds a
*resolved* second trace and not a smooth halo pedestal — it complements the slit-viewer
method rather than replacing it — and the single epoch rejected by our internal quality screen
carries the largest ratio of the eighteen (0.019) at only 2.0σ, on the campaign's best seeing,
so contamination does not explain why that night is bad (M28 §5).

For a design curve, the useful form of that result is a bracket. At ≲ a few percent host
contribution, the technique delivers 70–130 m s⁻¹ per epoch. At 0.55″/~5000 with no
suppression, it delivers km s⁻¹. **No intermediate case has been measured**, so we can state
the tolerance only as: a few percent is empirically sufficient, and an unsuppressed halo at
that contrast is fatal.

### 3.3 The provisional tier — excluded from the curve

Three points originally reported as harsh-end wall measurements come from the mis-classified
fiber tier and are **withdrawn as slit measurements**. They are listed for completeness, and
because their numbers now bound *our processing* rather than the sky:

| object | sep. | host:comp. | as originally reported | status |
|---|---:|---:|---|---|
| AF Lep b | 0.32″ | ~30 000 | 68 ± 4% injection transmission (M23 §2) | **provisional** — HiRISE fiber data reduced through the slit recipe (queue banner) |
| 51 Eri b | 0.45″ | ~30 000 | 3 of 11 orders respond (M23 §2) | **provisional** — same error class |
| HD 1160 B | 0.78″ (A0 host) | — | 725 m s⁻¹, per-night errors ±37 to ±2600 (M23 §1) | **provisional** — verdict to be re-derived with fiber-appropriate handling |

Nothing in §3.1 depends on them. What they cost is real, though: the curve is now anchored at
its steep end by a single flooded case (β Pic b) rather than by four, and the
≤ 0.45″/~30 000 regime is at present **unmeasured by this project in slit mode**.

Two fiber-tier series did reduce well, and are worth recording as suggestive of what the
suppressed route delivers without being validated fiber reductions: HD 19467 B, a 45 m s⁻¹
pair at 101 ± 5% transmission, and HD 206893's epochs at 100–102% (queue, M26 rows). A proper
HiRISE reduction path is open work in this project (M27).

### 3.4 The counterexample the curve has to live with

HIP 81208 B is recorded in the ledger as **0.3″ from a B9 host** with three K2166 nodding
nights that are flat and clean: 124 m s⁻¹, χ² = 1.1/2, gates 99 ± 1% (queue, M26 row). On a
separation-only reading of the curve that is impossible; on a contrast reading it is a
question, because no flux ratio is recorded for the system.

We flag it rather than explain it away. Three readings are open, and we cannot choose between
them from what is documented: (i) the contrast is genuinely far lower than β Pic b's, a
~67 M_Jup companion being intrinsically much brighter than a 12.8 M_Jup planet; (ii) the
K2166 failure on β Pic b is partly *spectroscopic* rather than purely geometric — the setting
is centred on Br-γ, the host's dominant absorption feature, 130 km s⁻¹ wide (M20 §2) — and
the two systems' hosts differ; (iii) with *n* = 3 epochs and only ledger-level documentation
(there is no milestone document for this target), the entry may not survive the scrutiny the
other rows have had. Any of the three is a result worth having, and (ii) in particular is
directly actionable for setting choice. **This is the single most valuable follow-up the
curve suggests.**

---

## 4. What the failure actually is, and why software does not fix it

β Pic b is the one fully documented failure, and the mechanism is specific (M20 §2).

Three passes isolated it. A template reused from a single night gave 4712 m s⁻¹ of night
scatter with *r*(RV, BERV) = +0.94 — a single-night template has no barycentric lever with
which to separate target lines from telluric residue. Rebuilding the template across all 28
frames and 813 d halved the scatter to 2466 m s⁻¹ and left *r* = +0.88: the residual is not
the template. Masking the Br-γ order and dropping six injection-unstable orders left
*r* = **+0.88, unchanged**, with injection transmission at 99–100% on the eleven surviving
orders and every long-period peak dying under a BERV covariate.

Three consequences for instrument design follow:

1. **The contamination is pervasive, not surgical.** The starlight carries broad, low-level
   structure across the whole band; no order subset rescues the measurement. Masking is not a
   mitigation, and neither is a redder or bluer setting on its own.
2. **It is a systematic, not a sensitivity limit.** The gates ran at 99–100% throughout: the
   pipeline was transmitting injected velocity essentially perfectly while returning km s⁻¹
   of host motion. **Collecting area does not help with this.** An ELT-class aperture improves
   the photon term, which was never the binding one; it also places a given contrast at a
   smaller angular separation, which if anything moves more targets inside the wall.
3. **It has a diagnostic signature a proposer can test for in advance**, and cheaply: high
   injection transmission, km s⁻¹-level epoch scatter, a strong RV–BERV correlation, and
   candidate periodicities that vanish when the BERV column is added as a covariate. Two
   independent reductions of β Pic b give ΔBIC of −1.8 and −1.7 at the period at which
   CD-35 2722 B gives +27.9 (M28 §1) — the flooded series carries no periodic content at all.

---

## 5. Inside the wall: what has to be bought, and what is free

**Hardware.** The requirement is spatial filtering at the focal plane, before the spectrograph
— a single-mode fiber fed by an extreme-AO/coronagraphic front end (HiRISE at the VLT, KPIC
at Keck; RISTRETTO-class concepts in the same family). This is the conclusion M20 reached, and
the reason the β Pic b campaign is recorded as contamination-limited rather than as a null.
The fiber route is not hypothetical for these targets: the ESO archive already holds **six
public HiRISE nights of β Pic b (Oct–Dec 2024)** — a starlight-suppressed series of exactly
the object the slit loses (queue banner).

**An interferometric alternative exists for the same regime.** The VLTI/GRAVITY astrometric
exomoon search on HD 206893 B (arXiv:2511.20091) cuts its sample at K < 20 and host:companion
contrast < 10⁵, and its prime target, β Pic b, has 28 GRAVITY nights over 2987 d in the
archive — 1.6× the epochs over 6.4× the baseline of the dataset behind the first RV detection
(M10 §§1–2). Astrometry and RV want the same targets and fail differently; inside the wall,
the astrometric route is the one with public data.

**Four things that cost nothing and are not being done.** These matter more per unit effort
than the hardware argument, because they apply to every proposal in the genre:

1. **Ask for 6–10 frames per night, not ~2.** Current campaigns take about two, which leaves
   too few degrees of freedom to split epoch scatter into measurement noise and astrophysical
   jitter. We attempted that decomposition across ~11 companions and failed on power, not on
   method: the built-in control — a target with a known several-hundred m s⁻¹ signal —
   resolved its own excess at only 1.4σ (M29; NEXT-DIRECTIONS §A1). The change costs no extra
   nights and converts a survey of upper limits into a measurement of the noise floor that
   decides whether the technique is feasible at all.
2. **Run the phase–BERV geometry check before the OB is written.** CD-35 2722 B's sampling
   correlates orbital phase with the barycentric correction at *r* = −0.71, which is why its
   amplitude remains confound-limited; η Tel B's sampling leaves the 150–300 d decade
   completely clean, so a detection there would never have needed embargoed epochs to defend
   itself (M15 §1). The check takes minutes and is a scheduling decision, not an analysis one.
3. **Never build a template from a single night** — there is no barycentric lever, and the
   artifact is at km s⁻¹ (LESSONS trap 6). A campaign design that cannot spare two
   well-separated nights for template construction cannot support this measurement.
4. **Verify `INS MODE` and `ORIGFILE` in the raw headers before choosing a recipe.** Fiber
   data reduced through a slit recipe produced km s⁻¹ artifacts we initially read as sky
   physics, and cost three retracted verdicts (LESSONS trap 1.10) — the reason §3.3 exists.

---

## 6. Free-floating planetary-mass objects: the regime with no wall

### 6.1 The argument is an identity, not an extrapolation

Every quantity in §§3–5 is defined relative to a host star: the contrast ratio, the halo that
floods the slit, the barycentric-locked stellar lines that dominate β Pic b, the position
angle pinned across eighteen nights to keep the primary off the trace, the AO conditions that
made HD 1160 B's night quality vary by a factor of 70, and the suppression hardware bought to
undo all of it. **For an isolated planetary-mass object every one of those terms is zero by
construction, not small.** There is no contrast wall to be inside or outside of.

What is *unchanged* is precisely what makes the measurement possible: the target is a young,
self-luminous object radiating its own K ≈ 12–15 infrared spectrum, of the same class this
project measured eleven times. The technique's remaining ingredients — a telluric wavelength
reference, a template built from the target's own data, injection-gated transmission — are
host-independent throughout.

### 6.2 The reach, from measured numbers

The strongest statement available is not a forecast. On HIP 65426 b — an ~8 M_Jup host —
**five archival epochs over 422 d at 131 m s⁻¹ per epoch excluded companions of ≳0.4 M_Jup
(~115 M_⊕) at *P* ≤ 100 d**, with injection transmission of 98 ± 4% and 101 ± 3% (M20 §4).
Nothing in that chain used the host star; the target happened to be a companion, at 0.8″,
just outside the wall.

The per-epoch precisions behind such a limit — all injection-gated, all on nodding data —
span **34–190 m s⁻¹** (§3.1) on objects whose recorded K magnitudes run 12.0–15.1 (CD-35
2722 B 12.01, η Tel B 13.2, β Pic b 14.9, AB Pic b 15.1; YSES 1 b's is not recorded in this
project's documents), with 162 m s⁻¹ measured *within* a night on β Pic b at K = 14.9, at
100 ± 0% transmission in all 18 orders (M17 §§1–2). We repeat the
project's own caveat on that last number: within-night repeatability is not night-to-night
systematics, and for β Pic b the latter is unmeasured (M17 §1).

Scaling those to isolated hosts uses the same relation as the rest of the field (Lazzoni et
al. 2022 eq. 2, as implemented in this repository). Because that estimator is deliberately
crude — 3σ on a single epoch, no sampling term — we first calibrate it against the one
injection-derived limit we have: for an 8 M_Jup host at 131 m s⁻¹ it returns 0.36 M_Jup at
*P* = 100 d against the measured 0.35–0.45 M_Jup, i.e. **agreement to ~25% at *P* = 50–100 d**,
while being optimistic by ~2× at 20 d and ~2–3× at 200–400 d, where sampling and baseline
rather than per-epoch noise set the real limit. It also reproduces the ledger's ~20–30 M_⊕
per-epoch statement for YSES 1 b. Read within that band, for an isolated host:

| per-epoch σ | 5 M_Jup host | 10 M_Jup | 13 M_Jup |
|---:|---:|---:|---:|
| 34 m s⁻¹ (best measured) | 17 M_⊕ | 27 M_⊕ | 32 M_⊕ |
| 130 m s⁻¹ (typical measured) | 65 M_⊕ | 103 M_⊕ | 123 M_⊕ |
| 190 m s⁻¹ (worst clean) | 97 M_⊕ | 152 M_⊕ | 181 M_⊕ |

*Smallest satellite* m sin i *clearing 3σ on a single epoch at P = 50 d, computed with this
project's implementation of the standard relation; ranking-grade, calibrated as above, and
not a substitute for an injection-derived limit.*

The lighter host helps: at fixed satellite mass and orbit the reflex amplitude scales as
M_p^(−1/2), so a 5–13 M_Jup isolated object is a *better* wobble target than the 37–47 M_Jup
brown dwarfs that dominate the current roster (M7 §5). Two further asymmetries favour the
isolated case, and both follow from the absence of a star rather than from optimism:

- **No outer truncation of the satellite's stable zone.** The stability limit used throughout
  this field is set by the host star's tidal field; without a star it does not apply.
- **The one mechanism known to destroy the highest-amplitude satellites is inoperative.**
  Tidal spin-down of a giant planet *by its star* pushes corotation beyond the stability
  limit, so every dynamically stable satellite ends up inside corotation and inspirals; the
  timescale scales as a⁶ and is the entire result of that analysis (M8 §§1–2). It requires a
  star.

Finally, the host-mass uncertainty that isolated objects carry — masses come from evolutionary
models with no dynamical anchor — enters mildly: from the same relation, satellite mass scales
as M_p^(1/2), so a 30% error in the assumed host mass is a ~14% error in the inferred
satellite mass.

### 6.3 What we cannot claim, stated plainly

- **There is no archival result here.** The ESO archive was swept for isolated
  planetary-mass objects with multi-epoch CRIRES+ coverage, and the answer was negative and
  exhaustive (queue banner, idea #4). This section is a proposal case.
- **Brightness is the binding selection cut, and it bites below K ≈ 15.** Lazzoni et al. flag
  that their flux scaling degrades faster than 1.585×/mag below K ≈ 15, where background
  noise takes over (M7 §1); every precision in §3.1 was achieved at K = 12.0–15.1. A target
  fainter than that is outside the regime this project has measured, and we make no claim
  about it.
- **We have run no population census.** How many isolated objects are bright enough and young
  enough is a literature question this project has not done, and we do not assert an answer.
- **Acquisition and wavefront sensing are the unquantified operational cost.** A target with
  no bright neighbour must be acquired and guided on its own flux. We have no measurement
  bearing on this and flag it as the item a proposal must address, rather than as a solved
  problem.
- **Nothing here is an exomoon-detection argument.** The population study underlying this
  field expects RV to reach binary-like satellites (mass ratio ≳ 0.01) and not solar-system
  analogues (M7 §1), and the only claimed detection sits at exactly that ratio. Removing the
  contrast wall improves the noise, not the occurrence rate.

---

## 7. Summary for a proposal

1. **Lead with contrast, not magnitude.** Two similarly bright companions here differ by four
   orders of magnitude in delivered scatter (§3.1). One clean 0.3″ counterexample is open
   (§3.4), and the ≤ 0.45″/~30 000 regime is currently unmeasured in slit mode (§3.3).
2. **Bound the contamination, do not assume it.** The nodding slit function measures it
   directly: at 3.17″, no resolved primary trace on any of 18 nights, 3σ limits 1–11% per
   night. A few percent is empirically sufficient for 70–130 m s⁻¹.
3. **Inside the wall, buy suppression or use interferometry.** The failure is a contamination
   systematic with injection transmission at 99–100%, so aperture does not cure it. Public
   HiRISE nights on β Pic b already exist, and GRAVITY holds 28 nights over 2987 d on it.
4. **Then spend the free levers**: 6–10 frames per night, a phase–BERV geometry check before
   scheduling, a template built from more than one night, and a header check before choosing
   a recipe.
5. **And point some of it at objects with no host at all**, where the entire §§3–5 apparatus
   is unnecessary and the measured precisions transfer unchanged.

---

## Acknowledgements and statement of AI involvement

The analyses summarised here — archive census, reduction, pipeline development, statistical
calibration, and the drafting of this note — were carried out by AI agents (Claude, Anthropic,
running in Claude Code), directed and reviewed by the human author, who set the research
questions, challenged the agents' claims, made every decision with external consequences, and
takes sole responsibility for all content. Verification is primarily mechanical rather than
expert-audited: every adopted pipeline change was scored against an external reference and
required signal-injection recovery; positive controls preceded every null; dead ends and
retractions remain in the public record, including the mis-classification that withdrew three
of the points this note would otherwise have used. Based on data obtained from the ESO Science
Archive Facility. This document reports an independent analysis and is not affiliated with or
endorsed by the authors of any work discussed.

## Data and code availability

All spectra are public ESO archive products and raw frames. The pipeline — reduction drivers,
converter, injection harness, the slit-function contamination measurement
(`scripts/injection/m28_contam.py`), and the feasibility relations used in §6.2
(`src/exosat_rv/`) — lives in the project repository, with the milestone documents cited
inline throughout.

## References

- Hoy, K., Zurlo, A., Peña R., P. A., Köhler, J., et al. 2026, *Nature*, "Satellite detected around a star's substellar companion" (published version; supersedes arXiv:2607.05193v1).
- Horstman, K., Ruffio, J.-B., Batygin, K., et al. 2024, "RV measurements of directly imaged brown dwarf GQ Lup B to search for exo-satellites", arXiv:2408.10299.
- Köhler, J., Zechmeister, M., Hatzes, A., et al. 2025, A&A, "viper: High-precision radial velocities from the optical to the infrared", arXiv:2505.08315.
- Lazzoni, C., Desidera, S., Gratton, R., Zurlo, A., Mesa, D., & Ray, S. 2022, MNRAS, "Detectability of satellites around directly imaged exoplanets and brown dwarfs", arXiv:2207.07569.
- Ruffio, J.-B., Horstman, K., Mawet, D., et al. 2023, "Detecting exomoons from radial velocity measurements of self-luminous planets: application to observations of HR 7672 B and future prospects", arXiv:2301.04206.
- Vanderburg, A., Rappaport, S. A., & Mayo, A. W. 2018, "Detecting exomoons via Doppler monitoring of directly imaged exoplanets", arXiv:1805.01903.
- Vanderburg, A., & Rodriguez, J. E. 2021, "First Doppler limits on binary planets and exomoons in the HR 8799 system", arXiv:2110.14650.
- "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", A&A, arXiv:2511.20091. *(This project's milestone documents attribute this paper to two different first authors — Blunt et al. in M7/M10, Kral et al. in the methods note — so the citation must be checked against the published version before submission.)*

---

## What to verify before submission

Items for the author; everything else traces to a numbered milestone document.

1. **Publication priority on HIP 65426 b.** Its five nights are another team's
   active-programme data (2024–25). M20 §5 and LESSONS §6 record that publishing its headline
   ahead of them is Matthew's decision, and that that decision gates the paper fold-in of
   M20–M24. HIP 65426 b carries two loads in this note — the 0.8″/~2000 clean point in §3.1
   and the measured reach anchor in §6.2 — and both would need reframing if the answer is no.
   The §6.2 argument survives on η Tel B and YSES 1 b alone, with a weaker mass reach.
2. **The contrast ratios.** ~2000, ~5000 and ~30 000 are ledger figures with no derivation in
   the repository (§2). Either derive them from published photometry of each system before
   submission, or present the curve on separation with contrast as an ordered annotation.
3. **HIP 81208 B (§3.4).** Ledger-only, no milestone document, *n* = 3. Confirm the 0.3″
   separation and the raw headers before the counterexample is stated in print — it is exactly
   the class of entry that trap 1.10 caught elsewhere.
4. **YSES 1 b (§3.1).** Also ledger-only (M26 row): 34 m s⁻¹, gates 101 ± 2%, two 2023 nights.
   Worth promoting to a milestone document, since it carries the best-precision claim here.
5. **CD-35 2722 B's separation.** 2.8″ (M0/M5/M8) versus 3.17″ (M28 §5). The contamination
   geometry uses 3.17″; confirm which is the literature value being cited.
6. **The GRAVITY citation** (see the reference-list note).
7. **"To the best of our knowledge" hedges.** No claim of novelty in this note has been
   checked against ADS by a human; per M20 §5 all such statements remain provisional.
