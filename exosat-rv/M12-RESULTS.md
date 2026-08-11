# M12 — The source was superseded, and viper was modelling a gas cell that was not there

**Question:** the extraction sits ~25x above the precision the paper reports. M9 and M11
closed three suspects. What is left?

**Answer: the framing was wrong in two places before any of the suspects mattered.**

1. **The paper this project reproduces was published in *Nature* on 22 July 2026, and the
   peer-reviewed version differs materially from the arXiv v1 every milestone has used.**
   The precision target moved from **31.44 to 57.68 m/s**, the RV table from 20 to 23
   epochs, its **timestamps were wrong by 0.87 d**, the period from 169.45 to 171.11 d,
   Msini from 0.743 to 0.918 M_Jup, and the second satellite's evidence from
   **delta-logZ 6.64 to 2.62**.
2. **`viper` has multiplied the forward model by the CRIRES+ N2O gas cell spectrum in
   every run since M2**, on data taken with the cell wheel at `OPTI1 = FREE`. `-nocell`
   was never set.

Correcting the cell, and then also building the template the published (telluric-free) way,
takes the paper's own error statistic from **763 to 480 m/s** and — the part that matters —
removes a **highly significant correlation between the extracted RV and the barycentric
correction** that the authors explicitly report they do not have.

**Net movement: the gap is 8.3x, not 25x**, and it is now decomposed. Of the baseline
823 m/s, **522 m/s was BERV-correlated systematic and is now 150 m/s**; the remaining
**~620 m/s is a separate, non-BERV per-order systematic** that none of this touches. That
residual is the real open problem, stated more sharply than before.

**Both fixes are adopted, on evidence from the target itself.** They fail the GJ 229 B
control (§7) — and §8 shows the control is wrong. An injection-recovery test on CD-35 2722 B
returns **95% ± 7%** of an injected signal under the corrected model, against the **46%** the
control predicted: a 7σ disagreement, measured on the object that matters. The corrected model
also measures velocity **4.7x more precisely** under controlled injection (295 vs 1373 m/s)
and lands every order at 81–112% recovery where the baseline runs from −4% to 493%.

**The whole process now runs from raw data** — cr2res 1.6.10 built locally, five nights taken
through `cal_dark → cal_flat → cal_wave → obs_nodding` and on to RVs, reproducing ESO's own
products to 42 m/s (§9b). Measured against the paper's published RVs for the same nights, the
best configuration reaches **387 m/s rms against their 54 m/s — a factor of 7.2.** Not a
reproduction. §9b.4 records how a ten-minute repeatability test made this look like 0.36σ
agreement before the comparison against the published values corrected it by a factor of six.

---

## 1. The source moved

The preprint says so itself, in a comments field nobody read: *"Work accepted in Nature,
this is the initial version submitted to them before peer review. Please see the final
version published in Nature ... before reaching specific conclusions about this work."*

