# Handoff

Start here if you are picking this project up cold. It exists because the expensive
knowledge in this repository is not the code — it is the list of things that were tried,
measured, and found to be wrong. That list is spread across eight documents and would
otherwise have to be rediscovered.

**One-line status:** M0–M5 + M7–M14 executed, the MPC's Isolated Tracklet File searched at
~100% coverage on both slices, **zero linking discoveries**, 616 tests green. The durable
outputs are a validated linking pipeline, a daily archive that independently confirmed 21
of its own groupings, a replicated methodological result drafted for publication — and an
**attribution** capability (ITF tracklet → known orbit) at production scale: a perturbed
ephemeris backend measured against Horizons (and to 28 y on TNOs: ≤ 0.45″), the full
Feb+April Rubin batches plus the June/July/August partitions swept under decoy controls,
and a candidate ledger now holding **733 live unsubmitted PASS rows across ~695 objects
(M8's 482 + M9's 272, 90% beyond the old 4-year window), a 45-object combined-fit tier
(40 passing, arc extensions to +5,107 d), 87 of 88 lost-object ambiguities resolved** —
plus M7's held pair (2025 PD152; 2025 MQ241 borderline, joined by M9's 2026 AK20), all
awaiting Matthew's per-batch review, now **ranked and ready to open at
`out/review-queue-v2-20260823.csv`** (M11's versioned successor to M10's
`out/review-queue.csv`, which is kept byte-identical alongside it). **Of the 103 ledger
tracklets the MPC has consumed since 08-16, 97 went to exactly the object the ledger
named — 68/68 of the PASS rows — and the five that did not were all rows the strict gate
had already refused** (`M11-RESULTS.md` §1): external ground truth for the chain,
agreeing on everything it asserted, and the gate's first five measured true negatives.
The **15–25 y shell tier** is separately priced: **0 of 300 decoy fits pass against 76 of
300 real** (`M11-RESULTS.md` §4), the MPC has consumed six of its PASS rows and agreed
with all six — but its multi-tracklet objects pass their combined fit only 3 of 10, so
the tier is **recorded, not promoted, and stays out of the review queue**. Nothing has
ever been submitted. **M12** then read the daily archive as a *series* for the first time:
the ITF is **draining 4.4 : 1** (−129,759 observations in 26 days), the departures are whole
tracklets being **linked** — 133 of a random 150, none of them ledger rows, confirmed against
the absorbing objects' own published records — and a **five-day collapse in Pan-STARRS intake**
(81% of everything entering the file, down 86×) is recorded that the MPC's own servers can no
longer show, since they serve only the current ITF. **M14** then authenticated the two new
August 19/24 canonical Rubin aggregates, but its anatomy accounting missed two rows with
neither `provid` nor `permid`; the prospective internal plan said to stop there. The later
real/decoy and 0/100 fit work is exploratory, and the residual-selector provenance bug can
create false FAILs. Exact accounting bounds the post-stop diagnostic at 0–2/100, with two
usage-HOLD rows, but it is noninferential. M14 opened no candidate queue and
its runner is retired pending a new preregistration (`M14-RESULTS.md`).

---

## 1. Read in this order

