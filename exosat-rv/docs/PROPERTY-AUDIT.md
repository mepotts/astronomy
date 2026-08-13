# Object-property audit — the externally-sourced astrophysical numbers, checked against their sources

**Date:** 2026-08-13 · **Scope:** `exosat-rv/` only · **Nothing in this file has been applied.**
It is a list of findings for review.

**Why this exists.** Today's reference audit found 14 wrong citations, all produced by the same
mechanism: when a fact was not in front of the writer, a plausible one was generated instead of
the source being opened. That mechanism has already cost this project one measurement — the M28
slit-contamination scan was computed at a **3.17″** separation recalled from memory when the
project's own M0-RESULTS documents **2.8″**, so it sampled the wrong place and was withdrawn
(M28 §5, M29). This audit asks the same question of every *object property*: the externally
sourced astrophysical numbers that are **not** this project's own measurements.

**Sources of truth, in priority order:**

1. **Papers in `papers/text/`** — read directly. The decisive find is that
   **Lazzoni et al. 2022 Table 1 (`lazzoni2022_detectability.txt`, line 849) is already in this
   repository and carries four columns the project never ingested**: `Parallax` (mas),
   `K` (**host** apparent K), `Sep` (**projected separation, in mas**) and a per-row reference.
   `src/exosat_rv/analysis/survey.py` transcribed only Age, Kp, a, M*, Mp. Every separation in
   arcsec used anywhere in this project could have been read out of a file already on disk.
2. **SIMBAD**, TAP `sync` endpoint, ADQL, `basic` + `allfluxes` + `ident`. Queried live for this
   audit (2026-08-13): `sp_type`, `plx_value`, `K`, `H`, `J`, `V`, and RA/Dec for pair separations.
3. Where neither has it: **UNSOURCED**. No value in this file was supplied from recall.

**Two mechanical checks run first, both clean:**

- `data/m7-survey.json` **regenerates byte-identically** from `survey.py` — it has not been
  hand-edited.
- `survey.py`'s `LAZZONI_TABLE1` is a **faithful transcription of Lazzoni Table 1: 0 mismatches
  in 37 rows × 5 fields**. Where an m7 value disagrees with SIMBAD below, the disagreement is
  between *Lazzoni and SIMBAD*, not a transcription slip. (Note: Lazzoni Table 1 has **37** rows,
  not 38. M7-RESULTS §3 and `survey.py`'s docstring both say "38 companions"; the 38 in
  `m7-survey.json` is 37 + CD-35 2722 B.)

**Counts.** 268 property instances checked across 21 systems and 30 files.
**VERIFIED 171 · CONFLICTING 34 · UNSOURCED 63.**

---

## 0. The headline

**`scripts/m29_contrast.py`'s derived contrast table — the second axis of the contrast wall, and
the number now printed in `docs/paper/draft.template.html` §9 and throughout
`docs/paper/contrast-wall-note.md` — rests on companion K magnitudes that SIMBAD contradicts by
1.0–4.9 mag on every row where SIMBAD has an independent measurement.**

The wall's stated ceiling, *"clean is measured up to ~1900×"*, has exactly two supporting rows,
and **both fail**:

| row | quoted | why it fails | value from the checkable source |
|---|---:|---|---:|
| η Tel B | **1888×** | m7's `k_mag = 13.2` (Lazzoni) has no SIMBAD counterpart, and SIMBAD's measured **H = 11.93** for η Tel B would require *H − K = −1.27* — no late-M/L dwarf has negative H−K. Separately, **the η Tel campaign is H1567, not K**. | **515×** (H-band, band-matched: 11.93 − 5.150) |
| AB Pic b | **1768×** | m7's `k_mag = 15.1` (Lazzoni) vs **SIMBAD K = 14.09** for `HD 44627B` (L1, `BD*`) — 1.01 mag brighter | **698×** (K-band, band-matched) |

With those two corrected, the highest cleanly-measured contrast in the nodding roster falls from
~1900× to **~700×**, while the flooded point (β Pic b, 36 983×, K-band, K2166 campaign — the one
row that *is* band-matched and rests on two 2MASS magnitudes) is unchanged. **The unsampled gap
therefore widens from a factor of ~20 to a factor of ~53.** The note's negative result gets
stronger; its headline number is wrong.

---

## 1. Separations in arcsec — the wall's other axis

Primary literature source available in-repo: **Lazzoni Table 1, `Sep` column, in mas.**
CD-35 2722 B is not in that table; its source is Hoy et al. directly.