The accepted version is public and unpaywalled — ESO hosts it with the press release.
Archived here as [`papers/pdf/hoy2026_nature_published.pdf`](papers/pdf/hoy2026_nature_published.pdf)
(35 pages, against the preprint's 27) and
[`papers/text/hoy2026_nature_published.txt`](papers/text/hoy2026_nature_published.txt).

| | arXiv v1 (used by M0–M11) | **Nature (published)** |
|---|---:|---:|
| Mean RV error — "the target" | **31.44 m/s** | **57.68 m/s** |
| Median RV error | 30.40 | 57.00 |
| Epochs in the RV table | 20 | **23** |
| Baseline | 465 d | **851 d** |
| Nodding-frame gain (Fig. 4) | 34.49 → 31.44 (**~10%**) | 60.50 → 57.68 (**4.9%**) |
| Period 1 (1-satellite) | 169.45 d | **171.112** +0.525/−0.363 d |
| Period 1 (2-satellite) | 169.45 d | **171.454** +0.191/−0.813 d |
| Amplitude 1 | — | 318.5 / 306.0 m/s |
| Msini 1 | 0.743 M_Jup | **0.918** +0.011/−0.045 M_Jup |
| Period 2 | 87 d | 87.349 +0.641/−0.451 d |
| Msini 2 | 0.277 M_Jup | 0.219 +0.048/−0.046 M_Jup |
| logZ (1-sat / 2-sat) | −122.654 / −129.295 | **−144.323 / −141.701** |
| **delta-logZ for a 2nd satellite** | **6.641** (text quotes 6.9) | **2.622** |
| Orders used | not stated | **eleven** |

Three consequences the project has to absorb:

- **`config.py` is pinned to superseded values throughout**, including
  `test_table1_logz_difference_does_not_match_the_quoted_delta`. M1 §1.3 corrected M0 by
  establishing that the second-satellite evidence is 6.9, not 2.6. That was right about the
  preprint and is now wrong about the paper. In the published Table 1 the **1-satellite fit
  is the eccentric one** (e = 0.269) and the **2-satellite fit is circular** (e = 0.001),
  separated by **delta-logZ = 2.62 with ±0.7 on each term.** That is a materially weaker
  second satellite than anything this project has recorded.
- **M6 fitted the wrong table.** It reproduced the conclusion from 20 preprint RVs. There
  are now 23, over 1.83x the baseline, with different values and corrected times.
- The published Methods still quote "169.45 +1.1/−1.06 days" in the barycentric-aliasing
  discussion while Table 1 gives 171.454. That is the authors' own residual inconsistency,
  noted rather than made much of.

### 1.1 The preprint's RV timestamps are wrong by 0.87 days, and our archive proves it

Computing BJD_TDB from the ESO product headers (`MJD-OBS + TEXPTIME/2`, Paranal, barycentric
light-travel to the target) and matching each table to it:

| table | median offset from our archive times |
|---|---:|
| arXiv v1 | **−75 348 s = −0.8721 d** (17 of 18 epochs; its first epoch is not offset) |
| **Nature** | **−232 s** |

The published times match the archive to under four minutes — that residual is just the
difference between the combined product's midpoint and the mean of the two nodding frames.
**This is an independent, archive-based confirmation that the published table is the correct
one**, and it is a check only the raw metadata can make.

## 2. What 57.68 m/s actually is — the project has been comparing two different statistics

The published version prints the error definition the preprint only described in words —
Köhler et al. (2025) Eq. 1, reproduced as the paper's Eq. (1):

```
eps_RV = sqrt( 1/(No-1) * sum_o eps_o^-2 (RV_o - RVbar)^2 / sum_o eps_o^-2 )
```

**This is a weighted dispersion of the per-order RVs *within a single epoch*.** It is not
the scatter of RVs across epochs. The project has been comparing its epoch-to-epoch rms
(823 m/s) against the paper's within-epoch across-order dispersion (31.44, now 57.68 m/s).
That comparison was never like-for-like.

Computed properly on M2's own output, the two happen to land close together:

| | epoch-to-epoch rms | Eq. 1, mean over epochs | ratio |
|---|---:|---:|---:|
| M2/M9 baseline | 823 m/s | **763 m/s** | 0.98 |

**The ratio near 1 is itself the finding.** If epoch-level systematics — drift between
nights, calibration ageing, barycentric arithmetic — dominated, epoch scatter would greatly
exceed the within-epoch order dispersion. It does not. **Whatever the pipeline gets wrong,
it gets wrong inside a single epoch, spread across orders.** That is M9 §6's conclusion
re-derived in the paper's own units and independent of M9's sqrt(N) argument.

## 3. Eq. 1 is the non-circular objective this project has been missing

M9's empirical weighting and M11's template iteration both improved the target and were
caught only by GJ 229 B. Each fooled the target metric for the same reason: **epoch-to-epoch
rms falls when you delete the signal.**

Eq. 1 does not. A real RV signal is **common-mode across orders**: it moves every `RV_o` by
the same amount, moves `RVbar` with them, and cancels exactly in `(RV_o − RVbar)`.

> **Eq. 1 is mathematically invariant to the signal it is trying to measure.**

A configuration therefore cannot improve Eq. 1 by suppressing the Keplerian. It can only
improve it by making the orders agree — which is what a correct forward model does. That
makes Eq. 1 safe to optimise in a way epoch rms never was, and it is what any grid search
should score. A control is still required (a config driving *all* per-order RVs toward a
constant would improve both), but the specific trap that caught M9 and M11 is closed
against it.

## 4. viper has been modelling a gas cell that was not in the beam

`config_viper.ini`'s `[CRIRES]` section is the **gas-cell** configuration. It does not set
`nocell`; only `[CRIRES_tpl1]` and `[CRIRES_tpl2]` do. Every run from M2 to M11 used
`[CRIRES]` and passed `-fts .../CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat`, so
`viper.py:780` loaded the **SGC2 N2O cell** FTS spectrum and `utils/model.py:179`
multiplied it into the forward model:

```python
spec_gas = 1 * self.spec_cell_j     # <- the cell
spec_gas *= flux_atm                # <- the tellurics
Sj_eff = conv(S_star(lnwave - rv/c) * (spec_gas + bkg), IP)
```

**The data has no cell.** Every ADP product carries `ESO INS1 OPTI1 ID = 'FREE'`,
`TYPE = 'NONE'` — the cell wheel is out. Köhler et al. 2025 §5.4 states the cell-free
procedure explicitly: *"The modelling within viper follows the same procedure as described
above, just without the modelling of the cell lines."*

The H-band cell template is not flat. Over 1550–1750 nm, after removing a 2001-point
running continuum:

```
scatter               3.3%
deepest line          0.174   (83% absorption)
pixels below 0.99     7.9%
pixels below 0.95     2.0%
```

So the model carried a few thousand absorption features, some nearly black, absent from the
data — competing with the telluric lines that *are* the cell-free wavelength reference.

**Measured cost** (identical run, one flag added; the re-run baseline reproduces M9's 823.1
and 775.5 to the digit, so the harness is validated):

| | epoch rms | Eq. 1 | r(RV, BERV) |
|---|---:|---:|---:|
| baseline | 823 m/s | 763 m/s | −0.63 (p = 0.005) |
| **`-nocell`** | **672 m/s** | **568 m/s** | −0.40 (p = 0.10) |

**−18% on scatter, −26% on the paper's own metric.** For scale, M9 measured order screening
at 6% and the published Fig. 4 puts the nodding frames at 4.9%.

## 5. The template is not telluric-free, and its tellurics move with the fitted RV

[`docs/viper-runbook.md`](docs/viper-runbook.md) §4 builds the template by copying an
observation and multiplying its wavelengths by 10. Confirmed: `cd35_2722B_tpl.fits` carries
`ESO PRO CATG = OBS_NODDING_EXTRACTC_IDP` — **it is an ADP science spectrum, telluric lines
and all.**

Köhler §2.2 requires the opposite. `-createtpl` divides each spectrum by the fitted telluric
model, masks pixels where `gas_model < 0.2`, then co-adds (`viper.py:588–632`). The
runbook's template skips all of it.

The consequence is not "slightly noisy template". In the forward model the template is
evaluated at `lnwave − rv/c` — **Doppler-shifted by the fitted RV** — while the real
tellurics are static. The template's baked-in telluric lines therefore sweep across the real
ones as the barycentric velocity swings over ±15 km/s, and the fit trades RV against that
mismatch. It is a moving contaminant sitting exactly on the wavelength reference.

**Prediction: the extracted RV should correlate with BERV. It does — and fixing the model
removes it.**

| config | r(RV, BERV) | p | epoch rms | Eq. 1 |
|---|---:|---:|---:|---:|
| baseline | **−0.63** | **0.005** | 823 | 763 |
| `-nocell` | −0.40 | 0.103 | 672 | 568 |
| **telluric-free template + `-nocell`** | **−0.23** | **0.349** | **638** | **480** |

### 5.1 The improvement is targeted, not uniform suppression

The obvious objection is M11's: an apparent improvement on a target with no detected signal
is what suppression looks like. Decomposing the variance into the part a linear BERV term
explains and the part it does not:

| config | epoch rms | **BERV-correlated** | non-BERV | BERV share |
|---|---:|---:|---:|---:|
| baseline | 823 | **522** | 637 | 63% |
| `-nocell` | 672 | **266** | 617 | 40% |
| telluric-free tpl + `-nocell` | 638 | **150** | 620 | 23% |

**The non-BERV variance does not move (637 → 617 → 620). The BERV-correlated part falls by
3.5x.** Uniform suppression would shrink both together. These fixes remove one specific
systematic and leave everything else untouched — and the satellite signal is at 171 d, not
at the 365-d BERV period, so removing the BERV term cannot be removing it.

### 5.2 Three independent things line up with this

- **Per-order correlations are large and of mixed sign** (order 7: +0.55, order 16: −0.62).
  That is what a contaminant whose position depends on where the template's telluric lines
  fall in each order looks like. A barycentric *arithmetic* error would be common in sign.
- **M2's GLS peaks at 368 days** with power 0.545, read at the time as "observing-season
  structure". 368 d is the BERV period.
- **The paper says it checked exactly this and found nothing**: *"we have extensively
  investigated this possibility and have found no correlations between the derived RVs and
  the applied barycentric correction."* Their template was telluric-free. Ours was not.
  **This is the sharpest measured difference between their extraction and ours.**

### 5.3 It also reframes M11

M11 rebuilt the template with `-createtpl`, got 776 → 620 m/s on the target, and rejected it
because the control collapsed to 41%. But `-createtpl` *simultaneously* removed the telluric
contamination and introduced self-templating — **and it ran with the cell error still
present.** Three effects, one number. **M11's verdict is conditional on a forward model now
known to be wrong**, and its headline rule ("do not iterate a self-built template") is not
retracted but is no longer cleanly established.

## 6. The paper's Fig. 11 names its own configuration, including `-telluric add2`

The published Fig. 11 (Fig. 7 in the preprint) plots a periodogram per fitted viper
parameter. The panel labels are a complete listing of the authors' free parameters:

```
RV
Instrument Profile                            -> ip = g   (one parameter)
0th / 1st Order Normalization Coefficient     -> deg_norm = 2
0th / 1st Order Wavelength Calibration Coeff. -> deg_wave = 2
Precipitable Water Vapor Coefficient          -.
Non-Water Telluric Abundance Coefficient      -'  -> TWO telluric coefficients
```

viper's help text: *"add: telluric forward modelling with one coeff for each molecule;
**add2: telluric forward modelling with combined coeff for non-water molecules**"*. Two
coefficients — water, and everything else — **is `add2`.** This project has used `add`,
which frees four (H2O, CH4, N2O, CO2 are the H-band molecules in
`lib/atmos/stdAtmos_H.fits`).

Tested, and it does not help on our data (§7): `add2` alone gives 858/772, worse than
baseline. Recorded because the inference is sound and the measurement is negative — any gain
is presumably downstream of the template fix. The rest of the panel list **confirms**
`deg_norm = 2`, `deg_wave = 2` and a single-parameter Gaussian IP, all of which this project
already had right.

## 7. Everything measured, target and control together

All runs: same 18 archive nights, `viper` under WSL per the runbook, one flag at a time.
Control: GJ 229 B, 16 products, known 12.1621 d binary, amplitude fitted at the known period.
`%base` is relative to the baseline **in this scorer**, which returns 8285 m/s where M3's
returns 6165 — the scorers differ, so only the relative column is meaningful and none of it
is comparable to numbers published in M3, M9 or M11.

| config | ord | epoch rms | **Eq. 1** | r(BERV) | p | ctrl K | %base | ctrl night rms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline (M2/M9) | 10 | 823 | 763 | −0.63 | 0.005 | 8285 | 100% | 1564 |
| `-nocell` | 10 | 672 | 568 | −0.40 | 0.103 | 5526 | 67% | 1405 |
| `-telluric add2` | 10 | 858 | 772 | −0.65 | 0.003 | 4436 | 54% | 1940 |
| `-nocell -telluric add2` | 10 | 836 | 686 | −0.43 | 0.078 | 3851 | 46% | 1623 |
| `-oset 1:18` | 17 | 682 | 748 | −0.41 | 0.089 | 5287 | 64% | 1008 |
| all three | 17 | 762 | 613 | +0.26 | 0.307 | 1482 | 18% | 895 |
| **telluric-free tpl + `-nocell`** | 10 | **638** | **480** | **−0.23** | **0.349** | 3814 | **46%** | 1373 |

**Every configuration fails the control, including the two that are certainly correct
physics.** Nothing here is adopted.

Note `-oset 1:18` separately: adding the seven bluest segments (1469–1550 nm) helps epoch rms
and hurts Eq. 1 and the control. Those are the telluric-poor orders, and the paper's own rule
— exclude orders without enough telluric lines to recalibrate — predicts exactly that. It is
the first time the paper's order rule has been *confirmed* here rather than contradicted
(M9 §5 found the reverse using `atm0` as the proxy; the proxy was the problem).

### 7.1 The GJ 229 B control can no longer adjudicate this, and here is why

The control's veto has been the project's most valuable instrument (M9 §5). It is being
over-applied here, for a reason that is quantitative rather than convenient:

**Self-templating suppression scales with the signal's amplitude relative to the template's
epoch spread.** GJ 229 B moves by **±6–18 km/s** across its six nights; CD-35 2722 B moves by
**±250 m/s** across eighteen. A co-added template absorbs a 12-km/s binary catastrophically
and a 250 m/s Keplerian **~70x less**. Using GJ 229 B to veto self-templating on CD-35 2722 B
is not conservative; it is the wrong test by nearly two orders of magnitude.

Two further limits, both already on record: GJ 229 B is an **unresolved double-lined blend**
whose "correct" recovered amplitude (~6000 m/s) is a model-dependent expectation, not a
measurement (M3 §4, M11 §6); and its own template is a raw observation, so both arms of every
comparison above run through the §5 defect.

**This was the blocker, and §8 removes it.** The injection test on CD-35 2722 B returns
**95% ± 7%** where the control predicted 46%. The argument above is no longer a plausibility
case; it is measured. **GJ 229 B remains a useful check that the extraction works at all
(M3's purpose) and must not be used to veto forward-model changes at the target's amplitude.**

## 8. The injection test — built, run, and it clears the corrected configuration

Inject a known Keplerian into CD-35 2722 B's own spectra and measure what comes back.

### 8.1 The trap in the obvious implementation

Multiplying each observation's `_WL` column by `(1 + v/c)` moves the star *and the tellurics*
together — and the tellurics are the wavelength reference, so viper recalibrates the
injection away. Measured on one epoch, injecting 1000 m/s:

| method | recovered | |
|---|---:|---|
| shift the **observation** wavelengths | **+83 m/s** | 92% absorbed — useless |
| shift the **template** wavelengths by −v | **+1175 m/s** | works |

Anyone building this the obvious way would have measured a pipeline 92% blind to radial
velocity and concluded the extraction was broken.

### 8.2 The harness

Shift the *template* by `−v_i` per epoch, with `v_i` a Keplerian at the published
**306 m/s / 171.454 d**; run viper once per epoch against its own shifted template; regress
`(RV_injected − RV_reference)` on `v_i`. The slope is the recovery fraction.

Epoch 0 lands at `v = 0` exactly, and its single-epoch run reproduces that epoch's value from
the 18-file run to **0.000 m/s** — viper fits epochs independently, so the multi-epoch run is
a valid reference and only the shifted arm needs re-running. Repeated at **5× amplitude**
(1530 m/s), since slope precision scales as 1/K.

### 8.3 Result

| run | n | recovery | ± | resid rms |
|---|---:|---:|---:|---:|
| K = 306, telluric-free tpl + `-nocell` | 18 | 143% | 36% | 306 |
| K = 306, M2/M9 baseline | 18 | 84% | 53% | 453 |
| **K = 1530, telluric-free tpl + `-nocell`** | 18 | **95%** | **7%** | **295** |
| K = 1530, M2/M9 baseline | 18 | 121% | 32% | **1373** |

**The corrected configuration recovers 95% ± 7% of an injected signal on the science target
itself.** The GJ 229 B control said 46%. That is a **7σ** disagreement, measured on the object
the project actually cares about, and it settles §7.1: **the control was the wrong instrument
and `-nocell` plus a telluric-free template should be adopted.**

Both configurations transmit roughly the full amplitude on average. What separates them is
noise: **295 m/s of differential scatter against 1373 m/s, a factor of 4.7.**

### 8.4 Per-order recovery is a non-circular order screen

| run | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K=306 corrected | 90% | 56% | 98% | 75% | 99% | 100% | 95% | 95% | 85% | 95% |
| K=306 baseline | **−49%** | **493%** | 69% | **25%** | **368%** | 93% | 81% | 91% | 125% | 73% |
| **K=1530 corrected** | 112% | 81% | 99% | 87% | 97% | 102% | 99% | 98% | 98% | 98% |
| K=1530 baseline | 83% | **−4%** | 77% | 86% | 60% | 96% | 101% | 114% | 100% | 114% |

Under the corrected model every order lands in **81–112%, median 98%** — the orders are
measuring velocity. Under the baseline they are chaotic: order 7 **anti-correlates** with the
injected signal at K=306, order 8 amplifies it 5× and then returns **−4%** at K=1530.

**This replaces M9's order screen with a principled one.** M9 dropped order 8 because its
scatter was largest — circular reasoning that the control had to rescue. Injection recovery
says the same thing for a physical reason: *order 8 does not respond to velocity.* A screen on
recovery fraction cannot delete signal, because deleting signal is exactly what it measures.

### 8.5 What the residual scatter says — and one lead already killed

295 m/s of scatter survives in the corrected arm, and both arms of each comparison use the
**same observation**, differing only in the template's wavelength grid. Per-epoch systematics
cancel exactly, so that 295 m/s is the fit's own instability under a template
reinterpolation. `config_viper.ini` sets `oversampling = 1`, which made template
interpolation noise the obvious suspect.

**Tested and false.** Oversampling the template makes it worse, non-monotonically:

| `-oversampling` | epoch rms | Eq. 1 |
|---:|---:|---:|
| **1 (default)** | **638** | **480** |
| 2 | 714 | 522 |
| 4 | 1116 | 501 |
| 8 | 688 | 602 |

So the 295 m/s is not sampling error in the template. It is real sensitivity of the
least-squares solution to a change in the template, which is a harder problem and still
unexplained. **The ~620 m/s residual keeps its leading candidate from §9: the wavelength
solution and the strength of the telluric anchor, per M9's finding that `atm0` is
unconstrained in 6 of 10 orders.**

### 8.6 One diagnostic attempted and not interpretable

`par.dat` carries `wave0`, the constant term of each order's wavelength polynomial, so in
principle one can measure how much of the injected shift leaked into the wavelength solution
instead of into `rv` — the degeneracy the telluric anchor is supposed to break. The numbers
come back scattered from −251% to +162% with no coherent pattern, and positive leaks coexist
with ~100% recovery, which should not both be true. Either the units/sign convention is wrong
or the comparison needs the covariance. **Recorded as attempted and unresolved, not as
evidence.**

## 9. What to do next, in order

0. ~~**Build the injection-recovery harness.**~~ **DONE — §8.** It clears the corrected
   configuration at 95% ± 7% and overturns the control's veto. The scripts are
   `scratchpad/mktpl.py`, `inject_run.sh`, `inject_final.py`; **budget one viper run per
   epoch per arm**, and remember §8.1 — shift the template, never the observation.
1. **Re-score §7's whole table under injection recovery.** Only two of seven configurations
   have been through it. `add2`, `oset 1:18` and the combinations are still judged by a
   control now known to be the wrong instrument.
2. **Chase the ~620 m/s non-BERV residual** — now the dominant term. `-oversampling` is
   already eliminated (§8.5). The standing candidate is the **wavelength solution and the
   strength of the telluric anchor**: M9 measured `atm0` unconstrained in 6 of 10 orders, and
   §8.4 now shows those same orders are the ones that fail injection recovery. Test
   `-deg_wave 3`, `-chunks > 1`, and `-telluric sig`/`mask`, each scored by §8.4.
3. **Then brute-force.** Runs cost 60–90 s. A few hundred cells over
   `{telluric add/add2/mask/sig} x {oset} x {ip} x {deg_wave} x {chunks} x {kapsig} x
   {oversampling}` is an afternoon. Score on **Eq. 1** (§3), with **per-order injection
   recovery** (§8.4) as the hard constraint — never on epoch rms, which is what M9's screen
   gamed, and no longer on GJ 229 B amplitude, which is what M11's did.
5. **Cross-check the wavelength solution without viper.** Correlate each order's telluric
   lines against a TAPAS/molecfit H-band model for a per-order, per-epoch velocity zero point.
   If that alone reproduces ~600 m/s, the residual is the wavelength solution; if not, it is
   the stellar side of the model.
6. **Re-run M6 against the published 23-epoch table** and re-pin `config.py` to the Nature
   values. M6's claim should be restated against delta-logZ = 2.62, not 6.9.
7. **The nodding frames, last, at 4.9%** — the published Fig. 4 revises M9's 10% downward.
8. **Ask the authors.** The Nature version carries *"All correspondence and request for
   materials can be made to Kevin Hoy (kevin.hoy@mail.udp.cl)"*, and Nature's materials policy
   makes a reproduction request for the exact viper invocation entirely ordinary. One email
   would settle §4, §5 and §6 outright. **Requires the human to send it — no agent should.**

## 9b. From raw data, end to end — and the null test that localises the residual

The archive route was never the whole process. `cr2res` 1.6.10 — the paper's exact version —
is now built locally (`scripts/cr2res/`), and one night has been taken from raw frames
through `cal_dark → cal_flat → cal_wave → obs_nodding` to RVs.

**The reduction is validated.** Our from-raw combined extraction reproduces ESO's archived
product for the same night to **57 m/s in wavelength** and, after viper, to **42 m/s in the
final RV** (−1975 vs −1933 m/s), with per-order agreement of 40–80 m/s. Every one of the
recipe's twelve default parameters matches what the ADP headers record ESO used.

### 9b.1 A retraction, made before it propagated

On finding that A and B sit **4.1 px apart** (median; up to 8.6 px, i.e. 0.4–8.6 km/s — real
slit tilt over a 108-px nodding throw, confirmed both from the wavelength solutions and by
cross-correlating the flux), I claimed ESO's combined product must be smeared and that the
archive route was therefore structurally incapable of reaching 57 m/s.

**That is wrong.** Fitting two explicit models to ESO's product — `a·A + b·B` at matching
pixel index versus `a·A + b·B_resampled_onto_A` — the resampled model wins **19 of 21
segments**, and by a wider margin where the offset is largest. cr2res resamples before
summing. The archived product is sound and the claim is withdrawn.

### 9b.2 The null test

A and B are the same star **10.6 minutes apart**. A 171-day orbit moves under 1 m/s in that
time, so the true difference is zero and **the astrophysical signal cancels exactly**.

| order | nodA | nodB | A − B |
|---:|---:|---:|---:|
| 7 | −4348 | −4894 | +545 |
| **8** | 3435 | 7624 | **−4189** |
| 9 | −4485 | −3978 | −507 |
| 10 | −4028 | −4291 | +263 |
| **11** | 1931 | −102 | **+2033** |
| 12 | −1021 | −1157 | +136 |
| 13 | −742 | −1315 | +573 |
| 14 | −1177 | −877 | −300 |
| **15** | 835 | −957 | **+1792** |
| 16 | −1050 | −1179 | +130 |

**Binned A − B = +518 m/s; per-order rms 866 m/s** (order 8 dropped). That is the whole
residual of §5.1, appearing between two exposures ten minutes apart.

It therefore cannot be the archive products (we reproduce them to 42 m/s), the A/B
combination (§9b.1), barycentric anything (ten minutes), the gas cell or the template (both
fixed, and identical across the two arms), or the signal (differenced away).
**The residual is a per-frame extraction error.**

### 9b.3 The mechanism, confirmed by intervention

Sweeping the forward model against A − B (17 configurations, ~15 s per run — the null test is
signal-free, needs one night, and needs no proxy target):

| config | A − B | rms(A−B) | Eq. 1 |
|---|---:|---:|---:|
| `-telluric add2 -deg_wave 3` | **+25** | 1040 | 574 |
| `-telluric add2` | **+91** | 917 | 578 |
| `-kapsig 3` | +168 | **620** | **536** |
| `-deg_wave 3` | +280 | 707 | 579 |
| **baseline (`telluric add`)** | **+518** | 866 | 584 |
| `-molec H2O` only | +1435 | 11390 | 1487 |
| `-telluric mask` | −3874 | 7875 | 2082 |
| `-telluric sig` | −4122 | 11671 | 3796 |

**Deliberately weakening the telluric anchor multiplies the per-frame error by 9x.** Masking
the tellurics, downweighting them, or fitting water alone all blow up A − B and the
within-frame dispersion together. That is the diagnosis established by intervention rather
than by correlation: **in cell-free mode the telluric lines are the only wavelength
reference, and the per-frame solution is limited by how well they pin it.**

Consistent with three independent things: M9 measured `atm0` unconstrained in **6 of 10
orders**; orders **8 and 11** are the worst here *and* the worst on injection recovery
(§8.4); and the well-behaved orders sit at 130–573 m/s while the bad ones reach 2000–4200.

### 9b.4 Five nights from raw, and the metric that nearly produced a false success

All five nights were taken from raw through the full cascade (~1.5 GB each). Sweeping five
configurations against A − B and adding an order screen on telluric anchor strength gave what
looked like a reproduction:

| | rms(A−B) | implied per-night error |
|---|---:|---:|
| baseline, no screen | 581 | 290 m/s |
| baseline + anchor screen | 269 | 134 m/s |
| **`-kapsig 3` + anchor screen** | **132** | **66 ± 23 m/s** |
| paper | — | **57.68 m/s** |

66 ± 23 against 57.68 is **0.36σ**. It is also wrong.

**A − B only probes ten minutes.** The paper's own statistic, Eq. 1, computed on the same
screened frames, says **563 m/s per frame → 398 m/s per night**, six times worse. The two
can only disagree if most of the per-order spread is a *static* offset that cancels in a
ten-minute difference. The question is whether those offsets are static on the timescales
that matter, and they are not.

**The decisive test — compare our from-raw RVs to the published ones, night by night:**

| config (+ anchor screen) | rms vs published Table 2 | published errors |
|---|---:|---:|
| baseline | 617 m/s | 54 m/s |
| **`-kapsig 3`** | **387 m/s** | 54 m/s |

**Eq. 1 predicted 398 m/s and the direct comparison measures 387 m/s — agreement to 3%.**
Eq. 1 was the right estimator all along; A − B was not, and the 66 m/s figure above is
withdrawn. Per-order zero points drift between nights, which A − B is blind to by
construction.

**So the honest number is 387 m/s against the paper's 54 m/s — a factor of 7.2.** Better
than the 823 m/s this project started with, better than the archive route's 480, and not a
reproduction.

Note also that the anchor screen improves A − B by 2–3× while leaving Eq. 1 flat
(720 → 760 baseline, 571 → 563 for `kapsig 3`). It improves ten-minute repeatability without
improving the actual RV precision. `-kapsig 3` does help on the real metric (617 → 387) and
was selected from ten cells, so it needs confirming on more nights.

**This is the fourth time in this project a metric has flattered a change** — after M9's
empirical weighting, M11's template iteration, and §7's control. The rule that survives:
**validate against the authors' actual published values whenever they exist; every internal
proxy tried here has been wrong by a factor of at least six.**

### 9b.5 What is not yet established

`add2` — the setting inferred from the paper's own Fig. 11 (§6) — looks best, taking A − B
from 518 to 91 m/s. **But one night gives 9 order-pairs, so the standard error on A − B is
~300 m/s and base-vs-`add2` is a 1.0σ difference.** It is not established. Three more nights
would give ~36 pairs and discriminate at ~150 m/s; the ESO archive was too slow to fetch them
at the time of writing (the intermittent outage of HANDOFF §5). **This is the next
measurement, and it is cheap.**

Note also that `-chunks > 1` and `-deg_wave 4` fail outright (zero orders returned).

## 10. Two suspects closed, cheaply

### 10.1 The ADP → cr2res conversion is correct. M11's "leading suspect" is dead.

M11 §5.2 named the converter the leading remaining suspect: lossless numbers could still have
landed in the wrong order/detector slots. They did not.

`inst_CRIRES.Spectrum` maps a viper order index to a (detector, DRS order) pair via
`divmod(order, 3)` and `det_ord_max`. Working that mapping through our files and comparing
each resulting segment's centre against **ESO's own per-order central wavelengths in the
product header**:

| viper order | segment centre | header value |
|---:|---:|---|
| 7 | 1567.0 | `CWLEN6 = 1567.099` |
| 10 | 1611.7 | `CWLEN5 = 1611.874` |
| 13 | 1659.1 | `CWLEN4 = 1659.282` |
| 16 | 1709.3 | `CWLEN3 = 1709.563` |

Every one lands on ESO's own value. All 21 segments are 2048 rows, strictly monotonic in
wavelength and in `XPOS`, three detectors x seven orders, detector 1 bluest. The reshape is
right — and this header cross-check took five minutes and was available from M1 onward.

### 10.2 `-tpl_wave tell` is a no-op for RV extraction

M11 §5.1 left this as the one experiment that could isolate the real part of M11. There is
none to isolate. `-tpl_wave` is read only inside the `if createtpl:` block
(`viper.py:609–618`); it selects the wavelength axis *written into a generated template*. An
RV run against a supplied template ignores it. Measured: `-tpl_wave tell` returns
**byte-identical** RVs to baseline (rms 1531.4399627620296 both ways). It matters for
`-createtpl`, and nowhere else.

## 11. Caveats

- **n = 18.** A single rms estimate carries ~17% fractional uncertainty, so the epoch-rms
  column separates almost nothing on its own. Eq. 1 averages 18 within-epoch dispersions of
  ~10 orders each and is roughly 7x tighter; read the ranking from that column.
- **r(RV, BERV) = −0.63 at n = 18** is significant (p = 0.005), but BERV is itself correlated
  with observing season, so season-dependent systematics are not excluded by the correlation
  alone. The variance decomposition (§5.1), the mixed-sign per-order pattern and the mechanism
  are what make the template the leading explanation.
- **The telluric-free template run is one iteration, not the paper's two.** It was stopped at
  one deliberately, to limit self-templating; the paper's two-iteration result is untested
  under a corrected forward model.
- **`-telluric add2` is inferred from figure panel labels**, not from a statement in the text.
  A strong inference, not a quotation.
- **The GJ 229 B control has been run under two different SIMBAD resolutions** across the
  project's history — `GJ 229` (the A component) in M3, `GJ 229 B` in M11. The positions
  differ by 7.5", worth about 1 m/s of BERV, so it is harmless — but M3 and M11 control
  numbers were not produced identically.
- **`-nocell` is correct physics and is still not adopted.** There is no cell in the beam and
  Köhler §5.4 says to model without cell lines. It improves the target on both metrics, it
  removes a systematic the authors report they do not have, and it costs 33% of the control's
  recovered amplitude. §7.1 argues the control is the wrong instrument for it. That argument
  should be *tested* (§9.1), not assumed.
