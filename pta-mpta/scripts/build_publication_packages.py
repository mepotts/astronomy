"""Build local, explicitly scoped PTA/eROSITA review ZIPs; never uploads.

The ZIPs go under each project's ignored data/ directory. Public manifests carry
only paths, sizes, digests, commands, and limitations. No whole out/ directory is
included. Files are enumerated and hashed before packaging and verified from ZIP.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import posixpath
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-09-05"


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def census_manuscript(source):
    """Keep the main science note; replace repository-only review front matter."""
    main = source.split("## Companion note B", 1)[0]
    if "\n---\n" not in main:
        raise ValueError("census manuscript lacks expected review/body separator")
    body = main.split("\n---\n", 1)[1].strip()
    before, separator, after = body.partition("### Data availability")
    if not separator or "### References" not in after:
        raise ValueError("census manuscript lacks data/reference sections")
    references = after.split("### References", 1)[1]
    availability = """### Data availability

This compact review package contains the 261-row forensic census, 60 steady
controls, stored selection aggregates, a census-only counterpart table, figure
code, and a scoped consistency verifier. The historical full audit and bulk
inputs are not included, so this package does not independently reproduce every
number or the parent selection. See the [publication closeout](PUBLICATION-CLOSEOUT-2026-09-05.md)
and [exact member manifest](PACKAGE-MANIFEST.json). A citable archive and final
submission require the human decisions recorded in that closeout.

The underlying catalogues and upper-limit service are public at
<https://erosita.mpe.mpg.de/>. Catalog column mappings are documented in the
[scoped source mapping](publication/SOURCE-MAPPING-2026-09-05.md).

### References"""
    header = """# DRAFT — LOCAL REVIEW ONLY; NOT SUBMITTED

The scientific manuscript below is the main census note. This package omits
the optional companion and unrelated project history. Author, venue, archive
scope/license/DOI, and submission remain human decisions. The included
[closeout](PUBLICATION-CLOSEOUT-2026-09-05.md) distinguishes stored-artifact
checks from complete raw-data reproduction. Exact member digests are in
[PACKAGE-MANIFEST.json](PACKAGE-MANIFEST.json).

---

"""
    return header + before + availability + references.rstrip() + "\n"


