# Independent-control feasibility - closed September 6

**6/6 pass the bounded coverage gate; no blind-search promotion.** This is the
first externally labelled stable-control sample here, not a century-scale truth
set or measured false-positive rate. [Specification](STABLE-SPEC-2026-09-06.md).

The literal no-comment parser selected zero stars because the publication uses
`---`. That zero result remains under `data/stable-20260906`; the
[recorded amendment](STABLE-PARSER-AMENDMENT-2026-09-06.md) preceded every new
DASCH curve. No selection or measurement threshold was tuned on the curves.

| Public standard | Clean detections | Span, years | Eligible years | Flagged years |
|---|---:|---:|---:|---|
| Feige 34 | 2,339 | 93.54 | 76 | none |
| Feige 66 | 1,590 | 90.21 | 70 | 1974 |
| HZ 44 | 1,601 | 99.01 | 70 | none |
| HILT 600 | 1,887 | 101.71 | 70 | none |
| Feige 67 | 2,297 | 98.93 | 75 | none |
| P177-D | 382 | 95.17 | 31 | none |

There are 10,096 clean detections and 392 eligible star-years, which are not
independent trials. All six identities are unique within 5 arcsec and catalogue/
lightcurve counts close. The normalized run used 14 requests, 7,208,535 response
bytes; the exact response ZIP is 2,588,927 bytes. The original two reference-file
requests are separate and retained. All raw response hashes/requests/times are in
[provenance](data/stable-normalized-20260906/provenance.json); the
[result](data/stable-normalized-20260906/results.json) cold-replays from the ZIP.

## Why the one alarm is not a discovery

The unchanged primary rule flags Feige 66's 1974 median by +0.6182 mag. A separately
labelled [post-hoc diagnostic](data/stable-normalized-20260906/flag-diagnostic.json)
finds four Damon North red and two blue plates. Red/blue medians are 10.8499/9.8215.
One red and one blue measurement carry the **same timestamp**, JD 2442094.844684,
but differ by 1.1282 mag. This is strong evidence of a band/calibration confound,
not a defensible single-band temporal excursion. It does not prove that all true
long-term variability is absent. Dropping red data leaves only two blue points:
the year becomes **insufficiently sampled**, not a quiet year. Keep the alarm.

[DASCH's own colour-term guide](https://dasch.cfa.harvard.edu/dr7/colorterms/)
documents this emulsion problem and recommends continuous colour terms over
series-only categories. The retained curve schema does not include those terms;
further work needs linked exposure-level calibration metadata. The
[published control labels](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/MNRAS/462/3616)
come from short observing runs; they cannot establish century-scale constancy.

**Decision:** retain this as a successful access/coverage pilot, but do not expand
to 120 stars or rank unknown objects with the current statistic. The next coherent
experiment is an emulsion-aware, matched-control calibration study with its own
held-out fields and period-appropriate stability labels. It is not a dated gate;
it is additional experimental work, deliberately not claimed completed here.

```powershell
python dasch-pilot/scripts/stable_controls.py --replay
python dasch-pilot/scripts/stable_controls.py --replay --normalize-missing-notes
python -m unittest discover -s dasch-pilot/tests -v
```

26 offline tests pass. No images, unknown stars or scientific submissions fetched
or produced in this extension.
