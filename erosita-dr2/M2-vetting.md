# M2 — vetting the first-sweep candidates: verdicts, vanished-source forensics, shortlist

*2026-08-14. Scripts: [`scripts/m2_download_counterparts.py`](scripts/m2_download_counterparts.py),
[`scripts/m2_extract_counterparts.py`](scripts/m2_extract_counterparts.py),
[`scripts/m2_archival_xray.py`](scripts/m2_archival_xray.py),
[`scripts/m2_extra_xmatch.py`](scripts/m2_extra_xmatch.py),
[`scripts/m2_vanished_forensics.py`](scripts/m2_vanished_forensics.py),
[`scripts/m2_upper_limits.py`](scripts/m2_upper_limits.py),
[`scripts/m2_asassn.py`](scripts/m2_asassn.py), [`scripts/m2_verdicts.py`](scripts/m2_verdicts.py).
Outputs in [`out/`](out/). Numbers computed by these scripts from local catalogs or queried
services are marked **[computed]**; external claims carry a source URL. Negative results are
results. No accounts were created; nothing was reported anywhere.*

---

## 1. Method — what every candidate was tested against

Every **touched** candidate (the 140 M1 candidates + the full 261-source vanished census = **381
distinct objects** [computed]) went through:

1. **NWAY counterpart catalogs** (DR2-detected candidates): all six released variants
   `eRASSc3_{Main,Hard}_{LS10,GDR3,CW2020}_Public_27Jul2026` downloaded from
   [Catalogues_dr2/RamosM_DR2](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/)
   (2.75 GB total, sizes verified against Content-Length [computed]) plus `eRASS3_Hard_v1.2.fits`.
   Per candidate: `NWAY_p_any`/`p_i`/`match_flag` + counterpart photometry from each variant, and
   Hard-catalog (2.3–5 keV) membership by 15″ match. Coverage of the 120 DR2-detected candidates:
   GDR3 117, CW2020 119, LS10 62 (footprint-limited), Hard-catalog members 79 [computed].
   *File defect found:* `eRASSc3_Main_GDR3` carries the column `GDR3_source_id` **twice**
   (fields 62 and 88; the Hard variant has `GDR3_designation` at the second slot), which breaks
   numpy record parsing — worked around by renaming the second occurrence in the in-memory header
   ([`m2_extract_counterparts.py`](scripts/m2_extract_counterparts.py)). NWAY secondary rows
   (`match_flag=2`) exist for 7 candidates; best row kept, count recorded.
