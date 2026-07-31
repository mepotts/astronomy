# M2 — vetting the 128

**Run date:** 2026-07-31 · **Report:** `m2-report.json` · **Verdict: GO, with the result read narrowly.**

M1 produced 128 ITF designations with acceptable orbit fits and *unknown* identification status.
M2 built the vetting layer that answers that question, and ran it.

**Nothing here is a discovery claim.** The output is a candidate list whose members are, at best,
*not identified as known objects by four catalogue services*. That is a much weaker statement than
"new", and the distinction is the entire point of this milestone.

---

## Controls — 7/7 pass, in the same run that produced the numbers

| Control | Expected | Identified | Best sep |
|---|---|---|---|
| `0073P-C` — the ITF designation Find_Orb recognised as comet 73P-C | 73P-C | **73P-C** | 32.842″ |
| (433) Eros [NEO] | 433 | **433** | 1.986″ |
| (7) Iris [inner main belt] | 7 | **7** | 0.893″ |
| (588) Achilles [Jupiter Trojan] | 588 | **588** | 0.261″ |
| (7) Iris via X05 Rubin, 2025 — *the candidate path* | 7 | **7** | 0.921″ |
| (433) Eros via W84 DECam, 2025 | 433 | **433** | 0.878″ |
| (588) Achilles via O18, 2025 | 588 | **588** | 0.122″ |

The 73P-C control is the load-bearing one: a known object sitting in the ITF, identified by a
completely independent route (Find_Orb reading a packed designation, not a catalogue query). Its
32.8″ separation is large because the astrometry is from April–May 2006, during the comet's
disintegration, and drifts from the catalogue ephemeris across the arc — that measured drift is what
calibrates `CONSIDER_ARCSEC`.

The three "candidate path" controls matter because they exercise the exact observatory codes and
epoch structure the real candidates use.

> ⚠️ **Process note.** The first full run reported 6/7 with 73P-C failing. That was an operator
> error, not a code defect: `vet-extract` was run with defaults, which regenerates the astrometry
> file for the 128 gate-passers only, and `0073P-C` is **not** among the 128 — it is in the 979
> fitted. The `--also` flag exists for exactly this. Re-run with `vet-extract --also 0073P-C`, the
> control passes and **every category count is unchanged**. Recorded because a control that can be
> silently starved of its input by a routine command is a trap worth documenting.

Incidental but reassuring: the MPC gates filtered the known comet out before it reached the 128.

---

## Result

| Category | Count |
|---|---|
| unmatched | **114** |
| ambiguous | 10 |
| known | 4 |

**Unmatched, by reason:**

| Reason | Count |
|---|---|
| `no_catalogue_object_near_astrometry` | **94** |
| `orbit_too_poorly_constrained` | 20 |

**The ≥2-epoch rule behaved exactly as designed** — the category boundary falls precisely on epochs
matched, with no overlap:

| Category | Epochs matched |
|---|---|
| unmatched (114) | 0 |
| ambiguous (10) | 1 |
| known (4) | 2 or 3 |

## Service coverage — the 94 are not a coverage artefact

| Services answering | Candidates |
|---|---|
| 3 | 110 |
| 2 | 18 |

Every candidate got at least two services to answer. For the 94, **75 had a catalogue neighbour
found and rejected on distance**: nearest neighbour ranged 30.6″–147.1″, median **90″**, with only
19 inside 60″. So the services were queried, they answered, they returned objects, and none was near
enough to identify. This is not silence from a broken query path.

Live service health this run: SkyBoT, MPChecker and SBDB served entirely from cache; SBIDENT made 10
live requests with 5 retries and 5 failures. No service was disabled, and coverage above confirms no
candidate was left under-evidenced.

---

## What 94 means, and what it does not

**It does not mean 94 new objects.** `no_catalogue_object_near_astrometry` is deliberately the
weakest claim the evidence supports. All of the following remain consistent with it:

- the object is genuinely uncatalogued;
- the object is known, but the fitted orbit — good enough to pass the MPC's gates — is still not
  precise enough to place it where a catalogue query recognises it;
- the object has been linked and designated by someone else *since* this ITF snapshot was taken.

There is also a structural reason to expect a high unmatched rate that has nothing to do with
discovery: **the ITF is, by construction, the observations that survey pipelines could not link.**
Failing to match a catalogue partly restates why the data is in the file at all.

**Composition warning:** 91 of the 128 carry the `RL` prefix (Rubin). A population that homogeneous
is more consistent with one survey's unlinked internal tracking than with a diverse set of
undiscovered objects.

## Next

1. **Do not submit anything.** No candidate here has been established as new.
2. **Use the snapshot delta chain as free validation.** The archive
   (`data/snapshots/`, running daily) records which observations leave the ITF. Any of these 128
   that disappear were linked by someone else — a direct, zero-cost test of whether "unmatched"
   meant "unknown". The first delta already caught 102 observations across 30 designations vanishing
   in a nine-hour window, so the signal rate is high enough to be useful quickly.
3. **Then linking**, per DISCOVERY/itf-linker.md M1 — pair→predict→confirm over the MJD > 60000
   slice. The vetting gate built here is what every future candidate runs through.
