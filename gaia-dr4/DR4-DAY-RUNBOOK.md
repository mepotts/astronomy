# DR4-DAY-RUNBOOK — 2026-12-02

*The operational sequence for release day, rehearsed end-to-end against DR3 on 2026-08-16
(`scripts/rehearse_dr4_day.py`, timings in `out/rehearsal_timings.csv`; M3 doc §3).
Config: `queries/dr4-triage-config.v2.json` (selection/screen frozen since M2; v2 adds the
covariance probability method + dust tier). Everything below is anonymous-TAP-safe; if the
Gaia Archive account exists by then (Matthew's TODO), the async branch gets a longer rope,
nothing else changes.*

**Standing rules.** Politeness gaps ≥ 0.5 s between sync calls; every bulk pull ends with
an exact `COUNT(*)` guard; nothing is published from a partial pull; negative results are
results. All commands below run from `gaia-dr4/` with `.venv\Scripts\python.exe`.

---

## Phase 0 — the moment the archive answers (T+0, ~15 min)

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
   incl. MC, plots and the gate — `out/rehearsal_timings.csv` stage D): config v2
   parameters — P ∈ [10, 2200] d,
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

## Phase 3 — the epoch-vet loop, the false-positive killer (T+2 h onward)

For every candidate, in priority order (Pr(III|corr) desc, retrieval bin's Pr ≥ 0.999
members interleaved — DR3's probable-NS at Pr 0.9997 is the archetype):
1. `has_epoch_astrometry` flag via TAP (in `gaia_source` and `all_source_flags`);
2. **DataLink fetch** (`retrieval_type='EPOCH_ASTROMETRY'`) — **not a TAP table** (M1
   finding #1); astroquery, batched politely, resumable;
3. `gaiasupdate` single-star fit → **|f2| ≤ 5 ⇒ DEMOTE** (no epoch-level wobble ⇒ the
   photocentre orbit has no epoch support); f2 ≫ 5 ⇒ keep → orbital refit
   (`scripts/fit_prerelease_orbit_bh3.py` pattern). Rehearsed on the pre-release file:
   3/3 orbit sources kept, 9/9 quiet sources demoted.
4. **eROSITA cross** (`scripts/erosita_xmatch.py` against the local DR2 catalogs,
   ~4 min): on DR3 this found 30/471 coronal counterparts and 0 accretors. **An X-ray
   match is an activity/spurious-risk tag first** (the one EB26-refuted match was the
   X-ray-loudest relative to its star), **a headline only if log f_X/f_opt ≳ 0.**

## Failure branches (rehearsed or measured)

| symptom | branch |
|---|---|
| async job QUEUED > 30 min | plan-B ranged sync pull (Phase 1) — delivered 169k rows in ~35 min twice |
| sync range hits 2,000-row cap | halve PACK for that range and re-pull; never accept a capped result |
| assembled ≠ exact COUNT(*) | find the gap via per-range recount; the histogram is approximate near 2^53, the COUNT is law |
| `nss_masses` row missing for a target (BH2 syndrome) | three-tier M₁ handles it; never hard-require a mass row (M2 landmine #2) |
| join fan-out (rows > distinct sources) | expected: dual solutions + multi-row masses; dedupe on (source_id, solution_type) + combination_method preference; count both sides |
| DataLink refuses/throttles | batch smaller, resume from the per-source cache; epoch-vet is restartable by design |
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
- the eROSITA cross of the new list (in-footprint count, matches, chance control,
  f_X/f_opt reads, the null-or-not statement).
**Checked, not shipped**: any single-object claim before its epoch-vet verdict + the
  M2/M3 caution list (1-yr alias, low-|b|, σ_TI² > 20, X-ray-active).

**72 h**:
- epoch-vet verdicts for the full priority queue; demotion statistics (the DR3-calibrated
  expectation: ~30 % of screen survivors are spurious — El-Badry operating point);
- the retrieval-bin adjudication (DR3 analog: 239 rows, 32 at Pr ≥ 0.999);
- HVS 6D rerun (W5) and the microlensing-input refresh (W4) start once the NSS thread is
  stable;
- draft-1 of the first-weeks note on whatever survived both epoch vetting and the caution
  list — target selection per `../DISCOVERY/run3-prospectus.md` axis #4.

**Never**: submissions, account creation, or externally-visible claims without Matthew's
explicit go (repo law).
