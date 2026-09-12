# XMM C0d: separate offline adjudication of retained metadata

Date: 2026-09-12. No HTTP, photon reads, code changes or rerun. This note is a
separate interpretation of retained metadata, **not a C0d PASS or amendment of
its executed rules**. The authoritative outcome remains STOP, worker exit 1,
with `STOP_SUMMARY_FOOTER`: five request markers, four accepted HEAD responses,
and one failed summary-validation slot.

## What the failure does and does not establish

The summary response was HTTP 200, `text/html; charset=ISO-8859-1`, with
Content-Length **50010**. The retained body contains exactly **50010 bytes** and
matches the worker receipt's SHA-256:

`aba0f32242f6d81b65132cdfa167dbc8f4d75c15ef2c5ab69a37d048e4fca837`.

The body ends in `</div>` followed by `</body>` and a newline, without the literal
`</html>` required by the frozen validator. There is no evidence of a client-side
short transfer relative to the advertised length. All six table openings have
six closing tags; all 132 row openings have closing tags. The final processing
footer and exposure table are present. This does not prove arbitrary upstream
HTML generation was perfect, but supports reading the explicit complete rows
below without pretending the frozen footer gate passed.

Offline interpretation used the advertised ISO-8859-1 encoding and an HTML
table parser; no external resources were loaded. The 98 exposure rows have 98
distinct `(instrument, exposure ID)` pairs and agree with the page's instrument
counts. The absence of a closing HTML tag is the exact recorded STOP reason;
it is not missing exposure rows inferred from a failed network transfer.

Sources: [retained body](XMM-C0d-2026-09-12-data/summary.html),
[HTTP receipt](XMM-C0d-2026-09-12-data/slot-5-http.json),
[failed-slot receipt](XMM-C0d-2026-09-12-data/slot-5-result.json).

## Observation and processing identity, directly transcribed

| Label in retained page | Value |
|---|---|
| Observation ID / page heading | `0884250101` |
| Target | `LTT 9779` |
| Revolution | `3931` |
| Odf Version | `004` |
| Start time | `2021-05-27T18:47:53.000` |
| Stop time | `2021-05-28T09:14:07.000` |
| Scheduled Length | `51974` — no unit attached to this header |
| Proposed Duration [s] | `43000` — seconds explicitly labelled here |
| Footer generator | `ppssumm-3.7.1` |
| Footer Processing Date | `2024-11-26T16:07:45` |
| Footer Odf Id | `3931_0884250101_004` |

The footer identifies the summary generator, not a verified installed SAS version
or a complete PPS version receipt. No explicit SAS version was found in this
page. The observation timestamps lack an explicit timezone suffix/label in the
retained table; they are preserved as written, not relabelled UTC. Observer
contact details and sky coordinates are unnecessary for this adjudication and
are not reproduced or sent anywhere.

## Exact rows corresponding to the selected EPIC products

These are the page's labels `Inst.`, `Exp Id`, `Sched.`, `Mode`, `Data Mode`,
`Filter`, `Position`, `Total Duration`, `Actual Start`, `Actual Stop`.

| Inst. / Exp Id | Sched. | Mode | Data Mode | Filter | Position | Total Duration |
|---|---|---|---|---|---|---:|
| EMOS1 / S001 | Y | PrimePartialW3 | Imaging | Thin1 | FILTER_A | 50020 |
| EMOS2 / S002 | Y | PrimePartialW3 | Imaging | Thin1 | FILTER_A | 50196 |
| EPN / S003 | Y | PrimeFullWindow | Imaging | Thin1 | blank | 49103 |

| Inst. / Exp Id | Actual Start | Actual Stop |
|---|---|---|
| EMOS1 / S001 | `2021-05-27T18:48:37` | `2021-05-28T08:42:17` |
| EMOS2 / S002 | `2021-05-27T18:48:56` | `2021-05-28T08:45:32` |
| EPN / S003 | `2021-05-27T19:14:17` | `2021-05-28T08:52:40` |

The exposure `Total Duration` header has **no explicit unit**. Separately,
subtracting each row's displayed start from stop gives nominal wall intervals
of 50020, 50196 and 49103 seconds respectively, matching those three numeric
values. This consistency is an inference, not a new unit annotation on the
source column. Assuming the page's timestamps share one clock, their nominal
three-camera intersection is `2021-05-27T19:14:17` through
`2021-05-28T08:42:17`, or **48480 seconds**. This is not measured simultaneous
good time, detector live time, cleaned exposure or an event selection.

