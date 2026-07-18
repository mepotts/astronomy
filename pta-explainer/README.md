# PTA Explainer — Hellings–Downs Live Demo

An interactive, browser-native explainer for how a **pulsar timing array** detects the
nanohertz gravitational-wave background — built around the famous 2023 **NANOGrav 15-year**
Hellings–Downs detection figure, made interactive.

> **Status: M1 complete · M2 in progress · [live on GitHub Pages](https://mepotts.github.io/pta-explainer/).**
>
> **M1 — Hellings–Downs Live Demo.** The page is interactive: a D3 sky map of the **real
> 67-pulsar NANOGrav 15-year array**, a pulsar-pair picker (click two dots) and a θ slider,
> and a marker that rides the **exact analytic Hellings–Downs curve** at the selected
> separation (draggable, kept in sync across all three controls). The digitized 2023
> detection backdrop points are wired in but currently empty (not published as a
> machine-readable table — see `DATA-SOURCES.md` §3); the analytic curve is exact regardless.
>
> **M2 — source sandbox** (§4 on the page). Drop a supermassive black-hole binary on the
> sky and drag its parameters (chirp mass, GW frequency, sky position, inclination); the
> panel draws the timing residual it stamps onto six real pulsars, and the source shows as
> a gold ★ on the §1 sky map so the geometry behind the differing amplitudes is visible.
> The shared **Earth-term** wiggle (same period everywhere, amplitude/sign set by each
> pulsar's antenna pattern) is the time-domain face of the same correlation. Tick **"add a
> second binary"** to watch two sources' residuals **superpose** (GR is linear) — the
> honest bridge toward "the real background is many sources." The residual physics lives in
> `src/physics/residuals.ts`, validated by 27 landmark tests — including a cross-check that
> the antenna patterns' sky-and-polarization average **reproduces the Hellings–Downs
> curve**, tying M2 back to the M1 physics. An adjustable **timing-noise band** overlays the
> plot so the signal-vs-noise problem is visible — with the honest point that a real PTA
> integrates ~15 yr across dozens of pulsars, pulling the signal out from *below* the
> single-measurement noise (which is how the 2023 detection worked). Still on the M2/M3
> list: physically-grounded *per-pulsar* noise and the scrollytelling explainer (see
> `BUILD-PLAN.md`). Honestly framed as *illustrative* sources, **not** the stochastic
> background.
>
> See `BUILD-PLAN.md`.

## Quick start

```bash
npm install
npm run dev      # starts Vite dev server (prints a localhost URL)
```

Open the printed URL — you should see axes (angular separation 0–180° vs. correlation)
with the recognizable Hellings–Downs curve: starting at 0.5, crossing zero near ~49°,
dipping to a slight anticorrelation near ~82°, recovering toward 180°.

```bash
npm run build    # type-check + static production build into dist/
npm run preview  # serve the production build locally
npm test         # run physics-validation unit tests (added in M1)
```

## Deploy

**Live demo (already deployed):** https://mepotts.github.io/pta-explainer/ (auto-built from `dist/`).

The source of truth is the private `astronomy` monorepo; the built site is mirrored to the
public repo `mepotts/pta-explainer` (GitHub Pages can't serve from a private repo on a free
plan). To re-ship the current state:

```bash
npm run deploy   # build:pages (base=/pta-explainer/) + force-push dist/ to the public repo
```

See `scripts/deploy-pages.sh` for the mechanics (overridable via `PAGES_REPO_URL`, etc.).

## What this is (and isn't)

- **Is:** the dossier's *adjacent-angle MVP* — the Hellings–Downs Live Demo (M1) plus the
  single-source timing-residual sandbox (M2). Pure client-side, analytic physics, static
  deploy (GitHub Pages), no backend.
- **Isn't (yet):** physically-grounded *per-pulsar* noise (the §4 timing-noise band is a
  single illustrative RMS, not real NANOGrav noise products), switchable EPTA/PPTA/IPTA
  arrays, or the guided scrollytelling explainer — the rest of M2–M3. And it is never the
  stochastic GW background: every residual shown is one or two illustrative sources.

## Project docs

- `SPEC.md` — the verified dossier + the tightened "what we build first."
- `DATA-SOURCES.md` — NANOGrav 15yr data (Zenodo, CC-BY-4.0), the H–D formula, and how the
  shipped JSON is derived. **Read this before touching the physics or data.**
- `BUILD-PLAN.md` — stack rationale, architecture, milestones M0→M3, first-task checklist,
  the **physics-validation plan**, kill criteria, and open questions.

## Layout

```
src/
  physics/hellingsDowns.ts      # the real analytic Γ(θ) formula (load-bearing)
  physics/angularSeparation.ts  # (RA,Dec)×2 → θ, spherical law of cosines
  physics/residuals.ts          # M2: single-SMBHB strain, antenna patterns, residual waveform
  physics/__tests__/            # physics-validation + integration suites (npm test)
  components/HDCurvePlot.ts      # D3: axes + curve + draggable marker
  components/SkyMap.ts           # D3: RA/Dec scatter + pulsar-pair picker
  components/ResidualPanel.ts    # M2: D3 multi-pulsar residual time-series plot
  data/nanograv15_pulsars.json   # the real 67-pulsar NANOGrav 15-yr array
  data/nanograv15_hd_points.json # digitized Fig 1c backdrop (empty for now; see DATA-SOURCES §3)
  main.ts                        # entry: wires physics → views, single θ source of truth
scripts/build-pulsars.mjs          # one-off par/tim → JSON (run manually, not by dev server)
scripts/build-pulsars-from-csv.mjs # one-off: data/raw/ position CSV → JSON (how the 67 were built)
data/raw/                          # provenance: the resolved-positions CSV the JSON derives from
```

## Attribution

Pulsar positions (M1 onward) derive from the NANOGrav 15-year Data Set
(Agazie et al. 2023; Zenodo `10.5281/zenodo.7967584`) under **CC-BY-4.0**. Hellings–Downs
reference points are digitized from Agazie et al. 2023 (ApJL 951 L8) for illustration.
**Independent educational tool — not affiliated with or endorsed by NANOGrav.**
