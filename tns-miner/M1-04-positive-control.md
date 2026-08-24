# M1-04 — The positive control: would we have caught them first?

**Date:** 2026-08-24 · **Verdict: PASS** ·
`scripts/m1_positive_control.py` → `out/m1_positive_control.{csv,json}`

> A filter that finds nothing and a filter that is broken look identical from the
> candidate list alone. This is the only test that separates them, and it is the
> acceptance test for M1.

## The headline

**Our filter recovers 70 of DCAP's 102 TNS discovery reports — 68.6% — using only
alert data that existed before DCAP's report was filed. The median lead is 4.15
days; measured within the same outburst episode it is 2.13 days. All 70 lead
times are positive: every object we recovered was in hand before their report
landed.**

| measure | value |
|---|---|
| DCAP reports in the last 12 months (TNS group 195) | 102 |
| resolved to a ZTF `objectId` | 98 |
| **recovered from pre-report data** | **70 (68.6%)** |
| of those with any pre-report alert in Fink | 70 / 97 (72.2%) |
| median lead vs. the report, all-time first pass | **4.15 d** (p25 1.06, p75 1265) |
| median lead vs. the report, **this episode only** | **2.13 d** (p25 0.49, p75 4.83) |
| leads that are positive | **70 / 70** |
| strict variant: only data up to DCAP's own discovery exposure | 30 (29.4%) |

The p75 of 1,265 days is not an error and not a boast — CVs recur, so the
*all-time* first pass for a re-erupting dwarf nova can be an outburst years
earlier that we would also have reported. The **2.13-day episode median** is the
number to quote for "this event".

For context: **DCAP themselves file a median 3.12 days after the discovery
exposure** (p90 11.6 d). The room to move is real, and a 2-day lead sits
comfortably inside it.

## How the rewind is made honest

1. **Cutoff = the true report time,** not the discovery epoch. TNS's search CSV
   only carries the discovery exposure; the moment the report was *filed* lives on
   the object page under *"Time received (UT)"*. Scraped for all 102 objects
   (`scripts/m1_report_times.py`). For AT 2026stb: discovery 2026-07-08 06:35:20,
   report received 2026-07-09 05:04:43 — **22.5 h apart**. Using the discovery
   epoch instead would have been a different, much harsher test; it is reported
   separately as the "strict" row above.
2. **The filter never sees the future.** `F.evaluate(alerts, jd_cutoff=…)` drops
   every alert after the cutoff before any cut runs.
3. **The answer is not hiding in the data.** Fink stamps `d:tns` at ingest and
   never back-fills, verified on ZTF26abfokua: empty on every alert before DCAP's
   report, `Nova` on every alert after. The catalogue veto therefore cannot
   "know" the object was reported.
4. **All 102 report times came back with `first_report_group = DCAP`** — DCAP
   filed first in every single case, so these really are 102 designations that
   were won, not shared.

## What it recovered, by channel

| channel | recovered |
|---|---|
| `A1_cv_outburst` — outburst on a catalogued point source | 36 |
| `A2_nova_like` — new star, nothing in PS1 within 3″ | 29 |
| `C_faint_residue` | 4 |
| `D_galactic_plane` | 1 |

## The class test — it finds novae and refuses supernovae

| TNS object type | recovered / total |
|---|---|
| **Nova** | **2 / 3** |
| CV | 0 / 2 |
| (unclassified) | 66 / 86 |
| SN II | 1 / 1 |
| **SN Ia** | **1 / 10** |

- Both spectroscopically confirmed novae with pre-report alert data were
  recovered: **AT 2026stb** (0.84 d lead, mag 15.06, |b| ≈ −0.6°) and
  **AT 2026rdg** (0.25 d lead, mag 12.53). Both landed in `A1_cv_outburst`, both
  flagged as galactic plane.
- The third nova, **AT 2026lck, was vetoed because VSX catalogues that position as
  a YSO.** That is a catalogue error propagating into our filter, not a filter
  error — but it is a real 1-in-3 loss on the highest-value class and it argues
  for demoting VSX from a hard veto to a flag. **M2 lever.**
- **9 of 10 SN Ia were correctly rejected** — by the nuclear/TDE veto, the SIMBAD
  galaxy veto, or the "no channel: extended non-stellar association" fallthrough.
  The mission scope says avoid nuclear transients and TDEs; the filter does.
- The two CVs failed for *data availability*, not classification: one had zero
  clean detections before the cutoff, one had no Fink alerts before it at all.

## Why the other 32 were missed

| reason | n |
|---|---|
| only 0–1 clean detections at the cutoff | 15 |
| nuclear: on a PS1 galaxy centroid (**correctly out of scope**) | 5 |
| no Fink alerts at all for that object | 4 |
| clean detections span < 30 min — cannot exclude a mover | 3 |
| SIMBAD says Galaxy (**correctly out of scope**) | 2 |
| no alerts before the cutoff | 1 |
| already catalogued in VSX (the YSO mis-ID above) | 1 |
| no channel: bright, off-plane, extended association | 1 |

**Ten of the 32 misses are the filter doing its job** (nuclear, galaxy host, out
of scope). The real losses are the 18 that are data-availability or multiplicity
failures.

**The single biggest structural cost is the 2-detection / 30-minute gate.** It is
what stops the filter firing on the discovery exposure itself, and it is exactly
why the strict variant drops to 29.4% while the report-time variant reaches
68.6%. A human looking at one alert can beat it by up to a night. That gate is
not negotiable at M1 — without it, single-epoch artifacts and slow movers get
into a candidate list, and a false discovery report is a public, permanent,
attributed error. Buying the latency back is an M2 problem (see below).

## The negative control

Sixty TNS objects reported *solely* by the automated pipelines (53 ZTF, 7 ALeRCE),
ZTF-sourced, since 2026-05-01, run through exactly the same rewind with their own
scraped report times. A filter that fires on everything is not a filter.

| | DCAP (target class) | auto-reporters (mainstream) |
|---|---|---|
| n | 102 | 60 |
| recovered from pre-report data | **70 (68.6%)** | **6 (10.0%)** |
| of those with pre-report alerts | 70/97 (72.2%) | 6/28 (21.4%) |
| ever passes at any epoch | 70 | 16 |

**A 6.9× contrast in recovery rate between the class we target and the class the
survey pipelines already own.** The mainstream is dominated by extragalactic
supernovae on resolved hosts, which the nuclear veto (3), the SIMBAD-galaxy /
QSO veto (1) and the "extended non-stellar association" fallthrough are built to
reject. Full numbers in `out/m1_positive_control.json` under `auto_reporters`.

## What this licenses, and what it does not

**Licensed:** the candidate list in `M1-05` is worth reading. The filter
demonstrably recovers the class it targets, from data available before the fact,
with days of margin.

**Not licensed:**

- It does not license reporting anything. Every candidate is Matthew-gated.
- 68.6% is *recovery of DCAP's chosen objects*, not precision on fresh data. The
  candidate list's false-positive rate is unmeasured — nothing in M1 tells you
  what fraction of a fresh pass is junk. That is the M2 acceptance test.
- The lead time is measured against **DCAP's filing latency**, which is generous
  (median 3.12 d). Against a same-night reporter like LAST (median 0.19 d) the
  same filter would lose.
