# Handoff

Start here if you are picking this project up cold. It exists because the expensive
knowledge in this repository is not the code — it is the list of things that were tried,
measured, and found to be wrong. That list is spread across eight documents and would
otherwise have to be rediscovered.

**One-line status:** M0–M5 complete, the MPC's Isolated Tracklet File searched at ~100%
coverage on both slices, **zero discoveries**, 411 tests green. The durable outputs are a
validated linking pipeline, a daily archive that independently confirmed 21 of its own
groupings, and a replicated methodological result drafted for publication.

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
| 9 | `SNAPSHOT-VALIDATION.md` | The one check independent of the whole pipeline |
| 10 | `docs/archive-operations.md` | How the daily archive runs and how it has failed |
| 11 | `docs/rnaas-subset-guard.md` + `rnaas-notes.md` | The publishable finding, and its 14 known weaknesses |

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
| **`(rms or 9e9)`** | An RMS of exactly 0.0 is falsy; one record miscounted. Logged, not fixed | `pipeline.py:190`, `docs/rnaas-notes.md` |
| **Enumerated gitignore** | Listed report filenames one by one, missed M4's differently-named `m4-new.json` (108 MB), push rejected by GitHub | Now pattern `/m[0-9]*.json` |

### Environment and harness traps

- **Find_Orb is 9× slower on `/mnt/c`** than a Linux scratch dir (437 s vs 47 s per 40-link chunk). Outputs verified identical before the change was kept.
- **Four `fo` harness traps** — `$HOME` inside single quotes, a relative `--workdir`, sharing `fo`'s own outputs between concurrent workers, dangling symlinks in incremental config dirs. All failed *silently*. `M1-RESULTS.md` §6.4b.
- **`git reset --hard` on a shared working tree destroyed an agent's uncommitted work.** Use `git branch -f <branch> <target>` to move a ref without touching the tree.
- **The MPC blocks datacenter IP ranges.** Actions runners cannot reach it; a residential connection resolves in 0.03 s. Do **not** route around this. `docs/archive-operations.md` §2.

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
- ~~**The guard's false-rejection rate is measured nowhere.**~~ **Measured 2026-08-07: zero
  of 26.** Against the links the snapshot archive shows somebody else independently made,
  the guard never rejected one on its own — every confirmed link it flagged was already
  failing the acceptance gate. `scripts/guard_vs_confirmed.py`, `SNAPSHOT-VALIDATION.md`
  §3a. Still a floor rather than a rate: *n* = 26, and the sample is biased toward links
  easy enough for someone else to have made. **The acceptance gate is now the open
  question** — it discards 22 of those 28 rows, where the MPC's published rule keeps 14.

## 5. If you are looking for a discovery

There is not one here, and M4/M5 explain why rather than merely reporting it: the ITF's
unlinked residue is dominated by material the surveys link themselves, and the
cross-observatory pool — the ITF's distinctive value — is small, finite, and now
demonstrably exhausted on both slices.

Better-odds pathways, already researched with URLs verified, are in
[`../DISCOVERY/README.md`](../DISCOVERY/README.md). **Plate archaeology** is the standout:
near-zero competition, no clock, and no automated pipeline reads photographic glass.
