# CHIME/FRB Catalog 2 periodicity

Status: **M0 stopped at the observing-window gate on 2026-09-02. No unknown-source period scan was run.**

This project tests whether CHIME/FRB Catalog 2 can support a defensible search for long-period activity cycles among repeating fast radio bursts. The public event table is sufficient to reproduce a known period. The public exposure product is not sufficient to assign discovery significance because it contains date-integrated sky maps, not the time-resolved operational/sensitivity window.

## M0 result

| Gate | Result |
|---|---|
| Exact public inputs and digests | Pass |
| Published Catalog 2 counts | Pass |
| Recover FRB 20180916B's published 16.35-day activity period | Pass: 16.3256 days |
| Time-resolved observing window available in DOI products | **Fail** |
| Scan unknown repeaters | **Not run** |

The catalog contains 5,045 sub-burst rows representing 4,539 independent events, 3,641 sources, 83 repeaters, and 981 repeater events. After the frozen quality cuts, 14 repeaters have at least 10 clean active days. Their identifiers are deliberately not emitted because the required window-function gate failed.

## Reproduce

Install `requirements.txt`, download the two files named in `data/provenance.json` to their `local_path` values, and verify the recorded byte counts and SHA-256 digests. Then run:

```powershell
python -m unittest discover -s tests -v
ruff check scripts tests
python scripts/m0_audit.py --output out/m0-audit.json
```

`out/` and `data/raw/` are gitignored. The audit exits successfully when a scientific gate blocks the scan because that is an expected M0 outcome; the JSON `verdict` and `gates` fields carry the scientific status. Input corruption instead fails closed with exit code 1.

## What unblocks M1

M1 requires a citable, exact time series covering 2018-09-04 through 2023-09-15 that identifies when the FRB pipeline was operational and nominal, plus enough beam/transit information to compute each source's exposure versus time. A plot or cumulative exposure value is not adequate. Once that input exists, freeze its digest and write a new complete M1 preregistration before inspecting unknown-source periods. It must specify the null rate/clustering model, transit definition, full statistic/harmonic/variant family, global correction and alpha, tail estimator, exact alias widths, and baseline/cycle eligibility. Passing M0 can only mark the window input ready; the code deliberately cannot authorize a scan.

## Primary sources

- [Catalog 2 paper](https://arxiv.org/abs/2601.09399), journal DOI [10.3847/1538-4365/ae3828](https://doi.org/10.3847/1538-4365/ae3828)
- [Catalog 2 data DOI 10.11570/25.0066](https://doi.org/10.11570/25.0066)
- [Published 16.35-day activity period for FRB 20180916B](https://arxiv.org/abs/2001.10275)
