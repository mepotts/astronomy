# M3 — The reproduction verdict, decided by a positive control

**Question:** M2 extracted RVs that showed no 169-day signal. Is that because the pipeline
is not precise enough, or because it is not working at all?

**Answer: not precise enough — and the difference was settled by a control, not by argument.**
Run against **GJ 229 B**, a brown dwarf with a *known, undisputed* 12.1-day binary companion,
the same pipeline recovers highly significant variation at the known period. It measures real
radial velocities. It is simply 25–60× too coarse to see a 246 m/s signal.

**Verdict: the CD-35 2722 B detection is neither confirmed nor contradicted by this work.**

---

## 1. Why a control was necessary

M2 produced RVs with ~800 m/s scatter and no signal at 169.45 d. On its own that is
uninterpretable. Two very different worlds produce it:

- the extraction works and is merely imprecise, or
- the extraction is emitting noise dressed as velocities.

Nothing internal to a null distinguishes them. M5 had already identified the object that
does: **GJ 229 B** — the archetypal T dwarf, resolved in 2024 by VLTI/GRAVITY *and CRIRES+*
into a close binary (Xuan et al. 2024, *Nature*). Its parameters:

| Quantity | Value |
|---|---|
| Period | 12.1 d |
| Semi-major axis | 0.042 au |
| Component masses | 38.1 and 34.4 M_Jup |
| Total (dynamical) | 71.4 ± 0.6 M_Jup |
| Distance | 5.8 pc |

The implied reflex amplitude is **K = 18.07 km/s** — 23× the scatter M2 achieved. A pipeline
that cannot see that is not measuring velocities.

16 public reduced products exist, over 6 nights, **all in H1567** — the identical setting to
CD-35 2722 B, so the identical pipeline applies with no new code.

## 2. The control fails with a mismatched template, and passes with a matched one

First attempt used the CD-35 2722 B template (L0–1) on GJ 229 B (T6.5). Result: reduced χ²
about a constant of **0.53**, night-to-night scatter (2691 m/s) *below* the within-night
noise (3028 m/s). No signal whatsoever.

Rerun with a template built from GJ 229 B itself:

| | mismatched template | matched template |
|---|---:|---:|
| within-night rms (noise) | 3028 m/s | **1847 m/s** |
| night-to-night rms | 2691 m/s | **4100 m/s** |
| reduced χ² about a constant | 0.53 | **5.36** |

**Template spectral match is not a refinement; it is the difference between a working
extraction and a broken one.** A single wrong choice there turns a real 18 km/s signal into
nothing. Any future null from this pipeline is meaningless unless the template matches.

The within-night triplets are what make this measurable: a 12.1-day period moves the RV by
under 0.5 km/s in an hour, so scatter within a night is noise almost by construction. That
gives an honest per-epoch precision of **~1850 m/s**, independent of the formal errors — which
M2 had already shown to be untrustworthy.

## 3. The signal is recovered at the known period

Fitting a circular signal at fixed period, with the errors set to the measured 1847 m/s:

| Model | χ² | dof | reduced χ² |
|---|---:|---:|---:|
| constant | 80.4 | 15 | 5.36 |
| **P = 12.1 d (known, fixed)** | **16.6** | 13 | **1.28** |

**Δχ² = 63.8 for two extra parameters.** The known binary explains the data; a constant does
not. That is the control passing.

The period is *not* uniquely recovered from six nights — a blind scan prefers 2.3–3.4 d
aliases, with 12.162 d in the top eight. That is expected from this sampling and is not a
failure of the extraction: it is the same aliasing pathology M4 quantified for CD-35 2722 B.

## 4. The recovered amplitude is suppressed, and that is correct

The fit at 12.1 d gives **K = 6165 m/s**, only 34% of the 18.07 km/s implied by the masses.
This is not a shortfall in the extraction — it is a property of the target.

GJ 229 Ba and Bb are **unresolved and double-lined**. A single-template fit tracks the
flux-weighted centroid, and because the components move in antiphase their contributions
partly cancel. For a luminosity ratio f = L_Bb/L_Ba the centroid amplitude is
approximately (K_Ba − f·K_Bb)/(1 + f):

| f | centroid K (m/s) |
|---:|---:|
| 0.0 | 18070 |
| 0.4 | 7190 |
| **0.45** | **6165 ← measured** |
| 0.6 | 3790 |
| 1.0 | −970 |

**The measurement implies L_Bb/L_Ba ≈ 0.45**, entirely reasonable for 38.1 vs 34.4 M_Jup,
where a 10% mass difference produces a substantial luminosity difference. The suppression is
quantitatively consistent, so the amplitude corroborates the control rather than undermining
it. *(The luminosity ratio is inferred here, not sourced; it is a consistency check, not a
measurement.)*

## 5. Verdict for CD-35 2722 B

With the pipeline validated, the CD-35 2722 B null can be read:

| | value |
|---|---|
| Per-epoch precision achieved | ~800–1850 m/s |
| Paper's precision | 31.44 m/s |
| Signal to be detected | 246 m/s |
| Reduced χ² about a constant | **0.58** (no significant variation) |

The signal is **7.5× below** the noise floor of this extraction. Non-detection is the
arithmetically required outcome, and carries no information about whether the satellite is
real.

**The published detection is neither confirmed nor contradicted.** Stating otherwise in
either direction would be unsupported.

What *is* established:

- ESO's public products can drive viper, via a verified-lossless converter (M2 §2).
- The pipeline measures real radial velocities — demonstrated against a known signal.
- Its precision in this configuration is ~1850 m/s, measured from within-night repeats
  rather than from formal errors.
- Closing the 25–60× gap is the whole remaining problem, and M2 §5 records which levers are
  already eliminated (co-added template, telluric forward modelling) and which are untried.

## 6. Caveats

- **The control's period is not independently recovered**, only confirmed at the known value.
  A six-night baseline cannot do better.
- **The luminosity ratio in §4 is inferred from the very measurement it explains.** It is
  self-consistent, not independent.
- **Several orders failed to converge** in the GJ 229 B runs
  (`Optimal parameters not found: maxfev`), so the control uses fewer orders than the
  CD-35 2722 B run.
- **The control does not validate precision, only correctness.** It shows the pipeline
  measures velocities; it says nothing about whether the remaining 25–60× is reachable.
