# M1-06 — The submission path, documented but not walked

**Date:** 2026-08-24 · **Status:** research complete, **nothing submitted, no
account created, no sandbox write attempted**

> **House law, absolute.** No agent on this project has submitted, or will submit,
> anything to TNS — not a discovery report, not a classification, not a bulk
> report, not a sandbox test. Every step below is described so Matthew can act
> without doing the research. The steps marked **MATTHEW** require a human because
> they require registration, and no agent creates accounts.

## The rule this whole project rests on

TNS, verbatim: *"the formal 'discoverer' of a transient is defined to be the
reporter/s whose discovery report first turns to public."* Not first to observe —
first to report.

---

## Step 1 — **MATTHEW**: register a TNS user account

- URL: `https://www.wis-tns.org/user/register`
- TNS states registration *"is open to all professional astronomers as well as to
  amateurs."* Affiliation may be "None"; no group is required (group ID 0 =
  "None").
- Accounts are **human-vetted**, so there is latency. State plainly that you are
  an amateur data-miner working the public ZTF alert stream and describe the
  pipeline.
- **This gates everything downstream.** Nothing else on this list can be done
  first.

## Step 2 — **MATTHEW**: define a Bot and obtain an `api_key`

- URL: `https://www.wis-tns.org/bots` → "+Add bot".
- A Bot is associated with a survey/group and carries an `api_key` used to
  authenticate every submission. Multiple bots per affiliation are allowed.
- A new key can be minted later by editing the bot and ticking "Create new API
  Key".
- **Define the bot on the PRODUCTION site even while you are only experimenting**,
  because the sandbox is overwritten from production every Sunday and a
  sandbox-only bot will vanish (manual §3.1).

## Step 3 — what the sandbox is actually for

- URL: `https://sandbox.wis-tns.org` · test form: `https://sandbox.wis-tns.org/api/test`
- A **replica of production** that can be freely experimented with. Reset every
  **Sunday 04 UT** from the real site — anything you submitted there is gone, and
  so are any sandbox-only bot definitions.
- The manual is blunt about it: *"Please do not commence sending real Bulk reports
  to the production site before verifying on the sandbox environment that all your
  codes and scripts work flawlessly."*
- **It still needs real credentials** (an `api_key` and a `tns_marker`), which is
  why no agent has touched it. This is a Matthew step, not an agent step.

## Step 4 — the read side, which needs no account at all

| route | auth | verdict |
|---|---|---|
| `POST /api/get/object`, `/api/get/search` | `api_key` + `tns_marker` | **401 without credentials** — the sweep's "reads are open" is wrong |
| `GET /search?…&format=csv` | **none** | **works, tokenless** — this is what this project uses |
| `tns_public_objects.csv.zip` bulk mirror | `api_key` | **403 without credentials** |

Rate limit measured on **both** `/api/get/` and `/search`:
`x-rate-limit-limit: 10`, `x-rate-limit-reset: 60` — ten requests per rolling
minute, unauthenticated. This project throttles to 8/60 s. Bulk reports are
exempt from the read limit.

## Step 5 — the discovery (AT) report itself

Two routes, same schema:

1. **Interactive form** on the website — right for the first one or two reports.
2. **Bulk API** — `POST https://www.wis-tns.org/api/set/bulk-report`
   (sandbox: `https://sandbox.wis-tns.org/api/set/bulk-report`).

**Mandatory POST parameters:** `api_key` (the bot's key), `User-Agent` (the bot's
`tns_marker` string), `data` (the JSON report).

**Limits:** up to **10 entries** for a repeated item inside one report (e.g.
photometry points), and up to **100 report entries** per submission. Split larger
batches.

### The AT-report JSON, verbatim field names

```json
{"at_report": {"0": {
  "ra":  {"value": "10:20:30.04", "error": "0.5", "units": "arcsec"},
  "dec": {"value": "+20:30:40.05", "error": "0.5", "units": "arcsec"},
  "reporting_groupid": "2",
  "data_source_groupid": "2",
  "reporter": "M. Potts, on behalf of ...",
  "discovery_datetime": "2016-03-01.234",
  "at_type": "1",
  "host_name": "", "host_redshift": "",
  "internal_name": "",
  "internal_name_format": {"prefix": "", "year_format": "YY", "postfix": ""},
  "auto_class": [{"algorithm": "", "version": "", "objtypeid": 3, "prob": 0.8,
                  "additional_params": []}],
  "remarks": "",
  "end_prop_period": "", "prop_period_groups": [],
  "non_detection": {"obsdate": "2016-02-28.123", "limiting_flux": "21.5",
                    "flux_unitid": "1", "filterid": "50", "instrumentid": "103",
                    "exptime": "60", "observer": "", "comments": "",
                    "archiveid": "", "archival_remarks": ""},
  "photometry": {"0": {"obsdate": "2016-03-01.234", "flux": "19.5",
                       "flux_error": "0.2", "limiting_flux": "",
                       "flux_unitid": "1", "filterid": "50",
                       "instrumentid": "103", "exptime": "60",
                       "observer": "", "comments": ""}},
  "internal_ids": {}
}}}
```

