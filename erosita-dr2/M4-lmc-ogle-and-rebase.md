# M4 — the LMC-fader × OGLE mini-study + the classifier-rebase M0 kill checks

*2026-08-16. Scripts: [`scripts/m4_lmc_ogle.py`](scripts/m4_lmc_ogle.py),
[`scripts/m4_reconciliation.py`](scripts/m4_reconciliation.py). Outputs in [`out/`](out/).
Numbers computed by these scripts from local catalogs or queried anonymous services are marked
**[computed]**; external claims carry a source URL or the mark UNSOURCED. Negative results are
results. No accounts created, nothing submitted anywhere, J0944 untouched (its decision package
stands as delivered in M3, gated on Matthew).*

---

## 1. Part A — the 25 LMC-box faders × OGLE (the M3-scoped design, executed)

### 1.1 Design and what the public archive can actually answer

**Sample**: the 25 FADE-CANDIDATE rows of [`out/m2_vanished_forensics.csv`](out/m2_vanished_forensics.csv)
inside the M2 LMC box (RA 60–105, Dec −75…−60; a 258 deg² box, of which the LMC stellar disc is
a small central part) [computed]. DET_LIKE_0 30–240, all with blank stack positions
(UL presence 1.00–1.47, M2 §3).

**Matching stack**, all account-free (M3 §3 feasibility, executed as scoped):

