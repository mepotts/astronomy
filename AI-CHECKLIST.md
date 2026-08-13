# AI involvement checklist

*Stage-by-stage disclosure of AI involvement in the research published from this
repository, with evidence pointers. Modeled on the stage-tracking idea of the
Agents4Science 2025 mandatory checklists, adapted for a mainstream-venue paper by
a sole human author using AI agents. Papers link here; the manuscript carries a
condensed statement. No venue this repository targets requires this checklist
(2026); it is provided voluntarily because the claim "AI did the work, a human
answers for it" should be checkable, not asserted.*

## Involvement levels

| Level | Meaning |
|---|---|
| 0 | No AI involvement — human only |
| 1 | Human-led; AI assisted (suggestions, refinements) |
| 2 | Collaborative; neither party's contribution dominates |
| 3 | AI-led with human review or challenge before adoption |
| 4 | AI-autonomous within standing verification gates; human sees results, not steps |

Model versions per stage are recorded in the repository commit trail
(`Co-Authored-By` lines) and the session-level milestone documents.

## Paper 1: CD-35 2722 B reproduction + eta Tel B limits (`exosat-rv/docs/paper/`)

| Research stage | Level | Notes and evidence |
|---|:---:|---|
| Research questions and scope | 1 | Human set the goal (reproduce Hoy et al., then survey) and re-scoped at each milestone; agent proposed refinements. Evidence: milestone briefs quoted in `exosat-rv/M13`–`M15-RESULTS.md` |
| Literature search and prior art | 3 | Agent-led sweep (found the method's lineage and two unnoticed prior nulls, `M7`); a human challenge ("you read every scientific paper?") forced the correction of an overclaimed "first" — `exosat-rv/M20-RESULTS.md` §5 |
| Data discovery and acquisition | 4 | Coordinate census, archive queries, downloads, integrity checks: `exosat-rv/scripts/m25_census2.py`, `scripts/cr2res/` |
| Reduction and pipeline engineering | 4 | cr2res cascade, ADP→cr2res converter, viper configuration: `exosat-rv/docs/viper-runbook.md`, `scripts/` |
| Method and validation design | 3 | Injection harness (shift-the-template rule), amplitude-matched controls, scoring law designed by agent, adopted as a standing human-approved contract: `exosat-rv/M12-RESULTS.md` §8 |
| Experiment execution | 4 | All runs, including failed ones; run scripts committed: `exosat-rv/scripts/injection/`, `scripts/cr2res/` |
| Statistical analysis | 3 | Nested sampling, blind search with BERV covariate: `exosat-rv/scripts/nested_orbits.py`, `scripts/injection/blind_search.py`; verdicts gated before adoption |
| Interpretation and claims | 3 | Agent drafts every verdict; adoption requires the mechanical gates plus survival of human challenge. Retractions and corrections stay in the record: `exosat-rv/LESSONS.md`, `HANDOFF.md` |
| Figure generation | 4 | `exosat-rv/scripts/m16_figures.py`, `m18_figures.py`; manuscript assembled by `m16_build_paper.py`, never hand-edited |
| Manuscript first draft | 4 | Generated from `docs/paper/draft.template.html` |
| Review and editing | 2 | Human directs framing, tone, and what is claimed; agent implements |
| Decisions with external consequences | 0 | Publication priority on other teams' programme data, making the repository public, all correspondence: human only (`PUBLISHING.md`) |
| Submission and outward communication | 0 | Human only, permanently — no automated submission machinery exists in this repository |

## Reuse

Future papers copy the Paper-1 table, re-grade each stage honestly, and link the
new section here. The grade that cannot change without a policy change is the
last two rows.
