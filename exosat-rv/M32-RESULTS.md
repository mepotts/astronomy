# M32 — the η Tel B note, and what preparing it for outside eyes turned up

> **Status: the RNAAS note is prepared, not submitted.** Submission is Matthew's call
> (`LESSONS.md` §6). The draft is [`docs/paper/rnaas-etatel-draft.md`](docs/paper/rnaas-etatel-draft.md);
> every number in it is printed by [`scripts/m32_etatel_numbers.py`](scripts/m32_etatel_numbers.py).

The task was narrow: package the M15 η Tel B first-limit result as a Research Note. Writing
for readers outside the repo forced every input to be sourced, and four of them turned out to
be wrong, unattributed, or missing. Three of those corrections reach beyond this note.

## 1. Nothing is hand-typed

`m32_etatel_numbers.py` regenerates the entire sensitivity table from `data/m15-limit.json`.
This is a direct response to M29's audit, which found 34 conflicting values that had entered
by hand-transcription between a result and a document. A document that goes outside the repo
cannot carry that risk.

It also makes two things explicit that prose hides. K₉₀ is **read off the measured detection
grid** — the smallest injected amplitude reaching 90% — not interpolated and not fitted. And
the formula is checked against the source paper's own numbers: Hoy et al.'s K₁ = 306 m/s,
P = 171.45 d, M = 37 M_Jup gives **0.915 M_Jup against their published 0.918 — 0.3%**.

The limit itself is unchanged from M15 and M28: **m sin i ≳ 0.51–1.27 M_Jup over
P = 20–300 d**, at 90% detection probability with a criterion whose measured false-alarm rate
is ≤ 0.85%.

## 2. The companion mass: the repo's attribution was wrong, and the value is disputed

The repo carried **47 M_Jup**, sourced as "Lazzoni T1 → Langlois et al. 2021b, not archived",
flagged by `PROPERTY-AUDIT.md` as single-source. The headline limit scales as M^(2/3), so this
was the most load-bearing unverified input in the note.

Run down through Chai et al. 2024 (now archived, `papers/text/chai2024_etatel_jwst.txt`):

| determination | value (M_Jup) | method | independent? |
|---|---|---|---|
| Lazzoni et al. 2020, A&A 641, A131 | **47 (+5/−6)** | AMES-COND evolutionary models | ✅ |
| Chai et al. 2024, ApJ | **29 (+16/−13)** | JWST/MIRI MRS atmospheric fit | ✅ |
| Chai et al. 2024, ApJ | 42 ± 14 | orbital posterior | ❌ "largely prior-driven", prior 35 ± 15 |
| Nogueira et al. 2024, A&A 687, A301 | 48 ± 15 | orbital fit | ❌ prior was 47 ± 15 — posterior barely moved |
| Neuhäuser et al. 2011, MNRAS 416, 1430 | 20–50 | bolometric luminosity | ✅ (wide) |

**The attribution was wrong** — it is Lazzoni et al. **2020**, a different paper from the 2022
detectability paper the repo holds, and that 2020 paper is *"The search for disks or planetary
objects around directly imaged companions: a candidate around DH Tauri B"*, which is squarely
on this project's own topic and had gone unread.

**Only two determinations are independent**, and they disagree by a factor 1.6. The note now
quotes both, adopts 47 as the conservative choice, and states that the atmospheric mass would
*deepen* every limit by 27%. The qualitative exclusion survives the disagreement; the exact
numbers do not.

## 3. ⚠ The K magnitude was wrong by 1.6 mag — and this is not only about η Tel B

`PROPERTY-AUDIT.md` flagged **K = 13.2 (Lazzoni T1) vs SIMBAD H = 11.93** as CONFLICTING and
unresolved. Neuhäuser et al. 2011 resolves it, with measured photometry:

> J = 12.06 ± 0.19, H = 11.75 ± 0.10, **K_s = 11.6 ± 0.1**, L = 11.1 ± 0.2

SIMBAD's H agrees. **Lazzoni's Kp = 13.2 is wrong by 1.6 mag — a factor 4.4 in flux.**

The same source settles the parallax row: Chai quotes **Gaia EDR3 20.6028 ± 0.09 mas**,
matching SIMBAD exactly, so Lazzoni's 21.11 mas (47.4 pc) is wrong by 2.5% and the distance is
**48.5 pc**. And Chai's JWST astrometry, **ρ = 4199 ± 15 mas**, confirms the 4.21″ separation
to 0.3% — the one η Tel B number that was already right.

### The consequence for the contrast wall

M29 established that Lazzoni's companion-magnitude column "is apparent magnitude but not
uniformly reliable", on the evidence of one hit and one miss. The tally is now:

| system | Lazzoni Kp | primary source | error |
|---|---:|---|---:|
| YSES 1 b | 13.4 | Bohn+2020 | **0.14 mag** ✅ |
| η Tel B | 13.2 | Neuhäuser+2011 K_s = 11.6 | **1.6 mag** ❌ |
| β Pic b | 14.9 | Currie+2013 K_s = 12.47 | **2.4 mag** ❌ |

