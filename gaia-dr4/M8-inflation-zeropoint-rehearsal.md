# M8 — the inflation factor measured at scale, the zero-point closed, and the pre-registration executed

*2026-08-24. Runs M7's own three recommendations, in M7's own priority order. M7 left a
refit arm validated on three objects, a dominant systematic that had been named but not
bounded, and a pre-registration nobody had run. Repo law: sourced-or-UNSOURCED; negative
results are results; rules pre-registered. Anonymous HTTP only. No accounts, no
submissions, no commits, no pushes.*

---

## 0. The one-paragraph answer

**M7's two caveats were one real measurement and one convention mismatch, and the
mismatch was the bigger of the two.** The parallax half is closed: Panuzzo's own Letter
applies a **35.4 µas** Lindegren+2021 correction to Gaia BH3's catalogue parallax, this
milestone's independent implementation computes **35.406 µas** for the same source, and
the paper's *orbital* parallaxes — the ones M7 compared against — are explicitly **not**
corrected. So on the one object where both sides can be checked, **both were uncorrected
and the zero-point cancels: M7's −14.9 µas on BH3 is not the zero-point at all.** The
zero-point is real, it is larger than M7 thought, and it had been left in.
Applying the correction inside the arm moves Gaia BH3's companion mass
from **34.68 to 32.64 M☉** against Panuzzo's published **32.70 ± 0.82**: the **+2.42 σ
offset becomes −0.07 σ**, and the corrected refit parallax lands on Panuzzo's
zero-point-**free** a₀/a₁ parallax to **+1.9 µas (+0.11 σ)** where the raw one sat
1.90 σ away. The residual is bounded at **≤ 2 µas**, which costs ≤ 0.4 % of a companion
mass at BH3's distance. The error-inflation half is measured on real samples for the first
time: against **SB9** — ground-based spectroscopy that shares no photons with Gaia —
**202 elements from 138 systems** give an inflation factor of **1.40 [1.31, 1.52]** with
**52 % inside 1 σ** against the expected 68 %, rising monotonically with NSS
`significance` from **0.88** to **1.83**; and an **injection–recovery experiment through
the arm's own fitter** (400 injections, 1,407 elements) returns **1.05 [1.03, 1.09]** when
the noise model is right and **1.51 [1.47, 1.56]** with one unit of unmodelled jitter —
which settles what M7 could not say: **the Laplace error bar is not broken, the inflation
is model misspecification**. And the pre-registration has now been *run*: eleven synthetic
verdict stores at December's projected sample sizes, every pre-registered command, every
outcome label — which found **a D4 command that does not parse**, **a December-scale crash
in `m5_activity_discriminator.py`**, and **four places where the frozen registration's own
rules do not determine a label**.

**The literal M8 ask — "run the refit arm at queue scale on DR3 NSS" — cannot be done by
anyone, and saying so is the first result.** Gaia DR3 publishes no stellar epoch
astrometry; DR4 is the first release that will, and it is DataLink-only. The arm's
Keplerian half has exactly twelve sources of input in the world today. §1 sets out what
was run instead and what each route does and does not bound.

---

## 1. Task 1 — the error-inflation factor, at scale

### 1a. What could not be run, stated first

M7 recommendation 1 asked for the arm at queue scale on DR3 NSS. The arm's first half
consumes **epoch astrometry**. DR3 publishes none for stars (M1 landmine #1: DR4
`epoch_astrometry` is DataLink-only, and the only file in existence is the 12-source
pre-release of 2026-06-26). So the Keplerian half cannot be run over hundreds of DR3
sources — not here, not anywhere — before 2026-12-02.

What *can* be run at scale, and what December will actually quote:

| route | what it measures | reference | n |
|---|---|---|---|
| **S1** DR3 NSS vs **SB9** | the **catalogue's** formal errors | ground-based spectroscopy, independent photons | **202 elements / 138 systems** |
| **S2** the 98 dual-solution sources | a **lower bound** (shared photons) | the same star's other NSS solution | 784 elements |
| **S3** injection–recovery **through the arm** | the **arm's own Laplace σ** | the injected truth | 1,407 / 1,288 elements |
| **S4** the M7 anchor | the arm vs published | three papers | 11 elements |

`scripts/m8_error_inflation.py` → `out/m8_error_inflation.txt`, plus
`out/m8_inflation_{sb9,duals,injection_clean,injection_jitter1x}.csv`.

**Rules pre-registered in the script's docstring before any z-distribution was looked at**:
SB9 crossmatch radius 2.0″ (1/3/5/10″ reported as a sensitivity strip); one orbit per SB9
system, best `Grade`, ties to the larger number of RVs; a **same-orbit gate**
|ln(P_Gaia/P_SB9)| < 0.05 with the failures counted; both sides must publish a finite
positive uncertainty; the factor is **median|z| / 0.67449** with a 5,000-resample
bootstrap; coverage reported against 68.27 % and 95.45 %.

> **A convention correction to M7 first.** M7's "**median factor 2.3**" is the median
> |Δ| / σ, not an inflation factor. A standard normal has median |z| = 0.674, so the
> multiplier that would make M7's own eleven elements self-consistent is
> **2.28 / 0.674 = 3.4**, not 2.3. Every number below is on the **median|z| / 0.674**
> convention and the raw median |z| is printed beside it, so the two can be compared.

### 1b. S1 — against SB9, the only reference that shares no photons with Gaia

Pourbaix et al. 2004, A&A 424, 727 — the Ninth Catalogue of Spectroscopic Binary Orbits,
CDS `B/sb9`, pulled live through VizieR and cached to `data/sb9/`. At the pre-registered
2″ radius: **169 matched systems**, of which **138 pass the same-orbit gate** and 31 do
not. (Of those 31, two sit within 10 % of a factor-2 period alias — a small number, and
worth saying because the alias failure mode is the one this project's `flag_alias_1yr`
exists for.)

| | n | median \|z\| | **inflation** | \|z\| < 1 | \|z\| < 2 |
|---|---|---|---|---|---|
| **all elements pooled** | 202 | 0.95 | **1.40 [1.31, 1.52]** | **52.0 %** | 84.7 % |
| period | 105 | 0.95 | 1.40 [1.29, 1.54] | 50.5 % | 82.9 % |
| eccentricity | 97 | 0.94 | 1.39 [1.22, 1.54] | 53.6 % | 86.6 % |
| *(expected under correct errors)* | | *0.674* | *1.00* | *68.3 %* | *95.5 %* |

**The coverage test is the headline of this section**: 52 % of elements fall within 1 σ
where 68 % should, and 85 % within 2 σ where 95 % should. Gaia DR3 NSS formal errors are
optimistic, by about 40 %, measured against an independent technique.

**Trends — and one of them matters for the candidate list.**

| by | inflation |
|---|---|
| **NSS `significance`** 9.7–35.8 / 35.8–65.5 / 65.5–113.9 / 113.9–520.7 | **0.88 → 1.33 → 1.37 → 1.83** |
| period (d) 15–298 / 298–544 / 544–692 / 692–1080 | 1.74 → 1.43 → 1.43 → 1.01 |
| G 4.2–7.3 / 7.3–8.4 / 8.4–9.2 / 9.2–12.6 | 1.54 / 1.14 / 1.38 / 1.55 — no monotone trend |
| solution type: `Orbital` 1.37, `AstroSpectroSB1` 1.42, `OrbitalTargetedSearch` 1.72, `…Validated` 1.49 | consistent within errors |

