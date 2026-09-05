# writeup-audit — every number that could enter the draft, re-derived

> **2026-09-05 interpretation correction:** numerical re-derivation did not validate
> the inference that fewer than six selected candidates are contaminants. That claim
> is withdrawn; the current CSV records `NOT_IDENTIFIABLE` and 92 verified/15 corrected
> rows. See [the closeout](PUBLICATION-CLOSEOUT-2026-09-05.md) for this and the prior-art,
> classifier and bright-end category corrections. The dated audit below is historical.

*2026-08-18, M5-writeup. Machine-readable version: [`out/m5w_audit.csv`](out/m5w_audit.csv),
produced by [`scripts/m5w_audit.py`](scripts/m5w_audit.py) (107 audited quantities, re-run
end-to-end in one command). Repo law: sourced-or-UNSOURCED. Nothing in the draft that is not
in this table.*

**Result: 93 VERIFIED, 14 CORRECTED, 0 NOT-RE-DERIVABLE.** Every headline quantity re-derives
from a committed artifact. Five of the corrections are load-bearing and change what the draft
can say; the rest are rounding or definitional and are recorded so the draft quotes the
re-derived value, not the milestone-doc value. One number in M1 turned out to be **UNSOURCED**
(§1.5) and is dropped. Separately, the audit exposed a validation gap in the census method and
closed it with a new measurement (§1.6) — the strongest single result of this milestone.

**Provenance tiers**

| tier | meaning |
|---|---|
| `[out]` | re-derived from a committed `out/` CSV or JSON |
| `[bulk]` | re-derived from `data/` — gitignored, but byte-for-byte regenerable by the M1–M4 download scripts from the public URLs recorded in M1 §1 |
| `[external]` | not derivable here; must be checked against a published source |

---

## 1. The corrections that matter

### 1.1 The artifact/fader threshold band is **+17/−8, not +35/−12**

M2 §3 states the fade-candidate count is "**107 (+35/−12)** under threshold choice". Replaying
M2's own classification tree ([`scripts/m2_upper_limits.py`](scripts/m2_upper_limits.py) lines
100–129) verbatim with the presence cut moved to 1.3 and 2.0 gives:

| presence cut | fade candidates |
|---|---|
| 1.2 | 94 |
| 1.3 | **99** |
| 1.4 | 103 |
| **1.5 (adopted)** | **107** |
| 1.75 | 119 |
| 2.0 | **124** |
| 2.5 | 137 |

So the honest band is **107 (+17/−8)**, i.e. **99–124**, not 95–142.

*Why M2 was wrong.* The cut does not act in isolation — the tree tests
`ARTIFACT-SPLIT/MOVED` (a DR2 source within 15″) and `INDETERMINATE-HALO` **before** the
presence branch, and applies the 40″ PSF-confuser test **after** it. M2's `+35` counted every
artifact row with presence in (1.5, 2.0]; 18 of those 35 are caught by the split/PSF branches
and never become faders. M2's `−12` counted every blank row with presence in (1.3, 1.5]; 4 of
those 12 are `CONFUSED-IDENTITY`, not fade candidates. The naive counts really are 35 and 12 —
they are simply not the answer to the question asked.

**Consequence for the draft**: the census systematic is *smaller and tighter* than M2 claimed.
The draft quotes 107 (+17/−8) and shows the full cut→count curve as the systematic.

### 1.2 One of the 25 upper-limit calibrators is degenerate — the presence calibration is n = 24

M2 §3 states "steady calibrators are all ≫1". One of the 25
(`3eRASS J114550.9-552043`) has `ul_s_flux = inf` and therefore `ul_presence = 0.0`; the
upper-limit server returned a degenerate source-flux limit at that position. The valid 24 give
presence **5.68–13.87**, which is the claim M2 wanted to make and which the data do support.
The `fade_frac` calibration is unaffected (it uses `ul_b_flux` only) and stays n = 25.

**Consequence for the draft**: state the calibration as 24 of 25 steady comparison sources, and
give the range, not the word "all".

### 1.3 The calibration statistic M2 calls a median is a mean

