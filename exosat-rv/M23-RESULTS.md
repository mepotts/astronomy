# M23–M24 — The roster closes: HD 1160 B's first series, the crumbs land on the far side of the wall, and a gate catches a fake-quiet series

**Question:** the last targets with public data — HD 1160 B (nine deep staring
nights), AF Lep b and 51 Eri b (staring crumbs), the CT Cha B order screen, and the
PDS 70 nine-night upgrade. What do they yield?

**Answers:**

1. **HD 1160 B (M23): a first multi-epoch series, quality-limited.** Nine nights
   reduced through the new staring branch; 725 m/s night-to-night scatter over 41 d
   with per-night errors spanning ±37 to ±2600 m/s. Combined injection ~94–95%, but
   per-order recovery is chaotic on the iteration-0 template. No defensible limit;
   the one ±37 m/s night proves the target's ceiling under good conditions (§1).
2. **AF Lep b and 51 Eri b (M24): beyond slit reach, as the wall predicted.**
   AF Lep b transmits only 68% ± 4% of an injected signal (dilution at ~30,000×
   contrast); 51 Eri b returns usable content in 3 of 11 orders. Both are recorded
   as harsh-end data points of the M20 §6 contrast wall, not as measurements (§2).
3. **CT Cha B screen: a variability candidate, undecidable at n = 3.** Seven orders
   survive both injection arms; on them, the 2025-05-02 epoch still sits 3.3σ low
   (−1.5 km/s). An accreting M8 plausibly does that; so does a bad night (§3).
4. **PDS 70 addendum: the gate caught a fake-quiet series.** The nine-night rebuild
   looked better than the validated six-night result and failed its injection gate
   at −62% ± 197% — the enlarged template lost its stellar lever. Rejected; the
   six-night state restored and reproduced exactly (χ² 3.5/5, 130 m/s, 99% gates).
   The M9 lesson, enforced by machinery (§4).

## 1. HD 1160 B: the staring route works; this dataset limits itself

The engineering deliverables held: classify.py routes staring-mode science to
`cr2res_obs_staring`, reduce_one.sh collapses each night to one deep spectrum, and
the calSelector-empty trap (associations missing for 1200 s darks) is bypassed by a
direct per-night CALIB query ([`m19_urls_from_raw.py`](scripts/cr2res/m19_urls_from_raw.py)
fallback). Two data quirks documented: staring extractions carry a phantom empty
order 01 on detector 1 (stripped at staging), and template iteration 1 crashes on a
degenerate chunk (run on tpl0; gates decide sufficiency).

The series itself: χ² = 36.2/8 against constant — excess scatter, but the night
quality varies by a factor of 70 (AO conditions at 0.78″ from an A0 star), and the
per-order injection table is unstable (o10 clean at 102±4/118±39; most others not).
Verdict: **first multi-epoch RV series of HD 1160 B** (hedged as always),
method-demonstration grade; a defensible limit needs either per-iteration template
gating or better-conditioned epochs.

## 2. The crumbs, and the wall's harsh end

| target | epochs | injection verdict | entry in the wall table |
|---|---|---|---|
| AF Lep b (0.32″, ~30,000×) | 2, 3 d apart | **68% ± 4%** — one third of any signal eaten | dilution-limited: no measurement possible |
| 51 Eri b (0.45″, ~30,000×) | 1 | 3 of 11 orders respond at all | beyond slit reach |

The M20 §6 wall now has both ends measured: clean at 0.8″/2000× (HIP 65426 b,
131 m/s), flooded at 0.55″/5000× (beta Pic b), gone at ≤0.45″/30,000× (these two)
and at 0.17″ (PDS 70). One more trap for the ledger: some staring products ship with
stripped headers (missing UTC/LST) that crash viper's template creation — patched at
staging with placeholder keywords (neither feeds the physics; BERV runs off MJD and
coordinates).

## 3. CT Cha B, screened

