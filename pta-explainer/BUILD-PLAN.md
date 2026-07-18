# BUILD-PLAN.md — PTA / Hellings–Downs Interactive Explainer

Plan to take this from an empty skeleton to a deployed, physics-validated, public interactive
explainer. v0 target = the **Hellings–Downs Live Demo** (see SPEC.md Part 2).

---

## 1. Stack (chosen, with alternatives considered)

**Chosen: Vite + vanilla TypeScript + D3 (for SVG axes/scales/curve), zero backend, static deploy to GitHub Pages.**

Justification:
- **Why static / no backend:** the entire v0 (and arguably the whole product) is pure client-side math — the H–D curve is analytic, the pulsar JSON is a few KB, angular separation is a one-line spherical-cosine. A server buys nothing and adds hosting + maintenance burden. Static = free GitHub Pages hosting, works offline, trivially handed off to NANOGrav EPO later. Matches the dossier's "static HTML/JS bundle, no server required."
- **Why Vite:** fastest dev server (`npm run dev` → instant HMR), zero-config TS, trivial static `build`, and `vite build --base` makes Pages deploys painless. Modern default.
- **Why D3 (not Chart.js / Plotly / raw canvas):** D3's `scaleLinear`, `axisBottom/Left`, and `d3.line` are exactly the primitives for "draw an analytic curve with proper scientific axes + a draggable marker." `d3-drag` gives us the drag interaction for free in M1. It's the same tool the dossier names. We use D3 as a **library** (import only the modules we need), not a framework.
- **Why vanilla TS, not React (yet):** v0 is one page with a handful of interactive elements. React/Svelte earn their keep when state/composition gets complex (M2: multiple linked panels). Starting vanilla keeps the skeleton tiny and the physics legible. **Revisit at M2** — if the residual panels + sky map + curve need to stay in sync, introduce a light framework (Svelte preferred for size, or React per the dossier). The physics/data modules are framework-agnostic by design, so this swap is cheap.

**Alternatives considered and rejected for v0:**
- **Observable Framework** (named in dossier): excellent for this genre and worth a look, but it's opinionated about project structure and data loaders; for a handoff-and-maintain outreach tool, a plain Vite/TS app is more conventional and easier for an arbitrary maintainer. Keep as a fallback if we want notebook-style authoring.
- **Pyodide / WebAssembly physics:** explicitly **deferred**. v0 needs no Python — the curve is a one-liner. The dossier flags Pyodide as the chief performance risk; we avoid it entirely until/unless M2 residual time-series demands it, and even then "precompute a grid + interpolate in JS" (dossier mitigation) is preferred over shipping a Python runtime.
- **React + heavy chart lib:** overkill for an axes-plus-curve view; larger bundle, slower to a runnable skeleton.

---

## 2. Architecture (2 lines)

A single static SPA: pure functions in `src/physics/` compute the analytic Hellings–Downs Γ(θ) and pairwise angular separations from the baked-in NANOGrav pulsar JSON, and a thin D3 view layer in `src/components/` renders an axes-plus-curve plot plus (M1) a sky map, reacting to a draggable separation control. No network, no server, no build-time data fetch — the derived pulsar/HD JSON ships in the bundle and everything recomputes client-side on interaction.

---

## 3. Repo layout

```
pta-explainer/
├── SPEC.md
├── DATA-SOURCES.md
├── BUILD-PLAN.md
├── README.md
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html                 # dev-server entry; mounts the app
├── scripts/
│   └── build-pulsars.mjs       # one-off: par/tim → src/data/*.json (NOT run by dev server)
└── src/
    ├── main.ts                 # app entry: wires physics → view, renders placeholder plot
    ├── physics/
    │   ├── hellingsDowns.ts     # Γ(θ) analytic formula  ← the load-bearing physics
    │   └── angularSeparation.ts # (RA,Dec)×2 → θ via spherical law of cosines
    ├── components/
    │   └── HDCurvePlot.ts       # D3: axes + hard-coded H–D curve (M0 stub)
    ├── data/
    │   ├── nanograv15_pulsars.json   # placeholder ~6 pulsars (M0) → 67 real (M1)
    │   └── nanograv15_hd_points.json # placeholder/empty (M0) → digitized Fig 1c (M1)
    └── styles.css
```
(The M0 skeleton in this repo ships `main.ts`, `hellingsDowns.ts`, `HDCurvePlot.ts`, both JSON
placeholders, `index.html`, `styles.css`, configs. `angularSeparation.ts`, the sky map, and the
build script land in M1.)

---

## 4. Milestones

### M0 — Skeleton (this deliverable) ✅
- Runnable Vite/TS project. `npm install && npm run dev` starts a dev server.
- Renders a **trivial placeholder**: D3 axes (x: angular separation 0–180°, y: correlation −0.5–1.0)
  with the **analytic H–D curve hard-coded/sampled** and a title. No interactivity, no real array.
- `hellingsDowns.ts` already contains the *real* analytic formula (so M0 is honest), but the page just
  draws it statically.
