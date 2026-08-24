# M5 — the ESS floor, the solar-wind prior-propping census, and the paper

*2026-08-24. Fifth milestone of avenue #2. Repo law: every externally-sourced number carries its
source URL or the mark UNSOURCED; negative results are results; blockers are findings;
**every criterion is pre-registered before the run that tests it**.
Foundation: [`M1-access-reproduction.md`](M1-access-reproduction.md) (access, stack, conventions,
the mode-vs-model diagnostic), [`M2-converge-scale.md`](M2-converge-scale.md) (hardened harness,
acceptance floor, factorised-likelihood machinery),
[`M3-noise-criticism.md`](M3-noise-criticism.md) (the table audit and the two seams) and
[`M4-finish-the-array.md`](M4-finish-the-array.md) (the finished array, the registered relative gate
R1 and its counter-measure R3, the R5 falsifier, the R4 ESS statistic, the V5 control failure, the
83-pulsar CURN, and the withdrawal of M3's "width not shift" headline). M5 executes M4 §8.3's
recommendations 2, 3, 4 and 5.*

---

## 1. Pre-registration

### 1.0 The state M5 starts from, and what carries no new criterion

Coverage on disk at 2026-08-24 15:41 UTC, measured before anything was launched, with **no process
alive anywhere on the box** (the M4 session was cut short by a disruption, not by a failure —
supervisor and all workers were dead with work outstanding):

| variant | gated | target |
|---|---|---|
| `noise` | 83 | 83 |
| `fl` | 83 | 83 |
| `table` | **82** | 83 |
| `swwide` (M4 registered variant) | **25** | 26 |

**The `swwide` count differs by one from the state M5 was handed, and the difference is a
transcription slip in M4's `STATUS.md` entry, not lost work.** That entry reads "24 of 26 SW_Full
pulsars compared" and "5 of 24 solar-wind rows widen"; M4's own milestone document §4.1 reads
**25 of 26**, and its artifact `results/m4/swwide.json` carries `compared: 25`. The document and the
artifact agree with each other and with the on-disk summaries; the one-line summary was written down
wrong. **M4's historical entry is left as written** — corrections in this repository are declared,
not retro-edited — and this is the declaration. Nothing about the finding changes: 5 of 25 rows
widened by more than 2×, not 5 of 24, and at full coverage it is 5 of 26.

**Two runs outstanding, and they are the same pulsar: J1525-5545**, the array's slowest model
(eval 300–430 ms against an array median of 68 ms `noise` / 12 ms `table`). Its `swwide` run stood
at 71,260 raw post-burn of the 100,000 the gate requires, its `table` run at 40,510 of 50,000.

**These two runs carry no M5 criterion.** They are M4-registered work — V1/V7 for `swwide`, M3's
`table` variant under M4's R1 gate — resumed from their own checkpoints under exactly the gate they
were started under. They were launched at 15:41 UTC, i.e. **before** §1.1–§1.3 below were written,
and that ordering is declared here rather than left to be discovered: no statistic registered in
this document had been computed at that point, and nothing about the tail's outcome could have
informed a criterion below.

**The lock check, done before launching.** There is no per-run lock anywhere in this harness: two
`m3_run.py` processes on one (pulsar, tag) would write one chain directory and corrupt it.
Before relaunching, `/proc` was walked for any live `m3_run.py`, `m3_campaign.sh`, `m4_swwide.sh`
or supervisor — **none** (the only matches were the walking shell itself, the sibling of the M3
`pkill` trap M4 §7.1 records). After launching, the live set was re-checked and is exactly two
samplers, one per outstanding run, one driver each.

**The supervisor defect M4 recorded is fixed in `scripts/m5_supervise.sh`**, which supersedes
`scripts/m4_supervise.sh` (left untouched as the M4 artifact). Three changes, each for something
that happened:

1. `MAX_ROUNDS` defaulted to **40** (~3.3 h). A longer campaign expired **silently** — the
   supervisor printed "supervisor exiting" and stopped with work outstanding, and nothing on disk
   distinguished that from success. Default is now 4000 rounds and the exit reason is recorded.
2. **A completion sentinel.** `results/m4/CAMPAIGN_STATE.json` is rewritten every round (heartbeat,
   coverage, worker count, pid); `results/m4/CAMPAIGN_COMPLETE.json` is written exactly once, when
   every target is met. Absence of the COMPLETE file now *means* unfinished; a stale heartbeat now
   *means* the supervisor is dead. A future reader can tell "finished" from "stopped" without
   guessing.
3. **The relaunch guard is tag-aware.** M4's supervisor guarded only the pool *driver*
   (`alive "m3_campaign.sh noise"`). A session disruption leaves orphaned *workers* with no driver —
   precisely the state M5 started in — so that guard would pass and a second pool would launch on
   top of live samplers, giving two processes one chain directory. A pool is now relaunched only
   when neither its driver **nor any `m3_run.py` worker carrying its tag** is alive. `table` is also
   a first-class target now; M4's supervisor hid it behind `N_TAB` and excluded it from the
   "all targets met" test, so it could declare success with a `table` run missing.

### 1.1 E-criteria — the ESS floor (registered here, before it is applied to anything)

M4 §1.2 R4 recorded a per-parameter effective sample size on every run and deliberately **did not**
gate on it, because introducing a second new criterion alongside R1 would have confounded the
comparison R3 exists to make. It then measured the cost of R1 honestly: **run-level minimum ESS,
median over the set, 347 (absolute-gated) vs 105 (relative-only)** (M4 §2.4), and recommended that
M5 register a floor sized from that measured distribution rather than from a guess. This is that
floor. It is fixed here, before a single pass/fail is computed.

**E1 — the floor.** A run **clears the ESS floor** when its **run-level minimum over sampled
parameters** of the effective sample size, computed by the initial-positive-sequence
autocorrelation estimator on the thinned post-burn chain (the M4 R4 statistic, unchanged), is

> **ESS_min ≥ 100.**

**E1a — where the number comes from, stated before use.** The gate exists to make the A2 comparison
trustworthy, and A2 is a test on **68% interval edges**. For an equal-tailed quantile *q* estimated
from an effectively independent sample of size *N*, the Monte-Carlo standard error is
√(q(1−q)/N)/f(x_q). Taking a Gaussian reference posterior, f at the 16th/84th percentile is
0.2444/σ, so

  MCSE(interval edge) = σ·√(0.16·0.84/N)/0.2444 = **1.50 σ/√N**,

and since the 68% half-width is 0.994 σ,

  **MCSE(edge) / (68% half-width) = 1.51/√N**,  MCSE(median)/(half-width) = 1.26/√N.

Requiring each interval edge to be determined to better than **15%** of the interval's own
half-width gives N ≥ 101. **The floor is 100.** At that value the median of a posterior is
determined to 13% of its half-width, which is the resolution at which the A2 overlap test is doing
real work rather than reading noise. A floor of 200 would buy 11% instead of 15% and cost roughly
four times the compute per run; a floor of 50 leaves the edges uncertain at 21% of the half-width,
which is comparable to the effect sizes M4 reports.

**E1b — cross-check against the measured distribution, which is what R4 asked for.** M4's published
medians are 347 (absolute-gated) and 105 (relative-only). A floor of 100 therefore sits *far* below
the median of the strongest population and *at* the median of the weakest, which is the property a
useful floor must have: it has to be clearable by a typical run and **capable of failing
something**. A floor chosen above 347 would reject the campaign; one chosen below 50 could not fail
a single relative-only run and would be decoration. Note explicitly: the floor is **not** tuned to
produce a particular pass count, and no pass count has been computed at the time of writing.

**E2 — how it is applied. Fixed now, in three parts.**

1. **It does not retro-un-gate anything.** `gate_met` on disk is untouched, and every number M4
   reported stands exactly as M4 reported it. The floor is an **additional reported column**
   (`ess_ok`), reported side by side with the gate columns — the same discipline R3 imposed on the
   absolute/relative pair, for the same reason: a new criterion adopted silently would let this
   project quietly reshape its own published results.
2. **It is a forward gate.** Any chain started after this registration is gated on
   R1 **and** acceptance ≥ 0.05 **and** ESS_min ≥ 100, conjunctively. (The two tail runs of §1.0
   pre-date this sentence and are explicitly exempt, as stated there; their ESS is reported anyway.)
3. **It is a minimum, not a mean.** Averaging ESS over parameters would let a well-mixed EFAC hide a
   stuck amplitude, which is the exact failure mode the M2 frozen-chain near-miss taught.

**E3 — the headline re-test, listed before it is run.** Every M4 headline is recomputed on the
ESS-floored subset and reported as a **pair** (as-M4 / ESS-floored), never replaced:

  (a) coverage per variant; (b) the 83-pulsar agreement rate, in parameters and in pulsars;
  (c) the ΔlnL mode-vs-model median and sign split; (d) the `fl` and `table` factorised-likelihood
  CURN products, MAP and 68%; (e) the seam-(b) ΔMAP between the two configurations;
  (f) the `swwide` variant's resolved-miss count; (g) the F5 growth-curve conclusion — does the
  one-pulsar step out of the prior-rail regime survive the floor?

> **If any headline moves by more than its own stated uncertainty, it is said plainly — in this
> document's own summary, in `STATUS.md`, and in the paper.** Both values are printed in every case.

**E4 — the estimator's own limits, declared.** This is a **single-chain** autocorrelation estimator.
It measures within-chain mixing and can say nothing about a mode the chain never visited; a
perfectly stuck chain in a single mode can have a high ESS, which is why the floor is *added to*
the acceptance floor and R1 rather than replacing either. The estimate is itself noisy, so any run
whose ESS_min falls in **[80, 125]** (±25% of the floor) is flagged **borderline** and **named**, so
that no conclusion in M5 rests on a knife-edge.

**E5 — the falsifier, registered.** A floor is worth having only if it selects against disagreement.
Registered test: **the per-parameter agreement rate with the published table over the runs the floor
REJECTS, against the rate over the runs it ADMITS.** If the rejected runs agree at least as well as
the admitted ones, then ESS_min is **not** diagnostic of accuracy in this problem, and that is
reported as a negative result *about the floor itself* — in the same words, in the same place — not
buried. In that event the floor is retained as a forward criterion (it still bounds Monte-Carlo
error, which is a statement about our own numbers' precision) but it is explicitly **not** claimed
to improve fidelity to the published table.

### 1.2 S-criteria — the re-specified solar-wind control and the prior-propping census

**What went wrong in M4, restated.** M4's registered control V5 defined "a pulsar whose γ_SW is
measured" as "a pulsar whose published γ_SW is comfortably positive and whose 68% interval does not
cross zero" — i.e. it used the **sign** of the published value as a proxy for *measured*. It is not
one. **J1744-1134 has a published γ_SW = +0.91 and its 68% width still goes 1.52 → 4.42 when the
prior is widened**, because the narrow posterior *was the prior edge*. The registered control
therefore failed on a pulsar whose failure was arithmetic, and V4's resolve count was reported VOID
as registered. M5 re-specifies the control by the only thing that can carry the meaning: **posterior
width relative to prior width**.

**S1 — the re-specified control set.** Per pulsar define the **prior occupancy** of γ_SW,

  O_narrow = W68(γ_SW | U(0,7)) / 7  and  O_wide = W68(γ_SW | U(−4,4)) / 8,

where W68 is our own post-burn equal-tailed 68% width from the `noise` (U(0,7)) and `swwide`
(U(−4,4)) runs. A pulsar is **MEASURED** iff **O_narrow < 0.25 and O_wide < 0.25**. The 0.25
threshold is **inherited unchanged** from M4 §4.3's declared post-hoc definition so that M5's number
is comparable with the one M4 printed; it is adopted, not re-tuned, and that is stated because
re-tuning it here would be choosing the threshold after seeing the answer.

**S2 — the control test (the actual replacement for V5).** Over the MEASURED set: the median γ_SW
and the median log₁₀A_SW must each move by less than **0.19** between the two priors (M3 §6.5's
repeat-yardstick, the 90th percentile of our own run-to-run difference — inherited unchanged), and
**no parameter that agreed under U(0,7) may disagree under U(−4,4)** anywhere in the 26. PASS/FAIL
is reported as the verdict. **If it FAILS, M4's V4 resolve count is reported VOID a second time and
the paper says so in the same sentence as the count.**

**S3 — the census, which is the deliverable.** Over **all 26** SW_Full pulsars (not the 19 the
published table alone flags — choosing the set from the answer is what V2 already refused), compute
the **width ratio**

  R = W68(γ_SW | U(−4,4)) / W68(γ_SW | U(0,7))

and classify every row, with thresholds fixed here:

| class | rule | meaning |
|---|---|---|
| **MEASURED** | O_narrow < 0.25 **and** O_wide < 0.25 | the data constrain γ_SW under both priors |
| **PRIOR-PROPPED** | R ≥ 2.0 **and** not MEASURED | the apparent constraint under the positive-only prior is the prior edge |
| **UNCONSTRAINED-BOTH** | O_narrow ≥ 0.25 **and** O_wide ≥ 0.25 **and** R < 2.0 | never constrained under either prior; the row carries no γ_SW information |
| **OTHER** | anything left | named individually, one line each |

> **Primary reported number, fixed now: how many of the 26 published γ_SW rows are, under this
> reproduction, NOT a measurement of γ_SW** — that is, PRIOR-PROPPED + UNCONSTRAINED-BOTH.

log₁₀A_SW widths are reported per class alongside, because the amplitude is what a reader usually
takes from that column and it is coupled to the index.

**S4 — sensitivity, registered before it is computed.** The class counts are recomputed on the grid
R ∈ {1.5, 2.0, 3.0} × occupancy ∈ {0.20, 0.25, 0.33}. **If the primary number moves by more than
±2 rows across that grid, it is quoted as a range and never as a point**, everywhere it appears.

**S5 — the table-only cross-check.** Independently of our chains, classify the **published printed**
γ_SW 68% widths by their own occupancy of each candidate prior, and compare that classification with
the chain-based census. This is the version a reader can perform with nothing but the paper, and any
divergence between the two is a finding to report, not to reconcile away.

**S6 — scope and fairness, binding on every sentence that quotes a census number.** This measures
**our** posteriors under **two priors we chose**. It establishes what a reproducer working from
public data can determine about that column; it does **not** establish what the collaboration's own
chains did, because their prior is not published — which is claim (a) of the note and the reason the
census exists. **No claim is made anywhere that a published γ_SW value is wrong.** The claim is
about what the printed interval can support in the hands of someone who has to guess the prior.
Every quoted number names the prior pair it is under.

**S7 — coverage honesty (F7, carried over).** If J1525-5545's `swwide` run gates in time it enters
the census as the 26th row; if it does not, the census is reported at 25 of 26 **with the shortfall
in the same sentence as the number**, and "26 of 26" is not written anywhere it is not true.

### 1.3 P-criteria — the paper

**P1 — shape and state.** An A&A/MNRAS-shaped short paper (letter length: abstract, ~6 sections,
2–3 tables, 2 figures, reference list). It carries **DRAFT — NOT SUBMITTED** in its title and its
first line; author, affiliation and ORCID are placeholders. It is a separate file from the RNAAS
note, which remains its own finished, separable deliverable; the paper cites the note and does not
depend on it.

**P2 — every number traceable to a committed artifact.** `scripts/m5_paper_numbers.py` emits an
audit table — claim → value → artifact → field → verdict — for **every** number in the paper, the
way `m4_note_numbers.py` does for the note, and `scripts/m5_paper_check.py` checks the drafted text
back against that artifact so transcription slips are caught mechanically rather than by re-reading.
No number enters the paper from prose, including this repository's own prose.

**P3 — scrupulously fair, as a hard requirement.** This is a measurement of a table the
collaboration chose to make public, and **their openness is what made it checkable**: that sentence
is in the abstract and in the introduction, not in an acknowledgement at the end. Every observation
is paired with the concrete fix. No claim of error is made where the correct statement is a
limitation. Where the paper's own text already flags something (the MAP-outside-interval caption,
the "red or blue spectrum" statement, the §Impacts of noise misspecification section), the paper is
quoted first and credited.

**P4 — positioning against prior art, fixed now.** **Goncharov & Sardana (2025) and van Haasteren
(2024) own the general claim that prior choices bias PTA gravitational-wave inference.** The paper
states this in the introduction and again in the discussion, and claims none of it. What is claimed
as new: (i) the **per-table measurement** — this specific published table, value by value, against
an independent implementation on the public data; (ii) the **γ_SW unreachability**, which is the
novel part and is a property of a published column rather than of a method; (iii) the **size** of the
collaboration's own misspecification-mitigation trade-off in the factorised CURN amplitude;
(iv) the **one-pulsar phase change** in the factorised-likelihood product. Any of these that prior
art turns out to own is cut, and the cut is recorded.

**P5 — corrections to our own earlier analysis, as a numbered section of the paper.** Every claim
this project has withdrawn, corrected or reinstated is listed with what replaced it. **A paper that
hides its own retractions is worth less than one that shows them**, and the same standard is being
applied outward, so it must be visible inward first.

**P6 — what remains before submission is stated inside the document**, in its own section, as a
list a human can act on.

**P7 — nothing is sent.** No submission, no account, no upload, no email, no commit, no push. The
Zenodo DOI that closes M3's condition B-4 is a human step and M5 does not take it.

### 1.4 Honesty and economics rules

Unchanged from M3 §1.8 / M4 §1.6. Every run's measured eval time, sustained it/s, acceptance, ESS
and exit reason go into its summary JSON; any chain behind a reported number has passed the
acceptance floor; coverage is stated exactly wherever a number depends on it.

### 1.5 Corrections to §1 made after the fact (declared, not silently edited)

- **§1.2 S4's rule was first implemented more loosely than it was written, and the difference
  decides the answer.** The registered wording is *"if the primary number moves by more than
  **±2 rows** across that grid, it is quoted as a range"*. The first implementation in
  `scripts/m5_sw_census.py` tested the **total spread** of the grid against 4 rather than the
  **deviation from the point value** against 2. Under the loose reading the census's primary number
  (20 at full coverage; 19 when the defect was found) would have been quoted as a point; under the
  registered reading the grid's low corner (16) is four rows below it, so it must be quoted as the
  range **16–20**. The code was corrected to the registration, not the registration to the code, and
  the looser version is used nowhere. §4.2 reports the range.
- Two further corrections are recorded in the sections where they were found rather than here,
  because they are corrections to **M4** and to the **harness**, not to this registration: M4 §4.3's
  post-hoc control names four pulsars where its own artifact lists five (§4.1), and the new
  supervisor's first heartbeat file was invalid JSON because `pgrep -fc` exits non-zero when it
  prints `0` (§2.2).

---

*Results below this line were written after the runs.*

## 2. The tail

### 2.1 What was outstanding, and what it cost

The M4 campaign stopped with two runs unfinished, and both were the same pulsar. **J1525-5545** is
the array's slowest model by a wide margin — 300–430 ms per likelihood evaluation against an array
median of 68 ms (`noise`) and 12 ms (`table`) — and it is the pulsar M4 §7 named as the one that
"would not have finished in this session at all" under the absolute gate.

| run | state at M5 start | gate needs | outcome |
|---|---|---|---|
| `J1525-5545_table_t1` | aborted (SIGTERM), 40,510 raw post-burn | ≥ 50,000 | **GATED** at 54,010 raw, acceptance 0.264, min-ESS 81.1 — and it clears **both** the relative and the absolute rule |
| `J1525-5545_swwide_s1` | `state: running` with no process alive, 71,260 raw post-burn | ≥ 100,000 | **GATED** at 115,510 raw, acceptance 0.226, min-ESS 86.0, 55.5 min of further wall time — under the **relative** rule only (§2.3) |

A stale `state: running` with nothing on the process table is exactly the signature M4 §7.1 warned
about — *killed mid-flight is not finished* — and it is why the lock check of §1.0 was done by
walking `/proc` rather than by trusting the summary.

**The `table` run's minimum ESS is 81.1, below the floor §1.1 registers.** It is exempt, as §1.0
states, because it is a resumed M4-registered run that pre-dates the registration — but it is said
here rather than left to be noticed, and it is counted as a failure in §3.2's ESS column like every
other run. It is also in the borderline band §1.1 E4 requires to be named.

Both runs were resumed from their own checkpoints with **4 BLAS threads each** instead of the
campaign's 1. That is a throughput knob and not a method change — same model, same data, same prior,
same gate, same chain continued — and it is declared here because M4 §7 recorded the campaign's
configuration as one thread per worker. With only two runs outstanding and 32 cores idle, the choice
was between 8 cores busy and 2. Measured effect: the `swwide` chain advanced at roughly 200–230 raw
iterations per minute against the 2–5 it/s M4 recorded for this pulsar under the loaded 30-worker
pool.

### 2.2 The supervisor, and a sentinel so this cannot happen silently again

`scripts/m5_supervise.sh` (§1.0) replaced `scripts/m4_supervise.sh` for the tail. Its three fixes are
listed in §1.0; the one worth repeating is the **completion sentinel**, because it changes what a
future reader can conclude from the repository alone:

- `results/m4/CAMPAIGN_STATE.json` — rewritten every round with a UTC timestamp, the round number,
  live coverage, the live worker count and the supervisor's own pid. **A timestamp older than a few
  minutes now means the supervisor is dead**, which is a fact no file on disk previously carried.
- `results/m4/CAMPAIGN_COMPLETE.json` — written once, when all four variants hit their targets.
  **Its absence now means unfinished.** M4's campaign ended with three runs outstanding and nothing
  on disk said so; that is what this file exists to prevent.

One defect was found in the sentinel itself within a minute of launching it and is recorded rather
than quietly patched: `pgrep -fc` prints `0` **and** exits non-zero when nothing matches, so
`w=$(pgrep -fc ... || echo 0)` wrote `0\n0` into the JSON and produced an invalid file. Fixed to
`|| true` with a default. The supervisor was stopped and relaunched to pick up the fix — and the new
tag-aware guard did its job on the very first round, correctly declining to relaunch either pool
because live `--tag s1` and `--tag t1` workers were on the process table with no driver of their
own. Under M4's driver-only guard that round would have started a second pool on top of two live
samplers.

### 2.3 The tail finished, and the campaign now says so on disk

**The array is complete in all four variants: `noise` 83/83, `table` 83/83, `fl` 83/83, `swwide`
26/26.** `results/m4/CAMPAIGN_COMPLETE.json` was written at 2026-08-24 16:39:27 UTC on the
supervisor's round 29, with `"reason": "all_targets_met"`, and the supervisor exited cleanly instead
of expiring — which is the difference from M4 that this milestone was asked to fix.

The last run to land, `J1525-5545_swwide_s1`, is worth three sentences because it is the honest
caveat on the 26th census row:

- it gated at **115,510 raw post-burn**, acceptance 0.226, after 55.5 further minutes of wall time;
- it clears the **relative** stability rule and **not** the absolute one, so the 26th solar-wind row
  exists because of M4's R1 relaxation — exactly the case R3 exists to make visible;
- its **minimum ESS is 86**, below the floor registered in §1.1 and inside the E4 borderline band.
  It is exempt from the floor by §1.0 (it is resumed M4-registered work), it is counted as a failure
  in §3.2's ESS column like everything else, and §4.2 names it.

What it does to the census: J1525-5545 classifies **UNCONSTRAINED-BOTH** (occupancy 0.32 narrow /
0.54 wide, R = 1.91), which is also what its *published* interval says on its own — a printed γ_SW
68% width of 3.44, 43% of a U(0,7) prior. So the census's primary number moves from 19 of 25 to
**20 of 26** and nothing else changes: no class boundary, no control member, no divergent row.
A number that only moves in the direction the incomplete version already pointed is the least
interesting kind of completion, and that is the right outcome for a coverage line.


---

## 3. The ESS floor, applied (E-criteria)

`scripts/m5_ess_floor.py`, `results/m5/ess_floor.json`.

### 3.1 R4 re-derived first, as a check on the machinery

Before applying anything, M4's own published R4 statistic was recomputed from the summaries:
**median run-level minimum ESS 347 over the absolute-gated `noise` runs and 105 over the
relative-only ones** — digit-identical to what M4 §2.4 printed. The floor is therefore being sized
against a distribution that reproduces.

### 3.2 E1/E2 — who clears the floor

| variant | gated | clear ESS_min ≥ 100 | fail | median ESS_min | 5th pct | 95th pct |
|---|---|---|---|---|---|---|
| `noise` | 83 | **65** | 18 | 339 | 40 | 6245 |
| `table` | 83 | **63** | 20 | 336 | 32 | 29073 |
| `fl` | 83 | **56** | 27 | 198 | 32 | 3883 |
| `swwide` | 26 | **18** | 8 | 214 | 41 | 1151 |

The distribution is enormously wide — five orders of magnitude between the 5th and 95th percentile —
which is itself worth saying: a run that clears this floor typically clears it by a factor of three
or more, and the ones that fail, fail badly. The floor is not slicing through a dense population.

**E4 — the borderline runs are named**, because a knife-edge should be visible. `noise`:
J0613-0200 (91), J1125-5825 (99), J1421-4409 (94), J1525-5545 (84), J1545-4550 (105). `fl`:
J0610-2100 (82), J0614-3329 (95), J1022+1001 (97), J1045-4509 (99), J1600-3053 (89), J1721-2457 (90),
J1730-2304 (111), J1802-2124 (106), J1811-2405 (98), J1909-3744 (108), J1918-0642 (85). Two of those
matter downstream and are flagged where they do: **J1909-3744** — the pulsar the factorised product
turns on — clears the floor in `fl` by eight, and **J1600-3053** — the reinstated M2 claim — fails it
by eleven.

### 3.3 E5 — the falsifier returns a NEGATIVE result, and it is reported as one

> Runs the floor **admits**: 389 of 398 parameters agree, **97.7 %**.
> Runs the floor **rejects**: 187 of 190 parameters agree, **98.4 %**.
>
> **NEGATIVE.** The rejected runs agree with the published table *at least as well* as the admitted
> ones. **ESS_min is not diagnostic of fidelity to the published table in this problem.**

This is the registered consequence, applied: the floor is **retained only as a bound on our own
Monte-Carlo error** — which is a real and useful thing, and is why it stays a forward gate under
E2(2) — and it is explicitly **not** claimed to improve agreement with the published values.

The reason is visible in the list of rejected pulsars, and it is the same one R1 was built for: the
parameter holding the minimum ESS down is nearly always a prior-limited amplitude or index whose
posterior is 3–5 units wide. The A2 comparison on such a parameter is an interval-overlap test
between two very wide intervals, and it is insensitive to a factor of several in mixing. Poor mixing
in a flat direction does not move an overlap test. That is a statement about what A2 can resolve, not
an endorsement of poorly mixed chains — and it is the reason M4's R1 relaxation was safe.

### 3.4 E3 — every M4 headline, recomputed on the floored subset

| # | headline | as M4 reported it | on the ESS-floored subset | verdict |
|---|---|---|---|---|
| a | `noise` coverage | 83 / 83 | 65 / 83 | subset, by construction |
| b | agreement | **576 / 588 (98.0 %)**, 73 / 83 pulsars in full | 389 / 398 (97.7 %), 58 / 65 | **holds** |
| c | ΔlnL (ours − published) | median **+0.70**, 79+ / 4− | median +0.39, 62+ / 3− | **holds** (sign structure identical) |
| d | `fl` CURN | 83 psr, **−14.44** [−14.64, −14.35] | 56 psr, −14.39 [−14.58, −14.29] | **holds**, both consistent with published |
| d′ | `table` CURN | 83 psr, **−14.18** [−14.28, −14.13] | 63 psr, −14.44 [−14.51, −14.29] | **moves 0.25 dex** — §3.5 |
| e | seam-(b) product shift | **+0.259 dex** (82 psr), "significant" | +0.040 dex (52 psr), not significant | **MOVES — withdrawn, §3.5** |
| f | γ_SW variant | 10 of 10 misses resolved, 0 created | 7 of 7 resolved, 0 created | **holds** (3 pairs drop out; none breaks) |
| g | F5 one-pulsar step | width 1.92 → 0.37 dex at J1909-3744 | biggest single step 0.98 dex at J2129-5721 | **structure holds, identity does not** — §3.5 |

Two of these move, and both moves point at the same thing.

### 3.5 The one headline that moves, and why the reason is bigger than the ESS floor

**M4's B-2 headline was the seam-(b) product-level shift: +0.259 dex, declared significant against a
pre-registered 0.21 dex threshold.** On the ESS-floored subset it is +0.040 dex and not significant.
Before reading that as "the ESS floor breaks the headline", the obvious alternative had to be
measured, and it was — as a **declared post-hoc diagnostic**, `scripts/m5_seamb_subset_null.py`,
which is *not* in §1's registration and is labelled post-hoc wherever it is quoted.

Two measurements, and they are decisive:

> **Delete-1 jackknife over the 83 pulsars gated in both configurations: ΔMAP = +0.257 ± 0.212
> dex.** The registered F4 magnitude threshold was 0.21 dex — *the same number as the uncertainty
> nobody had computed*. The effect is **1.2σ**. Removing a single pulsar (J2129-5721) takes it to
> **+0.075**.
>
> **Random 52-of-83 subsets: ΔMAP has standard deviation 0.340 dex** and a 95% band
> [+0.002, +0.407]. The ESS-floored value sits at the 5.5th percentile of that band — a low draw,
> **inside** it.
>
> (M4 reported +0.259 dex on the 82 pulsars available to it; the 83rd arrived in M5's tail and moves
> it by 0.002 dex. The two are the same number and neither is resolved.)

So the ESS-floored value is **not** evidence against the full-array value; the two are not
distinguishable, because a subset version of this statistic carries almost no precision. The converse
is the real finding: **M4 declared a 0.26 dex shift significant using a threshold rule that had
never been given an uncertainty, and when the uncertainty is supplied the result is 1.2σ.**

**M4's B-2 quantitative headline is therefore withdrawn as a magnitude claim.** What replaces it is
better, not weaker, and it was already in the data — the *paired per-pulsar* form of the same
question, which never passes through a product (`scripts/m5_curn_stability.py`):

> Over the 70 pulsars where the two configurations genuinely differ, the common amplitude moves
> **down in 49** (sign test **p = 0.0011**; Wilcoxon signed-rank **p = 5.8 × 10⁻⁶**), median
> **−0.073 dex**. Over the 12 control pulsars — where the two runs are the *same model*, so any
> difference is sampler noise — the shift is consistent with zero (median +0.0004,
> Wilcoxon **p = 0.68**).

**The effect is real and its direction is established at 6 × 10⁻⁶ against a proper control; its size
in the factorised product is not established.** That is the honest split, and it is what the paper
says.

**Row d′ and row g are the same story told twice.** The `table` CURN product moves 0.25 dex when 19
of 83 pulsars are removed, while its own 68% interval is 0.149 dex wide; measured directly by
jackknife, its composition sensitivity is **0.256 dex — larger than its own credible interval**. And
the F5 growth curve's one-pulsar step survives as *structure* (there is still a single addition that
drops the width by ~1 dex) but which pulsar does it, and by how much, depends on which set is being
grown. Both are the same underlying fact, and it is a result in its own right: **a
factorised-likelihood product's credible interval understates how much it depends on which pulsars
are in it, and any comparison of two such products must be quoted with a composition jackknife.**

