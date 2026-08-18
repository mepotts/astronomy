# Candidate I — the dossier

**Gaia DR3 3854090071297359616 · AllWISE J093954.31+070027.9 · 2MASS J09395432+0700281**

*Assembled 2026-08-18 (milestone M2) for a decision. Candidate-level claims in this
repository are Matthew-gated: nothing here has been submitted, posted, or sent
anywhere. Every externally-sourced number carries its source; anything unsourced is
marked UNSOURCED.*

---

## The headline, in one sentence

**The last Dyson-sphere candidate standing is standing only because nothing in the
archive can knock it down: its entire infrared excess is two WISE measurements that both
fall *below WISE's own 5σ sensitivity* on the ecliptic, that sit inside the 95% upper
limits of their own neighbours, that were never detected in a single exposure, and one of
which is a formal non-detection in the other reduction of the same photons — so candidate
I is not an unrefuted candidate, it is an unvettable one, and ≈1.2 h of JWST/MIRI imaging
would settle it either way.**

| | |
|---|---|
| **Verdict** | **INDETERMINATE**, and — new in M2 — *indeterminate for a stronger reason than M1 knew*: the W3 excess is not stable between WISE data releases. |
| **What would settle it** | JWST/MIRI imaging, two filters (F1000W or F1280W + F2100W), one visit, **≈1.2 h charged**. Section 8. |
| **What would not** | Any ground-based mid-IR facility; SPHEREx; any deeper optical/NIR survey; more WISE analysis. Section 9. |
| **Prior** | The candidate that archival vetting ranked *cleanest* of all ten (D) was destroyed by JWST. Archival cleanliness has demonstrated ~zero predictive value here. Section 7. |

---

## 1. Identity, position, provenance

| Quantity | Value | Source |
|---|---|---|
| Gaia DR3 source_id | 3854090071297359616 | Gaia DR3 |
| RA, Dec (ICRS, J2016.0) | 144.976333, +7.007741 | Gaia DR3 |
| Proper motion | µ<sub>α*</sub> = −4.744, µ<sub>δ</sub> = −14.760 mas yr⁻¹ | Gaia DR3 |
| Parallax | 5.894 ± 0.103 mas | Gaia DR3 |
| Distance (Bailer-Jones geometric) | 169.28 (166.75–172.01) pc | `external.gaiaedr3_distance.r_med_geo` |
| G, BP, RP | 17.402, 19.003, 16.182 | Gaia DR3 |
| M_G | 11.26 | this work |
| T_eff (GSP-Phot) | 3327 K → M3.5V | Gaia DR3; spectral type per Heph III |
| RUWE | 0.959 | Gaia DR3 (single-star astrometry, no companion signal) |
| classprob_dsc_combmod_star | 0.998 | Gaia DR3 |
| J, H, K_s | 14.417 ± 0.032, 13.900 ± 0.042, 13.669 ± 0.035 | 2MASS (ph_qual AAA) |
| W1, W2 | 13.459 ± 0.024, 13.259 ± 0.031 | AllWISE |
| W3, W4 | 12.316 ± 0.448, 8.489 ± 0.326 | AllWISE |
| AllWISE ph_qual / cc_flags / ext_flg | AACB / 0000 / 0 | AllWISE |
| AllWISE nb / na | 1 / 0 — single-PSF fit, no active deblending | AllWISE |
| Gaia↔AllWISE separation | 0.074″ | `gaiadr3.allwise_best_neighbour` |
| Excess fit (published) | T = 99 ± 20 K, γ = 0.147 ± 0.046 | Heph III Table 3 |
| Excess fit (this work) | T = 125 K, γ = 0.085, RMSE 0.056 | `out/w2_sed_fits.csv` |
| Galactic coordinates | l = 227.76°, **b = +40.39°** (high; low Galactic confusion) | AllWISE `glon`/`glat` |
| **Ecliptic latitude** | **β = −6.58°** — the source sits essentially **on the ecliptic** | AllWISE `elon`/`elat` |
| AllWISE artifact/coverage detail | `moon_lev` 0000, `w3cc_map` 0, `w4cc_map` 0, `w3cov` 10.9, `w4cov` 11.0 | AllWISE |

**Provenance — this is a Hephaistos *III* object, not a Hephaistos II candidate.**
Candidate I was **not** among the seven candidates of Suazo et al. (2024). It
**failed Hephaistos II's own S/N ≥ 3.5 cut** (its W3 S/N is 2.4) and entered the
candidate list only through Korn et al. (2026, Heph III), who ran NOT/ALFOSC
spectroscopy on sub-threshold objects. My independent implementation of the
Hephaistos II cuts reproduces this exactly: I passes C1–C5 and fails C6 and only C6
(M1 §2.2, `out/w1_acceptance.csv`).

