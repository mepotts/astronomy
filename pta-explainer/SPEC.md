# SPEC — Pulsar Timing Array / Hellings–Downs Interactive Explainer

> Source of truth: the verified research dossier
> `c:\Users\matth\projects\idea-research\astronomy\shortlist\02-pulsar-timing-array-explainer-simulator.md`
> This SPEC reproduces that dossier verbatim (Part 1), then tightens it into a v0 build target (Part 2).

---

## Part 1 — Verified dossier (reproduced)

### Pulsar Timing Array Explainer & Simulator
`[sources: gw-universe.org, nanograv.org, github/fakepta, arxiv:2511.08966, arxiv:2106.13662]`

**Pitch (refined):** A browser-native interactive sandbox where a user drags nanohertz gravitational-wave source parameters (chirp mass, separation, sky location of a SMBHB pair) and watches correlated timing residuals update in real time across a simulated array of ~30 pulsars, with the Hellings-Downs correlation curve rendering live below. Backed by real NANOGrav 15-year data release timing parameters (publicly available at data.nanograv.org) for the pulsar positions and noise floors, so the residual amplitudes are physically grounded, not illustrative cartoons.

**Landscape (verified):** Adversarial search found three plausible rivals; none fill the gap.

- **GW Universe Toolbox** (gw-universe.org, Python package + web form, arxiv:2106.13662) is the strongest competitor. It covers PTAs (EPTA, PPTA, NANOGrav, IPTA) and outputs detection statistics. However: it is a batch-run scientific tool for researchers, not an interactive real-time sandbox; it returns detection-probability numbers, not timing-residual plots; there are no drag-and-update sliders; and its audience is explicitly "astronomers in different fields," not undergraduates or the public.
- **PINT + pintk** (Python GUI, pip-install-only) lets researchers inspect and fit timing residuals interactively, but it requires local Python installation, expert knowledge of TOA files, and has no GW pedagogical layer at all.
- **fakepta** (github.com/mfalxa/fakepta) generates synthetic PTA data as ENTERPRISE pickle files — purely a research pipeline tool; no visualization, no educational framing.
- **NANOGrav outreach** (nanograv.org/collaboration/impact) consists of school visits, Jupyter notebooks at researcher level, and the Pulsar Search Collaboratory (discovering pulsars, not explaining PTAs). No browser sandbox exists.
- **LIGO educational tools** offer museum-grade GW detector interactives (Space Time Quest, Black Hole Pong) but nothing analogous for the PTA/nanohertz regime.

The gap is real: there is no maintained, publicly accessible, browser-based tool that lets a non-expert drag GW source parameters and watch timing residuals and Hellings-Downs correlations respond in real time. The 2023 NANOGrav 15-year evidence announcement generated enormous public interest with essentially no interactive companion tool to explain what timing residuals or spatial correlations actually look like.

**Agent-MVP (1 week):** A three-agent pipeline: (1) Data-prep agent fetches the NANOGrav 15-yr published pulsar positions and white-noise RMS values from the public data release (JSON/HDF5 at data.nanograv.org), distills them into a static JSON config of ~30 pulsars with sky coordinates and noise floors. (2) Physics-engine agent (Python → compiled to WebAssembly via Pyodide, or pure JS) implements the analytic timing residual formula for a monochromatic SMBHB: h(t, chirp_mass, f_gw, sky_position) → per-pulsar residual time series. (3) UI agent scaffolds a React + D3 (or Observable Framework) page with three sliders (log chirp mass, GW frequency, source RA/Dec) and two live panels — residual time series for each pulsar and the accumulated Hellings-Downs scatter plot. Artifact out: a static HTML/JS bundle deployable to GitHub Pages, no server required. All within a one-week agent sprint producing a working demo at a public URL.

