# M1-02 — The gap, measured (and the founding premise is half wrong)

**Date:** 2026-08-24 · **Status:** complete · reproduce with `scripts/m1_gap.py`

Every number below comes from a tokenless harvest of the TNS public search CSV,
`https://www.wis-tns.org/search?…&format=csv`, taken 2026-08-24: **30,454 objects**
with discovery dates 2025-08-01 → 2026-08-24, TNS IDs 185270–218750. Raw data in
`data/tns/` (gitignored); derived tables in `out/m1_gap.json` and
`out/m1_gap_groups.csv`.

The instruction was to test the sweep's claims rather than inherit them. Three of
the four fail.

---

## C1 — "~80% of TNS reports come from five automated pipelines: Pan-STARRS 26%, ZTF 17%, ALeRCE 14%, ATLAS 13%, Gaia 10%"

**Verdict: the shape is right, the five names are not, and one of them has stopped
reporting entirely.**

Measured over the last 12 months, **51 distinct reporting groups**. A report may
name several groups, so two counts are given: *credit* (each named group scores
one) and *sole* (only reports naming exactly one group).

| Group | credit % | sole % |
|---|---|---|
| ATLAS | 27.29 | 4.74 |
| Pan-STARRS | 27.09 | 12.22 |
| **GOTO** | 26.94 | 4.50 |
| **WFST** | 26.68 | 18.76 |
| ZTF | 26.05 | 6.85 |
| ALeRCE | 12.01 | — |

- **Gaia filed zero discovery reports in the whole 12-month window.** The sweep
  lists it at 10%. Source URL for the claim is the sweep itself; the measurement
  says the group does not appear in the TNS reporting-group column at all.
- **WFST and GOTO are now top-five reporters and neither appears in the sweep's
  list.** WFST alone is the single largest *sole* reporter at 18.8% — it is a
  faint, high-galactic-latitude machine (median discovery mag 21.52, 0.4% of its
  reports at |b| < 15°).
- The five names the sweep gives sum to 92.4% on a credit basis, but that number
  is inflated by multi-group reports; the honest reading is that **five machines
  dominate, they are ATLAS / Pan-STARRS / GOTO / WFST / ZTF, and the list churns
  fast enough that a year-old list is wrong.**

## C2 / C3 — "the bright end is dead; the faint end (mag 19–20.6) is under-reported; DCAP lives at 19–20.6"

**Verdict: inverted. The faint end is where TNS already is. The gap is the BRIGHT
end, and it is in the galactic plane.**

All 30,454 TNS reports, discovery magnitude:

| statistic | value |
|---|---|
| median | **20.36** |
| 5 / 25 / 50 / 75 / 95 pct | 18.42 / 19.59 / 20.36 / 21.44 / 22.75 |
| fraction brighter than 18.5 | **0.056** |
| fraction 19.0–20.6 | **0.450** |
| fraction fainter than 20.6 | 0.432 |

45% of everything TNS receives is already inside the "under-reported" band, and
another 43% is fainter still. Only **5.6%** of TNS reports are brighter than 18.5.

Now the same cut on the group we are trying to imitate:

| Group | n | median mag | frac mag < 18.5 | median \|b\| | frac \|b\| < 15° |
|---|---|---|---|---|---|
| **DCAP** | 103 | **18.74** | **0.437** | **12.8°** | **0.553** |
| **XOSS** | 297 | **18.24** | **0.579** | **10.4°** | **0.680** |
| ZTF | 7,934 | 19.82 | 0.056 | 41.1° | 0.076 |
| ATLAS | 8,310 | 19.43 | 0.111 | 40.4° | 0.081 |
| GOTO | 8,205 | 19.73 | 0.079 | 41.8° | 0.076 |
| Pan-STARRS | 8,250 | 20.52 | 0.023 | 45.2° | 0.023 |
| WFST | 8,126 | 21.52 | 0.009 | 55.7° | 0.004 |
| ALeRCE | 3,657 | 20.65 | 0.021 | 43.1° | 0.046 |
| **all TNS** | 30,454 | 20.36 | 0.056 | **46.2°** | **0.058** |

**DCAP's median discovery is 1.6 mag BRIGHTER than TNS's median, not fainter.**
And the axis that actually separates DCAP and XOSS from every survey pipeline is
not magnitude at all — it is **galactic latitude**. 5.8% of all TNS reports are at
|b| < 15°. For DCAP it is 55%, for XOSS 68%. Every automated reporter sits between
0.4% and 8.1%.

