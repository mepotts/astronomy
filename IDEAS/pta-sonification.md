# PTA/GW Sonification & Accessibility Layer

**One-liner:** A small Web Audio sonification module + accessibility pass that lets you *hear* pulsar-timing residuals and the Hellings–Downs correlation, and makes the sibling `pta-explainer` usable non-visually (keyboard, ARIA, audio) — turning the nanohertz gravitational-wave story into an inclusive outreach piece.

**Scores (U/B/E):** U 5 (accessibility/sonification had *zero* presence in run 1; PTA-specific audio is genuinely empty white space) · B 5 (pure data+software, the physics already exists in the TS repo, tiny surface, no data acquisition) · E 4 (first-ever audio of the nHz background/HD curve + a real inclusion win — but outreach-weight, not a citable dataset; the lightest idea in the portfolio by design)

**Status:** proposed

## The wedge
- **What exists (adversarial prior-art check).** Astronomy sonification is a crowded, mature space — but every existing tool is either a *different signal* or a *generic engine*, none touch PTAs:
  - **Astronify** (STScI; PyPI `astronify`; efficacy study MNRAS 516, 5674, 2022) — Python light-curve sonification (time→time, flux→pitch), aimed at MAST. Not PTA, not browser, not a *correlation* curve.
  - **STRAUSS** (Trayford et al.; JOSS 2025; arXiv:2504.01660, intro arXiv:2311.16847; PyPI `strauss`) — the flexible, general Python sonification *engine*. This is a tool to **build on** for offline renders, not a competitor.
  - **A Universe of Sound / SYSTEM Sounds / Chandra** (Arcand, Russo, Santaguida; blind-community consultant Christine Malec; Frontiers in Communication 2024, arXiv:2403.18082) — the gold standard for sonification-as-inclusion, but *fixed* renders of images/light curves/the Perseus "black-hole song," not an interactive, keyboard-drivable tool, and not PTAs.
  - **LIGO / GWOSC chirps** (gwosc.org/audio; SYSTEM Sounds; lensed-GW sonification arXiv:2407.09588) — GW audio, but in the **audio band** (~kHz, ~0.2 s), a near-direct frequency-to-sound shift. The nanohertz PTA band is ~16–17 orders of magnitude lower (periods of *years*): it *cannot* be played directly and needs a deliberate time-compression mapping — a different design problem nobody has solved for outreach.
  - **"Pulsar sounds"** (Jodrell Bank / Weltevrede; Paul Bourke's Vela render) — the iconic beeps are the pulsar *rotation* (Hz–kHz, directly audible). That is a *different quantity* from the nanohertz timing-residual wander or the GWB correlation. Must be distinguished honestly so we don't claim "pulsars have never been sonified."
  - **Jenet & Romano 2015** (arXiv:1412.1142; Am. J. Phys. 83, 635) — "Understanding the HD curve … in terms of sound and EM waves." **Nearest miss, and the biggest novelty risk to name:** it uses acoustic waves as a *mathematical analogy* to explain HD — there is **no audio artifact you listen to**. So "no one has produced actual audio of the HD correlation / the nHz background" survives, but this paper must be cited and distinguished (analogy vs. artifact).
  - **Web accessible-chart sonifiers** — Highcharts Sonification module + Sonification Studio; `sonifier` (Ather Sharif, UW; ASSETS 2022); `sound3fy` (Ismael Martinez, D3.js); Erie declarative grammar (arXiv:2402.00156). All *generic* chart sonifiers with keyboard/ARIA; none carry PTA physics. We can reuse their patterns (and even sit on top of Tone.js / a generic sonifier) rather than reinvent them.
- **The defensible gap.** Two things are unoccupied at their intersection: (1) **PTA-specific sonification** — mapping the timing residuals, the correlated Earth-term wiggle, and the Hellings–Downs curve to sound with an honest year→second time compression; (2) **sonification wired into an interactive, keyboard-accessible explainer** rather than a fixed render. `pta-explainer` already ships the physics (`src/physics/residuals.ts`, `hellingsDowns.ts`) and the controls — an agent can bolt on an audio module + a keyboard/ARIA pass cheaply, because there is no data to acquire and no service to run.
- **Why now.** The 2023 NANOGrav 15-yr detection made the nHz background famous; sonification-for-inclusion is a live funding/outreach priority (NASA's A Universe of Sound; JOSS accepting STRAUSS in 2025); and `pta-explainer` is already **built and deployed** (mepotts.github.io/pta-explainer), so the marginal cost of an accessibility + audio layer is tiny.

## Target user & the "who cites this" test
- **Primary user:** outreach audiences and, specifically, blind/low-vision learners and educators — the moment is a planetarium show, an astrobites reader, or a screen-reader user landing on the explainer who today hits a mouse-only sky map and silent SVGs. Secondary: sighted learners for whom "hearing the sign change" is a genuinely better intuition pump than seeing it.
- **Citable / referenceable, not just consumable:** the right-sized legitimacy for something this small is an **RNAAS** note ("Sonifying the nanohertz gravitational-wave background") and/or an **astrobites** post, a **Zenodo DOI** on the render set (WAV/MP4), and a **STRAUSS example** contributed upstream. A tiny `pta-sonify` npm/PyPI package gives an importable, versioned reference. This is outreach/education legitimacy, not a professional dataset — state that plainly.

## Data sources & access
- **No data acquisition.** The "signal" is the physics *already in the repo*: `sampleResidualSeries` / `residualMultiSec` (residual time-series), `earthTermResidualSec`, and `hellingsDownsDeg` (the correlation curve), over the real 67-pulsar NANOGrav-15 positions in `src/data/nanograv15_pulsars.json`.
- **Browser audio:** **Web Audio API** (native, no dependency, no auth) for the minimal path; optionally **Tone.js** (npm `tone`, MIT) for scheduling/synths if the raw API gets unwieldy. Account-free.
- **Offline/outreach renders:** **STRAUSS** (PyPI `strauss`, free/OSS) to produce high-quality WAV/stereo/multichannel renders; optionally seeded from the real **NANOGrav 15-yr** residual products (already cited in-app: Zenodo `10.5281/zenodo.7967584`, CC-BY-4.0). All account-free/offline.
- **Honesty constraint (load-bearing):** sonification here is **pedagogy/outreach, not measurement**. The mapping is illustrative — it never implies audio is a detection method. This mirrors the explainer's existing "illustrative sources, not the stochastic background" framing.

## Architecture sketch
Keep it minimal-runnable-first; this is a *feature + a small module*, not a service.
- **In `pta-explainer` (TS/Vite, no framework):**
  - `src/audio/sonify.ts` — pure, testable functions mapping a `ResidualSample[]` and the HD curve to Web Audio events: year→second time compression (a single explicit constant), residual amplitude→pitch (and/or stereo pan), HD correlation→a pitch that sweeps as θ goes 0→180°. Reuses the existing physics; no new physics.
  - A small **"Listen" toggle** + play/pause, following the accessible pattern already in `src/components/annotations.ts` (aria-expanded/controls/label).
  - **Accessibility pass:** keyboard nav for the sky map (`SkyMap.ts` is mouse-only today — `.on("click", …)`, no focusable dots), i.e. roving `tabindex` + arrow-key movement + Enter to pick; an ARIA **live region** in `main.ts` announcing θ and the selected pair; focus management; a `prefers-reduced-motion` guard on the animated residual wiggle. The SVGs already carry `aria-label`s — a foundation to build on.
- **Optional tiny standalone lib `pta-sonify`** — extract the mapping functions as a framework-agnostic Web Audio module (or a thin STRAUSS recipe), small enough to stay a single-purpose package.
- **Optional Python outreach script** — STRAUSS-based renderer for planetarium/astrobites WAV/MP4.

## Milestones
- **M0 — kill checks (cheap disproofs).** (a) Prior-art: confirm no polished PTA/HD/nHz-background *audio* exists — searches already show only the analogy paper, audio-band LIGO chirps, and rotation "pulsar sounds"; email Trayford (STRAUSS) and Arcand/Russo (A Universe of Sound) to ask if PTA sonification is on their roadmap. (b) Technical smoke test: Web Audio plays one `sampleResidualSeries` in the browser. (c) Intelligibility gut-check: does the year→second mapping actually let a listener perceive the HD sign change / anticorrelation? **Acceptance:** a one-page prior-art memo + a working in-browser tone from real residual data. **Kill if** a polished interactive PTA sonification already exists, or the mapping conveys nothing.
- **M1 — thin accessible slice.** A working "Listen" toggle that sonifies the *selected pulsar's* residual series, plus a keyboard-selectable sky map and an ARIA live region announcing θ/pair. **Acceptance:** a keyboard-only + screen-reader user can select a pulsar, hear its residual, and hear the selection announced; unit test on the mapping function; axe/Lighthouse a11y check with no critical violations.
- **M2 — the correlation, audible.** Sonify the HD curve (sweep θ 0→180°: pitch = correlation, so you *hear* the ~49° zero-crossing and the ~82° anticorrelation dip) and two-pulsar correlated-residual playback (hear correlation vs. anticorrelation). Extract `pta-sonify`. **Acceptance:** the HD sweep audibly reproduces the curve's sign changes; lib published.
- **M3 — distribution.** STRAUSS offline renders + one outreach piece (astrobites post / planetarium clip); a WCAG 2.2 AA conformance statement for the explainer. **Acceptance:** published render set (Zenodo DOI) + one outreach artifact live.

## First week / first tasks
- Read the `residuals.ts` / `hellingsDowns.ts` APIs and pick the exact mapping (time-compression constant; residual→pitch; stereo use).
- Prototype Web Audio playback of a single `sampleResidualSeries` behind a throwaway button; sanity-check intelligibility.
- Add keyboard navigation + focus to `SkyMap.ts` (roving tabindex, arrow keys, Enter) and an ARIA live region in `main.ts`.
- Write the mapping unit test; run an axe/Lighthouse pass to baseline current a11y debt.
- Send the two prior-art emails (Trayford; Arcand/Russo) and log answers in the M0 memo.

## Risks & kill criteria
- **Someone already built it** — a polished, interactive PTA sonification surfaces → kill or pivot to pure accessibility.
- **Unintelligible mapping** — listeners can't perceive the HD sign change → redesign the mapping or drop the "hear the correlation" claim (accessibility pass still stands on its own).
- **Over-claiming** — never imply audio == detection; the honesty framing is non-negotiable.
- **Accessibility theater** — a half-done ARIA/keyboard pass is worse than none; must be tested with a real screen reader / AT, not just an automated linter.
- **Scope creep** — this must stay a feature + small lib; if it starts wanting a backend or a big dataset, it has drifted.

## Distribution & legitimacy
- **Primary:** fold into the already-deployed `pta-explainer` as a toggle + a11y pass (immediate reach, zero new hosting).
- **Package:** optional `pta-sonify` on npm (and/or a PyPI STRAUSS recipe) — versioned, importable.
- **Citable:** an **RNAAS** note and/or an **astrobites** post (JOSS is too heavy for this size); **Zenodo DOI** for the render set; contribute a **STRAUSS example** upstream. **WCAG 2.2 AA** statement as the accessibility credential.

## Rough size
Small — **M1 in ~3–5 focused days** (the physics already exists in TS; the work is one audio module + a keyboard/ARIA pass on an app that's already built and deployed). **Biggest uncertainty:** whether the nanohertz→audio mapping is genuinely *intelligible and pedagogically useful* — i.e., does a listener actually perceive the Hellings–Downs sign change? That's a design-and-test question to settle in M0, not a build risk.
