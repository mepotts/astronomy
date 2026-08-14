# M29 — the YSES 1 b prize, opened and then rejected

Three things were attempted from `NEXT-DIRECTIONS.md`. One infrastructure defect was
found that had silently disabled the whole reduction toolchain. The headline is a
negative result reached by a rule fixed before the data was looked at.

---

## 1. The M26 blocker was one line in a log

YSES 1 b's 2022 pair has sat in the ledger since M26 as "blocked on an empty-extraction
cr2res issue". The cause, present in `nod.log` all along:

```
[ ERROR ] cr2res_obs_nodding: Require an even number of raw frames
[ ERROR ] cr2res_obs_nodding: Invalid Inputs
[WARNING] cr2res_obs_nodding: Failed to reduce detector 1, 2, 3
```

…after which cr2res wrote **all eleven products anyway, empty, and exited 0**. Every
check that looked at file existence passed it.

The 8-exposure template was **aborted after 7** — the archive holds seven too, so
nothing was lost in download — leaving 3 A and 4 B nod positions. Dropping the unpaired
B gives an even six and the night reduces normally: **1161 kB, 21 spectral columns, 18
non-empty**, matching the 2023 nights exactly, against 112 kB and zero columns before.

Three hypotheses were wrong first, each recorded because it cost a check: mixed
wavelength settings (no — all K2166 at DIT 450), bad calibrations (no — the trace-wave
products are structurally identical to the working night, 21 traces over 7 orders per
chip), and a lost download (no — the archive holds seven as well).

**Also settled:** `raw_m26/yses1a` and `yses1b` are byte-identical duplicates of one
night. The "4-night / 290-day prize" was always **3 nights** — one 2022, two 2023.

## 2. The reduction toolchain was entirely unrunnable

The first attempt at that reduction reported exit 0 and did nothing. Git runs
`core.autocrlf=true` here, so it rewrites shell scripts to CRLF on checkout, and WSL's
bash then fails on the carriage return — a bogus "No such file or directory" for the
sourced environment file, `$'\r': command not found`, and a syntax error, none of which
reach the exit status. **All 39 shell scripts were in that state**, so the whole cr2res
chain, and any fresh clone, was broken.

Fixed with `.gitattributes` pinning `*.sh`/`*.py`/`*.sof` to `eol=lf`. Diagnose with
`file script.sh` **from inside WSL** — a `grep $'\r'` from git-bash reports LF and will
mislead you (it did).

## 3. The screen, with the rule fixed in advance — and the rejection

The 3-night series ran cleanly through the pipeline (`m2x_run_target.sh`): template
ladder, RVs, both injection arms. **Gates pass: 98 ± 3% (K=1530) and 98 ± 4% (matched).**
The machinery transmits velocity correctly.

The series does not hold up. Per-frame, the 2022 epoch is about twice as noisy
internally as the 2023 nights (across-order spread 1300–1400 vs 630–770 m/s), and the
two order-combines disagree violently:

| | median-combine | mean-combine | disagreement |
|---|---:|---:|---:|
| unscreened, 18 orders | 356 m/s | 31 m/s | **11.6×** |
| screened, 10 orders | 270 m/s | 157 m/s | 1.7× |

Before running the screen, the decision rule was fixed and written down
(`m29_screen.py` docstring):

- **A** — most orders survive *and* combines converge → epoch usable
- **B** — most orders survive *and* combines still disagree → epoch bad as a whole
- **C** — the screen must drop ~half the orders to work → **selection, not repair;
  reject regardless of how good the survivor looks**

with "most" fixed at > 2/3 and "converge" at within 2×.

**The screen keeps 10 of 18 orders (56%) — and the combines then converge, 11.6× → 1.7×.**
That is branch **C**, and it is precisely the trap the pre-commitment existed for: the
convergence *looks* like a fix, and it was bought by discarding 44% of the orders. M9
recorded the same shape once already — the best-looking RV improvement worked by
deleting the signal.

**VERDICT: the 2022 epoch is rejected.** YSES 1 b remains a **two-night series at 34 m/s**.
The 290-day baseline does not exist in usable form. Note that even the screened series
sits at 157–270 m/s, nowhere near the 2023 pair's 34 m/s, so nothing of value was given
up by holding the line.

Also uninterpretable and worth not quoting: `r(RV, BERV) = −0.59` on this series. There
are only **two distinct BERV values** across all three nights (−0.30 and +18.54 km/s); a
correlation over two clusters is not a correlation.

**To revive the epoch:** new 2022-season data, or an independent reduction of that night
that survives the screen without a 44% cut. Not a software fix.

## 4. A1, the jitter floor — attempted, closed negative

Detail in `NEXT-DIRECTIONS.md` §A1. Both noise channels fail: within-night frame scatter
has too few degrees of freedom at ~2 frames/night (the built-in control settles it —
CD-35 2722 B, carrying a real signal, resolves at only 1.4σ), and across-order dispersion
reads 1333 m/s on CD-35 against a 272 m/s epoch scatter even after per-order centering,
because the per-epoch order distribution is heavy-tailed. β Pic b's known contamination
resolves at 2.1–2.2σ, so the machinery is sound; the excesses sought elsewhere are
simply below the available power.

**What it became:** the binding constraint on measuring companion RV jitter is **frames
per night, not nights** — campaigns take ~2, a decomposition needs 6–10. A cheap change
to any future OB. And one number is banked for Paper I: **η Tel B's 116–130 m/s epoch
scatter is fully accounted for by its own within-night measurement noise**, with no
astrophysical jitter required.

## 5. For the ledger

