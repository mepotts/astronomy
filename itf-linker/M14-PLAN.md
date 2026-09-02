# M14 — Anatomy-first processing of the 2026-08-19/24 Rubin batches

**Prospectively written internal plan:** recorded as 2026-09-02 before either aggregate
was downloaded or inspected, but not independently timestamped or committed before the
outcome. “Frozen” below describes the intended internal contract, not a public
preregistration.
**Status recorded at internal freeze:** inputs identified by public object metadata only; no anatomy,
sweep, decoy, or fit outcome seen. **Nothing in M14 submits or publishes anything.**

## Question

Do the two new canonical Rubin/MPC replica aggregates contain useful unnumbered objects,
and do current orbit solutions for those objects produce a fit-grade excess over the
existing half-period decoy when swept against one frozen current ITF generation?

Byte size is not evidence of a designation batch. M9 found a 100 MB aggregate that was
99.4% numbered-object bookkeeping, so the input gate and anatomy report run before any
orbit selection or scientific interpretation.

## Frozen input contract

1. The only batch inputs are the exact canonical objects
   `2026-08-19/parquet/obs_sbn_X05_2026-08-19.parquet` and
   `2026-08-24/parquet/obs_sbn_X05_2026-08-24.parquet` in the public
   `asteroid-institute-public` bucket. Each download must match the GCS generation, byte
   count, MD5, ETag, CRC32C metadata, and a locally computed SHA-256. Nested generation
   shards and any other path are ineligible.
2. Both Parquets must be nonempty and carry `provid`, `permid`, `obstime`, `created_at`,
   and `disc`. The anatomy report records observation counts, numbered/unnumbered split,
   distinct unnumbered objects, discovery asterisks, time spans, and designation-year
   counts without exposing object identifiers.
3. The MPCORB corpus must be at least 100 MiB, carry a valid ETag and content length, and
   have an HTTP `Last-Modified` time strictly later than both authenticated GCS object
   update times. HEAD and GET metadata must agree; its complete bytes receive SHA-256.
4. The ITF input is one named daily archive generation. Its archived raw `itf.txt.gz` is
   copied and reparsed into a run-local full astrometric Parquet. Raw and Parquet counts,
   hashes, archive manifest, parser source, and required columns form one fingerprint.
   The mutable developer checkout files are not run inputs.
5. M8, M9, M10-shell, and M11-deep ledgers are read-only inputs. Their SHA-256 digests
   enter the run contract.

Any missing sidecar, stale corpus, changed generation, digest mismatch, malformed or empty
response, partial input pair, or accounting residue stops the run. No cache without a
matching request and content proof may stand in for a live result.

## Orbit population and candidate deduplication

Every distinct unnumbered object in the two batches is resolved against the fresh corpus.
Objects seen in an earlier milestone are deliberately retained: a newer orbit and newer ITF
can yield a new tracklet pair. Current aliases collapse to one primary orbit. MPCORB misses
may use the read-only `get-orb` endpoint at at least 1.1 seconds between requests, capped at
2,000 misses; a larger miss set is treated as a broken parse and stops before API fallback.

Only U ≤ 6 orbits enter the sweep. After the real sweep, a candidate is removed if any
current alias plus its `link_key` already occurs in a prior ledger. A prior use of the same
tracklet under a different orbit is retained and explicitly labelled for adjudication; it
is not silently treated as either a duplicate or a discovery.

## Frozen scientific method

- Perturbed propagation, Sun plus eight planets, RK4 one-day nodes with dense Hermite
  interpolation: M8 implementation unchanged.
- Lookback: 0–15 years only, the M8 calibrated range.
- Gate: 120 arcsec floor + 1.5 × the monotonic M8 perturbed envelope + unchanged U-runoff.
- Rate and magnitude gates: M8 values unchanged.
- Control: the identical sweep with every orbit shifted by half a period.
- Ranking: encounter flag, then separation divided by gate radius, with deterministic
  orbit/key tie breaks.

## Fit rule

Find_Orb tags use the new seven-character `mEa####`/`mEb####` namespace. Published object
astrometry is fetched into a new request-bound, content-hashed cache. Tracklet lines are
extracted only from the frozen raw ITF paired to the sweep Parquet.

Fits run in tranches of 100, at most 400 total and at most 90 minutes in the initial run.
Before beginning each new tranche, stop if the preceding 100 contain fewer than 20 strict,
fully-used fits. The hard cap, time cap, queue exhaustion, or stopping rule—whichever comes
first—is reported. Missing frozen tracklet lines, missing/malformed published astrometry,
or another proof failure stops closed; the affected row cannot become a PASS.

The coarse sweep always completes before fitting begins. No radius, U threshold, window,
rank, fit gate, or stopping threshold may be changed in response to the outcomes.

## Private outputs and decision boundary

All identifier-bearing batches, orbit tables, API caches, checkpoints, matches, and fits
live below gitignored `data/m14/`. A separate aggregate summary contains counts only. No
M13 payload is built. No MPC account action, submission, publication, email, issue, release,
or candidate-identifier commit is permitted by this milestone.

An aggregate excess and passing fits are evidence for a private human review queue, not a
discovery claim. Alternate-orbit collisions, conflict-service vetting, fresh liveness, and
human examination remain required before any separately authorized submission decision.
