"""NL -> ADQL generation (M2+, LLM). NOT active in v0.

The generator is the least-trusted component: it only ever sees the live schema slice (real
table/column names + UCDs) for the chosen endpoint, and whatever it emits is re-run through
parser -> schema resolver -> linter before any execution (see BUILD-PLAN S6). Provider is
pluggable behind this one function; default plan is the Claude API (model id chosen at M2 against
the then-current model list, never hardcoded here).
"""

from __future__ import annotations

from .models import ColumnMeta


def generate_adql(nl: str, schema: list[ColumnMeta], endpoint_key: str) -> str:
    """Turn a natural-language request into a grounded ADQL string.

    NOT IMPLEMENTED in v0 — the deterministic linter/explainer ships first and is the harness
    that validates whatever this returns.
    """
    raise NotImplementedError(
        "NL->ADQL generation is M2. v0 is the deterministic schema-aware linter/explainer; "
        "use `adql-copilot lint` with a hand-written ADQL string."
    )