| item | before M29 | after M29 |
|---|---|---|
| YSES 1 b 2022 pair | "blocked on empty extraction; the queued prize" | **rejected** — aborted 7-frame template; reduces once even, fails the screen at 56% kept |
| YSES 1 b series | "4 nights / 290 d once unblocked" | **2 nights at 34 m/s**; `yses1a`/`yses1b` were duplicates |
| shell toolchain | assumed working | was **entirely CRLF-broken**; fixed |
| jitter floor | proposed as the top new idea | closed negative, with an observing-strategy result |

## 6. The contrast wall's x-axis — derived, then the derivation itself put in doubt

> ### ⚠ CORRECTION (same day, after the property audit)
>
> **§6 below over-claimed, and the over-claim is mine.** It states that the ledger's
> contrast figures are "wrong by one to two orders of magnitude". That conclusion rests
> entirely on the companion-magnitude column of Lazzoni et al. 2022 Table 1 — transcribed
> into `data/m7-survey.json` as `k_mag`, and labelled **`Kp`** in `survey.py`'s own
> provenance comment. The band and photometric system of that column were never
> established, and the property audit found it fails a physical check:
>
> - SIMBAD gives **η Tel B: H = 11.93** (verified directly). Lazzoni's Kp for the same
>   object is **13.2**, which implies **H − K = −1.27** — K fainter than H. Late-M and L
>   dwarfs are red; H − K is positive. One of the two numbers is not what it is labelled.
> - The same doubt reaches β Pic b, whose Kp of 14.9 sits ~2.4 mag fainter than the K
>   magnitude commonly published for it. Were its true K ≈ 12.5, its contrast would be
>   ~4000× rather than 36 983× — **close to the ~5000× the ledger asserted all along.**
>
> **So the honest state of the contrast axis is: unresolved.** Two things are established
> and survive. The ledger's figures were never derived anywhere in this repository — that
> remains true and was worth finding. And deriving them from the only table available
> gives numbers that disagree with the ledger. What is *not* established is which set is
> right, because the input column fails its own consistency check.
>
> The host-magnitude column is not in doubt: 3.480 (β Pic), 5.010 (η Tel), 8.542 (PDS 70)
> match published K magnitudes exactly. The problem is confined to the companion column.
>
> **Consequence.** `docs/paper/contrast-wall-note.md` was rebuilt on the derived values
> and must now say the axis is unresolved rather than corrected. Nothing about the
> *mechanism* changes — contamination rather than photon noise, β Pic b's r(BERV) = +0.88
> at 99–100% injection transmission, the CD-35 slit-function bound, and the separation
> axis being independent are all measured here and use no contrast figure at all.
>
> ### ⚠⚠ SECOND CORRECTION — the retraction above was itself too broad
>
> `langlois2021b_shine2` and `bohn2020_tyc8998` are now archived in `papers/`, and Bohn
> settles the central question. Its Table 2 for TYC 8998-760-1 (= YSES 1) gives, per
> filter, the **host magnitude** and the **contrast**: `K1 | 8.31 | 10.03 ± 0.04`. The
> middle column falls from 12.25 (J3) to 9.57 (K2) to 8.02 (L') while the host column
> stays near 8.3 — the signature of a contrast for a red companion, not an apparent
> magnitude. So Bohn gives YSES 1 b an apparent K1 of **8.31 + 10.03 = 18.34**.
>
> **`m7-survey.json` carries `k_mag = 18.2` for that object.** The two agree to
> **0.14 mag**, from wholly independent routes.
>
> **Therefore Lazzoni's `Kp` column IS companion apparent magnitude, and it is
> corroborated.** The derivation method in §6 was correct, and the doubt cast on it above
> was over-broad. What remains genuinely unresolved is narrower:
>
> - **β Pic b**: `Kp = 14.9` against a K commonly published nearer 12.5. A 2.4 mag gap no
>   archived source settles. Its contrast is either ~37 000× or ~4000×.
> - **η Tel B**: `Kp = 13.2` against SIMBAD's `H = 11.93`. Note this is the weaker of the
>   two claims — SIMBAD photometry for companions a few arcsec from bright stars is often
>   contaminated or mis-associated, and Lazzoni's column has just been independently
>   validated elsewhere. Both need their discovery-paper photometry.
>
> ### The contrast axis, as it now stands
>
> | system | sep | contrast | sourcing | extraction |
> |---|---|---:|---|---|
> | CD-35 2722 B | 2.8″ | 97× | Lazzoni column, host K verified | clean |
> | PDS 70 | 0.17″ | 460× | same | star dominates |
> | **YSES 1 b** | **1.7″** | **~10 000×** | **Bohn 2020 directly — best-sourced point here** | **clean, 34 m/s** |
> | β Pic b | 0.51″ | 4000× or 37 000× | disputed | flooded |
>
> **YSES 1 b is the most valuable new point**, and it partly fills the gap §6 called
> unsampled: extraction is *clean* at ~10 000×, on the campaign's best per-epoch
> precision. The unsampled interval narrows from roughly 1900–37 000× (a factor of 20) to
> **10 000–37 000× — a factor of under four**, and collapses further if β Pic b's lower
> value is the right one.
>
> **Two flip-flops on this axis are enough. The stable statement is:** the derivation
> method is sound and the column is the right quantity; one point is independently
> confirmed; two remain disputed pending discovery-paper photometry; and no claim about
> where the wall sits should be made in print until β Pic b is settled, because it is the
> sole anchor of the flooded end.
>
> ### ✅ CLOSED — and the wall is misnamed
>
> β Pic b is settled from the primary source. Bonnefoy et al. 2014 states that β Pic b's
> Ks photometry comes from **Currie et al. 2013**; that paper (now archived,
> arXiv:1306.0610) gives **Gemini/NICI Ks = 12.47 ± 0.13**. With the host at K = 3.48,
> Δmag = 8.99 → contrast **≈ 3950×**.
>
> **So Lazzoni's Kp = 14.9 is wrong for β Pic b, and the ledger's asserted "~5000×" was
> approximately right all along.** My derived 36 983× was the error. The Kp column is
> apparent magnitude (validated on YSES 1 b to 0.14 mag) but it is not uniformly reliable:
> right for YSES 1 b, wrong by 2.4 mag for β Pic b.
>
> #### The finding this exposes
>
> With every point sourced or flagged, the outcomes order like this:
>
> | separation | contrast | extraction | system |
> |---:|---:|---|---|
> | 0.17″ | 460× | **fails** | PDS 70 b |
> | 0.51″ | 3 950× | **fails** | β Pic b |
> | 1.70″ | 10 280× | clean, 34 m/s | YSES 1 b |
> | 2.80″ | 97× | clean, 70–90 m/s | CD-35 2722 B |
> | 4.21″ | 1 888× | clean, 116–130 m/s | η Tel B |
>
> **Sorted by separation the column reads fails, fails, clean, clean, clean — perfectly
> monotonic. Sorted by contrast it reads clean, fails, clean, fails, clean — it alternates,
> and predicts nothing.**
>
> The decisive pair is YSES 1 b against β Pic b: **YSES 1 b extracts cleanly at 10 280×
> while β Pic b floods at 3950×.** A target 2.6× harder in contrast is clean, because it
> sits 3.3× further out. No contrast threshold can separate this set; separation separates
> it completely.
>
> **The "contrast wall" is misnamed.** On this evidence the binding axis is angular
> separation — consistent with the physical mechanism already measured, which is that
> starlight enters the *slit*, a geometric aperture, and pervades the band rather than
> concentrating in any order subset (M20 §2, three-pass template ladder, r(BERV) = +0.88
> unchanged after masking).
>
> **The one potential counterexample:** HIP 81208 B is reported clean at 0.3″, which would
> break the ordering. Its separation is **UNSOURCED** (property audit) and must be settled
> before this is written up. If it holds, the rule is not separation alone either.
>
> **Consequence:** `docs/paper/contrast-wall-note.md` needs a third revision — not to fix a
> number, but because its organising axis is the wrong one. That is a better paper than the
> one it replaces, and it is the sort of conclusion only reachable once the numbers have
> sources.

> **Closed:** Lazzoni's sources are now archived (Langlois 2021b, Bohn 2020, Currie 2013,
> Bonnefoy 2014, Viswanath 2023).