This matters for how the candidate should be read. Every statement of the form "the
last surviving Dyson sphere candidate" is about an object that the parent survey's
own quality gate rejected. Hephaistos II drew its S/N ≥ 3.5 line precisely to keep
objects like this one out.

Spectroscopy (Heph III §3.2): Hα in emission, EW ≈ −2.8 Å — consistent with ordinary
M-dwarf chromospheric activity, not accretion. Gaia's own ESP-ELS pseudo-EW for this
star is +0.292 ± 0.167 nm, i.e. the same |EW| ≈ 2.9 Å; the two measurements agree in
magnitude, and the sign difference is the two catalogues' opposite conventions.
**Caveat (UNRESOLVED):** I have not verified from the Gaia DR3 documentation which
sign `ew_espels_halpha` uses for emission. M1's implementation of cut C5a assumed
negative = emission and reproduced the published funnel; if the convention is the
reverse, C5a's behaviour on the whole sample needs re-checking. Flagged for W4.

---

## 2. The full photometric SED, including the SPHEREx extraction

Figure: **`out/m2_I_sed.png`**. Contents:

- **179 archival photometric points from 26 catalogues** within 3″ (VizieR SED
  service, CDS/CfA mirror; `data/photometry/sed_I.csv`), 0.35–22 µm.
- **SPHEREx QR2 forced aperture spectrophotometry — 271 usable exposures, 102 bands,
  0.75–5.0 µm** (`scripts/w3_spherex.py`, `out/w3_spherex_I_sed.csv`). This is, to my
  knowledge, the first extraction of candidate I's SPHEREx spectrum — I was not in
  Hephaistos IV. Validation against catalogue fluxes (medians, mJy): J 2.74/2.73,
  H 3.11/2.82, K_s 2.45/2.27, W1 1.27/1.30, W2 0.92/0.85 — ~10% with no aperture
  correction.
- **The star is photospheric through the last SPHEREx bin** (4.8–5.0 µm: 0.60 mJy).
  No excess onset, no hot component. A ≳600 K dust component or a very red close
  companion would have bent the 3–5 µm continuum; none is seen.
- Photospheric template: empirical M-dwarf locus, 1320 clean dwarfs within 30 pc
  (`scripts/w1_fetch_locus.py`), because Pecaut & Mamajek 2013 has no W1−W2/W3/W4
  colours for K6V–M4.5V.

**What SPHEREx settles and what it does not.** It settles that the *photosphere model
underlying the excess claim is right* — the excess is not an artefact of a mis-fitted
star. It cannot see the excess itself: a 100–200 K blackbody peaks at 15–30 µm and
contributes essentially nothing below 5 µm. And with 6.15″ pixels it blends
star + contaminant exactly as WISE W1/W2 do.

---

## 3. The excess, stated honestly

**The excess lives in exactly two bands — W3 and W4 — and it is 2σ-class in both.**

`scripts/m2_i_excess.py` → `out/m2_I_excess.json`. Excess is stated in **flux**, not
magnitudes, because magnitudes flatter a faint excess badly: candidate I's 4.46 mag
W1−W4 colour excess looks like a 12σ result and is a 3.3σ flux measurement. W2 is
included as the internal control — the same machinery must find *no* excess there.

| Band | m_pro | S/N | f_obs (mJy) | f_phot (mJy) | f_excess (mJy) | **excess significance (flux)** |
|---|---|---|---|---|---|---|
| W2 (4.6 µm) | 13.259 | 35.0 | 0.854 | 0.836 | 0.018 | **0.5σ** — photospheric, as it should be |
| W3 (11.6 µm) | 12.316 | 2.4 | 0.375 | 0.175 | 0.201 | **1.3σ** |
| W4 (22 µm) | 8.489 | 3.3 | 3.363 | 0.056 | 3.308 | **3.3σ** |

**Joint W3+W4 significance: 3.5σ, before any trials factor.** The trials factor is
not small: the object was selected from a 5 × 10⁶-star search precisely *because* it
has the largest apparent W3/W4 excess, and it entered the candidate list through a
follow-up campaign targeting sub-threshold excesses.

Several further facts, all new in M2 — and they compound:

**(a) Both W3 and W4 are sub-5σ against WISE's own published sensitivity, and the target
sits on the ecliptic — the survey's shallowest regime.** WISE's quoted 5σ point-source
sensitivities *on the ecliptic* are 0.86 mJy (W3) and 5.4 mJy (W4) (All-Sky Explanatory
Supplement §1.1). At β = −6.58° that is the applicable column, not the deeper
ecliptic-pole values. Candidate I's measurements are **0.375 mJy (W3) = 0.44×** and
**3.36 mJy (W4) = 0.62×** those limits. **Neither band reaches the survey's own 5σ
threshold.**

