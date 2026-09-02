# 3eRASS J094452.8-711152 — decision package for Matthew

*2026-08-16, M3. Everything needed to decide on follow-up for M2's only GENUINELY-UNEXPLAINED
object, in one document. Scripts: [`scripts/m3_j0944_local.py`](scripts/m3_j0944_local.py),
[`scripts/m3_j0944_services.py`](scripts/m3_j0944_services.py),
[`scripts/m3_j0944_radio.py`](scripts/m3_j0944_radio.py),
[`scripts/m3_j0944_finder.py`](scripts/m3_j0944_finder.py); machine-readable results in
[`out/j0944_rows.json`](out/j0944_rows.json) and [`out/j0944_services.json`](out/j0944_services.json).
Numbers computed by these scripts from the local DR1/DR2 catalogs or from queried public services
are marked **[computed]**; external claims carry a source URL. **Nothing has been sent anywhere —
no ToO, no TNS, no note. The ToO text in §9 is a DRAFT for Matthew's decision.***

---

## 1. Bottom line

A source at RA 146.22033, Dec −71.19802 (±0.48″) was faint in eRASS1 (Jan 2020, F(0.2–2.3) =
3.4×10⁻¹⁴) and averaged **×47 brighter** over the following ~1.4 yr of the eRASS:3 stack
(1.6×10⁻¹²), with a genuine 2–5 keV tail and **no counterpart in any public optical/IR/radio
survey** (Gaia ~21, SkyMapper g~21, VHS Ks~18, CatWISE W1~17.7, SUMSS/RACS radio, 4FGL γ — all
empty at the position). Every riser-side catalog-artifact mode that can be tested without event
data is excluded (§6). **No pointed X-ray instrument has ever observed the position** (§8) —
eROSITA's four catalog numbers are the entire X-ray record of this object.

The evidence favors a **Galactic low-luminosity X-ray transient with an optically invisible
(compact or very-low-mass) companion** — a VFXT-type/subluminous LMXB outburst or a magnetic CV
at ≳2 kpc; a magnetar-like outburst is possible but disfavored by the b = −13.6° latitude; any
AGN/TDE reading requires an extreme hostless ignition at z ≳ 0.3 (§7). The single highest-value
next step is a short Swift-XRT look (§9, DRAFT): it decides "still on vs off" and delivers an
arcsecond-level position for ~5 ks.

## 2. Position and field

| quantity | value | source |
|---|---|---|
| ICRS RA, Dec | 146.220330, −71.198023 | eRASS3_Main_v1.3 row [computed] |
| POS_ERR (1σ) | 0.48″ (RADEC_ERR 0.33″; 3σ ≈ 1.4″) | same row [computed] |
| Galactic l, b | 288.983, −13.574 | same row (LII/BII) [computed] |
| Ecliptic ELON, ELAT | 218.375, **−70.019** | same row [computed]; high \|ELAT\| → long visit windows each eRASS |
| E(B−V) | 0.139 (Schlafly & Finkbeiner 2011) / 0.162 (SFD98), A_V ≈ 0.43 | IRSA dust service, https://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust [queried 2026-08-16] |
| Galactic N_H | 8.85×10²⁰ cm⁻² (HI4PI map) | HEASARC w3nh, https://heasarc.gsfc.nasa.gov/cgi-bin/Tools/w3nh/w3nh.pl [queried 2026-08-16] |

Foreground extinction is negligible for counterpart searches (A_V ≈ 0.4 mag): the counterpart
absence in §5 is not an extinction effect.

Finder chart (SkyMapper color via CDS hips2fits, error circle + rejected neighbors marked):
[`out/j0944_finder.png`](out/j0944_finder.png). The 3σ error circle is **empty** in SkyMapper
imagery; the bright object 10.2″ NW is the NWAY-rejected G=16.4 star.

## 3. The X-ray record (all of it)

Four catalog measurements + the UL server. Complete Main/Hard/DR1 rows: appendix §11.