| system | value(s) in repo | files carrying it | in-repo source | status |
|---|---:|---|---|---|
| **CD-35 2722 B** | **2.8″** | `config.py:bd_projected_sep_arcsec`, `scripts/injection/m28_contam.py:SEP_DOC`, `scripts/m29_contrast.py:51`, `M0:86`, `M1:30`, `HANDOFF:278`, `M28:134`, `draft.template.html:712,716,722`, `cd35-etatel-draft.html:712,716,722`, `contrast-wall-note:108,121,460` | `hoy2026_nature_published.txt:50` "At a projected separation of ∼2.8”"; identically `hoy2026_v1.txt:64` | ✅ **VERIFIED** |
| **CD-35 2722 B (alt)** | **3.17″** | `m28_contam.py:SEP_ALT`, `contrast-wall-note:109,158,384,460`, `draft.template.html:712,722`, `cd35-etatel-draft.html:712,722`, `M28:134,151` | **none — `3.17` occurs in no archived paper** (grep of all of `papers/text/`) | ⛔ **UNSOURCED + CONFLICTING** |
| β Pic b | 0.55″ | `m29_contrast.py:52`, `queue:46,54`, `contrast-wall-note:127,139,152,206`, `M20:113`, `HANDOFF:29,30` | Lazzoni 510.8 mas = **0.511″** | ⚠️ **CONFLICTING** (+7.6%) |
| PDS 70 b | 0.17″ | `m29:52`, `contrast-wall-note:128,144,381`, `M20:61,114`, `queue:55` | Lazzoni 173.5 mas = **0.174″** | ✅ VERIFIED |
| PDS 70 c | 0.24″ | `m29:52` | Lazzoni 213.2 mas = **0.213″** | ⚠️ **CONFLICTING** (+12.6%) |
| HIP 65426 b | 0.8″ | `m29:52`, `contrast-wall-note:125,314,438`, `M20:67,112`, `queue:54` | Lazzoni 824.0 mas = **0.824″** | ✅ VERIFIED |
| η Tel B | 4.2″ | `m29:52`, `contrast-wall-note:120,138,144`, `queue:122`, `M5:81`, `BUILD-PLAN:121`, `README:195`, `M29:127` | Lazzoni 4210 mas = **4.210″** | ✅ VERIFIED |
| **AF Lep b** | **0.45″** | `m29_contrast.py:52` | none | ⛔ **UNSOURCED + CONFLICTING** (see next row; note `m29` gives AF Lep b and 51 Eri b the *same* 0.45 — the signature of a copied cell) |
| **AF Lep b** | **0.32″** | `contrast-wall-note:188`, `M23:48` | none | ⛔ **UNSOURCED** |
| 51 Eri b | 0.45″ | `m29:52`, `contrast-wall-note:189`, `M23:49`, `M20:126`, `queue:55` | Lazzoni 434.0 mas = **0.434″** | ✅ VERIFIED (within 4%) |
| **HIP 81208 B** | **0.3″** | `m29:53`, `contrast-wall-note:126,146,204,454`, `queue:69`, `M29:146` | none — not in Lazzoni; SIMBAD's B-component position is not independently resolved (pair separation computes to 0.027″, i.e. unusable) | ⛔ **UNSOURCED** |
| YSES 1 b | 1.7″ | `m29:53`, `contrast-wall-note:124`, `queue:68` | Lazzoni (`TYC 8998-760-1 b`) 1712.5 mas = **1.713″**; SIMBAD coord pair 1.629″ | ✅ VERIFIED |
| AB Pic b | "≥ 2.7″" | `contrast-wall-note:122,152` | Lazzoni 5400 mas = **5.400″** | ⚠️ true as a bound but **understated by 2×**; the value is available |
| CT Cha B | "≥ 2.7″" | `contrast-wall-note:123,152` | Lazzoni 2680 mas = **2.680″**; SIMBAD coord pair **2.670″** | ⚠️ the bound "≥ 2.7″" is **marginally false** (2.68 < 2.7); value available |
| HD 1160 B | 0.78″ | `contrast-wall-note:190`, `M23:38` | Lazzoni (listed as "HD1160 c") 773 mas = **0.773″**; SIMBAD coord pair 0.700″ | ✅ VERIFIED |
| HD 19467 B | not quoted | — | Lazzoni 1631 mas = 1.631″; SIMBAD coord pair 1.642″ | (available, unused) |
| HD 206893 B, 2M0103AB b | not quoted | — | none | — |

