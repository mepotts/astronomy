---
title: 'adql-copilot: a schema-aware ADQL linter and validation gate for Virtual Observatory TAP endpoints'
tags:
  - Python
  - astronomy
  - virtual observatory
  - ADQL
  - TAP
  - Gaia
authors:
  - name: Matthew Potts
    orcid: 0000-0000-0000-0000  # TODO: add your ORCID before submission
    affiliation: 1
affiliations:
  - name: Independent researcher  # TODO: update affiliation
    index: 1
date: 18 July 2026
bibliography: paper.bib
---

<!--
DRAFT JOSS paper scaffold. Not yet submittable: fill ORCID/affiliation, confirm the
software meets JOSS's "substantial scholarly effort" bar (typically the NL->ADQL M2 layer
landed and a tagged release + archived DOI exist), and expand the references. JOSS body is
~250-1000 words; keep it tight.
-->

# Summary

Astronomical archives increasingly expose their holdings through the International Virtual
Observatory Alliance's Table Access Protocol (TAP), queried in the Astronomical Data Query
Language (ADQL) [@ADQL2.1]. ADQL is a constrained SQL dialect with astronomy-specific
geometry functions and per-archive quirks, and the usual feedback loop for a malformed query
is an opaque server-side error after a round trip. `adql-copilot` is a deterministic,
dependency-light Python tool that validates an ADQL query *before* it is sent: it parses the
query, resolves every table and column reference against the target endpoint's live
`TAP_SCHEMA`, and emits structured, machine-readable diagnostics — unknown tables/columns
(with did-you-mean suggestions), missing spatial constraints, missing row limits, and
archive-specific join pitfalls — together with a plain-English explanation.

# Statement of need

Interactive query editors such as TOPCAT [@TOPCAT] and the Gaia archive's web interface
already offer schema-aware editing for humans at a keyboard. What is missing is a
*programmatic, machine-readable* validation gate: a component that a notebook, a continuous-
integration check for a query cookbook, or — increasingly — a large language model (LLM)
generating ADQL from natural language can consume to catch errors deterministically. LLMs
readily hallucinate column names, mis-handle the `TOP n` versus `LIMIT` distinction, and
invent joins; a deterministic linter grounded in the real schema is the guardrail that makes
LLM-assisted query generation trustworthy. `adql-copilot` is built for exactly this seam: its
diagnostics carry stable codes and optional structured fix payloads, and its validation core
is deliberately separable from any LLM so that generation can be re-checked and retried
against ground truth.

The linter also encodes per-archive knowledge that the standard leaves implicit. For example,
Gaia's `TAP_SCHEMA` declares no foreign keys between its science tables, so a naive
"schema-declared join key" rule would flag every legitimate `source_id` join; `adql-copilot`
resolves joins against a curated per-archive key allowlist and a shared-column co-existence
check instead, and reports honestly when a query's identifiers could not be validated rather
than silently passing it.

# Functionality

- Parse ADQL and resolve identifiers against a cached-or-live `TAP_SCHEMA` (Gaia and other VO
  endpoints), with graceful fallback to a bundled offline fixture.
- Deterministic rules: unknown table/column, clause-aware spatial-constraint checking,
  aggregate-aware row-limit advice, and archive-aware join validation.
- Machine-readable `LintReport` (JSON) with stable diagnostic codes and optional structured
  fixes, designed to gate an LLM NL->ADQL loop (the M2 layer).

# Acknowledgements

This work uses the Gaia archive; Gaia data are processed by the Gaia Data Processing and
Analysis Consortium (DPAC).

# References