**(b) The "detections" sit inside the upper limits of their own neighbours.** All nine
AllWISE sources within 60″ have W3 *and* W4 `ph_qual` = 'U' — their catalogued values are
95% confidence upper limits. Those limits are **2.07–3.79 mJy in W4** and
**0.31–0.58 mJy in W3**. Candidate I's W4 "detection" is **3.36 mJy** and its W3 is
**0.375 mJy** — both squarely inside the neighbours' upper-limit range, and **the nearest
neighbour (21.3″ away) has a W4 upper limit of 3.79 mJy, brighter than candidate I's
detection.** That is what the local noise floor looks like.

**(c) The W3 excess does not survive the earlier WISE reduction.** The same photons
reduced for the **WISE All-Sky Release** give ph_qual **AAUC** — W3 flagged **'U'**, i.e.
no detection, null uncertainty, S/N 1.3 (`allsky_4band_p3as_psd`, IRSA). AllWISE upgraded
it to 'C' at S/N 2.4. W4 is consistent between the two (All-Sky 8.594 ± 0.366 at S/N 3.0;
AllWISE 8.489 ± 0.326 at S/N 3.3). The AllWISE Explanatory Supplement defines 'U' as
"Source measurement has w?snr<2. The profile-fit magnitude w?mpro is a 95% confidence
upper limit." So one of the two points carrying the entire candidacy is a detection in one
reduction and a non-detection in the other. The All-Sky W3 limit (12.015 = ≤0.496 mJy) is
*brighter* than the AllWISE detection (12.316) and does not even exclude the photosphere
(13.15) — the releases do not contradict each other; they show that at this flux level
WISE's W3 answer depends on the pipeline.

**(d) The independent aperture photometry never detected W4 at all.** `w?flg` describes
AllWISE's *aperture* measurement (`w?mag`), which is independent of the profile fit, and
its documented value **32 = "The magnitude is a 95% confidence upper limit."**

| | AllWISE aperture mag | σ | `w?flg` | verdict |
|---|---|---|---|---|
| W3 | 12.027 | 0.518 | 0 | marginal aperture detection |
| W4 | 7.825 | **null** | **32** | **95% upper limit (≤6.2 mJy) — not detected** |

In the WISE All-Sky Release **both** `w3flg` and `w4flg` = 32: neither aperture measurement
detected the source. This does not contradict the profile fit — the W4 aperture limit
(6.2 mJy) is weaker than the 3.36 mJy profile flux — but it means **only the profile fit
ever produced a "detection" at all.**

**(e) Nothing was detected in individual exposures.** `w?nm` is documented as "the number
of individual 8.8s exposures on which this source was detected with SNR>3 in the
profile-fit measurement". AllWISE: **w3nm = 0**, **w4nm = 1**, against `w3m = w4m = 11`
(full coverage in both bands — this is faintness, not a coverage gap). WISE All-Sky:
**w3nm = w4nm = 0**. `nb = 1`, `na = 0` — a clean, isolated single-PSF fit with no passive
or active deblending, so **nothing nearby was fit simultaneously**. `w3rchi2 = 1.068`,
`w4rchi2 = 1.103`: an acceptable point-source fit, though a near-unity reduced χ² on a
2–3σ measurement discriminates almost nothing. `var_flg` = "11nn" — W3 and W4 = 'n',
"insufficient or inadequate data to make a determination", which follows directly from
w3nm = 0.

**(f) No other facility has ever observed this position longward of 5 µm.** Not "observed
and undetected" — **never observed**. Each null below was validated with a positive
control at a field known to be covered (IRSA's services return byte-identical empty
results for misspelled collection names, so a bare null proves nothing).

| Facility | Result | How established |
|---|---|---|
| **Spitzer** | **not covered** — 0 rows out to 0.25°; no IRAC, MIPS or IRS AOR | IRSA SIA `spitzer_sha`; control at COSMOS returns 106,523 rows |
| **JWST** | **not covered** — 31 observations cover the position (HLSP, GALEX, TESS, PS1, SDSS); **zero JWST** | MAST CAOM TAP footprint test `CONTAINS(POINT, s_region)`; control at COSMOS returns JWST rows |
| **Herschel** | **not covered** — nearest footprint edge 38.3′ | ESA HSA TAP, point-in-polygon on `polygon_fov` for all 160 obs within 5°; four independent routes agree |
| **ISO** | **never observed** (pointed observatory); nearest observation 4.95° away | ESA ISO archive TAP `ivoa.obscore`, 88,595 rows |
| AKARI IRC | non-detection; limits 0.05 Jy (9 µm), 0.09 Jy (18 µm) | region confirmed scanned (12 IRC sources within 1°) |
| IRAS PSC | non-detection; upper-limit floor 0.25 Jy (12 µm), 0.25 Jy (25 µm) | region confirmed scanned (5 PSC sources within 1°) |
| MSX | not covered (b = +40°, outside the Galactic Plane Survey) | IRSA |