**Also available and unused** (Lazzoni `Sep`, mas → ″, for every remaining m7 row):
1RXS J1609 b 2.215 · 2M1207 b 0.878 · CT Cha b 2.680 · DH Tau B 2.350 · GJ 504 b 2.490 ·
GQ Lup b 0.712 · HD 4747 B 0.590 · HD 72946 B 0.235 · HD 95086 b 0.630 · HR 2562 B 0.640 ·
HR 3549 B 0.850 · HR 8799 b/c/d/e 1.721/0.955/0.690/0.397 · HIP 64892 B 1.270 · HIP 74865 B 0.201 ·
HIP 78530 B 4.180 · HIP 79098 B 2.359 · HIP 107412 B 0.252 · κ And b 0.876 · PZ Tel B 0.558 ·
TYC 7084-794-1 B 2.990 · TYC 8047-232-1 B 3.210 · TYC 8998-760-1 c 3.373 · TYC 8984-2245-1 b 1.050 ·
GSC 6214-210 B 2.205.

### `separation_au` in `data/m7-survey.json` is not one quantity

All 38 values transcribe faithfully, but the **field name is a trap**. For CD-35 2722 B,
`separation_au = 222.0` is the *semi-major axis* implied by P ≈ 5000 yr — `survey.py`'s docstring
says so explicitly, and the projected separation is 62.6 au (2.8″ × 22.36 pc). For most Lazzoni
rows the column equals `Sep/parallax`, i.e. a converted *projected* separation. For β Pic b it is
neither: Lazzoni's `a = 8.9` au against `Sep/plx = 9.93` au. A field called `separation_au` that
silently holds three different quantities is the shape of defect that produced M0's retracted
Hill-radius disproof. **Flagged, not corrected.**

---

## 2. Companion K magnitudes — every `k_mag` in `data/m7-survey.json`

All are Lazzoni Table 1 `Kp`. SIMBAD has an independent K for eight of them. **It disagrees with
six**, three of them by more than 3 mag.

| companion | m7 `k_mag` | SIMBAD K (main_id) | Δ | status | consequence |
|---|---:|---:|---:|---|---|
| **HIP78530 B** | 18.40 | **13.491** (`HD 143567B`, M8) | **−4.91** | ⛔ CONFLICTING | `threshold_ms` 1789 → 187 m/s (**9.6×**); verdict would move off "nothing physical reachable" |
| **HD19467 B** | 14.20 | **17.970** (`HD 19467B`, T5.5+1) | **+3.77** | ⛔ CONFLICTING | `threshold_ms` 259 → 1468 m/s (**5.7×**); T5.5 dwarfs are faint in K, so SIMBAD is the physically coherent one |
| **TYC 8998-760-1 b** (YSES 1 b) | 18.20 | **14.700** (`NAME TYC 8998-760-1B`) | **−3.50** | ⛔ CONFLICTING | `threshold_ms` 1632 → 326 m/s (**5.0×**); derived contrast 8379× → **334×** |
| **AB Pic b** | 15.10 | **14.090** (`HD 44627B`, L1, `BD*`) | **−1.01** | ⛔ CONFLICTING | derived contrast **1768× → 698×** — one of the two pillars of "clean up to ~1900×" |
| DH Tau B | 14.70 | 14.190 (`V* DH Tau B`, M9.25) | −0.51 | ⚠️ CONFLICTING | `threshold_ms` 326 → 257 m/s |
| k And b | 13.90 | 14.370 (`* kap And B`, L1) | +0.47 | ⚠️ CONFLICTING | `threshold_ms` 225 → 280 m/s |
| **51 Eri b** | 21.00, flagged *"no measured K — upper limit only"* | **18.670** (`* 51 Eri b`; H 18.99, J 19.04) | −2.33 | ⛔ **the flag is now false** | a measured K exists. The wall note's *"3.8-million-× point"* argument (§2, §3.4, verify-item 3) is computed from the bogus 21.0; the real K-band figure is **450 000×** |
| HD1160 c | 14.20 | 14.120 (`HD 1160B`) | −0.08 | ✅ VERIFIED | but see naming defect below |
| η Tel B | 13.20 | *no K in SIMBAD*; **H = 11.93** | — | ⛔ CONFLICTING | K = 13.2 with H = 11.93 requires H−K = −1.27, unphysical for M7.5V. Pillar 2 of "clean up to ~1900×" |
| β Pic b | 14.90 | none | — | ⚠️ UNSOURCED beyond Lazzoni | sole input to the 36 983× flooded anchor |
| PDS 70 b / c | 15.20 | none | — | ⚠️ UNSOURCED beyond Lazzoni | sole input to 460× |
| CT Cha b | 14.80 | none | — | ⚠️ UNSOURCED beyond Lazzoni | |
| HIP65426 b, HD95086 b, GJ504 b, TYC 8998-760-1 c, TYC 8984-2245-1 b | 21.00 (all limits, `¡ 21` in Lazzoni) | none | — | ✅ correctly flagged as limits | |
| remaining 20 m7 rows | as transcribed | none in SIMBAD | — | ⚠️ **single-source (Lazzoni only)** | |

