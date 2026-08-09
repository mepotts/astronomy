# Snapshot validation — the linker checked against other people's work

**Re-derived 2026-08-06** from the committed delta chain. Regenerate with the query in §4;
the numbers grow as the archive accumulates and this document should be re-run, not trusted.

M2 identified the snapshot archive as free validation, and this is that test performed. It
is the only check in the project that is **independent of everything the pipeline does** —
no orbit fit, no catalogue query, no gate. It asks one question:

> Of the tracklet groupings M3 proposed, how many did *somebody else* independently link?

The ITF holds observations no survey pipeline could link. When someone links them, they
leave the file. So an M3 link whose **every member tracklet has since departed** is a
grouping the world independently agreed with.

---

## 1. Result

| | |
|---|---:|
| Departed observations across the chain | **30,751** |
| Distinct departed designations | 8,598 |
| M3 gated links touching a departed tracklet | 171 |
| **Links where every member departed** | **21** |
| …of those, **cross-observatory** | **14** |

> **Re-run 2026-08-09: 26 complete, 16 cross-observatory.** The archive has three more days
> in it; the table below is still the 2026-08-06 set. As the header says, re-run rather than
> trust.
>
> **The "every member tracklet has since departed" claim was also checked at a stricter
> granularity, and it holds.** §4's query takes `.unique()` on `desig`, so a trkSub counts as
> departed once *any one* of its observations leaves — which is weaker than the sentence
> above promises. Recomputed so that a member counts only when **no** observation of it
> survives in the current key set: **26 complete, 16 cross-observatory — identical**. Of
> 17,680 trkSubs with a departed observation, 17,596 are gone entirely, and not one of the
> remaining 84 appears in a complete link. The stronger query is in §4.

Fourteen of the twenty-one join tracklets from **different telescopes** — F51+O18,
F52+V00, F52+W84, F52+G96, N94+V00, O18+X09, and one three-site F51+G96+O18. Those are
associations no single survey is positioned to make, proposed from positions and epochs
alone, and subsequently made by someone else.

| link | members | observatories | nights |
|---|---:|---|---:|
| `lnk00do` | 4 | F51 + O18 | 4 |
| `lnk012i` | 3 | F51 + G96 + O18 | 3 |
| `lnk03lt` `lnk03px` `lnk03q2` `lnk03sw` `lnk05zi` | 3 | F52 + V00 | 3 |
| `lnk03m6` | 3 | F52 + W84 | 3 |
| `lnk04wr` | 3 | F52 + G96 | 3 |
| `lnk05ca` | 3 | N94 + V00 | 3 |
| `lnk00dm` `lnk03l1` `lnk08t8` | 2 | F51 + O18 | 3–4 |
| `lnk03yk` | 2 | O18 + X09 | 3 |
| `lnk09xt` `lnk0aw7` `lnk099e` `lnk09ol` `lnk09xj` `lnk0cty` | 1–3 | single site | 3–4 |

## 2. Two of them close a three-way loop

`lnk00do` and `lnk00dm` are the same links M3's vetting resolved to **2026 OB4** and
**2026 DK65**, at 0.536″ and 0.693″ across every epoch queried.

So three methods, with different data and different failure modes, agree on the same two
objects:

1. **The linker** grouped tracklets from different observatories on geometry alone.
2. **Catalogue vetting** matched the fitted orbit to a designated minor planet at
   sub-arcsecond separation, against an orbit computed by someone else.
3. **The archive** recorded those exact observations leaving the ITF.

None of the three could produce that agreement by accident, and no two of them share a
mechanism that could produce it jointly.

## 3. What this does and does not establish

**Establishes:** the linker assembles *real objects*. A chance cluster does not get
independently linked by a third party and does not match a catalogued orbit. This is the
strongest evidence in the project that M3's proposals are physical rather than statistical.

**Does not establish:** that any survivor is *new*. Every one of the 21 is, by
construction, a grouping somebody else also made — which is the opposite of a discovery.
The result validates the method, not the yield.

**Does not give a rate.** 21 of 13,618 gated links is not a precision estimate. The
archive covers eight days against a file spanning 1995–2026, so it samples only links
whose members happened to be linked by others during that window. The true agreement rate
is unknown and this number is a floor.

## 3a. What the gates did to the confirmed links — the guard's first measured false-rejection rate

