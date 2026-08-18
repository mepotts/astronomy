# erosita-dr2 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-18 (M5-writeup COMPLETE)** — [`M5-writeup.md`](M5-writeup.md),
  [`draft-rnaas-vanished-census.md`](draft-rnaas-vanished-census.md) and
  [`writeup-audit.md`](writeup-audit.md) landed. Label is **M5-writeup**, not M5 — the
  classifier thin-slice M5 stays queued behind Matthew's pivot acceptance. J0944 untouched and
  **deliberately absent from the draft** (it is a riser; a fader census has no place for it).
  **Venue: one RNAAS note**, not a short paper — one clean measurement, one decisive figure, no
  confirmed individual object, and every candidate that could carry a longer paper is fenced or
  unconfirmed; limits verified live at journals.aas.org ("1,500 words or fewer", "a single
  figure or table (but not both)", abstract required, non-peer-reviewed). Draft = **1,338
  words, one figure, no table**, DRAFT — NOT SUBMITTED, author/affiliation placeholders.
  **Headline**: of the 261 bright (DET_LIKE_0 ≥ 30) eRASS1 sources absent from DR2, **57% still
  have flux at their position (catalogue artifacts) and 41% sit on blank sky (real faders)** —
  the release paper's §5.1 assumption that unmatched ⇒ spurious breaks at the bright end, and
  breaks harder the brighter the source (71% artifacts above DET_LIKE 100, 100% above 242).
  **Prior art: NOT SCOOPED** (arXiv complete 2026-07-28→08-17, ADS, DR2 pages: nobody has ever
  published an eRASS1↔eRASS:3 variability/vanishing census, no DR2 variability VAC exists) —
  **but Ramos-Ceja+2026 §5.1 already runs the same UID_DR1 cross-walk and publishes the
  unmatched fractions (21% / 3.5% >DL10 / 0.15% >DL50) while never mentioning variability**;
  uncited that would be fatal, so the draft now opens on it as the thing being tested.
  **Audit: 107 quantities, 93 VERIFIED / 14 CORRECTED / 0 not-re-derivable**, plus 1 UNSOURCED
  dropped. Load-bearing corrections: the threshold band is **+17/−8, not M2's +35/−12** (M2
  counted rows in the presence interval; the tree tests split/halo *before* and the 40″ PSF
  confuser *after*, so 18+4 never change class); M1's "12.6% spurious + 8.4% variability" is
  **not in §5.1** (UNSOURCED, dropped); 1 of 25 UL calibrators is degenerate (UL_S=inf) and
  M2's "median 1.13±0.07" is a mean; `fade_frac` never discriminated (fader 1.25 vs steady
  1.13) — only `presence` does; t₃/t₁ = 2.84 not 2.9; XROM 49.8′ and LMC HMXB 12.9′ were
  rounded *up* in M4; M1's eRASS:3 span is internally inconsistent (552 d ≠ 556 d) so the draft
  quotes no span. **New measurement that closed a real gap**: the presence threshold had only
  ever been calibrated on ≥20σ sources, so 60 steady controls **matched to the faders in flux
  AND DET_LIKE** were queried — controls land at P = 2.03–3.78, faders at P ≤ 1.49, **disjoint,
  0/60 misclassified → <4.9% contamination (95% one-sided), fewer than 6 of the 107**. The cut
  is not tuned; the data put a gap there. 3 scripts, 4 out/ files (incl. the one-figure
  `m5w_vanished_census.png`); one anonymous UL-server POST, cached. LMC null + OGLE scoping law
  drafted as **companion note B** (needs XROM contact, not done; its gap dates must stay worded
  as measured-by-us — 2022-08-16 is unsourced in the literature). No accounts, no submissions,
  no commits (orchestrator's job). Matthew's gates in doc §6: submit-or-not + affiliation/ORCID,
  a citable Zenodo DOI (same open item as itf-linker C5), confirm A&A 712, A171 against ADS,
  and the unchanged J0944 ToO decision.
- **2026-08-16 (M4 COMPLETE)** — [`M4-lmc-ogle-and-rebase.md`](M4-lmc-ogle-and-rebase.md)
  landed; J0944 untouched (Matthew's gate). **Part A (LMC-fader × OGLE mini-study, the M3
  design executed)**: the 25 LMC-box fade-candidates match **nothing** — 0/25 in OCVS
  (217,725 variables, OGLE-IV 7 classes + OGLE-III lpv/dpv/rcb), 0/25 in XROM (97 monitored
  XRBs), 0/25 in the 53-object eRASS1_HMXB_LMC VAC, 0/25 Sabogal Be candidates
  (footprint-void, nearest 2°) vs 0.19 chance matches expected (16-position shifted control);
  positions are inside OGLE territory (nearest variable 0.4–4.8′). Gaia DR3 Be-donor test
  (donors must be G ≤ 17, per the VAC's G 12.68–17.00): **24/25 have no Be-donor-capable star**
  → the Be/XRB reading is dead for the population (M2 §2.5's LMC lines withdrawn); demographics
  = 9 AGN-colored + 4 AGN-leaning + 3 foreground active stars + 8 ambiguous + 1 blue-star
  ambiguity (J055216.6-681015: G=16.85 BP−RP=−0.21 plx 0±0.07 photometric OBe profile, but
  μδ ~1 mas/yr ≈ 230 km/s off LMC systemic → halo hot star equally likely; spectroscopy would
  decide; nothing reported). **Scoping law (measured)**: OCVS collection light curves are
  frozen at release epochs (RRLYR end 2016-04) and the live XROM series shows OGLE-IV dark
  2020-03-13 → 2022-08-16 (886 d, CAL 83) — the entire eRASS2/3 fade window is optically
  unobservable in public OGLE data; future eRASS-window optical designs must use ASAS-SN, not
  OGLE. **Part B (classifier-rebase M0 vs DR2 reality)**: (1) VAC inventory — DR2 today =
  Main/Hard + 6 eRASSc3 counterpart cats (classification now BAKED IN: class_gal_exgal, STAREX,
  class_jetted, SIMBAD, Gaia DSC) + 2 CV lists; **no** DR2 coronal/cluster/blazar/ULX/HMXB/
  variability successors; DR1 verdicts inheritable via UID_DR1 for 37.6% of rows; DR2 still
  bulk-FITS-only (HEASARC/VizieR/ESASky all DR1-only, checked). (2) Reconciliation experiment
  (n=100 primary + n=2000, seed 20260816): **49%/53.9% NOT trivially classified by one catalog**
  (p_any ≥ 0.5; 54–57% at 0.8; 40.2% even at DET_LIKE ≥ 20) — 2–2.5× above the ~20% kill bar;
  gap = 28% outside LS10 footprint + 21% low-confidence, NOT catalog disagreement (0.5%
  diff-object, 4.3% DSC conflict). (3) Prior-art re-sweep: nobody has shipped a dossier layer
  or even ingested DR2 anywhere. **Memo: PIVOT** — from "unify 15 VACs" (dead: consortium
  consolidated) to "the only queryable access + translation layer over DR2" (+UID_DR1
  inheritance + out-of-footprint fallback); BUILD decision stays with Matthew/IDEAS. 2 scripts,
  4 out/ CSVs (m4_lmc_ogle_{matches,control,lightcurves}, m4_reconciliation); data/ogle/ cache
  +~30 MB; no accounts, no submissions, no commits (orchestrator's job). Recommended M5 in doc
  §3 (J0944 gate; rebase M1 thin slice if pivot accepted; W4 on schedule 2026-12-02).
- **2026-08-16 (M3 COMPLETE)** — [`M3-state-bounds.md`](M3-state-bounds.md) +
  [`J0944-decision-package.md`](J0944-decision-package.md) landed (ANALYSIS scope: nothing
  submitted anywhere; ToO text is DRAFT for Matthew). **J0944 package**: amplitude case now
  three-tier (stacked ×47.5 / epoch ×74 / assumption-free floor ≥×20 vs the DR1 UL_B with
  25-steady-pair calibration median 1.25); sub-band spectrum revises M2's "hard/absorbed" to
  **absorbed-moderate peaking 1–2 keV** (HR_P1/P23=+0.87 — ~Galactic N_H 8.9×10²⁰; supersoft
  classes excluded); counterpart absence quantified (no source <10″ to G≈21 / g≈21 / Ks≈18 /
  W1≈17.7; LS10 doesn't cover; SUMSS+RACS radio and 4FGL empty; the lone 5.2″ CatWISE object is
  NWAY-rejected and VHS-invisible); riser-side artifact audit excludes every catalog-testable
  mode (split/merge, confusion, extended, optical loading, moving object, UL-presence 14.1,
  pileup) — only a single-visit detector artifact remains untestable without event data; class
  verdict: **Galactic VFXT/subluminous-LMXB or magnetic CV favored, Be/HMXB excluded, magnetar
  disfavored at b=−13.6°, AGN/TDE needs hostless z≳0.3**; SkyMapper finder chart
  `out/j0944_finder.png`; full Main/Hard/DR1 rows in the package appendix; DRAFT Swift-XRT 5 ks
  ToO prepared — NOT SENT. **State bounds (shortlist 1–5)**: HEASARC TAP (swiftmastr 17′ /
  xmmmaster 15′ / chanmaster 10′, LMC X-1 control validates) + live Swift LSXPS via swifttools
  4.0.2 unauthenticated (py3.12 needs setuptools for distutils): **zero post-eRASS pointed
  X-ray data on all five** — J0944+J1551+J0519 never observed pointed at all; J0606 (4 obs
  2009–14, stack UL 0.0068 ct/s whose on-position exposure equals those 4 obs exactly) and
  J0503 (LSXPS J050338.1-304509 = 0.020 ct/s from 2005–13 data only) have nothing since
  2013/2014 → most recent X-ray knowledge of every shortlist object is the eRASS:3 stack
  (≤2021-06). **OGLE feasibility**: OCVS/XROM light curves scriptable account-free (FTP + UPJS
  SSA/TAP), but no public arbitrary-position OGLE-IV photometry (photdb = OGLE-II only) → LMC
  mini-study feasible via OCVS/XROM matching, not executed (scope). 6 scripts, 5 new out/
  files; no accounts, no submissions, no commits (orchestrator's job). Recommended M4 in
  M3 doc §4 (Matthew's ToO gate; OGLE mini-study; classifier rebase; W4 on schedule).
- **2026-08-14 (M2 COMPLETE)** — [`M2-vetting.md`](M2-vetting.md) landed: per-candidate verdicts
  for all **381 touched sources** (140 M1 candidates + full 261 vanished census) in
  [`out/m2_verdicts.csv`](out/m2_verdicts.csv): **104 IDENTIFIED / 123 PLAUSIBLE-CLASS /
  153 ARTIFACT / 1 GENUINELY-UNEXPLAINED**. The survivor is **3eRASS J094452.8-711152** — ×57
  hard-detected riser, NWAY p_any≈0 in GDR3+CW2020, no archival X-ray (2RXS/XMMSL3/CSC2.1/
  2SXPS/5XMM/ART-XC all empty), TNS+SIMBAD+literature empty — **flagged for Matthew, nothing
  reported by us**. Vanished-list forensics (paper §3.2.5 + DR2 UL server, 25-steady-pair
  calibrated): **148 artifacts / 6 indeterminate / 107 plausible real faders (+35/−12 threshold
  band)**; M1's top-20-by-DET_LIKE vanished list was artifact-selected (14/20). Headline M1 rows
  resolved: SRGt J071522.1-191609, SRGt J123822.3-253206, eRASSt J142140-295321 (published TDE),
  eRASSt J234402.9-352640, eRASSt J045650.3-203750, MAXI J0903-531, EP240309a, SMC X-1 split;
  TDE-like fader J060622.5-624814 downgraded to host-unconfirmed (LS10 cp g=23.5 at 7″,
  p_any=0.002); new-bright J155100.8-453347 = M-dwarf-superflare candidate (91 pc, hard-detected,
  NWAY ambiguous). Consortium file defect found+worked around: eRASSc3_Main_GDR3 ships
  `GDR3_source_id` twice. Data +2.77 GB (6 NWAY counterpart cats + Hard cat). 8 scripts, 7 out/
  CSVs; no accounts, no submissions, no commits/pushes (orchestrator's job). Recommended M3 in
  doc §5 (J0944 decision package for Matthew; LMC fader × OGLE mini-study; classifier rebase
  unblocked).
- **2026-08-14 (M1 COMPLETE)** — [`M1-first-sweep.md`](M1-first-sweep.md) landed; all three
  workstreams ran. **W1**: DR2 = catalogue-only, stacked-values-only (NO per-eRASS columns — the
  README premise is corrected in M1 §1), Main v1.3 = 1,975,540 rows, no TAP anywhere yet
  (HEASARC + VizieR still DR1-only), consortium shipped no variability product (novelty holds,
  as a first-public-look). **W2**: 632,668 clean DR1×DR2 point-source pairs via the consortium
  `UID_DR1` cross-walk; scale offset measured at 2% (median bright-pair R = 0.979); 2,138 pairs
  at z ≥ 5; conservative amplitudes: 62 pairs > 5x, 14 > 10x stacked, 49 > 10x in reconstructed
  epoch space; censuses: 261 vanished bright DR1 sources, 286 bright DR2-new risers.
  **W3**: 140 candidates × Gaia DR3 + SIMBAD (133/140, 114/140 matched) —
  top ranks recover known transients (V* QX Nor LMXB ×475 epoch-amp, SWIFT J1626.5-5156,
  V1708 Sco B nova, 2 eRASSt transients, 2 CVs in outburst) and leave genuinely unidentified
  candidates: 3eRASS J094452.8-711152 (rise ×57, no Gaia/SIMBAD), 3eRASS J155100.8-453347
  (new-bright ≥×49), 7 optical-faint vanished, 1 TDE-like fader. Candidate CSV committed
  (`out/m1_candidates.csv`, 59 KB). Recommended M2 in doc §5 (vet unidentified; vanished-list
  dropout forensics vs paper §3.2.5; classifier rebase on the released eRASSc3 counterpart cats;
  W4 ingest ready). Downloads in `data/` (3.8 GB); scripts LF-clean; no accounts, no submissions,
  no pushes.
- **2026-08-14 (M1 W1 log)** — W1 inventory verified against the live portal + release paper
  (arXiv:2607.27772). Pre-download disk check per rule: **360 GB free on C:**; planned bulk pulls
  into `data/` (gitignored): `eRASS3_Main_v1.3.fits` **2.14 GB**
  (https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.fits)
  and `eRASS1_Main.v1.2.fits.tar.gz` **0.64 GB**
  (https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/MerloniA_DR1/eRASS1_Main.v1.2.fits.tar.gz),
  serial downloads. Key W1 findings so far: DR2 is catalogue-only, stacked eRASS:3 values only
  (no per-eRASS epoch columns), but ships a consortium DR1 cross-walk column `UID_DR1`
  (no flux criterion in that match) — W2 route (b) via DR1 join.
- **2026-08-14** — Folder created from run-3 avenue #5. First agent launched: W1 inventory
  (access, catalog structure, value-added survey, DR2-paper novelty check) + first W2 slice
  (flux-ratio ranking) + W3 spot cross-match of top variables against Gaia DR3. Nothing verified
  yet; treat everything in README as claims until the M1 doc lands.
