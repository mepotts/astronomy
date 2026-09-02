# M6 — the verdict-harvesting harness: one schema, two producers, and a measured day-one clock

*2026-08-21. Runs M5's own recommendation. Three milestones have now tested candidate
discriminators — X-ray (M4), chromospheric and photometric (M5) — against exactly one
verdict source, the 65 El-Badry+2026 follow-up verdicts, and every one came back
footprint-, coverage- or power-limited. M5's conclusion was that **the bottleneck is the
verdict sample, not the axes**, and that the epoch-vetting loop is the only machine that
manufactures verdicts at scale. M6 builds that machine, freezes the record it emits,
rewires the existing tests to eat it, and measures how fast it goes. Repo law:
sourced-or-UNSOURCED; negative results are results; rules pre-registered. Anonymous
HTTP only. No accounts, no submissions, no commits, no pushes.*

---

## 0. The one-paragraph answer

The epoch-vet loop is now a production harness (`scripts/epoch_vet_harness.py`): batched,
resumable, rate-limit-aware, instrumented, and emitting **verdict records** in a frozen
schema instead of an ad-hoc CSV. The **single-star fit runs at 0.036 s/source — about
100,000 sources/hour — and is not, and never will be, the bottleneck**; DataLink is, at a
**measured 3.9 s/source**, and the projected day-one throughput at batch 20 is a **band of
125–857 sources/hour**, i.e. the 983-row queue in **1.1–7.9 h**. (Two queue counts appear
throughout and both are correct: **983** is what the rehearsal driver emits from its own
pre-dust triage — the shape December will see — and **981** is the DR3 production copy
after the Phase-2 dust re-triage, `out/epoch_vet_day1_queue.v2.csv`.) The M4 and M5
discriminator tests now read verdicts through the schema, and **all five of their frozen
artifacts reproduce byte-identically** through the new path. The harness reproduces M3's
prototype end-to-end (3 kept, 9 demoted, max |Δf2| 0.005 = the prototype's own rounding).
`flag_astrom_quiet` is **CARRIED, not settled** — and M6 measured exactly why: on the
population the flag actually operates on, the test that would judge it cannot see
anything smaller than AUC 0.80, and its thresholded form cannot see anything at all.

---

## 1. The harness (task 1)

### 1a. What M3 had, and what was missing

M3's prototype (`scripts/vet_epoch_astrometry.py`, 40 lines) read one local file, held
everything in memory, and printed a table. It proved the science works. It could not
survive December: no batching, no cache, no resume, no retry, no timings, and one HTTP
round trip per source if it had ever touched DataLink.

`scripts/epoch_vet_harness.py` is the production version. Every property below was a
requirement, and every one is exercised by a run in this milestone.

| property | how | evidence |
|---|---|---|
| **batched** | one DataLink request per batch via `Gaia.load_data(ids=[...], data_structure='RAW')`, which returns one file holding every requested source | measured: per-request overhead 2.3–6.0 s is amortised over the batch (§1c) |
| **resumable** | per-source epoch parquet under `data/epoch_cache/<release>/` + an **append-only** verdict ledger; on start, cached sources are not re-fetched and ledgered sources are not re-fit | demonstrated: a 5-source run then a 12-source run over the same ledger processed **5 then 7**, ended with 12 records, acceptance PASS |
| **crash-safe** | every cache file is written `.tmp` → `os.replace` | a kill mid-write cannot leave a half-file that looks cached |
| **polite / rate-limit-aware** | ≥ 0.5 s between requests, 6 retries with exponential backoff, `Retry-After` honoured to the second | §1d — and the soak test says the archive is *not* throttling us |
| **fail-fast on deterministic errors** | reads the *body* of a 500 for `Unknown retrieval type` / `Unknown release` and aborts instead of retrying | measured landmine, §1e |
| **instrumented** | per-batch (`n_ids`, `n_served`, rows, seconds) and per-source (transits, fit seconds, verdict) rows appended to `out/m6_harness_timings.csv` every run | every number in §1c comes from that file |

### 1b. The pre-registered verdict rules

Written into the harness docstring before the M6 runs; they *extend* M3's single rule
rather than replacing it, and they are copied verbatim into config v5.

| condition | verdict (scope `orbit_reality`) |
|---|---|
| `n_used < 50` transits | **INCONCLUSIVE** — too few epochs to adjudicate. **Not a demotion** |
| `\|f2\| > 5` | **CONFIRMED** — epoch-level wobble present → hand to the orbital refit |
| `\|f2\| ≤ 5` | **SPURIOUS** — no epoch-level support for the claimed photocentre orbit |
| DataLink served nothing | **NO_DATA** |
| the fit raised | **ERROR**, exception text in `notes` — never silently dropped |

Confidence: `r = |f2|/5`; **HIGH** if `r ≥ 2` or `r ≤ 0.5`, **MEDIUM** inside a factor 2
of the gate, **LOW** if INCONCLUSIVE/NO_DATA/ERROR or `n_used < 100`. The INCONCLUSIVE
rule is the one M3 did not have and the one that matters: a thin epoch series must never
be allowed to masquerade as "no wobble".

### 1c. The measured throughput, and the projection

`scripts/m6_datalink_throughput.py`. What could be measured today was measured; what
could not is labelled.

**Measured — the fit**, on real DR4 epoch astrometry (the 2026-06-26 pre-release file,
77–115 transit rows and 462–824 usable CCD transits per source):

> **steady-state mean 0.036 s/source, median 0.025 s** over n = 22 fits in two runs
> (10–90 %: 0.020–0.045 s; the single 0.163 s tail is CPU contention, not source
> complexity) ⇒ **~100,000 sources/hour**. The **first fit of every run** costs
> 1.4–2.5 s (`gaiasupdate` import + pandas accessor registration) and is excluded
> per run, not globally — the timings CSV accumulates, so a global-max rule would
> silently inflate the figure as the file grows. **The fit half of the loop is free
> by three orders of magnitude.**

**Measured — the DataLink service.** DR4 epoch astrometry does not exist yet, so the
transport was measured with DR3 `EPOCH_PHOTOMETRY`: the same service, the same endpoint,
the same RAW batching, the same anonymous quota, a different payload. Labelled a proxy
everywhere it appears. Batch sweep 1→40 plus a 5-request soak, all anonymous, all polite:

| quantity | measured 2026-08-21 |
|---|---|
| per-request overhead | 2.3–6.0 s |
| per-source cost at 7.5 KiB/source | **3.9 s** |
| effective delivered rate | **~1.8 KiB/s** |
| soak: 5 identical batch-10 requests | 22.7 / 27.2 / 29.3 / 42.3 / 72.2 s |

**~1.8 KiB/s is not a network.** The Gaia DataLink service is **server-work-limited, not
bandwidth-limited** — it is assembling products, not shipping bytes. That single
observation is what makes an honest projection hard, and it is why there are two models.

**Measured — the payload**, from the real thing: the pre-release RAW file is 1,183,282 B
for 12 sources = **96.3 KiB/source raw, 50.9 KiB/source zipped** (DataLink sets
`USE_ZIP_ALWAYS=true`, so the zip *is* the transfer). That is **6.8×** the probe's
payload per source.

**Two models, both fitted to the same calls, both reported:**

| model | fit | R² | what it says about DR4 |
|---|---|---|---|
| **A** transport-limited | `t = 2.3 s + bytes / 1.8 KiB/s` | 0.934 | a DR4 source costs ~7× more, because its payload is ~7× bigger |
| **B** per-source work | `t = 6.0 s + 3.86 s × n_sources` | 0.917 | a DR4 source costs the same as a DR3 one, because the cost is assembly, not bytes |

They fit the same data about equally well — bytes and sources are collinear in the probe
— and they disagree **only** about the extrapolation that cannot be tested until the data
exists. Reporting one number would be exactly the kind of confident-wrong answer this
repo keeps finding in other people's papers. So:

> **PROJECTED day-one throughput, batch 20, undegraded: 125–857 sources/hour**
> ⇒ the **983-row queue in 1.1–7.9 h**.
> At a 10×-degraded archive (release-day branch, model A): **78 h** — the only branch
> measured that does *not* fit inside the runbook's 72 h.

Batch size barely matters above ~5 (the per-request overhead is already amortised);
**payload and archive health are the whole story**.

**The consequence is operational, and it is reassuring**: the queue is *ranked* and the
harness consumes it in rank order, so a slow archive costs **depth, not the headline** —
BH1, BH2 and the EB26-refuted poster child are adjudicated in the first minutes under
every branch measured. The failure mode to plan for is running out of *hours*, not out of
throughput, and the mitigation is already built in: the harness is resumable, so the 72-h
mark is a checkpoint, not a deadline.

### 1d. The soak test: load, not throttling

Five identical batch-10 requests back to back spanned **22.7–72.2 s, a 3.2× spread**,
with **no monotone rise** (trend −7.6 s/request, R² 0.35). That is archive **load**, not a
rate limit aimed at us — which changes the day-one plan: the answer to a slow DataLink is
patience and the resumable cache, *not* smaller batches. It also means **any single-call
timing is worthless for planning**, which is the second reason the projection is a band.

### 1e. The landmine the probe found

Asking the live ESAC data server for `retrieval_type='EPOCH_ASTROMETRY'` returns

```
HTTP 500   Unknown retrieval type: 'EPOCH_ASTROMETRY'
```

for **both** `RELEASE='Gaia DR4'` and `'Gaia DR4_INT4'` (the default in `gaiasupdate`
0.1.2's own `from_gacs_datalink`). **astroquery 0.4.11 lists `EPOCH_ASTROMETRY` in its
client-side `VALID_DATALINK_RETRIEVAL_TYPES`, so nothing catches this before the request
goes out** — and it arrives as a *500*, which is precisely what the retry policy exists
for. Retrying it is five wasted minutes on a deterministic answer. The harness now reads
the **body** of the error and fails fast on `Unknown retrieval type` / `Unknown release`,
and the runbook's new Phase 3.0 makes a one-source DataLink probe a hard gate before the
harness starts.

---

## 2. The verdict schema (task 2)

`scripts/verdict_schema.py`, JSON Schema sidecar `schemas/day1_verdict_record.v1.json`,
`schema_version = day1_verdict.v1`. One record per **adjudicated orbit**, in five blocks:

| block | fields |
|---|---|
| **identity** | `source_id`, `release`, `source_id_dr3`, `nss_solution_type` — the orbit key is *(source_id, solution_type)*, because `source_id` is a key of neither `nss_two_body_orbit` nor `binary_masses` (M2 landmine #4) |
| **orbit provenance** | `orbit_source`, `orbit_period_d`, `orbit_significance`, `orbit_a0_mas`, `queue_bin`, `queue_rank` |
| **fit statistics** | `n_transits_fetched`, `n_transits_used`, `f2_single_star`, `parallax_mas`, `excess_noise_mas`, `fit_model`, `fit_seconds` — null for an external verdict, filled by the harness |
| **the verdict** | `verdict`, **`verdict_scope`**, `verdict_basis`, `verdict_confidence`, `verdict_confidence_basis` |
| **cautions + provenance** | the seven flags frozen in config v4, plus `schema_version`, `verdict_source`, `verdict_source_version`, `config_version`, `epoch_data_release`, `epoch_data_structure`, `gaiasupdate_version`, `produced_utc`, `run_id`, `notes` |

### The honest part: `verdict_scope`

An EB26 verdict and a harness verdict are the **same record type** — that is what lets one
test consume both — but they do **not** answer the same question, and the schema refuses
to let that be forgotten:

- `compact_companion` — *is there a dark massive companion?* (EB26, basis `rv_followup`)
- `orbit_reality` — *does the published photocentre orbit have epoch-level support?*
  (the harness, basis `epoch_astrometry_f2`)

**The mapping is asymmetric.** A harness SPURIOUS and an EB26 SPURIOUS mean nearly the
same thing — the orbit is not real. A harness **CONFIRMED is weaker** than an EB26
CONFIRMED: the orbit is real, the companion's nature is unestablished. Pooling the scopes
is therefore legitimate on one side and not the other, so `scope_composition_string()`
exists and **every consumer prints the composition of both groups the moment the run
carries more than one (source, scope) combination**. The M4/M5 tests default to the EB26
file alone, so today's runs carry exactly one and their output is unchanged — which is
exactly what makes the byte-identity check in §3 meaningful rather than a tautology.

The store: `out/verdicts/eb26.v1.csv` (76 records: 42 CONFIRMED / 23 SPURIOUS / 7 UNKNOWN
/ 2 NOT_CO / 1 OTHER / 1 MARGINAL) and `out/verdicts/harness_prerelease.v1.csv` (12
records, all `orbit_reality`). `load_store()` accepts a file list, a directory, a glob, or
the word `all` (cmd.exe does not expand wildcards, and a runbook command that works in
only one shell is a trap), then concatenates, coerces and **validates** — vocabulary,
required fields, foreign schema versions and duplicate orbit keys all raise.

---

## 3. Wiring the consumers (task 3) — five artifacts, byte-identical

`m4_eb26_erosita_test.py` and `m5_activity_discriminator.py` no longer read
`fixtures/elbadry2026_astrometric_candidates.csv`. They call
`verdict_schema.load_store(...)` and `eb26_compatible_frame(...)`, which hands back
exactly the column names they already used (`source_id`, `verdict`, `period_d`,
`significance`, `notes`). Both gained `--verdicts / --scopes / --sources / --out-dir`.
That is the whole change: **the source of verdicts, not the behaviour.**

The acceptance test of a refactor like this is not "the numbers look right":

| artifact | frozen sha256 | re-run through the store | |
|---|---|---|---|
| `m4_eb26_erosita_xmatch.csv` | `556144fc…dcd27e8d` | `556144fc…dcd27e8d` | **IDENTICAL** |
| `m4_eb26_discriminator_stats.txt` | `ecea9350…36373550d` | `ecea9350…36373550d` | **IDENTICAL** |
| `m5_activity_eb26_table.csv` | `450c8f4e…f412df7f1` | `450c8f4e…f412df7f1` | **IDENTICAL** |
| `m5_activity_metric_results.csv` | `183234d1…dcd7f59e063` | `183234d1…dcd7f59e063` | **IDENTICAL** |
| `m5_activity_discriminator_stats.txt` | `e6d9e1a2…5d4e2d4f9` | `e6d9e1a2…5d4e2d4f9` | **IDENTICAL** |

(`out/m6_refactor_check/SHA256SUMS.txt`; the re-run wrote into a separate directory, so
the frozen files were never at risk.) Every published number therefore reproduces
**exactly**, not approximately:

- **M4**: in-footprint detections **2/13 SPURIOUS vs 0/16 CONFIRMED**, Fisher two-sided
  **p = 0.1921**, smallest detectable spurious rate at 80 % power ≈ 0.40.
- **M5 family A**: `activityindex_espcs` **7/76** (3 confirmed / 1 spurious) — **NOT
  TESTABLE** under the pre-registered ≥ 5-per-side rule.
- **M5 family B**: ΔAmp_G AUC **0.659**, p 0.0352 → Holm **0.1409**, against a
  smallest-detectable AUC of 0.725.
- **M5 family C**: `astrometric_gof_al` p 0.0011 → Holm **0.0067**, AUC 0.254;
  `ruwe` Holm 0.041; negative control `phot_g_n_obs` p 0.144.

One landmine was found and paid for during the refactor rather than in December: the
EB26 fixture's `significance` is *EB26's published value*, not the archive's, and M4's
merge relied on column-order precedence to keep it (`suffixes=("", "_tri")`). The schema
carries it as `orbit_significance` with `orbit_source = elbadry2026_table`, and the
compatibility frame restores the name — otherwise the refactor would have silently
swapped in the archive's `significance` and changed one column of a frozen artifact.

---

## 4. End-to-end validation (task 4)

The harness was run over the only real epoch astrometry that exists — the 12-source
2026-06-26 pre-release file — through the production code path and the new schema:

| | result |
|---|---|
| kept (**CONFIRMED**, `orbit_reality`) | **3/3**: Gaia BH3 f2 **893.97**, HD 114762 **186.50**, Gaia-4 **31.53** |
| demoted (**SPURIOUS**) | **9/9**, all \|f2\| ≤ 1.55 |
| confidence | **HIGH on all 12** (every one clear of the gate by ≥ 2× or ≤ 0.5×) |
| agreement with M3's prototype | max **\|Δf2\| = 0.005**, max \|Δparallax\| = 5×10⁻⁵ mas — i.e. the prototype's own printed precision (2 dp / 4 dp). **Not drift; rounding.** |
| transits used | 462–824 per source, `n_used` == the prototype's `n_epochs` on all 12 |

This is rehearsal **stage F** now, and it is also acceptance gate **A4** on the config
write. The M3 prototype survives as the thing the harness is checked *against*.

---

## 5. `flag_astrom_quiet` (task 5) — CARRY, and the reason is measured

### The error M5 made, and M6 corrected

M5 measured `astrometric_gof_al` across **all 65** verdicted EB26 targets. But the flag
does not operate on those 65. It operates on the **day-one queue** — and the frozen screen
removes 17 of the 65 before the flag is ever computed, leaving a biased survivor set
(brighter, far higher `significance`). **A discriminator measured on a population it will
never see is not evidence about the flag.** So M6 re-asked family C on the flag's own
operating population (`scripts/m6_astrom_quiet_decision.py`).

Reconciliation first, so the counts cannot look like a disagreement: M5's published
"46 rows / flag marks 2 / catches 0 of 7" are the **main-bin** counts and **reproduce
exactly**; the flag also marks the 32-row retrieval bin, which adds one confirmed and one
spurious verdicted row → **48 in-list (40 confirmed / 8 spurious), flag marks 3, catches
0 of 8**.

| test | all-65 (M5's population) | **in-list (the flag's own)** |
|---|---|---|
| `astrometric_gof_al`, MWU | p **0.0011**, AUC 0.254 [0.136–0.388] | p **0.174**, AUC 0.344 [0.172–0.541] |
| smallest AUC detectable at 80 % power | 0.725 | **0.800** |
| `ruwe`, MWU | p 0.0083, AUC 0.300 | p 0.635, AUC 0.444 |
| the flag itself (Fisher) | — | 3/40 confirmed vs 0/8 spurious, **p = 1.000** |
| smallest spurious marking-rate detectable at 80 % power | — | **0.55** |

### The finding that settles the argument about the argument

**M5's "0 of 7" was never evidence that the flag fails.** At the flag's measured in-list
marking rate of 7.5 %, the *expected* catch among 8 spurious rows is **0.60**. Observing
zero is what a working flag and a dead flag *both* predict. And the thresholded test
cannot notice anything until the flag marks **55 %** of spurious rows — a discriminator
nobody has ever claimed. The in-list test, as of today, **has no power at all**.

> **DECISION: CARRY.** The flag stays exactly as config v4 froze it — tiebreaker only,
> both caveats attached, never a cut, never quoted beside `significance`. **Removing it
> today would be as unevidenced as promoting it.** This is the honest answer the
> milestone allowed for, and it is now backed by numbers rather than by hesitation.

### The test that will decide it, pre-registered

In `scripts/m6_astrom_quiet_decision.py`'s docstring and copied into config v5, so the
answer cannot be chosen after seeing December's verdicts:

- **KEEP** — the in-list continuous test reaches p < 0.05 two-sided in the M5 direction
  (AUC < 0.5) **and** the thresholded flag's in-list catch rate beats its marking rate at
  Fisher p < 0.05.
- **REMOVE** — the in-list test is *well powered* (smallest detectable AUC ≤ 0.70) and the
  observed in-list AUC is consistent with 0.5.
- **CARRY** — anything else.

And the harvest it needs, computed at the achieved effects:

| at this effect | needs (in-list verdicts) | has today |
|---|---|---|
| M5's all-65 AUC 0.254 | 80 confirmed + 16 spurious | 40 + 8 |
| the observed in-list AUC 0.344 | 160 confirmed + 32 spurious | 40 + 8 |

One harness pass over the 981-row queue takes the in-list verdict count from **48 to
O(981)**. That is more than enough for either row — and it is the whole argument for M6
existing.

---

## 6. Runbook and rehearsal (task 6)

**`DR4-DAY-RUNBOOK.md` Phase 3 is rewritten as a first-class harness phase**, with a new
**Phase 3.0** (probe DataLink's retrieval type, *then* measure it — ~7 min), the measured
timing table, the pre-registered verdict rules, the scope warning, and **§3.3: the exact
commands that re-ask every discriminator question against the day's own verdicts, run
twice (scope-pure and pooled)**. Six new failure branches were added, all measured or
demonstrated: DataLink throttling (it isn't throttling — it's load), a killed harness,
a slower-than-projected archive, thin epoch series, `gaiasupdate` raising, and a store
that fails schema validation. Config pointer → **v5**.

**The rehearsal driver now runs the production harness**: stage F calls
`epoch_vet_harness.run(source="prerelease")` instead of the M3 prototype, deletes its
ledger first so verdicts are always recomputed, and asserts *both* the 3/9 acceptance and
f2 agreement with the prototype. **New stage I — the verdict store**: it assembles the
day's records from both producers, validates them against the JSON Schema, and checks the
consumer contract. Stage I is the stage that makes 2026-12-03 a re-run instead of a
rewrite.

**Full rehearsal re-run, all nine stages, COMPLETE and green:**

| stage | s | status | note |
|---|---|---|---|
| A — schema pin | 7.3 | OK | ESAC healthy today; served by esac, no failover needed |
| B — rename patch + live TOP-5 probe | 4.0 | OK | 5 rows / 38 cols |
| C — plan-B ranged pull | 8.1 | OK | resumed from 94 cached chunks; 169,227 rows, id-sum match, sha256 `b3b099a6…dddd5231` for the **fourth** time |
| D — triage + BH1/BH2 acceptance | 59.0 | **PASS** | |
| E — corr_vec (measured, not re-run) | 74 + 10 | OK(measured) | politeness |
| **F — epoch-vet, PRODUCTION harness** | **3.2** | **PASS** | 3/3 kept, 9/9 demoted, max \|Δf2\| 0.0050 |
| G — bulletin | 0.4 | OK | 951 candidates |
| H — day-one queue | 0.3 | **PASS** | 983 rows, BH1/BH2 top-2 asserted inside the builder |
| **I — verdict store (new)** | **0.1** | **PASS** | 88 records, 2 producers, 2 scopes, schema-validated |
| **total driver** | **82 s** | **COMPLETE** | |

**82 s is not a speedup and must not be read as one.** M5's 1,150 s was measured while
ESAC was having its worst afternoon on record (stage A alone 179 s with endpoint failover,
B 291 s with an HTTP 500 retry); today the same stages took 7.3 s and 4.0 s because the
archive was healthy. Stage C is cache-resume in both runs. Stage D moved *both* ways
across three runs today — 59.0 s alone, 89.6 s and 104.2 s while a second job held the
CPU — which is the same lesson in miniature. **The rehearsal total is a measurement of
archive weather and machine load, not of pipeline speed**, exactly as the DataLink soak
test found in §1d. What the rehearsal actually certifies is the nine **statuses**, and
all nine are green.

---

## 7. Acceptance and config v5

`scripts/m6_acceptance_and_config.py`. The acceptance gates the config write, as in M4
and M5:

- **A1** Gaia BH1 + BH2 present, Pr(III|corr) = 1.0000, M₂_min 12.81 / 9.76, top-2 — **PASS**
- **A2** EB26 operating point **read through the verdict store**: **39/42 confirmed kept,
  7/23 spurious passed** — identical to the frozen M2 numbers; and the store reproduces
  the fixture column-for-column on everything the tests consume — **PASS**
- **A3** the store validates against `schemas/day1_verdict_record.v1.json`: 88 records,
  2 producers, 2 scopes — **PASS**
- **A4** the harness's end-to-end validation reproduces M3's prototype (3 kept, 9 demoted,
  max |Δf2| 0.0050) — **PASS**

**`queries/dr4-triage-config.v5.json`** (v1–v4 untouched on disk). Selection, screen,
probability method and membership **identical to v2/v3/v4 — 949 rows; M6 moved nothing
about the candidate list.** What v5 adds:

1. `verdict_schema` — the record, the vocabularies, the **scope rule** and its asymmetry,
   the wired consumers, and the byte-identity acceptance;
2. `epoch_vet_policy` — the pre-registered f2 rules, the operational contract
   (resumable / polite / instrumented), the measured throughput and the projection band,
   and `day1_probe_REQUIRED` carrying the `Unknown retrieval type` landmine;
3. `astrometric_quality_flag.m6_decision` — CARRY, the in-list numbers, why "0 of 7" is
   not evidence, and the pre-registered December decision rule.

---

## 8. Files

| artifact | what |
|---|---|
| `scripts/verdict_schema.py` | the day-one verdict record: fields, vocabularies, validation, the EB26 adapter, the compatibility frame, `--emit-schema` / `--build-eb26` |
| `schemas/day1_verdict_record.v1.json` | the JSON Schema sidecar |
| `scripts/epoch_vet_harness.py` | the production loop — batched DataLink, per-source cache, append-only ledger, pre-registered verdict rules, timings |
| `scripts/m6_datalink_throughput.py` | the DataLink probe + soak test, the two transport models, the day-one wall-clock projection → `out/m6_datalink_probe.csv`, `out/m6_throughput_projection.{txt,csv}` |
| `scripts/m6_astrom_quiet_decision.py` | the flag's in-list test, its exact power, and December's pre-registered decision rule → `out/m6_astrom_quiet_decision.txt`, `out/m6_astrom_quiet_inlist.csv` |
| `scripts/m6_acceptance_and_config.py` | acceptance A1–A4 → gates → `queries/dr4-triage-config.v5.json` |
| `out/verdicts/eb26.v1.csv`, `out/verdicts/harness_prerelease.v1.csv` | the store |
| `out/m6_harness_timings.csv` | per-batch and per-source timings, appended every run |
| `out/m6_refactor_check/SHA256SUMS.txt` | the byte-identity evidence for the five refactored artifacts |
| `scripts/m4_eb26_erosita_test.py`, `scripts/m5_activity_discriminator.py` | **modified**: verdicts from the store; `--verdicts/--scopes/--sources/--out-dir`; provenance disclosure |
| `scripts/rehearse_dr4_day.py` | **modified**: stage F = the production harness; **stage I** = the verdict store |
| `DR4-DAY-RUNBOOK.md` | **modified**: Phase 3 rewritten, Phase 3.0 added, six failure branches, config → v5 |

M2/M3/M4/M5 outputs untouched and verified byte-identical at close:
`amrf_class3_candidates.csv`, `…_v2.csv`, `amrf_class3_lowsig_retrieval.csv`,
`epoch_vet_day1_queue.csv`, `…v2.csv`, `m4_bayestar_dozen.csv`, both M4 stats artifacts,
all three M5 activity artifacts, `m5_vergely_*`, `erosita_class3_xmatch.csv`,
`corrvec_eb26_operating_point.csv`, `epoch_vetting_prototype.csv`, and configs v1–v4.

---

## 9. Corrections and new landmines

1. **The Gaia DataLink service is server-work-limited, not bandwidth-limited.** It
   delivered 8–278 KiB in 2.8–164 s — an effective ~1.8 KiB/s. Any capacity plan that
   reasons about DataLink in megabits is reasoning about the wrong resource.
2. **`retrieval_type='EPOCH_ASTROMETRY'` returns HTTP 500 "Unknown retrieval type" today**
   for both `Gaia DR4` and `Gaia DR4_INT4`, while **astroquery 0.4.11 accepts it
   client-side**. A deterministic rejection arrives dressed as a transient one; read the
   body, do not retry. (New Phase 3.0 gate; harness fails fast.)
3. **`gaiasupdate`'s `from_gacs_datalink()` sends one id per request** (`ids=[source_id]`)
   and defaults to the *internal* release string `'Gaia DR4_INT4'`. Anyone using it as
   the day-one fetch path gets one HTTP round trip per source against an archive that
   charges 2.3–6.0 s of overhead per request.
4. **Identical DataLink requests vary 3.2× within minutes**, with no monotone trend — so a
   single timing measurement is worthless for planning, and slow responses are *load*, not
   a rate limit to back off from.
5. **M5's in-list flag counts (46 / marks 2 / 0-of-7) are main-bin-only**; the flag is
   computed over the whole queue and also marks the retrieval bin (→ 48 / 3 / 0-of-8).
   Both are correct; the population has to be named. Not a disagreement — a definition.
6. **"0 of 7" was never evidence of failure.** At a 7.5 % marking rate the expected catch
   among 8 spurious rows is 0.6. A null result quoted without its expected value under
   the *working* hypothesis is not a null result.
7. **The EB26 fixture's `significance` is EB26's published value, not the archive's**, and
   M4's merge preserved it only through pandas suffix precedence. Any refactor that
   re-sources verdicts must carry it explicitly or it will silently substitute the
   archive's number into a frozen artifact.
8. **`astroquery.Gaia.load_data(dump_to_file=True)` writes its zip into the current
   working directory**, ignoring the `output_file` argument — the throughput probe has to
   `chdir` to measure wire bytes.
9. **The first `gaiasupdate` fit of every run costs 1.4-2.5 s** (import + pandas accessor
   registration) against ~0.03 s steady state. A throughput figure taken from a
   12-source run without dropping the warm-up is 10× pessimistic — and dropping only the
   *global* maximum from an accumulating timings file is worse, because every later run
   contributes a warm-up that then stays in.
10. **The M3 prototype printed f2 at 2 dp.** The harness agrees to 0.005, which *is* that
    rounding. An agreement threshold has to be set from the reference's precision, not
    from a hopeful epsilon.

---

## 10. Recommended M7

1. **Dry-run the harness at day-one scale against a service that answers.** Everything
   about the loop is now measured except the one thing that cannot be: DataLink serving
   DR4 epoch astrometry. A full-scale rehearsal against DR3 `EPOCH_PHOTOMETRY` for all
   981 queue members — same batching, same cache, same ledger, ~1–8 h by the projection —
   would convert the *transport* half of the band into a measurement and exercise the
   resume path at real scale. It is the only remaining unrehearsed component, and it
   costs a night of politeness, not a decision.
2. **Build the orbital-refit arm.** The harness produces `CONFIRMED (orbit_reality)` and
   then stops; the runbook hands those to "the `fit_prerelease_orbit_bh3.py` pattern",
   which is a pattern, not a pipeline. December's headline is not "the orbit is real", it
   is *the independent orbit and its M₂* — and that arm has never been run at scale or
   given a verdict schema of its own. It is the natural extension of the record built here
   (the fields are already reserved).
3. **Pre-register the December discriminator re-runs now**, while no verdicts exist. The
   sample sizes are known (84 + 46 for variability; 80 + 16 in-list for the flag), the
   commands are in the runbook, and the scope-pooling asymmetry is the one place where a
   post-hoc choice could still launder a null into a result. Writing the analysis plan
   before the data is the cheapest integrity guarantee left on the table.
4. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew). Note that a
   logged-in DataLink quota is now a *measured* lever, not a hypothetical one — the
   anonymous service is the binding constraint on day-one depth.
