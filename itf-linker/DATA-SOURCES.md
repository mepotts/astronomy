# DATA SOURCES

Endpoints, auth, formats, and access notes for every external feed. Values marked
**(verified 2026-07-29)** were measured by code in this repo against a live fetch; the rest
come from [`DISCOVERY/itf-linker.md`](../DISCOVERY/itf-linker.md) and are **not** yet
independently confirmed.

| Source | What | Endpoint | Auth | Format | Used in |
|---|---|---|---|---|---|
| **ITF** | ~9.3M unlinked observations | `minorplanetcenter.net/iau/ITF/itf.txt.gz` | **none** | MPC1992 80-col, gzipped | **M0** |
| **ObsCodes** | Observatory longitudes | `minorplanetcenter.net/iau/lists/ObsCodes.html` | **none** | fixed-width HTML | **M0** |
| **MPECs** | Published circulars | `minorplanetcenter.net/mpec/K{yy}/{packed}.html` | **none** | HTML `<pre>` | **M0** |
| Solicited targets | Observations lacking orbits | `.../mpcops/orbits/no-orbits-astrometry/` | none | `.obs` / `.xml` | M1 |
| NOIRLab DAD | `dad_dr2`, 662,154 tracklets | `datalab.noirlab.edu/tap` | anonymous ADQL | TAP | M2 |
| Identifications | **Submission** endpoint | `.../mpcops/submissions/identifications/` | — | JSON | M3 only |

**Everything M0 touches is anonymous HTTP GET.** No registration, no key, no rate limit
encountered.

---

## 1. The ITF (primary input)

`https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz`

**(verified 2026-07-29)**

