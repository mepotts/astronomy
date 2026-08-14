# erosita-dr2 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

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
