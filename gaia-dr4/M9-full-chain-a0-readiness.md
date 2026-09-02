# M9 — the chain run end to end, the zero-point decision fixed in advance, a₀'s external reference measured and found wanting, and the front closed for December

*2026-08-24. The closing milestone. Runs M8's own recommendations 2, 3 and 4 (the
amendment ruling, recommendation 1, is Matthew's and is untouched). Repo law:
sourced-or-UNSOURCED; negative results are results; rules pre-registered. Anonymous HTTP
only. No accounts, no submissions, no commits, no pushes.*

---

## 0. The one-paragraph answer

**The chain had never been run, and running it broke four things that no amount of
component testing would have found — including the fact that the December refit command
in the runbook could not consume a single December source.** Harness → orbital refit arm
→ v2 verdict store → the pre-registered labels now runs as one thing over the real
981-row queue in **7.8 minutes of compute** (adjudicate 51 s → refit 98 s → labels 319 s)
on top of transport, which is **94 % of the day**; every stage was **SIGKILLed and
restarted** and every one resumed with **0 duplicated and 0 lost rows**. The four
scale-only defects: **(1)** `orbital_refit_arm.py --ids`, the command this runbook
prescribed for release day, routes to the twelve-source pre-release file — it answers
`NO_DATA` for every DR4 id and then dies on a `KeyError`; a `--queue` entry point that
consumes the harness's own ledger now exists and is measured at **0.44 s/source, 219
refits, 0 failures, 218 of 219 zero-point-corrected**. **(2)** DR4's `astrometric_params` is a **bitmask**, not DR3's
3/31/95 — **17 of its 19 declared values fail `zpt.get_zpt`, 11 of them are the
non-single-star values, i.e. this project's entire list** — and because the house wrapper
*masks* rather than raises, the zero-point would have **silently vanished on all 981 rows**
and every mass would have shipped high by ~3Z/ϖ. **(3)** `os.replace` on Windows killed a
981-source transport run at source 360 with a sharing violation. **(4)** Two harness runs
on one ledger duplicated **180 rows** with nothing in the code to stop them. All four are
fixed; a nine-stage rehearsal is green in **41 s** with the fixes in.
**December's zero-point comparison is now a prediction, not a shrug**: L21's Z is frozen
for all 981 queue members (median **−35.47 µas**, 99.8 % correctable), five verdicts with
numeric thresholds are pre-registered, the rule has been **run against six declared
synthetic bias columns and returned all six correctly**, and which correction wins is
decided in advance — **DR4's own column, wherever it is usable**.
**And a₀'s external calibration is closed by being declared impossible, with a number.**
The entire published, machine-readable, non-Gaia supply of photocentric semi-major axes —
Hipparcos DMSA Part O ∪ ORB6 grade 9 — is **36 systems** after matching, its σ(a₀)/a₀ is
**13.6 % against Gaia's 4.7 %**, and its measured power to detect M8's ×1.4 is **10 %**.
**a₀'s error bar has no external calibration and will not get one before December.** What
it *can* do is bound the **scale**, and it does: **0.979 ± 0.004**, with two named
astrophysical alternatives of the same sign that 36 systems cannot separate from a real
Gaia offset. A second, fully external and one-sided route (SB9's K₁ → a₁ sin i, 53
astrometry-only solutions, where a luminous secondary can only push the ratio down) agrees:
median **R = 0.968**, over-run above 1 at **5.7 / 1.9 / 1.9 %** against 15.9 / 2.3 / 0.14
expected.

---

## 1. Task 1 — the production chain, end to end, at December scale

### 1a. What was actually missing, and why only the chain could show it

M6 built the harness. M7 measured transport at 981-row scale and built the refit arm,
validated on three objects. M8 measured the analysis half at 981-row scale on synthetic
stores and ran every pre-registered command. M8's own recommendation 4 named what was
left: *"the pieces are all now measured; the chain is not."*

The obstacle is real and is stated first, as M8 stated its own: **the fitting half of the
chain consumes epoch astrometry, and twelve sources of it exist in the world** before
2026-12-02. So the chain was driven with the best stand-in each half admits:

| stage | stand-in | what it does and does not rehearse |
|---|---|---|
| **1 transport** | live DR3 `EPOCH_PHOTOMETRY` over M7's payload-stratified 981 ids, into a **chain-private cache root** so the fetch is real and not a cache-hit replay | rehearses batching, retry/backoff, `Retry-After`, the atomic cache, resume and the real network. Differs from December in **kind** (photometry, not astrometry); M7's cost model converts |
| **2 adjudicate** | the **real 981-row day-one queue** through the harness's real adjudication path, reading epoch astrometry from the M9 fixture | rehearses the verdict rules, the schema, the ledger, the checkpoint and the resume at December's exact size and shape |
| **3 refit** | every `CONFIRMED (orbit_reality)` row through the arm's **December entry point**, with `--zeropoint` | rehearses the whole arm: M₁ ladder, mass function, Laplace posterior, zero-point, v2 store |
| **4 labels** | the seven pre-registered commands + the label function | rehearses §3.3 exactly as written |

`scripts/m9_dec_scale_fixture.py` builds the fixture: each queue member gets a **donor**
epoch table copied from one of the twelve real pre-release sources, with the donor's
`source_id` rewritten so the frame is internally consistent. **Declared before the build**
(seed 20261202): 0.90 full donor, 0.05 truncated (must return `INCONCLUSIVE`), 0.05 no
file at all (must return `NO_DATA`). Three of the twelve donors carry a real photocentre
orbit, so the split reproduces the harness's own measured 3 : 9 — which the
pre-registration §4 already lists as a projected December ratio.

**Nothing synthetic can reach December's analysis.** The fixture lives under its own
release tag with a `README.NOTE.md` saying it is not data; the verdicts go to
`out/verdicts_dec_rehearsal/`, never `out/verdicts/` (what `--verdicts all` reads) or
`out/verdicts_v2/`. Both directories are hashed before and after every chain run.

### 1b. DEFECT M9-1 — the December refit command could not consume a December source

The runbook §3.4 prescribed, and the arm's own help advertised:

