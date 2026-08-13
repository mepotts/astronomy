# The contrast wall, bracketed: a two-axis feasibility constraint for slit-fed companion radial velocimetry — and the free-floating regime where it does not exist

*Matthew Potts · independent analysis · draft 2026-08-13*

*Instrument-oriented note. Target venue: A&A/MNRAS short paper or an instrument-design note. Written from milestones M7–M29 of the `exosat-rv` archival project; every number traces to a document in that repository and is cited inline as (M-n §s) or (queue) for the roster ledger `docs/target-queue.md`. Numbers that could not be sourced are omitted rather than estimated.*

---

## Abstract

Companion-side radial velocimetry — measuring the reflex motion of a directly imaged brown
dwarf or giant planet from its own spectrum, to detect a satellite or a second companion —
is normally proposed on a photon-noise argument: the companion's K magnitude sets the
achievable precision. That axis is incomplete. Running one injection-gated CRIRES+ pipeline
over eleven archival systems, we find the binding constraint is **host-star contamination in
the slit**, and that it changes the outcome discontinuously: the same pipeline delivers
34–190 m s⁻¹ per epoch on well-separated companions and km s⁻¹ on β Pic b, whose scatter is
locked to the barycentric correction at *r* = +0.88 and survives both a rebuilt template and
the masking of the responsible spectral order. We report where that transition lies and — the
main negative result — how poorly it is localised. Deriving the host:companion flux ratios
from photometry rather than asserting them, **clean is measured up to ~1900× (η Tel B at
4.2″, AB Pic b) and at 97× (CD-35 2722 B), while flooded is measured only at ~37 000×
(β Pic b at 0.55″): a factor-20 gap containing no observation.** Nor is contrast sufficient
alone — PDS 70 sits at an easy 460× and is unusable at 0.17″, where the extracted spectrum is
the star's — and this dataset never separates the two axes. At the wide end we bound the
contamination directly: on CD-35 2722 B the primary leaves **no detectable second trace in
the nodding slit function on any of 18 nights**, with per-night 3σ limits of 1–11% (median
2.5%). The failure has a signature — 99–100% injection transmission together with km s⁻¹
scatter — identifying it as a contamination systematic rather than a sensitivity limit, so
collecting area does not cure it; where it bites, the requirement is hardware spatial
filtering or an interferometric route. Finally, **isolated planetary-mass objects remove the
constraint by construction**, deleting every host-dependent term while keeping the young,
self-luminous K ≈ 12–15 spectra that make the technique work at all. On measured rather than
forecast precisions, five archival epochs at 131 m s⁻¹ excluded ≳0.4 M_Jup companions at
*P* ≤ 100 d around an 8 M_Jup host, and nothing in that chain used the host star. No suitable
multi-epoch archival data exist for isolated objects, so that case is a proposal, not a
result.

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
brightness differ by four orders of magnitude in delivered velocity scatter, and the
discriminant is how much of the host lands in the slit.

A second lesson concerns how such a constraint should be stated. This project quoted the wall
in contrast — clean at ~2000×, flooded at ~5000× — for several milestones before anyone
computed those ratios from magnitudes. Computed, they move by one to two orders of magnitude
(§2), and the constraint that survives is weaker, better defined, and not expressible on one
axis. We report it that way (§§2–5), then make the case that free-floating planetary-mass
objects are the regime in which it does not exist at all (§6).

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

Two rules constrain what we call a measurement.

**Nodding only.** Every dataset this project had classified as "staring-mode" turned out to
be **HiRISE**: fiber-fed SPHERE→CRIRES+ observations (`ESO INS MODE = HIRISE`, original files
`HIRISE_SPEC_OBS*`), reduced by us through a slit recipe. Three ledgered verdicts were
retracted (queue, HiRISE banner; LESSONS trap 1.10). Nodding conclusions stand; the fiber tier
is provisional pending a fiber-appropriate reduction and is quarantined in §3.4 — which
removes two of the four points that once anchored the harsh end.

**Contrast is derived, and it moved.** The flux ratios previously quoted for this wall
(~2000×, ~5000×, ~30 000×; M20 §6) were asserted, not computed. We derive them as
contrast = 10^(0.4 (m_comp − m_host)), with companion K magnitudes from M7's screen
(`data/m7-survey.json`) and host magnitudes from SIMBAD (M29 §6). They disagree by one to two
orders of magnitude: CD-35 2722 B, filed under "clean at ≥ 2000×", is **97×**, twenty times
easier than advertised; β Pic b, the flooded case quoted at ~5000×, is **36 983×**, seven
times harder. Both rest on well-measured 2MASS magnitudes of bright hosts, so these are not
marginal corrections. Three caveats travel with every derived value below:

