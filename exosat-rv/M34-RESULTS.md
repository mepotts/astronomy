# M34 — Is the CD-35 detection an artefact of tuning the extraction on the published RVs?

> **Verdict: no — and the question splits in two, which the first draft of this document ran
> together.**
>
> **Is the METHOD overfitted? No.** The configuration transferred unmodified to nine further
> companions across three wavelength settings and both observing modes, none with a published
> velocity to tune against, at 99–101% injection recovery. A configuration fitted to one series
> would not survive that. The tuning is *calibration against the only external reference that
> exists in this class*, followed by demonstrated transfer where no reference exists — which is
> the ordinary way a pipeline of this kind is validated, not a defect in it.
>
> **Is this particular REPRODUCTION fully independent? Not quite**, and that is a narrower
> claim about one comparison rather than about the pipeline. Our agreement with H26's
> velocities is not independent evidence, because the configuration was fixed with those
> velocities in view. Everything downstream is independent, and §2 below bounds what the
> calibration could have bought: the period survives in configurations that agree *poorly*
> with the published series.
>
> The pipeline is also not a reconstruction of H26's procedure, which has never been
> published. It is a different route to the same quantity, and it does not need to match
> theirs in method for the two to be compared in result.

Matthew asked the sharpest question anyone has put to this work: *is our raw-to-RV pipeline
overfitted on Hoy et al.'s published RVs?*

He is right that there is something to ask about. The manuscript's own Table 1 says it
plainly — **"the scoring metric for every choice was the rms against the published RV
series"**. The extraction configuration (order set, template iteration, clipping,
oversampling) was chosen by minimising disagreement with their answer. Everything downstream
is blind: the period search never sees a published number, and its epoch screen is internal
and independently rediscovers the one epoch the published table omits. But the *input* to that
blind search was selected with their numbers in hand.

**So the honest statement is: the analysis is blind; the extraction is not.**

## 1. The test

A configuration sweep already existed on disk and had never been re-scored this way:
`M13_A`…`M13_J` and the `M14_*` variants, twenty-one complete RV series from the same spectra
under different configurations. For each, `scripts/injection/m34_overfit_test.py` computes two
numbers that had never been put side by side:

- **rms against the published series** — the metric that *selected* the adopted configuration
- **ΔBIC near 171 d** — the result that configuration was used to obtain

and asks whether the detection appears **only** in the configurations that best match Hoy.

If the signal lives only where agreement is best, better agreement is buying the detection and
the reproduction cannot be called independent. If it survives where agreement is poor, the
period is in the spectra.

Nothing is re-reduced. This re-scores runs that already exist, which is why the sharpest
question about the project could be answered in an afternoon.

## 2. Result

```
config         n  rms_pub   best P    dBIC   P@171    dBIC   rank
M13_A         18      279      6.3     8.3   166.6    -3.3   1253
M13_B         17      211    115.9    18.2   175.7   +17.1     32
M13_C         18      222    165.0    10.2   165.0   +10.2      1
M13_D         17      161      6.4    12.3   171.6    +9.5     16
M13_E         17      209    114.9    17.6   175.1   +11.8     83
M13_F         17      197    114.2    15.0   173.6   +14.9      7
M13_G         17      147    365.2     7.9   171.4    +2.8     31
M13_H         17      240      7.7     7.9   171.6    -0.3    354
M13_I         17      196    115.7    13.8   175.5    +9.4     85
M13_J         18      202      8.1     8.0   182.0    -1.6    894
M14_IPag      16      241      6.4     8.8   178.7    +3.1    111
M14_IPg       17      147    365.2     7.9   171.4    +2.8     31
M14_IPmcg     17      163      9.7    10.0   175.5    +2.4    144
M14_IPsg      17      226    116.8    13.5   178.5   +13.2     18
M14_NODALL    34      163     15.0     8.1   171.2    +4.4    126
M14_NODT2     34      141    171.2    43.8   171.2   +43.8      1
M14_T2        17      144    167.8    23.8   167.8   +23.8      1
M14_O2        17      133      8.5    10.5   171.4    +3.0     34
M14_O4        17      163    365.7     7.1   172.0    +4.9     10
M14_O8        18      180      8.0     5.5   182.0    -3.6   1348
M14_nod       10      200     77.2     1.1   182.0    +0.2   1554
```