```
orbital_refit_arm.py --ids <comma-separated> --zeropoint
```

`--ids` routes to `run_prerelease()`, which fetches epoch astrometry from the twelve-source
2026-06-26 pre-release VOTable. Handed a real DR4 id it returns `NO_DATA` for every source
and then dies:

```
KeyError: 'delta_over_refit_formal_err'
```

inside `literature_comparison`, because the comparison frame is empty — **after** writing
an empty trio CSV. `build_v2_store` likewise defaulted its `ledger` to the pre-release
one, so there was no way to attach refits to a December ledger either.

This is M8's DEFECT C-1 one layer down, and the same sentence covers both: *a
pre-registered command is only as executed as its least-run line, and the line nobody runs
is the one against the input that does not exist yet.* M7 and M8 both exercised the arm —
on the trio, which is exactly the input that hides this.

**Built in M9: `orbital_refit_arm.py --queue`,** the December entry point. It reads a v1
harness ledger, selects `CONFIRMED (orbit_reality)`, fetches each source's epoch astrometry
from the cache the harness already filled, takes M₁ from **the triage frame's own ladder**
(so no per-source DR3 cone search — December already knows the id), applies `--zeropoint`,
and appends to a **per-source ledger** so a kill costs at most the source in flight. The
`KeyError` is also fixed: an empty comparison now says so and returns.

### 1c. DEFECT M9-3 — `os.replace` killed a 981-source run at source 360

The transport leg died with

```
PermissionError: [WinError 5] Access is denied:
  '...5872921517343356032.parquet.tmp' -> '...5872921517343356032.parquet'
```

`os.replace` is atomic on Windows but it is **not** immune to a sharing violation — an
antivirus or the search indexer scanning the file microseconds after it is written is the
usual cause. It is transient and per-file. The `.tmp` → `os.replace` pattern is the exact
mechanism M6 and M7 relied on for *"a kill mid-write cannot leave a half-file that looks
cached"*, and it took down the stage that owns 97 % of December's wall clock, with a
non-zero exit, at row 360 of 981.

