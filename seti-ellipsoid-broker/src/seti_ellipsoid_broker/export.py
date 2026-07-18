"""Export ranked targets to nightly artifacts.

Produces the dossier's offline artifact set from a list of `models.RankedTarget`:

  ellipsoid_targets_YYYYMMDD.csv     human + machine readable table
  ellipsoid_targets_YYYYMMDD.tgt     ACP target list (amateur scheduling)
  ellipsoid_digest_YYYYMMDD.md       human-readable Markdown digest

All three writers are DETERMINISTIC: given the same targets and datestamp they produce
byte-identical files (no timestamps, no dict-ordering surprises, fixed float formatting,
``\n`` newlines, UTF-8). VOTable export is deferred to M2 (see BUILD-PLAN.md).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from pathlib import Path

from astropy.coordinates import Angle
from astropy import units as u

from .models import RankedTarget

# CSV / table schema, in fixed order. Mirrors RankedTarget's load-bearing fields.
CSV_COLUMNS: tuple[str, ...] = (
    "rank",
    "source_ref",
    "survey",
    "gaia_source_id",
    "ra_deg",
    "dec_deg",
    "distance_pc",
    "parallax_over_error",
    "ruwe",
    "crossing_epoch_jyear",
    "crossing_window_yr",
    "crossing_now",
    "crossing_flag_2yr",
    "density_bin",
    "score",
    "notes",
)


def _row_dict(rank: int, t: RankedTarget) -> dict[str, str]:
    """One CSV row as strings with fixed numeric formatting (deterministic)."""
    return {
        "rank": str(rank),
        "source_ref": t.source_ref,
        "survey": t.survey,
        "gaia_source_id": str(t.gaia_source_id),
        "ra_deg": f"{t.ra_deg:.6f}",
        "dec_deg": f"{t.dec_deg:.6f}",
        "distance_pc": f"{t.distance_pc:.3f}",
        "parallax_over_error": f"{t.parallax_over_error:.3f}",
        "ruwe": f"{t.ruwe:.3f}",
        "crossing_epoch_jyear": f"{t.crossing_epoch_jyear:.4f}",
        "crossing_window_yr": f"{t.crossing_window_yr:.4f}",
        "crossing_now": str(bool(t.crossing_now)),
        "crossing_flag_2yr": str(bool(t.crossing_flag_2yr)),
        "density_bin": str(t.density_bin),
        "score": f"{t.score:.6f}",
        "notes": t.notes,
    }


def _csv_text(targets: Sequence[RankedTarget]) -> str:
    """Render the CSV body as a string (so callers/tests can diff without touching disk)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for i, t in enumerate(targets, start=1):
        writer.writerow(_row_dict(i, t))
    return buf.getvalue()


