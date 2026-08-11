# M15 — eta Tel B: the recipe transfers, nothing is orbiting loudly, and the first RV limit on the object is sub-Jupiter

> **Status: archive route complete; per-nodding route running** (20 epochs fetching
> from raw; endgame chain armed). The numbers below are the archive-product route —
> on CD-35 the per-nodding route *improved* them, so these limits are, if anything,
> conservative.

**Question:** M14 validated a full extraction recipe on CD-35 2722 B. Does it
transfer to a target with no published RVs, and what does it find there? eta Tel B —
the only orbit-capable CRIRES+ archive in the class (docs/target-queue.md) — is the
test: ~47 M_Jup brown dwarf companion to the A star eta Tel, β Pic moving group,
K = 13.2, **no RV measurement of any kind in the literature**.

**Answer:** the recipe transfers cleanly (the target even shares CD-35's exact
H1567 setting), the pipeline passes every injection gate at ~100% with 4× better
stability than on CD-35, no companion is detected, and the resulting first RV limit
excludes **msini ≳ 0.5–1.2 M_Jup companions across P ≈ 20–300 d** at 90%
confidence — three times deeper than the survey forecast. A twin of the CD-35
satellite would have been seen with ~70% probability.

## 0. What ran

| artifact | what it is |
|---|---|
| [`m15_inventory.py`](scripts/m15_inventory.py) | ESO TAP inventory + the phase–BERV geometry check (the M13 §4b design rule) |
| [`m15_fetch_products.py`](scripts/m15_fetch_products.py) / [`m15_convert.py`](scripts/m15_convert.py) | product fetch + ADP→cr2res converter, rebuilt from the surviving CD-35 format, M10-style verification per file |
| [`m15_stage_tpl.sh`](scripts/m15_stage_tpl.sh) | template ladder (flat → iter1 → iter2, `-kapsig 3` creation) + RV runs |
| [`m15_inject.sh`](scripts/injection/m15_inject.sh) / [`m15_diag.py`](scripts/injection/m15_diag.py) | eta Tel injection arm; informational-only internals reader |
| [`m15_limit.py`](scripts/injection/m15_limit.py) | end-to-end injected-series detection + the sensitivity curve → [`data/m15-limit.json`](data/m15-limit.json) |
| [`m15_allnights.sh`](scripts/cr2res/m15_allnights.sh) / [`m15_nodall.sh`](scripts/injection/m15_nodall.sh) | per-epoch raw reduction + the armed per-nodding endgame |
| [`data/m15-eta-tel-inventory.json`](data/m15-eta-tel-inventory.json) | nights, products, geometry |

Rules in force: no published RVs exist for this target, so **the injection harness
carries the entire validation burden** (M9/M12: every internal metric has lied at
least once); the order set transfers by identity (same H1567 wavelength grid ⇒ the
telluric-density criterion selects the same segments); template iterations are
guarded per target; nothing is adopted on internal look.

## 1. The archive, and two more filter_path lies

34 CRIRES nights sit on the object: 8 from **old CRIRES in 2009** (a 16-year drift
hook, not usable by cr2res), the modern CRIRES+ campaign 2023–2025 (programmes
111.24M0 → 113.268Y → 115.287U — someone is actively monitoring this target), and
4 embargoed. Of 24 reduced products, **20 are H1567 — the identical setting to
CD-35 2722 B** — spanning **18 nights / 815 d** (two nights carry double visits).
The `filter_path` column lied twice more (a "J" and a "K" label, both H1567 in the
authoritative header) — the M2 trap, now confirmed three times. The one Y1029
product is excluded.

**The phase–BERV geometry passes where CD-35 failed** (`geometry_modern_H` in the
inventory): on the 17-night modern-H sampling, only 11% of the 5–460 d period grid
is BERV-degenerate (R² > 0.5), confined to slivers at 6–29 d, 138–148 d, and
> 306 d. The 150–300 d decade — where a CD-35-analog satellite would live — is
**completely clean**: a detection there would never have needed embargoed epochs to
survive a BERV covariate. This check cost ten minutes and three milestones' worth
of CD-35 pain justified it.

## 2. Extraction: the recipe transfers, and the target is kinder