M2 §3: "`fade_frac` … calibration median **1.13 ± 0.07**". Re-derived from
[`out/m2_ul_calibration.csv`](out/m2_ul_calibration.csv): mean 1.127, sample sd 0.0675,
**median 1.140**. The quoted pair is the mean ± sd. Both are defensible; the label was wrong.

**Consequence for the draft**: quote "mean 1.13 ± 0.07 (median 1.14)".

### 1.4 The eRASS:3 span is internally inconsistent by 4 days

M1 §1 attributes to the DR2 portal: "eRASS:3 = cumulative eRASS1+2+3, **2019-12-12 → 2021-06-16,
556 days**". Those three figures cannot all be right — 2019-12-12 → 2021-06-16 is **552 days**;
556 days after 2019-12-12 is 2021-06-20. One of the three is a transcription error and the
milestone doc does not record which. The eRASS1 half is independently checkable and is correct:
the DR1 catalogue's own `MJD_MIN`/`MJD_MAX` span 2019-12-11 22:07 UT → 2020-06-11, 182.5 d.

**Consequence for the draft**: the draft does not quote the span in days. It states the epoch
range only ("2019 December – 2021 June"), cited to the release paper, and derives everything
epoch-dependent from the per-source `ML_EXP` ratio (median t₃/t₁ = 2.84, re-derived) instead.

### 1.5 UNSOURCED: M1's decomposition of the release paper's unmatched fraction

M1 §2 writes: "Consortium context: 21% of clean eRASS1 point sources lack an eRASS:3 match
overall, **~12.6% spurious + ~8.4% variability/Poisson** ([paper] §5.1)", and M2 §3 repeats the
8.4% figure. The M5-writeup prior-art sweep read §5.1 directly. What the paper actually reports
(Fig. 10 caption, verbatim) is:

> "While in the entire catalogue the fraction of point sources not matched to eRASS:3 is about
> 21%, this drops to about 3.5% for DET_LIKE>10 and 0.15% for DET_LIKE>50."

§5.1's framing is that unmatched implies spurious; **it does not mention variability at all**,
and the 12.6/8.4 split appears nowhere. That decomposition is an M1 gloss misattributed to the
paper. Marked **UNSOURCED**.

**Consequence for the draft**: the 12.6/8.4 split is not used. The draft quotes only the three
figures the paper actually publishes (21% / 3.5% / 0.15%) — and this correction turns out to
*strengthen* the note, because §5.1's silence on variability is precisely what the census tests.

### 1.6 The gap the audit found, and the measurement that closed it

The census calls a vanished source a real fader when the DR2 upper-limit server returns
presence *P* = UL_B/UL_S ≤ 1.5. M2 calibrated that threshold on 25 steady sources selected at
**≥ 20σ** — far brighter than the fade candidates, whose median eRASS1 flux is
6.8 × 10⁻¹⁴ erg cm⁻² s⁻¹ and median DET_LIKE_0 is 40. Nothing in M1–M4 tested whether *P*
still discriminates down there. If it did not, the census would be measuring detectability
rather than variability and the headline would be wrong.

[`scripts/m5w_faint_validation.py`](scripts/m5w_faint_validation.py) settles it. Sixty steady
DR1×DR2 pairs, drawn to match the fade candidates in **both** eRASS1 flux (1.9 × 10⁻¹⁴ –
1.7 × 10⁻¹³) and DET_LIKE_0 (31–82), were queried at the same DR2 upper-limit service (one
anonymous POST, no account, nothing submitted):

| population | n | presence *P* | falls in the fader class (*P* ≤ 1.5)? |
|---|---|---|---|
| fade candidates | 107 | 1.00 – **1.49** (median 1.04) | all, by construction |
| steady flux-matched controls | 60 | **2.03** – 3.78 (median 2.60) | **0 of 60** |

The two populations are **disjoint**, with the adopted cut of 1.5 sitting inside the empty
interval between them. With 0 of 60 controls misclassified, the false-positive rate is
< 4.9% at 95% one-sided confidence: **fewer than 6 of the 107 faders can be sources that are
still there.**

