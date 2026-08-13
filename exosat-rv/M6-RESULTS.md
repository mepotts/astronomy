# M6 — Reproducing the conclusion from the paper's own RVs

**This milestone exists because M2–M3 answered the wrong question.**

M2 tried to re-derive radial velocities from the archive spectra, fell 25–60× short of the
precision required, and M3 reported "the detection is neither confirmed nor contradicted."
That was true of the *extraction*. It said nothing about the *conclusion* — and the
conclusion is separately testable, because **the preprint publishes its full RV table**
(Table 2, appendix A, "A Full RV dataset").

Reproducing an analysis has two independent halves: getting the same measurements, and
drawing the same inference from them. Failing the first does not bear on the second.
Conflating them is how a reproduction attempt reports the wrong verdict, and this one did
for an entire milestone.

**Result: the conclusion reproduces.** Run with `exosat-rv orbits`.

---

## 1. The data

20 RVs, extracted from the arXiv PDF with `pypdf`, stored with provenance at
[`data/published/hoy2026_table2_rvs.csv`](data/published/hoy2026_table2_rvs.csv).

The extraction verifies itself: 20 rows, baseline 464.9 d, and the mean of the error column
is **31.45 m/s** against the **31.44 m/s** the paper states in its Methods for its favoured
per-nodding extraction. That is not a number I fed in — it falls out of the digitised table,
so the table is complete and correctly parsed.

## 2. The signal is there, independently

Generalised Lomb–Scargle on the published RVs, with astropy's analytic false-alarm levels:

| | |
|---|---|
| Highest peak | **164.15 d**, power 0.831 |
| 0.1% FAP level | 0.818 |
| Power at the published 169.45 d | 0.805 (above the 1% level, 0.756) |
| Second peak | **112.50 d** |

**The primary signal is recovered above the 0.1% false-alarm threshold.** The paper's Fig. 1
labels its raw-RV peaks at 87.1, 113.0, 166.4 and 333.3 d; my independent 112.50 d matches
their 113.0, and 164.15 matches their 166.4 within the grid resolution.

## 3. The model comparison reproduces

Maximum-likelihood fits with the period(s) **held fixed** and a jitter term free, 400
optimiser restarts each. Fixing the periods is essential: let them float and every candidate
slides into the same basin, destroying the comparison the paper actually made.

| Model (periods fixed) | −ln L | BIC | Δlog Z proxy | K₂ | jitter |
|---|---:|---:|---:|---:|---:|
| 1 satellite, eccentric @169.45 | 104.61 | 227.19 | — | — | 35.8 |
| 2 satellites, +14 d | 114.10 | 246.17 | −9.49 | 28 | 65.8 |
| 2 satellites, +70 d | 104.71 | 227.40 | −0.11 | 89 | 34.6 |
| **2 satellites, +88 d** | **102.06** | **222.10** | **+2.55** | **114** | 28.1 |
| 2 satellites, +115 d | 103.92 | 225.81 | +0.69 | 196 | 33.6 |

Against the published values:

| Quantity | This work | Hoy et al. | |
|---|---|---|---|
| Preferred second period | **88 d** | 87.46 d | ✅ |
| K₂ | **114 m/s** | 113.92 m/s | ✅ 0.1% |
| 88 d over 115 d | Δ = **1.85** | Δlog Z = 2.6 | ✅ same sign, ~70% |
| 2 satellites over eccentric 1 | Δ = **2.55** | Δlog Z = 6.9 | ⚠️ same sign, weaker |
| Eccentric 1-satellite e | 0.35 | 0.29 | ✅ same signature |

**The paper's period choice, its secondary amplitude, and the direction of both model
comparisons all reproduce.** With the periods left free, the two-satellite fit converges to
**86.97 d / 115 m/s from every starting point tried** (87, 115 and 70 d), which is a stronger
statement than the fixed-period table: 115 d is not even a surviving local optimum.

## 4. Where the numbers differ, and why

My evidence differences are systematically smaller than theirs — 1.85 vs 2.6, and 2.55 vs
6.9. Three reasons, none of which change a sign:

1. **BIC/2 is a proxy, not a log evidence.** The paper used nested sampling (`EMPEROR`,
   parallel-tempered MCMC). ΔBIC/2 approximates Δlog Z but penalises parameters differently
   and ignores prior volume.
2. **My two-satellite models are circular.** The paper fits eccentricity for both
   satellites; the published values are 0.005 and 0.01, so this should be minor, but it costs
   my fits some flexibility.
3. **Maximum likelihood, not marginalisation.** A single best fit is not an integral over the
   posterior, and the difference grows with model complexity — exactly where my 2-vs-1
   comparison falls furthest short.

The 2-satellite-versus-1-satellite gap (2.55 vs 6.9) is the largest discrepancy and the one
I would want a proper nested-sampling run to settle before quoting either number as *the*
evidence. The 88-vs-115 comparison, where my 1.85 sits close to their 2.6, is the more
robust of the two.

## 5. Consistency with M4

M4 predicted, from the cadence alone and with no RVs, that peak *position* could not separate
88 d from 115 d (a true 115-day signal recovers as ~87 d 92% of the time) but that
*detectability* could (6% vs 74% clearing the 1% FAP).

M6 bears that out on the real data: the two periods are separated not by where a peak sits
but by how much better one model fits — 88 d wins by Δ = 1.85 in the likelihood comparison,
while the periodogram peak positions are barely distinguishable. **The two milestones were
built independently and agree.**

## 6. Verdict

**The Hoy et al. conclusion reproduces from their published radial velocities**, using a
different fitter and an independent implementation:

- the ~169-day signal is significant above the 0.1% false-alarm level;
- a second satellite at ~88 days is preferred over 14, 70 and 115 days;
- the secondary amplitude agrees to 0.1%;
- the two-satellite model is favoured over the eccentric single-satellite alternative.

**What is *not* reproduced remains M2's problem: the radial velocities themselves.** Those
still cannot be re-derived from the public archive at the required precision, so this
reproduction inherits their RVs and tests only what was done with them. That is a real
limitation and it is the honest boundary of this result — but it is a much narrower one than
M3 claimed.

## 7. What this changes about M2 and M3

M3's verdict — "neither confirmed nor contradicted" — was correct about the extraction and
**wrong as a statement about the paper's conclusion**, which was never tested there. Both
documents now carry a pointer here. The mistake is indexed in [`HANDOFF.md`](HANDOFF.md) §1.

The lesson generalises past this project: **before concluding that a result cannot be
reproduced, check whether the authors published the intermediate data.** A great many papers
do, in an appendix nobody reads.