| # | File | Why |
|---|---|---|
| 1 | `SPEC.md` | What the ITF is and why it is worth mining |
| 2 | `../DISCOVERY/itf-linker.md` | The plan, its milestones, and the guardrails. **Read the guardrails before touching submission code.** |
| 3 | `M0-RESULTS.md` | Parsing, tracklets, and why the obvious validation is impossible |
| 4 | `M1-RESULTS.md` | Find_Orb, validated against JPL Horizons, and the subset guard's origin |
| 5 | `M2-RESULTS.md` | The vetting layer and its controls |
| 6 | `M3-RESULTS.md` | HelioLinC linking. The longest and most useful document |
| 7 | `M4-RESULTS.md` | Widened grid, NEOs and TNOs, and a negative result |
| 8 | `M5-RESULTS.md` | The older 80% of the file, fitted completely |
| 9 | `M7-RESULTS.md` | **Attribution** (tracklet → known orbit) against Rubin's bulk-batch orbits: the measured two-body window, the decoy control, and why the MPC got there first |
| 10 | `M8-RESULTS.md` | Attribution at **full batch scale**: the perturbed backend (measured ~100× tighter than two-body at 5–15 y), bulk MPCORB orbits, the decoy at scale, the checkpointed fit queue, ledger v2, and the batch watcher |
| 11 | `M9-RESULTS.md` | The unconsumed partitions consumed, the queue extended under a pre-registered stopping rule, combined fits for the multi-tracklet tier, the 88 ambiguities adjudicated — and the MPC **independently confirming 30/30 consumed M8 candidates**, ground truth the chain never had before |
| 12 | `M10-RESULTS.md` | The ledger refreshed against a same-hour pull for review (`out/review-queue.csv`), the decay clock re-measured across three intervals and found concentrated in M8's queue head alone, M9's 60 ambiguities adjudicated, the 15–25 y main-belt shell, and the pointed-field screen validated and measured |
| 13 | `M11-RESULTS.md` | The shell's **fit stage priced with a decoy** (0/300 vs 76/300) and the finding that the primary "did fo use the tracklet" gate does all the discriminating; the shell's deep end closed at 20.74 y; the cumulative ledger refreshed after the archive pruned the base snapshot; the versioned review queue |
| 14 | `M12-RESULTS.md` | The daily archive read as a **series** rather than as snapshot pairs: the ITF is draining 4.4 : 1, the departures are whole tracklets being linked (confirmed against the objects' own published records), and a five-day collapse in Pan-STARRS intake that only a daily archive could have recorded |
| 15 | `M14-PLAN.md` + `M14-RESULTS.md` | Anatomy-first intake of the August 19/24 aggregates; the post-run accounting/provenance breach, exploratory 0–2/100 diagnostic bound, and required repair |
| 16 | `SNAPSHOT-VALIDATION.md` | The one check independent of the whole pipeline |
| 17 | `docs/archive-operations.md` | How the daily archive runs and how it has failed |
| 18 | `docs/rnaas-subset-guard.md` + `rnaas-notes.md` | The publishable finding, and its 14 known weaknesses |

`git log` is worth reading; commit messages carry the reasoning, not just the change.

## 2. Corrections and bugs — the index

Everything below was believed, written down, and later found wrong. **Check this list
before re-deriving anything or asserting a claim from an older document.**

### Claims that were published in this repo and are false

| Claim | Reality | Where |
|---|---|---|
| The subset guard rejects more than "every published criterion combined" | False. Published criteria reject 9,876; the guard 9,383. True comparison is against the RMS ceiling alone (9,383 vs 6,312), and the ordering **reverses** on survey-made associations (59 vs 263) | `M4-RESULTS.md` §9, dated note |
| "A wrong link does not raise residuals" | Too strong. Guard-rejected fits do carry higher median RMS (0.39″ vs 0.21″). The defensible claim is the 0.25″ threshold does not *act* on it — 80% of converged fits inside the ceiling are subset fits | `M4-RESULTS.md` §9 |
| An Atira *requires* the near branch | False. The far branch also clusters one inside the radius. Narrowed to "half the valid states inside 1 AU the old solver could not express" | `M4-RESULTS.md` §2.2 |
| 29P sat in a band M3 could not reach | False. Its hypothesis is at 5.6 AU, the **shared ceiling of both grids**. What made it findable is the *slice*, not the band | `M4-RESULTS.md` |
| M4's fit ordering was good prioritisation | It scored **worse than a random shuffle** (0.000/0.025/0.102 vs 0.127/0.271/0.517 at top 10/25/50%) | `M5-RESULTS.md` §2 |
| "The ledger's decay is **entirely** in M8's queue head — M9 PASS **0 of 272**, half-life > 101 d, Fisher p = 7 × 10⁻⁵" (M10 §2) | A two-day sample of a bursty process, as M10's own trap 2 warned. Over seven days M9 PASS lost **12 of 272** (half-life 106 d) against M8's 50 of 482 (43.8 d): real but **2.4×, not infinite** (p = 0.0024) | `M11-RESULTS.md` §1.2, `M10-RESULTS.md` addendum |
| "The 24–25 y bin has 14,717 coarse matches **that nothing has fitted**" (M10 §9 item 4) | M10's own head already held 90 fits at 21–25 y, all zero fit-grade. The *yield* stopped at −20.74 y, not the queue | `M11-RESULTS.md` §5.0 |
| "**Thirteen** objects carry ≥ 2 passing shell tracklets" (M10 §5.2) | Thirteen counts *fit-grade* fits; the verdict chain leaves **10** with ≥ 2 PASS rows, of which only 3 survive a combined fit — and M10's flagship **2015 KP488 is one of the failures** | `M11-RESULTS.md` §3.2 |

### Methods that were tried and do not work

| Approach | Why it fails | Where |
|---|---|---|
| Re-deriving known identification MPECs as a kill-check | The ITF contains **zero designated objects**; those MPECs link previously-designated ones. The test could not pass on any snapshot, on any day | `M0-RESULTS.md` |
| Detecting reused tracklet IDs by apparent sky motion | Great-circle separation saturates at 180°, so a long gap implies a *small* rate. `des278` computes to 0.021°/day, slower than a main-belt asteroid | `M3-RESULTS.md` §5, `fit/collide.py` |
| Single-linkage clustering | Chains catastrophically on real data — a Pan-STARRS/DECam field at RA 349° merged 50 tracklets into one "object". Replaced by three structural rules. **Do not weaken them** | `M3-RESULTS.md` §5.1 |
| Enumerating triplets | 15.4M pairs vs **753M triplets** at the same partitioning. Non-negotiable: use pair→predict→confirm or clustering | `M0-RESULTS.md` |
| Widening the clustering radius | Makes results *worse*, not merely noisier — 0.872 → 0.772 exact recall | `M3-RESULTS.md` §5.2 |
| Densifying the hypothesis grid | Moves recall 0.06 percentage points. The grid was never the limit | `M4-RESULTS.md` |

### Silent failures — the ones that cost real data

| Bug | Symptom | Fix |
|---|---|---|
| **Delta of zero when unmeasurable** | Archive logged `{appeared: 0, disappeared: 0}` across a step where 21,627 observations had left. Indistinguishable from a genuine no-change, which really occurs | Walk back to the newest ancestor retaining a key set; every manifest now carries `delta_status`. `snapshot.py`, `tests/test_snapshot_delta_status.py` |
| **Lines ≠ observations** | Space-based observations occupy two lines (`S` sky + `s` spacecraft, whose x/y/z sit in the RA/Dec columns). NEOWISE counted exactly half | `mpc80.py` |
| **Find_Orb ships `PERTURBERS=0`** | Unperturbed fits, ~0.1″ over 7 days against a 0.25″ gate | `DATA-SOURCES.md` §4 |
| **Find_Orb below ~0.05″ declared sigma** | Destabilises: at 0.01″ a main-belt object fits to a = 3.33 AU against truth 1.458, **with a plausible-looking uncertainty** | `M1-RESULTS.md` |
| **`(rms or 9e9)`** | An RMS of exactly 0.0 is falsy; one record miscounted. **Fixed 2026-08-07** in both counter sites | `fit/pipeline.py`, `link/run.py`, `docs/rnaas-notes.md` |
| **Enumerated gitignore** | Listed report filenames one by one, missed M4's differently-named `m4-new.json` (108 MB), push rejected by GitHub | Now pattern `/m[0-9]*.json` |
| **`fo` residual records name the station `obscode`, not `obs_code`** | The wrong key matches nothing, so per-tracklet residual checks silently report every tracklet as *unused* — inverting the subset-guard question in M7's joint fits | Verified against a live `total.json` before trusting it; `scripts/m7_attribution.py` |
| **`_relabel` truncates to the 7-character trkSub field** | An 8-character fit tag (`m7att000`) silently labels the obs file `m7att00`; two tags in one run could collide into one object | 7-character tags; noted in `M7-RESULTS.md` §10 |
| **`get-obs` OBS80 for a merged object interleaves multiple packed designations** | Fed to `fo` unrelabelled, the "baseline" fit is per-designation *fragments*, not the object (2025 MH98 = three designations) | Relabel under one tag before any fit; `M7-RESULTS.md` §10 |
| **M8's resume path dropped `real_matches` from the final report** | The 08-17 tranche-2 run silently destroyed the 119,607-row ranked queue; `--resume-sweep` would KeyError, and "rank 901" pointed at nothing | Fixed in `m8_attribution.py`; queue regenerated bit-compatibly from the reconstructed snapshot (M9 §0.1, §10). Pre-fix report preserved at `data/raw/rubin/m8-attribution-asof-20260817.json` |
| **The MPC's object records update in the same cycle as the ITF removal** | Tempting to explain a "consumed but not in the object" row as republication lag. It is not: in the same six-hour window one candidate's object gained exactly the consumed tracklet's four rows while two others' records were byte-identical. A consumption that does not show up in the attributed object went **somewhere else**, and that is a measurable verdict, not a timing artefact | `M10-RESULTS.md` §1.1, `scripts/m10_refresh.py` |
| **One candidate can be recorded twice across milestones** | 2025 MQ241 + `nf2088` is both an M7 held row and M8's BORDERLINE row. A reviewer working from either document alone double-counts it; a naive queue emits it twice | Deduplicate by `(object, tracklet key)`; `scripts/m10_review_queue.py` |
| **The archive's retention prunes the snapshot a milestone pinned, and the refresh answers anyway** | `m10_refresh.py` scanned `data/snapshots/` for surviving key sets at/after `BASE_SNAPSHOT`. Five days after M10 the 08-16 … 08-20 key sets are gone, so element 0 became **08-21** and "consumed since 08-16" reported **18** where the truth was **103** — under a heading that still said 08-16 | `scan_series` now raises and names the substitute; `scripts/m11_snapshot_series.py` rebuilds the series exactly by inverting the contiguous `delta.parquet` chain (`keys(parent) = keys(child) − appeared + gone`). `M11-RESULTS.md` §1.0 |
| **`itf_observations_20260816_reconstructed.parquet` is the 08-16 ∩ 08-18 *intersection*, not the 08-16 table** | M9 dropped whole every tracklet that lost any observation, so verifying an 08-16 rebuild against it fails by exactly the tracklets consumed in between (106 ledger observations). Read as a rebuild error it would condemn a correct series | Verify at **08-18**, where the two must agree; use the delta walk for 08-16. `scripts/m11_snapshot_series.py` |
| **A refresh reusing an older milestone's "fresh" get-obs cache measures the wrong thing** | The agreement check asks whether a consumed tracklet is in the object's record *now*. Against M10's 08-18 cache every consumption since would read `CONSUMED_AND_DISAGREED` | `--fresh-cache` is explicit; every refresh gets its own directory. `scripts/m10_refresh.py` |
| **Combined fits took tracklet lines from *today's* ITF** | A tracklet the MPC has *partially* consumed since the sweep still appears in the current file with fewer observations, so the joint fit is silently of a different tracklet from the one the ledger passed | Accept live lines only when their count matches the pinned slim table, else use the verbatim `obs.txt` fo fitted. `scripts/m9_combined.py` |
| **Same-station sibling tracklets break JD-window residual attribution** | Pan-STARRS pairs can share the same *exposures* with near-duplicate astrometry 0.03–0.16″ apart; an obscode+JD-window match then counts the sibling's rows as yours (`obs_used > n_obs` on 7 of 29 combined fits) | Match per observation by epoch **and** observed RA/Dec (fo residual records carry both); `scripts/m9_combined.py`, `M9-RESULTS.md` §6 |

### Environment and harness traps

- **Find_Orb is 9× slower on `/mnt/c`** than a Linux scratch dir (437 s vs 47 s per 40-link chunk). Outputs verified identical before the change was kept.
- **Four `fo` harness traps** — `$HOME` inside single quotes, a relative `--workdir`, sharing `fo`'s own outputs between concurrent workers, dangling symlinks in incremental config dirs. All failed *silently*. `M1-RESULTS.md` §6.4b.
- **`git reset --hard` on a shared working tree destroyed an agent's uncommitted work.** Use `git branch -f <branch> <target>` to move a ref without touching the tree.
- **The MPC blocks datacenter IP ranges.** Actions runners cannot reach it; a residential connection resolves in 0.03 s. Do **not** route around this. `docs/archive-operations.md` §2.
- **JPL Horizons `TLIST` replies come back in chronological order regardless of the order requested.** M7's calibration paired its 1-year prediction with the 15-year truth row and measured a 65° "propagation error" on every target before this was caught (by predicting at the orbit epoch itself). Sort the request. `scripts/m7_calibration.py`.
- **`mpc_orb` (get-orb API) states are heliocentric *ecliptic* at an MJD/TDT epoch.** The linker is ICRS-equatorial end to end; unrotated they are up to 23.4° wrong. `attrib/core.py::parse_mpc_orb` asserts the declared frame per document and refuses others.
- **A streaming JSON parser that re-slices its buffer per object is O(chunk × objects)** — invisible to unit tests, hours-long on the real 1.56M-object MPCORB file. The index-based `raw_decode(buf, idx)` scan does the same file in 21 s. `attrib/bulk.py::iter_mpcorb_objects`, `M8-RESULTS.md` §9.
- **get-orb and MPCORB can quote different standard epochs on the same day** (MJD 61000 vs 61200, 2026-08-16). A same-epoch state comparison between the two routes silently compares nothing; M8 bridges the gap with the measured perturbed integrator before comparing. `scripts/m8_fetch_bulk.py`.
- **In the Asteroid Institute replica, the discovery asterisk is the `disc` column ('*')** — `designation_asterisk` is an all-null Boolean (2026-08-16). `disc` reproduces M7's Feb count (17,043) exactly.
- **A single-interval decay difference is a sample of one MPC batch sweep, not a rate.**
  Consumption is bursty (0.80 → 2.01 → 0.00 %/day across M10's three intervals) and
  strongly rank-dependent, so a pooled two-point number both overstates the deep queue's
  perishability and understates the head's. Measure per-interval and per-population.
  `scripts/m10_decay.py`, `M10-RESULTS.md` §2.
- **A decoy control cannot be reconstructed from a finished sweep report.**
  `m8_attribution.run_sweep(decoy=True)` does `m.pop("row")` — the decoy matches lose
  their tracklet identity — and only `fake[:100]`, *unranked*, is stored as
  `control_matches_sample`. Any milestone that wants to price a **fit** stage must
  re-run the control and then prove it is the same control: M11's reproduction gate
  (188,494 matches and five histogram bins, exact) is what licenses comparing its
  0-of-300 to M10's 76-of-300. `scripts/m11_shell_decoy.py`, `M11-RESULTS.md` §4.
- **A post-fit orbit-quality gate is the wrong instrument for a decoy, and it fails
  flatteringly.** Measured on the shell: the strict gate passes **295 of 300 decoy fits
  against 228 of 300 real**, because fo drops the fake tracklet whole and then grades the
  object's own pristine baseline orbit. The entire separation lives in the primary gate —
  *did fo use the tracklet* — at 162/300 real against **0/300** decoy (p = 1 × 10⁻⁶²).
  Never report a decoy comparison on the RMS gate alone, and never relax "fully used"
  without a decoy arm. `M11-RESULTS.md` §4.2.
- **"N objects with ≥ 2 passing tracklets" depends on which population you count.**
  M10's "13 multi-tracklet shell objects" counts *fit-grade* fits; the verdict chain then
  demoted one member each of three objects, leaving **10** with ≥ 2 PASS rows. State the
  population or the next milestone derives a different number and thinks something moved.
- **A "nothing has fitted this" claim needs checking against the fit report.** M10 §9
  item 4 said the 24–25 y bin was unfitted; M10's own head already held 90 fits at
  21–25 y (40 of them at 24–25 y) with zero fit-grade. It was the *yield* that stopped at
  −20.74 y, not the queue. `M11-RESULTS.md` §5.0.
- **A long bash heredoc silently truncates in the Claude Code harness** — a ~120-line
  `cat > file <<'EOF'` fails with "unexpected EOF while looking for matching `''`",
  the content having been cut before the terminator. Write long files with the
  file-writing tool.
- **A trkSub that IS the object's own packed designation sails through every gate.**
  The all-sky distant head held rows like `/18K03H` sitting 2.6" from **2018 KH3**
  (packed `K18K03H`) — the same seven characters with the century byte replaced. The
  separation is tiny *because it is the object*, the joint fit is excellent for the same
  reason, the duplicate rule does not fire (these are precisely the rows the MPC has not
  linked), and SkyBoT finds the object and records it as **confirmation**. 7 of the top
  200 were this. Measured across all 1,971 M8/M9/M10-shell ledger rows: **0** — the
  review queue is clean of it. `scripts/m10_pointed.py::self_designation`.
- **The decoy control cannot price a pointed field.** A half-period phase shift puts the
  decoy orbit where nobody was looking, so it measures chance alignment against the
  survey footprint — a different and easier question than "was this survey *tracking*
  the object?". Screen candidates whose object has a published same-station row within
  the same exposure. Validated 3/3 against M9's failures and measured against the live
  ledger (0 of 735 flagged): `scripts/m10_pointed.py`, `M10-RESULTS.md` §6.
- **A per-night scalar `astropy` ephemeris call costs milliseconds of Time-object overhead** — across 5k nights × dozens of orbit chunks × two sweeps that is minutes of pure overhead. Precompute Earth's state for all night midpoints in one vectorised call. `scripts/m8_attribution.py::NightIndex`.
- **The MPC newsletter index moved to Buttondown** (`buttondown.com/MPC_newsletter/archive/`; linked from the MPC front page). Every plausible `minorplanetcenter.net` index path 404s; the per-issue PDFs under `/media/newsletters/` still resolve. `scripts/watch_rubin_batches.py`.
- **The daily archive re-pulls the ITF under this repo**, so `data/raw/itf.txt.gz` and `data/parquet/itf_observations.parquet` are *the newest pull*, not the one the last milestone used — between M8 and M9 the MPC consumed 22,353 observations and the files moved. Pin the snapshot explicitly for any resumed or comparative work; the archive's content-addressed `obs_key` tables reconstruct an old snapshot exactly (`scripts/m9_reconstruct_snapshot.py`, `M9-RESULTS.md` §0.1).
- **Rubin partition size says nothing about attribution content.** The 100 MB 2026-08-10 partition is 99.4% numbered-object rows; two 13 MB partitions carry zero unnumbered objects; a 3.2 MB one carries 412 new discoveries. Measure `permid`/`provid` before planning a sweep (`M9-RESULTS.md` §1).
- **M8's “tracklet residual” selector does not preserve row provenance.** Published and
  appended observations receive one Find_Orb tag, then the code selects residuals by
  observatory plus a padded JD interval. In M14, 58 of 100 fits had published rows inside
  that window, 58 residual counts exceeded the real tracklet size, and two *used* counts
  did too. It cannot create a recorded above-total PASS, but it can create false FAILs;
  neither positive nor negative yield is valid until residuals are assigned one-to-one to
  exact appended observation identities. `M14-RESULTS.md` §5–6.

## 3. Standing constraints

1. **Nothing is submitted anywhere without explicit per-batch human review.** Automated
   end-to-end submission is permanently out of scope. The MPC tracks submitter reputation;
   a bad batch causes *future* reports to be disregarded.
2. **Validate against the sandbox first** — `submit_psv_test` / `submit_xml_test`.
3. **Contact SARC before any archival submission.** For DECam/SDSS that is Tyler Linder.
4. **A link passing every gate is not a discovery.** M3 vetted 30 and found three
   already-catalogued objects and no new ones. Report candidates as candidates.
5. **A zero yield reported plainly is a success condition**, not a failure. Do not loosen a
   threshold to produce candidates — M4 documents each lever that would have worked and
   confirms none was touched.
6. **Rate-limit and cache every external service.** ≥1.2 s, descriptive User-Agent, back
   off on error. Getting IP-banned from MPC services would be worse than any result.

## 4. Known-open items

- **Every `lnk…` id in this repo is run-local, and the ones already written down cannot be
  fixed.** `link_id` is a positional counter, so `lnk034r` means "row 4,347 of whichever
  link table this run produced". Across the two link tables here, **13,618 ids appear in
  both and not one denotes the same link.** Twice in one session this silently answered the
  wrong question — see §2. New runs now also carry **`link_key`**, a content-addressed id
  hashed from the member `(desig, obscode, night)` tracklets, which is stable across runs
  and is the only one that should ever be cited or joined on. The ids printed in M3–M5,
  `SNAPSHOT-VALIDATION.md` and the RNAAS drafts predate it and are **not** back-fillable
  without re-running the linker against the same ITF snapshot. Treat them as row numbers.
- The **RNAAS draft is a draft.** References unverified against ADS; nothing submitted.
- ~~**`pipeline.py:190`** `(rms or 9e9)` is logged but unfixed.~~ **Fixed 2026-08-07**, in
  `link/run.py` too. Stored reports predate it; a re-run now matches the drafts.
- The **archive misses days when the machine is off.** An always-on host on a residential
  connection would close that; see `docs/archive-operations.md` §1.
- The **MPC reachability email is drafted and unsent** — `docs/archive-operations.md` §5.
- **The candidate ledger decays at a measured rate, and the rate is not uniform.**
  M9 measured one interval and reported 3.3%/2 days over M8's 900 fitted rows. M10
  measured three intervals over the whole 1,900-row cumulative ledger and found the
  decay is **entirely in M8's queue head**: M8 PASS rows 21/482 (half-life **32 d**,
  95% CI 21–49) against M9 PASS rows **0 of 272** (half-life > 101 d), Fisher one-sided
  **p = 7.1 × 10⁻⁵**; inside M8's own queue the top half decays 2.8× faster than the
  bottom (`M10-RESULTS.md` §2). Consumption is also **bursty**, not a smooth hazard —
  the PASS population's per-interval rate ran 0.80 → 2.01 → 0.00 %/day — so a
  single-interval estimate samples one MPC batch sweep. Practical consequence for
  review order: **the M8 rows are the perishable ones.**
  **M11 (2026-08-23) re-measured this over eight intervals and M10's headline did not
  survive.** M9's PASS rows are *not* static: 12 of 272 gone in seven days (half-life
  106 d) against M8's 50 of 482 (43.8 d). The head-vs-tail effect is real but **2.4×,
  not infinite** (Fisher p = 0.0024), and M8's own top-half/bottom-half ratio fell from
  2.8× to 1.9×. Burstiness is confirmed and larger: per-interval PASS hazards ran
  0.73 → 1.84 → 1.00 → 2.33 → 1.31 → **0.00** → 1.67 → **0.00** %/day. The shell tier
  decays at main-tier speed (6/71). Work the M8 rows first, but M9's are perishable too.
  `M11-RESULTS.md` §1.2.