**Component-naming defect.** `m7-survey.json` calls the object **`HD1160 c`** (Lazzoni's own
label). SIMBAD resolves `HD 1160B` → K 14.12 at a pair separation of 0.700″, and `HD 1160C` → K
12.18 at 5.157″. The 0.773″/K 14.2 row is therefore **HD 1160 B**, which is what the queue and
`contrast-wall-note` call it. `m7-survey.json` and `M7-RESULTS:107` carry the wrong component
letter for an object the roster discusses under the right one.

**Provenance ceiling.** Lazzoni's Table 1 cites Langlois et al. 2021b, Bohn et al. 2020, Maire
et al. 2020b, De Rosa et al. 2020b, etc. **None of those papers is in `papers/`.** So where
SIMBAD is silent, the Lazzoni value cannot be adjudicated inside this repository at all — it is
corroborated-secondary at best. M7-RESULTS §7 caveats "some have moved"; the six SIMBAD
disagreements above show that is an understatement for at least three rows.

---

## 3. Host magnitudes — the one part of the contrast derivation that holds up

Lazzoni's `K` column is the **host** apparent K, and **SIMBAD reproduces it to ≤0.03 mag on 15
of 16 hosts checked** (CD-35 2722 7.046 · β Pic 3.480 · PDS 70 8.542 · HIP 65426 6.771 ·
η Tel 5.010 · HD 1160 7.040 · 51 Eri 4.537 · TYC 8998-760-1 8.392 · HD 19467 5.401 · AB Pic 6.981 ·
CT Cha 8.661 · HD 95086 6.789 · HR 8799 5.240 · GQ Lup 7.096 · GSC 6214-210 9.152 · HD 4747 5.305).
Two exceptions: **HD 72946** SIMBAD 5.497 vs Lazzoni 5.467; **DH Tau** SIMBAD 8.178 vs Lazzoni
8.824 (0.65 mag). ✅ **VERIFIED** — `contrast-wall-note` verify-item 2(a) can be closed.

`draft.template.html:537` — *"Its host is an M1 V star at K = 7.05"* — ✅ VERIFIED
(SIMBAD `CD-35 2722`, M1Ve, K = 7.046).

---

## 4. Five of the nine "unresolved" contrast rows are a key-naming bug, not missing data

`contrast-wall-note` §2 and M29 §6 state that only six systems resolve, and list nine as *"absent
from M7's table or unresolved at SIMBAD"*. That diagnosis is wrong for five of them:
`scripts/m29_contrast.py`'s `HOSTS` dict is keyed with names that **do not match
`m7-survey.json`'s**, so `comp.get(c)` returns `None` and the row is dropped silently before
SIMBAD is ever consulted.

| `HOSTS` key (m29) | actual `m7-survey.json` name | why it drops |
|---|---|---|
| `HIP 65426 b` | `HIP65426 b` | space (would be excluded anyway — K is a limit) |
| `HD 1160 B` | `HD1160 c` | space **and** component letter |
| `HD 19467 B` | `HD19467 B` | space |
| `YSES 1 b` | `TYC 8998-760-1 b` | different catalogue name entirely |
| `CT Cha B` | `CT Cha b` | case |

Four of those five have **both magnitudes already in the repo or in SIMBAD**, so the derivation
that "does not resolve" in fact yields:

