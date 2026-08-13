# Reference audit — every citation in the project, checked against the source documents

**Date:** 2026-08-13 · **Scope:** `exosat-rv/` only · **Method:** every citation was read against
the paper itself in `papers/text/*.txt` (extracted from `papers/pdf/*.pdf`). No citation was
verified against another citation in this repository. Where no local source exists, the
bibliographic detail was taken from the reference list of a *published* paper that cites it
(H26's own list, or Lazzoni/Ruffio/Oza/Kral's) and is labelled **corroborated (secondary)** —
that is weaker than VERIFIED and is called out as such.

**Coverage:** 316 citation-bearing lines across 49 files (all of `docs/paper/`, `CITATION.cff`,
`paper/joss/`, `README.md`, `SPEC.md`, `BUILD-PLAN.md`, `HANDOFF.md`, `NEXT-DIRECTIONS.md`,
`LESSONS.md`, `DATA-SOURCES.md`, all `M*-RESULTS.md`, `.zenodo.json`, `data/*.json`,
`src/exosat_rv/`, `scripts/`, `tests/`).

**Headline:** 54 distinct citation claims across 29 distinct works. **14 are wrong**, in 60+
places. Three source PDFs in `papers/` carry filenames that name the wrong first author, and
every one of those three wrong names has been copied into prose — and in two cases into Python
identifiers. Nothing in this file has been applied; it is a list of corrections for review.

---

## Ground truth established from `papers/`

Read directly off the title pages / arXiv stamps of the archived sources:

| File in `papers/` | What the document actually is |
|---|---|
| `hoy2026_nature_published` | Hoy, K., Zurlo, A., Peña R., P. A., Köhler, J., Desidera, S., Gratton, R., Lazzoni, C., Petrus, S., Rodler, F., Smoker, J., D'Orazi, V., Carleo, I., Giovannini, I. 2026, *Nature*, "Satellite Detected Around a Star's Substellar Companion" |
| `hoy2026_2607.05193v1` | Same authors, "Planetary-Mass Exosatellite Detected Around the Substellar Companion of a Star", arXiv:2607.05193v1 [astro-ph.EP], 6 Jul 2026 |
| `kohler2025_viper_2505.08315` | **J.** Köhler, M. Zechmeister, A. Hatzes, S. Chamarthi, E. Nagel, U. Seemann, et al., "viper: High-precision radial velocities from the optical to the infrared — Reaching 3 m/s in the K band of CRIRES+ with telluric modelling", A&A (ms. aa53919-25), arXiv:2505.08315v1. H26 [18] gives **A&A 698, 44 (2025)**, doi 10.1051/0004-6361/202553919 |
| `lazzoni2022_detectability_2207.07569` | Lazzoni, C., Desidera, S., Gratton, R., Zurlo, A., Mesa, D., Ray, S., "Detectability of satellites around directly imaged exoplanets and brown dwarfs", **MNRAS**. H26 [10]: **516(1), 391–409 (2022)**, doi 10.1093/mnras/stac2081 |
| `vanderburg2018_method_1805.01903` | Vanderburg, A., Rappaport, S. A., Mayo, A. W., "Detecting Exomoons via Doppler Monitoring of Directly Imaged Exoplanets", arXiv:1805.01903v2. H26 [12]: **AJ 156(5), 184 (2018)** |
| `vanderburg2021_hr8799_2110.14650` | Vanderburg, A. & Rodriguez, J. E., "First Doppler Limits on Binary Planets and Exomoons in the HR 8799 System", submitted to ApJL. H26 [15]: **922(1), L2 (2021)** |
| `ruffio2023_hr7672b_2301.04206` | Ruffio, J.-B., Horstman, K., Mawet, D., et al., "Detecting exomoons from radial velocity measurements of self-luminous planets: application to observations of HR 7672 B and future prospects", draft 8 Feb **2023**. H26 [14]: **AJ 165(3), 113 (2023)** |
| `horstman2024_gqlupb_2408.10299` | Horstman, K., Ruffio, J.-B., Batygin, K., Mawet, D., et al., "RV measurements of directly imaged brown dwarf GQ Lup B to search for exo-satellites", arXiv:2408.10299v1, 19 Aug 2024. Instrument: **Keck/KPIC** |
| `blunt2026_gravity_hd206893b_2511.20091` ⚠️ | **Q. Kral**, J. Wang, J. Kammerer, S. Lacour, M. Malin, T. Winterhalder, B. Charnay, C. Perrot, P. Huet, et al., "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", A&A, ©ESO **2025**, ms. dated 26 Nov 2025, arXiv:2511.20091. **S. Blunt is the 15th author** |
| `kpic2025_velocity_shift_limits_2505.09781` | **Kevin S. Hong**, Luke Finnerty, Michael P. Fitzgerald, "Velocity shift and SNR limits for high-resolution spectroscopy of hot Jupiters using Keck/KPIC", arXiv:2505.09781v1, 14 May 2025 |
| `martinez2020_ominous_fate_2008.13778` ⚠️ | **Alessandro A. Trani**, Adrian S. Hamers, Aaron Geller, Mario Spera, "The ominous fate of exomoons around hot Jupiters in the high-eccentricity migration scenario", **MNRAS**, arXiv:2008.13778v2. **No author named Martinez, Stone or Muñoz** |
| `tokadjian2023_pathways_survival_2302.04646` ⚠️ | **Valeri V. Makarov & Michael Efroimsky**, "Pathways of survival for exomoons and inner exoplanets", **A&A**, arXiv:2302.04646v4. **No author named Tokadjian or Piro** |
| `retrograde2025_massive_moons_2509.13263` | Yangjun Pu, Chenyang Li, Bohang Zhu, "Massive Retrograde Moons May Survive During Different Hot Jupiters' Migration Scenario", MNRAS, arXiv:2509.13263v1 |
| `oza2019_volcanic_moons_1908.10732` | Oza, A. V., Johnson, R. E., Lellouch, E., Schmidt, C., Schneider, N., et al., "Sodium and Potassium Signatures of Volcanic Satellites Orbiting Close-in Gas Giant Exoplanets", arXiv:1908.10732v1. H26 [3]: **ApJ 885, 168 (2019)** |