This is a new result, not a re-derivation, and it is the main reason the note is worth
writing: the threshold is not a tuned parameter, it sits in a gap the data themselves put
there. It is now the black outline in Figure 1a of the draft.

---

## 2. The full audit table

Claimed values are as written in the M1–M4 milestone docs. `→` marks the value the draft uses.

### 2a. Cross-walk, flux scale, amplitude census (M1 §1–§2)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 1 | clean DR1↔DR2 pairs | 632,668 | 632,668 | bulk | `data/w2_pairs.parquet` row count | VERIFIED |
| 2 | DR2 Main rows | 1,975,540 | 1,975,540 | bulk | `eRASS3_Main_v1.3.fits` NAXIS2 | VERIFIED |
| 3 | DR2 Main columns | 250 | 250 | bulk | FITS header | VERIFIED |
| 4 | DR2 point sources | 1,911,744 | 1,911,744 | bulk | `EXT_LIKE == 0` | VERIFIED |
| 5 | DR2 extended sources | 63,796 | 63,796 | bulk | `EXT_LIKE > 0` | VERIFIED |
| 6 | DR2 Hard rows | 15,980 | 15,980 | bulk | `eRASS3_Hard_v1.2.fits` | VERIFIED |
| 7 | DR1 Main rows | 930,203 | 930,203 | bulk | `eRASS1_Main.v1.2.fits` | VERIFIED |
| 8 | DR2 rows with non-zero `UID_DR1` | 742,056 | 742,056 | out | `out/w2_stats.json` | VERIFIED |
| 9 | DR2 fraction with DR1 cross-walk | 37.6% | 37.6% | out | 742,056 / 1,975,540 | VERIFIED |
| 10 | DR2 carries **no** per-epoch time column | 0 such columns | 0 | bulk | FITS column list | VERIFIED |
| 11 | DR2 carries `UID_DR1` | yes | yes | bulk | FITS column list | VERIFIED |
| 12 | ≥20σ bright-tier pairs | 1,238 | 1,238 | out + bulk | `w2_stats.json`; independently recomputed from the parquet | VERIFIED |
| 13 | scale offset, median R | 0.979 | 0.9794 | out + bulk | independently recomputed from the parquet | VERIFIED |
| 14 | scale offset as a percentage | "~2%" | **2.06%** → *2%* | out | 1 − 0.9794 | CORRECTED (rounding) |
| 15 | all-pair median R (scale-normalised) | 0.825 | 0.825 | bulk | raw median 0.808 ÷ 0.9794 | VERIFIED |
| 16 | exposure ratio t₃/t₁, median | 2.9 | **2.84** | bulk | `ML_EXP_1 / ML_EXP_1_D1`, all clean pairs | CORRECTED |
| 17 | pairs at variability significance z ≥ 5 | 2,138 | 2,138 | out | `w2_stats.json` | VERIFIED |
| 18 | z ≥ 5 with conservative stacked amp > 5× | 62 | 62 | out | `w2_stats.json` | VERIFIED |
| 19 | z ≥ 5 with conservative stacked amp > 10× | 14 | 14 | out | `w2_stats.json` | VERIFIED |
| 20 | epoch-space amp > 5× | 225 | 225 | out | `w2_stats.json` | VERIFIED |
| 21 | epoch-space amp > 10× | 49 | 49 | out | `w2_stats.json` | VERIFIED |
| 22 | clean DR1 point sources at DET_LIKE_0 ≥ 30 | 118,253 | 118,253 | out | `w2_stats.json` | VERIFIED |
| 23 | vanished (no DR2 counterpart) | 261 | 261 | out | `w2_stats.json`, `m2_vanished_forensics.csv` | VERIFIED |
| 24 | new-bright risers | 286 | 286 | out | `w2_stats.json`, `m2_new_bright_full.csv` | VERIFIED |
| 25 | eRASS1 epoch span | 2019-12-12 → 2020-06-11 | 2019-12-11 22:07 UT → 2020-06-11, 182.5 d | bulk | DR1 `MJD_MIN`/`MJD_MAX` | VERIFIED (sub-day rounding) |
| 26 | eRASS:3 span | 2019-12-12 → 2021-06-16, 556 d | **552 d** from the quoted dates | external | arithmetic; portal figure not independently checkable here | **CORRECTED — see §1.4; not used in the draft** |