> **The most significant solutions have the worst-calibrated errors.** That is the
> opposite of the intuition, it is monotone across four bins, and it is the axis this
> project selects on (`significance > 10`, frozen since M2). It is the sort of thing that
> only shows up when the reference is genuinely external.

**The SB9 sample is not the day-one queue, and must not be quoted as if it were.** SB9's
stars are bright spectroscopic binaries — median **G 8.4** against the queue's **15.0** —
and their Gaia solutions are more significant (median **65.5** vs **33.9**). Reweighting
the per-bin median |z| by the *queue's own* `significance` distribution gives
**inflation 1.19** against the raw 1.40. Both are reported;
**1.2–1.4 is the honest range for the catalogue's elements on the day-one population.**

### 1c. S2 — internal replication, and why it is a floor and not an answer

The 98 DR3 sources carrying two astrometric solutions (M2 landmine #4) are
`AstroSpectroSB1` + `OrbitalTargetedSearch[Validated]`: two NSS pipelines, one star.
Pooled over eight shared elements, **784 comparisons give inflation 0.89 [0.85, 0.94]**,
with `nss_parallax` at 0.71 and `t_periastron` at 0.58.

That is *below* one, and the reason is structural: the two solutions are fitted to the
same astrometry, so their errors are strongly correlated and the difference is smaller
than two independent draws would be. **This route can only ever produce a lower bound**,
it is reported as one, and its real value is negative evidence — the catalogue's errors
are not wrong by a factor of several *internally*, so the factor 1.4 that SB9 sees is
about the difference between Gaia and the world, not about arithmetic inside the pipeline.

### 1d. S3 — injection–recovery through the arm, which is the route that settles it

The arm's own chain — `single_star_model` → periodogram → `keplerian_fit` →
`get_param_error` — run on **real pre-release scan geometry** (times, scan angles,
parallax factors, per-CCD σ from the twelve pre-release sources) with a **real DR3 NSS
orbit injected** and Gaussian noise at the real per-CCD σ. 400 injections, seeded, drawn
from the day-one queue's own orbits; 355 recovered (45 `NO_PEAK`, 0 errors); 125 s.

| variant | n | median \|z\| | **inflation** | \|z\| < 1 | \|z\| < 2 |
|---|---|---|---|---|---|
| **noise model correct** | 1,407 | 0.71 | **1.05 [1.03, 1.09]** | 65.7 % | 92.6 % |
| **one unit of unmodelled jitter** | 1,288 | 1.02 | **1.51 [1.47, 1.56]** | 49.0 % | 80.1 % |

Per element in the clean run: P 1.00, a₀ 0.98, ϖ 1.05, e 1.16.

**One caveat on this route, stated because the summary statistic hides it.** The maximum
|z| in the clean run is 3.6×10⁶ — a few fits land on a wrong periodogram peak and report
an absurdly small formal error for it. The **median**-based factor is immune to those by
construction (which is why it is the statistic used), but they are real and they are
countable: **15 of 1,420 elements exceed |z| = 10, spread over 15 distinct recovered
orbits of 355 — about 4 %, and there is nothing between |z| = 10 and |z| = 100**, so it is
a discrete failure mode rather than a tail. **Roughly one recovered orbit in twenty-five
is catastrophically wrong with a confident error bar.** That
is a different failure from the inflation factor and no multiplier fixes it — the defence
is the FAP gate (which already rejected 45 of 400) and the per-source comparison against
the catalogue orbit that the runbook's §3.4 branch prescribes.

> **This is the discriminator M7 could not run.** The Laplace/Hessian error bar is
> **correct to 5 %** when the model is correctly specified. So M7's factor is **not** a
> broken Hessian, a bad covariance or a Laplace approximation failing — it is **model
> misspecification**, and one unit of astrometric jitter that the fitter is not told about
> reproduces the SB9 factor almost exactly (1.51 vs 1.40). The inflation factor is a
> property of the **data**, not of the code, and it scales with how much of the real noise
> the model is missing.

### 1e. S4 — the M7 anchor, recomputed, and why it is the largest of the four

The same eleven elements: median |z| **2.28**, inflation **3.38 [1.04, 4.03]**, 4/11
inside 1 σ. It is larger than every scale route and it should be, for reasons that are
visible in M7's own table: HD 114762's refit period is 6.2 σ from **Winn's Doppler**
period and its inclination is 83 σ from Winn's — those are disagreements between an
astrometric photocentre orbit and a spectroscopic orbit, not error bars being 3.4× too
small. n = 11 across three objects with three different reference techniques cannot
separate the two.

### 1f. What December quotes

> **Recommended, and now in the runbook: quote a formal Laplace interval, and beside it an
> inflation factor of ×1.4, sourced to 202 SB9 comparisons — with the caveats that the
> queue-reweighted value is ×1.2, that the factor rises to ×1.8 for the highest-
> `significance` solutions, and that the arm's own statistical error bar is correct to 5 %
> so anything above 1.0 is a statement about unmodelled noise.** Never quote a Laplace
> posterior as a total uncertainty, and never quote M7's 2.3 as an inflation factor — it
> is a median |z|.

**One limit named, because §1's four routes do not cover it.** SB9 gives **P** and **e**.
The companion mass goes as **a₀³**, and no external reference for **a₀** is used anywhere
above — the injection–recovery run recovers a₀ to 0.98 of its own σ, but that is the arm
against itself. **An inflation factor measured on P and e does not license one on a₀**,
and the honest statement is that a₀'s external calibration is still open. It is M9's
third recommendation.

### 1g. And the arm's *second* half did run at queue scale

The half of the arm that cannot run is the Keplerian fit. The half that produces the
number December quotes — Campbell elements + parallax → astrometric mass function →
companion mass — **was run over the whole 981-row day-one queue**, twice (with and
without the zero-point), in §2e. That run is what the ϖ⁻³ distribution in §2e is measured
on: 979 rows with an a₀ and a positive NSS parallax, 823 with an M₁ rung from the triage's
own ladder. It is reported there rather than here because its interesting output is the
zero-point's effect, not the error bar's.

---

## 2. Task 2 — the parallax zero-point, bounded and applied

`scripts/m8_zeropoint.py` (the house pattern), `scripts/m8_zeropoint_effect.py` (the
measurement) → `out/m8_zeropoint_effect.txt`, `out/m8_zeropoint_{trio,queue}.csv`,
`out/m8_zeropoint_summary.json`.

### 2a. The house pattern, reused rather than reinvented

The sibling **seti-ellipsoid-broker** project in this portfolio already applies
Lindegren+2021 correctly, and its pattern is reproduced here in intent and in the four
details it pays for: `corrected = parallax − Z`; applied **before** anything inverts or
cubes the parallax; `astrometric_params_solved ∈ {31, 95}` masked **before** the call
(`zpt.get_zpt` raises otherwise); arrays not scalars (numpy ≥ 2 forbids the package's
scalar `np.can_cast` path); and out-of-box sources fall back to the uncorrected parallax
**and are counted**. `gaiadr3-zeropoint` 0.1.0, installed into `gaia-dr4/.venv`. The
module's own `--selftest` reproduces the sibling project's pinned anchor
(G 18.5, ν_eff 1.6, 6p, ecl −66 → **−0.028661 mas**) exactly.

Inputs pulled for **1,904 sources** (the day-one queue, the class-III list, the 98
dual-solution sources, the trio) — `data/dr3_zeropoint_columns.parquet`, ESAC, 9 s,
1,904/1,904 matched, **1,898 correctable**. The 6 that are not are worth naming, because
each is a different edge of the validity box: **four six-parameter solutions whose
`pseudocolour` (1.159, 1.193, 1.734, 1.762) lies outside 1.24–1.72**, and **two
five-parameter solutions at G ≈ 5.27 and 5.29**, below the G > 6 bound. All six fall back
to the uncorrected parallax and are counted; **two of the six are in the day-one queue**
and neither is in its top ten by M₂_min.
Z over the queue: median **−35.5 µas**, p10 −43.5, p90 −23.7.

### 2b. Validated against two independent users before being used

**(a) Panuzzo et al. 2024 (A&A 686, L2), Table 1 footnote b**, verbatim: *"A zero-point
correction (Lindegren+2021) of **35.4 µas** has been applied to the parallax value given
in the catalogue."*

| | |
|---|---|
| DR3 catalogue parallax, pulled live | 1.644349 mas |
| Z computed here | **−35.406 µas** |
| corrected here | 1.679755 mas |
| **Panuzzo's printed corrected value** | **1.679 ± 0.069 mas** |
| \|Z_here\| − \|Z_Panuzzo\| | **0.006 µas**, against their 0.05 µas printed precision |

**(b) El-Badry et al. 2026** — the same paper this project takes its verdicts from —
publishes the same eight sources fitted **with and without** L21, so the difference of
their two parallax columns is their applied shift. Median |difference| from this
implementation over the eight: **2.0 µas**, against 1 µas of rounding on each of their
columns.

**(c) And EB26 measured the zero-point for astrometric *orbital* solutions directly**,
which is the one thing this task could not otherwise justify: a joint fit of 40
dark-companion binaries gives **Z = −0.0362 ± 0.0053 mas** under the same
ϖ_true = ϖ − Z convention, against the **L21 median −0.0342** for the same 40 sources.
Their conclusion, quoted: *"the single-star zeropoint can and should be applied to binary
solutions as well."*

### 2c. M7's 5–41 µas was a convention mismatch, and the paper says so twice

Panuzzo states the convention in two places, and they are **opposite**:

- **Table 1** (the DR3 single-star parallax): L21 **applied**, footnote b, 35.4 µas.
- **Table 2** (the NSS orbital solutions): **not** applied — *"we do not have enough
  information at this stage to quantify the bias for the preliminary NSS solutions. As a
  consequence, the uncertainty on the mass function reported in Table 2 is
  underestimated."*

**M7 compared its uncorrected refit parallax against the Table-2 value.** Both are
uncorrected, the zero-point cancels in that difference, and M7's −14.9 µas on BH3 is
therefore *not* the zero-point at all. The five BH3 parallaxes on one scale:

| | mas |
|---|---|
| DR3 single-star, catalogue | 1.644349 |
| DR3 single-star + L21 | 1.679755 → **Panuzzo Table 1: 1.679** |
| Panuzzo NSS astrometric, **raw** | 1.6747 ± 0.0094 |
| arm refit (M7), **raw** | 1.659797 ± 0.006523 |
| **arm refit + L21** | **1.695203** |
| **Panuzzo a₀/a₁, zero-point FREE** | **1.6933 ± 0.0164** |

**How much of M7's 5–41 µas does the correction remove?** Asked literally — refit minus
the same published values M7 used — **none of it, and it makes two of the three larger**:
−4.5 / −40.6 / −14.9 µas become **+18.2 / −3.6 / +20.5**. That is the correct answer and
it is the diagnosis: those published parallaxes are **uncorrected**, so correcting one
side of the comparison and not the other cannot help. Asked properly — against a reference
on the *same* convention — the correction removes **essentially all of it**: 33.5 µas of
BH3's offset from the zero-point-free a₀/a₁ parallax becomes **1.9 µas**, and the 2.42 σ
mass offset becomes 0.07 σ.

> **The test that decides it.** Panuzzo also publishes ϖ = a₀/a₁ = 1.6933 ± 0.0164 mas,
> derived from the **spectroscopic** a₁ and therefore carrying no astrometric zero-point
> at all. Against that reference: the **raw** refit parallax is **−33.5 µas = −1.90 σ**;
> the **L21-corrected** refit parallax is **+1.9 µas = +0.11 σ**. The correction moves the
> arm onto an independent, zero-point-free measurement. That is not a fit; it is a
> prediction that could have failed.

### 2d. Gaia BH3's mass, with and without — the 2.4 σ closes

Through the production arm (`orbital_refit_arm.py --trio --zeropoint`, new flag, §2f):

| | ϖ (mas) | f_M (M☉) | **M₂ (M☉)** | 68 % |
|---|---|---|---|---|
| **raw (M7)** | 1.659797 | 33.2128 | **34.6843** | [34.204, 35.169] |
| **L21-corrected** | 1.695203 | 31.1749 | **32.6434** | [32.199, 33.092] |

| against | raw | **L21** |
|---|---|---|
| Panuzzo's headline **M_BH 32.70 ± 0.82** (from a₁, no parallax) | **+2.42 σ** | **−0.07 σ** |
| Panuzzo's a₁-derived, zero-point-free **f_M 31.23 ± 0.81** | +2.45 σ | **−0.07 σ** |
| Panuzzo's Table-2 astrometric **f_M 32.03 ± 0.64** (parallax **not** corrected) | +1.85 σ | −1.34 σ |

**The 2.4 σ closes.** The third row is the control: against a reference computed from an
*uncorrected* parallax, correcting the arm makes the agreement *worse* — exactly as it
must, and the reason the first two rows are the meaningful comparisons.

HD 114762 M₂ 0.23336 → 0.23298 (−0.17 %); Gaia-4 0.010330 → 0.010313 (−0.17 %). Both
nearby, so both barely move: the correction is a **distance-dependent** effect.

### 2e. At scale, and the residual bounded

Applying L21 across the 981-row day-one queue (979 with an a₀, a positive NSS parallax and
a defined correction; 823 with an M₁ rung):

| | median | p10 | p90 | worst |
|---|---|---|---|---|
| relative shift in M₂ | **−1.95 %** | −4.93 % | −0.95 % | **−11.94 %** |
| absolute shift in M₂ | −0.0121 M☉ | −0.0602 | −0.0054 | |

EB26 measured a **median −0.018 M☉** on their own joint fits; this gives −0.0121 M☉ on a
different sample, same sign, same order.

The shift is 3Z/ϖ to first order, so it is a distance effect and December's candidates are
the distant ones:

| ϖ | n | median shift in M₂ |
|---|---|---|
| < 0.5 mas | 51 | **−9.86 %** |
| 0.5–1.0 | 133 | −6.83 % |
| 1.0–2.0 | 214 | −3.31 % |
| 2.0–5.0 | 455 | −1.79 % |
| > 5.0 | 126 | −0.91 % |

**79 of 823 rows move by more than 5 %, 4 by more than 10 %** — and EB26's own forecast
is that this gets worse in DR4 because DR4's binaries will be further away.

> **And the M₁-free number is much bigger, which is the one the headline candidates
> carry.** The mass function itself moves by a median **−4.09 %**, p10 **−12.17 %**,
> **worst −33.66 %** over all 979 rows — three to four times the M₂ shift, because
> M₂ ≈ (F(M₁+M₂)²)^(1/3) compresses a change in F when the companion is not much heavier
> than the primary. **Where the triage's M₁ ladder reaches only the evolved bracket, F is
> all there is to quote** — and that is the case for **six of the ten highest-M₂_min queue
> members**, whose mass functions move by −1.7 %, −6.1 %, **−30.6 %**, −20.9 %, −26.3 %,
> −24.7 %. Reporting "the correction is worth about 2 %" would be true of the median
> companion mass and badly wrong about the candidates anyone will look at first, because
> the December list is ranked by M₂_min and M₂_min is highest exactly where the parallax
> is smallest.

**The residual, bounded three ways**: EB26's measured Z minus the L21 median for the same
40 sources = **−2.0 µas (0.38 σ from zero)**; the scatter of this implementation against
EB26's applied shift on eight published pairs = **2.0 µas**; BH3 against the zero-point-free
a₀/a₁ = **+1.9 µas**. **Bound adopted: ≤ 2 µas**, against the **35 µas the correction
removes at this sample's median** — note that the often-quoted **−17 µas is the DR3
*global* mean**, and this sample is fainter and redder than the all-sky average, so
quoting the global number here would understate what is being removed by a factor two.
That costs **≤ 0.4 % of a companion mass at BH3's 1.66 mas**, 2.0 % at 0.3 mas —
0.13 M☉ on a 34.7 M☉ companion, against Panuzzo's own 0.82 M☉ uncertainty.

> **The zero-point is no longer the dominant systematic on a companion mass. It was
> dominant only while it was being ignored.** After correction the dominant term is the
> error inflation of §1 — ×1.4 — which is a much less comfortable place to be, because
> that one cannot be fixed by a published table.

### 2f. Wired into the arm, opt-in, and December must pass it

`orbital_refit_arm.py --zeropoint` applies Z to the fitted parallax **before** the mass
function *and* to the parallax draws inside the Laplace posterior. **Default off**, so
M7's frozen acceptance and trio table reproduce byte-identically without the flag —
re-verified: the acceptance still passes at P 11.45429, e 0.727816, M₂ 34.68425, and
`out/m7_refit_trio.csv` and `out/verdicts_v2/harness_prerelease_refit.v2.csv` are
unchanged on disk. **The runbook now makes `--zeropoint` mandatory for December** (§3.4).

Two bugs were paid for in the wiring, both worth naming: the first version shifted the
point estimate and **left the posterior percentiles on the raw parallax** — a corrected
mass inside an uncorrected interval; and `build_v2_store` ignored `--out-dir` and wrote
the v2 store **over the frozen one** (caught by hashing before and after; same family as
M7 landmine #14).

---

## 3. Task 3 — the pre-registration, executed

`scripts/m8_synthetic_store.py` (the store), `scripts/m8_prereg_labels.py` (§5 as one
total function), `scripts/m8_prereg_rehearsal.py` (the driver) →
`out/m8_prereg_rehearsal.txt`, `out/m8_prereg_rehearsal_{labels,runs}.csv`,
`out/verdicts_synth/`.

### 3a. The synthetic store, and where it is not

Eleven scenarios over the **981 real day-one queue members** — real `source_id`s, so the
joins to the triage frame, the DR3 activity columns and the eROSITA footprint behave as
they will in December; fabricated ids would make every test read NOT TESTABLE for the
wrong reason. The generative model is **declared before the run** and the **realised**
effect is recorded, so the store's truth is a measured number rather than an intention:

| scenario | mode | n | realised |
|---|---|---|---|
| `null_eb26` / `null_even` / `null_harness` | verdict independent of every metric | 633+347 / 490+490 / 245+735 | — |
| `d1_effect` | in-footprint X-ray rate | 631+346 | **0.1512 vs 0.0000** (target 0.154 vs 0.000) |
| `d2_effect` | AUC on ΔAmp_G | 633+347 | **0.6573** (target 0.659) |
| `d3_effect` | AUC on `astrometric_gof_al` | 633+347 | **0.3440** (target 0.344) |
| `d4_effect` | `flag_astrom_quiet` marking rate | 554+304 | **0.2993 vs 0.0758** (target 0.30 vs 0.075) |
| `d2_reversal` / `d3_reversal` | the same tilt, sign flipped | 633+347 | 0.3421 / 0.6576 |
| `thin` | the NOT TESTABLE arm, too few rows | 5+4 | — |
| `no_coverage` | the OTHER NOT TESTABLE arm — the metric's data does not exist | 380+208 | 588 class-III sources with **no row in the activity pull** |

> **The `no_coverage` scenario was built wrong the first time, and the way it was wrong is
> the point.** It blanked the driver column *inside the store*. The store carries
> `source_id`s and verdicts; M5 reads `astrometric_gof_al` from
> `data/dr3_activity_columns.parquet`, so blanking a column in the store changes nothing
> the test looks at — the scenario would have silently rehearsed the *null* while claiming
> to rehearse zero coverage. **A synthetic control that does not actually change what the
> test reads is worse than no control**, because it produces a green tick. The honest
> construction uses sources for which the metric's data genuinely does not exist: the
> **604 class-III sources outside the 1,199-row activity pull**, which is exactly M5 family
> A's real situation with `activityindex_espcs`. Rebuilt and re-run; §3e.

**Nothing synthetic is ever written into `out/verdicts/`.** The December command is
`--verdicts all`, and `all` means "every CSV in that directory". The stores live in
`out/verdicts_synth/<scenario>/` and the rehearsal passes that directory —
`load_store()` expands a directory through the same branch it expands `all` with, so the
code path under test is identical and no fabricated verdict can join December's real
analysis. That substitution is the **only** deviation from the commands as frozen.

### 3b. Three defects in the CODE, and the first one would have fired on the day

**DEFECT C-1 — the D4 command does not parse.** The frozen registration §6 and runbook
§3.3 both prescribe

```
scripts\m6_astrom_quiet_decision.py --verdicts all --scopes orbit_reality
```

and that script had no `--scopes` argument. It exits 2 with
`unrecognized arguments: --scopes orbit_reality`. **M7's executability note covers the two
discriminator commands only**, and its claim that "the commands as written below run" is
false for the D4 line — one of seven, and the only one nobody had typed. `--scopes` and
`--sources` added, matching the other two consumers; no rule and no default changed.

**DEFECT C-2 — `m5_activity_discriminator.py` crashes at December's sample size**, and it
could not have been found on the 65 EB26 verdicts. The pre-registered confound guard runs
only for a metric that *discriminates*. On 65 rows the only metrics that ever reached it
were `astrometric_gof_al` and `ruwe`, both strictly positive floats. On a 633+347 store a
**binary** metric reaches it — `B4 phot_variable_flag == VARIABLE` did — and `np.clip` on
a boolean Series returns object dtype, so `np.log10` raises

```
TypeError: loop of ufunc does not support argument 0 of type float
           which has no callable log10 method
```

after most of the output has already been printed. The pooled *and* primary December runs
would both have died. Fixed with an explicit `.astype(float)`, a no-op for the float
columns; the five frozen M4/M5 artifacts reproduce byte-identically.

**DEFECT C-3 — `m6_astrom_quiet_decision.py` announced `out/…` no matter where it wrote**,
the third occurrence of M7 landmine #14 (M7 fixed it in `m5_activity_discriminator.py` and
did not check the other consumers). A December run into a scratch directory reported that
it had just overwritten the frozen M6 artifacts when it had not.

Two machine-readable results files were also added — `m4_eb26_discriminator_results.csv`
and `m6_astrom_quiet_d4_results.csv` — because §5 says the label follows "mechanically
from the numbers" and until now those numbers existed only inside prose. **A December
label assigned by regexing a `.txt` at 3 a.m. is not mechanical.** Both are new files; the
five frozen artifacts are untouched and their byte-identity check still means what it
meant.

### 3c. Four gaps in the FROZEN registration — reported, not patched

The registration is frozen and only Matthew may amend it. `m8_prereg_labels.py` implements
§5 as one total function and emits a placeholder plus a defect code wherever the rules do
not determine a label.

| gap | what the registration says | what it does not cover |
|---|---|---|
| **GAP-1** | POSITIVE = significant **and** direction **and** DECISIVE | **significant, right direction, NOT decisive** — POSITIVE fails on decisiveness, NULL and UNDERPOWERED both require "not significant", DIRECTION REVERSAL requires the wrong direction, NOT TESTABLE requires n < 5. *No label applies.* The six are not exhaustive. Emitted as `POSITIVE (not decisive)` |
| **GAP-2** | §5: "exactly one of these six labels" | §2.2 mandates a **seventh** outcome — a pooled non-significant result "must be reported as 'pooled: uninterpretable'" and "must never be quoted as a null". Applying §5 literally to a pooled run forces NULL or UNDERPOWERED, both of which §2.2 forbids. Emitted as `POOLED: UNINTERPRETABLE (diluted)`; §2.2 is followed because it is the more specific rule and the one that prevents the error |
| **GAP-3** | §2.2 permits only the pooled **positive** to be interpreted; §5's DIRECTION REVERSAL carries no scope qualifier | a **pooled significant reversal** is covered by neither. Emitted as `DIRECTION REVERSAL (pooled, not interpretable)` |
| **GAP-4** | §4: DECISIVE iff the smallest detectable effect at 80 % power is at least as small as the effect under test | for the two **rate** tests the effect under test is a *pair* (D1 "0.154 vs 0.000", D4 "0.30 vs 0.075") while `min_detectable_rate(n1, p0, n2)` returns the smallest detectable **spurious** rate against the **observed** baseline. The two are comparable only when the observed baseline equals the pre-registered one. Both readings are computed and GAP-4 is raised where they disagree |

**Proposed amendments, for Matthew, to be appended to the variant log — not applied here.**
(1) add a seventh label, *POSITIVE (not decisive)*, or state that a significant result is
decisive by construction; (2) name *pooled: uninterpretable* in §5's table so §5 and §2.2
agree; (3) say whether a pooled reversal is reportable; (4) say, for rate tests, whether
DECISIVE is evaluated at the pre-registered baseline or at the observed one; and (5) a
one-line interpretation note that **D1 and D2 are correlated axes** (§6.12) so two
positives are one finding, which changes no rule and no p-value.

**None of these is a reason to distrust the pre-registration.** Every one is a hole in the
*label bookkeeping*, not in the parts that stop a null being laundered into a result: the
scope-pure primary, the one-direction pooling rule, the fixed Holm family sizes, the fixed
directions and the negative-control veto all survive the rehearsal intact and all executed
exactly as written. The gaps are what you find when you turn prose into a total function,
and finding them now is what M7's third recommendation was for.

Also implemented here because no consumer implements it: **the negative-control veto**.
If `phot_g_n_obs` reaches p < 0.05, every D1–D4 POSITIVE in that run is relabelled
`… — VETOED by the negative control`. §3's rule now has a code path.

### 3d. The rehearsal, path by path

`out/m8_prereg_rehearsal.txt` (and `…_run1.txt`, the run before the `no_coverage` rebuild).
**55 command runs, 0 non-zero exits, 77 labels assigned, 3,397 s of subprocess time.**
Every scenario's targeted test produced the label its declared truth requires.

| scenario | targeted test | expected | **got** | |
|---|---|---|---|---|
| `null_eb26` 633+347 | D2, D3 | NULL | **NULL, NULL** | ✓ |
| `null_even` 490+490 | D2, D3 | NULL | **NULL, NULL** | ✓ |
| `null_harness` 245+735 | D2, D3 | NULL | **NULL, NULL** | ✓ |
| `d1_effect` | D1 | POSITIVE | **POSITIVE** (Holm 0.0000) | ✓ |
| `d2_effect` | D2 | POSITIVE | **POSITIVE** (Holm 0.0000, AUC 0.655) | ✓ |
| `d3_effect` | D3 | POSITIVE | **POSITIVE** (Holm 0.0000, AUC 0.344) | ✓ |
| `d4_effect` | D4 | POSITIVE | **POSITIVE** (Holm 0.0000, rate diff 0.224) | ✓ |
| `d3_reversal` | D3 | DIRECTION REVERSAL | **DIRECTION REVERSAL** | ✓ |
| `d2_reversal` | D2 | DIRECTION REVERSAL | **DIRECTION REVERSAL** | ✓ |
| `thin` 5+4 | D1–D4 | NOT TESTABLE | **NOT TESTABLE ×4** | ✓ |
| `no_coverage` 380+208 | D3 | NOT TESTABLE | see §3e | ✓ (after rebuild) |

**The headline: at every one of the three projected ratios, a non-significant D1, D2 and
D3 comes back `NULL` and not `UNDERPOWERED`** — the smallest detectable AUC at 633+347 is
**0.575** against effects under test of 0.659 and 0.656, so the tests are decisive with
room to spare. The pre-registration's central promise — *"a non-significant December
result on D2/D3/D4 is a NULL, the outcome this project has never been able to claim"* —
**executes**.

**Label totality, from real numbers rather than from the selftest:**

| label | occurrences | first reached in |
|---|---|---|
| POSITIVE | 7 | `d1_effect`/D1/primary |
| POSITIVE (conservative, pooled) | 7 | `d1_effect`/D1/pooled |
| **NULL** | **20** | `null_eb26`/D1/primary |
| UNDERPOWERED | 7 | `null_eb26`/D4/primary |
| DIRECTION REVERSAL | 5 | `d1_effect`/D3/primary |
| NOT TESTABLE | 4 | `thin`/D1/primary |
| *POSITIVE (not decisive)* — GAP-1 | 1 | `d2_effect`/D4/primary |
| *POOLED: UNINTERPRETABLE (diluted)* — GAP-2 | 24 | `null_eb26`/D1/pooled |
| *DIRECTION REVERSAL (pooled, not interpretable)* — GAP-3 | 2 | `d3_reversal`/D3/pooled |

`scripts/m8_prereg_labels.py --selftest` (`out/m8_prereg_labels_selftest.txt`) additionally
proves the function is **total and deterministic** from hand-built inputs, including the
negative-control veto, which no real scenario tripped.

**Three things the rehearsal showed that no amount of reading would have.**

**(i) GAP-4 is not cosmetic — under the literal reading it costs December the D4 NULL.**
It fired **11 times**, and in *every one* the literal reading said NOT DECISIVE while the
difference-based reading said DECISIVE. Concretely: in all three null scenarios D4 came
back **`UNDERPOWERED`** where the difference reading gives **`NULL`**. `min_detectable_rate`
returns the smallest detectable *spurious* rate against the *observed* confirmed rate — on
the queue, `flag_astrom_quiet` marks ~26 % of rows, so the routine returns 0.35–0.45 and
the literal comparison against the pre-registered *absolute* 0.30 fails, even though the
sample has ample power for the pre-registered *difference* of 0.225. **December will
either claim a D4 null or not, depending on which sentence of §4 is read**, and the
registration does not say. This is the amendment that matters most.

**(ii) D1 and D2 really are one axis, demonstrated in situ.** On `d2_effect`, where *only*
ΔAmp_G was tilted, **D1 also came back POSITIVE** (Holm 0.0270). Nothing about X-ray was
touched — the correlation measured in §6.12 (AUC 0.873) did it. Two families, one finding.

**(iii) The pooled arm reproduces M5's real result, which is the check that it works.**
In `thin`, where the harness store is 5+4 and contributes almost nothing, the pooled D3
comes back **POSITIVE (conservative, pooled)** at Holm 0.0005 on 47+27 — that is M5's
published `astrometric_gof_al` effect, arriving through the pooling path exactly as it
should, and correctly labelled as a *secondary* conservative positive rather than a
headline.

### 3e. The regression check, the rebuild, and the final tally

**The frozen EB26 replication reproduces byte-identically through every M8 change**, which
is what §2.2 of the registration demands of it. Run as the first act of the driver, with
the sha256 prefixes M6 published:

| artifact | | |
|---|---|---|
| `m4_eb26_erosita_xmatch.csv` | `556144fc3299…` | **IDENTICAL** |
| `m4_eb26_discriminator_stats.txt` | `ecea9350f3ce…` | **IDENTICAL** |
| `m5_activity_eb26_table.csv` | `450c8f4e638a…` | **IDENTICAL** |
| `m5_activity_metric_results.csv` | `183234d12599…` | **IDENTICAL** |
| `m5_activity_discriminator_stats.txt` | `e6d9e1a2f459…` | **IDENTICAL** |

So the `--scopes` addition, the `.astype(float)` crash fix, the two new machine-readable
results files and the path-message fix change **no published number**.

**The one failure, and why it is reported rather than quietly re-run.** The first pass
returned `1 failure(s)`: `no_coverage`/D3 came back **NULL** where NOT TESTABLE was
expected — with numbers *identical to `null_eb26`*, which is the diagnosis. That scenario
had been built by blanking the driver column inside the verdict store, and M5 reads the
metric from `data/dr3_activity_columns.parquet`; the store's copy is never consulted, so
the scenario was silently rehearsing the null (§3a). Rebuilt from the **588 class-III
sources with no row in the activity pull** and re-run
(`out/m8_prereg_rehearsal_nocoverage.txt`):

```
  D2  primary  n= 0+0  -> NOT TESTABLE        D1 primary n=164+105 -> UNDERPOWERED
  D3  primary  n= 0+0  -> NOT TESTABLE        D3 pooled  n= 42+23  -> POSITIVE (conservative, pooled)
  D4  primary  n= 0+0  -> NOT TESTABLE
```

**PASS** — and it exercises the *second* NOT TESTABLE arm, "zero rows survive the join",
which is the one M5 family A actually returns for `activityindex_espcs`. D1 stays
testable, correctly: those sources have sky positions, so the eROSITA join works; it is
the *activity* metrics that do not exist for them.

**Final tally across the 11 scenarios** (`out/m8_prereg_rehearsal_labels.csv`, 77 labels;
the first pass is kept as `…_run1.txt` so the failure and its fix are both on the record):

| | primary | pooled |
|---|---|---|
| POSITIVE | 7 | — |
| POSITIVE (conservative, pooled) | — | 8 |
| **NULL** | **17** | — |
| UNDERPOWERED | 7 | — |
| DIRECTION REVERSAL | 5 | — |
| NOT TESTABLE | 7 | — |
| *POSITIVE (not decisive)* (GAP-1) | 1 | — |
| *POOLED: UNINTERPRETABLE (diluted)* (GAP-2) | — | 23 |
| *DIRECTION REVERSAL (pooled…)* (GAP-3) | — | 2 |

**0 non-zero exits in 55 subprocess runs**, every targeted expectation met, and the
regression check green.

> **A last landmine, and it eats the one result this project has never been able to
> claim.** The pre-registered label **`NULL` is exactly pandas' default NA token.**
> `pd.read_csv('…labels.csv')` reads all 17 of them back as `NaN`, and
> `df.label.value_counts()` then reports **zero nulls**. The file is written with the
> literal string because that is the registration's vocabulary; the writer now emits a
> `# READ WITH keep_default_na=False` header line so the reader does not have to know in
> advance. December will produce this file and somebody will load it.

---

## 4. Task 4 — runbook, config v6, and the rehearsal

### 4a. Runbook

`DR4-DAY-RUNBOOK.md`, changed in six places, all of them things somebody has to *do* on
the day:

1. **Header** — a new standing block: apply the zero-point, inflate by ×1.4, and the one
   line that says M7's ×2.3 was a median |z|.
2. **§3.3** — a new *"THEN ASSIGN THE LABELS — do not do this by hand"* step pointing at
   `m8_prereg_labels.py`, the four registration gaps in a table with what each emits, the
   negative-control veto's new code path, and the D1/D2 axis-correlation caveat.
   The D4 command line gains `--out-dir out\dec\primary` so it stops writing beside the
   frozen M6 artifacts.
3. **§3.4** — both caveats rewritten from the M8 measurements, and the command block now
   starts with `m8_zeropoint.py --selftest` + `--pull` and runs the science pass with
   **`--zeropoint`** while the acceptance pass deliberately does not.
4. **A DR4-specific STOP** in §3.4 — and checking it turned up something the repository
   did not know. Lindegren+2021 is calibrated on **EDR3/DR3** and `m8_zeropoint.py` reads
   `gaiadr3.gaia_source`, so applying it to DR4 is an approximation. Reading the
   pre-release **draft data model** to see whether the five input columns survive
   (`data/draft-data-model/…pdf`, 1,231 pp.) found that they do — and found a column
   nobody here had looked for, declared in **both `gaia_source` and
   `all_source_astrometry`**:

   > **`tentative_parallax_bias`** : Parallax bias correction (double, Angle[mas]) —
   > *"This is the parallax bias correction computed based on the recipe in [the DR4
   > astrometry paper]. **This correction is to be subtracted from `parallax` to get the
   > corrected parallax.**"*

   **DR4 ships its own zero-point, on L21's exact convention.** The runbook now says to
   pull it in Phase 0 and prefer it, keeping L21 as the cross-check — with the caveat that
   the name says *tentative* and the model is a *draft*. The same read also found that
   **`astrometric_params_solved` becomes `astrometric_params`** in DR4, and that column is
   the 31/95 guard `zpt.get_zpt` **raises** on if it is wrong.
