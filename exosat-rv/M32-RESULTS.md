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

## 6. ⚠ THE COMPETITIVE LANDSCAPE — the method is not ours, and one target is now taken

Checking whether a prior η Tel B RV existed turned into the most consequential hour of the
milestone. **Companion-side RV exosatellite searching is an established, actively published
technique**, and this repo's reading list had almost none of it.

| work | target | method | result |
|---|---|---|---|
| Vanderburg & Rodriguez 2021, ApJ 922, L2 | HR 8799 planets | companion RV | null |
| Ruffio et al. 2023, AJ 165, 113 | HR 7672 B | companion RV | null |
| Horstman et al. 2024 | GQ Lup B | companion RV | null |
| **Kenworthy et al. 2026, MNRAS** (arXiv:2606.04685) | **β Pic b** | **CRIRES+ companion RV** | **null, 160 m/s** |
| Hoy et al. 2026, Nature | CD-35 2722 B | CRIRES+ companion RV | **the detection** |
| Macias, Jenkins & Vanderburg 2026, AJ 171, 197 | β Pic b | GRAVITY+SPHERE astrometry | null |
| Kral et al. 2026 | HD 206893 B | VLTI/GRAVITY astrometry | tantalising signal |
| Lazzoni et al. 2026 (SaNDi-SHoP I) | 12 companions | SPHERE star-hopping imaging | 3 candidates |

**β Pic b is done.** Kenworthy et al. — Leiden, published MNRAS July 2026, accepted 29 May —
measured β Pic b's RV over Oct 2024–Mar 2025 at **160 m/s mean precision** and set limits of
80 M⊕ at P = 1 d and **1 M_Jup at P = 200 d**. Their data is the **0.2″ slit at K2166**, so
this project's H1567 HiRISE night is not theirs — but the target now has a published limit
from a dedicated campaign, and **a single 0.7-S/N-per-pixel fibre night cannot compete with
it.** M29/M32's β Pic b thread should be deprioritised accordingly; §7's negative result is
the right place to stop.

### What this does and does not do to the η Tel B note

**It does not preempt it.** No one has measured η Tel B. The note's claim is target-specific
and stands. On the numbers it is competitive: **1.11 M_Jup at P = 200 d from archival data at
127–130 m/s**, against Kenworthy's 1 M_Jup at the same period from a dedicated campaign at
160 m/s. Better precision, comparable depth, no telescope time.

**But the note's framing was wrong and has been fixed.** It read as though Hoy et al. were the
only prior work — which, against a published MNRAS paper doing the same thing four months ago,
is the kind of error a referee rejects on sight. The introduction now places η Tel B as an
addition to a named sample rather than a novel application, and notes that at ~47 M_Jup it
extends that sample into the brown-dwarf host regime alongside HR 7672 B.

### The genuinely good news: RV owns a region imaging cannot reach

For a 47 M_Jup host, **P = 20–300 d is 0.05–0.31 au**. The SPHERE star-hopping survey of
twelve directly imaged companions constrains satellites only **beyond ~1–5 au** — a factor
3–100 away, with no overlap. The reason is generic and is stated by the competing group
themselves: astrometric amplitude scales as the satellite's semi-major axis, RV amplitude as
a^(−1/2), so **imaging and astrometry own the wide orbits and RV owns the close ones**
(Macias et al. 2026). This is now in the note, and it is the strongest argument the project
has for why the RV route is worth pursuing at all.

Kenworthy et al. also motivate β Pic b by its near-edge-on orbit — **the same argument §4
independently derived for η Tel B**, which is reassuring rather than a problem.

### Papers now archived (`papers/text/`)

`kenworthy2026_bpb_exosatellites`, `sandishop2026_satellites`, `astrometric2025_bpb_exomoon`,
`epsindi2026_exomoon_limits`, `chai2024_etatel_jwst`. Still missing and worth having:
**Vanderburg & Rodriguez 2021** and **Lazzoni et al. 2020** (the latter is also η Tel B's mass
source, per §2).

