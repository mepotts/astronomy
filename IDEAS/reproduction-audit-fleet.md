# Rederive (reproduction-audit fleet)

**One-liner:** A recurring, agent-fleet-driven effort that picks a recent astronomy paper with public data and code, attempts to re-derive its headline figure/result end-to-end, and publishes a transparent, collaborate-first audit (what reproduced, what didn't, with the code) — compounding into a citable credibility artifact: "N attempted, M held, K had discrepancies."

**Scores (U/B/E):** **4 underexplored** (the astronomy public-audit niche is empty; general agent-reproduction is a hot 2025–26 topic, so not virgin space) / **4 agent-buildable** (a curated reproduction *class* is desk-tractable today; general "any paper" reproduction is genuinely hard — scope tightly) / **5 excitement** (a compounding credibility asset, and the astronomy-shaped version of the user's own agentic idea-research machinery).

**Status:** proposed

## The wedge

**What exists already (adversarial prior-art check).** The space is active but no incumbent occupies our exact niche:

- **PaperBench** (OpenAI, ICML 2025; [arXiv:2504.01848](https://arxiv.org/abs/2504.01848)) — agents replicate 20 ICML 2024 papers from scratch against 8,316 graded rubric items. Best agent scored **27%** vs **41%** for human ML PhDs; the top agent was **Claude 3.5 Sonnet** with open scaffolding. It is a *static ML benchmark*, not an ongoing service, not astronomy, and not a public audit that engages authors.
- **ARA — Agentic Reproducibility Assessment** ([arXiv:2605.02651](https://arxiv.org/abs/2605.02651), 2026), **AutoReproduce** ([arXiv:2505.20662](https://arxiv.org/abs/2505.20662)), **reflective paper-to-code** ([arXiv:2508.16671](https://arxiv.org/abs/2508.16671)) — 2025–26 research prototypes for agentic reproduction/peer-review support. General-purpose, CS/ML-leaning, not deployed as a living astronomy audit.
- **ReScience C** ([rescience.github.io](http://rescience.github.io/)) — a platinum-OA, GitHub-native journal of replications; ~213 published since 2015. Human-driven, slow (one careful reimplementation at a time), cross-domain with little astronomy. It is the *journal-of-reproductions* model, not an autonomous ongoing sweep.
- **ReproHack** ([reprohack.org](https://www.reprohack.org/resources)) — episodic human reproducibility hackathons. Great community, not continuous, not automated.
- **showyourwork** (Luger; [github.com/showyourwork](https://github.com/showyourwork/showyourwork)) — Snakemake + GitHub Actions + Zenodo/Overleaf so an *author* can rebuild their own paper "at the click of a button." Author-side prevention, not third-party audit — **complementary**: showyourwork papers are our guaranteed-reproducible warm-up baselines.
- **BITSS Social Science Reproduction Platform (SSRP) + ACRe Guide** ([bitss.org](https://www.bitss.org/introducing-the-social-science-reproduction-platform-a-resource-for-teaching-and-improving-computational-reproducibility/)) — the closest thing to a *process* model: a 5-stage workflow, a **10-point reproducibility scale (not binary pass/fail)**, and template language for constructive author contact. Social science only, human-run. We borrow its scale and its ethics playbook wholesale; astronomy has no equivalent.
- **AAS reproducibility infrastructure** — the [AAS Data Guide](https://journals.aas.org/data-guide/), [software](https://journals.aas.org/policy-statement-on-software/) and [notebook](https://journals.aas.org/policy-statement-on-notebooks/) policies, "Data behind the Figure," and machine-readable tables. AAS *requires* "all data necessary to reproduce the results" and encourages archived, cited code — but **compliance is not independently audited.** That unverified norm is the raw material and the gap.

**Where the defensible gap is.** Nobody runs an *ongoing, autonomous, astronomy-specific, third-party* reproduction audit that (a) targets real recently-published papers on their real public data, (b) engages authors collaborate-first, and (c) accretes a public, citable corpus over time. PaperBench is a frozen ML benchmark; ReScience is human and slow; showyourwork is the author's own build; AAS mandates data but never checks it. An agent fleet fills this cheaply because the desk-tractable reproduction classes (below) are *templated* — one class-specific reproduction agent, run monthly across many papers, does in hours what a human reproducer does in a week, and the whole run is public and re-runnable.

**Why now (2026 catalyst).** Three things converge: (1) 2025–26 agent-reproduction results (PaperBench, ARA) prove agents can do *partial but real* reproduction today — good enough to be useful, weak enough that humility is mandatory; (2) **Gaia DR4 lands 2 Dec 2026** and will trigger a wave of high-profile papers built entirely on public data — perfect, timely fuel for a reproduction fleet positioned in advance; (3) AAS data/software policies plus Rubin/LSST steady-state mean recent astronomy papers increasingly *ship* the data + code that make automated reproduction possible.

## Ethics, tone & the corrections process (the core design constraint)

This is treated as the #1 design problem, not an afterthought. Publishing "did not reproduce" findings can read as a gotcha, can damage an author unfairly, and — critically — **our own reproduction can be the thing that's wrong** (PaperBench's best agent managed 27%: an agent "failure to reproduce" is often the agent's bug, not the paper's). Design rules:

- **Reproducibility, not correctness policing.** We report "we could/could not re-derive X from the public artifacts with effort E, here is exactly what we ran." We never assert a result is *wrong*, never imply misconduct, never use the language of retraction. This is emphatically **not** PubPeer-style anonymous critique or Retraction Watch misconduct framing.
- **Collaborate-first, notify-before-publish.** Every audit that finds a discrepancy goes to the author(s) with a right-of-reply and an embargo/notice window *before* anything is public. Their response (including "here's the missing config") is published alongside — often the audit's most valuable output.
- **Graded, not binary.** Adopt an SSRP-style 10-point reproducibility score (data available → runs → figure matches → number within stated uncertainty → robust to reasonable variations). A paper at "code ran but figure differs" is a *documentation gap*, framed as such, not a failure.
- **"We may be wrong too."** Every discrepancy is dual-checked by a human before publication, the audit ships our full code/env so the author can find *our* mistake, and we log our own corrections publicly. Our false-discrepancy rate is a tracked, published metric.
- **Positive-sum incentive (the carrot).** Opt-in "Reproduced ✓ (graded n/10)" badge authors can embed. Most authors *want* this signal; leading with the badge, not the gotcha, sets the tone.
- **Pre-registered, unbiased selection.** Publish the selection rule up front (e.g., a random draw from eligible open-data papers in a window) so we can't be accused of cherry-picking high-profile targets to dunk on.
- **Respect data rights & licenses.** Only genuinely open data; never bypass embargoes or LSST/collaboration data-rights; honor author code licenses. Authors can opt out of engagement (the audit may still run on public data, but framing stays neutral and the author's silence is never spun as guilt).

## Target user & the "who cites this" test

- **Primary users & the moment they reach for it:** (a) an **author** who wants an independent "reproduced" signal to cite in grant/tenure packets — reached the moment their public-data paper posts; (b) **journal data editors / meta-scientists** who want an audited compliance signal on the "we require reproducible data" policy they can't themselves check; (c) **the reader/referee** deciding whether to trust a headline number, who wants to see it independently re-derived; (d) the **portfolio itself** — the running scoreboard is the credibility artifact.
- **Why it's citable, not just consumable:** each audit is a **1-page RNAAS** (citable, DOI'd) and a **Zenodo-DOI'd reproduction notebook**; the aggregate is a **versioned HuggingFace corpus + leaderboard** ("N attempted / M held / K discrepant") that meta-science and open-science-policy papers cite; the harness/methodology is a **JOSS paper**. Authors cite their badge; editors cite the corpus; we cite the whole thing as evidence the machinery works.

## Data sources & access

All account-free or free-token; all desk-scale compute. The unit of work is *one paper's public artifacts*.

- **Paper + artifact discovery:** arXiv API (open, polite rate limit) and NASA **ADS** API (free token) for recent AAS-journal papers; follow the paper's **Zenodo** deposit (REST API, optional token), **GitHub** repo, and AAS **"Data behind the Figure"** / machine-readable tables ([journals.aas.org/data-guide](https://journals.aas.org/data-guide/)). **showyourwork** repos are a curated guaranteed-reproducible starter set.
- **Underlying open datasets (the account-free re-derivation fuel):**
  - **MAST** (`archive.stsci.edu`, `astroquery.mast`, `lightkurve`) — TESS/Kepler/K2 light curves. Anonymous.
  - **NASA Exoplanet Archive** (`exoplanetarchive.ipac.caltech.edu` TAP) — published planet/transit parameters to compare against. Anonymous.
  - **Gaia TAP** (`gea.esac.esa.int/tap-server`, anonymous `launch_job_async`) — astrometry/photometry; the DR4 firehose from Dec 2026.
  - **DESI DR1** public release ([data.desi.lbl.gov/public/dr1/](https://data.desi.lbl.gov/doc/releases/dr1/)) — BAO cosmology VAC (provided `cobaya` MCMC chains + `iminuit` fits) and LSS catalogs. Public, no auth.
  - Portfolio-adjacent open brokers (Fink/ALeRCE/ANTARES public REST) for alert-derived results.

**Candidate reproduction classes (desk-tractable today):**

| Class | Data / endpoint | Tractability | Example anchor |
|---|---|---|---|
| Exoplanet transit depth/period | MAST + `lightkurve` + `exoplanet`/`juliet`/`batman` | Minutes on a laptop; near-solved path | The `exoplanet` "quick-tess" tutorial reproduces **Pi Mensae c** (Huang et al. 2018) |
| Rotation/variability period catalogs | TESS/Kepler/ZTF + `astropy` Lomb–Scargle | Seconds–minutes per source; sample a subset | TESS All-Sky Rotation Survey, [arXiv:2603.05586](https://arxiv.org/abs/2603.05586) (1.05M stars) |
| BAO / cosmology figure-repro | DESI DR1 BAO VAC (provided chains/fits) | Re-plot & re-fit provided 2pt/chain products; **not** a full re-run of the sampler | DESI DR1 BAO cosmology params |
| Catalog cross-match / selection results | Gaia + partner catalogs via TAP | TAP-side; cheap | Gaia-selected samples |

Note the honesty boundary: we reproduce *headline figures/numbers from provided public products*, not multi-CPU-week pipeline re-runs. Coverage is **curated, not comprehensive** — stated plainly in every publication.

## Architecture sketch

Minimal-runnable-first: a single class agent that reproduces one transit paper end-to-end, wrapped in an audit-report template. The fleet is that agent, parameterized and scheduled.

```
  arXiv/ADS ─┐                         ┌───────────────────────────────┐
  Zenodo    ─┼─► CANDIDATE SELECTOR ─► │  per-paper reproduction job   │
  GitHub    ─┤   (pre-registered      │  ┌────────┐  ┌─────────────┐   │
  AAS DbF   ─┘    eligibility rule)   │  │ INGEST │─►│ CLASS AGENT │   │─► AUDIT bundle
                                       │  │ agent  │  │ (transit /  │   │   • notebook + lockfile
  MAST / Exo Archive / Gaia / DESI ──► │  └────────┘  │  period /   │   │   • Binder link
       (public data)                   │              │  BAO / …)   │   │   • reproducibility score /10
                                       │              └──────┬──────┘   │   • AUDIT.md + PROVENANCE.md
                                       │        ┌────────────▼────────┐ │
                                       │        │ SELF-GRADE + HUMAN  │ │─► author email (right-of-reply)
                                       │        │ dual-check gate     │ │   then publish → corpus + RNAAS
                                       │        └─────────────────────┘ │
                                       └───────────────────────────────┘
```

- **Stack:** Python (astropy/astroquery/lightkurve/exoplanet + the paper's own deps), reproduced inside a pinned env (conda-lock / uv + Binder + a Dockerfile) so *our* environment is itself reproducible. Orchestration via the agent fleet; scheduling via **GitHub Actions cron** (free, public, auditable — same pattern as seti-ellipsoid-broker). Each audit is its own git repo in a public GitHub org, Zenodo-archived.
- **Data flow:** selector picks an eligible paper → ingest agent pulls artifacts + the underlying open data → class agent re-derives the headline figure/number → self-grade produces a draft score + diff against the published value → **human dual-check** → author notified → publish audit + update the running scoreboard.
- **Determinism:** every audit is a one-command / one-click Binder rebuild; the harness re-runs itself in CI so "the audit reproduces" is machine-checked.

## Milestones

- **M0 — Kill checks (cheapest disproofs).**
  - *Prior-art / incumbency:* email ReScience editors, Luger (showyourwork), BITSS/SSRP, and an AAS data editor: "Does an ongoing astronomy reproduction-audit exist? Would you collaborate/endorse?" If a maintained astronomy service already exists → **contribute, don't rebuild.**
  - *Can the easy case be automated?* Have the agent reproduce **Pi Mensae c** (Huang et al. 2018) from MAST via the `exoplanet` quick-tess path, unassisted, and recover transit depth/period within the published uncertainty. If even the curated easy case can't be automated → de-scope to human-in-the-loop *assisted* audits.
  - *Does collaborate-first survive contact?* Draft the corrections/right-of-reply policy; run it past 2–3 authors + one data editor. If the reaction to even a collaborate-first framing is hostile → rethink positioning before building.
  - **Acceptance:** a written go/no-go answering all three: no incumbent, ≥1 real paper's headline auto-reproduced to within its error bar, ≥1 author agrees to be a friendly first public case.
- **M1 — Thin end-to-end slice (one class, one paper, published audit).**
  - One reproduction class (recommend **exoplanet transits on TESS**). Agent fleet re-derives the headline figure + number from public MAST data; produces the full audit bundle (notebook + lockfile + Binder + graded score + `AUDIT.md` + `PROVENANCE.md`); author notified with right-of-reply **before** publish.
  - **Acceptance:** a public audit page for **one** real recent paper — reproduced number within published uncertainty *or* a documented, author-acknowledged discrepancy — fully re-runnable by one command/Binder, with the author on record as contacted.
- **M2 — Cadence + expansion (make it a fleet).**
  - Monthly orchestrator: pre-registered selector → class-routing → self-grade → drafts both the audit and the author email. Add classes: period/rotation catalog, DESI BAO figure-repro, catalog cross-match. Publish an RNAAS per notable audit.
  - **Acceptance:** **≥3 audits/month for 2 consecutive months**, each author-notified and Zenodo-archived, feeding a public "N attempted / M held / K discrepant" scoreboard with the false-discrepancy metric shown.
- **M3 — Distribution + meta-paper.**
  - Public site + GitHub org of reproduction notebooks (each DOI'd); HuggingFace corpus + leaderboard; JOSS methodology paper; opt-in "Reproduced ✓ (n/10)" badge; optional MCP server ("reproduce this arXiv paper").
  - **Acceptance:** JOSS submission of the harness; **≥20 DOI'd audits** in the public corpus; ≥1 author has embedded a badge; an editor/venue references or links an audit.

## First week / first tasks

1. **Warm-up reproduction:** drive an agent to re-derive **Pi Mensae c** from MAST end-to-end (quick-tess/`lightkurve`/`exoplanet`), recovering depth/period within Huang et al. (2018) error bars — proves the easy case is automatable and seeds the audit-bundle template.
2. **Candidate selector v0:** query arXiv/ADS for recent AAS papers shipping code+data (Zenodo/GitHub + AAS "Data behind the Figure"), and pull the **showyourwork** repo list as guaranteed-reproducible baselines; write down the pre-registered eligibility rule.
3. **Ethics/corrections policy draft** (collaborate-first, notify-before-publish, right-of-reply, 10-point graded scale, "we may be wrong," pre-registered selection, opt-out) and circulate to 2–3 authors + one AAS data editor for reaction.
4. **Kill-check emails** to ReScience editors, Luger, BITSS/SSRP, AAS data editor (incumbency + collaboration).
5. **Audit schema + repo template:** define the reproducibility score (adapt SSRP 10-point) and the per-audit repo skeleton (notebook + conda-lock/uv lockfile + Binder + Dockerfile + `PROVENANCE.md` + `AUDIT.md`), with CI that re-runs the audit so it self-verifies.
6. **Pick the M1 target paper:** a recent public-data, tractable transit paper with a contactable, likely-friendly author; secure consent to be the first public case.

## Risks & kill criteria

- **Tone/reputational (the dominant risk).** Audits read as gotcha; a wrong "discrepancy" (agent error) harms an author; community turns hostile. *Mitigation:* the entire ethics section — collaborate-first, dual human-check, right-of-reply, graded language, positive badge. **Kill/pivot:** if a collaborate-first pilot still nets a negative community reaction or harms an author, pivot to **authors-opt-in-only** or assisted mode.
- **Our own error rate.** Agent reproduction is unreliable (PaperBench best 27%); a "failed reproduction" is often *our* bug. *Mitigation:* never claim "irreproducible" — only "we could not reproduce with effort E, here's our code"; publish our false-discrepancy metric; human-gate every discrepancy. **Kill:** if the human gate shows our discrepancy calls are mostly our own bugs, the signal is worthless — stop.
- **Buildability ceiling.** If only a single narrow class ever works, the "fleet" story shrinks to a demo. *Mitigation:* scope to tractable classes, market coverage as curated. **Kill:** can't get past one class after M2 effort.
- **Incumbent appears.** ARA/PaperBench-for-astronomy launches as a live service, or AAS builds it in-house. *Response:* partner/contribute rather than duplicate (design for this from day one).
- **Data-rights / legal.** "Public" data with embargo or collaboration rights (LSST, proprietary pipelines). *Mitigation:* open-data-only allowlist; never bypass embargoes; honor code licenses.
- **Selection-bias optics.** Auditing choices look like targeting. *Mitigation:* pre-registered, transparent, ideally randomized selection.

## Distribution & legitimacy

- **RNAAS** — a citable 1-page note per notable audit (fast, DOI'd).
- **Zenodo** — a DOI per reproduction notebook + a versioned corpus dataset ("N attempted / M held / K discrepant").
- **GitHub org** of public, Binder-runnable, showyourwork-style reproduction repos.
- **HuggingFace dataset + leaderboard** of the corpus (the meta-science citation surface).
- **JOSS** paper for the harness/methodology (software legitimacy).
- **Opt-in "Reproduced ✓ (n/10)" badge** — the positive-sum hook that makes authors want in.
- **Community surfaces:** AAS data editors, Astropy/OpenAstronomy, ReproHack collaboration, `.Astronomy`, possibly an arXiv overlay; an **MCP server** ("reproduce this paper") reaching every LLM-client user (per the 2026 MCP-distribution thesis).

## Rough size

**Effort to M1: ~2–4 focused weeks.** The astrophysics of a well-behaved transit reproduction is a near-solved, tutorial-backed path; the real M1 work is the **audit harness, the graded scoring, the self-reproducing CI, and the author-engagement workflow** — not the fit. **Single biggest uncertainty is not technical:** it is whether collaborate-first framing actually holds in practice — i.e., whether you can publish "did not reproduce" findings on real papers without it becoming a gotcha/liability. Second-order: the agent fleet's own false-discrepancy rate, which sets whether the audits are trustworthy at all.

---

*Key sources (load-bearing): PaperBench [arXiv:2504.01848](https://arxiv.org/abs/2504.01848); ARA [arXiv:2605.02651](https://arxiv.org/abs/2605.02651); ReScience C [rescience.github.io](http://rescience.github.io/); showyourwork [github.com/showyourwork](https://github.com/showyourwork/showyourwork); BITSS SSRP/ACRe [bitss.org](https://www.bitss.org/introducing-the-social-science-reproduction-platform-a-resource-for-teaching-and-improving-computational-reproducibility/); AAS Data Guide/policies [journals.aas.org/data-guide](https://journals.aas.org/data-guide/); DESI DR1 [data.desi.lbl.gov](https://data.desi.lbl.gov/doc/releases/dr1/); TESS rotation survey [arXiv:2603.05586](https://arxiv.org/abs/2603.05586). Gaia DR4 date (2 Dec 2026) per the portfolio brief.*