**Fixed**: six retries with exponential backoff, then a named failure. Atomicity is
unchanged — a reader still sees either the old file or the new one. The runbook now also
says to exclude `data\epoch_cache\` from real-time scanning before 2 December.

### 1d. DEFECT M9-4 — a crash lost every per-batch timing it had made

The same crash exposed its twin. `out/m6_harness_timings.csv` was written **once, after
the batch loop**. A run that dies at batch 17 of 50 therefore loses every timing it
recorded — which is precisely (a) what you need to diagnose the crash and (b) what runbook
§3.0 instructs you to read the day's delivered KiB/s from. **The ledger checkpointed every
batch and the instrumentation did not.** Fixed: flushed per batch.

### 1e. DEFECT M9-5 — two writers, one ledger, 180 duplicated rows

Mid-milestone a background transport run was reported finished by the shell while the
detached process ran on; a second run was launched against the same ledger. The result:

```
ledger rows 440 | distinct sources 260 | duplicates 180
```

and a restart that announced *"981 queued, **220** already in the ledger"* against a file
holding 360. Both runs fetched, both appended, and the resume count — the number the whole
contract rests on — was wrong in a way nothing printed.

**This was an operator error, and the point is that nothing in the harness prevented it.**
The resume contract ("the ledger is the resume point; a restart skips what is in it") is
only true of **one** writer: two processes each read the ledger at start-up, each compute a
`todo` from a snapshot that is stale the moment the other appends. On release day somebody
*will* double-launch — a terminal left open, a scheduled retry, a detached job the shell
called done.

**Fixed: `LedgerLock`.** An exclusive-create lock file beside the ledger; a second run is
refused out loud with the holder's pid and start time, and `--force-unlock` clears a stale
one. Verified: the second acquisition raises, the lock is removed on exit.

### 1f. The measured chain

`scripts/m9_full_chain.py --run` → `out/m9_chain/m9_chain_result.json`.

| stage | wall clock | output |
|---|---|---|
| 0 preflight (fixture + zero-point table + frozen hashes) | 0.0 s | — |
| 1 transport (live DR3 DataLink, 981 ids, batch 20) | **the day's weather** — see §1g | 981 transport-ledger rows |
| **2 adjudicate** | **50.6 s** | **981 verdicts**: 219 CONFIRMED / 668 SPURIOUS / 47 INCONCLUSIVE / 47 NO_DATA |
| **3 refit, `--zeropoint`** | **97.9 s** | **219 refits, 0 FIT_FAILED, 0 NO_PEAK, 0 NO_DATA**, 0.444 s/source, **218 of 219 zero-point-corrected** |
| **4 labels** | **318.9 s** | 7 labels, 0 non-zero exits, 5 subprocess runs |
| **total, transport excluded** | **467.8 s = 7.8 min** | frozen-artifact check **13/13 unchanged** |

**The verdict tally matches the fixture's declared expectation exactly** — 219 / 668 / 47 /
47 — so all four reachable verdict rules fired at scale, which had never happened in one
run before. (`ERROR` did not fire, correctly: no fit raised.)

**What the refit arm produced, and one number worth carrying into December**: of 219
refits, **171 got M₁ from `binary_masses`, 5 from the photometric MS rung, and 43 came
back `UNSOURCED`** — **20 % of December's confirmed orbits will have no primary mass, so
the M₁-free mass function is all there is to quote for them.** That is the population M8
measured the −4.1 % median (−33.7 % worst) zero-point shift on.

**Chain wall clock, stated honestly, three ways.** Transport is 94 % of the day and it is
the one stage whose stand-in differs in kind, so:

* **7.8 min of compute** for everything after transport — measured here, and measured
  **pessimistically**: the live transport leg was running concurrently and competing for
  the same machine. An earlier, uncontended run of the same three stages took **6.7 min**.
  The pessimistic number is the one quoted.
* **≈ 2.2 h end to end**, taking transport at M7's measured median (2.1 h) — measured in
  M7, quoted here.
* **Neither is a projection of the other**, and the second is the one that moves: see §1g.

### 1g. The archive was slow today, and that is the data point

The transport leg ran live against ESAC all afternoon, through the production harness, on
M7's payload-stratified 981 ids. **520 sources transported, 0 duplicates, 33,761 transits,
21.9 MiB cached**, with per-batch timings recorded for every batch that ran after the
instrumentation fix of §1d:

| | today (M9, 2026-08-24) | M7 (2026-08-23) |
|---|---|---|
| seconds per batch of 20 | min **34.4**, median **129.0**, p90 205.4, max **224.7** | min 15.2, median **26.9**, p90 34.3, max 42.2 |
| spread within the run | **6.5×** | 2.8× |
| sustained rate | **554 sources/hour** | 2,379 sources/hour (at DR3 payload) |

**A 4–8× degraded archive on the same service, the same code and the same id list, one day
apart.** That is exactly the "weather" M7 said only release day could settle, and it lands
between M7's p90 branch and M6's bad afternoon — inside the bracket the runbook already
carries, at the pessimistic end of it. **It changes no plan**: the queue is ranked, so a
slow archive costs **depth, not the headline** (BH1, BH2 and the EB26-refuted poster child
are adjudicated in the first minutes on every branch), and the chain's compute half is
minutes either way.

**The leg was stopped at the close of this milestone, at 520 of 981, and it was never required to finish.**
Its purpose was to exercise the real network through the real code at real scale, and it
did that four times over — including by crashing (§1c), by being resumed from its ledger
three times, and by catching the duplicate-writer defect (§1e). What December quotes for
transport is M7's cost model with the day's own KiB/s substituted, which is a number
release day reads off the first ten batches; today's run is one more measurement of how
wide that number's distribution is.

### 1h. Resume, tested by killing things

`scripts/m9_full_chain.py --resume-test` → `out/m9_chain/m9_resume_test.json`. Each stage
is run as a subprocess, **SIGKILLed** partway, and restarted.

| stage | killed at | after restart | duplicates | orphan `.tmp` | |
|---|---|---|---|---|---|
| 2 adjudicate | **260 / 981** | **981** | **0** | 0 | **PASS** |
| 3 refit | **56 / 219** | **219** | **0** | 0 | **PASS** |
| 4 labels | — (no ledger; the contract is idempotence) | byte-identical re-run, sha `1a4dcd3041dfc9e5` | — | — | **PASS** |
| 1 transport | killed twice at real scale during the milestone | resumed both times from the ledger | (see §1e — and now locked) | 0 | **PASS** |

**Every stage boundary and every mid-stage kill.** No `.tmp` file was ever left behind
pretending to be a cache hit, which is the failure the atomic-write design exists to
prevent and the one a resume test that only restarts cleanly would never look for.

### 1i. And a fixture that did not control what it claimed to

The first chain run came back **without a single `INCONCLUSIVE`**: all 47 thin-donor rows
adjudicated exactly like the full ones. The cause is a unit mismatch the ledger's own
column names invite: **a row of the raw epoch table is one FIELD-OF-VIEW transit, and
`gaiasupdate` expands each into ~8.5 CCD transits**, so a donor truncated to "30 CCD
transits" arrived at the gate with **255** `n_transits_used` — five times `MIN_TRANSITS`.

This is M8 landmine #13 again — *a control that does not change what the test reads is
worse than none* — and it was caught the same way M8 caught its own: **the arm's numbers
came out indistinguishable from the arm it was supposed to differ from.** Fixed
(4 FoV rows ≈ 34 CCD transits), and the fixture now asserts after the run that every rule
actually fired. `n_transits_fetched` and `n_transits_used` are not the same unit, and the
runbook now says so.

---

## 2. Task 2 — how December decides between L21 and DR4's own column

`scripts/m9_zeropoint_crosscal.py` → `out/m9_zeropoint_crosscal.txt`,
`out/m9_zeropoint_prediction.csv`, `out/m9_astrometric_params_decode.csv`.

### 2a. The column, verified independently

M8's read of the pre-release draft data model is confirmed here from the same PDF, at both
sites, verbatim:

> **`tentative_parallax_bias`** : Parallax bias correction (double, Angle[mas]) — "This is
> the parallax bias correction computed based on the recipe in [?]. **This correction is to
> be subtracted from `parallax` to get the corrected parallax.**"

— declared in **`gaia_source`** (draft p. 20) and in **`all_source_astrometry`** (p. 74),
on L21's exact convention.

### 2b. DEFECT M9-2 — the guard column is not just renamed, and the failure is silent

M8 flagged that `astrometric_params_solved` becomes `astrometric_params` and that
`zpt.get_zpt` **raises** if that column is wrong. Reading the same page to the end (p. 19,
the value table) shows the bigger half: **the value set changed.**

DR3 took **3 / 31 / 95**. DR4 declares **nineteen** values —

`3, 7, 27, 31, 63, 95, 479, 2015, 2079, 2463, 3999, 4127, 4575, 6111, 6175, 8223, 8607, 10143, 10271`

— because DR4 adds bits for fitted **acceleration** terms and, at bits 11/12/13, for
**non-single-star models (Orbital / VIM / Resolved)**. `zpt.get_zpt` accepts 31 and 95 and
nothing else:

| | |
|---|---|
| declared DR4 values | **19** |
| of those, rejected by `zpt.get_zpt` if passed raw | **17** |
| of those, non-single-star (Orbital/VIM/Resolved) values | **11** — *this project's entire candidate list* |
| of the eleven, how many carry the pseudocolour bit | **0** — December's queue is expected **entirely on L21's five-parameter branch** |

**And it would not have crashed.** `m8_zeropoint.parallax_zeropoint` already masks anything
outside {31, 95} rather than letting `zpt.get_zpt` raise — M8 built that guard deliberately.
The consequence on release day is therefore **NaN for every queue member**, the arm printing
`no L21 zero-point available … UNCORRECTED` 981 times, and **every companion mass shipping
high by ~3Z/ϖ, 5–10 %**. *A defensive mask turns the raise you were watching for into a
silent total loss.*

**Fixed: `m8_zeropoint.normalise_solved()`** reads the two bits that decide L21's branch —
bit 2 (=4) parallax fitted at all, bit 6 (=64) pseudocolour fitted — and ignores the rest,
because the extra bits say what *else* was fitted, not which colour quantity the astrometry
used. Verified: **a strict no-op on DR3's 3/31/95**; `--selftest` still reproduces the
sibling project's pinned **−0.028661 mas** anchor; a DR4-style NSS value **2079 now returns
exactly the Z that 31 returns**, where it previously returned NaN.

### 2c. The prediction, frozen

`out/m9_zeropoint_prediction.csv` — L21's Z for all 981 queue members, so December compares
against a written-down number rather than a fresh run:

| | |
|---|---|
| queue rows with all five L21 inputs | **981 / 981** |
| correctable (inside the validity box) | **979 (99.8 %)** |
| Z over the queue | median **−35.47 µas**, p10 −43.52, p90 −23.66, range −52.46 … −2.01 |
| branch | 971 five-parameter, 10 six-parameter *(on DR3; on DR4 expect ~all five-parameter, §2b)* |

### 2d. The decision rule, and which one wins

With `D = bias_DR4 − Z_L21` in µas, ρ = Spearman(bias_DR4, Z_L21), NMAD the robust scatter
of D — **thresholds fixed 2026-08-24, before DR4 exists**:

| verdict | condition | what the pipeline does |
|---|---|---|
| **AGREE** | \|median D\| ≤ 10 µas **and** ρ ≥ 0.5 **and** NMAD ≤ 20 µas | use **DR4's column**; M8's ≤ 2 µas DR3 residual bound may be quoted as **carried** |
| **OFFSET** | \|median D\| > 10 µas, ρ ≥ 0.5, NMAD ≤ 20 µas | use **DR4's column**; the offset is the DR3→DR4 recalibration and is expected. L21's bound does **not** carry |
| **UNCORRELATED** | ρ < 0.5 **or** NMAD > 20 µas | use DR4's column, **flag every mass, quote both** |
| **CONVENTION FLIP** | ρ ≤ −0.5 | **STOP. Correct nothing.** |
| **UNUSABLE** | absent, or null for > 50 % of the queue | fall back to **L21**, record the ≤ 2 µas bound as **UNVERIFIED for DR4** |

**Which one wins is decided now: DR4's own column, wherever it is usable.** Three reasons
in order — (1) it is computed on the very astrometric solution it corrects, while L21 is
calibrated on EDR3/DR3, a different solution with half the time baseline; (2) the effect on
a mass is 3Z/ϖ, a **distance** effect, and DR4's binaries reach further, so a correction
calibrated on a nearer sample is exactly the wrong approximation; (3) a mass on the
release's own convention is reproducible by anyone holding the release. **The single
exception is CONVENTION FLIP**, where neither is used, because applying the wrong sign
*doubles* the error instead of removing it.

### 2e. The rule has been run — 6/6

Six declared synthetic bias columns through `--compare`, each required to return its
declared verdict:

| scenario | declared | got | |
|---|---|---|---|
| DR4 = L21 exactly | AGREE | **AGREE** (ρ 1.000, NMAD 0.0) | ✓ |
| DR4 = L21 + N(0, 5 µas) | AGREE | **AGREE** (ρ 0.813, NMAD 5.0, median −0.4) | ✓ |
| DR4 = 0.7 × L21 + N(0, 5 µas) | OFFSET | **OFFSET** (median +10.3, ρ 0.678) | ✓ |
| DR4 = a random draw with L21's spread | UNCORRELATED | **UNCORRELATED** (ρ −0.04) | ✓ |
| DR4 = −L21 | CONVENTION FLIP | **CONVENTION FLIP** (ρ −1.000) | ✓ |
| DR4 present for 20 % of the queue | UNUSABLE | **UNUSABLE** (80.9 % null) | ✓ |

**And the rehearsal earned its keep on the first run.** The sign-flip scenario reported a
71 µas difference as worth **0.01 %** of a companion mass — a factor-1000 unit error
(`bias` and `Z` are already in mas; a stray `1e-3` converted them to arcsec). Corrected, a
convention flip costs a median **8.4 %** and a worst **88 %** of a companion mass, which is
the number that justifies making it a STOP. *A rehearsal that checks only the verdict and
not the numbers beside it would have shipped that.*

### 2f. One thing to watch for on the day, because it would close M8's last gap

DR4 declares `tentative_parallax_bias` on **`gaia_source`**, whose `astrometric_params` for
an NSS source carries the *orbital* bits — so the published bias may be **for the orbital
solution itself**. That is exactly the quantity Panuzzo said he could not compute (*"we do
not have enough information at this stage to quantify the bias for the preliminary NSS
solutions"*), and the reason M8 had to fall back on EB26's global −36.2 ± 5.3 µas. If it
is there, it supersedes both, and it is a result in its own right.

---

## 3. Task 3 — an external reference for a₀, and the honest close

`scripts/m9_a0_external.py` → `out/m9_a0_external.txt`, `out/m9_a0_{sb9,photocentric,eb26}.csv`.

M8 §1f named the gap precisely: *"SB9 gives P and e. The companion mass goes as a₀³, and no
external reference for a₀ is used anywhere above … An inflation factor measured on P and e
does not license one on a₀."*

### 3a. What exists in the world, established rather than assumed

An exhaustive sweep (VizieR TAP by UCD `phys.angSize.smajAxis` and by every column
description containing "photocentr", plus the non-VizieR catalogues) leaves **exactly
these**, and every one was re-pulled and re-measured here with this repo's own tooling:

| route | what it publishes | n | independent of Gaia? |
|---|---|---|---|
| **Hipparcos DMSA Part O** — ESA 1997, SP-1200 Vol. 10, VizieR `I/239/hip_dm_o` | **a₀ [mas] + e_a0**, the photocentric orbit | 235 orbits (231 with e_a0) | **yes** — Hipparcos photons, 1989–93 |
| **ORB6 grade 9** — Hartkopf, Mason & Worley 2001, AJ 122, 3472; USNO, fixed-width over anonymous HTTPS | grade 9 = *astrometric binary* = a photocentric orbit | 4,051 orbits, **551 grade-9**, 495 with an a₀ and an error | **yes**, but see below |
| **SB9** — Pourbaix et al. 2004, A&A 424, 727 | K₁, P, e ⇒ **a₁ sin i** (not a₀) | 5,099 orbits | **yes** — ground-based spectroscopy |
| **El-Badry et al. 2026** joint astrometry+RV | **å₀ with intervals** | 41 systems (8 in the arXiv preview) | **no** — a₀ is fixed by Gaia's own A,B,F,G |
| van Leeuwen 2007 (`I/311`) | accelerations only | — | **no a₀ anywhere in I/311** |
| DEBCat (`V/152/debcat`) | absolute dimensions of EBs | 195 | **0 matches** to NSS astrometric orbits — structural: near-equal flux drives a₀ → 0 |
| TRAP (`J/A+A/682/A12`, 49,530 binaries) | relative-orbit *a* | large | **derived from Gaia DR3 NSS** — zero independent photons |

### 3b. Route 1 — the photocentric catalogues, and they overlap

After a 2″ positional match to DR3 NSS orbital solutions and the same-orbit period gate:

| | matched | gated | |
|---|---|---|---|
| HIP-DMSA/O | 27 | **18** | + a₀ > 0 and a published e_a0 |
| ORB6 grade 9 | 51 | **34** | provenance of the matched rows: `Ren2013` 11, **`HIP1997d` 11**, `Pbx2000a` 4, `SaJ2011` 2, `Gln2007` 2, `Jnc2005` 2, `Trr2011` 1, `SaJ2013b` 1 |
| **union** | | **36 unique systems** | **16 appear in both** |

**The two catalogues are not independent of each other, and the code proves it rather than
assuming it**: most ORB6 grade-9 entries cite `HIP1997d` — the DMSA/O numbers themselves.
The union is smaller than the sum, and it is 36.

### 3c. The measurement, and the number that closes the question

| | |
|---|---|
| n | **36 systems** |
| Gaia σ(a₀)/a₀ | **4.7 %** (median, MC over the published Thiele-Innes errors) |
| external σ(a₀)/a₀ | **13.6 %** (median) |
| **⇒ the reference's error is** | **2.9× the error it would calibrate** |
| median a₀_Gaia / a₀_external | **0.924** [0.882, 1.041] |
| inverse-variance weighted ratio | **0.979 ± 0.004** (5.6 σ from 1) |
| median \|z\| (both errors combined) | **0.74** ⇒ implied inflation **1.10** (1.00 = errors honest) |
| within 1 σ | 21/36 = **58 %** (expect 68) |

**And the power, simulated rather than asserted** — draw 36 systems with the *observed*
σ ratio, inflate Gaia's error by f, ask how often the median |z| beats its own f = 1 95th
percentile:

| f | 1.4 | 2.0 | 3.0 | 4.0 |
|---|---|---|---|---|
| **power** | **10 %** | 21 % | 56 % | 84 % |

> **The honest close: no adequate external reference for a₀ exists, and here is the number
> that says so.** The best reference in the published literature is **2.9× worse than the
> quantity it would calibrate**, and it has **10 % power** against M8's ×1.4. It could only
> ever flag a catastrophic ×3–4 error, and then barely. **a₀'s error bar is uncalibrated
> externally and will not be calibrated before December.** That is what the ×1.4 does not
> cover, and it must be said in the same sentence the ×1.4 is said in.

**What it does close.** The route constrains a₀'s **scale** to a per cent or two, and that
is worth having: **0.979 ± 0.004**. Taken at face value a 2 % a₀ deficit is a 6 % companion
mass. **It should not be taken at face value, and the reason is measured, not waved at.**
Two alternatives predict the same sign:

* **Eddington bias** — near-threshold Hipparcos-era detections are biased high, so the
  deficit should shrink as the external S/N rises. It does: low-S/N half median ratio
  **0.917**, high-S/N half **0.946**, Spearman ρ = **+0.241** — *the sign predicted, and
  p = 0.156, so not significant at n = 36.*
* **The photocentre is band-dependent.** A red secondary contributes more light in G than
  in Hp, so β is larger in G and a₀ is **genuinely** smaller in G. That is astrophysics,
  not error.

Neither can be separated from a real Gaia offset with 36 systems, and all three have the
same sign. **The deficit is therefore not attributed to Gaia here.**

### 3d. Route 2 — SB9, one-sided and fully external

For a spectroscopic binary the radial velocities alone fix a₁ sin i = K₁P√(1−e²)/2π. Gaia
independently gives a₀ and i from the Thiele-Innes elements. The photocentre identity
a₀ = a_rel(B − β) with β ≥ 0 gives **a₀ ≤ a₁ for every system, with no astrophysical
escape** — so the test is one-sided and every luminous secondary makes it *weaker*, never
falsely positive.

`AstroSpectroSB1` solutions are joint astrometry+RV fits — Gaia's own RVS supplies K₁
inside the solution that produces a₀ — so they are **excluded from the primary sample** and
reported as the circular control.

| | n | median R = (a₀ sin i)/(a₁ sin i) | R > 1 at all | over-run above 1 at 1σ / 2σ / 3σ |
|---|---|---|---|---|
| **PRIMARY** astrometry-only | **53** | **0.968** [0.858, 0.991] | 32.1 % | **5.7 % / 1.9 % / 1.9 %** |
| CONTROL `AstroSpectroSB1` | 52 | 0.964 [0.917, 0.999] | 36.5 % | 5.8 % / 1.9 % / 0.0 % |
| *(expected under honest errors)* | | ≤ 1 | | *15.87 % / 2.28 % / 0.14 %* |

The over-run is **at or below expectation at 1σ and 2σ**, so there is no evidence of an a₀
error-bar failure in the tail either. The single 3σ over-run is one system,
`5076269164798852864` (R = 2.06 ± 0.22, 4.7σ, an `OrbitalTargetedSearch` with a₀ = 8.2 mas
against K₁ = 1.5 km/s) — a mismatched orbit or a bad a₀; it is named, not swept.

### 3e. Route 3 — El-Badry+2026, and a correction to how it is read

EB26 publish å₀ with intervals from joint astrometry+RV fits. **It is not photon-
independent** — their Gaia term is a multivariate Gaussian on the Thiele-Innes elements, so
a₀ is Gaia's — but it is a different pipeline with RV information Gaia does not have. On the
eight preview rows:

| | |
|---|---|
| median a₀_Gaia / a₀_EB26 | **0.9975** |
| median \|z\| (both errors combined) | **0.40**, 6/8 within 1 σ |

> **A landmine, and it is the kind that produces a headline.** Computed the obvious way —
> against **EB26's error alone** — the same table gives median |z| = 2.95, only 1/8 within
> 1 σ, and Gaia BH1 at **+24.8 σ**. Combining both errors, as a z-score must, BH1 is
> **+1.6 σ** and the sample is unremarkable. **A z-score against one side's error is not a
> z-score.** The a₀ ratio for BH1 is 13.2 % either way, which cubes to 45 % in mass and is
> worth its own sentence — but it is a 1.6 σ difference, not a 25 σ one.

---

## 4. Task 4 — the front, closed

### 4a. Runbook

`DR4-DAY-RUNBOOK.md`, rewritten in seven places:

1. **Header** — the measured full-chain block, and the four scale-only defects named.
2. **§3.3** — a one-command driver, `scripts/m9_december_analysis.py`, which runs the seven
   pre-registered commands in the frozen order with the frozen flags, does the regression
   byte-identity check, applies the negative-control veto and writes `dec_labels.csv`
   (with the `keep_default_na=False` header), `dec_runs.csv` and `dec_analysis.txt`. **It
   decides nothing**: where the registration determines no label it emits the label *and*
   the defect code. If it ever disagrees with the seven commands, the commands and the
   pre-registration win.
3. **§3.4** — the December refit command replaced (`--queue`, not `--ids`), with what the
   old one did.
4. **§3.4** — the ⚠⚠ block on the guard column's value set, and the five-verdict
   zero-point decision table with its 6/6 rehearsal.
5. **§3.4 caveat 1** — a₀ has **no** external error calibration; the ×1.4 is P and e only.
6. **Six new failure branches** — the `os.replace` sharing violation, the lost timings, the
   `--ids` KeyError, the zero-point vanishing on all of DR4, the FoV-vs-CCD transit units,
   and a "pooled" arm that is secretly the primary because `eb26.v1.csv` was not in the store.
7. **A new closing section** — the complete day-one command sequence with measured timings,
   the **first-24-hour** and **first-72-hour** checklists, and the open items that are
   Matthew's.

### 4b. The rehearsal, re-run with every M9 change in

`scripts/rehearse_dr4_day.py`, after the harness, the zero-point module and the refit arm
were all modified: **all nine stages green in 41 s.** Stage D acceptance PASS, stage F
PASS (3/3 kept, 9/9 demoted, max |Δf2| vs the M3 prototype **0.0050**), stage I
schema-validated. The plan-B ranged pull resumed from its 94 cached chunks for the
**seventh** time.

### 4c. Frozen artifacts

Verified with `git status` at close: configs **v1–v6 untouched**, schemas v1/v2 untouched,
`out/verdicts/*` and `out/verdicts_v2/*` untouched, every M2–M8 result file untouched. The
chain driver additionally hashes thirteen of them **before and after every run** and prints
the check, so an out-dir leak (M8 landmine #4) is caught by the driver rather than by git
at close. It reported **13/13 unchanged**.

**One file legitimately moved, and it is named so nobody reads it as a violation:**
`out/rehearsal_timings.csv` is the rehearsal's live output and is *rewritten* by every run
— M8 rewrote M7's, M9 rewrites M8's. Only the seconds changed; **all nine statuses are
identical and stage F still reproduces max |Δf2| = 0.0050 against the M3 prototype.**

**No config v7.** M9 changed no selection, no screen, no threshold, no flag and no
membership. Two *code* defects were fixed and one *rule* was written down; none of them
moves a number the config records. M7 declined to write a config for the same reason and
was right to.

### 4d. The pre-registration

**Not edited. Not amended. The variant log is still empty.** M8's four gaps and the D1/D2
interpretation note remain exactly as M8 wrote them, and they remain Matthew's. **GAP-4 is
the one that changes an outcome** — under §4's literal reading D4 comes back
`UNDERPOWERED` where the difference reading gives `NULL`, 11 occurrences, unanimous — and
until it is ruled, December reports both readings. The M9 chain run reproduced it: D4 came
back `UNDERPOWERED` with `decisive_by_diff = True`, carrying the `GAP-4` code, exactly as
M8 predicted.

### 4e. What the chain's own labels said, and why it is a check and not a result

The rehearsal store's verdicts are donor-determined, i.e. independent of every metric, so
the pre-registered expectation is a null. What came back on 229 + 705:

| test | analysis | n | Holm p | label | |
|---|---|---|---|---|---|
| D1 | primary | 103 + 330 | 1.000 | `UNDERPOWERED` + **GAP-4** | the footprint cap; `decisive_by_diff` = True |
| **D2** | primary | 219 + 668 | 0.971 | **`NULL`** | min detectable AUC **0.575** vs the effect under test 0.659 — M8's central promise, executing through the real chain |
| D3 | primary | 219 + 668 | **0.029** | `DIRECTION REVERSAL` | AUC 0.563 against a pre-registered AUC < 0.5 |
| D4 | primary | 219 + 668 | 0.104 | `UNDERPOWERED` + **GAP-4** | |
| D1/D2/D3 | pooled | 119+343 / 261+691 | — | `POOLED: UNINTERPRETABLE (diluted)` ×3 + GAP-2 | the pooled arm is genuinely pooled — the EB26 rows are in the store |

**And the D3 reversal was falsified rather than explained away.** A store whose verdicts
are donor-determined is independent of every metric by construction, so a Holm-significant
reversal is either chance or a bug, and *"it must be chance"* is not a check. **Declared
control: rebuild the fixture at a different seed (20261203) and re-run.** Result — D3
comes back **`NULL` at AUC 0.506, Holm p 1.000**, and so do D1 and D2:

| seed | D1 primary | D2 primary | D3 primary | D4 primary |
|---|---|---|---|---|
| 20261202 | UNDERPOWERED (GAP-4) | **NULL** | **DIRECTION REVERSAL** (0.029) | UNDERPOWERED (GAP-4) |
| **20261203** | **NULL** | **NULL** | **NULL** (p 1.000, AUC 0.506) | UNDERPOWERED (GAP-4) |

**The reversal is a chance realisation of one donor draw, not a property of the code** —
and the second seed delivers the thing this project has spent five milestones trying to
earn: **three simultaneous pre-registered NULLs, all DECISIVE, out of the real production
chain.** The reversal is still worth recording, for one reason: it is what a chance
reversal looks like coming out of the real machine, and **the label machinery refused to
call it a confirmation.**

**A bonus illustration of GAP-4, for free.** D1 reads `UNDERPOWERED` at one seed and
`NULL` at the other with the same test and almost the same n — because
`min_detectable_rate` is evaluated against the **observed** baseline (0.200 vs 0.150),
which is exactly the ambiguity GAP-4 names. **The label of a rate test can change with a
resample of the same null.** That is the strongest argument yet that GAP-4 needs ruling.

---

## 5. Files

| artifact | what |
|---|---|
| `scripts/m9_full_chain.py` | the four-stage chain driver, the frozen-hash guard, and the kill-and-restart resume test |
| `scripts/m9_dec_scale_fixture.py` | the December-scale epoch-astrometry fixture, its declared model and its rule-fired assertion |
| `scripts/m9_transport_leg.py` | M7's phase B as a chain stage, into a cache root of its own so the fetch is real |
| `scripts/m9_december_analysis.py` | **§3.3 as one command** — the seven pre-registered commands, the regression check, the veto and the labels |
| `scripts/m9_zeropoint_crosscal.py` | the `astrometric_params` decode, the frozen L21 prediction, the five-verdict decision rule and its six-scenario rehearsal |
| `scripts/m9_a0_external.py` | SB9's one-sided a₀ test, the HIP-DMSA/O ∪ ORB6-g9 photocentric comparison, the power simulation, and the EB26 read |
| `out/m9_chain/m9_chain_result.json`, `…/m9_resume_test.json`, `…/dec/` | task 1 — the chain, the kill-and-restart test, and December's own label file |
| `out/m9_chain/seedctl_store/`, `…/seedctl_dec/` | the seed-variation control that falsified the D3 reversal (§4e) |
| `out/m9_chain/transport_ledger.csv`, `…/transport_timings.csv`, `…/stage1_transport{,.pre-lock}.log` | the live transport leg, including the crash that found DEFECT M9-3 |
| `out/m9_zeropoint_crosscal.txt`, `out/m9_zeropoint_prediction.csv`, `out/m9_astrometric_params_decode.csv` | task 2 |
| `out/m9_a0_external.txt`, `out/m9_a0_{sb9,photocentric,eb26}.csv`, `out/m9_a0_external.json` | task 3 |
| `data/hipparcos/I_239_hip_dm_o.parquet`, `data/orb6/orb6orbits.{txt,parquet}` | the two new external inputs, both live-pulled and cached |
| `out/verdicts_dec_rehearsal/` | the December-scale rehearsal store — **never** `out/verdicts/` |
| **modified** | `scripts/epoch_vet_harness.py` (the `os.replace` retry, the per-batch timings flush, `LedgerLock`), `scripts/orbital_refit_arm.py` (`--queue` and its December path, the empty-comparison guard), `scripts/m8_zeropoint.py` (`normalise_solved`), `DR4-DAY-RUNBOOK.md`, `STATUS.md` |

---

## 6. Corrections and new landmines

1. **A pre-registered command is only as executed as its least-run line — and the line
   nobody runs is the one against the input that does not exist yet.** M7 and M8 both ran
   the refit arm, on the trio, which is exactly the input that hides the fact that `--ids`
   cannot read a December id. M8 found the identical shape in the D4 argparse line.
   *Rehearse against the input's SHAPE, not against the input you have.*
2. **A defensive mask turns a raise into a silent total loss.** `parallax_zeropoint` masks
   non-{31,95} guard values rather than letting `zpt.get_zpt` raise — deliberately, and it
   is the right design. On DR4 it would have returned NaN for all 981 rows and printed a
   per-source warning the runbook already calls a STOP. **The warning nobody reads 981
   times is not a stop.** Count them and gate on the count.
3. **`os.replace` is atomic on Windows but not immune to a sharing violation.** WinError 5
   killed a 981-source run at source 360. Retry; and exclude the cache directory from
   real-time scanning.
4. **The ledger checkpointed every batch and the instrumentation did not.** A crash lost
   every per-batch timing — the data needed both to diagnose the crash and to read the
   day's throughput. *Anything you would want after a crash must be flushed before it.*
5. **The resume contract is only true of one writer, and nothing enforced it.** Two runs on
   one ledger produced 440 rows for 260 sources and a restart that under-reported its own
   progress by 140. A lock file costs nothing. **A shell reporting a background job as
   finished does not mean the detached process died.**
6. **A control that does not change what the test reads is worse than none — second
   occurrence, different mechanism.** The fixture's INCONCLUSIVE arm never fired because
   **a raw epoch row is a FIELD-OF-VIEW transit and the gate is on CCD transits, ~8.5×
   more.** Caught the same way M8 caught its own: the arm's numbers were indistinguishable
   from the arm it was meant to differ from.
7. **A z-score against one side's error is not a z-score.** Against EB26's error alone, Gaia
   BH1's a₀ sits at **+24.8 σ**; with both errors combined it is **+1.6 σ**. The first
   number is a headline and it is wrong.
8. **A rehearsal that checks the verdict and not the numbers beside it will ship a unit
   error.** The zero-point cross-calibration's six scenarios all returned their declared
   verdict while reporting a 71 µas convention flip as worth 0.01 % of a companion mass —
   a stray `1e-3`. The true cost is a median **8.4 %** and a worst **88 %**.
9. **Two "external" catalogues can be the same measurement.** 16 of the 36 matched
   photocentric orbits appear in both HIP-DMSA/O and ORB6 grade 9, because most ORB6
   grade-9 entries cite `HIP1997d`. Check the provenance column before adding two samples.
10. **An external reference can be worse than the thing it calibrates, and you have to
    measure that before quoting it.** σ(a₀)_external/σ(a₀)_Gaia = **2.9**, power against
    ×1.4 = **10 %**. A null from a route with 10 % power is not evidence of correct errors;
    it is evidence of nothing, and saying which is the whole difference.
11. **DR4's `astrometric_params` binary column has at least one typo** in the draft data
    model (6175 is printed with 4127's bit string). **The decimals are the data.**
12. **A "pooled" analysis on a store with one producer is the primary analysis wearing a
    different label.** The first chain run's pooled numbers were identical to its primary's
    because `eb26.v1.csv` was not in the rehearsal store. The pooling code path was never
    exercised and nothing said so. Fixed: the chain's preflight copies the frozen EB26
    file into the rehearsal store, and the final run's pooled arm is genuinely pooled
    (261 + 691 against the primary's 219 + 668).
13. **astroquery leaves a `temp_<timestamp>/` directory in the CWD for every
    `Gaia.load_data` call**, holding a second copy of the payload, and never removes it.
    M6 landmine #8 caught the habit on `dump_to_file`; this is the same habit on the normal
    path. At DR4's 50.9 KiB/source and batch 20 that is ~1 MB per batch, so a 50-batch
    December run leaves **~50 MB of duplicated payload and 50 untracked directories in the
    repo root**, on top of the harness's own cache. `DataLinkSource.fetch` now removes only
    the directories that call created (snapshot before, diff after — never a blanket
    `temp_*` sweep), and `.gitignore` covers the rest.
14. **"It must be chance" is not a check.** A Holm-significant DIRECTION REVERSAL came out
    of a store built to be null. The reasoning that it had to be chance was correct and it
    was still not evidence; **re-drawing the fixture's seed is** — and it came back
    `NULL` at p = 1.000 (§4e). A one-line control that takes seven minutes beats a
    paragraph of argument.
15. **`--verdicts <absolute path outside the repo>` returns NOT TESTABLE for everything.**
    Running the December driver against a store in a scratch directory gave seven
    `NOT TESTABLE` labels — a *plausible-looking* answer to a broken input. It was caught
    only because the driver counts and prints non-zero exits (5 of 5). **Keep the store
    inside the repo**, and read the exit count before the labels.

---

## 7. Readiness statement

**Proven.** The whole production chain runs end to end at December's exact scale — 981
queue members, 219 refits with the zero-point applied, a schema-validated v2 store, and the
pre-registered labels — in **7.8 minutes of compute** on top of transport, with **0
duplicated and 0 lost rows across a SIGKILL at every stage boundary**, a nine-stage
rehearsal green in **41 s**, the BH1/BH2 acceptance and the Gaia BH3 refit acceptance both
passing, and every frozen artifact byte-identical. December's zero-point comparison is a
written-down prediction with five pre-registered verdicts that have been **run 6/6**, and
the correction that wins is chosen in advance.

**Assumed.** That DR4's `nss_two_body_orbit`, `gaia_source` and DataLink behave as the
draft data model and the pre-release file say they will — the schema, the
`EPOCH_ASTROMETRY` retrieval type (which the live service still rejects), the **50.9
KiB/source** payload, and near-complete epoch-astrometry coverage of the queue; that
Lindegren+2021, calibrated on EDR3/DR3, is a usable fallback for DR4 astrometry, with its
≤ 2 µas residual bound explicitly **unverified for DR4**; that the ×1.4 error inflation
measured on P and e is indicative for a₀, **which is assumed and not shown** — a₀'s error
bar has no external calibration and the best available reference has 10 % power to give it
one; and that the fixture's donor-driven verdict split is a fair stand-in for December's,
which only December can settle.

**Could still go wrong on the day.** The archive: today's live DataLink ran **4–8× slower
than M7's median**, and if DR4 serves epoch astrometry for materially less than the whole
queue that is the day's biggest finding and changes everything downstream. The schema: a
rename not in the map, a `solution_type` string that does not exist yet, or
`tentative_parallax_bias` arriving null — each has a branch, none has been tested against
the real thing. The registration: **GAP-4 is unruled**, so whether December may claim a D4
null still turns on which sentence of §4 is read, and that is Matthew's call, not the
day's.

---

## 8. Recommended M10 — there isn't one

**The front is ready and waiting for 2 December.** Every recommendation M8 left that an
agent may act on has been executed; what remains is either Matthew's (the four
pre-registration amendments and the GAP-4 ruling; the two free accounts) or the data
itself. Building more machinery now would add code that release day has not asked for, and
"release day needs no new code and no new decisions" is the condition this milestone was
written to reach.

Three things are worth doing **only if** the front is reopened before December, in this
order:

1. **Re-run `rehearse_dr4_day.py` on 1 December** and require nine green. It is 41 seconds
   and it is the only check that the archive, the local maps, the venv and the code still
   agree.
2. **Exclude `data\epoch_cache\` from real-time antivirus scanning** — an operational step,
   not a code change, and it removes the failure mode that killed a 981-source run.
3. **A ~90-source `corr_vec` pull for the a₀ comparison samples.** `data/dr3_nss_corrvec.parquet`
   was pulled for the class-III + retrieval sets only (M3), and it covers **0 of the 36**
   matched photocentric systems and **2 of the 53** SB9 astrometry-only ones — verified,
   not assumed. So the σ(a₀) in §3c and §3d is an uncorrelated-Thiele-Innes approximation
   and is labelled as one. A pull would sharpen the *scale* measurement; it would **not**
   change the power verdict, which is set by the reference's own 13.6 % errors and not by
   ours.

Human TODOs unchanged: the pre-registration amendments (Matthew), and the Gaia Archive +
NOIRLab Data Lab accounts (both free, neither on any critical path).
