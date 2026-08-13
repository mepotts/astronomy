# LESSONS — the consolidated trap catalog (exosat-rv)

**Read this file first.** It exists so no future agent re-learns these the hard way.
Every entry was paid for with a wrong result, a dead run, or a retraction.
Reading order for a new session: this file → `HANDOFF.md` banner →
`docs/target-queue.md` (the roster ledger) → the latest `M*-RESULTS.md`.

Scoring law, stated once: **every change is scored with
`scripts/injection/vs_published.py` against the published RVs, never an internal
metric, and anything adopted must pass injection-recovery first.** Success was
always "rms_pub ≤ threshold AND blind search survives the BERV covariate" — both,
not either.

---

## 1. Method traps (the ones that produce *wrong science quietly*)

| # | Trap | Symptom | Rule |
|---|------|---------|------|
| 1 | viper modeled a gas cell that wasn't there | +283 m/s of structured residual | `-nocell` always for CRIRES+; check instrument config before trusting defaults (M6) |
| 2 | Template built from telluric-contaminated coadd | RV–BERV correlation the authors don't have | Telluric-clean the template; verify r(RV,BERV)≈0 after (M6) |
| 3 | Self-templating absorbs the signal | Known binary's amplitude halved | Any template recipe must pass injection recovery; M12 makes this conditional, not absolute (M11/M12) |
| 4 | Injection by shifting the *observation* | 92% of the injected shift absorbed → fake 100% gates | **Shift the TEMPLATE, never the observation** (M12 §8.1) |
| 5 | Optimizing a metric the signal can game | "Best" change worked by deleting the signal | Controls must be amplitude-matched; prefer signal-invariant metrics (across-order dispersion), and size a fix before ranking it (M9/M10) |
| 6 | Single-night template | 4.7 km/s BERV-locked artifact (r=+0.94) on beta Pic b | **Never build a template from one night** — no BERV lever to separate target lines from telluric residue (M20) |
| 7 | Template ladder upgraded without re-gating | PDS 70 9-night template: −62% injection recovery, a *fake-quiet* series that looks like an improvement | **Gate every template iteration**, not just the first; keep a bit-for-bit restore script (`m21_restore.sh`) (M23) |
| 8 | Phase–BERV degeneracy | CD-35's blind peak entangled with BERV at r=−0.71 | Ten-minute phase–BERV geometry pre-check **before** any campaign compute (M15, permanent) |
| 9 | Claiming "first ever" | "First RVs of beta Pic b" was wrong (A&A 2024 got there) | Literature-search every first; hedge as "to the best of our knowledge"; log corrections in place (M20 §5) |
| 10 | Trusting the mode label | The entire "staring" tier was actually **HiRISE fiber data**; slit-recipe reductions produced km/s artifacts we mistook for sky physics | **Check `INS MODE` + `ORIGFILE` in raw headers before classifying any dataset**; three ledgered verdicts had to be retracted (M27 banner, target-queue) |

## 2. viper quirks (mechanical, cost hours each)

- K-band branch is **1-indexed**: `oset 1:19` for K2166, `1:18` for K2192 (order 02 has no det3). H-band is 0-indexed. Getting it wrong = `KeyError '08_01_ERR'`.
- `-ip` is a dead knob in this configuration — changing it does nothing; don't tune it.
- viper's *printed* rms is not the rms of its RV output column. Score from the column.
- Order mapping assumes the last table column is the reddest (`names[-1]`); staring/HiRISE products can store columns **descending**, which silently inverts the mapping.
- `-wlen` must match the product's actual setting; converter (`m15_convert.py`) validates per-order detector monotonicity (global det-means false-alarm on K2192).

## 3. ESO archive traps (all seven+ documented in `docs/target-queue.md`)

