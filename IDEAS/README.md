# Astronomy build ideas — "run 2" white space

Sprint-level plans for eight new build candidates, deliberately chosen in the **white space the
original idea-research run (2026-06-14) never swept**: high-energy astrophysics, planetary/meteor
science, satellites/space-situational-awareness, historical archives, and the AI-application
patterns of MCP tooling, agentic reproduction, and accessibility. Shared framing, 2026 data-access
facts, and the plan template are in [`_BRIEF.md`](_BRIEF.md). Each plan did an adversarial
prior-art check and scored itself honestly (U/B/E = underexplored / agent-buildable / excitement,
1–5).

## The eight, ranked by my read of priority

| # | Idea | U/B/E | The wedge in one line | Sharpest prior-art risk |
|---|---|---|---|---|
| 1 | [Gaia DR4 diff auditor](gaia-dr4-diff-auditor.md) | 4/5/5 | Point it at a paper's Gaia target list; it reports what DR4 changed (parallaxes moved beyond quoted error, new RUWE/NSS/variability/exoplanet flags), source_id remapping resolved | `pyia` resolves cross-release IDs, but nobody ships a *paper-level, uncertainty-aware* diff report |
| 2 | [astro-mcp](astro-mcp.md) | 3/5/4 | Astronomy archives as MCP tools for any LLM client, every generated ADQL **validated by adql-copilot's linter** before it runs — reframes the CLI as a distributed engine | `SandyYuan/astro_mcp` exists but undistributed, no validation layer |
| 3 | [Reproduction-audit fleet](reproduction-audit-fleet.md) | 4/4/5 | Ongoing agent-fleet re-derivation of published headline results, collaborate-first, compounding into a citable credibility artifact | PaperBench (frozen ML benchmark), ReScience C (human/slow) — none ongoing + astronomy-specific |
| 4 | [PTA sonification & a11y](pta-sonification.md) | 5/5/4 | First actual *audio* of the nanohertz GW background + Hellings–Downs, folded into pta-explainer as an accessibility pass | Astronify/STRAUSS exist but light-curve/generic; the nHz band is genuinely unsonified |
| 5 | [eROSITA source dossier](erosita-source-classifier.md) | 4/5/4 | Account-free "what is this X-ray source?" plain-language dossier unifying the scattered eRASS1-DE value-added catalogs | Salvato 2025 / HamStar already classify most sources — wedge is unification/translation only |
| 6 | [DASCH time-machine](dasch-time-machine.md) | 5/4/4 | Auto-answers "what did this transient's position do over the last century?" by wiring DASCH's ~1885–1990 light curves to live broker alerts | `daschlab` serves the light curves; the alert-integration/translation layer is new |
| 7 | [Meteorite-fall recovery](meteorite-fall-recovery.md) | 3/4/4 | Turns GMN's public orbit feed into dropper flags + strewn-field alerts + recovery briefings — "where to walk" | DFN/FRIPON/StrewnLAB mature; GMN/Western team may already be productizing this (M0 kill-check) |
| 8 | [Satellite-streak forecaster](satellite-streak-forecaster.md) | 3/5/4 | "Will a satellite cross my field tonight?" with honest TLE uncertainty, plus a citable cross-survey contamination-rate index | IAU CPS SatHub/SatChecker already returns FOV crossings; the rate index is the defensible core |

## How to read the ranking

- **1–2 are the strategic bets.** The **Gaia DR4 diff auditor** has the rare combination of a hard
  dated catalyst (DR4 on 2 Dec 2026), a tool professionals run on *their own* papers, and pure
  account-free TAP buildability. **astro-mcp** is the highest-leverage *reframe*: it turns the
  adql-copilot work into a distribution surface reaching every MCP client, and the linter is the
  guardrail that makes LLM-generated archive queries trustworthy — nobody else pairs the two.
- **3–4 are compounding / cheap wins.** The **reproduction-audit fleet** is the astronomy-shaped
  version of the idea-research machinery itself, and a credibility asset that grows with every run.
  **PTA sonification** is the lightest lift (folds into an existing green project) and opens an
  accessibility angle that had zero presence in run 1.
- **5–8 are domain-expansion plays** into genuinely unswept subfields. Each is real, but each has a
  strong incumbent, so the value is the *translation/productization layer*, and each carries an
  explicit M0 kill-check to run before building.

## Recurring lesson across all eight

In almost every case the raw capability or the underlying science already exists somewhere; the
defensible, agent-buildable value is the **usability/translation/distribution layer** on top of it —
the same thesis the existing portfolio is built on. The honest scores reflect that: nothing here is
virgin green field, and the plans say so. The two worth starting are the two where that layer is both
empty and time-sensitive: the **DR4 diff auditor** (dated catalyst) and **astro-mcp** (distribution
leverage on work you've already done).
