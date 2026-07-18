# Astronomy Projects

Build portfolio for the astronomy opportunities surfaced by the **idea-research astronomy run** (2026-06-14). The research and ranked dossiers live in [`../idea-research/astronomy/`](../idea-research/astronomy/FINAL-REPORT.md); **this** folder is where the promising ones get built.

**The pattern they all attack:** astronomy data is now open and abundant, but the *usability/translation layer* between raw archives and the humans who want to use them (newcomers, amateurs, even working scientists) is systematically missing — aggregation layers, query translators, quality-weighting, interactive explainers. That connective tissue is cheap for an agent fleet to build.

---

## Active builds

| Folder | Project | Scores (U/B/E) | Status (verified 2026-06-30) |
|---|---|---|---|
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | SETI Ellipsoid Alert Broker — sibling of catalog item #5; fuses ZTF/ASAS-SN/CHIME alerts × Gaia DR3 into nightly target lists | 4/4/4 | **M1 implemented** — pipeline + export, 42 tests green, demo artifacts in `_demo_out/` |
| [`pta-explainer/`](pta-explainer/) | Pulsar Timing Array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | 5/5/4 | **M1 ✓ + M2 in progress** — live HD demo, plus source-sandbox (residuals, sky-map source marker, 2-source superposition); 50 tests, build green; **deployed to GitHub Pages** |
| [`adql-copilot/`](adql-copilot/) | TAP/ADQL natural-language query copilot over Virtual-Observatory endpoints | 4/5/4 | **M1 implemented** — deterministic linter live vs Gaia `TAP_SCHEMA`, 26 tests green |

Each project folder contains: `SPEC.md` (the verified research dossier), `DATA-SOURCES.md` (exact APIs/endpoints/formats), `BUILD-PLAN.md` (stack decision, architecture, milestones, first tasks), and a minimal runnable skeleton.

---

## Backlog (surfaced by the run, not yet started)

Strong Tier-2/3 candidates — dossiers in [`../idea-research/astronomy/shortlist/`](../idea-research/astronomy/shortlist/):

- **Cosmology Tensions Monitor** (5/3/4) — live H0/S8/w0–wa tracker → adjacent: >2σ disagreement detector
- **Interactive Asteroseismology Simulator** (4/4/4) — pairs with a TESS mode-ID crowdsourcing game
- **Strong-Lens Training Dataset Generator** (4/4/4) — versioned HF dataset → lens-finder leaderboard
- **δ Scuti Mode Identification** (4/4/4, experiment) — per-frequency ML labeling
- **Amateur Observation Quality-Weighting Framework** (4/4/3) — makes citizen data ingestible by pros
- …plus 7 more (DESI reproducibility kit, AAVSO broker filter, SHARP→NOAA API, multi-messenger overlay, observatory bias auditor, CHIME Cat-2 pipeline, RR Lyrae calibration audit).

## Origin & full research

- [Ranked report](../idea-research/astronomy/FINAL-REPORT.md) · [15 dossiers](../idea-research/astronomy/shortlist/) · [13 subfield sweeps](../idea-research/astronomy/clusters/) · [synthesis](../idea-research/astronomy/clusters/00-synthesis.md)
