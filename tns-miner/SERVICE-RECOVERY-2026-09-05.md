# TNS source recovery check — 2026-09-05

**Verdict: PARKED, pending source recovery or a proved replacement enumerator.**
The required Fink `Em*` class still cannot be retrieved within the bounded
diagnostic timeout. Two later documented ALeRCE TAP alternatives also timed out.
Both brokers serve other public data, so this does not show
that the whole service is down. No new scientific campaign, TNS registry scan,
candidate census, submission, or account action was started.

The fresh prospective alert window was MJD **[61285, 61288]**, September 2–5,
2026 UTC, exactly three days. These diagnostics ran September 5 at
13:40:22–13:47:40 UTC. They did not resume the stopped September 2 bundle.

## Measured checks

Thirteen serial public API requests were made across three immutable diagnostic
bundles. Each had a 10-second connection and 30-second read timeout, no automatic
retries, no redirects, and a fixed request list recorded before network access.
Fink requests asked only for the observation time (`i:jd`), never coordinates or
object IDs. ALeRCE returned at most one row; its exact response is private and
only aggregate metadata appears here.

The subsequent Rubin shortlist review found ALeRCE's supported TAP alternative.
Two additional finite ZTF-only aggregate probes brought the TNS recovery budget
to **15 requests**; their evidence is described below.

| Request | Result | Interpretation |
|---|---|---|
| Fink taxonomy | HTTP 200 in 0.735 s; **295 required classes**, including `Em*` | Existing taxonomy contract passes. |
| `Em*`, full three days, GET `n=1000` | Read timeout, 30.015 s | No count available. |
| `Em*`, full three days, GET `n=1` | Read timeout, 30.328 s | Reducing response size does not resolve it. |
| `Em*`, first 16 seconds, GET `n=1` | Read timeout, 30.313 s | Narrowing the time slice does not resolve it. |
| `CataclyV*` control, full window, GET `n=1` | HTTP 200 in 0.750 s; one valid time in the requested window | Fink can serve a target-family control; this cap-bound sample is not a class census. |
| ALeRCE `firstmjd`, corrected query, count enabled | HTTP 200 in 2.218 s; **reported total 3,512**, one row returned | New-source arm is responsive; its full pagination was not run, so this is not a proved E1 total. |
| ALeRCE `lastmjd`, ordered by ID, count enabled / disabled | Read timeouts, 30.016 / 30.172 s | No complete replacement pool or reliable count. |
| `Em*`, documented read-only POST, full window, `n=1` | Read timeout, 30.329 s | Alternate HTTP query encoding does not resolve it. |
| ALeRCE `lastmjd`, ordered by last detection descending, count enabled / disabled | Read timeouts, 30.203 / 30.188 s | Alternate documented ordering does not resolve it. |

Two initial ALeRCE requests incorrectly serialized the ranges as JSON strings;
they returned explicit HTTP 400 validation errors. They are retained in the
first diagnostic bundle and **do not count as evidence of a source outage**.
The helper was corrected to send repeated numeric parameters, matching the
existing science runner. A regression test now checks the prepared URL. The
science runner did not have this diagnostic-only defect.

The corrected `lastmjd` alternatives extended their upper bound to each probe
plan's creation time (MJD 61288.572325870686 and 61288.5737253975), rather than
stopping at midnight: a source active during the target window can have a later
last detection. This is only a potential over-enumeration strategy; completeness
and stable pagination under ongoing ingestion remain unproved.

## Alternatives reviewed

