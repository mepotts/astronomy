#!/usr/bin/env python3
"""Fast, dependency-free checks for the portfolio root.

This deliberately does not claim to reproduce the data-heavy science fronts. It checks
only contracts that can be evaluated from a clean checkout without network access:

* required root documents and project directories exist;
* relative Markdown links in the four root documents resolve inside the repository; and
* committed Python scripts in the newer science fronts parse successfully.
"""

from __future__ import annotations

import ast
import re
import sys
import tokenize
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
ROOT_DOCS = (
    ROOT / "README.md",
    ROOT / "STATUS.md",
    ROOT / "PUBLISHING.md",
    ROOT / "CONTRIBUTING.md",
)
PROJECTS = (
    "adql-copilot",
    "dyson-revet",
    "erosita-dr2",
    "gaia-dr4",
    "itf-linker",
    "pta-explainer",
    "pta-mpta",
    "seti-ellipsoid-broker",
    "tns-miner",
)
PARSED_FRONTS = ("dyson-revet", "erosita-dr2", "gaia-dr4", "pta-mpta", "tns-miner")
TARGET_PYTHON = (3, 12)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REMOTE_SCHEMES = {"http", "https", "mailto"}


def local_link_target(raw_target: str) -> str | None:
    """Return the path part of a local Markdown target, or None for remote/anchor links."""
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        # Markdown permits an optional title after the target. Root paths contain no spaces.
        target = target.split(maxsplit=1)[0]

    parts = urlsplit(target)
    if parts.scheme.lower() in REMOTE_SCHEMES or target.startswith("#"):
        return None
    # pathlib accepts forward slashes on both CI/Linux and local Windows.
    return unquote(parts.path)


def check_required_paths(errors: list[str]) -> None:
    for path in ROOT_DOCS:
        if not path.is_file():
            errors.append(f"missing root document: {path.relative_to(ROOT)}")
    for project in PROJECTS:
        if not (ROOT / project).is_dir():
            errors.append(f"missing project directory: {project}")


def check_root_links(errors: list[str]) -> int:
    checked = 0
    for document in ROOT_DOCS:
        text = document.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = local_link_target(match.group(1))
            if target is None or not target:
                continue
            checked += 1
            candidate = (document.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"{document.name}: local link escapes repository: {match.group(1)}"
                )
                continue
            if not candidate.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{document.name}:{line}: missing local link target: {match.group(1)}"
                )
    return checked


def check_python_syntax(errors: list[str]) -> int:
    checked = 0
    for front in PARSED_FRONTS:
        scripts = ROOT / front / "scripts"
        if not scripts.is_dir():
            errors.append(f"missing scripts directory: {scripts.relative_to(ROOT)}")
            continue
        for path in sorted(scripts.rglob("*.py")):
            checked += 1
            try:
                with tokenize.open(path) as handle:
                    source = handle.read()
                ast.parse(
                    source,
                    filename=str(path),
                    feature_version=TARGET_PYTHON,
                )
            except (OSError, SyntaxError, UnicodeError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
    return checked


def main() -> int:
    errors: list[str] = []
    check_required_paths(errors)
    link_count = check_root_links(errors)
    python_count = check_python_syntax(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"portfolio verification failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(
        "portfolio verification passed: "
        f"{len(ROOT_DOCS)} root documents, {link_count} local links, "
        f"{python_count} Python scripts (Python {TARGET_PYTHON[0]}.{TARGET_PYTHON[1]} syntax)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