---

## (a) Every citation found, and its verdict

| # | Work as cited | Where it appears | Verdict |
|---|---|---|---|
| 1 | Hoy et al. 2026, *Nature*, "Satellite Detected Around a Star's Substellar Companion" | `draft.template.html:749`, `cd35-etatel-draft.html`, `methods-note.md:521`, `contrast-wall-note.md:397`, `sampler-reproducibility-note.md:107`, `paper.bib:1`, `paper.md`, `RELEASE-CHECKLIST.md:83`, `data/m12-fromraw.json:6` | **VERIFIED** — authors, title, venue and DOI `10.1038/s41586-026-10751-w` all match the published PDF |
| 2 | Hoy et al. 2026 preprint, "Planetary-Mass Exosatellite…", arXiv:2607.05193v1 | `draft.template.html:749`, `paper.bib:14`, `SPEC.md:6`, `DATA-SOURCES.md:118`, `data/m12-fromraw.json:5` | **VERIFIED** as the preprint title |
| 3 | Hoy et al. 2026 preprint title used with `Nature` as the venue | `CITATION.cff:50-56`, `README.md:7-9` | **WRONG (venue/title mismatch)** — (b)#8 |
| 4 | Köhler, J. et al. 2025, A&A 698, A44, viper | `CITATION.cff:57`, `paper.bib:52`, `methods-note.md:523`, `contrast-wall-note.md:399`, `SPEC.md:85`, `HANDOFF.md:479`, `M2-RESULTS.md:135` | **VERIFIED** — initial **J.**, A&A 698, 44 (2025), doi …202553919, arXiv:2505.08315 |
| 5 | "Köhler, J., et al. 2025, A&A, viper: velocity and IP estimator for CRIRES+" | `draft.template.html:750`, `cd35-etatel-draft.html` | **WRONG (title)** — (b)#5 |
| 6 | "Köhler et al. 2025 **Eq. 1**" (the ε_RV statistic) | `methods-note.md:214`, `M12-RESULTS.md:105`, `scripts/injection/score.py:3`, `scripts/cr2res/ab_score.py:4`, `scripts/cr2res/eq1_final.py:3` | **WRONG (equation number)** — (b)#6 |
| 7 | Köhler et al. 2025 **§2.2** (template recipe) and **§5.4** (cell-free / telluric wavelength reference) | `viper-runbook.md:7,142,163,173,192`, `M11-RESULTS.md:4,24,79`, `M12-RESULTS.md:161,196,639`, `HANDOFF.md:385,425,507`, `orders.py:114`, `M9-RESULTS.md:156` | **VERIFIED** — §2.2 is "Creation of telluric-free stellar templates", §5.4 is "RV precision using tellurics as the wavelength reference". The quoted sentences ("the situation becomes more complex when Doppler shifts are present… an alternative approach is required") appear verbatim at lines 399–403 of the extracted text |
| 8 | Köhler et al. 2025 **eq. 14** weighting `w = T_atm/ε²` | `M11-RESULTS.md:33`, `viper-runbook.md:192` | **VERIFIED** — viper Eq. (14) is `w_n(λ) = T_atm,n(λ)/ε_{S_star,n}(λ)²` |
| 9 | "Köhler et al. 2024" = the GQ Lup B null | `M5-RESULTS.md:73` | **WRONG, and known-wrong** — (b)#9 |
| 10 | Lazzoni, C. et al. 2022, **MNRAS** 516, 391 | `CITATION.cff:64`, `paper.bib:127`, `methods-note.md:525`, `contrast-wall-note.md:400`, `SPEC.md:93`, `satellites.py:41`, `survey.py:3` | **VERIFIED** |
| 11 | "Lazzoni, C., et al. 2022, **A&A**, on satellite detectability…" | `draft.template.html:751`, `cd35-etatel-draft.html` | **WRONG (journal)** — (b)#4 |
| 12 | Lazzoni §4.3.2 threshold `0.1·10^{0.2(K_p−13.5)}` km/s; eq. 2; Table 2 P = 0.999 astrometry / 0.996 RV, N_det 6.1 / 5.1, planet-like 0.08; sample of 38; CD-35 2722 B absent | `satellites.py:84,91,443`, `survey.py:6,14,36,93,105,111,159`, `M7-RESULTS.md:52,60,74,83,99,115,136,180`, `M10-RESULTS.md:21`, `gravity.py:12`, `README.md:217,220,310`, `data/m7-survey.json:732` | **VERIFIED** — every one of these is in the Lazzoni text (§4.3.2 line 972; Table 2 lines 1085–1098; "38 substellar companions" line 23). CD-35 2722 B genuinely does not appear anywhere in the paper |
| 13 | Vanderburg, Rappaport & Mayo 2018, AJ 156, 184 | `CITATION.cff:70`, `paper.bib:74`, `methods-note.md:528`, `contrast-wall-note.md:402`, `SPEC.md:81`, `satellites.py:44`, `HANDOFF.md:325` | **VERIFIED** |
| 14 | Vanderburg et al. 2018 **eq. 9** = `ΔRV ≈ F_spot · v sin i` | `satellites.py:249` | **VERIFIED** — eq. (9) at line 464 of the extracted text |
| 15 | Vanderburg et al. 2018 **§2.4** = "the false-positive taxonomy" | `CITATION.cff:73`, `satellites.py:42,242` | **IMPRECISE** — (d)#1 |
| 16 | Vanderburg et al. 2018 §2.4 spurious-RV amplitude (~100 m/s) | `M8-RESULTS.md:179` | **VERIFIED** — §2.4 is "Planetary Activity Signals"; Table 1 gives "Up to ∼100 m s⁻¹" |
| 17 | Vanderburg & Rodriguez 2021, ApJL 922, L2, HR 8799 | `paper.bib:88`, `methods-note.md:529`, `contrast-wall-note.md:403`, `SPEC.md:80`, `M7-RESULTS.md:27`, `HANDOFF.md:324` | **VERIFIED** |
| 18 | Ruffio et al. **2023**, AJ 165, 113, HR 7672 B | `paper.bib:101`, `methods-note.md:526`, `contrast-wall-note.md:401`, `SPEC.md:79`, `satellites.py:46`, `M7-RESULTS.md:26` | **VERIFIED** |
| 19 | "Ruffio et al. (**2022**) … forecast to be feasible with **CRIRES+**" | `draft.template.html:191`, `cd35-etatel-draft.html` | **WRONG (year + claim)** — (b)#3 |
| 20 | Ruffio et al. 2023 §4: ~13 M_Jup deuterium/brightness cliff | `satellites.py:46,123` | **VERIFIED** — "mass of the planet decreases below ∼13 M_Jup … due to the onset of deuterium burning", inside §4 |
| 21 | Ruffio et al. 2023 use Batygin & Morbidelli (2020) `q ∝ √M` | `satellites.py:455` | **VERIFIED** — Ruffio lines 813–819 |
| 22 | "how **Ruffio et al.** constrained HR 8799" | `NEXT-DIRECTIONS.md:89` | **AMBIGUOUS / probably conflated** — (d)#4 |
| 23 | Horstman et al. 2024, arXiv:2408.10299, GQ Lup B, Keck/KPIC, a null | `paper.bib:113`, `methods-note.md:522`, `contrast-wall-note.md:398`, `SPEC.md:75-77`, `M7-RESULTS.md:28,35`, `HANDOFF.md:320,486` | **VERIFIED** — 11 epochs, 400–1000 m/s, upper limits only; KPIC confirmed |
| 24 | Kral, Q. et al., "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", arXiv:2511.20091 | `CITATION.cff:77`, `paper.bib:143`, `methods-note.md:524`, `contrast-wall-note.md:404`, `README.md:311,314` | **VERIFIED** (first author Kral) |
| 25 | "**Blunt** et al. 2026" for the same paper | `SPEC.md:98`, `M7-RESULTS.md:163`, `M10-RESULTS.md:25,30,41,69,79,98,131`, `HANDOFF.md:206,224`, `gravity.py:4,13,15,20,43,50,125`, `_gravity_cmd.py:16` | **WRONG (first author)** — (b)#1 |
| 26 | Kral et al. **year** (2025 vs 2026) | 2025 in `methods-note.md:54,524,594,597`; 2026 in `CITATION.cff:81`, `paper.bib:150`, `README.md:311`, `SPEC.md:99`, `M7-RESULTS.md:164`, `M10-RESULTS.md:31` | **INCONSISTENT / UNVERIFIABLE** — (c)#5 |
| 27 | Kral eq. 6 scaling `M_moon ∝ T_moon^(−2/3)·d·M_pl^(2/3)`; "first astrometric exomoon search"; ~0.4 M_Jup at P ≈ 0.76 yr; feasibility "lower than Jupiter … down to less than Neptune"; AF Lep b and β Pic b the best short-term targets; K < 20 and contrast < 10⁵ cuts; HD 60584 b unconfirmed (Bonavita et al. 2022) | `M10-RESULTS.md:25,30-41,79,131`, `gravity.py:4-54`, `SPEC.md:99`, `README.md:311` | **VERIFIED** — every quoted phrase and number is in the Kral text (abstract; §5.1 lines 974–1010) |
| 28 | Kral "**section 6**" for the target selection | `gravity.py:50`, `M10-RESULTS.md:41` | **WRONG (section number)** — (b)#7 |
| 29 | "five viable targets, plus HD 206893 B" / "a **sixth** target, HD 60584 b" | `gravity.py:50-55`, `M10-RESULTS.md:41,131` | **WRONG (miscount)** — (d)#2 |
| 30 | Hong et al. 2025 (arXiv:2505.09781), Δv ≈ 30–60 km/s against 9 km/s resolution | `satellites.py:383,399` | **VERIFIED** — abstract gives "Δv_pl ∼ 30, 50, 60 km s⁻¹ … instrumental resolution of 9 km s⁻¹" |
| 31 | "**Horstman** et al. 2025" for arXiv:2505.09781 | `M8-RESULTS.md:77`, `M8-RESULTS.md:250` | **WRONG (author)** — (b)#2 |
| 32 | "Martinez, Stone & Muñoz 2020" / "Martinez et al. 2020" (arXiv:2008.13778) | `M8-RESULTS.md:201`, `README.md:244`, `closein.py:43` | **WRONG (authors)** — (b)#10 |
| 33 | The claim attached to it — moons do not survive high-eccentricity migration; massive moons prevent it | same lines | **VERIFIED against the paper** (Trani abstract). Only the names are wrong |
| 34 | "Tokadjian & Piro 2023 (A&A 672 A5, arXiv:2302.04646)" | `M8-RESULTS.md:206,228,247`, `closein.py:37`, `satellites.py:345,350,359,369`, `tests/test_satellites.py:147,156` | **WRONG (authors; volume/page unverifiable)** — (b)#11 |
| 35 | The claims attached to it — eq. 9 `n_p < 0.198 θ̇_p (1 − 1.03 e_p)^(3/2)`; "26 systems have any niche, 5 wider than 1 R_p"; "massive moons are more likely to survive" | same lines | **VERIFIED against the paper** — eq. (9) at line 327; "26 systems, with only 5 of them having a niche" at line 397; the conclusion is near-verbatim from the abstract |
| 36 | arXiv:2509.13263 (2025), disc migration, retrograde 5× more often, > 10 M_⊕ | `M8-RESULTS.md:203`, `closein.py:47` | **VERIFIED** (arXiv ID and both numbers). Cited anonymously — the authors are **Pu, Y., Li, C. & Zhu, B.** |
| 37 | Oza et al. 2019 (arXiv:1908.10732) | `satellites.py:49`, `M8-RESULTS.md:237` | **VERIFIED**; full citation is ApJ 885, 168 (2019) per H26 [3] |
| 38 | Wahhaj et al. 2011, ApJ 729, 139, arXiv:1101.2893, discovery of CD-35 2722 B; K = 12.01, H = 12.78 ± 0.12, J = 13.63 | `draft.template.html:754`, `paper.bib:19`, `config.py:62`, `satellites.py:107`, `survey.py:78`, `M5-RESULTS.md:139`, `HANDOFF.md:493`, `tests/test_feasibility.py:215` | **Corroborated (secondary)** — H26 [7] confirms authors, title, ApJ 729(2), 139 (2011), DOI and arXiv ID. **No local copy**, so the photometry is unchecked — (c)#1 |
| 39 | Dorn et al. 2023, A&A 671, A24, CRIRES+ | `paper.bib:35`, `paper.md:31` | **Corroborated (secondary)** — H26 [11] confirms every field. No local copy |
| 40 | Speagle, J. S. 2020, MNRAS 493, 3132, dynesty | `draft.template.html:753`, `methods-note.md:361,527`, `sampler-reproducibility-note.md:18`, `paper.bib:165`, `paper.md:37` | **UNVERIFIABLE** — no local copy, and no archived paper cites it — (c)#2 |
| 41 | "Peña, R., et al. 2025, A&A 706, 323, EMPEROR/reddemcee" | `draft.template.html:752`, `cd35-etatel-draft.html` | **WRONG on four counts** — (b)#12 |
| 42 | Domingos, Winter & Yokoyama 2006, MNRAS 373, 1227 | `satellites.py:48`, `config.py:201`, `feasibility.py:86,99`, `M0-RESULTS.md:75`, `M1-RESULTS.md:26,33`, `M7-RESULTS.md:119`, `HANDOFF.md:275,280`, `README.md:104`, `tests/test_feasibility.py:110` | **Corroborated (secondary)** — exact match in Lazzoni's reference list (line 1236). No local copy |
| 43 | Barnes & O'Brien 2002, ApJ 575, 1087 | `satellites.py:49`, `M8-RESULTS.md:49` | **Corroborated (secondary)** — exact match in Oza's reference list (line 1665). No local copy |
| 44 | Cassidy et al. 2009 | `satellites.py:49` | **Corroborated (secondary)** — cited five times in Oza's body text on exactly this topic. No identifier given in-repo, no local copy |
| 45 | Canup & Ward (2006), gas-starved disc `q ≈ 1e-4` | `satellites.py:454` | **Corroborated (secondary)** — Ruffio line 93 uses it for the same number; Ruffio's list gives Nature 441, 834 |
| 46 | Batygin & Morbidelli (2020) | `satellites.py:455` | **Corroborated (secondary)** — Ruffio's list gives ApJ 894, 143 |
| 47 | Inderbitzi et al. 2020 as H26's "reference [21]" | `satellites.py:461`, `M7-RESULTS.md:68` | **WRONG for the published version** — (b)#13 |
| 48 | Xuan et al. 2024, *Nature*, "The cool brown dwarf Gliese 229 B is a close binary", doi 10.1038/s41586-024-08064-x, P = 12.1 d | `config.py:218`, `M3-RESULTS.md:33`, `M5-RESULTS.md:102`, `viper-runbook.md:198` | **UNVERIFIABLE** — (c)#3 |
| 49 | Bonavita et al. 2022 (HD 60584 b unconfirmed) | `gravity.py:54`, `M10-RESULTS.md:131` | **Corroborated (secondary)** — Kral §5.1 attributes exactly this to Bonavita et al. 2022 |
| 50 | "Hoy et al.'s reference **[11]** is Lazzoni et al. 2022" | `README.md:205`, `SPEC.md:93`, `M7-RESULTS.md:6,24`, `satellites.py:42`, `survey.py:7`, `scripts/fetch_paper.py:4` | **WRONG for the published version** — (b)#14 |
| 51 | "**[32]** Vanderburg, Rappaport & Mayo 2018" | `M7-RESULTS.md:25` | **WRONG for the published version** — (b)#14 |
| 52 | H26 [13] Horstman, [14] Ruffio, [15] Vanderburg & Rodriguez | `M7-RESULTS.md:26-28` | **VERIFIED** — these three numbers are identical in both versions |
| 53 | Wahhaj et al. (2011)'s "31 ± 8 M_Jup" for the host | `scripts/m16_build_paper.py:113`, `scripts/m18_posteriors.py:77,134` | **UNVERIFIABLE** — (c)#1 |
| 54 | `paper.bib` note that "CITATION.cff and README misattribute this paper to Blunt et al." | `paper/joss/paper.bib:158-161` | **STALE** — both have since been fixed to Kral — (d)#5 |

