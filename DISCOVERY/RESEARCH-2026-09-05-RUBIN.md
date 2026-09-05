# Rubin broker finalist — 2026-09-05

**Recommendation: retain Rubin as the third finalist for an unknown-source
discovery pilot, conditional on a known-control audit first.** Public data access
works substantially better than the blocked ZTF outburst enumerator, but two
target-family controls have no current matches and one rich control has a
material cross-broker history difference. These are reasons to test coverage
before promoting a new search. This ranking is a research judgment, not a
measured comparison of discovery yield against CCOR-2 or Legacy Surveys DR11.

## The specific scientific question

Can Rubin's southern, deeper detections and accompanying forced photometry
recover **recurrent dwarf-nova-like outbursts on faint quiescent sources** that
are absent from existing variable-star catalogues and from the old ZTF search?
The discriminating evidence would be repeated, spatially consistent positive
events with quiescence measured between them, plus clean image morphology and
independent catalogue/history checks. An unclassified source with one bright
point would not answer this question. Photometry alone would establish a
candidate class, not a spectroscopic classification.

The generic idea of finding CVs with Rubin is already studied. Buckley et al.'s
[2025 CV study](https://arxiv.org/abs/2509.07298) models outburst detectability,
polar state changes and short bursts. Its results make cadence and saturation
central to sample selection; they do not establish that today's observed
footprint contains our target controls. A new contribution must come from an
actual previously unknown object or a clearly delimited measurement with a
defensible selection function, not from reimplementing an alert filter.

Competition is already substantial: Rubin distributes public alerts through
[seven full-stream brokers](https://rubinobservatory.org/for-scientists/data-products/alerts-and-brokers),
and ALeRCE already reported the two public Rubin objects used below. ALeRCE's
[current experimental tools](https://science.alerce.online/alerce-labs/) include
multi-survey exploration, transient hunting and a TNS reporting workflow. The
old portfolio claim that Rubin/TNS activity was confined to a small commissioning
batch is therefore obsolete. No claim that this CV niche is unsearched has been
established by this bounded review.

## What is accessible now

The live [Fink/LSST schema](https://api.lsst.fink-portal.org/swagger.json), version
3.7.0, separates object summaries, detected-source histories, forced photometry,
cutouts, cones and tags. Unlike the old ZTF class enumerator, the LSST
[cone guide](https://doc.lsst.fink-broker.org/services/api/conesearch/) explicitly
documents `kind=across` for objects varying inside a window even if they also
vary outside it. Its default `within` semantics are stricter. This is promising
for a bounded region or fixed catalogue; it is not proof of a complete all-sky
enumerator. A cone returns the most recent record per object, so full histories
require a separate `/sources` request. Caps, overlapping cones and association
duplicates need explicit accounting.

Fink's [migration guide](https://doc.lsst.fink-broker.org/data/ztf_to_lsst/)
documents real-time LSST database updates and multiple tags per alert; the ZTF
API is updated after the observing night. Thus the ZTF `Em*` failure should not
be treated as evidence that Rubin itself is inaccessible. Conversely, a union
of scientific tags is not automatically the full stream.

ALeRCE's supported [TAP interface](https://science.alerce.online/services/accessing-data-tap/)
also worked anonymously. The public
[LSST table notebook](https://github.com/alercebroker/usecases/blob/master/notebooks/LSST/ALeRCE_LSST_Tables.ipynb)
specifies `sid=1` for static `diaObjectId` objects, exact 64-bit IDs, and joins on
`(oid,sid,measurement_id)`. Detection times are renamed from
`midpointMjdTai` to `mjd`; that rename must not silently turn TAI into UTC.
Its latest object record is not a historical snapshot. All queried columns and
the complete published metadata response were retained before control queries.

## Actual bounded control retrieval

On September 5, 13:54–14:00 UTC, 29 read-only requests were made across three
retained bundles: **27 Rubin/public-documentation requests and two ZTF-only
aggregate fallback checks**. No unknown-source list or private target query was
made. Three guessed metadata/source locations returned 404 and were replaced
by the official published notebooks and TAP metadata; these were not data
outages. The two ZTF TAP requests timed out and are recorded separately in the
[TNS recovery closeout](../tns-miner/SERVICE-RECOVERY-2026-09-05.md).

| Already-public control | Fink detections / forced rows | ALeRCE detections / forced rows | Result |
|---|---:|---:|---|
| [AT 2026uqf](https://www.wis-tns.org/object/2026uqf), ID `170644228968284415` | 2 / 1 | 2 / 1 | Shared source IDs, fluxes and times agree. |
| [AT 2026spb](https://www.wis-tns.org/object/2026spb), ID `170635501063110696` | 1 / 0 | 1 / 0 | Both report no forced rows for this control; this is not a measured pre-discovery upper limit. |
| [Fink documented example](https://doc.lsst.fink-broker.org/services/api/forced_photometry/), ID `313761043604045880` | 693 / 580 | 742 / 589 | **49 extra ALeRCE detection IDs and 9 extra forced rows.** Difference remains unexplained. |
| VW Hyi, 3-arcsecond cone at public SIMBAD position | 0 objects | 0 objects | No target-family recovery established. |
| OY Car, same radius and public-name resolution | 0 objects | 0 objects | No target-family recovery established. |

All **696 Fink detection IDs** across the first three controls occur in ALeRCE.
On those common IDs, the maximum absolute time difference is **4.41 microseconds**
and the returned PSF flux values are identical. The extra 49 ALeRCE detections
of the rich control fall at MJD TAI **61091.028357–61097.163359**, well before the
probe; the few minutes between queries cannot explain them as newly observed
alerts. This is an observed database-content difference, not proof that either
broker is wrong. No recall or cross-broker completeness claim is made.

The three Fink FITS cutouts for AT 2026uqf were successfully fetched and parsed:
science, template and difference each contain finite **30×30** primary and
uncertainty arrays, with **41×41 / 49×49 / 41×41** PSF arrays respectively.
Together they are **109,440 bytes**. This establishes usable image access, not
an independent scientific vetting of the object. ALeRCE TAP served 745 joined
detection rows and 590 joined forced rows for the three public controls, matching
its object-table aggregate counts in this finite sample.

The two named CV nulls do not imply that no CVs are detectable: they could
reflect footprint, saturation, template history or association limitations.
The present test does not distinguish these explanations. It also does not
substitute successful supernova-like controls for a CV positive control.

## Constraints on a real pilot

Rubin [forced photometry](https://doc.lsst.fink-broker.org/services/api/forced_photometry/)
is available for alert-associated objects; it is not an arbitrary-position
forced-photometry service or proof of complete pre-discovery coverage. Rubin
[photometry semantics](https://doc.lsst.fink-broker.org/data/photometry/) use
nanoJansky fluxes and distinguish difference, science and template fits. Science
minus template PSF flux need not equal the separately fitted difference flux.
The old ZTF magnitude and sign cuts cannot simply be copied.

The current [known-issues record](https://doc.lsst.fink-broker.org/data/issues/)
lists missing fields, early missing forced photometry, object-association
problems and diffraction-spike artifacts. A complete pipeline must preserve
quality flags, deduplicate source identifiers, group association fragments using
a frozen rule, use signed fluxes, and make time scales explicit. No-data
responses must retain their provenance and stay distinct from service failures.

The [Rubin Science Platform alerts API](https://rsp.lsst.io/guides/api/alerts.html)
itself requires authentication. World-public broker alerts do not confer access
to every RSP image/catalogue product. No token, new account or full-stream
download was needed or attempted here.

## Exact next experiment if Rubin is selected

**M0-R: known-control completeness and quiescence audit.** Freeze the retrieved
API schemas and the three public history controls above. First obtain enough
metadata for the 49 discrepant detected epochs and 9 forced rows to distinguish
documented ingestion/quality/association policy from unaccounted loss. Compare
exact IDs, band mapping, time scale, flux and uncertainty fields; do not patch
around missing rows by inventing measurements.

Then freeze **ten catalogued southern CV controls** from a cited machine-readable
catalogue, selected by sky coverage and quiescent brightness before querying
their histories. The catalogue version, ordered list, exclusion reasons and
digest must be fixed first. Their event labels must come from independently
published historical observations, not from a peak chosen after looking at
Rubin. Reserve half the controls for validation of the episode/quality rules.

**Advance condition:** at least one independently documented target outburst
must be recovered with pre/post-event quiescence information and usable stamps;
all required control retrievals must either reconcile or have explicit, justified
coverage limitations. An unknown-source search then needs a separately frozen
small sky region/time window, completeness accounting and negative controls.
No population recall claim follows from merely recovering one outburst.

**Stop condition:** no covered target-family positive control, insufficient
quiescent measurements, unresolved history losses affecting the question, or an
enumerator that remains cap-bound/incomplete. Stop the unknown-search proposal
under any of those conditions; do not expand sky coverage to find a success.
The current exercise passes access checks but has not passed these science gates.

Estimated M0-R resources: one analyst day, fewer than 200 narrow HTTP queries,
under 500 MB retained data and under 4 GB RAM; no GPU or full alert stream.
These are budget caps/estimates, not measured production costs. If CCOR-2
recovers a confirmed comet and offers a distinct search opportunity, it has a
more direct path to an official identification. DR11 still requires a novelty
and diffuse-structure artifact check. Rubin should not displace either merely
because its API is fast; it first needs the target-specific control above.

## Reproduction and retained proofs

Exact responses, frozen request plans and executed scripts are under ignored
`tns-miner/data/probes/`. All **36 manifested files / 3,012,572 bytes** were
re-authenticated after retrieval. The offline comparison reads these files only;
it has no network or candidate-selection operation.

| Bundle | Manifest SHA-256 |
|---|---|
| `20260905_rubin_metadata` | `89c724d7645acda4084ff4bf4447bc4470a6830648eee465e21bce156d427802` |
| `20260905_rubin_access` | `f8b9c21b26c96588ec9c30a611ea1b3ca19ee694bd4f63bd370780b5040019da` |
| `20260905_rubin_tap` | `1a175e682a93616bf0e4b34c9cefa325cc3a9c2b58401714be41290bbc4e35e9` |

Offline comparison JSON SHA-256:
`da8d8345a1c96fe63e6c1c8af98cd426bfdad6ecbf2a0a0c6996ec524f4fc47e`.
Its script SHA-256 is
`bc67ad583b71e5b4effd296a7969176feae21e9c88130d2b6855198035d31a06`.

Commands from the repository root, with original immutable output directories:

```powershell
./tns-miner/.venv/Scripts/python.exe tns-miner/data/probes/rubin_20260905_metadata.py
./tns-miner/.venv/Scripts/python.exe tns-miner/data/probes/rubin_20260905_access.py
./tns-miner/.venv/Scripts/python.exe tns-miner/data/probes/rubin_20260905_tap.py
./tns-miner/.venv/Scripts/python.exe tns-miner/data/probes/rubin_20260905_compare.py
```

The first three refuse to overwrite their existing output directories. Their
source copies and exact API parameters are available inside each bundle for
review; the HTTP timeouts were 10 seconds connect / 30 seconds read, with no
retries. This research checked access and controls only. It did not create a
candidate hunt, claim a new discovery, publish a result or send a scientific report.
