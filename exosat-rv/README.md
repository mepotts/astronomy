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

**Current state: M0 (archive kill-check) complete.** Findings:
[`M0-RESULTS.md`](M0-RESULTS.md).

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

M0 also **disproved a published-looking number**: a Hill radius of 1.07 au implies the
companion orbits at 3.7 au, but it is imaged at 2.8" = 62.6 au, where the Hill radius is
~18 au. That value came from an AI summary of the paper body rather than from the paper,
which exposed a provenance problem across the whole config — every field is now tagged
`[TAP]` (archive-confirmed), `[v1]` (read from the abstract), or `[SUMM]` (unverified, and
barred from backing any test).

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
it is whether the **second, marginal 87-day signal** is a satellite or the first harmonic
of an eccentric 169-day orbit. 169.45/2 = 84.7 d sits 4.34 sigma from the claimed
87.46 +/- 0.63 d, and the paper's evidence for it (delta-log-Z = 2.6, a Bayes factor of
~14) is positive rather than decisive. M4 exists to answer that.

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