def missing_local_links(payload, paths):
    """Validate current review entry points without rewriting historical records."""
    present = set(payload) | {"PACKAGE-MANIFEST.json"}
    missing = []
    for path in paths:
        text = payload[path].decode("utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0]
            if not target or target.startswith(("https:", "http:", "mailto:")):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if resolved not in present:
                missing.append((path, target))
    return missing


def build(name, paths, derived, commands, limitations):
    project = ROOT / name
    payload = {p: (project / p).read_bytes() for p in sorted(set(paths))}
    payload.update(derived)
    closeout_path = f"PUBLICATION-CLOSEOUT-{DATE}.md"
    payload[closeout_path] = payload[closeout_path].decode("utf-8").replace(
        f"(publication/manifest-{DATE}.json)", "(PACKAGE-MANIFEST.json)").encode("utf-8")
    entrypoints = [closeout_path]
    if name == "erosita-dr2":
        entrypoints += ["draft-rnaas-vanished-census.md", f"publication/SOURCE-MAPPING-{DATE}.md"]
    broken = missing_local_links(payload, entrypoints)
    if broken:
        raise ValueError(f"Package review links refer to omitted files: {broken}")
    if any("j0944" in p.lower() for p in payload):
        raise ValueError("Fenced source material in allowlist")
    try:
        revision = subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unavailable"
    manifest = dict(schema_version=1, status="LOCAL_REVIEW_ONLY_NOT_PUBLISHED", date=DATE,
                    base_git_revision=revision, note="File digests include uncommitted closeout edits.",
                    project=name, commands=commands, limitations=limitations,
                    files=[dict(path=p, bytes=len(b), sha256=digest(b))
                           for p, b in sorted(payload.items())])
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    archive = project / "data" / f"publication-review-{DATE}.zip"
    archive.parent.mkdir(exist_ok=True)
    # Deterministic member metadata; no timestamps or user filesystem attributes.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
        for path, blob in sorted({**payload, "PACKAGE-MANIFEST.json": encoded}.items()):
            info = zipfile.ZipInfo(f"{name}/{path}", (2026, 9, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            stream.writestr(info, blob)
    with zipfile.ZipFile(archive) as stream:
        expected = {f"{name}/{p}" for p in payload} | {f"{name}/PACKAGE-MANIFEST.json"}
        if set(stream.namelist()) != expected:
            raise ValueError("ZIP member set differs from allowlist")
        for row in manifest["files"]:
            blob = stream.read(f"{name}/{row['path']}")
            if len(blob) != row["bytes"] or digest(blob) != row["sha256"]:
                raise ValueError(f"ZIP verification failed: {row['path']}")
    manifest["local_archive"] = dict(path=archive.relative_to(ROOT).as_posix(),
                                    bytes=archive.stat().st_size, sha256=digest(archive.read_bytes()))
    publication = project / "publication"
    publication.mkdir(exist_ok=True)
    (publication / f"manifest-{DATE}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {len(payload)} files, ZIP {archive.stat().st_size} bytes, all digests verified")


def main():
    pta = ROOT / "pta-mpta"
    # Final-paper/note inputs, sampling definitions, and final per-run records.
    paths = [p.relative_to(pta).as_posix() for p in pta.glob("M[1-6]-*.md")]
    paths += [p.relative_to(pta).as_posix() for p in pta.glob("draft-*.md")]
    paths += ["PUBLICATION-CLOSEOUT-2026-09-05.md"]
    paths += [f"scripts/{p}.py" for p in [
        "m4_note_check", "m4_note_numbers", "m5_paper_check", "m5_paper_numbers",
        "m6_methods_note_check", "m6_methods_note_numbers", "mpta_harness", "mpta_models",
        "mpta_models3", "m3_run", "m3_prepare", "m3_analyze", "m3_chunks", "m3_diag",
        "m3_parse_tables", "m4_regate", "m5_curn_stability", "m5_sw_census",
        "m5_seamb_subset_null", "m5_ess_floor", "build_publication_packages"]]
    paths += ["scripts/sksparse_shim/sksparse/__init__.py", "scripts/sksparse_shim/sksparse/cholmod.py"]
    paths += [f"results/m3/{p}.json" for p in ["a1_summary", "published_table", "seam_a", "seam_b", "campaign_table"]]
    for pattern in ["results/m3/*.summary.json", "results/m3/manifest/*.json",
                    "results/m4/*.json", "results/m5/*.json", "results/m6/*.json"]:
        paths += [p.relative_to(pta).as_posix() for p in pta.glob(pattern)]
    paths += [f"figures/{p}.png" for p in ["m3_agreement", "m5_sw_census", "m4_fl_growth_fl", "m5_seamb_null", "m4_table_audit_a13"]]
    build("pta-mpta", paths, {}, [
        "python scripts/m4_note_check.py", "python scripts/m5_paper_check.py",
        "python scripts/m6_methods_note_check.py", "python scripts/m6_methods_note_numbers.py"], [
        "Run commands from the extracted pta-mpta directory. Text checks and methods-number regeneration use Python standard library only.",
        "Not a raw-data or full-chain archive. data/partim/*.tim and *.par, data/paper/mnras_template.tex, .venv, chains/, and posterior .npy arrays are deliberately omitted.",
        "Re-deriving m4_note_numbers needs arXiv:2412.01148v1 LaTeX plus the timing release DOI 10.57891/j0vh-5g31 and the recorded enterprise_extensions 3.0.3 source default. Re-deriving m5_paper_numbers additionally needs NumPy and all 83 .tim files; without them its ToA count silently becomes zero, so do not run it on this compact package.",
        "Full sampling requires the M6 recorded WSL stack (Python 3.12.3, enterprise 3.5.0, enterprise_extensions 3.0.3, PTMCMCSampler 2.1.4, PINT 1.1.6, NumPy 2.5.2, SciPy 1.18.0, Astropy 8.0.1); no portable lockfile/full rerun certification is asserted.",
        "Final run summaries/manifests and aggregate numbers are included. The full campaign consumed at least 192.4 recorded core-hours. No chains were rerun in this closeout.",
        "Authorship, venue, duplicate-publication/overlap decision, archive license/DOI, and submission remain human decisions."])
    ero = ROOT / "erosita-dr2"
    # Project the mixed archival table onto census members before inclusion.
    with (ero / "out/m2_vanished_forensics.csv").open(encoding="utf-8", newline="") as stream:
        names = {r["IAUNAME"] for r in csv.DictReader(stream)}
    with (ero / "out/m2_archival_xray.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        cols = reader.fieldnames
        selected = [r for r in reader if r["name"] in names]
    if len(selected) != len(names) or len({r["name"] for r in selected}) != len(names):
        raise ValueError("Census-only archival join incomplete or duplicated")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=cols)
    writer.writeheader()
    writer.writerows(selected)
    # Strip optional companion B from the review manuscript; XROM publication use is separate.
    manuscript = (ero / "draft-rnaas-vanished-census.md").read_text(encoding="utf-8")
    manuscript = census_manuscript(manuscript)
    derived = {"out/m2_archival_xray_census_only.csv": output.getvalue().encode(),
               "draft-rnaas-vanished-census.md": manuscript.encode()}
    paths = ["PUBLICATION-CLOSEOUT-2026-09-05.md", "publication/SOURCE-MAPPING-2026-09-05.md",
             "scripts/verify_census_package.py",
             "scripts/m5w_figure.py", "out/w2_stats.json", "out/m2_vanished_forensics.csv",
             "out/m5w_faint_validation.csv", "out/m5w_faint_validation.json",
             "out/m5w_vanished_census.png", "out/m5w_vanished_census.pdf"]
    build("erosita-dr2", paths, derived, ["python scripts/verify_census_package.py",
          "python scripts/m5w_figure.py"], [
        "Run from the extracted erosita-dr2 directory. Verifier is standard-library-only; figure requires NumPy, pandas, Matplotlib.",
        "Scope is the 261 vanished-source census and 60 steady controls only. The mixed archival table is filtered to the 261 exact census names; no riser, J0944, XROM photometry, companion B, or blanket out/ content is included.",
        "The parent selection and scale offset are stored aggregates here, not independently regenerated. Bulk DR1/DR2 FITS, w2_pairs.parquet, archive query caches, and runtime environment are omitted.",
        "Full original audit: erosita-dr2/.venv/Scripts/python.exe erosita-dr2/scripts/m5w_audit.py from repository root, with original data/ and wider out/ present. Its historical corrections are expected; it is not a text verifier and returns zero even for unverified rows.",
        "The main note's limitations and interpretation corrections are part of this package. Candidate contamination and physical switch-off count are unknown.",
        "No DOI, author metadata, account, submission or external message has been created. Final archive scope and license require human approval."])


if __name__ == "__main__":
    main()