### 3.6 What the floor is worth

It failed its own falsifier, and it is kept anyway, for the reason E5 registered in advance: it
bounds the Monte-Carlo error on *our* numbers, independently of whether it improves agreement with
anyone else's. Concretely, at ESS_min = 100 every 68% interval edge we quote is determined to better
than 15% of its own half-width. That is the claim it supports, and it is the only claim made for it.

---

## 4. The solar-wind control, re-specified — and the prior-propping census (S-criteria)

`scripts/m5_sw_census.py`, `results/m5/sw_census.json`, `figures/m5_sw_census.png`.

### 4.1 S2 — the re-specified control PASSES, and M4's V4 count is reinstated

M4's registered control V5 keyed on the **sign** of the published γ_SW as a proxy for "measured", it
failed, and the registered consequence — V4's resolve count reported VOID — was applied. M5's S1
replaces the proxy with the thing itself: a row is **measured** when its γ_SW 68% posterior occupies
less than a quarter of the prior under **both** priors. Five pulsars qualify: **J0711-6830,
J1017-7156, J1732-5049, J1909-3744, J2241-5236**.

| pulsar | Δ median γ_SW | Δ median log₁₀A_SW | γ_SW 68% width, U(0,7) → U(−4,4) |
|---|---|---|---|
| J1732-5049 | −0.135 | −0.014 | 1.55 → 1.57 |
| J1017-7156 | −0.077 | −0.035 | 0.94 → 0.92 |
| J1909-3744 | +0.048 | +0.017 | 0.67 → 0.69 |
| J0711-6830 | −0.028 | +0.015 | 1.13 → 1.01 |
| J2241-5236 | −0.013 | −0.001 | 0.52 → 0.50 |

