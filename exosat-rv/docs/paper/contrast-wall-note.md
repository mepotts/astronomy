# The wall is not a contrast wall: scattered host flux as a one-parameter feasibility criterion for companion-side radial velocimetry — and the free-floating regime where it vanishes

*Matthew Potts · independent analysis · draft 2026-08-13*

*Instrument-oriented note. Target venue: A&A/MNRAS short paper or an instrument-design note. Written from milestones M7–M29 of the `exosat-rv` archival project; every measured number traces to a milestone document, cited inline as (M-n §s) or (queue) for the roster ledger, and every separation and contrast traces to a primary source, cited by author. Quantities that could not be sourced are marked, not estimated.*

---

## Abstract

Companion-side radial velocimetry — measuring the reflex motion of a directly imaged brown
dwarf or giant planet from its own spectrum, to detect a satellite or a second companion — is
normally proposed on a photon-noise argument: the companion's K magnitude sets the achievable
precision. That axis is incomplete. Running one injection-gated CRIRES+ pipeline over eleven
archival systems, we find the binding constraint is **host-star contamination in the slit**,
and that it switches the outcome discontinuously: the same pipeline delivers 34–190 m s⁻¹ per
epoch on some companions and km s⁻¹ on β Pic b, whose scatter is locked to the barycentric
correction at *r* = +0.88 and survives both a rebuilt template and the masking of the
responsible spectral order, at 99–100% injection transmission throughout. With every
separation and contrast traced to a primary source, **neither axis orders the outcomes**: by
contrast the sequence reads clean, fails, clean, clean, fails, clean; by separation, fails,
clean, fails, clean, clean, clean. The decisive pair is YSES 1 b, clean at 34 m s⁻¹ from 1.70″
at a contrast of 10 280, against β Pic b, flooded at 0.51″ and 3950. What does order them is the physically motivated combination
**S = contrast / θⁿ** — the ratio of scattered host flux to companion flux at the slit, since
a seeing- or AO-limited halo wing falls as θ⁻² to θ⁻³. The exponent was chosen from the
physics and then scanned, not fitted: S separates the two classes for *n* = 1.5–4.0, most
cleanly at *n* = 2, with four clean cases at S = 12, 107, 3557 and 4327 against two failures
at 15 202 and 15 917. Applied to 31 catalogued companions with thresholds fixed in advance,
four predictions agree and none disagree — but only two systems were genuinely held out,
both clean and 50–100× below the threshold, and there is no held-out failure case at all.
**S is therefore consistent with every outcome measured here and is not yet tested by any of
them**; the informative interval, 4327 < S < 15 202, has never been observed, by us or by
anyone. Three falsifiable predictions are placed on the record. Finally, isolated
planetary-mass objects have no host and hence no scattered host flux: S is identically zero,
and the entire criterion is vacuous for them.

---

## 1. Introduction

Doppler monitoring of a directly imaged companion was proposed by Vanderburg et al. (2018),
applied to HR 8799 by Vanderburg & Rodriguez (2021) and to HR 7672 B by Ruffio et al. (2023),
forecast for the CRIRES+ era by Lazzoni et al. (2022), and pursued by Horstman et al. (2024)
on GQ Lup B. Hoy et al. (2026, hereafter H26) reported the first detection, in CD-35 2722 B.

Proposals in this genre are written on a single feasibility axis: how bright the companion
is. Lazzoni et al.'s threshold is a pure flux scaling — 100 m s⁻¹ at K = 13.5, degrading
1.585× per magnitude (M7 §1) — and this project's own ranking used the same form, re-anchored
on H26's achieved 31.44 m s⁻¹ at K = 12.01 (M7 §2). Having run one pipeline across eleven
systems from 0.17″ to 4.21″ of host separation, we can say the flux axis is the wrong one to
lead with: companions of similar brightness differ by four orders of magnitude in delivered
velocity scatter, and the discriminant is how much of the host lands in the slit.

Saying *which* companions is harder than it looks, and the history is worth one paragraph
because it is the reason this note exists in its present form. This project asserted a
"contrast wall" — clean at ~2000×, flooded at ~5000× — for several milestones without ever
computing those ratios. Computing them moved some by an order of magnitude and, on one
target, produced a value that a primary source later contradicted by 2.4 mag. Only when every
point had been traced to its discovery photometry did the useful fact appear: contrast does
not order the outcomes, separation does not order them either, and a specific combination of
the two does (§5). The measurements themselves never moved. What moved was the variable they
were being plotted against.

