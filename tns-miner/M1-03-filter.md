# M1-03 — The filter: pre-registered thresholds

**Date:** 2026-08-24 · **Status:** frozen before candidate generation ·
code: `scripts/m1_filter.py`

## The rule that fixes a threshold

Written down before any number was chosen, and applied in this priority order:

> **(i)** the value the published ZTF / AMPEL / ZTF-BTS "real transient" recipes
> already use for that same alert field; **(ii)** a boundary this project's own
> README names; **(iii)** the loosest value that excludes an artifact class by
> construction.
>
> **No threshold may be chosen by looking at how many candidates it yields.**

Two thresholds were revised once, on 2026-08-24, still before any candidate was
counted. Both revisions are recorded in full below with the measurement that
forced them, and the v1 values are kept in the source. Nothing was moved after
seeing a candidate count.

## Why the filter is an inversion, not a tightening

The survey auto-reporters hunt extragalactic supernovae. Their cuts demand a
*resolved host*: PS1 star/galaxy score low, offset from the host centroid large
enough to be off-nucleus but small enough to be associated. Novae, dwarf novae and
CVs are **stellar** and usually sit exactly on their own quiescent progenitor.
The SN cuts do not merely deprioritise them — they exclude them by construction.
`M1-02` measures the consequence: 5.8% of all TNS reports come from |b| < 15°,
while 55% of DCAP's and 68% of XOSS's do.

So this filter keeps what those pipelines throw away, and throws away what they
keep.

## Data source

One row per detection, straight from Fink's
`https://api.ztf.fink-portal.org/api/v1/objects` — the complete raw ZTF alert
packet (`i:` fields) plus Fink's own cross-matches (`d:` fields: SIMBAD, **VSX**,
**GCVS**, **TNS**, MPC/`roid`, Gaia). Tokenless. This removes the need for
separate VSX / SIMBAD / MPChecker calls per candidate: the broker has already
done them at ingest time.

**One property of `d:tns` matters enormously and was verified before use:** Fink
stamps it at the instant it processes each alert and never back-fills. On
ZTF26abfokua (= AT 2026stb) every alert before DCAP's report carries an empty
`d:tns` and every alert after carries `Nova`. That is what makes the rewind in
`M1-04` an honest test rather than a lookup of the answer.

---

## Layer 1 — universal hygiene gate (per detection)

| cut | value | rule | why |
|---|---|---|---|
| `i:isdiffpos` | `t` / `1` | (iii) | positive subtraction: brightening, not fading |
| `i:drb` | ≥ **0.90** | (i) | ZTF deep real-bogus, standard high-purity cut |
| `i:rb` (fallback) | ≥ **0.55** | (i) | legacy score, alerts predating `drb` |
| `i:nbad` | **0** | (iii) | any bad pixel in the stamp → reject by construction |
| `i:fwhm` | ≤ **5.0** | (i) | ZTF standard |
| `i:elong` | ≤ **1.4** | (i) | ZTF standard |
| `abs(i:magdiff)` | ≤ **0.5** | (i) | ZTF standard is 0.1; loosened to 0.5 because at mag ~20 the PSF-vs-aperture scatter alone exceeds 0.1 |
| `i:magpsf` | **12.0 – 20.6** | (ii) | see revision R1 |
| `i:ssdistnr` | < 0 or > **5.0″** | (i) | ZTF's own known-minor-planet match radius |
| `d:roid` | not 2 or 3 | (i) | Fink's solar-system candidate / MPC match flags |

## Layer 2 — detection multiplicity

- **≥ 2** detections passing Layer 1, and
- the pair separated by **≥ 0.02083 d (30 min)**.

Rule (iii): below 30 min a main-belt asteroid has not moved measurably, so a
shorter baseline cannot exclude a mover. This is the single cut that costs the
most speed — see `M1-04`, where it is exactly why the filter fires ~1 night
behind a human eyeballing a single alert.

## Layer 3 — catalogue veto

Rejected if any alert on the object carries a non-null `d:vsx` (VSX), `d:gcvs`
(GCVS), or `d:tns` (already reported), or a `d:cdsxmatch` SIMBAD class in the
known-variable / known-host list (RRLyr, Mira, LPV, EclBin, Cepheid, AGN, QSO,
Blazar, Galaxy, …). SIMBAD classes `CataclyV*`, `Nova`, `DwarfNova`, `Symbiotic*`
and their `_Candidate` forms are **targets, not vetoes**.

> **Trap paid for here:** Fink writes the literal string `"Fail 502"` into a `d:`
> column when its cross-match service errored at ingest. Treating that as a
> catalogue hit silently vetoes real candidates. `"Fail*"` counts as null.

## Layer 4 — nuclear / TDE veto

