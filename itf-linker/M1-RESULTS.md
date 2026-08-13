# M1 — fit first, link second

**Outcome: the fit chain works end to end. 128 ITF designations have orbit solutions that
pass the MPC's published post-fit criteria.**

**None of them is a discovery, and nothing here says otherwise.** A trkSub that fits
cleanly is, far more often than not, a known object under a survey's internal tracking
name. Distinguishing the two requires the catalogue cross-match (MPChecker / SkyBoT /
JPL SBIDENT) that is M2 and is deliberately not done here. §7 gives the concrete evidence
that this caution is not boilerplate: one of the designations submitted for fitting came
back identified by Find_Orb as **comet 73P/Schwassmann-Wachmann 3, fragment C**.

Nothing was submitted anywhere. All network access was read-only HTTPS GET against public
MPC and JPL endpoints.

Every number below came from code in this repo. Reproduce with `itf-linker m1 --out
m1-report.json`; the build verification is `itf-linker fit-selftest`.

---

## 1. Provenance

| | |
|---|---|
| ITF snapshot | `Last-Modified` **Wed, 29 Jul 2026 05:26:45 GMT**, ETag `"8084534-657b9338b6bcf"`, 134,759,732 B |
| Snapshot id | `20260729T052645Z` (archive entry #1) |
| Find_Orb | `~/bin/fo`, built 2026-07-29 from `find_orb@143c823` (2026-07-23) |
| Force model | `PERTURBERS=000007fe` (Mercury–Pluto + Luna), **JPL DE-440** |
| Tests | **140 passing** (60 from M0, unchanged) |

---

## 2. Find_Orb build and verification

Full, reproducible build steps are in
[`DATA-SOURCES.md` §4](DATA-SOURCES.md#4-find_orb-build-wsl--verified-2026-07-29). Summary:
Find_Orb has no supported Windows build, so the console binary `fo` is built under WSL
Ubuntu 24.04 from the project's own `DOWNLOAD.sh`/`INSTALL.sh` order and driven from
Windows through `fit/wsl.py`. Only `make fo` is built — `make all` also builds the
interactive ncurses UI, which needs `libncurses-dev` and root.

### The verification is a closed loop against JPL Horizons

"It compiled" proves nothing about an orbit solver. `itf-linker fit-selftest` asks
**Horizons** for astrometric RA/Dec of a known minor planet as seen from observatory 703,
writes it as MPC 80-column astrometry, fits it with `fo`, then asks Horizons for the
osculating elements **at the epoch Find_Orb chose** and compares. No truth value comes
from Find_Orb, and the epoch is not agreed in advance.

Three targets spanning dynamical classes, two cadences, clean and noisy — **11 of 12 pass**
(all 6 at the ITF-like 9-day cadence). On noise-free 49-day arcs:

| Target | Arc | RMS | Δa/a vs JPL |
|---|---|---|---|
| (433) Eros — NEO | 49 d | 0.0026″ | −6.4 × 10⁻⁷ |
| (7) Iris — inner main belt | 54 d | 0.0034″ | −2.2 × 10⁻⁶ |
| (588) Achilles — Jupiter Trojan | 49 d | 0.0036″ | +7.0 × 10⁻⁸ |

With 0.30″ noise injected, every element lands within **2.1 σ** of truth using Find_Orb's
*own* reported sigmas. That is the property the MPC's σ(a)/σ(q)/σ(i)/σ(e) gate depends on,
and it is the reason the noisy run is judged on σ rather than on absolute agreement: over a
9-day arc the semimajor axis is genuinely undetermined (σ(a) ≈ 0.1 AU) however good the
astrometry, so a fixed tolerance would be measuring the arc, not the solver.

### Three things the verification found that would otherwise have been silent

1. **`PERTURBERS=0` is the shipped default** — "only what the automatic close-approach
   logic switches on", which for a main-belt asteroid is *nothing*. Dropping Jupiter
   displaces a 2.5 AU asteroid by ~0.1″ over a 7-day arc, against an 0.25″ RMS gate: a
   third of the error budget, spent silently. Fixed by `PERTURBERS=7fe`, and the force
   model is now parsed out of every `elements.txt` and recorded with each fit.
2. **Find_Orb destabilises below ~0.05″ declared positional sigma.** Holding the
   astrometry fixed on an 8-day Eros arc and varying only the `#Posn sigma` directive:
   0.01″ → a = 3.33 AU (truth 1.458), 0.02″ → 3.45 AU with 5 of 15 observations rejected,
   0.05″ and above → 1.4576 AU with σ(a) scaling linearly with the declared sigma, exactly
   as a correct covariance must. Real astrometry is never that precise so the limit does
   not bind, but an optimistic sigma is a way to break a fit while it still reports a
   plausible-looking σ(a) = 0.25.
3. **A documented Find_Orb limitation, not a build fault.** The single failing case is
   Eros over a 49-day arc with weekly gaps *and* 0.30″ noise: initial-orbit determination
   locks onto a 6-observation subset and returns a ≈ 13.5 AU, e ≈ 0.88. Isolated by A/B —
   the same 24 epochs noise-free converge exactly; the same noisy data truncated to 14- or
   21-day arcs converge correctly (a = 1.426 / 1.466 against truth 1.458). `-j`, `-y 5`,
   `-y 10` do not help. It does not touch M1 (median fitted arc 7 days) but it is the
   direct reason the post-fit guard in §6 exists.

---

## 3. The funnel

```
9,322,655  observations in the snapshot
       −4  pre-1900 sentinel epochs
       −3  blank designations
   −1,161  exact duplicate records            <- new finding, §3.1
─────────
9,321,487  usable observations
           -> 2,628,833 tracklets -> 2,602,958 designations

    2,515  designations spanning 3+ nights          (M0's figure, reproduced exactly)
   −1,395  fail the MPC's published pre-fit gate
─────────
    1,120  pass the pre-fit gate                    (1,034 single-observatory, median arc 7.02 d)
     −141  trkSub collision suspects                                            §4
─────────
      979  submitted to Find_Orb
       −4  no usable astrometry (all their S observations unpaired)
─────────
      975  fitted
```

Pre-fit rejections (a designation can fail on more than one): arc < 3 d — **884**;
exactly 3 nights with arc > 15 d — **465**; singleton tracklet at both ends — **152**;
fewer than 3 nights — 0 by construction.

**M0 quoted 1,046 here and 976 single-observatory; this run measures 1,120 and 1,034.**
M0's figure came from a calculation that was not kept in the repo, so it cannot be
reconciled directly. The difference is the arc definition: measuring the arc between
*night indices* rather than between the first and last observation admits 1,293, and
measuring it between observations admits 1,120. This milestone uses the true observation
arc — the exact epochs are in hand, and rounding each end to a night boundary can add a day
at each end and lift a 2.6-day arc over the 3-day threshold. The median arc, 7.02 d,
matches M0's "median arc 7 days" exactly. The gate is implemented twice (vectorised in
`fit/candidates.py`, scalar in `verify/mpec.py`) and the two are pinned against each other
in `tests/test_candidates.py`.

### 3.1 The ITF contains exact duplicate records

**476 (designation, observatory, epoch, RA, Dec) groups repeat — 1,161 redundant rows.**
Almost all are from **W84** (DECam), repeated *six* times, byte-identical including
magnitude and catalogue code, and carrying the `!` do-not-redistribute flag in note 1.

Not a parser artefact: the whole 80-column line is duplicated in the source file. It
matters because six copies of one detection are not six measurements — left in, they
multiply that epoch's weight in a least-squares fit, and let a one-detection night appear
to satisfy the MPC's "two observations per object per night" rule. They are removed by
`fit/candidates.py::bad_data_filter` and counted. Find_Orb independently detects some of
them at fit time (`2 observations were duplicates. They have been removed.`), which is
corroboration rather than a reason to leave the job to it.

Also worth recording: **1,282 unpaired `S` observations** (M0's count) become **576**
inside the 979 candidates' astrometry, and four designations (`soho179`, `soho180`,
`soho185`, `soho187`) lose *all* of their observations to it, so they cannot be fitted at
all. Unpaired `S` records are dropped during extraction, where the pairing is visible;
they cannot be detected in the parsed Parquet, which does not keep `s` lines.

---

## 4. trkSub collisions — and why the obvious test fails

trkSubs are survey-internal identifiers with no uniqueness guarantee. M0 named two
reused ones: `des278` (17 nights over 1,154 d) and `soho183` (12 nights over 3,555 d).

**The heuristic the plan suggested — implausible sky motion — misses both.** Measured on
this snapshot, the largest apparent rate between consecutive tracklets is **0.021 °/day**
for `des278` and **1.06 °/day** for `soho183`. The first is slower than a typical
main-belt asteroid. The reason is geometric and unavoidable: great-circle separation is
capped at 180°, so across a 713-day gap even two *random* sky directions imply only
~0.25 °/day. Rate screening is sharp at short gaps and asymptotically blind at long ones —
which is exactly where name reuse lives.

Three independent screens are used instead (`fit/collide.py`), reported separately:

| Screen | Flagged (of 2,515) | Flagged by this alone |
|---|---:|---:|
| **Arc > 200 d under one trkSub** | 487 | 446 |
| **Sustained rate > 5 °/day over gaps ≥ 0.5 d** | 91 | 50 |
| **Same-night cross-site separation > 5°** | 1 | 1 |
| **any** | **538** | |

**Why 200 days.** Two reasons, one measured and one structural.

*Measured*: the arc distribution of the 2,515 multi-night designations is sharply bimodal
— a dense mode below 15 days (1,878 designations), a near-empty valley from 15 to 200 days
(119 designations spread over 185 days, ~0.6/day against ~125/day inside the mode), then a
second population running out to 4,945 days. The threshold sits in the valley.

*Structural, and the stronger argument*: an ITF trkSub covers one survey processing run. It
**cannot** span apparitions, because recognising that two apparitions belong to one object
is precisely the linking problem the ITF exists because nobody solved. A survey able to
carry one name across years would have submitted an orbit, and the observations would not
be in the ITF.

The names themselves confirm it. The longest-arc designations caught by this screen are
`T00001` (4,946 d), `object` (4,797 d), `UNK` (4,490 d), `Sar0004`, `T0000E`, `obj02`,
`obj10`, `GB00001`, `obj01`, `soho177` — generic placeholders and counters, not object
identifiers.

**The same-night screen is the only one with no tunable threshold.** Two ground sites see
one object displaced by at most ~2 R⊕/Δ — about 5° even at a geocentric distance of
0.01 AU, closer than essentially anything in the ITF. `so2107` shows tracklets from three
observatories on one night separated by **173.5°**. That is two objects, with no
astronomical judgement required. It is also rare: only 11 (designation, night) cells in the
whole snapshot hold more than one tracklet.

**None of this is the real defence** — see §6.

---

## 5. Fitting the 979

`fo`, 12 concurrent workers, 40 designations per invocation: **975 fitted in ~4.5 minutes**.

| | |
|---|---:|
| Submitted | 979 |
| Converged | **917** |
| Did not converge | 62 (57 no covariance, 4 no astrometry, 1 not returned) |
| Converged with RMS ≤ 0.25″ | **654** |
| Converged with RMS > 0.25″ | 263 |
| Rejected by the subset guard (§6) | 59 |
| **Passing every published gate** | **128** |

Residual RMS among the 917 converged fits:

| RMS | Count |
|---|---:|
| < 0.05″ | 176 |
| 0.05–0.10″ | 317 |
| 0.10–0.15″ | 83 |
| 0.15–0.20″ | 46 |
| 0.20–0.25″ | 31 |
| 0.25–0.50″ | 116 |
| 0.50–1.0″ | 129 |
| > 1.0″ | 19 |

**Convergence is not an explicit output of `fo`** and had to be defined. A genuine
least-squares solution carries a covariance and therefore per-element sigmas; when the
differential correction fails, Find_Orb still emits whatever preliminary orbit Gauss or
Väisälä produced, but the `* sigma` fields are simply absent. That absence — together with
a finite RMS, a bound orbit, and at least three observations used — is the test in
`fit/findorb.py::_convergence`. It is why the 57 `no_covariance` cases are counted as
failures despite having printable elements.

### The three-night sigma gate is where most candidates die

> **Corrected 2026-08-07.** These four are only four of the **five** published quality
> conditions — `e < 0.5` is published alongside them and was implemented nowhere in this
> project when M1 ran, so it is not in the table below and the "all four" column is not the
> published quality test. Scoping the block to three-night links is *our* choice, not the
> MPC's. See [`DATA-SOURCES.md`](DATA-SOURCES.md) §"Published acceptance criteria".

Of 862 converged three-night fits, four of the five published limits are met by:

| | σ(a) < 0.05 AU | σ(q) < 0.05 AU | σ(i) < 0.5° | σ(e) < 0.05 | **all four** |
|---|---:|---:|---:|---:|---:|
| Three-night fits passing | 269 | 149 | 405 | 259 | **101** |

**σ(q) is the binding constraint**, passed by only 17% of three-night fits. That is the
single most useful number for planning M1's successor: a three-night ITF arc usually
determines the *direction* of the orbit well and its *scale* poorly, and perihelion
distance is a scale quantity.

---

## 6. The guard that matters: one orbit must fit all of it

A name collision does not merely raise the residuals. Find_Orb can converge on the subset
belonging to *one* of the objects, discard the rest, and report a perfectly respectable
RMS. The build self-test reproduced exactly that shape on a hard NEO arc — **6 of 24
observations used, RMS 0.225″**, elements wrong by a factor of nine in `a`. **An RMS gate
alone would have passed it.**

So a solution is credited only if Find_Orb used ≥ 80% of the observations *and* the
observations it actually used still span three nights
(`fit/collide.py::post_fit_collision_check`). **59 of 917 converged fits are rejected by
this**, and they would otherwise have been indistinguishable from good ones. 875 of the
917 used every single observation.

This, not the pre-fit screens, is the real collision test: it is the physics — a single
bound Keplerian orbit either fits every detection or it does not — rather than a threshold.

---

## 7. What the 128 actually are

**Not discoveries.** Three measurements from this run, each of which should temper the
number before anyone repeats it:

**(a) One submitted designation came back as a known comet.** `0073P-C` — 5 nights, 13
observations from observatory 084 — was returned by Find_Orb under the name **73P-C**,
i.e. comet 73P/Schwassmann-Wachmann 3, fragment C, which it recognised from the packed
designation in the record itself. It is not a trkSub collision and not a candidate; it is a
known object sitting in the ITF under its own designation. It also refines an M0 finding:
M0 tested columns 1–5 for minor-planet numbers and the trkSub field for packed *asteroid*
provisional designations, and found none. A packed *periodic-comet* designation was not in
that pattern, and at least one is present.

**(b) 100 of the 128 are Rubin (X05) alone**, and 539 of the 979 candidates are X05-only;
91 of the 128 share the single naming family `RL00…`. This is overwhelmingly one survey's
recent tracking names, not a cross-archive result. Whether Rubin has already linked these
internally is exactly the M2 question.

**(c) 29 of the 128 pass on a technicality.** *Our* gate applies the sigma limits only to
three-night links, so a fit with more nights clears it on RMS alone. (Corrected 2026-08-07:
this was written as the MPC's scoping. It is not — their published rule has a separate
bullet for links with more than 3 nights, and applies the quality block only when RMS
> 0.25″ *and* the arc is short. The technicality is real but it is ours.) Applying the same
four limits to every passer regardless of night count leaves **99 of 128**. The 29 that fall out
are distant-object candidates whose arcs cannot constrain distance — fitted a of 58–304 AU
with σ(a) of 37–784 AU — and one, `t75502b`, is worse than that:

```
t75502b   5 nights, 54.7 d arc, RMS 0.086"
          a = 1.09e+11 AU   e = 0.999999999711   sigma(a) = 8173 AU   U = -2.38
```

A numerically meaningless orbit that satisfies the MPC's published post-fit criteria,
because the only criterion it is tested against is its residual RMS. **This is reported
rather than filtered**: the criteria are the MPC's and the ranking is ours. The ranked list
in `m1-report.json` (`fits.ranked`) sorts by RMS, then σ(a), then arc, so these sort to the
bottom on their own.

**The defensible headline is therefore: 99 designations have orbit fits that are both
acceptable to the MPC's published filter and numerically well-constrained.**

The best-conditioned ten:

| desig | nights | obs | arc (d) | RMS (″) | a (AU) | e | i (°) | q (AU) | σ(a) | U |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `RL00adt` | 3 | 6 | 11.27 | 0.0198 | 2.186 | 0.121 | 3.79 | 1.921 | 0.0016 | 7.6 |
| `RL00eAJ` | 3 | 6 | 7.04 | 0.0226 | 2.169 | 0.192 | 5.17 | 1.753 | 0.0228 | 9.2 |
| `RL00Zz9` | 3 | 8 | 10.01 | 0.0302 | 3.154 | 0.212 | 2.48 | 2.484 | 0.0072 | 8.0 |
| `RL00d8o` | 3 | 34 | 6.98 | 0.0328 | 2.370 | 0.201 | 2.08 | 1.893 | 0.0171 | 8.8 |
| `RL00XSM` | 3 | 9 | 12.98 | 0.0328 | 2.899 | 0.024 | 0.91 | 2.828 | 0.0206 | 8.8 |
| `RL00YHG` | 3 | 7 | 12.97 | 0.0328 | 2.861 | 0.083 | 0.96 | 2.623 | 0.0051 | 8.1 |
| `RL00iMW` | 3 | 6 | 10.32 | 0.0331 | 2.374 | 0.135 | 6.07 | 2.054 | 0.0281 | 9.2 |
| `RL00hfG` | 3 | 8 | 7.04 | 0.0332 | 2.585 | 0.199 | 9.97 | 2.071 | 0.0300 | 9.1 |
| `RL00iWy` | 3 | 6 | 10.00 | 0.0333 | 2.289 | 0.227 | 4.90 | 1.770 | 0.0046 | 8.0 |
| `RL00aYD` | 3 | 7 | 11.03 | 0.0339 | 2.288 | 0.112 | 3.12 | 2.032 | 0.0015 | 7.4 |

Every one is an ordinary inner-to-middle main-belt orbit (a = 1.7–3.2 AU, e < 0.25,
i < 10°) — the population an all-sky survey re-detects constantly. **The prior that any
given one is unreported is low**, which is the whole reason M2 exists.

The full ranked list, with covariances, per-observation residuals and every gate decision,
is in `m1-report.json`.

---

## 8. Reproducibility

Re-running the fit on the same snapshot gives a **byte-identical set of 128 passers**.
Only 5 of 979 designations differ at all between runs, and all 5 already fail the RMS gate
(one moves 0.398″ → 4.44″); one designation flips between `converged` and `no_covariance`.
This is Find_Orb's own stochastic component, not the harness — the harness was made
deterministic by sorting designations before chunking, since Python randomises string
hashing per process and unsorted grouping changed which objects shared an invocation.

### Four harness bugs worth recording, because each failed silently

1. **`$HOME` inside single quotes.** The `fo` path was passed as `'$HOME/bin/fo'`, which
   the kernel never expands. `fo` simply never ran; every designation came back
   "not returned". Configuration is now double-quoted (expansion intact) and data
   single-quoted (expansion suppressed), and both are tested.
2. **A relative `--workdir`.** `to_wsl_path("data/fits")` has no drive letter to translate
   and passed it through unchanged; `fo` is invoked as `cd <dir> && fo obs.txt -O <dir>`,
   so `-O` resolved *inside* the directory it had already entered. `fo` exited **0**,
   printed nothing, and wrote its results where nobody read them — "0 of 979 converged"
   from the CLI while the identical run from a script gave 916. Paths are now made
   absolute before translation.
3. **Sharing `fo`'s own outputs between workers.** `fo` leaves `elements.json`,
   `total.json` and a dozen others in whatever directory it treats as its own. Building
   each worker's config directory by symlinking the *whole* shared directory therefore
   pointed twelve concurrent processes at one `elements.json` — and `fo` merges each
   object by re-reading that file, so the reader tripped
   `fo.cpp:457 Assertion 'found_start' failed` and aborted with SIGABRT, losing the whole
   batch. Worker configs now exclude a denylist of `fo` outputs and are rebuilt from
   scratch each time.
4. **Incremental worker config directories.** Adding missing symlinks and never removing
   stale ones leaves entries behind forever, and a `[ -e ]` guard cannot even see a
   dangling symlink to test for it.

Because a failed `fo` invocation looks exactly like "every object failed to converge", the
runner now **bisects** any invocation that returns nothing, down to single designations, so
one poisoned object costs log₂(chunk) extra runs instead of the other 39 results. Every
such failure is recorded in the report (`fits.fo_invocation_failures`, currently empty).

---

## 9. Snapshot archive (Task 4)

`itf-linker snapshot` archives each ITF pull so that *"which observations disappeared
between date A and date B"* stays answerable. This is the ground-truth control M0 asked
for, and it can only be built forward in time.

**Today's pull is snapshot #1**, not discarded: `20260729T052645Z`, the exact file the
whole of §3–§7 was computed from. A second, `20260729T072634Z`, was taken two hours later.

Storage is a **baseline plus a delta chain**, not a file per day:

| Kept | Retention | Size |
|---|---|---|
| `manifest.json` — provenance + counts | **forever** | ~1 KB |
| `delta.parquet` — every observation that appeared or disappeared since the previous snapshot | **forever** | 608 B for a no-change pull |
| `observations.parquet` — full 64-bit key set | rolling window of 3 | 178 MB |
| `designations.parquet` — per-designation summary | rolling window of 3 | 8.9 MB |
| `itf.txt.gz` — original bytes | rolling window of 1 | 135 MB |

A full key set per snapshot is 178 MB — *larger than the compressed source*, because a
64-bit digest is incompressible by construction and sorting by it destroys the locality
that would let the designation and epoch columns compress. Keeping one per day would be
65 GB/year for a signal measured in thousands of rows. The delta chain answers the same
question for any pair, for all time, from kilobytes; `snapshot.diff` uses full key sets when
both snapshots still have them and replays the chain otherwise, and the two paths are
pinned to agree in `tests/test_snapshot.py`.

The observation key is a 64-bit digest of *quantised* fields — designation, observatory,
MJD to 1e-6 d, RA and Dec to 1e-7° — deliberately **not** the raw line. The MPC re-reduces
observations against new star catalogues; hashing the line would report a changed
magnitude as "this observation vanished and a different one appeared", which is precisely
the signal being measured. It is BLAKE2b plus a fixed splitmix64 fold rather than polars'
`.hash()`, whose algorithm is an implementation detail that could change between versions
and silently invalidate every older snapshot.

### The first real diff is a clean negative control

The two pulls have **different ETags and `Last-Modified` two hours apart**, and byte-identical
content: 0 observations appeared, 0 disappeared, 9,322,655 both times. The MPC regenerates
the file without changing it — M0 saw the same thing (`Last-Modified` moving twice in an
hour at constant size).

That is a useful result rather than a wasted pull. It is a null control on the whole
pipeline: an unstable key, a timestamp accidentally folded into the digest, or a
non-deterministic sort would all have produced spurious churn across 9.3 million rows.
None appeared. Snapshots are keyed on the file's own `Last-Modified` rather than on fetch
date, so a no-change regeneration costs a manifest and a 608-byte delta.

---

## 10. What M1 did not do

- **No linking.** M1 fits designations that already span 3+ nights. The
  pair→predict→confirm work over the MJD > 60000 sandbox is untouched, and M0's
  "never enumerate triplets" constraint still stands.
- **No vetting.** No MPChecker, SkyBoT, SBIDENT or DAD cross-match. This is why §7 is
  worded as it is.
- **No submission.** No submission code exists in this repo, sandbox or otherwise.
- **The trkSub-hiding ground-truth control** that M0 called for is not built, because it
  tests the *linker*, and there is no linker yet.

## 11. Verdict

**GO.** The single genuinely new component — Find_Orb integration — is built, verified
against an independent authority, and fast enough to be irrelevant to planning (975
designations in 4.5 minutes on a laptop). The published gates are implemented and each is
tested to reject on its own. The funnel is auditable end to end.

The binding constraint for M2 is now clearly **vetting**, exactly as the plan predicted.
128 designations pass a filter the MPC would apply; 99 of those are also numerically
well-constrained; and the honest expectation is that most are already-known objects.
Finding out which is a catalogue-lookup problem, not an orbit problem, and it is the next
thing to build.

The second-order finding is that **the MPC's published post-fit criteria are not
sufficient on their own**. They admit a fit with σ(a) = 8,173 AU, and they would admit a
subset fit of a colliding trkSub because RMS says nothing about how many observations were
used. Both holes are closed here by additional checks that are clearly labelled as ours,
not the MPC's.

> **Corrected 2026-08-07.** The first hole was attributed to the sigma limits being "scoped
> to exactly-three-night links". That scoping is *ours*. The MPC's actual rule admits
> σ(a) = 8,173 AU for a different and larger reason: its post-fit conditions are
> **conjunctive**, so a converged fit with RMS ≤ 0.25″ is never quality-tested at all,
> whatever its night count. The finding stands and is in fact stronger than stated.
