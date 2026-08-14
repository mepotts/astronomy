# erosita-dr2 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

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
