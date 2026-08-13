# exosat-rv

Independently reproduce the first exosatellite radial-velocity detection — a planetary-mass
companion to the brown dwarf **CD-35 2722 B**, itself orbiting an M dwarf — from public ESO
data, and then apply the same method to substellar-companion analogues.

The claim under test is Hoy et al. 2026, *Planetary-Mass Exosatellite Detected Around the
Substellar Companion of a Star* ([arXiv:2607.05193](https://arxiv.org/abs/2607.05193);
[Nature](https://www.nature.com/articles/s41586-026-10751-w)). They pointed VLT/CRIRES+ at
the **companion** rather than the star and measured its reflex wobble — the first time
radial velocity has produced evidence of a satellite.

Everything this project does runs on a laptop against public archives. See
[`SPEC.md`](SPEC.md) for the thesis and prior-art assessment,
[`DATA-SOURCES.md`](DATA-SOURCES.md) for endpoints and their known incompletenesses, and
[`BUILD-PLAN.md`](BUILD-PLAN.md) for the milestone plan.

**Current state: M0–M26 complete, M27 open.** Start at [`LESSONS.md`](LESSONS.md) — the
consolidated trap catalog and the map of which milestone document owns which conclusion —
then [`HANDOFF.md`](HANDOFF.md) and the roster ledger
[`docs/target-queue.md`](docs/target-queue.md). Milestone documents:
[`M0`](M0-RESULTS.md) archive · [`M1`](M1-RESULTS.md) the source, and two retractions ·
[`M2`](M2-RESULTS.md) RV extraction · [`M3`](M3-RESULTS.md) the positive control ·
[`M4`](M4-RESULTS.md) aliases · [`M5`](M5-RESULTS.md) analogues ·
[`M6`](M6-RESULTS.md) reproduction from the published table ·
[`M7`](M7-RESULTS.md) the literature, and three attribution corrections ·
[`M8`](M8-RESULTS.md) young close-in giants · [`M9`](M9-RESULTS.md) order screening
falsified, and a trap the control caught · [`M10`](M10-RESULTS.md) the astrometric route ·
[`M11`](M11-RESULTS.md) self-templating suppresses the signal ·
[`M12`](M12-RESULTS.md) injection discipline (shift the template, never the observation) ·
[`M13`](M13-RESULTS.md) the paper's own eleven orders, and the evidence flip ·
[`M14`](M14-RESULTS.md) **the floor closed and the flip confirmed** ·
[`M15`](M15-RESULTS.md) **eta Tel B's first RV limit** · [`M17`](M17-RESULTS.md) the
K-band tier · [`M20`](M20-RESULTS.md) the census harvest and the contrast wall ·
[`M23`](M23-RESULTS.md) the roster closed.

## The verdict

**The primary conclusion reproduces — now from the raw data too. The second satellite does
not survive the paper's own table.** Getting to sentence one took fourteen milestones;
sentence two emerged on the way.

**Reproduced.** An independent re-reduction (cr2res from raw frames, viper forward
modeling, the paper's own eleven-order set found in M13) reaches **70–90 m/s rms against
the paper's published per-epoch RVs** — down from ~1850 m/s at M6 — and a **blind period
search re-detects the ~171-day signal at rank 1 with a BERV nuisance covariate in the
model** (ΔBIC +26 to +28), on two independent reduction routes. Fitted amplitude
K = 304 ± 69 m/s against the published 306. Every adopted pipeline change passed
injection-recovery gating; the decisive levers were a second template iteration,
oversampling, and per-nodding-frame extraction (M14).

**Contradicted.** Nested sampling (dynesty) on the paper's *own published RV table* gives
ΔlogZ(two satellites − one eccentric satellite) between **−0.8 and −6.6 across ten
configurations** (three model pairings × prior styles × seeds), never positive, against
the paper's claimed **+2.62**. The evidence for the second satellite does not reproduce
on the data as published (M13 §4, M14 §1).

**Caveats, stated plainly.** The recovered amplitude runs 20–40% high and the published
RVs correlate with BERV at r = −0.71, so the reproduction is confound-limited at current
sampling; the epochs that decide it are embargoed until Dec 2026 – May 2027
(the calendar is in [`docs/target-queue.md`](docs/target-queue.md)).

The floor-closing is only trustworthy because of the **positive control** discipline from
M3 onward (GJ 229 B, a known 12.1-day binary — Δχ² = 63.8) and injection gates on every
change: three separate "improvements" that deleted signal were caught and rejected by
exactly that machinery (M9, M11, M23).

## After the reproduction: the survey (M15–M26) and what it found

The validated recipe was then pointed at **every archival CRIRES+ companion-spectroscopy
campaign** a coordinate-based census could find (names lie; a 50,000-frame sky-clustered
sweep does not). Eighteen systems adjudicated; final roster in M23 §5 — **one
confirmation, one contradiction, four upper limits, one contamination-limited case, four
data-limited**. Highlights:

- **eta Tel B** — the first RV constraint a literature search can find on the object:
  no detection, **msini ≳ 0.5–1.2 M_Jup (90%) across P = 20–300 d**, confirmed on both
  reduction routes; the injection-calibrated machinery re-finds its own end-to-end
  K = 300 m/s injection at rank 1, so the null is meaningful (M15).
- **The K-band tier** — RVs of **beta Pic b itself** at 162 m/s within-night scatter
  (adding night-to-night repeatability to the 2024 CRIRES+ spin/RV literature), AB Pic b,
  and CT Cha B with a 3.3σ variability candidate undecidable at n = 3 (M17, M23).
- **The contrast wall, measured** — slit companion-RV is clean at ≥0.8″/2000× contrast,
  flooded at 0.55″/5000×, and the star *is* the spectrum at 0.17″ (M20 §6). Where the
  wall stands, fiber starlight suppression is the instrument answer.
- **YSES 1 b** — 34 m/s night-to-night, the best per-epoch quality of the whole campaign
  (~20–30 M⊕ satellite reach if its blocked 2022 pair is recovered) (M25–M26).
- **The machinery catches fakes** — PDS 70's nine-night template upgrade *looked* quieter
  and failed its injection gate at −62% recovery; rejected, and the validated six-night
  state restored bit-for-bit (M23).

**M27, open:** a header audit revealed that every dataset this project had classed as
"staring mode" is actually **HiRISE** — fiber-fed SPHERE→CRIRES+ starlight-suppressed
observations — which retracted three staring-tier verdicts (our slit-recipe reductions,
not the sky) and revealed **six public suppressed nights of beta Pic b** awaiting a
fiber-appropriate reduction. The correction log lives at the top of
[`docs/target-queue.md`](docs/target-queue.md).

A Hoy-style manuscript draft (CD-35 + eta Tel, figure-for-figure against the paper) is
generated in [`docs/paper/`](docs/paper/) — built from `draft.template.html`, never
hand-edited.

⚠️ **M1 retracted two claims M0 published.** M0 asserted that a value in the paper
(a "Hill radius" of 1.07 au) was impossible; it is a Domingos+2006 *stability limit*, the
companion's orbit is highly eccentric (e > 0.9, a ~ 222 au, not a circular 62.6 au), and
recomputed properly the paper's value is **correct**. M0 also misreported what the paper's
Δlog Z = 2.6 compares. Both retractions, with working, are in
[`M1-RESULTS.md`](M1-RESULTS.md) §1 and indexed in [`HANDOFF.md`](HANDOFF.md) §1.

---

> **The sections below are the M0–M11 record, kept as written.** Several of their verdicts
> were later superseded — most importantly, "the measurements do not reproduce" (M6's
> ~1850 m/s floor, M9/M11's 776 m/s) was closed by M13–M14, and M10's astrometric route
> was shelved once the RV route worked. They stay because the dead ends are the method:
> each one was closed by a control or an injection gate, and
> [`LESSONS.md`](LESSONS.md) §7 maps every conclusion to the milestone that owns it.

## M0 in one table

CRIRES+ H-band nights on CD-35 2722 B, measured 2026-08-09 (`exosat-rv inventory`):

| Class | Nights |
|---|---:|
| **Usable now** — public *and* pipeline-reduced | **17** |
| **Reduction gap** — public raw, needs esorex | **3** |
| Embargoed until Dec 2026 – May 2027 | 8 |

**17 + 3 = 20, and the preprint claims exactly 20 usable epochs.** The paper's dataset is
the set of public H-band nights, with nothing held back — asserted as a live test so it
fails loudly when the embargo lifts. Usable baseline 2023-10-13 to 2025-01-21.

M1 then read the actual PDF (`pypdf`, 27 pages — no poppler or WSL needed) and sourced every
config value. The unverified `[SUMM]` tier is **eliminated**; two further values it held were
wrong (primary mass 0.4 not 0.5 M☉; mean RV error 31.44 not 30 m/s). The lesson M0 drew —
tag unverified values — was too weak: **an unverified value must not be an input to any
conclusion, not merely absent from tests.**

## Why this is reproducible at all

Two archive facts decide the whole project, both measured in M0 rather than assumed:

- The preprint's dataset — 20 H-band epochs, Oct 2023 to Jan 2025 — **has left its
  proprietary period.** The Dec-2025-onward frames that changed the accepted Nature
  numbers have not, and lift between Dec 2026 and May 2027.
- ESO publishes **pipeline-reduced 1-D spectra** (`calib_level=2`) for 17 of those nights,
  and M1 confirmed they are **per-order extractions with native wavelength solutions**:
  7 echelle orders x 3 detectors x 2048 native pixels, labelled by `ORDER`/`DETEC`/`XPOS`.
  That is exactly what a forward-modelling RV code consumes, so the raw-to-1D reduction —
  the expensive part — does not have to be redone. **The project's last kill-risk is
  retired.** Working from the combined product costs ~10% precision (34.49 vs 31.44 m/s),
  which is understood in advance rather than discovered in M3.

## What "reproduce" means here

Not re-running the authors' pipeline on the authors' products. The inference stage is
deliberately built on a *different* Keplerian fitter than the paper's, so agreement means
something. The sharpest question in the data is not whether the 169-day signal is real —
it is the **period of the second signal**. The paper is explicit that 14, 70, 88 and 115 days
are aliases of one another, produced by two observing seasons almost exactly a year apart,
and that its favoured 88-day model beats the 115-day one by only Δlog Z = 2.6. That is a
*sampling* problem, and a reanalysis can attack it without new telescope time — via the
spectral window function and injection-recovery across the alias family.

(The obvious alternative — that the second signal is a harmonic of an eccentric 169-day
orbit — is one the paper already fits and rejects at Δlog Z = 6.9. M4 was re-scoped once
M1 read the source.)

## What else came out

**M4 — the second signal's period.** All four candidates (14, 70, 88, 115 d) lie on a
one-year alias comb built from the *primary* 169.45 d signal. Injection-recovery on the real
cadence shows a true 115-day signal is recovered as ~87 d **92%** of the time, so peak
position cannot discriminate. But a 115-day signal clears the 1% FAP only **6%** of the time
against **74%** for 87.46 d — so the *significance* of the observed peak does favour the
paper's choice, by an argument stronger than the Δlog Z = 2.6 it quotes.

**M1 — two of M0's published claims were wrong**, found by reading the actual PDF. M0 had
"disproved" a value in the paper that turned out to be correct. Both retractions are indexed
in [`HANDOFF.md`](HANDOFF.md) §1.

**M2 — a converter that unlocks the archive.** ESO's products can drive `viper` after a
verified-lossless reshape into cr2res layout, plus four undocumented configuration facts
(K-band FTS default, Ångström-vs-nm templates, gnuplot at import, `termios`).

## The analogue targets (M5)

Searched **archive-first** — a catalogue-first list cannot contain CD-35 2722 B, since the
NASA Exoplanet Archive caps at 30 M_Jup. Rediscovering CD-35 2722 B is the control, and it
passes. Frame counts mislead badly (beta Pic b's 753 frames are 6 nights); what matters is
nights spread over time:

| Target | Usable H nights | Baseline | Why it matters |
|---|---:|---|---|
| **eta Tel B** | 16 | 800 d | Best analogue — more baseline than CD-35 2722 B's own campaign, and a wider 4.2″ separation |
| **GJ 229 B** | 11 | 361 d | 5.8 pc, and a **known binary brown dwarf** — a positive control where a signal is *expected* |

M5 also found that this is **not white space**: programme 110.23RW is a pilot survey by the
same group across AB Pic B, beta Pic B and CD-35 2722 B, and every later programme targets
CD-35 2722 B alone.

## Generalising the method (M7–M8)

The obvious next question — *where else does this work?* — turned out to have a published
answer the project had never read. Hoy et al. cite
[Lazzoni et al. 2022](https://arxiv.org/abs/2207.07569), by four of their own co-authors,
which simulates satellite populations around 38 imaged companions and computes RV detection
probabilities for each. The method itself was proposed by
[Vanderburg, Rappaport & Mayo 2018](https://arxiv.org/abs/1805.01903), and **three published
nulls preceded this detection**, not the one SPEC named (under the wrong author). There is
now a `papers/` archive and [`scripts/fetch_paper.py`](scripts/fetch_paper.py) to extend it.

**[`M7`](M7-RESULTS.md) — the feasibility framework.** Four conditions, not two: wobble,
flux, dynamical allowance, and *survival*. Two results worth stating:

- **eta Tel B is the best analogue on two independent criteria.** M5 ranked it #1 on archive
  holdings alone; Lazzoni et al. rank it **4th of 38** on physics alone. Neither ranking
  shares an assumption with the other.
- **No imaged companion reaches planet-like (Galilean/Titan-class) satellites.** This method
  finds binary-like satellites or nothing — reproducing Lazzoni et al.'s central conclusion
  from a threshold recalibrated on the *achieved* 31.44 m/s rather than their forecast, which
  the real instrument beat by 1.6x.

**[`M8`](M8-RESULTS.md) — young close-in giants.** Pushing the M_host^(-2/3) scaling to
hot Jupiters: an Earth-mass moon there gives K ~ 71 m/s, and a 10 M_Earth one ~708 m/s,
*larger* than the 246 m/s actually detected. The signal is easy; survival is the problem.

An old hot Jupiter is tidally locked to its star, which puts its corotation radius outside
the Hill-stability limit — so **every dynamically stable satellite is inside corotation and
spirals in**. A *young* planet has not been despun and the window is open. The catch is that
hot Jupiters cannot be spatially resolved, so the slit trick is replaced by cross-correlation
spectroscopy, which needs the planet's velocity to sweep >= 30 km/s in a night. Survival wants
a wide orbit; cross-correlation wants a narrow one, and the trade is
**tau_spin-down ~ M_star t^3 / dv^3** — a factor 2 in observability costs 8 in survival time.

**3 known planets clear both cuts at the pessimistic tidal Q, 8 at the optimistic one**
(`exosat-rv closein`). And planet mass is the cheapest lever: the planetary range runs to
13 M_Jup, spin-down goes as M_p while the satellite geometry is self-similar, so **from
~5 M_Jup upward the observability bar clears unaided.** No such planet is currently known
young *and* close enough — CoRoT-20 b (4.3 M_Jup, 0.090 au) misses by 1.25x — which makes
that a gap in the catalogue rather than in the physics.

The prize is not the moon. Massive satellites do not survive high-eccentricity migration
([Trani et al. 2020](https://arxiv.org/abs/2008.13778)) and preferentially do survive
disc migration, so **a limit at 10–30 M_Earth around a young hot Jupiter discriminates
between hot-Jupiter migration channels** — and RV is most sensitive to exactly the massive
satellites the theory says are the survivors.

## The control earned its keep (M9)

M9 tested whether per-order screening could close the extraction gap. It cannot — **6%**,
against the factor of 25 needed — and the individual nodding frames the plan had ranked first
turn out to be a **10%** lever, quantified in the paper's own Fig. 4. Both cheap levers are
now measured rather than assumed, and the conclusion is that the shortfall is **entirely
per-order**: median per-order rms is 2133 m/s over 10 orders, the √10 floor is 674, and viper
delivers 823. The combination stage was never the problem.

The more useful result is a near miss. **Weighting orders by their measured scatter gives the
best number the project has produced on CD-35 2722 B — 514 m/s, a 1.6× gain — and destroys
the GJ 229 B control**, dropping Δχ² from 63.8 to 5.8 and the recovered amplitude from 6165
to 1825 m/s on a binary nobody disputes. For a target with a real signal, an order's scatter
*is* the signal, so inverse-scatter weighting deletes exactly what it should keep. On a target
with no detection that is invisible.

HANDOFF has said since M3 that no result from this pipeline may be reported without re-running
the control. **M9 is the first time that rule actually caught something**, and without it the
screen would have been adopted and every later null made deeper and more wrong.

## The template, rebuilt the published way (M11)

M9 named the template as the leading suspect, so M11 ran it: viper under WSL, the recipe from
Köhler et al. 2025 §2.2 that Hoy et al. defer to, two template iterations, telluric-derived
wavelength solution. **CD-35 2722 B improved, 776 → 620 m/s. The control collapsed.**

| Template | Control Δχ² | Recovered K | vs. correct |
|---|---:|---:|---:|
| 0 iterations (baseline) | 76.5 | 5948 m/s | 100% |
| 1 iteration | 23.7 | 2452 m/s | **41%** |
| 2 iterations (the published recipe) | 21.1 | 2360 m/s | **40%** |

**Self-templating absorbs the signal.** The template is co-added from the target's own spectra
aligned by RVs measured against a template that already contains the signal, so the residual
is baked in and later velocities are partly the star measured against itself. The damage
arrives with the *first* iteration and does not recover. Köhler et al. flag the hazard for
targets with real Doppler shifts; their prescribed workaround is what viper implements, and
at our precision it was not enough.

CD-35 2722 B "improved" because that is what suppression looks like on a target with no
detected signal. **Three changes in a row have now improved the science target and been
rejected by the control** — M9's empirical weighting, M9's telluric screen, and this. On a
non-detection, anything that removes signal looks like success.

**Net movement on the reproduction: none.** Still 776 m/s against 31.44 needed. What it did
buy is elimination: the template, order screening and the nodding frames are all now measured
rather than assumed, and the leading suspect is what remains — the ADP→cr2res conversion,
verified *lossless* but never verified to put segments in the right order/detector slots.

## A second route, with better data (M10)

M9 closed the cheap options on the RV extraction gap, so M10 asked whether the project's
actual goal — bounding a *new* exosatellite — has another path. It does, and its public
dataset is better:

| Dataset | Nights | Baseline |
|---|---:|---:|
| CD-35 2722 B — the published RV detection | 18 | 466 d |
| eta Tel B — M5's best RV analogue | 16 | 800 d |
| **beta Pic b — VLTI/GRAVITY astrometry** | **28** | **2987 d** |

Astrometry also **outranks RV in Lazzoni et al.'s own table** (P = 0.999 vs 0.996) and reaches
*below* RV's ~0.4 M_Jup floor. And **HD 206893 B, where Kral et al. 2026 report a tentative
astrometric exomoon candidate, has 22 public reduced nights** — their result is reanalysable.

**beta Pic b is the crossover target**: #2 in M7's RV ranking, one of Kral et al.'s two best
astrometric targets, and the best public GRAVITY dataset of the five. It is the one object
where an RV limit and an astrometric limit could be set independently and cross-checked.
(M5 *rejected* it for RV — 753 frames on 6 nights. The same target can be hopeless for one
technique and best-in-class for another.)

⚠️ **A kill-check is open.** This is the M0-equivalent, not the M1-equivalent: the data is
public and reduced, but whether those visibility products carry the dual-field differential
phase astrometry needs is unverified. M1's precedent applies — the first automated verdict on
ESO's CRIRES+ products was wrong. See [`M10-RESULTS.md`](M10-RESULTS.md) §5.

## Continuing this work

Reading order: [`LESSONS.md`](LESSONS.md) (every trap this project paid for, so you don't
pay twice) → [`HANDOFF.md`](HANDOFF.md) (state and next actions) →
[`docs/target-queue.md`](docs/target-queue.md) (the per-system roster, embargo calendar,
and the M27/HiRISE front) → the latest `M*-RESULTS.md`.

To rebuild the RV extraction from scratch, [`docs/viper-runbook.md`](docs/viper-runbook.md)
has the full sequence: WSL setup, the two gnuplot patches, the ADP→cr2res conversion, the
Ångström-vs-nm template trap, the mandatory `-fts` H-band flag, and the positive control that
must pass before any null from the pipeline means anything. The M12+ machinery (reduction
cascade, injection harness, census, per-target runners) lives in
[`scripts/`](scripts/) — the CLI below covers the M0–M10 layer.

## Quickstart

```bash
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
exosat-rv inventory          # M0: what is public, reduced, and usable right now
exosat-rv probe              # M1: open a reduced product, check viper can use it
exosat-rv targets            # M5: analogue target list, archive-first
exosat-rv alias              # M4: is the second period set by the data or the sampling?
exosat-rv orbits             # M6: reproduce the model comparison from the published RVs
exosat-rv survey             # M7: which imaged companions can the method work on?
exosat-rv closein            # M8: can it reach satellites of young close-in giants?
exosat-rv orders             # M9: per-order screening, and the ceiling on what it buys
exosat-rv gravity            # M10: public VLTI/GRAVITY data on the astrometric shortlist
pytest -m "not network"      # offline suite
pytest                       # adds the live archive assertions
```

## Honest scope

This project does not claim a discovery and will not submit one. Its output is a
reproduction verdict, a harmonic test, and — for the analogue survey — most likely
**upper limits** rather than detections. Upper limits are the expected result and are
reported as the result.
