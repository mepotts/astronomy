# M1-01 — Kill checks: is this route reachable today, with no credentials?

**Date:** 2026-08-24 · **Verdict: PASS, with one correction to the sweep** ·
reproduce with `scripts/m1_killchecks.py`, raw output `out/m1_killchecks.json`

All probes below were made anonymously: no account, no token, no API key, no
cookie. No write path was touched.

---

## (a) TNS — API shape and rate limits

| probe | result |
|---|---|
| `GET https://www.wis-tns.org/api/get/object` | **HTTP 401 Unauthorized** |
| `POST https://www.wis-tns.org/api/get/search` | **HTTP 401 Unauthorized** |
| `GET https://www.wis-tns.org/search?…&format=csv` | **HTTP 200**, `Content-disposition: attachment; filename=tns_search.csv` |
| `HEAD .../system/files/tns_public_objects/tns_public_objects.csv.zip` | **HTTP 403 Forbidden** |

**Correction to the sweep.** `../DISCOVERY/README.md` §2 records "reads are
`/api/get/…`" in a way that implies they are open. They are not: `/api/get/` and
the bulk `tns_public_objects` mirror both require an `api_key` + `tns_marker`.

**The tokenless read route that does work** is the ordinary web search page with
`&format=csv` — the same CSV the "download" button produces, with every field the
web UI shows (ID, Name, RA, DEC, Obj. Type, Reporting Group/s, Discovery Data
Source/s, Disc. Internal Name, Discovery Mag/Flux, Discovery Filter, Discovery
Date (UT), Sender, …). It accepts `date_start[date]` / `date_end[date]`,
`reporting_groupid[]`, `num_page` and `page`, so a full year can be harvested
deterministically. **`num_page` maxes at 500** — `num_page=1000` silently falls
back to 50.

The per-object **report time** is not in the CSV. It is on the object page
(`https://www.wis-tns.org/object/<name>`) in the "AT Reports" table under
*"Time received (UT)"*. That distinction matters for the positive control: for
AT 2026stb the discovery epoch is 2026-07-08 06:35:20 UT and DCAP's report landed
2026-07-09 05:04:43 UT — **22.5 hours later**.

**Rate limit, re-measured today:** `x-rate-limit-limit: 10`,
`x-rate-limit-reset: 60` — ten requests per rolling 60 s, unauthenticated. The
sweep's figure is confirmed. Two things the sweep does not say, both measured by
watching `x-rate-limit-remaining` decrement across a mixed probe
(`/api/get/object` → 9, then `/search?…&format=csv` → 8, then four more
`/api/get/object` → 7, 6, 5, 4):

- **the same limit is served on the `/search` path**, not just `/api/`, so the
  tokenless CSV route is throttled identically; and
- **it is one shared bucket** — a `/search` call spends the same quota as an
  `/api/get/` call. There is no separate allowance for the route that actually
  works.

This project uses 8/60 s (7.5 s spacing) throughout, and never runs two
TNS-touching jobs at once.

## (b) Brokers — which give tokenless access to the full public ZTF stream

| broker | endpoint | tokenless? | newest alert seen | latency |
|---|---|---|---|---|
| **ALeRCE** | `https://api.alerce.online/ztf/v1/` | **YES** | MJD 61276.362 | 0.2 s simple / 42 s for a full-table `order_by=lastmjd` |
| **Fink** | `https://api.ztf.fink-portal.org/api/v1/` | **YES** (REST; Kafka needs free registration) | MJD 61276.362 | 0.43 s |
| **ANTARES** | `https://api.antares.noirlab.edu/v1/` | **YES** | MJD 61276.362 | 1.4 s |
| Lasair | `https://lasair-ztf.lsst.ac.uk/api/` | **NO** — per-account token; not probed | — | — |

MJD 61276.362 is **last night**. All three are still ingesting ZTF at full
cadence despite the wind-down. **Kill check (b) passes three ways.**

Practical differences that decided the architecture:

- **Fink is the richest.** `POST /api/v1/objects` returns the *complete raw ZTF
  alert packet* per detection (`i:drb`, `i:sgscore1`, `i:distpsnr1`, `i:distnr`,
  `i:magnr`, `i:ssdistnr`, `i:ndethist`, `i:jdstarthist`, `i:nbad`, `i:fwhm`,
  `i:elong`, `i:magdiff`, …) **plus Fink's own cross-matches**: `d:cdsxmatch`
  (SIMBAD), **`d:vsx`**, **`d:gcvs`**, **`d:tns`**, `d:roid` (MPC/solar-system),
  Gaia `d:DR3Name`/`d:Plx`, and `d:mangrove_*` (nearby galaxies). That removes
  the need for separate VSX/SIMBAD/MPChecker calls per candidate.
- **ALeRCE is the best enumerator.** `GET /ztf/v1/objects/?firstmjd=A&firstmjd=B`
  gives every object whose first-ever detection falls in a window, 1000 per page,
  with a working `count`. Fink's `latests` has no offset (it always returns the
  newest N, ceiling 1000 — `n=2000` returns HTTP 500), so it cannot page backwards
  through a night.
- **ANTARES** works and is live but was not needed once Fink + ALeRCE covered
  enrichment and enumeration.

**Verified property that the positive control depends on:** Fink stamps `d:tns`
at the moment it processes each alert and **does not back-fill**. On ZTF26abfokua
(= AT 2026stb) every alert before DCAP's report carries an empty `d:tns`; every
alert after carries `Nova`. The rewind is therefore genuine, not a lookup of the
answer.

## (c) Is ZTF still flowing, and how much?

**Yes.** `https://ztf.uw.edu/alerts/public/` holds **2,990** nightly tarballs; the
newest is `ztf_public_20260824.tar.gz`, posted **2026-08-24 07:15**, 4.2 GB.

Recent observing nights run **1.0 – 15.0 GB** compressed, median **8.3 GB** over the
last 30 (four of those 30 are 74-byte stubs — weathered-out nights).

Alert counts, from Fink's own nightly counters
(`POST /api/v1/statistics`, 182 nights of 2026 so far):

| | science alerts / night |
|---|---|
| median, 2026 | **135,245** |
| median, last 30 nights | **97,188** |
| maximum, 2026 | 313,532 |

Class breakdown for a representative night (2026-08-19, 83,247 science alerts):
simbad_gal 42,069 · simbad_tot 40,500 · Solar System MPC 28,230 · **Unknown
14,138** · LongPeriodV\* 9,014 · EclBin 8,252 · RRLyrae 6,851. The "Unknown"
bucket — no SIMBAD/VSX/GCVS/MPC match and no Fink classifier hit — is **5,000 to
14,000 alerts a night**, and that is the residue this project fishes in.

**ZTF primary operations still end December 2026.** The window is ~4 months.

---

## Verdict

| check | result |
|---|---|
| (a) TNS reachable for reads without credentials | **PASS** — via `/search?…&format=csv`, not `/api/get/` |
| (b) tokenless full-stream broker exists | **PASS** — ALeRCE, Fink and ANTARES all serve last night's alerts with no token |
| (c) ZTF still flowing | **PASS** — 4.2 GB posted this morning, ~97k science alerts/night |

No kill-check failure. The route is open. What is *not* open without an account:
TNS `/api/get/`, the TNS bulk object mirror, and every write path — all of which
are Matthew's steps (`M1-06`).