The current [Fink/ZTF API schema](https://api.ztf.fink-portal.org/swagger.json)
documents `class` as required for `/latests` and supports both GET and POST.
`/conesearch` restricts date filters to first detections, so it cannot substitute
for a known-source outburst enumerator. Object-history queries require names;
statistics supply counts rather than the identities needed for a complete pool.
No documented drop-in all-class time-range enumerator was established.

The current [ALeRCE client reference](https://alerce.readthedocs.io/en/latest/apis.html#alerce.Alerce.query_objects)
documents `lastmjd`, counting and ordering options for ZTF. The four corrected
last-detection probes above exhausted the cheap combinations of the existing
ordering and the date ordering, with and without a count query. A timeout is not
a scientific zero, and it does not prove a longer or differently hosted request
could never succeed. It is the stopping point for this finite recovery attempt.

**TAP follow-up, 13:59:19–14:00:20 UTC:** the official
[June 30 migration guide](https://science.alerce.online/services/accessing-data-tap/)
documents an independent ADQL interface and says ZTF users should select the
`ztf` schema. Two `GET https://tap.alerce.online/tap/sync` requests used
`ndet>=2 AND lastmjd>=61285 AND lastmjd<=<probe creation MJD>`: a `COUNT(*)`
query and `SELECT TOP 1 lastmjd ... ORDER BY lastmjd DESC`. Both timed out at
30.016 and 30.203 seconds, respectively. The same TAP session successfully
served known Rubin controls, so the supported service itself is reachable.
This alternative does not currently remove the TNS blocker either. The exact
requests, source and failure records are in ignored
`data/probes/20260905_rubin_tap/`; its manifest SHA-256 is
`1a175e682a93616bf0e4b34c9cefa325cc3a9c2b58401714be41290bbc4e35e9`.
That shared bundle also contains six Rubin metadata/control requests, which
are not TNS recovery probes.

## Retained proofs and reproduction

All response bodies remain under ignored `data/probes/`. Five exact HTTP entity
bodies total **9,058 bytes**; ten timed-out requests have no response body to
invent. Contracts, per-request timestamps/statuses, result JSON, and manifest
digests are retained. All 13 manifest file entries and all three executed helper
copies re-authenticated after the probes. The first helper copy was preserved
after execution and separately verified against its pre-run contract digest;
later bundles include the source copy in their manifest.

| Private bundle | Requests | Manifest SHA-256 |
|---|---:|---|
| `20260905_services_v1` | 7 | `8ab85a61b517e3f9dc4c3aa9ef51ca222d8524aaaa247df53664416bc2176f84` |
| `20260905_services_v2_alerce` | 3 | `0f7cadd34dc1cd73ff4d5e9a26b9073fc8d3fb9ecba4b641c4ce4fd13ea9ace7` |
| `20260905_services_v3_alternatives` | 3 | `4e7630f5fd88b891ea0185a14e65062ecd0d88ab719dbf6bde60db926a720c97` |

Executed commands, from the repository root:

```powershell
./tns-miner/.venv/Scripts/python.exe tns-miner/scripts/probe_service_recovery.py --tag 20260905_services_v1 --mjd-end 61288
./tns-miner/.venv/Scripts/python.exe tns-miner/scripts/probe_service_recovery.py --tag 20260905_services_v2_alerce --mjd-end 61288 --only-alerce
./tns-miner/.venv/Scripts/python.exe tns-miner/scripts/probe_service_recovery.py --tag 20260905_services_v3_alternatives --mjd-end 61288 --alternatives-only
```

These tags cannot be reused. The first two commands ran earlier helper versions,
which are preserved in their respective bundles; the current helper includes the
parameter correction and the final variants. Final executed helper SHA-256:
`6246d4c10fca2e45bd5fffebb06000b4949561773e33186fcab2ad31c8897f9e`.

A post-execution root-Ruff review sorted imports, removed unused suppressions and
made invalid payload **types** raise `TypeError` (invalid numeric values still raise
`ValueError`; the runner already catches both). The archived executed copies remain
unchanged. The working helper at that review had SHA-256
`d63fe97adcc75a16eb25094ad14f2b5fa7b47e89cdbafcc7f58c65b0ca56c599`;
76 tests and full root-config Ruff 0.16.5 passed again. No new service probe was run
as part of this formatting/exception-type correction.

Validation: **76 TNS tests pass**, including six new diagnostic regressions;
Ruff and Python compilation pass; diagnostic bundles are confirmed ignored.
No scientific threshold, cache reuse policy, candidate membership, or TNS
read-only guard changed.

## Exact restart condition

1. On evidence of service recovery, rerun the bounded helper with a unique tag
   and a **newly closed three-day** window. `Em*` must return structurally valid
   in-window rows and the taxonomy must still authenticate. A cap-bound result
   requires the existing science runner's complete bisection, not a zero or a
   dropped class.
2. Start a **new** `run_proved_window.py` campaign. Its fresh full TNS scan must
   start after, and within one day of, the alert ceiling. Every required E2
   class, E1 page and input proof must complete before `SEALED.json` exists.
3. If Fink remains unavailable but another source responds, freeze and review a
   replacement-source protocol that proves coverage, pagination, date semantics
   and recall of known historical outbursts before inspecting candidate ranks.

Until then, keep this front parked. M31/M81 remains a separate unvalidated
extension requiring its enumerator, host-background treatment and own positive
control; seasonal observability alone does not reopen it. Human submission and
account gates remain as documented in the operating guide.
