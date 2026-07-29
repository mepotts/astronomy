# Coronagraph comets — the last place zero-equipment amateurs still discover

**One-liner:** Blink public coronagraph image sequences from SOHO/LASCO, GOES-19/CCOR-1, PUNCH and
PSP/WISPR, identify sungrazing comets by their constant pixel velocity, and report positions to the
NASA-funded Sungrazer Project — which has confirmed **5,204 comets**, almost all found by amateurs
looking at downloaded images.

**Scores (U/B/E):** U **2/5** on LASCO (30 years, ~4 dominant hunters), **4/5** on CCOR-1 (live since
2025), **5/5** on PUNCH (open, and **zero comets discovered in it to date**) · B **4/5** (image
sequence analysis; the detection is visual/CV, not catalogue work) · E **4/5** (a real IAU comet
designation — but see the naming rule)

**Status:** proposed

**Cost to operate: $0** — every feed below is an unauthenticated HTTP download.

---

## Read the naming rule before you invest

IAU Comet-Naming Guidelines, **3.4(b)**, verbatim:

> "Comets that are discovered from data or images made public through printed publication or electronic
> posting (e.g., World Wide Web) are not eligible for individual names of people and generally will not be
> named unless there is an established program name for the origin of the images. Such discoverers are
> considered members of the 'team'."

**This is why all 5,204 SOHO comets are named "SOHO."** You get: discovery credit in the CBET/MPEC, your
name permanently in the discoverer column at `https://sungrazer.nrl.navy.mil/soho-discoveries`, and a real
IAU-designated object. You do **not** get your name on the sky. Decide whether that trade is acceptable
before starting — it is the single most common source of disappointment in this pathway.

---

## Why this still works when everything else got automated

Coronagraphs see sky that ground-based surveys **structurally cannot reach** — within tens of degrees of
the Sun. Rubin will never touch it. Sungrazers are also faint, fast, and embedded in a noisy, streaming
coronal background, which is exactly the regime where automated detection has historically underperformed
a human blinking three frames.

## The four feeds, ranked by openness

| Feed | Access | Volume / cadence | State |
|---|---|---|---|
| **PUNCH** ⭐ | `https://punch.space.swri.edu/punch_science_getdata.php` · archive `https://umbra.nascom.nasa.gov/punch` · browse `https://helioviewer.org/` | Launched **March 2025** | *"Fully open to anyone for use with no restrictions."* No registration. Already tracked comet SWAN over 40 days and imaged C/2026 R3. **No comet has ever been discovered in PUNCH data.** Highest upside, zero precedent |
| **GOES-19 CCOR-1** ⭐ | `https://services.swpc.noaa.gov/products/ccor1/` — `fits/`, `jp2/`, `jpegs/`, `mp4s/` | FITS **8.8 MB each**, rolling ~24-day window; JPEGs at **15-min cadence** **[measured]** | Live since 2025; **~30 sungrazers in its first two months**. Passband includes **589 nm sodium**, which lights up sungrazers. ⚠️ Use `/products/ccor1/` — the older `/experimental/…/ccor-1/jpegs/` path returns 200 but is **empty** |
| **SOHO/LASCO** C2/C3 | `https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/{YYYY}/{c2\|c3}/{YYYYMMDD}/` · realtime `/data/realtime/c2/1024/latest.jpg` | **~105 images/day per camera, 12-min cadence, ~800 KB/frame → ~165 MB/day** for both **[measured]**. Full mission 1996→present | The workhorse: **>99% of SOHO's discoveries**. Heavily mined. ⚠️ ESA funding phase-out; operations extended *"at least until September 2026."* Poll no faster than every 15 min |
| **SOHO/SWAN** | `http://swan.projet.latmos.ipsl.fr/` (HTTP only; HTTPS 404s) · images `https://soho.nascom.nasa.gov/data/summary/swan/swan-images.html` | Lyman-α | Sensitive to **water in cometary comae**; reaches low solar elongations ground surveys cannot. **The verified no-telescope discovery route** — see below |
| **PSP/WISPR** | `https://wispr.nrl.navy.mil/wisprdata/` | Released **every ~3 months** | **8 confirmed comets.** Use **L3** products — *"fully pre-processed and require absolutely no preparation."* The slow release cadence removes time pressure. Low competition |
| STEREO-A/SECCHI HI-1, HI-2 | `https://secchi.nrl.navy.mil/data-overview` | — | STEREO-A only (B lost 2014). ⚠️ Sungrazer's official guide covers **only LASCO C2/C3** — no HI-specific citizen guidance exists. Community lives at `http://sungrazer.groups.io/g/STEREO` |
| Solar Orbiter / SoloHI | `https://solohi.nrl.navy.mil/` | — | **No citizen-discovery programme found. Treat as closed.** |

---

## Verified no-telescope discoveries — this is not theoretical

- **C/2025 F2 (SWAN)** — **Michael Mattiazzo** analysed publicly downloaded SWAN Lyman-α data with **no
  telescope of his own**, using *Guide 9 planetarium software* merely to convert ecliptic→equatorial
  coordinates. Noticed the brightening 30 May 2025 (detectable from 22 Mar), posted for help 1 April,
  confirmed 3 April by **Quicheng Zhang with a 40 mm refractor**. Co-discoverers **Vladimir Bezugly**
  (Ukraine) and **Rob Matson** (USA). Reached APOD.
  Writeup: `https://southerncomets.info/webpage/2025f2_discovery.htm`
- **C/2025 R2 (SWAN)** — **Vladimir Bezugly** spotted *"a rather obvious blob"* on 11 Sep 2025; ground
  confirmation next day by Martin Mašek with the FRAM robotic telescope.
