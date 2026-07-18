"""adql-copilot — schema-aware ADQL linter/explainer over live VO TAP endpoints.

v0 (M0/M1) is a deterministic, no-LLM linter/explainer: parse an ADQL string, resolve its
table/column references against the live TAP_SCHEMA of a chosen endpoint, and emit diagnostics
plus a plain-English explanation. The NL->ADQL copilot (M2+) is layered on top and gated by
this same deterministic core. See SPEC.md / BUILD-PLAN.md.
"""

__version__ = "0.1.0"