---

## (b) Every WRONG citation, with the correction and every place it appears

### 1. "Blunt et al. 2026" → **Kral, Q., et al.** — 19 surviving sites

The VLTI/GRAVITY HD 206893 B exomoon search is first-authored by **Q. Kral**. S. Blunt is the
15th of ~90 authors. Fixed in `CITATION.cff`, `paper.bib`, `README.md` and the notes; **not**
fixed anywhere else.

- `SPEC.md:98` — "Blunt et al. 2026 ([arXiv:2511.20091], A&A) report tentative…"
- `M7-RESULTS.md:163` — "**Blunt et al. 2026, *Exomoon search with VLTI/GRAVITY…***"
- `M10-RESULTS.md:25, 30, 41, 69, 79, 98, 131` — seven separate mentions
- `HANDOFF.md:206, 224`
- `src/exosat_rv/archive/gravity.py:4, 13, 15, 20, 50` — prose; plus the **symbol name**
  `BLUNT_SHORTLIST` at `:43` and its use at `:125`
- `src/exosat_rv/_gravity_cmd.py:16` — **user-visible CLI output**:
  `"VLTI/GRAVITY holdings on Blunt et al. 2026's exomoon shortlist"`

**Correction:** "Kral et al." throughout; rename `BLUNT_SHORTLIST` → `KRAL_SHORTLIST`.

