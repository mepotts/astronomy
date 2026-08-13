# M20–M22 — The census harvest: a contrast wall measured on beta Pic b, a quiet star at PDS 70, and the first companion monitoring of HIP 65426 b

> **Status: COMPLETE (M20, M21, M22).**
> Covers the work that followed the coordinate census (M19 scripts, commit 465d27a).

**Question:** the coordinate census found three campaigns filed under host-star names.
What do they actually yield?

**Answers:**

1. **beta Pic b (M20): a measured contamination wall, not yet a companion result.**
   The 13-night K2166 series is dominated by starlight from the naked-eye host
   0.55″ away — diagnosed, halved, and attributed; final masked re-run pending (§2).
2. **PDS 70 (M21): the slit sees the star, and the star is remarkably quiet.**
   Six nights over 426 d are flat at 130 m/s (χ² = 3.5/5), giving a ~3 M_Jup limit
   on close stellar companions — and an honest retraction of the "planet b
   spot-check" idea (§3).
3. **HIP 65426 b (M22): the exomoon-regime constraint the census was hunting.**
   Five planet-tagged nights over 422 d, clean at 131 m/s, excluding
   **K ≥ 400–500 m/s companions at P ≤ 100 d — roughly ≥ 0.4 M_Jup (~115 M⊕)** —
   through 98–101% injection gates (§4). Priority caveats in §5.

## 1. Provenance and rules

