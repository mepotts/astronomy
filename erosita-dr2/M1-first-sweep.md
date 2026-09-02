# M1 — first sweep: DR2 inventory, DR1→DR2 variability slice, top-candidate cross-match

*2026-08-14. Scripts: [`scripts/download_catalogs.py`](scripts/download_catalogs.py),
[`scripts/w2_variability_slice.py`](scripts/w2_variability_slice.py),
[`scripts/w3_crossmatch.py`](scripts/w3_crossmatch.py). Outputs in [`out/`](out/); bulk data in
`data/` (gitignored). Numbers computed by these scripts from the two downloaded catalog files are
marked **[computed]**; everything else carries its source URL. Negative results are results.*

---

## 1. What eROSITA-DE DR2 actually is (W1, verified)

**Release.** 2026-07-31, confirmed on the portal news feed
([erosita.mpe.mpg.de/dr2/news_dr2](https://erosita.mpe.mpg.de/dr2/news_dr2/)); press release
[MPG 2026-07-29](https://www.mpg.de/26891434/20260729-erosita-dr2-nearly-doubles-known-x-ray-sources-to-two-million).
Survey paper: Ramos-Ceja et al., "The SRG/eROSITA All-Sky Survey DR2"
([arXiv:2607.27772](https://arxiv.org/abs/2607.27772)). **Catalogue-only release** — unlike DR1 it
ships *no* event lists, images, exposure/sensitivity maps, spectra, or light curves
([FAQ](https://erosita.mpe.mpg.de/dr2/FAQ_dr2/)). Footprint: Western Galactic hemisphere,
359.94423568° > l > 179.94423568° ([FAQ](https://erosita.mpe.mpg.de/dr2/FAQ_dr2/)). Data are
eRASS:3 = cumulative eRASS1+2+3, 2019-12-12 → 2021-06-16, 556 days
([portal](https://erosita.mpe.mpg.de/dr2/)), processed with pipeline **version 030** vs DR1's 010
— refinements to energy calibration, astrometry (time-dependent boresight), flare filtering, event
reconstruction; "changes relative to DR1 are generally small"
([arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §3).

**Catalog products** (file listing read from
[Catalogues_dr2](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/), sizes from
HTTP Content-Length headers, 2026-08-14):

| Product | File | Size | Contents |
|---|---|---|---|
| Main (1B, 0.2–2.3 keV) | `RamosM_DR2/eRASS3_Main_v1.3.fits` | 2,139,595,200 B | 1,911,744 point (EXT_LIKE=0) + 63,796 extended, DET_LIKE_0 ≥ 6 ([paper](https://arxiv.org/abs/2607.27772) Table 15); file has 1,975,540 rows **[computed]** — consistent |
| Hard (3B-selected, 2.3–5.0 keV) | `RamosM_DR2/eRASS3_Hard_v1.2.fits` | 9,054,720 B | 15,980 sources, DET_LIKE_3 ≥ 12 (likelihood over 0.2–5.0 keV) ([paper](https://arxiv.org/abs/2607.27772) §4.4/Table 15) |
| Counterparts ×6 | `eRASSc3_{Main,Hard}_{LS10,GDR3,CW2020}_Public_27Jul2026.fits.gz` | 1.05 GB / 0.86 GB / 0.82 GB (Main three) | NWAY probabilistic counterparts vs Legacy Survey DR10, Gaia DR3, CatWISE2020 ([paper](https://arxiv.org/abs/2607.27772) §6) |
| CVs (SDSS-V) | `BrinkJ_DR2/SRG_eROSITA_SDSS_CV_CATALOGUE.fits.gz` | — | 587 CVs from SDSS-V DR20 spectroscopy of eRASS1/eRASS:3 sources ([arXiv:2607.27960](https://arxiv.org/abs/2607.27960)) |
| CVs (new eRASS1) | `SchwopeA_DR2/allnewdr1cvs_fin_2cds.fits` | — | new CV systems from eRASS1 ([arXiv:2607.28066](https://arxiv.org/abs/2607.28066)) |

Unlike DR1 there is **no supplementary 5 ≤ DET_LIKE_0 < 6 list** ("given the high expected spurious
detection rate", [paper](https://arxiv.org/abs/2607.27772) §4). Spurious fraction at the DET_LIKE_0=6
threshold is expected ~14%, as in eRASS1 ([paper](https://arxiv.org/abs/2607.27772) §4).

**THE column-structure verdict (kill check #1).** The Main catalog data model
([eRASS3_Main_v1.3.html](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.html),
250 columns **[computed from file]**) carries **only stacked eRASS:3 quantities** — DET_LIKE_0,
ML_CTS/ML_RATE/ML_FLUX (+asymmetric errors), ML_BKG/ML_EXP/ML_EEF and aperture photometry in the
0.2–2.3 keV band plus nine sub-bands P1–P9, plus flags. **There are no per-eRASS (per-epoch)
columns.** The README's premise "DR2's multi-epoch (eRASS1 vs eRASS:3) fluxes" is therefore wrong
as stated: no per-epoch fluxes ship *inside* DR2. What ships instead is a consortium cross-walk
column **`UID_DR1`** (eRASS1 Main UID; >0 strong association, <0 weak, 0 none), built with
positional criteria only — "no flux criterion was applied for matching" because the epochs differ
([paper](https://arxiv.org/abs/2607.27772) §5; strong point matches: 4× combined positional error,
5″–16″; weak: ≤16″). So the public variability axis is exactly one comparison: **eRASS1 (DR1) vs
the eRASS:3 stack (DR2)** — route (b), with the DR1 catalog downloaded separately. The
[upper-limit server](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/UpperLimitServer_dr2/) is
likewise **cumulative eRASS:3 only** (no per-survey limits). Per-source light curves exist inside
the consortium (srctool products for DET_LIKE > 20 sources, [paper](https://arxiv.org/abs/2607.27772)
§3.2.4) but are **not released** ([FAQ](https://erosita.mpe.mpg.de/dr2/FAQ_dr2/)).

**Access.** Bulk FITS over HTTP only. **No TAP anywhere yet** (checked 2026-08-14): HEASARC TAP has
`erass1main`, `erass1hard`, `erassmastr` — DR1 only
([heasarc.gsfc.nasa.gov/xamin/vo/tap](https://heasarc.gsfc.nasa.gov/xamin/vo/tap)); VizieR TAP has
eRASS1 as [J/A+A/682/A34](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/682/A34) and
no eRASS:3 table ([TAPVizieR](https://tapvizier.cds.unistra.fr/TAPVizieR/tap), `tap_schema` search).
No account was needed for anything.

**DR1 value-added products → DR2 successors** (for the
[`../IDEAS/erosita-source-classifier.md`](../IDEAS/erosita-source-classifier.md) rebase; DR1 file
list: [Catalogues_dr1](https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/)):

| DR1 product | DR2 successor? |
|---|---|
| Salvato counterparts (`Salvato_etal2025_DR1_{LS10,GDR3,CW2020}`) | **Yes** — `eRASSc3_*_Public_27Jul2026` (Ramos-Ceja §6) |
| Merloni Main/Hard/Supp | **Yes** — Main v1.3 / Hard v1.2 (no Supp) |
| Bulbul cluster catalogs, Kluge optical clusters, Liu superclusters | **No DR2 successor in the release** |
| Freund coronal (HamStar-style, [J/A+A/684/A121](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/684/A121)) | **No DR2 successor in the release** |
| BLAZE/BlazEr1 blazars, Kaltenbrunner HMXB-LMC | **No DR2 successor in the release** |
| — | **New in DR2**: Brink SDSS-V CVs, Schwope new-eRASS1 CVs |

**DR1 side note.** The DR1 Main tarball now serves **v1.2**
(`MerloniA_DR1/eRASS1_Main.v1.2.fits.tar.gz`, 643,072,855 B, inner FITS dated 2026-01-09,
930,203 rows **[computed]**) — a revision of the original 2024 release; `UID_DR1` resolves against
it perfectly (742,056 of 742,056 non-zero `|UID_DR1|` values found, 100.0% **[computed]**, see §2).

---

## 2. W2 — the DR1→DR2 variability slice: method and caveats

**Construction.** Join DR2 Main on `|UID_DR1|` → DR1 `UID` (742,056 DR2 rows carry a non-zero
`UID_DR1`: 708,307 strong + 33,749 weak **[computed]**; the paper's Table 6 counts 689,050 strong +
10,324 weak *point-like* + extended, [arXiv:2607.27772](https://arxiv.org/abs/2607.27772)).
Compare `ML_RATE_1` (0.2–2.3 keV, identical band definition in both catalogs — DR1 data model:
[eRASS1_Main_v1.2.html](https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/MerloniA_DR1/eRASS1_Main_v1.2.html)).
Rates, not fluxes, avoid ECF assumptions — though empirically it makes no difference: the median
flux-ratio/rate-ratio for bright pairs is 1.0000 **[computed]**, i.e. DR1 and DR2 use identical
energy conversion.

**The physics trap this construction must respect:** the eRASS:3 stack *contains* the eRASS1 data.
A source that switched off after eRASS1 does not go to ratio 0 — it goes to R ≈ t₁/t₃ ≈ 1/3
(median t₃/t₁ = 2.9 over the ranked set **[computed]**). Fader amplitudes in raw stacked ratios are
therefore compressed to ≳ 1/3, while riser amplitudes are diluted ×~3 but unbounded. We therefore
also reconstruct the implied **post-eRASS1 rate** r₂₃ = (r₃t₃ − r₁t₁)/(t₃ − t₁) per source and
quote epoch-space amplitudes from it. This assumes the 030 reprocessing preserves the eRASS1
counts; where r₂₃ + 2σ < 0 that assumption is **violated** (030 flare-filtering removed eRASS1
events, pileup, or a bad fit — plausible for exactly the brightest eRASS1 transients) and the
amplitude is reported as NaN with `containment_violated=True` (5 such at z ≥ 5 **[computed]**);
milder tension (R < 0.9·floor) is flagged `subfloor`.

**Cleaning cuts** (all documented in the script; consortium-endorsed flag recipe from
[arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §5.3 — "exclude all flagged sources except
those with the FLAG_SP_SCL flag"):

- point-like in **both** catalogs (EXT_LIKE = 0) — extent changes fake flux changes;
- none of FLAG_SP_SNR/BPS/LGA/GC_CONS, FLAG_NO_RADEC_ERR, FLAG_NO_CTS_ERR, FLAG_OPT in either
  (FLAG_OPT also kills optical-loading fake variability of bright stars — cost: the very brightest
  stars are excluded from this slice);
- separation ≤ 10″ **and** ≤ 3.44·√(POS_ERR₁²+POS_ERR₃²) (2-D 99% Rayleigh radius);
- valid positive rates/errors both sides, t₃ > t₁.

742,056 → **632,668 clean pairs** (cut-failure counts, each over the full join and overlapping:
52,879 not point-both, 19,479 flagged, 86,278 separation, 4,507 invalid rates **[computed]**).

**Scale systematic, measured not assumed:** for 1,238 pairs at ≥20σ rate significance on both
sides, median R = **0.979** — the net 030-vs-010 + stacking scale offset is ~2%, and all ratios are
normalized by it. Its 5–95% spread (0.59–1.42 **[computed]**) at 20σ is real source variability
(statistical scatter at 20σ would be ~7%), consistent with an AGN-dominated bright population.

**Eddington bias, bounded not ignored:** the all-pair median R = 0.825 **[computed]** — the typical
eRASS1-selected source is 17% "fainter" in the deeper stack, the classic flux-limited-selection
artifact (faint eRASS1 detections ride upward fluctuations). This is why the ranked list requires
variability significance z ≥ 5 (computed from both catalogs' asymmetric errors after scale
correction) and why fade candidates near the DR1 threshold are distrusted; the top-30 fade
candidates all have DR1 DET_LIKE_0 > 94 **[computed from out/w2_ranked_variables.csv]**, far from
the DET_LIKE_0 = 6 threshold.

### Ratio distribution (the threshold, informed)

632,668 clean pairs **[computed → `out/w2_stats.json`, plot `out/w2_ratio_distribution.png`]**:

| population | n | R 1% | R 50% | R 99% | amp>2 | amp>5 | amp>10 |
|---|---|---|---|---|---|---|---|
| all clean | 632,668 | 0.376 | 0.825 | 2.09 | 9.7% | 0.030% | 0.0054% |
| z ≥ 5 | 2,138 | 0.340 | 1.955 | 12.3 | 58.9% | 8.6% | 1.5% |

Conservative (1σ-worst-direction) amplitudes at z ≥ 5: **904** pairs > 2×, **264** > 3×, **62** >
5×, **14** > 10× in *stacked* space; in reconstructed *epoch* space **225** > 5×, **49** > 10×,
**10** > 20× **[computed]**. So "factor >10" is a usable headline threshold on the rise side, but
the stacked construction cannot show a >3× fade directly — fade claims live in epoch space with the
containment caveat. The ranked table (`out/w2_ranked_variables.csv`, top 200 by
max(stacked, epoch) conservative amplitude at z ≥ 5) is **69 risers / 31 faders** in the top 100
**[computed]**.

### Census margins (both directions of catalog non-overlap)

- **Vanished** (`out/w2_vanished.csv`): clean DR1 point sources at DET_LIKE_0 ≥ 30 with *no* DR2
  counterpart at all: **261 of 118,253** (0.22%) **[computed]** — the deeper stack should contain
  every constant source, so these are strong-fade candidates, *but* the paper warns some bright
  sources drop out of DR2 through a source-confusion issue
  ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §3.2.5/§5.3), so each needs vetting before
  any claim. Consortium context: 21% of clean eRASS1 point sources lack an eRASS:3 match overall,
  ~12.6% spurious + ~8.4% variability/Poisson ([paper](https://arxiv.org/abs/2607.27772) §5.1) —
  our DET_LIKE ≥ 30 cut removes the spurious-dominated regime.
- **New-bright** (`out/w2_new_bright.csv`): clean DR2 point sources with UID_DR1 = 0 at
  DET_LIKE_0 ≥ 30: 36,792 (expected — deeper stack), of which **286 with stacked rate > 0.2 ct/s**
  **[computed]** are risers eRASS1 should have seen; implied minimum rise factors (stacked rate ÷
  empirical eRASS1 5th-percentile detected rate at matching exposure — an approximation, flagged in
  the CSV) reach ×97–×223 for the top objects **[computed]**.

---

## 3. W3 — cross-match of the top candidates

140 candidates (top 100 ranked pairs + top 20 vanished + top 20 new-bright) were cross-matched
against **Gaia DR3** (CDS X-Match, `vizier:I/355/gaiadr3`, ≤10″, anonymous single call) and
**SIMBAD** (TAP upload join, ≤15″, anonymous single call), both on 2026-08-14. Coverage: **133/140
have a Gaia counterpart, 114/140 a SIMBAD entry** **[computed]**. Output:
[`out/m1_candidates.csv`](out/m1_candidates.csv) (59 KB) with position, ratios, likelihoods, Gaia
astrometry/photometry, SIMBAD identity, first-guess class, and per-object caveats.

**The slice recovers known transient classes at the top of the list** (all identifications =
nearest SIMBAD object, queried 2026-08-14):

| rank | 3eRASS name | direction, amplitude (cons.) | SIMBAD | class |
|---|---|---|---|---|
| 1 | J161242.8-522522 | rise, ×475 (epoch), z=101 | V* QX Nor | LMXB outburst |
| 2 | J054334.0-682222 | rise, ×99 | 2E 1550 | X-ray binary (LMC direction) |
| 3 | J162636.4-515631 | rise, ×77 | SWIFT J1626.5-5156 | Be/X-ray pulsar HXB |
| **4** | **J094452.8-711152** | **rise, ×57, z=43** | **— none within 15″; no Gaia within 10″** | **unidentified riser** |
| 5 | J090506.7-533020 | rise, ×55 | 2MASS J09050682-5330195 | XB* |
| 7 | J071521.8-191603 | fade, ≥×32 (epoch, 2σ) | SRGt J071522.1-191609 | SRG transient caught declining |
| 9 | J142111.9-624156 | rise, ×26 | 4U 1416-62 | HXB |
| 13 | J060622.5-624814 | fade, ≥×18 (epoch, 2σ) | WISE J060621.36-624826.5 (G, Gaia G=20.6, no plx) | **TDE-like candidate** |

New-bright validates independently: **V1708 Sco B** (nova), **RX J1709.5-2639** (LXB),
**eRASSt J234402.9-352640** and **eRASSt J045650.3-203750** (already-named eROSITA transients),
**CTCV J1928-5001** and **RX J0749.1-0549** (CVs in outburst) — plus one unidentified:
**3eRASS J155100.8-453347** (1.38 ct/s stacked, implied rise ≥×49, Gaia G=17.75 star nearby, no
SIMBAD). Vanished top-20: an SMC-region RB? candidate, YSOs (single-flare detections in eRASS1),
and **7 with no optical/SIMBAD identity at all** — fade-or-dropout, unvetted. Class mix over all
140: X-ray binaries (14), SIMBAD CVs (10) + Galactic-star/CV? guesses (11, of which 6 on the
red-dwarf flare locus), AGN/Seyfert/blazar/radio (24), young-star types Or*/TT*/Y*O/Y*?/Em*/Pe*
(22), galaxies (8), unidentified or X-ray-only (23), remainder miscellaneous stars **[computed]**.

**Blunt honesty about what this is:** a ranked, class-annotated candidate list built from public
catalogs — not confirmed discoveries. Every object needs the M2 vetting pass (archival X-ray,
known-transient registries, per-object plausibility) before any external claim.

---

## 4. Novelty check (kill check #2) — verdict

**The DR2 release itself ships no variability/transient product.** The release contents are the
three catalog groups in §1's table (file listing:
[Catalogues_dr2](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/)); the survey
paper uses the eRASS1↔eRASS:3 match only to *quality-check eRASS1* (spurious-fraction accounting,
[arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §5.1) and publishes no ranked flux-ratio list.

What already exists nearby, so our claim-space is drawn honestly:

- **DR1 variability catalogue** ([arXiv:2401.17280](https://arxiv.org/abs/2401.17280)): *intra*-eRASS1
  (eroday-scale) variability of ~128k sources — different axis (hours–days, not the 0.5–1.5 yr
  eRASS1→eRASS2/3 axis probed here).
- **eRO-ExTra** ([arXiv:2501.04208](https://arxiv.org/abs/2501.04208)): eRASS1-vs-eRASS2
  extragalactic non-AGN transients — the consortium *has* run inter-eRASS variability, on
  proprietary per-eRASS catalogs, for a restricted class selection; not reproducible publicly and
  not a DR2 product.
- **eRASS1 Galactic transients** ([VizieR J/MNRAS/544/885](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/MNRAS/544/885),
  Maan, Katira & Mooley, updated 2026-01-23): eRASS1-based Galactic transient catalog.
- Single-object eRASSt papers (e.g. [eRASSt J234402.9-352640](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/672/A167)).

**Verdict: the specific slice run here — a public, reproducible DR1×DR2 ranked variable list over
the full Western hemisphere, both directions, with the stacking algebra made explicit — has not
been published as of 2026-08-14.** It is a *first-public-look* novelty, not a durable one: the
consortium holds per-eRASS catalogs and will supersede this axis whenever it publishes them (DR3,
H2 2028, per [erosita.mpe.mpg.de/erass](https://erosita.mpe.mpg.de/erass/)). The durable assets are
(a) individual unidentified candidates if any survive vetting, and (b) the ingest + joins built
here, which are exactly what the December Gaia DR4 NSS join needs (W4).

---

## 5. Recommended M2

1. **Vet the unidentified candidates** (highest value density): 3eRASS J094452.8-711152 (×57 riser,
   no counterpart), 3eRASS J155100.8-453347 (new-bright ≥×49), the 7 optical-faint vanished
   sources, and the TDE-like fader J060622.5-624814. Per object: archival X-ray (upper-limit server
   for the stacked limit, 2RXS/XMM slew), ZTF/ATLAS forced photometry where public, transient-name
   servers, and the DR2 counterpart catalogs' p_any (we only used raw Gaia cones here — the
   released NWAY counterpart catalogs are the professional-grade version, §1).
2. **Vanished-list forensics**: distinguish real strong faders from §3.2.5 confusion dropouts
   using the DR1 images (public in DR1) at each vanished position; the paper explicitly recommends
   exactly this check ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §5.3).
3. **Classifier rebase decision** for [`../IDEAS/erosita-source-classifier.md`](../IDEAS/erosita-source-classifier.md):
   the released `eRASSc3` counterpart catalogs (LS10/GDR3/CW2020 features at 2M-source scale)
   are the training substrate; DR1's Salvato-era features map 1:1.
4. **W4 prep stays on schedule**: the parquet pair table + scripts here are the ingest layer for
   the Gaia DR4 NSS × DR2 join on 2026-12-02.

## Files

- `out/w2_stats.json` — all W2 statistics quoted above
- `out/w2_ranked_variables.csv` — top 200 ranked variable pairs (z ≥ 5)
- `out/w2_vanished.csv` / `out/w2_new_bright.csv` — census margins (top 100 each)
- `out/m1_candidates.csv` — the 140-candidate annotated table (W3 deliverable)
- `out/w2_ratio_distribution.png` — ratio distribution, clean pairs vs z ≥ 5
- `data/w2_pairs.parquet` — full 632,668-pair cleaned join (gitignored, regenerable)
