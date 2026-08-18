# DRAFT — Research Note of the AAS, for Matthew's decision. NOT SUBMITTED.

> **Status: prepared, not submitted.** Submission is outward-facing and irreversible, this
> project's own rules (`LESSONS.md` §6) gate it to Matthew, and the agent that prepared this
> holds no journal credentials. Nothing here has been sent anywhere.
>
> Every number below is printed by [`scripts/m32_etatel_numbers.py`](../../scripts/m32_etatel_numbers.py)
> from `data/m15-limit.json` — none is hand-transcribed, because the repo's own audit found
> 34 conflicting values that entered exactly that way. Re-run it before submitting and diff.
>
> **Blockers are listed at the bottom.** Read those first.

---

**Title:** First Radial-Velocity Constraints on the Brown Dwarf Companion η Telescopii B

**Authors:** Matthew Potts (affiliation TBD; ORCID TBD)

---

## Abstract

*(Required by RNAAS since May 2020.)*

We present the first radial-velocity constraints on η Telescopii B, an M7–M8 brown dwarf
companion at 4.2″ from the A0V star η Tel, derived entirely from public CRIRES+ archival
data: 20 epochs in the H1567 setting spanning 18 nights and 815 days, reduced by two
independent routes that agree at 127–130 m s⁻¹ per-epoch scatter. No periodic signal is
detected. Injection–recovery through the full pipeline returns 99–101 ± 1% of the injected
amplitude, and a detection criterion whose false-alarm probability is measured at ≤ 0.85% by
permutation yields 90% exclusion limits of m sin i ≈ 0.51–1.27 M_Jup for satellites with
P = 20–300 d. Because η Tel B's own orbit is near edge-on (i ≈ 79–82°), these are true-mass
limits to within 2% for any satellite orbiting near the companion's orbital plane. The
constrained periods correspond to 0.05–0.31 au, a region inaccessible to the high-contrast
imaging surveys that constrain satellites only beyond ~1–5 au.

---

## Body

η Telescopii B is an M7–M8 brown dwarf companion at 4.199 ± 0.015″ projected separation
(Chai et al. 2024) from the A0V star η Tel, a member of the β Pictoris moving group. It is
well studied photometrically, spectroscopically and astrometrically — a 25-year astrometric
baseline and, recently, an 11–21 μm JWST/MIRI spectrum — but to our knowledge **no
radial-velocity measurement of it has been published**. We report the first, derived entirely
from public archival data. The system inverts the usual arrangement: HARPS velocities exist for
the *primary* but are unusable, scattering at 12.8 km s⁻¹ because η Tel A is a young, rapidly
rotating A0V star, and the most recent orbital analysis omits them for that reason (Chai et al.
2024). The faint companion, not the bright host, is the viable radial-velocity target here.

Radial-velocity monitoring of a directly imaged companion's own spectrum is an established
route to constraining massive satellites. Searches have been reported for the HR 8799 planets
(Vanderburg & Rodriguez 2021), HR 7672 B (Ruffio et al. 2023), GQ Lup B (Horstman et al. 2024)
and β Pictoris b (Kenworthy et al. 2026), all null, alongside astrometric limits from
interferometry (Macias et al. 2026; Kral et al. 2026). Against that run, Hoy et al. (2026)
reported the first detection, around CD-35 2722 B — which sharpens rather than settles how
common the configuration is, and makes each further constrained system worth having.

η Tel B is the only other object in the accessible class with an archival CRIRES+ series long
enough to constrain an orbit, and it was observed in the **identical H1567 setting** as
CD-35 2722 B, so that reduction transfers unmodified. At ~47 M_Jup it also extends the sample
into the brown-dwarf host regime, with HR 7672 B.

**Data.** We use 20 public CRIRES+ H1567 epochs of η Tel B spanning 18 nights and 815 days
(ESO programmes 111.24M0, 113.268Y, 115.287U). We reduce them twice by independent routes:
from the archive's reduced products, and from raw frames through the full `cr2res` cascade
with per-nodding extraction. Radial velocities come from `viper` (Köhler et al. 2025) in its
cell-free configuration, using telluric lines as the wavelength reference, over an
eleven-order set selected for telluric density. Both routes give **127–130 m s⁻¹** per-epoch
scatter, on an object of K_s = 11.6 ± 0.1 (Neuhäuser et al. 2011).

