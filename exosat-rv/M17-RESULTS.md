# M17 — The K-band spot-checks: first RVs of three more objects, and beta Pic b says the exomoon regime is reachable

**Question:** what does the validated recipe return on the tier-2 targets — the ones
with some archival data but not enough for an orbit (docs/target-queue.md)?

**Answer:** first multi-epoch RV series of AB Pic b and CT Cha B, and a
demonstration on beta Pic b, each injection-validated in K-band (a new configuration
for this project), with per-epoch precisions that beat the survey forecasts by ~2×
on the well-behaved targets. The headline is beta Pic b: **162 m/s within-night
repeatability on a directly imaged planet at K = 14.9, with 100% ± 0% injection
recovery in every one of 18 orders** — a dedicated campaign at this precision would
probe ~100 M⊕ exomoons.

> **Correction (M20 §5):** this document originally claimed "first-ever RV
> measurements of beta Pic b." That is wrong — a 2024 CRIRES+ study published the
> planet's spin and radial velocity (single-epoch). The defensible statements are
> the *monitoring/precision* forms, hedged "to the best of our knowledge after a
> literature search." AB Pic b / CT Cha B firsts stand under the same hedge.

## 0. What ran

[`m17_inventory.py`](scripts/m17_inventory.py) (per-target archive census +
products), [`m15_convert.py`](scripts/m15_convert.py) (now setting-parameterized),
[`m17_run.sh`](scripts/injection/m17_run.sh) (per-target template ladder → RV run →
injections), [`m17_score.py`](scripts/injection/m17_score.py) (small-n recovery by
per-epoch ratio; phase-90 plans so 2–3-epoch targets still measure transmission).
Everything on archive calib_level=2 products — no raw reduction needed for
spot-checks.

Two traps documented on the way in:

1. **The whole tier is K2166, not H-band** (the pilot programme observed these
   targets in K). `filter_path` lied twice more — five lies total now; the product
   header remains the only truth.
2. **viper's K-band branch is 1-indexed**: its source treats K-band "separately",
   mapping viper order o → DRS order 7−(o−1)//3, so K2166's six orders are
   `oset 1:19`, and an H-band-style `oset 0:…` seeks a nonexistent order 08 and
   crashes template creation.

The known-object hygiene case: beta Pic b's coordinate box contains 14 products of
**the star** (bet Pic itself, a different campaign); only the 8 products tagged
`bet Pic b` (2023-01-03) were staged.

## 1. Results by target

| target | epochs used | per-epoch scatter | injection (K=1530 / K=300) | verdict |
|---|---|---:|---|---|
| **beta Pic b** (planet, K=14.9) | 8 sub-exposures, one night | **162 m/s** (within-night) | **100±0% / 100±0%**, all 18 orders 98–104% | cleanest gates the project has recorded; forecast was 357 m/s |
| **AB Pic b** (~14 M_Jup, K=15.1) | 2 nights, 1 d apart | ~120–190 m/s | 97±3% / 106±8% | first RVs; forecast was 391 m/s |
| **CT Cha B** (accreting M8) | 3 nights / 70 d (1 screened) | ~180–310 m/s | core orders 98–105%; several edge orders catastrophic (−188%…+2400%) | first RVs, usable only with per-order screening — disk emission suspected |
| GSC 08047-00232 B | — | — | — | only product still embargoed (401); 2 raw K nights exist |

Notes. AB Pic b's two epochs bound night-to-night repeatability at roughly the
per-epoch scatter — no anomaly between the nights. CT Cha B's screened epoch is the
same product the raw table mislabels as J-band; its instability pattern (specific
orders, not specific epochs) is what circumstellar emission contaminating part of
the band would produce, and any future use of this target needs an injection-based
order screen first (the M13 rule: dropping orders on injection grounds is
legitimate). beta Pic b's r(RV, BERV)=+1.00 is meaningless with one night of
monotonic BERV; night-to-night systematics — the quantity that actually limited
CD-35 — are unmeasured until more epochs exist.

## 2. What beta Pic b's number means

The survey (M7) forecast 357 m/s per epoch for beta Pic b and a minimum detectable
satellite of ~214 M⊕ for a campaign at that noise. Measured within-night precision
is 162 m/s with transmission proven at both the loud and matched amplitudes; if
night-to-night behaves (unknown — the CD-35 lesson says that is the real fight),
the same campaign math reaches **~100 M⊕, i.e. two-Neptune-mass exomoons of a
directly imaged planet, from the ground**. This is the number a CRIRES+ proposal
would be built on, and it is now measured rather than forecast.

Remaining beta Pic b archive: five more nights (2022–2025) exist raw-only in mixed
settings (≈4 K-family, ≈2 H-family); reducing the K-family nights would give a
4-epoch, ~900-day series — enough for a first night-to-night systematics
measurement on a planet, not yet an orbit. Plumbing note: these nights have no
reduced products, so the fetch needs raw-frame datalink resolution (the existing
`urls_for_night.py` walks an ADP's PROV chain; a raw-first variant is the one new
piece required).

## 3. For the next agent

1. beta Pic b raw K-nights → night-to-night repeatability of a planet RV (the
   number that turns §2 from promise into proposal).
2. CT Cha B: injection-based order screen, then re-assess; possibly a clean
   accretion-RV curiosity.
3. GSC 08047-00232 B: two raw K nights reducible any time; the product unlocks
   on its embargo date.
4. The K2166 order map and the five filter_path lies belong in any eventual
   method paper's appendix (the config-archaeology table already carries the
   H-band half).
