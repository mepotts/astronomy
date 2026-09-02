"""M1 step 5: turn a filtered pool into a Matthew-gated candidate list.

NOTHING HERE REPORTS ANYTHING.  This writes a CSV.  No TNS write path is imported,
called, or referenced anywhere in this repository.

Per candidate: position, magnitude and band at the passing epoch, detection
history, nearest catalogued source and separation, why it passed, and a
plain-language guess at what it is.

Also does the final TNS exclusion: a 3" positional cross-match against the full
12-month TNS harvest, on top of Fink's own per-alert d:tns column.

usage: python m1_candidates.py <tag> [--window-tag <tag-for-json>]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as F  # noqa: E402
from cache_contract import (  # noqa: E402
    atomic_write,
    canonical_digest,
    load_cache_contract,
    sha256_file,
    validated_tag,
    write_cache,
)
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    cache_provenance,
    fetch_one,
    history_as_of,
    require_single_jd_ceiling,
)
from tns_candidate_match import apply_tns_contract, verified_provenance  # noqa: E402
from tnscommon import DATA, OUT, session  # noqa: E402

POOL = DATA / "pool"
CANDIDATE_COLUMNS = [
    "oid", "STATUS", "tier", "flat_residual", "ra", "dec", "gal_b",
    "history_jd_ceiling", "channel", "reason", "ptp_mag_60d",
    "n_alerts_60d_maxband", "mag_at_pass", "band_at_pass", "first_pass_jd",
    "outburst_amp", "n_clean", "n_alerts_total", "first_alert_mjd",
    "last_alert_mjd", "nearest_catalogued_source", "nearest_sep_arcsec",
    "distnr", "magnr", "drb", "simbad_class", "tns_frozen_nearest",
    "tns_frozen_sep_arcsec", "tns_current_nearest", "tns_current_sep_arcsec",
    "tns_current_match", "tns_snapshot_id", "tns_snapshot_jd",
    "tns_current_snapshot_id", "probably", "detection_history_mjd_band_mag",
    "ztf_link",
]


def _empty_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a schema-stable zero-row candidate result."""
    return frame.iloc[0:0].reindex(columns=CANDIDATE_COLUMNS)


def _load_filtered(tag: str) -> pd.DataFrame:
    tag = validated_tag(tag)
    path = POOL / f"filtered_{tag}.csv"
    manifest = OUT / f"m1_pool_{tag}.json"
    try:
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        proved = saved["filtered_output_provenance"]
        contract = proved["contract"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"{manifest} does not prove a completed filtered pool; rerun m1_pool.py"
        ) from exc
    if saved.get("tag") != tag or contract.get("tag") != tag:
        raise RuntimeError(f"filtered pool tag mismatch for {tag}")
    if contract.get("mjd_window") != saved.get("mjd_window"):
        raise RuntimeError(f"filtered pool window mismatch for {tag}")
    if float(contract.get("history_jd_ceiling", float("nan"))) != float(
        saved.get("history_jd_ceiling", float("nan"))
    ):
        raise RuntimeError(f"filtered pool ceiling mismatch for {tag}")
    actual = load_cache_contract(
        path,
        kind="m1_filtered_pool",
        expected_contract=contract,
    )
    if actual != proved:
        raise RuntimeError(f"filtered pool proof does not match manifest for {tag}")
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise RuntimeError(f"cannot parse proved filtered pool {path}") from exc
    if len(frame) != int(proved.get("row_count", -1)):
        raise RuntimeError(f"filtered pool row-count mismatch for {tag}")
    if len(frame):
        ceiling = require_single_jd_ceiling(
            frame["history_jd_ceiling"].tolist(), str(path)
        )
        if ceiling != float(saved["history_jd_ceiling"]):
            raise RuntimeError(f"filtered rows do not share manifest ceiling for {tag}")
    return frame


def _existing_tns_reference(tag: str) -> dict | None:
    """Read the crash-safe immutable TNS input selected for this candidate tag."""
    tag = validated_tag(tag)
    manifest = OUT / f"m1_candidates_{tag}.tns-input.json"
    if not manifest.exists():
        return None
    try:
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        reference = saved["frozen_dedupe"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"invalid frozen TNS input manifest {manifest}") from exc
    if not isinstance(reference, dict):
        raise RuntimeError(f"invalid frozen TNS reference in {manifest}")
    return reference


