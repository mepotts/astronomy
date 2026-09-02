# itf-linker

> **Picking this up cold, or handing it to someone who is? Start with
> [`HANDOFF.md`](HANDOFF.md).** It gives the reading order and — more importantly —
> indexes every claim in this repository that was published and later found to be false,
> every approach measured and rejected, and every silent failure that cost real data.
> That index is the expensive part; the code is not.

Mine the Minor Planet Center's **Isolated Tracklet File** — ~9.3 million astrometric
observations that no pipeline ever linked to an orbit — for tracklets that *can* be linked.

The ITF is a 135 MB gzipped text file, free, no registration, no data rights. Everything
this project does runs on a laptop. See [`SPEC.md`](SPEC.md) for the thesis and honest
prior-art assessment, [`DATA-SOURCES.md`](DATA-SOURCES.md) for endpoints and formats, and
[`BUILD-PLAN.md`](BUILD-PLAN.md) for the milestone plan.

**Current state: M0–M5 and M7–M14 have been executed. M13's public automation is
counts/freshness only. M14 authenticated the August 19/24 Rubin aggregates, but its
prospective internal plan's anatomy gate should have stopped on two unclassified rows.
The downstream sweep/fits are exploratory; a residual-attribution bug bounds their
corrected diagnostic at 0–2/100 rather than the recorded 0/100, and the M14 runner is
retired. No M14 candidate queue was opened.**

> **Reviewing candidates? Open
> [`out/review-queue-v2-20260823.csv`](out/review-queue-v2-20260823.csv)** — the current
> version, **669 still-live rows** against a 2026-08-23 18:27 GMT ITF pull, ranked by
> submission value, with an adjudicable column set and a ten-row spot-check sample at
> the top.
> [`out/review-queue.csv`](out/review-queue.csv) is the earlier 08-18 copy and is kept
> **byte-identical** so a half-finished review is not renumbered underneath it;
> [`out/review-queue-v2-20260823-diff.json`](out/review-queue-v2-20260823-diff.json)
> lists exactly what changed (32 rows left, 0 entered, 0 changed tier — every departure
> an MPC consumption that agreed with the ledger). Regenerate with
> `python scripts/m10_review_queue.py --out <new versioned path> --refresh <a fresh
> refresh> --slim <a rebuilt 08-16 table>`, never in place. Nothing in it has been
> submitted anywhere. Milestone findings:
[`M0-RESULTS.md`](M0-RESULTS.md) (kill-check) · [`M1-RESULTS.md`](M1-RESULTS.md)
(orbit fitting) · [`M2-RESULTS.md`](M2-RESULTS.md) (catalogue vetting) ·
[`M3-RESULTS.md`](M3-RESULTS.md) (linking) · [`M4-RESULTS.md`](M4-RESULTS.md) (NEO to TNO
distances, and the pre-2023 slice) · [`M5-RESULTS.md`](M5-RESULTS.md) (that slice fitted
from 1.08% to 100%, and the cross-survey pool exhausted) ·
[`M7-RESULTS.md`](M7-RESULTS.md) (the ITF-to-designated direction: known Rubin orbits
propagated *into* the ITF under a measured two-body window and a decoy control, yielding
one unsubmitted precovery candidate) · [`M8-RESULTS.md`](M8-RESULTS.md) (a perturbed
ephemeris backend measured against Horizons — two-body's degree-scale error at 5–15
years becomes tens of arcseconds — opening the pre-2023 ITF to attribution at full
Feb+April Rubin batch scale, with bulk MPCORB orbits, the decoy control at scale, a
checkpointed fit queue, the SkyBoT check folded into the verdict chain, and a
batch-landing watcher designed but deliberately not scheduled) ·
[`M9-RESULTS.md`](M9-RESULTS.md) (the watcher's flagged partitions consumed on an
exactly-reconstructed snapshot, the fit queue extended under a pre-registered
stopping rule, combined fits promoting 28 of 29 multi-tracklet objects, the 88
lost-object ambiguities adjudicated, a 28-year TNO calibration with three scoping
candidates — and the MPC consuming 30 of M8's fitted candidates within two days,
**every one into the object the ledger had attributed it to**) ·
[`M10-RESULTS.md`](M10-RESULTS.md) (the whole cumulative ledger refreshed against a
pull taken that hour — 733 live PASS rows, 33 consumed, 21/21 PASSes still agreeing
and the strict gate's **first two measured true negatives**; the decay clock
re-measured across three intervals and found to be **entirely concentrated in M8's
queue head**, half-life 32 d there against zero of 272 M9 PASS rows;
`out/review-queue.csv`; M9's 60 ambiguities adjudicated 57-3; the 15-25 y main-belt
shell swept on a gate *derived* from M9's measured envelope; and the pointed-field
screen built, validated 3/3 against M9's failures, and measured against the live
ledger) ·
[`M11-RESULTS.md`](M11-RESULTS.md) (the 15-25 y shell's **fit stage priced against a
decoy for the first time — 0 of 300 decoy fits pass against 76 of 300 real**, with the
re-run control reproducing M10's to the count, and the separation living **entirely in
the "did fo use the tracklet" primary gate** while the strict RMS gate passes *more*
decoys than reals; the MPC independently consuming **6 shell PASS rows and agreeing with
all 6**; the shell's multi-tracklet objects passing their combined fit only 3 of 10
against the main tier's 40 of 45; the deep end closed at **0 fit-grade of 130 fits
beyond 20.74 y**; the cumulative ledger refreshed to 2,203 rows with **68 of 68 consumed
PASSes agreeing** and the strict gate's true-negative count at five; and the archive's
retention found to have **pruned the base snapshot**, which made the first refresh read
18 consumptions instead of 103 with nothing in the output to show it) ·
[`M12-RESULTS.md`](M12-RESULTS.md) (the daily archive read as a series: a 4.4:1 drain,
departures confirmed as whole tracklets being linked, and a transient Pan-STARRS intake
collapse that current-only servers can no longer reconstruct) ·
[`M14-PLAN.md`](M14-PLAN.md) + [`M14-RESULTS.md`](M14-RESULTS.md) (generation-pinned
anatomy of the August 19/24 aggregates; a post-run audit found the mandatory accounting
STOP was missed, the run fingerprint omitted effective inputs, and the later fit
diagnostic is bounded 0–2/100 because M8's station/time selector cannot preserve
observation identity; M14 is retired pending a newly preregistered repair).

