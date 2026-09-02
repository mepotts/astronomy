# The high-latitude extreme mid-IR-excess catalogue, v1

**`dyson-revet_highlat_extreme_IR_excess_v1.csv` — 223 objects, 62 columns, 153 KB.**
Produced 2026-08-23 by [`../scripts/m5_catalog.py`](../scripts/m5_catalog.py);
every number in it is emitted by code, never hand-entered. Machine-readable
provenance and the completeness/contamination numbers quoted below live in
[`catalog_stats.json`](catalog_stats.json).


> **Dated annotation, 2026-08-24 (M6).** A **v2** of this catalogue exists:
> [`dyson-revet_highlat_extreme_IR_excess_v2.csv`](dyson-revet_highlat_extreme_IR_excess_v2.csv)
> and [`README_v2.md`](README_v2.md) — the same 223 rows with 13 added columns
> (the M6 N4 coadd-morphology statistics) and **completeness measured by
> injection-recovery** in place of the UNMEASURED line below. **Nothing in this
> file or in v1 has been changed**; this annotation is append-only, per repo
> practice, so that a reader arriving here is not left on the older version.

---

## What this is

A catalogue of **223 stars within 300 pc whose 12 and 22 μm fluxes exceed a
stellar photosphere by more than any dust-free model allows**, selected from a
**100 %-of-sky** Gaia DR3 × AllWISE × 2MASS screen and restricted to
**|b| > 30°**, where that screen is calibrated.

