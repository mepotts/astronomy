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