---

## 2. Provenance, and the rules that govern what counts

All spectra are public ESO archive holdings. RVs are extracted with `viper` (Köhler et al.
2025) in gas-cell-free CRIRES+ mode, forward-modelling each order against a telluric-free
template built from the target's own observations; reductions use `cr2res` 1.6.10, from raw
frames where required, and reproduce ESO's archived products to 42 m s⁻¹ in the final RV
(M12 §9b). No published RV truth exists off CD-35 2722 B, so **signal injection carries the
entire validation burden**: every series below had to transmit an injected Keplerian —
imposed by shifting the template, never the observation — at both a loud and an
amplitude-matched semi-amplitude (M12 §8.1, M20 §1). Transmission is quoted throughout,
because a series that transmits nothing is always quiet (M23 §4).

**Nodding only.** Every dataset this project had classified as "staring-mode" turned out to
be **HiRISE**: fiber-fed SPHERE→CRIRES+ observations (`ESO INS MODE = HIRISE`, original files
`HIRISE_SPEC_OBS*`), reduced by us through a slit recipe. Three ledgered verdicts were
retracted (queue, HiRISE banner; LESSONS trap 1.10). Nodding conclusions stand; the fiber
tier is provisional pending a fiber-appropriate reduction and is quarantined in §3.4.

**Separations and contrasts come from primary sources, or are marked.** Two things had to be
fixed before any axis could be tested. First, the separations quoted throughout this project
were unsourced, while Lazzoni et al.'s Table 1 carries a `Sep` column in mas and the host K
magnitude for 37 companions — columns that sat unread in this repository for its whole
duration. Read off it, β Pic b is at **0.511″, not the 0.55″** carried everywhere here,
51 Eri b at 0.434″, AB Pic b at 5.40″, η Tel B at 4.21″, PDS 70 b at 0.1735″, CT Cha b at
2.68″. Second, that table's companion-magnitude column is apparent magnitude — validated on
YSES 1 b against Bohn et al. (2020) to **0.14 mag** — but **not uniformly reliable**: for
β Pic b it gives K = 14.9, where Currie et al. (2013, Gemini/NICI, the source Bonnefoy et al.
2014 cite for that object's K_s photometry) measure **K_s = 12.47 ± 0.13**, giving a contrast
of **≈ 3950×, not 36 983×**, against the host's K = 3.48. A primary source overrides the
column; rows resting on the column alone are marked.

Two caveats travel with every contrast below. **Band mismatch:** several campaigns observed
in H1567, not K, and a companion's H−K colour differs from its host's, so a K-band ratio
approximates the ratio that applied at the slit. **η Tel B is disputed:** Lazzoni's K = 13.2
against SIMBAD's H = 11.93 implies H−K = −1.27, the wrong sign for a late-M/L dwarf; one of
the two is mislabelled, and the discovery photometry (Langlois et al. 2021) would settle it.
η Tel B is a clean case at wide separation and is not load-bearing for anything below.

---

## 3. The measurements

### 3.1 The outcomes, with every point sourced

| system | sep. | contrast | S = C/θ² | setting | epochs / span | per-epoch scatter | injection | outcome |
|---|---:|---:|---:|---|---|---:|---|---|
| η Tel B | 4.21″ | 1888× | 107 | H1567 | 18 n / 815 d | **116–130 m s⁻¹** | 99–101 ± 1% | clean; limit *m* sin *i* ≳ 0.5–1.2 M_Jup, *P* = 20–300 d (M15) |
| CD-35 2722 B | 2.80″ | 97× | 12 | H1567 | 18 n / 466 d | **70–90** (rms vs published) | 105 ± 4% | clean; H26's detection reproduces (M14) |
| YSES 1 b | 1.70″ | 10 280× | 3557 | K2166 | 2 nights (2023 pair) | **34** | 101 ± 2% | clean; best precision of the campaign (queue) |
| HIP 81208 B | 0.325″ | 457× | 4327 | K2166 | 3 n / ~470 d | **124** | 99 ± 1% | clean (queue, M26 row) |
| β Pic b | 0.511″ | 3950× | 15 202 | K2166 | 13 n / 813 d | **2466–4712** | 99–100% | **flooded**; no claim possible (M20 §2) |
| PDS 70 b | 0.1735″ | 460× | 15 917 | K2166 | 6 n / 426 d | **130** (the star) | 99 ± 1–2% | **companion unreachable**; the extracted spectrum is the star's (M20 §3) |

Sources: separations and contrasts as in §2 — Viswanath et al. (2023) for HIP 81208 B
(320.9 and 328.7 mas over two epochs, K2 Δmag 6.64), Bohn et al. (2020) for YSES 1 b (K1
Δmag 10.03), Currie et al. (2013) for β Pic b, Lazzoni et al. (2022) Table 1 with a verified
host K for CD-35 2722 B, η Tel B and PDS 70 b. Three further clean series carry precisions
but no placeable contrast and are therefore absent from any axis test: HIP 65426 b (0.8″,
131 m s⁻¹, 98 ± 4 / 101 ± 3%, ≳0.4 M_Jup excluded at *P* ≤ 100 d; M20 §4), AB Pic b (5.40″,
120–190 m s⁻¹; M17) and CT Cha b (2.68″, 180–310 m s⁻¹, usable only after an injection-based
order screen because of its own accretion; M17, M23 §3) — the latter two do have catalogue
contrasts and reappear as held-out tests in §5.4. The clean entries are not merely "not
obviously broken": η Tel B's scatter is fully accounted for by its own within-night
measurement noise (M29; NEXT-DIRECTIONS §A1), and CD-35 2722 B reproduces a published
detection blind, through a barycentric covariate, at *p* = 5×10⁻⁴ (M28 §§1–2).

### 3.2 Neither axis orders the outcomes

| axis, ascending | sequence | orders the outcomes? |
|---|---|---|
| contrast | C C **F** C **F** C | no |
| separation | **F** C **F** C C C | no |

The decisive pair is YSES 1 b against β Pic b: **YSES 1 b extracts cleanly, at the best
per-epoch precision of the whole campaign, at a contrast 2.6× harder than β Pic b's, because
it sits 3.3× further out.** No contrast threshold survives that. Separation alone fails from
the other side: HIP 81208 B is clean at 0.325″ while β Pic b floods at 0.511″.

So the "contrast wall" this project has been quoting since M20 is not merely mis-located, it
is the wrong variable — and so is the obvious alternative.

### 3.3 The contamination bound at the wide end, measured directly

At CD-35 2722 B's 3.17″ (the slit-function geometry of M28 §5; the same object's literature
separation is 2.8″) we can do better than inferring cleanliness from the velocities. The
nodding extraction swath spans the full slit — order height 179.8 px at 0.056″/px, i.e.
10.07″, sampled by a 512-point slit function at 0.0197″ per point — and the slit angle is
pinned at POSANG = 153.1° on all eighteen nights with a 6″ nod throw, so the primary falls a
fixed **161 points** from the companion trace in every frame of the campaign.

