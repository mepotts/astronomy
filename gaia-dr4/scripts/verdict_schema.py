#!/usr/bin/env python
"""M6: the DAY-ONE VERDICT RECORD -- one schema, two producers.

Three milestones (M3 n=1, M4 X-ray, M5 activity/variability/astrometric)
have now tested candidate discriminators against exactly one verdict
source: the 65 El-Badry+2026 follow-up verdicts hard-coded as
fixtures/elbadry2026_astrometric_candidates.csv.  Every one of those tests
came back footprint-, coverage- or power-limited, and M5's conclusion was
that the bottleneck is the VERDICT SAMPLE, not the axes.

The epoch-vetting loop manufactures verdicts at scale.  For its output to
be usable by the discriminator tests without a rewrite, a harness verdict
and an EB26 verdict have to be *the same record type*.  That is what this
module defines.

=======================================================================
THE RECORD  (schema_version = "day1_verdict.v1"; JSON Schema sidecar in
schemas/day1_verdict_record.v1.json)
=======================================================================

IDENTITY -- who was adjudicated
  source_id            int64   the source_id in `release`
  release              str     'Gaia DR3' | 'Gaia DR4' | ...  (which
                               catalogue `source_id` belongs to -- DR3->DR4
                               ids are NOT guaranteed stable, M1 landmine)
  source_id_dr3        int64?  DR3 id where known (crosswalk insurance)
  nss_solution_type    str?    the solution type; source_id alone is NOT a
                               key of nss_two_body_orbit (M2 landmine #4:
                               98 DR3 sources carry two astrometric
                               solutions), so the orbit key is
                               (source_id, nss_solution_type)

ORBIT PROVENANCE -- which orbit the verdict is about
  orbit_source         str     'gaiadr3.nss_two_body_orbit' |
                               'gaiadr4.nss_two_body_orbit' |
                               'elbadry2026_table' | ...
  orbit_period_d       float?  period of the adjudicated orbit
  orbit_significance   float?  the solution's own significance
  orbit_a0_mas         float?  photocentre semi-major axis
  queue_bin            str?    'v2_main' | 'retrieval_pr999' | 'external'
  queue_rank           int?    rank in the day-one queue where applicable

FIT STATISTICS -- null for an external verdict, filled by the harness
  n_transits_fetched   int?    rows served by DataLink for this source
  n_transits_used      int?    CCD transits entering the single-star fit
  f2_single_star       float?  the gaiasupdate goodness-of-fit statistic
  parallax_mas         float?  single-star-fit parallax
  excess_noise_mas     float?  (gaiasupdate 0.1.2 returns None; kept so the
                               column exists the day it does not)
  fit_model            str?    'lite'|'5p_single_source'|'6p_constrained_colour'
  fit_seconds          float?  wall time of the fit (throughput accounting)

THE VERDICT
  verdict              str     controlled vocabulary, shared by BOTH
                               producers:
                                 CONFIRMED, SPURIOUS, MARGINAL, UNKNOWN,
                                 NOT_CO, OTHER, INCONCLUSIVE, NO_DATA, ERROR
  verdict_scope        str     WHAT the verdict is about.  This column is
                               the honest part and it is mandatory:
                                 'compact_companion' -- is there a dark
                                     massive companion?  (EB26: RV
                                     follow-up.)
                                 'orbit_reality'     -- does the published
                                     photocentre orbit have epoch-level
                                     support?  (the harness.)
                               A harness DEMOTE and an EB26 SPURIOUS mean
                               nearly the same thing ("the orbit is not
                               real"); a harness KEEP is WEAKER than an
                               EB26 CONFIRMED (orbit real, companion nature
                               unestablished).  Pooling the two scopes is
                               therefore asymmetric, and any consumer that
                               pools them must print the scope composition
                               of both groups.  scope_composition_string()
                               exists so that costs one line of code.
  verdict_basis        str     'rv_followup' | 'epoch_astrometry_f2' | ...
  verdict_confidence   str     HIGH | MEDIUM | LOW
  verdict_confidence_basis str the rule that set it, in words

CAUTION FLAGS -- the seven frozen in config v4, carried on the record so a
consumer never has to re-derive them (all bool, default False)
  flag_alias_1yr, flag_low_lat, flag_hi_sigma_ti2, flag_xray_active,
  flag_dust_unresolved_south, flag_dust_sigma_fragile, flag_astrom_quiet

PROVENANCE / VERSIONING -- so a verdict can be reproduced or retired
  schema_version       str     'day1_verdict.v1'
  verdict_source       str     'elbadry2026' | 'epoch_vet_harness'
  verdict_source_version str   citation or code version
  config_version       int?    triage config the row was produced under
  epoch_data_release   str?    DataLink RELEASE string used
  epoch_data_structure str?    'RAW' | 'INDIVIDUAL'
  gaiasupdate_version  str?
  produced_utc         str     ISO-8601 UTC
  run_id               str     harness run identifier (external: the
                               fixture's provenance tag)
  notes                str?    free text, carried verbatim from the source

=======================================================================
WHY THE EB26 ADAPTER CARRIES period_d / significance / notes
=======================================================================
The M4 and M5 tests consume those three columns from the fixture and write
them into their artifacts.  They are orbit-provenance fields in this schema
already (orbit_period_d, orbit_significance, notes), so the adapter is a
rename, not an extension -- and eb26_compatible_frame() hands the tests
back exactly the column names they already use, which is what makes the
refactor a change of SOURCE and not a change of BEHAVIOUR.  The store is
written in fixture order for the same reason: byte-identical reproduction
is the acceptance test of the refactor.
"""

