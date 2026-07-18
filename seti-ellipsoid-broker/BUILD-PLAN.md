# BUILD PLAN — SETI Ellipsoid Alert Broker

Plan for a desk/data/software-only build (no telescope, no hardware). Facts current to
June 2026. See `SPEC.md` for the thesis and `DATA-SOURCES.md` for endpoints.

---

## 1. Chosen stack (justified)

| Concern | Choice | Why | Alternatives considered |
|---|---|---|---|
| Language | **Python 3.11+** | Entire astronomy/SETI toolchain (astropy, astroquery, voevent-parse, pyasassn) is Python; the prior art is Python; matches sibling catalog #5. | None viable — would re-implement astropy. |
| Packaging | **`pyproject.toml` + hatchling**, `src/` layout | Single source of truth, editable installs, clean test isolation; src-layout prevents accidental "works because cwd" bugs. | Poetry (heavier, lockfile churn); flat layout (import-shadowing risk). |
| CLI | **`typer`** | Declarative subcommands (`run`, `predict`, `version`), free `--help`, type-validated args; thin wrapper over click. | argparse (more boilerplate); click (typer wraps it more ergonomically). |
| Astronomy core | **astropy** (`SkyCoord`, units, `Time`), **astroquery.gaia** | Coordinate transforms, MJD/epoch handling, and the Gaia TAP client are first-party and battle-tested. | Hand-rolled trig (error-prone, no units). |
| HTTP | **`requests`** (+ official `lasair` client) | Lasair ships a thin client; `requests` covers any raw call. | httpx (async unneeded at nightly cadence). |
| FRB events | **`voevent-parse`** + **`comet`** broker | Standard VOEvent parsing; Comet is the reference subscriber CHIME documents. | lxml by hand (reinvents voevent-parse). |
| Optical corroboration | **`pyasassn`** (ASAS-SN Sky Patrol V2) | Official client, no auth, ~111M-target light curves. | Direct DB (undocumented). |
| Storage | **SQLite** (stdlib `sqlite3`) staging + flat **CSV/VOTable/.tgt/.md** artifacts | Zero-ops, file-based, perfectly reproducible, trivially diffable in git; matches "self-contained, installable." | Postgres (ops overhead for a solo nightly job); Parquet (fine for bulk LCs later). |
| Scheduling | **GitHub Actions cron** (M2+) | Free, no server to babysit, artifacts publish to **GitHub Pages**; logs are public/auditable. | Local cron (laptop must be on); a VPS (cost, ops). |
| Config / secrets | **env vars** (`LASAIR_TOKEN`, …) + `pydantic-settings` | Keeps tokens out of git; typed config. | dotenv-only (no validation). |
| Tests | **pytest** | Standard; lets us pin the ellipsoid math against the Nilipour reference star list. | unittest (more verbose). |

**Note on CHIME hosting:** the CHIME/FRB subscription needs a **static, allowlisted public IP**
(see `DATA-SOURCES.md` §4). A GitHub Actions runner cannot hold a stable inbound IP, so the
CHIME ingest path (M2/M3) requires either a small always-on VPS running `comet`, or a
store-and-forward design where a tiny VPS captures VOEvents to a repo/bucket the Actions job
then reads. **This is an OPEN QUESTION for Matthew (below).**

---

## 2. Architecture

Two modes over a shared core. The shared core is the **3-agent pipeline** from the dossier;
the **Window Predictor** is a second entry point reusing the same ellipsoid + Gaia layers.

```
                         ┌──────────────────────────────────────────────┐
   external feeds        │            seti_ellipsoid_broker             │
   ───────────────       │                                              │
   Lasair ZTF  ─┐        │  ┌──────────┐   ┌───────────┐   ┌─────────┐  │
   ASAS-SN     ─┼──────► │  │ INGEST   │──►│ ELLIPSOID │──►│ EXPORT  │  │──► artifacts
   CHIME/FRB   ─┘        │  │ agent    │   │ agent     │   │ agent   │  │    CSV / .tgt /
                         │  └──────────┘   └─────┬─────┘   └─────────┘  │    VOTable / .md
   Gaia DR3 TAP ───────► │        (writes SQLite staging table)         │
   (shared layer)        │              ▲       │                       │
                         │              │       ▼                       │
                         │        ┌─────┴───────────────┐               │
                         │        │ WINDOW PREDICTOR     │──────────────│──► forward calendar
                         │        │ (proactive mode)     │              │    + iCal feed (M3)
                         │        └──────────────────────┘              │
                         └──────────────────────────────────────────────┘
```