In particular, the MOS modes are explicitly **PrimePartialW3**, not full-frame.
Do not silently substitute PrimeFullWindow or infer usable common sky coverage,
source location on active CCDs, EXOD mode compatibility, valid event flags or
background acceptability from these rows. Those remain data/header and scientific
control checks. The page alone does not establish instrument-product calibration
equivalence to the published EXOD control analysis.

## Every exposure row accounted for

| Instrument | Declared exposures / parsed rows | Disposition of all rows |
|---|---:|---|
| EMOS1 | 2 / 2 | S001 above; U002 is unscheduled PrimePartialW3 / Imaging / CalClosed / NOT_VALID_CS. |
| EMOS2 | 2 / 2 | S002 above; U002 is unscheduled PrimePartialW3 / Imaging / CalClosed / NOT_VALID_CS. |
| EPN | 14 / 14 | S003 above; U700 is unscheduled Offset / Offsetdata / Thin1; U002–U013 are 12 unscheduled Diagnostic / Discardedlinesdata rows with blank filter. |
| RGS1 | 34 / 34 | S004 is scheduled HighEventRateWithSES / Spectroscopy; S900–S932 are 33 scheduled Diagnostic3x3 / Diagnostic rows. Filters blank. |
| RGS2 | 34 / 34 | S005 is scheduled HighEventRateWithSES / Spectroscopy; S900–S932 are 33 scheduled Diagnostic3x3 / Diagnostic rows. Filters blank. |
| OM | 12 / 12 | Ten scheduled Fast / Fast, imaging rows: S006 and S008–S016; S007 and S400 are scheduled UNDEFINED with blank Data Mode. All have UVM2 filter. |
| **Total** | **98 / 98** | **Three selected EPIC rows, 95 other configuration/exposure rows retained and accounted for.** |

All six instruments are marked Active `Y`. Instrument priorities are EMOS1=0,
EMOS2=0, EPN=1, RGS1=0, RGS2=0 and OM=2. These flags do not convert diagnostic,
closed-filter or undefined rows into additional science exposure. Exposure IDs
are unique only together with instrument; the repeated U002 or S900 labels must
not be deduplicated across cameras.

The two extra MOS rows display durations 1515 and 1319, with respective intervals
`2021-05-28T08:45:30`–`09:10:45` and `08:48:46`–`09:10:45`. The PN U700 row
displays 497 and spans `2021-05-27T19:05:47`–`19:14:04`. Each of the twelve PN
diagnostic rows displays 1; collectively their listed timestamps lie between
`2021-05-28T09:10:04` and `09:14:07`, not one continuous science interval. These
rows are not added to the selected event-list durations or requested as products.

## Size evidence and narrow next eligibility

All four saved HEAD receipts show the fixed method, HTTP 200, positive decimal
Content-Length, zero body bytes read and no retained product body:

| Exact product filename | Advertised compressed entity bytes |
|---|---:|
| `P0884250101PNS003PIEVLI0000.FTZ` | 109245605 |
| `P0884250101M1S001MIEVLI0000.FTZ` | 7643540 |
| `P0884250101M2S002MIEVLI0000.FTZ` | 9972723 |
| `P0884250101EPX000OBSMLI0000.FTZ` | 120581 |
| **Total** | **126982449** |

These are advertised stored compressed sizes, not verified body checksums,
decompressed FITS sizes, RAM requirements or available photon counts. Coupled
with the explicit summary rows, they support specifying a **separately approved,
bounded published-control product/header validation**. They do not authorize
that acquisition here or demonstrate a scientifically usable bundle. Expanded
resource bounds, exact FITS identities, camera/mode/FOV compatibility, GTIs,
timing calibration and processing versions remain unresolved gates.

Offline hash closure checked all **23 parent-outcome artifacts** and all
**17 worker-bound artifacts**, without changing them. Parent outcome SHA-256:
`7895f2fd39ce85ab745fbff40a291abbf7376086e9f58a2245352b2c348453a3`.
The four lengths were independently compared to their HTTP and slot receipts and
summed. No frozen metadata code was rerun or edited; no new request was made.

**Disposition: useful, internally consistent retained size/mode/timing metadata;
authoritative C0d STOP preserved; no photon or discovery acceptance.**
