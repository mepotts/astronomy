# M7 — Attribution: old ITF tracklets against the Rubin bulk-batch orbits

**Date:** 2026-08-16 · **ITF snapshot:** `Last-Modified: Sun, 16 Aug 2026 20:27:01 GMT`,
133,928,330 B, 9,292,997 lines → **9,255,644 observations**, 2,611,699 tracklets
(provenance in `data/raw/itf.provenance.json`; every count below is against this pull).
**Nothing was submitted anywhere. Candidates are candidates.**

**One-line result:** attribution — matching ITF orphan tracklets to *known* orbits —
did not exist in this pipeline and now does as a thin validated slice: 349 orbits from
Rubin's verified 2026-02-05 bulk batch swept against 703,643 ITF tracklets inside a
*measured* 4-year two-body validity window, with an amplitude-matched decoy control run
alongside and Find_Orb joint fits as the arbiter. The coarse gate's 914 matches are
statistically indistinguishable from the decoy's 944 — and the fits then rejected 148
of the 150 fitted, which is the discipline working. What survives every gate is **one
attribution candidate: 2025 PD152 ← two independent same-night Pan-STARRS tracklets
of 2022-10-02** (7 detections, all used, combined RMS 0.0905″, no other known object
within 105″), which would extend a 30-day single-opposition arc to **2.9 years and a
second opposition** — plus one borderline 0.0007″ over the frozen strict ceiling.
Prepared for Matthew's review; **not submitted**.

---

## 1. Scope check, answered plainly

**The pipeline did not support attribution.** M0–M5 are ITF-internal end to end: M1
fits designations the ITF already groups, M3–M5 link ITF tracklets *to each other*,
and M2's vetting asks the inverse question ("is this candidate link a known object?"
— a position cone-search against MPChecker/SkyBoT/SBIDENT), never "which ITF
tracklets are consistent with this known orbit?". No module ingested an external
orbit. The deliverable was therefore the thinnest working slice, built almost
entirely from parts this repository had already validated:

| New | Reused unchanged |
|---|---|
| `src/itf_linker/attrib/core.py` — mpc_orb parse (ecliptic CAR state → ICRS equatorial), two-body geocentric prediction with light-time, phase-shifted decoy control | `link/geometry.py` (Earth ephemeris, universal-variable propagation, frames), `fit/findorb.py` (`run_fo`, per-worker config dirs, Linux scratch), `fit/gates.py` (both post-fit gates), `link/assemble.py` (`tracklet_line_index`, `_relabel`, `link_key`), `fit/extract.py` (verbatim 80-column lines), `mpc80.py` |
| `scripts/m7_fetch_orbits.py` · `m7_calibration.py` · `m7_attribution.py` · `m7_tno_stat.py` | vetting-layer politeness discipline (≥1.1 s spacing, disk cache, identifying User-Agent, retry-with-backoff) |
| `tests/test_attrib_core.py` — 10 tests against captured fixtures + recorded Horizons truth | the whole existing suite — **447 tests green** (437 + 10) |

## 2. The premise, verified against primary sources

Every load-bearing external claim was re-verified this run; two of the run-3 report's
citations resolved to different-but-real places.

