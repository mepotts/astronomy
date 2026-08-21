# First resolve, then worry about contrast: a measured resolution gate for slit-fed companion radial velocimetry — and the free-floating regime where neither gate applies

*Matthew Potts · independent analysis · draft 2026-08-14*

*Instrument-oriented note. Target venue: A&A/MNRAS short paper or an instrument-design note. Written from milestones M7–M29 of the `exosat-rv` archival project; measured quantities are cited inline as (M-n §s), or (queue) for the roster ledger, and every separation traces to a primary source. Quantities that could not be sourced are marked, not estimated.*

---

## Abstract

Companion-side radial velocimetry — measuring the reflex motion of a directly imaged brown
dwarf or giant planet from its own spectrum, to detect a satellite or a second companion — is
normally proposed on a photon-noise argument, and this project twice tried to replace that
with a contrast threshold. Both are downstream of something simpler. Reading the **nodding
slit function** — the spatial profile along the slit, whose FWHM is the resolution that
observation actually delivered after AO, seeing and instrument — we measure **R = projected
separation / delivered PSF FWHM**, the number of resolution elements between companion and
host, for every target with a reduction on disk. **R < 1 means the pair sits inside one
resolution element: there is no companion spectrum to extract, at any contrast.** Across
eight classifiable reductions the roster splits cleanly — resolved at R = 1.32, 1.42, 1.79,
10.64, 11.26; blended at 0.39, 0.52, 0.54 — with nothing in between, and a second,
independent diagnostic from the same profile (its height at the companion's offset)
corroborates with a clean gap: 0.00–0.15 of peak when resolved, 0.55–0.71 when blended. The
consequences are concrete. **One of our own earlier readings is withdrawn**: we had recorded
HD 206893 B as "clean, gates 100–102%", and at R = 0.52 that extraction is a measurement of
its host. The withdrawal is of our reading of public archival data and of nothing that anyone
has published about this system; the GRAVITY astrometry that supplies the separation, and on
which the correction depends, is Kral et al.'s. **β Pic b's verdict
survives but its mechanism changes**: at R = 0.54 there was never a resolved companion to
contaminate, which is why its RV–barycentric correlation of *r* = +0.88 was unmoved by a
rebuilt template and by masking the responsible spectral order, at 99–100% injection
transmission throughout. And **no fit statistic detects this**: an injection gate measures
whether the *fitter* transmits an imposed velocity, which a bright host does better than a
faint companion — as do per-epoch precision and across-order dispersion. Only the spatial
profile catches it. The contrast question survives only above R ≈ 1, and it is untested:
every system in the interval where a contrast threshold would be tested is blended, which is
not a coincidence but the same fact stated twice. The instrument consequence is therefore a
requirement rather than a preference: **fibre-fed starlight suppression is not a better way
to work close in, it is the only way**, because the slit cannot deliver a companion spectrum
there to be limited by contrast at all. Isolated planetary-mass objects have no host, so
neither gate applies.

---

## 1. Introduction

Doppler monitoring of a directly imaged companion was proposed by Vanderburg et al. (2018),
applied to HR 8799 by Vanderburg & Rodriguez (2021) and to HR 7672 B by Ruffio et al. (2023),
forecast for the CRIRES+ era by Lazzoni et al. (2022), and pursued by Horstman et al. (2024)
on GQ Lup B. Hoy et al. (2026, hereafter H26) reported the first detection, in CD-35 2722 B.

Proposals in this genre are written on one feasibility axis: how bright the companion is.
Lazzoni et al.'s threshold is a pure flux scaling — 100 m s⁻¹ at K = 13.5, degrading 1.585×
per magnitude (M7 §1) — and this project's own ranking used the same form, re-anchored on
H26's achieved 31.44 m s⁻¹ at K = 12.01 (M7 §2). Running one injection-gated pipeline across
eleven archival systems shows that axis is not the binding one: companions of similar
brightness differ by four orders of magnitude in delivered velocity scatter.

Finding what *is* binding took four attempts, and the failures are part of the result. A
contrast threshold was asserted for several milestones before anyone computed the ratios;
computed, they moved, and one was contradicted by 2.4 mag by the discovery photometry.
Contrast alone then failed to order the outcomes, and so did separation alone. A combination,
S = contrast/θ², ordered them but could not be tested. What settled it was not a better
statistic but a measurement nobody had made: **the resolution each observation actually
delivered**, read off the spatial profile the pipeline already writes. This note reports two
gates in series — a geometric one that decides whether a companion spectrum exists at all
(§§3–6), and a contrast one that governs its quality and remains untested (§8) — and then the
instrument requirement that follows (§9) and the regime where neither gate applies (§10).

---

## 2. Provenance, and the rules that govern what counts

All spectra are public ESO archive holdings. RVs are extracted with `viper` (Köhler et al.
2025) in gas-cell-free CRIRES+ mode, forward-modelling each order against a telluric-free
template built from the target's own observations; reductions use `cr2res` 1.6.10, from raw
frames where required, and reproduce ESO's archived products to 42 m s⁻¹ in the final RV
(M12 §9b). No published RV truth exists off CD-35 2722 B, so signal injection carries the
validation burden for the velocities: every series below had to transmit an injected
Keplerian — imposed by shifting the template, never the observation — at both a loud and an
amplitude-matched semi-amplitude (M12 §8.1, M20 §1). §5 is about what that gate does *not*
cover.

**Nodding only.** Every dataset this project had classified as "staring-mode" turned out to
be **HiRISE**: fibre-fed SPHERE→CRIRES+ observations (`ESO INS MODE = HIRISE`), reduced by us
through a slit recipe. Three ledgered verdicts were retracted (queue, HiRISE banner; LESSONS
trap 1.10). Nodding conclusions stand; the fibre tier is provisional pending a
fibre-appropriate reduction (M27) and appears here only where noted.

**Every separation is sourced.** The values this project quoted were, until this milestone,
mostly unsourced — and a guessed separation is exactly what invalidates the analysis below.
They now read: CD-35 2722 B 2.800″ (M0), η Tel B 4.210″ and β Pic b 0.511″ (Lazzoni et al.
2022, Table 1, whose `Sep` column and host magnitudes sat unread in this repository for the
project's whole duration), HIP 81208 B 0.325″ (Viswanath et al. 2023; 320.9 and 328.7 mas
over two epochs), YSES 1 b 1.698″ (Bohn et al. 2020's projected 160 au with SIMBAD's
parallax), 2M0103AB b 1.764″ (SIMBAD component coordinates, PA 338.7°), HD 206893 B 0.205″
(GRAVITY astrometry, arXiv:2511.20091, interpolated to the CRIRES epoch between 206.8 mas at
MJD 59453.093 and 193.1 mas at 60127.218), HD 4747 B 0.590″ (Lazzoni Table 1).

**Contrasts are used only in §8, and carry known problems.** The catalogue's
companion-magnitude column is apparent magnitude — validated on YSES 1 b against Bohn et al.
(2020) to 0.14 mag — but not uniformly reliable: for β Pic b it gives K = 14.9 where Currie
et al. (2013, the source Bonnefoy et al. 2014 cite for that object's K_s photometry) measure
K_s = 12.47 ± 0.13, i.e. a contrast of ≈ 3950× rather than 36 983×. A primary source
overrides the column. η Tel B's entry is disputed on a colour argument and is not
load-bearing anywhere below.

---

## 3. The measurement that changed the question

HD 4747 B was pulled from the archive as a decisive test of the contrast criterion (§8): at
0.590″ it sat in the one interval no observation had ever sampled, with 19 public H-band
nodding frames in the same slit and grating as CD-35 2722 B. The night reduced cleanly — 24
of 24 spectral columns populated. The extraction is nevertheless of **HD 4747 A**.

The slit function says so directly. At the companion's 0.590″ offset the profile sits at
**0.75 of the primary's peak height** (median over 38 order-sides; 90th percentile 0.77).
That is not a faint companion trace; it is the host's own PSF wing. Seeing that night ran
0.86–1.31″, and the delivered profile FWHM is **1.514″** — the companion is well inside the
host's seeing disk (M29 §9).

That failure is more useful than the test would have been, because it names a quantity the
whole contrast discussion had been assuming. The nodding slit function *is* the spatial
profile along the slit, and its FWHM is the resolution that observation achieved after AO,
seeing and instrument together. Measured per order per night (`scripts/m29_psf.py`; median
subtracted, normalised to the peak, FWHM by linear interpolation on each side), it gives

    R = projected separation / delivered PSF FWHM

the number of resolution elements between companion and host. Both inputs are measured;
nothing is modelled or assumed. The classification rule was fixed before the sweep was run:
**R < 1 means the pair lies within one resolution element, so the extraction describes the
host, whatever the pipeline was told to call it.**

The same profile yields a second, independent diagnostic: its **height at the companion's
offset**, the quantity that flagged HD 4747 B. R comes from the profile's width, the wing
from its height somewhere else; they share no arithmetic.

This also dissolves what had looked like the roster's central anomaly. HIP 81208 B is clean
at 0.325″ — closer than β Pic b (0.511″, flooded) and HD 4747 B (0.590″, unresolvable) —
because its AO, on a bright B9 guide star, delivered a **0.246″** PSF, while β Pic b's nights
delivered **0.952″**, nearly four times worse. In arcseconds the ordering is incoherent. In
resolution elements it is trivial.

---

## 4. The roster sweep

`scripts/m29_blend.py` applies the test to every target with a reduction on disk.

| target | sep. | delivered PSF | orders | **R** | wing | class | ledger verdict |
|---|---:|---:|---:|---:|---:|---|---|
| η Tel B | 4.210″ | 0.374″ | 367 | **11.26** | 0.00 | resolved | NULL, injection-gated (M15) |
| CD-35 2722 B | 2.800″ | 0.263″ | 283 | **10.64** | 0.00 | resolved | CONFIRMED, 70–90 m s⁻¹ (M14) |
| 2M0103AB b | 1.764″ | 0.986″ | 10 | **1.79** | 0.02 | resolved | clean, ~53 m s⁻¹ (queue) |
| YSES 1 b | 1.698″ | 1.197″ | 24 | **1.42** | 0.12 | resolved | clean, 34 m s⁻¹ (queue) |
| HIP 81208 B | 0.325″ | 0.246″ | 32 | **1.32** | 0.15 | resolved | clean, 124 m s⁻¹ (queue) |
| β Pic b | 0.511″ | 0.952″ | 114 | **0.54** | 0.55 | **blended** | contamination-limited (M20 §2) |
| HD 206893 B | 0.205″ | 0.393″ | 11 | **0.52** | 0.63 | **blended** | *"clean, gates 100–102%"* — **withdrawn** |
| HD 4747 B | 0.590″ | 1.514″ | 15 | **0.39** | 0.71 | **blended** | reduced as the §8 test; no verdict |
| CD-35 deep pair | unsourced | 0.278″ | 14 | — | — | unknown | shelved (thermal-IR); carries no verdict |

Three things follow.

**The two diagnostics agree, with a gap.** Resolved cases have wing ≤ 0.15, blended cases
≥ 0.55, and the ordering by wing is the ordering by R. No point lies between R = 0.54 and
R = 1.32, so the empirical threshold is bracketed by a factor of 2.4 — and the value optics
predicts, R ≈ 1, lies inside that bracket. Unlike every threshold this project has previously
quoted, it was not read off the data.

**One verdict is withdrawn.** HD 206893 B is recorded in the ledger as "clean data both
settings, gates 100–102%, epochs banked". At R = 0.52 with a wing of 0.63 the pair is
unresolved: the spectrum is the host's, and the verdict is not a companion measurement.

**Four verdicts are confirmed as genuine companion measurements** — CD-35 2722 B, η Tel B,
YSES 1 b and HIP 81208 B, at R from 1.32 to 11.26, with 2M0103AB b's at-risk entry clearing
at R = 1.79 and a wing of 0.02. Every claim this project rests on survives the check: the
detection, the η Tel B limit, and the two best-precision series.

Four limitations belong with the table. PDS 70 is absent, because its H-band nights were
never reduced (blocked on an order-mapping quirk), so the one system that plausibly fails by
a different mechanism — companions inside the AO core at 0.17–0.21″ — has no R. The slit
function is fitted to the brightest trace, which is the companion when it is observed alone
and the host when the pair is blended; the width is the delivered resolution either way, but
these are not identical measurements. Order counts run from 10 to 367, and HD 4747 B's PSF
rests on 15 order-profiles from a single night. And R was formed *after* the outcomes were
known: it is a better-motivated hypothesis than its predecessors, not a validated criterion,
and the honest test remains a target classified before its reduction.

---

## 5. Why no fit statistic catches this

The transferable lesson is not about resolution but about what verification can see.

The injection gate this project relies on — impose a Keplerian on the template, re-run the
full fit, require the amplitude back — measures whether **the fitter** transmits a velocity.
A bright host transmits one *better* than a faint companion. HD 206893 B's gates read
100–102% while the object being measured was the wrong star. The same holds for the other
internal diagnostics: per-epoch precision improves on a host, and so does across-order
dispersion. A blended extraction therefore looks, by every statistic this subfield uses,
like an unusually good observation.

This is the second time in this project that a passing gate accompanied a meaningless
measurement, and the two are instructively different. In the first (PDS 70's nine-night
template, M23 §4) the template had lost its stellar lever and the gate *did* catch it, at
−62 ± 197% recovery. Here the gate cannot help, because nothing is wrong with the fit — the
spectrum is real, well exposed, and belongs to another object.

**A blending check therefore belongs in the pipeline before the injection gate, not after
the verdict.** It costs one read of a profile the reduction already writes, needs no extra
data, and tests the one thing every other check assumes: that the spectrum belongs to the
object named in the verdict.

---

## 6. β Pic b: the same verdict, a different mechanism

β Pic b remains contamination-limited, and the three-pass ladder that established it stands
(M20 §2). A template reused from a single night gave 4712 m s⁻¹ of night scatter at
*r*(RV, BERV) = +0.94. Rebuilding it across all 28 frames and 813 d halved the scatter to
2466 m s⁻¹ and left *r* = +0.88. Masking the Br-γ order and dropping six injection-unstable
orders left *r* = **+0.88, unchanged**, with injection transmission at 99–100% on the eleven
surviving orders and every long-period peak dying under a BERV covariate.

What changes is the explanation. This was reported as starlight leaking into a resolved
companion's spectrum. At R = 0.54, with a wing of 0.55, **there was no resolved companion**:
the extraction is a blend dominated by the host, which is precisely why no order mask and no
template rebuild could move *r*(BERV) through v1, v2 and v3. An empirical result that had to
be described — "pervasive, not surgical" — now has a cause.

Three consequences survive intact and are strengthened by having a mechanism:

1. **It is a systematic, not a sensitivity limit.** The gates ran at 99–100% throughout: the
   pipeline transmitted injected velocity essentially perfectly while returning km s⁻¹ of
   host motion. **Collecting area does not help.** An ELT-class aperture improves the photon
   term, which was never binding; it also concentrates the PSF, which is the term that *does*
   bind — an argument for extreme-AO feeds rather than for aperture alone.
2. **Masking is not a mitigation.** Not because the contamination is spectrally broad, but
   because there is nothing to unmask.
3. **The signature is cheap to test for in advance**: km s⁻¹ epoch scatter with high injection
   transmission, a strong RV–BERV correlation, and candidate periodicities that vanish under a
   BERV covariate. Two independent reductions of β Pic b give ΔBIC −1.8 and −1.7 at the period
   where CD-35 2722 B gives +27.9 (M28 §1): no periodic content at all. The profile check of
   §3 is cheaper still, and diagnostic rather than suggestive.

---

## 7. Inside the resolved regime: contamination, bounded directly

At the far end of the roster the contaminating flux can be measured rather than inferred. On
CD-35 2722 B (R = 10.64, wing 0.00) the extraction swath spans the full slit — order height
179.8 px at 0.056″/px, i.e. 10.07″, sampled by a 512-point slit function at 0.0197″ per point
— and the slit angle is pinned at POSANG = 153.1° on all eighteen nights with a 6″ nod throw,
so the primary falls a fixed 161 points from the companion trace in every frame (M28 §5).

Measured there, **no primary peak is detected on any night**: median height at the primary's
offset, relative to the companion peak, 0.0006 against a local profile noise of 0.0072 —
0.1σ. Per-night 3σ upper bounds run **1–11%, median 2.5%**, consistent with and on most
nights tighter than H26's ~15% worst-night slit-viewer estimate. Two caveats: the profile
median is removed first, so this bounds a *resolved* second trace rather than a smooth halo
pedestal, and complements the slit-viewer method; and the one epoch our quality screen
rejects carries the largest ratio of the eighteen (0.019) at 2.0σ, on the campaign's best
seeing — contamination does not explain why that night is bad.

Expressed as the fraction of host light in the extracted spectrum, ≲ a few percent
accompanies 70–130 m s⁻¹ per epoch. That is the resolved regime working as intended, and it
is the only direct measurement of the contaminating flux in the series.

---

## 8. The second gate: contrast, and why it is untested

Within the resolved regime, how much host light contaminates a real companion spectrum should
still matter, and the natural quantity is the scattered host flux relative to the companion's:
S = contrast / θⁿ, with a seeing- or AO-limited halo wing falling as θ⁻² to θ⁻³. The exponent
was fixed by that argument and then scanned rather than fitted (`scripts/m29_wallaxis.py`); S
separates this project's outcomes for *n* = 1.5–4.0, most cleanly at *n* = 2, with clean cases
at S = 12, 24, 3557, 4327 against non-clean cases at 15 202 and 15 917.

**One robustness check has since been run, and it passed.** η Tel B's contrast rested on a
catalogue magnitude that primary-source photometry has since overturned by 1.6 mag
(Neuhäuser et al. 2011: K_s = 11.6, not 13.2), moving its S from 107 to 24. The class
separation is unchanged — the correction only pushes a clean case further from the boundary.

**The same correction exposed where this was weakest, and a better source has since closed
it.** The failure side rested on two points 4% apart — β Pic b at S = 15 202, primary-sourced
(Currie et al. 2013), and PDS 70 b at S = 15 917, from the same suspect catalogue column and
therefore effectively unverified. One verified point does not define a boundary.

Lazzoni et al. (2020) resolves this. Its Table 2 carries contrasts **measured from SPHERE
observations** for 27 companions, with matching separations at the same epoch — one
instrument, one band, one paper, which is the primary-source photometry this axis needed. Three
of our six systems appear in it, and re-running the class test on that column alone
(`scripts/m32_wall_measured.py`), with no mixing of bands and the exponent carried over
unchanged:

| system | sep (″) | measured contrast | S | verdict |
|---|---:|---:|---:|---|
| η Tel B | 4.21 | 667× | **38** | clean |
| PDS 70 b | 0.19 | 1818× | **50 365** | fails |
| β Pic b | 0.33 | 10 000× | **91 827** | fails |

**The ordering survives, and the margin widens from a factor 3.5 to a factor 1339.** Both
failure cases sit three orders of magnitude above the clean one. Crucially, PDS 70 b — the
point that previously defined the boundary, on an unverified magnitude — is *further* into the
failing regime when measured, so the boundary was drawn too tight rather than too loose.

This is three points, and three points in two classes separate by chance easily; no threshold
should be read off them, and it cannot replace the six-system test because CD-35 2722 B,
HIP 81208 B and YSES 1 b are absent from that table. It is a check, and the check passed.
PDS 70 b may still fail by a different mechanism regardless of photometry (§8).

We report that, and claim nothing from it, for a reason that is itself the result. Applied to
31 catalogued companions with thresholds fixed in advance, S predicted correctly for the only
two systems genuinely held out (CT Cha b, AB Pic b) — both clean, both 50–100× below the
threshold, neither discriminating — and there is no held-out failure case. Searching the
catalogue for the untested interval, 4327 < S < 15 202, returns four systems, and **every one
of them is unavailable**: κ And b is unobservable from Paranal, PDS 70 c shares frames with
PDS 70 b inside the AO core, β Pic b sets the threshold it would be tested against, and
HD 4747 B — the reduction that prompted this note — is blended.

**That is not bad luck.** Being close enough to have an interesting S is what makes a
companion unresolvable at a slit. The three blended systems have the three highest S values in
the roster, and they are blended for the same reason their S is high. So the second gate may
be not merely untested but **untestable with slit spectroscopy**: the regime where contrast
would decide the outcome is the regime where the first gate has already decided it.

Three predictions from S were placed on the record before the fact and are kept, restated in
the two-gate form — all three sit at ≥ 2.2″ and so should pass the resolution gate under any
delivered PSF in our sample (0.246–1.514″): DH Tau B (S = 41), GSC 6214-210 B (S = 37) and
1RXS J160929.1-210524 b (S = 318) are predicted **resolved and clean**. They are weak tests,
far below the threshold, and we say so.

---

## 9. The instrument requirement

The recommendation this project has carried since M20 — fibre-fed starlight suppression for
close companions — changes character here, from a preference to a requirement derived from a
measurement.

**Nor is this a problem an algorithm can dissolve, which is worth stating because a reader
will reasonably ask.** The state of the art for host contamination in companion long-slit
spectroscopy is EXOSPECO (Thé et al. 2023), a regularised inverse method that models the
chromatic PSF and the spatio-spectral dispersion laws jointly and separates the star's and the
companion's contributions from SPHERE/IRDIS data. It is a genuine advance, and it is aimed at
the *other* gate: its data model is built around "residual stellar light diffracted by the
coronagraphic mask", which presupposes a coronagraph and, crucially, a companion that is
already resolved from its host. Deconvolving a bright halo away from a faint but separable
source is not the same operation as recovering two spectra from one resolution element, and
nothing in that literature claims the latter. The two gates are attacked by different means:
the contrast gate by better modelling, the resolution gate only by better optics.

**A slit cannot deliver a companion spectrum below R ≈ 1 at any contrast.** The three blended
systems were not limited by contrast, by exposure time, by template quality or by extraction
choices; there was no second spectrum in the aperture. Extreme-AO fibre feeds (HiRISE at the
VLT, KPIC at Keck; RISTRETTO-class concepts in the same family) are therefore not a way to do
the close regime *better*. They are the only way to do it at all. Interferometry sits in the
same position from the other direction: the VLTI/GRAVITY astrometric exomoon search on
HD 206893 B (arXiv:2511.20091) resolves at 0.205″ what our slit could not, which is how this
note has that separation to quote in the first place.

Two practical statements follow for anyone writing an observing block:

- **Specify the delivered PSF, not the separation.** β Pic b at 0.511″ needed better than
  ~0.5″ delivered; it got 0.952″, and thirteen nights over 813 days produced a host
  measurement. HIP 81208 B at 0.325″ succeeded on 0.246″. The measured spread across this
  roster is 0.246–1.514″ — a factor of six, and the difference between a companion series and
  an expensive stellar one.
- **The archive already holds the alternative**: six public HiRISE nights of β Pic b (Oct–Dec
  2024), a starlight-suppressed series of exactly the object the slit loses (queue banner).

And four things that cost nothing: read the slit function before trusting any verdict (§5);
ask for 6–10 frames per night rather than ~2, the binding constraint on measuring companion RV
jitter being frames per night rather than nights (M29; NEXT-DIRECTIONS §A1); run the
phase–BERV geometry check before the block is written (CD-35 2722 B's sampling correlates
orbital phase with the barycentric correction at *r* = −0.71, η Tel B's leaves the 150–300 d
decade clean, M15 §1); and never build a template from a single night (LESSONS trap 6).

---

## 10. Free-floating planetary-mass objects: neither gate applies

**Both gates are defined by the presence of a host, and an isolated planetary-mass object has
none.** R is not large, it is undefined: there is no pair to resolve, no PSF wing at the
companion's position, and no blend to mistake for a companion spectrum. The numerator of S is
zero. Every failure mode in §§3–8 requires a star to produce it, as do the slit angle pinned
across eighteen nights to keep a primary off the trace and the AO performance on which that
turns. That matters more than it would if the gates were well located: the weakest parts of
this note are the two thresholds — R ≈ 1 bracketed by a factor of 2.4, and a contrast gate
that may be untestable at a slit — and for an isolated target neither uncertainty is reduced,
both are irrelevant.

What is *unchanged* is what makes the measurement possible: a young, self-luminous object
radiating its own K ≈ 12–15 infrared spectrum, of the class this project measured eleven
times. The telluric wavelength reference, the template built from the target's own data and
the injection test are all host-independent.

**The reach, from measured numbers.** On η Tel B, a ~47 M_Jup host, 20 archival epochs over
815 d at 127–130 m s⁻¹ exclude companions of 0.51–1.27 M_Jup across *P* = 20–300 d, at
injection transmission 99–101 ± 1%. Nothing in that chain used the host star. We anchor on
this target rather than on the deeper archival limit we also hold for HIP 65426 b, because
those five nights belong to another group's active programme; that limit is not reported here.
The per-epoch precisions behind such a limit — all injection-gated, all on resolved
pairs — span **34–190 m s⁻¹** (§4), with 162 m s⁻¹ measured within a night on β Pic b (M17
§§1–2), a number we now read as a statement about a blend rather than about a planet. Scaling
to isolated hosts with the field's standard relation (Lazzoni et al. 2022 eq. 2, as
implemented here), calibrated against our own injection-derived limits — at 3σ per epoch it
returns 0.65, 1.18 and 1.40 M_Jup at *P* = 20, 120 and 200 d for η Tel B, against the measured
0.51, 0.77 and 1.11, i.e. **conservative by 1.3–1.5×** across the decade it is anchored on:

| per-epoch σ | 5 M_Jup host | 10 M_Jup | 13 M_Jup |
|---:|---:|---:|---:|
| 34 m s⁻¹ (best measured) | 17 M_⊕ | 27 M_⊕ | 32 M_⊕ |
| 130 m s⁻¹ (typical measured) | 65 M_⊕ | 103 M_⊕ | 123 M_⊕ |
| 190 m s⁻¹ (worst clean) | 97 M_⊕ | 152 M_⊕ | 181 M_⊕ |

*Smallest satellite* m sin i *clearing 3σ on a single epoch at P = 50 d; ranking-grade,
calibrated as above, not a substitute for an injection-derived limit.*

A lighter host helps — at fixed satellite mass and orbit the reflex amplitude scales as
M_p^(−1/2), so a 5–13 M_Jup isolated object is a better wobble target than the 37–47 M_Jup
brown dwarfs dominating this roster (M7 §5) — and two dynamical asymmetries follow from the
absence of a star: the satellite's stable zone is not truncated from outside, that limit being
set by the host's tidal field; and tidal spin-down of a giant planet *by its star*, which
pushes corotation beyond the stability limit so that every stable satellite inspirals
(M8 §§1–2), requires a star. Against that, the host mass is model-derived with no dynamical
anchor, entering mildly: satellite mass scales as M_p^(1/2), so a 30% host-mass error is ~14%
in it.

**What we cannot claim.** There is no archival result: the ESO archive was swept for isolated
planetary-mass objects with multi-epoch CRIRES+ coverage and came back negative and exhaustive
(queue banner, idea #4), so this is a proposal case. Brightness remains the binding cut and
bites below K ≈ 15, where the flux scaling degrades faster than 1.585×/mag as background takes
over (M7 §1); every precision quoted here was achieved at K = 12.0–15.1. We have run no
population census. Acquisition and wavefront sensing on a target with no bright neighbour is
an unquantified operational cost we have no measurement bearing on. And none of this is an
exomoon-detection argument: the underlying population study expects RV to reach binary-like
satellites (mass ratio ≳ 0.01), not solar-system analogues (M7 §1). Removing the host improves
the noise, not the occurrence rate.

---

## 11. Summary for a proposal

1. **Check resolution first.** R = separation / delivered PSF FWHM, both measured. Below
   R ≈ 1 there is no companion spectrum at any contrast, and the empirical bracket from this
   roster is 0.54 < R_crit < 1.32.
2. **Read the slit function before believing any verdict.** A blended extraction passes
   injection gates, improves per-epoch precision and improves across-order dispersion. One
   verdict here was withdrawn on this basis; four survived it.
3. **Specify the delivered PSF in the observing block**, not the separation. The spread across
   this roster is 0.246–1.514″.
4. **Treat the contrast gate as open.** It applies only above R ≈ 1, it is untested, and every
   system that would test it is blended — possibly making it untestable at a slit.
5. **Where the pair is unresolved, a fibre feed or an interferometer is not an improvement but
   a requirement.** Public HiRISE nights on β Pic b already exist.
6. **And point some of it at objects with no host at all**, where neither gate applies and the
   measured precisions transfer unchanged.

---

## Acknowledgements and statement of AI involvement

The analyses summarised here — archive census, reduction, pipeline development, statistical
calibration, the sourcing and blending audits, and the drafting of this note — were carried
out by AI agents (Claude, Anthropic, running in Claude Code), directed and reviewed by the
human author, who set the research questions, challenged the agents' claims, made every
decision with external consequences, and takes sole responsibility for all content.
Verification is primarily mechanical rather than expert-audited: every adopted pipeline change
was scored against an external reference and required signal-injection recovery; positive
controls preceded every null. Dead ends and retractions remain in the public record, including
the three superseded framings of this note's organising variable and the verdict withdrawn in
§4. Based on data obtained from the ESO Science Archive Facility. This document reports an
independent analysis and is not affiliated with or endorsed by the authors of any work
discussed.

## Data and code availability

All spectra are public ESO archive products and raw frames. The pipeline — reduction drivers,
converter, injection harness, the delivered-PSF measurement (`scripts/m29_psf.py`), the roster
blending sweep (`scripts/m29_blend.py`), the slit-function contamination bound
(`scripts/injection/m28_contam.py`), the contrast-axis tests (`scripts/m29_wallaxis.py`,
`scripts/m29_wallpredict.py`) and the feasibility relations of §10 (`src/exosat_rv/`) — lives
in the project repository, with the milestone documents cited inline throughout.

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
- Thé, S., Thiébaut, É., Denis, L., et al. 2023, A&A, "Characterization of stellar companions
  from high-contrast long-slit spectroscopy data: the EXOSPECO algorithm", arXiv:2306.03467.
- "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", A&A, arXiv:2511.20091 — the source of HD 206893 B's projected separation. *(This project's milestone documents attribute this paper to two different first authors — Kral et al. in M7/M10, Kral et al. in M11 and the methods note — so the citation must be checked against the published version before submission.)*

---

## What to verify before submission

Items for the author; everything else traces to a numbered milestone document or to a paper

0. **⚠ THE CONTRAST AXIS'S SOURCE COLUMN IS UNRELIABLE (M32) — but the result survived the
   one correction available.** §8's numbers, and the 31-companion held-out test, read Lazzoni
   et al. 2022 Table 1's companion-magnitude column. Checked against primary sources three
   times, it is wrong twice: YSES 1 b to 0.14 mag (Bohn+2020) ✅, **η Tel B by 1.6 mag**
   (Neuhäuser+2011 K_s = 11.6) ❌, **β Pic b by 2.4 mag** (Currie+2013) ❌ — a factor 4–9 in
   contrast against a boundary interval only a factor 3.5 wide.

   **Applying the η Tel B correction did not break §8:** S moves 107 → 24, and the class
   separation for *n* = 1.5–4.0 is unchanged, because the correction only pushes a clean case
   further from the boundary. That is a real robustness check and it is now stated in §8.

   **What it does expose is the failure side.** It rests on two points 4% apart — β Pic b
   (primary-sourced) and PDS 70 b (same suspect column, unverified, and possibly failing by a
   different mechanism). *One verified point does not define a boundary.*

   **RESOLVED, and better than expected.** Lazzoni et al. **2020** (A&A 641, A131 — the
   satellite-search paper that is also η Tel B's mass source, and which was unread here until
   M32) carries *measured* SPHERE contrasts for 27 companions in its Table 2, one instrument
   and one band. Re-running the class test on that column alone (`scripts/m32_wall_measured.py`)
   reproduces the ordering with the margin widening from a factor 3.5 to **1339**, and moves
   PDS 70 b — the point that defined the boundary from an unverified magnitude — *further*
   into the failing regime. Both results are now in §8.

   **What remains:** the check covers only 3 of the 6 roster systems (CD-35 2722 B,
   HIP 81208 B and YSES 1 b are absent from that table), so the K-band test is not replaced,
   only corroborated. §1–§7 were never affected — they rest on measured separations and
   measured PSFs. **The resolution gate is the note's result; the contrast gate is now a
   supported open question rather than an unsupported one.**

1. ~~**The withdrawn verdict, HD 206893 B (§4).**~~ — **REWORDED (M33).** §4 now says
   explicitly that it is *our own earlier reading* that is withdrawn, that the withdrawal
   concerns public archival data and not anything published about the system, and that the
   GRAVITY astrometry the correction depends on is Kral et al.'s.
2. ~~**Publication priority on HIP 65426 b.**~~ — **RESOLVED BY REMOVING THE DEPENDENCY (M33).**
   Rather than decide whether to publish a headline from another group's active-programme
   nights, the reach argument is now anchored on **η Tel B**, which this project owns outright
   and is publishing separately. The relation reproduces its measured limits at
   *P* = 20/120/200 d to within **1.3–1.5× and on the conservative side**, so the anchor is
   better constrained than before — three periods instead of one — and the HIP 65426 b limit is
   explicitly not reported. No permission is now required from anyone.
3. ~~**The delivered-PSF measurement.**~~ — **TESTED AND PASSED (M33,
   `scripts/m33_psf_validation.py`).** The referee's question is whether the slit-function
   FWHM is the sky's or the extraction's. ESO writes independent image-quality measurements
   into every header — DIMM seeing from a separate telescope, and an image-analysis FWHM from
   the guide probe — and neither passes through `cr2res`, so they are a clean external
   reference. Across 60 nights:

   - it varies by **69%** night to night, so it is not set by fixed extraction parameters;
   - **within a target, guide star held fixed, it tracks the telescope's own image-analysis
     FWHM at r = +0.51 (CD-35, n = 18) and +0.50 (β Pic, n = 11)**;
   - it sits at **0.60×** the seeing-limited H-band prediction, as adaptive optics plus the
     λ^(−1/5) gain require.

   Pooling targets gives only r = +0.25, but that is the wrong test: the AO loop is closed and
   guide-star magnitude spans 3.3–10.7, and AO exists to break the seeing-to-delivered
   relation. **η Tel B shows no correlation at all (r = +0.02), and that is the informative
   case rather than a counter-example** — its guide star is magnitude 5.2 against CD-35's 10.1,
   and a bright guide star is exactly where AO delivers a near-diffraction-limited core whose
   width stops following the seeing. Its R = 11.3 is nowhere near the threshold, so nothing in
   its classification depends on this.

   **What this does not establish, and the note should say so:** the systems nearest the
   threshold cannot be validated individually — HIP 81208 B, YSES 1 b and 2M0103AB b have 3, 2
   and 1 nights. Their PSFs rest on the method validated here, not on their own evidence.
4. ~~**HD 4747 B's PSF rests on 15 order-profiles from one night**, HD 206893 B's on 11.~~ —
   **TESTED (M33, `scripts/m33_psf_robustness.py`).** Bootstrapping the median over the
   available profiles and propagating into R gives 68% intervals of **R = 0.39–0.39**
   (HD 4747 B), **0.52–0.57** (HD 206893 B) and **0.53–0.55** (β Pic b, 114 profiles over 12
   nights). Every interval stays entirely below the boundary, so **the blended classification
   does not depend on the thinness of the sample** — only the point estimate would have.
5. **PDS 70's R is still unmeasured — but the recorded reason was wrong (M33).** These nights
   are not unreduced. All three ran through the *staring* recipe and carry
   `cr2res_obs_staring_slitfunc.fits`; every earlier sweep searched for the nodding filename
   and so read three usable nights as zero. The staring profile still cannot be used: only one
   of the three nights carries a trace-wave file, the profile is sampled ~906 points against
   the nodding path's ~512 over the same order height, and the width it yields is **0.18× the
   telescope's own image-analysis FWHM on that night, where every nodding target sits between
   0.42× and 1.46×** — several times too narrow to be a delivered PSF. Taken at face value it
   would place both PDS 70 companions *above* R = 1 and contradict this note's assumption that
   the system fails by sitting inside the AO core, which is precisely why it is not taken at
   face value. Closing this needs a nodding reduction or a standard star, not a re-read of
   what is already on disk.
6. **Bibliographic details.** Bohn 2020, Bonnefoy 2014, Viswanath 2023 and Langlois 2021 are
   cited from archived full texts; journal, volume and bibcode should come from ADS, and the
   GRAVITY citation resolved (see the reference-list note).
7. **"To the best of our knowledge" hedges.** No novelty claim here has been checked against ADS
   by a human; per M20 §5 all such statements remain provisional, including the §8 statement
   that no observation exists inside the untested contrast interval.
