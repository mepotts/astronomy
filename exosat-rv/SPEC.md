# SPEC — exosat-rv

## The claim under test

Hoy et al. 2026, *Planetary-Mass Exosatellite Detected Around the Substellar Companion of a
Star* ([arXiv:2607.05193](https://arxiv.org/abs/2607.05193), submitted 2026-07-06;
[Nature](https://www.nature.com/articles/s41586-026-10751-w), 2026-07-22).

VLT/CRIRES+ spectra of the directly imaged brown dwarf **CD-35 2722 B** show a periodic
Doppler signal attributed to an orbiting satellite: m·sin i = 0.743 M_Jup at 169.45 d, plus
a less certain second candidate at 0.277 M_Jup / 87.46 d, near a 2:1 resonance. The
hierarchy is star → brown dwarf → satellite. It is the first time radial velocity has
produced evidence of a satellite anywhere.

## Why the method works, and why that generalises

The enabling physics is the mass ratio. K scales as M_host^(-2/3), so the reflex velocity of
a **37 M_Jup** host under a Jupiter-mass satellite is ~250 m/s semi-amplitude — an enormous
signal, ~8x the paper's mean per-epoch error. A satellite around a *stellar*-mass host is
hopeless; around a substellar one it is easy. This is why 20 epochs sufficed.

The corollary drives M5: the scaling keeps improving as hosts get lighter. At the paper's
31.44 m/s precision, a 5 M_Jup young giant planet would reveal a **~19 M_Earth** satellite.
Signal amplitude is not the limiting factor for satellite RV — **flux and angular
separation are**:

- **Flux.** RV error scales ~1.585x per magnitude. CD-35 2722 B is near the bright end of
  imaged companions; H ~ 15 targets (DH Tau b, kappa And b, both measured) remain workable,
  H > 17 (51 Eri b at 18.99) do not on an 8 m.
  **Unverified:** CD-35 2722 B's own H magnitude. It is estimated at ~14 from an L4 type at
  22.36 pc, but the preprint does not state it and SIMBAD does not resolve the companion
  separately. M5's flux cut is calibrated against this number, so it must be sourced from
  the 2011 discovery paper before the cut is trusted. Flagged in HANDOFF.
- **Separation.** CD-35 2722 B sits 2.8" from its primary, wide enough for a slit aligned
  perpendicular to the axis, holding contamination to 13-15%. Companions inside ~0.5" need
  fibre-fed high-contrast spectroscopy (VLT/HiRISE, Keck/KPIC) — a different instrument and
  a different archive, and out of scope here.

## What this project is

**An independent reproduction, not a re-run.** Three things make it worth doing:

1. **The dataset is public.** M0 measured that the preprint's 20 epochs are exactly the 20
   public H-band CRIRES+ nights, and 17 of them already exist as ESO pipeline-reduced 1-D
   spectra. The reproduction is not gated on telescope time or on rebuilding cr2res.
2. **The inference can be made genuinely independent.** The paper used `EMPEROR`; this uses
   `radvel`. Extraction still uses the paper's own `viper` — forward-modelling RV
   extraction is not credibly reimplemented — so independence is claimed at the inference
   stage only, and claimed no more broadly than that.
3. **There is a real open question in the data, and the paper names it.** The *existence*
   of a second satellite is reasonably supported (delta-log-Z = 6.9 over an eccentric
   one-satellite model). Its *period* is not. The preprint states outright:

   > "There are 4 possible solutions at periods of 14 days, 70 days, 88 days, and 115 days.
   > These periods are all aliases of each other with our current sampling, due to the two
   > sets of observations being almost exactly a year apart."

   The favoured 88-day model beats the 115-day one by only delta-log-Z = 2.6, and the 88-day
   periodogram peak sits *just* above the 1% FAP threshold. That is a sampling-induced
   degeneracy, and a reanalysis can attack it from the same public data — spectral window
   function, and injection-recovery across the alias family — without new observations.

   **What this project must NOT claim as a gap:** that the second signal might be a harmonic
   of an eccentric 169-day orbit. The paper fits that model explicitly (e = 0.29, Table 1),
   cites the known 2:1-MMR/eccentricity degeneracy, and rejects it. An earlier draft of this
   SPEC framed M4 that way; M1 read the source and corrected it.

## Honest prior-art assessment

- **This is not a novel method, and the analogue survey is not white space.** The technique
  is the paper's, and it has a documented prior literature that M7 finally read in full
  (`papers/`). **Two corrections, the second found only in M7 by reading Hoy et al.'s own
  reference list:**

  1. Earlier drafts cited the GQ Lup B exosatellite search at arXiv:2408.10299 as a
     viper/CRIRES+ precursor. It uses **Keck/KPIC**, a different instrument.
  2. That paper is **Horstman et al. 2024**, not "Köhler et al. 2024" — Köhler is not an
     author on it at all. And it is **not** the first dedicated RV exosatellite search
     around a directly imaged companion: **Ruffio et al. 2023** (HR 7672 B, AJ 165 113,
     arXiv:2301.04206) and **Vanderburg & Rodriguez 2021** (HR 8799, arXiv:2110.14650)
     both precede it, and **Vanderburg, Rappaport & Mayo 2018** (arXiv:1805.01903)
     proposed the method. Three published nulls existed before Hoy et al.'s detection;
     SPEC previously named one of them, under the wrong author, with the wrong priority.

  The relevant Köhler paper is the viper instrument paper,
  [arXiv:2505.08315](https://arxiv.org/abs/2505.08315), A&A 698 A44 (2025). M5 measured the
  archive and found the shape of the programme behind it: **110.23RW** (Nov 2022 – Feb 2023)
  is a pilot across AB Pic B, beta Pic B and CD-35 2722 B; every later programme (112.25HG,
  114.271E, 116.2AP9) is CD-35 2722 B alone. **The same group is already running the survey
  M5 imagines.** Anything M5 produces is a reanalysis of their data, not an independent
  search, and must be described that way.
- **The detectability of this method was forecast before it worked, and the forecast is
  citable.** Hoy et al. cite **Lazzoni et al. 2022** (MNRAS 516 391,
  arXiv:2207.07569), by four of their own co-authors, which simulates satellite populations
  around 38 directly imaged companions and predicts that *binary-like* satellites are
  detectable by RV (P ~ 0.996 at f = 1) while *planet-like* ones are not (P ~ 0.08). M7
  reproduces that split and recalibrates its threshold on the real detection.
- **A second, independent exosatellite candidate now exists, by astrometry.** Blunt et al.
  2026 ([arXiv:2511.20091](https://arxiv.org/abs/2511.20091), A&A) report tentative
  VLTI/GRAVITY astrometric residuals around **HD 206893 B** consistent with a ~0.4 M_Jup
  companion at P ~ 0.76 yr, and flag them as possibly systematic. Two tentative candidates
  around substellar companions, by two techniques, inside a year. Any framing of Hoy et al.
  as a lone result is out of date. See [`M7-RESULTS.md`](M7-RESULTS.md) §6b.
- **Reproductions rarely overturn detections, and should not be framed as trying to.** The
  169 d signal has a fitted amplitude of 246.45 m/s against ~31 m/s per-epoch errors. The
  realistic outcomes are: it reproduces (most likely and worth recording), or the second
  signal's *period* proves to be sampling-driven rather than data-driven (plausible, and the
  genuinely useful result).
- **The accepted version may already have moved.** The v1 disclaimer says "which of the
  presented satellite models is favored ... [has] meaningfully changed." It is entirely
  possible the alias degeneracy is what moved. This project cannot know until the
  Dec-2025-onward frames are public in 2027.
- **The analogue survey will most likely produce upper limits.** There is precedent for
  publishing exactly that — [astrometric limits on beta Pic b satellites](https://arxiv.org/abs/2512.00160)
  (2025) — and limits on satellite mass around imaged companions are a real contribution.
  Framing M5 as a discovery hunt would be dishonest about the base rate.

## Scope added after M6, and how it is labelled

The reproduction is a *prerequisite*, not the goal — the goal is to find or bound a **new**
exosatellite. Four milestones extend the project toward that, and they are not all equal in
standing:

- **M7 (generalisation) and M10 (astrometric route) are on the main line.** Both stay within
  "apply the same method to substellar-companion analogues", both are archive-first, and both
  serve the goal directly.
- **M8 (young close-in giants) is a spur, and is labelled one.** It is not ESO archive data,
  not CRIRES+, not a reproduction of anything, and its observable is cross-correlation
  spectroscopy rather than slit spectroscopy of a resolved companion. It answers a real
  question and it is not the same project. Do not let it drift into the main sequence.
- **M9 and M11 are diagnostic**, both negative, both aimed squarely at the prerequisite.

## Non-goals

- No discovery claim, and no submission of one anywhere.
- No re-derivation of the *Nature* numbers. Those rest on frames embargoed to 2027.
- No exomoon nomenclature argument. Whether a 0.74 M_Jup body orbiting a 37 M_Jup body is a
  "moon" is a definitional question this project has no data to settle, and the authors
  chose "exosatellite" for exactly that reason.