**The measurement is of the companion.** At 4.2″ against a delivered spatial PSF of 0.37″,
measured from the extraction's own slit function, the pair is separated by 11.3 resolution
elements. The check is not incidental: companions inside one resolution element yield a
spectrum that is the host's, while every downstream diagnostic — precision, order-to-order
dispersion, injection recovery — nonetheless improves. η Tel B is unambiguously resolved.

**Validation.** Because no published RV exists for this target, there is nothing to check
against, so the entire validation burden falls on injection–recovery. We inject a Keplerian
by shifting the *template*, never the observation, and re-run the complete pipeline per
epoch. Recovery is **99–101% ± 1%** of the injected amplitude with 12–23 m s⁻¹ residual
scatter, and every individual order transmits at 95–108%; the per-nodding route independently
returns 100% ± 3%. An injected series assembled from those runs is recovered by the same
blind period search that returns the null, at rank 1 and the correct period. The pipeline
detects what it is given.

**Result: no detection.** Across the 150–300 day window — where a CD-35 2722 B analogue would
lie — every ΔBIC is negative on both extraction routes. The strongest features are
short-period (5–12 d) and inconsistent between routes and between combination methods,
characteristic of sampling aliases rather than signal; Hoy et al. discard periods this short
on the same grounds. The null is not a sampling artefact: on this cadence only 11% of the
5–460 d period grid is degenerate with the barycentric velocity, and the 150–300 d decade is
completely clean.

**Sensitivity.** We add a circular-orbit signal to the real series, marginalize over 12
phases, and require ΔBIC ≥ 10 *and* rank 1 at the injected period. That criterion's
false-alarm probability is ≤ 0.85% at every period tested — the rank-1 clause, not the ΔBIC
bar, carries the protection.

| Period (d) | K₉₀ (m s⁻¹) | m sin i limit (M_Jup) |
|---:|---:|---:|
| 20 | 300 | 0.51 |
| 60 | 250 | 0.61 |
| 120 | 250 | 0.77 |
| 200 | 300 | 1.11 |
| 300 | 300 | 1.27 |

*90% detection probability, companion mass 47 M_Jup (Lazzoni et al. 2020). K₉₀ is read off
the measured detection grid — the smallest injected amplitude reaching 90% — not interpolated
or fitted.*

**These are the first radial-velocity constraints of any kind on η Tel B**, and they exclude
sub-Jupiter to Jupiter-mass companions across most of the 20–300 day range. They sit
comfortably alongside the published sample: Kenworthy et al. (2026) reach 1 M_Jup at
P = 200 d on β Pic b from a dedicated campaign at 160 m s⁻¹ mean precision, against
1.11 M_Jup at the same period here from archival data at 127–130 m s⁻¹.

These limits also probe a region no imaging survey reaches. For a 47 M_Jup host, P = 20–300 d
corresponds to **0.05–0.31 au**, whereas the dedicated SPHERE star-hopping survey of twelve
directly imaged companions constrains satellites only beyond ~1–5 au (Lazzoni et al. 2026).
The two techniques do not overlap, and the reason is generic: astrometric amplitude scales as
the satellite's semi-major axis while radial-velocity amplitude scales as a^(−1/2), so
imaging and astrometry own the wide orbits and RV owns the close ones (Macias et al. 2026).

The limits are on m sin i, but in this system that costs almost nothing. η Tel B's own orbit
about η Tel A is near edge-on — i = 79 (+5/−6)° (Chai et al. 2024, stable across five
independent fit configurations) and 81.9° from a separate analysis (Nogueira et al. 2024). A satellite formed in a circum-companion disc would be expected to orbit near that
plane, and if it does, sin i ≈ 0.98 and **the tabulated limits are true-mass limits to within
2%**. This is an assumption, not a measurement, and a strongly misaligned satellite would
evade the constraint — but it is the same near-edge-on geometry that motivates β Pic b as an
RV target (Kenworthy et al. 2026), and the same coplanarity expectation under which the
CD-35 2722 B satellite is interpreted.

