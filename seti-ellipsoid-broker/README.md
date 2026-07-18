# SETI Ellipsoid Alert Broker

A standalone Python service that fuses transient alert streams — ZTF (via the **Lasair**
REST API), **ASAS-SN** Sky Patrol, and **CHIME/FRB** VOEvents — against the **SN 1987A SETI
Ellipsoid**, using **Gaia DR3** parallaxes (`astroquery.gaia` TAP) as its own distance layer.
It ranks ellipsoid-crossing candidates and exports amateur-facing observing lists. A second
**Window Predictor** mode proactively projects Gaia stars entering the SN 1987A shell into a
rolling forward calendar + iCal feed.

The motivation, prior-art landscape, MVP, and kill criteria are in **[SPEC.md](SPEC.md)**.
Exact endpoints/auth/limits/code per feed are in **[DATA-SOURCES.md](DATA-SOURCES.md)**.
Stack, architecture, milestones, and open questions are in **[BUILD-PLAN.md](BUILD-PLAN.md)**.

> **Status: M1 — offline core complete.** `seti-broker run` runs the *full* reactive
> pipeline offline (synthetic alerts → SQLite staging → real SN 1987A ellipsoid math →
> ranking → real CSV / ACP `.tgt` / Markdown artifacts), all deterministic and credential-free.
> The *live* ZTF (Lasair) + Gaia DR3 legs are gated behind `--live` and require a `LASAIR_TOKEN`
> plus network; the Window Predictor (`predict`) remains an M3 mock. See BUILD-PLAN.md.
> This is a desk/data/software project — no telescope or hardware required.

## Quickstart

```bash
# from the repo root
python -m venv .venv && . .venv/bin/activate    # (Windows: .venv\Scripts\activate)
pip install -e ".[dev]"

seti-broker run                 # REACT mode, OFFLINE: writes real artifacts from synthetic data
seti-broker run -o output       # choose the artifact directory (default: ./output)
seti-broker run --live          # live ZTF+Gaia (needs LASAIR_TOKEN + network; not in offline core)
seti-broker predict             # PREDICT mode: Window Predictor (M3 stub; prints a mocked row)
seti-broker version

pytest                          # run the test suite
```

`seti-broker run` (offline) stages synthetic alerts, computes crossings, ranks survivors, and
writes `output/ellipsoid_targets_YYYYMMDD.csv`, `…​.tgt`, and `ellipsoid_digest_YYYYMMDD.md`:

```
[M1 offline] SN 1987A ellipsoid broker | baseline d=51.4 kpc | ref epoch 1987-02-23
REACT mode (OFFLINE/synthetic) - full pipeline: alerts -> SQLite -> ellipsoid -> rank -> export

Staged 6 synthetic alert(s); 5 survived quality cuts and were ranked.

Top ranked ellipsoid-crossing target:
... ZTF26aaaaaab | ... | 985.8 | 2027.5 | 1.65 | 9 | 3.385

Artifacts written:
  csv: output\ellipsoid_targets_YYYYMMDD.csv
  tgt: output\ellipsoid_targets_YYYYMMDD.tgt
   md: output\ellipsoid_digest_YYYYMMDD.md
```

(You can also run without installing: `python -m seti_ellipsoid_broker.cli run`.)

## What this is / isn't

- **Is:** a self-contained, installable, public-API-first broker that carries its own Gaia DR3
  distance layer — the gap left open by the `eleanorgallay/alert_seti` research prototype.
- **Isn't:** a complete sky survey. ~90% of ZTF/Rubin stars lack usable Gaia parallaxes, so this
  is a *high-parallax-quality-star monitor*. The science window peaks ~2026–2028 (natural sunset).

## Layout

```
src/seti_ellipsoid_broker/
  cli.py        # typer entry point (run = offline pipeline; --live gated; predict = M3 mock)
  ellipsoid.py  # SN 1987A constants (real) + crossing math (real: S(t), crossing_epoch, window)
  ranking.py    # quality cuts + density bins + scoring (real) + M0 mock rows
  export.py     # CSV / ACP .tgt / Markdown digest (real, deterministic); VOTable = M2
  pipeline.py   # offline pipeline: synthetic alerts -> SQLite staging -> ellipsoid -> rank -> export
  models.py     # Alert / RankedTarget records
  config.py     # env-var settings (LASAIR_TOKEN, ...)
  gaia.py       # live astroquery.gaia crossmatch (stub; needs network; pairs with live Lasair)
  predictor.py  # (M3) Window Predictor + iCal (stub)
  ingest/       # lasair (live stub; needs LASAIR_TOKEN) / asassn (M2) / chime (M2-3)
```

## License

MIT.
