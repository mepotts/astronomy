# M15 stage A — offline observation-identity engineering

2026-09-12. **Prototype verified; real-fit integration HOLD. No discovery campaign.**

This separately named repair addresses M14-RESULTS section 6, items 3–6. It does
not reopen M14, reinterpret its 0–2/100 noninferential diagnostic, change any
historical fit/result/queue, or repair every prerequisite for a future campaign.
No network science, Find_Orb execution, scheduling, notification change, or
submission occurred. The global reusable kit was not present; the existing ITF
handoff constraints, separate files, synthetic tests and explicit HOLD boundary
govern this small engineering stage.

## Implemented contract

`scripts/m15_identity.py` is a dependency-free prototype, not imported by any
historical or daily runner. `tests/test_m15_identity.py` contains synthetic data.

- Strict OBS80 ingestion supports only complete ASCII single-line C/B optical
  records. Each occurrence retains the complete source-file SHA-256, physical
  1-based row number, line SHA-256, Decimal JD/observed coordinates, original
  time/coordinate quantization, station, note1, note2 and discovery marker.
  Source hashes are caller-supplied; a future driver must authenticate the actual
  complete source bytes. Unsupported two-line types HOLD, never disappear.
- Semantic exact published duplicates are rejected before a fit; different
  designations, spelling or trailing decimal zeros do not make a new observation.
  This is an exact identity check, not a replacement for broader publication,
  alternative-orbit or scientific duplicate vetting.
- The complete published-plus-appended input is compared with the complete
  residual output, not a station/time-selected subset. Input multiplicity must
  equal output multiplicity. Used and unused residuals both require provenance.
- Compatibility uses station and all note fields, plus independently verified
  export-error bounds for JD and observed RA/Dec. There is no nearest-neighbor
  tie break, input-order association, or astrophysical matching radius.
- Each input must have exactly one compatible residual, no residual can be
  consumed twice, and every residual must be consumed. Repeated equal-time rows
  with distinct positions can match; indistinguishable repeated occurrences HOLD.
  This intentionally conservative graph criterion also HOLDs some graphs that
  have a unique *global* perfect matching but locally multiple candidates.
- `MATCHED` measures identity/inclusion only, not orbit quality or discovery.
  Successful counts obey `0 <= used <= appended_total`. HOLD and already-published
  outcomes return `used=None`, not a misleading zero. Missing fields, nonfinite
  numbers, binary floats that lost lexical precision, implicit inclusion flags,
  unmatched residuals and ambiguous maps all HOLD.

An `ExportContract` requires a retained evidence hash and asserted UTC/observed
J2000-degree semantics, verbatim notes, complete row emission and separate
Decimal error bounds. The prototype caps JD error at 1e-6 **day** and RA/Dec
error at 1e-6 **degree**: small engineering scope limits, not equal physical
tolerances or a statement that the archive is invalid. These permit a future
proof of six-decimal rounding, but that proof is not assumed. Bounds are supplied
by a verified exporter, never estimated by fitting residual matches. The evidence
hash alone does not authenticate its contents; the future driver must do so.

## Retained-file compatibility audit (read-only)

The audit inspected `data/m14/runs/20260902T062614Z/fits`:

| Quantity | Result |
|---|---:|
| Retained total.json files, including baseline and joint products | 192 |
| Paired obs.txt files | 192 |
| Serialized residual rows | 18,305 |
| Rows carrying JD/RA/Dec, station, both notes, discovery marker and incl | 18,305 |
| Decimal places in every serialized JD/RA/Dec | 6 / 6 / 6 |
| Scientific rows regraded | **0** |

All inclusion fields are JSON integers; note fields are strings. No original
source-row token is present. No identifiers, coordinates, or filenames from the
private corpus were emitted. The aggregate manifest SHA-256 is
`ab630172478d9eab5af1f37a6e8f4bac0b58aff00f2be74d0afae36fd911aa83`.
It binds 384 sorted `(relative path, file SHA-256)` entries using compact JSON
serialization. It is an engineering audit anchor, not prospective science proof.

Six decimal places alone do not establish a safe round-trip error bound. The
missing token is not inherently fatal: full-field, verified-rounding compatibility
may prove uniqueness. Ambiguous rows still require HOLD.

## Read-only local exporter source check and exact next proof

Existing WSL source is available at `/home/matth/find_orb`, revision
`143c8233e78368505f1b08e7a917be5841ba65f6`. Tracked source showed no modifications;
untracked build files `PREFIX` and `prefix.h` are present. Both source-tree `fo`
and `/home/matth/bin/fo` currently hash to
`a9a83d3ed9a1cfc2afde5b582da0be834d20a80f0826505e7c92fad5e14a4f4d`.
No binary was executed or rebuilt.

