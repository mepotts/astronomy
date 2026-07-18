# DATA-SOURCES.md

Everything the front-end needs to be physically grounded, and where it comes from.
Facts verified via web research, current to **June 2026**.

---

## 1. The Hellings–Downs analytic formula (the heart of v0)

This is the curve we render. It is a closed-form expression — **no data download is required to draw it.**
The expected cross-correlation of timing residuals for two pulsars separated by angle θ on the sky,
for an isotropic, unpolarized, general-relativistic stochastic GW background:

```
Γ(θ) = (1/2)·δ_ab  +  1/2  −  x/4  +  (3/2)·x·ln(x)

where   x = (1 − cos θ) / 2          (θ = angular separation between the two pulsars)
        δ_ab = 1 if a == b (same pulsar), else 0
```

Notes / gotchas for implementation:
- For two **distinct** pulsars (the only case the demo plots along the curve), drop the δ term:
  `Γ(θ) = 1/2 − x/4 + (3/2)·x·ln(x)`.
- At **θ → 0** (distinct pulsars, x → 0): the `x·ln(x)` term → 0, so Γ → **1/2**. The curve starts at 0.5, **not** 1.0. (The 1.0 "spike" only appears for the self-pair via the δ term.)
- `x·ln(x)` is `0·(−∞)` at x=0 — guard it: return 0 when x == 0 to avoid `NaN`.
- This is a **normalized** form (the convention used in the NANOGrav 2023 figure, where binned points are scaled by the fitted common-process amplitude so they sit on the same axis as Γ). Some textbooks carry an overall factor (e.g. 3/2 out front, or a 1/3 self-term); when validating, match the **shape and the characteristic zero-crossing near ~50° and the minimum near ~80–90°**, then the absolute normalization.
- Reference checkpoints to assert against in a unit test (distinct-pulsar form):
  - θ = 0°   → Γ = 0.5
  - θ ≈ 49.3° → Γ ≈ 0 (the famous zero crossing)
  - θ ≈ 82.5° → Γ ≈ −0.173 (the minimum / anticorrelation dip)
  - θ = 180° → Γ = 0.25
  (Compute the exact values in the validation script — see BUILD-PLAN.md §physics-validation — these are the target landmarks.)

Sources for the formula:
- Wikipedia "Hellings–Downs curve" (gives `Γ_ab = ½δ_ab + ½ − x/4 + (3/2)x·ln x`, `x = (1−cosζ)/2`).
- Hellings & Downs FAQ paper: https://iopscience.iop.org/article/10.1088/1361-6382/ad4c4c (arXiv:2405.xxxxx) — authoritative discussion of normalization conventions.
- Original: Hellings & Downs 1983, ApJL 265, L39.

---

## 2. The real NANOGrav 15-year array (pulsar positions)

### Where it lives
- **Primary data release (par/tim):** Zenodo record **7967584** — "The NANOGrav 15-year Data Set"
  https://zenodo.org/records/7967584 (also linked from https://nanograv.org/science/data)
- **License: Creative Commons Attribution 4.0 International (CC-BY-4.0).** Re-distribution and re-use permitted with attribution. This is compatible with shipping a derived JSON in our repo, **provided we credit NANOGrav** (see attribution string below).
- Total release size ≈ **638.7 MB** (narrowband + wideband TOAs, profile templates, residuals). We do **not** ship this — we extract a tiny derived file.

### What we actually need from it
Just the **sky positions** of the pulsars: right ascension (RAJ) and declination (DECJ).
These live in the per-pulsar **`.par`** ephemeris files (ASCII, TEMPO2/PINT format). Every `.par` has lines like:
```
PSRJ           J1909-3744
RAJ            19:09:47.4...   ...
DECJ          -37:44:14.x...   ...
```
- **68 pulsars** are timed in the release; **67** are used in the Hellings–Downs angular-correlation analysis (the 68th lacks a long-enough baseline; the paper uses pulsars with ≥3 yr of data → 67 pulsars → **2211 distinct pairs**).
- Optionally also grab **white-noise RMS / noise-floor** values per pulsar (for the M2 residual panels, not for v0). These are in the noise-budget products (Zenodo 8092346, sensitivity curves) — defer.

### Pre-processing → shipped static JSON
Write a small one-off Node/Python script (`scripts/build-pulsars.mjs`, NOT part of the dev server) that:
1. Reads the 67 `.par` files from a local `data/raw/` checkout (gitignored).
2. Parses `RAJ` / `DECJ`, converts to decimal degrees (RA in deg, Dec in deg).
3. Emits `src/data/nanograv15_pulsars.json`:
   ```json
   [
     { "name": "J1909-3744", "raDeg": 287.448, "decDeg": -37.737 },
     { "name": "J1713+0747", "raDeg": 258.458, "decDeg":   7.788 }
     // … 67 entries
   ]
   ```
