# M15 — eta Tel B: the recipe transfers, nothing is orbiting loudly, and the first RV limit on the object is sub-Jupiter

> **Status: COMPLETE.** Both routes ran: archive products and the full per-nodding
> recipe from raw (all 20 epochs reduced, zero failed downloads). The per-nodding
> route confirms the archive route at equal depth — §6.

**Question:** M14 validated a full extraction recipe on CD-35 2722 B. Does it
transfer to a target with no published RVs, and what does it find there? eta Tel B —
the only orbit-capable CRIRES+ archive in the class (docs/target-queue.md) — is the
test: ~47 M_Jup brown dwarf companion to the A star eta Tel, β Pic moving group,
K = 13.2 [**CORRECTED M32: K_s = 11.6 ± 0.1**, Neuhäuser et al. 2011; Lazzoni's
13.2 is wrong by 1.6 mag], **no RV measurement of any kind in the literature**.

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
forecast

> **⚠ CORRECTED IN M32 — THIS COMPARISON INVERTS.** The magnitude was wrong: K_s
> is **11.6**, not 13.2 (Neuhäuser et al. 2011). At the true brightness the M7
> forecast is **78 m/s**, not 163, so the achieved 127–129 m/s is **1.6x WORSE than
> forecast, not better**. The null, the injection gates and the published limit are
> unaffected — none of them uses the magnitude — but the "beats the forecast" claim
> is withdrawn and is absent from the RNAAS draft. `survey.py` and
> `data/m7-survey.json` are corrected.

, because the M7.5 spectrum is far richer in H-band lines than CD-35 B's
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

## 6. The per-nodding route confirms at equal depth

All 20 epochs were fetched raw and reduced through the cr2res cascade (zero failed
downloads — the ESO archive cooperated twice in one day), giving 40 per-nodding
frames. The full paper recipe (iter-2 template, `H_C`, `-kapsig 3`,
`-oversampling 2`, bin A/B; double-visit nights merge under the 0.2 d binning →
18 nights):

- **Per-frame injection (K=300, P=200, 40 full re-runs): 100% ± 3% mean /
  94% ± 2% median, residuals 19–26 m/s.** Every order 87–117%. The per-nodding
  pipeline transmits as cleanly as the archive one.
- **Blind search: the null holds.** Every variant in the 150–300 d clean window is
  negative (ΔBIC −2.7 to −4.8 near 171–182 d; fitted K only 40–116 m/s). Per-night
  precision ≈ 130 m/s — parity with the archive route, not the ~20% gain CD-35
  showed; the resampling penalty the per-nodding route avoids is evidently not the
  limiting noise on this target.
- **The short-period comb is behaving like an alias, not a signal.** On the archive
  series it led at 5.7 d; here it leads at 7.1/10.0/12.1 d — different periods,
  inconsistent across combines (median +13.7 at 10.0 d, but mean/clip only +5 to
  +11), all inside the < 20 d regime the Hoy paper itself rejects as low-cadence
  artifacts. Its strongest variant (+25.6 at 7.1 d) appears only *with* the BERV
  covariate in the model — the opposite of robustness. Not claimed; a proper
  window-function/alias analysis is the follow-up if anyone wants to chase it.

The §5 limit therefore stands as quoted, now confirmed by two independent
extraction routes.

## 7. For the next agent

1. Writeup: "First radial-velocity constraints on the eta Tel B brown dwarf" — an
   RNAAS-scale null with an injection-calibrated limit, or the second half of a
   method paper with the CD-35 reproduction (M14). All numbers, scripts and JSONs
   are in place.
2. The 2009 CRIRES epochs: an old-instrument RV point would stretch the baseline to
   16 years for free — separate tooling (no cr2res), separate milestone.
3. The embargoed 2025–26 epochs release on their own schedule; re-run then.
4. beta Pic b spot-check (6 nights) is the next queue item
   (docs/target-queue.md tier 2).
5. If the short-period comb itches: window-function analysis first (M4's machinery
   exists in `analysis/aliases.py`), and remember it must survive all three
   combines and both routes before it is anything.
