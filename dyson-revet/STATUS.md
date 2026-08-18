# dyson-revet — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-18** — **M1 ✓** ([M1-reproduce-and-vet.md](M1-reproduce-and-vet.md)). Selection
  reproduced **7/7** (catalog cuts as code; H/I/J fail exactly the SNR cut as Heph III states);
  boundary documented — candidate F (γ=0.03) is incompatible with the paper's stated γ≥0.1 model
  grid, the CNN + visual stages are unpublishable-irreproducible, and Heph II Table 5 swaps C/D's
  Gvar↔RUWE. **Premise correction: D was killed by JWST on 10 Jul 2026** (Hephaistos IV,
  arXiv:2607.09460 — z≈0.9 galaxy 1″ away; my centroid test shows why archival methods can't see
  1″ blends). **I is the last candidate standing: verdict INDETERMINATE** (2σ excess, centroid
  directions flip between AllWISE/unWISE coadds, no contaminant in Legacy DR10/UKIDSS; new: a very
  red PSF source 6.8″ NE). Control C reproduces the published refutation to 0.05″ (W3 3.72″ vs
  3.67″). Found + verified a **3600× unit error** in Ren et al. 2024's hot-DOG density (9e-6 is per
  arcmin², not arcsec²): catalogued Hot DOGs explain ~0.4 candidates, not all 7 — the contaminant
  class is the ~10× fainter red-galaxy population (S24's own 15000/sr ⇒ ~60 expected among 5M).
  **SPHEREx QR2 axis opened, account-free**: 373/287 planes at D/I, forced spectrophotometry
  validates to ~10% vs catalogs, both stars photospheric through 5 µm — but the 100–200 K excess
  band is beyond SPHEREx; the discriminating axis stays ≥10 µm (JWST). CDS sed main host still
  half-broken (truncated VOTables); CFA mirror works. Next (M2 proposal in doc §6): I dossier as
  the deliverable, W4 via bulk downloads + centroid stage with the JWST-calibrated 1–2″ floor.

- **2026-08-17** — Folder created from run-3 avenue #7 (wave 4). First agent launched: W1
  (reproduce the Hephaistos II selection; acceptance = recover all 7 published candidates) +
  W2 on the two surviving candidates (D, I: centroid-offset + density priors) + W3 coverage
  check (SPHEREx QR2 at candidate positions). Nothing verified yet.
