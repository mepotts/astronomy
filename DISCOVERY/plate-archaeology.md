# Plate archaeology — IAU designations from century-old glass

**One-liner:** Digitized photographic plate archives span 1880–1990 and contain transients that nobody
alive ever noticed, because no survey pipeline reads glass. Find one, report it to the Transient Name
Server, and it receives a permanent IAU designation — for an event that happened decades ago.

**Official recognition: YES.** TNS issues a real IAU `AT` designation plus a citable ADS bibcode.

**Scores (U/B/E):** U **5/5** (near-zero competition — this is the least contested pathway in the folder) ·
B **3/5** (image work on heterogeneous scanned plates; harder than catalogue queries) · E **5/5** (a
permanent IAU designation for a supernova that exploded before you were born)

**Status:** proposed

**Cost to operate: $0** — DASCH and DSS/POSS scans are free downloads.

---

## The proof case

**AT 1994au** — TNS Report No. 275562, bibcode `2025TNSTR4419....1R`, received 2025-11-03:

```
Reporting Group: F. D. Romanov     Discovery Data Source: None
IAU Designation: AT 1994au         Discovery date: 1994-12-28
Flux: 12.3 VegaMag                 Filter: R-Cousins
Remarks: Possible bright missed supernova in ESO 157-27 on POSS-II F plate (1994-12-28)
Last non-detection: 1992-01-13, limit 19 mag (SERC-I Survey plate)
```

**Filipp Romanov mined a 30-year-old digitized photographic plate, found a missed magnitude-12.3
supernova, and received a permanent IAU designation and a citable bibcode.** No telescope. No affiliation.
No competition — because nobody's bot reads glass.

Romanov has done this repeatedly: arXiv:1809.03091 (a dwarf nova found on Digitized Sky Survey plates),
arXiv:2111.11086 (Romanov V20), and arXiv:2212.12543 — *"The contribution of the modern amateur astronomer
to the science of astronomy."*

---

## Why the competition is near-zero

Every automated discovery pipeline in astronomy operates on **digital** data with consistent photometric
calibration, known PSFs, and machine-readable metadata. Plate scans have none of that: variable emulsion
response, plate defects that mimic point sources, non-linear reciprocity failure, hand-written metadata,
and astrometric solutions tied to obsolete reference catalogues.

That is a **feature** for you. The barrier is *unglamorous data engineering*, not access, funding, or
instrument time — and it is the kind of barrier that keeps a field empty for decades.

---

## Data sources

| Archive | Access | Scale | State |
|---|---|---|---|
| **DASCH** ⭐ | `https://dasch.cfa.harvard.edu/` — ⚠️ **`dasch.rc.fas.harvard.edu` is DEAD** (expired cert, retired) | **429,274 plates, 1880–1990, full sky, 23.6 billion measurements of 252M sources, ~678 TiB** | **DR7 released 2024-12-29**; scanning completed 2024-03-28; **all access restrictions lifted**. Client `daschlab` (`https://daschlab.readthedocs.io`), REST API `/dr7/web-apis/`, Starglass `https://starglass.cfa.harvard.edu/`, zero-install Binder notebook |
| **DSS / POSS-I, POSS-II, SERC** | via SkyView `https://skyview.gsfc.nasa.gov/`, CDS hips2fits (`CDS/P/DSS2/*`), STScI | Multi-epoch all-sky | The archive Romanov actually used for AT 1994au |
| **hips2fits** (universal cutouts) | `https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=<ID>&ra=&dec=&fov=&width=&height=&projection=TAN&coordsys=icrs&format=fits` | **1,373 image surveys** | Single API for DSS2, POSS, and every modern comparison survey. **The sleeper tool for this pathway** — build cross-epoch comparison in ~20 lines |
| Modern comparison layer | DESI LS DR10, Pan-STARRS, Gaia DR3, ZTF | — | For confirming the position is *empty now* and identifying the host |

**Reference for what DASCH is and isn't:** it is a *photometric* pipeline. It has **no moving-object
handling and actively rejects transients as plate defects** — which is exactly why transients survive in
it unreported.

---

## Two distinct products, and only one of them is easy

**(A) Missed transients → TNS.** The proven route. A supernova or nova visible on one plate epoch, absent
on earlier and later epochs, coincident with a plausible host, not matching any known variable. → IAU
designation. **This is the priority.**

**(B) Asteroid precovery → MPC.** Much harder, and honestly rated **2/5**. Reasons, verified:
- DASCH's 11 µm scanning gives **~4.4–9.9″/px on patrol plates**, against the MPC's ≤2–3″/px preference.
  **Only narrow-field plates qualify.**
- The WCS is solved against **Tycho-2, not Gaia** — a systematic astrometric handicap.
- **DASCH is not on the SARC archive list**, so the submission path is undefined; you would contact the
  MPC directly.
