# Loud-failure shim for scikit-sparse (see scripts/setup_wsl_env_phase3.sh).
# Real scikit-sparse needs system SuiteSparse (libsuitesparse-dev), which this
# no-sudo WSL cannot install. enterprise 3.5.0 imports sksparse at module top
# level but, for single-pulsar PTAs with no CommonSignal, its likelihood uses
# scipy dense cho_factor and never calls cholmod. This shim satisfies the
# import and raises loudly if any sparse-cholesky code path is ever reached.
