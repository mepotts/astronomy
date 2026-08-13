"""Orbit fitting: a bridge to Bill Gray's Find_Orb (``fo``) built under WSL.

``wsl``      Windows <-> WSL path translation and subprocess plumbing.
``findorb``  Run ``fo``; parse elements, sigmas, residual RMS, covariance, convergence.
``mpcfmt``   Emit MPC 80-column astrometry (synthetic self-test data only).
``extract``  Pull a designation's *original* 80-column lines back out of the ITF snapshot.
``collide``  Detect trkSub name collisions before they are mistaken for long-arc objects.
``gates``    The MPC's published post-fit acceptance criteria.
``verify``   Closed-loop build verification against JPL Horizons.
"""

from .findorb import (
    FitResult,
    FoRun,
    parse_covar_json,
    parse_elements_txt,
    parse_total_json,
    run_fo,
    run_fo_batched,
)
from .gates import (
    GateResult,
    mpc_published_gate,
    orbit_quality_reasons,
    orbit_quality_sufficient,
    post_fit_gate,
)
from .wsl import Shell, default_shell, from_wsl_path, to_wsl_path

__all__ = [
    "FitResult",
    "FoRun",
    "GateResult",
    "Shell",
    "default_shell",
    "from_wsl_path",
    "mpc_published_gate",
    "orbit_quality_reasons",
    "orbit_quality_sufficient",
    "parse_covar_json",
    "parse_elements_txt",
    "parse_total_json",
    "post_fit_gate",
    "run_fo",
    "run_fo_batched",
    "to_wsl_path",
]