## 7. It is neither axis: the binding quantity is scattered host flux

HIP 81208 B's separation is now sourced — Viswanath et al. 2023 gives **320.9 ± 1.0 and
328.7 ± 1.0 mas** over two epochs, and its K2 contrast **Δmag = 6.64 → 457×**. That was the
counterexample flagged in §6, and it holds: HIP 81208 B extracts **cleanly at 124 m/s from
0.325″**, while β Pic b floods at 0.51″.

So separation alone does not order the outcomes either. With all six systems sourced:

| axis, ascending | sequence | orders the outcomes? |
|---|---|---|
| contrast | C C **F** C **F** C | no |
| separation | **F** C **F** C C C | no |

**There is a physical reason to expect neither to work.** What floods the slit is not the
magnitude ratio between host and companion — it is the host's light *scattered to the
companion's position*. That scales as contrast × PSF(θ), and for a seeing- or AO-limited
halo the wing falls roughly as θ⁻² to θ⁻³. The natural quantity is therefore

    S = contrast / θⁿ

which is, to a constant, **the ratio of scattered host flux to companion flux at the slit**.

`scripts/m29_wallaxis.py` tests it. The exponent is **not fitted** — it is scanned across
the physically plausible range and the whole range reported:

| n | highest CLEAN | lowest FAILS | gap | separates |
|---:|---:|---:|---:|---|
| 1.0 | 6047 | 2706 | — | no |
| **2.0** | **4327** | **15202** | **3.5×** | **yes** |
| 3.0 | 13313 | 29808 | 2.2× | yes |
| 4.0 | 40962 | 58446 | 1.4× | yes |

**S separates the two classes for n = 1.5–4.0, most cleanly at n = 2** — squarely inside
the θ⁻²–θ⁻³ falloff a halo actually has. Ordered by S at n = 2:

| S | outcome | system |
|---:|---|---|
| 12 | clean | CD-35 2722 B |
| 107 | clean | η Tel B |
| 3 557 | clean, 34 m/s | YSES 1 b |
| 4 327 | clean, 124 m/s | HIP 81208 B |
| 15 202 | **fails** | β Pic b |
| 15 917 | **fails** | PDS 70 b |

### How much to claim

Not much yet, and the caveats are in the script rather than only here.

- **Six points and two classes.** Many statistics separate such a set by chance. What
  makes this more than curve-fitting is that the exponent was chosen by physics and then
  scanned, not tuned to the answer — and that the two single-axis alternatives both fail
  outright.
- **PDS 70 b may fail for a different reason.** At 0.17″ the companion sits inside the AO
  core; the host is not a halo there, it is the spectrum. Dropping it does not change the
  separation.
- **η Tel B's contrast is disputed** (Lazzoni Kp 13.2 vs SIMBAD H 11.93). It is a clean
  case at wide separation, so it is not load-bearing; dropping it also does not change the
  separation.
