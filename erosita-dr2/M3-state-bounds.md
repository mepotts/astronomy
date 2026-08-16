# M3 — the J0944 decision package + present-day state bounds on the shortlist

*2026-08-16. Scripts: [`scripts/m3_j0944_local.py`](scripts/m3_j0944_local.py),
[`scripts/m3_j0944_services.py`](scripts/m3_j0944_services.py),
[`scripts/m3_j0944_radio.py`](scripts/m3_j0944_radio.py),
[`scripts/m3_j0944_finder.py`](scripts/m3_j0944_finder.py),
[`scripts/m3_j0944_appendix.py`](scripts/m3_j0944_appendix.py),
[`scripts/m3_state_bounds.py`](scripts/m3_state_bounds.py). Outputs in [`out/`](out/).
Numbers computed by these scripts from local catalogs or queried anonymous services are marked
**[computed]**; external claims carry a source URL. Negative results are results. **No accounts
created, nothing submitted anywhere; the ToO text in the J0944 package is a DRAFT.***

---

## 1. Deliverable 1: the J0944 decision package

[`J0944-decision-package.md`](J0944-decision-package.md) — position/extinction, the complete
X-ray record with a three-tier amplitude case (stacked ×47.5 / epoch-space ×74 / assumption-free
floor ≥×20 against the DR1 UL with the 25-steady-pair calibration), sub-band spectral analysis,
counterpart-absence depths per survey, a SkyMapper finder chart
([`out/j0944_finder.png`](out/j0944_finder.png)), the riser-side artifact audit, a
class-by-class discussion, and a **DRAFT — NOT SENT** Swift ToO. Headline refinements over M2's
dossier [all computed]:

- **The spectrum is absorbed-moderate, not flat-hard**: sub-band rates peak at 1–2 keV with
  0.2–0.5 keV suppressed (HR +0.874±0.011) and a real 2–5 keV tail — consistent with roughly the
  Galactic column (N_H(HI4PI) = 8.85×10²⁰), *not* with a heavily obscured source. Supersoft
  classes (nova-SSS, thermal TDE) are excluded outright.
- **The counterpart absence is now quantified**: nothing within 10″ in Gaia DR3 (to G≈21),
  SkyMapper DR4 (g≈21), VHS DR5 (Ks≈18); the only object inside 10″ anywhere is a
  NWAY-rejected CatWISE-only source at 5.2″ (W1=16.7) that itself has no VHS/optical
  counterpart (blend/artifact or very red — noted honestly). LS10 does not cover Dec −71.2
  (cutout probe 500 vs control 200). log(f_X/f_opt) ≳ +1.9; F_X/νF_W1 ≳ 70.
- **Radio and γ silence**: SUMSS (≤6 mJy), RACS-low DR1 (~1.3 mJy 5σ) and 4FGL-DR4 all empty —
  the blazar/jetted escape hatch is closed.
- **Artifact audit**: split/merge (reverse crosswalk), confusion, extended-absorption, optical
  loading, moving object, catalog-fit fluke (UL-server presence 14.1), and pileup are all
  excluded; the *only* unexcludable mode is a single-visit detector artifact, which needs event
  data nobody has public access to — and which the DRAFT ToO would settle.
- **Class verdict**: Galactic VFXT/subluminous-LMXB or magnetic CV favored; Be/HMXB excluded
  (no donor to g≈21); magnetar-like disfavored at b = −13.6°; AGN/TDE requires a hostless
  z ≳ 0.3 ignition.

## 2. Deliverable 2: present-day state bounds (shortlist items 1–5)

**Method.** Two independent layers, both anonymous [computed 2026-08-16 →
[`out/m3_state_bounds.csv`](out/m3_state_bounds.csv), per-observation detail in
[`out/m3_state_bounds_detail.json`](out/m3_state_bounds_detail.json)]:

