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

- **This is not a novel method.** The technique is the paper's. Applying RV to directly
  imaged companions has an explicit precursor in the same group — a
  [GQ Lup B exosatellite search](https://arxiv.org/abs/2408.10299) (Köhler et al. 2024, a
  co-author here) — which found no satellite. That null result is the honest prior for M5.
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

## Non-goals

- No discovery claim, and no submission of one anywhere.
- No re-derivation of the *Nature* numbers. Those rest on frames embargoed to 2027.
- No exomoon nomenclature argument. Whether a 0.74 M_Jup body orbiting a 37 M_Jup body is a
  "moon" is a definitional question this project has no data to settle, and the authors
  chose "exosatellite" for exactly that reason.