import datetime as _dt
import glob
import json
import os

import numpy as np
import pandas as pd

SCHEMA_VERSION = "day1_verdict.v1"

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_DIR = os.path.join(BASE, "out", "verdicts")

VERDICT_VOCAB = ["CONFIRMED", "SPURIOUS", "MARGINAL", "UNKNOWN", "NOT_CO",
                 "OTHER", "INCONCLUSIVE", "NO_DATA", "ERROR"]
SCOPE_VOCAB = ["compact_companion", "orbit_reality"]
CONFIDENCE_VOCAB = ["HIGH", "MEDIUM", "LOW"]

# the seven caution flags frozen in queries/dr4-triage-config.v4.json
CAUTION_FLAGS = ["flag_alias_1yr", "flag_low_lat", "flag_hi_sigma_ti2",
                 "flag_xray_active", "flag_dust_unresolved_south",
                 "flag_dust_sigma_fragile", "flag_astrom_quiet"]

# column -> (dtype, required)
FIELDS = [
    # identity
    ("source_id", "Int64", True),
    ("release", "string", True),
    ("source_id_dr3", "Int64", False),
    ("nss_solution_type", "string", False),
    # orbit provenance
    ("orbit_source", "string", True),
    ("orbit_period_d", "Float64", False),
    ("orbit_significance", "Float64", False),
    ("orbit_a0_mas", "Float64", False),
    ("queue_bin", "string", False),
    ("queue_rank", "Int64", False),
    # fit statistics
    ("n_transits_fetched", "Int64", False),
    ("n_transits_used", "Int64", False),
    ("f2_single_star", "Float64", False),
    ("parallax_mas", "Float64", False),
    ("excess_noise_mas", "Float64", False),
    ("fit_model", "string", False),
    ("fit_seconds", "Float64", False),
    # the verdict
    ("verdict", "string", True),
    ("verdict_scope", "string", True),
    ("verdict_basis", "string", True),
    ("verdict_confidence", "string", True),
    ("verdict_confidence_basis", "string", False),
] + [(f, "boolean", False) for f in CAUTION_FLAGS] + [
    # provenance / versioning
    ("schema_version", "string", True),
    ("verdict_source", "string", True),
    ("verdict_source_version", "string", True),
    ("config_version", "Int64", False),
    ("epoch_data_release", "string", False),
    ("epoch_data_structure", "string", False),
    ("gaiasupdate_version", "string", False),
    ("produced_utc", "string", True),
    ("run_id", "string", True),
    ("notes", "string", False),
]
COLUMNS = [c for c, _d, _r in FIELDS]
DTYPES = {c: d for c, d, _r in FIELDS}
REQUIRED = [c for c, _d, r in FIELDS if r]


def utcnow():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_frame():
    return pd.DataFrame({c: pd.Series(dtype=DTYPES[c]) for c in COLUMNS})


def coerce(df):
    """Return `df` with every schema column present and correctly typed."""
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


def validate(df, strict=True):
    """Check a verdict frame against the schema.  Returns a list of
    problems; raises when `strict` and the list is non-empty."""
    problems = []
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")
        if strict:
            raise ValueError(problems[-1])
    for c in REQUIRED:
        if c in df.columns and df[c].isna().any():
            n = int(df[c].isna().sum())
            problems.append(f"required column {c} has {n} null(s)")
    for col, vocab in (("verdict", VERDICT_VOCAB),
                       ("verdict_scope", SCOPE_VOCAB),
                       ("verdict_confidence", CONFIDENCE_VOCAB)):
        if col in df.columns:
            bad = sorted(set(df[col].dropna().astype(str)) - set(vocab))
            if bad:
                problems.append(f"{col} outside vocabulary: {bad}")
    if "schema_version" in df.columns:
        bad = sorted(set(df["schema_version"].dropna().astype(str))
                     - {SCHEMA_VERSION})
        if bad:
            problems.append(f"foreign schema_version: {bad}")
    # the orbit key must not silently collide
    if {"source_id", "nss_solution_type", "verdict_source"} <= set(df.columns):
        k = df[["source_id", "nss_solution_type", "verdict_source",
                "verdict_scope"]].astype(str)
        dup = int(k.duplicated().sum())
        if dup:
            problems.append(f"{dup} duplicate (source_id, solution_type, "
                            f"source, scope) key(s)")
    if strict and problems:
        raise ValueError("verdict schema violations: " + "; ".join(problems))
    return problems