- **Band mismatch.** Several campaigns observed in H1567, not K, and the companion's H−K
  colour differs from its host's, so a K-band ratio only approximates the contrast that
  applied at the slit.
- **Only six rows resolve** — CD-35 2722 B, AB Pic b, η Tel B, PDS 70 b and c (one host) and
  β Pic b. HIP 65426 b, HD 1160 B, AF Lep b, YSES 1 b, HIP 81208 B, HD 19467 B, HD 206893 B,
  CT Cha B and 2M0103AB b are absent from M7's table or unresolved at SIMBAD; those cells are
  left empty rather than estimated.
- **51 Eri b is excluded** on M7's own flag — its K = 21.0 is an upper limit, "unrankable".
  Propagating it would have manufactured a 3.8-million-× point, which is, in retrospect, how
  a "gone at ~30 000×" tier could have been defended.

Separations are literature values; CD-35 2722 B's is quoted as 2.8″ (M0, M5, M8, and the
derivation) and as 3.17″ in the slit-function geometry (M28 §5), and both are carried below
where they are used.

---

## 3. The constraint, as measured

### 3.1 The measured points (nodding)

| object | sep. | contrast (derived) | setting | epochs / span | per-epoch scatter | injection | outcome |
|---|---:|---:|---|---|---:|---|---|
| η Tel B | ~4.2″ | **1888×** | H1567 | 18 n / 815 d | **116–130 m s⁻¹** | 99–101 ± 1% | clean; first limit, *m* sin *i* ≳ 0.5–1.2 M_Jup, *P* = 20–300 d (M15) |
| CD-35 2722 B | 2.8″ | **97×** | H1567 | 18 n / 466 d | **70–90** (rms vs published) | 105 ± 4% | clean; H26's detection reproduces (M14) |
| AB Pic b | ≥ 2.7″ | **1768×** | K2166 | 2 n / 3 d | **120–190** | 97 ± 3 / 106 ± 8% | clean (M17) |
| CT Cha B | ≥ 2.7″ | not derived | K2166 | 3 n / 70 d | **180–310** | core orders 98–105%; edge orders unusable | clean of the host; limited by the companion's own accretion (M17, M23 §3) |
| YSES 1 b | 1.7″ | not derived | K2166 | 2 nights (2023 pair) | **34** | 101 ± 2% | clean; best quality of the campaign (queue) |
| HIP 65426 b | 0.8″ | not derived | K2192 | 5 n / 422 d | **131** | 98 ± 4 / 101 ± 3% | clean; ≳0.4 M_Jup excluded at *P* ≤ 100 d (M20 §4) |
| HIP 81208 B | 0.3″ (B9 host) | not derived | K2166 | 3 n / ~470 d | **124** | 99 ± 1% | clean — a counterexample on the separation axis (§3.5) |
| β Pic b | 0.55″ | **36 983×** | K2166 | 13 n / 813 d | **2466–4712** | 99–100% | **flooded**; no claim possible (M20 §2) |
| PDS 70 | 0.17″ | **460×** | K2166 | 6 n / 426 d | **130** | 99 ± 1–2% | companion unreachable at an easy contrast; the extracted spectrum is the *star's* (M20 §3) |

The clean entries are not merely "not obviously broken": η Tel B's 116–130 m s⁻¹ scatter is
fully accounted for by its own within-night measurement noise (M29; NEXT-DIRECTIONS §A1), and
CD-35 2722 B reproduces a published detection blind, through a barycentric covariate, at
*p* = 5×10⁻⁴ (M28 §§1–2).

### 3.2 Where the wall is, and how much of the plane was never sampled

On the contrast axis, the roster brackets the transition and does not locate it: **clean is
measured up to ~1900×** (η Tel B at 4.2″, AB Pic b) and at 97× (CD-35 2722 B); **flooded is
measured at ~37 000×** (β Pic b at 0.55″); and **between them lies a factor of ~20 containing
no observation.** The campaign never sampled the gap and we decline to interpolate across it —
a proposal at, say, 5000× cannot cite this work in either direction.

On the separation axis, contrast is demonstrably not sufficient. PDS 70's companions sit at an
*easy* **460×**, a quarter of η Tel B's clean contrast, and are unreachable at 0.17″ inside
the AO core, where the extracted spectrum is the star's (M20 §3). From the other side,
HIP 81208 B is clean at 124 m s⁻¹ at 0.3″ from a B9 host (§3.5). Separation limits the method
independently of contrast, and small separation does not by itself condemn a target.