That is the gap, and it is a *filter-policy* gap exactly as the project premise
argued — just on a different axis than the premise named. The survey pipelines are
tuned for extragalactic supernovae: they demand a resolved host, they cut on
star/galaxy score, and they avoid the crowded, extinguished, high-surface-
brightness plane. Everything stellar and in-plane falls out, at *any* magnitude.

**Consequence for this project:** the filter's bright-magnitude floor was moved
from 16.0 to 12.0 and a dedicated galactic-plane channel was added. Both changes
are recorded in `M1-03-filter.md` and were made before any candidate was counted.

## C4 — "~90% of TNS objects sit unclassified"

**Verdict: confirmed.** 2,407 of 30,454 objects in the window carry an object
type: **92.1% unclassified**. The hard gate stands — a classification report needs
a spectrum, so this project can produce discoverers, not classifiers.

---

## How long the reporters take

TNS object IDs are issued in report order, so
`report_clock(ID) = running max of discovery epoch over all IDs ≤ that ID` is a
**lower bound** on when each ID was filed. Validated against the true
"Time received (UT)" scraped from TNS object pages (see `M1-04`).

| Group | n | median report lag (lower bound, days) |
|---|---|---|
| LAST | 1,602 | 0.19 |
| XOSS | 297 | 0.32 |
| MASTER | 361 | 0.37 |
| ATLAS | 8,310 | 1.07 |
| GOTO | 8,205 | 1.22 |
| ZTF | 7,934 | 2.57 |
| **DCAP** | 103 | 2.72 |
| Pan-STARRS | 8,250 | 6.08 |
| WFST | 8,126 | 7.23 |
| all | 30,454 | 3.64 |

Nobody is fast. The median TNS report is filed **days** after the exposure that
found it, and Pan-STARRS and WFST — two of the five biggest — take a week. A
pipeline that turns a night's alerts around in under 24 h is competitive with the
entire field on latency alone.

---

## What the auto-reporters are leaving: the direct count

Window: **MJD 61241–61243** (nights of 2026-07-20 and 2026-07-21) — chosen 34 days
in the past so that every report for it has already been filed, so "not in TNS"
is a fact and not a race. Pool: every ZTF object whose first-ever detection falls
in the window with ≥2 detections, enumerated from ALeRCE (`firstmjd` range,
tokenless), enriched from Fink, cross-matched against the full 12-month TNS
harvest at 3″.

| layer | n | in TNS | **not in TNS** | unreported |
|---|---|---|---|---|
| A. whole pool (new ZTF objects, ndet ≥ 2) | 1,350 | 3 | 1,347 | 99.8% |
| B. passes a sane real-transient hygiene filter | 214 | 3 | **211** | **98.6%** |
| C. passes our targeted channels | 7 | 1 | 6 | 85.7% |

**≈105 defensible real-transient detections per night are never reported to
anybody**, and ≈3 per night fall inside the classes this project targets.

Two honest caveats on that number:

1. **It is a floor, not a ceiling.** The pool contains only objects whose *first
   ever* ZTF detection is in the window. A previously-catalogued CV going into a
   new outburst — DCAP's bread and butter — is invisible to this enumeration. The
   candidate pass in `M1-05` adds Fink's `latests` stream to partly cover that;
   closing it properly is the top M2 lever.
2. **"Passes a hygiene filter" is not "is worth reporting".** Layer B is the
   count of things that are real, positive, multiply-detected, not a known minor
   planet, and not in any variable-star catalogue. Most are still ordinary faint
   extragalactic transients that nobody has any obligation to name.

## Stream volume, for scale

From Fink's own nightly counters (`/api/v1/statistics`, 182 nights of 2026):
median **135,245** science alerts per night, max 313,532; the last 30 nights
median **97,188** (the seasonal low). The public ZTF tarballs at
`https://ztf.uw.edu/alerts/public/` run 1–15 GB per observing night, 2,990
nightly files, newest `ztf_public_20260824.tar.gz` posted 2026-08-24 07:15.

---

## Sources

- TNS public search CSV — `https://www.wis-tns.org/search?…&format=csv`
- TNS object pages (report times) — `https://www.wis-tns.org/object/<name>`
- ALeRCE object query — `https://api.alerce.online/ztf/v1/objects/`
- Fink object / statistics API — `https://api.ztf.fink-portal.org/api/v1/`
- ZTF public alert archive — `https://ztf.uw.edu/alerts/public/`
- DCAP — `https://dcap-minruining.github.io/DCAP/` (TNS reporting group 195)