- **C/2026 B4** — **Hanjie Tan**, SWAN, 22 January 2026; later confirmed in **PUNCH** imagery.
- **CCOR-1, early 2025** — ~30 sungrazers. **Robert Pickard** made the first (11 Feb 2025) and had 8;
  **Jiangao Ruan** leads; **Worachate Boonplod** and **Zhijian Xu** also prolific.

---

## Method

Blink 3+ consecutive frames (GIMP, Photoshop, PixSpy, or your own aligner). Record `time, x, y` pixel
coordinates. **Validate constant pixel velocity** — Kreutz-group comets vary **<10 px/h in C3** and move
~70 px/h in C2. Require visibility across **≥5 consecutive images**.

**Reporting:** register at `https://sungrazer.nrl.navy.mil/contributors/request_form` (1–3 day approval),
then report at `https://sungrazer.nrl.navy.mil/report`. Minimum **2 positions in C2 or 3 in C3**, object
visible in 6–7 consecutive images. *"Credit will be given to the first person to provide two or more
accurate positions"* — **single positions get nothing.**

⚠️ **Confirmation backlog is severe.** Sungrazer's most recent site update (2026-05-28) covers *"July–August
2025 Confirmations"* — a **~9-month lag** from report to confirmation. Budget for it emotionally; do not
interpret silence as rejection.

⚠️ **TOCP is the wrong route.** It states it is *"designed for use with stationary, extra-solar-system
objects only."* Comets go via Sungrazer → MPC **PCCP** (`https://www.minorplanetcenter.net/iau/NEO/pccp_tabular.html`)
or plain-ASCII email to `cbatiau@eps.harvard.edu`.

---

## Guardrails

1. **Never claim cometary activity you have not seen.** MPC's PCCP warns in capitals: *"IF YOU DO NOT
   DETECT CLEAR COMETARY ACTIVITY, DO NOT CLAIM THAT AN OBJECT IS A COMET."* False claims damage your
   observatory reputation score and can cause future reports to be disregarded.
2. **Cosmic rays and internal reflections are the dominant false positive.** The constant-pixel-velocity
   test across ≥5 frames exists specifically to kill them. Do not shortcut it.
3. **Respect polling limits** — LASCO scripts must not poll more often than every 15 minutes.
4. **Known-object check.** Cross-check against the MPC's known comet ephemerides before reporting; the
   sungrazer population is well-populated with returning fragments.

---

## Architecture sketch

```
coronagraph/
  fetch/     per-feed downloaders (LASCO, CCOR-1, PUNCH, WISPR); rate-limited; incremental by date
  prep/      frame alignment, running-difference, background/streak suppression
  detect/    moving-point-source candidates; constant-velocity fit across N frames; CR rejection
  vet/       known-comet ephemeris cross-check; visibility-across-5-frames gate
  review/    animated blink packet per candidate — the human decision surface
  report/    Sungrazer-format position list (time, x, y); manual submission
```

**Honest note on automation:** this pathway is the least catalogue-shaped of the eight. Detection is image
processing, and the humans currently winning at it are doing it *by eye*. An automated detector is a real
engineering project, not a weekend script — which is precisely why PUNCH has zero discoveries in it.

---

## Milestones

**M0 — kill-check (~1 day).** Register with Sungrazer (1–3 day approval — start the clock). Download the
LASCO C3 frames covering a **known, already-confirmed** SOHO comet and confirm you can see it by blinking
and measure its positions to Sungrazer's stated tolerance. *If you cannot recover a known comet by hand,
no detector you write will find an unknown one.*

**M1 — automated candidate detection on LASCO.** Prove the pipeline against the historical archive where
ground truth exists (5,204 confirmed comets = an enormous labelled training/validation set — this is the
underrated asset in this pathway).

**M2 — port to CCOR-1.** Newest feed, only ~18 months of history, ~4 active hunters. Best
discovery-per-effort ratio of the four.

**M3 — PUNCH.** Genuinely unexplored. If M1's detector generalises, this is where a first-ever result lives.

**M4 — publish the detector.** A validated open-source sungrazer detector benchmarked against the 5,204
confirmed comets is itself a citable **RNAAS**-shaped contribution, independent of whether you discover
anything.

---

## What success looks like

`C/2026 XX (SOHO)` or `(CCOR)`, your name in the project's permanent discoverer column and in the CBET
text. Plus eligibility for the **Edgar Wilson Award** (`http://www.cbat.eps.harvard.edu/special/EdgarWilson1.html`)
— though note recent winners (Nishimura, Borisov, Camarasa, Duszanowicz, Hahn) discovered with their own
telescopes, and the award targets amateur discoverers generally.

---

## Sources

- Sungrazer: `https://sungrazer.nrl.navy.mil/` · report `/report` · register `/contributors/request_form` ·
  guide `/soho_guide` · discoveries `/soho-discoveries`
- CCOR-1: `https://services.swpc.noaa.gov/products/ccor1/` · `https://ccor.nrl.navy.mil/ccordata`
- PUNCH: `https://punch.space.swri.edu/punch_science_getdata.php` · `https://punchbowl.readthedocs.io/en/latest/data/index.html`
- LASCO: `https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/` · FITS `https://umbra.nascom.nasa.gov/pub/lasco_level05/`
- WISPR: `https://wispr.nrl.navy.mil/wisprdata/` · confirmations `https://sungrazer.nrl.navy.mil/index.php/psp-confs-jul2023`
- IAU comet naming: `https://www.wgsbn-iau.org/documentation/CometNamingGuidelines.html` ·
  `http://www.cbat.eps.harvard.edu/cometnameg.html`
- MPC PCCP: `https://www.minorplanetcenter.net/iau/NEO/pccp_tabular.html`
- BAA comet lists: `https://people.ast.cam.ac.uk/~jds/coms26.htm`