## 7. The empirical-template route: tried, and vetoed by its own control

M29 §22 left the fibre pipeline blocked on one missing **input** — a template. The idea was to
skip the model atmosphere entirely: two directly imaged companions are already extracted here
at high S/N in the *same* H1567 setting, so **CD-35 2722 B (L0–1) and η Tel B (M7.5) can serve
as empirical templates**, carrying a real line list at the real instrument resolution with no
model systematics. `scripts/injection/m32_empirical_ccf.py`.

One prediction was fixed before running, and it is the one that matters. **β Pic A is A6V.**
In H band an A star has essentially no molecular structure, so correlating the *host* against
a cool-dwarf template must give nothing. If the host correlates, anything the target does is
instrumental, and the experiment is void.

**The control failed, at every masking level, with both templates.**

| telluric mask | kept | CD-35 template: control | η Tel template: control |
|---|---:|---:|---:|
| > 0.75 | 69% | 3.5σ at +23.7 km/s | 3.9σ at +51.7 km/s |
| > 0.90 | 54% | 4.4σ at +23.7 | 4.6σ at +53.7 |
| > 0.95 | 49% | 4.6σ at +24.7 | 4.8σ at +53.7 |
| > 0.98 | 46% | 4.7σ at +23.7 | 4.9σ at +53.7 |
| > 0.90, Brackett cut | 49% | **3.1σ** at +23.7 | **4.1σ** at +55.7 |
| > 0.98, Brackett cut | 42% | **3.4σ** at +24.7 | **4.4σ** at +53.7 |

**The pattern identifies what it is not.** Telluric correlation weakens as the mask tightens
and sits at 0 km/s in the observatory frame. This one **strengthens** as the mask tightens and
sits at a **stable, template-specific, non-zero velocity** — +23.7 and +53.7 km/s, unchanged
to ~1 km/s across every level. Masking the Brackett series removes roughly a quarter of it for
the L0–1 template and less for the M7.5, so **hydrogen contributes but does not explain it**,
and the peak does not move when hydrogen is removed.

**The likely dominant term is structural to the method.** The target is planet *divided by*
host, which imprints the host's own spectrum into it inverted. At ~0.7 S/N per pixel for the
planet, host structure dominates the ratio — so any template sharing structure with the host
correlates with target and control alike. **Removing the tellurics and correlating against a
stellar template are not independent operations**, and M29 §22's success at the first is what
creates the problem at the second.

**No β Pic b velocity is claimed.** The target column ran 1.8–3.2σ with peaks wandering from
−182 to +92 km/s and no stability across mask levels or templates — noise, and it would have
been noise whatever the control did.

### What this is worth

It is a genuine negative methodological result, and the control is the whole of it. **An
empirical companion template is not a drop-in replacement for a model atmosphere**, because an
A-star host and a cool-dwarf template share enough structure — hydrogen plus whatever survives
the ratio — to manufacture a 3–5σ correlation out of nothing. A cross-correlation analysis
without a host control would have reported the 3.2σ η Tel peak as marginal evidence.

Two routes remain open and neither is blocked by this: a **model atmosphere** template, which
is what §22 said was needed and still is; and **more nights**, since the whole problem is that
the planet is 0.7 S/N per pixel against a host that dominates the ratio. Seven more public
β Pic HiRISE nights exist.

## 8. The three follow-ups, executed

**(a) The magnitude propagation — and one claim inverts.** K = 13.2 was still live in
`survey.py`, `data/m7-survey.json`, `docs/target-queue.md` and M15. It is not cosmetic: the
survey's detection threshold is *computed* from the magnitude via
`3 x 31.44 x 10^(0.2(K-12.01))`. At 13.2 that forecasts **163 m/s**; at the measured
K_s = 11.6 it forecasts **78 m/s**.

