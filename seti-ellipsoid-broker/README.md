# SETI Ellipsoid Alert Broker

A standalone Python service that fuses transient alerts against the **SN 1987A SETI
Ellipsoid**, using **Gaia DR3** parallaxes (`astroquery.gaia` TAP) as its own distance layer.
It ranks ellipsoid-crossing candidates and exports amateur-facing observing lists.

The motivation, prior-art landscape, MVP, and kill criteria are in **[SPEC.md](SPEC.md)**.
Exact endpoints/auth/limits/code per feed are in **[DATA-SOURCES.md](DATA-SOURCES.md)**.
Stack, architecture, milestones, and open questions are in **[BUILD-PLAN.md](BUILD-PLAN.md)**.

> **Status — offline core complete + a live, account-free path.**
>
> * **Offline core: complete and numerically correct.** The SN 1987A ellipsoid math is real
>   and **externally validated** — it reproduces the published crossing epochs of *all 217*
>   SN 1987A SETI-Ellipsoid targets in Nilipour et al. (2023), AJ 166, 79, to within
>   ~5×10⁻⁴ yr (see `tests/test_nilipour.py`). Ranking and the deterministic CSV / ACP
>   `.tgt` / Markdown exporters are real. `seti-broker run` runs the whole thing offline on
>   synthetic data, credential-free.
> * **Live, account-free path: works now.** `seti-broker run --transients-csv PATH` takes an
>   alert list exported from *any* broker (or your own), crossmatches it against **anonymous**
>   Gaia DR3 TAP (no token), applies the **Gaia DR3 parallax zero-point correction**
>   (Lindegren et al. 2021) before inverting distance, then runs the full ellipsoid → rank →
>   export pipeline. This is the supported way to run live.
> * **Still stubs.** `--live` (Lasair ZTF *auto*-ingest) is **account-gated** and exits 2 —
>   Lasair-ZTF accounts don't carry into the Rubin era, so most users can't get a token; use
>   `--transients-csv` instead. ASAS-SN and CHIME auto-ingest, and the Window Predictor
>   (`predict`), remain stubs. See DATA-SOURCES.md / BUILD-PLAN.md.
>
> Desk/data/software project — no telescope or hardware required.

## Quickstart

```bash
# from the repo root
python -m venv .venv && . .venv/bin/activate    # (Windows: .venv\Scripts\activate)
pip install -e ".[dev]"

# LIVE, ACCOUNT-FREE (the happy path): your CSV -> anonymous Gaia DR3 + zero-point -> artifacts
seti-broker run --transients-csv examples/transients_example.csv

seti-broker run                 # OFFLINE demo: real artifacts from deterministic synthetic data
seti-broker run -o output       # choose the artifact directory (default: ./output)
seti-broker run --now 2026.5    # pin the reference "now" (else: current time) for reproducibility
seti-broker run --transients-csv my.csv --no-zeropoint   # diagnostics: skip the zero-point
seti-broker run --live          # Lasair ZTF auto-ingest: ACCOUNT-GATED, exits 2 (use --transients-csv)
seti-broker predict             # PREDICT mode: Window Predictor (stub; prints a mocked row)
seti-broker version

pytest                          # run the OFFLINE test suite (network-free; live Gaia test is skipped)
```

The `--transients-csv` file needs only `name,ra,dec` columns (optional
`gaia_source_id,mjd/discovery_date,survey,mag`); see
[`examples/transients_example.csv`](examples/transients_example.csv) and the schema in
`src/seti_ellipsoid_broker/ingest/transients.py`. Each run writes
`ellipsoid_targets_YYYYMMDD.csv`, `…​.tgt`, and `ellipsoid_digest_YYYYMMDD.md` — including a
`crossing_now` flag (star on-shell within its own crossing window right now).

```
[offline] SN 1987A ellipsoid broker | baseline d=51.4 kpc | ref epoch 1987-02-23 | now=2026.545
REACT mode (OFFLINE/synthetic) - full pipeline: alerts -> SQLite -> ellipsoid -> rank -> export

Staged 6 synthetic alert(s); 5 survived quality cuts and were ranked.

Top ranked ellipsoid-crossing target:
... ZTF26aaaaaab | ... | 985.8 | 2027.5 | 1.65 | True | 9 | 3.45
```

(The score tracks the current date because "now" is clock-coupled; pass `--now` to pin it.
You can also run without installing: `python -m seti_ellipsoid_broker.cli run`.)

## What this is / isn't

- **Is:** a self-contained, installable broker that carries its own Gaia DR3 distance layer
  (with the DR3 parallax zero-point correction) — the gap left open by the
  `eleanorgallay/alert_seti` research prototype — and runs live **without any broker account**.
- **Isn't:** a complete sky survey. ~90% of ZTF/Rubin stars lack usable Gaia parallaxes, so this
  is a *high-parallax-quality-star monitor*. The science window peaks ~2026–2028 (natural sunset).

## Layout

```
src/seti_ellipsoid_broker/
  cli.py        # typer entry point (run: --transients-csv live / offline synthetic / --live gated)
  ellipsoid.py  # SN 1987A constants (real) + crossing math (real; validated vs Nilipour 2023)
  zeropoint.py  # Gaia DR3 parallax zero-point correction (real; Lindegren et al. 2021)
  gaia.py       # live anonymous astroquery.gaia DR3 crossmatch (real; injectable launcher)
  ranking.py    # quality cuts + density bins + scoring (real) + M0 mock rows
  export.py     # CSV / ACP .tgt / Markdown digest (real, deterministic); VOTable = M2
  pipeline.py   # staging -> ellipsoid -> rank -> export; offline synthetic + live CSV entry points
  models.py     # Alert / RankedTarget records
  config.py     # env-var settings (LASAIR_TOKEN, ...)
  predictor.py  # (M3) Window Predictor + iCal (stub)
  ingest/       # transients (live CSV, real) / lasair (account-gated stub) / asassn, chime (stubs)
```

## License

MIT.