A twin of the CD-35 2722 B satellite (m sin i = 0.918 M_Jup) would produce K ≈ 540 m s⁻¹ at 20 d falling to
≈ 217 m s⁻¹ at 300 d, and would have been detected in ~100% of trials at short periods but
only 42–83% at 200–300 d. The non-detection is therefore decisive below ~120 d and merely
suggestive at the period where the one known example actually sits.

**Caveats.** The 90% contour is grid-pointwise rather than a continuous exclusion curve, and
assumes circular orbits. The mass of η Tel B is itself disputed, and m sin i scales as
M^(2/3): evolutionary-model fits give 47 (+5/−6) M_Jup (Lazzoni et al. 2020) while the
JWST/MIRI atmospheric fit gives 29 (+16/−13) M_Jup (Chai et al. 2024). The two dynamical
posteriors that sit between them, 42 ± 14 and 48 ± 15, both use priors traceable to the
former and are described by their own authors as prior-driven, so they are not independent
evidence. We adopt 47 M_Jup, the conservative choice — the atmospheric mass would deepen
every limit in the table by 27%. The exclusion remains sub-Jupiter to Jupiter-mass across the
full range, so the disagreement changes the numbers but not the conclusion.

Eight archival epochs from 2009 on the original CRIRES, and embargoed 2025–26 K-band epochs,
remain unexploited and would extend the baseline substantially.

