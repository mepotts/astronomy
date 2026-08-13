"""M10 -- the astrometric route to an exosatellite, inventoried archive-first.

**Why this exists.** The project's whole search has been radial velocity, and M9 measured
that the RV extraction gap is not closing by any cheap lever. Meanwhile Kral et al. 2026
(`papers/text/kral2026_gravity_hd206893b.txt`, [arXiv:2511.20091](https://arxiv.org/abs/2511.20091))
published **the first astrometric exomoon search** -- VLTI/GRAVITY on HD 206893 B -- and
reported tentative residuals consistent with a ~0.4 M_Jup companion at P ~ 0.76 yr, while
cautioning they may be systematics.

Three facts make that the strongest parallel track available:

1. **Lazzoni et al. 2022 rank astrometry above RV** for binary-like satellites -- P = 0.999
   against 0.996, the best of their four techniques -- and until Kral et al. nobody had run
   it.
2. **It reaches deeper than RV.** Kral et al. claim feasibility "to detect moons with
   masses lower than Jupiter and potentially down to less than Neptune in optimistic cases",
   below the ~0.4 M_Jup floor M7 finds for RV on any imaged companion.
3. **It is independent of the extraction gap** that M2/M3/M9 have failed to close.

Kral et al. name their own follow-up shortlist -- and the two they call best short-term,
**AF Lep b and beta Pic b**, include the object sitting at **#2 in M7's RV ranking**. beta
Pic b is therefore the one target where an RV limit and an astrometric limit could be set
independently and cross-checked.

Their selection scaling, for reference (their eq. 6): detectable moon mass goes as
``T_moon^(-2/3) * d * M_planet^(2/3)`` -- so short satellite periods, nearby systems and
light planets win, the same directions the RV scaling prefers.

**What this module does and does not establish.** It is the M0-equivalent: an inventory of
what is public. The M1-equivalent probe -- open a product and verify it carries what an
astrometric fit needs -- has **not** been done. See ``KILL_CHECK``.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from ..config import ESO_TAP

MJD_EPOCH = dt.datetime(1858, 11, 17, tzinfo=dt.UTC)

BLUNT_SHORTLIST: dict[str, tuple[float, float]] = {
    "AF Lep b": (81.7686, -11.9012),
    "beta Pic b": (86.8212, -51.0665),
    "HD 206893 B": (326.3423, -12.7863),
    "HD 155555 (AB) b": (259.3556, -66.9508),
    "2M1315-2649 b": (198.8789, -26.8309),
}
"""Kral et al. 2026 section 6's five viable GRAVITY+ exomoon targets, plus HD 206893 B
where their own candidate sits. They cut on K < 20 mag and host-companion contrast < 1e5.

``HD 60584 b`` is in their list but omitted here: it is an unconfirmed candidate
(Bonavita et al. 2022) with no reliable position to query on.
"""

KILL_CHECK = """The probe has NOT been run.

M0/M1 established for CRIRES+ that (a) the data is public and (b) the reduced products are
per-order extractions viper can actually consume -- and M1 nearly got (b) wrong, which would
have cost the project a needless cr2res rebuild. The same two questions apply here and only
the first is answered.

Open: ESO serves GRAVITY calib_level=2 products as ``dataproduct_type='visibility'``.
Whether those carry the **dual-field differential phase** an astrometric fit needs, at the
~10-50 micro-arcsecond precision the science requires, is unverified. Interferometric
astrometry of a companion is not extracted the way a spectrum is, and 'reduced visibilities
exist' is not the same claim as 'the astrometry is recoverable from them'.

Do not describe this route as open until a product has been downloaded and inspected."""


@dataclass
class GravityTarget:
    name: str
    ra_deg: float
    dec_deg: float
    n_products: int = 0
    nights: list[str] = field(default_factory=list)
    n_raw_science: int = 0
    n_raw_public: int = 0
    programmes: list[str] = field(default_factory=list)

    @property
    def baseline_days(self) -> int:
        if len(self.nights) < 2:
            return 0
        a = dt.date.fromisoformat(self.nights[0])
        b = dt.date.fromisoformat(self.nights[-1])
        return (b - a).days

    @property
    def usable(self) -> bool:
        """Enough epochs over enough time to separate a satellite wobble from the orbit.

        The bar is M5's, reused deliberately: >= 8 nights over >= 100 days. A satellite
        signature is a *residual* after the companion's own orbit is removed, so orbital
        coverage matters as much as epoch count -- if anything the bar should be higher here.
        """
        return len(self.nights) >= 8 and self.baseline_days >= 100


def _service():
    import pyvo

    return pyvo.dal.TAPService(ESO_TAP)


def inventory(
    targets: dict[str, tuple[float, float]] | None = None, radius_deg: float = 0.03
) -> list[GravityTarget]:
    """Public VLTI/GRAVITY holdings at each shortlist position.

    Queries both tables for the same reason M0 does: ``dbo.raw`` says what was *observed*
    and carries the release dates, ``ivoa.ObsCore`` says what is *reduced and servable*.
    They disagree, and the difference is the work someone would have to redo.
    """
    import warnings

    warnings.filterwarnings("ignore")
    svc = _service()
    out: list[GravityTarget] = []
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")

    for name, (ra, dec) in (targets or BLUNT_SHORTLIST).items():
        box = (
            f"s_ra BETWEEN {ra - radius_deg} AND {ra + radius_deg} "
            f"AND s_dec BETWEEN {dec - radius_deg} AND {dec + radius_deg}"
        )
        rows = svc.search(
            "SELECT t_min FROM ivoa.ObsCore WHERE instrument_name LIKE 'GRAVITY%' "
            f"AND calib_level=2 AND {box}"
        ).to_table()
        nights = sorted(
            {
                (MJD_EPOCH + dt.timedelta(days=float(r["t_min"]))).strftime("%Y-%m-%d")
                for r in rows
                if r["t_min"]
            }
        )

        raw_box = (
            f"ra BETWEEN {ra - radius_deg} AND {ra + radius_deg} "
            f"AND dec BETWEEN {dec - radius_deg} AND {dec + radius_deg}"
        )
        raw = svc.search(
            "SELECT release_date, prog_id FROM dbo.raw WHERE instrument='GRAVITY' "
            f"AND dp_cat='SCIENCE' AND {raw_box}"
        ).to_table()
        public = [r for r in raw if str(r["release_date"])[:10] <= now]

        out.append(
            GravityTarget(
                name=name,
                ra_deg=ra,
                dec_deg=dec,
                n_products=len(rows),
                nights=nights,
                n_raw_science=len(raw),
                n_raw_public=len(public),
                programmes=sorted({str(r["prog_id"]) for r in raw}),
            )
        )
    out.sort(key=lambda t: (-len(t.nights), -t.baseline_days))
    return out
