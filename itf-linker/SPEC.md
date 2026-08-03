# ITF Linker — SPEC

> Source of truth for pitch / landscape / scope / kill criteria.
> The thesis and prior-art assessment reproduce [`DISCOVERY/itf-linker.md`](../DISCOVERY/itf-linker.md),
> which remains authoritative. Endpoints and formats live in [`DATA-SOURCES.md`](DATA-SOURCES.md);
> the milestone plan in [`BUILD-PLAN.md`](BUILD-PLAN.md); M0 findings in [`M0-RESULTS.md`](M0-RESULTS.md).

---

## 1. Pitch

Download the MPC's public file of ~9.3 million observations that no pipeline ever linked to
an orbit, link tracklets across nights into gravitationally valid orbits, vet them hard, and
submit the survivors to the MPC's identifications endpoint — which credits successful linkers
**by name** in an MPEC.

**Cost to operate: $0.** One 135 MB download, local compute, free submission endpoint. M0
confirmed this exactly: 6 s to fetch, 9 s to parse, no auth, no data rights, no gated archive.

## 2. Be honest about the wedge

This is **not** white space, and the plan says so explicitly. The algorithms are published and
open source; the data is public; and at least half a dozen individuals work the ITF
successfully right now. In July 2026 alone, three separate identification MPECs credited
private individuals — the three replayed in M0.

The framing is therefore: **an open, uncrowded, formally-credited field where the binding
constraint is sustained engineering effort against millions of rows.** Not a novel method.

What is genuinely defensible:

- **Nobody publishes an ITF triage layer.** The file ships as 80-column text with no orbit
  fits, no quality flags, no per-tracklet linkability score.
- **Cross-archive linking is under-exploited.** F51, W84, G96 and T09 tracklets sit in one
  file and can be linked *to each other*.
- **The DAD overlap** — NOIRLab `dad_dr2` holds 50,163 tracklets never submitted to the MPC.

## 3. Prior art (adversarial)

| Project | What it is | Status |
|---|---|---|
| **HelioLinC** (`lsst-dm/heliolinc2`) | Rubin-lineage linking; propagate to a common epoch, cluster | active, LSST-backed |
| **THOR** (`moeyensj/thor`) | Tracklet-less recovery; 8.5M vCPU-h over NSC DR2, ~27,500 candidates (2024-04-30) | ⚠️ only 104 confirmed MPC designations; fate of the rest **unverified** |
| **FindPOTATOs** (Nugent+ 2025, PSJ 6, 18) | Written for archival data | best starting point for a solo build |
| **find-asteroids** (Stetzler+ 2025) | Shift-and-stack on detection catalogs | 10–10³× speedup |
| **Find_Orb** | Orbit-determination workhorse | what you actually fit with |
| **CANFind** (Fasbender & Nidever 2021) | 527,055 tracklets from NSC DR1, **two authors** | existence proof at individual scale |

**Conclusion: nothing needs inventing.** The build is integration, vetting discipline, and
throughput.

## 4. Scope of this repository

M0 only, as built:

```
ingest/   fetch + provenance; MPC1992 80-col -> typed Parquet
index/    tracklet reconstruction; HEALPix x night partitioning
verify/   replay published MPECs against the snapshot; sensitivity control
```

```
snapshot  ITF snapshot archive: observation keys, delta chain, diffing        (M1)
fit/      Find_Orb wrapper; candidate selection; the MPC's published gates    (M1)
vet/      MPChecker / SkyBoT / SBIDENT / SBDB cross-match and verdict         (M2)
link/     HelioLinC: arrows, hypothesis grid, clustering, gating, ranking     (M3)
```

`report/` (the human-review packet) and `submit/` (ADES emit, sandbox-first) are **not
implemented** and are gated behind the milestones in `BUILD-PLAN.md`.

## 5. Kill criteria

M0's own kill criterion — "if you cannot re-derive a known link, stop" — was **evaluated and
found to be untestable as specified**: all three reference MPECs link previously-designated
objects whose observations were never in the ITF. See `M0-RESULTS.md` §5. The replacement
criterion for M1:

> **Hide the trkSub linkage on the 2,515 ITF designations that already span 3+ nights and
> confirm the linker rediscovers those groupings from positions and epochs alone.**
> If it cannot recover in-file ground truth, stop.

**Met in M3 (2026-08-02).** Of the 1,534 groupings that are collision-screened and reachable
by a 14-day window, **87.4% are re-derived to the exact tracklet**; inside the full
511,274-arrow production population the same measurement gives 75.8%. `itf-linker
link-validate` reproduces it. See `M3-RESULTS.md` §4.

Later kill criteria, unchanged from the plan:

- **M1** — ≥1 candidate surviving every published acceptance gate and every catalogue
  cross-check. Zero survivors after a full partition sweep ⇒ reassess.
- **M3** — a sandbox round-trip that the MPC's test endpoint accepts. Never the live
  endpoint first.

## 6. Guardrails (binding, not aspirational)

This project's failure mode is **polluting a shared scientific resource** and burning
credibility, not wasted effort.

1. **Nothing is submitted without explicit per-batch human review.** Automated end-to-end
   submission is out of scope permanently.
2. **Sandbox first, always** (`submit_psv_test` / `submit_xml_test`).
3. **Contact SARC before any archival submission.**
4. **Duplicate submissions are actively harmful** — cross-check MPChecker, SkyBoT, SBIDENT,
   and DAD's `mpcid`/`mpcsent` before claiming anything is unlinked.
5. **≥2 observations per object per night**, or the *entire batch* is auto-rejected. M0
   measured that 2,580,036 of 2,581,159 single-night designations already satisfy this.
6. **Do not claim cometary activity you have not seen.**

Current codebase compliance: every network call is an HTTP GET against a public MPC URL.
There is no write path to any external service and no credentials are used or stored.

## 7. What success looks like

A **provisional designation** and an MPEC carrying `Id.` and your name — the line that read
`Id. A. Lowe` on 2026-07-20.

Be clear-eyed about the credit distinction: under the post-2010 rule the discoverer is *"the
observer who made the earliest-reported observation at the opposition with the earliest-reported
second-night observation."* For ITF work you are the **identifier**, not the discoverer. You
get the `Id.` credit, **not** naming rights.