The honest object is a **two-axis constraint**, and this dataset does not separate the axes:
the single flooded case is simultaneously the sample's highest contrast *and* one of its
smallest separations, so β Pic b cannot attribute its own failure. What the data support is a
joint statement — at ~37 000× and 0.55″ the measurement fails, at ≤ ~1900× and ≥ 2.7″ it
succeeds — plus three clean points at 1.7″, 0.8″ and 0.3″ whose contrasts do not resolve, and
the mechanism of §4, which is the part that generalises.

### 3.3 The contamination bound at the wide end, measured directly

At CD-35 2722 B's 3.17″ we can do better than inferring cleanliness from the velocities. The
nodding extraction swath spans the full slit — order height 179.8 px at 0.056″/px, i.e.
10.07″, sampled by a 512-point slit function at 0.0197″ per point — and the slit angle is
pinned at POSANG = 153.1° on all eighteen nights with a 6″ nod throw, so the primary falls a
fixed **161 points** from the companion trace in every frame of the campaign (M28 §5).

Measured there, **no primary peak is detected on any night**: median slit-function height at
the primary's offset, relative to the companion peak, 0.0006 against a local profile noise of
0.0072 — 0.1σ. Per-night 3σ upper bounds run **1–11%, median 2.5%**, consistent with and on
most nights tighter than H26's ~15% worst-night slit-viewer estimate. Two caveats: the profile
median is removed first, so this bounds a *resolved* second trace, not a smooth halo pedestal,
and complements the slit-viewer method rather than replacing it; and the one epoch our quality
screen rejects carries the largest ratio of the eighteen (0.019) at 2.0σ, on the campaign's
best seeing — contamination does not explain why that night is bad (M28 §5).

The useful form of this is a bracket on the quantity that actually matters, the fraction of
host light in the extracted spectrum rather than the flux ratio on the sky. At ≲ a few percent
the technique delivers 70–130 m s⁻¹ per epoch; at 0.55″ and ~37 000× unsuppressed it delivers
km s⁻¹. **No intermediate case has been measured in this quantity either**, so the tolerance
is stated only as: a few percent is empirically sufficient, and an unsuppressed halo at that
contrast and separation is fatal.

### 3.4 The provisional tier — excluded from the constraint

Three points originally reported as harsh-end wall measurements come from the mis-classified
fiber tier and are **withdrawn as slit measurements**; their numbers now bound *our
processing* rather than the sky:

| object | sep. | contrast | as originally reported | status |
|---|---:|---:|---|---|
| AF Lep b | 0.32″ | not derived | 68 ± 4% injection transmission (M23 §2) | **provisional** — HiRISE fiber data reduced through the slit recipe (queue banner) |
| 51 Eri b | 0.45″ | not derivable | 3 of 11 orders respond (M23 §2) | **provisional** — same error class; K = 21.0 is an upper limit (§2) |
| HD 1160 B | 0.78″ (A0 host) | not derived | 725 m s⁻¹, per-night errors ±37 to ±2600 (M23 §1) | **provisional** — verdict to be re-derived with fiber-appropriate handling |

Nothing in §§3.1–3.2 depends on them, and the "~30 000×" once attached to the first two rows
was never derived: AF Lep b's host magnitude does not resolve, and 51 Eri b's companion
magnitude is an upper limit that would have manufactured a 3.8-million-× point (§2). The two
costs compound. **The steep end now has neither a measured point nor a derived contrast** —
it rests on β Pic b alone rather than on four cases — so the regime beyond ~37 000×, and the
whole ≤ 0.5″ slit regime, is unmeasured here. Two fiber series did reduce well and hint at
what the suppressed route delivers, without being validated fiber reductions: HD 19467 B, a
45 m s⁻¹ pair at 101 ± 5%, and HD 206893's epochs at 100–102% (queue, M26 rows); a proper
HiRISE reduction path is open work (M27).

### 3.5 The counterexample on the separation axis

HIP 81208 B is recorded in the ledger as **0.3″ from a B9 host** with three K2166 nodding
nights that are flat and clean: 124 m s⁻¹, χ² = 1.1/2, gates 99 ± 1% (queue, M26 row). On a
separation-only reading that is impossible — it sits well inside β Pic b's 0.55″. On a contrast
reading it is simply a question, because the system does not resolve in the derivation (§2).