- Dropping both still leaves clean at 12 and 3557 against fails at 15 202.

### What this means for the papers

The "contrast wall" is not merely mis-located, it is **the wrong variable**, and so is
separation. `docs/paper/contrast-wall-note.md` needs rebuilding a third time around
S = contrast/θ², and it becomes a better paper for it: a one-parameter, physically
motivated feasibility criterion that a proposer can evaluate for any target from two
catalogue numbers, in place of a threshold this project could never locate.

It is also **falsifiable and cheap to test**: any archival companion with a measured
separation and contrast predicts its own extraction quality before a single frame is
reduced. That is the experiment the next campaign should run. Adding **Langlois et al. 2021b**
> (η Tel B, AB Pic b) and **Bohn et al. 2020** (YSES 1 b) to `papers/` would settle the
> companion magnitudes for four of the load-bearing systems.
>
> One genuinely good thing came out of the audit: **Lazzoni Table 1 also carries `Sep` in
> mas and the host K for all 37 companions**, and the project never transcribed those
> columns. Every arcsec separation quoted here could have been read off disk — η Tel B
> 4210 mas, PDS 70 b 173.5, β Pic b **510.8 (0.51″, not 0.55″)**, 51 Eri b **434 (0.43″)**,
> AB Pic b **5400 (5.4″)**, which this project had left blank.

*The original §6 follows, unaltered:*

### The derivation as first reported

`scripts/m29_contrast.py` computes what nothing in this repository ever did:
contrast = 10^(0.4 (m_comp - m_host)), companion K from `data/m7-survey.json`, host
magnitudes queried live from SIMBAD.

