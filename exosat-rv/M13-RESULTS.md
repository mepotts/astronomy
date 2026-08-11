# M13 — The eleven orders found, the combine fixed, and the second satellite does not survive its own revised table

**Question:** M12 §9b left the from-raw extraction at **387 m/s rms against the paper's
published RVs** (their per-epoch claim: 57.68 m/s), with the paper's eleven orders unknown
and the inference never re-run on the corrected Nature table.

**Answer in three parts:**

1. **The paper's eleven orders are identified** — the `H_C` set,
   `oset 4,7,8,9,10,12,13,14,17,18,19` in current viper numbering — confirmed three
   independent ways (§1).
2. **The best extraction is now within reach of the published series.** `H_C` + `-kapsig 3`
   on a full-coverage telluric-free template (run `M13_G`) scores **218 m/s (mean combine),
   165 (clipped), 147 (median)** against the published RVs, from 511 at M12 baseline and
   382 at M12 best. An injection-recovery test returns **100% ± 5%** of a known signal —
   this improvement is not signal deletion (§3). Fitting the matched epochs at the published
   period returns **K = 304 ± 69 m/s against their K₁ = 306.0** (clipped combine): **the
   published orbit's amplitude now reproduces from raw archive data** (§4).
3. **The inference, re-run on the paper's own published table, no longer favours the second
   satellite.** The same code that reproduces the v1 comparison (+3.04 for two satellites,
   paper claimed 6.9) returns **−0.51 on the Nature table** (paper claims +2.62). The
   87.349 d period choice *does* reproduce — it beats 14/70/115 d in both tables. Only the
   evidence for its existence flips sign under the revision the authors themselves made (§5).

Two caveats stated up front. The model comparison uses this project's BIC/2 proxy with
periods fixed at the published values, not nested sampling — the sign flip is a proxy
result until someone runs the full evidence integral. And the per-epoch gap is *smaller*,
not closed: 147–218 m/s against their 57.68 claimed precision and the 91 m/s their own
table scatters about its orbit fit (§6).

---

## 0. What ran, and how to re-run it

All extraction happens in WSL `~/viper-src` (viper + cr2res products from M12 §9b).
Scripts live in [`scripts/injection/`](scripts/injection/):

| artifact | what it is |
|---|---|
| [`m13_batch.sh`](scripts/injection/m13_batch.sh) | builds the M13 template and all ten sweep runs |
| `M13tpl_tpl.fits` (WSL) | telluric-free template, all 21 segments, one `-createtpl -nocell -tpl_wave tell` iteration over all frames |
| `M13_A..J.rvo.dat` (WSL) | the sweep outputs |
| [`vs_published.py`](scripts/injection/vs_published.py) | the honest scorer: per-run rms vs the published Nature RVs |
| [`median_test.py`](scripts/injection/median_test.py) | mean / median / clipped-mean order combines, same metric |
| [`perorder_pub.py`](scripts/injection/perorder_pub.py) | per-order regression on the published series |
| [`berv_check.py`](scripts/injection/berv_check.py) | BERV-confound test + matched-epoch K fit (§4) |
| [`inject_generic.sh`](scripts/injection/inject_generic.sh) / [`inject_score2.py`](scripts/injection/inject_score2.py) | injection-recovery arm for any template+config (§3) |
| [`data/published/hoy2026_nature_table2_rvs.csv`](data/published/hoy2026_nature_table2_rvs.csv) | Nature Table 2, 23 epochs, provenance in header — the scoring truth |

The scoring truth is the **published Nature table**, per M12 §9b.4's rule: every internal
proxy this project has tried (epoch rms, A–B repeatability, GJ 229 B, anchor screens) has
been wrong by ≥6× at least once. `rms_pub` below is the rms of (ours − published) after
removing one constant offset; `slope` is the regression of ours on published (1 = we
transmit their signal at full amplitude).

```bash
# score any run:
cd ~/viper-src && ~/viperenv/bin/python .../scripts/injection/vs_published.py G=M13_G.rvo.dat
# injection-validate a config (18 single-epoch runs, ~4 min):
bash .../scripts/injection/inject_generic.sh G13 M13tpl_tpl.fits "4,7,8,9,10,12,13,14,17,18,19" -kapsig 3
~/viperenv/bin/python .../scripts/injection/inject_score2.py G13 M13_G.rvo.dat
```

## 1. The eleven orders are the H_C set

The paper says eleven orders were kept, selected for "sufficient telluric lines", and
names order numbers in figures — but viper's CRIRES+ order *numbering changed* in commit
`6e1b19c` (the inst_CRIRES.py order-mapping fix). The paper's run predates the fix, so its
labels must be mapped through the **pre-fix** numbering. Doing so yields:

