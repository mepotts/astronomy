# M5 — The analogue target list

**Question:** which other substellar companions have public CRIRES+ data good enough to run
the same method on?

**Answer: two, and one of them comes with a built-in positive control.** The pool is far
smaller than frame counts suggest, because what matters is not frames but *nights spread
over time*. Reproduce with `exosat-rv targets`; machine-readable form in
[`data/m5-targets.json`](data/m5-targets.json).

---

## 1. The search had to run backwards

The obvious direction — take a catalogue of imaged companions, ask which have archive data —
cannot work. The NASA Exoplanet Archive caps companion mass at 30 M_Jup and **does not
contain CD-35 2722 B**, so a list built that way omits the object being reproduced and
systematically misses the most favourable hosts.

So M5 asks the archive first: which CRIRES+ pointings name a *companion*? 4,166 distinct
OBJECT strings, filtered by a deliberately loose component-letter pattern, then resolved
against SIMBAD.

**The method carries its own control: CD-35 2722 B must come back.** It does, typed `BD*`,
L0–1. Asserted in `tests/test_catalog.py` so the pipeline cannot silently stop working.

## 2. Resolution needed two stages, and one stage got it wrong

A cone search identifies the *system*; it cannot pick the *component*, because a companion
and its primary are arcseconds apart. The single-stage version resolved **`BET PIC B` to
beta Pic c** — the wrong planet — and **`PZ TEL B` to the G9IV primary**.

The fix is to compare the ESO OBJECT string against every SIMBAD identifier of every object
in the cone, under a normalisation that strips type prefixes and separators (SIMBAD writes
`* bet Pic b`, `V* PZ Tel B`, `CD-35  2722B`; observers write `BET PIC B`). Every target
records `match_kind`, so an `identifier` match is never confused with a `nearest-*` fallback.

Spectral type then outranks SIMBAD's `otype`, in both directions: `tau Boo B` (M3V) and
`HD 149274B` (M5) are typed `*` and would otherwise pass as "borderline". An M3 dwarf is a
star.

## 3. Frame counts are the wrong metric

Ranking by frames puts beta Pic b first with 753. But an RV orbit needs epochs spread over
time, and most of those frames are single deep sequences:

| Target | Nights | Public | Baseline | Span |
|---|---:|---:|---|---:|
| **eta Tel B** (= HR 7329 B) | 26 | **22** | 2023-05-13 → 2025-08-05 | **815 d** |
| **GJ 229 B** (`HD 42581 B`) | 9 | **9** | 2024-02-19 → 2024-10-04 | **228 d** |
| beta Pic b | 6 | 6 | 2022-04-05 → 2025-02-02 | 1034 d, only 6 nights |
| HR-7329-B (2009, pre-upgrade) | 6 | 6 | 2009-08-04 → 2009-09-21 | 48 d |
| AB Pic B | 4 | 4 | 2022-11-02 → 2022-11-05 | 3 d |
| CT Cha B | 3 | 3 | 2025-04-07 → 2025-06-16 | 70 d |
| GSC 08047-00232 B | 3 | 2 | 2025-07-11 → 2025-07-15 | 4 d |
| 2M0103AB B | 1 | 1 | — | 0 |
| eps Ind B | 1 | 1 | 2006 | 0 |