**90-day arc:**
- **Week 1-2:** Agent-MVP as above. Validate residual amplitudes against published NANOGrav sensitivity curves. Deploy to GitHub Pages. Post to NANOGrav Slack/mailing list and r/AskAstronomy for early feedback.
- **Week 3-6:** Add a second GW source (to show superposition of residuals), add a "detection threshold" overlay so users can see when a signal would be detectable, and add an explainer annotation layer keyed to each slider. Incorporate EPTA/PPTA pulsar sets as switchable array configs. Optional: Jupyter notebook version for classroom use.
- **Week 7-10:** Write a 1-2 page companion explainer targeted at physics undergrads. Submit to AAS Nova "Astrobite"-style outlets and the IAU Office of Astronomy for Development. Reach out to the NANOGrav Education & Public Outreach lead (listed on nanograv.org) and EPTA outreach contacts to request endorsement or hosting.
- **Day 90:** Tool is live, cited by at least one outreach blog post, and handed to NANOGrav EPO or IPTA for long-term maintenance. Optionally wrap in a Zooniverse-style citizen-science shell where users classify whether a given residual pattern is consistent with a GWB.

**Risks / kill criteria:**
- WebAssembly/Pyodide overhead may make real-time drag-to-update too sluggish for the full 30-pulsar array — mitigation: precompute a parameter grid and interpolate in JS, dropping the Pyodide dependency entirely.
- NANOGrav or IPTA might release their own official interactive explainer in the 12 months following the 15-yr data hype cycle — monitor nanograv.org/news. Kill if an official tool appears with comparable interactivity before Week 3.
- The Hellings-Downs visualization has been done in static form in several review papers; if a slick static D3 notebook already exists (check Observable HQ before coding), pivot to adding the dynamic parameter-drag layer on top rather than building from scratch.
- Physics correctness risk: the monochromatic SMBHB timing residual formula is analytically simple, but stochastic GWB superposition requires Monte Carlo — keep MVP to the single-source illustrative case to avoid misrepresenting the science to a lay audience.

**Tag:** solo-side-project · **Underexplored:** 5/5 · **Agent-buildable:** 5/5 · **Excitement:** 4/5

**Sources:**
- https://www.gw-universe.org (Gravitational Wave Universe Toolbox — closest rival)
- https://arxiv.org/abs/2106.13662 (GW Universe Toolbox paper)
- https://nanograv.org/collaboration/impact (NANOGrav outreach; no browser simulator found)
- https://github.com/mfalxa/fakepta (fakepta — researcher-only pipeline tool)
- https://arxiv.org/html/2511.08966v1 (Dawn of GW Astronomy at light-year wavelengths review, Nov 2025)
- https://iopscience.iop.org/article/10.1088/1361-6382/ad4c4c (Hellings-Downs FAQ paper)
- https://arxiv.org/pdf/2505.18639 (Detecting GWs with light — undergraduate-level review, May 2025)

---

## Part 2 — What we build first (v0)

> The dossier's **adjacent angle is the MVP.** We do NOT start with the full draggable-SMBHB sandbox (that's M2–M3). We start with the single most legible, most defensible artifact: the famous 2023 detection figure, made interactive.

**v0 = the Hellings–Downs Live Demo.** A single static web page in which the user (a) sees the real NANOGrav 15-year array of 67 pulsars plotted on a sky map, (b) picks any two of them (or drags a slider that sets an arbitrary angular separation θ from 0° to 180°), and (c) watches a marker travel along the analytic Hellings–Downs curve — Γ(θ) = ½ − x/4 + (3/2)·x·ln x with x = (1−cos θ)/2 — rendered live against the published curve, with the NANOGrav 15-yr binned correlation points shown as the static "this is what the real detection looked like" backdrop. No Pyodide, no Monte-Carlo, no time-series residuals yet: just the quadrupolar correlation signature that *is* the headline result, computed analytically in plain JS, validated against the published curve to sub-percent accuracy, and shipped as a zero-backend GitHub-Pages bundle. This de-risks the single biggest threat in the dossier (physics-correctness for a lay audience) before any heavier simulation is attempted, and it stands alone as a useful explainer even if the project stops at M1.
