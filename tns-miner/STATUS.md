# tns-miner — status log

*Newest first. Root [`../STATUS.md`](../STATUS.md) carries the one-line summary.*

- **2026-09-02 — Input/cache correctness repair complete in code; proved-input
  reproduction still pending.** A repository audit found that the M1 history
  fetcher cached `[]` after an exhausted retry loop and the M2 batch fallback
  still wrote `[]` for objects whose individual fetch never succeeded. The
  existing cache held **5,133 object files, including 1,104 legacy empty arrays**;
  because the old format recorded no HTTP status, those empties cannot be split
  honestly into real no-history responses and outages.

  Both M1/positive-control and M2 paths now use one validated cache client. Only
  HTTP 200 plus a structurally valid response is cached; batch omissions are
  confirmed individually; failures abort rather than become scientific zeros.
  Per-object sidecars record timestamp, endpoint, HTTP status, request mode, row
  count, and payload digest. Reuse now requires both age ≤24 hours and a fetch
  timestamp at or beyond the requested history JD; proved-empty histories and
  cone nulls therefore expire, and future timestamps are rejected. Legacy
  nonempty filesystem mtimes cannot prove window coverage. Cone-resolution
  positives/nulls now carry query/value-bound proofs, so a mismatched or
  interrupted two-file update refetches; failures abort and are never cached as
  "unresolved." Legacy `[]` files are moved reversibly under
  `data/fink/_quarantine/` by an offline migration or when accessed, then fetched
  normally on the next run. **No threshold or human-submission gate changed.**

  Historical M1/M2 pool evaluation now has an inclusive `mjd_end + 2400000.5`
  ceiling (and M2 retains its 60-day floor). Candidate amplitudes/episodes and
  evidence light curves use the same ceiling; evidence forces a live refresh;
  all outputs record the as-of JD and cache provenance. Old intermediates without
  exactly one ceiling fail closed.

  Tag-derived ALeRCE/Fink pool caches now bind their exact MJD window and payload
  digest; strict portable-slug validation rejects traversal before tag-derived
  I/O, and reusing `tonight` for another night fails. Fink E2 outages, malformed
  or empty class taxonomies, malformed alert rows, and still-cap-bound slices
  abort without caching an incomplete arm. Its versioned multi-family taxonomy
  baseline rejects partial-but-plausible class catalogues, and JSON boolean
  subtraction signs are normalized consistently between validation and selection.
  CDS X-Match caches bind the ordered OID/position list, and all-catalogue failure
  aborts. Cutout outages no longer become permanent 1×1 zero images. Output
  manifests retain the exact per-OID Fink status/fetch/source/payload digest.

  TNS candidate dedupe now uses a full-12-month immutable snapshot whose entire
  scan starts after the history ceiling and within one day, excluding rows with
  later discovery dates. UTC month windows include the current day on the first
  of a month. Header-only closed months, repeated/overlapping page IDs, and ID
  overlap across month windows abort the harvest instead of being deduplicated;
  each row's discovery timestamp must lie in its requested UTC interval, and
  pagination continues through short nonempty pages until an explicit empty page.
  Latest
  registry matches are annotation-only. This is
  deliberately **not called exact registry-as-of**: the public CSV lacks report
  publication time, so later-filed reports with older discovery dates cannot be
  separated and the 2026-08-24 candidate-veto state is unreconstructible.

  Final M1/M2 candidate CSVs now receive atomic digest/row/input proofs, and the
  atomic JSON summary embeds the identical proof. Evidence/precision readers
  reject partial payloads and same-tag payload/summary mismatches; legacy
  candidate artifacts remain historical until rebuilt.

  The offline regression suite covers outages, non-200s, truly malformed JSON,
  missing core fields, wrong objects, proved empty results, TTL and coverage
  expiry, legacy adoption/quarantine including invalid sidecars, batch omission,
  fallback failure, cone-search provenance, pool/evidence time-window
  propagation, window/digest binding, interrupted filtered pools, ALeRCE total/
  repeated-page mismatches, every-row E2 schema/JD checks, TNS interval/pinning,
  cap-bound E2 slices, xmatch schema/radius failure, and cutout failure. The old M1/M2 measurements are
  historical rather than automatically false, but completeness-dependent counts
  must be rerun after the 1,104 suspect entries are refreshed. Candidate work
  must use a new window plus a post-window snapshot before publication or renewed
  operations.