*(CD-35 2722 B's own campaign is 20 public H-band nights over ~460 d — see M0.)*

**beta Pic b's 753 frames are 6 nights.** AB Pic B's 64 frames are 4 consecutive nights.
Neither can constrain an orbit.

## 4. Why the pool is shaped this way

Programme **110.23RW** (Nov 2022 – Feb 2023) is a **pilot survey**: AB Pic B, beta Pic B and
CD-35 2722 B, plus a set of 4-frame standards (KAP ERI, LAM TAU, MU PIC, PHI ERI, TET COL,
ZET PHE, ZET CMA, HD 31331). Everything after it — 112.25HG, 114.271E, 116.2AP9 — is
**CD-35 2722 B and nothing else.**

That is the signature of a pilot that found one thing and concentrated on it. It also means
**this is not white space.** The same group is already running the survey M5 imagines, with
a published null on GQ Lup B (Köhler et al. 2024). Any M5 result is a reanalysis of their
data, not a new search — and SPEC should say so.

## 5. The two real targets

### eta Tel B — the best analogue

22 public nights over 815 days: **better cadence and baseline than the CD-35 2722 B campaign
itself.** M7.5V, typed `LM*`, orbiting an A0V primary at ~4.2″ — wider than CD-35 2722 B's
2.8″, so slit isolation is easier, not harder. Masses in the literature put it near the
star/brown-dwarf boundary; at ~20–40 M_Jup the RV scaling is essentially identical to
CD-35 2722 B's 37 M_Jup, so a satellite of a given mass produces a comparable wobble.

Six further nights exist from 2009 under the name `HR-7329-B`, on the pre-upgrade CRIRES.
Different instrument, so not naively combinable — but a 16-year baseline is worth knowing
about.

### GJ 229 B — the positive control

9 public nights over 228 days at **5.8 pc**, the nearest object in the list by a wide margin
and therefore the brightest. Its CRIRES+ data comes with GRAVITY interferometry under the
same programmes (112.25RU, 112.26Z1).

**GJ 229 B is a known binary brown dwarf.** That makes it the thing this project otherwise
lacks: a target where a companion-induced RV signal is *expected*, so recovering it tests
the pipeline against a known answer rather than against a claim under dispute. That is the
same shape as `itf-linker`'s ground-truth recovery test, and it should be run before any
analogue null result is believed.

**Not yet verified from primary sources:** the binary's orbital parameters, and hence the
amplitude and period the pipeline should recover. Sourcing them is the first M5 task, and
they must come from the discovery paper — not from recall. Compare
[`HANDOFF.md`](HANDOFF.md) §1.

## 6. Both targets already have reduced products

Re-running M0's inventory at each resolved position:

| Target | Band | Usable (public + reduced) | Reduction gap | Baseline | Span |
|---|---|---:|---:|---|---:|
| **eta Tel B** | H | **16** | 9 | 2023-05-13 → 2025-07-21 | **800 d** |
| **GJ 229 B** | H | **11** | 4 | 2024-02-19 → 2025-02-14 | 361 d |
| CT Cha B | K | 2 | 1 | 2025-04-07 → 2025-06-16 | 70 d |
| AB Pic B | K | 2 | 2 | 2022-11-03 → 2022-11-04 | 1 d |

*(CD-35 2722 B: 17 usable H-band nights over 466 d.)*

**eta Tel B has 16 usable H-band nights over an 800-day baseline — nearly the epoch count of
the CD-35 2722 B campaign, over a longer span.** Nothing new needs building: `probe` and the
M2 pipeline apply unchanged.

**Caveat, and it matters more for GJ 229 B.** The inventory uses a 108″ cone, which also
catches pointings on the *primary*. eta Tel B's name-based count (26 nights) and its cone
count (25 H-band) agree, so the cone is essentially all companion. GJ 229 B's do not — 9
by name against 15 by cone — so up to ~6 of its nights are probably GJ 229 A. **Its usable
count is an upper bound until filtered by OBJECT name.**

## 7. What M5 does not establish

- **No H magnitudes.** The flux cut in SPEC is still anchored on an unverified estimate of
  CD-35 2722 B's H mag. SIMBAD does not resolve most companions' photometry. Empirically,
  the existence of usable CRIRES+ spectra is a better feasibility proof than a magnitude
  cut — which is how this list was built — but the cut itself remains unsourced.
- **10 candidates are unresolved or weakly matched** and need by-hand checks: eps Ind B and
  B Aql resolved to nothing (eps Ind's proper motion is ~4.7″/yr, so its catalogue position
  is minutes of arc from where it was observed), and 8 more matched only by proximity.
- **Data quality beyond availability.** `probe` reports structure, not S/N. Whether these
  spectra reach the ~31 m/s the method needs is an M2 question.