| catalog | contents | access route (checked 2026-08-16) |
|---|---|---|
| OGLE-IV OCVS, LMC | acep 148, cep 4,713, dsct 15,256, ecl(+ELL) 63,252, hb 439, rrlyr 41,471, t2cep 291 [computed from ident.dat] | https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/lmc/ (per-type `ident.dat` + `phot/I/*.dat`; collection page https://ogle.astrouw.edu.pl/main/collections.html) |
| OGLE-III OIII-CVS, LMC (classes OGLE-IV lacks) | lpv 91,995, dpv 137, rcb 23 [computed] | https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/ |
| XROM (real-time XRB monitoring) | 97 monitored X-ray binaries, roster with coordinates [computed from page] | https://ogle.astrouw.edu.pl/ogle4/xrom/xrom.html + https://ftp.astrouw.edu.pl/ogle/ogle4/xrom/ (per-object `phot.dat`) |
| OGLE-II Be-star candidates (Sabogal et al. 2005, MNRAS 361, 1055) | 2,446 LMC Be candidates, types 1–4 | VizieR TAP `J/MNRAS/361/1055/table1` (CDS X-Match was 502-down on 2026-08-16; TAP sync used instead) |
| eRASS1_HMXB_LMC v1.0 (Kaltenbrunner et al., DR1 VAC) | 53 known LMC HMXBs with eRASS1 detections | https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/ (KaltenbrunnerD_DR1, arXiv:2602.08152 per portal link) |

Total OCVS pool 217,725 variables [computed]. **Structural gaps found while executing** (these
bound what "no match" can mean): OGLE-IV OCVS has **no Be-star class and no LMC LPV class**
(LPVs are OGLE-III only, light curves 2001–2009); the only public OGLE Be list is OGLE-II
(central-bar footprint — the nearest catalogued Be candidate to *any* fader is 2.0° away
[computed], so that check is void-by-footprint, not negative); and there is no public
arbitrary-position OGLE-IV photometry (M3 §3). The XROM page asks to be contacted before its
photometry is used in a publication — noted; nothing is being published from it here.

**Match radius**: 3.44·√(POS_ERR² + 1″²) per fader (2-D 99% Rayleigh incl. 1″ systematic floor)
= 5.7–11.2″ [computed]; context recorded to 30″. **Chance-alignment control (house pattern)**:
each fader re-matched from 16 shifted positions (8 azimuths × 240″/480″), same radii →
[`out/m4_lmc_ogle_control.csv`](out/m4_lmc_ogle_control.csv).

### 1.2 Headline: zero matches, everywhere, at chance level

[computed → [`out/m4_lmc_ogle_matches.csv`](out/m4_lmc_ogle_matches.csv)]:

| catalog | faders matched (of 25) | expected by chance (control) |
|---|---|---|
| OCVS (all 10 classes, IV+III) | **0** | 0.19 (3 hits / 400 control positions) |
| XROM roster | **0** | 0.00 (0/400) |
| Sabogal Be candidates | **0** | 0.00 (0/400; footprint 2°+ away) |
| eRASS1_HMXB_LMC (53 known HMXBs) | **0** | 0.00 (0/400) |

The zeros are not a coverage artifact of the variable catalogs: the nearest OCVS variable of any
class sits 0.4–4.8′ from every fader [computed] — all 25 positions are inside OGLE-monitored
territory. The nearest monitored XROM object is ≥ 50′ and the nearest known LMC HMXB ≥ 13′ from
any fader [computed]. **None of the 25 LMC-box faders is a known X-ray binary, a monitored XRB,
or a catalogued OGLE variable.**

### 1.3 The Be-donor test: Gaia kills the Be/XRB reading for 24 of 25

A Be/XRB fade (disk-loss quiescence) requires a Be donor, and LMC Be donors are bright: the 53
donors in the eRASS1_HMXB_LMC VAC span **Gaia G 12.68–17.00 (median 14.85)** [computed from the
VAC]. So per fader we asked Gaia DR3 (ESA archive TAP, one anonymous sync query, 10″ cones)
whether *any* star inside the match radius could be a donor: G ≤ 17.5, BP−RP ≤ 0.7, parallax
consistent with zero at 3σ [computed → matches CSV, `be_donor_candidate`].

**Result: 1 of 25 faders has a Be-donor-capable star; 24 have none.** Per-object verdicts
(evidence columns in the CSV; CatWISE from the M2 archival sweep):

| # | fader (1eRASS) | DET_LIKE | counterpart evidence [computed] | reading |
|---|---|---|---|---|
| 1 | J054656.6-653401 | 240 | CatWISE 1.6″ W1=15.8 **W1−W2=0.89**; Gaia G=20.1 | background AGN (M2 §2.5's "Be/XRB natural reading" for this object is **withdrawn**) |
| 2 | J055329.9-663938 | 166 | W1−W2=0.45; Gaia G=20.9 red | AGN-leaning; Be excluded (no donor) — M2 reading withdrawn |
| 3 | J054351.5-654739 | 99 | W1−W2=0.60; G=20.9 | ambiguous, AGN-leaning |
| 4 | J055855.6-665204 | 81 | **W1−W2=0.81** | background AGN |
| 5 | J060317.3-675951 | 71 | W1−W2=−0.01 (5.7″); G=20.7 | ambiguous faint |
| 6 | J062127.7-671207 | 63 | CatWISE 1.4″ W1=16.8 flat; plx-star G=16.9 at 6.9″ edge | ambiguous |
| 7 | J060437.7-665131 | 61 | **W1−W2=1.18** | background AGN (33″ from #10 — two independent faders, sep ≫ combined error [computed]) |
| 8 | J055043.8-641628 | 59 | Gaia G=13.3, plx 1.756±0.011 (570 pc), Gaia-vari ECL 0.95, W1=11.5 | foreground star flare |
| 9 | J060134.1-615749 | 56 | W1−W2=0.51; G=20.8 | AGN-leaning (7° N of the LMC disc) |
| 10 | J060434.9-665101 | 53 | W1−W2=0.19; G=20.3 red | ambiguous faint |
| 11 | J062955.1-673115 | 51 | Gaia G=15.5, plx 2.653±0.024 (377 pc), Gaia-vari RS-CVn 0.46, W1=12.6 | foreground active star |
| 12 | J041933.5-682038 | 47 | **no Gaia within 10″**; CatWISE-only 4.4″ W1=16.2 flat | unidentified; optical-hostless |
| 13 | J055216.6-681015 | 47 | **Gaia G=16.85, BP−RP=−0.21, plx −0.02±0.07 at 2.9″**; PM (1.99, 1.33) mas/yr; W1−W2=0.49 | **the only blue-luminous-star candidate** — kinematically strained, see below |
| 14 | J051213.9-625407 | 45 | W1−W2=0.19; G=18.7 red | ambiguous |
| 15 | J063353.0-681544 | 45 | **W1−W2=1.03** | background AGN |
| 16 | J050746.0-620612 | 43 | W1−W2=0.78; Gaia-classifier AGN 0.31 | AGN-leaning |
| 17 | J062940.4-654602 | 43 | **W1−W2=1.01**; 2RXS at 29″ | recurrently variable AGN |
| 18 | J050724.6-635419 | 42 | W1−W2=0.77; G=18.7 | AGN-leaning |
| 19 | J064954.3-705132 | 36 | **no Gaia within 10″**; CatWISE-only W1=18.0 flat | unidentified; optical-hostless |
| 20 | J061803.5-681611 | 33 | **W1−W2=1.36** | background AGN |
| 21 | J061316.4-684004 | 33 | **W1−W2=1.19** | background AGN |
| 22 | J044343.1-652640 | 33 | **W1−W2=0.96**, Gaia-blank | obscured background AGN |
| 23 | J061641.2-720512 | 32 | **W1−W2=1.07** | background AGN |
| 24 | J055938.6-615349 | 31 | Gaia G=14.9, plx 2.785±0.017 (359 pc), Gaia-vari RS-CVn 0.51, W1=12.0, 2RXS at 15.8″ | foreground active star, recurrent |
| 25 | J064116.3-665547 | 30 | G=18.9 red at 0.7″; W2 unreliable | ambiguous |

Tally: **9 firm AGN-colored (W1−W2 ≥ 0.8) + 4 AGN-leaning + 3 foreground active stars
(parallax 5σ+, two with Gaia RS-CVn votes, one ECL) + 8 ambiguous/faint (2 of them
optical-hostless CatWISE-only) + 1 blue-star ambiguity (photometric Be-donor profile,
kinematically strained — below)** [computed + hand-read from the evidence columns; the CSV's
`auto_reading` is the mechanical draft, this table is the finalized read].

**The near-candidate, honestly framed — 1eRASS J055216.6-681015**: a DET_LIKE 47 eRASS1-only
X-ray source (0.019 ct/s, blank in the eRASS:3 stack, presence 1.12 [M2]) 2.9″ from a Gaia DR3
star that *photometrically* fits an OBe donor: G=16.85, BP−RP=−0.21, parallax 0 at 0.3σ →
M_G ≈ −1.6 at the LMC distance modulus 18.48 (Pietrzyński et al. 2019,
https://ui.adsabs.harvard.edu/abs/2019Natur.567..200P/abstract), with a modest WISE excess
(W1−W2 = 0.49). **But its kinematics argue against LMC membership**: μδ = 1.325 ± ~0.09 mas/yr
vs the LMC systemic μδ ≈ 0.3–0.4 (e.g. Gaia Collaboration/Luri et al. 2021,
https://ui.adsabs.harvard.edu/abs/2021A%26A...649A...7G/abstract) — a ~1 mas/yr residual that
at 50 kpc is ~230 km/s [computed], beyond any disc-rotation or plausible natal-kick velocity.
The zero-parallax + blue color is equally consistent with a Galactic **halo hot star (BHB/sdB
at ~10–20 kpc)**, for which the PM is unremarkable; an X-ray-emitting hot-subdwarf binary would
itself be interesting, but it is not a Be/XRB. The star is in **no** Be/XRB roster (XROM,
eRASS1_HMXB_LMC, Sabogal) and no OCVS class. Evidence supports: *a faded X-ray transient whose
only plausible luminous counterpart is a blue star of ambiguous distance — Be/XRB possible only
if the Gaia PM is wrong or the star is unbound; spectroscopy (Hα, radial velocity) decides.*
Nothing reported by us.

### 1.4 The structural finding: the eRASS fade window is optically dark in the public OGLE archive

Measured from the data, not assumed [computed →
[`out/m4_lmc_ogle_lightcurves.csv`](out/m4_lmc_ogle_lightcurves.csv)]:

- **The frozen OCVS collection light curves end at their release epochs**, mostly *before* the
  eRASS window: context RRLYR files end 2016-04-14 (HJD′ 7492.5); the heartbeat (hb) collection,
  the newest, ends 2020-03-10.
- **The live XROM series measures the OGLE-IV COVID interruption directly**: CAL 83's photometry
  (the XROM object nearest a fader, 50′) has its largest gap **2020-03-13 → 2022-08-16 (886
  days)**, then continues to 2026-05-25.
- The eROSITA fade window — eRASS2+3, 2020-06 → 2021-06, the epochs in which the 25 faders went
  dark — therefore lies **entirely inside the OGLE shutdown**. Even a perfect OCVS/XROM match
  could not have shown the Be-disk-loss light curve *during* the X-ray fade; the best possible
  test was "known Be/XRB or catalogued variable at the position, with pre-2020-03 and
  post-2022-08 states". That test ran; the answer is no.

This is a scoping law worth keeping: **for any eRASS1→eRASS:3 fade, contemporaneous public
optical monitoring from OGLE does not exist (COVID gap), and static OCVS light curves predate
the window** — future "optical behavior across the eRASS window" designs must lean on ASAS-SN
(all-sky, ran through 2020–21; used in M2) or ATLAS (account-gated), not OGLE.

### 1.5 Population verdict

**The Be-fade story does not hold.** Zero of 25 LMC-box faders is a known or catalogued Be/XRB,
and at most one position even hosts a blue luminous-star candidate — itself kinematically
disfavored as an LMC member (above). The LMC-box fader group decomposes into the *same*
demographic mix as the general fader census (M2 §3: 39/107 AGN-like, 23/107 stellar): here ~13
AGN(-leaning), 3 foreground active stars, 8 ambiguous, 1 blue-star ambiguity. **M2's "Be/XRB-
outburst territory" prior for the LMC box — including the §2.5 readings of J055329.9-663938 and
J054656.6-653401 — is tested and rejected**; the box was a positional grouping, not a population
(most members sit degrees outside the LMC stellar disc, and the two §2.5 objects have
AGN(-leaning) counterparts). There is no population-level Be-fade note in this data; the durable
outputs are the negative result, the scoping law of §1.4, and the J055216.6-681015 ambiguity as
a minor shortlist addendum.

---

## 2. Part B — classifier-rebase M0 kill checks against DR2 reality

*(against [`../IDEAS/erosita-source-classifier.md`](../IDEAS/erosita-source-classifier.md) §M0;
the BUILD decision stays with Matthew and the IDEAS process.)*

### 2.1 Kill check 1 — VAC successor inventory: what exists for DR2 today

Directory listing of
[Catalogues_dr2](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/) re-read
2026-08-16 + the DR2 paper ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772)); completes the
M1 §1 table:

| DR1 value-added product | DR2 successor (2026-08-16) |
|---|---|
| Merloni Main/Hard/Supp | **Yes**: Main v1.3 + Hard v1.2 (no Supp) |
| Salvato counterparts ×3 | **Yes, and upgraded**: `eRASSc3_{Main,Hard}_{LS10,GDR3,CW2020}` — and unlike DR1-era Salvato these **carry the classification inside**: `class_gal_exgal` ("negative values for stars, positive for extragalactic", [data model](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASSc3_Main_LS10_Public_27Jul2026.html)), `Class_STAREX` + `Exgal_prob_STAREX`, `class_jetted` (1=bzcat, 2=crates, 3=SIMBAD blazar), SIMBAD id/redshift columns, and Gaia DSC `GDR3_PQSO/PGal/Pstar` in the GDR3 variant [columns read from the local files]. The DR2 paper: ~88% of identified counterparts in the LS footprint are extragalactic ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772)) |
| HamStar coronal (Freund) | **None** (portal has no FreundS_DR2; no eRASS:3 coronal paper found, searches 2026-08-16) |
| Clusters (Bulbul/Kluge/Liu/Sanders) | **None** — DR2's 63,796 extended sources ship with no cluster identification/confirmation catalog |
| BlazEr1/BLAZE blazars | **None** (per-source `class_jetted` flags partially substitute, in-footprint) |
| Weber ULX ×3 | **None** |
| Kaltenbrunner LMC HMXB | **None** (DR1 VAC used in Part A) |
| Boller variability | **None** — DR2 is catalogue-only, no variability product (M1 kill-check verdict stands) |
| — | **New in DR2**: Brink SDSS-V CVs (587), Schwope new-eRASS1 CVs (rehosted) |

Two structural facts for the dossier plan: (a) **DR1 verdicts are inheritable** onto DR2 rows
through the consortium `UID_DR1` crosswalk for 742,056 / 1,975,540 = **37.6%** of DR2 sources
[computed, M1]; (b) **DR2 is reachable only as bulk FITS** — HEASARC TAP still serves
`erass1main/erass1hard/erassmastr` only, VizieR TAP has no eRASS:3 table, ESASky lists only
eRASS1/eFEDS catalogs [all checked 2026-08-16; HEASARC/VizieR by TAP-schema query, ESASky via
https://www.cosmos.esa.int/web/esdc/esasky-catalogues].

**Plain statement for the "reuse published verdicts" tier**: for DR2 today that tier is
*one product family* (the eRASSc3 counterpart catalogs, in-footprint Galactic/extragalactic +
blazar flags + Gaia DSC) plus two CV lists plus DR1 inheritance over 37.6% of rows. The dozen
single-class DR1 VACs have no DR2 successors.

### 2.2 Kill check 2 — value-of-reconciliation on DR2 (the plan's M0 check #3)

**Design** ([`scripts/m4_reconciliation.py`](scripts/m4_reconciliation.py), local files only):
2,000 random DR2 point sources (EXT_LIKE = 0, rng seed 20260816; the first 100 are the plan's
"~100 random sources" primary sample), joined on `DETUID` to all three Main counterpart
catalogs; `NWAY_match_flag`=1 rows are the primary counterpart, =2 rows count as alternatives.
Tiers: **T1** = the single best released catalog (eRASSc3-LS10) gives a confident counterpart
(p_any ≥ threshold) with a gal/exgal class → "trivially classified by one catalog";
**T2** = classified but contested (alternative counterpart, or a *different* confident GDR3
object, or a Gaia-DSC class conflict); **T3** = outside the LS10 file (no released class),
subdivided by whether Gaia DSC rescues a class; **T4** = in-footprint but unclassifiable
(p_any below threshold or class 0). All numbers **[computed →
`out/m4_reconciliation.csv`]**:

| tier at p_any ≥ 0.5 | primary n=100 | robustness n=2000 |
|---|---|---|
| T1 — single-catalog classified | 51.0% | 46.1% |
| T2 — classified but contested | 3.0% | 5.0% |
| T3 — outside LS10, Gaia DSC class only | 10.0% | 8.9% |
| T3 — outside LS10, nothing | 15.0% | 18.9% |
| T4 — in LS10, unclassifiable | 21.0% | 21.0% |
| **NOT trivially classified by one catalog** | **49.0%** | **53.9%** |

At the stricter p_any ≥ 0.8 the not-trivial fraction rises to 54.0% / 57.3%. Coverage: 75% /
72.1% of sampled sources appear in the LS10 counterpart file at all — i.e. **~28% of DR2 point
sources sit outside the released classification's footprint**, the same "quarter outside LS10"
the DR1 plan assumed. Disagreement anatomy (n=2000): ≥1 alternative counterpart in some variant
17.4%; confident LS10-vs-GDR3 counterparts that are *different objects* only 0.5%; LS10
gal/exgal sign vs Gaia DSC **class conflicts 4.3%**.

**Honesty about the faint tail**: the unclassified tiers are faint-dominated (T4 median
DET_LIKE 8.2, 69% below 10; T3-nothing median 8.9 [computed]), and at the DET_LIKE = 6 catalog
threshold ~14% of entries are expected spurious ([arXiv:2607.27772](https://arxiv.org/abs/2607.27772)
§4, M1) — part of the gap is genuinely unaddressable. The load-bearing number is therefore:
**among securely real sources (DET_LIKE ≥ 20), 40.2% (214/532) are still not trivially
classified** [computed].

**Kill-check verdict: the wedge survives, with a changed shape.** The plan's kill threshold was
"~everything trivially classified by one catalog" / "<~20% ambiguous-or-uncovered" — measured
reality is 49–54% not-trivial overall and 40% among secure sources, 2–2.5× above the survival
bar. But the *composition* matters: the gap is dominated by footprint absence (28%) and
low-confidence counterparts (21%), not by catalogs disagreeing with each other (5%) — so the
value is in **coverage + honest evidence translation**, much less in adjudicating conflicts.

### 2.3 Kill check 3 — prior-art re-sweep (has anyone shipped the layer since the plan?)

Checked 2026-08-16, all negative:

- **ESASky**: still eRASS1 + eFEDS overlays only; no DR2/eRASS:3 ingestion
  (https://www.cosmos.esa.int/web/esdc/esasky-catalogues).
- **MPE portal**: no new services since release day — the news feed carries only the 2026-07-31
  release item (https://erosita.mpe.mpg.de/dr2/news_dr2/); no per-source explorer or
  classification service; the only DR2 services are the catalog directory + the updated
  upper-limit server.
- **HEASARC / VizieR**: DR1-only tables (TAP schema queries [computed 2026-08-16]).
- **GitHub / HuggingFace / MCP**: web sweeps find no unified per-source eROSITA dossier or
  "what is this X-ray source" service. Nearest neighbors, none of which is the layer: DAXA
  (archive/data-processing tooling, https://github.com/DavidT3/DAXA), the UMLCAXS playground
  (Chandra-based unsupervised classification), SRGz (Russian-consortium eastern-hemisphere
  counterparts, not public-western, https://link.springer.com/article/10.1134/S1063773723070022).

The translation-layer gap the IDEAS plan identified is still open — and at DR2 it is *wider*,
because nobody (including the archives) has even ingested the catalog yet.

### 2.4 The memo: go / no-go / pivot

**Recommendation: PIVOT** — the plan's *original* wedge ("unify the dozen-plus scattered
value-added catalogs") is substantially dead at DR2, but its *access/translation* wedge is wider
than it was at DR1. The BUILD decision itself stays with Matthew and the IDEAS process.

- **What the kill checks killed.** The DR1 pitch assumed ~15 fragmented verdict catalogs needing
  unification. DR2 reality (§2.1): the consortium consolidated classification *into* the
  counterpart product (gal/exgal + STAREX prob + blazar flags + SIMBAD + Gaia DSC in one file
  family), and the single-class VACs simply have no DR2 successors. There is far less to unify,
  and the main thing to "reuse" is one catalog family. The reconciliation experiment (§2.2):
  the single-catalog answer covers 46–51% of point sources — the majority of the *in-footprint,
  confident-counterpart* population — and cross-catalog conflict is rare (0.5% different-object,
  4.3% class conflict), so the "reconcile disagreeing verdicts" pitch is thin.
- **What survived, measured.** **49–54% of DR2 point sources (40% even at DET_LIKE ≥ 20) have
  no trivial single-catalog class** (§2.2) — 2–2.5× above the plan's ~20% survival bar — driven
  by the out-of-LS10-footprint 28% (no released class at all, only partially rescued by Gaia
  DSC) and the in-footprint low-p_any tail (21%), plus classes the released columns cannot give
  at all: **no coronal/CV/XRB-level classes for DR2, and DR2's 63,796 extended sources ship
  with no cluster catalog whatsoever** (§2.1).
- **What got stronger.** Nobody — not HEASARC, not VizieR, not ESASky — has even ingested DR2
  (§2.3): the deepest all-sky X-ray catalog is reachable only as a 2.1 GB FITS download. An
  account-free position/name → dossier service over DR2 would today be **the only queryable
  interface to DR2 of any kind**, before any translation value is counted. The Gaia DR4 refresh
  catalyst (2026-12-02) is unchanged.
- **The pivot.** Rebase the plan from "reconciler of many catalogs" to: (1) host + serve DR2
  Main/Hard + eRASSc3 classification per source (the tier that exists); (2) inherit DR1 verdicts
  (HamStar, clusters, blazars, ULX, HMXB…) across the `UID_DR1` crosswalk — 37.6% of DR2 rows —
  with explicit "eRASS1-era verdict" provenance; (3) rule-based fallback (Canis Major loci) for
  the out-of-footprint remainder and the DSC-only cases; (4) surface disagreements and the
  unclassified honestly. That is a smaller, sharper project than the DR1 plan — mostly ingest +
  translation, still account-free end-to-end.
- **Kill condition going forward** unchanged: if MPE/ESASky ship a DR2 per-source explorer or
  TAP ingestion with classification, the access wedge collapses to translation-only; re-check
  before build.

---

## 3. Recommended M5

1. **Matthew's gate, unchanged**: the J0944 Swift ToO decision
   ([J0944-decision-package.md](J0944-decision-package.md) §9, DRAFT — his account, his call).
   Untouched by this milestone.
2. **Classifier rebase M1 (thin slice), if Matthew accepts the §2.4 pivot** via the IDEAS
   process: position/name → dossier CLI over the local DR2 + eRASSc3 + UID_DR1-inherited DR1
   verdicts; acceptance per the IDEAS plan M1 (traceable evidence lines, zero fabricated
   numbers).
3. **W4 (Gaia DR4 NSS × DR2, 2026-12-02) — on schedule**; ingest layer unchanged; this remains
   the calendar-fixed priority.
4. **Bookkeeping, small**: carry the M4 counterpart readings for the 25 LMC faders into any
   future verdict roll-up (M2's `m2_verdicts.csv` §2.5 LMC lines are superseded as noted in
   §1.5; M2 stays as the dated log).
5. **Optional external note (Matthew's call, not urgent)**: the §1.4 scoping law + the 0/25
   negative is RNAAS-sized, but its natural home is a paragraph in any eventual fader-census
   write-up rather than a standalone note.

## 4. Files

- `out/m4_lmc_ogle_matches.csv` — 25 faders × all match results + Gaia/CatWISE evidence +
  Be-donor test [computed]
- `out/m4_lmc_ogle_control.csv` — shifted-position chance-alignment control (per catalog and
  per OCVS class)
- `out/m4_lmc_ogle_lightcurves.csv` — context light-curve window statistics (OCVS + XROM CAL 83)
- `out/m4_reconciliation.csv` — 2,000-source reconciliation experiment rows (first 100 = the
  plan's primary sample)
- `data/ogle/` (gitignored): OCVS/XROM/Sabogal/Gaia caches; `data/eRASS1_HMXB_LMC_v1.0.fits.tgz`