**Filename:** `papers/pdf/blunt2026_gravity_hd206893b_2511.20091.pdf` and
`papers/text/blunt2026_gravity_hd206893b.txt` **should be renamed** to `kral2026_…`. The
filename is the demonstrated proximate cause of this error — `gravity.py:5` cites the
*filename* as its source pointer, and `methods-note.md:597` already flags it as misleading
without renaming it.

### 2. "Horstman et al. 2025" → **Hong, K. S., Finnerty, L. & Fitzgerald, M. P. 2025**

arXiv:2505.09781 is "Velocity shift and SNR limits for high-resolution spectroscopy of hot
Jupiters using Keck/KPIC" by Hong, Finnerty & Fitzgerald. Already fixed in `satellites.py`.
Surviving:

- `M8-RESULTS.md:77` — "Horstman et al. 2025 ([arXiv:2505.09781])"
- `M8-RESULTS.md:250` — "Horstman et al. constrain the *detection* threshold…"

**Correction:** "Hong et al. 2025". The genuine **Horstman et al. 2024** (GQ Lup B,
arXiv:2408.10299) is a different paper cited elsewhere in the same repo — do not merge them.
(`src/exosat_rv/analysis/__pycache__/satellites.cpython-312.pyc` still contains the old string;
that is a stale build artifact, not a source file.)