> Worst move **0.135** in γ_SW and **0.035** in log₁₀A_SW, against the inherited 0.19 yardstick;
> **0** parameters anywhere in the 26 stop agreeing under the wider prior. **S2: PASS.**

**Consequence, applied as registered: M4's V4 count is reinstated, and it is now at full
coverage.** Over **all 26** SW_Full pulsars — every one with both runs gated — the γ_SW ~ U(−4,4)
variant resolves **10 of the 10** solar-wind misses in the registered campaign and creates none, and
that statement no longer carries a VOID. (M4's own registered V5 verdict still reads FAIL when
`scripts/m4_swwide_compare.py` is re-run, because V5 is M4's criterion and M5 does not edit it; S2
is the replacement, and it is the one that tests the claim.) The machinery was never perturbing measured parameters; M4's
control set simply was not made of measured parameters, and M4 said so at the time — M5 supplies the
control that tests the claim it was meant to test.

**A prose/artifact mismatch in M4, found by re-deriving rather than re-reading.** M4 §4.3's
declared post-hoc control names **four** pulsars (J0711-6830, J1017-7156, J1732-5049, J2241-5236);
its own artifact `results/m4/swwide.json` (`posthoc_control.pulsars`) lists **five**, adding
J1909-3744. The artifact is right — J1909-3744's γ_SW occupancy is 0.10/0.09, the most tightly
measured in the column — and M5's independently written classifier returns the same five. M4's
*worst-move* number (0.135 on J1732-5049) is unaffected, because J1909-3744 moves by 0.048. Recorded
here as a correction to M4's prose.