Rejected if `i:sgscore1 ≤ 0.30` **and** `i:distpsnr1 ≤ 1.0″` — sitting on a PS1
galaxy centroid. Rule (i). The mission scope excludes TDEs and nuclear
transients; this is the cut that enforces it.

## Layer 5 — target channels

Evaluated at the first epoch that satisfies Layers 1–2, falling back to the
brightest clean detection if association is epoch-noisy.

| channel | condition | what it is hunting |
|---|---|---|
| **B_M31 / B_M81** | inside 1.5° of M31 (10.6847, +41.2687) or 0.5° of M81 (148.8882, +69.0653) | resolved-galaxy novae |
| **A2_nova_like** | no PS1 source within **3.0″**, or the nearest is fainter than **21.0** | classical nova, new star where nothing was |
| **A1_cv_outburst** | PS1 source within **3.0″** and `sgscore1 ≥ 0.50` (or PS1 has no opinion) | CV / dwarf-nova outburst on its own progenitor |
| **D_galactic_plane** | \|b\| < **15°**, any magnitude | the measured gap of `M1-02` |
| **C_faint_residue** | mag **19.0 – 20.6**, nothing above matched | faint ZTF residue |

`sgscore1 = 0.5` is what ZTF writes when PS1 has no opinion. For this class the
no-opinion side is the side to keep, so the A1 test is `≥ 0.50`, not `> 0.50`.

## Layer 6 — TNS exclusion

On top of Fink's per-alert `d:tns`, every candidate is positionally cross-matched
at **3.0″** against the full 12-month TNS harvest (30,454 objects). 3″ is TNS's
own duplicate-report radius.

---

## The two revisions, in full

### R1 — bright-magnitude floor 16.0 → 12.0

- **v1 reasoning:** "brighter than 16.0 is ASAS-SN / ZTF-BTS territory."
- **What forced the change:** the DCAP reports this project exists to reproduce
  run **12.53 – 20.58 mag with a median of 18.74**, and **7.8% are brighter than
  16.0**. `M1-02` then showed the whole premise was inverted: DCAP is 1.6 mag
  *brighter* than the TNS median, not fainter. A 16.0 floor structurally excludes
  the target class.
- **New value:** 12.0 — just below DCAP's brightest report and at ZTF's
  saturation limit.

### R2 — the A1/A2 dead zone at 1.5–3.0″

- **v1 had** `A1_SEP ≤ 1.5″` and `A2_SEP > 3.0″`, so an object with a PS1
  association between 1.5″ and 3.0″ matched **no channel** and fell through to
  the faint-residue channel, which requires mag ≥ 19. Every bright in-plane
  object with a ~2″ association was silently dropped.
- **What forced the change:** AT 2026stb — a **real, spectroscopically confirmed
  nova** DCAP reported — sits at `distpsnr1 = 2.19″`, mag 15.06. v1 rejected it.
- **This is a partition bug, not a threshold choice.** A1 and A2 now tile the axis
  at a single radius, 3.0″, the same radius used everywhere else in this project.

Nothing else moved. `DRB_MIN`, `NBAD_MAX`, `FWHM_MAX`, `ELONG_MAX`,
`MAGDIFF_MAX`, `N_DET_MIN`, `DT_MIN_DAYS`, `SSDIST_MAX_ARCSEC`, the nuclear veto,
the M31/M81 cones and `GAL_PLANE_ABS_B` are all at their v1 values.

## Known limitations, stated up front

1. **Latency.** The 2-detection / 30-minute gate means the filter cannot fire on
   the discovery exposure itself. A human looking at one alert beats it by up to
   one night. Measured in `M1-04`.
2. **Enumeration, not the filter, is the current bottleneck.** ALeRCE's
   `firstmjd` window finds only objects whose *first ever* detection is in the
   window, so a known ZTF source re-erupting is invisible to it. Fink's `latests`
   partly covers this; a proper outburst-detection enumerator is the top M2 lever.
3. **No forced photometry.** A credible discovery report wants a pre-discovery
   non-detection. ATLAS forced photometry provides it but requires free
   registration — Matthew's step, not an agent's.
4. **No variability requirement, and no amplitude requirement.** A source that
   is *constant* in the difference image passes every cut — that is how a source
   missing from the reference template looks, and on a fresh pass 22 of 184
   candidates are exactly that. Both cuts belong in M2. Related trap, paid for in
   `M1-05`: **any variability measure on ZTF difference photometry must be
   computed per `fid`.** Mixed across filters, a perfectly constant source with
   g − r = 1.5 reads as a 1.5-magnitude variable.
5. **The Mira trap is only half-closed.** VSX/GCVS/SIMBAD catch catalogued
   long-period variables; an *uncatalogued* red LPV in the plane can still look
   like a nova. A colour cut (g−r) belongs in M2.