We flag it rather than explain it away. Three readings are open and the documentation cannot
choose between them: (i) the contrast is genuinely far lower than β Pic b's, a ~67 M_Jup
companion being intrinsically much brighter than a 12.8 M_Jup planet — which the derivation
would settle if the magnitudes resolved; (ii) β Pic b's failure is partly *spectroscopic*
rather than geometric, K2166 being centred on Br-γ, its host's dominant absorption feature,
130 km s⁻¹ wide (M20 §2); (iii) at *n* = 3, with only ledger-level documentation, the entry
may not survive the scrutiny the other rows have had.

Any of the three is worth having, and (ii) is directly actionable for setting choice. With
PDS 70 — clean contrast, unusable separation — this is the pair that forces the two-axis
statement of §3.2, and resolving either is the most valuable follow-up available: **two
magnitudes and an archive query would do more for the location of this wall than another
season of spectroscopy.**

---

## 4. What the failure actually is, and why software does not fix it

β Pic b is the one fully documented failure, and the mechanism is specific (M20 §2). Three
passes isolated it. A template reused from a single night gave 4712 m s⁻¹ of night scatter at
*r*(RV, BERV) = +0.94 — one night carries no barycentric lever with which to separate target
lines from telluric residue. Rebuilding the template across all 28 frames and 813 d halved the
scatter to 2466 m s⁻¹ and left *r* = +0.88: the residual is not the template. Masking the Br-γ
order and dropping six injection-unstable orders left *r* = **+0.88, unchanged**, with
transmission at 99–100% on the eleven surviving orders and every long-period peak dying under
a BERV covariate. Three consequences for instrument design follow:

1. **The contamination is pervasive, not surgical.** The starlight carries broad, low-level
   structure across the whole band; no order subset rescues the measurement, so masking is
   not a mitigation and neither is a redder or bluer setting on its own.
2. **It is a systematic, not a sensitivity limit.** The gates ran at 99–100% throughout: the
   pipeline was transmitting injected velocity essentially perfectly while returning km s⁻¹
   of host motion. **Collecting area does not help with this.** An ELT-class aperture improves
   the photon term, which was never the binding one; it also places a given contrast at a
   smaller angular separation, which if anything moves more targets inside the failure
   regime — wherever that regime's edge turns out to lie (§3.2).
3. **It has a cheap diagnostic signature, testable in advance**: high injection transmission,
   km s⁻¹ epoch scatter, a strong RV–BERV correlation, and candidate periodicities that vanish
   under a BERV covariate. Two independent reductions of β Pic b give ΔBIC −1.8 and −1.7 at
   the period where CD-35 2722 B gives +27.9 (M28 §1): no periodic content at all.

---

## 5. Where it bites: what has to be bought, and what is free

**Hardware.** The requirement is spatial filtering at the focal plane, before the
spectrograph — a single-mode fiber fed by an extreme-AO/coronagraphic front end (HiRISE at
the VLT, KPIC at Keck; RISTRETTO-class concepts in the same family), which is why the β Pic b
campaign is recorded as contamination-limited rather than as a null. The route is not
hypothetical here: the archive already holds **six public HiRISE nights of β Pic b (Oct–Dec
2024)**, a starlight-suppressed series of exactly the object the slit loses (queue banner).

**An interferometric alternative covers the same regime.** The VLTI/GRAVITY astrometric
exomoon search on HD 206893 B (arXiv:2511.20091) cuts its sample at K < 20 and contrast
< 10⁵; its prime target, β Pic b, has 28 GRAVITY nights over 2987 d in the archive — 1.6× the
epochs over 6.4× the baseline of the dataset behind the first RV detection (M10 §§1–2). At a
derived 36 983×, the one object our slit measurement loses sits comfortably inside that cut.
Astrometry and RV want the same targets and fail differently; here, astrometry is the route
with public data.

**Four things that cost nothing and are not being done**, which apply to every proposal in
the genre:

1. **Ask for 6–10 frames per night, not ~2.** Two leaves too few degrees of freedom to split
   epoch scatter into measurement noise and astrophysical jitter: attempted across ~11
   companions, the decomposition failed on power, with the built-in control — a target
   carrying a known several-hundred m s⁻¹ signal — resolving its own excess at 1.4σ (M29;
   NEXT-DIRECTIONS §A1). It costs no extra nights and converts a survey of upper limits into
   a measurement of the noise floor.