| Property | Measured | Plan's figure (2026-07-28) |
|---|---|---|
| Size | 134,759,732 B | 134,758,290 B |
| Lines | 9,359,688 | 9,359,693 |
| **Observations** | **9,322,655** | — (the plan's figure is a *line* count) |
| Observatory codes | 882 | 882 |
| Observations dated 2026 | 248,819 | 248,810 |
| `Last-Modified` | Wed, 29 Jul 2026 05:26:45 GMT | moves daily |
| Download time | ~6 s | — |

**Regenerated continuously.** `Last-Modified` and `ETag` moved twice within one hour during
M0 while size and line count held. Any count must be quoted alongside the snapshot's
provenance, which `itf-linker fetch` records to `data/raw/itf.provenance.json`.

Top contributors **(verified)**: F51 Pan-STARRS-1 2,752,362 · W84 DECam 1,196,646 ·
G96 Catalina 1,083,646 · F52 Pan-STARRS-2 1,041,621 · T09 Subaru 872,715 · V00 Bok/Kuiper
484,879 · 705 462,094 · X05 Rubin 64,362 · C51 NEOWISE 34,943 · 645 SDSS 28,120.

### Format

Plain MPC1992 80-column. Field positions (1-based, inclusive):

```
 1- 5  minor planet number      (blank throughout the ITF -- 0 records carry one)
 6-12  packed designation / trkSub
13     discovery asterisk
14     note 1
15     note 2   (observation TYPE -- see the continuation trap below)
16-32  date, UTC, "YYYY MM DD.dddddd"
33-44  RA  (J2000.0), "HH MM SS.ddd"
45-56  Dec (J2000.0), "sDD MM SS.dd"
57-65  blank
66-71  magnitude (66-70) + band (71)
72     astrometric catalogue code
73-77  reference
78-80  observatory code
```

Confirmed against a real record — MPEC 2026-O57 prints `2009 AC16` astrometry under packed
designation `K09A16C` with catalogue code `X` (Gaia-EDR3), which pins columns 6–12 and 72.

### Traps found in M0

1. **Lines ≠ observations.** A space-based observation is *two* lines: the `S` line has the
   sky position, the following `s` line has the **spacecraft's geocentric x/y/z in the RA/Dec
   columns**. 36,860 `s` + 172 `v` (roving) continuation lines exist. Counting them inflates
   totals and injects garbage positions. C51's count halves exactly when handled correctly.
2. **1,282 `S` observations have no partner `s` line** — unusable for reduction.
3. **One malformed record** in 9.36M: observatory 947, `2004 03 28`, declination seconds
   `39 8` (space for the decimal point). A source defect; reject it.
4. **4 pre-1900 observations**, three within 0.0003 d of MJD 0, from modern CCD survey 705 —
   sentinel epochs, not real astrometry. Filter before any temporal partitioning.
5. **3 records have entirely blank designations** (columns 1–12).
6. **trkSubs are not globally unique.** `des278` spans 17 nights over 1,154 days; `soho183`
   12 nights over 3,555 days. Always key tracklets on `(desig, obscode, night)`, and treat
   multi-night trkSub groups as needing verification.

## 2. ObsCodes (supporting)

`https://www.minorplanetcenter.net/iau/lists/ObsCodes.html` — **(verified 2026-07-29)**
2,686 codes carry a longitude. Fixed-width: code in columns 1–3, east longitude in 5–13.

Needed because tracklets are keyed on **local** night. Space telescopes and roving observers
have blank coordinates and fall back to longitude 0; 38,329 ITF observations are affected.
Longitudes are wrapped to (−180, +180] so the night index equals the UTC date the night is
conventionally labelled with — see `M0-RESULTS.md` §4.

## 3. MPECs (validation)

`https://www.minorplanetcenter.net/mpec/K{yy}/{packed}.html` — the URL form in the plan is
correct; all three M0 targets returned HTTP 200. Index at
`.../mpec/RecentMPECs.html`.

Constituent observations appear in two forms, and **most identification MPECs carry only the
second**:

1. Full 80-column blocks (`Additional Observations:`) — exact positions. Only 1 of the 3 M0
   MPECs had these.
2. A `Residuals in seconds of arc` table — `YYMMDD` + observatory + O−C, in 2–3 side-by-side
   columns. A complete inventory of which observatory contributed how many observations on
   which night.

**Trap:** an MPEC may carry a *second*, two-row residual table headed *"First and last
observations above in comparison with prediction"* whose rows duplicate the main table.
Counting both inflated 2026-O57 from 49 constituent observations to 51.

## 4. Find_Orb build (WSL) — **(verified 2026-07-29)**

Find_Orb has **no supported Windows build**: its own README says the Windows version needs
MFC and the Microsoft compiler, and only pre-built EXEs are offered. The console binary
`fo` — the scriptable one, as opposed to the interactive ncurses `find_orb` — is therefore
built and run under **WSL Ubuntu 24.04**, and driven from Windows through
`src/itf_linker/fit/wsl.py`.

### Sources

| Repo | Purpose | Commit built |
|---|---|---|
| `github.com/Bill-Gray/find_orb` | orbit determination | `143c823` (2026-07-23) |
| `github.com/Bill-Gray/lunar` | ephemeris/time functions (`liblunar.a`) | `b939e9b` (2026-07-09) |
| `github.com/Bill-Gray/jpl_eph` | JPL DE reader (`libjpl.a`) | `a73f25e` (2026-07-09) |
| `github.com/Bill-Gray/sat_code` | Earth-satellite ephemerides (`libsatell.a`) | `ff7b989` (2026-02-04) |
| `github.com/Bill-Gray/miscell` | cloned by the project's own `DOWNLOAD.sh`; **not built** — `INSTALL.sh` never compiles it, and `fo` links only the three libraries above | `9ba48b3` |

The dependency list and build order below are the project's own, from `find_orb/DOWNLOAD.sh`
and `find_orb/INSTALL.sh`. The repos must sit as **siblings directly in `$HOME`**: the
makefile's `PREFIX` defaults to `~`, and its install directory is then `../.find_orb`
relative to the source tree, i.e. `~/.find_orb`.

### Steps actually run

```bash
# 1. Clone. (Equivalent to `bash find_orb/DOWNLOAD.sh -d $HOME`.)
cd ~ && for r in lunar jpl_eph sat_code find_orb miscell; do
  git clone --depth 1 https://github.com/Bill-Gray/$r.git
done
mkdir -p ~/bin ~/lib ~/include

# 2. Build, in INSTALL.sh's order. Headers -> ~/include, libraries -> ~/lib, binaries -> ~/bin.
cd ~/lunar    && make clean && make -j8      && make install
cd ~/jpl_eph  && make clean && make libjpl.a && make install
cd ~/lunar    && make integrat
cd ~/sat_code && make clean && make sat_id   && make install

# 3. Build ONLY the console binary.
#    `make` (= `make all`) also builds the interactive ncurses UI and fails without
#    libncurses-dev, which needs root. `fo` does not link curses, so `make fo` is enough.
cd ~/find_orb && make clean && make -j8 fo

# 4. Install. `make install` depends on `all`, so it would drag in the curses build;
#    the binary and the data files are copied by hand instead. The file list is the
#    makefile's own INSTALL_FILES, extracted from a dry run so it cannot drift.
mkdir -p ~/.find_orb
cp -u ~/find_orb/fo ~/bin/
cd ~/find_orb && make -n install 2>/dev/null | grep '^cp -u' | grep -v 'bin$' \
  | sed "s|\.\./\.find_orb|$HOME/.find_orb|" | bash        # 51 data files

# 5. JPL planetary ephemeris. Without one Find_Orb warns and falls back to its built-in
#    analytic theory. DE-440 covers 1550-2650, which spans the whole ITF.
#    (INSTALL.sh points at an ftp:// URL for DE-430 that no longer resolves.)
cd ~/.find_orb && wget https://ssd.jpl.nasa.gov/ftp/eph/planets/Linux/de440/linux_p1550p2650.440
#    -> 102,272,352 bytes

# 6. Turn perturbers on. THIS MATTERS -- see below.
sed -i 's/^PERTURBERS=.*/PERTURBERS=7fe/' ~/.find_orb/environ.dat
```

Result: `~/bin/fo`, `~/.find_orb/` (51 data files + DE-440), `~/lib/{liblunar,libjpl,libsatell}.a`.

### `PERTURBERS=7fe` is not optional

Find_Orb ships with `PERTURBERS=0`, which means "only whatever the automatic close-approach
logic switches on". For a main-belt asteroid that is *nothing*, and `elements.txt` then
reads `Perturbers: 00000000 (unperturbed orbit)`.

Neglecting Jupiter displaces a 2.5 AU asteroid by roughly ½·a_J·t² ≈ 7.7 × 10⁻⁷ AU over a
7-day arc — about **0.1″** at 1.5 AU geocentric. The MPC's post-fit gate is an RMS of
0.25″. A silently unperturbed force model would therefore consume a third of the entire
error budget. `7fe` is the hexadecimal mask for Mercury–Pluto plus the Moon; the setting
persists across runs and is echoed in every `elements.txt`, which
`fit/findorb.py::parse_elements_txt` records with each fit.

### Running it

```bash
fo <obs.txt> -O <output dir> -x <config dir>/ -q -i
```

`-O` sends results to a chosen directory, `-x` selects an alternate configuration
directory, `-q` suppresses progress output, `-i` ignores any previously stored solution so
a run does not depend on earlier state. Outputs: `total.json` (merged elements + sigmas +
per-observation residuals for **every** object in the input), `covar.json` (6×6 state
covariance), `elements.txt` (human-readable, and the only place the force model is
recorded).

Two behaviours worth knowing, both found the hard way:

- **`fo`'s own `-p N` multi-process mode leaves `total.json` unmerged** — header, empty
  `objects`. Parallelism is done in Python instead, by splitting designations across
  single-process `fo` runs.
- **`fo` rewrites `environ.dat` inside its config directory on every run**, so concurrent
  runs sharing one config directory race. Each worker gets its own directory of symlinks
  (`fit/findorb.py::prepare_config_dir`); the 102 MB ephemeris is symlinked, so a worker
  costs a few kilobytes.

### Build verification

`itf-linker fit-selftest` runs a closed loop against **JPL Horizons**: fetch astrometric
RA/Dec for a known minor planet as seen from observatory 703, write it as MPC 80-column
astrometry, fit it with `fo`, then ask Horizons for the osculating elements *at the epoch
Find_Orb chose* and compare. Nothing in the truth values comes from Find_Orb.

**Result: 11 of 12 cases pass** (all 6 at the ITF-like 9-day cadence). On noise-free
49-day arcs the recovered semimajor axis matches JPL to 7 × 10⁻⁸ – 2 × 10⁻⁶ relative:

| Target | Cadence | RMS | Δa/a (clean) |
|---|---|---|---|
| (433) Eros — NEO | 49 d | 0.0026″ | −6.4 × 10⁻⁷ |
| (7) Iris — inner main belt | 54 d | 0.0034″ | −2.2 × 10⁻⁶ |
| (588) Achilles — Jupiter Trojan | 49 d | 0.0036″ | +7.0 × 10⁻⁸ |

With 0.30″ noise injected, every element lands within 2.1 σ of truth using Find_Orb's own
reported sigmas — which is the property the MPC's σ(a)/σ(q)/σ(i)/σ(e) gate depends on.

**The one failure is a real Find_Orb limitation, not a build fault.** On the 49-day Eros
arc with weekly gaps *and* 0.30″ noise, initial-orbit determination locks onto a
6-observation subset and returns a≈13.5 AU, e≈0.88. Isolated by A/B: the same 24 epochs
noise-free converge exactly; the same noisy data truncated to 14- or 21-day arcs converge
correctly (a = 1.426 / 1.466 vs truth 1.458). `-j`, `-y 5`, `-y 10` do not help. It does
not affect M1 — the fitted population has a median arc of 7 days — but a wide-cadence
NEO link should not be trusted from `fo` without a residual check.

**Do not declare positional sigmas below ~0.05″.** Find_Orb's weighted least-squares
(weights ∝ 1/σ²) becomes ill-conditioned below that; on the 8-day Eros arc, declaring
0.01″ returned a = 3.33 AU against a truth of 1.458 AU while reporting a plausible-looking
σ(a) = 0.25. At and above 0.05″ the solution is stable and σ(a) scales linearly with the
declared sigma. Real astrometry is never this precise, so the limit does not bind — but it
is a way to break a fit silently. Full table in `fit/verify.py`.

---

## 5. Later-milestone sources (not yet verified)

- **Solicited targets** — `.../mpcops/orbits/no-orbits-astrometry/`: `c51_desigs.txt`
  (440 NEOWISE designations), `no_orbit_desigs.obs` (14.6 MB), `no_orbit_desigs.xml`
  (85.6 MB). **The MPC is explicitly asking for this work.**
- **NOIRLab DAD** — `dad_dr2` via anonymous ADQL at `datalab.noirlab.edu/tap`; 662,154
  tracklets, `movgrp` carries `digest`/`mpcid`/`mpcsent`, coverage 2012-10-24 → 2018-04-20.
- **Submission** — JSON to `.../mpcops/submissions/identifications/`; format spec at
  `.../documentation/identifications/submission-format/`; acceptance criteria at
  `.../identifications/additional/`. **M3 only, sandbox first, per-batch human review.**

### Published acceptance criteria (implemented and tested in M0)

ITF-to-ITF links are **auto-rejected** if: fewer than 3 distinct nights · arc < 3 days ·
exactly 3 nights with arc > 15 days · the arc both starts *and* ends with a single-detection
tracklet. After fitting: rejected if RMS > 0.25″ or non-convergence. Three-night links
additionally need σ(a) < 0.05 AU, σ(q) < 0.05 AU, σ(i) < 0.5°, σ(e) < 0.05.

The night/arc/singleton gate is implemented in `verify/mpec.py::acceptance_summary` and
verified to accept all three published MPECs while rejecting each failure mode. The
post-fit RMS and covariance gates await the Find_Orb wrapper (M1).