- **Reactive broker (REACT mode, the dossier pipeline):**
  - **Ingest agent** — pull recent alerts from each feed, normalize to
    `(ra, dec, mjd, survey, mag_or_dm, source_ref)`, write to SQLite `alerts_staging`.
  - **Ellipsoid agent** — batch-crossmatch staged alerts to Gaia DR3 (one ADQL upload-join),
    apply quality cuts (RUWE<1.4, parallax_over_error>5), compute geocentric distance and
    signed ellipsoid offset `S(t)` + crossing epoch, flag uncertainty window < 2 yr, score by
    crossing proximity × stellar-density bin. Write `ranked_targets`.
  - **Export agent** — render `ranked_targets` to `ellipsoid_targets_YYYYMMDD.csv`, ACP `.tgt`,
    VOTable, and a Markdown digest.
- **Window Predictor (PREDICT mode, the proactive adjacent angle):**
  - Independently of any incoming alert, sweep Gaia DR3 stars near the SN 1987A line of sight,
    solve `t_cross` for each (reusing `ellipsoid.py`), and emit a **rolling forward calendar**
    (next N months of predicted shell crossings) plus an **iCal (`.ics`) feed** and a small
    **ephemeris JSON/CSV API artifact**. This is the "what will cross soon" companion to the
    reactive "what just lit up" broker, and it is the publication-differentiating piece.

Both modes are pure-functional over inputs → deterministic artifacts, so M0 can mock the feed
layer and still exercise the full ellipsoid + export path.

---

## 3. Repo layout

```
seti-ellipsoid-broker/
├── pyproject.toml
├── README.md
├── SPEC.md
├── DATA-SOURCES.md
├── BUILD-PLAN.md
├── .gitignore
└── src/
    └── seti_ellipsoid_broker/
        ├── __init__.py          # version
        ├── cli.py               # typer app: run / predict / version   (M0: wired, mocked)
        ├── config.py            # env-var settings (tokens, paths)      (M0: stub)
        ├── ellipsoid.py         # SN 1987A constants + crossing math    (M0: constants + signatures)
        ├── ranking.py           # quality cuts + scoring                (M0: stub)
        ├── models.py            # Alert / RankedTarget dataclasses      (M0: defined)
        ├── ingest/
        │   ├── __init__.py
        │   ├── lasair.py        # Lasair ZTF client wrapper             (M1)
        │   ├── asassn.py        # pyasassn wrapper                      (M2)
        │   └── chime.py         # VOEvent ingest                        (M2/M3)
        ├── gaia.py              # astroquery.gaia batched crossmatch    (M1)
        ├── predictor.py         # Window Predictor + iCal/ephemeris     (M3)
        └── export.py            # CSV / .tgt / VOTable / Markdown       (M1)
   (tests/ added at M1)
```

---

## 4. Milestones

### M0 — Skeleton (this commit) ✅
- `src/` package, `pyproject.toml` with real deps, `.gitignore`, `README.md`.
- `typer` CLI that **runs**: `seti-broker run` prints one **mocked** ranked target row;
  `seti-broker predict` prints a mocked upcoming-crossing row; `seti-broker version`.
- `ellipsoid.py` carries the real SN 1987A constants and function signatures (mathematical
  body stubbed / returns a deterministic placeholder).
- **Deliverable:** `pip install -e .` then `seti-broker run` exits 0 and prints a plausible row.
  No network, no real computation.

### M1 — Reactive broker, ZTF + Gaia only, nightly CSV
- Implement `ingest/lasair.py` (cone + SQL query, token from env, pagination handled).
- Implement `gaia.py` batched ADQL crossmatch + `ranking.py` quality cuts & scoring.
- Implement real `ellipsoid.py` crossing math and `export.py` (CSV + `.tgt` + Markdown).
- Add `tests/`; **validate against the Nilipour et al. reference list (≈32 TESS-zone targets
  should appear)** — this is the M1 acceptance gate.
- **Deliverable:** `seti-broker run` produces a real `ellipsoid_targets_YYYYMMDD.csv` from live
  Lasair+Gaia data, locally.

### M2 — Add feeds + automation + publish
- Add `ingest/asassn.py` (ASAS-SN corroboration) and `ingest/chime.py` (VOEvent parse).
- Stand up CHIME subscription (needs hosting decision — see Open Questions) and the
  GitHub Actions **nightly cron** that runs M1, then publishes artifacts to **GitHub Pages**.