### 2b. Vanished-source census and its systematic (M2 §3)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 27 | census size | 261 | 261 | out | `m2_vanished_forensics.csv` row count | VERIFIED |
| 28 | fade candidates | 107 | 107 | out | `forensic_class_v2` tally | VERIFIED |
| 29 | catalogue artifacts | 148 | 148 | out | tally | VERIFIED |
| 30 | indeterminate | 6 | 6 | out | `CONFUSED-IDENTITY` 5 + `INDETERMINATE-HALO` 1 | VERIFIED |
| 31 | artifact percentage | 57% | 57% | out | 148/261 | VERIFIED |
| 32 | fader percentage | 41% | 41% | out | 107/261 | VERIFIED |
| 33 | erbox/confusion sub-mode | 85 | 85 | out | tally | VERIFIED |
| 34 | extended-absorption sub-mode | 36 | 36 | out | tally | VERIFIED |
| 35 | cross-walk-miss sub-mode | 25 | 25 | out | tally | VERIFIED |
| 36 | vanished as a fraction of bright DR1 | 0.22% | 0.22% | out | 261 / 118,253 | VERIFIED |
| 37 | faders as a fraction of bright DR1 | 0.09% | 0.09% | out | 107 / 118,253 | VERIFIED |
| 38 | band, tightening cut 1.5 → 1.3 | −12 | **−8** | out | M2 tree replayed | **CORRECTED — §1.1** |
| 39 | band, loosening cut 1.5 → 2.0 | +35 | **+17** | out | M2 tree replayed | **CORRECTED — §1.1** |
| 40 | fader count, low end | 95 | **99** | out | tree replay at 1.3 | **CORRECTED** |
| 41 | fader count, high end | 142 | **124** | out | tree replay at 2.0 | **CORRECTED** |
| 42 | fader presence range | ≤1.5 by construction | 1.00–1.49, median 1.04 | out | `ul_presence` | VERIFIED |
| 43 | artifact presence range | 2–95 | 1.50–95.55 | out | `ul_presence` | VERIFIED |
| 44 | M1 top-20-by-DET_LIKE artifact count | 14/20 | 14/20 | out | tally over the top 20 | VERIFIED |
| 45 | artifact fraction above DET_LIKE 100 | (new) | 71% (20/28) | out | `m5w_audit.py` / `m5w_figure.py` | NEW, re-derived |
| 46 | brightest fade candidate | (new) | DET_LIKE_0 = 242; all 6 dropouts above it are artifacts or indeterminate | out | `m2_vanished_forensics.csv` | NEW, re-derived |

### 2c. Upper-limit-server calibration (M2 §3)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 47 | steady calibration pairs | 25 | 25 | out | `m2_ul_calibration.csv` | VERIFIED |
| 48 | `fade_frac` central value | median 1.13 | **mean 1.127, median 1.140** | out | `m2_ul_calibration.csv` | **CORRECTED — §1.3** |
| 49 | `fade_frac` scatter | ±0.07 | sample sd 0.0675 | out | `m2_ul_calibration.csv` | VERIFIED (it is an sd) |
| 50 | calibrator presence | "all ≫1" | **24 of 25**; one degenerate (UL_S = inf → P = 0) | out | `m2_ul_calibration.csv` | **CORRECTED — §1.2** |
| 51 | valid calibrator presence range | — | 5.68–13.87 | out | `m2_ul_calibration.csv` | NEW, re-derived |

