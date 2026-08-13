# M8 — Satellites of young close-in giants

**Question:** the Hoy et al. wobble scales as M_host^(−2/3), so a 1 M_Jup planet should be
an even better host than a 37 M_Jup brown dwarf. Can the method be turned on hot Jupiters —
and specifically on *young* ones, where a moon might not yet have been destroyed?

**Answer: the signal is easy, the survival is the whole problem, and "young" is exactly the
right fix — but it must be paired with a different observing technique, and the two
requirements pull against each other as an inverse cube.** Three known planets satisfy both
even under the most pessimistic tidal assumption, and eight under the optimistic one.

Run with `exosat-rv closein`; machine-readable form in [`data/m8-closein.json`](data/m8-closein.json).

---

## 1. The signal is not the problem

A satellite at the edge of the stable zone around a 1 M_Jup planet:

| Satellite mass | K on the planet |
|---|---:|
| Io (0.015 M_⊕) | 1 m/s |
| 1 M_⊕ | **71 m/s** |
| 5 M_⊕ | **354 m/s** |
| 10 M_⊕ | **708 m/s** |

Hoy et al. detected **246 m/s**. So a 3–4 M_⊕ moon of a hot Jupiter produces a *larger*
signal than the first exosatellite ever found. On amplitude alone this is easier, not
harder, and the intuition that drove the question is correct.

There is a second, underrated advantage. A close-in giant's Hill sphere is a few R_Jup
across, so **every allowed satellite period is under ~36 hours**. The entire orbit is
sampled in one or two nights — no seasons, no year-long aliasing, none of the sampling
pathology that M4 spent a milestone quantifying and that leaves the paper's second period
undetermined between 14, 70, 88 and 115 days.

## 2. Survival is the problem, and the planet's spin decides it

Tides move a satellite in a direction set by whether it orbits inside or outside the
planet's **corotation radius**. Outside, the tidal bulge leads and pushes it out (our
Moon). Inside, the bulge trails and drags it in (Phobos).

A close-in giant is despun by its star until it rotates synchronously with its *orbit*.
For a 1 M_Jup planet at 0.05 au on a 3-day orbit that puts corotation at **10.3 R_Jup**,
while the Hill-stability limit is **3.5 R_Jup**:

> **Every dynamically stable satellite is inside corotation, so every one spirals in.**

This is the Barnes & O'Brien (2002) result, and it is why "hot Jupiter moons" is not an
obviously good idea. `moon_inspiral_yr` puts the clock at 10³–10⁶ years — instant.

**The escape is the one the question already contained.** A *young* planet has not been
despun, spins in ~10 hours like every young giant we can measure, and corotation sits at
2.3 R_Jup — **inside** the stability limit. A window opens between corotation and the
stability limit in which satellites migrate *outward* and survive.

So the spin state is derived rather than assumed (`satellites.survival_window`), from:

> τ_spin-down ≈ α M_p R_p² Ω a⁶ Q / (1.5 k₂ G M_*² R_p⁵)

**τ ∝ a⁶ is the entire story.** At 0.05 au a 1 M_Jup planet despins in 0.3 Myr; at 0.1 au,
18 Myr; at 0.2 au, 1.2 Gyr. Every other parameter is uncertain by a factor of a few; `a`
moves the answer by six orders of magnitude. "Young" alone is not enough — 0.05 au
synchronises before any observable age. **Young *and* somewhat further out** is the
prescription.

## 3. The method has to change, and that is where the tension appears

Hot Jupiters cannot be spatially resolved. CD-35 2722 B sits 2.8″ from its star and
CRIRES+'s 0.2″ slit isolates it; a hot Jupiter at 0.05 au and 150 pc subtends **0.3
milliarcseconds**. The slit trick is unavailable, and with it the whole observational basis
of the Hoy method.

