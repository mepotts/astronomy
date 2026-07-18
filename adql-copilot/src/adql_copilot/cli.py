"""adql-copilot CLI (typer).

`adql-copilot lint` runs the deterministic M1 pipeline on a supplied (or built-in demo) ADQL
string: parse (queryparser) -> resolve against the endpoint's live TAP_SCHEMA (cache -> live ->
offline fixture) -> lint (4 always-correct rules) -> plain-English explanation. No LLM. The
NL->ADQL `ask` command is M2.
"""

from __future__ import annotations

import logging

import typer
from rich.console import Console

from . import __version__, explainer, linter, parser, schema
from .endpoints import DEFAULT_ENDPOINT, ENDPOINTS
from .models import LintReport, Schema, Severity

app = typer.Typer(add_completion=False, help="Schema-aware ADQL linter/explainer (NL->ADQL copilot to come).")
console = Console()

# A representative, intentionally-imperfect query used when none is supplied:
# valid ADQL but with NO spatial constraint and NO row limit -> exercises the demo rules.
_DEMO_ADQL = (
    "SELECT source_id, ra, dec, parallax, ruwe\n"
    "FROM gaiadr3.gaia_source\n"
    "WHERE parallax_over_error > 10 AND ruwe < 1.4"
)

_SEV_STYLE = {Severity.ERROR: "bold red", Severity.WARNING: "yellow", Severity.INFO: "cyan"}


def _run_pipeline(adql: str, endpoint_key: str, *, refresh: bool = False) -> tuple[LintReport, Schema]:
    sch = schema.load_schema(endpoint_key, refresh=refresh)
    parsed = parser.parse(adql)
    diags = linter.lint(parsed, sch, endpoint_key)
    text = explainer.explain(parsed, sch)
    report = LintReport(endpoint_key=endpoint_key, parsed=parsed, diagnostics=diags, explanation=text)
    return report, sch


_SOURCE_NOTE = {
    "live": "live TAP fetch",
    "cache": "cached schema",
    "fixture": "offline fixture (live TAP unavailable)",
}


@app.command()
def lint(
    query: str = typer.Argument(None, help="ADQL string to lint. Omit to use the built-in demo query."),
    endpoint: str = typer.Option(DEFAULT_ENDPOINT, "--endpoint", "-e", help=f"One of: {', '.join(ENDPOINTS)}"),
    as_json: bool = typer.Option(False, "--json", help="Emit the LintReport as JSON."),
    refresh: bool = typer.Option(False, "--refresh", help="Force a live TAP_SCHEMA fetch (bypass cache)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Log schema-source details to stderr."),
) -> None:
    """Parse, resolve against the live TAP schema, and lint an ADQL query."""
    if endpoint not in ENDPOINTS:
        raise typer.BadParameter(f"unknown endpoint {endpoint!r}; choose from {list(ENDPOINTS)}")
    if verbose:
        # Scope logging to our own loggers only: queryparser chats on the root logger at INFO,
        # which would otherwise drown the schema-source message in ANTLR walker internals.
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        pkg_logger = logging.getLogger("adql_copilot")
        pkg_logger.setLevel(logging.INFO)
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False

    adql = query or _DEMO_ADQL
    report, sch = _run_pipeline(adql, endpoint, refresh=refresh)

    if as_json:
        console.print_json(report.model_dump_json())
        raise typer.Exit(code=0 if report.ok else 1)

    ep = ENDPOINTS[endpoint]
    src = _SOURCE_NOTE.get(sch.source, sch.source)
    console.rule(
        f"adql-copilot v{__version__}  ·  endpoint: {ep.name}  ·  "
        f"schema: {len(sch.tables)} tables / {len(sch.columns)} cols  ·  [dim]{src}[/dim]"
    )
    console.print("[bold]Query:[/bold]")
    console.print(adql, style="dim")
    console.print("\n[bold]Explanation:[/bold]")
    console.print(report.explanation)
    console.print("\n[bold]Diagnostics:[/bold]")
    if not report.diagnostics:
        console.print("  (none)", style="green")
    for d in report.diagnostics:
        style = _SEV_STYLE.get(d.severity, "white")
        console.print(f"  [{style}]{d.severity.value.upper():7}[/{style}] {d.code}: {d.message}")
        if d.suggestion:
            console.print(f"          -> {d.suggestion}", style="dim")
    console.print(f"\n[bold]Result:[/bold] {'OK (no errors)' if report.ok else 'has errors'}")
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def ask() -> None:
    """[M2 — not yet implemented] Natural language -> grounded, lint-checked ADQL."""
    console.print("[yellow]`ask` (NL->ADQL) is M2.[/yellow] v0 ships the deterministic linter; use `lint`.")
    raise typer.Exit(code=2)


@app.command()
def endpoints() -> None:
    """List the supported public TAP endpoints."""
    for ep in ENDPOINTS.values():
        console.print(f"[bold]{ep.key}[/bold]  {ep.name}\n  {ep.tap_url}\n  [dim]{ep.note}[/dim]")


if __name__ == "__main__":
    app()