| system | K_comp source | host K | derived K-band contrast |
|---|---|---:|---:|
| CT Cha B | m7 14.80 | 8.661 | **285×** |
| YSES 1 b | **SIMBAD 14.70** (m7's 18.20 → 8379×) | 8.392 | **334×** |
| HD 1160 B | m7 14.20 / SIMBAD 14.12 | 7.040 | **731× / 679×** |
| HD 19467 B | **SIMBAD 17.97** (m7's 14.20 → 3308×) | 5.401 | **106 561×** |

And two of the four genuinely-absent systems resolve from SIMBAD alone:

| system | SIMBAD K / H | host K / H | K-band | H-band |
|---|---:|---:|---:|---:|
| **HIP 81208 B** | 13.410 / 13.960 | 6.768 / 6.773 | **454×** | **750×** |
| **HD 206893 B** | — / 16.790 | 5.593 / 5.687 | — | **27 618×** |

**This settles `contrast-wall-note` §3.5 / verify-item 4.** The note lists three open readings for
why HIP 81208 B is clean at 0.3″ and says *"two magnitudes and an archive query would do more for
the location of this wall than another season of spectroscopy."* Reading (i) is the right one:
HIP 81208 B sits at **454×**, i.e. **81× easier in contrast than β Pic b's 36 983×**. It is not
an anomaly; it is a low-contrast target at small separation, and it is the cleanest evidence in
the roster that the two axes are genuinely independent.

### Band-matched contrasts (verify-item 2(b), now computable)

Two campaigns are H1567, so their K-band ratios are the wrong quantity:

| system | setting | quoted (K) | **band-matched** | inputs |
|---|---|---:|---:|---|
| CD-35 2722 B | H1567 | 97× | **158×** | comp H 12.78 (`config.py`, Wahhaj 2011) − host H 7.280 (SIMBAD) |
| η Tel B | H1567 | 1888× | **515×** | comp H 11.93 (SIMBAD) − host H 5.150 (SIMBAD) |

Both stay comfortably "clean". The CD-35 correction is harmless; the η Tel one removes the wall's
ceiling.

---

## 5. CD-35 2722 B and η Tel B — the two systems that carry results

### CD-35 2722 B

| property | value | file(s) | source | status |
|---|---|---|---|---|
| companion mass | **37 M_Jup** | `config.py:bd_mass_mjup`, `m7-survey.json`, `M7:133`, `DATA-SOURCES:70`, `README:189` | `hoy2026_nature_published.txt:54` "a 37 M_Jup companion to a 0.4 M⊙ M-type star" | ✅ **VERIFIED** |
| companion mass (range) | **31–37 M_Jup** | `draft.template.html:198`, `cd35-etatel-draft.html:198` | 37 verified as above; **31 ± 8 from Wahhaj et al. 2011, which is *not* in `papers/`** | ⚠️ half-verified; lower end unarchived |
| host mass | **0.4 M_⊙** | `config.py:star_mass_msun`, `m7-survey.json`, `M1` | `hoy2026_nature_published.txt:54` | ✅ **VERIFIED** (M1 already caught an earlier 0.5) |
| host spectral type | M-type / **M1 V** | Hoy; `draft:537` | Hoy line 54; SIMBAD **M1Ve** | ✅ VERIFIED |
| companion spectral type | **L0-1** / "L0-type" | `m5-targets.json:174`, `draft:198` | SIMBAD `CD-35 2722B` **L0-1**, otype `BD*` | ✅ VERIFIED |
| parallax / distance | **44.7203 mas / 22.36 pc** | `config.py:parallax_mas`, `M0:86` | SIMBAD 44.720 mas | ✅ VERIFIED |
| companion K / H / J | **12.01 / 12.78 / 13.63** MKO | `config.py:bd_h_mag` docstring, `m7-survey.json:k_mag`, `satellites.py:107`, `tests/test_satellites.py:78`, `draft:538` | Wahhaj et al. 2011 (arXiv:1101.2893) — **cited everywhere, archived nowhere** | ⚠️ **UNVERIFIABLE IN-REPO** |
| age | **100 Myr** ("AB Dor moving group") | `m7-survey.json:age_myr`, `draft:198` | none archived | ⛔ **UNSOURCED** |
| projected separation | 2.8″ / 62.6 au | see §1 | Hoy | ✅ VERIFIED |
| semi-major axis / ecc / period | 222 au / >0.9 / ~5000 yr | `survey.py:CD35`, `config.py` | `hoy2026_nature_published.txt:52-53` | ✅ VERIFIED |

### η Tel B

| property | value | file(s) | source | status |
|---|---|---|---|---|
| companion mass | **47 M_Jup** | `m7-survey.json`, `M7:133`, `M15:10`, `queue:122` | Lazzoni T1 (→ Langlois et al. 2021b, **not archived**) | ⚠️ **single-source**; M15's headline msini limit scales as M_host^(2/3) |
| host mass | **2.18 M_⊙** | `m7-survey.json` | Lazzoni T1 | ⚠️ single-source |
| host spectral type | **A0V** | `M5:81`, `contrast-wall-note` | SIMBAD `* eta Tel` **A0V** | ✅ VERIFIED |
| companion spectral type | **M7.5V** | `M5:81`, `m5-targets.json` | SIMBAD `* eta Tel B` **M7.5V** | ✅ VERIFIED |
| companion K | **13.2** | `m7-survey.json`, `M7:133`, `queue:122`, `M15:10,70`, `M29:127`, `contrast-wall-note:120` | Lazzoni T1 only; **SIMBAD H = 11.93 contradicts it** | ⛔ **CONFLICTING** |
| age | **24 Myr** (β Pic group) | `m7-survey.json`, `queue:122`, `M15` | Lazzoni T1 age column | ⚠️ single-source |
| parallax | 21.11 mas (47.4 pc) | Lazzoni T1 (not stored in repo) | SIMBAD **20.603 mas (48.5 pc)** | ⚠️ CONFLICTING (2.4%) |
| separation | 4.2″ | see §1 | Lazzoni 4.210″ | ✅ VERIFIED |

---

## 6. (b) Every value that appears with two different numbers

| quantity | value A (files) | value B (files) | adjudication |
|---|---|---|---|
| **CD-35 2722 B separation** | **2.8″** — `config.py`, `m28_contam.py:SEP_DOC`, `m29_contrast.py`, `M0`, `M1`, `M28`, `HANDOFF`, both HTML drafts, `contrast-wall-note` | **3.17″** — `m28_contam.py:SEP_ALT`, `contrast-wall-note:109,158,384,460`, both HTML drafts (712, 722), `M28:134,151` | **2.8″ wins.** Hoy (both versions) says ~2.8″; **3.17 appears in no archived paper.** The drafts describe 3.17″ as *"the 3.17″ value quoted in the literature"* — that attribution is unsupported. |
| **AF Lep b separation** | **0.45″** — `m29_contrast.py:52` | **0.32″** — `contrast-wall-note:188`, `M23:48` | **Neither is sourced.** 0.45 duplicates the 51 Eri b cell in the same dict. |
| **η Tel B contrast** | **1888×** — `M29:127`, `contrast-wall-note:120,138`, `draft:544` | **"~2000× clean"** — `M20:111-112`, `README:83`, `queue:54` | Both superseded: band-matched H value is **515×**. |
| **β Pic b contrast** | **36 983×** — `M29`, `contrast-wall-note`, `draft:545` | **~5000×** — `M20:113`, `queue:54`, `README:84`, `HANDOFF:30` | **36 983× wins** (2MASS K on both components, band-matched to K2166). The ~5000× figure is the pre-M29 assertion and is **still live in README:84 and queue:54.** |
| **CD-35 2722 B contrast** | **97×** — `M29`, `draft:538` | **"≥ 2000× clean"** — `M20:111`, `README:83` | 97× (K) / **158×** (H, band-matched). |
| **HIP 65426 b / AF Lep b / 51 Eri b contrast** | **"~2000×" / "~30 000×"** — `M20:112,126`, `queue:50,54,55`, `M23:48-49` | **"not derivable"** — `contrast-wall-note:125,188-189` | The note is right that HIP 65426 b's m7 K is a limit and AF Lep b has no companion magnitude anywhere. **But 51 Eri b's K *is* measured in SIMBAD (18.67) → 450 000×.** |
| **HD 1160 companion letter** | **`HD1160 c`** — `m7-survey.json`, `M7:107`, `survey.py` | **`HD 1160 B`** — `queue`, `contrast-wall-note:190`, `M23:38`, `m29_contrast.py` | **B is correct** (SIMBAD: B at 0.700″/K 14.12; C at 5.157″/K 12.18). |
| **AB Pic b K** | **15.1** — `m7-survey.json`, `M17:49`, `M29:127` | **14.09** — SIMBAD `HD 44627B` | Conflicting; SIMBAD is the independent measurement. |
| **AB Pic b separation** | **"≥ 2.7″"** — `contrast-wall-note:122` | **5.400″** — Lazzoni | Bound true but 2× loose. |
| **CT Cha B separation** | **"≥ 2.7″"** — `contrast-wall-note:123` | **2.680″** — Lazzoni, **2.670″** — SIMBAD coords | The bound is marginally **false**. |
| **η Tel parallax** | 21.11 mas — Lazzoni | 20.603 mas — SIMBAD | 2.4% |
| **AB Pic parallax** | 21.97 mas — `m5-targets.json` (companion entry) | 19.945 mas — SIMBAD (host) | different objects' entries; 10% apart |
| **Lazzoni sample size** | **38** — `survey.py` docstring, `M7:3` and `M7 §3` | **37** rows in Lazzoni Table 1 | 37 + CD-35 = 38 |

---

## 7. (c) What downstream results move if these are corrected

**Highest impact — the contrast wall (paper-bearing).**
The wall's contrast axis is `contrast = 10^(0.4 (K_comp − K_host))` with `K_comp` from
`m7-survey.json`. Correcting the companion magnitudes and band-matching:

| row | published in draft/note | corrected | change |
|---|---:|---:|---|
| η Tel B | 1888× | **515×** (H) | ÷3.7 — **removes the "clean up to ~1900×" ceiling** |
| AB Pic b | 1768× | **698×** (K, SIMBAD) | ÷2.5 — removes the second support for that ceiling |
| CD-35 2722 B | 97× | 158× (H) | ×1.6, cosmetic |
| β Pic b | 36 983× | unchanged | the flooded anchor survives |
| PDS 70 | 460× | unchanged | survives |
| YSES 1 b | "not derived" | **334×** | new clean point |
| HIP 81208 B | "not derived" | **454×** | new clean point — **resolves §3.5** |
| CT Cha B | "not derived" | **285×** | new clean point |
| HD 1160 B | "not derived" | 679–731× | new (provisional tier) |
| HD 19467 B | "not derived" | **106 561×** | new (fiber tier — a clean 45 m/s pair at 10⁵ contrast) |
| 51 Eri b | "excluded; would be 3.8 M×" | **450 000×** | the exclusion argument as written is wrong |

**Net effect on the paper's claim:** *clean ≤ ~700×, flooded at ~37 000×, gap factor ~53* (was
*≤ ~1900× / factor ~20*). The negative result strengthens; §3.2, §3.5, §7 item 2, the abstract of
`contrast-wall-note.md`, and `draft.template.html` §9 (lines 536–553) all need renumbering.
`README:83-84`, `queue:54-55`, `M20:111-114` and `HANDOFF:29-30` additionally still carry the
**pre-M29 asserted** 2000×/5000× figures that M29 §6 already superseded — an unpropagated
correction independent of this audit.

**Second — the M7 ranking and every verdict derived from it.**
`k_mag` is the sole input to `hoy_calibrated_threshold_ms`, which sets `threshold_ms` →
`min_sat_mearth` → `verdict` → the sort order of all 38 rows. Using SIMBAD instead of Lazzoni:
HIP78530 B **9.6× better** (1789 → 187 m/s), YSES 1 b **5.0× better** (1632 → 326 m/s),
HD19467 B **5.7× worse** (259 → 1468 m/s), AB Pic b 1.6× better, 51 Eri b becomes rankable at all.
At least HIP78530 B and HD19467 B change *verdict class*, and HD19467 B is one of the three
targets M7 §4 names as ranking **above η Tel B** in Lazzoni's own ordering — the comparison that
justified pointing the pipeline at η Tel B first.

**Third — the η Tel B msini limit (M15, and the queue/README/LESSONS lines that quote it).**
"msini ≳ 0.5–1.2 M_Jup excluded, P = 20–300 d" is computed at `M_host = 47 M_Jup`, a
single-sourced Lazzoni value whose companion magnitude in the same table row is contradicted by
SIMBAD. msini scales as M_host^(2/3): a 20 M_Jup host would move the limit to ≈0.29–0.68 M_Jup,
a 60 M_Jup host to ≈1.2–1.4. **The published limit is only as good as that one number, and this
repository cannot check it.** Same structure for HIP 65426 b's "≳0.4 M_Jup (~115 M⊕)" at
`M_host ≈ 8 M_Jup` (M20 §4, Lazzoni Table 1).

**Fourth — the M28 contamination measurement, already partly paid for.**
`m28_contam.py` now scans 1.5–4.5″ rather than trusting a single offset, so the *measurement* is
robust. But both HTML drafts still report the result "at 2.8″ … and at 3.17″" and describe 3.17″
as a literature value. With 3.17″ unsourced, the two-column presentation should collapse to one.

**Fifth — no impact.** M14's CD-35 reproduction, M28 §§1–2's detection statistics, the sampler
reproducibility work, and all injection gates use no external object property.

---

## 8. (d) The most dangerous unsourced numbers, ranked

1. **η Tel B's K = 13.2** — anchors the wall's clean ceiling (1888×), the M7 threshold that set
   observing priority, and every "K = 13.2" in the queue and M15. Single-source (Lazzoni →
   Langlois 2021b, unarchived) and **contradicted by SIMBAD's measured H = 11.93**. Fixing it
   requires opening Langlois et al. 2021 or adopting the H-band ratio.
2. **CD-35 2722 B's 3.17″** — still in both HTML drafts, described as *"the 3.17″ value quoted in
   the literature"*. **It is quoted in no literature this repository holds**, and it has already
   caused one withdrawn measurement. It is the exact defect this audit was commissioned to find,
   and it is currently in the manuscript.
3. **HIP 81208 B's 0.3″** — carries the whole separation-axis counterexample (§3.5 of the wall
   note, and the two-axis conclusion that follows from it). No source anywhere; SIMBAD cannot
   confirm it. The note's own verify-item 4 already flags it; this audit confirms nothing backs it.
   *(Its contrast, by contrast, is now sourced: 454×.)*
