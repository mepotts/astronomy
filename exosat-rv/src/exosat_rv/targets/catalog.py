"""Build the M5 analogue target list: substellar companions with public CRIRES+ spectra.

**Searched backwards on purpose.** The obvious direction — take a catalogue of imaged
companions and ask which have archive data — cannot work here, because the NASA Exoplanet
Archive caps companion mass at 30 M_Jup and therefore does not contain CD-35 2722 B. A list
built that way would omit the object being reproduced, and would systematically miss the
most favourable hosts (brown dwarf companions wide enough to sit in a slit).

So this asks the archive first: *which CRIRES+ pointings were aimed at a companion?* Then it
resolves each against SIMBAD to find out what the companion actually is. The method carries
its own control — **CD-35 2722 B must come back** — asserted in `tests/test_catalog.py`.

Resolution is two-stage: a cone search finds the *system* (robust, since SIMBAD identifiers
are unforgiving about spacing — `CD-35  2722B` resolves, `CD-35 2722 B` does not — while the
archive's OBJECT strings are free text), then an identifier match picks the *component*.
Position alone cannot do the second job: a companion and its primary are arcseconds apart.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pyvo

from ..config import ESO_TAP

SIMBAD_TAP = "https://simbad.cds.unistra.fr/simbad/sim-tap"

COMPANION_TOKEN = re.compile(r"(?:^|[\s_-])([BbCc])(?:\s|$|_|-)")
"""An OBJECT string naming a companion ends with a bare B/b/C/c component letter.

Deliberately loose: it over-selects, and SIMBAD's object type does the real filtering. A
tight regex would silently drop pointings whose observer used an unusual convention, and a
silent drop in a target list is worse than a false positive that gets classified out.
"""

JUNK_NAME = re.compile(r"^(?:C|P)[_/]\d{4}(?:[_\W]|$)|^\d{1,3}[PD]/|COMET", re.IGNORECASE)
"""Comet designations (``C_2006_W3``, ``C_2007_N3_LULIN``) trip the component-letter regex.
Excluded by name because no cone search will classify them usefully.

Note the trailing ``(?:[_\\W]|$)`` rather than ``\b``: these names continue with an
underscore, which *is* a word character, so a word boundary never matches there."""

SUBSTELLAR_OTYPES = {"BD*", "Pl", "brownD*", "Planet"}
"""SIMBAD types that are unambiguously substellar."""

BORDERLINE_OTYPES = {"LM*", "Y*O", "*"}
"""Low-mass stars and unclassified objects. Kept and reported, never silently dropped:
the star/brown-dwarf boundary is exactly where the interesting hosts sit, and several
genuine imaged companions (GQ Lup B, eta Tel B) are typed `LM*` in SIMBAD."""


STELLAR_SPTYPE = re.compile(r"^\s*[OBAFGK]\d|^\s*M[0-6]", re.IGNORECASE)
"""Spectral types that settle the question against substellar, whatever SIMBAD's otype says.