1. **Has any pointed X-ray instrument ever covered the position?** HEASARC Xamin TAP
   ([xamin/vo/tap](https://heasarc.gsfc.nasa.gov/xamin/vo/tap)) upload joins against
   `swiftmastr` (r = 17′ — the XRT 23.6′-square FOV half-diagonal), `xmmmaster` (r = 15′),
   `chanmaster` (r = 10′), counting only rows with real start times. Control queries at LMC X-1
   return 5 XMM + 84 Chandra rows, so the zeros below are real negatives, not join failures.
2. **What does the live Swift record say?** The Swift-XRT **LSXPS living catalog**
   ([Evans et al. 2023](https://ui.adsabs.harvard.edu/abs/2023MNRAS.518..174E/abstract)) via the
   `swifttools` 4.0.2 python package — cone searches (30″) plus the SXPS upper-limit server
   (3σ, total band 0.3–10 keV, per-dataset). Both are unauthenticated paths; registration is
   only needed for XRT product builds/ToO submission, which we did not touch. (Python 3.12 trap:
   `swifttools` imports `distutils` — installing `setuptools` into the venv fixes it.)

**Results** — the one-line answer per object is that **nothing has pointed at any of them since
the eRASS window**:

| # | object (M2 shortlist) | pointed coverage ever | most recent public X-ray information | present-day state |
|---|---|---|---|---|
| 1 | 3eRASS J094452.8-711152 (unexplained riser) | **none** (Swift LSXPS: "NotObserved"; XMM 0; Chandra 0) | the eRASS:3 stack itself (≤2021-06) | **unbounded** — eROSITA is the only X-ray instrument ever to have seen it |
| 2 | 3eRASS J155100.8-453347 (M-dwarf superflare cand.) | **none** | eRASS:3 stack | **unbounded** |
| 3 | 3eRASS J060622.5-624814 (TDE-like fader) | Swift ×4, 3.5 ks total, 2009-11→2014-11 (all pre-eROSITA) | LSXPS stack 3σ UL **< 0.0068 XRT ct/s** — but its on-position exposure (3081 s) equals the four 2009–2014 obs exactly [computed], so no post-eRASS data; per-obs UL 2014-11-04 < 0.0195 ct/s | **unbounded since 2014**; the deepest XRT UL corresponds to ~3×10⁻¹³ (0.3–10 keV, rate→flux conversion approximate) — above the eRASS1 peak (1.4×10⁻¹³), so XRT at this depth could only catch a re-brightening |
| 4 | 1eRASS J050338.2-304513 (AGN X-ray collapse) | Swift ×4, 4.3 ks, 2005-03→2013-08 (pre-eROSITA) | **LSXPS J050338.1-304509** at 3.5″, catalog rate 0.0204±0.0034 ct/s — built from the same 2005–2013 data; UL server refuses (catalogued source present) | **unbounded since 2013**: Swift saw it persistent through 2013, eROSITA saw it gone by the 2020–21 stack; no data since |
| 5 | 1eRASS J051910.4-253443 (flaring AGN now low) | **none** pointed (XMMSL3 slew detections only, M2) | eRASS:3 stack (blank, presence 1.03, M2) | **unbounded** |

**Interpretation (the durable point):** none of the five has any post-eRASS pointed X-ray
data — there is no "currently bright" headline because *nobody has looked*, including at the two
objects (3, 4) that Swift used to visit before eROSITA existed. The most recent X-ray knowledge
of all five objects is the public eRASS:3 stack ending 2021-06; the next survey epochs (eRASS4/5)
are unreleased until DR3 (H2 2028, [erosita.mpe.mpg.de/erass](https://erosita.mpe.mpg.de/erass/)).
Every one of these is therefore a live follow-up target, and the J0944 DRAFT ToO (package §9) is
the ranked-first ask.

## 3. Deliverable 3 (optional item): LMC-fader × OGLE mini-study — feasibility

**Verdict: feasible account-free, with one structural caveat.** Checked 2026-08-16:

- **What is scriptable without an account**: the OGLE Collection of Variable Stars serves
  per-object OGLE-IV I/V light curves as flat `.dat` files over FTP/HTTP
  ([OCVS](https://ogle.astrouw.edu.pl/main/collections.html),
  [query interface](https://ogledb.astrouw.edu.pl/~ogle/OCVS/)) — no registration; a third-party
  SSA/TAP mirror of OCVS light curves exists at
  [UPJS](https://skvo.science.upjs.sk/ogle/lc/lc-web/info). The
  [XROM](https://ogle.astrouw.edu.pl/ogle4/xrom/xrom.html) real-time pages publish I-band light
  curves of known X-ray binaries in the Magellanic system.
- **The caveat**: there is **no public arbitrary-position OGLE-IV forced photometry** — the
  on-line photometric databases cover OGLE-II only
  ([overview](http://ogledb.astrouw.edu.pl/~ogle/photdb/overview.html), checked 2026-08-16), so
  positions whose counterparts are not in OCVS/XROM get nothing.
- **Scoped study**: match the 25 LMC-box fade-candidates (M2 §3) against OCVS classes
  (Be+eclipsing+LPV, which is where Be/XRB donors live) and the XROM roster; pull `.dat` light
  curves for matches; look for I-band brightenings coincident with the eRASS1 X-ray detections
  (the classic Be-disk/outburst correlation, [Reig 2011](https://ui.adsabs.harvard.edu/abs/2011Ap%26SS.332....1R/abstract)).
  Expected yield: OCVS Be-star coverage of the LMC is extensive, so most genuine Be/XRB donors
  should match; non-matches stay unresolved (that is the honest limit of the public data).
  Effort: one script + one doc section. **Not executed in M3** (kept within approved scope).

## 4. Recommended M4

1. **Matthew's gate, unchanged and now fully prepared**: decide on the J0944 Swift ToO
   ([package §9](J0944-decision-package.md), DRAFT — submission would be via his own account at
   https://www.swift.psu.edu/too/). Everything else about J0944 is exhausted from public data.
2. **LMC-fader × OGLE mini-study** — scoped feasible above; a self-contained note if a few
   faders match OCVS Be stars with correlated I-band states.
3. **Classifier rebase** (M2 recommendation #4) — still unblocked, counterpart catalogs local.
4. **W4 Gaia DR4 NSS join (2026-12-02)** — unaffected; ingest layer unchanged.

## 5. Files

- [`J0944-decision-package.md`](J0944-decision-package.md) — deliverable 1 (with full catalog
  rows in the appendix)
- `out/j0944_rows.json` — full DR2 Main/Hard + DR1 rows + neighbor context [computed]
- `out/j0944_services.json` — UL server, dust, N_H, SkyMapper/Gaia/CatWISE/VHS cones, LS10
  probe, radio/γ cones, amplitude algebra [computed]
- `out/j0944_finder.png` — finder chart (SkyMapper color, hips2fits), 534 KB
- `out/m3_state_bounds.csv` — deliverable 2, one row per shortlist object
- `out/m3_state_bounds_detail.json` — per-observation records behind the CSV
- venv addition: `swifttools` 4.0.2 + `setuptools` (python-3.12 `distutils` shim)