### 2d. Fader demographics (M2 §3)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 52 | AGN-like counterparts | 39 | 39 | out | Gaia DR3 DSC class AGN/QSO **or** CatWISE W1−W2 ≥ 0.8 | VERIFIED |
| 53 | bright IR-flat (stellar) counterparts | 23 | 23 at \|W1−W2\| < 0.3 | out | CatWISE W1 < 15 | VERIFIED, **definition supplied** |
| 54 | — sensitivity of #53 | — | 24 at <0.4, 25 at <0.5; 39 have W1<15 at any colour | out | `m2_archival_xray.csv` | NEW |
| 55 | faders in the LMC box | 25 | 25 | out | RA 60–105, Dec −75…−60 | VERIFIED |
| 56 | faders with a prior X-ray detection | 21 | 21 | out | 2RXS/XMMSL3/CSC2.1/2SXPS/XMMSSC | VERIFIED |
| 57 | faders with no CatWISE source | 3 | 3 | out | `catwise_sep` null | VERIFIED |
| 58 | fader median DET_LIKE_0 | 40 | 40 (39.7) | out | `m2_vanished_forensics.csv` | VERIFIED |
| 59 | faders above DET_LIKE 100 | 8 | 8 | out | `m2_vanished_forensics.csv` | VERIFIED |
| 60 | AGN-like and stellar sets disjoint | (implied) | overlap = 0 | out | `m2_archival_xray.csv` | VERIFIED |

### 2e. LMC sub-study (M4 Part A)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 61 | LMC-box fade candidates | 25 | 25 | out | `m4_lmc_ogle_matches.csv` | VERIFIED |
| 62 | matches in OGLE OCVS (10 classes) | 0 | 0 | out | `ocvs_n_match` | VERIFIED |
| 63 | matches in XROM | 0 | 0 | out | `xrom_n_match` | VERIFIED |
| 64 | matches in Sabogal Be candidates | 0 | 0 | out | `be_n_match` | VERIFIED |
| 65 | matches in eRASS1_HMXB_LMC | 0 | 0 | out | `hmxb_n_match` | VERIFIED |
| 66 | shifted-position control positions | 400 | 400 | out | `m4_lmc_ogle_control.csv` | VERIFIED |
| 67 | control OCVS hits | 3 | 3 | out | `m4_lmc_ogle_control.csv` | VERIFIED |
| 68 | expected chance matches per 25 | 0.19 | 0.188 | out | 3/400 × 25 | VERIFIED |
| 69 | faders with a Be-donor-capable star | 1 | 1 | out | `be_donor_candidate` | VERIFIED |
| 70 | faders with none | 24 | 24 | out | `be_donor_candidate` | VERIFIED |
| 71 | nearest OCVS variable to any fader | 0.4–4.8′ | 0.4–4.8′ | out | `ocvs_nearest_any_arcmin` | VERIFIED |
| 72 | nearest XROM object | ≥50′ | **49.8′** | out | `xrom_nearest_any_arcmin` | **CORRECTED (rounded the wrong way)** |
| 73 | nearest known LMC HMXB | ≥13′ | **12.9′** | out | `hmxb_nearest_any_arcmin` | **CORRECTED (rounded the wrong way)** |
| 74 | nearest Sabogal Be candidate | 2.0° | 2.05° | out | `be_nearest_any_arcmin` | VERIFIED |
| 75 | match radii | 5.7–11.2″ | 5.7–11.2″ | out | `r_match_arcsec` | VERIFIED |
| 76 | firm AGN-coloured of the 25 | 9 | 9 | out | W1−W2 ≥ 0.8 | VERIFIED |
| 77 | OCVS pool searched | 217,725 | 217,725 | bulk | `data/ogle/*_ident.dat` line counts | VERIFIED |
| 78 | — OGLE-IV rrlyr / ecl | 41,471 / 63,252 | same | bulk | ident files | VERIFIED |
| 79 | — OGLE-III lpv | 91,995 | 91,995 | bulk | ident file | VERIFIED |
| 80 | Sabogal LMC Be candidates | 2,446 | 2,446 | bulk | `data/ogle/sabogal_lmc_be.csv` | VERIFIED |
| 81 | eRASS1_HMXB_LMC rows | 53 | 53 | bulk | `eRASS1_HMXB_LMC_v1.0.fits.tgz` | VERIFIED |
| 82 | OGLE-IV dark interval | 886 d | 886 d | out | XROM CAL 83 max gap, `m4_lmc_ogle_lightcurves.csv` | VERIFIED |
| 83 | — its endpoints | 2020-03-13 → 2022-08-16 | JD difference of those two dates = 886 d | out | astropy | VERIFIED (self-consistent) |
| 84 | eRASS2+3 window inside the OGLE dark interval | yes | yes | out | 2020-06-11 → 2021-06-16 ⊂ 2020-03-13 → 2022-08-16 | VERIFIED |
| 85 | XROM series last epoch | 2026-05-25 | HJD′ 11186.5 | out | `m4_lmc_ogle_lightcurves.csv` | VERIFIED |
| 86 | OCVS RRLYR light curves end | 2016-04-14 | HJD′ 7492.5 | out | `m4_lmc_ogle_lightcurves.csv` | VERIFIED |
| 87 | LMC HMXB donor G range | 12.68–17.00, median 14.85 | column present but named `Gmag_Gaia`; values not re-read in this pass | bulk | `eRASS1_HMXB_LMC_v1.0.fits.tgz` | **see note below** |

