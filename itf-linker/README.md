# itf-linker

Mine the Minor Planet Center's **Isolated Tracklet File** — ~9.3 million astrometric
observations that no pipeline ever linked to an orbit — for tracklets that *can* be linked.

The ITF is a 135 MB gzipped text file, free, no registration, no data rights. Everything
this project does runs on a laptop. See [`SPEC.md`](SPEC.md) for the thesis and honest
prior-art assessment, [`DATA-SOURCES.md`](DATA-SOURCES.md) for endpoints and formats, and
[`BUILD-PLAN.md`](BUILD-PLAN.md) for the milestone plan.

**Current state: M1 (orbit fitting) complete.** Findings in
[`M1-RESULTS.md`](M1-RESULTS.md); the M0 kill-check verdict is in
[`M0-RESULTS.md`](M0-RESULTS.md).

M1 built Find_Orb under WSL, verified it against JPL Horizons, and fitted the 979 ITF
designations that already span 3+ nights and survive a trkSub-collision screen. **128 pass
the MPC's published post-fit criteria.**

> ⚠️ Those are **designations with acceptable orbit fits, not discoveries.** A trkSub that
> fits cleanly is usually a known object under a survey's internal tracking name — one of
> the designations submitted here came back identified as comet 73P-C. Establishing that
> anything is unreported requires catalogue cross-matching (MPChecker / SkyBoT / SBIDENT),
> which is **M2 and not done**.

No linking and no submission code exists.

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
```

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