**Two of the three checked cases are wrong, by 1.6 and 2.4 mag.** That is a factor 4–9 in
contrast, from the column that supplies the *x*-axis of the contrast-wall analysis — and
`m29_wallpredict.py` reads that column for all **31** companions in its held-out test.

η Tel B's own contrast moves from 1888× to **~433×**, so S = contrast/θ² moves from 107 to
**~25**. Its classification does not change (both are far below the CLEAN threshold of 4327),
and **no verdict in the roster flips**. But the axis positions are unreliable at the
factor-of-4 level, comparable to the width of the transition interval the criterion is trying
to locate (4327–15202, a factor 3.5).

**This does not falsify S. It removes most of what remained of the case for testing it against
Lazzoni's table.** M29 already recorded S as "consistent with every outcome and not yet tested
by them"; the honest position now is that the table cannot test it either, because the input
column is unreliable at the scale of the effect. A real test needs primary-source photometry
per system. This is now item 0 on the wall note's pre-submission list, with the recommendation
that the note **stand on the resolution gate alone** — §1–§7 of it use measured separations
and measured PSFs, and are untouched by this.

## 4. The inclination was available and makes the result stronger

The note was drafted saying "the limit is on m sin i; the inclination is unknown." That was
wrong by omission. η Tel B's orbit about η Tel A is **near edge-on**:

- **i = 79 (+5/−6)°** — Chai et al. 2024, and stable at 79–80° across all five diagnostic
  fit configurations in their Table 3
- **i = 82 (+3/−4)°** — Nogueira et al. 2024, independently

A satellite formed in a circum-companion disc is expected to orbit near that plane. If it
does, sin i ≈ 0.98 and **the m sin i limits are true-mass limits to within 2%**. That is an
assumption rather than a measurement, and a strongly misaligned satellite escapes it — but it
is the same coplanarity expectation under which the CD-35 2722 B satellite is interpreted, and
stating it converts the note's result from a projected limit into a near-absolute one.

## 5. The "first RV" claim survives a search, with a caveat

Literature on η Tel B is photometric, spectroscopic (spectral typing; now an 11–21 μm MIRI
spectrum) and astrometric across a 25-year baseline. The radial velocities in the literature
are of η Tel **A**. No RV of the companion was found.

This is supporting evidence, not proof of absence. A targeted ADS query remains on the
pre-submission list, because a missed prior measurement is the one error in a note titled
"First…" that cannot be walked back gracefully.

## 6. The field is more active than the repo's reading list suggests

Searching for prior η Tel B velocities surfaced several 2024–2026 papers directly in this
project's competitive space, none of which appear anywhere in the repo:

| paper | why it matters |
|---|---|
| **Lazzoni et al. 2020**, A&A 641, A131 — disks/planetary objects around directly imaged companions, candidate around DH Tau B | the satellite-search precedent, and the source of η Tel B's adopted mass |
| **Nogueira et al. 2024**, A&A 687, A301 — η Tel B over two decades | the dedicated characterization paper for this note's target |
| **SaNDi-SHoP I**, arXiv:2603.24796 — satellites and discs around DI companions by star-hopping | a 2026 systematic survey of the same question |
| Astrometric limits on binary planets and exomoons around **β Pic b**, arXiv:2512.00160 | a competing constraint on a target this project has reduced |
| Direct-imaging constraints on exomoons around **ε Indi A b**, arXiv:2604.23448 | same class of limit |

Only Chai et al. 2024 was archived here (in this milestone). **Reading these is the
highest-value next literature task**, both for the paper's introduction and because two of
them place limits on objects in this project's own roster.

## 7. A process note: a milestone number was nearly overwritten

This work was first written to `M30-RESULTS.md` without checking whether that file existed. It
did — M30 is the archive-sweep reconciliation, committed the same day — and the write replaced
it. It was caught before commit only because `git status` reported the file as *modified*
rather than *added*, and it was restored from `HEAD` intact.

**The lesson, now LESSONS §5d:** milestone numbers are allocated in more than one thread, and
they are not sequential in time — M29 is still gaining sections while M30 and M31 are open.
Check `ls M*-RESULTS.md` and `git log --oneline -15` before claiming a number, and read
`git status` letters before committing: `M` on a file you believe you created is the signal
that something already lived there.

## 8. State of the note

Prepared, ~1,050 words, one table, within RNAAS limits. Four of the seven blockers listed in
the first draft are resolved. What remains is Matthew's: whether to publish it standalone at
all rather than folding it into the method paper, the author/affiliation/ORCID line, and an
AAS account. Two small tasks remain open — obtaining Lazzoni et al. 2020 directly rather than
through Chai's citation of it, and the targeted ADS check of §5.