- ~~**Attribution's lookback is bounded at 4 years by measurement, not preference.**~~
  **Closed by M8 (2026-08-17):** the perturbed backend (`attrib/perturbed.py` — Sun +
  eight planets as point masses, vectorised RK4, dense Hermite output; a justified
  integrator validated exactly the way the 4-year bound was measured) brings 15-year
  prediction error from degree scale to ≤ ~94″ worst-case on the calibration set, and
  the sweep runs at |Δt| ≤ 15 y. Beyond 15 years stays closed — unmeasured, not
  impossible. `M8-RESULTS.md` §1–2.
- ~~**The guard's false-rejection rate is measured nowhere.**~~ **Measured 2026-08-07: zero
  of 26.** Against the links the snapshot archive shows somebody else independently made,
  the guard never rejected one on its own — every confirmed link it flagged was already
  failing the acceptance gate. `scripts/guard_vs_confirmed.py`, `SNAPSHOT-VALIDATION.md`
  §3a. Still a floor rather than a rate: *n* = 26, and the sample is biased toward links
  easy enough for someone else to have made. **The acceptance gate is now the open
  question** — it discards 22 of those 28 rows, where the MPC's published rule keeps 14.
  A second, independent sample is now accumulating for free from the ledger refresh:
  across 33 consumed **FAIL** rows the MPC's destination agrees with the ledger 27 times
  (the gate was over-conservative), disagrees 5 times (the gate was **right**) and splits
  once. That puts the strict gate's rejections at roughly **15 % correct refusals** —
  the first sample large enough to be a rate rather than an anecdote.
  `M11-RESULTS.md` §1.1.