### 4.2 S3 — the census

Over the SW_Full pulsars with both priors gated, classified by prior occupancy
(O = 68% width / prior width) and widening ratio (R = wide width / narrow width), with every
threshold fixed in §1.2 before the classification was run:

| class | rule | rows | median log₁₀A_SW 68% width, U(0,7) → U(−4,4) |
|---|---|---|---|
| **MEASURED** | O < 0.25 under both | **5** | 0.29 → 0.30 dex |
| **PRIOR-PROPPED** | R ≥ 2.0, not measured | **5** | 0.47 → **2.14** dex |
| **UNCONSTRAINED-BOTH** | O ≥ 0.25 under both, R < 2.0 | **15** | 2.75 → 3.04 dex |
| **OTHER** | J1125-5825 (R = 0.76: it *narrows* under the wider prior) | 1 | 2.38 → 2.12 dex |

> **PRIMARY (registered S3): 20 of the 26 published γ_SW rows are NOT a measurement of γ_SW under
> this reproduction** — 5 because their apparent constraint is the prior edge, 15 because they were
> never constrained under either prior. Only **5** are measurements.

**The five prior-propped rows** — the ones that look constrained and are not — are
**J1327-0755** (γ_SW width 0.89 → 3.32), **J1614-2230** (0.61 → 2.41), **J1811-2405** (0.73 → 2.69),
**J1744-1134** (1.52 → 4.42) and **J2145-0750** (1.52 → 3.79). Their **amplitude** widths go from
0.34–0.52 dex to 1.4–2.4 dex, so it is not only the index that was prior-supported but the
solar-wind amplitude the column is usually read for. These are exactly the five M4 §4.3 identified
post hoc; M5 arrives at them from a registered rule instead.