**The machinery is verified against M14**: `M14_T2` returns ΔBIC **+23.8 at P = 167.8, rank 1**,
which is exactly what M14 §6 reported for that configuration. This test is therefore on the
same scale as the published claim, not a private one.

| quantity | value |
|---|---|
| configurations tested | 21 |
| rms against published | 133–279 m/s (factor 2.1) |
| ΔBIC near 171 d | −3.6 to +43.8 |
| **correlation(rms_pub, ΔBIC@171)** | **−0.31** |
| worst-matching half showing ΔBIC > 10 | **5 of 10** |

## 3. Reading it

**Half the configurations that match the published series *worse* than median still detect the
signal at ΔBIC > 10.** That is the finding. A period tuned into existence by an rms metric
would not survive in the configurations that score badly on that metric.

**The −0.31 correlation is weak and is expected even if the signal is entirely real.** Both
quantities improve with extraction fidelity: a better extraction agrees better with any
competent measurement of the same photons *and* recovers a real signal more strongly. A
positive association between the two is therefore the null expectation, not evidence of
circularity. What would have been damning is the signal *vanishing* off the best-matching
configurations, and it does not.

**A more careful reading of the ranks.** Only three configurations put ~171 d at rank 1
(`M13_C`, `M14_T2`, `M14_NODT2`). In most others the period is *present* at ΔBIC ≈ +3 to +17
but not dominant. That is what a real but marginal signal looks like when the extraction is
degraded: it survives, it weakens, and it stops being the top peak before it stops existing.
It is not what a manufactured signal looks like, which would be absent rather than merely
demoted.

**What this does not establish.** Every configuration in the sweep is drawn from a family that
was itself explored with the published series available, so this bounds the effect of choosing
*within* that family, not the effect of the family's boundaries. The fully independent
experiment — select a configuration by injection recovery alone, never computing rms against
the published series at any point, then run the blind search — has still not been done. It
requires re-running viper rather than re-scoring, and it remains the cleanest available
strengthening of the reproduction.

## 4. ⚠ The first version of this test said the opposite, and it was wrong

Round 1 announced *"the detection tracks the tuning metric… the reproduction cannot be claimed
as independent."* That would have been a false alarm on the project's central result, and it
was caught only because the adopted configuration came out at ΔBIC ≈ 0 where M14 had measured
+24.8. **A rank-1 peak carrying zero evidence is incoherent, and that incoherence is what
exposed the bug rather than any suspicion about the conclusion.**

The cause was that the period search had been **reimplemented here instead of imported**, for a
reason that does not survive inspection — "to avoid a dependency", when `blind_search.py` takes
a filename and there was no dependency to avoid. The reimplementation differed in two ways,
both of which crush the evidence toward zero:

| | this project | round 1 |
|---|---|---|
| order combine | **median across per-order RVs** | viper's own `RV` column |
| fit | **unweighted** | inverse-variance from `e_RV` |
| score | **BIC = n·log(RSS/n) + k·log(n)** | χ² + k·log(n) |

The `e_RV` column carries 400–1000 m/s against a true epoch precision of 70–90, so weighting by
it discards the signal.

The fix was to stop duplicating and start importing. `blind_search.py` cannot be imported —
it reads `sys.argv[1]` at module level — so the function's **source is extracted and executed**,
giving one definition and one behaviour, with a loud failure if it ever moves.

**The lesson is the one this project keeps paying for in a new costume.** Reimplementing a
reference computation "to keep things clean" is the same error class as re-typing a number
instead of citing it: it creates a second source of truth that can silently disagree with the
first. It nearly produced a retraction of a correct result.

## 5. What changed in the manuscript

The limitation is now stated in the paper rather than left implicit, together with this test.
A referee would have found the Table 1 sentence and asked exactly Matthew's question; better to
answer it in the text than in correspondence.