4. **AF Lep b's separation, 0.45″ vs 0.32″** — two values, neither sourced, one of them a copy of
   the adjacent cell in the same dict.
5. **AB Pic b's K = 15.1** — pillar 2 of the "~1900×" ceiling; SIMBAD says 14.09.
6. **CD-35 2722 B's K = 12.01 (Wahhaj et al. 2011)** — not wrong as far as can be told, but the
   paper is **not in `papers/`**, and this single number anchors `hoy_calibrated_threshold_ms`,
   hence the entire 38-target ranking, and is pinned by `tests/test_satellites.py:78`. The most
   load-bearing unarchived citation in the project.
7. **η Tel B's mass, 47 M_Jup** — the M15 headline limit's denominator; single-source.
8. **51 Eri b's "no measured K" flag** — false per SIMBAD (K = 18.67), and the flag is used as an
   argument in print.
9. **CD-35 2722 B's age, 100 Myr / "AB Dor moving group"** — no archived source. Low impact
   (feeds only `activity_floor_ms`, a constant 200 m/s for every row), but unsourced.
10. **β Pic b's 0.55″ and PDS 70 c's 0.24″** — both differ from Lazzoni's own `Sep` column
    (0.511″, 0.213″) by 8% and 13%. Cosmetic for the wall, but they are quoted to two significant
    figures as though measured.

