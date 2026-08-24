# The high-latitude extreme mid-IR-excess catalogue, v2

**`dyson-revet_highlat_extreme_IR_excess_v2.csv` — 223 objects, 75 columns.**
Produced 2026-08-24 by [`../scripts/m6_catalog_v2.py`](../scripts/m6_catalog_v2.py)
from v1; every number below is emitted by code, never hand-entered. Machine-readable
provenance lives in [`catalog_stats_v2.json`](catalog_stats_v2.json).

**v1 is not superseded in the sense of being withdrawn.**
[`dyson-revet_highlat_extreme_IR_excess_v1.csv`](.), [`catalog_stats.json`](catalog_stats.json) and
[`README.md`](README.md) are unmodified and still describe exactly what M5
released. Read [`README.md`](README.md) first for what the catalogue *is*, the
footprint, the selection function, the contamination numbers and the column
dictionary; this file records only what v2 changes.

---

## The v1 → v2 difference, enumerated

**Rows added: 0. Rows removed: 0.** The row set is byte-identical in
`source_id` to v1's 223. **Columns added: 13** —
`w3_S`, `w4_S`, `w3_A`, `w4_A`, `w3_G`, `w4_G`, `w3_C`, `w4_C`, `morph_ok`, `n4_score`, `n4_flag`, `nebular_flag_v2`, `catalog_version`.

The nebular stage is a statement about the **field**, not about the object, and
this catalogue's policy since M5 §4 is to **retain and flag**, never to cut. M6's
new morphology component **N4** is carried the same way, so it changes no row's
membership. `nebular_flag_v2` is the union N1 ∨ N2 ∨ N4; `nebular_flag` (v1's,
N1 ∨ N2) is retained unchanged beside it.

## What N4 is

A **training-free structure statistic measured on the AllWISE W3 and W4 Atlas
coadds themselves**, in an annulus 12″ < r < 45″ around each object after 3σ
clipping of neighbouring point sources:

> **S = σ_obs / σ_exp** — the robust dispersion of the PSF-smoothed intensity
> divided by the dispersion the coadd's own uncertainty image predicts under
> the same smoothing.

S is dimensionless and has a parameter-free null: on sky whose only structure is
noise, S → 1. A raised but *flat* background — the thing N2 already measures —
leaves S at 1. The flag threshold reuses M5 PR-2's N2 rule **verbatim**: the
percentile rank of S within |ecliptic latitude| bins of the |b| > 50° parent,
maximum over the two bands, cut at 0.99, with the combined false-positive rate
**measured** on the calibration set at **1.20%**. No new free
parameter is introduced anywhere.

Per-object columns: `w3_S`, `w4_S` (the statistic), `n4_score` (its percentile
rank), `n4_flag` (the cut), `morph_ok` (whether a valid cutout was obtained at
all), and the three **reported-but-not-cut** diagnostics `w3_A`/`w4_A`
(azimuthal asymmetry), `w3_G`/`w4_G` (local gradient) and `w3_C`/`w4_C` (source
concentration against the coadd PSF), all in units of the local noise.

## Completeness — now MEASURED where the injection reaches

M5's README said, under Completeness: *"UNMEASURED: no injection-recovery test
has been run."* **That line is now false, and this is what replaces it.**

**75,600 synthetic star + blackbody SEDs** were built by the
selection code's own forward model, injected onto **real parent hosts** with the
survey's own per-band uncertainties evaluated at the *injected* brightness, and
pushed through the **unmodified** pipeline (M6 §3). Inside the model grid the
pipeline can actually represent — γ ≥ 0.10 and 100 ≤ T_ds ≤ 700 K, n =
36,000:

| | pre-visual recovery |
|---|---|
| all sky | **50.2%** |
| **\|b\| > 30° — this catalogue's footprint** | **45.8%** |
| **\|b\| > 50° — the calibrated core (90 objects)** | **45.8%** |

**Where the rest goes at |b| > 30°**: 20.2%
never detected in W3 or W4 at all; 31.2%
removed by the extra cuts (Gvar, RUWE, `ext_flg`, `classprob` — all properties of
the host star, not of the excess); 3.1%
removed by the S/N ≥ 3.5 gate. The RMSE fit itself passes
90.3% — **it is not the bottleneck.**

**Outside the grid, the catalogue is blind, and now quantitatively so:**

- covering fraction **γ = 0.01 → recovery 0.00%**,
  γ = 0.02 → 0.01%,
  γ = 0.05 → 2.5%. v1's README
  said the catalogue "misses the majority of weaker excesses by construction";
  the measurement is harsher — **below γ ≈ 0.05 it misses essentially all of
  them.**
- **T_ds = 1000 K → recovery 0.17%**, against
  ~31% at every temperature inside the [100, 700] K grid. **The grid's
  temperature range is a second hard boundary**, and it had not been costed
  before.
- A **control**: 8,400 bare photospheres (γ = 0) through
  the same pipeline gave an RMSE-gate false-positive rate of
  **0.00%**.
  Nothing in this catalogue is a photosphere scattered over the line by noise.

**Still UNMEASURED, and marked so**: the injection can only inject what the
forward model can generate — a single blackbody shell on a main-sequence
photosphere. Two-temperature disks, silicate-featured disks and edge-on systems
are **outside the test** and their recovery fraction is **not known**.

## Everything else is unchanged from v1

Footprint, selection function, contamination numbers, the retirement of V5, the
per-row `v5_centroid = "RETIRED"` column, and the statement that
**nothing in this catalogue is a candidate for anything** — all as in
[`README.md`](README.md).

## Reproducing v2

```
# ... v1's chain first (see README.md), then:
python scripts/m6_morph.py coadd --what calib
python scripts/m6_morph.py coadd --what rmse
python scripts/m6_morph.py stats --what calib
python scripts/m6_morph.py stats --what rmse
python scripts/m6_morph.py calibrate
python scripts/m6_morph.py apply --what rmse
python scripts/m6_injection.py run --per-cell 200 --jobs 8
python scripts/m6_injection.py report
python scripts/m6_catalog_v2.py
```

All services are used **anonymously**: no account at ESAC, AIP, IRSA, VizieR,
SVO or MAST was created at any point in this project.

## Version history

- **v2** — 2026-08-24. Same 223 objects. N4 coadd-morphology statistics
  and flag added per row; completeness measured by injection–recovery.
- **v1** — 2026-08-23. First release. 223 objects, |b| > 30°, full-sky screen,
  M5 nebular stage applied as a flag (not a cut) inside the footprint, V5
  retired.