The injection-based order screen ([`ctcha_screen.py`](scripts/injection/ctcha_screen.py),
the sanctioned M13 drop rule: survive BOTH arms within 15 points of unity at ≤25
scatter) keeps orders 3,4,5,8,11,12,13. On the screened set: +46 ± 84, −1511 ± 463,
+159 ± 213 m/s — the middle epoch is 3.3σ deviant *after* screening. Recorded as a
**variability candidate on an accreting companion** (veiling/accretion RV shifts of
this size are plausible at ~2 Myr), explicitly undecidable against a bad night at
three epochs. A cheap future test: any two additional epochs.

## 4. The PDS 70 upgrade that failed its own gate

Retrieving the six straggler products (direct dataportal URLs beat the flaky
datalink host) grew PDS 70 to 9 nights / 483 d. The rebuilt series looked excellent
— 150 m/s, tighter K₉₀ — and the K=1530 arm returned **−62% ± 197%** with
systematically negative per-order recoveries: the 14-file template converged to a
solution with no stellar lever, and a series that measures nothing is always quiet.
**Rejected on the gate; the validated six-night state re-staged and reproduced
bit-for-bit** ([`m21_restore.sh`](scripts/injection/m21_restore.sh)). Two lessons
banked: the injection gate is the only thing standing between this pipeline and
publishing flat noise as a limit — it caught exactly that, twice in one project —
and the generic runner should gate **every** template iteration, not just the last
(logged as the m2x improvement).

## 5. The plan, walked end to end — final roster

| target | data used | verdict |
|---|---|---|
| CD-35 2722 B | 18 nights / 466 d (H1567) | **CONFIRMED** (satellite 1, blind, BERV-robust) / **CONTRADICTED** (satellite 2, on their own table) |
| eta Tel B | 18 nights / 815 d (H1567) | **NULL** — msini ≳ 0.5–1.2 M_Jup excluded, P = 20–300 d |
| HIP 65426 b | 5 nights / 422 d (K2192) | **NULL** — ≳0.4 M_Jup excluded at P ≤ 100 d (priority caveat, M20 §5) |
| PDS 70 (star) | 6 nights / 426 d (K2166) | **NULL** — flat at 130 m/s; ~3 M_Jup stellar-companion limit |
| beta Pic b | 13 nights / 813 d (K2166) | **CONTAMINATION-LIMITED** — the measured case for fiber-fed suppression |
| HD 1160 B | 9 nights / 41 d (H1567 staring) | first series; quality-limited, no claim |
| CT Cha B | 3 epochs / 70 d (K2166) | variability candidate, undecidable at n=3 |
| AB Pic b | 2 epochs / 3 d (K2166) | clean repeatability datum; archive exhausted |
| AF Lep b | 2 epochs / 3 d (H1567 staring) | dilution-limited (68% transmission) |
| 51 Eri b | 1 epoch (H1567 staring) | beyond slit reach |
| GSC 08047-00232 B | — | embargoed; 2 raw K nights bankable later |

Eleven systems: one confirmation, one contradiction, four nulls with limits, one
contamination case, and four honestly-classified data-limited entries. Every claim
injection-gated; every "first" hedged to a literature search; the contrast wall
measured at four points.

## 6. For the next agent

1. m2x runner: gate every template iteration (would have caught the PDS 70 collapse
   at build time and possibly rescued HD 1160's ladder).
2. Embargo calendar: GSC product; PDS 70's 2025 K nights; eta Tel's K epochs;
   beta Pic b's late-2025 K2166 nights; **CD-35's decisive epochs Dec 2026 – May
   2027** (the amplitude question and satellite 2, finally).
3. Paper: fold M20–M24 + the wall into docs/paper/ — gated on Matthew's HIP 65426 b
   priority decision (M20 §5) and worth doing with the M18 figure-appendix pattern.
4. CT Cha B: two more epochs decide the variability candidate.
5. The proposal case is complete: AB Pic b campaign (better host than CD-35),
   beta Pic b / PDS 70 b via HiRISE-class fibers, with every sensitivity number
   measured rather than forecast.
