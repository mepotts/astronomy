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
| **Horizons** | Ephemerides + osculating elements | `ssd.jpl.nasa.gov/api/horizons.api` | **none** | text | **M1**, **M2** |
| **MPChecker** | *"Is a known minor planet here?"* | `minorplanetcenter.net/cgi-bin/**mpcheck**.cgi` | **none** | HTML `<pre>` table | **M2** |
| **SkyBoT** | Cone search, 1889–2060 | `ssp.imcce.fr/webservices/skybot/api/conesearch.php` | **none** | JSON | **M2** |
| **SBIDENT** | JPL small-body identification | `ssd-api.jpl.nasa.gov/sb_ident.api` | **none** | JSON | **M2** |
| **SBDB** | Name → definite object + orbit | `ssd-api.jpl.nasa.gov/sbdb.api` | **none** | JSON | **M2** |
| Solicited targets | Observations lacking orbits | `.../mpcops/orbits/no-orbits-astrometry/` | none | `.obs` / `.xml` | — |
| NOIRLab DAD | `dad_dr2`, 662,154 tracklets | `datalab.noirlab.edu/tap` | anonymous ADQL | TAP | M2+ (not yet) |
| Identifications | **Submission** endpoint | `.../mpcops/submissions/identifications/` | — | JSON | M3 only |

**Every source above is anonymous HTTP GET.** No registration, no key. M0 and M1 met no
rate limit at all; M2 met exactly one hard refusal, documented in §6.3.

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

### The parallax constants, and why splitting on whitespace is wrong — **(verified 2026-08-02)**

M3 needs the observatory's *position*, not just its longitude, so it parses the two further
fixed-width columns: `rho cos phi'` in 14–21 and `rho sin phi'` in 22–30, both in Earth
radii, already folding in the Earth's flattening.

**They must be read by column, not by `split()`.** The fields abut in many rows and the
separator simply disappears:

```
005   2.231000.659891+0.748875Meudon
F51 203.744090.936241+0.351543Pan-STARRS 1, Haleakala
```

`"005   2.231000.659891+0.748875Meudon".split()` yields `['005', '2.231000.659891+0.748875Meudon']`
— a longitude that is not a number. Whitespace splitting works on most rows and fails on
several major survey sites, which is the worst possible failure shape. `parse_obscodes_full`
slices columns and is pinned by a test carrying both forms.

All **2,686** codes that carry a longitude also carry both constants, so the two parsers
cover the same set. Codes with *no* coordinates at all — C51/WISE, 247 Roving Observer,
275 — are **omitted rather than defaulted**, and M3 drops their tracklets: placing a space
telescope at the geocentre misplaces the observer by up to ~0.01 AU, four times the
clustering radius, which fabricates links rather than finding them. In the MJD > 60000
slice that costs 114 observations, plus 248 dropped for carrying note 2 = `S`.
(500 Geocentric is present with all-zero constants, which is correct for it.)

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
---

## 6. Vetting services (M2) — **(verified 2026-07-29)**

Four services, all anonymous GET, all driven through
`src/itf_linker/vet/cache.py::CachedSession`: **≤1 request/second per host, no concurrency
anywhere, every 2xx response written to disk, exponential backoff honouring `Retry-After`,
and a circuit breaker that switches a service off after 5 consecutive failures instead of
retrying around it.** Errors are never cached — a 504 is a fact about a moment.

```
User-Agent: itf-linker/0.2 vetting (read-only; contact matthew.e.potts@gmail.com) python-requests
```

### 6.1 Summary of what each one is good for

| Service | Typical latency | Catalogue | Best used as |
|---|---|---|---|
| **SkyBoT** | 1–2 s | IMCCE, 1889–2060 | the primary sweep — every epoch of every candidate |
| **MPChecker** | 4–6 s | the MPC's own element files (1.41M objects) | the authority; every epoch |
| **SBIDENT** | 20 s – timeout | JPL SBDB + integrator | escalation only, recent epochs only |
| **SBDB** | <1 s | JPL | resolving a name to a definite object + its orbit |

### 6.2 SkyBoT cone search

`https://ssp.imcce.fr/webservices/skybot/api/conesearch.php`

