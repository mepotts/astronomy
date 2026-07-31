"""The vetting stage: *"is this candidate a catalogue object?"*, asked properly.

M1 ends with designations that have acceptable orbit fits. That is not the same thing as
an unreported object, and the gap between the two is where this project could do real
damage -- submitting an already-known object to the MPC's identifications endpoint costs
the submitter's reputation and the MPC's time. This package closes that gap and is designed
to be the mandatory stage every candidate passes, whatever produced it: an ITF trkSub, a
linked triplet, a DAD tracklet.

The contract is small on purpose::

    from itf_linker.vet import CachedSession, VetCandidate, vet_candidates

    session = CachedSession(Path("data/vet-cache"))
    report = vet_candidates(session, candidates)

and the honesty constraints are structural rather than advisory:

* the only verdict categories are ``known``, ``unmatched``, ``ambiguous`` and
  ``service_failed``. **There is no "new" and no "confirmed".**
* ``unmatched`` always carries a reason, because "no match" and "not covered" and "orbit
  too loose to match" are three different findings and only one of them is interesting.
* every external call is a rate-limited, disk-cached, read-only GET, and a service that
  starts failing is switched off rather than retried around.
"""

from .cache import USER_AGENT, CachedSession, ServiceUnavailable
from .pipeline import Resolver, select_epochs, vet_candidate, vet_candidates
from .sources import from_m1_report, from_mpc80_lines, horizons_control
from .types import (
    ElementComparison,
    OrbitElements,
    ServiceMatch,
    ServiceReport,
    VetCandidate,
    VetObservation,
    VetVerdict,
    angular_sep_arcsec,
)
from .verdict import classify, tally

__all__ = [
    "USER_AGENT",
    "CachedSession",
    "ElementComparison",
    "OrbitElements",
    "Resolver",
    "ServiceMatch",
    "ServiceReport",
    "ServiceUnavailable",
    "VetCandidate",
    "VetObservation",
    "VetVerdict",
    "angular_sep_arcsec",
    "classify",
    "from_m1_report",
    "from_mpc80_lines",
    "horizons_control",
    "select_epochs",
    "tally",
    "vet_candidate",
    "vet_candidates",
]