**Note on #87.** The audit script looked for a Gaia G column under the names `Gmag`/`G`/
`phot_g_mean_mag`/`gaia_g`/`g_mag`; the VAC's column is `Gmag_Gaia`, so the three donor-magnitude
figures were not re-derived in the automated pass. They are **not used in the draft** — the draft
states the Be-donor test's magnitude cut (G ≤ 17.5) and its outcome, not the VAC's magnitude
distribution. Flagged here rather than silently dropped.

### 2f. Vetting verdicts (M2 §1)

| # | number | claimed | re-derived | tier | source | verdict |
|---|---|---|---|---|---|---|
| 88 | touched sources | 381 | 381 | out | `m2_verdicts.csv` | VERIFIED |
| 89 | IDENTIFIED | 104 | 104 | out | `verdict` tally | VERIFIED |
| 90 | PLAUSIBLE-CLASS | 123 | 123 | out | tally | VERIFIED |
| 91 | ARTIFACT | 153 | 153 | out | tally | VERIFIED |
| 92 | GENUINELY-UNEXPLAINED | 1 | 1 | out | tally | VERIFIED |

### 2g. Faint-end validation of the presence metric (new in M5-writeup)

Produced by [`scripts/m5w_faint_validation.py`](scripts/m5w_faint_validation.py) →
[`out/m5w_faint_validation.csv`](out/m5w_faint_validation.csv) +
[`out/m5w_faint_validation.json`](out/m5w_faint_validation.json). Seed 20260818; one anonymous
POST to the DR2 upper-limit service; no account, nothing submitted.

| # | number | value | source | verdict |
|---|---|---|---|---|
| 93 | steady flux-matched controls | 60 | `m5w_faint_validation.csv` | NEW |
| 94 | control selection band, eRASS1 flux | 1.86 × 10⁻¹⁴ – 1.65 × 10⁻¹³ | 10th–90th percentile of the 107 faders | NEW |
| 95 | control selection band, DET_LIKE_0 | 30.9 – 82.0 | 10th–90th percentile of the 107 faders | NEW |
| 96 | control presence range | 2.03 – 3.78 (median 2.60) | `m5w_faint_validation.csv` | NEW |
| 97 | controls falling below the *P* = 1.5 cut | **0 / 60** | `m5w_faint_validation.csv` | NEW |
| 98 | fader presence maximum | 1.49 | `m2_vanished_forensics.csv` | VERIFIED |
| 99 | populations disjoint | yes (1.49 < 2.03) | derived | NEW |
| 100 | false-positive rate, 95% one-sided | < 4.9% | 1 − 0.05^(1/60) | NEW |
| 101 | implied maximum contaminants of the 107 | fewer than 6 | 0.049 × 107 | NEW |

---

## 3. Externally-sourced values — checked against their actual sources

These are not re-derivable from this repo. Each was checked against the source named, in the
M5-writeup prior-art sweep; the verdict column records what the source actually says. Only the
rows marked **used** appear in the draft.

