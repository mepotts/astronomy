# M1 — Reading the source, and three corrections to M0

**Two tracks.** Track A: read the actual arXiv PDF and promote every `[SUMM]` config field.
**Done, and it invalidated three things M0 published.** Track B: download an ESO reduced
product and prove `viper` could use it. **Blocked — `archive.eso.org` was unreachable.**

The PDF that M0 could not extract yielded to `pypdf` (27 pages, 55,679 characters) — no
poppler, no WSL, no sudo. That should have been tried first.

---

## 1. Corrections to M0

### 1.1 RETRACTED: "the paper's Hill radius cannot be true"

M0 published, in `M0-RESULTS.md`, `HANDOFF.md`, `README.md` and a pinned test, the claim
that a value of 1.07 au was inconsistent with the system as imaged. **That claim was wrong,
and it was wrong twice over.**

The paper's own words:

> *"our model orbits are fully compatible with the stability limit, which is 1.07 au (both
> satellites have such low eccentricities, they yield the same result)"*

1. **Wrong quantity.** 1.07 au is a *satellite stability limit* — Domingos et al. (2006)
   eq. 5, `a_E ≈ 0.49 R_Hill (1 − 1.0305 e_host − 0.2738 e_sat)` — not a Hill radius. The
   paper computes the Hill radius separately and says it "varies significantly during its
   orbit". The mislabelling came from the AI summary, not from the paper.
2. **Wrong orbit.** M0 computed a Hill radius from the *projected separation* (2.8″ =
   62.6 au) as though the orbit were circular. The paper states the companion has
   **e > 0.9** and a period of **~5000 years**, which puts its semi-major axis at ~222 au.
   The eccentricity term is brutal: at e = 0.9 the Domingos bracket collapses to ~0.07.

Recomputed with the paper's own parameters (0.4 M☉ primary, 37 M_Jup companion, a = 222 au):

| e_host | Stability limit |
|---:|---:|
| 0.90 | 2.34 au |
| 0.92 | 1.65 au |
| **0.94** | **0.96 au** |
| 0.95 | 0.61 au |

**1.07 au falls out at e_host ≈ 0.93–0.94, comfortably inside the published ">0.9".** The
value is correct. `domingos_stability_limit_au` now implements this, and
`test_reproduces_the_published_stability_limit` brackets the published value instead of
asserting against it.

**Root cause:** M0 treated an AI summary of an unread source as a fact firm enough to
publish a disproof of a peer-reviewed paper. The provenance tagging M0 introduced was the
right response to the wrong lesson — tagging a value `[SUMM]` does not make it safe to
*reason* from, and M0 reasoned from one all the way to a public claim.

### 1.2 The `[SUMM]` tier is gone

Every field in `config.py` is now `[v1]` (read from the PDF) or `[TAP]` (archive-confirmed).
Two other `[SUMM]` values were also wrong or imprecise:

| Field | M0 (`[SUMM]`) | M1 (`[v1]`) |
|---|---|---|
| Primary mass | 0.5 M☉ (assumed) | **0.4 M☉** |
| Mean RV error | 30 m/s | **31.44 m/s** (favoured method) |
| Epoch count | 20 | **21 obtained, 20 used** (one cut, continuum S/N ~5) |

Values M0 had right: `bd_mass_mjup` 37, `bd_vsini_kms` 9.58, `bd_max_prot_days` 0.65,
`roche_limit_rbd` 8.4, resolving power 100,000, and the 1469–1780 nm coverage (which M0 had
independently confirmed from ObsCore anyway).

### 1.3 RETRACTED: what Δlog Z = 2.6 measures

M0's `SPEC.md` and `README.md` said the paper's evidence for a *second satellite* was
Δlog Z = 2.6, "positive rather than decisive". **That is not what 2.6 compares.**

- **Δlog Z = 2.6** is the **88-day model versus the 115-day model** — a choice between two
  candidate *periods* for the second signal.
- **Δlog Z = 6.9** is the two-satellite model versus the eccentric one-satellite model —
  the actual evidence that a second satellite exists.

So the second satellite's *existence* is better supported than M0 represented, while its
*period* is considerably less certain than M0 represented.