### 3. "Ruffio et al. (2022) … forecast to be feasible with CRIRES+"

`docs/paper/draft.template.html:191-192` (and the generated `docs/paper/cd35-etatel-draft.html`):

> "were proposed by Vanderburg et al. (2018) and forecast to be feasible with CRIRES+ by
> Ruffio et al. (2022, in the framework of Lazzoni et al.)."

Two errors. **(i) Year:** the paper is 2023 (AJ 165, 113; draft dated 8 Feb 2023), and the repo
cites it as 2023 everywhere else. **(ii) Claim:** the string "CRIRES" **does not occur anywhere
in Ruffio et al. 2023**. Its forward-looking section is §4, "FUTURE EXOMOON SENSITIVITY OF
**TMT/MODHIS**". The CRIRES+-era forecast is Lazzoni et al. 2022's, which this sentence demotes
to a parenthetical.

**Correction:** e.g. "…applied to HR 7672 B with Keck/KPIC by Ruffio et al. (2023) and forecast
for the CRIRES+ era by Lazzoni et al. (2022)" — which is what `methods-note.md:51-54` and
`contrast-wall-note.md:43-45` already say correctly.

### 4. Lazzoni et al. 2022 given as **A&A**; it is **MNRAS**

- `docs/paper/draft.template.html:751` — "Lazzoni, C., et al. 2022, **A&A**, on satellite
  detectability around directly imaged companions."
- the same line in `docs/paper/cd35-etatel-draft.html`

**Correction:** "Lazzoni, C., Desidera, S., Gratton, R., Zurlo, A., Mesa, D., & Ray, S. 2022,
MNRAS 516, 391, *Detectability of satellites around directly imaged exoplanets and brown
dwarfs*." Every other file already says MNRAS — the draft is the only offender.

### 5. The viper reference in the draft carries the wrong title

`docs/paper/draft.template.html:750` (and the generated draft):

> "Köhler, J., et al. 2025, A&A, viper: velocity and IP estimator for CRIRES+."

"Velocity and IP EstimatoR" is the title of a **different** reference — H26 [17],
*Zechmeister, M., Köhler, J., & Chamarthi, S., "Viper: Velocity and IP EstimatoR"* (the software
entry). The A&A 2025 paper (H26 [18]) is "viper: High-precision radial velocities from the
optical to the infrared: Reaching 3 m/s in the K band of CRIRES+ with telluric modelling",
**A&A 698, A44**.

**Correction:** use the real title and add volume/page, or cite both entries separately if the
software is what is meant.

### 6. "Köhler et al. 2025 **Eq. 1**" → **Eq. (6)**

The ε_RV weighted across-order dispersion is **Köhler et al. 2025 Eq. (6)** (extracted text
lines 186–190). Köhler's **Eq. (1)** is the forward model
`S(x) = k·[T_cell(λ)·S_star(λ(v_star))] ⊗ IP(λ,x)` (line 114). The statistic is **H26's**
Eq. (1) — H26 writes "the corresponding final uncertainty is given by this equation from
Köhler et al. (2025)¹⁸" and numbers it (1) in their own paper.