| value | verdict | used |
|---|---|---|
| RNAAS length limit | **VERIFIED**: "1,500 words or fewer" — <https://journals.aas.org/research-notes/> | used |
| RNAAS figure/table limit | **VERIFIED**: "no more than a single figure or table (but not both)" | used |
| RNAAS abstract requirement | **VERIFIED**: required since 2020-05-01 | used |
| RNAAS peer-review status | **VERIFIED**: "non-peer reviewed", "moderated but not edited" | used |
| eROSITA DR2 / eRASS:3 release paper | **VERIFIED**: arXiv:2607.27772 is the DR2 release paper. Ramos-Ceja, M. E., Lamer, G., Salvato, M., et al. 2026. Journal ref **A&A 712, A171** taken from <https://erosita.mpe.mpg.de/publications/>; the arXiv page carries no journal-ref, so ⚠ **confirm against ADS before submission** | used |
| DR2 release date 2026-07-31 | **VERIFIED** — <https://erosita.mpe.mpg.de/dr2/> | used |
| DR2 §5.1 unmatched fractions | **VERIFIED verbatim**: "about 21% … 3.5% for DET_LIKE>10 and 0.15% for DET_LIKE>50" (Fig. 10 caption) | used |
| DR2 §5.1 12.6% spurious + 8.4% variability split | **UNSOURCED** — not in §5.1; see §1.5 | **dropped** |
| DR2 §3.2.5 erbox dropout mechanism | **VERIFIED** as a mechanism named by the release paper | used (mechanism only; the "~200 sources" figure is not quoted) |
| DR2 spurious fraction ~14% at DET_LIKE_0 = 6 | **VERIFIED** — release paper §4; Merloni et al. 2024 give ~14% at DET_LIKE_0 ≥ 6 from simulations | used |
| DR2 upper-limit server spectral assumption Γ = 2.0, *N*_H = 3 × 10²⁰ cm⁻² | **VERIFIED** — <https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/UpperLimitServer_dr2/> | used |
| upper-limit-server citation requirement | **VERIFIED verbatim**: "We kindly request to cite Tubín-Arenas et al. (2024) and Ramos-Ceja et al. (2026)" — both are cited | used |
| upper-limit-server method paper | **VERIFIED**: Tubín-Arenas, D., Krumpe, M., Lamer, G., et al. 2024, **A&A 682, A35** (arXiv:2401.17305). Note the accent: Tubín-Arenas | used |
| eROSITA DR1 catalogue | **VERIFIED**: Merloni, A., et al. 2024, **A&A 682, A34** (arXiv:2401.17274) | used |
| Gaia DR3 | **VERIFIED**: Gaia Collaboration, Vallenari, A., Brown, A. G. A., et al. 2023, **A&A 674, A1** | used |
| eROSITA telescope | **VERIFIED**: Predehl, P., et al. 2021, **A&A 647, A1** | not needed in a 1,500-word note |
| survey PSF HEW ≈ 26–30″ | not re-checked in this pass | **dropped** — the draft says "the ~40″ PSF scale" as the geometric criterion actually applied, not a HEW value |
| Boller et al. intra-eRASS1 variability | **CORRECTED**: it is **2025**, A&A 700, A61 (arXiv:2401.17280 is the 2024 preprint). Measures ~4 h eROday-cadence variability of 128,669 sources; no inter-survey work | used, as 2025 |
| eRO-ExTra | **VERIFIED**: Grotova et al. 2025, **A&A 693, A62** (arXiv:2501.04208). 304 extragalactic non-AGN transients, **eRASS1↔eRASS2 only** | used |
| MKM Galactic transients | **VERIFIED and expanded**: Maan, Katira & Mooley 2025, **MNRAS staf1752** (arXiv:2510.12982); VizieR J/MNRAS/544/885. Covers 2RXS↔eRASS1 over ~30 yr, and its "true transients" *appear* in eRASS1 — the opposite direction to this census | used |
| eRASS1_HMXB_LMC VAC | **VERIFIED**: Kaltenbrunner, D., Maitra, C., Haberl, F., et al. 2026, **A&A 707, A225** (arXiv:2602.08152). Uses eRASS1–4 consortium products, OGLE light curves directly, and a Gaia **eDR3** CMD screen | companion note only |
| OGLE-IV survey | **VERIFIED**: Udalski, Szymański & Szymański 2015, **Acta Astron. 65, 1** | companion note only |
| XROM | **VERIFIED**: Udalski 2008, **Acta Astron. 58, 187**; ⚠ the XROM page asks to be contacted before its photometry is used in a publication — **not done** | companion note only, flagged |
| OGLE-IV interruption start 2020-03-13 | **NOT CITABLE as written** — measured by us from the XROM CAL 83 series; the citable survey-level halt is **2020 March 15** (Mróz et al., arXiv:2507.13794) | companion note, reworded to "measured" |
| OGLE-IV resumption 2022-08-16 | **UNSOURCED in the published record** — the literature says only "2022 August" (Mróz et al., arXiv:2410.06251) | companion note, reworded to "measured" |
| VASCO (optical vanishing-sources framing) | **VERIFIED**: Villarroel et al. 2020, **AJ 159, 8** | not used (X-ray note; no framing borrowed) |