Measured there, **no primary peak is detected on any night**: median slit-function height at
the primary's offset, relative to the companion peak, 0.0006 against a local profile noise of
0.0072 — 0.1σ. Per-night 3σ upper bounds run **1–11%, median 2.5%**, consistent with and on
most nights tighter than H26's ~15% worst-night slit-viewer estimate. Two caveats: the profile
median is removed first, so this bounds a *resolved* second trace, not a smooth halo pedestal,
and complements the slit-viewer method rather than replacing it; and the one epoch our quality
screen rejects carries the largest ratio of the eighteen (0.019) at 2.0σ, on the campaign's
best seeing — contamination does not explain why that night is bad (M28 §5).

This is the only direct measurement of the contaminating flux in the series, and it is at the
easy end. Expressed as the fraction of host light in the extracted spectrum, ≲ a few percent
accompanies 70–130 m s⁻¹ per epoch. Nothing intermediate has been measured in that quantity
either.

### 3.4 The provisional tier — excluded

Three points originally reported as harsh-end measurements come from the mis-classified fiber
tier and are **withdrawn as slit measurements**; their numbers bound *our processing* rather
than the sky:

| system | sep. | as originally reported | status |
|---|---:|---|---|
| AF Lep b | 0.32″ | 68 ± 4% injection transmission (M23 §2) | **provisional** — HiRISE fiber data reduced through the slit recipe (queue banner) |
| 51 Eri b | 0.434″ | 3 of 11 orders respond (M23 §2) | **provisional** — same error class; and its catalogue magnitude is an upper limit, so it cannot be placed on any contrast axis |
| HD 1160 B | 0.78″ (A0 host) | 725 m s⁻¹, per-night errors ±37 to ±2600 (M23 §1) | **provisional** — verdict to be re-derived with fiber-appropriate handling |