The substitute separates planet from star in **velocity** instead of position:
high-resolution cross-correlation spectroscopy. It requires the planet's line-of-sight
velocity to sweep far enough during one observation to walk its lines clear of the static
stellar and telluric lines. Horstman et al. 2025
([arXiv:2505.09781](https://arxiv.org/abs/2505.09781)) put that at **Δv ≈ 30–60 km/s** for
a 6σ Keck/KPIC detection against 9 km/s resolution, and note it scales with resolution.

Δv ≈ G M_* t / a², so cross-correlation wants a **small** orbit. Survival wants a **large**
one. Eliminating `a`:

> **τ_spin-down ∝ M_* t_obs³ / Δv³**

**Every factor 2 gained in observability costs a factor 8 in satellite survival time.** The
trade cannot be escaped by choosing a different host star: Δv ∝ M_* favours massive stars,
τ ∝ 1/M_*² favours light ones, and they oppose in both variables.

## 4. Whether the two overlap comes down to Q, and often they do

At Q_p = 10⁵ a 1 M_Jup planet keeping its spin for 20 Myr must sit at 0.094 au, where
Δv = 19 km/s — **1.6× short** of the threshold. That near-miss is the whole result, because
Q_p is the least-constrained number in planetary science:

| Q_p | a where τ_spin-down = 20 Myr | Δv there | vs. 30 km/s |
|---:|---:|---:|---|
| 10⁵ | 0.094 au | 19 km/s | 1.6× short |
| 10⁶ | 0.064 au | 41 km/s | **clears** |
| 10⁷ | 0.044 au | 88 km/s | **clears** |

**The idea is not ruled out; it is Q-limited.** Against the real catalogue of young
close-in giants (NASA Exoplanet Archive, age < 200 Myr, a < 2 au):

| Q_p | survivable | observable | **both** |
|---:|---:|---:|---:|
| 10⁵ | 18 | 12 | **3** |
| 10⁶ | 26 | 12 | **6** |
| 10⁷ | 28 | 12 | **8** |

### Planet mass is the cheapest lever, and it was under-used

A "hot Jupiter" is not 1 M_Jup. The planetary range runs to the **deuterium-burning limit
at ~13 M_Jup**, and moving up it is the single cheapest fix to the Q-dependence above.

Two effects cancel and a third does not:

- **The geometry is self-similar.** Roche limit, corotation radius and Hill-stability limit
  *all* scale as M_p^(1/3). Window width in dex and the satellite periods inside it are
  therefore **independent of planet mass** — a 13 M_Jup planet has a bigger satellite
  system at the *same* periods, not a proportionally roomier one.
- **Spin-down does not scale that way.** τ ∝ M_p R_p^(−3) a⁶ — the planet's *mean density* —
  and degeneracy pins R_p near 1.2 R_Jup across the whole 1–13 M_Jup range. So **τ ∝ M_p**:
  a 13 M_Jup planet resists despinning **13× longer**. The critical distance moves in as
  a_crit ∝ (age/M_p)^(1/6), and since Δv ∝ 1/a², observability improves as M_p^(1/3).
- **Sensitivity pays.** At the scaled orbit K ∝ m_sat/M_p^(2/3).

At 20 Myr, 1 M_⊙ host, Q = 10⁵ — the pessimistic case throughout:

| M_p | a_crit | Δv / 8 hr | Observable? | P_sat max | min m_sat | K for 10 M_⊕ |
|---:|---:|---:|---|---:|---:|---:|
| 1 M_J | 0.095 au | 18.8 km/s | 1.6× short | 51 hr | 20 M_⊕ | 513 m/s |
| 3 M_J | 0.079 au | 27.1 km/s | 1.1× short | 39 hr | 37 M_⊕ | 270 m/s |
| **5 M_J** | 0.073 au | **32.1 km/s** | **clears** | 34 hr | 50 M_⊕ | 201 m/s |
| **8 M_J** | 0.067 au | **37.5 km/s** | **clears** | 30 hr | 66 M_⊕ | 153 m/s |
| **13 M_J** | 0.062 au | **44.1 km/s** | **clears** | 27 hr | 87 M_⊕ | 115 m/s |

**From ~5 M_Jup upward the observability bar clears at Q = 10⁵**, with no favourable tidal
assumption required. Net over 1 → 13 M_Jup: Δv improves 2.35×, minimum satellite mass
worsens 5.5×. **The first is what matters**, because Δv faces a hard threshold — below
30 km/s there is no detection at all — while satellite mass is a continuous sensitivity
limit. Part of the 5.5× is bought back anyway: a 13 M_Jup young planet is far brighter than
a 1 M_Jup one, and cross-correlation precision is photon-limited.

So §4's Q-dependence is real but **partly an artefact of thinking in 1 M_Jup units**.
Ranking close-in candidates should prefer *massive* young planets, and 13 M_Jup is the
optimum: the most massive object that is still a planet. Just above it, deuterium burning
makes objects brighter again — but those are brown dwarfs, and at wide separation they are
M7's targets, not M8's.

This is visible in the candidate list below, which was built from real catalogue masses
rather than a 1 M_Jup assumption: the three targets that clear the pessimistic cut have
M_p = 1.19, 2.60 and 3.70 M_Jup — the massive end of what is known and young, exactly as
the scaling predicts. **No young close-in planet above ~4.3 M_Jup with a small enough orbit
is currently known**, which makes "young, close-in, and 5–13 M_Jup" a concrete thing to
watch for in new discoveries rather than a parameter to tune.

### The candidates

Surviving even the pessimistic Q = 10⁵ cut:

| Planet | Age | a | M_p | Δv/8 hr | P_sat max | min m_sat | K |
|---|---:|---:|---:|---:|---:|---:|---:|
| **TOI-942 b** | 53 Myr | 0.049 au | 2.60 M_J | 59 km/s | 21 hr | 27 M_⊕ | 9.6 |
| **K2-33 b** | 9 Myr | 0.041 au | 3.70 M_J | 57 km/s | 19 hr | 34 M_⊕ | 10.0 |
| **HIP 94235 b** | 118 Myr | 0.079 au | 1.19 M_J | 30 km/s | 37 hr | 20 M_⊕ | 6.9 |

Adding at Q = 10⁶: **TOI-251 b**, **V830 Tau b** (2 Myr), **HIP 67522 b** (17 Myr).

**K2-33 b at 9 Myr and V830 Tau b at 2 Myr are the literal form of the question** — planets
young enough that a primordial satellite system may not yet have been dismantled.
HIP 94235 b is the brightest host (K = 6.9) at 58 pc, the only one inside 100 pc.

The minimum detectable satellite masses (12–34 M_⊕, at an assumed and generous 1 km/s
cross-correlation velocity precision) land in a suggestive place — see §6.

## 5. The false positive that does not go away

Vanderburg, Rappaport & Mayo 2018 §2.4 give the spurious-RV amplitude from inhomogeneities
rotating across a planet as ΔRV ≈ F_spot × v sin i — a few hundred m/s for a few per cent
of spot coverage on a fast rotator. **That is the same order as the satellite signal**, and
amplitude never separates them. Only timescale does, and they add that the two are hardest
to separate when the periods lie within ~10% of each other or a low harmonic.

For CD-35 2722 B this is a non-issue: P_rot ≤ 0.65 d against 87 and 169 d, a ratio of 260.

Here it is structural. **The inner edge of the survival window *is* the corotation radius,
where the satellite period equals the planet's rotation period exactly, by construction.**
The most secure satellites — those just outside corotation, migrating slowly outward — are
precisely the ones whose period is indistinguishable from the planet's rotation.

It is not fatal. For the candidates above, satellites near the *outer* edge have
`activity_confusion` of 0.9–2.7, comfortably outside the 0.1 danger zone. But it means the
usable part of the window is its outer half, and any search must say so rather than quoting
the full window.

## 6. What this is actually worth, and it is not the moon

Three papers, none previously in this project, converge on something better:

- **Martinez, Stone & Muñoz 2020** ([arXiv:2008.13778](https://arxiv.org/abs/2008.13778)) —
  moons do not survive high-eccentricity (ZLK) migration, and massive moons *prevent* it.
- **arXiv:2509.13263 (2025)** — after *disc* migration, both prograde and retrograde moons
  survive, retrograde 5× more often; under coplanar secular excitation **only massive
  (> 10 M_⊕) retrograde moons** make it.
- **Tokadjian & Piro 2023** ([arXiv:2302.04646](https://arxiv.org/abs/2302.04646)) — a moon
  of ~1% of the planet's mass can synchronise the planet *to itself*, overpowering the
  star and holding corotation inside its own orbit. **Massive moons are therefore more
  likely to survive** — the opposite of what the naive tidal clock in §2 predicts, and a
  correction this milestone would not have found without reading them.

Put together:

> **A satellite around a hot Jupiter is a migration-channel discriminant.** Finding one
> argues the planet arrived by disc migration rather than high-eccentricity migration.
> The surviving population is predicted to be **massive (> 10 M_⊕)** — and RV sensitivity
> goes as satellite mass, so the technique is most sensitive to exactly the satellites the
> theory says are the survivors.

The §4 detection floor of 12–34 M_⊕ sits directly on the > 10 M_⊕ survival threshold. A
clean **upper limit** at 10–30 M_⊕ around a young hot Jupiter is therefore a real result
whether or not anything is found — which is the same honest framing SPEC applies to M5, and
a considerably sharper one, because a null here constrains a named theoretical prediction
rather than an open-ended "are there moons".

## 7. Where the idea is genuinely novel, and where it is not

- **Not novel:** that young hot Jupiters are the preferred exomoon targets. Tokadjian &
  Piro 2023 say so explicitly, and derive the stability niches. Of their sample of hundreds
  of innermost exoplanets, only **26 have any niche at all and 5 a niche wider than 1 R_p**
  — a useful reality check on §4's counts, which are more permissive because they assume a
  10-hour primordial spin rather than solving the coupled spin evolution.
- **Not found in the literature:** proposing **cross-correlation spectroscopy of the
  planet's own spectrum** as the satellite-detection observable. The existing RV exomoon
  literature (Vanderburg+2018, Ruffio+2023, Lazzoni+2022, Hoy+2026) is entirely about
  *spatially resolved* companions; the hot-Jupiter exomoon literature is about transits,
  TTVs and Na/K exospheres (Oza et al. 2019). The two have not been joined.
  **This is a literature-absence claim from targeted searching, not a systematic review —
  it should be checked properly before it is ever asserted in writing.** This project has
  been wrong about white space before (SPEC §prior-art).

## 8. Caveats

- **Q_p is doing more work than any other parameter, and it is unmeasured.** The candidate
  list triples across its plausible range. Nothing here should be quoted without it.
- **The spin evolution is decoupled.** §2 evolves the planet's spin under stellar tides
  alone; Tokadjian & Piro solve the coupled planet–moon–star problem and find the moon can
  win. The two regimes are reported separately rather than resolved
  (`moon_can_synchronise_planet` implements their criterion, P_spin < P_orb/5.05).
- **1 km/s cross-correlation velocity precision is assumed, not sourced.** Horstman et al.
  constrain the *detection* threshold, not the centroid precision. If a target ever clears
  §4, this is the number to measure — the minimum satellite masses scale linearly with it.
- **Most of these planets have masses from mass–radius relations, not measurements**, and
  the survival window depends on M_p and R_p.
- **A satellite period of 10–36 hours against an 8-hour observation** means less than one
  full cycle per night. The signal is a within-night velocity drift partly degenerate with
  the K_p and v_sys that cross-correlation already fits — a modelling problem this milestone
  identifies but does not solve.
