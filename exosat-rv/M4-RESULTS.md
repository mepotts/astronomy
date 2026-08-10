# M4 — The alias test

**Question:** the preprint says the second signal's period is undetermined — 14, 70, 88 and
115 d are "aliases of each other" — and prefers 88 d by only Δlog Z = 2.6. Is that preference
a property of the data, or of the sampling?

**Answer: both, in different respects.** Peak *position* cannot separate 88 d from 115 d — a
true 115-day signal is recovered as ~87 d **92%** of the time. But peak *significance* can:
a 115-day signal at the fitted amplitude clears the 1% FAP only **6%** of the time, against
**74%** for 87.46 d. The paper's choice is better supported than the periodogram alone
suggests, and for a reason the paper does not state.

Run with `exosat-rv alias`; machine-readable form in [`data/m4-aliases.json`](data/m4-aliases.json).

**This milestone needs no radial velocities** — only the times the target was observed. That
is why it could run before M2.

---

## 1. The cadence

20 public H-band epochs, 2023-10-13 → 2025-01-21, baseline **466 d**, in two seasons of
exactly 10 nights each. Mean-to-mean season separation **338.4 d = 0.926 yr** — the paper's
"almost exactly a year apart".

The resulting GLS peak width is 1/T = 0.00215 d⁻¹, while |1/88 − 1/115| = 0.00267 d⁻¹.
**The two candidate periods are 1.2 peak widths apart.** They are barely resolved, and every
result below follows from that one number.

## 2. All four candidates are yearly aliases of the *primary*

The paper describes 14/70/88/115 d as aliases of one another. They are more specifically
aliases of the **169.45 d primary signal**, on a one-year comb `f = f_primary + m/365.25`:

| Candidate | Order m | Comb tooth off by | Implied sampling period |
|---:|---:|---:|---:|
| 115.0 d | +1 | 0.750 d | 357.9 d |
| 88.0 d | +2 | **0.105 d** | 366.2 d |
| 70.0 d | +3 | 0.847 d | 357.8 d |
| 14.0 d | +24 | **0.035 d** | 366.3 d |

Every implied sampling period lands within 8 days of a year. The fitted 87.46 d — not just
the 88 d periodogram peak — also sits on the m = +2 tooth, within its own quoted uncertainty.

**Why "aliases of the primary" matters.** The candidates were found in the residuals *after*
subtracting the 169-day model. If that model is imperfect in period, amplitude or
eccentricity, the leftover power sits at 169 d, and the yearly window scatters it onto
exactly this comb. The alias family is therefore not merely a nuisance in locating a real
second signal — it is also the shape that imperfect subtraction of the *first* signal would
produce. §3 tests whether that actually happens.

## 3. Injection-recovery

Inject a primary at 169.45 d / 246.45 m/s, optionally a secondary at the fitted 113.92 m/s,
sample at the real cadence, add Gaussian noise at 35.5 m/s (the 31.44 m/s measurement error
and 16.39 m/s fitted jitter in quadrature), remove a fixed-period sinusoid at 169.45 d, and
take the GLS of the residuals. 500 trials each; the "favourite" is the candidate with the
most power within half a peak width.

| Injected | Recovered as favourite | Peak clears 1% FAP |
|---|---|---:|
| **nothing** (primary only) | 14 d 44.0%, 70 d 27.4%, 87.46 d 19.8%, 115 d 8.8% | **1.8%** |
| **87.46 d** | **87.46 d 96.8%**, 70 d 3.0% | **74.2%** |
| **115 d** | **87.46 d 91.8%**, 115 d 4.6%, 14 d 3.0% | **6.4%** |
| **70 d** | 70 d 100.0% | 98.2% |
| **14 d** | 14 d 100.0% | 99.8% |

Four things follow.

**The residual-leakage worry does not survive.** With no second satellite injected, a
"favourite" is always nameable — the test forces a choice — but the peak is significant in
only 1.8% of trials, consistent with the nominal 1% false-alarm rate. Imperfect subtraction
of the primary does **not** manufacture a significant second signal at this noise level. The
paper's detection of *some* second signal is not a sampling artefact.

**Peak position cannot separate 88 d from 115 d.** A genuine 115-day signal is recovered as
~87 d in 91.8% of trials and as itself in 4.6%. Any argument for 88 d that rests on where the
periodogram peaks is therefore close to uninformative, and this is the quantitative form of
the caveat the paper states in words.

**Peak significance can, and it favours the paper.** A 115-day signal at the same amplitude
clears the 1% FAP in only 6.4% of trials, against 74.2% for 87.46 d. The 466-day baseline
splits into two ~150-day seasons, so a 115-day period completes barely one cycle per season
and is far more degenerate with the season structure and the removed primary. **The paper
observed a significant peak; that observation is itself evidence for the shorter period**,
independent of where the peak sat. Δlog Z = 2.6 understates the case.

**70 d and 14 d are cleanly excluded**, recovered as themselves 100% of the time and
significant in ~99%. The paper's rejection of them is well founded.

## 4. What this does and does not say

It does **not** overturn anything. The two-satellite model's evidence over the eccentric
one-satellite alternative (Δlog Z = 6.9) is untouched by this analysis, which assumes a
second signal exists and asks only which period it has.

It does say that the 88-vs-115 discrimination rests on detectability rather than on peak
position, which is a stronger and different argument than the one in the paper. And it
sharpens what new data would settle it: the paper suggests observing away from the ~1-year
spacing, and §2 gives the reason in one number — the comb tooth spacing is 1/365.25 d⁻¹, so
any cadence whose season separation is not near a year collapses the family.

## 5. Caveats

- **The injected secondary amplitude is the one fitted at 87.46 d** (113.92 m/s). A real
  115-day signal need not have that amplitude; a larger one would be more detectable and the
  6.4% would rise. The comparison is controlled, not exhaustive.
- **Sinusoid, not Keplerian, subtraction** of the primary. Deliberate — it models an
  imperfect model — but it is not the paper's procedure, which fitted a full Keplerian
  jointly.
- **Gaussian white noise.** Real CRIRES+ residuals may be correlated, which would raise the
  false-alarm rate above the 1.8% measured here.
- **No real RVs.** Every number above comes from synthetic signals on the real cadence.
  Repeating this on measured RVs is an M3 task.