- `docs/paper/methods-note.md:214-215` — "(Köhler et al. 2025, Eq. 1; adopted as Eq. 1 of H26)"
- `M12-RESULTS.md:105` — "Köhler et al. (2025) Eq. 1, reproduced as the paper's Eq. (1)"
- `scripts/injection/score.py:3` — "Kohler et al. 2025 Eq.(1), quoted as Eq.(1) in Hoy et al."
- `scripts/cr2res/ab_score.py:4` — "(Kohler Eq.1, computed on frame A)"
- `scripts/cr2res/eq1_final.py:3` — "Kohler Eq.1 = weighted dispersion of the per-order RVs"

**Correction:** "Köhler et al. 2025 Eq. 6, adopted as Eq. 1 of H26". Everywhere else in
`M12-RESULTS.md` "Eq. 1" means *H26's* Eq. 1 and is fine as-is. The script filename
`eq1_final.py` need not change; its docstring should.

### 7. Kral "section 6" → **section 5.1**

The GRAVITY+ target selection (K < 20 mag, contrast < 10⁵, five viable targets) is
**§5.1, "Target selection for GRAVITY+"**. **§6 is "Conclusions."**

- `src/exosat_rv/archive/gravity.py:50` — "Blunt et al. 2026 section 6's five viable…"
- `M10-RESULTS.md:41` — "Blunt et al. §6 cut their sample on K < 20 mag…"

### 8. `CITATION.cff` and `README.md` pair the **preprint title** with **Nature**

- `CITATION.cff:50-56` — title "Planetary-Mass Exosatellite Detected Around the Substellar
  Companion of a Star", `year: 2026`, notes "arXiv:2607.05193; **Nature**. The claim under test."
- `README.md:7-9` — the same preprint title, linked to both arXiv **and** the Nature article.

Neither is false about the arXiv record, but as written each asserts that the *Nature* paper
carries the preprint's title. It does not. Given that this exact confusion was one of today's
four fixes, both should be split the way `paper.bib` and `draft.template.html:749` now do it:
published title first, with an explicit "supersedes arXiv:2607.05193v1, «…»" note.

### 9. "Köhler et al. 2024" for the GQ Lup B null — a known-false citation still live

`M5-RESULTS.md:73` — "a published null on GQ Lup B (Köhler et al. 2024)". The paper is
**Horstman et al. 2024** (arXiv:2408.10299); Köhler is not an author on it at all. This is
documented as false in `HANDOFF.md:316-325`, `SPEC.md:75-77` and `M7-RESULTS.md:35`, but
`M5-RESULTS.md` carries no inline correction marker, so a reader landing there gets the wrong
citation with nothing to warn them.

**Correction:** if M-docs are frozen historical records, add an inline
`> **CORRECTED in M7:** …` note as that file does elsewhere; do not leave it bare.

### 10. "Martinez, Stone & Muñoz 2020" → **Trani, A. A., Hamers, A. S., Geller, A. & Spera, M. 2020**

arXiv:2008.13778 is "The ominous fate of exomoons around hot Jupiters in the high-eccentricity
migration scenario", MNRAS, by **Trani, Hamers, Geller & Spera**. No author named Martinez,
Stone or Muñoz appears on it.

- `M8-RESULTS.md:201` — "**Martinez, Stone & Muñoz 2020** ([arXiv:2008.13778])"
- `README.md:244` — "([Martinez et al. 2020](https://arxiv.org/abs/2008.13778))"
- `src/exosat_rv/analysis/closein.py:43` — "**Martinez, Stone & Munoz 2020** (arXiv:2008.13778)"