- **The 15–25 y shell tier is priced but not promoted.** Its fit stage survives a decoy
  outright (0/300 vs 76/300, p = 5.7 × 10⁻²⁶) and the MPC has consumed six of its PASS
  rows into exactly the objects it named — but 47 of 71 passes are one observatory, 56 of
  71 are 2-observation tracklets, and its multi-tracklet objects pass a combined fit only
  **3 of 10** where the main tier passes 40 of 45. It lives in `m10-shell-ledger.json` +
  `m11-deep-ledger.json` and is deliberately **absent from the review queue**.
  `M11-RESULTS.md` §3.2, §4.
- **The shell's deep end is closed, not unexplored.** 220 fits at 20–25 y under a
  rank-stratified round-robin: **0 fit-grade of 130 beyond 20.74 y** against 33 of 90 at
  20–21 y (p = 2.3 × 10⁻¹⁵). The productive window is 15 y < |Δt| ≲ 20.7 y. Do not spend
  further fo time at 21–25 y, and do not widen past 25 y — that bound is measured and the
  main-belt envelope breaks at 28 y. `M11-RESULTS.md` §5.
- **M14 is a procedural STOP/HOLD, not a resumable queue or a negative result.** Its
  anatomy accounting failed before the exploratory sweep, and the broken usage counter
  changes the recorded 0/100 to a noninferential 0–2/100 diagnostic bound. Repair the complete input contract and
  one-to-one residual provenance before a separately named preregistration; do not resume
  ranks 101–400 or reinterpret M14.

## 5. If you are looking for a discovery

There is not one here, and M4/M5 explain why rather than merely reporting it: the ITF's
unlinked residue is dominated by material the surveys link themselves, and the
cross-observatory pool — the ITF's distinctive value — is small, finite, and now
demonstrably exhausted on both slices.

Better-odds pathways, already researched with URLs verified, are in
[`../DISCOVERY/README.md`](../DISCOVERY/README.md). **Plate archaeology** is the standout:
near-zero competition, no clock, and no automated pipeline reads photographic glass.
