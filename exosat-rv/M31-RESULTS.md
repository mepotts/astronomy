# M31 — HIP 65426's three HiRISE nights through the validated fibre path (2026-08-14)

M30 staged three public HiRISE H1567 nights of HIP 65426 (27 frames, prog 114.2712 —
another team's; the M20 §5 priority caveat rides along) and banked their minimal-calib
URL lists. M31, approved by Matthew, extracts them through the chain the concurrent
session validated on β Pic b (M29 §§15, 19–20; commits 198ef74, 4de1ed0).

**Headline: all 27 frames of all three nights extract and verify by contents — 21
non-empty orders each, FPET wavelength solutions, ranges identical to the β Pic
reference to <1 nm — and the on-sky test transfers: night 2's deep frames share
tellurics with its host at 11.8σ at exactly 0 km/s, against the bpbhi benchmark's
9.8σ. The chain generalises with zero parameter changes. The same numbers also close
a door: HIP 65426 b itself sits 40–130× below the fibre background in every deep
frame (ΔH2 = 11.14 sourced from Chauvin et al. 2017 against the measured host rates),
so this corpus is a methods and telluric-reference asset, not a companion-spectrum
dataset.**

Machinery (committed, LF, verified with `file` from WSL): `scripts/cr2res/m31_night.sh`
(driver) → `m31_fetch_cal.sh` (banked lists, LESSONS §3.6 discipline) →
`m31_reduce.sh` (the reduce_hirise.sh chain + footprint management) →
`scripts/m31_verify.py` (contents, not existence — LESSONS §4) →
`scripts/injection/m31_ccf.py` (the M29 §20 statistics + host/deep classing by
measured flux). Verification numbers: `data/m31-verify.json` (committed); full logs
`~/cr2res/logs_m31/`.

---

## 1. Disk reconciliation first (Matthew's correction, applied)

Measured at session start: the WSL data volume `/dev/sdd` (1007 GB) at **949 GB used,
7.2 GB free, 100%**; `/mnt/c` at 3.3 TB with **689 GB free**. No esorex/cr2res/curl
process running (`ps` checked before any I/O) — the β Pic thread was idle throughout.

**Decision: stay on the ext4 data volume and manage the footprint, rather than route
to C:.** Two reasons: DrvFs I/O is slower, and — decisive — **ESO raw filenames
contain colons (`CRIRE.2025-01-31T09:31:18.060.fits`), which NTFS rejects**, so both
the calib fetch and every esorex product named after an input frame would need a
renaming layer on any C:-backed path. The footprint plan instead (all in
`m31_reduce.sh`, documented inline):

| lever | size | justification |
|---|---:|---|
| dark **masters** deleted right after BPM selection | 201 MB × 6–8 DITs/night | nothing in the validated chain consumes them — `util_calib` takes BPM + master flat only |
| per-frame `_cal.fits` + `_cal_extrModel.fits` deleted once its `extr1D` exists >200 kB | 403 MB/frame | the extr1D (1.4 MB) and slit function (0.14 MB) are kept; bpbhi kept these and paid 15 GB |
| flat `slit_model` + `wave_map` deleted at night end | 402 MB/night | diagnostics, consumed by nothing downstream |
| night's **calib raw** deleted after verification passes (`m31_cleanup.sh`, gated on a clean verify JSON) | 1.3–1.6 GB/night | LESSONS §4 sanction + the house rule "the archive is the backup"; logged below |
| **science raw kept** | 1.3 GB total | with the masters kept, `util_calib`+`util_extract` re-run at any height in ~30 s/frame — M32's re-extraction path needs no re-fetch |

Outcome: free space never fell below **4.0 GB** (floor during night 3); ended at
**5.4 GB free** vs 7.2 at start, the difference being red_m31's 1.78 GB of durable
products. Nothing belonging to any other thread was read, written, or deleted.

**Deletion log (sanctioned, each file printed in `~/cr2res/logs_m31/m31_*_cleanup.log`):**
h65hi1: 33 calib raw, 1591 MB · h65hi2: 27, 1301 MB · h65hi3: 30, 1446 MB —
**90 files, 4.34 GB, all after their night's contents verification passed.**

## 2. The inputs, header-verified (and one aborted template)

All 27 staged frames read: `INS MODE = HIRISE`, `INS WLEN ID = H1567`,
`DPR TECH = SPECTRUM`, `TPL ID = HIRISE_spec_obs`. Per night (DIT · TPL EXPNO/NEXP):

| night | prog | OBJECT | structure (time order) |
|---|---|---|---|
| h65hi1 2025-01-31 | 114.2712.001 | HD 116434 | 2×200 s (1of1, 1of1) **bright host** · 5×1200 s (**1–5 of NEXP=6 — aborted template**) · 2×200 s (1of2, 2of2) faint |
| h65hi2 2025-02-01 | 114.2712.002 | HIP 65426 | 2×600 s (pair) **bright host** · 5×1200 s deep · 1×600 s (1of1) faint |
| h65hi3 2025-02-02 | 114.2712.002 | HIP 65426 | 2×600 s (pair) **bright host** · 6×1200 s deep (six 1of1) · 2×600 s (pair) faint |

The LESSONS §4 staging check (TPL EXPNO vs NEXP) caught h65hi1's deep sequence
aborted after 5 of 6 — fatal for `obs_nodding`'s even-count requirement, **irrelevant
for the per-frame util_ path**; all five frames reduce.

Two structural findings about HiRISE nights, extending M29 §16:

1. **A third frame class exists: trailing faint short-DIT frames** (sky/offset
   exposures; h65hi3's last frame extracts at exactly 0.0 median flux). The β Pic
   night had host + deep only. **DIT alone does not label the host** — classing must
   use measured flux per second (`m31_ccf.py` does: host-bright = short-DIT frames
   above 3× the deep rate).
2. **The M30-style raw-percentile probe cannot see a faint-but-real host trace.**
   h65hi1's 200 s host pair sits at p99.9 ≈ 8.9k (hot-pixel level, indistinguishable
   from its sky frames) yet extracts at S/N 10/pixel. β Pic's host was visible that
   way only because it saturates the percentile (18k). Extraction flux is the truth.

## 3. Calibration fetch: 90/90, zero failures

Per night from the banked lists (`logs_m30/m30_h65hi*_cal.txt`, verified LF with
`file` before use; `m31_fetch_cal.sh` refuses CRLF lists outright — commit 2e0781b's
trap): **33/33, 27/27, 30/30 attempted, 0 failed**, serial with 3-try loops and
sleeps, size-validated skip-existing, judged by files on disk. Calibs arrived as
`.fits.Z` (LZW); `gzip -d` decompresses them fine (the §3.4 `uncompresspy` caveat is
about Python, not gzip). M30's warning that DITs 4.281/9/15 s lack same-day darks
required **no action on this chain**: dark frames feed only `cal_dark`, whose masters
the chain never consumes — only the BPM is used, and the deepest (1200 s) BPM wins
selection on every night. No adjacent-day top-up was fetched; deviation from M30's
suggestion documented here with this reasoning.

## 4. Reduction: the validated chain, unchanged where it matters

`m31_reduce.sh` = reduce_hirise.sh (198ef74) with identical recipes, parameters and
SOF lines (`util_calib` → `util_extract --height=9 --method=SUM --smooth_slit=1.0`,
riding the `cal_wave` trace-wave; `util_trace` is not called on this path — that is
what the bpbhi run validated), plus the §1 footprint hooks. Every recipe exited 0 on
every night; every night used the real FPET solution (`tw_fpet`), not the flat
fallback; the H1567 lines catalog resolved to `lines_u_redman_H1567.fits` as on
bpbhi.

| night | science | extracted | orders/frame | wavelength (nm) |
|---|---:|---:|---:|---|
| h65hi1 | 9 | **9** | 21 | 1468.7–1780.6 |
| h65hi2 | 8 | **8** | 21 | 1468.7–1781.4 |
| h65hi3 | 10 | **10** | 21 | 1468.7–1782.0 |

Cross-check on the reference: the same statistic applied to a bpbhi extraction gives
**1469.0–1779.9 nm, 21 orders** — identical setting behaviour. (M29 §19's quoted
"1499–1744 nm" is a different masking of the same products, not a discrepancy.)

## 5. Verification by contents (LESSONS §4), per class

`m31_verify.py` gates: every science frame extracted; ≥15 non-empty orders/frame
(non-empty = >50% finite and non-zero scatter); content on all 3 detectors;
wavelength range inside H1567 expectations. **All gates pass on all three nights**
(`data/m31-verify.json`). The classes, by measured median flux (counts) and per-pixel
S/N:

| night | host-bright (n) | host flux · S/N · c/s | deep (n) | deep flux · err · S/N · c/s | short-faint (n) |
|---|---|---|---|---|---|
| h65hi1 | 2 × 200 s | 337 · 10.4 · **1.686** | 5 | 9.2 · 27.7 · 0.28 · 0.0077 | 2 |
| h65hi2 | 2 × 600 s | 2818 · 54.6 · **4.697** | 5 | 11.3 · 26.1 · 0.42 · 0.0094 | 1 |
| h65hi3 | 2 × 600 s | 2066 · 44.4 · **3.443** | 6 | 7.9 · 26.2 · 0.30 · 0.0065 | 2 |

Host coupling varies 2.8× across the three consecutive nights (1.69 → 4.70 c/s) —
fibre-injection efficiency is a per-night quantity; any cross-night photometric
argument must carry that factor.

## 6. The on-sky test (M29 §20 machinery, same statistics)

Benchmark: bpbhi host-vs-deep peak at 0.0 km/s, height 0.140, **9.8σ** (M29 §20).
Here, per night (all peaks quoted at their velocity; "at 0" = CCF value at v=0):

| test | h65hi1 | h65hi2 | h65hi3 |
|---|---|---|---|
| **host-vs-deep** | 4.8σ at 0 (global max at grid edge −140, 5.0σ); with h65hi2's brighter host: 5.0σ at 0 (max −38, 5.7σ) | **peak at exactly +0.0 km/s, height 0.0471, 11.8σ** | peak at exactly +0.0, height 0.0259, 2.9σ |
| host-vs-host control | 0.538 at 0, 14.7σ | 0.900 at 0, 9.6σ | 0.861 at 0, 10.6σ |
| deep-vs-deep split | 0.087 at 0, 16.4σ | 0.153 at 0, 23.3σ | 0.108 at 0, 18.0σ |

Plus: cross-night host(n1)-vs-host(n2): peak at exactly +0.0 km/s, 0.124, 3.1σ.
Pooled 3-night host-vs-deep: 2.9σ at 0 (max +8 km/s, 3.7σ); pooled deep split 8.4σ —
**pooling across nights weakens every statistic** (each night carries its own
wavelength solution, and only night 2's deep background is telluric-rich), so
per-night numbers are the honest ones.

**Verdicts:**

- **h65hi2 — ON-SKY PROVEN.** The deep-position extraction shares telluric
  absorption with the host down the same fibre at 11.8σ, peak at exactly 0 km/s;
  the transfer target beats the benchmark night (9.8σ).
- **h65hi3 — extracted and verified; on-sky signature present but weak** (2.9σ at
  exactly 0). Controls pass at 10.6–18.0σ.
- **h65hi1 — extracted and verified; deep-position telluric proof marginal** (~5σ at
  0, not the global max, under either host stack). Its host frames are proven real
  spectra (14.7σ internal control; 3.1σ cross-night peak at exactly 0).

One caveat recorded rather than glossed: a deep-split peak at 0 shift proves *shared
structure on the common wavelength grid* — sky emission, but conceivably also
detector-fixed residuals; there is no velocity lever inside one night to separate
them (the pooled deep split's elevated baseline, +0.024, is consistent with a
cross-night fixed-pattern component). The **host-vs-deep telluric CCF is the
discriminating test**, and night 2 passes it decisively. A plausible reading of the
night-to-night difference, not a claim: night 2's deep background is the brightest
(0.0094 c/s vs 0.0077/0.0065) — more scattered host light means more
telluric-absorbed continuum for the CCF to grip.

## 7. What these frames can never yield: HIP 65426 b's spectrum

Every input measured above or sourced: the companion sits at **ΔH2 = 11.14 ± 0.05,
ΔH3 = 10.78 ± 0.06** (Chauvin et al. 2017, Table F.1 — fetched to
`papers/text/chauvin2017_hip65426b.txt` this session, title page read; separation
830 mas, consistent with the audit's 0.824″). At the measured host rates, the
planet's expected contribution to a deep frame is

> host c/s × 10^(−0.4·ΔH) × 1200 s = **0.07–0.27 counts** (night- and band-dependent),

against measured deep-position backgrounds of 6–14 counts and per-pixel errors ~26:
**the planet is 40–130× below the fibre background in every deep frame** — per-pixel
S/N ~0.007 per frame, ~0.02 for all 16 deep frames co-added. Even a perfect
planetary template over 21 orders × 2048 px caps a CCF near **2–3σ**, before
telluric handling costs anything. Contrast bpbhi: β Pic b's flux *dominates* its
deep frames (21.6 counts ≈ host_rate/6027 — M29 §19's ratio *is* the planet), at
~280× more planet signal per frame than here.

So the fibre did suppress the starlight — and the planet then sits below the
instrument's own background floor at 1200 s. **This corpus's value is
methodological**: the second HiRISE target through the util_ chain, three host
epochs at S/N 10–55/px through the fibre, and a sky-frame set — a telluric/sky
reference library for the β Pic thread's next step, not a companion dataset. The
exomoon-regime lever on HIP 65426 b remains the K2192 slit series (M20 §4) and its
priority call.

## 8. Traps hit (all survivable, two new)

1. **Outer-shell variable expansion blanked a WSL-side `$P`** and bash executed a
   .py file as shell — my tooling slip, caught on the first line of output; rerun
   with literal paths. (The Windows→WSL quoting boundary is a standing hazard;
   committed scripts avoid it, which is LESSONS §5's point.)
2. **Raw-percentile staging probes under-call faint hosts** (§2). New.
3. **DIT does not label the host on HiRISE nights** — trailing sky frames share the
   host's DIT class (§2). New; `m31_ccf.py`/`m31_verify.py` class by measured rate.
4. h65hi1's aborted deep template (5 of 6) — pre-checked at staging, harmless here.
5. None of: CRLF (lists verified, scripts LF-checked from WSL), fetch throttling
   (90/90 with pacing), empty-product exit-0 (contents gated per frame and night).

## 9. For the ledger

| item | before M31 | after M31 |
|---|---|---|
| HIP 65426 HiRISE (3 nights, 27 frames) | staged raw, unreduced | **27/27 extracted, contents verified, wavelength-solved (FPET)**; products `~/cr2res/red_m31/h65hi{1,2,3}` (1.78 GB); science raw kept, calib raw deleted post-verification (logged) |
| util_ fibre chain | validated on one target (bpbhi) | **transfers to a second target with zero parameter changes**; on-sky proof reproduced at 11.8σ (h65hi2) |
| HIP 65426 b via HiRISE | "starlight-suppressed epochs on the exomoon-regime target" (M30 hope) | **companion out of photon reach in this corpus** (40–130× under background; CCF ceiling 2–3σ) — value is host/sky reference + methods |
| HiRISE night anatomy | host + deep (M29 §16) | + **trailing sky/offset class**; host classing by measured rate, not DIT |
| Data volume | 7.2 GB free | 5.4 GB free; floor 4.0 GB; no other thread touched |

## 10. Recommended M32

1. **Stay coordinated with the β Pic thread** (their stated queue: telluric removal
   against the same-fibre host, planetary-template CCF, injection gate on the util_
   chain — M30 §6.1). The natural contribution from this corpus: the three HIP 65426
   host epochs + sky frames as a cross-target telluric/sky reference; and the
   injection gate, once built there, should be run on one h65hi night as the second
   transfer check.
2. **Do not budget companion-search compute on the h65hi deep frames** — §7's
   ceiling is arithmetic, not pessimism. If M32 wants it anyway, re-extraction at
   different heights needs no re-fetch (science raw + masters kept).
3. HIP 65426 b's real lever stays the K2192 slit series + embargo calendar +
   Matthew's priority decision (M20 §5) — unchanged by M31.
4. Housekeeping option for Matthew: red_m31 keeps per-frame slit functions (small)
   and per-night masters (~0.6 GB/night); the 15 GB-class per-frame intermediates
   were never kept, so no cleanup decision is pending on M31's account.
