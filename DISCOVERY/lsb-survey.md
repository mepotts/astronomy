# LSB survey — stellar streams and dwarf galaxies in public deep imaging

**One-liner:** Systematically search DESI Legacy Survey DR10 imaging for low-surface-brightness structures
— tidal streams, shells, ultra-diffuse and dwarf galaxies — in the sky nobody has looked at yet, and
publish through a collaboration that has co-authored amateurs for fifteen years.

**Official recognition: NO.** ⚠️ **There is no registry, timestamping service, or priority-claiming
mechanism for static extragalactic objects.** TNS is explicitly *"for reporting new astronomical
transients"* and excludes non-transients. **Priority is established only by publication.** You cannot claim
a find and work it up later; you can be scooped silently. Credit here means **named co-authorship**, not a
designation.

**Scores (U/B/E):** U **3/5** (catalogue construction is saturated; the *unsearched-sky* problem is not) ·
B **4/5** (anonymous ADQL + cutout APIs) · E **4/5** (A&A/RNAAS co-authorship is demonstrably reachable)

**Status:** proposed

**Cost to operate: $0**

---

## The proof case

arXiv:2510.24836, **RNAAS 9, 292 (2025)** — *"A stellar stream around the spiral galaxy Messier 61 in Rubin
First Look imaging."* Five authors, one an unaffiliated Italian amateur (**Giuseppe Donatiello**). First
stellar stream ever found with Rubin. ~50 kpc, µ_g ≈ 28. **Found in a public press-release image** — the
15.1 GB Virgo "Cosmic Treasure Chest" TIFF.

**Donatiello is the template.** No affiliation, now a routine A&A co-author. Donatiello II/III/IV (**A&A
652, A48**) came from *visual inspection of DECam images in the DESI Legacy Surveys* — and **Donatiello II
was missed by the detection algorithm**. Twelve Local Volume dwarfs, three Local Group.

**The open door:** David Martínez-Delgado (IAA-CSIC) has given amateurs full co-authorship for 15 years —
arXiv:2504.02071, **A&A 701, A182 (2025)**, 28 authors including eight amateurs.

---

## The sobering counterpoint — and what it tells you

Professional David Sand found three dwarf galaxies (arXiv:2409.16345, ApJL) by *"watching TV and scrolling
through the DESI Legacy Survey viewer, focusing on areas I knew hadn't been searched."*

**Your differentiator is not tooling and not technique. It is solving the "which sky is unsearched"
database problem** — and that is a problem you can actually solve with code, by cross-referencing published
survey footprints, existing catalogues, and coverage maps to produce a defensible map of unexamined sky.
Nobody has published that map. It would be useful to everyone working this field, including as a standalone
contribution.

## Where the ground is genuinely open

1. **Citizen-science LSB detection has never existed.** An arXiv search for `"ultra-diffuse" AND "citizen
   science"` and `"low surface brightness" AND "citizen science"` returns **0 results each** — while the
   best professional pipeline (SMUDGes) still terminates in **two-person by-eye vetting with ~15%
   inter-reviewer disagreement**. That is the clearest structural gap in the whole landscape.
2. **DESI LS DR10's i-band.** SMUDGes V (**7,070 UDG candidates over 20,000 deg²**) is **DR9-based**; DR10's
   new colour space is not fully exploited.
3. **Streams and shells around *dwarf* hosts.** Sakowska et al., **A&A 707, L1 (2026)** inspected only 730
   dwarfs in the DES footprint and found **5.1% show accretion features**. The authors flag the DECaLS
   footprint as open.
4. **Galactic cirrus / IFN** — universally treated as contamination to be masked, never catalogued.

**Saturated — do not start here:** UDG/LSBG catalogue construction in DES/DECaLS/KiDS. Tanoglidis et al.
found 23,790 LSBGs in DES; Thuruthipilly et al. added 4,083 via transformers; arXiv:2605.13842 (May 2026)
found **20,180 LSBGs and 434 UDGs in KiDS DR5** via domain adaptation. The ML frontier moves faster than
you can. Note also the SMUDGes rejection rate: **3,574,596 raw detections → 275 final Coma UDGs (99.992%
rejected)**. Your first hundred candidates will all be artifacts.

---

## Data access

**NOIRLab Astro Data Lab, anonymous ADQL, no account:** `https://datalab.noirlab.edu/tap`
- `ls_dr10.tractor` — **3,145,841,852 rows**, 214 columns
- `ls_dr10.photo_z` — 2,827,055,986
- `sga2020.ellipse` / `.zoobot` — Siena Galaxy Atlas + morphology
- Pre-computed 1.5″ cross-match tables (`x1p5__…`) to Gaia DR3, unWISE, SDSS — removes the hardest step

**Cutouts:** CDS hips2fits against `CDS/P/DESI-Legacy-Surveys/DR10/{color,g,r,i,z}` — no auth, FITS or JPG,
any position/FOV. ⚠️ `legacysurvey.org` itself was unreachable during research (NERSC **"Major Power
Upgrade" outage 22 July – 3 Aug 2026**) — hips2fits and Data Lab are the resilient routes.

**Toolchain:** Gnuastro/**NoiseChisel**, GALFIT, photutils 3.0, à trous wavelet transform, extended-PSF
(Moffat wing) subtraction. Systematics dominate at µ ~ 28–29 — PSF wings and flat-fielding residuals *are*
the science.

---

## Milestones

**M0 — calibration kill-check.** Reproduce **SMUDGes on DR10** for the Coma field. *If you recover their
275 UDGs, your systematics handling is real.* If you cannot, nothing downstream is trustworthy.

**M1 — the unsearched-sky map.** Cross-reference published footprints (SMUDGes, DES LSBG, Sakowska,
Miró-Carretero, SSLS) against DR10 coverage. **This is the actual differentiator and a publishable
artifact on its own.**

**M2 — blind search in genuinely unexamined sky**, prioritised by the M1 map.

**M3 — collaboration contact.** Martínez-Delgado (IAA-CSIC) for streams; Zaritsky (Arizona) for UDGs;
Keel (Alabama) for morphological oddities. Approach with a vetted candidate list and your M0 calibration
result — that is what makes an unaffiliated approach credible.

**M4 — publish.** **RNAAS** for individual objects (free, ~72 h, ADS-indexed, *"Independent Researcher"*
accepted); A&A via collaboration for anything systematic.

⚠️ **arXiv endorsement** is the real gate for a first solo paper — automatic endorsement needs an
institutional email. The documented workaround is the Donatiello path: **get co-authorship on someone
else's paper first.**

---

## Sources

- Data Lab TAP: `https://datalab.noirlab.edu/tap` · hips2fits: `https://alasky.cds.unistra.fr/hips-image-services/hips2fits`
- Rubin stream / RNAAS proof case: arXiv:2510.24836
- Amateur-telescope streams: arXiv:2504.02071 (**A&A 701, A182**)
- Dwarf accretion features: arXiv:2511.23314 (**A&A 707, L1, 2026**)
- SMUDGes V: arXiv:2306.01524 · DES LSBGs: arXiv:2006.04294 · KiDS DR5: arXiv:2605.13842
- Sand dwarfs: arXiv:2409.16345
- RNAAS: `https://journals.aas.org/research-notes/`
