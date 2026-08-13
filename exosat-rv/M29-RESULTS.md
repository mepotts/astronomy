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
> **To close it:** Lazzoni's own sources are not archived. Adding **Langlois et al. 2021b**
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