The AKARI and IRAS limits are **scientifically vacuous** here — roughly 150× and 670× above
the source's flux. Quote them for completeness, never as constraints. (Note also that
IRAS's tabulated numbers are *completeness* limits, not 10σ limits; the Explanatory
Supplement's per-detection threshold is S/N ≈ 5.7.)

**Everything anyone knows about this object longward of 5 µm comes from WISE's cryogenic
mission — and inside WISE it comes down to two sub-5σ coadd measurements, one of which is
a non-detection in the other release, neither of which was ever seen in a single exposure,
and one of which the independent aperture photometry never detected.**

---

## 4. The centroid evidence, and why it is ambiguous

Method (Ren et al. 2026 §2–3, reproduced in `scripts/w2_centroids.py`): compare the
Gaia position, proper-motion-propagated to the per-band AllWISE mean epoch, against
the mid-IR emission centroid measured on AllWISE Atlas cutouts, with unWISE full-depth
coadds as an independent imaging basis. Centroid uncertainty = FWHM/(2.355·S/N) with
aperture S/N measured against random-aperture scatter. Proper motion moves the star
only 0.088″ between J2016 and the 2010.35 WISE epoch, so epoch propagation is not a
factor here.

| Band | basis | offset | **position angle** | aperture S/N | σ_pos | Ren+26 published |
|---|---|---|---|---|---|---|
| W1 | AllWISE | 0.20″ | 125° | 105 | 0.02″ | 0.24″ |
| W2 | AllWISE | 0.32″ | 124° | 43 | 0.06″ | 0.40″ |
| W3 | AllWISE | **2.64″** | **202°** | 2.4 | 1.15″ | 2.10″ ± 0.62 |
| W3 | unWISE | **4.29″** | **192°** | 1.9 | 1.43″ | — |
| W4 | AllWISE | **5.48″** | **345°** | 5.2 | 0.99″ | 3.22″ ± 2.15 |
| W4 | unWISE | **1.11″** | **121°** | 2.3 | 2.23″ | — |

W1 and W2 are locked on the star to 0.2–0.3″: the machinery works, and the *stellar*
position is not in doubt.

**Why the W3/W4 offsets are not evidence of anything.** Restating M1 more precisely
than M1 did — M1 said the directions "flip" in both bands, which is right for W4 and
wrong for W3:

- **W3 keeps its direction between the two coadd bases (202° vs 192°) but changes
  magnitude by 62%** (2.64″ → 4.29″), and both measurements are at aperture S/N < 2.5,
  where σ_pos (1.15–1.43″) is comparable to the offset itself.
- **W4 flips outright**: PA 345° on AllWISE versus PA 121° on unWISE — a 224° change
  of direction — and the magnitude changes by a factor of 5 (5.48″ → 1.11″). The two
  measurements are not consistent with each other at any level.

At S/N 2–5 the emission cannot be localised; these offsets are noise. This is
consistent with Ren et al. (2026)'s own Rayleigh test, which finds no significant
offsets for I, and with their description of I's W3 emission as "an extended stripe"
whose centroid they took on the SE peak — a choice, not a measurement.

**And the floor is hard.** The JWST-calibrated lesson from candidate D (M1 §3.2,
Hephaistos IV §5.2): a *real* contaminant at 1.0″ separation produced AllWISE centroid
offsets of only ~0.5–1.4″ — below any defensible threshold against the ~0.2–0.5″
control-star floor. Hephaistos IV states it outright: the centroid method "provided no
evidence for interloper contamination in the case of candidate D". **A contaminant
inside ~1–2″ of candidate I would be invisible to every test in this section.** The
centroid axis cannot clear I; it can only ever have condemned it.

---

## 5. The 6.8″ NE red PSF source

From my Legacy Survey DR10 pull (NOIRLab Datalab TAP, `data/photometry/legacy_dr10_I.csv`).
Ren et al. (2026) report no companion within 3″ in Legacy/UKIDSS; my pull confirms
nothing within 6.5″ — and then flags one object just outside that radius.