2. **Run the phase–BERV geometry check before the OB is written.** CD-35 2722 B's sampling
   correlates orbital phase with the barycentric correction at *r* = −0.71, which is why its
   amplitude stays confound-limited; η Tel B's leaves the 150–300 d decade clean, so a
   detection there would never have needed embargoed epochs to defend itself (M15 §1). Minutes
   of work, at scheduling time rather than analysis time.
3. **Never build a template from a single night** — no barycentric lever, and the artifact is
   at km s⁻¹ (LESSONS trap 6).
4. **Verify `INS MODE` and `ORIGFILE` before choosing a recipe.** Fiber data through a slit
   recipe produced km s⁻¹ artifacts we read as sky physics, and cost three retracted verdicts
   (LESSONS trap 1.10) — the reason §3.4 exists.

---

## 6. Free-floating planetary-mass objects: the regime with no wall

### 6.1 The argument is an identity, not an extrapolation

Every quantity in §§3–5 is defined relative to a host star: the contrast ratio, the halo that
floods the slit, the barycentric-locked stellar lines that dominate β Pic b, the position
angle pinned across eighteen nights to keep the primary off the trace, the AO performance on
which all of that depends, and the hardware bought to undo it. **For an isolated planetary-mass object every one of those terms is zero by construction,
not small** — and, usefully, there is then no need to know where the transition lies, which
is the weakest part of §3. For an isolated target that factor-20 uncertainty is not reduced,
it is irrelevant: what β Pic b's 36 983× against a naked-eye K = 3.48 host measures, an
isolated object does not have.

What is *unchanged* is what makes the measurement possible: a young, self-luminous object
radiating its own K ≈ 12–15 infrared spectrum, of the class this project measured eleven
times. The remaining ingredients — a telluric wavelength reference, a template built from the
target's own data, injection-gated transmission — are host-independent throughout.

### 6.2 The reach, from measured numbers

The strongest statement available is not a forecast. On HIP 65426 b, an ~8 M_Jup host,
**five archival epochs over 422 d at 131 m s⁻¹ excluded companions of ≳0.4 M_Jup (~115 M_⊕)
at *P* ≤ 100 d**, at injection transmission 98 ± 4% and 101 ± 3% (M20 §4). Nothing in that
chain used the host star; the target merely happened to be a companion, at 0.8″, on the clean
side of wherever the transition is.

The precisions behind such a limit — all injection-gated, all nodding — span **34–190 m s⁻¹**
(§3.1) on objects whose recorded K magnitudes run 12.0–15.1 (CD-35 2722 B 12.01, η Tel B 13.2,
β Pic b 14.9, AB Pic b 15.1; YSES 1 b's is not recorded here), with 162 m s⁻¹ measured
*within* a night on β Pic b at 100 ± 0% transmission in all 18 orders (M17 §§1–2) — subject to
that milestone's own caveat that within-night repeatability is not night-to-night systematics.

Scaling to isolated hosts uses the field's standard relation (Lazzoni et al. 2022 eq. 2, as
implemented in this repository). The estimator is deliberately crude — 3σ on one epoch, no
sampling term — so we calibrate it against the one injection-derived limit available: for an
8 M_Jup host at 131 m s⁻¹ it returns 0.36 M_Jup at *P* = 100 d against the measured 0.35–0.45,
**agreement to ~25% at *P* = 50–100 d**, while running optimistic by ~2× at 20 d and ~2–3× at
200–400 d, where sampling rather than per-epoch noise sets the limit. It also reproduces the
ledger's ~20–30 M_⊕ statement for YSES 1 b. Read within that band:

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
brown dwarfs dominating the current roster (M7 §5). Two further asymmetries follow from the
absence of a star rather than from optimism. **The satellite's stable zone is not truncated
from outside**: the stability limit this field uses is set by the host star's tidal field.
And **the one mechanism known to destroy the highest-amplitude satellites is inoperative** —
tidal spin-down of a giant planet *by its star* pushes corotation beyond the stability limit,
so every stable satellite ends up inside corotation and inspirals (M8 §§1–2); it requires a
star. Against that, the host mass is model-derived with no dynamical anchor, which enters
mildly: satellite mass scales as M_p^(1/2), so a 30% host-mass error is ~14% in the satellite
mass.

### 6.3 What we cannot claim, stated plainly

