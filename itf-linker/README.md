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

**Current state: M5 (the pre-2023 slice fitted to completion) and M7 (attribution
against the Rubin bulk-batch orbits) complete.** Milestone findings:
[`M0-RESULTS.md`](M0-RESULTS.md) (kill-check) · [`M1-RESULTS.md`](M1-RESULTS.md)
(orbit fitting) · [`M2-RESULTS.md`](M2-RESULTS.md) (catalogue vetting) ·
[`M3-RESULTS.md`](M3-RESULTS.md) (linking) · [`M4-RESULTS.md`](M4-RESULTS.md) (NEO to TNO
distances, and the pre-2023 slice) · [`M5-RESULTS.md`](M5-RESULTS.md) (that slice fitted
from 1.08% to 100%, and the cross-survey pool exhausted) ·
[`M7-RESULTS.md`](M7-RESULTS.md) (the ITF-to-designated direction: known Rubin orbits
propagated *into* the ITF under a measured two-body window and a decoy control, yielding
one unsubmitted precovery candidate).

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

**No submission code exists in this repo**, sandbox or otherwise.

## Safety posture

This project's failure mode is not wasted effort — it is **polluting a shared scientific
resource**. Accordingly:

- Nothing is ever submitted to the MPC without explicit, per-batch human review. Automated
  end-to-end submission is permanently out of scope.
- Every network call in this codebase is an HTTP GET against a public MPC URL. There is no
  write path to any external service, and no credentials are used or stored.
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

The fitting commands need Find_Orb. It is **not** bundled: build it once with the steps in
[`DATA-SOURCES.md` §4](DATA-SOURCES.md#4-find_orb-build-wsl--verified-2026-07-29), which
takes about two minutes plus a 102 MB ephemeris download. `ITF_LINKER_FO` and
`ITF_LINKER_FO_CONFIG` override the default locations (`$HOME/bin/fo`, `$HOME/.find_orb`).

`data/` is gitignored in full — the ITF snapshot regenerates continuously and is always
re-fetchable, so nothing bulk is ever committed.

## Tests

```bash
.venv/Scripts/python -m pytest          # unit tests, no network, no snapshot needed
.venv/Scripts/python -m pytest -m slow  # additionally requires a fetched ITF snapshot
```

Unit tests run against small in-repo fixtures. The `slow` and `network` markers gate the
tests that need the full 9.3M-row snapshot or live MPC access.

## Licence

MIT — see [`LICENSE`](LICENSE).
