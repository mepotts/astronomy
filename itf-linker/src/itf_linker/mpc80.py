"""Parser for the MPC 1992 80-column optical astrometry format.

Two entry points that MUST agree, and are pinned against each other in
``tests/test_mpc80.py``:

* :func:`parse_line` -- pure-Python, one record at a time. Used for MPEC observation
  blocks, fixtures, and anything where clarity beats throughput.
* :func:`parse_frame` -- vectorised polars expressions over a column of raw 80-char
  lines. Used for the ~9.4M-row ITF, where a Python loop would take minutes.

Field positions (1-based, inclusive) per
https://www.minorplanetcenter.net/iau/info/OpticalObs.html and the ITF plan::

     1 -  5   minor planet number                     (blank throughout the ITF)
     6 - 12   packed provisional designation / trkSub
    13        discovery asterisk
    14        note 1  (programme / observation circumstances)
    15        note 2  (observation TYPE: C=CCD, B=CMOS, S=space-based, ...)
    16 - 32   date of observation, UTC, "YYYY MM DD.dddddd"
    33 - 44   observed RA  (J2000.0), "HH MM SS.ddd"
    45 - 56   observed Dec (J2000.0), "sDD MM SS.dd"
    57 - 65   must be blank
    66 - 71   observed magnitude (66-70) and band (71)
    72        astrometric catalogue code
    73 - 77   reference / publication
    78 - 80   observatory code

Note-2 continuation lines
-------------------------
A space-based observation (note 2 ``S``) is followed by a second physical line with
note 2 ``s`` carrying the *observatory's* geocentric x/y/z in the RA/Dec columns --
not a sky position. Roving observers (``V``/``v``) and radar (``R``/``r``) work the
same way. Those lowercase lines are **not** observations; counting them inflates the
row count. :data:`CONTINUATION_NOTE2` drives that filter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import polars as pl

# --- Field slices, 0-based (start, length), derived from the 1-based table above. ------
# Single source of truth: both parsers index these, so they cannot drift apart.
F_NUMBER = (0, 5)
F_DESIG = (5, 7)
F_DISCOVERY = (12, 1)
F_NOTE1 = (13, 1)
F_NOTE2 = (14, 1)
F_YEAR = (15, 4)
F_MONTH = (20, 2)
F_DAY = (23, 9)
F_RA_H = (32, 2)
F_RA_M = (35, 2)
F_RA_S = (38, 6)
F_DEC_SIGN = (44, 1)
F_DEC_D = (45, 2)
F_DEC_M = (48, 2)
F_DEC_S = (51, 5)
F_MAG = (65, 5)
F_BAND = (70, 1)
F_CATALOG = (71, 1)
F_REFERENCE = (72, 5)
F_OBSCODE = (77, 3)

LINE_WIDTH = 80

#: Lowercase note-2 codes marking a *continuation* line of the preceding observation.
CONTINUATION_NOTE2 = frozenset({"s", "v", "r"})


class Mpc80ParseError(ValueError):
    """Raised when a line cannot be parsed as MPC 1992 80-column astrometry."""


@dataclass(frozen=True, slots=True)
class Observation:
    """One parsed optical astrometric observation."""

    number: str
    desig: str
    discovery: bool
    note1: str
    note2: str
    year: int
    month: int
    day: float
    mjd: float
    ra_deg: float
    dec_deg: float
    mag: float | None
    band: str
    catalog: str
    reference: str
    obscode: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cut(line: str, field: tuple[int, int]) -> str:
    start, length = field
    return line[start : start + length]


def gregorian_to_mjd(year: int, month: int, day: float) -> float:
    """Convert a Gregorian calendar date with fractional day to Modified Julian Date.

    Uses the standard integer Julian Day Number recurrence (Fliegel & Van Flandern),
    then adds the day fraction. Pinned against ``astropy.time.Time`` in the tests.
    """
    day_int = int(day // 1)
    day_frac = day - day_int
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = (
        day_int
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )
    # JDN is the Julian day number at noon; MJD = JD - 2400000.5, and the day starts
    # at midnight, hence the -2400001.0 (= -2400000.5 - 0.5) offset.
    return jdn - 2400001.0 + day_frac


def _sexagesimal(a: str, b: str, c: str) -> float:
    return float(a) + float(b) / 60.0 + float(c) / 3600.0


def parse_line(line: str, *, strict: bool = True) -> Observation | None:
    """Parse one 80-column line.

    Returns ``None`` for blank lines and for note-2 continuation lines (``s``/``v``/``r``),
    which are not independent observations. Raises :class:`Mpc80ParseError` on a
    malformed record when ``strict`` (the default), else returns ``None``.
    """
    raw = line.rstrip("\r\n")
    if not raw.strip():
        return None
    # Pad rather than reject: a handful of ITF rows are short by a trailing blank or two.
    if len(raw) < LINE_WIDTH:
        raw = raw.ljust(LINE_WIDTH)

    note2 = _cut(raw, F_NOTE2)
    if note2 in CONTINUATION_NOTE2:
        return None

    try:
        year = int(_cut(raw, F_YEAR))
        month = int(_cut(raw, F_MONTH))
        day = float(_cut(raw, F_DAY))
        ra_deg = 15.0 * _sexagesimal(
            _cut(raw, F_RA_H), _cut(raw, F_RA_M), _cut(raw, F_RA_S)
        )
        dec_sign = -1.0 if _cut(raw, F_DEC_SIGN).strip() == "-" else 1.0
        dec_deg = dec_sign * _sexagesimal(
            _cut(raw, F_DEC_D), _cut(raw, F_DEC_M), _cut(raw, F_DEC_S)
        )
    except ValueError as exc:  # non-numeric where a number is required
        if strict:
            raise Mpc80ParseError(f"unparseable 80-col record: {line!r}") from exc
        return None

    mag_txt = _cut(raw, F_MAG).strip()
    try:
        mag = float(mag_txt) if mag_txt else None
    except ValueError:
        mag = None

    number = _cut(raw, F_NUMBER).strip()
    desig = _cut(raw, F_DESIG).strip()
    return Observation(
        number=number,
        desig=desig or number,
        discovery=_cut(raw, F_DISCOVERY) == "*",
        note1=_cut(raw, F_NOTE1),
        note2=note2,
        year=year,
        month=month,
        day=day,
        mjd=gregorian_to_mjd(year, month, day),
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        mag=mag,
        band=_cut(raw, F_BAND).strip(),
        catalog=_cut(raw, F_CATALOG).strip(),
        reference=_cut(raw, F_REFERENCE).strip(),
        obscode=_cut(raw, F_OBSCODE).strip(),
    )


# ----------------------------------------------------------------------------------
# Vectorised path
# ----------------------------------------------------------------------------------

def _slice(col: str, field: tuple[int, int]) -> pl.Expr:
    return pl.col(col).str.slice(field[0], field[1])


def _num(col: str, field: tuple[int, int], dtype: pl.DataType) -> pl.Expr:
    return _slice(col, field).str.strip_chars().cast(dtype, strict=False)


def mjd_expr(year: pl.Expr, month: pl.Expr, day: pl.Expr) -> pl.Expr:
    """Vectorised :func:`gregorian_to_mjd`."""
    day_int = day.floor().cast(pl.Int64)
    day_frac = day - day_int
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = (
        day_int
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )
    return jdn - 2400001.0 + day_frac


def parse_frame(lf: pl.LazyFrame, raw_col: str = "raw") -> pl.LazyFrame:
    """Parse a LazyFrame whose ``raw_col`` holds 80-column records into typed columns.

    Drops blank lines and note-2 continuation lines, matching :func:`parse_line`.
    """
    year = _num(raw_col, F_YEAR, pl.Int32)
    month = _num(raw_col, F_MONTH, pl.Int32)
    day = _num(raw_col, F_DAY, pl.Float64)

    ra_deg = 15.0 * (
        _num(raw_col, F_RA_H, pl.Float64)
        + _num(raw_col, F_RA_M, pl.Float64) / 60.0
        + _num(raw_col, F_RA_S, pl.Float64) / 3600.0
    )
    dec_abs = (
        _num(raw_col, F_DEC_D, pl.Float64)
        + _num(raw_col, F_DEC_M, pl.Float64) / 60.0
        + _num(raw_col, F_DEC_S, pl.Float64) / 3600.0
    )
    dec_deg = (
        pl.when(_slice(raw_col, F_DEC_SIGN).str.strip_chars() == "-")
        .then(-dec_abs)
        .otherwise(dec_abs)
    )

    number = _slice(raw_col, F_NUMBER).str.strip_chars()
    packed = _slice(raw_col, F_DESIG).str.strip_chars()

    out = lf.with_columns(
        number.alias("number"),
        pl.when(packed.str.len_chars() > 0).then(packed).otherwise(number).alias("desig"),
        (_slice(raw_col, F_DISCOVERY) == "*").alias("discovery"),
        _slice(raw_col, F_NOTE1).alias("note1"),
        _slice(raw_col, F_NOTE2).alias("note2"),
        year.alias("year"),
        month.alias("month"),
        day.alias("day"),
        mjd_expr(year, month, day).alias("mjd"),
        ra_deg.alias("ra_deg"),
        dec_deg.alias("dec_deg"),
        _num(raw_col, F_MAG, pl.Float64).alias("mag"),
        _slice(raw_col, F_BAND).str.strip_chars().alias("band"),
        _slice(raw_col, F_CATALOG).str.strip_chars().alias("catalog"),
        _slice(raw_col, F_REFERENCE).str.strip_chars().alias("reference"),
        _slice(raw_col, F_OBSCODE).str.strip_chars().alias("obscode"),
    ).filter(
        # Same exclusions as parse_line: blanks, continuations, and rows whose required
        # numeric fields did not parse.
        (~pl.col("note2").is_in(list(CONTINUATION_NOTE2)))
        & pl.col("mjd").is_not_null()
        & pl.col("ra_deg").is_not_null()
        & pl.col("dec_deg").is_not_null()
    )
    return out.drop(raw_col)


OUTPUT_COLUMNS = [
    "number",
    "desig",
    "discovery",
    "note1",
    "note2",
    "year",
    "month",
    "day",
    "mjd",
    "ra_deg",
    "dec_deg",
    "mag",
    "band",
    "catalog",
    "reference",
    "obscode",
]