| companion | sep (") | K_comp | host K | dmag | **derived contrast** | wall said |
|---|---:|---:|---:|---:|---:|---|
| CD-35 2722 B | 2.8 | 12.01 | 7.05 | 4.96 | **97x** | clean, ">= 2000x" |
| AB Pic b | — | 15.10 | 6.98 | 8.12 | **1768x** | clean |
| eta Tel B | 4.2 | 13.20 | 5.01 | 8.19 | **1888x** | clean |
| PDS 70 b/c | 0.17 / 0.24 | 15.20 | 8.54 | 6.66 | **460x** | "the star IS the spectrum" |
| beta Pic b | 0.55 | 14.90 | 3.48 | 11.42 | **36983x** | flooded, "~5000x" |

**The quoted figures are wrong by one to two orders of magnitude.** CD-35 2722 B, grouped
under "clean at >= 2000x", is a 97x target — twenty times easier than advertised. beta Pic
b, the flooded case quoted at ~5000x, is **37000x** — seven times harder. Both rest on
well-measured 2MASS magnitudes on bright hosts, so these are not marginal corrections.

**What the wall actually says, restated honestly:**

- **clean is measured up to ~1900x** (eta Tel B at 4.2", AB Pic b) — and at 97x (CD-35);
- **flooded is measured at ~37000x** (beta Pic b at 0.55");
- **the transition is bracketed by a factor of ~20 and contains no measured point.**

That is a weaker claim than the ledger's, and a better-defined one. The wall exists; its
location is known only to within a decade and a half, and the campaign never sampled the
gap. Separately, PDS 70 at **460x** — an easy contrast — is unusable at 0.17", which shows
separation limits the method independently of contrast. A wall stated in contrast alone
was always going to mislead, and HIP 81208 B (clean at 0.3" from a B9 host) is the
matching counterexample from the other side.

**Caveats, all material:**
- Several campaigns observed in **H1567, not K**; a K-band ratio approximates the contrast
  that applied at the slit, since the companion's H-K colour differs from its host's.
- Only six systems resolve. HIP 65426 b, HD 1160 B, AF Lep b, YSES 1 b, HIP 81208 B and
  HD 19467 B are absent from M7's magnitude table or unresolved at SIMBAD.
- **51 Eri b is excluded**: its K = 21.0 is flagged by M7 itself as "no measured K —
  upper limit only, unrankable". Using it would have produced a spurious 3.8-million-x
  point, which is exactly how the "gone at ~30000x" figure could have been defended.

**Consequence:** `docs/paper/contrast-wall-note.md` is drafted against the old numbers and
must be revised before it goes anywhere. Its own pre-submission list already flagged that
the ratios had no derivation; the derivation now exists and disagrees.

## 8. Testing S on held-out systems — and why it barely counts

`scripts/m29_wallpredict.py` parses **31 of Lazzoni's 37 companions** (Sep in mas, host
and companion magnitudes) and applies S with the thresholds **fixed in advance** from the
construction set: CLEAN below 4327, FAILS above 15 202. Where a primary source exists it
overrides Lazzoni — β Pic b uses Currie+2013 (3954×), not Lazzoni's 36 983×.

| system | sep | contrast | S | predicted | observed | role |
|---|---:|---:|---:|---|---|---|
| GSC 6214-210 B | 2.21″ | 182× | 37 | clean | *no data* | held out |
| CT Cha b | 2.68″ | 285× | 40 | clean | **clean** | **held out ✓** |
| DH Tau B | 2.35″ | 224× | 41 | clean | *no data* | held out |
| AB Pic b | 5.40″ | 1768× | 61 | clean | **clean** | **held out ✓** |
| η Tel B | 4.21″ | 1888× | 107 | clean | clean | built-on |
| 1RXS J1609 b | 2.22″ | 1562× | 318 | clean | *no data* | held out |
| PDS 70 b | 0.17″ | 460× | 15 297 | fails | fails | built-on |
| β Pic b | 0.51″ | 3954× | 15 154 | *indeterminate* | fails | built-on |

**Four agree, none disagree — and it barely counts.** The script says so in its own output
rather than only here:

1. **Only two systems were genuinely held out**, CT Cha b and AB Pic b, both CLEAN, both
   sitting **50–100× below** the clean threshold. Predicting "clean" for a target two
   orders below the boundary is not a discriminating test.
2. **There is no held-out FAILS case at all.** S has never been asked to predict a failure
   it did not already know about.
3. **β Pic b at its sourced contrast lands *on* the threshold** (15 154 vs 15 202) — of
   course it does, the threshold was set by β Pic b. Correcting its contrast from
   Lazzoni's bad 36 983× to Currie's 3954× collapsed the failure side onto two points 1%
   apart, and one of those (PDS 70 b, inside the AO core) may fail by a different
   mechanism entirely.

**The honest statement: S is consistent with every outcome this project has measured, and
is not yet tested by any of them.** The informative experiment needs a target with S
between 4327 and 15 202 — precisely the interval where nothing has been observed. That is
the same gap §6 identified on the contrast axis, and it has survived every reframing:
whatever variable is used, this campaign never sampled the transition.

**Three falsifiable predictions** for systems with archival data but no reduction here:
DH Tau B (S = 41), GSC 6214-210 B (S = 37), 1RXS J160929.1-210524 b (S = 318) — all
predicted CLEAN. They are weak tests for the same reason, but they are on the record
before the fact, which is the only way this stops being curve-fitting.

## 9. The decisive test does NOT exist: HD 4747 B is unresolvable in the archival data

> **⚠ This section originally claimed HD 4747 B was the experiment that decides S. It is
> not. Reducing the data settled it, and the original text is kept below for the record.**

**What the reduction showed.** The H-band night reduced cleanly — 24 of 24 spectral columns
non-empty, median flux 65 000, using the new per-setting SOF split (the night is four
settings × 2 frames: H1582, H1559, K2192, K2148). But the extraction is of **HD 4747 A**,
not B:

- `OBJECT` and `OBS TARG NAME` are both **`HD  4747`** — the host.
- `POSANG = 0.0`, so the slit runs N–S. HD 4747 B lies at PA ≈ 180°, so the geometry *is*
  right — the companion is along the slit, exactly as CD-35's 153.1° aligned on its own
  binary axis. That part was not the problem.
- **The slit function at 0.59″ from the peak sits at 0.75 of the primary's peak height**
  (median over 38 order-sides; 90th pct 0.77). That is not a companion trace. It is the
  primary's own PSF wing. Seeing on the night ran 0.86–1.31″, so a companion at 0.59″ is
  well inside the host's seeing disk.

**HD 4747 B cannot be separated from its host in this data, so it does not test S.** The
interval 4327 < S < 15 202 remains entirely unobserved.

**What this does establish, and it is not nothing.** There is a geometric floor sitting
underneath the whole S discussion that no flux ratio can describe: **if the companion is
not spatially resolved from its host, there is no companion spectrum to extract at any
contrast.** HD 4747 B at 0.59″ under ~1″ seeing is the first direct measurement of that
floor in this project — a slit-function profile showing the two objects blended rather
than an inference from a failed extraction.

**Why this does not simply reduce to "separation wins".** HIP 81208 B is *clean* at 0.325″,
closer than both HD 4747 B (0.59″, unresolvable) and β Pic b (0.51″, flooded). Whatever
separates those cases is not raw separation, and is not seeing alone either — AO
performance depends on the guide star, and HIP 81208 is a bright B9. Establishing that
would need the AO-corrected PSF core per observation, which is a real piece of work and is
not attempted here.

**Consequence for the wall paper.** Its §5.4 must now say the untested interval has been
*searched* as well as identified: of the four systems in it, κ And b is unobservable from
Paranal, PDS 70 c shares frames with PDS 70 b inside the AO core, β Pic b sets the
threshold, and **HD 4747 B's archival data cannot resolve the companion**. There is no
archival test available. The criterion must be published as a hypothesis with
pre-registered predictions, or wait for new observations.

---

*The original §9, written before the reduction and wrong in its conclusion:*

### The decisive test exists, and it is public: HD 4747 B

§8 concluded that S is untested because nothing has been observed with
4327 < S < 15 202. Searching all 31 companions parsed from Lazzoni Table 1 for that
interval — which took one query once the table was finally parsed — returns **four
systems, three of them new**:

| system | S | sep | contrast | archive |
|---|---:|---:|---:|---|
| **HD 4747 B** | **5 974** | 0.590″ | 2 080× | **27 public CRIRES+ frames, 3 nights** |
| κ And b | 8 859 | 0.876″ | 6 792× | none — dec +44°, unobservable from Paranal |
| PDS 70 c | 10 130 | 0.213″ | 460× | same frames as PDS 70 b; inside the AO core |
| β Pic b | 15 154 | 0.511″ | 3 954× | the threshold-setter, not a test |

**HD 4747 B is the experiment.** Verified against the ESO archive:

- **19 H-band nodding frames**, `W_0.2` slit, `CRIRES_spec_obs_AutoNodOnSlit` — the same
  grating and slit as CD-35 2722 B and η Tel B, so the existing order maps and the whole
  `m2x_run_target.sh` chain apply unchanged.
- **Three nights**: 2022-11-07 (4), 2022-12-23 (8), 2023-11-20 (15, programme 112.25FU.001),
  spanning about a year. Plus 8 pre-upgrade CRIRES frames from 2012, a different instrument.
- **All public** — released 2023-11-07, 2023-12-23 and 2024-11-20.
- Seeing on those nights ran 0.86–1.31″, against a companion at 0.59″: the companion sits
  **inside the seeing disk**, which is precisely the regime the criterion is about.

**Why this single reduction is worth more than the rest of the wall paper.** S is currently
built on six points, thresholded by one of them, with no held-out failure. HD 4747 B sits
at 5974 — in the middle of the interval no one has sampled — and its outcome is a genuine
two-sided test:

- **If it extracts cleanly**, the clean ceiling moves from 4327 to ≥ 5974 and the untested
  interval narrows by a third.
- **If it floods**, the failure floor drops from 15 202 to ≤ 5974, the interval narrows to
  4327–5974, and — more importantly — **S survives its first real opportunity to fail.**
- **If it is marginal**, that locates the transition rather than bracketing it, which is
  the one thing four milestones of "contrast wall" work never achieved.

Either way it is the first observation ever made inside the interval, and it costs one
download and one pass of an existing pipeline.

**Status: not yet reduced.** Disk headroom is ~7 GB, and 19 frames plus calibrations and a
reduction fit. This is the top of the queue — ahead of the wall paper's submission, which
should wait for it, and ahead of everything in `NEXT-DIRECTIONS.md`.

## 10. The variable is resolution, not contrast — and the threshold is not fitted

§9 left the open question: HIP 81208 B is CLEAN at 0.325″, closer than β Pic b (0.51″,
flooded) and HD 4747 B (0.59″, unresolvable). No function of contrast and separation
explains that ordering, and I said it would need the AO-corrected PSF per observation.

**That is measurable from data already on disk.** The nodding slit function *is* the
spatial profile along the slit; its FWHM is the delivered PSF for that observation, after
AO, seeing and instrument. `scripts/m29_psf.py` measures it per order per night and forms

    R = separation / PSF_FWHM

the number of resolution elements between companion and host.

| target | sep (″) | delivered PSF (″) | orders | **R** | outcome |
|---|---:|---:|---:|---:|---|
| HD 4747 B | 0.590 | 1.514 | 15 | **0.39** | unresolved |
| β Pic b | 0.511 | 0.952 | 114 | **0.54** | flooded |
| HIP 81208 B | 0.325 | **0.246** | 32 | **1.32** | clean, 124 m/s |
| YSES 1 b | 1.698 | 1.197 | 24 | **1.42** | clean, 34 m/s |
| CD-35 2722 B | 2.800 | 0.263 | 283 | **10.64** | clean, 70–90 m/s |
| η Tel B | 4.210 | 0.374 | 367 | **11.26** | clean, 116–130 m/s |

**R orders every outcome, and it separates at R ≈ 1.** Lowest clean is 1.32; highest
non-clean is 0.54.

**HIP 81208 B was never an anomaly.** It is clean at 0.325″ because its AO delivered a
**0.246″** PSF — a bright B9 guide star — while β Pic b's nights delivered **0.952″**,
nearly four times worse. Once the delivered resolution is measured rather than assumed,
the ordering is trivial.

### Why this is a better result than S = contrast/θ²

**The threshold is not a free parameter.** S needed an exponent (chosen from physics, then
scanned) and a threshold read off the data, which is why §8 concluded it was consistent
with the outcomes but untested by them. R ≈ 1 is where two point sources merge. Nothing
was fitted; the number was predicted by optics before the measurement.

**It uses no external catalogue.** Every input is measured from the project's own reduced
frames. The contrast axis needed Lazzoni's magnitudes, which cost two reversals and are
still disputed for η Tel B.

**It explains the failures mechanistically rather than ranking them.** At R < 1 there is
no companion spectrum to extract at any contrast — the objects are one source. At R ≈ 0.5
the pair is partially blended and host light dominates the extraction, which is exactly
β Pic b's pervasive, mask-proof r(BERV) = +0.88.

The coherent picture is therefore **two gates in series, not one axis**: R decides whether
a companion spectrum exists at all, and only within the resolved regime does contrast
govern how much host light contaminates it. That subsumes the contrast wall rather than
contradicting it — and it explains why four milestones of work could never locate a
contrast threshold. There isn't one to locate until R > 1.

### What this does not establish

- **Six points again**, and four are clean. R separates them, but so would other monotone
  functions; the argument for R is that its threshold was not chosen from the data.
- **PDS 70 returns no measurement** — its H-band nights were never reduced (blocked on the
  order-mapping quirk), so the one case that plausibly fails by a *different* mechanism is
  absent from the table.
- **The slit function is fitted for the brightest trace** — the companion when it is
  observed alone, the host when the pair is blended. The width is the delivered resolution
  either way, which is what R needs, but the two cases are not identical measurements.
- **Order counts vary 15–367.** HD 4747 B's PSF rests on 15 order-profiles from one night.
- R was formed *after* seeing the outcomes. It is a better-motivated hypothesis than S,
  not a validated criterion. The honest test remains a target predicted before reduction.

### ⚠ HELD-OUT TEST: R ≈ 1 IS FALSIFIED

Two reductions on disk carried M26 verdicts that were **not** used to form R. Testing
against them was the obvious next step and it damages the claim.

**HD 206893 B** — semi-major axis 9 au (Kral+2026) at parallax 24.5252 mas → 40.77 pc,
so 0.221″; measured PSF **0.393″** over 11 order-profiles; **R = 0.56**; verdict **CLEAN**.

That is *below* the R ≈ 1 threshold, and it lands between two failures (HD 4747 B at 0.39,
β Pic b at 0.54). The script still reports "separates: True", but only because 0.56 exceeds
0.54 — a margin of 0.02 in R, which is not a separation, it is a coincidence.

**So the part of §10 that made R better than S is gone.** The advantage claimed was that
R ≈ 1 is predicted by optics rather than read off the data. A clean case at R = 0.56
refutes that threshold. What survives is only that R happens to order these seven points,
with a 4% margin — the same "consistent with, untested by" status §8 assigned to S, and on
a narrower margin.

**Two caveats that cut both ways, stated because neither rescues the claim by itself:**

- **The separation input is wrong in kind.** I used a *semi-major axis* where every other
  row uses a *projected separation*. For an eccentric or inclined orbit those differ, and
  the projected separation at the observed epoch could be well below 0.221″ — which would
  lower R further, not raise it. Getting this right needs the astrometry at that epoch, not
  the orbit.
- **HD 206893 B's verdict is the weakest in the table.** It is "clean epochs banked" from a
  single K night — not an injection-gated null over a series like η Tel B, nor a detection
  like CD-35. A single clean-looking night is a much softer claim than the others.

**Honest status: R is a better-motivated hypothesis than S and is not established either.**
Both order the measured outcomes; neither has survived a test that could have refuted it,
and R has now nearly failed one. The two-gate physical picture (resolution first, then
contrast) remains the most coherent reading, but the *threshold* in either variable is
unlocated.

### Consequence

`docs/paper/contrast-wall-note.md` should lead with R and demote S to the
within-resolved-regime question. The paper's title is already "the wall is not a contrast
wall"; this says what it is instead, with a threshold that was not tuned.

## 11. Both candidate variables are dead: HD 206893 B kills S and R together

§10 flagged that HD 206893 B's separation was wrong *in kind* — a semi-major axis where
every other row uses a projected separation — and predicted that fixing it "would lower R
rather than raise it". Kral+2026's GRAVITY astrometry table gives the projected separation
directly, ΔRA and ΔDec per epoch:

| GRAVITY MJD | projected sep |
|---|---:|
| 59453.093 | 206.8 mas |
| **59534.021 — the CRIRES epoch** | **205.2 mas (interpolated, 12% between)** |
| 60127.218 | 193.1 mas |

**R = 0.205 / 0.393 = 0.52**, against β Pic b **FLOODED at R = 0.54**. A clean case now sits
*below* a flooded one. **R does not order the outcomes.** The prediction that the correct
input would make it worse was right.

**And the same point kills S.** SIMBAD carries both magnitudes: host H = 5.687,
companion H = 16.79, so Δmag = 11.10 and contrast = **27 618×** in H.

    S = 27 618 / 0.205² = 655 912

against thresholds of CLEAN < 4327 and FAILS > 15 202, with β Pic b flooding at 15 154.
**HD 206893 B is clean at 43× the S of the flooded case.** Even the conservative variant —
converting to a K-band contrast with an L-dwarf colour of H−K ≈ 1.2, giving ~9970× — leaves
S = 236 835, still **16× above** the failure threshold. This is not a marginal miss.

### Where that leaves the feasibility question

Four framings, each replacing the last, all now tested against the same data:

| variable | status |
|---|---|
| contrast alone | fails — clean at 97× and 10 280×, floods at 3950× |
| separation alone | fails — clean at 0.325″, floods at 0.51″ |
| S = contrast/θ² | **falsified** — HD 206893 B clean at 43× the flooded case |
| R = sep/PSF | **falsified** — HD 206893 B clean at R below the flooded case |

**No single-parameter combination of contrast and separation orders these outcomes.** That
is a clean negative result, it is well sourced, and it is more defensible than any of the
four positive claims I attempted today.

### The caveat that could rescue everything, and why it should be checked first

**HD 206893 B's verdict is by some distance the weakest in the table.** M26 records "clean
data both settings, gates 100–102%, epochs banked" — a single night per setting with
passing injection gates, not an injection-calibrated null over a series like η Tel B, nor a
detection like CD-35. If that night is clean because the *host* was extracted rather than
the companion — the HD 4747 B failure mode, which was only caught by reading the slit
function — then this data point is not a companion measurement at all and both refutations
collapse.

At 0.205″ separation with a 0.393″ delivered PSF, R = 0.52 means **the pair is blended**,
exactly as HD 4747 B was at R = 0.39. That is strong prior reason to suspect the same
thing. Checking it costs one slit-function scan of the kind §9 ran on HD 4747 B, and it
should happen before any of §11 is written up.

### ✓ THE CHECK WAS RUN IMMEDIATELY, AND IT VOIDS THE REFUTATION

HD 206893 B's slit function at 0.205″ sits at **0.598 of the peak height** (median over 31
order-sides) — essentially the HD 4747 B signature of 0.75, and nothing like the ≪0.1 a
resolved faint companion would give. **The pair is blended, and the extraction is of the
host.**

So HD 206893 B is not a companion measurement, cannot refute S or R, and §11's two
refutations are withdrawn. **S and R return to "untested", not "falsified".**

### The structural result underneath all of this

Three systems have now been checked for blending by reading the slit function rather than
trusting the extraction:

| system | sep | delivered PSF | R | profile at the companion | state |
|---|---:|---:|---:|---:|---|
| HD 4747 B | 0.590″ | 1.514″ | 0.39 | 0.75 of peak | blended |
| HD 206893 B | 0.205″ | 0.393″ | 0.52 | 0.60 of peak | blended |
| β Pic b | 0.511″ | 0.952″ | 0.54 | — (km/s, r(BERV)=+0.88) | flooded |

versus the clean cases, all at R ≥ 1.32.

**Every system in the regime where the criterion would be tested is blended — and that is
not a coincidence, it is the same fact stated twice.** Being close enough to have an
interesting S or R is exactly what makes a companion unresolvable from its host. The
untested interval is not merely unobserved; with slit spectroscopy it may be
*unobservable*, because below R ≈ 1 there is no companion spectrum to extract at any
contrast.

**This is the strongest conclusion available from the day's work, and it is a negative
one.** It also converts the project's existing instrument recommendation from a preference
into a requirement: fiber-fed starlight suppression (HiRISE, KPIC) is not a way to do this
*better* in the close regime — it is the only way to do it *at all*, because the slit
cannot deliver a companion spectrum there to be limited by contrast in the first place.

**Two verdicts in the ledger need re-examining on this basis.** HD 206893 B is recorded in
M26 as "clean data both settings, gates 100–102%" and 2M0103AB b as "within-night pair
agrees at ~53 m/s, gates 100±0%". Passing injection gates does not distinguish a companion
spectrum from a host spectrum — the gate measures whether the *fitter* transmits velocity,
and it transmits just as well on a bright host. Any verdict from a blended pair is a
statement about the host. That check is one slit-function scan per target and it should be
run across the roster.
## 12. The roster blending sweep - one verdict withdrawn, two unclassifiable

`scripts/m29_blend.py` applies section 11's test to every target with a reduction on disk.
Both quantities come from the same slit function and share no arithmetic: the delivered PSF
(its FWHM) and the profile height at the companion's offset ("wing"). Classification was
fixed before running: **R < 1 means the pair is inside one resolution element, so the
extraction is of the host.**

| target | sep (arcsec) | PSF | orders | **R** | wing | class | ledger verdict |
|---|---:|---:|---:|---:|---:|---|---|
| CD-35 2722 B | 2.800 | 0.263 | 283 | 10.64 | 0.00 | resolved | CONFIRMED, 70-90 m/s |
| eta Tel B | 4.210 | 0.374 | 367 | 11.26 | 0.00 | resolved | NULL, injection-gated |
| YSES 1 b | 1.698 | 1.197 | 24 | 1.42 | 0.12 | resolved | clean, 34 m/s |
| HIP 81208 B | 0.325 | 0.246 | 32 | 1.32 | 0.15 | resolved | clean, 124 m/s |
| beta Pic b | 0.511 | 0.952 | 114 | **0.54** | **0.55** | **blended** | contamination-limited |
| HD 206893 B | 0.205 | 0.393 | 11 | **0.52** | **0.63** | **blended** | *clean, gates 100-102%* |
| HD 4747 B | 0.590 | 1.514 | 15 | **0.39** | **0.71** | **blended** | reduced M29 as a test |
| 2M0103AB b | 1.764 | 0.986 | 10 | 1.79 | 0.02 | resolved | clean, gates 100+-0% |
| CD-35 deep pair | unsourced | 0.278 | 14 | - | - | unknown | shelved, thermal-IR |

**The two measurements agree with a clean gap.** R comes from the profile's width, the wing
from its height somewhere else; they share no arithmetic. Resolved cases have wing <= 0.15,
blended cases >= 0.55, and the ordering by wing is the ordering by R.

### What the sweep changes

**One verdict withdrawn. HD 206893 B is not a companion measurement.** M26 records it as
"clean data both settings, gates 100-102%, epochs banked". At R = 0.52 the pair is
unresolved and the extraction is of the host; the queue row now says so. The gates are not
evidence against this - a gate measures whether the *fitter* transmits an imposed velocity,
and it does that just as well on a bright star as on a faint companion. **This is the second
time a passing gate has accompanied a meaningless measurement** (the first was PDS 70's
nine-night template, M23 section 4), and the two failures differ: there the template had
lost its stellar lever, here the target is the wrong object.

**Beta Pic b's verdict was right and its mechanism was wrong.** "Contamination-limited" is
correct, but the cause is not starlight leaking into a resolved companion's spectrum - at
R = 0.54 there is no resolved companion. That explains what the three-pass template ladder
found empirically, an r(BERV) of +0.88 unchanged through v1, v2 and v3: no order mask or
template rebuild could have rescued it.

**Four verdicts confirmed as genuine companion measurements** - CD-35 2722 B, eta Tel B,
YSES 1 b and HIP 81208 B, at R from 1.32 to 11.26. Every claim the project rests on
survives: the detection, the eta Tel limit, and the two best-precision series.

**The two unsourced separations were then sourced, and both verdicts survive.**

- **2M0103AB b** — SIMBAD carries both components: SCR J0103-5515 (the AB binary) and
  SCR J0103-5515C (the companion). Their coordinates give **1.764 arcsec** at PA 338.7 deg,
  so **R = 1.79**, resolved. The wing corroborates independently at **0.02** — the profile
  at the companion's offset is 2% of the peak, which is what a genuinely separated pair
  looks like. The at-risk verdict clears.
- **YSES 1 b** — Bohn+2020 gives a projected physical separation of 160 au for the inner
  companion; SIMBAD's parallax of 10.6124 mas puts the system at 94.23 pc, so **1.698
  arcsec**. The queue's 1.7 was right; it simply had no provenance. R is unchanged at 1.42.

**Every live verdict in the roster now rests on a sourced separation.** The only
unclassified entry is the CD-35 deep pair, which is shelved thermal-IR and carries no
verdict to protect.

### The generalisable point

**A blending check belongs in the pipeline, before the injection gate, not after the
verdict.** It costs one slit-function read, needs no extra data, and it tests the one thing
every other check assumes: that the spectrum belongs to the object named in the verdict.
The gate cannot do it, RV precision cannot do it, and across-order dispersion cannot do it -
a host spectrum is *better* by all three.