- Add VOTable export. Post to Breakthrough Listen GitHub Discussions / SETI Institute Slack.
- **Deliverable:** a public, auto-updating nightly target page.

### M3 — Window Predictor + write-up
- Implement `predictor.py`: forward-calendar sweep, **iCal (`.ics`) feed**, ephemeris API artifact.
- FRB DM–distance consistency check (Macquart relation, stretch).
- Draft a 3-page arXiv technical note; reach out to Gallay/Davenport (UW) and Croft (BL Berkeley).
- **Deliverable:** `seti-broker predict` emits a rolling crossing calendar + `.ics`; arXiv note drafted.

---

## 5. First-task checklist (do these in order)

1. **[kill-check, do FIRST]** Email Eleanor Gallay (UW, `alert_seti` first author): *"Is
   `alert_seti` being developed into a public, maintained service?"* If **yes → contribute,
   do not duplicate.** If no/no-reply in 2 weeks → proceed.
2. **[kill-check]** Re-read the Lasair changelog / schema page for a **distance-aware alert
   schema**. As of June 2026 it is **not shipped** (verified) — but this is the strongest kill
   risk, so confirm before investing in M1.
3. Register a Lasair account, generate a token, export `LASAIR_TOKEN` locally; confirm a free
   cone search returns JSON (10 calls/hr is enough to start).
4. Run the Gaia TAP snippet from `DATA-SOURCES.md` §2; confirm anonymous `launch_job_async`
   returns a table with `parallax`, `ruwe`, `parallax_over_error`.
5. Pin the SN 1987A constants and write `tests/test_ellipsoid.py` first (TDD): a star at the
   known crossing geometry must yield `t_cross` in the expected ~2026–2028 window.
6. Implement `ingest/lasair.py` → SQLite staging → `gaia.py` crossmatch → `ranking.py` → CSV.
7. Reproduce the Nilipour ≈32-target validation set; only then call M1 done.

---

## 6. Kill criteria (carried from the dossier)

- **Strongest kill risk — Lasair ships a distance-aware alert schema.** Would let the existing
  prototype filters do this job natively and obsolete our Gaia TAP layer. **Check the Lasair
  changelog quarterly.** (Status June 2026: **not triggered** — verified open.)
- **Scientific sunset.** Ellipsoid crossing rate for dense Gaia targets **peaks ~2026–2028** and
  drops sharply after ~2030. Ship while the window is open; the project is intentionally finite.
- **Completeness caveat.** ~90% of ZTF/Rubin stars lack usable Gaia parallaxes; this is a
  **high-parallax-quality-star monitor, not a sky survey.** State plainly in any publication.
- **Pre-start duplication check.** If Gallay confirms `alert_seti` is becoming a maintained
  public service, **contribute rather than rebuild.**

---

## 7. OPEN QUESTIONS FOR MATTHEW

1. **CHIME hosting (blocks M2 CHIME path).** CHIME/FRB needs a `comet` subscriber on a machine
   with a **static, allowlisted public IP** — a GitHub Actions runner can't provide this. Do you
   want to (a) stand up a small always-on VPS for the VOEvent subscriber, (b) defer CHIME entirely
   and ship ZTF+ASAS-SN only, or (c) do a store-and-forward (tiny VPS captures events → repo →
   Actions reads)? Default if unspecified: **(b) defer CHIME**, keep the parser stub.
2. **Hosting/automation for the nightly run.** Confirm **GitHub Actions cron + GitHub Pages** is
   the intended home (free, public, auditable), vs. a self-hosted runner/VPS. Default: **Actions + Pages.**
3. **Scope of v0 vs. emphasis.** The dossier leads with the *reactive* broker; the brief asks to
   build in the *Window Predictor* as a co-equal second mode. Confirm priority: should M3's
   **predictor + iCal feed** be pulled earlier (it's the cleaner publication differentiator), or
   stay after the reactive broker is solid? Default: **reactive broker first (M1), predictor at M3.**
4. **Distribution.** Publish to **PyPI** as an installable (`pip install seti-ellipsoid-broker`),
   or keep it repo-only with the GitHub Pages artifact as the public face? Default: **repo + Pages
   first, PyPI once M1 is stable.**
5. **Identity.** Final package/CLI name + GitHub org/owner for the repo (affects `pyproject.toml`
   metadata and the Pages URL). Default placeholder used: package `seti_ellipsoid_broker`,
   CLI `seti-broker`.