```
H_C = oset 4,7,8,9,10,12,13,14,17,18,19    (post-fix / current numbering)
```

against the naive reading (`H_A = oset 2,5,6,7,8,10,11,12,15,16,17`). Three confirmations:

1. **Commit archaeology** — mapping the paper's order labels through the pre-`6e1b19c`
   numbering lands on `H_C`.
2. **Selection-criterion coherence** — `H_C` is what you get by excluding exactly the
   segments with ~zero telluric line density in viper's atmosphere model, i.e. the paper's
   own stated criterion actually produces this set.
3. **Empirical** — `H_C` beats `H_A` head-to-head on identical config: 535 vs 973 m/s epoch
   rms, 492 vs 680 m/s against the published RVs (runs B and C below).

## 2. The sweep

Ten configs, all on the M13 template, all scored per-epoch against the Nature table
(17 of 18 archive epochs match within 0.05 d; the standard combine is the mean over orders):

| run | config | rms_pub | slope | r_pub | Eq.(1) |
|---|---|---:|---:|---:|---:|
| A | `7:17` (M12's guess) | 611 | 0.07 ± 0.73 | 0.02 | 480 |
| B | `H_C` | 492 | 0.52 ± 0.61 | 0.22 | 448 |
| C | `H_A` | 680 | 0.75 ± 0.85 | 0.22 | 474 |
| D | all 21 segments | 538 | −0.27 ± 0.59 | −0.12 | 326 |
| E | `H_C -chunks 2` | 283 | 0.78 ± 0.35 | 0.49 | 437 |
| F | `H_C -telluric add2` | 493 | 0.52 ± 0.61 | 0.22 | 434 |
| **G** | **`H_C -kapsig 3`** | **218** | **0.82 ± 0.27** | **0.62** | **331** |
| H | `7:17 -chunks 2` (= M12 best) | 382 | 0.60 ± 0.47 | 0.31 | 521 |
| I | `H_C add2 -chunks 2` | 282 | 0.74 ± 0.35 | 0.48 | 426 |
| J | `H_C -deg_wave 3` | 411 | 0.26 ± 0.48 | 0.14 | 389 |

Run H reproduces M12's best (382) exactly — continuity holds. Aggressive spectral-fit
outlier rejection (`kapsig 3`) is worth more than any other single flag on the `H_C` set.

**Robust order combining is worth another ~50–70 m/s.** Across every run, replacing the
mean over orders with the median or a 3×MAD clipped mean improves the published-RV match:

| combine (run G) | rms_pub | slope |
|---|---:|---:|
| mean | 218 | 0.82 ± 0.27 |
| clipped mean | **165** | **0.95 ± 0.21** |
| median | **147** | 1.31 ± 0.17 |

Why: the eleven orders are **bimodal**. Per-order regression on the published series
([`perorder_pub.py`](scripts/injection/perorder_pub.py)) splits them cleanly —

```
transmitting:  o12 1.23±0.20   o13 1.91±0.27   o17 1.28±0.22   o14 1.40±0.62
overshooting:  o4  2.76±0.41   o18 2.10±0.53   o19 2.46±0.41
dead/anti:     o7 −0.69±1.03   o8 −0.42±0.64   o9 −1.71±1.27   o10 −1.25±0.95
```

The mean averages the dead orders in (slope 0.82 = the mean of ~0s and ~2s); the median
rides the transmitting half (its slope, 1.31, equals the median of the per-order slopes,
1.28). No order is selected by hand and nothing is tuned on the published values — the
median is blind to which orders agree with the paper.

## 3. The M9 screen: injection recovery passes at 100%

M9's lesson stands on file: the best-looking "improvement" this project ever produced
worked by deleting the signal. So the winning config was fed a known K = 1530 m/s
Keplerian at the published period, injected by shifting the *template* (M12 §8.1 — never
the observation), one shifted template per epoch, full viper re-run per epoch
([`inject_generic.sh`](scripts/injection/inject_generic.sh)):

```
G13: n=18  recovery = 100% ± 5%   resid_rms = 213 m/s
```

Per order: 83–128% everywhere except **o18 (8% ± 56%)** — the one genuine transmission
failure in the set (and a candidate to drop *on injection grounds*, which is legitimate;
dropping orders for disagreeing with the paper would not be). Note the cross-reading with
§2: **orders 7–10 transmit an injected signal at 83–103% yet anti-correlate with the
published series** — their defect is night-to-night systematics, not Doppler response.
The improvement chain mean → kapsig → robust combine does not suppress signal anywhere.

## 4. The published amplitude reproduces — and an overshoot hint that does not survive scrutiny

Fitting a circular orbit at the published two-satellite period (171.454 d) to the
**matched epochs only** ([`berv_check.py`](scripts/injection/berv_check.py)):

| series | K (m/s) | resid (m/s) |
|---|---:|---:|
| G, clipped mean | **304 ± 69** | 166 |
| G, median | 408 ± 62 | 147 |
| published table itself | 273 ± 30 | 91 |
| published K₁ (2-sat circular) | 306.0 | — |

**K = 304 ± 69 against 306.0**: the from-raw pipeline recovers the published orbit's
amplitude at the published period. That is the closest this project has come to an
end-to-end reproduction of the measurement.

The median series and the transmitting orders individually run *above* the published
amplitude (slopes 1.3–2.8 in §2), which would rhyme with M11 — their self-templating
recipe measurably absorbs signal amplitude, ours does not. **Do not claim this.** The
confound: over these 17 epochs, **corr(published RV, BERV) = −0.71** — the orbital phase
and the barycentric correction are strongly entangled in the actual sampling. Any
BERV-proportional systematic in our series therefore projects onto the published signal
and inflates slopes; and because of the same collinearity, *controlling* for BERV absorbs
real signal and deflates them (median slope 1.31 → 0.90 ± 0.19 under BERV control; o4,
o13, o19 stay ~2σ high at 1.7–2.4). With n = 17 the amplitude ratio and a BERV term
cannot be cleanly separated. Recorded as a hint, testable only with epochs where phase
and BERV decouple. The −0.71 itself is worth knowing: the published detection's epoch
sampling is not BERV-orthogonal either.

## 5. The second satellite does not survive its own revised table

`exosat-rv orbits` now takes `--version nature|v1`
([cli.py](src/exosat_rv/cli.py), [orbits.py](src/exosat_rv/analysis/orbits.py)) and fits
the corresponding published table with periods fixed at the published values, eccentric
1-sat vs circular 2-sat exactly as the paper's Table 1 pairs them. Same code, both tables:

```
v1 (20 epochs, 464.9 d, mean err 31.45):          Nature (23 epochs, 850.7 d, mean err 57.68):
1-sat ecc   BIC 227.19  e=0.35 K=291              1-sat ecc   BIC 264.20  e=0.39 K=351
2-sat +87.46d  proxy +3.04  (paper: 6.9)          2-sat +87.349d  proxy −0.51  (paper: +2.622)
best P2 = 87.46 d = paper's                       best P2 = 87.349 d = paper's
vs 115 d: +2.35 (paper: 2.6)                      vs 115 d: +3.02
```

Reading it: **M6's continuity holds** (v1 still prefers two satellites under the proxy,
as it did when M6 ran), the **period selection reproduces in both tables** (87 d beats
every alias), and the **existence evidence flips sign** on the corrected data. The paper's
own revision — 3 more epochs, corrected timestamps, errors nearly doubled — moved its
second satellite from "decisively favoured" (v1 proxy +3.04, claimed 6.9) to "slightly
disfavoured" (−0.51, claimed +2.62). The proxy tracked the paper's own numbers everywhere
it could be checked (2.35 vs 2.6 on the alias comparison), which makes its disagreement on
the one number that matters — +2.62 claimed, −0.51 measured — hard to dismiss as proxy
noise. A nested-sampling run on the Nature table is the natural next step; the author
query ([docs/author-query-draft.md](docs/author-query-draft.md)) stays polite about it.

