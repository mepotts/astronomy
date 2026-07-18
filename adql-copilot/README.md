# adql-copilot

Schema-aware **ADQL linter / explainer** over live Virtual-Observatory **TAP** endpoints
(Gaia, VizieR, MAST, DESI) — with a natural-language **NL→ADQL copilot** layered on top later.

**What ships first (v0):** a deterministic, *no-LLM* tool. Give it an ADQL string; it parses it,
resolves every table/column reference against the **live `TAP_SCHEMA`** of your chosen endpoint,
and reports problems — unknown table/column (with "did you mean?" from the real schema), missing
JOIN keys, and the classic footgun of a positional query with **no spatial constraint** (a
full-catalog scan) — plus a plain-English explanation. It is correct by construction because it
asserts nothing the live schema doesn't confirm. The LLM copilot (NL→ADQL) is added afterward and
is *gated by this same linter*. See [`SPEC.md`](SPEC.md), [`DATA-SOURCES.md`](DATA-SOURCES.md),
and [`BUILD-PLAN.md`](BUILD-PLAN.md).

> Not to be confused with **STILTS-NLI** (arXiv 2602.22357), which does NL→local table-ops.
> This is schema-validated **ADQL over live TAP endpoints** — a different layer of the stack.

## Status

**M1 — deterministic linter against live Gaia (shipping).** Real ADQL parsing
(`queryparser-python3`, `lark` fallback), live `TAP_SCHEMA` resolution for Gaia (cache → live →
offline fixture), and the four always-correct lint rules — unknown table/column (with "did you
mean?"), missing JOIN key (vs declared foreign keys), no-spatial-constraint full-scan warning, and
no-`TOP` row-limit advisory — plus a schema-grounded plain-English explanation. No LLM. The
NL→ADQL `ask` command is **M2** (not yet implemented).

## Quickstart

```bash
# from the repo root
python -m venv .venv && .venv\Scripts\activate     # Windows (PowerShell: .venv\Scripts\Activate.ps1)
# source .venv/bin/activate                          # macOS/Linux
pip install -e .

# lint the built-in demo query (valid ADQL, but no spatial constraint / no row limit)
adql-copilot lint

# lint your own ADQL string
adql-copilot lint "SELECT source_id, ra, dec FROM gaiadr3.gaia_source WHERE ruwe < 1.4"

# machine-readable
adql-copilot lint --json

# list the supported public TAP endpoints
adql-copilot endpoints
```

All target endpoints are **public/anonymous — no account or key needed.** (The NL→ADQL `ask`
command is M2 and not yet implemented.)

## Layout

```
src/adql_copilot/
  cli.py        # typer CLI: lint / endpoints / (ask = M2)
  parser.py     # ADQL parse + identifier extraction (queryparser; lark fallback)
  schema.py     # TAP_SCHEMA resolver: cache -> live (pyvo) -> offline fixture
  linter.py     # the four deterministic lint rules over (parse, schema) -> diagnostics
  explainer.py  # schema-grounded plain-English query summary
  generate.py   # NL->ADQL generator, schema-grounded + linter-gated (M2)                [STUB]
  models.py     # pydantic: Diagnostic / ParsedQuery / ColumnMeta / Schema / LintReport
  endpoints.py  # the 4 verified public TAP base URLs
  fixtures/     # committed offline TAP_SCHEMA snapshots (gaia.json) for no-network use
```

## Dev

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT.