- **2026-08-24 — M2 complete, and the front is closed. Precision measured for the
  first time: the M1 candidate list was NOT SUBMITTABLE at 3.5%; the fixed filter
  reaches 8.0% and cuts image artifacts from 40% to 12%.** Nothing submitted to
  TNS; no account created anywhere; the read-only allowlist in `tnscommon.py` is
  unchanged and was re-verified.

  **Read [`OPERATING-GUIDE.md`](OPERATING-GUIDE.md) instead of this log.** It is
  the hand-over document: nightly commands, every threshold and the rule that
  fixed it, nine known failure modes, M31/M81's September reopening, and the
  end-to-end submission path with the three accounts a human must create.

  **The headline — precision, which M1 could not claim**
  ([`M2-02`](M2-02-precision.md), protocol frozen first in
  [`M2-01`](M2-01-preregistration.md)). Forty objects hand-vetted against ZTF
  cutout triplets, per-band light curves and six archival catalogues: tiers A+B as
  a census, tier C a seeded random sample. **Precision of the 184-object M1 list =
  3.5%, 95% CI [1.1%, 15.6%]** — **40% image artifacts, 53% known or evident
  variables, 2 plausible transients**. The pre-registered rule ("upper bound below
  0.20 → NOT SUBMITTABLE") fired, and so did the second rule: tiers A+B yielded
  one plausible object, below the threshold of two, so **`M1-05`'s declared triage
  did not work either**. Three causes, all measured:
  - **`drb ≥ 0.90` cannot see a bad subtraction.** All 16 artifacts carry
    `drb ≥ 0.913`. The classifier asks "is there a real source in this stamp",
    and for a registration dipole the answer is yes.
  - **The catalogue layer was reading one catalogue when it needed four.** Fink's
    `d:vsx` matched 1 of 40; an independent ATLAS-variable-star match found 14,
    Gaia DR3 variability 2 — **40% were already catalogued and the filter did not
    know**.
  - **The Mira trap is not theoretical.** `ZTF18abobdzu`, written up in `M1-05` as
    the single best candidate, is BP−RP = 5.18, J−K = 1.69, with an ATLAS-VS
    counterpart 0.39″ away and seven years of continuous detection. A red LPV.
  - **The one cheap discriminator M1 had and never used:** 39 of 40 have a Gaia
    DR3 counterpart within 3″; the exception is the one clean dwarf nova.

  **Five fixes, each costed against the M1-04 positive control**
  ([`M2-03`](M2-03-the-fixes.md); the baseline config reproduces M1-04 at exactly
  70/102). **M2 full: recall 46.1%, median lead 3.12 d, negative control 10.0% →
  5.0%, contrast 6.9× → 9.2×.**
  - **(a) per-band amplitude ≥ 1.0 + flat-residual veto — costs 24 objects
    (68.6% → 45.1%)**, and *all 24 are unclassified DCAP reports*: confirmed novae
    stay at 2/3, confirmed CVs at 0/2. It also fixed a mixed-filter bug inside M1's
    own amplitude — `magnr` is per-band, and `M1-05` averaged it across filters.
  - **(b) a real outburst enumerator — the discovery that made it possible is that
    Fink's `/api/v1/latests` accepts `startdate`/`stopdate`**, undocumented in M1.
    Two arms: ALeRCE `firstmjd` for new sources, Fink `latests` across every
    non-vetoed class for known sources erupting, with `magnr − magpsf ≥ 1.0`
    applied at enumeration. **46 of the 51 objects passing the final pass came
    from the new arm; M1's entire enumerator contributed 5.**
  - **(c1) VSX/GCVS demoted to a flag — costs nothing and gains a nova.** Novae go
    **2/3 → 3/3**: `AT 2026lck` is recovered, the confirmed nova `M1-04` lost to a
    `YSO:` mislabel.
  - **(c2) SIMBAD's generic classes demoted — measured effect zero**, reported as
    a null result and kept because the failure mode is structural.
  - **(c3) `_Candidate` suffix stripped before every class comparison** — not
    pre-registered, but a structural symmetry bug with no threshold. `M1-03`
    handled the suffix on the target side and never on the veto side, so `AGN` was
    vetoed while `AGN_Candidate`, `QSO_Candidate`, `Mira_Candidate` and
    `LongPeriodV*_Candidate` (≈2,700 alerts a night) all passed. Zero recall cost.
  - **(d) negative-subtraction veto — POST-HOC, and the best cut in the
    milestone.** A source above its reference cannot subtract negative. **0 of
    DCAP's 98 objects has a single high-confidence negative detection in its whole
    Fink history**, so the cut costs nothing at any threshold from 0.00 to 0.50 —
    and it removes 16 of 40 M1 candidates, all sixteen non-transients, neither
    plausible transient touched.

  **The final list — 37 candidates, MATTHEW-GATED**
  ([`M2-04`](M2-04-final-list.md)). Pool 3,039 over MJD 61274–61277 → 51 pass → 14
  already in TNS → **37**. **Precision 8.0%, 95% CI [2.2%, 25.0%]** on a
  pre-registered random 25; **artifacts 40% → 12%**; a further **32% are real
  dwarf-nova or symbiotic outbursts on already-catalogued stars** — found,
  flagged `known_cv`, and told in words not to file. Real-event rate 40%
  [23%, 59%].
  - **A bug found while vetting and fixed:** the first list had **41 of 44
    candidates whose passing epoch was more than a year before the window**.
    Evaluating a candidate pass without a `jd_floor` fires the filter at the
    object's all-time first pass, so magnitude, amplitude, peak-to-peak and the
    flat veto all described an outburst from 2019. **M1's pass has the same
    defect.** Floored at 60 days; no threshold moved; 44 → 37 candidates and the
    flat veto's catch tripled.
  - **Live fire, unrewound:** 14 of the passing objects were independently
    reported to TNS by other groups from the same three nights — **all 11 that
    reached channel `A2_nova_like` were real transients somebody filed**. Our
    passing epoch preceded their report in **5 of 14**, median −0.55 d, best
    +1.42 d; ZTF's own pipeline filed 11 of them. Thirteen of the fourteen sit at
    |b| > 12°, i.e. outside this front's niche.
  - **Best objects:** `ZTF18accebtg` (19:04:52.95 +09:15:02.8, **|b| = +1.25°**,
    no Gaia counterpart, PS1 reference 21.7, **four outburst episodes** over four
    years, 2.8 mag up — an uncatalogued recurrent dwarf nova in the plane);
    `ZTF19acbplek` (**vetted plausible twice independently**, 13 episodes, 3.7 mag
    up); `ZTF19aampgvg` (21 episodes over seven years, 3.3 mag up).
  - **Submission-grade: five objects vetted as plausible new transients across the
    milestone, and none submittable today** — a TNS AT report is rejected without
    a pre-discovery non-detection, which needs an ATLAS forced-photometry account.
  - **A two-column rule that works:** rows with no `known_cv` flag *and* no
    ATLAS-VS / VSX / Gaia-variability match were 13 of 37, and a full census of
    that subset found **zero artifacts and five plausible transients**.

  **Recommended M3: none for the filter. The front is done.** The one change worth
  making is named and costed in the guide (§4.5): promote Gaia DR3 `vclassre` from
  a printed column to a Layer-3 veto input — it identified five AGN that Fink's
  SIMBAD match calls `Unknown`. Everything else that remains is Matthew's:
  register at TNS, define a bot on production, register at ATLAS forced
  photometry, and walk the §5 check on `ZTF18accebtg`. **M31 reopens in
  mid-September and needs the three changes in §7 first — a cone enumerator, a
  host-galaxy exemption from the nuclear veto, and its own positive control.**

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
