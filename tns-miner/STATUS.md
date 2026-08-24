# tns-miner — status log

*Newest first. Root [`../STATUS.md`](../STATUS.md) carries the one-line summary.*

- **2026-08-24 — M1 complete. Access verified, the gap re-measured and half the
  founding premise withdrawn, filter built and validated against a positive
  control at 68.6% recovery.** Nothing submitted to TNS; no account created
  anywhere.

  **Kill checks — all three PASS** ([`M1-01`](M1-01-kill-checks.md)). *Correction
  to the sweep:* TNS `/api/get/` is **401 without credentials** and the bulk
  `tns_public_objects` mirror is **403** — reads are *not* open. The tokenless
  route that works is the web search CSV export (`/search?…&format=csv`). Rate
  limit re-measured at **10 per rolling 60 s**, and it is **one shared bucket
  across `/api/` and `/search`**. **ALeRCE, Fink and ANTARES are all tokenless and
  all serving last night's alerts** (MJD 61276.36). ZTF still flowing:
  `ztf_public_20260824.tar.gz` posted this morning, ~97k science alerts/night.

  **The gap, measured on 30,454 real TNS reports** ([`M1-02`](M1-02-the-measured-gap.md)).
  Three of the sweep's four claims fail:
  - **Gaia filed zero reports in 12 months.** The top five are now ATLAS 27.3%,
    Pan-STARRS 27.1%, **GOTO 26.9%**, **WFST 26.7%**, ZTF 26.1% — two of which the
    sweep never mentions.
  - **The faint-end premise is inverted.** TNS's median discovery magnitude is
    **20.36** and 45% of all reports are already in the "under-reported" 19.0–20.6
    band. **DCAP's median is 18.74 — 1.6 mag *brighter* than the population.**
  - **The real axis is galactic latitude.** 5.8% of all TNS reports come from
    |b| < 15°; for DCAP it is **55%**, for XOSS **68%**, and for every automated
    reporter between **0.4% and 8.1%**.
  - Confirmed: **92.1% of TNS objects are unclassified**.
  - Direct count of what is left on the table: over two nights 34 days back,
    **211 of 214 objects passing a sane real-transient filter never reached TNS
    (98.6%) — ≈105 per night.** README corrected in place.

  **The filter** ([`M1-03`](M1-03-filter.md)) — thresholds pre-registered under a
  stated rule and frozen before counting. Two revisions, both made before any
  candidate was counted and both documented in full: the bright floor moved
  16.0 → 12.0 (a 16.0 floor structurally excluded the target class), and a
  1.5–3.0″ dead zone between channels A1 and A2 was closed (it had rejected
  AT 2026stb, a real confirmed nova). Runs entirely on Fink's alert packets plus
  its native VSX / GCVS / SIMBAD / TNS / MPC cross-matches.

  **The positive control — PASS** ([`M1-04`](M1-04-positive-control.md)).
  Rewound to DCAP's true TNS report times (scraped per object; the search CSV only
  has the discovery epoch, and the two differ by ~22 h). **70 of 102 DCAP
  designations recovered from pre-report data = 68.6%, median lead 4.15 d (2.13 d
  within the same outburst episode), and all 70 leads positive.** Negative control
  on 60 auto-reporter objects: **10.0%** — a **6.9× contrast**. Class behaviour is
  right: 2 of 3 confirmed novae recovered, 9 of 10 SN Ia correctly rejected.

  **Candidates** ([`M1-05`](M1-05-candidates.md)) — **184 objects, MATTHEW-GATED,
  nothing reported.** And an honest caveat the positive control could not have
  surfaced: the pre-registered filter has **no amplitude and no variability
  requirement**, so the raw list is dominated by low-amplitude variability on
  uncatalogued point sources (median amplitude **−1.15 mag**; 22 are flat
  difference-image residuals, i.e. sources missing from the reference image). A
  declared post-hoc triage (which changes no threshold) leaves **tier A = 3,
  tier B = 5, tier C = 176**. Best three: `ZTF18abobdzu` (|b| = +6.4°, amplitude
  1.54 mag, 1.01 mag ptp in g — best dwarf nova), `ZTF19acbplek` (amplitude
  4.17 mag, recurrent outbursts), `ZTF18abbsyyw` (|b| = −2.3°, r = 16.4, ~1 mag
  ptp). **Trap paid for:** a variability measure taken across mixed filters makes
  any constant source with a 1.5 mag colour look like a 1.5 mag variable — it
  promoted a flat reference-image residual to top candidate before the per-band
  fix caught it.

  **Submission path documented, not walked** ([`M1-06`](M1-06-submission-path.md)):
  the AT-report JSON verbatim, the TNS2.0 field renames, the `/api/set/bulk-report`
  route, and the blocking error that governs everything — **a pre-discovery
  non-detection is mandatory**, which makes ATLAS forced photometry a hard
  dependency. Matthew's steps: register at TNS, define a bot, register at ATLAS
  forced photometry.

  **Recommended M2:** measure *precision*, which M1 did not. Hand-vet a
  pre-registered sample of candidates against cutouts; add the amplitude and
  colour cuts the fresh pass proved are missing; build a real outburst enumerator
  (ALeRCE's `firstmjd` window cannot see a known source re-erupting, which is most
  of DCAP's business); demote VSX from hard veto to flag (it cost a real nova); and
  re-open the M31 channel in September, when the field returns — it is empty right
  now for purely seasonal reasons.

- **2026-08-24** — Folder created. Front chosen by Matthew as the portfolio's
  discovery-shaped push after an honest review found real results but **no claimed
  discoveries**. First agent launched: verify TNS + broker access, measure the
  actual gap, build the filter, and validate it against a **positive control**
  (transients that were reported by others — would our filter have caught them
  first?). Nothing verified yet.