M1 built Find_Orb under WSL, verified it against JPL Horizons, and fitted the ITF
designations that already span 3+ nights. M2 built the MPChecker / SkyBoT / SBIDENT /
SBDB vetting gate and ran it. **M3 links tracklets nobody has connected** — HelioLinC over
the MJD > 60000 slice, ranked so that links spanning two or more observatory codes come
first, because individual surveys already link their own data.

**M4 widens the distance grid from M3's 1.4–5.6 AU to 0.55–50 AU** — four bands, each swept
with the window length its own orbital curvature permits — and runs the older 80% of the
file that M3 left untouched.

The linker is validated against the only ground truth the ITF can supply: hide the trkSub
linkage on the designations that already span 3+ nights and see whether it comes back.
M3's grid re-derived **87.4%** to the exact tracklet; the widened grid re-derives **93.0%**,
and cuts the groups it never touches at all from 99 to 28. Independently, against JPL
Horizons astrometry of thirteen real objects, the widened grid recovers **11 of 13** where
M3's recovers 4 — including an Atira at 0.70 AU, two Centaurs and two TNOs — with none
merged into a neighbour. It also recovers comet **73P-C**, which M3-RESULTS stated in print
its grid *could not* find.

⚠️ **The NEO-distance bands produced no near-Earth candidate, and that is the result.** They
fitted **5,547 converged near-Earth orbits** (147 Aten, 3,688 Apollo, 1,712 Amor) and all
but two were rejected by the gates — **84.4% of converged fits by M1's supplementary "one
orbit fits all of it" guard alone**, against 74% in M3 and 6% on survey-made associations.
The two NEO-class survivors are Amors that M3's own 1.4–5.6 AU grid already reached; what
found them is the orbit classifier M4 added, not the distances. A short arc near 1 AU admits
an eccentric NEO solution easily and a good one rarely — that is a filter working, not a
population found.