---

## 9. What this audit could **not** check

- **Any Lazzoni Table 1 value where SIMBAD is silent** (20 of 38 companions' K, and all 38 masses,
  ages and host masses). Lazzoni's own sources — Langlois et al. 2021b, Bohn et al. 2020, De Rosa
  et al. 2020b, Maire et al. 2020a/b, Mesa et al. 2020, Wang et al. 2021, Desidera et al. 2021,
  Lagrange et al. 2019b, Chauvin et al. 2017, Sheehan et al. 2019, Stolker et al. 2021 — are
  **none of them in `papers/`**. Archiving even two (Langlois 2021b and Bohn 2020) would settle
  η Tel B, AB Pic b, HIP 78530 B and YSES 1 b, which is most of §8.
- **Wahhaj et al. 2011** — CD-35 2722 B's photometry and its 31 ± 8 M_Jup mass.
- **HIP 81208 B, AF Lep b, HD 206893 B, 2M0103AB b separations** — no in-repo paper, and SIMBAD
  coordinate pairs are not independently resolved for these systems.
- **Whether SIMBAD or Lazzoni is right** where they disagree. This audit reports the disagreement
  and which side has an independent measurement; it does not adjudicate. SIMBAD's `allfluxes` is
  itself a compilation, and for close companions its photometry provenance should be checked per
  object before any value is adopted.
- **SIMBAD coordinate-derived separations** are a weak secondary check only: astrometric epoch,
  orbital motion and unresolved component positions all bite (β Pic b, PDS 70 b/c, 51 Eri b,
  AF Lep b, HR 8799 b–e and GJ 504 b all return 0.000″ because SIMBAD carries no distinct
  position for the companion). They are quoted above only where they corroborate an independent
  value.