The *claim* attached to it is correct (Trani abstract: "massive exomoons are efficient at
preventing high-eccentricity migration … it is unlikely that the HJ formed can host exomoons").

**Filename:** `papers/{pdf,text}/martinez2020_ominous_fate*` should be renamed `trani2020_…`.

### 11. "Tokadjian & Piro 2023" → **Makarov, V. V. & Efroimsky, M. 2023**

arXiv:2302.04646 is "Pathways of survival for exomoons and inner exoplanets", A&A, by
**Makarov & Efroimsky** (both US Naval Observatory). No author named Tokadjian or Piro.

- `M8-RESULTS.md:206, 228, 247`
- `src/exosat_rv/analysis/closein.py:37`
- `src/exosat_rv/analysis/satellites.py:350, 359, 369` — the constant docstring and the
  `moon_can_synchronise_planet` docstring
- `tests/test_satellites.py:147, 156`
- Symbol name `TOKADJIAN_SPIN_RATIO` at `satellites.py:345`

Additionally `satellites.py:350` asserts "**A&A 672 A5**" — that volume/page cannot be verified
from the archived preprint and should be re-checked or dropped.

Every scientific claim drawn from it is correct (eq. 9, the 26/5 niche counts, "massive moons
are more likely to survive"). Only the names are invented.

**Filename:** `papers/{pdf,text}/tokadjian2023_pathways_survival*` → `makarov2023_…`.

### 12. The EMPEROR/reddemcee reference is wrong four ways

`docs/paper/draft.template.html:752` (and the generated draft):

> "Peña, R., et al. 2025, A&A 706, 323, EMPEROR/reddemcee."

From H26's own reference list, which is where this came from:

- **[37]** Peña R., P. A. & Jenkins, J. S.: "EMPEROR: I. Exoplanet MCMC parallel tempering for
  RV orbit retrieval." **A&A 704, 323 (2025)**, doi 10.1051/0004-6361/202554336, arXiv:2511.05331
- **[38]** Peña R., P. A. & Jenkins, J. S.: "Closing the evidence gap: reddemcee, a fast
  adaptive parallel tempering sampler — next-generation ladder adaptation and evidence
  estimators for parallel tempering." **A&A 706, 323 (2026)**, doi 10.1051/0004-6361/202556609

So: **(i)** the surname is **"Peña R."** with initials **P. A.** — "Peña, R." reads the "R." as
an initial and is wrong; **(ii)** it is a **two-author** paper, so "et al." is wrong — the
co-author is **Jenkins, J. S.**; **(iii)** **two distinct papers** are merged into one entry;
**(iv)** "A&A 706, 323" belongs to the **reddemcee** paper, which is **2026**, not 2025 — the
2025 EMPEROR paper is **A&A 704, 323**.

**Correction:** two entries —
`Peña R., P. A., & Jenkins, J. S. 2025, A&A 704, 323, "EMPEROR: I. Exoplanet MCMC parallel tempering for RV orbit retrieval"` and
`Peña R., P. A., & Jenkins, J. S. 2026, A&A 706, 323, "Closing the evidence gap: reddemcee…"`.

### 13. "H26's reference [21], Inderbitzi et al. 2020" — dropped from the published version

`src/exosat_rv/analysis/satellites.py:461` and `M7-RESULTS.md:68` attribute H26's
formation-channel argument to "its reference [21], Inderbitzi et al. 2020". That is true of
**arXiv v1 only**. In the published *Nature* version, **Inderbitzi does not appear in the
reference list at all** (searched for "Inderbitzi", "Szulágyi", "Cilibrasi" — no hits), and
**[21] is Anglada-Escudé, López-Morales & Chambers 2010**, "How Eccentric Orbital Solutions Can
Hide Planetary Systems in 2:1 Resonant Orbits".

Given the project's decision to cite the published version, this is a live error.

### 14. H26 reference numbers are the **preprint's**, and two of them changed

The reference list was renumbered between versions (v1: 37 entries; published: 47).

| Work | arXiv v1 | Published *Nature* |
|---|---|---|
| Lazzoni et al. 2022, detectability | **[11]** | **[10]** |
| Dorn et al. 2023, CRIRES+ | [12] | **[11]** |
| Vanderburg, Rappaport & Mayo 2018 | **[32]** | **[12]** |
| Horstman et al. 2024 | [13] | [13] |
| Ruffio et al. 2023 | [14] | [14] |
| Vanderburg & Rodriguez 2021 | [15] | [15] |
| Inderbitzi et al. 2020 | [21] | *absent* |
| Peña R. & Jenkins, EMPEROR | [20] | [37] |

So "**Hoy et al.'s reference [11] is Lazzoni et al. 2022**" — a sentence the project repeats as
one of its headline findings — is **false of the published paper**, where [11] is the CRIRES+
instrument paper. Sites:

- `README.md:205`, `SPEC.md:93`, `M7-RESULTS.md:6` and the table row at `:24`,
  `src/exosat_rv/analysis/satellites.py:42`, `src/exosat_rv/analysis/survey.py:7`,
  `scripts/fetch_paper.py:4`
- `M7-RESULTS.md:25` — "[32] Vanderburg, Rappaport & Mayo 2018" (published: [12])

**Correction:** either qualify as "reference [11] of the preprint / [10] of the published
version", or renumber to the published version, which is the one the paper cites.

---

## (c) Citations that could not be checked — no source in `papers/`

| Citation | Where | Why unverifiable | Best available corroboration |
|---|---|---|---|
| **1. Wahhaj et al. 2011** photometry (K = 12.01, H = 12.78 ± 0.12, J = 13.63) and host mass **31 ± 8 M_Jup** | `config.py:62`, `satellites.py:107`, `survey.py:78`, `M5-RESULTS.md:139`, `HANDOFF.md:493`, `m16_build_paper.py:113`, `m18_posteriors.py:77,134`, `tests/test_feasibility.py:215` | No copy of Wahhaj et al. 2011 in `papers/` | The *bibliographic* entry is confirmed by H26 [7] (ApJ 729(2), 139, doi 10.1088/0004-637X/729/2/139, arXiv:1101.2893). **The numbers taken from it are confirmed by nothing in the repo** — and 31 ± 8 M_Jup feeds a figure axis and a posterior comparison. Worth a direct check |
| **2. Speagle, J. S. 2020, MNRAS 493, 3132, dynesty** | `draft.template.html:753`, `methods-note.md:361,527`, `sampler-reproducibility-note.md:18`, `paper.bib:165`, `paper.md:37` | No local copy; the string "Speagle" appears in **no** archived paper | None. `paper.bib` already carries an honest note that the volume/page come from the in-repo citation and are not independently verified. This is the most-used unverified reference in the project |
| **3. Xuan et al. 2024**, *Nature*, "The cool brown dwarf Gliese 229 B is a close binary", doi 10.1038/s41586-024-08064-x, P = 12.1 d | `config.py:218`, `M3-RESULTS.md:33`, `M5-RESULTS.md:102`, `viper-runbook.md:198` | No local copy | None in-repo. This underpins the GJ 229 B **positive control** — the project's most load-bearing methodological device — so the 12.1 d period and the amplitude taken from it deserve a direct check |
| **4. Cassidy et al. 2009** | `satellites.py:49` | No local copy, and no identifier (year only) given in-repo | Oza et al. 2019 cites it five times for exactly this claim (close-in satellite orbital stability, its Eqns. 19–20) |
| **5. Kral et al. year: 2025 or 2026** | 2025 in `methods-note.md`; 2026 in `CITATION.cff`, `paper.bib`, `README.md`, `SPEC.md`, `M7`, `M10` | The archived manuscript is stamped ©ESO **2025**, dated 26 Nov 2025, arXiv 2511 — there is no acceptance or publication line | The **preprint** year is unambiguously 2025. A 2026 A&A publication year is plausible but asserted, not evidenced. Pick one and say which record it refers to |
| **6. Barnes & O'Brien 2002** (ApJ 575, 1087), **Domingos, Winter & Yokoyama 2006** (MNRAS 373, 1227), **Canup & Ward 2006** (Nature 441, 834), **Batygin & Morbidelli 2020** (ApJ 894, 143), **Bonavita et al. 2022** | `satellites.py:48-49,454-455`, `config.py:201`, `feasibility.py:86,99`, `gravity.py:54`, `M8-RESULTS.md:49` | No local copies | All five are corroborated field-for-field by the reference list or body text of an archived paper (Oza, Lazzoni, Ruffio, Kral respectively). Low risk, but not primary-verified |
| **7. Dorn et al. 2023** (A&A 671, A24) | `paper.bib:35`, `paper.md:31` | No local copy | H26 [11] confirms authors, title, volume, page, DOI and arXiv ID exactly. Low risk |

---

## (d) Claims attributed to a paper that the paper does not appear to support

1. **"Vanderburg et al. 2018 §2.4 is the false-positive taxonomy"**
   (`CITATION.cff:73`, `satellites.py:42`, `satellites.py:242`).
   §2.4 is *one* of six: "Planetary Activity Signals". The taxonomy is §2 as a whole — Table 1
   enumerates §2.1 exomoon reflex motion, §2.2 planet orbit, §2.3 planetary illumination,
   §2.4 planetary activity, §2.5 peak-pulling by exomoon light, §2.6 disk-clump occultation.
   `M8-RESULTS.md:179`, which cites §2.4 specifically for the activity amplitude, is correct;
   the three "taxonomy" citations should point at §2 / Table 1.

2. **The GRAVITY shortlist is miscounted** (`gravity.py:50-55`, `M10-RESULTS.md:41,131`).
   Kral et al. name exactly **five** best targets: AF Lep b, HD 155555 (AB) b, β Pic b,
   **HD 60584 b**, and 2MASS J1315-2649 b. HD 206893 B is the *paper's own target*, not one of
   the five. The repo's `BLUNT_SHORTLIST` holds five names = four of Kral's five (HD 60584 b
   dropped) **plus** HD 206893 B, yet the docstring describes it as "five viable GRAVITY+
   exomoon targets, **plus** HD 206893 B" (six), and `M10-RESULTS.md:131` calls HD 60584 b
   "a **sixth** target". There is no sixth. Correct phrasing: "four of Kral et al.'s five
   targets — HD 60584 b dropped as an unconfirmed candidate — plus HD 206893 B."

3. **"Ruffio et al. forecast CRIRES+ feasibility"** — see (b)#3. Ruffio et al. 2023 never
   mentions CRIRES; its forecast instrument is TMT/MODHIS.

4. **"this is how Ruffio et al. constrained HR 8799"** (`NEXT-DIRECTIONS.md:89`).
   The HR 8799 exomoon/binary-planet constraint in `papers/` is **Vanderburg & Rodriguez 2021**,
   which models RVs *from* Ruffio et al. (2021) — a third Ruffio paper that is **not** archived
   here and is not the Ruffio et al. 2023 HR 7672 B paper cited everywhere else in this repo.
   As written the sentence is ambiguous at best and conflates two papers at worst. Either name
   Vanderburg & Rodriguez 2021, or cite "Ruffio et al. 2021" explicitly and add it to `papers/`.

5. **`paper/joss/paper.bib:158-161` describes a defect that no longer exists.** Its `kral2026`
   note says "the exosat-rv repository's own CITATION.cff and README misattribute this paper to
   «Blunt et al.»". Both were corrected today; the note is now false about those two files
   (though still true of the 19 sites in (b)#1). Reword to point at the files that are actually
   still wrong, or delete once (b)#1 is applied.

6. **`docs/paper/contrast-wall-note.md:404` is a live "unresolved" marker.** It cites the Kral
   paper with **no first author at all** and a parenthetical saying the milestone docs give two
   different first authors and "the citation must be checked against the published version
   before submission". It has now been checked: **Kral, Q.** Replace the hedge with the name.

7. **`docs/paper/methods-note.md:593-600` is out of date.** It lists journal/volume/year as
   "not confirmed anywhere in the repository" for Köhler 2025, Lazzoni 2022, Ruffio 2023,
   Horstman 2024, Kral, Vanderburg 2018 and Vanderburg & Rodriguez 2021. Six of those seven
   **are** now confirmable — H26's own published reference list carries full bibliographic data
   for all of them (see the ground-truth table above); only the Kral publication year remains
   open. That note is currently suppressing citation detail the project has in hand.

---

## Cross-cutting notes

- **`docs/paper/cd35-etatel-draft.html` is generated from `docs/paper/draft.template.html`** and
  reproduces every error in it verbatim (verified by diffing the citation strings; the only
  difference is one extra Wahhaj mention injected by `scripts/m16_build_paper.py:113`).
  Fix the template and regenerate — do not hand-edit the draft.
- **Three of fourteen archived papers are filed under the wrong first author's name**
  (`blunt2026_…` → Kral; `martinez2020_…` → Trani; `tokadjian2023_…` → Makarov). All three wrong
  names have propagated into prose and, in two cases, into Python identifiers and a test file.
  Renaming the files is the durable fix; `scripts/fetch_paper.py` takes the slug from the
  command line, so there is no registry to correct — only operator discipline.
- **Papers with no author name in the filename fared better.** `kpic2025_…` and
  `retrograde2025_…` produced one wrong author citation between them (`M8-RESULTS.md:77`) and
  one correct-but-anonymous citation (`M8-RESULTS.md:203`, cited by arXiv ID only). A slug
  convention of `firstauthor_year` is only safe if the first author is read off the title page.
- **`src/exosat_rv/**/__pycache__/*.pyc`** still contain pre-fix docstring text (e.g. "Horstman
  … 2505.09781"). Harmless build artifacts; they regenerate.
- **`papers/text/abs.html`** is the arXiv abstract page for 2607.05193 (preprint title), not a
  paper. Harmless, but it is the only non-`.txt` file in that directory.