---

## 4. Numbers that do NOT go in the draft

Per the mission rule — anything that cannot be re-derived does not enter the draft.

| number | why it is excluded |
|---|---|
| eRASS:3 span "556 days" | internally inconsistent with the quoted dates (§1.4); the draft gives the epoch range only |
| "107 (+35/−12)" | superseded by the re-derived +17/−8 (§1.1) |
| "~12.6% spurious + ~8.4% variability/Poisson" | UNSOURCED; not in the release paper's §5.1 (§1.5) |
| "steady calibrators are all ≫1" | one of 25 is degenerate (§1.2). The draft does not use the 25-source calibration at all — the new 60-source flux-matched control (§1.6) supersedes it |
| `fade_frac` as a fade diagnostic | re-derivation shows it barely separates the populations (fader median 1.25 vs steady 1.13); only `presence` discriminates, and the draft uses only `presence` |
| "nearest XROM ≥50′", "nearest LMC HMXB ≥13′" | rounded the wrong way; the companion note uses 49.8′ / 12.9′ |
| LMC HMXB donor G 12.68–17.00 / median 14.85 | not re-derived in the automated pass (#87); not needed |
| survey PSF HEW "26–30″" | not re-checked; the draft states the 40″ geometric criterion actually applied instead |
| any amplitude for any fader | the stacked ratio compresses fades to ≳1/3 and the epoch-space reconstruction has an unverifiable containment assumption; the draft makes no amplitude claim |
| M2 §2.5's Be/XRB readings of J055329.9-663938 and J054656.6-653401 | withdrawn by M4 §1.5 on the counterpart evidence |
| everything about **3eRASS J094452.8-711152** | fenced: Matthew's ToO gate. It is a *riser*, so it does not belong in a fader census in any case; the draft does not mention it, name it, or give any of its numbers |
| the M2 shortlist objects and their per-object dossiers | the note is a population result; naming individual unconfirmed candidates would invite follow-up on objects that have had none |
| "first" / priority claims of any kind | none is made anywhere in the draft; the prior-art position is stated in [`M5-writeup.md`](M5-writeup.md) §4 and reflected in the draft's related-work paragraph |

---

## 5. How to reproduce

```
cd erosita-dr2
.venv/Scripts/python.exe scripts/m5w_faint_validation.py  # -> out/m5w_faint_validation.{csv,json}
.venv/Scripts/python.exe scripts/m5w_audit.py             # -> out/m5w_audit.csv, 107 rows
.venv/Scripts/python.exe scripts/m5w_figure.py            # -> out/m5w_vanished_census.{png,pdf}
```

`m5w_faint_validation.py` caches its server response in `out/m5w_faint_validation.csv` and
reuses it on re-runs, so the DR2 upper-limit service is queried exactly once.
`m5w_audit.py` exits non-zero on nothing — it is a report, not a gate — but every
`CORRECTED` row it prints is a claim in M1–M4 that this milestone has superseded.