**M15's claim that the achieved 127-129 m/s "beat the 163 m/s forecast" therefore inverts —
it is 1.6x WORSE than a correct forecast.** Withdrawn and annotated in place in M15 rather
than deleted. Nothing else moves: the null, the injection gates and the published limit never
used the magnitude, and **no verdict in the 38-target survey changes class** (pass/marginal/
fail stays 0/3/35). beta Pic b's 14.9 was corrected to 12.47 in the same pass. The remaining
magnitudes are left alone — guessing at unsourced values is what caused this.

**(b) The two missing references, both archived.** Vanderburg & Rodriguez 2021 (ApJL 922, L2,
*"First Doppler Limits on Binary Planets and Exomoons in the HR 8799 System"*) — the first work
of this kind, and its limits (2 M_Jup at P < 5 d) are much shallower than this project's, which
is useful context. And **Lazzoni et al. 2020**, which closes the last open blocker: it states
eta Tel B's mass as **47 (+5/-6) M_Jup** first-hand, confirming §2's second-hand attribution.

**(c) The wall note — the fix beat the recommendation.** §3 recommended the note stand on the
resolution gate alone. Two things changed that.

First, applying the eta Tel B correction *did not break §8*: S moves 107 -> 24 and the class
separation for n = 1.5-4.0 is unchanged, because the correction only pushes a clean case
further from the boundary. A robustness check that passed.

Second — the find — **Lazzoni et al. 2020 Table 2 carries contrasts measured directly from
SPHERE observations** for 27 companions, one instrument, one band, one paper. That is exactly
the primary-source photometry item 0 demanded, sitting inside a reference the repo already
depended on. Re-running the class test on that column alone (`scripts/m32_wall_measured.py`),
with no band mixing:

| system | sep | measured contrast | S | verdict |
|---|---:|---:|---:|---|
| eta Tel B | 4.21" | 667x | **38** | clean |
| PDS 70 b | 0.19" | 1818x | **50 365** | fails |
| beta Pic b | 0.33" | 10 000x | **91 827** | fails |

**The ordering survives and the margin widens from a factor 3.5 to a factor 1339.** The
decisive detail is *which* point moved: PDS 70 b previously defined the failure boundary at
S = 15 917 on an unverified magnitude, and measured it sits far deeper into the failing
regime — **the boundary was drawn too tight, not too loose.**

Three points separate by chance easily and no threshold should be read off them; it also
cannot replace the six-system test, since CD-35 2722 B, HIP 81208 B and YSES 1 b are absent
from that table. It is a check on an independent, better-sourced measurement of the same
quantity, and it passed. Item 0 is marked resolved. **The resolution gate remains the note's
result; the contrast gate has moved from an unsupported open question to a supported one.**

## 9. A process note: a milestone number was nearly overwritten

This work was first written to `M30-RESULTS.md` without checking whether that file existed. It
did — M30 is the archive-sweep reconciliation, committed the same day — and the write replaced
it. It was caught before commit only because `git status` reported the file as *modified*
rather than *added*, and it was restored from `HEAD` intact.

**The lesson, now LESSONS §5d:** milestone numbers are allocated in more than one thread, and
they are not sequential in time — M29 is still gaining sections while M30 and M31 are open.
Check `ls M*-RESULTS.md` and `git log --oneline -15` before claiming a number, and read
`git status` letters before committing: `M` on a file you believe you created is the signal
that something already lived there.

## 10. State of the note

Prepared, ~1,050 words, one table, within RNAAS limits. Four of the seven blockers listed in
the first draft are resolved. What remains is Matthew's: whether to publish it standalone at
all rather than folding it into the method paper, the author/affiliation/ORCID line, and an
AAS account. Two small tasks remain open — obtaining Lazzoni et al. 2020 directly rather than
through Chai's citation of it, and the targeted ADS check of §5.
