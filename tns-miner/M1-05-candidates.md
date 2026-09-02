# M1-05 — Candidate list (Matthew-gated, nothing reported)

**Date:** 2026-08-24 ·
`out/m1_candidates_recent.csv` (184 rows) · `out/m1_candidates_gapwin.csv` (6 rows)

> ## NOTHING IN THIS LIST HAS BEEN REPORTED TO ANYONE
> No discovery report, no classification, no bulk report, no sandbox submission.
> No account was created anywhere. Every row carries
> `STATUS = MATTHEW-GATED -- NOT REPORTED TO TNS`.
> Reporting is Matthew's decision and Matthew's step (`M1-06`).

## The pass

| | |
|---|---|
| window | MJD **61274 – 61277** (nights of 2026-08-21 → 2026-08-24) |
| enumeration | ALeRCE new-object `firstmjd` window ∪ Fink `latests` class=Unknown (1000 newest) |
| pool | **2,924** unique ZTF objects |
| pass a sane real-transient hygiene gate | 208 |
| pass the targeted channels | 189 |
| minus objects already in TNS within 3″ | −5 |
| **candidates** | **184** |
| of which in the galactic plane (\|b\| < 15°) | 124 |

Per-object columns: position, galactic latitude, channel and the reason it passed,
magnitude and band at the passing epoch, outburst amplitude, 60-day peak-to-peak,
nearest catalogued source and separation, `distnr`/`magnr`, `drb`, SIMBAD class,
nearest TNS object and its separation, the full detection history as
`MJD band=mag`, a Fink portal link, and a plain-language one-liner.

## The honest headline: **184 is not 184 good candidates**

The fresh pass exposed something the positive control structurally could not.
DCAP's objects were genuine outbursts, so recovering them says nothing about what
*else* the filter lets through. On live data it lets through a lot:

- **outburst amplitude** (`magnr − magpsf`; positive means the new light outshines
  the quiescent source) has a **median of −1.15** across the 184. Most "candidates"
  are variations *fainter* than the star they sit on — ordinary low-amplitude
  variability on point sources that simply happen to be absent from VSX, GCVS and
  SIMBAD. Only **7 have amplitude ≥ 1.0** and **4 have ≥ 1.5**.
- the median candidate has **160 previous ZTF alerts**. These are long-known ZTF
  sources, not new transients.
- **22 have a flat difference-image light curve** — constant magnitude *within
  each filter* for weeks. That is the signature of a source *missing from the
  reference image*, producing a permanent positive residual. It passes every
  pre-registered cut: high `drb`, positive subtraction, ≥2 detections 30 min
  apart, stellar association, no catalogue match.

> **A trap paid for here, and it nearly went into this document.** The first
> version of the variability diagnostic took peak-to-peak across *all* filters at
> once. A source that is perfectly constant but has g − r = 1.5 then reads as a
> 1.5-magnitude variable. `ZTF26aabkpvd` — a 6.76-mag apparent amplitude at
> r = 14.4 — was written up as the single best candidate in this list on exactly
> that error. Computed **per band** it is flat to **0.11 mag**: a source missing
> from the reference image, not a transient. Any variability measure on ZTF
> difference photometry has to be per-`fid`.

**The pre-registered filter has no amplitude requirement and no variability
requirement.** That is a real gap and it is stated here rather than papered over
by quietly re-tuning after the fact. The thresholds stay frozen; what is added is
a *declared post-hoc ranking*, not a filter change, and every passing object
remains in the CSV.

### The triage rule (stated, applied after the filter, changes no threshold)

- **flat override** — ≥3 alerts in the 60 days ending at the last detection with
  peak-to-peak < **0.3 mag** → tier C regardless of amplitude. 0.3 mag is below
  ZTF's own scatter at mag ~20, so there is no variability left to claim.
- **tier A** — amplitude ≥ 1.5 mag, or channel `A2`/`B` (no quiescent source to
  measure against), and not flat.
- **tier B** — amplitude 0.5 – 1.5 mag, not flat.
- **tier C** — everything else: passes the filter, weak on its face.

**Result: tier A = 3, tier B = 5, tier C = 176** (22 of the tier-C rows are
flat residuals).

Read tiers A and B. Tier C is kept for completeness and for the M2 precision test,
not because those rows are worth a report.

## The three most interesting

