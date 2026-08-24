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

**Where the gap is.** ~80% of TNS reports come from five automated pipelines (Pan-STARRS, ZTF,
ALeRCE, ATLAS, Gaia). The bright end is dead — ZTF's Bright Transient Survey sweeps everything
brighter than ~18.5. But the auto-reporters filter on real-bogus score, host separation and
detection multiplicity, **not** the full 5σ stream. DCAP lives at mag 19–20.6.

**The clock: ZTF primary operations end December 2026.** This niche compresses hard and then
migrates to Rubin/LS4 streams.

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