Two fiber series did reduce well and hint at what the suppressed route delivers, without being
validated fiber reductions: HD 19467 B, a 45 m s⁻¹ pair at 101 ± 5%, and HD 206893's epochs at
100–102% (queue, M26 rows). A proper HiRISE reduction path is open work (M27).

---

## 4. What the failure is, and why software does not fix it

β Pic b is the one fully documented failure, and the mechanism is specific (M20 §2). Three
passes isolated it. A template reused from a single night gave 4712 m s⁻¹ of night scatter at
*r*(RV, BERV) = +0.94 — one night carries no barycentric lever with which to separate target
lines from telluric residue. Rebuilding the template across all 28 frames and 813 d halved the
scatter to 2466 m s⁻¹ and left *r* = +0.88: the residual is not the template. Masking the Br-γ
order and dropping six injection-unstable orders left *r* = **+0.88, unchanged**, with
transmission at 99–100% on the eleven surviving orders and every long-period peak dying under
a BERV covariate. Three consequences follow, and they are what motivates §5:

1. **The contamination is pervasive, not surgical.** The starlight carries broad, low-level
   structure across the whole band; no order subset rescues the measurement, so masking is not
   a mitigation and neither is a redder or bluer setting on its own. It behaves like light
   entering an aperture, not like a line-blending problem.
2. **It is a systematic, not a sensitivity limit.** The gates ran at 99–100% throughout: the
   pipeline was transmitting injected velocity essentially perfectly while returning km s⁻¹ of
   host motion. **Collecting area does not help with this.** An ELT-class aperture improves the
   photon term, which was never the binding one; it also places a given contrast at a smaller
   angular separation, which moves targets the wrong way on the axis of §5.
3. **It has a cheap diagnostic signature, testable in advance**: high injection transmission,
   km s⁻¹ epoch scatter, a strong RV–BERV correlation, and candidate periodicities that vanish
   under a BERV covariate. Two independent reductions of β Pic b give ΔBIC −1.8 and −1.7 at the
   period where CD-35 2722 B gives +27.9 (M28 §1): no periodic content at all.

---

## 5. S = contrast / θ²: the quantity that does order them

### 5.1 The quantity, and why the exponent is not free

What floods the slit is not the magnitude ratio between host and companion. It is the host's
light *scattered to the companion's position*, which is the contrast times the PSF halo
evaluated at the separation. For a seeing- or AO-limited halo the wing falls roughly as θ⁻² to
θ⁻³, so the natural quantity is

    S = contrast / θⁿ,   n ≈ 2–3

which is, to a constant, the **ratio of scattered host flux to companion flux at the slit** —
the physical quantity the mechanism of §4 says should matter. With six points and two classes,
many statistics will separate the set by chance, so the exponent was fixed by that argument
and then scanned across its plausible range, with the whole range reported
(`scripts/m29_wallaxis.py`):

| *n* | highest CLEAN | lowest FAILS | gap | separates |
|---:|---:|---:|---:|---|
| 1.0 | 6047 | 2706 | — | no |
| **2.0** | **4327** | **15 202** | **3.5×** | **yes** |
| 3.0 | 13 313 | 29 808 | 2.2× | yes |
| 4.0 | 40 962 | 58 446 | 1.4× | yes |

S separates the two classes for *n* = 1.5–4.0 and most cleanly at *n* = 2 — inside the falloff
a halo actually has. At *n* = 2:

| S | outcome | system |
|---:|---|---|
| 12 | clean, 70–90 m s⁻¹ | CD-35 2722 B |
| 107 | clean, 116–130 | η Tel B |
| 3 557 | clean, 34 | YSES 1 b |
| 4 327 | clean, 124 | HIP 81208 B |
| 15 202 | **fails** | β Pic b |
| 15 917 | **fails** | PDS 70 b |

### 5.2 What survives dropping the weak points