- **Done when:** dev server shows axes + the recognizable H–D curve shape; `npm run build` succeeds.

### M1 — Hellings–Downs Live Demo (the v0 product)
- Replace placeholder pulsar JSON with the **real 67 NANOGrav 15-yr pulsars** via `scripts/build-pulsars.mjs` (parse RAJ/DECJ from par files → decimal degrees → JSON). See DATA-SOURCES.md §2.
- Add **`angularSeparation.ts`** (spherical law of cosines) + unit tests.
- Add a **sky map** (RA/Dec scatter of the 67 pulsars) and a **pulsar-pair picker** (click two pulsars OR drag a θ slider 0–180°).
- A **marker rides the analytic H–D curve** at the selected θ, updating in real time on drag/selection.
- Overlay the **digitized NANOGrav 15-yr binned points** (DATA-SOURCES.md §3, option 1) as the static "real detection" backdrop, clearly labeled illustrative.
- Attribution string (DATA-SOURCES.md §5) rendered in a footer.
- **Run the physics-validation suite (see §6) and make it pass.**
- **Done when:** user picks J1909−3744 + J1713+0747 (or any pair / arbitrary θ), the marker sits on the correct point of the published curve, and the curve matches the published H–D shape within tolerance.

### M2 — Residual / timing-intuition panels  *(in progress)*
- [x] **Single-source residual physics** — `src/physics/residuals.ts`: circular-SMBHB
  strain amplitude (`h0 = 2(Gℳ)^5/3(πf)^2/3 / c⁴d_L`), the Ellis-2012 antenna patterns
  F+/F×, and the Earth-term (+ optional pulsar-term) residual waveform. Single illustrative
  monochromatic source only — no stochastic-GWB Monte-Carlo (per dossier).
- [x] **Validation suite** — `physics/__tests__/residuals.test.ts` (27 tests): h0 pinned to
  the published 2.76e-14 landmark + power-law scalings; the headline cross-check that the
  antenna patterns' sky+polarization average **reproduces the Hellings–Downs curve** (ties
  M2 back to the M1 physics); and the superposition linearity checks. Plus
  `residualWiring.integration.test.ts` on the real array.
- [x] **Residual panel** — `components/ResidualPanel.ts` + page §4: drag chirp mass / GW
  frequency / source RA,Dec / inclination → live residual time-series for six real pulsars,
  with a live peak-amplitude readout. Kept vanilla-TS+D3 (no framework needed yet).
- [x] **Source marker on the sky map** — the §4 source position(s) render as gold ★ on the
  §1 sky map (`SkyMap.setSources`), so the geometry driving the antenna-pattern modulation
  is visible alongside the pulsars.
- [x] **Second GW source (superposition)** — `residualMultiSec`/`sampleResidualSeriesMulti`
  sum independent sources (GR is linear); a "add a second binary" toggle reveals a compact
  control set and a second ★. The honest bridge toward "background = many sources".
- [x] **Detection-threshold / noise overlay** — an adjustable ±RMS timing-noise band on the
  residual panel (`ResidualPanel` `rmsNs`) + a live "N of 6 pulsars clear the band" readout,
  with the honest caveat that real detection integrates the whole span across many pulsars
  (so the 2023 result dug the signal out from *below* the single-measurement noise). Uses a
  single illustrative, clearly-labeled RMS — NOT fabricated per-pulsar values.
- [ ] Physically-grounded **per-pulsar** noise (real NANOGrav noise products) + validation
  vs. published sensitivity curves. **(data-fidelity fork — real products vs. the current
  illustrative band — is an open question for Matthew.)**
- [x] **Annotation layer keyed to each control** ("what am I looking at?") —
  `components/annotations.ts`: an on-demand "?" toggle beside each control reveals a
  plain-language, physically-grounded note (collapsed by default, accessible). Deployed.
- [ ] Framework (Svelte/React) — revisit ONLY if the growing panel set needs it; not yet.

### M3 — Full PTA explainer + deploy
- Guided/scrollytelling explainer wrapping the interactives (what a pulsar is → timing residuals → why correlation → quadrupole → the curve → the 2023 result).
- Switchable array configs (EPTA/PPTA/IPTA) if data permits (dossier week 3–6).
- **Deploy to GitHub Pages** (`vite build --base=/pta-explainer/` + Pages action). (Can deploy M1 earlier for feedback — recommended.)
- Companion 1–2 page undergrad explainer; outreach per dossier 90-day arc.

---

## 5. Concrete first-task checklist (start of M1, right after M0 lands)