A genuine inconsistency does exist here, and it is the paper's: Table 1 gives
logZ = −122.654 ± 0.952 and −129.295 ± 0.920, a difference of **6.641**, while the text
quotes **6.9**. Both are recorded in `config.py` and pinned by
`test_table1_logz_difference_does_not_match_the_quoted_delta`. This is a small discrepancy,
noted rather than made much of.

---

## 2. The archived products carry a known precision penalty

From the Methods: the authors ran ESO's `cr2res` pipeline but **deliberately did not use its
combined output**. They kept the individual nodding frames as separate observations:

| Method | Mean RV error |
|---|---:|
| Separate nodding RVs, binned (**paper's choice**) | **31.44 m/s** |
| Spectral combination first (standard pipeline output) | 34.49 m/s |

ESO's archived `calib_level=2` product is almost certainly the combined one. **Working from
it therefore costs ~10% precision by construction.** That is a quantified penalty, not a
blocker — but M3 must not read the resulting offset as a disagreement with the paper. If
the per-nodding route turns out to matter, the raw frames are public for all 20 nights.

---

## 3. The paper already answered M4's question

M0 framed M4 as: *is the 87-day signal the first harmonic of an eccentric 169-day orbit?*
The paper asks exactly this, fits it, and rejects it:

> *"it has been shown that systems hosting bodies on circular orbits in 2:1 MMR are
> mathematically degenerate with a single body on a more eccentric orbit"* … *"a derived
> eccentricity of ≈0.3 is common when fitting 2:1 MMR systems"*

Table 1 carries the eccentric one-satellite fit in full: P = 170.05 d, e = **0.29**,
K = 283.27 m/s, jitter 24.16 m/s versus 16.39 m/s for two satellites. It loses by
Δlog Z = 6.9.

**M4 as originally scoped was redundant, and framing it as a gap the authors missed would
have been false.** It is re-scoped below.

## 4. The real open question is the alias structure

The paper is explicit that the second signal's period is not determined:

> *"There are 4 possible solutions at periods of 14 days, 70 days, 88 days, and 115 days.
> These periods are all aliases of each other with our current sampling, due to the two sets
> of observations being almost exactly a year apart. Observing this target again, avoiding
> this ~1 year mean time difference will help break this degeneracy."*

The residual periodogram shows peaks at ~14, 70, 88 and 115 d, with 88 d "just above the
1% FAP threshold". The 88-day model wins by only Δlog Z = 2.6 over the 115-day one.

This is a **sampling** problem, and it is exactly the kind a reanalysis can attack without
new telescope time:

- Compute the spectral window function of the real cadence and confirm the 14/70/88/115 d
  family is generated by the ~1-year season gap.
- Inject known signals at each candidate period into the real cadence and measure how often
  the injected period is recovered as the favourite. If 115 d injections frequently recover
  as 88 d, the paper's choice is sampling-driven rather than data-driven.
- **The two public J-band epochs from Jan/Feb 2023** (M0 §3) sit ~9 months before the
  paper's first epoch. They cannot be combined with H-band RVs without a cross-setting
  zero-point, but as an *alias-breaking* constraint the cadence leverage may be worth the
  systematic. Untested.

Note the accepted Nature version's disclaimer states that **"which of the presented
satellite models is favored"** changed. It is entirely possible this degeneracy is what
moved. We will not know until those data are public.

---

## 5. Blocked: the product kill-check

`archive.eso.org` became unreachable partway through M1 and stayed down: connect timeout at
21 s, HTTP 000. Not a local problem — `www.eso.org` returned 302 and the NASA Exoplanet
Archive 200 in the same second. It had served M0's queries an hour earlier.

So **the one risk M0 identified is still unretired**: nobody has opened a `calib_level=2`
CRIRES+ product to see whether it is per-order or order-merged. `exosat-rv probe` is written
and wired to answer it in one command; its datalink branch is untested against a live URL.

Section 2 sharpens what the answer means. If the products are order-merged, the ~10%
penalty becomes moot because `viper` cannot use them at all, and the project reverts to
running `cr2res` on public raw frames for all 20 nights.

---

## 6. Status

- `config.py` fully sourced; `[SUMM]` tier eliminated.
- 29 tests (was 23), all passing; ruff clean.
- `exosat-rv probe` written, **unexercised**.
- M4 re-scoped from harmonic leakage to alias structure.
- **Next:** re-run `exosat-rv probe` when ESO returns. Nothing else should be built first.
