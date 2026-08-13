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
[`exosat-rv/docs/author-query-draft.md`](exosat-rv/docs/author-query-draft.md) is
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

**Zenodo** — not a journal, but the DOI mint: every tagged GitHub release of this
repo archives with a DOI via `.zenodo.json`, which is what a paper's Code
Availability section cites.

## What the field expects a companion repo to look like

The pattern, from working astronomers' repositories (the
[showyourwork](https://github.com/showyourwork/showyourwork) ecosystem and the
repo-per-paper practice common among its users): **one repository or one clearly
bounded directory per paper**, containing the manuscript source, every script
needed to regenerate every figure from raw or archived data, an environment
specification, and a tagged release archived to Zenodo at submission time — so
the README can carry an arXiv badge, a DOI badge, and a one-line "reproduce
figure N with command X."

This repository is already close: the exosat-rv draft is *generated* from a
template with figure exports produced by committed scripts, and each project
carries its environment and tests. The recorded plan (2026-08-13): **at
submission time, exosat-rv splits into its own repository** via
`git filter-repo --subdirectory-filter exosat-rv` — full history preserved —
then tags v1.0 and mints its DOI. Until then it stays here; dual-homing before
submission risks the public copy drifting from the one that made the figures.

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

## The current queue, mapped to venues

| Work | State | Natural venue |
|---|---|---|
| eta Tel B first RV limit | Result complete (`exosat-rv/M15-RESULTS.md`) | RNAAS now; folds into the full paper later |
| CD-35 reproduction + second-satellite contradiction | Draft in `exosat-rv/docs/paper/`; decisive epochs embargoed to Dec 2026–May 2027 | Author correspondence → Nature Matters Arising, or a full OJA/journal paper |
| ITF-linker method + validation | RNAAS draft in `itf-linker/docs/`; blocked on the citable data archive (Zenodo) step | RNAAS |
| seti-ellipsoid-broker tool note | RNAAS draft in `seti-ellipsoid-broker/docs/`, validation passed | RNAAS |
| adql-copilot | JOSS draft in `adql-copilot/paper/` | JOSS |