M4 also ran the older 80% of the file, which M3 skipped because follow-up on a 2015
candidate is impossible — but identification does not need follow-up. It proposes **412,929
gated links to the new slice's 40,623**, and **94% of its survivors span two or more
observatories** against 36% for the post-2023 slice. That is the ITF's whole premise finally
visible in the output: F51 to Subaru, Catalina's old Schmidt to DECam, Steward to Palomar.
M4 could only fit **1.08%** of those 412,929 links.

**M5 fits all of them — 412,929 of 412,929, in 4 h 24 min — and the result is a negative
one.** Fitting 92× more links than M4 produced **not one additional cross-observatory
candidate** beyond the first six batches: the cross-survey pool on the pre-2023 ITF is
**213 survivors**, and M4's 1% sample already held 96 of them. That question is now closed
at this grid and these gates. Of the 3,190 total survivors, **2,977 are one observatory's
own unlinked residue** (2,147 from Palomar's 2005–2006 archive alone), and of **1,850
formally-NEO survivors exactly two are cross-observatory** — from 47,190 converged
near-Earth orbits. No trans-Neptunian survivor has a determined orbit.

Getting there needed a fitting order that works: M4's — argued from value, never checked
against an outcome — put **none** of its own survivors in the first 10% of its queue and
was worse than a random shuffle. A logistic regression fitted to M4's 4,461 outcomes puts
**58%** there. Detail in [`M5-RESULTS.md`](M5-RESULTS.md).

> ⚠️ Everything this repo produces is **candidates that have not been ruled out**, never new
> objects — and M4 measured exactly how much that distinction matters. Of the 30 links sent
> through catalogue vetting, **three came back as already-catalogued objects**: minor planets
> **2026 OB4** and **2026 DK65** at 0.5–0.7″, and **comet 29P/Schwassmann-Wachmann 1** at
> 1.2″ — the latter assembled from four tracklets taken by two telescopes twelve days apart
> in **2002**, never previously associated, its fitted orbit agreeing with JPL's to 1.3σ.
> That is excellent evidence the linker assembles *real objects*, and equally good evidence
> that "no catalogue match" does not mean "new".

**No network submission code exists in this repo.** M13 added an offline payload builder,
`scripts/m13_submit_payload.py`, but it only writes a private local file. The public CI
watcher publishes counts and snapshot health only; it cannot build or upload a payload.

## Safety posture

This project's failure mode is not wasted effort — it is **polluting a shared scientific
resource**. Accordingly:

- Nothing is ever submitted to the MPC without explicit, per-batch human review. Automated
  end-to-end submission is permanently out of scope.
- Science-data network calls are read-only HTTP GETs. There is no MPC write path and no
  MPC credential is used or stored. The counts-only GitHub watcher uses workflow
  summaries/annotations only; it opens no issue or comment and never includes candidate
  identifiers or a submission payload.
- Sandbox-first when submission code eventually lands (M3), never the live endpoint.

## Install

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"    # POSIX: .venv/bin/python
```

## Use

```bash
itf-linker fetch        # download the ITF snapshot (~135 MB) + record provenance
itf-linker parse        # 80-column text -> typed Parquet (~9 s)
itf-linker counts       # observation / observatory / top-code census
itf-linker tracklets    # reconstruct tracklets, report the distribution
itf-linker killcheck    # replay three published identification MPECs against the snapshot
itf-linker partition    # HEALPix x night occupancy and candidate-pair combinatorics
itf-linker m0 --out m0-report.json   # all of the above as one JSON report

itf-linker snapshot                  # archive this pull so future disappearances are measurable
itf-linker snapshots                 # list the archive
itf-linker snapshot-diff first last  # what disappeared / appeared between two pulls

itf-linker fit-selftest              # verify the Find_Orb build against JPL Horizons
itf-linker candidates                # 3+-night designations, gated and collision-screened
itf-linker fit                       # fit them; apply the MPC's published post-fit gate
itf-linker m1 --out m1-report.json   # snapshot + candidates + fits as one JSON report

itf-linker vet-extract               # pull a report's 80-column astrometry out of the ITF
itf-linker vet-control               # positive controls: objects whose answer is known
itf-linker vet                       # MPChecker / SkyBoT / SBIDENT / SBDB cross-match
itf-linker m2 --out m2-report.json   # controls + vetting as one JSON report

itf-linker link                      # HelioLinC: propose links nobody has made
itf-linker link-validate             # hide the trkSub linkage; measure recall + precision
itf-linker link-populations          # re-link real NEOs/Centaurs/TNOs from Horizons astrometry
itf-linker link-fit                  # fit saved links without repeating the search
itf-linker link-fit-all              # fit the WHOLE gated set, survival-ranked, checkpointed
itf-linker link-vet-extract          # reassemble a link report's survivors' astrometry
itf-linker m3 --out m3-report.json   # link + gate + fit + rank as one JSON report
```

`m3`, `link`, `link-validate` and `link-populations` take **`--bands`**: `belt` is M3's
single 1.4–5.6 AU grid, `wide` is M4's four-band 0.55–50 AU set (NEO / main belt /
Centaur–TNO), each band swept with the window its own curvature permits. `--mjd-max 60000`
runs the older 80% of the file.

`m3` is the long one: linking the MJD > 60000 slice is minutes with `--link-workers`, and
fitting the proposals is hours. Two things make that survivable — it saves the gated links
to `data/link-candidates.parquet` *before* fitting starts, and `--fit-resume` (or
`link-fit --resume`) re-reads any `fo` chunk directory a previous run already completed
rather than repeating it.

`link-fit-all` is the long one *squared*: the pre-2023 slice gates 412,929 links. It orders
them cross-observatory first and then by a survival score fitted to M4's own outcomes
(`link/priority.py`), writes a JSON checkpoint per batch as it finishes, and re-reads any
chunk — including another milestone's, via `--seed-workroot` — rather than refitting it. On
Windows it runs `fo` in a Linux-side scratch directory, which is worth ~9× under load
because `/mnt/c` is reached over WSL's 9p bridge; `--no-scratch` restores the earlier
file layout.

**Attribution (M7/M8) runs as scripts rather than CLI subcommands** — the direction is
inverted (known orbit → ITF tracklets) and the run shape is one-shot per batch:

```bash
python scripts/m8_calibration.py        # measure two-body AND perturbed error vs Horizons
python scripts/m8_fetch_bulk.py         # MPCORB extended JSON + batch partitions + verify
python scripts/m8_attribution.py        # the sweep + decoy + ranked, checkpointed fo fits
python scripts/m8_verdicts.py           # verdict chain v2 -> m8-ledger.json (SkyBoT folded in)
python scripts/watch_rubin_batches.py   # has a new Rubin bulk batch landed? (no scheduling)

# Historical M14 invocation (all outputs below ignored data/m14/). The attribution
# driver now refuses every new or resumed run; preserve the artifacts for audit only.
python scripts/m14_prepare.py
python scripts/m14_freeze_itf.py --snapshot-id 20260902T062614Z
python scripts/m14_attribution.py --snapshot-id 20260902T062614Z
python scripts/m14_fit_audit.py --snapshot-id 20260902T062614Z
```

The fitting commands need Find_Orb. It is **not** bundled: build it once with the steps in
[`DATA-SOURCES.md` §4](DATA-SOURCES.md#4-find_orb-build-wsl--verified-2026-07-29), which
takes about two minutes plus a 102 MB ephemeris download. `ITF_LINKER_FO` and
`ITF_LINKER_FO_CONFIG` override the default locations (`$HOME/bin/fo`, `$HOME/.find_orb`).

`data/` is gitignored in full — the ITF snapshot regenerates continuously and is always
re-fetchable, so nothing bulk is ever committed.

## Tests

```bash
.venv/Scripts/python -m pytest          # unit tests: no network, no snapshot needed
.venv/Scripts/python -m pytest -m slow  # additionally requires a fetched ITF snapshot
```

Unit tests run against small in-repo fixtures. The `slow` and `network` markers gate the
tests that need the full 9.3M-row snapshot or live MPC access.

## Licence

MIT — see [`LICENSE`](LICENSE).