ADPs converted to the cr2res layout (all 20 pass the structural checks including
CWLEN header matching), template ladder built from flat (iter0 → iter1 → iter2,
creation stabilised with `-kapsig 3` per M14), RV runs with the transferred config
(`H_C` orders, `-kapsig 3`, `-oversampling 2`; targ line from SIMBAD astrometry,
verified token-by-token against viper's positional parser):

| series (20 epochs) | epoch rms, median combine | across-order spread (median) | r(RV, BERV) |
|---|---:|---:|---:|
| E15_R1 (iter-1 template) | 127 m/s | 331 m/s | +0.05 |
| E15_R2 (iter-2 template) | 129 m/s | 378 m/s | +0.03 |

127–129 m/s per epoch on a K = 13.2 object — better than the 163 m/s the M7 survey
forecast, because the M7.5 spectrum is far richer in H-band lines than CD-35 B's
L0-1. **No RV–BERV correlation** (CD-35 sat at −0.5). The internal 3×-spread screen
(M14 §6) drops exactly one epoch: the second 2025-07-02 visit, at ~3000 m/s
across-order spread against a 331–378 median.

## 3. Injection: the cleanest gates this project has recorded

Template-shift injection (M12 §8.1), 20 single-epoch full re-runs per arm, P = 200 d
(inside the BERV-clean window):

| arm | recovery (mean / median combine) | resid rms |
|---|---|---:|
| iter-2 template, K = 1530 | 99% ± 1% / 100% ± 1% | 22–23 m/s |
| iter-1 template, K = 1530 | 99% ± 1% / 99% ± 0% | 19–24 m/s |
| iter-2 template, K = 300 (amplitude-matched) | 101% ± 1% / 97% ± 2% | 12–15 m/s |

Every order transmits at 95–108% in every arm; the ladder shows **no absorption at
either iteration** (M11's failure mode absent here too). The injection residuals —
12–23 m/s — mean the *extraction* is stable at the ~20 m/s level under template
perturbation: the 127 m/s epoch scatter is sky and instrument, not pipeline. On
CD-35 the equivalent arm scattered 88–95 m/s; this target is ~4× kinder, as its
spectral type predicts.

## 4. The blind search: nothing credible

Same machinery as M14 §6 (internal screen, mean/median/clip, ± BERV covariate),
n = 19: **no peak anywhere approaches the M14 detection regime** (which was
ΔBIC +37–43). Best features: +14.9 at 5.7 d and +11.7 at 17.6 d (median combine) —
a weak short-period comb sitting exactly in the regime the Hoy paper itself
discards as low-cadence artifacts ("periods this short are simply too difficult to
constrain"; their own 14 d alias was rejected the same way). Across the clean
150–300 d window the fitted amplitudes are 28–62 m/s and every ΔBIC near 171 d is
negative. Recorded, not claimed; the per-nodding series will re-test the comb.

## 5. The end-to-end proof, and the first RV limit on eta Tel B

**The null is meaningful because the machinery detects its own injection.** The 20
amplitude-matched runs assemble into a real injected series (K = 300, P = 200 d
through the full pipeline); the same blind search that returned the null finds it at
**rank 1, P = 196–199 d, ΔBIC +15 to +19, in all three combines**.

Transmission at ~100% with 12–23 m/s repeatability licenses a post-extraction
sensitivity grid ([`m15_limit.py`](scripts/injection/m15_limit.py)): add
K sin(2πt/P + φ) to the real screened series, demand ΔBIC ≥ 10 *and* rank 1 at the
injected period, marginalize over 12 phases:

| P | K₉₀ (90% detection) | msini limit (M_host = 47 M_Jup) |
|---:|---:|---:|
| 20 d | 300 m/s | **0.5 M_Jup** |
| 60 d | 250 m/s | **0.6 M_Jup** |
| 120 d | 250 m/s | **0.8 M_Jup** |
| 200 d | 300 m/s | **1.1 M_Jup** |
| 300 d | 300 m/s | **1.2 M_Jup** |

(The mass conversion reproduces the paper's own Msini₁ = 0.918 M_Jup from their
K₁ = 306, P = 171.45, M = 37 M_Jup — the formula is checked against the source.)

Read against the class: **the first RV constraint ever placed on eta Tel B excludes
sub-Jupiter-mass companions over most of the 20–300 d range** — 3× deeper than the
survey forecast (min 3.3 M_Jup), because the real noise beat the forecast and the
detection bar is injection-calibrated rather than assumed. A CD-35-satellite twin
(0.918 M_Jup; K ≈ 261 m/s here) would have been detected with ~70% probability;
anything ≥ 1.1 M_Jup inside 200 d, ≥ 90%.

Honest edges of the claim: msini only (inclination unknown); the φ-marginalized 90%
is grid-pointwise, not a continuous exclusion curve; the limit is the archive-route
series — the per-nodding route (running) should tighten it; the 2009 old-CRIRES
epochs and the embargoed 2025–2026 K-band epochs are untouched levers.

## 6. ⏳ Pending

- Per-nodding route: 20 epochs reducing from raw ([`m15_allnights.sh`](scripts/cr2res/m15_allnights.sh));
  endgame armed ([`m15_nodall.sh`](scripts/injection/m15_nodall.sh)): full-recipe
  series → diag → blind search → per-frame K=300 injection.
- Re-test of the weak short-period comb on the per-nodding series.
- Writeup candidate: "First radial-velocity constraints on the eta Tel B brown
  dwarf" — an RNAAS-scale null with an injection-calibrated limit, or folded into a
  method paper with the CD-35 reproduction.

## 7. For the next agent

1. Finish the per-nodding endgame when the raw pipeline lands; update §5's table if
   it tightens.
2. The 2009 CRIRES epochs: an old-instrument RV point would stretch the baseline to
   16 years for free — separate tooling (no cr2res), separate milestone.
3. The embargoed epochs release on their own schedule; re-run then.
4. beta Pic b spot-check (6 nights) is the next queue item after eta Tel closes
   (docs/target-queue.md tier 2).