1. [ ] `npm install && npm run dev` — confirm M0 skeleton renders the hard-coded curve. (smoke test)
2. [ ] Download the 67 `.par` files from Zenodo 7967584 into `data/raw/` (gitignored).
3. [ ] Write `scripts/build-pulsars.mjs`: parse `RAJ`/`DECJ` → decimal degrees → `src/data/nanograv15_pulsars.json` (67 entries). Spot-check 2–3 against SIMBAD.
4. [ ] Write `src/physics/angularSeparation.ts` (spherical law of cosines) + a unit test (e.g. known pair J1713+0747 / J1909−3744 separation).
5. [ ] Write `src/physics/__tests__/hellingsDowns.test.ts`: assert Γ(0°)=0.5, zero-crossing ≈49.3°, min ≈−0.173 near ≈82.5°, Γ(180°)=0.25. (This is the physics-validation gate — §6.)
6. [ ] Digitize ~15 binned points from Agazie 2023 Fig 1c → `src/data/nanograv15_hd_points.json`; visually confirm they hug the analytic curve within error bars.
7. [ ] Build the sky-map component + pair picker; wire selection → θ → marker on curve.
8. [ ] Add footer attribution; run validation; deploy M1 to Pages for early feedback.

---

## 6. Physics-validation plan (de-risks the #1 dossier threat)

**One-line approach:** prove the rendered curve IS the published Hellings–Downs curve by asserting the analytic Γ(θ) against known closed-form landmark values in an automated test, then visually overlaying it on the digitized 2023 NANOGrav points.

Concretely:
1. **Unit test the formula** (`hellingsDowns.test.ts`, runs in CI via `npm test`):
   - Γ(0°, distinct) = 0.5 exactly.
   - Zero crossing at θ ≈ **49.3°** (assert |Γ| < 1e−3 there).
   - Minimum (most anticorrelated) ≈ **−0.173** near θ ≈ **82.5°** (assert via derivative or sampled min).
   - Γ(180°) = 0.25 exactly.
   - `x·ln x` guarded → no `NaN` at θ=0.
   These landmarks are independently derivable from the closed form, so the test is self-checking, not circular.
2. **Cross-check against an independent implementation:** compute the same curve in a 5-line Python/NumPy snippet (or the `enterprise`/`hasasia` `hd_orf` helper) on a θ grid and diff against the TS output (max abs error < 1e−6). Document in the test or a `scripts/validate-hd.mjs`.
3. **Visual overlay regression:** the digitized NANOGrav 15-yr binned points must lie within their error bars of the analytic curve. If they don't, the digitization or normalization is wrong — fix before shipping.
4. **Normalization sanity:** confirm the convention matches the NANOGrav figure (points normalized by fitted common-process amplitude). DATA-SOURCES.md §1 documents the convention and the gotcha that the curve starts at 0.5, not 1.0.
5. **Lay-audience correctness guardrails:** never present the single-source M2 residuals as "the GWB" (it's an illustrative monochromatic source); label digitized points "illustrative"; keep the δ-self-term out of the distinct-pulsar curve. (Directly addresses the dossier's "physics correctness risk.")

---

## 7. Kill criteria (from the dossier — monitor throughout)

- **Official tool ships first:** if NANOGrav/IPTA release an official interactive explainer with comparable interactivity **before Week 3**, kill or pivot. Monitor https://nanograv.org/news.
- **Slick static H–D notebook already exists** (check Observable HQ before coding M1): if so, pivot to *adding the dynamic drag/array-picker layer* rather than rebuilding the static curve.
- **Performance (M2+):** if WebAssembly/Pyodide makes drag-to-update sluggish for the full array → drop Pyodide, precompute a parameter grid + interpolate in JS. (v0 sidesteps this by being analytic/pure-JS.)
- **Physics-correctness fails validation:** if the curve can't be validated to the landmarks above, or stochastic-GWB superposition can't be shown without Monte-Carlo, **keep MVP to the single-source illustrative case** and do not misrepresent the science.

---

## 8. OPEN QUESTIONS FOR MATTHEW

1. **Audience priority for v0:** is the target the **general public / press-curious** (lean hard into "the famous 2023 figure, now you can poke it"; minimal jargon) or **physics undergrads** (allow the formula, axes labels, a bit of derivation)? This changes copy, default view, and how much we annotate. The dossier serves both eventually, but v0 should pick one.
2. **Faithfulness bar for the backdrop points:** is **digitizing the ~15 binned points from Fig 1c** (clearly labeled "illustrative") acceptable for launch, or do you want the **faithful regeneration from the public TOAs via the enterprise pipeline** (a real offline research task, slower) before going public? (DATA-SOURCES.md §3 — this is the main data-fidelity fork.)
3. **Framework now or at M2?** OK to start vanilla-TS+D3 and introduce Svelte/React only when the residual panels arrive (my recommendation), or do you want React from the start per the dossier's wording (more boilerplate now, less churn later)?
4. **Deploy target + branding:** GitHub Pages under your account is assumed. Any preferred repo name / domain, and do you want the "independent, not affiliated with NANOGrav" disclaimer front-and-center, or to actively seek NANOGrav EPO endorsement/hosting early (dossier 90-day arc)?
5. **Scope ceiling:** is the goal to ship **M1 (the Live Demo) as a standalone artifact** and stop if it lands well, or commit to the full M3 explainer? (M1 stands alone and de-risks the rest.)
