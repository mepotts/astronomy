"""Emit MPC 1992 80-column astrometry.

The inverse of :mod:`itf_linker.mpc80`. Only needed for *synthetic* astrometry -- the
build self-test writes JPL Horizons positions in the format Find_Orb reads. Real ITF
observations are never round-tripped through here: their original 80-column lines are
extracted verbatim (see :mod:`itf_linker.fit.extract`), which preserves the catalogue
code, magnitude, and the space-based ``s`` continuation lines that carry the spacecraft's
position and that a re-emit would destroy.

Round-tripping ``format_line -> itf_linker.mpc80.parse_line`` is pinned by tests.
"""

from __future__ import annotations

from ..mpc80 import LINE_WIDTH


def _sexagesimal(value: float, places: int, width: int) -> tuple[int, int, str]:
    """Split a positive decimal quantity into (whole, minutes, seconds-as-text)."""
    whole = int(value)
    rem = (value - whole) * 60.0
    minutes = int(rem)
    seconds = (rem - minutes) * 60.0
    text = f"{seconds:0{width}.{places}f}"
    # Carry the rounding: 59.996 -> "60.00" must become the next minute.
    if float(text) >= 60.0:
        text = f"{0.0:0{width}.{places}f}"
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        whole += 1
    return whole, minutes, text


def format_ra(ra_deg: float) -> str:
    """RA in degrees -> ``HH MM SS.sss`` (12 characters, columns 33-44)."""
    hours = (ra_deg % 360.0) / 15.0
    h, m, s = _sexagesimal(hours, 3, 6)
    return f"{h % 24:02d} {m:02d} {s}"


def format_dec(dec_deg: float) -> str:
    """Dec in degrees -> ``sDD MM SS.ss`` (12 characters, columns 45-56)."""
    sign = "-" if dec_deg < 0 else "+"
    d, m, s = _sexagesimal(abs(dec_deg), 2, 5)
    return f"{sign}{d:02d} {m:02d} {s}"


def format_date(year: int, month: int, day: float) -> str:
    """``YYYY MM DD.dddddd`` (17 characters, columns 16-32)."""
    return f"{year:04d} {month:02d} {day:09.6f}"


def format_line(
    *,
    desig: str,
    year: int,
    month: int,
    day: float,
    ra_deg: float,
    dec_deg: float,
    obscode: str,
    mag: float | None = None,
    band: str = "V",
    catalog: str = " ",
    note1: str = " ",
    note2: str = "C",
    number: str = "",
    discovery: bool = False,
) -> str:
    """Build one 80-column record. ``desig`` occupies columns 6-12 (max 7 characters)."""
    if len(desig) > 7:
        raise ValueError(f"designation {desig!r} exceeds the 7-character trkSub field")
    if len(obscode) != 3:
        raise ValueError(f"observatory code {obscode!r} must be 3 characters")

    line = [" "] * LINE_WIDTH
    def put(start: int, text: str) -> None:  # 0-based start
        line[start : start + len(text)] = list(text)

    put(0, f"{number:>5.5s}")
    put(5, f"{desig:<7.7s}")
    put(12, "*" if discovery else " ")
    put(13, note1[:1] or " ")
    put(14, note2[:1] or " ")
    put(15, format_date(year, month, day))
    put(32, format_ra(ra_deg))
    put(44, format_dec(dec_deg))
    if mag is not None:
        put(65, f"{mag:5.1f}")
        put(70, band[:1])
    put(71, catalog[:1] or " ")
    put(77, obscode)
    return "".join(line)