5. **Three new failure branches** — the D4 `--scopes` argparse exit, the M5
   December-scale `log10` crash, and `no L21 zero-point available … UNCORRECTED` (with
   what it costs: ~3Z/ϖ, ≈ 6 % at 1.7 mas and ≈ 20 % at 0.5 mas).
6. **"What ships when"** — the headline artifact must be produced with `--zeropoint` and
   shipped with both M8 caveats.

`queries/dr3-to-dr4-tables.md` gains a section for the **five zero-point input columns**,
because none of them was in the rename map and one of them
(`astrometric_params_solved` → likely `astrometric_params`) is already flagged there as a
probable DR4 rename — and getting *that* one wrong makes `zpt.get_zpt` **raise** rather
than return NaN.

### 4b. Config v6 — and this time the bump carries a decision

`scripts/m8_config_v6.py` → `queries/dr4-triage-config.v6.json`. M7 declined to write a
config and was right to; M8's two decisions change every number the pipeline publishes, so
v6 exists. **Selection, screen, probability method and membership are identical to
v2/v3/v4/v5 — 949 rows, unchanged since M2.** Acceptance re-checked before writing:
**BH1 + BH2 are the top two by M₂_min** in the day-one queue (PASS), and the frozen EB26
operating point is unchanged at **39/42 kept, 7/23 passed** (PASS). v1–v5 untouched on
disk. What v6 adds:

- `parallax_zeropoint_policy` — the correction, the convention, where it is applied, the
  house-pattern guards, the three validations, the measured effect, the residual bound,
  "prefer `a1` where DR4 publishes it", and a `dr4_supersession` block naming
  **`tentative_parallax_bias`**, the column the DR4 draft data model already declares
  (§4a) and which December should prefer over the L21 recipe;
- `error_inflation_policy` — ×1.4 with its CI, the convention (and the explicit statement
  that M7's 2.3 was a median |z|), the coverage numbers, the queue-reweighted 1.19, all
  four trends, and the injection–recovery result that says the Laplace σ itself is fine;
- `discriminator_axis_independence` — D1 vs D2 at AUC 0.873;
- `prereg_execution` — the three code defects fixed and the four registration gaps
  reported.

### 4c. The full DR4-day rehearsal — all nine stages green

`scripts/rehearse_dr4_day.py`, re-run end to end after every M8 change
(`out/m8_rehearsal_day.log`, `out/rehearsal_timings.csv`):

| stage | s | status | note |
|---|---|---|---|
| A — schema pin | 4.8 | OK | ESAC answered directly today; no ARI failover needed |
| B — rename patch + live probe | 3.8 | OK | |
| C — plan-B ranged pull | 4.6 | OK | resumed from 94 cached chunks; **169,227 rows, sha256 `b3b099a6…dddd5231` for the SIXTH time** |
| D — triage + BH1/BH2 acceptance | 36.5 | **PASS** | |
| E — corr_vec (measured) | 74 + 10 | OK(measured) | |
| F — epoch-vet, production harness | 2.1 | **PASS** | 3/3 kept, 9/9 demoted, max \|Δf2\| vs the M3 prototype **0.0050** |
| G — bulletin | 0.1 | OK | |
| H — day-one queue | 0.1 | **PASS** | 983 rows, BH1/BH2 top-2 asserted by the builder |
| I — verdict store | 0.1 | **PASS** | 88 records, 2 producers, 2 scopes, schema-validated |
| **total** | **52 s** | **COMPLETE** | |

Re-run twice: 56 s early in the milestone, **52 s at close after every change**. Against
M7's 722 s and M6's 82 s that is archive weather, not a speedup — stage A was 291.8 s of
ESAC failover in M7 and 4.8 s today. **What the rehearsal certifies is the nine statuses,
and all nine are green in both M8 runs.**

---

## 5. Files

| artifact | what |
|---|---|
| `scripts/m8_zeropoint.py` | the Lindegren+2021 house pattern + the 5-column pull; `--selftest` reproduces the sibling project's pinned anchor |
| `scripts/m8_zeropoint_effect.py` | Z1–Z5: validation, the convention correction, BH3 with and without, the queue-scale shift, the residual bound |
| `scripts/m8_error_inflation.py` | S1 SB9, S2 dual solutions, S3 injection–recovery through the arm, S4 the M7 anchor |
| `scripts/m8_synthetic_store.py` | the eleven declared synthetic verdict stores; `--axis-correlation` |
| `scripts/m8_prereg_labels.py` | **the pre-registration's §5 and §2.2 as one total function**, with the four gaps flagged |
| `scripts/m8_prereg_rehearsal.py` | runs every pre-registered command + label against every store; the byte-identity regression check |
| `scripts/m8_config_v6.py` | acceptance re-check → `queries/dr4-triage-config.v6.json` |
| `out/m8_zeropoint_effect.txt`, `out/m8_zeropoint_{trio,queue}.csv`, `out/m8_zeropoint_summary.json` | task 2 |
| `out/m8_error_inflation.txt`, `out/m8_inflation_{sb9,duals,injection_clean,injection_jitter1x}.csv` | task 1 |
| `out/m8_prereg_rehearsal.txt`, `out/m8_prereg_rehearsal_{labels,runs}.csv`, `out/verdicts_synth/` | task 3 |
| `out/m8_refit_{trio,vs_literature}_zeropoint.csv`, `out/m8_verdicts_v2_zeropoint.csv` | the arm's December-mode output |
| `out/m8_refit_acceptance_corrected.json` | the acceptance JSON with the DR3 id that M7's frozen copy gets wrong (§6.1) |
| `out/m8_axis_correlation.txt` | D1 and D2 are not independent |
| `out/m8_prereg_labels_selftest.txt` | the label function is total and deterministic: all six labels, all three beyond-the-six cases, the veto |
| `out/m8_rehearsal_day.log`, `out/rehearsal_timings.csv` | the green nine-stage rehearsal |
| `queries/dr4-triage-config.v6.json` | **config v6** (v1–v5 untouched) |
| `data/dr3_zeropoint_columns.parquet` + `.NOTE.md`, `data/sb9/*.parquet` + `README.NOTE.md` | the two new inputs, both with sourced provenance |
| **modified** | `scripts/orbital_refit_arm.py` (`--zeropoint`, two out-dir leaks), `scripts/m4_eb26_erosita_test.py` (+results CSV), `scripts/m5_activity_discriminator.py` (the December-scale crash), `scripts/m6_astrom_quiet_decision.py` (`--scopes`/`--sources`, +D4 results CSV, the lying path), `DR4-DAY-RUNBOOK.md`, `queries/dr3-to-dr4-tables.md`, `STATUS.md` |

**Frozen-artifact verification at close** (`git status` over `gaia-dr4/`): configs
v1–v5 **untouched**; `schemas/day1_verdict_record.v{1,2}.json` **untouched**;
`out/verdicts/*.csv` and `out/verdicts_v2/*.csv` **untouched**; every M2–M7 result CSV,
PNG, JSON and stats file **untouched** — including `out/m7_refit_trio.csv`,
`out/m7_refit_vs_literature.csv` and `out/m7_refit_acceptance.json`. One of them,
`m7_refit_vs_literature.csv`, **was** overwritten by an M8 run before the second out-dir
leak in §6.4 was found; it was restored from git, the leak was fixed, and the frozen file
re-verified byte-identical afterwards. The v2 store was at risk from the same class of bug
and was caught first, by hashing before and after. The five frozen M4/M5 artifacts additionally reproduce
**byte-identically** through the modified consumers (§3e).

---

## 6. Corrections and new landmines

1. **`out/m7_refit_acceptance.json` — a frozen M7 artifact — contains a source_id that
   does not exist.** It records `_dr3_source_id = 4318465066420528128`; Gaia BH3's DR3 id
   is `…528000`. This is M7's own landmine #4 (`.iloc[0].to_dict()` rounding past 2⁵³): M7
   found it, fixed the code, and never regenerated the artifact that had already been
   written with the bad value. `out/m7_refit_trio.csv` and the v2 store, written after the
   fix, are correct. **Not overwritten here** — the freeze is the freeze; the corrected
   file sits beside it as `out/m8_refit_acceptance_corrected.json`. *Fixing the code does
   not fix the artifacts the bug already wrote.*
2. **M7's "median factor 2.3" is a median |z|, not an inflation factor.** A standard
   normal has median |z| = 0.674, so the multiplier implied by the same eleven elements is
   **3.4**. Two conventions in one repository is one too many; every M8 number is
   median|z|/0.674 with the raw median printed beside it.
3. **`DataFrame.iterrows()` is the same 2⁵³ trap as `.iloc[0].to_dict()`.** M7 documented
   the row-dict form; the loop form does the same thing, and printed
   `1522897482203494912` for a source whose id ends `…494784`. The computation used the
   right ids — only the printed table was wrong, which is the worst kind of wrong.
   **Take an int column from the COLUMN, by position.**
4. **A script that takes `--out-dir` and then writes somewhere else, twice in one file.**
   `orbital_refit_arm.py --trio --out-dir <scratch>` wrote `m7_refit_vs_literature.csv`
   and the **v2 verdict store** into `out/` and `out/verdicts_v2/` — straight over frozen
   artifacts. Caught by hashing before and after, and by `git status` at close. Same
   family as M7 landmine #14, and the reason the close-out check exists.
5. **A zero-point applied to the point estimate and not to the posterior** ships a
   corrected mass inside an uncorrected interval. The first wiring did exactly that; the
   correction has to enter `posterior_draws` as well.
6. **A confound guard that only runs for metrics that discriminate is a code path that
   only executes at scale.** `m5_activity_discriminator.py` had a `np.log10(np.clip(...))`
   that had never seen a boolean column because no boolean metric had ever survived Holm
   on 65 rows. At 633+347 one did, and the test died after printing most of its output.
   **Latent bugs live behind significance gates.**
7. **A pre-registered command list is only as executed as its least-run line.** M7 ran the
   four discriminator commands and wrote "the commands as written below run". The D4 line
   — `--scopes` against a parser that had no `--scopes` — was never typed, and would have
   exited 2 on release day.
8. **The six pre-registered labels are not exhaustive, and §5 and §2.2 disagree.** Four
   distinct cases (§3c) reach no label or two. Every one of them was found by *writing the
   function*, not by reading the document — which is the argument for making a rule
   executable even when nobody plans to run it yet.
9. **`min_detectable_rate` is measured against the OBSERVED baseline**, so "DECISIVE"
   is only well-defined for a rate test when the observed baseline matches the
   pre-registered one. It did not, on the very first synthetic store.
10. **Panuzzo's paper corrects one parallax table and not the other, and says so in two
    different places.** Any comparison against a published parallax must state which
    convention both sides are on. M7's 5–41 µas was half systematic, half bookkeeping.
11. **`gaiadr3-zeropoint`'s dist metadata says 0.1.0 while `zero_point.__version__` says
    "0.0.1"** (carried from the sibling project). Stamp provenance from the dist metadata.
12. **The pre-registration corrects within families "because the families ask different
    questions of different data" — and for D1 and D2 that premise is false.** Measured on
    the queue itself: X-ray-detected rows are more photometrically variable at
    **AUC 0.873, p = 7.4×10⁻¹²**. The rule stays; the interpretation must not. The
    rehearsal showed this in situ before it was measured deliberately: on the `d2_effect`
    store, where only ΔAmp_G was tilted, **D1 came out POSITIVE too**.
13. **A synthetic control that does not change what the test reads is worse than none.**
    The first `no_coverage` scenario blanked a column *in the verdict store*, but the
    metric lives in a parquet the test loads separately — so it would have rehearsed the
    null and printed a green tick for the coverage path. Zero coverage has to be
    manufactured out of sources whose data genuinely does not exist (§3a). It was caught
    only because the scenario's numbers came out **byte-for-byte identical to
    `null_eb26`** — two "different" scenarios agreeing exactly is the signature.
14. **The pre-registered label `NULL` is pandas' default NA token**, so the December label
    file reads back with every null as `NaN` and `value_counts()` reports zero of them.
    The result this project has spent four milestones trying to earn, deleted by a default
    argument. Write the header line; read with `keep_default_na=False` (§3e).
15. **GAP-4 changes an outcome, not just a label.** Under §4's literal reading D4 comes
    back UNDERPOWERED in all three null scenarios; under the difference reading it comes
    back NULL. Eleven occurrences, unanimous disagreement. An ambiguity that only bites in
    one direction is not a footnote.

---

## 7. Recommended M9

1. **Take the pre-registration amendments to Matthew, then append them to the variant
   log.** Four gaps (§3c) and one interpretation caveat (§6.12) are written up and
   costed; none may be applied by an agent. This is the only item on this list that is
   blocked on a human, and it is the one that decides what December is allowed to report.
2. **Cross-calibrate L21 against DR4's own `tentative_parallax_bias`** — because M8
   answered half of this recommendation while writing it, and the answer changes the plan.
   Reading the pre-release **draft data model** (`data/draft-data-model/…pdf`, pp. 20 and
   74) turned up a column this repository did not know existed, in **both `gaia_source`
   and `all_source_astrometry`**:

   > `tentative_parallax_bias` : Parallax bias correction (double, Angle[mas]) — *"This is
   > the parallax bias correction computed based on the recipe in [the DR4 astrometry
   > paper]. **This correction is to be subtracted from `parallax` to get the corrected
   > parallax.**"*

   Same convention as L21, computed by ESA for DR4's own astrometry. **December should
   prefer it and keep L21 as the cross-check** (runbook §3.4 now says so). What is left
   for M9 is the calibration work: predict what DR4's bias will be for the queue's sources
   from the L21 model, so that on the day the two can be compared as a *prediction* rather
   than a shrug; and re-derive EB26's orbital-solution zero-point
   (Z = −0.0362 ± 0.0053) from their published with/without-L21 tables, which would give
   this project its own measurement instead of a quoted one. The same read also confirmed
   that `nu_eff_used_in_astrometry`, `pseudocolour` and `ecl_lat` survive into DR4 while
   **`astrometric_params_solved` becomes `astrometric_params`** — and that column is the
   31/95 guard, which makes `zpt.get_zpt` **raise** if it is wrong.
3. **Close the error-inflation loop where it is still open: the a₀ element.** SB9 gives P
   and e; neither is the element the mass function is cubed in. The queue's masses go as
   **a₀³**, and no external reference for a₀ has been used here. The candidates are
   EB26's own joint astrometry+RV solutions (they publish å₀ with intervals, and the full
   machine-readable table exists even though the arXiv source carries only eight rows) and
   the Hipparcos–Gaia proper-motion anomaly. **An inflation factor on P and e does not
   license one on a₀**, and §1 should say so more loudly than it does.
4. **Run the harness's own resume/kill contract against the synthetic-store machinery.**
   M8 rehearsed the *analysis*; the *production* half of December (harness → refit arm →
   v2 store → labels) has never been run as one chain on a store of December's size. The
   pieces are all now measured; the chain is not.
5. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew).
