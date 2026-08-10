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

**Current state: M0 complete; M1 half complete.** Findings:
[`M0-RESULTS.md`](M0-RESULTS.md), [`M1-RESULTS.md`](M1-RESULTS.md).

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
- ESO publishes **pipeline-reduced 1-D spectra** (`calib_level=2`) for 17 of those nights.
  Reduced spectra are exactly what a forward-modelling RV code consumes, so the raw-to-1D
  reduction — the expensive part — does not have to be redone for them.

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

## Quickstart

```bash
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
exosat-rv inventory          # M0: what is public, reduced, and usable right now
pytest -m "not network"      # offline suite
pytest                       # adds the live archive assertions
```

## Honest scope

This project does not claim a discovery and will not submit one. Its output is a
reproduction verdict, a harmonic test, and — for the analogue survey — most likely
**upper limits** rather than detections. Upper limits are the expected result and are
reported as the result.