Parameters used: `-ra` / `-dec` (degrees), `-rd` (radius, degrees), `-ep` (JD UTC),
`-loc` (IAU observatory code), `-mime=json`, `-output=all`, `-filter=0`,
`-objFilter=111`, `-from=itf-linker-vet`.

`-mime=json` returns a **bare JSON array**, one object per match, with units baked into the
key names (`"d (arcsec)"`, `"Err (arcsec)"`, `"VMag (mag)"`). An empty field returns `[]`.

- **`-filter=0` matters.** SkyBoT will otherwise apply its own positional-uncertainty cut,
  which silently turns a match into a non-match. Deciding what is too uncertain is the
  caller's job.
- **`Err (arcsec)` is the one genuinely useful extra.** No other service reports how
  uncertain the ephemeris it just computed is, and it is what lets a 30″ separation from a
  0.7″-accurate prediction be told apart from a 30″ separation from a 60″-accurate one.
- **No rate limit encountered** in ~450 requests at 1/s. Occasional single 5xx, cured by
  one backoff.
- Accepts every observatory code tried, including `X05` (Rubin).

### 6.3 MPChecker — three quirks, all found the hard way

**The endpoint in the project plan is wrong.** `checkmp.cgi` answers, but answers *every*
well-formed query with `Invalid data (R1/017/000/001) passed to script` and the note that
*"any use of WebCS scripts via a route other than our on-line forms is unsupported"*. The
form's own `ACTION` is **`/cgi-bin/mpcheck.cgi`**, and that one works.

**`METHOD=POST` is declared, but GET works** — which is what keeps this project's
"read-only GET only" rule intact.

**`oc=703` returns `403 Forbidden`.** Isolated by holding every other parameter fixed:

| `oc` | result |
|---|---|
| X05, O18, W84, 568, 269, T09, 304, 807, G37, 691, F51, 500, 084 | **200**, identical 3,886-byte page |
| **703** | **403**, nine-byte body `Forbidden` |

Cause unknown and not ours to fix; it is reported here because 703 is Catalina, a code any
minor-planet pipeline will reach for, and because it is indistinguishable from a block
until you vary it. It did real damage before being found: M1's Find_Orb self-test uses 703,
the M2 controls inherited it, and three consecutive 403s spent the circuit breaker's
failure budget and disabled MPChecker mid-run. The controls now use 568.

Parameters (all required — the CGI rejects a partial form):

```
year, month, day     UT date; day takes FULL precision despite maxlength=5 on the form
which=pos            search by position (which=obs takes 80-column records instead)
ra, decl             "HH MM SS.ss" / "sDD MM SS.s"; the sign on decl is mandatory
radius               arcminutes, 5 (minimum) .. 300
limit                limiting V magnitude
oc                   observatory code
sort=d mot=h tmot=s pdes=u needed=f ps=n type=p     output options; these are the defaults
```

- **`day` takes full precision.** `maxlength=5` is a client-side hint only. `day=18.093279`
  is accepted and moves the returned position ~15″ against the truncated `day=18.09`.
  Sending the truncated value puts a 14-minute smear — several arcseconds of main-belt
  motion — into every separation.
- **Comets are absent before 2009.** From the form's own notes: for 1900–2009 the
  comparison uses *"elements at the nearest 200-day epoch"* and covers only numbered and
  perturbed unnumbered minor planets; *"for more recent dates, all objects are included
  (including comets)"*. Before 1900, only the first 500 numbered minor planets. This is
  exactly why the 73P-C control returns nothing here — a coverage gap, not a negative
  result, and `vet/mpchecker.py::coverage_gap` labels it so.
- **Output precision is 0.1 s in RA and 1″ in Dec**, so separations from this service have
  a ~1″ floor. They are computed from those positions, not from the `Offsets` columns,
  which are rounded to 0.1 arcminute (6″).
- **Transient 504s are common.** Roughly 1 in 15 requests during M2; all cleared on the
  first or second backoff.
- Reports `Number of objects checked = 1411747`, which the MPC itself asks be checked for
  truncation.

### 6.4 JPL SBIDENT

`https://ssd-api.jpl.nasa.gov/sb_ident.api` · docs `https://ssd-api.jpl.nasa.gov/doc/sb_ident.html`