*Software:* `cr2res`, `viper` (Köhler et al. 2025), `astropy`, `numpy`, `scipy`. All
reduction and analysis code, the injection harness, and the sensitivity grid are public at
[github.com/mepotts/astronomy](https://github.com/mepotts/astronomy) (`exosat-rv/`).
This work is based on observations collected at the European Southern Observatory under
ESO programmes 111.24M0, 113.268Y and 115.287U.

---

## References

- Chai, Y. et al. 2024, *ApJ*, "A JWST MIRI MRS View of the η Tel Debris Disk and its Brown
  Dwarf Companion", arXiv:2408.11692
- Dorn, R. J. et al. 2023, *A&A*, **671**, A24 (CRIRES+)
- Horstman, K. et al. 2024, GQ Lup B RV exosatellite search
- Kenworthy, M. A. et al. 2026, *MNRAS*, "Upper limits on exosatellites around β Pictoris b",
  arXiv:2606.04685
- Kral, Q. et al. 2026, *A&A*, exomoon search around HD 206893 B with VLTI/GRAVITY
- Lazzoni, C., Zurlo, A., Desidera, S. et al. 2026, *A&A* (SaNDi-SHoP I), arXiv:2603.24796
- Macias, I., Jenkins, S. A. & Vanderburg, A. 2026, *AJ*, **171**, 197
- Hoy, K. et al. 2026, *Nature*, "Satellite Detected Around a Star's Substellar Companion",
  doi:10.1038/s41586-026-10751-w
- Köhler, J. et al. 2025, *A&A*, **698**, A44 (viper), doi:10.1051/0004-6361/202553919
- Lazzoni, C. et al. 2020, *A&A*, **641**, A131
- Neuhäuser, R., Ginski, C., Schmidt, T. O. B., & Mugrauer, M. 2011, *MNRAS*, **416**, 1430
- Nogueira, P. H., Lazzoni, C., Zurlo, A. et al. 2024, *A&A*, "Astrometric and photometric characterization of η Tel B combining two decades of observations", arXiv:2405.04723
- Ruffio, J.-B. et al. 2023, *AJ*, **165**, 113
- Vanderburg, A. & Rodriguez, J. E. 2021, *ApJ*, **922**, L2

*(Verification status per `docs/REFERENCE-AUDIT.md`. Hoy, Köhler and Chai are checked against
full copies archived in `papers/`. Dorn is corroborated via Hoy et al.'s reference [11];
Neuhäuser against the MNRAS record — both photometry and mass range quoted verbatim from it.
Lazzoni et al. 2020 is cited via Chai et al. 2024 §5, which attributes the 47 (+5/−6) M_Jup
AMES-COND mass to it; **obtain the paper itself before submitting.**)*

---

## BLOCKERS before this can be submitted

**Matthew's calls — nothing below can be resolved by an agent:**

1. **Do you want to publish this at all?** It is a null result with a limit. It is genuinely
   first-of-its-kind for this object, and it is also small. It may be worth more as a section
   of the full method paper (`docs/paper/draft.template.html`) than as a standalone note.
   Publishing separately does not preclude the paper, but does mean self-citing.
2. **Author list, affiliation, ORCID.** RNAAS accepts independent affiliations.
3. **AAS account.** RNAAS submission requires one; there is a fee-waiver path for
   non-members but it must be requested.

**resolved in M32 — recorded here so the work is not repeated:**

4. ~~The 47 M_Jup mass is single-source and unarchived~~ — **run down.** The repo attributed
   it to "Lazzoni T1 → Langlois et al. 2021b"; Chai et al. 2024 attributes it instead to
   **Lazzoni et al. 2020, A&A 641, A131**, AMES-COND models, **47 (+5/−6) M_Jup**. Chai's own
   MIRI atmospheric fit gives **29 (+16/−13)**, and their orbital posterior 42 ± 14 is
   explicitly "largely prior-driven" and so not independent. The note now quotes the
   disagreement and its 27% effect rather than a bare number. *Residual task: obtain Lazzoni
   et al. 2020 itself — the attribution is currently second-hand through Chai.*
5. ~~K = 13.2 conflicts with SIMBAD H = 11.93~~ — **resolved against 13.2.** Neuhäuser et al.
   2011 measures J = 12.06 ± 0.19, H = 11.75 ± 0.10, **K_s = 11.6 ± 0.1**, L = 11.1 ± 0.2.
   SIMBAD's H agrees; Lazzoni's Kp = 13.2 is wrong by 1.6 mag. The note now quotes K_s = 11.6
   with its source, and the "beats the forecast" claim has been **deleted** — that forecast
   was computed from the wrong magnitude, and at the true brightness the achieved precision
   probably does not beat a corrected one. See M30 for the repo-wide consequences.
6. ~~Confirm no prior RV exists~~ — **as close to settled as it can get without ADS.** The
   decisive evidence is Chai et al. (2024), the dedicated η Tel B characterization paper: it
   performs a full orbital fit and states that the only RV data in the system is HARPS
   velocities of η Tel **A**, unusable at 12.8 km s⁻¹ rms, which it therefore omits. That is
   precisely the paper that would cite a companion RV if one existed. Lazzoni et al. (2020),
   SaNDi-SHoP (2026) and Kenworthy et al. (2026) likewise cite none.
7. ~~Obtain Lazzoni et al. 2020 directly~~ — **done.** Archived
   (`papers/text/lazzoni2020_disks_satellites.txt`); its Table 2 gives η Tel B **47 (+5/−6)
   M_Jup**, age 24 ± 5 Myr, sep 4.21″ first-hand.
8. ~~AAS fee/membership~~ — **not a gate.** RNAAS carries **no publication charge** and AAS
   membership is **not required** to submit. A free submission account is all that is needed.

**Still to do — all of it yours:**

9. **Register an ORCID** (orcid.org, free, ~2 min) and fix the affiliation line.
10. **Re-run `scripts/m32_etatel_numbers.py` and diff against the table above** — a 60-second
    check that the manuscript matches the data before it leaves the building.
11. **Submit.** Deliberately not done here: outward-facing, irreversible, gated to you by
    `LESSONS.md` §6, and no agent in this repo holds credentials for it.

**Word count:** body is ~1,000 words against RNAAS's 1,500 limit, with one table and no
figure — within limits, with room for a sensitivity-curve figure if preferred.