Two of the six can be challenged. **PDS 70 b may fail for a different reason**: at 0.1735″ the
companion is inside the AO core, where the host is not a halo but the spectrum itself. **η Tel
B's contrast is disputed** (§2). Both are droppable: removing either, or both, still leaves
clean cases at S = 12 and 3557 against a failure at 15 202. The separation is not carried by a
single point — but with one failure left it is carried by a single *class boundary*, which is
the real limitation and is the subject of §5.3.

The appeal, if it survives testing, is that S costs two catalogue numbers: a separation in
mas and a companion–host magnitude difference give it before a single frame is reduced, on any
archival companion with published photometry, and it is directly evaluable for HiRISE/KPIC and
ELT/ANDES target lists.

### 5.3 The test on held-out systems, and why it barely counts

`scripts/m29_wallpredict.py` parses 31 of Lazzoni et al.'s 37 companions and applies S with
the thresholds **fixed in advance** from the construction set — CLEAN below 4327, FAILS above
15 202, anything between recorded as indeterminate rather than assigned to whichever side
looks better. Where a primary source exists it overrides the catalogue column.

| system | sep. | contrast | S | predicted | observed | role |
|---|---:|---:|---:|---|---|---|
| GSC 6214-210 B | 2.21″ | 182× | 37 | clean | *no data* | held out |
| CT Cha b | 2.68″ | 285× | 40 | clean | **clean** | **held out ✓** |
| DH Tau B | 2.35″ | 224× | 41 | clean | *no data* | held out |
| AB Pic b | 5.40″ | 1768× | 61 | clean | **clean** | **held out ✓** |
| η Tel B | 4.21″ | 1888× | 107 | clean | clean | built-on |
| 1RXS J1609 b | 2.22″ | 1562× | 318 | clean | *no data* | held out |
| PDS 70 b | 0.1735″ | 460× | 15 297 | fails | fails | built-on |
| β Pic b | 0.511″ | 3950× | 15 154 | *indeterminate* | fails | built-on |

(S values here differ by a few percent from §5.1's for the two built-on failures, because the
prediction script uses the catalogue separation at full precision.)

**Four agree, none disagree — and it barely counts.** Three reasons, and the script prints
them in its own output rather than leaving them to this paragraph:

1. **Only two systems were genuinely held out**, CT Cha b and AB Pic b, both CLEAN, both
   sitting 50–100× *below* the clean threshold. Predicting "clean" two orders of magnitude
   inside the boundary does not discriminate between S and almost any monotone alternative.
2. **There is no held-out failure case at all.** S has never been asked to predict a failure
   it did not already know about.
3. **β Pic b lands essentially on the threshold** — 15 154 against a FAILS floor of 15 202 set
   by β Pic b itself, so the criterion returns *indeterminate* for the very object that
   defines the boundary. With PDS 70 b at 15 297, the failure side rests on two points about
   1% apart, one of which may fail by a different mechanism.

**The honest statement, which this note carries rather than buries: S is consistent with every
outcome measured in this project and is not yet tested by any of them.**

### 5.4 The interval nobody has observed, and three predictions on the record

The informative experiment needs a target with **4327 < S < 15 202** — and nothing has been
observed there, by this project or, as far as we can tell after a literature search, by
anyone. That gap is not new: it is the same unsampled transition that appeared when the
constraint was stated in contrast and again when it was stated in separation. Whatever
variable is used, this campaign never sampled the boundary.

Three systems have archival data and no reduction here, and their predictions are placed on
the record before the fact, since predictions made in advance are the only thing separating
this from curve-fitting:

| system | S | prediction |
|---|---:|---|
| GSC 6214-210 B | 37 | **clean** |
| DH Tau B | 41 | **clean** |
| 1RXS J160929.1-210524 b | 318 | **clean** |

All three are weak tests, for the reason given above — they sit far below the threshold. A
single target between 4327 and 15 202 would be worth more than all of them together.

---

## 6. What to do about it

**Where S is large, buy suppression or use interferometry.** The requirement is spatial
filtering at the focal plane, before the spectrograph — a single-mode fiber fed by an
extreme-AO/coronagraphic front end (HiRISE at the VLT, KPIC at Keck; RISTRETTO-class concepts
in the same family), which is why the β Pic b campaign is recorded as contamination-limited
rather than as a null. The route is not hypothetical here: the archive already holds **six
public HiRISE nights of β Pic b (Oct–Dec 2024)**, a starlight-suppressed series of exactly the
object the slit loses (queue banner). The interferometric alternative covers the same regime —
the VLTI/GRAVITY astrometric exomoon search on HD 206893 B (arXiv:2511.20091) cuts its sample
at K < 20 and contrast < 10⁵, and its prime target, β Pic b, has 28 GRAVITY nights over 2987 d
in the archive, 1.6× the epochs over 6.4× the baseline of the dataset behind the first RV
detection (M10 §§1–2).