**S4 — the sensitivity grid, and the registered quoting rule bites.** Across
R ∈ {1.5, 2.0, 3.0} × O ∈ {0.20, 0.25, 0.33} the primary number ranges **16–20**, a deviation of 4
rows from the point value. §1.2 S4 registered that anything beyond ±2 must be **quoted as a range**,
so the primary number is quoted **16–20 of 26** wherever it appears, never as a point.

The complement is the more stable statistic and is reported beside it: **the count of rows that ARE
measurements is 5 at the registered thresholds and 4–7 across the entire grid.** The reason the
primary number moves more than its complement is a property of the classification cascade, not of
the data: at R ≥ 3 two prior-propped rows (J1744-1134 at R = 2.92, J2145-0750 at R = 2.49) fall into
OTHER rather than becoming measurements. **No point of the grid makes more than seven of the 26
rows a measurement of γ_SW**, and that is the sentence that carries the result.

*Implementation correction, declared (§1.5).* The first implementation of the S4 rule tested the
**total spread** against 4 rather than the **deviation from the point value** against 2, and that
looser reading would have licensed quoting "19" as a point. The registered wording is "moves by more
than ±2 rows"; the code was corrected to it, and the answer changed from a point to a range. The
looser version is not used anywhere.

### 4.3 S5 — how much of this a reader can see from the printed table alone

Classifying the **published printed** γ_SW 68% widths by their own occupancy of a candidate prior,
with no chains involved at all, agrees with the chain-based classification on **24 of 26 rows**.

> **A reader with the paper and nothing else can identify 18 of the 20 non-measurements. Two they
> cannot: J1614-2230 and J1744-1134** print γ_SW intervals of 1.73 and 1.47 — narrow, and around
> *positive* central values (+0.24 and +0.91) — that look like measurements and are not. Recognising
> those two requires re-running the chains under a wider prior, which requires knowing what the
> original prior was.

That is the sharpest form of the documentation argument this project has produced: the missing prior
range is not merely inconvenient, it is the difference between a column a reader can grade and one
they cannot. It also explains, precisely, why M4's V5 control failed: J1744-1134 is one of the two.

### 4.4 S6 — what this does and does not say

It measures **our** posteriors under **two priors we chose**, and it therefore states what a
reproducer working from public data can determine about that column. It does **not** state what the
collaboration's own chains did, because their prior is unpublished — which is claim (a) of the note
and the reason the census exists at all. **No claim is made anywhere that a published γ_SW value is
wrong.**

---