## 6. What remains

- **Per-epoch precision is still 2.5–3.8× theirs**: 147–218 m/s against a claimed
  57.68 m/s, with the paper's own Eq. (1) statistic at 331 m/s on run G against their
  60.50. The floor is the night-to-night per-order drift (author query Q4) — unchanged
  from M12, just smaller.
- **The Eq. (1) gap and the rms_pub gap are now the same size** (~3×), which they were
  not before: the extraction is no longer dominated by removable configuration error.
- **o18 fails injection** (8% ± 56%) and can be dropped on injection grounds; o12's
  injection scatter (995 m/s) deserves a look.
- The K = 1530 m/s injection amplitude is 5× the published K₁. Recovery at ~306 m/s
  scale is untested (linearity assumed); an amplitude-matched arm is one command.

## 7. For the next agent

1. **Nested sampling on the Nature table** (dynesty/ultranest over the M6 model space) —
   turns §5's proxy flip into a checkable claim or kills it.
2. **The survey was the point.** The validated recipe — cr2res → M13 template → `H_C`-style
   telluric-selected orders → `kapsig 3` → median combine → injection-validated, scored
   against something external — is now transferable. The target class that survives the
   four-way conjunction (young, close-in 5–13 M_Jup companions with CRIRES+ H-band archives)
   is in the discovery notes; picking the first non-CD-35 target starts M14.
3. Amplitude-matched injection (≈300 m/s) to close §6's linearity assumption.
