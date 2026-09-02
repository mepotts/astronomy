#!/usr/bin/env python
"""M7: day-one verdict record **v2** -- v1 plus the orbital-refit block.

WHY A NEW VERSION AND NOT AN EDIT.  v1 (`scripts/verdict_schema.py`,
`schemas/day1_verdict_record.v1.json`) is frozen: `out/verdicts/eb26.v1.csv`
and `out/verdicts/harness_prerelease.v1.csv` are written against it, the M4
and M5 discriminator artifacts are certified byte-identical through it, and
its `validate()` rejects a foreign `schema_version` by design.  Mutating it
in place would silently invalidate all of that.  v2 is therefore a separate
module that IMPORTS v1, adds columns after v1's, and is backward compatible
in one direction only, which is stated out loud:

    every v1 record is a valid v2 record (upgrade() fills the new columns
    with nulls and rewrites schema_version)
    a v2 record is NOT a valid v1 record

WHAT v2 ADDS, and why exactly this.  The harness answers `orbit_reality`:
"the photocentre orbit has epoch-level support".  December's headline is not
that -- it is *the independent orbit and the companion mass it implies*.
That output has no home in v1: `orbit_period_d` / `orbit_a0_mas` are ORBIT
PROVENANCE fields (the catalogue's orbit, the thing being adjudicated), and
writing a re-derived value into them would destroy the distinction between
what Gaia published and what we measured.  So the refit gets its own block,
every field prefixed `refit_`, and the provenance fields keep meaning what
they meant.

THE REFIT BLOCK (all nullable; null = the arm did not run or did not reach
this stage, which is why `refit_status` is the field a consumer reads first)

  refit_status        SKIPPED | OK | NO_PEAK | FIT_FAILED | NO_DATA
  refit_method        code path, e.g. 'kepmodel_spleaf_astro'
  refit_code_version  version string of the arm that produced the row
  refit_n_ccd         CCD transits entering the Keplerian fit
  refit_rms_single_mas   single-star (linear-only) residual rms
  refit_peak_period_d    periodogram peak of the single-star residuals
  refit_peak_fap         its false-alarm probability
  refit_period_d / _err_d          Campbell elements and their formal
  refit_ecc / _err                 (Hessian) errors
  refit_a0_mas / _err_mas
  refit_inc_deg, refit_omega_deg, refit_bigomega_deg, refit_tp_d
  refit_parallax_mas / _err_mas    from the same fit, NOT the catalogue's
  refit_pmra_masyr, refit_pmdec_masyr
  refit_mass_function_msun         a0^3 / (P_yr^2 * parallax^3): the
                                   M1-FREE observable.  This is the number
                                   that survives a wrong primary mass.
  refit_m1_msun / _sigma_msun / _source    the adopted primary mass and
                                   WHICH RUNG of the triage's own three-tier
                                   ladder it came from (binary_masses /
                                   photometric_ms / evolved_bracket /
                                   literature) -- the refit arm must not
                                   invent an M1 chain the candidate list was
                                   not ranked with
  refit_m2_msun                    companion mass at the point estimate
  refit_m2_p05/_p16/_p50/_p84/_p95 the companion-mass POSTERIOR
  refit_m2_posterior_n             draws
  refit_posterior_method           how the posterior was made
  refit_seconds

VOCABULARY.  v2 adds one verdict value, `NOT_ADJUDICATED`, for a record the
harness handled without attempting an adjudication.  It exists so that a
non-adjudicating pass can never be mistaken for a null verdict; today only
the transport rehearsal would use it, and that writes its own ledger outside
the store instead, so the value is declared and unused.  No scope is added:
the refit does not answer a new question, it quantifies the one already
answered CONFIRMED.

Emit the sidecar:  .venv/Scripts/python.exe scripts/verdict_schema_v2.py --emit-schema
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as v1                                      # noqa: E402

BASE = v1.BASE
STORE_DIR_V2 = os.path.join(BASE, "out", "verdicts_v2")

SCHEMA_VERSION = "day1_verdict.v2"
SUPPORTED_SCHEMA_VERSIONS = [v1.SCHEMA_VERSION, SCHEMA_VERSION]

VERDICT_VOCAB = list(v1.VERDICT_VOCAB) + ["NOT_ADJUDICATED"]
SCOPE_VOCAB = list(v1.SCOPE_VOCAB)
CONFIDENCE_VOCAB = list(v1.CONFIDENCE_VOCAB)
CAUTION_FLAGS = list(v1.CAUTION_FLAGS)
REFIT_STATUS_VOCAB = ["SKIPPED", "OK", "NO_PEAK", "FIT_FAILED", "NO_DATA"]

REFIT_FIELDS = [
    ("refit_status", "string", False),
    ("refit_method", "string", False),
    ("refit_code_version", "string", False),
    ("refit_n_ccd", "Int64", False),
    ("refit_rms_single_mas", "Float64", False),
    ("refit_peak_period_d", "Float64", False),
    ("refit_peak_fap", "Float64", False),
    ("refit_period_d", "Float64", False),
    ("refit_period_err_d", "Float64", False),
    ("refit_ecc", "Float64", False),
    ("refit_ecc_err", "Float64", False),
    ("refit_a0_mas", "Float64", False),
    ("refit_a0_err_mas", "Float64", False),
    ("refit_inc_deg", "Float64", False),
    ("refit_omega_deg", "Float64", False),
    ("refit_bigomega_deg", "Float64", False),
    ("refit_tp_d", "Float64", False),
    ("refit_parallax_mas", "Float64", False),
    ("refit_parallax_err_mas", "Float64", False),
    ("refit_pmra_masyr", "Float64", False),
    ("refit_pmdec_masyr", "Float64", False),
    ("refit_mass_function_msun", "Float64", False),
    ("refit_m1_msun", "Float64", False),
    ("refit_m1_sigma_msun", "Float64", False),
    ("refit_m1_source", "string", False),
    ("refit_m2_msun", "Float64", False),
    ("refit_m2_p05", "Float64", False),
    ("refit_m2_p16", "Float64", False),
    ("refit_m2_p50", "Float64", False),
    ("refit_m2_p84", "Float64", False),
    ("refit_m2_p95", "Float64", False),
    ("refit_m2_posterior_n", "Int64", False),
    ("refit_posterior_method", "string", False),
    ("refit_seconds", "Float64", False),
    ("refit_notes", "string", False),
]

FIELDS = list(v1.FIELDS) + REFIT_FIELDS
COLUMNS = [c for c, _d, _r in FIELDS]
DTYPES = {c: d for c, d, _r in FIELDS}
REQUIRED = [c for c, _d, r in FIELDS if r]
REFIT_COLUMNS = [c for c, _d, _r in REFIT_FIELDS]

utcnow = v1.utcnow
scope_composition_string = v1.scope_composition_string
eb26_compatible_frame = v1.eb26_compatible_frame


def empty_frame():
    return pd.DataFrame({c: pd.Series(dtype=DTYPES[c]) for c in COLUMNS})


def coerce(df):
    """Every v2 column present and correctly typed."""
    out = df.copy()
    for c in COLUMNS:
        if c not in out.columns:
            out[c] = pd.NA
    for c in COLUMNS:
        if DTYPES[c] == "boolean":
            out[c] = out[c].astype("object").where(out[c].notna(), False)
            out[c] = out[c].astype(bool).astype("boolean")
        else:
            out[c] = out[c].astype(DTYPES[c])
    return out[COLUMNS]


def upgrade(df):
    """A v1 frame as a v2 frame: refit columns null, schema_version bumped.

    The reverse does not exist on purpose.  A v2 record carries measurements
    v1 has nowhere to put, so 'downgrading' would be data loss dressed as a
    conversion.
    """
    out = coerce(df)
    out["schema_version"] = SCHEMA_VERSION
    if "refit_status" in out.columns:
        out["refit_status"] = out["refit_status"].fillna("SKIPPED")
    return out


def validate(df, strict=True):
    problems = []
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        problems.append("missing columns: %s" % missing)
        if strict:
            raise ValueError(problems[-1])
    for c in REQUIRED:
        if c in df.columns and df[c].isna().any():
            problems.append("required column %s has %d null(s)"
                            % (c, int(df[c].isna().sum())))
    for col, vocab in (("verdict", VERDICT_VOCAB),
                       ("verdict_scope", SCOPE_VOCAB),
                       ("verdict_confidence", CONFIDENCE_VOCAB),
                       ("refit_status", REFIT_STATUS_VOCAB)):
        if col in df.columns:
            bad = sorted(set(df[col].dropna().astype(str)) - set(vocab))
            if bad:
                problems.append("%s outside vocabulary: %s" % (col, bad))
    if "schema_version" in df.columns:
        bad = sorted(set(df["schema_version"].dropna().astype(str))
                     - {SCHEMA_VERSION})
        if bad:
            problems.append("foreign schema_version: %s (use upgrade())"
                            % bad)
    if {"source_id", "nss_solution_type", "verdict_source"} <= set(df.columns):
        k = df[["source_id", "nss_solution_type", "verdict_source",
                "verdict_scope"]].astype(str)
        dup = int(k.duplicated().sum())
        if dup:
            problems.append("%d duplicate (source_id, solution_type, source, "
                            "scope) key(s)" % dup)
    # a refit that says OK must carry the two numbers the arm exists to make
    if "refit_status" in df.columns:
        ok = df["refit_status"].astype(str) == "OK"
        for c in ("refit_period_d", "refit_mass_function_msun"):
            if c in df.columns and ok.any() and df.loc[ok, c].isna().any():
                problems.append("refit_status OK with null %s" % c)
    if strict and problems:
        raise ValueError("verdict schema v2 violations: " + "; ".join(problems))
    return problems


def write_store(df, path, verbose=True):
    df = coerce(df)
    validate(df)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")
    if verbose:
        print("  wrote %s: %d records (%s)"
              % (os.path.relpath(path, BASE), len(df),
                 df["verdict"].value_counts().to_dict()))
    return path


def load_store(paths=None, scopes=None, sources=None, strict=True,
               supersede=True, verbose=True):
    """Load v1 and/or v2 store files into one validated v2 frame.

    v1 files are upgraded on read, which is what makes the December store a
    superset of the frozen one rather than a replacement for it.

    SUPERSEDING, and why it is not silent.  The refit arm ENRICHES a harness
    verdict: it writes the same (source_id, solution_type, source, scope) key
    with the refit block filled in.  So after a refit pass the same orbit
    exists in the v1 harness ledger and in the v2 refit store, and loading
    both raised `12 duplicate key(s)` the first time it was tried -- correctly,
    because a duplicate key is normally a bug.  The rule, declared here:

      * a key present in BOTH a v1 file and a v2 file  -> the v2 row wins
        (it is the same verdict plus measurements), and the number superseded
        is PRINTED;
      * a key duplicated WITHIN one schema version     -> still raises.

    Set supersede=False to get the raw union and let validate() object.
    """
    if paths is None:
        paths = [v1.STORE_DIR, STORE_DIR_V2]
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    expanded = []
    for p in paths:
        p = str(p)
        if p.lower() == "all":
            for d in (v1.STORE_DIR, STORE_DIR_V2):
                if os.path.isdir(d):
                    expanded += sorted(os.path.join(d, f)
                                       for f in os.listdir(d)
                                       if f.endswith(".csv"))
        elif os.path.isdir(p):
            expanded += sorted(os.path.join(p, f) for f in os.listdir(p)
                               if f.endswith(".csv"))
        elif any(ch in p for ch in "*?["):
            import glob as _glob
            expanded += sorted(_glob.glob(p))
        else:
            expanded.append(p)
    if not expanded:
        raise FileNotFoundError("no verdict store found")
    frames = []
    for p in expanded:
        d = pd.read_csv(p)
        sv = set(d.get("schema_version", pd.Series(dtype=object))
                 .dropna().astype(str))
        unknown = sv - set(SUPPORTED_SCHEMA_VERSIONS)
        if unknown:
            raise ValueError("unsupported schema_version %s in %s"
                             % (sorted(unknown), p))
        u = upgrade(d)
        # native version BEFORE the upgrade rewrote it -- this is what
        # decides who supersedes whom
        u["_native_schema"] = (SCHEMA_VERSION if SCHEMA_VERSION in sv
                               else v1.SCHEMA_VERSION)
        u["_src_file"] = os.path.basename(p)
        frames.append(u)
    df = pd.concat(frames, ignore_index=True)
    if supersede and len(df):
        key = ["source_id", "nss_solution_type", "verdict_source",
               "verdict_scope"]
        k = df[key].astype(str).agg("|".join, axis=1)
        is_v2 = df["_native_schema"] == SCHEMA_VERSION
        dup_keys = set(k[k.duplicated(keep=False)])
        drop = pd.Series(False, index=df.index)
        for kk in dup_keys:
            rows = k[k == kk].index
            if is_v2.loc[rows].any() and not is_v2.loc[rows].all():
                drop.loc[[r for r in rows if not is_v2.loc[r]]] = True
        if drop.any() and verbose:
            print("  superseded %d v1 record(s) by their v2 refit rows"
                  % int(drop.sum()))
        df = df[~drop].reset_index(drop=True)
    df = df.drop(columns=["_native_schema", "_src_file"], errors="ignore")
    df = coerce(df)
    validate(df, strict=strict)
    if scopes is not None:
        df = df[df["verdict_scope"].isin(scopes)].reset_index(drop=True)
    if sources is not None:
        df = df[df["verdict_source"].isin(sources)].reset_index(drop=True)
    return df


def json_schema():
    tmap = {"Int64": "integer", "Float64": "number", "string": "string",
            "boolean": "boolean"}
    props = {}
    for c, d, req in FIELDS:
        p = {"type": tmap[d] if req else [tmap[d], "null"]}
        if c == "verdict":
            p["enum"] = VERDICT_VOCAB
        if c == "verdict_scope":
            p["enum"] = SCOPE_VOCAB
        if c == "verdict_confidence":
            p["enum"] = CONFIDENCE_VOCAB
        if c == "refit_status":
            p["enum"] = REFIT_STATUS_VOCAB + [None]
        props[c] = p
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "gaia-dr4 day-one verdict record v2",
        "description": (
            "v1 plus the orbital-refit block.  v1 fields are unchanged and "
            "keep their meaning: orbit_* is the CATALOGUE orbit being "
            "adjudicated, refit_* is the orbit this pipeline re-derived from "
            "epoch astrometry.  Every v1 record is a valid v2 record after "
            "upgrade(); the reverse is data loss and is not provided."),
        "schema_version": SCHEMA_VERSION,
        "supersedes": v1.SCHEMA_VERSION,
        "type": "object",
        "required": REQUIRED,
        "properties": props,
        "additionalProperties": False,
    }


if __name__ == "__main__":
    if "--emit-schema" in sys.argv:
        p = os.path.join(BASE, "schemas", "day1_verdict_record.v2.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(json_schema(), fh, indent=2)
            fh.write("\n")
        print("wrote %s" % p)
    if "--selftest" in sys.argv:
        old = v1.load_store([os.path.join(v1.STORE_DIR, "eb26.v1.csv")])
        up = upgrade(old)
        validate(up)
        back = up[v1.COLUMNS].copy()
        back["schema_version"] = v1.SCHEMA_VERSION
        same = v1.coerce(old).equals(v1.coerce(back))
        print("v1 -> v2 -> v1 round trip identical on the frozen EB26 store:",
              same)
        print("v2 columns: %d (v1 %d + refit %d)"
              % (len(COLUMNS), len(v1.COLUMNS), len(REFIT_COLUMNS)))