def _pin_tns_reference(tag: str, jd_ceiling: float) -> dict:
    tag = validated_tag(tag)
    existing = _existing_tns_reference(tag)
    if existing is not None:
        saved = json.loads(
            (OUT / f"m1_candidates_{tag}.tns-input.json").read_text(encoding="utf-8")
        )
        if float(saved.get("history_jd_ceiling", float("nan"))) != float(jd_ceiling):
            raise RuntimeError(f"TNS input manifest ceiling mismatch for tag {tag}")
        verified_provenance(existing, jd_ceiling)
        return existing
    frozen, _current = verified_provenance(None, jd_ceiling)
    manifest = {
        "schema_version": 1,
        "tag": tag,
        "history_jd_ceiling": jd_ceiling,
        "frozen_dedupe": frozen,
    }
    atomic_write(
        OUT / f"m1_candidates_{tag}.tns-input.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return frozen


def _source_jd_ceiling(tag: str, frame: pd.DataFrame) -> float:
    tag = validated_tag(tag)
    if "history_jd_ceiling" in frame.columns and len(frame):
        return require_single_jd_ceiling(
            frame["history_jd_ceiling"].tolist(), f"filtered_{tag}.csv"
        )
    manifest = OUT / f"m1_pool_{tag}.json"
    if not manifest.exists():
        raise RuntimeError(
            f"no history ceiling for {tag}; rerun m1_pool.py before candidates"
        )
    saved = json.loads(manifest.read_text(encoding="utf-8"))
    try:
        return require_single_jd_ceiling(
            [saved["history_jd_ceiling"]], str(manifest)
        )
    except KeyError as exc:
        raise RuntimeError(
            f"{manifest} predates history ceilings; rerun m1_pool.py"
        ) from exc


def one_liner(r: pd.Series) -> str:
    """Plain language, and honest about the sign of the amplitude.

    outburst_amp = magnr - magpsf: the quiescent reference-image magnitude of the
    nearest source minus the difference-image magnitude of the transient.
    POSITIVE means the new light outshines whatever was there -- a real outburst.
    NEGATIVE means the variation is smaller than the star it sits on, which is a
    much weaker case and must be said so rather than dressed up as a brightening.
    """
    ch = r["channel"]
    b = r.get("gal_b")
    mag = r.get("mag_at_pass")
    amp = r.get("outburst_amp")
    plane = (not pd.isna(b)) and abs(b) < F.GAL_PLANE_ABS_B
    where = (f"galactic plane (|b| = {abs(b):.1f} deg)" if plane
             else f"|b| = {abs(b):.1f} deg" if pd.notna(b) else "unknown latitude")

    if ch == "A1_cv_outburst":
        if pd.notna(amp) and amp >= 1.0:
            what = (f"a catalogued point source has brightened by {amp:.1f} mag "
                    "above its quiescent level")
            guess = ("a dwarf-nova outburst or a classical nova" if plane
                     else "a dwarf-nova outburst or a flare star")
        elif pd.notna(amp) and amp > 0:
            what = f"a catalogued point source is up {amp:.1f} mag"
            guess = "a low-amplitude variable; weak case without a colour or a longer baseline"
        else:
            what = ("a variation on a catalogued point source that is FAINTER than "
                    "the source itself" + (f" ({amp:.1f} mag)" if pd.notna(amp) else ""))
            guess = ("not an outburst on this evidence -- most likely ordinary "
                     "variability or a subtraction residual")
        return f"{what}, {where}; {guess}"

    if ch == "A2_nova_like":
        return (f"a new point source with nothing in Pan-STARRS within 3 arcsec, "
                f"{where}, mag {mag:.1f}; "
                + ("classical-nova shaped" if plane else
                   "could be a nova, a faint CV, or a supernova in an uncatalogued host"))
    if ch and ch.startswith("B_"):
        return (f"inside the {ch[2:]} field at mag {mag:.1f}; "
                "M31/M81 novae peak near this brightness")
    if ch == "D_galactic_plane":
        return (f"{where}, mag {mag:.1f} -- the survey pipelines report almost "
                "nothing from here at any magnitude")
    if ch == "C_faint_residue":
        return f"faint residue at mag {mag:.1f}, {where}, no catalogue counterpart"
    return "unclassified pass"


def build(tag: str, *, tns_reference: dict | None = None) -> pd.DataFrame:
    tag = validated_tag(tag)
    res = _load_filtered(tag).drop_duplicates(subset=["oid"])
    if "history_jd_ceiling" not in res.columns and len(res):
        raise RuntimeError(
            f"filtered_{tag}.csv predates history ceilings; rerun m1_pool.py first"
        )
    jd_ceiling = _source_jd_ceiling(tag, res)
    pinned_reference = _pin_tns_reference(tag, jd_ceiling)
    if tns_reference is not None and tns_reference != pinned_reference:
        raise RuntimeError(f"caller supplied a different frozen TNS snapshot for {tag}")
    tns_reference = pinned_reference
    cands = res[res["passed"] == True].copy()  # noqa: E712
    print(f"{tag}: {len(res)} pool objects, {int(res['passed'].sum())} pass the filter")
    if not len(cands):
        return _empty_candidates(cands)

    # --- frozen historical TNS exclusion + current-status annotation ---------
    cands, tns_contract = apply_tns_contract(
        cands,
        frozen_reference=tns_reference,
        jd_ceiling=jd_ceiling,
        match_arcsec=F.TNS_MATCH_ARCSEC,
    )
    print(
        f"  {tns_contract['n_removed_frozen_discovery_date_bounded']} frozen TNS "
        f"dedupe matches within {F.TNS_MATCH_ARCSEC}\" -- removed; current-only matches "
        "remain flagged"
    )
    if not len(cands):
        return _empty_candidates(cands)

    # --- detection history + outburst amplitude ------------------------------
    s = session()
    hist_rows = []
    for _, r in cands.iterrows():
        records = fetch_one(
            s,
            r["oid"],
            max_age_seconds=HISTORY_MAX_AGE_SECONDS,
            required_coverage_jd=jd_ceiling,
        )
        a = pd.DataFrame(history_as_of(records, jd_ceiling))
        if len(a):
            a["i:jd"] = pd.to_numeric(a["i:jd"], errors="coerce")
            a["i:magpsf"] = pd.to_numeric(a["i:magpsf"], errors="coerce")
            fid = pd.to_numeric(a.get("i:fid"), errors="coerce")
            bands = {1: "g", 2: "r", 3: "i"}
            hist = "; ".join(
                f"{(row['i:jd']-2400000.5):.4f} {bands.get(int(f), '?')}="
                f"{row['i:magpsf']:.2f}"
                for (_, row), f in zip(a.sort_values("i:jd").iterrows(),
                                       fid[a.sort_values("i:jd").index].fillna(0))
                if pd.notna(row["i:magpsf"]))
            magnr = pd.to_numeric(a.get("i:magnr"), errors="coerce")
            amp = (float(magnr.median() - a["i:magpsf"].min())
                   if magnr.notna().any() else np.nan)
            # Variability diagnostic.  A difference-image source that sits at a
            # CONSTANT magnitude for weeks is not a transient -- it is the
            # signature of a source missing from (or mis-subtracted in) the
            # reference image.  Nothing in the pre-registered filter tests this,
            # and on live data it is the dominant contaminant, so measure it and
            # say so.  Peak-to-peak of magpsf in the passing band over the 60 days
            # ending at the last alert.
            # MUST be computed PER BAND.  Mixing g and r makes any constant
            # source with a 1.5 mag colour look like a 1.5 mag variable -- which
            # is exactly how ZTF26aabkpvd first read as the strongest candidate
            # in the list when it is in fact flat in both filters.
            jd_hi = float(a["i:jd"].max())
            a["_fid"] = pd.to_numeric(a.get("i:fid"), errors="coerce")
            win = a[(a["i:jd"] >= jd_hi - 60) & a["i:magpsf"].notna()]
            ptps, n_win = [], 0
            for _fid, grp in win.groupby("_fid"):
                if len(grp) >= 2:
                    ptps.append(float(grp["i:magpsf"].max() - grp["i:magpsf"].min()))
                n_win = max(n_win, len(grp))
            ptp = max(ptps) if ptps else np.nan
            first_mjd = float(a["i:jd"].min() - 2400000.5)
            last_mjd = float(a["i:jd"].max() - 2400000.5)
            ndet = int(len(a))
            simbad = next((v for v in a.get("d:cdsxmatch", pd.Series(dtype=str))
                           if not F._isnull(v)), "")
        else:
            hist, amp, first_mjd, last_mjd, ndet, simbad = "", np.nan, np.nan, np.nan, 0, ""
            ptp, n_win = np.nan, 0
        hist_rows.append({"detection_history_mjd_band_mag": hist[:900],
                          "ptp_mag_60d": None if pd.isna(ptp) else round(ptp, 2),
                          "n_alerts_60d_maxband": n_win,
                          "outburst_amp": None if pd.isna(amp) else round(amp, 2),
                          "first_alert_mjd": first_mjd, "last_alert_mjd": last_mjd,
                          "n_alerts_total": ndet, "simbad_class": simbad})
    cands = pd.concat([cands.reset_index(drop=True),
                       pd.DataFrame(hist_rows)], axis=1)

    cands["nearest_catalogued_source"] = np.where(
        cands["distpsnr1"].fillna(999) <= 5,
        "PS1 source, sgscore=" + cands["sgscore1"].round(2).astype(str),
        "none within 5 arcsec")
    cands["nearest_sep_arcsec"] = cands["distpsnr1"].round(2)
    cands["probably"] = cands.apply(one_liner, axis=1)
    cands["ztf_link"] = "https://fink-portal.org/" + cands["oid"]
    cands["STATUS"] = "MATTHEW-GATED -- NOT REPORTED TO TNS"

    # --- triage tier -------------------------------------------------------
    # NOT a filter change: the pre-registered filter's output is unaltered and
    # every passing object stays in the CSV.  This is a stated RANKING, applied
    # after the fact and declared here, because the fresh pass exposed something
    # the positive control could not: the filter has no amplitude requirement, so
    # on live data it is dominated by low-amplitude variability sitting on
    # catalogued point sources.  amp = magnr - magpsf; positive means the new
    # light outshines the quiescent source.
    #   tier A -- amp >= 1.5, or channel A2/B (no quiescent source to compare to)
    #   tier B -- 0.5 <= amp < 1.5
    #   tier C -- amp < 0.5 or unmeasurable: passes the filter, weak on its face
    #   FLAT override -- a candidate whose magnitude varies by less than 0.3 mag
    #   peak-to-peak across >=3 alerts in the 60 days ending at its last detection
    #   is a constant residual, not a transient, and drops to tier C whatever its
    #   apparent amplitude.  0.3 mag is below ZTF's own scatter at mag ~20, so
    #   there is no variability left to claim.
    amp = pd.to_numeric(cands["outburst_amp"], errors="coerce")
    ptp = pd.to_numeric(cands["ptp_mag_60d"], errors="coerce")
    nw = pd.to_numeric(cands["n_alerts_60d_maxband"], errors="coerce").fillna(0)
    ch = cands["channel"].astype(str)
    flat = (nw >= 3) & (ptp < 0.3)
    cands["flat_residual"] = flat
    tier = np.where(
        (amp >= 1.5) | ch.str.startswith("A2") | ch.str.startswith("B_"), "A",
        np.where(amp >= 0.5, "B", "C"))
    cands["tier"] = np.where(flat, "C", tier)

    cands = cands[[c for c in CANDIDATE_COLUMNS if c in cands.columns]]
    cands["_amp"] = pd.to_numeric(cands["outburst_amp"], errors="coerce").fillna(-9)
    cands = cands.sort_values(["tier", "_amp"], ascending=[True, False])                  .drop(columns="_amp")
    return cands


def main() -> None:
    tag = validated_tag(sys.argv[1])
    tns_reference = _existing_tns_reference(tag)
    c = build(tag, tns_reference=tns_reference)
    tns_reference = _existing_tns_reference(tag)
    jd_ceiling = _source_jd_ceiling(tag, c)
    historical_tns, current_tns = verified_provenance(
        tns_reference, jd_ceiling
    )
    out = OUT / f"m1_candidates_{tag}.csv"
    pool_summary_path = OUT / f"m1_pool_{tag}.json"
    history_provenance = cache_provenance(c["oid"].tolist())
    output_contract = {
        "contract_schema_version": 1,
        "tag": tag,
        "history_jd_ceiling": jd_ceiling,
        "source_pool_summary_sha256": sha256_file(pool_summary_path),
        "history_cache_provenance_sha256": canonical_digest(history_provenance),
        "frozen_tns_provenance_sha256": canonical_digest(historical_tns),
        "current_tns_provenance_sha256": canonical_digest(current_tns),
    }
    output_provenance = write_cache(
        out,
        c.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        kind="m1_candidate_output",
        contract=output_contract,
        row_count=len(c),
    )
    summary = {"tag": tag, "n_candidates": int(len(c)),
               "history_jd_ceiling": jd_ceiling,
               "history_as_of_mjd": jd_ceiling - 2400000.5,
               "history_cache_policy": {
                   "refresh": False,
                   "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
                   "required_coverage_jd": jd_ceiling,
               },
               "history_cache_provenance": history_provenance,
               "candidate_output_provenance": output_provenance,
               "tns_snapshot_provenance": {
                   "frozen_dedupe": historical_tns,
                   "operational_current": current_tns,
                   "membership_rule": (
                       "conservative dedupe using Discovery Date (UT) <= "
                       "history_jd_ceiling in an immutable candidate-pinned snapshot; "
                       "not exact historical registry membership; latest is annotation-only"
                   ),
               },
               "tiers": c["tier"].value_counts().to_dict() if len(c) else {},
               "n_flat_residual": int(c["flat_residual"].sum()) if len(c) else 0,
               "channels": c["channel"].value_counts().to_dict() if len(c) else {},
               "in_galactic_plane": int((c["gal_b"].abs() < F.GAL_PLANE_ABS_B).sum())
               if len(c) else 0,
               "note": "MATTHEW-GATED. Nothing in this list has been reported to TNS."}
    atomic_write(
        OUT / f"m1_candidates_{tag}.json",
        (json.dumps(summary, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps(summary, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