- **There is no archival result here.** The ESO archive was swept for isolated planetary-mass
  objects with multi-epoch CRIRES+ coverage; the answer was negative and exhaustive (queue
  banner, idea #4). This section is a proposal case.
- **Brightness is the binding cut, and it bites below K ≈ 15**, where Lazzoni et al. flag
  that their flux scaling degrades faster than 1.585×/mag as background takes over (M7 §1).
  Every precision in §3.1 was achieved at K = 12.0–15.1; fainter targets are outside the
  regime this project has measured, and we claim nothing about them.
- **We have run no population census.** How many isolated objects are bright and young enough
  is a literature question we have not done, and we do not assert an answer.
- **Acquisition and wavefront sensing are the unquantified operational cost.** A target with
  no bright neighbour must be acquired and guided on its own flux; we have no measurement
  bearing on this and flag it as the item a proposal must address.
- **Nothing here is an exomoon-detection argument.** The population study underlying this
  field expects RV to reach binary-like satellites (mass ratio ≳ 0.01), not solar-system
  analogues (M7 §1), and the only claimed detection sits at that ratio. Removing the wall
  improves the noise, not the occurrence rate.

---

## 7. Summary for a proposal

1. **Lead with contrast, not magnitude — and derive it.** Similarly bright companions here
   differ by four orders of magnitude in delivered scatter (§3.1), and the ratios this project
   quoted for several milestones were wrong by one to two orders of magnitude once computed
   (§2). Two catalogue magnitudes precede any feasibility argument.
2. **Do not read a threshold out of this work.** Clean to ~1900×, flooded at ~37 000×, nothing
   between; separation limits the method independently (PDS 70 at 460×, unusable at 0.17″);
   the two axes are not separated here (§3.2). Targets in the gap are unaddressed.
3. **Bound the contamination, do not assume it.** The nodding slit function measures it
   directly: at 3.17″, no resolved primary trace on any of 18 nights, 3σ limits 1–11% per
   night. A few percent is empirically sufficient for 70–130 m s⁻¹.
4. **Where it does bite, buy suppression or use interferometry** — the failure is a systematic
   at 99–100% transmission, so aperture does not cure it. Public HiRISE nights on β Pic b
   exist, and GRAVITY holds 28 nights over 2987 d on it, inside its own contrast cut.
5. **Spend the free levers**: 6–10 frames per night, a phase–BERV check before scheduling, a
   template from more than one night, a header check before choosing a recipe.
6. **And point some of it at objects with no host at all**, where the entire §§3–5 apparatus
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
   M20–M24. HIP 65426 b carries two loads here — the clean 0.8″ point in §3.1 and the measured
   reach anchor in §6.2 — and both would need reframing if the answer is no. The §6.2 argument
   survives on η Tel B and YSES 1 b alone, with a weaker mass reach. Note that HIP 65426 b no
   longer carries a contrast coordinate either way (§2), so it is now a separation-axis point
   only.
2. **The derived contrasts (§2, M29 §6).** The derivation replaced the asserted figures, and
   three things about it should be checked by hand before print: (a) the SIMBAD host
   magnitudes and their 2MASS provenance for CD-35 2722, bet Pic, eta Tel, AB Pic and PDS 70;
   (b) the **band mismatch** — CD-35 2722 B and η Tel B were observed in H1567, so their
   K-band ratios approximate the contrast that applied at the slit, and an H-band ratio
   computed from published companion H photometry would be the correct number for those two
   rows; (c) that no cell was filled by estimation. Nine systems do not resolve and are left
   blank on purpose.
3. **51 Eri b's exclusion (§2, §3.4).** Confirm the K = 21.0 entry in M7's table really is an
   upper limit. The exclusion is load-bearing: including it would produce a 3.8-million-×
   point and would appear to support the old "~30 000×" tier.
4. **HIP 81208 B (§3.5).** Ledger-only, no milestone document, *n* = 3. Confirm the 0.3″
   separation and the raw headers before the counterexample is stated in print — it is exactly
   the class of entry that trap 1.10 caught elsewhere. Its host and companion magnitudes would
   also convert it from an anomaly into a data point.
5. **YSES 1 b (§3.1).** Also ledger-only (M26 row): 34 m s⁻¹, gates 101 ± 2%, two 2023 nights.
   Worth promoting to a milestone document, since it carries the best-precision claim here.
6. **CD-35 2722 B's separation.** 2.8″ (M0/M5/M8, and the contrast derivation) versus 3.17″
   (M28 §5, the slit-function geometry). Both are used, in the places they were measured;
   confirm which is the literature value being cited.
7. **The GRAVITY citation** (see the reference-list note).
8. **"To the best of our knowledge" hedges.** No claim of novelty in this note has been
   checked against ADS by a human; per M20 §5 all such statements remain provisional.