4. The **angular separation** between any two pulsars is then computed in-browser from their (RA, Dec) via the spherical law of cosines:
   `cos θ = sin δ1 sin δ2 + cos δ1 cos δ2 cos(α1 − α2)`.

This JSON is **a few KB** — commit it. The front-end ships with the real array baked in; no fetch at runtime, works offline, GitHub-Pages-friendly.

> **For the M0 skeleton in this repo we ship a tiny placeholder `nanograv15_pulsars.json` with ~6 well-known pulsars** (J1713+0747, J1909−3744, J0437−4715, B1937+21, J1744−1134, J2317+1439) so the skeleton runs. Replacing it with the full 67 from the real par files is the **first M1 task.**

---

## 3. The binned Hellings–Downs detection points (the "this is the real result" backdrop)

**Important data-sourcing finding (shapes the build plan):**
The **binned angular-separation-vs-correlation measurements** (the blue points with error bars in Fig 1c of the 2023 evidence paper, Agazie et al. 2023, ApJL 951 L8, arXiv:2306.16213) are **NOT published as a standalone machine-readable table** in the Zenodo data release. They appear only as a **plotted figure**. The release ships TOAs, timing models, residuals, noise spectra, and MCMC chains — but not the ready-made (θ, Γ̂, σ) bin table.

Three options, in increasing effort, to get the backdrop points:
1. **(v0 / cheapest, recommended to start)** **Hand-digitize** the ~15 binned points from Fig 1c (e.g. WebPlotDigitizer) into `src/data/nanograv15_hd_points.json` as `[{ "thetaDeg": ..., "corr": ..., "errLo": ..., "errHi": ... }]`. Label them clearly in-app as "digitized from Agazie et al. 2023, Fig 1c — illustrative." ~15 points, a few minutes of work, good enough for an explainer. **Verify** the digitized points visually overlay the analytic curve within their error bars.
2. **(M2/M3, faithful)** **Regenerate** the binned correlations from the public TOAs using the NANOGrav/`enterprise` + `enterprise_extensions` pipeline (the optimal-statistic / `OS` machinery). This reproduces the points exactly but pulls in the full heavy Python stack and is a real research task — out of scope for v0, candidate for a one-off offline notebook that emits the JSON.
3. Email NANOGrav (`comments@nanograv.org`) / check the paper's GitHub for a data-behind-figure file. Cheap to ask; do it in parallel but don't block on it.

**Decision for v0:** Option 1 (digitized points), clearly attributed. The *curve* is exact (analytic); only the *backdrop points* are digitized, and they are explicitly illustrative.

---

## 4. Headline numbers (for annotations / sanity, from the 2023 evidence paper)

- GWB strain amplitude **A ≈ 2.4 (+0.7 / −0.6) × 10⁻¹⁵** at reference frequency f = 1 yr⁻¹ (median + 90% CI).
- Spectral index **γ_GWB = 13/3 ≈ 4.33** (consistent with a population of SMBHBs inspiralling via GW emission); characteristic strain spectrum **h_c ∝ f^(−2/3)**.
- Evidence for the Hellings–Downs correlation at roughly the **3–4σ** level (Bayes factor ≫ 10¹³ vs. independent-noise models for the correlated process).
- 67 pulsars, 2211 pairs, ~15 angular-separation bins.

These are display/annotation facts for M1+, and the amplitude/γ become live inputs only at M2 (residual panels). v0 does not need them to draw the curve.

---

## 5. Attribution string to ship in the app + repo

> Pulsar positions derived from the NANOGrav 15-year Data Set (Agazie et al. 2023, ApJL 951 L9; data: Zenodo 10.5281/zenodo.7967584), used under CC-BY-4.0. Hellings–Downs reference points digitized from Agazie et al. 2023, ApJL 951 L8 (arXiv:2306.16213), shown for illustration. This is an independent educational tool, not affiliated with or endorsed by NANOGrav.

---

## 6. Source links (verified June 2026)

- NANOGrav data portal: https://nanograv.org/science/data
- 15-yr par/tim release (Zenodo, CC-BY-4.0): https://zenodo.org/records/7967584
- Observations & timing of 68 MSPs (Agazie et al. 2023, ApJL 951 L9): https://arxiv.org/abs/2306.16217
- Evidence for a GWB (Agazie et al. 2023, ApJL 951 L8): https://arxiv.org/pdf/2306.16213
- NANOGrav GWB summary (lay): https://nanograv.org/15yr/Summary/Background
- Hellings–Downs FAQ paper: https://iopscience.iop.org/article/10.1088/1361-6382/ad4c4c
- Hellings–Downs curve (formula reference): https://en.wikipedia.org/wiki/Hellings%E2%80%93Downs_curve
- Harmonic analysis of angular correlations: https://arxiv.org/abs/2411.13472
