# M9 — Order screening: a hypothesis, falsified, and a trap the control caught

**Question:** Hoy et al. state that spectral orders without enough telluric lines produce
"highly erratic results" and must be excluded. M2 applied no such screen and its per-order
RV scatter ranges from 1082 to 4130 m/s. Does order screening explain a meaningful part of
the 25–60× precision shortfall?

**Answer: no. It is worth 6%.** The best screen that survives the positive control takes
the combined scatter from **823 m/s to 776 m/s**, against the 31.44 m/s needed. And the
screen that *looked* best — a 1.6× improvement on the science target — turned out to work by
deleting the signal.

Run with `exosat-rv orders`; machine-readable form in [`data/m9-orders.json`](data/m9-orders.json).

---

## 1. Why this was worth testing, and why it was the wrong lever

HANDOFF named the individual nodding frames as "the only remaining difference the authors
themselves name", making them the default next step. But the authors *quantify* that
difference in their own Fig. 4: **31.44 m/s vs 34.49 m/s, a ~10% gain.** A 10% lever cannot
close a factor of 25, and building `cr2res` to chase it would have been days of work aimed
at the wrong target.

Order screening looked more promising because the paper describes a mechanism with the right
words attached — "highly erratic" — and M2's per-order table showed exactly that spread.
It was cheap to test on data already in hand. It was also wrong.

## 2. Both prior milestones reproduce exactly

Before testing anything, the reanalysis had to recover what M2 and M3 published from the
same files. It does, to the digit:

| | This analysis | Published |
|---|---:|---:|
| CD-35 2722 B combined rms (M2) | **823.1 m/s** | 823 m/s |
| GJ 229 B control Δχ² (M3) | **63.8** | 63.8 |
| GJ 229 B recovered K (M3) | **6165 m/s** | 6165 m/s |

One subtlety cost an hour and is worth recording: an order counts only if **both** its RV
and its error are finite and the error positive — which is what viper itself does. Masking
on the RV alone admits orders viper discarded and shifts the plain mean from 823 to 878 m/s.
It looks like a rounding difference and is actually a silent failure to reproduce.

## 3. The per-order picture

| Order | λ (nm) | rms (m/s) | formal err | ratio | fit rms | telluric S/N |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 1567.1 | 1768 | 534 | 3.3 | 5.45 | 0.31 |
| **8** | **1577.7** | **4130** | **101** | **40.8** | **30.39** | **0.01** |
| 9 | 1600.5 | 2485 | 357 | 7.0 | 7.90 | 0.01 |
| 10 | 1611.9 | 1785 | 430 | 4.2 | 7.26 | 0.02 |
| 11 | 1622.8 | 3954 | 1221 | 3.2 | 4.69 | 0.77 |
| 12 | 1647.5 | 1396 | 444 | 3.1 | 6.01 | 1.48 |
| 13 | 1659.3 | 2113 | 456 | 4.6 | 4.16 | 0.13 |
| 14 | 1670.5 | 2152 | 484 | 4.5 | 4.94 | 1.84 |
| 15 | 1697.4 | 2327 | 446 | 5.2 | 4.64 | 4.01 |
| 16 | 1709.5 | 1082 | 264 | 4.1 | 4.15 | 4.61 |

*(telluric S/N = |atm0| / e_atm0, how well viper constrains the telluric abundance.)*

**Order 8 is pathological on every independent diagnostic**: 6× the fit rms of any other
order, 5× the telluric-abundance error — and the **smallest formal error in the table**.

**The correlation I expected is not there.** Spearman rank correlation of per-order rms
against fit rms and against telluric-abundance error is ρ = +0.38, p = 0.28 (n = 10) for
both. Not significant. Order 8 is an outlier, not the end of a trend.

## 4. viper's formal errors are not merely useless — they are actively harmful

M2 established that formal errors disagree with actual scatter by 2–42×. M9 measures what
acting on them costs:

| Weighting | Combined rms |
|---|---:|
| plain mean | 823 m/s |
| **inverse formal variance** | **2620 m/s** |

Weighting by formal error makes the result **3× worse**, because order 8 has the largest
scatter (4130 m/s) and the smallest formal error (101 m/s), so it receives ~20× the weight
of a well-behaved order. Anyone reaching for `np.average(rv, weights=1/err**2)` on this data
will make it worse and have no way to notice.

## 5. Every screen, scored on the target *and* the control