**It does not accept user-supplied orbital elements.** The M2 brief expected it to, and the
published parameter list settles it: the caller supplies an *observer*, a *time* and a
*field of view*, and the objects identified are always whatever JPL already knows about.
There is no element-based mode. Element-space corroboration therefore has to be done
afterwards, by resolving each match in the SBDB and comparing its catalogue orbit against
the fitted one.

**The first pass is not an identification.** With `two-pass=false` the API returns a coarse
pre-filter whose quoted positional errors run to ~1.6 × 10⁵ arcsec (44°) and which ignores
the requested field of view. Only `two-pass=true` with `suppress-first-pass=true` yields
positions worth comparing.

**Cost grows without bound as the epoch recedes.** Measured directly — first-pass-only
counts on one fixed field, observatory 703, seven epochs:

| epoch | first-pass rows | | epoch | first-pass rows |
|---|---:|---|---|---:|
| 2026 | 6,469 | | 2014 | 93,390 |
| 2023 | 5,355 | | 2010 | 189,980 |
| 2020 | 11,377 | | 2006 | 308,897 |
| 2017 | 37,889 | | | |

The pre-filter propagates catalogue elements with a two-body model, so its error grows and
it stops rejecting anything; the second pass then has to integrate all of it. A two-pass
request at a 2025 epoch (5,455 rows) returns in ~35 s; one at a 2006 epoch did **not**
return within 200 s, twice. `vet/sbident.py::too_old` therefore refuses epochs more than
**9 years** old before sending them — sending them anyway spends minutes of JPL's CPU to
learn something already measured.

Parameters used: `mpc-code`, `obs-time` (JD UTC), `fov-ra-center` (`hh-mm-ss.ss`),
`fov-dec-center` (`[-]dd-mm-ss.s`), `fov-ra-hwidth` / `fov-dec-hwidth` (degrees),
`two-pass=true`, `suppress-first-pass=true`, `mag-required=false`, `req-elem=false`.
`mag-required=false` is deliberate: the default `true` skips objects with no magnitude
parameters, which is a silent recall loss.

Separations are recomputed from the returned astrometric RA/Dec, not read from the API's
`Dist. from center Norm (")` column, which is quoted to two significant figures (`"1.E4"`).

### 6.5 JPL SBDB

`https://ssd-api.jpl.nasa.gov/sbdb.api` — `sstr`, `full-prec=true`, `discovery=0`.

**`full-prec=true` is not optional.** Without it elements come back rounded to three
significant figures (`"a": "3.06"` for 73P-C), which is coarser than any disagreement the
element comparison is trying to measure.

Its role is to turn a service's display string into a *definite object*, because the three
positional services name the same object three different ways:

```
MPChecker  (130536) 2000 QV208      2018 EC25
SBIDENT    887872 (2007 TO134)      (2018 EC25)      8 Flora (A847 UA)
SkyBoT     73P-C                    2018 EC25
```

**The normalisation is where the one genuinely dangerous bug of M2 lived.** An early version
peeled a leading integer off any name, which turned the comet `73P-C` into `73` and
resolved it, confidently and wrongly, to minor planet **(73) Klytia**. The positive control
is what caught it. The rules are now ordered and conservative, and anything unrecognised is
passed to SBDB unchanged (`vet/sbdb.py::name_to_sstr`, with the regression pinned in
`tests/test_vet_services.py`).

### 6.6 Observed costs, one full M2 run

Rates are the *effective* ones — the 1 s floor plus the service's own compute.

| Service | Requests | Effective rate | Failures |
|---|---:|---|---|
| SkyBoT | see `M2-RESULTS.md` §6 | ~1 per 2 s | rare 5xx, cured by backoff |
| MPChecker | ” | ~1 per 6 s | ~1 in 15 requests 504; all recovered |
| SBIDENT | ” | ~1 per 40 s | timeouts beyond ~9 years lookback |
| SBDB | ” | ~1 per 1.5 s | none |

Re-running the whole pass costs **zero requests**: every 2xx body is on disk under
`data/vet-cache/<service>/<sha256>.json`, keyed by the exact parameter set.