1. **`filter_path` lies** — seven documented cases. Product headers are the only band truth.
2. TAP caps at 20k rows (`MAXREC`) *silently* — window big queries by year (`m25_census2.py`).
3. calSelector returns **zero** calibs for HiRISE/staring frames — fall back to a direct `dbo.raw` CALIB query by night+setting (`m19_urls_from_raw.py`).
4. Old files are `.Z` (LZW) — Python needs `uncompresspy`.
5. Datalink host flakes — go straight to `dataportal.eso.org` URLs.
6. **Serial downloads only.** Parallel lanes lost 37 files mid-batch. Skip-existing must be size-validated (`find -size +1M`); judge a night by files on disk, never by attempt logs.
7. Targets hide under **host-star and programme names** — only a coordinate census with reverse sky-clustering finds them (that's how YSES 1 b's record series and beta Pic b's K campaign were found).
8. The archive's "staring" datasets are **HiRISE** (fiber-fed SPHERE→CRIRES+). See trap 1.10.

## 4. cr2res reduction traps

- Mixed-setting nights crash `obs_nodding` ("Expect only one DROT POSANG") — split SOFs per setting (queued: cd35d1).
- A recipe can "succeed" in 0.656 s and write **empty extractions** (YSES 1 2022) — staging must verify *table contents*, not file existence.
- **`cr2res_obs_nodding` requires an EVEN number of science frames.** That *is* the YSES 1 2022 cause, found M29: an 8-exposure template aborted after 7 (the archive holds 7 too — nothing was lost in download), leaving 3 A and 4 B. The log says `Require an even number of raw frames` / `Invalid Inputs` / `Failed to reduce detector 1,2,3` — and the recipe then writes **all 11 products anyway, empty, and exits 0**. Drop one frame to make the count even. Check `ESO TPL EXPNO` vs `ESO TPL NEXP` at staging: an aborted sequence is common and silent.
- Some frames arrive with UTC/LST stripped — patch placeholder keywords at staging (AF Lep).
- Dark failures are non-fatal (`reduce_one.sh` continues); missing darks ≠ dead night.
- Delete raw after a reduction verifies — raw kept "just in case" filled 1007G to 100% and killed a batch.

## 5. Ops rules (WSL/Windows/harness)

- Long shell chains go in **committed script files** — inline one-liners died silently twice and cost whole runs.
- **Line endings will break every script in this repo.** Git is configured `core.autocrlf=true`, so it rewrites `*.sh` to CRLF on checkout; WSL's bash then fails with `$'': command not found`, a bogus `No such file or directory` on the sourced env file, and a syntax error — while the *task* still reports exit 0. All 39 shell scripts were in this state (found M29, after a "completed" reduction had done nothing). Fixed by `.gitattributes` pinning `*.sh`/`*.py`/`*.sof` to `eol=lf`. Diagnose with `file script.sh` **from inside WSL** — a `grep $''` from git-bash reports LF and will mislead you.
- `git commit -F <file>` always; PowerShell here-strings mangle multi-line messages.
- Read **full** logs on failure — `tail -30` hid the actual retry error once.
- Long WSL jobs run as harness background tasks; recover from TAP outages with a probe-then-rerun loop and a 6 h ceiling.

## 6. Human-gated actions (never automate)

- The author email (`docs/author-query-draft.md`) is **sent by Matthew only**.
- HIP 65426 b's headline uses another team's active-programme data — publication priority is **Matthew's decision** (M20 §5) and gates the paper fold-in of M20–M24.
- Never push/merge to main, never submit anywhere (journals, MPC) without explicit approval.

## 7. Where the conclusions live

| Artifact | What it holds |
|---|---|
| `M13/M14-RESULTS.md` | The reproduction: floor 147→70–90 m/s, blind detection through BERV, dynesty flip (10/10 negative vs paper's +2.62) |
| `M15-RESULTS.md` | eta Tel B: first-ever RV limit, msini ≳ 0.5–1.2 M_Jup (P=20–300 d), both routes |
| `M17-RESULTS.md` | K-band tier: beta Pic b 162 m/s within-night, AB Pic b, CT Cha B (+ the corrected "first" claim) |
| `M20-RESULTS.md` | Census harvest: HIP 65426 b exomoon-regime limit, PDS 70 star, beta Pic b contamination, **the contrast wall**, correction log |
| `M23-RESULTS.md` | Roster closed: 1 confirmation, 1 contradiction, 4 limits, 1 contamination, 4 data-limited (§5); embargo calendar (§6) |
| `docs/target-queue.md` | **The living ledger**: every system's verdict + the HiRISE/M27 banner + archive traps + standing machinery |
| `docs/paper/draft.template.html` | The manuscript (generated, never hand-edited) + Figs 5–12 answering Hoy figure-for-figure |
| `~/.claude/.../memory/` | Cross-session index of all of the above |

**Open front (M27):** proper HiRISE reduction → re-do the fiber tier → beta Pic b's
six public starlight-suppressed nights. Post-M27 frontier: Keck/NIRSPEC (HR 8799
~25 nights, DH Tau ~27; needs a new pipeline). Queued fixes: yses1 2022 SOF ("the
prize": 4-night/290-d exomoon-depth series), cd35d1 split, pds70h mapping.
