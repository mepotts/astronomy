# tns-miner — faint transients the big pipelines filter out

**What this is.** Avenue **#2** of [`../DISCOVERY/README.md`](../DISCOVERY/README.md) — the one
discovery-shaped route in this portfolio that ends in an **IAU designation with you named as
discoverer**, and the one the 2026-08-14 sweep ranked highly and nobody ever built.

**The rule that makes it possible**, verbatim from TNS: *"the formal 'discoverer' of a transient is
defined to be the reporter/s whose discovery report first turns to public."* If a public survey's
camera recorded it, nobody filed it, and you file it — **you are the discoverer**.

**The proof case.** TNS group 195 (DCAP): two people, no telescope, **~100 TNS discovery reports in
12 months** off the public ZTF alert stream — including **2 of the 6 galactic novae discovered in
all of 2026**. Site: `https://dcap-minruining.github.io/DCAP/`.

**Where the gap is.** *(This paragraph was written from the 2026-08-14 sweep. M1 measured it
against 30,454 real TNS reports on 2026-08-24 and found it half wrong — see
[`M1-02-the-measured-gap.md`](M1-02-the-measured-gap.md). Superseded text kept below for the
record.)*

- ~~"~80% of TNS reports come from five automated pipelines (Pan-STARRS, ZTF, ALeRCE, ATLAS,
  Gaia)"~~ → **MEASURED**: five machines do dominate, but they are **ATLAS, Pan-STARRS, GOTO,
  WFST, ZTF**. **Gaia filed zero reports in the last 12 months.** WFST and GOTO are not in the
  sweep's list at all.
- ~~"The bright end is dead… DCAP lives at mag 19–20.6"~~ → **MEASURED and inverted**: the TNS
  median discovery magnitude is **20.36**, and 45% of all reports already sit in 19.0–20.6.
  DCAP's median is **18.74** — 1.6 mag *brighter* than the population. The bright end is not
  dead; it is where the survey pipelines are absent.
- **The axis that actually separates DCAP from the pipelines is galactic latitude.** 5.8% of all
  TNS reports come from |b| < 15°. For DCAP it is **55%**, for XOSS **68%**, and for every
  automated reporter it is between **0.4% and 8.1%**.

The mechanism the paragraph named is still right: the auto-reporters filter on real-bogus score,
host separation and star/galaxy score because they hunt supernovae, **not** the full 5σ stream —
which structurally discards stellar, in-plane transients at any magnitude.

**The clock: ZTF primary operations end December 2026.** This niche compresses hard and then
migrates to Rubin/LS4 streams.

## Start here

**[`OPERATING-GUIDE.md`](OPERATING-GUIDE.md) is the only file you need to run this
front.** It carries the nightly commands, every pre-registered threshold and the
rule that fixed it, the known failure modes, and the end-to-end submission path
including the three accounts a human has to create. The `M<N>-*.md` documents are
the evidence behind it, not required reading.

**The number that governs how this tool is used** ([`M2-02`](M2-02-precision.md)):
a hand-vetted, pre-registered random sample of the M1 candidate list measured
**precision at 3.5%, 95% CI [1.1%, 15.6%]** — 40% image artifacts, 53% known or
evident variables. The M1 list was declared **not submittable** under a rule fixed
before counting. This is a human-in-the-loop search tool that turns ~100,000
alerts a night into a handful of objects to look at. It is not an automatic
reporter, and it cannot be run unattended.

## Scope

- **Target classes:** galactic novae, M31/M81 novae, CVs and dwarf novae, faint ZTF residue.
- **Avoid:** TDEs, nuclear transients, anything needing a spectrum to be interesting.
- **The hard gate:** classification reports require a spectrum, no exceptions. You can be the
  *discoverer*; you cannot be the *classifier*. ~90% of TNS objects sit unclassified.

## House law (non-negotiable)

**Nothing is ever submitted to TNS by an agent.** Candidates are prepared; Matthew submits.
Any write-path testing happens **only** against the sandbox (`sandbox.wis-tns.org`).

## Conventions

Results docs `M<N>-*.md`, dated, sourced-or-UNSOURCED; `STATUS.md` newest-first; bulk data in
`data/` (gitignored); committed scripts LF; no accounts created by agents.
