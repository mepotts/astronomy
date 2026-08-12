# Target interrogation queue — FINAL STATUS (plan complete, 2026-08-12)

> ## The roster, adjudicated (M14–M24; detail per milestone doc)
>
> Every target with public data has a verdict. All claims injection-gated; all
> "firsts" hedged to a literature search (M20 §5).
>
> | target | data used | setting | **verdict** | doc |
> |---|---|---|---|---|
> | **CD-35 2722 B** | 18 nights / 466 d | H1567 nodding | ✅ **CONFIRMED** — satellite 1 reproduces blind, BERV-robust (ΔBIC +25–28); ❌ satellite 2 **CONTRADICTED** on their own table (10/10 integrals negative) | M14 |
> | **eta Tel B** | 18 nights / 815 d | H1567 nodding | ⛔ **NULL** — msini ≳ 0.5–1.2 M_Jup excluded, P = 20–300 d (90%), both routes | M15 |
> | **HIP 65426 b** | 5 nights / 422 d | K2192 nodding | ⛔ **NULL** — ≳0.4 M_Jup (~115 M⊕) excluded at P ≤ 100 d; *priority caveat: active-programme data* | M20 §4–5 |
> | **PDS 70 (star)** | 6 nights / 426 d | K2166 nodding | ⛔ **NULL** — flat at 130 m/s; ~3 M_Jup stellar-companion limit; planet b unreachable by slit. (9-night rebuild **gate-rejected**, 6-night state reproduced) | M20 §3, M23 §4 |
> | **beta Pic b** | 13 nights / 813 d | K2166 nodding | 🚧 **CONTAMINATION-LIMITED** — km/s BERV-locked starlight (0.55″ / ~5000×); no claim possible; the measured case for fiber-fed suppression | M20 §2 |
> | **HD 1160 B** | 9 nights / 41 d | H1567 staring | 📊 **FIRST SERIES, quality-limited** — 725 m/s, night quality varies 70×; no claim; ±37 m/s best night shows the ceiling | M23 §1 |
> | **CT Cha B** | 3 epochs / 70 d | K2166 nodding | ❓ **VARIABILITY CANDIDATE** — 3.3σ epoch survives the order screen; undecidable at n=3; two more epochs settle it | M17, M23 §3 |
> | **AB Pic b** | 2 epochs / 3 d | K2166 nodding | 📊 clean repeatability datum (~120–190 m/s, gates pass); archive exhausted — **top proposal target** (lighter host than CD-35) | M17 |
> | **AF Lep b** | 2 epochs / 3 d | H1567 staring | 🚧 **DILUTION-LIMITED** — 68% injection transmission at ~30,000× contrast; no measurement | M23 §2 |
> | **51 Eri b** | 1 epoch | H1567 staring | 🚧 **BEYOND SLIT REACH** — 3 of 11 orders respond | M23 §2 |
> | **GSC 08047-00232 B** | — | K | ⏸ **EMBARGOED** — 2 raw K nights bankable on release | — |
>
> **The contrast wall (M20 §6, now measured at four points):** clean ≥ 0.8″/2000×;
> flooded at 0.55″/5000×; gone at ≤ 0.45″/30,000× and at 0.17″. Inside the wall:
> fiber-fed starlight suppression (HiRISE/KPIC) is the instrument requirement.
>
> **Standing machinery** (all committed): `m2x_run_target.sh` (per-target
> ladder→RV→diag→injections; improvement logged: gate every template iteration —
> would have caught the PDS 70 collapse at build time), `m19_urls_from_raw.py`
> (raw-first fetch + direct-CALIB fallback), staring branch in `reduce_one.sh`,
> `ctcha_screen.py` (two-arm order screen). Downloads SERIAL always.
>
> ## Census v2 additions (2026-08-12, header-verified; fetch chain M26 running)
>
> | target | verified data (public) | grade |
> |---|---|---|
> | **YSES 1 b/c** (2-planet system) | 4 K2166 nodding nights / ~290 d | mini-series — best of the new tier |
> | **HIP 81208 B** (~67 M_Jup in a 4-body hierarchy) | 6 H staring + 3 K2166 nodding / ~470 d | two sub-series; eta-Tel-lite |
> | **HD 206893** (BD + inner planet host) | 1 deep K2166 nodding + 2 H staring | spot-check |
> | **HD 19467 B** (benchmark T dwarf) | 2 H staring (+1 embargoed) | spot-check |
> | **PDS 70** (H side) | 3 H1567 staring nights 2025 | adds a second setting to the system |
> | **CD-35 2722 B extras** | 2 deep public H/K nights (Oct 2024, 150 frames each) + pilot K/J; **ten embargoed 116.2AP9 nights Dec 2025–May 2026** (the campaign continues!) | deep pair analyzable now; embargo calendar grows |
> | 2M0103AB b | 1 pilot night public (the "25-night cluster" is mostly J-band monitoring of the host binary); 6-night multi-band deep campaign embargoed to late 2026 | reframed: calendar item |
> | HR 8799 b–e | 2 K2148 nights (new setting) | shelf until worth a new order map |
> | GQ Lup b | Y1029 | out of scope (no Y telluric reference) |
>
> **What reopens the queue (all dated or decisions):**
> - Embargoes: GSC product; PDS 70's 2025 K nights; eta Tel's K epochs; beta Pic b's
>   late-2025 K2166 nights; **CD-35's decisive epochs Dec 2026 – May 2027** (settles
>   the amplitude overshoot and satellite 2 for good).
> - Matthew's decisions: HIP 65426 b priority handling (gates the paper fold-in of
>   M20–M24); sending the author email; proposals (AB Pic b campaign; fiber-fed
>   beta Pic b / PDS 70 b — every sensitivity number measured, not forecast).
> - CT Cha B: any two new epochs decide the variability candidate.

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
