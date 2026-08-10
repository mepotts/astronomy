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

**Current state: M0–M6 complete.** Findings:
[`M0`](M0-RESULTS.md) archive · [`M1`](M1-RESULTS.md) the source, and two retractions ·
[`M2`](M2-RESULTS.md) RV extraction · [`M3`](M3-RESULTS.md) the positive control ·
[`M4`](M4-RESULTS.md) aliases · [`M5`](M5-RESULTS.md) analogues ·
[`M6`](M6-RESULTS.md) **the reproduction**.

## The verdict

**The conclusion reproduces. The measurements do not.** Those are separate claims, and this
project needed six milestones to stop conflating them.

**Reproduced** — from the paper's *own published RV table* (Table 2, appendix A), fitted with
an independent code:

| Quantity | This work | Hoy et al. |
|---|---|---|
| ~169-day signal | power 0.831, **above the 0.1% FAP level** | detected |
| Preferred second period | **88 d** (over 14, 70, 115) | 87.46 d |
| Secondary amplitude K₂ | **114 m/s** | 113.92 m/s |
| 88 d over 115 d | Δ = 1.85 | Δlog Z = 2.6 |
| 2 satellites over eccentric 1 | Δ = 2.55 | Δlog Z = 6.9 |

**Not reproduced** — the radial velocities themselves. Re-deriving them from public archive
spectra reached ~1850 m/s per epoch against the 31.44 m/s needed; the 246 m/s signal sits
7.5× below that floor, so its absence there is arithmetic, not evidence.

That second reading is only trustworthy because of a **positive control**: run against
**GJ 229 B**, a brown dwarf with a *known* 12.1-day binary (Xuan et al. 2024), the same
pipeline recovers the signal — χ² about a constant falls from 80.4 to 16.6 at the known
period, Δχ² = 63.8. It measures real velocities; it is simply coarse.

⚠️ **M1 retracted two claims M0 published.** M0 asserted that a value in the paper
(a "Hill radius" of 1.07 au) was impossible; it is a Domingos+2006 *stability limit*, the
companion's orbit is highly eccentric (e > 0.9, a ~ 222 au, not a circular 62.6 au), and
recomputed properly the paper's value is **correct**. M0 also misreported what the paper's
Δlog Z = 2.6 compares. Both retractions, with working, are in
[`M1-RESULTS.md`](M1-RESULTS.md) §1 and indexed in [`HANDOFF.md`](HANDOFF.md) §1.

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

## Quickstart

```bash
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
exosat-rv inventory          # M0: what is public, reduced, and usable right now
exosat-rv probe              # M1: open a reduced product, check viper can use it
exosat-rv targets            # M5: analogue target list, archive-first
pytest -m "not network"      # offline suite
pytest                       # adds the live archive assertions
```

## Honest scope

This project does not claim a discovery and will not submit one. Its output is a
reproduction verdict, a harmonic test, and — for the analogue survey — most likely
**upper limits** rather than detections. Upper limits are the expected result and are
reported as the result.
