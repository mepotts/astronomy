# Publishing from this repository

*How an independent (unaffiliated) researcher gets work like this into the formal
scientific record, what the field expects a companion repository to look like, and
what this repository deliberately does and does not expose. Venue facts checked
2026-08-13; fees and policies drift, so re-verify before submitting.*

## Where an independent researcher can publish

**[Research Notes of the AAS (RNAAS)](https://journals.aas.org/research-notes/)** —
the first rung, and free. ≤1,500 words, one figure *or* one table, moderated by an
editor but not peer-reviewed, published within ~72 hours, DOI-assigned and indexed
in ADS (citable forever). Independent affiliations are accepted. Right-sized for:
the eta Tel B first-limit, the ITF-linker method note, the seti-ellipsoid tool
note — drafts for the latter two already exist in-repo.

**[The Open Journal of Astrophysics](https://astro.theoj.org/)** — free,
peer-reviewed, arXiv-overlay: the paper lives on arXiv and OJA runs real referee
review on it. The strongest free venue for a full-length paper from an
unaffiliated author. Requires the paper to be on arXiv first (see endorsement,
below).

**Nature Matters Arising** — the formal channel for a substantive challenge to a
published Nature paper, which is exactly what the CD-35 2722 B second-satellite
contradiction is. Free to submit; the original authors are shown the submission
and respond. Etiquette (and the journal) expect prior correspondence with the
authors — the drafted query letter in
[`docs/author-query-draft.md`](https://github.com/mepotts/exosat-rv/blob/main/docs/author-query-draft.md) is
step one of that path, not just politeness.

**Mainstream journals** (AJ/ApJ, A&A, MNRAS, PASP) — all accept "Independent
Researcher, City" as an affiliation; review is on the work. Publication charges
vary widely (A&A currently publishes under subscribe-to-open with no author
charge while that program holds; AAS journals and MNRAS carry article charges
with waiver processes). Check current terms per journal.

**[JOSS](https://joss.theoj.org/)** (Journal of Open Source Software) — free,
peer-reviewed, for the *tools*: adql-copilot's draft in
[`adql-copilot/paper/`](adql-copilot/paper/) is aimed here.

**arXiv** — the field's noticeboard; astro-ph requires a one-time
**endorsement** for new submitters. Practical routes for an independent: an
established author who knows the work (author correspondence, e.g. the Hoy query,
often leads here naturally), or publish first via RNAAS (which needs no arXiv)
and let the record speak. Never pay anyone for endorsement; it is free by design.

**Zenodo** — not a journal, but one possible DOI archive. Several packaged projects
carry `.zenodo.json` metadata, but metadata and a Git tag do not mint a DOI. This
repository has no root-wide automatic archival contract. A DOI exists only after the
owner deliberately creates or connects the archive, verifies its scope and files, and
records the resulting identifier; until then a manuscript must keep its DOI placeholder.

## What the field expects a companion repo to look like

The pattern, from working astronomers' repositories (the
[showyourwork](https://github.com/showyourwork/showyourwork) ecosystem and the
repo-per-paper practice common among its users): **one repository or one clearly
bounded directory per paper**, containing the manuscript source, every script
needed to regenerate every figure from raw or archived data, an environment
specification, and a tagged release archived to Zenodo at submission time — so
the README can carry an arXiv badge, a DOI badge, and a one-line "reproduce
figure N with command X."

The repository is a portfolio, not a single paper package, and its directories do not
share one layout or verification stack. Packaged tools carry manifests and tests;
data-heavy fronts may depend on documented local bulk data, WSL environments, and
milestone-specific checkers. A green root CI run therefore is useful evidence, but not a
claim that every result has been regenerated.

`exosat-rv` has already moved to its own repository and is no longer present in this
working tree: [github.com/mepotts/exosat-rv](https://github.com/mepotts/exosat-rv).
That repository, rather than a stale portfolio copy, is the source for its drafts,
reduction code, release scope, and any eventual archive. Other work should split only
when a real submission package needs an independently versioned record, not because this
root document assumes every project follows the same route.

## What to expose, and what to hold

**Exposed deliberately, as policy.** Dead ends, retractions, correction logs,
`LESSONS.md`, the milestone documents, and the full raw-data-to-figure pipeline.
For an independent researcher the transparent audit trail is the credential —
it is the thing an institutional byline would otherwise vouch for.

**Held, or gated on a human decision:**
- **Unsent correspondence.** A letter should reach its recipient before the
  public; drafts belong out of the tree or sent promptly once public.
- **Headline results derived from another team's active observing programme**,
  until the priority question is decided by a person, not a pipeline (the
  standing example: HIP 65426 b, `exosat-rv/M20-RESULTS.md` §5 — made public
  2026-08-13 by explicit decision).
- **Speculation about other groups' unpublished or embargoed data.** Embargo
  dates are public facts and may be listed; inferences about what rivals will
  find are not for the record.
- **Always:** no credentials or tokens, no third-party personal contact details,
  and no machinery that submits to shared registries (MPC, TNS, journals)
  without per-batch human review — automated submission is permanently out of
  scope.

## AI authorship, disclosure, and submission

Most of the work in this repository was carried out by AI agents (Claude, via
Claude Code) operating under the owner's direction. The rules, per the 2026
publishing consensus (ICMJE, COPE, Springer Nature, Elsevier, Science, AAS
ethical standards):

**AI is never an author.** Every major publisher and ethics body rejects AI
authorship on the same ground: authorship means accountability, and only a
human can be accountable to a journal, a referee, or the record. The human
owner is the sole author and answers for every claim.

**Substantive AI use must be disclosed — and here it is methodology, not a
footnote.** The 2026 norm is a dedicated AI-use statement at submission plus
description in the manuscript where the use occurred. Grammar-level assistance
is exempt everywhere; analysis-level involvement is not. Since in this work the
agent drove the analysis, the honest form is a Methods paragraph describing the
agentic workflow itself — model and version, what the agent did, and the
verification discipline that gated its output (positive controls,
injection-recovery gates, scoring only against published values, the
correction log). This repository's audit trail is the evidence that the
discipline existed. Template statement:

The disclosure is split into two artifacts so the manuscript stays lean: a
condensed **"AI contribution and responsibility statement"** in the paper itself
([`docs/paper/draft.template.html`](https://github.com/mepotts/exosat-rv/blob/main/docs/paper/draft.template.html)),
and the full stage-by-stage **[AI-CHECKLIST.md](AI-CHECKLIST.md)** it links to —
involvement levels 0–4 per research stage with evidence pointers into the
repository, modeled on the Agents4Science 2025 mandatory checklists. No
mainstream venue requires the checklist (2026) — statements suffice — but
providing it voluntarily makes the disclosure checkable rather than asserted.
Future papers copy and re-grade the checklist table per paper. The honest
adaptation: where the WASP-4b paper's human co-author was a domain expert
auditing the AI's analysis, here verification is primarily *mechanical*
(injection gates, amplitude-matched positive controls, published-values-only
scoring) plus the public audit trail, and the human role is direction,
adversarial challenge, external-consequence decisions, and sole accountability.
The statement says so explicitly rather than borrowing the expert-audit framing.

Mapped to the CRediT taxonomy journals ask for (AI listed as a disclosed tool,
never an author):

| CRediT role | Matthew Potts (author) | Claude agents (disclosed tool) |
|---|---|---|
| Conceptualization | direction, research questions | approach within those questions |
| Methodology, Software, Data curation | — | ✓ |
| Formal analysis, Investigation, Visualization | — | ✓ |
| Validation | adversarial review of claims | machine-enforced gates |
| Writing — original draft | — | ✓ |
| Writing — review & editing | ✓ | revisions under review |
| Supervision, Project administration | ✓ | — |
| Accountability for the published record | ✓ (sole) | none — cannot hold it |

**Check the target venue's current AI policy at submission time** — policies
are converging but not identical (Science required a policy change to allow
disclosed AI text at all; some funders now reject substantially-AI-developed
proposals). Venues that experiment with AI-as-author (Sakana's AI Scientist at
an ICLR 2025 workshop; Stanford's Agents4Science 2025, where AI agents are
primary authors and reviewers by design) are sandboxed meta-science
experiments, not channels for astronomy results.

**Worked examples of AI-driven papers (found 2026-08-13):**
- *Transit Timing Variations of Exoplanet WASP-4b: Evidence of Orbital Decay* —
  [Agents4Science 2025](https://openreview.net/forum?id=Yja2KMahOL), AI primary
  author with a working exoplanet astronomer (A. Shporer, MIT) as human
  co-author. Archival public-data orbit reanalysis — the same shape as the
  exosat-rv work. Its mandatory AI-involvement checklist (disclosure by research
  stage: planning, execution, writing) is the closest thing to a standard
  "methods section for AI-driven work" that exists; readable in a browser
  (OpenReview blocks automated fetchers).
- *QITT-Enhanced … Cosmological Parameter Estimation* — same venue; the AI
  framework is literally the named first author ("Denario Astropilotai"), with
  professional cosmologists as co-authors ([Denario project,
  arXiv:2510.26887](https://arxiv.org/abs/2510.26887)).
- *Kosmos* ([arXiv:2511.02824](https://arxiv.org/abs/2511.02824)) — autonomous
  discovery system; its report style is the model for quantified transparency:
  independent scientists audited its statements (79.4% accurate) and the papers
  disclose the AI/human split explicitly.
- Sakana's AI Scientist-v2 passed an ICLR 2025 *workshop* review fully
  AI-generated — then was withdrawn by design; the enduring peer-reviewed
  artifact is the human-authored Nature paper about the system. The lesson:
  AI-as-author remains a sandboxed experiment; AI-driven work with a human
  accountable author is the publishable path in mainstream venues.

**AI never submits.** Three independent reasons, any one sufficient: (1)
submission portals require legal representations — originality, licensing,
accountability — that only a human can truthfully make; (2) peer review is a
months-long correspondence with an accountable person; (3) this repository's
standing safety policy gates every outward send behind per-item human review.
Agents prepare submission packages down to the last byte; the owner presses
submit.

The same boundary applies to repository operations: merging code, tagging a commit, or
passing CI is not publication and is not scientific submission. Each DOI mint, journal
upload, registry payload, email, or public announcement remains a separate human-reviewed
outward action.

## The current queue, mapped to venues

| Work | State | Natural venue |
|---|---|---|
| eta Tel B first RV limit | Result and draft live in the separate [`exosat-rv`](https://github.com/mepotts/exosat-rv) repository; not submitted | RNAAS, or fold into the full paper |
| CD-35 reproduction + second-satellite contradiction | Draft lives in [`exosat-rv`](https://github.com/mepotts/exosat-rv); author correspondence and submission remain human gates | Nature Matters Arising, or a full OJA/journal paper |
| ITF-linker method + validation | RNAAS draft in `itf-linker/docs/`; M13 prepares a local review payload and publicly reports counts/freshness only; M14 stopped procedurally and supplies no discovery result or queue; the archive DOI plus every MPC/journal action remain human gates | RNAAS |
| TNS low-latitude triage | M2 historical front closed; the 37-object review list was never a submission queue. The newest proved run sealed its TNS input but produced no pool/candidate count after a required Fink class timed out; nothing sent | No venue selected |
| eROSITA DR2 fader census | Draft complete and not submitted; archive scope, bibliographic check, and author metadata remain open | RNAAS |
| MPTA reproduction and audits | Full paper plus two RNAAS notes are drafts with deterministic text-to-artifact checks; no DOI and nothing submitted | Full journal paper and/or RNAAS |
| Dyson candidate-D negative | M7 analysis closed; no draft, pending a human go/no-go on whether the negative result warrants one | Undecided |
| Gaia DR4 compact-companion front | M9 rehearsal closed; this is release readiness, not a paper or discovery claim | Decide only after the planned DR4 release and gated analysis |
| CHIME/FRB Catalog 2 periodicity | M0 blocked before any unknown-source scan because the released exposure map has no time-resolved observing window | No venue; obtain the missing citable window or close the lane |
| DASCH targeted plate pilot | Narrow public-API light-curve gate reproduced the published T CrB control with one nearby field control; the original Mira/faint/crowded and plate-cutout M0 gates remain open, and no unknown-source search ran | No venue yet; complete M0, multi-control validation, and an independently vetted result would come first |
| SPHEREx warm-tail pilot | Broad catalog scan killed on detectability; narrow paired test remains behind an exact private-coordinate query gate | No venue; feasibility/privacy gate only |
| seti-ellipsoid-broker tool note | RNAAS draft in `seti-ellipsoid-broker/docs/`, validation passed | RNAAS |
| adql-copilot | JOSS draft in `adql-copilot/paper/` | JOSS |