**Four things that cost nothing and are not being done**, which apply to every proposal in the
genre:

1. **Ask for 6–10 frames per night, not ~2.** Two leaves too few degrees of freedom to split
   epoch scatter into measurement noise and astrophysical jitter: attempted across ~11
   companions, the decomposition failed on power, with the built-in control — a target carrying
   a known several-hundred m s⁻¹ signal — resolving its own excess at 1.4σ (M29;
   NEXT-DIRECTIONS §A1). It costs no extra nights and converts a survey of upper limits into a
   measurement of the noise floor.
2. **Run the phase–BERV geometry check before the OB is written.** CD-35 2722 B's sampling
   correlates orbital phase with the barycentric correction at *r* = −0.71, which is why its
   amplitude stays confound-limited; η Tel B's leaves the 150–300 d decade clean (M15 §1).
   Minutes of work, at scheduling time rather than analysis time.
3. **Never build a template from a single night** — no barycentric lever, and the artifact is
   at km s⁻¹ (LESSONS trap 6).
4. **Verify `INS MODE` and `ORIGFILE` before choosing a recipe.** Fiber data through a slit
   recipe produced km s⁻¹ artifacts we read as sky physics, and cost three retracted verdicts
   (LESSONS trap 1.10) — the reason §3.4 exists.

---

## 7. Free-floating planetary-mass objects: S = 0

### 7.1 The argument is an identity, not an extrapolation

Every quantity in §§3–6 is defined relative to a host star: the contrast, the halo scattered
to the companion's position, the barycentric-locked stellar lines that dominate β Pic b, the
slit angle pinned across eighteen nights to keep the primary off the trace, the AO performance
on which all of it depends, and the hardware bought to undo it. **For an isolated
planetary-mass object the numerator of S is zero.** The criterion of §5 is not merely small
for such a target; it is undefined, and every failure mode this project measured requires a
star to produce it.

That matters more than it would if S were well determined. The weakest part of this note is
the location of the boundary — a threshold interval that has never been observed (§5.4). For
an isolated target that uncertainty is not reduced but *irrelevant*: what β Pic b's 3950×
against a naked-eye K = 3.48 host produces, an isolated object does not have at any
separation, and no proposal for one needs to know where the boundary lies.

What is *unchanged* is what makes the measurement possible: a young, self-luminous object
radiating its own K ≈ 12–15 infrared spectrum, of the class this project measured eleven
times. The remaining ingredients — a telluric wavelength reference, a template built from the
target's own data, injection-gated transmission — are host-independent throughout.

### 7.2 The reach, from measured numbers

The strongest statement available is not a forecast. On HIP 65426 b, an ~8 M_Jup host, **five
archival epochs over 422 d at 131 m s⁻¹ excluded companions of ≳0.4 M_Jup (~115 M_⊕) at
*P* ≤ 100 d**, at injection transmission 98 ± 4% and 101 ± 3% (M20 §4). Nothing in that chain
used the host star. The precisions behind such a limit — all injection-gated, all nodding —
span **34–190 m s⁻¹** (§3.1) on objects whose recorded K magnitudes run 12.0–15.1, with
162 m s⁻¹ measured *within* a night on β Pic b at 100 ± 0% transmission in all 18 orders
(M17 §§1–2), subject to that milestone's caveat that within-night repeatability is not
night-to-night systematics.

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
project's implementation of the standard relation; ranking-grade, calibrated as above, and not
a substitute for an injection-derived limit.*

The lighter host helps: at fixed satellite mass and orbit the reflex amplitude scales as
M_p^(−1/2), so a 5–13 M_Jup isolated object is a *better* wobble target than the 37–47 M_Jup
brown dwarfs dominating the current roster (M7 §5). Two further asymmetries follow from the
absence of a star rather than from optimism. **The satellite's stable zone is not truncated
from outside**: the stability limit this field uses is set by the host star's tidal field. And
**the one mechanism known to destroy the highest-amplitude satellites is inoperative** — tidal
spin-down of a giant planet *by its star* pushes corotation beyond the stability limit, so
every stable satellite ends up inside corotation and inspirals (M8 §§1–2); it requires a star.
Against that, the host mass is model-derived with no dynamical anchor, which enters mildly:
satellite mass scales as M_p^(1/2), so a 30% host-mass error is ~14% in the satellite mass.

