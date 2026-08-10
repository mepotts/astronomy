"""Roll raw frames and reduced products up into a per-night observing inventory.

Pure functions over plain records: no network, no TAP, no astropy Table. ``tap.py`` does
the I/O and hands the results here. That split is what makes the awkward part -- deciding
which nights are actually *usable* -- testable without hitting ESO.

Two distinctions do all the work:

* **public vs proprietary.** ESO release dates are per-frame. A night is usable now only
  if its release date has passed.
* **raw vs reduced.** A night present in ``dbo.raw`` but absent from ``ivoa.ObsCore``
  ``calib_level=2`` has no pipeline-reduced spectrum, and reducing it ourselves means
  esorex/cr2res under WSL. M0 measures how many nights fall in that gap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Frame:
    """One raw frame or one reduced product, normalised."""

    target: str
    night: str          # ISO date, YYYY-MM-DD
    prog_id: str
    setting: str        # CRIRES+ wavelength setting, e.g. "H", "K", "HX5E-2", "J"
    release: datetime   # tz-aware UTC
    reduced: bool = False
    access_url: str = ""   # populated for reduced products only; how `probe` fetches them


@dataclass
class Night:
    """Everything known about one night on one target."""

    night: str
    n_raw: int = 0
    n_reduced: int = 0
    prog_ids: set[str] = field(default_factory=set)
    settings: set[str] = field(default_factory=set)
    earliest_release: datetime | None = None

    @property
    def has_reduced(self) -> bool:
        return self.n_reduced > 0

    def is_public(self, now: datetime) -> bool:
        return self.earliest_release is not None and self.earliest_release <= now

    def in_band(self, prefix: str) -> bool:
        """True if any setting this night belongs to the given band, e.g. "H"."""
        return any(s.upper().startswith(prefix.upper()) for s in self.settings)


def parse_setting(filter_path: str | None) -> str:
    """CRIRES+ ``filter_path`` is "<setting>,<band group>", e.g. "H,HK" or "HX5E-2,HK"."""
    if not filter_path:
        return "?"
    return str(filter_path).split(",")[0].strip()


def parse_release(value: str) -> datetime:
    """ESO release dates come back as ISO with a trailing Z, which fromisoformat
    parses natively on our 3.11+ floor."""
    return datetime.fromisoformat(str(value))


def roll_up(frames: list[Frame]) -> list[Night]:
    """Group frames into nights, newest release wins nothing -- we keep the *earliest*.

    Earliest release is the right choice: if any frame from a night is public, that night
    has some usable data. Taking the latest would hide partially-released nights.
    """
    by_night: dict[str, Night] = {}
    for f in frames:
        n = by_night.setdefault(f.night, Night(night=f.night))
        if f.reduced:
            n.n_reduced += 1
        else:
            n.n_raw += 1
        n.prog_ids.add(f.prog_id)
        n.settings.add(f.setting)
        if n.earliest_release is None or f.release < n.earliest_release:
            n.earliest_release = f.release
    return sorted(by_night.values(), key=lambda n: n.night)


@dataclass
class Inventory:
    """The M0 answer for one target."""

    target: str
    nights: list[Night]
    now: datetime

    def _sel(self, band: str | None, public: bool | None, reduced: bool | None) -> list[Night]:
        out = self.nights
        if band is not None:
            out = [n for n in out if n.in_band(band)]
        if public is not None:
            out = [n for n in out if n.is_public(self.now) is public]
        if reduced is not None:
            out = [n for n in out if n.has_reduced is reduced]
        return out

    def usable(self, band: str = "H") -> list[Night]:
        """Public *and* pipeline-reduced in the requested band: what M2 can run on today."""
        return self._sel(band, public=True, reduced=True)

    def reduction_gap(self, band: str = "H") -> list[Night]:
        """Public but with no reduced product -- recoverable only via esorex/cr2res."""
        return self._sel(band, public=True, reduced=False)

    def embargoed(self, band: str = "H") -> list[Night]:
        """Observed but still proprietary, with the date each becomes available."""
        return self._sel(band, public=False, reduced=None)

    def summary(self, band: str = "H") -> dict:
        usable, gap, emb = self.usable(band), self.reduction_gap(band), self.embargoed(band)
        return {
            "target": self.target,
            "band": band,
            "nights_total": len(self._sel(band, None, None)),
            "usable_now": len(usable),
            "reduction_gap": len(gap),
            "embargoed": len(emb),
            "usable_baseline": [usable[0].night, usable[-1].night] if usable else None,
            "gap_nights": [n.night for n in gap],
            "embargo_lifts": sorted(
                {n.earliest_release.date().isoformat() for n in emb if n.earliest_release}
            ),
        }


def utcnow() -> datetime:
    return datetime.now(UTC)