`HANDOFF.md` §4 names this the sharpest weakness in the publishable finding: *"The guard's
false-rejection rate is measured nowhere. '84.4% rejected' is not '84.4% were wrong'."* The
links above are the first ground truth the project has had — somebody else agreed with them,
without any fit, catalogue query or gate of ours. So: find them in a completed run and ask
what each gate did.

All 26 appear in the M4-new run (28 outcome rows — a member set can form more than one
link). Reproduce with `scripts/guard_vs_confirmed.py`, which matches on **member trkSubs and
never on `desig`**, because link ids are positional and mean different things in different
tables.

| | of 28 fitted rows |
|---|---:|
| Converged | 26 |
| Passed every gate in the run | 6 |
| Kept by our post-fit gate | 6 |
| **Kept by the MPC's published rule** | **14** |
| **Rejected by the subset guard alone** | **0** |

**The guard did not falsely reject anything.** Not once did it discard a confirmed link that
would otherwise have been kept: every confirmed link it flagged was already failing σ or RMS.
Its false-rejection rate against ground truth is **0 of 26**. That is the number the RNAAS
draft could not previously quote, and it is favourable.

**Our acceptance gate is the thing rejecting confirmed links, not the guard.** It discards 22
of the 28 — 62 σ failures and 12 RMS failures — for links the world independently confirmed
are real. The MPC's published rule keeps **14**, more than twice as many, because its RMS
condition is one conjunct rather than a ceiling (see `M5-RESULTS.md` §5.3). This is the
A-series gate finding measured against ground truth instead of argued.

**Two caveats, both real.** *n* = 26 is small, and one clean number is not a rate with an
error bar on it. More importantly the sample is **biased toward easy links**: these are
exactly the associations somebody else was able to make, so they are plausibly better
conditioned than the general population, and a guard that never rejects an easy link may
still reject hard ones wrongly. What this establishes is a floor — the guard is not
indiscriminate — not that its false-rejection rate is zero in general.

---

## 4. Regenerating this

```python
import polars as pl, pathlib
root = pathlib.Path("data/snapshots")
deps = [pl.read_parquet(d / "delta.parquet").filter(pl.col("change") == -1)
        for d in sorted(root.iterdir()) if (d / "delta.parquet").exists()]
departed = set(pl.concat([d for d in deps if len(d)])["desig"].unique().to_list())

links = pl.read_parquet("data/link-candidates.parquet").filter(pl.col("link_pass"))
complete = [r for r in links.iter_rows(named=True)
            if (m := set(r["source_desigs"])) & departed == m]
print(len(complete), sum(1 for r in complete if r["cross_observatory"]))
```

The query above is the weak form: `departed` is every trkSub with *at least one* departed
observation. To test what the claim actually says — that nothing of the member is left —
require that no observation of it survives in the newest key set:

```python
newest = sorted(d for d in root.iterdir() if (d / "observations.parquet").exists())[-1]
surviving = set(pl.scan_parquet(newest / "observations.parquet")
                  .select("desig").collect()["desig"].unique().to_list())
gone = departed - surviving          # departed, and nothing of it left behind
strict = [r for r in links.iter_rows(named=True)
          if (m := set(r["source_desigs"])) and m <= gone]
print(len(strict), sum(1 for r in strict if r["cross_observatory"]))
```

Both forms give the same answer as of 2026-08-09 (26 / 16). Run the strict one: it is the
one that matches the sentence in the header, and it costs one extra parquet read. It needs a
snapshot that still retains its key set — `FULL_KEEP` keeps the newest three.

⚠️ **Departure means somebody linked the tracklet. It does not date the designation.** A
packed designation encodes the discovery half-month, not when a designation was issued —
an error made and corrected in `M4-RESULTS.md` §6.6. Do not infer timing from this.

## 5. Provenance note

An earlier run of this analysis (2026-08-05) found **16** complete links, 11
cross-observatory. The increase to 21 and 14 is not new observations arriving: it is the
recovery of the 2026-08-04 → 2026-08-06 delta, which had been silently written as empty
when the parent key set was unavailable. That bug and its fix are recorded in
`src/itf_linker/snapshot.py` and `tests/test_snapshot_delta_status.py`. **Five confirmed
groupings were invisible for a day because of it**, which is the concrete cost of a
silent failure in an archive that cannot be rebuilt.