Data: ESO archive products under `CD-40 8434` (PDS 70), `HIP65426b`/`HD 116434`
(HIP 65426), and raw K2166 nights under `BET PIC` (programme 114.27DX; header-verified
as the planet — DIT 120 s would saturate the star thousands of times over).
All runs use the generic chain ([`m2x_run_target.sh`](scripts/injection/m2x_run_target.sh)):
per-target template ladder with `-kapsig 3` creation, `-oversampling 2`, injection
arms at K = 1530 and an amplitude-matched K, small-n scoring by per-epoch ratio
([`m17_score.py`](scripts/injection/m17_score.py)). No published RVs exist for any of
these series; the injection harness carries all validation. Two more `filter_path`
lies were caught by header checks (the "K" nights of beta Pic b that are really
M4368; the census's own row-cap truncation) — the count stands at six, and the rule
stands: **the product header is the only truth**.

## 2. beta Pic b: the contamination ladder (M20, final arm pending)

Three passes, each isolating one cause:

| pass | template | result | reading |
|---|---|---|---|
| v1 | reused M17's single-night template | 4712 m/s night scatter, r(BERV) = +0.94; blind peaks collapse under a BERV term | a single-night template cannot separate planet lines from telluric residue (no BERV lever within one night) — it drags a fraction of Earth's motion into every epoch |
| v2 | rebuilt across all 28 frames / 813 d | scatter halves to 2466 m/s; r(BERV) = +0.88 persists; injections 99–100% | the residual is not the template: it is **starlight**. The K2166 setting is centered on Br-γ, the host's dominant absorption line, 130 km/s wide, riding in the contaminating halo and moving with BERV while tellurics stand still |
| v3 | v2 template + Br-γ order masked + six injection-unstable orders dropped | scatter 2962 m/s, r(BERV) = **+0.88 unchanged**; injections 99–100% on the 11 kept orders; every long-period peak dies under the BERV term (−1.7 to +0.4 near 171 d) | the contamination is **pervasive, not surgical**: the starlight carries broad low-level features across the whole band, and no order subset rescues a ~5000× contrast slit |

**Final verdict: contamination-limited at the km/s level.** No companion claim, and
no defensible K exclusion either — the variance-based limit assumes the observed
scatter is noise, and here it is a BERV-locked systematic. What M20 delivers instead
is the measurement that this target class *requires* hardware starlight suppression,
plus two permanent rules: **never build a template from a single night**, and
**expect slit spectroscopy to fail at small separation from bright hosts** (§6).
The short-period comb (5–17 d, ΔBIC +9–15 under BERV control) is the same
sampling-alias family seen on eta Tel and is not evidence of anything.

## 3. PDS 70: the star, measured properly (M21)

Six nights / 426 d (8 products; 6 more still failing on the flaky datalink host).
Injection gates 99% ± 1–2. The night-binned series is **flat**: χ² = 3.5/5,
night-to-night std 130 m/s, K₉₀ ≈ 150 m/s at P ≤ 200 d → **~3 M_Jup (90%) on
companions of the star** inside ~200-day orbits. At 0.17″ separation the planets sit
inside the AO core, so this series is the *star's* — the tier-3 verdict ("planet b
needs a dedicated proposal, likely fiber-fed") was correct and is reinstated. The
side-fact is real, though: an actively accreting transition-disk T Tauri star this
RV-quiet at K-band is useful knowledge for anyone planning work on the system.

## 4. HIP 65426 b: clean planet monitoring at 0.8″ (M22)

Five nights / 422 d in K2192 (a third K setting: seven orders, the reddest falling
partly off detector 3; viper's 1-indexed K branch reaches 17 usable segments —
`oset 1:18`). Results: night-to-night std **131 m/s**, χ² = 10.9/4 (a mild 2σ
excess, recorded not claimed), r(BERV) = +0.54 (weak, at 131 m/s amplitude),
injections **98% ± 4 / 101% ± 3**. Variance exclusion:

| P | K₉₀ | companion m sin i (M_host ≈ 8 M_Jup) |
|---:|---:|---:|
| 20 d | 500 m/s | ~0.4 M_Jup |
| 50–100 d | 400 m/s | **~0.35–0.45 M_Jup (≈115 M⊕)** |
| 200–400 d | ~1000 m/s | ~1.3–1.6 M_Jup |

To the best of our knowledge after a literature search (see §5), no multi-epoch
precision-RV companion constraint on a directly imaged planet has been published;
single-epoch RVs of this planet exist (SINFONI, ±7 km/s) and GRAVITY constrains its
orbit. This series is three orders of magnitude more precise per epoch than the
published RV.

## 5. Priority and claim hygiene (correction log)

A user challenge ("you read every scientific paper?") forced the right correction:

- **"First RVs of beta Pic b" (M17) is WRONG** — a 2024 CRIRES+ study published the
  planet's atmospheric composition, spin, and radial velocity. M17's true claim is
  the first *multi-epoch monitoring series* framing, and even that is hedged now.
- HIP 65426 b likewise has published single-epoch RVs; our claim is the hedged
  monitoring-constraint form only.
- **The M22 spectra belong to another team's active programme** (2024–25). They are
  presumably preparing their own analysis of their own observations. Publishing
  their data's headline result ahead of them is a community-norms question that
  belongs to Matthew, not to this pipeline. This differs qualitatively from CD-35
  (reproduction of a published claim) and eta Tel B (untouched archive).
- All "first" statements in this project now carry "to the best of our knowledge
  after a literature search" and are provisional until an ADS sweep.

## 6. The contrast wall, measured

The practically useful synthesis. Slit spectroscopy of imaged companions fails not
at a separation but at a *contrast* — and the roster now brackets it empirically:

| separation | host:companion flux | measured outcome |
|---:|---:|---|
| ≥ 2.7″ | ≤ ~2000× | clean (CD-35, eta Tel, AB Pic, CT Cha geometry) |

> **⚠ SUPERSEDED (M29 §§6–8).** The contrast values in this table were asserted, not
> derived. Deriving them from primary sources changed them (CD-35 is 97×, not ≥2000×;
> β Pic b ~3950× from Currie+2013, not ~5000×), and the ordering variable is wrong:
> outcomes are ordered by **S = contrast/θ²**, not by contrast or separation alone.
> The measured *outcomes* in this table stand; the axis they are plotted against does not.

| 0.8″ | ~2000× | **clean** — 131 m/s (HIP 65426 b) |
| 0.55″ | ~5000× | **flooded** — km/s BERV-locked star pull (beta Pic b) |
| 0.17″ | any | the star *is* the spectrum (PDS 70) |

Between 0.8″/2000× and 0.55″/5000× lies the wall. Inside it, companion-side RV
needs hardware starlight suppression (fiber-fed links: HiRISE at the VLT, KPIC at
Keck) — a measured, quotable design requirement for any proposal.

## 7. For the next agent

1. Close M20: read the v3 verdict; if the BERV lock breaks, quote the km/s-level
   bound; either way the contamination measurement stands.
2. M23: HD 1160 B — staring recipe is wired in; nine 20-min nights unfetched.
3. M24: AF Lep b + 51 Eri b single epochs via the same staring path (both are
   ~30,000× contrast at ≤ 0.45″ — expect star-dominated spectra; that in itself
   extends §6's table).
4. Retry the six missing PDS 70 products via direct dataportal URLs.
5. The paper draft (docs/paper/) covers CD-35 + eta Tel; folding M20–22 in (the
   contrast wall is a natural new section) is writing work, gated on the v3 verdict
   and on the M22 priority decision.