SIMBAD types `tau Boo B` (M3V) and `HD 149274B` (M5) as `*`, which the otype filter alone
lets through as "borderline". An M3 dwarf is a star. M7 and later, and all L/T/Y, stay
borderline-or-substellar because that is genuinely where the boundary sits at young ages.
"""

SUBSTELLAR_SPTYPE = re.compile(r"^\s*[LTY]\d|^\s*M[789]", re.IGNORECASE)


@dataclass
class CompanionTarget:
    """One candidate, as the archive and SIMBAD jointly describe it."""

    eso_object: str
    n_frames: int
    n_public: int
    ra_deg: float
    dec_deg: float
    simbad_id: str | None = None
    otype: str | None = None
    sp_type: str | None = None
    plx_mas: float | None = None
    match_kind: str | None = None
    """How SIMBAD was matched: ``identifier`` (strong -- the component itself),
    ``nearest-substellar`` / ``nearest-borderline`` / ``nearest-any`` (weak -- may be the
    primary or a sibling planet, and must not be quoted as the companion's properties)."""
    aliases: list[str] = field(default_factory=list)
    """Other ESO OBJECT strings that resolved to the same SIMBAD object."""

    @property
    def distance_pc(self) -> float | None:
        """SIMBAD returns NaN, not NULL, for a missing parallax -- so a bare truthiness
        check lets NaN through and prints "nan pc" as though it were a measurement."""
        p = self.plx_mas
        if p is None or not math.isfinite(p) or p <= 0:
            return None
        return 1000.0 / p

    @property
    def is_substellar(self) -> bool | None:
        """True / False / None-for-unknown. Never guesses.

        Spectral type outranks object type in both directions: it is the more specific
        statement, and SIMBAD's `otype` is often just `*` for a resolved companion.
        """
        if self.sp_type:
            if STELLAR_SPTYPE.match(self.sp_type):
                return False
            if SUBSTELLAR_SPTYPE.match(self.sp_type):
                return True if self.otype in SUBSTELLAR_OTYPES else None
        if self.otype is None:
            return None
        if self.otype in SUBSTELLAR_OTYPES:
            return True
        if self.otype in BORDERLINE_OTYPES:
            return None
        return False


def _service(url: str) -> pyvo.dal.TAPService:
    return pyvo.dal.TAPService(url)


def candidate_pointings(min_frames: int = 4) -> list[CompanionTarget]:
    """CRIRES+ science pointings whose OBJECT names a companion.

    ``min_frames`` drops one-off acquisitions; an RV campaign leaves many frames. Set to 0
    to see everything.
    """
    q = """
    SELECT object, COUNT(*) AS n, AVG(ra) AS ra, AVG(dec) AS dec,
           MIN(release_date) AS first_rel
    FROM dbo.raw
    WHERE instrument LIKE 'CRIRES%' AND dp_cat = 'SCIENCE' AND dp_tech LIKE 'SPECTRUM%'
    GROUP BY object
    """
    rows = _service(ESO_TAP).search(q, maxrec=100000)
    now = datetime.now(UTC)
    out: list[CompanionTarget] = []
    for r in rows:
        name = str(r["object"]).strip()
        if not COMPANION_TOKEN.search(name) or JUNK_NAME.search(name):
            continue
        n = int(r["n"])
        if n < min_frames:
            continue
        try:
            ra, dec = float(r["ra"]), float(r["dec"])
        except (TypeError, ValueError):
            continue
        if not (-90 <= dec <= 90):
            continue
        rel = datetime.fromisoformat(str(r["first_rel"]))
        out.append(
            CompanionTarget(
                eso_object=name, n_frames=n, n_public=n if rel <= now else 0,
                ra_deg=ra, dec_deg=dec,
            )
        )
    return sorted(out, key=lambda t: -t.n_frames)


def _norm(name: str) -> str:
    """Collapse an identifier to something comparable across catalogues.

    SIMBAD writes ``* bet Pic b``, ``V* PZ Tel B``, ``CD-35  2722B``; observers write
    ``BET PIC B``, ``PZ TEL B``, ``CD-35 2722 B``. Strip the type prefixes, drop every
    separator, uppercase.
    """
    n = re.sub(r"^(?:NAME|V\*|\*\*|\*)\s+", "", name.strip())
    return re.sub(r"[\s_\-]+", "", n).upper()


def resolve(targets: list[CompanionTarget], radius_arcsec: float = 20.0) -> None:
    """Attach SIMBAD identity to each target, in place.

    Two stages, because neither alone is sufficient:

    1. **Cone search** finds the *system*. Robust to naming, useless for picking a
       component — a companion and its primary are arcseconds apart, and an earlier
       single-stage version duly resolved ``BET PIC B`` to beta Pic **c** and ``PZ TEL B``
       to the G9IV primary.
    2. **Identifier match** picks the *component*, by comparing the ESO OBJECT string to
       every SIMBAD identifier of every object in the cone, under `_norm`.

    Falls back to the nearest substellar/borderline object, then to the nearest object of
    any type, and records which stage succeeded in `match_kind` so a weak match is never
    mistaken for a strong one.
    """
    sim = _service(SIMBAD_TAP)
    rad = radius_arcsec / 3600.0
    for t in targets:
        q = f"""
        SELECT TOP 200 b.main_id, b.otype, b.sp_type, b.plx_value, i.id,
               DISTANCE(POINT('ICRS', b.ra, b.dec),
                        POINT('ICRS', {t.ra_deg:.6f}, {t.dec_deg:.6f})) AS d
        FROM basic AS b JOIN ident AS i ON i.oidref = b.oid
        WHERE CONTAINS(POINT('ICRS', b.ra, b.dec),
                       CIRCLE('ICRS', {t.ra_deg:.6f}, {t.dec_deg:.6f}, {rad:.8f})) = 1
        ORDER BY d ASC
        """
        try:
            rows = list(sim.search(q, maxrec=200))
        except Exception as exc:  # noqa: BLE001 - unresolved stays unresolved, not fatal
            t.match_kind = f"error:{type(exc).__name__}"
            continue
        if not rows:
            continue

        want = _norm(t.eso_object)
        by_main: dict[str, list] = {}
        for r in rows:
            by_main.setdefault(str(r["main_id"]).strip(), []).append(r)

        chosen, kind = None, None
        for main, rs in by_main.items():
            if any(_norm(str(r["id"])) == want for r in rs) or _norm(main) == want:
                chosen, kind = rs[0], "identifier"
                break
        if chosen is None:
            sub = [r for r in rows if str(r["otype"]).strip() in SUBSTELLAR_OTYPES]
            bord = [r for r in rows if str(r["otype"]).strip() in BORDERLINE_OTYPES]
            if sub:
                chosen, kind = sub[0], "nearest-substellar"
            elif bord:
                chosen, kind = bord[0], "nearest-borderline"
            else:
                chosen, kind = rows[0], "nearest-any"

        t.simbad_id = str(chosen["main_id"]).strip()
        t.otype = str(chosen["otype"]).strip()
        t.sp_type = str(chosen["sp_type"]).strip() or None
        t.match_kind = kind
        try:
            plx = float(chosen["plx_value"])
            t.plx_mas = plx if math.isfinite(plx) and plx > 0 else None
        except (TypeError, ValueError):
            t.plx_mas = None


def dedupe(targets: list[CompanionTarget]) -> list[CompanionTarget]:
    """Collapse targets that resolved to the same SIMBAD object.

    Observers name the same companion differently across programmes -- ``ETA TEL B`` and
    ``HR-7329-B`` are one object, since HR 7329 *is* eta Tel. Frames are summed and the
    alternate OBJECT strings retained, because a target list that hides a name will send
    someone back to the archive for data it already counted.
    """
    merged: dict[str, CompanionTarget] = {}
    out: list[CompanionTarget] = []
    for t in targets:
        if not t.simbad_id:
            out.append(t)
            continue
        keep = merged.get(t.simbad_id)
        if keep is None:
            merged[t.simbad_id] = t
            out.append(t)
            continue
        keep.n_frames += t.n_frames
        keep.n_public += t.n_public
        keep.aliases.append(t.eso_object)
        if keep.match_kind != "identifier" and t.match_kind == "identifier":
            keep.match_kind = t.match_kind
    return sorted(out, key=lambda t: -t.n_frames)


def shortlist(targets: list[CompanionTarget]) -> list[CompanionTarget]:
    """Targets worth actually pursuing: substellar or borderline, and publicly available.

    Borderline (`LM*`) types are kept deliberately. The star/brown-dwarf boundary is where
    the favourable hosts live, and SIMBAD types several genuine imaged companions -- GQ Lup B,
    eta Tel B, CT Cha B -- as low-mass stars.
    """
    return [t for t in targets if t.is_substellar is not False and t.n_public > 0]


def build(min_frames: int = 4) -> list[CompanionTarget]:
    targets = candidate_pointings(min_frames)
    resolve(targets)
    return dedupe(targets)