# ------------------------------------------------------------------ EB26
EB26_CITATION = ("El-Badry et al. 2026, arXiv:2608.06453 -- follow-up "
                 "verdict table, parsed by scripts/parse_elbadry2026_table.py "
                 "into fixtures/elbadry2026_astrometric_candidates.csv")


def from_eb26(fixture_path=None, queue_path=None, run_id="eb26_import_v1"):
    """The external verdicts as day-one verdict records.

    Row order is the fixture's, deliberately: the M4/M5 refactor is
    verified by byte-identical reproduction of their frozen artifacts, and
    those follow fixture order.
    """
    fixture_path = fixture_path or os.path.join(
        BASE, "fixtures", "elbadry2026_astrometric_candidates.csv")
    eb = pd.read_csv(fixture_path)
    r = pd.DataFrame({
        "source_id": eb["source_id"].astype("Int64"),
        "release": "Gaia DR3",
        "source_id_dr3": eb["source_id"].astype("Int64"),
        "nss_solution_type": pd.NA,
        "orbit_source": "elbadry2026_table",
        "orbit_period_d": eb["period_d"].astype("Float64"),
        "orbit_significance": eb["significance"].astype("Float64"),
        "orbit_a0_mas": pd.NA,
        "queue_bin": "external",
        "queue_rank": pd.NA,
        "verdict": eb["verdict"].astype("string"),
        "verdict_scope": "compact_companion",
        "verdict_basis": "rv_followup",
        "verdict_confidence": "HIGH",
        "verdict_confidence_basis": (
            "published follow-up verdict; EB26 report it as a decision, not "
            "a score -- UNKNOWN/MARGINAL rows carry their own label in "
            "`verdict` rather than a downgraded confidence"),
        "schema_version": SCHEMA_VERSION,
        "verdict_source": "elbadry2026",
        "verdict_source_version": EB26_CITATION,
        "config_version": 5,
        "produced_utc": utcnow(),
        "run_id": run_id,
        "notes": eb["notes"].astype("string"),
    })
    # UNKNOWN is a non-verdict: say so in the confidence column too
    r.loc[r["verdict"] == "UNKNOWN", "verdict_confidence"] = "LOW"
    r.loc[r["verdict"] == "UNKNOWN", "verdict_confidence_basis"] = (
        "EB26 UNKNOWN = follow-up absent or incomplete; not a verdict")
    r.loc[r["verdict"] == "MARGINAL", "verdict_confidence"] = "MEDIUM"
    r = attach_queue_flags(r, queue_path=queue_path)
    return coerce(r)


def attach_queue_flags(r, queue_path=None):
    """Fill the seven caution flags (and queue_bin/rank/solution type) from
    the day-one queue for whichever rows are in it."""
    queue_path = queue_path or os.path.join(
        BASE, "out", "epoch_vet_day1_queue.v2.csv")
    if not os.path.exists(queue_path):
        return r
    q = pd.read_csv(queue_path)
    cols = ["source_id", "nss_solution_type", "rank", "queue_bin"] + \
           [f for f in CAUTION_FLAGS if f in q.columns]
    q = q[cols].drop_duplicates("source_id")
    m = r.merge(q, on="source_id", how="left", suffixes=("", "_q"))
    for f in CAUTION_FLAGS:
        if f in q.columns:
            m[f] = m[f + "_q"] if f + "_q" in m.columns else m[f]
            m[f] = m[f].astype("object").where(m[f].notna(), False)
    if "nss_solution_type_q" in m.columns:
        m["nss_solution_type"] = m["nss_solution_type"].fillna(
            m["nss_solution_type_q"])
    if "rank" in m.columns:
        m["queue_rank"] = m["rank"].astype("Float64").astype("Int64")
    if "queue_bin_q" in m.columns:
        m["queue_bin"] = m["queue_bin_q"].fillna(m["queue_bin"])
    return m[[c for c in m.columns if not c.endswith("_q")
              and c != "rank"]]


# ------------------------------------------------------------ store I/O
def write_store(df, path, verbose=True):
    df = coerce(df)
    validate(df)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")
    if verbose:
        print(f"  wrote {os.path.relpath(path, BASE)}: {len(df)} records "
              f"({df['verdict'].value_counts().to_dict()})")
    return path