**1. `ZTF18abobdzu` — 18:12:49.55 −04:47:08.8 (273.2065, −4.7858), |b| = +6.35°**
**In the galactic plane**, where 94% of TNS reporting never goes. A Pan-STARRS
point source 0.49″ away, amplitude **1.54 mag** above quiescent, and — measured
per band — **1.01 mag peak-to-peak across 26 g-band alerts in the last 60 days**,
on top of a 700-alert history. Genuinely varying, large-amplitude, in-plane,
uncatalogued in VSX, GCVS, SIMBAD and TNS. The best **dwarf nova** candidate in
the list on light-curve shape, and it sits exactly in the gap `M1-02` measured.

**2. `ZTF19acbplek` — 17:48:04.23 +08:03:39.8 (267.0176, +8.0611), |b| = +17.7°**
Amplitude **4.17 mag** over a reference source 0.11″ away at magnitude 21.9. Its
51-alert history is not flat and not periodic: 19.25 → 17.7 in 2020, quiet at
~18.8, and now back up to 17.84. **Recurrent large-amplitude outbursts on a faint
blue point source** is the dwarf-nova signature, and nothing catalogues it. Only
two alerts in the last 60 days, so the recent variability is unconstrained — that
is what to check first.

**3. `ZTF18abbsyyw` — 19:09:50.09 +03:55:32.2 (287.4587, +3.9256), |b| = −2.29°**
Tier B on amplitude (0.99 mag) but **deep in the plane at |b| = −2.3° and bright
at r = 16.4**, with 0.92 mag peak-to-peak across 28 r-band alerts in 60 days out
of a 210-alert history. Bright, in-plane, varying by ~1 mag, uncatalogued —
precisely the object class the survey pipelines never report and the periodogram
classifiers discard.

Also worth a look: `ZTF19aaxsbas` (18:49:04.39 −05:34:05.3, |b| = −2.0°, g = 19.1,
amplitude 1.04) and `ZTF18abbdqqd` (18:54:40.89 +12:06:25.3, |b| = +4.8°,
r = 17.7, 0.94 mag ptp over 1,017 alerts).

## Channel B (M31 / M81) returned nothing, and the reason is seasonal

Zero candidates from either field, because **there is nothing to enumerate right
now**: ALeRCE reports **0 new ZTF objects in the last 60 days** within 1.5° of M31
or 0.5° of M81. Over the last 365 days the M31 field produced 173, and their
monthly distribution is the explanation —

| 2025-08 | 09 | 10 | 11 | 12 | 2026-01 | 02–03 | 04 | 05 | 06 | 07 | 08 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 42 | 29 | 8 | 19 | 11 | 0 | 8 | 37 | 9 | **0** | **0** |

M31 (RA 10.7°, Dec +41.3°) is a September-to-January object and M81 (RA 148.9°,
Dec +69.1°) a February-to-May one. **Late August is the worst week of the year for
both.** The channel is not broken; it is out of season, and M31 reopens within
about a fortnight. Point M2 at it in September.

## The historical window, for contrast

`out/m1_candidates_gapwin.csv` is the same pipeline on MJD 61241–61243
(2026-07-20/21), five weeks old, so every TNS report for it has landed. Six
candidates survive (3 tier A, all channel `A2`); the strongest is
**`ZTF26abipxqv`** (18:18:29.59 −09:14:44.6) at |b| = +3.0°, mag 18.2 g, nothing
in PS1 within 3.65″, brightening from r = 19.25 to g = 18.22 over four days —
nova-shaped, in the plane, and still absent from TNS five weeks later.

## Caveats that must travel with this list

1. **Nothing here has been eyeballed.** No cutout triplet has been looked at. The
   classic ZTF false positives — bad subtractions near bright stars, ghosts,
   diffraction spikes — are invisible to a filter that never sees an image.
2. **No pre-discovery non-detection.** A TNS report is *rejected outright* without
   one (blocking error 6). That needs ATLAS forced photometry, which needs
   registration.
3. **The Mira trap is open.** Uncatalogued red long-period variables in the plane
   masquerade as novae, and there is no colour cut in the M1 filter.
4. **`d:vsx` cost a real nova.** In the positive control, AT 2026lck — a
   confirmed nova — was vetoed because VSX catalogues that position as a YSO. The
   same veto is running here and may be discarding good objects silently.
5. **These are candidates, not discoveries.** The claim is "passes a filter that
   recovers 69% of DCAP's designations from pre-report data", nothing stronger.