## 5. The paper (P-criteria) — DRAFTED, NOT SUBMITTED

The draft is [`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md).
It carries **DRAFT — NOT SUBMITTED** in its title and its first line, every author field is a
placeholder, and the archive DOI is a placeholder. Nothing has been sent to anyone.

### 5.1 The headline claim, in one sentence

> **An independent reproduction of the MPTA 4.5-year noise table from public data agrees with 576 of
> its 588 values, and every disagreement traces to a single undocumented prior — the solar-wind
> spectral index — whose published column is, on this measurement, mostly not a measurement.**

### 5.2 Shape and content

A&A/MNRAS short-paper shape: abstract, ten numbered sections, three tables, four figures, a
reference list, and two appendices. Sections 1–2 set up the release and the method (including the
pre-registration discipline and the two gate rules reported side by side); §3 is the reproduction;
§4 is the solar wind, ending in the census; §5 is what else in the table is prior rather than data;
§6 is the common signal; §7 is **Corrections to our own earlier analysis**; §8 threats to validity;
§9 the three caption-sized fixes; §10 data availability. Two clearly-marked non-paper sections at the
end list what remains before submission and what the draft deliberately does not contain.

**P4 — positioning, as registered.** Goncharov & Sardana (2025) and van Haasteren (2024) own the
general claim that prior choices bias PTA gravitational-wave inference, and the paper says so in its
second paragraph, in the words *"This paper claims none of that."* Hazboun et al. (2020) is cited
beside them for the model-dependence of PTA Bayesian statistics. What the paper claims as new is
four things and no more: the per-table value-by-value measurement; **the γ_SW unreachability and the
census, which is the novel part**; the size of the collaboration's own misspecification-mitigation
trade in the factorised amplitude; and the one-pulsar phase change in the factorised product.

**P3 — fairness, as a hard requirement.** The release's completeness is given as the reason the
paper can exist, in the abstract and again in §1, not in an acknowledgement — *"That openness is the
entire reason this paper exists"*. Every observation is paired with its fix. The paper's own §4.4
states that it **cannot** say a published value is wrong, and why. Where the MPTA paper already
flags something (the MAP-outside-interval caption, the "red or blue spectrum" statement, its own
misspecification section), it is quoted first and credited.

**P5 — the retractions are a numbered section with ten rows**, covering every claim this project
has withdrawn, narrowed or reinstated across M1–M5, including the two M5 adds: M4's product-level
seam-(b) magnitude (withdrawn, §3.5) and M4's four-vs-five control-set prose (§4.1). A paper that
hides its own retractions is worth less than one that shows them, and the same standard is being
applied outward.

### 5.3 P2 — every number traceable, and the checker

`scripts/m5_paper_numbers.py` re-derives **105 numbers** from committed artifacts and emits the audit
table in §6 below (claim → value → artifact → field). `scripts/m5_paper_check.py` then checks the
**drafted text** back against that artifact — the direction that actually catches transcription
slips, which is how `m4_note_check.py` earned its keep on the note:

> **90 checks, 0 failures.**

The checks are not cosmetic: they include the state marks (DRAFT, placeholders), every headline
count and interval, the census class counts and the named pulsars in each class, the registered
quoting rule for the sensitivity range, both sides of the E5 falsifier, and the presence of the
prior-art disclaimer, the retractions section and the submission checklist. Six mismatches were
caught and fixed on the first run, all of them checker-side (word forms, markdown emphasis, the
multiplication sign) rather than wrong numbers in the draft — recorded because a checker that has
never failed has not been tested.

### 5.4 What remains before it could be submitted

Stated inside the draft itself, in §11, and repeated here because it is the operative list:

**Matthew's, and only his:** author/affiliation/ORCID; **the archive DOI**, which is the single
blocking item and the same open item as M3's condition B-4; the choice of venue; whether to send the
collaboration paragraph first; and whether the Research Note goes out ahead of the paper.

**Still owed by the analysis, all small:** **software and facility citations**, which are currently
placeholders and are the only UNSOURCED items in the draft; a prior-art re-check dated to the week
of submission; exact package versions named inline once the archive is minted; and one cold read for
tone, because the argument only works if it is unmistakably a contribution rather than a complaint.

### 5.5 The note, reviewed and unchanged

[`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md) was re-derived
(`m4_note_numbers.py`: 29 audited, 28 PASS, 1 CORRECTED — the same M4 pre-registration row) and
re-checked (`m4_note_check.py`: **22 checks, 0 failures**). **No M5 result changes any number in
it**, because every claim in the note is a property of the published table requiring no sampling —
which is exactly the scope its N-criteria fixed. It is left as drafted, with a short addendum in its
non-note section recording that it was reviewed, that claim (b)'s "19 of 26" is a lower bound the
census now quantifies, and that a companion paper exists in draft. The note remains separately
publishable: none of its four claims depends on the reproduction.

---

## 6. P2 — the paper number audit (105 rows)

