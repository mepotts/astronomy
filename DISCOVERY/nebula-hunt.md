# Nebula hunt — planetary nebula candidates in unsearched narrowband surveys

**One-liner:** Search Hα/[OIII] survey imagery that the professionals have publicly stated is unsearched,
submit candidates to the HASH database via the French 2SPOT group, and receive a discoverer-initials
designation forwarded to CDS.

**Official recognition: PARTIAL.** You get a **your-initials designation** (e.g. `StDr 1`, `Kn 61`,
`Pa 30`) recorded in HASH and forwarded to CDS, plus co-authorship when the object is written up. You do
**not** get an IAU designation — the permanent identifier is `PN GLLL.l±BB.b`, assigned on confirmation.
⚠️ Most amateur prefixes are **not CDS-registered**: `DSH` is; **`StDr` and `SDSO` are not** — SIMBAD will
not resolve them, so query by coordinates.

**Scores (U/B/E):** U **4/5** (professionals have said in print which archives are unsearched) ·
B **4/5** (image + catalogue cross-matching, no pixel-level reduction) · E **3/5** (real designation, but
confirmation requires spectroscopy you cannot do)

**Status:** proposed

**Cost to operate: $0**

---

## Why this is open, in the professionals' own words

Li, Parker & Jia (2024), **A&A 692, A103** — a Swin-Transformer trained on IPHAS/HASH labels, applied to
~2,000 deg² of VPHAS+, produced **>800 high-quality candidates at 70.97% spectroscopic success**. The
paper states VPHAS+ *"has not yet undergone extensive manual, systematic searching."*

That is Quentin Parker's own group — the people who maintain HASH — publishing that a major archive is
unmined. Only **~3,500–4,000 Galactic PNe are known against an estimated ~25,000**.

**Track record that this is real:** Le Dû, Mulato, Parker, Petit, Ritter, **Drechsler, Strottner, Patchick,
Prestgard, Garde, Outters, Raffaelli** (2022), **A&A 666, A152** — 209 spectroscopically confirmed PNe,
≈**5% of the entire Galactic PN inventory**, with **11 of 13 authors amateur**.

Highest-impact amateur archival find ever: **Dana Patchick's** DSS candidate **Pa 30** turned out to be the
remnant of **SN 1181 CE**, a Type Iax supernova (Fesen, Schaefer, Patchick, **ApJL 945, L4, 2023**).

---

## Where to look

| Archive | Access | Why |
|---|---|---|
| **VPHAS+** | via CDS hips2fits `CDS/P/VPHAS/DR4/Halpha` | **Declared unsearched in print.** The headline target |
| **MDW Hα Sky Survey** ⭐ | `https://mdw.astro.columbia.edu/` | Founded by amateurs (Mittelman, di Cicco, Walker), Columbia joined 2022. **4,120 fields, 3.6°×3.6°, 4 hr each, 3.17″/px, 3 nm Hα.** DR1 (Jan 2025) = entire northern sky; **DR2 = first full-sky release, end of 2026**. Free FITS + catalogs |
| **simg.de** (Ziegenbalg) | `https://simg.de` | Northern Sky Narrowband Survey, Hα/[OIII]/[SII], DR0.2 May 2025. **This is the archive the JAM 2/3/4 ghost-PN discoveries were mined from** |
| **S-PLUS DR4** | Data Lab `splus_dr4.dual` | **80,155,547 objects** with narrowband `j0660` (Hα) and `j0515` ([OIII]) — confirmed columns. Catalogue-space PN selection at scale |
| IPHAS, SHASSA, VTSS | hips2fits | Comparison epochs and mimic rejection |
| WISE / GALEX / Gaia DR3 | Data Lab, TAP | Colour-based mimic rejection and central-star identification |

---

## Submission

**Protocol:** `https://planetarynebulae.net/EN/collecte_donnees.php` — verify not instrumental → check
other wavelengths (DSS/Pan-STARRS/DECaPS) → check Aladin/HASH/French Lists → match Frew & Parker 2010
morphology → **email `pascal.ledu@2spot.org`**.

> *"The object is baptized with the initials of the name of the discoverer followed by a number…
> subsequently forwarded to CDS, to the HASH database and may be the subject of an article."*

Live counts at planetarynebulae.net: **1,295 entries, 559 unpublished PN candidates, 167 discoverer
prefixes.**

**HASH:** `http://hashpn.space` → `http://202.189.117.101:8999/gpne/`. ⚠️ **There is no `hash-pn.org`.**
Password-gated but **registration is open to anyone** — no affiliation enforced. Contact
`hashpn.db@gmail.com`. Grades **True / Likely / Possible**; ~2,670 T / 464 L / 696 P Galactic; 11,460
entries; ~500,000 FITS cutouts from 24 surveys. Cite Parker, Bojičić & Frew 2016.

**Deep Sky Hunters** (`https://groups.io/g/deepskyhunters`, 68 members) remains active and **`DSH` is a
CDS-registered acronym** (~800 objects, dictionary updated 2026-07-10). Canonical 9-step archival recipe:
Jacoby, Kronberger, Patchick et al. (2010), **PASA 27, 156** (arXiv:0910.0465).

---

## The wall, stated plainly

**"True PN" grade requires spectroscopy**, and confirmation exposures are brutal: StDr 140 took ~76 h,
**JAM 2 took 131 h in [OIII]**, SDSO 1 took 111 h. You can be **discoverer of record and a co-author**;
you must hand off confirmation to someone with a telescope and patience.

**There is also no priority mechanism.** No registry timestamps a claim. **JAM 2 was already privately in
HASH**, entered by D. J. Frew and never made public; **JAM 4 = Celnik's TBG-N1**, found independently the
same year. 559 candidates sit unpublished right now. **Publish or be scooped silently.**

---

## Milestones

**M0 — kill-check (~1 day).** Register at HASH. Then take **10 known PNe of varying grade** and confirm
your Hα/[OIII] selection recovers them from public imagery. *If you cannot re-find known PNe, you will not
find new ones.*

**M1 — mimic rejection.** The hard part. PN mimics include HII regions, SNRs, reflection nebulae, and
plate artifacts. Build the colour/morphology cuts and measure your contamination rate against HASH's
graded catalogue — which is an unusually good labelled dataset for exactly this.

**M2 — candidate list from VPHAS+ or MDW**, cross-checked against HASH, SIMBAD, and the French lists.

**M3 — submit to `pascal.ledu@2spot.org`** and open a confirmation conversation.

**M4 — publish.** **RNAAS** precedent exists with an all-amateur author list: Mishra, **Patchick**, Mohan,
Rasool (2026), *"Discovery of a Large [O III]-dominant Emission Nebula in Monoceros: PaRasMoMi-1"*,
**RNAAS 10, 100** — all four listed as *"Independent Researcher."*

---

## Sources

- HASH: `http://hashpn.space` · `hashpn.db@gmail.com`
- French group / submission: `https://planetarynebulae.net/EN/collecte_donnees.php` · `pascal.ledu@2spot.org`
- Deep Sky Hunters: `https://groups.io/g/deepskyhunters` · method paper arXiv:0910.0465
- VPHAS+ ML precedent: **A&A 692, A103** (Li, Parker & Jia 2024)
- Amateur PN anchor paper: **A&A 666, A152** (Le Dû et al. 2022)
- Pa 30 / SN 1181: **ApJL 945, L4 (2023)**
- MDW: `https://mdw.astro.columbia.edu/` · simg: `https://simg.de` · hips2fits: `https://alasky.cds.unistra.fr/hips-image-services/hips2fits`
