# Contributing

Thanks for looking. This repository is a portfolio of independent astronomy tools,
science fronts, and planning dossiers. Top-level directories are separately documented,
but they do not all have a package manifest or test suite.

## Repository layout

| Path | What it is |
|---|---|
| [`adql-copilot/`](adql-copilot/) | Python — schema-aware ADQL linter over Virtual-Observatory TAP endpoints |
| [`pta-explainer/`](pta-explainer/) | TypeScript — interactive pulsar-timing-array / Hellings–Downs explainer |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Python — SN 1987A SETI-ellipsoid alert broker |
| [`itf-linker/`](itf-linker/) | Python — minor-planet linking from the MPC Isolated Tracklet File |
| [`tns-miner/`](tns-miner/) | Python scripts and operating guide — low-latitude transient triage |
| [`chime-frb-periodicity/`](chime-frb-periodicity/) | Catalog 2 activity-period feasibility gate — blocked without a time-resolved window |
| [`dasch-pilot/`](dasch-pilot/) | DASCH DR7 targeted positive/field-control feasibility pilot |
| [`spherex-pilot/`](spherex-pilot/) | Candidate-free SPHEREx warm-tail detectability and privacy gate |
| [`dyson-revet/`](dyson-revet/) | Data-analysis scripts and milestone record — Dyson-candidate re-vetting |
| [`erosita-dr2/`](erosita-dr2/) | Data-analysis scripts and drafts — eROSITA DR2 variability |
| [`gaia-dr4/`](gaia-dr4/) | Release-day rehearsal scripts and preregistration — Gaia DR4 compact companions |
| [`pta-mpta/`](pta-mpta/) | WSL/data-heavy PTA reproduction plus deterministic draft checkers |
| [`DISCOVERY/`](DISCOVERY/README.md) | Research dossier: verified routes to formally-recognised astronomical discovery |
| [`IDEAS/`](IDEAS/README.md) | Dated build plans; some have since moved into project directories |

Layouts are intentionally not uniform. Packaged tools have manifests and ordinary test
suites; science fronts are organised around `README.md`, `STATUS.md`, milestone documents,
committed scripts, and small result artifacts. Read the project documentation before
assuming a dependency manager, environment, or command.

## Running the tests

There is no root-level build. The dependency-free root verifier checks the four portfolio
documents and parses Python scripts in the newer science fronts:

```bash
python scripts/verify_repository.py
```

The packaged projects tested in CI use their own manifests:

```bash
# Packaged Python projects
cd adql-copilot          # or seti-ellipsoid-broker, itf-linker
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip.exe
.venv/bin/pytest -q                    # Windows: .venv\Scripts\pytest.exe -q

# TypeScript
cd pta-explainer
npm ci
npm test          # vitest
npm run build     # tsc --noEmit && vite build
```

The three committed PTA drafts have fast, standard-library consistency checks that do not
run the data-analysis stack:

```bash
cd pta-mpta
python scripts/m5_paper_check.py
python scripts/m4_note_check.py
python scripts/m6_methods_note_check.py
```

CI currently runs the packaged Python suites, the `pta-explainer` test/build, the root
verifier, the offline `tns-miner` cache-contract tests, the three candidate-free discovery-pilot
suites, and those three PTA draft checks.
The root verifier also performs syntax-only parsing of scripts under `dyson-revet`,
`erosita-dr2`, `gaia-dr4`, `pta-mpta`, and `tns-miner`. That is not an end-to-end
reproduction of those data-heavy fronts. Network-backed archive pulls,
bulk-data analyses, WSL campaigns, and registry-facing operations remain outside this CI
and are not implied by a green badge.

## Standards this repository holds itself to

These are not aspirational — they are the rules the existing code was written under, and
the reason several documented numbers carry a measurement date.

**Never fabricate a scientific value.** Every number in documentation must come from code
that was actually run, or from a cited published source. Where a figure was measured
against a live service, the documentation records the date it was measured, because
services change. Placeholder data is written as an empty structure, never as invented
values that look plausible.

**Verify claims against primary sources.** Archive documentation is frequently stale. This
repository has repeatedly found published limits, URLs, and release states to be wrong —
for example, the widely-repeated "Gaia TAP sync caps at 2000 rows" is not a server limit
(a raw sync query returns 50,000+ rows; the service's declared `outputLimit` is 3,000,000).
Where a documented claim and an observed behaviour disagree, both are recorded, along with
which one was tested.

**Say "unverified" rather than guessing.** Research notes here distinguish confirmed facts
from unconfirmed ones explicitly. That distinction is load-bearing, not decorative.

**Nothing irreversible without human review.** Several projects here can submit data to
shared scientific registries — the Minor Planet Center, the Transient Name Server. Bad or
duplicate submissions pollute resources the whole field depends on and damage submitter
reputation such that future reports get disregarded. Automated end-to-end submission is
permanently out of scope. Code may prepare a review artifact, but an accountable human
must inspect the exact payload and perform each outward submission. See the applicable
project's operating guide and the guardrails in [`DISCOVERY/`](DISCOVERY/README.md).

## Contributions

Issues and pull requests are welcome. If you are proposing a change to a documented
scientific claim, please include the command or query you ran and the date, so the result
can be reproduced.

## Licence

MIT — see [LICENSE](LICENSE). Where a project carries `CITATION.cff`, use that
project-specific record. Several science-front directories do not yet have one; do not
infer a DOI or citation record from the root repository.