Emitted by `scripts/m5_paper_numbers.py --markdown`, which re-derives every number in
[`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md) from a
committed artifact. No number in the paper is transcribed from prose, including this
repository's own. `scripts/m5_paper_check.py` then checks the drafted text back against this
artifact: **92 checks, 0 failures.**

| # | claim | value | artifact | field |
|---|---|---|---|---|
| 1 | pulsars in the release | 83 | `results/m4/note_numbers.json` | `n_noise_rows` |
| 2 | tabulated parameter values with a printed interval | 588 | `results/m4/note_numbers.json` | `n_values` |
| 3 | sub-banded ToAs in the release (counted from the 83 .tim) | 245907 | `data/partim/*.tim` | `line count` |
| 4 | model inventory: chromatic Gaussian events | 15 | `results/m3/published_table.json` | `model.bump` |
| 5 | model inventory: annual chromatic variations | 8 | `results/m3/published_table.json` | `model.annual` |
| 6 | model inventory: free-index chromatic GPs | 13 | `results/m3/published_table.json` | `model.chrom_free` |
| 7 | model inventory: fixed-index chromatic GPs | 10 | `results/m3/published_table.json` | `model.chrom_fixed` |
| 8 | model inventory: DM GPs | 49 | `results/m3/published_table.json` | `model.dm` |
| 9 | model inventory: solar-wind GPs | 26 | `results/m3/published_table.json` | `model.sw_full` |
| 10 | model inventory: free achromatic red processes | 12 | `results/m3/published_table.json` | `model.red` |
| 11 | model inventory: EQUAD terms | 20 | `results/m3/published_table.json` | `model.equad` |
| 12 | model inventory: ECORR terms | 29 | `results/m3/published_table.json` | `model.ecorr` |
| 13 | pulsars whose release ships as many ToAs as its ephemeris was fitted to | 63 | `results/m3/a1_summary.json` | `records[].ntoa == ntoa_pub` |
| 14 | pulsars that ship fewer ToAs than their ephemeris fitted | 20 | `results/m3/a1_summary.json` | `records[]` |
| 15 | median |wRMS - TRES| / TRES over the complete set (%) | 0.015 | `results/m3/a1_summary.json` | `records[].frac` |
| 16 | pulsars clearing the registered (relative) gate | 83 | `results/m4/agreement_both_gates.json` | `relative.n` |
| 17 | pulsars clearing the absolute (M1-M3) gate | 76 | `results/m4/agreement_both_gates.json` | `absolute.n` |
| 18 | parameters agreeing under the registered A2 rule | 576 | `results/m4/agreement_both_gates.json` | `relative.params_agree` |
| 19 | parameters compared | 588 | `results/m4/agreement_both_gates.json` | `relative.params_total` |
| 20 | agreement rate (%) | 98.0 | `results/m4/agreement_both_gates.json` | `relative.pct` |
| 21 | pulsars agreeing on every tabulated value | 73 | `results/m4/agreement_both_gates.json` | `relative.n_full` |
| 22 | parameters missing | 12 | `results/m4/agreement_both_gates.json` | `derived` |
| 23 | misses that are solar-wind parameters | 10 | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 24 | misses that are the Gaussian-event width | 2 | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 25 | the miss keys themselves | {"bump_sigma": 2, "sw_gamma": 8, "sw_log10_A": 2} | `results/m4/agreement_both_gates.json` | `miss_keys` |
| 26 | median dlnL(ours - published) | 0.7 | `results/m4/agreement_both_gates.json` | `dlnl.median` |
| 27 | pulsars with dlnL > 0 | 79 | `results/m4/agreement_both_gates.json` | `dlnl.n_pos` |
| 28 | pulsars with dlnL < 0 | 4 | `results/m4/agreement_both_gates.json` | `dlnl.n_neg` |
| 29 | most negative dlnL | -0.67 | `results/m4/agreement_both_gates.json` | `dlnl.min` |
| 30 | lowest acceptance over gated runs | 0.158 | `results/m4/agreement_both_gates.json` | `relative.acc_min` |
| 31 | highest acceptance over gated runs | 0.527 | `results/m4/agreement_both_gates.json` | `relative.acc_max` |
| 32 | pulsars whose favoured model samples gamma_SW | 26 | `results/m4/note_numbers.json` | `n_swfull` |
| 33 | published gamma_SW values that are negative | 7 | `results/m4/note_numbers.json` | `n_sw_gamma_negative` |
| 34 | further rows whose 68% interval crosses zero | 12 | `results/m4/note_numbers.json` | `n_sw_gamma_ci_crossing` |
| 35 | rows outside or straddling gamma in [0,7] | 19 | `results/m4/note_numbers.json` | `n_sw_affected` |
| 36 | published values below the e_e U(-2,1) floor | 2 | `results/m4/note_numbers.json` | `n_sw_below_ee_default` |
| 37 | lowest printed gamma_SW 68% lower edge | -3.21 | `results/m4/note_numbers.json` | `sw_gamma_lowest_ci_edge` |
| 38 | the pulsar it belongs to | J1811-2405 | `results/m4/note_numbers.json` | `sw_gamma_lowest_ci_edge_psr` |
| 39 | enterprise_extensions solar_wind_block gamma default | [-2.0, 1.0] | `results/m4/note_numbers.json` | `ee_sw_gamma_default` |
| 40 | SW_Full pulsars with both priors gated (M4 variant) | 26 | `results/m4/swwide.json` | `compared` |
| 41 | campaign misses covered by the variant | 10 | `results/m4/swwide.json` | `n_miss_registered` |
| 42 | misses remaining under U(-4,4) | 0 | `results/m4/swwide.json` | `n_miss_variant` |
| 43 | misses created by the wide prior | 0 | `results/m4/swwide.json` | `created` |
| 44 | SW_Full pulsars in the census | 26 | `results/m5/sw_census.json` | `n_compared` |
| 45 | census class MEASURED | 5 | `results/m5/sw_census.json` | `counts.MEASURED` |
| 46 | census class PRIOR-PROPPED | 5 | `results/m5/sw_census.json` | `counts.PRIOR-PROPPED` |
| 47 | census class UNCONSTRAINED-BOTH | 15 | `results/m5/sw_census.json` | `counts.UNCONSTRAINED-BOTH` |
| 48 | census class OTHER | 1 | `results/m5/sw_census.json` | `counts.OTHER` |
| 49 | rows that are NOT a measurement of gamma_SW | 20 | `results/m5/sw_census.json` | `primary` |
| 50 | how the primary number must be quoted (S4 rule) | 16-20 | `results/m5/sw_census.json` | `sensitivity.quote` |
| 51 | MEASURED count across the sensitivity grid | [4, 7] | `results/m5/sw_census.json` | `sensitivity.measured_range` |
| 52 | re-specified control set size | 5 | `results/m5/sw_census.json` | `control.n` |
| 53 | worst |d median gamma_SW| over the control set | 0.135 | `results/m5/sw_census.json` | `control.worst_d_gamma` |
| 54 | S2 control verdict | PASS | `results/m5/sw_census.json` | `control.verdict` |
| 55 | rows the printed table alone already flags | 19 | `results/m5/sw_census.json` | `table_only.counts` |
| 56 | rows the printed table alone CANNOT flag | ["J1614-2230", "J1744-1134"] | `results/m5/sw_census.json` | `table_only.divergent` |
| 57 | the prior-propped pulsars | ["J1327-0755", "J1614-2230", "J1744-1134", "J1811-2405", ... | `results/m5/sw_census.json` | `rows[].klass` |
| 58 | A_13/3 rows whose 68% reaches below -16.5 | 66 | `results/m4/note_numbers.json` | `n_a13_prior_limited` |
| 59 | A_13/3 rows constrained better than 0.7 dex | 6 | `results/m4/note_numbers.json` | `n_a13_better_than_0p7` |
| 60 | median 68% width of the prior-bounded A_13/3 rows | 3.01 | `results/m4/note_numbers.json` | `a13_median_width_prior_limited` |
| 61 | values whose MAP lies outside their own 68% interval | 26 | `results/m4/note_numbers.json` | `n_map_outside` |
| 62 | pulsars affected | 22 | `results/m4/note_numbers.json` | `n_pulsars_map_outside` |
| 63 | median decorrelating reference frequency (MHz) | 857 | `results/m3/seam_a.json` | `nu_pivot_MHz (free-beta rows)` |
| 64 | median log10A_Chrom 68% width at 1400 MHz (dex) | 0.46 | `results/m3/seam_a.json` | `width_A_1400` |
| 65 | the same width at the pivot frequency (dex) | 0.19 | `results/m3/seam_a.json` | `width_A_pivot` |
| 66 | free-beta chromatic pulsars that are prior-driven | 2 | `results/m3/seam_a.json` | `prior_driven` |
| 67 | free-beta chromatic pulsars | 13 | `results/m3/seam_a.json` | `chrom == free` |
| 68 | pulsars in the fl factorised-likelihood product | 83 | `results/m5/curn_stability.json` | `fl.n` |
| 69 | fl product MAP log10 A_CURN | -14.439 | `results/m5/curn_stability.json` | `fl.map` |
| 70 | fl product 68% interval | [-14.642, -14.348] | `results/m5/curn_stability.json` | `fl.ci68` |
| 71 | fl product 68% width | 0.294 | `results/m5/curn_stability.json` | `fl.ci68_width` |
| 72 | fl product jackknife SE over pulsar composition | 0.137 | `results/m5/curn_stability.json` | `fl.jackknife_se` |
| 73 | pulsars in the table-configuration product | 83 | `results/m5/curn_stability.json` | `table.n` |
| 74 | table product MAP | -14.183 | `results/m5/curn_stability.json` | `table.map` |
| 75 | table product 68% interval | [-14.283, -14.134] | `results/m5/curn_stability.json` | `table.ci68` |
| 76 | table product 68% width | 0.149 | `results/m5/curn_stability.json` | `table.ci68_width` |
| 77 | table product jackknife SE over pulsar composition | 0.256 | `results/m5/curn_stability.json` | `table.jackknife_se` |
| 78 | pulsars in the paired seam-(b) test | 70 | `results/m5/curn_stability.json` | `seam_b_paired.n_test` |
| 79 | of those, moving DOWN | 49 | `results/m5/curn_stability.json` | `seam_b_paired.n_down` |
| 80 | median per-pulsar shift (dex) | -0.0728 | `results/m5/curn_stability.json` | `seam_b_paired.median` |
| 81 | sign-test p | 0.0011 | `results/m5/curn_stability.json` | `seam_b_paired.sign_test_p` |
| 82 | Wilcoxon signed-rank p | 5.8e-06 | `results/m5/curn_stability.json` | `seam_b_paired.wilcoxon_p` |
| 83 | control pulsars (same model twice) | 12 | `results/m5/curn_stability.json` | `seam_b_paired.n_control` |
| 84 | Wilcoxon p on the control set | 0.677 | `results/m5/curn_stability.json` | `seam_b_paired.control_wilcoxon_p` |
| 85 | product-level shift (table - fl) on the common set | 0.257 | `results/m5/seamb_subset_null.json` | `dmap_all` |
| 86 | pulsars in that comparison | 83 | `results/m5/seamb_subset_null.json` | `n_common` |
| 87 | delete-1 jackknife SE of that shift | 0.212 | `results/m5/seamb_subset_null.json` | `jackknife.se` |
| 88 | the shift in units of its own jackknife SE | 1.2 | `results/m5/seamb_subset_null.json` | `derived` |
| 89 | the registered F4 magnitude threshold | 0.21 | `results/m5/seamb_subset_null.json` | `jackknife.f4_threshold` |
| 90 | single pulsar whose removal moves it most | ["J2129-5721", 0.075] | `results/m5/seamb_subset_null.json` | `jackknife.most_influential` |
| 91 | addition at which the FL product leaves the prior rail | 58 | `results/m4/fl_growth_fl.json` | `curve` |
| 92 | the pulsar responsible | J1909-3744 | `results/m4/fl_growth_fl.json` | `curve` |
| 93 | 68% width just before that step (dex) | 1.92 | `results/m4/fl_growth_fl.json` | `curve` |
| 94 | 68% width just after (dex) | 0.37 | `results/m4/fl_growth_fl.json` | `curve` |
| 95 | MAP swing over the final ten additions (dex) | 0.0303333333333331 | `results/m4/fl_growth_fl.json` | `map_swing_last10` |
| 96 | the registered floor | 100 | `results/m5/ess_floor.json` | `floor` |
| 97 | noise runs gated / clearing the floor | [83, 65] | `results/m5/ess_floor.json` | `coverage.noise` |
| 98 | table runs gated / clearing the floor | [83, 63] | `results/m5/ess_floor.json` | `coverage.table` |
| 99 | fl runs gated / clearing the floor | [83, 56] | `results/m5/ess_floor.json` | `coverage.fl` |
| 100 | swwide runs gated / clearing the floor | [26, 18] | `results/m5/ess_floor.json` | `coverage.swwide` |
| 101 | agreement rate over runs the floor ADMITS | 97.74 | `results/m5/ess_floor.json` | `e5_falsifier.admitted.pct` |
| 102 | agreement rate over runs the floor REJECTS | 98.42 | `results/m5/ess_floor.json` | `e5_falsifier.rejected.pct` |
| 103 | E5 falsifier verdict | NEGATIVE | `results/m5/ess_floor.json` | `e5_falsifier.verdict` |
| 104 | core-hours recorded on the final launch of each run | 192.4 | `results/m3/*.summary.json` | `elapsed_min` |
| 105 | runs with a recorded final launch | 277 | `results/m3/*.summary.json` | `elapsed_min` |

---

## 7. Economics

- **≥ 192.4 core-hours** recorded across 277 runs on the *final launch of each*
  (`results/m3/*.summary.json`, `elapsed_min`). As in M4 this is a firm lower bound: `elapsed_min`
  resets on resume and most runs were resumed at least once. M4 recorded ≥ 187 on 275 runs; M5's tail
  added the difference.
- **The tail cost 1.15 core-hours of recorded run time on two runs** — `table` 13.5 min for 13,500
  further raw post-burn iterations, `swwide` 55.5 min for 44,250 — at 4 BLAS threads each on an
  otherwise idle 32-core box, i.e. about 1.2 hours of wall clock end to end. J1525-5545 is 5–6× the
  array's median cost per evaluation, and both outstanding runs being the same pulsar is not a
  coincidence.
- **What the analysis cost.** Every M5 measurement — the ESS floor over 275 runs, the census, the
  jackknives, the 400-draw subset null, the figures, the paper's 93-number audit — is
  post-processing on artifacts already on disk and runs in under fifteen minutes total on one core.
  The expensive thing in this project has always been the chains; nothing in this milestone needed a
  new one except the two that were already owed.

---

## 8. The venue bar, and the recommended M6

### 8.1 M3's four conditions, re-scored

| condition | M4 | M5 |
|---|---|---|
| **B-1 Coverage** | MET (83/83) | **MET, and now closed on disk** — 83/83 `noise`, 83/83 `table`, 83/83 `fl`, 26/26 `swwide`, with a completion sentinel saying so |
| **B-2 A quantitative headline the collaboration has not published** | MET, on the +0.259 dex product shift | **MET, but on a different number.** The product-level shift is withdrawn (1.2σ, §3.5). What carries B-2 now is (i) the **census** — of the 26 published γ_SW rows, 16–20 are not measurements and at most seven are, with two of them undetectable from the printed table; (ii) the **paired** seam-(b) result, 49 of 70 down at Wilcoxon p = 5.8 × 10⁻⁶ against a control consistent with zero; and (iii) the **composition sensitivity** of factorised products, where the `table` product's jackknife SE (0.256 dex) exceeds its own 68% width (0.149 dex) |
| **B-3 Constructive and fair** | MET | **MET** — and M5 withdrew one of M4's own headlines, corrected M4's control-set prose, corrected its own S4 implementation against its own registration, and reports its registered ESS floor as having failed its own falsifier |
| **B-4 Reproducibility of the reproduction** | MET in substance, PENDING in form | **unchanged: PENDING.** The archive DOI is a human step and has not been taken |

**Verdict: three of four met, the gap is still B-4, and B-4 is still not a measurement.** The paper
is drafted and internally checked; it cannot go out until §10's DOI exists, and it should not — a
paper whose central observation is an unpublished prior would be self-defeating if it did not publish
its own.

### 8.2 Recommended M6

1. **Close B-4.** Deposit priors, models, harness, per-run summaries, the parsed published table and
   the CURN marginals under a DOI, and replace the placeholder in the paper's §10 and §11. This is
   Matthew's step and it is the only thing standing between the draft and a submittable paper.
2. **Fill the paper's UNSOURCED slots** — the software and facility citations (§5.4). Small, and it
   is the only category of number in the draft that is not traceable to an artifact.
3. **Re-run the prior-art sweep the week of submission.** The last one is dated 2026-08-23, rests on
   one citation provider plus a count from another, and is the check most likely to have changed.
4. **Give the composition jackknife its own short treatment.** §3.5 turned up, almost incidentally,
   that a factorised-likelihood product's credible interval can understate its dependence on set
   composition by more than a factor of 1.5 — and that a difference-of-two-products significance rule
   without a composition term is not a significance test. That is a methods result about a technique
   several PTAs use, it costs no new chains, and it may be worth a short methods note of its own
   rather than four paragraphs inside this paper.
5. **If, and only if, more chains are ever run:** they are now gated on R1 **and** acceptance ≥ 0.05
   **and** ESS_min ≥ 100 (E2(2)). The natural first candidates are the three `swwide` pairs the floor
   drops (J0900-3144, J1643-1224, J1652-4838), because all three are pulsars where the variant
   resolves a miss, and J1525-5545's `swwide` run (min-ESS 86, relative-gate-only), because it is the
   census's one row that leans on both relaxations at once. None of them changes a reported number;
   they would only remove caveats.
6. **Still deferred, unchanged from M1–M4:** the full-PTA (non-factorised) CURN posterior, and all
   Hellings–Downs and continuous-wave work, until the sparse-stack upgrade lands.

### 8.3 What M5 did not do

No submissions, no accounts, no outward sends, no commits, no pushes. The paper is DRAFT — NOT
SUBMITTED with placeholder author fields and a placeholder DOI; the Research Note is unchanged and
still DRAFT — NOT SUBMITTED; the collaboration paragraph inside it is still DRAFTED — NOT SENT and
has no addressee. The `enterprise` 3.5.0 upstream report M2 identified is still unfiled and still
Matthew's call.
