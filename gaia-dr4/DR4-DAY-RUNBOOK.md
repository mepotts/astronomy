# DR4-DAY-RUNBOOK — 2026-12-02

*The operational sequence for release day, rehearsed end-to-end against DR3 on 2026-08-16
(`scripts/rehearse_dr4_day.py`, timings in `out/rehearsal_timings.csv`; M3 doc §3).
Config: `queries/dr4-triage-config.v5.json` (selection/screen frozen since M2; v2 added the
covariance probability method + dust tier; v3 (M4) added the Bayestar19 far-star
arbitration and the X-ray caution-tag policy; v4 (M5) added the all-sky
Vergely+2022 far-star arbitration, the measured activity policy — no activity flag — and
one astrometric-quality caution flag; **v5 (M6, 2026-08-21)** adds the day-one verdict
record schema, the epoch-vet harness policy with its measured throughput, and the
`flag_astrom_quiet` decision. Membership and all cuts unchanged since M2: 949.
**M7 (2026-08-23) wrote no config**: it changed nothing about the list, the screen or any
flag, so v5 stands.)
Everything below is anonymous-TAP-safe; if the
Gaia Archive account exists by then (Matthew's TODO), the async branch gets a longer rope,
nothing else changes.*

**Standing rules.** Politeness gaps ≥ 0.5 s between sync calls; every bulk pull ends with
an exact `COUNT(*)` guard; nothing is published from a partial pull; negative results are
results. All commands below run from `gaia-dr4/` with `.venv\Scripts\python.exe`.

> **⏱ THE DAY-ONE CLOCK, MEASURED (M7, 2026-08-23).** The 981-row queue is adjudicated in
> **2.1 h at 468 sources/hour** — a *measured* central value where M6 had only a band.
> A band remains (**1.2–7.8 h, 126–803/hour**) but it is archive weather with every edge
> an observed archive state, and a **sustained** run varied by only ± 8 % today. Measured,
> not projected: a 981-source dry run through the production harness at fixed batch 20 with
> payload varied 4.7× separates the two cost terms M6 could not, at 13.5 σ. Details and
> the weather bracket in **Phase 3.0**.
>
> **📌 THE DECEMBER ANALYSIS IS PRE-REGISTERED AND FROZEN:**
> [`PREREG-2026-08-23-december-discriminators.md`](PREREG-2026-08-23-december-discriminators.md).
> Read it **before** running anything in §3.3. It fixes which verdicts enter each test,
> how the two scopes may and may not be pooled, the decisive sample sizes, the Holm family
> sizes, and what counts as a positive, a null and an underpowered result — all written
> while zero December verdicts existed. It is not editable; later work appends to its
> variant log only.

---

## Phase 0 — the moment the archive answers (T+0, ~15 min)

0. **Is the archive answering at all?** (M5, 2026-08-18 — learned the hard way.)
   Fire a trivial indexed probe (`SELECT TOP 1 source_id FROM …gaia_source WHERE
   source_id = <BH1>`) at each endpoint, 45 s timeout, and use the first that
   answers **and honours `FORMAT=csv`**:

   | endpoint | note |
   |---|---|
   | `https://gea.esac.esa.int/tap-server/tap/sync` | ESAC, primary — the only one that will carry DR4 on day one |
   | `https://gaia.ari.uni-heidelberg.de/tap/sync` | ARI Heidelberg partner mirror; CSV, answered in 0.6–2 s all afternoon while ESAC was timing out |
   | `https://gaia.aip.de/tap/sync` | AIP partner mirror; **ignores `FORMAT=csv` and returns VOTable** — parse accordingly or skip |

   On 2026-08-18 ESAC alternated between 30–80 s replies, HTTP 500 and 90 s
   read-timeouts *on one-row indexed queries*; the mirrors were unaffected.
   **Mirror validation gate before trusting one**: re-pull a handful of columns
   you already hold from ESAC (`ruwe`, `phot_g_mean_mag`, `ipd_frac_multi_peak`
   for the EB26 76) and require an exact match — ARI reproduced ESAC to
   0.000e+00 relative on 2026-08-18 (`scripts/m5_pull_activity_columns.py`).
   **Caveat for December**: the mirrors host DR3 and will not have DR4 on
   release day. They are a fallback for the *DR3-side* work (calibration
   fixtures, cross-checks), not for the DR4 pull. Every sync helper now retries
   6× with backoff (`scripts/pull_dr3_nss_orbits_ranged.py`,
   `scripts/rehearse_dr4_day.py`) — a 94-request pull cannot survive a
   no-retry policy on an archive in this state, and the M5 rehearsal needed
   three attempts to get `TAP_SCHEMA.schemas` to answer at all.
   **Where failover is allowed, and where it is not** (encoded in
   `rehearse_dr4_day.py` as two different helpers): **schema introspection MAY
   fail over** — "does column X exist in this release" is answered identically
   by any host serving the same release — but **the data path MUST NOT**, because
   the pull has to be reproducible against one archive and because on release day
   only ESAC has DR4. If ESAC's data path is down, you wait; the resumable ranged
   pull means waiting costs nothing already fetched.

1. **Schema pin** (rehearsed: 6–8 s):
   `SELECT schema_name FROM TAP_SCHEMA.schemas` → confirm the real DR4 prefix
   (`gaiadr4.` is an ASSUMPTION — dr3-to-dr4-tables.md).
   Then `TAP_SCHEMA.columns` for `nss_two_body_orbit`, `gaia_source`, `nss_masses`,
   `dr3_neighbourhood` and diff against `queries/dr3-to-dr4-tables.md`.
   **Check `corr_vec` exists and its shape convention; check the solution-type strings
   with a `GROUP BY solution_type` (the draft list has no `*TargetedSearch*`; M2 found
   198 solutions hiding in `*Validated` variants on DR3 — assume the same trick).**
2. **Patch the canned queries** (rehearsed: the machine patch ran and probed live in 2 s):
   apply the rename map to `queries/01*.sql`, `02*.sql`, `03*.sql`; probe each with
   `TOP 5` sync (expect HTTP 200). Patch lessons already encoded: strip inline `--`
   comments before token surgery; guard column tokens with `(?!\w)`.
3. **Resolve stored DR3 ids** through `dr3_neighbourhood` before ANY use (BH1, BH2, the
   949 v2 candidates, the 239 retrieval bin, the 12 pre-release sources). No code may
   *depend* on ids changing or on ids being stable (M2 correction #1).

## Phase 1 — the NSS pull (T+15 min; plan A ≤ 90 min, plan B ~35–40 min)

**Plan A — one async job** (`scripts/pull_dr3_nss_orbits.py` patched to DR4 names):
submit, poll every 60 s, **abandon at T+30 min if still QUEUED** (M2 operational finding:
the anonymous queue sat > 100 min on a Saturday evening with zero load feedback; assume
release day is worse).

**Plan B — the ranged sync pull** (`scripts/pull_dr3_nss_orbits_ranged.py`; run at full
scale twice — M2 production ~35 min Saturday evening, M3 rehearsal 38.7 min Sunday
daytime — producing **byte-identical parquets**, same sha256):
1. 3-s server-side bucket histogram (`FLOOR(source_id/2^52)`) — **tile the id space, never
   skip "empty" buckets** (ADQL computes the floor in double precision; ids past 2^53
   round and rows can hide in gaps — M2 landmine #5);
2. pack ranges ≤ 1,900 expected rows, pull each with an indexed predicate, 0.5 s gaps;
   any range returning ≥ 2,000 rows = possible truncation = ABORT;
3. assemble; **dedupe on (source_id, solution_type), never on source_id alone** (98 DR3
   sources carry two genuine orbits; DR4 must be assumed multi-row too — M2 landmine #4);
   resolve the `nss_masses` LEFT-JOIN fan-out by `combination_method` preference;
4. hard-check assembled rows == live exact `COUNT(*)`.

DR4 scale note: DR3's six types were 169k rows; DR4's NSS catalog is advertised much
larger. Plan-B cost scales linearly (~35–40 min per 170k rows at ~1,800 rows / 25 s per
range); if the
histogram predicts > 1M rows, raise PACK toward the sync cap and expect hours, or split by
solution type and pull `Orbital` first (the triage's bread and butter).

## Phase 2 — triage + covariance probabilities (T+1–2 h, ~15 min compute)

1. **AMRF triage** (`scripts/amrf_triage.py`, rehearsed full-scale: 65 s for 169k rows
   incl. MC, plots and the gate — `out/rehearsal_timings.csv` stage D): config v5
   parameters (selection identical to v4/v3/v2/v1) — P ∈ [10, 2200] d,
   Halbwachs gates, σ_TI² ≤ 36, boundary ×1.15, screen sig > 10 + F2 mag-split; flags
   never cuts; **acceptance gate = BH1 + BH2 land class III** (their DR4 solutions exist
   by construction; if the gate fails, STOP — the config or the schema diff is wrong,
   not the sky).
2. **corr_vec pull for the class-III + retrieval sets only** (never the full catalog;
   rehearsed: 4,203 rows / 74 s in 11 sync chunks): `scripts/pull_dr3_nss_corrvec.py`
   with the day's candidate ids. **VOTable format** (corr_vec is an array; and the Gaia
   archive upper-cases `source_id` in VOTable — normalize).
3. **Covariance MC** (`scripts/corrvec_probs.py`; rehearsed: 10 s for 4,203 rows):
   Pr(III|corr) per candidate; priority tier Pr ≥ 0.999. Sanity triplet that must hold
   before anything ships: covmat diagonals == published errors; campbell a₀/σ(a₀) vs
   archive significance median ≈ 1.000; BH1/BH2 Pr = 1.0000.
   σ_TI² ≳ 5 rows: Pr is conservative (M3 §1 tail mechanism) — rank, don't drop.
4. **Dust tier** (`scripts/dust_retriage.py`; local maps already on disk, ~3 min):
   Edenhofer ≤ 1.25 kpc; far stars bracketed Edenhofer-floor/SFD; movements logged;
   `binary_masses`→`nss_masses` tier is immune by construction.
   **Far-star ambiguity — arbitrate with a far 3D map, ALL SKY (M5):**
   - `scripts/m5_vergely_south.py` — **Vergely+2022** (CDS J/A+A/664/A174, local
     cubes in `data/dustmaps/vergely2022/`, ~20 s load) covers the whole sky inside
     a 6×6×0.8 kpc box (25 pc) / 10×10×0.8 kpc (50 pc, with an error cube).
     Unit chain in config v4 `extinction_tier.vergely2022_chain`: the cubes are
     A₀(550 nm)/pc, one link to the house scale, `E = A0(550)/2.6798`.
     **Run its pre-registered geometry gate first** — the declared axis convention
     must beat the three corruptions against Edenhofer23 (DR3 dress: ρ 0.966 vs
     0.38–0.41; median E_V22/E_Eden 1.010; 25 pc/50 pc cubes agree 0.977). It writes
     `out/m5_vergely_geometry_gate.txt`; **if the gate fails, the reader is wrong and
     nothing may be written.**
   - `scripts/m4_bayestar_dozen.py` — **Bayestar19** where dec > −30 (local
     `data/dustmaps/bayestar2019.h5`, ~1 min load; chain in v4
     `extinction_tier.bayestar19_chain`). Keep running it: two independent far maps
     agreeing is the whole evidence base. The Argonaut web API is DOWN (HTTP 500,
     2026-08-18) — local file only.
   - Policy either way: best estimate = max(map at the star's distance, Edenhofer
     floor); a row whose class flips inside V22's own ±1 σ is flagged
     `flag_dust_sigma_fragile`, not frozen. `flag_dust_unresolved_south` survives
     only for sightlines outside *every* map box.
   DR3 dress (M5): of 13 ambiguous rows, **12 resolved class-III alive on both
   chains, 0 die, 1 σ-fragile, 0 left unresolved** — B19's 9 reproduced at the
   central value 9/9, and the 4 southern rows M4 could not reach are now closed.

## Phase 3 — the epoch-vet HARNESS, the false-positive killer *and the verdict factory* (T+2 h onward)

**Phase 3 is now a harness, not a loop you drive by hand** (M6):
`scripts/epoch_vet_harness.py`. It is batched, resumable, rate-limit-aware and
instrumented, and it emits **verdict records** in the frozen day-one schema
(`schemas/day1_verdict_record.v1.json`) rather than an ad-hoc CSV. That last point is
what makes 2026-12-03 a re-run instead of a rewrite: the M4 and M5 discriminator tests
take `--verdicts` and consume harness verdicts and El-Badry+2026 verdicts through the
same code path.

**The queue is emitted BY THE REHEARSED DRIVER** (M5): `scripts/rehearse_dr4_day.py`
**stage H** calls the shared builder `scripts/m5_day1_queue.py` on the day's own triage
output and writes `epoch_vet_day1_queue.csv` next to the bulletin — nothing to
remember, and the builder itself asserts the BH1/BH2 acceptance before it will write.
The DR3 production copy (dust-corrected membership) is
`out/epoch_vet_day1_queue.v2.csv` (M4's 981-row original stays frozen at
`out/epoch_vet_day1_queue.csv`). Contents: main list + retrieval bin's
Pr ≥ 0.999 members in one ranking — Pr(III|corr)
desc, M₂_min tiebreak — carrying every caution flag (1-yr alias, low-|b|, σ_TI² > 20,
X-ray-active, EB26 verdict, dust-unresolved-south, dust-σ-fragile, **astrom-quiet**).
DR3 shape: 981 rows = 949 + 32;
ranks 1–2 are BH1/BH2 and rank 3 is the EB26-refuted spurious — the loop's first kill.

### 3.0 — probe DataLink, THEN measure it (~7 min)

**First, one source, and read the body of any error.** On 2026-08-21 the live ESAC data
server answered `retrieval_type='EPOCH_ASTROMETRY'` with

```
HTTP 500  Unknown retrieval type: 'EPOCH_ASTROMETRY'
```

for **both** `RELEASE='Gaia DR4'` and `'Gaia DR4_INT4'` — the service does not serve it
yet, and **astroquery 0.4.11 lists `EPOCH_ASTROMETRY` in its client-side
`VALID_DATALINK_RETRIEVAL_TYPES`, so nothing catches this before the request goes out.**
It arrives as a 500, which is exactly what the retry policy is built for; retrying it is
five wasted minutes on a deterministic answer. The harness now reads the body and fails
fast on `Unknown retrieval type` / `Unknown release`
(`scripts/epoch_vet_harness.py::_is_deterministic`). On release day:

```
.venv\Scripts\python.exe -c "from astroquery.gaia import Gaia; ^
  print(Gaia.load_data(ids=[4373465352415301632], data_release='Gaia DR4', ^
  retrieval_type='EPOCH_ASTROMETRY', data_structure='RAW', format='votable').keys())"
```

If it 500s with an "Unknown …" body, the `RELEASE`/`retrieval_type` strings are wrong —
go back to Phase 0's schema pin and find the live values. **Do not start the harness
until one source comes back.**

Then measure the archive **before** committing to a batch size:

```
.venv\Scripts\python.exe scripts\m6_datalink_throughput.py --repeats 1
```

It sweeps DataLink batch sizes against the live service, fits the two transport models,
and reprints the wall-clock projection with *measured* coefficients. **Do this first.**
**But do not re-fit both terms from a batch-size sweep — that is the collinear design M7
had to undo.** The cost model below is already measured; what release day needs from the
probe is ONE number, the day's delivered **KiB/s**, which drops straight into
`t = 2.42 s + 0.215 s/source × n + (KiB in the batch) / rate`. The harness's own first
ten batches give it for free: `out/m6_harness_timings.csv`, `seconds` against served rows.
**A batch-size sweep cannot improve on that and can only re-create the ambiguity.**
Every number below was measured on 2026-08-21 with DR3 `EPOCH_PHOTOMETRY` as a labelled
proxy, because DR4 epoch astrometry did not exist yet; six minutes on release day
replaces the proxy with the real thing.

DR3-day baselines to compare against (`out/m7_throughput_measured.txt`, superseding
M6's `out/m6_throughput_projection.txt`):

| quantity | measured |
|---|---|
| **the cost model** | **`t = 2.42 ±0.81 s + 0.215 ±0.100 s/source × n + 0.1424 ±0.0105 s/KiB × KiB`** (M7, 100 requests, R² 0.878) |
| DataLink per-request overhead, empty request | **0.65 s** (M7, 14 requests that served nothing) — *not* M6's 2.3–6.0 s, which absorbed payload |
| delivered rate | **6.9 KiB/s** (M7, 2026-08-23) vs **1.8 KiB/s** (M6, 2026-08-21) — same service, different weather. Neither is a network: it is server-side work, and it is proportional to the **bytes** |
| run-to-run spread, identical batch-20 requests **over 2.0 h** | 15.2–42.2 s, median 26.9, p90 34.3, **2.8×**, no monotone trend, **0 failures in 60** (M7). M6 saw 3.2× in a few minutes |
| SUSTAINED-run spread (what a 50-batch wall clock sees) | **± 8 %** — the two halves of phase B, 2,626 and 2,236 sources/hour. Single-request extremes average away |
| DR4 epoch-astrometry payload (real, pre-release) | 96.3 KiB/source raw, **50.9 KiB/source zipped** |
| `gaiasupdate` single-star fit, **sustained over 981 fits** | **0.123 s/source = 29,000/hour**, drift −0.011 s per 1000 fits, f2 bit-identical on repeats (M7). Still 60× cheaper than transport |

**Measured day-one throughput at batch 20: 468 sources/hour ⇒ the 981-row queue in
2.1 h.** M6's 125–857 band was a *model* ambiguity — per-source work vs per-byte transport
— created by a probe that varied both together. M7 held the batch size fixed at 20 and
varied the payload 4.7× (batch time then varied 6.0×, where a flat model predicts 1.0×): the per-byte term is **13.5 σ**, the per-source term 2.2 σ, and at
DR4 payload the bytes cost 7.25 s/source against the source term's 0.22 s. **They were
never rivals; they are the two terms of one model.**

What is left is weather, and it is bracketed:

| branch | 981 rows | sources/hour |
|---|---|---|
| best single request observed | 1.2 h | 803 |
| **MEDIAN — the measured branch (2026-08-23)** | **2.1 h** | **468** |
| p90 request | 2.6 h | 371 |
| worst single request observed | 3.2 h | 303 |
| M6's bad afternoon (1.8 KiB/s) | 7.8 h | 126 |
| **10× degraded** — M6's old 78 h branch | **20.2 h** | 49 |

**Read the quantile rows as instantaneous conditions, not achievable wall clocks.** A
50-batch run averages them; the sustained spread measured today was ± 8 %. The rows that
bound a *whole run* are the day-to-day ones — M6's afternoon and the 10× branch.

**M6's 78-h worst case is superseded**: it extrapolated model A from a 2.3 s overhead and
a 1.8 KiB/s rate. Every branch now fits inside 72 h with margin.

**Consequence, and it is the actionable one:** the queue is ranked and the harness
consumes it in rank order, so a slow archive costs **depth, not the headline** — BH1,
BH2 and the EB26-refuted poster child are adjudicated in the first minutes under every
branch. Plan for running out of *hours*, not out of throughput; the harness is
resumable, so 72 h is a checkpoint, not a deadline. **At 468 sources/hour the queue is no
longer the constraint** — what to do with the remaining ~70 h is a depth question, and the
refit arm (§3.4) is the answer.

### 3.1 — run the harness

```
.venv\Scripts\python.exe scripts\epoch_vet_harness.py --source datalink ^
    --queue data\rehearsal\out\epoch_vet_day1_queue.csv ^
    --release "Gaia DR4" --batch 20 ^
    --ledger out\verdicts\harness_dr4day.v1.csv
```

What it does, per batch, in queue-rank order:
1. skip sources already in the ledger and epochs already in
   `data/epoch_cache/<release>/` — **restart is free**;
2. **one DataLink request per batch** (`retrieval_type='EPOCH_ASTROMETRY'`,
   `data_structure='RAW'`) — epoch astrometry is **DataLink-only, not a TAP table**
   (M1 finding #1). Note `gaiasupdate`'s own `from_gacs_datalink()` sends **one id per
   request**; the harness deliberately does not use it;
3. write each served source to its own parquet **atomically** (`.tmp` → `os.replace`),
   so a kill mid-write cannot leave a half-file that looks cached;
4. `gaiasupdate` single-star fit (`6p_constrained_colour`, the DR4-like configuration)
   → the pre-registered verdict rules below;
5. append the verdict records to the ledger and the timings to
   `out/m6_harness_timings.csv`. **Checkpoint after every batch.**

**Pre-registered verdict rules** (config v5 `epoch_vet_policy`; these extend M3's
prototype rule, they do not replace it):

| condition | verdict (scope `orbit_reality`) |
|---|---|
| `n_used < 50` | **INCONCLUSIVE** — too few epochs to adjudicate. *Not* a demotion |
| `\|f2\| > 5` | **CONFIRMED** — epoch-level wobble present → hand to **the orbital refit arm, §3.4** (`scripts/orbital_refit_arm.py`; M7 turned M1's one-source script into a pipeline) |
| `\|f2\| ≤ 5` | **SPURIOUS** — no epoch-level support for the claimed photocentre orbit |
| DataLink served nothing | **NO_DATA** |
| the fit raised | **ERROR**, with the exception text in `notes` — never silently dropped |

Confidence: `r = |f2| / 5`; **HIGH** if `r ≥ 2` or `r ≤ 0.5`, **MEDIUM** within a factor
2 of the gate, **LOW** if INCONCLUSIVE/NO_DATA/ERROR or `n_used < 100`.

Validated end-to-end on the only real epoch astrometry that exists (the 2026-06-26
pre-release file): **3/3 orbit sources CONFIRMED** (Gaia BH3 f2 894.0, HD 114762 186.5,
Gaia-4 31.5), **9/9 quiet sources SPURIOUS** (|f2| ≤ 1.55), all twelve at HIGH
confidence, and every f2 agreeing with M3's prototype to **0.005** — its own printed
precision. That is rehearsal **stage F**.

**Read `verdict_scope` before quoting anything.** A harness verdict answers *"does this
photocentre orbit have epoch-level support?"* (`orbit_reality`). An EB26 verdict answers
*"is there a dark massive companion?"* (`compact_companion`). A harness SPURIOUS and an
EB26 SPURIOUS mean nearly the same thing; **a harness CONFIRMED is weaker than an EB26
CONFIRMED** — orbit real, companion nature unestablished. Pooling the scopes is
asymmetric, so every consumer prints the scope composition of both groups the moment
the store holds more than one.

### 3.2 — the caution crosses (unchanged in substance)

4. **eROSITA cross** (`scripts/erosita_xmatch.py` against the local DR2 catalogs,
   ~4 min): on DR3 this found 30/471 coronal counterparts and 0 accretors. **An X-ray
   match is an activity/spurious-risk tag first, a headline only if log f_X/f_opt ≳ 0.**
   M4 measured the tag against EB26 ground truth (`out/m4_eb26_discriminator_stats.txt`):
   in-footprint detections 2/13 spurious vs **0/16 confirmed** (+ 0/7 other verdicts) —
   direction consistent, but Fisher p = 0.19: **underpowered, NOT a validated
   discriminator; never a cut** (as a cut it would drop 30 in-list rows, 0 of them
   EB26-confirmed but 29 unverdicted incl. the top NS-range candidates). Policy: an
   X-ray match routes the candidate to **epoch-vet-first**, and the bulletin carries
   the flag; the M4 numbers are the DR3 baseline to compare the day's match rate against.
5. **Gaia's own indicators, one column pull, no telescope** (M5,
   `scripts/m5_pull_activity_columns.py` → `scripts/m5_activity_discriminator.py`).
   Three families measured against EB26 ground truth on **all 65** verdicted
   targets (no footprint penalty at all):
   - **chromospheric `activityindex_espcs`: NOT TESTABLE** — it exists for 7 of 76
     EB26 targets (3 confirmed / 1 spurious) and 44 of 1,199 candidates. M4's
     recommendation assumed this axis was all-sky; **it is not.** Pull it anyway
     (it is free), report coverage, claim nothing.
   - **photometric variability: measured underpowered null.** Magnitude-detrended
     Belokurov+2017 eq.-2 amplitude ΔAmp_G gives AUC(spurious > confirmed) = 0.659
     [0.507–0.805], p = 0.035 raw → **0.141 after Holm within the family**; the
     smallest AUC this n can detect at 80 % power is 0.725. The *direction* agrees
     with M4's X-ray direction (spurious are the more active side) — two independent
     activity axes agreeing and neither significant.
   - **astrometric quality DOES discriminate, and points the other way**:
     `astrometric_gof_al` p = 0.0011 (Holm 0.0067), AUC 0.254; `ruwe` p = 0.0083
     (Holm 0.041). **EB26-CONFIRMED hosts are the NOISIER single-star fits** — a real
     massive dark companion makes a big photocentre orbit. Frozen as the single
     caution flag `flag_astrom_quiet` (bottom quartile of `astrometric_gof_al` in
     the day's own main bin) — **tiebreaker only.** Post-hoc caveat carried in
     config v4: controlling for `significance`, G and distance, gof_al retains only
     p = 0.048 and ruwe 0.094, so the flag largely restates the significance tier
     v2 already ranks on. Never quote it as independent evidence.
     **M6 re-asked this on the flag's own operating population** (the verdicted rows
     that are *in* the queue, 40 confirmed / 8 spurious): AUC 0.344, p = 0.17, and the
     thresholded flag at Fisher p = 1.00 — but the smallest effect that population can
     see is AUC 0.80, and the smallest spurious marking-rate the Fisher test can see is
     **0.55**. M5's "0 of 7" is a statement about sample size, not about the flag: at
     the measured 7.5 % marking rate the *expected* catch among 8 spurious rows is 0.6.
     **Decision: CARRY** — unchanged from v4, and the test that settles it is
     pre-registered (§3.3).

### 3.3 — re-ask every discriminator question against the day's own verdicts

> **STOP. Read
> [`PREREG-2026-08-23-december-discriminators.md`](PREREG-2026-08-23-december-discriminators.md)
> first.** It was written and frozen on 2026-08-23, while zero December verdicts existed,
> precisely so that none of the choices below can be made after seeing a p-value. The
> commands here are copied from it; if they ever disagree, **the pre-registration wins**.

This is the milestone's whole point and it needs **no new code**:

```
.venv\Scripts\python.exe scripts\verdict_schema.py --build-eb26

:: PRIMARY -- scope-pure, harness verdicts only. This is the powered analysis.
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py       --verdicts all --scopes orbit_reality --sources epoch_vet_harness --out-dir out\dec\primary
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py  --verdicts all --scopes orbit_reality --sources epoch_vet_harness --out-dir out\dec\primary
.venv\Scripts\python.exe scripts\m6_astrom_quiet_decision.py   --verdicts all --scopes orbit_reality

:: REGRESSION CHECK -- EB26 alone. MUST reproduce the frozen M4/M5 artifacts byte-identically.
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py       --verdicts all --scopes compact_companion --sources elbadry2026 --out-dir out\dec\regression
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py  --verdicts all --scopes compact_companion --sources elbadry2026 --out-dir out\dec\regression

:: SECONDARY -- pooled. POSITIVE results only may be interpreted (see below).
.venv\Scripts\python.exe scripts\m4_eb26_erosita_test.py       --verdicts all --out-dir out\dec\pooled
.venv\Scripts\python.exe scripts\m5_activity_discriminator.py  --verdicts all --out-dir out\dec\pooled
```

`--verdicts all` means "every producer file in `out/verdicts/`". A directory path or a
glob work too — `load_store()` expands all three itself, because **cmd.exe does not
expand wildcards** and a runbook command that only works in one shell is a trap.
**Note what `all` does *not* include: `out/verdicts_v2/`.** The discriminator tests read
the v1 store and need no `refit_*` field, so the refit arm's output cannot perturb them —
which is why the byte-identity regression check above is meaningful. Use
`verdict_schema_v2.load_store('all')` when you want both (it spans `out/verdicts/` and
`out/verdicts_v2/`, upgrades v1 rows on read, and resolves a key present in both in favour
of the v2 row, printing how many it superseded).

**The pooling rule, in one line:** a pooled **significant** result is a *conservative*
positive (it survived the dilution caused by pooling a heterogeneous CONFIRMED group); a
pooled **non-significant** result is **not** evidence of absence and may never be reported
as a null. If the scope-pure primary is underpowered, the answer is "underpowered" — not
"pool and try again".

The sample sizes that settle each open question (`out/m7_prereg_power.txt`, computed with
M5's own power routines), quoted at the EB26 conf:spur ratio:

| question | needs | today | after one harness pass |
|---|---|---|---|
| D2 photometric variability (ΔAmp_G, AUC 0.659) | 71 conf + 39 spur | 42 + 23 | ✓ (~633 + 347) |
| D3 `astrometric_gof_al`, at the **in-list** effect (AUC 0.344) | 73 + 40 | 40 + 8 | ✓ |
| D4 `flag_astrom_quiet`, thresholded (0.30 vs 0.075) | 64 + 35 | 40 + 8 | ✓ |
| D1 X-ray (0.154 vs 0.000) | 49 + 27 **in the eROSITA-DE footprint** | 16 + 13 | ✓ *only if* the split is not extreme — the footprint caps this at ~45 % and throughput cannot fix it |
| chromospheric ESP-CS | ≥ 5 per side with a published index | 3 conf / 1 spur | **report DR4 coverage first — it may still be untestable** |

**Because D2, D3 and D4 clear their thresholds at every plausible split, a
non-significant December result on them is a NULL, not "underpowered"** — the outcome this
project has not yet been able to claim. The six outcome labels and the exact conditions
for each are in §5 of the pre-registration.

`flag_astrom_quiet`'s December decision rule is pre-registered in
`scripts/m6_astrom_quiet_decision.py`, copied into config v5, and restated unchanged in the
pre-registration: **KEEP** if the in-list continuous test reaches p < 0.05 in the M5
direction *and* the thresholded flag beats its own marking rate at Fisher p < 0.05;
**REMOVE** if the in-list test is well powered (smallest detectable AUC ≤ 0.70) and the
observed AUC is consistent with 0.5; **CARRY** otherwise.

**The negative control has a veto.** `phot_g_n_obs` is re-run uncorrected and outside every
family. If it reaches p < 0.05, no D1–D4 positive may be reported as a finding until it is
explained.

### 3.4 — the ORBITAL REFIT ARM: from "the orbit is real" to the orbit and its mass

**This is the headline, and it is now a pipeline** (`scripts/orbital_refit_arm.py`, M7 —
before M7 it was a one-source script and a sentence saying "the BH3 pattern"). It consumes
`CONFIRMED (orbit_reality)` verdicts and produces, per source: an independent Keplerian
orbit from the epoch astrometry, the **M₁-free astrometric mass function**, and a
**companion-mass posterior**, written as verdict-record **v2** so the refit lands on the
same row as the verdict that triggered it.

```
:: acceptance FIRST -- it re-derives Gaia BH3 and must match M1's numbers
.venv\Scripts\python.exe scripts\orbital_refit_arm.py --acceptance

:: then the day's confirmed orbits
.venv\Scripts\python.exe scripts\orbital_refit_arm.py --ids <comma-separated>
```

Cost: **1.0–2.2 s per source** (n = 3, on 558–824 CCD transits, machine-load dependent) — negligible beside DataLink.
Acceptance, pre-registered in the arm's docstring: BH3 to **P 11.454 yr, e 0.7278,
M₂ 34.68 M☉** within M1's *printed* precision (0.005 / 0.0005 / 0.005). Passed
2026-08-23, `out/m7_refit_acceptance.json`.

**Two caveats that must be printed next to every mass this arm produces** (both measured
in M7 §2e against three published solutions):

1. **The formal error bars are lower bounds.** Across 11 trio elements with a published
   comparison, |refit − published| / (the refit's own σ) has **median 2.28, max 6.16**, and
   only 4 of 11 land inside 1 σ. The posterior is a **Laplace** interval, not a total
   uncertainty. **Inflate by ≥ 2.3, or say it is formal.**
2. **The parallax zero-point, cubed.** All three trio parallaxes came out 5–41 µas *below*
   the published values (the Lindegren+2021 scale) and the photocentre mass function goes
   as **ϖ⁻³**. That is the whole of the arm's +2.4 σ offset from Panuzzo's published
   M_BH — and Panuzzo avoided the same trap by deriving the headline mass from the
   **combined astrometry+RVS** solution via `a1` in AU rather than from a₀/ϖ. **If DR4
   publishes `a1` for a candidate, prefer it.**

Sanity numbers to compare the day's output against (M7 `out/m7_refit_vs_literature.txt`):
BH3 every Campbell element within **1.1 σ** of Panuzzo's astrometric solution; HD 114762
**M₂ 0.233 vs Winn 2022's 0.215 ± 0.013** (and excluding Kiefer's 0.10–0.14); Gaia-4
**10.8 M_Jup vs Stefánsson 2025's 11.8 ± 0.7**, with the `binary_masses` M₁ rung
reproducing their host mass to **−0.20 σ**.

## Failure branches (rehearsed or measured)

| symptom | branch |
|---|---|
| **ESAC sync answers slowly / 500s / read-times-out on trivial queries** | measured 2026-08-18. Every sync helper retries 6× with backoff; the ranged pull is **resumable** (a range whose parquet is on disk with the expected count is skipped) so a killed pull restarts where it stopped. For DR3-side work fail over to the ARI/AIP mirrors after the validation gate (Phase 0.0); for the DR4 pull itself there is no mirror — wait, retry, and keep the resumable pull running |
| **`TAP_SCHEMA.columns` specifically hangs** (it was the worst-behaved path on 2026-08-18) | schema introspection is the one place failover is legitimate — `rehearse_dr4_day.py` uses `sync_csv_schema` (2 attempts × 90 s per endpoint, ESAC then ARI) and records in `out/rehearsal_timings.csv` when it fired. Never route the data path this way |
| async job QUEUED > 30 min | plan-B ranged sync pull (Phase 1) — delivered 169k rows in ~35 min twice |
| sync range hits 2,000-row cap | halve PACK for that range and re-pull; never accept a capped result |
| assembled ≠ exact COUNT(*) | find the gap via per-range recount; the histogram is approximate near 2^53, the COUNT is law |
| `nss_masses` row missing for a target (BH2 syndrome) | three-tier M₁ handles it; never hard-require a mass row (M2 landmine #2) |
| join fan-out (rows > distinct sources) | expected: dual solutions + multi-row masses; dedupe on (source_id, solution_type) + combination_method preference; count both sides |
| **DataLink refuses/throttles** | measured 2026-08-21: 5 identical batch-10 requests spanned 22.7–72.2 s (3.2×) with **no monotone rise** — that is archive *load*, not a rate limit aimed at us, so the answer is patience, not smaller batches. The harness already retries 6× with backoff and honours `Retry-After` to the second. If a real 429 appears, it is new information: record it, then halve `--batch` |
| **the harness is killed mid-run** | restart the same command. Sources already in the ledger are not re-fit, epochs already in `data/epoch_cache/<release>/` are not re-fetched, and each cache file is written `.tmp` → `os.replace`, so a half-written file cannot masquerade as cached. Cost of a kill: at most the batch in flight. **Demonstrated at real scale (M7):** a 981-source run stopped at 400 and restarted reported `981 queued, 400 already in the ledger, 581 to do` and resumed at batch 20 of 50 |
| **DataLink much slower than measured** | the clock is now an equation, not a band: `t = 2.42 s + 0.215 s/source × n + 0.1424 s/KiB × KiB` (M7). Measure the day's KiB/s from the harness's own first ten batches (`out/m6_harness_timings.csv`, `seconds` vs served rows) and read the wall clock straight off it. 6.9 KiB/s → 2.1 h; 1.8 KiB/s → 7.8 h; 0.69 KiB/s → 20 h. All inside 72 h. The queue is *ranked*: a slow archive costs depth, not the headline. **Do not shrink `--batch`** — the per-source term is 0.215 s and the per-request overhead 0.65 s, so smaller batches buy nothing and cost overhead |
| **DataLink serves nothing for many sources** | measured on DR3: an empty request costs 0.65 s, so a low-coverage queue runs *fast* and the ledger fills with `NO_DATA`. That is not a failure of the harness — but if DR4 serves epoch astrometry for materially less than the whole queue, **that is the day's biggest finding** and it is a STOP-and-report, not a footnote. (M7 measured DR3 epoch-photometry coverage of the queue at **7.5 %**; DR4 epoch astrometry is expected to be near-complete for NSS sources, and if it is not, everything downstream changes) |
| **the refit arm returns `NO_PEAK`** | the periodogram of the single-star residuals has FAP ≥ 1e−3: there is no orbit to refit even though f2 said the source is not a single star. Record it, keep the `orbit_reality` CONFIRMED verdict, and do **not** quote a mass. It is a real outcome, not an error |
| **the refit arm's mass disagrees with the catalogue's `m2_min`** | expected and informative. M7 measured the arm against DR3 for two sources: period agreed to 0.1–2.6 %, a₀ to 3–18 %, and the mass function goes as a₀³, so an 18 % a₀ difference is 1.8× in mass. The **refit** is the independent measurement; the catalogue value is the thing being checked. Report both, and check the parallax offset before believing either |
| **a source comes back with < 50 usable transits** | `INCONCLUSIVE`, not a demotion — the verdict record says so and the row stays in the queue for the 72-h pass. Never let a thin epoch series masquerade as "no wobble" |
| **`gaiasupdate` raises on a source** | the record is written as `ERROR` with the exception text and the loop continues. Errors are counted in the bulletin; a systematic error class (same exception on many sources) is a STOP, not a footnote |
| **the verdict store fails schema validation** | `scripts/verdict_schema.py` raises with the exact violation. Nothing downstream may run on an invalid store — the discriminator tests would silently mix vocabularies |
| **a discriminator test raises on the verdict join** | fixed in M7, but know what it means. Both tests used to hard-code `== 76` — the size of the only store that existed when they were written — so `--verdicts all` died the moment the store held a second producer, and the *pooled* command this runbook prescribes died with it. They now assert only **no fan-out** (`len(t) == len(eb)`) and **drop unjoinable rows with a printed count**. If the drop count is large, that is the story: a verdict row that is not in the day's triage frame or has no `gaia_source` row cannot be tested, and the reason needs finding before any result is quoted |
| corr_vec length ≠ n(n−1)/2 | that solution's fitted-parameter set differs from the nsstools layout — set the row's Pr to NaN, flag, continue (never guess an ordering) |
| TAP_SCHEMA diff shows a rename not in the map | patch `queries/dr3-to-dr4-tables.md` first, then the SQL — the map is the single source of truth |
| BH1/BH2 acceptance FAIL | full stop on publishing; diff schema + config against rehearsal state; the rehearsal proves the code path is sound on DR3-shaped data |

## What ships when

**First 24 h** (all reproducible from artifacts, nothing irreversible without Matthew):
- the schema diff vs the draft model (also feeds ../IDEAS/gaia-dr4-diff-auditor.md);
- the day-one candidate bulletin (rehearsal format `data/rehearsal/out/dr4day_bulletin.csv`):
  class-III list, Pr(III|corr), dust columns, flags, epoch-vet verdicts for whatever
  fraction DataLink has served;
- BH1/BH2 acceptance statement + funnel counts (input → core → screen → class III);
- **the day-one VERDICT STORE** (`out/verdicts/*.csv`, schema
  `day1_verdict_record.v1`): one record per adjudicated orbit, with the fit
  statistics, the verdict, its confidence and its **scope**, the seven caution
  flags and full provenance. This is the artifact every later test consumes,
  and the count of records in it is the day's real yield number;
- **the ORBITAL REFITS** (`out/verdicts_v2/*.csv`, schema `day1_verdict_record.v2` =
  v1 + 35 `refit_*` fields): for every `CONFIRMED (orbit_reality)` source, an
  independent Keplerian orbit, the M₁-free astrometric mass function, and a companion
  -mass posterior with the M₁ rung recorded. **This is the headline artifact.** Ship it
  with both M7 caveats attached — the formal errors are lower bounds (median ×2.3 too
  small on the trio) and the mass function goes as ϖ⁻³ against a parallax that ran
  5–41 µas low on all three test objects;
- **the day-one epoch-vet queue** (`epoch_vet_day1_queue.csv`: main list +
  retrieval-bin Pr ≥ 0.999, all caution flags) — **emitted by the driver itself**
  (stage H, M5), so it exists the moment the rehearsed pipeline finishes; the
  retrieval-bin members are IN the first-24h queue, not the 72-h backlog (M4; DR3
  analog: 32 rows, 4 of them at Pr 1.0000 with M₂_min 2.9–3.6 — never epoch-vetted,
  day-one fresh);
- **the Gaia-indicator table for the day's list** (one `gaia_source` +
  `astrophysical_parameters` + `vari_summary` column pull, minutes, no telescope) with
  the M5 DR3 baselines to compare against: ESP-CS coverage (DR3: 7/76 of EB26 —
  report the DR4 number, it is the single fact that decides whether the chromospheric
  axis is ever testable), ΔAmp_G AUC 0.659 vs the 0.725 needed, `astrometric_gof_al`
  AUC 0.254 with confirmed on the noisy side, and the `flag_astrom_quiet` count;
- **the far-star dust arbitration, all-sky** (`m5_vergely_south.py` +
  `m4_bayestar_dozen.py`, both maps, both unit chains, the geometry gate's own file):
  the count of ambiguous rows resolved alive / dead / σ-fragile / still-unresolved,
  and **whether any membership moved** (DR3: 12/0/1/0, moved 0);
- the eROSITA cross of the new list (in-footprint count, matches, chance control,
  f_X/f_opt reads, the null-or-not statement) **+ the comparison against the M4 DR3
  baselines: 30/471 list match rate; EB26 direction 2/13 spurious vs 0/16 confirmed —
  an X-ray match stays a caution tag (config v3 `xray_policy`), epoch-vet-first,
  never a cut.**
**Checked, not shipped**: any single-object claim before its epoch-vet verdict + the
  M2/M3/M5 caution list (1-yr alias, low-|b|, σ_TI² > 20, X-ray-active,
  dust-unresolved-south, dust-σ-fragile, astrom-quiet).

**72 h**:
- epoch-vet verdicts for the full priority queue; demotion statistics (the DR3-calibrated
  expectation: ~30 % of screen survivors are spurious — El-Badry operating point);
- **every discriminator test re-run on the day's own epoch-vet verdicts, with no new
  code** (M6): `m5_activity_discriminator.py`, `m4_eb26_erosita_test.py` and
  `m6_astrom_quiet_decision.py` all take `--verdicts out\verdicts\*.csv`. Run each
  **twice** — `--scopes orbit_reality` and pooled — and report both; the scope
  composition is printed automatically the moment the store holds more than one
  producer. Ship the family verdicts with their power statements whether or not
  anything reaches significance, plus the `flag_astrom_quiet` KEEP/REMOVE/CARRY
  decision under its pre-registered rule;
- the rest of the retrieval-bin adjudication (DR3 analog: 239 rows; the 32 at Pr ≥ 0.999
  were already in the day-one queue);
- HVS 6D rerun (W5) and the microlensing-input refresh (W4) start once the NSS thread is
  stable;
- draft-1 of the first-weeks note on whatever survived both epoch vetting and the caution
  list — target selection per `../DISCOVERY/run3-prospectus.md` axis #4.

**Never**: submissions, account creation, or externally-visible claims without Matthew's
explicit go (repo law).
