# Target interrogation queue (post-M14)

> ## Plan of attack (2026-08-12, post-census — supersedes the tiers below where they conflict)
>
> The coordinate census + header verification (M19, `data/m19-coord-census.json`)
> found campaigns filed under host names. Working order:
>
> | milestone | target | data | actions | state |
> |---|---|---|---|---|
> | **M20** | beta Pic b | 13 K2166 nights / ~810 d (114.27DX + 2023 pilot) | serial fetch+reduce → combined run → blind search + injections | **fetch running** |
> | **M21** | PDS 70 b | ≥5 K2166 product epochs 2022–23 (+9 products to retry, +3 raw 2025 nights, +2 embargoed) | finish product fetch → convert → `m2x_run_target.sh` → verdict | products partly on disk |
> | **M22** | HIP 65426 b | 8 nights: ~4 H-family (H1575) + ~4 K-family | fetch products → per-setting sub-series; H1575 oset by wavelength-overlap map from H_C | queued |
> | **M23** | HD 1160 B | 9 staring H1567 nights / 42 d, DIT 1200 (+1 K pilot night) | staring recipe **now wired in** (classify + reduce_one) → fetch → run | engineering done, unfetched |
> | **M24** | AF Lep b + 51 Eri b | 2 + 1 public staring nights | piggyback on M23's staring path; single-epoch RVs | queued |
> | — | CT Cha B | 3 epochs on disk | injection-based order screen, re-verdict | idle task |
> | — | GSC 08047-00232 B | 2 raw K nights + embargoed product | reduce when convenient; embargo calendar | parked |
>
> Standing machinery: `m2x_run_target.sh` (generic ladder→RV→diag→injection runner),
> `m19_urls_from_raw.py` (raw-first fetch, no PROV chain needed), staring branch in
> `reduce_one.sh`. Order sets: K-band targets run all orders + injection screening
> (M13's order-drop rule); H1575 maps H_C by wavelength overlap — the raw-FTS
> line-count deriver failed validation (`m2x_derive_oset.py` docstring) and the
> fitted-molecule variant is future work. Downloads SERIAL always (parallel lanes
> saturate the portal — measured twice).
>
> Embargo calendar: PDS 70 K nights (2025-08 obs), 51 Eri (2025-09), GSC product,
> eta Tel K epochs, beta Pic b late-2025 K nights, CD-35's decisive epochs
> (**Dec 2026 – May 2027**).

The validated recipe (per-nodding from raw, 2-iteration template with `-kapsig 3`
creation and the injection guard, telluric-selected orders, `-kapsig 3`,
`-oversampling 2`, robust combine, internal 3×-spread epoch screen, blind search that
must survive a BERV covariate) is transferable. This queue orders where to point it.
Sources: M5 (archive holdings, night-level audit), M7 (physics feasibility, 38
companions), M14 (demonstrated 70–90 m/s per epoch on CD-35 2722 B, K = 12.0 — right
at the ~94 m/s anchor M7's thresholds assumed, so the survey numbers stand and are
mildly conservative).

Class note: every target below the brown-dwarf boundary here is a *young, self-luminous
giant* — 10⁴–10⁵× brighter than a field-age Jupiter, which is the only reason
companion-side spectroscopy works at all. The M7 screen says which of them offer
genuinely satellite-mass (sub-Jovian) science vs binary-mass limits.

## Tier 1 — analyzable today (archive orbit-capable)

| target | class | K | nights (public) | baseline | reachable |
|---|---|---:|---:|---:|---|
| **eta Tel B** | ~47 M_Jup BD, β Pic group, 24 Myr | 13.2 | 26 (22) | 815 d | companions ≳3.3 M_Jup — binary-mass limit or detection; first RVs of the object either way |

**This is M15.** Check the epoch sampling's phase–BERV geometry before anything else
(M13 §4b design rule).

## Tier 2 — partial archive: spot-checks now, not orbits

Young planetary-mass / borderline objects with CRIRES+ frames under their own OBJECT
name, but night structures that cannot constrain an orbit (M5 §3):

| target | mass | K | archive reality | what a spot-check yields |
|---|---:|---:|---|---|
| **beta Pic b** | 12.8 M_Jup | 14.9 | 753 frames = **6 nights** / 1034 d | first RV series of the planet; variability limit at ~400 m/s scale; min-sat physics is real (~214 M_Earth) so any variability is interesting |
| AB Pic b | ~14 M_Jup | 15.1 | 64 frames = 4 consecutive nights (3 d) | single-epoch RV + short-term stability; no orbit |
| CT Cha B | M8 companion, accreting | — | 3 nights / 70 d | RV spot-check only |
| GSC 08047-00232 B | M9.5 | 16.4 | 3 nights (2 public) / 4 d | thin; skip unless free |

Note: programme **110.23RW** (the Hoy team's pilot survey) is the origin of the
AB Pic b / beta Pic b / CD-35 frames — assume the discovering team is actively
extending this sample.

## Tier 3 — physics-reachable, no archive: proposal targets

Where the method could reach **genuinely satellite-mass moons** (the exomoon regime),
but no orbit-capable CRIRES+ data exists yet:

| target | mass | age | K | expected per-epoch σ | min. detectable satellite |
|---|---:|---:|---:|---:|---:|
| **beta Pic b** | 12.8 M_Jup | 16 Myr | 14.9 | ~357 m/s | **~214 M_Earth** |
| **PDS 70 b** | 7.9 M_Jup | 5 Myr | 15.2 | ~410 m/s | **~292 M_Earth** (has a known circumplanetary disk) |
| PDS 70 c | 7.8 M_Jup | 5 Myr | 15.2 | ~410 m/s | ~372 M_Earth (verdict: marginal) |

And the limits class — young planetary-mass objects where only 1–10 M_Jup companions
are reachable (still first-ever RV constraints on each): DH Tau B (10.6 M_Jup, ~326
m/s), GSC 6214-210 B (14, ~341), 2M1207 b (5, ~493), 1RXS J1609 b (8, ~897),
HR 8799 d (9.2, ~897), TYC 8047-232-1 B (13.8, ~712), TYC 8998-760-1 b (14, ~1632).

Out of reach at any plausible exposure: HR 8799 b/c/e, 51 Eri b, HD 95086 b,
HIP 65426 b, TYC 8998 c (K ≥ 18 or no measured K-band flux).

## Standing rules for any new target

1. No published-RV truth exists off CD-35 — the injection harness (full-amplitude +
   amplitude-matched, per-frame) carries the entire validation burden. Every internal
   metric in this project's history has lied at least once; do not substitute one for
   the harness.
2. Re-derive the order set from the telluric-density criterion for the target's
   setting; never copy `H_C`.
3. Re-run the template-iteration injection guard per target (M11 proved iteration can
   absorb signal; M14 proved it doesn't always — the guard decides which case you're in).
4. Phase–BERV geometry check before spending compute; a −0.7 entanglement bakes the
   M13 §4b ambiguity in from the start.