def write_csv(targets: Sequence[RankedTarget], out_dir: Path, datestamp: str) -> Path:
    """Write ``ellipsoid_targets_<datestamp>.csv`` and return its path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ellipsoid_targets_{datestamp}.csv"
    path.write_text(_csv_text(targets), encoding="utf-8", newline="")
    return path


def _ra_hms(ra_deg: float) -> str:
    """RA in HH MM SS.s (ACP target convention)."""
    a = Angle(ra_deg * u.deg).wrap_at(360 * u.deg)
    return a.to_string(unit=u.hourangle, sep=" ", precision=1, pad=True)


def _dec_dms(dec_deg: float) -> str:
    """Dec in +DD MM SS (ACP target convention, signed)."""
    a = Angle(dec_deg * u.deg)
    return a.to_string(unit=u.deg, sep=" ", precision=0, alwayssign=True, pad=True)


def _acp_text(targets: Sequence[RankedTarget], datestamp: str) -> str:
    """Render an ACP ``.tgt`` plan.

    ACP target lists are line-oriented: ``;`` introduces a comment, and a target line is
    ``Name<TAB>RA<TAB>Dec`` with RA in hours (HH MM SS) and Dec in degrees (+DD MM SS). We
    emit one target per ranked star, name = source_ref, plus a directive header and a
    per-target comment carrying the crossing epoch / score so an observer sees the priority.
    """
    lines: list[str] = []
    lines.append(f"; SETI Ellipsoid Alert Broker - ACP target plan {datestamp}")
    lines.append("; SN 1987A SETI ellipsoid crossing candidates, ranked (highest score first).")
    lines.append("; Format: Name<TAB>RA(h m s)<TAB>Dec(d m s).  ';' = comment.")
    lines.append(";")
    for i, t in enumerate(targets, start=1):
        now_tag = "  ON-SHELL-NOW" if t.crossing_now else ""
        lines.append(
            f"; #{i}  score={t.score:.3f}  t_cross={t.crossing_epoch_jyear:.2f}"
            f" +/-{t.crossing_window_yr:.2f}yr  density_bin={t.density_bin}"
            f"  crossing_now={bool(t.crossing_now)}"
            f"  Gaia DR3 {t.gaia_source_id}{now_tag}"
        )
        name = t.source_ref.replace("\t", " ").strip() or f"target_{i}"
        lines.append(f"{name}\t{_ra_hms(t.ra_deg)}\t{_dec_dms(t.dec_deg)}")
    return "\n".join(lines) + "\n"


def write_acp_tgt(targets: Sequence[RankedTarget], out_dir: Path, datestamp: str) -> Path:
    """Write ``ellipsoid_targets_<datestamp>.tgt`` (ACP plan) and return its path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ellipsoid_targets_{datestamp}.tgt"
    path.write_text(_acp_text(targets, datestamp), encoding="utf-8", newline="")
    return path


def _markdown_text(targets: Sequence[RankedTarget], datestamp: str) -> str:
    """Render the human-readable Markdown digest."""
    lines: list[str] = []
    lines.append(f"# SETI Ellipsoid crossing candidates - {datestamp}")
    lines.append("")
    lines.append(
        f"Ranked SN 1987A SETI-ellipsoid crossing candidates ({len(targets)} target(s) "
        "after Gaia quality cuts, RUWE<1.4 and parallax_over_error>5)."
    )
    lines.append("")
    if not targets:
        lines.append("_No surviving candidates._")
        lines.append("")
        return "\n".join(lines)
    header = (
        "| # | source | survey | Gaia DR3 | RA (deg) | Dec (deg) | dist (pc) "
        "| t_cross | window (yr) | now? | density | score |"
    )
    sep = "|---|---|---|---|---:|---:|---:|---:|---:|:-:|---:|---:|"
    lines.append(header)
    lines.append(sep)
    for i, t in enumerate(targets, start=1):
        now_mark = "yes" if t.crossing_now else "no"
        lines.append(
            f"| {i} | {t.source_ref} | {t.survey} | {t.gaia_source_id} "
            f"| {t.ra_deg:.4f} | {t.dec_deg:.4f} | {t.distance_pc:.1f} "
            f"| {t.crossing_epoch_jyear:.2f} | {t.crossing_window_yr:.2f} "
            f"| {now_mark} | {t.density_bin} | {t.score:.3f} |"
        )
    lines.append("")
    lines.append(
        "Generated offline by `seti-ellipsoid-broker`. Distances are simple parallax "
        "inversions (1000/parallax) under the quality cuts; Bailer-Jones geometric distances "
        "and proper-motion correction are M2+ refinements. See SPEC.md / DATA-SOURCES.md."
    )
    lines.append("")
    return "\n".join(lines)


def write_markdown_digest(targets: Sequence[RankedTarget], out_dir: Path, datestamp: str) -> Path:
    """Write ``ellipsoid_digest_<datestamp>.md`` and return its path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ellipsoid_digest_{datestamp}.md"
    path.write_text(_markdown_text(targets, datestamp), encoding="utf-8", newline="")
    return path


def write_all(targets: Sequence[RankedTarget], out_dir: Path, datestamp: str) -> dict[str, Path]:
    """Write all three offline artifacts; return {kind: path}."""
    return {
        "csv": write_csv(targets, out_dir, datestamp),
        "tgt": write_acp_tgt(targets, out_dir, datestamp),
        "md": write_markdown_digest(targets, out_dir, datestamp),
    }
