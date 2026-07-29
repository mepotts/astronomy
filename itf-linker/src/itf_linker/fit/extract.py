"""Pull a designation's *original* 80-column lines back out of the ITF snapshot.

Find_Orb reads MPC 80-column text, and the parsed Parquet cannot be turned back into it
faithfully. Three things are lost or damaged by a re-emit:

* **precision** -- positions are stored as degrees; re-formatting them as sexagesimal
  reintroduces rounding that the original file did not have;
* **the astrometric catalogue code** (column 72) and the magnitude/band, which Find_Orb
  uses for debiasing and for its own weighting;
* **the ``s`` continuation lines**, which carry a space telescope's geocentric x/y/z *in
  the RA/Dec columns*. The parser drops them (they are not observations). Without its
  partner ``s`` line an ``S`` observation cannot be reduced at all.

So the lines are re-read verbatim from ``itf.txt.gz``. One streaming pass over 9.36M
lines takes a few seconds and is exact by construction.

The same pass is where **unpaired ``S`` observations** are removed: M0 counted 1,282 ``S``
records with no following ``s`` line across the whole file. They are dropped here, where
the pairing is actually visible, rather than in the Parquet, where it is not.
"""

from __future__ import annotations

import gzip
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .. import config
from ..mpc80 import CONTINUATION_NOTE2, F_DESIG, F_NOTE2, F_OBSCODE, LINE_WIDTH

#: Note-2 codes whose observation is split across two physical lines.
PAIRED_NOTE2 = {"S": "s", "V": "v", "R": "r"}


def _field(line: str, field: tuple[int, int]) -> str:
    start, length = field
    return line[start : start + length]


def extract_lines(
    designations: Iterable[str],
    src: Path | None = None,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Return ``{designation: [80-column lines]}`` plus extraction statistics.

    Lines are returned in file order, with each observation immediately followed by its
    continuation line where one exists. An observation whose continuation is missing is
    dropped and counted.
    """
    src = src or config.ITF_GZ
    wanted = {d for d in designations if d}
    # Sorted, not set-ordered: the returned dict's order decides how designations are
    # grouped into `fo` invocations, and Python randomises string hashing per process.
    # Left unsorted, two runs of the same command group objects differently and the
    # headline counts wobble by a designation or two -- which is indistinguishable from
    # a real change and makes the report unreproducible.
    out: dict[str, list[str]] = {d: [] for d in sorted(wanted)}

    stats = {
        "designations_requested": len(wanted),
        "lines_scanned": 0,
        "observations_kept": 0,
        "continuations_kept": 0,
        "dropped_unpaired_paired_note": 0,
        "dropped_short_line": 0,
    }

    #: An emitted observation still waiting for its continuation line:
    #: (designation, expected note-2, index of the line already appended).
    pending: tuple[str, str, int] | None = None

    def retract_unpaired() -> None:
        """Undo the provisional emit of an observation whose continuation never arrived."""
        nonlocal pending
        if pending is not None:
            desig, _, idx = pending
            del out[desig][idx]
            stats["observations_kept"] -= 1
            stats["dropped_unpaired_paired_note"] += 1
            pending = None

    with gzip.open(src, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        for raw in fh:
            stats["lines_scanned"] += 1
            line = raw.rstrip("\n").rstrip("\r")
            if len(line) < LINE_WIDTH:
                if not line.strip():
                    continue
                line = line.ljust(LINE_WIDTH)
                stats["dropped_short_line"] += 1

            note2 = _field(line, F_NOTE2)
            desig = _field(line, F_DESIG).strip()

            if note2 in CONTINUATION_NOTE2:
                # Only keep a continuation if it belongs to the observation just emitted.
                if pending is not None and pending[0] == desig and pending[1] == note2:
                    out[desig].append(line)
                    stats["continuations_kept"] += 1
                    pending = None
                continue

            retract_unpaired()

            if desig not in wanted:
                continue
            expected = PAIRED_NOTE2.get(note2)
            out[desig].append(line)
            stats["observations_kept"] += 1
            if expected is not None:
                # Provisional: retracted by retract_unpaired if no continuation follows.
                pending = (desig, expected, len(out[desig]) - 1)

        retract_unpaired()

    stats["designations_found"] = sum(1 for v in out.values() if v)
    return out, stats


def observatory_codes(lines: Iterable[str]) -> set[str]:
    return {_field(ln, F_OBSCODE).strip() for ln in lines if len(ln) >= LINE_WIDTH}