| Screen | CD-35 rms | GJ 229 B Δχ² | control K | Verdict |
|---|---:|---:|---:|---|
| all orders, equal (viper as-run) | 823 | 63.8 | 6165 | baseline |
| all orders, inverse formal variance | 2620 | 20.5 | 5422 | **fails control** |
| **drop order 8, equal** | **776** | **76.5** | **5948** | **accepted** |
| drop order 8, empirical weights | **514** | **5.8** | **1825** | **fails control** |
| telluric-constrained orders only | 1142 | 46.7 | 3620 | rejected |

### The trap

**Empirical weighting — weight each order by 1/rms² measured from the data — gives the best
number in the table on the science target: 514 m/s, a 1.6× improvement on viper's own
output.** It also collapses the control: Δχ² from 63.8 to 5.8, and the recovered amplitude
from 6165 to 1825 m/s, on a binary whose existence is not in dispute.

The reason is circularity. **For a target with a real signal, an order's scatter *is* the
signal.** Weighting by inverse scatter systematically downweights exactly the orders carrying
it. On CD-35 2722 B, where no signal is detected, that pathology is completely invisible —
it looks like clean noise suppression.

This is the strongest vindication the project has produced of HANDOFF's rule that **no
result from this pipeline may be reported without re-running the control.** The screen that
looked best on the science target was the one that worked by deleting the answer. Without
GJ 229 B it would have been adopted, and it would have made every future null deeper and
more wrong.

### The paper's own rule does not transfer

Keeping only orders where viper constrains the telluric abundance (12, 14, 15, 16) is the
paper's stated prescription. It makes the target **worse** (1142 m/s) and weakens the
control (63.8 → 46.7, K suppressed to 3620). Either our per-order `atm0` errors do not mean
what they appear to, or the rule cannot be applied to ESO's *combined* product. Recorded as
measured, not resolved.

## 6. The result, and why it closes the whole approach

    median per-order rms  = 2133 m/s over 10 orders
    naive sqrt(10) floor  =  674 m/s
    viper's actual output =  823 m/s
    best validated screen =  776 m/s
    target                = 31.44 m/s

**The combination is already working as expected.** 823 m/s sits within 20% of the √N floor
implied by the per-order scatter, so the orders are behaving as roughly independent
measurements and averaging them is doing its job.

**The entire shortfall is in per-order precision**, which is ~100× above the photon limit
(order 1 m/s at R = 100,000, S/N ≈ 18, ~40,000 pixels). That is a systematic present in
every order, and **no weighting, screening or recombination scheme can remove it.**

So this route is closed, and closing it is the milestone's value: two of the three cheap
levers on the table are now measured rather than assumed —

| Lever | Believed worth | Measured |
|---|---|---|
| individual nodding frames | "the only remaining difference" | **10%** (authors' own Fig. 4) |
| order screening / reweighting | plausibly large | **6%** |

## 7. What is actually left

The gap is in the **per-order forward model**. Three candidates, in the order I would attack
them:

1. **The template.** M3 already proved this is decisive rather than marginal — the same
   control returns reduced χ² = 0.53 (nothing) with a mismatched template and 5.36 with a
   matched one. The CD-35 2722 B template is built from its own data at S/N ≈ 18; the paper
   used **two iterations** of a co-added template over all 20 epochs (S/N ≈ 80). M2 tried
   `-createtpl` and reported "changed nothing" — but it made things *worse* (823 → 1638 m/s),
   which is not "nothing" and is the signature of a template co-added without correct RV
   alignment. **Re-examine how the co-added template is built before trying anything else.**
2. **The wavelength solution.** Köhler et al. 2025 attribute up to 1 km/s of drift to
   improper wavelength correction, and 823–2133 m/s is squarely in that range. The telluric
   abundance is unconstrained (|atm0|/e_atm0 < 1) in **6 of 10 orders**, which is what a
   failing wavelength anchor looks like. This is consistent with §5's finding that the
   *paper's* telluric screen does not transfer — the diagnostic may be broken rather than
   the orders.
3. **The nodding frames**, last, and with the expectation correctly set at 10%.

Note that (1) and (2) are both *within* one order and neither is addressable by combination
— which is exactly what §6 predicts.

## 8. Caveats

- The per-order diagnostics come from a single viper run (`full1`). The three other stored
  runs use different templates and are not directly comparable.
- The telluric S/N proxy (|atm0|/e_atm0) is a reading of viper's covariance output, not an
  independent measurement of telluric line content. A real telluric line-density measurement
  from an atmospheric model would test §5's negative result properly.
- Dropping order 8 is adopted on evidence but rests on n = 18 epochs; it is a 6% effect and
  should not be over-interpreted.
- The control has six nights and cannot recover the 12.1-day period blind (M3 §6). It tests
  whether a screen preserves a *known* signal, which is what is needed here, and nothing more.