It is the positive by-product of a re-vetting of Project Hephaistos II's
Dyson-sphere search ([Suazo et al. 2024, MNRAS 531,
695](https://academic.oup.com/mnras/article/531/1/695/7665761)). **It is not a
candidate list for anything.** Not one object here is claimed to be a
technosignature, and nothing in it has been reported anywhere. Roughly two
thirds of it is convicted of contamination by this project's own gates, and
those objects are **kept in the table with their evidence** rather than
silently dropped, because a catalogue that hides its own rejects cannot be
checked.

## Why |b| > 30°, and why the |b| > 50° core is different

The parent screen overproduces relative to the published one by 4.2× all-sky,
and that overproduction is **entirely a Galactic-latitude effect** — 20.9× at
|b| < 5°, falling to **1.05× [0.94–1.17] at |b| > 50°**
([M4 §4.3](../M4-sky-parent-gvar-jwst.md)). At high latitude the screen
reproduces the published yield; in the plane it does not, because the published
pipeline's nebular classifier is unpublished and cannot be reproduced.

So the footprint is a statement about where the selection is trustworthy:

| `b_band` | definition | n | area | measured yield vs the published rate |
|---|---|---|---|---|
| `core_b50` | \|b\| > 50° | **90** | 9,651 deg² | **1.05× [0.94–1.17]** — calibrated |
| `outer_b30_50` | 30° < \|b\| < 50° | **133** | 10,975 deg² | 1.32× after the M5 nebular stage |

**Use `core_b50` when the selection function has to be defensible.** The outer
band is included because it is useful, and flagged because it is not equally
calibrated.

## Selection function

Applied in this order; each stage is code, and each is documented in
[M1](../M1-reproduce-and-vet.md)–[M5](../M5-nebular-stage-highlat-catalog.md).

1. **Parent** — Gaia DR3 × `allwise_best_neighbour` × 2MASS; Bailer-Jones EDR3
   `r_med_geo < 300 pc` (exact, never proxied); **W3 *and* W4 profile-fit
   detections**; AllWISE `cc_flags` clean; full 10-band G/BP/RP/J/H/Ks/W1–W4
   photometry; inside the template M_G window [0.5, 14.0]. **328,937 stars,
   1.03× the published parent.**
2. **Model** — star + blackbody "Dyson sphere" grid fitted over 10 bands,
   **RMSE ≤ 0.2 mag**, covering fraction **γ ≥ 0.10** (the paper's own stated
   grid floor). 9,486 survivors.
3. **Nebular stage** — M5's replacement for the unpublished CNN: rejected if
   inside the published extent of a catalogued nebula (N1) **or** if the
   AllWISE coadd background at the position is in the top 1 % of clean
   high-latitude sky at the same ecliptic latitude (N2).
4. **Extra cuts** — Gvar < 2, RUWE < 1.4, `ext_flg` = 0, `classprob` > 0.9.
5. **S/N** — W3 **and** W4 signal-to-noise ≥ 3.5.

## Completeness — what is missing, and why

**This is a selection-function-defined catalogue, not a complete one.** Every
line below is a known way it is incomplete, measured or cited, never estimated.

- **The γ floor dominates.** Objects with covering fraction below 0.10 are not
  selected at all. M3 measured that dropping the floor to γ ≥ 0.01 multiplies
  RMSE survivors by 5.83× and pre-visual survivors by 2.93×. **The catalogue
  misses the majority of weaker excesses by construction.**
- **The S/N ≥ 3.5 cut removes 92.8 %** of the 3,095 objects that reach it in
  this footprint. It is a bright-end selection, not a completeness-preserving
  one.
- **Full 10-band photometry is required**; 326,540 of 328,937 parent rows
  (99.27 %) have it.
- **Nothing beyond 300 pc is in the parent.**
- **Sky coverage is complete** — 100.00 % of the sky is screened — so there is
  no coverage incompleteness. The N1 catalogue veto masks **0.97 %** of the
  |b| > 30° sky and **0.03 %** of the |b| > 50° core, i.e. essentially none of
  it.
- **UNMEASURED**: no injection-recovery test has been run. The fraction of real
  extreme-excess objects that the 10-band RMSE fit recovers is **not known** by
  this project.

## Contamination — what is in here that should not be

The honest summary is that **most of this catalogue is probably contaminated,
and the table says which objects and on what evidence.**

| verdict | n | % |
|---|---|---|
| `CONTAMINATION-CONSISTENT` | 85 | 38.1 % |
| `SUB-THRESHOLD` | 63 | 28.3 % |
| `INDETERMINATE` | 75 | 33.6 % |
| `STILL-CLEAN` | **0** | — |

**`STILL-CLEAN` is zero by construction, not by measurement.** It requires a
valid centroid measurement, and the centroid axis (V5) is **retired**:
on candidate D — the one object where JWST supplies the truth — the archival
centroid is wrong in direction (PA 82.9° against the real 33°, pointing where
MIRI shows nothing) as well as magnitude (W4 2.55 ± 0.50″ against a hard
geometric ceiling of 1.23″). See [M5 §6](../M5-nebular-stage-highlat-catalog.md)
and [M4 §5.3](../M4-sky-parent-gvar-jwst.md).

Consequences you must carry when using this table:

- **`INDETERMINATE` does not mean clean.** It means *no detectable
  contamination evidence, from a method with a known blind spot.*
- **The blind spot has a number**: `sep_thr(ρ) = F · (1 + 1/ρ)`, so at a 1″
  floor **≈10 %**, and at a 2″ floor **≈40 %**, of chance-aligned contaminants
  inside Suazo et al.'s own 3.25″ aperture are **invisible at any brightness**.
- **Chance alignment with the *catalogued* faint-red-galaxy population is not
  the explanation.** With Suazo et al.'s own 15,000 sr⁻¹ the expected number of
  such alignments is **3.8 over the entire 328,937-star parent** and **0.003
  inside this footprint** — so V4 is a weak axis at this sample size. What the
  gates actually convict on is photometric: single-exposure non-detections,
  release-dependent photometry, and sub-5σ bands. The ~10× fainter red-galaxy
  population identified in [M1](../M1-reproduce-and-vet.md) as the real
  contaminant class **has no published density and is not quantified here**.
- **The empirical base rate is high.** Of the ten labelled Hephaistos objects,
  five have an identified contaminant (B, C, D, E, G), two of them confirmed by
  JWST.

## What it is scientifically useful for, beyond technosignatures

The framing that does *not* depend on the technosignature question, and the one
this project recommends:

1. **Extreme debris disks.** Main-sequence stars within 300 pc with 12 and
   22 μm excesses far above the photosphere. The fitted blackbody temperature
   (`t_ds`, median **141 K**, range 100–283 K) and covering fraction (`gamma`,
   median 0.10) are in the table. Objects at the low-temperature end are
   candidate cold-debris systems; the warm end overlaps the extreme/transient
   debris-disk population.
2. **Extreme M-dwarf mid-IR excesses.** The sample is dominated by
   **M_G 10–12 dwarfs** (full range 7.5–13.6, median 10.9) at a median distance
   of 224 pc — a regime where WISE-excess samples are sparse, and where an
   excess is hard to produce by any conventional mechanism.
3. **Dust pollution around low-mass and evolved stars.** The M_G window is the
   only prior on host type; nothing about the selection assumes a disk.
4. **A measured false-positive set for WISE-excess searches.** The objects the
   gates convict are a catalogued, position-resolved sample of the ways AllWISE
   manufactures a 22 μm excess: `w3nm`/`w4nm` = 0 (never seen in a single
   exposure), `w?flg` = 32 (aperture photometry is a 95 % upper limit),
   release-dependent `ph_qual`, and sub-5σ bands. Anyone building a WISE-excess
   pipeline can test it against these.
5. **A test set for the archival contamination floor.** Paired with the JWST
   measurement of candidate D ([M4 §5](../M4-sky-parent-gvar-jwst.md)), these
   are the objects on which `sep_thr(ρ) = F(1 + 1/ρ)` can be checked if imaging
   becomes available.

## Column dictionary

62 columns in five blocks. Units are as stated; magnitudes are Vega for
2MASS/WISE and Gaia's own system for G/BP/RP.

**Identity and position** — `source_id` (Gaia DR3), `designation_aw` (AllWISE),
`tmass_designation`, `ra`/`dec` (ICRS deg, Gaia epoch J2016.0), `glon`/`glat`,
`ecl_lat`, `b_band`.

**Astrometry** — `parallax`, `parallax_error` (mas), `pmra`, `pmdec` (mas/yr),
`r_med_geo` (Bailer-Jones EDR3 geometric distance, pc — exact, not proxied),
`ruwe`.

**Photometry** — `phot_g_mean_mag`, `phot_bp_mean_mag`, `phot_rp_mean_mag`,
`M_G`; `j_m`, `h_m`, `ks_m`; `w1mpro`…`w4mpro` with `_error`; `snr3`, `snr4`
(from the screen's own uncertainties) and `w3snr_aw`, `w4snr_aw` (the AllWISE
catalogue's).

**The excess model** — `rmse` (10-band fit residual, mag), `t_ds` (fitted
blackbody temperature, K), `gamma` (covering fraction), `gvar`.

**Vetting** — `verdict`, `verdict_reason`; `flag_v1_w3nm0`, `flag_v1_w4nm0`,
`flag_v1_w3flg32`, `flag_v1_w4flg32`; `ph_qual_aw`, `ph_qual_as`,
`flag_v2_release_inconsistent`; `flag_v3_subthreshold`; `p_chance_1as`;
`v5_centroid` (constant string: RETIRED).

**Nebular stage** — `n1_flag`, `n1_cat`, `n1_name`, `n1_sep_as`, `n1_r_as`;
`n2_score`, `n2_flag`; `nebular_flag`; `w3sky`, `w4sky` (AllWISE median
background in the profile-fit annulus, DN), `w3conf`, `w4conf`.

*Four of the 223 carry a nebular flag; they are retained and flagged, not cut,
because at |b| > 30° the flag is at the stage's own ~1 % false-positive rate
and is not by itself evidence about the object.*

## Reproducing it

```
python scripts/m4_aip_screen.py select --source aip --jobs 14   # the screen
python scripts/m3_vet_survivors.py --tag m4_g0.1 --skip-centroid --backend gator
python scripts/m5_nebular.py fetch
python scripts/m5_nebular.py sky --what calib
python scripts/m5_nebular.py sky --what previsual
python scripts/m5_nebular.py calibrate
python scripts/m5_nebular.py apply --what previsual
python scripts/m5_catalog.py
```

All services are used **anonymously**: no account at ESAC, AIP, IRSA, VizieR or
MAST was created at any point in this project.

## Citing the inputs

Gaia DR3 (Gaia Collaboration 2023); AllWISE (Cutri et al. 2013; Wright et al.
2010); 2MASS (Skrutskie et al. 2006); Bailer-Jones et al. 2021 (EDR3
distances); Suazo et al. 2024 (the selection this reproduces); Pecaut &
Mamajek 2013 (the photospheric locus). The nebular catalogues used by N1 are
listed with their references in
[`../out/m5_nebular_catalog_report.json`](../out/m5_nebular_catalog_report.json).

## Version history

- **v1** — 2026-08-23. First release. 223 objects, |b| > 30°, full-sky screen,
  M5 nebular stage applied as a flag (not a cut) inside the footprint, V5
  retired.