Notes that matter:

- Keys were **renamed for TNS2.0**: `reporting_group_id` → **`reporting_groupid`**,
  `discovery_data_source_id` → **`data_source_groupid`**, `flux_units` →
  `flux_unitid`, `filter_value` → `filterid`, `instrument_value` →
  `instrumentid`. Old field names will be rejected.
- Every preset-value field takes an **id**, not a label. The id tables are at
  `https://www.wis-tns.org/api/get/values` (or the "Get AUX tables values id's"
  button on the bulk page).
- `internal_name_format` builds the internal name from the TNS-assigned name
  (prefix `iPTF` + `YY` + `16xyz` → `iPTF16xyz`) if you'd rather not supply one.
- `internal_ids` returns up to 5 key-value pairs untouched in the reply, for
  matching your own records. Not stored by TNS.

### The three blocking errors that will actually bite

From the manual's message-id table:

| id | message | consequence |
|---|---|---|
| **2** | *"At least one Photometry point — that of the discovery — should be filled"* | the discovery photometry point is mandatory |
| **6** | *"Last non-detection or archival info must be filled"* | **a pre-discovery non-detection (or archival info) is MANDATORY** |
| **1** | *"Last non-detection should precede the Discovery Datetime"* | and it must be earlier than the discovery |
| 5 | *"An identical AT report (sender, RA/DEC, discovery date, internal_name) already exists"* | duplicate guard |
| 3 | *"Required field"* | generic |

**Error 6 is the operational one.** It is why ATLAS forced photometry
(`https://fallingstar-data.com/forcedphot/`, free registration, amateurs
accepted, 60 submissions/min, 500 queued tasks, 100 positions/task) is not a
nice-to-have — brokers cannot give you photometry at arbitrary positions
*including non-detections*, and a report without one is rejected outright.
Registering there is a second **MATTHEW** step.

## Step 6 — the reply

- `POST https://www.wis-tns.org/api/get/bulk-report-reply`
  (sandbox: `https://sandbox.wis-tns.org/api/get/bulk-report-reply`)
- Mandatory: `api_key`, `User-Agent` (tns_marker), `report_id`.
- Submission returns a sequential **`report_id`** as a receipt. Poll for the reply
  every few seconds until it appears; processing is normally immediate but
  asynchronous. The reply says whether a new object was created or the
  coordinates already matched an existing one, and gives the designated name.

## Step 7 — after the designation

- The object gets `AT 2026xyz` and the discovery report gets an ADS-indexed
  bibcode of the form `2026TNSTR….1P`.
- **You cannot classify it.** A classification report requires a spectrum, no
  exceptions — which is why 92.1% of TNS objects in the last 12 months are
  unclassified (measured, `M1-02`). A confirming spectroscopist can be found
  through **ARAS** (`https://aras-database.github.io/database/novae.html`).
- **TNS AstroNotes** (`https://www.wis-tns.org/astronotes`) are open to any
  registered user and are ADS-indexed — a legitimate citable output that does not
  require owning a discovery.
- Registering a **reporting group** (DCAP is the precedent, group 195) makes
  discoveries carry a project name.

## Non-negotiables before any report is filed

1. **Sandbox first, always.** Learn the schema against
   `sandbox.wis-tns.org`, never the live registry.
2. **A false discovery report is a public, permanent, attributed error.** Every
   candidate must clear VSX, GCVS, SIMBAD, MPChecker (asteroid contamination),
   the ZTF `catflag` mask, and a cross-epoch artifact check. The filter in
   `M1-03` does the first four from Fink's cross-match columns; the last is still
   eyeball work.
3. **The classic false positive is a Mira.** Unfiltered CCDs over-respond to red
   objects, so long-period variables masquerade as novae. Colour-check before
   reporting. (This is the largest hole left in the M1 filter.)
4. **File `at_type` honestly.** Do not report as "Nova" what has not been
   classified. Let the spectrum decide the type.
5. **Never bypass the read rate limit.** 8 requests / 60 s; use the bulk CSV
   mirror for cross-matching once you have credentials.

## Sources

- Bulk API manual (TNS 2.0, updated Jan 2025) —
  `https://www.wis-tns.org/sites/default/files/api/tns2_manuals/TNS2.0_bulk_reports_manual.pdf`
- TNS getting started — `https://www.wis-tns.org/content/tns-getting-started`
- Register — `https://www.wis-tns.org/user/register` · Bots — `https://www.wis-tns.org/bots`
- Sandbox — `https://sandbox.wis-tns.org` · test form `https://sandbox.wis-tns.org/api/test`
- Value-id tables — `https://www.wis-tns.org/api/get/values`
- ATLAS forced photometry — `https://fallingstar-data.com/forcedphot/`
- ARAS spectroscopy network — `https://aras-database.github.io/database/novae.html`