2. **Archival X-ray state**, one anonymous CDS X-Match call per catalog
   (http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync, 2026-08-14) against 2RXS
   ([J/A+A/588/A103/cat2rxs](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/588/A103), r=40″),
   XMMSL3 clean ([IX/71/xmmsl3c](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=IX/71), r=20″),
   Chandra CSC 2.1 ([IX/70/csc21mas](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=IX/70), r=15″),
   Swift 2SXPS ([IX/58/2sxps](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=IX/58), r=15″),
   CatWISE2020 ([II/365/catwise](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=II/365), r=10″),
   Gaia DR3 variability ([I/358/varisum + vclassre](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=I/358), r=10″);
   plus a TAP upload join at HEASARC ([xamin/vo/tap](https://heasarc.gsfc.nasa.gov/xamin/vo/tap),
   table `xmmssc`, r=15″ — the service now returns **5XMM-era** names [computed 2026-08-14], i.e.
   the same catalog generation the DR2 paper checks against). Follow-ups: SRG/ART-XC all-sky
   catalog ([J/A+A/687/A183/catalog](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/A+A/687/A183),
   updated 18-Jul-2025, r=30″) and the eRASS1 Galactic-transient catalog of Maan, Katira & Mooley
   ([J/MNRAS/544/885/ero-g-t](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/MNRAS/544/885), r=30″).
   Result: **185/381 touched sources have ≥1 prior/independent X-ray catalog entry; ART-XC matches 27;
   MKM flags 9** [computed] → `out/m2_archival_xray.csv`.
3. **DR2 upper-limit server** at every vanished position + 25 steady calibration pairs — §3.
4. **Optical time domain**: ASAS-SN Sky Patrol v2 (public, account-free;
   https://asas-sn.osu.edu/, client [pyasassn](http://asas-sn.ifa.hawaii.edu/skypatrol/)) cone
   searches (r=15″) with light-curve download at 12 priority positions
   (`out/m2_asassn_summary.csv`); Gaia DR3 variability flags + CatWISE W1−W2 colors for all 381
   via the X-Match sweep. ZTF was not used (these are southern targets); ATLAS forced photometry
   was skipped (needs an account — hard rule).
5. **Already-reported checks**: TNS public cone searches (https://www.wis-tns.org/search,
   r=60″, no account) at 6 priority positions — **all six returned zero transients** [checked
   2026-08-14]; web searches for candidate designations (eRASSU/eRASSt/SRGe/SRGt/1eRASS variants)
   and ATel/paper trails; SIMBAD 30″ cones for the two headline unidentified objects (both empty).
6. **Morphology**: Legacy Surveys DR10 viewer cutout
   (https://www.legacysurvey.org/viewer/cutout.jpg?ra=…&dec=…&layer=ls-dr10) inspected for the
   TDE-like fader (the other two headline objects fall outside LS10 coverage).

Verdict grammar (per the M2 brief): **IDENTIFIED** (as what, with source) /
**PLAUSIBLE-CLASS** (best class + evidence + what would confirm) / **GENUINELY-UNEXPLAINED**
(which checks it survived) / **ARTIFACT** (which systematic). Deliverable:
[`out/m2_verdicts.csv`](out/m2_verdicts.csv) — 381 rows = all m1_candidates columns + verdict
columns (the 241 vanished-census sources beyond M1's twenty carry `cand_set=vanished_full` and
were scored on forensics + archival evidence; SIMBAD/Gaia per-object columns exist only for the
140 M1 rows).

**Verdict counts** [computed]:

| set | IDENTIFIED | PLAUSIBLE-CLASS | GENUINELY-UNEXPLAINED | ARTIFACT | total |
|---|---|---|---|---|---|
| pair (top 100 ranked) | 85 | 14 | **1** | 0 | 100 |
| vanished (M1 top-20) | 2 | 4 | 0 | 14 | 20 |
| new_bright (top 20) | 17 | 3 | 0 | 0 | 20 |
| vanished_full (rest of 261) | 0 | 102 | 0 | 139 | 241 |
| **all touched** | **104** | **123** | **1** | **153** | **381** |

---

## 2. Priority dossiers

### 2.1 3eRASS J094452.8-711152 — GENUINELY-UNEXPLAINED (shortlist #1)

×57 riser (epoch-space conservative, z=43 [computed, M1]), RA/Dec 146.22033 −71.19802,
l,b = 288.98, −13.57. The only candidate that survived **every** check:

- **No counterpart**: NWAY `p_any` = 0.0000 (GDR3) and 4×10⁻⁶ (CW2020) [computed from the
  released counterpart catalogs]; nearest Gaia object 10.2″ away (~21× the 0.48″ POS_ERR);
  outside LS10 footprint; SIMBAD 30″ cone empty [2026-08-14]; nearest CatWISE source 5.2″
  (W1=16.7, W1−W2=0.26, stellar colors) — rejected by NWAY.
- **No prior X-ray**: absent from 2RXS, XMMSL3, CSC 2.1, 2SXPS, 5XMM-era xmmssc [computed];
  absent from ART-XC (4–12 keV, surveys 1–8) [computed].
- **Not reported**: TNS 60″ empty; no literature under any plausible designation (web searches
  2026-08-14).
- **What it is doing**: eRASS1 DET_LIKE 25 → eRASS:3 stack DET_LIKE 9401 at 1.71 ct/s; and it is
  in the **Hard catalog** (DET_LIKE_3 = 197, `eRASS3_Hard_v1.2`) [computed] — a hard/absorbed
  spectrum. The ASAS-SN source at this position is the 10.2″ star (sep computed from Sky Patrol
  master-list coordinates) — an unrelated blend.

An eRASS2/3-era transient or strong riser, X-ray-loud, hard, with **no optical/IR counterpart to
W1≈17, G≈21**. Candidate natures: obscured X-ray binary / very-faint X-ray transient, magnetar
outburst, heavily absorbed CV; an extragalactic interpretation needs the counterpart to be
fainter than any AGN of this X-ray flux would normally be. **Flagged for Matthew — worth an
external follow-up proposal or a note; nothing has been reported by us.**

### 2.2 3eRASS J155100.8-453347 — PLAUSIBLE-CLASS: M-dwarf superflare candidate (shortlist #2)

New-bright: 1.38 ct/s stacked, implied rise ≥×49 [M1], **hard-detected** (DET_LIKE_3=70
[computed]). Gaia DR3 star at 1.95″: G=17.75, plx = 10.99±0.13 mas (91 pc), M_G≈13.0 +
CatWISE W1−W2=0.10 → mid-M dwarf. NWAY is split: `p_any` 0.07 (GDR3) vs 0.71 (CW2020)
[computed] — the M dwarf is not a confident association. If it is the source, the stack-averaged
Lx ≈ 1×10³⁰ erg s⁻¹ over 556 days — flare-dominated activity at the extreme end for an M dwarf
(quiescent M-dwarf Lx is orders lower; UNSOURCED as a general statement). Gaia's own G-band
range 17.67–17.84 caught no flare [computed, I/358]. No prior X-ray, TNS empty, SIMBAD 30″
empty, no literature. **Confirm**: optical spectroscopy (activity/youth indicators) and an X-ray
re-observation; if the M dwarf is rejected, this object escalates.

### 2.3 3eRASS J060622.5-624814 — PLAUSIBLE-CLASS: TDE-like fader, host unconfirmed (shortlist #3)

Epoch fade ≥×18 (2σ conservative) [M1], POS_ERR 2.9″. The M1 "G=20.6 galaxy" story weakened
under NWAY: the SIMBAD galaxy WISE J060621.36-624826.5 is 14.4″ out; the actual LS10 counterpart
candidate is a **g=23.5 galaxy-class source ~7″ away with `p_any`=0.002** [computed] — a very
weak association. No CatWISE source, no archival X-ray, TNS empty. LS10 cutout (inspected):
faint field, no bright host at the X-ray position. Still the best TDE-like fader in the slice,
but the honest statement is: *an X-ray transient that switched off, on a position whose deepest
optical counterpart is g≈23.5 and unconfirmed*. **Confirm**: deep imaging/spectroscopy + a
sub-arcsec X-ray position (Chandra/XMM ToO would resolve it).

### 2.4 The 7 "optical-faint vanished" priority sources — mostly artifacts

The UL-server test (§3) settles them individually [all values computed]:

| source | DET_LIKE (eRASS1) | verdict | key numbers |
|---|---|---|---|
| 1eRASS J050558.2-680146 | 554 | ARTIFACT (indeterminate-halo) | 13 ct/s DR2 source 16.6″ away; UL presence 0.0 (insensitive) |
| 1eRASS J053323.7-645745 | 308 | ARTIFACT (extended) | LMC diffuse EXT_LIKE=136 at 28.6″; presence 2.19 — flux still there |
| 1eRASS J050338.2-304513 | 242 | **PLAUSIBLE: AGN deep low state** | see §2.5 |
| 1eRASS J054656.6-653401 | 240 | **PLAUSIBLE: faint LMC-direction fader** | presence 1.08 (blank); nearest bright neighbor 51.6″ — beyond PSF |
| 1eRASS J052524.1-655818 | 233 | ARTIFACT (confusion) | EXT_LIKE=42107 complex 45″; presence 7.86 — flux still there |
| 1eRASS J063020.5-674651 | 177 | ARTIFACT (extended) | LMC diffuse EXT_LIKE=106 at 32.1″; presence 2.52 |
| 1eRASS J051910.4-253443 | 157 | **PLAUSIBLE: flaring AGN now low** | see §2.5 |

The M1 top-20 vanished list (ranked by DET_LIKE) was, in hindsight, **selected for artifacts**:
the §3.2.5 erbox failure mode preferentially removes *bright* sources near other bright emission,
which is why 14/20 resolved to ARTIFACT while the astrophysical faders live further down the
likelihood range (§3).

### 2.5 Vanished sources that are (probably) real astrophysics

- **1eRASS J050338.2-304513** — AGN into a deep X-ray low state. CatWISE 0.46″ W1−W2=0.94 (AGN
  colors); Gaia DR3 classifier AGN p=0.93 [I/358/vclassre]; ASAS-SN master-list seed = MORX.
  Prior X-ray: 2RXS J050337.2-304501 (16.6″ — inside ROSAT positional errors; 43.5 cts, 1990-91)
  and 2SXPS (3.8″, 0.019 ct s⁻¹) → historically persistent at ~its eRASS1 flux (3.9×10⁻¹³);
  now **blank** in the eRASS:3 stack (UL presence 1.02). A changing-state/X-ray-collapse AGN
  candidate. TNS empty. (shortlist #4)
- **1eRASS J051910.4-253443** — flaring AGN (blazar?) now X-ray-low. XMMSL3 detection at 4.2″ with
  F(0.2–2)=1.3×10⁻¹² (i.e. previously bright); CatWISE W1−W2=0.82; Gaia classifier AGN 0.63;
  ASAS-SN light curve shows optical brightenings up to ~1.4 mag *within* the eRASS1–3 window;
  stack position now blank (presence 1.03). TNS empty. (shortlist #5)
- **1eRASS J024930.1-274958** (from the full census) — nuclear-transient candidate: GLADE/HyperLEDA
  galaxy 6.0″ from the X-ray position, ASAS-SN blend shows ~1 mag excursions, no prior X-ray,
  stack blank, TNS empty. Association unproven at eRASS1 position error. (shortlist #6)
- **1eRASS J055329.9-663938 / J054656.6-653401** — LMC-direction faders (DET_LIKE 166/240) with
  blank stack positions; Be/X-ray-binary outbursts in the LMC are the natural reading (cf. the
  known LMC Be/XRB transient population, e.g.
  [arXiv:2302.01804](https://arxiv.org/abs/2302.01804)); background AGN not excluded. OGLE light
  curves of the IR sources would decide.
- **1eRASS J034852.6-552534 = WTP 15abymdq** — IDENTIFIED: the eRASS1 source sits 1.0″ from the
  known MIT-WTP mid-infrared nuclear transient (z=0.0374; WTP sample, e.g.
  [arXiv:2503.10053](https://arxiv.org/abs/2503.10053) context) — an X-ray active phase at a
  known dusty nuclear transient, gone by the stack (though counts persist nearby — presence 5.2
  with a 21.6″ neighbor, so the fade amplitude is not clean).
- **1eRASS J131400.5-190157** — IDENTIFIED: already in the MKM eRASS1 Galactic-transient catalog
  ([J/MNRAS/544/885/ero-g-t](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/MNRAS/544/885);
  d=58 pc, L=2.1×10²⁹ erg s⁻¹) — a nearby-star flare; bright CatWISE star (W1=8.6) at 2.9″;
  stack blank (flare over).

### 2.6 Already-reported transients confirmed among the M1 headline rows

- **3eRASS J071521.8-191603 = SRGt J071522.1-191609** — eROSITA-discovered 2020 transient:
  discovery [ATel #13657](https://ui.adsabs.harvard.edu/abs/2020ATel13657....1G/abstract),
  optical counterpart [ATel #13669](https://ui.adsabs.harvard.edu/abs/2020ATel13669....1K/abstract),
  VLA radio [ATel #13716](https://www.astronomerstelegram.org/?read=13716). Our slice sees the decline.
- **3eRASS J123822.2-253210 = SRGt J123822.3-253206** — bright short-duration X-ray flare,
  [ATel #13416](https://www.astronomerstelegram.org/?read=13416); = SRGA J123821.5-253208
  (ART-XC, flagged new+unidentified [computed]); discussed as a fast X-ray transient with a radio
  counterpart ([arXiv:2407.07257](https://arxiv.org/abs/2407.07257)).
- **3eRASS J142139.6-295321 = eRASSt J142140-295321** — published TDE candidate (IMBH candidate;
  ATCA radio study [arXiv:2504.08426](https://arxiv.org/abs/2504.08426)).
- **3eRASS J234403.0-352639 = eRASSt J234402.9-352640** — published "luminous X-ray ignition"
  ([arXiv:2302.06989](https://arxiv.org/abs/2302.06989); radio outflow
  [MNRAS 528, 7123](https://doi.org/10.1093/mnras/stae362)).
- **3eRASS J045649.7-203747 = eRASSt J045650.3-203750** — published repeating partial-TDE
  candidate ([arXiv:2208.12452](https://arxiv.org/abs/2208.12452)).
- **3eRASS J090506.7-533020 = MAXI J0903-531** (Be/XRB; via ART-XC counterpart name [computed]),
  **3eRASS J115415.8-501801 = EP240309a / SRGA J115415.6-501801** (intermediate polar,
  [arXiv:2405.01996](https://arxiv.org/abs/2405.01996)), **3eRASS J144357.1-390839 = PKS 1440-389**
  (blazar, z=0.1385 via ART-XC [computed]), **1eRASS J011706.7-732648 → SMC X-1 field** (split
  detection of the piled-up HMXB; UL presence 95.5 [computed]).

Remaining pair/new_bright verdicts are in `out/m2_verdicts.csv`: the M1 SIMBAD identifications
held up (XRBs, CVs in outburst, novae, flare stars, Seyferts); 14 pair rows settle at
PLAUSIBLE-CLASS (7 parallax flare-star/CV candidates, 4 AGN by WISE/Gaia-classifier evidence,
1 obscured plane transient/YSO, 1 recurrent 1RXS source, 1 CV candidate at 4σ parallax).

---

## 3. Vanished-source forensics: the §3.2.5 split, quantified

**The paper's mechanism** ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772) §3.2.5):
significant sources missing from eRASS:3 are "typically located in the vicinity (~1′) of other
similarly bright sources and were filtered out during the erbox peak finding stage"; from a
5XMM-DR15 comparison the paper estimates **~200 significant sources** lost this way catalog-wide;
§5.3 tells users to inspect complex regions manually.

**Pass 1 — geometry** ([`m2_vanished_forensics.py`](scripts/m2_vanished_forensics.py), against the
local DR2 catalog): for each of the 261 vanished (DR1 clean, DET_LIKE_0 ≥ 30, no `UID_DR1`
counterpart [computed — reproduces M1's count]): nearest DR2 source of any kind, nearest
similarly-bright point source (stacked rate ≥ 0.5× the vanished eRASS1 rate) within 2′, nearest
extended source, 2′ source counts, DR1-epoch neighbors.

**Pass 2 — the upper-limit server** ([`m2_upper_limits.py`](scripts/m2_upper_limits.py)): one
POST to the DR2 UL service
([API](https://erosita.mpe.mpg.de/erodat/apis/#upper-limits); method:
[Tubín-Arenas et al. 2024](https://ui.adsabs.harvard.edu/abs/2024A%26A...682A..35T/abstract)),
band 024 = 0.2–2.3 keV, `DR2_eRASSc3`, at all 261 positions + **25 steady calibration pairs**
(|R−1|<0.05, z<1, 20σ). Two derived metrics per position:

- `presence` = UL_B/UL_S — ≫1 means real counts sit at the position (empirically: a persisting
  2.6×10⁻¹¹ source gives presence ~90; steady calibrators are all ≫1; blank sky gives ~1.0–1.3);
- `fade_frac` = UL_B/F1(eRASS1) — calibration median **1.13 ± 0.07** for unchanged sources
  [computed].

**The physics**: the eRASS:3 stack *contains* the eRASS1 photons (M1 §2), so even a source that
switched off right after eRASS1 leaves ~F1·t1/t3 ≈ 0.2–0.5·F1 of stack-averaged flux. A **blank**
UL position (presence ≈ 1) is therefore only possible if the source really faded — no neighbor
50″+ away can absorb its counts (survey PSF HEW ≈ 26–30″,
[arXiv:2607.27772](https://arxiv.org/abs/2607.27772)). Conversely presence ≫ 1 near the position
means the flux is still there and only the *catalog entry* vanished — the erbox/extended
mechanism.

**Refined classification (v2)** [computed → `out/m2_vanished_forensics.csv`]:

| class | n | meaning |
|---|---|---|
| ARTIFACT-CONFUSION | 85 | counts persist (presence>1.5) + similarly-bright neighbor ≤2′ (the §3.2.5 mode) |
| ARTIFACT-EXTENDED | 36 | counts persist + extended source ≤2′ (absorbed into diffuse/cluster model) |
| ARTIFACT-SPLIT/MOVED | 25 | a DR2 source ≤15″ exists — the `UID_DR1` cross-walk missed it |
| ARTIFACT-UNCLEAR-PERSIST | 2 | counts persist, no geometric partner found |
| CONFUSED-IDENTITY | 5 | blank position but a bright source within ~PSF (40″): eRASS1 identity itself suspect |
| INDETERMINATE-HALO | 1 | UL insensitive inside a bright-source halo |
| **FADE-CANDIDATE** | **107** | **position blank (presence ≤1.5), no PSF-scale confuser: the flux really left** |

So the honest split of the 261: **148 catalog artifacts (57%), 6 indeterminate (2%), 107
plausible real faders (41%)**. The geometric pass alone (M1's plan) would have called 248/261
artifacts — the UL server flipped 94 "confusion" cases whose neighbors are 50–120″ away but whose
positions are demonstrably blank. Threshold sensitivity: presence cut 1.5 (the blank population clusters at
1.0–1.3, clear artifacts at 2–95); PSF radius 40″. Both documented in the script. The cut is the
soft spot of the split: tightening it to 1.3 would reclassify 12 faders → artifact, loosening to
2.0 would reclassify 35 artifacts → fader [computed] — so the fader count is honestly
**107 (+35/−12)** under threshold choice, and per-object claims in §2.5 rest on presence values
far from the boundary.

**Who the 107 faders are** [computed, from the archival sweep]: 39 have AGN-like counterparts
(Gaia DR3 classifier AGN or W1−W2 ≥ 0.8) — high-amplitude AGN variability; 23 have bright stellar
counterparts (W1<15, flat W1−W2) — single-epoch flare stars; 25 lie in the LMC box (RA 60–105,
Dec −75…−60) — Be/XRB-outburst territory; 21 had a prior X-ray detection; only 3 are CatWISE-blank.
Median DET_LIKE 40; only 8 exceed 100 (the brightest real faders are §2.5's objects). This is a
population-level result of the W2 axis: **~0.09% of clean bright eRASS1 sources genuinely
switched off** by eRASS:3 (107/118,253 [computed]; the consortium's own §5.1 accounting predicts
~8.4% missing at *all* likelihoods from variability+Poisson — our DET_LIKE≥30 cut removes the
Poisson-dominated regime, so the numbers are consistent in kind).

**Artifact-rate accounting vs the paper**: our 148 artifacts are drawn from the clean point-source
DET_LIKE≥30 margin only; the paper's ~200 estimate covers the whole catalog at all likelihoods
and only the erbox mode. The two are compatible: we find the erbox mode dominates (85/148), with
extended-absorption (36) and cross-walk misses (25) as distinct sub-modes the paper does not
separate. **Practical DR2 lesson: a bright DR1 source with no DR2 counterpart is an artifact
first, astrophysics second — at DET_LIKE>100 the artifact fraction in our sample is 14/20.**

---

## 4. Shortlist — objects worth external follow-up or a note

Ranked; one honest sentence each on what the evidence actually supports.

1. **3eRASS J094452.8-711152** (GENUINELY-UNEXPLAINED) — a ×57, hard-spectrum X-ray riser with no
   optical/IR counterpart, no prior X-ray, no report anywhere: the evidence supports *a new,
   unreported, obscured X-ray transient or high-amplitude riser*, nature unknown — **flagged for
   Matthew; this is the one that merits a follow-up proposal or community note.**
2. **3eRASS J155100.8-453347** — evidence supports *a hard-detected new X-ray source whose most
   likely counterpart is a 91-pc M dwarf caught in extreme flaring activity*, but NWAY leaves the
   association at 7–71%, so "M-dwarf superflare" is a hypothesis, not a result.
3. **3eRASS J060622.5-624814** — evidence supports *a real X-ray switch-off at a position with at
   most a g≈23.5 galaxy candidate*: TDE-like, but the host association is too weak to claim a TDE.
4. **1eRASS J050338.2-304513** — evidence supports *an AGN with a 30-year X-ray record that has
   dropped below eRASS1 detectability in the stack*: a changing-state candidate worth a spectrum.
5. **1eRASS J051910.4-253443** — evidence supports *an AGN (possibly blazar) that flared optically
   during the eRASS window and has since gone X-ray-quiet*.
6. **1eRASS J024930.1-274958** — evidence supports *a vanished X-ray source 6″ from a GLADE galaxy
   with contemporaneous optical excursions*: a nuclear-transient candidate, association unproven.
7. **1eRASS J055329.9-663938 & J054656.6-653401** — evidence supports *real single-epoch X-ray
   transients toward the LMC*, most naturally Be/XRB outbursts; individually unremarkable, jointly
   part of the 25-source LMC fader group.
8. *(population)* the **107-source fade-candidate census** with its artifact accounting is itself
   the durable W2 product — reproducible, quantified, and not published elsewhere (M1 §4 novelty
   verdict unchanged).

Nothing was reported to TNS or anywhere else; item 1 (and only it) looks live enough to justify
external action, which is Matthew's call.

---

## 5. Recommended M3

1. **J094452.8-711152 decision package** (Matthew): assemble the one-pager (finder chart, DR1/DR2
   numbers, UL history, counterpart limits) for a possible ATel-style note or a Swift/XMM ToO
   request. We hold until instructed.
2. **X-ray re-observation check, cheap version**: the eRASS DR3 (H2 2028 per
   [erosita.mpe.mpg.de/erass](https://erosita.mpe.mpg.de/erass/)) will settle riser/fader
   persistence; meanwhile Swift 2SXPS-era archives are exhausted — a `swifttools` XRT products
   query (account-free) on shortlist items 1–5 could bound present-day states.
3. **LMC fader mini-study**: cross the 25 LMC-box faders with OGLE-IV and published Be/XRB lists —
   a self-contained note if a few are new outbursts.
4. **Classifier rebase (M1 recommendation #3) is now unblocked**: the counterpart-catalog ingest +
   dedup fix from this milestone is the feature layer; the 6 released eRASSc3 files are local.
5. **W4 (Gaia DR4 NSS join, 2026-12-02) unaffected** — ingest layer unchanged.

## Files

- `out/m2_verdicts.csv` — 381 verdict rows (140 M1 candidates + 241 vanished-census) [~260 KB]
- `out/m2_vanished_forensics.csv` — 261 rows: geometry + UL metrics + v1/v2 classes
- `out/m2_ul_calibration.csv` — 25 steady-pair UL calibration rows
- `out/m2_archival_xray.csv` — 381 rows × 9 catalogs archival sweep
- `out/m2_counterparts.csv` — 120 rows NWAY counterpart extraction (+Hard membership)
- `out/m2_new_bright_full.csv` — full 286-source new-bright census
- `out/m2_asassn_summary.csv` — ASAS-SN light-curve summaries at 12 positions
- `data/` (gitignored): +2.77 GB counterpart/Hard catalogs (7 files, listed in
  [`m2_download_counterparts.py`](scripts/m2_download_counterparts.py))