### 7.3 What we cannot claim, stated plainly

- **There is no archival result here.** The ESO archive was swept for isolated planetary-mass
  objects with multi-epoch CRIRES+ coverage; the answer was negative and exhaustive (queue
  banner, idea #4). This section is a proposal case.
- **Brightness is the binding cut, and it bites below K ≈ 15**, where Lazzoni et al. flag that
  their flux scaling degrades faster than 1.585×/mag as background takes over (M7 §1). Every
  precision in §3.1 was achieved at K = 12.0–15.1; fainter targets are outside the regime this
  project has measured, and we claim nothing about them.
- **We have run no population census.** How many isolated objects are bright and young enough
  is a literature question we have not done.
- **Acquisition and wavefront sensing are the unquantified operational cost.** A target with no
  bright neighbour must be acquired and guided on its own flux; we have no measurement bearing
  on this and flag it as the item a proposal must address.
- **Nothing here is an exomoon-detection argument.** The population study underlying this field
  expects RV to reach binary-like satellites (mass ratio ≳ 0.01), not solar-system analogues
  (M7 §1), and the only claimed detection sits at that ratio. Removing the scattered-light term
  improves the noise, not the occurrence rate.

---

## 8. Summary for a proposal

1. **Compute S = contrast/θ² before anything else.** Two catalogue numbers. On this project's
   six sourced systems it orders the outcomes where neither contrast nor separation does.
2. **Treat the threshold as unmeasured.** Clean is observed to S = 4327 and failure from
   S = 15 202; between them nothing has ever been observed, and the failure side rests on two
   points 1% apart, one of which may fail by a different mechanism. S is consistent with
   everything measured here and tested by none of it.
3. **Where S is large, buy suppression or use interferometry** — the failure is a systematic
   at 99–100% injection transmission, so aperture does not cure it. Public HiRISE nights on
   β Pic b exist, and GRAVITY holds 28 nights over 2987 d on the same object.
4. **Bound the contamination rather than assuming it.** The nodding slit function measures it
   directly: at 3.17″, no resolved primary trace on any of 18 nights, 3σ limits 1–11% per night.
5. **Spend the free levers**: 6–10 frames per night, a phase–BERV check before scheduling, a
   template from more than one night, a header check before choosing a recipe.
6. **And point some of it at objects with no host at all**, where S is identically zero and the
   measured precisions transfer unchanged.

---

## Acknowledgements and statement of AI involvement

The analyses summarised here — archive census, reduction, pipeline development, statistical
calibration, the sourcing audit, and the drafting of this note — were carried out by AI agents
(Claude, Anthropic, running in Claude Code), directed and reviewed by the human author, who
set the research questions, challenged the agents' claims, made every decision with external
consequences, and takes sole responsibility for all content. Verification is primarily
mechanical rather than expert-audited: every adopted pipeline change was scored against an
external reference and required signal-injection recovery; positive controls preceded every
null; dead ends, retractions and the two superseded framings of this note's central axis
remain in the public record. Based on data obtained from the ESO Science Archive Facility.
This document reports an independent analysis and is not affiliated with or endorsed by the
authors of any work discussed.

## Data and code availability

All spectra are public ESO archive products and raw frames. The pipeline — reduction drivers,
converter, injection harness, the slit-function contamination measurement
(`scripts/injection/m28_contam.py`), the axis test (`scripts/m29_wallaxis.py`), the held-out
prediction test (`scripts/m29_wallpredict.py`) and the feasibility relations of §7.2
(`src/exosat_rv/`) — lives in the project repository, with the milestone documents cited
inline throughout.

## References

- Bohn, A. J., Kenworthy, M. A., Ginski, C., et al. 2020, "Two directly imaged, wide-orbit giant planets around the young, solar analog TYC 8998-760-1".
- Bonnefoy, M., Marleau, G.-D., Galicher, R., et al. 2014, A&A (Letter), "Physical and orbital properties of β Pictoris b".
- Currie, T., Burrows, A., Madhusudhan, N., et al. 2013, "A combined VLT and Gemini study of the atmosphere of the directly-imaged planet β Pictoris b", arXiv:1306.0610.
- Hoy, K., Zurlo, A., Peña R., P. A., Köhler, J., et al. 2026, *Nature*, "Satellite detected around a star's substellar companion" (published version; supersedes arXiv:2607.05193v1).
- Horstman, K., Ruffio, J.-B., Batygin, K., et al. 2024, "RV measurements of directly imaged brown dwarf GQ Lup B to search for exo-satellites", arXiv:2408.10299.
- Köhler, J., Zechmeister, M., Hatzes, A., et al. 2025, A&A, "viper: High-precision radial velocities from the optical to the infrared", arXiv:2505.08315.
- Langlois, M., Gratton, R., Lagrange, A.-M., et al. 2021, A&A, "The SPHERE infrared survey for exoplanets (SHINE). II.".
- Lazzoni, C., Desidera, S., Gratton, R., Zurlo, A., Mesa, D., & Ray, S. 2022, MNRAS, "Detectability of satellites around directly imaged exoplanets and brown dwarfs", arXiv:2207.07569.
- Ruffio, J.-B., Horstman, K., Mawet, D., et al. 2023, "Detecting exomoons from radial velocity measurements of self-luminous planets: application to observations of HR 7672 B and future prospects", arXiv:2301.04206.
- Vanderburg, A., Rappaport, S. A., & Mayo, A. W. 2018, "Detecting exomoons via Doppler monitoring of directly imaged exoplanets", arXiv:1805.01903.
- Vanderburg, A., & Rodriguez, J. E. 2021, "First Doppler limits on binary planets and exomoons in the HR 8799 system", arXiv:2110.14650.
- Viswanath, G., Janson, M., Gratton, R., et al. 2023, A&A, "BEAST detection of a brown dwarf and a low-mass stellar companion around the young bright B star HIP 81208".
- "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", A&A, arXiv:2511.20091. *(This project's milestone documents attribute this paper to two different first authors — Kral et al. in M7/M10, Kral et al. in the methods note — so the citation must be checked against the published version before submission.)*

---

## What to verify before submission

Items for the author; everything else traces to a numbered milestone document or to a paper
archived in `papers/`.

1. **Publication priority on HIP 65426 b.** Its five nights are another team's
   active-programme data (2024–25). M20 §5 and LESSONS §6 record that publishing its headline
   ahead of them is Matthew's decision, and that that decision gates the paper fold-in of
   M20–M24. It is not on any axis here (no placeable contrast), but it is the measured reach
   anchor of §7.2; that argument survives on η Tel B and YSES 1 b alone, with weaker reach.
2. **Bibliographic details.** Bohn 2020, Bonnefoy 2014, Viswanath 2023 and Langlois 2021 are
   cited from the archived full texts; journal, volume and bibcode should be filled in from
   ADS, and the GRAVITY citation resolved (see the reference-list note).
3. **η Tel B's companion magnitude.** Lazzoni's K = 13.2 against SIMBAD's H = 11.93 implies
   H−K = −1.27, the wrong sign for a late-M/L dwarf. Langlois et al. 2021 is archived and
   should settle it. η Tel B is not load-bearing (§5.2), but the number appears in two tables.
4. **The construction-set separations that are not from a catalogue column.** YSES 1 b's 1.70″
   is the project ledger's value, and CD-35 2722 B's 2.80″ comes from M0; both should be
   attributed to their discovery papers. HIP 81208 B's two epochs differ (320.9 vs 328.7 mas)
   and 0.325″ is the midpoint — state that in the caption.
5. **HIP 81208 B's series.** Ledger-only, no milestone document, *n* = 3 epochs. Confirm the
   raw headers before it is stated in print; it is the highest clean S value and therefore sets
   the clean threshold.
6. **The n = 2 choice.** It is physically motivated and scanned, not fitted, and the scan is in
   the paper — but a referee will ask whether any monotone function of both variables would
   separate six points. The answer is yes, and the defence is §5.3's admission plus the
   pre-registered predictions of §5.4. Consider whether that is enough for a refereed venue.
7. **"To the best of our knowledge" hedges.** No claim of novelty here has been checked against
   ADS by a human; per M20 §5 all such statements remain provisional. This includes the claim
   in §5.4 that nobody has observed a system in the transition interval.