- **No published DASCH asteroid precovery exists.**

The technique *is* proven on other plate archives — NAROO, **DANEOPS (~146 NEOs)**, Arcetri **ANEOPP
(>70)**, and a 2026 Tautenburg paper in *Icarus* — so this is a real research direction, just not a
tractable first project. **Do (A). Treat (B) as a later, separate question.**

---

## Guardrails

1. **Plate defects are the dominant false positive**, and they are *designed* to look like point sources.
   Require the candidate on **two independent plates of the same epoch** where available, or an
   unambiguous morphological argument.
2. **Emulsion flaws, dust, and scanner artifacts** cluster non-randomly. Check the plate's own defect
   record and neighbouring sky.
3. **Cross-check every candidate** against VSX (10.3M entries), SIMBAD, GCVS, and MPChecker before
   reporting. A century-old "transient" is usually a known long-period variable near maximum.
4. **Report honestly as `AT`,** with the archival non-detection stated. TNS explicitly permits
   *"archival info + comments"* in place of a measured non-detection limit — which is what makes
   telescope-free reporting legitimate here.
5. **Do not overclaim a type.** Without a spectrum it is an `AT`, not an `SN`. Romanov's own report says
   *"Possible bright missed supernova."*

---

## Architecture sketch

```
plate-arch/
  fetch/     daschlab light curves + plate cutouts; hips2fits for DSS/POSS epochs
  align/     per-plate WCS sanity check; note the Tycho-2-vs-Gaia offset explicitly
  detect/    epoch-differencing: present-on-one-epoch, absent-before-and-after
  defect/    plate-artifact rejection — the make-or-break module
  context/   VSX + SIMBAD + GCVS + MPChecker; host-galaxy association from DESI LS / Pan-STARRS
  review/    per-candidate packet: all plate epochs + modern imaging side by side
  report/    TNS AT report with archival non-detection; sandbox-first
```

**This composes directly with [IDEAS/dasch-time-machine](../IDEAS/dasch-time-machine.md)** — that plan
already scoped wiring DASCH's ~1885–1990 light curves to live broker alerts. Same `fetch/` layer, opposite
direction of inference. Build one, get most of the other.

---

## Milestones

**M0 — kill-check (~1–2 days).** Install `daschlab`, pull the DASCH light curve and plate cutouts for
**a known historical transient** (a catalogued historical nova or supernova with a known plate detection),
and confirm you can recover it — visible at the right epoch, absent adjacent. *If you cannot recover a
known event, the detection logic is not ready.* Also verify the TNS account from
[tns-alert-miner](tns-alert-miner.md) is approved — same account serves both.

**M1 — blind search on a bounded sky region.** Pick a well-plated field. Run epoch-differencing. Measure
your false-positive rate against plate defects — **this number decides whether the project is viable**,
and it is the one thing no existing paper will tell you.

**M2 — the defect-rejection module.** The genuine engineering contribution. Everything else here is
plumbing.

**M3 — one hand-reviewed TNS report.**

**M4 — the citable artifact.** Two options, both real: an **RNAAS** note on individual recoveries, or —
more interesting — a systematic paper on *transient recovery rates in DASCH DR7*, which characterises a
678 TiB public archive that has never been searched this way. Note the AAS explicitly accepts
**"Independent Researcher"** as an affiliation.

---

## What success looks like

`AT 19XXxx` — an IAU designation for an event that happened decades ago, with your name as the reporter of
record and a permanent ADS bibcode. And, if M1's false-positive rate is respectable, the first systematic
transient search of the DASCH archive.

**No clock on this one.** Unlike the alert-stream and archival-asteroid pathways, Rubin does not compress
this niche at all — the plates are not getting any newer, and nobody else is coming for them.

---

## Sources

- DASCH: `https://dasch.cfa.harvard.edu/` · `daschlab` `https://daschlab.readthedocs.io` ·
  REST `https://dasch.cfa.harvard.edu/dr7/web-apis/` · Starglass `https://starglass.cfa.harvard.edu/`
- TNS: `https://www.wis-tns.org` · the proof case `https://www.wis-tns.org/object/1994au/discovery-cert`
- Romanov's method papers: arXiv:1809.03091 · arXiv:2111.11086 · arXiv:2212.12543
- hips2fits: `https://alasky.cds.unistra.fr/hips-image-services/hips2fits`
- SkyView: `https://skyview.gsfc.nasa.gov/current/cgi/pskcall`
- VSX: `https://vsx.aavso.org/` · GCVS: `http://www.sai.msu.su/gcvs/` (HTTP only)
- Related repo plan: [IDEAS/dasch-time-machine.md](../IDEAS/dasch-time-machine.md)