| Claim | Verified against | Result |
|---|---|---|
| Rubin submitted a bulk batch ~Feb 5: ~20k candidates / ~246k obs | [MPC Newsletter, Feb 2026 (PDF)](https://www.minorplanetcenter.net/media/newsletters/MPC_Newsletter_Feb2026.pdf) | ✓ verbatim: *"On the night of February 5, 2026, the Rubin team submitted a large batch of approximately 20,000 candidate discoveries, corresponding to roughly 246,000 individual observations."* |
| Same batch, independent count | Asteroid Institute daily partition `2026-02-06` (below) | ✓ **245,904 rows** — the newsletter's "roughly 246,000" on the nose |
| ~1M obs / 11k+ new asteroids announced Apr 2 | [rubinobservatory.org/news/11000-new-asteroids](https://rubinobservatory.org/news/11000-new-asteroids) | ✓ "approximately one million observations of over 11,000 new asteroids and more than 80,000 already known" (2026-04-02) |
| Rubin does **not** put 2-detection tracklets in the ITF | [community.lsst.org thread 11548](https://community.lsst.org/t/method-of-report-to-minor-planet-center-by-rubin/11548), A. Heinze reply 2026-02-07 | ✓ *"two-point tracklets cannot be submitted to the MPC without overwhelming the ITF"*; future unlinked-tracklet submissions (3–4+ detections) planned, **not yet begun** (J. Kurlander, same day) |
| `ls.st/ast` (run-3 citation) | followed the redirect | 301 → **`b612.ai/rubin-mpc-downloads/`** — Asteroid Institute page serving X05 observations from their BigQuery replica of the MPC obs database: full dumps (`obs_sbn_X05_full.{csv.gz,parquet}`, `rubin.sqlite.gz`) + daily partitions keyed by `public_obs_sbn.created_at`, public GCS bucket `asteroid-institute-public`, no auth |
| MPC accepted 58,116 ITF-ITF + 49,986 ITF-DES in 2025 | [identifications stats 2025](https://www.minorplanetcenter.net/mpcops/documentation/identifications/stats/2025/) | ✓ exact, plus DES-DES 4,746 · NEOCP 1,310 · **26 NEOs discovered from ITF linkages** |
| Orbits/observations APIs | [orbits-api](https://www.minorplanetcenter.net/mpcops/documentation/orbits-api/) / [observations-api docs](https://www.minorplanetcenter.net/mpcops/documentation/observations-api/) | ✓ `data.minorplanetcenter.net/api/get-orb` (`{"desig": …}` → `mpc_orb` with CAR/COM state + covariance + fit stats) and `/api/get-obs` (`{"desigs": […], "output_format": ["OBS80"]}` → the published 80-column record). Anonymous GET, no key |

## 3. The headwind, found in the same primary source

The February newsletter documents (p. 2) that the MPC's dedicated Rubin pipeline
**already checks the ITF at designation time**: for every candidate that fits cleanly
and looks new, *"we check if the orbit belongs to any known object or if ITF
tracklets from the ITF can be linked to the object"*, and found matches are
**automatically linked and consumed** (the tracklets leave the ITF; no new
designation). The subset carries direct evidence: **2025 MH98**'s published record
*opens* with an F51 (Pan-STARRS 1) line dated 2025-06-29 carrying the discovery
asterisk, and 2025 MQ241's record contains F52 astrometry — archival precovery was
folded in at or after designation.

So the pool this milestone sweeps is the *residue* of the MPC's own automated
ITF check: what their sweep missed, plus what has churned into the ITF since
February. The expected yield is small, and a zero reported plainly is a success
condition (standing constraint 5). What the milestone must deliver either way is a
working, gated, controlled attribution capability — that is the durable output.

## 4. The batch and the validation subset

The 2026-02-06 partition (`created_at` 01:00–01:17 UTC — one 17-minute ingestion):

| Quantity | Count |
|---|---:|
| Observations | 245,904 |
| … with a current provisional designation (`provid`) | 244,152 → **19,347 objects** |
| Objects with an in-batch discovery asterisk | 17,043 (one per object) |
| Objects already numbered | 104 |
| Observations left unattributed in the replica | 1,752 |
| `obstime` span | **2025-06-20 → 2025-12-24** — HelioLinc3D linkages span months, not nights |

**Subset: the 400 brightest unnumbered new discoveries** (in-batch mean mag 19.71 →
21.30). Brightness is the honest selection axis for a *precovery* validation: the ITF's
archival mass is Pan-STARRS/Catalina/DECam at limits ~21.5–23, so only the bright tail
of Rubin's (median mag 22.4) discoveries can plausibly appear in it.

`get-orb` returned a current orbit for **400 of 400**. After parsing: **2** were
secondary designations of another subset member (the API resolves merges — e.g.
2025 PD126 → primary **2025 MH98**, three designations deep), **49** carried
U > 6 (along-track runoff > ~26′/decade — no coarse gate survives that) and were
excluded, leaving **349 swept orbits**. Two primaries are 2014/2015 designations
(2014 OM341, 2015 RX139): Rubin re-found decade-old single-opposition objects, and
the MPC's merge machinery quietly upgraded them to two-opposition orbits — worth
knowing when "new discoveries" is the label on a batch.

## 5. The gate is measured, not assumed

The sweep propagates each orbit with the linker's own two-body propagator
(`link/geometry.py`), which neglects planetary perturbations. Rather than guess the
resulting position error, `scripts/m7_calibration.py` measures it in the M1
self-test's pattern — current MPC orbit from the same `get-orb` API, two-body'd
backwards, compared against **JPL Horizons** astrometric geocentric truth for four
numbered asteroids spanning the subset's orbit space (nothing in the truth values
touches this repo's code):

| Lookback | (7) Iris a=2.39 | (170) Maria a=2.55 | (24) Themis a=3.13 | (153) Hilda a=3.97 |
|---|---:|---:|---:|---:|
| 0.25 y | 4.2″ | 0.5″ | 1.8″ | 0.8″ |
| 1 y | 3.5″ | 39.0″ | 8.6″ | 13.7″ |
| 2 y | 559″ | 186″ | 112″ | 110″ |
| 3 y | 516″ | 99″ | 379″ | 304″ |
| 4 y | 491″ | 336″ | 57″ | 106″ |
| 5 y | 1,295″ | 264″ | 3,537″ | 621″ |
| 10 y | 1,320″ | 98″ | 3,367″ | **6,776″** |
| 15 y | 1,781″ | 978″ | **7,545″** | 4,132″ |

Two-body prediction is tens-of-arcsec inside a year, ~10′ out to four years, and
**degree-scale by 5–15** — the deep, pre-2023 ITF (exactly where M4/M5 located the
cross-survey pool) is *unreachable by a two-body coarse gate at any radius that
still rejects anything*. Hence, the thin slice bounds itself:

- **Window:** |t − epoch| ≤ 4.0 years (703,643 of today's tracklets).
- **Position gate:** `120″ + 1.5 × envelope(|Δt|) + runoff(U)·|Δt|/decade`, the
  envelope being the monotonicised max of the four curves above (a gate that
  *shrank* with lookback would claim precision the calibration never demonstrated);
  U-runoff `0.01″·10^0.868·U` per decade. Floor covers the geocentric approximation
  (≤ ~9″/AU parallax) and the young orbit's cross-track uncertainty.
- **Rate gate:** predicted-vs-observed rate vector within
  `3″/hr + 25% · |μ_pred| + 2·0.3″/span` — the last term is the tracklet's own
  endpoint noise. Tracklets need n_obs ≥ 2 (rates from verbatim endpoint pairs, RA
  wrapped ±180°).
- **The arbiter is never the prediction:** every surviving candidate goes to a full
  Find_Orb fit of the object's complete published astrometry *plus* the tracklet,
  gated like every other fit in this repository.

## 6. The sweep, and the control that prices it

Every orbit was also swept as an **amplitude-matched decoy**: the same state
propagated half a period, so a, e, i, the node, the rate statistics and the time
spent in each sky region are identical — only *where the object actually is* is
scrambled. (M9 of the sibling exosat-rv project is why this is house law: an
unmatched control screens nothing.)

| | real orbits | phase-shifted decoys |
|---|---:|---:|
| Coarse matches | **914** | **944** |
| Orbits with ≥ 1 match | 254 | 258 |
| Median separation | 673″ | 730″ |
| Median |Δt| | 1,071 d | 1,339 d |

**The coarse gate's aggregate yield is chance.** Real ≈ decoy to within Poisson
noise: at radii of hundreds of arcsec over a 700k-tracklet window, the position+rate
gate admits ~2.6 background tracklets per orbit and possible true attributions are
invisible in the totals. Where they would show is the smallest separations — chance
scales with enclosed area, truth piles up at the prediction:

| separation bin | real | decoy |
|---|---:|---:|
| [0″, 30″) | 2 | 2 |
| [30″, 60″) | 2 | 6 |
| [60″, 120″) | 10 | 16 |
| [120″, 300″) | 87 | 89 |
| [300″, 600″) | 269 | 228 |
| [600″, 1000″) | 489 | 454 |
| [1000″, 2000″) | 55 | 149 |

**There is no excess at small separation either.** The decoy produces sub-30″
coincidences at the same rate as the real orbits — with ~350 orbits, a 700k-tracklet
window and the MPC having already consumed the easy precovery at designation time
(§3), zero-to-few true matches buried in 914 is exactly this picture. The coarse
sweep therefore *selects candidates for fitting*; it demonstrates nothing by itself,
and no separation threshold would have. Only the joint fit separates truth from
background — including at 3.5″, where the single tightest coarse match in the whole
run sits and does **not** survive (§7).

## 7. Joint fits — the arbiter

The 150 best-separated real candidates (104 distinct orbits) were fitted: the
object's **complete published astrometry** (get-obs OBS80 — 26–57 observations each,
often already multi-survey) plus the ITF tracklet's **verbatim 80-column lines**,
relabelled under one tag and fitted by the same `fo` build, perturbers `7fe`,
DE-440, as every M1–M5 fit. Each orbit also got an object-only baseline fit. Whole
run — both sweeps plus 248 Find_Orb invocations — 391 s wall-clock, fits on the
Linux-side scratch per M5's 9× measurement.

| Outcome (150 fitted) | n |
|---|---:|
| Converged | 149 |
| Pass the **MPC published** post-fit rule | 149 |
| Pass the strict M1–M5 gate | 91 |
| Fit **used every tracklet observation** | 36 |
| Both of the above | 3 |
| … **and** ≥90% of joint set used **and** not already in the published record | **2** |

Failure reasons (a candidate can carry several): tracklet not fully used **114**,
joint set <90% used **115**, strict-gate rejections **59**, non-convergence **1**
(a 2-observation degenerate the convergence rule catches by `n_used < 3`).

Two findings about the gates themselves:

* **Convergence and the published rule are nearly vacuous for attribution.** 149 of
  150 pass both — a joint arc of 1–3 years clears every conjunctive arc-length
  bullet, so the published rule only ever rejects non-convergence here. All the
  discriminating power is in the question M1's subset guard taught this repository
  to ask: *did the least-squares actually use the new observations?* `fo` quietly
  excludes a wrong tracklet and converges beautifully on the rest — 114 of 150 did
  exactly that. A pipeline that checked only "converged + RMS" would have declared
  dozens of false attributions.
* **The tightest coarse match failed honestly.** 2025 MQ241 + `nf2088` (W76
  CHILESCOPE, three detections, 2025-07-24) matched at **3.5″** — the best
  separation in the run, rate-consistent, and the object's published record already
  carries W76 astrometry from *other* nights. The joint fit uses all three
  detections but lands at RMS **0.25066″** — 0.0007″ over the frozen strict
  ceiling (baseline 0.165″, so the tracklet does degrade the fit), while passing
  the MPC's published rule. Under this project's rules that is a **borderline for
  the human**, not a pass: the strict gate stays frozen (HANDOFF law), and the
  degradation pattern is consistent with either slightly poor amateur astrometry of
  the right object or a wrong association. It is listed for Matthew's judgement,
  clearly marked.

**The survivor is one object with two independently-passing tracklets:**

**2025 PD152** — Main Belt, H = 20.0, and one of the *worst-constrained* orbits in
the subset: single opposition, **30-day arc**, 26 observations, **U = 6** (just
inside the cut; its U-runoff term is what widened the gate to admit a ~200″
separation at 3.1 years lookback — the gate design paying off on exactly the case
it was built for).

| | `P11zG98` | `P11zFtH` | combined |
|---|---|---|---|
| F51 Pan-STARRS 1, 2022-10-02 UTC | 4 detections, 11:58–12:57 | 3 detections, 09:11–09:51 | 7 |
| Coarse separation / gate | 197″ / pos+rate pass | 203″ / pos+rate pass | — |
| Joint fit | RMS 0.086″, 30/30 used | RMS 0.091″, 29/29 used | **RMS 0.0905″, 33/33 used** |
| Max tracklet residual | 0.18″ | 0.22″ | 0.25″ |
| Orbit (a, e, i) | 2.1674, 0.1661, 3.611° | 2.1674, 0.1661, 3.611° | 2.16745 ± 0.0000013 AU |
| Both gates (strict + published) | pass | pass | pass |

The two tracklets are disjoint Pan-STARRS sequences **2.8 hours apart** whose
positions continue each other along the fitted motion (RA 01:02:21 → 01:02:19 →
gap → 01:02:14 → 01:02:11, exactly the −40″/hr the orbit predicts); Pan-STARRS
never cross-linked them, and each *independently* lands on the same orbit to four
decimals — a mutual confirmation neither the sweep nor the fit was told to look
for. Predicted magnitudes agree with the measured ones to 0.05–0.15 mag
(v_pred 21.83/21.84 vs w-band 21.78/21.94). A SkyBoT cone search at the 2022
epoch/position returns exactly one known object within 6′ — 2013 PY12 at
**104.9″** with a 0.22″-accurate ephemeris — so no other catalogued body can claim
the detections; and the tracklet epochs/positions appear nowhere in the object's
published record (the ALREADY_LINKED check found 0 duplicates of 7).

Accepting the attribution would extend 2025 PD152's arc from **30 days to ~1,060
days** and from one opposition to two, collapsing σ(a) to ~1.3 × 10⁻⁶ AU. It would
also explain *why the MPC's own designation-time sweep missed it*: in February the
orbit was 30 days old with U = 6 — back-propagated to October 2022 its position
uncertainty was hundreds of arcsec at minimum, beyond any tight automated matcher,
and only a wide-gate + rate-test + full-fit chain reaches it.

## 8. The deliverable: a gated candidate list, and the submission that was NOT made

| # | Rubin object | ITF tracklet (`link_key`) | Δt | sep | joint RMS | tracklet used | strict | published | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **2025 PD152** (K25PF2D) | `P11zG98` F51 night 59854 — `lk6230bd2f8b02f30d` | −3.14 y | 197″ | 0.086″ | 4/4 | ✓ | ✓ | **PASS** |
| 2 | **2025 PD152** (K25PF2D) | `P11zFtH` F51 night 59854 — `lk6fa8132ffbde598b` | −3.14 y | 203″ | 0.091″ | 3/3 | ✓ | ✓ | **PASS** |
| 3 | 2025 MQ241 (K25M41Q) | `nf2088` W76 night 60880 — `lkd3386eec6d56df1d` | −0.33 y | 3.5″ | 0.2507″ | 3/3 | ✗ (by 0.0007″) | ✓ | **borderline — human call** |

(1) and (2) stand together: one object, one night, two independent tracklets, one
combined 33-of-33 fit at 0.0905″. The stable citation for each tracklet is its
content-addressed **`link_key`** (hashed from the `(trkSub, obscode, night)` member —
HANDOFF §4; the run-local ids inside `m7-attribution.json` are not citable). Full
verdict table for all 150 fits: `m7-verdicts.json`.

**What a submission WOULD look like** — format only, per the
[submission-format doc](https://www.minorplanetcenter.net/mpcops/documentation/identifications/submission-format/),
JSON to `…/mpcops/submissions/identifications/`:

```json
{
  "header": {"name": "…", "email": "…",
             "comment": "archival precovery: ITF F51 tracklets attributed to 2025 PD152"},
  "links": {
    "link_0": {
      "designations": ["K25PF2D"],
      "trksubs": [["P11zG98", "2022-10-02", "F51"],
                  ["P11zFtH", "2022-10-02", "F51"]]
    }
  }
}
```

**No submission code exists in this repo and none was written for M7.** Whether this
candidate goes anywhere is Matthew's decision alone; if it ever does, the MPC's
sandbox (`submit_psv_test`/`submit_xml_test`) comes first, per standing
constraints 1–2. What can be said for it: every gate this project trusts passes,
both tracklets corroborate each other, the magnitude and rate match, no other known
object is within 105″, and the fit that would accompany it uses every observation.

## 9. The TNO-niche feasibility stat (deliverable 5)

Over the full snapshot — tracklets (desig × obscode × local night), n_obs ≥ 2,
span > 0, endpoint great-circle rate:

| Quantity | Count |
|---|---:|
| Rate-measurable tracklets | 2,605,223 |
| … north of Dec +30° | 111,468 |
| … **north of +30° AND slower than 10″/hr** | **5,435** |
| … of those, span ≥ 30 min (rate robust against 0.3″ endpoint noise) | **3,239** |

The slow-northern pool is dominated by **T09 Subaru (2,651)** and **645 SDSS
(1,464)**, with year-spikes at 2019 (1,904 — the Subaru HSC deep work), 2000–2003
(SDSS era) and 2016. A TNO at opposition moves 1–3″/hr; at these counts the northern
slow-mover niche is a *few-thousand-tracklet* problem — small enough to fit
exhaustively once a distant-band gating build exists, and sitting in exactly the
deep-survey data (Subaru) whose operators do not run their own ITF recovery.
Numbers: `scripts/m7_tno_stat.py` → `data/raw/rubin/m7-tno-stat.json`.

## 10. Traps hit (all paid for; check before touching this code)

1. **Horizons TLIST replies are chronological regardless of request order.** The
   first calibration paired the 1-year prediction with the 15-year truth row and
   reported 55–170° "propagation errors" for all four targets. Diagnosed by
   predicting at the orbit epoch itself (0.015″); fix is to sort the request.
2. **`mpc_orb` CAR states are heliocentric *ecliptic*** (`system_data.refsys:
   "Ecliptic"`, obliquity 84381.448″) at an **MJD/TDT** epoch. Feed them to the
   ICRS-equatorial linker unrotated and everything is up to 23.4° wrong.
   `parse_mpc_orb` asserts the frame per document and refuses anything else.
3. **`get-obs` OBS80 for a merged object carries multiple packed designations**
   (2025 MH98 = K25M98H + K25N71B + K25PC6D lines interleaved). Unrelabelled, `fo`
   fits them as separate fragments — the first baseline implementation did exactly
   that; caught mid-run, relabelled under one 7-char tag, rerun.
4. **`fo`'s residual records name the station `obscode`, not `obs_code`.** The
   wrong key matches nothing and silently reports every tracklet as *unused* —
   which inverts the meaning of the subset-guard check. Verified against a live
   `total.json` before trusting any per-tracklet residual number.
5. **The trkSub field is 7 characters; `_relabel` truncates.** An 8-character fit
   tag (`m7att000`) silently labels the obs file `m7att00`. Harmless in
   single-object runs; fatal the day two tags collide inside one run. Tags are now
   7 characters.
6. **`mag` is a *string* column in the Asteroid Institute parquet** — cast before
   arithmetic, or polars raises on `.quantile()` only after `.mean()` silently
   produced garbage-free-looking output.
7. **Daily partitions are keyed by `created_at`, not `obstime`.** The "Feb 5 batch"
   is partition 2026-02-06 (ingested 01:00–01:17 UTC), and its *observations* span
   2025-06-20 → 12-24. Filtering MPCORB-style by designation half-month (2026 C…)
   would have found nothing: the batch designates by **discovery date** — 2025 M/N/P….
8. **Designation merges shrink a "batch object list" under you**: 400 requested
   orbits → 351 distinct primaries (2 in-subset collisions; several secondaries),
   two of them 2014/2015 objects. Dedupe on `packed_primary_provisional_designation`,
   never on the requested name.
9. **Windows console is cp1252** — polars' box-drawing repr crashes `print` unless
   `PYTHONIOENCODING=utf-8`.

## 11. Recommended next milestone (M8)

1. **A perturbed ephemeris backend** — `fo` can emit ephemerides from the same
   astrometry it fits; per-object ephemerides would open |Δt| > 4 y, which is where
   the pre-2023, cross-survey ITF mass sits (M5 measured that pool at 213 survivors
   for ITF-ITF; attribution reaches it with far better-conditioned orbits). This is
   the single change that converts M7 from validation slice to production sweep.
2. **Scale the batch axis**: 349 → all 19,347 Feb objects + the ~11k April batch
   (the sweep is ~0.3 s/orbit; fits are the cost and the coarse gate already prices
   them via the control).
3. **SkyBoT cross-check** on every fit survivor (the M2 layer, unchanged) — an ITF
   tracklet can fit a Rubin orbit *and* belong to a different known object; only a
   cone search rules that out.
4. **The watcher** (run-3 prospectus): new bulk batch lands → attribution run
   queued automatically, per-batch human review always.

---

*Generated by `scripts/m7_attribution.py`; full per-candidate detail in
`m7-attribution.json` (root, gitignored by the `/m[0-9]*.json` pattern, regenerable
from the cached inputs under `data/raw/rubin/`).*
