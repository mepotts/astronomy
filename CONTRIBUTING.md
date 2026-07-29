# Contributing

Thanks for looking. This repository is a portfolio of independent astronomy tools and
discovery pipelines; each top-level directory is its own project with its own toolchain,
tests, and documentation.

## Repository layout

| Path | What it is |
|---|---|
| [`adql-copilot/`](adql-copilot/) | Python — schema-aware ADQL linter over Virtual-Observatory TAP endpoints |
| [`pta-explainer/`](pta-explainer/) | TypeScript — interactive pulsar-timing-array / Hellings–Downs explainer |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Python — SN 1987A SETI-ellipsoid alert broker |
| [`itf-linker/`](itf-linker/) | Python — minor-planet linking from the MPC Isolated Tracklet File |
| [`DISCOVERY/`](DISCOVERY/README.md) | Research dossier: verified routes to formally-recognised astronomical discovery |
| [`IDEAS/`](IDEAS/README.md) | Sprint-level plans for candidate builds not yet started |

Each project directory contains `SPEC.md` (the verified research dossier),
`DATA-SOURCES.md` (exact APIs, endpoints, formats, and limits), and `BUILD-PLAN.md`
(stack decisions, architecture, milestones).

## Running the tests

Every project is self-contained. There is no root-level build.

```bash
# Python projects — each ships its own virtualenv
cd adql-copilot          # or seti-ellipsoid-broker, itf-linker
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip.exe
.venv/bin/pytest -q

# TypeScript
cd pta-explainer
npm ci
npm test          # vitest
npm run build     # tsc --noEmit && vite build
```

CI runs the same commands on every push. Tests that require live network access to
external archives are gated behind environment flags and stay skipped by default, so the
suite is hermetic.

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
permanently out of scope. Every submission path is gated behind per-batch human review and
validates against a sandbox endpoint first. See the guardrails section of any
[`DISCOVERY/`](DISCOVERY/README.md) plan.

## Contributions

Issues and pull requests are welcome. If you are proposing a change to a documented
scientific claim, please include the command or query you ran and the date, so the result
can be reproduced.

## Licence

MIT — see [LICENSE](LICENSE). Each project also carries a `CITATION.cff`; if you use one in
published work, please cite the specific project rather than the repository.