`elem_out.cpp` lines 1122–1198 show `utc_from_td`, `%.6f` JD and RA/Dec
serialization, notes, and `is_included`. Crucially, `mpc_obs.cpp` lines 2990–3034
sort/remove or reconcile duplicates; lines 3853–3856 conditionally subtract
astrometric debias corrections from the stored RA/Dec that the JSON writer emits.
Thus raw-coordinate equality and complete input-row emission cannot simply be
asserted from the JSON field names. These are **source capabilities**, not a claim
that a particular historical fit used a particular correction configuration.

Next stage, separately scoped before any new real campaign:

1. Bind the installed binary, complete relevant source/library revisions, compiler
   and build options (including untracked generated build files), exact runtime
   configuration, leap-second/time-conversion and debias data. Current source and
   binary hashes do not by themselves prove a reproducible build or historical use.
2. Trace input date/coordinate parsing through time-scale conversion, rounding,
   any epoch transformation, bias correction, sorting and duplicate reconciliation.
   Prove numeric error bounds relative to the actual original observation, not
   merely the final floating-point value printed by `fprintf`.
3. Establish an authenticated original-row sidecar/export token, **or** a proved
   invertible/full-field transformation for unique matches, retaining original
   precision, notes and occurrence multiplicity. Debiased coordinates cannot be
   fed into this raw-coordinate prototype without that transformation proof.
4. Validate complete-row handling and explicit exclusion/inclusion semantics on
   newly specified synthetic exporter fixtures (future work; none run here).
   Missing or collapsed occurrences remain HOLD; never guess which duplicate
   survived. A higher-precision exporter may help, but precision alone does not
   recover identity lost during preprocessing.
5. Only then integrate into a separately named, fully bound preregistration that
   also repairs anatomy accounting and full dependency capture and prospectively
   calibrates fit-yield stopping. No ranks from M14 are resumed.

The available local source can support steps 1–3 without network access; the
remaining proof has not been completed in this stage.

## Verification and source lineage

From the repository root:

```powershell
python -B -m unittest discover -s itf-linker/tests -p test_m15_identity.py -v
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache itf-linker/scripts/m15_identity.py itf-linker/tests/test_m15_identity.py
python -B itf-linker/scripts/m15_identity.py --audit-root itf-linker/data/m14/runs/20260902T062614Z/fits
```

**27 tests PASS; Ruff PASS.** Tests cover every M14 required identity case, all
six residual permutations and eight inclusion patterns for three observations,
nontransitive tolerance chains, globally unique-but-locally ambiguous maps,
multiple assignments under every input/output order, malformed/missing fields,
and aggregate-only audit output. This is matcher verification, not exporter or
scientific pipeline validation.

The implementation imports no historical scientific module. The OBS80 field
layout follows the locally retained `mpc80.py`; M8/M9 selectors and the M14 audit
are read-only problem lineage, not reused algorithms. SHA-256 anchors:

| Source | SHA-256 |
|---|---|
| New scripts/m15_identity.py | `5d255a35183021498086408698816b717a69b9524b969ca8a8764dfcf63451fe` |
| New tests/test_m15_identity.py | `a17f0871d6175f8c002a8a664d88b3fcccfb00a3d02d9dec5176418b9f8fd2d2` |
| Existing scripts/m8_attribution.py | `f3e48c55e7c720b6c62c8f268b8449a21559c294cc6b15297d99575eedbb7752` |
| Existing scripts/m9_combined.py | `6874e06d7266a67c8fce4cc5f9e824a661108b05e184460d10e22ef3f90f3998` |
| Existing scripts/m14_fit_audit.py | `b0316b585c1d894a4dd926fcbb545785365df537d7cc4f1f7aa598648f841182` |
| Existing src/itf_linker/mpc80.py | `c61e8d3a4fa480b6eb5dfc41a885b278285b39e91fbdcef8a891441efae40477` |
| Existing src/itf_linker/fit/findorb.py | `137309047493fb1e58c604c36a20887eaaa38fa82bb0da716f4f0242af4d1aa2` |
| WSL elem_out.cpp | `5729ae36f639697a860015c73ad9ecff0f5dc87ec441fc83475df84fd5521981` |
| WSL mpc_obs.cpp | `f260de67d9178f658e2206dfc59d4318650b7ab9fc4733b013a22f482692d4b8` |
| WSL prefix.h | `d9720f063aededb2322514e0f603f1f8ec2442e0f620bfa0d2987f98f49b9337` |
| WSL PREFIX | `7ace431cb61584cb9b8dc7ec08cf38ac0a2d649660be86d349fb43108b542fa4` |

All historical result files and runner code remain unchanged. This stage opens
no review queue and makes no discovery/no-discovery or corrected-yield claim.