def load_store(paths=None, scopes=None, sources=None, strict=True):
    """Load one or more verdict-store CSVs into a single validated frame.

    paths  : list of CSV paths (default: every *.csv in out/verdicts/)
    scopes : keep only these verdict_scope values (None = all)
    sources: keep only these verdict_source values (None = all)
    """
    if paths is None:
        paths = sorted(os.path.join(STORE_DIR, f)
                       for f in os.listdir(STORE_DIR)
                       if f.endswith(".csv")) if os.path.isdir(STORE_DIR) \
            else []
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    # Accept what a human will actually type: a directory, a glob, or the
    # word "all".  cmd.exe does not expand wildcards, so
    # `--verdicts out\verdicts\*.csv` arrives here as a literal string --
    # a runbook command that only works in one shell is a trap.
    expanded = []
    for p in paths:
        p = str(p)
        if p.lower() == "all":
            expanded += sorted(os.path.join(STORE_DIR, f)
                               for f in os.listdir(STORE_DIR)
                               if f.endswith(".csv"))
        elif os.path.isdir(p):
            expanded += sorted(os.path.join(p, f) for f in os.listdir(p)
                               if f.endswith(".csv"))
        elif any(ch in p for ch in "*?["):
            expanded += sorted(glob.glob(p))
        else:
            expanded.append(p)
    paths = expanded
    if not paths:
        raise FileNotFoundError(f"no verdict store found under {STORE_DIR}")
    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df = coerce(df)
    validate(df, strict=strict)
    if scopes is not None:
        df = df[df["verdict_scope"].isin(scopes)].reset_index(drop=True)
    if sources is not None:
        df = df[df["verdict_source"].isin(sources)].reset_index(drop=True)
    return df


def scope_composition_string(df, group_col="verdict"):
    """One line naming, per verdict class, how many records came from each
    (verdict_source, verdict_scope).  Any consumer that pools scopes is
    required to print this."""
    bits = []
    for v, g in df.groupby(group_col, sort=True):
        inner = ", ".join(
            f"{s}/{sc}:{n}" for (s, sc), n in
            g.groupby(["verdict_source", "verdict_scope"]).size().items())
        bits.append(f"{v}[{inner}]")
    return "  ".join(bits)


def eb26_compatible_frame(df):
    """Hand a consumer the column names the M4/M5 tests already use.

    This is the whole compatibility layer: `verdict` unchanged, the two
    orbit-provenance fields renamed back, `notes` verbatim.  A harness
    record passes through the same function, which is the point -- the
    tests cannot tell (and must not need to tell) where a verdict came
    from, except through the columns that say so, which are kept.
    """
    out = pd.DataFrame({
        "source_id": df["source_id"].astype("int64"),
        "period_d": df["orbit_period_d"].astype(float),
        "significance": df["orbit_significance"].astype(float),
        "notes": df["notes"].astype(object).where(df["notes"].notna(), np.nan),
        "verdict": df["verdict"].astype(object),
        "verdict_source": df["verdict_source"].astype(object),
        "verdict_scope": df["verdict_scope"].astype(object),
        "verdict_confidence": df["verdict_confidence"].astype(object),
    })
    return out


def json_schema():
    """The JSON Schema sidecar (written by --emit-schema)."""
    tmap = {"Int64": "integer", "Float64": "number", "string": "string",
            "boolean": "boolean"}
    props = {}
    for c, d, req in FIELDS:
        p = {"type": [tmap[d], "null"] if not req else tmap[d]}
        if c == "verdict":
            p["enum"] = VERDICT_VOCAB
        if c == "verdict_scope":
            p["enum"] = SCOPE_VOCAB
        if c == "verdict_confidence":
            p["enum"] = CONFIDENCE_VOCAB
        props[c] = p
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "gaia-dr4 day-one verdict record",
        "description": (
            "One record per adjudicated orbit.  Produced identically by an "
            "external follow-up table (El-Badry+2026) and by the epoch-vet "
            "harness; verdict_scope says which question was answered."),
        "schema_version": SCHEMA_VERSION,
        "type": "object",
        "required": REQUIRED,
        "properties": props,
        "additionalProperties": False,
    }


if __name__ == "__main__":
    import sys
    if "--emit-schema" in sys.argv:
        p = os.path.join(BASE, "schemas", "day1_verdict_record.v1.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(json_schema(), fh, indent=2)
            fh.write("\n")
        print(f"wrote {p}")
    if "--build-eb26" in sys.argv:
        r = from_eb26()
        write_store(r, os.path.join(STORE_DIR, "eb26.v1.csv"))
        print("  scope composition:", scope_composition_string(r))