| epoch | data | value (0.2–2.3 keV unless noted) | source |
|---|---|---|---|
| 2020-01-24 → 01-28 (MJD 58872.5–58877.0) | eRASS1 detection **1eRASS J094453.1-711153**, sep 1.67″, DET_LIKE 25.3, 18 aperture cts (APE_POIS 1.3×10⁻¹⁰) | rate 0.0367±0.0100 ct/s; **F = (3.4±0.9)×10⁻¹⁴** | eRASS1_Main.v1.2 via strong `UID_DR1` [computed] |
| same epoch, catalog-independent | DR1 UL server at position: 17 cts in 486 s | **F(eRASS1) ≤ 7.9×10⁻¹⁴** (UL_B, one-sided 99.87% CL) | https://erosita.mpe.mpg.de/erodat/upperlimit/service_multi, band 024 [queried 2026-08-16]; method [Tubín-Arenas et al. 2024](https://arxiv.org/abs/2401.17305) |
| 2019-12 → 2021-06 stack (this position: visits ~Jan 2020, ~Jul 2020, ~Jan 2021 — inferred from the 6-month cadence, [portal](https://erosita.mpe.mpg.de/dr2/)) | eRASS:3 **3eRASS J094452.8-711152**, DET_LIKE 9401, 2181±48 ML cts (1637 aperture cts vs 5.6 bkg) | rate 1.7080±0.0379 ct/s; **F = (1.590±0.035)×10⁻¹²** | eRASS3_Main_v1.3 [computed] |
| same stack, hard band | Hard-catalog member, DET_LIKE_3 = 197 | **F(2.3–5 keV) = (7.2±0.9)×10⁻¹³**; F(0.2–5) = 2.29×10⁻¹² | eRASS3_Hard_v1.2 [computed] |
| stack, catalog-independent | DR2 UL server: presence UL_B/UL_S = **14.1** (soft), 2.7 (2.3–5 keV) | flux is at the position, not a catalog-fit artifact | UL server, bands 024/023 [queried 2026-08-16] |

**Consortium crosswalks in the DR2 row itself: UID_5XMM = −1, UID_2RXS = 0, UID_CSC empty,
UID_DR1Hard = 0** [computed] — no prior X-ray identity there either, consistent with M2's
2RXS/XMMSL3/CSC2.1/2SXPS/5XMM/ART-XC/TNS/SIMBAD/literature sweep (all empty, M2 §2.1).

### The amplitude case, stated honestly

- **Stacked space (weakest assumptions):** F_stack/F_eRASS1 = 46.5; ×47.5 after the M1 ×0.979
  DR1↔DR2 scale correction [computed].
- **Robust floor (no trust in the DR1 catalog fit at all):** F_stack / UL_B(eRASS1) =
  1.59×10⁻¹² / 7.9×10⁻¹⁴ = **≥ ×20**, and the DR1-side UL calibration on M2's 25 steady pairs
  gives UL_B/F1 median 1.25 (16–84%: 1.16–1.32) [computed] — i.e. for an unchanged source UL_B
  sits just above its true flux, so ×20 is a hard floor.
- **Epoch space (M1 reconstruction):** r₂₃ = (r₃t₃ − r₁t₁)/(t₃ − t₁) = 2.735±0.062 ct/s →
  post-eRASS1 average F ≈ 2.5×10⁻¹², **×74 the eRASS1 level (×57 at 1σ-conservative)**
  [computed]. *M1 caveat carried forward:* this assumes the version-030 stack contains the eRASS1
  counts unchanged; no containment tension here (the stack is far brighter, subfloor/violation
  flags clean [computed]).
- **Hard band:** eRASS1 UL_B(2.3–5) = 3.6×10⁻¹³ vs stack 7.2×10⁻¹³ → rise ≥ ×2 only (eRASS1
  hard sensitivity is poor; weak bound) [computed].
- **What the stack cannot say:** whether the post-Jan-2020 brightening was steady. The 2.5×10⁻¹²
  epoch average is consistent with anything from a sustained ~1.4-yr high state to a single
  ≥×150 outburst confined to one ~days-long visit window (eRASS2 *or* eRASS3). Per-eRASS fluxes
  exist only inside the consortium (M1 §1).

## 4. Spectral information from the catalog columns

Sub-band ML rates from the Main row (band definitions:
[data model](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.html))
[all computed]:

| band | keV | rate (ct/s) | DET_LIKE |
|---|---|---|---|
| P1 | 0.2–0.5 | 0.104 ± 0.009 | 450 |
| P2 | 0.5–1.0 | 0.648 ± 0.023 | 3522 |
| P3 | 1.0–2.0 | 0.888 ± 0.027 | 5384 |
| P4 | 2.0–5.0 | 0.142 ± 0.013 | 378 |
| P5 | 5.0–8.0 | 0.000 ± 0.004 | 0 |
| P6 | 4.0–10 | 0.012 ± 0.006 | 4.8 |

Hardness ratios: HR(P1 vs P2+P3) = **+0.874 ± 0.011** (0.2–0.5 keV strongly suppressed);
HR(P2+P3 vs P4) = −0.831 ± 0.015 [computed].

What this does and doesn't constrain:

- The count spectrum **peaks at 1–2 keV with a real 2–5 keV tail and nothing above 5 keV**
  (eROSITA's effective area above 5 keV is small, so P5's emptiness is weak information).
- The P1 suppression is consistent with absorption at roughly the full Galactic column
  (N_H ~ 10²¹ cm⁻²) or somewhat above; it is **not** the signature of a heavily obscured
  (10²³⁺ cm⁻²) source — those would also kill P2. M2's "hard/absorbed spectrum" phrase should be
  read as *moderately absorbed with a hard-detected tail*, not intrinsically flat-hard.
- **Supersoft classes are excluded** (nova-SSS, thermal-TDE-like kT ≲ 100 eV spectra would put
  essentially nothing above 1 keV; here F(2.3–5)/F(0.2–2.3) = 0.45 in the catalog ECF fluxes).
- Quantitative Γ/N_H needs response folding of event data that DR2 does not ship; catalog fluxes
  assume the consortium's Γ=2.0, N_H=3×10²⁰ ECF model
  ([Merloni et al. 2024 §4](https://arxiv.org/abs/2401.17274), DR1 convention; DR2 "changes
  small", [arXiv:2607.27772 §3](https://arxiv.org/abs/2607.27772)).

## 5. The counterpart absence, quantified

All cones re-run at the DR2 position on 2026-08-16 [computed] unless cited otherwise.

| survey | reaches | nearest object | inside 10″? |
|---|---|---|---|
| Gaia DR3 | G ≈ 21 survey limit; completeness rolls off past G ≈ 20.3 ([Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3); [Fabricius et al. 2021](https://www.aanda.org/articles/aa/full_html/2021/05/aa39657-20/aa39657-20.html)); faintest source in our 30″ cone G = 20.91 | 10.18″: G = 16.36, plx 0.465±0.041 mas (~2.2 kpc), Pstar 1.00 | **no** |
| SkyMapper DR4 | 10σ field depths 18.5–20.5 by filter ([Onken et al. 2024](https://arxiv.org/abs/2402.02015)); faintest in cone g = 20.96 | 10.21″ (the same star, g = 16.69) | **no** |
| VHS DR5 (near-IR) | 5σ Ks ≈ 18.1 Vega target depth ([McMahon et al. 2013](https://ui.adsabs.harvard.edu/abs/2013Msngr.154...35M/abstract)); faintest in cone Ks = 17.46, J = 18.96 | 10.07″ (same star, J = 15.00, Ks = 14.55) | **no** |
| CatWISE2020 (mid-IR) | 90% complete at W1 = 17.7, W2 = 17.5 ([Marocco et al. 2021](https://ui.adsabs.harvard.edu/abs/2021ApJS..253....8M/abstract)) | **5.24″**: W1 = 16.69, W1−W2 = 0.26 — see below | 1 object, rejected |
| Legacy Surveys DR10 | — | **position not covered** (cutout probe HTTP 500 vs 200 at a control position [computed 2026-08-16]; consistent with the NWAY LS10 catalog having no row, M2) | n/a |
| SUMSS 843 MHz | catalog limit 6 mJy at δ ≤ −50 ([Mauch et al. 2003](https://ui.adsabs.harvard.edu/abs/2003MNRAS.342.1117M/abstract)) | none within 60″ | **no** |
| RACS-low DR1 887 MHz | median rms 0.25 mJy/beam → ~1.3 mJy at 5σ ([Hale et al. 2021](https://ui.adsabs.harvard.edu/abs/2021PASA...38...58H/abstract); footprint −80° ≤ δ ≤ +30°, \|b\| > 5° includes this position) | none within 60″ | **no** |
| Fermi-LAT 4FGL-DR4 | — | none within 10′ ([VizieR IX/72](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=IX/72)) | **no** |

NWAY verdicts from the released counterpart catalogs (M2 [computed]): `p_any` = 0.0000 (GDR3),
4×10⁻⁶ (CW2020). The DR1→DR2 position agreement (1.67″ at DR1 POS_ERR 2.76″) shows no sign of an
unmodeled astrometric systematic that could rescue a 5–10″ association.

**The one object inside 10″, honestly:** the CatWISE source at 5.24″ (= 10.9× POS_ERR) has
nominally stellar colors (W1−W2 = 0.26) but **no VHS counterpart** (Ks > ~17.5 at its position)
and no optical source — W1 = 16.69 with Ks−W1 ≳ 1 (Vega) is either a CatWISE blend/artifact in a
moderately crowded field or a genuinely very red object. NWAY rejects it at p_any = 4×10⁻⁶; it is
noted here because it is the only catalogued object that a (hypothetical, unevidenced) ~2″ X-ray
systematic could bring into play.

**X-ray-to-optical/IR ratio:** with F_X(0.2–2.3) = 1.59×10⁻¹² and no optical source to g ≈ 21,
log(f_X/f_opt) ≳ **+1.9** (Maccacaro-convention, g as V proxy;
[Maccacaro et al. 1988](https://ui.adsabs.harvard.edu/abs/1988ApJ...326..680M/abstract)); against
the W1 = 17.7 completeness limit (zero point 309.54 Jy,
[WISE Expl. Supp. §IV.4.h](https://wise2.ipac.caltech.edu/docs/release/allsky/expsup/sec4_4h.html)),
F_X/νF_ν(3.4 μm) ≳ **70** [computed]. AGN and normal stars live at log(f_X/f_opt) ≈ −1…+1;
ratios ≳ +2 are compact-object / obscured territory.

## 6. Riser-side artifact audit

Checks runnable against the local catalogs + UL server [all computed]; the M2 vanished-side
forensics ran the same modes in the fade direction.

**Excluded artifact modes:**

- **Crosswalk split/merge (reverse):** no other DR2 source shares |UID_DR1|; no second DR2 source
  within 60″; the two DR1 sources within 5′ (both faint, 262″/279″ away) each have their own DR2
  counterpart — no vanished DR1 neighbor whose flux could have been re-assigned here.
- **Source confusion / PSF blending:** nearest DR2 source of any kind is 166″ away at 0.017 ct/s
  (1% of target) — 5.5× the survey PSF HEW (~30″, [arXiv:2607.27772](https://arxiv.org/abs/2607.27772)).
- **Extended-emission absorption:** the source is point-like (EXT_LIKE = 0); nearest extended
  DR2 source is 370″ away with EXT_LIKE 5.5 (negligible).
- **Optical loading:** FLAG_OPT = 0, and the brightest star within 30″ is G = 16.4 — far below
  the loading regime (the consortium flags optical loading for very bright stars, §5.3 of the
  DR2 paper).
- **All consortium quality flags clean:** FLAG_SP_SNR/BPS/SCL/LGA/GC_CONS, FLAG_NO_RADEC_ERR,
  FLAG_NO_CTS_ERR all 0 in Main and Hard rows.
- **Moving object:** detected at the same position (1.67″) in Jan 2020 and in the 2019–2021
  stack — no solar-system object returns to the same ecliptic position over 1.4 yr of survey
  scans.
- **Catalog-fit fluke:** the UL server's aperture photometry (a different code path from the
  PSF-fitting catalog) independently shows the flux at the position (presence 14.1 soft / 2.7
  hard); 1637 aperture counts over 5.6 expected background.
- **Pileup:** 1.7 ct/s stacked is far below eROSITA pileup rates (pileup afflicts ≳ tens of ct/s
  sources, cf. SMC X-1's split detection in M2).

**Not excludable without event/image data (stated plainly):** single-visit detector artifacts
(ghost images, background-flare residuals leaking through the version-030 filter) cannot be ruled
out by catalog columns alone — DR2 ships no images (M1 §1), and the public DR1 images cover only
the *faint* epoch, so they cannot vet the bright state. Mitigation, not proof: the excess is
~2160 counts, it appears in two independent selections (Main 0.2–2.3 and Hard 2.3–5 likelihoods
9401/197), and at ELAT −70 the stack co-adds many separate telescope passes — a single-visit
artifact would have to survive averaging with ~2 clean visit windows. A short pointed observation
(§9) settles it definitively.

## 7. What can it be? (grounded in the data above)

Luminosity ladder for F(0.2–5) = 2.29×10⁻¹² [computed]: L_X ≈ 2.7×10³² (1 kpc), 2.5×10³³
(3 kpc), 1.7×10³⁴ (8 kpc), 6.9×10³⁵ (50 kpc), 2.7×10⁴² (100 Mpc), ~10⁴⁵ (z≈0.5).

| class | predicts | verdict on current evidence |
|---|---|---|
| **Be/HMXB outburst** | OB donor V ≲ 16–18 anywhere in the Galaxy (A_V here 0.4) | **excluded** — no optical source to g ≈ 21 ([Reig 2011](https://ui.adsabs.harvard.edu/abs/2011Ap%26SS.332....1R/abstract) for class properties) |
| **VFXT / subluminous LMXB transient** (NS/BH, faint donor) | L_peak 10³⁴–10³⁶, months-long outbursts, absorbed soft-to-moderate spectra, optically invisible donors; old population reaches high \|b\| | **fits at d ≳ 5 kpc**; nothing contradicts ([Wijnands et al. 2006](https://ui.adsabs.harvard.edu/abs/2006A%26A...449.1117W/abstract)) |
| **magnetic CV (IP) high state / long outburst** | L_X 10³²–10³⁴; donor invisible beyond ~1.5–2 kpc; year-scale high states possible | **fits at d ≳ 2 kpc**; sustained ×50 rise would be unusual but CV X-ray states vary ([Mukai 2017](https://ui.adsabs.harvard.edu/abs/2017PASP..129f2001M/abstract)) |
| **magnetar outburst** | L_X 10³⁴–10³⁶ decaying over months–years, kT ~ 0.5–1 keV — spectral shape compatible | **possible but disfavored**: magnetars sit in the plane (nearly all \|b\| ≲ 2°, [McGill catalog](https://www.physics.mcgill.ca/~pulsar/magnetar/main.html), [Olausen & Kaspi 2014](https://ui.adsabs.harvard.edu/abs/2014ApJS..212....6O/abstract)); b = −13.6° needs d ≲ 2 kpc or a halo outlier |
| **obscured AGN flare** | X-ray absorption ≫ Galactic (killed here: §4 shows only ~Galactic column) *and* a WISE-bright dusty nucleus (absent) | **strongly disfavored** in the standard sense; the object is radio-quiet too (§5) |
| **unobscured AGN / blazar flare** | host/nucleus at W1 ≲ 16–17 for any normal AGN at this F_X; blazars radio-loud | **excluded** except at z ≳ 0.3: a normal (≳0.1 L*) host ([Kochanek et al. 2001](https://ui.adsabs.harvard.edu/abs/2001ApJ...560..566K/abstract) K-band LF) would be visible in VHS/CatWISE to z ≈ 0.15–0.2; beyond that L_X ≳ 10⁴⁴–10⁴⁵ sustained → an eRASSt J234402-style "ignition" ([arXiv:2302.06989](https://arxiv.org/abs/2302.06989)), rare but real |
| **thermal TDE** | supersoft spectrum (excluded §4) + visible host (absent) | **disfavored** on both counts |

**Reading:** a Galactic compact accretor with an invisible companion — VFXT/subluminous-LMXB or
magnetic CV — explains every observable without strain; magnetar-like needs a latitude excuse;
extragalactic readings need z ≳ 0.3 and extreme luminosity. Between the Galactic options the
data cannot yet choose: that is exactly what one short pointed X-ray observation plus the
resulting arcsecond position would do.

## 8. Present-day state: unbounded (and by whom)

From [`out/m3_state_bounds.csv`](out/m3_state_bounds.csv) [computed 2026-08-16]:
**no Swift observation has ever contained the position** (LSXPS UL server: "NotObserved";
swiftmastr 17′ cone: 0 obs), **no pointed XMM** (xmmmaster: 0), **no Chandra** (chanmaster: 0);
control queries at LMC X-1 confirm the joins work. Combined with M2's archival sweep (2RXS,
XMMSL3 slews, CSC 2.1, 2SXPS, 5XMM, ART-XC): *the eROSITA survey is the only X-ray instrument
that has ever looked at this piece of sky deeply enough to matter, and its public record ends
2021-06.* eRASS4/5 exist but are unreleased (DR3 H2 2028,
[erosita.mpe.mpg.de/erass](https://erosita.mpe.mpg.de/erass/)). MAXI's all-sky sensitivity
(~mCrab) is orders too shallow at this flux. Nothing in TNS at the position (M2). The source
could today be anything from off to brighter than ever — **that is the case for the ToO.**

## 9. DRAFT ToO request — NOT SENT (Matthew's decision)

> **DRAFT — NOT SUBMITTED. Prepared for Matthew's review; submission (if any) is his action via
> his own account at https://www.swift.psu.edu/too/ . Nothing has been sent.**
>
> **Target:** 3eRASS J094452.8-711152 — RA 146.22033, Dec −71.19802 (ICRS), err 0.48″ (1σ)
> **Instrument/mode:** Swift XRT, PC mode; UVOT u (filter of the day acceptable)
> **Exposure:** 5 ks, single epoch; urgency: weeks (no fast trigger — the outburst epoch is
> 2020–2021; the science is the *present* state)
> **Science case:** an eROSITA-only X-ray transient/riser: faint in eRASS1 (3.4×10⁻¹⁴,
> 2020-01), ×47 brighter averaged over eRASS2/3 (1.6×10⁻¹², 0.2–2.3 keV; hard-band detected,
> F(2.3–5) = 7×10⁻¹³), no optical/IR counterpart to G≈21/Ks≈18/W1≈17.7, no radio counterpart
> (SUMSS/RACS), never observed by any pointed X-ray mission. Candidate nature: VFXT/subluminous
> LMXB outburst, magnetic CV, or magnetar-like transient. A single XRT snapshot decides
> (a) whether the source is still active — if at the stack-average level (~2×10⁻¹², 0.2–5 keV
> ~ 0.04–0.08 XRT ct/s for N_H ~ 10²¹, Γ ~ 2 — conversion approximate), PC mode collects
> ~200–400 counts in 5 ks: a spectrum (N_H, Γ/kT) and an enhanced position (~2″, cf.
> [Evans et al. 2023 LSXPS](https://ui.adsabs.harvard.edu/abs/2023MNRAS.518..174E/abstract))
> that shrinks the counterpart search to VHS/deep-imaging territory;
> (b) if undetected, the 3σ limit (~2×10⁻³ ct/s ≈ 1×10⁻¹³, XRT sensitivity
> [Burrows et al. 2005](https://ui.adsabs.harvard.edu/abs/2005SSRv..120..165B/abstract)) is
> ≥ ×20 below the stack average — establishing a transient (outburst over) rather than a
> persistent riser, which itself discriminates the classes (CV high states persist; VFXT
> outbursts end).
> **Alternative/escalation:** XMM 20–25 ks if the XRT result is a marginal detection
> (spectrum + timing); NICER only if bright (timing search for a spin period — IP/magnetar
> discriminant).

## 10. Provenance

Catalogs: eRASS3_Main_v1.3 / eRASS3_Hard_v1.2 / eRASS1_Main.v1.2 (local, M1 downloads);
NWAY counterpart values from M2 (`out/m2_counterparts.csv`). Services queried 2026-08-16,
all anonymous: eROSITA UL server ([API](https://erosita.mpe.mpg.de/erodat/apis/#upper-limits)),
IRSA dust, HEASARC w3nh + Xamin TAP, SkyMapper DR4 cone
([sm-cone](https://skymapper.anu.edu.au/how-to-access/)), TAPVizieR (Gaia DR3 I/355, CatWISE
II/365, VHS II/367, SUMSS VIII/81B, RACS J/other/PASA/38.58, 4FGL IX/72), legacysurvey.org
cutout probe, CDS hips2fits (finder), Swift LSXPS via `swifttools` 4.0.2 (unauthenticated
paths only). No accounts created; nothing submitted.

## 11. Appendix — complete catalog rows

<!-- FULL-ROWS-BELOW (auto-generated by scripts/m3_j0944_appendix.py from out/j0944_rows.json; do not hand-edit below this line) -->

### DR2 Main row (`eRASS3_Main_v1.3.fits`, all 250 columns)

| column | value | column | value |
|---|---|---|---|
| `IAUNAME` | 3eRASS J094452.8-711152 | `SKYTILE` | 149162 |
| `ID_SRC` | 3 | `ID_CLUSTER` | 3 |
| `DETUID` | sm03_149162_020_ML00003_001_c030 | `UID` | 314916200003 |
| `UID_5XMM` | -1 | `UID_CSC` | (empty) |
| `FLAG_CSC` | -1 | `UID_2RXS` | 0 |
| `UID_DR1` | 114916200171 | `UID_Hard` | 414916200003 |
| `RA` | 146.22 | `DEC` | -71.198 |
| `POS_ERR` | 0.480443 | `RA_LOWERR` | 0.214448 |
| `RA_UPERR` | 0.247047 | `DEC_LOWERR` | 0.237914 |
| `DEC_UPERR` | 0.234179 | `RADEC_ERR` | 0.330094 |
| `RA_RAW` | 146.22 | `DEC_RAW` | -71.198 |
| `LII` | 288.983 | `BII` | -13.5745 |
| `ELON` | 218.375 | `ELAT` | -70.0187 |
| `EXT` | 0 | `EXT_ERR` | 0 |
| `EXT_LOWERR` | 0 | `EXT_UPERR` | 0 |
| `EXT_LIKE` | 0 | `DET_LIKE_0` | 9401.14 |
| `ML_CTS_1` | 2181.16 | `ML_CTS_ERR_1` | 48.4537 |
| `ML_CTS_LOWERR_1` | 47.9638 | `ML_CTS_UPERR_1` | 48.9437 |
| `ML_RATE_1` | 1.708 | `ML_RATE_ERR_1` | 0.0379425 |
| `ML_RATE_LOWERR_1` | 0.0375588 | `ML_RATE_UPERR_1` | 0.0383262 |
| `ML_FLUX_1` | 1.59031e-12 | `ML_FLUX_ERR_1` | 3.53282e-14 |
| `ML_FLUX_LOWERR_1` | 3.4971e-14 | `ML_FLUX_UPERR_1` | 3.56854e-14 |
| `ML_BKG_1` | 7.88502 | `ML_EXP_1` | 1277.03 |
| `ML_EEF_1` | 0.883602 | `APE_CTS_1` | 1637 |
| `APE_BKG_1` | 5.58296 | `APE_EXP_1` | 1276.99 |
| `APE_RADIUS_1` | 7.6054 | `APE_POIS_1` | 0 |
| `DET_LIKE_P1` | 449.893 | `ML_CTS_P1` | 134.495 |
| `ML_CTS_ERR_P1` | 12.0159 | `ML_CTS_LOWERR_P1` | 11.637 |
| `ML_CTS_UPERR_P1` | 0.00955623 | `ML_RATE_P1` | 0.103694 |
| `ML_RATE_ERR_P1` | 0.00926409 | `ML_RATE_LOWERR_P1` | 0.00897194 |
| `ML_RATE_UPERR_P1` | 0.00955623 | `ML_FLUX_P1` | 1.12503e-13 |
| `ML_FLUX_ERR_P1` | 1.00511e-14 | `ML_FLUX_LOWERR_P1` | 9.73412e-15 |
| `ML_FLUX_UPERR_P1` | 1.03681e-14 | `ML_BKG_P1` | 1.88859 |
| `ML_EXP_P1` | 1297.04 | `ML_EEF_P1` | 0.892302 |
| `APE_CTS_P1` | 113 | `APE_BKG_P1` | 1.31973 |
| `APE_EXP_P1` | 1296.96 | `APE_RADIUS_P1` | 7.05462 |
| `APE_POIS_P1` | 0 | `DET_LIKE_P2` | 3522.32 |
| `ML_CTS_P2` | 842.651 | `ML_CTS_ERR_P2` | 30.1434 |
| `ML_CTS_LOWERR_P2` | 29.7013 | `ML_CTS_UPERR_P2` | 0.0235344 |
| `ML_RATE_P2` | 0.648388 | `ML_RATE_ERR_P2` | 0.0231942 |
| `ML_RATE_LOWERR_P2` | 0.022854 | `ML_RATE_UPERR_P2` | 0.0235344 |
| `ML_FLUX_P2` | 4.77107e-13 | `ML_FLUX_ERR_P2` | 1.70671e-14 |
| `ML_FLUX_LOWERR_P2` | 1.68168e-14 | `ML_FLUX_UPERR_P2` | 1.73175e-14 |
| `ML_BKG_P2` | 3.81202 | `ML_EXP_P2` | 1299.61 |
| `ML_EEF_P2` | 0.886942 | `APE_CTS_P2` | 618 |
| `APE_BKG_P2` | 2.84257 | `APE_EXP_P2` | 1299.58 |
| `APE_RADIUS_P2` | 7.29751 | `APE_POIS_P2` | 0 |
| `DET_LIKE_P3` | 5383.85 | `ML_CTS_P3` | 1136.04 |
| `ML_CTS_ERR_P3` | 34.8528 | `ML_CTS_LOWERR_P3` | 34.5066 |
| `ML_CTS_UPERR_P3` | 0.0275175 | `ML_RATE_P3` | 0.888117 |
| `ML_RATE_ERR_P3` | 0.0272468 | `ML_RATE_LOWERR_P3` | 0.0269761 |
| `ML_RATE_UPERR_P3` | 0.0275175 | `ML_FLUX_P3` | 8.75855e-13 |
| `ML_FLUX_ERR_P3` | 2.68706e-14 | `ML_FLUX_LOWERR_P3` | 2.66037e-14 |
| `ML_FLUX_UPERR_P3` | 2.71376e-14 | `ML_BKG_P3` | 2.41141 |
| `ML_EXP_P3` | 1279.15 | `ML_EEF_P3` | 0.883602 |
| `APE_CTS_P3` | 859 | `APE_BKG_P3` | 2.0777 |
| `APE_EXP_P3` | 1279.1 | `APE_RADIUS_P3` | 7.76115 |
| `APE_POIS_P3` | 0 | `DET_LIKE_P4` | 377.997 |
| `ML_CTS_P4` | 141.615 | `ML_CTS_ERR_P4` | 12.9009 |
| `ML_CTS_LOWERR_P4` | 12.4899 | `ML_CTS_UPERR_P4` | 0.0133555 |
| `ML_RATE_P4` | 0.14208 | `ML_RATE_ERR_P4` | 0.0129432 |
| `ML_RATE_LOWERR_P4` | 0.0125309 | `ML_RATE_UPERR_P4` | 0.0133555 |
| `ML_FLUX_P4` | 8.80841e-13 | `ML_FLUX_ERR_P4` | 8.0243e-14 |
| `ML_FLUX_LOWERR_P4` | 7.76868e-14 | `ML_FLUX_UPERR_P4` | 8.27993e-14 |
| `ML_BKG_P4` | 3.34693 | `ML_EXP_P4` | 996.731 |
| `ML_EEF_P4` | 0.856246 | `APE_CTS_P4` | 124 |
| `APE_BKG_P4` | 4.60791 | `APE_EXP_P4` | 996.671 |
| `APE_RADIUS_P4` | 9.87753 | `APE_POIS_P4` | 0 |
| `DET_LIKE_P5` | 0 | `ML_CTS_P5` | 0 |
| `ML_CTS_ERR_P5` | 2.31114 | `ML_CTS_LOWERR_P5` | 0 |
| `ML_CTS_UPERR_P5` | 0.00366567 | `ML_RATE_P5` | 0 |
| `ML_RATE_ERR_P5` | 0.00366567 | `ML_RATE_LOWERR_P5` | 0 |
| `ML_RATE_UPERR_P5` | 0.00366567 | `ML_FLUX_P5` | 0 |
| `ML_FLUX_ERR_P5` | 1.32049e-13 | `ML_FLUX_LOWERR_P5` | 0 |
| `ML_FLUX_UPERR_P5` | 1.32049e-13 | `ML_BKG_P5` | 2.76914 |
| `ML_EXP_P5` | 630.482 | `ML_EEF_P5` | 0.732981 |
| `APE_CTS_P5` | 9 | `APE_BKG_P5` | 6.85817 |
| `APE_EXP_P5` | 630.526 | `APE_RADIUS_P5` | 13.2973 |
| `APE_POIS_P5` | 0.252614 | `DET_LIKE_P6` | 4.78686 |
| `ML_CTS_P6` | 8.05502 | `ML_CTS_ERR_P6` | 4.17859 |
| `ML_CTS_LOWERR_P6` | 3.64632 | `ML_CTS_UPERR_P6` | 0.00702355 |
| `ML_RATE_P6` | 0.0120095 | `ML_RATE_ERR_P6` | 0.00622999 |
| `ML_RATE_LOWERR_P6` | 0.00543642 | `ML_RATE_UPERR_P6` | 0.00702355 |
| `ML_FLUX_P6` | 3.60645e-13 | `ML_FLUX_ERR_P6` | 1.87087e-13 |
| `ML_FLUX_LOWERR_P6` | 1.63256e-13 | `ML_FLUX_UPERR_P6` | 2.10918e-13 |
| `ML_BKG_P6` | 5.26623 | `ML_EXP_P6` | 670.722 |
| `ML_EEF_P6` | 0.732981 | `APE_CTS_P6` | 21 |
| `APE_BKG_P6` | 12.9978 | `APE_EXP_P6` | 670.708 |
| `APE_RADIUS_P6` | 13.2973 | `APE_POIS_P6` | 0.0249731 |
| `DET_LIKE_P7` | 0 | `ML_CTS_P7` | 0 |
| `ML_CTS_ERR_P7` | 0.813481 | `ML_CTS_LOWERR_P7` | 0 |
| `ML_CTS_UPERR_P7` | 0.00116975 | `ML_RATE_P7` | 0 |
| `ML_RATE_ERR_P7` | 0.00116975 | `ML_RATE_LOWERR_P7` | 0 |
| `ML_RATE_UPERR_P7` | 0.00116975 | `ML_FLUX_P7` | 0 |
| `ML_FLUX_ERR_P7` | 3.0518e-14 | `ML_FLUX_LOWERR_P7` | 0 |
| `ML_FLUX_UPERR_P7` | 3.0518e-14 | `ML_BKG_P7` | 0.9448 |
| `ML_EXP_P7` | 695.429 | `ML_EEF_P7` | 0.732981 |
| `APE_CTS_P7` | 2 | `APE_BKG_P7` | 1.93052 |
| `APE_EXP_P7` | 695.568 | `APE_RADIUS_P7` | 12.075 |
| `APE_POIS_P7` | 0.574861 | `DET_LIKE_P8` | 0.0235603 |
| `ML_CTS_P8` | 0.432914 | `ML_CTS_ERR_P8` | 1.66652 |
| `ML_CTS_LOWERR_P8` | 0.432914 | `ML_CTS_UPERR_P8` | 0.00498984 |
| `ML_RATE_P8` | 0.000744857 | `ML_RATE_ERR_P8` | 0.00286735 |
| `ML_RATE_LOWERR_P8` | 0.000744857 | `ML_RATE_UPERR_P8` | 0.00498984 |
| `ML_FLUX_P8` | 3.39652e-14 | `ML_FLUX_ERR_P8` | 1.3075e-13 |
| `ML_FLUX_LOWERR_P8` | 3.39652e-14 | `ML_FLUX_UPERR_P8` | 2.27535e-13 |
| `ML_BKG_P8` | 0.866661 | `ML_EXP_P8` | 581.204 |
| `ML_EEF_P8` | 0.732981 | `APE_CTS_P8` | 4 |
| `APE_BKG_P8` | 2.155 | `APE_EXP_P8` | 581.218 |
| `APE_RADIUS_P8` | 13.2973 | `APE_POIS_P8` | 0.171873 |
| `DET_LIKE_P9` | 0 | `ML_CTS_P9` | 0 |
| `ML_CTS_ERR_P9` | 0.682526 | `ML_CTS_LOWERR_P9` | 0 |
| `ML_CTS_UPERR_P9` | 0.00126638 | `ML_RATE_P9` | 0 |
| `ML_RATE_ERR_P9` | 0.00126638 | `ML_RATE_LOWERR_P9` | 0 |
| `ML_RATE_UPERR_P9` | 0.00126638 | `ML_FLUX_P9` | 0 |
| `ML_FLUX_ERR_P9` | 1.02541e-13 | `ML_FLUX_LOWERR_P9` | 0 |
| `ML_FLUX_UPERR_P9` | 1.02541e-13 | `ML_BKG_P9` | 0.873045 |
| `ML_EXP_P9` | 538.958 | `ML_EEF_P9` | 0.700575 |
| `APE_CTS_P9` | 2 | `APE_BKG_P9` | 2.15884 |
| `APE_EXP_P9` | 538.937 | `APE_RADIUS_P9` | 13.2973 |
| `APE_POIS_P9` | 0.635284 | `FLAG_SP_SNR` | 0 |
| `FLAG_SP_BPS` | 0 | `FLAG_SP_SCL` | 0 |
| `FLAG_SP_LGA` | 0 | `FLAG_SP_GC_CONS` | 0 |
| `FLAG_NO_RADEC_ERR` | 0 | `FLAG_NO_EXT_ERR` | 0 |
| `FLAG_NO_CTS_ERR` | 0 | `FLAG_OPT` | 0 |

### DR2 Hard row (`eRASS3_Hard_v1.2.fits`, all 111 columns)

| column | value | column | value |
|---|---|---|---|
| `IAUNAME` | 3eRASS J094452.8-711152 | `DETUID` | sm03_149162_020_ML00003_001_c030 |
| `SKYTILE` | 149162 | `ID_SRC` | 3 |
| `UID` | 414916200003 | `UID_5XMM` | -1 |
| `UID_2RXS` | 0 | `UID_CSC` | (empty) |
| `FLAG_CSC` | -1 | `UID_DR1Hard` | 0 |
| `UID_Main` | 314916200003 | `ID_CLUSTER` | 3 |
| `RA` | 146.22 | `DEC` | -71.198 |
| `RA_LOWERR` | 0.212336 | `RA_UPERR` | 0.264411 |
| `DEC_LOWERR` | 0.23232 | `DEC_UPERR` | 0.228952 |
| `POS_ERR` | 0.481154 | `RADEC_ERR` | 0.331685 |
| `RA_RAW` | 146.22 | `DEC_RAW` | -71.198 |
| `LII` | 288.984 | `BII` | -13.5743 |
| `ELON` | 218.375 | `ELAT` | -70.0187 |
| `EXT` | 0 | `EXT_ERR` | 0 |
| `EXT_LOWERR` | 0 | `EXT_UPERR` | 0 |
| `EXT_LIKE` | 0 | `ML_CTS_0` | 2260.2 |
| `ML_CTS_ERR_0` | 49.3895 | `ML_RATE_0` | 1.77943 |
| `ML_RATE_ERR_0` | 0.0390094 | `ML_FLUX_0` | 2.28902e-12 |
| `ML_FLUX_ERR_0` | 9.45522e-14 | `DET_LIKE_0` | 9825.84 |
| `ML_BKG_0` | 11.1144 | `ML_CTS_1` | 259.515 |
| `ML_CTS_ERR_1` | 16.8213 | `ML_CTS_LOWERR_1` | 16.5241 |
| `ML_CTS_UPERR_1` | 17.1185 | `ML_RATE_1` | 0.200491 |
| `ML_RATE_ERR_1` | 0.0129954 | `ML_RATE_LOWERR_1` | 0.0127658 |
| `ML_RATE_UPERR_1` | 0.013225 | `ML_FLUX_1` | 1.9503e-13 |
| `ML_FLUX_ERR_1` | 1.26415e-14 | `ML_FLUX_LOWERR_1` | 1.24181e-14 |
| `ML_FLUX_UPERR_1` | 1.28648e-14 | `DET_LIKE_1` | 889.856 |
| `ML_BKG_1` | 3.10792 | `ML_EXP_1` | 1294.4 |
| `ML_EEF_1` | 0.892302 | `APE_CTS_1` | 210 |
| `APE_BKG_1` | 2.26661 | `APE_EXP_1` | 1294.33 |
| `APE_RADIUS_1` | 7.08482 | `APE_POIS_1` | 0 |
| `ML_CTS_2` | 1922.25 | `ML_CTS_ERR_2` | 45.431 |
| `ML_CTS_LOWERR_2` | 44.9338 | `ML_CTS_UPERR_2` | 45.9283 |
| `ML_RATE_2` | 1.49669 | `ML_RATE_ERR_2` | 0.0353733 |
| `ML_RATE_LOWERR_2` | 0.0349861 | `ML_RATE_UPERR_2` | 0.0357605 |
| `ML_FLUX_2` | 1.3769e-12 | `ML_FLUX_ERR_2` | 3.25421e-14 |
| `ML_FLUX_LOWERR_2` | 3.21859e-14 | `ML_FLUX_UPERR_2` | 3.28983e-14 |
| `DET_LIKE_2` | 8752.34 | `ML_BKG_2` | 5.13372 |
| `ML_EXP_2` | 1284.33 | `ML_EEF_2` | 0.883602 |
| `APE_CTS_2` | 1443 | `APE_BKG_2` | 3.48825 |
| `APE_EXP_2` | 1284.29 | `APE_RADIUS_2` | 7.7299 |
| `APE_POIS_2` | 0 | `ML_CTS_3` | 78.4404 |
| `ML_CTS_ERR_3` | 9.6119 | `ML_CTS_LOWERR_3` | 9.21334 |
| `ML_CTS_UPERR_3` | 10.0105 | `ML_RATE_3` | 0.0822507 |
| `ML_RATE_ERR_3` | 0.0100788 | `ML_RATE_LOWERR_3` | 0.00966089 |
| `ML_RATE_UPERR_3` | 0.0104967 | `ML_FLUX_3` | 7.17094e-13 |
| `ML_FLUX_ERR_3` | 8.7871e-14 | `ML_FLUX_LOWERR_3` | 8.42274e-14 |
| `ML_FLUX_UPERR_3` | 9.15146e-14 | `DET_LIKE_3` | 197.152 |
| `ML_BKG_3` | 2.87281 | `ML_EXP_3` | 953.675 |
| `ML_EEF_3` | 0.856246 | `APE_CTS_3` | 72 |
| `APE_BKG_3` | 4.08399 | `APE_EXP_3` | 953.6 |
| `APE_RADIUS_3` | 10.0245 | `APE_POIS_3` | 0 |
| `FLAG_SP_SNR` | 0 | `FLAG_SP_BPS` | 0 |
| `FLAG_SP_SCL` | 0 | `FLAG_SP_LGA` | 0 |
| `FLAG_SP_GC_CONS` | 0 | `FLAG_NO_RADEC_ERR` | 0 |
| `FLAG_NO_EXT_ERR` | 0 | `FLAG_NO_CTS_ERR` | 0 |
| `FLAG_OPT` | 0 |  |  |

### DR1 row (`eRASS1_Main.v1.2.fits`, all 252 columns)

| column | value | column | value |
|---|---|---|---|
| `IAUNAME` | 1eRASS J094453.1-711153 | `DETUID` | em01_149162_020_ML00171_002_c010 |
| `SKYTILE` | 149162 | `ID_SRC` | 171 |
| `UID` | 114916200171 | `UID_Hard` | 0 |
| `ID_CLUSTER` | 163 | `RA` | 146.222 |
| `DEC` | -71.1982 | `RA_RAW` | 146.222 |
| `DEC_RAW` | -71.1992 | `RA_LOWERR` | 2.28887 |
| `RA_UPERR` | 2.28172 | `DEC_LOWERR` | 2.81468 |
| `DEC_UPERR` | 2.59387 | `POS_ERR` | 2.75669 |
| `RADEC_ERR` | 3.23189 | `LII` | 288.985 |
| `BII` | -13.5747 | `ELON` | 218.378 |
| `ELAT` | -70.0186 | `MJD` | 58874.6 |
| `MJD_MIN` | 58872.5 | `MJD_MAX` | 58877 |
| `EXT` | 0 | `EXT_ERR` | 0 |
| `EXT_LOWERR` | 0 | `EXT_UPERR` | 0 |
| `EXT_LIKE` | 0 | `DET_LIKE_0` | 25.2987 |
| `ML_CTS_1` | 17.8598 | `ML_CTS_ERR_1` | 4.88057 |
| `ML_CTS_LOWERR_1` | 4.50802 | `ML_CTS_UPERR_1` | 5.25312 |
| `ML_RATE_1` | 0.0367448 | `ML_RATE_ERR_1` | 0.0100413 |
| `ML_RATE_LOWERR_1` | 0.0092748 | `ML_RATE_UPERR_1` | 0.0108078 |
| `ML_FLUX_1` | 3.4213e-14 | `ML_FLUX_ERR_1` | 9.34943e-15 |
| `ML_FLUX_LOWERR_1` | 8.63576e-15 | `ML_FLUX_UPERR_1` | 1.00631e-14 |
| `ML_BKG_1` | 2.99284 | `ML_EXP_1` | 486.05 |
| `ML_EEF_1` | 0.883602 | `APE_CTS_1` | 18 |
| `APE_BKG_1` | 2.4244 | `APE_EXP_1` | 486.105 |
| `APE_RADIUS_1` | 7.62777 | `APE_POIS_1` | 1.32577e-10 |
| `DET_LIKE_P1` | 16.3031 | `ML_CTS_P1` | 9.1606 |
| `ML_CTS_ERR_P1` | 3.39826 | `ML_CTS_LOWERR_P1` | 3.05149 |
| `ML_CTS_UPERR_P1` | 3.74503 | `ML_RATE_P1` | 0.0185601 |
| `ML_RATE_ERR_P1` | 0.00688513 | `ML_RATE_LOWERR_P1` | 0.00618255 |
| `ML_RATE_UPERR_P1` | 0.00758772 | `ML_FLUX_P1` | 2.01368e-14 |
| `ML_FLUX_ERR_P1` | 7.47004e-15 | `ML_FLUX_LOWERR_P1` | 6.70777e-15 |
| `ML_FLUX_UPERR_P1` | 8.23231e-15 | `ML_BKG_P1` | 0.668286 |
| `ML_EXP_P1` | 493.564 | `ML_EEF_P1` | 0.892302 |
| `APE_CTS_P1` | 8 | `APE_BKG_P1` | 0.466469 |
| `APE_EXP_P1` | 493.531 | `APE_RADIUS_P1` | 7.0772 |
| `APE_POIS_P1` | 3.67672e-08 | `DET_LIKE_P2` | 7.51975 |
| `ML_CTS_P2` | 5.92705 | `ML_CTS_ERR_P2` | 2.87417 |
| `ML_CTS_LOWERR_P2` | 2.47792 | `ML_CTS_UPERR_P2` | 3.27042 |
| `ML_RATE_P2` | 0.0119855 | `ML_RATE_ERR_P2` | 0.00581205 |
| `ML_RATE_LOWERR_P2` | 0.00501076 | `ML_RATE_UPERR_P2` | 0.00661333 |
| `ML_FLUX_P2` | 8.81933e-15 | `ML_FLUX_ERR_P2` | 4.27671e-15 |
| `ML_FLUX_LOWERR_P2` | 3.68709e-15 | `ML_FLUX_UPERR_P2` | 4.86632e-15 |
| `ML_BKG_P2` | 1.39842 | `ML_EXP_P2` | 494.52 |
| `ML_EEF_P2` | 0.886942 | `APE_CTS_P2` | 5 |
| `APE_BKG_P2` | 1.06363 | `APE_EXP_P2` | 494.729 |
| `APE_RADIUS_P2` | 7.32 | `APE_POIS_P2` | 0.00473164 |
| `DET_LIKE_P3` | 5.74039 | `ML_CTS_P3` | 3.37334 |
| `ML_CTS_ERR_P3` | 2.06896 | `ML_CTS_LOWERR_P3` | 1.65709 |
| `ML_CTS_UPERR_P3` | 2.48083 | `ML_RATE_P3` | 0.00692929 |
| `ML_RATE_ERR_P3` | 0.00424992 | `ML_RATE_LOWERR_P3` | 0.00340389 |
| `ML_RATE_UPERR_P3` | 0.00509595 | `ML_FLUX_P3` | 6.83362e-15 |
| `ML_FLUX_ERR_P3` | 4.19124e-15 | `ML_FLUX_LOWERR_P3` | 3.35689e-15 |
| `ML_FLUX_UPERR_P3` | 5.02559e-15 | `ML_BKG_P3` | 0.944252 |
| `ML_EXP_P3` | 486.823 | `ML_EEF_P3` | 0.883602 |
| `APE_CTS_P3` | 3 | `APE_BKG_P3` | 0.790359 |
| `APE_EXP_P3` | 486.948 | `APE_RADIUS_P3` | 7.78346 |
| `APE_POIS_P3` | 0.0460464 | `DET_LIKE_P4` | 1.45762 |
| `ML_CTS_P4` | 2.27085 | `ML_CTS_ERR_P4` | 2.01902 |
| `ML_CTS_LOWERR_P4` | 1.59662 | `ML_CTS_UPERR_P4` | 2.44141 |
| `ML_RATE_P4` | 0.00598961 | `ML_RATE_ERR_P4` | 0.00532536 |
| `ML_RATE_LOWERR_P4` | 0.00421125 | `ML_RATE_UPERR_P4` | 0.00643947 |
| `ML_FLUX_P4` | 3.71333e-14 | `ML_FLUX_ERR_P4` | 3.30153e-14 |
| `ML_FLUX_LOWERR_P4` | 2.61082e-14 | `ML_FLUX_UPERR_P4` | 3.99223e-14 |
| `ML_BKG_P4` | 1.19648 | `ML_EXP_P4` | 379.133 |
| `ML_EEF_P4` | 0.856246 | `APE_CTS_P4` | 4 |
| `APE_BKG_P4` | 1.6281 | `APE_EXP_P4` | 379.225 |
| `APE_RADIUS_P4` | 9.9188 | `APE_POIS_P4` | 0.082734 |
| `DET_LIKE_P5` | 0 | `ML_CTS_P5` | 0 |
| `ML_CTS_ERR_P5` | 1.01067 | `ML_CTS_LOWERR_P5` | 0 |
| `ML_CTS_UPERR_P5` | 1.01067 | `ML_RATE_P5` | 0 |
| `ML_RATE_ERR_P5` | 0.00421493 | `ML_RATE_LOWERR_P5` | 0 |
| `ML_RATE_UPERR_P5` | 0.00421493 | `ML_FLUX_P5` | 0 |
| `ML_FLUX_ERR_P5` | 1.51835e-13 | `ML_FLUX_LOWERR_P5` | 0 |
| `ML_FLUX_UPERR_P5` | 1.51835e-13 | `ML_BKG_P5` | 1.00928 |
| `ML_EXP_P5` | 239.783 | `ML_EEF_P5` | 0.732981 |
| `APE_CTS_P5` | 3 | `APE_BKG_P5` | 2.53383 |
| `APE_EXP_P5` | 239.796 | `APE_RADIUS_P5` | 13.3626 |
| `APE_POIS_P5` | 0.464836 | `DET_LIKE_P6` | 0.0204856 |
| `ML_CTS_P6` | 0.329488 | `ML_CTS_ERR_P6` | 1.36158 |
| `ML_CTS_LOWERR_P6` | 0.329488 | `ML_CTS_UPERR_P6` | 2.39367 |
| `ML_RATE_P6` | 0.00129175 | `ML_RATE_ERR_P6` | 0.00533804 |
| `ML_RATE_LOWERR_P6` | 0.00129175 | `ML_RATE_UPERR_P6` | 0.00938433 |
| `ML_FLUX_P6` | 3.87914e-14 | `ML_FLUX_ERR_P6` | 1.60302e-13 |
| `ML_FLUX_LOWERR_P6` | 3.87914e-14 | `ML_FLUX_UPERR_P6` | 2.81812e-13 |
| `ML_BKG_P6` | 1.84478 | `ML_EXP_P6` | 255.07 |
| `ML_EEF_P6` | 0.732981 | `APE_CTS_P6` | 6 |
| `APE_BKG_P6` | 4.63359 | `APE_EXP_P6` | 255.103 |
| `APE_RADIUS_P6` | 13.3626 | `APE_POIS_P6` | 0.320044 |
| `DET_LIKE_P7` | 0 | `ML_CTS_P7` | 0 |
| `ML_CTS_ERR_P7` | 0.644545 | `ML_CTS_LOWERR_P7` | 0 |
| `ML_CTS_UPERR_P7` | 0.644545 | `ML_RATE_P7` | 0 |
| `ML_RATE_ERR_P7` | 0.00243386 | `ML_RATE_LOWERR_P7` | 0 |
| `ML_RATE_UPERR_P7` | 0.00243386 | `ML_FLUX_P7` | 0 |
| `ML_FLUX_ERR_P7` | 6.34975e-14 | `ML_FLUX_LOWERR_P7` | 0 |
| `ML_FLUX_UPERR_P7` | 6.34975e-14 | `ML_BKG_P7` | 0.338156 |
| `ML_EXP_P7` | 264.824 | `ML_EEF_P7` | 0.732981 |
| `APE_CTS_P7` | 1 | `APE_BKG_P7` | 0.693939 |
| `APE_EXP_P7` | 264.569 | `APE_RADIUS_P7` | 12.1354 |
| `APE_POIS_P7` | 0.500396 | `DET_LIKE_P8` | 0 |
| `ML_CTS_P8` | 0 | `ML_CTS_ERR_P8` | 1.59557 |
| `ML_CTS_LOWERR_P8` | 0 | `ML_CTS_UPERR_P8` | 1.59557 |
| `ML_RATE_P8` | 0 | `ML_RATE_ERR_P8` | 0.00722345 |
| `ML_RATE_LOWERR_P8` | 0 | `ML_RATE_UPERR_P8` | 0.00722345 |
| `ML_FLUX_P8` | 0 | `ML_FLUX_ERR_P8` | 3.29387e-13 |
| `ML_FLUX_LOWERR_P8` | 0 | `ML_FLUX_UPERR_P8` | 3.29387e-13 |
| `ML_BKG_P8` | 0.315062 | `ML_EXP_P8` | 220.888 |
| `ML_EEF_P8` | 0.732981 | `APE_CTS_P8` | 2 |
| `APE_BKG_P8` | 0.791672 | `APE_EXP_P8` | 221.005 |
| `APE_RADIUS_P8` | 13.3626 | `APE_POIS_P8` | 0.188218 |
| `DET_LIKE_P9` | 0 | `ML_CTS_P9` | 0 |
| `ML_CTS_ERR_P9` | 0.727273 | `ML_CTS_LOWERR_P9` | 0 |
| `ML_CTS_UPERR_P9` | 0.727273 | `ML_RATE_P9` | 0 |
| `ML_RATE_ERR_P9` | 0.00354855 | `ML_RATE_LOWERR_P9` | 0 |
| `ML_RATE_UPERR_P9` | 0.00354855 | `ML_FLUX_P9` | 0 |
| `ML_FLUX_ERR_P9` | 2.87332e-13 | `ML_FLUX_LOWERR_P9` | 0 |
| `ML_FLUX_UPERR_P9` | 2.87332e-13 | `ML_BKG_P9` | 0.306295 |
| `ML_EXP_P9` | 204.949 | `ML_EEF_P9` | 0.700575 |
| `APE_CTS_P9` | 0 | `APE_BKG_P9` | 0.769727 |
| `APE_EXP_P9` | 204.959 | `APE_RADIUS_P9` | 13.3626 |
| `APE_POIS_P9` | NaN | `APE_CTS_S` | 8 |
| `APE_BKG_S` | 1.85399 | `APE_EXP_S` | 491.702 |
| `APE_POIS_S` | 0.000678729 | `FLAG_SP_SNR` | 0 |
| `FLAG_SP_BPS` | 0 | `FLAG_SP_SCL` | 0 |
| `FLAG_SP_LGA` | 0 | `FLAG_SP_GC_CONS` | 0 |
| `FLAG_NO_RADEC_ERR` | 0 | `FLAG_NO_EXT_ERR` | 0 |
| `FLAG_NO_CTS_ERR` | 0 | `FLAG_OPT` | 0 |