| | separation | PA | g | r | z | forced W1 | forced W4 |
|---|---|---|---|---|---|---|---|
| the star | — | — | 19.44 | 17.88 | 15.86 | 16.17 | 14.57 |
| **red PSF source** | **6.76″** | **37.4° (NE)** | **25.59** | **24.78** | **20.26** | **19.47** | **14.97** |

(AB magnitudes converted from Legacy's nanomaggy fluxes.) It is independently catalogued
as **SDSS J093954.62+070033.0** (g = 25.50, r = 24.83, i = 22.28, z = 20.12, y = 19.70 —
g − z = 5.4), which confirms the Legacy photometry and adds the i and y bands. It is a
point source with
r − z ≈ 4.5 and z − W1 ≈ 0.8 — the colours of a faint, dusty, high-redshift-galaxy-like
object, i.e. the class JWST found at D and E.

**Caveats, and they are heavy:**

1. **Its W4 brightness is a deblending outcome, not a measurement.** Tractor's forced
   W4 photometry splits one unresolved 12″-beam blob among catalogued optical
   positions. It assigns 1489.9 nmgy (5.41 mJy) to the star and 1023.8 nmgy (3.72 mJy)
   to the red source. The noise on that split is visible in the same file: a third
   source 7.3″ SE is assigned **−390 nmgy (−1.42 mJy)**. So the per-source W4 noise is
   ~1.4 mJy and *neither* the star's nor the red source's forced W4 flux is
   significantly determined. All this file establishes is that ~9 mJy of 22 µm flux is
   somewhere in this beam and Tractor cannot say where. (For comparison, AllWISE
   assigns 3.4 mJy to the star.)
2. **6.76″ is outside the W3 PSF half-width (3.25″)**, though inside the 12″ W4 beam.
3. **Its direction does not match the W4 centroid pull.** The red source is at PA 37°;
   the AllWISE W4 centroid offset is at PA 345° — 52° away, on the other side of north
   — and the unWISE W4 centroid is at PA 121°, nowhere near it. M1 described the red
   source as "on the same side as the northward W4 centroid pull"; that is true only in
   the loosest sense and is corrected here.
4. It is **not** in 2MASS, AllWISE or CatWISE2020 as a separate source — consistent with
   `nb = 1`, `na = 0`: AllWISE fit candidate I as an isolated single PSF and never
   deblended against it.
5. It is not alone. A second faint object, **SDSS J093954.74+070024.6** (SDSS class 3 =
   GALAXY, r = 22.73), lies 7.1–7.3″ SE — the same source whose Tractor-forced W4 flux is
   **negative**. Both objects are inside the 12″ W4 beam and inside AllWISE's 8.25″
   standard aperture, and neither was deblended.

**Assessment: worth one line in a follow-up proposal, and no more.** It is not
evidence today, and it is not the leading contamination hypothesis — a blend inside
1–2″, of the kind JWST resolved at D and E, is, and would be invisible to everything
in this dossier.

---

## 6. Chance alignment, with the corrected density

The arithmetic behind this section is re-derived in `scripts/w2_chance_alignment.py`
and `scripts/m2_note_table.py`; the correction to Ren et al. (2024)'s density is
written up separately in `note-ren24-unit-error-DRAFT.md` (DRAFT, not submitted).

Poisson geometry, P(≥1 within r) = 1 − exp(−ρπr²), against a parent sample of
5 × 10⁶ stars:

| Population | ρ (deg⁻²) | expected among 5 × 10⁶, r = 3.25″ | r = 1.0″ |
|---|---|---|---|
| Ren et al. 2024 **as printed** (the 3600× unit error) | 116.6 | 1493 | 141 |
| Assef et al. 2015 catalogued Hot DOGs, **converted correctly** | 0.0323 | **0.41** | 0.039 |
| Blain 2024 full WISE Hot DOG sample | 0.100 | 1.28 | 0.12 |
| **Suazo et al. 2024 faint red galaxies** (15000 sr⁻¹) | 4.57 | **58.5** | **5.5** |
| *required to produce all seven Heph II candidates* | *0.547 / 5.78* | *7* | *7* |

**Read the last two rows together.** Catalogued Hot DOGs are not the contaminant
class — corrected, they supply 0.41 of the seven. The faint red-galaxy population
that Suazo et al. estimated themselves supplies 5.5 within 1″, against the 5.78 deg⁻²
required. **At the population level chance alignment already accounts for the entire
candidate yield.** No candidate-specific rescue is needed for any of them, I included.

Per-position, at Suazo's density:

| radius | P(≥1 red background galaxy) per star | expected among 5 × 10⁶ | among the 2 × 10⁵ S/N-cut subsample |
|---|---|---|---|
| 1.0″ (the JWST-measured blend scale at D/E) | 1.1 × 10⁻⁶ | 5.5 | 0.22 |
| 2.64″ (I's AllWISE W3 offset) | 7.7 × 10⁻⁶ | 38.6 | 1.54 |
| 3.25″ (W3 PSF half-width) | 1.2 × 10⁻⁵ | 58.5 | 2.34 |
| 6.76″ (the red PSF source) | 5.1 × 10⁻⁵ | 254 | 10.2 |

The last line is the honest verdict on Section 5: a source as red as that one, within
6.8″, is expected ~250 times over in a sample this size. Finding one next to candidate
I is not surprising and is not evidence.

---

## 7. The class prior — and why "archivally clean" means almost nothing

Status of all ten labelled candidates (M1 §1; sources there):

| | candidates | evidence |
|---|---|---|
| **Identified contaminant** | **B, C, D, E, G** (5/10) | radio counterpart at 0.4″ (B); NIR companion at 3.75″ + 3.7″/5.0″ W3/W4 centroid offsets (C); **JWST/MIRI: z ≈ 0.9 AGN-like galaxy at ~1″ (D)**; **JWST/MIRI: z ≈ 0.4 dusty starburst at ~1″ (E)**; EVN T_b > 10⁸ K background AGN (G) |
| Suggestive | A (1/10) | radio counterpart 4.9″ off, α = 0.40 ± 0.35 |
| Ambiguous indications | H, J (2/10) | W3 offset 2.6″ at ~2σ + Legacy PSF source ~5″ NE (H); W3–W4 centroids ~7″ apart, uncatalogued companion (J) |
| **No positive contamination evidence** | **F, I** (2/10) | F: offsets not significant, nearest catalogued source > 5″. I: weakest of all ten on Ren+26's own metric |

The raw count ("9 of 10 show contamination evidence") is the weaker argument. The
strong one is this:

> **Candidate D was the *cleanest* of the ten by archival centroid vetting — Ren et al.
> found its offsets indistinguishable from control stars, and my own measurements
> agree — and JWST destroyed it.** Both candidates JWST has published were contaminated,
> and the archival ranking gave no warning for either.

**A third candidate has already been observed by JWST and the result is not out.** A MAST
query on program **GO 7199** (Cycle 4, PI Zackrisson, 13.5 h, status Completed) returns
**three** targets, not two:

| GO 7199 target | RA, Dec | matches | in Hephaistos IV? |
|---|---|---|---|
| Object_D | 351.96365, +5.10720 | **candidate D** (0.36″) | yes — killed |
| Object_E | 60.53258, −10.91123 | **candidate E** (0.44″) | yes — killed |
| **Object_A** | **191.30390, −26.86784** | **candidate A** (0.95″) | **no — unpublished** |

Object_A was observed **14 July 2026**, four days after Hephaistos IV appeared, and does
not appear in that paper. Candidate A is the one with a *suggestive* radio counterpart
4.9″ off (α = 0.40 ± 0.35). So the JWST sample will shortly be 3, not 2, and the class
prior will get sharper — in one direction or the other — without anyone doing anything.
**This should be watched, and it changes the timing calculus for any proposal on
candidate I.** (Exclusive-access status of the GO 7199 data has not been checked; GO
programs normally carry a 12-month exclusive access period.) Instrument for all three was
MIRI **MRS** (CH1–CH4 × SHORT/MEDIUM/LONG) with MIRI imaging in F560W/F1000W/F1500W
riding along as MRS simultaneous imaging on the background visits.

Archival cleanliness has therefore demonstrated approximately zero predictive value in
this sample. Candidate I's position — "no identified contaminant" — is exactly the
position candidate D occupied on 9 July 2026.

Two asymmetries that should also be on the record, in I's favour:

- I is a **fainter, lower-S/N** object than D was, so its excess is *more* easily faked
  by noise, not less. And unlike D, one of its two excess points is release-dependent.
- I is at |b| ≈ 43°, so Galactic cirrus confusion is low — the W3 "extended stripe"
  Ren et al. describe is more likely instrumental/noise structure than Galactic dust,
  but this has not been tested. (UNSOURCED assessment.)

---

## 8. What would actually settle it

**JWST/MIRI imaging. Two filters, one visit. ≈1.2 h charged. Nothing else works.**

*The design.*

| | |
|---|---|
| Instrument/mode | JWST MIRI **imaging** (not MRS — imaging alone answers the question, and MRS costs several times more) |
| Filters | **F2100W** (21 µm) — where the excess lives; plus **F1000W** or **F1280W** as the photosphere/colour anchor. Keep both in **one observation**: splitting them into two roughly doubles the charge |
| Predicted fluxes | F2100W: **3.36 mJy total**, of which the M-dwarf photosphere is **0.056 mJy** (1.7%) — at 21 µm the excess *is* the source. F1130W/F1280W: total ~0.38 mJy, photosphere ~0.18 mJy |
| Why it resolves the question | Measured on-orbit MIRI PSF FWHM: **0.356″ at F1000W, 0.430″ at F1280W, 0.685″ at F2100W** (0.11″ pixels), against WISE's ~6.5″ (W3) and ~12″ (W4). That is ~17–18× sharper linearly and ~300× smaller in beam solid angle. The ~1″ blends that killed D and E are trivially resolved, well inside the 1–2″ floor of Section 4 |
| Sensitivity margin | MIRI 10σ-in-10 ks point-source limits: **F1000W 0.47 µJy, F1280W 0.85 µJy, F2100W 4.78 µJy** (JDox, ETC 6.0, in-flight). The predicted 21 µm source is **711× the F2100W limit**; even the **bare photosphere** is 11.7× it and reaches S/N = 10 in **~73 s**. Exposure is set by overheads, not depth |
| Saturation | Safe. F2100W bright-source limit is 25.4 mJy (FULL frame) vs 3.36 mJy — 7.5× margin. The real constraint at 21 µm is *background* saturation (only ~32 groups in FASTR1), so use FASTR1 with short ramps |
| Precedent | Exactly this instrument was used on candidates D and E in **JWST GO 7199** (Cycle 4, PI Zackrisson, 13.5 h, completed), and it settled both |

*The cost, honestly.* JWST charges a fixed floor of **2100 s initial slew + 294 s
guide-star acquisition ≈ 40 min** to any single-target observation, plus instrument and
visit overheads, plus a **16% observatory indirect charge**. A one-visit, two-filter,
4-point-dithered observation with 300 s of science per filter comes to **≈4,260–4,380 s ≈
1.2 h charged** — of which science time is 14%. Even with zero science time and no
dithers the floor is **0.87 h**. There is **no documented minimum program size** ("A GO
proposal may be submitted for any amount of observing time"); DD proposals are "typically
small, <15 hours". So ~1.2 h is the real number, not the ~0.5 h one might guess from the
exposure times. *(This corrects an earlier estimate in this dossier.)*

*What each outcome would mean.*

1. **A separate 21 µm source, offset from the proper-motion-propagated Gaia position.**
   → Contamination confirmed. Candidate I joins B, C, D, E, G. The Hephaistos II/III
   candidate list would then be **10/10 accounted for**, which is the calibrated null
   on the method's yield — a real and publishable result, and the one this project was
   set up to be able to deliver. *This is the outcome I expect.*
2. **21 µm emission centred on the star to ≲0.1″, at the predicted ~3.4 mJy.** → The
   excess is real and co-located. This would be the first genuinely unresolved
   extreme-mid-IR-excess M dwarf in the sample. It is *not* a Dyson sphere detection:
   the immediate next question is a debris disk or an unusual circumstellar dust
   population, and the discriminating follow-up is MIRI/MRS — silicate and PAH features
   say dust, a featureless continuum says something that needs explaining. Even at
   T ≈ 100–125 K and γ ≈ 0.09–0.15, γ is a *covering fraction* fitted to two noisy
   points and would need re-deriving from the MIRI photometry.
3. **No 21 µm source above ~0.1 mJy.** → The AllWISE W4 "detection" at S/N 3.3 was a
   noise fluctuation or unresolved background, and the excess evaporates. Because the
   prediction sits so far above MIRI's floor, a null is *decisive*, not merely
   uninformative — this is the outcome the W3 release instability (Section 3a) and
   w3nm = 0 (Section 3b) point toward.

Every one of those three is a result. There is no outcome in which the observation
is wasted, which is the argument a proposal would rest on.

*The honest cost caveat.* JWST time is the scarcest resource in astronomy and this is
a 3.5σ excess on an object the parent survey's own quality cut rejected. The case for
spending it is not "this might be a Dyson sphere" — it is "this is the last object in
a published, widely-covered candidate list that has not been resolved, and closing it
costs half an hour." That is a DDT-scale or small-GO-scale argument, and it is the
only framing that should ever be used.

*A cheaper partial test, if one exists.* Whether Spitzer/MIPS ever covered this
position is checked in `scripts/m2_i_excess.py` (SEIP source list: zero rows within
10″). MIPS 24 µm has a ~6″ FWHM — no better than WISE for resolving a 1″ blend — but
is roughly an order of magnitude more sensitive, so archival MIPS coverage, if it
exists, would independently confirm or refute the 3.4 mJy flux without resolving it.
That would collapse outcome 3 without JWST. **Coverage status: see the coverage note
in Section 11.**

---

## 9. What would *not* settle it

- **Ground-based mid-IR.** The excess is 3.4 mJy at 22 µm and ~0.2 mJy at 12 µm. The
  best available 8-m-class N- and Q-band imagers reach ~1 mJy (N) and ~10 mJy (Q) at
  10σ in an hour under good conditions. Both predicted fluxes are *below* those limits.
  Ground-based mid-IR cannot detect this object at all, let alone resolve it.
- **SPHEREx.** Ends at 5 µm; 6.15″ pixels. Already done (Section 2) — it anchors the
  photosphere and finds no hot component, and that is its whole contribution.
- **Deeper optical/NIR imaging.** The galaxy that killed candidate D was **invisible to
  Legacy DR10**, the deepest wide-field optical survey — my own Legacy pull at D finds
  nothing at ~1″ (M1 §3.2). Deep optical catalogues did not find C's contaminant either
  (NIR-detected only). A non-detection in a deeper optical survey would prove nothing.
- **More WISE analysis.** Both coadd bases have been measured, in both releases. The
  measurement is at the instrument's floor. There is nothing left to extract.
- **Gaia astrometry.** RUWE 0.959 already says there is no astrometric companion; it
  says nothing about a background galaxy.

---

## 10. Finder chart

**`out/m2_I_finder.png`** (`scripts/m2_i_figures.py`, all sources account-free).
Four panels on a common 60″ field, N up / E left:

1. **Legacy Survey DR10 *grz*** (0.262″/px) — the star, and the 6.8″ NE red PSF source
   circled, with a 10″ scale bar and compass.
2. **AllWISE W1** (3.4 µm, S/N 44) — the star, unambiguous.
3. **AllWISE W3** (12 µm, S/N 2.4) — with both measured centroids (AllWISE and unWISE)
   and the 6.5″ PSF FWHM circle. The disagreement is visible by eye.
4. **AllWISE W4** (22 µm, S/N 3.3) — same, with the 12″ beam.

The Gaia position is proper-motion-propagated to the per-band WISE epoch in every
panel.

---

## 11. Provenance, artifacts, and open caveats

**Scripts** (all in `scripts/`, all account-free, nothing sent externally):
`w1_fetch_candidates.py`, `w1_selection.py` (the reproduced cuts),
`w1_fetch_locus.py` (photospheric template), `w2_centroids.py` (centroids),
`w2_sed.py` (archival SED), `w2_chance_alignment.py`, `w3_spherex.py` (SPHEREx),
**`m2_i_excess.py`** (flux-space excess + archival mid-IR probes, new in M2),
**`m2_i_figures.py`** (finder chart + dossier SED, new in M2),
**`m2_note_table.py`** (density table, new in M2).

**Artifacts:** `out/m2_I_finder.png`, `out/m2_I_sed.png`, `out/m2_I_excess.json`,
`out/w2_centroid_offsets.csv`, `out/w2_sed_fits.csv`, `out/w2_chance_alignment.csv`,
`out/w3_spherex_I_sed.csv`, `out/w1_acceptance.csv`, `out/m2_note_table.csv`.

**Open caveats, stated so they are not lost:**

1. **The Gaia Hα sign convention (Section 1) is unverified.** It does not change I's
   status, but it may affect cut C5a across the W4 screen.
2. ~~The AllWISE `w4flg = 32` bit meaning is unverified.~~ **RESOLVED**: the AllWISE
   Explanatory Supplement defines 32 as "The magnitude is a 95% confidence upper limit",
   and `w?flg` refers to the *aperture* measurement, not the profile fit. Section 3d.
3. ~~Spitzer coverage vs non-detection is unresolved.~~ **RESOLVED**: the position is in
   **no Spitzer footprint** out to 0.25° (IRSA SIA `spitzer_sha`, validated against a
   positive control). There is no cheap archival substitute for the JWST observation.
   Section 3f.
6. **Approved-but-unexecuted JWST programs could not be checked.** MAST CAOM holds
   executed observations only, and there is no account-free way to search all approved
   target lists by coordinate. What is established: no *executed* observation from any
   program covers this position, and no Zackrisson program targets it.
4. **`γ` should not be quoted as a covering fraction.** Both the published (0.147) and
   my (0.085) values are fits to two points, one of which is release-dependent. The
   published uncertainty (±0.046) does not include that instability.
5. **This dossier argues for an observation, not for a detection.** Nothing in it is
   evidence *for* a Dyson sphere, and it should never be summarised as though it were.
